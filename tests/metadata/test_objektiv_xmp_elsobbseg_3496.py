"""Az „Objektív" sor elsőként az XMP `aux:Lens`-t mutatja (#3496).

## A mérés

`docs/specs/picasa-metaadat-tulajdonsagok.md` 9.14: a panel 255-ös sorát az
eredeti **először az XMP `aux:Lens`-ből** tölti — a `ytXMPReader` „első nyer"
alapon szúr be, és mindkét betöltő az objektív-elosztó (`0x00a35940`) ELŐTT
olvas XMP-t. Az elosztó „már megvan?" próbával kezd, tehát ha az XMP adott
értéket, a MakerNote-feloldás (Canon, Nikon) kimarad.

A mintakép (D7000, Lightroomon átment, csak XMP `aux:Lens = 70.0-200.0 mm
f/2.8`) a NAS-on él; itt a belőle készült kis tesztfájl áll helyette:
Nikon-gyártó, `LensModel` nélkül, csak XMP-vel.
"""

from __future__ import annotations

from unittest import mock

import pytest
from PIL import Image

from picasapy.metadata import reader
from picasapy.metadata.reader import read_exif_details

from test_canon_objektiv_makernote_3121 import _beallitasok, _tiff_canon

_D7000_LENS = "70.0-200.0 mm f/2.8"


def _xmp_attr(lens: str) -> bytes:
    """A Lightroom alakja: `aux:Lens` attribútumként az `rdf:Description`-ön."""
    return (
        '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
        ' <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        '  <rdf:Description rdf:about=""\n'
        '    xmlns:aux="http://ns.adobe.com/exif/1.0/aux/"\n'
        f'   aux:Lens="{lens}"/>\n'
        ' </rdf:RDF>\n'
        '</x:xmpmeta>\n'
        '<?xpacket end="w"?>'
    ).encode()


def _xmp_elem(lens: str) -> bytes:
    """A másik szabályos RDF-alak: `<aux:Lens>` gyerekelemként."""
    return (
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about=""'
        ' xmlns:aux="http://ns.adobe.com/exif/1.0/aux/">'
        f'<aux:Lens>{lens}</aux:Lens>'
        '</rdf:Description></rdf:RDF></x:xmpmeta>'
    ).encode()


def _jpeg(path, *, exif: bytes | None = None, xmp: bytes | None = None):
    kwargs = {}
    if exif is not None:
        kwargs["exif"] = b"Exif\x00\x00" + exif
    if xmp is not None:
        kwargs["xmp"] = xmp
    Image.new("RGB", (8, 6), "red").save(path, "JPEG", **kwargs)
    return path


@pytest.fixture
def canon_35mm() -> tuple[int, ...]:
    return _beallitasok(e22=11, e23=35, e24=35, e25=1, e26=64)


class TestAzXmpElsobbsege:
    def test_d7000_minta_csak_xmp_lens(self, tmp_path) -> None:
        """A mért eset: Nikon, `LensModel` nélkül — ma üres volt a sor."""
        kep = _jpeg(
            tmp_path / "d7000.jpg",
            exif=_tiff_canon(_beallitasok(), make="NIKON CORPORATION"),
            xmp=_xmp_attr(_D7000_LENS),
        )
        assert read_exif_details(kep).lens == _D7000_LENS

    def test_canon_kep_aux_lensszel_az_xmp_szoveget_mutatja(
        self, tmp_path, canon_35mm
    ) -> None:
        kep = _jpeg(
            tmp_path / "canon.jpg",
            exif=_tiff_canon(canon_35mm),
            xmp=_xmp_attr("EF35mm f/2 (XMP)"),
        )
        assert read_exif_details(kep).lens == "EF35mm f/2 (XMP)"

    def test_xmp_mellett_a_makernote_ag_nem_fut(self, tmp_path, canon_35mm) -> None:
        """Az elosztó „már megvan?" próbája: a MakerNote-ot meg sem nyitja."""
        kep = _jpeg(
            tmp_path / "canon.jpg",
            exif=_tiff_canon(canon_35mm),
            xmp=_xmp_attr("EF35mm f/2 (XMP)"),
        )
        with mock.patch.object(reader, "tiff_blokk") as blokk:
            assert read_exif_details(kep).lens == "EF35mm f/2 (XMP)"
        blokk.assert_not_called()

    def test_az_xmp_a_lensmodelt_is_megelozi(self, tmp_path, canon_35mm) -> None:
        tiff = _tiff_canon(canon_35mm, make="FUJIFILM", lens_model="XF35mmF2")
        kep = _jpeg(tmp_path / "fuji.jpg", exif=tiff, xmp=_xmp_attr("XMP név"))
        assert read_exif_details(kep).lens == "XMP név"

    def test_elem_alak_is_olvasodik(self, tmp_path) -> None:
        kep = _jpeg(tmp_path / "x.jpg", xmp=_xmp_elem(_D7000_LENS))
        assert read_exif_details(kep).lens == _D7000_LENS


class TestHaNincsHasznalhatoXmp:
    @pytest.mark.parametrize("ertek", ["", "   "])
    def test_ures_aux_lens_a_makernote_ra_esik_vissza(
        self, tmp_path, canon_35mm, ertek
    ) -> None:
        kep = _jpeg(
            tmp_path / "canon.jpg",
            exif=_tiff_canon(canon_35mm),
            xmp=_xmp_attr(ertek),
        )
        assert read_exif_details(kep).lens == "Canon EF 35mm f/2"

    def test_aux_lens_nelkuli_xmp_nem_zavar(self, tmp_path, canon_35mm) -> None:
        xmp = _xmp_attr("x").replace(b' aux:Lens="x"', b"")
        kep = _jpeg(tmp_path / "canon.jpg", exif=_tiff_canon(canon_35mm), xmp=xmp)
        assert read_exif_details(kep).lens == "Canon EF 35mm f/2"

    def test_serult_xmp_nem_dob(self, tmp_path, canon_35mm) -> None:
        kep = _jpeg(
            tmp_path / "canon.jpg",
            exif=_tiff_canon(canon_35mm),
            xmp=b"<x:xmpmeta aux:Lens=",
        )
        assert read_exif_details(kep).lens == "Canon EF 35mm f/2"

    def test_mas_nevter_lens_attributuma_nem_szamit(self, tmp_path) -> None:
        xmp = _xmp_attr("x").replace(
            b"http://ns.adobe.com/exif/1.0/aux/", b"urn:mas:nevter")
        kep = _jpeg(tmp_path / "x.jpg", xmp=xmp)
        assert read_exif_details(kep).lens is None
