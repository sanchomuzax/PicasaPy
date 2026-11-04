"""Az Effekt-térszelvény rajzgeometriája, mérése és tartós állapota (#6522)."""

# SAJÁT FUNKCIÓ (#6522): az őrök a PicasaPy saját térszelvényét védik, az eredeti Picasában nincs ilyen.

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QRectF, QSettings

from picasapy.app.effect_slice import EffectSliceController
from picasapy.app.effect_slice_paint import (
    DIMENSIONS,
    interpolate_row,
    make_projection,
    ramp_color,
)
from picasapy.app.effect_slice_render import _color_cube, render_surface
from picasapy.ini.filters import parse_filters

RECT = QRectF(0.0, 0.0, 212.0, 105.0)


@pytest.mark.parametrize("azimuth", (-180.0, -32.0, 0.0, 45.0, 90.0, 137.0))
@pytest.mark.parametrize("kind", ("tone", "color", "point"))
def test_a_keret_nyolc_sarka_minden_szogben_kitolti_a_rajzteruletet(azimuth, kind):
    project = make_projection(DIMENSIONS[kind], azimuth, 28.0, RECT)
    corners = [project(u, v, w) for u in (0, 1) for v in (0, 1) for w in (0, 1)]
    xs = [corner[0] for corner in corners]
    ys = [corner[1] for corner in corners]

    assert min(xs) >= 1.9 and max(xs) <= RECT.width() - 1.9
    assert min(ys) >= 1.4 and max(ys) <= RECT.height() - 1.4
    # legalább az egyik irányban széltől szélig ér (nem marad sok üres hely)
    assert (max(xs) - min(xs)) == pytest.approx(RECT.width() - 4.0, abs=0.01) or (
        max(ys) - min(ys)
    ) == pytest.approx(RECT.height() - 3.0, abs=0.01)


def test_a_szinskala_vilagosbol_sotetkekbe_megy():
    low = ramp_color(0.0, 1.0)
    high = ramp_color(1.0, 1.0)

    assert (low.red(), low.green(), low.blue()) == (227, 237, 248)
    assert (high.red(), high.green(), high.blue()) == (29, 79, 145)


def test_a_jelolo_a_csuszka_tort_allasat_soronkent_interpolalja():
    rows = [[0.0, 0.0], [1.0, 0.5]]

    assert interpolate_row(rows, 0.0) == [0.0, 0.0]
    assert interpolate_row(rows, 0.5) == [0.5, 0.25]
    assert interpolate_row(rows, 1.0) == [1.0, 0.5]


def test_a_szinkocka_pontja_oda_kerul_ahova_az_effekt_a_szint_viszi():
    surface = _color_cube(tuple(parse_filters("bw=1;")))

    for point in surface["points"]:
        assert point["x"] == pytest.approx(point["color"][0] / 255.0)
        assert point["y"] == pytest.approx(point["color"][1] / 255.0)
        assert point["z"] == pytest.approx(point["color"][2] / 255.0)
    # fekete-fehérben minden pont a szürke átlóra esik
    assert all(p["color"][0] == p["color"][1] == p["color"][2] for p in surface["points"])


def test_szines_lancnal_a_csatornak_szetvalnak():
    ops = tuple(parse_filters("contrast=1,0.1;colortemp=1,0.6;"))
    target = EffectSliceController._chain_depth_target(ops, "tone")
    depth = {key: target[key] for key in ("operationIndex", "parameterIndex", "minimum", "maximum", "current")}

    surface = render_surface(None, ops, "tone", depth=depth)

    assert target["label"] == "Contrast"
    assert len(surface["rows"]) == 12
    spread = max(
        abs(red - blue)
        for row in surface["channels"]
        for red, blue in zip(row[0], row[2], strict=True)
    )
    assert spread > 0.05


def _controller(tmp_path) -> EffectSliceController:
    settings = QSettings(str(tmp_path / "beallitas.ini"), QSettings.Format.IniFormat)
    edit = SimpleNamespace(_photo_id="", _provider=None, _image_size=None)
    return EffectSliceController(edit, settings=settings)


def test_a_menu_allasa_es_a_forgas_ujrainditas_utan_megmarad(qt_app, tmp_path):
    first = _controller(tmp_path)
    assert first.mode == "editing"
    assert first.spinning is True
    first.setMode("never")
    first.setSpinning(False)
    first._settings.sync()

    second = _controller(tmp_path)

    assert second.mode == "never"
    assert second.spinning is False


def test_ervenytelen_menuallas_az_alapertekre_esik_vissza(qt_app, tmp_path):
    settings = QSettings(str(tmp_path / "beallitas.ini"), QSettings.Format.IniFormat)
    settings.setValue("view/effectSlice", "valami")
    controller = EffectSliceController(
        SimpleNamespace(_photo_id=""), settings=settings
    )

    controller.setMode("hibas")

    assert controller.mode == "editing"


def test_a_jelolo_csak_a_tonus_feluleten_jelenik_meg(qt_app, tmp_path):
    controller = _controller(tmp_path)
    target = {"minimum": 0.0, "maximum": 1.0, "current": 0.5}
    image = {"kind": "image", "rows": [[0.0, 0.0], [0.0, 0.0]]}
    tone = {"kind": "tone", "rows": [[0.0, 0.0], [1.0, 1.0]]}

    controller._set_marker(image, target)
    controller._set_marker(tone, target)

    assert image["hasMarker"] is False
    assert tone["hasMarker"] is True
    assert tone["current"] == 0.5


def test_a_finomhangolas_ful_utoljara_mozgatott_csuszkaja_a_melysegtengely(qt_app, tmp_path):
    from picasapy.edit.session import EditSession

    controller = _controller(tmp_path)
    controller._edit = SimpleNamespace(
        _photo_id="1",
        _provider=None,
        _image_size=None,
        _image_path=None,
        _session=EditSession.from_value("contrast=1,0.1;"),
    )

    controller.request("finetune2", [0.0, 0.0, 0.0, 0.5], 3, "", "", "")

    assert controller.sliderLabel == "Color Temperature"
    assert controller.sliderValue == pytest.approx(0.5)
    assert controller.chainLength == 2
    controller.shutdown()


def test_a_kepszolgaltato_a_vezerlo_adatabol_nem_ures_kepet_rajzol(qt_app, tmp_path):
    from PySide6.QtCore import QSize

    from picasapy.app.effect_slice import EffectSliceImageProvider

    controller = _controller(tmp_path)
    ops = tuple(parse_filters("contrast=1,0.1;"))
    target = EffectSliceController._chain_depth_target(ops, "tone")
    depth = {key: target[key] for key in ("operationIndex", "parameterIndex", "minimum", "maximum", "current")}
    controller._surface_data = render_surface(None, ops, "tone", depth=depth)
    controller._set_marker(controller._surface_data, target)
    provider = EffectSliceImageProvider(controller)
    size = QSize()

    image = provider.requestImage("35/1", size, QSize(424, 210))

    assert (image.width(), image.height()) == (424, 210)
    assert (size.width(), size.height()) == (424, 210)
    # a felület kék, a jelölő narancs: mindkét szín megjelenik
    kek = narancs = 0
    for x in range(0, 424, 3):
        for y in range(0, 210, 3):
            pixel = image.pixelColor(x, y)
            if pixel.alpha() > 200 and pixel.blue() > pixel.red() + 40:
                kek += 1
            if pixel.alpha() > 200 and pixel.red() > 180 and pixel.blue() < 80:
                narancs += 1
    assert kek > 200
    assert narancs > 5
