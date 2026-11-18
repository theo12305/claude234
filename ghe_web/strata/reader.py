"""Reading a borehole log that exists as text: copied from a portal, the text layer of a PDF, a web page a state
service links to, or a picture or scan of a Schichtenverzeichnis through optical character recognition (Tesseract,
free and open source, installed on the server). Rules only, no paid service.

Every result is a ``Borehole`` like an uploaded log, so the user checks it in a table before it is used.
"""
from __future__ import annotations

import html
import io
import os
import re

from ghe_web.i18n import t
from ghe_web.siteplan import lookup
from ghe_web.siteplan.lookup import LookupError_
from ghe_web.strata import rocks
from ghe_web.strata.predict import Borehole, LogLayer

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


# ---------------------------------------------------------------- pictures (OCR)

# A depth as the log prints it: "13,30" or, when the recognition lost the comma, "1330" (two decimals)
_OCR_DEPTH = re.compile(r"^(\d{1,3})[,.](\d{2})(?!\d)|^(\d{3,5})(?![\d,.])")
_OCR_JUNK = re.compile(r"^[\s|\[\]=_.:;,'\"`´‚„~—–-]+|^[a-zA-Z]\s+(?=\d)")
_OCR_SCALE = re.compile(r"^\d{1,4}[,.]\d(?!\d)[.\s]*")  # height scale of the column: "25,0"
_OCR_STOP = re.compile(r"^(höhenma|hohenma|horizontalma|bezirk|ortsteil|lage:|rechtswert|hochwert|bohrbeginn|"
                       r"bohrverfahren|tk ?25|landkreis|gemeinde)", re.IGNORECASE)


def _ocr_depth(line: str, top: float = 0.0, limit: float = 2000.0) -> tuple[float, str] | None:
    """(depth, rest of the line) when the line starts with a layer bottom, after the recognition's stray marks
    and the height scale are removed. A number whose comma was lost ("1160") is read with two decimals, or with
    one more digit cut off when that is the only reading between ``top`` and ``limit`` ("12500": 12.50)."""
    for _ in range(3):
        line = _OCR_SCALE.sub("", _OCR_JUNK.sub("", line))
    m = _OCR_DEPTH.match(line)
    if not m:
        return None
    if m.group(3):
        digits = m.group(3)
        value = float(digits[:-2] + "." + digits[-2:])
        if not top < value <= limit and len(digits) >= 4:
            value = float(digits[:-3] + "." + digits[-3:-1])
    else:
        value = float(f"{m.group(1)}.{m.group(2)}")
    rest = line[m.end():].strip(" |_.:;-—–[]=")
    return value, rest


def _clean_ocr_description(text: str) -> str:
    """Drops what the recognition read from the drawn column in front of a description ("as | 9 Sand", "B2 B2
    Sand", "© 0® Kies"): leading marks, numbers and short fragments that are not a rock name themselves."""
    words = text.split()
    while words:
        letters = re.sub(r"[^A-Za-zÄÖÜäöüß]", "", words[0])
        if (len(letters) > 3 or (len(letters) == 3 and rocks.classify(letters) != rocks.UNKNOWN)) and \
                re.fullmatch(r"[(\"„“]?[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß(),.;/-]*", words[0]):
            break
        words.pop(0)
    return " ".join(words)


def layers_from_ocr(text: str, name: str = "Log", x: float = 0.0, y: float = 0.0, source: str = "picture",
                    max_depth: float | None = None) -> Borehole:
    """The layers of a Schichtenverzeichnis read from a picture: the depth of each layer bottom at the start of a
    line, the description after it. Recognition errors are tolerated where they are typical (a lost comma in
    "1160", stray strokes of the drawn column, the height scale next to the depths, a description that wraps onto
    the line of its depth). The result always goes to the user's check table."""
    layers: list[LogLayer] = []
    pending = ""  # description lines that came before their depth
    top = 0.0
    started = False
    for raw in text.replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if started and _OCR_STOP.match(line):
            break
        limit = (max_depth + 0.5) if max_depth else 2000.0
        found = _ocr_depth(line, top, limit)
        if found is None:
            words = re.sub(r"[^A-Za-zÄÖÜäöüß ]", "", line)
            if started and len(words.strip()) >= 8 and rocks.classify(line) != rocks.UNKNOWN:
                pending = f"{pending} {line}".strip()
            elif started and pending and line[:1].islower():
                pending = f"{pending} {line}".strip()
            continue
        bottom, rest = found
        if bottom <= top or bottom > limit:
            continue
        if re.match(r"m\s*(?:NHN|NN|HN|ü|u\.)", rest):  # a height (Geländeoberkante), not a layer
            continue
        desc = _clean_ocr_description(f"{pending} {rest}".strip() if pending else rest)
        if not re.search(r"[A-Za-zÄÖÜäöü]{3}", desc) or (not started and rocks.classify(desc) == rocks.UNKNOWN):
            continue
        layers.append(LogLayer(top, bottom, rocks.classify(desc), desc))
        top, pending, started = bottom, "", True
    if not layers:
        raise ReadError(t("No layers were recognised in the picture. Type the layers into the box, or try a "
                          "sharper picture of the Schichtenverzeichnis."))
    gw = _GW.search(text)
    return Borehole(name, x, y, layers, source, _f(gw.group(1)) if gw else None)


def ocr_available() -> bool:
    import shutil
    return shutil.which("tesseract") is not None


