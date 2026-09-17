#!/usr/bin/env python3
"""
Luma → HubSpot scaffolding builder.

Creates the HubSpot-side schema for the Luma event-registration integration:
two custom objects (Event, Event Registration), their properties, the new
contact properties, and the v4 labeled associations between them.

SAFETY
  - Defaults to DRY-RUN. Nothing is written until you pass --apply.
  - Refuses to run unless the connected portal matches --portal (default: the
    sandbox 12345679). Override intentionally with --allow-any-portal.

AUTH  (never commit these — .env is gitignored; HubSpot auto-deactivates tokens
       found in public repos, so keep them in the environment only)
  Reads a HubSpot bearer token + portal id from the environment / .env. The token
  can be a Service Key (beta; recommended for new system-to-system work) OR a
  legacy private-app token — both are `pat-na1-...` bearer tokens, used identically:
    HUBSPOT_API_KEY=pat-na1-...        # (or HUBSPOT_SERVICE_KEY) SANDBOX token
    HUBSPOT_SANDBOX_PORTAL_ID=12345679 # (or HUBSPOT_PORTAL_ID) optional; guard also reads portal from the API
  Scopes required (same for either credential type):
    crm.schemas.custom.read, crm.schemas.custom.write,
    crm.objects.custom.read, crm.objects.custom.write,
    crm.schemas.contacts.read, crm.schemas.contacts.write

USAGE
    pip install requests            # already present in this repo's env
    # 1) see what it would do (safe):
    python3 scripts/hubspot/luma_scaffold.py
    # 2) build it for real against the sandbox:
    python3 scripts/hubspot/luma_scaffold.py --apply

NOTES / KNOWN LIMITS
  - Association *limits* (max = 1 on Registration→Contact and Registration→Event)
    are NOT set here — set them in Settings → Objects → Associations, or via the
    v4 configurations endpoint.
  - Idempotent at the object/property/label level (skips what already exists).
    If an object exists but is missing a property, re-running adds the property
    to that object's default group.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import fleet_paths  # noqa: E402

import requests

BASE = "https://api.hubapi.com"
SANDBOX_PORTAL_ID = "12345679"  # GTM Fleet marketing sandbox (app.hubspot.com/home?portalId=12345679)
PROD_PORTAL_ID = "12345678"      # guardrail: never scaffold production by accident

# Object internal names (proposals; align with the gtm-fleet_* house convention).
EVENT = "gtm_event"
REG = "gtm_event_registration"

# ---------------------------------------------------------------------------
# Declarative spec
# ---------------------------------------------------------------------------

def _enum(options):
    return [
        {"label": lbl, "value": val, "displayOrder": i, "hidden": False}
        for i, (val, lbl) in enumerate(options)
    ]


EVENT_PROPERTIES = [
    {"name": "external_event_id", "label": "External Event ID", "type": "string", "fieldType": "text",
     "hasUniqueValue": True,
     "description": "Luma event id; unique key joining registrations + the native Marketing Event mirror."},
    {"name": "event_name", "label": "Event Name", "type": "string", "fieldType": "text"},
    {"name": "event_format", "label": "Event Format", "type": "enumeration", "fieldType": "select",
     "options": _enum([("in_person", "In Person"), ("virtual", "Virtual"), ("hybrid", "Hybrid")])},
    {"name": "event_type", "label": "Event Type", "type": "enumeration", "fieldType": "select",
     "options": _enum([("dinner", "Dinner"), ("webinar", "Webinar"), ("workshop", "Workshop"),
                       ("meetup", "Meetup"), ("conference", "Conference"), ("other", "Other")])},
    {"name": "event_start", "label": "Event Start", "type": "datetime", "fieldType": "date"},
    {"name": "event_end", "label": "Event End", "type": "datetime", "fieldType": "date"},
    {"name": "event_timezone", "label": "Event Timezone", "type": "string", "fieldType": "text"},
    {"name": "event_url", "label": "Event URL", "type": "string", "fieldType": "text"},
    {"name": "meeting_url", "label": "Meeting URL", "type": "string", "fieldType": "text"},
    {"name": "venue_name", "label": "Venue Name", "type": "string", "fieldType": "text"},
    {"name": "venue_full_address", "label": "Venue Full Address", "type": "string", "fieldType": "text"},
    {"name": "venue_city", "label": "Venue City", "type": "string", "fieldType": "text"},
    {"name": "venue_region", "label": "Venue Region", "type": "string", "fieldType": "text"},
    {"name": "venue_country", "label": "Venue Country", "type": "string", "fieldType": "text"},
]

REG_PROPERTIES = [
    {"name": "registration_id", "label": "Registration ID", "type": "string", "fieldType": "text",
     "hasUniqueValue": True,
     "description": "Deterministic reg_ surrogate id derived from guest_id (sha256 -> base62); "
                    "the primary display id. guest_id remains the dedup/idempotency key."},
    {"name": "guest_id", "label": "Guest ID", "type": "string", "fieldType": "text",
     "hasUniqueValue": True,
     "description": "Luma guest id; unique per guest-per-event. Idempotency key."},
    {"name": "event_external_id", "label": "Event External ID", "type": "string", "fieldType": "text",
     "description": "= gtm_event.external_event_id (the Luma event id)."},
    {"name": "registration_status", "label": "Registration Status", "type": "enumeration", "fieldType": "select",
     "options": _enum([("invited", "Invited"), ("registered", "Registered"), ("approved", "Approved"),
                       ("attended", "Attended"), ("attended_on_demand", "Attended (On-Demand)"),
                       ("no_show", "No-Show"), ("canceled", "Canceled")])},
    {"name": "registered_at", "label": "Registered At", "type": "datetime", "fieldType": "date"},
    {"name": "approved_at", "label": "Approved At", "type": "datetime", "fieldType": "date"},
    {"name": "checked_in_at", "label": "Checked In At", "type": "datetime", "fieldType": "date"},
    {"name": "ticket_type", "label": "Ticket Type", "type": "string", "fieldType": "text"},
    {"name": "ticket_amount_cents", "label": "Ticket Amount (cents)", "type": "number", "fieldType": "number"},
    {"name": "linkedin_answer", "label": "LinkedIn", "type": "string", "fieldType": "text"},
    {"name": "top_of_mind", "label": "Top of Mind", "type": "string", "fieldType": "textarea"},
    {"name": "dietary_restrictions", "label": "Dietary Restrictions", "type": "string", "fieldType": "text"},
    {"name": "answers_json", "label": "Answers (raw JSON)", "type": "string", "fieldType": "textarea"},
    {"name": "question_ids", "label": "Question IDs", "type": "string", "fieldType": "text",
     "description": "Luma question ids alongside answers (labels collide; ids kept for traceability)."},
    {"name": "platform", "label": "Platform", "type": "string", "fieldType": "text",
     "description": "Source platform, e.g. Luma."},
]

# New CONTACT properties (generic / source-agnostic; reuse standard props otherwise).
CONTACT_PROPERTIES = [
    {"name": "most_recent_event_id", "label": "Most Recent Event ID", "type": "string", "fieldType": "text"},
    {"name": "most_recent_event_registered_at", "label": "Most Recent Event Registered At",
     "type": "datetime", "fieldType": "date"},
    {"name": "most_recent_event_platform", "label": "Most Recent Event Platform",
     "type": "string", "fieldType": "text", "description": "e.g. Luma, Zoom."},
    {"name": "additional_emails", "label": "Additional Emails", "type": "string", "fieldType": "textarea",
     "description": "Captured work/alternate addresses (mirror of hs_additional_emails). Consumed by the "
                    "email-routing project; this integration does not repoint the primary email."},
    {"name": "luma_user_id", "label": "Luma User ID", "type": "string", "fieldType": "text",
     "description": "Stable per-person Luma id; secondary identity key."},
]

OBJECT_SPECS = {
    EVENT: {
        "labels": {"singular": "Event", "plural": "Events"},
        "primaryDisplayProperty": "event_name",
        "requiredProperties": ["external_event_id", "event_name"],
        "searchableProperties": ["external_event_id", "event_name"],
        "secondaryDisplayProperties": ["event_type", "event_format"],
        "properties": EVENT_PROPERTIES,
    },
    REG: {
        "labels": {"singular": "Event Registration", "plural": "Event Registrations"},
        "primaryDisplayProperty": "registration_id",
        "requiredProperties": ["registration_id", "guest_id", "event_external_id"],
        "searchableProperties": ["registration_id", "guest_id", "event_external_id"],
        "secondaryDisplayProperties": ["guest_id", "registration_status"],
        "properties": REG_PROPERTIES,
    },
}

# v4 labeled associations (limits set separately — see module docstring / build guide).
ASSOCIATIONS = [
    {"from": REG, "to": "contacts", "label": "Registrant"},
    {"from": REG, "to": EVENT, "label": "Registered For Event"},
]

CONTACT_GROUP = "contactinformation"  # always-present standard group


# ---------------------------------------------------------------------------
# HTTP + env
# ---------------------------------------------------------------------------

class Client:
    def __init__(self, token: str, apply: bool):
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        self.apply = apply

    def get(self, path, ok=(200,)):
        r = self.s.get(BASE + path, timeout=30)
        return r

    def post(self, path, body):
        if not self.apply:
            print(f"    DRY-RUN POST {path}\n      {json.dumps(body)[:400]}")
            return None
        r = self.s.post(BASE + path, data=json.dumps(body), timeout=30)
        if r.status_code >= 300:
            raise SystemExit(f"POST {path} failed [{r.status_code}]: {r.text}")
        return r.json()


def load_env():
    """Populate os.environ from a local .env if present (no dependency required)."""
    env = fleet_paths.FLEET_ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


# ---------------------------------------------------------------------------
# Idempotent operations
# ---------------------------------------------------------------------------

def existing_schemas(c: Client) -> dict:
    r = c.get("/crm/v3/schemas")
    if r.status_code != 200:
        raise SystemExit(f"Could not list schemas [{r.status_code}]: {r.text}")
    out = {}
    for s in r.json().get("results", []):
        # match by the object's name (fullyQualifiedName looks like p<portal>_<name>)
        out[s.get("name")] = s
        out[s.get("fullyQualifiedName")] = s
    return out


def ensure_object(c: Client, name: str, spec: dict, schemas: dict):
    if name in schemas:
        # v3 properties endpoints can't resolve a custom object by its bare name —
        # use the objectTypeId (e.g. 2-00000001) HubSpot assigned at creation.
        object_type = schemas[name].get("objectTypeId", name)
        print(f"  ✓ object '{name}' already exists — reconciling properties")
        _reconcile_props(c, object_type, spec["properties"])
        return
    print(f"  + creating object '{name}' with {len(spec['properties'])} properties")
    body = {"name": name, **{k: spec[k] for k in spec if k != "properties"}, "properties": spec["properties"]}
    c.post("/crm/v3/schemas", body)


def _existing_prop_names(c: Client, object_type: str) -> set:
    r = c.get(f"/crm/v3/properties/{object_type}")
    if r.status_code != 200:
        return set()
    return {p["name"] for p in r.json().get("results", [])}


def _reconcile_props(c: Client, object_type: str, props: list):
    have = _existing_prop_names(c, object_type)
    # find/choose a group for this custom object
    for p in props:
        if p["name"] in have:
            continue
        print(f"    + property {object_type}.{p['name']}")
        c.post(f"/crm/v3/properties/{object_type}", p)


def ensure_contact_props(c: Client):
    have = _existing_prop_names(c, "contacts")
    for p in CONTACT_PROPERTIES:
        if p["name"] in have:
            print(f"  ✓ contact.{p['name']} exists")
            continue
        print(f"  + contact.{p['name']}")
        c.post("/crm/v3/properties/contacts", {**p, "groupName": CONTACT_GROUP})


def ensure_associations(c: Client):
    # v4 associations can't infer a custom object from its name — resolve custom
    # object names to their objectTypeId (e.g. 2-00000002); standard object names
    # (e.g. "contacts") are not in the schema listing and pass through unchanged.
    schemas = existing_schemas(c)

    def resolve(t):
        s = schemas.get(t)
        return s.get("objectTypeId") if s else t

    for a in ASSOCIATIONS:
        path = f"/crm/v4/associations/{resolve(a['from'])}/{resolve(a['to'])}/labels"
        r = c.get(path)
        labels = [x.get("label") for x in r.json().get("results", [])] if r.status_code == 200 else []
        if a["label"] in labels:
            print(f"  ✓ association {a['from']} → {a['to']} '{a['label']}' exists")
            continue
        print(f"  + association {a['from']} → {a['to']} '{a['label']}'")
        c.post(path, {"label": a["label"], "name": a["label"].lower().replace(" ", "_")})


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    load_env()
    ap = argparse.ArgumentParser(description="Build the Luma→HubSpot custom-object scaffolding.")
    ap.add_argument("--apply", action="store_true", help="actually write (default: dry-run)")
    ap.add_argument("--portal",
                    default=(os.environ.get("HUBSPOT_SANDBOX_PORTAL_ID")
                             or os.environ.get("HUBSPOT_PORTAL_ID") or SANDBOX_PORTAL_ID),
                    help="expected portal id guard")
    ap.add_argument("--allow-any-portal", action="store_true", help="skip the portal guard (dangerous)")
    args = ap.parse_args()

    token = os.environ.get("HUBSPOT_API_KEY") or os.environ.get("HUBSPOT_SERVICE_KEY")
    if not token or token.startswith("your_"):
        raise SystemExit("No token set. Put a SANDBOX Service Key or private-app token in "
                         "HUBSPOT_API_KEY (or HUBSPOT_SERVICE_KEY) — see module docstring.")

    c = Client(token, apply=args.apply)

    # portal guard
    r = c.get("/account-info/v3/details")
    if r.status_code != 200:
        raise SystemExit(f"Could not read account info [{r.status_code}]: {r.text}")
    portal = str(r.json().get("portalId"))
    print(f"Connected portal: {portal}  (mode: {'APPLY' if args.apply else 'DRY-RUN'})")
    if portal == PROD_PORTAL_ID and not args.allow_any_portal:
        raise SystemExit(f"Refusing to run against PRODUCTION portal {PROD_PORTAL_ID}. Use the sandbox.")
    if portal != args.portal and not args.allow_any_portal:
        raise SystemExit(f"Connected portal {portal} != expected {args.portal}. "
                         f"Point HUBSPOT_API_KEY at the sandbox, or pass --portal {portal} / --allow-any-portal.")

    schemas = existing_schemas(c)
    print("\n[1/4] Custom object: Event")
    ensure_object(c, EVENT, OBJECT_SPECS[EVENT], schemas)
    print("\n[2/4] Custom object: Event Registration")
    ensure_object(c, REG, OBJECT_SPECS[REG], schemas)
    print("\n[3/4] Contact properties")
    ensure_contact_props(c)
    print("\n[4/4] Associations (labels; set max=1 limits in the UI — see build guide §4)")
    ensure_associations(c)

    print("\nDone." if args.apply else "\nDry-run complete. Re-run with --apply to build.")


if __name__ == "__main__":
    main()
