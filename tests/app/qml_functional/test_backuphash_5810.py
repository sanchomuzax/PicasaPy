"""#5810: a Picasa-műveletek backuphash-t írnak a kép ini-szakaszába."""
# rontás-kontroll: picasapy.ini.backuphash.backuphash_for_local_datetime = 65536 → 3 failed

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import load_document, update_document
from picasapy.metadata import read_file_metadata
from support.jpeg_factory import make_minta_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre


_WINDOW_HEIGHT_OFFSETS = (-5, 0, 5)


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(window, name: str):
    found = window.findChild(QObject, name)
    if found is not None:
        return found
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    raise AssertionError(f"A QML-felületen nincs ilyen elem: {name}")


def _child_item(parent, name: str):
    found = parent.findChild(QObject, name)
    if found is not None:
        return found
    for item in _walk(parent):
        if item.objectName() == name:
            return item
    raise AssertionError(f"A {parent.objectName()} panelen nincs ilyen elem: {name}")


def _wait(qt_app, predicate, timeout: float = 10.0) -> bool:
    return var_feltetelre(qt_app, predicate, timeout)


def _click(window, qt_app, item, button=Qt.MouseButton.LeftButton):
    assert _wait(qt_app, lambda: item.isVisible() and item.width() > 0 and item.height() > 0), (
        f"{item.objectName()}: nem látható vagy nincs kattintható mérete"
    )
    target_window = item.window()
    previous_geometry = None

    def intersects_window() -> bool:
        nonlocal previous_geometry
        top_left = item.mapToScene(QPointF(0, 0))
        bottom_right = item.mapToScene(QPointF(item.width(), item.height()))
        geometry = (
            top_left.x(),
            top_left.y(),
            item.width(),
            item.height(),
        )
        on_screen = (
            bottom_right.x() > 0
            and top_left.x() < target_window.width()
            and bottom_right.y() > 0
            and top_left.y() < target_window.height()
        )
        stable = previous_geometry == geometry
        previous_geometry = geometry
        return on_screen and stable

    assert _wait(qt_app, intersects_window), (
        f"{item.objectName()} nem került az ablak látható területére"
    )
    top_left = item.mapToScene(QPointF(0, 0))
    bottom_right = item.mapToScene(QPointF(item.width(), item.height()))
    left = max(0.0, top_left.x())
    top = max(0.0, top_left.y())
    right = min(float(target_window.width()), bottom_right.x())
    bottom = min(float(target_window.height()), bottom_right.y())
    assert left < right and top < bottom, (
        f"{item.objectName()} nem látszik a saját ablakának területén"
    )
    point = QPoint(round((left + right) / 2), round((top + bottom) / 2))
    QTest.mouseClick(
        target_window,
        button,
        Qt.KeyboardModifier.NoModifier,
        point,
    )
    qt_app.processEvents()


def _key_clicks(window, qt_app, text: str) -> None:
    """Karakterenkénti QTest billentyűleütés a QQuickWindow fókuszába."""
    for character in text:
        QTest.keyClick(window, Qt.Key(ord(character.upper())))
        qt_app.processEvents()


def _row(controller, name: str) -> int:
    return next(
        index
        for index, photo in enumerate(controller.photos.photos)
        if photo.name == name
    )


def _section(folder: Path, name: str) -> dict[str, str]:
    section = load_document(folder / ".picasa.ini").section(name)
    return dict(section.items()) if section is not None else {}


def _without_backuphash(values: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in values.items() if key.casefold() != "backuphash"}


