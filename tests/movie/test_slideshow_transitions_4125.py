"""A filmátmenet és a hangsáv beállításai a képkockaíróig jutnak (#4125)."""

import shutil
import struct
import subprocess
import wave

import numpy as np
import pytest
from picasapy.lazy_cv2 import cv2

from picasapy.movie import MovieSettings
from picasapy.movie.slideshow import _atmeneti_kocka, export_movie


def test_a_valasztott_atmenet_es_hangsav_a_film_beallitasainak_resze(tmp_path):
    hang = tmp_path / "zenesav.mp3"
    settings = MovieSettings(
        width=640,
        height=480,
        seconds_per_photo=2.0,
        transition_seconds=0.4,
        transition_type="wipeleft",
        audio_path=hang,
        audio_option=2,
    )

    assert settings.transition_type == "wipeleft"
    assert settings.transition_seconds == 0.4
    assert settings.audio_path == hang
    assert settings.audio_option == 2


def test_a_wipe_atmenet_a_feluleten_valasztott_iranyba_rajzol():
    kilepo = np.zeros((20, 40, 3), dtype=np.uint8)
    erkezo = np.full_like(kilepo, 240)

    kocka = _atmeneti_kocka(kilepo, erkezo, "wipeleft", 0.5)

    assert np.all(kocka[10, 5] == 240)
    assert np.all(kocka[10, 35] == 0)


def test_a_hang_hozzaadodik_es_a_valasztott_meret_marad(tmp_path):
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("Az FFmpeg nincs telepítve ezen a rendszeren.")
    cel = tmp_path / "film.mp4"
    proba = cv2.VideoWriter(
        str(tmp_path / "codec-proba.mp4"),
        cv2.VideoWriter_fourcc(*"mp4v"),
        8.0,
        (64, 48),
    )
    codec_ok = proba.isOpened()
    proba.release()
    if not codec_ok:
        pytest.skip("Nincs elérhető MP4-kodek ezen a rendszeren.")

    kepek = []
    for index, szin in enumerate(((0, 0, 240), (240, 0, 0))):
        kep = np.full((48, 64, 3), szin, dtype=np.uint8)
        ut = tmp_path / f"{index}.jpg"
        assert cv2.imwrite(str(ut), kep)
        kepek.append(ut)
    hang = tmp_path / "hang.wav"
    with wave.open(str(hang), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"".join(struct.pack("<h", 5000) for _ in range(8000)))

    report = export_movie(
        kepek,
        cel,
        MovieSettings(
            width=64,
            height=48,
            fps=8,
            seconds_per_photo=0.5,
            transition_seconds=0.1,
            transition_type="wipeleft",
            audio_path=hang,
            audio_option=2,
        ),
    )

    assert report.target == cel
    assert len(report.used) == 2
    olvaso = cv2.VideoCapture(str(cel))
    ok, kep = olvaso.read()
    olvaso.release()
    assert ok and kep.shape[:2] == (48, 64)
    probe = subprocess.run(
        [ffmpeg, "-i", str(cel)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert "Audio:" in probe.stderr
