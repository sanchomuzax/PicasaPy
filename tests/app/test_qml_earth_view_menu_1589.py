"""#1589: a „Megtekintés a Google Earth programban…" menüpont (Eszközök ▸
Geocímke).

A `PicasaMenuBar.qml` ÖNÁLLÓAN betöltve (a `test_qml_earth_menu_530.py`
mintája). A felirat a hivatalos honosításból:
`eMenuTools::ID_VIEW_EARTH` = „View in Google Earth..." /
„Megtekintés a Google Earth programban...".

⚠️ A várt feliratot KIÍRT LITERÁL adja meg, nem a termék konstansa — a
#1576-nál épp az nyelte el a hibát, hogy a teszt ugyanabból a forrásból
olvasott, amit mérni akart.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt


@pytest.fixture
def menubar(qt_app):
    import picasapy.app.application as app_module
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", None)
    factory = QQmlComponent(
        engine, str(app_module._APP_DIR / "qml" / "PicasaPy" / "PicasaMenuBar.qml")
    )
    item = factory.create()
    assert item is not None, factory.errorString()
    yield item
    item.deleteLater()
    qt_app.processEvents()


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestMegtekintesMenupont:
    def test_a_menupont_letezik_es_KATTINTHATO(self, menubar) -> None:
        """Nem helyfoglaló: a #1475/#1052/#1526 hibaosztálya pontosan az,
        amikor a tétel LÁTSZIK, de nem lehet rákattintani."""
        item = _child(menubar, "menuToolsViewEarth")

        assert item.property("enabled") is True
        assert not item.property("placeholder"), (
            "a Megtekintés… tétel helyfoglaló maradt, tehát halott"
        )

    def test_a_felirat_a_hivatalos_honositasbol_valo(self, menubar) -> None:
        item = _child(menubar, "menuToolsViewEarth")

        assert item.property("text") == "View in Google Earth..."

    def test_az_export_tetel_MELLETT_all_kulon_tetelkent(self, menubar) -> None:
        """Az eredetiben KÉT tétel van: az `ID_EXPORT_EARTH` csak kiírja a
        fájlt, az `ID_VIEW_EARTH` kiírja és megnyitja. Egyik sem váltja ki
        a másikat."""
        assert _child(menubar, "menuToolsExportEarth").property("text") == (
            "Export to Google Earth File"
        )
        assert _child(menubar, "menuToolsViewEarth").property("text") == (
            "View in Google Earth..."
        )

    def test_a_kivaltas_sajat_jelet_kuld(self, menubar, qt_app) -> None:
        """A menüsáv csak JELET küld; a párbeszédet a Main.qml nyitja."""
        megtekintes: list[bool] = []
        export: list[bool] = []
        menubar.earthViewRequested.connect(lambda: megtekintes.append(True))
        menubar.earthExportRequested.connect(lambda: export.append(True))

        item = _child(menubar, "menuToolsViewEarth")
        QMetaObject.invokeMethod(
            item, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert megtekintes == [True]
        assert export == [], "a Megtekintés… az EXPORT jelzését sütötte el"
