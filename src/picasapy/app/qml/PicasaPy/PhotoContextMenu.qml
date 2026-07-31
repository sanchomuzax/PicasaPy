import QtQuick
import QtQuick.Controls

// Kontextusmenü a rács jobbklikkjéhez (#15): átnevezés/áthelyezés/törlés/
// megnyitás a fájlkezelőben, a Picasa 3.9 Fájl-menüjének elnevezéseivel.
// Önálló, próba-oldallal tesztelt komponens (CONTRIBUTING.md mintája) — a
// ThumbDelegate.contextMenuRequested → popup(x, y) bekötést és a jelek
// FileOpsControllerhez/PhotoOpsControllerhez kapcsolását (Main.qml, forró
// fájl) az integrátor végzi.
Menu {
    id: menu
    objectName: "photoContextMenu"

    signal renameRequested()
    signal moveRequested()
    signal deleteRequested()
    signal locateRequested()
    // #17: Elrejtés — pipával, ha a célpont már rejtett (Picasa-minta)
    property bool hideChecked: false
    signal hideToggleRequested()

    // #9 (2. lépés): albumtagság — a Main.qml köti be a `controller.albums`
    // listáját és az aktív album tokent (#305 null-őr, ld. ott).
    property var albums: []
    property string currentAlbumToken: ""
    signal addToAlbumRequested(string token)
    signal removeFromAlbumRequested()
    signal newAlbumRequested()

    MenuItem {
        objectName: "contextMenuRename"
        text: qsTr("Rename...")
        onTriggered: menu.renameRequested()
    }
    MenuItem {
        objectName: "contextMenuHide"
        text: qsTr("Hide")
        checkable: true
        checked: menu.hideChecked
        onTriggered: menu.hideToggleRequested()
    }
    MenuItem {
        objectName: "contextMenuMove"
        text: qsTr("Move to Folder...")
        onTriggered: menu.moveRequested()
    }
    MenuItem {
        objectName: "contextMenuDelete"
        text: qsTr("Delete from Disk")
        onTriggered: menu.deleteRequested()
    }
    MenuSeparator {}
    Menu {
        id: addToAlbumMenu
        objectName: "contextMenuAddToAlbum"
        title: qsTr("Add to Album")

        Repeater {
            id: addToAlbumRepeater
            objectName: "contextMenuAddToAlbumRepeater"
            model: menu.albums
            delegate: MenuItem {
                id: addToAlbumItem
                required property var modelData
                objectName: "contextMenuAddToAlbumItem_" + modelData.token
                text: modelData.name
                onTriggered: menu.addToAlbumRequested(modelData.token)
            }
        }
        MenuSeparator { visible: menu.albums.length > 0 }
        MenuItem {
            objectName: "contextMenuNewAlbum"
            text: qsTr("New Album...")
            onTriggered: menu.newAlbumRequested()
        }
    }
    MenuItem {
        objectName: "contextMenuRemoveFromAlbum"
        text: qsTr("Remove from Album")
        // csak album-nézetben (#9): a rács ott az adott album tagjait
        // mutatja, ott van értelme a kijelölés kivételének
        visible: menu.currentAlbumToken !== ""
        onTriggered: menu.removeFromAlbumRequested()
    }
    MenuSeparator {}
    MenuItem {
        objectName: "contextMenuLocate"
        text: qsTr("Locate on Disk")
        onTriggered: menu.locateRequested()
    }
}
