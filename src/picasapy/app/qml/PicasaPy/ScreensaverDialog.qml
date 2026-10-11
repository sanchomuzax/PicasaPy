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
        // a bejegyzést közben kívülről is törölhették: a vezérlő újraolvassa
        if (dialog.saverController
                && dialog.saverController.refreshScreensaverIdle !== undefined)
            dialog.saverController.refreshScreensaverIdle()
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
        idleMinutesBox.value = dialog.saverController
                ? dialog.saverController.screensaverIdleMinutes : 10
        dialog.idleSaveFailed = false
    }

    //: #4613: a tétlenségi indítás állapota a vezérlőből; a kattintás után
    //: a kötés visszaáll, így a pipa mindig a valódi bejegyzést mutatja
    readonly property bool idleSupported: (dialog.saverController
            && dialog.saverController.screensaverIdleSupported !== undefined)
        ? dialog.saverController.screensaverIdleSupported : false
    readonly property bool idleEnabled: (dialog.saverController
            && dialog.saverController.screensaverIdleEnabled !== undefined)
        ? dialog.saverController.screensaverIdleEnabled : false
    readonly property bool idleAutostart: (dialog.saverController
            && dialog.saverController.screensaverIdleAutostart !== undefined)
        ? dialog.saverController.screensaverIdleAutostart : true
    readonly property string idleReason: dialog.saverController
        ? dialog.saverController.screensaverIdleReason : "not-linux"
    readonly property string idleDesktop: dialog.saverController
        ? dialog.saverController.screensaverIdleDesktop : ""
    property bool idleSaveFailed: false
    readonly property string idleMessage: {
        if (dialog.idleSaveFailed)
            return qsTr("The setting could not be saved.")
        if (dialog.idleReason === "not-linux")
            return qsTr("Starting when the computer is idle is only available on Linux.")
        if (dialog.idleReason === "no-swayidle")
            return qsTr("Install the swayidle package to use this option.")
        if (dialog.idleReason === "desktop")
            return qsTr("Not supported on this desktop (%1). It works on wlroots-based Wayland desktops (labwc, sway, Wayfire) with swayidle.")
                .arg(dialog.idleDesktop.length > 0 ? dialog.idleDesktop : qsTr("unknown"))
        if (dialog.idleSupported && !dialog.idleAutostart)
            return qsTr("This desktop does not start it by itself after you log in again; it works in the current session.")
        return ""
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

        RowLayout {
            Layout.fillWidth: true
            CheckBox {
                id: idleCheck
                objectName: "screensaverIdleCheck"
                text: qsTr("Start when the computer is idle for")
                enabled: dialog.idleSupported
                checked: dialog.idleEnabled
                onClicked: {
                    var ok = dialog.saverController
                            ? dialog.saverController.setScreensaverIdleEnabled(checked)
                            : false
                    dialog.idleSaveFailed = !ok
                    checked = Qt.binding(function() { return dialog.idleEnabled })
                }
            }
            SpinBox {
                id: idleMinutesBox
                objectName: "screensaverIdleMinutes"
                from: 1
                to: 120
                value: 10
                editable: true
                enabled: dialog.idleSupported
                // a nyilak nevet kapnak, hogy a felület-teszt rájuk kattinthasson
                Component.onCompleted: {
                    if (up.indicator) up.indicator.objectName = "screensaverIdleMinutesUp"
                    if (down.indicator) down.indicator.objectName = "screensaverIdleMinutesDown"
                }
                onValueModified: {
                    if (dialog.saverController)
                        dialog.idleSaveFailed =
                            !dialog.saverController.setScreensaverIdleMinutes(value)
                }
            }
            Text {
                text: qsTr("minutes")
                font.pixelSize: Theme.fontSize
                color: dialog.idleSupported ? Theme.ink : Theme.textGray
            }
        }

        Text {
            objectName: "screensaverIdleMessage"
            visible: text.length > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: dialog.idleMessage
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
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
