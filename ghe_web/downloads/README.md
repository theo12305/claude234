# downloads: files the user takes away

| File            | What it makes                                                                          |
|-----------------|----------------------------------------------------------------------------------------|
| `pdf_report.py` | the PDF report (reportlab), with the result charts as on the page                     |
| `excel.py`      | the Excel workbook with every table, and the zip with workbook, PDF and project file   |
| `share_link.py` | the project packed into a link (`?p=...`); nothing is stored on the server             |

The project file itself (JSON) is written and read in `core/model.py`.
