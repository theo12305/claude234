# results: 📊 Results of borehole heat exchangers

Each view of the "View" drop-down is a plug-in: one file in `views/` with a `render(ctx)` function and a
`register(ResultView(...))` line. `ctx` (see `registry.py`) carries the result, the inputs and the key results.

| File           | What it does                                                                       |
|----------------|------------------------------------------------------------------------------------|
| `registry.py`  | `ResultView`, `Ctx`, `register()`, `plugin_data()` for view settings saved with the project |
| `cache.py`     | cached calculations (sizing, sensitivity, maps, ...)                               |
| `common.py`    | `figure()` with number and downloads, compact key table                             |
| `summary.py`   | the answer card with key tiles, and the one-page results of Simple mode             |
| `sheet.py`     | which parts of the results are shown ("Customize the results")                      |
| `views/*.py`   | temperatures, energy, ground, borefield map, layers, hourly, export, further analysis, and the hidden overview, heat pump, hydraulics, design check views |

To add a view: new file in `views/`, import it in `__init__.py`.
