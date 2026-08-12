"""QML-funkcionális teszt: az adatbázis-tömörítés ablaka — #449.

Az eredeti `compacting.fen` három dolgot ígért: megmondja, MIÉRT vár a
felhasználó, kiírja, hogy percekig tarthat, és ad egy **Mégse** gombot.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


def _trigger(window, qt_app):
    """A MenuItem-nek nincs hívható `trigger()`-e — a `triggered` SIGNAL
    kiváltása futtatja az `onTriggered` kezelőt (ld. test_qml_dedup.py)."""
    QMetaObject.invokeMethod(
        _child(window, "menuToolsCompactDatabase"),
        "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestCompactDialog:
    def test_the_menu_opens_it(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        _trigger(window, qt_app)

        assert _child(window, "compactDatabaseDialog").property("visible") is True

    def test_it_has_a_status_line_and_a_cancel_button(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        _trigger(window, qt_app)

        assert _child(window, "compactStatusText").property("text")
        # futás közben Mégse, utána Bezárás — egyetlen gomb, ahogy az
        # eredetin
        assert _child(window, "compactCancelButton").property("text") in (
            "Cancel",
            "Close",
        )

    def test_the_progress_bar_is_indeterminate(self, qml_app, qt_app):
        """A `VACUUM` nem mond százalékot — kitalálni hazugság lenne."""
        window, _controller, _engine = qml_app

        _trigger(window, qt_app)

        assert _child(window, "compactProgressBar").property("indeterminate") is True

    def test_a_compact_database_is_not_vacuumed_for_nothing(self, qml_app, qt_app):
        """Az eredeti `compactpercentage` küszöbe: egy amúgy is tömör
        adatbázison meg sem indul a percekig tartó munka."""
        window, _controller, _engine = qml_app

        _trigger(window, qt_app)

        dialog = _child(window, "compactDatabaseDialog")
        assert dialog.property("nothingToDo") is True
        assert _child(window, "compactProgressBar").property("visible") is False
