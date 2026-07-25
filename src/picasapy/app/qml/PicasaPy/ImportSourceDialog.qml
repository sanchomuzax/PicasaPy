import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Import forrásból (#23): külső mappa (pl. fényképezőgép/kártya csatolt
// mappája, vagy bármely más mappa) képeinek/videóinak másolása/áthelyezése
// a könyvtárba, dátum szerinti mappa-sablonnal — a Mappakezelő/DedupDialog
// mintájára ÖNÁLLÓ, mozgatható/átméretezhető ablak (nem a főablakba ékelt
// Dialog).
//
// Alapértelmezés NEM-DESZTRUKTÍV (#23 DoD): másolás — a forrás (kártya/
// mappa) érintetlen marad; az áthelyezés kapcsoló (`moveInsteadOfCopy`)
// explicit bekapcsolást igényel. A mappa-sablon józan alapértelmezése
// "év/év-hónap-nap" (`{YYYY}/{YYYY}-{MM}-{DD}`, a kép EXIF-dátuma vagy
// hiányában a fájl módosítási ideje alapján — ld. `picasapy.importsource`).
Window {
    id: importSourceWindow
    objectName: "importSourceDialog"
    title: qsTr("Import from Source")
    modality: Qt.ApplicationModal
    width: 640
    height: 560
    minimumWidth: 480
    minimumHeight: 420
    color: Theme.canvasBg

    // a forrás/cél FolderDialog `selectedFolder.toString()`-ja (file:// URL
    // is lehet) — a Pythonnak MINDIG ezt a nyers alakot adjuk át, a
    // `to_local_path` ott alakítja lokális útvonallá (a Mappakezelő
    // `addWatchedFolder`-jének mintája); a felület a megjelenítéshez
    // egyszerűen lehántja a "file://" előtagot.
    property string sourceFolder: ""
    property string destFolder: ""
    property string template: "{YYYY}/{YYYY}-{MM}-{DD}"
    property bool moveInsteadOfCopy: false

    property bool scanning: false
    // előnézeti elemek — dict-ek listája: {path, thumbUrl}; a controller
    // MINDIG listát ad (soha tuple-t, ld. MEMORY.md-tanulság)
    property var previewItems: []
    property int previewCount: 0

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

    function startImport() {
        if (importSourceWindow.destFolder.length === 0) return
        if (importSourceWindow.previewCount === 0) return
        importSourceWindow.lastError = ""
        importSourceController.runImport(
            importSourceWindow.destFolder,
            importSourceWindow.template,
            importSourceWindow.moveInsteadOfCopy)
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
                cellHeight: 76
                model: importSourceWindow.previewItems
                delegate: Rectangle {
                    id: previewCell
                    required property var modelData
                    required property int index
                    objectName: "importSourceThumb:" + previewCell.index
                    width: 72
                    height: 72
                    color: Theme.thumbCard
                    border.color: Theme.thumbBorder
                    border.width: 1
                    Image {
                        anchors.fill: parent
                        anchors.margins: 2
                        source: previewCell.modelData.thumbUrl
                        fillMode: Image.PreserveAspectFit
                        asynchronous: Qt.platform.pluginName !== "offscreen"
                    }
                }
                ScrollBar.vertical: PicasaScrollBar {}
            }
        }

        // -- cél + mappa-sablon --------------------------------------------
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

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                text: qsTr("Folder template:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: templateField
                objectName: "importSourceTemplateField"
                Layout.fillWidth: true
                font.pixelSize: Theme.fontSize
                text: importSourceWindow.template
                onEditingFinished: importSourceWindow.template = text
            }
        }

        CheckBox {
            objectName: "importSourceMoveCheckBox"
            text: qsTr("Move instead of copy (source files will be deleted)")
            checked: importSourceWindow.moveInsteadOfCopy
            onToggled: importSourceWindow.moveInsteadOfCopy = checked
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
                enabled: importSourceWindow.previewCount > 0
                         && importSourceWindow.destFolder.length > 0
                         && !importSourceWindow.importing
                onClicked: importSourceWindow.startImport()
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
}
