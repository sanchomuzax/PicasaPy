"""Az export frissíti a kép metaadatait, ahogy az eredeti Picasa (#3961).

Spec: `docs/specs/picasa-metaadat-tulajdonsagok.md` 16. szakasz (204 eredeti
export). Két mért eset: metaadat nélküli forrás (`3229-lanc-sorrend`) és
kamerás, XMP-s forrás (`3084-poszterizalas/Warm grasses…`).

A repóbeli tesztek a mért blokkok kicsinyített MÁSAIT építik (a NAS-tól
függetlenül); a NAS-os összevetés az eredeti Picasa exportjával mezőnként
`skipif`-fel fut, ha a mérőkészlet elérhető."""

import os
import re
from datetime import datetime
from pathlib import Path

import piexif
import pytest
from PIL import Image
from PIL.IptcImagePlugin import getiptcinfo

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.metadata.copy_signature import ALAIRAS
from picasapy.metadata.export_metadata import _szegmensek
from support.jpeg_factory import make_jpeg

_XMP_ID = b"http://ns.adobe.com/xap/1.0/\x00"
_MERT_MTIME = datetime(2026, 9, 16, 8, 0, 14)

# A kamerás forrás XMP-je (Lightroom), kicsinyítve; az `exif:` névtérben
# kamerás mező is van, amelyet az eredeti az XMP-ből TÖRÖL.
_KAMERAS_XMP = """<?xpacket begin='﻿' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'>
<rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
 <rdf:Description xmlns:xmp='http://ns.adobe.com/xap/1.0/'>
  <xmp:Rating>5</xmp:Rating>
  <xmp:ModifyDate>2014-08-13T22:19:41+01:00</xmp:ModifyDate>
 </rdf:Description>
 <rdf:Description xmlns:aux='http://ns.adobe.com/exif/1.0/aux/'>
  <aux:Lens>70.0-200.0 mm f/2.8</aux:Lens>
 </rdf:Description>
 <rdf:Description xmlns:exif='http://ns.adobe.com/exif/1.0/'>
  <exif:FNumber>32/10</exif:FNumber>
  <exif:DateTimeOriginal>2014-06-21T15:03:38</exif:DateTimeOriginal>
 </rdf:Description>
 <rdf:Description xmlns:crs='http://ns.adobe.com/camera-raw-settings/1.0/'>
  <crs:Contrast2012>-58</crs:Contrast2012>
 </rdf:Description>
</rdf:RDF>
</x:xmpmeta>
<?xpacket end='r'?>""".encode("utf-8")


def _metaadat_nelkuli_forras(tmp_path, size=(80, 60)):
    """A `3229-lanc-sorrend` forrás: nincs EXIF, nincs XMP; a fájl mtime-ja
    a mért `2026:09:16 08:00:14`."""
    source = tmp_path / "forras-3229.jpg"
    Image.new("RGB", size, "red").save(source, "JPEG")
    ts = _MERT_MTIME.timestamp()
    os.utime(source, (ts, ts))
    return source


def _kameras_forras(tmp_path, size=(80, 60)):
    """A `3084` forrás kicsinyített mása: a mért EXIF-mezők, Lightroom-XMP
    és IPTC."""
    source = make_jpeg(tmp_path / "Warm grasses.jpg", size=size, caption="Rét")
    exif = piexif.dump(
        {
            "0th": {
                piexif.ImageIFD.Make: b"NIKON CORPORATION",
                piexif.ImageIFD.Software: b"GIMP 2.8.14",
                piexif.ImageIFD.DateTime: b"2014:09:09 15:40:30",
                piexif.ImageIFD.Artist: b"David C Searle",
            },
            "Exif": {
                piexif.ExifIFD.ExifVersion: b"0230",
                piexif.ExifIFD.DateTimeOriginal: b"2014:06:21 15:03:38",
                piexif.ExifIFD.FNumber: (32, 10),
                piexif.ExifIFD.ISOSpeedRatings: 200,
            },
            "GPS": {},
            "1st": {},
        }
    )
    piexif.insert(exif, str(source))
    raw = source.read_bytes()
    hossz = len(_XMP_ID) + len(_KAMERAS_XMP) + 2
    xmp = b"\xff\xe1" + hossz.to_bytes(2, "big") + _XMP_ID + _KAMERAS_XMP
    source.write_bytes(raw[:2] + xmp + raw[2:])
    return source


def _export(source, tmp_path, **settings):
    """A `bw` lánc kifejezetten újrakódolást kér a metaadat-próbákhoz.

    A #4018 spec szerint szerkesztetlen JPEG-nél a méretbeállítás sem tiltja
    le a bájthű másolást, ezért ezek a tesztek nem erre támaszkodnak."""
    report = export_photos(
        [ExportItem(source, filters="bw=1;")],
        tmp_path / "out",
        ExportSettings(**settings),
    )
    assert report.failed == ()
    return report.exported[0]


def _xmp(path):
    for marker, seg in _szegmensek(path.read_bytes()):
        if marker == 0xE1 and seg[4:].startswith(_XMP_ID):
            return seg[4 + len(_XMP_ID) :].decode("utf-8")
    return None


