# charts: drawings and charts

No Streamlit code here; the page shows them with `look.show_figure` (matplotlib, as crisp SVG) or
`st.altair_chart` (Altair).

| File                | What it draws                                                                          |
|---------------------|----------------------------------------------------------------------------------------|
| `palette.py`        | the shared colours, the matplotlib look and the chart style the results page can switch |
| `input_drawings.py` | beside the inputs: borefield layout, borehole cross-section, borehole log, load profiles. `DRAWINGS` says which drawing belongs to which section and variant. |
| `result_charts.py`  | the results: temperatures, last year, hourly, energy balance, g-function, ground map, further analysis |
