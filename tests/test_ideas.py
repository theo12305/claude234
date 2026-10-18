"""Example projects, share links, the design check and the per-borehole map."""
import base64
import json
import zlib

import pytest

from ghe_web import analysis, checks, examples, model, share
from ghe_web.properties import SectionInput


@pytest.mark.parametrize("example", examples.EXAMPLES, ids=lambda e: e.key)
def test_examples_are_valid_and_size_to_a_sensible_length(example):
    inputs = example.inputs()
    assert not model.validate(inputs)
    result = model.size(inputs)
    assert 60 < result.borehole_length < 150  # realistic, and no warning about deep drilling for most


def test_share_link_round_trip_keeps_the_project_and_language():
    inputs = examples.get("school").inputs()
    text = model.to_json(inputs, "School", language="de")
    url, dropped = share.link("https://example.org/app/?x=1", text)
    assert url.startswith("https://example.org/app/?p=") and not dropped
    back = share.decode(url.split("p=", 1)[1])
    name, loaded = model.from_json(back)
    assert name == "School" and model.saved_language(back) == "de"
    assert loaded["borefield"].values["points"] == inputs["borefield"].values["points"]


def test_share_link_leaves_out_the_hourly_file():
    inputs = model.default_inputs()
    from ghe_web import properties
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
    inputs = examples.get("house").inputs()
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
