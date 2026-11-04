"""Feature package: the material list (bill of quantities, no prices) with the plan of the horizontal piping.

Self-contained like a plug-in: importing it registers its result view and its German texts. Nothing else in the app
knows about it except the import in ``ghe_web/results/__init__.py``.

  network.py     trench routing (automatic or drawn), plain geometry
  quantities.py  the material list from the sizing result and the settings
  page.py        the result view: plan with clicks and drawing, settings, table, downloads
  de.py          German texts of this package
"""
from .. import i18n
from . import de

i18n.add_table("de", de.DE)

from . import page  # noqa: E402,F401 (registers the view)
