"""#4398 — a gyorsbillentyű gazdanézet- és fókuszkapui valódi billentyűvel."""

from __future__ import annotations

import time
import re
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest


def _wait_until(qt_app, predicate, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(predicate())


def _click_item(window, item, qt_app) -> None:
    assert item is not None and item.isVisible()
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _visual_children(item):
    for child in item.childItems():
        yield child
        yield from _visual_children(child)


def _find_visual_item(root, object_name):
    return next(
        (item for item in _visual_children(root) if item.objectName() == object_name),
        None,
    )


def _press(window, key, modifiers, qt_app) -> None:
    QTest.keyClick(window, key, modifiers)
    qt_app.processEvents()


def _press_text_keys(window, field, qt_app) -> str:
    initial = str(field.property("text") or "")
    field.setProperty("cursorPosition", len(initial))
    QTest.keyClick(window, Qt.Key.Key_X)
    qt_app.processEvents()
    expected = initial + "x"
    assert field.property("text") == expected

    _press(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier, qt_app)
    assert field.property("selectedText") == expected
    _press(window, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier, qt_app)
    _press(window, Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier, qt_app)
    assert field.property("text") == ""
    _press(window, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier, qt_app)
    assert field.property("text") == expected
    return expected


def _shortcut_blocks(qml_source: str):
    """A Shortcut deklarációkat kapcsos zárójelek szerint vágja ki."""
    for match in re.finditer(r"\bShortcut\s*\{", qml_source):
        opening = qml_source.find("{", match.start(), match.end())
        depth = 0
        index = opening
        quote = None
        while index < len(qml_source):
            char = qml_source[index]
            if quote is not None:
                if char == "\\":
                    index += 2
                    continue
                if char == quote:
                    quote = None
            elif char in "\"'`":
                quote = char
            elif qml_source.startswith("//", index):
                newline = qml_source.find("\n", index)
                index = len(qml_source) if newline < 0 else newline + 1
                continue
            elif qml_source.startswith("/*", index):
                end = qml_source.find("*/", index + 2)
                index = len(qml_source) if end < 0 else end + 2
                continue
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    yield qml_source[opening + 1 : index]
                    break
            index += 1


def _declared_shortcut_sequences(qml_root: Path):
    sequences = []
    for qml_file in sorted(qml_root.rglob("*.qml")):
        source = qml_file.read_text(encoding="utf-8")
        for block in _shortcut_blocks(source):
            match = re.search(r"\bsequence\s*:\s*['\"]([^'\"]+)['\"]", block)
            if match:
                sequences.append(match.group(1))
            elif re.search(r"\bsequences\s*:\s*\[\s*StandardKey\.Cancel\s*\]", block):
                sequences.append("Escape")
            else:
                raise AssertionError(f"nincs leütéshez oldható szekvencia: {qml_file}")
    return sequences


def _open_editor(window, qt_app):
    window.setProperty("selectedIndex", 0)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    controller = window.property("controller")
    if controller is not None:
        controller.setEditorControlsVisible(True)
    viewer.setProperty("editorControlsVisible", True)
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    assert _wait_until(qt_app, lambda: viewer.isVisible())
    viewer.forceActiveFocus()
    return viewer, window.findChild(QObject, "viewerEditorPanel")


def _open_param_slider(panel, qt_app, active_tab):
    panel.setProperty("activeTab", active_tab)
    panel.setProperty("paramEffectName", "shortcut-focus-test")
    panel.setProperty(
        "paramEffectParams",
        [{
            "key": "amount",
            "label": "Amount",
            "kind": "slider",
            "minimum": 0.0,
            "maximum": 100.0,
            "step": 2.0,
            "default": 50.0,
        }],
    )
    panel.setProperty("paramEffectValues", [50.0])
    panel.setProperty("paramPanelActive", True)
    qt_app.processEvents()
    slider = _find_visual_item(panel, "effectParamSlider0")
    assert slider is not None and slider.isVisible()
    return slider


def _record_shortcut_activations(window, activated):
    for shortcut in window.findChildren(QObject):
        try:
            if shortcut.metaObject().className().startswith("QQuickShortcut"):
                name = shortcut.objectName() or str(shortcut.property("sequence"))
                shortcut.activated.connect(
                    lambda name=name: activated.append(name)
                )
        except RuntimeError:
            # A lazily destroyed QML object can remain in findChildren's
            # snapshot while the app is rebuilding its visible tree.
            continue


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_library_thumbnail_shortcut_is_inactive_in_editor(
    qml_app, qt_app, height_delta
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + height_delta)
    window.show()
    window.requestActivate()
    _open_editor(window, qt_app)

    before = window.property("thumbSize")
    _press(window, Qt.Key.Key_1, Qt.KeyboardModifier.ControlModifier, qt_app)

    assert window.property("thumbSize") == before, (
        "a könyvtár Ctrl+1 billentyűje az editor nézetben indexképméretet váltott"
    )

    window.setProperty("viewerOpen", False)
    window.setProperty("thumbSize", 144)
    qt_app.processEvents()
    _press(window, Qt.Key.Key_1, Qt.KeyboardModifier.ControlModifier, qt_app)
    assert _wait_until(qt_app, lambda: window.property("thumbSize") == 96), (
        "a Ctrl+1 nem váltott kis indexképre a könyvtárnézetben"
    )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_search_caption_and_tag_fields_keep_their_keys(
    qml_app, qt_app, height_delta
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + height_delta)
    window.show()
    window.requestActivate()
    qt_app.processEvents()

    field = window.findChild(QObject, "searchField")
    _click_item(window, field, qt_app)
    assert _wait_until(qt_app, lambda: field.property("activeFocus") is True)

    activated = []
    _record_shortcut_activations(window, activated)

    shortcut = window.findChild(QObject, "searchShortcut")
    _press_text_keys(window, field, qt_app)
    _press(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier, qt_app)
    assert field.property("activeFocus") is True, "a Ctrl+F elvette a fókuszt a keresőmezőtől"
    assert shortcut.property("enabled") is False

    # A felirat mező ugyanazt a szöveghelyi billentyűkészletet tartja meg
    # a nézőben; a Ctrl+F a kereső rövidítése lenne, nem a feliraté.
    _controller.setCaptionVisible(True)
    viewer, _panel = _open_editor(window, qt_app)
    caption = window.findChild(QObject, "captionField")
    assert _wait_until(qt_app, lambda: caption is not None and caption.isVisible())
    _click_item(window, caption, qt_app)
    assert _wait_until(qt_app, lambda: caption.property("activeFocus") is True)
    caption_text = _press_text_keys(window, caption, qt_app)
    _press(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier, qt_app)
    assert caption.property("activeFocus") is True
    assert caption.property("text") == caption_text

    # A címkemező Ctrl+T leütése sem zárhatja be az éppen szerkesztett mezőt.
    window.setProperty("viewerOpen", False)
    window.setProperty("selectedIndex", 0)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("activeDrawerTab", "tags")
    qt_app.processEvents()
    tag = window.findChild(QObject, "tagInput")
    assert _wait_until(qt_app, lambda: tag is not None and tag.isVisible())
    assert _wait_until(qt_app, lambda: tag.property("enabled") is True)
    _click_item(window, tag, qt_app)
    tag.forceActiveFocus()
    assert _wait_until(qt_app, lambda: tag.property("activeFocus") is True)
    assert window.property("_szovegmezoneVanFokusz") is True
    _press_text_keys(window, tag, qt_app)
    _press(window, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier, qt_app)
    assert tag.property("activeFocus") is True
    assert window.property("activeDrawerTab") == "tags"
    assert activated == [], f"szövegmező billentyűzés közben Shortcut aktiválódott: {activated}"


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_all_54_shortcut_sequences_are_silent_while_search_has_focus(
    qml_app, qt_app, height_delta
):
    """Mind az 54 QML-kötés szekvenciáját valódi leütéssel próbálja szövegfókuszban."""
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + height_delta)
    window.show()
    window.requestActivate()
    qt_app.processEvents()

    field = window.findChild(QObject, "searchField")
    _click_item(window, field, qt_app)
    assert _wait_until(qt_app, lambda: field.property("activeFocus") is True)

    activated = []
    _record_shortcut_activations(window, activated)

    qml_root = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml"
    sequences = _declared_shortcut_sequences(qml_root)
    assert len(sequences) == 54, f"a QML-leltár {len(sequences)} Shortcut-kötést ad"

    for sequence in sequences:
        parsed = QKeySequence(sequence)
        assert not parsed.isEmpty(), f"nem értelmezhető billentyűszekvencia: {sequence}"
        stroke = parsed[0]
        QTest.keyClick(window, stroke.key(), stroke.keyboardModifiers())
        qt_app.processEvents()
        assert activated == [], (
            f"a {sequence} szekvencia Shortcutot indított keresőmező-fókuszban: "
            f"{activated}"
        )
    field.forceActiveFocus()


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
@pytest.mark.parametrize("tab_index", [1])
def test_editor_slider_character_keys_are_limited_to_tabs_three_to_five(
    qml_app, qt_app, height_delta, tab_index
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + height_delta)
    window.show()
    window.requestActivate()
    _viewer, panel = _open_editor(window, qt_app)
    slider = _open_param_slider(panel, qt_app, tab_index)
    _click_item(window, slider, qt_app)
    assert _wait_until(qt_app, lambda: slider.property("activeFocus") is True)
    assert slider.property("keyboardStepEnabled") is False
    before = float(slider.property("value"))

    for key in (
        Qt.Key.Key_Plus,
        Qt.Key.Key_Equal,
        Qt.Key.Key_Minus,
        Qt.Key.Key_Underscore,
    ):
        _press(window, key, Qt.KeyboardModifier.NoModifier, qt_app)

    assert float(slider.property("value")) == before, (
        "a +, =, - vagy _ billentyű a 3–5. fülön kívül léptette a csúszkát"
    )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_editor_slider_accepts_plus_key_when_keyboard_gate_is_enabled(
    qml_app, qt_app, height_delta
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + height_delta)
    window.show()
    window.requestActivate()
    _viewer, panel = _open_editor(window, qt_app)
    slider = _open_param_slider(panel, qt_app, active_tab=2)
    _click_item(window, slider, qt_app)
    assert _wait_until(qt_app, lambda: slider.property("activeFocus") is True)
    assert slider.property("keyboardStepEnabled") is True

    source = (
        Path(__file__).resolve().parents[3]
        / "src/picasapy/app/qml/PicasaPy/EditorParamPanel.qml"
    ).read_text(encoding="utf-8")
    gate = re.compile(
        r"keyboardStepEnabled:\s*panel\.activeTab\s*>=\s*2\s*"
        r"&&\s*panel\.activeTab\s*<=\s*4"
    )
    assert len(gate.findall(source)) == 2, (
        "az effekt- és ecsetcsúszkáknak a szerkesztő 3–5. füléhez kell kötniük"
    )

    before = float(slider.property("value"))
    step = (float(slider.property("to")) - float(slider.property("from"))) * 0.02

    for key, direction in (
        (Qt.Key.Key_Plus, 1),
        (Qt.Key.Key_Equal, 1),
        (Qt.Key.Key_Minus, -1),
        (Qt.Key.Key_Underscore, -1),
    ):
        before = float(slider.property("value"))
        _press(window, key, Qt.KeyboardModifier.NoModifier, qt_app)
        expected = max(
            float(slider.property("from")),
            min(float(slider.property("to")), before + direction * step),
        )
        assert float(slider.property("value")) == pytest.approx(expected)
