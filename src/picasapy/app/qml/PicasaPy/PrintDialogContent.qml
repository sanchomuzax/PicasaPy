import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A nyomtatási párbeszéd görgethető és rögzített nézetrészei.
Item {
    id: contentRoot
    required property var hostWindow
    required property var hostWindowHelp
    required property var hostOptionsPanel
    required property var hostPdfTargetDialog
    required property var hostReviewPanel
    property alias settingsPanel: printSettingsPanel
    property alias printerPanel: printPrinterPanel
    property alias statusPanel: printStatusPanel
    property alias buttonRow: printButtonRow
    property alias content: printContent
    property alias frame: printFrame

    // #4795: a gombsor (Súgó/Nyomtatás/Bezárás) az ablak alján RÖGZÍTETT, a
    // fölötte lévő tartalom görgethető — kis képernyőn sem lóg ki a gomb.
    ColumnLayout {
        id: printFrame
        anchors.fill: parent
        anchors.margins: hostWindow.keretMargo
        spacing: 10

        Flickable {
            id: printContentFlick
            objectName: "printContentFlick"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 60
            clip: true
            contentWidth: width
            contentHeight: printContent.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.VerticalFlick
            ScrollBar.vertical: ScrollBar {
                id: printScrollBar
                policy: size < 1.0 ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
            }

        ColumnLayout {
            id: printContent
            width: printContentFlick.width - (printScrollBar.visible ? printScrollBar.width : 0)
            spacing: 10

            PrintSelectionPanel {
                Layout.fillWidth: true
                printWindow: hostWindow
            }

            PrintSettingsPanel {
                id: printSettingsPanel
                Layout.fillWidth: true
                printWindow: hostWindow
                printOptionsPanel: hostOptionsPanel
                printAreaVisible: !hostWindow.contactSheet

                // #1819: KÉPENKÉNTI példányszám.
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        text: qsTr("Copies of each picture:")
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                    }
                    PicasaButton {
                        objectName: "printCopiesMinusButton"
                        text: "–"
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 22
                        enabled: hostWindow.copies > 1
                        onClicked: {
                            hostWindow.copies -= 1
                            hostWindow.frissitsdAzElonezetet()
                        }
                    }
                    Text {
                        objectName: "printCopiesText"
                        text: hostWindow.copies
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                        Layout.minimumWidth: 20
                        horizontalAlignment: Text.AlignHCenter
                    }
                    PicasaButton {
                        objectName: "printCopiesPlusButton"
                        text: "+"
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 22
                        ToolTip.text: qsTr(
                            "Add another copy of each Photo to be printed")
                        ToolTip.visible: hovered
                        ToolTip.delay: Theme.tooltipDelay
                        onClicked: {
                            hostWindow.copies += 1
                            hostWindow.frissitsdAzElonezetet()
                        }
                    }
                    Item { Layout.fillWidth: true }
                }

                PrintPreviewPanel {
                    printWindow: hostWindow
                }

                Text {
                    objectName: "printQualityText"
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    font.pixelSize: Theme.fontSize
                    color: hostWindow.quality.ready === false
                           && hostWindow.quality.total > 0
                           ? Theme.brandRed : Theme.ink
                    text: {
                        var q = hostWindow.quality
                        if (!q || !q.total) return ""
                        var sor = qsTr("Smallest picture: %1 pixels/inch.")
                                      .arg(q.smallest)
                        if (q.small > 0) {
                            var mi = q.small === 1 ? qsTr("picture") : qsTr("pictures")
                            return sor + "\n"
                                   + qsTr("Please review before printing.\n%1 small %2 found.")
                                         .arg(q.small).arg(mi)
                        }
                        return sor + "\n" + qsTr("You are ready to print.")
                    }
                }

                PicasaButton {
                    objectName: "printReviewButton"
                    text: qsTr("Review")
                    font.pixelSize: Theme.fontSize
                    ToolTip.text: qsTr(
                        "Make sure your photos are ready to print")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    visible: hostWindow.quality.small > 0
                    onClicked: {
                        if (!hostWindow.printCtl) return
                        hostWindow.reviewList = hostWindow.printCtl.reviewPictures(
                            hostWindow.rows, hostWindow.printSize)
                        hostWindow.reviewOpen = true
                        hostReviewPanel.currentIndex =
                            hostWindow.reviewList.length > 0 ? 0 : -1
                    }
                }
            }

            PrintPrinterPanel {
                id: printPrinterPanel
                Layout.fillWidth: true
                printWindow: hostWindow
                pdfTargetDialog: hostPdfTargetDialog
            }

            PrintPrinterPanel {
                id: printPrinterDetailsPanel
                Layout.fillWidth: true
                printWindow: hostWindow
                pdfTargetDialog: hostPdfTargetDialog
                details: true
            }

            PrintFitPanel {
                Layout.fillWidth: true
                printWindow: hostWindow
            }
        }
        }

        // #4795: a hiba/haladás/eredmény a RÖGZÍTETT részben van (a görgetett
        // tartalmon kívül), hogy a Nyomtatás után mindig látsszon.
        // Felső korlát (az ablak harmada): hosszú kihagyott-lista se tolja
        // ki a gombsort — a szövegek ekkor a saját területükön görgethetők.
        PrintStatusPanel {
            id: printStatusPanel
            printWindow: hostWindow
        }

        PrintButtonRow {
            id: printButtonRow
            printWindow: hostWindow
            printWindowHelp: hostWindowHelp
        }
    }
}
