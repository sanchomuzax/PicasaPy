"""#459 — hibatűrés-audit: a korábban NÉMÁN elbukó ini-írási hibák
(`syncFailed`/`photoOpFailed`, `albumWriteFailed`, `geoWriteFailed`,
`faceWriteFailed`) mostantól LÁTHATÓAN jelennek meg a `Main.qml` globális
hibasávjában (`errorBanner`/`errorBannerText`). Korábban EGYIK jelzés sem
volt QML-oldalon bekötve — ez a regressziós teszt annak marad a záloga,
hogy ez nem történik meg csendben újra."""

from __future__ import annotations

from PySide6.QtCore import QObject


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestErrorBannerVisibility:
    def test_sync_failed_shows_in_banner(self, qml_app, qt_app):
        window, controller, engine = qml_app
        banner_text = _child(window, "errorBannerText")
        assert banner_text.property("text") == ""
        controller.syncFailed.emit("teszt: ütközés az iniben")
        qt_app.processEvents()
        assert banner_text.property("text") == "teszt: ütközés az iniben"
        banner = _child(window, "errorBanner")
        assert banner.property("visible") is True

    def test_album_write_failed_shows_in_banner(self, qml_app, qt_app):
        window, controller, engine = qml_app
        banner_text = _child(window, "errorBannerText")
        controller.albumWriteFailed.emit("teszt: album-írás sikertelen")
        qt_app.processEvents()
        assert banner_text.property("text") == "teszt: album-írás sikertelen"

    def test_geo_write_failed_shows_in_banner(self, qml_app, qt_app):
        window, controller, engine = qml_app
        banner_text = _child(window, "errorBannerText")
        controller.geoWriteFailed.emit("teszt: geotag-írás sikertelen")
        qt_app.processEvents()
        assert banner_text.property("text") == "teszt: geotag-írás sikertelen"

    def test_close_button_clears_banner(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, engine = qml_app
        banner_text = _child(window, "errorBannerText")
        controller.syncFailed.emit("teszt")
        qt_app.processEvents()
        assert banner_text.property("text") == "teszt"
        close_button = _child(window, "errorBannerCloseButton")
        QMetaObject.invokeMethod(
            close_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert banner_text.property("text") == ""
