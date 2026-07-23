"""XMP-export (issue #27): MWG-RS arcrégiók + HierarchicalSubject.

A cél a digiKam/Lightroom-kompatibilis sidecar — az adat soha ne ragadjon
halott formátumba (UX-alapelv 5). A tesztek a formátum HELYESSÉGÉT nézik
(nem csak a „lefutott-e"): a kimenet jól formált XML, a normalizált
arckoordináták a MWG-konvenció szerinti KÖZÉPPONT-alapúak, és a kritikus
névterek/mértékegységek jelen vannak.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from picasapy.export.xmp import (
    XmpImageMetadata,
    XmpRegion,
    build_sidecar_from_picasa,
    build_xmp,
    region_from_rect64,
    write_sidecar,
)
from picasapy.ini.rect64 import Rect64

# A parse-oláshoz kivágott x:xmpmeta elem (a body a BOM + xpacket-PI burokban
# él, amit az ElementTree str-ként nem mindig nyel le — a gyökér elemet
# önmagában parse-oljuk).
_NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "lr": "http://ns.adobe.com/lightroom/1.0/",
    "mwg-rs": "http://www.metadataworkinggroup.com/schemas/regions/",
    "stArea": "http://ns.adobe.com/xmp/sType/Area#",
    "stDim": "http://ns.adobe.com/xap/1.0/sType/Dimensions#",
    "x": "adobe:ns:meta/",
}


def _parse(xmp: str) -> ET.Element:
    start = xmp.index("<x:xmpmeta")
    end = xmp.index("</x:xmpmeta>") + len("</x:xmpmeta>")
    return ET.fromstring(xmp[start:end])


class TestRegionFromRect64:
    def test_center_and_size(self):
        # left/top/right/bottom = 0.4/0.325/0.5/0.475 → w=0.1, h=0.15,
        # középpont = (0.45, 0.4)
        rect = Rect64(left=0.4, top=0.325, right=0.5, bottom=0.475)
        region = region_from_rect64(rect, "Anna")
        assert region.name == "Anna"
        assert region.w == pytest.approx(0.1)
        assert region.h == pytest.approx(0.15)
        assert region.x == pytest.approx(0.45)
        assert region.y == pytest.approx(0.4)
        assert region.kind == "Face"


class TestBuildXmpWellFormed:
    def test_output_is_parseable_and_wrapped(self):
        xmp = build_xmp(XmpImageMetadata(keywords=("tenger",)))
        assert xmp.startswith("﻿<?xpacket begin=")
        assert "<?xpacket end=" in xmp
        assert "<x:xmpmeta" in xmp
        # jól formált XML
        root = _parse(xmp)
        assert root.tag == "{adobe:ns:meta/}xmpmeta"

    def test_empty_metadata_still_valid(self):
        xmp = build_xmp(XmpImageMetadata())
        root = _parse(xmp)
        # üres leírás is jól formált marad
        desc = root.find(".//rdf:Description", _NS)
        assert desc is not None


class TestKeywords:
    def test_dc_subject_bag(self):
        xmp = build_xmp(XmpImageMetadata(keywords=("tenger", "nyár")))
        root = _parse(xmp)
        items = root.findall(".//dc:subject/rdf:Bag/rdf:li", _NS)
        assert [i.text for i in items] == ["tenger", "nyár"]

    def test_no_keywords_no_subject(self):
        xmp = build_xmp(XmpImageMetadata(caption="szia"))
        root = _parse(xmp)
        assert root.find(".//dc:subject", _NS) is None


class TestCaption:
    def test_description_altlang(self):
        xmp = build_xmp(XmpImageMetadata(caption="Nyaralás 2015"))
        root = _parse(xmp)
        li = root.find(".//dc:description/rdf:Alt/rdf:li", _NS)
        assert li is not None
        assert li.text == "Nyaralás 2015"
        assert li.get("{http://www.w3.org/XML/1998/namespace}lang") == "x-default"


class TestHierarchicalSubject:
    def test_people_prefix(self):
        meta = XmpImageMetadata(hierarchical=("People|Anna", "tenger"))
        xmp = build_xmp(meta)
        root = _parse(xmp)
        items = root.findall(".//lr:hierarchicalSubject/rdf:Bag/rdf:li", _NS)
        assert [i.text for i in items] == ["People|Anna", "tenger"]


class TestRegions:
    def test_region_list_with_dimensions(self):
        region = XmpRegion(name="Anna", x=0.45, y=0.4, w=0.1, h=0.15)
        meta = XmpImageMetadata(regions=(region,), dimensions=(4000, 3000))
        xmp = build_xmp(meta)
        root = _parse(xmp)

        dims = root.find(".//mwg-rs:Regions/mwg-rs:AppliedToDimensions", _NS)
        assert dims is not None
        assert dims.get("{http://ns.adobe.com/xap/1.0/sType/Dimensions#}w") == "4000"
        assert dims.get("{http://ns.adobe.com/xap/1.0/sType/Dimensions#}h") == "3000"
        assert dims.get("{http://ns.adobe.com/xap/1.0/sType/Dimensions#}unit") == "pixel"

        li = root.find(".//mwg-rs:RegionList/rdf:Bag/rdf:li", _NS)
        assert li.find("mwg-rs:Name", _NS).text == "Anna"
        assert li.find("mwg-rs:Type", _NS).text == "Face"
        area = li.find("mwg-rs:Area", _NS)
        base = "{http://ns.adobe.com/xmp/sType/Area#}"
        assert area.get(base + "x") == "0.45"
        assert area.get(base + "y") == "0.4"
        assert area.get(base + "w") == "0.1"
        assert area.get(base + "h") == "0.15"
        assert area.get(base + "unit") == "normalized"

    def test_regions_without_dimensions_omits_appliedto(self):
        region = XmpRegion(name="Anna", x=0.45, y=0.4, w=0.1, h=0.15)
        xmp = build_xmp(XmpImageMetadata(regions=(region,)))
        root = _parse(xmp)
        assert root.find(".//mwg-rs:AppliedToDimensions", _NS) is None
        assert root.find(".//mwg-rs:RegionList", _NS) is not None


class TestEscaping:
    def test_special_chars_escaped(self):
        meta = XmpImageMetadata(
            keywords=("A & B", "x<y"), caption='idéz "ő" & <jel>'
        )
        xmp = build_xmp(meta)
        # nyers escape a szövegben
        assert "&amp;" in xmp
        assert "&lt;" in xmp
        # és mégis jól formált marad
        root = _parse(xmp)
        items = [i.text for i in root.findall(".//dc:subject/rdf:Bag/rdf:li", _NS)]
        assert items == ["A & B", "x<y"]


class TestBuildSidecarFromPicasa:
    def test_faces_and_keywords_combined(self):
        rect = Rect64(left=0.4, top=0.325, right=0.5, bottom=0.475)
        xmp = build_sidecar_from_picasa(
            keywords=("tenger",),
            caption="Nyár",
            faces=((rect, "Anna"),),
            dimensions=(4000, 3000),
        )
        root = _parse(xmp)
        # lapos dc:subject: kulcsszó + arcnév
        flat = [i.text for i in root.findall(".//dc:subject/rdf:Bag/rdf:li", _NS)]
        assert "tenger" in flat
        assert "Anna" in flat
        # hierarchikus: People|Anna
        hier = [
            i.text
            for i in root.findall(".//lr:hierarchicalSubject/rdf:Bag/rdf:li", _NS)
        ]
        assert "People|Anna" in hier
        # régió is jelen
        name = root.find(".//mwg-rs:RegionList/rdf:Bag/rdf:li/mwg-rs:Name", _NS)
        assert name.text == "Anna"

    def test_unnamed_face_skipped(self):
        rect = Rect64(left=0.1, top=0.1, right=0.2, bottom=0.2)
        xmp = build_sidecar_from_picasa(faces=((rect, ""),))
        root = _parse(xmp)
        assert root.find(".//mwg-rs:RegionList", _NS) is None

    def test_dedup_preserves_order(self):
        xmp = build_sidecar_from_picasa(
            keywords=("tenger", "tenger", "nyár"),
        )
        root = _parse(xmp)
        flat = [i.text for i in root.findall(".//dc:subject/rdf:Bag/rdf:li", _NS)]
        assert flat == ["tenger", "nyár"]


class TestWriteSidecar:
    def test_appends_xmp_extension(self, tmp_path):
        image = tmp_path / "kép.jpg"
        image.write_bytes(b"\xff\xd8\xff\xd9")
        xmp = build_xmp(XmpImageMetadata(keywords=("tenger",)))
        out = write_sidecar(image, xmp)
        assert out.name == "kép.jpg.xmp"
        assert out.read_text(encoding="utf-8") == xmp
