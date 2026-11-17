# GHEtool & Co.: map for working on the code

Streamlit app on GHEtool (borehole heat exchanger sizing), live from `main` on Streamlit Community Cloud.
Read only the files a change needs; this map says where things are.

- `app.py`: page frame only (~90 lines), calls the parts in `ghe_web/page/` top to bottom. Do not add views here.
- Every folder has a README.md with its file list; `ghe_web/README.md` is the overall map.
- `ghe_web/core/`: model.py (sizing, project file), analysis.py, checks.py, catalog.py (typical values), hourly.py,
  geometry.py. No Streamlit.
- Inputs: `ghe_web/inputs/*.py` (Property / Variant / Section registry). No Streamlit.
- Page (Streamlit): `ghe_web/page/` — state.py (`Page` shared by the parts), look.py (CSS, colours), appbar, menu,
  project, start, steps, sections, fields, site_plan, calculation, design_check, results_tab.
- Charts: `ghe_web/charts/` — palette.py, input_drawings.py (DRAWINGS), result_charts.py. No Streamlit.
- Downloads: `ghe_web/downloads/` — pdf_report.py, excel.py, share_link.py.
- Results of BHEs: `ghe_web/results/` — `registry.py` (ResultView, Ctx, plugin_data), one file per view in
  `views/`, figures via `common.figure()`, cached calculations in `cache.py`, answer card in `summary.py`.
- Feature packages register themselves: `ghe_web/materials/` (material list + piping plan) is the example.
  New feature = new package with logic (no Streamlit), `page.py` registering a view, own `de.py`.
- Groundwater wells (open loop) have their own page: `ghe_web/wells/`. Site plan: `ghe_web/siteplan/`.
  Ground layers: `ghe_web/strata/`.
- Texts: English inside `t("...")`; German in `ghe_web/i18n/de.py` or the feature's `de.py`.
  `tests/test_i18n.py` fails on missing or unused translations.
- Tests: `pytest -m "not slow"` for a quick check, `pytest` before a PR (about 2.5 min).
  `tests/test_app_views.py` opens every result view in Streamlit's test runner.
- Rules from theo: proper technical terms in labels (explanations go in the "?" help), input drawings always
  visible, don't reduce options (Simple mode may tuck fields under "More options"), only free services.
