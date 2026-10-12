import QtQuick
import QtQuick.Window
import PicasaPy

// A `picasapy --screensaver` önálló vetítőablaka (#4613): a tétlenség-figyelő
// indítja, főablak nélkül. A vetítést a meglévő SlideshowView képernyővédő-
// módja végzi (ugyanaz, mint az Előnézet), így a kilépés is ugyanaz: bármely
// billentyű, egérmozdulat vagy kattintás.
Window {
    id: saverWindow
    objectName: "screensaverWindow"
    visible: true
    visibility: Window.FullScreen
    color: "#000000"
    title: "PicasaPy"

    SlideshowView {
        id: slideshow
        objectName: "slideshowView"
        anchors.fill: parent
        photosModel: saver ? saver.photos : null
        transitionKind: saver ? saver.effect : "dissolve"
        captionMode: saver && saver.showCaptions ? "caption" : "none"
        seconds: saver ? saver.seconds : 3
        loop: true
        musicEnabled: false
        onClosed: if (saver) saver.finish()
    }

    // a mutató ne látsszon a vetítés felett; a HoverHandler nem nyeli el a
    // mozgást, tehát a kilépés továbbra is működik
    HoverHandler {
        cursorShape: Qt.BlankCursor
    }

    Component.onCompleted: {
        slideshow.startScreensaver()
        if (!slideshow.visible && saver)
            saver.finish()
    }
}
