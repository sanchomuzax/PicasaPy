"""#351: a `PicasaMenuBar.qml` "Export as HTML Page..." menüpontja
(`Mappa` menü) — a `PicasaMenuBar.qml` ÖNÁLLÓAN betöltve (a
`test_qml_move_database.py` mintája), Main.qml-bekötés nélkül (az az
integrátoré, ld. `webexport_controller.py` docstringje)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt


@pytest.fixture
def menubar(qt_app):
    """A `PicasaMenuBar.qml` önállóan betöltve, `controller` nélkül (az
    érintett menüpont nem olvas `bar.ctl`-t) — a `test_qml_move_database.py`
    mintája."""
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


class TestWebExportMenuItem:
    def test_menu_item_exists_and_is_enabled(self, menubar):
        item = _child(menubar, "menuFolderWebExport")
        assert item.property("enabled") is True

    def test_triggering_emits_web_export_requested(self, menubar, qt_app):
        item = _child(menubar, "menuFolderWebExport")
        seen = []
        menubar.webExportRequested.connect(lambda: seen.append(True))
        QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert seen == [True]
