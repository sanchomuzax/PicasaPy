"""#936 — a menüpontról indítva NYÍLJON meg a kollázs-párbeszéd.

## Miért nem fogta meg ezt a #922 hat tesztje

Azok a párbeszéd `openForSelection()` függvényét **közvetlenül hívták**:

    dialog.metaObject().invokeMethod(dialog, "openForSelection")

Ezzel átugrották a teljes valódi utat — menüpont → `collageRequested`
jelzés → kezelő → párbeszéd —, és pont az a láncszem hiányzott, amit így
sosem érintettek: a `Main.qml` menüsor-blokkjában **nem volt**
`onCollageRequested` kezelő. A menüpont elsütötte a jelzést, és az a
semmibe ment.

A PROTOKOLL erre való szabálya: **a KIMENETET ellenőrizd, ne a szándékot.**
Az izoláltan hívott komponens működhet úgy is, hogy a felhasználó útja
törött.

Ezek az őrök ezért a JELZÉSTŐL indulnak, nem a párbeszédtől.
"""

from __future__ import annotations

from PySide6.QtCore import QEventLoop, QObject, QTimer


def _settle(qt_app, rounds=4):
    for _ in range(rounds):
        qt_app.processEvents()
        pause = QEventLoop()
        QTimer.singleShot(10, pause.quit)
        pause.exec()


def _menusor(window):
    bar = window.property("menuBar")
    assert bar is not None, "nincs menüsor"
    return bar


class TestMenuJelzesVegigmegy:
    def test_a_menusor_jelzese_MEGNYITJA_a_kollazs_parbeszedet(self, qml_app, qt_app):
        """A valódi út: a menüsor jelzését sütjük el, nem a párbeszédet hívjuk."""
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        dialog = window.findChild(QObject, "collageDialog")
        assert dialog.property("visible") is False

        _menusor(window).metaObject().invokeMethod(_menusor(window), "collageRequested")
        _settle(qt_app, 3)

        assert dialog.property("visible") is True, (
            "a menüsor jelzésének nincs kezelője — a kattintás a semmibe megy"
        )

    def test_a_menusor_jelzese_MEGNYITJA_a_film_parbeszedet(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0])
        dialog = window.findChild(QObject, "movieDialog")
        _menusor(window).metaObject().invokeMethod(_menusor(window), "movieRequested")
        _settle(qt_app, 3)
        assert dialog.property("visible") is True

    def test_kijeloles_NELKUL_is_megnyilik_es_megmondja(self, qml_app, qt_app):
        """#922 + #936 együtt: a menüből, forrás nélkül is történik valami."""
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [])
        dialog = window.findChild(QObject, "collageDialog")
        _menusor(window).metaObject().invokeMethod(_menusor(window), "collageRequested")
        _settle(qt_app, 3)
        assert dialog.property("visible") is True
        assert window.findChild(QObject, "collageNoSourceHint").property("visible") is True
