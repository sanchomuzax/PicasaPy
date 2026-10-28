import QtQuick

// Mappán belüli léptetés és görgős lapozás.
QtObject {
    id: navigation
    property var hostViewer: null
    readonly property var viewer: hostViewer
    readonly property var photosModel: viewer.photosModel
    readonly property var editorPanel: viewer.editorPanel
    property var hostAutoAdvanceTimer: null

    function stopCtrlF9AutoAdvance() {
        hostAutoAdvanceTimer.stop()
    }
    function startCtrlF9AutoAdvance() {
        if (!viewer.visible || !viewer.photosModel || !viewer.hasNext())
            return
        if (!hostAutoAdvanceTimer.running)
            hostAutoAdvanceTimer.start()
    }

// A lapozás a #84 óta a modell mappán-belüli lépését használja: a
// rács (feed) nézet mappaátlépő listáin (csillag-szűrő, keresés) sem
// ugorhatunk át a szomszéd mappába - a folderNeighbor a saját mappa
// határán a jelenlegi indexet adja vissza, tehát nem lép tovább. #4525:
// kettős nézetben a „Kijelölve” oldalt léptetjük, a másik sort hagyjuk.
function next() {
    if (!viewer.ctrlF9AutoStep)
        viewer.stopCtrlF9AutoAdvance()
    if (!photosModel) return
    var sor = viewer._kijeloltSort()
    if (sor < 0) return
    var cel = photosModel.folderNeighbor(sor, 1)
    if (viewer.layoutMode === "ab" && viewer.aktivOldal === "jobb")
        viewer.masodikIndex = cel
    else
        viewer.currentIndex = cel
function handleReturnPressed() {
        if (viewer.textEntryHasFocus)
            return
        // #4500: a kikapcsolt SingleClickExit az állóképes előnézetben
        // Enterrel lép vissza a könyvtárba. Az aktív eszközök saját Enter-
        // útját (pl. sorozat-vágás), a videót és a kettős nézetet meghagyjuk.
        if (!viewer.singleClickExitEnabled
                && !viewer.isCurrentVideo
                && viewer.layoutMode === "1up"
                && !editorPanel.modeToolActive
                && !editorPanel.tiltActive
                && !editorPanel.paramPanelActive
                && !viewer.facesEditMode) {
            viewer.kerBezaras()
            return
        }
        viewer.next()
    }

}
function previous() {
    viewer.stopCtrlF9AutoAdvance()
    if (!photosModel) return
    var sor = viewer._kijeloltSort()
    if (sor < 0) return
    var cel = photosModel.folderNeighbor(sor, -1)
    if (viewer.layoutMode === "ab" && viewer.aktivOldal === "jobb")
        viewer.masodikIndex = cel
    else
        viewer.currentIndex = cel
}
// a ◀/▶ gombok (és Keys.onLeft/Right) enabled-je is a mappahatárt
// tükrözi: nincs hova lépni, ha a folderNeighbor helyben marad
function _vanSzomszed(sor, irany) {
    if (!photosModel || sor < 0) return false
    return photosModel.folderNeighbor(sor, irany) !== sor
}
function hasNext() {
    return viewer._vanSzomszed(viewer._kijeloltSort(), 1)
}
function hasPrevious() {
    return viewer._vanSzomszed(viewer._kijeloltSort(), -1)
}
// Egérgörgős lapozás (#77): a nagy nézőben a görgő a képek között
// lép (Picasa-viselkedés). A touchpad kis deltáit egy teljes
// görgő-fokozatig (120) gyűjtjük, hogy ne ugráljon több képet.
property real wheelAccum: 0
function wheelStep(delta) {
    wheelAccum += delta
    while (wheelAccum <= -120) { wheelAccum += 120; next() }
    while (wheelAccum >= 120) { wheelAccum -= 120; previous() }
}
function urlAt(index) {
    return photosModel ? photosModel.fileUrlAt(index) : ""
}
// elő-betöltéshez: videót NEM adunk az Image-nek (#14) - a képként
// dekódolás hibát logolna, a videó elő-betöltése nem a mi dolgunk
function preloadUrlAt(index) {
    if (!photosModel || photosModel.isVideoAt(index)) return ""
    return urlAt(index)
}

}
