"""Long texts of Learn mode come in both languages side by side (modules, glossary, explanations), so they do not
go through the translation table. Short labels on the page use ``t()`` and ``learn/de.py`` as everywhere else."""
from __future__ import annotations

from .. import i18n


def L(en: str, de: str) -> str:  # noqa: N802 (short on purpose: used in every text)
    """The text in the current language."""
    return de if i18n.language() == "de" else en
