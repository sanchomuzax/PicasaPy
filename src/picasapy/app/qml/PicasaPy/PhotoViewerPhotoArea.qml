import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import PicasaPy.Gpu
import "aranykenyszer.js" as AranyKenyszer

Item {
    id: photoArea
    property var hostViewer: null
    readonly property var hostEditCtl:
        (typeof editController !== "undefined") ? editController : null
    property var hostViewerPanArea: null
    property var hostEditorPanel: null
    property alias hostCropOverlay: cropOverlay
    property alias hostEditorToolBar: editorToolBar
    property alias hostEffectColorPickArea: effectColorPickArea
    property alias hostFacesOverlay: facesOverlay
    property alias hostGpuPrefixImage: gpuPrefixImage
    property alias hostKepkockaJelzes: kepkockaJelzes
    property alias hostNeutralPickArea: neutralPickArea
    property alias hostPaintMaskArea: paintMaskArea
    property alias hostPhoto: photo
    property alias hostPhotoElotte: photoElotte
    property alias hostPhotoElotteKeret: photoElotteKeret
    property alias hostPhotoKeret: photoKeret
    property alias hostRedeyeDragArea: redeyeDragArea
    property alias hostRetouchClickArea: retouchClickArea
    property alias hostTextClickArea: textClickArea
    property alias hostVideoLoader: videoLoader
    objectName: "viewerPhotoArea"
    anchors.fill: parent
    anchors.margins: 14
    anchors.bottomMargin: 30
    // #6 utójavítás (felhasználói hibajelzés): a nagyított
    // kép NE lógjon ki a képterületből a bal panel / a
    // felső sáv / a felirat-sor fölé — a QML alapból nem
    // vág, a zoomhoz kötelező a clip
    clip: true

    //: #3013: a KETTŐS NÉZET bal oldala — a szerkesztés
    //: ELŐTTI kép. A nyers fájl URL-je, a `filters=` lánc
    //: nélkül: ez a „mi volt" oldal. Csak 2-up módban
    //: látszik, és a fő képpel EGYFORMA méretet kap.
    //: #3741: a BAL/FELSŐ fél kerete — a `photoElotte` régi
    //: befoglaló doboza. Bal fókusznál a nagyított kép ezen
    //: belül marad (ld. a `photoKeret` párját).
    Item {
        id: photoElotteKeret
        objectName: "viewerImageElotteKeret"
        //: ⚠️ Horgony helyett SZÁMOLT geometria: a
        //: `anchors.bottom: … ? undefined : parent.bottom`
        //: alakot a Qt nem bontja vissza, tehát függőleges
        //: elrendezésben a magasság-kötés néma no-op lett
        //: volna (mérve: a felső kép a teljes területet
        //: kapta, a két kép egymásra csúszott).
        x: 0
        y: 0
        width: photoArea.hostViewer.layoutMode === "1up"
            ? 0
            : (photoArea.hostViewer.fuggolegesElrendezes
               ? parent.width
               : Math.floor((parent.width - 8) / 2))
        height: photoArea.hostViewer.layoutMode === "1up"
            ? 0
            : (photoArea.hostViewer.fuggolegesElrendezes
               ? Math.floor((parent.height - 8) / 2)
               : parent.height)
        clip: photoArea.hostViewer.balFokusz && photoArea.hostViewer.zoomFactor > 1
        PhotoViewerElotteImage {
            id: photoElotte
            photoArea: photoArea
            paintMaskArea: paintMaskArea
        }
    }

    //: #3741: a JOBB/ALSÓ fél kerete — a `photo` régi befoglaló
    //: doboza (ugyanaz a középpont és méret), hogy a nagyított
    //: kép a SAJÁT felén belül maradjon (`clip`), ne lógjon rá
    //: a másikra. Nagyítás nélkül nincs vágás: ilyenkor a kép
    //: amúgy is a felén belül van, a vágókeret fogantyúi pedig
    //: a résbe nyúlhatnak, ahogy eddig. Egy képen a keret a
    //: teljes `photoArea` (ott a `photoArea` maga vág).
    //: #3014: a fél középpontja a fél terület közepére
    //: kerül: eltolás = (méret + rés) / 4.
    Item {
        id: photoKeret
        objectName: "viewerImageKeret"
        anchors.centerIn: parent
        anchors.horizontalCenterOffset:
            photoArea.hostViewer.layoutMode === "1up"
                || photoArea.hostViewer.fuggolegesElrendezes
            ? 0 : (photoArea.width + 8) / 4
        anchors.verticalCenterOffset:
            photoArea.hostViewer.layoutMode !== "1up"
                && photoArea.hostViewer.fuggolegesElrendezes
            ? (photoArea.height + 8) / 4 : 0
        width: photoArea.hostViewer.layoutMode === "1up"
                || photoArea.hostViewer.fuggolegesElrendezes
            ? photoArea.width
            : Math.floor((photoArea.width - 8) / 2)
        height: photoArea.hostViewer.layoutMode !== "1up"
                && photoArea.hostViewer.fuggolegesElrendezes
            ? Math.floor((photoArea.height - 8) / 2)
            : photoArea.height
        clip: photoArea.hostViewer.layoutMode !== "1up" && !photoArea.hostViewer.balFokusz
              && photoArea.hostViewer.zoomFactor > 1
        PhotoViewerFotoImage {
            id: photo
            photoArea: photoArea
            paintMaskArea: paintMaskArea
        }
    }

    //: #3741: az eszközátfedők (vágás/retusálás/szöveg/
    //: vörösszem, és a hozzájuk tartozó `frameContentArea`/
    //: `editorToolBar`/`paintMaskArea`/`neutralPickArea`)
    //: mind a TÉNYLEGESEN szerkesztett — a fő
    //: `editController` láncát viselő — félre kerülnek. Az
    //: melyik VIZUÁLIS fél ez, az `aktivOldal`-tól függ,
    //: ugyanaz a leképezés, mint a `viewerFocusBadge`
    //: (lentebb, a `photoArea` testvéreként deklarált
    //: „Kijelölve” jelvény) saját `fokuszKep`-jéé:
    //: `viewer.balFokusz` esetén a `photoElotte` (a
    //: `source`-kötés szerint EKKOR kapja az
    //: `editCtl.previewSource`-t), egyébként — egy képes
    //: módban MINDIG — a `photo`. A hiba előtt minden felsorolt
    //: elem fixen a `photo`-hoz volt rögzítve — helyes volt
    //: az alapértelmezett jobb fókusznál, de bal fókusznál a
    //: NEM kijelölt képen jelent meg (mérve, #3741).
    readonly property var fokuszKep:
        photoArea.hostViewer.balFokusz ? photoElotte : photo
    //: a fókuszban lévő kép fele (`photoElotteKeret`/
    //: `photoKeret`) — a pásztázás határa és a nagyított
    //: kép vágása
    readonly property var fokuszKeret:
        photoArea.hostViewer.balFokusz ? photoElotteKeret : photoKeret

    // #4553: a fókuszos effekt nyitott paraméterpaneljén a
    // puck a ténylegesen szerkesztett, kirajzolt képre kerül.
    // Saját rétegként követi a kétképes nézet fókuszváltását,
    // a zoomot, az elforgatást és a képernyőhöz illesztést.
    EffectFocalPuck {
        targetImage: photoArea.fokuszKep
        panel: photoArea.hostEditorPanel
    }

    PhotoViewerStraightenGrid {
        photoArea: photoArea
        editorToolBar: editorToolBar
    }

    // GPU élő-előnézet (#22): a `fokuszKep` FÖLÖTT (#3755:
    // ab/aa módban ez a kijelölt fél, `photoElotte` vagy
    // `photo` — l. lent a geometriánál), csak akkor
    // látható, ha `gpuFinetuneActive && gpuFinetuneEligible`
    // (ld. a fenti property-k docsztringjét). A két rejtett
    // `Image` a forrás (a finetune2 ELŐTTI kép) és a
    // 256×1 LUT-textúra betöltője — `smooth: false` a
    // LUT-on kötelező (egzakt indexelés, ld.
    // GpuPointFilterPreview.qml). GPU-képtelen
    // futtatókörnyezetben (`gpuFinetuneEligible` mindig
    // false) ez a réteg SOSEM válik láthatóvá — a `fokuszKep`
    // Image alatta változatlanul a rendes CPU-előnézetet
    // mutatja, semmi nem törhet emiatt CI-ban.
    Image {
        id: gpuPrefixImage
        objectName: "gpuPrefixImage"
        visible: false
        source: photoArea.hostViewer.gpuFinetuneEligible
                ? photoArea.hostEditCtl.gpuPrefixSource : ""
        asynchronous: Qt.platform.pluginName !== "offscreen"
        autoTransform: true
        // #3800: befoglaló doboz — álló képnél a csak szélességre
        // kért méret a V3D 4096-os textúraplafonja fölé nőne
        sourceSize: Qt.size(2560, 2560)
    }
    Image {
        id: gpuLutImage
        objectName: "gpuLutImage"
        visible: false
        smooth: false
        cache: false
        source: photoArea.hostViewer.gpuFinetuneEligible
                ? photoArea.hostEditCtl.gpuLutSource : ""
    }
    PhotoViewerGpuFinetune {
        id: gpuFinetuneVago
        photoArea: photoArea
        gpuPrefixImage: gpuPrefixImage
        gpuLutImage: gpuLutImage
    }

    // #14: videó-lejátszó — csak videónál töltődik be, így
    // a Qt Multimedia hiánya a fotó-nézetet nem érinti
    Loader {
        id: videoLoader
        objectName: "videoLoader"
        anchors.fill: parent
        active: photoArea.hostViewer.visible && photoArea.hostViewer.isCurrentVideo
        source: "VideoPlayerView.qml"
    }
    Binding {
        target: videoLoader.item
        property: "source"
        value: photoArea.hostViewer.urlAt(photoArea.hostViewer.currentIndex)
        when: videoLoader.status === Loader.Ready
              && photoArea.hostViewer.isCurrentVideo
    }
    //: #1838: a VÁGÁSPONTOK átadása a lejátszónak. A Picasából
    //: örökölt `moviestart`/`movieend` a `filters=` láncban ül;
    //: a modell ezredmásodpercre váltva adja, és a **−1
    //: jelenti, hogy azon az oldalon nincs vágás** (a 0 a
    //: nulla pontra állított kezdés lenne).
    //: ⚠️ A `revision` SZÁNDÉKOS kötés-függőség: a
    //: `movieTrimAt` sima slot-hívás, magától nem szól, ha a
    //: vágás mentése átírta a sort. Enélkül a `setin` után a
    //: lejátszó a RÉGI szakaszt tartaná, és a vágás csak
    //: átnavigálás után élne (a projekt itemAt/revision
    //: mintája, `LightboxFeed.qml`).
    Binding {
        target: videoLoader.item
        property: "trimStartMs"
        value: photoArea.hostViewer.photosModel
               ? (photoArea.hostViewer.photosModel.revision,
                  photoArea.hostViewer.photosModel.movieTrimAt(
                      photoArea.hostViewer.currentIndex).start) : -1
        when: videoLoader.status === Loader.Ready
              && photoArea.hostViewer.isCurrentVideo
    }
    Binding {
        target: videoLoader.item
        property: "trimEndMs"
        value: photoArea.hostViewer.photosModel
               ? (photoArea.hostViewer.photosModel.revision,
                  photoArea.hostViewer.photosModel.movieTrimAt(
                      photoArea.hostViewer.currentIndex).end) : -1
        when: videoLoader.status === Loader.Ready
              && photoArea.hostViewer.isCurrentVideo
    }
    //: #1838: a vágás MENTÉSE — a lejátszó jelez, a vezérlő ír.
    //: A sor indexe itt ismert, a komponens nem is látja.
    Connections {
        target: videoLoader.item
        enabled: videoLoader.status === Loader.Ready
                 && photoArea.hostViewer.isCurrentVideo
        ignoreUnknownSignals: true
        function onTrimRequested(startMs, endMs) {
            if (typeof controller !== "undefined" && controller
                    && controller.setMovieTrim !== undefined)
                controller.setMovieTrim(
                    photoArea.hostViewer.currentIndex, startMs, endMs)
        }
        //: #1838: a képkocka mentése — a vezérlő dekódol és ír
        function onCaptureFrameRequested(positionMs) {
            if (typeof controller !== "undefined" && controller
                    && controller.captureMovieFrame !== undefined)
                controller.captureMovieFrame(
                    photoArea.hostViewer.currentIndex, positionMs)
        }
        // #4449/#4458: csak a videó-előnézeti terület
        // kérhet kattintásra visszalépést; a PhotoViewer
        // közös kilépési kapuja védi a félkész szerkesztést.
        function onExitRequested() {
            photoArea.hostViewer.kerBezaras()
        }
    }
    //: #5715: a képkocka-mentés négy állapota a vezérlő
    //: jelzéseit követi (`CCaptureFrame::captureframeprog1..4`).
    Text {
        id: kepkockaJelzes
        objectName: "videoCaptureNotice"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 56
        visible: text !== ""
        color: Theme.mediaOverlayText
        font.pixelSize: Theme.fontSize
        text: ""

        Timer {
            id: kepkockaJelzesIdozito
            interval: 4000
            onTriggered: kepkockaJelzes.text = ""
        }

        function mutasd(uzenet) {
            kepkockaJelzes.text = uzenet
            kepkockaJelzesIdozito.restart()
        }
    }

    Connections {
        target: typeof controller !== "undefined" ? controller : null
        ignoreUnknownSignals: true
        function onMovieFrameCapturing() {
            kepkockaJelzes.mutasd(qsTr("Capturing frame..."))
        }
        function onMovieFrameSaving() {
            kepkockaJelzes.mutasd(
                qsTr("Saving to Captured Videos"))
        }
        //: `CCaptureFrame::captureframeprog3`
        function onMovieFrameCaptured(path) {
            kepkockaJelzes.mutasd(
                qsTr("Saved %1 to Captured Videos").arg(
                    path.substring(path.lastIndexOf("/") + 1)))
        }
        //: `CCaptureFrame::captureframeprog4`
        function onMovieFrameCaptureFailed() {
            kepkockaJelzes.mutasd(qsTr("Failed to capture frame"))
        }
        function onMovieClipExported(path) {
            var fajlnev = String(path).replace(/^.*[\\/]/, "")
            kepkockaJelzes.mutasd(
                qsTr("Saved %1 to Exported Videos").arg(fajlnev))
        }
        function onMovieClipExportFailed() {
            kepkockaJelzes.mutasd(qsTr("Failed to export clip"))
        }
    }

    Text {
        objectName: "videoUnavailableText"
        visible: photoArea.hostViewer.isCurrentVideo
                 && videoLoader.status === Loader.Error
        anchors.centerIn: parent
        text: qsTr("Video playback requires the Qt Multimedia module.")
        color: Theme.mediaOverlayText
        font.pixelSize: Theme.fontSize
    }

    PhotoViewerTiltToolBar {
        id: editorToolBar
        photoArea: photoArea
    }

    // #3166 (a #819 `resizes` ága): a FÉNYKÉP területe a
    // kirajzolt képen belül. Keret-effekt (Border,
    // MuseumMatte, DropShadow, Polaroid, Cinemascope) után a
    // kirajzolt kép már a keretezett kimenet, tehát a relatív
    // koordinátákkal dolgozó rétegek a KERETRE skálázódnának.
    // A leképezést a renderelő méri (`chain_geometry`), a
    // vezérlő `framePlacement`-je adja tovább — a szimmetrikus
    // `(kimenet − forrás) / 2` képlet HAMIS (a DropShadow
    // árnyéka szögfüggő, a Polaroid forgat).
    //
    // Keret nélkül `hely === null`, és a terület pontosan a
    // kirajzolt kép — vagyis a mai viselkedés.
    //: #3741: a `photo` helyett a `photoArea.fokuszKep` a
    //: szülő és a mérce — ez viszi a `cropOverlay`-t és a
    //: `facesOverlay`-t is a fókuszban lévő félre.
    Item {
        id: frameContentArea
        objectName: "frameContentArea"
        parent: photoArea.fokuszKep
        readonly property var hely:
            (typeof editController !== "undefined" && editController
             && editController.framePlacement)
                ? editController.framePlacement : null
        readonly property real kepSzelesseg: photoArea.fokuszKep.paintedWidth
        readonly property real kepMagassag: photoArea.fokuszKep.paintedHeight
        width: kepSzelesseg * (hely ? hely.szelesseg : 1)
        height: kepMagassag * (hely ? hely.magassag : 1)
        x: (photoArea.fokuszKep.width - kepSzelesseg) / 2
           + (hely ? hely.kozepX * kepSzelesseg : kepSzelesseg / 2)
           - width / 2
        y: (photoArea.fokuszKep.height - kepMagassag) / 2
           + (hely ? hely.kozepY * kepMagassag : kepMagassag / 2)
           - height / 2
        //: a renderelő szöge az óramutatóval ellentétes, a QML
        //: `rotation`-je egyező irányú — innen az előjelváltás
        rotation: hely ? -hely.szog : 0
    }

    CropOverlay {
        id: cropOverlay
        parent: frameContentArea
        visible: photoArea.hostEditorPanel.cropActive
        aspectRatio: photoArea.hostEditorPanel.currentAspect
        //: KÖTÉS, nem `anchors.fill`: a tesztek (és a
        //: nagyítás-logika) felülírhatják a méretet
        x: 0
        y: 0
        width: frameContentArea.width
        height: frameContentArea.height
        onVisibleChanged: {
            if (visible) forceActiveFocus()
            else photoArea.hostViewer.forceActiveFocus()
        }
        // Enter-flow: elfogad ÉS következő kép, a vágó-mód
        // megtartásával (sorozat-vágás, UX-alapelv 1)
        onAccepted: function(r) {
            photoArea.hostViewer.applyCrop(true)
            if (visible) forceActiveFocus()
        }
        onCancelled: {
            cropOverlay.resetSelection()
            photoArea.hostEditorPanel.cropActive = false
        }
    }

    // #147/#26: a mentett arc-régiók a kép kirajzolt
    // (letterbox nélküli) területén — a cropOverlay
    // mintájára. Szerkesztő módban (facesEditMode) itt
    // rajzolható/nevezhető/törölhető egy régió.
    FacesOverlay {
        id: facesOverlay
        //: #3166: a keret-leképezés szerinti területben — a
        //: mentett arc-régiók a FÉNYKÉPRE vonatkoznak
        parent: frameContentArea
        visible: (photoArea.hostViewer.facesVisible
                  || photoArea.hostViewer.hasDetectedFaceHitTargets)
                 && !photoArea.hostEditorPanel.cropActive
                 && !photoArea.hostViewer.isCurrentVideo
        x: 0
        y: 0
        width: frameContentArea.width
        height: frameContentArea.height
        faces: photoArea.hostViewer.currentFaces
        showSavedFaces: photoArea.hostViewer.facesVisible
        editMode: photoArea.hostViewer.facesEditMode
        //: #3741: a kijelölt fél fotója — az arcszerkesztés
        //: ennek a sorába ír (`currentFaces` ugyanígy)
        imagePath: photoArea.hostViewer.photosModel && photoArea.hostViewer.aktivSor >= 0
            ? photoArea.hostViewer.photosModel.filePathAt(photoArea.hostViewer.aktivSor) : ""
        onEdited: function(manualAdded) {
            photoArea.hostViewer.facesEditRevision += 1
            if (typeof controller !== "undefined" && controller
                    && photoArea.hostViewer.controllerReady)
                controller.refreshCollections()
            if (manualAdded) {
                if (photoArea.hostViewer.appWindow)
                    photoArea.hostViewer.appWindow.peopleFaceRevision += 1
                photoArea.hostViewer.manualFaceAddRevision += 1
            }
        }
        onManualCancelRequested: photoArea.hostViewer.facesEditMode = false
    }
    Connections {
        target: photoArea.hostViewer
        function onManualFaceAddCancelRequested() {
            facesOverlay.cancelManualAdd()
        }
    }

    PhotoViewerPaintMaskArea {
        id: paintMaskArea
        photoArea: photoArea
    }

    PhotoViewerNeutralPickArea {
        id: neutralPickArea
        photoArea: photoArea
    }

    PhotoViewerEffectColorPickArea {
        id: effectColorPickArea
        photoArea: photoArea
    }

    PhotoViewerRetouchArea {
        id: retouchClickArea
        photoArea: photoArea
    }

    // #445: Vörösszem — kézi kijelölés téglalap-húzással
    // („Click, hold, and drag the mouse around each eye
    // separately to select it. A selection box appears over
    // the area."). A már felvett régiókat a kontroller adja
    // vissza normált [0..1] alakban, ezért a nagyítástól/
    // illesztéstől függetlenül rajzolhatók. A
    // `redeyeHideOutlines` a jegy „Preview changes without
    // square outlines" jelölőnégyzete: csak a RAJZOT tünteti
    // el, a javítást nem.
    //: #3741: a `photo` helyett a `photoArea.fokuszKep` a
    //: szülő — a vörösszem-átfedő a TÉNYLEGESEN szerkesztett
    //: félen jelenik meg.
    Item {
        id: redeyeOverlay
        objectName: "redeyeOverlay"
        parent: photoArea.fokuszKep
        visible: photoArea.hostEditorPanel.redeyeActive
        x: (photoArea.fokuszKep.width
            - photoArea.fokuszKep.paintedWidth) / 2
        y: (photoArea.fokuszKep.height
            - photoArea.fokuszKep.paintedHeight) / 2
        width: photoArea.fokuszKep.paintedWidth
        height: photoArea.fokuszKep.paintedHeight

        Repeater {
            model: photoArea.hostEditorPanel.redeyeHideOutlines
                   ? []
                   : (photoArea.hostEditCtl
                      ? photoArea.hostEditCtl.redeyeRegions : [])
            delegate: Rectangle {
                required property var modelData
                objectName: "redeyeRegionFrame"
                x: modelData.x * redeyeOverlay.width
                y: modelData.y * redeyeOverlay.height
                width: modelData.w * redeyeOverlay.width
                height: modelData.h * redeyeOverlay.height
                color: "transparent"
                border.width: 1
                border.color: Theme.selectionBlue
            }
        }

        // #900: az `editpanel/redselection` a téglalapon
        // KÍVÜLI területet ugyanazzal a
        // `negativemode 8f2f2f2f` értékkel sötétíti, mint a
        // vágó. Csak húzás közben — a már rögzített régiók
        // körül nincs sötétítés, azokat csak keret jelöli.
        SelectionDim {
            objectName: "redeyeSelectionDim"
            active: redeyeDragArea.dragging
                    && !photoArea.hostEditorPanel.redeyeHideOutlines
            selX: redeyeDragArea.selX
            selY: redeyeDragArea.selY
            selW: redeyeDragArea.selW
            selH: redeyeDragArea.selH
        }

        // az ÉPP húzott téglalap (még nincs a pufferben)
        Rectangle {
            objectName: "redeyeDragRect"
            visible: redeyeDragArea.dragging
                     && !photoArea.hostEditorPanel.redeyeHideOutlines
            x: redeyeDragArea.selX
            y: redeyeDragArea.selY
            width: redeyeDragArea.selW
            height: redeyeDragArea.selH
            color: "transparent"
            border.width: 1
            border.color: Theme.selectionBlue
        }

        // #891: a húzás közben lenyomott módosító a KÉP
        // saját arányára (Shift), annak 4/3-ára (Ctrl) vagy
        // 3/2-ére (Alt) kényszeríti a téglalapot — Alt üt
        // Ctrl-t, Ctrl üt Shiftet. A `selX/selY/selW/selH` a
        // MÁR KÉNYSZERÍTETT téglalap, ezt rajzoljuk és ezt
        // adjuk át felengedéskor. Minden lépés újraszámol,
        // ezért a billentyű felengedése azonnal felszabadít.
        MouseArea {
            id: redeyeDragArea
            objectName: "redeyeDragArea"
            anchors.fill: parent
            enabled: photoArea.hostEditorPanel.redeyeActive
            //: #604: a keret fölött a kurzor JELZI, hogy
            //: kattintva törölhető — az eredeti mindhárom
            //: útmutatója ezt ígéri. Húzás közben marad a
            //: célkereszt, különben a kurzor a keret fölé
            //: érve váltogatna.
            cursorShape: (!dragging && keretenAll)
                         ? Qt.PointingHandCursor
                         : Qt.CrossCursor
            hoverEnabled: photoArea.hostEditorPanel.redeyeActive
            property bool keretenAll: false
            property bool dragging: false
            property real startX: 0
            property real startY: 0
            property real selX: 0
            property real selY: 0
            property real selW: 0
            property real selH: 0
            function frissit(mouse) {
                var r = AranyKenyszer.huzottTeglalap(
                    startX, startY, mouse.x, mouse.y,
                    width, height,
                    mouse.modifiers & Qt.ShiftModifier,
                    mouse.modifiers & Qt.ControlModifier,
                    mouse.modifiers & Qt.AltModifier)
                selX = r.x; selY = r.y
                selW = r.width; selH = r.height
            }
            onPressed: function(mouse) {
                dragging = true
                startX = mouse.x; startY = mouse.y
                selX = mouse.x; selY = mouse.y
                selW = 0; selH = 0
            }
            onPositionChanged: function(mouse) {
                if (!dragging) {
                    keretenAll = (width > 0 && height > 0
                        && typeof editController !== "undefined" && editController
                        && editController.redeyeRegionHitAt(
                            mouse.x / width, mouse.y / height))
                    return
                }
                frissit(mouse)
            }
            onExited: keretenAll = false
            onReleased: function(mouse) {
                dragging = false
                if (width <= 0 || height <= 0) return
                frissit(mouse)
                //: #604: a nulla méretű kijelölés — vagyis a
                //: puszta KATTINTÁS — a kereten TÖRLÉS, azon
                //: kívül továbbra is néma no-op. A húzás
                //: változatlanul új régiót ad, akkor is, ha
                //: egy meglévő kereten indul.
                if (selW <= 0 || selH <= 0) {
                    if (typeof editController !== "undefined" && editController) {
                        editController.removeRedeyeRegionAt(
                            mouse.x / width, mouse.y / height)
                        keretenAll = editController
                            .redeyeRegionHitAt(
                                mouse.x / width, mouse.y / height)
                    }
                    return
                }
                if (typeof editController !== "undefined" && editController)
                    editController.addRedeyeRegion(
                        selX / width, selY / height,
                        selW / width, selH / height)
            }
        }
    }
    //: #3741: a `photo` helyett a `photoArea.fokuszKep` a
    //: szülő — a szöveg-elhelyezés a TÉNYLEGESEN szerkesztett
    //: félen megy.
    MouseArea {
        id: textClickArea
        objectName: "textClickArea"
        parent: photoArea.fokuszKep
        visible: photoArea.hostEditorPanel.textActive
        enabled: photoArea.hostEditorPanel.textActive
        x: (photoArea.fokuszKep.width
            - photoArea.fokuszKep.paintedWidth) / 2
        y: (photoArea.fokuszKep.height
            - photoArea.fokuszKep.paintedHeight) / 2
        width: photoArea.fokuszKep.paintedWidth
        height: photoArea.fokuszKep.paintedHeight
        cursorShape: Qt.CrossCursor
        onClicked: function(mouse) {
            if (width <= 0 || height <= 0) return
            if (typeof editController !== "undefined" && editController)
                editController.previewNewTextPlacement(
                    mouse.x / width, mouse.y / height)
        }
    }
    // #4545: a mentett szövegdobozok áttetsző, kattintható
    // találati területei a raszter-előnézet fölött vannak.
    // A betűt a szolgáltató rajzolja; itt csak a doboz
    // hozzávetőleges QML-méretét használjuk kijelöléshez.
    Repeater {
        id: textOverlaySelector
        parent: photoArea.fokuszKep
        model: photoArea.hostEditorPanel.textActive && photoArea.hostEditCtl
               ? photoArea.hostEditCtl.textOverlayItems : []
        delegate: Item {
            required property var modelData
            objectName: "textOverlaySelector_" + modelData.index
            z: 1
            width: Math.max(16, hitText.implicitWidth + 12)
            height: Math.max(16, hitText.implicitHeight + 12)
            x: (photoArea.fokuszKep.width
                - photoArea.fokuszKep.paintedWidth) / 2
               + photoArea.fokuszKep.paintedWidth * modelData.x - 6
            y: (photoArea.fokuszKep.height
                - photoArea.fokuszKep.paintedHeight) / 2
               + photoArea.fokuszKep.paintedHeight * modelData.y
               - hitText.implicitHeight - 6
            rotation: modelData.rotation * 180 / Math.PI
            transformOrigin: Item.BottomLeft

            Text {
                id: hitText
                anchors.centerIn: parent
                text: modelData.content
                font.family: modelData.font
                font.pixelSize: Math.max(1, Math.round(
                    modelData.size * photoArea.fokuszKep.paintedHeight
                    / 360))
                color: "transparent"
            }
            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.color: "#4a90e2"
                border.width: 1
                visible: photoArea.hostEditCtl
                         && modelData.index
                            === photoArea.hostEditCtl.textSelectedIndex
            }
            MouseArea {
                objectName: "textOverlayHitTarget_" + modelData.index
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: containsMouse ? Qt.IBeamCursor : Qt.ArrowCursor
                onClicked: {
                    if (typeof editController !== "undefined" && editController)
                        editController.selectTextOverlay(modelData.index)
                }
            }
        }
    }
}
