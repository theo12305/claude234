# GHEtool Web

A browser interface for sizing borehole heat exchangers with [GHEtool](https://github.com/wouterpeere/GHEtool).

## Run locally

```bash
pip install -r requirements-dev.txt
streamlit run app.py      # opens http://localhost:8501
pytest                    # runs the tests
```

## Put it online (Streamlit Community Cloud, free)

1. Sign in at https://share.streamlit.io with your GitHub account.
2. Click **Create app**, choose this repository, branch `main`, main file `app.py`.
3. Under **Advanced settings** pick Python 3.13, then **Deploy**.

Every push to `main` updates the site automatically.

## Irregular borefields from a shapefile

Choose **Irregular field (shapefile)** under Borefield and upload a point shapefile, one point
per borehole, either zipped or as the separate .shp, .shx, .dbf and .prj files.
Coordinates in degrees (e.g. WGS 84) are converted to metres; projected coordinates in metres
(e.g. UTM) or feet are used directly. The positions appear in an editable table and a numbered
map, and boreholes closer than one borehole diameter are flagged as overlapping.
GHEtool then calculates the g-function for the real layout and sizes one common length
for all boreholes. Try it with `examples/irregular_field.zip`.

## Hourly heating and cooling demand

Under Ground load choose **Hourly building demand** and upload a CSV or Excel file with 8760 rows:
heating demand [kW] in the first column and cooling demand [kW] in the second (a header row is
optional; `;` or `,` separators and decimal commas work). The SCOP and SEER turn building demand
into ground load. With **Size with hourly resolution** on, GHEtool sizes on every hour (L4), and the
results show hourly fluid temperatures. Try it with `examples/hourly_demand_example.csv`.

## Structure

```
app.py                     web page (Streamlit); draws every registered section automatically
ghe_web/model.py           builds a GHEtool Borefield from the inputs, runs sizing, saves/loads projects (no web code)
ghe_web/hourly.py          reads hourly demand files (CSV/Excel) and makes the example profile
ghe_web/geometry.py        reads borehole positions from a point shapefile (.zip or .shp/.shx/.dbf/.prj)
ghe_web/plots.py           drawings of the inputs (layout, borehole, loads) and result charts
ghe_web/properties/
  base.py                  Property, Variant, Section: the building blocks
  registry.py              list of all sections
  ground.py                ground: constant temperature, or with geothermal heat flux
  borefield.py             borefield layout: rectangular, or irregular from a shapefile
  pipe.py                  borehole heat exchanger: single U, double U
  fluid.py                 water / antifreeze mixture
  flow.py                  constant flow per borehole
  load.py                  monthly ground load, or hourly building demand with SCOP/SEER
  limits.py                min/max average fluid temperature
tests/
```

- **Property**: one input field with label, unit, default, limits and help text.
- **Variant**: one way to describe a topic (e.g. "Single U-tube") plus a `build` function
  that turns its values into a GHEtool object. Optional `checks` validate several fields together.
- **Section**: a topic on the page with one or more variants; the user picks the variant.

## How to extend

| You want to add...                       | Do this |
|------------------------------------------|---------|
| A field to an existing input             | Add a `Property` to the variant and use it in `build`. |
| A new option, e.g. coaxial pipe          | Add a `Variant` to the section in `pipe.py`. |
| A drawing for an input                   | Add an entry to `DRAWINGS` in `plots.py` for that section and variant. |
| A new topic, e.g. costs                  | New module with a `Section`, `register(...)` it, import it in `properties/__init__.py`, then use it in `model.py`. |

Saved projects are JSON files. Values that no longer exist are ignored and new ones get their
defaults, so old project files keep working after you extend the interface.

The page picks up new properties, variants and sections without changes to `app.py`.
Units shown to the user (mm, MJ/m³K) are converted to GHEtool's SI units inside `build`.
