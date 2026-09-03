"""A mozgófilm KIMENETE: célmappa, fájlnév, sorszámozás, projekt-jelölés (#1977).

Az eredeti Picasában a „Mozgófilm létrehozása" **nem kér célfájlt**: maga
dönti el a mappát, a nevet és a kiterjesztést, és a mappát
projekt-mappaként be is jelöli. Nálunk eddig a felhasználónak kellett
fájlválasztóban célfájlt adnia, és amíg nem adott, az OK gomb tiltott volt.

A **kollázs** ága ezt a mintát már viszi (`collage_output`); ez a modul a
film ágára hozza ugyanazt. A közös részeket (tiltott karakterek,
DOS-eszköznevek, `pictures_dir`, `.picasa.ini` írás) SZÁNDÉKOSAN a
`collage_output`-ból használjuk újra — két külön másolat előbb-utóbb
elcsúszna egymástól.

## Mért alapok (`docs/specs/picasa-create-features.md` 2.6/c)

| mit | cím |
|---|---|
| célmappa: `My Pictures` → `Picasa` → honosított `Movies` | `0x0061cf20`, `0x00c9ce3c` |
| tartalék `My Videos`, ha a mappa nem hozható létre | `0x00620af9`–`0x00620b1d` |
| a mappa `.picasa.ini`-je `P2category=Projects (internal)` | `0x0061d005` → `0x00445a30` |
| alapnév `slideshowmovie` / `diavetites_jellegu_film` | `CMakeMoviePanel::deffilename` |
| tiltott karakterek | `0x00620b61` → `0x009946f0` |
| sorszámozás `%s%lu`, SZÓKÖZ NÉLKÜL | `0x00993030` → `0x00992ed0` |

## ⚠️ Egy TUDATOS eltérés: a kiterjesztés

Az eredeti `.wmv`-t ír a WMF SDK-val (`wmvcore.dll`,
`WMCreateProfileManager` + `WMCreateWriter`, `0x00549240`). Az a
könyvtár Linuxon nem létezik, ezért nálunk **`.mp4`** marad — a jegy 9.
pontja ezt kimondottan így kéri. A mappa, a név és a sorszámozás
viszont az eredetit követi, mert azon múlik, hogy a windowsos Picasa
ugyanott találja meg a filmeket.
"""

from __future__ import annotations

from pathlib import Path

from .collage_output import (
    _ESZKOZNEVEK,
    _TILTOTT_KARAKTEREK,
    pictures_dir,
)
from .collage_output import write_album_ini as write_album_ini

#: A film alapértelmezett fájlnév-tője — a `CMakeMoviePanel::deffilename`
#: MAGYAR oszlopa a `stringres` szótárból. Nem fordítjuk újra: a windowsos
#: Picasa ezt a nevet adja, és a két program egymás mellé ír.
FILENAME_STEM = "diavetites_jellegu_film"

#: A kimenet kiterjesztése. Ld. a modul fejlécét — tudatos eltérés.
OUTPUT_SUFFIX = ".mp4"

#: A film-kimenet mappájának beállítás-kulcsa — a `collage/outputDir`
#: párja. Nem csak kényelem: enélkül a próbák a felhasználó VALÓDI
#: `~/Képek` mappájába írnának (#1054 — ott hagytunk egyszer egy
#: `autosave.cxf`-et, amit később valódi felhasználói munkának néztünk).
OUTPUT_DIR_KEY = "movie/outputDir"


def safe_stem(title: str | None) -> str:
    """A címből fájlnév-tő; üres címnél a mért alapnév.

    Ugyanaz a szabály, mint a kollázsnál: a tiltott karakterek kiesnek, a
    DOS-eszköznevek aláhúzást kapnak, és a tartalékra esés az UTOLSÓ
    lépés (a „..." típusú cím a csonkolás után lesz üres).
    """
    tiszta = _TILTOTT_KARAKTEREK.sub("", str(title or ""))
    tiszta = tiszta.strip().strip(".").strip()
    if not tiszta:
        return FILENAME_STEM
    if tiszta.split(".")[0].casefold() in _ESZKOZNEVEK:
        return f"{tiszta}_"
    return tiszta


def output_dir(configured: str | None, language: str | None = None) -> Path:
    """A célmappa: a beállított, egyébként a `Picasa` alatti Filmek-mappa.

    ⚠️ #1131: a mappanév honosított erőforrás
    (`CMakeMoviePanel::SlideshowFolder`), és a tulajdonos gyűjteményében
    **három** alak áll egymás mellett (`Movies`, `Filmek`,
    `Mozgófilmek`). Ha bármelyik létezik, abba írunk — újat csak akkor
    nyitunk, ha egyik sem.
    """
    if configured:
        return Path(str(configured))
    from .collage_output import _felulet_nyelve
    from .project_folder_names import ProjectFolderKind, letezo_vagy_honos_mappa

    nyelv = language or _felulet_nyelve()
    return letezo_vagy_honos_mappa(
        pictures_dir() / "Picasa", ProjectFolderKind.MOVIES, nyelv
    )


def output_path(folder: Path | str, title: str | None = "") -> Path:
    """A célfájl: `<cím>.mp4`, ütközéskor `<cím>1.mp4`, `<cím>2.mp4`…

    Az `%s%lu` formátum SZÓKÖZ NÉLKÜLI — a Picasa így számozott, és a mi
    kimenetünk mellette fog állni ugyanabban a mappában.
    """
    mappa = Path(folder)
    to = safe_stem(title)
    for sorszam in range(0, 10_000):
        nev = to if sorszam == 0 else f"{to}{sorszam}"
        jelolt = mappa / f"{nev}{OUTPUT_SUFFIX}"
        if not jelolt.exists():
            return jelolt
    raise ValueError(f"Nem található szabad fájlnév a(z) {mappa} mappában.")


def _rendszer_videok() -> Path | None:
    """A rendszer Videók mappája — a Picasa `My Videos` tartaléka."""
    from PySide6.QtCore import QStandardPaths

    ut = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.MoviesLocation
    )
    return Path(ut) if ut else None


def tartalek_mappa(cel: Path | str) -> Path:
    """A célmappa létrehozása; ha nem megy, a rendszer Videók mappája.

    Az eredeti ugyanígy jár el (`0x00620af9`–`0x00620b1d`): ha a
    `Picasa\\Mozgófilmek` nem hozható létre, a `My Videos`-ba ír — és NEM
    hibaüzenetet ad. Ha a tartalék sincs meg, a kivétel FELSZÁLL: néma
    hiba helyett a hívó dönt, mit mutat a felhasználónak.
    """
    cel = Path(cel)
    try:
        cel.mkdir(parents=True, exist_ok=True)
        return cel
    except OSError:
        tartalek = _rendszer_videok()
        if tartalek is None:
            raise
        tartalek.mkdir(parents=True, exist_ok=True)
        return tartalek


__all__ = [
    "FILENAME_STEM",
    "OUTPUT_SUFFIX",
    "output_dir",
    "output_path",
    "safe_stem",
    "tartalek_mappa",
    "write_album_ini",
]
