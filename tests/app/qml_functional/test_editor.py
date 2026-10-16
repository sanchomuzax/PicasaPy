"""Szerkesztési munkamenet, vágás és kiegyenesítés funkcionális próbái."""

import pytest
from PySide6.QtCore import QObject
from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers


class TestEditorWiring(EditorTestHelpers):
    """A #19-es bekötés: munkamenet, vágás és kiegyenesítés."""

    def test_viewer_open_starts_edit_session(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        edit = self._edit_controller(engine)
        assert edit.property("previewSource").startswith("image://editpreview/")
        image = window.findChild(QObject, "viewerImage")
        assert image.property("source").toString().startswith("image://editpreview/")

    def test_viewer_close_ends_edit_session(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        assert self._edit_controller(engine).property("previewSource") == ""

    def test_panel_toggle_writes_ini_and_syncs_state(self, qml_app, qt_app, tmp_path):
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None, "viewerEditorPanel nem található"
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "autolight"),
        )
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "[a.jpg]" in ini_text
        assert "autolight=1" in ini_text
        # a panel állapota az EditController igazságforrásából szinkronizált:
        # az egygombos javítás gombja tiltott, amíg ő a lánc utolsó eleme (#116)
        assert panel.property("autolightEnabled") is False
        # a kép forrása új ?rev=-et kap → az előnézet frissül
        image = window.findChild(QObject, "viewerImage")
        assert "?rev=" in image.property("source").toString()

    def test_crop_accept_persists_and_advances(self, qml_app, qt_app, tmp_path):
        from PySide6.QtCore import QMetaObject, QRectF, Qt

        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        assert overlay is not None, "cropOverlay nem található"
        assert overlay.property("visible") is True
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        overlay.setProperty("hasSelection", True)
        QMetaObject.invokeMethod(
            overlay, "acceptCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "crop64=1," in ini_text
        # Enter-flow: elfogadás után a néző a következő képre lép, a
        # vágó-mód megmarad (sorozat-vágás)
        assert viewer.property("currentIndex") == 1
        assert panel.property("cropActive") is True

    def test_tilt_drag_previews_until_apply_button(
        self, qml_app, qt_app, tmp_path
    ):
        """#72/#4058: húzás és elengedés előnézet; csak az Alkalmaz ír ini-t."""
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("tiltActive", True)
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"
        image = window.findChild(QObject, "viewerImage")
        before_source = image.property("source").toString()
        ini_path = tmp_path / "kepek" / ".picasa.ini"

        slider.setProperty("value", 0.3)
        qt_app.processEvents()
        assert not ini_path.exists(), "húzás közben nem szabadna ini-be írni"
        assert image.property("source").toString() != before_source

        slider.setProperty("pressed", True)
        slider.setProperty("pressed", False)
        qt_app.processEvents()
        assert not ini_path.exists(), "elengedéskor még nem szabadna ini-be írni"

        apply_button = window.findChild(QObject, "tiltApplyButton")
        assert apply_button is not None, "tiltApplyButton nem található"
        QMetaObject.invokeMethod(
            apply_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        ini_text = ini_path.read_text(encoding="utf-8")
        assert "filters=tilt=1,0.300000,0.000000;" in ini_text

    def test_tilt_keyboard_step_previews_until_apply_button(
        self, qml_app, qt_app, tmp_path
    ):
        """#3865/#4058: billentyűs léptetéskor is előnézet, majd Apply ment."""
        from PySide6.QtCore import Qt, QMetaObject
        from PySide6.QtTest import QTest

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("tiltActive", True)
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"
        ini_path = tmp_path / "kepek" / ".picasa.ini"

        slider.setProperty("focus", True)
        qt_app.processEvents()
        assert slider.property("activeFocus") is True, (
            "a csúszka nem kapott fókuszt — a mérés nem érvényes"
        )

        QTest.keyClick(window, Qt.Key.Key_Plus)
        qt_app.processEvents()

        assert not ini_path.exists(), "a billentyűs előnézet nem írhat ini-be"
        apply_button = window.findChild(QObject, "tiltApplyButton")
        assert apply_button is not None, "tiltApplyButton nem található"
        QMetaObject.invokeMethod(
            apply_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert ini_path.exists(), "az Alkalmaz nem véglegesítette a billentyűs értéket"
        ini_text = ini_path.read_text(encoding="utf-8")
        assert "filters=tilt=1,0.040000,0.000000;" in ini_text

    def test_tilt_keyboard_step_then_cancel_restores_opening_value(
        self, qml_app, qt_app, tmp_path
    ):
        """#3865/#4058: Mégse eldobja a billentyűs előnézetet mentés nélkül."""
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt
        from PySide6.QtTest import QTest

        window, _, _ = qml_app
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        ini_path.write_text(
            "[a.jpg]\nfilters=tilt=1,0.100000,0.000000;\n", encoding="utf-8"
        )
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "tilt"),
        )
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"
        assert slider.property("value") == pytest.approx(0.1)

        slider.setProperty("focus", True)
        qt_app.processEvents()
        assert slider.property("activeFocus") is True

        QTest.keyClick(window, Qt.Key.Key_Plus)
        qt_app.processEvents()
        assert "filters=tilt=1,0.100000,0.000000;" in ini_path.read_text(
            encoding="utf-8"
        ), "a billentyűs előnézet átírta a mentett szöget"

        cancel_button = window.findChild(QObject, "tiltCancelButton")
        assert cancel_button is not None, "tiltCancelButton nem található"
        QMetaObject.invokeMethod(
            cancel_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        ini_text = ini_path.read_text(encoding="utf-8")
        assert "filters=tilt=1,0.100000,0.000000;" in ini_text, (
            "a Mégse nem állította vissza a nyitáskori szöget a billentyűs "
            "léptetés után"
        )
        assert panel.property("tiltActive") is False

    def test_tilt_tool_opens_with_saved_value_not_zero(
        self, qml_app, qt_app, tmp_path
    ):
        """#131: a döntés-csúszka a MENTETT tilt-értékről induljon, ne néma
        0-ról — különben az első érintés kinullázza a mentett döntést."""
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, _ = qml_app
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        ini_path.write_text(
            "[a.jpg]\nfilters=tilt=1,0.400000,0.000000;\n", encoding="utf-8"
        )
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "tilt"),
        )
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"
        assert slider.property("value") == pytest.approx(0.4)

    def test_navigation_with_tilt_tool_active_closes_it_for_the_next_photo(
        self, qml_app, qt_app, tmp_path
    ):
        """#3924: lapozáskor a Picasa bezárja a döntés-eszközt és a rácsot."""
        window, _, _ = qml_app
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        ini_path.write_text(
            "[a.jpg]\nfilters=tilt=1,0.400000,0.000000;\n"
            "[b.jpg]\nfilters=tilt=1,-0.200000,0.000000;\n",
            encoding="utf-8",
        )
        viewer = self._open_viewer(window, qt_app, index=0)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("tiltActive", True)
        qt_app.processEvents()
        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()

        assert panel.property("tiltActive") is False
        # a b.jpg mentett tilt-je az ini-ben érintetlen maradt
        ini_text = ini_path.read_text(encoding="utf-8")
        assert "filters=tilt=1,-0.200000,0.000000;" in ini_text

    def test_reopen_crop_tool_shows_uncropped_image_and_existing_selection(
        self, qml_app, qt_app, tmp_path
    ):
        """#71: a Vágás eszköz újranyitásakor a teljes (vágatlan) kép +
        a meglévő kijelölés látszik, a vágás folytatható marad."""
        from PySide6.QtCore import QMetaObject, QRectF, Qt

        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        overlay.setProperty("hasSelection", True)
        QMetaObject.invokeMethod(
            overlay, "acceptCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        # Enter-flow: elfogadás után a vágó-mód megmarad, de a kijelölés
        # üresre áll vissza a következő képre lépéskor
        assert panel.property("cropActive") is True
        assert overlay.property("hasSelection") is False

        # visszalépés az imént megvágott képre: a teljes kép + a mentett
        # kijelölés (nem a levágott eredmény) jelenjen meg
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        assert edit.property("previewSource").startswith("image://editpreview/")
        assert overlay.property("hasSelection") is True
        crop_rect = overlay.property("cropRect")
        assert crop_rect.x() == pytest.approx(0.25, abs=1e-3)
        assert crop_rect.width() == pytest.approx(0.5, abs=1e-3)

    def test_crop_cancel_leaves_crop_mode(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        QMetaObject.invokeMethod(
            overlay, "cancelCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("cropActive") is False
