"""#7254: az EXIF Artist szava gépeléskor megjelenik, majd megtalálja a képet."""

from __future__ import annotations

from pathlib import Path

import piexif
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


def _value(obj, name):
    value = obj.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _click(window, item, qt_app):
    assert item is not None and item.isVisible()
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _type_text(window, text):
    for character in text:
        modifier = (
            Qt.KeyboardModifier.ShiftModifier
            if character.isupper()
            else Qt.KeyboardModifier.NoModifier
        )
        QTest.keyClick(window, Qt.Key(ord(character.upper())), modifier)


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_typing_artist_word_suggests_and_searches_the_photo(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    library = Path(controller._db_path).parent / "kepek"
    photo = make_jpeg(library / "artist.jpg", size=(64, 48))
    piexif.insert(
        piexif.dump(
            {
                "0th": {piexif.ImageIFD.Artist: b"Diego Delso"},
                "Exif": {},
                "GPS": {},
            }
        ),
        str(photo),
    )
    with open_index(controller._db_path) as conn:
        sync_tree(conn, library)
    controller._reload()

    window.show()
    window.setHeight(window.height() + height_delta)
    window.requestActivate()
    qt_app.processEvents()
    field = window.findChild(QObject, "searchField")
    popup = window.findChild(QObject, "searchSuggestions")
    assert field is not None and popup is not None

    _click(window, field, qt_app)
    assert var_feltetelre(qt_app, lambda: field.property("activeFocus") is True)
    _type_text(window, "del")

    def _suggestion_ready():
        rows = _value(popup, "suggestions") or []
        return (
            popup.property("query") == "del"
            and any(
                row["kind"] == "word"
                and row["name"] == "delso"
                and row["count"] == 1
                for row in rows
            )
        )

    assert var_feltetelre(qt_app, _suggestion_ready, 10.0)

    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    _type_text(window, "diego delso")
    assert var_feltetelre(
        qt_app,
        lambda: controller.searchQuery == "diego delso"
        and controller.searchActive
        and controller.searchResultCount == 1
        and controller.photos.rowCount() == 1,
        10.0,
    )
    assert field.property("text") == "diego delso"
    assert controller.photos.photos[0].name == "artist.jpg"
