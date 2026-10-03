"""Az export JPEG-je EXIF-bélyegképet kap, ha mindkét oldala > 300 px (#3998).

Spec: `picasa-metaadat-tulajdonsagok.md` 16. H) és I). A mért méretek
(960×640 → 160×112, 1650×1250 → 160×128, 1090×770 → 160×120, 818×950 → 144×160)
szintetikus képen; a valódi exporttal való összevetés a helyi kör dolga.
"""

from __future__ import annotations

import io
import struct
from datetime import datetime

import cv2
import numpy as np
import piexif
import pytest
from PIL import Image

from picasapy.metadata import exif_belyegkep as bk
from picasapy.metadata import export_metadata as em
from picasapy.metadata import tiff_helyben as th

_EXIF_ID = b"Exif\x00\x00"
_MOST = datetime(2026, 9, 30, 12, 0, 0)


def _kep(w, h, seed=1):
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 255, w, dtype=np.float32)[None, :, None]
    y = np.linspace(0, 255, h, dtype=np.float32)[:, None, None]
    zaj = rng.integers(0, 20, (h, w, 3))
    return np.clip(np.concatenate([x + 0 * y, y + 0 * x, (x + y) / 2], axis=2) + zaj, 0, 255).astype(
        np.uint8
    )


def _kodolt(w, h):
    ok, buf = cv2.imencode(".jpg", _kep(w, h), [cv2.IMWRITE_JPEG_QUALITY, 90])
    assert ok
    return buf.tobytes()


def _forras(tmp_path, *, exif=None, name="forras.jpg"):
    b = io.BytesIO()
    kwargs = {"exif": exif} if exif is not None else {}
    Image.new("RGB", (64, 48), "gray").save(b, "JPEG", **kwargs)
    p = tmp_path / name
    p.write_bytes(b.getvalue())
    return p


def _regi_elonezet():
    b = io.BytesIO()
    Image.new("RGB", (40, 30), (250, 0, 250)).save(b, "JPEG")
    return b.getvalue()


def _forras_elonezettel(tmp_path):
    exif = piexif.dump(
        {
            "0th": {piexif.ImageIFD.Make: b"Kamera", piexif.ImageIFD.Orientation: 1},
            "Exif": {},
            "1st": {piexif.ImageIFD.Orientation: 1, piexif.ImageIFD.XResolution: (300, 1)},
            "thumbnail": _regi_elonezet(),
        }
    )
    return _forras(tmp_path, exif=exif), _regi_elonezet()


def _exif_torzs(jpeg):
    pos = 2
    while pos + 4 <= len(jpeg) and jpeg[pos] == 0xFF and jpeg[pos + 1] != 0xDA:
        hossz = int.from_bytes(jpeg[pos + 2 : pos + 4], "big")
        if jpeg[pos + 1] == 0xE1 and jpeg[pos + 4 : pos + 10] == _EXIF_ID:
            return jpeg[pos + 10 : pos + 2 + hossz]
        pos += 2 + hossz
    return None


def _ifd1(tiff):
    e = "<" if tiff[:2] == b"II" else ">"
    ifd0 = struct.unpack_from(e + "I", tiff, 4)[0]
    n = struct.unpack_from(e + "H", tiff, ifd0)[0]
    kov = struct.unpack_from(e + "I", tiff, ifd0 + 2 + 12 * n)[0]
    if not kov:
        return e, None
    m = struct.unpack_from(e + "H", tiff, kov)[0]
    return e, {
        t: (ty, d, mezo)
        for t, ty, d, mezo in (
            struct.unpack_from(e + "HHI4s", tiff, kov + 2 + 12 * i) for i in range(m)
        )
    }


def _belyegkep(jpeg):
    tiff = _exif_torzs(jpeg)
    assert tiff is not None
    e, ifd1 = _ifd1(tiff)
    assert ifd1 is not None
    kezdet = struct.unpack(e + "I", ifd1[0x201][2])[0]
    hossz = struct.unpack(e + "I", ifd1[0x202][2])[0]
    return tiff, tiff[kezdet : kezdet + hossz]


