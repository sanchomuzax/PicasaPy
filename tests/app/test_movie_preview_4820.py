"""A filmátmenet-előnézet előkészítése külön szálon és az exporttal közösen (#4820)."""

from __future__ import annotations

import threading
import time
import os
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw
from PySide6.QtTest import QSignalSpy

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
    assert movie_preview._preview_size(1920, 1080, True, 240, 118) == (1920, 1080)


def test_a_szovegdia_betukeresese_a_provider_pooljaban_melegszik(monkeypatch):
    render_threads = []
    gui_thread = threading.get_ident()

    def fake_render(_slide, _settings):
        render_threads.append(threading.get_ident())
        return np.zeros((16, 16, 3), dtype=np.uint8)

    monkeypatch.setattr(movie_preview, "render_text_slide", fake_render)
    provider = MovieTransitionPreviewProvider()
    try:
        assert provider.wait_for_done(2_000), "a betű-előmelegítő beragadt"
        assert render_threads, "a provider létrehozása nem melegítette be a betűkeresést"
        assert all(thread != gui_thread for thread in render_threads)
    finally:
        provider.wait_for_done(2_000)


def test_a_kovetkezo_dia_alapkockaja_hatterszalban_elore_cachelodik(
    monkeypatch, tmp_path
):
    prefetch = getattr(MovieTransitionPreviewProvider, "prefetch_frame", None)
    assert callable(prefetch), "a provider nem tud következő diát előre cache-elni"
    provider = MovieTransitionPreviewProvider()
    photo_path = tmp_path / "kovetkezo.jpg"
    photo_path.touch()
    prepared = []

    def fake_prepare(path, settings, documents, decoder=None):
        prepared.append(Path(path))
        return np.full((settings.height, settings.width, 3), 80, dtype=np.uint8)

    monkeypatch.setattr(movie_preview, "prepare_photo_frame", fake_prepare)
    try:
        provider.prefetch_frame(
            str(photo_path), "", 80, 40, False, False, False,
            False, 80, 40, 1.0,
        )
        assert provider.wait_for_done(2_000), "a következő dia előtöltése beragadt"
        assert prepared == [photo_path]
    finally:
        provider.wait_for_done(2_000)


def test_a_keszulo_regi_kocka_is_jelzi_a_generaciojat_es_megjelenitheto(
    qt_app, monkeypatch
):
    provider = MovieTransitionPreviewProvider()
    ready = QSignalSpy(provider.frameReady)
    monkeypatch.setattr(provider, "_store_frame", lambda _frame: "image://moviepreview/frame?rev=old")
    provider._generation = 2
    provider._running = True

    provider._finish_request(1, np.zeros((2, 2, 3), dtype=np.uint8))

    assert ready.count() == 1, "a közben elkészült régi kocka el lett dobva"
    assert ready.at(0) == ["image://moviepreview/frame?rev=old", 1]


def test_a_picasa_ini_mtime_valtozasa_ervenyteleniti_a_fotokockat(
    monkeypatch, tmp_path
):
    provider = MovieTransitionPreviewProvider()
    photo_path = tmp_path / "feliratos.jpg"
    photo_path.touch()
    ini_path = tmp_path / ".picasa.ini"
    ini_path.write_text("[feliratos.jpg]\ncaption=első\n", encoding="utf-8")
    calls = []

    def fake_prepare(path, settings, documents, decoder=None):
        calls.append(Path(path))
        return np.full((settings.height, settings.width, 3), 100, dtype=np.uint8)

    monkeypatch.setattr(movie_preview, "prepare_photo_frame", fake_prepare)
    args = _request_args(photo_path, 40, 20)
    provider.render_transition(*args)
    first_mtime = ini_path.stat().st_mtime_ns
    ini_path.write_text("[feliratos.jpg]\ncaption=második\n", encoding="utf-8")
    os.utime(ini_path, ns=(first_mtime + 1_000_000, first_mtime + 1_000_000))
    provider.render_transition(*args)

    assert calls == [photo_path, photo_path], (
        "a feliratfájl módosítása után a fotó az elavult gyorsítótárból jött"
    )


_MASZKOS_ATMENETEK = (
    "wipeleft", "wiperight", "wipeup", "wipedown",
    "diagwipeul", "diagwipeur", "diagwipedl", "diagwipedr",
    "circlein", "circleout", "rect",
)


def _regi_mgrid_atmeneti_kocka(kilepo, erkezo, tipus, arany):
    """A review előtti np.mgrid képlet, a float64 kerekítési őréhez."""
    p = min(1.0, max(0.0, arany))
    magassag, szelesseg = kilepo.shape[:2]
    y, x = np.mgrid[0:magassag, 0:szelesseg]
    xn = (x + 0.5) / max(1, szelesseg)
    yn = (y + 0.5) / max(1, magassag)
    if tipus == "wipeleft":
        mask = xn < p
    elif tipus == "wiperight":
        mask = xn >= 1.0 - p
    elif tipus == "wipeup":
        mask = yn >= 1.0 - p
    elif tipus == "wipedown":
        mask = yn < p
    elif tipus == "diagwipeul":
        mask = xn + yn < 2.0 * p
    elif tipus == "diagwipeur":
        mask = (1.0 - xn) + yn < 2.0 * p
    elif tipus == "diagwipedl":
        mask = xn + (1.0 - yn) < 2.0 * p
    elif tipus == "diagwipedr":
        mask = (1.0 - xn) + (1.0 - yn) < 2.0 * p
    elif tipus in {"circlein", "circleout"}:
        mask = np.sqrt(((xn - 0.5) * 2) ** 2 + ((yn - 0.5) * 2) ** 2) <= p * np.sqrt(2)
        if tipus == "circleout":
            mask = ~mask
    else:
        mask = (np.abs(xn - 0.5) <= p * 0.5) & (np.abs(yn - 0.5) <= p * 0.5)
    return np.where(mask[..., None], erkezo, kilepo)


@pytest.mark.parametrize("tipus", _MASZKOS_ATMENETEK)
@pytest.mark.parametrize("shape", ((600, 800), (1080, 1920)))
def test_a_maszkos_atmenet_bitre_egyezik_a_regi_mgrid_keplettel(tipus, shape):
    height, width = shape
    y, x = np.mgrid[0:height, 0:width]
    outgoing = np.stack((x % 251, y % 253, (x + y) % 255), axis=-1).astype(np.uint8)
    incoming = np.stack(((x * 3) % 255, (y * 5) % 255, (x * 2 + y) % 255), axis=-1).astype(np.uint8)

    progresses = [step / 30 for step in (6, 12, 24, 29)] + [2 / 3]
    for progress in progresses:
        actual = slideshow._atmeneti_kocka(outgoing, incoming, tipus, progress)
        expected = _regi_mgrid_atmeneti_kocka(outgoing, incoming, tipus, progress)
        np.testing.assert_array_equal(
            actual, expected, err_msg=f"{tipus}, előrehaladás={progress:.6f}"
        )


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
