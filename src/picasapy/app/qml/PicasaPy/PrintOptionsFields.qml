import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A nyomtatási beállítások űrlapja és színmintái.
Item {
    id: fields
    required property var panel
    property alias textColorPickerBevel: textColorPickerBevel
    property alias colorSwatchComponent: printOptionColorSwatch
    property var sourceLabels: [
        qsTr("No text"), qsTr("Caption"), qsTr("Filename"),
        qsTr("Exif information")
    ]
    property var placementLabels: [
        qsTr("Below image"), qsTr("On image"), qsTr("On border")
    ]

    Component {
        id: printOptionColorSwatch
        Rectangle {
            required property int paletteIndex
            property bool textSwatch: false
            objectName: (textSwatch ? "printOptionTextColor" :
                         "printOptionBorderColor") + paletteIndex
            width: 18
            height: 18
            x: textSwatch ? (paletteIndex % 5) * 21 : paletteIndex * 20
            y: textSwatch ? Math.floor(paletteIndex / 5) * 21 : 0
            enabled: panel.editable
            color: panel.colorPalette[paletteIndex]
            border.width: panel.colorArgb(
                textSwatch ? panel.options.textColor : panel.options.borderColor)
                === panel.colorPalette[paletteIndex] ? 2 : 1
            border.color: Theme.chromeBorder
            MouseArea {
                anchors.fill: parent
                enabled: panel.editable
                cursorShape: Qt.PointingHandCursor
                onClicked: panel.chooseColor(parent.paletteIndex, parent.textSwatch)
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            Text {
                objectName: "printOptionsTitle"
                text: qsTr("Border and text options")
                font.pixelSize: Theme.fontSize + 3
                font.bold: true
                color: Theme.ink
                Layout.fillWidth: true
            }
            PicasaButton {
                objectName: "printOptionsCloseButton"
                text: qsTr("Close")
                onClicked: panel.cancelChanges()
            }
        }

        Text {
            objectName: "printOptionsDisabledText"
            visible: panel.contactSheet
            text: qsTr("Sorry, but these options cannot be used when printing contact sheets.")
            color: Theme.textGray
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        ScrollView {
            id: optionScroll
            objectName: "printOptionScrollView"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth

            ColumnLayout {
                id: optionColumn
                width: optionScroll.availableWidth
                spacing: 6

                Text {
                    objectName: "printOptionCaptionLabel"
                    text: qsTr("Captions")
                    color: Theme.ink
                    font.bold: true
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    RadioButton {
                        objectName: "printOptionSource0"
                        text: panel.sourceLabels[0]
                        checked: panel.options.textSource === 0
                        enabled: panel.editable
                        onClicked: panel.setOption("textSource", 0)
                    }
                    RadioButton {
                        objectName: "printOptionSource1"
                        text: panel.sourceLabels[1]
                        checked: panel.options.textSource === 1
                        enabled: panel.editable
                        onClicked: panel.setOption("textSource", 1)
                    }
                    RadioButton {
                        objectName: "printOptionSource2"
                        text: panel.sourceLabels[2]
                        checked: panel.options.textSource === 2
                        enabled: panel.editable
                        onClicked: panel.setOption("textSource", 2)
                    }
                    RadioButton {
                        objectName: "printOptionSource3"
                        text: panel.sourceLabels[3]
                        checked: panel.options.textSource === 3
                        enabled: panel.editable
                        onClicked: panel.setOption("textSource", 3)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    RadioButton {
                        objectName: "printOptionPlacement0"
                        text: panel.placementLabels[0]
                        checked: panel.options.textPlacement === 0
                        enabled: panel.editable
                        onClicked: panel.setOption("textPlacement", 0)
                    }
                    RadioButton {
                        objectName: "printOptionPlacement1"
                        text: panel.placementLabels[1]
                        checked: panel.options.textPlacement === 1
                        enabled: panel.editable
                        onClicked: panel.setOption("textPlacement", 1)
                    }
                    RadioButton {
                        objectName: "printOptionPlacement2"
                        text: panel.placementLabels[2]
                        checked: panel.options.textPlacement === 2
                        enabled: panel.editable
                        onClicked: panel.setOption("textPlacement", 2)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: qsTr("Font")
                        color: Theme.ink
                    }
                    PicasaComboBox {
                        id: fontBox
                        objectName: "printOptionFontBox"
                        Layout.fillWidth: true
                        model: panel.fontFamilies
                        currentIndex: Math.max(
                            0, panel.fontFamilies.indexOf(panel.options.textFont))
                        enabled: panel.editable && panel.options.textSource !== 0
                        onActivated: panel.setOption("textFont", textAt(currentIndex))
                    }
                    Text {
                        text: qsTr("Size")
                        color: Theme.ink
                    }
                    PicasaComboBox {
                        id: sizeBox
                        objectName: "printOptionSizeBox"
                        Layout.preferredWidth: 90
                        model: panel.textSizes
                        currentIndex: Math.max(
                            0, panel.textSizes.indexOf(panel.options.textSize))
                        enabled: panel.editable && panel.options.textSource !== 0
                        onActivated: panel.setOption(
                            "textSize", Number(textAt(currentIndex)))
                    }
                }

                CheckBox {
                    objectName: "printOptionWrapCheckBox"
                    text: qsTr("Wrap text")
                    checked: panel.options.wrap
                    enabled: panel.editable && panel.options.textSource !== 0
                    onClicked: panel.setOption("wrap", checked)
                }

                CheckBox {
                    objectName: "printOptionBorderCheckBox"
                    text: qsTr("Border")
                    checked: panel.options.border
                    enabled: panel.editable
                    onClicked: panel.setOption("border", checked)
                }
                Text {
                    objectName: "printOptionBorderSizeLabel"
                    text: qsTr("Border width")
                    color: Theme.textGray
                }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        objectName: "printOptionBorderNoneLabel"
                        text: qsTr("None")
                        color: Theme.textGray
                    }
                    Slider {
                        id: borderSlider
                        objectName: "printOptionBorderSlider"
                        Layout.fillWidth: true
                        from: 0
                        to: 1
                        value: Number(panel.options.borderSize || 0) / 1024.0
                        enabled: panel.editable && panel.options.border
                        onMoved: panel.setOption("borderSize", Math.floor(value * 1024))
                    }
                    Text {
                        objectName: "printOptionBorderMaxLabel"
                        text: qsTr("Max.")
                        color: Theme.textGray
                    }
                }
                CheckBox {
                    objectName: "printOptionBottomOnlyCheckBox"
                    text: qsTr("Bottom only")
                    checked: panel.options.borderEdge
                    enabled: panel.editable && panel.options.border
                    onClicked: panel.setOption("borderEdge", checked)
                }
                CheckBox {
                    objectName: "printOptionEvenBorderCheckBox"
                    text: qsTr("Even width border")
                    checked: panel.options.evenBorder
                    enabled: panel.editable && panel.options.border
                    onClicked: panel.setOption("evenBorder", checked)
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: qsTr("Text color")
                        color: Theme.ink
                    }
                    Rectangle {
                        id: textColorPickerBevel
                        objectName: "printOptionTextColorBevel"
                        width: 34
                        height: 24
                        color: Theme.chromeBorder
                        border.width: 1
                        border.color: Theme.chromeBorder
                        enabled: panel.editable && panel.options.textSource !== 0
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 3
                            color: panel.colorArgb(panel.options.textColor)
                            border.width: 1
                            border.color: Theme.canvasBg
                        }
                        MouseArea {
                            anchors.fill: parent
                            enabled: parent.enabled
                            cursorShape: Qt.PointingHandCursor
                            onClicked: panel.openTextColorPicker()
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: qsTr("Border color")
                        color: Theme.ink
                    }
                    Item {
                        id: borderColorPalette
                        objectName: "printOptionBorderColorPalette"
                        width: 10 * 18 + 9 * 2
                        height: 18
                        Component.onCompleted: {
                            for (var i = 0; i < panel.colorPalette.length; ++i) {
                                printOptionColorSwatch.createObject(
                                    borderColorPalette,
                                    { paletteIndex: i, textSwatch: false })
                            }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "printOptionsCancelButton"
                text: qsTr("Cancel")
                onClicked: panel.cancelChanges()
            }
            PicasaButton {
                objectName: "printOptionsApplyButton"
                text: qsTr("Apply")
                enabled: panel.editable
                onClicked: panel.applyChanges()
            }
            PicasaButton {
                objectName: "printOptionsOkButton"
                text: qsTr("OK")
                enabled: panel.editable
                accent: Theme.picasaGreen
                onClicked: panel.acceptChanges()
            }
        }
    }
}
