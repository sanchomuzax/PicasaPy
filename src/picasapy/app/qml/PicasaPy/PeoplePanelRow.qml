import QtQuick

// Egy sor az Emberek-panelen (#26): név + a fotók száma.
//
// A darabszám formátuma az eredeti `PeoplePanel::Cluster` = „%d photos".
// A sor kattintható: a személy albumára vált.
Rectangle {
    id: row
    property string personName: ""
    property int photoCount: 0
    signal chosen()

    objectName: "peoplePanelRow_" + personName
    height: 20
    color: rowMouse.containsMouse ? Theme.panelSelection : "transparent"

    Row {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 4
        spacing: 5
        Text {
            text: row.personName
            font.pixelSize: Theme.fontSize
            color: rowMouse.containsMouse ? Theme.panelSelectionText : Theme.ink
        }
        Text {
            objectName: "peoplePanelCount_" + row.personName
            text: qsTr("%1 photos").arg(row.photoCount)
            font.pixelSize: Theme.fontSize - 1
            color: rowMouse.containsMouse ? Theme.panelSelectionText : Theme.textGray
        }
    }

    MouseArea {
        id: rowMouse
        anchors.fill: parent
        hoverEnabled: true
        onClicked: row.chosen()
    }
}
