"""A Picasa 16 bites szemcsézése — a spec 5.3 és 5.3/b alapján (#4412)."""

from __future__ import annotations

import numpy as np

from picasapy.render.display_modes import (
    PicasaDitherGenerator,
    apply_display_mode,
    display_mode_changes_pixels,
)

# A spec 5.3/b.5 bizonyított, ismert vetőmagja.
VETOMAG = 0x80AE2D6C

# A spec 5.3/b.5-ből, kiírva (B, G, R sorrendben), nem a termékkódból olvasva.
ELSO_NYOLC_ZAJ_BGR = (
    (5, 3, 3),
    (4, 2, 0),
    (2, 2, 6),
    (4, 0, 7),
    (2, 0, 1),
    (5, 3, 0),
    (4, 2, 2),
    (7, 1, 0),
)


def test_a_picasa_generatormag_elso_nyolc_zaja_bajtra_pontos():
    generalt = PicasaDitherGenerator(VETOMAG).random_uint32(8)
    kapott = tuple(
        (
            int(ertek & 0x07),
            int((ertek >> 8) & 0x03),
            int((ertek >> 16) & 0x07),
        )
        for ertek in generalt
    )

    assert kapott == ELSO_NYOLC_ZAJ_BGR


def test_a_generatormag_a_624_elemu_twist_utan_is_bajtra_pontos():
    szavak = PicasaDitherGenerator(VETOMAG).random_uint32(689)

    def zaj(indexek):
        return tuple(
            (
                int(ertek & 0x07),
                int((ertek >> 8) & 0x03),
                int((ertek >> 16) & 0x07),
            )
            for ertek in szavak[indexek]
        )

    vart_elso = (
        (3, 2, 5),
        (5, 1, 1),
        (1, 1, 0),
        (2, 0, 7),
        (6, 0, 1),
        (0, 2, 4),
        (1, 0, 3),
        (6, 0, 5),
    )
    vart_masodik = (
        (6, 0, 0),
        (4, 0, 0),
        (7, 1, 7),
        (2, 2, 0),
        (4, 2, 2),
        (1, 2, 3),
        (3, 3, 2),
        (1, 2, 4),
    )

    assert zaj(slice(624, 632)) == vart_elso
    assert zaj(slice(681, 689)) == vart_masodik


def test_a_menu_modja_telito_bajtonkent_adja_hozza_a_zajt():
    forras = np.full((2, 4, 3), 250, dtype=np.uint8)
    elotte = forras.copy()

    eredmeny = apply_display_mode(forras, "dither16")

    # A vetőmag első nyolc értéke, a B/G/R bitek és a telítő összeadás
    # eredménye a spec képletéből, kézzel kiírva.
    vart = np.array(
        [
            [
                (253, 253, 255),
                (250, 252, 254),
                (255, 252, 252),
                (255, 250, 254),
            ],
            [
                (251, 250, 252),
                (250, 253, 255),
                (252, 252, 254),
                (250, 251, 255),
            ],
        ],
        dtype=np.uint8,
    )

    assert np.array_equal(eredmeny, vart)
    assert np.array_equal(forras, elotte), "a megjelenítési mód átírta a bemenetet"
    assert display_mode_changes_pixels("dither16") is True
