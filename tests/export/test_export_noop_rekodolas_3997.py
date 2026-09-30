"""A #3997 két 684-es Picasa-exportja bájthű másolat helyett újrakódolódik.

A `meroadat.tar` CI-n hiányzik, ezért csak a két forrásképet, a hozzájuk tartozó
Picasa-exportot és a forrás `.picasa.ini` fájlját olvassuk ki belőle.

Mérés: mindkét 960×640-es forrás 61 548 bájt, 4:2:0 SOF-fal; a Picasa-kimenet
48 384 bájt, 4:4:4 SOF-fal és eltérő DQT-vel. Mindkét kimenetben 533 660/614 400
dekódolt képpont pontosan egyezik a forrással, de a legnagyobb csatornaeltérés
12. Ez JPEG-újrakódolás, nem puszta EXIF-beillesztés.

# rontás-kontroll: picasapy.metadata.export_metadata._INTEROP_VERZIO = b"0000" → 2 failed
"""

from __future__ import annotations

import re
import struct
import tarfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.metadata import tiff_helyben as th
from picasapy.metadata.export_metadata import _szegmensek

_TAR = Path.home() / ".local/share/picasapy-meroadat/meroadat.tar"
_MAPPA = "684-merokeszlet"
_ESETEK = ("tint__hex4", "tint__hex8")
_EXIF_ID = b"Exif\x00\x00"


def _kibont(tmp_path: Path) -> Path:
    """Pontosan a két párt, a láncleíró INI-t és a Picasa-exportot olvassa ki."""
    mappa = tmp_path / _MAPPA
    tagok = [
        f"{_MAPPA}/.picasa.ini",
        *(
            f"{_MAPPA}/{hely + '/' if hely else ''}{nev}.jpg"
            for nev in _ESETEK
            for hely in ("", "export")
        ),
    ]
    with tarfile.open(_TAR, "r") as tar:
        for tag in tagok:
            member = tar.getmember(tag)
            cel = tmp_path / tag
            cel.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as forras, cel.open("wb") as kimenet:
                kimenet.write(forras.read())
    return mappa


def _interop(path: Path) -> dict[int, int | bytes]:
    """Az Interop IFD mezői az EXIF-blokk saját bájtsorrendjében."""
    for marker, seg in _szegmensek(path.read_bytes()):
        if marker != 0xE1 or not seg[4:].startswith(_EXIF_ID):
            continue
        tiff = seg[4 + len(_EXIF_ID) :]
        e = "<" if tiff[:2] == b"II" else ">"
        mezok: dict[int, int | bytes] = {}
        for (ifd, tag), peldanyok in th._szerkezet(tiff, len(tiff)).items():
            if ifd != "Interop":
                continue
            assert len(peldanyok) == 1, hex(tag)
            tipus, darab, nyers = peldanyok[0]
            mezok[tag] = (
                struct.unpack(e + "I", nyers)[0]
                if (tipus, darab) == (4, 1)
                else nyers
            )
        return mezok
    raise AssertionError(f"nincs EXIF: {path.name}")


def _kep(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def _dqt(path: Path) -> dict[int, list[int]]:
    tables: dict[int, list[int]] = {}
    for marker, segment in _szegmensek(path.read_bytes()):
        if marker != 0xDB:
            continue
        payload = segment[4:]
        offset = 0
        while offset < len(payload):
            specifikacio = payload[offset]
            offset += 1
            precizio, tabla = specifikacio >> 4, specifikacio & 0x0F
            meret = 64 * (2 if precizio else 1)
            nyers = payload[offset : offset + meret]
            offset += meret
            tables[tabla] = (
                list(struct.unpack(f">{len(nyers) // 2}H", nyers))
                if precizio
                else list(nyers)
            )
    assert tables
    return tables


def _sof(path: Path) -> tuple[tuple[int, int, int, int], ...]:
    with Image.open(path) as image:
        return tuple(image.layer)


def _app_markerek(path: Path) -> tuple[int, ...]:
    return tuple(
        marker
        for marker, _ in _szegmensek(path.read_bytes())
        if 0xE0 <= marker <= 0xEF
    )


@pytest.mark.skipif(not _TAR.is_file(), reason="a mérőadat-tar nincs meg (CI-n nincs)")
@pytest.mark.parametrize("nev", _ESETEK)
def test_a_meres_szerint_a_picasa_es_a_picasapy_is_ujrakodol(nev, tmp_path):
    mappa = _kibont(tmp_path)
    ini = (mappa / ".picasa.ini").read_text(encoding="utf-8")
    lancok = dict(
        re.findall(r"^\[(tint__hex[48]\.jpg)\]\nfilters=(.*?)\n", ini, re.MULTILINE)
    )
    assert lancok == {
        "tint__hex4.jpg": "Tint=1,79.842102,ffff;",
        "tint__hex8.jpg": "Tint=1,79.842102,0000ffff;",
    }

    forras = mappa / f"{nev}.jpg"
    picasa = mappa / "export" / f"{nev}.jpg"
    sajat_mappa = tmp_path / "picasapy-export"
    report = export_photos(
        [ExportItem(forras, filters=lancok[forras.name])],
        sajat_mappa,
        ExportSettings(),
    )
    assert report.failed == ()
    sajat = sajat_mappa / forras.name

    # A referencia saját DQT-je és dekódolt képpontjai bizonyítják, hogy a
    # Picasa újrakódolt, noha ez a Tint= írásmód a PicasaPy effektlistájában üres.
    assert len(forras.read_bytes()) == 61_548
    assert len(picasa.read_bytes()) == 48_384
    assert _dqt(picasa) != _dqt(forras)
    assert _dqt(forras)[0][:8] == [1, 1, 1, 1, 1, 1, 1, 1]
    assert _dqt(picasa)[0][:8] == [2, 2, 2, 2, 2, 1, 2, 2]
    assert _sof(forras) == ((1, 2, 2, 0), (2, 1, 1, 1), (3, 1, 1, 1))
    assert _sof(picasa) == ((1, 1, 1, 0), (2, 1, 1, 1), (3, 1, 1, 1))
    assert _app_markerek(forras) == (0xE0,)
    assert _app_markerek(picasa) == (0xE0, 0xE1, 0xE1, 0xED)
    forras_pixelek, picasa_pixelek = _kep(forras), _kep(picasa)
    elteres = np.abs(picasa_pixelek.astype(np.int16) - forras_pixelek.astype(np.int16))
    assert np.count_nonzero(np.all(elteres == 0, axis=2)) == 533_660
    assert int(elteres.max()) == 12

    # Az exportnak is újra kell kódolnia: a puszta metadata-injektálás nem elég.
    assert _dqt(sajat) != _dqt(forras)
    assert not np.array_equal(_kep(sajat), _kep(forras))
    assert _interop(sajat) == _interop(picasa)
    assert _interop(picasa)[0x0002] == b"0100"
    assert (_interop(picasa)[0x1001], _interop(picasa)[0x1002]) == (960, 640)
