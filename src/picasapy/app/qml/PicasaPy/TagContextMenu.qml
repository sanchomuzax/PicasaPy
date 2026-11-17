import QtQuick
import QtQuick.Controls

// A címke jobbklikk-menüje — a Picasa `Tags` menüosztálya, 3 tétellel
// és egy elválasztóval a Search és a Remove között (#422, 3. lépcső; #7136).
//
// Forrás: `docs/specs/ui-audit-context-menus.md` A.2 szakasza. Ez a menü a
// képernyőképeken nem szerepelt, a string-táblából derült ki — nálunk
// eddig teljesen hiányzott.
//
// Mindhárom parancs mögött van réteg: a hozzáadás/eltávolítás a
// kulcsszó-vezérlőn, a keresés a meglévő keresőn át.
//
// Önálló, signal-alapú komponens: a bekötést a TagsPanel.qml végzi.
PicasaMenu {
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
        text: qsTr("Add this tag to entire selection")
        onTriggered: menu.addToSelectionRequested()
    }
    MenuItem {
        objectName: "tagMenuFindTagged"
        text: qsTr("Search for items with this tag")
        onTriggered: menu.findTaggedRequested()
    }
    // #7136: az eredeti `0x00735480` négy rekordot ad a `0x00a6aee0`-nak:
    // Add (`0xa0b8`), Search (`0xa0b7`), csupa nulla rekord (`0x00d6f868`),
    // Remove (`0xa0b9`); a nulla rekord elválasztó (`0x00a6af04-0x00a6af20`).
    MenuSeparator { objectName: "tagMenuSeparator" }
    MenuItem {
        objectName: "tagMenuRemove"
        text: qsTr("Remove this tag")
        onTriggered: menu.removeRequested()
    }
}
