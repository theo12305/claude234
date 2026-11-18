"""Feature package: Learn mode, the third mode next to Simple and Expert, for colleagues who are new to borefield
design (with a scientific or engineering background).

Learn mode is a page of its own: three sized example projects, each parameter explained with its governing relation,
its sensitivity on the project and its sources, parameter studies and scenarios. Simple and Expert stay as they are
except for one "Read more" line in some fields' "?" help and the literature button in the menu.

  projects.py    the example projects, the parameters Learn mode explains, sensitivities and studies (no Streamlit)
  examples.json  precomputed lengths and sensitivities (python -m tools.learn_examples)
  glossary.py    every parameter and concept: definition, equation, practice values, sources
  sources.py     the numbered literature list (one list for the whole app)
  explain.py     "why this length" and the temperature budget with the project's numbers (no Streamlit)
  page.py        the Learn page, the menu button and the "Read more" line
  text.py        L(en, de): long texts in both languages side by side
  de.py          German labels of this package
"""
from .. import i18n
from . import de

i18n.add_table("de", de.DE)
