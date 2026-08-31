import QtQuick
import QtQuick.Controls

// A gyűjtemény jobbklikk-menüje — a Picasa `Collection` menüosztálya
// (#422, utolsó hiányzó menü).
//
// Forrás: `docs/specs/ui-audit-context-menus.md` 4. szakasza. Három tétel:
// átnevezés, eltávolítás, jelszó. A #476-ban elkészült felhasználói
// gyűjtemény-fejlécre (`CollectionHeader`,
// `labelObjectName: "customCollection_" + name`) kell ezt a menüt kötni.
//
// A jelszavas gyűjtemény funkció mögött nálunk nincs réteg (a
// `.picasa.ini`/kontroller nem ismer jelszót) — a tétel
// `PicasaMenuItem { placeholder: true }`-ként szürkén LÁTSZIK (#416, spec
// 5.1.). A másik kettő (átnevezés, eltávolítás) valódi parancsokat kap: a
// kontroller `renameCollection`/`deleteCollection` metódusait a
// FolderPane.qml köti be.
//
// Önálló, signal-alapú komponens: a bekötést a FolderPane.qml végzi.
PicasaMenu {
    id: menu
    objectName: "collectionContextMenu"

    // a jobbklikkelt gyűjtemény neve — a hívó állítja be popup() előtt
    property string collectionName: ""

    signal renameRequested()
    signal removeRequested()

    // -- gyűjtemény-műveletek ----------------------------------------------

    MenuItem {
        objectName: "collectionMenuRename"
        text: qsTr("Rename &Collection...")
        onTriggered: menu.renameRequested()
    }
    MenuItem {
        objectName: "collectionMenuRemove"
        text: qsTr("&Remove Collection")
        onTriggered: menu.removeRequested()
    }
    PicasaMenuItem {
        objectName: "collectionMenuPassword"
        text: qsTr("&Add/Change a password...")
        placeholder: true
    }
}
