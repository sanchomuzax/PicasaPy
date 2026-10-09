"""A rendszer betűtípusának kattintásos választása (#4546)."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest
import pytest

from picasapy.app import edit_preview as preview_module
from picasapy.ini import load_document
from picasapy.ini.text_overlay import parse_text


def _varj(qt_app, predicate, timeout_s=3.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(predicate())


def _kattints(elem, qt_app):
    point = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(elem.window(), Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, point)
    qt_app.processEvents()


def _sor(lista, index, qt_app):
    expression = QQmlExpression(
        qmlContext(lista), lista, f"itemAtIndex({index})"
    )
    talalat = []

    def _epul():
        value, error = expression.evaluate()
        assert not error, expression.error()
        if value is not None:
            talalat.append(value)
        return value is not None

    assert _varj(qt_app, _epul), f"a betűcsalád-lista {index}. sora nem épült fel"
    return talalat[-1]


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_a_legordulobol_kattintott_rendszerbetu_elonezetre_es_inibe_kerul(
    qml_app, qt_app, tmp_path, monkeypatch, height_delta
):
    window, _app_controller, engine = qml_app
    height = window.height()
    window.setHeight(height + height_delta)
    qt_app.processEvents()
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()

    edit = engine.rootContext().contextProperty("editController")
    system_families = sorted(
        set(QFontDatabase.families()), key=lambda family: (family.casefold(), family)
    )
    offered = [entry["key"] for entry in edit.textFontFamilies]
    assert offered == system_families, (
        "a betűtípus-legördülő nem a telepített rendszerbetűket kínálja"
    )

    current = str(edit.property("textFontFamily"))
    current_index = offered.index(current) if current in offered else 0
    target_index = current_index + 1 if current_index + 1 < len(offered) else current_index - 1
    assert target_index >= 0 and target_index != current_index
    chosen = offered[target_index]

    calls = []
    original = preview_module.apply_text_overlay

    def track_render(*args, **kwargs):
        calls.append(kwargs["font_family"])
        return original(*args, **kwargs)

    monkeypatch.setattr(preview_module, "apply_text_overlay", track_render)

    panel = window.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("textActive", True)
    qt_app.processEvents()
    field = window.findChild(QObject, "textContentField")
    field.setProperty("text", "System font")
    edit.previewTextPlacement(0.3, 0.6)
    qt_app.processEvents()

    combo = window.findChild(QObject, "textFontFamilyBox")
    assert combo is not None
    _kattints(combo, qt_app)
    popup = combo.findChild(QObject, "picasaComboPopup")
    lista = combo.findChild(QObject, "picasaComboList")
    assert popup is not None and lista is not None
    assert _varj(qt_app, lambda: popup.property("visible") is True)
    row = _sor(lista, target_index, qt_app)
    _kattints(row, qt_app)

    assert _varj(qt_app, lambda: str(edit.property("textFontFamily")) == chosen)
    assert calls[-1] == chosen, "a kiválasztott család nem jutott el a képi rajzolóig"

    apply_button = window.findChild(QObject, "textApplyButton")
    assert apply_button is not None and apply_button.property("enabled") is True
    _kattints(apply_button, qt_app)

    ini = load_document(tmp_path / "kepek" / ".picasa.ini")
    saved = parse_text(ini.section("a.jpg").get("text"))
    assert saved.primary.font == chosen

    edit.endEdit()
    edit.beginEdit("1", str(tmp_path / "kepek" / "a.jpg"))
    assert edit.textFontFamily == chosen
