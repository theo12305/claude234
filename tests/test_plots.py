import matplotlib.pyplot as plt

from ghe_web.core import model
from ghe_web.inputs import registry as input_registry
from ghe_web.charts import input_drawings, result_charts


def test_every_input_drawing_renders():
    for section in input_registry.sections():
        for variant in section.variants:
            inputs = model.default_inputs()
            inputs[section.key].variant = variant.key
            inputs[section.key].values = variant.defaults()
            for _, drawing in input_drawings.input_drawings(inputs):
                for part in drawing if isinstance(drawing, tuple) else (drawing,):
                    if isinstance(part, plt.Figure):
                        plt.close(part)
                    else:
                        part.to_dict()


def test_result_charts_render():
    result = model.size(model.default_inputs())
    limits = model.default_inputs()["limits"].values
    result_charts.temperature_chart(result.temperatures, limits).to_dict()
    result_charts.last_year_chart(result.temperatures, limits).to_dict()
