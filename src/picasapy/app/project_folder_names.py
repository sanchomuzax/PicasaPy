"""A gyári projekt-mappák HONOSÍTOTT nevei és felismerésük (#1131).

## Miért van ez a modul

A tulajdonos képernyőképén a **Projektek** gyűjtemény két „Kollázsok" és
két képernyőfelvétel-mappát mutatott. Az ok mérve:

**A mappanév maga is honosított erőforrás.** A `Scrapture::capturepath`
értéke angolul `Picasa\\Screen Captures\\`, magyarul
`Picasa\\Képernyőfelvételek\\`. Ezért **más nyelvű Picasa MÁS mappát hoz
létre, és a régit nem költözteti át.** A tulajdonos NAS-korpusza ezt meg
is erősíti: `Movies`, `Filmek` ÉS `Mozgófilmek` áll egymás mellett, plusz
`Captured Videos` és `Rögzített videoklipek`.

➡️ Ez az eredeti viselkedése, nem hiba. **A mi szabályunk ebből
következik:** ha van MEGLÉVŐ (bármely nyelvű) mappa, azt használjuk —
csak akkor hozunk létre újat, ha egyik alak sem létezik. Enélkül mi
nyitnánk néma harmadikat a felhasználó gépén.

## A hat gyári mappa és az erőforrás-kulcsa

| mappa | kulcs | mikor kerül bele anyag |
|---|---|---|
| Collages / **Kollázsok** | `CCollageManager::CollagesFolder` (`0x00ca778c`) | kollázs mentésekor |
| Movies / **Mozgófilmek**, **Filmek** | `CMakeMoviePanel::SlideshowFolder` (`0x00c9ce3c`) | filmkészítéskor |
| Screen Captures / **Képernyőfelvételek** | `Scrapture::capturepath` | képernyőfelvételkor |
| Captured Videos / **Rögzített videoklipek** | `CCaptureFrame::CaptureFolder` | videórögzítéskor |
| Exported Pictures / **Exportált képek** | `IDS_EXPORTED_CATEGORY` | exportáláskor |
| Other Stuff / **Egyebek** | `IDS_DEFAULTCAT` | a be nem sorolt mappák gyűjtője |

A magyar alakok a `Picasa3i18n.dll` hivatalos fordításai.

⚠️ A **besorolást** mindegyiknél a `.picasa.ini` `[Picasa] P2category`
kulcsa adja (#1029) — a mappa neve önmagában nem elég.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class ProjectFolderKind(Enum):
    """A hat gyári projekt-mappa."""

    COLLAGES = "collages"
    MOVIES = "movies"
    SCREEN_CAPTURES = "screen_captures"
    CAPTURED_VIDEOS = "captured_videos"
    EXPORTED_PICTURES = "exported_pictures"
    OTHER_STUFF = "other_stuff"


#: nyelv → név, fajtánként. Az `en` az eredeti (nyers) alak; a `hu` a
#: `Picasa3i18n.dll` fordítása. A TÖBBALAKÚ mappák (Movies) minden ismert
#: nevét a `_TOVABBI_ALAKOK` sorolja — azokat felismerjük, de nem írunk
#: beléjük, ha van mai nyelvű.
_NEVEK: dict[ProjectFolderKind, dict[str, str]] = {
    ProjectFolderKind.COLLAGES: {"en": "Collages", "hu": "Kollázsok"},
    ProjectFolderKind.MOVIES: {"en": "Movies", "hu": "Filmek"},
    ProjectFolderKind.SCREEN_CAPTURES: {
        "en": "Screen Captures",
        "hu": "Képernyőfelvételek",
    },
    ProjectFolderKind.CAPTURED_VIDEOS: {
        "en": "Captured Videos",
        "hu": "Rögzített videoklipek",
    },
    ProjectFolderKind.EXPORTED_PICTURES: {
        "en": "Exported Pictures",
        "hu": "Exportált képek",
    },
    ProjectFolderKind.OTHER_STUFF: {"en": "Other Stuff", "hu": "Egyebek"},
}

#: Ugyanannak a mappának a KORÁBBI vagy verziófüggő alakjai. Mérve a
#: tulajdonos NAS-korpuszán: a `Mozgófilmek` (a `SlideshowFolder` kulcs
#: mai magyar értéke) a `Filmek` mellett áll — a Picasa nyelv- vagy
#: verzióváltáskor újat nyitott.
_TOVABBI_ALAKOK: dict[ProjectFolderKind, tuple[str, ...]] = {
    ProjectFolderKind.MOVIES: ("Mozgófilmek",),
}


def project_folder_name(kind: ProjectFolderKind, language: str) -> str:
    """A mappa neve az adott nyelven; ismeretlen nyelvnél az angol alak."""
    nevek = _NEVEK[kind]
    return nevek.get(language, nevek["en"])


def ismert_nevek(kind: ProjectFolderKind) -> tuple[str, ...]:
    """A mappa ÖSSZES ismert neve — a felismeréshez.

    A sorrend nem jelent elsőbbséget; a választást a
    `letezo_vagy_honos_mappa` végzi."""
    nevek = tuple(_NEVEK[kind].values())
    return nevek + _TOVABBI_ALAKOK.get(kind, ())


def letezo_vagy_honos_mappa(
    picasa_dir: Path, kind: ProjectFolderKind, language: str
) -> Path:
    """A használandó mappa: a MEGLÉVŐ, egyébként a mai nyelv szerinti.

    A szabály (#1131):

    1. ha a mai nyelv szerinti mappa létezik, az nyer — az a felhasználó
       aktuális Picasájának a mappája;
    2. ha nem, de valamelyik MÁS ismert alak létezik, azt használjuk —
       így nem nyitunk néma harmadikat a régi mellé;
    3. ha egyik sem létezik, a mai nyelv szerinti nevet adjuk vissza
       (a hívó hozza létre).

    Fájlt sosem nézünk mappának.
    """
    picasa_dir = Path(picasa_dir)
    honos = picasa_dir / project_folder_name(kind, language)
    if honos.is_dir():
        return honos
    for nev in ismert_nevek(kind):
        jelolt = picasa_dir / nev
        if jelolt.is_dir():
            return jelolt
    return honos


__all__ = [
    "ProjectFolderKind",
    "ismert_nevek",
    "letezo_vagy_honos_mappa",
    "project_folder_name",
]
