"""Az egyszeri Quick Tags Autofill valódi gombkattintással (#7053)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QPoint, QPointF, QObject, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import open_index
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre


@pytest.fixture
def qml_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path)


def _seed_keywords(controller, values: dict[str, str]) -> None:
    with open_index(controller._db_path) as conn:
        for name, keywords in values.items():
            conn.execute(
                "UPDATE photos SET keywords_ini = ?, keywords_file = ? "
                "WHERE name = ?",
                (keywords, keywords, name),
            )
        conn.commit()
    controller.quickTagsChanged.emit()


def _click_item(window, qt_app, item: QQuickItem) -> None:
    assert var_feltetelre(
        qt_app,
        lambda: item.isVisible() and item.width() > 0 and item.height() > 0,
        3.0,
    ), "a kattintandó vezérlő nem épült fel"
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _open_dialog(window, qt_app):
    window.setProperty("activeDrawerTab", "tags")
    assert var_feltetelre(
        qt_app,
        lambda: window.findChild(QQuickItem, "quickTagsGearButton") is not None,
        3.0,
    ), "a gyorscímke konfigurációgomb nem épült fel"
    dialog = window.findChild(QObject, "quickTagsConfigDialog")
    assert dialog is not None, "a gyorscímke konfigurációs ablak hiányzik"
    QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
    assert var_feltetelre(
        qt_app, lambda: dialog is not None and dialog.property("visible"), 3.0
    ), "a gyorscímke konfigurációs ablak nem nyílt meg"
    return dialog


def _autofill_button(window, qt_app) -> QQuickItem:
    button = window.findChild(QQuickItem, "quickTagsAutoFillButton")
    assert var_feltetelre(
        qt_app,
        lambda: button is not None and button.width() > 0,
        3.0,
    ), "az Autofill gomb nem épült fel"
    return button


def _fields(window):
    fields = [
        window.findChild(QQuickItem, f"quickTagField{i}") for i in range(10)
    ]
    assert all(field is not None for field in fields), "nem mind a tíz mező épült fel"
    return fields


def _click_autofill(window, qt_app):
    button = _autofill_button(window, qt_app)
    assert button.property("enabled") is True
    _click_item(window, qt_app, button)


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_reserved_recent_click_fills_only_empty_fields_in_order(
    qml_app, qt_app, magassag_eltolas
):
    window, controller, _engine = qml_app
    _seed_keywords(
        controller,
        {
            "a.jpg": "legutobbi, Nap, Nap, nap",
            "b.jpg": "alpha, beta",
        },
    )
    settings = controller._get_settings()
    settings.setValue("quickTags/recentKeywords", ["legutobbi"])
    controller.setQuickTagsReserveRecent(True)
    controller.setQuickTagLabel(0, "kézi nulla")
    controller.setQuickTagLabel(1, "kézi egy")
    controller.setQuickTagLabel(3, "már kitöltött")
    window.setHeight(window.height() + magassag_eltolas)

    _open_dialog(window, qt_app)
    mezok = _fields(window)
    assert [mezok[i].property("text") for i in range(10)] == [
        "kézi nulla", "kézi egy", "", "már kitöltött", "", "", "", "", "", ""
    ]

    _click_autofill(window, qt_app)

    assert [field.property("text") for field in mezok] == [
        "kézi nulla",
        "kézi egy",
        "Nap",
        "már kitöltött",
        "nap",
        "alpha",
        "beta",
        "",
        "",
        "",
    ]
    assert controller.quickTagConfigLabels[2:7] == [
        "Nap", "már kitöltött", "nap", "alpha", "beta"
    ]


def test_unreserved_click_uses_next_candidate_after_clear_and_then_exhausts(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    candidates = [f"cimke-{i}" for i in range(10)]
    _seed_keywords(
        controller,
        {
            "a.jpg": ", ".join(candidates[:4]),
            "b.jpg": ", ".join(candidates[4:]),
        },
    )
    settings = controller._get_settings()
    settings.setValue("quickTags/recentKeywords", ["recent-egy", "recent-ketto"])
    controller.setQuickTagsReserveRecent(False)

    _open_dialog(window, qt_app)
    mezok = _fields(window)
    mezok[0].setProperty("text", "   ")
    controller.setQuickTagLabel(1, "kézi")
    mezok[1].setProperty("text", "kézi")

    _click_autofill(window, qt_app)

    assert [field.property("text") for field in mezok] == [
        *candidates[:1], "kézi", *candidates[1:9]
    ]
    mezok[0].setProperty("text", "")
    _click_autofill(window, qt_app)
    assert mezok[0].property("text") == candidates[9]

    mezok[2].setProperty("text", "")
    _click_autofill(window, qt_app)
    assert mezok[2].property("text") == ""
    assert controller.quickTagConfigLabels[0] == candidates[9]


def test_autofill_button_is_disabled_without_candidates(qml_app, qt_app):
    window, controller, _engine = qml_app
    _open_dialog(window, qt_app)
    assert len(_fields(window)) == 10
    button = _autofill_button(window, qt_app)
    assert button.property("enabled") is False


def test_cancel_restores_and_ok_keeps_autofilled_values(qml_app, qt_app):
    window, controller, _engine = qml_app
    _seed_keywords(controller, {"a.jpg": "Nap"})
    controller.setQuickTagsReserveRecent(False)
    controller.setQuickTagLabel(3, "eredeti")

    dialog = _open_dialog(window, qt_app)
    _click_autofill(window, qt_app)
    assert controller.quickTagConfigLabels[0] == "Nap"
    cancel = next(
        item
        for item in dialog.findChildren(QQuickItem)
        if item.property("text") in {"Cancel", "Mégse"}
    )
    _click_item(window, qt_app, cancel)
    assert var_feltetelre(
        qt_app, lambda: not dialog.property("visible"), 3.0
    ), "a Mégse nem zárta be a konfigurációt"
    assert controller.quickTagConfigLabels == ["", "", "", "eredeti", *([""] * 6)]

    dialog = _open_dialog(window, qt_app)
    _click_autofill(window, qt_app)
    ok = next(
        item
        for item in dialog.findChildren(QQuickItem)
        if item.property("text") in {"OK", "Ok"}
    )
    _click_item(window, qt_app, ok)
    assert var_feltetelre(
        qt_app, lambda: not dialog.property("visible"), 3.0
    ), "az OK nem zárta be a konfigurációt"
    assert controller.quickTagConfigLabels[0] == "Nap"
