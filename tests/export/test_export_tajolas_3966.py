"""Az exportált kép nem fordulhat el kétszer (#3966).

A dekódolás (`IMREAD_COLOR`) az EXIF tájolás szerint már elforgatja a
képpontokat, tehát az újrakódolt kimenet tájolás-tagje nem maradhat a
forrásé. A spec (`picasa-metaadat-tulajdonsagok.md` 16. E) szerint az eredeti
mentő a forrásban MEGLÉVŐ `0x0d` kulcsot (6.1: `0x0112` Orientation) üres
értékkel teszi a friss halmazba — nálunk: `1`, a helyén. A bájthű másolatnál
a képpontok sem forognak, ott a tag a forrásé.

A várt állást a Pillow `exif_transpose`-a adja (egy tájolást tisztelő néző),
a termékkódtól függetlenül."""

from __future__ import annotations

import struct

import numpy as np
import piexif
import pytest
from PIL import Image, ImageOps

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.metadata import tiff_helyben as th
from picasapy.metadata.export_metadata import _szegmensek

_EXIF_ID = b"Exif\x00\x00"


def _forras(tmp_path, tajolas, size=(60, 20)):
    """Fekvő tárolt kép: a bal harmada piros, a többi kék; EXIF `Orientation`."""
    tomb = np.zeros((size[1], size[0], 3), np.uint8)
    tomb[:, :] = (0, 0, 255)
    tomb[:, : size[0] // 3] = (255, 0, 0)
    exif = piexif.dump({"0th": {piexif.ImageIFD.Orientation: tajolas}, "Exif": {}})
    path = tmp_path / f"tajolas{tajolas}.jpg"
    Image.fromarray(tomb).save(path, "JPEG", quality=95, exif=exif)
    return path


def _tajolas(path):
    """Az első EXIF-szegmens `Orientation`-je, vagy `None`."""
    for marker, seg in _szegmensek(path.read_bytes()):
        if marker == 0xE1 and seg[4:].startswith(_EXIF_ID):
            return piexif.load(seg[4 + len(_EXIF_ID) :])["0th"].get(
                piexif.ImageIFD.Orientation
            )
    return None


def _nezoben(path):
    """A kép, ahogy egy tájolást tisztelő néző mutatja (RGB tömb)."""
    with Image.open(path) as kep:
        return np.asarray(ImageOps.exif_transpose(kep).convert("RGB"), dtype=np.int16)


def _export(source, tmp_path, **settings):
    report = export_photos([ExportItem(source)], tmp_path / "out", ExportSettings(**settings))
    assert report.failed == ()
    return report.exported[0]


@pytest.mark.parametrize("tajolas", [6, 8])
class TestUjrakodoltKimenet:
    def test_a_tag_1_lesz(self, tajolas, tmp_path):
        kimenet = _export(_forras(tmp_path, tajolas), tmp_path, max_dimension=1000)
        assert _tajolas(kimenet) == 1

    def test_kepek_es_tag_egyutt_egyszer_forgat(self, tajolas, tmp_path):
        source = _forras(tmp_path, tajolas)
        kimenet = _export(source, tmp_path, max_dimension=1000)
        vart, kapott = _nezoben(source), _nezoben(kimenet)
        # álló (20×60): a néző egyszer fordít, nem kétszer (akkor 60×20 lenne)
        assert kapott.shape == vart.shape == (60, 20, 3)
        assert np.abs(kapott - vart).mean() < 8


@pytest.mark.parametrize("tajolas", [6, 8])
def test_bajthu_masolatnal_a_tag_valtozatlan(tajolas, tmp_path):
    source = _forras(tmp_path, tajolas)
    kimenet = _export(source, tmp_path)
    assert kimenet.read_bytes() == source.read_bytes()
    assert _tajolas(kimenet) == tajolas


class TestTiffSzinten:
    """A `Valtozas(csak_ha_megvan=True)`: a meglévőt írja, hiányzót nem pótol."""

    @staticmethod
    def _orientation(tiff):
        return piexif.load(b"Exif\x00\x00" + tiff)["0th"].get(piexif.ImageIFD.Orientation)

    def test_meglevo_tag_helyben_1(self):
        tiff = piexif.dump({"0th": {piexif.ImageIFD.Orientation: 6}})[6:]
        v = th.Valtozas("0th", 0x0112, th.Ertek(th.SHORT, 1), csak_ha_megvan=True)
        ki = th.frissitett_tiff(tiff, [v])
        assert self._orientation(ki) == 1
        assert len(ki) == len(tiff)  # helyben íródott, nem fűződött hozzá semmi

    def test_hianyzo_tag_nem_kerul_be(self):
        tiff = piexif.dump({"0th": {piexif.ImageIFD.Make: b"Canon"}})[6:]
        v = th.Valtozas("0th", 0x0112, th.Ertek(th.SHORT, 1), csak_ha_megvan=True)
        ki = th.frissitett_tiff(tiff, [v])
        assert self._orientation(ki) is None
        assert ki == tiff

    def test_nem_helyben_irhato_tag_athelyezve_1(self):
        # idegen típusú (LONG, 2 darab) tájolás: a helyén nem írható, az IFD
        # másolatába kerül SHORT 1-ként
        e = "<"
        tiff = (
            b"II*\x00\x08\x00\x00\x00"
            + struct.pack(e + "H", 1)
            + struct.pack(e + "HHII", 0x0112, 4, 2, 26)
            + b"\x00" * 4
            + struct.pack(e + "II", 6, 6)
        )
        v = th.Valtozas("0th", 0x0112, th.Ertek(th.SHORT, 1), csak_ha_megvan=True)
        ki = th.frissitett_tiff(tiff, [v])
        ifd0 = struct.unpack_from(e + "I", ki, 4)[0]
        tag, tipus, darab, ertek = struct.unpack_from(e + "HHIH", ki, ifd0 + 2)
        assert (tag, tipus, darab, ertek) == (0x0112, th.SHORT, 1, 1)

