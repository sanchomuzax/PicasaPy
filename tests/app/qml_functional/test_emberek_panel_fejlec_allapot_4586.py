"""QML-funkcionális teszt: az Emberek-panel állapot-feliratai — #4586.

A háttér-arckeresés közben a panel (spec `picasa-arcfelismeres.md` 9/b):

    betöltés  → egysoros ág: „Loading faces for file..." (Loading1)
                többsoros ág: személy-album ? „Looking for other people..."
                                            : „Loading faces for %d files..."
    hátralévő fájlok, nem személy-album → a fejléc mögé
                „, %d files unchecked." (Unchecked)
    Név nélküliek album + lenyomat-számítás → „Sorting face data, N%"

A kijelölés VALÓDI kattintás a rács celláira; az arckeresés állapotát a
valódi `FaceScanController` állítja (ugyanazokkal a setterekkel, amelyeket a
háttérszál hív), és a panel a kattintás UTÁN, a keresés közben vált.

Amit ez a teszt NEM mér: a feliratok képernyőképes egyezését az eredetivel —
csak a renderelt fejléc-szöveget a döntési fa szerint. A `SortingFaces`
(„Sorting faces...") felirat szándékosan nincs: a spec nem mondja meg, mikor
jelenik meg, és nincs hozzá valódi esemény.
"""

from __future__ import annotations

from PySide6.QtTest import QTest

import test_emberek_panel_fejlec_3566 as fejlec_teszt
from test_emberek_panel_fejlec_3566 import (
    _child,
    _header,
    _library,
    _person_album,
    _select,
    _settle,
    _unselect,
)


def _scan_controller(engine):
    ctl = engine.rootContext().contextProperty("faceScanController")
    assert ctl is not None
    return ctl


def _scan_state(ctl, qt_app, lib, *pending: str):
    """Futó keresés állapota: a MÉG nem átvizsgált fotók (a worker halmaza).
    Üres felsorolás = nem fut keresés. A fő szálból, a worker setterein át."""
    from picasapy.app.face_scan_controller import _path_key

    with ctl._pending_lock:
        ctl._pending_paths = {_path_key(lib / name) for name in pending}
    ctl._set_scan_percent(50 if pending else -1)
    ctl._set_unchecked_files(len(pending))
    _settle(qt_app)


class TestLoading:
    def test_one_clicked_photo_shows_loading1_with_unchecked_suffix(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        ctl = _scan_controller(engine)

        _select(window, controller, qt_app, lib, "c.jpg")
        assert _header(window) == "Who is in these photos?"

        # a keresés a kijelölés UTÁN indul — a panel menet közben vált
        _scan_state(ctl, qt_app, lib, "c.jpg", "d.jpg")
        assert _header(window) == (
            "Loading faces for file..., 1 files unchecked.")

        # a c.jpg elkészül, a d.jpg még nem: a kijelölésre már nincs betöltés
        _scan_state(ctl, qt_app, lib, "d.jpg")
        assert _header(window) == "Who is in these photos?"

        _scan_state(ctl, qt_app, lib)
        assert _header(window) == "Who is in these photos?"

    def test_scan_running_elsewhere_keeps_the_in_this_photo_header(
        self, qml_app, qt_app, tmp_path
    ):
        """Regressziőr: az automatikus keresés végigjárja a könyvtárat, de a
        már átvizsgált kijelölt képnél a fejléc nem változik."""
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        ctl = _scan_controller(engine)
        _scan_state(ctl, qt_app, lib, "c.jpg", "d.jpg")

        _select(window, controller, qt_app, lib, "b.jpg")

        assert _header(window) == "In this photo:"

    def test_several_clicked_photos_show_loading2_with_the_count(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        ctl = _scan_controller(engine)
        _scan_state(ctl, qt_app, lib, "c.jpg", "d.jpg")

        _select(window, controller, qt_app, lib, "c.jpg", "a.jpg")

        # a kijelölt fájlok száma 2, ebből egy ellenőrizetlen
        assert _header(window) == (
            "Loading faces for 2 files..., 1 files unchecked.")

    def test_no_selection_shows_no_loading_text(self, qml_app, qt_app, tmp_path):
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        _scan_state(_scan_controller(engine), qt_app, lib, "c.jpg")

        _unselect(window, qt_app)

        assert _header(window) is None

    def test_person_album_looks_for_other_people_without_unchecked(
        self, qml_app, qt_app, tmp_path
    ):
        """Személy-albumban a Looking áll, és az Unchecked utótag nem."""
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        _person_album(controller, qt_app)
        _scan_state(_scan_controller(engine), qt_app, lib, "a.jpg")

        _select(window, controller, qt_app, lib, "a.jpg")

        assert _header(window) == "Looking for other people..."

    def test_no_suffix_when_nothing_unchecked(self, qml_app, qt_app, tmp_path):
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        _select(window, controller, qt_app, lib, "a.jpg")

        _scan_state(_scan_controller(engine), qt_app, lib)

        assert _header(window) == "People in these photos:"

    def test_unnamed_album_never_shows_loading2(self, qml_app, qt_app, tmp_path):
        """A Név nélküliek albumban a kijelölés arcoké — nincs fájl-betöltés."""
        window, controller, engine = qml_app
        album = fejlec_teszt.TestUnnamedAlbum()
        lib = _library(window, controller, qt_app, tmp_path)
        face_id = album._seed_unnamed_face(tmp_path, "c.jpg")
        _scan_state(_scan_controller(engine), qt_app, lib, "c.jpg")
        album._open(window, qt_app)
        album._click_face_tile(window, qt_app, face_id)

        assert _header(window) == "Who is in these photos?"

    def test_a_new_unnamed_face_refreshes_the_list_during_the_scan(
        self, qml_app, qt_app, tmp_path
    ):
        """Futó keresés + SQLite-ba írt névtelen arc → a `facesStored` jelre
        (összevonva, ~500 ms) frissül a panel arc-listája."""
        window, controller, engine = qml_app
        album = fejlec_teszt.TestUnnamedAlbum()
        lib = _library(window, controller, qt_app, tmp_path)
        ctl = _scan_controller(engine)
        _select(window, controller, qt_app, lib, "c.jpg")
        _scan_state(ctl, qt_app, lib, "c.jpg", "d.jpg")
        panel = _child(window, "peoplePanel")
        assert len(panel.property("unnamedFacesHere")) == 0

        album._seed_unnamed_face(tmp_path, "c.jpg")
        ctl.facesStored.emit()
        QTest.qWait(900)
        _settle(qt_app)

        assert len(panel.property("unnamedFacesHere")) == 1


class TestSortingData:
    def test_unnamed_album_shows_the_embedding_percentage(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, engine = qml_app
        album = fejlec_teszt.TestUnnamedAlbum()
        _library(window, controller, qt_app, tmp_path)
        face_id = album._seed_unnamed_face(tmp_path, "c.jpg")
        ctl = _scan_controller(engine)
        album._open(window, qt_app)
        album._click_face_tile(window, qt_app, face_id)
        assert _header(window) == "Who is in these photos?"

        ctl._set_sorting_percent(40)
        _settle(qt_app)
        assert _header(window) == "Sorting face data, 40%"

        ctl._set_sorting_percent(-1)
        _settle(qt_app)
        assert _header(window) == "Who is in these photos?"

    def test_the_percentage_is_not_shown_outside_the_unnamed_album(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        _select(window, controller, qt_app, lib, "c.jpg")

        _scan_controller(engine)._set_sorting_percent(40)
        _settle(qt_app)

        assert _header(window) == "Who is in these photos?"
