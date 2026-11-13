"""Az Időrend virtuális friss albumának és kezelőinek felületi útjai (#6902)."""

import sys
from datetime import datetime
from pathlib import Path

import piexif
import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.ini import RECENT_ALBUM_TOKEN
from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre


def _photo(path: Path, taken_at: str) -> None:
    make_jpeg(path, size=(640, 480))
    piexif.insert(
        piexif.dump(
            {
                "0th": {},
                "Exif": {
                    piexif.ExifIFD.DateTimeOriginal: taken_at.encode("ascii")
                },
                "GPS": {},
            }
        ),
        str(path),
    )


def _timeline_photos(root: Path) -> None:
    groups = (
        ("2009_majus", ("2009:05:14 10:00:00",)),
        ("2014_november", ("2014:11:02 15:30:00",)),
        (
            "2019_marcius",
            (
                "2019:03:08 09:15:00",
                "2019:03:09 09:15:00",
                datetime.now().strftime("%Y:%m:%d %H:%M:%S"),
                datetime.now().strftime("%Y:%m:%d %H:%M:%S"),
            ),
        ),
    )
    for folder_name, dates in groups:
        folder = root / folder_name
        folder.mkdir()
        for index, taken_at in enumerate(dates, start=1):
            _photo(folder / f"{folder_name}_{index:02d}.jpg", taken_at)


def _child(parent, object_name):
    child = parent.findChild(QObject, object_name)
    assert child is not None, f"{object_name} nem található"
    return child


def _wait(qt_app, condition, message: str, seconds: float = 10.0) -> None:
    assert var_feltetelre(qt_app, condition, seconds), message


@pytest.fixture(scope="module")
def qml_app_6902(
    qt_app, tmp_path_factory, _module_qml_warnings, _module_user_folder_guard
):
    yield from _build_qml_app(
        qt_app,
        tmp_path_factory.mktemp("idorend-6902"),
        kepeket_keszit=_timeline_photos,
        belyegkep_meret=256,
        valodi_belyegkep=True,
        keep_modul=sys.modules[__name__],
    )


@pytest.fixture(autouse=True)
def _close_timeline_after_each_test(qml_app_6902, qt_app):
    yield
    window, _controller, _engine = qml_app_6902
    if window.property("timelineOpen") is True:
        timeline = _child(window, "timelineView")
        QTest.keyClick(timeline, Qt.Key.Key_Escape)
        _wait(
            qt_app,
            lambda: window.property("timelineOpen") is False,
            "az automatikus Escape nem zárta be az Időrendet",
        )


def _open_timeline(qml_app_6902, qt_app, height_delta: int = 0):
    window, controller, engine = qml_app_6902
    window.requestActivate()
    _wait(qt_app, window.isActive, "a főablak nem lett aktív")
    QTest.keyClick(window, Qt.Key.Key_5, Qt.KeyboardModifier.ControlModifier)
    _wait(
        qt_app,
        lambda: window.property("timelineOpen") is True,
        "a Ctrl+5 nem nyitotta meg az Időrendet",
    )
    timeline = _child(window, "timelineView")
    timeline.requestActivate()
    _wait(qt_app, timeline.isActive, "az Időrend nem kapott fókuszt")
    timeline.setProperty("visibility", timeline.property("windowedVisibility"))
    expected_height = 800 + height_delta
    timeline.resize(1280, expected_height)
    _wait(
        qt_app,
        lambda: timeline.width() == 1280 and timeline.height() == expected_height,
        "az Időrend tesztablakának mérete nem állt be",
    )
    return window, controller, engine, timeline


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_valodi_sliderhuzas_frissiti_a_fejlecet_es_4000_ms_mozgast_indit(
    qml_app_6902, qt_app, height_delta
):
    window, _controller, _engine, timeline = _open_timeline(
        qml_app_6902, qt_app, height_delta
    )
    timeline_controller = _engine.rootContext().contextProperty("timelineController")
    collections = timeline_controller.collections
    recent_index = next(
        index
        for index, collection in enumerate(collections)
        if collection["albumToken"] == RECENT_ALBUM_TOKEN
    )
    assert recent_index > 0
    assert collections[recent_index]["count"] == 2
    assert {photo["name"] for photo in collections[recent_index]["photos"]} == {
        "2019_marcius_03.jpg",
        "2019_marcius_04.jpg",
    }

    panel = _child(timeline, "timelinePanel")
    slider = _child(timeline, "timelineSliderMouseArea")
    start_point = slider.mapToItem(
        timeline.contentItem(), QPointF(slider.width() / 2, slider.height() / 2)
    ).toPoint()
    slider_y = slider.mapToItem(
        panel, QPointF(slider.width() / 2, slider.height() / 2)
    ).y()
    target_point = panel.mapToItem(
        timeline.contentItem(),
        QPointF(
            float(panel.property("sliderAreaX"))
            + float(panel.property("sliderAreaWidth")),
            slider_y,
        ),
    ).toPoint()
    original_offset = timeline.property("carouselOffset")

    QTest.mousePress(timeline, Qt.MouseButton.LeftButton, pos=start_point)
    _wait(
        qt_app,
        lambda: timeline.property("draggingSlider") is True,
        "a valódi csúszka-nyomás nem indította el a húzást",
    )
    QTest.mouseMove(timeline, target_point)
    _wait(
        qt_app,
        lambda: timeline.property("pendingSliderIndex") == recent_index,
        "a húzás nem választotta ki a Recently Updated kártyát",
    )
    name = _child(timeline, "timelineCollectionName")
    date = _child(timeline, "timelineCollectionDate")
    _wait(
        qt_app,
        lambda: name.property("text") == "Recently Updated",
        "a fejléc húzás közben nem követte a fogantyút",
    )
    assert date.property("text") == collections[recent_index]["dateLabel"]
    assert timeline.property("currentIndex") == 0
    assert timeline.property("carouselOffset") == original_offset

    QTest.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=target_point)
    assert timeline.property("animationDurationMs") == 4000
    _wait(
        qt_app,
        lambda: timeline.property("currentIndex") == recent_index,
        "a felengedési animáció nem érte el a Recently Updated kártyát",
        seconds=12.0,
    )
    _wait(
        qt_app,
        lambda: timeline.property("currentCardsLoaded") is True,
        "a Recently Updated kártya képei nem töltődtek be",
    )

    QTest.keyClick(timeline, Qt.Key.Key_Escape)
    _wait(
        qt_app,
        lambda: window.property("timelineOpen") is False,
        "az Escape nem zárta be az Időrendet a húzás után",
    )

