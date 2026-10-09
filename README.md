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

## Structure

```
app.py                     web page (Streamlit); draws every registered section automatically
ghe_web/model.py           builds a GHEtool Borefield from the inputs and runs sizing (no web code)
ghe_web/properties/
  base.py                  Property, Variant, Section: the building blocks
  registry.py              list of all sections
  ground.py                ground: constant temperature, or with geothermal heat flux
  borefield.py             borefield layout: rectangular
  pipe.py                  borehole heat exchanger: single U, double U
  fluid.py                 water / antifreeze mixture
  flow.py                  constant flow per borehole
  load.py                  monthly extracted/injected energy and peaks
  limits.py                min/max average fluid temperature
tests/test_model.py
```

- **Property**: one input field with label, unit, default, limits and help text.
- **Variant**: one way to describe a topic (e.g. "Single U-tube") plus a `build` function
  that turns its values into a GHEtool object. Optional `checks` validate several fields together.
- **Section**: a topic on the page with one or more variants; the user picks the variant.

## How to extend

| You want to add...                       | Do this |
|------------------------------------------|---------|
| A field to an existing input             | Add a `Property` to the variant and use it in `build`. |
| A new option, e.g. coaxial pipe          | Add a `Variant` to the section in `pipe.py`. |
| A new topic, e.g. costs                  | New module with a `Section`, `register(...)` it, import it in `properties/__init__.py`, then use it in `model.py`. |

The page picks up new properties, variants and sections without changes to `app.py`.
Units shown to the user (mm, MJ/m³K) are converted to GHEtool's SI units inside `build`.
