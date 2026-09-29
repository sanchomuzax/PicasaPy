"""A csak tükrözött kép exportja nem lehet bájthű másolat (#3977).

Az `_is_noop_copy` korábban nem nézte a `flip_flags`-et, így a tükrözés
elveszett. A várt képpontokat a Pillow tükrözése adja, a termékkódtól
függetlenül; a kimenet tájolás-tagje (#3966) tükrözésnél is `1` marad."""

from __future__ import annotations

import numpy as np
import piexif
import pytest
from PIL import Image, ImageOps

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.metadata.export_metadata import _szegmensek

_EXIF_ID = b"Exif\x00\x00"


def _forras(tmp_path, tajolas=None, size=(60, 20)):
    """Aszimmetrikus kép: bal harmad piros, felül-jobbra zöld folt, a többi kék."""
    tomb = np.zeros((size[1], size[0], 3), np.uint8)
    tomb[:, :] = (0, 0, 255)
    tomb[:, : size[0] // 3] = (255, 0, 0)
    tomb[: size[1] // 3, -size[0] // 4 :] = (0, 255, 0)
    path = tmp_path / "forras.jpg"
    kwargs = {}
    if tajolas is not None:
        kwargs["exif"] = piexif.dump(
            {"0th": {piexif.ImageIFD.Orientation: tajolas}, "Exif": {}}
        )
    Image.fromarray(tomb).save(path, "JPEG", quality=95, subsampling=0, **kwargs)
    return path


def _tajolas(path):
    for marker, seg in _szegmensek(path.read_bytes()):
        if marker == 0xE1 and seg[4:].startswith(_EXIF_ID):
            return piexif.load(seg[4 + len(_EXIF_ID) :])["0th"].get(
                piexif.ImageIFD.Orientation
            )
    return None


def _rgb(path):
    with Image.open(path) as kep:
        return np.asarray(kep.convert("RGB"), dtype=np.int16)


def _tukor(path, flags):
    with Image.open(path) as kep:
        kep = kep.convert("RGB")
        if flags & 1:
            kep = ImageOps.mirror(kep)
        if flags & 2:
            kep = ImageOps.flip(kep)
        return np.asarray(kep, dtype=np.int16)


def _export(item, tmp_path):
    report = export_photos([item], tmp_path / "out", ExportSettings())
    assert report.failed == ()
    return report.exported[0]


@pytest.mark.parametrize("flags", [1, 2, 3])
def test_csak_tukrozott_kep_kimenete_tukrozott(tmp_path, flags):
    forras = _forras(tmp_path)
    kimenet = _export(ExportItem(forras, flip_flags=flags), tmp_path)
    assert kimenet.read_bytes() != forras.read_bytes()
    elteres = np.abs(_rgb(kimenet) - _tukor(forras, flags))
    assert elteres.mean() < 6  # JPEG-újrakódolás zaja (éleken a színbontás)
    # és tényleg nem az eredeti állás
    assert np.abs(_rgb(kimenet) - _rgb(forras)).mean() > 4 * elteres.mean()


@pytest.mark.parametrize("flags", [1, 2])
def test_tukrozesnel_a_tajolas_tag_is_helyes(tmp_path, flags):
    """Forgatott (6-os tájolású) forrás + tükrözés: a képpontok a néző
    szerinti állásból tükröződnek, a tag `1` — nem forog újra."""
    forras = _forras(tmp_path, tajolas=6)
    kimenet = _export(ExportItem(forras, flip_flags=flags), tmp_path)
    assert _tajolas(kimenet) == 1
    with Image.open(forras) as kep:
        allo = ImageOps.exif_transpose(kep).convert("RGB")
    var = allo
    if flags & 1:
        var = ImageOps.mirror(var)
    if flags & 2:
        var = ImageOps.flip(var)
    got = _rgb(kimenet)
    assert got.shape[:2] == (var.height, var.width)
    assert np.abs(got - np.asarray(var, dtype=np.int16)).mean() < 6


def test_jelzo_nelkul_a_bajthu_ag_valtozatlan(tmp_path):
    forras = _forras(tmp_path, tajolas=6)
    for flags in (0, 4):  # a 4-es bitet nem értelmezzük: nincs tükrözés
        kimenet = _export(ExportItem(forras, flip_flags=flags), tmp_path)
        assert kimenet.read_bytes() == forras.read_bytes()
        kimenet.unlink()


def test_a_webexport_ugyanazt_az_utat_hasznalja():
    """A webexport `ExportItem(flip_flags=...)`-ot ad az `export_photos`-nak, tehát
    a döntés egyetlen helyen (`_is_noop_copy`) születik. Forrásszöveg-őr, a
    kimenetet nem méri. Az e-mail eredeti méretű ága NEM ezt az utat járja
    (a nyers forrásfájlt csatolja) — az a #3993 tárgya."""
    import inspect

    from picasapy.webexport import images

    forras = inspect.getsource(images)
    assert "flip_flags=" in forras and "export_photos(" in forras
