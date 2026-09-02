import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Weboldal exportálása (#351, `webexport.fen`, docs/specs/
// picasa-fen-dialogs.md 3.12.): a kijelölt mappa/album exportja statikus
// HTML-galériává a Picasa `.tpl` sablonnyelvével (`picasapy.webexport`).
//
// A FEN-eredetiben van egy élő `printpreview` sablon-előnézet — ez itt
// KIMARADT (a motor a lényeg, nem a sablonválasztó UI-csiszolása); helyette
// a sablon neve/leírása szöveges. Önálló, mozgatható/átméretezhető Window
// (a MoveDatabaseDialog/#368 mintája) — a `Main.qml`-be illesztés (menü-
// bekötés, `webExportController` context property) az integrátoré, ld. a
// `webexport_controller.py` docstringjét.
Window {
    id: webExportWindow
    objectName: "webExportDialog"
    title: qsTr("Export as HTML Page...")
    modality: Qt.ApplicationModal
    width: 520
    height: exporting || lastOutputFolder.length > 0 || lastError.length > 0 ? 420 : 360
    minimumWidth: 460
    minimumHeight: 320
    color: Theme.canvasBg

    // a `webexport.fen` cím-mezője ("edit") — a generált oldalak
    // <%albumName%>-je ez lesz
    property string albumTitle: ""
    property string targetFolder: ""
    property var templates: []          // [{id, name, description}, ...]
    property int templateIndex: 0
    readonly property string templateId:
        webExportWindow.templateIndex >= 0
        && webExportWindow.templateIndex < webExportWindow.templates.length
            ? webExportWindow.templates[webExportWindow.templateIndex].id : ""

    property bool exporting: false
    property int progressDone: 0
    property int progressTotal: 0

    property string lastError: ""
    property string lastOutputFolder: ""
    property int lastPageCount: 0

    function open() {
        webExportWindow.lastError = ""
        webExportWindow.lastOutputFolder = ""
        //: #1956: `typeof` a NÉVRE, `&&` az ÉRTÉKRE
        if (typeof webExportController !== "undefined"
                && webExportController) {
            webExportWindow.templates = webExportController.listWebExportTemplates()
        }
        webExportWindow.visible = true
    }

    function startExport() {
        if (webExportWindow.targetFolder.length === 0
            || webExportWindow.templateId.length === 0) return
        webExportWindow.lastError = ""
        webExportController.generateWebExport(
            webExportWindow.targetFolder,
            webExportWindow.templateId,
            webExportWindow.albumTitle,
            thumbSizeBox.sizeOptions[thumbSizeBox.currentIndex],
            imageSizeBox.sizeOptions[imageSizeBox.currentIndex],
            shadowThumbsCheck.checked,
            shadowImagesCheck.checked)
    }

    Connections {
        target: typeof webExportController !== "undefined" ? webExportController : null
        function onWebExportStarted() {
            webExportWindow.exporting = true
            webExportWindow.progressDone = 0
            webExportWindow.progressTotal = 0
        }
        function onWebExportProgress(done, total) {
            webExportWindow.progressDone = done
            webExportWindow.progressTotal = total
        }
        function onWebExportFinished(outputFolder, pageCount) {
            webExportWindow.exporting = false
            webExportWindow.lastOutputFolder = outputFolder
            webExportWindow.lastPageCount = pageCount
        }
        function onWebExportFailed(message) {
            webExportWindow.exporting = false
            webExportWindow.lastError = message
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        // -- cím (albumName override) --------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            enabled: !webExportWindow.exporting
            Text {
                text: qsTr("Page title:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: titleField
                objectName: "webExportTitleField"
                Layout.fillWidth: true
                text: webExportWindow.albumTitle
                onTextEdited: webExportWindow.albumTitle = text
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }

        // -- célmappa ---------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            enabled: !webExportWindow.exporting
            Text {
                text: qsTr("Save to:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text {
                    objectName: "webExportTargetText"
                    Layout.fillWidth: true
                    elide: Text.ElideMiddle
                    text: webExportWindow.targetFolder.length > 0
                          ? webExportWindow.targetFolder
                          : qsTr("(not selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    objectName: "webExportBrowseButton"
                    text: qsTr("Browse...")
                    onClicked: targetFolderDialog.open()
                }
            }
        }

        // -- sablon -------------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            enabled: !webExportWindow.exporting
            Text {
                text: qsTr("Template:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ComboBox {
                id: templateBox
                objectName: "webExportTemplateBox"
                Layout.fillWidth: true
                model: webExportWindow.templates.map(function(t) { return t.name })
                currentIndex: webExportWindow.templateIndex
                onActivated: webExportWindow.templateIndex = currentIndex
            }
            Text {
                objectName: "webExportTemplateDescription"
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: webExportWindow.templateIndex >= 0
                      && webExportWindow.templateIndex < webExportWindow.templates.length
                      ? webExportWindow.templates[webExportWindow.templateIndex].description : ""
                font.pixelSize: Theme.fontSize - 1
                color: Theme.textGray
            }
        }

        // -- méretek ------------------------------------------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: 16
            enabled: !webExportWindow.exporting
            ColumnLayout {
                spacing: 2
                Text {
                    text: qsTr("Thumbnail size:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                ComboBox {
                    id: thumbSizeBox
                    objectName: "webExportThumbSizeBox"
                    readonly property var sizeOptions: [0, 100, 160, 200, 320]
                    Layout.preferredWidth: 160
                    model: [qsTr("Original size"), "100 px", "160 px", "200 px", "320 px"]
                    currentIndex: 3
                }
            }
            ColumnLayout {
                spacing: 2
                Text {
                    text: qsTr("Picture size:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                ComboBox {
                    id: imageSizeBox
                    objectName: "webExportImageSizeBox"
                    readonly property var sizeOptions: [0, 640, 800, 1024, 1600]
                    Layout.preferredWidth: 160
                    model: [qsTr("Original size"), "640 px", "800 px", "1024 px", "1600 px"]
                    currentIndex: 2
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 16
            enabled: !webExportWindow.exporting
            CheckBox {
                id: shadowThumbsCheck
                objectName: "webExportShadowThumbsCheck"
                text: qsTr("Shadow thumbnails")
                checked: true
            }
            CheckBox {
                id: shadowImagesCheck
                objectName: "webExportShadowImagesCheck"
                text: qsTr("Shadow pictures")
            }
        }

        Text {
            objectName: "webExportErrorText"
            visible: webExportWindow.lastError.length > 0
            text: webExportWindow.lastError
            color: Theme.brandRed
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // -- haladás-nézet --------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            visible: webExportWindow.exporting
            spacing: 6
            Text {
                text: qsTr("PicasaPy is generating the web page.")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 8
                radius: 4
                color: Theme.trackBg
                border.color: Theme.chromeBorder
                Rectangle {
                    objectName: "webExportProgressFill"
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    radius: parent.radius
                    color: Theme.picasaGreen
                    width: webExportWindow.progressTotal > 0
                           ? parent.width * webExportWindow.progressDone
                                 / webExportWindow.progressTotal
                           : 0
                }
            }
        }

        Text {
            objectName: "webExportResultText"
            visible: webExportWindow.lastOutputFolder.length > 0
            text: qsTr("Web page generated: %1 file(s) in %2")
                  .arg(webExportWindow.lastPageCount).arg(webExportWindow.lastOutputFolder)
            color: Theme.picasaGreen
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "webExportGenerateButton"
                text: qsTr("Create")
                accent: Theme.picasaGreen
                enabled: webExportWindow.targetFolder.length > 0
                         && webExportWindow.templateId.length > 0
                         && !webExportWindow.exporting
                onClicked: webExportWindow.startExport()
            }
            PicasaButton {
                objectName: "webExportCloseButton"
                text: qsTr("Close")
                enabled: !webExportWindow.exporting
                onClicked: webExportWindow.visible = false
            }
        }
    }

    FolderDialog {
        id: targetFolderDialog
        title: qsTr("Choose target folder...")
        onAccepted: webExportWindow.targetFolder = selectedFolder.toString()
    }
}
