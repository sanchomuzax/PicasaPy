"""#7350: a Shortcuts almenü Desktop és My Pictures tétele szürke, ha a
könyvtárban nincs alattuk mappa, mint az eredetiben.

Mindkét menüben: a ▾ gomb legördülőjében (`toolbarFolderListMenu`) és a
menüsor Nézet ▸ Mappanézet almenüjében (`menuViewFolderView`).

A próba két KÜLÖN alkalmazást épít (két könyvtár): az egyikben a könyvtár
mappája a (helyettesített) Képek-gyökér alatt áll, a másikban nem. A Desktop
gyökerében sosincs könyvtári mappa. A menüket valódi `QTest.mouseClick`-kel
nyitja, a szürkeséget a renderelt ablakból olvassa (a felirat legsötétebb
képpontja), a tiltott tétel kattintását is kipróbálja.

Fok (a jegy szerint): a szabály statikus lelet és egy negatív mintán igazolt
(Colab job-804 17. kép); a pozitív eset (mappa a Pictures alatt) és a lista
azonosítása nincs mérve. A próba az eredeti képével való vizuális egyezést NEM
méri, csak azt, hogy a szürkítés látszik és működik.

Rontás-kontroll (futás közben): a két tétel `enabled` kötésének törlése után
a szürkeséget és a tiltást mérő próbák pirosra váltak.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.app import folder_hierarchy_controller as fhc
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import MAPPA, app_epitese
from tests.app.qml_functional._nezet_menu_5150_helpers import almenu_nyit
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    almenu_megnyitasa,
    gyerek,
    kattints,
    varj,
    zar,
)

#: A két menü tételnevei: (Desktop, My Documents, My Pictures, My Computer).
_NEVEK = {
    "nezetbeallito": (
        "toolbarFolderListMenuDesktop",
        "toolbarFolderListMenuMyDocuments",
        "toolbarFolderListMenuMyPictures",
        "toolbarFolderListMenuMyComputer",
    ),
    "menusor": (
        "menuViewShortcutDesktop",
        "menuViewShortcutMyDocuments",
        "menuViewShortcutMyPictures",
        "menuViewShortcutMyComputer",
    ),
}


#: Az almenük objectName-je (a Shortcuts sorokat tartalmazó menü).
_ALMENU = {
    "nezetbeallito": "toolbarFolderListMenuShortcuts",
    "menusor": "menuViewFolderViewShortcuts",
}


@pytest.fixture(params=(True, False), ids=("kepek_alatt_van_mappa", "nincs_mappa"))
def kepek_alatt(request) -> bool:
    return request.param


@pytest.fixture
def konyvtar_app(qt_app, tmp_path, monkeypatch, kepek_alatt):
    """Teljes app; a Képek-gyökér a könyvtár fölé vagy mellé mutat.

    A modulszintű fogantyút cseréljük (#1217): a próba nem függ a futtató gép
    XDG-mappáitól. A csere az app építése ELŐTT történik, mert a vezérlő az
    indulásakor tölti fel a mappalistát."""
    #: a könyvtár helye az app-építőben: `tmp_path / "kepek"` (azt az építő hozza
    #: létre, ezért itt nem mkdir)
    kepek_gyoker = tmp_path / "kepek" if kepek_alatt else tmp_path / "ures_kepek"
    asztal = tmp_path / "ures_asztal"
    iratok = tmp_path / "ures_iratok"
    for mappa in (asztal, iratok, tmp_path / "ures_kepek"):
        mappa.mkdir()
    utak = {"mypics": str(kepek_gyoker), "desktop": str(asztal), "mydocs": str(iratok)}
    monkeypatch.setattr(fhc, "_rendszermappa", lambda token: utak.get(token, ""))
    yield from app_epitese(qt_app, tmp_path)


def _felirat_sotetsege(window, qt_app, almenu, elem, kiemelt_sor: int) -> int:
    """A tétel legsötétebb képpontjának fényessége a renderelt ablakból
    (0 = fekete, 255 = fehér): az engedélyezett felirat sötét, a szürke
    világosabb.

    A mért tétel nem lehet kiemelt (az almenü első sora nyitáskor az, és
    másképp rajzolódik), ezért a kiemelést előbb a `kiemelt_sor` indexű, mindig
    engedélyezett tételre tesszük. Ez csak a mérés előkészítése: a tiltást és a
    kattintást külön, valódi egérrel próbáljuk."""
    almenu.setProperty("currentIndex", kiemelt_sor)
    assert varj(qt_app, lambda: elem.property("highlighted") is False), (
        f"{elem.objectName()} kiemelt maradt, a felirata nem mérhető"
    )
    qt_app.processEvents()
    kep = window.grabWindow()
    assert not kep.isNull(), "az ablak nem rajzolódott ki"
    dpr = kep.devicePixelRatio()
    bal_felso = elem.mapToScene(QPointF(0, 0))
    legsotetebb = 255
    for dx in range(round(elem.width())):
        for dy in range(round(elem.height())):
            x = round((bal_felso.x() + dx + 0.5) * dpr)
            y = round((bal_felso.y() + dy + 0.5) * dpr)
            if not (0 <= x < kep.width() and 0 <= y < kep.height()):
                continue
            szin = kep.pixelColor(x, y)
            fenyesseg = (
                szin.red() * 299 + szin.green() * 587 + szin.blue() * 114
            ) // 1000
            legsotetebb = min(legsotetebb, fenyesseg)
    return legsotetebb


def _nezetbeallito_shortcuts(window, qt_app):
    """Valódi kattintás a ▾ gombra, majd a Shortcuts sorra."""
    kattints(window, qt_app, gyerek(window, "toolbarFolderViewPopupButton"))
    menu = gyerek(window, "toolbarFolderListMenu")
    assert varj(qt_app, lambda: menu.property("opened") is True), (
        "a ▾ gomb nem nyitotta meg a legördülőjét"
    )
    almenu_megnyitasa(window, qt_app, menu, "toolbarFolderListMenuShortcuts")
    return menu


def _menusor_shortcuts(window, qt_app):
    return almenu_nyit(window, qt_app, ("menuViewFolderView", "menuViewFolderViewShortcuts"))


def _megnyit(menu_neve: str, window, qt_app):
    if menu_neve == "nezetbeallito":
        return _nezetbeallito_shortcuts(window, qt_app)
    return _menusor_shortcuts(window, qt_app)


def _bezar(window, qt_app, menu_neve: str) -> None:
    if menu_neve == "nezetbeallito":
        zar(qt_app, gyerek(window, "toolbarFolderListMenu"))
    else:
        for nev in ("menuViewFolderViewShortcuts", "menuViewFolderView", "menuView"):
            zar(qt_app, gyerek(window, nev))


@pytest.mark.parametrize("menu_neve", ("nezetbeallito", "menusor"))
class TestAShortcutsTiltasai:
    def test_az_engedelyezettseg_a_konyvtar_szerint_all(
        self, konyvtar_app, qt_app, kepek_alatt, menu_neve
    ):
        window, _controller, _motor = konyvtar_app
        window.show()
        window.requestActivate()
        _megnyit(menu_neve, window, qt_app)
        desktop, dokumentumok, kepek, gep = (
            gyerek(window, nev) for nev in _NEVEK[menu_neve]
        )

        assert desktop.property("enabled") is False, (
            "az Asztal alatt nincs mappa, a Desktop tételnek szürkének kell lennie"
        )
        assert kepek.property("enabled") is kepek_alatt, (
            "a My Pictures engedélyezettsége nem követi a könyvtárat"
        )
        assert dokumentumok.property("enabled") is True, (
            "a My Documents az eredetiben sosem tiltott"
        )
        assert gep.property("enabled") is True, "a My Computer sosem tiltott"

    def test_a_szurkeseg_a_renderelt_kepen_is_latszik(
        self, konyvtar_app, qt_app, kepek_alatt, menu_neve
    ):
        window, _controller, _motor = konyvtar_app
        window.show()
        window.requestActivate()
        _megnyit(menu_neve, window, qt_app)
        desktop, dokumentumok, kepek, gep = (
            gyerek(window, nev) for nev in _NEVEK[menu_neve]
        )

        almenu = gyerek(window, _ALMENU[menu_neve])
        # sorok: 0 Desktop, 1 My Documents, 2 My Pictures, 3 elválasztó, 4 My Computer
        engedelyezett = _felirat_sotetsege(window, qt_app, almenu, dokumentumok, 4)
        assert _felirat_sotetsege(window, qt_app, almenu, gep, 1) < engedelyezett + 25, (
            "a két mindig engedélyezett tétel felirata eltér egymástól"
        )
        assert _felirat_sotetsege(window, qt_app, almenu, desktop, 4) > engedelyezett + 40, (
            "a Desktop felirata nem szürke a renderelt képen"
        )
        kepek_sotetseg = _felirat_sotetsege(window, qt_app, almenu, kepek, 4)
        if kepek_alatt:
            assert abs(kepek_sotetseg - engedelyezett) < 25, (
                "az engedélyezett My Pictures felirata szürke a renderelt képen"
            )
        else:
            assert kepek_sotetseg > engedelyezett + 40, (
                "a My Pictures felirata nem szürke a renderelt képen"
            )

    def test_a_tiltott_tetel_kattintasa_nem_valtoz_gyokeret(
        self, konyvtar_app, qt_app, kepek_alatt, menu_neve
    ):
        window, _controller, _motor = konyvtar_app
        window.show()
        window.requestActivate()
        fa = gyerek(window, "folderPane").property("hierarchyController")
        _megnyit(menu_neve, window, qt_app)
        desktop, _dokumentumok, kepek, _gep = (
            gyerek(window, nev) for nev in _NEVEK[menu_neve]
        )
        elotte = fa.property("viewRoot")

        # a tiltott tétel valódi kattintása nem történik meg: a Qt nem kézbesíti
        _kattintas_tiltottra(window, qt_app, desktop)
        assert fa.property("viewRoot") == elotte, (
            "a szürke Desktop tétel kattintása gyökeret váltott"
        )

        if kepek_alatt:
            kattints(window, qt_app, kepek)
            assert varj(qt_app, lambda: fa.property("viewRoot") == "mypics"), (
                "az engedélyezett My Pictures kattintása nem váltott gyökeret"
            )
        else:
            _kattintas_tiltottra(window, qt_app, kepek)
            assert fa.property("viewRoot") == elotte, (
                "a szürke My Pictures tétel kattintása gyökeret váltott"
            )
        _bezar(window, qt_app, menu_neve)


def _kattintas_tiltottra(window, qt_app, elem) -> None:
    """Valódi egérkattintás egy tiltott tételen (a `kattints` segéd csak az
    engedélyezetteket várja)."""
    assert elem.isVisible() and elem.width() > 0 and elem.height() > 0
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def test_a_konyvtar_mappaja_tenyleg_a_kepek_gyoker_alatt_all(
    konyvtar_app, qt_app, kepek_alatt
):
    """Őr a próbákhoz: a két könyvtár tényleg az, aminek mondjuk magunkat."""
    window, controller, _motor = konyvtar_app
    fa = gyerek(window, "folderPane").property("hierarchyController")
    mappa = Path(str(controller.watchedFolders[0])) / MAPPA
    kepek_gyoker = Path(fhc._rendszermappa("mypics"))
    assert (kepek_gyoker in mappa.parents) is kepek_alatt
    assert fa.property("picturesAvailable") is kepek_alatt
    assert fa.property("desktopAvailable") is False
