"""#4597 — a „Rejtett mappák" jelszó-lenyomatának átvétele a db3 `catdata`
táblájából (`catdata_name.pmp` + `catdata_info.pmp`).

A mintafájlt a próba maga építi (a `catdata_info.pmp` valódi mintán nem
látott): a fejléc a `pmp_column` olvasóéval egyező, a rekordok NUL-lezárt
UTF-8 sztringek.
"""

from __future__ import annotations

import struct
from pathlib import Path

from picasapy.pmpimport.pmp_column import _CONST_1332, _CONST_2, _MAGIC
from picasapy.pmpimport.rejtett_jelszo import read_hidden_password_hash

_MD5 = "5f4dcc3b5aa765d61d8327deb882cf99"


def _pmp(ut: Path, ertekek: list[str]) -> None:
    fejlec = struct.pack(
        "<IHHIHHI", _MAGIC, 0, _CONST_1332, _CONST_2, 0, _CONST_1332, len(ertekek)
    )
    ut.write_bytes(fejlec + b"".join(e.encode() + b"\x00" for e in ertekek))


_NEVEK = ["Labels", "Folders on Disk", "Hidden Folders", "People"]


def test_a_hidden_folders_sor_info_erteke_a_lenyomat(tmp_path):
    _pmp(tmp_path / "catdata_name.pmp", _NEVEK)
    _pmp(tmp_path / "catdata_info.pmp", ["", "", _MD5.upper(), ""])
    assert read_hidden_password_hash(tmp_path) == _MD5


def test_hianyzo_info_fajl_csendben_nincs_jelszo(tmp_path):
    _pmp(tmp_path / "catdata_name.pmp", _NEVEK)
    assert read_hidden_password_hash(tmp_path) is None


def test_ures_info_nincs_jelszo(tmp_path):
    _pmp(tmp_path / "catdata_name.pmp", _NEVEK)
    _pmp(tmp_path / "catdata_info.pmp", ["", "", "", ""])
    assert read_hidden_password_hash(tmp_path) is None


def test_nem_md5_ertek_nem_jelszo(tmp_path):
    _pmp(tmp_path / "catdata_name.pmp", _NEVEK)
    _pmp(tmp_path / "catdata_info.pmp", ["", "", "nem-hex", ""])
    assert read_hidden_password_hash(tmp_path) is None


def test_sérult_fajl_csendben_nincs_jelszo(tmp_path):
    _pmp(tmp_path / "catdata_name.pmp", _NEVEK)
    (tmp_path / "catdata_info.pmp").write_bytes(b"torott")
    assert read_hidden_password_hash(tmp_path) is None
