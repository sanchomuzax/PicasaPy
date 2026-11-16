"""Valódi, gyors keresőmező-gépelés a #7081 szerint."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QKeyEvent
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre


def _fokuszba_kattint(window, field, qt_app) -> None:
    point = field.mapToScene(QPointF(field.width() / 2, field.height() / 2)).toPoint()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point,
    )
    qt_app.processEvents()


def _billentyu(window, key, modifiers, text="") -> None:
    for event_type in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
        QGuiApplication.sendEvent(
            window, QKeyEvent(event_type, key, modifiers, text)
        )


def _gyors_gepeles(window, text: str) -> None:
    for character in text:
        _billentyu(
            window,
            Qt.Key(ord(character.upper())),
            Qt.KeyboardModifier.NoModifier,
            character,
        )


def test_gyors_gepeles_osszevonja_a_keresest_es_azonos_szoveget_atugorja(
    qml_app, qt_app, monkeypatch
):
    from picasapy.app import search_controller as search_module

    window, controller, _engine = qml_app
    field = window.findChild(QObject, "searchField")
    assert field is not None
    _fokuszba_kattint(window, field, qt_app)

    original_search = search_module.search_photos
    queries = []

    def count_searches(conn, query, **kwargs):
        queries.append(query)
        return original_search(conn, query, **kwargs)

    monkeypatch.setattr(search_module, "search_photos", count_searches)

    text = "quick"
    _gyors_gepeles(window, text)

    assert varj_feltetelre(
        qt_app, lambda: controller.searchQuery == text, 3.0
    ), "a keresés nem jutott el a teljesen begépelt szövegig"
    assert len(queries) < len(text), (
        f"{len(queries)} keresés futott {len(text)} billentyűre: {queries!r}"
    )
    assert queries == [text]

    timer = window.findChild(QObject, "searchDebounceTimer")
    assert timer is not None, "a keresési késleltető nem található"
    _billentyu(
        window,
        Qt.Key.Key_A,
        Qt.KeyboardModifier.ControlModifier,
        "a",
    )
    _gyors_gepeles(window, text)
    assert timer.property("running") is True
    assert varj_feltetelre(
        qt_app, lambda: timer.property("running") is False, 3.0
    ), "az azonos szöveg ellenőrzéséhez nem zárult le a késleltető"
    assert field.property("text") == text
    assert controller.searchQuery == text
    assert queries == [text], f"azonos szövegre új keresés futott: {queries!r}"
