"""Every text on the page, in the reports and in the input definitions has a German translation, with the same
placeholders, and the language switch changes numbers and words."""
import ast
import pathlib
import string

import pytest

from ghe_web import analysis, catalog, i18n, model, plots, properties, report
from ghe_web.i18n import fmt, t
from ghe_web.i18n_de import DE
from ghe_web.siteplan import page as siteplan_page, states
from ghe_web.strata import rocks, sources
from ghe_web.wells import page as wells_page, plots as wells_plots, sources as wells_sources

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _literal_calls() -> set[str]:
    """First arguments of t(...) / i18n.t(...) / translate(...) that are plain strings, in all source files."""
    found = set()
    for path in [ROOT / "app.py", *(ROOT / "ghe_web").rglob("*.py")]:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if name in ("t", "translate") and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str):
                found.add(node.args[0].value)
    return found


def _app_tables() -> set[str]:
    """Dictionaries of labels in app.py (tabs, result views, ...) whose values are translated with t()."""
    texts = set()
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict) and node.targets[0].id.isupper():
            texts |= {v.value for v in node.value.values if isinstance(v, ast.Constant)}
    return texts


def _registry_texts() -> set[str]:
    texts = set()
    for section in properties.sections():
        texts |= {section.label, section.help}
        for variant in section.variants:
            texts |= {variant.label, variant.help}
            for p in variant.properties:
                texts |= {p.label, p.help, p.unit}
                texts |= {o for o in p.options if isinstance(o, str)}
            for group in variant.presets:
                texts |= {group.label, group.help, *group.options}
    return texts


def _data_texts() -> set[str]:
    """Names that come from data tables or result columns and are translated where they are shown."""
    texts = set(rocks.NAMES) | set(catalog.FLUIDS) | set(catalog.MONTHLY_PROFILES)
    texts |= {s.border_note for s in states.STATES} | set(sources.EPSG_CHOICES) | set(sources.LOG_SERVICES.values())
    texts |= {s.label for s in sources.POINT_SERVICES.values()} | {s.link_note for s in sources.POINT_SERVICES.values()}
    texts |= {note for _, _, note in sources.PORTALS.values()}
    texts |= set(siteplan_page.HOW.values())
    texts |= set(analysis.OBJECTIVES.values()) | set(report.METHOD.values())
    texts |= {title for title, _ in plots.DRAWINGS.values()} | set(plots.SERIES_COLORS)
    texts |= {"Ground conductivity ±15 %", "Ground temperature ±1 K", "Building load ±10 %",
              "Grout conductivity ±25 %", "Borehole resistance ±15 %"}  # analysis.sensitivity
    texts |= {"L-shape", "U-shape", "Box", "Rectangle", "Staggered", "Layout", "Boreholes", "Grid", "Spacing [m]",
              "Length each [m]", "Total length [m]"}  # analysis.optimise_layout
    texts |= {"Variant", "Lowest temp. [°C]", "Highest temp. [°C]", "Rb [m·K/W]"}  # kept variants in app.py
    texts |= {"heating", "cooling", "cadastre", "OpenStreetMap", "Parcel", "State", "quick", "normal", "thorough",
              "outside-in rows", "nothing fits", "hexagonal grid at {angle}", "square grid at {angle}",
              "extrapolated", "geological map", "assumed", "entered", "above groundwater"}
    hp = model.heat_pump_table.__code__.co_consts
    texts |= {c for c in hp if isinstance(c, str) and "[MWh]" in c} | {"Year", "SPF heating", "SEER"}
    for who in ("Building", "Ground", "External"):
        for kind in ("heating", "cooling"):
            texts.add(f"{who} {kind} [MWh]")
    texts |= {"Month", "Heating demand", "Cooling demand", "Ground extraction", "Ground injection"}
    texts |= set(wells_page.VIEWS.values()) | set(wells_plots.COMPASS) | {"problem", "warning", "fine"}
    texts |= {text for topic, method, _ in wells_sources.SOURCES for text in (topic, method)}
    return texts


def english_texts() -> set[str]:
    return {x for x in _literal_calls() | _app_tables() | _registry_texts() | _data_texts() if x and x.strip()}


def _fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_everything_is_translated():
    missing = sorted(english_texts() - set(DE))
    assert not missing, "No German translation for:\n" + "\n".join(missing)


def test_placeholders_match():
    wrong = [en for en, de in DE.items() if _fields(en) != _fields(de)]
    assert not wrong, wrong


def test_no_unused_translations():
    unused = sorted(set(DE) - english_texts())
    assert not unused, "Translations that are no longer used:\n" + "\n".join(unused)


def test_number_format_follows_the_language():
    assert fmt("{x:,.1f} m", x=1234.56) == "1,234.6 m"
    with i18n.using("de"):
        assert fmt("{x:,.1f} m", x=1234.56) == "1.234,6 m"
        assert t("{n} boreholes", n=12) == "12 Sonden"
        assert t("Not a known text") == "Not a known text"
        assert i18n.months()[2] == "Mär"
    assert t("{n} boreholes", n=12) == "12 boreholes"


@pytest.mark.parametrize("code", list(i18n.LANGUAGES))
def test_validation_messages_in_both_languages(code):
    inputs = model.default_inputs()
    inputs["limits"].values["T_max"] = -5.0
    with i18n.using(code):
        errors = model.validate(inputs)
    assert errors["limits"]
    if code == "de":
        assert "Fluidtemperatur" in " ".join(errors["limits"])


def test_project_file_keeps_the_language():
    text = model.to_json(model.default_inputs(), "Test", language="de")
    assert model.saved_language(text) == "de"
    assert model.from_json(text)[0] == "Test"
    assert model.saved_language(model.to_json(model.default_inputs())) is None
