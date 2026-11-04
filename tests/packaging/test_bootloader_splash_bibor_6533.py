"""A PyInstaller bootloader-indulóképén nincs félig átlátszó képpont (#6533).

A PyInstaller Windowson az átlátszóságot bíbor (#ff00ff) kulcsszínnel oldja
meg: a félig átlátszó képpontok bíbor derengésként, keretként látszanak
(PyInstaller dokumentáció, Splash screen; pyinstaller#8579). A tulajdonos
2026-11-04-én lila/piros keretet látott a logó körül."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

_PNG = Path(__file__).resolve().parents[2] / "packaging" / "windows" / "startup-splash.png"


def test_a_bootloader_kepen_nincs_felig_atlatszo_kepont() -> None:
    kep = Image.open(_PNG)
    if "A" in kep.getbands() or "transparency" in kep.info:
        alfa = set(kep.convert("RGBA").getchannel("A").getdata())
        assert alfa <= {0, 255}, f"félig átlátszó képpontok: {sorted(alfa - {0, 255})[:5]}"


def test_a_bootloader_kep_az_eredeti_meretu_atlatszatlan_feher_kartya() -> None:
    kep = Image.open(_PNG).convert("RGBA")
    assert kep.size == (640, 235)
    assert kep.getchannel("A").getextrema() == (255, 255)
    for pont in [(0, 0), (639, 0), (0, 234), (639, 234)]:
        assert kep.getpixel(pont)[:3] == (255, 255, 255)


def test_a_kepen_nincs_bibor_kulcsszin() -> None:
    kep = Image.open(_PNG).convert("RGB")
    assert (255, 0, 255) not in set(kep.getdata())
