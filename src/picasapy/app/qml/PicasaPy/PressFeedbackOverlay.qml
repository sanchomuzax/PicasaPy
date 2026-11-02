import QtQuick

// Az egér-/érintéskezelő célterületét sötétíti, amíg az lenyomott.
Rectangle {
    id: feedback
    property var pressSource: null

    anchors.fill: parent
    visible: feedback.pressSource !== null && feedback.pressSource.pressed
    z: 10000
    color: "#26000000"
}
