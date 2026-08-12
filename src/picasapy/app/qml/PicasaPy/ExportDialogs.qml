import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Exportálás mappába (#16, Ctrl+Shift+S; #150-ben kiemelve a Main.qml-ből):
// beállítás-dialógus (célmappa, méret, minőség), mappaválasztó és a
// háttérszálas export végeredmény-dialógusa (controller.exportFinished).
Item {
    id: dialogs
    anchors.fill: parent

    // a főablak (a kijelölt sorok forrása)
    required property var appWindow

    function openForSelection() {
        exportDialog.openForSelection()
    }

    Dialog {
        id: exportDialog
        objectName: "exportDialog"
        // #350 (export.fen paritás): a FEN forrás címe "Export to Folder" —
        // az app eddigi elnevezési konvencióját (három pont a végén) megtartva
        title: qsTr("Export to Folder...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string targetFolder: ""
        // a méret-lista indexei → leghosszabb oldal px-ben (0 = eredeti)
        readonly property var sizeOptions: [0, 2048, 1600, 1024, 800]
        function openForSelection() {
            if (dialogs.appWindow.selectedIndexes.length === 0) return
            open()
        }
        // tesztelhetőség: ld. renameDialog.acceptButtonText() megjegyzése
        function acceptButtonText() {
            return standardButton(Dialog.Ok) ? standardButton(Dialog.Ok).text : ""
        }
        // #369 (export.fen paritás): a "Name of exported folder:" mező
        // opcionális — üresen a célmappa változatlanul a browse-szal
        // választott hely (a régi viselkedés), kitöltve alá-mappaként jön
        // létre (az exporter mkdir(parents=True)-ja már ma is kezeli).
        function resolvedTargetFolder() {
            var name = exportFolderNameField.text
            if (name.length === 0) return targetFolder
            var sep = targetFolder.endsWith("/") ? "" : "/"
            return targetFolder + sep + name
        }
        onOpened: {
            standardButton(Dialog.Ok).enabled = Qt.binding(
                function() { return exportDialog.targetFolder.length > 0 })
            // #350 (export.fen paritás): a FEN accept gombjának felirata
            // "Export", nem generikus "OK"
            standardButton(Dialog.Ok).text = qsTr("Export")
        }
        // #369: a lenyíló megjelenített (fordítható) szövege és a
        // resolveExportQuality-nak átadott kulcs szándékosan külön —
        // a logika így nem törik el, ha a szöveg egyszer lefordítódik.
        readonly property var qualityPresetKeys:
            ["automatic", "normal", "maximum", "minimum", "custom"]
        onAccepted: controller.exportRows(
            dialogs.appWindow.selectedIndexes, resolvedTargetFolder(),
            sizeOptions[exportSizeBox.currentIndex],
            controller.resolveExportQuality(
                qualityPresetKeys[exportQualityPreset.currentIndex],
                exportQuality.value),
            exportAddNumbersCheck.checked,
            exportWatermarkCheck.checked ? exportWatermarkField.text : "")
        ColumnLayout {
            spacing: 10
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Export location:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                Text {
                    objectName: "exportTargetLabel"
                    Layout.preferredWidth: 240
                    elide: Text.ElideMiddle
                    text: exportDialog.targetFolder.length > 0
                          ? exportDialog.targetFolder
                          : qsTr("(not selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    text: qsTr("Browse...")
                    onClicked: exportTargetDialog.open()
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Name of exported folder:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                TextField {
                    id: exportFolderNameField
                    objectName: "exportFolderNameField"
                    Layout.preferredWidth: 180
                    // #422: jobbklikk-menü (Picasa `Address`)
                    TextFieldContextArea {}
                }
            }
            CheckBox {
                id: exportAddNumbersCheck
                objectName: "exportAddNumbersCheck"
                text: qsTr("Add numbers to file names to preserve order")
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Image size:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                ComboBox {
                    id: exportSizeBox
                    objectName: "exportSizeBox"
                    Layout.preferredWidth: 160
                    model: [qsTr("Original size"), "2048 px", "1600 px",
                            "1024 px", "800 px"]
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Image quality:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                ComboBox {
                    id: exportQualityPreset
                    objectName: "exportQualityPreset"
                    Layout.preferredWidth: 130
                    model: [qsTr("Automatic"), qsTr("Normal"),
                            qsTr("Maximum"), qsTr("Minimum"), qsTr("Custom")]
                    currentIndex: 1  // Normal — a korábbi, mindig-küldött 85 alapértelmezéssel egyező
                }
                SpinBox {
                    id: exportQuality
                    objectName: "exportQuality"
                    from: 1; to: 100; value: 85
                    // #369: csak "Custom" presetnél számít az érték, ekkor
                    // aktív — az exportRows-nak enélkül is mindig átadjuk
                    // (resolveExportQuality a nem-custom preseteknél eldobja).
                    enabled: exportQualityPreset.currentIndex === 4
                }
            }
            ColumnLayout {
                spacing: 4
                CheckBox {
                    id: exportWatermarkCheck
                    objectName: "exportWatermarkCheck"
                    text: qsTr("Add watermark")
                }
                RowLayout {
                    spacing: 8
                    Item { Layout.preferredWidth: 20 }  // behúzás (a FEN "indent" spacere)
                    TextField {
                        id: exportWatermarkField
                        objectName: "exportWatermarkField"
                        Layout.preferredWidth: 200
                        enabled: exportWatermarkCheck.checked
                        // #422: jobbklikk-menü (Picasa `Address`)
                        TextFieldContextArea {}
                    }
                }
            }
        }
    }

    FolderDialog {
        id: exportTargetDialog
        title: qsTr("Export Picture to Folder...")
        onAccepted: exportDialog.targetFolder = selectedFolder.toString()
    }

    Dialog {
        id: exportResultDialog
        objectName: "exportResultDialog"
        title: qsTr("Export")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        property var failedDetails: []
        Text {
            objectName: "exportResultText"
            text: exportResultDialog.message
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Connections {
        target: controller
        // #136: a sikertelen fájlok neve/oka a számszerű összegzés ELŐTT
        // érkezik — a dialógus szövegébe fűzzük, hogy a felhasználó lássa,
        // melyik fájl és miért hiúsult meg, ne csak a darabszámot.
        function onExportFailedDetails(details) {
            exportResultDialog.failedDetails = details
        }
        function onExportFinished(done, failed) {
            var message = failed > 0
                ? qsTr("%1 pictures exported, %2 failed.").arg(done).arg(failed)
                : qsTr("%1 pictures exported.").arg(done)
            if (exportResultDialog.failedDetails.length > 0)
                message += "\n" + exportResultDialog.failedDetails.join("\n")
            exportResultDialog.message = message
            exportResultDialog.failedDetails = []
            exportResultDialog.open()
        }
    }
}
