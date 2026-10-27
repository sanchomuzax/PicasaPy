"""A Picasa 16 bites, OLE DATE-alapú backuphash képlete (#5810)."""
# rontás-kontroll: picasapy.ini.backuphash.backuphash_for_local_datetime = 65536 → 6 failed

from datetime import datetime

import pytest

from picasapy.ini.backuphash import backuphash_for_local_datetime
from picasapy.ini import parse_document
from picasapy.ini.backuphash import with_backuphash


@pytest.mark.parametrize(
    ("local_datetime", "expected"),
    [
        (datetime(1899, 12, 30, 0, 0, 0), 0),
        (datetime(1899, 12, 30, 12, 0, 0), 16352),
        (datetime(2024, 2, 29, 12, 34, 56), 63496),
        (datetime(2026, 10, 25, 12, 34, 56), 17128),
    ],
)
def test_backuphash_a_helyi_ole_date_negy_16_bites_szavanak_xorja(
    local_datetime, expected
):
    assert backuphash_for_local_datetime(local_datetime) == expected


def test_backuphash_a_tm_masodperc_pontossagat_hasznalja():
    assert backuphash_for_local_datetime(
        datetime(2026, 10, 25, 12, 34, 56, 999999)
    ) == 17128


def test_backuphash_az_ini_szakaszban_megoriz_minden_mas_kulcsot():
    document = parse_document(
        "[A.JPG]\r\ncaption=felirat\r\nbackuphash=12\r\nuntouched=keep\r\n"
    )

    updated = with_backuphash(
        document, "a.jpg", datetime(2024, 2, 29, 12, 34, 56)
    )

    section = updated.section("A.JPG")
    assert section is not None
    assert section.items() == (
        ("caption", "felirat"),
        ("backuphash", "63496"),
        ("untouched", "keep"),
    )