def ocr_text(content: bytes) -> str:
    """The text in a picture (PNG, JPEG, GIF, TIFF), German language model, page read as one column of lines."""
    import subprocess
    import tempfile
    if not ocr_available():
        raise ReadError(t("Text recognition (Tesseract) is not installed on this server, so pictures cannot be "
                          "read. Type the layers into the box instead."))
    from PIL import Image
    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except Exception as exc:
        raise ReadError(t("This picture could not be opened ({error}).", error=type(exc).__name__)) from exc
    image = image.convert("L")
    if image.width < 1600:  # small pictures read better enlarged
        f = 1600 / image.width
        image = image.resize((1600, int(image.height * f)), Image.LANCZOS)
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        image.save(tmp.name)
        try:
            # one thread per page: Tesseract's own parallelism makes it many times slower on small servers
            done = subprocess.run(["tesseract", tmp.name, "-", "-l", "deu", "--psm", "4"], capture_output=True,
                                  text=True, timeout=90, env={**os.environ, "OMP_THREAD_LIMIT": "1"})
        except subprocess.TimeoutExpired as exc:
            raise ReadError(t("Reading the picture took too long.")) from exc
    return done.stdout


def read_picture(content: bytes, name: str, x: float, y: float, source: str, max_depth: float | None = None
                 ) -> Borehole:
    return layers_from_ocr(ocr_text(content), name, x, y, source, max_depth)


# ---------------------------------------------------------------- log columns as PDF (GeODin)

_COLUMN_DEPTH = re.compile(r"(\d{1,4},\d{2})")


def layers_from_column(text: str, name: str = "Log", x: float = 0.0, y: float = 0.0, source: str = "PDF"
                       ) -> Borehole:
    """The layers of a drawn log column exported as PDF (GeODin portals, e.g. Schleswig-Holstein): the text layer
    has the rock names and the layer boundaries as separate words in drawing order. The boundaries are the rising
    depths, the names fill the intervals between them in the same order."""
    head = re.split(r"\n\s*(?:-?\d+\s*\n\s*)*m\s*NHN|Höhenmaßstab", text, maxsplit=1)[0]
    depths: list[float] = []
    names: list[str] = []
    for line in head.replace("\r", "").split("\n"):
        for part in re.split(_COLUMN_DEPTH, line.strip()):
            part = part.strip(" /|")
            if not part:
                continue
            if _COLUMN_DEPTH.fullmatch(part):
                value = _f(part)
                if not depths or value > depths[-1]:
                    depths.append(value)
            elif re.search(r"[A-Za-zÄÖÜäöü]{3}", part):
                names.append(part)
    if depths and depths[0] > 0:
        depths.insert(0, 0.0)
    if len(depths) < 2 or len(names) != len(depths) - 1:
        raise ReadError(t("The log column could not be split into layers ({n} names, {m} depths).",
                          n=len(names), m=max(len(depths) - 1, 0)))
    layers = [LogLayer(a, b, rocks.classify(n), n) for a, b, n in zip(depths, depths[1:], names)]
    return Borehole(name, x, y, layers, source)


def pdf_images(content: bytes) -> list[bytes]:
    """The pictures inside a scanned PDF, page by page (a scan is one picture per page)."""
    from pypdf import PdfReader
    out = []
    try:
        for page in PdfReader(io.BytesIO(content)).pages[:6]:
            for image in page.images:
                out.append(image.data)
    except Exception:  # noqa: BLE001 - a broken PDF just has no pictures to read
        return out
    return out


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
        if not text.strip():  # a scan: read its pictures
            text = "\n".join(ocr_text(image) for image in pdf_images(content))
            if not text.strip():
                raise ReadError(t("This PDF is a scan and no text was recognised in it. Type its layers into the "
                                  "box instead."))
            return layers_from_ocr(text, filename, x, y, source)
        return layers_from_text(text, filename, x, y, source)
    if ext in IMAGE_TYPES or ext in ("tif", "tiff", "bmp"):
        return read_picture(content, filename, x, y, source)
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
    if ext in IMAGE_TYPES or kind.startswith("image/"):
        return read_picture(r.content, name, x, y, source)
    if ext != "pdf":
        raise ReadError(t("The log behind this link could not be read. Open the link and type its layers into "
                          "the box."))
    hole = read_file(f"{name}.pdf", r.content, x, y)
    hole.name, hole.source = name, source
    return hole


def read_service_log(url: str, kind: str, name: str, x: float, y: float, source: str,
                     max_depth: float | None = None) -> Borehole:
    """A log that a state service publishes as a picture or a log column PDF (see sources.readable_log)."""
    try:
        r = lookup._get(url, timeout=40)
    except LookupError_ as exc:
        raise ReadError(str(exc)) from exc
    if kind == "column":
        if not r.content.startswith(b"%PDF"):
            raise ReadError(t("The service did not return the log column."))
        hole = layers_from_column(text_from_pdf(r.content), name, x, y, source)
    else:
        if not (r.headers.get("Content-Type") or "").lower().startswith("image/"):
            raise ReadError(t("The service did not return the log sheet."))
        hole = read_picture(r.content, name, x, y, source, max_depth)
    if max_depth and hole.layers and hole.layers[-1].bottom > max_depth + 0.5:
        raise ReadError(t("The layers read go deeper than the borehole ({d:.1f} m); check the log by hand.",
                          d=max_depth))
    return hole
