"""#4202 — a keresősáv és az eredményfejléc meglévő elemeinek párosítása.

A próba a lefedettségi táblát is őrzi, majd a valódi főablakon kattintással
ellenőrzi a keresést, a javaslatot, az arcsszűrőt és a másodpéldány-módot.
Az ablak magassága ±5 képponttal változik; minden kattintás a vezérlő
pillanatnyi QML-geometriájából számolódik.
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest

_ROOT = Path(__file__).resolve().parents[3]
_ELEMENTS = _ROOT / "docs/specs/ui-lefedettseg-elemek.csv"
_THIS_TEST = "tests/app/qml_functional/test_search_lefedettseg_4202.py"

_EXPECTED = {
    "searchcontainer/search": "megvan",
    "searchcontainer/searchautocomplete": "megvan",
    "searchcontainer/searchbutton": "megvan",
    "searchcontainer/webview": "nem-cel",
    "searchoptions/dupesearch": "megvan",
    "searchoptions/facesearch": "megvan",
    "searchoptions/searchcenter": "megvan",
    "searchoptions/searchresult": "megvan",
}


def _wait_until(qt_app, predicate, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(predicate())


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _click_item(window, item, qt_app) -> None:
    assert item is not None and item.isVisible(), "a kattintandó elem nem látható"
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _send_text(field, text: str, qt_app) -> None:
    for character in text:
        key = Qt.Key(ord(character.upper()))
        QCoreApplication.sendEvent(
            field,
            QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, character),
        )
        QCoreApplication.sendEvent(
            field,
            QKeyEvent(QEvent.Type.KeyRelease, key, Qt.KeyboardModifier.NoModifier, character),
        )
    qt_app.processEvents()


def _send_shortcut(window, key, modifiers, qt_app) -> None:
    QCoreApplication.sendEvent(
        window, QKeyEvent(QEvent.Type.KeyPress, key, modifiers)
    )
    QCoreApplication.sendEvent(
        window, QKeyEvent(QEvent.Type.KeyRelease, key, modifiers)
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_keresesi_elemlista_es_valodi_felhasznaloi_ut(
    qml_app, qt_app, height_delta
):
    # A lefedettségi párosítások és teszthivatkozások részei a kimeneti szerződésnek.
    with _ELEMENTS.open(encoding="utf-8", newline="") as source:
        rows = {row["elem"]: row for row in csv.DictReader(source)}
    missing = sorted(set(_EXPECTED) - set(rows))
    assert not missing, f"hiányzó lefedettségi párosítások: {missing}"
    wrong_states = {
        name: rows[name]["allapot"]
        for name, expected in _EXPECTED.items()
        if rows[name]["allapot"] != expected
    }
    assert not wrong_states, f"hibás lefedettségi állapotok: {wrong_states}"
    for name, state in _EXPECTED.items():
        evidence = rows[name]["bizonyitek"]
        if state == "megvan":
            assert _THIS_TEST in evidence, f"{name}: hiányzik a kimeneti teszt"
    assert "docs/decisions/keresosav-webview-szuro-kimarad.md" in rows[
        "searchcontainer/webview"
    ]["bizonyitek"]

    window, controller, _engine = qml_app
    original_height = window.height()
    window.setHeight(original_height + height_delta)
    window.show()
    window.requestActivate()
    qt_app.processEvents()

    field = window.findChild(QObject, "searchField")
    assert field is not None and field.width() > 0 and field.height() > 0

    # search: valódi kattintás a mezőbe, majd gépelés és megjelenő
    # találati állapot a főablakban.
    _click_item(window, field, qt_app)
    assert _wait_until(qt_app, lambda: field.property("activeFocus") is True)
    _send_text(field, "kep", qt_app)
    suggestions = window.findChild(QObject, "searchSuggestions")
    assert _wait_until(qt_app, lambda: suggestions.property("visible") is True)
    rows_in_popup = [
        item for item in _walk(suggestions) if item.objectName() == "suggestionRow"
    ]
    assert rows_in_popup, "a kereső-javaslat nem jelent meg"
    target_folder = controller.currentFolder
    _click_item(window, rows_in_popup[0], qt_app)
    assert _wait_until(qt_app, lambda: field.property("text") == "")
    assert _wait_until(qt_app, lambda: suggestions.property("visible") is False)
    assert controller.currentFolder == target_folder

    _click_item(window, field, qt_app)
    _send_text(field, "a", qt_app)
    assert _wait_until(
        qt_app,
        lambda: controller.searchActive and controller.searchResultCount == 1,
    ), "a keresés nem szűrte egy találatra a főablakot"
    status = window.findChild(QObject, "folderPaneHeader")
    assert status is not None and status.isVisible()
    assert status.property("text") == 'Search results for "a" (1)'
    grouped_results = window.findChild(QObject, "groupedSearchResults")
    assert grouped_results is not None and grouped_results.isVisible(), (
        "a főablak központi keresési találatrácsa nem jelent meg"
    )

    # Visszaállítási kontroll: a keresés törlése visszahozza mindkét képet.
    clear = window.findChild(QObject, "searchClear")
    _click_item(window, clear, qt_app)
    assert _wait_until(
        qt_app,
        lambda: not controller.searchActive and controller.photos.rowCount() == 2,
    ), "a keresés törlése nem állította vissza a teljes nézetet"

    # facesearch: ugyanazon valódi szűrőgomb ki- és bekapcsolása mérhetően
    # leszűkíti, majd visszaállítja a főablak fotólistáját.
    face_filter = window.findChild(QObject, "faceFilter")
    _click_item(window, face_filter, qt_app)
    assert _wait_until(
        qt_app,
        lambda: controller.viewModeName == "faces"
        and controller.photos.rowCount() == 0,
    ), "az arc-szűrő nem adott üres eredményt a két arc nélküli mintaképre"
    _click_item(window, face_filter, qt_app)
    assert _wait_until(
        qt_app,
        lambda: controller.viewModeName == "folder"
        and controller.photos.rowCount() == 2,
    ), "az arc-szűrő kikapcsolása nem állította vissza a fotókat"

    # A könyvtári gyorsbillentyű nem aktív, amíg a keresőmezőé a fókusz.
    face_filter.forceActiveFocus()
    qt_app.processEvents()
    assert field.property("activeFocus") is False
    assert window.property("_szovegmezoneVanFokusz") is False

    # dupesearch: a valódi Ctrl+F6 út megjeleníti a kapcsolót, annak valódi
    # kattintása pedig visszavisz az összes képhez.
    _send_shortcut(
        window, Qt.Key.Key_F6, Qt.KeyboardModifier.ControlModifier, qt_app
    )
    assert _wait_until(
        qt_app,
        lambda: controller.viewModeName == "dupes"
        and window.findChild(QObject, "dupeFilter").isVisible(),
    ), "a másodpéldány-mód nem jelent meg"
    dupe_filter = window.findChild(QObject, "dupeFilter")
    _click_item(window, dupe_filter, qt_app)
    assert _wait_until(
        qt_app,
        lambda: controller.viewModeName == "folder"
        and controller.photos.rowCount() == 2,
    ), "a másodpéldány-kapcsoló nem állította vissza a teljes nézetet"


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_searchbutton_valodi_kattintassal_megnyitja_a_keresesi_beallitasokat(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    window.setHeight(window.height() + height_delta)
    window.show()
    window.requestActivate()
    qt_app.processEvents()

    field = window.findChild(QObject, "searchField")
    assert field is not None
    _click_item(window, field, qt_app)
    _send_text(field, "a", qt_app)
    assert _wait_until(qt_app, lambda: controller.searchActive)

    button = window.findChild(QObject, "searchbutton")
    assert button is not None and button.isVisible(), (
        "a keresési beállítások gombja hiányzik vagy nem látható"
    )
    _click_item(window, button, qt_app)

    popup = window.findChild(QObject, "searchOptionsPopup")
    assert _wait_until(
        qt_app, lambda: popup is not None and popup.property("visible") is True
    ), "a keresési beállítások nem nyíltak meg a valódi gombkattintásra"
    for element in ("searchcenter", "facesearch", "dupesearch", "searchresult"):
        option = window.findChild(QObject, element)
        assert option is not None and option.isVisible(), (
            f"a megnyitott keresési beállításból hiányzik: {element}"
        )

    face_option = window.findChild(QObject, "facesearch")
    _click_item(window, face_option, qt_app)
    assert _wait_until(
        qt_app,
        lambda: controller.viewModeName == "faces"
        and controller.photos.rowCount() == 0,
    ), "az arcos képek beállítása nem szűrte a főablakot"
    _click_item(window, face_option, qt_app)
    assert _wait_until(
        qt_app,
        lambda: controller.viewModeName == "folder"
        and controller.photos.rowCount() == 2,
    ), "az arcos képek beállításának kikapcsolása nem állította vissza a nézetet"

    dupe_option = window.findChild(QObject, "dupesearch")
    _click_item(window, dupe_option, qt_app)
    assert _wait_until(
        qt_app,
        lambda: controller.viewModeName == "dupes"
        and not controller.dupeSearchScanning,
    ), "a másodpéldány-beállítás nem futott le a főablakban"
    _click_item(window, dupe_option, qt_app)
    assert _wait_until(
        qt_app,
        lambda: controller.viewModeName == "folder"
        and controller.photos.rowCount() == 2,
    ), "a másodpéldány-beállítás kikapcsolása nem állította vissza a nézetet"

    _click_item(window, button, qt_app)
    assert _wait_until(qt_app, lambda: popup.property("visible") is False)
    _send_shortcut(
        window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier, qt_app
    )
    assert _wait_until(qt_app, lambda: field.property("activeFocus") is True)
    assert _wait_until(qt_app, lambda: popup.property("visible") is True), (
        "a Ctrl+F nem nyitotta meg a keresési beállításokat"
    )
