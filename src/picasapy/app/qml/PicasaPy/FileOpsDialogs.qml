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
    // #1614: Fájl ▸ Áthelyezés új mappába… — a `newAlbumDialog` mintáját
    // követi (egyetlen névmező), mert a párbeszéd pontos alakjára nincs
    // erősebb bizonyíték (ld. a jegy „Bizonyítottsági fok" szakasza).
    function openMoveToNewFolder(paths) {
        moveToNewFolderDialog.openFor(paths)
    }
    function openDelete(paths) {
        deleteConfirmDialog.openFor(paths)
    }
    // #457/2: a köteg indítása — előbb MEGNÉZZÜK, van-e névütközés, és csak
    // akkor kérdezünk (az eredeti sem kérdezett fölöslegesen); ütközés nélkül
    // az „átnevezés" ág fut, de az ott nem nevez át semmit.
    function startBatch(operation, paths, dest) {
        if (fileOpsController.conflictCountFor(paths, dest) > 0)
            duplicateNamesDialog.openFor(operation, paths, dest)
        else
            runBatch(operation, paths, dest, "rename")
    }
    function runBatch(operation, paths, dest, policy) {
        if (operation === "copy")
            fileOpsController.copyPhotos(paths, dest, policy)
        else
            fileOpsController.movePhotos(paths, dest, policy)
        dialogs.appWindow.clearSelection()
    }

    // #9 (2. lépés): új album neve — a rows a kijelölés sorindexei, amelyek
    // a controller.createAlbum(name, rows) hívásba kerülnek elfogadáskor
    function openNewAlbum(rows) {
        newAlbumDialog.openFor(rows)
    }

    // #1612: a vezérlő VISSZAJELZÉSEI. A hozzájuk tartozó `Connections`
    // SZÁNDÉKOSAN nem itt áll, hanem a `Main.qml`-ben (a #2096 mintája):
    // ez a komponens halasztott, és a `fileOpsController` jelzései nem csak
    // innen indulhatnak — a mappafa áthelyezés/törlés útja
    // (`FolderPane.qml`, `moveFolder`/`deleteFolder`) is ezen jelez vissza.
    // Belső hallgatóval a hibaüzenet NÉMÁN elmaradna, amíg a felhasználó
    // egyszer sem nyitott meg fájlművelet-párbeszédet.
    function reportBatch(operation, destination, done, total, speed) {
        batchProgressDialog.report(operation, destination, done, total, speed)
    }
    function finishBatch(operation, done, skipped, failed, reason) {
        batchProgressDialog.close()
        batchSummaryDialog.showFor(operation, done, skipped, failed, reason)
    }
    function showOperationError(operation, message) {
        fileOpsErrorDialog.message = message
        fileOpsErrorDialog.open()
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

    // #1614: Fájl ▸ Áthelyezés új mappába… — a `newAlbumDialog` mintáját
    // követő egyetlen névmező. A tényleges névellenőrzés (üres/csak
    // szóköz/Windows-tiltott karakter) és a mappa létrehozása a
    // `fileOpsController.moveSelectionToNewFolder`-ben történik — hiba
    // esetén a szokásos `operationFailed` → `fileOpsErrorDialog` úton jut
    // el a felhasználóhoz, ezért itt nincs saját hibaágra szükség.
    Dialog {
        id: moveToNewFolderDialog
        objectName: "moveToNewFolderDialog"
        title: qsTr("Move to New Folder...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property var paths: []
        function openFor(pathList) {
            if (!pathList || pathList.length === 0) return
            paths = pathList
            moveToNewFolderField.text = ""
            open()
            moveToNewFolderField.forceActiveFocus()
        }
        // ⚠️ SZÁNDÉKOSAN nincs `clearSelection()` itt (eltérően a
        // `runBatch`-től): a mappa létrehozása ELŐBB fut, mint bármelyik
        // kép mozdulna — érvénytelen név vagy már foglalt célmappa esetén
        // EGYETLEN fájl sem mozdul, tehát a kijelölés ürítése félrevezető
        // volna. Sikeres áthelyezésnél a `wire_fileops` resyncje úgyis
        // frissíti a rácsot; a kijelölés megmaradása itt nem hibaosztály.
        onAccepted: {
            if (fileOpsController)
                fileOpsController.moveSelectionToNewFolder(
                    paths, moveToNewFolderField.text.trim())
        }
        TextField {
            id: moveToNewFolderField
            objectName: "moveToNewFolderField"
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
        onAccepted: moveConfirmDialog.openFor(paths, selectedFolder.toString())
    }

    // #457/2: az eredeti a célmappa kiválasztása UTÁN még rákérdezett
    // (`CThumbUI::MoveFilesToAlbumFolder::6`, elfogadó gomb: „Fájlok
    // áthelyezése" — `MoveYesButton`). Csak ezután jött a névütközés
    // kérdése, ha volt egyáltalán ütközés.
    Dialog {
        id: moveConfirmDialog
        objectName: "moveConfirmDialog"
        // #1185: a `Dialog` a saját `implicitWidth`-ét a `contentItem`-ből
        // számolja, a tördelő `Text` implicit szélessége viszont a kapott
        // szélességtől függ — ez a kör „Binding loop … implicitWidth"-ként
        // jelent meg a konzolon. A tartalom szélessége itt amúgy is
        // rögzített (`width: 380`), ezért kimondjuk: a párbeszéd szélessége
        // a szövegdoboz + a stílus térközei. A `Text.implicitWidth` Qt 6-ban
        // ÍRÁSVÉDETT, ezért nem ott törjük meg a kört.
        implicitWidth: 380 + leftPadding + rightPadding
        title: qsTr("Confirm Move")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property var paths: []
        property string dest: ""
        onOpened: standardButton(Dialog.Ok).text = qsTr("Move Files")
        function acceptButtonText() {
            return standardButton(Dialog.Ok) ? standardButton(Dialog.Ok).text : ""
        }
        function openFor(pathList, destFolder) {
            if (!pathList || pathList.length === 0) return
            paths = pathList
            dest = destFolder
            open()
        }
        onAccepted: dialogs.startBatch("move", paths, dest)
        Text {
            width: 380
            text: qsTr("Are you sure you want to move the file(s) to\n%1 ?").arg(
                      moveConfirmDialog.dest)
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    // #457/2: névütközéskor az eredeti NEM döntött a felhasználó helyett —
    // ugyanezt a párbeszédet adta másolásra és áthelyezésre is
    // (`CThumbUI::MoveFilesToAlbumFolder::2` és `::5`), két gombbal:
    // „Másodpéldányok átnevezése" / „Másodpéldányok kihagyása".
    Dialog {
        id: duplicateNamesDialog
        objectName: "duplicateNamesDialog"
        // #1185: a `Dialog` a saját `implicitWidth`-ét a `contentItem`-ből
        // számolja, a tördelő `Text` implicit szélessége viszont a kapott
        // szélességtől függ — ez a kör „Binding loop … implicitWidth"-ként
        // jelent meg a konzolon. A tartalom szélessége itt amúgy is
        // rögzített (`width: 380`), ezért kimondjuk: a párbeszéd szélessége
        // a szövegdoboz + a stílus térközei. A `Text.implicitWidth` Qt 6-ban
        // ÍRÁSVÉDETT, ezért nem ott törjük meg a kört.
        implicitWidth: 380 + leftPadding + rightPadding
        title: moveConfirmDialog.title
        modal: true
        anchors.centerIn: parent
        property string operation: "move"
        property var paths: []
        property string dest: ""
        function openFor(op, pathList, destFolder) {
            operation = op
            paths = pathList
            dest = destFolder
            open()
        }
        Text {
            width: 380
            text: qsTr("This folder already contains files with the same name.\n\nWould you like to rename or skip these files?")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        footer: DialogButtonBox {
            Button {
                objectName: "duplicateRenameButton"
                text: qsTr("Rename Duplicates")
                onClicked: {
                    duplicateNamesDialog.close()
                    dialogs.runBatch(duplicateNamesDialog.operation,
                                     duplicateNamesDialog.paths,
                                     duplicateNamesDialog.dest, "rename")
                }
            }
            Button {
                objectName: "duplicateSkipButton"
                text: qsTr("Skip Duplicates")
                onClicked: {
                    duplicateNamesDialog.close()
                    dialogs.runBatch(duplicateNamesDialog.operation,
                                     duplicateNamesDialog.paths,
                                     duplicateNamesDialog.dest, "skip")
                }
            }
            Button {
                objectName: "duplicateCancelButton"
                text: qsTr("Cancel")
                onClicked: duplicateNamesDialog.close()
            }
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
        // #1185: a `Dialog` a saját `implicitWidth`-ét a `contentItem`-ből
        // számolja, a tördelő `Text` implicit szélessége viszont a kapott
        // szélességtől függ — ez a kör „Binding loop … implicitWidth"-ként
        // jelent meg a konzolon. A tartalom szélessége itt amúgy is
        // rögzített (`width: 380`), ezért kimondjuk: a párbeszéd szélessége
        // a szövegdoboz + a stílus térközei. A `Text.implicitWidth` Qt 6-ban
        // ÍRÁSVÉDETT, ezért nem ott törjük meg a kört.
        implicitWidth: 380 + leftPadding + rightPadding
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

    // #457/2 + #459: a köteg végén EGYETLEN összegzés (nem fájlonkénti ablak).
    // Ha minden gond nélkül átment, nem zavarjuk a felhasználót ablakkal.
    Dialog {
        id: batchSummaryDialog
        objectName: "batchSummaryDialog"
        // #1185: a `Dialog` a saját `implicitWidth`-ét a `contentItem`-ből
        // számolja, a tördelő `Text` implicit szélessége viszont a kapott
        // szélességtől függ — ez a kör „Binding loop … implicitWidth"-ként
        // jelent meg a konzolon. A tartalom szélessége itt amúgy is
        // rögzített (`width: 380`), ezért kimondjuk: a párbeszéd szélessége
        // a szövegdoboz + a stílus térközei. A `Text.implicitWidth` Qt 6-ban
        // ÍRÁSVÉDETT, ezért nem ott törjük meg a kört.
        implicitWidth: 380 + leftPadding + rightPadding
        title: qsTr("File operation finished")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        // #1430: a `reason` az ELSŐ bukás fájlneve és oka. A darabszám
        // önmagában nem cselekvésre fordítható, és a felületen az
        // áthelyezés mindig ezen az úton fut — a magok magyarázó üzenete
        // csak így jut el a felhasználóhoz. A szöveg a magból jön, magyarul
        // és készen (ahogy a `fileOpsErrorDialog`-ban is), ezért nincs
        // `qsTr()` köré vonva.
        function showFor(operation, done, skipped, failed, reason) {
            if (skipped === 0 && failed === 0) return
            var lines = [qsTr("%n file(s) done.", "", done)]
            if (skipped > 0)
                lines.push(qsTr("%n file(s) skipped (a file with the same name already exists).", "", skipped))
            if (failed > 0)
                lines.push(qsTr("%n file(s) could not be processed.", "", failed))
            if (reason)
                lines.push(reason)
            message = lines.join("\n")
            open()
        }
        Text {
            width: 380
            text: batchSummaryDialog.message
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    // #457: haladásjelző a kötegelt másoláshoz/áthelyezéshez. Az eredeti
    // címei: `CThumbUI::CopyProgress` = „Copying Files" és
    // `CThumbUI::MoveProgress` = „Moving Files"; a törzse megmondta, HOVA
    // megy (`MoveFilesToAlbumFolder::1`/`::4`), a számláló pedig azt, hol
    // tart (`CAcquireUI::copying` = „Copying %1$d of %2$d files").
    Dialog {
        id: batchProgressDialog
        objectName: "batchProgressDialog"
        title: operation === "move" ? qsTr("Moving Files") : qsTr("Copying Files")
        modal: true
        anchors.centerIn: parent
        closePolicy: Popup.NoAutoClose
        property string operation: "copy"
        property string destination: ""
        property int done: 0
        property int total: 0
        property real speed: 0        // bájt/mp

        // „%s/s" — az eredeti a sebességet is kiírta; MB/s-ban mutatjuk,
        // mert ezen a nagyságrenden ez a beszédes
        readonly property string speedText:
            speed > 0 ? (speed / (1024 * 1024)).toFixed(1) + " MB/s" : ""

        function report(op, dest, doneCount, totalCount, bytesPerSec) {
            batchProgressDialog.speed = bytesPerSec || 0
            batchProgressDialog.operation = op
            batchProgressDialog.destination = dest
            batchProgressDialog.done = doneCount
            batchProgressDialog.total = totalCount
            // egyetlen fájlnál nincs mit nézni rajta
            if (totalCount > 1 && doneCount < totalCount)
                batchProgressDialog.open()
            else
                batchProgressDialog.close()
        }

        ColumnLayout {
            spacing: 8
            Text {
                objectName: "batchProgressTarget"
                Layout.preferredWidth: 360
                wrapMode: Text.WrapAnywhere
                text: batchProgressDialog.operation === "move"
                      ? qsTr("Moving file(s) to %1").arg(batchProgressDialog.destination)
                      : qsTr("Copying file(s) to %1").arg(batchProgressDialog.destination)
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                objectName: "batchProgressCount"
                Layout.preferredWidth: 360
                text: (batchProgressDialog.operation === "move"
                       ? qsTr("Moving %1 of %2 files")
                         .arg(batchProgressDialog.done).arg(batchProgressDialog.total)
                       : qsTr("Copying %1 of %2 files")
                         .arg(batchProgressDialog.done).arg(batchProgressDialog.total))
                      + (batchProgressDialog.speedText.length > 0
                         ? "  (" + batchProgressDialog.speedText + ")" : "")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            ProgressBar {
                objectName: "batchProgressBar"
                Layout.preferredWidth: 360
                from: 0
                to: Math.max(1, batchProgressDialog.total)
                value: batchProgressDialog.done
            }
        }
    }

}
