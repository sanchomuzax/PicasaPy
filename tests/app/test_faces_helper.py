"""FacesHelper: a faces= régiók csak-olvasás szintű lekérdezése (#147)."""

import pytest

from picasapy.ini.rect64 import decode_rect64
from support.jpeg_factory import make_jpeg


@pytest.fixture
def helper(qt_app):
    from picasapy.app.faces_helper import FacesHelper

    return FacesHelper()


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


class TestFacesFor:
    def test_no_ini_gives_empty_list(self, helper, photo):
        assert helper.facesFor(str(photo)) == []

    def test_no_section_gives_empty_list(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text("[other.jpg]\nstar=yes\n", encoding="utf-8")
        assert helper.facesFor(str(photo)) == []

    def test_no_faces_key_gives_empty_list(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text("[IMG_0001.jpg]\nstar=yes\n", encoding="utf-8")
        assert helper.facesFor(str(photo)) == []

    def test_identified_face_resolves_name(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[Contacts2]\n"
            "8e62b2035b74b477=Kis Éva;;\n"
            "[IMG_0001.jpg]\n"
            "faces=rect64(3f845bcb59418507),8e62b2035b74b477;\n",
            encoding="utf-8",
        )
        faces = helper.facesFor(str(photo))
        assert len(faces) == 1
        face = faces[0]
        assert face["name"] == "Kis Éva"
        expected = decode_rect64("3f845bcb59418507")
        assert face["left"] == pytest.approx(expected.left)
        assert face["top"] == pytest.approx(expected.top)
        assert face["right"] == pytest.approx(expected.right)
        assert face["bottom"] == pytest.approx(expected.bottom)

    def test_ignored_face_is_not_returned(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\n"
            "faces=rect64(10000000f1ddff49),ffffffffffffffff;\n",
            encoding="utf-8",
        )
        assert helper.facesFor(str(photo)) == []

    def test_zero_contact_is_not_returned_and_ini_bytes_are_preserved(
        self, helper, photo
    ):
        ini = photo.parent / ".picasa.ini"
        ini.write_bytes(
            b"[Contacts2]\r\n8e62b2035b74b477=Kis Eva;;\r\n"
            b"[IMG_0001.jpg]\r\n"
            b"faces=rect64(3f845bcb59418507),8e62b2035b74b477;"
            b"rect64(10000000f1ddff49),0;"
            b"rect64(20000000f1ddff49),ffffffffffffffff\r\n"
            b"; ezt a sort is meg kell orizni\r\n"
        )
        before = ini.read_bytes()

        faces = helper.facesFor(str(photo))

        assert [face["name"] for face in faces] == ["Kis Eva"]
        assert ini.read_bytes() == before

    def test_identified_face_without_contact_entry_has_empty_name(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\n"
            "faces=rect64(3f845bcb59418507),8e62b2035b74b477;\n",
            encoding="utf-8",
        )
        faces = helper.facesFor(str(photo))
        assert faces[0]["name"] == ""

    def test_ignored_face_is_filtered_without_reordering_named_faces(
        self, helper, photo
    ):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[Contacts2]\n"
            "8e62b2035b74b477=Kis Éva;;\n"
            "17be12be040e4089=Anna;;\n"
            "[IMG_0001.jpg]\n"
            "faces=rect64(3f845bcb59418507),8e62b2035b74b477;"
            "rect64(10000000f1ddff49),ffffffffffffffff;"
            "rect64(20000000f1ddff49),17be12be040e4089\n",
            encoding="utf-8",
        )
        faces = helper.facesFor(str(photo))
        assert [face["name"] for face in faces] == ["Kis Éva", "Anna"]

    def test_malformed_faces_value_gives_empty_list(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text("[IMG_0001.jpg]\nfaces=nemertelmes;\n", encoding="utf-8")
        assert helper.facesFor(str(photo)) == []

    def test_empty_path_gives_empty_list(self, helper):
        assert helper.facesFor("") == []


# -- írás (#26, 2. kör): arc-téglalap rajzolása/átnevezése/törlése a --------
# nézőben — a csillag/album minta (update_document, útvonalankénti szerializálás).

_RECT = decode_rect64("3f845bcb59418507")
_RECT2 = decode_rect64("10000000f1ddff49")


class TestKnownNames:
    def test_no_ini_gives_empty_list(self, helper, photo):
        assert helper.knownNames(str(photo)) == []

    def test_lists_contacts2_names_sorted(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[Contacts2]\n"
            "8e62b2035b74b477=Zoltán;;\n"
            "b8e4117cf1d6615b=Anna;;\n",
            encoding="utf-8",
        )
        assert helper.knownNames(str(photo)) == ["Anna", "Zoltán"]


class TestAddFace:
    @pytest.mark.parametrize("name", ["", "   ", " \t "])
    def test_empty_name_does_not_modify_ini(self, helper, photo, name):
        ini = photo.parent / ".picasa.ini"
        ini.write_bytes(b"[IMG_0001.jpg]\r\nstar=yes\r\n; maradjon\r\n")
        before = ini.read_bytes()

        ok = helper.addFace(
            str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, name
        )

        assert ok is True
        assert ini.read_bytes() == before

    def test_adds_region_with_new_name_creates_contact(self, helper, photo):
        ok = helper.addFace(
            str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, "Kis Éva"
        )
        assert ok is True
        faces = helper.facesFor(str(photo))
        assert faces[0]["name"] == "Kis Éva"

    def test_adds_region_reusing_existing_contact_id(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text("[Contacts2]\n8e62b2035b74b477=Kis Éva;;\n", encoding="utf-8")
        helper.addFace(
            str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, "Kis Éva"
        )
        # nem jött létre MÁSODIK "Kis Éva" bejegyzés — a meglévő id-t használta
        ini_text = ini.read_text(encoding="utf-8")
        assert ini_text.count("Kis Éva") == 1

    def test_two_faces_accumulate(self, helper, photo):
        helper.addFace(str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, "Anna")
        helper.addFace(
            str(photo), _RECT2.left, _RECT2.top, _RECT2.right, _RECT2.bottom, "Béla"
        )
        faces = helper.facesFor(str(photo))
        assert {f["name"] for f in faces} == {"Anna", "Béla"}


class TestRenameFace:
    def test_assigns_name_to_existing_region(self, helper, photo):
        helper.addFace(
            str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, "Kata"
        )
        ok = helper.renameFace(
            str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, "Anna"
        )
        assert ok is True
        assert helper.facesFor(str(photo))[0]["name"] == "Anna"

    def test_clearing_name_removes_region(self, helper, photo):
        helper.addFace(str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, "Anna")
        ok = helper.renameFace(
            str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, "  "
        )

        assert ok is True
        faces = helper.facesFor(str(photo))
        assert faces == []
        assert "faces=" not in (photo.parent / ".picasa.ini").read_text(
            encoding="utf-8"
        )

    def test_unknown_rect_is_a_no_op(self, helper, photo):
        ok = helper.renameFace(
            str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, "Anna"
        )
        assert ok is True
        assert helper.facesFor(str(photo)) == []


class TestRemoveFace:
    def test_removes_the_region(self, helper, photo):
        helper.addFace(str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, "Anna")
        ok = helper.removeFace(str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom)
        assert ok is True
        assert helper.facesFor(str(photo)) == []

    def test_removing_one_of_two_keeps_the_other(self, helper, photo):
        helper.addFace(str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom, "Anna")
        helper.addFace(
            str(photo), _RECT2.left, _RECT2.top, _RECT2.right, _RECT2.bottom, "Béla"
        )
        helper.removeFace(str(photo), _RECT.left, _RECT.top, _RECT.right, _RECT.bottom)
        faces = helper.facesFor(str(photo))
        assert len(faces) == 1
        assert faces[0]["name"] == "Béla"


class TestRemoveIgnoredFace:
    """#3670 (B3): a mellőzés visszavétele CSAK a pontos (régió,
    `ffffffffffffffff`) párt törölheti — a `removeFace` keret alapján
    töröl, és egy közben elnevezett régiót is vinne."""

    _RECT = "10000000f1ddff49"

    def test_it_removes_the_ffff_pair(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            f"[IMG_0001.jpg]\nfaces=rect64({self._RECT}),ffffffffffffffff;\n",
            encoding="utf-8",
        )
        rect = decode_rect64(self._RECT)

        assert helper.removeIgnoredFace(
            str(photo), rect.left, rect.top, rect.right, rect.bottom
        )

        assert helper.facesFor(str(photo)) == []

    def test_it_keeps_a_named_face_on_the_same_region(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[Contacts2]\n"
            "8e62b2035b74b477=Roy Avery;;\n"
            "[IMG_0001.jpg]\n"
            f"faces=rect64({self._RECT}),8e62b2035b74b477;\n",
            encoding="utf-8",
        )
        rect = decode_rect64(self._RECT)

        assert helper.removeIgnoredFace(
            str(photo), rect.left, rect.top, rect.right, rect.bottom
        )

        faces = helper.facesFor(str(photo))
        assert [face["name"] for face in faces] == ["Roy Avery"]
