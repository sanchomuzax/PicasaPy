"""„Arcos képek" szűrő — a MEGLÉVŐ ini-adatra épül (#1830).

Az eredeti keresősávján ez a `facesearch` gomb. A jegy kikötése:

> az „arcos képek" a **meglévő** `faces=` adatra épül, és nem igényel
> arcfelismerést

Ezért NEM a `face` táblát kérdezzük (azt az `index/faces_detected.py`
tölti, vagyis a felismerő motor), hanem ugyanazt az ini-söprést
használjuk, amiből az „Emberek" gyűjtemény is él (`people.py`).

⚠️ A **megnevezetlen** arc is arc: a szűrő nem a „kit ismerünk fel"
kérdésre válaszol, hanem arra, hogy „van-e a képen bejelölt arc".
Ebben tér el a `person_photos`-tól, ami nevet keres.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, sync_tree
from picasapy.index.people import photos_with_faces
from support.jpeg_factory import make_jpeg

_ROY = "b8e4117cf1d6615b"
_UNKNOWN = "ffffffffffffffff"
_RECT = "3f840000c3509f84"


@pytest.fixture
def library(tmp_path):
    """`a.jpg` — nevesített arc; `b.jpg` — CSAK megnevezetlen arc;
    `c.jpg` — nincs arc, csak csillag; `d.jpg` — másik mappában, arccal."""
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    (root / "varos").mkdir()
    for nev in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / "nyaralas" / nev)
    make_jpeg(root / "varos" / "d.jpg")
    make_jpeg(root / "varos" / "e.jpg")

    (root / "nyaralas" / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY};\n"
        f"[b.jpg]\nfaces=rect64({_RECT}),{_UNKNOWN};\n"
        f"[c.jpg]\nstar=yes\n",
        encoding="utf-8",
    )
    (root / "varos" / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n"
        f"[d.jpg]\nfaces=rect64({_RECT}),{_ROY};\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def conn(tmp_path, library):
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        yield connection


class TestAzArcosKepek:
    def test_csak_az_arcos_kepeket_adja(self, conn):
        nevek = sorted(r.name for r in photos_with_faces(conn))
        assert nevek == ["a.jpg", "b.jpg", "d.jpg"]

    def test_a_MEGNEVEZETLEN_arc_is_arc(self, conn):
        """A foga: ha valaki a `person_photos` név-egyeztetését másolná
        ide, a `b.jpg` kiesne."""
        assert "b.jpg" in {r.name for r in photos_with_faces(conn)}

    def test_az_arc_NELKULI_kep_kimarad(self, conn):
        nevek = {r.name for r in photos_with_faces(conn)}
        assert "c.jpg" not in nevek, "a csillagozott, arc nélküli kép bekerült"
        assert "e.jpg" not in nevek, "az ini-ben nem is szereplő kép bekerült"

    def test_TOBB_mappan_at_gyujt(self, conn):
        mappak = {r.folder_path for r in photos_with_faces(conn)}
        assert len(mappak) == 2

    def test_rendezes_mappa_majd_nev(self, conn):
        """A testvér-szűrők (csillag, film) sorrendje."""
        tetelek = photos_with_faces(conn)
        assert list(tetelek) == sorted(
            tetelek, key=lambda r: (r.folder_path, r.name)
        )

    def test_arc_NELKULI_konyvtarban_URES(self, tmp_path):
        root = tmp_path / "ures"
        root.mkdir()
        make_jpeg(root / "x.jpg")
        with open_index(tmp_path / "ures.db") as c:
            sync_tree(c, root)
            assert photos_with_faces(c) == ()
