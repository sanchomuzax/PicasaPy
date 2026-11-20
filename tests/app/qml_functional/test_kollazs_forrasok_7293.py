"""A fejléc és a Létrehozás menü forrásképei (#7293).

A mért szabály: fejlécnél nulla vagy egy csoporton belüli kijelölés a teljes
csoportot teszi a vászonra; a menü kijelölés nélkül a teljes mappát veszi.
Két vagy több kijelölt kép mindkét belépőnél a vászonra kerül, a mappa
fennmaradó képei pedig a Klipek listába.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional._fomenu_4420_menu import (
    _elero_menu,
    _kattints as _kattints_menu,
    _megnyit,
)
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre


_MINTA_KEPEK = 5
_MAGASSAG_ELTOLASOK = (-5, 0, 5)
_DARABOK = {
    "header": ((5, 0), (5, 0), (2, 3), (3, 2)),
    "menu": ((5, 0), (1, 4), (2, 3), (3, 2)),
}
_KIJELÖLÉS_SORREND = {"header": (0, 1, 2, 3), "menu": (1, 2, 3, 0)}


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elem(window, object_name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == object_name:
            return item
    return window.findChild(QQuickItem, object_name)


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _kattints(window, item: QQuickItem, qt_app) -> None:
    assert item is not None and item.isEnabled(), "a valódi vezérlő nem kattintható"
    assert item.width() > 0 and item.height() > 0, "a vezérlőnek nincs mérete"
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _allitsd_kijelolest(window, qt_app, count: int) -> None:
    rows = list(range(count))
    window.setProperty("selectedIndexes", rows)
    window.setProperty("selectedIndex", rows[0] if rows else -1)
    qt_app.processEvents()


def _merd_a_kimenetet(window, controller, qt_app, vart_vaszon: int, vart_klip: int):
    vaszon_db = controller.collageNodes.rowCount()

    clips_button = _elem(window, "collageClipsTabButton")
    _kattints(window, clips_button, qt_app)
    clips_tab = _elem(window, "collageClipsTab")
    assert _var(qt_app, lambda: clips_tab.property("visible") is True), (
        "a Klipek fül nem nyílt meg"
    )
    clips_list = _elem(window, "collageClipList")
    qt_app.processEvents()
    klip_db = int(clips_list.property("count"))
    felirat = str(clips_button.property("text"))
    return (vaszon_db, klip_db, felirat), (vart_vaszon, vart_klip, f"Clips ({vart_klip})")


def _futtasd_negy_kijelolest(window, controller, qt_app, belepo: str) -> None:
    assert controller.photos.rowCount() == _MINTA_KEPEK
    elteresek = []
    for kijeloles in _KIJELÖLÉS_SORREND[belepo]:
        vart_vaszon, vart_klip = _DARABOK[belepo][kijeloles]
        controller.closeCollage()
        _allitsd_kijelolest(window, qt_app, kijeloles)

        if belepo == "header":
            gomb = _elem(window, "headerCollageButton")
            _kattints(window, gomb, qt_app)
        else:
            menu_bar = window.property("menuBar")
            _megnyit(menu_bar, qt_app, "&Create")
            # A Picture Collage sor a negyedik tényleges menüelem.
            parancs = _elero_menu(menu_bar, qt_app, "&Create", (3,))
            assert parancs.objectName() == "menuCreateCollage"
            if not parancs.isEnabled():
                elteresek.append(
                    f"0 kijelölésnél a menüpont letiltott; "
                    f"várt vászon/klip: {vart_vaszon}/{vart_klip}"
                )
                continue
            _kattints_menu(qt_app, parancs)

        assert _var(qt_app, lambda: controller.collageOpen is True), (
            f"a {belepo} belépő nem nyitotta meg a kollázst "
            f"{kijeloles} kijelölt képnél"
        )
        actual, expected = _merd_a_kimenetet(
            window, controller, qt_app, vart_vaszon, vart_klip
        )
        if actual != expected:
            elteresek.append(
                f"{kijeloles} kijelölés: {actual!r}, várt {expected!r}"
            )
    assert not elteresek, f"{belepo} kollázsforrás-eltérések: " + "; ".join(elteresek)


@pytest.mark.parametrize("magassag_eltolas", _MAGASSAG_ELTOLASOK)
def test_a_mappafejlec_0_1_2_3_kijelolest_mer(
    qml_app_5_negyzet_kep, qt_app, magassag_eltolas
):
    window, controller, _engine = qml_app_5_negyzet_kep
    window.setHeight(window.height() + magassag_eltolas)
    assert _var(qt_app, lambda: window.height() > 0)
    _futtasd_negy_kijelolest(window, controller, qt_app, "header")


@pytest.mark.parametrize("magassag_eltolas", _MAGASSAG_ELTOLASOK)
def test_a_letrehozas_menu_0_1_2_3_kijelolest_mer(
    qml_app_5_negyzet_kep, qt_app, magassag_eltolas
):
    window, controller, _engine = qml_app_5_negyzet_kep
    window.setHeight(window.height() + magassag_eltolas)
    assert _var(qt_app, lambda: window.height() > 0)
    _futtasd_negy_kijelolest(window, controller, qt_app, "menu")
