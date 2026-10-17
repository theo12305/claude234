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

## Using the page

The inputs are split into four steps (tabs): ① ground and borefield, ② borehole and fluid,
③ loads, ④ limits and costs. The **Size borefield** button sits in the sidebar together with a list of
inputs that still need attention; after the calculation the page jumps to **Results**.

Results start with a one-line verdict and five numbers (length, total length, lowest and highest
temperature with their margin to the limits, investment). Below that, pick a view:

- **Overview**: the temperature chart and the key results in groups: temperatures (incl. long-term
  drift and supply temperatures), ground energy (incl. W/m and full-load hours), borehole and
  hydraulics (Rb, Reynolds, pressure drop and pump power at the coldest fluid), cost.
- **Temperatures**, **Energy**, **Hourly** (hourly loads only): the detailed charts.
- **Further analysis**: sensitivity check (in %), variant comparison, layout optimisation for a plot
  (about 5 s per trial), hybrid share for hourly loads, g-function.
- **Export**: Excel workbook (summary, inputs, all result tables and any analysis you ran), PDF report,
  a zip with workbook + PDF + project file, and CSV files. Files are built when you click.

Only the chosen view is drawn, and input drawings and sizing results are cached, so the page stays
quick even with hourly results.

## Heat pump efficiency

Under step ③, **Heat pump efficiency** can be set to *Depends on the fluid temperature*: enter the COP at
-5, 0, 5, 10 and 15 °C average fluid temperature and the EER at 10 to 30 °C, or pick a heating system
(floor heating, 45 °C or 55 °C radiators) and a cooling mode (passive or active). GHEtool then iterates
the sizing with the COP that belongs to each month's (or hour's) temperature, so a colder ground means
less heat from the ground and more electricity. Results get a **Heat pump** view with the seasonal
performance factor per year, electricity per year and the COP curve with the temperatures the design
reaches. This only applies to building demand (yearly or hourly); with hourly sizing it takes one to two
minutes.

## Features taken from EED

Rock type, grout, pipe and drilling diameter databases (drop-downs that fill in typical values),
yearly building demand split over months with a profile and DHW, peak durations, coaxial pipes,
a measured (constant) borehole resistance, ground temperature from a geothermal gradient, and
checking a given length instead of sizing. Typical values are in `ghe_web/catalog.py`.

## Structure

```
app.py                     web page (Streamlit); draws every registered section automatically
ghe_web/model.py           builds a GHEtool Borefield from the inputs, runs sizing, saves/loads projects (no web code)
ghe_web/hourly.py          reads hourly demand files (CSV/Excel) and makes the example profile
ghe_web/geometry.py        reads borehole positions from a point shapefile (.zip or .shp/.shx/.dbf/.prj)
ghe_web/plots.py           drawings of the inputs (layout, borehole, loads) and result charts
ghe_web/analysis.py        key results, hydraulics, costs, sensitivity, layout optimisation, hybrid share
ghe_web/report.py          PDF report
ghe_web/export.py          Excel workbook and zip export
ghe_web/catalog.py         typical values for rock, grout, pipes, drilling diameters, fluids, load profiles
ghe_web/properties/
  base.py                  Property, Variant, Section: the building blocks
  registry.py              list of all sections
  ground.py                ground: constant temperature, geothermal heat flux, or gradient
  borefield.py             borefield layout: rectangular, or irregular from a shapefile
  pipe.py                  borehole heat exchanger: single U, double U, coaxial, measured Rb
  fluid.py                 water / antifreeze mixture
  flow.py                  constant flow per borehole
  load.py                  monthly ground load, yearly building demand (EED style), or hourly demand
  heat_pump.py             heat pump efficiency: fixed SCOP/SEER or COP/EER curves over fluid temperature
  calculation.py           size or check a given length; cost inputs
  limits.py                min/max average fluid temperature
tests/
```

- **Property**: one input field with label, unit, default, limits and help text.
- **Variant**: one way to describe a topic (e.g. "Single U-tube") plus a `build` function
  that turns its values into a GHEtool object. Optional `checks` validate several fields together,
  `warnings` flag unusual but allowed values, and `presets` add drop-downs with typical values.
- **Section**: a topic on the page with one or more variants; the user picks the variant. Its `group`
  (Site, Borehole, Loads, Design) decides which input step it appears in.

## How to extend

| You want to add...                       | Do this |
|------------------------------------------|---------|
| A field to an existing input             | Add a `Property` to the variant and use it in `build`. |
| A new option, e.g. coaxial pipe          | Add a `Variant` to the section in `pipe.py`. |
| A drawing for an input                   | Add an entry to `DRAWINGS` in `plots.py` for that section and variant. |
| Typical values for a drop-down           | Add them to `catalog.py`; they appear in the matching preset. |
| A new topic                              | New module with a `Section`, `register(...)` it, import it in `properties/__init__.py`, then use it in `model.py`. |

Saved projects are JSON files. Values that no longer exist are ignored and new ones get their
defaults, so old project files keep working after you extend the interface.

The page picks up new properties, variants and sections without changes to `app.py`.
Units shown to the user (mm, MJ/m³K) are converted to GHEtool's SI units inside `build`.
