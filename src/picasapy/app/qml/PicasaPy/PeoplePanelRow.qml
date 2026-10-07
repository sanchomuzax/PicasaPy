import QtQuick
import QtQuick.Controls

// A jobb oldali Emberek-panel egyik arcos sora (#4511).
Rectangle {
    id: row
    property string personName: ""
    property string photoUrl: ""
    property bool unnamedFace: false
    property int faceId: -1
    property real availableWidth: 266
    signal chosen()
    signal nameSubmitted(int faceId, string name)
    signal ignoreRequested(int faceId)

    function submitName(name) {
        var cleanName = String(name).trim()
        if (row.unnamedFace && cleanName.length > 0)
            row.nameSubmitted(row.faceId, cleanName)
    }

    objectName: row.unnamedFace
        ? "peoplePanelFaceRow_" + row.faceId
        : "peoplePanelRow_" + row.personName
    width: row.availableWidth
    height: 76
    radius: 5
    color: Theme.panelSelectionActive
    border.width: 1
    border.color: Theme.panelSelectionActive

    // A named sor a személyalbumra kattintható; a névtelen sor vezérlői
    // közvetlenül kapják az egeret és a billentyűzetet.
    MouseArea {
        anchors.fill: parent
        enabled: !row.unnamedFace
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: row.chosen()
    }

    Image {
        id: faceImage
        objectName: "peoplePanelFaceImage_"
                    + (row.unnamedFace ? row.faceId : row.personName)
        anchors.left: parent.left
        anchors.leftMargin: 7
        anchors.verticalCenter: parent.verticalCenter
        width: 60
        height: 70
        source: row.photoUrl
        smooth: true
        mipmap: true
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }

    Text {
        objectName: "peoplePanelName_" + row.personName
        visible: !row.unnamedFace
        anchors.left: faceImage.right
        anchors.leftMargin: 16
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.verticalCenter: parent.verticalCenter
        text: row.personName
        elide: Text.ElideRight
        font.pixelSize: Theme.fontSize
        color: Theme.panelSelectionText
    }

    TextField {
        id: nameField
        objectName: "peoplePanelAddName_"
                    + (row.unnamedFace ? row.faceId : row.personName)
        visible: row.unnamedFace
        anchors.left: faceImage.right
        anchors.leftMargin: 16
        anchors.right: parent.right
        anchors.rightMargin: 20
        anchors.verticalCenter: parent.verticalCenter
        height: 22
        placeholderText: qsTr("Add a name")
        font.pixelSize: Theme.fontSize - 1
        Keys.onReturnPressed: row.submitName(nameField.text)
        TextFieldContextArea {}
    }

    Rectangle {
        id: ignoreButton
        objectName: "peoplePanelIgnoreX_"
                    + (row.unnamedFace ? row.faceId : row.personName)
        visible: row.unnamedFace
        anchors.top: faceImage.top
        anchors.right: faceImage.right
        width: 13
        height: 13
        color: "#222222"
        border.width: 1
        border.color: "#ffffff"

        Text {
            anchors.centerIn: parent
            text: "×"
            font.pixelSize: 11
            font.bold: true
            color: "#ffffff"
        }

        MouseArea {
            id: ignoreMouse
            anchors.fill: parent
            anchors.margins: -3
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: row.ignoreRequested(row.faceId)
        }
        ToolTip.visible: ignoreMouse.containsMouse
        ToolTip.text: qsTr("Ignore person")
        ToolTip.delay: Theme.tooltipDelay
    }
}
