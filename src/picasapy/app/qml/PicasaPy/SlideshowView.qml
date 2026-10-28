import QtQuick
import QtQuick.Controls

// Diavetítés (#8) — a Picasa Ctrl+4-es teljes képernyős vetítése.
// Időzített léptetés (videókat kihagyva, körbefordulással), szóköz =
// szünet, Esc = kilépés, nyilak = kézi léptetés, Ctrl+R / Ctrl+Shift+R =
// forgatás vetítés közben. A léptetés-logika a controllertől független
// (csak a photosModel-t használja); a csillag/forgatás műveleteket
// jelekkel kéri — a bekötés a Main.qml dolga.
Rectangle {
    id: show
    color: "#000000"
    visible: false
    clip: true

    property var photosModel: null
    //: A Pan and Zoom két kivágását a host Python-vezérlője adja át;
    //: a képernyővédő ugyanazt az illesztőt használja.
    property var panZoomRectanglesProvider: null
    // #1640: az AKTÍV megjelenítési mód — a vetített kép URL-jének valódi
    // argumentuma (`displayUrlAt(index, mód)`). A hívó (Main.qml) köti a
    // `controller.displayMode`-hoz; így a kötés módváltáskor újraértékelődik.
    // Eldobott referenciával (`(controller.displayMode, url)`) MÉRVE nem
    // működött: a dia a nyers fájlnál maradt.
    property string displayMode: ""
    property int currentIndex: -1
    //: #3881: a LÁTHATÓ kép útvonala — ezen keresztül követjük a modellt
    //: (törlés, átrendezés), mert a nyers index a modell szerkezeti
    //: változásakor (sor-eltolódás, teljes reset) mást jelenthet, mint
    //: amit a felhasználó épp néz.
    property string _currentFilePath: ""
    //: igazra állítva az `onCurrentIndexChanged` nem indít átmenetet — a
    //: `_modellKovetes` csendben igazítja az indexet ugyanarra a fájlra
    property bool _resyncing: false
    property bool screensaverMode: false
    property bool screensaverInputArmed: false
    // #5653: az eredeti oneup láthatósági feltételei. A képernyőmélység
    // tesztben felülírható; az éles értéket a host adja át QScreenből.
    property bool bigSlideshow2: true
    property int screenDepth: 0
    property bool timelineSlideshow: false
    readonly property bool timelineButtonVisible: bigSlideshow2
        && (screenDepth === 16 || screenDepth === 32)
        && !timelineSlideshow
    //: #2992: a diaidő MÁSODPERCBEN, a sáv ± gombjaival állítható
    //: (`tpslabel`/`minusone`/`tps`/`plusone`). Az alapérték 3 — mérve
    //: (`SlideshowEffectTime`, `0x007facd3`). A hívó a vezérlőhöz köti,
    //: hogy megmaradjon; kötés nélkül a mért alapérték marad.
    property int seconds: 3
    readonly property int intervalMs: Math.max(1, show.seconds) * 1000
    property bool playing: false
    // #4320: a beállításfül tartós ismétlés- és zenebeállításai.
    property bool loop: true
    property bool musicEnabled: false
    property var musicTrackUrls: []
    property int _musicTrackIndex: 0

    function _syncMusic() {
        if (!show.visible || !show.playing || show.screensaverMode
                || !show.musicEnabled || !show.musicTrackUrls
                || show.musicTrackUrls.length === 0) {
            musicPlayerLoader.active = false
            return
        }
        musicPlayerLoader.active = true
        var player = musicPlayerLoader.item
        if (!player) return
        if (show._musicTrackIndex < 0
                || show._musicTrackIndex >= show.musicTrackUrls.length)
            show._musicTrackIndex = 0
        var target = show.musicTrackUrls[show._musicTrackIndex]
        if (player.source !== target || !player.playing)
            player.playTrack(target)
    }

    function _nextMusicTrack() {
        if (!show.musicTrackUrls || show.musicTrackUrls.length === 0) {
            show._syncMusic()
            return
        }
        show._musicTrackIndex = (show._musicTrackIndex + 1)
            % show.musicTrackUrls.length
        show._syncMusic()
    }

    Loader {
        id: musicPlayerLoader
        objectName: "slideshowMusicPlayerLoader"
        active: false
        source: active ? "SlideshowMusicPlayer.qml" : ""
        onLoaded: show._syncMusic()
    }
    Connections {
        target: musicPlayerLoader.item
        function onTrackEnded() { show._nextMusicTrack() }
    }
    onMusicEnabledChanged: show._syncMusic()
    onMusicTrackUrlsChanged: {
        show._musicTrackIndex = 0
        show._syncMusic()
    }
    onPlayingChanged: show._syncMusic()
    onScreensaverModeChanged: show._syncMusic()

    //: #4856: a diavetítés átmenet-választója az eredeti hét elemét kínálja
    //: (`picasa-create-features.md` 4.3), ebben a sorrendben. A feliratok a
    //: meglévő `CTransitions::*` szövegek.
    readonly property var atmenetek: [
        { kulcs: "cut", nev: qsTr("Cut") },
        { kulcs: "kenburns", nev: qsTr("Pan and Zoom") },
        { kulcs: "dissolve", nev: qsTr("Dissolve") },
        { kulcs: "wiperight", nev: qsTr("Wipe") },
        { kulcs: "circleout", nev: qsTr("Circle") },
        { kulcs: "pushright", nev: qsTr("Push") },
        { kulcs: "rect", nev: qsTr("Rectangle") }
    ]
    property string transitionKind: "dissolve"
    //: #2992: a diaidő a sáv ± gombjairól a HÍVÓNAK megy (Main.qml →
    //: vezérlő), hogy megmaradjon — a vetítő maga nem ír beállítást. Az
    //: átmenet és a feliratmód ugyanezt az utat járja (`transitionPicked`,
    //: `captionModePicked`).
    signal secondsChosen(int masodperc)
    //: az átmenet hossza (`SlideshowEffectTime`) — a dia-időnél rövidebb
    property int transitionMs: 700
    //: #433: a felirat megjelenítési módja vetítés közben (`captionmode`):
    //: a felirat, a fájlnév, vagy semmi — ugyanaz a hármas, mint a
    //: nyomtatás-opciókban.
    readonly property var feliratModok: ["caption", "filename", "none"]
    property string captionMode: "caption"

    //: a VETÍTETT felirat — a mód szerint felirat, fájlnév vagy üres
    readonly property string aktualisFelirat: {
        if (!show.photosModel || show.currentIndex < 0) return ""
        if (show.captionMode === "none") return ""
        show.photosModel.revision  // a kötés kövesse a szerkesztést
        if (show.captionMode === "filename") {
            var ut = show.photosModel.filePathAt(show.currentIndex)
            var perjel = ut.lastIndexOf("/")
            return perjel >= 0 ? ut.substring(perjel + 1) : ut
        }
        return show.photosModel.captionAt(show.currentIndex)
    }
    signal closed()
    signal starToggled(int index)
    signal rotateRequested(int index, int delta)
    signal timelineRequested()
    //: #433: a választó nem ír közvetlenül a beállításba — a gazda dönti el,
    //: hova kerül (a `starToggled`/`rotateRequested` mintája).
    signal transitionPicked(string kulcs)
    signal captionModePicked(string mod)

    //: #3832: a vetített kép textúrájának leghosszabb éle. A V3D
    //: textúraplafonja 4096 — ez alatt marad, és egy 4K-s kijelzőt is
    //: kitölt.
    readonly property int texturaEl: 2560

    //: #3832: a kép `sourceSize`-a a VALÓDI méretéből (`pixelWidthAt`/
    //: `pixelHeightAt`, #2492 — a megjelenített, EXIF-orientált méret): a
    //: `texturaEl` dobozba illő, legfeljebb natív méret, MINDKÉT élen
    //: kitöltve.
    //:
    //: ⚠️ Miért pontos méret, és miért nem doboz. Valódi GPU-n MÉRVE a Qt
    //: saját fájlbetöltője FELNAGYÍT a kért méretre: a csak-szélességes
    //: 2560-as kérés egy 1440×2560-as és egy 3000×5333-as képből is
    //: 2560×4551-es textúrát csinált (a 4096-os plafon fölött — a Qt
    //: ilyenkor csendben lekicsinyít, a kár képenként ~46 MB memória és a
    //: CPU-idő), a `Qt.size(2560, 2560)` doboz pedig egy 400×300-as képből
    //: 3413×2560-at. A pontos, natívnál nem nagyobb méretre nincs mit
    //: felnagyítani.
    //:
    //: Ismeretlen méretnél (0, pl. még nem indexelt kép) a korábbi út: csak
    //: szélesség a nyers fájlnak, 2560-as doboz a `displayphoto`
    //: szolgáltatónak (az a dobozba nem nagyít fel).
    function forrasMeret(index) {
        var el = show.texturaEl
        if (!photosModel || index < 0
                || typeof photosModel.pixelWidthAt !== "function")
            return Qt.size(el, 0)
        var szolgaltato = photosModel.displayUrlAt(index, show.displayMode)
                          .indexOf("image://displayphoto/") === 0
        var szel = photosModel.pixelWidthAt(index)
        var mag = photosModel.pixelHeightAt(index)
        if (szel <= 0 || mag <= 0)
            return Qt.size(el, szolgaltato ? el : 0)
        var w = Math.min(el, szel)
        var h = Math.round(mag * w / szel)
        if (h > el) {
            h = el
            w = Math.round(szel * el / mag)
        }
        //: ⚠️ A Qt fájlbetöltője a kért méretet a fájlban TÁROLT tájolásra
        //: alkalmazza, nem a megjelenítettre (mérve: egy 6-os EXIF-állású
        //: 5333×3000-es képnek 1440×2560-at kérve 2560×4551 lett) — ott a
        //: pár fordítva kell. A `displayphoto` a megjelenített tájolásban
        //: dolgozik, annak nem.
        if (!szolgaltato && typeof photosModel.pixelSidesSwappedAt === "function"
                && photosModel.pixelSidesSwappedAt(index))
            return Qt.size(h, w)
        return Qt.size(w, h)
    }

    function count() {
        return photosModel ? photosModel.rowCount() : 0
    }

    // a következő FOTÓ indexe (a videókat kihagyjuk, #8/#14); -1, ha nincs
    function nextPhotoIndex(fromIndex, step) {
        var n = count()
        if (n === 0) return -1
        var idx = fromIndex
        for (var i = 0; i < n; ++i) {
            var next = idx + step
            if (next < 0 || next >= n) {
                if (!show.screensaverMode && !show.loop) return -1
                next = ((next % n) + n) % n
            }
            idx = next
            if (!photosModel.isVideoAt(idx)) return idx
        }
        return -1
    }

    // az induló index fotóra igazítása (videón álló kijelölésről indítva
    // a következő fotóra ugrunk)
    function clampToPhoto(index) {
        if (photosModel && index >= 0 && index < count()
                && !photosModel.isVideoAt(index))
            return index
        return nextPhotoIndex(index >= 0 ? index : -1, 1)
    }

    function start(index) {
        screensaverMode = false
        screensaverInputArmed = false
        slideshowTiming.inputArmTimer.stop()
        var target = clampToPhoto(index)
        if (target < 0) return   // nincs vetíthető fotó
        currentIndex = target
        //: #3881: azonos számra indítva az `onCurrentIndexChanged` nem fut
        //: le — ha a modell közben (rejtve) változott, a követett útvonal
        //: elavult volna, ezért itt mindig újraírjuk
        show._kovetettUtFrissit()
        playing = true
        visible = true
        forceActiveFocus()
    }

    function startScreensaver() {
        screensaverMode = true
        screensaverInputArmed = false
        slideshowTiming.inputArmTimer.stop()
        var target = clampToPhoto(0)
        if (target < 0) {
            currentIndex = -1
            screensaverMode = false
            return
        }
        currentIndex = target
        show._kovetettUtFrissit()
        playing = true
        visible = true
        slideshowControls.controls.shown = false
        slideshowControls.autoHideTimer.stop()
        forceActiveFocus()
        slideshowTiming.inputArmTimer.start()
    }

    function stop() {
        if (!visible) return
        var wasScreensaver = screensaverMode
        slideshowTiming.inputArmTimer.stop()
        screensaverInputArmed = false
        playing = false
        visible = false
        show.closed()
        if (wasScreensaver)
            screensaverMode = false
    }

    function advance() {
        var target = nextPhotoIndex(currentIndex, 1)
        if (target < 0) { stop(); return }
        currentIndex = target
    }

    function goBack() {
        var target = nextPhotoIndex(currentIndex, -1)
        if (target >= 0) currentIndex = target
    }

    //: #433: a váltás pillanatában a `slide.source` MÉG a kimenő kép URL-je
    //: (a `_diakBetolt` csak utána írja át) — ezt adjuk az áttűnésnek.
    //:
    //: ⚠️ #3018 — MÉRVE, és ez volt a hiba. Korábban egy külön `elozoUrl`
    //: tárolón át ment, és EGY LÉPÉSSEL eltolódott: az áttűnés a KÉT
    //: lépéssel korábbi képet mutatta. A tulajdonos ezt látta „bevillanó
    //: idegen képként". A mérés (három kép, két váltás): a második
    //: áttűnés kimenő képe az ELSŐ kép volt, pedig a MÁSODIKAT nézte.
    onCurrentIndexChanged: {
        show._kovetettUtFrissit()
        var kimeno = imageLayer.currentImage.source
        if (show.visible && kimeno !== "" && !show._resyncing)
            show._atmenetIndit(kimeno)
        show._diakBetolt()
    }
    onVisibleChanged: {
        show._diakBetolt()
        show._syncMusic()
    }
    onPhotosModelChanged: {
        show._kovetettUtFrissit()
        show._diakBetolt()
    }
    onDisplayModeChanged: show._diakBetolt()
    onTransitionKindChanged: show._frissitKenBurns()
    onWidthChanged: show._frissitKenBurns()
    onHeightChanged: show._frissitKenBurns()

    //: #3881: a látott kép útvonala a JELEN indexből
    function _kovetettUtFrissit() {
        show._currentFilePath = show.photosModel && show.currentIndex >= 0
            ? show.photosModel.filePathAt(show.currentIndex) : ""
    }

    //: #3881: a modell szerkezeti jelére (sortörlés, teljes reset — pl.
    //: átrendezés) a LÁTHATÓ képet követjük, nem a nyers indexet: a sorok
    //: eltolódhatnak vagy átrendeződhetnek anélkül, hogy a nézett kép
    //: megváltozna. A `layoutChanged`-et a `PhotoGridModel` nem küldi (az
    //: átrendezés teljes reset), ezért arra nincs kezelő.
    Connections {
        target: show.photosModel
        function onRowsRemoved(parent, first, last) {
            show._sorokTorolve(first, last)
        }
        function onModelReset() { show._modellReset() }
    }

    //: az index CSENDBEN (átmenet nélkül) áll a megadott sorra
    function _indexCsendben(index) {
        show._resyncing = true
        show.currentIndex = index
        show._resyncing = false
    }

    //: kiürült lista: nincs látott kép, tehát a kilépés se jelöljön ki
    //: nem létező sort (`exitSlideshow` a -1-et kihagyja)
    function _uresListaLeall() {
        show._indexCsendben(-1)
        show.stop()
    }

    //: a törlés a jel argumentumaiból dől el, a lista bejárása nélkül
    function _sorokTorolve(first, last) {
        if (!show.visible || !show.photosModel) return
        if (show.count() === 0) { show._uresListaLeall(); return }
        var i = show.currentIndex
        if (i < 0) return
        if (last < i) {
            show._indexCsendben(i - (last - first + 1))
        } else if (first <= i) {
            // a látott kép törlődött: a helyén a KÖVETKEZŐ áll, a lista
            // végén — ahogy az `advance()` — körbe a 0. sor
            show._kovetkezoreLep(first)
        } else {
            // későbbi sor: a látott kép marad, de a következő változhatott
            show._diakBetolt()
        }
    }

    //: teljes reset után a látott fájlt EGY Python-hívás keresi vissza
    function _modellReset() {
        if (!show.visible || !show.photosModel) return
        if (show.count() === 0) { show._uresListaLeall(); return }
        if (show._currentFilePath === "") return
        var sor = show.photosModel.rowOfPath(show._currentFilePath)
        if (sor >= 0) {
            if (sor !== show.currentIndex)
                show._indexCsendben(sor)
            else
                show._diakBetolt()   // az elő-betöltő a friss következőt
            return
        }
        show._kovetkezoreLep(show.currentIndex)
    }

    //: a látott kép eltűnt; `jelolt` az a sor, ahol most a következő áll
    function _kovetkezoreLep(jelolt) {
        var kezdo = jelolt >= 0 && jelolt < show.count() ? jelolt : 0
        var kovetkezo = show.clampToPhoto(kezdo)
        if (kovetkezo < 0) { show._uresListaLeall(); return }
        if (kovetkezo !== show.currentIndex) {
            show.currentIndex = kovetkezo
            return
        }
        // a szám nem változott, de alatta más kép áll — azonos értékre az
        // `onCurrentIndexChanged` nem fut le, ezért kézzel váltunk
        var kimeno = imageLayer.currentImage.source
        show._kovetettUtFrissit()
        if (kimeno !== "") show._atmenetIndit(kimeno)
        show._diakBetolt()
    }

    //: a vetített kép URL-je (#1640: a mód VALÓDI argumentum), üres, ha
    //: nincs mit vetíteni
    function _diaUrl(index) {
        return show.visible && show.photosModel && index >= 0
            ? show.photosModel.displayUrlAt(index, show.displayMode) : ""
    }

    //: #3832: a forrás és a forrásméret EGYÜTT, egyetlen betöltéssel.
    //:
    //: ⚠️ Miért nem két kötés. A Qt az `Image` `source`-ának ÉS a
    //: `sourceSize`-ának minden egyes változására AZONNAL betölt. Két
    //: kötésnél lépéskor az egyik előbb fordul át, és a kép egyszer a
    //: rossz párral is betöltődik (a régi kép az új mérettel, vagy az új a
    //: régivel) — a gyorstárban egyik sincs meg, tehát teljes dekódolás.
    //: MÉRVE a `displayphoto` úton, három különböző méretű képen, három
    //: lépésben: két kötéssel 17 szolgáltató-kérés, köztük rossz párok (egy
    //: 400×300-as kép 1440×1080-ra, egy álló kép 168×300-ra méretezve);
    //: ezzel az úttal (és az elő-betöltő egyező `fillMode`-jával) 5.
    //: Ezért méretváltáskor a forrás előbb kiürül (üres forrásra a Qt nem
    //: tölt), a méret beáll, és csak utána jön az új forrás.
    function _betolt(kep, url, meret) {
        var regi = kep.sourceSize
        var ujMeret = regi.width !== meret.width || regi.height !== meret.height
        if (!ujMeret && kep.source.toString() === String(url))
            return
        if (ujMeret) {
            kep.source = ""
            kep.sourceSize = meret
        }
        kep.source = url
    }

    function _panZoomRectanglesFor(index) {
        if (typeof show.panZoomRectanglesProvider !== "function"
                || !show.photosModel || index < 0
                || typeof show.photosModel.pixelWidthAt !== "function"
                || typeof show.photosModel.pixelHeightAt !== "function"
                || typeof show.photosModel.rotateAt !== "function")
            return []
        var sourceWidth = show.photosModel.pixelWidthAt(index)
        var sourceHeight = show.photosModel.pixelHeightAt(index)
        if (show.photosModel.rotateAt(index) % 2) {
            var swap = sourceWidth
            sourceWidth = sourceHeight
            sourceHeight = swap
        }
        if (sourceWidth <= 0 || sourceHeight <= 0
                || show.width <= 0 || show.height <= 0)
            return []
        return show.panZoomRectanglesProvider(
            sourceWidth, sourceHeight,
            Math.max(1, Math.round(show.width)),
            Math.max(1, Math.round(show.height)))
    }

    function _frissitKenBurns() {
        if (show.transitionKind === "kenburns" && show.visible
                && show.currentIndex >= 0) {
            imageLayer.currentImage.panZoomRectangles =
                show._panZoomRectanglesFor(show.currentIndex)
            imageLayer.currentImage.panZoomProgress = 0
            if (imageLayer.currentImage.panZoomRectangles.length === 2)
                imageLayer.panZoomAnimation.restart()
            else
                imageLayer.panZoomAnimation.stop()
        } else {
            imageLayer.panZoomAnimation.stop()
            imageLayer.currentImage.panZoomRectangles = []
            imageLayer.currentImage.panZoomProgress = 0
        }
    }

    //: a dia és az elő-betöltő forrása — minden olyan változáskor, amitől a
    //: vetített kép függ (index, láthatóság, modell, megjelenítési mód)
    function _diakBetolt() {
        show._betolt(imageLayer.currentImage, show._diaUrl(show.currentIndex),
                     show.forrasMeret(show.currentIndex))
        show._frissitKenBurns()
        var kovetkezo = show.visible && show.photosModel
            ? show.nextPhotoIndex(show.currentIndex, 1) : -1
        // #1640: az elő-betöltés is a mód-tudatos URL-t kérje — különben a
        // következő dia egy pillanatra a festetlen képet villantaná
        show._betolt(imageLayer.preloadImage, show._diaUrl(kovetkezo),
                     show.forrasMeret(kovetkezo))
    }

    function togglePause() { playing = !playing }
    function starCurrent() { show.starToggled(currentIndex) }
    function rotateCurrent(delta) { show.rotateRequested(currentIndex, delta) }

    //: #433/#4567: az átmenetmotor két `Image`-et használ
    //: (`slideshowPrevImage`, `slideshowImage`); a fekete/fehér áttűnéshez
    //: fátyol tartozik, a mozgó változatok az iránytól függő geometriát
    //: animálják.
    //:
    //: ⚠️ A `cut` nem „nincs átmenet": az eredeti készletben SAJÁT tétel
    //: (`transtype` 1. eleme), ezért a választóban is szerepel — a
    //: viselkedése nulla hosszú áttűnés.
    //: #3023: a kimenő másolat GEOMETRIÁJA is a látott diáé. A tulajdonos
    //: jelentése: „az éppen eltűnő kép egy picit kisebb lesz, emiatt ugrálás
    //: hatás van" — a másolat ugyanis alapméreten (`scale` 1,0, elfordulás
    //: nélkül) jelent meg, tehát a váltás pillanatában visszaugrott.
    //:
    //: A kötések itt MÉG a kimenő diáé (ugyanaz a lusta újraértékelés, amin
    //: a #3018 kimenő URL-je is múlik), ezért a dia élő értékeit másoljuk.
    function _geometriatAtvesz() {
        imageLayer.previousImage.width = imageLayer.currentImage.width
        imageLayer.previousImage.height = imageLayer.currentImage.height
        imageLayer.previousImage.rotation = imageLayer.currentImage.rotation
        imageLayer.previousImage.scale = imageLayer.currentImage.scale
        imageLayer.previousImage.transitionOffsetX = imageLayer.currentImage.transitionOffsetX
        imageLayer.previousImage.transitionOffsetY = imageLayer.currentImage.transitionOffsetY
        imageLayer.previousImage.capturedPanZoomX =
            imageLayer.currentImage.x
            - imageLayer.currentImage.transitionOffsetX
        imageLayer.previousImage.capturedPanZoomY =
            imageLayer.currentImage.y
            - imageLayer.currentImage.transitionOffsetY
        imageLayer.previousImage.exactPanZoomGeometry = imageLayer.currentImage.panZoomActive
    }

    function _atmenetIrany() {
        var w = show.width
        var h = show.height
        switch (show.transitionKind) {
        case "wipeleft": return { x: w, y: 0 }
        case "wiperight": return { x: -w, y: 0 }
        case "wipeup": return { x: 0, y: h }
        case "wipedown": return { x: 0, y: -h }
        case "diagwipeul": return { x: w, y: h }
        case "diagwipeur": return { x: -w, y: h }
        case "diagwipedl": return { x: w, y: -h }
        case "diagwipedr": return { x: -w, y: -h }
        case "pushleft": return { x: -w, y: 0 }
        case "pushright": return { x: w, y: 0 }
        case "pushtop": return { x: 0, y: -h }
        case "pushdown": return { x: 0, y: h }
        default: return { x: 0, y: 0 }
        }
    }

    function _kilepoKepMozog() {
        return show.transitionKind.indexOf("wipe") === 0
                || show.transitionKind.indexOf("diagwipe") === 0
                || show.transitionKind.indexOf("push") === 0
    }

    function _beuszoKepMozog() {
        return show.transitionKind.indexOf("push") === 0
    }

    function _atmenetVege() {
        imageLayer.previousImage.opacity = 0
        imageLayer.previousImage.transitionOffsetX = 0
        imageLayer.previousImage.transitionOffsetY = 0
        imageLayer.currentImage.transitionOffsetX = 0
        imageLayer.currentImage.transitionOffsetY = 0
        if (show.transitionKind !== "kenburns"
                && show.transitionKind !== "kenburnsaoi")
            imageLayer.currentImage.scale = 1
        imageLayer.veil.opacity = 0
    }

    function _atmenetIndit(elozoUrl) {
        imageLayer.transitionAnimation.stop()
        show._geometriatAtvesz()
        imageLayer.previousImage.transitionOffsetX = 0
        imageLayer.previousImage.transitionOffsetY = 0
        imageLayer.currentImage.transitionOffsetX = 0
        imageLayer.currentImage.transitionOffsetY = 0
        //: a bejövő dia a saját mozgásának elejéről induljon: az előző dia
        //: geometriája a másolaton él tovább, a diát visszaállítjuk
        imageLayer.currentImage.scale = 1.0
        if (show.transitionKind === "kenburnsaoi")
            imageLayer.panZoomFaceAnimation.restart()
        if (show.transitionKind === "cut" || !elozoUrl) {
            imageLayer.previousImage.opacity = 0
            imageLayer.currentImage.opacity = 1
            imageLayer.veil.opacity = 0
            return
        }
        //: #3832: a kimenő kép a SAJÁT forrásméretével (a dia még azt
        //: tartja) — ugyanaz a pár, tehát a Qt gyorstárából jön
        show._betolt(
            imageLayer.previousImage, elozoUrl, imageLayer.currentImage.sourceSize)
        imageLayer.previousImage.opacity = 1
        var irany = show._atmenetIrany()
        if (show._beuszoKepMozog()) {
            imageLayer.currentImage.transitionOffsetX = -irany.x
            imageLayer.currentImage.transitionOffsetY = -irany.y
        }
        if (show.transitionKind.indexOf("wipe") >= 0) {
            // A kimenő kép irányba kicsúszik; az új kép közben fokozatosan
            // fedi fel az alatta maradó képet, hogy a wipe látható legyen.
            imageLayer.currentImage.opacity = 0
        } else if (show.transitionKind === "circleout") {
            imageLayer.currentImage.scale = 0.18
            imageLayer.currentImage.opacity = 0
        } else if (show.transitionKind === "rect") {
            imageLayer.currentImage.scale = 0.72
            imageLayer.currentImage.opacity = 0
        } else if (show.transitionKind === "circlein") {
            imageLayer.currentImage.scale = 1.2
            imageLayer.currentImage.opacity = 0
        } else if (show.transitionKind === "timelapse") {
            imageLayer.currentImage.scale = 1.16
            imageLayer.currentImage.opacity = 0
        } else {
            imageLayer.currentImage.opacity = show.transitionKind === "dissolve" ? 0 : 1
        }
        imageLayer.veil.color = show.transitionKind === "dissolvewhite"
            ? "#ffffff" : "#000000"
        imageLayer.veil.opacity = 0
        imageLayer.transitionAnimation.start()
    }

    SlideshowImageLayer {
        id: imageLayer
        slideshow: show
        previousImage: elozoSlide
        currentImage: slide
        veil: fatyol
        preloadImage: elobetoltoSlide
        panZoomAnimation: slide.panZoomAnimation
        panZoomFaceAnimation: slide.panZoomFaceAnimation
    }

    SlideshowTiming {
        id: slideshowTiming
        slideshow: show
    }

    Keys.onEscapePressed: {
        if (!show.screensaverMode || show.screensaverInputArmed)
            show.stop()
    }
    Keys.onSpacePressed: {
        if (show.screensaverMode) {
            if (show.screensaverInputArmed) show.stop()
        } else show.togglePause()
    }
    Keys.onRightPressed: {
        if (show.screensaverMode) {
            if (show.screensaverInputArmed) show.stop()
        } else show.advance()
    }
    Keys.onReturnPressed: {
        if (show.screensaverMode) {
            if (show.screensaverInputArmed) show.stop()
        } else show.advance()
    }
    Keys.onLeftPressed: {
        if (show.screensaverMode) {
            if (show.screensaverInputArmed) show.stop()
        } else show.goBack()
    }
    Keys.onPressed: (event) => {
        if (show.screensaverMode) {
            if (show.screensaverInputArmed) show.stop()
            event.accepted = true
            return
        }
        if (event.key === Qt.Key_R
                && (event.modifiers & Qt.ControlModifier)) {
            show.rotateCurrent(
                (event.modifiers & Qt.ShiftModifier) ? -1 : 1)
            event.accepted = true
        }
    }

    SlideshowPreviousImage {
        id: elozoSlide
        slideshow: show
    }
    SlideshowCurrentImage {
        id: slide
        slideshow: show
    }
    SlideshowVeil {
        id: fatyol
    }
    SlideshowPreloadImage {
        id: elobetoltoSlide
        slideshow: show
    }

    SlideshowControls {
        id: slideshowControls
        slideshow: show
    }

}
