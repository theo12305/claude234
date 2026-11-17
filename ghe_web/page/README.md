# page: the Streamlit page

The parts of the page that `app.py` calls, in the order they appear on screen. They share one `Page` object
(`state.py`) with the language, the mode, the input steps and, once read, the inputs.

| File              | Part of the page                                                                         |
|-------------------|------------------------------------------------------------------------------------------|
| `state.py`        | `Page`: what the parts share while the page is drawn                                     |
| `look.py`         | colours (light and dark), CSS, answer card, key tiles, range bars, crisp SVG figures     |
| `appbar.py`       | the bar at the top: name, Simple / Expert, language, menu ☰                             |
| `menu.py`         | the menu ☰: project name, open, save, share link, help                                  |
| `project.py`      | the starting values (defaults, project file, share link) and saving the project          |
| `start.py`        | the start page (address, heat source) and the intro above the steps                      |
| `steps.py`        | the input steps as tabs and the Next buttons                                             |
| `sections.py`     | one box per input section, the "Typical values" card of Simple mode                      |
| `fields.py`       | single input fields, preset drop-downs, monthly table, file uploads, input drawings      |
| `guidance.py`     | typical ranges, Simple / Expert fields, side notes (no Streamlit, so it can be tested)   |
| `site_plan.py`    | the ⓪ Site plan step and what it hands to the inputs                                     |
| `calculation.py`  | the calculation and the calculate bar at the bottom                                      |
| `design_check.py` | the design check step                                                                    |
| `results_tab.py`  | the 📊 Results and 🔬 Further analysis tabs (the views themselves are in `results/`)       |
