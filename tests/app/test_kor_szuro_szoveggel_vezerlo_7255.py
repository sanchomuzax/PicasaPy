"""#7255: a kor-csúszka a keresőszöveggel KÖZÖS állapot (vezérlő-szint).

Mérve az eredeti Picasán (`picasa-colab-jobs` #744, #748): szöveg mellett a
csúszka mozgatása a szöveget a mezőben meghagyja, a találat a szöveges
találat és a `kor <= N nap` metszete; a szöveg törlése után a csúszka marad,
és önmagában dátumszűrő a teljes könyvtáron. A felirat
`Date Range:  Pictures up to N <egység> old.`, a 0 állásban nincs.

A próbakönyvtár képei ismert korúak (a mai naphoz mérve), így a próba
nem függ attól, hogy mikor fut:

| kép                  | felirat (`zqsearch`) | kor        |
|----------------------|----------------------|------------|
| friss.jpg            | van                  | 1 nap      |
| kozepso.jpg          | van                  | 400 nap    |
| regi.jpg             | van                  | 2800 nap   |
| friss_szoveg_nelkul  | nincs                | 1 nap      |
| regi_szoveg_nelkul   | nincs                | 2800 nap   |

A csúszka 0,14 állása ~2320 nap (kb. 6 év), a 0,53 ~70 nap (2 hónap).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg

_I18N = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"

KULCS = "zqsearch"
CSUSZKA_HAT_EV = 0.14
CSUSZKA_KET_HONAP = 0.53


def _exif_datum(nap_ota: int) -> str:
    mikor = datetime.now() - timedelta(days=nap_ota)
    return mikor.strftime("%Y:%m:%d %H:%M:%S")


#: név -> (felirat, kor napban)
_KEPEK: dict[str, tuple[str, int]] = {
    "friss.jpg": (KULCS, 1),
    "kozepso.jpg": (KULCS, 400),
    "regi.jpg": (KULCS, 2800),
    "friss_szoveg_nelkul.jpg": ("", 1),
    "regi_szoveg_nelkul.jpg": ("", 2800),
}


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "elso").mkdir(parents=True)
    sorok: list[str] = []
    for nev, (felirat, kor) in _KEPEK.items():
        make_jpeg(root / "elso" / nev, taken_at=_exif_datum(kor))
        if felirat:
            sorok += [f"[{nev}]", f"caption={felirat}"]
    (root / "elso" / ".picasa.ini").write_text(
        "\n".join(sorok) + "\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return AppController(
        tmp_path / "index.db", (str(library),), provider, settings=settings
    )


def _nevek(controller) -> set[str]:
    return {foto.name for foto in controller.photos.photos}


_SZOVEGES = {"friss.jpg", "kozepso.jpg", "regi.jpg"}


class TestASzovegEsAKorMetszete:
    def test_szoveg_utan_a_csuszka_a_szoveg_es_a_kor_metszetet_adja(
        self, controller
    ):
        controller.search(KULCS)
        assert _nevek(controller) == _SZOVEGES

        controller.setAgeFilter(CSUSZKA_HAT_EV)

        assert controller.viewModeName == "search"
        assert controller.searchActive is True
        assert controller.searchQuery == KULCS
        assert _nevek(controller) == {"friss.jpg", "kozepso.jpg"}
        assert controller.searchResultCount == 2

    def test_szukebb_allasban_csak_a_friss_marad(self, controller):
        controller.search(KULCS)

        controller.setAgeFilter(CSUSZKA_KET_HONAP)

        assert _nevek(controller) == {"friss.jpg"}

    def test_a_csuszka_nulla_allasa_a_szoveget_megtartja(self, controller):
        controller.search(KULCS)
        controller.setAgeFilter(CSUSZKA_HAT_EV)

        controller.setAgeFilter(0.0)

        assert controller.viewModeName == "search"
        assert controller.searchQuery == KULCS
        assert controller.ageFilterBarText == ""
        assert _nevek(controller) == _SZOVEGES

    def test_a_csuszka_a_zold_savot_nem_oltja_ki(self, controller):
        controller.search(KULCS)

        controller.setAgeFilter(CSUSZKA_HAT_EV)

        assert controller.filterActive is True


class TestACsuszkaASzovegValtozasakorMarad:
    def test_a_csuszka_utan_begepelt_szoveg_a_metszetet_adja(self, controller):
        controller.setAgeFilter(CSUSZKA_HAT_EV)
        assert controller.viewModeName == "age"

        controller.search(KULCS)

        assert controller.viewModeName == "search"
        assert controller.ageFilterBarText != "", (
            "a keresésre váltás eldobta a kor-szűrőt"
        )
        assert _nevek(controller) == {"friss.jpg", "kozepso.jpg"}

    def test_szoveg_modositasakor_a_kor_marad(self, controller):
        controller.search(KULCS)
        controller.setAgeFilter(CSUSZKA_HAT_EV)
        felirat = controller.ageFilterBarText

        controller.search(KULCS + " ")
        controller.search("kozepso")

        assert controller.ageFilterBarText == felirat
        assert _nevek(controller) == {"kozepso.jpg"}

    def test_a_szoveg_torlese_utan_a_kor_onmagaban_szur_a_teljes_konyvtaron(
        self, controller
    ):
        controller.search(KULCS)
        controller.setAgeFilter(CSUSZKA_HAT_EV)

        controller.search("")

        assert controller.searchActive is False
        assert controller.viewModeName == "age"
        assert controller.ageFilterBarText != ""
        assert _nevek(controller) == {
            "friss.jpg",
            "kozepso.jpg",
            "friss_szoveg_nelkul.jpg",
        }

    def test_a_szoveg_torlese_utan_a_nulla_allas_mindent_mutat(self, controller):
        """Szöveg és szűrő nélkül a mappa-nézet áll vissza, nem üres szűrés."""
        controller.search(KULCS)
        controller.setAgeFilter(CSUSZKA_HAT_EV)
        controller.setAgeFilter(0.0)

        controller.search("")

        assert controller.viewModeName == "folder"
        assert controller.ageFilterBarText == ""


class TestAMapparaSzukitettKereses:
    def test_a_mappara_szukitett_keresesben_a_kor_marad(self, controller, library):
        controller.search(KULCS)
        controller.setAgeFilter(CSUSZKA_HAT_EV)

        controller.selectFolderKeepSearch(str(library / "elso"))

        assert controller.viewModeName == "search-folder"
        assert controller.ageFilterBarText != ""
        assert _nevek(controller) == {"friss.jpg", "kozepso.jpg"}
        assert controller.searchResultCount == 2


class TestAKorFeliratNemMaradElavultan:
    def test_a_clearFilter_a_szoveget_es_a_kort_is_torli(self, controller):
        controller.search(KULCS)
        controller.setAgeFilter(CSUSZKA_HAT_EV)

        controller.clearFilter()

        assert controller.viewModeName == "folder"
        assert controller.ageFilterBarText == ""
        assert controller.ageFilterText == ""

    def test_mappavaltas_torli_a_kort(self, controller, library):
        controller.search(KULCS)
        controller.setAgeFilter(CSUSZKA_HAT_EV)

        controller.selectFolder(str(library / "elso"))

        assert controller.viewModeName == "folder"
        assert controller.ageFilterBarText == ""

    def test_kereses_nelkul_a_csuszka_a_mai_kor_nezet(self, controller):
        """Szöveg nélkül változatlan: külön `age` nézet a teljes könyvtáron."""
        controller.setAgeFilter(CSUSZKA_HAT_EV)

        assert controller.viewModeName == "age"
        assert _nevek(controller) == {
            "friss.jpg",
            "kozepso.jpg",
            "friss_szoveg_nelkul.jpg",
        }
        controller.setAgeFilter(0.0)
        assert controller.viewModeName == "folder"


class TestASavFelirataAHaromMertAllasban:
    """0: nincs felirat; kb. 0,53: `2 months`; 1,0: `2 days`."""

    def test_nulla_allasban_nincs_felirat(self, controller):
        controller.setAgeFilter(0.0)

        assert controller.ageFilterBarText == ""

    def test_kb_0_53_ket_honap(self, controller):
        controller.setAgeFilter(CSUSZKA_KET_HONAP)

        assert (
            controller.ageFilterBarText
            == "Date Range:  Pictures up to 2 months old."
        )

    def test_a_jobb_szelso_allas_ket_nap(self, controller):
        controller.setAgeFilter(1.0)

        assert (
            controller.ageFilterBarText
            == "Date Range:  Pictures up to 2 days old."
        )

    def test_szoveg_mellett_is_ugyanez_a_felirat(self, controller):
        controller.search(KULCS)

        controller.setAgeFilter(CSUSZKA_KET_HONAP)
        assert (
            controller.ageFilterBarText
            == "Date Range:  Pictures up to 2 months old."
        )
        controller.setAgeFilter(1.0)
        assert (
            controller.ageFilterBarText
            == "Date Range:  Pictures up to 2 days old."
        )

    def test_a_felirat_a_kereses_torlese_utan_is_latszik(self, controller):
        controller.search(KULCS)
        controller.setAgeFilter(CSUSZKA_KET_HONAP)

        controller.search("")

        assert (
            controller.ageFilterBarText
            == "Date Range:  Pictures up to 2 months old."
        )

    def test_az_ageFilterText_valtozatlan_a_felirat_nelkuli_mondat(
        self, controller
    ):
        """A meglévő tulajdonság (#3639 szerződés) az előtag nélküli mondat."""
        controller.setAgeFilter(CSUSZKA_KET_HONAP)

        assert controller.ageFilterText == "Pictures up to 2 months old."


class TestASavFeliratMagyarul:
    """Az előtag az eredeti `il_SetSearchStatus::1` erőforrás magyar szövege."""

    @pytest.fixture
    def magyar(self, qt_app):
        from PySide6.QtCore import QCoreApplication, QTranslator

        translator = QTranslator()
        assert translator.load("picasapy_hu", str(_I18N)), "a .qm nem tölthető be"
        QCoreApplication.installTranslator(translator)
        yield translator
        QCoreApplication.removeTranslator(translator)

    def test_a_felirat_datumtartomany_elotaggal_jon(self, controller, magyar):
        controller._age_filter_days = 3

        assert (
            controller.ageFilterBarText
            == "Dátumtartomány:  Legfeljebb 3 napos képek."
        )

    def test_a_felirat_nelkuli_mondat_magyarul_valtozatlan(self, controller, magyar):
        controller._age_filter_days = 3

        assert controller.ageFilterText == "Legfeljebb 3 napos képek."
