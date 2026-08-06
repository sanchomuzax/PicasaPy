"""faces= kulcs: rect64 + contact_id párok — spec: picasa-ini-format.md."""

import pytest

from picasapy.ini import (
    UNIDENTIFIED_CONTACT,
    Face,
    decode_rect64,
    parse_document,
    parse_faces,
    serialize_faces,
    with_face,
    with_reassigned_face,
    without_face,
    without_face_at_rect,
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


# -- írás (#26, 1. kör) --------------------------------------------------

_DOC = "[a.jpg]\nstar=yes\n"
_FACE = Face(rect=decode_rect64("3f845bcb59418507"), contact_id="8e62b2035b74b477")
_FACE2 = Face(rect=decode_rect64("10000000f1ddff49"), contact_id=UNIDENTIFIED_CONTACT)


class TestWithFace:
    def test_adds_faces_key_when_missing(self):
        document = with_face(parse_document(_DOC), "a.jpg", _FACE)
        section = document.section("a.jpg")
        assert parse_faces(section.get("faces")) == (_FACE,)

    def test_appends_to_existing_faces(self):
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE,))
        )
        updated = with_face(document, "a.jpg", _FACE2)
        assert parse_faces(updated.section("a.jpg").get("faces")) == (_FACE, _FACE2)

    def test_idempotent_for_identical_pair(self):
        document = with_face(parse_document(_DOC), "a.jpg", _FACE)
        again = with_face(document, "a.jpg", _FACE)
        assert again == document

    def test_missing_section_is_a_no_op_free_add(self):
        # nincs [b.jpg] szekció — with_face létrehozza (a with_value mintája)
        document = with_face(parse_document(_DOC), "b.jpg", _FACE)
        assert document.section("b.jpg") is not None
        assert parse_faces(document.section("b.jpg").get("faces")) == (_FACE,)


class TestWithoutFace:
    def test_removes_the_matching_pair(self):
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE, _FACE2))
        )
        updated = without_face(document, "a.jpg", _FACE)
        assert parse_faces(updated.section("a.jpg").get("faces")) == (_FACE2,)

    def test_removing_last_face_drops_the_key(self):
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE,))
        )
        updated = without_face(document, "a.jpg", _FACE)
        assert updated.section("a.jpg").get("faces") is None

    def test_no_such_pair_is_unchanged(self):
        document = parse_document(_DOC)
        assert without_face(document, "a.jpg", _FACE) == document

    def test_missing_section_is_unchanged(self):
        document = parse_document(_DOC)
        assert without_face(document, "nincs.jpg", _FACE) == document


class TestWithReassignedFace:
    def test_replaces_contact_id_for_matching_rect(self):
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE2,))
        )
        updated = with_reassigned_face(
            document, "a.jpg", _FACE2.rect, "0000000000000001"
        )
        faces = parse_faces(updated.section("a.jpg").get("faces"))
        assert faces == (Face(rect=_FACE2.rect, contact_id="0000000000000001"),)

    def test_region_is_unchanged_only_contact_id_moves(self):
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE,))
        )
        updated = with_reassigned_face(document, "a.jpg", _FACE.rect, UNIDENTIFIED_CONTACT)
        faces = parse_faces(updated.section("a.jpg").get("faces"))
        assert faces[0].rect == _FACE.rect
        assert not faces[0].is_identified

    def test_unknown_rect_is_a_no_op(self):
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE,))
        )
        other_rect = decode_rect64("0000111122223333")
        updated = with_reassigned_face(document, "a.jpg", other_rect, "1111111111111111")
        assert updated == document

    def test_missing_section_is_unchanged(self):
        document = parse_document(_DOC)
        updated = with_reassigned_face(document, "nincs.jpg", _FACE.rect, "1")
        assert updated == document

    def test_only_the_first_matching_rect_is_reassigned(self):
        # két azonos rect, eltérő contact_id — csak az ELSŐ cserélődik
        duplicate = Face(rect=_FACE.rect, contact_id="2222222222222222")
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE, duplicate))
        )
        updated = with_reassigned_face(document, "a.jpg", _FACE.rect, "9999999999999999")
        faces = parse_faces(updated.section("a.jpg").get("faces"))
        assert faces[0].contact_id == "9999999999999999"
        assert faces[1].contact_id == "2222222222222222"


# -- törlés rect szerint (#26, 2. kör) — a szerkesztő overlay ezt hívja, ------
# mert a QML-oldal nem feltétlenül ismeri a törlendő régió contact_id-ját
# (pl. a facesFor() csak nevet ad vissza, contact_id-t nem szükségszerűen).


class TestWithoutFaceAtRect:
    def test_removes_regardless_of_contact_id(self):
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE, _FACE2))
        )
        updated = without_face_at_rect(document, "a.jpg", _FACE.rect)
        assert parse_faces(updated.section("a.jpg").get("faces")) == (_FACE2,)

    def test_removing_last_face_drops_the_key(self):
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE,))
        )
        updated = without_face_at_rect(document, "a.jpg", _FACE.rect)
        assert updated.section("a.jpg").get("faces") is None

    def test_unknown_rect_is_a_no_op(self):
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE,))
        )
        other_rect = decode_rect64("0000111122223333")
        updated = without_face_at_rect(document, "a.jpg", other_rect)
        assert updated == document

    def test_missing_section_is_unchanged(self):
        document = parse_document(_DOC)
        assert without_face_at_rect(document, "nincs.jpg", _FACE.rect) == document

    def test_only_the_first_matching_rect_is_removed(self):
        duplicate = Face(rect=_FACE.rect, contact_id="2222222222222222")
        document = parse_document(_DOC).with_value(
            "a.jpg", "faces", serialize_faces((_FACE, duplicate))
        )
        updated = without_face_at_rect(document, "a.jpg", _FACE.rect)
        faces = parse_faces(updated.section("a.jpg").get("faces"))
        assert faces == (duplicate,)