def _kulonbseg_mp(szoveg_bajt, mikor):
    ertek = datetime.strptime(szoveg_bajt.decode(), "%Y:%m:%d %H:%M:%S")
    return abs((ertek - mikor).total_seconds())


class TestMetaadatNelkuliForras:
    """3229: az eredeti exportja mind az öt hiányzó mezőt pótolja."""

    def test_datetime_az_export_ideje(self, tmp_path):
        elotte = datetime.now()
        kimenet = _export(_metaadat_nelkuli_forras(tmp_path), tmp_path)
        exif = piexif.load(str(kimenet))
        assert _kulonbseg_mp(exif["0th"][piexif.ImageIFD.DateTime], elotte) <= 5

    def test_szoftver_es_szerzo_a_program_neve(self, tmp_path):
        exif = piexif.load(
            str(_export(_metaadat_nelkuli_forras(tmp_path), tmp_path))
        )
        assert exif["0th"][piexif.ImageIFD.Software] == ALAIRAS.encode()
        assert exif["0th"][piexif.ImageIFD.Artist] == ALAIRAS.encode()

    def test_eredeti_datum_a_forrasfajl_modositasi_ideje(self, tmp_path):
        exif = piexif.load(
            str(_export(_metaadat_nelkuli_forras(tmp_path), tmp_path))
        )
        assert (
            exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2026:09:16 08:00:14"
        )

    def test_exif_verzio_hozzaadva(self, tmp_path):
        exif = piexif.load(
            str(_export(_metaadat_nelkuli_forras(tmp_path), tmp_path))
        )
        assert exif["Exif"][piexif.ExifIFD.ExifVersion] == b"0220"

    def test_kimeneti_meret_atmeretezesnel(self, tmp_path):
        source = _metaadat_nelkuli_forras(tmp_path, size=(400, 200))
        kimenet = _export(source, tmp_path, max_dimension=100)
        exif = piexif.load(str(kimenet))
        assert exif["Exif"][piexif.ExifIFD.PixelXDimension] == 100
        assert exif["Exif"][piexif.ExifIFD.PixelYDimension] == 50
        with Image.open(kimenet) as kep:
            assert kep.size == (100, 50)

    def test_kimeneti_meret_forgatasnal(self, tmp_path):
        source = _metaadat_nelkuli_forras(tmp_path, size=(80, 40))
        report = export_photos(
            [ExportItem(source, rotate_steps=1)], tmp_path / "out"
        )
        exif = piexif.load(str(report.exported[0]))
        assert exif["Exif"][piexif.ExifIFD.PixelXDimension] == 40
        assert exif["Exif"][piexif.ExifIFD.PixelYDimension] == 80

    def test_xmp_uj_csomag_a_mert_szerkezettel(self, tmp_path):
        xmp = _xmp(_export(_metaadat_nelkuli_forras(tmp_path), tmp_path))
        assert re.search(r'xmp:ModifyDate="\d{4}-\d\d-\d\dT', xmp)
        assert 'exif:DateTimeOriginal="2026-09-16T08:00:14' in xmp
        assert f"<rdf:li>{ALAIRAS}</rdf:li>" in xmp


class TestKamerasForras:
    """3084: a meglévő megmarad, a hiányzó pótolva, a dátum és a méret frissül."""

    def test_meglevo_mezoket_nem_ir_felul(self, tmp_path):
        exif = piexif.load(str(_export(_kameras_forras(tmp_path), tmp_path)))
        assert exif["0th"][piexif.ImageIFD.Software] == b"GIMP 2.8.14"
        assert exif["0th"][piexif.ImageIFD.Artist] == b"David C Searle"
        assert exif["Exif"][piexif.ExifIFD.ExifVersion] == b"0230"
        assert (
            exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2014:06:21 15:03:38"
        )

    def test_datetime_felulirva_az_export_idejevel(self, tmp_path):
        elotte = datetime.now()
        exif = piexif.load(str(_export(_kameras_forras(tmp_path), tmp_path)))
        ertek = exif["0th"][piexif.ImageIFD.DateTime]
        assert ertek != b"2014:09:09 15:40:30"
        assert _kulonbseg_mp(ertek, elotte) <= 5

    def test_kameras_exif_mezok_erintetlenek(self, tmp_path):
        exif = piexif.load(str(_export(_kameras_forras(tmp_path), tmp_path)))
        assert exif["0th"][piexif.ImageIFD.Make] == b"NIKON CORPORATION"
        assert exif["Exif"][piexif.ExifIFD.FNumber] == (32, 10)
        assert exif["Exif"][piexif.ExifIFD.ISOSpeedRatings] == 200

    def test_kimeneti_meret_a_hianyzo_mezo_hozzaadva(self, tmp_path):
        source = _kameras_forras(tmp_path, size=(400, 200))
        exif = piexif.load(str(_export(source, tmp_path, max_dimension=100)))
        assert exif["Exif"][piexif.ExifIFD.PixelXDimension] == 100
        assert exif["Exif"][piexif.ExifIFD.PixelYDimension] == 50

    def test_xmp_meglevo_megmarad_modifydate_frissul(self, tmp_path):
        xmp = _xmp(_export(_kameras_forras(tmp_path), tmp_path))
        assert "Contrast2012" in xmp and "-58" in xmp
        assert "70.0-200.0 mm f/2.8" in xmp
        assert "2014-08-13T22:19:41" not in xmp
        assert re.search(r"ModifyDate[>=\"]+\d{4}-\d\d-\d\dT", xmp)
        assert str(datetime.now().year) in xmp

    def test_xmp_exif_nevter_csak_a_ket_datum(self, tmp_path):
        xmp = _xmp(_export(_kameras_forras(tmp_path), tmp_path))
        assert "FNumber" not in xmp
        assert "DateTimeOriginal" in xmp

    def test_iptc_megmarad(self, tmp_path):
        kimenet = _export(_kameras_forras(tmp_path), tmp_path)
        with Image.open(kimenet) as kep:
            assert (getiptcinfo(kep) or {}).get((2, 120)) == "Rét".encode("utf-8")

    def test_a_kimenet_dekodolhato(self, tmp_path):
        with Image.open(_export(_kameras_forras(tmp_path), tmp_path)) as kep:
            kep.load()


