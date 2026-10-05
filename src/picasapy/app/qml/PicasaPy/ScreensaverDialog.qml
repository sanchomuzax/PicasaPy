import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A Linuxos képernyővédő saját helyi forrásokat használ (#4259). A régi
// Picasa-mezők közül a forrás, az effekt, a képidő és a felirat marad; a
// megszűnt webalbum- és RSS-források nem választhatók.
Dialog {
    id: dialog
    objectName: "screensaverDialog"
    title: qsTr("Configure Screensaver...")
    modal: true
    focus: true
    width: 500
    parent: Overlay.overlay
    anchors.centerIn: parent
    standardButtons: Dialog.Ok | Dialog.Cancel

    signal previewRequested()
    property var saverController: null

    readonly property var effects: [
        { key: "cut", label: qsTr("Cut") },
        { key: "dissolve", label: qsTr("Dissolve") },
        { key: "dissolveblack", label: qsTr("Dissolve through black") },
        { key: "dissolvewhite", label: qsTr("Dissolve through white") },
        { key: "kenburns", label: qsTr("Pan and Zoom") }
    ]
    readonly property var sources:
        dialog.saverController ? dialog.saverController.screensaverSources : []
    readonly property int selectedPhotoCount: {
        var total = 0
        for (var i = 0; i < dialog.sources.length; ++i) {
            if (dialog.sources[i].selected)
                total += Number(dialog.sources[i].count)
        }
        return total
    }

    function frissitsd() {
        var effect = dialog.saverController
                   ? dialog.saverController.screensaverEffect : "dissolve"
        effectBox.currentIndex = 0
        for (var i = 0; i < dialog.effects.length; ++i) {
            if (dialog.effects[i].key === effect) {
                effectBox.currentIndex = i
                break
            }
        }
        secondsSlider.value = dialog.saverController
                ? dialog.saverController.screensaverSeconds : 3.0
        captionCheck.checked = dialog.saverController
                ? dialog.saverController.screensaverShowCaptions : true
    }

    onOpened: dialog.frissitsd()
    onAccepted: close()
    onRejected: close()

    ColumnLayout {
        width: parent ? parent.width : 460
        spacing: 10

        Text {
            Layout.fillWidth: true
            text: qsTr("Display photos from:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        ScrollView {
            id: sourceScroll
            objectName: "screensaverSourceList"
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(176, Math.max(64, sourceColumn.implicitHeight))
            clip: true

            ColumnLayout {
                id: sourceColumn
                width: sourceScroll.availableWidth
                spacing: 2

                Repeater {
                    model: dialog.sources
                    delegate: CheckBox {
                        required property var modelData
                        required property int index
                        objectName: "screensaverSourceCheck" + index
                        Layout.fillWidth: true
                        text: modelData.kind === "photos"
                              ? qsTr("Selected Pictures") : modelData.name
                        checked: modelData.selected
                        onClicked: {
                            if (dialog.saverController)
                                dialog.saverController.setScreensaverSource(
                                    modelData.key, checked)
                        }
                    }
                }
            }
        }

        Text {
            objectName: "screensaverNoSourcesText"
            visible: dialog.sources.length === 0
            Layout.fillWidth: true
            text: qsTr("No folders or albums contain pictures.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: qsTr("Visual effect:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ComboBox {
                id: effectBox
                objectName: "screensaverEffectBox"
                Layout.fillWidth: true
                model: dialog.effects
                textRole: "label"
                onActivated: function(index) {
                    if (dialog.saverController)
                        dialog.saverController.setScreensaverEffect(
                            dialog.effects[index].key)
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: qsTr("Change pictures every:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Slider {
                id: secondsSlider
                objectName: "screensaverSecondsSlider"
                Layout.fillWidth: true
                from: 1
                to: 30
                stepSize: 1
                onMoved: if (dialog.saverController)
                    dialog.saverController.setScreensaverSeconds(value)
            }
            Text {
                objectName: "screensaverSecondsValue"
                text: qsTr("%1 seconds").arg(Math.round(secondsSlider.value))
                font.pixelSize: Theme.fontSize - 1
                color: Theme.textGray
            }
        }

        CheckBox {
            id: captionCheck
            objectName: "screensaverCaptionCheck"
            text: qsTr("Show captions")
            onClicked: if (dialog.saverController)
                dialog.saverController.setScreensaverShowCaptions(checked)
        }

        Button {
            id: previewButton
            objectName: "screensaverPreviewButton"
            Layout.alignment: Qt.AlignRight
            text: qsTr("Preview")
            enabled: dialog.selectedPhotoCount > 0
            onClicked: {
                dialog.close()
                dialog.previewRequested()
            }
        }
    }
}
