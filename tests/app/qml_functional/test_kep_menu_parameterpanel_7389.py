"""#7389: Nyitott effekt-paraméterpanelnél a Kép menü és a Csoportos szerkesztés
almenü tételei legyenek letiltva.

Spec: docs/specs/paritas-folyamat-7346.md T7.
Eredeti viselkedés (job-878 #15, #17): nyitott Soft Focus panel mellett a
teljes Kép menü szürke (View and Edit, Batch Edit, Undo All Edits, Hide,
Unhide, Reset Faces, Properties), a Batch Edit kijelölve, de nem nyit almenüt.
A panel nem kerül felfüggesztett állapotba, a lánc és a kép változatlan.
A panel bezárása (Alkalmaz, Mégse, Escape) után a menü újra él.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    gyerek,
    szures,
    varj,
    zar,
)
from tests.app.qml_functional._nezet_menu_5150_helpers import almenu_sora
from tests.app.qml_functional._szerkeszto_5150_helpers import item, kattint

_HET_TETEL = (
    "menuPictureViewAndEdit",
    "menuPictureBatchEdit",
    "menuPictureUndoAllEdits",
    "menuPictureHide",
    "menuPictureUnhide",
    "menuPictureResetFaces",
    "menuPictureProperties",
)

_EFFEKTEK_FUL = 2


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _nezot_nyit(window, qt_app, ful: int = _EFFEKTEK_FUL):
    window.setProperty("viewerOpen", True)
    nezo = gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = gyerek(window, "viewerEditorPanel")
    panel.setProperty("activeTab", ful)
    qt_app.processEvents()
    return nezo, panel, nezo.property("editCtl")


def _kezdo_allapot(kep_app, qt_app, ful: int = _EFFEKTEK_FUL):
    window, controller, _engine = kep_app
    elokeszit(window, qt_app, controller)
    nezo, panel, szerk = _nezot_nyit(window, qt_app, ful)
    assert szures(controller, 0) == "", "a kiinduló lánc nem üres: nem bizonyít"
    return window, controller, panel, szerk


def _kattints_elemre(qt_app, elem):
    assert elem is not None, "az elem hiányzik"
    center = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _kep_menut_nyit(window, qt_app):
    menu_bar = window.property("menuBar")
    fejlec = next(
        elem
        for elem in menu_bar.findChildren(QObject)
        if "MenuBarItem" in elem.metaObject().className()
        and elem.property("text") in {"&Picture", "&Kép"}
    )
    _kattints_elemre(qt_app, fejlec)
    menu = next(
        elem
        for elem in menu_bar.findChildren(QObject)
        if elem.property("title") in {"&Picture", "&Kép"}
    )
    assert varj(qt_app, lambda: menu.property("opened") is True), (
        "a Kép menü nem nyílt meg valódi kattintásra"
    )
    return menu


class TestKepMenuNyitottParameterpanelnel:
    def test_nyitott_soft_focus_panelnel_a_kep_menu_het_tetele_szurke_es_almenu_nem_nyilik(
        self, kep_app, qt_app
    ):
        """Soft Focus nyitásakor a 7 tétel szürke, a Batch Edit nem nyit almenüt,
        és a panel nem kerül felfüggesztett állapotba."""
        window, controller, panel, _szerk = _kezdo_allapot(kep_app, qt_app)
        kattint(window, item(window, "effectRadblur"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True), (
            "a Soft Focus nem nyitotta meg a paraméterpanelt"
        )
        assert panel.property("paramEffectName") == "radblur"

        menu = _kep_menut_nyit(window, qt_app)

        for tetel_nev in _HET_TETEL:
            tetel = gyerek(window, tetel_nev)
            assert tetel.property("enabled") is False, (
                f"nyitott Soft Focus panel mellett a {tetel_nev} tétel aktív maradt"
            )

        # Batch Edit almenü kattintási próbája: letiltott sorként nem nyithat almenüt
        sor, almenu = almenu_sora(window, menu, "menuPictureBatchEdit")
        assert sor.property("enabled") is False
        _kattints_elemre(qt_app, sor)
        assert almenu.property("opened") is False, (
            "a letiltott Batch Edit almenü megnyílt a kattintásra"
        )

        # A panel nem került felfüggesztett állapotba, a lánc és a kép változatlan
        assert panel.property("paramPanelSuspended") is False, (
            "a panel felfüggesztett állapotba került a menükattintásra"
        )
        assert szures(controller, 0) == "", (
            "a lánc megváltozott a menüművelet alatt"
        )
        zar(qt_app, menu)

    def test_sharpen_es_film_grain_panelnel_is_szurke_megse_es_escape_utan_ujra_el(
        self, kep_app, qt_app
    ):
        """Sharpen és Film Grain panel mellett is szürke a menü, és a Mégse/Escape után újra él."""
        window, _controller, panel, _szerk = _kezdo_allapot(kep_app, qt_app)

        # 1. Sharpen panel
        kattint(window, item(window, "effectUnsharp"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True)
        menu = _kep_menut_nyit(window, qt_app)
        assert gyerek(window, "menuPictureBatchEdit").property("enabled") is False
        assert gyerek(window, "menuPictureProperties").property("enabled") is False
        zar(qt_app, menu)

        # Mégse gomb a panelen
        kattint(window, item(window, "effectParamCancelButton"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is False)
        assert gyerek(window, "menuPictureBatchEdit").property("enabled") is True
        assert gyerek(window, "menuPictureProperties").property("enabled") is True

        # 2. Film Grain panel (csempéje a 3. lapon: PicnikGrain)
        kattint(window, item(window, "effectPicnikGrain"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True)
        menu2 = _kep_menut_nyit(window, qt_app)
        assert gyerek(window, "menuPictureBatchEdit").property("enabled") is False
        zar(qt_app, menu2)

        # Escape leütése a nézőben bezárja a panelt
        QTest.keyClick(window, Qt.Key.Key_Escape)
        qt_app.processEvents()
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is False)
        assert gyerek(window, "menuPictureBatchEdit").property("enabled") is True

    def test_panel_alkalmazasa_utan_is_ujra_el_a_menu(self, kep_app, qt_app):
        """Alkalmaz gomb megnyomása után a paraméterpanel bezárul és a menü újra él."""
        window, _controller, panel, _szerk = _kezdo_allapot(kep_app, qt_app)
        kattint(window, item(window, "effectRadblur"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True)

        menu = _kep_menut_nyit(window, qt_app)
        assert gyerek(window, "menuPictureBatchEdit").property("enabled") is False
        zar(qt_app, menu)

        kattint(window, item(window, "effectParamApplyButton"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is False)
        assert gyerek(window, "menuPictureBatchEdit").property("enabled") is True
        assert gyerek(window, "menuPictureViewAndEdit").property("enabled") is True

    def test_select_menu_effect_nyitott_panelnel_nem_fuggeszti_fel_a_panelt(
        self, kep_app, qt_app
    ):
        """A selectMenuEffect hívása nyitott panelnél sem hívhat selectTab-ot és nem függeszthet fel."""
        window, controller, panel, _szerk = _kezdo_allapot(kep_app, qt_app)
        kattint(window, item(window, "effectRadblur"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True)

        nezo = gyerek(window, "photoViewer")
        # Közvetlen hívás a néző selectMenuEffect függvényére
        nezo.selectMenuEffect("autolight")
        qt_app.processEvents()

        assert panel.property("paramPanelActive") is True
        assert panel.property("paramPanelSuspended") is False, (
            "a selectMenuEffect felfüggesztette a nyitott panelt"
        )
        assert szures(controller, 0) == ""
