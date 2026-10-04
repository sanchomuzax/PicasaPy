import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import PicasaPy

// #4137: a `capturemoviepanelpopup` panel. Qt Multimedia kezeli a kamerát,
// a külön mikrofonbemenetet, a képkockát és az MP4-rögzítést.
Popup {
    id: panel
    objectName: "captureMoviePanelPopup"
    property var storage: null
    property string fallbackCaptureSize: "640x480"
    readonly property string selectedSize:
        storage ? storage.captureSize : fallbackCaptureSize
    readonly property string savedCameraId: storage ? storage.cameraId : ""
    readonly property string savedAudioId: storage ? storage.audioId : ""
    property bool settingsPage: false
    property string statusMessage: ""
    property string currentCapturePath: ""
    property var clips: []
    property int clipIndex: -1

    readonly property var mediaRuntime: mediaRuntimeLoader.item
    readonly property var videoDevices:
        mediaRuntime ? mediaRuntime.videoDevices : []
    readonly property var audioDevices:
        mediaRuntime ? mediaRuntime.audioDevices : []
    readonly property bool cameraAvailable:
        mediaRuntime ? mediaRuntime.cameraAvailable : false
    readonly property bool cameraActive:
        mediaRuntime ? mediaRuntime.cameraActive : false
    readonly property bool recording:
        mediaRuntime ? mediaRuntime.recording : false
    readonly property bool clipPlaying:
        mediaRuntime ? mediaRuntime.clipPlaying : false

    function deviceIndex(devices, savedId) {
        if (savedId) {
            for (var i = 0; i < devices.length; ++i) {
                if (String(devices[i].id) === savedId)
                    return i
            }
        }
        return devices.length ? 0 : -1
    }

    function showSettings() {
        if (mediaRuntime)
            mediaRuntime.stopClipPlayback()
        pendingSize = selectedSize
        pendingVideoIndex = deviceIndex(videoDevices, savedCameraId)
        pendingAudioIndex = deviceIndex(audioDevices, savedAudioId)
        settingsPage = true
    }

    function applySettings() {
        if (storage) {
            storage.setCaptureSize(pendingSize)
            if (pendingVideoIndex >= 0)
                storage.setCameraId(String(videoDevices[pendingVideoIndex].id))
            if (pendingAudioIndex >= 0)
                storage.setAudioId(String(audioDevices[pendingAudioIndex].id))
        } else {
            fallbackCaptureSize = pendingSize
        }
        settingsPage = false
    }

    function cancelSettings() {
        pendingSize = selectedSize
        settingsPage = false
    }

    function setClip(index) {
        if (index < 0 || index >= clips.length)
            return
        clipIndex = index
        if (!mediaRuntime)
            return
        mediaRuntime.playClip(clips[index])
    }

    function addClip(path) {
        if (!path)
            return
        var next = clips.slice(0)
        next.push(path)
        clips = next
        clipIndex = next.length - 1
        setClip(clipIndex)
    }

    function outputPath(kind) {
        if (!storage)
            return ""
        try {
            return storage.reserveCapturePath(kind)
        } catch (error) {
            statusMessage = qsTr("Unable to prepare the capture folder.")
            return ""
        }
    }

    function startOrStopRecording() {
        if (!mediaRuntime)
            return
        if (recording) {
            mediaRuntime.recorder.stop()
            return
        }
        var path = outputPath("video")
        if (!path)
            return
        currentCapturePath = path
        mediaRuntime.currentPath = path
        mediaRuntime.recorder.outputLocation = path
        mediaRuntime.recorder.record()
    }

    function takeSnapshot() {
        if (!mediaRuntime)
            return
        var path = outputPath("snapshot")
        if (!path)
            return
        currentCapturePath = path
        mediaRuntime.imageCapture.captureToFile(path)
    }

    property string pendingSize: selectedSize
    property int pendingVideoIndex: -1
    property int pendingAudioIndex: -1
    readonly property var meretek: ["320x240", "640x480", "800x600", "1280x720"]

    width: Math.min(760, parent ? parent.width - 32 : 728)
    height: Math.min(520, parent ? parent.height - 32 : 488)
    padding: 0
    modal: true
    focus: true
    dim: true
    closePolicy: Popup.CloseOnEscape
    parent: Overlay.overlay
    anchors.centerIn: parent

    onOpened: {
        settingsPage = false
        statusMessage = ""
        if (mediaRuntime)
            mediaRuntime.stopClipPlayback()
        clipIndex = -1
    }
    onClosed: {
        if (mediaRuntime) {
            if (recording)
                mediaRuntime.recorder.stop()
            mediaRuntime.stopClipPlayback()
        }
    }

    Component {
        id: mediaRuntimeComponent
        CaptureMovieMedia {
            anchors.fill: parent
            panelVisible: panel.visible
            settingsPage: panel.settingsPage
            captureSize: panel.selectedSize
            cameraId: panel.savedCameraId
            audioId: panel.savedAudioId
            clipIndex: panel.clipIndex
            onCameraStatusChanged: function(message) {
                panel.statusMessage = message
            }
            onSnapshotSaved: function(path) {
                panel.currentCapturePath = ""
                panel.statusMessage = qsTr("Snapshot saved")
            }
            onClipSaved: function(path) {
                panel.currentCapturePath = ""
                panel.addClip(path)
            }
            onCaptureFailed: function(message) {
                panel.currentCapturePath = ""
                panel.statusMessage = message
            }
        }
    }
    Connections {
        target: panel.storage
        function onCapturePathFailed(message) {
            panel.statusMessage = message
        }
    }

    background: Rectangle {
        objectName: "captureMoviePanelSurface"
        color: Theme.panelBg
        border.color: Theme.chromeBorder
        border.width: 1
        radius: 3
    }

    contentItem: Item {
        anchors.fill: parent

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 18
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Text {
                    objectName: "captureMoviePanelTitle"
                    text: qsTr("Recording")
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize + 2
                    font.bold: true
                }
                Text {
                    objectName: "capturemoviepanelpopup/video_label"
                    text: qsTr("Video")
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize
                }
                Item { Layout.fillWidth: true }
                Button {
                    objectName: "capturemoviepanelpopup/live_video"
                    text: qsTr("Camera")
                    ToolTip.text: qsTr("Capture live video from camera")
                    ToolTip.delay: Theme.tooltipDelay
                    ToolTip.visible: hovered
                    onClicked: {
                        if (panel.mediaRuntime)
                            panel.mediaRuntime.stopClipPlayback()
                        panel.settingsPage = false
                        panel.clipIndex = -1
                    }
                }
                Button {
                    objectName: "capturemoviepanelpopup/camchange"
                    text: qsTr("Settings")
                    ToolTip.text: qsTr("Change camera settings")
                    ToolTip.delay: Theme.tooltipDelay
                    ToolTip.visible: hovered
                    onClicked: panel.showSettings()
                }
            }

            Item {
                id: mediaArea
                objectName: "capturemoviepanelpopup/movieparent"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 230
                Rectangle {
                    anchors.fill: parent
                    color: Theme.canvasBg
                    border.color: Theme.chromeBorder
                    border.width: 1
                    radius: 2
                }
                Loader {
                    id: mediaRuntimeLoader
                    objectName: "captureMovieMediaLoader"
                    anchors.fill: parent
                    active: panel.visible && panel.storage !== null
                    sourceComponent: mediaRuntimeComponent
                    onLoaded: {
                        if (panel.storage)
                            panel.clips = panel.storage.capturedVideos()
                    }
                }
                Text {
                    objectName: "captureMovieAvailabilityText"
                    anchors.centerIn: parent
                    visible: !panel.settingsPage
                             && (!panel.cameraAvailable || panel.statusMessage.length > 0)
                    text: !panel.cameraAvailable
                          ? qsTr("Not available")
                          : (panel.statusMessage || qsTr("Connecting to camera"))
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize
                }
                Rectangle {
                    id: settingsPanel
                    objectName: "capturemoviepanelpopup/settingspanel"
                    anchors.fill: parent
                    visible: panel.settingsPage
                    color: Theme.panelBg
                    ColumnLayout {
                        anchors.centerIn: parent
                        width: Math.min(parent.width - 48, 460)
                        spacing: 14

                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: qsTr("Camera")
                                color: Theme.ink
                                Layout.preferredWidth: 90
                            }
                            ComboBox {
                                id: cameraCombo
                                objectName: "capturemoviepanelpopup/videosrc"
                                Layout.fillWidth: true
                                model: panel.videoDevices
                                textRole: "description"
                                currentIndex: panel.pendingVideoIndex
                                onCurrentIndexChanged: panel.pendingVideoIndex = currentIndex
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                objectName: "capturemoviepanelpopup/audio_label"
                                text: qsTr("Audio")
                                color: Theme.ink
                                Layout.preferredWidth: 90
                            }
                            ComboBox {
                                id: audioCombo
                                objectName: "capturemoviepanelpopup/audiosrc"
                                Layout.fillWidth: true
                                model: panel.audioDevices
                                textRole: "description"
                                currentIndex: panel.pendingAudioIndex
                                onCurrentIndexChanged: panel.pendingAudioIndex = currentIndex
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                objectName: "capturemoviepanelpopup/size_label"
                                text: qsTr("Size")
                                color: Theme.ink
                                Layout.preferredWidth: 90
                            }
                            ComboBox {
                                id: sizeCombo
                                objectName: "capturemoviepanelpopup/outputsize"
                                Layout.fillWidth: true
                                model: panel.meretek
                                currentIndex: Math.max(0, panel.meretek.indexOf(panel.pendingSize))
                                onCurrentIndexChanged: panel.pendingSize = currentText
                            }
                        }
                    }
                }
            }

            RowLayout {
                objectName: "capturemoviepanelpopup/filmstrip"
                Layout.fillWidth: true
                spacing: 8
                Button {
                    objectName: "capturemoviepanelpopup/prev"
                    text: "‹"
                    enabled: panel.clipIndex > 0
                    onClicked: panel.setClip(panel.clipIndex - 1)
                }
                Button {
                    objectName: "capturemoviepanelpopup/next"
                    text: "›"
                    enabled: panel.clips.length > 0
                             && panel.clipIndex < panel.clips.length - 1
                    onClicked: panel.setClip(panel.clipIndex < 0 ? 0 : panel.clipIndex + 1)
                }
                Button {
                    objectName: "capturevbar/moviecontrols/play"
                    text: "▶"
                    visible: panel.clipIndex >= 0 && panel.mediaRuntime
                             && !panel.clipPlaying
                    ToolTip.text: qsTr("Play")
                    ToolTip.delay: Theme.tooltipDelay
                    ToolTip.visible: hovered
                    onClicked: if (panel.mediaRuntime) panel.mediaRuntime.playClip()
                }
                Button {
                    objectName: "capturevbar/moviecontrols/pause"
                    text: "Ⅱ"
                    visible: panel.clipIndex >= 0 && panel.mediaRuntime
                             && panel.clipPlaying
                    ToolTip.text: qsTr("Pause")
                    ToolTip.delay: Theme.tooltipDelay
                    ToolTip.visible: hovered
                    onClicked: if (panel.mediaRuntime) panel.mediaRuntime.pauseClip()
                }
                Item { Layout.fillWidth: true }
                Button {
                    objectName: "capturemoviepanelpopup/snapshot"
                    text: qsTr("Snapshot")
                    enabled: panel.cameraAvailable && panel.cameraActive
                             && panel.storage !== null
                    onClicked: panel.takeSnapshot()
                }
                Button {
                    objectName: "capturemoviepanelpopup/capture"
                    text: panel.recording ? qsTr("Stop") : qsTr("Record")
                    ToolTip.text: panel.recording
                                 ? qsTr("Stop camera recording")
                                 : qsTr("Start camera recording")
                    ToolTip.delay: Theme.tooltipDelay
                    ToolTip.visible: hovered
                    enabled: panel.cameraAvailable && panel.cameraActive
                             && panel.storage !== null
                    onClicked: panel.startOrStopRecording()
                }
                Button {
                    objectName: "capturemoviepanelpopup/record_pause"
                    text: panel.mediaRuntime && panel.mediaRuntime.paused
                          ? qsTr("Resume") : qsTr("Pause")
                    visible: panel.recording
                    onClicked: if (panel.mediaRuntime) panel.mediaRuntime.togglePause()
                }
                Button {
                    objectName: "capturemoviepanelpopup/settings_cancel"
                    text: qsTr("Cancel")
                    visible: panel.settingsPage
                    onClicked: panel.cancelSettings()
                }
                Button {
                    objectName: "capturemoviepanelpopup/settings_apply"
                    text: qsTr("Apply")
                    visible: panel.settingsPage
                    onClicked: panel.applySettings()
                }
                Button {
                    objectName: "capturemoviepanelpopup/done"
                    text: qsTr("Done")
                    onClicked: panel.close()
                }
            }
        }
    }
}
