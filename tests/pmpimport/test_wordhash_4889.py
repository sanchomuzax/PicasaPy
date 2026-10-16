"""A Picasa kézi mappa- és albumsorrendjének átvétele a wordhashből."""

from __future__ import annotations

import re

import logging
import struct

import pytest

from picasapy.ini.document import parse_document
from picasapy.pmpimport import PathRemapper
from picasapy.pmpimport.db3_atvetel import rekordokat_atvesz
from support.pmp_factory import build_pmp_column, build_thumb_index

_FOLDER = r"C:\Users\felhasznalo\Pictures\PicasaTeszt"
_FOLDER_TOKEN = "]album:folder-token"
_ALBUM_ID = "604c294a68b0de9cc9222c4714f289d5"
_ALBUM_TOKEN = f"]album:{_ALBUM_ID}"
_INDEX_ENTRIES = 32

# A #4884 szerinti, három Colab-pillanatképből kiemelt postinglisták.
_B_ROWS = (2, 8, 10, 14, 15, 9, 17, 18, 20, 5, 19, 13, 11, 12, 16, 21, 22, 23, 24, 25, 3, 4, 6, 7)
_C_ROWS = (5, 2, 10, 14, 15, 9, 17, 18, 20, 19, 13, 11, 12, 16, 21, 22, 23, 24, 25, 3, 4, 8, 6, 7)


def _nev(local_path: str) -> str:
    """A fájlnév platformfüggetlenül (Windowson a rekord útja `\\`-t használ)."""
    return re.split(r"[\\/]", local_path)[-1]


def _wordhash_bytes(entries: tuple[tuple[str, tuple[int, ...]], ...]) -> bytes:
    """Kis kivonat a mért 1.6-os wordhash-formátummal és listákkal."""
    pool = bytearray(0x10000)
    offsets: dict[str, int] = {}
    used = 0
    for word, _rows in entries:
        encoded = word.encode("ascii") + b"\x00"
        offsets[word] = used
        pool[used : used + len(encoded)] = encoded
        used += len(encoded)

    # A mért 0x04/0x08 érték 36/1. A 0x04 jelentése nem ismert, és nem a
    # thumbindex 32 sorának darabszáma, ezért a beolvasó nem egyeztetheti őket.
    result = bytearray(struct.pack("<fIIII", 1.6, 36, 1, 0x10000, used))
    result.extend(pool)
    result.extend(struct.pack("<I", len(entries)))
    for word, rows in entries:
        result.extend(struct.pack("<II", offsets[word], len(rows)))
        result.extend(struct.pack(f"<{len(rows)}I", *rows))
    return bytes(result)


def _write_db3(tmp_path, wordhash_entries, *, nested_directory=False):
    db3 = tmp_path / "db3"
    db3.mkdir()
    local_folder = tmp_path / "photos"
    local_folder.mkdir()

    thumb_entries = [(_FOLDER, None), (r"D:\other", None)]
    for row in range(2, 26):
        if row == 5:
            name = "gray_ramp.jpg"
        elif row == 8:
            name = "rgb_gradient.jpg"
        else:
            name = f"photo-{row:02}.jpg"
        thumb_entries.append((name, 0))
        (local_folder / name).write_bytes(b"synthetic photo")
    for row in range(len(thumb_entries), _INDEX_ENTRIES):
        if nested_directory and row == 26:
            thumb_entries.append((f"{_FOLDER}\\Subdir", 0, 1, 1))
        else:
            thumb_entries.append(("", None))

    (db3 / "thumbindex.db").write_bytes(build_thumb_index(thumb_entries))
    (db3 / "imagedata_caption.pmp").write_bytes(
        build_pmp_column(0x0, [""] * _INDEX_ENTRIES)
    )
    (db3 / "albumdata_filename.pmp").write_bytes(
        build_pmp_column(0x0, [_FOLDER, "PicasaTeszt album"])
    )
    (db3 / "albumdata_token.pmp").write_bytes(
        build_pmp_column(0x0, [_FOLDER_TOKEN, _ALBUM_TOKEN])
    )
    (db3 / "albumdata_category.pmp").write_bytes(
        build_pmp_column(0x1, [2, 0])
    )
    (db3 / "wordhash.dat").write_bytes(_wordhash_bytes(tuple(wordhash_entries)))

    remapper = PathRemapper.from_dict({_FOLDER: str(local_folder)})
    return db3, local_folder, remapper


