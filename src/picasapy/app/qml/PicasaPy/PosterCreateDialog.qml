import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

Dialog {
    id: posterDialog
    required property var appWindow
    objectName: "posterDialog"
    title: qsTr("Poster Settings")
    modal: true
    focus: true
    anchors.centerIn: parent
    width: Math.min(440, posterDialog.appWindow.width - 32)
    standardButtons: Dialog.NoButton
    property string sourcePath: ""
    readonly property var paperOptions: {
        var sizes = typeof controller !== "undefined" && controller
                && typeof controller.posterPaperSizes === "function"
                ? controller.posterPaperSizes() : ["4x6", "8.5x11"]
        var options = []
        for (var i = 0; i < sizes.length; ++i)
            options.push({key: sizes[i], label: posterPaperLabel(sizes[i])})
        return options
    }

    function posterPaperLabel(key) {
        if (key === "4x6") return qsTr("4x6")
        if (key === "8.5x11") return qsTr("8.5x11")
        if (key === "10x15") return qsTr("10x15")
        if (key === "20x25") return qsTr("20x25")
        return key
    }

    function openForSource(path) {
        sourcePath = String(path || "")
        posterSizeBox.currentIndex = 0
        posterPaperBox.currentIndex = 0
        if (typeof controller !== "undefined" && controller
                && typeof controller.posterPaperSize === "function") {
            var preferredPaper = controller.posterPaperSize()
            for (var i = 0; i < paperOptions.length; ++i) {
                if (paperOptions[i].key === preferredPaper) {
                    posterPaperBox.currentIndex = i
                    break
                }
            }
        }
        posterOverlapCheck.checked = false
        open()
    }

    onAccepted: {
        if (!(typeof controller !== "undefined" && controller)
                || sourcePath.length === 0) return
        var paper = paperOptions[posterPaperBox.currentIndex].key
        if (typeof controller.setPosterPaperSize === "function")
            controller.setPosterPaperSize(paper)
        controller.createPoster(
            sourcePath, 200 + posterSizeBox.currentIndex * 100,
            paper, posterOverlapCheck.checked)
    }

    ColumnLayout {
        spacing: 12

        Text {
            objectName: "posterTip"
            Layout.fillWidth: true
            text: qsTr("Tip: if you don't want to trim, crop your picture to the same size as the paper.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        RowLayout {
            Layout.fillWidth: true
            Text {
                objectName: "posterSizeLabel"
                text: qsTr("Poster size:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: posterSizeBox
                objectName: "posterSizeBox"
                Layout.fillWidth: true
                model: [qsTr("200%"), qsTr("300%"), qsTr("400%"),
                        qsTr("500%"), qsTr("600%"), qsTr("700%"),
                        qsTr("800%"), qsTr("900%"), qsTr("1000%")]
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Text {
                objectName: "posterPaperLabel"
                text: qsTr("Paper size:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: posterPaperBox
                objectName: "posterPaperBox"
                Layout.fillWidth: true
                textRole: "label"
                model: posterDialog.paperOptions
            }
        }

        CheckBox {
            id: posterOverlapCheck
            objectName: "posterOverlapCheck"
            text: qsTr("Overlap tiles")
            font.pixelSize: Theme.fontSize
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8
            PicasaButton {
                objectName: "posterAcceptButton"
                text: qsTr("OK")
                accent: Theme.picasaGreen
                onClicked: posterDialog.accept()
            }
            PicasaButton {
                objectName: "posterCancelButton"
                text: qsTr("Cancel")
                onClicked: posterDialog.reject()
            }
        }
    }
}
