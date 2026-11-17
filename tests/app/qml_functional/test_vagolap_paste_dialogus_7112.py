"""#7112: a Paste kérdései a felületen, valódi kattintásokkal."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest


def _varj(qt_app, feltetel, masodperc=10):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(feltetel())


def _gyerek(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem épült fel"
    return elem


def _kattints(window, qt_app, nev):
    elem = _gyerek(window, nev)
    kozep = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _keresd_a_dialogust(window, qt_app, object_name):
    def megvan_es_latszik():
        dialog = window.findChild(QObject, object_name)
        return dialog is not None and dialog.property("visible") is True

    assert _varj(qt_app, megvan_es_latszik), f"{object_name} nem lett látható"
    dialog = window.findChild(QObject, object_name)
    return dialog


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_paste_megerosites_es_utkozesvalaszok_valodi_kattintassal(
    qml_app, qt_app, tmp_path, magassag_elteres
):
    window, _controller, engine = qml_app
    window.setHeight(window.height() + magassag_elteres)
    qt_app.processEvents()
    fileops = engine.rootContext().contextProperty("fileOpsController")

    forras = tmp_path / "forras"
    cel = tmp_path / "cel"
    forras.mkdir()
    cel.mkdir()

    # Elvetéskor sem a konfliktusmentes fájl, sem az ütköző fájl ne változzon.
    elvetendo = forras / "elvetendo.jpg"
    elvetendo.write_bytes(b"eredeti")
    fileops.clipboardPasteConfirmationRequested.emit(
        [str(elvetendo)], str(cel), "copy"
    )
    megerosito = _keresd_a_dialogust(window, qt_app, "pasteConfirmDialog")
    assert megerosito.property("title") == "Confirm Copy"
    assert _gyerek(window, "pasteConfirmAcceptButton").property("text") == "Copy Files"
    _kattints(window, qt_app, "pasteConfirmCancelButton")
    assert not (cel / elvetendo.name).exists()
    assert elvetendo.read_bytes() == b"eredeti"

    # Jóváhagyott, ütközésmentes másolás után a célfájl ténylegesen létrejön.
    masolando = forras / "masolando.jpg"
    masolando.write_bytes(b"masolat")
    fileops.clipboardPasteConfirmationRequested.emit(
        [str(masolando)], str(cel), "copy"
    )
    _keresd_a_dialogust(window, qt_app, "pasteConfirmDialog")
    _kattints(window, qt_app, "pasteConfirmAcceptButton")
    assert _varj(qt_app, lambda: (cel / masolando.name).exists())
    assert (cel / masolando.name).read_bytes() == b"masolat"

    # A Kivágás ugyanazt a másik mappás kérdést használja, de mozgatási
    # címmel és gombbal; jóváhagyva a forrásból a célba kerül a fájl.
    cel_mozgatas = tmp_path / "cel-mozgatas"
    cel_mozgatas.mkdir()
    mozgatando = forras / "mozgatando.jpg"
    mozgatando.write_bytes(b"mozgatott")
    fileops.clipboardPasteConfirmationRequested.emit(
        [str(mozgatando)], str(cel_mozgatas), "cut"
    )
    megerosito = _keresd_a_dialogust(window, qt_app, "pasteConfirmDialog")
    assert megerosito.property("title") == "Confirm Move"
    assert _gyerek(window, "pasteConfirmAcceptButton").property("text") == "Move Files"
    _kattints(window, qt_app, "pasteConfirmAcceptButton")
    celre_mozgatott = cel_mozgatas / mozgatando.name
    assert _varj(qt_app, lambda: celre_mozgatott.exists() and not mozgatando.exists())
    assert celre_mozgatott.read_bytes() == b"mozgatott"

    # Ütközésenként a három eredeti választ valódi gombnyomás oldja fel.
    valaszok = (
        ("atnevez", "duplicateRenameButton"),
        ("kihagy", "duplicateSkipButton"),
        ("megse", "duplicateCancelButton"),
    )
    for nev, gomb in valaszok:
        src = forras / f"{nev}.jpg"
        target = cel / src.name
        src.write_bytes(f"forras-{nev}".encode())
        target.write_bytes(f"cel-{nev}".encode())
        fileops.clipboardPasteConfirmationRequested.emit([str(src)], str(cel), "copy")
        _keresd_a_dialogust(window, qt_app, "pasteConfirmDialog")
        _kattints(window, qt_app, "pasteConfirmAcceptButton")
        _keresd_a_dialogust(window, qt_app, "duplicateNamesDialog")
        _kattints(window, qt_app, gomb)
        assert _varj(
            qt_app,
            lambda: window.findChild(QObject, "duplicateNamesDialog") is None
            or window.findChild(QObject, "duplicateNamesDialog").property("visible") is False,
        )
        assert target.read_bytes() == f"cel-{nev}".encode()
        if nev == "atnevez":
            assert len(list(cel.glob("atnevez*"))) == 2
        else:
            assert len(list(cel.glob(f"{nev}*"))) == 1

    # Albumcélon a MainWindowCommands nem kéri az eltérő mappa megerősítését,
    # és (#7142) fájlt sem másol: az album tagságát bővíti (a részletes
    # próbák: `test_album_beillesztes_7142.py`). A könyvtáron kívüli fájl a
    # korábbi mappába sem kerül át.
    album_forras = tmp_path / "album-forras"
    album_forras.mkdir()
    album_kep = album_forras / "album-cel.jpg"
    album_kep.write_bytes(b"album-masolat")
    _controller.showAlbum("7112-test-album")
    fileops.copyFilesToClipboard([str(album_kep)])
    commands = _gyerek(window, "mainWindowCommands")
    assert QMetaObject.invokeMethod(commands, "beillesztAVagolaprol")
    qt_app.processEvents()
    assert not (Path(_controller.currentFolder) / album_kep.name).exists()
    paste_dialog = window.findChild(QObject, "pasteConfirmDialog")
    assert paste_dialog is None or paste_dialog.property("visible") is False
