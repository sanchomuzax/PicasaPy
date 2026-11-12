"""#6852: az öt eltérő mappa-helyimenü folyamat valódi kattintásos próbája."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QStandardPaths, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest

from picasapy.app.webexport_controller import WebExportController
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    almenu_megnyitasa,
    gyerek,
    jobbklikk_mappan,
    kattints,
    nyitott,
    varj,
    zar,
)


_ABLAKMAGASSAG_ELTERESEK = (-5, 0, 5)


class _MemSettings:
    def value(self, _key, default=None):
        return default

    def setValue(self, _key, _value):
        pass


@pytest.fixture(scope="module")
def mappa_app(qml_app_module, qt_app):
    window, controller, engine = qml_app_module
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    folder = str(controller.currentFolder)
    assert folder, "a tesztmappa nincs kiválasztva"
    return window, controller, engine, folder, int(window.height())


@pytest.fixture(autouse=True)
def _popupok_takaritasa(mappa_app, qt_app):
    yield
    window, _controller, _engine, _folder, _height = mappa_app
    for name in (
        "folderMenuSortBy",
        "folderContextMenu",
        "removeFolderConfirmDialog",
        "deleteFolderConfirmDialog",
        "moveFolderDialog",
        "webExportDialog",
    ):
        item = window.findChild(QObject, name)
        if item is not None and nyitott(item):
            QMetaObject.invokeMethod(item, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _magassag(mappa_app, qt_app, delta):
    window, _controller, _engine, _folder, base_height = mappa_app
    target = base_height + delta
    window.setHeight(target)
    assert varj(qt_app, lambda: int(window.height()) == target), (
        f"a főablak nem vette fel a {delta:+d} px-es magasságeltérést"
    )


def _elonezet_proba(engine, image):
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick
Item {
    property var imageItem
    readonly property bool ready:
        imageItem ? imageItem.status === Image.Ready : false
    readonly property bool failed:
        imageItem ? imageItem.status === Image.Error : false
}""",
        QUrl(),
    )
    assert component.isReady(), component.errors()
    probe = component.createWithInitialProperties({"imageItem": image})
    assert probe is not None, component.errors()
    return component, probe


