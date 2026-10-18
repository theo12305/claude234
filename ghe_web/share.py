"""A project packed into a link: the project file, compressed and URL-safe, so a colleague opens the same
inputs from one link. Nothing is stored on the server; the link itself carries the project.

Hourly demand files (8760 values per column) would make the link too long for e-mail and chat programs, so they
are left out and the colleague uploads the file again.
"""
from __future__ import annotations

import base64
import json
import zlib

PARAM = "p"
MAX_PROJECT_BYTES = 2_000_000  # a project file is a few kB; this stops a crafted link from inflating to gigabytes
DROPPED = {("load", "profile")}  # (section, value) left out of links


def encode(project_json: str) -> tuple[str, bool]:
    """The link text for a project file, and whether something was left out."""
    data = json.loads(project_json)
    dropped = False
    for section, value in DROPPED:
        values = data.get("sections", {}).get(section, {}).get("values", {})
        if value in values:
            del values[value]
            dropped = True
    raw = json.dumps(data, separators=(",", ":")).encode()
    packed = base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode().rstrip("=")
    return packed, dropped


def decode(packed: str) -> str:
    """The project file from link text. Raises ValueError for anything that is not a packed project."""
    try:
        raw = base64.urlsafe_b64decode(packed + "=" * (-len(packed) % 4))
        inflater = zlib.decompressobj()
        text = inflater.decompress(raw, MAX_PROJECT_BYTES)
        if inflater.unconsumed_tail:
            raise ValueError("too large")
        return text.decode()
    except (ValueError, zlib.error, UnicodeDecodeError) as exc:
        raise ValueError(str(exc)) from exc


def link(base_url: str, project_json: str) -> tuple[str, bool]:
    packed, dropped = encode(project_json)
    return f"{base_url.split('?')[0].rstrip('/')}/?{PARAM}={packed}", dropped
