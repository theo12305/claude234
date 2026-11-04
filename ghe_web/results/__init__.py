"""The 📊 Results tab of borehole heat exchangers. Importing this package registers every built-in view.

Map (to change one thing, open only its file):
  registry.py   ResultView, Ctx, register(), plugin_data() for settings saved with the project
  cache.py      cached calculations (sizing, sensitivity, maps, ...)
  common.py     figure() with number and downloads, key_table(), in_language()
  summary.py    answer card, key tiles and the one-page results of Simple mode
  views/*.py    one file per view of the "View" drop-down
Feature packages (e.g. ghe_web/materials) register their own views.
"""
from .views import (overview, checks, temperatures, energy, hourly, heat_pump, hydraulics, ground,  # noqa: F401
                    field, layers, load_optimisation, analysis, export)
from .registry import Ctx, ResultView, register, views  # noqa: F401
from .. import materials  # noqa: F401,E402 (a feature package: registers the material list view)
