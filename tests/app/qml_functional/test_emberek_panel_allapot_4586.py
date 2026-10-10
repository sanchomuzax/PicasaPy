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


def _scan_state(ctl, qt_app, *, running: bool, unchecked: int = 0):
    """Az arckeresés állapota — a háttérszál setterein át, a fő szálból."""
    ctl._set_scan_percent(50 if running else -1)
    ctl._set_unchecked_files(unchecked)
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
        _scan_state(ctl, qt_app, running=True, unchecked=7)
        assert _header(window) == (
            "Loading faces for file..., 7 files unchecked.")

        _scan_state(ctl, qt_app, running=False)
        assert _header(window) == "Who is in these photos?"

    def test_several_clicked_photos_show_loading2_with_the_count(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        ctl = _scan_controller(engine)
        _scan_state(ctl, qt_app, running=True, unchecked=3)

        _select(window, controller, qt_app, lib, "c.jpg", "d.jpg")

        assert _header(window) == (
            "Loading faces for 2 files..., 3 files unchecked.")

    def test_no_selection_shows_no_loading_text(self, qml_app, qt_app, tmp_path):
        window, controller, engine = qml_app
        _library(window, controller, qt_app, tmp_path)
        _scan_state(_scan_controller(engine), qt_app, running=True, unchecked=3)

        _unselect(window, qt_app)

        assert _header(window) is None

    def test_person_album_looks_for_other_people_without_unchecked(
        self, qml_app, qt_app, tmp_path
    ):
        """Személy-albumban a Looking áll, és az Unchecked utótag nem."""
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        _person_album(controller, qt_app)
        _scan_state(_scan_controller(engine), qt_app, running=True, unchecked=9)

        _select(window, controller, qt_app, lib, "a.jpg")

        assert _header(window) == "Looking for other people..."

    def test_unchecked_suffix_follows_a_named_header(
        self, qml_app, qt_app, tmp_path
    ):
        """Nem futó keresésnél is lehet hátralévő szám? Nem: 0 → nincs utótag."""
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        ctl = _scan_controller(engine)
        _select(window, controller, qt_app, lib, "a.jpg")

        _scan_state(ctl, qt_app, running=False, unchecked=0)

        assert _header(window) == "People in these photos:"

    def test_a_photo_with_a_new_face_refreshes_the_list_during_the_scan(
        self, qml_app, qt_app, tmp_path
    ):
        """A `facesStored` jelre a lista a keresés közben frissül."""
        window, controller, engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        ctl = _scan_controller(engine)
        _select(window, controller, qt_app, lib, "c.jpg")
        assert _child(window, "peoplePanelHeader").property("text") == (
            "Who is in these photos?")

        (lib / ".picasa.ini").write_text(
            (lib / ".picasa.ini").read_text(encoding="utf-8")
            + "[c.jpg]\nfaces=rect64(1e00280045006e00),1111111111111111\n",
            encoding="utf-8",
        )
        ctl.facesStored.emit()
        _settle(qt_app)

        assert _header(window) == "In this photo:"


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
