import QtQuick
import QtQuick.Controls

// Közös spektrumválasztó szöveg-, körvonal- és effekt-színekhez (#4548).
// A 225×225-ös panelen az öt MRU-rekesz, a 181×147-es HSV-paletta és a
// teljes színskála külön kattintható; az aktuális szín azonnal érvényesül.
Popup {
    id: picker
    objectName: "colorSpectrumPicker"

    property Item anchorItem: null
    property string currentColor: "#ffffff"
    property var recentColors: ["", "", "", "", ""]
    property real hue: 0
    property real saturation: 0
    property real brightness: 1
    readonly property alias spectrumFieldItem: spectrumField
    readonly property alias hueSpectrumItem: hueSpectrum

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

    background: Rectangle {
        color: Theme.canvasBg
        border.width: 1
        border.color: Theme.chromeBorder
    }

    function syncFromCurrentColor() {
        var selected = Qt.color(currentColor)
        if (selected.hsvHue >= 0)
            hue = selected.hsvHue
        saturation = selected.hsvSaturation
        brightness = selected.hsvValue
    }

    function channelHex(value) {
        var hex = Math.max(0, Math.min(255, Math.round(value * 255)))
                         .toString(16)
        return hex.length < 2 ? "0" + hex : hex
    }

    function selectedHex() {
        var selected = Qt.hsva(hue, saturation, brightness, 1)
        return "#" + channelHex(selected.r)
                   + channelHex(selected.g)
                   + channelHex(selected.b)
    }

    function publishColor() {
        picker.colorPicked(picker.selectedHex())
    }

    function pickHue(position, extent) {
        hue = Math.max(0, Math.min(1, position / Math.max(1, extent)))
        publishColor()
    }

    function pickSaturationAndBrightness(xPosition, yPosition, extentWidth,
                                         extentHeight) {
        saturation = Math.max(0, Math.min(1,
                                          xPosition / Math.max(1, extentWidth)))
        brightness = 1 - Math.max(0, Math.min(1,
                                             yPosition / Math.max(1, extentHeight)))
        publishColor()
    }

    onCurrentColorChanged: syncFromCurrentColor()
    Component.onCompleted: syncFromCurrentColor()

    Repeater {
        model: picker.recentColors

        delegate: Rectangle {
            required property string modelData
            required property int index

            objectName: picker.objectName + "Recent" + index
            x: 51 + index * 31
            y: 13
            width: 26
            height: 26
            color: modelData || "transparent"
            border.width: 1
            border.color: Theme.chromeBorder

            MouseArea {
                anchors.fill: parent
                enabled: parent.modelData !== ""
                cursorShape: Qt.PointingHandCursor
                onClicked: picker.colorPicked(parent.modelData)
            }
        }
    }

    Rectangle {
        id: spectrumField
        objectName: picker.objectName + "Spectrum"
        x: 20
        y: 48
        width: 181
        height: 147
        color: Qt.hsva(picker.hue, 1, 1, 1)
        clip: true

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: "#ffffffff" }
                GradientStop { position: 1; color: "#00ffffff" }
            }
        }
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0; color: "#00000000" }
                GradientStop { position: 1; color: "#ff000000" }
            }
        }
        MouseArea {
            objectName: picker.objectName + "SpectrumInput"
            anchors.fill: parent
            cursorShape: Qt.CrossCursor
            onClicked: picker.pickSaturationAndBrightness(
                           mouse.x, mouse.y, parent.width, parent.height)
            onPositionChanged: {
                if (pressed)
                    picker.pickSaturationAndBrightness(
                                mouse.x, mouse.y, parent.width, parent.height)
            }
        }
    }

    Rectangle {
        x: 20
        y: 198
        width: 181
        height: 12
        color: picker.currentColor
        border.width: 1
        border.color: Theme.chromeBorder
    }

    Rectangle {
        id: hueSpectrum
        objectName: picker.objectName + "HueSpectrum"
        x: 20
        y: 213
        width: 181
        height: 10
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.00; color: "#ff0000" }
            GradientStop { position: 0.17; color: "#ffff00" }
            GradientStop { position: 0.33; color: "#00ff00" }
            GradientStop { position: 0.50; color: "#00ffff" }
            GradientStop { position: 0.67; color: "#0000ff" }
            GradientStop { position: 0.83; color: "#ff00ff" }
            GradientStop { position: 1.00; color: "#ff0000" }
        }
        border.width: 1
        border.color: Theme.chromeBorder

        Rectangle {
            objectName: picker.objectName + "HueMarker"
            x: Math.max(0, Math.min(parent.width - width,
                                     picker.hue * parent.width - width / 2))
            y: -2
            width: 4
            height: parent.height + 4
            color: "transparent"
            border.width: 1
            border.color: Theme.ink
        }

        MouseArea {
            objectName: picker.objectName + "HueInput"
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: picker.pickHue(mouse.x, parent.width)
            onPositionChanged: {
                if (pressed)
                    picker.pickHue(mouse.x, parent.width)
            }
        }
    }
}
