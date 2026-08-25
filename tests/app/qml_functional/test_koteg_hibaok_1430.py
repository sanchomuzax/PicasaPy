"""#1430: a kötegelt áthelyezés BUKÁSÁNAK OKA jusson el a felhasználóig.

A felületen a „Move to Folder…" MINDIG a kötegelt úton megy (`Main.qml` →
`openMove` → `startBatch("move")` → `movePhotos`), egyetlen kijelölt képnél
is; az egyfájlos `movePhoto` slotnak nincs QML-hívója. A köteg viszont eddig
csak DARABSZÁMOT jelentett („1 fájlt nem sikerült feldolgozni"), az okot a
`BatchResult.failed` szövegéből eldobta.

Emiatt a megőrzött eredeti ütközéséről szóló, magyarázó üzenet (#1430) az
áthelyezésnél a semmibe ment — pontosan az a néma elutasítás, amit az
`originals.py` fejléce (#1003, #1207, #1213) kizárni ígér.

Ez a fájl a VALÓDI kötést méri: a vezérlő `batchFinished` jelzését a
`FileOpsDialogs.qml` fogadja, és a `batchSummaryDialog.message`-be teszi.
"""

from __future__ import annotations

from PySide6.QtCore import QObject

from picasapy.edit import ORIGINALS_DIR_NAME


def _kep(mappa, nev: str, tartalom: bytes = b"kep") -> object:
    mappa.mkdir(parents=True, exist_ok=True)
    ut = mappa / nev
    ut.write_bytes(tartalom)
    return ut


def _eredeti(mappa, nev: str, tartalom: bytes) -> None:
    konyvtar = mappa / ORIGINALS_DIR_NAME
    konyvtar.mkdir(parents=True, exist_ok=True)
    (konyvtar / nev).write_bytes(tartalom)


def test_a_koteg_hibaoka_megjelenik_az_osszegzo_parbeszeden(qml_app, tmp_path):
    window, _controller, engine = qml_app
    fileops = engine.rootContext().contextProperty("fileOpsController")
    assert fileops is not None

    forras = tmp_path / "forras-1430"
    cel = tmp_path / "cel-1430"
    cel.mkdir(parents=True, exist_ok=True)
    kep = _kep(forras, "a.jpg")
    # a képnek van pillanatképe, a célban viszont ugyanaz a hely foglalt egy
    # ÉLŐ kép eredetijével — a köteg ezen bukik el
    _eredeti(forras, "a.1.jpg", b"pillanatkep")
    _kep(cel, "a.1.jpg", b"masik-elo-kep")
    _eredeti(cel, "a.1.jpg", b"masik-kep-eredetije")

    fileops.movePhotos([str(kep)], str(cel), "rename")

    parbeszed = window.findChild(QObject, "batchSummaryDialog")
    assert parbeszed is not None
    uzenet = parbeszed.property("message")

    assert "a.jpg" in uzenet, "a felhasználó nem tudja meg, MELYIK fájl bukott"
    assert "eredeti" in uzenet.lower(), "az OK nem jut el a felhasználóig"
    assert kep.exists(), "a kép nem maradt a helyén"
