"""#4554: az Árnyalás színe a panelen választható, kirajzolódik és mentődik."""

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest


def _find_item(root, object_name):
    if root.objectName() == object_name:
        return root
    for child in root.childItems():
        found = _find_item(child, object_name)
        if found is not None:
            return found
    return None


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _click_item(window, item, qt_app):
    """Valódi egérkattintás az elem felépült, aktuális helyén."""
    scene_pos = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=scene_pos.toPoint(),
    )
    qt_app.processEvents()


def test_picnik_tint_color_click_changes_preview_and_is_saved(
    qml_app, qt_app, tmp_path
):
    window, _controller, engine = qml_app
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()

    panel = window.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("activeTab", 2)
    qt_app.processEvents()
    _click_item(window, panel.findChild(QObject, "effectTint"), qt_app)
    assert panel.property("paramPanelActive") is True

    params = _variant(panel.property("paramEffectParams"))
    values = _variant(panel.property("paramEffectValues"))
    assert [param["key"] for param in params] == ["fade", "color"]
    assert values == [0.0, "#80cfff"]

    color_label = _find_item(panel, "effectParamColorLabel1")
    color_picker = _find_item(panel, "effectParamColor1")
    assert color_label is not None and color_label.isVisible()
    assert color_label.property("text") == "Tint Color"
    assert color_picker is not None and color_picker.isVisible()
    assert color_picker.property("currentColor") == "#80cfff"

    original_height = window.height()
    # A ±5 px ablakmagasság-változásnál is az elem friss geometriájából
    # számítjuk a kattintási pontot.
    for delta, swatch_index, expected in (
        (5, 4, "#00a651"),
        (-5, 2, "#ff0000"),
        (0, 5, "#0072bc"),
    ):
        window.setHeight(original_height + delta)
        qt_app.processEvents()
        swatch = _find_item(
            color_picker, f"effectParamColor1Swatch{swatch_index}"
        )
        assert swatch is not None and swatch.isVisible()
        _click_item(window, swatch, qt_app)
        assert _variant(panel.property("paramEffectValues")) == [0.0, expected]

    _click_item(
        window,
        panel.findChild(QObject, "effectParamApplyButton"),
        qt_app,
    )
    ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
    assert "filters=PicnikTint=1,0.000000,000072bc;" in ini_text

    edit_controller = engine.rootContext().contextProperty("editController")
    preview_id = str(edit_controller.previewSource).split(
        "image://editpreview/", 1
    )[1].split("?", 1)[0]
    rendered = edit_controller._provider.requestImage(preview_id, None, None)
    assert not rendered.isNull()
    middle = rendered.pixelColor(rendered.width() // 2, rendered.height() // 2)
    assert middle.blue() > middle.red() and middle.blue() > middle.green(), (
        f"a kiválasztott kék árnyalat nem látszik a képen: {middle.name()}"
    )
