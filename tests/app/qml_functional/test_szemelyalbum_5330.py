"""#5330: a személyalbum fejléce, arcsávja és a teljes mappa-feed."""

from __future__ import annotations

from pathlib import Path

import cv2
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.ini import parse_document, update_document
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre

_PERSON = "Teszt Elek"
_FOLDER = "kepek"
_PERSON_ID = "0123456789abcdef"
_FACE_RECT = "1e00280045006e00"
_WINDOW_HEIGHT_OFFSETS = (-5, 0, 5)


def _make_person_album_library(library: Path) -> None:
    """24 fotó a mappa-rácshoz; kettőn az eredeti arc-címke formátumával."""
    portrait_path = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "face_type_a_name_reference_en38.png"
    )
    portrait_source = cv2.imread(str(portrait_path), cv2.IMREAD_COLOR)
    assert portrait_source is not None, f"A próbaportré nem olvasható: {portrait_path}"
    portrait = portrait_source[138:572, 96:444]
    assert portrait.size > 0

    filenames = []
    for index in range(24):
        filename = f"{index:02d}-photo.jpg"
        filenames.append(filename)
        target = library / filename
        make_jpeg(target, size=(480, 360), taken_at="2026:10:18 12:00:00")
        if index < 2:
            image = portrait if index == 0 else cv2.flip(portrait, 1)
            if index == 0:
                image = cv2.cvtColor(
                    cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR
                )
            assert cv2.imwrite(str(target), image)

    update_document(
        library / ".picasa.ini",
        lambda _old: parse_document(
            "[Contacts2]\n"
            f"{_PERSON_ID}={_PERSON};;\n"
            f"[{filenames[0]}]\nfaces=rect64({_FACE_RECT}),{_PERSON_ID}\n"
            f"[{filenames[1]}]\nfaces=rect64({_FACE_RECT}),{_PERSON_ID}\n"
        ),
        backup=False,
    )


@pytest.fixture
def qml_app_5330(qt_app, tmp_path, monkeypatch, request):
    """Teljes app izolált profillal és renderelt bélyegképekkel."""
    isolated_home = tmp_path / "home"
    for variable, folder in (
        ("HOME", isolated_home),
        ("XDG_CONFIG_HOME", isolated_home / ".config"),
        ("XDG_DATA_HOME", isolated_home / ".local" / "share"),
        ("XDG_CACHE_HOME", isolated_home / ".cache"),
        ("XDG_STATE_HOME", isolated_home / ".local" / "state"),
    ):
        folder.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(variable, str(folder))

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_make_person_album_library,
        belyegkep_meret=220,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _find_item(window, object_name: str):
    return next(
        (
            item
            for item in _walk(window.contentItem())
            if item.objectName() == object_name
        ),
        None,
    )


def _find_items(window, object_name: str):
    return [
        item
        for item in _walk(window.contentItem())
        if item.objectName() == object_name
    ]


