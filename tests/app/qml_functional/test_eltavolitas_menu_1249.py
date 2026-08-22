"""„Eltávolítás a Picasából…" a VALÓDI menü-úton (#1249).

A jegy DoD-ja: valódi menü-kattintással, ne a controller-metódus
közvetlen hívásával — az a minta már kétszer engedett át hibát
(#1148, #1200): itt is pont az volt a baj, hogy a menü kezelője a ROSSZ
metódust hívta, miközben a metódus-szintű tesztek zöldek voltak.
"""

from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from support.jpeg_factory import make_jpeg


def _ujraolvas(controller, qt_app) -> None:
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _almappas_konyvtar(qml_app, qt_app):
    window, controller, _ = qml_app
    gyoker = Path(controller.watchedFolders[0])
    (gyoker / "alma").mkdir(exist_ok=True)
    make_jpeg(gyoker / "alma" / "x.jpg", size=(32, 24))
    _ujraolvas(controller, qt_app)
    alma = str(gyoker / "alma")
    assert alma in tuple(controller.folders.folder_paths())
    return window, controller, alma


def _elem(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


class TestMenuUt:
    def test_a_menu_es_a_megerosites_eltunteti_az_almappat(
        self, qml_app, qt_app
    ):
        """A teljes út: menüpont → megerősítés (a mappa NEVÉVEL, az
        eredeti igen-gombbal) → az almappa eltűnik, és rescan után sem
        jön vissza."""
        window, controller, alma = _almappas_konyvtar(qml_app, qt_app)
        pane = _elem(window, "folderPane")

        # a menü megnyitása az almappára — a valódi jobbklikk-kezelő útja
        QMetaObject.invokeMethod(
            pane, "openFolderContextMenu",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", alma),
        )
        qt_app.processEvents()

        # a menü „Remove from Picasa..." tétele — a menü saját jelzésén át
        menu = window.findChild(QObject, "folderContextMenu")
        assert menu is not None, "folderContextMenu nem található"
        QMetaObject.invokeMethod(
            menu, "removeFromPicasaRequested", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        megerosites = _elem(window, "removeFolderConfirmDialog")
        assert megerosites.property("visible") is True, (
            "a megerősítő nem nyílt meg"
        )
        uzenet = str(megerosites.property("message"))
        assert "alma" in uzenet, f"a mappa neve hiányzik: {uzenet!r}"
        assert "subfolders" in uzenet, f"az almappákat nem mondja ki: {uzenet!r}"
        assert str(megerosites.property("yesText")) == "Remove Folder"

        QMetaObject.invokeMethod(
            megerosites, "confirmed", Qt.ConnectionType.DirectConnection
        )
        for _ in range(200):
            qt_app.processEvents()
            if controller.waitForBackgroundWorkers(0.05):
                break
        qt_app.processEvents()

        assert alma not in tuple(controller.folders.folder_paths()), (
            "az almappa a menü-út után is a panelen maradt"
        )

        _ujraolvas(controller, qt_app)
        assert alma not in tuple(controller.folders.folder_paths()), (
            "az almappa visszajött a rescan után (nincs sírkő)"
        )
