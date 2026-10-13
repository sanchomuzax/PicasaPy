"""#4579: Fájl dátuma, CCD szélessége, Rekesz, JPEG minőség és Személycímkék
sor a Tulajdonságok-panelen (spec `picasa-metaadat-tulajdonsagok.md` 17.)."""

from types import SimpleNamespace

import piexif
import pytest
from PIL import Image
from PySide6.QtCore import QLocale

from picasapy.app.formatting import exif_entries, properties_entries


def _tr(text):
    return text


def _photo(folder, name, *, taken_at=None, mtime_ns=1_700_000_000_000_000_000):
    return SimpleNamespace(
        name=name,
        folder_path=str(folder),
        size=1024,
        width=32,
        height=32,
        taken_at=taken_at,
        kind="photo",
        keywords=(),
        sort_mtime_ns=mtime_ns,
    )


def _jpeg(path, exif=None, **kwargs):
    kep = Image.new("RGB", (32, 32), "red")
    if exif is not None:
        kwargs["exif"] = piexif.dump(exif)
    kep.save(path, "JPEG", **kwargs)
    return path


def _ccd_exif(unit=2, xres=(3888000, 876), pixel=(3888, 2592), interop=None):
    exif_ifd = {
        piexif.ExifIFD.PixelXDimension: pixel[0],
        piexif.ExifIFD.PixelYDimension: pixel[1],
    }
    if unit is not None:
        exif_ifd[piexif.ExifIFD.FocalPlaneResolutionUnit] = unit
    if xres is not None:
        exif_ifd[piexif.ExifIFD.FocalPlaneXResolution] = xres
    sajat = {"0th": {}, "Exif": exif_ifd, "GPS": {}, "1st": {}, "Interop": {}}
    if interop is not None:
        sajat["Interop"] = {
            0x1001: interop[0],
            0x1002: interop[1],
        }
    return sajat


def _ertekek(folder, name, **kw):
    photo = _photo(folder, name, **kw)
    return exif_entries(photo, QLocale("en"), _tr)


def _dict(entries):
    return dict(entries)


class TestCcdSzelesseg:
    def test_mintaertek_hold_inch(self, tmp_path):
        _jpeg(tmp_path / "a.jpg", _ccd_exif())
        assert _dict(_ertekek(tmp_path, "a.jpg"))["CCD Width"] == "22.3"

    def test_interop_elony_a_pixelx_ellen(self, tmp_path, monkeypatch):
        # a piexif nem ismeri az Interop 0x1001/0x1002 címkét: tanítjuk
        for kod, nev in ((0x1001, "RelatedImageWidth"), (0x1002, "RelatedImageLength")):
            monkeypatch.setitem(
                piexif.TAGS["Interop"], kod, {"name": nev, "type": piexif.TYPES.Long}
            )
        # Interop 1944x1296 fele méret -> fele CCD
        _jpeg(tmp_path / "a.jpg", _ccd_exif(interop=(1944, 1296)))
        assert _dict(_ertekek(tmp_path, "a.jpg"))["CCD Width"] == "11.1"

    @pytest.mark.parametrize(
        ("unit", "vart"),
        [(3, "8.76"), (4, "0.876"), (5, "0.000876")],
    )
    def test_egysegek(self, tmp_path, unit, vart):
        # 3888 * egyseg_mm / (3888000/876) -> egyseg * 0.876
        _jpeg(tmp_path / "a.jpg", _ccd_exif(unit=unit))
        szoveg = _dict(_ertekek(tmp_path, "a.jpg"))["CCD Width"]
        assert szoveg == {3: "8.76", 4: "0.876", 5: "0.000876"}[unit]
        assert vart

    def test_centi_egyseg_is_25_4(self, tmp_path):
        _jpeg(tmp_path / "a.jpg", _ccd_exif(unit=1))
        assert _dict(_ertekek(tmp_path, "a.jpg"))["CCD Width"] == "22.3"

    @pytest.mark.parametrize(
        "exif",
        [
            _ccd_exif(unit=None),
            _ccd_exif(unit=6),
            _ccd_exif(xres=None),
            _ccd_exif(xres=(0, 1)),
            _ccd_exif(xres=(5, 0)),
            _ccd_exif(pixel=(0, 2592)),
            _ccd_exif(pixel=(3888, 0)),
        ],
    )
    def test_nincs_sor(self, tmp_path, exif):
        _jpeg(tmp_path / "a.jpg", exif)
        assert "CCD Width" not in _dict(_ertekek(tmp_path, "a.jpg"))

    def test_sorrend_a_35mm_utan_az_expozicio_elott(self, tmp_path):
        exif = _ccd_exif()
        exif["Exif"][piexif.ExifIFD.FocalLengthIn35mmFilm] = 50
        exif["Exif"][piexif.ExifIFD.ExposureTime] = (1, 100)
        _jpeg(tmp_path / "a.jpg", exif)
        cimkek = [c for c, _ in _ertekek(tmp_path, "a.jpg")]
        assert (
            cimkek.index("Focal Length in 35mm Film")
            < cimkek.index("CCD Width")
            < cimkek.index("Exposure Time")
        )


