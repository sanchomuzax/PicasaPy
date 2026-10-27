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
        Image {
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
        Image {
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

    //: #3924, „⛳ A Kiegyenesítés négyzethálója”:
    //: a csempézett rács a kép fölött áll, a kép forgása alatt.
    //: A becsomagolt 44×44-es mintát az Image.Tile
    //: változatlan logikai képpontméretben ismétli a képre.
    Item {
        id: straightenGridOverlay
        objectName: "straightenGridOverlay"
        // A közös, forgatatlan szülőben a Qt clip mind a négy
        // egész képernyőszélt azonosan raszterezi; a rács
        // így a 90°-os képeknél sem veszít el perempixelt.
        parent: photoArea
        z: 1
        scale: 1
        rotation: 0
        clip: true
        visible: photoArea.hostEditorPanel.tiltActive
                 && photoArea.hostEditorPanel.activeTab === 0
                 && !photoArea.hostViewer.isCurrentVideo

        property int racsKezdoX: 0
        property int racsKezdoY: 0
        property int vagasJelenetX: 0
        property int vagasJelenetY: 0
        property real gombparBal: 0
        property real gombparFelso: 0
        property real gombparJobb: 0
        property real gombparAlso: 0
        property bool gombparMaszkAktiv: false
        property bool elsoKirajzolasUtaniMaszkFrissult: false

        function frissitGombparMaszk() {
            if (!editorToolBar.visible)
            {
                gombparMaszkAktiv = false
                return
            }

            var gombok = [
                editorToolBar.cancelButtonItem,
                editorToolBar.applyButtonItem,
            ]
            var xek = []
            var yek = []
            for (var i = 0; i < gombok.length; ++i) {
                var gomb = gombok[i]
                var sarkok = [
                    gomb.mapToItem(straightenGridOverlay, 0, 0),
                    gomb.mapToItem(straightenGridOverlay,
                                   gomb.width, 0),
                    gomb.mapToItem(straightenGridOverlay,
                                   0, gomb.height),
                    gomb.mapToItem(straightenGridOverlay,
                                   gomb.width, gomb.height),
                ]
                for (var j = 0; j < sarkok.length; ++j) {
                    xek.push(sarkok[j].x)
                    yek.push(sarkok[j].y)
                }
            }

            var bal = Math.min.apply(null, xek)
            var fent = Math.min.apply(null, yek)
            var jobb = Math.max.apply(null, xek)
            var lent = Math.max.apply(null, yek)
            gombparBal = Math.max(0, Math.min(width, bal))
            gombparFelso = Math.max(0, Math.min(height, fent))
            gombparJobb = Math.max(0, Math.min(width, jobb))
            gombparAlso = Math.max(0, Math.min(height, lent))
            gombparMaszkAktiv = gombparJobb > gombparBal
                && gombparAlso > gombparFelso
        }

        function racsSzeletX(szeletX) {
            var jelenetX = vagasJelenetX + szeletX
            return racsKezdoX
                + Math.floor((jelenetX - racsKezdoX) / 44) * 44
                - jelenetX
        }

        function racsSzeletY(szeletY) {
            var jelenetY = vagasJelenetY + szeletY
            return racsKezdoY
                + Math.floor((jelenetY - racsKezdoY) / 44) * 44
                - jelenetY
        }

        function frissitGeometria() {
            var kep = photoArea.fokuszKep
            if (kep.paintedWidth <= 0 || kep.paintedHeight <= 0)
                return

            var kozep = kep.mapToItem(
                null, kep.width / 2, kep.height / 2)
            var nagyitas = Math.abs(kep.scale)
            var fordult = kep.iniSteps % 2 !== 0
            var kepSzel = (fordult
                ? kep.paintedHeight : kep.paintedWidth) * nagyitas
            var kepMag = (fordult
                ? kep.paintedWidth : kep.paintedHeight) * nagyitas
            var bal = Math.floor(kozep.x - kepSzel / 2)
            var jobb = Math.floor(kozep.x + kepSzel / 2)
            var fent = Math.floor(kozep.y - kepMag / 2)
            var lent = Math.floor(kozep.y + kepMag / 2)
            var helyiKezdo = parent.mapFromItem(
                null, bal, fent)

            width = jobb - bal
            height = lent - fent
            x = helyiKezdo.x
            y = helyiKezdo.y
            vagasJelenetX = bal
            vagasJelenetY = fent

            var teruletKozep = photoArea.mapToItem(
                null, photoArea.width / 2, photoArea.height / 2)
            racsKezdoX = Math.trunc(teruletKozep.x - 249)
            racsKezdoY = Math.trunc(teruletKozep.y - 153)
            Qt.callLater(frissitGombparMaszk)
        }

        onVisibleChanged: {
            if (visible) {
                elsoKirajzolasUtaniMaszkFrissult = false
                Qt.callLater(frissitGeometria)
            }
        }
        Component.onCompleted: Qt.callLater(frissitGeometria)

        //: Négy, egymást nem fedő csempézett rész alkotja a
        //: rácsot. A középső bal/jobb résszel a teljes gombpár
        //: téglalapja marad üres; a csúszkasáv fölött továbbra
        //: is látszik a rács. A QtQuick.Effects nem fut minden
        //: célgépen, ezért a kivágás egyszerű QtQuick-clip.
        // Felső sáv: a gombpár fölötti teljes képterület.
        Item {
            x: 0
            y: 0
            width: straightenGridOverlay.width
            height: straightenGridOverlay.gombparMaszkAktiv
                    ? straightenGridOverlay.gombparFelso
                    : straightenGridOverlay.height
            clip: true
            visible: width > 0 && height > 0
            Image {
                objectName: "straightenGridImage"
                x: straightenGridOverlay.racsSzeletX(parent.x)
                y: straightenGridOverlay.racsSzeletY(parent.y)
                width: parent.width + 88
                height: parent.height + 88
                source: "../../assets/tools/straighten_grid.png"
                sourceSize: Qt.size(44, 44)
                fillMode: Image.Tile
                horizontalAlignment: Image.AlignLeft
                verticalAlignment: Image.AlignTop
                smooth: false
                cache: false
                asynchronous: false
            }
        }
        // A gombok bal oldalán megmarad a háló, a résen nem.
        Item {
            x: 0
            y: straightenGridOverlay.gombparFelso
            width: straightenGridOverlay.gombparBal
            height: straightenGridOverlay.gombparAlso
                    - straightenGridOverlay.gombparFelso
            clip: true
            visible: straightenGridOverlay.gombparMaszkAktiv
                     && width > 0 && height > 0
            Image {
                x: straightenGridOverlay.racsSzeletX(parent.x)
                y: straightenGridOverlay.racsSzeletY(parent.y)
                width: parent.width + 88
                height: parent.height + 88
                source: "../../assets/tools/straighten_grid.png"
                sourceSize: Qt.size(44, 44)
                fillMode: Image.Tile
                horizontalAlignment: Image.AlignLeft
                verticalAlignment: Image.AlignTop
                smooth: false
                cache: false
                asynchronous: false
            }
        }
        // A gombok jobb oldalán megmarad a háló.
        Item {
            x: straightenGridOverlay.gombparJobb
            y: straightenGridOverlay.gombparFelso
            width: straightenGridOverlay.width
                    - straightenGridOverlay.gombparJobb
            height: straightenGridOverlay.gombparAlso
                    - straightenGridOverlay.gombparFelso
            clip: true
            visible: straightenGridOverlay.gombparMaszkAktiv
                     && width > 0 && height > 0
            Image {
                x: straightenGridOverlay.racsSzeletX(parent.x)
                y: straightenGridOverlay.racsSzeletY(parent.y)
                width: parent.width + 88
                height: parent.height + 88
                source: "../../assets/tools/straighten_grid.png"
                sourceSize: Qt.size(44, 44)
                fillMode: Image.Tile
                horizontalAlignment: Image.AlignLeft
                verticalAlignment: Image.AlignTop
                smooth: false
                cache: false
                asynchronous: false
            }
        }
        // Alsó sáv: a gombpár alatti teljes képterület.
        Item {
            x: 0
            y: straightenGridOverlay.gombparMaszkAktiv
               ? straightenGridOverlay.gombparAlso : 0
            width: straightenGridOverlay.width
            height: straightenGridOverlay.gombparMaszkAktiv
                    ? straightenGridOverlay.height
                      - straightenGridOverlay.gombparAlso
                    : 0
            clip: true
            visible: width > 0 && height > 0
            Image {
                x: straightenGridOverlay.racsSzeletX(parent.x)
                y: straightenGridOverlay.racsSzeletY(parent.y)
                width: parent.width + 88
                height: parent.height + 88
                source: "../../assets/tools/straighten_grid.png"
                sourceSize: Qt.size(44, 44)
                fillMode: Image.Tile
                horizontalAlignment: Image.AlignLeft
                verticalAlignment: Image.AlignTop
                smooth: false
                cache: false
                asynchronous: false
            }
        }
        Connections {
            target: photoArea.fokuszKep
            function frissit() {
                Qt.callLater(straightenGridOverlay.frissitGeometria)
            }
            function onXChanged() { frissit() }
            function onYChanged() { frissit() }
            function onWidthChanged() { frissit() }
            function onHeightChanged() { frissit() }
            function onPaintedWidthChanged() { frissit() }
            function onPaintedHeightChanged() { frissit() }
            function onScaleChanged() { frissit() }
            function onRotationChanged() { frissit() }
            function onIniStepsChanged() { frissit() }
        }
        Connections {
            target: photoArea
            function frissit() {
                Qt.callLater(straightenGridOverlay.frissitGeometria)
            }
            function onXChanged() { frissit() }
            function onYChanged() { frissit() }
            function onWidthChanged() { frissit() }
            function onHeightChanged() { frissit() }
        }
        Connections {
            target: photoArea.parent
            function frissit() {
                Qt.callLater(straightenGridOverlay.frissitGeometria)
            }
            function onXChanged() { frissit() }
            function onYChanged() { frissit() }
            function onWidthChanged() { frissit() }
            function onHeightChanged() { frissit() }
        }
        Connections {
            target: photoArea.hostViewer
            function frissit() {
                Qt.callLater(straightenGridOverlay.frissitGeometria)
            }
            function onXChanged() { frissit() }
            function onYChanged() { frissit() }
            function onWidthChanged() { frissit() }
            function onHeightChanged() { frissit() }
        }
        Connections {
            target: editorToolBar
            function frissit() {
                Qt.callLater(
                    straightenGridOverlay.frissitGombparMaszk)
            }
            function onXChanged() { frissit() }
            function onYChanged() { frissit() }
            function onWidthChanged() { frissit() }
            function onHeightChanged() { frissit() }
            function onScaleChanged() { frissit() }
            function onRotationChanged() { frissit() }
            function onVisibleChanged() { frissit() }
        }
        // A Row gyermekei az első megnyitás elrendezési
        // körében kapják meg a végleges x/y-t. Az első
        // animációs/layout kör után olvassuk ki a gombpár
        // tényleges helyét, így a háló első kirajzolása sem
        // régi koordinátával indul.
        Connections {
            target: straightenGridOverlay.Window.window
            function onAfterAnimating() {
                if (straightenGridOverlay.visible
                        && editorToolBar.visible
                        && !straightenGridOverlay
                             .elsoKirajzolasUtaniMaszkFrissult) {
                    straightenGridOverlay
                        .elsoKirajzolasUtaniMaszkFrissult = true
                    straightenGridOverlay.frissitGombparMaszk()
                }
            }
        }
        Connections {
            target: editorToolBar.applyButtonItem
            function frissit() {
                Qt.callLater(
                    straightenGridOverlay.frissitGombparMaszk)
            }
            function onXChanged() { frissit() }
            function onYChanged() { frissit() }
            function onWidthChanged() { frissit() }
            function onHeightChanged() { frissit() }
        }
        Connections {
            target: editorToolBar.cancelButtonItem
            function frissit() {
                Qt.callLater(
                    straightenGridOverlay.frissitGombparMaszk)
            }
            function onXChanged() { frissit() }
            function onYChanged() { frissit() }
            function onWidthChanged() { frissit() }
            function onHeightChanged() { frissit() }
        }
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
    //: #3755: a GPU-réteg a `fokuszKeret` geometriáját és
    //: VÁGÁSÁT követő tartóban ül. A `photoArea` közvetlen
    //: gyerekeként nagyításnál (ab, bal fókusz, zoom 0,8)
    //: átlógott a másik fél képére, mert a keret `clip`-je
    //: csak a keret SAJÁT gyerekeit vágja. Egyképes nézetben
    //: a `fokuszKeret` a `photoKeret` (a teljes `photoArea`,
    //: `clip: false`), tehát ott semmi nem változik.
    Item {
        id: gpuFinetuneVago
        objectName: "gpuFinetuneVago"
        x: photoArea.fokuszKeret.x
        y: photoArea.fokuszKeret.y
        width: photoArea.fokuszKeret.width
        height: photoArea.fokuszKeret.height
        clip: photoArea.fokuszKeret.clip
        GpuPointFilterPreview {
            id: gpuFinetunePreview
            objectName: "gpuFinetunePreview"
            // #415: NEM `anchors.fill: photo` — az a `photo`
            // TELJES befoglaló dobozára igazítana (a
            // rendelkezésre álló terület, `photo.width`/
            // `photo.height`), nem a `PreserveAspectFit`
            // fillMode által ténylegesen kirajzolt, letterboxolt
            // téglalapra. Álló képnél a doboz szélesebb, mint a
            // kirajzolt kép — a húzás alatt ez a réteg (a
            // `fokuszKep` fölött) a doboz teljes szélességére
            // nyúlt, majd
            // elrejtésekor (elengedéskor) a helyesen illesztett
            // `photo` vált újra láthatóvá: ez okozta a
            // bejelentett "kiugrást". A helyes geometria a
            // `cropOverlay`/`facesOverlay` mintáját követi —
            // `paintedWidth`/`paintedHeight`, középre igazítva.
            //: #3755: fixen a `photo`-ra volt kötve — bal
            //: fókusznál (`photoArea.fokuszKep === photoElotte`)
            //: ezért a jobb, NEM kijelölt félre rajzolt a húzás
            //: alatt. A `fokuszKeret`/`fokuszKep` ugyanaz a
            //: leképezés, mint a `frameContentArea`/`cropOverlay`
            //: párjáé fent. Az `x`/`y` a `gpuFinetuneVago`-hoz
            //: (= a `fokuszKeret`-hez) relatív.
            x: photoArea.fokuszKep.x
               + (photoArea.fokuszKep.width
                  - photoArea.fokuszKep.paintedWidth) / 2
            y: photoArea.fokuszKep.y
               + (photoArea.fokuszKep.height
                  - photoArea.fokuszKep.paintedHeight) / 2
            width: photoArea.fokuszKep.paintedWidth
            height: photoArea.fokuszKep.paintedHeight
            rotation: photoArea.fokuszKep.rotation
            scale: photoArea.fokuszKep.scale
            transformOrigin: Item.Center
            // #402: shader-hibánál (shaderOk=false) némán a
            // CPU-előnézet marad
            visible: photoArea.hostViewer.gpuFinetuneActive && photoArea.hostViewer.gpuFinetuneEligible
                     && photoArea.hostViewer.gpuFinetunePointSafe
                     && gpuFinetunePreview.shaderOk
            sourceItem: gpuPrefixImage
            lutItem: gpuLutImage
            satGain: 1.0
            bwMix: 0.0
        }
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
        color: "#e8e8e8"
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
        color: "#e8e8e8"
        font.pixelSize: Theme.fontSize
    }

    // vágó-overlay a kép TÉNYLEGESEN kirajzolt (letterbox
    // nélküli) területén. Enter: elfogad + következő kép a
    // vágó-mód megtartásával (sorozat-vágás, UX-alapelv 1);
    // Esc: kilép a vágásból. MVP-korlát: ini-forgatott
    // (rotate=) képnél a koordináták a megjelenített térben
    // értendők — a forgatás+vágás kombináció a #21-ben pontosodik.
    // #3123: az eszköz-sáv a KÉP FÖLÖTT lebeg — az
    // eredetiben az Alkalmaz/Mégse pár nem a bal panelben ül
    // (`editpanel/tool_container: editpanel/preview`,
    // `m_centerX`, `YConstraint 1, 1, -10`). A gombok a
    // korábbi panel-gombok OBJEKTUMNEVÉT viszik tovább, hogy
    // a rájuk épülő működés (és annak ellenőrzése) ne
    // szakadjon meg.
    //: #3741: a `photo` helyett a `photoArea.fokuszKep` a
    //: szülő — a sáv a TÉNYLEGESEN szerkesztett félre kerül,
    //: bal fókusznál a `photoElotte`-ra (ld. a `fokuszKep`
    //: docsztringjét a `photo` alatt).
    EditorToolBar {
        id: editorToolBar
        objectName: "editorToolBar"
        textEntryHasFocus: photoArea.hostViewer.textEntryHasFocus
        parent: photoArea
        z: 20
        //: #3320: a sáv KIZÁRÓLAG a kiegyenesítésé. A
        //: `.tre` a `tool_container`-t a
        //: `#---Straighen Overlay---` szakaszfejléc alá
        //: teszi (`:1038`–`:1052`); a másik négy eszköz
        //: párja a SAJÁT paneljében ül (`crop_well`,
        //: `retouch_well`, `redeye_well`).
        tool: (photoArea.hostEditorPanel.tiltActive
               && photoArea.hostEditorPanel.activeTab === 0) ? "tilt" : ""
        //: a kiegyenesítés Alkalmaz gombja mindig aktív —
        //: a döntés értéke már ki van írva (#72)
        applyEnabled: true
        //: #3234: a döntés-csúszka tartománya — −1…1
        //: Picasa-egység (±11,5°)
        csuszkaMin: -1
        csuszkaMax: 1
        //: húzás közben ÉLŐ előnézet, ini-mentés nélkül
        //: (#72); a programozott szinkron (nyitás, lapozás)
        //: nem vált ki előnézetet (#131)
        onCsuszkaMozgott: (ertek) => {
            if (typeof editController !== "undefined"
                    && photoArea.hostEditorPanel.tiltActive && !photoArea.hostViewer.tiltSzinkronFut)
                editController.previewTilt(ertek)
        }
        //: #4058: az elengedés csak az előnézetet frissíti;
        //: menteni az Alkalmaz gomb fog.
        onCsuszkaElengedve: (ertek) => {
            if (typeof editController !== "undefined"
                    && photoArea.hostEditorPanel.tiltActive)
                editController.previewTilt(ertek)
        }
        //: A sáv a kép forgatása fölötti, forgatatlan rétegen
        //: marad. A képernyőn látható képrész négy sarkát
        //: leképezzük a forgatás utáni befoglaló téglalaphoz;
        //: a sáv közepe ehhez igazodik, az alsó rés 10×képskála.
        readonly property point kepernyoKozep:
        {
            var kep = photoArea.fokuszKep
            var kepBal = (kep.width - kep.paintedWidth) / 2
            var kepFelso = (kep.height - kep.paintedHeight) / 2
            var kepJobb = kepBal + kep.paintedWidth
            var kepAlso = kepFelso + kep.paintedHeight
            var sarkok = [
                kep.mapToItem(null, kepBal, kepFelso),
                kep.mapToItem(null, kepJobb, kepFelso),
                kep.mapToItem(null, kepBal, kepAlso),
                kep.mapToItem(null, kepJobb, kepAlso),
            ]
            var minX = Math.min(sarkok[0].x, sarkok[1].x,
                                sarkok[2].x, sarkok[3].x)
            var maxX = Math.max(sarkok[0].x, sarkok[1].x,
                                sarkok[2].x, sarkok[3].x)
            var maxY = Math.max(sarkok[0].y, sarkok[1].y,
                                sarkok[2].y, sarkok[3].y)
            var kepSkala = kep.scale
            //: A mapToItem() a transzformált sarkokat
            //: visszaadja, de a QML-kötés nem iratkozik fel
            //: a belső x/y/méret/scale/rotation olvasásokra.
            //: A nullával szorzott függőség frissíti a sávot
            //: lapozáskor, nagyításkor és átméretezéskor is.
            var fuggoseg = (kep.x + kep.y + kep.width
                + kep.height + kep.paintedWidth
                + kep.paintedHeight + kep.scale + kep.rotation) * 0
            return Qt.point(
                (minX + maxX) / 2 + fuggoseg,
                maxY - kepSkala * (height / 2 + 10)
                    + fuggoseg)
        }
        readonly property point szuloKozep:
            parent.mapFromItem(
                null, kepernyoKozep.x, kepernyoKozep.y)
        x: Math.round(szuloKozep.x - width / 2)
        y: Math.round(szuloKozep.y - height / 2)
        rotation: 0
        scale: photoArea.fokuszKep.scale
        transformOrigin: Item.Center
        onApplyClicked: {
            //: #4058: a Kiegyenesítés egyetlen mentése az
            //: Alkalmazás. Változatlan értéknél ne keletkezzen
            //: fölösleges réteg vagy Visszavonás-lépés.
            if (tool === "tilt") {
                if (typeof editController !== "undefined"
                        && editorToolBar.csuszkaErtek
                        !== photoArea.hostViewer.tiltErtekNyitaskor)
                    editController.setTilt(
                        editorToolBar.csuszkaErtek)
                photoArea.hostViewer.tiltAlkalmazasFut = true
                photoArea.hostEditorPanel.tiltActive = false
                photoArea.hostViewer.tiltAlkalmazasFut = false
            }
        }
        onCancelClicked: {
            //: #4058: a Mégse a nyitáskori mentett láncot
            //: rendereli újra; a mentett lánc és az előzmény
            //: addig változatlan maradt.
            if (tool === "tilt")
                photoArea.hostEditorPanel.tiltActive = false
        }
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
            if (typeof controller !== "undefined"
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

    // #445: a retusálás a Picasa súgószövege szerinti,
    // KÉTKATTINTÁSOS, irányított klónozás — 1. kattintás a
    // CÉL kijelölése, egérmozgatás a FORRÁS élő előnézete,
    // 2. kattintás véglegesíti. `Ctrl`+húzás eközben a
    // meglévő nagyítás-pásztázó (`viewer.panX`/`panY`/
    // `clampPan()`, ld. lent a `viewerPanArea`-t) állapotára
    // ül rá, hogy zoomolt nézetben kattintás nélkül lehessen
    // odébb húzni a képet.
    // #464: a „semleges szín" pipetta — amíg aktív, a képre
    // kattintás színmintát vesz (nem navigál). A kattintás
    // helyét a KIRAJZOLT képhez képest normálva adjuk át, így
    // a nagyítástól/illesztéstől független.
    // #3541: az ECSET csak a Vámpírszemnél aktív; a négy
    // teljes képre ható effekt nem festhető. A mutató KÖR alakú
    // (`thumbui/circlecursor`, mérve), az átmérőjét a panel
    // csúszkája adja; a vonás a KIRAJZOLT képhez normálva megy
    // a vezérlőnek, tehát a nagyítástól független.
    //: #3741: a `photo` helyett a `photoArea.fokuszKep` a
    //: szülő — a festés a TÉNYLEGESEN szerkesztett félen megy.
    MouseArea {
        id: paintMaskArea
        objectName: "paintMaskArea"
        parent: photoArea.fokuszKep
        z: 5
        readonly property bool aktiv:
            (typeof editController !== "undefined" && editController
             && editController.paintMaskSupported !== undefined)
                ? editController.paintMaskSupported : false
        visible: paintMaskArea.aktiv
        enabled: paintMaskArea.aktiv
        hoverEnabled: true
        x: (photoArea.fokuszKep.width
            - photoArea.fokuszKep.paintedWidth) / 2
        y: (photoArea.fokuszKep.height
            - photoArea.fokuszKep.paintedHeight) / 2
        width: photoArea.fokuszKep.paintedWidth
        height: photoArea.fokuszKep.paintedHeight
        //: a rendszer-kurzort elrejtjük: a KÖR maga a mutató
        cursorShape: Qt.BlankCursor

        function fess(pont) {
            if (typeof editController === "undefined" || !editController) return
            editController.paintStroke(
                pont.x / Math.max(1, width),
                pont.y / Math.max(1, height))
        }
        onPressed: function (eger) { paintMaskArea.fess(eger) }
        onPositionChanged: function (eger) {
            if (eger.buttons) paintMaskArea.fess(eger)
        }

        //: a kör alakú mutató — a sugár a kép RÖVIDEBB
        //: oldalához mért arány (a vezérlő így számol)
        Rectangle {
            objectName: "paintMaskCursor"
            visible: paintMaskArea.containsMouse
            readonly property real sugar:
                ((typeof editController !== "undefined" && editController
                  && editController.paintBrushRatio !== undefined)
                    ? editController.paintBrushRatio : 0.03)
                * Math.min(paintMaskArea.width,
                           paintMaskArea.height)
            width: 2 * sugar
            height: 2 * sugar
            radius: sugar
            x: paintMaskArea.mouseX - sugar
            y: paintMaskArea.mouseY - sugar
            color: "transparent"
            border.width: 1
            border.color: (typeof editController !== "undefined"
                           && editController && editController.paintEraser)
                ? "#ff6666" : "#ffffff"
        }
    }

    //: #3741: a `photo` helyett a `photoArea.fokuszKep` a
    //: szülő — a pipetta a TÉNYLEGESEN szerkesztett félen ül.
    MouseArea {
        id: neutralPickArea
        objectName: "neutralPickArea"
        parent: photoArea.fokuszKep
        visible: photoArea.hostEditorPanel.neutralPickerActive
        enabled: photoArea.hostEditorPanel.neutralPickerActive
        x: (photoArea.fokuszKep.width
            - photoArea.fokuszKep.paintedWidth) / 2
        y: (photoArea.fokuszKep.height
            - photoArea.fokuszKep.paintedHeight) / 2
        width: photoArea.fokuszKep.paintedWidth
        height: photoArea.fokuszKep.paintedHeight
        cursorShape: Qt.CrossCursor
        onClicked: function(mouse) {
            if (typeof editController === "undefined" || !editController) return
            editController.pickNeutralColor(
                mouse.x / Math.max(1, width),
                mouse.y / Math.max(1, height))
            photoArea.hostEditorPanel.neutralPickerActive = false
        }
    }

    //: #5674: az effekt-színparaméter pipettája: ugyanazon a
    //: KIRAJZOLT képen mintavesz, mint a semleges szín pipettája.
    //: A szín a cél-paraméter sorába megy, és a legutóbbi színek
    //: közé is bekerül (ugyanaz az út, mint a színminta).
    MouseArea {
        id: effectColorPickArea
        objectName: "effectColorPickArea"
        parent: photoArea.fokuszKep
        visible: photoArea.hostEditorPanel.effectColorPickerTarget >= 0
        enabled: photoArea.hostEditorPanel.effectColorPickerTarget >= 0
        x: (photoArea.fokuszKep.width
            - photoArea.fokuszKep.paintedWidth) / 2
        y: (photoArea.fokuszKep.height
            - photoArea.fokuszKep.paintedHeight) / 2
        width: photoArea.fokuszKep.paintedWidth
        height: photoArea.fokuszKep.paintedHeight
        cursorShape: Qt.CrossCursor
        onClicked: function(mouse) {
            if (typeof editController === "undefined" || !editController) return
            var hex = editController.pickEffectColor(
                mouse.x / Math.max(1, width),
                mouse.y / Math.max(1, height))
            if (hex !== "") {
                photoArea.hostEditorPanel.updateParamValue(
                    photoArea.hostEditorPanel.effectColorPickerTarget, hex)
                editController.rememberPickerColor(hex)
            }
            photoArea.hostEditorPanel.effectColorPickerTarget = -1
        }
    }

    //: #3741: a `photo` helyett a `photoArea.fokuszKep` a
    //: szülő — a retusálás a TÉNYLEGESEN szerkesztett félen
    //: megy, ne a másik (nem kijelölt) képen.
    MouseArea {
        id: retouchClickArea
        objectName: "retouchClickArea"
        parent: photoArea.fokuszKep
        visible: photoArea.hostEditorPanel.retouchActive
        enabled: photoArea.hostEditorPanel.retouchActive
        hoverEnabled: true
        x: (photoArea.fokuszKep.width
            - photoArea.fokuszKep.paintedWidth) / 2
        y: (photoArea.fokuszKep.height
            - photoArea.fokuszKep.paintedHeight) / 2
        width: photoArea.fokuszKep.paintedWidth
        height: photoArea.fokuszKep.paintedHeight
        // A Picasa a `thumbui/circlecursor` elemmel helyettesíti
        // a rendszermutatót. A kör mérete egyezzen a retusáló
        // patch tényleges, modellből kapott sugarával.
        cursorShape: ctrlPanning ? Qt.CrossCursor : Qt.BlankCursor
        property bool ctrlPanning: false
        property real panLastX: 0
        property real panLastY: 0
        property real retouchTargetX: 0
        property real retouchTargetY: 0
        property real retouchSourceX: 0
        property real retouchSourceY: 0
        property bool hasRetouchTarget: false
        property bool hasRetouchSource: false
        property bool committingRetouchPatch: false
        readonly property real brushRadius:
            (typeof editController !== "undefined" && editController
             && editController.retouchBrushRadiusRatio !== undefined
                ? editController.retouchBrushRadiusRatio : 0)
            * Math.min(width, height)

        function torolRetouchJeloleseket() {
            hasRetouchTarget = false
            hasRetouchSource = false
        }

        onVisibleChanged: {
            if (!visible) {
                torolRetouchJeloleseket()
                ctrlPanning = false
            }
        }

        Connections {
            target: photoArea.hostEditorPanel
            function onRetouchPatchPendingChanged() {
                if (!photoArea.hostEditorPanel.retouchPatchPending
                        && !retouchClickArea.committingRetouchPatch)
                    retouchClickArea.torolRetouchJeloleseket()
            }
            function onRetouchRegionCountChanged() {
                if (photoArea.hostEditorPanel.retouchRegionCount === 0
                        && !photoArea.hostEditorPanel.retouchPatchPending)
                    retouchClickArea.torolRetouchJeloleseket()
            }
        }
        onPressed: function(mouse) {
            if (mouse.modifiers & Qt.ControlModifier) {
                ctrlPanning = true
                panLastX = mouse.x; panLastY = mouse.y
            }
        }
        onPositionChanged: function(mouse) {
            if (width <= 0 || height <= 0) return
            if (ctrlPanning) {
                photoArea.hostViewer.panX += mouse.x - panLastX
                photoArea.hostViewer.panY += mouse.y - panLastY
                panLastX = mouse.x; panLastY = mouse.y
                photoArea.hostViewer.clampPan()
                return
            }
            if (typeof editController !== "undefined"
                    && editController.retouchPatchPending)
                editController.previewRetouchSource(
                    mouse.x / width, mouse.y / height)
        }
        onReleased: function(mouse) { ctrlPanning = false }
        onClicked: function(mouse) {
            if (width <= 0 || height <= 0) return
            // Ctrl+húzás UTÁNi felengedés is "clicked"-et vált
            // ki QML-ben — ez NEM patch-kattintás
            if (mouse.modifiers & Qt.ControlModifier) return
            if (typeof editController !== "undefined"
                    && editController.retouchPatchPending) {
                retouchSourceX = mouse.x / width
                retouchSourceY = mouse.y / height
                hasRetouchSource = true
                committingRetouchPatch = true
                editController.commitRetouchPatch(
                    mouse.x / width, mouse.y / height)
                committingRetouchPatch = false
            } else {
                retouchTargetX = mouse.x / width
                retouchTargetY = mouse.y / height
                hasRetouchTarget = true
                hasRetouchSource = false
                if (typeof editController !== "undefined")
                    editController.beginRetouchPatch(
                        mouse.x / width, mouse.y / height)
            }
        }

        Component {
            id: retouchCircleComponent
            Item {
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    radius: width / 2
                    border.width: 2
                    border.color: "#000000"
                }
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 2
                    color: "transparent"
                    radius: width / 2
                    border.width: 1
                    border.color: "#ffffff"
                }
            }
        }

        Loader {
            id: retouchTargetCircle
            objectName: "retouchTargetCircle"
            sourceComponent: retouchCircleComponent
            visible: retouchClickArea.hasRetouchTarget
            width: 2 * retouchClickArea.brushRadius
            height: width
            x: retouchClickArea.retouchTargetX
                * retouchClickArea.width - width / 2
            y: retouchClickArea.retouchTargetY
                * retouchClickArea.height - height / 2
            z: 1
        }

        Loader {
            id: retouchSourceCircle
            objectName: "retouchSourceCircle"
            sourceComponent: retouchCircleComponent
            visible: retouchClickArea.hasRetouchSource
            width: 2 * retouchClickArea.brushRadius
            height: width
            x: retouchClickArea.retouchSourceX
                * retouchClickArea.width - width / 2
            y: retouchClickArea.retouchSourceY
                * retouchClickArea.height - height / 2
            z: 2
        }

        Loader {
            id: retouchBrushCursor
            objectName: "retouchBrushCursor"
            sourceComponent: retouchCircleComponent
            visible: retouchClickArea.containsMouse
                     && !retouchClickArea.ctrlPanning
            width: 2 * retouchClickArea.brushRadius
            height: width
            x: retouchClickArea.mouseX - width / 2
            y: retouchClickArea.mouseY - height / 2
            z: 3
        }
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
                        && typeof editController !== "undefined"
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
                    if (typeof editController !== "undefined") {
                        editController.removeRedeyeRegionAt(
                            mouse.x / width, mouse.y / height)
                        keretenAll = editController
                            .redeyeRegionHitAt(
                                mouse.x / width, mouse.y / height)
                    }
                    return
                }
                if (typeof editController !== "undefined")
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
            if (typeof editController !== "undefined")
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
                    if (typeof editController !== "undefined")
                        editController.selectTextOverlay(modelData.index)
                }
            }
        }
    }
}
