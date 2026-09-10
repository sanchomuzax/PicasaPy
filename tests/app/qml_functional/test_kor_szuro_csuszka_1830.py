"""Az idő-csúszka a FELÜLETEN is szűr (#1830).

A `test_kor_szuro_1830.py` a képletet és a lekérdezést méri; ez a fájl azt,
hogy a csúszka mozgatása tényleg eljut a vezérlőig, és a találati sáv
felirata megjelenik. A #1187 tanulsága szerint a VEZÉRLŐT nem hívjuk
közvetlenül: a csúszka `value`-ját állítjuk, és a `moved` jelzést váltjuk
ki — pontosan azt az utat, amit a felhasználó bejár.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


def _child(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


class TestACsuszkaEleroEsMukodik:
    def test_a_csuszka_ENGEDELYEZETT(self, qml_app, qt_app):
        """A #1830 előtt `enabled: false` volt — halott vezérlő a sávon."""
        window = qml_app[0]
        csuszka = _child(window, "dateRangeFilterSlider")

        assert csuszka.property("enabled") is True, (
            "a csúszka le van tiltva — a felhasználó nem tudja használni, "
            "és a mért kor-szűrő sehol nem érvényesül"
        )

    def test_a_mozgatas_a_vezerlonek_szol(self, qml_app, qt_app):
        window, controller = qml_app[0], qml_app[1]
        csuszka = _child(window, "dateRangeFilterSlider")

        csuszka.setProperty("value", 0.5)
        QMetaObject.invokeMethod(csuszka, "moved", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert controller.filterActive is True, (
            "a csúszka mozgatása után nincs szűrt nézet — a `moved` jelzés "
            "nem ér el a `setAgeFilter`-ig"
        )
        assert controller.ageFilterText != "", (
            "a találati sáv felirata üres — a felhasználó nem látja, MIRE "
            "szűrt (az eredeti a fejlécben kiírja)"
        )

    def test_a_nulla_kikapcsolja(self, qml_app, qt_app):
        """A csúszka bal széle „nincs szűrés" — nem „nagyon régi"."""
        window, controller = qml_app[0], qml_app[1]
        csuszka = _child(window, "dateRangeFilterSlider")

        csuszka.setProperty("value", 0.5)
        QMetaObject.invokeMethod(csuszka, "moved", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert controller.filterActive is True

        csuszka.setProperty("value", 0.0)
        QMetaObject.invokeMethod(csuszka, "moved", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert controller.filterActive is False, "a nullának ki kell kapcsolnia"
        assert controller.ageFilterText == "", (
            "a kor-felirat ottmaradt szűrés nélkül — a sáv hazudik"
        )