def _members_ini() -> str:
    sections = []
    for row in range(2, 26):
        name = (
            "gray_ramp.jpg"
            if row == 5
            else "rgb_gradient.jpg"
            if row == 8
            else f"photo-{row:02}.jpg"
        )
        sections.append(f"[{name}]\nalbums={_ALBUM_ID}\n")
    return "".join(sections)


def _document(path):
    return parse_document(path.read_text(encoding="utf-8"))


def test_wordhash_a_meres_24_elemu_listat_sorrendben_olvassa(tmp_path):
    from picasapy.pmpimport.wordhash import read_wordhash

    path = tmp_path / "wordhash.dat"
    path.write_bytes(_wordhash_bytes(((_FOLDER_TOKEN, _B_ROWS),)))

    assert read_wordhash(path) == {_FOLDER_TOKEN: _B_ROWS}


@pytest.mark.parametrize(
    ("rows", "photo_name", "place"),
    [
        (_B_ROWS, "gray_ramp.jpg", 9.0),  # B: a 10. hely
        (_C_ROWS, "rgb_gradient.jpg", 21.0),  # C: a 22. hely
    ],
)
def test_a_mappa_kezi_sorrendje_a_mert_wordhash_poziciot_orzi(
    tmp_path, rows, photo_name, place
):
    from picasapy.pmpimport.importer import beolvas_db3

    db3, local_folder, remapper = _write_db3(
        tmp_path, ((_FOLDER_TOKEN, rows),)
    )
    beolvasas = beolvas_db3(db3, remapper)
    records = {_nev(record.local_path): record for record in beolvasas.rekordok}

    assert beolvasas.wordhash_kihagyott == 0
    assert records[photo_name].manual_priority == place

    report = rekordokat_atvesz(beolvasas.rekordok, backup=False)

    section = _document(local_folder / ".picasa.ini").section(photo_name)
    assert float(section.get("priority")) == place
    assert report.sorrend == 24


def test_az_album_sorrendje_a_4599_albumorder_kulcsaba_kerul(tmp_path):
    from picasapy.pmpimport.importer import beolvas_db3

    db3, local_folder, remapper = _write_db3(
        tmp_path, ((_ALBUM_TOKEN, (8, 5, 2)),)
    )
    (local_folder / ".picasa.ini").write_text(_members_ini(), encoding="utf-8")
    beolvasas = beolvas_db3(db3, remapper)

    assert {
        name: places
        for record in beolvasas.rekordok
        for name, places in [(_nev(record.local_path), record.manual_album_places)]
        if places
    } == {
        "rgb_gradient.jpg": ((_ALBUM_ID, 1.0),),
        "gray_ramp.jpg": ((_ALBUM_ID, 2.0),),
        "photo-02.jpg": ((_ALBUM_ID, 3.0),),
    }

    report = rekordokat_atvesz(beolvasas.rekordok, backup=False)

    document = _document(local_folder / ".picasa.ini")
    assert document.section("rgb_gradient.jpg").get("albumorder") == f"{_ALBUM_ID}:1.0"
    assert document.section("gray_ramp.jpg").get("albumorder") == f"{_ALBUM_ID}:2.0"
    assert document.section("photo-02.jpg").get("albumorder") == f"{_ALBUM_ID}:3.0"
    assert report.sorrend == 3


def test_meglevo_mappa_sorrendet_nem_irja_felul(tmp_path):
    from picasapy.pmpimport.importer import beolvas_db3

    db3, local_folder, remapper = _write_db3(
        tmp_path, ((_FOLDER_TOKEN, _B_ROWS),)
    )
    ini_path = local_folder / ".picasa.ini"
    ini_path.write_text("[gray_ramp.jpg]\npriority=70.0\n", encoding="utf-8")

    report = rekordokat_atvesz(beolvas_db3(db3, remapper).rekordok, backup=False)

    document = _document(ini_path)
    assert document.section("gray_ramp.jpg").get("priority") == "70.0"
    assert all(
        section.get("priority") is None
        for section in document.file_sections()
        if section.name != "gray_ramp.jpg"
    )
    assert report.sorrend == 0


