import QtQuick

Image {
    required property var photoArea
    required property var paintMaskArea
    id: photo
    objectName: "viewerImage"
    // videónál a fotó-Image üres és rejtett (#14) — a
    // videofájlt nem próbáljuk képként dekódolni
    visible: !photoArea.hostViewer.isCurrentVideo
    // a model.revision referencia miatt a kötés minden
    // modell-frissítésnél újraértékelődik
    readonly property int iniSteps: photoArea.hostViewer.photosModel
        ? (photoArea.hostViewer.photosModel.revision,
           photoArea.hostViewer.photosModel.rotateAt(photoArea.hostViewer.abMasikSor))
        : 0
    // #6: zoom + pásztázás — a skála az illesztett
    // mérethez képest, az eltolás a pan-állapotból
    //
    //: #3014/#3773: 2-up módban a fő kép a MÁSIK
    //: (a `abMasikSor`) felet kapja — a bal a
    //: `currentIndex`-et — a fél helyét és méretét a
    //: `photoKeret` adja.
    //: #3741: a nagyítás és a pásztázás csak akkor
    //: az övé, ha ez a fókuszban lévő fél.
    //: #3756: a `photoElotte` párja — a jelvény
    //: helyét fenntartó illesztési doboz (egy képen
    //: a teljes keret).
    readonly property real kepArany:
        implicitWidth > 0 && implicitHeight > 0
        ? (iniSteps % 2 ? implicitHeight / implicitWidth
                        : implicitWidth / implicitHeight)
        : 0
    readonly property var doboz: photoArea.hostViewer.illesztesiDoboz(
        parent.width, parent.height, kepArany)
    anchors.centerIn: parent
    anchors.horizontalCenterOffset: doboz.dx
        + (photoArea.hostViewer.balFokusz ? 0 : photoArea.hostViewer.panX)
    anchors.verticalCenterOffset: doboz.dy
        + (photoArea.hostViewer.balFokusz ? 0 : photoArea.hostViewer.panY)
    scale: photoArea.hostViewer.balFokusz ? 1 : photoArea.hostViewer.zoomFactor
    transformOrigin: Item.Center
    // 90°/270°-nál a befoglaló doboz oldalai cserélődnek
    width: iniSteps % 2 ? doboz.mag : doboz.szel
    height: iniSteps % 2 ? doboz.szel : doboz.mag
    rotation: iniSteps * 90
    //: #3877: a forrás és a forrásméret EGYÜTT
    //: íródik — ld. `viewer._betolt`; a pár és a
    //: forrás szabálya (#3187/#3773, #305 null-őr):
    //: `viewer._photoPar`.
    readonly property var betoltes: photoArea.hostViewer._photoPar(
        photoArea.hostViewer._abMasikSort())
    onBetoltesChanged: Qt.callLater(photoArea.hostViewer._betoltesekIrasa)
    Component.onCompleted: photoArea.hostViewer._betolt(photo, betoltes)
    fillMode: Image.PreserveAspectFit
    // #53: offscreen (teszt) platformon szinkron betöltés —
    // itt reprodukálódott a GIL-deadlock (a lapozás
    // setProperty-je vs. az image-provider szál). Szinkron
    // betöltésnél nincs provider-szál, így nincs holtpont;
    // produkcióban marad az async.
    asynchronous: Qt.platform.pluginName !== "offscreen"
    autoTransform: true   // EXIF-orientáció

    //: #3663: a képre kattintás a JOBB/ALSÓ felet
    //: aktiválja — ld. a `photoElotte`-n lévő párját.
    //: #3693: itt a `retouchClickArea`/`cropOverlay`/
    //: `textClickArea`/`redeyeOverlay` valódi átfedő
    //: `MouseArea`-k, ezért amíg a fókusz JOBB (tehát az
    //: átfedő a `photoArea.fokuszKep`-en át épp ide, a
    //: `photo`-ra kerül, #3741), a kattintás MARAD az ő
    //: dolguk. #3741: BAL fókusznál az átfedő a MÁSIK
    //: félre, a `photoElotte`-ra kerül — itt ekkor nincs
    //: ütközés, tehát a kattintás mehet a kapun
    //: (`fokuszValt`) át, ahogy a `photoElotte` felől is
    //: már ment (#3693, `TestAKepreKattintassal`).
    //: `neutralPickArea`/`paintMaskArea` marad kivétel
    //: MINDKÉT irányban — ld. a `photoElotte` párját.
    TapHandler {
        enabled: photoArea.hostViewer.layoutMode !== "1up"
            && !photoArea.hostEditorPanel.neutralPickerActive
            && photoArea.hostEditorPanel.effectColorPickerTarget < 0
            && !paintMaskArea.aktiv
            && !(photoArea.hostViewer.aktivOldal === "jobb"
                 && (photoArea.hostEditorPanel.cropActive
                     || photoArea.hostEditorPanel.redeyeActive
                     || photoArea.hostEditorPanel.retouchActive
                     || photoArea.hostEditorPanel.textActive))
        onTapped: photoArea.hostViewer.fokuszValt("jobb")
    }
}
