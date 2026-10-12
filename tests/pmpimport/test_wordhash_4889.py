"""A Picasa mappák kézi sorrendjének átvétele a wordhash.dat-ból (#4889)."""

from __future__ import annotations

import logging
import struct

import pytest

from picasapy.pmpimport import PathRemapper, iter_photo_records
from picasapy.pmpimport.db3_atvetel import rekordokat_atvesz
from support.pmp_factory import build_pmp_column, build_thumb_index

_FOLDER_TOKEN = "]album:folder-token"
_ALBUM_TOKEN = "]album:604c294a68b0de9cc9222c4714f289d5"
_ALBUM_ID = "604c294a68b0de9cc9222c4714f289d5"
_FOLDER = r"C:\Users\felhasznalo\Pictures"


def _wordhash_bytes(entity_count: int, entries: tuple[tuple[str, tuple[int, ...]], ...]) -> bytes:
    """A #4884 spec szerinti kis, egy poolos, little-endian fájl."""
    pool = bytearray(0x10000)
    offsets: dict[str, int] = {}
    used = 0
    for word, _rows in entries:
        encoded = word.encode("utf-8") + b"\x00"
        offsets[word] = used
        pool[used : used + len(encoded)] = encoded
        used += len(encoded)

    blob = bytearray(
        struct.pack("<fIIII", 1.6, entity_count, 1, 0x10000, used)
    )
    blob.extend(pool)
    blob.extend(struct.pack("<I", len(entries)))
    for word, rows in entries:
        blob.extend(struct.pack("<II", offsets[word], len(rows)))
        blob.extend(struct.pack(f"<{len(rows)}I", *rows))
    return bytes(blob)


def _db3(tmp_path, *, wordhash: bytes | None = None):
    (tmp_path / "thumbindex.db").write_bytes(
        build_thumb_index(
            [
                (_FOLDER + "\\", None),  # 0: mappa
                ("a.jpg", 0),              # 1: fájl
                ("b.jpg", 0),              # 2: fájl
                ("c.jpg", 0),              # 3: fájl
                ("", 0),                   # 4: arcrekord, nem fájl
                ("", None),                # 5: törölt rekord, nem fájl
                ("other.jpg", None),       # 6: másik gyökér, nincs remap
            ]
        )
    )
    (tmp_path / "imagedata_caption.pmp").write_bytes(
        build_pmp_column(0x0, [""] * 7)
    )
    (tmp_path / "albumdata_filename.pmp").write_bytes(
        build_pmp_column(0x0, [_FOLDER, _FOLDER + "\\album", ""])
    )
    # A harmadik albumdata sor üres tokenje nem indít importot.
    (tmp_path / "albumdata_token.pmp").write_bytes(
        build_pmp_column(0x0, [_FOLDER_TOKEN, _ALBUM_TOKEN, ""])
    )
    (tmp_path / "albumdata_category.pmp").write_bytes(
        build_pmp_column(0x1, [2, 0, 0])
    )
    if wordhash is not None:
        (tmp_path / "wordhash.dat").write_bytes(wordhash)


@pytest.fixture
def remapper(tmp_path):
    local_folder = tmp_path / "photos"
    local_folder.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        (local_folder / name).write_bytes(b"synthetic photo")
    (local_folder / ".picasa.ini").write_text(
        "[a.jpg]\nalbums=" + _ALBUM_ID + "\n"
        "[b.jpg]\nalbums=" + _ALBUM_ID + "\n"
        "[c.jpg]\nalbums=" + _ALBUM_ID + "\n",
        encoding="utf-8",
    )
    return PathRemapper.from_dict({_FOLDER: str(local_folder)})


def _rendezett_db3(tmp_path):
    _db3(
        tmp_path,
        wordhash=_wordhash_bytes(
            7,
            (
                (_FOLDER_TOKEN, (2, 1, 4, 3, 99)),
                # Album és mappa együtt; az album-lista nem növekvő.
                (_ALBUM_TOKEN, (3, 1, 2, 4, 99, 2)),
            ),
        ),
    )


def _priority_ini(path):
    values = {}
    for section in path.read_text(encoding="utf-8").split("[")[1:]:
        name, _, body = section.partition("]")
        for line in body.splitlines():
            if line.startswith("priority="):
                values[name] = line.partition("=")[2]
    return values


def test_a_wordhash_az_entitasok_sorrendjet_orizve_olvassa(tmp_path):
    from picasapy.pmpimport.wordhash import read_wordhash

    path = tmp_path / "wordhash.dat"
    path.write_bytes(_wordhash_bytes(7, ((_FOLDER_TOKEN, (2, 1, 3)),)))

    assert read_wordhash(path, expected_entity_count=7) == {
        _FOLDER_TOKEN: (2, 1, 3)
    }


def test_a_mappalista_thumbindex_utvonalakbol_priority_sorrendet_ad(
    tmp_path, remapper, caplog
):
    _rendezett_db3(tmp_path)
    with caplog.at_level(logging.WARNING):
        records = iter_photo_records(tmp_path, remapper)

    priorities = {
        record.local_path.rsplit("/", 1)[-1]: record.manual_priority
        for record in records
    }
    assert priorities == {"a.jpg": 1.0, "b.jpg": 0.0, "c.jpg": 2.0}
    assert any("kihagyott" in record.getMessage().casefold() for record in caplog.records)

    report = rekordokat_atvesz(records, backup=False)
    assert report.sorrend == 3
    assert _priority_ini(tmp_path / "photos" / ".picasa.ini") == {
        "b.jpg": "0.0",
        "a.jpg": "1.0",
        "c.jpg": "2.0",
    }


