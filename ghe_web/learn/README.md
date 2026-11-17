# learn: Learn mode for new colleagues

The third mode next to Simple and Expert. It is Simple plus explanations: three more tabs (Introduction, Glossary,
Literature) and two cards on the results ("Why this length?" and "Where the degrees go"). Simple and Expert stay as
they are; only the literature list in the menu ☰ and a "Read more" line in the "?" help of some fields appear there.

| File           | What is in it                                                                              |
|----------------|--------------------------------------------------------------------------------------------|
| `sources.py`   | the numbered literature list ([1] … [12]); add new entries at the end so numbers stay      |
| `glossary.py`  | the technical terms, with symbol, text, sources; `FIELDS` links input fields to terms      |
| `modules.py`   | the 8 introduction modules: text, exercises, self-check question, sources                  |
| `explain.py`   | the "Why this length?" steps and the split of the fluid temperature (no Streamlit)         |
| `exercises.py` | the practice project (6 boreholes) and the calculations behind the exercises (no Streamlit)|
| `page.py`      | everything drawn on the page (Streamlit)                                                   |
| `text.py`      | `L(en, de)`: long texts are written in both languages in place                             |
| `de.py`        | German for the short labels in `t("...")`                                                  |

To correct a text, edit it in `modules.py` or `glossary.py`; both languages sit next to each other.
