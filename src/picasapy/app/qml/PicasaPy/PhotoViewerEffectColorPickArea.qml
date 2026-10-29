import QtQuick

//: #5674: az effekt-színparaméter pipettája: ugyanazon a
//: KIRAJZOLT képen mintavesz, mint a semleges szín pipettája.
//: A szín a cél-paraméter sorába megy, és a legutóbbi színek
//: közé is bekerül (ugyanaz az út, mint a színminta).
MouseArea {
    required property var photoArea
    id: effectColorPickArea
    objectName: "effectColorPickArea"
    parent: photoArea.fokuszKep
    visible: photoArea.hostEditorPanel.effectColorPickerTarget >= 0
    enabled: photoArea.hostEditorPanel.effectColorPickerTarget >= 0
    x: (photoArea.fokuszKep.width
        - photoArea.fokuszKep.paintedWidth) / 2
    y: (photoArea.fokuszKep.height
        - photoArea.fokuszKep.paintedHeight) / 2
    width: photoArea.fokuszKep.paintedWidth
    height: photoArea.fokuszKep.paintedHeight
    cursorShape: Qt.CrossCursor
    onClicked: function(mouse) {
        if (typeof editController === "undefined" || !editController) return
        var hex = editController.pickEffectColor(
            mouse.x / Math.max(1, width),
            mouse.y / Math.max(1, height))
        if (hex !== "") {
            photoArea.hostEditorPanel.updateParamValue(
                photoArea.hostEditorPanel.effectColorPickerTarget, hex)
            editController.rememberPickerColor(hex)
        }
        photoArea.hostEditorPanel.effectColorPickerTarget = -1
    }
}
