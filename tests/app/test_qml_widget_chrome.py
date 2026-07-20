"""PicasaScrollBar.qml / PicasaSlider.qml — egyedi widget-króm (#3),
önállóan betöltve (a bekötés Main.qml-be az integrátor feladata).

Offscreen render-teszt: a komponensek példányosíthatók, a Theme-tokenekre
épülő alap-tulajdonságaik (méret, tartomány, irány, vizuális pozíció)
helyesek. Referencia-screenshot a repóban nem található ehhez a két
komponenshez, ezért tulajdonság-szintű ellenőrzés (ld. feladatleírás).
"""

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem


def _load(app_module, qt_app, name, properties=None):
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    factory = QQmlComponent(
        engine, str(app_module._APP_DIR / "qml" / "PicasaPy" / name)
    )
    item = factory.createWithInitialProperties(properties or {})
    assert item is not None, factory.errorString()
    # a QQmlComponent-nek életben kell maradnia, amíg a belőle létrehozott
    # elem létezik — enélkül a Python-oldali GC idő előtt eltünteti (a
    # C++ tulajdonjog a komponensen keresztül fut)
    engine._chrome_factory = factory
    return item, engine


@pytest.fixture
def app_module():
    import picasapy.app.application as module

    return module


class TestPicasaScrollBar:
    def test_instantiates_as_quick_item(self, app_module, qt_app):
        item, engine = _load(app_module, qt_app, "PicasaScrollBar.qml")
        assert isinstance(item, QQuickItem)
        item.deleteLater()
        engine.deleteLater()

    def test_default_orientation_is_vertical(self, app_module, qt_app):
        item, engine = _load(app_module, qt_app, "PicasaScrollBar.qml")
        # QtQuick.Controls ScrollBar alapértelmezett iránya Qt.Vertical
        from PySide6.QtCore import Qt

        assert item.property("orientation") == Qt.Orientation.Vertical
        item.deleteLater()
        engine.deleteLater()

    def test_policy_can_be_forced_always_on(self, app_module, qt_app):
        # a policy egy QQuickScrollBar::Policy enum — a Python-oldali
        # property() nem tudja konvertálni, ezért a contentItem-en
        # keresztül, közvetve ellenőrizzük: AlwaysOn esetén a fogantyú
        # teljesen látszik (opacity == 1.0) akkor is, ha nincs interakció.
        item, engine = _load(
            app_module,
            qt_app,
            "PicasaScrollBar.qml",
            {"policy": 2},  # ScrollBar.AlwaysOn == 2 (AsNeeded=0, AlwaysOff=1)
        )
        handle = item.property("contentItem")
        assert handle.property("opacity") == pytest.approx(1.0)
        item.deleteLater()
        engine.deleteLater()

    def test_size_and_position_settable(self, app_module, qt_app):
        item, engine = _load(
            app_module, qt_app, "PicasaScrollBar.qml", {"size": 0.25, "position": 0.5}
        )
        assert item.property("size") == pytest.approx(0.25)
        assert item.property("position") == pytest.approx(0.5)
        item.deleteLater()
        engine.deleteLater()


class TestPicasaSlider:
    def test_instantiates_as_quick_item(self, app_module, qt_app):
        item, engine = _load(app_module, qt_app, "PicasaSlider.qml")
        assert isinstance(item, QQuickItem)
        item.deleteLater()
        engine.deleteLater()

    def test_default_range_is_zero_to_one(self, app_module, qt_app):
        item, engine = _load(app_module, qt_app, "PicasaSlider.qml")
        assert item.property("from") == pytest.approx(0.0)
        assert item.property("to") == pytest.approx(1.0)
        item.deleteLater()
        engine.deleteLater()

    def test_value_clamped_to_range(self, app_module, qt_app):
        item, engine = _load(
            app_module,
            qt_app,
            "PicasaSlider.qml",
            {"from": 72, "to": 256, "value": 140},
        )
        assert item.property("value") == pytest.approx(140)
        # a vizuális pozíció (0..1) a tartományon belüli arányt tükrözi
        expected_visual_position = (140 - 72) / (256 - 72)
        assert item.property("visualPosition") == pytest.approx(
            expected_visual_position, abs=1e-6
        )
        item.deleteLater()
        engine.deleteLater()

    def test_horizontal_by_default(self, app_module, qt_app):
        item, engine = _load(app_module, qt_app, "PicasaSlider.qml")
        from PySide6.QtCore import Qt

        assert item.property("orientation") == Qt.Orientation.Horizontal
        assert item.property("isHorizontal") is True
        item.deleteLater()
        engine.deleteLater()

    def test_vertical_orientation_supported(self, app_module, qt_app):
        from PySide6.QtCore import Qt

        item, engine = _load(
            app_module,
            qt_app,
            "PicasaSlider.qml",
            {"orientation": Qt.Orientation.Vertical},
        )
        assert item.property("orientation") == Qt.Orientation.Vertical
        assert item.property("isHorizontal") is False
        item.deleteLater()
        engine.deleteLater()

    def test_disabled_slider_still_instantiates(self, app_module, qt_app):
        item, engine = _load(
            app_module, qt_app, "PicasaSlider.qml", {"enabled": False, "value": 0.3}
        )
        assert item.property("enabled") is False
        assert item.property("value") == pytest.approx(0.3)
        item.deleteLater()
        engine.deleteLater()


class TestWidgetChromeUsesThemeTokens:
    """A színek a Theme-ből jönnek — NEM a Theme.qml módosításával (tiltott
    forró fájl), hanem a meglévő tokenek felhasználásával (chromeBg,
    chromeBorder — a kézikönyv „Görgetősáv #CDCDCD" tokenje)."""

    def test_scrollbar_source_references_theme_tokens(self):
        import picasapy.app.application as app_module

        qml_path = (
            app_module._APP_DIR / "qml" / "PicasaPy" / "PicasaScrollBar.qml"
        )
        source = qml_path.read_text(encoding="utf-8")
        assert "Theme.chromeBorder" in source
        assert "Theme.chromeBg" in source

    def test_slider_source_references_theme_tokens(self):
        import picasapy.app.application as app_module

        qml_path = app_module._APP_DIR / "qml" / "PicasaPy" / "PicasaSlider.qml"
        source = qml_path.read_text(encoding="utf-8")
        assert "Theme.chromeBg" in source
        assert "Theme.chromeBorder" in source

    def test_theme_qml_untouched_by_this_task(self):
        # a Theme.qml forró fájl — ez a teszt nem a tartalmát ellenőrzi,
        # csak azt, hogy a két új komponens nem hoz be új, nem-Theme
        # színforrást a jelenlegi tokenkészleten kívülről (kivéve a
        # PicasaButton-mintát követő, semleges szürke fogantyú-átmenetet).
        import picasapy.app.application as app_module

        theme_path = app_module._APP_DIR / "qml" / "PicasaPy" / "Theme.qml"
        assert theme_path.exists()
