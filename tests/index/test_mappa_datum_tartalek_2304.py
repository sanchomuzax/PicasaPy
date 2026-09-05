"""#2304: a mappa dátumának legyen tartaléka, ha egyetlen képen sincs EXIF.

## A mérés, amiből ez jön

A tulajdonos `AI` mappája (DALL·E-kimenetek, EXIF felvételi idő nélkül)
a Picasa 3-ban dátumos fejlécet és a 2023-as évcsoportot kapja, nálunk
dátum nélkül maradt és az ELŐZŐ év fejléce alá csúszott.

Az ok mérve: `index/sync.py` a mappa dátumát `MIN(p.taken_at)`-ból
számolja, a `metadata/reader.py:_taken_at` pedig EXIF hiányában `None`-t
ad — tartalék nélkül.

## Miért a fájlidő a tartalék

Nem új találmány: a `photos` táblában MEGVAN a `mtime_ns`
(`index/schema.py:259`), és a rács rendezőkulcsa
(`app/photo_sort.photo_date`) MÁR MA IS pontosan erre esik vissza. Ez a
javítás az indexet hozza szinkronba azzal, ami a rácsban már működik.

## Amit ez az őr NEM állít

Nem állítja, hogy az EREDETI is a módosítási időt használja. A Picasánál
a létrehozási idő is szóba jön; a kettő szétválasztásához olyan minta
kell, ahol a két fájlidő KÜLÖNBÖZIK — az a #2304-en nyitva marad.
Ez az őr csak azt köti ki, hogy a mappa NE maradjon dátumtalan, ha a
fájlokból egyáltalán kiolvasható idő.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


def _mappa_datum(conn, ut: Path) -> str | None:
    sor = conn.execute(
        "SELECT date FROM folders WHERE path = ?", (str(ut),)
    ).fetchone()
    return sor["date"] if sor else None


@pytest.fixture
def exif_nelkuli_mappa(tmp_path: Path) -> Path:
    gyoker = tmp_path / "AI"
    gyoker.mkdir()
    for nev in ("_d0ccc81b.jpg", "DALL-E 2023-11-14.jpg"):
        kep = gyoker / nev
        make_jpeg(kep)          # a gyár nem ír EXIF felvételi időt
        ido = time.mktime((2023, 11, 14, 17, 49, 15, 0, 0, -1))
        os.utime(kep, (ido, ido))
    return gyoker


def test_a_mappa_datuma_a_fajlidobol_jon_exif_nelkul(
    tmp_path: Path, exif_nelkuli_mappa: Path
) -> None:
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, exif_nelkuli_mappa)
        datum = _mappa_datum(conn, exif_nelkuli_mappa)
    assert datum is not None, "a mappa dátum nélkül maradt"
    assert datum.startswith("2023-11-14"), datum


def test_az_exif_datum_tovabbra_is_eroesebb(tmp_path: Path) -> None:
    """A tartalék NEM veheti át a helyet ott, ahol van EXIF."""
    gyoker = tmp_path / "Nyaralas"
    gyoker.mkdir()
    kep = gyoker / "IMG_1.jpg"
    make_jpeg(kep, taken_at="2019:07:04 10:00:00")
    ido = time.mktime((2023, 11, 14, 17, 49, 15, 0, 0, -1))
    os.utime(kep, (ido, ido))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, gyoker)
        datum = _mappa_datum(conn, gyoker)
    assert datum is not None and datum.startswith("2019-07-04"), datum
