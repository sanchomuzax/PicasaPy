import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Name Tags" fül (options.fen) — V3/arcfelismerés hatókör.
//
// A névcímke-beállítások a FaceScanController meglévő motorjához kötődnek.
ColumnLayout {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.preferredWidth: parent ? parent.width : implicitWidth
    Layout.preferredHeight: 0
    spacing: 0
    readonly property var faceCtl:
        typeof faceScanController !== "undefined" ? faceScanController : null

    ColumnLayout {
        id: controls
        objectName: "optionsNameTagsControls"
        Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
        Layout.topMargin: 8
        Layout.preferredWidth: 434
        Layout.minimumWidth: 434
        Layout.maximumWidth: 434
        spacing: 0

        CheckBox {
            objectName: "optionsFaceDetectionCheck"
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            text: qsTr("Enable face detection")
            enabled: !!root.faceCtl
            checked: root.faceCtl ? root.faceCtl.automaticDetectionEnabled() : true
            onToggled: {
                if (root.faceCtl)
                    root.faceCtl.setAutomaticDetectionEnabled(checked)
            }
        }
        CheckBox {
            id: suggestionsCheck
            objectName: "optionsFaceSuggestionsCheck"
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            text: qsTr("Enable suggestions:")
            enabled: !!root.faceCtl
            checked: root.faceCtl ? root.faceCtl.suggestionsEnabled() : true
            onToggled: if (root.faceCtl)
                root.faceCtl.setSuggestionsEnabled(checked)
        }

        // Az options.fen külön behúzott, 20em széles, tízosztású
        // csúszkasort ír le. A képernyőkép alapján a címke jobb széle a sín
        // előtt áll, az érték pedig a sín jobb oldalára kerül. A FEN-ben
        // szereplő uploadcontactphotos vezérlőt a megszűnt szolgáltatás miatt
        // elrejtjük; a döntés a specifikációban dokumentált.
        Item { Layout.preferredHeight: 6 }
        RowLayout {
            objectName: "optionsFaceSuggestionThresholdRow"
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.preferredHeight: 23
            spacing: 8
            enabled: !!root.faceCtl && suggestionsCheck.checked

            Text {
                objectName: "optionsFaceSuggestionThresholdLabel"
                property bool rightAligned: horizontalAlignment === Text.AlignRight
                Layout.preferredWidth: 85
                Layout.minimumWidth: 85
                Layout.maximumWidth: 85
                Layout.alignment: Qt.AlignTop
                text: qsTr("Suggestion threshold:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 23
                spacing: 0
                PicasaSlider {
                    id: suggestionSlider
                    objectName: "optionsFaceSuggestionThresholdSlider"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 14
                    Layout.minimumHeight: 14
                    Layout.maximumHeight: 14
                    from: 50
                    to: 95
                    stepSize: 5
                    snapMode: Slider.SnapAlways
                    showTicks: false
                    value: root.faceCtl ? root.faceCtl.suggestionThreshold() : 85
                    onMoved: if (root.faceCtl)
                        root.faceCtl.setSuggestionThreshold(value)
                }
                Item {
                    id: suggestionTicks
                    objectName: "optionsFaceSuggestionThresholdTicks"
                    property int tickCount: suggestionTickRepeater.count
                    Layout.fillWidth: true
                    Layout.preferredHeight: 9
                    Repeater {
                        id: suggestionTickRepeater
                        model: Math.round(
                            (suggestionSlider.to - suggestionSlider.from)
                            / suggestionSlider.stepSize
                        ) + 1
                        delegate: Rectangle {
                            objectName: "optionsFaceSuggestionTick" + index
                            width: 1
                            height: 3
                            y: 5
                            x: 5 + index * (suggestionTicks.width - 10)
                                / (suggestionTickRepeater.count - 1)
                            color: "#c4c4c4"
                        }
                    }
                }
            }
            Text {
                objectName: "optionsFaceSuggestionThresholdValue"
                Layout.preferredWidth: 16
                Layout.minimumWidth: 16
                Layout.maximumWidth: 16
                Layout.alignment: Qt.AlignTop
                text: Math.round(suggestionSlider.value).toString()
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                verticalAlignment: Text.AlignVCenter
            }
        }

        Item { Layout.preferredHeight: 18 }
        RowLayout {
            objectName: "optionsFaceClusterThresholdRow"
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.preferredHeight: 23
            spacing: 8
            enabled: !!root.faceCtl && suggestionsCheck.checked

            Text {
                objectName: "optionsFaceClusterThresholdLabel"
                property bool rightAligned: horizontalAlignment === Text.AlignRight
                Layout.preferredWidth: 85
                Layout.minimumWidth: 85
                Layout.maximumWidth: 85
                Layout.alignment: Qt.AlignTop
                text: qsTr("Cluster threshold:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 23
                spacing: 0
                PicasaSlider {
                    id: clusterSlider
                    objectName: "optionsFaceClusterThresholdSlider"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 14
                    Layout.minimumHeight: 14
                    Layout.maximumHeight: 14
                    from: 50
                    to: 95
                    stepSize: 5
                    snapMode: Slider.SnapAlways
                    showTicks: false
                    value: root.faceCtl ? root.faceCtl.clusterThreshold() : 70
                    onMoved: if (root.faceCtl)
                        root.faceCtl.setClusterThreshold(value)
                }
                Item {
                    id: clusterTicks
                    objectName: "optionsFaceClusterThresholdTicks"
                    property int tickCount: clusterTickRepeater.count
                    Layout.fillWidth: true
                    Layout.preferredHeight: 9
                    Repeater {
                        id: clusterTickRepeater
                        model: Math.round(
                            (clusterSlider.to - clusterSlider.from)
                            / clusterSlider.stepSize
                        ) + 1
                        delegate: Rectangle {
                            objectName: "optionsFaceClusterTick" + index
                            width: 1
                            height: 3
                            y: 5
                            x: 5 + index * (clusterTicks.width - 10)
                                / (clusterTickRepeater.count - 1)
                            color: "#c4c4c4"
                        }
                    }
                }
            }
            Text {
                objectName: "optionsFaceClusterThresholdValue"
                Layout.preferredWidth: 16
                Layout.minimumWidth: 16
                Layout.maximumWidth: 16
                Layout.alignment: Qt.AlignTop
                text: Math.round(clusterSlider.value).toString()
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                verticalAlignment: Text.AlignVCenter
            }
        }

        Item { Layout.preferredHeight: 14 }
        CheckBox {
            objectName: "optionsFacePersistToFileCheck"
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            text: qsTr("Store name tags in the file")
            enabled: !!root.faceCtl
            checked: root.faceCtl ? root.faceCtl.persistFaceToFile() : true
            onToggled: if (root.faceCtl)
                root.faceCtl.setPersistFaceToFile(checked)
        }
        CheckBox {
            objectName: "optionsFaceUploadContactPhotosCheck"
            visible: false
            Layout.fillWidth: true
            Layout.preferredHeight: 0
            Layout.minimumHeight: 0
            Layout.maximumHeight: 0
            text: qsTr("Upload people album thumbnails to Google Contacts")
            enabled: false
        }
    }

    Item { Layout.fillHeight: true }
}
