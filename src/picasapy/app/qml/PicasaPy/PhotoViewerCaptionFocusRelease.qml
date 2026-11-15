import QtQuick

// #7027: passzív kattintás-figyelő a teljes néző fölött. A gyerekek (gombok,
// egérterületek) kattintását nem veszi el, csak jelzi, hogy a képaláírás-mezőn
// KÍVÜL történt kattintás (`0x0067ed05-0x0067ed5b`). A mező ettől elveszti a
// fókuszát, és elmenti a begépelt szöveget (`0x005f89a0`).
//
// A kezelő nem gomb: nincs látható felülete, tehát lenyomott képe sem lehet
// (a #6381 gombleltár ezért kivételként tartja nyilván).
TapHandler {
    objectName: "captionFocusReleaseHandler"
    property var hostOverlayControls: null

    gesturePolicy: TapHandler.DragThreshold
    onPressedChanged: {
        if (pressed && hostOverlayControls)
            hostOverlayControls.releaseCaptionFocus(point.scenePosition)
    }
}
