#!/usr/bin/env python3
"""
mermaid_link.py — Generate a Mermaid Live Editor URL from diagram code.

Usage:
    # From a file:
    python3 mermaid_link.py diagram.mmd

    # From a string argument:
    python3 mermaid_link.py "flowchart TD\n    A --> B"

    # From stdin:
    cat diagram.mmd | python3 mermaid_link.py

Output:
    A clickable Mermaid Live Editor URL.
    Example: https://mermaid.live/edit#pako:eNpLykktLi4p...

Encoding details:
    Mermaid Live Editor uses pako.deflate (zlib format) + js-base64's fromUint8Array
    (URL-safe base64 without padding). Python equivalent:
      1. JSON.stringify the state object
      2. zlib.compress (produces zlib format with 2-byte header + Adler32 checksum)
      3. base64url-encode WITHOUT padding (rstrip '=')
"""

import sys
import json
import zlib
import base64
import os


def encode_mermaid_url(code: str) -> str:
    """
    Encode Mermaid diagram code as a Mermaid Live Editor URL.

    Matches the encoding used by mermaid-live-editor:
      - pako.deflate()     → Python: zlib.compress() [full zlib format, NOT raw deflate]
      - js-base64 encode   → Python: base64.urlsafe_b64encode().rstrip('=')
    """
    state = {
        "code": code,
        "mermaid": {"theme": "default"}
    }
    payload = json.dumps(state, separators=(",", ":"), ensure_ascii=False)

    # IMPORTANT: Keep the full zlib format (2-byte header + Adler32 checksum).
    # pako.deflate() uses zlib wrapping — do NOT strip header bytes.
    compressed = zlib.compress(payload.encode("utf-8"), level=9)

    # URL-safe base64 without padding (matches js-base64's fromUint8Array)
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")

    return f"https://mermaid.live/edit#pako:{encoded}"


def read_input() -> str:
    """Read diagram code from file, argument, or stdin."""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isfile(arg):
            with open(arg, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return arg.replace("\\n", "\n")
    else:
        return sys.stdin.read()


if __name__ == "__main__":
    code = read_input().strip()

    if not code:
        print("Error: No diagram code provided.", file=sys.stderr)
        sys.exit(1)

    url = encode_mermaid_url(code)
    print(url)
