"""A nyitott néző menüi az aktív képre hassanak (#4629)."""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt

from tests.support.qt_wait import wait_for_photo_op


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
    window, controller, engine = qml_app
    window.show()
    viewer = _elem(window, "photoViewer")
    file_ops = engine.rootContext().contextProperty("fileOpsController")
    szerkeszto = engine.rootContext().contextProperty("editController")
    file_ops._vagolap_adat = None
    wait_for_photo_op(
        controller,
        lambda: controller.applyEffectMany([1], "enhance"),
        qt_app=qt_app,
    )

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
            "menuEditCopy",
            "menuEditCopyEffects",
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
            "menuPictureResetFaces",
            "menuPictureProperties",
        ):
            assert _elem(window, nev).property("enabled") is True, (
                f"{nev} szürke nyitott néző mellett"
            )
        assert _elem(window, "menuPictureUnhide").property("enabled") is False, (
            "a látható, megnyitott kép mellett a Kép ▸ Unhide szürke"
        )

        # #7143: az eredeti nézőben és szerkesztőben a Kivágást és a
        # Beillesztést szürkíti (`0x0056e95f-0x0056e98d`), a Másolás él.
        assert _elem(window, "menuEditCut").property("enabled") is False, (
            "nyitott néző mellett a Kivágás nem szürke"
        )
        assert _elem(window, "menuEditPaste").property("enabled") is False, (
            "nyitott néző mellett a Beillesztés nem szürke"
        )

        # A tesztképeken nincs Text eszközös réteg; a nyitott néző önmagában
        # nem engedélyezi a Copy Text/Paste Text rétegműveleteket.
        assert _elem(window, "menuEditCopyText").property("enabled") is False
        assert _elem(window, "menuEditPasteText").property("enabled") is False

        # A két eredetileg tiltott mappaparancs szerkesztőben maradjon szürke.
        assert _elem(window, "menuFileAddFolder").property("enabled") is False
        assert _elem(window, "menuToolsFolderManager").property("enabled") is False

        _elsut(window, qt_app, "menuFileSave")
        save_dialogs = _elem(window, "saveDialogs")
        assert _list_property(save_dialogs, "pendingRows") == [1], (
            "a Fájl ▸ Mentés a rács kijelölt sorát célozta a nézett kép helyett"
        )
        _elem(window, "saveConfirmDialog").setProperty("visible", False)

        # #7030: a nézőben a Másolás a MEGJELENÍTETT, szerkesztett képet teszi
        # a vágólapra képadatként (nem fájl-hivatkozást). A célpont mérése
        # ezért a szerkesztési munkamenet fotója: a megnyitott (1.) kép, nem
        # a rács kijelölése (0.), és a vágólap-kép az ő előnézete.
        file_ops._vagolap_adat = None
        szerkeszto._vagolap_kep = None
        _elsut(window, qt_app, "menuEditCopy")
        assert file_ops._vagolap_adat is None, (
            "a nézőben a Szerkesztés ▸ Másolás fájl-hivatkozást tett a vágólapra"
        )
        copied = szerkeszto._vagolap_kepe()
        assert copied is not None and not copied.isNull(), (
            "a Szerkesztés ▸ Másolás nem írt vágólapot"
        )
        assert controller.photos.idAt(0) != controller.photos.idAt(1)
        assert szerkeszto._photo_id == controller.photos.idAt(1), (
            "a vágólap-kép nem a megnyitott kép munkamenetéből jött: "
            f"{szerkeszto._photo_id!r}"
        )
        megjelenitett = szerkeszto._provider.requestImage(
            szerkeszto._kulcs, None, None
        )
        assert copied == megjelenitett, (
            "a vágólap-kép nem a megnyitott kép megjelenített előnézete"
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
