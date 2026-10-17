import io
import math
import zipfile

import pytest
import shapefile

from ghe_web import geometry, model, properties

WGS84 = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],' \
        'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'
UTM = 'PROJCS["ETRS_1989_UTM_Zone_32N",GEOGCS["GCS_ETRS_1989"],UNIT["Meter",1.0]]'


def make_shapefile(points, shape_type=shapefile.POINT, prj=None):
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    with shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shape_type) as w:
        w.field("id", "N")
        if shape_type == shapefile.POINT:
            for i, (x, y) in enumerate(points):
                w.point(x, y)
                w.record(i)
        else:
            w.poly([list(points) + [points[0]]])
            w.record(0)
    parts = {"field.shp": shp.getvalue(), "field.shx": shx.getvalue(), "field.dbf": dbf.getvalue()}
    if prj:
        parts["field.prj"] = prj.encode()
    return parts


def zipped(parts):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in parts.items():
            zf.writestr(f"folder/{name}", content)
    return {"field.zip": buf.getvalue()}


def test_reads_separate_files_and_shifts_to_origin():
    result = geometry.read_shapefile(make_shapefile([(500010, 5600020), (500016, 5600020)], prj=UTM))
    assert result.points == [(0.0, 0.0), (6.0, 0.0)]
    assert result.notes == []


def test_reads_zip():
    result = geometry.read_shapefile(zipped(make_shapefile([(0, 0), (6, 0), (3, 5)], prj=UTM)))
    assert len(result.points) == 3


def test_degrees_are_converted_to_metres():
    # two points 0.0001° of latitude apart are ~11.1 m apart
    result = geometry.read_shapefile(make_shapefile([(7.0, 50.0), (7.0, 50.0001)], prj=WGS84))
    assert math.dist(*result.points) == pytest.approx(11.12, abs=0.02)
    assert "degrees" in result.notes[0]


def test_missing_prj_is_assumed_metres():
    result = geometry.read_shapefile(make_shapefile([(0, 0), (6, 0)]))
    assert "metres" in result.notes[0]


def test_polygons_are_rejected():
    with pytest.raises(geometry.GeometryError, match="point"):
        geometry.read_shapefile(make_shapefile([(0, 0), (10, 0), (10, 10)], shape_type=shapefile.POLYGON))


def test_missing_part_is_reported():
    parts = make_shapefile([(0, 0)])
    del parts["field.shx"]
    with pytest.raises(geometry.GeometryError, match=".shx"):
        geometry.read_shapefile(parts)


def _custom_inputs(points):
    inputs = model.default_inputs()
    inputs["borefield"].variant = "custom"
    inputs["borefield"].values = properties.get("borefield").variant("custom").defaults()
    inputs["borefield"].values["points"] = points
    return inputs


def test_custom_field_matches_rectangular_field():
    # the same 10 x 12 grid entered as points must size to the same length
    grid = tuple((i * 6.0, j * 6.0) for i in range(10) for j in range(12))
    custom = model.size(_custom_inputs(grid))
    rectangular = model.size(model.default_inputs())
    assert custom.number_of_boreholes == 120
    assert custom.borehole_length == pytest.approx(rectangular.borehole_length, rel=1e-3)


def test_irregular_example_field_sizes():
    result = model.size(_custom_inputs(properties.get("borefield").variant("custom").defaults()["points"]))
    assert result.number_of_boreholes == 60
    assert 50 < result.borehole_length < 300


def test_overlapping_boreholes_are_reported():
    errors = model.validate(_custom_inputs(((0.0, 0.0), (0.1, 0.0))))
    assert "overlap" in errors["borefield"][0]
