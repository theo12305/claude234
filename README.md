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

## Site plan: from a Flurstück to borehole positions

The first tab, **⓪ Site plan**, finds the largest number of boreholes that fit on a parcel and writes them
as a shapefile:

1. **Parcel**: search an address, the Flurstück number (Gemarkung number, Flur, Zähler, Nenner), click the
   parcel on the map, draw it, or upload its outline (GeoJSON, KML, zipped shapefile). The parcel is loaded
   from the state's open cadastre service (INSPIRE or ALKIS WFS). Bayern publishes no open parcel
   outlines: there the parcel lines of the cadastre map are shown so it can be drawn.
2. **Distances**: to the parcel border (pre-filled per state from its Leitfaden, editable), to buildings
   (2 m), between boreholes (6 m), and to areas drawn on the map.
3. **Buildings**: official building outlines from the state's cadastre plus OpenStreetMap buildings the
   cadastre lacks, on top of the state's aerial image (DOP). Buildings are not detected automatically from
   the image: compare with the image, draw missing buildings or other areas to keep free, and untick
   buildings that are gone.
4. **Result**: the boreholes (rotated and shifted hexagonal and square grids plus an outside-in fill; the
   pattern with the most boreholes wins), the BHE shapefile, a GIS project zip (shapefiles, QGIS project with
   the aerial image, preview map, read-me) and **Use in the sizing**, which sets Borefield to an irregular
   field with these positions.

The services and border distances of the 16 states are plain data in `ghe_web/siteplan/states.py`.
Check the distances with the local water authority (Untere Wasserbehörde) before planning.

## Ground layers: predicted from borehole logs

Under Ground in step ① the panel **Predict the layers** estimates the layers at the site:

- Location: the parcel from the site plan, an address or coordinates.
- Data: borehole logs within a search radius, weighted by 1/distance², and the BGR geological map (GÜK250) at
  the surface. Logs come from the open BoreholeML service of GD NRW (North Rhine-Westphalia) or from files you upload:
  BoreholeML (.xml, the exchange format of the state surveys) or a table with one row per layer (template on the
  page; SEP 3 codes such as `mS,g` or words such as `Tonstein` are recognised). Other states have no open log service
  yet; download the logs from the state portal and upload them.
- Thermal values: VDI 4640 Blatt 1 per rock type (`ghe_web/strata/rocks.py`); loose sediments above the groundwater
  table get lower, moist values.
- **Fill in the averages** puts the depth-weighted averages into the single fields; **Use the layers** copies the
  layers into an editable table and switches on the layered calculation (GHEtool `GroundLayer`), which averages the
  layers over the borehole length while sizing. The Results get a **Layers** view with the borehole log, each layer's
  share of the heat exchange, the average conductivity for other lengths and a comparison with a single value.

## Hourly heating and cooling demand

Under Ground load choose **Hourly building demand** and upload a CSV or Excel file with 8760 rows:
heating demand [kW] in the first column and cooling demand [kW] in the second (a header row is
optional; `;` or `,` separators and decimal commas work). The SCOP and SEER turn building demand
into ground load. With **Size with hourly resolution** on, GHEtool sizes on every hour (L4), and the
results show hourly fluid temperatures. Try it with `examples/hourly_demand_example.csv`.

## Languages

The page, the PDF report and the Excel workbook are available in English (default) and German. The switch is at
the top of the sidebar, and the choice is saved in the project file. German numbers use the decimal comma.

Texts are written in English in the code and wrapped in `t("...")` (`ghe_web/i18n.py`); the German texts are in
`ghe_web/i18n_de.py`, keyed by the English text. `tests/test_i18n.py` fails when a text has no German entry, when
the placeholders differ, or when an entry is no longer used. German terms follow VDI 4640.

## Using the page

The inputs are split into four steps (tabs): ① ground and borefield, ② borehole and fluid,
③ loads, ④ limits and calculation. The **Size borefield** button sits in the sidebar together with a list of
inputs that still need attention; after the calculation the page jumps to **Results**.

Results start with a one-line verdict and five numbers (length, total length, lowest and highest
temperature with their margin to the limits, borehole resistance). The default simulation period is
50 years. Below that, pick a view (modelled on the result views of the paid GHEtool Cloud):

- **Overview**: the temperature chart and the key results in groups: temperatures (incl. long-term
  drift and supply temperatures), ground energy (incl. W/m and full-load hours), borehole and
  hydraulics (Rb, Reynolds, pressure drop, pump power and pump energy at the coldest fluid).
- **Temperatures**, **Energy** (incl. load duration curve for hourly loads), **Hourly** (hourly loads only),
  **Heat pump** (building loads): the detailed charts. With hourly (L4) sizing all key results come
  from the hourly run; the monthly charts are shown for comparison only.
- **Hydraulics**: Rb, Reynolds, pressure drop and pump power, and the pressure drop curve against flow rate.
- **Ground**: map of the ground temperature change around the field at mid-depth at the end of the
  simulation (finite line source of the yearly imbalance), and the g-function.
- **Load optimisation** (hourly building demand): keeps the field and finds how much demand it can
  cover, optimised for power, energy or a balanced ground (GHEtool's `optimise_load_profile_*`). The rest
  is backup heating or cooling; the optimised load can be downloaded.
- **Further analysis**: sensitivity check (in %), variant comparison, layout optimisation for a plot
  (about 5 s per trial).
- **Export**: Excel workbook (summary, inputs, all result tables and any analysis you ran), PDF report
  (full report with cover page, or a one-page summary; title, author, company, client, logo, introduction
  and conclusion can be filled in), a zip with workbook + PDF + project file, and CSV files. Files are
  built when you click.

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
ghe_web/analysis.py        key results, hydraulics, sensitivity, layout and load optimisation, ground map
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
  calculation.py           size or check a given length
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
| Any text on the page or in a report      | Write it in English inside `t("...")` and add the German text to `ghe_web/i18n_de.py`. |

Saved projects are JSON files. Values that no longer exist are ignored and new ones get their
defaults, so old project files keep working after you extend the interface.

The page picks up new properties, variants and sections without changes to `app.py`.
Units shown to the user (mm, MJ/m³K) are converted to GHEtool's SI units inside `build`.