def _assert_valid_backuphash(values: dict[str, str], photo_name: str) -> None:
    value = values.get("backuphash")
    assert value is not None, f"[{photo_name}] szakaszból hiányzik a backuphash"
    assert value.isdecimal(), f"a backuphash nem decimális: {value!r}"
    assert 0 <= int(value) <= 0xFFFF, f"a backuphash nem 16 bites: {value!r}"


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Két valódi, mintás JPEG valódi bélyegképpel (a kiadásképhez is)."""

    def kepeket(lib: Path) -> None:
        make_minta_jpeg(lib / "a.jpg", size=(640, 480), seed=11)
        make_minta_jpeg(lib / "b.jpg", size=(640, 480), seed=12)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _valodi_belyegkep_kesz(window) -> bool:
    for elem in _vizualis(window.contentItem()):
        if elem.objectName() != "thumbImage" or not elem.property("source"):
            continue
        kifejezes = QQmlExpression(qmlContext(elem), elem, "status === Image.Ready")
        ertek, hiba = kifejezes.evaluate()
        if not hiba and ertek:
            return True
    return False


def _vizualis(item):
    for gyerek in item.childItems():
        yield gyerek
        yield from _vizualis(gyerek)


@pytest.fixture
def backuphash_app(qml_app, qt_app):
    window, controller, engine = qml_app
    library = Path(controller._roots[0])

    def prepare(document):
        for name, marker in (("a.jpg", "keep-a"), ("b.jpg", "keep-b")):
            for key, value in (
                ("caption", "ini-caption"),
                ("keywords", "ini-tag"),
                ("rotate", "rotate(0)"),
                ("untouched", marker),
            ):
                document = document.with_value(name, key, value)
        return document

    update_document(library / ".picasa.ini", prepare, backup=False)
    with open_index(controller._db_path) as conn:
        sync_tree(conn, str(library))
    controller._reload()
    controller.selectFolder(str(library))
    assert _wait(qt_app, lambda: controller.photos.rowCount() == 2)
    yield window, controller, engine, library


@pytest.mark.parametrize("height_delta", _WINDOW_HEIGHT_OFFSETS)
def test_valodi_kattintas_utan_forgatas_felirat_es_cimke_hash_ezutan_textactive_nelkul(
    backuphash_app, qt_app, height_delta
):
    window, controller, _engine, library = backuphash_app
    base_width = int(window.width())
    window.setWidth(base_width + 320)
    assert _wait(qt_app, lambda: int(window.width()) == base_width + 320)
    base_height = int(window.height())
    target_height = base_height + height_delta
    window.setHeight(target_height)
    assert _wait(qt_app, lambda: int(window.height()) == target_height), (
        f"az ablak magassága {window.height()}, várt: {target_height}"
    )

    row_a = _row(controller, "a.jpg")
    row_b = _row(controller, "b.jpg")
    window.setProperty("selectedIndexes", [row_a])
    window.setProperty("selectedIndex", row_a)
    window.setProperty("viewerOpen", True)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", row_a)
    assert _wait(qt_app, lambda: viewer.isVisible() and viewer.property("currentIndex") == row_a)

    original_a = _section(library, "a.jpg")
    assert "backuphash" not in original_a

    # Forgatás: valódi jobbklikk a nézőn, majd valódi kattintás a menütételen.
    _click(window, qt_app, viewer, Qt.MouseButton.RightButton)
    assert _wait(
        qt_app, lambda: window.findChild(QObject, "viewerContextMenu") is not None
    ), "a jobbklikk nem nyitotta meg a néző helyi menüjét"
    context_menu = _item(window, "viewerContextMenu")
    assert _wait(qt_app, lambda: bool(context_menu.property("visible")))
    _click(window, qt_app, _item(window, "viewerMenuRotateRight"))
    assert _wait(
        qt_app,
        lambda: _section(library, "a.jpg").get("rotate") == "rotate(1)"
        and "backuphash" in _section(library, "a.jpg"),
    ), "a forgatás kattintása után nem jelent meg a backuphash a kép szakaszában"
    after_rotate = _section(library, "a.jpg")
    _assert_valid_backuphash(after_rotate, "a.jpg")
    expected_after_rotate = dict(original_a, rotate="rotate(1)")
    assert _without_backuphash(after_rotate) == expected_after_rotate

    # Felirat: a feliratmezőbe valódi gépelés és Enter írja a JPEG IPTC-jét;
    # az ini-ben a meglévő kulcsok változatlanok, a backuphash megjelenik.
    # A forgatás háttérírása a rács-sor frissítésével zárul; addig Windowson a
    # képfájl foglalt lehet, és a felirat az ini-tartalékútra esne (#5830).
    assert _wait(qt_app, lambda: controller.photos.rotateAt(row_a) == 1), (
        "a forgatás háttérírása nem zárult le"
    )
    update_document(
        library / ".picasa.ini",
        lambda document: document.with_removed("a.jpg", "backuphash"),
        backup=False,
    )
    caption_field = _item(window, "captionField")
    _click(window, qt_app, caption_field)
    assert _wait(qt_app, lambda: bool(caption_field.property("activeFocus"))), (
        "a feliratmező a kattintás után nem kapott fókuszt"
    )
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    _key_clicks(window, qt_app, "caption-5810")
    assert _wait(qt_app, lambda: caption_field.property("text") == "caption-5810"), (
        f"a feliratmező szövege: {caption_field.property('text')!r}"
    )
    QTest.keyClick(window, Qt.Key.Key_Return)
    # #5856: a két feltétel külön lépésben, hogy a windowsos bukás megnevezze
    # a hiányzó részt; a háttérírásnak ott több idő kell.
    assert _wait(
        qt_app,
        lambda: read_file_metadata(library / "a.jpg").caption == "caption-5810",
        20.0,
    ), (
        "a felirat nem került a JPEG IPTC-jébe: "
        f"{read_file_metadata(library / 'a.jpg').caption!r}, "
        f"ini: {_section(library, 'a.jpg')!r}"
    )
    assert _wait(qt_app, lambda: "backuphash" in _section(library, "a.jpg"), 20.0), (
        "a felirat mentése után nem íródott backuphash az ini-be: "
        f"{_section(library, 'a.jpg')!r}"
    )
    after_caption = _section(library, "a.jpg")
    _assert_valid_backuphash(after_caption, "a.jpg")
    assert _without_backuphash(after_caption) == expected_after_rotate

    # Címke: valódi beírás és kattintás a Címkék panel hozzáadó gombján.
    # A felirat háttérírása a rács-sor frissítésével zárul (#5830).
    assert _wait(qt_app, lambda: controller.photos.captionAt(row_a) == "caption-5810"), (
        "a felirat háttérírása nem zárult le"
    )
    update_document(
        library / ".picasa.ini",
        lambda document: document.with_removed("a.jpg", "backuphash"),
        backup=False,
    )
    window.setProperty("viewerOpen", False)
    assert _wait(qt_app, lambda: not viewer.isVisible())
    window.setProperty("activeDrawerTab", "tags")
    tags_panel = _item(window, "tagsPanel")
    tag_field = _child_item(tags_panel, "tagInput")
    assert tag_field.isEnabled(), (
        f"a címkemező nem engedélyezett; kijelölés={window.property('selectedIndexes')}"
    )
    _click(window, qt_app, tag_field)
    assert tag_field.property("activeFocus") is True
    tag_field.setProperty("text", "tag-5810")
    assert tag_field.property("text") == "tag-5810"
    add_button = _child_item(tags_panel, "tagAddButton")
    assert add_button.property("enabled") is True
    _click(window, qt_app, add_button)
    assert _wait(
        qt_app,
        lambda: "tag-5810" in read_file_metadata(library / "a.jpg").keywords
        and "backuphash" in _section(library, "a.jpg"),
    ), "a címke mentése után nem íródott backuphash az ini-be"
    after_tag = _section(library, "a.jpg")
    _assert_valid_backuphash(after_tag, "a.jpg")
    assert _without_backuphash(after_tag) == expected_after_rotate

    screenshot = os.environ.get("PICASAPY_5810_SCREENSHOT")
    if screenshot and height_delta == 0:
        output = Path(screenshot)
        output.parent.mkdir(parents=True, exist_ok=True)
        window.setProperty("viewerOpen", False)
        assert _wait(qt_app, lambda: _valodi_belyegkep_kesz(window)), (
            "a kiadásképhez nem töltődött be a valódi bélyegkép"
        )
        image = window.grabWindow()
        assert not image.isNull(), "a PicasaPy műveletéről készült kiadáskép üres"
        assert image.save(str(output), "PNG"), f"nem menthető a kiadáskép: {output}"

    # Ellenpélda: az új fotó textactive írása nem indít hash-írást.
    window.setProperty("activeDrawerTab", "")
    window.setProperty("selectedIndexes", [row_b])
    window.setProperty("selectedIndex", row_b)
    window.setProperty("viewerOpen", True)
    assert _wait(qt_app, lambda: viewer.isVisible())
    viewer.setProperty("currentIndex", row_b)
    assert _wait(qt_app, lambda: viewer.property("currentIndex") == row_b)
    before_textactive = _section(library, "b.jpg")
    assert "backuphash" not in before_textactive
    if not controller.editorControlsVisible:
        controller.setEditorControlsVisible(True)

    _click(window, qt_app, _item(window, "editToolText"))
    panel = _item(window, "viewerEditorPanel")
    assert _wait(qt_app, lambda: panel.property("textActive") is True)
    _click(window, qt_app, _item(window, "textClickArea"))
    text_field = _item(window, "textContentField")
    _click(window, qt_app, text_field)
    _key_clicks(window, qt_app, "text-5810")
    apply_button = _item(window, "textApplyButton")
    assert _wait(qt_app, lambda: bool(apply_button.property("enabled")))
    _click(window, qt_app, apply_button)
    assert _wait(
        qt_app,
        lambda: _section(library, "b.jpg").get("textactive") == "1",
    ), "a szöveges overlay nem írta ki a textactive=1 értéket"
    after_textactive = _section(library, "b.jpg")
    assert "backuphash" not in after_textactive
    assert _without_backuphash(after_textactive) == before_textactive | {
        "text": after_textactive.get("text", ""),
        "textactive": "1",
    }
