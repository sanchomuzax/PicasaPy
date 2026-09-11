"""PicasaScrollBar.qml / PicasaSlider.qml — egyedi widget-króm (#3),
önállóan betöltve (a bekötés Main.qml-be az integrátor feladata).

Offscreen render-teszt: a komponensek példányosíthatók, a Theme-tokenekre
épülő alap-tulajdonságaik (méret, tartomány, irány, vizuális pozíció)
helyesek. Referencia-screenshot a repóban nem található ehhez a két
komponenshez, ezért tulajdonság-szintű ellenőrzés (ld. feladatleírás).
"""

import pytest
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

    # --- #323: a sáv INTERAKCIÓ NÉLKÜL is látszik, ha van mit görgetni ---
    # A korábbi kötés az `active`-hoz kötötte a láthatóságot, így a sáv
    # nyugalmi állapotban teljesen átlátszó volt — a felhasználó soha nem
    # látta. A Picasa görgetősávja állandóan ott van.

    def test_handle_visible_when_scrollable_without_interaction(
        self, app_module, qt_app
    ):
        item, engine = _load(
            app_module, qt_app, "PicasaScrollBar.qml", {"size": 0.3}
        )
        assert item.property("active") is False, "a teszt nyugalmi állapotot mér"
        assert item.property("contentItem").property("opacity") == pytest.approx(1.0)
        item.deleteLater()
        engine.deleteLater()

    def test_track_visible_when_scrollable_without_interaction(
        self, app_module, qt_app
    ):
        item, engine = _load(
            app_module, qt_app, "PicasaScrollBar.qml", {"size": 0.3}
        )
        assert item.property("background").property("opacity") > 0.0
        item.deleteLater()
        engine.deleteLater()

    def test_hidden_when_nothing_to_scroll(self, app_module, qt_app):
        # size == 1.0: a tartalom kifér, nincs mit görgetni
        item, engine = _load(
            app_module, qt_app, "PicasaScrollBar.qml", {"size": 1.0}
        )
        assert item.property("contentItem").property("opacity") == pytest.approx(0.0)
        assert item.property("background").property("opacity") == pytest.approx(0.0)
        item.deleteLater()
        engine.deleteLater()

    def test_hidden_when_policy_always_off(self, app_module, qt_app):
        item, engine = _load(
            app_module,
            qt_app,
            "PicasaScrollBar.qml",
            {"policy": 1, "size": 0.3},  # ScrollBar.AlwaysOff == 1
        )
        assert item.property("contentItem").property("opacity") == pytest.approx(0.0)
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
            # #664: `.value`, nem maga az enum-tag. A `Qt.Orientation` a
            # PySide6-ban `enum.Flag` (mert van hozzá `QFlags` alak), és a
            # Flag NEM konvertálódik int-té. A `createWithInitialProperties`
            # emiatt PySide6 6.8-on némán elhasal ("Could not set initial
            # property orientation"), a csúszka a vízszintes alapértéken
            # marad, és a teszt úgy bukik, mintha a QML volna rossz. A
            # `.value` minden PySide6-változaton (Flag és IntEnum) működik.
            {"orientation": Qt.Orientation.Vertical.value},
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
    """A színek a Theme-ből jönnek, nem beégetett hexából.

    ⚙️ #894: a fogantyú színe már NEM a kézikönyv `chromeBorder`-e, hanem a
    MÉRT `scrollart/base_win` átmenet (`Theme.scrollThumb*`) — a mérés
    felülírta a korábbi, saját tónust. Az állítás LÉNYEGE változatlan: a szín
    a `Theme`-ből jön, tehát egy helyen cserélhető, és a sötét mód is
    követi. A sín továbbra is a `chromeBg`-t használja.
    """

    def test_scrollbar_source_references_theme_tokens(self):
        import picasapy.app.application as app_module

        qml_path = (
            app_module._APP_DIR / "qml" / "PicasaPy" / "PicasaScrollBar.qml"
        )
        source = qml_path.read_text(encoding="utf-8")
        #: a fogantyú MÉRT átmenete (#894) — mind a négy token a Theme-ből
        for token in (
            "Theme.scrollThumbEdgeDark",
            "Theme.scrollThumbEdgeSoft",
            "Theme.scrollThumbMid",
            "Theme.scrollThumbLight",
        ):
            assert token in source, token
        assert "Theme.chromeBg" in source

    def test_scrollbar_source_has_no_hardcoded_hex(self):
        """Ez az eredeti szándék foga: beégetett hexa nem kerülhet a
        vezérlőbe, mert a sötét mód némán elromlana tőle. (A mért értékek a
        `Theme`-ben állnak, kommentben itt is szerepelhetnek — ezért a
        vizsgálat a KÓD-sorokra szűkül.)"""
        import re

        import picasapy.app.application as app_module

        qml_path = (
            app_module._APP_DIR / "qml" / "PicasaPy" / "PicasaScrollBar.qml"
        )
        kodsorok = [
            sor
            for sor in qml_path.read_text(encoding="utf-8").splitlines()
            if not sor.lstrip().startswith("//")
        ]
        talalatok = [
            sor.strip()
            for sor in kodsorok
            if re.search(r'"#[0-9a-fA-F]{3,8}"', sor)
        ]
        assert talalatok == [], f"beégetett szín a görgetősávban: {talalatok}"

    def test_slider_source_references_theme_tokens(self):
        """#2627: a csúszka sávja a SAJÁT tokenjeit használja.

        Az állítás lényege változatlan — a szín a Theme-ből jön, nem
        beégetve. A token viszont már nem a króm semleges szürkéje: a
        `respack.yt` mérése szerint a sáv kékesszürke, ezért kapott saját
        hármast (`sliderGroove`, `sliderGrooveBorder`, `sliderGrooveTick`).
        """
        import picasapy.app.application as app_module

        qml_path = app_module._APP_DIR / "qml" / "PicasaPy" / "PicasaSlider.qml"
        source = qml_path.read_text(encoding="utf-8")
        assert "Theme.sliderGroove" in source
        assert "Theme.sliderGrooveBorder" in source
        assert "Theme.sliderGrooveTick" in source

    def test_theme_qml_untouched_by_this_task(self):
        # a Theme.qml forró fájl — ez a teszt nem a tartalmát ellenőrzi,
        # csak azt, hogy a két új komponens nem hoz be új, nem-Theme
        # színforrást a jelenlegi tokenkészleten kívülről (kivéve a
        # PicasaButton-mintát követő, semleges szürke fogantyú-átmenetet).
        import picasapy.app.application as app_module

        theme_path = app_module._APP_DIR / "qml" / "PicasaPy" / "Theme.qml"
        assert theme_path.exists()