def test_fel_le_nyilak_a_bal_jobb_2000_ms_mozgasat_hasznaljak(
    qml_app_6902, qt_app
):
    _window, _controller, _engine, timeline = _open_timeline(qml_app_6902, qt_app)

    QTest.keyClick(timeline, Qt.Key.Key_Down)
    _wait(
        qt_app,
        lambda: timeline.property("currentIndex") == 1,
        "a le nyíl nem lépett a következő kártyára",
    )
    assert timeline.property("animationDurationMs") == 2000

    QTest.keyClick(timeline, Qt.Key.Key_Up)
    _wait(
        qt_app,
        lambda: timeline.property("currentIndex") == 0,
        "a fel nyíl nem lépett vissza az előző kártyára",
    )
    assert timeline.property("animationDurationMs") == 2000

    QTest.keyClick(timeline, Qt.Key.Key_Escape)
    _wait(
        qt_app,
        lambda: _window.property("timelineOpen") is False,
        "az Escape nem zárta be az Időrendet a nyílpróba után",
    )


def test_escape_mappafokusznal_a_mappat_es_elso_kepet_jeloli_ki(
    qml_app_6902, qt_app
):
    window, controller, engine, timeline = _open_timeline(qml_app_6902, qt_app)
    collections = engine.rootContext().contextProperty("timelineController").collections
    assert collections[0]["kind"] == "folder"
    first_photo = collections[0]["firstPhotoPath"]

    QTest.keyClick(timeline, Qt.Key.Key_Escape)
    _wait(
        qt_app,
        lambda: window.property("timelineOpen") is False,
        "az Escape nem zárta be az Időrendet",
    )

    assert controller.currentFolder == str(Path(first_photo).parent)
    first_row = controller.photos.rowOfPath(first_photo)
    assert window.property("selectedIndex") == first_row
    assert window.property("selectedIndexes").toVariant() == [first_row]


def test_escape_recently_updated_fokusznal_megtartja_a_belépési_nezetet(
    qml_app_6902, qt_app
):
    window, controller, engine, timeline = _open_timeline(qml_app_6902, qt_app)
    entry_folder = controller.currentFolder
    entry_album = controller.currentAlbumToken
    entry_selected_index = window.property("selectedIndex")
    entry_selected_indexes = window.property("selectedIndexes").toVariant()
    collections = engine.rootContext().contextProperty("timelineController").collections
    recent_index = next(
        index
        for index, collection in enumerate(collections)
        if collection["albumToken"] == RECENT_ALBUM_TOKEN
    )
    for index in range(recent_index):
        QTest.keyClick(timeline, Qt.Key.Key_Right)
        expected_index = index + 1
        _wait(
            qt_app,
            lambda expected_index=expected_index: timeline.property("currentIndex")
            == expected_index,
            "a jobb nyíl nem érte el a Recently Updated kártyát",
        )

    assert collections[recent_index]["albumToken"] == RECENT_ALBUM_TOKEN
    QTest.keyClick(timeline, Qt.Key.Key_Escape)
    _wait(
        qt_app,
        lambda: window.property("timelineOpen") is False,
        "az Escape nem zárta be az Időrendet",
    )
    assert controller.currentFolder == entry_folder
    assert controller.currentAlbumToken == entry_album
    assert window.property("selectedIndex") == entry_selected_index
    assert window.property("selectedIndexes").toVariant() == entry_selected_indexes