def test_meglevo_albumhely_az_egesz_album_atvetelet_megallitja(tmp_path):
    from picasapy.pmpimport.importer import beolvas_db3

    db3, local_folder, remapper = _write_db3(
        tmp_path, ((_ALBUM_TOKEN, (8, 5, 2)),)
    )
    ini_path = local_folder / ".picasa.ini"
    ini_path.write_text(
        _members_ini().replace(
            f"[gray_ramp.jpg]\nalbums={_ALBUM_ID}\n",
            f"[gray_ramp.jpg]\nalbums={_ALBUM_ID}\nalbumorder={_ALBUM_ID}:40.0\n",
        ),
        encoding="utf-8",
    )

    report = rekordokat_atvesz(beolvas_db3(db3, remapper).rekordok, backup=False)

    document = _document(ini_path)
    assert document.section("gray_ramp.jpg").get("albumorder") == f"{_ALBUM_ID}:40.0"
    assert document.section("rgb_gradient.jpg").get("albumorder") is None
    assert document.section("photo-02.jpg").get("albumorder") is None
    assert report.sorrend == 0


def test_ismeretlen_es_ismetelt_sorazonositot_kihagy_de_a_listat_atveszi(
    tmp_path,
):
    from picasapy.pmpimport.importer import beolvas_db3

    db3, local_folder, remapper = _write_db3(
        tmp_path, ((_FOLDER_TOKEN, (2, 99, 3, 2)),)
    )

    beolvasas = beolvas_db3(db3, remapper)
    records = {_nev(record.local_path): record for record in beolvasas.rekordok}

    assert beolvasas.wordhash_kihagyott == 2
    assert records["photo-02.jpg"].manual_priority == 0.0
    assert records["photo-03.jpg"].manual_priority == 1.0

    report = rekordokat_atvesz(beolvasas.rekordok, backup=False)

    document = _document(local_folder / ".picasa.ini")
    assert document.section("photo-02.jpg").get("priority") == "0.0"
    assert document.section("photo-03.jpg").get("priority") == "1.0"
    assert report.sorrend == 2


def test_a_mappalistaban_a_beagyazott_konyvtar_nem_kep(tmp_path):
    from picasapy.pmpimport.importer import beolvas_db3

    db3, _local_folder, remapper = _write_db3(
        tmp_path,
        ((_FOLDER_TOKEN, (2, 26, 3)),),
        nested_directory=True,
    )

    beolvasas = beolvas_db3(db3, remapper)
    records = {record.row: record for record in beolvasas.rekordok}

    assert beolvasas.wordhash_kihagyott == 1
    assert records[2].manual_priority == 0.0
    assert records[26].manual_priority is None
    assert records[3].manual_priority == 1.0


def test_csonka_wordhash_mellett_a_tobbi_adatot_beolvassa(tmp_path, caplog):
    from picasapy.pmpimport.importer import beolvas_db3

    db3, _local_folder, remapper = _write_db3(
        tmp_path, ((_FOLDER_TOKEN, _B_ROWS),)
    )
    path = db3 / "wordhash.dat"
    path.write_bytes(path.read_bytes()[:-1])

    with caplog.at_level(logging.WARNING):
        beolvasas = beolvas_db3(db3, remapper)

    assert len(beolvasas.rekordok) == 24
    assert all(record.manual_priority is None for record in beolvasas.rekordok)
    assert any("wordhash" in record.getMessage().casefold() for record in caplog.records)


def test_csonka_wordhashot_a_parser_format_hibakent_elutasitja(tmp_path):
    from picasapy.pmpimport.wordhash import WordHashFormatError, read_wordhash

    path = tmp_path / "wordhash.dat"
    path.write_bytes(_wordhash_bytes(((_FOLDER_TOKEN, _B_ROWS),))[:-1])

    with pytest.raises(WordHashFormatError):
        read_wordhash(path)
