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

    //: #1838: a Picasából örökölt VÁGÁSPONTOK ezredmásodpercben. A **−1
    //: jelenti, hogy azon az oldalon nincs vágás** — nem 0 és nem a hossz.
    //: Az eredeti a `video_control_bar/setin`/`setout` gombokkal állítja
    //: őket, és a `filters=` lánc `moviestart`/`movieend` tokenjében tárolja
    //: (100 ns-os egységben, ld. `ini/movie_trim.py`).
    //:
    //: ⚠️ A vágás nálunk ma CSAK a lejátszásra hat: a fájlt nem alakítjuk át,
    //: és a pontokat a felületen még nem lehet ÁLLÍTANI — az a #1838 további
    //: része. Ami már most számít: egy Picasából örökölt klip a megfelelő
    //: helyen indul és ott áll meg, nem a nyers fájl elején-végén.
    property int trimStartMs: -1
    property int trimEndMs: -1

    readonly property bool trimmed: trimStartMs >= 0 || trimEndMs >= 0
    //: a lejátszható szakasz — a vágás nélküli oldalon a fájl határa
    readonly property int playFromMs: Math.max(0, trimStartMs)
    readonly property int playToMs: trimEndMs >= 0
        ? trimEndMs : Math.max(1, media.duration)

    //: a vágás kezdetére ugrás — a betöltés UTÁN, mert a `position` írása
    //: üres médián elveszik
    function seekToTrimStart() {
        if (player.trimStartMs > 0 && media.duration > 0)
            media.position = Math.min(player.trimStartMs, media.duration)
    }

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
        //: #1838: a hossz csak a betöltés után ismert — a kezdőpontra ekkor
        //: tudunk ugrani (előbb a `position` írása elveszik)
        onDurationChanged: () => player.seekToTrimStart()
        //: a kimeneti pont: ott megállunk, mintha a klip véget érne. A
        //: vágáson TÚLI szakaszt nem játsszuk le — az eredeti sem teszi.
        onPositionChanged: () => {
            if (player.trimEndMs >= 0 && media.position > player.trimEndMs)
                media.pause()
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
            PicasaSlider {
                id: seek
                objectName: "videoSeekSlider"
                Layout.fillWidth: true
                //: #1838: a csúszka a VÁGOTT szakaszra szorítva — a vágáson
                //: kívüli részre a felhasználó se tudjon odatekerni (vágás
                //: nélkül a szakasz a fájl eleje…vége, tehát a viselkedés a
                //: #1838 előtti)
                from: player.playFromMs
                to: Math.max(player.playFromMs + 1, player.playToMs)
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
            PicasaSlider {
                objectName: "videoVolumeSlider"
                Layout.preferredWidth: 70
                from: 0; to: 1
                value: audio.volume
                onMoved: audio.volume = value
            }
        }
    }
}