def _frissit(source, w, h):
    return em.frissitett_metaadat(source, _kodolt(w, h), size=(w, h), now=_MOST)


@pytest.mark.parametrize(
    "w,h,cel",
    [
        (960, 640, (160, 112)),
        (1650, 1250, (160, 128)),
        (1090, 770, (160, 120)),
        (818, 950, (144, 160)),
    ],
)
def test_a_mert_esetek_belyegkepe(tmp_path, w, h, cel):
    ki = _frissit(_forras(tmp_path), w, h)
    _, jpeg = _belyegkep(ki)
    with Image.open(io.BytesIO(jpeg)) as kep:
        assert kep.size == cel
        assert kep.format == "JPEG"


def test_a_belyegkep_a_kimenet_lanczos3_elofelezett_kicsinyitese(tmp_path):
    w, h = 960, 640
    ki = _frissit(_forras(tmp_path), w, h)
    _, jpeg = _belyegkep(ki)
    dekodolt = cv2.imdecode(np.frombuffer(_kodolt(w, h), np.uint8), cv2.IMREAD_COLOR)
    elvart = bk.kodol(bk.kicsinyitett(dekodolt), 85)
    assert jpeg == elvart


def test_metaadat_nelkuli_forras_is_kap_exifet_es_belyegkepet(tmp_path):
    ki = _frissit(_forras(tmp_path), 1000, 700)
    assert _exif_torzs(ki) is not None
    assert _belyegkep(ki)[1].startswith(b"\xff\xd8")


def test_a_forras_ifd1_je_es_belyegkepe_nem_kerul_at(tmp_path):
    source, regi = _forras_elonezettel(tmp_path)
    ki = _frissit(source, 1000, 700)
    tiff, jpeg = _belyegkep(ki)
    assert regi not in ki
    assert jpeg != regi
    _, ifd1 = _ifd1(tiff)
    assert sorted(ifd1) == [0x103, 0x11A, 0x11B, 0x128, 0x201, 0x202]
    # a forrás többi EXIF-tagje megmarad
    assert piexif.load(b"Exif\x00\x00" + tiff)["0th"][piexif.ImageIFD.Make] == b"Kamera"


@pytest.mark.parametrize("w,h", [(300, 700), (700, 300), (300, 300), (250, 200)])
def test_300_px_alatt_nincs_ifd1_es_a_forras_belyegkepe_sem_marad(tmp_path, w, h):
    source, regi = _forras_elonezettel(tmp_path)
    ki = _frissit(source, w, h)
    assert regi not in ki
    tiff = _exif_torzs(ki)
    assert tiff is not None and _ifd1(tiff)[1] is None
    assert piexif.load(b"Exif\x00\x00" + tiff)["0th"][piexif.ImageIFD.Make] == b"Kamera"


def test_300_px_alatt_metaadat_nelkuli_forrasnal_sincs_ifd1(tmp_path):
    ki = _frissit(_forras(tmp_path), 200, 150)
    assert _ifd1(_exif_torzs(ki))[1] is None


def test_301_px_mar_kap(tmp_path):
    ki = _frissit(_forras(tmp_path), 301, 301)
    _, jpeg = _belyegkep(ki)
    with Image.open(io.BytesIO(jpeg)) as kep:
        assert kep.size == (160, 160)


