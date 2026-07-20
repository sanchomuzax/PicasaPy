import QtQuick

// #147: a mentett faces= régiók megjelenítése a nézőben — csak olvasás,
// felismerés nélkül (a teljes Emberek-panel a #26-ban, V3). Az overlay a
// kép TÉNYLEGESEN kirajzolt (letterbox nélküli) területére kerül — a
// PhotoViewer ugyanígy pozicionálja a CropOverlay-t is.
Item {
    id: overlay
    objectName: "facesOverlay"

    // {left, top, right, bottom, name} elemek relatív [0..1] koordinátákkal
    // — a FacesHelper.facesFor() visszatérési formátuma.
    property var faces: []

    Repeater {
        model: overlay.faces
        delegate: Item {
            required property var modelData
            readonly property real relLeft: modelData.left
            readonly property real relTop: modelData.top
            readonly property real relRight: modelData.right
            readonly property real relBottom: modelData.bottom
            readonly property string personName: modelData.name || ""

            x: relLeft * overlay.width
            y: relTop * overlay.height
            width: Math.max(0, (relRight - relLeft) * overlay.width)
            height: Math.max(0, (relBottom - relTop) * overlay.height)

            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.color: "#ffd34e"
                border.width: 2
                radius: 2
            }
            Rectangle {
                visible: nameLabel.text.length > 0
                anchors.top: parent.bottom
                anchors.topMargin: 2
                anchors.horizontalCenter: parent.horizontalCenter
                width: nameLabel.implicitWidth + 8
                height: nameLabel.implicitHeight + 4
                radius: 3
                color: "#00000099"

                Text {
                    id: nameLabel
                    anchors.centerIn: parent
                    text: personName
                    color: "#ffffff"
                    font.pixelSize: Theme.fontSize - 1
                }
            }
        }
    }
}
