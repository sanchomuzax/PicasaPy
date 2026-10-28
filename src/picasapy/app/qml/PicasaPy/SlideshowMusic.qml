import QtQuick

// A vetítés zenéjének lusta betöltése és a lejátszási lista léptetése.
Item {
    id: music

    property var slideshow: null

    visible: false

    function sync() {
        if (!slideshow.visible || !slideshow.playing || slideshow.screensaverMode
                || !slideshow.musicEnabled || !slideshow.musicTrackUrls
                || slideshow.musicTrackUrls.length === 0) {
            musicPlayerLoader.active = false
            return
        }
        musicPlayerLoader.active = true
        var player = musicPlayerLoader.item
        if (!player) return
        if (slideshow._musicTrackIndex < 0
                || slideshow._musicTrackIndex >= slideshow.musicTrackUrls.length)
            slideshow._musicTrackIndex = 0
        var target = slideshow.musicTrackUrls[slideshow._musicTrackIndex]
        if (player.source !== target || !player.playing)
            player.playTrack(target)
    }

    function nextTrack() {
        if (!slideshow.musicTrackUrls || slideshow.musicTrackUrls.length === 0) {
            slideshow._syncMusic()
            return
        }
        slideshow._musicTrackIndex = (slideshow._musicTrackIndex + 1)
            % slideshow.musicTrackUrls.length
        slideshow._syncMusic()
    }

    Loader {
        id: musicPlayerLoader
        objectName: "slideshowMusicPlayerLoader"
        active: false
        source: active ? "SlideshowMusicPlayer.qml" : ""
        onLoaded: slideshow._syncMusic()
    }
    Connections {
        target: musicPlayerLoader.item
        function onTrackEnded() { slideshow._nextMusicTrack() }
    }
}