class TestMinosegVisszalepes:
    """Ha az APP1 > 0xfffd bájt, a minőség 15-tel csökken (85 → … → 10)."""

    def _hamis(self, monkeypatch, meretek):
        hivasok = []

        def kodol(kicsi, minoseg=85):
            hivasok.append(minoseg)
            return b"\xff\xd8" + bytes([minoseg]) * (meretek[minoseg] - 2)

        monkeypatch.setattr(bk, "kodol", kodol)
        return hivasok

    def test_az_elso_amelyik_elfer(self, tmp_path, monkeypatch):
        hivasok = self._hamis(
            monkeypatch, {85: 70000, 70: 66000, 55: 3000, 40: 2000, 25: 1000, 10: 500}
        )
        ki = _frissit(_forras(tmp_path), 1000, 700)
        assert hivasok == [85, 70, 55]
        jpeg = _belyegkep(ki)[1]
        assert jpeg == b"\xff\xd8" + bytes([55]) * 2998

    def test_ha_10_sem_fer_el_nincs_ifd1_de_a_tobbi_frissul(self, tmp_path, monkeypatch):
        hivasok = self._hamis(
            monkeypatch, {q: 70000 for q in (85, 70, 55, 40, 25, 10)}
        )
        source, regi = _forras_elonezettel(tmp_path)
        ki = _frissit(source, 1000, 700)
        assert hivasok == [85, 70, 55, 40, 25, 10]
        tiff = _exif_torzs(ki)
        assert tiff is not None and _ifd1(tiff)[1] is None
        assert regi not in ki
        uj = piexif.load(b"Exif\x00\x00" + tiff)
        assert uj["0th"][piexif.ImageIFD.Software] == b"PicasaPy"


def test_kodolasi_hiba_nem_buktatja_az_exportot(tmp_path, monkeypatch, caplog):
    def hiba(*_a, **_k):
        raise ValueError("kényszerített hiba")

    monkeypatch.setattr(bk, "kodol", hiba)
    source, regi = _forras_elonezettel(tmp_path)
    with caplog.at_level("WARNING"):
        ki = _frissit(source, 1000, 700)
    tiff = _exif_torzs(ki)
    assert tiff is not None and _ifd1(tiff)[1] is None
    assert regi not in ki
    assert any("bélyegkép" in r.getMessage() for r in caplog.records)


def test_az_exif_tobbi_resze_nem_gyengul(tmp_path):
    """A DateTime, a méret-tagek és az Interop változatlanul frissülnek."""
    ki = _frissit(_forras(tmp_path), 1000, 700)
    uj = piexif.load(b"Exif\x00\x00" + _exif_torzs(ki))
    assert uj["0th"][piexif.ImageIFD.DateTime] == b"2026:09:30 12:00:00"
    assert uj["Exif"][piexif.ExifIFD.PixelXDimension] == 1000
    assert uj["Exif"][piexif.ExifIFD.PixelYDimension] == 700
    tiff = _exif_torzs(ki)
    szerk = th._szerkezet(tiff, len(tiff))
    assert szerk[("Interop", 0x0002)][0][2] == b"0100"
    assert ("Interop", 0x1001) in szerk and ("Interop", 0x1002) in szerk


def test_valodi_export_bejarata(tmp_path):
    """A teljes út (`export_photos`): a kimenet érvényes JPEG, az EXIF-ben ott a bélyegkép."""
    from picasapy.export.exporter import ExportItem, ExportSettings, export_photos

    source = tmp_path / "nagy.jpg"
    Image.fromarray(cv2.cvtColor(_kep(1000, 700), cv2.COLOR_BGR2RGB)).save(source, "JPEG")
    # A tényleges szerkesztés újrakódolást kér; a max_dimension önmagában nem
    # tiltja le az érintetlen JPEG bájthű másolását (#4018).
    report = export_photos(
        [ExportItem(source, filters="bw=1;")],
        tmp_path / "out",
        ExportSettings(max_dimension=800),
    )
    assert report.failed == ()
    ki = report.exported[0].read_bytes()
    _, jpeg = _belyegkep(ki)
    with Image.open(io.BytesIO(jpeg)) as kep:
        assert kep.size == (160, 112)
    with Image.open(report.exported[0]) as fo:
        assert fo.size == (800, 560)
    assert piexif.load(str(report.exported[0]))["thumbnail"] == jpeg
