"""#3573 — ahol az eredeti üzenet NEVET vagy LISTÁT mond, a felépült
párbeszéd is azt mutatja.

A `test_hivatalos_feliratok_3573.py` a `.ts`-t és a `.qm`-et nézi; az
viszont nem látja, hogy a QML a helyére teszi-e a képnevet
(`IDS_CONFIRM_REDEYE_REVERT`) és a hibás fájlok listáját
(`CThumbUI::GetBadImages` + lista + `GetBadImages2`). Ez a fájl a valódi
`Main.qml`-ben építi fel a két párbeszédet, és a megjelenő szöveget olvassa.

Amit NEM mér: a magyar fordítást (a próba-ablak angolul fut) és a
tördelés képi megjelenését.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt
from PySide6.QtTest import QTest


def _felepit(window, burok: str) -> None:
    loader = window.findChild(QObject, burok)
    assert loader is not None, burok
    QMetaObject.invokeMethod(loader, "ensure", Qt.ConnectionType.DirectConnection)


def test_a_vorosszem_figyelmeztetes_a_kep_nevet_mondja(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    lib = tmp_path / "kepek"
    (lib / ".picasa.ini").write_text(
        "[b.jpg]\nfilters=redeye=1,333333334ccd4ccd;\n", encoding="utf-8")
    controller.selectFolder(str(lib))
    qt_app.processEvents()
    sorok = list(range(controller.photos.rowCount()))
    assert len(sorok) == 2

    _felepit(window, "undoAllEditsDialogLoader")
    qt_app.processEvents()
    dialog = window.findChild(QObject, "undoAllEditsDialog")
    assert dialog is not None
    QMetaObject.invokeMethod(
        dialog, "openFor", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", sorok))
    qt_app.processEvents()

    szoveg = window.findChild(QObject, "undoAllEditsMessageLabel").property("text")
    assert (
        "Red eye fixes have been applied to b.jpg.\nIf you remove all edits, "
        "your red eye fixes cannot be recovered with redo. \nAre you sure "
        "you want to remove the fixes forever?"
    ) in szoveg, szoveg
    assert "a.jpg" not in szoveg, "csak a vörösszemes kép neve kell"


def test_a_serult_fajl_uzenet_soronkent_listazza_a_fajlokat(qml_app, qt_app):
    window, controller, _engine = qml_app
    _felepit(window, "brokenPhotoDialogLoader")
    qt_app.processEvents()

    controller.brokenPhotosDetected.emit(
        [{"id": 1, "name": "a.jpg"}, {"id": 2, "name": "b.jpg"}])
    # a valódi út: az összegyűjtő időzítő (400 ms) lejár, és az nyitja meg
    QTest.qWait(700)
    qt_app.processEvents()

    szoveg = window.findChild(QObject, "brokenPhotoMessageLabel").property("text")
    assert szoveg == (
        "Picasa had a problem loading this file(s)\na.jpg\nb.jpg"
        "\nWould you like to hide the files on disk?"
    ), szoveg
