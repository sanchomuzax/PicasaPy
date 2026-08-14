"""#530: a Google Earth-export menüpontja (Eszközök → Geocímke).

A `PicasaMenuBar.qml` ÖNÁLLÓAN betöltve (a `test_qml_webexport_menu.py`
mintája). A felirat a bináris index szerinti:
`eMenuTools::ID_EXPORT_EARTH` = „Export to Google Earth File" /
„Exportálás Google Earth-fájlba".
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


class TestEarthExportMenuItem:
    def test_a_menupont_letezik_es_aktiv(self, menubar) -> None:
        """A Geocímke almenü eddig `enabled: false` volt — az export motorja
        (#530) elkészült, tehát a menüpontnak élnie kell."""
        item = _child(menubar, "menuToolsExportEarth")

        assert item.property("enabled") is True

    def test_a_felirat_az_eredetibol_valo(self, menubar) -> None:
        item = _child(menubar, "menuToolsExportEarth")

        assert item.property("text") == "Export to Google Earth File"

    def test_a_kivaltas_jelet_kuld(self, menubar, qt_app) -> None:
        """A menüsáv csak JELET küld — a párbeszédet a hívó nyitja
        (ExportDialogs.openGoogleEarth), a menüsáv nem ismeri a kijelölést."""
        kapott = []
        menubar.earthExportRequested.connect(lambda: kapott.append(True))

        item = _child(menubar, "menuToolsExportEarth")
        QMetaObject.invokeMethod(
            item, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert kapott == [True]
