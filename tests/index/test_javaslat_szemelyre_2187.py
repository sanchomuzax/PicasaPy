"""#2187 — a személy-album javaslatai: melyik arcra van MÉG EL NEM DÖNTÖTT
javaslat EGY megnevezett személyre.

A javaslat-munkafolyamat `confirmsug` parancsa (kezelő `0x00602640`) az
EGÉSZ személy-album javaslataira hat, a `confirmsel` ugyanaz a kezelő
`push 0`-val, a kijelöltekre — *egy művelet két hatókörrel* (a #2187
312. körének mérése). Mindkettőhöz ugyanaz kell előbb: **kik tartoznak
ehhez a személyhez javaslatként.**

A meglévő `suggested_faces()` MINDEN függő javaslatot ad; ez a lekérdezés
névre szűri. A névösszevetés kis-nagybetűre érzéketlen — az `ini/`
`[Contacts2]` neveivel ugyanez a szokás (`COLLATE NOCASE`).
"""

from __future__ import annotations

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces, sync_tree
from picasapy.index.faces_detected import (
    set_suggested_name,
    suggested_faces,
    suggested_faces_for,
)
from support.jpeg_factory import make_jpeg

_LANDMARKS = FaceLandmarks(
    right_eye=(2.0, 2.0),
    left_eye=(4.0, 2.0),
    nose=(3.0, 3.0),
    mouth_right=(2.0, 3.5),
    mouth_left=(4.0, 3.5),
)


def _face() -> FaceDetection:
    return FaceDetection(
        left=1.0, top=1.0, right=5.0, bottom=4.0, score=0.9, landmarks=_LANDMARKS
    )


def _keszlet(tmp_path):
    """Három arc: kettő „Anna"-javaslattal, egy „Béla"-val."""
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
        for nev in ("a.jpg", "b.jpg", "c.jpg"):
            replace_faces(conn, photo_ids[nev], [_face()])
        arcok = {
            row["photo_id"]: row["id"]
            for row in conn.execute("SELECT id, photo_id FROM face")
        }
        set_suggested_name(conn, arcok[photo_ids["a.jpg"]], "Anna")
        set_suggested_name(conn, arcok[photo_ids["b.jpg"]], "Anna")
        set_suggested_name(conn, arcok[photo_ids["c.jpg"]], "Béla")
        conn.commit()
    return db


class TestNevreSzures:
    def test_csak_az_adott_szemely_javaslatai(self, tmp_path):
        db = _keszlet(tmp_path)

        with open_index(db) as conn:
            annak = suggested_faces_for(conn, "Anna")

        assert len(annak) == 2
        assert {arc.suggested_name for arc in annak} == {"Anna"}

    def test_a_teljes_lista_tobbet_ad(self, tmp_path):
        """Ellenpróba: a szűrés tényleg szűr, nem mindent ad vissza."""
        db = _keszlet(tmp_path)

        with open_index(db) as conn:
            assert len(suggested_faces(conn)) == 3

    def test_kis_nagybetu_nem_szamit(self, tmp_path):
        db = _keszlet(tmp_path)

        with open_index(db) as conn:
            assert len(suggested_faces_for(conn, "anna")) == 2

    def test_ismeretlen_nevre_ures(self, tmp_path):
        db = _keszlet(tmp_path)

        with open_index(db) as conn:
            assert suggested_faces_for(conn, "Cecil") == ()

    def test_ures_nevre_ures_nem_hiba(self, tmp_path):
        """A felület üres névvel is meghívhatja (nincs nyitott személy-album)."""
        db = _keszlet(tmp_path)

        with open_index(db) as conn:
            assert suggested_faces_for(conn, "") == ()
