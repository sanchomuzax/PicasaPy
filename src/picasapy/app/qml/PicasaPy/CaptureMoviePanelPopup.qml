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
    // #6332: a mentési út hamis ImageCapture-rel is gyakorolható kamera nélkül.
    property var imageCaptureOverride: null
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
    readonly property bool snapshotBusy: snapshotCapture.busy

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
        if ((!mediaRuntime && !imageCaptureOverride) || !storage || snapshotBusy)
            return
        var path = outputPath("snapshot")
        if (!path)
            return
        currentCapturePath = path
        snapshotCapture.requestSnapshot(path)
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

    component SnapshotCaptureFlow: QtObject {
        property var imageCapture: panel.imageCaptureOverride
            ? panel.imageCaptureOverride
            : (panel.mediaRuntime
                ? (panel.mediaRuntime.imageCaptureObject
                    || panel.mediaRuntime.imageCapture || null)
                : null)
        property string pendingSnapshotPath: ""
        property string currentSnapshotPath: ""
        readonly property bool busy:
            pendingSnapshotPath.length > 0 || currentSnapshotPath.length > 0

        signal snapshotSaved(string path)
        signal captureFailed(string message)
        signal snapshotFailureDetails(int errorCode, string errorString, string path)

        function requestSnapshot(path) {
            if (!path || busy)
                return
            if (!imageCapture) {
                failSnapshot(-1, "", path, qsTr("Capture failed"))
                return
            }
            // A valódi ImageCapture bool tulajdonságot ad; régebbi
            // médiateszthelyettesítőkben ez még hiányozhat.
            if (imageCapture.readyForCapture !== false) {
                startSnapshot(path)
            } else {
                pendingSnapshotPath = path
                snapshotReadyTimer.restart()
            }
        }

        function tryPendingSnapshot() {
            if (!pendingSnapshotPath || !imageCapture
                    || !imageCapture.readyForCapture)
                return
            var path = pendingSnapshotPath
            pendingSnapshotPath = ""
            snapshotReadyTimer.stop()
            startSnapshot(path)
        }

        function startSnapshot(path) {
            pendingSnapshotPath = ""
            currentSnapshotPath = path
            snapshotReadyTimer.stop()
            var requestId = -1
            try {
                requestId = imageCapture.captureToFile(path)
            } catch (error) {
                var exceptionText = error && error.message
                    ? String(error.message) : String(error)
                failSnapshot(-1, exceptionText, path,
                             exceptionText || qsTr("Capture failed"))
                return
            }
            if (Number(requestId) < 0 && currentSnapshotPath === path) {
                var errorText = String(imageCapture.errorString || "")
                failSnapshot(-1, errorText, path,
                             errorText || qsTr("Capture failed"))
            }
        }

        function failSnapshot(errorCode, errorString, path, message) {
            if (pendingSnapshotPath === path)
                pendingSnapshotPath = ""
            if (currentSnapshotPath === path)
                currentSnapshotPath = ""
            snapshotReadyTimer.stop()
            snapshotFailureDetails(Number(errorCode), String(errorString || ""),
                                   String(path))
            captureFailed(String(message || errorString || qsTr("Capture failed")))
        }

        function failCurrentSnapshot(errorCode, errorString) {
            var path = currentSnapshotPath || pendingSnapshotPath
            if (!path)
                return
            var actualError = String(errorString
                || (imageCapture ? imageCapture.errorString : "") || "")
            failSnapshot(errorCode, actualError, path,
                         actualError || qsTr("Capture failed"))
        }

        function completeSnapshot(path) {
            if (!currentSnapshotPath)
                return
            var savedPath = String(path || currentSnapshotPath)
            currentSnapshotPath = ""
            snapshotSaved(savedPath)
        }

        function expirePendingSnapshot() {
            if (!pendingSnapshotPath)
                return
            if (imageCapture && imageCapture.readyForCapture) {
                tryPendingSnapshot()
                return
            }
            var path = pendingSnapshotPath
            // Az 5 mp-es várakozás lejárt; saját felirat helyett a már
            // lefordított általános hibaszöveg (minden nyelven megvan).
            var message = qsTr("Capture failed")
            failSnapshot(-1, message, path, message)
        }

    }
    SnapshotCaptureFlow {
        id: snapshotCapture
        objectName: "snapshotCaptureRequest"
    }
    Timer {
        id: snapshotReadyTimer
        objectName: "snapshotReadyTimer"
        interval: 5000
        repeat: false
        onTriggered: snapshotCapture.expirePendingSnapshot()
    }
    Connections {
        target: snapshotCapture.imageCapture
        ignoreUnknownSignals: true
        function onReadyForCaptureChanged() {
            snapshotCapture.tryPendingSnapshot()
        }
        function onImageSaved(id, path) {
            snapshotCapture.completeSnapshot(String(path))
        }
        function onErrorOccurred(id, error, errorString) {
            snapshotCapture.failCurrentSnapshot(Number(error), String(errorString || ""))
        }
    }
    Connections {
        target: snapshotCapture
        function onSnapshotSaved(path) {
            panel.currentCapturePath = ""
            panel.statusMessage = qsTr("Snapshot saved")
            // A nem figyelt kamera-mappát is egyszeri beolvasással vesszük
            // fel; figyelt mappánál a meglévő watcher végzi a frissítést.
            if (panel.storage && typeof controller !== "undefined" && controller)
                controller.scanFolderOnce(panel.storage.captureFolder)
        }
        function onCaptureFailed(message) {
            panel.currentCapturePath = ""
            panel.statusMessage = message
        }
        function onSnapshotFailureDetails(errorCode, errorString, path) {
            if (panel.storage)
                panel.storage.logSnapshotFailure(errorCode, errorString, path)
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
                snapshotCapture.completeSnapshot(String(path))
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
                            && panel.imageCaptureOverride === null
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
                                onCurrentIndexChanged: panel.pendingSize = panel.meretek[currentIndex]
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
                             && panel.storage !== null && !panel.snapshotBusy
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
