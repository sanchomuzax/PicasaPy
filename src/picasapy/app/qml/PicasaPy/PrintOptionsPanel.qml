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
    property alias sourceLabels: optionsFields.sourceLabels
    property alias placementLabels: optionsFields.placementLabels
    property alias textColorPickerBevel: optionsFields.textColorPickerBevel
    property alias colorSwatchComponent: optionsFields.colorSwatchComponent
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

    PrintOptionsFields {
        id: optionsFields
        anchors.fill: parent
        panel: panel
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
            panel.textColorPickerBevel.mapToItem(panel, 0, 0).x))
        y: Math.max(0, Math.min(
            panel.height - height,
            panel.textColorPickerBevel.mapToItem(
                panel, 0, panel.textColorPickerBevel.height).y))
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
                    panel.colorSwatchComponent.createObject(
                        textColorPalette,
                        { paletteIndex: i, textSwatch: true })
                }
            }
        }
    }
}
