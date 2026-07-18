"""Mappánként csoportosított keresési találatok (#7).

A Picasa találati nézete (150933-as referencia) a találatokat mappánként
csoportosítja: minden csoportnak fejléce van (mappanév + dátum). Tiszta,
immutábilis adatszerkezet — a QML-bekötés az integrátoré.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from picasapy.index.queries import PhotoRecord

_PATH_SEP = re.compile(r"[/\\]")


@dataclass(frozen=True)
class SearchGroup:
    folder_path: str
    folder_name: str
    first_row: int  # a csoport első képének sorindexe a lapos találat-listában
    earliest_taken_at: str | None
    photos: tuple[PhotoRecord, ...]


def group_by_folder(records: tuple[PhotoRecord, ...]) -> tuple[SearchGroup, ...]:
    """A (mappa szerint rendezett) találatok csoportosítása mappánként.

    A rekordok sorrendjét megőrizzük — a `search_photos` már mappa+név
    szerint rendez, így a csoportok is rendezettek."""
    groups: list[SearchGroup] = []
    current_path: str | None = None
    bucket: list[PhotoRecord] = []
    first_row = 0
    for row, record in enumerate(records):
        if record.folder_path != current_path:
            if bucket:
                groups.append(_make_group(current_path, first_row, bucket))
            current_path = record.folder_path
            bucket = []
            first_row = row
        bucket.append(record)
    if bucket:
        groups.append(_make_group(current_path, first_row, bucket))
    return tuple(groups)


def _make_group(
    folder_path: str, first_row: int, bucket: list[PhotoRecord]
) -> SearchGroup:
    dates = sorted(r.taken_at for r in bucket if r.taken_at)
    return SearchGroup(
        folder_path=folder_path,
        folder_name=_PATH_SEP.split(folder_path)[-1],
        first_row=first_row,
        earliest_taken_at=dates[0] if dates else None,
        photos=tuple(bucket),
    )
