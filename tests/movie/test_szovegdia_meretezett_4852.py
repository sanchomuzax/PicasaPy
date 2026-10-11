"""A szöveges dia előnézeti kockája a nézőke méretén készül (#4852)."""

from __future__ import annotations

import time

import numpy as np
import pytest

from picasapy.movie.slideshow import MovieSettings, render_text_slide

_DIA = {
    "text": "Nyári emlékek\n2026",
    "font": "DejaVuSans",
    "size": 48,
    "style": 0,
    "bold": True,
    "outline": True,
    "textColor": "#ffffff",
    "backgroundColor": "#203040",
}


def test_a_teljes_meretu_render_nem_valtozik():
    settings = MovieSettings(width=1920, height=1080)
    teljes = render_text_slide(_DIA, settings)
    explicit = render_text_slide(_DIA, settings, (1920, 1080))
    assert teljes.shape == (1080, 1920, 3)
    assert np.array_equal(teljes, explicit), "az export kockája bitre változott"


def test_a_kis_kocka_merete_a_kert_meret():
    kocka = render_text_slide(_DIA, MovieSettings(width=1920, height=1080), (480, 270))
    assert kocka.shape == (270, 480, 3)


@pytest.mark.parametrize("style", (0, 2, 4, 9, 10))
def test_a_kis_kocka_arányosan_ugyanazt_mutatja_kicsiben(style):
    settings = MovieSettings(width=1920, height=1080)
    dia = {**_DIA, "style": style, "outline": False, "bold": False}
    kicsi = render_text_slide(dia, settings, (480, 270)).astype(np.float32)
    referencia = render_text_slide(dia, settings).astype(np.float32)
    import cv2

    referencia = cv2.resize(referencia, (480, 270), interpolation=cv2.INTER_AREA)
    atlag_elteres = float(np.abs(kicsi - referencia).mean())
    assert atlag_elteres < 6.0, f"a kis kocka nem a nagy kicsinyítése: {atlag_elteres}"


def test_a_nezoke_meretu_szovegdia_gyorsan_renderelodik():
    settings = MovieSettings(width=1920, height=1080)
    render_text_slide(_DIA, settings, (480, 270))  # betűkeresés bemelegítése
    kezdet = time.perf_counter()
    for _ in range(5):
        render_text_slide(_DIA, settings, (480, 270))
    atlag = (time.perf_counter() - kezdet) / 5
    assert atlag < 0.150, f"a nézőke méretű render {atlag * 1000:.0f} ms"