class TestSzerkesztetlenMasolat:
    def test_szerkesztetlen_jpeg_export_bajthu_marad(self, tmp_path):
        source = _kameras_forras(tmp_path)
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert report.exported[0].read_bytes() == source.read_bytes()


class TestNemJpegForras:
    def test_png_forras_valtozatlan_kimenet_metaadat_nelkul(self, tmp_path):
        source = tmp_path / "kép.png"
        Image.new("RGB", (20, 10), "red").save(source)
        assert _xmp(_export(source, tmp_path)) is None


# --- a NAS-os mérőkészlet: mezőnkénti összevetés az eredeti Picasa exportjával

_NAS = Path("/mnt/nas/My Pictures")
_ESETEK = {
    "3229": _NAS / "3229-lanc-sorrend" / "01-keret-utan-szepia.jpg",
    "3084": _NAS / "3084-poszterizalas" / "Warm grasses by dcsearle.t21.jpg",
}
#: futásonként más, vagy a képzése nincs meg (16. C) 1.), vagy mutató
_KIHAGY = {
    ("0th", piexif.ImageIFD.DateTime),
    ("0th", piexif.ImageIFD.ExifTag),
    ("Exif", piexif.ExifIFD.ImageUniqueID),
    ("Exif", piexif.ExifIFD.InteroperabilityTag),
    # a 3229 forrás mtime-ja gépenként más — külön ellenőrizzük
    ("Exif", piexif.ExifIFD.DateTimeOriginal),
}


def _mezok(path):
    exif = piexif.load(str(path))
    return {
        (ifd, tag): ertek
        for ifd in ("0th", "Exif")
        for tag, ertek in exif[ifd].items()
        if (ifd, tag) not in _KIHAGY
    }


@pytest.mark.skipif(
    not all(p.is_file() for p in _ESETEK.values()),
    reason="a 3229/3084 NAS-os mérőkészlet nem elérhető",
)
@pytest.mark.parametrize("eset", sorted(_ESETEK))
def test_nas_exif_mezoi_egyeznek_az_eredeti_exportjaval(eset, tmp_path):
    forras = _ESETEK[eset]
    eredeti = forras.parent / "export" / forras.name
    if not eredeti.is_file():
        pytest.skip("az eredeti export nem elérhető")
    kimenet = _export(forras, tmp_path)
    mi, ok = _mezok(kimenet), _mezok(eredeti)
    with Image.open(kimenet) as kep:
        mi_meret = kep.size
    exif_mi = piexif.load(str(kimenet))["Exif"]
    # a kimeneti méret minden esetben a KIMENET saját mérete
    assert (
        exif_mi[piexif.ExifIFD.PixelXDimension],
        exif_mi[piexif.ExifIFD.PixelYDimension],
    ) == mi_meret
    # a 3229 eredeti exportja a lánc keretével nagyobb: méretet nem vetünk össze
    meret_kulcsok = {
        ("Exif", piexif.ExifIFD.PixelXDimension),
        ("Exif", piexif.ExifIFD.PixelYDimension),
    }
    for kulcs in set(ok) - (meret_kulcsok if eset == "3229" else set()):
        # #1642: az eredeti `Picasa` nevét a sajátunkra cseréljük
        vart = ALAIRAS.encode() if ok[kulcs] == b"Picasa" else ok[kulcs]
        assert mi.get(kulcs) == vart, kulcs
    # ami az eredetiben nincs, az nálunk se legyen (kivéve a mérethez tartozót)
    assert set(mi) - set(ok) <= meret_kulcsok
    eredeti_dto = piexif.load(str(eredeti))["Exif"][piexif.ExifIFD.DateTimeOriginal]
    assert exif_mi[piexif.ExifIFD.DateTimeOriginal] == eredeti_dto
