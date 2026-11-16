"""Valódi, gyors keresőmező-gépelés a #7081 szerint.

Az eredeti (`0x0097fb90`, `0x005e4e0d`) nem vár időt: a mező `EN_CHANGE`
értesítése azonnal keres, és csak a billentyűsorban váró további leütésnél
hagyja ki. A Qt-megfelelő a nulla késleltetésű összevonás (`Qt.callLater`):
az egy eseményhurok-körön belül érkező leütések EGY keresést adnak.
"""

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


def _kiurul_a_varakozo_kereses(qt_app, toolbar) -> bool:
    """Igaz, ha a függő (összevont) keresés már lefutott."""
    return varj_feltetelre(
        qt_app, lambda: toolbar.property("searchPending") is False
    )


def test_gyors_gepeles_egy_esemenyhurok_koron_belul_egy_kereses(
    qml_app, qt_app, monkeypatch
):
    from picasapy.app import search_controller as search_module

    window, controller, _engine = qml_app
    field = window.findChild(QObject, "searchField")
    toolbar = window.findChild(QObject, "mainToolbar")
    assert field is not None
    assert toolbar is not None
    _fokuszba_kattint(window, field, qt_app)

    original_search = search_module.search_photos
    queries = []

    def count_searches(conn, query, **kwargs):
        queries.append(query)
        return original_search(conn, query, **kwargs)

    monkeypatch.setattr(search_module, "search_photos", count_searches)

    text = "Quick"
    _gyors_gepeles(window, text)
    # Az eseményhurok még nem fordult: a leütések nem kerestek külön-külön.
    assert queries == []
    assert toolbar.property("searchPending") is True

    assert varj_feltetelre(
        qt_app, lambda: controller.searchQuery == text
    ), "a keresés nem jutott el a teljesen begépelt szövegig"
    assert len(queries) < len(text), (
        f"{len(queries)} keresés futott {len(text)} billentyűre: {queries!r}"
    )
    assert queries == [text]
    # A felületen a BEÍRT szöveg marad, nem a kisbetűs, szavakra bontott alak.
    assert field.property("text") == text
    assert controller.searchQuery == text


def test_szunet_utan_azonnal_keres_es_azonos_szoveget_atugorja(
    qml_app, qt_app, monkeypatch
):
    from picasapy.app import search_controller as search_module

    window, controller, _engine = qml_app
    field = window.findChild(QObject, "searchField")
    toolbar = window.findChild(QObject, "mainToolbar")
    assert field is not None
    assert toolbar is not None
    _fokuszba_kattint(window, field, qt_app)

    original_search = search_module.search_photos
    queries = []

    def count_searches(conn, query, **kwargs):
        queries.append(query)
        return original_search(conn, query, **kwargs)

    monkeypatch.setattr(search_module, "search_photos", count_searches)

    text = "quick"
    _gyors_gepeles(window, text)
    assert varj_feltetelre(qt_app, lambda: controller.searchQuery == text)
    assert queries == [text]

    # A gépelés szünetében a következő leütés külön, azonnali keresés.
    _gyors_gepeles(window, "s")
    assert _kiurul_a_varakozo_kereses(qt_app, toolbar)
    assert queries == [text, text + "s"]

    # Az egész mező kijelölése és ugyanannak a szövegnek az újragépelése:
    # azonos szövegre nem fut új keresés (`0x0065b906`-`0x0065b988`).
    _billentyu(
        window,
        Qt.Key.Key_A,
        Qt.KeyboardModifier.ControlModifier,
        "a",
    )
    _gyors_gepeles(window, text + "s")
    assert toolbar.property("searchPending") is True
    assert _kiurul_a_varakozo_kereses(qt_app, toolbar)
    assert field.property("text") == text + "s"
    assert controller.searchQuery == text + "s"
    assert queries == [text, text + "s"], (
        f"azonos szövegre új keresés futott: {queries!r}"
    )
