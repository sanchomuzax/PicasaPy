"""A Fájl ▸ Visszaállítás tétel a mentés után azonnal engedélyezett (#5206).

A mentés VALÓDI kattintásokkal indul: a Fájl ▸ Save tételre kattintunk, majd a
megerősítő párbeszéd Mentés gombjára. A mentés befejezését (`saveFinished`)
megvárjuk, aztán a Fájl menüt valódi kattintással megnyitjuk.

Megjegyzés: a mentés utáni nézetfrissítés (modell-újratöltés) a kijelölést
újraírja, ami önmagában is újraértékeli a kötést. Ezért ez a teszt a teljes
menüutat védi, de a javítást nem egyedül bizonyítja. A notify-jelzést és a
számláló léptetését a `tests/app/test_save_controller.py` pinezi, ott a
régi viselkedés reprodukálható bukással.

A főmenü wrapperét a teszt függvényében tartjuk: a rövid életű Python-wrapper
felszabadulása a menüsor C++ objektumát is elvihetné.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.qt_wait import wait_for_photo_op, wait_for_signal
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional.test_fajl_szerkesztes_menu_valodi_5150 import (  # noqa: F401
    _elokeszit,
    _gyerek,
    _varj,
    fajl_app,
)


def _klikk(qt_app, ablak, elem) -> None:
    """Valódi bal kattintás az `elem` közepén, a MEGTARTOTT `ablak`-ra küldve.

    Az `elem.window()` új wrappert ad vissza, és a Python ezt felszabadíthatja,
    ami a főablakot is megsemmisíti (ld. `test_menu_talca_egyeb_valodi_5135_b`).
    """
    assert elem is not None, "a kattintandó elem hiányzik"
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName() or 'az elem'}: nincs kattintható mérete"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _vizualis_bejaras(item: QQuickItem):
    """A VIZUÁLIS fa bejárása: a gombok nem feltétlenül QObject-gyerekek."""
    for gyerek in item.childItems():
        yield gyerek
        yield from _vizualis_bejaras(gyerek)


def _gomb_szovege(parbeszed, szovegek: tuple[str, ...]) -> QQuickItem:
    """A párbeszéd láblécének látható gombja a megadott felirattal."""
    lab = parbeszed.property("footer")
    assert lab is not None, "a megerősítésnek nincs lábléce"
    for elem in _vizualis_bejaras(lab):
        if elem.property("text") in szovegek and elem.isVisible():
            return elem
    raise AssertionError(f"a láblécen nincs gomb: {szovegek}")


def _mentes_valodi_kattintassal(window, menu_bar, qt_app, controller) -> None:
    """Fájl ▸ Save valódi kattintással, majd a megerősítő Mentés gombjával.

    A kattintás után a mentés befejezését megvárjuk, és csak utána térünk
    vissza a teszthez.
    """
    mentes_tetel = _fajl_menu_tetele(window, menu_bar, qt_app, "menuFileSave")
    _klikk(qt_app, window, mentes_tetel)
    parbeszed = _gyerek(window, "saveConfirmDialog")
    assert _varj(qt_app, lambda: parbeszed.property("visible") is True), (
        "a Fájl ▸ Save nem kérdezett rá a mentésre"
    )
    mentes = _gomb_szovege(parbeszed, ("Save", "Mentés"))
    wait_for_signal(
        controller.saveFinished,
        action=lambda: _klikk(qt_app, window, mentes),
        description="a mentés",
        process_events_with=qt_app,
    )


def _fajl_menu_tetele(window, menu_bar, qt_app, nev: str):
    """Megnyitja a Fájl menüt valódi kattintással, és visszaadja a tételt."""
    _megnyit(menu_bar, qt_app, "&File")
    return _gyerek(window, nev)


class TestMentesUtan:
    def test_mentes_utan_a_visszaallitas_engedelyezett_kijeloles_nelkul(
        self, fajl_app, qt_app  # noqa: F811
    ):
        window, controller, _engine = fajl_app
        menu_bar = window.property("menuBar")
        _elokeszit(window, qt_app, controller)
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        wait_for_photo_op(
            controller,
            lambda: controller.applyEffectMany([0], "enhance"),
            qt_app=qt_app,
        )
        assert _gyerek(window, "menuFileRevert").property("enabled") is False, (
            "a próba előfeltétele: mentés előtt a Visszaállítás tiltott legyen"
        )

        _mentes_valodi_kattintassal(window, menu_bar, qt_app, controller)

        tetel = _fajl_menu_tetele(window, menu_bar, qt_app, "menuFileRevert")
        assert _varj(qt_app, lambda: tetel.property("enabled") is True), (
            "mentés után a Fájl ▸ Visszaállítás tiltott maradt; csak a "
            "kijelölés megváltoztatása engedélyezte volna"
        )
