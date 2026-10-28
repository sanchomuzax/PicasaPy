import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

GridView {
    id: unnamedFacesGrid
    property var viewRoot: null
    objectName: "unnamedGroupsList"
    visible: !viewRoot.ignoredMode
    Layout.fillWidth: true
    Layout.fillHeight: true
    clip: true
    cellWidth: viewRoot.grouped ? 194 : 162
    cellHeight: 198
    readonly property int columns: Math.max(1, Math.floor(width / cellWidth))
    height: Math.ceil(viewRoot.facesModel.length / columns) * cellHeight
    model: viewRoot.facesModel
    ScrollBar.vertical: PicasaScrollBar {}

    delegate: Item {
        id: faceCard
        required property var modelData
        objectName: "unnamedFaceCard_" + faceCard.modelData.faceId
        property var nameSuggestions: []
        property int selectedSuggestionIndex: -1
        width: unnamedFacesGrid.cellWidth
        height: unnamedFacesGrid.cellHeight

        function refreshNameSuggestions() {
            var needle = faceNameField.text.trim().toLocaleLowerCase()
            if (!needle || typeof controller === "undefined" || !controller
                    || !controller.nameSuggestions) {
                faceCard.nameSuggestions = []
                faceCard.selectedSuggestionIndex = -1
                return
            }
            faceCard.nameSuggestions = controller.nameSuggestions(needle)
            faceCard.selectedSuggestionIndex = -1
        }

        // #5285: a névadás egy útja Enterre és a javaslat kattintására
        // is: a mező kiürül, a javaslat-lista záródik
        function submitName(name) {
            faceNameField.text = ""
            faceCard.nameSuggestions = []
            faceCard.selectedSuggestionIndex = -1
            viewRoot.nameSubmitted(faceCard.modelData.faceId, name)
        }

        function acceptSelectedSuggestion() {
            var selectedIndex = faceCard.selectedSuggestionIndex
            if (selectedIndex < 0 || selectedIndex >= faceCard.nameSuggestions.length)
                return false
            faceCard.submitName(
                String(faceCard.nameSuggestions[selectedIndex].name || ""))
            return true
        }

        Column {
            width: 172
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 2

            Rectangle {
                id: faceTile
                objectName: "faceTile_" + faceCard.modelData.faceId
                width: viewRoot.grouped ? 146 : 120
                height: viewRoot.grouped ? 172 : 145
                x: viewRoot.grouped ? 0 : 13
                color: "transparent"
                border.width: 2
                border.color: viewRoot.selectedFaceIds[faceCard.modelData.faceId]
                              ? Theme.panelSelectionActive : "transparent"

                Image {
                    objectName: "faceImage_" + faceCard.modelData.faceId
                    anchors.fill: parent
                    source: faceCard.modelData.thumbUrl
                    smooth: true
                    mipmap: true
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: viewRoot.toggleFace(faceCard.modelData.faceId)
                }

                Rectangle {
                    objectName: "faceIgnoreX_" + faceCard.modelData.faceId
                    visible: viewRoot.grouped
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.margins: 2
                    width: 13
                    height: 13
                    radius: 0
                    color: "#ffffff"
                    border.color: "#1b1b1b"
                    border.width: 1
                    Text {
                        anchors.centerIn: parent
                        text: "X"
                        font.pixelSize: 8
                        font.bold: true
                        color: "#111111"
                    }
                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -2
                        onClicked: viewRoot.requestIgnore(
                            [faceCard.modelData.faceId])
                    }
                }

                Rectangle {
                    objectName: "suggestionBar_" + faceCard.modelData.faceId
                    visible: (faceCard.modelData.suggestedName || "") !== ""
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 3
                    height: 20
                    color: Theme.infoBar
                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 4
                        spacing: 4
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - 22
                            elide: Text.ElideRight
                            text: qsTr("%1?").arg(
                                faceCard.modelData.suggestedName || "")
                            font.pixelSize: Theme.fontSize - 1
                            color: Theme.infoBarText
                        }
                        Text {
                            objectName: "suggestionYes_"
                                        + faceCard.modelData.faceId
                            anchors.verticalCenter: parent.verticalCenter
                            text: "✓"
                            color: Theme.infoBarText
                            MouseArea {
                                anchors.fill: parent
                                anchors.margins: -4
                                onClicked: viewRoot.acceptSuggestion(
                                    faceCard.modelData.faceId)
                            }
                        }
                    }
                }
            }

            TextField {
                id: faceNameField
                objectName: "unnamedFaceNameField_"
                            + faceCard.modelData.faceId
                visible: viewRoot.grouped
                width: 172
                height: 20
                x: (faceTile.width - width) / 2
                padding: 1
                horizontalAlignment: TextInput.AlignHCenter
                verticalAlignment: TextInput.AlignVCenter
                font.pixelSize: Theme.fontSize - 2
                placeholderText: qsTr("Add a name")
                background: Rectangle {
                    color: "#ffffff"
                    border.color: "#8a8a8a"
                    border.width: 1
                    radius: 0
                }
                TextFieldContextArea {}
                onAccepted: {
                    if (faceCard.acceptSelectedSuggestion())
                        return
                    var name = text.trim()
                    if (!name)
                        return
                    faceCard.submitName(name)
                }
                onTextEdited: faceCard.refreshNameSuggestions()
                Keys.onPressed: function(event) {
                    var count = faceCard.nameSuggestions.length
                    if (count === 0)
                        return
                    if (event.key === Qt.Key_Down) {
                        faceCard.selectedSuggestionIndex = Math.min(
                            count - 1,
                            faceCard.selectedSuggestionIndex + 1
                        )
                        event.accepted = true
                    } else if (event.key === Qt.Key_Up) {
                        faceCard.selectedSuggestionIndex =
                            faceCard.selectedSuggestionIndex < 0
                            ? count - 1
                            : Math.max(0, faceCard.selectedSuggestionIndex - 1)
                        event.accepted = true
                    }
                }
            }
        }

        Popup {
            id: nameSuggestionsPopup
            objectName: "unnamedNameSuggestionPopup_"
                        + faceCard.modelData.faceId
            parent: Overlay.overlay
            property var suggestions: faceCard.nameSuggestions
            readonly property point rootPosition:
                viewRoot.mapToItem(parent, 0, 0)
            readonly property real nameFieldX:
                rootPosition.x + unnamedFacesGrid.x
                - unnamedFacesGrid.contentX + faceCard.x
                + faceNameField.parent.x + faceNameField.x
            readonly property real nameFieldY:
                rootPosition.y + unnamedFacesGrid.y
                - unnamedFacesGrid.contentY + faceCard.y
                + faceNameField.parent.y + faceNameField.y
            x: nameFieldX + (faceNameField.width - width) / 2
            y: nameFieldY + faceNameField.height
            width: 212
            height: Math.min(170, suggestions.length * 42 + 2)
            visible: faceNameField.activeFocus
                     && faceNameField.text.trim().length > 0
                     && suggestions.length > 0
            z: 1000
            padding: 0
            closePolicy: Popup.NoAutoClose

            background: Rectangle {
                objectName: "unnamedNameSuggestions_"
                            + faceCard.modelData.faceId
                color: "#ffffff"
                border.color: "#8a8a8a"
                border.width: 1
            }

            contentItem: ListView {
                anchors.fill: parent
                clip: true
                model: nameSuggestionsPopup.suggestions
                delegate: Item {
                    required property var modelData
                    required property int index
                    objectName: "unnamedFaceSuggestion_"
                                + faceCard.modelData.faceId + "_" + index
                    property string personName: String(modelData.name)
                    property string thumbUrl: String(modelData.thumbUrl || "")
                    width: ListView.view.width
                    height: 40
                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: Theme.panelSelectionActive
                        border.width: faceCard.selectedSuggestionIndex === index ? 1 : 0
                    }
                    Image {
                        objectName: "unnamedFaceSuggestionImage_"
                                    + faceCard.modelData.faceId + "_" + index
                        anchors.left: parent.left
                        anchors.leftMargin: 17
                        anchors.verticalCenter: parent.verticalCenter
                        width: 28
                        height: 30
                        source: parent.thumbUrl !== ""
                                ? parent.thumbUrl
                                : Qt.resolvedUrl(
                                      "icons/person-silhouette.svg")
                        fillMode: Image.PreserveAspectCrop
                        smooth: true
                        mipmap: true
                        asynchronous: true
                    }
                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 58
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width - 64
                        text: parent.personName
                        font.pixelSize: Theme.fontSize - 1
                        color: Theme.textDark
                        elide: Text.ElideRight
                    }
                    // #5285: a tételre kattintás a kattintott személy nevét
                    // nevezi meg, ugyanazon az úton, mint az Enter
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            faceCard.selectedSuggestionIndex = index
                            faceCard.submitName(parent.personName)
                        }
                    }
                }
            }
        }
    }
}

