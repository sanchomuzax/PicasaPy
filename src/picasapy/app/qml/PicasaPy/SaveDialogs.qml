import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

// Mentés a lemezre / Visszaállítás / Utolsó mentés visszavonása (#444);
// Mentés másként… / Másolat mentése / három hibaág (#1527).
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
    // #1527: a „Mentés másként…” célja EGY kép — a fájlválasztó
    // egyetlen célt tud megnevezni
    property int saveAsRow: -1

    // #1527: a „többé ne kérdezd" TARTÓS beállításának kulcsa. Az eredeti
    // Picasa neve `DoNotAskFileSave` (a `0x0053a790` olvassa a
    // Preferences mellől) — a mi tárolónkban
    // `confirm/DoNotAskFileSave/remember` alatt él, ugyanabban a
    // QSettings-ben, mint a többi megerősítés (#367).
    readonly property string doNotAskKey: "DoNotAskFileSave"

    function saveConfirmSuppressed() {
        return typeof confirmSettings !== "undefined" && confirmSettings
               && confirmSettings.isSuppressed(dialogs.doNotAskKey)
    }

    function openSave(rows) {
        if (!rows || rows.length === 0) return
        dialogs.pendingRows = rows
        var lost = controller ? controller.unrenderableFiltersIn(rows) : []
        if (lost.length > 0) {
            // A nem renderelhető láncelem figyelmeztetése (#484) NEM
            // nyomható el: ott a felhasználó beállítása vész el
            // véglegesen, nem csak egy kérdés ismétlődik.
            unrenderableDialog.names = lost.join(", ")
            unrenderableDialog.open()
        } else if (dialogs.saveConfirmSuppressed()) {
            controller.saveRowsToDisk(rows)
        } else {
            saveConfirmDialog.rememberChecked = false
            saveConfirmDialog.open()
        }
    }

    // #1527 — „Másolat mentése": nem kérdez semmit (a felirata ellipszis
    // nélküli), a célnevet a mért `-001` minta adja. A teljes kijelölésre
    // hat: a hivatalos hibaüzenete is többes számú („…a fájlok mentése").
    function openSaveCopy(rows) {
        if (!rows || rows.length === 0) return
        controller.saveCopyRows(rows)
    }

    // #1527 — „Mentés másként…": fájlválasztót nyit, EGY képre (egy
    // választó egy célt tud megnevezni). A felkínált név a `-001` minta,
    // mert a forrásra menteni az eredeti is tiltja
    // (`IDS_CANT_SAVE_TO_SAME`).
    function openSaveAs(row) {
        if (row === undefined || row < 0) return
        dialogs.saveAsRow = row
        var javaslat = controller ? controller.suggestedCopyUrl(row) : ""
        if (javaslat.length > 0)
            saveAsFileDialog.selectedFile = javaslat
        saveAsFileDialog.open()
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

    // #1527: a mentés megerősítése. HÁROM hivatalos erőforrásból áll —
    // a kérdés (`CThumbUI::FileSave::message`), és a kiegészítés KÉT
    // külön alakja: `messagetag1` egy fájlra, `messagetagX` többre. A
    // kettőt SZÁNDÉKOSAN nem vonjuk össze egyetlen, %1-es sztringbe: az
    // eredetiben is két erőforrás, és a magyar mondat sem egy szó
    // cseréjével áll elő („erről a fájlról" ↔ „ezekről a fájlokról").
    Dialog {
        id: saveConfirmDialog
        objectName: "saveConfirmDialog"
        title: qsTr("Save")
        modal: true
        anchors.centerIn: parent
        //: CThumbUI::FileSave::saveButton — az eredeti gombfelirata nem
        //: „OK", hanem a művelet neve
        standardButtons: Dialog.Save | Dialog.Cancel
        property bool rememberChecked: false
        readonly property int fileCount: dialogs.pendingRows
                                         ? dialogs.pendingRows.length : 0
        onAccepted: {
            if (saveConfirmDialog.rememberChecked
                    && typeof confirmSettings !== "undefined" && confirmSettings)
                confirmSettings.setSuppressed(dialogs.doNotAskKey, true)
            controller.saveRowsToDisk(dialogs.pendingRows)
        }
        Column {
            spacing: 6
            Text {
                objectName: "saveConfirmMessage"
                width: 380
                wrapMode: Text.WordWrap
                text: qsTr("Save changes to disk?")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                objectName: "saveConfirmBackupNote"
                width: 380
                wrapMode: Text.WordWrap
                //: az eredeti megnyugtató kiegészítése — a mentés NEM
                //: visszafordíthatatlan, mert előtte másolat készül.
                //: EGY kijelölt fájlra (CThumbUI::FileSave::messagetag1)
                text: saveConfirmDialog.fileCount === 1
                      ? qsTr("A backup of this file will be made.")
                      //: ugyanez TÖBB fájlra (messagetagX)
                      : qsTr("A backup of these files will be made.")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            // ⚠️ #1468 rádió-csapda ellen: ez NEM `checkable`+kötött
            // `checked` pár. A jelölő SAJÁT állapotot tart, és csak az
            // „Mentés" ág írja ki tartósan — a Mégse ág szándékosan nem,
            // különben egy elvetett párbeszéd némán kikapcsolná a kérdést.
            CheckBox {
                objectName: "saveConfirmRememberCheck"
                text: qsTr("Don't ask again")
                checked: saveConfirmDialog.rememberChecked
                onToggled: saveConfirmDialog.rememberChecked = checked
            }
        }
    }

    // #1527 — „Mentés másként…" célválasztója. A szűrők az eredetiéi:
    // `CThumbUI::SaveAsFilterJPG` = „JPEG Files" / `*.jpg`, és
    // `CThumbUI::SaveAsFilterWebP` = „WebP Files" / `*.webp`.
    FileDialog {
        id: saveAsFileDialog
        objectName: "saveAsFileDialog"
        title: qsTr("Save As...")
        fileMode: FileDialog.SaveFile
        defaultSuffix: "jpg"
        nameFilters: [qsTr("JPEG Files (*.jpg)"), qsTr("WebP Files (*.webp)")]
        onAccepted: controller.saveRowAs(dialogs.saveAsRow,
                                         selectedFile.toString())
    }

    // #1527: a HÁROM hivatalos hibaág (plusz a másolat azonosság-ága).
    // Egy ág = egy mondat; a lemezhiba a FÁJLNEVET és a HIBAKÓDOT is
    // kiírja, mert csak abból derül ki, melyik lemezen mi történt.
    Dialog {
        id: saveErrorDialog
        objectName: "saveErrorDialog"
        title: qsTr("Save")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string kind: ""
        property string fileName: ""
        property int code: 0
        readonly property string message: {
            if (kind === "collision")
                //: CFileSaveThread:filesaveerr2
                return qsTr("Unable to save file due to filename collision.")
            if (kind === "same")
                //: IDS_CANT_SAVE_TO_SAME
                return qsTr("Cannot replace image. Please try again with a different filename.")
            if (kind === "format")
                //: CFileSaveThread:filesaveerr3
                return qsTr("Unable to save file due to a file format error.")
            //: CFileSaveThread::filesaveerr-win — %1 a fájlnév, %2 a hibakód
            return qsTr("Unable to save all files due to a disk error. The disk may be full or read-only.\n\n%1\nerror(%2)")
                   .arg(saveErrorDialog.fileName).arg(saveErrorDialog.code)
        }
        Text {
            objectName: "saveErrorMessage"
            width: 380
            wrapMode: Text.WordWrap
            text: saveErrorDialog.message
            font.pixelSize: Theme.fontSize
            color: Theme.ink
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
        // #1527: a besorolt hibaág — a hivatalos, ágspecifikus mondat
        function onSaveErrorOccurred(kind, fileName, code) {
            saveErrorDialog.kind = kind
            saveErrorDialog.fileName = fileName
            saveErrorDialog.code = code
            saveErrorDialog.open()
        }
    }
}
