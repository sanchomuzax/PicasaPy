import QtQuick
import QtQuick.Controls

// Az eredeti 225×225-ös `pickerpanel`: öt MRU-rekesz, 30 színminta és a
// mért HSL-paletta. A palettakép a specifikáció RGB-horgonyaiból készül;
// az eredeti erőforrás-kép nem kerül a repóba (#5730).
Popup {
    id: picker
    objectName: "colorSpectrumPicker"

    property Item anchorItem: null
    property string currentColor: "#ffffff"
    property var recentColors: ["", "", "", "", ""]
    // A natív panel `palette` tulajdonságának megfelelő mód. A Popup örökölt
    // `palette` tulajdonsága miatt a saját neve `paletteMode`.
    property int paletteMode: 0

    readonly property alias spectrumFieldItem: paletteArea

    signal colorPicked(string hex)

    width: 225
    height: 225
    padding: 0
    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    parent: Overlay.overlay
    x: anchorItem && parent
       ? Math.max(0, Math.min(parent.width - width,
                              anchorItem.mapToItem(parent, 0, 0).x)) : 0
    y: anchorItem && parent
       ? Math.max(0, Math.min(parent.height - height,
                              anchorItem.mapToItem(parent, 0,
                                                   anchorItem.height).y)) : 0

    readonly property var paletteSamples: [
        "#63001e", "#b10039", "#895227", "#c47338", "#d39815",
        "#e9a518", "#ffbd00", "#ffd154", "#c8c866", "#e3e274",
        "#629c33", "#85cd44", "#8ab28d", "#a8d8ab", "#00727c",
        "#00b2bd", "#87a2b0", "#a6c7d7", "#a9d1e7", "#cde7f6",
        "#007bc4", "#0091e1", "#002455", "#004baa", "#586695",
        "#778cca", "#38175a", "#692dac", "#c88dac", "#e3a1c4"
    ]

    readonly property var emptyRecentColors: [
        "#00b2bd", "#87a2b0", "#007bc4", "#00727c", "#692dac"
    ]

    background: Rectangle {
        color: Theme.canvasBg
        border.width: 1
        border.color: Theme.chromeBorder
    }

    function _pickPalettePixel(mouseX, mouseY) {
        var x = Math.max(2, Math.min(179, Math.floor(mouseX) + 2))
        var y = Math.max(56, Math.min(144, Math.floor(mouseY) + 56))
        picker.colorPicked(colorPalette.colorAt(x, y, picker.paletteMode))
    }

    Item {
        id: paletteArea
        objectName: picker.objectName + "Spectrum"
        x: 20
        y: 15
        width: 181
        height: 147

        Image {
            id: paletteBitmap
            objectName: picker.objectName + "PaletteImage"
            anchors.fill: parent
            source: "image://colorpalette/palette" + picker.paletteMode
            sourceSize: Qt.size(181, 147)
            fillMode: Image.Stretch
            smooth: false
            asynchronous: false
            cache: false
        }

        Repeater {
            model: picker.paletteSamples

            delegate: Rectangle {
                required property string modelData
                required property int index

                objectName: picker.objectName + "PaletteSample" + index
                x: 1 + index * 6
                y: 28
                width: 6
                height: 12
                color: modelData

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: picker.colorPicked(parent.modelData)
                }
            }
        }

        MouseArea {
            objectName: picker.objectName + "SpectrumInput"
            x: 2
            y: 56
            width: 178
            height: 89
            cursorShape: Qt.CrossCursor
            onClicked: picker._pickPalettePixel(mouse.x, mouse.y)
            onPositionChanged: {
                if (pressed)
                    picker._pickPalettePixel(mouse.x, mouse.y)
            }
        }
    }

    Repeater {
        model: picker.recentColors

        delegate: Rectangle {
            required property string modelData
            required property int index

            objectName: picker.objectName + "Recent" + index
            property string recentColor: modelData || ""
            property string baseColor: picker.emptyRecentColors[index]
            x: 51 + index * 31
            y: 15
            width: 26
            height: 26
            color: recentColor || baseColor
            border.width: recentColor.toLowerCase() === picker.currentColor.toLowerCase()
                          ? 2 : 1
            border.color: recentColor.toLowerCase() === picker.currentColor.toLowerCase()
                          ? Theme.selectionBlue : Theme.chromeBorder

            MouseArea {
                anchors.fill: parent
                enabled: parent.recentColor !== ""
                cursorShape: Qt.PointingHandCursor
                onClicked: picker.colorPicked(parent.recentColor)
            }
        }
    }
}
