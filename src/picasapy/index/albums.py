"""Virtuális albumok az indexben (#9).

A `.picasa.ini` `[.album:<token>]` szekciói adják az album nevét/dátumát, a
képek `albums=` CSV-kulcsa a tagságot. Ez a modul a lekérdező oldal; a
feltöltés a szinkron során történik (`picasapy.index.sync`).

Az azonosító mindig a **token**: ugyanaz az album több mappa ini-jében is
szerepel (a Picasa minden érintett mappába kiírja a definíciót), és a
tagság is átnyúlhat mappákon. Az `albums` tábla ezért DEFINÍCIÓNKÉNT tárol
(mappa, token) — a hasábnak szánt lista itt vonja össze őket tokenre, a
nevet és a dátumot a legbővebb definícióból véve.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .queries import _SELECT, PhotoRecord, _records


@dataclass(frozen=True)
class AlbumRecord:
    """Egy album a hasábnak: azonosító, megjelenítendő név, dátum, darabszám."""

    token: str
    name: str | None
    date: str | None
    photo_count: int


def albums_in_index(conn: sqlite3.Connection) -> tuple[AlbumRecord, ...]:
    """Az összes ismert album, NÉV szerint rendezve (kis-nagybetű-tűrően).

    A névtelen albumok a lista végére kerülnek — a Picasa is így mutatja a
    hiányos definíciókat.
    """
    rows = conn.execute(
        """
        SELECT a.token AS token,
               max(a.name) AS name,
               max(a.date) AS date,
               (SELECT count(*) FROM photo_albums pa WHERE pa.token = a.token)
                   AS n
        FROM albums a
        GROUP BY a.token
        ORDER BY (max(a.name) IS NULL), lower(max(a.name)), a.token
        """
    ).fetchall()
    return tuple(
        AlbumRecord(
            token=row["token"],
            name=row["name"],
            date=row["date"],
            photo_count=row["n"],
        )
        for row in rows
    )


def album_photos(conn: sqlite3.Connection, token: str) -> tuple[PhotoRecord, ...]:
    """Az album képei — a rács ugyanazt a rekord-alakot kapja, mint máshol.

    Ismeretlen token esetén üres eredmény (nem hiba): a hasáb és az ini
    átmenetileg eltérhet, ha közben egy másik program írta az ini-t.
    """
    rows = conn.execute(
        f"{_SELECT} JOIN photo_albums pa ON pa.photo_id = p.id"
        " WHERE pa.token = ? ORDER BY f.path, p.name",
        (token,),
    )
    return _records(rows)