class TestRekesz:
    @pytest.mark.parametrize(
        ("racionalis", "vart"),
        [((497, 100), "4.97"), ((5, 1), "5"), ((1125, 1000), "1.13")],
    )
    def test_nyers_apex_g3(self, tmp_path, racionalis, vart):
        exif = {"0th": {}, "Exif": {piexif.ExifIFD.ApertureValue: racionalis}}
        _jpeg(tmp_path / "a.jpg", exif)
        assert _dict(_ertekek(tmp_path, "a.jpg"))["Aperture"] == vart

    def test_nulla_nevezo_nincs_sor(self, tmp_path):
        exif = {"0th": {}, "Exif": {piexif.ExifIFD.ApertureValue: (5, 0)}}
        _jpeg(tmp_path / "a.jpg", exif)
        assert "Aperture" not in _dict(_ertekek(tmp_path, "a.jpg"))

    def test_az_expozicio_es_az_f_szam_kozott(self, tmp_path):
        exif = {
            "0th": {},
            "Exif": {
                piexif.ExifIFD.ExposureTime: (1, 100),
                piexif.ExifIFD.ApertureValue: (5, 1),
                piexif.ExifIFD.FNumber: (56, 10),
            },
        }
        _jpeg(tmp_path / "a.jpg", exif)
        cimkek = [c for c, _ in _ertekek(tmp_path, "a.jpg")]
        assert (
            cimkek.index("Exposure Time")
            < cimkek.index("Aperture")
            < cimkek.index("F Number")
        )


class TestJpegMinoseg:
    def test_sor_a_belyegkep_es_a_kulcsszavak_kozott(self, tmp_path):
        exif = {"0th": {}, "Exif": {}, "1st": {}, "thumbnail": _kis_jpeg()}
        _jpeg(tmp_path / "a.jpg", exif, quality=90, subsampling=2)
        photo = _photo(tmp_path, "a.jpg")
        photo.keywords = "alma"
        cimkek = [c for c, _ in exif_entries(photo, QLocale("en"), _tr)]
        assert (
            cimkek.index("Embedded Thumbnail")
            < cimkek.index("JPEG Quality")
            < cimkek.index("Keywords")
        )
        assert _dict(exif_entries(photo, QLocale("en"), _tr))[
            "JPEG Quality"
        ] == "90 (411)"

    def test_nem_jpeg_nincs_sor(self, tmp_path):
        Image.new("RGB", (8, 8)).save(tmp_path / "a.png", "PNG")
        assert "JPEG Quality" not in _dict(_ertekek(tmp_path, "a.png"))


def _kis_jpeg():
    import io

    buf = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buf, "JPEG")
    return buf.getvalue()


