import QtQuick

Image {
    required property var photoArea
    required property var paintMaskArea
    id: photoElotte
    objectName: "viewerImageElotte"
    visible: photoArea.hostViewer.layoutMode !== "1up"
             && !photoArea.hostViewer.isCurrentVideo
    //: #3014: vízszintesen a BAL, függőlegesen a FELSŐ
    //: felet kapja — a `swap_2up_layout` ezt fordítja
    //: (a `photoElotteKeret` geometriája).
    //:
    //: #3741: a `photo` mintájára a SAJÁT forgatásával
    //: (`rotate=` az ini-ben) jelenik meg, és bal
    //: fókusznál övé a nagyítás és a pásztázás.
    readonly property int iniSteps: photoArea.hostViewer.photosModel
        ? (photoArea.hostViewer.photosModel.revision,
           photoArea.hostViewer.photosModel.rotateAt(photoArea.hostViewer.currentIndex))
        : 0
    //: #3756: a képernyőn látszó arány és a jelvény
    //: helyét fenntartó illesztési doboz.
    readonly property real kepArany:
        implicitWidth > 0 && implicitHeight > 0
        ? (iniSteps % 2 ? implicitHeight / implicitWidth
                        : implicitWidth / implicitHeight)
        : 0
    readonly property var doboz: photoArea.hostViewer.illesztesiDoboz(
        parent.width, parent.height, kepArany)
    anchors.centerIn: parent
    anchors.horizontalCenterOffset: doboz.dx
        + (photoArea.hostViewer.balFokusz ? photoArea.hostViewer.panX : 0)
    anchors.verticalCenterOffset: doboz.dy
        + (photoArea.hostViewer.balFokusz ? photoArea.hostViewer.panY : 0)
    scale: photoArea.hostViewer.balFokusz ? photoArea.hostViewer.zoomFactor : 1
    transformOrigin: Item.Center
    width: iniSteps % 2 ? doboz.mag : doboz.szel
    height: iniSteps % 2 ? doboz.szel : doboz.mag
    rotation: iniSteps * 90
    //: #3014/#3187: AB módban itt a JELENLEGI kép áll
    //: (#3773: a bal a `currentIndex`-et mutatja, ld.
    //: `aktivSor`), a SAJÁT előnézet-rekeszén át —
    //: tehát a mentett `filters=` láncával, ahogy a
    //: rácsban és az egy képes nézetben is látszik (a
    //: #3187 előtt itt a nyers fájl jött, és ugyanaz a
    //: kép kétféleképp látszott a programban).
    //: #3187: ez a fél a `currentIndex` fotóját
    //: mutatja — a fő rekeszből, ha a KIJELÖLT oldal
    //: ez, egyébként a másodikból.
    //: #3014: „aa" módban UGYANÍGY — ott a két rekesz
    //: ugyanannak a fotónak két önálló szerkesztése.
    //: #3877: a forrás és a forrásméret EGYÜTT
    //: íródik (`viewer._betolt`) — ld. ott, miért
    //: nem két kötés. Ez csak a pár kötése.
    readonly property var betoltes: photoArea.hostViewer._par(
        photoArea.hostViewer.currentIndex,
        photoArea.hostViewer._videoE()
        ? ""
        : (photoArea.hostViewer.layoutMode === "1up"
           ? photoArea.hostViewer.urlAt(photoArea.hostViewer.currentIndex)
           : (photoArea.hostViewer.aktivOldal === "bal"
              ? (photoArea.hostEditCtl
                 && photoArea.hostEditCtl.previewSource !== ""
                 ? photoArea.hostEditCtl.previewSource
                 : photoArea.hostViewer.urlAt(photoArea.hostViewer.currentIndex))
              : (photoArea.hostViewer.masodikEditCtl
                 && photoArea.hostViewer.masodikEditCtl.previewSource !== ""
                 ? photoArea.hostViewer.masodikEditCtl.previewSource
                 : photoArea.hostViewer.urlAt(photoArea.hostViewer.currentIndex)))))
    onBetoltesChanged: Qt.callLater(photoArea.hostViewer._betoltesekIrasa)
    Component.onCompleted: photoArea.hostViewer._betolt(photoElotte, betoltes)
    fillMode: Image.PreserveAspectFit
    asynchronous: Qt.platform.pluginName !== "offscreen"
    autoTransform: true

    //: #3663: a képre kattintás a BAL/FELSŐ felet
    //: aktiválja — a `swap_2up_focus` gomb ugyanezt
    //: teszi (ld. `ui-audit-editor.md` 3/b.4). Csak
    //: 2-up módban hat, és csak akkor, ha épp nincs
    //: aktív pontos-kattintású szerkesztő-eszköz a
    //: KÉPEN (azok kattintása MÁST jelent — célpont,
    //: minta, pötty). #3741: a `retouchClickArea`/
    //: `cropOverlay`/`textClickArea`/`redeyeOverlay` a
    //: `photoArea.fokuszKep`-re kerül — bal fókusznál
    //: épp IDE, tehát ilyenkor itt IS old ütközést,
    //: ugyanúgy, ahogy a `photo` párja jobb fókusznál.
    //: `neutralPickArea`/`paintMaskArea` marad kivétel
    //: MINDKÉT irányban (ld. a `photo` párját).
    TapHandler {
        enabled: photoArea.hostViewer.layoutMode !== "1up"
            && !photoArea.hostEditorPanel.neutralPickerActive
            && photoArea.hostEditorPanel.effectColorPickerTarget < 0
            && !paintMaskArea.aktiv
            && !(photoArea.hostViewer.aktivOldal === "bal"
                 && (photoArea.hostEditorPanel.cropActive
                     || photoArea.hostEditorPanel.redeyeActive
                     || photoArea.hostEditorPanel.retouchActive
                     || photoArea.hostEditorPanel.textActive))
        onTapped: photoArea.hostViewer.fokuszValt("bal")
    }
}
