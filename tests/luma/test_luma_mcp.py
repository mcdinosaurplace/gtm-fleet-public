"""Tests for the Luma MCP server (scripts/luma_mcp.py).

Mocked-httpx units, no network. Covers the behaviors the build plan §5 calls
out: cursor pagination, 429 retry honoring Retry-After, the _provenance /
next_cursor envelope shape, tool registration (read tier always; write tier
only when LUMA_ENABLE_WRITES=1), the write-tier safe defaults (create ->
private, update -> suppress_notifications), and — the load-bearing one (§9) —
API-key redaction from every error message and repr. Live behavior is verified
separately via `luma_mcp.py --smoke` and the M2 contained write verification.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import anyio
import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import luma_mcp as L  # noqa: E402

# A fake key used only in these tests — never a real credential.
KEY = "lu_test_secret_key_ABC123XYZ"

READ_TOOLS = {"get_self", "list_events", "get_event",
              "lookup_event", "list_guests", "get_guest"}
WRITE_TOOLS = {"create_event", "update_event", "create_upload_url"}


def client_with(handler) -> L.LumaClient:
    """A LumaClient backed by a mocked httpx transport."""
    http = httpx.Client(
        base_url=L.BASE_URL,
        headers={"x-luma-api-key": KEY},
        transport=httpx.MockTransport(handler),
    )
    return L.LumaClient(KEY, http_client=http)


def ok(body):
    """A handler that always returns 200 with `body` as JSON."""
    return lambda request: httpx.Response(200, json=body)


def capture_client(captured):
    """A LumaClient whose transport records the outgoing method + JSON body into
    `captured`, then returns a benign 200. Lets write tests assert what we send."""
    def handler(request):
        captured["method"] = request.method
        captured["body"] = json.loads(request.content) if request.content else {}
        return httpx.Response(200, json={"id": "evt-new"})
    return client_with(handler)


# ---- tool registration (flag-off = no write tools; M1 has none at all) ----

def test_only_read_tools_registered():
    names = {t.name for t in anyio.run(L.mcp.list_tools)}
    assert names == READ_TOOLS
    assert not (names & WRITE_TOOLS)


# ---- header injection ----

def test_client_injects_api_key_header():
    c = L.LumaClient(KEY)
    assert c._client.headers["x-luma-api-key"] == KEY


# ---- envelope shape: _provenance present, next_cursor/has_more passthrough ----

def test_envelope_shape_and_passthrough(monkeypatch):
    body = {"entries": [{"api_id": "evt-1"}], "has_more": True, "next_cursor": "CUR"}
    monkeypatch.setattr(L, "_client", lambda: client_with(ok(body)))
    out = L.list_events(pagination_limit=1)
    # Luma fields returned verbatim
    assert out["entries"] == [{"api_id": "evt-1"}]
    assert out["has_more"] is True
    assert out["next_cursor"] == "CUR"          # passthrough for caller-driven paging
    # provenance stamp
    assert out["_provenance"] == {
        "tier": "T1",
        "source": "public-api.luma.com/v1/calendars/events/list",
    }


def test_provenance_tiers(monkeypatch):
    # guests -> T3 (PII)
    monkeypatch.setattr(L, "_client",
                        lambda: client_with(ok({"entries": [], "has_more": False,
                                                 "next_cursor": None})))
    assert L.list_guests(event_id="evt-1")["_provenance"]["tier"] == "T3"
    assert L.get_guest(event_id="evt-1", id="gst-1")["_provenance"]["tier"] == "T3"
    # lookup -> T2 (may reference another calendar / external platform)
    monkeypatch.setattr(L, "_client", lambda: client_with(ok({"event": None})))
    assert L.lookup_event(event_id="evt-demo0002",
                          platform="luma")["_provenance"]["tier"] == "T2"
    monkeypatch.setattr(L, "_client", lambda: client_with(ok({"name": "X"})))
    assert L.get_self()["_provenance"]["tier"] == "T1"


# ---- pagination walk ----

def test_pagination_walk():
    pages = {
        None: {"entries": [{"api_id": "e1"}], "has_more": True, "next_cursor": "c1"},
        "c1": {"entries": [{"api_id": "e2"}], "has_more": True, "next_cursor": "c2"},
        "c2": {"entries": [{"api_id": "e3"}], "has_more": False, "next_cursor": None},
    }

    def handler(request):
        cur = request.url.params.get("pagination_cursor")
        return httpx.Response(200, json=pages[cur])

    c = client_with(handler)
    seen, cursor = [], None
    while True:
        page = c.get("/v1/calendars/events/list",
                     L._params(pagination_cursor=cursor, pagination_limit=1))
        seen += [e["api_id"] for e in page["entries"]]
        if not page["has_more"]:
            break
        cursor = page["next_cursor"]
    assert seen == ["e1", "e2", "e3"]


# ---- 429 retry honoring Retry-After ----

def test_429_retry_then_success():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"},
                                  json={"error": "rate limited"})
        return httpx.Response(200, json={"ok": True})

    out = client_with(handler).get("/v1/users/get-self")
    assert out == {"ok": True}
    assert calls["n"] == 2          # exactly one retry


def test_429_gives_up_after_single_retry():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(429, headers={"Retry-After": "0"},
                              json={"error": "rate limited"})

    with pytest.raises(L.LumaAPIError) as ei:
        client_with(handler).get("/v1/users/get-self")
    assert calls["n"] == 2          # tried once, retried once, then raised
    assert "429" in str(ei.value)


# ---- error passthrough: Luma's error text is surfaced (nonexistent ID) ----

def test_luma_error_surfaced_untouched():
    def handler(request):
        return httpx.Response(404, json={"message": "Event not found"})

    with pytest.raises(L.LumaAPIError) as ei:
        client_with(handler).get("/v1/events/get", L._params(event_id="evt-nope"))
    msg = str(ei.value)
    assert "404" in msg
    assert "Event not found" in msg     # Luma's own body, surfaced


# ---- key redaction (§9: actively try to leak one) ----

def test_key_redacted_from_error_message_and_repr():
    # Adversarial: force a body that (impossibly) echoes the key back.
    def handler(request):
        return httpx.Response(403, text=f"forbidden; x-luma-api-key={KEY} echoed")

    with pytest.raises(L.LumaAPIError) as ei:
        client_with(handler).get("/v1/users/get-self")
    msg, rep = str(ei.value), repr(ei.value)
    assert KEY not in msg
    assert KEY not in rep
    assert "***REDACTED***" in msg      # redaction actually fired
    assert "403" in msg                 # status still surfaced


def test_transport_error_wrapped_and_redacted():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    c = client_with(handler)
    with pytest.raises(L.LumaAPIError) as ei:
        c.get("/v1/users/get-self")
    assert KEY not in str(ei.value)
    assert KEY not in repr(ei.value)


# ---- write-tier registration is gated by LUMA_ENABLE_WRITES (§4) ----

def test_write_tools_registered_only_when_flag_enabled():
    # flag off (this process): the three W tools are NOT registered...
    off = {t.name for t in anyio.run(L.mcp.list_tools)}
    assert not (off & WRITE_TOOLS)
    # ...but the functions stay importable/callable (so these tests can call them).
    assert all(callable(getattr(L, n)) for n in WRITE_TOOLS)
    # flag on (fresh process): all three ARE registered.
    scripts = str(Path(L.__file__).resolve().parent)
    code = (f"import sys, anyio; sys.path.insert(0, {scripts!r}); "
            "import luma_mcp as M; "
            "print(sorted(t.name for t in anyio.run(M.mcp.list_tools)))")
    r = subprocess.run([sys.executable, "-c", code],
                       env={**os.environ, "LUMA_ENABLE_WRITES": "1"},
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    for w in WRITE_TOOLS:
        assert w in r.stdout


# ---- write-tier safe defaults (build plan §1, §3) ----

def test_create_event_defaults_to_private(monkeypatch):
    cap = {}
    monkeypatch.setattr(L, "_client", lambda: capture_client(cap))
    out = L.create_event(name="zz-api-test",
                         start_at="2027-01-01T18:00:00.000Z",
                         timezone="America/New_York")
    assert cap["method"] == "POST"
    assert cap["body"]["visibility"] == "private"      # default unlisted (§3)
    assert cap["body"]["name"] == "zz-api-test"
    assert out["_provenance"] == {
        "tier": "T1", "source": "public-api.luma.com/v1/events/create"}


def test_update_event_suppresses_notifications_by_default(monkeypatch):
    cap = {}
    monkeypatch.setattr(L, "_client", lambda: capture_client(cap))
    L.update_event(event_id="evt-x", name="new title")
    assert cap["body"]["suppress_notifications"] is True   # no guest comms (§1)
    assert cap["body"]["event_id"] == "evt-x"
    assert cap["body"]["name"] == "new title"
    # an explicit opt-in to notify is still possible
    cap2 = {}
    monkeypatch.setattr(L, "_client", lambda: capture_client(cap2))
    L.update_event(event_id="evt-x", suppress_notifications=False)
    assert cap2["body"]["suppress_notifications"] is False


def test_create_upload_url_posts(monkeypatch):
    cap = {}
    monkeypatch.setattr(L, "_client", lambda: capture_client(cap))
    out = L.create_upload_url(content_type="image/png")
    assert cap["method"] == "POST"
    assert cap["body"]["content_type"] == "image/png"
    assert out["_provenance"]["source"].endswith("/v1/images/create-upload-url")


# ---- POST errors are redacted too (writes are the sensitive path) ----

def test_post_error_redacted():
    def handler(request):
        return httpx.Response(400, text=f"bad request; key={KEY}")

    with pytest.raises(L.LumaAPIError) as ei:
        client_with(handler).post("/v1/events/create", {"name": "x"})
    assert KEY not in str(ei.value)
    assert "***REDACTED***" in str(ei.value)
    assert "400" in str(ei.value)
