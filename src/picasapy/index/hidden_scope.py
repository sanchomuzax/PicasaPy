"""#4887: a REJTETT mappák képeinek közös láthatósági kapuja.

A rejtett mappa (`folders.hidden != 0`, #1637/#4597) képei a mappán kívüli
nézetekben sem látszhatnak — keresés, szűrők, Emberek, idővonal, albumok,
térkép, diavetítés, képernyővédő. A szűrés ezért NEM nézetenként történik,
hanem itt, az olvasó lekérdezések közös pontján: a fotó-lekérdezések
`folders` illesztése ezt a feltételt kapja (`visible_folder_sql`).

## Honnan tudja a lekérdezés, hogy látszhatnak-e a rejtettek?

A láthatóság a felület TÉNYLEGES `showHidden` értéke (tárolt kapcsoló ÉS
nincs jelszó vagy fel van oldva). Ezt a felület EGY helyről közli
(`set_hidden_folders_visible`), adatbázis-fájlonként; a lekérdezés a
kapcsolat saját fájljából (`PRAGMA database_list`) keresi ki. Így a több
tucat `open_index` hívóhelyen semmit nem kell átadni, és a felület nélkül
futó belépési pontok (pl. a tétlenségkor induló képernyővédő) is a
biztonságos alapértéket kapják: **a rejtett mappa képe nem látszik**.

A belső, nem megjelenítő utak (importnál a „már a könyvtárban van-e",
személy átnevezése minden ini-ben, arcfelismerés) a lekérdezés
`include_hidden_folders=True` paraméterével kérik a teljes könyvtárat.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path

#: Adatbázis-fájl (normalizált út) → látszhatnak-e a rejtett mappák képei.
#: Hiányzó kulcs = nem látszanak (biztonságos alapérték).
_LATHATO: dict[str, bool] = {}
_ZAR = threading.Lock()


def _kulcs(db_path: str | Path) -> str:
    szoveg = str(db_path)
    if not szoveg or szoveg == ":memory:":
        return szoveg
    return os.path.normcase(os.path.realpath(szoveg))


def set_hidden_folders_visible(db_path: str | Path, visible: bool) -> None:
    """A felület tényleges `showHidden` értékének közlése az indexszel."""
    with _ZAR:
        _LATHATO[_kulcs(db_path)] = bool(visible)


def hidden_folders_visible(db_path: str | Path) -> bool:
    """Látszhatnak-e a rejtett mappák képei ennél az adatbázisnál."""
    with _ZAR:
        return _LATHATO.get(_kulcs(db_path), False)


def _connection_path(conn: sqlite3.Connection) -> str:
    for sor in conn.execute("PRAGMA database_list"):
        if sor[1] == "main":
            return sor[2] or ""
    return ""


def show_hidden_folders(
    conn: sqlite3.Connection, include_hidden_folders: bool | None = None
) -> bool:
    """A lekérdezésre érvényes döntés: a kifejezett kérés, különben a
    felület által közölt láthatóság."""
    if include_hidden_folders is not None:
        return bool(include_hidden_folders)
    return hidden_folders_visible(_connection_path(conn))


def visible_folder_sql(
    conn: sqlite3.Connection,
    alias: str = "f",
    include_hidden_folders: bool | None = None,
) -> str:
    """SQL-feltétel a `folders` illesztéshez: csak a látható mappák sorai.

    A `JOIN folders <alias> ON ... AND <feltétel>` alakba való, így a
    hívó saját `WHERE`/`JOIN` ágai változatlanok maradnak."""
    if show_hidden_folders(conn, include_hidden_folders):
        return "1 = 1"
    return f"{alias}.hidden = 0"


def excluded_folder_paths(
    conn: sqlite3.Connection, include_hidden_folders: bool | None = None
) -> frozenset[str]:
    """A kiszűrendő (rejtett) mappák útvonalai — az ini-söprésből élő
    összesítőknek (Emberek), ahol nincs SQL-illesztés. Üres, ha a
    rejtettek látszhatnak."""
    if show_hidden_folders(conn, include_hidden_folders):
        return frozenset()
    return frozenset(
        sor[0] for sor in conn.execute("SELECT path FROM folders WHERE hidden != 0")
    )


__all__ = [
    "excluded_folder_paths",
    "hidden_folders_visible",
    "set_hidden_folders_visible",
    "show_hidden_folders",
    "visible_folder_sql",
]
