"""Share links, the design check and the per-borehole map."""
import base64
import json
import zlib

import pytest

from ghe_web import analysis, checks, model, properties, share
from ghe_web.properties import SectionInput


def _irregular_field() -> dict:
    inputs = model.default_inputs()
    values = {**properties.get("borefield").variant("custom").defaults(),
              "points": tuple((x * 7.0, y * 7.0) for x in range(6) for y in range(3))}
    inputs["borefield"] = SectionInput("custom", values)
    return inputs


def _small_house() -> dict:
    inputs = model.default_inputs()
    inputs["borefield"].values.update(N_1=3, N_2=1, B_1=8.0)
    inputs["load"] = SectionInput("annual_building", {
        **properties.get("load").variant("annual_building").defaults(), "annual_heating_mwh": 18.0,
        "peak_heating_kw": 10.0, "annual_cooling_mwh": 0.0, "peak_cooling_kw": 0.0, "dhw_mwh": 3.0})
    inputs["limits"].values["T_min"] = -1.5
    return inputs


def test_share_link_round_trip_keeps_the_project_and_language():
    inputs = _irregular_field()
    text = model.to_json(inputs, "School", language="de")
    url, dropped = share.link("https://example.org/app/?x=1", text)
    assert url.startswith("https://example.org/app/?p=") and not dropped
    back = share.decode(url.split("p=", 1)[1])
    name, loaded = model.from_json(back)
    assert name == "School" and model.saved_language(back) == "de"
    assert loaded["borefield"].values["points"] == inputs["borefield"].values["points"]


def test_share_link_leaves_out_the_hourly_file():
    inputs = model.default_inputs()
    inputs["load"] = SectionInput("hourly_building", properties.get("load").variant("hourly_building").defaults())
    url, dropped = share.link("https://x/", model.to_json(inputs))
    assert dropped and len(url) < 3000
    _, loaded = model.from_json(share.decode(url.split("p=", 1)[1]))
    assert loaded["load"].variant == "hourly_building"  # opens with the example profile


@pytest.mark.parametrize("packed", ["", "not-base64!!", base64.urlsafe_b64encode(b"plain").decode()])
def test_bad_links_raise_value_error(packed):
    with pytest.raises(ValueError):
        model.from_json(share.decode(packed))


def test_a_link_cannot_inflate_without_limit():
    bomb = base64.urlsafe_b64encode(zlib.compress(b" " * (share.MAX_PROJECT_BYTES * 3))).decode()
    with pytest.raises(ValueError):
        share.decode(bomb)


def test_design_check_flags_inputs_and_results():
    inputs = model.default_inputs()
    inputs["borefield"].values.update(B_1=4.0)
    found = checks.input_checks(inputs)
    assert any(c.level == checks.WARNING and c.section == "borefield" and "4.0 m" in c.detail for c in found)
    inputs["limits"].values["T_max"] = -5.0
    assert any(c.level == checks.PROBLEM and c.section == "limits" for c in checks.input_checks(inputs))


def test_design_check_after_sizing():
    inputs = _small_house()
    result = model.size(inputs)
    found = checks.result_checks(result, inputs, analysis.key_results(result, inputs))
    titles = {c.title: c.level for c in found}
    assert titles["Temperature limits"] == checks.FINE
    assert titles["Antifreeze"] == checks.FINE
    assert "Ground balance" in titles
    assert sum(checks.counts(found).values()) == len(found)


def test_borehole_map_edges_take_more_than_the_centre():
    inputs = model.default_inputs()
    inputs["borefield"].values.update(N_1=5, N_2=5)
    table = analysis.borehole_map(model.size(inputs))
    assert len(table) == 25 and table["Share"].mean() == pytest.approx(1.0)
    corner, centre = table.loc[0], table.loc[12]
    assert corner["Share"] > 1 > centre["Share"]
    assert abs(centre["Change"]) > abs(corner["Change"])  # neighbours add up in the middle
    early = analysis.borehole_map(model.size(inputs), years=1.0)
    assert early["Share"].max() < table["Share"].max()  # the difference grows over the years
