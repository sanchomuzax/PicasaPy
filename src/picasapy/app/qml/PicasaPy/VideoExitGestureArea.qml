import QtQuick

// A videó-előnézeti felület kilépési gesztusa. A komponens Qt Multimedia
// nélkül is tesztelhető, és kizárólag a videó képterületét fedi le.
Item {
    id: root

    implicitWidth: 640
    implicitHeight: 360
    property bool singleClickExit: false
    signal exitRequested()

    MouseArea {
        objectName: "videoExitMouseArea"
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onPressed: {
            if (root.singleClickExit)
                root.exitRequested()
        }
        onDoubleClicked: {
            if (!root.singleClickExit)
                root.exitRequested()
        }
    }
}
