"""#2985: a háttérkép beállítása WINDOWSON is.

A tulajdonos jelentette (Windows): a kép elkészül, de a program kiírja,
hogy nem tudja beállítani. A lánc négy eleme (`gsettings`, `pcmanfm`,
`xfconf-query`, `feh`) mind Linux-eszköz — Windowson egyik sincs, tehát a
lánc mindig üres kézzel tért vissza.

## Az eredeti bináris menete (#7312, `0x0057aa10`)

1. `SystemParametersInfoW(0x14, 0, BMP-út, 0)`,
2. `HKCU\\Control Panel\\Desktop` → `Wallpaper` = BMP-út,
   `WallpaperStyle="0"`, `TileWallpaper="0"`.

A próbák **befecskendezett** registry- és API-hívással mérnek: a valódi
asztalt semmi nem állítja át (a jegy külön kéri).
"""

# rontás-kontroll: picasapy.app.wallpaper._SPI_SETDESKWALLPAPER = 0x15 → 1 failed

from __future__ import annotations


from types import SimpleNamespace

import pytest

from picasapy.app import wallpaper


class _Registry:
    """A `winreg` helyett — megjegyzi, mit írtunk volna."""

    def __init__(self) -> None:
        self.ertekek: dict[str, str] = {}

    def __call__(self, kulcs: str, ertek: str) -> None:
        self.ertekek[kulcs] = ertek


class TestAWindowsAg:
    def test_a_binari_szerinti_hivasrendet_es_registry_ertekeket(self, tmp_path):
        esemenyek = []
        ut = str(tmp_path / "picasabackground.bmp")

        def registry_setter(kulcs, ertek):
            esemenyek.append(("registry", kulcs, ertek))

        def windows_api(api_ut):
            esemenyek.append(("api", api_ut))
            return True

        nev = wallpaper.set_desktop_background(
            tmp_path / "picasabackground.bmp",
            platform="win32",
            registry_setter=registry_setter,
            windows_api=windows_api,
        )

        assert nev == "windows"
        assert esemenyek == [
            ("api", ut),
            ("registry", "Wallpaper", ut),
            ("registry", "WallpaperStyle", "0"),
            ("registry", "TileWallpaper", "0"),
        ]

    def test_a_windows_api_nulla_jelzovel_hiv(self, monkeypatch, tmp_path):
        hivasok = []

        class User32:
            def SystemParametersInfoW(self, *argumentumok):
                hivasok.append(argumentumok)
                return 1

        monkeypatch.setattr(
            wallpaper, "ctypes", SimpleNamespace(windll=SimpleNamespace(user32=User32()))
        )
        ut = str(tmp_path / "picasabackground.bmp")

        assert wallpaper._windows_api(ut)
        assert hivasok == [(0x0014, 0, ut, 0)]

    def test_a_WINDOWS_agat_valasztja_platform_szerint(self, tmp_path):
        """A jegy kéri: platform szerint dőljön el, ne eszköz-kereséssel —
        Windowson a négy Linux-eszköz keresése fölösleges alfutás."""
        hivasok = []
        registry = _Registry()
        nev = wallpaper.set_desktop_background(
            tmp_path / "picasabackground.bmp",
            platform="win32",
            registry_setter=registry,
            windows_api=lambda ut: hivasok.append(ut) or True,
            which=lambda _nev: pytest.fail("Windowson nem keresünk Linux-eszközt"),
        )
        assert nev == "windows"
        assert hivasok == [str(tmp_path / "picasabackground.bmp")]

    def test_a_KOZEPRE_illesztes_ket_registry_erteke(self, tmp_path):
        registry = _Registry()
        bmp = tmp_path / "k.bmp"
        ut = str(bmp)
        wallpaper.set_desktop_background(
            bmp,
            platform="win32",
            registry_setter=registry,
            windows_api=lambda _ut: True,
        )
        assert registry.ertekek == {
            "Wallpaper": ut,
            "WallpaperStyle": "0",
            "TileWallpaper": "0",
        }, (
            "az eredeti bináris (#7312, 0x0057aa10) registry-értékei hiányoznak"
        )

    def test_a_BUKAS_nem_hazudik_sikert(self, tmp_path):
        nev = wallpaper.set_desktop_background(
            tmp_path / "k.bmp",
            platform="win32",
            registry_setter=_Registry(),
            windows_api=lambda _ut: False,
        )
        assert nev is None, "a sikertelen API-hívás sikernek látszott"

    def test_a_KIVETEL_sem_dont_le_semmit(self, tmp_path):
        def robban(_ut):
            raise OSError("nincs jogosultság")

        nev = wallpaper.set_desktop_background(
            tmp_path / "k.bmp",
            platform="win32",
            registry_setter=_Registry(),
            windows_api=robban,
        )
        assert nev is None


class TestALinuxAgErintetlen:
    def test_a_linux_lanc_valtozatlan(self, tmp_path):
        """Regresszió-őr: a Linux-ág ugyanúgy fut, mint eddig."""
        futtatott = []

        def fut(parancs, **_kw):
            futtatott.append(parancs[0])

            class Eredmeny:
                returncode = 0
                stderr = ""

            return Eredmeny()

        nev = wallpaper.set_desktop_background(
            tmp_path / "k.bmp",
            platform="linux",
            desktop="",
            runner=fut,
            which=lambda nev: "/usr/bin/" + nev if nev == "feh" else None,
        )
        assert nev == "feh"
        assert futtatott and futtatott[0] == "feh"

    def test_eszkoz_nelkul_None(self, tmp_path):
        nev = wallpaper.set_desktop_background(
            tmp_path / "k.bmp", platform="linux", which=lambda _n: None
        )
        assert nev is None
