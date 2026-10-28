import QtQuick

// görgő-elfogó réteg (#77/#89): a wheel-eseményt egy a
    // rács fölött ülő átlátszó réteg kapja el (pointer-
    // handler Flickable-ben nem támogatott), és lapgörgetéssé
    // (wheelStep → contentY) alakítja; kattintás és lasszó
    // átmegy rajta (csak görgőt kezel).
Item {
    required property var feed
    parent: feed
    anchors.fill: parent
    z: 15
    WheelHandler {
            acceptedDevices: PointerDevice.Mouse
                             | PointerDevice.TouchPad
            onWheel: function(event) {
                feed.wheelStep(event.angleDelta.y)
            }
        }
    }
