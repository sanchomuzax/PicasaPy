"""#7217: javaslatlista korlátja, ikonjai és mappasorának valódi kiválasztása."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre
from tests.support.javaslatsor_kattintas import kattints_a_javaslatsorra


def _wait(qt_app, predicate, timeout: float = 10.0) -> bool:
    return var_feltetelre(qt_app, predicate, timeout)


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _value(obj, name):
    value = obj.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _type_text(window, text: str) -> None:
    for character in text:
        QTest.keyClick(window, Qt.Key(ord(character.upper())))


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


def _seed_suggestions(controller, tmp_path) -> str:
    root = tmp_path / "kepek"
    folder = root / "ai-folder"
    folder.mkdir()
    make_jpeg(folder / "target.jpg", size=(64, 48))
    (folder / ".picasa.ini").write_text(
        "[target.jpg]\nkeywords=ai\n", encoding="utf-8"
    )

    other = root / "other"
    other.mkdir()
    make_jpeg(other / "mainstream.jpg", size=(64, 48))
    (other / ".picasa.ini").write_text(
        "[mainstream.jpg]\nkeywords=mainstream\n", encoding="utf-8"
    )

    many = root / "many"
    many.mkdir()
    sections = []
    for number in range(1, 16):
        filename = f"word_{number:02}.jpg"
        make_jpeg(many / filename, size=(64, 48))
        sections.append(f"[{filename}]\nkeywords=ai{number}\n")
    (many / ".picasa.ini").write_text("".join(sections), encoding="utf-8")

    with open_index(controller._db_path) as conn:
        sync_tree(conn, root)
    controller._reload()
    return str(folder)


def _render(window, name: str) -> Path:
    output = Path.cwd() / ".tmp" / name
    output.parent.mkdir(parents=True, exist_ok=True)
    assert window.grabWindow().save(str(output)), f"nem menthető a render: {output}"
    return output


def test_search_suggestion_rows_and_folder_click_keep_search(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    target = _seed_suggestions(controller, tmp_path)

    window.show()
    window.requestActivate()
    qt_app.processEvents()
    field = window.findChild(QObject, "searchField")
    popup = window.findChild(QObject, "searchSuggestions")
    search_box = window.findChild(QObject, "toolbarSearchBox")
    pane = window.findChild(QObject, "folderPane")
    assert field is not None and popup is not None and search_box is not None
    assert pane is not None

    _click(window, field, qt_app)
    assert _wait(qt_app, lambda: field.property("activeFocus") is True)
    _type_text(window, "ai")

    def _ai_rows_ready():
        rows = _value(popup, "suggestions") or []
        return (
            popup.property("visible") is True
            and popup.property("query") == "ai"
            and len(rows) == 10
        )

    assert _wait(qt_app, _ai_rows_ready)
    suggestions = _value(popup, "suggestions")
    assert len(suggestions) <= 10
    kinds = [row["kind"] for row in suggestions]
    folder_index = kinds.index("folder")
    first_word_index = kinds.index("word")
    assert folder_index < first_word_index

    rows = [item for item in _walk(popup) if item.objectName() == "suggestionRow"]
    folder_row = next(
        row for row in rows if _value(row, "modelData")["kind"] == "folder"
    )
    word_row = next(
        row for row in rows if _value(row, "modelData")["kind"] == "word"
    )
    assert any(
        item.objectName() == "suggestionFolderIcon" and item.isVisible()
        for item in _walk(folder_row)
    )
    assert any(
        item.objectName() == "suggestionWordIcon" and item.isVisible()
        for item in _walk(word_row)
    )

    base_height = window.height()
    for delta in (-5, 0, 5):
        window.setHeight(base_height + delta)
        qt_app.processEvents()
        popup_pos = popup.mapToScene(QPointF(0, 0))
        search_pos = search_box.mapToScene(QPointF(0, 0))
        assert abs(popup_pos.x() - search_pos.x()) <= 3
        assert abs(popup_pos.y() - search_pos.y() - search_box.height()) <= 3
        assert abs(popup.width() - search_box.width()) <= 3
    _render(window, "7217-search-suggestions.png")

    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    _type_text(window, "main")

    def _mainstream_ready():
        current = _value(popup, "suggestions") or []
        return (
            popup.property("query") == "main"
            and any(
                row["kind"] == "word" and row["name"] == "mainstream"
                for row in current
            )
        )

    assert _wait(qt_app, _mainstream_ready)

    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    _type_text(window, "ai")

    def _folder_ready():
        current = _value(popup, "suggestions") or []
        return (
            popup.property("query") == "ai"
            and any(
                row["kind"] == "folder" and row["param"] == target
                for row in current
            )
        )

    assert _wait(qt_app, _folder_ready)

    # #7317: a sort a TARTALMA alapján keressük, nem a lista egy korábbi
    # pillanatképéből vett sorszámmal: a javaslatlista frissülhet a kettő
    # között, és akkor a sorszám alatt már egy szójavaslat (pl. „ai8”) áll.
    def _folder_row():
        for row in _walk(popup):
            if row.objectName() != "suggestionRow" or not row.isVisible():
                continue
            data = _value(row, "modelData") or {}
            if data.get("kind") == "folder" and data.get("param") == target:
                return row
        return None

    assert _wait(qt_app, lambda: _folder_row() is not None)
    # #7324: a sor helye a lista újraépülése után áll be; addig a régi
    # helyén egy szójavaslat állhat, és a kattintás arra esne.
    kattints_a_javaslatsorra(window, popup, _folder_row, qt_app)

    assert _wait(
        qt_app,
        lambda: controller.searchActive is True
        and field.property("text") == "ai-folder ",
    )
    assert field.property("text") == "ai-folder "
    assert controller.searchQuery == "ai-folder"
    assert controller.currentFolder == target
    assert _value(pane, "selectedPath") == target
