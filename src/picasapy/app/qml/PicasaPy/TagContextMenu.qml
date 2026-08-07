import QtQuick
import QtQuick.Controls

// A címke jobbklikk-menüje — a Picasa `Tags` menüosztálya, 3 tétellel
// (#422, 3. lépcső).
//
// Forrás: `docs/specs/ui-audit-context-menus.md` A.2 szakasza. Ez a menü a
// képernyőképeken nem szerepelt, a string-táblából derült ki — nálunk
// eddig teljesen hiányzott.
//
// Mindhárom parancs mögött van réteg: a hozzáadás/eltávolítás a
// kulcsszó-vezérlőn, a keresés a meglévő keresőn át.
//
// Önálló, signal-alapú komponens: a bekötést a TagsPanel.qml végzi.
Menu {
    id: menu
    objectName: "tagContextMenu"

    // a jobbklikkelt címke — a hívó állítja be popup() előtt
    property string keyword: ""

    // a címke rátétele a TELJES kijelölésre (nem csak az aktuális képre)
    signal addToSelectionRequested()
    signal findTaggedRequested()
    signal removeRequested()

    MenuItem {
        objectName: "tagMenuAddToSelection"
        text: qsTr("Add Tag to Entire Selection")
        onTriggered: menu.addToSelectionRequested()
    }
    MenuItem {
        objectName: "tagMenuFindTagged"
        text: qsTr("Find Items Tagged This Way")
        onTriggered: menu.findTaggedRequested()
    }
    MenuItem {
        objectName: "tagMenuRemove"
        text: qsTr("Remove Tag")
        onTriggered: menu.removeRequested()
    }
}
