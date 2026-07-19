import QtQuick.Controls

// Kontextusmenü a rács jobbklikkjéhez (#15): átnevezés/áthelyezés/törlés/
// megnyitás a fájlkezelőben, a Picasa 3.9 Fájl-menüjének elnevezéseivel.
// Önálló, próba-oldallal tesztelt komponens (CONTRIBUTING.md mintája) — a
// ThumbDelegate.contextMenuRequested → popup(x, y) bekötést és a jelek
// FileOpsControllerhez kapcsolását (Main.qml, forró fájl) az integrátor
// végzi.
Menu {
    id: menu
    objectName: "photoContextMenu"

    signal renameRequested()
    signal moveRequested()
    signal deleteRequested()
    signal locateRequested()

    MenuItem {
        objectName: "contextMenuRename"
        text: qsTr("Rename...")
        onTriggered: menu.renameRequested()
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
    MenuItem {
        objectName: "contextMenuLocate"
        text: qsTr("Locate on Disk")
        onTriggered: menu.locateRequested()
    }
}
