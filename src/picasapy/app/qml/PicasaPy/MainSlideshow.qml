import QtQuick
import QtQuick.Controls
import PicasaPy

// A főablak diavetítési rétege.
SlideshowView {
    property var hostWindow
    id: slideshow
    objectName: "slideshowView"
    anchors.fill: parent
    bigSlideshow2: (typeof controller !== "undefined" && controller)
        ? controller.bigSlideshow2 : true
    screenDepth: (typeof controller !== "undefined" && controller)
        ? controller.slideshowScreenDepth : 0
    timelineSlideshow: hostWindow.timelineSlideshowActive
    panZoomRectanglesProvider: function(
        sourceWidth, sourceHeight, viewWidth, viewHeight
    ) {
        return (typeof controller !== "undefined" && controller)
            ? controller.slideshowPanZoomRectangles(
                  sourceWidth, sourceHeight, viewWidth, viewHeight)
            : []
    }
    z: 100
    // #305: null-őr
    photosModel: typeof controller === "undefined" || !controller ? null
        : slideshow.screensaverMode ? controller.screensaverPhotos
        : hostWindow.timelineSlideshowActive ? hostWindow.timelineSlideshowModel
        : controller.photos
    // #1640: a megjelenítési mód a vetített képre is hat - a kötés innen
    // adja át, hogy a dia URL-je módváltáskor újraértékelődjön
    displayMode: (typeof controller !== "undefined" && controller)
        ? controller.displayMode : ""
    //: #433: a vetítés-beállítások MEGŐRZÖTTEK - a választó a
    //: vezérlőbe ír, a kötés innen olvassa vissza.
    transitionKind: typeof controller === "undefined" || !controller
        ? "dissolve"
        : slideshow.screensaverMode ? controller.screensaverEffect
        : controller.slideshowTransition
    transitionMs: (typeof controller !== "undefined" && controller)
        ? controller.slideshowTransitionMs : 700
    captionMode: typeof controller === "undefined" || !controller
        ? "caption"
        : slideshow.screensaverMode
            ? (controller.screensaverShowCaptions ? "caption" : "none")
            : controller.slideshowCaptionMode
    //: #2992: a diaidő (`SlideshowEffectTime`) - a sáv ± gombjai a
    //: vezérlőbe írnak, a kötés innen olvassa vissza.
    seconds: typeof controller === "undefined" || !controller ? 3
        : slideshow.screensaverMode ? controller.screensaverSeconds
        : controller.slideshowSeconds
    // #4320: a képernyővédő saját ciklusát megtartja; az ismétlés és a
    // zene a Beállítások Diavetítés füléről vezérli a normál vetítést.
    loop: typeof controller === "undefined" || !controller
        || slideshow.screensaverMode ? true : controller.slideshowLoop
    musicEnabled: typeof controller !== "undefined" && controller
        && !slideshow.screensaverMode && controller.slideshowMusicEnabled
    musicTrackUrls: typeof controller === "undefined" || !controller
        || slideshow.screensaverMode ? [] : controller.slideshowMusicTrackUrls
    onTransitionPicked: function (kulcs) {
        if (typeof controller !== "undefined" && controller)
            controller.setSlideshowTransition(kulcs)
    }
    onCaptionModePicked: function (mod) {
        if (typeof controller !== "undefined" && controller)
            controller.setSlideshowCaptionMode(mod)
    }
    onSecondsChosen: function (masodperc) {
        if (typeof controller !== "undefined" && controller)
            controller.setSlideshowSeconds(masodperc)
    }
    // #5653: ugyanaz az Időrend-belépés, mint a Nézet menüben; a vetítés
    // bezárása előbb lefuttatja az exitSlideshow visszaállítását.
    onTimelineRequested: {
        slideshow.stop()
        hostWindow.toggleTimeline()
    }
    onClosed: hostWindow.exitSlideshow()
    onStarToggled: function(index) {
        if (typeof controller !== "undefined" && controller)
            controller.toggleStar(index)
    }
    onRotateRequested: function(index, delta) {
        if (typeof controller === "undefined" || !controller) return
        if (delta > 0) controller.rotateRight(index)
        else controller.rotateLeft(index)
    }
}
