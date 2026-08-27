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
// #1526: az „Automatikus kitöltés" ÉLŐ kapcsoló lett. A beállítás a
// `controller.autoComplete` (perzisztens, `view/autoComplete`), és két
// VALÓDI javaslat-felületet kapcsol: a keresőmező buborékját (#7) és az
// arcnév-mező ismert-név listáját (#147). A `typeof`-őr azért kell, mert a
// menüt önmagában betöltő próbák nem regisztrálnak `controller`-t.
//
// Használat: a mezőre tett MouseArea (jobb gomb) hívja a `popupFor(mező)`-t.
Menu {
    id: menu
    objectName: "textFieldContextMenu"

    //: a mező, amire a menü vonatkozik — a `popupFor()` állítja be
    property var target: null

    // #1526: null-őr (#305 mintája) — a menü önmagában is betölthető
    readonly property var appCtl:
        (typeof controller !== "undefined") ? controller : null
    readonly property bool autoCompleteOn:
        menu.appCtl ? menu.appCtl.autoComplete : true

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
        checkable: true
        // a pipa a MENTETT beállítást mutatja, tehát az újraindítást is
        // túléli; a kapcsoló minden mező helyi menüjében ugyanazt állítja
        checked: menu.autoCompleteOn
        enabled: menu.appCtl !== null
        onTriggered: menu.appCtl.setAutoComplete(!menu.autoCompleteOn)
    }
}
