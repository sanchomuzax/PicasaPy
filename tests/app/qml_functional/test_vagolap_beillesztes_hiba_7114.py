"""#7114: a vágólapos Beillesztés megállása a VALÓDI ablakon (renderelt QML).

A „Kész, ha": három képből a második írási hibájánál az első másolat megmarad,
a második hibás állapotú, a harmadik nem keletkezik; EGY összegző jelzés
nevezi meg a hibát.

A vezérlő-szintű mérés (`tests/app/test_vagolap_koteg_leall_7114.py`)
a jelzés ADATÁT méri. Ez a fájl a KÉPERNYŐT: a Szerkesztés ▸ Beillesztés
parancs (`beillesztAVagolaprol`) a valódi főablakból fut, és az összegző
párbeszéd tényleg megnyílik, látható szöveggel, ami a hibás képet és az okot
megnevezi. A párbeszéd a lemezen álló fájlokkal együtt kerül ellenőrzésre,
hogy a felület ne mondhasson mást, mint ami a mappában van.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import (
    QByteArray,
    QMetaObject,
    QMimeData,
    QObject,
    QPoint,
    QPointF,
    Qt,
    QUrl,
)
from PySide6.QtTest import QTest

from picasapy.fileops import copy as copy_module

_GNOME = "x-special/gnome-copied-files"


def _mime(utak, muvelet: str) -> QMimeData:
    adat = QMimeData()
    urlek = [QUrl.fromLocalFile(str(u)) for u in utak]
    adat.setUrls(urlek)
    sorok = [muvelet, *(u.toString() for u in urlek)]
    adat.setData(_GNOME, QByteArray("\n".join(sorok).encode("utf-8")))
    return adat


def _varj(qt_app, feltetel, masodperc=10):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(feltetel())


def _kattints(window, qt_app, object_name):
    elem = window.findChild(QObject, object_name)
    assert elem is not None, f"{object_name} nem épült fel"
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


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_a_beillesztes_hibaja_az_osszegzo_parbeszeden_latszik(
    qml_app, qt_app, tmp_path, monkeypatch, magassag_elteres
):
    window, controller, engine = qml_app
    window.setHeight(window.height() + magassag_elteres)
    qt_app.processEvents()
    fileops = engine.rootContext().contextProperty("fileOpsController")
    assert fileops is not None

    forras, cel = tmp_path / "forras-7114", tmp_path / "cel-7114"
    forras.mkdir()
    cel.mkdir()
    kepek = []
    for nev in ("a.jpg", "b.jpg", "c.jpg"):
        kep = forras / nev
        kep.write_bytes(nev.encode())
        kepek.append(kep)

    # A második kép képfájlja MÁR lemezen van, de a megőrzött eredetije nem
    # másolható: a `copy_photo` a fél másolatot visszavonja (hibás állapot).
    # A hibát a `copy` modul saját fogantyúján injektáljuk (#1375).
    eredeti = copy_module.copy_preserved_originals

    def copy_preserved_originals(source, target):
        if Path(source).name == "b.jpg":
            raise OSError(28, "No space left on device")
        return eredeti(source, target)

    monkeypatch.setattr(copy_module, "copy_preserved_originals", copy_preserved_originals)
    monkeypatch.setattr(fileops, "_vagolap_adata", lambda: _mime(kepek, "copy"))
    controller._current_folder = str(cel)

    QMetaObject.invokeMethod(window, "beillesztAVagolaprol", Qt.ConnectionType.DirectConnection)
    megerosito = window.findChild(QObject, "pasteConfirmDialog")
    assert _varj(
        qt_app,
        lambda: megerosito is not None and megerosito.property("visible") is True,
    ), "az eltérő mappás Paste nem kért jóváhagyást"
    accept = window.findChild(QObject, "pasteConfirmAcceptButton")
    assert accept is not None and accept.property("text") == "Copy Files"
    _kattints(window, qt_app, "pasteConfirmAcceptButton")

    parbeszed = window.findChild(QObject, "batchSummaryDialog")
    assert _varj(
        qt_app,
        lambda: parbeszed is not None and parbeszed.property("visible") is True,
    ), "a jóváhagyás utáni köteg nem nyitotta meg az összegzést"
    assert (cel / "a.jpg").read_bytes() == b"a.jpg", "az első másolat nem maradt meg"
    assert not (cel / "b.jpg").exists(), "a hibás képből félkész példány maradt"
    assert not (cel / "c.jpg").exists(), "a hiba után a harmadik kép is elindult"

    assert parbeszed.property("visible") is True, "az összegző jelzés nem jelent meg"
    uzenet = parbeszed.property("message")
    assert "b.jpg" in uzenet, "a jelzés nem nevezi meg a hibás képet"
    assert "No space left" in uzenet, "a jelzés nem nevezi meg a hiba okát"
    assert "a.jpg" not in uzenet and "c.jpg" not in uzenet, (
        "a jelzés a nem hibás képeket is hibásnak mutatja"
    )
