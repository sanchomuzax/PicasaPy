"""#4553 — a fókuszpont egérrel húzható az előnézeti képen."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_editor_panel_rendered_651 import _child
from tests.app.qml_functional.test_effect_sliders import _as_list
from tests.support.varakozas import var_feltetelre


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
    pytest.param("linblur", 5, "legacyEffect_linblur", False, id="linblur"),
    pytest.param("dir_sat", 5, "legacyEffect_dir_sat", False, id="dir_sat"),
    pytest.param("dir_brite", 5, "legacyEffect_dir_brite", False, id="dir_brite"),
    pytest.param("dir_sharp", 5, "legacyEffect_dir_sharp", False, id="dir_sharp"),
]

_IRANYITOTT_EFFEKTEK = {"dir_sat", "dir_brite", "dir_sharp"}


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


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 10.0):
    if not var_feltetelre(qt_app, feltetel, masodperc):
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

    gomb = _child(ablak.contentItem(), csempe)
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

    puck = _child(ablak.contentItem(), "viewerEffectFocalPuck")
    assert puck.property("visible") is True
    assert puck.width() > 0 and puck.height() > 0

    eredeti_magassag = ablak.height()
    celpontok = (
        ((0.92, 0.08), (0.18, 0.84), (0.81, 0.20))
        if kulcs in _IRANYITOTT_EFFEKTEK
        else ((0.68, 0.34), (0.32, 0.67), (0.61, 0.72))
    )
    for magassag_elteres, (cel_x, cel_y) in zip(
        (-5, 0, 5), celpontok, strict=True
    ):
        ablak.resize(ablak.width(), eredeti_magassag + magassag_elteres)
        _varj(
            qt_app,
            lambda cel=eredeti_magassag + magassag_elteres:
                ablak.height() == cel,
            "az ablak nem vette fel a kért magasságot",
        )
        ertekek_elotte = list(_as_list(panel.property("paramEffectValues")))
        irany_x = (
            (ertekek_elotte[0] + 1.0) / 2.0
            if kulcs in _IRANYITOTT_EFFEKTEK else ertekek_elotte[0]
        )
        irany_y = (
            (ertekek_elotte[1] + 1.0) / 2.0
            if kulcs in _IRANYITOTT_EFFEKTEK else ertekek_elotte[1]
        )
        kezdo = puck.mapToScene(
            QPointF(puck.width() * irany_x, puck.height() * irany_y)
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
        vart_x = cel_x * 2.0 - 1.0 if kulcs in _IRANYITOTT_EFFEKTEK else cel_x
        vart_y = cel_y * 2.0 - 1.0 if kulcs in _IRANYITOTT_EFFEKTEK else cel_y
        assert ertekek[0] == pytest.approx(vart_x, abs=0.01)
        assert ertekek[1] == pytest.approx(vart_y, abs=0.01)

        if kulcs == "linblur":
            vart_mennyiseg = {
                -5: 2.0,
                0: 5.0,
                5: 8.0,
            }[magassag_elteres]
            panel.updateParamValue(2, vart_mennyiseg)
            _varj(
                qt_app,
                lambda cel=vart_mennyiseg:
                    _as_list(panel.property("paramEffectValues"))[2] == cel,
                "a linblur mennyiségértéke nem állt be",
            )
            x_csuszka = _child(panel, "effectParamSlider0")
            y_csuszka = _child(panel, "effectParamSlider1")
            amount_csuszka = _child(panel, "effectParamSlider2")
            amount_cimke = _child(panel, "effectParamLabel2")
            assert x_csuszka.property("visible") is False
            assert y_csuszka.property("visible") is False
            assert amount_csuszka.property("value") == pytest.approx(
                vart_mennyiseg
            )
            assert amount_cimke.property("visible") is True
            assert amount_cimke.property("text") == "Amount"
        else:
            x_csuszka = _child(panel, "effectParamSlider0")
            y_csuszka = _child(panel, "effectParamSlider1")
            x_cimke = _child(panel, "effectParamLabel0")
            y_cimke = _child(panel, "effectParamLabel1")
            assert x_csuszka.property("value") == pytest.approx(ertekek[0])
            assert y_csuszka.property("value") == pytest.approx(ertekek[1])
            if kulcs in _IRANYITOTT_EFFEKTEK:
                assert x_cimke.property("text") == "Left to Right"
                assert y_cimke.property("text") == "Top to Bottom"

        if kulcs == "dir_tint":
            assert puck.property("directional") is True
            assert puck.property("directionAngle") == pytest.approx(
                (ertekek[0] - 0.5) * 30.0
            )
        else:
            assert puck.property("directional") is False
        assert puck.property("directionalAxes") is (
            kulcs in _IRANYITOTT_EFFEKTEK
        )

        # A valódi, kirajzolt nézőkép bizonyítéka; a görgetés és a betűk
        # platformfüggő geometriáját a teszt nem méri.
        kep = ablak.grabWindow()
        assert not kep.isNull(), "a néző képe nem rajzolódott ki"
        assert kep.save(
            str(tmp_path / f"focal-puck-{kulcs}-{magassag_elteres}.png")
        )


# Rontás-kontroll: a `viewerEffectFocalPuck` példányt a javítás nélkül nem
# lehet megtalálni; a hat paraméterezett effekt mind piros.
