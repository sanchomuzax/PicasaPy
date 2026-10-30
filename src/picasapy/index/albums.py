"""Virtuális albumok az indexben (#9).

A `.picasa.ini` `[.album:<token>]` szekciói adják az album nevét/dátumát, a
képek `albums=` CSV-kulcsa a tagságot. Ez a modul a lekérdező oldal; a
feltöltés a szinkron során történik (`picasapy.index.sync`).

Az azonosító mindig a **token**: ugyanaz az album több mappa ini-jében is
szerepel (a Picasa minden érintett mappába kiírja a definíciót), és a
tagság is átnyúlhat mappákon. Az `albums` tábla ezért DEFINÍCIÓNKÉNT tárol
(mappa, token) — a hasábnak szánt lista itt vonja össze őket tokenre, a
nevet és a dátumot a legbővebb definícióból véve. A még tag nélküli,
PicasaPy-ban létrehozott albumok külön profil-index táblában maradnak addig,
amíg az első tagságuk be nem kerül az ini-be (#6278).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .hidden_scope import visible_folder_sql
from .queries import PhotoRecord, _records, _select


@dataclass(frozen=True)
class AlbumRecord:
    """Egy album a hasábnak: azonosító, megjelenítendő név, dátum, darabszám."""

    token: str
    name: str | None
    date: str | None
    photo_count: int


@dataclass(frozen=True)
class PendingEmptyAlbum:
    """Üres album az ini-be írás előtti, tartós helyi tárból (#6278)."""

    token: str
    folder_path: str
    name: str | None
    date: str | None
    location: str | None
    description: str | None
    use_music: bool
    music_file: str


def _store_empty_album(
    conn: sqlite3.Connection,
    *,
    token: str,
    folder_path: str,
    name: str | None,
    date: str,
    location: str,
    description: str,
    use_music: bool,
    music_file: str,
) -> None:
    """Eltárol egy tag nélküli albumot az indexben, ini-írás nélkül."""
    conn.execute(
        "INSERT INTO local_empty_albums"
        " (token, folder_path, name, date, location, description, use_music, music_file)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            token,
            folder_path,
            name,
            date,
            location,
            description,
            int(use_music),
            music_file,
        ),
    )
    conn.commit()


def _pending_empty_album(
    conn: sqlite3.Connection, token: str
) -> PendingEmptyAlbum | None:
    """A még ini-be nem materializált album mezői, ha vannak."""
    row = conn.execute(
        "SELECT token, folder_path, name, date, location, description,"
        " use_music, music_file FROM local_empty_albums WHERE token = ?",
        (token,),
    ).fetchone()
    if row is None:
        return None
    return PendingEmptyAlbum(
        token=row["token"],
        folder_path=row["folder_path"],
        name=row["name"],
        date=row["date"],
        location=row["location"],
        description=row["description"],
        use_music=bool(row["use_music"]),
        music_file=row["music_file"],
    )


_EMPTY_ALBUM_FIELDS = frozenset(
    {"name", "date", "location", "description", "use_music", "music_file"}
)


def _update_empty_album(conn: sqlite3.Connection, token: str, **fields) -> bool:
    """A függő üres album megadott mezőinek frissítése (#6281).

    Csak a `_EMPTY_ALBUM_FIELDS` nevei írhatók; a visszatérés megmondja,
    létezett-e a sor.
    """
    unknown = set(fields) - _EMPTY_ALBUM_FIELDS
    if unknown:
        raise ValueError(f"ismeretlen albummező: {sorted(unknown)}")
    if not fields:
        return _pending_empty_album(conn, token) is not None
    values = {
        key: int(value) if key == "use_music" else value
        for key, value in fields.items()
    }
    assignments = ", ".join(f"{key} = ?" for key in values)
    cursor = conn.execute(
        f"UPDATE local_empty_albums SET {assignments} WHERE token = ?",
        (*values.values(), token),
    )
    conn.commit()
    return cursor.rowcount > 0


def _remove_empty_album(conn: sqlite3.Connection, token: str) -> bool:
    """Kivezeti a függő sort (az ini-be került vagy törölt albumnál).

    Visszatérés: létezett-e a sor.
    """
    cursor = conn.execute("DELETE FROM local_empty_albums WHERE token = ?", (token,))
    conn.commit()
    return cursor.rowcount > 0


def albums_in_index(conn: sqlite3.Connection) -> tuple[AlbumRecord, ...]:
    """Az összes ismert album, NÉV szerint rendezve (kis-nagybetű-tűrően).

    A névtelen albumok a lista végére kerülnek — a Picasa is így mutatja a
    hiányos definíciókat.
    """
    # #4887: a darabszám csak a LÁTHATÓ mappák képeit számolja — különben
    # az album a rejtett mappa képeinek számát is elárulná.
    rows = conn.execute(
        f"""
        SELECT a.token AS token,
               max(a.name) AS name,
               max(a.date) AS date,
               (SELECT count(*) FROM photo_albums pa
                  JOIN photos p ON p.id = pa.photo_id
                  JOIN folders f ON f.id = p.folder_id
                   AND {visible_folder_sql(conn)}
                 WHERE pa.token = a.token)
                   AS n
        FROM (
            SELECT token, name, date FROM albums
            UNION ALL
            SELECT token, name, date FROM local_empty_albums
        ) AS a
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

    A sorrend az `albumorder=` kézi helye szerint áll (#4599), a hely nélküliek
    a végén, utána mappa útvonala és fájlnév szerint.

    Ismeretlen token esetén üres eredmény (nem hiba): a hasáb és az ini
    átmenetileg eltérhet, ha közben egy másik program írta az ini-t.
    """
    rows = conn.execute(
        f"{_select(conn)} JOIN photo_albums pa ON pa.photo_id = p.id"
        " WHERE pa.token = ?"
        # #4599 (ADR-016): kézi hely szerint; a hely nélküliek a végén,
        # utána mappa útvonala, fájlnév (hely nélküli albumnál = a mai rend)
        " ORDER BY (pa.place IS NULL), pa.place, f.path, p.name",
        (token,),
    )
    return _records(rows)
