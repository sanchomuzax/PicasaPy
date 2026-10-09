import QtQuick
import QtQuick.Controls

// Az Emberek-album jobbklikk-menüje — a Picasa `PplAlbum` menüosztálya,
// 4 tétellel (#422, 4. lépcső).
//
// Forrás: `docs/specs/ui-audit-context-menus.md` A.2 szakasza, ahol a négy
// tétel név szerint szerepel: az Emberek album törlése · szerkesztése… ·
// Az összes kijelölése · Kijelölés törlése.
//
// Önálló, signal-alapú komponens: a bekötést a FolderPane.qml végzi.
PicasaMenu {
    id: menu
    objectName: "peopleAlbumContextMenu"

    // a jobbklikkelt személy neve — a hívó állítja be popup() előtt
    property string personName: ""

    signal deleteRequested(string personName)
    signal editRequested(string personName)
    signal selectAllRequested()
    signal clearSelectionRequested()

    PicasaMenuItem {
        objectName: "peopleAlbumMenuDelete"
        text: qsTr("&Delete People Album")
        placeholder: false
        onTriggered: menu.deleteRequested(menu.personName)
    }
    PicasaMenuItem {
        objectName: "peopleAlbumMenuEdit"
        text: qsTr("&Edit People Album...")
        placeholder: false
        onTriggered: menu.editRequested(menu.personName)
    }
    MenuSeparator {}
    MenuItem {
        objectName: "peopleAlbumMenuSelectAll"
        text: qsTr("Select &All")
        onTriggered: menu.selectAllRequested()
    }
    MenuItem {
        objectName: "peopleAlbumMenuClearSelection"
        text: qsTr("&Clear Selection")
        onTriggered: menu.clearSelectionRequested()
    }
}