def _click(window, qt_app, item) -> None:
    assert item is not None, "A kattintandó felületi elem hiányzik."
    assert item.width() > 0 and item.height() > 0
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def test_person_sidebar_row_opens_reference_album_layout(qml_app_5330, qt_app):
    window, controller, _engine = qml_app_5330
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    person_row = _find_item(window, f"personItem_{_PERSON}")
    assert person_row is not None
    assert var_feltetelre(qt_app, lambda: person_row.isVisible(), 3.0)
    assert controller.photos.rowCount() == 24

    for offset in _WINDOW_HEIGHT_OFFSETS:
        expected_height = 1005 + offset
        window.setHeight(expected_height)
        assert var_feltetelre(
            qt_app, lambda height=expected_height: window.height() == height, 3.0
        )
        _click(window, qt_app, person_row)
        assert var_feltetelre(
            qt_app, lambda: controller.currentPersonName == _PERSON, 3.0
        )

        header_name = _find_item(window, "personAlbumName")
        avatar = _find_item(window, "personAlbumAvatar")
        remove = _find_item(window, "headerRemovePersonButton")
        face_strip = _find_item(window, "personAlbumFaceStrip")
        face_image = _find_item(window, "personAlbumFaceImage")
        face_images = _find_items(window, "personAlbumFaceImage")
        back_to_all = _find_item(window, "searchBackToViewAll")
        assert header_name is not None and header_name.property("text") == _PERSON
        assert avatar is not None and avatar.property("source")
        assert remove is not None and remove.property("enabled") is False
        assert face_strip is not None and face_strip.property("count") == 2
        assert face_image is not None and face_image.isVisible()
        assert len(face_images) == 2
        assert var_feltetelre(
            qt_app,
            lambda images=face_images: all(
                item.property("imageReady") for item in images
            ),
            3.0,
        ), "Az arcsáv bélyegképei nem töltődtek be."
        assert var_feltetelre(
            qt_app, lambda image=avatar: image.property("imageReady"), 3.0
        ), f"A fejléc-arckép nem töltődött be: {avatar.property('status')}"
        assert back_to_all is None or not back_to_all.isVisible()
        assert not any(
            item.isVisible()
            for item in _find_items(window, "headerMoreSuggestionsButton")
        )

        # A referencia geometriáját a saját fejléc- és sáv-elemekhez
        # viszonyítjuk, nem a Pi ablakkeretéhez. A fotók alatti pixeleket
        # mérjük; a feliratok betűképe gépenként eltérhet.
        person_header = _find_item(window, "personAlbumHeader")
        play = _find_item(window, "headerPlayButton")
        collage = _find_item(window, "headerCollageButton")
        movie = _find_item(window, "faceHeaderMovieButton")
        face_movie = _find_item(window, "faceHeaderFaceMovieButton")
        set_thumbnail = _find_item(window, "headerSetPersonThumbnailButton")
        zoom = _find_item(window, "headerZoomContainer")
        face_zoom = _find_item(window, "headerFaceZoomButton")
        picture_zoom = _find_item(window, "headerPictureZoomButton")
        assert all(
            item is not None
            for item in (
                person_header,
                play,
                collage,
                movie,
                face_movie,
                set_thumbnail,
                zoom,
                face_zoom,
                picture_zoom,
            )
        )
        assert play.isVisible() and collage.isVisible() and movie.isVisible()
        assert face_movie.isVisible() and set_thumbnail.isVisible()
        assert set_thumbnail.property("enabled") is False
        assert face_zoom.property("checked") is False
        assert picture_zoom.property("checked") is True
        assert not _find_item(window, "folderSyncRow").isVisible()
        assert not _find_item(window, "folderDescriptionField").isVisible()

        button_x = [
            item.mapToItem(person_header, 0, 0).x()
            for item in (play, collage, movie, face_movie, set_thumbnail)
        ]
        button_y = [
            item.mapToItem(person_header, 0, 0).y()
            for item in (play, collage, movie, face_movie, set_thumbnail)
        ]
        assert button_x == sorted(button_x)
        assert all(abs(y - 57) <= 3 for y in button_y)
        avatar_pos = avatar.mapToItem(person_header, 0, 0)
        face_pos = face_image.mapToItem(person_header, 0, 0)
        zoom_pos = zoom.mapToItem(person_header, 0, 0)
        assert abs(avatar_pos.x() - 12) <= 3
        assert abs(avatar_pos.y() - 8) <= 3
        assert abs(face_pos.x() - 37) <= 3
        assert abs(face_pos.y() - 122) <= 3
        assert abs(zoom_pos.x() + zoom.width() - person_header.width() + 13) <= 3
        assert abs(button_x[0] - 80) <= 3
        assert abs(button_x[1] - 116) <= 3
        assert abs(button_x[2] - 150) <= 3
        assert abs(button_x[3] - 181) <= 3
        assert abs(button_x[4] - 212) <= 3
        remove_pos = remove.mapToItem(person_header, 0, 0)
        assert abs(remove_pos.x() + remove.width() - person_header.width() + 15) <= 3
        assert abs(remove_pos.y() - 58) <= 3

        # A teljes album tartalmi sávját a bal oldali hasáb geometriájához
        # kötjük, hogy a kártya belső margói ne tolják el a Picasa-fejlécet.
        main_split = _find_item(window, "mainSplit")
        assert main_split is not None
        avatar_in_main = avatar.mapToItem(main_split, 0, 0)
        main_split_in_window = main_split.mapToScene(QPointF(0, 0))
        avatar_in_window = avatar.mapToScene(QPointF(0, 0))
        assert abs(avatar_in_main.x() - (folder_pane.width() + 19)) <= 3
        assert abs(avatar_in_window.y() - main_split_in_window.y() - 16) <= 3

        # A teljes könyvtári mappa-feed marad a személyfotók külön arcsávja alatt.
        assert controller.photos.rowCount() == 24
        assert len(controller.feedGroups) == 1
        assert controller.feedGroups[0]["count"] == 24
        if offset == 0:
            output = Path.cwd() / ".bt" / "kep_5330.png"
            output.parent.mkdir(parents=True, exist_ok=True)
            image = window.grabWindow()
            assert not image.isNull()
            assert image.save(str(output))

        feed_header = _find_item(window, "personAlbumFeedHeader")
        photo_grid = _find_item(window, "photoGrid")
        assert feed_header is not None and feed_header.height() > 0, (
            f"A személy-feed fejléce nem kapott magasságot: "
            f"{feed_header.height() if feed_header else 'nincs elem'}"
        )
        assert photo_grid is not None and abs(
            photo_grid.property("contentY") - photo_grid.property("originY")
        ) <= 1

        assert var_feltetelre(
            qt_app,
            lambda: any(
                item.isVisible() and item.property("text") == _FOLDER
                for item in _find_items(window, "folderTitleText")
            ),
            3.0,
        )
        assert any(
            item.isVisible() and item.property("text") == _FOLDER
            for item in _find_items(window, "folderTitleText")
        )
        assert any(item.isVisible() for item in _find_items(window, "thumbImage"))
        first_folder_frame = min(
            (
                item
                for item in _find_items(window, "thumbFrame")
                if item.isVisible()
            ),
            key=lambda item: item.mapToItem(feed_header, 0, 0).y(),
        )
        folder_frame_top = first_folder_frame.mapToItem(
            feed_header, 0, 0
        ).y()
        assert abs(folder_frame_top - 423) <= 3
