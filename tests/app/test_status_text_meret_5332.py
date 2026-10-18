"""#5332: az állapotsor a Picasa bináris méretfokozatait használja."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from PySide6.QtCore import QLocale

from picasapy.app.formatting import status_text


@dataclass
class _Rekord:
    size: int
    taken_at: str | None = None
    keywords: str | None = None
    mtime_ns: int = 0
    sort_mtime_ns: int = 0
    name: str = "a.jpg"
    folder_path: str = "/kepek"


def _tr(text: str) -> str:
    return text


def _tr_n(text: str, _comment: str, count: int) -> str:
    return f"{count} pictures"


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (1023, "1023 bytes"),
        (1024, "1 KB"),
        (174 * 1024, "174 KB"),
        (1024**2 - 1, "1024 KB"),
        (1024**2, "1.0 MB"),
        (3 * 1024**2 // 2, "1,5 MB"),
        (1024**3, "1.0 GB"),
        (1024**4, "1.0 TB"),
    ],
)
def test_status_text_meret_a_picasa_binarias_fokozatait_kiirja(size, expected):
    locale = QLocale("hu_HU") if size == 3 * 1024**2 // 2 else QLocale("en_US")
    text = status_text(
        [_Rekord(size=size, taken_at="2026-01-02T12:00:00")],
        locale,
        _tr,
        _tr_n,
    )

    assert f"{expected} on disk" in text


def test_status_text_datum_nelkul_a_174_kb_alakot_irja():
    text = status_text(
        [_Rekord(size=174 * 1024, mtime_ns=10**26, sort_mtime_ns=10**26)],
        QLocale("en_US"),
        _tr,
        _tr_n,
    )

    assert "174 KB on disk" in text
