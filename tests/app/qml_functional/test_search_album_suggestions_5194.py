"""#5194: album-javaslat valódi kereséssel és az eredeti elrendezéssel."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


@pytest.fixture(autouse=True)
def _isolated_home_and_xdg(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    for name in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
        path = home / name.removeprefix("XDG_").lower()
        path.mkdir()
        monkeypatch.setenv(name, str(path))


def _wait(qt_app, predicate, timeout: float = 5.0) -> bool:
    return var_feltetelre(qt_app, predicate, timeout)


def _key_clicks(window, text: str) -> None:
    # A PySide6 QTest.keyClicks csak QWidgetet fogad; QQuickWindow-nál a Qt
    # saját, karakterenkénti keyClick eseményeit adjuk a fókuszált mezőnek.
    for character in text:
        QTest.keyClick(window, Qt.Key(ord(character.upper())))


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _click(window, item, qt_app) -> None:
    assert item is not None and item.isVisible()
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _seed_album(controller, tmp_path) -> str:
    from picasapy.index import open_index, sync_tree

    root = tmp_path / "kepek"
    album_folder = root / "Recently Folder"
    album_folder.mkdir(parents=True)
    photo_sections = []
    for index in range(24):
        filename = f"photo_{index:02d}.jpg"
        make_jpeg(album_folder / filename, size=(64, 48))
        photo_sections.append(f"[{filename}]\nalbums=aabb01\n")
    (album_folder / ".picasa.ini").write_text(
        "[.album:aabb01]\nname=Recently Updated\n"
        + "".join(photo_sections),
        encoding="utf-8",
    )
    with open_index(controller._db_path) as conn:
        sync_tree(conn, root)
    controller._reload()
    return "aabb01"


def _render(window, name: str) -> Path:
    output = Path.cwd() / ".bt" / name
    output.parent.mkdir(parents=True, exist_ok=True)
    assert window.grabWindow().save(str(output)), f"nem menthető a render: {output}"
    return output


def test_real_typing_popup_geometry_keyboard_and_reference_renders(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    _seed_album(controller, tmp_path)

    window.show()
    window.requestActivate()
    qt_app.processEvents()
    field = window.findChild(QObject, "searchField")
    popup = window.findChild(QObject, "searchSuggestions")
    search_box = window.findChild(QObject, "toolbarSearchBox")
    assert field is not None and popup is not None and search_box is not None

    _click(window, field, qt_app)
    assert _wait(qt_app, lambda: field.property("activeFocus") is True)
    _key_clicks(window, "recently")
    assert _wait(qt_app, lambda: popup.property("visible") is True), (
        "gépelésre nem nyílt meg az album-javaslatlista"
    )

    suggestions = popup.property("suggestions")
    if hasattr(suggestions, "toVariant"):
        suggestions = suggestions.toVariant()
    assert [(row["kind"], row["name"], row["count"]) for row in suggestions] == [
        ("album", "Recently Updated", 24),
        ("folder", "Recently Folder", 24),
    ]
    _render(window, "5194-11-typing.png")

    QTest.keyClick(window, Qt.Key.Key_Down)
    assert _wait(qt_app, lambda: popup.property("selectedIndex") == 0)
    _render(window, "5194-13-down.png")

    base_height = window.height()
    for height_delta in (-5, 0, 5):
        window.setHeight(base_height + height_delta)
        qt_app.processEvents()
        popup_pos = popup.mapToScene(QPointF(0, 0))
        field_pos = search_box.mapToScene(QPointF(0, 0))
        assert abs(popup_pos.x() - field_pos.x()) <= 3
        assert abs(popup_pos.y() - field_pos.y() - search_box.height()) <= 3
        assert abs(popup.width() - search_box.width()) <= 3

    QTest.keyClick(window, Qt.Key.Key_Escape)
    assert _wait(qt_app, lambda: popup.property("visible") is False)
    assert field.property("text") == "recently"
    QTest.keyClick(window, Qt.Key.Key_Down)
    qt_app.processEvents()
    assert popup.property("visible") is False


def test_clicking_album_suggestion_opens_that_album(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    token = _seed_album(controller, tmp_path)
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    field = window.findChild(QObject, "searchField")
    popup = window.findChild(QObject, "searchSuggestions")
    assert field is not None and popup is not None

    _click(window, field, qt_app)
    assert _wait(qt_app, lambda: field.property("activeFocus") is True)
    _key_clicks(window, "recently")

    def _javaslatok():
        ertek = popup.property("suggestions")
        return ertek.toVariant() if hasattr(ertek, "toVariant") else ertek

    # A lista késleltetve (150 ms) frissül; a sort csak a TELJES szóhoz
    # tartozó, albumot is tartalmazó lista után keressük, különben a régi
    # lista egy éppen lecserélődő sorára kattintanánk.
    assert _wait(
        qt_app,
        lambda: popup.property("visible") is True
        and popup.property("query") == "recently"
        and any(s["kind"] == "album" for s in (_javaslatok() or [])),
    )
    rows = [row for row in _walk(popup) if row.objectName() == "suggestionRow"]
    assert rows and rows[0].isVisible()
    suggestions = _javaslatok()
    album_index = next(
        index
        for index, suggestion in enumerate(suggestions)
        if suggestion["kind"] == "album"
    )
    album_row = next(row for row in rows if row.property("index") == album_index)
    _click(window, album_row, qt_app)

    assert _wait(
        qt_app,
        lambda: controller.currentAlbumToken == token
        and controller.photos.rowCount() == 24,
    ), "az album-javaslat kiválasztása nem nyitotta meg az albumot"
    assert field.property("text") == ""
    assert popup.property("visible") is False
