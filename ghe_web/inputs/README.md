# inputs: the input sections

Every topic on the input steps is a `Section` in its own file. The page draws whatever is registered here, so a
new field or option needs no change in `page/` or `app.py`.

- **Property**: one input field with label, unit, default, limits and help text.
- **Variant**: one way to describe a topic (e.g. "Single U-tube") plus a `build` function that turns its values
  into a GHEtool object. Optional `checks`, `warnings` and `presets` (drop-downs with typical values).
- **Section**: a topic with one or more variants. Its `group` decides the input step, its `system` ("closed",
  "open" or empty) for which heat source it is shown.

| File             | Section                                                                   |
|------------------|---------------------------------------------------------------------------|
| `base.py`        | the building blocks: Property, Variant, Section, PresetGroup              |
| `registry.py`    | the list of all sections                                                  |
| `ground.py`      | ground: constant temperature, geothermal heat flux, gradient, layers      |
| `borefield.py`   | borefield layout: rectangular, or irregular from a shapefile / site plan  |
| `pipe.py`        | borehole heat exchanger: single U, double U, coaxial, measured Rb         |
| `fluid.py`       | water / antifreeze mixture                                                |
| `flow.py`        | flow rate                                                                 |
| `load.py`        | monthly ground load, yearly building demand (EED style), hourly demand    |
| `heat_pump.py`   | fixed SCOP/SEER or COP/EER curves over the fluid temperature             |
| `calculation.py` | size, or check a given length                                             |
| `limits.py`      | minimum and maximum mean fluid temperature                                |
| `wells.py`       | heat source switch and the inputs of groundwater wells                    |

To add a topic: new file with a `Section`, `register(...)` it, import it in `__init__.py`, use it in
`core/model.py`.
