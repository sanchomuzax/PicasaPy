"""A nyitott néző menüi az aktív képre hassanak (#4629)."""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


def _elem(window, object_name: str):
    elem = window.findChild(QObject, object_name)
    assert elem is not None, f"{object_name} nem található"
    return elem


def _elsut(window, qt_app, object_name: str):
    elem = _elem(window, object_name)
    assert elem.property("enabled") is True, f"{object_name} szürke"
    QMetaObject.invokeMethod(
        elem, "triggered", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _list_property(obj, name: str) -> list:
    value = obj.property(name)
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return list(value or [])


def test_a_fajl_szerkesztes_es_kep_menu_a_nezett_keppel_dolgozik(
    qml_app, qt_app
):
    from pathlib import Path

    window, controller, engine = qml_app
    window.show()
    viewer = _elem(window, "photoViewer")
    file_ops = engine.rootContext().contextProperty("fileOpsController")
    file_ops._vagolap_adat = None

    # A rács másik képet tart kijelölve, hogy a menü célpontja mérhetően
    # eltérjen a kijelöléstől. A három ablakmagasság a felületi kötést is
    # platformfüggő geometriától függetlenül ellenőrzi.
    for magassag in (1019, 1024, 1029):
        window.resize(1280, magassag)
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        viewer.setProperty("currentIndex", 1)
        window.setProperty("viewerOpen", True)
        qt_app.processEvents()

        for nev in (
            "menuFileSave",
            "menuFileSaveAs",
            "menuFileSaveCopy",
            "menuFileExport",
            "menuFileLocate",
            "menuFileDelete",
            "menuFilePrint",
            "menuFileEmail",
            "menuFileMoveToNewFolder",
            "menuFileRename",
            "menuFileNewAlbum",
            "menuFileOpenInEditor",
            "menuEditCut",
            "menuEditCopy",
            "menuEditCopyEffects",
            "menuEditCopyText",
            "menuPictureViewAndEdit",
            "menuBatchAutoContrast",
            "menuBatchAutoColor",
            "menuBatchAutoRedeye",
            "menuBatchEnhance",
            "menuBatchSharpen",
            "menuBatchFilmGrain",
            "menuBatchWarmify",
            "menuBatchRotateRight",
            "menuBatchRotateLeft",
            "menuPictureUndoAllEdits",
            "menuPictureHide",
            "menuPictureUnhide",
            "menuPictureResetFaces",
            "menuPictureProperties",
        ):
            assert _elem(window, nev).property("enabled") is True, (
                f"{nev} szürke nyitott néző mellett"
            )

        # A két eredetileg tiltott mappaparancs szerkesztőben maradjon szürke.
        assert _elem(window, "menuFileAddFolder").property("enabled") is False
        assert _elem(window, "menuToolsFolderManager").property("enabled") is False

        _elsut(window, qt_app, "menuFileSave")
        save_dialogs = _elem(window, "saveDialogs")
        assert _list_property(save_dialogs, "pendingRows") == [1], (
            "a Fájl ▸ Mentés a rács kijelölt sorát célozta a nézett kép helyett"
        )
        _elem(window, "saveConfirmDialog").setProperty("visible", False)

        _elsut(window, qt_app, "menuEditCopy")
        copied = file_ops._vagolap_adat
        assert copied is not None, "a Szerkesztés ▸ Másolás nem írt vágólapot"
        paths = [Path(url.toLocalFile()) for url in copied.urls()]
        assert paths == [Path(controller.photos.filePathAt(1))], (
            f"a vágólap tartalma nem a megnyitott kép: {paths}"
        )

        _elsut(window, qt_app, "menuFileExport")
        export_dialog = _elem(window, "exportDialog")
        assert _list_property(export_dialog, "requestedRows") == [1], (
            "a Fájl ▸ Export a rács kijelölt sorát célozta a nézett kép helyett"
        )
        export_dialog.setProperty("visible", False)

        panel = _elem(window, "viewerEditorPanel")
        panel.setProperty("activeTab", 1)
        _elsut(window, qt_app, "menuBatchEnhance")
        assert panel.property("activeTab") == 0, (
            "a Kép ▸ I'm Feeling Lucky nem navigált a Gyakori javítások fülre"
        )
        panel.setProperty("activeTab", 1)
        _elsut(window, qt_app, "menuBatchWarmify")
        assert panel.property("activeTab") == 2, (
            "a Kép ▸ Warmify nem navigált az Effektek fülre"
        )
