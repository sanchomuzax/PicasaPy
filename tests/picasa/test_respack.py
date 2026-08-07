"""A `tools/picasa/respack.py` kicsomagoló egységtesztjei.

A valódi `respack.yt` (a Picasa-telepítésből) a fejlesztői gépen él és
szerzői jogvédett — ezért itt **szintetikus** csomagot építünk pontosan a
`docs/specs/picasa-respack-format.md`-ben rögzített szabályok szerint, és
azon ellenőrizzük az indexolvasást, a tömör/RLE dekódolást, a `.tre`
szövegkinyerést és a hibakezelést.
"""

from __future__ import annotations

import importlib.util
import struct
import sys
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "tools" / "picasa" / "respack.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("respack_tool", _MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["respack_tool"] = module
    spec.loader.exec_module(module)
    return module


respack = _load_module()


def _header(x0: int, y0: int, x1: int, y1: int, encoding: int) -> bytes:
    return struct.pack("<4hBBHB", x0, y0, x1, y1, 0, 1, 0, encoding)


def _build_pack(records: list[tuple[str, bytes]]) -> bytes:
    """Szintetikus respack: 4 bájt indexeltolás, adatblokkok, majd névindex."""
    body = bytearray(b"\0\0\0\0")
    offsets: list[tuple[str, int]] = []
    for name, blob in records:
        offsets.append((name, len(body)))
        body += blob
    index_off = len(body)
    body += struct.pack("<I", len(offsets))
    for name, off in offsets:
        body += name.encode("latin1") + b"\0" + struct.pack("<I", off)
    struct.pack_into("<I", body, 0, index_off)
    return bytes(body)


SOLID = _header(0, 0, 2, 2, respack.ENC_SOLID) + bytes([1, 2, 3, 255])
# 3x2 kép: első sor 3× piros, második sor 1× zöld + 2× kék
RLE = (
    _header(0, 0, 3, 2, respack.ENC_RLE)
    + bytes([3, 255, 0, 0, 255])
    + bytes([1, 0, 255, 0, 255])
    + bytes([2, 0, 0, 255, 255])
)
TRE = b"root/child: root\nProperty hidden 1\n"


@pytest.fixture()
def pack() -> bytes:
    return _build_pack(
        [
            ("layer:demo/solid", SOLID),
            ("layer:demo/rle", RLE),
            ("tre:demo", TRE),
        ]
    )


class TestIndex:
    def test_minden_bejegyzest_megtalal(self, pack: bytes) -> None:
        entries = respack.read_index(pack)
        assert [e.name for e in entries] == [
            "layer:demo/solid",
            "layer:demo/rle",
            "tre:demo",
        ]

    def test_a_rekordhatart_a_kovetkezo_offset_adja(self, pack: bytes) -> None:
        entries = respack.read_index(pack)
        assert entries[0].end == entries[1].offset
        assert entries[-1].end - entries[-1].offset == len(TRE)

    def test_tre_felismerese(self, pack: bytes) -> None:
        entries = respack.read_index(pack)
        assert [e.is_tre for e in entries] == [False, False, True]

    def test_ures_fajl_hibat_dob(self) -> None:
        with pytest.raises(respack.RespackError):
            respack.read_index(b"\x00\x00")

    def test_ervenytelen_indexeltolas_hibat_dob(self) -> None:
        with pytest.raises(respack.RespackError):
            respack.read_index(struct.pack("<I", 10**9) + b"\0" * 32)


