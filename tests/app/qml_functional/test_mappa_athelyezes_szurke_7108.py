"""A hét ismert mappa mozgatása szürke mindhárom menüben (#7108).

Az eredeti Picasa a Mappa menü (`0x0056e1c0`), a mappafa helyi menüje
(`0x0056c5a0`, `0xa6`) és a HierFolder menü (Move, `0x9df5`) mozgatás tételét
szürkíti, ha a mappa az ismert hét mappa (My Pictures, Desktop, My Music,
My Videos, My Documents, Application Data, Common Application Data) egyike.
Az alattuk álló könyvtárak mozgathatók.

## Mit mér

Valódi jobbklikk a mappasoron, valódi kattintás a menüsáv Mappa menüjén; a
tétel `enabled` állapota ÉS a kirajzolt felirat színe (a szürke tétel
halványabb, mint a mozgatható mappa tétele). A szürke tételre kattintás nem
nyitja meg a mappaválasztót, a mozgatható mappáé igen.

## Amit NEM mér

A szürkített menü vizuális egyezése az eredetivel NEM mérhető: az eredeti
szürke menütételéről nincs felvételünk. A teszt csak azt méri, hogy a
tételünk szürke (halvány) és kattinthatatlan, és hogy a szürke és a
mozgatható állapot a kirajzolt képen különbözik.

A Qt szabványos útvonalait a `known_folders` fogantyúin át váltjuk ki, a hét
ismert mappa a teszt-könyvtár alatti mappákra mutat.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from support.ismert_mappak_7108 import ISMERT_NEVEK, kiegyenesit, profil_utak
from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    _elem_ablaka,
    gyerek,
    jobbklikk_mappan,
    kattints,
    nyitott,
    varj,
    vizualis,
    zar,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit

#: a mozgatható mappák neve a teszt-könyvtárban
_HETKOZNAPI = "hetkoznapi"
_ALATTA = "nyaralas"


def _kep(ut: Path) -> None:
    ut.parent.mkdir(parents=True, exist_ok=True)
    make_jpeg(ut, size=(64, 48))


def _keszit_sajat_kepes(lib: Path) -> None:
    """Minden ismert mappának SAJÁT képe és egy alkönyvtára van."""
    for nev in ISMERT_NEVEK:
        _kep(lib / nev / "sajat.jpg")
        _kep(lib / nev / _ALATTA / "kep.jpg")
    _kep(lib / _HETKOZNAPI / "kep.jpg")


def _keszit_koztes(lib: Path) -> None:
    """Az ismert mappáknak NINCS saját képük: a fában köztes csomópontok
    (a `HierFolder` menü nyílik rajtuk), alattuk egy képes alkönyvtár."""
    for nev in ISMERT_NEVEK:
        _kep(lib / nev / _ALATTA / "kep.jpg")
    # köztes csomópont egy ismert mappa ALATT, és egy hétköznapi köztes
    _kep(lib / "Documents" / "koztes" / "mely" / "kep.jpg")
    _kep(lib / _HETKOZNAPI / "mely" / "kep.jpg")


def _epit(qt_app, tmp_path, request, monkeypatch, keszit):
    def konyvtar(lib: Path) -> None:
        keszit(lib)
        kiegyenesit(monkeypatch, profil_utak(lib))

    gen = _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=konyvtar, keep_modul=request.module
    )
    window, controller, engine = next(gen)
    # a menüsor Python-wrappere a GC után megsemmisítené az ablakot
    # (ld. a `qml-teszt-python-wrapper-torles` tanulságot): a kerete tartja
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    yield window, controller, engine
    del menu_bar
    next(gen, None)


@pytest.fixture
def sajat_kepes_app(qt_app, tmp_path, request, monkeypatch):
    yield from _epit(qt_app, tmp_path, request, monkeypatch, _keszit_sajat_kepes)


@pytest.fixture
def koztes_app(qt_app, tmp_path, request, monkeypatch):
    yield from _epit(qt_app, tmp_path, request, monkeypatch, _keszit_koztes)


def _lib(app) -> Path:
    _window, controller, _engine = app
    return Path(str(controller.watchedFolders[0]))


def _escape(window, qt_app) -> None:
    QTest.keyClick(window, Qt.Key.Key_Escape)
    qt_app.processEvents()


def _legsotetebb(kep, elem, ablak) -> int:
    """Az elem téglalapjának legsötétebb pontja (a felirat színe): 0-255."""
    sarok = elem.mapToScene(QPointF(0, 0))
    x, y = int(sarok.x()), int(sarok.y())
    szel, mag = int(elem.width()), int(elem.height())
    legsotetebb = 255
    for py in range(max(y, 0), min(y + mag, kep.height())):
        for px in range(max(x, 0), min(x + szel, kep.width())):
            szin = QColor(kep.pixel(px, py))
            legsotetebb = min(legsotetebb, szin.lightness())
    return legsotetebb


def _felirat_sotetsege(window, qt_app, elem) -> int:
    """A tétel KIRAJZOLT feliratának sötétsége: a tételt tartalmazó ablak
    képéből (a menü külön ablakban is nyílhat)."""
    ablak = _elem_ablaka(window, elem)
    qt_app.processEvents()
    return _legsotetebb(ablak.grabWindow(), elem, ablak)


def _menubar_tetel(window, qt_app, nev: str):
    """Megnyitja a Mappa menüt (valódi kattintás a fejlécre), visszaadja a tételt."""
    _megnyit(window.property("menuBar"), qt_app, "F&older")
    tetel = _objektum(window, nev)
    assert tetel is not None and tetel.property("visible") is True, (
        f"{nev} nem látszik a megnyitott Mappa menüben"
    )
    return tetel


class TestMappaMenu:
    """A menüsor Mappa ▸ Move... tétele."""

    def test_a_het_ismert_mappan_szurke_es_nem_nyit_valasztot(
        self, sajat_kepes_app, qt_app
    ):
        window, controller, _engine = sajat_kepes_app
        lib = _lib(sajat_kepes_app)
        window.show()
        window.requestActivate()
        qt_app.processEvents()
        pane = _objektum(window, "folderPane")

        for nev in ISMERT_NEVEK:
            controller.selectFolder(str(lib / nev))
            assert varj(
                qt_app, lambda nev=nev: Path(controller.currentFolder) == lib / nev
            ), nev
            tetel = _menubar_tetel(window, qt_app, "menuFolderMove")

            assert tetel.property("enabled") is False, (
                f"a Mappa ▸ Move tétele az ismert {nev} mappán nem szürke (#7108)"
            )
            kattints(window, qt_app, tetel)
            assert pane.property("_movingFolder") in ("", None), (
                f"a szürke Mappa ▸ Move kijelölte az áthelyezendő mappát: {nev}"
            )
            assert not nyitott(_objektum(window, "moveFolderDialog")), (
                f"a szürke Mappa ▸ Move megnyitotta a mappaválasztót: {nev}"
            )
            _escape(window, qt_app)

    @pytest.mark.parametrize("mappa", [_HETKOZNAPI, f"Pictures/{_ALATTA}"])
    def test_a_hetkoznapi_es_az_alattuk_allo_mappan_enged_es_nyit_valasztot(
        self, sajat_kepes_app, qt_app, mappa
    ):
        window, controller, _engine = sajat_kepes_app
        lib = _lib(sajat_kepes_app)
        window.show()
        window.requestActivate()
        qt_app.processEvents()
        controller.selectFolder(str(lib / mappa))
        assert varj(qt_app, lambda: Path(controller.currentFolder) == lib / mappa)

        tetel = _menubar_tetel(window, qt_app, "menuFolderMove")

        assert tetel.property("enabled") is True, (
            f"a Mappa ▸ Move le van tiltva a mozgatható {mappa} mappán"
        )
        kattints(window, qt_app, tetel)
        valaszto = _objektum(window, "moveFolderDialog")
        assert varj(qt_app, lambda: nyitott(valaszto)), (
            f"a mozgatható {mappa} mappán a Move nem nyitott mappaválasztót"
        )
        zar(qt_app, valaszto)

    def test_a_torles_tetele_nem_valtozik(self, sajat_kepes_app, qt_app):
        """A Delete szürkítése a mappatörlés jegyére tartozik: itt NEM nyúlunk."""
        window, controller, _engine = sajat_kepes_app
        lib = _lib(sajat_kepes_app)
        window.show()
        qt_app.processEvents()
        controller.selectFolder(str(lib / "Pictures"))
        assert varj(qt_app, lambda: Path(controller.currentFolder) == lib / "Pictures")

        tetel = _menubar_tetel(window, qt_app, "menuFolderDelete")

        assert tetel.property("enabled") is True
        _escape(window, qt_app)

    def test_a_szurke_felirat_a_kirajzolt_kepen_halvanyabb(
        self, sajat_kepes_app, qt_app
    ):
        """LÁTÁS: a szürke tétel felirata a kirajzolt képen világosabb, mint a
        mozgatható mappa ugyanazon tételéé (a Delete tétel közös mérce)."""
        window, controller, _engine = sajat_kepes_app
        lib = _lib(sajat_kepes_app)
        window.show()
        window.requestActivate()
        qt_app.processEvents()

        controller.selectFolder(str(lib / _HETKOZNAPI))
        assert varj(qt_app, lambda: Path(controller.currentFolder) == lib / _HETKOZNAPI)
        mozgathato = _felirat_sotetsege(
            window, qt_app, _menubar_tetel(window, qt_app, "menuFolderMove")
        )
        _escape(window, qt_app)

        controller.selectFolder(str(lib / "Pictures"))
        assert varj(qt_app, lambda: Path(controller.currentFolder) == lib / "Pictures")
        szurke = _felirat_sotetsege(
            window, qt_app, _menubar_tetel(window, qt_app, "menuFolderMove")
        )
        _escape(window, qt_app)

        assert szurke > mozgathato + 40, (
            "a szürke Move felirata nem látszik halványabbnak a kirajzolt "
            f"képen (szürke={szurke}, mozgatható={mozgathato})"
        )


class TestMappaHelyiMenu:
    """A mappasor jobbklikkjére nyíló teljes mappa-menü Move Folder tétele."""

    def test_a_het_ismert_mappan_szurke_es_nem_nyit_valasztot(
        self, sajat_kepes_app, qt_app
    ):
        window, _controller, _engine = sajat_kepes_app
        lib = _lib(sajat_kepes_app)
        window.show()
        window.requestActivate()
        qt_app.processEvents()

        for nev in ISMERT_NEVEK:
            menu = jobbklikk_mappan(window, qt_app, lib / nev)
            tetel = gyerek(menu, "folderMenuMoveFolder")

            assert tetel.property("enabled") is False, (
                f"a helyi menü Move Folder tétele az ismert {nev} mappán nem szürke (#7108)"
            )
            kattints(window, qt_app, tetel)
            assert not nyitott(_objektum(window, "moveFolderDialog")), (
                f"a szürke Move Folder megnyitotta a mappaválasztót: {nev}"
            )
            _escape(window, qt_app)

    @pytest.mark.parametrize("mappa", [_HETKOZNAPI, f"Desktop/{_ALATTA}"])
    def test_a_hetkoznapi_es_az_alattuk_allo_mappan_enged(
        self, sajat_kepes_app, qt_app, mappa
    ):
        window, _controller, _engine = sajat_kepes_app
        lib = _lib(sajat_kepes_app)
        window.show()
        window.requestActivate()
        qt_app.processEvents()

        menu = jobbklikk_mappan(window, qt_app, lib / mappa)
        tetel = gyerek(menu, "folderMenuMoveFolder")

        assert tetel.property("enabled") is True, (
            f"a helyi menü Move Folder tétele le van tiltva a mozgatható {mappa} mappán"
        )
        kattints(window, qt_app, tetel)
        valaszto = _objektum(window, "moveFolderDialog")
        assert varj(qt_app, lambda: nyitott(valaszto)), (
            f"a mozgatható {mappa} mappán a Move Folder nem nyitott mappaválasztót"
        )
        zar(qt_app, valaszto)

    def test_a_torles_tetele_nem_valtozik(self, sajat_kepes_app, qt_app):
        window, _controller, _engine = sajat_kepes_app
        lib = _lib(sajat_kepes_app)
        window.show()
        window.requestActivate()
        qt_app.processEvents()

        menu = jobbklikk_mappan(window, qt_app, lib / "Music")

        assert gyerek(menu, "folderMenuDeleteFolder").property("enabled") is True
        _escape(window, qt_app)


def _fa_engine(engine):
    fa = engine.rootContext().contextProperty("folderHierarchyController")
    assert fa is not None, "a folderHierarchyController nincs regisztrálva"
    return fa


def _fasor(window, ut: Path):
    """A fanézet sorának egérterülete (az útvonal elválasztóit egységesítve)."""
    cel = str(ut).replace("\\", "/")
    for nev in (f"hierRowMouse:{cel}",):
        try:
            return vizualis(window, nev)
        except AssertionError:
            continue
    raise AssertionError(f"a fanézet sora nem található: {ut}")


def _jobbklikk_fasor(window, qt_app, ut: Path):
    elem = _fasor(window, ut)
    gorgeto = _objektum(window, "folderPaneFlickable")
    tartalom = gorgeto.property("contentItem")
    sor_y = elem.mapToItem(tartalom, QPointF(0, 0)).y()
    content_y = gorgeto.property("contentY")
    viewport_height = gorgeto.height()
    if sor_y < content_y:
        content_y = sor_y
    elif sor_y + elem.height() > content_y + viewport_height:
        content_y = sor_y + elem.height() - viewport_height
    max_y = max(0, gorgeto.property("contentHeight") - viewport_height)
    gorgeto.setProperty("contentY", max(0, min(content_y, max_y)))
    qt_app.processEvents()
    # A fasor itemje a görgetésnél újraköthető; a kattintás pillanatában
    # frissen kérjük le a cél sort.
    elem = _fasor(window, ut)
    kattints(window, qt_app, elem, Qt.MouseButton.RightButton)
    menu = _objektum(window, "hierFolderContextMenu")
    assert varj(qt_app, lambda: menu.property("visible") is True), (
        f"a fanézet sorának jobbklikkje nem nyitotta meg a HierFolder menüt: {ut}"
    )
    return menu


def _fanezetbe(window, qt_app, engine, lib: Path) -> None:
    window.show()
    window.requestActivate()
    fa = _fa_engine(engine)
    fa.setTreeView(True)
    fa.revealPath(str(lib / "Documents" / "koztes"))
    qt_app.processEvents()
    assert varj(qt_app, lambda: _fasor(window, lib / "Documents" / "koztes")), (
        "a fanézet nem rajzolta ki a köztes mappát"
    )


class TestHierFolderMenu:
    """A fa KÖZTES csomópontjának (HierFolder) menüje: Move Folder."""

    def test_a_het_ismert_mappan_szurke_es_nem_nyit_valasztot(
        self, koztes_app, qt_app
    ):
        window, _controller, engine = koztes_app
        lib = _lib(koztes_app)
        _fanezetbe(window, qt_app, engine, lib)

        alapmagassag = window.height()
        for elteres in (-5, 0, 5):
            window.resize(window.width(), alapmagassag + elteres)
            assert varj(
                qt_app,
                lambda elteres=elteres: window.height()
                == alapmagassag + elteres,
            )
            for nev in ISMERT_NEVEK:
                menu = _jobbklikk_fasor(window, qt_app, lib / nev)
                tetel = gyerek(menu, "hierMenuMoveFolder")

                assert tetel.property("enabled") is False, (
                    f"a HierFolder menü Move Folder tétele az ismert {nev} mappán nem szürke (#7108)"
                )
                kattints(window, qt_app, tetel)
                assert not nyitott(_objektum(window, "moveFolderDialog")), (
                    f"a szürke Move Folder megnyitotta a mappaválasztót: {nev}"
                )
                _escape(window, qt_app)

    @pytest.mark.parametrize(
        "mappa", [_HETKOZNAPI, "Documents/koztes"], ids=["hetkoznapi", "ismert-alatt"]
    )
    def test_a_hetkoznapi_es_az_alattuk_allo_kozteson_enged(
        self, koztes_app, qt_app, mappa
    ):
        window, _controller, engine = koztes_app
        lib = _lib(koztes_app)
        _fanezetbe(window, qt_app, engine, lib)

        menu = _jobbklikk_fasor(window, qt_app, lib / mappa)
        tetel = gyerek(menu, "hierMenuMoveFolder")

        assert tetel.property("enabled") is True, (
            f"a HierFolder menü Move Folder tétele le van tiltva a mozgatható {mappa} mappán"
        )
        kattints(window, qt_app, tetel)
        valaszto = _objektum(window, "moveFolderDialog")
        assert varj(qt_app, lambda: nyitott(valaszto)), (
            f"a mozgatható {mappa} mappán a Move Folder nem nyitott mappaválasztót"
        )
        zar(qt_app, valaszto)

    def test_a_tobbi_tetel_nem_valtozik(self, koztes_app, qt_app):
        window, _controller, engine = koztes_app
        lib = _lib(koztes_app)
        _fanezetbe(window, qt_app, engine, lib)

        menu = _jobbklikk_fasor(window, qt_app, lib / "Desktop")

        for nev in (
            "hierMenuExpandAll",
            "hierMenuCollapseAll",
            "hierMenuLocateOnDisk",
            "hierMenuRemoveFromPicasa",
        ):
            assert gyerek(menu, nev).property("enabled") is True, nev
        _escape(window, qt_app)
