"""#4578: a Keywords párbeszéd valódi kattintással, a főablakban."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pytest
from PySide6.QtCore import QElapsedTimer, QObject, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QSignalSpy, QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import load_document, update_document


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(root, name: str):
    found = root.findChild(QObject, name)
    if found is not None:
        return found
    visual_root = root.contentItem() if hasattr(root, "contentItem") else root
    if hasattr(visual_root, "childItems"):
        for item in _walk(visual_root):
            if item.objectName() == name:
                return item
    assert found is not None, f"A kirajzolt felületen nincs ilyen elem: {name}"


def _click(window, item, qt_app):
    assert item.width() > 0 and item.height() > 0, "a kattintási cél mérete nulla"
    point = item.mapToScene(item.boundingRect().center()).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
    qt_app.processEvents()


def _wait_for(qt_app, predicate, timeout_ms: int = 3000) -> bool:
    timer = QElapsedTimer()
    timer.start()
    while timer.elapsed() < timeout_ms:
        qt_app.processEvents()
        if predicate():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(predicate())


def _wait_for_next_frame(window, qt_app) -> None:
    rendered = QSignalSpy(window.frameSwapped)
    window.requestUpdate()
    assert _wait_for(qt_app, lambda: rendered.count() > 0), (
        "a QML ablak nem rajzolt új képkockát"
    )


def _as_list(value):
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return list(value or [])


def _status_date(text: str) -> str:
    parts = str(text).split("   ")
    assert len(parts) >= 3, f"az állapotsorból hiányzik a dátum: {text!r}"
    return parts[1]


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_cimkek_parbeszed_kattintassal_megjelenit_es_ini_be_ir(
    qml_app_szines_belyegkep, qt_app, magassag_eltolas
):
    window, controller, _engine = qml_app_szines_belyegkep
    library = Path(controller._roots[0])
    png = Path(library) / "c.png"
    image = QImage(96, 64, QImage.Format.Format_RGB32)
    image.fill(QColor("#477da5"))
    assert image.save(str(png), "PNG")
    png_timestamp = datetime(2099, 2, 3, 4, 5, 6).timestamp()
    update_document(
        Path(library) / ".picasa.ini",
        lambda document: document.with_value(
            "c.png", "keywords", "kezdő címke"
        ),
        backup=False,
    )
    os.utime(png, (png_timestamp, png_timestamp))

    with open_index(controller._db_path) as conn:
        sync_tree(conn, str(library))
    controller._reload()
    controller.selectFolder(str(library))
    assert _wait_for(qt_app, lambda: controller.photos.rowCount() == 3)

    row = next(
        index
        for index in range(controller.photos.rowCount())
        # útvonalként hasonlítunk: Windowson a modell `/`-es alakot ad (#4831)
        if Path(controller.photos.filePathAt(index)) == png
    )
    png_bytes_before = png.read_bytes()
    window.setHeight(int(window.height()) + magassag_eltolas)
    window.setProperty("selectedIndexes", [row])
    window.setProperty("selectedIndex", row)
    window.setProperty("activeDrawerTab", "properties")
    assert _wait_for(
        qt_app,
        lambda: window.findChild(QObject, "editKeywordsButton") is not None,
    )

    panel = window.findChild(QObject, "propertiesPanel")
    assert panel is not None and panel.isVisible()
    edit_button = _item(panel, "editKeywordsButton")
    assert edit_button.isVisible() and edit_button.isEnabled()
    _click(window, edit_button, qt_app)
    dialog = _item(panel, "keywordsDialog")
    assert _wait_for(qt_app, lambda: bool(dialog.property("visible")))
    info_bar = _item(window, "trayInfoText")
    kezdo_status = str(info_bar.property("nyersSzoveg"))
    kezdo_datum = _status_date(kezdo_status)
    assert "2099" in kezdo_datum

    assert dialog.property("photoName") == "c.png"
    assert dialog.property("tags") == ["kezdő címke"]
    thumbnail = _item(dialog, "keywordPhotoThumbnail")
    assert thumbnail.property("source") == controller.photos.itemAt(row)["thumbUrl"]
    assert _wait_for(qt_app, lambda: dialog.property("thumbnailReady"))

    # A program saját, kirajzolt geometriája a mérce; nincs beégetett Pi-
    # ablakszám. A két középpontot legfeljebb 3 px választja el.
    dialog_x = float(dialog.property("x"))
    dialog_y = float(dialog.property("y"))
    dialog_width = float(dialog.property("width"))
    dialog_height = float(dialog.property("height"))
    assert abs(dialog_x + dialog_width / 2 - window.width() / 2) <= 3
    assert abs(dialog_y + dialog_height / 2 - window.height() / 2) <= 3
    assert dialog_x >= -3 and dialog_y >= -3
    assert dialog_x + dialog_width <= window.width() + 3
    assert dialog_y + dialog_height <= window.height() + 3

    _click(window, _item(window, "keywordListRow0"), qt_app)
    _click(window, _item(dialog, "keywordRemoveButton"), qt_app)
    assert _wait_for(qt_app, lambda: _as_list(dialog.property("tags")) == [])
    section = load_document(Path(library) / ".picasa.ini").section("c.png")
    assert section is None or section.get("keywords") is None

    add_field = _item(dialog, "keywordAddField")
    add_field.setProperty("text", "új címke")
    qt_app.processEvents()
    _click(window, _item(dialog, "keywordAddButton"), qt_app)
    assert _wait_for(
        qt_app, lambda: _as_list(dialog.property("tags")) == ["új címke"]
    )
    assert load_document(Path(library) / ".picasa.ini").section("c.png").get(
        "keywords"
    ) == "új címke"
    assert png.read_bytes() == png_bytes_before, "a címkézés átírta a PNG bájtjait"
    # #2491: az ini-írás a képfájl mtime-ját szándékosan frissíti (a futó
    # Picasa értesítése) — a PNG tartalma viszont változatlan marad.
    assert "2099" in str(dialog.property("dateText")), (
        "az EXIF nélküli PNG befagyasztott fájldátuma hiányzik a párbeszédből"
    )

    property_list = _item(panel, "propertyList")

    def rendered_property_values():
        return [
            item.property("text")
            for item in _walk(property_list)
            if item.property("text") is not None
        ]

    # A lista JS-tömb modellből épül: a címke változásakor MINDEN delegált
    # újra létrejön, a következő elrendezési körben. Azonnali olvasásnál a
    # CI-n csak az első két delegált volt kész (main CI 38048260650, #4827).
    tulajdonsag_felfrissult = _wait_for(
        qt_app, lambda: "új címke" in rendered_property_values()
    )
    tray_bar = _item(window, "trayBar")
    hianyok = []
    if not tulajdonsag_felfrissult:
        hianyok.append(f"Tulajdonságok mezők: {rendered_property_values()!r}")
    status_felfrissult = _wait_for(
        qt_app,
        lambda: "új címke" in str(info_bar.property("text")),
    )
    if not status_felfrissult:
        hianyok.append(
            "alsó állapotsor: "
            f"{info_bar.property('text')!r}; "
            f"nyers adat: {info_bar.property('nyersSzoveg')!r}; "
            f"modellverzió: {controller.photos.revision}; "
            f"sávverzió: {tray_bar.property('photoRevision')}; "
            f"kijelölés: {window.property('selectedIndex')!r}/"
            f"{window.property('selectedIndexes')!r}; "
            f"fotoInfo: {controller.photoInfo(row)!r}; "
            f"rekord-címke: {controller.photos.itemAt(row)['keywords']!r}; "
            f"tálca: {tray_bar.property('trayCount')}/"
            f"{tray_bar.property('trayInfoText')!r}"
        )
    assert not hianyok, "; ".join(hianyok)

    if magassag_eltolas == 0:
        _wait_for_next_frame(window, qt_app)
        screenshot = window.grabWindow()
        cel = Path(__file__).resolve().parents[3] / ".bt" / "4578-keywords-dialog.png"
        cel.parent.mkdir(parents=True, exist_ok=True)
        assert screenshot.save(str(cel), "PNG")

    _click(window, _item(dialog, "keywordDoneButton"), qt_app)
    assert _wait_for(qt_app, lambda: not dialog.property("visible"))


def test_a_textfield_helyi_menuje_megmarad_a_forrasban():
    qml = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml/PicasaPy/KeywordsDialog.qml"
    assert qml.exists(), "a KeywordsDialog QML-komponens hiányzik"
    source = qml.read_text(encoding="utf-8")
    assert "TextFieldContextArea {}" in source
    assert 'text: qsTr("Tags:")' in source
    assert "font.pixelSize: Theme.fontSize" in source
    assert "font.pixelSize: Theme.fontSize - 1" in source
