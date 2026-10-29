import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: printFitPanel
    property var printWindow
    spacing: 10

    // -- illesztés ----------------------------------------------------
    // #1590: az indexképnél nincs értelme — ott MINDIG a teljes kép
    // látszik a cellában (ez az indexkép lényege), és a tájolást sem a
    // képek szabják meg, mert egy lapon sok kép van
    ColumnLayout {
        Layout.fillWidth: true
        visible: !printFitPanel.printWindow.contactSheet
        spacing: 2
        Text {
            text: qsTr("Fit to page:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        RowLayout {
            spacing: 16
            RadioButton {
                objectName: "printFitRadio"
                text: qsTr("Whole picture")
                checked: printFitPanel.printWindow.fitMode === "fit"
                onClicked: {
                    printFitPanel.printWindow.fitMode = "fit"
                    printFitPanel.printWindow.frissitsdAzElonezetet()
                }
            }
            RadioButton {
                objectName: "printFillRadio"
                text: qsTr("Fill the page (crop)")
                checked: printFitPanel.printWindow.fitMode === "fill"
                onClicked: {
                    printFitPanel.printWindow.fitMode = "fill"
                    printFitPanel.printWindow.frissitsdAzElonezetet()
                }
            }
        }
    }

    // -- tájolás ------------------------------------------------------
    ColumnLayout {
        Layout.fillWidth: true
        visible: !printFitPanel.printWindow.contactSheet
        spacing: 2
        Text {
            text: qsTr("Orientation:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        PicasaComboBox {
            id: orientationBox
            objectName: "printOrientationBox"
            readonly property var values: ["auto", "portrait", "landscape"]
            Layout.preferredWidth: 200
            model: [qsTr("Automatic"), qsTr("Portrait"), qsTr("Landscape")]
            currentIndex: 0
            onActivated: printFitPanel.printWindow.orientation = values[currentIndex]
        }
    }
}
