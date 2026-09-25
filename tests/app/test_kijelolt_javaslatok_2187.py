"""#2187 — a KIJELÖLT hatókör (`confirmsel`, `removesel`): a rács
kijelöléséből a személy javaslat-arcai.

A rács sora a FOTÓ, nem az arc (`PeopleMixin._osszefuzve`), a művelet
viszont arcokra hat (`confirmPersonSuggestions(name, face_ids)`). A kettő
közé kell egy leképezés: a kijelölt fotók útvonalaiból a személy MÉG
FÜGGŐ javaslat-arcai. Idegen személy javaslata és a megerősített arc nem
kerülhet bele — különben a „Kijelölt javaslatok jóváhagyása" többre hatna,
mint amit a felirat ígér.

Amit ez a fájl NEM mér: a fejléc két állapotát (az a QML-funkcionális
teszté, `qml_functional/test_javaslat_fejlec_ui_2187.py`).
"""

from __future__ import annotations

import pytest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces, sync_tree
from picasapy.index.faces_detected import set_suggested_name, suggested_faces_for
from support.jpeg_factory import make_jpeg

_LANDMARKS = FaceLandmarks(
    right_eye=(2.0, 2.0),
    left_eye=(4.0, 2.0),
    nose=(3.0, 3.0),
    mouth_right=(2.0, 3.5),
    mouth_left=(4.0, 3.5),
)


def _face(eltolas: float = 0.0) -> FaceDetection:
    return FaceDetection(
        left=1.0 + eltolas, top=1.0, right=5.0 + eltolas, bottom=4.0,
        score=0.9, landmarks=_LANDMARKS,
    )


@pytest.fixture
def vezerlo(qt_app, tmp_path):
    """`a.jpg`: két arc, mindkettő „Anna"-javaslat. `b.jpg`: egy
    „Anna"-javaslat. `c.jpg`: egy „Béla"-javaslat."""
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.app.faces_helper import FacesHelper

    root = tmp_path / "kepek"
    root.mkdir()
    for nev in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / nev)
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, root)
        photo_ids = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM photos")
        }
        replace_faces(conn, photo_ids["a.jpg"], [_face(), _face(10.0)])
        replace_faces(conn, photo_ids["b.jpg"], [_face()])
        replace_faces(conn, photo_ids["c.jpg"], [_face()])
        for row in conn.execute("SELECT id, photo_id FROM face").fetchall():
            nev = "Béla" if row["photo_id"] == photo_ids["c.jpg"] else "Anna"
            set_suggested_name(conn, row["id"], nev)
        conn.commit()
    return FaceScanController(db, faces_helper=FacesHelper()), db, root


def _ut(root, nev: str) -> str:
    """Pontosan az az alak, amit a rács ad (`PhotoGridModel.filePathAt`)."""
    return f"{root}/{nev}"


class TestLekepezes:
    def test_a_kijelolt_foto_MINDEN_javaslat_arca(self, vezerlo):
        """Egy képen több arc is javasolhatja ugyanazt a nevet — a
        kijelölés a fotót jelöli, tehát mindegyikük a hatókörbe tartozik."""
        ctl, _, root = vezerlo

        arcok = ctl.personSuggestionIdsForPaths("Anna", [_ut(root, "a.jpg")])

        assert len(arcok) == 2

    def test_tobb_kijelolt_foto(self, vezerlo):
        ctl, _, root = vezerlo

        arcok = ctl.personSuggestionIdsForPaths(
            "Anna", [_ut(root, "a.jpg"), _ut(root, "b.jpg")])

        assert len(arcok) == 3

    def test_idegen_szemely_javaslata_nem_kerul_bele(self, vezerlo):
        ctl, _, root = vezerlo

        arcok = ctl.personSuggestionIdsForPaths("Anna", [_ut(root, "c.jpg")])

        assert arcok == []

    def test_ures_nev_vagy_kijeloles(self, vezerlo):
        ctl, _, root = vezerlo

        assert ctl.personSuggestionIdsForPaths("", [_ut(root, "a.jpg")]) == []
        assert ctl.personSuggestionIdsForPaths("Anna", []) == []


class TestKijeloltMuvelet:
    def test_a_jovahagyas_csak_a_kijelolt_fotora_hat(self, vezerlo):
        ctl, db, root = vezerlo
        arcok = ctl.personSuggestionIdsForPaths("Anna", [_ut(root, "b.jpg")])

        darab = ctl.confirmPersonSuggestions("Anna", arcok)

        assert darab == 1
        with open_index(db) as conn:
            assert len(suggested_faces_for(conn, "Anna")) == 2

    def test_a_torles_csak_a_kijelolt_fotora_hat(self, vezerlo):
        ctl, db, root = vezerlo
        arcok = ctl.personSuggestionIdsForPaths("Anna", [_ut(root, "a.jpg")])

        darab = ctl.removePersonSuggestions("Anna", arcok)

        assert darab == 2
        with open_index(db) as conn:
            megmaradt = suggested_faces_for(conn, "Anna")
        assert [arc.photo_path.name for arc in megmaradt] == ["b.jpg"]
