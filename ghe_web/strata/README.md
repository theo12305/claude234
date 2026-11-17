# strata: ground layers

Predicts the layers under the site from nearby borehole logs and geological maps and turns them into thermal
properties for the ground section.

| File         | What it does                                                                     |
|--------------|----------------------------------------------------------------------------------|
| `sources.py` | where the data comes from: geological survey services and uploaded files          |
| `reader.py`  | reads borehole logs given as text (copied, PDF text layer, web page), pictures and scans by text recognition (Tesseract), and log column PDFs |
| `rocks.py`   | rock types with thermal properties, and the classifier for log descriptions      |
| `predict.py` | the prediction from the nearest logs and the thermal properties of the layers    |
| `page.py`    | the ground layers panel in the ground step (Streamlit)                           |
| `de.py`      | German texts added since the move to feature tables (older ones in i18n/de.py)   |

Which states deliver logs without the user:

- NRW (GD NRW) and Baden-Württemberg (LGRB): BoreholeML web feature services with layers, asked in widening
  squares (300, 800, 2000 m) with at most 30 to 40 boreholes per request (larger requests time out).
- Berlin: the log sheet picture of each borehole (GeODin layout 1) read by Tesseract; Schleswig-Holstein: the log
  column PDF (GeODin layout SGD_SH_Start) has a text layer. The nearest few are read and put into "Logs to check".
- Tesseract comes from `packages.txt` (apt packages on Streamlit Community Cloud); call it with
  `OMP_THREAD_LIMIT=1`, otherwise it is about ten times slower on small servers.
- Not possible (Nov 2026): Brandenburg and Niedersachsen log pictures have no depths as text; Sachsen shows no layers
  publicly; the MV log viewer refuses non-German networks; Hessen, Bayern, RP, SL, ST, TH, HB, HH have no open logs.
