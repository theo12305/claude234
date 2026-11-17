# core: the engineering

No Streamlit code here, so everything can be tested and reused on its own (for example in a Jupyter notebook).

| File          | What it does                                                                                     |
|---------------|--------------------------------------------------------------------------------------------------|
| `model.py`    | turns the inputs into a GHEtool `Borefield`, sizes or checks it, saves and opens project files    |
| `analysis.py` | after the sizing: key results, hydraulics, sensitivity, layout and load optimisation, ground map  |
| `checks.py`   | the design check: every input and result check, marked problem, warning or fine                   |
| `catalog.py`  | typical values (rock, grout, pipes, drilling diameters, fluids, load profiles), like EED's databases |
| `hourly.py`   | reads hourly demand files (CSV / Excel) and makes the example profile                             |
| `geometry.py` | reads borehole positions from a point shapefile                                                  |

Example:

```python
from ghe_web.core import model
inputs = model.default_inputs()
result = model.size(inputs)
print(result.borehole_length)
```
