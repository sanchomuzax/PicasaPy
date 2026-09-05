"""#2304 (1. eltérés): a rács mappa-fejlécében EXIF nélkül is legyen dátum.

## A mérés — a tulajdonos VALÓDI `AI` mappáján (2026-09-05)

A mappa 82 médiafájlt tartalmaz (62 png · 18 jpg · 1 webp · 1 mp4), és
**egyetlen** fájlban sincs EXIF felvételi idő. A mérés a PRODUKCIÓS
olvasóval (`metadata/reader.py`, Pillow `getexif()`) készült, mind a 82
fájlra: 82 beolvasás, **0** `taken_at`. (A korábbi indoklás — „a png-k
eleve nem hordoznak EXIF-et" — HIBÁS volt: a PNG 2017 óta hordozhat
`eXIf` chunkot, és a `getexif()` ki is olvassa; a `_getexif()` a
JPEG-only örökölt API. A KÖVETKEZTETÉS a méréssel változatlanul áll.)
A Picasa 3 a mappa fejlécébe mégis dátumot ír („AI — 2023. november 14.,
kedd"), nálunk a fejléc dátum nélkül maradt.

Az ok: a `formatting.first_date_text` **csak** a `taken_at`-et nézte,
tartalék nélkül — csupa EXIF-nélküli mappánál a lista üres maradt, és a
`build_feed_groups` üres `dateText`-et adott.

A tartalék nem új találmány, hanem a három testvér-hely negyedike: a rács
rendezőkulcsa (`app/photo_sort.photo_date`), a mappa indexelt dátuma
(`index/sync._sync_folder_date`) és az állapotsor dátumtartománya
(`formatting.status_text`) a #2304 óta MIND a fájlidőre esik vissza. A
fejléc kimaradt közülük.

## A tartalék hatóköre — „mindent vagy semmit"

A `formatting.photo_dates` csak akkor esik vissza fájlidőre, ha a
halmazban EGYETLEN felvételi idő sincs. Ez szűkebb, mint a rekordonkénti
visszaesés, és szándékosan: a mérés csak a csupa EXIF-nélküli mappát
fedi, rekordonkénti tartalék mellett pedig egyetlen romlott vagy régi
`mtime`-ú fájl egy EXIF-fel bíró mappa fejlécét is évekkel korábbra
húzná (a `min` csak korábbra mozdulhat). A vegyes mappát külön eset
méri.

## Amit ez az őr NEM állít

Nem állítja, hogy a fejlécben ugyanaz a NAP áll, mint az eredetiben. Az
eredeti a mappa saját, TÁROLT dátumát mutatja (`albumdata_date.pmp`, a
mappa felvételekor befagyasztva: az `AI`-nál 2023-11-14 17:29:11), mi a
mappa legkorábbi képének idejét — a mért legkorábbi fájlidő 2023-05-10.
Az ÉV mindkettőnél 2023; a nap eltérése a #2304-en nyitott kérdés.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import pytest
from PySide6.QtCore import QLocale

from picasapy.app.formatting import build_feed_groups, first_date_text, photo_dates
from picasapy.app.photo_sort import photo_date


@dataclass(frozen=True)
class _Rekord:
    """A `first_date_text` / `build_feed_groups` által olvasott mezők."""

    folder_path: str
    name: str
    mtime_ns: int
    taken_at: str | None = None


def _ido(ev: int, ho: int, nap: int) -> int:
    return int(time.mktime((ev, ho, nap, 12, 0, 0, 0, 0, -1)) * 1_000_000_000)


def test_exif_nelkul_is_van_fejlecdatum() -> None:
    rekordok = [
        _Rekord("/foto/AI", "_d0ccc81b.jpg", _ido(2023, 11, 14)),
        _Rekord("/foto/AI", "DALL-E.png", _ido(2025, 5, 21)),
    ]
    szoveg = first_date_text(rekordok, QLocale("hu_HU"))
    assert "2023" in szoveg, f"a fejléc dátum nélkül maradt: {szoveg!r}"


def test_a_feedcsoport_datuma_is_megjelenik() -> None:
    """A tényleges fogyasztó a `build_feed_groups` `dateText` mezője."""
    rekordok = [
        _Rekord("/foto/AI", "_d0ccc81b.jpg", _ido(2023, 11, 14)),
        _Rekord("/foto/AI", "DALL-E.png", _ido(2025, 5, 21)),
    ]
    (csoport,) = build_feed_groups(rekordok, QLocale("hu_HU"))
    assert csoport["name"] == "AI"
    assert "2023" in csoport["dateText"], csoport["dateText"]


def test_az_exif_datum_eroesebb_a_fajlidonel() -> None:
    """A tartalék NEM veheti át a helyet ott, ahol van EXIF."""
    rekordok = [
        _Rekord("/foto/Nyaralas", "IMG_1.jpg", _ido(2025, 5, 21),
                taken_at="2019-07-04T10:00:00"),
    ]
    szoveg = first_date_text(rekordok, QLocale("hu_HU"))
    assert "2019" in szoveg and "2025" not in szoveg, szoveg


def test_vegyes_mappaban_az_exif_dont_a_fajlido_nem_huzhat_korabbra() -> None:
    """#2304 (3. lelet): egy régi fájlidejű, EXIF NÉLKÜLI kép nem húzhatja
    korábbra egy EXIF-fel bíró mappa fejlécét.

    A tartalék „mindent vagy semmit": ha a halmazban van akár egyetlen
    felvételi idő, kizárólag a felvételi idők számítanak.
    """
    rekordok = [
        _Rekord("/foto/Nyaralas", "IMG_1.jpg", _ido(2025, 5, 21),
                taken_at="2019-07-04T10:00:00"),
        # rossz órájú fényképezőgépről átmásolt, EXIF nélküli fájl
        _Rekord("/foto/Nyaralas", "scan.png", _ido(1998, 1, 2)),
    ]
    szoveg = first_date_text(rekordok, QLocale("hu_HU"))
    assert "2019" in szoveg, szoveg
    assert "1998" not in szoveg, szoveg


def test_romlott_fajlido_nem_viszi_ki_a_fejlecepitest() -> None:
    """#2304 (4. lelet): a `photo_date` DOBHAT — a fejléc ne szálljon el.

    Mérve: `mtime_ns = 10**26` → `OSError: [Errno 75] Value too large for
    defined data type` a `datetime.fromtimestamp`-ből. A fejléc-építés a
    rács `_show`-jának közepén fut, tehát egyetlen romlott indexsor
    kivitte volna az EGÉSZ rácsot.
    """
    romlott = _Rekord("/foto/AI", "romlott.jpg", 10**26)
    # 1) a nyers `photo_date` tényleg dob — a tartalék nem elméleti
    with pytest.raises((OSError, ValueError, OverflowError)):
        photo_date(romlott)
    # 2) a fejléc mégis felépül, a jó rekord dátumával
    rekordok = [romlott, _Rekord("/foto/AI", "jo.png", _ido(2023, 11, 14))]
    assert "2023" in first_date_text(rekordok, QLocale("hu_HU"))
    (csoport,) = build_feed_groups(rekordok, QLocale("hu_HU"))
    assert "2023" in csoport["dateText"], csoport["dateText"]


def test_csupa_romlott_fajlidonel_ures_a_fejlec_de_nincs_kivetel() -> None:
    """Ha EGYETLEN dátum sem nyerhető ki, a fejléc üres — de nem dob."""
    rekordok = [_Rekord("/foto/AI", "romlott.jpg", 10**26)]
    assert photo_dates(rekordok) == []
    assert first_date_text(rekordok, QLocale("hu_HU")) == ""
