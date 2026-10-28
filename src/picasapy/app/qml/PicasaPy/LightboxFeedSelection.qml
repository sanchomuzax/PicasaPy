import QtQuick
import "lasso.js" as Lasso
import "../selection.js" as Selection

QtObject {
    id: selection
    required property var feed
    readonly property var ctl: typeof controller !== "undefined" ? controller : null
    property var lassoSnapshot: []
    property bool lassoActive: false

    // -- lasszós (gumikeretes) kijelölés ------------------
    // Az indexeket a csoport képfolyamának geometriájából
    // számoljuk (egyenletes cellák a Flow-ban); a lasszó a
    // húzás kezdő-csoportján belül jelöl ki.
    function lassoIndexes(start, count, flowWidth, x1, y1, x2, y2) {
        // #85: az oszlopszámot a névleges cellaméretből
        // számoljuk (mint a rács maga), de a képernyő-
        // koordináták bucketeléséhez a TÉNYLEGES (effektív,
        // kitöltő) cellaszélesség kell — ugyanaz a pitch,
        // amit a delegate-ek ténylegesen elfoglalnak.
        // A metszés-teszt és a soha-nem-nulla téglalap a lasso.js-ben.
        var cols = Math.max(1, Math.floor(flowWidth / feed.nominalCellWidth))
        var pitch = Math.max(1, Math.floor(flowWidth / cols))
        return Lasso.hitRows(
            Lasso.normalizedRect(x1, y1, x2, y2),
            start, count, cols, pitch, feed.cellHeight)
    }

    // #1148/#897: a húzás INDULÁSAKOR mentett kijelölés — a Shift és a
    // Ctrl ehhez viszonyít, ezért a keret visszahúzása is visszavon.
    // Az eredeti minden elem kijelöltségét elmenti (`[elem+0x5c]`,
    // `0x00719d80`–`0x00719d94`).
    // #897: az eredeti `[+0x2ce]` „lasszó aktív" jelzőjének megfelelője.
    // A gesztus kezdetét ez mondja meg — a keretsáv láthatósága NEM
    // megbízható jel (a sávot a rajzolás állítja, nem a modell).

    //: #1721 (ADR-014): a KÉZI sorrend ejtési pontja a rácson.
    //:
    //: A #3053 MÉRÉSE szerint az eredeti a lenyomáskor dönt: kép fölött,
    //: módosító nélkül HÚZÁS indul (átrendezés), módosítóval csak a
    //: kijelölés változik, üres területen LASSZÓ. A húzást nálunk a
    //: `ThumbDelegate` indítja (#455, kijelölt képről) — ez a rész az
    //: EJTÉST fogadja: kiszámolja, MELYIK kép ELÉ kerül a blokk.
    //:
    //: Az `acceptsPhotoDrag` ugyanaz a szerződés, amit az album-ejtés is
    //: használ (`AlbumsSection.qml`): a húzás „teste" a `thumbDragProxy`,
    //: és a `payload === "photos"` mondja meg, hogy fotók érkeznek.
    function acceptsPhotoDrag(drop) {
        return !!drop && !!drop.source && drop.source.payload === "photos"
    }

    /** A cél SOR-index egy ejtési pontból: a blokk EZ ELÉ kerül.
        `-1`, ha az ejtés a csoport utolsó cellája után történt — akkor a
        blokk a mappa végére megy. */
    function ejtesiCelSor(start, count, flowWidth, x, y) {
        var oszlopok = Math.max(
            1, Math.floor(flowWidth / feed.nominalCellWidth))
        var oszlop = Math.floor(x / Math.max(1, Math.floor(flowWidth / oszlopok)))
        var sor = Math.floor(y / Math.max(1, feed.cellHeight))
        if (oszlop < 0) oszlop = 0
        if (oszlop >= oszlopok) oszlop = oszlopok - 1
        var helyi = sor * oszlopok + oszlop
        if (helyi < 0) helyi = 0
        if (helyi >= count) return -1
        return start + helyi
    }

    /** Az ejtés végrehajtása: a kijelölt képek a cél ELÉ kerülnek, és a
        vezérlő kiírja az új kézi sorrendet a mappa `.picasa.ini`-jébe. */
    // #5105: a húzott képeket a saját helyükre (vagy közvetlenül az
    // összefüggő blokk mögé) ejtve a sorrend nem változik — különben egy
    // kis elhúzás és felengedés véletlenül átrendezne.
    function sajatHelyereEjtes(sorok, celSor) {
        var szamok = []
        for (var i = 0; i < sorok.length; ++i) szamok.push(Number(sorok[i]))
        szamok.sort(function(a, b) { return a - b })
        if (szamok.indexOf(celSor) >= 0) return true
        var osszefuggo =
            szamok[szamok.length - 1] - szamok[0] === szamok.length - 1
        return osszefuggo && celSor === szamok[szamok.length - 1] + 1
    }

    function ejtsdAzAtrendezest(start, count, flowWidth, x, y, photoRows) {
        if (!feed.ctl) return
        var sorok = photoRows
        if (!sorok || sorok.length === 0)
            sorok = feed.appWindow.selectedIndexes
        if (!sorok || sorok.length === 0) return
        var celSor = feed.ejtesiCelSor(start, count, flowWidth, x, y)
        if (feed.sajatHelyereEjtes(sorok, celSor)) return
        if (feed.ctl.currentAlbumToken) {
            if (typeof ctl.reorderAlbumPhotos === "function")
                ctl.reorderAlbumPhotos(sorok, celSor)
            return
        }
        if (typeof ctl.reorderPhotos === "function")
            ctl.reorderPhotos(sorok, celSor)
    }

    function beginLasso() {
        lassoSnapshot = feed.appWindow.selectedIndexes.slice()
        lassoActive = true
    }

    /** `{ picked, sel }`: a keret találatai (ebből lesz a kurzor a gesztus
        végén), és a pillanatfelvétellel összefésült végleges kijelölés. */
    function _lassoResult(start, count, flowWidth, x1, y1, x2, y2, modifiers) {
        var picked = lassoIndexes(start, count, flowWidth, x1, y1, x2, y2)
        var mods = Number(modifiers)
        return {
            picked: picked,
            sel: Lasso.merged(feed.lassoSnapshot, picked,
                              (mods & Qt.ShiftModifier) !== 0,
                              (mods & Qt.ControlModifier) !== 0)
        }
    }

    /** Húzás KÖZBEN (#897): a kijelölés minden mozdulatnál újraszámolódik
        a pillanatfelvételből — a felhasználó végig LÁTJA, mit fog be a
        keret, és a visszahúzás visszavon. ⚠️ A KURZORT (`selectedIndex`)
        szándékosan nem mozdítjuk: arra mappaváltás (`focusFolder`, #1183)
        van kötve, ami minden egérmozdulatnál elsülne — az a felengedéskor
        áll be. */
    function updateLasso(start, count, flowWidth,
                         x1, y1, x2, y2, modifiers) {
        if (!feed.lassoActive) beginLasso()
        feed.appWindow.selectedIndexes = _lassoResult(
            start, count, flowWidth, x1, y1, x2, y2, modifiers).sel
    }

    /** Felengedés: a kijelölés mellett a kurzor is a keret utolsó képére áll. */
    function applyLasso(start, count, flowWidth,
                        x1, y1, x2, y2, modifiers) {
        var r = _lassoResult(
            start, count, flowWidth, x1, y1, x2, y2, modifiers)
        feed.appWindow.selectedIndexes = r.sel
        if (r.picked.length > 0)
            feed.appWindow.selectedIndex = r.picked[r.picked.length - 1]
        feed.lassoActive = false
    }

    /** Egérkattintás egy indexképen — a rács szintjén, hogy a HORGONY
        (`selectionAnchor`) egyetlen helyen éljen (#897).

        ⚠️ EGÉRREL a Shift TARTOMÁNYT jelöl a horgonytól a kattintott
        képig (`0x0071bb34`, `[edi+0x390]`), és a horgonyt NEM lépteti;
        BILLENTYŰZETTEL viszont egyesével bővít, és a horgony lép
        (#892/#96). Az eredetiben is két külön kódút — itt sem közös.
        A Shift a Ctrl ELŐTT dönt, mint az eredetiben (`0x0071bb1f` a
        `0x0071bbeb` előtt áll).

        Horgony híján az eredeti kiszámol egyet (`0x714550`). A MI
        alapértelmezésünk: előbb a kurzor (`selectedIndex`), és ha az
        sincs, a Shift-kattintás sima kattintásként viselkedik — a
        kattintott képre szűkít, és leteszi a horgonyt. Üres nézeten a
        „kiszámolt" horgony (a lista eleje) megjósolhatatlan tartományt
        adna, a felhasználó pedig azt sem látná, honnan mérünk. */
    function applyThumbClick(index, modifiers) {
        var i = Number(index)
        var mods = Number(modifiers)
        var horgony = feed.selectionAnchor >= 0
                      ? feed.selectionAnchor : feed.appWindow.selectedIndex
        if ((mods & Qt.ShiftModifier) && horgony >= 0) {
            feed.selectionAnchor = horgony
            // #1219: a tartomány a HORGONY mappacsoportján belül marad
            var veg = feed._csoportraVagva(horgony, i)
            feed.appWindow.selectedIndexes = Selection.range(horgony, veg)
            // a kurzor a tartomány CSOPORTHATÁRRA VÁGOTT végpontjára ül
            // (a Shift+nyíl mintája) — így nem szökik át a szomszéd
            // mappába, ami a #1145 kijelölés-törlését hozná mozgásba
            feed.appWindow.selectedIndex = veg
            return
        }
        feed.appWindow.handleThumbClick(i, mods)
        feed.selectionAnchor = i
    }
}
