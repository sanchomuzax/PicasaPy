import QtQuick

// A fotóméret, betöltés, vágás és nagyítás számításai.
QtObject {
    id: geometryActions
    property var hostViewer: null
    property var hostPhotoArea: null
    property var hostEditController: null
    readonly property var viewer: hostViewer
    readonly property var editorPanel: viewer.editorPanel
    readonly property var cropOverlay: viewer.cropOverlay
    property var nextPreloadImage: null
    property var previousPreloadImage: null

function illesztesiDoboz(keretSzel, keretMag, arany) {
    var teljes = { szel: keretSzel, mag: keretMag, dx: 0, dy: 0 }
    if (!(arany > 0)) return teljes
    var kepSzel = Math.min(keretSzel, keretMag * arany)
    var kepMag = kepSzel / arany
    var fent = viewer.jelvenyHelyFent
    if (fent > 0 && (keretMag - kepMag) / 2 < fent)
        return { szel: keretSzel, mag: keretMag - fent, dx: 0, dy: fent / 2 }
    var bal = viewer.jelvenyHelyBal
    if (bal > 0 && (keretSzel - kepSzel) / 2 < bal)
        return { szel: keretSzel - bal, mag: keretMag, dx: bal / 2, dy: 0 }
    return teljes
}

//: #3877: a `photo`/`photoElotte`/az elő-betöltők textúra-plafonja -
//: ld. `SlideshowView.qml` `texturaEl` (#3832), ugyanaz a V3D-korlát.
readonly property int texturaEl: 2560

//: #3877: a kép `sourceSize`-a - a két betöltési út MÁST kér.
//:
//: - Szolgáltatós út (`image://…`): az állandó `texturaEl`-doboz, mint
//:   a `gpuPrefixImage`-é (#3800). A szolgáltató magától csak kicsinyít
//:   (`edit_preview.py` `_belefer`), KIVÉVE a képpontot jelölő
//:   megjelenítési módot (#1576): az a kis képet szándékosan a kért
//:   dobozra nagyítja, és utána jelöl. Natív méretet kérve a jelölés
//:   natív méreten készülne, és a kirajzolás szétkenné (mérve: 640×400-as
//:   PNG, „Túlcsordult képpontok").
//: - Nyers `file://` út: a Qt fájlbetöltője a kért méretre FELNAGYÍT
//:   (mérve valódi GPU-n: 1440×2560 és 3000×5333 is 2560×4551), ezért a
//:   VALÓDI méretből (`pixelWidthAt`/`pixelHeightAt`, #2492) a dobozba
//:   illő, legfeljebb natív méret kell - a fájlban TÁROLT tájolásban
//:   (`pixelSidesSwappedAt`), mert a Qt a kért méretet arra alkalmazza.
//:   Ugyanaz, mint a `SlideshowView.qml` `forrasMeret`-je (#3832).
function forrasMeret(index, url) {
    var el = viewer.texturaEl
    if (String(url).indexOf("image://") === 0)
        return Qt.size(el, el)
    if (!viewer.photosModel || index < 0
            || typeof viewer.photosModel.pixelWidthAt !== "function")
        return Qt.size(el, 0)
    // a revision-referencia kötelező: a pixelWidthAt/pixelHeightAt
    // Slot-hívás, önmagában nem hoz létre kötés-függőséget (ld.
    // `valodiSzelesseg` ugyanezt a mintát fent)
    var szel = (viewer.photosModel.revision,
                viewer.photosModel.pixelWidthAt(index))
    var mag = viewer.photosModel.pixelHeightAt(index)
    if (szel <= 0 || mag <= 0)
        return Qt.size(el, 0)
    var w = Math.min(el, szel)
    var h = Math.round(mag * w / szel)
    if (h > el) {
        h = el
        w = Math.round(szel * el / mag)
    }
    if (typeof viewer.photosModel.pixelSidesSwappedAt === "function"
            && viewer.photosModel.pixelSidesSwappedAt(index))
        return Qt.size(h, w)
    return Qt.size(w, h)
}

//: #3877: a forrás és a forrásméret EGYÜTT, egyetlen betöltéssel - a
//: `SlideshowView.qml` `_betolt`-jának mintája (#3832). A Qt az `Image`
//: `source`-ának ÉS `sourceSize`-ának MINDEN változására tölt; két külön
//: kötésnél lépéskor mindkettő átfordul, és a kép egyszer a rossz párral
//: is betöltődik (mérve: lépésenként elemenként 2-3 kérés, köztük egy
//: 640×400-as kép 1440×2560-nal kérve → 4096×2560). Méretváltáskor
//: ezért a forrás előbb kiürül (üres forrásra a Qt nem tölt), a méret
//: beáll, és csak utána jön az új forrás.
//:
//: Az elemek `betoltes`-pár változását a `Qt.callLater` fogja össze egy
//: írássá, a kör végén. Mérve: kettős nézetre váltáskor a `photo` párja
//: még a `onLayoutModeChanged` ELŐTT kiértékelődik, amikor a második
//: rekesz előnézete üres - így egyetlen körön belül előbb a nyers fájlt,
//: aztán a szolgáltató helyőrzőjét, végül a kész képet kérte (3 kérés).
function _betoltesekIrasa() {
    viewer._betolt(photoElotte, photoElotte.betoltes)
    viewer._betolt(photo, photo.betoltes)
    viewer._betolt(viewerOverlayControls.nextPreloadImage,
                   viewerOverlayControls.nextPreloadImage.betoltes)
    viewer._betolt(viewerOverlayControls.previousPreloadImage,
                   viewerOverlayControls.previousPreloadImage.betoltes)
}
function _betolt(kep, par) {
    var regi = kep.sourceSize
    var ujMeret = regi.width !== par.meret.width
        || regi.height !== par.meret.height
    if (!ujMeret && kep.source.toString() === String(par.url))
        return
    if (ujMeret) {
        kep.source = ""
        kep.sourceSize = par.meret
    }
    kep.source = par.url
}

//: #3877: a (forrás, méret) pár EGY kiértékelésben, ugyanabból a sorból
//: - a kötött `abMasikSor`/`isCurrentVideo` helyett a friss függvényt
//: és a modellt kérdezzük (#218), különben a pár egyik fele a régi, a
//: másik az új képé lehetne.
function _par(sor, url) {
    return { url: url, meret: viewer.forrasMeret(sor, url) }
}
function _videoE() {
    return viewer.photosModel
        ? (viewer.photosModel.revision,
           viewer.photosModel.isVideoAt(viewer.currentIndex)) === true
        : false
}
//: #3187/#3773: a `photo` a `sor` (az `abMasikSor`) fotóját mutatja. A
//: FŐ vezérlő a KIJELÖLT oldalt szerkeszti, tehát egy képes módban (itt
//: `sor === currentIndex`) és jobb fókusznál a FŐ vezérlő képe jön - a
//: hozzárendelés a fókusszal cserél. Nyitott szerkesztésnél a
//: `filters=` láncot alkalmazó `editpreview` szolgáltató rendereli
//: (`?rev=` cache-buster), egyébként a nyers fájl jön.
function _photoPar(sor) {
    var url = viewer._videoE() ? ""
        : (viewer.layoutMode === "1up" || viewer.aktivOldal === "jobb"
           ? (viewer.editCtl && viewer.editCtl.previewSource !== ""
              ? viewer.editCtl.previewSource : viewer.urlAt(sor))
           : (viewer.masodikEditCtl
              && viewer.masodikEditCtl.previewSource !== ""
              ? viewer.masodikEditCtl.previewSource : viewer.urlAt(sor)))
    return viewer._par(sor, url)
}
function _elotoltoPar(irany) {
    var sor = viewer.photosModel
        ? viewer.photosModel.folderNeighbor(viewer.currentIndex, irany) : -1
    return viewer._par(sor, viewer.photosModel ? viewer.preloadUrlAt(sor) : "")
}

//: #3014: a ténylegesen megjelenített másik kép sora. AB módon kívül
//: mindig a jelenlegi kép (az „aa" mód ugyanazt mutatja kétszer).
//: #3773: a számítás FÜGGVÉNY (`_abMasikSort`), mert a kijelölt és a
//: második sort az imperatív kezelők is ebből számolják - a kötött
//: property ott még a RÉGI értéket adhatja (#218).
readonly property int abMasikSor: viewer._abMasikSort()

function _abMasikSort() {
    if (viewer.layoutMode !== "ab") return viewer.currentIndex
    if (viewer.masodikIndex >= 0) return viewer.masodikIndex
    return viewer._vanSzomszed(viewer.currentIndex, 1)
        ? viewer.currentIndex + 1
        : Math.max(0, viewer.currentIndex - 1)
}

readonly property real zoomFactor: viewer.skalaErtekbol(viewer.zoomValue)
property bool zoomNavigatorDismissed: false
readonly property string zoomMode:
    viewer.zoomValue === 0 ? "fit"
    : viewer.zoomValue === 0.5 ? "actual" : "custom"
property real panX: 0
property real panY: 0

//: #2564: „a fotón értelmezett vezérlők használhatók-e" - EGY helyen
//: kimondva. Eddig a lebegő `zoomBar` `visible`-je hordozta ezt a
//: szabályt; a nagyítás-hármas azóta az ALSÓ ESZKÖZSÁVBAN ül
//: (`TrayBar.qml`), az arc-gombok pedig itt maradtak - a feltételt
//: ezért a néző GYÖKERÉRŐL kell kiadni, hogy ne íródjon meg kétszer
//: (#1486 osztálya). A két ág változatlan: videón nincs mit nagyítani
//: és nincs arc-keret, vágás közben pedig a kép 1:1-re áll vissza.
readonly property bool photoOverlaysUsable:
    !viewer.isCurrentVideo && !editorPanel.cropActive

//: #2492: a csúszka BEAKAD a valódi méretnél. `FUN_005d1300`: a
//: léptetés eredményét a 0,5-höz méri, és az azt átlépő lépés
//: pontosan ott áll meg.
readonly property real zoomDetent: 0.5

// A négy sarok átvitele a fókuszkép helyi koordinátáira a forgatást,
// a nagyítást, a pásztázást és a kétképes nézet kivágását is leképezi.
// A geometriai mezők olvasása a kötést minden QML-átrendezéskor frissíti.
readonly property rect zoomNavigatorViewRect: {
    var image = hostPhotoArea ? hostPhotoArea.fokuszKep : null
    var frame = hostPhotoArea ? hostPhotoArea.fokuszKeret : null
    if (!hostPhotoArea || !image || !frame || image.paintedWidth <= 0
            || image.paintedHeight <= 0 || viewer.zoomFactor <= 0
            || !isFinite(viewer.panX) || !isFinite(viewer.panY))
        return Qt.rect(0, 0, 1, 1)
    var geometryStamp = image.x + image.y + image.width + image.height
                       + image.scale + image.rotation
                       + frame.x + frame.y + frame.width + frame.height
    if (!isFinite(geometryStamp)) return Qt.rect(0, 0, 1, 1)

    var p0 = image.mapFromItem(frame, 0, 0)
    var p1 = image.mapFromItem(frame, frame.width, 0)
    var p2 = image.mapFromItem(frame, 0, frame.height)
    var p3 = image.mapFromItem(frame, frame.width, frame.height)
    var left = Math.min(p0.x, p1.x, p2.x, p3.x)
    var right = Math.max(p0.x, p1.x, p2.x, p3.x)
    var top = Math.min(p0.y, p1.y, p2.y, p3.y)
    var bottom = Math.max(p0.y, p1.y, p2.y, p3.y)
    var contentX = (image.width - image.paintedWidth) / 2
    var contentY = (image.height - image.paintedHeight) / 2
    var x0 = Math.max(0, Math.min(1,
        (left - contentX) / image.paintedWidth))
    var x1 = Math.max(0, Math.min(1,
        (right - contentX) / image.paintedWidth))
    var y0 = Math.max(0, Math.min(1,
        (top - contentY) / image.paintedHeight))
    var y1 = Math.max(0, Math.min(1,
        (bottom - contentY) / image.paintedHeight))
    return Qt.rect(x0, y0, Math.max(0, x1 - x0), Math.max(0, y1 - y0))
}

// Ezek a teljes képre ható eszközök megnyitáskor kitöltő nézetet kérnek.
// Bezáráskor a kitöltő nézet marad: az eredeti nagyítást nem mentjük el.
readonly property var forceFitFilters: [
    "tilt", "radblur", "radsat", "linblur", "dir_tint",
    "radtint", "dir_sat", "dir_brite", "dir_sharp"
]

function forceFitForFilter(filterName) {
    if (viewer.forceFitFilters.indexOf(filterName) >= 0)
        viewer.zoomFit()
}

//: #2492: a kép VALÓDI képpont-mérete a modellből - a `revision`
//: referencia miatt képváltáskor és mentés után is újraértékelődik.
readonly property int valodiSzelesseg: viewer.photosModel
    ? (viewer.photosModel.revision,
       viewer.photosModel.pixelWidthAt(viewer.aktivSor)) : 0

function actualZoomFactor() {
    // Ez a MÉRT képlet `r`-je: a VALÓDI és az ILLESZTETT méret
    // aránya (`docs/specs/ui-audit-editor.md`, „A szerkesztő
    // NAGYÍTÁS-HÁRMASA"). Az eredeti `1to1` buboréksúgója is ezt
    // mondja: „Display Photo at actual size".
    //
    // ⚠️ #2492: KORÁBBAN `photo.sourceSize.width / photo.paintedWidth`
    // állt itt - HIBÁSAN. A Qt olvasáskor a BEÁLLÍTOTT `sourceSize`-t
    // adja vissza, ez az elem pedig 2560-as plafont kap
    // (`sourceSize.width: 2560` lent). Így a képlet a valódi mérettől
    // FÜGGETLENÜL 2560-cal számolt: egy 896 képpont széles képnél
    // ~3,7-es arányt az 1,28 helyett - mérve a tulajdonos
    // képernyőmentésén 3-4-szeres túlnagyítás.
    //
    // Invariáns (#3760): a `paintedWidth` a fájl SZÉLESSÉGÉVEL
    // arányos, a `.picasa.ini` forgatásától függetlenül - a
    // `PreserveAspectFit` a forgatatlan raszter arányával illeszt, a
    // `rotation:` csak utána forgatja a kész dobozt. Ezért az arány
    // forgatott képnél is `valodiSzelesseg / paintedWidth`.
    //: #3741: a fókuszban lévő fél képe - kettős nézetben bal
    //: fókusznál a `photoElotte`.
    var kep = hostPhotoArea ? hostPhotoArea.fokuszKep : null
    if (!kep || kep.paintedWidth <= 0)
        return 1
    if (viewer.valodiSzelesseg > 0)
        return viewer.valodiSzelesseg / kep.paintedWidth
    // Tartalék, ha az index nem tud méretet adni (frissen felvett kép,
    // vagy olvashatatlan fejléc): a BETÖLTÖTT raszter mérete. Ez a
    // `sourceSize`-plafon miatt legfeljebb kisebb lehet a valódinál -
    // tehát a nagyítás legrosszabb esetben kevesebb, sosem több.
    // NEM a `sourceSize`: az a beállított plafont adná vissza.
    return kep.implicitWidth > 0
        ? kep.implicitWidth / kep.paintedWidth : 1
}

//: A MÉRT leképezés (`0x00a601cf`-`0x00a60221`), két folytonos ágon:
//:
//:   0 ≤ v < 0,5 :  1 + (2^(2v) - 1) · (r - 1)
//:   0,5 ≤ v ≤ 1 :  r · 2^(4·(v - 0,5))
//:
//: Rögzített pontok: v=0 → 1 (illesztés), v=0,5 → r (100 %),
//: v=1 → 4r (400 %). A felső fél negyedenként pontosan duplázódik.
function skalaErtekbol(v) {
    var r = viewer.actualZoomFactor()
    var t = Math.max(0, Math.min(1, v))
    return t < 0.5
        ? 1 + (Math.pow(2, 2 * t) - 1) * (r - 1)
        : r * Math.pow(2, 4 * (t - 0.5))
}

function setZoomValue(v) {
    // ⚠️ MÉRT vágás [0, 1]-re (`0x005d13a9` fldz / `0x005d13c6` fld1):
    // az illesztettnél kisebbre és a 400 %-nál nagyobbra nem lehet
    // állítani.
    var uj = Math.max(0, Math.min(1, v))
    if (uj === 0 || viewer.zoomValue === 0)
        zoomNavigatorDismissed = false
    viewer.zoomValue = uj
    if (viewer.zoomValue === 0) { panX = 0; panY = 0 }
    clampPan()
}
function zoomFit() {
    zoomNavigatorDismissed = false
    setZoomValue(0)
    panX = 0
    panY = 0
}
function zoomActual() { setZoomValue(viewer.zoomDetent) }

//: #2492: a léptető út a 0,5-ös beakadással. Ha az érték MÁR pontosan
//: a detenten áll, a lépés elmozdítja (`0x005d1383` - ugyanabban a
//: lépésben nem mozdul el, tehát a következő lépés viszi tovább).
function lepjZoom(delta) {
    var regi = viewer.zoomValue
    var uj = Math.max(0, Math.min(1, regi + delta))
    if (regi !== viewer.zoomDetent
            && (regi - viewer.zoomDetent) * (uj - viewer.zoomDetent) < 0)
        uj = viewer.zoomDetent
    setZoomValue(uj)
}

//: az egérgörgő egy „kattanása" (120 egység) a csúszka 1/20-a - a
//: lépésköz a MI választásunk, a beakadás és a vágás a mért.
function wheelZoom(delta) { lepjZoom((delta / 120) * 0.05) }
// a kép széle ne szakadjon el a látótértől pásztázáskor
//: #3741: a fókuszban lévő fél képét és a SAJÁT felét nézi - egy képen
//: ez a teljes `photoArea`, kettős nézetben a kép fele.
function clampPan() {
    if (!hostPhotoArea) return
    var kep = hostPhotoArea.fokuszKep
    var keret = hostPhotoArea.fokuszKeret
    if (!kep || !keret) return
    var w = (kep.iniSteps % 2 ? kep.paintedHeight
                              : kep.paintedWidth) * zoomFactor
    var h = (kep.iniSteps % 2 ? kep.paintedWidth
                              : kep.paintedHeight) * zoomFactor
    var maxX = Math.max(0, (w - keret.width) / 2)
    var maxY = Math.max(0, (h - keret.height) / 2)
    panX = Math.max(-maxX, Math.min(maxX, panX))
    panY = Math.max(-maxY, Math.min(maxY, panY))
}

function panFromZoomNavigator(deltaX, deltaY) {
    if (!hostPhotoArea) return
    var image = hostPhotoArea.fokuszKep
    if (!image || viewer.zoomFactor <= 1.01) return
    var origin = image.mapToItem(hostPhotoArea, 0, 0)
    var moved = image.mapToItem(
        hostPhotoArea,
        deltaX * image.paintedWidth,
        deltaY * image.paintedHeight)
    panX -= moved.x - origin.x
    panY -= moved.y - origin.y
    clampPan()
}

function show(index) { viewer.currentIndex = index; viewer.forceActiveFocus() }

// A Kép menü egyes egylépéses javításai szerkesztőben a megfelelő
// panelfület nyitják meg; a könyvtárnézetben a kijelölésre futnak.
function selectMenuEffect(name) {
    if (name === "autolight" || name === "autocolor"
            || name === "enhance") {
        editorPanel.selectTab(0)
        return true
    }
    if (name === "unsharp" || name === "warm" || name === "grain2") {
        editorPanel.selectTab(2)
        return true
    }
    return false
}

// Vágás alkalmazása a kijelölésből. advance=true: Enter-flow -
// következő kép, vágó-mód megtartva; false: Alkalmaz gomb - a panel
// visszaáll az eszközrácsra (Picasa-viselkedés).
function applyCrop(advance) {
    if (!hostEditController) return
    if (!cropOverlay.hasSelection) {
        if (!advance) editorPanel.cropActive = false
        return
    }
    var r = cropOverlay.cropRect
    hostEditController.applyCrop(r.x, r.y, r.width, r.height)
    cropOverlay.resetSelection()
    if (advance) viewer.next()
    else editorPanel.cropActive = false
}

}
