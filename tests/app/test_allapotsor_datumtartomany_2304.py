"""#2304 (3. eltérés): az állapotsor dátumtartománya EXIF nélkül is legyen.

## A mérés

A tulajdonos képernyőmentésén a Picasa 3 az `AI` mappára
dátumtartományt ír az állapotsorba („2023. május 10., szerda–2025. május
21., szerda"), nálunk csak „81 kép   113,9 MB a lemezen" állt.

Az ok: a `formatting.status_text` **csak** a `taken_at`-et nézte
(`:417`), tartalék nélkül — csupa EXIF-nélküli mappánál a `dates` üres
maradt, és a dátum-rész kimaradt.

A tartalék nem új találmány: a rács rendezőkulcsa
(`app/photo_sort.photo_date`) és — a #2304 óta — a mappa dátuma is
pontosan a fájlidőre esik vissza. Ez a javítás az állapotsort hozza
szinkronba azzal, ami máshol már működik.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from PySide6.QtCore import QLocale

from picasapy.app.formatting import status_text


@dataclass(frozen=True)
class _Rekord:
    """A `status_text` csak ezt a három mezőt olvassa."""

    size: int
    mtime_ns: int
    taken_at: str | None = None


def _ido(ev: int, ho: int, nap: int) -> int:
    return int(time.mktime((ev, ho, nap, 12, 0, 0, 0, 0, -1)) * 1_000_000_000)


def _azonos_fordito(szoveg, _megjegyzes=None, _n=None):
    return szoveg


def test_exif_nelkul_is_van_datumtartomany() -> None:
    rekordok = [
        _Rekord(size=1024, mtime_ns=_ido(2023, 5, 10)),
        _Rekord(size=2048, mtime_ns=_ido(2025, 5, 21)),
    ]
    szoveg = status_text(rekordok, QLocale("hu_HU"), _azonos_fordito, _azonos_fordito)
    assert "2023" in szoveg and "2025" in szoveg, szoveg


def test_az_exif_datum_eroesebb_a_fajlidonel() -> None:
    rekordok = [
        _Rekord(size=1024, mtime_ns=_ido(2025, 5, 21), taken_at="2019-07-04T10:00:00"),
    ]
    szoveg = status_text(rekordok, QLocale("hu_HU"), _azonos_fordito, _azonos_fordito)
    assert "2019" in szoveg and "2025" not in szoveg, szoveg


def test_ures_kijelolesnel_valtozatlan() -> None:
    assert status_text([], QLocale("hu_HU"), _azonos_fordito, _azonos_fordito) == (
        "0 pictures"
    )
