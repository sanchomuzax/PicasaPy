"""#1601: a `has_ini=1` mappák `.picasa.ini`-jeinek **egyszeri** végigolvasása.

## Miért kell ez

A bal hasáb két gyűjteménye — az **Emberek** (`index/people.py`, #26) és a
**Projektek** (`index/project_folders.py`, #1029) — séma-bővítés nélkül,
DIREKT ini-olvasással áll elő (a `schema.py` forró fájl, ld. az ottani
modul-docstringeket). Mindkettő ugyanazon a `has_ini=1` mappahalmazon megy
végig, egymástól függetlenül — tehát **minden `.picasa.ini`-t kétszer**
nyitott meg és elemzett.

MÉRVE (#1601, RPi5, tmpfs, szintetikus index, 2026-08-27):

| mappa | `people_in_index` | `project_folders` | együtt |
|---|---|---|---|
| 100 | 44 ms | 19 ms | 64 ms |
| 1 000 | 610 ms | 296 ms | 906 ms |
| 5 000 | 3 765 ms | 1 527 ms | **5 292 ms** |

Ez az induláskori szinkron munka **94%-a** — és NAS-on (a tulajdonos
gyűjteménye ott él) egy fájlnyitás nagyságrendekkel drágább, mint helyben.
Ez a „egyre lassabb": a költség a mappák számával nő, és a mappák száma
soha nem csökken.

## Miért söprés, és miért nem gyorstár

Egy „olvassuk be egyszer, tartsuk meg" gyorstár MÉRVE 5000 mappánál
**139 MB**-ot tartana bent (a nyers 14,7 MB ini-ből) — a gyorsítást a
memórián fizetnénk meg. A söprés ezért **átfolyó**: mappánként egyszer
olvas, az összes fogyasztónak odaadja ugyanazt a dokumentumot, majd
elengedi. A csúcsmemória így egyetlen ini-é marad.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterable
from pathlib import Path

from picasapy.ini import IniDocument, load_document
from picasapy.scanner import PICASA_INI_NAME

#: Egy fogyasztó: `(mappa útvonala, beolvasott dokumentum)` párt kap.
FolderIniConsumer = Callable[[str, IniDocument], None]


def sweep_folder_inis(
    conn: sqlite3.Connection, consumers: Iterable[FolderIniConsumer]
) -> None:
    """A `has_ini=1` mappák ini-jei — mappánként EGY olvasás, N fogyasztó.

    Olvashatatlan vagy hibás ini-t csendben kihagy: a könyvtár másik
    folyamat általi éppen-írása (a párhuzamosan futó Picasa!) ne omlassza
    össze a hasábot. Ez a viselkedés a `people._iter_face_data` és a
    `project_folders` korábbi, külön-külön írt kihagyásával azonos.

    Üres fogyasztólistával nem nyúl a lemezhez — nincs mit gyűjteni."""
    sinks = tuple(consumers)
    if not sinks:
        return
    for row in conn.execute("SELECT path FROM folders WHERE has_ini = 1"):
        folder_path = row["path"]
        try:
            document = load_document(Path(folder_path) / PICASA_INI_NAME)
        except (OSError, ValueError):
            continue
        for consume in sinks:
            consume(folder_path, document)


__all__ = ["FolderIniConsumer", "sweep_folder_inis"]
