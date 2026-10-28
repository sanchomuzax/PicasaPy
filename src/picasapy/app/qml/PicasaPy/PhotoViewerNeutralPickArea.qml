import QtQuick

// #464: a „semleges szín" pipetta — amíg aktív, a képre
// kattintás színmintát vesz (nem navigál). A kattintás
// helyét a KIRAJZOLT képhez képest normálva adjuk át, így
// a nagyítástól/illesztéstől független.

//: #3741: a `photo` helyett a `photoArea.fokuszKep` a
//: szülő — a pipetta a TÉNYLEGESEN szerkesztett félen ül.
MouseArea {
    required property var photoArea
    id: neutralPickArea
    objectName: "neutralPickArea"
    parent: photoArea.fokuszKep
    visible: photoArea.hostEditorPanel.neutralPickerActive
    enabled: photoArea.hostEditorPanel.neutralPickerActive
    x: (photoArea.fokuszKep.width
        - photoArea.fokuszKep.paintedWidth) / 2
    y: (photoArea.fokuszKep.height
        - photoArea.fokuszKep.paintedHeight) / 2
    width: photoArea.fokuszKep.paintedWidth
    height: photoArea.fokuszKep.paintedHeight
    cursorShape: Qt.CrossCursor
    onClicked: function(mouse) {
        if (typeof editController === "undefined" || !editController) return
        editController.pickNeutralColor(
            mouse.x / Math.max(1, width),
            mouse.y / Math.max(1, height))
        photoArea.hostEditorPanel.neutralPickerActive = false
    }
}