def test_az_albumlista_albumorder_helyeket_vesz_at_es_szamolja_a_kihagyottakat(
    tmp_path, remapper
):
    from picasapy.ini.document import parse_document
    from picasapy.pmpimport.importer import beolvas_db3

    _rendezett_db3(tmp_path)
    beolvasas = beolvas_db3(tmp_path, remapper)
    report = rekordokat_atvesz(beolvasas.rekordok, backup=False)

    document = parse_document(
        (tmp_path / "photos" / ".picasa.ini").read_text(encoding="utf-8")
    )
    assert {
        name: document.section(name).get("albumorder")
        for name in ("a.jpg", "b.jpg", "c.jpg")
    } == {
        "a.jpg": f"{_ALBUM_ID}:2.0",
        "b.jpg": f"{_ALBUM_ID}:3.0",
        "c.jpg": f"{_ALBUM_ID}:1.0",
    }
    assert beolvasas.wordhash_kihagyott == 5
    assert report.sorrend == 3


def test_egy_meglevo_albumhely_minden_tagon_megakadalyozza_az_atvetelt(
    tmp_path, remapper
):
    from picasapy.ini.document import parse_document
    from picasapy.pmpimport.importer import beolvas_db3

    _rendezett_db3(tmp_path)
    ini_path = tmp_path / "photos" / ".picasa.ini"
    ini_path.write_text(
        f"[a.jpg]\nalbums={_ALBUM_ID}\nalbumorder={_ALBUM_ID}:40.0\n"
        f"[b.jpg]\nalbums={_ALBUM_ID}\n"
        f"[c.jpg]\nalbums={_ALBUM_ID}\n",
        encoding="utf-8",
    )

    beolvasas = beolvas_db3(tmp_path, remapper)
    assert beolvasas.rekordok[0].manual_album_places == ((_ALBUM_ID, 2.0),)
    assert beolvasas.rekordok[1].manual_album_places == ((_ALBUM_ID, 3.0),)
    assert beolvasas.rekordok[2].manual_album_places == ((_ALBUM_ID, 1.0),)
    rekordokat_atvesz(beolvasas.rekordok, backup=False)

    document = parse_document(ini_path.read_text(encoding="utf-8"))
    assert document.section("a.jpg").get("albumorder") == f"{_ALBUM_ID}:40.0"
    assert document.section("b.jpg").get("albumorder") is None
    assert document.section("c.jpg").get("albumorder") is None


def test_a_meglevo_mappasorrendet_teljesen_erintetlenul_hagyja(
    tmp_path, remapper
):
    _rendezett_db3(tmp_path)
    records = iter_photo_records(tmp_path, remapper)
    ini_path = tmp_path / "photos" / ".picasa.ini"
    ini_path.write_text(
        "[a.jpg]\npriority=40.0\n[b.jpg]\npriority=20.0\n", encoding="utf-8"
    )

    report = rekordokat_atvesz(records, backup=False)

    assert report.sorrend == 0
    assert _priority_ini(ini_path) == {"a.jpg": "40.0", "b.jpg": "20.0"}


def test_hibas_wordhash_nem_allitja_le_az_importot_es_naplozza(
    tmp_path, remapper, caplog
):
    _db3(tmp_path, wordhash=b"\xcd\xcc\xcc\x3f\x07\x00")

    with caplog.at_level(logging.WARNING):
        records = iter_photo_records(tmp_path, remapper)

    assert [record.local_path.rsplit("/", 1)[-1] for record in records] == [
        "a.jpg",
        "b.jpg",
        "c.jpg",
    ]
    assert all(record.manual_priority is None for record in records)
    assert any("wordhash" in record.getMessage().casefold() for record in caplog.records)


def test_csonka_wordhash_fajlt_format_hibakent_elutasitja(tmp_path):
    from picasapy.pmpimport.wordhash import WordHashFormatError, read_wordhash

    path = tmp_path / "wordhash.dat"
    path.write_bytes(_wordhash_bytes(7, ((_FOLDER_TOKEN, (2, 1)),))[:-1])

    with pytest.raises(WordHashFormatError):
        read_wordhash(path, expected_entity_count=7)


def test_a_beolvasas_megszamolja_a_wordhash_kihagyott_elemeit(tmp_path, remapper):
    from picasapy.pmpimport.importer import beolvas_db3

    _rendezett_db3(tmp_path)

    beolvasas = beolvas_db3(tmp_path, remapper)

    # Mappa: 4 és 99; album: 4, 99 és a duplikált 2 — összesen öt.
    assert beolvasas.wordhash_kihagyott == 5
    assert len(beolvasas.rekordok) == 3


def test_a_jelentes_osszeadodik_a_wordhash_kihagyott_szamlalojaval():
    from picasapy.pmpimport.db3_atvetel import AtvetelJelentes

    osszes = AtvetelJelentes(wordhash_kihagyott=2) + AtvetelJelentes(
        wordhash_kihagyott=1, kihagyott=4
    )

    assert osszes.wordhash_kihagyott == 3
    assert osszes.kihagyott == 4
