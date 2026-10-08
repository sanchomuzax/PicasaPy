import QtQuick
import QtQuick.Controls

// Szövegmező-kontextusmenü — a Picasa `Address` menüosztálya, 7 tétellel
// (#422, a jegy kommentjének „azonnal hasznosítható" 1. pontja).
//
// Forrás: `docs/specs/ui-audit-menus.md` K.9 — Visszavonás · Kivágás ·
// Másolás · Beillesztés · Törlés · Az összes kijelölése · Automatikus
// kitöltés. Az eredetiben MINDEN szövegmező alatt ott van; nálunk eddig
// egyetlen mezőben sem volt jobbklikk-menü. A kitöltéskapcsoló csak ott
// látszik, ahol a címzett-kiegészítéshez tartozik (#4636).
//
// A #422 viselkedési szabályai közül kettő itt is érvényes:
//  * az inaktív tétel LÁTSZIK, szürkén — nem tűnik el (a menü magassága
//    állandó marad, az izommemória működik);
//  * a csoportosítást elválasztók adják (visszavonás · vágólap · kijelölés).
//
// Az „Automatikus kitöltés" csak a címzett mezőn jelenik meg: az eredeti
// `Address::ID_AUTOCOMPLETE` a `Preferences\\EmailAutocomplete` beállítást
// tárolja, de a javaslómotort nem kapcsolja ki (#4636).
//
// Használat: a mezőre tett MouseArea (jobb gomb) hívja a `popupFor(mező)`-t.
PicasaMenu {
    id: menu
    objectName: "textFieldContextMenu"

    //: a mező, amire a menü vonatkozik — a `popupFor()` állítja be
    property var target: null
    property bool autoCompleteSupported: false
    property var autoCompleteController: null

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
    MenuItem {
        objectName: "textMenuAutoComplete"
        text: qsTr("Auto-Complete")
        visible: menu.autoCompleteSupported
                 && menu.autoCompleteController !== null
        enabled: visible
        checkable: true
        checked: menu.autoCompleteController
                 && menu.autoCompleteController.emailAutocompleteEnabled === true
        onTriggered: {
            if (menu.autoCompleteController)
                menu.autoCompleteController.setEmailAutocompleteEnabled(checked)
        }
    }
}
