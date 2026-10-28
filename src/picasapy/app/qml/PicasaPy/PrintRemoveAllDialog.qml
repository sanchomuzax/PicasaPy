import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: printRemoveAllDialog
    property var printWindow
    objectName: "printRemoveAllDialog"
    parent: Overlay.overlay
    anchors.centerIn: parent
    modal: true
    closePolicy: Popup.CloseOnEscape
    // a nyomtatási ablak saját palettája sötét lehet: a háttér a téma
    // tartalompaneljéé, mint a többi kérdésé
    background: Rectangle {
        color: Theme.contentPanel
        border.width: 1
        border.color: Theme.chromeBorder
    }

    ColumnLayout {
        spacing: 12

        Text {
            objectName: "printRemoveAllMessage"
            Layout.preferredWidth: 340
            text: qsTr("This will remove all of your pictures and cancel printing. Would you like to continue?")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8

            PicasaButton {
                objectName: "printRemoveAllYesButton"
                text: qsTr("Remove and Cancel")
                onClicked: {
                    printRemoveAllDialog.close()
                    printRemoveAllDialog.printWindow.removeAllReviewPicturesAndCancel()
                }
            }
            PicasaButton {
                objectName: "printRemoveAllNoButton"
                text: qsTr("Don't Remove")
                onClicked: printRemoveAllDialog.close()
            }
        }
    }
}
