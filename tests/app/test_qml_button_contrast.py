"""#336: a PicasaButton felirata MINDKÉT témában olvasható.

A felhasználó éles, sötét témás képein az Importálás / Vissza a könyvtárhoz /
E-mail / Nyomtatás / Exportálás gombok teljesen üresen jelentek meg: a
komponens háttere hardkódolt VILÁGOS volt, a felirata viszont a témafüggő
`Theme.textDark` — sötét témában világos szöveg világos gombon.

Ugyanaz a hiba, amit a #314 az EditorPanel PanelButton-jánál javított; ez a
komponens kimaradt a körből.
"""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor


@pytest.fixture
def app_module():
    import picasapy.app.application as module

    return module


def _relative_luminance(color: QColor) -> float:
    """WCAG relatív luminancia (sRGB → lineáris)."""

    def channel(value: float) -> float:
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    return (
        0.2126 * channel(color.redF())
        + 0.7152 * channel(color.greenF())
        + 0.0722 * channel(color.blueF())
    )


def _contrast(first: QColor, second: QColor) -> float:
    light, dark = sorted(
        (_relative_luminance(first), _relative_luminance(second)), reverse=True
    )
    return (light + 0.05) / (dark + 0.05)


def _load_button(app_module, qt_app, properties=None):
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    factory = QQmlComponent(
        engine, str(app_module._APP_DIR / "qml" / "PicasaPy" / "PicasaButton.qml")
    )
    item = factory.createWithInitialProperties(
        {"text": "Exportálás", **(properties or {})}
    )
    assert item is not None, factory.errorString()
    return item, factory, engine


def _theme_singleton(item):
    """A Theme singleton az elem QML-kontextusából."""
    from PySide6.QtQml import qmlContext

    return qmlContext(item).contextProperty("Theme") or _theme_via_engine(item)


def _theme_via_engine(item):
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent, qmlEngine

    engine = qmlEngine(item)
    probe = QQmlComponent(engine)
    probe.setData(
        b"import QtQuick\nimport PicasaPy\nQtObject { property var t: Theme }",
        QUrl(),
    )
    holder = probe.create()
    assert holder is not None, probe.errorString()
    theme = holder.property("t")
    holder.setParent(item)  # életben tartás
    return theme


def _button_colours(item):
    """(háttér, felirat) — a gomb nevesített szín-tulajdonságaiból.

    A gradiens alsó (sötétebb) stopját vesszük: a szöveg túlnyomórészt azon
    ül, tehát az a szigorúbb mérce.
    """
    return (
        QColor(item.property("surfaceBottom")),
        QColor(item.property("inkColor")),
    )


@pytest.mark.parametrize("dark", [False, True])
@pytest.mark.parametrize("enabled", [True, False])
class TestPicasaButtonContrast:
    def test_label_is_readable(self, app_module, qt_app, dark, enabled):
        item, factory, engine = _load_button(
            app_module, qt_app, {"enabled": enabled}
        )
        theme = _theme_singleton(item)
        theme.setProperty("dark", dark)
        qt_app.processEvents()

        background, label = _button_colours(item)
        ratio = _contrast(background, label)
        assert ratio >= 3.0, (
            f"olvashatatlan felirat (dark={dark}, enabled={enabled}): "
            f"kontraszt {ratio:.2f}, háttér {background.name()}, "
            f"felirat {label.name()}"
        )

        theme.setProperty("dark", False)
        item.deleteLater()
        engine.deleteLater()
        del factory


class TestAccentButtonUnchanged:
    """A zöld (Feltöltés a Google Fotókba) gomb mindkét témában jó volt —
    maradjon fehér felirat a zöld háttéren."""

    def test_accent_label_stays_white(self, app_module, qt_app):
        from PySide6.QtGui import QColor as _QColor

        item, factory, engine = _load_button(
            app_module, qt_app, {"accent": _QColor("#3b8f00")}
        )
        background, label = _button_colours(item)
        assert label.name().lower() == "#ffffff"
        assert _contrast(background, label) >= 3.0
        item.deleteLater()
        engine.deleteLater()
        del factory
