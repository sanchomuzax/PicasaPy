import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Fájlművelet-dialógusok (#15, #150-ben kiemelve a Main.qml-ből):
// átnevezés (F2), áthelyezés mappába, lomtárba törlés megerősítéssel,
// hiba-visszajelzés. A tényleges műveletek a fileOpsController slotjai;
// a sikeres művelet utáni resync a Python-oldali bekötés (wire_fileops)
// dolga.
Item {
    id: dialogs
    anchors.fill: parent

    // a főablak (kijelölés-ürítés a műveletek után)
    required property var appWindow

    function openRename(row) {
        renameDialog.openFor(row)
    }
    // #366 (rename.fen paritás — tömeges mód): a kijelölés TÖBB sorára
    // egyszerre. Az egyfájlos F2-út (openRename/renameDialog) változatlan —
    // ez egy külön dialógus, amely dátum-/felbontás-utótag jelölőnégyzeteket
    // és élő fájlnév-előnézetet ad (az integrátor Main.qml-bekötése:
    // ld. a jelentést).
    function openRenameMany(rows) {
        renameManyDialog.openFor(rows)
    }
    function openMove(paths) {
        moveFolderDialog.paths = paths
        if (moveFolderDialog.paths.length > 0) moveFolderDialog.open()
    }
    function openDelete(paths) {
        deleteConfirmDialog.openFor(paths)
    }
    // #9 (2. lépés): új album neve — a rows a kijelölés sorindexei, amelyek
    // a controller.createAlbum(name, rows) hívásba kerülnek elfogadáskor
    function openNewAlbum(rows) {
        newAlbumDialog.openFor(rows)
    }

    Dialog {
        id: renameDialog
        objectName: "renameDialog"
        title: qsTr("Rename...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string targetPath: ""
        // #350 (rename.fen paritás): az eredeti dialógus "Rename" feliratú
        // elfogadó gombot használ, nem generikus "OK"-t.
        onOpened: standardButton(Dialog.Ok).text = qsTr("Rename")
        // tesztelhetőség: a standardButton() visszatérése QQuickAbstractButton*,
        // ami Python oldalról marshalva bizonytalan — inkább egy egyszerű
        // stringet adunk vissza.
        function acceptButtonText() {
            return standardButton(Dialog.Ok) ? standardButton(Dialog.Ok).text : ""
        }
        function openFor(row) {
            var p = controller.photos.filePathAt(row)
            if (p.length === 0) return
            targetPath = p
            renameField.text = controller.photos.itemAt(row).name || ""
            open()
            renameField.forceActiveFocus()
            renameField.selectAll()
        }
        onAccepted: {
            if (renameField.text.trim().length > 0)
                fileOpsController.renamePhoto(
                    targetPath, renameField.text.trim())
        }
        ColumnLayout {
            spacing: 8
            // #350 (rename.fen paritás): a PicasaPy jelenleg egyszerre egy
            // fájlt nevez át (F2-út) — a FEN dinamikus "%s file(s) selected"
            // szövegét ennek megfelelően rögzített "1"-gyel jelenítjük meg;
            // a tömeges átnevezés (dátum-/felbontás-toldalék, élő előnézet)
            // önálló, nagyobb feladat (ld. jelentés).
            Text {
                objectName: "renameSelectionLabel"
                text: qsTr("%n file(s) selected for rename.", "", 1)
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                objectName: "renamePromptLabel"
                text: qsTr("Please enter a new name for these files:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: renameField
                objectName: "renameField"
                width: 300
                font.pixelSize: Theme.fontSize
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }
    }

    // #366: tömeges átnevezés — `rename.fen` teljes paritás (alapnév +
    // dátum-/felbontás-utótag jelölőnégyzetek + élő "Example:" előnézet,
    // a kijelölés ELSŐ fájlján). A sorszámozás (`név`, `név-1`, `név-2`…)
    // az elfogadáskor a backendben (`controller.renamePhotosMany`) történik.
    Dialog {
        id: renameManyDialog
        objectName: "renameManyDialog"
        title: qsTr("Rename...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property var rows: []
        onOpened: standardButton(Dialog.Ok).text = qsTr("Rename")
        function acceptButtonText() {
            return standardButton(Dialog.Ok) ? standardButton(Dialog.Ok).text : ""
        }
        function openFor(rowList) {
            if (!rowList || rowList.length === 0) return
            rows = rowList
            renameManyField.text = ""
            includeDateCheck.checked = false
            includeSizeCheck.checked = false
            updatePreview()
            open()
            renameManyField.forceActiveFocus()
        }
        // élő előnézet: a kijelölés első fájljának végleges neve, ahogy a
        // rename.fen "Example:" felirata is csak az elsőt mutatja
        function updatePreview() {
            renameManyDialog.previewText = (controller && rows.length > 0)
                ? controller.renamePreview(
                      rows, renameManyField.text,
                      includeDateCheck.checked, includeSizeCheck.checked)
                : ""
        }
        property string previewText: ""
        onAccepted: {
            var base = renameManyField.text.trim()
            if (base.length > 0 && controller)
                controller.renamePhotosMany(
                    rows, base, includeDateCheck.checked, includeSizeCheck.checked)
        }
        ColumnLayout {
            spacing: 8
            Text {
                objectName: "renameManySelectionLabel"
                text: qsTr(
                    "%n file(s) selected for rename.", "",
                    renameManyDialog.rows.length)
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                objectName: "renameManyPromptLabel"
                text: qsTr("Please enter a new name for these files:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: renameManyField
                objectName: "renameManyField"
                width: 300
                font.pixelSize: Theme.fontSize
                onTextChanged: renameManyDialog.updatePreview()
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
            RowLayout {
                objectName: "renameManyIncludeRow"
                spacing: 16
                Text {
                    text: qsTr("Include in filename:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                CheckBox {
                    id: includeDateCheck
                    objectName: "renameManyDateCheck"
                    text: qsTr("Date")
                    onCheckedChanged: renameManyDialog.updatePreview()
                }
                CheckBox {
                    id: includeSizeCheck
                    objectName: "renameManySizeCheck"
                    text: qsTr("Image resolution")
                    onCheckedChanged: renameManyDialog.updatePreview()
                }
            }
            Text {
                objectName: "renameManySampleLabel"
                text: qsTr("Example:") + " " + renameManyDialog.previewText
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
        }
    }

    Dialog {
        id: newAlbumDialog
        objectName: "newAlbumDialog"
        title: qsTr("New Album...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property var rows: []
        function openFor(rowList) {
            if (rowList.length === 0) return
            rows = rowList
            newAlbumField.text = ""
            open()
            newAlbumField.forceActiveFocus()
        }
        onAccepted: {
            if (controller) controller.createAlbum(newAlbumField.text.trim(), rows)
        }
        TextField {
            id: newAlbumField
            objectName: "newAlbumField"
            width: 300
            font.pixelSize: Theme.fontSize
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
    }

    FolderDialog {
        id: moveFolderDialog
        objectName: "moveFolderDialog"
        title: qsTr("Move to Folder...")
        property var paths: []
        onAccepted: {
            var dest = selectedFolder.toString()
            for (var i = 0; i < paths.length; ++i)
                fileOpsController.movePhoto(paths[i], dest)
            dialogs.appWindow.clearSelection()
        }
    }

    // #367: az általános ConfirmDialog komponensre állítva (confirm.fen
    // paritás) — a törlés-kulcs "delete", a "Don't ask again" jelöléssel
    // legközelebb nem nyílik meg újra, hanem azonnal törli a kijelöltet.
    //
    // #457: NAS/hálózati meghajtón (ahol nincs elérhető lomtár, sem a
    // home, sem a mount-specifikus) a Picasa 3 külön, hangsúlyos szöveggel
    // figyelmeztet, hogy a törlés AZONNALI és VÉGLEGES — ezt a
    // `fileOpsController.trashAvailableFor(paths)` dönti el megnyitáskor;
    // a "ne kérdezze újra" kulcs ("delete") ilyenkor is a lomtár-ágé marad
    // (`DoNotConfirmDeleteFromDisk` — ld. picasa-fen-dialogs.md), a
    // végleges ágnak külön kulcsa van, hogy a NAS-figyelmeztetés soha ne
    // legyen elnémítható elnémítás-tévedésből.
    ConfirmDialog {
        id: deleteConfirmDialog
        objectName: "deleteConfirmDialog"
        title: qsTr("Delete from Disk")
        property var paths: []
        property bool trashAvailable: true
        function openFor(pathList) {
            if (pathList.length === 0) return
            paths = pathList
            trashAvailable = fileOpsController.trashAvailableFor(pathList)
            if (trashAvailable) {
                ask("delete", qsTr(
                        "%n picture(s) will be moved to the system trash.",
                        "", pathList.length))
            } else {
                ask("deletePermanently", qsTr(
                    "This file cannot be moved to the Trash and will be deleted immediately. This cannot be undone."))
            }
        }
        onConfirmed: {
            for (var i = 0; i < paths.length; ++i) {
                if (trashAvailable)
                    fileOpsController.deletePhoto(paths[i])
                else
                    fileOpsController.deletePhotoPermanently(paths[i])
            }
            dialogs.appWindow.clearSelection()
        }
    }

    Dialog {
        id: fileOpsErrorDialog
        objectName: "fileOpsErrorDialog"
        title: qsTr("File operation failed")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        Text {
            width: 380
            text: fileOpsErrorDialog.message
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Connections {
        target: fileOpsController
        function onOperationFailed(operation, message) {
            fileOpsErrorDialog.message = message
            fileOpsErrorDialog.open()
        }
    }
}
