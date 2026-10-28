import QtQuick

// A vetítés léptető- és képernyővédő-ébresztő időzítői.
Item {
    id: timing

    property var slideshow: null
    property alias advanceTimer: stepTimer
    property alias inputArmTimer: screensaverInputTimer

    Timer {
        id: stepTimer
        objectName: "slideshowTimer"
        interval: slideshow.intervalMs
        repeat: true
        running: slideshow.visible && slideshow.playing
        onTriggered: slideshow.advance()
    }

    Timer {
        id: screensaverInputTimer
        objectName: "screensaverInputArmTimer"
        interval: 250
        onTriggered: if (slideshow.visible && slideshow.screensaverMode)
                         slideshow.screensaverInputArmed = true
    }


}
