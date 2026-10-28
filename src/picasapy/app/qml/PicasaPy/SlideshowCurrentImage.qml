import QtQuick

Image {
    id: slide
    property alias panZoomAnimation: kenBurns
    property alias panZoomFaceAnimation: kenBurnsFace
    property var slideshow: null
    objectName: "slideshowImage"
    property real transitionOffsetX: 0
    property real transitionOffsetY: 0
    property var panZoomRectangles: []
    property real panZoomProgress: 0
    // az ini-forgatást a nézővel azonos módon követi (revision-kötés)
    readonly property int iniSteps: slideshow.photosModel
        ? (slideshow.photosModel.revision,
           slideshow.photosModel.rotateAt(slideshow.currentIndex))
        : 0
    readonly property real forrasPixelSzelesseg: slideshow.photosModel
        && slideshow.currentIndex >= 0
        && typeof slideshow.photosModel.pixelWidthAt === "function"
        ? slideshow.photosModel.pixelWidthAt(slideshow.currentIndex) : 0
    readonly property real forrasPixelMagassag: slideshow.photosModel
        && slideshow.currentIndex >= 0
        && typeof slideshow.photosModel.pixelHeightAt === "function"
        ? slideshow.photosModel.pixelHeightAt(slideshow.currentIndex) : 0
    readonly property real forgatottPixelSzelesseg: iniSteps % 2
        ? forrasPixelMagassag : forrasPixelSzelesseg
    readonly property real forgatottPixelMagassag: iniSteps % 2
        ? forrasPixelSzelesseg : forrasPixelMagassag
    readonly property bool panZoomActive: slideshow.transitionKind === "kenburns"
        && panZoomRectangles && panZoomRectangles.length === 2
        && forrasPixelSzelesseg > 0 && forrasPixelMagassag > 0
    readonly property real panZoomX: panZoomActive
        ? panZoomRectangles[0].x
            + (panZoomRectangles[1].x - panZoomRectangles[0].x)
                * panZoomProgress : 0
    readonly property real panZoomY: panZoomActive
        ? panZoomRectangles[0].y
            + (panZoomRectangles[1].y - panZoomRectangles[0].y)
                * panZoomProgress : 0
    readonly property real panZoomWidth: panZoomActive
        ? panZoomRectangles[0].width
            + (panZoomRectangles[1].width - panZoomRectangles[0].width)
                * panZoomProgress : 1
    readonly property real panZoomHeight: panZoomActive
        ? panZoomRectangles[0].height
            + (panZoomRectangles[1].height - panZoomRectangles[0].height)
                * panZoomProgress : 1
    readonly property real panZoomScale: panZoomActive && panZoomWidth > 0
        ? parent.width / panZoomWidth : 1
    width: panZoomActive ? forrasPixelSzelesseg * panZoomScale
                         : (iniSteps % 2 ? parent.height : parent.width)
    height: panZoomActive ? forrasPixelMagassag * panZoomScale
                          : (iniSteps % 2 ? parent.width : parent.height)
    x: panZoomActive
       ? -panZoomX * panZoomScale
            + (forgatottPixelSzelesseg - forrasPixelSzelesseg)
                * panZoomScale / 2 + transitionOffsetX
       : (parent.width - width) / 2 + transitionOffsetX
    y: panZoomActive
       ? -panZoomY * panZoomScale
            + (forgatottPixelMagassag - forrasPixelMagassag)
                * panZoomScale / 2 + transitionOffsetY
       : (parent.height - height) / 2 + transitionOffsetY
    rotation: iniSteps * 90
    // #1640: a megjelenítési mód (Projektor mód stb.) a NYERS fájl
    // URL-jén nem látszik — a `displayUrlAt` aktív módnál a
    // `displayphoto` szolgáltatóra vált, mód nélkül a sima file://-t adja
    // vissza.
    //
    // ⚠️ A mód VALÓDI ARGUMENTUM, nem eldobott referencia. Az első
    // változat `(controller.displayMode, …)` alakú vessző-kifejezés volt,
    // és MÉRVE nem hozott létre kötés-függőséget: módváltás után a dia
    // URL-je a nyers fájlé maradt, a mód némán elveszett.
    //
    // #3832: a `source`-ot és a `sourceSize`-t a `_diakBetolt` írja,
    // EGYÜTT — két külön kötés lépésenként fölösleges betöltést okozott
    // (ld. `_betolt`). A módváltást az `onDisplayModeChanged` követi.
    fillMode: Image.PreserveAspectFit
    asynchronous: Qt.platform.pluginName !== "offscreen"
    autoTransform: true
    //: #3832: a kép VALÓDI méretéből számolt, pontos forrásméret (ld.
    //: `forrasMeret`); a `_diakBetolt` írja. Ez csak a kezdőérték.
    sourceSize: slideshow.forrasMeret(-1)

    //: #5258: a képarányra illesztett képből számolt két kivágás között
    //: pásztáz; a dia-idő alatt ér el a B téglalapig.
    NumberAnimation on panZoomProgress {
        id: kenBurns
        objectName: "slideshowKenBurns"
        running: slideshow.visible
                 && slideshow.transitionKind === "kenburns"
                 && slideshow.currentIndex >= 0
                 && slide.panZoomRectangles.length === 2
        from: 0.0
        to: 1.0
        duration: Math.max(slideshow.intervalMs, 1)
    }
    //: A képernyővédő arcos változata (`kenburnsaoi`) külön átmenet;
    //: a #5258 csak a sima Pan and Zoom kivágásait cseréli le.
    NumberAnimation on scale {
        id: kenBurnsFace
        objectName: "slideshowKenBurnsFace"
        running: slideshow.visible
                 && slideshow.transitionKind === "kenburnsaoi"
                 && slideshow.currentIndex >= 0
        from: 1.0
        to: 1.12
        duration: Math.max(slideshow.intervalMs, 1)
    }
    //: a nagyítás NEM ragadhat be: átmenet-váltáskor visszaáll
    onScaleChanged: if (slideshow.transitionKind !== "kenburns"
                        && slideshow.transitionKind !== "kenburnsaoi"
                        && scale !== 1.0)
                        scale = 1.0
}
