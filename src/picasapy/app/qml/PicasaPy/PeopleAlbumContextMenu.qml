import QtQuick
import QtQuick.Controls

// Az Emberek-album jobbklikk-menüje — a Picasa `PplAlbum` menüosztálya,
// 4 tétellel (#422, 4. lépcső).
//
// Forrás: `docs/specs/ui-audit-context-menus.md` A.2 szakasza, ahol a négy
// tétel név szerint szerepel: az Emberek album törlése · szerkesztése… ·
// Az összes kijelölése · Kijelölés törlése.
//
// Az első kettő mögött még nincs réteg — a személy-albumok szerkesztése és
// törlése az arcfelismerés-jegy (#26) hatóköre —, ezért szürkén látszanak
// (#416, spec 5.1.). A két kijelölés-parancs élő.
//
// Önálló, signal-alapú komponens: a bekötést a FolderPane.qml végzi.
Menu {
    id: menu
    objectName: "peopleAlbumContextMenu"

    // a jobbklikkelt személy neve — a hívó állítja be popup() előtt
    property string personName: ""

    signal selectAllRequested()
    signal clearSelectionRequested()

    PicasaMenuItem {
        objectName: "peopleAlbumMenuDelete"
        text: qsTr("&Delete People Album")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "peopleAlbumMenuEdit"
        text: qsTr("&Edit People Album...")
        placeholder: true
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
