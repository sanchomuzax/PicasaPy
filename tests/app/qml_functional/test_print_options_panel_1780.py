"""A #1780 panel valódi QML-felületi kapuja és indexkép-tiltása."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, QObject, QTranslator


def _child(root, name):
    child = root.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


@pytest.fixture
def magyar_forditas(qt_app):
    from picasapy.app import application

    fordito = QTranslator(qt_app)
    qm = Path(application.__file__).parent / "i18n" / "picasapy_hu.qm"
    assert fordito.load(str(qm)), f"a magyar fordítás nem tölthető be: {qm}"
    assert qt_app.installTranslator(fordito)
    yield
    qt_app.removeTranslator(fordito)


@pytest.fixture
def qml_app_magyar(magyar_forditas, qml_app):
    """A QML a fordító telepítése után töltődjön be."""
    return qml_app


def _open_print_dialog(window, qt_app):
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    menu = _child(window, "menuFilePrint")
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return _child(window, "printDialog")


class TestPrintOptionsPanel:
    def test_a_feliratok_a_betoltott_magyar_forditassal_es_rejtett_szinvalasztoval(
        self, qml_app_magyar, qt_app
    ):
        window, _controller, _engine = qml_app_magyar
        dialog = _open_print_dialog(window, qt_app)
        panel = _child(dialog, "printOptionsPanel")
        QMetaObject.invokeMethod(
            _child(dialog, "printOptionsButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        # Ezek a feliratok az éles magyar .qm-ből érkeznek, nem QML-be írt
        # magyar szövegből.
        assert _child(panel, "printOptionCaptionLabel").property("text") == (
            "Képfeliratok"
        )
        assert QCoreApplication.translate("PrintOptionsPanel", "Captions") == (
            "Képfeliratok"
        )
        assert [
            _child(panel, f"printOptionSource{index}").property("text")
            for index in range(4)
        ] == ["Nincs szöveg", "Képfelirat", "Fájlnév", "Exif-adatok"]
        assert [
            _child(panel, f"printOptionPlacement{index}").property("text")
            for index in range(3)
        ] == ["A kép alatt", "A képen", "A szegélyen"]
        assert _child(panel, "printOptionTextPickerPanel").property("visible") is False

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
        self, qml_app_magyar, qt_app
    ):
        window, _controller, _engine = qml_app_magyar
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
        assert _child(panel, "printOptionsDisabledText").property("text") == (
            "Ezek a beállítások indexképek nyomtatásakor nem használhatók."
        )
        for object_name in (
            *(f"printOptionSource{index}" for index in range(4)),
            *(f"printOptionPlacement{index}" for index in range(3)),
            "printOptionFontBox",
            "printOptionSizeBox",
            "printOptionWrapCheckBox",
            "printOptionBorderCheckBox",
            "printOptionBorderSlider",
            "printOptionBottomOnlyCheckBox",
            "printOptionEvenBorderCheckBox",
            "printOptionTextColorBevel",
            "printOptionBorderColor0",
        ):
            assert _child(panel, object_name).property("enabled") is False, object_name
