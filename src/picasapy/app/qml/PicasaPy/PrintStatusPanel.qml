import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Flickable {
    id: printStatusPanel
    property var printWindow
    property alias statusBox: printStatusBox
    objectName: "printStatusFlick"
    Layout.fillWidth: true
    Layout.preferredHeight: printStatusBox.implicitHeight
    Layout.maximumHeight: Math.max(60, printStatusPanel.printWindow.height / 3)
    visible: printStatusPanel.printWindow.lastSkipped.length > 0
             || printStatusPanel.printWindow.lastError.length > 0
             || printStatusPanel.printWindow.printTotalPages > 0
             || printStatusPanel.printWindow.lastResult.length > 0
    clip: true
    contentWidth: width
    contentHeight: printStatusBox.implicitHeight
    boundsBehavior: Flickable.StopAtBounds
    flickableDirection: Flickable.VerticalFlick
    ScrollBar.vertical: ScrollBar {
        policy: size < 1.0 ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
    }

    ColumnLayout {
        id: printStatusBox
        width: printStatusPanel.width
        spacing: 10

        Text {
            objectName: "printSkippedText"
            visible: printStatusPanel.printWindow.lastSkipped.length > 0
            text: qsTr("These pictures could not be printed: %1")
                  .arg(printStatusPanel.printWindow.lastSkipped.join(", "))
            color: Theme.brandRed
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Text {
            objectName: "printErrorText"
            visible: printStatusPanel.printWindow.lastError.length > 0
            text: printStatusPanel.printWindow.lastError
            color: Theme.brandRed
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // #3016: LAPONKÉNTI haladás. A festés a GUI-szálon fut (a mérés
        // szerint nem tolható háttérszálra: az a munka kétharmada, és a Qt
        // festő-API-ja a GUI-szálhoz kötött), ezért a vezérlő laponként
        // enged vissza a felületnek — enélkül a párbeszéd a feladat teljes
        // idejére befagyna, és a felhasználó nem tudná, dolgozik-e még.
        Text {
            objectName: "printProgressText"
            visible: printStatusPanel.printWindow.printTotalPages > 0
            text: qsTr("Printing: %1 / %2")
                .arg(printStatusPanel.printWindow.printDonePages)
                .arg(printStatusPanel.printWindow.printTotalPages)
            color: Theme.textDark
            font.pixelSize: Theme.fontSize
            Layout.fillWidth: true
        }

        Text {
            objectName: "printResultText"
            visible: printStatusPanel.printWindow.lastResult.length > 0
            text: qsTr("Finished: %1").arg(printStatusPanel.printWindow.lastResult)
            color: Theme.picasaGreen
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }
}
