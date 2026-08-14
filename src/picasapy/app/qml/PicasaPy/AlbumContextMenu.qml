import QtQuick
import QtQuick.Controls

// Az album jobbklikk-menüje — a Picasa `Album` menüosztálya (#422,
// 4. lépcső). Ez a mappa-menü album-változata: ugyanaz a szerep, más
// parancsokkal.
//
// FIGYELEM a teljességről: a `docs/specs/ui-audit-context-menus.md` A.2
// szakasza szerint az osztály **13 tételes**, de a dokumentum név szerint
// csak **11-et** sorol fel. A hiányzó kettőt NEM találjuk ki — amíg elő
// nem kerül (a string-táblából vagy képernyőképről), ez a menü a 11
// dokumentált tételt tartalmazza, se többet, se kevesebbet. Ld. a jegyet
// a hiányzó tételek felderítésére.
//
// A még be nem kötött parancsok `PicasaMenuItem { placeholder: true }`-ként
// szürkén LÁTSZANAK (#416, spec 5.1.). Az album törlése/leírása mögött
// nincs réteg (a `photo_ops_controller` csak létrehozni és tagságot írni
// tud), a webes műveletek pedig nálunk nem értelmezhetők.
//
// Önálló, signal-alapú komponens: a bekötést a FolderPane.qml végzi.
Menu {
    id: menu
    objectName: "albumContextMenu"

    // a jobbklikkelt album azonosítója — a hívó állítja be popup() előtt
    property string albumToken: ""
    property string albumName: ""

    signal selectAllRequested()
    signal clearSelectionRequested()
    signal invertSelectionRequested()
    signal refreshThumbnailsRequested()
    signal exportAsHtmlRequested()

    // -- 1. blokk: album-műveletek ----------------------------------------

    PicasaMenuItem {
        objectName: "albumMenuDelete"
        text: qsTr("Delete Album")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "albumMenuEditDescription"
        text: qsTr("Edit Album Description...")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "albumMenuAddNameTags"
        text: qsTr("Add Name Tags")
        placeholder: true
    }
    MenuSeparator {}

    // -- 2. blokk: kijelölés ------------------------------------------------

    MenuItem {
        objectName: "albumMenuSelectAll"
        text: qsTr("Select All Pictures")
        onTriggered: menu.selectAllRequested()
    }
    MenuItem {
        objectName: "albumMenuClearSelection"
        text: qsTr("Clear Selection")
        onTriggered: menu.clearSelectionRequested()
    }
    MenuItem {
        objectName: "albumMenuInvertSelection"
        text: qsTr("Invert Selection")
        onTriggered: menu.invertSelectionRequested()
    }
    MenuSeparator {}

    // -- 3. blokk: nézet -----------------------------------------------------

    MenuItem {
        objectName: "albumMenuRefreshThumbnails"
        text: qsTr("Refresh Thumbnails")
        onTriggered: menu.refreshThumbnailsRequested()
    }
    MenuSeparator {}

    // -- 4. blokk: megosztás / export -----------------------------------------

    PicasaMenuItem {
        objectName: "albumMenuOnlineActions"
        text: qsTr("Online Actions")
        placeholder: false
        // #422: megszűnt szolgáltatás — véglegesen szürke, nem hátralévő munka
        retired: true
    }
    PicasaMenuItem {
        objectName: "albumMenuUploadToGooglePhotos"
        text: qsTr("Upload to Google Photos...")
        placeholder: false
        // #422: megszűnt szolgáltatás — véglegesen szürke, nem hátralévő munka
        retired: true
    }
    MenuItem {
        objectName: "albumMenuExportAsHtml"
        text: qsTr("Export as HTML Page...")
        onTriggered: menu.exportAsHtmlRequested()
    }
}
