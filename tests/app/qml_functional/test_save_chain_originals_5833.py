"""#5833: a Mentés és az Undo Save valódi QML-kattintásai a lemezre írnak."""

from __future__ import annotations

from pathlib import Path

import cv2
import pytest
from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem

from picasapy.ini import load_document
from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    kijelol,
    tetel_kattintasa,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import kattints
from tests.support.varakozas import var_feltetelre

_HEIGHT_DELTAS = (-5, 0, 5)
_PHOTO_SECTION = "a.jpg"


@pytest.fixture
def picasa_jpeges_app(qt_app, tmp_path):
    """A teljes QML-app a repóban lévő JPEG-fájllal, elszigetelt könyvtárban."""
    from conftest import _build_qml_app
    from support.jpeg_factory import make_minta_jpeg

    photo_source = (
        Path(__file__).resolve().parents[3]
        / "tests"
        / "fixtures"
        / "face_type_a_name_reference_en38.png"
    )

    def real_photo_fixture(folder: Path):
        image = cv2.imread(str(photo_source), cv2.IMREAD_COLOR)
        assert image is not None
        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 96])
        assert ok
        (folder / _PHOTO_SECTION).write_bytes(encoded.tobytes())
        make_minta_jpeg(folder / "b.jpg", size=(320, 240), seed=5833)

    app = _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=real_photo_fixture,
        valodi_belyegkep=True,
        belyegkep_meret=256,
    )
    window, controller, engine = next(app)
    menu_bar = window.property("menuBar")
    assert menu_bar is not None
    yield window, controller, engine
    del menu_bar
    next(app, None)


def _wait(qt_app, condition, timeout: float = 10.0) -> bool:
    return var_feltetelre(qt_app, condition, timeout)


def _child(window, name: str):
    item = window.findChild(QQuickItem, name)
    assert item is not None, f"{name} nem található"
    return item


def _save_button(dialog):
    buttons = [
        item
        for item in dialog.findChildren(QQuickItem)
        if "Button" in item.metaObject().className()
        and item.property("text") in {"Save", "Mentés"}
        and item.isVisible()
    ]
    assert buttons, "a mentés párbeszéd valódi Save gombja hiányzik"
    return buttons[0]


def _disk_filters(image_path: Path) -> str:
    ini_path = image_path.parent / ".picasa.ini"
    if not ini_path.is_file():
        return ""
    section = load_document(ini_path).section(image_path.name)
    return (section.get("filters") if section is not None else None) or ""


def _click_file_item(window, qt_app, object_name: str):
    menu_bar = window.property("menuBar")
    assert menu_bar is not None
    _megnyit(menu_bar, qt_app, "&File")
    item = _child(window, object_name)
    assert item.property("visible") is True, f"{object_name} nem látható"
    assert item.property("enabled") is True, f"{object_name} le van tiltva"
    kattints(window, qt_app, item)
    return item


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_lucky_mentes_undo_save_az_ini_bejegyzest_es_a_kepet_is_frissiti(
    picasa_jpeges_app, qt_app, tmp_path, height_delta
):
    window, controller, _engine = picasa_jpeges_app
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    original_height = int(window.height())
    window.resize(int(window.width()), original_height + height_delta)
    assert _wait(qt_app, lambda: int(window.height()) == original_height + height_delta), (
        "az ablak nem vette fel a kért magasságot"
    )
    assert _wait(qt_app, lambda: controller.photos.rowCount() >= 2), (
        "a helyi JPEG-könyvtár nem töltődött be"
    )
    kijelol(window, qt_app, [0])

    image_path = Path(str(controller.photos.filePathAt(0)))
    assert image_path.name == _PHOTO_SECTION
    bytes_before_save = image_path.read_bytes()

    wait_for_photo_op(
        controller,
        lambda: tetel_kattintasa(
            window,
            qt_app,
            "&Picture",
            "menuBatchEnhance",
            almenu_utvonal=("menuPictureBatchEdit",),
        ),
        qt_app=qt_app,
    )
    assert _wait(
        qt_app, lambda: _disk_filters(image_path) == "enhance=1;"
    ), "az I'm Feeling Lucky kattintása nem tette a láncba az enhance effektet"

    _click_file_item(window, qt_app, "menuFileSave")
    save_dialog = window.findChild(QObject, "saveConfirmDialog")
    assert save_dialog is not None
    assert _wait(qt_app, lambda: save_dialog.property("visible") is True), (
        "a Mentés nem nyitotta meg a megerősítő párbeszédet"
    )
    kattints(window, qt_app, _save_button(save_dialog))
    wait_for_photo_op(controller, lambda: None, qt_app=qt_app)

    current_section = load_document(image_path.parent / ".picasa.ini").section(
        image_path.name
    )
    assert current_section is not None
    assert current_section.items() == (("backuphash", current_section.get("backuphash")),)
    assert (current_section.get("backuphash") or "").isdecimal()
    original_ini_path = image_path.parent / ".picasaoriginals" / ".picasa.ini"
    original_section = load_document(original_ini_path).section(image_path.name)
    assert original_section is not None
    assert original_section.get("filters") == "enhance=1;"
    bytes_after_save = image_path.read_bytes()
    assert bytes_after_save != bytes_before_save, "a Mentés nem változtatta meg a képfájlt"

    screenshot = tmp_path / f"picasapy-mentes-utan-5833-{height_delta:+d}.jpg"
    assert window.grabWindow().save(str(screenshot), "JPEG", 90), (
        "a Mentés utáni QML-képernyőkép nem menthető"
    )

    _click_file_item(window, qt_app, "menuFileRevert")
    revert_dialog = window.findChild(QObject, "revertConfirmDialog")
    assert revert_dialog is not None
    assert _wait(qt_app, lambda: revert_dialog.property("visible") is True), (
        "a Visszaállítás párbeszéd nem nyílt meg"
    )
    undo_button = _child(window, "revertUndoSaveButton")
    assert _wait(qt_app, lambda: undo_button.isVisible()), (
        "az Undo Save gomb nem látható"
    )
    kattints(window, qt_app, undo_button)
    wait_for_photo_op(controller, lambda: None, qt_app=qt_app)

    restored_section = load_document(image_path.parent / ".picasa.ini").section(
        image_path.name
    )
    assert restored_section is not None
    assert restored_section.get("filters") == "enhance=1;"
    assert restored_section.get("redo") is None
    assert image_path.read_bytes() == bytes_before_save
