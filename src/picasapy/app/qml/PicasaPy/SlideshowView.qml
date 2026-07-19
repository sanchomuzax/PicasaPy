import QtQuick
import QtQuick.Controls

// Diavetítés (#8) — a Picasa Ctrl+4-es teljes képernyős vetítése.
// Időzített léptetés (videókat kihagyva, körbefordulással), szóköz =
// szünet, Esc = kilépés, nyilak = kézi léptetés, Ctrl+R / Ctrl+Shift+R =
// forgatás vetítés közben. A léptetés-logika a controllertől független
// (csak a photosModel-t használja); a csillag/forgatás műveleteket
// jelekkel kéri — a bekötés a Main.qml dolga.
Rectangle {
    id: show
    color: "#000000"
    visible: false

    property var photosModel: null
    property int currentIndex: -1
    property int intervalMs: 3000
    property bool playing: false
    signal closed()
    signal starToggled(int index)
    signal rotateRequested(int index, int delta)

    function count() {
        return photosModel ? photosModel.rowCount() : 0
    }

    // a következő FOTÓ indexe (a videókat kihagyjuk, #8/#14); -1, ha nincs
    function nextPhotoIndex(fromIndex, step) {
        var n = count()
        if (n === 0) return -1
        var idx = fromIndex
        for (var i = 0; i < n; ++i) {
            idx = ((idx + step) % n + n) % n
            if (!photosModel.isVideoAt(idx)) return idx
        }
        return -1
    }

    // az induló index fotóra igazítása (videón álló kijelölésről indítva
    // a következő fotóra ugrunk)
    function clampToPhoto(index) {
        if (photosModel && index >= 0 && index < count()
                && !photosModel.isVideoAt(index))
            return index
        return nextPhotoIndex(index >= 0 ? index : -1, 1)
    }

    function start(index) {
        var target = clampToPhoto(index)
        if (target < 0) return   // nincs vetíthető fotó
        currentIndex = target
        playing = true
        visible = true
        forceActiveFocus()
    }

    function stop() {
        playing = false
        visible = false
        show.closed()
    }

    function advance() {
        var target = nextPhotoIndex(currentIndex, 1)
        if (target < 0) { stop(); return }
        currentIndex = target
    }

    function goBack() {
        var target = nextPhotoIndex(currentIndex, -1)
        if (target >= 0) currentIndex = target
    }

    function togglePause() { playing = !playing }
    function starCurrent() { show.starToggled(currentIndex) }
    function rotateCurrent(delta) { show.rotateRequested(currentIndex, delta) }

    Timer {
        id: stepTimer
        objectName: "slideshowTimer"
        interval: show.intervalMs
        repeat: true
        running: show.visible && show.playing
        onTriggered: show.advance()
    }

    Keys.onEscapePressed: show.stop()
    Keys.onSpacePressed: show.togglePause()
    Keys.onRightPressed: show.advance()
    Keys.onReturnPressed: show.advance()
    Keys.onLeftPressed: show.goBack()
    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_R
                && (event.modifiers & Qt.ControlModifier)) {
            show.rotateCurrent(
                (event.modifiers & Qt.ShiftModifier) ? -1 : 1)
            event.accepted = true
        }
    }

    Image {
        id: slide
        objectName: "slideshowImage"
        // az ini-forgatást a nézővel azonos módon követi (revision-kötés)
        readonly property int iniSteps: show.photosModel
            ? (show.photosModel.revision,
               show.photosModel.rotateAt(show.currentIndex))
            : 0
        anchors.centerIn: parent
        width: iniSteps % 2 ? parent.height : parent.width
        height: iniSteps % 2 ? parent.width : parent.height
        rotation: iniSteps * 90
        source: show.visible && show.photosModel && show.currentIndex >= 0
                ? show.photosModel.fileUrlAt(show.currentIndex)
                : ""
        fillMode: Image.PreserveAspectFit
        asynchronous: true
        autoTransform: true
        sourceSize.width: 2560
    }

    // elő-betöltés a következő fotóra (DoD): mire a timer lép, a kép
    // már dekódolva van
    Image {
        visible: false
        source: show.visible && show.photosModel
                ? show.photosModel.fileUrlAt(
                      show.nextPhotoIndex(show.currentIndex, 1))
                : ""
        asynchronous: true
        autoTransform: true
        sourceSize.width: 2560
    }

    // vezérlő-overlay: egérmozgásra jelenik meg, pár másodperc múlva
    // magától eltűnik (Picasa-minta) — a vetítést nem takarja feleslegesen
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        onPositionChanged: {
            controlsBar.shown = true
            hideTimer.restart()
        }
    }
    Timer {
        id: hideTimer
        interval: 2500
        onTriggered: controlsBar.shown = false
    }

    Rectangle {
        id: controlsBar
        objectName: "slideshowControls"
        property bool shown: false
        visible: opacity > 0
        opacity: shown ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 200 } }
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        width: controlsRow.width + 24
        height: 40
        radius: 6
        color: "#2b2b2bd9"

        Row {
            id: controlsRow
            anchors.centerIn: parent
            spacing: 6

            PicasaButton {
                objectName: "slideshowExitButton"
                text: "✕ " + qsTr("Exit")
                onClicked: show.stop()
            }
            PicasaButton {
                text: "◀"; width: 34
                onClicked: show.goBack()
            }
            PicasaButton {
                objectName: "slideshowPlayButton"
                text: show.playing ? "❚❚" : "▶"
                width: 34
                onClicked: show.togglePause()
            }
            PicasaButton {
                text: "▶▶"; width: 38
                onClicked: show.advance()
            }
            PicasaButton {
                text: "↺"; width: 34
                onClicked: show.rotateCurrent(-1)
            }
            PicasaButton {
                text: "↻"; width: 34
                onClicked: show.rotateCurrent(1)
            }
            PicasaButton {
                objectName: "slideshowStarButton"
                width: 34
                onClicked: show.starCurrent()
                contentItem: Text {
                    text: "★"
                    font.pixelSize: 15
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: show.photosModel
                           && (show.photosModel.revision,
                               show.photosModel.starAt(show.currentIndex))
                           ? Theme.starYellow : "#ffffff"
                    style: Text.Outline
                    styleColor: "#9a9a9a"
                }
            }
        }
    }
}
