import QtQuick

Item {
    id: root
    required property var movieDialog
    required property var tabs
    visible: false
    width: 0
    height: 0

    property alias transitionFallbackTimer: moviePreviewTransitionFallbackTimer
    property alias itemsRefreshTimer: movieItemsRefreshTimer
    property alias resizeTimer: moviePreviewResizeTimer
    property alias frameTimer: moviePreviewFrameTimer
    property alias previewTimer: moviePreviewTimer
    property alias musicLoader: moviePreviewMusicLoader
    property alias transition: moviePreviewTransition

    Connections {
        target: moviePreviewTransition
        function onRunningChanged() {
            if (root.movieDialog.previewResettingTransition) return
            if (moviePreviewTransition.running) return
            moviePreviewFrameTimer.stop()
            root.movieDialog.requestPreviewFrame()
        }
    }

    Timer {
        id: moviePreviewTransitionFallbackTimer
        objectName: "moviePreviewTransitionFallbackTimer"
        interval: 100
        repeat: false
        onTriggered: {
            if (!root.movieDialog.previewAwaitingTransitionFrame) return
            root.movieDialog.previewAwaitingTransitionFrame = false
            moviePreviewTransition.restart()
        }
    }

    Timer {
        id: movieItemsRefreshTimer
        objectName: "movieItemsRefreshTimer"
        interval: 120
        repeat: false
        onTriggered: {
            root.movieDialog.requestPreviewFrame()
            root.movieDialog.prefetchNextPreviewFrame()
        }
    }

    Timer {
        id: moviePreviewResizeTimer
        objectName: "moviePreviewResizeTimer"
        interval: 120
        repeat: false
        onTriggered: root.movieDialog.requestPreviewFrame()
    }

    Timer {
        id: moviePreviewFrameTimer
        objectName: "moviePreviewFrameTimer"
        interval: Math.max(
            1,
            Math.round(1000 / (Number(root.movieDialog.previewFramesPerSecond) || 24)))
        repeat: true
        running: moviePreviewTransition.running
            && !moviePreviewTransition.paused
            && !root.movieDialog.previewAwaitingTransitionFrame
        onTriggered: root.movieDialog.requestPreviewFrame()
    }

    Timer {
        id: moviePreviewTimer
        objectName: "moviePreviewTimer"
        interval: Math.max(
            500,
            (root.tabs.movieSeconds && root.tabs.movieSeconds.value !== undefined
                ? root.tabs.movieSeconds.value : 40) * 100)
        repeat: true
        onRunningChanged: {
            if (!moviePreviewMusicLoader.item) return
            if (running) moviePreviewMusicLoader.item.play()
            else moviePreviewMusicLoader.item.pause()
        }
        onTriggered: root.movieDialog.advancePreview()
    }

    Loader {
        id: moviePreviewMusicLoader
        objectName: "moviePreviewMusicLoader"
        active: root.movieDialog.visible && moviePreviewTimer.running
            && root.movieDialog.audioFile.length > 0
        source: active ? "MoviePreviewMusicPlayer.qml" : ""
        property string audioSource: root.movieDialog.audioFile
        property real outputVolume: root.movieDialog.previewAudioVolume
        property bool loopMusic: root.movieDialog.audioOption === 2
        onLoaded: {
            item.source = audioSource
            item.volume = outputVolume
            item.loop = loopMusic
            if (moviePreviewTimer.running) item.play()
        }
        onAudioSourceChanged: {
            if (!item) return
            item.source = audioSource
            if (audioSource && moviePreviewTimer.running) item.play()
            else if (!audioSource) item.stop()
        }
        onOutputVolumeChanged: if (item) item.volume = outputVolume
        onLoopMusicChanged: if (item) item.loop = loopMusic
    }

    NumberAnimation {
        id: moviePreviewTransition
        objectName: "moviePreviewTransition"
        target: root.movieDialog
            && root.movieDialog.previewTransitionProgress !== undefined
            ? root.movieDialog : null
        property: "previewTransitionProgress"
        from: 0
        to: 1
        duration: Math.max(
            1,
            (root.tabs.movieOverlapSlider && root.tabs.movieOverlapSlider.value !== undefined
                ? root.tabs.movieOverlapSlider.value : 0.5) * 1000)
    }
}
