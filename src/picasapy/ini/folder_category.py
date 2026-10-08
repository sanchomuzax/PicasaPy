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

from .document import IniDocument

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
DOWNLOADED_ALBUMS_PREFIX = "Downloaded Albums~"

_BUILTIN_CATEGORIES = frozenset(
    {
        FOLDERS_ON_DISK_CATEGORY.casefold(),
        PROJECTS_CATEGORY.casefold(),
        OTHER_STUFF_CATEGORY.casefold(),
        EXPORTED_PICTURES_CATEGORY.casefold(),
    }
)


def read_folder_category(document: IniDocument) -> str | None:
    """A mappa `P2category` értéke, körülvevő szóközök nélkül.

    NEM szűr és nem értelmez: a hívó dönti el, melyik gyűjteménybe sorolja.
    Hiányzó szekció, hiányzó kulcs és üres érték egyaránt `None`."""
    section = document.section(FOLDER_SECTION)
    if section is None:
        return None
    value = section.get(CATEGORY_KEY)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


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
