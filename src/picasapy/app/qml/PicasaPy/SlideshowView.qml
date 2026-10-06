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

    property var photosModel: null
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

    //: #433: az ÁTMENET a diák között. Az eredeti diavetítése ugyanazt a
    //: 18-as készletet használja, mint a filmkészítő (`transtype`,
    //: `picasa-create-features.md` 2.1) — ebből az az öt van meg, amelyik a
    //: Picasa jellegzetes érzetét adja; a maradék 13 a filmkészítővel
    //: együtt jön (#432). A választó csak azt sorolja fel, ami MŰKÖDIK.
    //: A feliratok az eredeti HIVATALOS magyar szövegei
    //: (`CTransitions::*`, `picasa-create-features.md` 2.1): Kivágás ·
    //: Szétoszlás · Szétoszlás feketén át · Szétoszlás fehéren át ·
    //: Pásztázás és nagyítás — nem a mi fordításunk.
    readonly property var atmenetek: [
        { kulcs: "cut", nev: qsTr("Cut") },
        { kulcs: "dissolve", nev: qsTr("Dissolve") },
        { kulcs: "dissolveblack", nev: qsTr("Dissolve through black") },
        { kulcs: "dissolvewhite", nev: qsTr("Dissolve through white") },
        { kulcs: "kenburns", nev: qsTr("Pan and Zoom") }
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
        screensaverInputTimer.stop()
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
        screensaverInputTimer.stop()
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
        controlsBar.shown = false
        hideTimer.stop()
        forceActiveFocus()
        screensaverInputTimer.start()
    }

    function stop() {
        if (!visible) return
        var wasScreensaver = screensaverMode
        screensaverInputTimer.stop()
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
        var kimeno = slide.source
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
        var kimeno = slide.source
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

    //: a dia és az elő-betöltő forrása — minden olyan változáskor, amitől a
    //: vetített kép függ (index, láthatóság, modell, megjelenítési mód)
    function _diakBetolt() {
        show._betolt(slide, show._diaUrl(show.currentIndex),
                     show.forrasMeret(show.currentIndex))
        var kovetkezo = show.visible && show.photosModel
            ? show.nextPhotoIndex(show.currentIndex, 1) : -1
        // #1640: az elő-betöltés is a mód-tudatos URL-t kérje — különben a
        // következő dia egy pillanatra a festetlen képet villantaná
        show._betolt(elobetoltoSlide, show._diaUrl(kovetkezo),
                     show.forrasMeret(kovetkezo))
    }

    function togglePause() { playing = !playing }
    function starCurrent() { show.starToggled(currentIndex) }
    function rotateCurrent(delta) { show.rotateRequested(currentIndex, delta) }

    //: #433: az ÁTMENET motorja. A kimenő képet egy második `Image` tartja
    //: (`slideshowPrevImage`), a fekete/fehér áttűnést pedig egy fátyol —
    //: így a négy átmenet ugyanabból a két elemből épül, elágazás nélkül a
    //: rajzoló oldalon.
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
        elozoSlide.width = slide.width
        elozoSlide.height = slide.height
        elozoSlide.rotation = slide.rotation
        elozoSlide.scale = slide.scale
    }

    function _atmenetIndit(elozoUrl) {
        atmenetAnimacio.stop()
        show._geometriatAtvesz()
        //: a bejövő dia a pásztázás ELEJÉRŐL induljon: az előző dia
        //: nagyítása a másolaton él tovább, a diát visszaállítjuk
        slide.scale = 1.0
        if (show.transitionKind === "kenburns")
            kenBurns.restart()
        if (show.transitionKind === "cut" || !elozoUrl) {
            elozoSlide.opacity = 0
            slide.opacity = 1
            fatyol.opacity = 0
            return
        }
        //: #3832: a kimenő kép a SAJÁT forrásméretével (a dia még azt
        //: tartja) — ugyanaz a pár, tehát a Qt gyorstárából jön
        show._betolt(elozoSlide, elozoUrl, slide.sourceSize)
        elozoSlide.opacity = 1
        slide.opacity = show.transitionKind === "dissolve" ? 0 : 1
        fatyol.color = show.transitionKind === "dissolvewhite"
            ? "#ffffff" : "#000000"
        fatyol.opacity = 0
        atmenetAnimacio.start()
    }

    SequentialAnimation {
        id: atmenetAnimacio
        objectName: "slideshowTransition"
        //: az egyszerű áttűnés PÁRHUZAMOS (a kimenő halványul, a bejövő
        //: erősödik), a fekete/fehér áttűnés SOROS (előbb a fátyol be, utána
        //: ki) — ezért van két, egymást kizáró szakasz.
        ParallelAnimation {
            NumberAnimation {
                target: elozoSlide; property: "opacity"; to: 0
                duration: show.transitionKind === "dissolve"
                          ? show.transitionMs : show.transitionMs / 2
            }
            NumberAnimation {
                target: slide; property: "opacity"; to: 1
                duration: show.transitionKind === "dissolve"
                          ? show.transitionMs : 1
            }
            NumberAnimation {
                target: fatyol; property: "opacity"
                to: show.transitionKind === "dissolve" ? 0 : 1
                duration: show.transitionKind === "dissolve"
                          ? 1 : show.transitionMs / 2
            }
        }
        NumberAnimation {
            target: fatyol; property: "opacity"; to: 0
            duration: show.transitionKind === "dissolve"
                      ? 1 : show.transitionMs / 2
        }
    }

    Timer {
        id: stepTimer
        objectName: "slideshowTimer"
        interval: show.intervalMs
        repeat: true
        running: show.visible && show.playing
        onTriggered: show.advance()
    }

    Timer {
        id: screensaverInputTimer
        objectName: "screensaverInputArmTimer"
        interval: 250
        onTriggered: if (show.visible && show.screensaverMode)
                         show.screensaverInputArmed = true
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

    //: #433: a KIMENŐ dia — az átmenet alatt ez halványul el. A fő kép
    //: ALATT rajzolódik (előbb szerepel), tehát az áttűnés végén a bejövő
    //: kép van fölül.
    Image {
        id: elozoSlide
        objectName: "slideshowPrevImage"
        anchors.centerIn: parent
        //: a méretet/elfordulást a váltáskor a `_geometriatAtvesz` írja —
        //: ezek csak a kezdőértékek (első dia, még nincs mit másolni)
        width: parent.width
        height: parent.height
        opacity: 0
        fillMode: Image.PreserveAspectFit
        asynchronous: false
        autoTransform: true
        //: #3832: a kimenő dia a KIMENŐ kép forrásméretét kapja (az
        //: `_atmenetIndit` írja a forrással együtt) — ez csak a kezdőérték
        sourceSize: show.forrasMeret(-1)
    }

    Image {
        id: slide
        objectName: "slideshowImage"
        // az ini-forgatást a nézővel azonos módon követi (revision-kötés)
        readonly property int iniSteps: show.photosModel
            ? (show.photosModel.revision,
               show.photosModel.rotateAt(show.currentIndex))
            : 0
        anchors.centerIn: parent
        width: iniSteps % 2 ? parent.height : parent.width
        height: iniSteps % 2 ? parent.width : parent.height
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
        sourceSize: show.forrasMeret(-1)

        //: #433 „Pan and Zoom" (`kenburns`): a dia a tartózkodása alatt
        //: LASSAN nagyít. Nem átmenet, hanem a diára rakott mozgás — ezért
        //: a dia-időhöz kötött, nem az átmenet-hosszhoz.
        NumberAnimation on scale {
            id: kenBurns
            objectName: "slideshowKenBurns"
            running: show.visible && show.transitionKind === "kenburns"
                     && show.currentIndex >= 0
            from: 1.0
            to: 1.08
            duration: Math.max(show.intervalMs, 1)
        }
        //: a nagyítás NEM ragadhat be: átmenet-váltáskor visszaáll
        onScaleChanged: if (show.transitionKind !== "kenburns" && scale !== 1.0)
                            scale = 1.0
    }

    //: #433: az áttűnés FÁTYLA (fekete vagy fehér) — a `dissolveblack` és a
    //: `dissolvewhite` ezen megy át. A diák FÖLÖTT, a vezérlősáv ALATT.
    Rectangle {
        id: fatyol
        objectName: "slideshowVeil"
        anchors.fill: parent
        color: "#000000"
        opacity: 0
        visible: opacity > 0
    }

    // elő-betöltés a következő fotóra (DoD): mire a timer lép, a kép
    // már dekódolva van
    Image {
        id: elobetoltoSlide
        objectName: "slideshowPreloadImage"
        visible: false
        // #1640 + #3832: a forrást és a forrásméretet a `_diakBetolt` írja
        // — ugyanazt a párt, amit a dia kér majd erre a képre, így a lépéskor
        // a Qt gyorstárából jön
        //: #3832: a kitöltési mód is a gyorstár kulcsának része (a Qt a
        //: betöltőnek átadja) — eltérő `fillMode`-dal az elő-betöltött kép
        //: nem volt a diáé, és lépéskor újra dekódolódott (MÉRVE: minden
        //: lépés kétszer kérte ugyanazt a képet a szolgáltatótól)
        fillMode: Image.PreserveAspectFit
        asynchronous: Qt.platform.pluginName !== "offscreen"
        autoTransform: true
        sourceSize: show.forrasMeret(-1)
    }

    // vezérlő-overlay: egérmozgásra jelenik meg, pár másodperc múlva
    // magától eltűnik (Picasa-minta) — a vetítést nem takarja feleslegesen
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: show.screensaverMode ? Qt.AllButtons : Qt.NoButton
        onPressed: if (show.screensaverMode && show.screensaverInputArmed)
                       show.stop()
        onPositionChanged: {
            if (show.screensaverMode) {
                if (show.screensaverInputArmed) show.stop()
            } else {
                controlsBar.shown = true
                hideTimer.restart()
            }
        }
    }
    WheelHandler {
        enabled: show.screensaverMode && show.screensaverInputArmed
        onWheel: show.stop()
    }
    //: #433: a felirat vetítés közben (`captionmode`). A vezérlősáv fölött
    //: ül, hogy a sáv megjelenése ne takarja el.
    Text {
        id: feliratSzoveg
        objectName: "slideshowCaption"
        visible: show.aktualisFelirat.length > 0
        text: show.aktualisFelirat
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 72
        width: parent.width - 96
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        maximumLineCount: 2
        elide: Text.ElideRight
        color: "#ffffff"
        font.pixelSize: Theme.fontSize + 4
        style: Text.Outline
        styleColor: "#000000"
    }

    Timer {
        id: hideTimer
        objectName: "slideshowHideTimer"
        interval: 2500
        //: #2992: a mutató alatt NEM rejtünk el. A lejáró időzítő így nem
        //: kapja el a sávot épp akkor, amikor a felhasználó a gombot
        //: célozza — az újraindítás a `slideshowControlsHover` dolga.
        onTriggered: if (!savLebeges.hovered) controlsBar.shown = false
    }

    Rectangle {
        id: controlsBar
        objectName: "slideshowControls"
        property bool shown: false

        //: ⛔ #2992: a sávnak SAJÁT lebegés-figyelő kell.
        //:
        //: A megjelenítő `MouseArea` a teljes vetítőt fedi, a sáv viszont
        //: UTÁNA van deklarálva, tehát takarja. Amíg a mutató a sávon áll,
        //: a `MouseArea` nem kap `positionChanged`-et — a `hideTimer`
        //: lejár, és a sáv **eltűnik a kéz alól**. A tulajdonos szava a
        //: jegyben: „egérmozgatásra nem jelenik meg a kis lejátszó, ami az
        //: eredetiben ott van, FIXEN" — az „ott van, fixen" épp ezt írja
        //: le: az eredetiben a sáv nem szökik el a mutató elől.
        HoverHandler {
            id: savLebeges
            objectName: "slideshowControlsHover"
            //: amikor a mutató elhagyja a sávot, az elrejtés újraindul —
            //: enélkül a sáv a vetítés végéig kint maradna
            onHoveredChanged: if (!hovered) hideTimer.restart()
        }
        visible: !show.screensaverMode && opacity > 0
        opacity: shown ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 200 } }
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        width: controlsRow.width + 24
        height: 40
        radius: 6
        color: "#2b2b2bd9"

        Row {
            id: controlsRow
            anchors.centerIn: parent
            spacing: 6
            // egységes gombmagasság: a csillag nagyobb glifje (15px) ne
            // növessze meg a saját gombját a többihez képest
            readonly property int buttonHeight: 28

            PicasaButton {
                objectName: "slideshowExitButton"
                text: "✕ " + qsTr("Exit")
                height: controlsRow.buttonHeight
                onClicked: show.stop()
            }
            PicasaButton {
                text: "◀"; width: 34
                height: controlsRow.buttonHeight
                onClicked: show.goBack()
            }
            PicasaButton {
                objectName: "slideshowPlayButton"
                text: show.playing ? "❚❚" : "▶"
                width: 34
                height: controlsRow.buttonHeight
                onClicked: show.togglePause()
            }
            PicasaButton {
                text: "▶▶"; width: 38
                height: controlsRow.buttonHeight
                onClicked: show.advance()
            }
            PicasaButton {
                objectName: "slideshowRotateLeftButton"
                text: "↺"; width: 34
                height: controlsRow.buttonHeight
                onClicked: show.rotateCurrent(-1)
            }
            PicasaButton {
                objectName: "slideshowRotateRightButton"
                text: "↻"; width: 34
                height: controlsRow.buttonHeight
                onClicked: show.rotateCurrent(1)
            }
            //: #433: az ÁTMENET-választó a vezérlősávban — az eredetiben is
            //: ott ül (`slideshowctrls/transtype`, a lebegő sáv alján).
            PicasaComboBox {
                objectName: "slideshowTransitionBox"
                height: controlsRow.buttonHeight
                width: 150
                model: show.atmenetek.map(function (a) { return a.nev })
                currentIndex: {
                    for (var i = 0; i < show.atmenetek.length; ++i)
                        if (show.atmenetek[i].kulcs === show.transitionKind)
                            return i
                    return 0
                }
                onActivated: show.transitionPicked(
                    show.atmenetek[currentIndex].kulcs)
            }
            //: #433: a feliratmód körbejáró gombja (felirat → fájlnév →
            //: semmi). Az eredetiben a `captionmode` beállítás; a vetítés
            //: közbeni váltás nálunk kényelmi többlet.
            PicasaButton {
                objectName: "slideshowCaptionModeButton"
                width: 34
                height: controlsRow.buttonHeight
                text: show.captionMode === "caption" ? "T"
                      : (show.captionMode === "filename" ? "F" : "—")
                onClicked: {
                    var i = show.feliratModok.indexOf(show.captionMode)
                    show.captionModePicked(
                        show.feliratModok[(i + 1) % show.feliratModok.length])
                }
            }
            PicasaButton {
                objectName: "slideshowStarButton"
                width: 34
                height: controlsRow.buttonHeight
                onClicked: show.starCurrent()
                contentItem: Text {
                    text: "★"
                    font.pixelSize: 15
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: show.photosModel
                           && (show.photosModel.revision,
                               show.photosModel.starAt(show.currentIndex))
                           //: #3070: a diavetítés a hatókörön KÍVÜL van
                           //: (11.7/3., NY-4), ezért a NYERS tokent olvassa —
                           //: a megjelenítési mód a csillagot sem színezheti át
                           ? Theme.nyers.starYellow : "#ffffff"
                    style: Text.Outline
                    styleColor: "#9a9a9a"
                }
            }

            //: #2992: a DIAIDŐ-blokk — az eredeti sávján `tpslabel`
            //: („Display Time"), `minusone`, `tps` (a szám) és `plusone`.
            //: A tulajdonos jelezte, hogy nálunk nem volt állítható.
            Row {
                objectName: "slideshowTimeBlock"
                spacing: 2
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: qsTr("Display Time")
                    color: "#ffffff"
                    font.pixelSize: Theme.fontSize - 2
                    rightPadding: 4
                }
                PicasaButton {
                    objectName: "slideshowTimeMinus"
                    width: 26
                    height: controlsRow.buttonHeight
                    text: "−"
                    //: #2992: az eredeti `oneup/minusone`-ján ott a
                    //: `Property setautorepeat 1` — a gomb NYOMVA TARTHATÓ
                    //: (`picasa-create-features.md` 2/b). Enélkül 30 mp-re
                    //: állítani 29 kattintás.
                    //: ⚠️ Az ismétlés SEBESSÉGÉT a forrás nem adja meg (csak a
                    //: jelzőt), ezért a Qt alapértelmezése marad — ez nem
                    //: mért érték.
                    autoRepeat: true
                    enabled: show.seconds > 1
                    onClicked: show.secondsChosen(show.seconds - 1)
                }
                Text {
                    objectName: "slideshowTimeValue"
                    anchors.verticalCenter: parent.verticalCenter
                    //: #3574: a mért `oneup/tps` mező 48 képpont széles, de a
                    //: kiírt „másodperc” szó abba csak olvashatatlanul apró
                    //: betűvel férne — a mező a LEGSZÉLESEBB értékhez nő, hogy
                    //: a számváltás ne rángassa a sort
                    TextMetrics {
                        id: diaidoMertek
                        font: diaidoErtek.font
                        text: "99 " + qsTr("seconds")
                    }
                    id: diaidoErtek
                    width: Math.max(48, Math.ceil(diaidoMertek.width) + 4)
                    horizontalAlignment: Text.AlignHCenter
                    //: másodperc-jelölés a szám után (az eredeti `tps` mezője)
                    //: #3574: `OneUpUI::Format` „%1$d %2$s” — a szó kiírva
                    text: show.seconds + " " + qsTr("seconds")
                    color: "#ffffff"
                    font.pixelSize: Theme.fontSize - 2
                }
                PicasaButton {
                    objectName: "slideshowTimePlus"
                    width: 26
                    height: controlsRow.buttonHeight
                    text: "+"
                    //: #2992: `oneup/plusone` — ugyanaz az auto-ismétlés,
                    //: mint a párjánál (ld. ott az indoklást).
                    autoRepeat: true
                    enabled: show.seconds < 30
                    onClicked: show.secondsChosen(show.seconds + 1)
                }
            }
        }
    }
}
