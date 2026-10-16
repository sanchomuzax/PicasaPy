import QtQuick

// A hat fókuszos effekt egérrel állítható fókuszpontja. A teljes kirajzolt
// képen fogadja a lenyomást, a puck pedig a csúszkákkal közös x/y értéket írja.
Item {
    id: root

    objectName: "viewerEffectFocalPuck"
    required property var targetImage
    required property var panel

    parent: targetImage
    x: targetImage ? (targetImage.width - targetImage.paintedWidth) / 2 : 0
    y: targetImage ? (targetImage.height - targetImage.paintedHeight) / 2 : 0
    width: targetImage ? targetImage.paintedWidth : 0
    height: targetImage ? targetImage.paintedHeight : 0
    z: 20

    readonly property string effectKey: panel && panel.paramEffectName
        ? panel.paramEffectName.toLowerCase() : ""
    readonly property bool isFocalEffect:
        effectKey === "radblur" || effectKey === "radsat"
        || effectKey === "dir_tint" || effectKey === "radtint"
        || effectKey === "focalzoom"
        || effectKey === "picnikfocalpixelate"
    readonly property bool directional: effectKey === "dir_tint"
    readonly property var values: panel ? panel.paramEffectValues : []
    readonly property real focusX:
        values && values.length > 0 ? Number(values[0]) : 0.5
    readonly property real focusY:
        values && values.length > 1 ? Number(values[1]) : 0.5
    // A natív `dir_tint` 0-s negyedében a puck x koordinátája adja a ±15°-os
    // szöget; ezt a tengelyt ugyanúgy forgatjuk, ahogy a képen húzott puck.
    readonly property real directionAngle: (focusX - 0.5) * 30.0

    visible: enabled && isFocalEffect && panel.paramPanelActive
             && !panel.paramPanelSuspended && !panel.modeToolActive
             && width > 0 && height > 0
    enabled: isFocalEffect && panel.paramPanelActive
             && !panel.paramPanelSuspended && !panel.modeToolActive

    function korlat(ertek) {
        return Math.max(0, Math.min(1, ertek))
    }

    function beallitFokuszt(x, y) {
        if (!panel || !panel.updateParamValue) return
        panel.updateParamValue(0, korlat(x / Math.max(1, width)))
        panel.updateParamValue(1, korlat(y / Math.max(1, height)))
    }

    MouseArea {
        objectName: "viewerEffectFocalPuckMouseArea"
        anchors.fill: parent
        enabled: root.enabled
        acceptedButtons: Qt.LeftButton
        preventStealing: true
        cursorShape: Qt.CrossCursor

        onPressed: function(mouse) {
            root.beallitFokuszt(mouse.x, mouse.y)
        }
        onPositionChanged: function(mouse) {
            if (mouse.buttons & Qt.LeftButton)
                root.beallitFokuszt(mouse.x, mouse.y)
        }
    }

    // A Graduated Tint rétegének iránya látszik, ahogy a puck vízszintes
    // helye változtatja a natív irányszöget. Más effekt nem kap irányvonalat.
    Rectangle {
        objectName: "viewerEffectPuckDirection"
        visible: root.directional
        width: 38
        height: 2
        x: root.focusX * root.width - width / 2
        y: root.focusY * root.height - height / 2
        color: "#fff"
        rotation: -root.directionAngle
        transformOrigin: Item.Center
        antialiasing: true
        z: 1

        Rectangle {
            width: 6
            height: 6
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            radius: width / 2
            color: parent.color
        }
        Rectangle {
            width: 6
            height: 6
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            radius: width / 2
            color: parent.color
        }
    }

    Rectangle {
        objectName: "viewerEffectPuckRing"
        width: 24
        height: 24
        x: root.focusX * root.width - width / 2
        y: root.focusY * root.height - height / 2
        radius: width / 2
        color: "#33000000"
        border.width: 2
        border.color: "#fff"
        antialiasing: true
        z: 2

        Rectangle {
            width: 6
            height: 6
            anchors.centerIn: parent
            radius: width / 2
            color: "#fff"
            antialiasing: true
        }
    }
}
