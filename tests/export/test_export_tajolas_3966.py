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
_RENDERELTETO_LANC = "Tint=1,79.842102,ffff;"  # elvetett lánc is újrakódolást kér


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


def _forras_elonezettel(tmp_path, tajolas=6):
    """Mint `_forras`, de az IFD1-ben is van JPEG-előnézet ÉS `Orientation`."""
    tomb = np.zeros((20, 60, 3), np.uint8)
    tomb[:, :20] = (255, 0, 0)
    tomb[:, 20:] = (0, 0, 255)
    elo = tmp_path / "elo.jpg"
    Image.fromarray(tomb[:, :, :]).resize((30, 10)).save(elo, "JPEG")
    exif = piexif.dump(
        {
            "0th": {piexif.ImageIFD.Orientation: tajolas},
            "Exif": {},
            "1st": {piexif.ImageIFD.Orientation: tajolas},
            "thumbnail": elo.read_bytes(),
        }
    )
    path = tmp_path / "elonezettel.jpg"
    Image.fromarray(tomb).save(path, "JPEG", quality=95, exif=exif)
    return path


def _tajolasok(path):
    """(IFD0, IFD1) `Orientation` az első EXIF-szegmensből."""
    for marker, seg in _szegmensek(path.read_bytes()):
        if marker == 0xE1 and seg[4:].startswith(_EXIF_ID):
            d = piexif.load(seg[4 + len(_EXIF_ID) :])
            return (
                d["0th"].get(piexif.ImageIFD.Orientation),
                d["1st"].get(piexif.ImageIFD.Orientation),
            )
    return None, None


def _export(source, tmp_path, *, filters="", **settings):
    report = export_photos(
        [ExportItem(source, filters=filters)],
        tmp_path / "out",
        ExportSettings(**settings),
    )
    assert report.failed == ()
    return report.exported[0]


@pytest.mark.parametrize("tajolas", [6, 8])
class TestUjrakodoltKimenet:
    def test_a_tag_1_lesz(self, tajolas, tmp_path):
        kimenet = _export(
            _forras(tmp_path, tajolas),
            tmp_path,
            filters="bw=1;",
            max_dimension=1000,
        )
        assert _tajolas(kimenet) == 1

    def test_kepek_es_tag_egyutt_egyszer_forgat(self, tajolas, tmp_path):
        source = _forras(tmp_path, tajolas)
        kimenet = _export(
            source,
            tmp_path,
            filters=_RENDERELTETO_LANC,
            max_dimension=1000,
        )
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



def test_az_ifd1_tajolas_tagje_nem_marad_6(tmp_path):
    """#3998: a forrás IFD1-e (és annak `Orientation`-je) nem kerül át; a
    20×60-as kimenetnek (≤ 300 px) nincs IFD1-e."""
    source = _forras_elonezettel(tmp_path)
    assert _tajolasok(source) == (6, 6)
    kimenet = _export(
        source, tmp_path, filters="bw=1;", max_dimension=1000
    )
    assert _tajolasok(kimenet) == (1, None)


def test_az_ifd1_hianyzo_tajolas_nem_potlodik(tmp_path):
    tiff = piexif.dump({"0th": {piexif.ImageIFD.Orientation: 6}, "1st": {}})[6:]
    v = th.Valtozas("1st", 0x0112, th.Ertek(th.SHORT, 1), csak_ha_megvan=True)
    ki = th.frissitett_tiff(tiff, [v])
    assert piexif.load(b"Exif\x00\x00" + ki)["1st"].get(0x0112) is None


