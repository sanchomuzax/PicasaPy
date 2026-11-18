"""#7172: a forrástörlés hibája után az importablak újra használható."""

from pathlib import Path

from PySide6.QtCore import QPointF, QObject, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.halasztott_parbeszed import nyisd_meg
from support.import_kartya_7183 import (
    csatolt_kartya_kivalasztasa,
    datum_szerinti_bontas,
    elem,
)
from support.jpeg_factory import make_jpeg
from support.qt_wait import hangos_hurok


def _dialog_and_controller(window, engine):
    nyisd_meg(window, "importSourceDialog")
    dialog = window.findChild(QQuickItem, "importSourceDialog")
    assert dialog is not None
    controller = engine.rootContext().contextProperty("importSourceController")
    assert controller is not None
    return dialog, controller


def _click_center(item, qt_app):
    centre = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    target_window = item.window()
    assert target_window is not None
    QTest.mouseClick(
        target_window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        centre.toPoint(),
    )
    qt_app.processEvents()


def test_delete_oserror_shows_error_and_enables_import_again(
    qml_app, qt_app, tmp_path, monkeypatch
):
    window, _controller, engine = qml_app
    dialog, controller = _dialog_and_controller(window, engine)
    import picasapy.app.import_source_controller as controller_module

    def fail_to_remove(_path: Path) -> None:
        raise OSError("a forrás írásvédett")

    monkeypatch.setattr(controller_module, "_remove_source_file", fail_to_remove)
    start_button = window.findChild(QObject, "importSourceStartButton")
    assert start_button is not None
    error_text = window.findChild(QObject, "importSourceErrorText")
    assert error_text is not None
    confirm = window.findChild(
        QObject, "importSourceConfirmRemoveDialog"
    )
    assert confirm is not None
    confirm_yes = window.findChild(
        QObject, "importSourceConfirmRemoveYesButton"
    )
    assert confirm_yes is not None
    original_height = window.height()

    # A tényleges gombkattintást a felépült ablak geometriájából számoljuk;
    # három közeli ablakmagasságon is újra használhatónak kell maradnia.
    for height_delta in (-5, 0, 5):
        window.setProperty("height", original_height + height_delta)
        source = tmp_path / f"kartya-{height_delta:+d}"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / f"cel-konyvtar-{height_delta:+d}"
        dest.mkdir()

        # #7183: törölni csak DCIM mappás csatolt kártyáról lehet (valódi
        # kattintás a meghajtó-listán és a törlési rádión)
        (source / "DCIM").mkdir()
        csatolt_kartya_kivalasztasa(
            dialog, controller, qt_app, monkeypatch, source, darab=1
        )
        dialog.setProperty("destFolder", str(dest))
        datum_szerinti_bontas(dialog, qt_app)
        _click_center(elem(dialog, "importSourceAfterDeleteCopiedRadio"), qt_app)
        assert dialog.property("effectiveAfterCopying") == "delete_copied"
        assert start_button.property("enabled") is True

        _click_center(start_button, qt_app)
        assert confirm.property("visible") is True
        finish_loop = hangos_hurok(controller.importFinished)
        _click_center(confirm_yes, qt_app)
        finish_loop.exec()
        qt_app.processEvents()

        assert error_text.property("visible") is True
        assert "a.jpg" in error_text.property("text")
        assert "írásvédett" in error_text.property("text")
        assert dialog.property("lastFailedCount") == 1
        assert dialog.property("importing") is False
        assert dialog.property("visible") is True
        assert start_button.property("enabled") is True
        assert (source / "a.jpg").exists()
        assert (dest / "2024-03-05" / "a.jpg").exists()

    window.setProperty("height", original_height)
