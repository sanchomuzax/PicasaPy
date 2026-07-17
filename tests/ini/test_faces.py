"""faces= kulcs: rect64 + contact_id párok — spec: picasa-ini-format.md."""

import pytest

from picasapy.ini import (
    UNIDENTIFIED_CONTACT,
    Face,
    decode_rect64,
    parse_faces,
    serialize_faces,
)

TWO_FACES = "rect64(3f845bcb59418507),8e62b2035b74b477;rect64(10000000f1ddff49),ffffffffffffffff;"


class TestParse:
    def test_two_faces(self):
        faces = parse_faces(TWO_FACES)
        assert len(faces) == 2
        assert faces[0].contact_id == "8e62b2035b74b477"
        assert faces[0].rect == decode_rect64("3f845bcb59418507")

    def test_unidentified_face(self):
        faces = parse_faces(TWO_FACES)
        assert faces[0].is_identified
        assert not faces[1].is_identified
        assert faces[1].contact_id == UNIDENTIFIED_CONTACT

    def test_short_rect_hex(self):
        # A Picasa a rect64-ben is elhagyhatja a vezető nullákat.
        faces = parse_faces("rect64(5bcb59418507),8e62b2035b74b477;")
        assert faces[0].rect.left == 0.0

    def test_empty_value(self):
        assert parse_faces("") == ()

    def test_missing_trailing_semicolon_tolerated(self):
        with_semi = parse_faces(TWO_FACES)
        without = parse_faces(TWO_FACES.rstrip(";"))
        assert with_semi == without

    @pytest.mark.parametrize(
        "bad",
        [
            "rect64(3f845bcb59418507);",  # nincs contact_id
            "8e62b2035b74b477;",  # nincs rect
            "rect64(xyz),8e62b2035b74b477;",  # rossz hex
            "rect64(3f845bcb59418507),8e62,extra;",  # plusz mező
            "rect64(3f845bcb59418507),nemhexid;",  # nem hex contact_id
            "rect64(3f845bcb59418507),8e62b2035b74b4770;",  # 17 jegyű id
        ],
    )
    def test_malformed_raises(self, bad):
        with pytest.raises(ValueError):
            parse_faces(bad)

    def test_short_contact_id_accepted(self):
        # A Picasa máshol is elhagyja a vezető nullákat — legyünk tűrők.
        faces = parse_faces("rect64(3f845bcb59418507),8e62;")
        assert faces[0].contact_id == "8e62"

    def test_uppercase_unidentified_id(self):
        faces = parse_faces("rect64(3f845bcb59418507),FFFFFFFFFFFFFFFF;")
        assert not faces[0].is_identified


class TestSerialize:
    def test_roundtrip_exact_for_full_length_rects(self):
        assert serialize_faces(parse_faces(TWO_FACES)) == TWO_FACES

    def test_serialize_from_face(self):
        face = Face(rect=decode_rect64("3f845bcb59418507"), contact_id="8e62b2035b74b477")
        assert serialize_faces((face,)) == "rect64(3f845bcb59418507),8e62b2035b74b477;"


class TestImmutability:
    def test_face_is_frozen(self):
        face = parse_faces(TWO_FACES)[0]
        with pytest.raises(AttributeError):
            face.contact_id = "0"
