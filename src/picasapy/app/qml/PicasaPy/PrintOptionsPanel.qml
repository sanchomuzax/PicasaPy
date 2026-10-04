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
    // Csak a színgomb engedélyezett nyitása hagyhatja nyitva a Popupot.
    property bool textColorPickerRequested: false
    property var sourceLabels: [
        qsTr("No text"), qsTr("Caption"), qsTr("Filename"),
        qsTr("Exif information")
    ]
    property var placementLabels: [
        qsTr("Below image"), qsTr("On image"), qsTr("On border")
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

    function readOptions() {
        if (typeof printController !== "undefined" && printController)
            return printController.printOptions()
        return panel.controller ? panel.controller.printOptions() : ({})
    }

    function readFontFamilies() {
        if (typeof printController !== "undefined" && printController)
            return printController.printFontFamilies()
        return panel.controller ? panel.controller.printFontFamilies() : []
    }

    function readTextSizes() {
        if (typeof printController !== "undefined" && printController)
            return printController.printTextSizes()
        return panel.controller ? panel.controller.printTextSizes() : []
    }

    function writeOption(name, value) {
        if (typeof printController !== "undefined" && printController) {
            printController.setPrintOption(name, value)
            return
        }
        if (panel.controller) panel.controller.setPrintOption(name, value)
    }

    function restoreOptions(values) {
        if (typeof printController !== "undefined" && printController) {
            printController.restorePrintOptions(values)
            return
        }
        if (panel.controller) panel.controller.restorePrintOptions(values)
    }

    function showOptions() {
        panel.closeTextColorPicker()
        if (!panel.controller) return
        panel.options = panel.copyOptions(panel.readOptions())
        panel.savedOptions = panel.copyOptions(panel.options)
        panel.fontFamilies = panel.readFontFamilies()
        panel.textSizes = panel.readTextSizes()
        panel.visible = true
        panel.closeTextColorPicker()
    }

    function openTextColorPicker() {
        panel.textColorPickerRequested = true
        textColorPicker.open()
    }

    function closeTextColorPicker() {
        panel.textColorPickerRequested = false
        textColorPicker.close()
    }

    function setOption(name, value) {
        if (!panel.controller || !panel.editable) return
        var next = panel.copyOptions(panel.options)
        next[name] = value
        panel.options = next
        panel.writeOption(name, value)
    }

    function applyChanges() {
        if (!panel.controller || !panel.editable) return
        panel.options = panel.copyOptions(panel.readOptions())
        panel.optionsApplied()
    }

    function cancelChanges() {
        if (panel.controller && !panel.contactSheet)
            panel.restoreOptions(panel.savedOptions)
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

    function chooseColor(index, textColor) {
        var name = textColor ? "textColor" : "borderColor"
        panel.setOption(name, parseInt(panel.colorPalette[index].slice(1), 16))
        if (textColor) panel.closeTextColorPicker()
    }

    onVisibleChanged: {
        if (!panel.visible) panel.closeTextColorPicker()
    }

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
                    text: qsTr("Only bottom")
                    checked: panel.options.borderEdge
                    enabled: panel.editable && panel.options.border
                    onClicked: panel.setOption("borderEdge", checked)
                }
                CheckBox {
                    objectName: "printOptionEvenBorderCheckBox"
                    text: qsTr("Even width")
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

    Popup {
        id: textColorPicker
        objectName: "printOptionTextPickerPanel"
        parent: panel
        onVisibleChanged: {
            // A panel/ablak láthatósági eseménye önmagában nem nyithatja ki.
            if (visible && !panel.textColorPickerRequested)
                textColorPicker.close()
        }
        onClosed: panel.textColorPickerRequested = false
        x: Math.max(0, Math.min(
            panel.width - width,
            textColorPickerBevel.mapToItem(panel, 0, 0).x))
        y: Math.max(0, Math.min(
            panel.height - height,
            textColorPickerBevel.mapToItem(
                panel, 0, textColorPickerBevel.height).y))
        padding: 6
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        contentWidth: textColorPalette.width
        contentHeight: textColorPalette.height
        background: Rectangle {
            color: Theme.canvasBg
            border.width: 1
            border.color: Theme.chromeBorder
        }
        Item {
            id: textColorPalette
            objectName: "printOptionTextColorPalette"
            width: 5 * 18 + 4 * 3
            height: 2 * 18 + 3
            Component.onCompleted: {
                for (var i = 0; i < panel.colorPalette.length; ++i) {
                    printOptionColorSwatch.createObject(
                        textColorPalette,
                        { paletteIndex: i, textSwatch: true })
                }
            }
        }
    }
}