class TestFajlDatuma:
    def test_a_modified_date_utan_az_orientation_elott(self, tmp_path):
        exif = {
            "0th": {
                piexif.ImageIFD.DateTime: b"2020:01:02 03:04:05",
                piexif.ImageIFD.Orientation: 6,
            },
            "Exif": {},
        }
        _jpeg(tmp_path / "a.jpg", exif)
        photo = _photo(tmp_path, "a.jpg", taken_at="2021-05-06T07:08:09")
        entries = exif_entries(photo, QLocale("en"), _tr)
        cimkek = [c for c, _ in entries]
        assert (
            cimkek.index("Modified Date")
            < cimkek.index("File Date")
            < cimkek.index("Orientation")
        )

    def test_ertek_a_photo_date_masodperccel(self, tmp_path):
        _jpeg(tmp_path / "a.jpg")
        photo = _photo(tmp_path, "a.jpg", taken_at="2021-05-06T17:08:09")
        szoveg = _dict(exif_entries(photo, QLocale("hu"), _tr))["File Date"]
        assert "17:08:09" in szoveg
        assert "2021" in szoveg

    def test_ejfelkor_csak_datum(self, tmp_path):
        _jpeg(tmp_path / "a.jpg")
        photo = _photo(tmp_path, "a.jpg", taken_at="2021-05-06T00:00:00")
        szoveg = _dict(exif_entries(photo, QLocale("hu"), _tr))["File Date"]
        assert ":" not in szoveg
        assert "2021" in szoveg

    def test_fajl_hianyaban_nincs_sor(self, tmp_path):
        photo = _photo(tmp_path, "nincs.jpg", taken_at="2021-05-06T17:08:09")
        assert "File Date" not in _dict(exif_entries(photo, QLocale("en"), _tr))

    def test_fajlido_tartalek(self, tmp_path):
        _jpeg(tmp_path / "a.jpg")
        photo = _photo(tmp_path, "a.jpg", taken_at=None)
        assert "File Date" in _dict(exif_entries(photo, QLocale("en"), _tr))

    def test_tortmasodperces_fajlido_is_kap_sort(self, tmp_path):
        """A `photo_date` ISO-ja `.mikroszekundum`-ot kap; a sor nem tűnhet el."""
        _jpeg(tmp_path / "a.jpg")
        egesz = _photo(tmp_path, "a.jpg", mtime_ns=1_700_000_000_000_000_000)
        tort = _photo(tmp_path, "a.jpg", mtime_ns=1_700_000_000_123_456_789)
        vart = _dict(exif_entries(egesz, QLocale("en"), _tr))["File Date"]
        assert _dict(exif_entries(tort, QLocale("en"), _tr))["File Date"] == vart

    def test_nulla_fajlido_nincs_sor(self, tmp_path):
        """A 0 ns „nincs adat", nem 1970."""
        _jpeg(tmp_path / "a.jpg")
        photo = _photo(tmp_path, "a.jpg", mtime_ns=0)
        assert "File Date" not in _dict(exif_entries(photo, QLocale("en"), _tr))


def _ini(folder, szoveg):
    (folder / ".picasa.ini").write_text(szoveg, encoding="utf-8")


