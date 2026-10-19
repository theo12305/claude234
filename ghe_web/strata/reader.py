"""Reading a borehole log that only exists as text, a PDF or a picture (a scan, a screenshot of a state portal, the
log images of Brandenburg, Berlin or Niedersachsen), so nobody has to type the layers in.

- Text with depths (pasted from a portal, or the text layer of a PDF) is read with rules, free and offline.
- Pictures and scanned PDFs are read by Claude (Anthropic API). This needs an API key in the app's secrets
  (``ANTHROPIC_API_KEY``) and costs about one to three cents per log; without a key only text and text PDFs work.

Every result is a ``Borehole`` like an uploaded log, so the user checks it in a table before it is used.
"""
from __future__ import annotations

import base64
import html
import io
import json
import os
import re

from ..i18n import t
from ..siteplan import lookup
from ..siteplan.lookup import LookupError_
from . import rocks
from .predict import Borehole, LogLayer

MODEL = "claude-opus-5-5"
IMAGE_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif",
               "webp": "image/webp"}


class ReadError(RuntimeError):
    """The log could not be read; the message is meant for the user."""


# ---------------------------------------------------------------- text

_NUM = r"(\d{1,4}(?:[.,]\d{1,3})?)"
# "0,00 - 0,40 m  Mutterboden", "0.4–6.5 m: Sand", "von 6,50 bis 18,00 Kies"
_RANGE = re.compile(rf"^\s*(?:von\s+)?{_NUM}(?:\s*m)?(?:\s*(?:-|–|—|bis|;|\|)\s*|\s+){_NUM}\s*(?:m\b\.?)?\s*(?:u\.?\s*GOK|u\.?\s*GOF)?"
                    r"\s*[:;|\t]?\s*(.*)$", re.IGNORECASE)
# "bis 6,50 m  Sand" or "6,50 Sand" (only the bottom, as in most Schichtenverzeichnisse)
_BOTTOM = re.compile(rf"^\s*(?:bis\s+)?{_NUM}\s*(?:m\b\.?)?\s*(?:u\.?\s*GOK|u\.?\s*GOF)?\s*[:;|\t]?\s*([A-Za-zÄÖÜäöü].*)$",
                     re.IGNORECASE)
_GW = re.compile(rf"(?:grundwasser|gw|wasserspiegel|ruhewasserspiegel|groundwater)\D{{0,25}}{_NUM}\s*m",
                 re.IGNORECASE)


def _f(text: str) -> float:
    return float(text.replace(",", "."))


def layers_from_text(text: str, name: str = "Log", x: float = 0.0, y: float = 0.0, source: str = "text"
                     ) -> Borehole:
    """The layers of a log written as text, one layer per line, with the depths in metres at the start."""
    layers: list[LogLayer] = []
    top = 0.0
    pending = None  # a layer whose description continues on the next line
    for raw in text.replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = _RANGE.match(line)
        if m:
            a, b, desc = _f(m.group(1)), _f(m.group(2)), m.group(3).strip()
        else:
            m = _BOTTOM.match(line)
            if not m:
                if pending is not None and (pending[2].endswith((",", "-")) or line[0].islower()):  # continued
                    pending[2] = f"{pending[2]} {line}".strip()
                continue
            a, b, desc = top, _f(m.group(1)), m.group(2).strip()
        if b <= a or b > 5000 or (layers and a < layers[-1].bottom - 0.01):
            continue
        if pending is not None:
            layers.append(LogLayer(pending[0], pending[1], rocks.classify(pending[2]), pending[2]))
        pending = [a, b, desc]
        top = b
    if pending is not None:
        layers.append(LogLayer(pending[0], pending[1], rocks.classify(pending[2]), pending[2]))
    if not layers:
        raise ReadError(t("No layers found. Each layer needs its depth at the start of a line, e.g. "
                          "'0,40 - 6,50 m Sand, kiesig' or 'bis 6,50 m Sand'."))
    gw = _GW.search(text)
    return Borehole(name, x, y, layers, source, _f(gw.group(1)) if gw else None)


def text_from_pdf(content: bytes) -> str:
    """The text layer of a PDF ("" for a scan)."""
    from pypdf import PdfReader
    try:
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages[:20])
    except Exception as exc:  # pypdf raises many types for broken files
        raise ReadError(t("Could not open the PDF ({error}).", error=type(exc).__name__)) from exc


# ---------------------------------------------------------------- pictures (Claude)

def api_key() -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:  # no secrets file
        return None


def ai_available() -> bool:
    return bool(api_key())


SCHEMA = {
    "type": "object",
    "properties": {
        "readable": {"type": "boolean"},
        "name": {"type": "string"},
        "groundwater_m": {"type": ["number", "null"]},
        "note": {"type": "string"},
        "layers": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "top_m": {"type": "number"},
                "bottom_m": {"type": "number"},
                "description": {"type": "string"},
                "rock": {"type": "string", "enum": rocks.NAMES},
            },
            "required": ["top_m", "bottom_m", "description", "rock"],
            "additionalProperties": False,
        }},
    },
    "required": ["readable", "name", "groundwater_m", "note", "layers"],
    "additionalProperties": False,
}

