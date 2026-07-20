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
        title: qsTr("Export Picture to Folder...")
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
        onOpened: standardButton(Dialog.Ok).enabled = Qt.binding(
            function() { return exportDialog.targetFolder.length > 0 })
        onAccepted: controller.exportRows(
            dialogs.appWindow.selectedIndexes, targetFolder,
            sizeOptions[exportSizeBox.currentIndex], exportQuality.value)
        ColumnLayout {
            spacing: 10
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Target folder:")
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
                SpinBox {
                    id: exportQuality
                    objectName: "exportQuality"
                    from: 1; to: 100; value: 85
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
        Text {
            text: exportResultDialog.message
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Connections {
        target: controller
        function onExportFinished(done, failed) {
            exportResultDialog.message = failed > 0
                ? qsTr("%1 pictures exported, %2 failed.")
                    .arg(done).arg(failed)
                : qsTr("%1 pictures exported.").arg(done)
            exportResultDialog.open()
        }
    }
}