def _mappavalaszto_nativ_proba(engine, dialog):
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick
import QtQuick.Dialogs
Item {
    property var folderDialog
    readonly property bool nativePicker:
        (folderDialog.options & FolderDialog.DontUseNativeDialog) === 0
}""",
        QUrl(),
    )
    assert component.isReady(), component.errors()
    probe = component.createWithInitialProperties({"folderDialog": dialog})
    assert probe is not None, component.errors()
    return component, probe


def _nyisd_meg_menuvel(mappa_app, qt_app, menu_item_name):
    window, _controller, _engine, folder, _height = mappa_app
    menu = jobbklikk_mappan(window, qt_app, folder)
    kattints(window, qt_app, gyerek(window, menu_item_name))
    return window, menu


@pytest.mark.parametrize("height_delta", _ABLAKMAGASSAG_ELTERESEK)
def test_a_rendezes_nevvel_kezdodik_es_nincs_elvalaszto_a_forditott_sorrend_elott(
    mappa_app, qt_app, height_delta
):
    _magassag(mappa_app, qt_app, height_delta)
    window, _controller, _engine, folder, _height = mappa_app
    menu = jobbklikk_mappan(window, qt_app, folder)
    submenu = gyerek(window, "folderMenuSortBy")
    almenu_megnyitasa(window, qt_app, menu, "folderMenuSortBy")

    names = [
        "folderMenuSortByName",
        "folderMenuSortByDate",
        "folderMenuSortBySize",
        "folderMenuSortByColor",
        "folderMenuSortByPriority",
        "folderMenuSortReverse",
    ]
    items = [gyerek(window, name) for name in names]
    centers = [item.mapToScene(item.boundingRect().center()).y() for item in items]
    assert centers == sorted(centers), "a rendezési tételek sorrendje hibás"
    assert submenu.property("count") == 6, (
        "a Reverse order előtt nem lehet elválasztó"
    )

    kattints(window, qt_app, items[0])
    assert varj(qt_app, lambda: not menu.property("visible")), (
        "a Name menütétel kattintása nem zárta be a menüt"
    )


@pytest.mark.parametrize("height_delta", _ABLAKMAGASSAG_ELTERESEK)
def test_az_eltavolitas_megerositese_jelolo_nelkul_cancel_gombbal(
    mappa_app, qt_app, height_delta
):
    _magassag(mappa_app, qt_app, height_delta)
    window, controller, _engine, folder, _height = mappa_app
    _nyisd_meg_menuvel(mappa_app, qt_app, "folderMenuRemoveFromPicasa")

    dialog = gyerek(window, "removeFolderConfirmDialog")
    assert varj(qt_app, lambda: nyitott(dialog)), "a Confirm ablak nem nyílt meg"
    assert dialog.property("title") == "Confirm"
    assert dialog.property("yesText") == "Remove Folder"
    remember = gyerek(dialog, "removeFolderConfirmRememberCheck")
    assert not remember.property("visible"), "az eltávolítási jelölőnek rejtve kell lennie"
    yes = gyerek(dialog, "removeFolderConfirmYesButton")
    no = gyerek(dialog, "removeFolderConfirmNoButton")
    cancel = gyerek(dialog, "removeFolderConfirmCancelButton")
    assert yes.property("visible") and yes.property("text") == "Remove Folder"
    assert not no.property("visible"), "az eredetiben nincs No gomb"
    assert cancel.property("visible") and cancel.property("text") == "Cancel", (
        "az eredeti Cancel gomb hiányzik vagy rossz feliratú"
    )

    kattints(window, qt_app, cancel)
    assert varj(qt_app, lambda: not nyitott(dialog)), "a Cancel nem zárta be a Confirm ablakot"
    assert Path(folder).is_dir() and controller.photos.photos, (
        "a Cancel az eltávolítás végrehajtása nélkül nem tarthatja meg a mappát"
    )


@pytest.mark.parametrize("height_delta", _ABLAKMAGASSAG_ELTERESEK)
def test_a_mappatorles_nem_alapertelmezett_igen_gombbal_kerdez(
    mappa_app, qt_app, height_delta
):
    _magassag(mappa_app, qt_app, height_delta)
    window, controller, _engine, folder, _height = mappa_app
    _nyisd_meg_menuvel(mappa_app, qt_app, "folderMenuDeleteFolder")

    dialog = gyerek(window, "deleteFolderConfirmDialog")
    assert varj(qt_app, lambda: nyitott(dialog)), "a Delete Folder ablak nem nyílt meg"
    assert dialog.property("title") == "Delete Folder"
    assert dialog.property("yesText") == "Delete Folder"
    yes = gyerek(dialog, "deleteFolderConfirmYesButton")
    no = gyerek(dialog, "deleteFolderConfirmNoButton")
    cancel = gyerek(dialog, "deleteFolderConfirmCancelButton")
    remember = gyerek(dialog, "deleteFolderConfirmRememberCheck")
    assert yes.property("visible") and no.property("visible")
    assert yes.property("text") == "Delete Folder" and no.property("text") == "No"
    assert not cancel.property("visible"), "az eredeti ablakban nincs Cancel gomb"
    assert not remember.property("visible"), "az eredeti ablakban nincs jelölő"
    assert varj(qt_app, lambda: no.property("activeFocus")), (
        "a No gombnak kell alapértelmezett fókuszt kapnia"
    )

    QTest.keyClick(window, Qt.Key.Key_Return)
    assert varj(qt_app, lambda: not nyitott(dialog)), "az Enter nem a No ágat választotta"
    assert Path(folder).is_dir() and controller.photos.photos, (
        "az Enter törlést indított a No alapértelmezés ellenére"
    )


@pytest.mark.parametrize("height_delta", _ABLAKMAGASSAG_ELTERESEK)
def test_az_athelyezes_mappavalasztasa_a_forras_szulojeben_nyilik(
    mappa_app, qt_app, height_delta
):
    _magassag(mappa_app, qt_app, height_delta)
    window, _controller, _engine, folder, _height = mappa_app
    _nyisd_meg_menuvel(mappa_app, qt_app, "folderMenuMoveFolder")

    dialog = gyerek(window, "moveFolderDialog")
    assert varj(qt_app, lambda: nyitott(dialog)), "a Browse for Folder ablak nem nyílt meg"
    assert dialog.property("title") == "Browse for Folder"
    _, native_probe = _mappavalaszto_nativ_proba(_engine, dialog)
    assert native_probe.property("nativePicker"), (
        "a mappaböngészőt nem natív módban kényszerítettük, így hiányozhat a "
        "Make New Folder művelet"
    )
    current_folder = dialog.property("currentFolder")
    assert current_folder is not None, "a mappaválasztó kezdőmappája hiányzik"
    current_path = current_folder.toLocalFile()
    assert Path(current_path) == Path(folder).parent, (
        f"a mappaválasztó nem a forrás szülőjében nyílt: {current_path!r}"
    )
    assert dialog.property("acceptLabel") == "OK"
    assert dialog.property("rejectLabel") == "Cancel"
    zar(qt_app, dialog)


@pytest.mark.parametrize("height_delta", _ABLAKMAGASSAG_ELTERESEK)
def test_a_html_export_mappa_es_sablonok_mar_a_megnyitaskor_latszanak(
    mappa_app, qt_app, monkeypatch, height_delta
):
    _magassag(mappa_app, qt_app, height_delta)
    window, controller, engine, folder, _height = mappa_app
    documents = Path(folder).parent / "Documents"
    # a windowsos alapmappa (#5714) méri az eredetit; más platformon a
    # rendszer képmappája marad (#534), ezt a teszt nem írja felül
    import picasapy.app.webexport_controller as webexport_modul

    monkeypatch.setattr(webexport_modul, "_platform", lambda: "win32")
    monkeypatch.setattr(
        QStandardPaths,
        "writableLocation",
        lambda _location: str(documents),
    )
    web_export = WebExportController(
        photo_source=lambda: controller.photos.photos,
        settings=_MemSettings(),
    )
    engine.rootContext().setContextProperty("webExportController", web_export)

    _nyisd_meg_menuvel(mappa_app, qt_app, "folderMenuExportAsHtml")
    dialog = gyerek(window, "webExportDialog")
    assert varj(qt_app, lambda: nyitott(dialog)), "az Export as HTML ablak nem nyílt meg"
    expected = documents / "Picasa HTML Exports" / Path(folder).name
    assert Path(str(dialog.property("targetFolder"))) == expected, (
        f"a Folder kezdőértéke hibás: {dialog.property('targetFolder')!r}"
    )
    template_list = gyerek(dialog, "webExportTemplateList")
    preview = gyerek(dialog, "webExportTemplatePreview")
    assert template_list.property("count") == 7, (
        "a sablonlista nincs feltöltve a megnyitáskor"
    )
    assert preview.property("visible"), "a sablon előnézete nincs megnyitáskor megjelenítve"
    component, preview_probe = _elonezet_proba(engine, preview)
    assert varj(
        qt_app,
        lambda: preview_probe.property("ready") or preview_probe.property("failed"),
    ), f"a sablon előnézete nem töltődött be: {component.errors()}"
    assert preview_probe.property("ready"), (
        "a sablon előnézeti képe nem töltődött be: "
        f"source={preview.property('source')}"
    )
    zar(qt_app, dialog)
