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
értelme; a jegy ezért kimondottan az asztali környezet saját beállítását
kéri (`gsettings`, `pcmanfm`, `swaybg`).

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

Amelyik eszköz létezik ÉS sikerrel lefut, az nyer; a többit meg sem
próbáljuk. Ha egyik sem, azt a hívó megtudja (`None`), és a felhasználónak
meg kell mondani, HOVA került a kép — a néma sikertelenség a legrosszabb
kimenet (#936).

⚠️ Ez a modul **nem** dönt arról, mikor van háttérkép-igény: azt a kollázs
ága adja (`collage_save`), a formátum-figyelmeztetéssel együtt (spec 9.1).
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

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
    """A képet BMP-ként a Hátterek mappába írja, és visszaadja az útvonalát.

    BMP, mert az eredeti is azt ír — és mert a legtöbb asztali környezet
    beolvassa. A mappát létrehozzuk, ha nincs.
    """
    from PySide6.QtGui import QImage

    kep = QImage(str(source_image))
    if kep.isNull():
        raise OSError(f"a kép nem olvasható: {source_image}")
    cel_mappa = Path(backgrounds_dir)
    cel_mappa.mkdir(parents=True, exist_ok=True)
    cel = background_bmp_path(cel_mappa)
    if not kep.save(str(cel), "BMP"):
        raise OSError(f"a BMP kiírása nem sikerült: {cel}")
    return cel


def set_desktop_background(
    bmp_path: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess] | None = None,
    which: Callable[[str], str | None] | None = None,
) -> str | None:
    """Beállítja a háttérképet; visszaadja a SIKERES eszköz nevét, vagy `None`.

    A `runner`/`which` befecskendezhető — a próbák így nem nyúlnak a valódi
    asztalhoz (és a CI-n sincs asztali környezet).
    """
    fut = runner or subprocess.run
    keres = which or shutil.which
    ut = str(Path(bmp_path))
    for nev, parancsok in _LANC:
        if keres(nev) is None:
            continue
        try:
            for parancs in parancsok:
                eredmeny = fut(
                    [darab.format(ut=ut) for darab in parancs],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=15,
                )
                if eredmeny.returncode != 0:
                    raise OSError(
                        f"{nev}: {eredmeny.returncode} — "
                        f"{(eredmeny.stderr or '').strip()[:200]}"
                    )
        except (OSError, subprocess.SubprocessError):
            continue  # a következő eszköz jön; a néma bukást a hívó jelzi
        return nev
    return None


__all__ = [
    "BACKGROUND_FILE",
    "backgrounds_dir",
    "background_bmp_path",
    "set_desktop_background",
    "write_background_bmp",
]
