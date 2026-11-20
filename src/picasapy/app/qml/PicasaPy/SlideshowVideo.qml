import QtQuick

// A vetítés videódiáját a néző meglévő lejátszója kezeli.
Item {
    id: video
    required property var slideshow
    property bool _playbackStarted: false
    property int _timerIndex: -1

    function isVideoAt(index) {
        return slideshow.photosModel && index >= 0
            && index < slideshow.count()
            && typeof slideshow.photosModel.isVideoAt === "function"
            && slideshow.photosModel.isVideoAt(index)
    }

    function videoUrl(index) {
        return slideshow.photosModel && index >= 0
            && typeof slideshow.photosModel.fileUrlAt === "function"
            ? slideshow.photosModel.fileUrlAt(index) : ""
    }

    function refresh() {
        if (!slideshow.visible) _playbackStarted = false
        var index = isVideoAt(slideshow.currentIndex)
            ? slideshow.currentIndex : -1
        if (index !== _timerIndex) {
            fallbackTimer.stop()
            _playbackStarted = false
            _timerIndex = index
        }

        var player = playerLoader.item
        if (index >= 0 && player) {
            var trim = { start: -1, end: -1 }
            if (typeof slideshow.photosModel.movieTrimAt === "function")
                trim = slideshow.photosModel.movieTrimAt(index)
            player.forceAutoPlay = true
            player.controlsVisible = false
            player.playbackEnabled = slideshow.playing
            player.trimStartMs = trim.start
            player.trimEndMs = trim.end
            player.source = video.videoUrl(index)
        }

        if (index < 0 || !slideshow.visible || !slideshow.playing
                || _playbackStarted) {
            fallbackTimer.stop()
        } else if (!fallbackTimer.running) {
            fallbackTimer.restart()
        }
    }

    function playbackStarted() {
        if (!isVideoAt(slideshow.currentIndex)) return
        _playbackStarted = true
        fallbackTimer.stop()
    }

    function playbackFailed() {
        if (!isVideoAt(slideshow.currentIndex)) return
        _playbackStarted = false
        if (slideshow.visible && slideshow.playing && !fallbackTimer.running)
            fallbackTimer.restart()
    }

    function playbackFinished() {
        if (!isVideoAt(slideshow.currentIndex)) return
        _playbackStarted = false
        fallbackTimer.stop()
        slideshow.advance()
    }

    Connections {
        target: video.slideshow
        function onCurrentIndexChanged() { video.refresh() }
        function onVisibleChanged() { video.refresh() }
        function onPlayingChanged() { video.refresh() }
        function onPhotosModelChanged() { video.refresh() }
    }

    Loader {
        id: playerLoader
        objectName: "slideshowVideoLoader"
        anchors.fill: parent
        active: video.slideshow.visible
                && video.isVideoAt(video.slideshow.currentIndex)
        source: "VideoPlayerView.qml"
        onLoaded: video.refresh()
    }

    Connections {
        target: playerLoader.item
        ignoreUnknownSignals: true
        function onPlaybackStarted() { video.playbackStarted() }
        function onPlaybackFinished() { video.playbackFinished() }
        function onPlaybackFailed() { video.playbackFailed() }
    }

    Timer {
        id: fallbackTimer
        objectName: "slideshowVideoFallbackTimer"
        interval: video.slideshow.intervalMs
        repeat: false
        onTriggered: {
            if (video.slideshow.visible && video.slideshow.playing
                    && video.isVideoAt(video.slideshow.currentIndex))
                video.slideshow.advance()
        }
    }
}
