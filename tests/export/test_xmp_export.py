"""Fotó-szintű XMP sidecar-export a `.picasa.ini`-ből (issue #27).

A tiszta XMP-építő fölötti réteg: valós fotó + melléírt `.picasa.ini`
(kulcsszavak, felirat, `faces=` + `[Contacts2]`) → digiKam-kompatibilis
`.xmp` sidecar. A tesztek a tényleges KIMENETET nézik (nem csak a lefutást).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from picasapy.export.xmp_export import (
    build_sidecar_for_photo,
    export_sidecar_for_photo,
    export_sidecars,
)
from picasapy.ini.faces import UNIDENTIFIED_CONTACT
from picasapy.ini.rect64 import Rect64, encode_rect64
from picasapy.scanner import PICASA_INI_NAME
from support.jpeg_factory import make_jpeg

_NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "lr": "http://ns.adobe.com/lightroom/1.0/",
    "mwg-rs": "http://www.metadataworkinggroup.com/schemas/regions/",
    "stDim": "http://ns.adobe.com/xap/1.0/sType/Dimensions#",
}


def _parse(xmp: str) -> ET.Element:
    start = xmp.index("<x:xmpmeta")
    end = xmp.index("</x:xmpmeta>") + len("</x:xmpmeta>")
    return ET.fromstring(xmp[start:end])


def _write_ini(folder, name: str, body: str) -> None:
    (folder / PICASA_INI_NAME).write_text(body, encoding="utf-8")


def _face_entry(rect: Rect64, contact_id: str) -> str:
    return f"rect64({encode_rect64(rect)}),{contact_id};"


class TestBuildSidecarForPhoto:
    def test_keywords_caption_and_named_face(self, tmp_path):
        image = make_jpeg(tmp_path / "kép.jpg", size=(4000, 3000))
        rect = Rect64(left=0.4, top=0.325, right=0.5, bottom=0.475)
        body = (
            f"[{image.name}]\n"
            "keywords=tenger,nyár\n"
            "caption=Nyaralás\n"
            f"faces={_face_entry(rect, '1234abcd')}\n"
            "[Contacts2]\n"
            "1234abcd=Anna;;\n"
        )
        _write_ini(tmp_path, image.name, body)

        xmp = build_sidecar_for_photo(image)
        assert xmp is not None
        root = _parse(xmp)

        flat = [i.text for i in root.findall(".//dc:subject/rdf:Bag/rdf:li", _NS)]
        assert "tenger" in flat and "nyár" in flat and "Anna" in flat
        hier = [
            i.text
            for i in root.findall(".//lr:hierarchicalSubject/rdf:Bag/rdf:li", _NS)
        ]
        assert "People|Anna" in hier
        name = root.find(".//mwg-rs:RegionList/rdf:Bag/rdf:li/mwg-rs:Name", _NS)
        assert name.text == "Anna"
        # a dimenzió a kép fejlécéből jött
        dims = root.find(".//mwg-rs:AppliedToDimensions", _NS)
        base = "{http://ns.adobe.com/xap/1.0/sType/Dimensions#}"
        assert dims.get(base + "w") == "4000"
        assert dims.get(base + "h") == "3000"

    def test_no_ini_returns_none(self, tmp_path):
        image = make_jpeg(tmp_path / "kép.jpg")
        assert build_sidecar_for_photo(image) is None

    def test_section_without_exportable_data_returns_none(self, tmp_path):
        image = make_jpeg(tmp_path / "kép.jpg")
        _write_ini(tmp_path, image.name, f"[{image.name}]\nstar=yes\n")
        assert build_sidecar_for_photo(image) is None

    def test_unidentified_face_no_region_but_keywords_kept(self, tmp_path):
        image = make_jpeg(tmp_path / "kép.jpg")
        rect = Rect64(left=0.1, top=0.1, right=0.2, bottom=0.2)
        body = (
            f"[{image.name}]\n"
            "keywords=tenger\n"
            f"faces={_face_entry(rect, UNIDENTIFIED_CONTACT)}\n"
        )
        _write_ini(tmp_path, image.name, body)
        xmp = build_sidecar_for_photo(image)
        assert xmp is not None
        root = _parse(xmp)
        assert root.find(".//mwg-rs:RegionList", _NS) is None
        flat = [i.text for i in root.findall(".//dc:subject/rdf:Bag/rdf:li", _NS)]
        assert flat == ["tenger"]


class TestExportSidecarForPhoto:
    def test_writes_sidecar_file(self, tmp_path):
        image = make_jpeg(tmp_path / "kép.jpg")
        _write_ini(tmp_path, image.name, f"[{image.name}]\nkeywords=tenger\n")
        out = export_sidecar_for_photo(image)
        assert out is not None
        assert out.name == "kép.jpg.xmp"
        assert out.exists()
        assert "tenger" in out.read_text(encoding="utf-8")

    def test_returns_none_without_data(self, tmp_path):
        image = make_jpeg(tmp_path / "kép.jpg")
        assert export_sidecar_for_photo(image) is None
        assert not (tmp_path / "kép.jpg.xmp").exists()


class TestExportSidecars:
    def test_batch_skips_dataless_photos(self, tmp_path):
        with_data = make_jpeg(tmp_path / "van.jpg")
        without = make_jpeg(tmp_path / "nincs.jpg")
        body = (
            f"[{with_data.name}]\nkeywords=tenger\n"
            f"[{without.name}]\nstar=yes\n"
        )
        _write_ini(tmp_path, with_data.name, body)

        written = export_sidecars([with_data, without])
        assert len(written) == 1
        assert written[0].name == "van.jpg.xmp"
