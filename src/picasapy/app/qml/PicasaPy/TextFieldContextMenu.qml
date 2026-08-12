import QtQuick
import QtQuick.Controls

// Szövegmező-kontextusmenü — a Picasa `Address` menüosztálya, 7 tétellel
// (#422, a jegy kommentjének „azonnal hasznosítható" 1. pontja).
//
// Forrás: `docs/specs/ui-audit-menus.md` K.9 — Visszavonás · Kivágás ·
// Másolás · Beillesztés · Törlés · Az összes kijelölése · Automatikus
// kitöltés. Az eredetiben MINDEN szövegmező alatt ott van; nálunk eddig
// egyetlen mezőben sem volt jobbklikk-menü.
//
// A #422 viselkedési szabályai közül kettő itt is érvényes:
//  * az inaktív tétel LÁTSZIK, szürkén — nem tűnik el (a menü magassága
//    állandó marad, az izommemória működik);
//  * a csoportosítást elválasztók adják (visszavonás · vágólap · kijelölés).
//
// Az „Automatikus kitöltés" a Picasa címsor-kiegészítése; nálunk nincs
// mögötte réteg, ezért `PicasaMenuItem` helyfoglalóként jelenik meg — így
// ránézésre is látszik, hogy a helye megvan, de még nem működik (#416).
//
// Használat: a mezőre tett MouseArea (jobb gomb) hívja a `popupFor(mező)`-t.
Menu {
    id: menu
    objectName: "textFieldContextMenu"

    //: a mező, amire a menü vonatkozik — a `popupFor()` állítja be
    property var target: null

    readonly property bool hasSelection: menu.target
        && menu.target.selectedText !== undefined
        && menu.target.selectedText.length > 0
    readonly property bool editable: menu.target
        && menu.target.readOnly !== true
        && menu.target.enabled !== false

    function popupFor(field) {
        menu.target = field
        menu.popup()
    }

    MenuItem {
        objectName: "textMenuUndo"
        text: qsTr("Undo")
        enabled: menu.editable && menu.target && menu.target.canUndo === true
        onTriggered: menu.target.undo()
    }

    MenuSeparator {}

    MenuItem {
        objectName: "textMenuCut"
        text: qsTr("Cut")
        enabled: menu.editable && menu.hasSelection
        onTriggered: menu.target.cut()
    }
    MenuItem {
        objectName: "textMenuCopy"
        text: qsTr("Copy")
        enabled: menu.hasSelection
        onTriggered: menu.target.copy()
    }
    MenuItem {
        objectName: "textMenuPaste"
        text: qsTr("Paste")
        enabled: menu.editable && menu.target && menu.target.canPaste === true
        onTriggered: menu.target.paste()
    }
    MenuItem {
        objectName: "textMenuDelete"
        text: qsTr("Delete")
        enabled: menu.editable && menu.hasSelection
        // a Picasa „Törlés" tétele a KIJELÖLÉST törli, nem a mezőt üríti
        onTriggered: menu.target.remove(
            menu.target.selectionStart, menu.target.selectionEnd)
    }

    MenuSeparator {}

    MenuItem {
        objectName: "textMenuSelectAll"
        text: qsTr("Select All")
        enabled: menu.target && menu.target.length > 0
        onTriggered: menu.target.selectAll()
    }
    PicasaMenuItem {
        objectName: "textMenuAutoComplete"
        text: qsTr("Auto-Complete")
    }
}
