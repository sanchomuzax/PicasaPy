import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350/#4318: a Picasa options.fen Nyomtatás füle élő beállításokat ad a
// PrintControllernek; a print.fen beállításai a nyomtatásnál érvényesülnek.
ColumnLayout {
    id: root
    objectName: "optionsTabPrintingPanel"
    spacing: 10

    readonly property var printCtl: (typeof printController !== "undefined")
        ? printController : null
    readonly property var printSizeLabelById: ({
        "M3X4": qsTr("3 x 4"),
        "M3_5X5": qsTr("3.5 x 5"),
        "M4X5": qsTr("4 x 5"),
        "M4X6": qsTr("4 x 6"),
        "M5X7": qsTr("5 x 7"),
        "M8X10": qsTr("8 x 10"),
        "TARCA": qsTr("Wallet"),
        "M5X8CM": qsTr("5 x 8 cm"),
        "M9X13CM": qsTr("9 x 13 cm"),
        "M10X15CM": qsTr("10 x 15 cm"),
        "M13X18CM": qsTr("13 x 18 cm"),
        "M15X20CM": qsTr("15 x 20 cm"),
        "M20X25CM": qsTr("20 x 25 cm"),
        "TELJES_OLDAL": qsTr("FullPage"),
        "CDSIZE": qsTr("CD Cover Size"),
        "PASSPORT": qsTr("Passport"),
        "CONTACT": qsTr("Contact Sheet")
    })
    readonly property var printSizeIds: printCtl ? printCtl.printOptionSizes() : []
    readonly property var printSizeLabels: printSizeIds.map(function (id) {
        return root.printSizeLabelById[id] || id
    })
    readonly property string previewsLabelText: qsTr("Previews:")
    readonly property string printerQualityLabelText: qsTr("Printer quality:")
    readonly property string resamplerLabelText: qsTr("Print resampler quality:")
    readonly property real settingsLabelWidth: Math.max(
        previewsLabelMetrics.advanceWidth,
        printerQualityLabelMetrics.advanceWidth,
        resamplerLabelMetrics.advanceWidth
    )

    TextMetrics {
        id: previewsLabelMetrics
        text: root.previewsLabelText
        font.pixelSize: Theme.fontSize
    }
    TextMetrics {
        id: printerQualityLabelMetrics
        text: root.printerQualityLabelText
        font.pixelSize: Theme.fontSize
    }
    TextMetrics {
        id: resamplerLabelMetrics
        text: root.resamplerLabelText
        font.pixelSize: Theme.fontSize
    }

    Text {
        text: qsTr("Available print sizes:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
        Layout.alignment: Qt.AlignHCenter
    }

    GridLayout {
        id: printSizeGrid
        objectName: "optionsPrintSizeGrid"
        columns: 2
        columnSpacing: 7
        rowSpacing: 7
        Layout.alignment: Qt.AlignHCenter

        Repeater {
            objectName: "optionsPrintSizeRepeater"
            model: 5

            Item {
                id: presetCell
                required property int index
                Layout.preferredWidth: 150
                Layout.preferredHeight: 23

                PicasaComboBox {
                    objectName: "optionsPrintSizeCombo" + presetCell.index
                    anchors.fill: parent
                    model: root.printSizeLabels
                    currentIndex: {
                        if (!root.printCtl) return -1
                        return root.printSizeIds.indexOf(
                            root.printCtl.printSizePresets()[presetCell.index])
                    }
                    onActivated: {
                        if (root.printCtl && currentIndex >= 0)
                            root.printCtl.setPrintSizePreset(
                                presetCell.index,
                                root.printSizeIds[currentIndex])
                    }
                }

                // Az eredeti sorszámcímke nem látszik, a qsTr-bejegyzését
                // megtartjuk a fordítási katalógus folytonosságához.
                Text {
                    objectName: "optionsPrintSizeLabel" + presetCell.index
                    visible: false
                    text: qsTr("Print size %1:").arg(presetCell.index + 1)
                }
            }
        }
    }

    Rectangle {
        objectName: "optionsPrintSettingsDivider"
        Layout.fillWidth: true
        height: 1
        color: "#a0a0a0"
    }

    ColumnLayout {
        id: printSettingsGrid
        objectName: "optionsPrintSettingsGrid"
        spacing: 8
        Layout.alignment: Qt.AlignHCenter

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                objectName: "optionsPrintPreviewsLabel"
                text: root.previewsLabelText
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                horizontalAlignment: Text.AlignRight
                Layout.preferredWidth: root.settingsLabelWidth
                Layout.alignment: Qt.AlignVCenter
            }
            CheckBox {
                objectName: "optionsPrintHiResPreviewCheck"
                text: qsTr("Use high quality previews (slower)")
                checked: root.printCtl ? !root.printCtl.printProxyPreview() : false
                onToggled: if (root.printCtl)
                    root.printCtl.setPrintProxyPreview(!checked)
            }
        }

        RowLayout {
            visible: Qt.platform.os === "windows"
            Layout.fillWidth: true
            spacing: 8
            Text {
                objectName: "optionsPrintQualityLabel"
                text: root.printerQualityLabelText
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                horizontalAlignment: Text.AlignRight
                Layout.preferredWidth: root.settingsLabelWidth
                Layout.alignment: Qt.AlignVCenter
            }
            ButtonGroup { id: qualityGroup }
            ColumnLayout {
                RadioButton {
                    objectName: "optionsPrintQualityCompatibleRadio"
                    text: qsTr("Compatible (half-res)")
                    ButtonGroup.group: qualityGroup
                    checked: root.printCtl
                        ? root.printCtl.printerQuality() === "compatible" : true
                    onToggled: if (root.printCtl && checked)
                        root.printCtl.setPrinterQuality("compatible")
                }
                RadioButton {
                    objectName: "optionsPrintQualityHighQualityRadio"
                    text: qsTr("High Quality (full-res)")
                    ButtonGroup.group: qualityGroup
                    checked: root.printCtl
                        ? root.printCtl.printerQuality() === "highQuality" : false
                    onToggled: if (root.printCtl && checked)
                        root.printCtl.setPrinterQuality("highQuality")
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                objectName: "optionsPrintResamplerLabel"
                text: root.resamplerLabelText
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                horizontalAlignment: Text.AlignRight
                Layout.preferredWidth: root.settingsLabelWidth
                Layout.alignment: Qt.AlignVCenter
            }
            ButtonGroup { id: resizeGroup }
            ColumnLayout {
                RadioButton {
                    objectName: "optionsPrintResizeGeneralRadio"
                    text: qsTr("General (Lanczos-3)")
                    ButtonGroup.group: resizeGroup
                    checked: root.printCtl
                        ? root.printCtl.printResamplerQuality() === 3 : true
                    onToggled: if (root.printCtl && checked)
                        root.printCtl.setPrintResamplerQuality(3)
                }
                RadioButton {
                    objectName: "optionsPrintResizeSharpRadio"
                    text: qsTr("Extra sharp (Lanczos-8)")
                    ButtonGroup.group: resizeGroup
                    checked: root.printCtl
                        ? root.printCtl.printResamplerQuality() === 8 : false
                    onToggled: if (root.printCtl && checked)
                        root.printCtl.setPrintResamplerQuality(8)
                }
            }
        }
    }

    Item { Layout.fillHeight: true }
}
