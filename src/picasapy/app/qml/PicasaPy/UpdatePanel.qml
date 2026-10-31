import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: root
    objectName: "updateDialog"
    property var updateAgent: null
    property bool noticeAllowed: false
    property var strings: ({})
    property bool pendingNotice: false
    property string feedback: ""

    function checkForUpdates() {
        feedback = ""
        open()
        if (updateAgent)
            updateAgent.checkForUpdates()
        else
            feedback = strings.couldNotCheck
    }

    title: updateAgent && updateAgent.updateAvailable
        ? strings.available.arg(updateAgent.availableVersion)
        : strings.dialogTitle
    modal: true
    focus: true
    anchors.centerIn: Overlay.overlay
    width: 520
    height: 410

    onRejected: {
        if (updateAgent && updateAgent.updateAvailable)
            updateAgent.deferAvailableVersion()
    }

    Timer {
        id: noticeTimer
        interval: 250
        repeat: true
        running: root.pendingNotice
        onTriggered: {
            if (!root.updateAgent || !root.updateAgent.updateAvailable) {
                root.pendingNotice = false
                stop()
            } else if (root.noticeAllowed) {
                root.pendingNotice = false
                updateNotice.open()
                updateNoticeTimeout.restart()
            }
        }
    }

    Popup {
        id: updateNotice
        objectName: "updateNoticeBubble"
        parent: Overlay.overlay
        x: 12
        y: parent ? parent.height - height - 46 : 0
        width: 300
        height: 42
        padding: 8
        modal: false
        focus: false
        closePolicy: Popup.NoAutoClose
        background: Rectangle {
            radius: 4
            color: Theme.chromeBg
            border.color: Theme.linkBlue
            border.width: 1
        }
        contentItem: Text {
            objectName: "updateNoticeText"
            text: root.updateAgent
                ? root.strings.available.arg(root.updateAgent.availableVersion)
                : ""
            color: Theme.ink
            font.pixelSize: Theme.fontSize
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        Timer {
            id: updateNoticeTimeout
            interval: 3500
            onTriggered: updateNotice.close()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        ProgressBar {
            objectName: "updateDialogCheckingProgress"
            Layout.fillWidth: true
            visible: (root.updateAgent && root.updateAgent.checking !== undefined)
                ? root.updateAgent.checking === true : false
            indeterminate: true
        }
        TextArea {
            objectName: "updateDialogReleaseNotes"
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.updateAgent && root.updateAgent.updateAvailable
            readOnly: true
            wrapMode: TextEdit.Wrap
            text: root.updateAgent ? root.updateAgent.releaseNotes : ""
            color: Theme.ink
            TextFieldContextArea {}
        }
        Text {
            objectName: "updateDialogUpdateCommand"
            Layout.fillWidth: true
            visible: root.updateAgent && root.updateAgent.updateAvailable
                && !root.updateAgent.oneClickUpdateSupported
            text: root.updateAgent ? root.updateAgent.updateCommand : ""
            color: Theme.ink
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            textFormat: Text.PlainText
        }
        Text {
            objectName: "updateDialogFeedback"
            Layout.fillWidth: true
            visible: root.feedback.length > 0
            text: root.feedback
            color: Theme.ink
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
        }
        ProgressBar {
            objectName: "updateDialogProgress"
            Layout.fillWidth: true
            visible: root.updateAgent
                && root.updateAgent.downloadState === "downloading"
            value: root.updateAgent
                ? root.updateAgent.downloadProgress / 100 : 0
        }
        Text {
            objectName: "updateDialogReleaseLink"
            Layout.fillWidth: true
            visible: root.updateAgent && root.updateAgent.updateAvailable
                && !root.updateAgent.oneClickUpdateSupported
            text: root.updateAgent ? root.updateAgent.releaseUrl : ""
            color: Theme.linkBlue
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WrapAnywhere
        }
    }

    footer: RowLayout {
        spacing: 8
        PicasaButton {
            objectName: "updateDialogCloseButton"
            visible: !root.updateAgent || !root.updateAgent.updateAvailable
            text: root.strings.close
            onClicked: root.close()
        }
        PicasaButton {
            objectName: "updateDialogOpenReleaseButton"
            visible: root.updateAgent && root.updateAgent.updateAvailable
                && !root.updateAgent.oneClickUpdateSupported
            text: root.strings.openReleases
            onClicked: Qt.openUrlExternally(root.updateAgent.releaseUrl)
        }
        PicasaButton {
            objectName: "updateDialogDownloadButton"
            visible: (root.updateAgent
                && root.updateAgent.oneClickUpdateSupported !== undefined)
                ? root.updateAgent.oneClickUpdateSupported === true
                    && root.updateAgent.downloadState !== undefined
                    && root.updateAgent.downloadState === "idle" : false
            text: root.strings.updateNow
            accent: Theme.picasaGreen
            onClicked: root.updateAgent.downloadUpdate()
        }
        PicasaButton {
            objectName: "updateDialogLaterButton"
            visible: (root.updateAgent && root.updateAgent.updateAvailable !== undefined)
                ? root.updateAgent.updateAvailable === true
                    && root.updateAgent.downloadState !== undefined
                    && root.updateAgent.downloadState !== "ready" : false
            text: root.strings.later
            onClicked: {
                root.updateAgent.deferAvailableVersion()
                root.close()
            }
        }
        PicasaButton {
            objectName: "updateDialogSkipButton"
            visible: (root.updateAgent && root.updateAgent.updateAvailable !== undefined)
                ? root.updateAgent.updateAvailable === true
                    && root.updateAgent.downloadState !== undefined
                    && root.updateAgent.downloadState === "idle" : false
            text: root.strings.skip
            onClicked: {
                root.updateAgent.skipAvailableVersion()
                root.close()
            }
        }
        PicasaButton {
            objectName: "updateDialogRestartButton"
            visible: root.updateAgent && root.updateAgent.downloadState === "ready"
            text: root.strings.restart
            accent: Theme.picasaGreen
            onClicked: {
                if (!root.updateAgent.installWhenExiting(true))
                    root.feedback = root.strings.helperError
                else
                    root.close()
            }
        }
        PicasaButton {
            objectName: "updateDialogInstallOnExitButton"
            visible: root.updateAgent && root.updateAgent.downloadState === "ready"
            text: root.strings.installOnExit
            onClicked: {
                if (!root.updateAgent.installWhenExiting(false))
                    root.feedback = root.strings.helperError
                else
                    root.close()
            }
        }
    }

    Connections {
        target: root.updateAgent
        function onNotificationRequested() {
            root.pendingNotice = true
        }
        function onManualCheckFinished(available, result) {
            if (available) {
                root.feedback = ""
            } else if (result === "up-to-date") {
                root.feedback = root.strings.upToDate
            } else {
                root.feedback = root.strings.couldNotCheck
            }
        }
        function onDownloadFinished(success, result) {
            if (success) {
                root.feedback = ""
            } else if (result === "integrity-error") {
                root.feedback = root.strings.integrityError
            } else {
                root.feedback = root.strings.downloadError
            }
        }
    }
}