class TestDekodolas:
    def test_tomor_kitoltes_kifejtese(self, pack: bytes) -> None:
        entry = respack.read_index(pack)[0]
        layer = respack.decode_layer(pack, entry)
        assert (layer.width, layer.height) == (2, 2)
        assert layer.pixels == bytes([1, 2, 3, 255]) * 4

    def test_rle_soronkent_fejt_ki(self, pack: bytes) -> None:
        entry = respack.read_index(pack)[1]
        layer = respack.decode_layer(pack, entry)
        assert (layer.width, layer.height) == (3, 2)
        assert layer.pixels[:12] == bytes([255, 0, 0, 255]) * 3
        assert layer.pixels[12:16] == bytes([0, 255, 0, 255])
        assert layer.pixels[16:] == bytes([0, 0, 255, 255]) * 2

    def test_negativ_koordinata_elojeles(self) -> None:
        """A határoló doboz `int16` — a negatív origó nem torzulhat."""
        blob = _header(-2, -2, 0, 0, respack.ENC_SOLID) + bytes([9, 9, 9, 255])
        data = _build_pack([("layer:d/neg", blob)])
        layer = respack.decode_layer(data, respack.read_index(data)[0])
        assert (layer.x0, layer.y0) == (-2, -2)
        assert (layer.width, layer.height) == (2, 2)

    def test_rossz_rle_hossz_hibat_dob(self) -> None:
        blob = _header(0, 0, 4, 4, respack.ENC_RLE) + bytes([1, 0, 0, 0, 255])
        data = _build_pack([("layer:d/bad", blob)])
        with pytest.raises(respack.RespackError, match="hossz"):
            respack.decode_layer(data, respack.read_index(data)[0])

    def test_ures_reteg_atlatszo(self) -> None:
        """A `0` kódolás csak fejléc — átlátszó rétegként kell kifejteni."""
        data = _build_pack([("layer:d/empty", _header(0, 0, 2, 1, respack.ENC_EMPTY))])
        layer = respack.decode_layer(data, respack.read_index(data)[0])
        assert layer.pixels == b"\0\0\0\0" * 2

    def test_ismeretlen_kodolas_hibat_dob(self) -> None:
        blob = _header(0, 0, 1, 1, 7) + bytes([0, 0, 0, 0])
        data = _build_pack([("layer:d/x", blob)])
        with pytest.raises(respack.RespackError, match="kódolás"):
            respack.decode_layer(data, respack.read_index(data)[0])

    def test_tre_bejegyzest_nem_dekodol_retegkent(self, pack: bytes) -> None:
        tre_entry = respack.read_index(pack)[2]
        with pytest.raises(respack.RespackError):
            respack.decode_layer(pack, tre_entry)


class TestVisszakodolas:
    """Round-trip: a dekódolt rétegből vissza kell kapnunk az eredeti bájtokat.

    Ez a formátum-értés legerősebb próbája — a valódi csomagon ez mutatta ki,
    hogy az RLE-futamok NEM sorhatárra igazítottak.
    """

    def test_rle_bajtra_azonos(self, pack: bytes) -> None:
        entry = respack.read_index(pack)[1]
        layer = respack.decode_layer(pack, entry)
        assert respack.encode_layer(layer) == RLE[respack.HEADER_SIZE :]

    def test_tomor_kitoltes_bajtra_azonos(self, pack: bytes) -> None:
        entry = respack.read_index(pack)[0]
        layer = respack.decode_layer(pack, entry)
        assert respack.encode_layer(layer) == SOLID[respack.HEADER_SIZE :]

    def test_futam_atlog_a_sorhataron(self) -> None:
        """Egyszínű 3x2-es kép: EGYETLEN 6-os futam, nem két 3-as."""
        blob = _header(0, 0, 3, 2, respack.ENC_RLE) + bytes([6, 1, 2, 3, 255])
        data = _build_pack([("layer:d/flat", blob)])
        layer = respack.decode_layer(data, respack.read_index(data)[0])
        assert respack.encode_layer(layer) == bytes([6, 1, 2, 3, 255])

    def test_255_folotti_futam_kettevagva(self) -> None:
        """A darabszám uint8 — 300 azonos képpont két futamra bomlik."""
        blob = _header(0, 0, 300, 1, respack.ENC_RLE) + bytes(
            [255, 9, 9, 9, 255]
        ) + bytes([45, 9, 9, 9, 255])
        data = _build_pack([("layer:d/long", blob)])
        layer = respack.decode_layer(data, respack.read_index(data)[0])
        assert respack.encode_layer(layer) == blob[respack.HEADER_SIZE :]


class TestSzoveg:
    def test_tre_szoveg_kinyerese(self, pack: bytes) -> None:
        entry = respack.read_index(pack)[2]
        assert respack.extract_tre(pack, entry) == TRE.decode("latin1")

    def test_tre_parancs_fajlba_ir(self, pack: bytes, tmp_path: Path) -> None:
        src = tmp_path / "respack.yt"
        src.write_bytes(pack)
        out = tmp_path / "tre"
        assert respack.main(["tre", str(src), str(out)]) == 0
        assert (out / "demo.tre").read_text(encoding="latin1") == TRE.decode("latin1")
