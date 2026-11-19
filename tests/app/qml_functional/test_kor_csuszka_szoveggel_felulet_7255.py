"""#7255: a kor-csúszka a keresőszöveg mellett is működik, a felirat a sáv jobb szélén áll.

Mérve az eredeti Picasán (`picasa-colab-jobs` #744, #748): szöveg mellett a
csúszka mozgatása a szöveget a mezőben MEGHAGYJA, a csúszka a szöveg
módosításakor és törlésekor MARAD, a zöld sáv JOBB szélén
`Date Range:  Pictures up to N <egység> old.` jelenik meg, a 0 állásban nincs
felirat.

A próbák valódi felületi úton mennek: a keresőmezőbe valódi billentyűleütés,
a csúszkára a `moved` jelzés (ugyanaz, amit az egér elengedése vált ki). A
vezérlő-szintű széljárások a `tests/app/test_kor_szuro_szoveggel_vezerlo_7255.py`-ban
vannak.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre

KULCS = "zqsearch"
CSUSZKA_HAT_EV = 0.14
CSUSZKA_KET_HONAP = 0.53

#: név -> (felirat, kor napban); a nevek nem tartalmazzák a kulcsot
_KEPEK: dict[str, tuple[str, int]] = {
    "friss.jpg": (KULCS, 1),
    "kozepso.jpg": (KULCS, 400),
    "regi.jpg": (KULCS, 2800),
    "friss_szoveg_nelkul.jpg": ("", 1),
    "regi_szoveg_nelkul.jpg": ("", 2800),
}
_SZOVEGES = {"friss.jpg", "kozepso.jpg", "regi.jpg"}
_SZOVEG_ES_KOR = {"friss.jpg", "kozepso.jpg"}


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _elem(window, nev: str) -> QObject:
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _exif_datum(nap_ota: int) -> str:
    return (datetime.now() - timedelta(days=nap_ota)).strftime("%Y:%m:%d %H:%M:%S")


def _beallit_konyvtar(controller, tmp_path, qt_app) -> None:
    """A próbakönyvtár: ismert korú képek, a felirat az ini-ben."""
    mappa = Path(controller.currentFolder)
    sorok: list[str] = []
    for nev, (felirat, kor) in _KEPEK.items():
        make_jpeg(mappa / nev, size=(80, 60), taken_at=_exif_datum(kor))
        if felirat:
            sorok += [f"[{nev}]", f"caption={felirat}"]
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


def _csuszka_mozgat(window, qt_app, ertek: float) -> None:
    """A csúszka értékét állítjuk és a `moved` jelzést váltjuk ki, ahogy az
    egér elengedése tenné (a #1187 tanulsága: nem a vezérlőt hívjuk)."""
    csuszka = _elem(window, "dateRangeFilterSlider")
    csuszka.setProperty("value", ertek)
    assert QMetaObject.invokeMethod(
        csuszka, "moved", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _csuszka_erteke(window) -> float:
    return float(_elem(window, "dateRangeFilterSlider").property("value"))


@pytest.fixture
def app(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    _beallit_konyvtar(controller, tmp_path, qt_app)
    return window, controller, qt_app


class TestASzovegAMezobenMarad:
    def test_a_csuszka_mozgatasa_a_beirt_szoveget_meghagyja(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        assert _nevek(controller) == _SZOVEGES

        _csuszka_mozgat(window, qt_app, CSUSZKA_HAT_EV)

        assert str(_elem(window, "searchField").property("text")) == KULCS
        assert controller.searchActive is True
        assert controller.searchQuery == KULCS
        assert _nevek(controller) == _SZOVEG_ES_KOR, (
            "a találat nem a szöveg és a kor metszete"
        )

    def test_a_csuszka_mozgatasa_szukit_a_kisebb_korra(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)

        _csuszka_mozgat(window, qt_app, CSUSZKA_KET_HONAP)

        assert _nevek(controller) == {"friss.jpg"}

    def test_a_bal_szelso_allas_a_szoveges_talalatot_adja_vissza(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _csuszka_mozgat(window, qt_app, CSUSZKA_HAT_EV)

        _csuszka_mozgat(window, qt_app, 0.0)

        assert controller.searchQuery == KULCS
        assert _nevek(controller) == _SZOVEGES


class TestACsuszkaNemAllVissza:
    def test_a_csuszka_marad_ha_keresesre_valt_a_nezet(self, app):
        window, controller, qt_app = app
        _csuszka_mozgat(window, qt_app, CSUSZKA_HAT_EV)
        assert controller.viewModeName == "age"

        _gepel(window, controller, qt_app, KULCS)

        assert controller.viewModeName == "search"
        assert _csuszka_erteke(window) == pytest.approx(CSUSZKA_HAT_EV), (
            "a keresésre váltás 0-ra állította a csúszkát"
        )
        assert _nevek(controller) == _SZOVEG_ES_KOR

    def test_a_csuszka_marad_a_szoveg_modositasakor(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _csuszka_mozgat(window, qt_app, CSUSZKA_HAT_EV)
        mezo = _elem(window, "searchField")
        mezo.forceActiveFocus()
        qt_app.processEvents()

        QTest.keyClick(window, "x")

        assert _varj(qt_app, lambda: controller.searchQuery == KULCS + "x")
        assert _csuszka_erteke(window) == pytest.approx(CSUSZKA_HAT_EV)
        assert controller.ageFilterBarText != ""

    def test_a_csuszka_marad_a_szoveg_torlesekor_es_onmagaban_szur(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _csuszka_mozgat(window, qt_app, CSUSZKA_HAT_EV)

        _torol_gepelve(window, controller, qt_app)

        assert _csuszka_erteke(window) == pytest.approx(CSUSZKA_HAT_EV), (
            "a szöveg törlése visszaállította a csúszkát"
        )
        assert controller.searchActive is False
        assert controller.viewModeName == "age"
        assert _nevek(controller) == {
            "friss.jpg",
            "kozepso.jpg",
            "friss_szoveg_nelkul.jpg",
        }

    def test_a_kereso_x_gombja_a_csuszkat_is_alaphelyzetbe_allitja(self, app):
        """Az eredeti `searchclr` mindent töröl: szöveget és szűrőket."""
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _csuszka_mozgat(window, qt_app, CSUSZKA_HAT_EV)
        x_gomb = _elem(window, "searchClear")
        kozep = x_gomb.mapToScene(QPointF(x_gomb.width() / 2, x_gomb.height() / 2))

        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            kozep.toPoint(),
        )
        qt_app.processEvents()

        assert controller.searchActive is False
        assert controller.ageFilterBarText == ""
        assert _csuszka_erteke(window) == 0.0


class TestAFeliratASavJobbSzelen:
    def _sav(self, window):
        return _elem(window, "filterResultsBar")

    def _felirat(self, window):
        return _elem(window, "ageFilterBarLabel")

    def _jobb_el(self, item) -> float:
        return item.mapToScene(QPointF(item.width(), 0.0)).x()

    def test_a_felirat_a_sav_jobb_szelere_igazodik(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)

        _csuszka_mozgat(window, qt_app, CSUSZKA_KET_HONAP)

        felirat = self._felirat(window)
        assert felirat.property("visible") is True
        assert (
            self._jobb_el(self._sav(window)) - self._jobb_el(felirat) <= 16.0
        ), "a felirat nem a sáv jobb szélén áll"
        assert felirat.mapToScene(QPointF(0.0, 0.0)).x() > (
            self._sav(window).mapToScene(QPointF(0.0, 0.0)).x()
            + self._sav(window).width() / 2
        ), "a felirat a sáv bal felén kezdődik"

    def test_a_felirat_szovege_ket_honap_es_ket_nap(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)

        _csuszka_mozgat(window, qt_app, CSUSZKA_KET_HONAP)
        assert (
            str(self._felirat(window).property("text"))
            == "Date Range:  Pictures up to 2 months old."
        )

        _csuszka_mozgat(window, qt_app, 1.0)
        assert (
            str(self._felirat(window).property("text"))
            == "Date Range:  Pictures up to 2 days old."
        )

    def test_a_bal_szelso_allasban_nincs_felirat(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _csuszka_mozgat(window, qt_app, CSUSZKA_KET_HONAP)

        _csuszka_mozgat(window, qt_app, 0.0)

        assert self._felirat(window).property("visible") is False

    def test_a_felirat_a_szoveg_torlese_utan_is_latszik(self, app):
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)
        _csuszka_mozgat(window, qt_app, CSUSZKA_KET_HONAP)

        _torol_gepelve(window, controller, qt_app)

        felirat = self._felirat(window)
        assert felirat.property("visible") is True
        assert (
            str(felirat.property("text"))
            == "Date Range:  Pictures up to 2 months old."
        )

    def test_a_talalati_szoveg_nem_hordozza_a_kor_mondatot(self, app):
        """A bal oldali találati szöveg a mért szöveges találatot mutatja."""
        window, controller, qt_app = app
        _gepel(window, controller, qt_app, KULCS)

        _csuszka_mozgat(window, qt_app, CSUSZKA_KET_HONAP)

        bal_szoveg = str(_elem(window, "filterStatusLabel").property("text"))
        assert bal_szoveg == controller.filterStatusText
        assert "Pictures up to" not in bal_szoveg
        assert "Date Range" not in bal_szoveg
