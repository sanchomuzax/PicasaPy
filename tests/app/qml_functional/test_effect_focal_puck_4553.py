"""#4553 — a fókuszpont egérrel húzható az előnézeti képen."""

from __future__ import annotations

import time

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_editor_panel_rendered_651 import _child
from tests.app.qml_functional.test_effect_sliders import _as_list


_EFFEKTEK = [
    pytest.param("radblur", 2, "effectRadblur", False, id="radblur"),
    pytest.param("radsat", 2, "effectRadsat", False, id="radsat"),
    pytest.param("dir_tint", 2, "effectDirTint", False, id="dir_tint"),
    pytest.param("radtint", 2, "effectDirTint", True, id="radtint"),
    pytest.param("focalzoom", 4, "effectFocalZoom", False, id="FocalZoom"),
    pytest.param(
        "picnikfocalpixelate", 4, "effectPixelate", True,
        id="PicnikFocalPixelate",
    ),
]


def _kepeket_keszit(konyvtar):
    """Színes tesztkép, amin a fókusz áthelyezése a renderben is látható."""
    y, x = np.indices((320, 480), dtype=np.uint16)
    rgb = np.empty((320, 480, 3), dtype=np.uint8)
    rgb[..., 0] = (x * 3 + y) % 256
    rgb[..., 1] = (y * 2 + x // 2) % 256
    rgb[..., 2] = ((x // 16 + y // 16) % 2) * 220 + 20
    Image.fromarray(rgb, "RGB").save(
        konyvtar / "a.jpg", format="JPEG", quality=100, subsampling=0
    )
    Image.fromarray(rgb[::-1].copy(), "RGB").save(
        konyvtar / "b.jpg", format="JPEG", quality=100, subsampling=0
    )


@pytest.fixture
def focal_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_kepeket_keszit,
        valodi_belyegkep=True,
    )


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 5.0):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    raise AssertionError(uzenet)


@pytest.mark.parametrize("kulcs,ful,csempe,shift", _EFFEKTEK)
def test_a_fokuszpuck_huzasa_mozgatja_a_pontot_es_a_csuszkat(
    focal_app,
    qt_app,
    tmp_path,
    kulcs,
    ful,
    csempe,
    shift,
):
    ablak, _vezerlo, _engine = focal_app
    ablak.setProperty("viewerOpen", True)
    nezo = ablak.findChild(QObject, "photoViewer")
    assert nezo is not None
    nezo.setProperty("currentIndex", 0)
    panel = ablak.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
    panel.setProperty("activeTab", ful)
    panel.setProperty("shiftMasodlagos", shift)
    _varj(
        qt_app,
        lambda: panel.property("activeTab") == ful,
        "az effektfül nem váltott át",
    )

    gomb = ablak.findChild(QObject, csempe)
    assert gomb is not None, f"a {kulcs} effekt csempéje hiányzik"
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        gomb.mapToScene(gomb.boundingRect().center()).toPoint(),
    )
    _varj(
        qt_app,
        lambda: panel.property("paramPanelActive") is True,
        f"a {kulcs} paraméterpanelje nem nyílt meg",
    )
    assert panel.property("paramEffectName") == kulcs

    puck = ablak.findChild(QObject, "viewerEffectFocalPuck")
    assert puck is not None, f"a {kulcs} fókuszpuckja nem jelent meg a képen"
    assert puck.property("visible") is True
    assert puck.width() > 0 and puck.height() > 0

    eredeti_magassag = ablak.height()
    for magassag_elteres, (cel_x, cel_y) in zip(
        (-5, 0, 5), ((0.68, 0.34), (0.32, 0.67), (0.61, 0.72)), strict=True
    ):
        ablak.resize(ablak.width(), eredeti_magassag + magassag_elteres)
        _varj(
            qt_app,
            lambda cel=eredeti_magassag + magassag_elteres:
                ablak.height() == cel,
            "az ablak nem vette fel a kért magasságot",
        )
        ertekek_elotte = list(_as_list(panel.property("paramEffectValues")))
        kezdo = puck.mapToScene(
            QPointF(puck.width() * ertekek_elotte[0], puck.height() * ertekek_elotte[1])
        )
        cel = puck.mapToScene(QPointF(puck.width() * cel_x, puck.height() * cel_y))
        QTest.mousePress(
            ablak,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            kezdo.toPoint(),
        )
        QTest.mouseMove(ablak, cel.toPoint())
        QTest.mouseRelease(
            ablak,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            cel.toPoint(),
        )
        qt_app.processEvents()

        ertekek = list(_as_list(panel.property("paramEffectValues")))
        assert ertekek[0] == pytest.approx(cel_x, abs=0.01)
        assert ertekek[1] == pytest.approx(cel_y, abs=0.01)
        x_csuszka = _child(panel, "effectParamSlider0")
        y_csuszka = _child(panel, "effectParamSlider1")
        assert x_csuszka.property("value") == pytest.approx(ertekek[0])
        assert y_csuszka.property("value") == pytest.approx(ertekek[1])

        if kulcs == "dir_tint":
            assert puck.property("directional") is True
            assert puck.property("directionAngle") == pytest.approx(
                (ertekek[0] - 0.5) * 30.0
            )
        else:
            assert puck.property("directional") is False

        # A valódi, kirajzolt nézőkép bizonyítéka; a görgetés és a betűk
        # platformfüggő geometriáját a teszt nem méri.
        kep = ablak.grabWindow()
        assert not kep.isNull(), "a néző képe nem rajzolódott ki"
        assert kep.save(
            str(tmp_path / f"focal-puck-{kulcs}-{magassag_elteres}.png")
        )


# Rontás-kontroll: a `viewerEffectFocalPuck` példányt a javítás nélkül nem
# lehet megtalálni; a hat paraméterezett effekt mind piros.
