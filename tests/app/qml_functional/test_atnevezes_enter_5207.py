"""Az Átnevezés párbeszéd szövegmezője: Enter elfogad, Escape mégse (#5207).

A párbeszédet a Fájl ▸ Átnevezés… tétel VALÓDI kattintása nyitja. A mezőbe
karakterenként gépelünk a billentyűzet eseményeivel (`QTest.keyClick`), majd
Enter-t vagy Escape-et nyomunk. A kiterjesztés kérdéséhez nem nyúlunk.

A főmenü wrapperét a teszt függvényében tartjuk (ld. a 5206-os tesztet).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional.test_fajl_szerkesztes_menu_valodi_5150 import (  # noqa: F401
    _MAPPA,
    _elokeszit,
    _gyerek,
    _latszik,
    _mappa_ut,
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


def _aktival(qt_app, ablak) -> None:
    """Az ablak aktiválása a billentyűzet-események előtt."""
    ablak.requestActivate()
    assert _varj(qt_app, lambda: ablak.property("active") is True), (
        "az ablak nem aktiválódott"
    )


def _gepel(window, qt_app, szoveg: str) -> None:
    """Karakterenként, a billentyűzet eseményeivel gépel a fókuszos mezőbe."""
    for betu in szoveg:
        QTest.keyClick(window, betu)
        qt_app.processEvents()


def _atnevezes_megnyitasa(window, menu_bar, qt_app):
    """Fájl ▸ Átnevezés… valódi kattintással; a mező fókuszát ellenőrzi.

    Visszaadja a szövegmezőt, hogy a gépelés eredményét a teszt lássa.
    """
    _megnyit(menu_bar, qt_app, "&File")
    _klikk(qt_app, window, _gyerek(window, "menuFileRename"))
    assert _varj(qt_app, lambda: _latszik(window, "renameDialog")), (
        "a Fájl ▸ Átnevezés… nem nyitotta meg a párbeszédet"
    )
    _aktival(qt_app, window)
    mezo = _gyerek(window, "renameField")
    assert _varj(qt_app, lambda: mezo.property("activeFocus") is True), (
        "az Átnevezés mezője nem kapta meg a fókuszt"
    )
    return mezo


class TestAtnevezesBillentyu:
    def test_enter_elfogadja_az_uj_nevet(self, fajl_app, qt_app):  # noqa: F811
        window, controller, _engine = fajl_app
        menu_bar = window.property("menuBar")
        _elokeszit(window, qt_app, controller)
        mappa = _mappa_ut(controller, _MAPPA)
        regi = controller.photos.itemAt(0)["name"]
        mezo = _atnevezes_megnyitasa(window, menu_bar, qt_app)

        _gepel(window, qt_app, "uj_nev.jpg")
        assert mezo.property("text") == "uj_nev.jpg", (
            "a gépelés nem jutott el a szövegmezőbe"
        )
        QTest.keyClick(window, Qt.Key.Key_Return)

        assert _varj(qt_app, lambda: (mappa / "uj_nev.jpg").exists()), (
            "az Enter nem fogadta el az új nevet: a fájl nem nevezódött át"
        )
        assert not (mappa / regi).exists(), "a régi néven maradt a fájl"
        assert _varj(qt_app, lambda: not _latszik(window, "renameDialog")), (
            "az Enter után az Átnevezés párbeszéd nyitva maradt"
        )

    def test_escape_megsemmisiti_az_atnevezest(self, fajl_app, qt_app):  # noqa: F811
        window, controller, _engine = fajl_app
        menu_bar = window.property("menuBar")
        _elokeszit(window, qt_app, controller)
        mappa = _mappa_ut(controller, _MAPPA)
        regi = controller.photos.itemAt(0)["name"]
        mezo = _atnevezes_megnyitasa(window, menu_bar, qt_app)

        _gepel(window, qt_app, "masik.jpg")
        assert mezo.property("text") == "masik.jpg", (
            "a gépelés nem jutott el a szövegmezőbe"
        )
        QTest.keyClick(window, Qt.Key.Key_Escape)

        assert _varj(qt_app, lambda: not _latszik(window, "renameDialog")), (
            "az Escape nem zárta be az Átnevezés párbeszédet"
        )
        assert (mappa / regi).exists(), "az Escape után a fájl elveszett"
        assert not (mappa / "masik.jpg").exists(), (
            "az Escape mégis átnevezte a fájlt"
        )
