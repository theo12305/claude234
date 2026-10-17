import matplotlib.pyplot as plt

from ghe_web import model, plots, properties


def test_every_input_drawing_renders():
    for section in properties.sections():
        for variant in section.variants:
            inputs = model.default_inputs()
            inputs[section.key].variant = variant.key
            inputs[section.key].values = variant.defaults()
            for _, drawing in plots.input_drawings(inputs):
                for part in drawing if isinstance(drawing, tuple) else (drawing,):
                    if isinstance(part, plt.Figure):
                        plt.close(part)
                    else:
                        part.to_dict()


def test_result_charts_render():
    result = model.size(model.default_inputs())
    limits = model.default_inputs()["limits"].values
    plots.temperature_chart(result.temperatures, limits).to_dict()
    plots.last_year_chart(result.temperatures, limits).to_dict()
