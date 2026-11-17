"""Feature package: Learn mode, the third mode next to Simple and Expert, for new colleagues.

Self-contained like a plug-in. Learn is Simple plus explanations; Simple and Expert stay as they are except for one
"Read more" line in some fields' "?" help and the literature button in the menu.

  sources.py    the numbered literature list (one list for the whole app)
  glossary.py   technical terms with symbol, typical values, sources; which field belongs to which term
  modules.py    the introduction: eight short modules along the input steps, with a self-check question each
  explain.py    "why this length" and "where the degrees go" with the project's numbers (no Streamlit)
  exercises.py  the "Try it" calculations on a small practice project (no Streamlit)
  page.py       everything on the page: result cards, the three Learn tabs, exercises, menu button
  text.py       L(en, de): long texts in both languages side by side
  de.py         German labels of this package
"""
from .. import i18n
from . import de

i18n.add_table("de", de.DE)
