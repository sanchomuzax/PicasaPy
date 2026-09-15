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
    //: ⚠️ A vágás nálunk CSAK a lejátszásra hat: a fájlt nem alakítjuk át.
    //: A pontok viszont ÁLLÍTHATÓK (`setin`/`setout`/`reset_trim`), és a
    //: `.picasa.ini` `filters=` láncába mennek vissza.
    property int trimStartMs: -1
    property int trimEndMs: -1

    //: #1838: a vágás MENTÉSE. A komponens nem ír inifájlt — jelez, és a
    //: gazda (`PhotoViewer`) hívja a vezérlő `setMovieTrim`/`resetMovieTrim`
    //: slotját a sor indexével. A `-1` itt is „nincs vágás azon az oldalon".
    //:
    //: ⚠️ A helyi `trimStartMs`/`trimEndMs` SZÁNDÉKOSAN nem íródik át itt: a
    //: két érték a modellből kötve jön, és csak SIKERES ini-írás után
    //: frissül. Ha itt optimistán átírnánk, a felület egy írásvédett mappán
    //: is mentettnek mutatná a vágást (#2497 tanulsága).
    signal trimRequested(int startMs, int endMs)
    signal trimResetRequested()

    //: #1838: KÉPKOCKA mentése (`movieeditpanel/capture_frame`). A komponens
    //: itt sem ír fájlt — a gazda hívja a vezérlő `captureMovieFrame`-jét a
    //: sor indexével és az ÉPP LÁTOTT pozícióval.
    signal captureFrameRequested(int positionMs)

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
            //: #1838: a három vágás-vezérlő, az eredeti sorrendjében
            //: (`setin` · `setout` · `reset_trim`). A feliratok a nyomdai
            //: vágásjelek: a be- és kimeneti pont szögletes zárójele.
            PicasaButton {
                objectName: "videoSetInButton"
                Layout.preferredWidth: 30
                text: "["
                ToolTip.text: qsTr("Create a new starting point")
                ToolTip.delay: Theme.tooltipDelay
                ToolTip.visible: hovered
                onClicked: player.trimRequested(media.position, player.trimEndMs)
            }
            PicasaButton {
                objectName: "videoSetOutButton"
                Layout.preferredWidth: 30
                text: "]"
                ToolTip.text: qsTr("Create a new ending point")
                ToolTip.delay: Theme.tooltipDelay
                ToolTip.visible: hovered
                onClicked: player.trimRequested(player.trimStartMs, media.position)
            }
            PicasaButton {
                objectName: "videoResetTrimButton"
                Layout.preferredWidth: 30
                text: "⟲"
                //: vágás nélkül nincs mit visszaállítani — a gomb szürke
                enabled: player.trimmed
                //: `Tooltip(movieeditpanel/reset_trim)` — az eredeti szövege
                ToolTip.text: qsTr("Restore movie to its original length (remove start and end points)")
                ToolTip.delay: Theme.tooltipDelay
                ToolTip.visible: hovered
                onClicked: player.trimResetRequested()
            }
            //: #1838: `movieeditpanel/capture_frame` — „Take Snapshot".
            //: A jel a fényképezőgép; a felirat a buboréksúgóban van, mert a
            //: sávon csak 30 képpont széles gombok férnek el.
            PicasaButton {
                objectName: "videoCaptureFrameButton"
                Layout.preferredWidth: 30
                text: "⃞"
                //: `Tooltip(movieeditpanel/capture_frame)`
                ToolTip.text: qsTr("Capture current frame")
                ToolTip.delay: Theme.tooltipDelay
                ToolTip.visible: hovered
                onClicked: player.captureFrameRequested(media.position)
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
