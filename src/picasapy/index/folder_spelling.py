"""Egy hálózati mappa EGYETLEN alakja az indexben (#7045).

## A hiba

A `folders.path` oszlop kis-nagybetű-érzékeny `UNIQUE` kulcs, Windowson viszont
a `\\\\DS215j\\photo\\...` és a `\\\\ds215j\\photo\\...` UGYANAZ a mappa. Ha a
szinkron a gyökeret más kis-nagybetűs alakban kapta, mint amilyenben az index
már ismerte, a mappa kétszer került a hasábba: a második sor a frissen
beolvasott (`unread`, félkövér) volt, és minden indításnál újra beolvasódott.

## A megoldás

A szinkron az útvonalat az INDEXBEN már látott alakra igazítja (a legrégebbi
sor szerint), mielőtt bejárna vagy írna. Az igazítás csak a már ismert ELŐTAGOT
cseréli le (szerver, megosztás, felettes mappák); ami az indexben még nincs,
az a megadott alakban marad. Így a tárolt és megjelenített alak az ELSŐ,
eredeti alak, és a bejárás útvonalai (kihagyás-állapot, takarítás) végig
ugyanazt a szöveget használják.

Csak Windowson, hálózati útvonalra fut: helyi útvonalon a `Path.resolve()` a
lemez saját kis-nagybetűjét adja, POSIX-on a kis-nagybetű valódi különbség.
Az összehasonlítás komponensenként, `lower()`-rel megy, ahogy a Windows
`normcase` is teszi; az ASCII-s SQL-szűrő csak a jelölteket szűkíti, a
döntést mindig a Python-összevetés hozza (nem ASCII nevű mappára az egész
táblát végignézzük).
"""

from __future__ import annotations

import ntpath
import sqlite3
from collections.abc import Iterator

from picasapy import paths


def split_unc(text: str) -> tuple[str, list[str]]:
    """`(\\\\szerver\\megosztás, [komponensek])`; a komponensek nem üresek."""
    meghajto, maradek = ntpath.splitdrive(text)
    reszek = [resz for resz in maradek.replace("/", "\\").split("\\") if resz]
    return meghajto, reszek


def _osszefuz(meghajto: str, reszek: list[str]) -> str:
    return meghajto + "".join("\\" + resz for resz in reszek)


def _kulcs(meghajto: str, reszek: list[str]) -> tuple[str, tuple[str, ...]]:
    return meghajto.lower(), tuple(resz.lower() for resz in reszek)


def candidate_rows(conn: sqlite3.Connection, meghajto: str, reszek: list[str]) -> Iterator[sqlite3.Row]:
    """Az `elotag` nevű mappa és a mappák alatta, kis-nagybetű-függetlenül
    JELÖLTEK (id szerint): az SQL `LIKE` az ASCII-t érzéketlenül hasonlítja,
    a hívó a komponensenkénti `lower()`-rel dönt. Nem ASCII előtagra az egész
    tábla jelölt."""
    elotag = _osszefuz(meghajto, reszek)
    if not elotag.isascii():
        yield from conn.execute("SELECT id, path, has_ini FROM folders ORDER BY id")
        return
    minta = elotag.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    yield from conn.execute(
        "SELECT id, path, has_ini FROM folders"
        " WHERE path = ? OR path = ? OR path LIKE ? ESCAPE '\\' ORDER BY id",
        (elotag, elotag + "\\", minta + "\\\\%"),
    )


def rows_under(conn: sqlite3.Connection, root: str) -> list[sqlite3.Row]:
    """A hálózati `root` és a mappái az indexben, bármilyen kis-nagybetűs alakban."""
    meghajto, reszek = split_unc(root)
    kulcs = _kulcs(meghajto, reszek)
    mennyi = len(reszek)
    talalatok = []
    for sor in candidate_rows(conn, meghajto, reszek):
        sor_meghajto, sor_reszek = split_unc(sor["path"])
        if len(sor_reszek) >= mennyi and _kulcs(sor_meghajto, sor_reszek[:mennyi]) == kulcs:
            talalatok.append(sor)
    return talalatok


def _ismert_alak(conn: sqlite3.Connection, meghajto: str, reszek: list[str]) -> str | None:
    kulcs = _kulcs(meghajto, reszek)
    mennyi = len(reszek)
    for sor in candidate_rows(conn, meghajto, reszek):
        sor_meghajto, sor_reszek = split_unc(sor["path"])
        if len(sor_reszek) >= mennyi and _kulcs(sor_meghajto, sor_reszek[:mennyi]) == kulcs:
            return _osszefuz(sor_meghajto, sor_reszek[:mennyi])
    return None


def adopt_indexed_spelling(conn: sqlite3.Connection | None, path: str) -> str:
    """A `path` az indexben ismert (legrégebbi sor szerinti) kis-nagybetűs alakban.

    A legmélyebb, az indexben már ismert előtagot cseréli az ismert alakra, a
    maradék változatlan. Nem hálózati útvonalra, illetve nem Windowson a
    bemenetet adja vissza, az adatbázishoz hozzá sem nyúl."""
    if not paths.windowsos_halozati_ut(path):
        return path
    # a leggyakoribb eset: pontosan ez az alak már az indexben van (egyedi
    # indexre támaszkodó kérdés, nem végigolvasás)
    if conn.execute("SELECT 1 FROM folders WHERE path = ?", (path,)).fetchone() is not None:
        return path
    meghajto, reszek = split_unc(path)
    for melyseg in range(len(reszek), -1, -1):
        ismert = _ismert_alak(conn, meghajto, reszek[:melyseg])
        if ismert is None:
            continue
        eredmeny = ismert + "".join("\\" + resz for resz in reszek[melyseg:])
        if not reszek and path.endswith(("\\", "/")):
            eredmeny += "\\"
        return eredmeny
    return path
