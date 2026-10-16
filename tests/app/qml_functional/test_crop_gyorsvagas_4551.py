"""Vágó panel: nincsenek az eredetiben nem létező feliratos gyorsvágás-gombok
(#4551).

## A lelet

Az eredeti Picasa vágó panelén csak a HÁROM bélyegképes javaslat van
(`editpanel/cropsug1..3`, #448). A „Bal felső / Fekvő / Álló" feliratos
gombok a régi, javaslat-előtti vázból maradtak meg; az eredetiben nincs
ilyen gomb, és a `picasa-menu-parancsok-viselkedes.md` 53.2 szakasza is
csak „többletként" tartja nyilván őket.

## Mit mér ez a fájl

- a három feliratos gomb nincs a panelen, −5 / 0 / +5 px ablakmagasságnál;
- a javaslat-sor VALÓDI kattintással még működik (a sor nem sérült);
- a Forgatás-sor közvetlenül a javaslat-sor alá kerül, a törölt sor helyén
  nem marad rés (a `ColumnLayout` 8 px-es közének megfelelően).
"""
from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

_GYORSVAGAS_GOMBOK = (
    "quickCropTopleft",
    "quickCropLandscape",
    "quickCropPortrait",
)

# a `ColumnLayout` közei (EditorCropPanel.qml: spacing: 8)
_OSZLOP_KOZ = 8


def _vagas_megnyitas(window, qt_app):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = window.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("cropActive", True)
    qt_app.processEvents()
    return panel


def _kozep(elem):
    return elem.mapToScene(
        QPointF(elem.width() / 2, elem.height() / 2)
    ).toPoint()


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
class TestNincsGyorsvagasGomb:
    def test_nincs_a_harom_feliratos_gyorsvagas_gomb(
        self, qml_app, qt_app, height_offset
    ):
        window, _, _ = qml_app
        window.setHeight(window.height() + height_offset)
        qt_app.processEvents()
        _vagas_megnyitas(window, qt_app)

        for name in _GYORSVAGAS_GOMBOK:
            assert window.findChild(QObject, name) is None, (
                f"az eredetiben nem létező gomb maradt: {name}"
            )

    def test_a_javaslat_sor_valodi_kattintasra_is_kivalasztja(
        self, qml_app, qt_app, height_offset
    ):
        """A törölt sor nem vitte magával a javaslat-sort: a 0. javaslatra
        kattintva a kijelölés létrejön."""
        window, _, _ = qml_app
        window.setHeight(window.height() + height_offset)
        qt_app.processEvents()
        _vagas_megnyitas(window, qt_app)

        gomb = window.findChild(QObject, "cropSuggestion0")
        assert gomb is not None and gomb.isVisible()
        overlay = window.findChild(QObject, "cropOverlay")
        assert overlay.property("hasSelection") is False

        kozep = _kozep(gomb)
        QTest.mouseMove(window, kozep, 10)
        qt_app.processEvents()
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
            kozep,
        )
        qt_app.processEvents()
        assert overlay.property("hasSelection") is True

    def test_a_forgatas_sor_a_javaslat_sor_ala_kerul_res_nelkul(
        self, qml_app, qt_app, height_offset
    ):
        window, _, _ = qml_app
        window.setHeight(window.height() + height_offset)
        qt_app.processEvents()
        _vagas_megnyitas(window, qt_app)

        sor = window.findChild(QObject, "cropSuggestionRow")
        forgatas = window.findChild(QObject, "cropRotateButton")
        assert sor is not None and forgatas is not None

        sor_alja = sor.mapToScene(QPointF(0, sor.height())).y()
        forgatas_teteje = forgatas.mapToScene(QPointF(0, 0)).y()
        res = forgatas_teteje - sor_alja
        assert res <= _OSZLOP_KOZ + 0.5, (
            f"{res:.1f} px rés a javaslat-sor és a Forgatás között "
            "(a törölt gyorsvágás-sor helye maradt meg)"
        )


def test_a_vagasi_panel_kepe_renderelodik(qml_app, qt_app, tmp_path):
    """Renderelt kép a vágó panelről: a képernyő a panellel együtt kirajzolódik
    és PNG-be menthető. A referencia-képernyőkép (NAS) összevetése nem ennek
    a tesztnek a dolga — az a jegy kézi ellenőrzése."""
    window, _, _ = qml_app
    _vagas_megnyitas(window, qt_app)
    assert window.findChild(QObject, "cropRotateButton") is not None
    kep = window.grabWindow()
    cel = tmp_path / "vagasi_panel_4551.png"
    assert kep.save(str(cel)), "a vágó panel képe nem menthető"
    assert kep.width() > 0 and kep.height() > 0
