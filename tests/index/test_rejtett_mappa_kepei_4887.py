"""#4887 — a rejtett mappák képei a mappán kívüli lekérdezésekben sem látszanak.

A szűrés EGY közös ponton történik (`index/hidden_scope.py`): a fotó-
lekérdezések `folders` illesztése a látható mappákra szűkül, hacsak a
felület nem közölte, hogy a rejtettek látszhatnak
(`set_hidden_folders_visible`). Itt minden olvasó lekérdezést mérünk:
rejtett mappa képe alapból NEM jön vissza, a láthatóság közlése után igen.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from picasapy.index import (
    album_photos,
    albums_in_index,
    all_photos,
    geotagged_photos,
    ignored_faces,
    ignored_ini_faces,
    open_index,
    people_in_index,
    people_with,
    person_photos,
    photos_in_folder,
    photos_under_folder,
    photos_up_to_age,
    photos_with_faces,
    photos_with_keyword,
    search_photos,
    search_suggestions,
    set_folder_hidden,
    starred_photos,
    suggested_faces_for,
    sync_tree,
    unnamed_album_photos,
    unnamed_faces,
    video_photos,
)
from picasapy.index.faces_detected import (
    faces_for_photo,
    suggested_album_photos,
    unnamed_photo_count,
)
from picasapy.index.hidden_scope import (
    hidden_folders_visible,
    set_hidden_folders_visible,
)
from picasapy.index.people import person_movie_photos
from support.jpeg_factory import make_jpeg

_ROY = "b8e4117cf1d6615b"
_ANNA = "a1a1a1a1a1a1a1a1"
_MELLOZOTT = "ffffffffffffffff"
_RECT = "3f840000c3509f84"
_ALBUM = "0123456789abcdef0123456789abcdef"


def _ini(kep: str) -> str:
    return (
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n{_ANNA}=Anna;;\n"
        f"[.album:{_ALBUM}]\nname=Nyar\ntoken={_ALBUM}\n"
        f"[{kep}]\nstar=yes\nkeywords=nyar\nalbums={_ALBUM}\n"
        f"faces=rect64({_RECT}),{_ROY};rect64({_RECT}),{_ANNA};"
        f"rect64({_RECT}),{_MELLOZOTT}\n"
    )


@pytest.fixture
def db(tmp_path):
    """`latszik/a.jpg` és a rejtett `titkos/b.jpg` — minden tulajdonságban
    egyformák (csillag, címke, album, hely, friss dátum, arcok, film)."""
    gyoker = tmp_path / "kepek"
    friss = (datetime.now() - timedelta(days=2)).strftime("%Y:%m:%d %H:%M:%S")
    for mappa, kep in (("latszik", "a.jpg"), ("titkos", "b.jpg")):
        (gyoker / mappa).mkdir(parents=True)
        make_jpeg(gyoker / mappa / kep, taken_at=friss, gps=(47.5, 19.05))
        (gyoker / mappa / ".picasa.ini").write_text(_ini(kep), encoding="utf-8")
    ut = tmp_path / "index.db"
    with open_index(ut) as conn:
        sync_tree(conn, gyoker)
        conn.execute("UPDATE photos SET kind = 'video'")
        for sor in conn.execute("SELECT id FROM photos").fetchall():
            conn.execute(
                "INSERT INTO face(photo_id, rect_left, rect_top, rect_right,"
                " rect_bottom, det_conf, right_eye_x, right_eye_y, left_eye_x,"
                " left_eye_y, nose_x, nose_y, mouth_right_x, mouth_right_y,"
                " mouth_left_x, mouth_left_y, state, suggested_name)"
                " VALUES (?, 1, 1, 4, 4, 0.9, 0,0,0,0,0,0,0,0,0,0, 'unnamed', 'Roy')",
                (sor[0],),
            )
            conn.execute(
                "INSERT INTO face(photo_id, rect_left, rect_top, rect_right,"
                " rect_bottom, det_conf, right_eye_x, right_eye_y, left_eye_x,"
                " left_eye_y, nose_x, nose_y, mouth_right_x, mouth_right_y,"
                " mouth_left_x, mouth_left_y, state)"
                " VALUES (?, 1, 1, 4, 4, 0.9, 0,0,0,0,0,0,0,0,0,0, 'ignored')",
                (sor[0],),
            )
        conn.commit()
        set_folder_hidden(conn, str(gyoker / "titkos"), True)
    return ut


def _nevek(rekordok) -> list[str]:
    return sorted(r.name for r in rekordok)


def _kepnevek(arcok) -> list[str]:
    return sorted(a.photo_path.name for a in arcok)


#: (név, lekérdezés) — minden fotót adó olvasó út
_FOTO_LEKERDEZESEK = {
    "all_photos": lambda c: all_photos(c),
    "starred": lambda c: starred_photos(c),
    "video": lambda c: video_photos(c),
    "keyword": lambda c: photos_with_keyword(c, "nyar"),
    "age": lambda c: photos_up_to_age(
        c, (datetime.now() - timedelta(days=30)).isoformat(timespec="seconds")
    ),
    "geo": lambda c: geotagged_photos(c),
    "search-text": lambda c: search_photos(c, "nyar"),
    "search-folder-name": lambda c: search_photos(c, "titkos"),
    "album": lambda c: album_photos(c, _ALBUM),
    "person": lambda c: person_photos(c, "Roy Avery"),
    "person-movie": lambda c: person_movie_photos(c, ("Roy Avery",)),
    "faces": lambda c: photos_with_faces(c),
    "suggested-album": lambda c: suggested_album_photos(c, "Roy"),
    "unnamed-album": lambda c: unnamed_album_photos(c),
    "under-parent-folder": lambda c: photos_under_folder(
        c, str(_gyoker(c) / "kepek")
    ),
}


def _gyoker(conn):
    from pathlib import Path

    ut = next(s[2] for s in conn.execute("PRAGMA database_list") if s[1] == "main")
    return Path(ut).parent


@pytest.mark.parametrize("nev", sorted(_FOTO_LEKERDEZESEK))
def test_rejtett_mappa_kepe_alapbol_nem_jon_vissza(db, nev):
    with open_index(db) as conn:
        nevek = _nevek(_FOTO_LEKERDEZESEK[nev](conn))
    assert "b.jpg" not in nevek
    if nev != "search-folder-name":
        assert "a.jpg" in nevek


@pytest.mark.parametrize("nev", sorted(_FOTO_LEKERDEZESEK))
def test_lathatosag_kozlese_utan_a_rejtett_kep_is_latszik(db, nev):
    set_hidden_folders_visible(db, True)
    with open_index(db) as conn:
        assert "b.jpg" in _nevek(_FOTO_LEKERDEZESEK[nev](conn))
    set_hidden_folders_visible(db, False)
    with open_index(db) as conn:
        assert "b.jpg" not in _nevek(_FOTO_LEKERDEZESEK[nev](conn))


def test_az_alapertek_a_biztonsagos(db, tmp_path):
    assert hidden_folders_visible(db) is False
    assert hidden_folders_visible(tmp_path / "masik.db") is False


def test_a_rejtett_mappa_sajat_lekerdezese_is_kovet(db, tmp_path):
    """A mappa saját listája is a közös kaput követi — a mappa nem is
    látszik a hasábon, tehát a képei sem kérhetők le mellékúton."""
    with open_index(db) as conn:
        assert photos_in_folder(conn, str(tmp_path / "kepek" / "titkos")) == ()


def test_belso_ut_kifejezetten_kerheti_a_teljes_konyvtarat(db):
    with open_index(db) as conn:
        assert _nevek(all_photos(conn, include_hidden_folders=True)) == [
            "a.jpg",
            "b.jpg",
        ]


def test_a_ketfele_rejtes_jeloles_is_rejt(db, tmp_path):
    """`folders.hidden = 2` (az ini-be még be nem írt rejtés) is rejtett."""
    with open_index(db) as conn:
        set_folder_hidden(conn, str(tmp_path / "kepek" / "titkos"), True,
                          ini_pending=True)
        assert _nevek(all_photos(conn)) == ["a.jpg"]


class TestEmberek:
    def test_nevsor_darabszama_nem_szamolja_a_rejtettet(self, db):
        with open_index(db) as conn:
            darab = {p.name: p.photo_count for p in people_in_index(conn)}
        assert darab == {"Anna": 1, "Roy Avery": 1}
        set_hidden_folders_visible(db, True)
        with open_index(db) as conn:
            darab = {p.name: p.photo_count for p in people_in_index(conn)}
        assert darab == {"Anna": 2, "Roy Avery": 2}

    def test_kivel_szerepel_nem_szamolja_a_rejtettet(self, db):
        with open_index(db) as conn:
            assert [(p.name, p.photo_count) for p in people_with(conn, "Roy Avery")] == [
                ("Anna", 1)
            ]

    def test_arc_javaslatok_es_nevtelenek_nem_adjak_a_rejtettet(self, db):
        with open_index(db) as conn:
            assert _kepnevek(suggested_faces_for(conn, "Roy")) == ["a.jpg"]
            assert _kepnevek(unnamed_faces(conn)) == ["a.jpg"]
            assert _kepnevek(ignored_faces(conn)) == ["a.jpg"]
            assert unnamed_photo_count(conn) == 1
            assert _kepnevek(ignored_ini_faces(conn)) == ["a.jpg"]
        set_hidden_folders_visible(db, True)
        with open_index(db) as conn:
            assert _kepnevek(unnamed_faces(conn)) == ["a.jpg", "b.jpg"]
            assert unnamed_photo_count(conn) == 2
            assert _kepnevek(ignored_ini_faces(conn)) == ["a.jpg", "b.jpg"]

    def test_a_fotonkenti_belso_arcutat_nem_szukiti(self, db):
        """A szkennelés belső útja (mellőzött régiók egyeztetése) a rejtett
        mappa képén is dolgozik — az nem megjelenítés."""
        with open_index(db) as conn:
            rejtett_id = conn.execute(
                "SELECT p.id FROM photos p JOIN folders f ON f.id = p.folder_id"
                " WHERE f.hidden != 0"
            ).fetchone()[0]
            assert len(faces_for_photo(conn, rejtett_id)) == 2


class TestAlbumokEsJavaslatok:
    def test_album_darabszama_csak_a_lathatot_szamolja(self, db):
        with open_index(db) as conn:
            assert [a.photo_count for a in albums_in_index(conn)] == [1]
        set_hidden_folders_visible(db, True)
        with open_index(db) as conn:
            assert [a.photo_count for a in albums_in_index(conn)] == [2]

    def test_keresojavaslat_nem_kinalja_a_rejtett_mappat(self, db):
        with open_index(db) as conn:
            assert search_suggestions(conn, "titkos") == ()
        set_hidden_folders_visible(db, True)
        with open_index(db) as conn:
            assert [s.name for s in search_suggestions(conn, "titkos")] == ["titkos"]
