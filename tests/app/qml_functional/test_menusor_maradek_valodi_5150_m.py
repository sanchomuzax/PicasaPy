"""A Menüsor maradék tételei VALÓDI bemenettel (#5150): Kép és Eszközök.

A tételek valódi egérkattintással (`QTest.mouseClick`) indulnak; nincs
`triggered`/`activated` hívás és nincs `.emit()`. A hatást a lemezre írt
`.picasa.ini`-n, a fotó állapotán, a keresőmező szövegén és a megnyíló
párbeszéden mérjük.

Két tételt az EGYÜTTES maradék miatt a `_l` fájl nem fed: az Eszközök ▸
Experimental ▸ Search for... almenüknek nincs objectName-je, ezért a
feliratukra keresünk (`tetel_kattintasa_cimlanc`).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    MAPPA,
    app_epitese,
    elokeszit,
    keszits_konyvtarat,
    kijelol,
    mappa_ut,
    szures,
)
from tests.app.qml_functional._menusor_maradek_5150_helpers import (
    keresomezo_szovege,
    latszik,
    tetel_kattintasa,
    tetel_kattintasa_cimlanc,
    varj,
)

_KIJELOLT_SOROK = [0, 1]
_KIJELOLETLEN_SOR = 2


def _szoveges_keszito(aktiv: str):
    """Könyvtár-építő: az `a_nagy.jpg`-hez látható vagy rejtett szövegfedvény."""

    def keszit(lib: Path) -> None:
        keszits_konyvtarat(lib)
        (lib / MAPPA / ".picasa.ini").write_text(
            f"[a_nagy.jpg]\ntext=1;2500;8000;Régi felirat;Arial\ntextactive={aktiv}\n",
            encoding="utf-8",
        )

    return keszit


def _aktiv_ertek(ini: Path) -> str:
    """A `.picasa.ini` `textactive=` értéke; hiányzó fájlnál üres."""
    if not ini.exists():
        return ""
    for sor in ini.read_text(encoding="utf-8").splitlines():
        if sor.startswith("textactive="):
            return sor.split("=", 1)[1].strip()
    return ""


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


@pytest.fixture
def szoveges_app(qt_app, tmp_path, request):
    yield from app_epitese(
        qt_app, tmp_path, kepeket_keszit=_szoveges_keszito(request.param)
    )


class TestKepAtnevezes:
    def test_az_atnevezes_valodi_kattintassal_megnyitja_a_parbeszedet(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)

        tetel_kattintasa(
            window,
            qt_app,
            "&Picture",
            "menuBatchRename",
            almenu_utvonal=("menuPictureBatchEdit",),
        )

        assert varj(qt_app, lambda: latszik(window, "renameManyDialog")), (
            "a Kép ▸ Csoportos szerkesztés ▸ Átnevezés kattintás nem nyitotta meg a párbeszédet"
        )


class TestKepKotegeltForgatas:
    @pytest.mark.parametrize(
        ("nev", "lepes"),
        [
            ("menuBatchRotateRight", 1),
            ("menuBatchRotateLeft", 3),
        ],
    )
    def test_a_forgatas_valodi_kattintassal_a_kijelolt_kepeket_forgatja(
        self, kep_app, qt_app, nev, lepes
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, _KIJELOLT_SOROK)
        assert controller.photos.photos[0].rotate_steps == 0, (
            "a kiinduló forgatás nem nulla: a teszt nem bizonyít"
        )

        tetel_kattintasa(
            window, qt_app, "&Picture", nev, almenu_utvonal=("menuPictureBatchEdit",)
        )

        assert varj(
            qt_app, lambda: controller.photos.photos[0].rotate_steps == lepes
        ), f"a {nev} kattintás nem forgatta a kijelölt képet {lepes} lépéssel"
        assert controller.photos.photos[_KIJELOLETLEN_SOR].rotate_steps == 0, (
            "a kijelöletlen kép is elfordult"
        )


class TestKepKotegeltEffektek:
    @pytest.mark.parametrize(
        ("nev", "kulcs"),
        [
            ("menuBatchAutoContrast", "autolight=1;"),
            ("menuBatchAutoColor", "autocolor=1;"),
            ("menuBatchEnhance", "enhance=1;"),
            ("menuBatchSepia", "sepia=1;"),
            ("menuBatchSharpen", "unsharp=1;"),
            ("menuBatchWarmify", "warm=1;"),
            ("menuBatchFilmGrain", "grain2=1;"),
            ("menuBatchBlackWhite", "bw=1;"),
            ("menuBatchAutoRedeye", "redeye="),
        ],
    )
    def test_az_effekt_valodi_kattintassal_a_kijelolt_kepekre_kerul(
        self, kep_app, qt_app, nev, kulcs
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, _KIJELOLT_SOROK)
        assert all(kulcs not in szures(controller, sor) for sor in _KIJELOLT_SOROK), (
            f"a {kulcs} már a kiinduló láncban van: a teszt nem bizonyít"
        )

        tetel_kattintasa(
            window, qt_app, "&Picture", nev, almenu_utvonal=("menuPictureBatchEdit",)
        )

        assert varj(
            qt_app,
            lambda: all(kulcs in szures(controller, sor) for sor in _KIJELOLT_SOROK),
        ), (
            f"a {nev} kattintás nem írta a {kulcs} szűrőt a kijelölt képekre: "
            f"{[szures(controller, sor) for sor in _KIJELOLT_SOROK]}"
        )
        assert kulcs not in szures(controller, _KIJELOLETLEN_SOR), (
            "a kijelöletlen kép is kapta az effektet"
        )


class TestKepSzovegfedveny:
    @pytest.mark.parametrize("szoveges_app", ["1"], indirect=True)
    def test_a_szoveg_elrejtese_valodi_kattintassal_kikapcsolja_a_feliratot(
        self, szoveges_app, qt_app
    ):
        window, controller, _engine = szoveges_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        ini = mappa_ut(controller) / ".picasa.ini"
        assert _aktiv_ertek(ini) == "1", "a felirat nem látszik kiinduláskor: nem bizonyít"

        tetel_kattintasa(
            window,
            qt_app,
            "&Picture",
            "menuPictureHideText",
            almenu_utvonal=("menuPictureBatchEdit",),
        )

        assert varj(qt_app, lambda: _aktiv_ertek(ini) == "0"), (
            "a Szöveg elrejtése kattintás nem írta a textactive=0 értéket"
        )

    @pytest.mark.parametrize("szoveges_app", ["0"], indirect=True)
    def test_a_szoveg_megjelenitese_valodi_kattintassal_bekapcsolja_a_feliratot(
        self, szoveges_app, qt_app
    ):
        window, controller, _engine = szoveges_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        ini = mappa_ut(controller) / ".picasa.ini"
        assert _aktiv_ertek(ini) == "0", "a felirat már látszik kiinduláskor: nem bizonyít"

        tetel_kattintasa(
            window,
            qt_app,
            "&Picture",
            "menuPictureShowText",
            almenu_utvonal=("menuPictureBatchEdit",),
        )

        assert varj(qt_app, lambda: _aktiv_ertek(ini) == "1"), (
            "a Szöveg megjelenítése kattintás nem írta a textactive=1 értéket"
        )


class TestEszkozokSzinkereses:
    @pytest.mark.parametrize(
        ("nev", "szin"),
        [
            ("menuToolsSearchRed", "red"),
            ("menuToolsSearchOrange", "orange"),
            ("menuToolsSearchYellow", "yellow"),
            ("menuToolsSearchGreen", "green"),
            ("menuToolsSearchBlue", "blue"),
            ("menuToolsSearchPurple", "purple"),
            ("menuToolsSearchBlack", "black"),
        ],
    )
    def test_a_szinkereses_valodi_kattintassal_beallitja_a_keresot(
        self, kep_app, qt_app, nev, szin
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        assert keresomezo_szovege(window) == "", "a keresőmező nem üres: nem bizonyít"

        tetel_kattintasa_cimlanc(
            window, qt_app, "&Tools", ("Experimental", "Search for..."), nev
        )

        assert varj(qt_app, lambda: keresomezo_szovege(window) == f"color:{szin}"), (
            f"a {nev} kattintás nem állította a keresőt: color:{szin}"
        )


class TestEszkozokXmp:
    def test_az_xmp_arcok_irasa_valodi_kattintassal_megnyitja_a_parbeszedet(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)

        tetel_kattintasa_cimlanc(
            window, qt_app, "&Tools", ("Experimental",), "menuToolsWriteXmpFaces"
        )

        assert varj(qt_app, lambda: latszik(window, "xmpFacesWriteDialog")), (
            "az Arcok írása XMP-be kattintás nem nyitotta meg a párbeszédet"
        )
