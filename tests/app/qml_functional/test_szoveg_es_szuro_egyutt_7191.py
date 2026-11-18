"""#7191: a keresőszöveg és a csillag, arc, geocímke szűrő EGYÜTT szűkít.

Az eredetiben a szöveg szavai és a gombok belső szójelei (`]star`, `]face`,
`]geo`) egyetlen pozitív szólistában vannak, a találat a lista minden
szavának metszete (`0x0043fda4`, `0x00413290`): a szöveg és a gomb ÉS
kapcsolatban áll. Eddig nálunk a szöveges keresés és a szűrők egymást
kizáró nézetmódok voltak.

Minden próba VALÓDI felületi eseménnyel megy: a szűrőgombra valódi egérkattintás,
a keresőmezőbe valódi billentyűleütés. A vezérlő függvényeit csak a
visszaolvasáshoz (találatlista, darabszám, bal hasáb) hívjuk.

A film, az online, a másodpéldány gomb és a kor-csúszka viselkedése a mai
marad (E1b, az M6 mérése dönt): ezt az utolsó osztály rögzíti.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op
from tests.support.varakozas import var_feltetelre

KULCS = "zqsearch"
_ARC = "faces=rect64(1e00280045006e00),0123456789abcdef;"
_HELY = "geotag=47.497900,19.040200"

#: név -> (felirat, ini-sorok); a nevek szándékosan nem tartalmazzák a kulcsot
_KEPEK: dict[str, tuple[str, tuple[str, ...]]] = {
    "cs_szoveg.jpg": (KULCS, ("star=yes",)),
    "csak_szoveg.jpg": (KULCS, ()),
    "csak_csillag.jpg": ("", ("star=yes",)),
    "arc_szoveg.jpg": (KULCS, (_ARC,)),
    "csak_arc.jpg": ("", (_ARC,)),
    "hely_szoveg.jpg": (KULCS, (_HELY,)),
    "csak_hely.jpg": ("", (_HELY,)),
    "mind_szoveg.jpg": (KULCS, ("star=yes", _ARC, _HELY)),
}


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _elem(window, nev: str) -> QObject:
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattint(window, qt_app, elem) -> None:
    """Valódi egérkattintás az elem ablakhoz leképzett közepére."""
    assert elem.width() > 0 and elem.height() > 0, "a gomb nem látszik"
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _beallit_konyvtar(controller, tmp_path, qt_app) -> None:
    """A próbakönyvtár: a mintaképek ini-adata és a frissített index."""
    mappa = Path(controller.currentFolder)
    sorok: list[str] = ["[Contacts2]", "0123456789abcdef=Teszt Elek;;"]
    for nev, (felirat, extra) in _KEPEK.items():
        make_jpeg(mappa / nev, size=(80, 60))
        sorok.append(f"[{nev}]")
        if felirat:
            sorok.append(f"caption={felirat}")
        sorok.extend(extra)
    (mappa / ".picasa.ini").write_text("\n".join(sorok) + "\n", encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, mappa)
    controller._reload_after_sync()
    qt_app.processEvents()


def _nevek(controller) -> set[str]:
    return {foto.name for foto in controller.photos.photos}


def _gepel(window, controller, qt_app, szoveg: str) -> None:
    """Valódi billentyűleütések a keresőmezőbe, majd várakozás a keresésre."""
    mezo = _elem(window, "searchField")
    mezo.forceActiveFocus()
    qt_app.processEvents()
    for betu in szoveg:
        QTest.keyClick(window, betu)
    assert _varj(qt_app, lambda: controller.searchQuery == szoveg), (
        f"a billentyűleütések nem indították el a(z) {szoveg!r} keresést"
    )


def _torol_gepelve(window, controller, qt_app) -> None:
    """A mező tartalmát BILLENTYŰVEL (Backspace) ürítjük, nem a ✕ gombbal."""
    mezo = _elem(window, "searchField")
    mezo.forceActiveFocus()
    qt_app.processEvents()
    for _ in range(len(str(mezo.property("text")))):
        QTest.keyClick(window, Qt.Key.Key_Backspace)
    assert _varj(qt_app, lambda: str(mezo.property("text")) == "")
    assert _varj(qt_app, lambda: controller.searchQuery == "")


@pytest.fixture
def app(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    _beallit_konyvtar(controller, tmp_path, qt_app)
    return window, controller, qt_app


_GOMBOK = {
    "starred": ("starFilterButton", {"cs_szoveg.jpg", "mind_szoveg.jpg"}),
    "faces": ("faceFilter", {"arc_szoveg.jpg", "mind_szoveg.jpg"}),
    "geo": ("geoFilter", {"hely_szoveg.jpg", "mind_szoveg.jpg"}),
}
_CSAK_GOMB = {
    "starred": {"cs_szoveg.jpg", "csak_csillag.jpg", "mind_szoveg.jpg"},
    "faces": {"arc_szoveg.jpg", "csak_arc.jpg", "mind_szoveg.jpg"},
    "geo": {"hely_szoveg.jpg", "csak_hely.jpg", "mind_szoveg.jpg"},
}
_CSAK_SZOVEG = {
    "cs_szoveg.jpg", "csak_szoveg.jpg", "arc_szoveg.jpg", "hely_szoveg.jpg",
    "mind_szoveg.jpg",
}


@pytest.mark.parametrize("gomb", list(_GOMBOK))
class TestASzovegEsAGombMetszete:
    def test_a_szoveg_utan_bekapcsolt_gomb_szukit(self, app, gomb):
        window, controller, qt_app = app
        nev, elvart = _GOMBOK[gomb]

        _gepel(window, controller, qt_app, KULCS)
        assert _nevek(controller) == _CSAK_SZOVEG

        _kattint(window, qt_app, _elem(window, nev))

        assert controller.searchQuery == KULCS, "a gomb eldobta a keresőszöveget"
        assert controller.searchActive is True
        assert controller.buttonFilterName == gomb
        assert _nevek(controller) == elvart, (
            "a találat nem a szöveg és a gomb metszete"
        )

    def test_a_gomb_utan_begepelt_szoveg_szukit(self, app, gomb):
        window, controller, qt_app = app
        nev, elvart = _GOMBOK[gomb]

        _kattint(window, qt_app, _elem(window, nev))
        assert _nevek(controller) == _CSAK_GOMB[gomb]

        _gepel(window, controller, qt_app, KULCS)

        assert controller.buttonFilterName == gomb, (
            "a keresés kikapcsolta a szűrőgombot"
        )
        assert _nevek(controller) == elvart

    def test_a_gomb_kikapcsolasa_megtartja_a_szoveget(self, app, gomb):
        window, controller, qt_app = app
        nev, _elvart = _GOMBOK[gomb]
        _gepel(window, controller, qt_app, KULCS)
        _kattint(window, qt_app, _elem(window, nev))

        _kattint(window, qt_app, _elem(window, nev))

        assert controller.searchQuery == KULCS
        assert controller.searchActive is True
        assert str(_elem(window, "searchField").property("text")) == KULCS
        assert controller.buttonFilterName == ""
        assert _nevek(controller) == _CSAK_SZOVEG

    def test_a_szoveg_torlese_megtartja_a_gombot(self, app, gomb):
        window, controller, qt_app = app
        nev, _elvart = _GOMBOK[gomb]
        _gepel(window, controller, qt_app, KULCS)
        _kattint(window, qt_app, _elem(window, nev))

        _torol_gepelve(window, controller, qt_app)

        assert controller.searchActive is False
        assert controller.buttonFilterName == gomb, (
            "a szöveg törlése kikapcsolta a szűrőgombot"
        )
        assert controller.viewModeName == gomb
        assert _nevek(controller) == _CSAK_GOMB[gomb]

    def test_a_darabszam_a_bal_hasab_es_a_racs_ugyanaz_a_halmaz(
        self, app, gomb
    ):
        window, controller, qt_app = app
        nev, elvart = _GOMBOK[gomb]
        _gepel(window, controller, qt_app, KULCS)
        _kattint(window, qt_app, _elem(window, nev))

        assert controller.searchResultCount == len(elvart)
        csoportok = controller.searchGroups
        assert sum(len(g["photos"]) for g in csoportok) == len(elvart)
        assert controller.photos.rowCount() == len(elvart)
        assert controller.searchFeedback == "found"
        hasab = controller.folders
        assert hasab.rowCount() == 1, "a találatos mappák listája nem szűkült"
        szam = hasab.data(hasab.index(0, 0), hasab.CountRole)
        assert szam == len(elvart), (
            "a bal hasáb darabszáma nem a közös halmazé"
        )

    def test_ures_metszetnel_nincs_talalat(self, app, gomb):
        window, controller, qt_app = app
        nev, _elvart = _GOMBOK[gomb]
        _kattint(window, qt_app, _elem(window, nev))

        _gepel(window, controller, qt_app, "zqnincsilyen")

        assert _nevek(controller) == set()
        assert controller.searchResultCount == 0
        assert controller.searchFeedback == "notfound"
        assert controller.buttonFilterName == gomb


class TestAMappaValasztasEsAFrissites:
    def test_mappara_szukitve_a_gomb_megmarad(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _kattint(window, qt_app, _elem(window, "starFilterButton"))
        mappa = controller.currentFolder

        controller.selectFolderKeepSearch(mappa)

        assert controller.searchActive is True
        assert controller.buttonFilterName == "starred"
        assert _nevek(controller) == {"cs_szoveg.jpg", "mind_szoveg.jpg"}

    def test_frissites_utan_is_a_metszet_latszik(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _kattint(window, qt_app, _elem(window, "faceFilter"))

        controller._refresh_view()
        qt_app.processEvents()

        assert _nevek(controller) == {"arc_szoveg.jpg", "mind_szoveg.jpg"}
        assert controller.searchResultCount == 2

    def test_a_gombok_egymast_kizarjak_a_szoveg_megmarad(self, app):
        """A három gomb ma is kizárja egymást; a szöveg közben marad."""
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _kattint(window, qt_app, _elem(window, "starFilterButton"))

        _kattint(window, qt_app, _elem(window, "faceFilter"))

        assert controller.buttonFilterName == "faces"
        assert controller.searchQuery == KULCS
        assert _nevek(controller) == {"arc_szoveg.jpg", "mind_szoveg.jpg"}


class TestACsillagLevetele:
    """A keresés mellé kötött ★ gomb tagsága a csillagtól függ (#1443 mintája)."""

    def _csillagot_levesz(self, window, controller, qt_app, nev: str) -> None:
        sor = [foto.name for foto in controller.photos.photos].index(nev)
        QMetaObject.invokeMethod(
            window,
            "handleThumbClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", sor),
            Q_ARG("QVariant", 0),
        )
        qt_app.processEvents()
        gomb = _elem(window, "trayStarButton")
        wait_for_photo_op(
            controller,
            lambda: QMetaObject.invokeMethod(
                gomb, "clicked", Qt.ConnectionType.DirectConnection
            ),
            qt_app=qt_app,
        )

    def test_a_csillag_levetele_kikeruli_a_kepet_a_metszetbol(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _kattint(window, qt_app, _elem(window, "starFilterButton"))
        assert _nevek(controller) == {"cs_szoveg.jpg", "mind_szoveg.jpg"}

        self._csillagot_levesz(window, controller, qt_app, "cs_szoveg.jpg")

        assert _nevek(controller) == {"mind_szoveg.jpg"}, (
            "a csillag levétele után a kép ott maradt a szöveg és a csillag "
            "metszetében"
        )
        assert controller.searchResultCount == 1

    def test_gomb_nelkul_a_kep_marad(self, app):
        """Ellenkező irányú őr: ★ gomb nélkül a tagság nem a csillagtól függ."""
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)

        self._csillagot_levesz(window, controller, qt_app, "cs_szoveg.jpg")

        assert _nevek(controller) == _CSAK_SZOVEG


