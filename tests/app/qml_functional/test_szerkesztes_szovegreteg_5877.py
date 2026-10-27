"""A Szerkesztés ▸ Copy/Paste Text a Text eszköz rétegét kezeli (#5877)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtQml import QQmlExpression, qmlContext
from picasapy.ini import load_document, update_document
from picasapy.ini.text_overlay import (
    TextBlock,
    TextGeometry,
    TextOverlay,
    TextStyle,
    serialize_text,
)
from picasapy.scanner import PICASA_INI_NAME
from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _kattints
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import vizualis_bejaras
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.app.qml_functional._fomenu_4420_menu import (
    _megnyit,
    _menupont,
    _varj,
    _zarj_menuket,
)


@pytest.fixture
def qml_app_kepekkel(qt_app, tmp_path):
    """Két mintázott JPEG a valódi bélyegkép-szolgáltatóval (a kiadásképhez)."""

    def kepeket(lib: Path) -> None:
        make_minta_jpeg(lib / "a.jpg", size=(640, 480), seed=7)
        make_minta_jpeg(lib / "b.jpg", size=(320, 240), seed=8)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _valodi_belyegkep_kesz(window) -> bool:
    for elem in vizualis_bejaras(window.contentItem()):
        if elem.objectName() != "thumbImage" or not elem.property("source"):
            continue
        kifejezes = QQmlExpression(qmlContext(elem), elem, "status === Image.Ready")
        ertek, hiba = kifejezes.evaluate()
        if not hiba and ertek:
            return True
    return False


def _menutetel(menu, object_name: str):
    for index in range(int(menu.property("count") or 0)):
        item = _menupont(menu, index)
        if item.objectName() == object_name:
            return item
    raise AssertionError(f"{object_name} nem található a Szerkesztés menüben")


def _kijelol(window, qt_app, rows: list[int]) -> None:
    window.setProperty("selectedIndexes", rows)
    window.setProperty("selectedIndex", rows[0] if rows else -1)
    qt_app.processEvents()


def _text_reteg() -> str:
    return serialize_text(
        TextOverlay(
            blocks=(
                TextBlock(
                    content="PicasaPy text layer",
                    font="Arial",
                    geometry=TextGeometry(0.5, 0.5),
                    style=TextStyle(
                        fill_argb=0xFFFFFFFF,
                        outline_argb=0xFF000000,
                    ),
                ),
            )
        )
    )


def _ini_szakasz(controller, row: int):
    photo = controller.photos.photos[row]
    path = Path(photo.folder_path) / PICASA_INI_NAME
    return load_document(path).section(photo.name)


def _szovegreteg_irasa(controller, row: int, value: str) -> None:
    photo = controller.photos.photos[row]
    path = Path(photo.folder_path) / PICASA_INI_NAME

    def mutate(document):
        document = document.with_value(photo.name, "text", value)
        return document.with_value(photo.name, "textactive", "1")

    update_document(path, mutate, backup=False)


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_szerkesztes_menu_a_szovegreteget_masolja_es_illeszti(
    qml_app_kepekkel, qt_app, magassag_eltolas
):
    window, controller, _engine = qml_app_kepekkel
    celmagassag = window.height() + magassag_eltolas
    window.setHeight(celmagassag)
    assert _varj(qt_app, lambda: window.height() == celmagassag), (
        "a főablak magassága nem állt be a kért értékre"
    )
    window.show()
    _kijelol(window, qt_app, [0])

    # Job-283: egy képfelirat nem Text eszközös réteg.
    wait_for_photo_op(controller, lambda: controller.setCaption(0, "Képfelirat"))
    assert _varj(
        qt_app, lambda: controller.photos.captionAt(0) == "Képfelirat"
    ), "a kiinduló képfelirat nem mentődött"
    menu_bar = window.property("menuBar")
    edit_menu = _megnyit(menu_bar, qt_app, "&Edit")
    copy_item = _menutetel(edit_menu, "menuEditCopyText")
    paste_item = _menutetel(edit_menu, "menuEditPasteText")
    assert copy_item.property("enabled") is False, (
        "a Copy Text a képfelirat miatt aktív; csak Text-réteget másolhat"
    )
    assert paste_item.property("enabled") is False, (
        "a Paste Text képfeliratból kapott tartalmat"
    )
    _zarj_menuket(menu_bar, qt_app)

    # Job-287: a Text eszközzel létrehozott réteg a két menütételt elérhetővé
    # teszi. A fájlba írás a termék ini-rétegén keresztül történik.
    value = _text_reteg()
    _szovegreteg_irasa(controller, 0, value)
    _kijelol(window, qt_app, [1])
    _kijelol(window, qt_app, [0])
    edit_menu = _megnyit(menu_bar, qt_app, "&Edit")
    copy_item = _menutetel(edit_menu, "menuEditCopyText")
    paste_item = _menutetel(edit_menu, "menuEditPasteText")
    assert copy_item.property("enabled") is True, (
        "a Text réteges kijelölt kép mellett a Copy Text szürke"
    )
    assert paste_item.property("enabled") is True, (
        "a Text eszközből származó szövegréteg-puffer mellett a Paste Text szürke"
    )

    # Kiadáskép a megnyitott Edit menüről a mért, Text-réteges állapotban.
    kepmappa = os.environ.get("PICASAPY_KIADASKEP_MAPPA")
    if kepmappa:
        assert _varj(qt_app, lambda: _valodi_belyegkep_kesz(window), 20.0), (
            "a kiadásképhez nem töltődött be valódi bélyegkép"
        )
        menu_window = _menupont(edit_menu, 0).window()
        screenshot = menu_window.grabWindow()
        assert not screenshot.isNull(), "a megnyitott Szerkesztés menü üres képet adott"
        kep = Path(kepmappa) / "kep5877_szerkesztes_menu.png"
        assert screenshot.save(str(kep), "PNG"), "a menükép nem menthető"

    _kattints(qt_app, copy_item)
    assert controller.hasTextLayerClipboard is True, (
        "a Copy Text kattintás nem töltötte fel a szövegréteg-vágólapot"
    )

    _kijelol(window, qt_app, [1])
    edit_menu = _megnyit(menu_bar, qt_app, "&Edit")
    copy_item = _menutetel(edit_menu, "menuEditCopyText")
    paste_item = _menutetel(edit_menu, "menuEditPasteText")
    assert copy_item.property("enabled") is False, (
        "a réteg nélküli célképnél a Copy Text kattintható"
    )
    assert paste_item.property("enabled") is True, (
        "a másolt Text-réteggel a Paste Text szürke"
    )
    _kattints(qt_app, paste_item)

    assert _varj(
        qt_app,
        lambda: (_ini_szakasz(controller, 1) or {}).get("text") == value,
    ), "a Paste Text nem másolta át a Text-réteget a másik kijelölt képre"
    assert (_ini_szakasz(controller, 1) or {}).get("textactive") == "1"
    assert controller.photos.captionAt(1) == "", (
        "a Text-réteg beillesztése a képfeliratot is módosította"
    )
