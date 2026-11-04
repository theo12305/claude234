# GHEtool & Co.: map for working on the code

Streamlit app on GHEtool (borehole heat exchanger sizing), live from `main` on Streamlit Community Cloud.
Read only the files a change needs; this map says where things are.

- `app.py`: page frame only (app bar, menu, input steps, calculate bar, results frame). Do not add views here.
- Inputs: `ghe_web/properties/*.py` (Property / Variant / Section registry). Typical values: `ghe_web/catalog.py`.
- Sizing and project file: `ghe_web/model.py` (no web code). Post-processing: `ghe_web/analysis.py`.
- Results of BHEs: `ghe_web/results/` — `registry.py` (ResultView, Ctx, plugin_data), one file per view in
  `views/`, figures via `common.figure()`, cached calculations in `cache.py`, answer card in `summary.py`.
- Feature packages register themselves: `ghe_web/materials/` (material list + piping plan) is the example.
  New feature = new package with logic (no Streamlit), `page.py` registering a view, own `de.py`.
- Groundwater wells (open loop) have their own page: `ghe_web/wells/`. Site plan: `ghe_web/siteplan/`.
  Ground layers: `ghe_web/strata/`.
- Texts: English inside `t("...")`; German in `ghe_web/i18n_de.py` or the feature's `de.py`.
  `tests/test_i18n.py` fails on missing or unused translations.
- Tests: `pytest -m "not slow"` for a quick check, `pytest` before a PR (about 2.5 min).
  `tests/test_app_views.py` opens every result view in Streamlit's test runner.
- Rules from theo: proper technical terms in labels (explanations go in the "?" help), input drawings always
  visible, don't reduce options (Simple mode may tuck fields under "More options"), only free services.
