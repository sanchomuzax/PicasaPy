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
        "Nincs szöveg", "Képfeliratok", "Fájlnév", "Exif-adatok"
    ]
    property var placementLabels: [
        "A kép alatt", "A képen", "A szegélyen"
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

    function disabledText() {
        if (typeof printController !== "undefined" && printController)
            return printController.printOptionsDisabledText()
        return panel.controller
               ? panel.controller.printOptionsDisabledText()
               : "Ezek a beállítások indexképek nyomtatásakor nem használhatók."
    }

    function showOptions() {
        if (!panel.controller) return
        panel.options = panel.copyOptions(panel.readOptions())
        panel.savedOptions = panel.copyOptions(panel.options)
        panel.fontFamilies = panel.readFontFamilies()
        panel.textSizes = panel.readTextSizes()
        panel.visible = true
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

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            Text {
                objectName: "printOptionsTitle"
                text: "Szegély- és feliratopciók"
                font.pixelSize: Theme.fontSize + 3
                font.bold: true
                color: Theme.ink
                Layout.fillWidth: true
            }
            PicasaButton {
                objectName: "printOptionsCloseButton"
                text: "Bezárás"
                onClicked: panel.cancelChanges()
            }
        }

        Text {
            objectName: "printOptionsDisabledText"
            visible: panel.contactSheet
            text: panel.controller
                  ? panel.disabledText()
                  : "Ezek a beállítások indexképek nyomtatásakor nem használhatók."
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
                    text: "Felirat forrása:"
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
                    text: "Felirat helye:"
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
                        text: "Betűtípus:"
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
                        text: "Méret:"
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
                    text: "Szöveg tördelése"
                    checked: panel.options.wrap
                    enabled: panel.editable && panel.options.textSource !== 0
                    onClicked: panel.setOption("wrap", checked)
                }

                Text {
                    text: "Szegély:"
                    color: Theme.ink
                    font.bold: true
                }
                CheckBox {
                    objectName: "printOptionBorderCheckBox"
                    text: "Szegély nyomtatása"
                    checked: panel.options.border
                    enabled: panel.editable
                    onClicked: panel.setOption("border", checked)
                }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Egyik sem"
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
                        text: "Maximális"
                        color: Theme.textGray
                    }
                }
                CheckBox {
                    objectName: "printOptionBottomOnlyCheckBox"
                    text: "Csak alul"
                    checked: panel.options.borderEdge
                    enabled: panel.editable && panel.options.border
                    onClicked: panel.setOption("borderEdge", checked)
                }
                CheckBox {
                    objectName: "printOptionEvenBorderCheckBox"
                    text: "Egyenletes szélességű szegély"
                    checked: panel.options.evenBorder
                    enabled: panel.editable && panel.options.border
                    onClicked: panel.setOption("evenBorder", checked)
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Szöveg színe:"
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
                        text: "Szegély színe:"
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
                text: "Mégse"
                onClicked: panel.cancelChanges()
            }
            PicasaButton {
                objectName: "printOptionsApplyButton"
                text: "Alkalmaz"
                enabled: panel.editable
                onClicked: panel.applyChanges()
            }
            PicasaButton {
                objectName: "printOptionsOkButton"
                text: "OK"
                enabled: panel.editable
                accent: Theme.picasaGreen
                onClicked: panel.acceptChanges()
            }
        }
    }
}
