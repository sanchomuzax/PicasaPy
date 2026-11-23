"""#7408: az Undo gomb közvetlenül vonja vissza a sikeres Mentést."""

from __future__ import annotations

import os
import time
from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication, QMetaObject, QObject, Qt
from PySide6.QtQuick import QQuickItem

from picasapy.ini import load_document
from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import kijelol
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import kattints
from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers
from tests.support.varakozas import var_feltetelre

_ABLAKMAGASSAG_ELTERESEK = (-5, 0, 5)
_KEPNEV = "gray_ramp.jpg"


@pytest.fixture
def picasa_szurke_rampas_app(qt_app, tmp_path):
    """Valódi fájlokon és az alkalmazás teljes QML-jén futó szerkesztő."""
    from conftest import _build_qml_app
    from support.jpeg_factory import make_minta_jpeg

    def keszits_kepeket(folder: Path) -> None:
        ramp = np.tile(np.arange(1024, dtype=np.uint8), (256, 1))
        kep = cv2.cvtColor(ramp, cv2.COLOR_GRAY2BGR)
        siker, kodolt = cv2.imencode(
            ".jpg", kep, [cv2.IMWRITE_JPEG_QUALITY, 96]
        )
        assert siker
        ramp_path = folder / _KEPNEV
        ramp_path.write_bytes(kodolt.tobytes())
        # A Picasa moddate 100 ns-os egységű; ilyen mtime-ról pontosan
        # visszaállítható és a próba nem az aktuális időzítéstől függ.
        eredeti_mtime = (time.time_ns() - 5_000_000_000) // 100 * 100
        os.utime(ramp_path, ns=(eredeti_mtime, eredeti_mtime))
        make_minta_jpeg(folder / "zz.jpg", size=(320, 240), seed=7408)

    app = _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=keszits_kepeket,
        valodi_belyegkep=True,
        belyegkep_meret=256,
    )
    window, controller, engine = next(app)
    menu_bar = window.property("menuBar")
    assert menu_bar is not None
    yield window, controller, engine
    del menu_bar
    next(app, None)


def _var(qt_app, feltetel, timeout: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, timeout)


def _item(window, nev: str) -> QQuickItem:
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _gombfelirat(window, nev: str) -> str:
    cimke = _item(window, f"{nev}Label")
    return str(cimke.property("text") or "")


@pytest.mark.parametrize("magassag_elteres", _ABLAKMAGASSAG_ELTERESEK)
def test_szoveg_mentes_utan_az_undo_gomb_visszavonja_a_mentest(
    picasa_szurke_rampas_app, qt_app, tmp_path, magassag_elteres
):
    window, controller, engine = picasa_szurke_rampas_app
    window.show()
    window.requestActivate()
    assert _var(qt_app, lambda: controller.photos.rowCount() >= 2)
    window.resize(1280, 1024 + magassag_elteres)
    assert _var(
        qt_app,
        lambda: int(window.height()) == 1024 + magassag_elteres,
    ), "az ablak nem vette fel a kért magasságot"
    kijelol(window, qt_app, [0])

    image_path = Path(str(controller.photos.filePathAt(0)))
    assert image_path.name == _KEPNEV

    EditorTestHelpers()._open_viewer(window, qt_app)
    panel = window.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
    panel.setProperty("textActive", True)
    qt_app.processEvents()
    field = window.findChild(QObject, "textContentField")
    assert field is not None
    field.setProperty("text", "PicasaUndoSave")
    edit = EditorTestHelpers()._edit_controller(engine)
    controller.set_edit_controllers(edit)
    edit._undoSaveRequested.connect(controller._undo_save_for_editor)
    edit.previewTextPlacement(0.316406, 0.144531)
    qt_app.processEvents()
    apply_button = window.findChild(QObject, "textApplyButton")
    assert apply_button is not None and apply_button.property("enabled") is True
    QMetaObject.invokeMethod(
        apply_button, "buttonClicked", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()

    applied_section = load_document(image_path.parent / ".picasa.ini").section(
        image_path.name
    )
    assert applied_section is not None
    assert "PicasaUndoSave" in (applied_section.get("text") or "")
    assert applied_section.get("textactive") == "1"
    # A .picasa.ini írás helyben megérinti a képfájl mtime-ját; a jegy a
    # közvetlenül Mentés előtti fájlállapot visszaállítását kéri.
    bytes_mentes_elott = image_path.read_bytes()
    mtime_mentes_elott = image_path.stat().st_mtime_ns
    undo_button = _item(window, "editUndoButton")
    redo_button = _item(window, "editRedoButton")
    assert undo_button.property("enabled") is False
    assert _gombfelirat(window, "editUndoButton") != QCoreApplication.translate(
        "SaveDialogs", "Undo Save"
    ), "a Mentés nélküli Apply nem jelölheti Undo Save-nek a gombot"

    # A főablak Ctrl+S engedélyezési őre jelenleg csak filters= láncot néz;
    # a mért #7408 eset tisztán text= állapot. A teszt a már létező mentési
    # slotot hívja, hogy a jegy által érintett sikeres mentés utáni Undo-utat
    # vizsgálja, és ne változtassa meg a mentés aktiválási szabályát.
    wait_for_photo_op(
        controller,
        lambda: controller.saveRowsToDisk([0]),
        qt_app=qt_app,
    )

    undo_label = QCoreApplication.translate("SaveDialogs", "Undo Save")
    redo_label = QCoreApplication.translate("EditorPanel", "Redo")
    assert _var(qt_app, lambda: undo_button.property("enabled") is True), (
        "sikeres Mentés után az Undo gomb nem aktív"
    )
    assert _gombfelirat(window, "editUndoButton") == undo_label
    assert redo_button.property("enabled") is False
    assert _gombfelirat(window, "editRedoButton") == redo_label
    assert window.grabWindow().save(
        str(tmp_path / f"mentes-utan-{magassag_elteres:+d}.png")
    )

    originals = image_path.parent / ".picasaoriginals"
    assert (originals / image_path.name).is_file()
    assert (originals / image_path.name).stat().st_mtime_ns == mtime_mentes_elott
    # A látható Undo gomb valódi egérkattintása közvetlenül a lemezműveletet
    # indítja; a Visszaállítás párbeszéd egyik ága sem jelenhet meg.
    kattints(window, qt_app, undo_button)
    wait_for_photo_op(controller, lambda: None, qt_app=qt_app)
    assert _var(qt_app, lambda: undo_button.property("enabled") is False)
    assert undo_button.property("enabled") is False
    assert redo_button.property("enabled") is False
    assert _gombfelirat(window, "editUndoButton") == QCoreApplication.translate(
        "EditorPanel", "Undo"
    )
    assert _gombfelirat(window, "editRedoButton") == redo_label
    assert not (originals / image_path.name).exists()
    originals_ini = originals / ".picasa.ini"
    assert originals_ini.is_file()
    assert originals_ini.read_bytes() == b""
    assert image_path.read_bytes() == bytes_mentes_elott
    assert image_path.stat().st_mtime_ns == mtime_mentes_elott

    restored_section = load_document(image_path.parent / ".picasa.ini").section(
        image_path.name
    )
    assert restored_section is not None
    assert "PicasaUndoSave" in (restored_section.get("text") or "")
    assert restored_section.get("textactive") == "1"
    revert_dialog = window.findChild(QObject, "revertConfirmDialog")
    assert revert_dialog is None or revert_dialog.property("visible") is False
    assert window.grabWindow().save(
        str(tmp_path / f"undo-save-utan-{magassag_elteres:+d}.png")
    )
