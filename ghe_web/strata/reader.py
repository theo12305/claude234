"""Reading a borehole log that exists as text: copied from a portal, the text layer of a PDF, or a web page a state
service links to. Rules only, so it is free and works offline; pictures and scans cannot be read (no paid service).

Every result is a ``Borehole`` like an uploaded log, so the user checks it in a table before it is used.
"""
from __future__ import annotations

import html
import io
import re

from ..i18n import t
from ..siteplan import lookup
from ..siteplan.lookup import LookupError_
from . import rocks
from .predict import Borehole, LogLayer

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


def read_file(filename: str, content: bytes, x: float, y: float) -> Borehole:
    """A log from an uploaded text file or PDF with a text layer."""
    ext = filename.rsplit(".", 1)[-1].lower()
    source = t("read from {name}", name=filename)
    if ext == "pdf":
        text = text_from_pdf(content)
        if not text.strip():
            raise ReadError(t("This PDF is a scan without text, so it cannot be read. Type its layers into the "
                              "box instead."))
        return layers_from_text(text, filename, x, y, source)
    if ext in IMAGE_TYPES:
        raise ReadError(t("Pictures cannot be read for free. Type the layers into the box instead."))
    return layers_from_text(content.decode("utf-8", errors="replace"), filename, x, y, source)


def html_text(page: str) -> str:
    """The visible text of a web page, one table row or paragraph per line."""
    page = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    page = re.sub(r"(?i)<br\s*/?>|</(tr|p|div|li|h\d)>", "\n", page)
    page = re.sub(r"(?i)</t[dh]>", "\t", page)
    page = re.sub(r"<[^>]+>", " ", page)
    return "\n".join(re.sub(r"[ \xa0]+", " ", line).strip() for line in html.unescape(page).split("\n"))


def read_url(url: str, name: str, x: float, y: float, source: str) -> Borehole:
    """A log behind a link of a state service, if it is a web page or PDF with text."""
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
            return layers_from_text(html_text(r.text), name, x, y, source)
        except ReadError:
            raise ReadError(t("The linked page has no layer list the app can read. Open the link instead.")) from None
    if ext != "pdf":
        raise ReadError(t("The log behind this link is a picture, which cannot be read for free. Open the link "
                          "and type its layers into the box."))
    hole = read_file(f"{name}.pdf", r.content, x, y)
    hole.name, hole.source = name, source
    return hole
