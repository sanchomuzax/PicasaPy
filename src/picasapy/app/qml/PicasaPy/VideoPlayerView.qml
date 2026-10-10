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
    // 1:1 bekapcsolásakor a VideoViewport a dekóder által jelzett
    // képkockaméretet tartja meg; a nézőterületen túli részt levágja.
    property bool actualSizeEnabled: false
    signal exitRequested()

    //: #4570: az `AutoPlayMovies` beállítás — kikapcsolva a videó megnyitáskor
    //: áll, és a lejátszó gombjával indul. Kontroller nélkül (próbákban) a
    //: Picasa alapja érvényes: magától indul.
    readonly property bool autoPlay:
        typeof controller !== "undefined" && controller
        && controller.autoPlayMovies !== undefined
            ? controller.autoPlayMovies : true

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

    //: #1838: KÉPKOCKA mentése (`movieeditpanel/capture_frame`). A komponens
    //: itt sem ír fájlt — a gazda hívja a vezérlő `captureMovieFrame`-jét a
    //: sor indexével és az ÉPP LÁTOTT pozícióval. A gombot a videó-panel
    //: (`VideoEditPanel.qml`) adja, ezért a jelzést a `captureFrame()` váltja ki.
    signal captureFrameRequested(int positionMs)

    function captureFrame() {
        player.captureFrameRequested(media.position)
    }

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
        videoOutput: viewport.videoOutput
        audioOutput: AudioOutput {
            id: audio
            // `video_control_bar2/volumeslider`: a Preferences/movievolume
            // 0..1000-es értéke 0..1-re normálva, az eredeti 500-as alappal.
            volume: typeof controller !== "undefined" && controller
                    && controller.movieVolume !== undefined
                ? controller.movieVolume / 1000 : 0.5
        }
        // a Picasa a megnyitáskor azonnal lejátszotta a videót. Nyíl-
        // függvény kell: a sourceChanged injektált jel-paramétere ("media")
        // különben árnyékolná a MediaPlayer id-ját.
        onSourceChanged: () => player.startIfAutoPlay()
        //: #1838: a hossz csak a betöltés után ismert — a kezdőpontra ekkor
        //: tudunk ugrani (előbb a `position` írása elveszik)
        onDurationChanged: () => player.seekToTrimStart()
        //: a kimeneti pont: ott megállunk, mintha a klip véget érne. A
        //: vágáson TÚLI szakaszt nem játsszuk le — az eredeti sem teszi.
        onPositionChanged: () => {
            if (player.trimEndMs >= 0 && media.position > player.trimEndMs)
                media.pause()
        }
        Component.onCompleted: () => player.startIfAutoPlay()
    }

    //: #4570: a megnyitás utáni indítás — az `AutoPlayMovies` szabályozza.
    //: Kikapcsolva a lejátszó áll marad, és a lejátszás gombra indul.
    function startIfAutoPlay() {
        if (String(media.source).length === 0) return
        if (player.autoPlay) media.play()
        else media.stop()
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

    VideoViewport {
        id: viewport
        objectName: "videoViewport"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: controls.top
        actualSizeEnabled: player.actualSizeEnabled
    }

    VideoExitGestureArea {
        objectName: "videoExitGestureArea"
        anchors.fill: viewport
        singleClickExit:
            typeof controller !== "undefined" && controller
            && controller.singleClickExitEnabled !== undefined
                ? controller.singleClickExitEnabled : false
        onExitRequested: player.exitRequested()
    }

    Text {
        objectName: "videoErrorText"
        visible: media.error !== MediaPlayer.NoError
        anchors.centerIn: viewport
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
        height: 72
        color: "#2b2b2b"

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 8; anchors.rightMargin: 8
            anchors.topMargin: 1; anchors.bottomMargin: 1
            spacing: 0

            VideoTrimSlider {
                Layout.fillWidth: true
                Layout.preferredHeight: 34
                durationMs: media.duration
                startMs: player.trimStartMs
                endMs: player.trimEndMs
                onTrimRequested: function(startMs, endMs) {
                    player.trimRequested(startMs, endMs)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 34
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
                //: #1838: a vágás-kezdő és -befejező vezérlő a sávon. A
                //: visszaállítás, a képkocka és az export a videó-panelen van.
                //: A feliratok a nyomdai vágásjelek: a be- és kimeneti pont
                //: szögletes zárójele.
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
                VideoPlayerControls {
                    objectName: "videoPlayerModeControls"
                    Layout.preferredWidth: implicitWidth
                    Layout.preferredHeight: implicitHeight
                    actualSizeEnabled: player.actualSizeEnabled
                    onActualSizeToggled: function(enabled) {
                        player.actualSizeEnabled = enabled
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
                    onMoved: {
                        audio.volume = value
                        if (typeof controller !== "undefined" && controller
                                && controller.setMovieVolume !== undefined)
                            controller.setMovieVolume(Math.round(value * 1000))
                    }
                }
            }
        }
    }
}
