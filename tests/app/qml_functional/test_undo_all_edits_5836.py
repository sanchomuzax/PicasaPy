"""Az Undo All Edits megerősítése és ini-hatása a job-254 mérése szerint (#5836).

A teljes programot és a Kép menü valódi kattintását használja. A főmenü és a
kép helyi menüje könyvtárnézetben egyaránt a mért többes szöveget mutatja,
akkor is, ha egyetlen kép van kijelölve. A teszt az ablakmagasságot ±5 px-szel
eltolja, a kattintási helyeket pedig a felépült QML-elemekből számolja.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlExpression, qmlContext

from picasapy.ini import load_document
from picasapy.scanner import PICASA_INI_NAME
from support.qt_wait import wait_for_photo_op
from support.jpeg_factory import make_minta_jpeg
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    elokeszit,
    gyerek,
    nyitott,
    tetel_kattintasa,
    varj,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    jobbklikk_fotón,
    kattints,
)
from tests.app.qml_functional.conftest import _build_qml_app


def _keszits_fotokat(lib: Path) -> None:
    fotok = lib / "fotok"
    fotok.mkdir()
    for index, nev in enumerate(("a_nagy.jpg", "b_kicsi.jpg", "c_kozepes.jpg")):
        make_minta_jpeg(fotok / nev, size=(640, 480), seed=index + 1)


def _vizualis_bejaras(item):
    for elem in item.childItems():
        yield elem
        yield from _vizualis_bejaras(elem)


def _valodi_belyegkepek_keszek(window) -> bool:
    kepek = [
        elem
        for elem in _vizualis_bejaras(window.contentItem())
        if elem.objectName() == "thumbImage"
        and elem.property("source")
        and elem.isVisible()
    ]
    if len(kepek) < 3:
        return False
    for elem in kepek:
        expression = QQmlExpression(qmlContext(elem), elem, "status === Image.Ready")
        value, error = expression.evaluate()
        if error or not value:
            return False
    return True


@pytest.fixture
def mappa_kep_app(qt_app, tmp_path):
    generator = _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_fotokat,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )
    window, controller, engine = next(generator)
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    yield window, controller, engine
    del menu_bar
    next(generator, None)


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
@pytest.mark.parametrize("entry_point", ["picture_menu", "photo_context_menu"])
def test_konyvtari_undo_all_edits_megerositi_es_backuphash_t_hagy(
    mappa_kep_app, qt_app, tmp_path, height_delta, entry_point
):
    window, controller, _engine = mappa_kep_app
    elokeszit(window, qt_app, controller)
    assert varj(qt_app, lambda: _valodi_belyegkepek_keszek(window)), (
        "a valódi bélyegkép-szolgáltató nem töltötte be mindhárom fotót"
    )
    initial_height = window.height()
    window.setHeight(initial_height + height_delta)
    assert varj(qt_app, lambda: window.height() == initial_height + height_delta)

    wait_for_photo_op(
        controller,
        lambda: controller.applyEffectMany([0], "sepia"),
        qt_app=qt_app,
    )
    assert varj(qt_app, lambda: "sepia=1;" in load_document(
        Path(controller.photos.photos[0].folder_path) / PICASA_INI_NAME
    ).section(controller.photos.photos[0].name).get("filters"))

    if entry_point == "picture_menu":
        tetel_kattintasa(window, qt_app, "&Picture", "menuPictureUndoAllEdits")
    else:
        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuUndoAllEdits"))

    dialog = gyerek(window, "undoAllEditsDialog")
    assert varj(qt_app, lambda: nyitott(dialog)), "a megerősítő párbeszéd nem nyílt meg"
    assert dialog.property("title") == "Confirm"
    assert gyerek(window, "undoAllEditsMessageLabel").property("text") == (
        "This will remove all edits you have made to ALL of the selected pictures.  "
        "Do you want to continue?"
    )
    assert gyerek(window, "undoAllEditsYesButton").property("text") == "Remove Edits"
    assert gyerek(window, "undoAllEditsNoButton").property("text") == "No"
    assert window.findChild(QObject, "undoAllEditsRememberCheck") is None
    assert window.findChild(QObject, "undoAllEditsCancelButton") is None

    if height_delta == 0 and entry_point == "picture_menu":
        screenshot = tmp_path / "undo-all-edits-5836.png"
        assert window.grabWindow().save(str(screenshot), "PNG"), (
            f"a valódi bélyegképeket és megerősítőt tartalmazó kép nem menthető: {screenshot}"
        )

    wait_for_photo_op(
        controller,
        lambda: kattints(window, qt_app, gyerek(window, "undoAllEditsYesButton")),
        qt_app=qt_app,
    )
    foto = controller.photos.photos[0]
    section = load_document(Path(foto.folder_path) / PICASA_INI_NAME).section(foto.name)
    assert section is not None, "a törölt lánc után a képszakasz hiányzik"
    values = dict(section.items())
    assert set(values) == {"backuphash"}, values
    assert values["backuphash"].isdecimal()
    assert 0 <= int(values["backuphash"]) <= 0xFFFF