PROMPT = """This is a borehole log from a German geological survey: a layer list (Schichtenverzeichnis), a drawn \
log column (Profilsäule) or a screenshot of a portal showing one. Read every layer from the top down.

For each layer give the top and bottom depth in metres below ground, the description as written (keep SEP 3 codes \
such as "mS,g" or "Tst"), and the rock type from the list that fits best for heat conduction. Use "Unknown" only \
when the description says nothing about the material. Depths in a log column are read from the depth scale; if \
only the bottom of each layer is given, the top is the bottom of the layer above (0 for the first).

Give the groundwater depth in metres below ground if the log shows one (Grundwasser, Ruhewasserspiegel, a water \
sign), else null. Use the borehole's name or number as name if one is shown, else "". Set readable to false and say \
why in note if this is not a borehole log or the layers cannot be read; otherwise put anything uncertain in note."""


def _client():
    import anthropic
    key = api_key()
    if not key:
        raise ReadError(t("Reading pictures needs an Anthropic API key in the app's secrets (ANTHROPIC_API_KEY). "
                          "Text and PDFs with text work without it."))
    return anthropic.Anthropic(api_key=key, timeout=120.0)


def _ask(block: dict) -> dict:
    import anthropic
    try:
        response = _client().beta.messages.create(
            model=MODEL, max_tokens=16000, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": [block, {"type": "text", "text": PROMPT}]}])
    except anthropic.AuthenticationError as exc:
        raise ReadError(t("The Anthropic API key in the app's secrets is not valid.")) from exc
    except anthropic.RateLimitError as exc:
        raise ReadError(t("Too many requests to the reading service; try again in a minute.")) from exc
    except anthropic.BadRequestError as exc:
        raise ReadError(t("The reading service refused the file: {error}", error=exc.message)) from exc
    except anthropic.APIStatusError as exc:
        raise ReadError(t("The reading service answered with error {code}.", code=str(exc.status_code))) from exc
    except anthropic.APIConnectionError as exc:
        raise ReadError(t("The reading service did not answer.")) from exc
    if response.stop_reason == "refusal":
        raise ReadError(t("The reading service declined this file."))
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except ValueError as exc:
        raise ReadError(t("The reading service gave no usable answer.")) from exc


def borehole_from_answer(data: dict, name: str, x: float, y: float, source: str) -> tuple[Borehole, list[str]]:
    """The checked layers of a reading-service answer."""
    if not data.get("readable", True) or not data.get("layers"):
        raise ReadError(t("No layers could be read: {why}", why=data.get("note") or "?"))
    layers, top = [], 0.0
    for item in sorted(data["layers"], key=lambda l: (l["top_m"], l["bottom_m"])):
        a, b = max(float(item["top_m"]), top), float(item["bottom_m"])
        if b <= a:
            continue
        rock = item["rock"] if item["rock"] in rocks.ROCKS or item["rock"] == rocks.UNKNOWN else rocks.UNKNOWN
        if rock == rocks.UNKNOWN:
            rock = rocks.classify(item["description"])
        layers.append(LogLayer(a, b, rock, item["description"]))
        top = b
    if not layers:
        raise ReadError(t("No layers could be read: {why}", why=data.get("note") or "?"))
    notes = [data["note"]] if data.get("note") else []
    gw = data.get("groundwater_m")
    return Borehole(data.get("name") or name, x, y, layers, source, float(gw) if gw else None), notes


def read_file(filename: str, content: bytes, x: float, y: float) -> tuple[Borehole, list[str]]:
    """A log from an uploaded file: text, PDF (text layer first, else as a scan) or picture."""
    ext = filename.rsplit(".", 1)[-1].lower()
    source = t("read from {name}", name=filename)
    if ext in ("txt", "text"):
        return layers_from_text(content.decode("utf-8", errors="replace"), filename, x, y, source), []
    if ext == "pdf":
        text = text_from_pdf(content)
        if text.strip():
            try:
                return layers_from_text(text, filename, x, y, source), []
            except ReadError:
                if not ai_available():
                    raise
        block = {"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                                  "data": base64.standard_b64encode(content).decode()}}
        return borehole_from_answer(_ask(block), filename, x, y, source)
    if ext in IMAGE_TYPES:
        block = {"type": "image", "source": {"type": "base64", "media_type": IMAGE_TYPES[ext],
                                               "data": base64.standard_b64encode(content).decode()}}
        return borehole_from_answer(_ask(block), filename, x, y, source)
    raise ReadError(t("Use a picture (PNG, JPG), a PDF or a text file."))


def html_text(page: str) -> str:
    """The visible text of a web page, one table row or paragraph per line."""
    page = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    page = re.sub(r"(?i)<br\s*/?>|</(tr|p|div|li|h\d)>", "\n", page)
    page = re.sub(r"(?i)</t[dh]>", "\t", page)
    page = re.sub(r"<[^>]+>", " ", page)
    return "\n".join(re.sub(r"[ \xa0]+", " ", line).strip() for line in html.unescape(page).split("\n"))


def read_url(url: str, name: str, x: float, y: float, source: str) -> tuple[Borehole, list[str]]:
    """A log behind a link of a state service (a picture or a PDF)."""
    try:
        r = lookup._get(url)
    except LookupError_ as exc:
        raise ReadError(str(exc)) from exc
    kind = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    ext = {v: k for k, v in IMAGE_TYPES.items()}.get(kind) or ("pdf" if kind == "application/pdf" else None)
    if ext is None:
        ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
    if kind == "text/html" or ext in ("html", "htm", "php", "aspx"):
        try:
            hole = layers_from_text(html_text(r.text), name, x, y, source)
            return hole, []
        except ReadError:
            pass
    if ext not in IMAGE_TYPES and ext != "pdf":
        raise ReadError(t("This link opens a web page, not a picture or PDF of the log. Take a screenshot of the "
                          "log and upload it."))
    hole, notes = read_file(f"{name}.{ext}", r.content, x, y)
    hole.name, hole.source = name, source
    return hole, notes
