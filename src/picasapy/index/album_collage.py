r"""#1168: „van-e ehhez az albumhoz kollázs?" — a `hascollage` megfelelője.

A Picasa PMP-adatbázisában van egy `albumdata_hascollage.pmp` oszlop (1
bájt albumonként, típuskód `0x03`). A K6-os visszafejtés (spec:
`docs/specs/pmp-database.md`) három dolgot tisztázott:

1. **Nem képoszlop, hanem ALBUM-oszlop.** A kollázs nem a forrásképeket
   jelöli meg — a jelző az albumhoz tartozik.
2. **A jelentése fájl-létezés**: „ehhez az albumhoz tartozik egy mentett
   `PicasaCollage.cxf`". Az útvonalat a `0x0047c3f0` építi, mindig
   `<az album mappája>\PicasaCollage.cxf` alakban.
3. **Nem a kollázs mentésekor íródik**, hanem az album
   mentésekor/betöltésekor (`0x005608f0`): a program megnézi, létezik-e a
   fájl, és abból lesz a bájt 1.

## Miért NINCS hozzá SQL-oszlop

Mert az eredetiben sincs igazi tárolt adat mögötte — származtatott jelző.
Ugyanaz a döntés, mint a `project_folders.py`-ban: a `schema.py` az
integrátoré (CONTRIBUTING.md), egy új oszlopot pedig a mappánkénti
scan-állapot miatt csak TELJES újraindexelés töltene fel, vagyis a
felhasználó a migráció után is helytelen listát látna. A lemez-olvasás a
meglévő indexen is azonnal helyes választ ad, és — az eredetivel
egyezően — magától követi, ha a `.cxf`-et közben törlik.

## Ki használja

Ma senki: a #1033 (egy projekt-mappa két gyűjteményben) és a #1131 (gyári
projekt-mappák) épül majd rá. A jelzőt ez a jegy azért adja meg most,
mert a JELENTÉSE derült ki (K6) — a hívó oldal külön jegy.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

#: Az album kollázs-projektfájlja. A név a binárisból való
#: (`0x0047c52b`: `"PicasaCollage"` + `".cxf"`), nem a mi választásunk.
COLLAGE_PROJECT_NAME = "PicasaCollage.cxf"

_CASEFOLDED = COLLAGE_PROJECT_NAME.casefold()


def folder_has_collage(folder: Path | str) -> bool:
    """Van-e `PicasaCollage.cxf` a megadott mappában.

    A keresés **kis-nagybetű-független**: a tulajdonos könyvtárában
    élesben előfordulnak csupa kisbetűs Picasa-fájlnevek (ugyanaz a
    tapasztalat, ami a `thumbindex.db` / `thumbs_index.db` kettősséget is
    adta), és egy Linuxra másolt Windows-könyvtárban a betűméret nem
    megbízható.

    Nem létező, olvashatatlan vagy időközben eltűnt mappára `False` — a
    könyvtár másik folyamat általi éppen-írása ne dobjon kivételt egy
    listázás közepén."""
    try:
        return any(
            entry.name.casefold() == _CASEFOLDED and entry.is_file()
            for entry in Path(folder).iterdir()
        )
    except OSError:
        return False


def albums_with_collage(conn: sqlite3.Connection) -> frozenset[str]:
    """Azon albumok tokenjei, amelyekhez tartozik kollázs-projektfájl.

    Az `albums` tábla DEFINÍCIÓNKÉNT tárol `(mappa, token)` párokat — a
    Picasa ugyanazt az album-definíciót minden érintett mappa ini-jébe
    kiírja. Elég, ha az EGYIK mappában ott a `.cxf`: a projektfájl az
    albumhoz tartozik, nem a mappához.

    Az eredmény immutábilis halmaz — a hívó nem tudja észrevétlenül
    módosítani a lekérdezés kimenetét."""
    tokens = set()
    rows = conn.execute(
        """
        SELECT DISTINCT a.token AS token, f.path AS path
        FROM albums a JOIN folders f ON f.id = a.folder_id
        """
    ).fetchall()
    # A mappánkénti lemez-olvasást EGYSZER végezzük el mappánként: egy
    # mappában több album is definiálva lehet, és a NAS-on minden extra
    # könyvtárbejárás valódi költség (MEMORY: 200 napló/mp limit).
    cache: dict[str, bool] = {}
    for row in rows:
        path = row["path"]
        if path not in cache:
            cache[path] = folder_has_collage(path)
        if cache[path]:
            tokens.add(row["token"])
    return frozenset(tokens)
