"""A Hálózat fül naplózási vezérlői VALÓDI egérkattintással (#5145).

Az eredeti options.fen „Network” fülén a naplózási szint legördülő működik, a
naplófájl mező pedig csak megjelenítés (`<pathbox>`, nincs Tallózás). Itt ugyanezt
mérjük:
- `optionsNetworkLogLevelCombo`: valódi kattintás a legördülőn, majd a
  „Detailed log information” tételen; a szint a beállításban marad;
- a naplófájl mező csak olvasható, és az aktív napló útvonalát mutatja
  (`network.log`, az adatmappában); a fülön nincs Tallózás gomb.

A proxy-mezők és az automatikus felismerés továbbra is tiltottak maradnak.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

from conftest import _build_qml_app
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _gyerek,
    _keszits_konyvtarat,
    _latszik,
    _valassz_legordulobol,
    _varj,
    _zar,
)
from tests.app.qml_functional.test_parbeszedek_valodi_5150_b import (
    _beallitasok_megnyit,
    _fulre_kattint,
)


@pytest.fixture
def halozat_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _halozati_ful(window, qt_app):
    """Eszközök ▸ Options… valódi kattintással, majd a Hálózat fül."""
    beallitasok = _beallitasok_megnyit(window, qt_app)
    _fulre_kattint(qt_app, beallitasok, "optionsTabNetwork", 5)
    return beallitasok


class TestNaplozasiSzint:
    def test_szint_valodi_kattintassal_valaszthato_es_megmarad(self, halozat_app, qt_app):
        window, controller, _engine = halozat_app
        _elokeszit(window, qt_app, controller)
        assert controller.networkLogLevel == 2, "az alapérték nem a 2-es szint"
        beallitasok = _halozati_ful(window, qt_app)
        legordulo = _gyerek(beallitasok, "optionsNetworkLogLevelCombo")

        _valassz_legordulobol(qt_app, beallitasok, legordulo, "Detailed log information")

        assert _varj(qt_app, lambda: controller.networkLogLevel == 3), (
            "a legördülő tétele nem mentette a naplózási szintet"
        )
        _zar(qt_app, beallitasok)

        beallitasok = _halozati_ful(window, qt_app)
        legordulo = _gyerek(beallitasok, "optionsNetworkLogLevelCombo")
        assert _varj(qt_app, lambda: legordulo.property("currentIndex") == 3), (
            "a párbeszéd újranyitása után nem a mentett szint látszik"
        )
        _zar(qt_app, beallitasok)


class TestNaplofajl:
    def test_alapertelmezett_naplofajl_az_adatkonyvtarban_van(self, halozat_app, tmp_path):
        _window, controller, _engine = halozat_app

        assert controller.networkLogFile == str(tmp_path / "network.log"), (
            "az alapértelmezett naplófájl nem az adatkönyvtárban van"
        )

    def test_a_fulon_nincs_tallozas_gomb_es_fajlvalaszto(self, halozat_app, qt_app):
        window, controller, _engine = halozat_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _halozati_ful(window, qt_app)

        nevek = {elem.objectName() for elem in beallitasok.findChildren(QObject)}
        assert "optionsNetworkLogBrowseButton" not in nevek, (
            "a Hálózat fülön van Tallózás gomb, pedig az eredetiben nincs"
        )
        assert "optionsNetworkLogFileDialog" not in nevek, (
            "a Hálózat fülön van naplófájl-választó, pedig az eredetiben nincs"
        )
        _zar(qt_app, beallitasok)

    def test_a_naplofajl_mezo_csak_olvashato_es_a_network_log_utvonalat_mutatja(
        self, halozat_app, qt_app, tmp_path
    ):
        window, controller, _engine = halozat_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _halozati_ful(window, qt_app)
        mezo = _gyerek(beallitasok, "optionsNetworkLogPathField")

        assert mezo.property("readOnly") is True, "a naplófájl mező szerkeszthető"
        assert mezo.property("text") == str(tmp_path / "network.log"), (
            "a naplófájl mező nem a network.log útvonalát mutatja"
        )
        _zar(qt_app, beallitasok)


class TestTiltottMezok:
    @pytest.mark.parametrize(
        "nev",
        [
            "optionsNetworkProxyUserField",
            "optionsNetworkProxyPasswordField",
            "optionsNetworkAutoDetectCheck",
        ],
    )
    def test_a_proxy_es_az_automatikus_felismeres_tiltott_marad(
        self, halozat_app, qt_app, nev
    ):
        window, controller, _engine = halozat_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _halozati_ful(window, qt_app)

        assert _latszik(beallitasok, "optionsNetworkLogLevelCombo")
        assert _gyerek(beallitasok, nev).property("enabled") is False, (
            f"{nev}: a proxy-vezérlő nem tiltott, pedig a PicasaPy nem használ proxyt"
        )
        _zar(qt_app, beallitasok)
