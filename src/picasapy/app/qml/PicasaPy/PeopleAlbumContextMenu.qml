import QtQuick
import QtQuick.Controls

// Az Emberek-album jobbklikk-menüje — a Picasa `PplAlbum` menüosztálya.
// #4645: az eredeti sorrend szerkesztés · kijelölés · indexképek · törlés.
// A „Sort Album By” almenü bekötése a #4599 része, ezért itt egyelőre kimarad.
//
// Forrás: `docs/specs/ui-audit-context-menus.md` F.1.
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
    signal invertSelectionRequested()
    signal refreshThumbnailsRequested()

    PicasaMenuItem {
        objectName: "peopleAlbumMenuEdit"
        text: qsTr("&Edit People Album...")
        placeholder: false
        onTriggered: menu.editRequested(menu.personName)
    }
    MenuSeparator {
        objectName: "peopleAlbumMenuSeparatorAfterEdit"
    }
    MenuItem {
        objectName: "peopleAlbumMenuSelectAll"
        text: qsTr("Select &All") + "\tCtrl+A"
        onTriggered: menu.selectAllRequested()
    }
    MenuItem {
        objectName: "peopleAlbumMenuClearSelection"
        text: qsTr("&Clear Selection") + "\tCtrl+D"
        onTriggered: menu.clearSelectionRequested()
    }
    MenuItem {
        objectName: "peopleAlbumMenuInvertSelection"
        text: qsTr("&Invert Selection") + "\tCtrl+I"
        onTriggered: menu.invertSelectionRequested()
    }
    MenuSeparator {
        objectName: "peopleAlbumMenuSeparatorAfterSelection"
    }
    MenuItem {
        objectName: "peopleAlbumMenuRefreshThumbnails"
        text: qsTr("&Refresh Thumbnails")
        onTriggered: menu.refreshThumbnailsRequested()
    }
    MenuSeparator {
        objectName: "peopleAlbumMenuSeparatorBeforeDelete"
    }
    PicasaMenuItem {
        objectName: "peopleAlbumMenuDelete"
        text: qsTr("&Delete People Album")
        placeholder: false
        onTriggered: menu.deleteRequested(menu.personName)
    }
}
