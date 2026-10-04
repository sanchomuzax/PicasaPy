import QtQuick
import QtMultimedia

// #4137: a hardverobjektumok külön, lusta komponensben élnek. A panelt
// megnyitni eszköz nélkül is lehet; a kamera/mikrofon csak akkor indul, ha
// az alkalmazás valódi tárolóvezérlőt adott át, és a felhasználó megnyitotta.
Item {
    id: media
    property bool panelVisible: false
    property bool settingsPage: false
    property string captureSize: "640x480"
    property string cameraId: ""
    property string audioId: ""
    property int clipIndex: -1
    property string currentPath: ""

    readonly property var videoDevices: mediaDevices.videoInputs
    readonly property var audioDevices: mediaDevices.audioInputs
    readonly property bool cameraAvailable: videoDevices.length > 0
    readonly property bool cameraActive: camera.active
    readonly property bool recording:
        recorder.recorderState === MediaRecorder.RecordingState
        || recorder.recorderState === MediaRecorder.PausedState
    readonly property bool paused:
        recorder.recorderState === MediaRecorder.PausedState
    readonly property bool clipPlaying:
        player.playbackState === MediaPlayer.PlayingState

    signal snapshotSaved(string path)
    signal clipSaved(string path)
    signal captureFailed(string message)
    signal cameraStatusChanged(string message)

    function deviceWithId(devices, savedId, fallback) {
        if (savedId) {
            for (var i = 0; i < devices.length; ++i) {
                if (String(devices[i].id) === savedId)
                    return devices[i]
            }
        }
        return fallback
    }

    function videoSize() {
        var parts = captureSize.split("x")
        return Qt.size(Number(parts[0]), Number(parts[1]))
    }

    function togglePause() {
        if (paused)
            recorder.record()
        else if (recording)
            recorder.pause()
    }

    function playClip(path) {
        if (path !== undefined && String(path).length > 0)
            player.source = String(path)
        player.play()
    }

    function pauseClip() {
        if (clipPlaying)
            player.pause()
    }

    function stopClipPlayback() {
        player.stop()
    }

    MediaDevices { id: mediaDevices }
    Camera {
        id: camera
        cameraDevice: media.deviceWithId(
            media.videoDevices, media.cameraId, mediaDevices.defaultVideoInput
        )
        active: media.panelVisible && media.cameraAvailable && !media.settingsPage
        onActiveChanged: {
            if (camera.active) {
                media.cameraStatusChanged(qsTr("Preview ready"))
                previewStatusTimer.restart()
            } else if (media.cameraAvailable && media.panelVisible) {
                media.cameraStatusChanged(qsTr("Connecting to camera"))
            }
        }
        onErrorOccurred: function(error, errorString) {
            media.cameraStatusChanged(errorString || qsTr("Connection failed"))
        }
    }
    AudioInput {
        id: microphone
        device: media.deviceWithId(
            media.audioDevices, media.audioId, mediaDevices.defaultAudioInput
        )
    }
    ImageCapture {
        id: imageCapture
        onImageSaved: function(id, path) {
            media.snapshotSaved(String(path))
        }
        onErrorOccurred: function(id, error, errorString) {
            media.captureFailed(errorString || qsTr("Capture failed"))
        }
    }
    MediaRecorder {
        id: recorder
        videoResolution: media.videoSize()
        onRecorderStateChanged: {
            if (recorder.recorderState === MediaRecorder.StoppedState
                    && media.currentPath) {
                media.clipSaved(media.currentPath)
                media.currentPath = ""
            }
        }
        onErrorOccurred: function(error, errorString) {
            media.currentPath = ""
            media.captureFailed(errorString || qsTr("Capture failed"))
        }
    }
    CaptureSession {
        camera: camera
        audioInput: microphone
        imageCapture: imageCapture
        recorder: recorder
        videoOutput: liveVideoOutput
    }
    VideoOutput {
        id: liveVideoOutput
        objectName: "captureMovieLiveVideoOutput"
        anchors.fill: parent
        visible: !media.settingsPage && media.clipIndex < 0
        fillMode: VideoOutput.PreserveAspectFit
    }
    VideoOutput {
        id: playbackVideoOutput
        objectName: "captureMoviePlaybackVideoOutput"
        anchors.fill: parent
        visible: !media.settingsPage && media.clipIndex >= 0
        fillMode: VideoOutput.PreserveAspectFit
    }
    MediaPlayer {
        id: player
        audioOutput: AudioOutput { }
        videoOutput: playbackVideoOutput
    }
    Timer {
        id: previewStatusTimer
        interval: 1400
        onTriggered: media.cameraStatusChanged("")
    }
}
