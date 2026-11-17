# tests

`pytest -m "not slow"` gives a quick check (about a minute); `pytest` runs everything (about 2.5 minutes).

| File                         | What it checks                                                          |
|------------------------------|-------------------------------------------------------------------------|
| `test_model.py`              | sizing, project files, validation                                       |
| `test_analysis.py`           | key results, hydraulics, sensitivity, optimisation                       |
| `test_pro_outputs.py`        | outputs compared with GHEtool Cloud, maths and physics review fixes      |
| `test_heat_pump.py`          | heat pump curves and their results                                      |
| `test_hourly.py`             | hourly demand files and hourly sizing                                   |
| `test_geometry.py`           | shapefile reading                                                       |
| `test_plots.py`, `test_charts_round2.py` | input drawings and result charts                            |
| `test_guidance.py`           | typical ranges, side notes, Simple-mode fields                          |
| `test_ideas.py`              | share links, design check, per-borehole map                             |
| `test_export.py`             | Excel workbook, PDF report, zip                                         |
| `test_siteplan.py`           | site plan geometry and state services                                    |
| `test_strata.py`             | ground layer prediction                                                  |
| `test_wells.py`              | groundwater wells against textbook results                               |
| `test_materials.py`          | material list and piping                                                |
| `test_i18n.py`               | every text has a German translation, and none is left over               |
| `test_app_views.py`          | the whole page in Streamlit's test runner, every result view             |
