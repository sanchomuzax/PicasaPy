"""XMP sidecar-export: MWG-RS arc-régiók + hierarchikus címkék (#27)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from picasapy.ini.rect64 import Rect64
from picasapy.metadata import (
    FaceRegion,
    apply_orientation,
    build_xmp,
    sidecar_path,
    write_sidecar,
)

_NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "mwg-rs": "http://www.metadataworkinggroup.com/schemas/regions/",
    "stArea": "http://ns.adobe.com/xmp/sType/Area#",
    "stDim": "http://ns.adobe.com/xap/1.0/sType/Dimensions#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "lr": "http://ns.adobe.com/lightroom/1.0/",
}


def _parse(xmp: str) -> ET.Element:
    return ET.fromstring(xmp)


class TestFaceRegion:
    def test_region_area_matches_rect(self):
        rect = Rect64(left=0.2, top=0.3, right=0.4, bottom=0.5)
        xmp = build_xmp(
            image_width=1000,
            image_height=2000,
            faces=(FaceRegion(name="Kovács Anna", rect=rect),),
        )
        root = _parse(xmp)
        area = root.find(".//mwg-rs:Area", _NS)
        assert area is not None
        assert float(area.get("{%s}x" % _NS["stArea"])) == pytest.approx(0.3)
        assert float(area.get("{%s}y" % _NS["stArea"])) == pytest.approx(0.4)
        assert float(area.get("{%s}w" % _NS["stArea"])) == pytest.approx(0.2)
        assert float(area.get("{%s}h" % _NS["stArea"])) == pytest.approx(0.2)
        assert area.get("{%s}unit" % _NS["stArea"]) == "normalized"

        name_el = root.find(".//mwg-rs:Name", _NS)
        type_el = root.find(".//mwg-rs:Type", _NS)
        assert name_el is not None and name_el.text == "Kovács Anna"
        assert type_el is not None and type_el.text == "Face"

    def test_applied_to_dimensions(self):
        rect = Rect64(left=0.0, top=0.0, right=0.1, bottom=0.1)
        xmp = build_xmp(
            image_width=1920,
            image_height=1080,
            faces=(FaceRegion(name="X", rect=rect),),
        )
        root = _parse(xmp)
        dims = root.find(".//mwg-rs:AppliedToDimensions", _NS)
        assert dims is not None
        assert dims.get("{%s}w" % _NS["stDim"]) == "1920"
        assert dims.get("{%s}h" % _NS["stDim"]) == "1080"
        assert dims.get("{%s}unit" % _NS["stDim"]) == "pixel"

    def test_no_faces_no_regions_block(self):
        xmp = build_xmp(image_width=100, image_height=100)
        root = _parse(xmp)
        assert root.find(".//mwg-rs:Regions", _NS) is None

    def test_multiple_faces(self):
        rects = (
            FaceRegion(name="A", rect=Rect64(0.0, 0.0, 0.1, 0.1)),
            FaceRegion(name="B", rect=Rect64(0.5, 0.5, 0.6, 0.6)),
        )
        xmp = build_xmp(image_width=100, image_height=100, faces=rects)
        root = _parse(xmp)
        names = [el.text for el in root.findall(".//mwg-rs:Name", _NS)]
        assert names == ["A", "B"]


class TestValidXml:
    def test_parses_without_error(self):
        xmp = build_xmp(
            image_width=640,
            image_height=480,
            faces=(FaceRegion(name="Teszt", rect=Rect64(0.1, 0.1, 0.2, 0.2)),),
            tags=("Család|Gyerekek", "Nyaralás"),
        )
        # Nem dobhat kivételt — ez maga az érvényesség-teszt.
        root = _parse(xmp)
        assert root is not None

    def test_special_characters_escaped_and_parseable(self):
        xmp = build_xmp(
            image_width=100,
            image_height=100,
            faces=(FaceRegion(name='Kis & Nagy "Béla" <teszt>', rect=Rect64(0, 0, 0.1, 0.1)),),
            tags=("A & B",),
        )
        root = _parse(xmp)
        name_el = root.find(".//mwg-rs:Name", _NS)
        assert name_el.text == 'Kis & Nagy "Béla" <teszt>'

    def test_empty_build_is_valid(self):
        xmp = build_xmp(image_width=10, image_height=10)
        root = _parse(xmp)
        assert root is not None


class TestHierarchicalTags:
    def test_hierarchical_tag_creates_both_entries(self):
        xmp = build_xmp(image_width=100, image_height=100, tags=("Család|Gyerekek",))
        root = _parse(xmp)
        hier = [el.text for el in root.findall(".//lr:hierarchicalSubject//rdf:li", _NS)]
        flat = [el.text for el in root.findall(".//dc:subject//rdf:li", _NS)]
        assert hier == ["Család|Gyerekek"]
        assert flat == ["Gyerekek"]

    def test_flat_tag_only_in_subject_and_hierarchical(self):
        xmp = build_xmp(image_width=100, image_height=100, tags=("Nyaralás",))
        root = _parse(xmp)
        hier = [el.text for el in root.findall(".//lr:hierarchicalSubject//rdf:li", _NS)]
        flat = [el.text for el in root.findall(".//dc:subject//rdf:li", _NS)]
        assert hier == ["Nyaralás"]
        assert flat == ["Nyaralás"]

    def test_mixed_tags_dedup_and_order(self):
        xmp = build_xmp(
            image_width=100,
            image_height=100,
            tags=("Család|Gyerekek", "Nyaralás", "Család|Gyerekek"),
        )
        root = _parse(xmp)
        hier = [el.text for el in root.findall(".//lr:hierarchicalSubject//rdf:li", _NS)]
        flat = [el.text for el in root.findall(".//dc:subject//rdf:li", _NS)]
        assert hier == ["Család|Gyerekek", "Nyaralás"]
        assert flat == ["Gyerekek", "Nyaralás"]

    def test_no_tags_no_subject_blocks(self):
        xmp = build_xmp(image_width=100, image_height=100)
        root = _parse(xmp)
        assert root.find(".//dc:subject", _NS) is None
        assert root.find(".//lr:hierarchicalSubject", _NS) is None


class TestSidecarWrite:
    def test_write_and_read_back(self, tmp_path):
        image = tmp_path / "kep.jpg"
        image.write_bytes(b"\xff\xd8\xff\xd9")  # minimál JPEG-váz (nem valós dekódolás kell)
        rect = Rect64(left=0.25, top=0.25, right=0.5, bottom=0.5)
        target = write_sidecar(
            image,
            image_width=800,
            image_height=600,
            faces=(FaceRegion(name="Teszt Elek", rect=rect),),
            tags=("Család|Gyerekek",),
        )
        assert target == image.with_name("kep.jpg.xmp")
        assert target.exists()

        root = ET.parse(target).getroot()
        assert root.tag == "{adobe:ns:meta/}xmpmeta"
        area = root.find(".//mwg-rs:Area", _NS)
        assert float(area.get("{%s}x" % _NS["stArea"])) == pytest.approx(0.375)
        name_el = root.find(".//mwg-rs:Name", _NS)
        assert name_el.text == "Teszt Elek"

    def test_sidecar_path_appends_full_filename(self):
        assert sidecar_path("/photos/kep.jpg") == __import__("pathlib").Path(
            "/photos/kep.jpg.xmp"
        )

    def test_overwrite_existing_sidecar(self, tmp_path):
        image = tmp_path / "kep.jpg"
        image.write_bytes(b"\xff\xd8\xff\xd9")
        write_sidecar(image, image_width=100, image_height=100, tags=("Régi",))
        write_sidecar(image, image_width=100, image_height=100, tags=("Új",))
        target = sidecar_path(image)
        root = ET.parse(target).getroot()
        flat = [el.text for el in root.findall(".//dc:subject//rdf:li", _NS)]
        assert flat == ["Új"]


class TestRoundTrip:
    def test_region_coordinates_survive_round_trip(self):
        rect = Rect64(left=0.123456, top=0.234567, right=0.345678, bottom=0.456789)
        xmp = build_xmp(
            image_width=1000,
            image_height=1000,
            faces=(FaceRegion(name="RT", rect=rect),),
        )
        root = _parse(xmp)
        area = root.find(".//mwg-rs:Area", _NS)
        x = float(area.get("{%s}x" % _NS["stArea"]))
        y = float(area.get("{%s}y" % _NS["stArea"]))
        w = float(area.get("{%s}w" % _NS["stArea"]))
        h = float(area.get("{%s}h" % _NS["stArea"]))

        recovered_left = x - w / 2
        recovered_top = y - h / 2
        recovered_right = x + w / 2
        recovered_bottom = y + h / 2

        assert recovered_left == pytest.approx(rect.left, abs=1e-6)
        assert recovered_top == pytest.approx(rect.top, abs=1e-6)
        assert recovered_right == pytest.approx(rect.right, abs=1e-6)
        assert recovered_bottom == pytest.approx(rect.bottom, abs=1e-6)


class TestOrientation:
    def test_orientation_1_is_noop(self):
        rect = Rect64(0.1, 0.2, 0.3, 0.4)
        assert apply_orientation(rect, 1) == rect

    def test_orientation_3_rotates_180(self):
        rect = Rect64(left=0.1, top=0.2, right=0.3, bottom=0.4)
        rotated = apply_orientation(rect, 3)
        assert rotated.left == pytest.approx(0.7)
        assert rotated.top == pytest.approx(0.6)
        assert rotated.right == pytest.approx(0.9)
        assert rotated.bottom == pytest.approx(0.8)

    def test_orientation_6_rotates_90_cw(self):
        # Bal-felső sarok közeli (landscape) régió a docstringben levezetett
        # példa szerint jobb-felsőbe kerül a 90 CW forgatás után.
        rect = Rect64(left=0.0, top=0.0, right=0.2, bottom=0.1)
        rotated = apply_orientation(rect, 6)
        assert rotated == Rect64(left=0.9, top=0.0, right=1.0, bottom=0.2)

    def test_orientation_8_is_inverse_of_6(self):
        rect = Rect64(left=0.1, top=0.2, right=0.3, bottom=0.4)
        back = apply_orientation(apply_orientation(rect, 6), 8)
        assert back.left == pytest.approx(rect.left, abs=1e-9)
        assert back.top == pytest.approx(rect.top, abs=1e-9)
        assert back.right == pytest.approx(rect.right, abs=1e-9)
        assert back.bottom == pytest.approx(rect.bottom, abs=1e-9)

    def test_unhandled_orientation_is_noop(self):
        rect = Rect64(0.1, 0.2, 0.3, 0.4)
        assert apply_orientation(rect, 2) == rect


class TestValidation:
    def test_non_positive_dimensions_raise(self):
        with pytest.raises(ValueError):
            build_xmp(image_width=0, image_height=100)
        with pytest.raises(ValueError):
            build_xmp(image_width=100, image_height=-1)
