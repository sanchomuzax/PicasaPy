import QtQuick
import QtQuick.Controls

// A jobb oldali Emberek-panel egyik arcos sora (#4511).
Rectangle {
    id: row
    property string personName: ""
    property string photoUrl: ""
    property bool unnamedFace: false
    property int faceId: -1
    property string suggestedName: ""
    property real availableWidth: 266
    signal chosen()
    signal nameSubmitted(int faceId, string name)
    signal ignoreRequested(int faceId)
    signal suggestionAccepted(int faceId)
    signal suggestionRejected(int faceId)
    signal faceDropped(int faceId, string personName)

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
        anchors.leftMargin: row.unnamedFace ? 3 : 7
        anchors.verticalCenter: parent.verticalCenter
        width: 60
        height: 70
        source: row.photoUrl
        smooth: true
        mipmap: true
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }

    Item {
        id: faceDragProxy
        objectName: row.unnamedFace
                    ? "peopleFaceDragProxy_" + row.faceId : ""
        x: faceImage.x + faceImage.width / 2
        y: faceImage.y + faceImage.height / 2
        width: 1
        height: 1
        visible: row.unnamedFace
        readonly property string payload: "face"
        readonly property int draggedFaceId: row.faceId
        Drag.active: faceDragMouse.dragging
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.MoveAction
        Drag.hotSpot.x: 0
        Drag.hotSpot.y: 0
    }

    MouseArea {
        id: faceDragMouse
        objectName: row.unnamedFace
                    ? "peopleFaceDragArea_" + row.faceId : ""
        x: faceImage.x
        y: faceImage.y
        width: faceImage.width
        height: faceImage.height
        visible: row.unnamedFace
        acceptedButtons: Qt.LeftButton
        preventStealing: true
        property bool dragging: false
        property real pressX: 0
        property real pressY: 0
        onPressed: function(mouse) {
            pressX = mouse.x
            pressY = mouse.y
            dragging = false
        }
        onPositionChanged: function(mouse) {
            if (!pressed) return
            var dx = mouse.x - pressX
            var dy = mouse.y - pressY
            if (!dragging && Math.abs(dx) + Math.abs(dy) > 8)
                dragging = true
            if (dragging) {
                var point = faceDragMouse.mapToItem(row, mouse.x, mouse.y)
                faceDragProxy.x = point.x
                faceDragProxy.y = point.y
            }
        }
        onReleased: function(mouse) {
            if (dragging) {
                faceDragProxy.Drag.drop()
                dragging = false
            }
        }
    }

    DropArea {
        objectName: !row.unnamedFace
                    ? "peoplePanelPersonDropArea_" + row.personName : ""
        anchors.fill: parent
        enabled: !row.unnamedFace
        onDropped: function(drop) {
            var source = drop.source
            if (!source || source.payload !== "face"
                    || Number(source.draggedFaceId) < 0)
                return
            drop.accept()
            row.faceDropped(Number(source.draggedFaceId), row.personName)
        }
    }

    Text {
        objectName: "peoplePanelName_" + row.personName
        visible: !row.unnamedFace
        anchors.left: faceImage.right
        anchors.leftMargin: 16
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.top: parent.top
        anchors.topMargin: 7
        text: row.personName
        elide: Text.ElideRight
        font.pixelSize: 16
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
        anchors.top: row.suggestedName.length > 0 ? parent.top : undefined
        anchors.topMargin: 7
        anchors.verticalCenter:
            row.suggestedName.length === 0 ? parent.verticalCenter : undefined
        height: 22
        placeholderText: qsTr("Add a name")
        font.pixelSize: Theme.fontSize - 1
        Keys.onReturnPressed: row.submitName(nameField.text)
        TextFieldContextArea {}
    }

    Rectangle {
        id: suggestionYes
        objectName: "peoplePanelSuggestionYes_" + row.faceId
        visible: row.unnamedFace && row.suggestedName.length > 0
        anchors.left: faceImage.right
        anchors.top: nameField.bottom
        anchors.topMargin: 5
        width: 27
        height: 22
        radius: 2
        color: Theme.infoBar
        border.width: 1
        border.color: Theme.panelSelectionActive

        Text {
            anchors.centerIn: parent
            text: "✓"
            font.pixelSize: Theme.fontSize - 1
            color: Theme.infoBarText
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: row.suggestionAccepted(row.faceId)
        }
    }

    Rectangle {
        id: suggestionNo
        objectName: "peoplePanelSuggestionNo_" + row.faceId
        visible: row.unnamedFace && row.suggestedName.length > 0
        anchors.left: suggestionYes.right
        anchors.leftMargin: 5
        anchors.top: suggestionYes.top
        width: 27
        height: 22
        radius: 2
        color: Theme.infoBar
        border.width: 1
        border.color: Theme.panelSelectionActive

        Text {
            anchors.centerIn: parent
            text: "✗"
            font.pixelSize: Theme.fontSize - 1
            color: Theme.infoBarText
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: row.suggestionRejected(row.faceId)
        }
    }

    Text {
        objectName: "peoplePanelSuggestionName_" + row.faceId
        visible: row.unnamedFace && row.suggestedName.length > 0
        anchors.left: suggestionNo.right
        anchors.leftMargin: 5
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.verticalCenter: suggestionNo.verticalCenter
        text: qsTr("%1?").arg(row.suggestedName)
        elide: Text.ElideRight
        font.pixelSize: Theme.fontSize - 1
        color: Theme.panelSelectionText
    }

    Rectangle {
        id: ignoreButton
        objectName: "peoplePanelIgnoreX_"
                    + (row.unnamedFace ? row.faceId : row.personName)
        visible: true
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
            enabled: row.unnamedFace
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: row.ignoreRequested(row.faceId)
        }
        ToolTip.visible: ignoreMouse.containsMouse
        ToolTip.text: qsTr("Ignore person")
        ToolTip.delay: Theme.tooltipDelay
    }
}
