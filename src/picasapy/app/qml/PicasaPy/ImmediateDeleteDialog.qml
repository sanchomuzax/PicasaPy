import QtQuick
import QtQuick.Controls

// #6969: a Lomtárba helyezés PONTOSAN `0x0f` Shell-eredményének külön
// kérdése (`0x005c9b00` -> `0x005fdb80`): `CThumbUI::ConfirmImmediateDeletion::
// Message`, gombok `Delete` / `Cancel`. A végleges törlést (`0x009929b0`)
// csak a jóváhagyás indítja - a komponens a `deletionConfirmed(path)`
// jelzéssel szól, a törlést a hívó végzi.
//
// A Cancel és az Esc meghagyja a fájlt; a kérdés MINDIG megnyílik (üres
// kulcs: nincs "ne kérdezze újra"), és a biztonságos Cancel a kezdeti
// fókusz. Több képnél képenként kérdez: a sor a lezáráskor lép tovább, így
// az Esc sem akasztja meg.
//
// ⚠️ Az eredeti ablak címe a `0x005fdb80`-ban nincs mérve (a függvény csak a
// `Delete` / `Cancel` / üzenet sztringeket tartalmazza), ezért a cím a
// törlés-megerősítő közös címe.
ConfirmDialog {
    id: root
    objectName: "immediateDeleteDialog"
    namePrefix: "immediateDelete"
    //: DeleteMessage::DeleteItemsTitle
    // Az ablak címe az eredetiben nincs mérve: a törlés-megerősítő közös
    // címét használjuk.
    title: qsTr("Delete Items")
    //: CThumbUI::ConfirmImmediateDeletion::Delete
    yesText: qsTr("Delete")
    noVisible: false
    rememberVisible: false
    focusCancelOnOpen: true

    // A jóváhagyott kép útja - a végleges törlést a hívó végzi.
    signal deletionConfirmed(string path)

    property var queue: []
    property string currentPath: ""

    function enqueue(path) {
        queue = queue.concat([path])
        if (!visible)
            advance()
    }
    function advance() {
        if (queue.length === 0) {
            currentPath = ""
            return
        }
        currentPath = queue[0]
        queue = queue.slice(1)
        //: CThumbUI::ConfirmImmediateDeletion::Message
        ask("", qsTr(
            "This file cannot be moved to the Trash and will be "
            + "deleted immediately. Are you sure you want to continue?"))
    }
    onConfirmed: root.deletionConfirmed(root.currentPath)
    onClosed: Qt.callLater(function() {
        if (!root.visible)
            root.advance()
    })
}
