"""A #3989 „Kész, ha” 4. pontja: a projekt exportjának Interop IFD-je a valódi,
MÉRT Picasa-exporttal összevetve (`3229-lanc-sorrend` mérőkészlet).

FIGYELEM: a mérőkészlet a `~/.local/share/picasapy-meroadat/meroadat.tar`-ban
van, ami a CI-n NINCS meg — ott ez a teszt kihagyódik (`skipif`). Helyben fut.

A tarból csak a `3229-lanc-sorrend/` tagjai bomlanak ki (`tmp_path` alá), a
teljes tar nem. Az olvasás a projekt saját `tiff_helyben._szerkezet`-ével
történik. Az összevetés az Interop-mezők ÉRTÉKÉRE szól (egész számként, a saját
bájtsorrendjük szerint): a bájtsorrend a teljes EXIF-blokk tulajdonsága, nem az
Interop IFD-é, és nem ennek a jegynek a tárgya."""

from __future__ import annotations

import re
import struct
import tarfile
from pathlib import Path

import pytest

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.metadata import tiff_helyben as th
from picasapy.metadata.export_metadata import _szegmensek

_TAR = Path.home() / ".local/share/picasapy-meroadat/meroadat.tar"
_MAPPA = "3229-lanc-sorrend"
_EXIF_ID = b"Exif\x00\x00"


def _kibont(tmp_path: Path) -> Path:
    """Csak a 3229-es mappa tagjai, a tar többi tartalma nem."""
    with tarfile.open(_TAR) as tar:
        tagok = [
            t for t in tar.getmembers()
            if t.name == _MAPPA or t.name.startswith(_MAPPA + "/")
        ]
        tar.extractall(tmp_path, members=tagok, filter="data")
    return tmp_path / _MAPPA


def _interop(path: Path) -> dict[int, int | bytes]:
    """{tag: érték}: LONG → egész (a fájl bájtsorrendjében), egyébként bájtok."""
    for marker, seg in _szegmensek(path.read_bytes()):
        if marker == 0xE1 and seg[4:].startswith(_EXIF_ID):
            tiff = seg[4 + len(_EXIF_ID) :]
            e = "<" if tiff[:2] == b"II" else ">"
            ki: dict[int, int | bytes] = {}
            for (ifd, tag), peldanyok in th._szerkezet(tiff, len(tiff)).items():
                if ifd != "Interop":
                    continue
                assert len(peldanyok) == 1, hex(tag)
                tipus, darab, nyers = peldanyok[0]
                ki[tag] = struct.unpack(e + "I", nyers)[0] if (tipus, darab) == (4, 1) else nyers
            return ki
    raise AssertionError(f"nincs EXIF: {path.name}")


@pytest.mark.skipif(not _TAR.is_file(), reason="a mérőadat-tar nincs meg (CI-n nincs)")
def test_interop_egyezik_a_valodi_picasa_exporttal(tmp_path):
    mappa = _kibont(tmp_path)
    ini = (mappa / ".picasa.ini").read_text(encoding="utf-8")
    lancok = re.findall(r"\[(.*?\.jpg)\]\r?\nfilters=(.*?)\r?\n", ini)
    assert len(lancok) == 4
    report = export_photos(
        [ExportItem(mappa / nev, filters=f) for nev, f in lancok],
        tmp_path / "sajat",
        ExportSettings(),
    )
    assert report.failed == ()
    for nev, _ in lancok:
        picasa = _interop(mappa / "export" / nev)
        sajat = _interop(tmp_path / "sajat" / nev)
        assert 0x0001 not in picasa, nev  # a Picasa nem ír InteropIndexet
        assert 0x0001 not in sajat, nev
        assert sajat == picasa, nev
        assert picasa[0x0002] == b"0100", nev
        assert (picasa[0x1001], picasa[0x1002]) == (1600, 1200), nev
