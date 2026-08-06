import QtQuick
import QtQuick.Controls

// Kontextusmenü a bal hasáb mappasorainak jobbklikkjéhez (#320): az eredeti
// Picasa mappakezelő-viselkedése — a mappa egy felhasználói gyűjteménybe
// sorolható ("Áthelyezés gyűjteménybe…" almenü + "Új gyűjtemény…"), és a
// mappa dátuma kézzel felülírható (az évszám-szakaszoláshoz).
//
// Önálló, próba-oldallal tesztelt komponens (CONTRIBUTING.md mintája, ld.
// PhotoContextMenu.qml): csak jeleket bocsát ki, a controllerhez kötést a
// FolderPane.qml (nem forró fájl) végzi.
Menu {
    id: menu
    objectName: "folderContextMenu"

    // a jobbklikkelt mappa útvonala — a hívó (FolderPane) állítja be
    // popup() előtt
    property string folderPath: ""
    // a felhasználó egyéni gyűjteményei: {name, folders} elemek listája
    property var customCollections: []

    signal moveToCollectionRequested(string collectionName)
    signal newCollectionRequested()
    signal setDateRequested()

    Menu {
        id: moveMenu
        objectName: "folderContextMenuMoveToCollection"
        title: qsTr("Move to Collection...")

        Repeater {
            id: moveMenuRepeater
            objectName: "folderContextMenuMoveToCollectionRepeater"
            model: menu.customCollections
            delegate: MenuItem {
                id: moveMenuItem
                required property var modelData
                objectName: "folderContextMenuMoveToCollectionItem_" + modelData.name
                text: modelData.name
                onTriggered: menu.moveToCollectionRequested(modelData.name)
            }
        }
        MenuSeparator { visible: menu.customCollections.length > 0 }
        MenuItem {
            objectName: "folderContextMenuNewCollection"
            text: qsTr("New Collection...")
            onTriggered: menu.newCollectionRequested()
        }
    }
    MenuSeparator {}
    MenuItem {
        objectName: "folderContextMenuSetDate"
        text: qsTr("Set Folder Date...")
        onTriggered: menu.setDateRequested()
    }
}
