"""A filmátmenet-előnézet előkészítése külön szálon és az exporttal közösen (#4820)."""

from __future__ import annotations

import threading
import time

import numpy as np
import pytest
from PIL import Image, ImageDraw

import picasapy.movie.slideshow as slideshow
import picasapy.app.movie_preview as movie_preview
from picasapy.app.movie_preview import MovieTransitionPreviewProvider


def _request_args(path, width=240, height=118):
    return (
        str(path),
        str(path),
        "wipeleft",
        0.5,
        width,
        height,
        False,
        False,
        False,
        "",
        "",
        False,
    )


def test_a_foto_elokeszites_kozos_az_export_es_az_elonezet_kozott(
    monkeypatch, tmp_path
):
    helper = getattr(slideshow, "prepare_photo_frame", None)
    assert callable(helper), "hiányzik a slideshow közös fotó-előkészítője"

    image = np.full((30, 60, 3), (30, 80, 160), dtype=np.uint8)
    monkeypatch.setattr(slideshow, "_decode", lambda _path: image.copy())
    settings = slideshow.MovieSettings(
        width=80,
        height=60,
        background=(7, 13, 19),
    )

    actual = helper(tmp_path / "minta.jpg", settings, {})
    expected = slideshow.letterbox(
        image, settings.width, settings.height, settings.background
    )

    np.testing.assert_array_equal(actual, expected)


def test_a_vagas_felirat_es_datum_a_szovegmentes_savon_is_megjelenik(
    tmp_path, monkeypatch
):
    helper = getattr(slideshow, "prepare_photo_frame", None)
    assert callable(helper), "hiányzik a slideshow közös fotó-előkészítője"
    photo_path = tmp_path / "felirat.jpg"
    Image.new("RGB", (160, 90), (200, 100, 50)).save(photo_path)
    (tmp_path / ".picasa.ini").write_text(
        "[felirat.jpg]\ncaption=teszt felirat\n", encoding="utf-8"
    )
    megjelenitett_szovegek = []
    eredeti = ImageDraw.ImageDraw.multiline_text

    def rogzit(draw, xy, text, *args, **kwargs):
        megjelenitett_szovegek.append(str(text))
        return eredeti(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "multiline_text", rogzit)
    settings = slideshow.MovieSettings(
        width=120,
        height=120,
        cropfit=True,
        show_captions=True,
        show_dates=True,
    )
    actual = helper(photo_path, settings, {})
    source = slideshow._decode(photo_path)
    unannotated = slideshow.crop_to_fit(source, settings.width, settings.height)

    assert any("teszt felirat" in text for text in megjelenitett_szovegek)
    assert any("20" in text and "-" in text for text in megjelenitett_szovegek)
    # A bal alsó sarok a feliratsáv része, a szövegtől távol; betűpixelt nem mérünk.
    assert actual[-1, 0].mean() < unannotated[-1, 0].mean() - 10


def test_a_kocka_dekodolasa_hatterben_fut_es_nem_varja_meg_a_gui(
    monkeypatch, tmp_path
):
    provider = MovieTransitionPreviewProvider()
    decode_started = threading.Event()
    gui_thread = threading.get_ident()
    decode_threads = []

    def slow_decode(_path, goal=None):
        decode_threads.append(threading.get_ident())
        decode_started.set()
        time.sleep(0.12)
        return np.full((118, 240, 3), (20, 90, 180), dtype=np.uint8)

    monkeypatch.setattr(movie_preview, "decode_photo", slow_decode)
    started = time.monotonic()
    provider.request_transition(*_request_args(tmp_path / "slow.jpg"))
    elapsed = time.monotonic() - started

    try:
        assert elapsed < 0.06, f"a GUI-hívás {elapsed * 1000:.1f} ms-ig blokkolt"
        assert decode_started.wait(2.0), "a háttérdekódolás nem indult el"
        assert provider.wait_for_done(2_000), "a film-előnézeti worker beragadt"
        assert decode_threads and all(thread != gui_thread for thread in decode_threads)
        rendered = provider.requestImage("frame", None, None)
        assert (rendered.width(), rendered.height()) == (240, 118)
    finally:
        provider.wait_for_done(2_000)


def test_a_hibas_forras_hibakockaja_cachelodik_es_csak_egyszer_naplozodik(
    monkeypatch, tmp_path, caplog
):
    provider = MovieTransitionPreviewProvider()
    decode_count = 0

    def broken_decode(_path, goal=None):
        nonlocal decode_count
        decode_count += 1
        raise OSError("sérült tesztkép")

    monkeypatch.setattr(movie_preview, "decode_photo", broken_decode)
    args = _request_args(tmp_path / "hibas.jpg")

    for _ in range(3):
        provider.render_transition(*args)

    errors = [
        record
        for record in caplog.records
        if "hibas.jpg" in record.getMessage()
        or "sérült tesztkép" in record.getMessage()
    ]
    assert decode_count == 1, f"a hibás képet {decode_count} alkalommal dekódolta"
    assert len(errors) == 1, f"a forráshibát {len(errors)} alkalommal naplózta"
    assert not any(record.exc_info for record in errors), "a forráshiba stack trace-t kapott"


def test_a_maszkkoordinatak_meretenkent_cachelodnak_es_pushnal_nem_keszulnek(
    monkeypatch
):
    coordinates = getattr(slideshow, "_atmenet_koordinatak", None)
    assert callable(coordinates), "hiányzik a méret szerint cache-elt átmeneti maszk"

    coordinates.cache_clear()
    outgoing = np.zeros((24, 40, 3), dtype=np.uint8)
    incoming = np.full_like(outgoing, 255)
    slideshow._atmeneti_kocka(outgoing, incoming, "wipeleft", 0.5)
    slideshow._atmeneti_kocka(outgoing, incoming, "wipeup", 0.5)
    assert coordinates.cache_info().misses == 1

    before = coordinates.cache_info().misses
    slideshow._atmeneti_kocka(outgoing, incoming, "pushleft", 0.5)
    assert coordinates.cache_info().misses == before


def test_a_nagy_filmfelbontasnal_is_a_nezoke_merete_keszul():
    assert movie_preview._preview_size(1920, 1080, True, 240, 118) == (210, 118)


def test_a_nezoke_dekodolasa_a_kert_meretre_kicsinyitva_tortenik(tmp_path):
    photo_path = tmp_path / "nagy.jpg"
    Image.new("RGB", (2400, 1600), (80, 120, 180)).save(photo_path)

    decoded = movie_preview._decode_preview(photo_path, 210, 118, False)

    assert decoded.shape[1] <= 210
    assert decoded.shape[0] <= 118


@pytest.mark.parametrize("transition", ("wipeleft", "pushleft", "circlein", "kenburns"))
def test_a_melegitett_atmeneti_kocka_60_ms_alatt_felkeszul(
    monkeypatch, tmp_path, transition
):
    provider = MovieTransitionPreviewProvider()
    image = np.full((118, 210, 3), (30, 120, 210), dtype=np.uint8)
    monkeypatch.setattr(movie_preview, "decode_photo", lambda _path, goal=None: image.copy())
    args = list(_request_args(tmp_path / "gyors.jpg", 210, 118))
    args[2] = transition
    provider.render_transition(*args)
    started = time.perf_counter()
    provider.render_transition(*args)
    elapsed = time.perf_counter() - started
    print(f"{transition} 210×118 meleg render: {elapsed * 1000:.2f} ms")
    assert elapsed < 0.060, f"{transition}: melegített render {elapsed * 1000:.1f} ms"
