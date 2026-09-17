import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A Picasa eredeti `printoptions` paneljának terméki megfelelője (#1780).
// A gyökér a PrintDialog fölötti overlay: így a QGuiApplication mellett is
// van külön, modálisnak látszó panelünk, QWidget-alapú QPrintDialog nélkül.
Rectangle {
    id: panel
    objectName: "printOptionsPanel"
    color: Theme.canvasBg
    border.width: 1
    border.color: Theme.chromeBorder
    z: 300
    visible: false

    property var controller: null
    property bool contactSheet: false
    property var options: ({
        textSource: 0, textPlacement: 0, textFont: "Arial", textSize: 12,
        textColor: 0, wrap: false, border: false, borderSize: 10,
        borderColor: 0, borderEdge: false, evenBorder: true
    })
    property var savedOptions: ({
        textSource: 0, textPlacement: 0, textFont: "Arial", textSize: 12,
        textColor: 0, wrap: false, border: false, borderSize: 10,
        borderColor: 0, borderEdge: false, evenBorder: true
    })
    property var fontFamilies: []
    property var textSizes: []
    property var sourceLabels: [
        qsTr("No text"), qsTr("Picture caption"),
        qsTr("File name"), qsTr("EXIF data")
    ]
    property var placementLabels: [
        qsTr("Below the picture"), qsTr("On the picture"),
        qsTr("On the border")
    ]
    property var colorPalette: [
        "#00000000", "#ff000000", "#ffffffff", "#ffff0000",
        "#ff00aa00", "#ff0000ff", "#ffffff00", "#ffff8800",
        "#ffff00ff", "#ff00ffff"
    ]

    signal optionsApplied()
    signal closeRequested()

    readonly property bool editable:
        panel.controller !== null && !panel.contactSheet

    function copyOptions(raw) {
        var source = raw || {}
        return {
            textSource: Number(source.textSource || 0),
            textPlacement: Number(source.textPlacement || 0),
            textFont: String(source.textFont || "Arial"),
            textSize: Number(source.textSize || 12),
            textColor: Number(source.textColor || 0),
            wrap: Boolean(source.wrap),
            border: Boolean(source.border),
            borderSize: Number(source.borderSize || 10),
            borderColor: Number(source.borderColor || 0),
            borderEdge: Boolean(source.borderEdge),
            evenBorder: source.evenBorder === undefined
                        ? true : Boolean(source.evenBorder)
        }
    }

    function showOptions() {
        if (!panel.controller) return
        panel.options = panel.copyOptions(panel.controller.printOptions())
        panel.savedOptions = panel.copyOptions(panel.options)
        panel.fontFamilies = panel.controller.printFontFamilies()
        panel.textSizes = panel.controller.printTextSizes()
        panel.visible = true
    }

    function setOption(name, value) {
        if (!panel.controller || !panel.editable) return
        var next = panel.copyOptions(panel.options)
        next[name] = value
        panel.options = next
        panel.controller.setPrintOption(name, value)
    }

    function applyChanges() {
        if (!panel.controller || !panel.editable) return
        panel.options = panel.copyOptions(panel.controller.printOptions())
        panel.optionsApplied()
    }

    function cancelChanges() {
        if (panel.controller && !panel.contactSheet)
            panel.controller.restorePrintOptions(panel.savedOptions)
        panel.options = panel.copyOptions(panel.savedOptions)
        panel.closeRequested()
    }

    function acceptChanges() {
        panel.applyChanges()
        panel.closeRequested()
    }

    function colorArgb(value) {
        var number = Number(value)
        if (!isFinite(number)) number = 0
        number = number >>> 0
        var hex = number.toString(16)
        while (hex.length < 8) hex = "0" + hex
        return "#" + hex
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
            text: panel.controller
                  ? panel.controller.printOptionsDisabledText()
                  : qsTr("These options cannot be used when printing contact sheets.")
            color: Theme.textGray
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        ScrollView {
            id: optionScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth

            ColumnLayout {
                id: optionColumn
                width: optionScroll.availableWidth
                spacing: 6

                Text {
                    text: qsTr("Text source:")
                    color: Theme.ink
                    font.bold: true
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Repeater {
                        model: panel.sourceLabels
                        delegate: RadioButton {
                            id: sourceOption
                            required property int index
                            required property string modelData
                            objectName: "printOptionSource" + index
                            text: sourceOption.modelData
                            checked: panel.options.textSource === index
                            enabled: panel.editable
                            onClicked: panel.setOption("textSource", index)
                        }
                    }
                }

                Text {
                    text: qsTr("Text placement:")
                    color: Theme.ink
                    font.bold: true
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Repeater {
                        model: panel.placementLabels
                        delegate: RadioButton {
                            id: placementOption
                            required property int index
                            required property string modelData
                            objectName: "printOptionPlacement" + index
                            text: placementOption.modelData
                            checked: panel.options.textPlacement === index
                            enabled: panel.editable
                            onClicked: panel.setOption("textPlacement", index)
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: qsTr("Font:")
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
                        text: qsTr("Size:")
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

                Text {
                    text: qsTr("Border:")
                    color: Theme.ink
                    font.bold: true
                }
                CheckBox {
                    objectName: "printOptionBorderCheckBox"
                    text: qsTr("Print a border")
                    checked: panel.options.border
                    enabled: panel.editable
                    onClicked: panel.setOption("border", checked)
                }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
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
                        text: qsTr("Maximum")
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
                    text: qsTr("Even-width border")
                    checked: panel.options.evenBorder
                    enabled: panel.editable && panel.options.border
                    onClicked: panel.setOption("evenBorder", checked)
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: qsTr("Text color:")
                        color: Theme.ink
                    }
                    Grid {
                        objectName: "printOptionTextColorPalette"
                        columns: 10
                        spacing: 2
                        Repeater {
                            model: panel.colorPalette
                            delegate: Rectangle {
                                required property string modelData
                                required property int index
                                objectName: "printOptionTextColor" + index
                                width: 18
                                height: 18
                                color: modelData
                                border.width:
                                    panel.colorArgb(panel.options.textColor)
                                    === modelData ? 2 : 1
                                border.color: Theme.chromeBorder
                                MouseArea {
                                    anchors.fill: parent
                                    enabled: panel.editable
                                    onClicked: panel.setOption(
                                        "textColor", parseInt(
                                            modelData.slice(1), 16))
                                }
                            }
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: qsTr("Border color:")
                        color: Theme.ink
                    }
                    Grid {
                        objectName: "printOptionBorderColorPalette"
                        columns: 10
                        spacing: 2
                        Repeater {
                            model: panel.colorPalette
                            delegate: Rectangle {
                                required property string modelData
                                required property int index
                                objectName: "printOptionBorderColor" + index
                                width: 18
                                height: 18
                                color: modelData
                                border.width:
                                    panel.colorArgb(panel.options.borderColor)
                                    === modelData ? 2 : 1
                                border.color: Theme.chromeBorder
                                MouseArea {
                                    anchors.fill: parent
                                    enabled: panel.editable
                                    onClicked: panel.setOption(
                                        "borderColor", parseInt(
                                            modelData.slice(1), 16))
                                }
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