class TestTartalekAgak:
    """Ha az EXIF-frissítés kimarad, a forrás tagje sem mehet ki 6-osan."""

    def test_exif_hiba_eseten_a_tajolas_1(self, tmp_path, monkeypatch):
        from picasapy.metadata import export_metadata as em

        def hiba(*a, **k):
            raise RuntimeError("kényszerített EXIF-hiba")

        monkeypatch.setattr(em, "_exif_szegmens", hiba)
        source = _forras_elonezettel(tmp_path)
        kimenet = _export(
            source, tmp_path, filters="bw=1;", max_dimension=1000
        )
        assert _tajolasok(kimenet) == (1, 1)
        with Image.open(kimenet) as kep:
            assert kep.size == (20, 60)  # álló: a képpontok egyszer fordultak

    def test_egesz_frissites_hibaja_eseten_a_tajolas_1(self, tmp_path, monkeypatch):
        from picasapy.metadata import export_metadata as em

        def hiba(*a, **k):
            raise RuntimeError("kényszerített hiba")

        monkeypatch.setattr(em, "_frissitett_szegmensek", hiba)
        kimenet = _export(
            _forras_elonezettel(tmp_path),
            tmp_path,
            filters=_RENDERELTETO_LANC,
            max_dimension=1000,
        )
        assert _tajolasok(kimenet) == (1, 1)

    def test_bajtmasolas_haloja_is_1_re_irja(self, tmp_path, monkeypatch):
        from picasapy.export import exporter as ex

        def hiba(*a, **k):
            raise RuntimeError("kényszerített hiba")

        monkeypatch.setattr(ex, "frissitett_metaadat", hiba)
        kimenet = _export(
            _forras_elonezettel(tmp_path),
            tmp_path,
            filters=_RENDERELTETO_LANC,
            max_dimension=1000,
        )
        assert _tajolasok(kimenet) == (1, 1)

    def test_a_tajolas_iras_hibaja_nem_buktatja_a_kepet(self, tmp_path, monkeypatch, caplog):
        from picasapy.metadata import export_metadata as em

        def hiba(*a, **k):
            raise RuntimeError("kényszerített hiba")

        monkeypatch.setattr(em, "_exif_szegmens", hiba)
        monkeypatch.setattr(em, "tajolas_1_helyben", hiba)
        with caplog.at_level("WARNING"):
            kimenet = _export(
                _forras_elonezettel(tmp_path),
                tmp_path,
                filters="bw=1;",
                max_dimension=1000,
            )
        assert kimenet.is_file()
        assert any("tájolás" in r.getMessage() for r in caplog.records)


class TestTartalekIroSzigorusaga:
    """A `tajolas_1_helyben` (tartalék út) ugyanúgy önellenőriz, mint a fő út."""

    def test_nem_helyben_irhato_tajolas_tiffhiba_nem_nema_kihagyas(self):
        # LONG, 2 darab: a helyén nem írható → hangos hiba (a hívó naplózza)
        e = "<"
        tiff = (
            b"II*\x00\x08\x00\x00\x00"
            + struct.pack(e + "H", 1)
            + struct.pack(e + "HHII", 0x0112, 4, 2, 26)
            + b"\x00" * 4
            + struct.pack(e + "II", 6, 6)
        )
        with pytest.raises(th.TiffHiba):
            th.tajolas_1_helyben(tiff)

    def test_idegen_tag_serulese_tiffhiba(self, monkeypatch):
        # ha az írás a tájoláson kívül bármi mást is megváltoztatna, az
        # önellenőrzés megfogja (rontás-kontroll: az ellenőrzés nélkül átmegy)
        tiff = piexif.dump({"0th": {piexif.ImageIFD.Orientation: 6, piexif.ImageIFD.Make: b"Canon"}})[6:]
        eredeti = th._helyben_irhato

        def rongalo(blokk, meglevo, ertek):
            ok = eredeti(blokk, meglevo, ertek)
            make = next(b for b in blokk.ifd(blokk.u32(4))[0] if b.tag == 0x010F)
            blokk.buf[blokk.u32(make.hely + 8)] ^= 0xFF
            return ok

        monkeypatch.setattr(th, "_helyben_irhato", rongalo)
        with pytest.raises(th.TiffHiba):
            th.tajolas_1_helyben(tiff)

    def test_ep_blokkon_csak_a_tajolas_valtozik(self):
        tiff = piexif.dump({"0th": {piexif.ImageIFD.Orientation: 8, piexif.ImageIFD.Make: b"Canon"}})[6:]
        ki = th.tajolas_1_helyben(tiff)
        assert piexif.load(_EXIF_ID + ki)["0th"][piexif.ImageIFD.Orientation] == 1
        assert sum(a != b for a, b in zip(tiff, ki, strict=True)) == 1 and len(ki) == len(tiff)
