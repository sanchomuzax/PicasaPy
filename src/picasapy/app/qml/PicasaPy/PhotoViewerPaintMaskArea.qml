import QtQuick

// #3541: az ECSET csak a Vámpírszemnél aktív; a négy
// teljes képre ható effekt nem festhető. A mutató KÖR alakú
// (`thumbui/circlecursor`, mérve), az átmérőjét a panel
// csúszkája adja; a vonás a KIRAJZOLT képhez normálva megy
// a vezérlőnek, tehát a nagyítástól független.
//: #3741: a `photo` helyett a `photoArea.fokuszKep` a
//: szülő — a festés a TÉNYLEGESEN szerkesztett félen megy.
MouseArea {
    required property var photoArea
    id: paintMaskArea
    objectName: "paintMaskArea"
    parent: photoArea.fokuszKep
    z: 5
    readonly property bool aktiv:
        (typeof editController !== "undefined" && editController
         && editController.paintMaskSupported !== undefined)
            ? editController.paintMaskSupported : false
    visible: paintMaskArea.aktiv
    enabled: paintMaskArea.aktiv
    hoverEnabled: true
    x: (photoArea.fokuszKep.width
        - photoArea.fokuszKep.paintedWidth) / 2
    y: (photoArea.fokuszKep.height
        - photoArea.fokuszKep.paintedHeight) / 2
    width: photoArea.fokuszKep.paintedWidth
    height: photoArea.fokuszKep.paintedHeight
    //: a rendszer-kurzort elrejtjük: a KÖR maga a mutató
    cursorShape: Qt.BlankCursor

    function fess(pont) {
        if (typeof editController === "undefined" || !editController) return
        editController.paintStroke(
            pont.x / Math.max(1, width),
            pont.y / Math.max(1, height))
    }
    onPressed: function (eger) { paintMaskArea.fess(eger) }
    onPositionChanged: function (eger) {
        if (eger.buttons) paintMaskArea.fess(eger)
    }

    //: a kör alakú mutató — a sugár a kép RÖVIDEBB
    //: oldalához mért arány (a vezérlő így számol)
    Rectangle {
        objectName: "paintMaskCursor"
        visible: paintMaskArea.containsMouse
        readonly property real sugar:
            ((typeof editController !== "undefined" && editController
              && editController.paintBrushRatio !== undefined)
                ? editController.paintBrushRatio : 0.03)
            * Math.min(paintMaskArea.width,
                       paintMaskArea.height)
        width: 2 * sugar
        height: 2 * sugar
        radius: sugar
        x: paintMaskArea.mouseX - sugar
        y: paintMaskArea.mouseY - sugar
        color: "transparent"
        border.width: 1
        border.color: (typeof editController !== "undefined"
                       && editController && editController.paintEraser)
            ? "#ff6666" : "#ffffff"
    }
}
