import pandas as pd
import pytest

from ghe_web import hourly, model, plots, properties


def _hourly_inputs(**overrides):
    inputs = model.default_inputs()
    inputs["load"].variant = "hourly_building"
    inputs["load"].values = properties.get("load").variant("hourly_building").defaults()
    inputs["load"].values.update(overrides)
    return inputs


def test_reads_semicolon_csv_with_header_and_decimal_comma():
    lines = ["Heizung;Kuehlung"] + [f"{h % 10},5;{h % 3},25" for h in range(8760)]
    heating, cooling, notes = hourly.read_profile("demand.csv", "\n".join(lines).encode())
    assert heating[:3] == [0.5, 1.5, 2.5] and cooling[:3] == [0.25, 1.25, 2.25]
    assert notes == []


def test_reads_template_with_hour_column_removed_and_excel(tmp_path):
    df = pd.DataFrame({"heating_kW": [1.0] * 8760, "cooling_kW": [2.0] * 8760})
    path = tmp_path / "demand.xlsx"
    df.to_excel(path, index=False)
    heating, cooling, _ = hourly.read_profile("demand.xlsx", path.read_bytes())
    assert sum(heating) == 8760 and sum(cooling) == 2 * 8760


def test_leap_year_is_trimmed():
    lines = ["1,2"] * 8784
    heating, _, notes = hourly.read_profile("demand.csv", "\n".join(lines).encode())
    assert len(heating) == 8760 and "leap" in notes[0]


@pytest.mark.parametrize("rows, message", [(["1,2"] * 100, "8760"), (["-1,2"] * 8760, "negative"), (["1"] * 8760, "two columns")])
def test_bad_files_are_reported(rows, message):
    with pytest.raises(hourly.HourlyFileError, match=message):
        hourly.read_profile("demand.csv", "\n".join(rows).encode())


def test_hourly_sizing_stays_within_limits():
    result = model.size(_hourly_inputs())
    assert result.sizing_method == "hourly"
    assert len(result.hourly_temperatures) == 8760 * result.borefield.load.simulation_period
    assert result.hourly_temperatures["Average fluid"].min() > -0.1
    assert result.hourly_temperatures["Average fluid"].max() < 17.1
    limits = model.default_inputs()["limits"].values
    plots.hourly_band_chart(result.hourly_temperatures, limits).to_dict()
    plots.hourly_last_year_chart(result.hourly_temperatures, limits).to_dict()


def test_hourly_demand_converted_with_scop():
    # with no cooling, a better heat pump (higher SCOP) takes more heat from the ground: longer boreholes
    flat = {"heating": [100.0] * 8760, "cooling": [0.0] * 8760}
    low = model.size(_hourly_inputs(profile=flat, scop=3.0, hourly_sizing=False)).borehole_length
    high = model.size(_hourly_inputs(profile=flat, scop=6.0, hourly_sizing=False)).borehole_length
    assert high > low


def test_hourly_project_round_trip():
    inputs = _hourly_inputs(scop=4.5)
    _, loaded = model.from_json(model.to_json(inputs))
    assert loaded["load"].variant == "hourly_building"
    assert loaded["load"].values["profile"]["heating"] == inputs["load"].values["profile"]["heating"]
    assert model.validate(loaded) == {}
