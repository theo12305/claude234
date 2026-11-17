# wells: groundwater wells (open loop)

GHEtool has no open-loop model, so the hydraulics and the thermal model live here. Only `page.py` uses Streamlit.

| File            | What it does                                                                   |
|-----------------|--------------------------------------------------------------------------------|
| `aquifer.py`    | hydraulic properties of rock types; the aquifer from the layer table           |
| `hydraulics.py` | drawdown and rise in the wells (Thiem)                                         |
| `thermal.py`    | thermal model of the doublet: recirculation and thermal breakthrough           |
| `design.py`     | sizing and checking: flow, wells, well distance                                |
| `checks.py`     | the design check for wells                                                     |
| `plots.py`      | drawings and charts                                                            |
| `report.py`     | key results, Excel workbook and PDF report                                     |
| `sources.py`    | what each part of the calculation is based on, with the literature             |
| `page.py`       | the calculation button and the results page                                    |
