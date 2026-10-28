import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    id: printButtonRow
    property var printWindow
    property var printWindowHelp
    Layout.fillWidth: true
    spacing: 8
    PicasaButton {
        objectName: "printHelpButton"
        text: qsTr("Help")
        onClicked: printButtonRow.printWindowHelp.nyisdASugot(
            printButtonRow.printWindow.helpTopic)
    }
    Item { Layout.fillWidth: true }
    PicasaButton {
        objectName: "printStartButton"
        text: qsTr("Print")
        accent: Theme.picasaGreen
        enabled: printButtonRow.printWindow.canPrint
        onClicked: printButtonRow.printWindow.startPrint()
    }
    PicasaButton {
        objectName: "printCloseButton"
        text: qsTr("Close")
        onClicked: printButtonRow.printWindow.visible = false
    }
}
