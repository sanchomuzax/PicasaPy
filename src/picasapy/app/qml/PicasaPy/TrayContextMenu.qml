import QtQuick
import QtQuick.Controls

// A képtálca jobbklikk-menüje — a Picasa `Tray` menüosztálya, 2 tétellel
// (#422, 3. lépcső).
//
// Forrás: `docs/specs/ui-audit-context-menus.md` A.2 szakasza. Ez a menü a
// képernyőképeken nem szerepelt, a string-táblából derült ki — nálunk
// eddig teljesen hiányzott.
//
// A két parancs a KIJELÖLÉSRE hat: a „megtartás" a jobbklikkelt képre
// szűkíti a kijelölést, az „eltávolítás" pedig kiveszi belőle.
//
// Önálló, signal-alapú komponens: a bekötést a TrayBar.qml végzi.
PicasaMenu {
    id: menu
    objectName: "trayContextMenu"

    signal keepSelectionRequested()
    signal removeSelectionRequested()

    MenuItem {
        objectName: "trayMenuKeepSelection"
        text: qsTr("Keep Selection")
        onTriggered: menu.keepSelectionRequested()
    }
    MenuItem {
        objectName: "trayMenuRemoveSelection"
        text: qsTr("Remove Selection")
        onTriggered: menu.removeSelectionRequested()
    }
}
