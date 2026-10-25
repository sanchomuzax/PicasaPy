"""#5861: a Revert alapból Mégse legyen, Enterre se dobja el a mentést."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QSignalSpy, QTest

from support.jpeg_factory import make_minta_jpeg
from support.qt_wait import wait_for_signal
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import szures
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    kattints,
    vizualis_bejaras,
)
from tests.support.varakozas import var_feltetelre

_ABLAKMAGASSAG_ELTERESEK = (-5, 0, 5)


@pytest.fixture
def revert_app(qt_app, tmp_path):
    """Mintás fotó valódi bélyegképpel, izolált tesztkönyvtárban."""

    def kepeket(lib: Path) -> None:
        make_minta_jpeg(lib / "a.jpg", size=(640, 480), seed=5861)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, masodperc), uzenet


def _kepkesz(window) -> bool:
    for item in vizualis_bejaras(window.contentItem()):
        if item.objectName() != "thumbImage" or not item.property("source"):
            continue
        expression = QQmlExpression(
            qmlContext(item), item, "status === Image.Ready"
        )
        ready, error = expression.evaluate()
        if not error and ready:
            return True
    return False


def _gombok(dialog) -> list[str]:
    footer = dialog.property("footer")
    assert footer is not None, "a Visszaállítás párbeszédnek nincs gombsora"
    nevek = {"revertOkButton", "revertUndoSaveButton", "revertCancelButton"}
    helyek = []
    for item in vizualis_bejaras(footer):
        if item.objectName() in nevek and item.isVisible():
            x = item.mapToScene(QPointF(0, 0)).x()
            helyek.append((x, item.objectName()))
    return [name for _x, name in sorted(helyek)]


def _kerdes_szovege(dialog) -> str:
    tartalom = dialog.property("contentItem")
    for item in vizualis_bejaras(tartalom):
        text = item.property("text")
        if text in (
            "Revert to original version of file?",
            "Revert to original version of these file(s)?",
        ):
            return text
    raise AssertionError("a Revert kérdéssora nem található")


def _kepernyokep(window, tmp_path: Path, offset: int) -> None:
    if offset != 0:
        return
    megadott = os.environ.get("PICASAPY_5861_SCREENSHOT", "")
    cel = Path(megadott) if megadott else tmp_path / "revert-confirm-5861.png"
    cel.parent.mkdir(parents=True, exist_ok=True)
    kep = window.grabWindow()
    assert not kep.isNull(), "üres lett a Revert párbeszéd képe"
    assert kep.save(str(cel)), f"nem menthető a Revert párbeszéd képe: {cel}"


@pytest.mark.parametrize("magassag_elteres", _ABLAKMAGASSAG_ELTERESEK)
def test_revert_enter_cancel_es_a_parbeszed_egykepes_kinézete(
    revert_app, qt_app, tmp_path, magassag_elteres
):
    window, controller, _engine = revert_app
    celmagassag = window.height() + magassag_elteres
    window.setHeight(celmagassag)
    _varj(
        qt_app,
        lambda: window.height() == celmagassag,
        "a főablak nem vette fel a kért magasságot",
    )

    _varj(qt_app, lambda: _kepkesz(window), "a valódi bélyegkép nem töltődött be")
    thumb = next(
        item for item in vizualis_bejaras(window.contentItem())
        if item.objectName() == "thumbMouseArea"
    )
    kattints(window, qt_app, thumb)
    kijeloles = window.property("selectedIndexes").toVariant()
    assert kijeloles == [0], f"a valódi bélyegkép nem jelölődött ki: {kijeloles!r}"

    photo = Path(str(controller.photos.filePathAt(0)))
    eredeti = photo.read_bytes()
    billentyu = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
    QTest.keyClick(window, Qt.Key.Key_B, billentyu)
    qt_app.processEvents()
    _varj(
        qt_app,
        lambda: "bw=1;" in szures(controller, 0),
        "a kijelölt képen nem jött létre szerkesztés",
    )

    wait_for_signal(
        controller.saveFinished,
        lambda: controller.saveRowsToDisk([0]),
        description="a tesztkép mentése a visszaállítás előtt",
        process_events_with=qt_app,
    )
    assert controller.hasSavedBackup([0]) is True, "a kép mentése nem hozott létre másolatot"
    mentett_kep = photo.read_bytes()
    assert mentett_kep != eredeti, "a próbakép mentés után nem változott"
    ini = photo.parent / ".picasa.ini"
    mentett_ini = ini.read_bytes()

    window.requestActivate()
    _varj(qt_app, lambda: window.isActive(), "a főablak nem aktiválódott")
    menu_bar = window.property("menuBar")
    _megnyit(menu_bar, qt_app, "&File")
    revert_menu = window.findChild(QObject, "menuFileRevert")
    assert revert_menu is not None and revert_menu.property("enabled") is True
    kattints(window, qt_app, revert_menu)

    dialog = window.findChild(QObject, "revertConfirmDialog")
    _varj(
        qt_app,
        lambda: dialog is not None and dialog.property("opened") is True,
        "a Fájl ▸ Revert nem nyitotta meg a megerősítést",
    )
    cancel = window.findChild(QObject, "revertCancelButton")
    assert cancel is not None
    cancel_focused = cancel.property("activeFocus") is True
    gombok = _gombok(dialog)
    kerdes = _kerdes_szovege(dialog)
    _kepernyokep(window, tmp_path, magassag_elteres)

    revert_spy = QSignalSpy(controller.revertFinished)
    QTest.keyClick(window, Qt.Key.Key_Return)
    _varj(
        qt_app,
        lambda: dialog.property("opened") is False,
        "az Enter nem zárta be a Revert párbeszédet",
    )
    _varj(
        qt_app,
        lambda: revert_spy.count() > 0
        or not controller.property("saveProgressActive"),
        "az Enter utáni lemezművelet nem állt be nyugalmi állapotba",
    )
    kep_valtozatlan = photo.read_bytes() == mentett_kep
    ini_valtozatlan = ini.read_bytes() == mentett_ini

    megfigyelt = {
        "cancel_focus": cancel_focused,
        "button_order": gombok,
        "single_photo_question": kerdes,
        "dialog_closed_by_enter": dialog.property("opened") is False,
        "photo_bytes_unchanged": kep_valtozatlan,
        "ini_bytes_unchanged": ini_valtozatlan,
    }
    assert megfigyelt == {
        "cancel_focus": True,
        "button_order": ["revertOkButton", "revertUndoSaveButton", "revertCancelButton"],
        "single_photo_question": "Revert to original version of file?",
        "dialog_closed_by_enter": True,
        "photo_bytes_unchanged": True,
        "ini_bytes_unchanged": True,
    }, f"a Visszaállítás megerősítő eltér a kért biztonságos működéstől: {megfigyelt!r}"
