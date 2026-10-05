"""Valódi kattintásos regresszióteszt a színválasztó MRU-rekeszeihez (#4283)."""

import pytest
from PySide6.QtCore import QPoint, QPointF, QSettings, QStandardPaths, Qt
from PySide6.QtTest import QTest


def _item(root, name):
    if root.objectName() == name:
        return root
    for child in root.childItems():
        found = _item(child, name)
        if found is not None:
            return found
    return None


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _click_item(window, item, qt_app):
    scene_pos = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(scene_pos.x()), round(scene_pos.y())),
    )
    qt_app.processEvents()


def _recent_items(swatches):
    return [
        _item(swatches, f"effectParamColor0Recent{index}")
        for index in range(5)
    ]


@pytest.fixture(autouse=True)
def picasapy_settings_identity(qt_app, tmp_path):
    previous_format = QSettings.defaultFormat()
    default_ini_path = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.GenericConfigLocation
    )
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path)
    )
    qt_app.setOrganizationName("PicasaPy")
    qt_app.setApplicationName("PicasaPy")
    settings = QSettings("PicasaPy", "PicasaPy")
    settings.clear()
    try:
        yield
    finally:
        settings.clear()
        settings.sync()
        QSettings.setPath(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            default_ini_path,
        )
        QSettings.setDefaultFormat(previous_format)


def _assert_recent_layout(swatches, recent):
    # A 5 rekesz a spec szerinti x=51, 82, 113, 144, 175 helyen van;
    # a mérések az elem saját koordinátarendszerében ±3 px tűréssel futnak.
    for index, expected_x in enumerate((51, 82, 113, 144, 175)):
        slot = recent[index]
        local_position = slot.mapToItem(swatches, 0, 0)
        assert abs(local_position.x() - expected_x) <= 3
        assert abs(local_position.y() - 15) <= 3
        assert abs(slot.width() - 26) <= 3
        assert abs(slot.height() - 26) <= 3


def test_three_real_color_clicks_update_recent_slots_and_persist(qml_app, qt_app):
    from PySide6.QtCore import QObject

    window, _, _ = qml_app
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = window.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("paramEffectName", "test")
    panel.setProperty("paramEffectParams", [{
        "key": "color",
        "label": "Color",
        "kind": "color",
        "minimum": 0,
        "maximum": 0,
        "step": 1,
        "default": 0,
        "color": "#000000",
    }])
    panel.setProperty("paramEffectValues", ["#000000"])
    panel.setProperty("paramPanelActive", True)
    qt_app.processEvents()
    swatches = _item(panel, "effectParamColor0")
    assert swatches is not None

    colors = ("#ff0000", "#00a651", "#0072bc")
    for index, expected in ((2, colors[0]), (4, colors[1]), (5, colors[2])):
        swatch = _item(swatches, f"effectParamColor0Swatch{index}")
        assert swatch is not None, f"a {expected} színminta nem található"
        _click_item(window, swatch, qt_app)
        assert _variant(panel.property("paramEffectValues"))[0] == expected

    recent = _recent_items(swatches)
    assert all(slot is not None for slot in recent), "az öt MRU-rekesz hiányzik"
    assert [recent[index].property("recentColor") for index in range(3)] == [
        colors[2], colors[1], colors[0]
    ]
    assert [recent[index].property("visible") for index in range(3)] == [
        True,
        True,
        True,
    ]
    _assert_recent_layout(swatches, recent)

    _click_item(window, recent[2], qt_app)
    assert _variant(panel.property("paramEffectValues"))[0] == colors[0]
    recent = _recent_items(swatches)

    eredeti_magassag = window.height()
    for elteres, recent_index, expected in (
        (5, 1, colors[2]),
        (-5, 2, colors[1]),
    ):
        window.setHeight(eredeti_magassag + elteres)
        qt_app.processEvents()
        _assert_recent_layout(swatches, recent)
        _click_item(window, recent[recent_index], qt_app)
        assert _variant(panel.property("paramEffectValues"))[0] == expected
        recent = _recent_items(swatches)
    window.setHeight(eredeti_magassag)
    qt_app.processEvents()

    # Ötnél több különböző választásnál a legrégebbi kiesik.
    for index, expected in ((0, "#ffffff"), (1, "#000000"), (3, "#ffff00"),
                            (6, "#ff7f27"), (7, "#a349a4")):
        swatch = _item(swatches, f"effectParamColor0Swatch{index}")
        _click_item(window, swatch, qt_app)
        assert _variant(panel.property("paramEffectValues"))[0] == expected

    settings = QSettings("PicasaPy", "PicasaPy")
    settings.sync()
    assert [settings.value(f"picker/mru_{index}", "") for index in range(5)] == [
        "#a349a4",
        "#ff7f27",
        "#ffff00",
        "#000000",
        "#ffffff",
    ]
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    restarted_controller = EditController(EditPreviewProvider())
    assert restarted_controller.recentPickerColors == [
        "#a349a4",
        "#ff7f27",
        "#ffff00",
        "#000000",
        "#ffffff",
    ]
