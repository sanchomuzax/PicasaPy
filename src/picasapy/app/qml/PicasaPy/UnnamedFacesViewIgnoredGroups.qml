import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ListView {
    id: groupsList
    property var viewRoot: null
    objectName: "ignoredGroupsList"
    visible: viewRoot.ignoredMode
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.leftMargin: -15
    clip: true
    spacing: 12
    model: viewRoot.groupsModel
    ScrollBar.vertical: PicasaScrollBar {}

    delegate: ColumnLayout {
        id: groupDelegate
        required property var modelData
        width: groupsList.width
        spacing: 4

        Text {
            visible: !viewRoot.ignoredMode
            text: groupDelegate.modelData.label
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.textDark
        }

        GridView {
            id: faceGrid
            objectName: "ignoredFaceGrid"
            Layout.fillWidth: true
            interactive: false
            cellWidth: 194
            cellHeight: 198
            readonly property int columns:
                Math.max(1, Math.floor(width / cellWidth))
            height: Math.ceil(
                groupDelegate.modelData.faces.length
                / Math.max(1, columns)) * cellHeight
            model: groupDelegate.modelData.faces

            delegate: Item {
                id: ignoredFaceCard
                required property var modelData
                width: faceGrid.cellWidth
                height: faceGrid.cellHeight

                Column {
                    width: 172
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 2

                    Rectangle {
                        id: faceTile
                        objectName: "faceTile_" + ignoredFaceCard.modelData.faceId
                        width: 146
                        height: 172
                        x: (parent.width - width) / 2
                        color: "transparent"
                        border.width: 2
                        border.color: viewRoot.selectedFaceIds[ignoredFaceCard.modelData.faceId]
                                      ? Theme.panelSelectionActive : "transparent"

                        Image {
                            objectName: "ignoredFaceImage_"
                                        + ignoredFaceCard.modelData.faceId
                            anchors.fill: parent
                            source: ignoredFaceCard.modelData.thumbUrl
                            smooth: true
                            mipmap: true
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: viewRoot.toggleFace(ignoredFaceCard.modelData.faceId)
                        }

                        // A mellőzött nézetben az eredeti sem mutatja a mellőző X-et.
                        Rectangle {
                            objectName: "faceIgnoreX_"
                                        + ignoredFaceCard.modelData.faceId
                            visible: false
                            anchors.top: parent.top
                            anchors.right: parent.right
                            width: 18
                            height: 18
                            color: Theme.infoBar
                        }

                        Rectangle {
                            objectName: "suggestionBar_"
                                        + ignoredFaceCard.modelData.faceId
                            visible: (ignoredFaceCard.modelData.suggestedName || "") !== ""
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            anchors.margins: 3
                            height: 20
                            color: Theme.infoBar
                            Text {
                                anchors.centerIn: parent
                                text: qsTr("%1?").arg(
                                    ignoredFaceCard.modelData.suggestedName || "")
                                font.pixelSize: Theme.fontSize - 1
                                color: Theme.infoBarText
                            }
                        }
                    }

                    TextField {
                        objectName: "ignoredFaceNameField_"
                                    + ignoredFaceCard.modelData.faceId
                        width: 172
                        height: 20
                        padding: 1
                        horizontalAlignment: TextInput.AlignHCenter
                        verticalAlignment: TextInput.AlignVCenter
                        font.pixelSize: Theme.fontSize - 2
                        placeholderText: qsTr("Add a name")
                        background: Rectangle {
                            color: "#ffffff"
                            border.color: "#8a8a8a"
                            border.width: 1
                        }
                        TextFieldContextArea {}
                        onAccepted: {
                            var cleanName = text.trim()
                            if (!cleanName)
                                return
                            text = ""
                            viewRoot.nameSubmitted(
                                ignoredFaceCard.modelData.faceId, cleanName)
                        }
                    }
                }
            }
        }
    }
}

