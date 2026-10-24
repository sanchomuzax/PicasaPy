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
// A jelszó-tétel mind a felhasználói, mind a beépített Rejtett mappák
// gyűjteményen aktív (#5704). A gazda a megfelelő jelszó-párbeszédet nyitja.
// Az átnevezés és az eltávolítás felhasználói gyűjteményen valódi parancs
// (a kontroller metódusait a FolderPane.qml köti be); a beépített Rejtett
// mappákon szürke.
//
// Önálló, signal-alapú komponens: a bekötést a FolderPane.qml végzi.
PicasaMenu {
    id: menu
    objectName: "collectionContextMenu"

    // a jobbklikkelt gyűjtemény neve — a hívó állítja be popup() előtt
    property string collectionName: ""
    // a jobbklikkelt fejléc a beépített „Rejtett mappák" csomópont-e (#3461)
    property bool hiddenCollection: false
    signal renameRequested()
    signal removeRequested()
    signal passwordRequested()

    // -- gyűjtemény-műveletek ----------------------------------------------

    MenuItem {
        objectName: "collectionMenuRename"
        text: qsTr("Rename &Collection...")
        enabled: !menu.hiddenCollection
        onTriggered: menu.renameRequested()
    }
    MenuItem {
        objectName: "collectionMenuRemove"
        text: qsTr("&Remove Collection")
        enabled: !menu.hiddenCollection
        onTriggered: menu.removeRequested()
    }
    PicasaMenuItem {
        objectName: "collectionMenuPassword"
        text: qsTr("&Add/Change a password...")
        placeholder: false
        onTriggered: menu.passwordRequested()
    }
}
