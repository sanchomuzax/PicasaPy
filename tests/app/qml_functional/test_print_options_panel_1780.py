"""A #1780 panel valódi QML-felületi kapuja és indexkép-tiltása."""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, Qt, QObject


def _child(root, name):
    child = root.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _open_print_dialog(window, qt_app):
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    menu = _child(window, "menuFilePrint")
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return _child(window, "printDialog")


class TestPrintOptionsPanel:
    def test_a_felhasznaloi_ut_megnyitja_a_teljes_panelt(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        dialog = _open_print_dialog(window, qt_app)
        panel = _child(dialog, "printOptionsPanel")
        assert panel.property("visible") is False

        QMetaObject.invokeMethod(
            _child(dialog, "printOptionsButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert panel.property("visible") is True
        assert len(_variant(panel.property("sourceLabels"))) == 4
        assert len(_variant(panel.property("placementLabels"))) == 3
        assert len(_variant(panel.property("textSizes"))) == 16
        assert _child(panel, "printOptionBorderSlider") is not None
        assert _child(panel, "printOptionTextColorPalette") is not None
        assert _child(panel, "printOptionBorderColorPalette") is not None

    def test_indexkepnel_a_vezrlok_tiltva_es_magyarazat_latszik(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        menu = _child(window, "menuFolderPrintContactSheet")
        QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        dialog = _child(window, "printDialog")
        panel = _child(dialog, "printOptionsPanel")

        QMetaObject.invokeMethod(
            _child(dialog, "printOptionsButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert panel.property("contactSheet") is True
        assert _child(panel, "printOptionsDisabledText").property("visible") is True
        assert _child(panel, "printOptionBorderCheckBox").property("enabled") is False
        assert _child(panel, "printOptionWrapCheckBox").property("enabled") is False
