"""Languages of the page, the PDF report and the Excel workbook.

The English text is the key: ``t("Borehole length")`` returns it in the current language. Translations live in
one dictionary per language (``i18n_de.py``); text without an entry stays English, so new text works before it is
translated. Values are passed as keywords and formatted after the lookup, with the number format of the language
(German: 1.234,5)::

    t("{n} boreholes of {length:.1f} m", n=12, length=98.25)   # "12 Sonden à 98,3 m"
    fmt("{x:,.0f} kWh", x=12345)                                 # "12.345 kWh", no translation

No web code here, so the reports and tests use it too. The language is stored per thread (each browser session
runs in its own thread), so two users can work in different languages at the same time.
"""
from __future__ import annotations

import contextvars
import string
from contextlib import contextmanager

LANGUAGES = {"en": "English", "de": "Deutsch"}
DEFAULT = "en"

_current: contextvars.ContextVar[str] = contextvars.ContextVar("language", default=DEFAULT)
_SWAP = str.maketrans({",": ".", ".": ","})

MONTHS = {"en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
          "de": ("Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez")}

# Number format for charts (Vega-Lite locale): decimal comma and point as thousands separator.
CHART_LOCALE = {"de": {"number": {"decimal": ",", "thousands": ".", "grouping": [3], "currency": ["", " €"]}}}


def _tables() -> dict[str, dict[str, str]]:
    from .i18n_de import DE
    return {"de": DE}


def set_language(code: str | None) -> str:
    code = code if code in LANGUAGES else DEFAULT
    _current.set(code)
    return code


def language() -> str:
    return _current.get()


@contextmanager
def using(code: str):
    """Runs the block in another language, e.g. a download made outside the page's own run."""
    token = _current.set(code if code in LANGUAGES else DEFAULT)
    try:
        yield
    finally:
        _current.reset(token)


def call_in(code: str, fn, *args, **kwargs):
    with using(code):
        return fn(*args, **kwargs)


class _Formatter(string.Formatter):
    def format_field(self, value, format_spec):
        text = super().format_field(value, format_spec)
        if language() == "de" and isinstance(value, (int, float)) and not isinstance(value, bool):
            text = text.translate(_SWAP)
        return text


_FORMATTER = _Formatter()


def fmt(template: str, **values) -> str:
    """Formats like str.format, with the number format of the current language."""
    return _FORMATTER.format(template, **values)


def translate(text: str) -> str:
    """The text in the current language, without formatting (English when there is no entry)."""
    lang = language()
    if lang == DEFAULT or not text:
        return text
    return _tables().get(lang, {}).get(text, text)


def t(text: str, **values) -> str:
    """The text in the current language; keyword values are filled in with the language's number format."""
    out = translate(text)
    return fmt(out, **values) if values else out


def months() -> tuple[str, ...]:
    return MONTHS.get(language(), MONTHS[DEFAULT])


def month(index: int) -> str:
    return months()[index]


def localize_chart(chart):
    """Gives an Altair chart the number format of the current language."""
    locale = CHART_LOCALE.get(language())
    return chart.configure(locale=locale) if locale else chart
