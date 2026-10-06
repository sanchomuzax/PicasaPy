import QtQuick
import QtMultimedia

// A QtMultimedia csak akkor töltődik be, amikor a vetítés ténylegesen zenét
// játszik; a SlideshowView a szülő Loaderének itemjeként használja.
Item {
    id: root
    objectName: "slideshowMusicPlayer"

    property url source: ""
    readonly property bool playing:
        media.playbackState === MediaPlayer.PlayingState
    signal trackEnded()

    function playTrack(trackUrl) {
        root.source = trackUrl
        media.play()
    }

    MediaPlayer {
        id: media
        objectName: "slideshowMusicMediaPlayer"
        source: root.source
        audioOutput: AudioOutput { }
        onMediaStatusChanged: if (mediaStatus === MediaPlayer.EndOfMedia)
            root.trackEnded()
    }
}