class TestAXGombMindentTorol:
    def test_a_kereso_x_gombja_a_szoveget_es_a_gombot_is_torli(self, app):
        """Az eredeti `searchclr` a szöveget ÉS a gombokat is törli."""
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _kattint(window, qt_app, _elem(window, "starFilterButton"))

        _kattint(window, qt_app, _elem(window, "searchClear"))

        assert controller.searchActive is False
        assert controller.buttonFilterName == ""
        assert controller.filterActive is False


class TestAMaiViselkedesMarad:
    """A film, a másodpéldány gomb és a kor-csúszka a mai marad (E1b)."""

    def test_a_film_gomb_ma_is_felulirja_a_keresest(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _kattint(window, qt_app, _elem(window, "starFilterButton"))

        _kattint(window, qt_app, _elem(window, "movieFilter"))

        assert controller.viewModeName == "videos"
        assert controller.searchActive is False
        assert controller.buttonFilterName == ""

    def test_a_kor_csuszka_ma_is_felulirja_a_keresest(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)

        controller.setAgeFilter(0.9)

        assert controller.viewModeName == "age"
        assert controller.searchActive is False

    def test_a_gomb_nelkuli_szuro_es_kereses_valtozatlan(self, app):
        window, controller, qt_app = app
        _kattint(window, qt_app, _elem(window, "starFilterButton"))
        assert controller.viewModeName == "starred"
        assert _nevek(controller) == _CSAK_GOMB["starred"]

        _kattint(window, qt_app, _elem(window, "starFilterButton"))

        assert controller.viewModeName == "folder"
        assert controller.filterActive is False
