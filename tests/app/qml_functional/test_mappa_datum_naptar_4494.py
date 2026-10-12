"""#4494: a Mappa tulajdonságai Dátum mezője naptár-gombbal, három magasságon.

Valódi egérkattintás és billentyűzet: a naptár-gomb nyit lenyíló naptárat, a
kiválasztott nap a mezőbe kerül (a nyelvi beállítás szerinti alakban), az OK
pedig ugyanúgy menti ISO-alakban, mint a kézi beírás.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QLocale, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


@pytest.fixture
def hu_locale():
    """A magyar nyelvi beállítás a teszt idejére; a dátumalak ettől függ."""
    eredeti = QLocale()
    QLocale.setDefault(QLocale(QLocale.Language.Hungarian, QLocale.Country.Hungary))
    yield
    QLocale.setDefault(eredeti)


def _wait(qt_app, condition, seconds=5.0):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qt_app.processEvents()
        try:
            if condition():
                return True
        except (AttributeError, RuntimeError):
            pass
        time.sleep(0.01)
    return bool(condition())


def _click(window, item):
    assert item is not None and item.property("enabled") is True
    center = item.mapToScene(
        QPointF(float(item.property("width")) / 2,
                float(item.property("height")) / 2)
    )
    assert 0 <= center.x() < window.width()
    assert 0 <= center.y() < window.height()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def _type_text(window, item, value):
    _click(window, item)
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert value.isascii()
    for char in value:
        QTest.keyEvent(QTest.KeyAction.Click, window, ord(char))


def _open_properties(window, controller, folder, qt_app, aktualis_datum):
    dialog = window.findChild(QObject, "folderPropertiesDialog")
    assert dialog is not None
    dialog.setProperty("mode", "folder")
    dialog.setProperty("folderPath", str(folder))
    dialog.setProperty("folderName", folder.name)
    dialog.setProperty("currentDate", aktualis_datum)
    dialog.setProperty(
        "currentDescription", controller.folderDescriptionOf(str(folder))
    )
    dialog.setProperty(
        "currentMusicEnabled", controller.folderMusicEnabled(str(folder))
    )
    dialog.setProperty(
        "currentMusicFile", controller.folderMusicFile(str(folder))
    )
    dialog.open()
    assert _wait(qt_app, lambda: dialog.property("opened") is True), (
        "a Mappa tulajdonságai nem nyílt meg"
    )
    return dialog


def _objektum(window, nev):
    objektum = window.findChild(QObject, nev)
    assert objektum is not None, f"hiányzik a(z) {nev} elem"
    return objektum


def _naptar_nap(calendar, nev):
    """A naptár napcellája: a lenyíló elem tartalmát a látvány-fán keressük.

    A Popup tartalma nem a főablak QObject-fájában ül, ezért a látvány-fát
    járjuk be a contentItem-től.
    """
    gyokerek = [calendar.property("contentItem")]
    while gyokerek:
        elem = gyokerek.pop()
        if elem is None:
            continue
        if elem.objectName() == nev:
            return elem
        gyokerek.extend(elem.childItems())
    raise AssertionError(f"hiányzik a(z) {nev} napcella a naptárban")


def _mappa_datum_mentes_es_naptar(window, controller, folder, qt_app):
    """Egy kör: naptár-gomb → nap → OK; visszaadja a mentett dátumot."""
    _open_properties(window, controller, folder, qt_app, "2026-01-01")
    date_field = _objektum(window, "folderPropertiesDateField")
    assert date_field.property("text") == "2026. 01. 01."

    calendar = _objektum(window, "folderPropertiesCalendar")
    _click(window, _objektum(window, "folderPropertiesDateCalendarButton"))
    assert _wait(qt_app, lambda: calendar.property("opened") is True), (
        "a naptár-gomb nem nyitotta meg a naptárat"
    )
    _click(window, _naptar_nap(calendar, "calendarDay_2026-01-15"))
    assert _wait(qt_app, lambda: calendar.property("opened") is False)
    assert _wait(
        qt_app,
        lambda: date_field.property("text") == "2026. 01. 15.",
    ), "a kiválasztott nap nem került a dátummezőbe"

    _click(window, _objektum(window, "folderPropertiesOkButton"))
    assert _wait(
        qt_app,
        lambda: not window.findChild(QObject, "folderPropertiesDialog")
        .property("opened"),
    )
    return controller.folderDateOverride(str(folder))


@pytest.mark.parametrize("delta", [-5, 0, 5])
def test_naptar_nap_valasztas_ok_mentes_harom_magassagon(
    hu_locale, qml_app, qt_app, tmp_path, delta
):
    window, controller, _engine = qml_app
    library = tmp_path / "kepek"
    folder = library / "datum-mappa"
    folder.mkdir(parents=True)
    make_jpeg(folder / "photo.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller._reload(preserve_scroll=True)
    controller.selectFolder(str(folder))

    original_height = window.height()
    try:
        window.resize(window.width(), original_height + delta)
        assert _wait(qt_app, lambda: window.height() == original_height + delta)
        assert _mappa_datum_mentes_es_naptar(
            window, controller, folder, qt_app
        ) == "2026-01-15"
    finally:
        window.resize(window.width(), original_height)


@pytest.mark.parametrize("delta", [-5, 0, 5])
def test_kezi_beiras_hu_alakban_es_hibas_datum_tiltja_az_ok_gombot(
    hu_locale, qml_app, qt_app, tmp_path, delta
):
    window, controller, _engine = qml_app
    library = tmp_path / "kepek"
    folder = library / "kezi-datum"
    folder.mkdir(parents=True)
    make_jpeg(folder / "photo.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller._reload(preserve_scroll=True)
    controller.selectFolder(str(folder))

    original_height = window.height()
    try:
        window.resize(window.width(), original_height + delta)
        assert _wait(qt_app, lambda: window.height() == original_height + delta)
        _open_properties(window, controller, folder, qt_app, "")
        date_field = _objektum(window, "folderPropertiesDateField")
        ok = _objektum(window, "folderPropertiesOkButton")

        _type_text(window, date_field, "2026. 02. 30.")
        assert _wait(qt_app, lambda: ok.property("enabled") is False), (
            "nem létező nap (február 30.) mellett az OK aktív maradt"
        )
        hint = _objektum(window, "folderPropertiesDateHint")
        assert _wait(qt_app, lambda: hint.property("visible") is True)

        _type_text(window, date_field, "2026. 02. 20.")
        assert _wait(qt_app, lambda: ok.property("enabled") is True)
        _click(window, ok)
        assert _wait(
            qt_app,
            lambda: not window.findChild(QObject, "folderPropertiesDialog")
            .property("opened"),
        )
        assert controller.folderDateOverride(str(folder)) == "2026-02-20"
    finally:
        window.resize(window.width(), original_height)
