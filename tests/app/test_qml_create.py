"""QML-funkcionális tesztek: Létrehozás menü — kollázs, mozgófilm (#29).

A menüpontok csak kijelölés mellett élnek, a dialógusok kijelölés nélkül
nem nyílnak, az OK csak célfájllal engedélyezett, és a háttérszálas munka
végén az eredmény-dialógus jelenik meg a controller jelzésére.
"""

import cv2
import numpy as np
from PySide6.QtCore import QEventLoop, QObject, QTimer


def _settle(qt_app, rounds=4):
    for _ in range(rounds):
        qt_app.processEvents()
        pause = QEventLoop()
        QTimer.singleShot(10, pause.quit)
        pause.exec()


class TestCreateMenu:
    def test_items_disabled_without_selection(self, qml_app):
        window, controller, lib, engine = qml_app
        for name in ("menuCreateCollage", "menuCreateMovie"):
            item = window.findChild(QObject, name)
            assert item is not None, name
            assert item.property("enabled") is False

    def test_items_enabled_with_selection(self, qml_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        for name in ("menuCreateCollage", "menuCreateMovie"):
            assert window.findChild(QObject, name).property("enabled") is True


class TestCollageDialog:
    def test_does_not_open_without_selection(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.findChild(QObject, "menuCreateCollage").property("enabled")
        dialog = window.findChild(QObject, "collageDialog")
        assert dialog is not None
        dialog.metaObject().invokeMethod(dialog, "openForSelection")
        _settle(qt_app, 2)
        assert dialog.property("visible") is False

    def test_opens_with_selection_and_offers_six_types(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        dialog = window.findChild(QObject, "collageDialog")
        dialog.metaObject().invokeMethod(dialog, "openForSelection")
        _settle(qt_app, 2)
        assert dialog.property("visible") is True
        # #431: a HAT Picasa-elrendezés (korábban a #29-es, saját tervezésű négy)
        assert len(window.findChild(QObject, "collageKindBox").property("model")) == 6
        # …és a képkeret-választó is megjelent mellette
        assert len(window.findChild(QObject, "collageBorderBox").property("model")) == 3
        assert dialog.property("targetFile") == ""

    def test_selection_count_is_shown(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        label = window.findChild(QObject, "collageCountLabel")
        assert "2" in label.property("text")


class TestMovieDialog:
    def test_opens_with_selection(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        dialog = window.findChild(QObject, "movieDialog")
        dialog.metaObject().invokeMethod(dialog, "openForSelection")
        _settle(qt_app, 2)
        assert dialog.property("visible") is True

    def test_seconds_spinbox_is_tenth_second_based(self, qml_app):
        window, controller, lib, engine = qml_app
        spin = window.findChild(QObject, "movieSeconds")
        assert spin is not None
        assert spin.property("from") == 10
        assert spin.property("to") == 100
        assert spin.property("value") == 30  # 3,0 mp alapértelmezés


class TestResultDialog:
    def test_collage_result_is_shown(self, qml_app, qt_app, tmp_path):
        window, controller, lib, engine = qml_app
        target = tmp_path / "kollazs.jpg"
        loop = QEventLoop()
        controller.collageFinished.connect(loop.quit)
        controller.makeCollage([0, 1], "regulargrid", str(target))
        QTimer.singleShot(10000, loop.quit)
        loop.exec()
        _settle(qt_app, 2)

        assert target.exists()
        decoded = cv2.imdecode(
            np.frombuffer(target.read_bytes(), np.uint8), cv2.IMREAD_COLOR
        )
        assert decoded is not None
        result = window.findChild(QObject, "createResultDialog")
        assert result.property("visible") is True
        assert str(target) in result.property("message")

    def test_missing_files_get_their_own_sentence(self, qml_app, qt_app):
        # #459/3: a hiányzó fájl KÜLÖN mondatot kap (megmondja, mi
        # történhetett), a csak olvashatatlan képek a semleges „kihagyva"
        # számban maradnak — a kettő nem folyhat össze.
        window, controller, lib, engine = qml_app
        # 3 kihagyott, ebből 2 nem található → 1 olvashatatlan
        controller.collageFinished.emit("/tmp/k.jpg", 5, 3, 2)
        _settle(qt_app, 2)
        result = window.findChild(QObject, "createResultDialog")
        lines = result.property("message").splitlines()
        missing_lines = [line for line in lines if "2" in line]
        unreadable_lines = [line for line in lines if "1" in line]
        assert missing_lines, lines
        assert unreadable_lines, lines
        assert missing_lines != unreadable_lines

    def test_no_missing_sentence_when_all_files_exist(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        controller.collageFinished.emit("/tmp/k.jpg", 5, 0, 0)
        _settle(qt_app, 2)
        result = window.findChild(QObject, "createResultDialog")
        assert len(result.property("message").splitlines()) == 2

    def test_collage_failure_is_shown(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        controller.makeCollage([], "regulargrid", "")
        _settle(qt_app, 2)
        result = window.findChild(QObject, "createResultDialog")
        assert result.property("visible") is True
        assert result.property("message")
