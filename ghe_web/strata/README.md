# strata: ground layers

Predicts the layers under the site from nearby borehole logs and geological maps and turns them into thermal
properties for the ground section.

| File         | What it does                                                                     |
|--------------|----------------------------------------------------------------------------------|
| `sources.py` | where the data comes from: geological survey services and uploaded files          |
| `reader.py`  | reads borehole logs given as text (copied, PDF text layer, web page)             |
| `rocks.py`   | rock types with thermal properties, and the classifier for log descriptions      |
| `predict.py` | the prediction from the nearest logs and the thermal properties of the layers    |
| `page.py`    | the ground layers panel in step ① (Streamlit)                                    |
