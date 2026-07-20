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

    def test_unidentified_face_has_empty_name(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\n"
            "faces=rect64(10000000f1ddff49),ffffffffffffffff;\n",
            encoding="utf-8",
        )
        faces = helper.facesFor(str(photo))
        assert len(faces) == 1
        assert faces[0]["name"] == ""

    def test_identified_face_without_contact_entry_has_empty_name(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\n"
            "faces=rect64(3f845bcb59418507),8e62b2035b74b477;\n",
            encoding="utf-8",
        )
        faces = helper.facesFor(str(photo))
        assert faces[0]["name"] == ""

    def test_two_faces_preserve_order(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[Contacts2]\n"
            "8e62b2035b74b477=Kis Éva;;\n"
            "[IMG_0001.jpg]\n"
            "faces=rect64(3f845bcb59418507),8e62b2035b74b477;"
            "rect64(10000000f1ddff49),ffffffffffffffff;\n",
            encoding="utf-8",
        )
        faces = helper.facesFor(str(photo))
        assert len(faces) == 2
        assert faces[0]["name"] == "Kis Éva"
        assert faces[1]["name"] == ""

    def test_malformed_faces_value_gives_empty_list(self, helper, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text("[IMG_0001.jpg]\nfaces=nemertelmes;\n", encoding="utf-8")
        assert helper.facesFor(str(photo)) == []

    def test_empty_path_gives_empty_list(self, helper):
        assert helper.facesFor("") == []
