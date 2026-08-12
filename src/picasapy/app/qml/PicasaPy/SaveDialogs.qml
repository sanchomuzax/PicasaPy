import QtQuick
import QtQuick.Controls

// Mentés a lemezre / Visszaállítás / Utolsó mentés visszavonása (#444).
//
// A Picasa NÉGY külön műveletet ismer; ebből három él itt (a negyedik, az
// „Összes szerkesztés visszavonása", a Kép menüben — #465). A szövegek az
// eredeti bináris sztringjeiből valók:
//
//   Mentés:          „Save changes to disk?" + „A backup of these files
//                     will be made."
//   Visszaállítás:   „Revert to original version of these file(s)?" +
//                     „This cannot be undone and all changes will be lost."
//   Utolsó mentés:   „To undo the last save and keep edits click
//                     'Undo Save'." — a szerkesztések MEGMARADNAK
//
// A mentés előtt külön figyelmeztetés jön, ha a láncban olyan effekt van,
// amit nem tudunk renderelni: a beégetés azt VÉGLEGESEN eldobná (#484).
Item {
    id: dialogs
    anchors.fill: parent

    required property var appWindow

    property var pendingRows: []

    function openSave(rows) {
        if (!rows || rows.length === 0) return
        dialogs.pendingRows = rows
        var lost = controller ? controller.unrenderableFiltersIn(rows) : []
        if (lost.length > 0) {
            unrenderableDialog.names = lost.join(", ")
            unrenderableDialog.open()
        } else {
            saveConfirmDialog.open()
        }
    }
    function openRevert(rows) {
        if (!rows || rows.length === 0) return
        dialogs.pendingRows = rows
        revertConfirmDialog.open()
    }
    function openUndoSave(rows) {
        if (!rows || rows.length === 0) return
        dialogs.pendingRows = rows
        undoSaveConfirmDialog.open()
    }

    Dialog {
        id: saveConfirmDialog
        objectName: "saveConfirmDialog"
        title: qsTr("Save")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: controller.saveRowsToDisk(dialogs.pendingRows)
        Column {
            spacing: 6
            Text {
                width: 380
                wrapMode: Text.WordWrap
                text: qsTr("Save changes to disk?")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                width: 380
                wrapMode: Text.WordWrap
                //: az eredeti megnyugtató kiegészítése — a mentés NEM
                //: visszafordíthatatlan, mert előtte másolat készül
                text: qsTr("A backup of these files will be made.")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
        }
    }

    // #484: a mentés a nem renderelhető láncelemet VÉGLEGESEN eldobja —
    // ez az egyetlen pont, ahol egy beállítás visszavonhatatlanul elvész,
    // ezért külön, hangsúlyos kérdés előzi meg.
    Dialog {
        id: unrenderableDialog
        objectName: "unrenderableFiltersDialog"
        title: qsTr("Save")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string names: ""
        onAccepted: controller.saveRowsToDisk(dialogs.pendingRows)
        Column {
            spacing: 6
            Text {
                width: 380
                wrapMode: Text.WordWrap
                text: qsTr("These pictures contain edits PicasaPy cannot render yet: %1")
                      .arg(unrenderableDialog.names)
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                width: 380
                wrapMode: Text.WordWrap
                text: qsTr("Saving writes the picture without them, and the settings are lost. This cannot be undone.")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
        }
    }

    Dialog {
        id: revertConfirmDialog
        objectName: "revertConfirmDialog"
        title: qsTr("Revert")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: controller.revertRowsToOriginal(dialogs.pendingRows)
        Column {
            spacing: 6
            Text {
                width: 380
                wrapMode: Text.WordWrap
                text: qsTr("Revert to original version of these file(s)?")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                width: 380
                wrapMode: Text.WordWrap
                text: qsTr("This cannot be undone and all changes will be lost.")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
        }
    }

    Dialog {
        id: undoSaveConfirmDialog
        objectName: "undoSaveConfirmDialog"
        title: qsTr("Undo Save")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: controller.undoLastSave(dialogs.pendingRows)
        Text {
            width: 380
            wrapMode: Text.WordWrap
            //: az eredeti magyarázata: ez a fokozat MEGTARTJA a
            //: szerkesztéseket, csak a lemezre írást vonja vissza
            text: qsTr("To undo the last save and keep edits click 'Undo Save'.")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    // a művelet végén EGY összegzés — csak ha volt hibás fájl (a #459 elve)
    Dialog {
        id: saveResultDialog
        objectName: "saveResultDialog"
        title: qsTr("File operation failed")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        Text {
            width: 380
            wrapMode: Text.WordWrap
            text: saveResultDialog.message
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Connections {
        target: controller
        function onSaveFailedDetails(details) {
            saveResultDialog.message = details.join("\n")
            saveResultDialog.open()
        }
    }
}
