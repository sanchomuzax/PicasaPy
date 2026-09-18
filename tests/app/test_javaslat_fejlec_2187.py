"""#2187 — a személy-album javaslat-munkafolyamata: a jóváhagyás és az
elvetés SZEMÉLYRE, a fejlécből.

## A mérés

A fejlécsáv elosztója (`0x005e0f70`) nyolc javaslat-parancsot ismer; ebből
kettő ugyanaz a kezelő, egyetlen logikai argumentummal (a #2187 312.
körének helyesbítése):

```
0x005e15bf  "confirmsug"  ->  0x005e15eb  push 1   (MIND)
0x005e160f  "confirmsel"  ->  0x005e163b  push 0   (a KIJELÖLTEK)
0x005e15f1  call 0x00602640
```

⇒ nálunk is EGY művelet két hatókörrel legyen, ne két útvonal.

A jóváhagyás tárolója az ADATBÁZIS (a `.picasa.ini`-írás a
`FRWriteFaceDataINI` mögött van, alapértéke 0); az ELVETÉS az, ami
közvetlenül ír. Nálunk a meglévő, egy arcra szóló út a mérce:
`acceptSuggestion` a nevet ténylegesen ráírja, `rejectSuggestion` csak a
javaslatot törli, az arc névtelen marad.

⚠️ Ami ebben a körben MÉG NINCS: a KIJELÖLT hatókör (`confirmsel`,
`removesel`). Ahhoz a javaslatoknak látszaniuk kell a személy-album
rácsában, hogy legyen mit kijelölni — az a következő szelet. A művelet
mindkét hatókört tudja, a felület egyelőre csak a teljeset hívja.
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


def _face() -> FaceDetection:
    return FaceDetection(
        left=1.0, top=1.0, right=5.0, bottom=4.0, score=0.9, landmarks=_LANDMARKS
    )


@pytest.fixture
def vezerlo(qt_app, tmp_path):
    """Két „Anna"-javaslat és egy „Béla" — valódi indexszel, hamis
    detektorral (a modul többi tesztjének mintája)."""
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
    return FaceScanController(db, faces_helper=FacesHelper()), db


class TestDarabszam:
    def test_a_szemely_fuggo_javaslatai(self, vezerlo):
        ctl, _ = vezerlo

        assert ctl.personSuggestionCount("Anna") == 2

    def test_mas_szemely_sajatja(self, vezerlo):
        ctl, _ = vezerlo

        assert ctl.personSuggestionCount("Béla") == 1

    def test_nincs_nyitott_szemely_album(self, vezerlo):
        """Üres névre nulla — a fejléc kötése ezt hívja, amikor mappa van
        nyitva, nem személy-album."""
        ctl, _ = vezerlo

        assert ctl.personSuggestionCount("") == 0


class TestJovahagyas:
    def test_mind_jovahagyva_eltunik_a_javaslatok_kozul(self, vezerlo):
        ctl, db = vezerlo

        darab = ctl.confirmPersonSuggestions("Anna")

        assert darab == 2
        with open_index(db) as conn:
            assert suggested_faces_for(conn, "Anna") == ()

    def test_a_masik_szemely_javaslatat_nem_banti(self, vezerlo):
        ctl, db = vezerlo

        ctl.confirmPersonSuggestions("Anna")

        with open_index(db) as conn:
            assert len(suggested_faces_for(conn, "Béla")) == 1

    def test_a_jovahagyott_arc_MEGKAPJA_a_nevet(self, vezerlo):
        """A jóváhagyás nem a javaslat törlése: a nevet tényleg ráírja —
        ez a különbség az elvetéshez képest."""
        ctl, db = vezerlo

        ctl.confirmPersonSuggestions("Anna")

        with open_index(db) as conn:
            allapotok = [
                row["state"]
                for row in conn.execute("SELECT state FROM face WHERE id IN "
                                        "(SELECT id FROM face)")
            ]
        assert allapotok.count("named") == 2

    def test_ures_nevre_nem_csinal_semmit(self, vezerlo):
        ctl, db = vezerlo

        assert ctl.confirmPersonSuggestions("") == 0
        with open_index(db) as conn:
            assert len(suggested_faces_for(conn, "Anna")) == 2


class TestElvetes:
    def test_elvetve_eltunik_a_javaslat(self, vezerlo):
        ctl, db = vezerlo

        darab = ctl.removePersonSuggestions("Anna")

        assert darab == 2
        with open_index(db) as conn:
            assert suggested_faces_for(conn, "Anna") == ()

    def test_az_arc_NEVTELEN_marad(self, vezerlo):
        """Az elvetés nem névadás és nem mellőzés: az arc marad névtelen,
        hogy egy későbbi futás újra megvizsgálhassa."""
        ctl, db = vezerlo

        ctl.removePersonSuggestions("Anna")

        with open_index(db) as conn:
            allapotok = [
                row["state"] for row in conn.execute("SELECT state FROM face")
            ]
        assert allapotok.count("unnamed") == 3


class TestHatokor:
    """Egy művelet két hatókörrel — a mérés szerint a `confirmsug` és a
    `confirmsel` UGYANAZ a kezelő, egyetlen logikai argumentummal."""

    def test_a_kijelolt_hatokor_csak_a_megadott_arcokra_hat(self, vezerlo):
        ctl, db = vezerlo
        with open_index(db) as conn:
            arcok = [arc.id for arc in suggested_faces_for(conn, "Anna")]

        darab = ctl.confirmPersonSuggestions("Anna", [arcok[0]])

        assert darab == 1
        with open_index(db) as conn:
            assert len(suggested_faces_for(conn, "Anna")) == 1

    def test_a_hatokor_nem_lephet_ki_a_szemelybol(self, vezerlo):
        """Ellenpróba: idegen arc azonosítója a listában NEM hat — a
        művelet a személy javaslatain belül marad."""
        ctl, db = vezerlo
        with open_index(db) as conn:
            belaje = [arc.id for arc in suggested_faces_for(conn, "Béla")]

        darab = ctl.confirmPersonSuggestions("Anna", belaje)

        assert darab == 0
        with open_index(db) as conn:
            assert len(suggested_faces_for(conn, "Béla")) == 1
