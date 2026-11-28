"""#7491: a Vörösszem útmutató az eredeti mezőből nő, ha a tördelés igényli."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Property, QTranslator, QUrl
from PySide6.QtGui import QFont
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

import picasapy.app

_QML_DIR = Path(picasapy.app.__file__).parent / "qml"
_I18N_DIR = Path(picasapy.app.__file__).parent / "i18n"
_QML_FILE = _QML_DIR / "PicasaPy" / "EditorRedeyePanel.qml"
_KEEPALIVE: list[object] = []

_ENGLISH_GUIDE = (
    "Click, hold, and drag the mouse around each eye separately "
    "to select it. A selection box appears over the area. "
    "Release the mouse to complete your selection. The Photo is "
    "displayed with the red-eye removed."
)


class _EditControllerStub(QObject):
    @Property(str, constant=True)
    def previewSource(self):
        return "image://editpreview/42?rev=1"

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self):
        return []


def _render(qt_app, width: int, height: int, translator: QTranslator):
    view = QQuickView()
    view.engine().addImportPath(str(_QML_DIR))
    stub = _EditControllerStub()
    view.engine().rootContext().setContextProperty("editController", stub)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    component = QQmlComponent(view.engine())
    component.setData(
        b"""
        import QtQuick
        import QtQuick.Layouts
        import PicasaPy 1.0
        Item {
            objectName: "redeyeFitRoot"
            EditorPanel {
                objectName: "redeyeFitPanel"
                anchors.fill: parent
                redeyeActive: true
            }
        }
        """,
        QUrl(),
    )
    assert not component.errors(), [error.toString() for error in component.errors()]
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    _KEEPALIVE.extend((view, root, component, stub, translator))
    view.show()
    qt_app.processEvents()
    return view, root


def _item(root: QObject, name: str) -> QObject:
    result = root.findChild(QObject, name)
    assert result is not None, f"A QML-fában hiányzik: {name}"
    return result


def _top_in_root(item: QObject, root: QObject) -> float:
    return item.mapToItem(root, QPointF(0, 0)).y()


def _wait_for_layout(qt_app, root, block, guide, note, buttons) -> None:
    """Határidőig várja meg, míg a szöveg és a gombok geometriája beáll."""
    deadline = time.monotonic() + 3.0
    previous = None
    while time.monotonic() < deadline:
        qt_app.processEvents()
        state = (
            round(block.width(), 2),
            round(block.height(), 2),
            round(guide.property("contentHeight"), 2),
            round(note.property("contentHeight"), 2),
            tuple(round(_top_in_root(button, root), 2) for button in buttons),
        )
        if state == previous:
            return
        previous = state
        time.sleep(0.05)
    raise AssertionError("A vörösszem-panel elrendezése 3 másodpercen belül nem állt be")


def _assert_layout(qt_app, view, root, width, guide, note, block, buttons):
    text_height = guide.height() + note.height()
    assert guide.height() + 0.5 >= guide.property("contentHeight"), (
        "Az útmutató tényleges szövegmagassága nagyobb a kirajzolt eleménél: "
        f"{guide.property('contentHeight'):.1f} > {guide.height():.1f} px"
    )
    assert note.height() + 0.5 >= note.property("contentHeight"), (
        "A megjegyzés tényleges szövegmagassága nagyobb a kirajzolt eleménél: "
        f"{note.property('contentHeight'):.1f} > {note.height():.1f} px"
    )
    assert block.width() == pytest.approx(min(242, width - 20), abs=0.5), (
        "Az útmutatómező nem az eredeti 242 px-es szélességet követi, "
        f"illetve a szűk panelben nem fér el: {block.width():.1f} px"
    )
    assert block.height() + 0.5 >= max(129, text_height), (
        "A szöveg nem fér el az eredeti 129 px-es blokkból növő mezőben: "
        f"szöveg={text_height:.1f} px, blokk={block.height():.1f} px"
    )

    guide_top = _top_in_root(guide, root)
    note_top = _top_in_root(note, root)
    block_top = _top_in_root(block, root)
    assert guide_top == pytest.approx(block_top, abs=0.5)
    assert note_top == pytest.approx(guide_top + guide.height(), abs=0.5), (
        "A megjegyzés nem közvetlenül az útmutató után jelenik meg"
    )

    note_bottom = note_top + note.height()
    block_bottom = block_top + block.height()
    first_button_top = _top_in_root(buttons[0], root)
    assert first_button_top >= note_bottom - 0.5, (
        "A gombsor eltakarja a Vörösszem-panel útmutatójának végét"
    )
    assert first_button_top - block_bottom == pytest.approx(36, abs=0.5), (
        "A szöveg növekedése nem tolta le a gombokat az eredeti 36 px-es térközzel"
    )
    assert all(_top_in_root(button, root) >= note_bottom - 0.5 for button in buttons)


def test_a_betumeret_es_a_sorkoz_az_eredeti_szerint_rogzitett():
    """A betű nem zsugorodhat; a 14 px-es, mért sorköz maradjon rögzített."""
    source = _QML_FILE.read_text(encoding="utf-8")
    instruction_section = source.split('objectName: "redeyeAutoResultLabel"', 1)[0]
    assert instruction_section.count("font.pixelSize: Theme.fontSize - 1") >= 2
    assert instruction_section.count("lineHeightMode: Text.FixedHeight") >= 2
    assert instruction_section.count("lineHeight: redeyePanel.sorkoz") >= 2
    assert "Text.Fit" not in instruction_section
    assert "minimumPixelSize" not in instruction_section


@pytest.mark.parametrize("width", [260, 280])
@pytest.mark.parametrize("language", ["en", "hu", "de"])
def test_a_forditott_szoveg_a_blokkot_noveli_es_a_gombokat_lejjebb_tolja(
    qt_app, width: int, language: str
):
    translator = QTranslator()
    assert translator.load(str(_I18N_DIR / f"picasapy_{language}.qm")), language
    qt_app.installTranslator(translator)
    view = None
    try:
        view, root = _render(qt_app, width, 900, translator)
        block = _item(root, "redeyeInstructionBlock")
        guide = _item(root, "redeyeGuideText")
        note = _item(root, "redeyeFrameHintLabel")
        buttons = [
            _item(root, name)
            for name in (
                "redeyeAutoButton",
                "redeyeResetButton",
                "redeyeApplyButton",
            )
        ]
        assert guide.property("text")
        if language != "en":
            assert guide.property("text") != _ENGLISH_GUIDE, (
                f"A {language} fordító nem a valódi panelfordítást adta vissza"
            )

        native_font = QFont(guide.property("font"))
        native_line_count = guide.property("lineCount") + note.property("lineCount")
        native_button_top = _top_in_root(buttons[0], root)
        native_block_height = block.height()
        for height_delta in (-5, 0, 5):
            view.resize(width, 900 + height_delta)
            root.setWidth(width)
            root.setHeight(900 + height_delta)
            _wait_for_layout(qt_app, root, block, guide, note, buttons)
            _assert_layout(qt_app, view, root, width, guide, note, block, buttons)
            assert _top_in_root(buttons[0], root) == pytest.approx(
                native_button_top, abs=0.5
            ), "Az ablakmagasság ±5 px-es változása elmozdította a gombokat"
            assert block.height() == pytest.approx(native_block_height, abs=0.5)

        # A helyi CI-gépen a Windows betűszélességét nagyobb próbaméret
        # szimulálja. A sorköz forrásból továbbra is rögzített 14 px.
        wide_font = QFont(native_font)
        wide_font.setPixelSize(max(18, native_font.pixelSize() + 5))
        wide_font.setStretch(135)
        guide.setProperty("font", wide_font)
        note.setProperty("font", wide_font)
        wide_font_size = guide.property("font").pixelSize()
        assert wide_font_size == wide_font.pixelSize()

        wide_heights = []
        wide_button_tops = []
        for height_delta in (-5, 0, 5):
            view.resize(width, 900 + height_delta)
            root.setWidth(width)
            root.setHeight(900 + height_delta)
            _wait_for_layout(qt_app, root, block, guide, note, buttons)
            _assert_layout(qt_app, view, root, width, guide, note, block, buttons)
            wide_heights.append(block.height())
            wide_button_tops.append(_top_in_root(buttons[0], root))

        wide_line_count = guide.property("lineCount") + note.property("lineCount")
        assert wide_line_count > native_line_count, (
            f"A {language} szélesbetűs próbája nem kényszerített ki több sort"
        )
        assert max(wide_heights) > native_block_height, (
            "A több sorra törő szöveg mellett a mező nem nőtt meg"
        )
        assert min(wide_button_tops) > native_button_top, (
            "A blokk növekedése nem tolta le a szomszédos gombokat"
        )
    finally:
        qt_app.removeTranslator(translator)
        if view is not None:
            view.close()
