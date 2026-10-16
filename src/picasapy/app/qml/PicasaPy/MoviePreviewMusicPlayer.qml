import QtQuick
import QtMultimedia

// A hangsáv lejátszója csak aktív filmelőnézet közben töltődik be.
Item {
    id: root
    objectName: "moviePreviewMusicPlayer"

    property url source: ""
    property real volume: 0.5
    property bool loop: false
    readonly property bool playing:
        media.playbackState === MediaPlayer.PlayingState

    function play() {
        if (String(source).length > 0) media.play()
    }

    function pause() {
        if (media.playbackState === MediaPlayer.PlayingState) media.pause()
    }

    function stop() {
        media.stop()
    }

    MediaPlayer {
        id: media
        objectName: "moviePreviewMediaPlayer"
        source: root.source
        loops: root.loop ? MediaPlayer.Infinite : 1
        audioOutput: AudioOutput {
            objectName: "moviePreviewAudioOutput"
            volume: root.volume
        }
    }
}
