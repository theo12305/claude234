# siteplan: ⓪ Site plan

From a parcel (Flurstück) or an address to borehole positions, using the free open data services of the German
states.

| File        | What it does                                                                             |
|-------------|------------------------------------------------------------------------------------------|
| `states.py` | the services and border distance rules of the 16 states (plain data: edit here when a state moves a service) |
| `lookup.py` | fetches parcels and buildings from those services and OpenStreetMap                       |
| `layout.py` | where boreholes may go on the parcel and as many positions as fit (pure geometry)         |
| `export.py` | shapefile, GIS project and preview map                                                    |
| `page.py`   | the Streamlit step: find the parcel, check buildings, place boreholes, export             |

`tools/check_sources.py` and the "Check data sources" GitHub Action test the state services regularly.
