# learn: Learn mode

The third mode next to Simple and Expert, for colleagues new to borefield design (scientific or engineering
background). Learn mode is a page of its own, without the planning steps: pick one of three sized example projects
and study it in five tabs.

- **Parameters**: every input that matters, with its value, its local sensitivity on this project (elasticity
  ε = (ΔL/L)/(Δx/x), or m/K for temperatures) and a "?" with definition, governing relation, practice values and
  sources.
- **Result explained**: why this length, the temperature budget of the limiting month, the yearly extremes and the
  method (temporal superposition on the g-function).
- **Explore**: parameter study, the three projects compared (normalised), regeneration share, ground temperature over
  the years, borehole resistance (grout and flow).
- **Glossary** and **Literature**.

Simple and Expert only get a "Read more" line in the "?" help of fields with a glossary entry, and the literature
list in the menu ☰.

| File            | What is in it                                                                              |
|-----------------|--------------------------------------------------------------------------------------------|
| `projects.py`   | the example projects, the parameters, sensitivities and studies (no Streamlit)             |
| `examples.json` | precomputed lengths and sensitivities; rewrite with `python -m tools.learn_examples`       |
| `glossary.py`   | every parameter and concept: definition, equation, practice values, sources                |
| `sources.py`    | the numbered literature list ([1] … [12]); add new entries at the end so numbers stay      |
| `explain.py`    | "why this length" and the temperature budget (no Streamlit)                                |
| `page.py`       | everything drawn on the page (Streamlit)                                                   |
| `text.py`       | `L(en, de)`: long texts are written in both languages in place                             |
| `de.py`         | German for the short labels in `t("...")`                                                  |

To correct a text, edit it in `projects.py`, `glossary.py` or `explain.py`; both languages sit next to each other.
