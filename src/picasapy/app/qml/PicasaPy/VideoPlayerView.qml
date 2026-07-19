import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia

// Videó-lejátszás a nézőben (#14): play/pause, pozíciócsúszka, idő-kijelzés
// és hangerő. A komponenst a PhotoViewer Loader-e CSAK videónál tölti be —
// ha a Qt Multimedia modul hiányzik, a Loader hibára fut, és a néző
// tartalék-szövege jelenik meg (a fotó-nézet érintetlen marad).
Item {
    id: player
    property url source: ""

    // Bezárásnál/navigálásnál a Loader elereszti a komponenst, a lejátszás
    // vele áll le — külön stop-kezelés nem kell.
    MediaPlayer {
        id: media
        objectName: "viewerMediaPlayer"
        source: player.source
        videoOutput: output
        audioOutput: AudioOutput { id: audio }
        // a Picasa a megnyitáskor azonnal lejátszotta a videót. Nyíl-
        // függvény kell: a sourceChanged injektált jel-paramétere ("media")
        // különben árnyékolná a MediaPlayer id-ját.
        onSourceChanged: () => {
            if (String(media.source).length > 0) media.play()
        }
        Component.onCompleted: () => {
            if (String(media.source).length > 0) media.play()
        }
    }

    function togglePlayback() {
        if (media.playbackState === MediaPlayer.PlayingState) media.pause()
        else media.play()
    }

    function formatTime(ms) {
        var total = Math.max(0, Math.round(ms / 1000))
        var minutes = Math.floor(total / 60)
        var seconds = total % 60
        return minutes + ":" + (seconds < 10 ? "0" + seconds : seconds)
    }

    VideoOutput {
        id: output
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: controls.top
        fillMode: VideoOutput.PreserveAspectFit
    }

    Text {
        objectName: "videoErrorText"
        visible: media.error !== MediaPlayer.NoError
        anchors.centerIn: output
        text: qsTr("Unable to play this video.")
        color: "#e8e8e8"
        font.pixelSize: Theme.fontSize
    }

    // vezérlősáv: sötét sáv a kép alatt (a szürke néző-háttéren olvasható)
    Rectangle {
        id: controls
        objectName: "videoControls"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 34
        color: "#2b2b2b"

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 8; anchors.rightMargin: 8
            spacing: 8

            PicasaButton {
                objectName: "videoPlayButton"
                Layout.preferredWidth: 34
                text: media.playbackState === MediaPlayer.PlayingState
                      ? "❚❚" : "▶"
                onClicked: player.togglePlayback()
            }
            Slider {
                id: seek
                objectName: "videoSeekSlider"
                Layout.fillWidth: true
                from: 0
                to: Math.max(1, media.duration)
                onMoved: media.position = value
                // húzás közben a kéz vezet; egyébként a lejátszás-pozíció
                Binding on value {
                    when: !seek.pressed
                    value: media.position
                }
            }
            Text {
                objectName: "videoTimeLabel"
                color: "#e8e8e8"
                font.pixelSize: Theme.fontSize
                text: player.formatTime(media.position) + " / "
                      + player.formatTime(media.duration)
            }
            Text {
                text: "🔊"
                color: "#e8e8e8"
                font.pixelSize: Theme.fontSize
            }
            Slider {
                objectName: "videoVolumeSlider"
                Layout.preferredWidth: 70
                from: 0; to: 1
                value: audio.volume
                onMoved: audio.volume = value
            }
        }
    }
}
