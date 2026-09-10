"""Az „Asztali háttérkép" gomb ÉL, és azt adja, amit ígér (#1005).

## Előzmény: a #1895 megfordítva

A #1895 köre **letiltotta** a gombot, mert a súgója háttérkép-beállítást
ígért, a lánc viszont a `collageDesktopBackgroundReady` jelzésnél véget ért:
a felhasználó „kész" értesítést kapott, és az asztala változatlan maradt.
Egy kattintható vezérlő, ami mást ad, mint amit ígér, rosszabb, mint a
hiánya (#936, #1903).

A #1895 őre KIMONDTA, mi oldja fel: *„van háttérkép-beállító kód — a gombot
engedélyezni kell, és ez a teszt elavult"*. A #1005 megépítette
(`app/wallpaper.py` + a kollázs-ág bekötése), ezért ez a fájl mostantól az
ELLENKEZŐJÉT őrzi: a gomb él, a súgó a teljes műveletet ígéri, és a
háttérkép-beállító kód TÉNYLEG megvan.

Ha valaki visszaírja `enabled: false`-ra vagy kiveszi a beállító kódot, itt
bukik el — a gomb és az ígérete nem csúszhat szét újra.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
from tests.support.qml_blokk import blokk_horgonyra

_PANEL = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "CollagePanel.qml"
).read_text(encoding="utf-8")


def _blokk() -> str:
    return blokk_horgonyra(_PANEL, 'objectName: "collageMakeDesktopButton"')


class TestAGombEl:
    def test_a_gomb_NEM_inaktiv(self):
        assert "enabled: false" not in _blokk(), (
            "a háttérkép-beállítás megvan (#1005) — a gomb nem lehet letiltva"
        )

    def test_a_sugo_a_TELJES_muveletet_igeri(self):
        blokk = _blokk()
        assert "set it as the desktop background" in blokk, (
            "a súgónak azt kell ígérnie, amit teszünk: a kép elkészül ÉS a "
            "háttér beáll"
        )
        assert "cannot be set yet" not in blokk, (
            "a #1895 „még nem lehet”-súgója elavult"
        )

    def test_a_HELYE_es_a_felirata_valtozatlan(self):
        """A mért geometria és felirat nem mozdul a bekötéstől."""
        blokk = _blokk()
        assert "x: 10; y: 415; width: 127; height: 28" in blokk
        assert 'text: qsTr("Desktop Background")' in blokk

    def test_a_forras_KIMONDJA_a_jegyet(self):
        """Hogy egy későbbi kör lássa, honnan jön a bekötés."""
        assert "#1005" in _PANEL


class TestVanHatterkepKod:
    """A #1895 alapállítása MEGFORDULT: most a kód LÉTE a követelmény."""

    def test_van_hatterkep_beallito_kod(self):
        from picasapy.app import wallpaper

        assert wallpaper.BACKGROUND_FILE == "picasabackground.bmp", (
            "a mért fájlnév az eredetiből való"
        )
        assert callable(wallpaper.set_desktop_background)
        assert callable(wallpaper.write_background_bmp)

    def test_a_kollazs_ag_HIVJA_a_lancot(self):
        """A #1895 hibaosztálya: a jelzés kimegy, de nem történik semmi."""
        forras = (
            Path(picasapy.app.__file__).parent / "collage_save.py"
        ).read_text(encoding="utf-8")
        assert "_allitsd_be_hatterkepnek" in forras
        assert "collageDesktopBackgroundReady.emit" in forras, (
            "a jelzés maradjon meg (a #1168 értesítője erre épül)"
        )
