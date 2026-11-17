# ghe_web: the code of GHEtool & Co.

`app.py` (in the repository root) draws the page from top to bottom and calls the parts below. Each folder has its
own README.md with a list of its files. To change one thing, open only the folder it belongs to.

| Folder        | What is in it                                                                          | Streamlit? |
|---------------|----------------------------------------------------------------------------------------|------------|
| `core/`       | the engineering: inputs to a GHEtool borefield, sizing, post-processing, design check  | no         |
| `inputs/`     | every input section with its fields, options and typical values (one file per topic)   | no         |
| `page/`       | the page around everything: look, app bar, menu, start page, steps, calculate bar      | yes        |
| `charts/`     | drawings of the inputs, charts of the results, shared colours                          | no         |
| `results/`    | 📊 Results of borehole heat exchangers, one file per view                              | yes        |
| `downloads/`  | PDF report, Excel workbook, share link                                                 | no         |
| `i18n/`       | English / German: `t("...")`, number format, German texts                              | no         |
| `siteplan/`   | ⓪ Site plan: parcel and buildings from the state services, borehole positions          | `page.py`  |
| `strata/`     | ground layers from borehole logs and geological maps                                   | `page.py`  |
| `wells/`      | groundwater wells (open loop): own model and own results page                          | `page.py`  |
| `materials/`  | material list and horizontal piping plan (hidden on the page for now)                  | `page.py`  |

## How one calculation flows through the code

1. `page/project.py` picks the starting values: defaults, an opened project file or a share link.
2. `page/steps.py` and `page/sections.py` draw the input steps from the sections in `inputs/`.
3. `page/calculation.py` sends the inputs to `core/model.py`, which builds a GHEtool borefield and sizes it.
4. `page/results_tab.py` hands the result to the views in `results/`, which use `core/analysis.py` for numbers
   and `charts/` for pictures.
5. `downloads/` turns the same result into the PDF, the Excel workbook and the share link.

Groundwater wells take their own path after step 2: `wells/page.py` calculates and shows them.
