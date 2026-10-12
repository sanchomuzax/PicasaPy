"""#4892: tesztből a háttérkép-beállítás SOHA nem érheti el a valódi asztalt.

A `wallpaper.set_desktop_background` labwc alatt valódi `swaybg`-t indított
(`start_new_session=True`, tehát túlélte a tesztet), és a teszt képe a
tulajdonos fizikai kijelzőjének háttere lett. A gyökér-`conftest.py`
`valodi_asztalhoz_nem_nyul` fixture-je minden befecskendezés nélküli hívásnak
ál-fogantyúkat ad; ez az őr azt méri, hogy közben alfolyamat nem indul.
"""

from __future__ import annotations

import subprocess

import pytest


def _tilos(*_args, **_kwargs):
    raise AssertionError("tesztből valódi asztali parancs indult (#4892)")


@pytest.fixture
def alfolyamat_tiltva(monkeypatch):
    monkeypatch.setattr(subprocess, "Popen", _tilos)
    monkeypatch.setattr(subprocess, "run", _tilos)


@pytest.mark.parametrize(
    "asztal", ["labwc:wlroots", "LXDE-pi-labwc:raspberrypi", "KDE", "GNOME", ""]
)
def test_befecskendezes_nelkul_sem_indul_asztali_parancs(
    alfolyamat_tiltva, tmp_path, asztal
):
    from picasapy.app import wallpaper

    bmp = tmp_path / wallpaper.BACKGROUND_FILE
    bmp.write_bytes(b"BM")
    wallpaper.set_desktop_background(
        bmp, desktop=asztal, platform="linux", which=lambda nev: f"/usr/bin/{nev}"
    )


def test_teljesen_csupasz_hivas_sem_indul(alfolyamat_tiltva, tmp_path):
    from picasapy.app import wallpaper

    bmp = tmp_path / wallpaper.BACKGROUND_FILE
    bmp.write_bytes(b"BM")
    wallpaper.set_desktop_background(bmp)
