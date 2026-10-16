"""#4440: a mentés-család QML-kattintása után a nézet frissül vagy a hiba látszik."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QPointF, Qt, QTimer
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.app import save_controller as save_controller_module
from picasapy.index import open_index, sync_tree
from picasapy.ini import update_document
from support.qt_wait import hangos_hurok


_MAGASSAG_ELTOLASOK = (-5, 0, 5)


def _vár(qt_app, feltétel, másodperc=3):
    határ = time.monotonic() + másodperc
    while not feltétel():
        if time.monotonic() >= határ:
            return False
        ébresztő = QEventLoop()
        QTimer.singleShot(50, ébresztő.quit)
        ébresztő.exec()
        qt_app.processEvents()
    return True


def _elem(gyökér, név):
    elem = gyökér.findChild(QQuickItem, név)
    assert elem is not None, f"{név} nem található"
    return elem


def _kattint(elem):
    ablak = elem.window()
    közép = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        közép.toPoint(),
    )


def _vár_magasságot(window, qt_app, alap: int, eltolás: int) -> None:
    várt = alap + eltolás
    window.resize(window.width(), várt)
    assert _vár(qt_app, lambda: window.height() == várt), (
        f"az ablak nem vette fel a {várt} px magasságot"
    )


def _mentes_gomb(dialog):
    gombok = [
        elem for elem in dialog.findChildren(QQuickItem)
        if "Button" in elem.metaObject().className()
        and elem.property("text") in {"Save", "Mentés"}
    ]
    assert gombok, "a mentés párbeszéd valódi Save gombja hiányzik"
    return gombok[0]


def _ini_szuro(path: Path, name: str, value: str | None) -> None:
    def mutate(document):
        if value is None:
            return document.with_removed(name, "filters").with_removed(name, "redo")
        return document.with_value(name, "filters", value, carried=True)

    update_document(path.parent / ".picasa.ini", mutate, backup=False)


def _szuro_szerkesztés(controller, window, qt_app, út: Path) -> QQuickItem:
    _ini_szuro(út, út.name, "bw=1;")
    with open_index(controller._db_path) as conn:
        sync_tree(conn, út.parent)
    controller.selectFolder(str(út.parent))
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    window.setProperty("viewerOpen", True)
    néző = window.findChild(QQuickItem, "photoViewer")
    assert néző is not None
    szerkesztő = néző.property("editCtl")
    assert szerkesztő is not None
    # Az éles alkalmazás az application.py-ban regisztrálja a két aktív
    # szerkesztő-vezérlőt; itt is be kell kötni, hogy a lemezművelet utáni
    # előnézetfrissítés ugyanazt a munkamenetet frissítse.
    controller.set_edit_controllers(szerkesztő)
    néző.setProperty("currentIndex", 0)
    assert _vár(qt_app, lambda: controller.photos.photos[0].filters == "bw=1;")
    kép = _elem(window, "viewerImage")
    assert _vár(qt_app, lambda: kép.property("source") != "")
    return kép


def _alaphelyzet(controller, window, qt_app, út: Path, eredeti: bytes) -> QQuickItem:
    út.write_bytes(eredeti)
    shutil.rmtree(út.parent / ".picasaoriginals", ignore_errors=True)
    shutil.rmtree(út.parent / "Originals", ignore_errors=True)
    _ini_szuro(út, út.name, None)
    return _szuro_szerkesztés(controller, window, qt_app, út)


def _parbeszedek(window):
    loader = window.findChild(QObject, "saveDialogsLoader")
    assert loader is not None
    QMetaObject.invokeMethod(loader, "ensure", Qt.ConnectionType.DirectConnection)
    dialogs = window.findChild(QObject, "saveDialogs")
    assert dialogs is not None
    return dialogs


def _kattint_a_mentesre(window, qt_app):
    dialogs = _parbeszedek(window)
    dialogs.openSave([0])
    párbeszéd = window.findChild(QObject, "saveConfirmDialog")
    assert párbeszéd is not None
    assert _vár(qt_app, lambda: párbeszéd.property("visible"))
    _kattint(_mentes_gomb(párbeszéd))


def _kattint_a_visszaallitasra(window, qt_app, *, undo=False):
    dialogs = _parbeszedek(window)
    dialogs.openRevert([0])
    párbeszéd = window.findChild(QObject, "revertConfirmDialog")
    assert párbeszéd is not None
    assert _vár(qt_app, lambda: párbeszéd.property("visible"))
    gomb = "revertUndoSaveButton" if undo else "revertOkButton"
    _kattint(_elem(párbeszéd, gomb))


def _elokeszit_mentest(controller, qt_app) -> None:
    kész = hangos_hurok(controller.saveFinished, timeout_ms=15000)
    controller.saveRowsToDisk([0])
    kész.exec()
    assert kész.jelzes_argumentumai == (1, 0)
    assert _vár(qt_app, lambda: not controller.photos.photos[0].filters)


def _művelet_vege(controller, qt_app, jelzés, kattintás):
    kész = hangos_hurok(jelzés, timeout_ms=15000)
    kattintás()
    kész.exec()
    qt_app.processEvents()
    assert kész.jelzes_argumentumai == (1, 0) or kész.jelzes_argumentumai == (0, 1)
    return kész.jelzes_argumentumai


def _ujraolvasott_ablakmagassag(window, qt_app) -> int:
    qt_app.processEvents()
    return window.height()


def test_a_save_kattintasa_utan_a_néző_a_mentett_allapotot_mutatja(qml_app, qt_app):
    window, controller, _engine = qml_app
    út = Path(str(controller.photos.filePathAt(0)))
    eredeti = út.read_bytes()
    alapmagasság = _ujraolvasott_ablakmagassag(window, qt_app)

    for eltolás in _MAGASSAG_ELTOLASOK:
        _vár_magasságot(window, qt_app, alapmagasság, eltolás)
        kép = _alaphelyzet(controller, window, qt_app, út, eredeti)
        forrás_előtte = kép.property("source")
        kész = hangos_hurok(controller.saveFinished, timeout_ms=15000)
        _kattint_a_mentesre(window, qt_app)
        kész.exec()

        assert kész.jelzes_argumentumai == (1, 0)
        assert _vár(qt_app, lambda: not controller.photos.photos[0].filters)
        assert kép.property("source") != forrás_előtte

    for eltolás in _MAGASSAG_ELTOLASOK:
        _vár_magasságot(window, qt_app, alapmagasság, eltolás)
        _alaphelyzet(controller, window, qt_app, út, eredeti)
        eredeti_mentes = save_controller_module.save_edited

        def hibas_mentes(*_args, **_kwargs):
            raise OSError("forced disk error for #4440")

        save_controller_module.save_edited = hibas_mentes
        try:
            kész = hangos_hurok(controller.saveFinished, timeout_ms=15000)
            _kattint_a_mentesre(window, qt_app)
            kész.exec()
            assert kész.jelzes_argumentumai == (0, 1)
            hiba = window.findChild(QObject, "saveErrorDialog")
            assert hiba is not None
            assert _vár(qt_app, lambda hiba=hiba: hiba.property("visible"))
            assert "forced disk error" not in hiba.property("message")
            QMetaObject.invokeMethod(hiba, "close")
            assert _vár(qt_app, lambda hiba=hiba: not hiba.property("visible"))
        finally:
            save_controller_module.save_edited = eredeti_mentes


def test_a_revert_kattintasa_siker_es_hiba_utan_is_frissit(qml_app, qt_app):
    window, controller, _engine = qml_app
    út = Path(str(controller.photos.filePathAt(0)))
    eredeti = út.read_bytes()
    alapmagasság = _ujraolvasott_ablakmagassag(window, qt_app)

    for eltolás in _MAGASSAG_ELTOLASOK:
        _vár_magasságot(window, qt_app, alapmagasság, eltolás)
        kép = _alaphelyzet(controller, window, qt_app, út, eredeti)
        _elokeszit_mentest(controller, qt_app)
        _szuro_szerkesztés(controller, window, qt_app, út)
        forrás_előtte = kép.property("source")
        _művelet_vege(
            controller,
            qt_app,
            controller.revertFinished,
            lambda: _kattint_a_visszaallitasra(window, qt_app),
        )
        assert _vár(qt_app, lambda: not controller.photos.photos[0].filters)
        assert kép.property("source") != forrás_előtte

    for eltolás in _MAGASSAG_ELTOLASOK:
        _vár_magasságot(window, qt_app, alapmagasság, eltolás)
        _alaphelyzet(controller, window, qt_app, út, eredeti)
        _elokeszit_mentest(controller, qt_app)
        eredeti_visszaallit = save_controller_module.revert

        def hibas_visszaallit(*_args, **_kwargs):
            raise OSError("forced restore error for #4440")

        save_controller_module.revert = hibas_visszaallit
        try:
            _művelet_vege(
                controller,
                qt_app,
                controller.revertFinished,
                lambda: _kattint_a_visszaallitasra(window, qt_app),
            )
            hiba = window.findChild(QObject, "saveResultDialog")
            assert hiba is not None
            assert _vár(qt_app, lambda hiba=hiba: hiba.property("visible"))
            assert "forced restore error" in hiba.property("message")
            QMetaObject.invokeMethod(hiba, "close")
            assert _vár(qt_app, lambda hiba=hiba: not hiba.property("visible"))
        finally:
            save_controller_module.revert = eredeti_visszaallit


def test_az_undo_save_kattintasa_siker_es_hiba_utan_is_frissit(qml_app, qt_app):
    window, controller, _engine = qml_app
    út = Path(str(controller.photos.filePathAt(0)))
    eredeti = út.read_bytes()
    alapmagasság = _ujraolvasott_ablakmagassag(window, qt_app)

    for eltolás in _MAGASSAG_ELTOLASOK:
        _vár_magasságot(window, qt_app, alapmagasság, eltolás)
        kép = _alaphelyzet(controller, window, qt_app, út, eredeti)
        _elokeszit_mentest(controller, qt_app)
        forrás_előtte = kép.property("source")
        _művelet_vege(
            controller,
            qt_app,
            controller.undoSaveFinished,
            lambda: _kattint_a_visszaallitasra(window, qt_app, undo=True),
        )
        assert _vár(qt_app, lambda: controller.photos.photos[0].filters == "bw=1;")
        assert kép.property("source") != forrás_előtte

    for eltolás in _MAGASSAG_ELTOLASOK:
        _vár_magasságot(window, qt_app, alapmagasság, eltolás)
        _alaphelyzet(controller, window, qt_app, út, eredeti)
        _elokeszit_mentest(controller, qt_app)
        eredeti_undo = save_controller_module.undo_save

        def hibas_undo(*_args, **_kwargs):
            raise OSError("forced undo error for #4440")

        save_controller_module.undo_save = hibas_undo
        try:
            _művelet_vege(
                controller,
                qt_app,
                controller.undoSaveFinished,
                lambda: _kattint_a_visszaallitasra(window, qt_app, undo=True),
            )
            hiba = window.findChild(QObject, "saveResultDialog")
            assert hiba is not None
            assert _vár(qt_app, lambda hiba=hiba: hiba.property("visible"))
            assert "forced undo error" in hiba.property("message")
            QMetaObject.invokeMethod(hiba, "close")
            assert _vár(qt_app, lambda hiba=hiba: not hiba.property("visible"))
        finally:
            save_controller_module.undo_save = eredeti_undo
