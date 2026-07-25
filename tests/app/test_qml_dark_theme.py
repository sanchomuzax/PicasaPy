"""QML-funkcionális tesztek: sötét téma (#28).

A Nézet → Sötét téma menüpont kapcsolható, a Theme-tokenek követik a
controller kapcsolóját (a főablak háttere a mérce), és a váltás a
felület minden rétegében ugyanabból a tokenkészletből él — nem marad
„fehér folt" egy-egy panelen.
"""

from PySide6.QtCore import QObject


def _theme_singleton(engine):
    """A Theme singleton példánya az engine-ből (a QML-oldali kötések forrása)."""
    return engine.singletonInstance("PicasaPy", "Theme")


def _evaluate(window, expression):
    """QML-kifejezés kiértékelése az ablak kontextusában — a Python-oldalról
    nem olvasható property-khez (a `palette` QQuickPalette*, amire nincs
    Python-konverter). A #232 tanulsága: az élő futásidőt kell mérni."""
    from PySide6.QtQml import QQmlEngine, QQmlExpression

    expr = QQmlExpression(QQmlEngine.contextForObject(window), window, expression)
    value = expr.evaluate()
    # a PySide6 (érték, undefined-e) párost ad vissza
    return value[0] if isinstance(value, tuple) else value


class TestDarkThemeMenu:
    def test_menu_item_present_and_unchecked(self, qml_app):
        window, controller, lib, engine = qml_app
        item = window.findChild(QObject, "menuViewDarkTheme")
        assert item is not None
        assert item.property("enabled") is True
        assert item.property("checkable") is True
        assert item.property("checked") is False

    def test_menu_item_follows_controller(self, qml_app):
        window, controller, lib, engine = qml_app
        item = window.findChild(QObject, "menuViewDarkTheme")
        controller.setDarkTheme(True)
        assert item.property("checked") is True
        controller.setDarkTheme(False)
        assert item.property("checked") is False


class TestDarkThemeBindings:
    def test_window_background_switches(self, qml_app):
        window, controller, lib, engine = qml_app
        light = window.property("color")
        controller.setDarkTheme(True)
        dark = window.property("color")
        assert dark != light
        # a sötét vászon tényleg sötét (a Qt-szín 0..1 komponenseket ad)
        assert dark.lightnessF() < 0.35
        assert light.lightnessF() > 0.65

    def test_toggle_returns_to_light(self, qml_app):
        window, controller, lib, engine = qml_app
        light = window.property("color")
        controller.toggleDarkTheme()
        controller.toggleDarkTheme()
        assert window.property("color") == light

    def test_panel_palette_follows_theme(self, qml_app):
        """A Qt Controls-paletta (beviteli mezők, gombok) sem ragadhat
        világoson — a sötét mód különben fehér mezőket hagyna."""
        window, controller, lib, engine = qml_app
        base_light = _evaluate(window, "palette.base")
        button_light = _evaluate(window, "palette.button")
        controller.setDarkTheme(True)
        base_dark = _evaluate(window, "palette.base")
        assert base_dark != base_light
        assert base_dark.lightnessF() < 0.4
        assert _evaluate(window, "palette.button") != button_light


class TestThemeTokens:
    def test_singleton_tokens_switch_together(self, qml_app):
        window, controller, lib, engine = qml_app
        theme = _theme_singleton(engine)
        assert theme is not None
        assert theme.property("dark") is False
        light_ink = theme.property("ink")
        light_panel = theme.property("panelBg")
        controller.setDarkTheme(True)
        assert theme.property("dark") is True
        # a tinta világosodik, a felület sötétedik — a kontraszt megfordul
        assert theme.property("ink").lightnessF() > light_ink.lightnessF()
        assert theme.property("panelBg").lightnessF() < light_panel.lightnessF()

    def test_brand_colors_are_theme_independent(self, qml_app):
        window, controller, lib, engine = qml_app
        theme = _theme_singleton(engine)
        brand = [theme.property(name) for name in ("brandRed", "brandYellow", "brandBlue")]
        controller.setDarkTheme(True)
        assert [theme.property(n) for n in ("brandRed", "brandYellow", "brandBlue")] == brand
