"""A Webalbumok fül feltöltési méretének legördülője valódi kattintással (#5482).

Az éles fül TILTOTT marad (ld. test_parbeszedek_valodi_5150_c.py): a fül
gyökerén `enabled: false`, ezért a legördülő a valóságban nem kattintható.
Ez a teszt a fület CSAK a saját példányán engedélyezi, és a kattintás-láncot
méri: a tétel kiválasztása után a mentett érték egyezik a legördülővel.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF

from conftest import _build_qml_app
from tests.app.qml_functional.test_beallitasok_legkisebb_szelesseg_3572 import (  # noqa: F401
    _kattints_kozepere,
    magyar_beallitasok,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _gyerek,
    _keszits_konyvtarat,
    _klikk_ablakban,
    _valassz_legordulobol,
    _varj,
    _zar,
)
from tests.app.qml_functional.test_parbeszedek_valodi_5150_b import (
    _beallitasok_megnyit,
    _fulre_kattint,
)

#: a sablon sorrendje (CGeneralPrefsPage), angol forrásszöveg
SABLON_TETELEK = [
    "Original size (slowest upload)",
    "Best for web sharing (2048px)",
    "Recommended: 1600 pixels (for prints, screensavers, and sharing)",
    "Medium: 1024 pixels (for sharing)",
    "Small: 800 pixels (for blogs and webpages)",
]


@pytest.fixture
def webalbum_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _webalbum_ful(window, qt_app):
    """Eszközök ▸ Options… valódi kattintással, majd a Webalbumok fül."""
    beallitasok = _beallitasok_megnyit(window, qt_app)
    _fulre_kattint(qt_app, beallitasok, "optionsTabWebAlbums", 6)
    return beallitasok


def _engedelyez_a_teszt_peldanyan(beallitasok) -> None:
    """Csak a teszt példányán: az éles QML-ben a fül tiltott marad."""
    _gyerek(beallitasok, "optionsWebAlbumsTab").setProperty("enabled", True)


def _tetelek(legordulo) -> list[str]:
    modell = legordulo.property("model")
    modell = modell.toVariant() if hasattr(modell, "toVariant") else modell
    return [str(tetel) for tetel in modell]


class TestMeretLegordulo:
    def test_a_sablon_ot_tetelt_adja_a_sorrendjeben(self, webalbum_app, qt_app):
        window, controller, _engine = webalbum_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _webalbum_ful(window, qt_app)

        assert _tetelek(_gyerek(beallitasok, "optionsWebUploadSizeCombo")) == SABLON_TETELEK
        _zar(qt_app, beallitasok)

    def test_kulcs_hianyaban_az_1600_van_kivalasztva(self, webalbum_app, qt_app):
        window, controller, _engine = webalbum_app
        _elokeszit(window, qt_app, controller)
        assert controller.webUploadSizeIndex == 2, "hiányzó kulcsnál nem az 1600 az alapérték"

        beallitasok = _webalbum_ful(window, qt_app)
        legordulo = _gyerek(beallitasok, "optionsWebUploadSizeCombo")
        assert legordulo.property("currentIndex") == 2, "a legördülőn nem az 1600 áll"
        _zar(qt_app, beallitasok)

    @pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
    def test_valodi_kattintassal_valasztott_meret_megmarad(
        self, webalbum_app, qt_app, magassag_eltolas
    ):
        window, controller, _engine = webalbum_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _webalbum_ful(window, qt_app)
        celmagassag = beallitasok.height() + magassag_eltolas
        beallitasok.setHeight(celmagassag)
        assert _varj(qt_app, lambda: beallitasok.height() == celmagassag)
        _engedelyez_a_teszt_peldanyan(beallitasok)
        legordulo = _gyerek(beallitasok, "optionsWebUploadSizeCombo")

        _valassz_legordulobol(qt_app, beallitasok, legordulo, "Best for web sharing (2048px)")

        assert controller.webUploadSizeIndex == 2, (
            "a legördülő módosítása az OK előtt kiírta a feltöltési méretet"
        )
        assert _varj(qt_app, lambda: legordulo.property("currentIndex") == 1), (
            "az új méret nem maradt látható a párbeszédben az OK előtt"
        )
        _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsOkButton"))
        assert _varj(qt_app, lambda: beallitasok.property("visible") is False)
        assert controller.webUploadSizeIndex == 1, "az OK nem mentette a feltöltési méretet"

        beallitasok = _webalbum_ful(window, qt_app)
        _engedelyez_a_teszt_peldanyan(beallitasok)
        legordulo = _gyerek(beallitasok, "optionsWebUploadSizeCombo")
        assert _varj(qt_app, lambda: legordulo.property("currentIndex") == 1), (
            "a párbeszéd újranyitása után nem a mentett méret látszik"
        )
        _zar(qt_app, beallitasok)


class TestSzelesseg:
    def test_a_legkisebb_ablakban_a_legordulo_nem_log_ki(self, webalbum_app, qt_app):
        """A hosszú, magyar tételek csonkolódnak, de a legördülő nem lóghat ki
        a 480 px-es legkisebb Beállítások-ablakból (a 12 px-es margón belül)."""
        window, controller, _engine = webalbum_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _webalbum_ful(window, qt_app)
        beallitasok.setProperty("width", 480)
        for _ in range(5):
            qt_app.processEvents()

        legordulo = _gyerek(beallitasok, "optionsWebUploadSizeCombo")
        jobb_szel = legordulo.mapToScene(QPointF(legordulo.property("width"), 0)).x()
        assert jobb_szel <= 480 - 12 + 1, f"a legördülő jobb széle {jobb_szel} px, 468 px fér el"
        _zar(qt_app, beallitasok)

    # a fixture-név szándékosan az importált név: a pytest ezen köti be
    def test_magyarul_a_legordulo_nem_szelesiti_a_fulet(self, magyar_beallitasok, qt_app):  # noqa: F811
        """A magyar tételek a leghosszabbak: a legördülő a fül szélességén marad,
        és nem kényszeríti szélesebbre (a leghosszabb tétel csonkolódik)."""
        ablak = magyar_beallitasok
        _kattints_kozepere(ablak, qt_app, ablak.findChild(QObject, "optionsTabWebAlbums"))
        for _ in range(5):
            qt_app.processEvents()

        legordulo = ablak.findChild(QObject, "optionsWebUploadSizeCombo")
        fül = ablak.findChild(QObject, "optionsWebAlbumsTab")
        assert legordulo.property("width") <= fül.property("width") + 1, (
            f"a legördülő {legordulo.property('width')} px, a fül {fül.property('width')} px"
        )
        assert legordulo.property("width") > 100, "a legördülő összeesett"


class TestTiltottFul:
    def test_az_eles_webalbum_ful_tiltott_marad(self, webalbum_app, qt_app):
        window, controller, _engine = webalbum_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _webalbum_ful(window, qt_app)

        assert _gyerek(beallitasok, "optionsWebAlbumsTab").property("enabled") is False, (
            "a Webalbumok fül nincs tiltva, pedig a PicasaPy-ban nincs webalbum-feltöltés"
        )
        _zar(qt_app, beallitasok)
