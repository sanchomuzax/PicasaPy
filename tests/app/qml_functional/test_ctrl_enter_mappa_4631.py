"""#4631 — a Ctrl+Enter kijelöléssel képet, nélküle aktuális mappát mutat."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest


def test_ctrl_enter_a_kijelolt_kepet_vagy_az_aktualis_mappat_mutatja(
    qml_app, qt_app, monkeypatch
):
    """Mindkét menürekord ugyanazt a billentyűt használja, eltérő célponttal."""
    import picasapy.app.fileops_controller as fileops_module

    window, controller, _engine = qml_app
    mutatott_kepek = []
    mutatott_mappak = []
    monkeypatch.setattr(
        fileops_module,
        "reveal_in_file_manager",
        lambda path: mutatott_kepek.append(Path(path)),
    )
    monkeypatch.setattr(
        fileops_module,
        "open_folder_in_file_manager",
        lambda path: mutatott_mappak.append(Path(path)),
    )

    kep = Path(controller.photos.filePathAt(0))
    mappa = Path(controller.currentFolder)
    alapmagassag = window.height()
    for elteres in (-5, 0, 5):
        window.resize(window.width(), alapmagassag + elteres)
        qt_app.processEvents()

        mutatott_kepek.clear()
        mutatott_mappak.clear()
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        QTest.keyClick(
            window, Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier
        )
        qt_app.processEvents()

        assert mutatott_kepek == [kep], f"kijelölt kép, ablakeltérés: {elteres}px"
        assert mutatott_mappak == []

        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        qt_app.processEvents()
        QTest.keyClick(
            window, Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier
        )
        qt_app.processEvents()

        assert mutatott_kepek == [kep]
        assert mutatott_mappak == [mappa], (
            f"üres kijelölés, ablakeltérés: {elteres}px"
        )
