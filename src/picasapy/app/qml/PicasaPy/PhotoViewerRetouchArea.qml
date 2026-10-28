import QtQuick

// #445: a retusálás a Picasa súgószövege szerinti,
// KÉTKATTINTÁSOS, irányított klónozás — 1. kattintás a
// CÉL kijelölése, egérmozgatás a FORRÁS élő előnézete,
// 2. kattintás véglegesíti. `Ctrl`+húzás eközben a
// meglévő nagyítás-pásztázó (`viewer.panX`/`panY`/
// `clampPan()`, ld. lent a `viewerPanArea`-t) állapotára
// ül rá, hogy zoomolt nézetben kattintás nélkül lehessen
// odébb húzni a képet.

//: #3741: a `photo` helyett a `photoArea.fokuszKep` a
//: szülő — a retusálás a TÉNYLEGESEN szerkesztett félen
//: megy, ne a másik (nem kijelölt) képen.
MouseArea {
    required property var photoArea
    id: retouchClickArea
    objectName: "retouchClickArea"
    parent: photoArea.fokuszKep
    visible: photoArea.hostEditorPanel.retouchActive
    enabled: photoArea.hostEditorPanel.retouchActive
    hoverEnabled: true
    x: (photoArea.fokuszKep.width
        - photoArea.fokuszKep.paintedWidth) / 2
    y: (photoArea.fokuszKep.height
        - photoArea.fokuszKep.paintedHeight) / 2
    width: photoArea.fokuszKep.paintedWidth
    height: photoArea.fokuszKep.paintedHeight
    // A Picasa a `thumbui/circlecursor` elemmel helyettesíti
    // a rendszermutatót. A kör mérete egyezzen a retusáló
    // patch tényleges, modellből kapott sugarával.
    cursorShape: ctrlPanning ? Qt.CrossCursor : Qt.BlankCursor
    property bool ctrlPanning: false
    property real panLastX: 0
    property real panLastY: 0
    property real retouchTargetX: 0
    property real retouchTargetY: 0
    property real retouchSourceX: 0
    property real retouchSourceY: 0
    property bool hasRetouchTarget: false
    property bool hasRetouchSource: false
    property bool committingRetouchPatch: false
    readonly property real brushRadius:
        (typeof editController !== "undefined" && editController
         && editController.retouchBrushRadiusRatio !== undefined
            ? editController.retouchBrushRadiusRatio : 0)
        * Math.min(width, height)

    function torolRetouchJeloleseket() {
        hasRetouchTarget = false
        hasRetouchSource = false
    }

    onVisibleChanged: {
        if (!visible) {
            torolRetouchJeloleseket()
            ctrlPanning = false
        }
    }

    Connections {
        target: photoArea.hostEditorPanel
        function onRetouchPatchPendingChanged() {
            if (!photoArea.hostEditorPanel.retouchPatchPending
                    && !retouchClickArea.committingRetouchPatch)
                retouchClickArea.torolRetouchJeloleseket()
        }
        function onRetouchRegionCountChanged() {
            if (photoArea.hostEditorPanel.retouchRegionCount === 0
                    && !photoArea.hostEditorPanel.retouchPatchPending)
                retouchClickArea.torolRetouchJeloleseket()
        }
    }
    onPressed: function(mouse) {
        if (mouse.modifiers & Qt.ControlModifier) {
            ctrlPanning = true
            panLastX = mouse.x; panLastY = mouse.y
        }
    }
    onPositionChanged: function(mouse) {
        if (width <= 0 || height <= 0) return
        if (ctrlPanning) {
            photoArea.hostViewer.panX += mouse.x - panLastX
            photoArea.hostViewer.panY += mouse.y - panLastY
            panLastX = mouse.x; panLastY = mouse.y
            photoArea.hostViewer.clampPan()
            return
        }
        if (typeof editController !== "undefined" && editController
                && editController.retouchPatchPending)
            editController.previewRetouchSource(
                mouse.x / width, mouse.y / height)
    }
    onReleased: function(mouse) { ctrlPanning = false }
    onClicked: function(mouse) {
        if (width <= 0 || height <= 0) return
        // Ctrl+húzás UTÁNi felengedés is "clicked"-et vált
        // ki QML-ben — ez NEM patch-kattintás
        if (mouse.modifiers & Qt.ControlModifier) return
        if (typeof editController !== "undefined" && editController
                && editController.retouchPatchPending) {
            retouchSourceX = mouse.x / width
            retouchSourceY = mouse.y / height
            hasRetouchSource = true
            committingRetouchPatch = true
            editController.commitRetouchPatch(
                mouse.x / width, mouse.y / height)
            committingRetouchPatch = false
        } else {
            retouchTargetX = mouse.x / width
            retouchTargetY = mouse.y / height
            hasRetouchTarget = true
            hasRetouchSource = false
            if (typeof editController !== "undefined" && editController)
                editController.beginRetouchPatch(
                    mouse.x / width, mouse.y / height)
        }
    }

    Component {
        id: retouchCircleComponent
        Item {
            Rectangle {
                anchors.fill: parent
                color: "transparent"
                radius: width / 2
                border.width: 2
                border.color: "#000000"
            }
            Rectangle {
                anchors.fill: parent
                anchors.margins: 2
                color: "transparent"
                radius: width / 2
                border.width: 1
                border.color: "#ffffff"
            }
        }
    }

    Loader {
        id: retouchTargetCircle
        objectName: "retouchTargetCircle"
        sourceComponent: retouchCircleComponent
        visible: retouchClickArea.hasRetouchTarget
        width: 2 * retouchClickArea.brushRadius
        height: width
        x: retouchClickArea.retouchTargetX
            * retouchClickArea.width - width / 2
        y: retouchClickArea.retouchTargetY
            * retouchClickArea.height - height / 2
        z: 1
    }

    Loader {
        id: retouchSourceCircle
        objectName: "retouchSourceCircle"
        sourceComponent: retouchCircleComponent
        visible: retouchClickArea.hasRetouchSource
        width: 2 * retouchClickArea.brushRadius
        height: width
        x: retouchClickArea.retouchSourceX
            * retouchClickArea.width - width / 2
        y: retouchClickArea.retouchSourceY
            * retouchClickArea.height - height / 2
        z: 2
    }

    Loader {
        id: retouchBrushCursor
        objectName: "retouchBrushCursor"
        sourceComponent: retouchCircleComponent
        visible: retouchClickArea.containsMouse
                 && !retouchClickArea.ctrlPanning
        width: 2 * retouchClickArea.brushRadius
        height: width
        x: retouchClickArea.mouseX - width / 2
        y: retouchClickArea.mouseY - height / 2
        z: 3
    }
}
