import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Import forrásból (#23/#441): külső mappa (pl. fényképezőgép/kártya
// csatolt mappája, vagy bármely más mappa) képeinek/videóinak másolása a
// könyvtárba — a Mappakezelő/DedupDialog mintájára ÖNÁLLÓ, mozgatható/
// átméretezhető ablak (nem a főablakba ékelt Dialog).
//
// #441 — a mai szabad szöveges mappa-sablon mező helyett HÁROM célmappa-
// elnevezési mód (namingMode: "manual" | "date" | "today"), duplikátum-
// kizárás (autoExclude, a jelölt-előnézetben "duplicate"/"excluded"
// zászlókkal), egyenkénti válogatás, és háromállapotú, kétlépcsős
// megerősítésű forrás-törlés ("After Copying:").
Window {
    id: importSourceWindow
    objectName: "importSourceDialog"
    title: qsTr("Import from Source")
    modality: Qt.ApplicationModal
    width: 640
    height: 680
    minimumWidth: 480
    minimumHeight: 480
    color: Theme.canvasBg

    // a forrás/cél FolderDialog `selectedFolder.toString()`-ja (file:// URL
    // is lehet) — a Pythonnak MINDIG ezt a nyers alakot adjuk át, a
    // `to_local_path` ott alakítja lokális útvonallá (a Mappakezelő
    // `addWatchedFolder`-jének mintája); a felület a megjelenítéshez
    // egyszerűen lehántja a "file://" előtagot.
    property string sourceFolder: ""
    property string destFolder: ""

    // #441: a HÁROM célmappa-elnevezési mód — a `picasapy.importsource.
    // NAMING_*` konstansaival egyező string. A dátum szerinti bontás a
    // Picasa import-munkafolyamatának lelke, ezért ez az alapértelmezés.
    property string namingMode: "date"
    property string manualFolderName: ""

    // #441: "After Copying:" — a `picasapy.app.import_source_controller.
    // AFTER_COPY_*` konstansaival egyező string.
    property string afterCopying: "leave"

    property bool scanning: false
    // előnézeti elemek — dict-ek listája: {path, thumbUrl, duplicate,
    // excluded}; a controller MINDIG listát ad (soha tuple-t, ld.
    // MEMORY.md-tanulság)
    property var previewItems: []
    property int previewCount: 0
    readonly property int duplicateCount: {
        var count = 0
        for (var i = 0; i < importSourceWindow.previewItems.length; i++) {
            if (importSourceWindow.previewItems[i].duplicate) count++
        }
        return count
    }
    readonly property int includedCount: {
        var count = 0
        for (var j = 0; j < importSourceWindow.previewItems.length; j++) {
            if (!importSourceWindow.previewItems[j].excluded) count++
        }
        return count
    }

    property bool importing: false
    property int importDone: 0
    property int importTotal: 0
    // -1: még nem futott import ebben a munkamenetben (az eredmény-sor rejtve)
    property int lastCopiedCount: -1
    property int lastFailedCount: -1

    property string lastError: ""

    readonly property string sourceFolderDisplay:
        importSourceWindow.sourceFolder.replace(/^file:\/\//, "")
    readonly property string destFolderDisplay:
        importSourceWindow.destFolder.replace(/^file:\/\//, "")

    function open() { importSourceWindow.visible = true }

    // a forrás (rekurzív) beolvasása háttérszálon — a FolderDialog
    // elfogadásakor és tesztből is hívható (a DedupDialog `scan()` mintája)
    function scanCurrentSource() {
        importSourceWindow.lastError = ""
        importSourceWindow.previewItems = []
        importSourceWindow.previewCount = 0
        importSourceWindow.lastCopiedCount = -1
        importSourceWindow.lastFailedCount = -1
        if (importSourceWindow.sourceFolder.length === 0) return
        importSourceWindow.scanning = true
        importSourceController.scanSource(importSourceWindow.sourceFolder)
    }

    // #441: a másolás tényleges indítása — a kétlépcsős megerősítés (ld.
    // lent, `requestImport`) UTÁN hívódik.
    function runImportNow() {
        importSourceWindow.lastError = ""
        importSourceController.runImport(
            importSourceWindow.destFolder,
            importSourceWindow.namingMode,
            importSourceWindow.manualFolderName,
            importSourceWindow.afterCopying)
    }

    // #441: "After Copying:" — kétlépcsős, egyre erősebb megerősítés a
    // törléssel járó két állapotnál; "Leave card alone"-nál nincs kérdés.
    function requestImport() {
        if (importSourceWindow.destFolder.length === 0) return
        if (importSourceWindow.includedCount === 0) return
        if (importSourceWindow.afterCopying === "leave") {
            importSourceWindow.runImportNow()
            return
        }
        removeImportedConfirm.ask("importSourceRemoveImported", qsTr(
            "Are you sure you want to remove the imported files from your "
            + "card? This cannot be undone."))
    }

    Connections {
        target: typeof importSourceController !== "undefined"
                ? importSourceController : null
        function onSourceScanFinished(items, count) {
            importSourceWindow.previewItems = items
            importSourceWindow.previewCount = count
            importSourceWindow.scanning = false
        }
        function onSourceScanFailed(message) {
            importSourceWindow.lastError = message
            importSourceWindow.scanning = false
        }
        function onSelectionChanged(items) {
            importSourceWindow.previewItems = items
        }
        function onImportStarted(total) {
            importSourceWindow.importing = true
            importSourceWindow.importDone = 0
            importSourceWindow.importTotal = total
        }
        function onImportProgress(done, total) {
            importSourceWindow.importDone = done
            importSourceWindow.importTotal = total
        }
        function onImportFailedDetails(details) {
            importSourceWindow.lastError = details.join("\n")
        }
        function onImportFinished(copied, failed) {
            importSourceWindow.importing = false
            importSourceWindow.lastCopiedCount = copied
            importSourceWindow.lastFailedCount = failed
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr(
                "Import pictures and videos from another folder (e.g. a "
                + "mounted camera or memory card) into your library.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        // -- forrás ------------------------------------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                text: qsTr("Source:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                objectName: "importSourcePathText"
                Layout.fillWidth: true
                elide: Text.ElideMiddle
                text: importSourceWindow.sourceFolderDisplay.length > 0
                      ? importSourceWindow.sourceFolderDisplay
                      : qsTr("(none selected)")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaButton {
                objectName: "importSourceChooseSourceButton"
                text: qsTr("Browse...")
                onClicked: sourceFolderDialog.open()
            }
        }

        // #441: "Exclude Duplicates" — "Exclude photos that are already
        // imported into Picasa" (autoexclude QSettings-kulcs, a
        // controller property-je).
        CheckBox {
            objectName: "importSourceAutoExcludeCheckBox"
            text: qsTr("Exclude Duplicates")
            checked: typeof importSourceController !== "undefined"
                     && importSourceController
                     ? importSourceController.autoExclude : false
            onToggled: importSourceController.setAutoExclude(checked)
        }
        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Exclude photos that are already imported into Picasa")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        Text {
            objectName: "importSourceDuplicateCountText"
            visible: importSourceWindow.duplicateCount > 0
            text: qsTr("%n of those are duplicates already in Picasa", "",
                       importSourceWindow.duplicateCount)
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        Text {
            objectName: "importSourceErrorText"
            visible: importSourceWindow.lastError.length > 0
            text: importSourceWindow.lastError
            color: Theme.brandRed
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        BusyIndicator {
            objectName: "importSourceBusyIndicator"
            Layout.alignment: Qt.AlignHCenter
            running: importSourceWindow.scanning
            visible: importSourceWindow.scanning
        }

        Text {
            objectName: "importSourceCountText"
            visible: !importSourceWindow.scanning && importSourceWindow.previewCount > 0
            text: qsTr("%1 pictures/videos found").arg(importSourceWindow.previewCount)
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        Text {
            objectName: "importSourceEmptyText"
            visible: !importSourceWindow.scanning
                     && importSourceWindow.sourceFolder.length > 0
                     && importSourceWindow.previewCount === 0
                     && importSourceWindow.lastError.length === 0
            text: qsTr("No pictures or videos found in this folder.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        // -- egyenkénti válogatás parancsai (#441) -------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: importSourceWindow.previewCount > 0
            PicasaButton {
                objectName: "importSourceExcludeAllButton"
                text: qsTr("Exclude All")
                onClicked: importSourceController.excludeAll()
            }
            PicasaButton {
                objectName: "importSourceIncludeAllButton"
                text: qsTr("Include All")
                onClicked: importSourceController.includeAll()
            }
            Item { Layout.fillWidth: true }
        }

        // -- előnézeti bélyegkép-rács -------------------------------------
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 110
            color: Theme.contentPanel
            border.color: Theme.chromeBorder

            GridView {
                id: previewGrid
                objectName: "importSourcePreviewGrid"
                anchors.fill: parent
                anchors.margins: 4
                clip: true
                cellWidth: 76
                cellHeight: 92
                model: importSourceWindow.previewItems
                delegate: Rectangle {
                    id: thumbFrame
                    required property var modelData
                    required property int index
                    objectName: "importSourceThumb:" + thumbFrame.index
                    width: 72
                    height: 72
                    color: Theme.thumbCard
                    border.color: thumbFrame.modelData.duplicate
                                  ? Theme.brandRed : Theme.thumbBorder
                    border.width: thumbFrame.modelData.duplicate ? 2 : 1
                    opacity: thumbFrame.modelData.excluded ? 0.4 : 1.0

                    Image {
                        anchors.fill: parent
                        anchors.margins: 2
                        source: thumbFrame.modelData.thumbUrl
                        fillMode: Image.PreserveAspectFit
                        asynchronous: Qt.platform.pluginName !== "offscreen"
                    }

                    Text {
                        id: toggleLabel
                        objectName: "importSourceToggleLabel:" + thumbFrame.index
                        anchors.top: parent.bottom
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: thumbFrame.modelData.excluded
                              ? qsTr("Include") : qsTr("Exclude")
                        font.pixelSize: Theme.fontSize - 1
                        color: Theme.brandBlue
                    }
                    MouseArea {
                        objectName: "importSourceToggle:" + thumbFrame.index
                        anchors.fill: toggleLabel
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (thumbFrame.modelData.excluded) {
                                importSourceController.includeFile(
                                    thumbFrame.modelData.path)
                            } else {
                                importSourceController.excludeFile(
                                    thumbFrame.modelData.path)
                            }
                        }
                    }
                }
                ScrollBar.vertical: PicasaScrollBar {}
            }
        }

        // -- cél + célmappa-elnevezés (#441) -------------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                text: qsTr("Destination:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                objectName: "importSourceDestPathText"
                Layout.fillWidth: true
                elide: Text.ElideMiddle
                text: importSourceWindow.destFolderDisplay.length > 0
                      ? importSourceWindow.destFolderDisplay
                      : qsTr("(none selected)")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaButton {
                objectName: "importSourceChooseDestButton"
                text: qsTr("Browse...")
                onClicked: destFolderDialog.open()
            }
        }

        ButtonGroup { id: namingModeGroup }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            RadioButton {
                objectName: "importSourceNamingManualRadio"
                text: qsTr("Enter new folder title or choose existing folder to continue")
                ButtonGroup.group: namingModeGroup
                checked: importSourceWindow.namingMode === "manual"
                onToggled: if (checked) importSourceWindow.namingMode = "manual"
            }
            TextField {
                id: manualFolderField
                objectName: "importSourceManualNameField"
                Layout.fillWidth: true
                Layout.leftMargin: 24
                enabled: importSourceWindow.namingMode === "manual"
                text: importSourceWindow.manualFolderName
                onEditingFinished: importSourceWindow.manualFolderName = text
            }
            RadioButton {
                objectName: "importSourceNamingByDateRadio"
                text: qsTr("Import into separate folders for each date taken")
                ButtonGroup.group: namingModeGroup
                checked: importSourceWindow.namingMode === "date"
                onToggled: if (checked) importSourceWindow.namingMode = "date"
            }
            RadioButton {
                objectName: "importSourceNamingTodayRadio"
                text: qsTr("Import into folder with today's date")
                ButtonGroup.group: namingModeGroup
                checked: importSourceWindow.namingMode === "today"
                onToggled: if (checked) importSourceWindow.namingMode = "today"
            }
        }

        // -- "After Copying:" háromállapotú forrás-törlés (#441) -----------
        Text {
            text: qsTr("After Copying:")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
        }
        ButtonGroup { id: afterCopyingGroup }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            RadioButton {
                objectName: "importSourceAfterLeaveRadio"
                text: qsTr("Leave card alone")
                ButtonGroup.group: afterCopyingGroup
                checked: importSourceWindow.afterCopying === "leave"
                onToggled: if (checked) importSourceWindow.afterCopying = "leave"
            }
            RadioButton {
                objectName: "importSourceAfterDeleteCopiedRadio"
                text: qsTr("Delete only copied photos")
                ButtonGroup.group: afterCopyingGroup
                checked: importSourceWindow.afterCopying === "delete_copied"
                onToggled: if (checked) importSourceWindow.afterCopying = "delete_copied"
            }
            RadioButton {
                objectName: "importSourceAfterDeleteAllRadio"
                text: qsTr("Delete everything on card")
                ButtonGroup.group: afterCopyingGroup
                checked: importSourceWindow.afterCopying === "delete_all"
                onToggled: if (checked) importSourceWindow.afterCopying = "delete_all"
            }
        }

        // -- haladás -------------------------------------------------------
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            visible: importSourceWindow.importing
            radius: 4
            color: Theme.trackBg
            border.color: Theme.chromeBorder

            Rectangle {
                objectName: "importSourceProgressFill"
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                radius: parent.radius
                color: Theme.picasaGreen
                width: importSourceWindow.importTotal > 0
                       ? parent.width * importSourceWindow.importDone
                             / importSourceWindow.importTotal
                       : 0
            }
        }

        Text {
            objectName: "importSourceProgressText"
            visible: importSourceWindow.importing
            text: qsTr("%1 / %2 imported")
                  .arg(importSourceWindow.importDone)
                  .arg(importSourceWindow.importTotal)
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        Text {
            objectName: "importSourceResultText"
            visible: !importSourceWindow.importing
                     && importSourceWindow.lastCopiedCount >= 0
            text: qsTr("Done: %1 imported, %2 failed")
                  .arg(importSourceWindow.lastCopiedCount)
                  .arg(importSourceWindow.lastFailedCount)
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "importSourceStartButton"
                text: qsTr("Import")
                accent: Theme.picasaGreen
                enabled: importSourceWindow.includedCount > 0
                         && importSourceWindow.destFolder.length > 0
                         && !importSourceWindow.importing
                onClicked: importSourceWindow.requestImport()
            }
            PicasaButton {
                objectName: "importSourceCloseButton"
                text: qsTr("Close")
                onClicked: importSourceWindow.visible = false
            }
        }
    }

    FolderDialog {
        id: sourceFolderDialog
        title: qsTr("Choose source folder...")
        onAccepted: {
            importSourceWindow.sourceFolder = selectedFolder.toString()
            importSourceWindow.scanCurrentSource()
        }
    }

    FolderDialog {
        id: destFolderDialog
        title: qsTr("Choose destination folder...")
        onAccepted: importSourceWindow.destFolder = selectedFolder.toString()
    }

    // #441 — kétlépcsős, egyre erősebb megerősítés a forrás-törléshez.
    // 1. lépés: mindkét törléssel járó "After Copying:" állapotra közös,
    // generikus kérdés. "delete_all"-nál ezt követi a 2. lépés (erősebb
    // figyelmeztetés + "ne figyelmeztess többé"), "delete_copied"-nél a
    // 2. lépés kimarad — a #422 mintája szerint EGYEDI namePrefix.
    ConfirmDialog {
        id: removeImportedConfirm
        namePrefix: "importSourceRemoveImportedConfirm"
        title: qsTr("Import from Source")
        onConfirmed: {
            if (importSourceWindow.afterCopying === "delete_all") {
                deleteAllWarningConfirm.ask("importSourceDeleteAllWarning", qsTr(
                    "WARNING! You have chosen to delete ALL FILES…"))
            } else {
                importSourceWindow.runImportNow()
            }
        }
    }

    ConfirmDialog {
        id: deleteAllWarningConfirm
        namePrefix: "importSourceDeleteAllWarningConfirm"
        title: qsTr("Import from Source")
        onConfirmed: importSourceWindow.runImportNow()
    }
}
