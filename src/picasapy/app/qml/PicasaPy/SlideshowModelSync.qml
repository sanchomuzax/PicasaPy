import QtQuick

// A vetítés aktuális képének követése a fotómodell szerkezeti változásainál.
Item {
    id: modelSync

    property var slideshow: null
    property var currentImage: null

    visible: false

    Connections {
        target: modelSync.slideshow.photosModel
        function onRowsRemoved(parent, first, last) {
            modelSync.slideshow._sorokTorolve(first, last)
        }
        function onModelReset() { modelSync.slideshow._modellReset() }
    }

    function kovetettUtFrissit() {
        slideshow._currentFilePath = slideshow.photosModel
                && slideshow.currentIndex >= 0
            ? slideshow.photosModel.filePathAt(slideshow.currentIndex) : ""
    }

    function indexCsendben(index) {
        slideshow._resyncing = true
        slideshow.currentIndex = index
        slideshow._resyncing = false
    }

    function uresListaLeall() {
        slideshow._indexCsendben(-1)
        slideshow.stop()
    }

    function sorokTorolve(first, last) {
        if (!slideshow.visible || !slideshow.photosModel) return
        if (slideshow.count() === 0) {
            slideshow._uresListaLeall()
            return
        }
        var i = slideshow.currentIndex
        if (i < 0) return
        if (last < i) {
            slideshow._indexCsendben(i - (last - first + 1))
        } else if (first <= i) {
            // A látott kép törlődött: a következő sor kerül a helyére.
            slideshow._kovetkezoreLep(first)
        } else {
            slideshow._diakBetolt()
        }
    }

    function modellReset() {
        if (!slideshow.visible || !slideshow.photosModel) return
        if (slideshow.count() === 0) {
            slideshow._uresListaLeall()
            return
        }
        if (slideshow._currentFilePath === "") return
        var sor = slideshow.photosModel.rowOfPath(slideshow._currentFilePath)
        if (sor >= 0) {
            if (sor !== slideshow.currentIndex)
                slideshow._indexCsendben(sor)
            else
                slideshow._diakBetolt()
            return
        }
        slideshow._kovetkezoreLep(slideshow.currentIndex)
    }

    function kovetkezoreLep(jelolt) {
        var kezdo = jelolt >= 0 && jelolt < slideshow.count() ? jelolt : 0
        var kovetkezo = slideshow.clampToPhoto(kezdo)
        if (kovetkezo < 0) {
            slideshow._uresListaLeall()
            return
        }
        if (kovetkezo !== slideshow.currentIndex) {
            slideshow.currentIndex = kovetkezo
            return
        }
        // Azonos index alatt más fájl állhatott, ezért itt nincs index-jelzés.
        var kimeno = modelSync.currentImage.source
        slideshow._kovetettUtFrissit()
        if (kimeno !== "") slideshow._atmenetIndit(kimeno)
        slideshow._diakBetolt()
    }
}
