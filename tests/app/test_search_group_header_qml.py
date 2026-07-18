"""SearchGroupHeader.qml — a kereső-rács mappánkénti szekció-fejléce (#7),
önállóan betöltve (a GridView.section.delegate-bekötés a Main.qml-ben)."""

import pytest
from PySide6.QtCore import QObject


@pytest.fixture
def component(qt_app):
    import picasapy.app.application as app_module
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    factory = QQmlComponent(
        engine,
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "SearchGroupHeader.qml"),
    )
    item = factory.createWithInitialProperties({"section": "/kepek/nyaralas"})
    assert item is not None, factory.errorString()
    yield item
    item.deleteLater()


class TestSearchGroupHeader:
    def test_shows_folder_name_not_full_path(self, component):
        label = component.findChild(QObject, "photoGridSectionLabel")
        assert label is not None, "photoGridSectionLabel nem található"
        assert label.property("text") == "nyaralas"

    def test_windows_path_separator_handled(self, qt_app):
        import picasapy.app.application as app_module
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        factory = QQmlComponent(
            engine,
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "SearchGroupHeader.qml"),
        )
        item = factory.createWithInitialProperties({"section": "C:\\Kepek\\Telek"})
        assert item is not None, factory.errorString()
        label = item.findChild(QObject, "photoGridSectionLabel")
        assert label.property("text") == "Telek"
        item.deleteLater()
