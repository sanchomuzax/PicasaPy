"""#26: `PeopleMixin` — a bal hasáb Emberek gyűjteménye és a személy-szűrt
nézet.

A mixin ÖNÁLLÓAN, egy minimális host-osztályon tesztelt (a
`test_custom_collections_controller_320.py` mintája) — a valódi
`AppController`-be kötés (`controller.py`, forró fájl) az integrátor
feladata (ld. jelentés a `_view_mode`/`_refresh_view`/`_reload` ág
felvételéről)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings

from support.jpeg_factory import make_jpeg

_ROY = "b8e4117cf1d6615b"
_ZOE = "c9f5228de2a7726c"
_RECT = "3f840000c3509f84"


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "a.jpg")
    make_jpeg(root / "b.jpg")
    (root / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY};\n"
        f"[b.jpg]\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def host(qt_app, tmp_path, library):
    from picasapy.app.people_controller import PeopleMixin
    from picasapy.index import open_index, sync_tree

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)

    class _Host(PeopleMixin, QObject):
        def __init__(self, db_path):
            super().__init__()
            self._db_path = db_path
            self._view_mode = ("folder", "")
            self._filter_active = False
            self._filter_status = ""
            self._shown: tuple = ()
            self._init_people()

        def _show(self, records):
            self._shown = records

        def _get_settings(self):
            """#1767: a `people` property a rendezési módot a
            beállításokból olvassa (`view/peopleSort`). A valódi gazda az
            `AppController`, ott ez megvan — a próbagazdának is meg kell
            adni, különben nem a valódi utat mérnénk."""
            if getattr(self, "_beallitasok", None) is None:
                self._beallitasok = QSettings(
                    str(Path(self._db_path).parent / "settings.ini"),
                    QSettings.Format.IniFormat,
                )
            return self._beallitasok

    instance = _Host(tmp_path / "index.db")
    with open_index(tmp_path / "index.db") as conn:
        instance._load_people(conn)
    return instance


class TestPeopleProperty:
    def test_people_is_a_list(self, host):
        # #232: a QML-ben a tuple NEM tömb.
        assert isinstance(host.people, list)

    def test_person_has_name_and_count(self, host):
        assert host.people == [
            {"name": "Roy Avery", "count": 1, "thumbnailUrl": ""}
        ]

    def test_signal_emitted_on_load(self, tmp_path, library, qt_app):
        from picasapy.app.people_controller import PeopleMixin
        from picasapy.index import open_index, sync_tree

        class _Host(PeopleMixin, QObject):
            def __init__(self, db_path):
                super().__init__()
                self._db_path = db_path
                self._view_mode = ("folder", "")
                self._init_people()

            def _show(self, records):
                pass

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        instance = _Host(tmp_path / "index.db")
        events = []
        instance.peopleChanged.connect(lambda: events.append(True))
        with open_index(tmp_path / "index.db") as conn:
            instance._load_people(conn)
        assert events == [True]

    def test_person_movie_sources_skip_empty_albums_and_keep_model_order(
        self, host, library
    ):
        from picasapy.index.people import PersonRecord
        from picasapy.index import open_index, sync_tree
        from tests.support.jpeg_factory import make_jpeg

        make_jpeg(library / "c.jpg")
        make_jpeg(library / "d.jpg")
        (library / ".picasa.ini").write_text(
            f"[Contacts2]\n{_ROY}=Roy Avery;;\n{_ZOE}=Zoe Zed;;\n"
            f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY};\n"
            f"[b.jpg]\n[c.jpg]\nfaces=rect64({_RECT}),{_ZOE};\n"
            f"[d.jpg]\nfaces=rect64({_RECT}),{_ZOE};\n",
            encoding="utf-8",
        )
        with open_index(host._db_path) as conn:
            sync_tree(conn, library)

        # A +0x2bc-listának megfelelő modell sorrendje nem a People-hasáb
        # aktuális rendezése. Az üres alsó lista kiesik, a többi album képei
        # az albumon belüli sorrendben követik egymást.
        host._people = (
            PersonRecord("Zoe Zed", 2),
            PersonRecord("Üres album", 0),
            PersonRecord("Roy Avery", 1),
        )

        from PySide6.QtCore import QUrl

        forrasok = host.personMovieSourceUrls()
        assert [Path(QUrl(url).toLocalFile()).name for url in forrasok] == [
            "c.jpg", "d.jpg", "a.jpg",
        ]


class TestShowPerson:
    def test_show_person_fills_grid(self, host):
        host.showPerson("Roy Avery")
        assert len(host._shown) == 1
        assert host._shown[0].name == "a.jpg"

    def test_show_person_activates_filter(self, host):
        host.showPerson("Roy Avery")
        assert host._filter_active is True
        assert host.currentPersonName == "Roy Avery"

    def test_unknown_name_gives_empty_grid(self, host):
        host.showPerson("Nincs Ilyen")
        assert host._shown == ()

    def test_empty_name_is_a_no_op(self, host):
        host.showPerson("Roy Avery")
        host.showPerson("")
        assert len(host._shown) == 1  # a korábbi eredmény megmaradt


class TestRefreshPeopleView:
    def test_refresh_handles_person_mode(self, host):
        host._view_mode = ("person", "Roy Avery")
        handled = host._refresh_people_view("person", "Roy Avery")
        assert handled is True
        assert len(host._shown) == 1

    def test_refresh_ignores_other_modes(self, host):
        handled = host._refresh_people_view("folder", "")
        assert handled is False


class TestPeopleOfRows:
    """#26: az Emberek-panel első szakasza — „In this photo:"."""

    @pytest.fixture
    def host_rows(self, qt_app, tmp_path, library):
        _ANNA = "a1a2a3a4a5a6a7a8"
        (library / ".picasa.ini").write_text(
            f"[Contacts2]\n{_ROY}=Roy Avery;;\n{_ANNA}=Anna Kis;;\n"
            f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY};"
            f"rect64({_RECT}),{_ANNA};\n"
            f"[b.jpg]\nfaces=rect64({_RECT}),{_ROY};\n",
            encoding="utf-8",
        )
        from picasapy.app.people_controller import PeopleMixin
        from picasapy.index import all_photos, open_index, sync_tree

        db = tmp_path / "sorok.db"
        with open_index(db) as conn:
            sync_tree(conn, library)
            photos = all_photos(conn)

        class _Host(PeopleMixin, QObject):
            def __init__(self, db_path):
                super().__init__()
                self._db_path = db_path
                self._view_mode = ("folder", "")
                self._init_people()

            def _rows_to_photos(self, rows):
                return [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]

        return _Host(db), photos

    def test_it_lists_the_named_people_on_the_selection(self, host_rows):
        host, photos = host_rows
        rows = list(range(len(photos)))

        found = {p["name"]: p["count"] for p in host.peopleOfRows(rows)}

        assert found == {"Roy Avery": 2, "Anna Kis": 1}

    def test_a_single_photo_lists_only_its_own_people(self, host_rows):
        host, photos = host_rows
        row = [i for i, p in enumerate(photos) if p.name == "b.jpg"]

        found = {p["name"] for p in host.peopleOfRows(row)}

        assert found == {"Roy Avery"}

    def test_an_empty_selection_is_not_an_error(self, host_rows):
        host, _photos = host_rows
        assert host.peopleOfRows([]) == []

    def test_named_people_include_their_photo_id_rect_and_cropped_url(
        self, host_rows
    ):
        from picasapy.ini.rect64 import decode_rect64

        host, photos = host_rows
        row = next(i for i, photo in enumerate(photos) if photo.name == "a.jpg")

        anna = next(
            person for person in host.peopleOfRows([row])
            if person["name"] == "Anna Kis"
        )

        rect = decode_rect64(_RECT)
        assert anna["photo_id"] == photos[row].id
        assert anna["rect"] == [rect.left, rect.top, rect.right, rect.bottom]
        assert anna["thumbUrl"].startswith(f"image://thumbs/{photos[row].id}?")
        assert "&fz=" in anna["thumbUrl"]

    def test_unnamed_faces_are_returned_only_for_selected_photos(self, host_rows):
        from picasapy.faces.detector import FaceDetection, FaceLandmarks
        from picasapy.index import open_index, replace_faces

        host, photos = host_rows
        a_row = next(i for i, photo in enumerate(photos) if photo.name == "a.jpg")
        b_row = next(i for i, photo in enumerate(photos) if photo.name == "b.jpg")
        detection = FaceDetection(
            left=1, top=1, right=4, bottom=5, score=0.99,
            landmarks=FaceLandmarks(
                right_eye=(2, 2), left_eye=(3, 2), nose=(2.5, 3),
                mouth_right=(2, 4), mouth_left=(3, 4),
            ),
        )
        with open_index(host._db_path) as conn:
            replace_faces(conn, photos[a_row].id, [detection])
            replace_faces(conn, photos[b_row].id, [detection])
            conn.commit()

        found = host.unnamedFacesOfRows([a_row])

        assert len(found) == 1
        assert found[0]["photo_id"] == photos[a_row].id
        assert found[0]["rect"] == [0.125, 1 / 6, 0.5, 5 / 6]
        assert found[0]["thumbUrl"].startswith(
            f"image://thumbs/{photos[a_row].id}?"
        )
        assert "&fz=" in found[0]["thumbUrl"]
