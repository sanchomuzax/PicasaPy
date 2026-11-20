"""#7292: az `update_document(touch=False)` a képfájlhoz nem nyúl.

A mentés-készlet bélyege tiszta könyvelés: az `.ini`-be kerül, a képfájl
mtime-ja viszont az inkrementális mentés döntésének része, ezért a bélyegző
írás nem érintheti meg. Szerkesztésnél (alapérték) az érintés marad
(`tests/ini/test_photo_touch_643.py`).
"""

from __future__ import annotations

import os

import pytest

from picasapy.ini import load_document, update_document
from picasapy.ini.photo_touch import TOUCH_ENV_VAR

_OLD_NS = 1_577_836_800_000_000_000


@pytest.fixture
def mappa(tmp_path, monkeypatch):
    monkeypatch.delenv(TOUCH_ENV_VAR, raising=False)  # az alapérték: BE
    (tmp_path / "kep.jpg").write_bytes(b"\xff\xd8\xffkep\xff\xd9")
    (tmp_path / ".picasa.ini").write_text("[kep.jpg]\nstar=yes\n", encoding="utf-8")
    os.utime(tmp_path / "kep.jpg", ns=(_OLD_NS, _OLD_NS))
    return tmp_path


def _ir(mappa, **kwargs) -> None:
    update_document(
        mappa / ".picasa.ini",
        lambda d: d.with_value("kep.jpg", "backuphash", "100"),
        backup=False,
        **kwargs,
    )


def test_touch_nelkul_a_kep_mtime_ja_valtozatlan(mappa):
    _ir(mappa, touch=False)
    assert (mappa / "kep.jpg").stat().st_mtime_ns == _OLD_NS


def test_touch_nelkul_az_ini_irasa_megtortenik(mappa):
    _ir(mappa, touch=False)
    szakasz = load_document(mappa / ".picasa.ini").section("kep.jpg")
    assert szakasz.get("backuphash") == "100"
    assert szakasz.get("star") == "yes"


def test_az_alapertek_tovabbra_is_megerinti_a_kepet(mappa):
    """A szerkesztő-útvonalak viselkedése NEM változik."""
    _ir(mappa)
    assert (mappa / "kep.jpg").stat().st_mtime_ns > _OLD_NS
