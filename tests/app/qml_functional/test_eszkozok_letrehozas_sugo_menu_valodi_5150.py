"""A Létrehozás és a Súgó menü tételei VALÓDI egérkattintással (#5150, 4. rész).

Minden tétel a főmenü fejlécére, majd magára a tételre kattintva indul
(`_megnyit`, `menupont_kattintasa`), tehát a menüsor kezelését is a valódi
bemenet viszi. Parancsot közvetlenül nem indítunk: nincs `triggered`/
`clicked`/`activated` hívás és nincs `.emit()`. A hatást a felületen, a
vezérlő állapotán és a lemezen maradt fájlokon mérjük.

Lefedve ebben a fájlban:
- `menuCreateWallpaper` - Létrehozás ▸ Set as Desktop...: a BMP-másolat az
  elszigetelt tárba kerül; a háttérbeállító program helyett hamis fogantyú fut;
- `menuCreateCollage` - Létrehozás ▸ Picture Collage...: a kollázs-lap nyílik;
- `menuHelpContents` - Súgó ▸ Help Contents and Index: a súgó megnyílik;
- `menuHelpSendLog` - Súgó ▸ Send Log...: tesztüzemben a vezérlőhöz jut.

Már lefedett tételek (ezeket itt nem ismételjük):
- `menuCreateMovie`: test_menusor_billentyu_valodi_5127.py:169
- `menuCreateMovieFromFaces`: test_arcfilm_fejlec_4212.py:201
- `menuCreateMovieFromPeopleAlbums`: test_emberek_album_film_menu_4633.py:115
- `menuHelpKeyboardShortcuts`: test_menusor_billentyu_valodi_5127.py:204
- `menuHelpPerfMonitor`: test_sajat_menu_jeloles_4638.py:146

A menü-segédek a `_eszkozok_menu_5150_helpers.py`-ban élnek.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import _build_qml_app
from picasapy.app import tesztuzem_controller, wallpaper
from tests.app.qml_functional._eszkozok_menu_5150_helpers import (
    elokeszit,
    gyerek,
    keszits_konyvtarat,
    latszik,
    menupont_kattintasa,
    varj,
    zar,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit


@pytest.fixture
def eszkoz_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=keszits_konyvtarat,
    )


class TestLetrehozas:
    def test_hatterkep_valodi_kattintassal_masolatot_ir_es_beallitja(
        self, eszkoz_app, qt_app, tmp_path, monkeypatch
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        beallitott: list[Path] = []

        def hamis_beallitas(bmp):
            # a háttérbeállító program (gsettings, feh, …) helyett csak feljegyzünk
            beallitott.append(Path(bmp))
            return "feh"

        monkeypatch.setattr(wallpaper, "set_desktop_background", hamis_beallitas)
        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&Create")

        menupont_kattintasa(window, qt_app, "menuCreateWallpaper")

        assert varj(qt_app, lambda: len(beallitott) == 1), (
            "a Létrehozás ▸ Set as Desktop kattintás nem állította be a hátteret"
        )
        assert beallitott[0].read_bytes()[:2] == b"BM", (
            "a háttérkép nem BMP-másolat"
        )
        assert tmp_path in beallitott[0].parents, (
            "a BMP-másolat a teszt elszigetelt tárán kívül került"
        )

    def test_kollazs_valodi_kattintassal_megnyitja_a_kollazs_lapot(
        self, eszkoz_app, qt_app
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        assert not bool(controller.collageOpen)
        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&Create")

        menupont_kattintasa(window, qt_app, "menuCreateCollage")

        assert varj(qt_app, lambda: bool(controller.collageOpen)), (
            "a Létrehozás ▸ Picture Collage kattintás nem nyitotta meg a kollázst"
        )


class TestSugo:
    def test_sugo_valodi_kattintassal_megnyilik(self, eszkoz_app, qt_app):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&Help")

        menupont_kattintasa(window, qt_app, "menuHelpContents")

        assert varj(qt_app, lambda: latszik(window, "helpDialog")), (
            "a Súgó ▸ Help Contents and Index kattintás nem nyitotta meg a súgót"
        )
        zar(qt_app, gyerek(window, "helpDialog"))

    def test_naplo_atadasa_valodi_kattintassal_a_vezerloig_jut(
        self, eszkoz_app, qt_app, tmp_path, monkeypatch
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        # üres naplómappa: a vezérlő hangosan megmondja, hogy nincs napló
        monkeypatch.setattr(
            tesztuzem_controller, "_naplo_mappa", lambda: tmp_path / "ures"
        )
        uzenetek: list[str] = []
        controller.tesztuzemUzenet.connect(uzenetek.append)
        controller.setTesztuzemEnabled(True)
        uzenetek.clear()
        qt_app.processEvents()
        try:
            menu_bar = window.property("menuBar")
            _megnyit(menu_bar, qt_app, "&Help")

            menupont_kattintasa(window, qt_app, "menuHelpSendLog")

            assert varj(qt_app, lambda: bool(uzenetek)), (
                "a Súgó ▸ Send Log kattintás nem jutott el a tesztüzem-vezérlőig"
            )
            assert "napló" in uzenetek[0].casefold()
        finally:
            controller.setTesztuzemEnabled(False)
            qt_app.processEvents()