class TestSzemelycimkek:
    def _ini_arcokkal(self, folder, nevek):
        contacts = "[Contacts2]\n" + "".join(
            f"{i:016x}={n};;\n" for i, n in enumerate(nevek, start=1)
        )
        faces = ";".join(
            f"rect64(1000000000000000),{i:016x}" for i, _ in enumerate(nevek, start=1)
        )
        _ini(folder, f"{contacts}\n[a.jpg]\nfaces={faces}\n")

    def test_ini_nevei_a_kulcsszavak_utan_a_gps_elott(self, tmp_path):
        exif = {"0th": {}, "Exif": {}, "GPS": {
            piexif.GPSIFD.GPSLatitudeRef: b"N",
            piexif.GPSIFD.GPSLatitude: ((47, 1), (30, 1), (0, 1)),
            piexif.GPSIFD.GPSLongitudeRef: b"E",
            piexif.GPSIFD.GPSLongitude: ((19, 1), (0, 1), (0, 1)),
        }}
        _jpeg(tmp_path / "a.jpg", exif)
        self._ini_arcokkal(tmp_path, ["Kata"])
        photo = _photo(tmp_path, "a.jpg")
        photo.keywords = "alma"
        entries = exif_entries(photo, QLocale("en"), _tr)
        cimkek = [c for c, _ in entries]
        assert (
            cimkek.index("Keywords")
            < cimkek.index("People Tags")
            < cimkek.index("GPS Latitude")
        )

    def test_tobb_nev_vesszovel(self, tmp_path):
        _jpeg(tmp_path / "a.jpg")
        self._ini_arcokkal(tmp_path, ["Kata", "Bela"])
        szoveg = _dict(_ertekek(tmp_path, "a.jpg"))["People Tags"]
        assert szoveg == "Kata, Bela"

    def test_azonos_nev_n_szer(self, tmp_path):
        _jpeg(tmp_path / "a.jpg")
        _ini(
            tmp_path,
            "[Contacts2]\n0000000000000001=Kata;;\n\n"
            "[a.jpg]\nfaces=rect64(1000000000000000),0000000000000001;"
            "rect64(2000000000000000),0000000000000001\n",
        )
        assert _dict(_ertekek(tmp_path, "a.jpg"))["People Tags"] == "Kata (2)"

    def test_ures_nev_kimarad(self, tmp_path):
        _jpeg(tmp_path / "a.jpg")
        self._ini_arcokkal(tmp_path, ["Kata"])
        _ini(
            tmp_path,
            "[Contacts2]\n0000000000000001=Kata;;\n\n"
            "[a.jpg]\nfaces=rect64(1000000000000000),ffffffffffffffff\n",
        )
        assert "People Tags" not in _dict(_ertekek(tmp_path, "a.jpg"))

    def test_xmp_tartalek_ha_nincs_ini(self, tmp_path):
        xmp = (
            b'<x:xmpmeta xmlns:x="adobe:ns:meta/" '
            b'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            b'xmlns:mwg-rs="http://www.metadataworkinggroup.com/schemas/regions/" '
            b'xmlns:stArea="http://ns.adobe.com/xap/1.0/sType/Area#">'
            b'<rdf:RDF><rdf:Description><mwg-rs:Regions rdf:parseType="Resource">'
            b"<mwg-rs:RegionList><rdf:Bag>"
            b'<rdf:li rdf:parseType="Resource"><mwg-rs:Name>Eszter</mwg-rs:Name>'
            b'<mwg-rs:Area stArea:x="0.5" stArea:y="0.5" stArea:w="0.2" '
            b'stArea:h="0.2"/></rdf:li></rdf:Bag></mwg-rs:RegionList>'
            b"</mwg-rs:Regions></rdf:Description></rdf:RDF></x:xmpmeta>"
        )
        kep = Image.new("RGB", (16, 16))
        kep.save(tmp_path / "a.jpg", "JPEG", xmp=xmp)
        assert _dict(_ertekek(tmp_path, "a.jpg"))["People Tags"] == "Eszter"

    def test_ini_felulirja_az_xmp_t(self, tmp_path):
        self.test_xmp_tartalek_ha_nincs_ini(tmp_path)
        self._ini_arcokkal(tmp_path, ["Kata"])
        assert _dict(_ertekek(tmp_path, "a.jpg"))["People Tags"] == "Kata"

    def test_kozponti_contacts_xml_is_feloldja_a_nevet(self, tmp_path):
        """A `faces=` azonosítója csak a központi `contacts.xml`-ben van."""
        _jpeg(tmp_path / "a.jpg")
        _ini(
            tmp_path,
            "[a.jpg]\nfaces=rect64(1000000000000000),00000000000000aa\n",
        )
        kozponti = tmp_path / "kozpont" / "contacts.xml"
        kozponti.parent.mkdir()
        kozponti.write_text(
            '<contacts><contact id="00000000000000aa" name="Kata" '
            'local_contact="1" modified_time="2020-01-01T00:00:00+00:00"/>'
            "</contacts>",
            encoding="utf-8",
        )
        photo = _photo(tmp_path, "a.jpg")
        ertek = dict(
            exif_entries(photo, QLocale("en"), _tr, contacts_xml=kozponti)
        )
        assert ertek["People Tags"] == "Kata"
        assert "People Tags" not in _dict(_ertekek(tmp_path, "a.jpg"))

    def test_properties_entries_tartalmazza(self, tmp_path):
        _jpeg(tmp_path / "a.jpg")
        self._ini_arcokkal(tmp_path, ["Kata"])
        entries = properties_entries(
            _photo(tmp_path, "a.jpg"), QLocale("en"), _tr
        )
        assert ("People Tags", "Kata") in entries
