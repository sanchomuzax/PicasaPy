import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: printPrinterPanel
    property var printWindow
    property var pdfTargetDialog
    property bool details: false
    readonly property int currentIndex: printPrinterPanel.comboBox
        ? printPrinterPanel.comboBox.currentIndex : 0
    readonly property var comboBox: !details && contentLoader.item
        ? contentLoader.item.comboBox : null
    implicitWidth: contentLoader.implicitWidth
    implicitHeight: contentLoader.implicitHeight

    Loader {
        id: contentLoader
        anchors.fill: parent
        sourceComponent: printPrinterPanel.details
            ? printerDetails : printerSelector
    }

    Component {
        id: printerSelector
        ColumnLayout {
            id: selector
            property alias comboBox: printerBox
            spacing: 2
            Text {
                text: qsTr("Printer:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: printerBox
                objectName: "printPrinterBox"
                Layout.fillWidth: true
                model: [qsTr("Print to a PDF file...")].concat(
                    printPrinterPanel.printWindow.printers)
                // a `currentIndex` a választó SAJÁTJA — a párbeszéd innen
                // olvassa (`printerIndex`), nem fordítva (ld. ott)
            }

            // #2103: belépési pont a nyomtató SAJÁT beállításaihoz
            // (`printpanel/psetupbutton`). Az eredetiben az illesztőprogram
            // tulajdonságlapját nyitja; itt a Qt oldalbeállítóját.
            PicasaButton {
                objectName: "printPrinterSetupButton"
                text: qsTr("Printer Setup")
                enabled: !printPrinterPanel.printWindow.pdfSelected
                ToolTip.text: qsTr(
                    "Open printer setup controls for the selected printer")
                ToolTip.visible: hovered
                ToolTip.delay: Theme.tooltipDelay
                onClicked: {
                    if (typeof printController !== "undefined" && printController) {
                        printController.openPrinterSetup(
                            printPrinterPanel.printWindow.printerName)
                        printPrinterPanel.printWindow.frissitsdAPapiradatot()
                    }
                }
            }
        }
    }

    Component {
        id: printerDetails
        ColumnLayout {
            spacing: 10
            // -- papíradat (#2368) ---------------------------------------
            // Az eredeti panel `printpanel/paperinfo` mezője: tisztán
            // SZÖVEGES kijelző a nyomtató neve mellett (az állapotfrissítő,
            // `0x00745980`, mind a négy információs mezőt ugyanazzal a
            // szövegbeállítóval tölti). Innen látja a felhasználó, MILYEN
            // LAPRA fog nyomtatni — a nyomat mérete és a „kis kép"
            // figyelmeztetés is ettől függ.
            Text {
                objectName: "printPaperInfoText"
                Layout.fillWidth: true
                elide: Text.ElideRight
                text: printPrinterPanel.printWindow.papiradat
                font.pixelSize: Theme.fontSizeLadder[0]
                color: Theme.textGray
            }

            // -- a PDF célfájlja (csak PDF-módban) ------------------------
            RowLayout {
                Layout.fillWidth: true
                visible: printPrinterPanel.printWindow.pdfSelected
                spacing: 8
                Text {
                    objectName: "printPdfTargetText"
                    Layout.fillWidth: true
                    elide: Text.ElideMiddle
                    text: printPrinterPanel.printWindow.pdfTarget.length > 0
                        ? printPrinterPanel.printWindow.pdfTarget
                        : qsTr("(not selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    objectName: "printPdfBrowseButton"
                    text: qsTr("Browse...")
                    onClicked: printPrinterPanel.pdfTargetDialog.open()
                }
            }
        }
    }
}
