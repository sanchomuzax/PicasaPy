"""#5935: a vágás-javaslatok képi előnézetek, cím és stratégiacímke nélkül."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre


def _list_property(obj, name):
    value = obj.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _open_crop(window, qt_app):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = window.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
    panel.setProperty("cropActive", True)
    qt_app.processEvents()
    return panel


def _button_center(button):
    scene_point = button.mapToScene(
        QPointF(button.width() / 2, button.height() / 2)
    )
    return QPoint(round(scene_point.x()), round(scene_point.y()))


def _selection_matches(overlay, suggestion):
    rect = overlay.property("cropRect")
    return (
        overlay.property("hasSelection") is True
        and rect.x() == suggestion["x"]
        and rect.y() == suggestion["y"]
        and rect.width() == suggestion["w"]
        and rect.height() == suggestion["h"]
    )


def test_a_javaslatok_renderelt_elonezetek_cim_es_felirat_nelkul(
    qml_app, qt_app, tmp_path
):
    window, _, _ = qml_app
    panel = _open_crop(window, qt_app)
    assert var_feltetelre(
        qt_app, lambda: len(_list_property(panel, "cropSuggestions") or []) == 3
    ), "a vágópanel nem három javaslatot töltött be"

    feliratok = [
        obj.property("text")
        for obj in panel.findChildren(QObject)
        if obj.property("text") is not None
    ]
    assert "Suggested crops" not in feliratok

    for index in range(3):
        button = window.findChild(QObject, f"cropSuggestion{index}")
        assert button is not None and button.isVisible(), index
        assert button.property("label") == "", (
            f"a(z) {index}. előnézeten stratégiacímke maradt"
        )
        label = window.findChild(QObject, f"cropSuggestion{index}Label")
        assert label is not None and label.property("text") == "", index
        thumbnail = window.findChild(QObject, f"cropSuggestion{index}ThumbCrop")
        assert thumbnail is not None
        assert var_feltetelre(
            qt_app,
            lambda image=thumbnail: image.property("visible") is True
            and image.width() > 0
            and image.height() > 0,
        ), f"a(z) {index}. képi előnézet nem rajzolódott ki"

    # A kiadási képkocka is a valódi QML-ablak renderelt kimenetéből készül.
    rendered = window.grabWindow()
    assert not rendered.isNull()
    assert rendered.save(str(tmp_path / "vagas-panel-5935.png"), "PNG")


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_mindharom_javaslatra_kattintva_az_adott_kijeloles_toltodik_be(
    qml_app, qt_app, height_delta
):
    window, _, _ = qml_app
    window.setHeight(window.height() + height_delta)
    qt_app.processEvents()
    panel = _open_crop(window, qt_app)
    suggestions = _list_property(panel, "cropSuggestions")
    assert len(suggestions) == 3, suggestions
    overlay = window.findChild(QObject, "cropOverlay")
    assert overlay is not None

    for index, suggestion in enumerate(suggestions):
        button = window.findChild(QObject, f"cropSuggestion{index}")
        assert button is not None and button.isVisible(), index
        point = _button_center(button)
        assert 0 <= point.x() < window.width()
        assert 0 <= point.y() < window.height()
        QTest.mouseMove(window, point, 10)
        qt_app.processEvents()
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            point,
        )
        assert var_feltetelre(
            qt_app,
            lambda expected=suggestion: _selection_matches(overlay, expected),
        ), f"a(z) {index}. kattintás nem a saját javaslatát töltötte be"
        overlay.resetSelection()
        qt_app.processEvents()
