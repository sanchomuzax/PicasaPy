"""Mappa gyűjtemény-hovatartozása: `[Picasa]` `P2category` (#1029).

A Picasa a bal hasáb **gyűjteményeit** (Albumok / Emberek / Projektek /
Mappák / Egyebek) nem találgatja: a mappa ini-jébe írja, melyikbe tartozik.
A kulcs a `P2category` — Picasa 2-örökség, de ma is EZ hordozza a
besorolást (ld. `docs/specs/picasa-ini-format.md`, `[Picasa]` táblázat).

A 859 valódi `.picasa.ini`-t tartalmazó korpusz `P2category`-értékei
(mérve 2026-10-09):

| érték | darab | hova tartozik |
|---|---:|---|
| `Folders on Disk` | 456 | **Mappák** |
| egyéni gyűjtemény-nevek (`tech`, `Csilla`, …) | 139 | a saját gyűjteménye |
| `Projects (internal)` | 8 | **Projektek** |
| `Other Stuff` | 3 | Egyebek |
| `Exported Pictures` | 3 | Projektek ▸ Exportált képek |
| `Downloaded Albums~<user>` | 6 | beépített letöltés-kategória |

⚠️ A besorolást a kulcs ÉRTÉKE dönti el, nem a kulcs megléte: a többség
(`Folders on Disk`) a Mappák alá tartozik, és ott is kell maradnia.

A kollázs/film mentésekor a Picasa a kimeneti mappa ini-jébe
`P2category=Projects (internal)` sort ír (`docs/specs/picasa-kollazs-
felulet.md` 9.1/b) — ettől jelenik meg az album a Projektek gyűjtőben.
"""

from __future__ import annotations

from pathlib import Path

from .document import IniDocument
from .io import update_document
from .names import INI_NAME

#: A besorolást hordozó kulcs és a mappaszintű szekció neve. Nyilvános:
#: az írók (kollázs-/film-kimenet) is EZT használják, hogy a kulcsnév
#: egyetlen helyen éljen.
CATEGORY_KEY = "P2category"
FOLDER_SECTION = "Picasa"

#: A Picasa saját projekt-mappáinak (Kollázsok, Filmek, Rögzített
#: videoklipek, …) `P2category` értéke — bájtra ez áll a valódi ini-kben.
PROJECTS_CATEGORY = "Projects (internal)"
FOLDERS_ON_DISK_CATEGORY = "Folders on Disk"
OTHER_STUFF_CATEGORY = "Other Stuff"
EXPORTED_PICTURES_CATEGORY = "Exported Pictures"
#: #4597: a „Mappa elrejtése" ide sorolja át a mappát (`0x005ee2a0`); a
#: megjelenítés `Folders on Disk`-et ír vissza.
HIDDEN_FOLDERS_CATEGORY = "Hidden Folders"
#: A Picasa 2-örökség kulcs: üres `P2category` mellett ez érvényes.
LEGACY_CATEGORY_KEY = "category"
DOWNLOADED_ALBUMS_PREFIX = "Downloaded Albums~"

_BUILTIN_CATEGORIES = frozenset(
    {
        FOLDERS_ON_DISK_CATEGORY.casefold(),
        PROJECTS_CATEGORY.casefold(),
        OTHER_STUFF_CATEGORY.casefold(),
        EXPORTED_PICTURES_CATEGORY.casefold(),
        HIDDEN_FOLDERS_CATEGORY.casefold(),
    }
)


def read_folder_category(document: IniDocument) -> str | None:
    """A mappa `P2category` értéke, körülvevő szóközök nélkül.

    NEM szűr és nem értelmez: a hívó dönti el, melyik gyűjteménybe sorolja.
    Üres vagy hiányzó `P2category` esetén a régi `category` kulcs érvényes
    (az eredeti olvasója is így tesz, #4597). Hiányzó szekció, hiányzó kulcs
    és üres érték egyaránt `None`."""
    section = document.section(FOLDER_SECTION)
    if section is None:
        return None
    for key in (CATEGORY_KEY, LEGACY_CATEGORY_KEY):
        value = section.get(key)
        stripped = value.strip() if value is not None else ""
        if stripped:
            return stripped
    return None


def with_folder_category(document: IniDocument, value: str) -> IniDocument:
    """Új dokumentum a mappa gyűjtemény-besorolásával.

    A `[Picasa] P2category` egy mappaszintű adat; az írás ugyanazon az
    immutábilis round-trip API-n halad át, mint a többi INI-metaadat.
    """
    return document.with_value(FOLDER_SECTION, CATEGORY_KEY, value)


def is_custom_collection_category(value: str | None) -> bool:
    """A `P2category` egy felhasználói gyűjtemény neve-e.

    A négy ismert beépített kategória és a letöltött albumok kategóriája
    saját Picasa-kategória. Minden más nem üres érték egyéni gyűjtemény
    neve — itt nem alkalmazunk előre rögzített névlistát.
    """
    if not value or not value.strip():
        return False
    normalized = value.strip().casefold()
    if normalized in _BUILTIN_CATEGORIES:
        return False
    if normalized == "downloaded albums" or normalized.startswith(
        DOWNLOADED_ALBUMS_PREFIX.casefold()
    ):
        return False
    return True


def is_projects_category(value: str | None) -> bool:
    """A `P2category` érték a **Projektek** gyűjteményt jelöli-e.

    Kis-nagybetűre és körülvevő szóközre tűrő összehasonlítás: az ini-t más
    program (vagy régebbi Picasa-verzió) is írhatta. A `Folders on Disk` és
    a többi érték szándékosan HAMIS — azok maradnak a saját helyükön."""
    if not value:
        return False
    return value.strip().casefold() == PROJECTS_CATEGORY.casefold()


def is_hidden_folders_category(value: str | None) -> bool:
    """A `P2category` érték a **Hidden Folders** (elrejtett mappa) jelölése-e.

    Az eredeti gyűjtemény-keresése csak az ASCII betűkre kis-nagybetű-tűrő,
    vágás nélkül hasonlít (`0x00453970`, #4597); a `casefold` ezt a
    magyar ékezetes betűkre is kiterjesztené, de a `Hidden Folders` név
    csupa ASCII, így a két viselkedés itt azonos."""
    if value is None:
        return False
    return value.strip().casefold() == HIDDEN_FOLDERS_CATEGORY.casefold()


def set_folder_hidden_in_ini(folder: str | Path, hidden: bool) -> None:
    """A mappa elrejtése/megjelenítése a mappa `.picasa.ini`-jében (#4597).

    Elrejtéskor `[Picasa] P2category=Hidden Folders`, megjelenítéskor
    `P2category=Folders on Disk` — az eredetihez híven NEM állítja vissza az
    elrejtés előtti gyűjteményt. A többi kulcs változatlan; ini nélküli
    mappánál létrejön a fájl."""
    value = FOLDERS_ON_DISK_CATEGORY if not hidden else HIDDEN_FOLDERS_CATEGORY
    update_document(
        Path(folder) / INI_NAME,
        lambda document: with_folder_category(document, value),
    )
