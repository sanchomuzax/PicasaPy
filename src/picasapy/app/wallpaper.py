"""Asztali háttérkép beállítása (#1005) — a mért Picasa-viselkedés Linuxon.

## Amit az eredeti tesz (mérve)

A kollázs „Asztali háttérkép" ága (`0x0057aa10`, a kész-értesítés kezelőjéből)
két lépést végez:

1. **BMP-t ír** a `<Képek>/Picasa/<Hátterek>/picasabackground.bmp` útvonalra
   (a mappanév honosított: `CThumbUI::BackgroundsFolder` — EN `Backgrounds`,
   HU `Hátterek`);
2. beállítja a rendszer háttérképét — Windowson a
   `HKCU\\Control Panel\\Desktop` három értékével és a
   `SystemParametersInfo(SPI_SETDESKWALLPAPER)`-rel. A két stílus-érték
   `WallpaperStyle = "0"` és `TileWallpaper = "0"`, ami a Windowsban
   **KÖZÉPRE, nyújtás és mozaik nélkül** jelent.

⇒ A **viselkedés**, amit át kell vennünk: BMP a mért helyen, és **középre
illesztett**, nem nyújtott háttérkép. A registry-írásnak Linuxon nincs
értelme; a beállítást az asztali környezet saját eszköze végzi (`gsettings`,
`pcmanfm`, `plasma-apply-wallpaperimage`, `swaybg`).

## A lánc — miért több eszköz, és miért ebben a sorrendben

Linuxon nincs EGY szabvány a háttérkép beállítására. A sorrend a projekt
környezeteitől indul (a tulajdonos gépe Raspberry Pi OS-alapú), és mindegyik
lépés a KÖZÉPRE illesztést kéri, ahogy az eredeti:

| eszköz | asztali környezet | középre |
|---|---|---|
| `gsettings` | GNOME / Cinnamon / Budgie | `picture-options=centered` |
| `pcmanfm` | LXDE, Raspberry Pi OS | `--wallpaper-mode=center` |
| `xfconf-query` | XFCE | `image-style=1` (centered) |
| `feh` | csupasz X11 (i3, openbox) | `--bg-center` |
| `plasma-apply-wallpaperimage` | KDE Plasma | a Plasma-munkamenet állítja be |
| `swaybg` | labwc, Sway és wlroots asztalok | `-m center` |

KDE és wlroots alatt a felismert asztalhoz tartozó eszköz fut; a `swaybg`
esetén a futva maradó Wayland-kliens jelzi, hogy létre tudta hozni a háttér
réteget. A többi környezetben a meglévő eszközlánc marad érvényben. Ha a
beállító eszköz nem érhető el vagy hibát jelez, a hívó `None`-t kap, és a
felhasználó megtudja, HOVA került a kép — a néma sikertelenség a legrosszabb
kimenet (#936).

⚠️ Ez a modul **nem** dönt arról, mikor van háttérkép-igény: azt a kollázs
ága adja (`collage_save`), a formátum-figyelmeztetéssel együtt (spec 9.1).
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

_log = logging.getLogger(__name__)

# A `swaybg` a háttér megjelenítése közben futó Wayland-kliens. A hivatkozást
# megtartjuk, hogy a következő háttérkép-váltáskor a saját előző példányunkat
# leállíthassuk, ne gyűljenek a rétegfelszínek.
_swaybg_folyamat: subprocess.Popen | None = None

#: #2985/#1775: a mért Windows-értékek. A `0`/`0` pár a KÖZÉPRE illesztés
#: (nyújtás és mozaik nélkül) — ugyanaz, amit a Linux-lánc minden eleme kér.
_WINDOWS_STILUS: tuple[tuple[str, str], ...] = (
    ("WallpaperStyle", "0"),
    ("TileWallpaper", "0"),
)

#: `SystemParametersInfoW` állandói (`winuser.h`): a művelet és a két jelző.
_SPI_SETDESKWALLPAPER = 0x0014
_SPIF_UPDATEINIFILE = 0x01
_SPIF_SENDCHANGE = 0x02

# Az XDG asztalazonosítói. Külön konstansok, hogy az ág-választást a teszt
# szándékos rontással is ellenőrizhesse.
_KDE_ASZTALOK = ("kde", "plasma")
_WLROOTS_ASZTALOK = ("wlroots", "labwc", "sway", "hyprland", "wayfire", "river")
_PCMANFM_ASZTALOK = ("lxde", "raspberrypi", "rpd")

#: A mért fájlnév — az eredeti ezt írja a Hátterek mappába.
BACKGROUND_FILE = "picasabackground.bmp"

#: Az egyes eszközök parancsai. A `{ut}` helyére a BMP teljes útvonala kerül.
#: MINDEGYIK a középre illesztést kéri (ld. a modul docstringjét).
_LANC: tuple[tuple[str, tuple[Sequence[str], ...]], ...] = (
    (
        "gsettings",
        (
            ("gsettings", "set", "org.gnome.desktop.background",
             "picture-uri", "file://{ut}"),
            ("gsettings", "set", "org.gnome.desktop.background",
             "picture-uri-dark", "file://{ut}"),
            ("gsettings", "set", "org.gnome.desktop.background",
             "picture-options", "centered"),
        ),
    ),
    (
        "pcmanfm",
        (
            ("pcmanfm", "--set-wallpaper={ut}", "--wallpaper-mode=center"),
        ),
    ),
    (
        "xfconf-query",
        (
            ("xfconf-query", "-c", "xfce4-desktop", "-p",
             "/backdrop/screen0/monitor0/workspace0/last-image", "-s", "{ut}"),
            ("xfconf-query", "-c", "xfce4-desktop", "-p",
             "/backdrop/screen0/monitor0/workspace0/image-style", "-s", "1"),
        ),
    ),
    ("feh", (("feh", "--bg-center", "{ut}"),)),
)


def backgrounds_dir(collage_output_dir: Path, language: str) -> Path:
    """A Hátterek mappa — a KOLLÁZS-célmappa szomszédja (#1005, #1775).

    Alapállapotban ez pontosan a mért `<Képek>/Picasa/<Hátterek>` útvonal,
    hiszen a kollázsok is a `Picasa` mappában laknak. Ha a felhasználó
    áthelyezte a kollázs-célmappát, a háttér is oda tartozik — egy
    Picasa-projektgyökér, egy hely.

    ⚠️ Ez egyben a próbák elszigetelése: a `collage/outputDir` beállítást a
    fixture-ök eltérítik, tehát a BMP nem a VALÓDI képmappába kerül. A #1005
    első változata a rendszer képmappájából számolt, és a CI őre (#1054) meg
    is fogta — egy meglévő teszt a `~/Pictures/Picasa/Backgrounds`-ba írt.
    """
    from .project_folder_names import ProjectFolderKind, letezo_vagy_honos_mappa

    return letezo_vagy_honos_mappa(
        Path(collage_output_dir).parent,
        ProjectFolderKind.BACKGROUNDS,
        language,
    )


def background_bmp_path(backgrounds_dir: Path) -> Path:
    """A háttérkép-BMP útvonala a mért fájlnévvel."""
    return Path(backgrounds_dir) / BACKGROUND_FILE


def write_background_bmp(source_image: Path, backgrounds_dir: Path) -> Path:
    """A szerkesztett, EXIF-helyes képet BMP-ként a Hátterek mappába írja.

    BMP, mert az eredeti is azt ír — és mert a legtöbb asztali környezet
    beolvassa. A `.picasa.ini` forgatását, tükrözését, vágását és
    szűrőláncát ugyanazzal a pixelrenderelővel égetjük bele, mint a poszter
    és az export kimenetébe. A mappát létrehozzuk, ha nincs.
    """
    from picasapy.lazy_cv2 import cv2
    from picasapy.printing.poster import render_edited_image

    try:
        kep = render_edited_image(Path(source_image))
    except (OSError, ValueError, cv2.error) as hiba:
        raise OSError(f"a kép nem olvasható: {source_image}") from hiba
    cel_mappa = Path(backgrounds_dir)
    cel_mappa.mkdir(parents=True, exist_ok=True)
    cel = background_bmp_path(cel_mappa)
    try:
        sikeres, kodolt = cv2.imencode(".bmp", kep)
    except cv2.error as hiba:
        raise OSError(f"a BMP kódolása nem sikerült: {cel}") from hiba
    if not sikeres:
        raise OSError(f"a BMP kiírása nem sikerült: {cel}")
    cel.write_bytes(kodolt.tobytes())
    return cel


def _windows_registry_setter(kulcs: str, ertek: str) -> None:
    """A `HKCU\\Control Panel\\Desktop` egy értékének írása (#2985)."""
    import winreg  # csak Windowson létezik — a hívás is csak ott fut

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0,
        winreg.KEY_SET_VALUE,
    ) as kulcs_objektum:
        winreg.SetValueEx(kulcs_objektum, kulcs, 0, winreg.REG_SZ, ertek)


def _windows_api(ut: str) -> bool:
    """`SystemParametersInfoW(SPI_SETDESKWALLPAPER, …)` — a mért hívás."""
    import ctypes

    return bool(
        ctypes.windll.user32.SystemParametersInfoW(
            _SPI_SETDESKWALLPAPER,
            0,
            ut,
            _SPIF_UPDATEINIFILE | _SPIF_SENDCHANGE,
        )
    )


def _allitsd_be_windowson(
    ut: str,
    registry_setter: Callable[[str, str], None],
    windows_api: Callable[[str], bool],
) -> str | None:
    """A Windows-ág: előbb a stílus, aztán a rendszernek szólás (#2985).

    A sorrend a mérésé (#1775): a stílus-értékek a registrybe mennek, és
    az API-hívás `SPIF_UPDATEINIFILE | SPIF_SENDCHANGE` jelzővel frissíti
    és szétkürtöli a változást. Bukásnál `None` — a hívó ilyenkor megmondja
    a felhasználónak, hova került a BMP (#936).
    """
    try:
        for kulcs, ertek in _WINDOWS_STILUS:
            registry_setter(kulcs, ertek)
        if not windows_api(ut):
            _log.warning("a háttérkép beállítása nem sikerült: %s", ut)
            return None
    except Exception:  # noqa: BLE001 — a kudarc nem dönthet le semmit
        _log.exception("a windowsos háttérkép-beállítás elszállt")
        return None
    return "windows"


def _asztali_kornyezet(override: str | None) -> str:
    """Az XDG által jelzett asztali környezet, vagy a próbához adott érték."""
    if override is not None:
        return override.casefold()
    reszek = [
        os.environ.get("XDG_CURRENT_DESKTOP", ""),
        os.environ.get("XDG_SESSION_DESKTOP", ""),
    ]
    if os.environ.get("KDE_SESSION_VERSION"):
        reszek.append("kde")
    return ":".join(reszek).casefold()


def _asztali_azonosito_van(kornyezet: str, azonosito: str) -> bool:
    """Illeszkedik az XDG kettősponttal elválasztott asztal-listájára is."""
    elemek = re.split(r"[:;,\s]+", kornyezet.casefold())
    return any(
        elem == azonosito or elem.startswith(f"{azonosito}-")
        for elem in elemek
        if elem
    )


def _futtasd_linux_parancsot(
    nev: str,
    parancs: Sequence[str],
    futtato: Callable[..., subprocess.CompletedProcess],
) -> str | None:
    """Szinkron beállítóparancs; a hibát a hívó felé `None` jelzi."""
    try:
        eredmeny = futtato(
            list(parancs),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        _log.exception("a %s háttérkép-parancs nem indult el", nev)
        return None
    if eredmeny.returncode != 0:
        _log.warning(
            "a %s háttérkép-parancs hibával tért vissza: %s — %s",
            nev,
            eredmeny.returncode,
            (eredmeny.stderr or "").strip()[:200],
        )
        return None
    return nev


def _allitsd_be_wlroots_hatteret(
    ut: str,
    launcher: Callable[..., subprocess.Popen],
) -> str | None:
    """Elindítja a swaybg-ot, és csak futva maradó kliensnél jelez sikert."""
    global _swaybg_folyamat

    try:
        folyamat = launcher(
            ["swaybg", "-i", ut, "-m", "center"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        # A swaybg normálisan a Wayland-munkamenetben marad. A gyors kilépés
        # azt jelenti, hogy nem tudott háttér-réteget létrehozni.
        try:
            folyamat.wait(timeout=0.25)
        except subprocess.TimeoutExpired:
            pass
        if folyamat.poll() is not None:
            _log.warning("a swaybg nem maradt futva a háttér beállítása után")
            return None
    except (OSError, subprocess.SubprocessError):
        _log.exception("a swaybg nem tudta beállítani a háttérképet")
        return None

    elozo = _swaybg_folyamat
    if elozo is not None and elozo.poll() is None:
        try:
            elozo.terminate()
            elozo.wait(timeout=1)
        except (OSError, subprocess.SubprocessError):
            _log.warning("a korábbi PicasaPy-s swaybg folyamat nem állt le")
    _swaybg_folyamat = folyamat
    return "swaybg"


def set_desktop_background(
    bmp_path: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess] | None = None,
    which: Callable[[str], str | None] | None = None,
    platform: str | None = None,
    desktop: str | None = None,
    launcher: Callable[..., subprocess.Popen] | None = None,
    registry_setter: Callable[[str, str], None] | None = None,
    windows_api: Callable[[str], bool] | None = None,
) -> str | None:
    """Beállítja a háttérképet; visszaadja a SIKERES ág nevét, vagy `None`.

    #2985: az ág-választás **platform szerint** dől el, nem
    eszköz-kereséssel — Windowson a négy Linux-eszköz keresése fölösleges
    alfutás volna, és mindig üres kézzel tért vissza (ez volt a hiba).

    Minden fogantyú befecskendezhető — a próbák így nem nyúlnak a valódi
    asztalhoz és a valódi registryhez. A KDE/labwc ág az XDG asztalazonosítója
    alapján választ, a `desktop` és `launcher` csak próbahorog.
    """
    ut = str(Path(bmp_path))
    if (platform or sys.platform) == "win32":
        return _allitsd_be_windowson(
            ut,
            registry_setter or _windows_registry_setter,
            windows_api or _windows_api,
        )
    fut = runner or subprocess.run
    keres = which or shutil.which
    kornyezet = _asztali_kornyezet(desktop)
    if any(
        _asztali_azonosito_van(kornyezet, azonosito)
        for azonosito in _KDE_ASZTALOK
    ):
        if keres("plasma-apply-wallpaperimage") is None:
            return None
        return _futtasd_linux_parancsot(
            "plasma-apply-wallpaperimage",
            ("plasma-apply-wallpaperimage", ut),
            fut,
        )

    if any(
        _asztali_azonosito_van(kornyezet, azonosito)
        for azonosito in _WLROOTS_ASZTALOK
    ):
        if keres("swaybg") is None:
            return None
        return _allitsd_be_wlroots_hatteret(ut, launcher or subprocess.Popen)

    for nev, parancsok in _LANC:
        if nev == "pcmanfm" and not any(
            _asztali_azonosito_van(kornyezet, azonosito)
            for azonosito in _PCMANFM_ASZTALOK
        ):
            continue
        if keres(nev) is None:
            continue
        eredmeny = None
        for parancs in parancsok:
            eredmeny = _futtasd_linux_parancsot(
                nev,
                tuple(darab.format(ut=ut) for darab in parancs),
                fut,
            )
            if eredmeny is None:
                break
        if eredmeny is not None:
            return nev
    return None


__all__ = [
    "BACKGROUND_FILE",
    "backgrounds_dir",
    "background_bmp_path",
    "set_desktop_background",
    "write_background_bmp",
]
