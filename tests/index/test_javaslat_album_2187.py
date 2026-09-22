"""#2187: a személy-album RÁCSA a függő javaslatokat is mutatja.

Az eredeti személy-album fejlécén ül a javaslat-munkafolyamat („Az összes
jóváhagyása", „Eltávolítás", javaslat-szűrő). Ehhez a javaslatoknak
LÁTSZANIUK kell a rácsban — különben a kijelölt hatókörű műveleteknek
nincs mire hatniuk, és a szűrőnek sincs mit szűrnie.

A névvel ELLÁTOTT arcok a `.picasa.ini`-ből jönnek (`person_photos`); a
függő javaslat viszont a saját `face` táblánkban él, `suggested_name`
mezővel, `unnamed` állapotban. Ez a két halmaz külön lekérdezés — a
metszetük sem üres feltétlenül: ugyanazon a képen lehet Anna megerősítve
és Roy javasolva.
"""

from __future__ import annotations

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces, sync_tree
from picasapy.index.faces_detected import (
    set_suggested_name,
    suggested_album_photos,
)
from support.jpeg_factory import make_jpeg

_LANDMARKS = FaceLandmarks(
    right_eye=(10.0, 20.0),
    left_eye=(30.0, 20.0),
    nose=(20.0, 30.0),
    mouth_right=(15.0, 40.0),
    mouth_left=(25.0, 40.0),
)


def _face() -> FaceDetection:
    return FaceDetection(
        left=5.0, top=10.0, right=40.0, bottom=50.0, score=0.9,
        landmarks=_LANDMARKS,
    )


def _konyvtar(tmp_path):
    """Három kép: az `a` és a `c` Royra javasolt, a `b` Annára."""
    root = tmp_path / "kepek"
    root.mkdir()
    for nev in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / nev)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
        azonositok = {
            sor["name"]: sor["id"]
            for sor in conn.execute("SELECT id, name FROM photos")
        }
        for nev, javaslat in (
            ("a.jpg", "Roy Avery"),
            ("b.jpg", "Anna Kis"),
            ("c.jpg", "roy avery"),
        ):
            replace_faces(conn, azonositok[nev], [_face()])
            arc = conn.execute(
                "SELECT id FROM face WHERE photo_id = ?", (azonositok[nev],)
            ).fetchone()
            set_suggested_name(conn, arc["id"], javaslat)
        conn.commit()
    return tmp_path / "index.db"


class TestJavaslatAlbum:
    def test_csak_az_adott_szemely_javaslatai(self, tmp_path):
        with open_index(_konyvtar(tmp_path)) as conn:
            nevek = {r.name for r in suggested_album_photos(conn, "Roy Avery")}
        assert nevek == {"a.jpg", "c.jpg"}

    def test_a_nev_osszevetese_kis_nagybetu_erzeketlen(self, tmp_path):
        """A `.picasa.ini` `[Contacts2]` szokása szerint — ugyanaz, amit a
        `suggested_faces_for` is tesz."""
        with open_index(_konyvtar(tmp_path)) as conn:
            nevek = {r.name for r in suggested_album_photos(conn, "ROY AVERY")}
        assert nevek == {"a.jpg", "c.jpg"}

    def test_ures_nevre_ures_eredmeny(self, tmp_path):
        """A felület akkor is hívja, amikor nincs nyitott személy-album."""
        with open_index(_konyvtar(tmp_path)) as conn:
            assert suggested_album_photos(conn, "") == ()

    def test_eldontott_javaslat_mar_nem_szerepel(self, tmp_path):
        """Az elvetés a `suggested_name`-et nullázza — a kép ettől kiesik a
        javaslat-halmazból, de a fájl megmarad."""
        db = _konyvtar(tmp_path)
        with open_index(db) as conn:
            arc = conn.execute(
                "SELECT f.id FROM face f JOIN photos p ON p.id = f.photo_id "
                "WHERE p.name = 'a.jpg'"
            ).fetchone()
            set_suggested_name(conn, arc["id"], None)
            conn.commit()
            nevek = {r.name for r in suggested_album_photos(conn, "Roy Avery")}
        assert nevek == {"c.jpg"}

    def test_minden_kep_csak_egyszer(self, tmp_path):
        """Két javaslat ugyanarra a képre ugyanarra a névre — a rácsban
        akkor is EGY sor (a `person_photos` szerződése is ez)."""
        db = _konyvtar(tmp_path)
        with open_index(db) as conn:
            foto = conn.execute(
                "SELECT id FROM photos WHERE name = 'a.jpg'"
            ).fetchone()["id"]
            masik = FaceDetection(
                left=60.0, top=60.0, right=90.0, bottom=90.0, score=0.8,
                landmarks=_LANDMARKS,
            )
            replace_faces(conn, foto, [_face(), masik])
            for sor in conn.execute(
                "SELECT id FROM face WHERE photo_id = ?", (foto,)
            ).fetchall():
                set_suggested_name(conn, sor["id"], "Roy Avery")
            conn.commit()
            sorok = list(suggested_album_photos(conn, "Roy Avery"))
        assert [r.name for r in sorok].count("a.jpg") == 1
