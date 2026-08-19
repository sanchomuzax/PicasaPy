"""Mappa gyűjtemény-hovatartozása: `[Picasa]` `P2category` (#1029).

A Picasa a bal hasáb **gyűjteményeit** (Albumok / Emberek / Projektek /
Mappák / Egyebek) nem találgatja: a mappa ini-jébe írja, melyikbe tartozik.
A kulcs a `P2category` — Picasa 2-örökség, de ma is EZ hordozza a
besorolást (ld. `docs/specs/picasa-ini-format.md`, `[Picasa]` táblázat).

A 859 valódi `.picasa.ini`-t tartalmazó korpusz értékei:

| érték | darab | hova tartozik |
|---|---:|---|
| `Folders on Disk` | 456 | **Mappák** |
| egyéni gyűjtemény-nevek (`tech`, `Csilla`, …) | 130 | a saját gyűjteménye |
| `Projects (internal)` | 8 | **Projektek** |
| `Other Stuff` | 3 | Egyebek |
| `Exported Pictures` | 3 | Projektek ▸ Exportált képek |

⚠️ A besorolást a kulcs ÉRTÉKE dönti el, nem a kulcs megléte: a többség
(`Folders on Disk`) a Mappák alá tartozik, és ott is kell maradnia.

A kollázs/film mentésekor a Picasa a kimeneti mappa ini-jébe
`P2category=Projects (internal)` sort ír (`docs/specs/picasa-kollazs-
felulet.md` 9.1/b) — ettől jelenik meg az album a Projektek gyűjtőben.
"""

from __future__ import annotations

from .document import IniDocument

_CATEGORY_KEY = "P2category"
_FOLDER_SECTION = "Picasa"

#: A Picasa saját projekt-mappáinak (Kollázsok, Filmek, Rögzített
#: videoklipek, …) `P2category` értéke — bájtra ez áll a valódi ini-kben.
PROJECTS_CATEGORY = "Projects (internal)"


def read_folder_category(document: IniDocument) -> str | None:
    """A mappa `P2category` értéke, körülvevő szóközök nélkül.

    NEM szűr és nem értelmez: a hívó dönti el, melyik gyűjteménybe sorolja.
    Hiányzó szekció, hiányzó kulcs és üres érték egyaránt `None`."""
    section = document.section(_FOLDER_SECTION)
    if section is None:
        return None
    value = section.get(_CATEGORY_KEY)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def is_projects_category(value: str | None) -> bool:
    """A `P2category` érték a **Projektek** gyűjteményt jelöli-e.

    Kis-nagybetűre és körülvevő szóközre tűrő összehasonlítás: az ini-t más
    program (vagy régebbi Picasa-verzió) is írhatta. A `Folders on Disk` és
    a többi érték szándékosan HAMIS — azok maradnak a saját helyükön."""
    if not value:
        return False
    return value.strip().casefold() == PROJECTS_CATEGORY.casefold()
