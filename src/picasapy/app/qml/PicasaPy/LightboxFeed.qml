import QtQuick
import QtQuick.Controls
import "groups.js" as Groups
import "lasso.js" as Lasso
import "scroll.js" as Scroll
import "../selection.js" as Selection

// Könyvtár-feed (#64, #150-ben kiemelve a Main.qml-ből): az ÖSSZES kép
// egyetlen görgethető folyamban, a bal hasáb mappa-sorrendjében —
// mappánként fejléc + képfolyam, ahogy az eredeti Picasa lightboxa.
// A kijelölés-állapot és a kattintás-logika az ApplicationWindow-é
// (appWindow); a néző/vetítés megnyitását jelekkel kéri.
ListView {
    id: grid
    objectName: "photoGrid"

    // a főablak (kijelölés-állapot + kijelölés-logika gazdája)
    required property var appWindow
    // dupla-katt vagy Enter (#1417) egy képen: néző megnyitása a sorral
    signal openRequested(int row)
    // zöld ▸ a mappa-fejlécen: vetítés a csoport első képétől
    signal slideshowRequested(int startRow)

    // #305: null-őr — a controller a QML-engine leépítésekor átmenetileg
    // null lehet, miközben ezek a kötések utoljára kiértékelődnek.
    readonly property var ctl: controller

    clip: true
    model: grid.ctl ? grid.ctl.feedGroups : []
    spacing: 14
    cacheBuffer: 600
    // #85: kiegyenlített sor-elrendezés — az oszlopszám a
    // névleges (thumbSize alapú) cellaméretből adódik, de a
    // ténylegesen kiosztott cellaszélesség (cellWidth) a
    // rendelkezésre álló szélességet tölti ki (bal–jobb
    // szél között), nem marad balra tömörült jobb sáv. A
    // ThumbDelegate a MEGJELENÍTETT képet a névleges
    // méretre plafonozza (#83 cache-minőség), a többlet a
    // cellán belüli térközbe megy.
    readonly property int nominalCellWidth: appWindow.thumbSize + 18
    readonly property int cellHeight: appWindow.thumbSize + 18
        + ((grid.ctl ? grid.ctl.thumbCaptionMode : "none") !== "none" ? 16 : 0)
    readonly property int columns:
        Math.max(1, Math.floor(width / nominalCellWidth))
    // #77-kompatibilis névalias — a navigáció-tesztek ezen
    // a néven olvassák az oszlopszámot.
    readonly property int feedColumns: columns
    readonly property int cellWidth:
        columns > 0 ? Math.floor(width / columns) : nominalCellWidth

    // -- kurzor/görgő navigáció (#77) ---------------------
    // A cél-sort a modell számolja (rácssor-ugrás, mappa-
    // csoport-határok); a kijelölés és a látótér követi. Az
    // oszlopszám a #85 szerinti effektív elrendezésből jön.
    // kijelölési horgony (#96, #897): a Shift+KATTINTÁS tartományának
    // töve; sima lépés/kattintás ide állítja vissza. A Shift+NYÍL töve
    // ezzel szemben a kurzor, és az lép (#892/#1222) — ld. selection.js
    property int selectionAnchor: -1
    function moveSelection(direction) {
        cancelRevealAfterViewer()  // #173: valódi lapozás
        var t = controller.photos.navigate(
            appWindow.selectedIndex, direction, columns)
        if (t < 0) return
        appWindow.selectedIndex = t
        appWindow.selectedIndexes = [t]
        selectionAnchor = t
        scrollToRow(t)
    }
    // Shift+nyíl (#96, #892/#1222): EGYESÉVEL bővít, és a léptetés töve
    // (a kurzor) is lép — nem tartomány, ezért az irányváltás nem
    // zsugorít. A miért: selection.js `withAdded`.
    function extendSelection(direction) {
        if (appWindow.selectedIndex < 0) {
            moveSelection(direction); return
        }
        if (selectionAnchor < 0)
            selectionAnchor = appWindow.selectedIndex
        var t = controller.photos.navigate(
            appWindow.selectedIndex, direction, columns)
        if (t < 0) return
        // #1219: a bővítés a kurzor mappacsoportjában marad
        t = _csoportraVagva(appWindow.selectedIndex, t)
        appWindow.selectedIndex = t
        appWindow.selectedIndexes = Selection.withAdded(
            appWindow.selectedIndexes, t)
        scrollToRow(t)
    }
    // a sor függőleges sávja content-koordinátában; null,
    // ha a csoport-delegate nincs példányosítva (a csoportkeresés
    // a `groups.js`-ben)
    function rowBounds(row) {
        var g = Groups.indexOfRow(model, row)
        if (g < 0) return null
        var it = itemAtIndex(g)
        if (!it) return null
        var gridRow = Math.floor(
            (row - model[g].start) / columns)
        var top = it.y + it.flowOffset + gridRow * cellHeight
        return { top: top, bottom: top + cellHeight }
    }
    // #1335: a görgethető tartományra vágott pozíció — a `wheelStep`, a
    // `scrollToRow` és a horgony-visszaállás KÖZÖS vágója. A számítás a
    // `scroll.js`-ben; ott áll az is, mit tör el a hiánya.
    function vagottY(y) {
        return Scroll.clampContentY(y, originY, contentHeight, height)
    }
    // #96: minimális görgetés — csak akkor és annyit mozdul
    // a nézet, hogy a cél-sor belógjon a látótérbe.
    // #1335: a `rowBounds` a még nem kész layoutból SZÁMOL, ezért túllőhet
    // a tartalom végén — a vágás nélkül a nézet érvénytelen helyre kerül.
    function scrollToRow(row) {
        var b = rowBounds(row)
        if (!b) {
            var g = Groups.indexOfRow(model, row)
            if (g < 0) return
            positionViewAtIndex(g, ListView.Contain)
            b = rowBounds(row)
        }
        contentY = vagottY(Scroll.rowRevealY(b, contentY, height))
        savedY = contentY
        captureAnchor()
    }
    // teszt-segéd (#95): az utolsó csoport aljának távolsága
    // a viewport tetejétől (<=0 vagy null → üres lap látszik)
    function feedEndGap() {
        var it = itemAtIndex(count - 1)
        if (!it) return null
        return it.y + it.height - contentY
    }
    // -- Home / End / PageUp / PageDown (#1147) -----------
    //
    // Az eredetiben a `CThumbUI` billentyűkezelője (`0x005c24c0`) a
    // `VK_HOME`/`VK_END`/`VK_PRIOR`/`VK_NEXT` kódokat a `CMultiAlbumNode`
    // felületére osztja (`+0x84` = `0x0076a390` Home, `+0x88` =
    // `0x0076a400` End). A nem-Ctrl ág a JELENLEGI mappa
    // kijelölés-csomópontján dolgozik, a Ctrl-ág pedig csak görget.
    // Teljes levezetés: `docs/specs/picasa-eger-es-kijeloles.md` 12.

    /** A sorhoz tartozó mappacsoport `[első, utolsó]` sorindexe, vagy
        `null`. A modelltől kérdezzük (#1219 `groupRange`), hogy a
        csoporthatár egyetlen helyen legyen kimondva. */
    function _groupRangeOfRow(row) {
        if (!grid.ctl || row < 0) return null
        var r = grid.ctl.photos.groupRange(row)
        return (r && r.length === 2) ? r : null
    }

    /** A `cel` sor a `horgony` MAPPACSOPORTJÁRA vágva (#1219) — a
        tartomány-kijelölés (nyíl, Shift-kattintás) nem lép mappahatárt. */
    function _csoportraVagva(horgony, cel) {
        var hatar = _groupRangeOfRow(horgony)
        return hatar ? Math.max(hatar[0], Math.min(hatar[1], cel)) : cel
    }

    /** A művelet hatóköre: a fókuszsor csoportja; kijelölés híján a
        JELENLEGI mappáé (az eredetiben a `[+0x2e0]` album), végül az
        első csoport. */
    function _activeGroupRange() {
        var byRow = _groupRangeOfRow(appWindow.selectedIndex)
        return byRow ? byRow : Groups.rangeOfPath(
            grid.ctl ? grid.ctl.feedGroups : null,
            grid.ctl ? grid.ctl.currentFolder : "")
    }

    /** Shift NÉLKÜL: a kijelölés a csoport szélső képére szűkül.
        Az eredetiben ez „minden kijelölés le" (`0x718a50`) + egy lépés,
        ami üres kijelölésnél az elemlista első/utolsó elemét veszi
        (`0x00717eb0`) — a látható eredmény az ugrás. */
    function jumpToGroupEdge(toEnd) {
        cancelRevealAfterViewer()
        var g = _activeGroupRange()
        if (!g) return
        var target = toEnd ? g[1] : g[0]
        appWindow.selectedIndexes = [target]
        appWindow.selectedIndex = target
        grid.selectionAnchor = target
        scrollToRow(target)
    }

    /** Shifttel: tartomány a horgonytól a csoport széléig; horgony
        nélkül a TELJES csoport (`0x716f40`). */
    function extendToGroupEdge(toEnd) {
        cancelRevealAfterViewer()
        var g = _activeGroupRange()
        if (!g) return
        var anchor = grid.selectionAnchor >= 0
                     ? grid.selectionAnchor : appWindow.selectedIndex
        // a csoporton kívüli (vagy hiányzó) horgony esetén az EGÉSZ csoport
        appWindow.selectedIndexes = (anchor >= g[0] && anchor <= g[1])
            ? Selection.range(anchor, toEnd ? g[1] : g[0])
            : Selection.range(g[0], g[1])
        appWindow.selectedIndex = toEnd ? g[1] : g[0]
        scrollToRow(appWindow.selectedIndex)
    }

    /** Ctrl-ág: csak görgetés, a kijelölés érintetlen. */
    function scrollToFeedEdge(toEnd) {
        cancelRevealAfterViewer()
        if (!toEnd) {
            positionViewAtBeginning()
        } else if (grid.model && grid.model.length > 0) {
            positionViewAtIndex(grid.model.length - 1, ListView.Beginning)
        }
        savedY = contentY
        captureAnchor()
    }

    /** PageUp/PageDown: egy viewportnyi lapozás, kijelölés nélkül —
        a görgő (`wheelStep`) mintája, csak nagyobb lépéssel. */
    function pageStep(down) {
        wheelStep(down ? -120 * Math.max(1, Math.floor(height / cellHeight))
                       : 120 * Math.max(1, Math.floor(height / cellHeight)))
    }

    Keys.onPressed: function(ev) {
        var ctrl = (ev.modifiers & Qt.ControlModifier) !== 0
        var shift = (ev.modifiers & Qt.ShiftModifier) !== 0
        if (ev.key === Qt.Key_Home || ev.key === Qt.Key_End) {
            var toEnd = ev.key === Qt.Key_End
            if (ctrl) scrollToFeedEdge(toEnd)
            else if (shift) extendToGroupEdge(toEnd)
            else jumpToGroupEdge(toEnd)
            ev.accepted = true
        } else if (ev.key === Qt.Key_PageUp || ev.key === Qt.Key_PageDown) {
            pageStep(ev.key === Qt.Key_PageDown)
            ev.accepted = true
        } else if (ev.key === Qt.Key_Return || ev.key === Qt.Key_Enter) {
            // #1417: az Enter a rács helyi menüjének FÉLKÖVÉR,
            // alapértelmezett tétele („Megjelenítés és szerkesztés\tEnter",
            // PhotoContextMenu.qml) — ugyanazt teszi, mint a dupla
            // kattintás. Kijelölés nélkül nincs mit megnyitni, olyankor az
            // eseményt sem vesszük el (mehet tovább a fókuszláncon).
            if (appWindow.selectedIndex >= 0) {
                openRequested(appWindow.selectedIndex)
                ev.accepted = true
            }
        }
    }

    /** A négy nyíl közös ága. Az eredetiben is EGY mag (`0x00717eb0`)
        szolgálja ki mindkét esetet, a Shift állapotát a hívó adja át neki
        (`0x0071728c`): Shifttel bővít (#892), enélkül léptet (#77). */
    function _arrowKey(ev, direction) {
        (ev.modifiers & Qt.ShiftModifier)
            ? extendSelection(direction) : moveSelection(direction)
    }
    Keys.onLeftPressed: function(ev) { _arrowKey(ev, "left") }
    Keys.onRightPressed: function(ev) { _arrowKey(ev, "right") }
    Keys.onUpPressed: function(ev) { _arrowKey(ev, "up") }
    Keys.onDownPressed: function(ev) { _arrowKey(ev, "down") }
    // görgő (#89): a LAPOT görgeti, mint egy dokumentumot —
    // a kijelölés nem mozdul; a rácssor-léptetés kizárólag
    // a nyilak (moveSelection) dolga. Egy görgő-kattanás
    // (120 delta) egy rácssornyit (cellHeight) mozgat, a
    // touchpad kis deltái arányosan simán görgetnek.
    function wheelStep(delta) {
        cancelRevealAfterViewer()  // #173: valódi görgetés
        var target = contentY - delta / 120 * cellHeight
        var last = itemAtIndex(count - 1)   // #95: ld. scroll.js
        if (delta < 0 && last) {
            var stopY = Scroll.feedEndStopY(
                last.y, last.height, originY, height)
            if (contentY >= stopY - 1) return
            if (target > stopY) target = stopY
        }
        contentY = vagottY(target)
        savedY = contentY
        captureAnchor()
    }

    // -- görgetés: mappára ugrás + pozíció-megőrzés --------
    // A feedGroups-frissítés (modell-csere) nullázná a
    // contentY-t; mappa-kattintásnál viszont a választott
    // csoporthoz ugrunk.
    property real savedY: 0
    property bool restoring: false
    property string pendingPath: ""
    // #17-visszajelzés: modellcsere után a nyers contentY
    // nem képezhető vissza megbízhatóan — a még nem
    // példányosított csoportok magassága BECSLÉS, így a
    // nézet „elugrott" (pl. elrejtésnél). A horgony ezért
    // szerkezeti: a viewport tetején látszó mappacsoport
    // útvonala + azon belüli eltolás; visszaálláskor
    // positionViewAtIndex (index-alapú, pontos).
    property string anchorPath: ""
    property real anchorOffset: 0
    function captureAnchor() {
        for (var i = 0; i < count; ++i) {
            var it = itemAtIndex(i)
            if (it && contentY >= it.y
                    && contentY < it.y + it.height) {
                anchorPath = model[i] ? model[i].path : ""
                anchorOffset = contentY - it.y
                return
            }
        }
    }
    // -- nézőből visszatérés: pozíció-megőrzés (#173) --------
    // A nézőt a mappa VÉGÉN álló képen megnyitva, majd
    // visszalépve a feed eddig a mappa elejére ugrott: a
    // néző-zárás resyncFolderOfRow-ja modellcserét vált ki,
    // és a SZERKEZETI horgony (restoreAnchor) a még nem kész
    // layout becsült csoport-magasságával a csoport tetejére
    // esett vissza. A megbízható visszaállás a NYERS, megnyitás
    // előtti contentY (savedY) — pontos és delegate-
    // magasságtól független. A néző-zárás ezt rögzíti, a
    // modellcsere utáni visszaállás pedig ezt (nem a horgonyt)
    // alkalmazza.
    // „Ragadós" reveal (#173): a néző-zárás resyncFolderOfRow-ja
    // HÁTTÉRSZÁLON fut, és a BEFEJEZÉSEKOR (a kék isWorking sáv
    // eltűnésekor) küld egy KÉSŐI feedChanged-et. A revealt ezért
    // NEM egyszer alkalmazzuk: a flag bekapcsolva marad, és a
    // néző-zárás utáni MINDEN feedChanged a megnyitás előtti nyers
    // pozícióra (revealTargetY) állít vissza — nem a szerkezeti
    // horgonyra, ami a még nem kész layout miatt a mappa elejére
    // ugrana. A flaget a felhasználó valódi görgetése/lapozása/
    // mappaváltása törli (cancelRevealAfterViewer).
    property bool revealAfterViewer: false
    property real revealTargetY: 0
    function beginRevealAfterViewer() {
        revealTargetY = savedY
        revealAfterViewer = true
    }
    function applyRevealAfterViewer() {
        if (!revealAfterViewer) return
        restoring = true
        contentY = vagottY(revealTargetY)
        savedY = contentY
        captureAnchor()
        restoring = false
    }
    function cancelRevealAfterViewer() {
        revealAfterViewer = false
    }
    function restoreAnchor() {
        var idx = -1
        for (var i = 0; i < model.length; ++i)
            if (model[i].path === anchorPath) { idx = i; break }
        if (idx < 0) {
            // horgony-mappa már nincs (pl. minden képe
            // rejtett) — durva pixel-visszaállás marad
            contentY = vagottY(savedY)
            savedY = contentY
            return
        }
        positionViewAtIndex(idx, ListView.Beginning)
        var it = itemAtIndex(idx)
        if (it) {
            // #1335: a horgony-cél is a görgethető tartományba vágva — a
            // csoport `y`-a a feed VÉGÉN túllóghat a maximumon (mérve:
            // contentY 277, miközben a maximum 0 volt), és a Flickable
            // csak a következő egérlenyomásra rántaná vissza.
            var maxOffset = Math.max(0, it.height - height)
            contentY = vagottY(
                it.y + Math.min(anchorOffset, maxOffset))
        }
        savedY = contentY
    }
    onContentYChanged: {
        if (!restoring && (contentY > 0 || moving)) {
            // #173: valódi felhasználói húzás/flick megszünteti
            // a néző-zárás utáni „ragadós" reveal-t
            if (moving) cancelRevealAfterViewer()
            savedY = contentY
            captureAnchor()
        }
    }
    // #173: amíg a reveal ragadós, a layout beállása
    // (delegate-ek példányosodása → contentHeight nő) újra
    // alkalmazza a mentett pozíciót — így az async resync utáni
    // fokozatos újralapozás sem hagyja a mappa elején a nézetet
    onContentHeightChanged: if (revealAfterViewer)
                                applyRevealAfterViewer()
    onMovementEnded: { savedY = contentY; captureAnchor() }
    function scrollToGroup(path) {
        cancelRevealAfterViewer()  // #173: mappaváltás
        for (var i = 0; i < model.length; ++i)
            if (model[i].path === path) {
                positionViewAtIndex(i, ListView.Beginning)
                savedY = contentY
                anchorPath = path
                anchorOffset = 0
                return
            }
    }
    Connections {
        target: controller
        function onFolderActivated(path) {
            grid.pendingPath = path
            Qt.callLater(function() {
                if (grid.pendingPath !== "") {
                    grid.scrollToGroup(grid.pendingPath)
                    grid.pendingPath = ""
                }
            })
        }
        function onFeedChanged() {
            if (grid.pendingPath !== "")
                return   // mappaválasztás — oda ugrunk úgyis
            Qt.callLater(function() {
                // nézőből visszatérve a megnyitás előtti nyers
                // pozíciót állítjuk vissza, nem a szerkezeti
                // horgonyt (#173)
                if (grid.revealAfterViewer) {
                    grid.applyRevealAfterViewer()
                    return
                }
                grid.restoring = true
                grid.restoreAnchor()
                grid.restoring = false
            })
        }
    }

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
        var cols = Math.max(1, Math.floor(flowWidth / nominalCellWidth))
        var pitch = Math.max(1, Math.floor(flowWidth / cols))
        return Lasso.hitRows(
            Lasso.normalizedRect(x1, y1, x2, y2),
            start, count, cols, pitch, cellHeight)
    }

    // #1148/#897: a húzás INDULÁSAKOR mentett kijelölés — a Shift és a
    // Ctrl ehhez viszonyít, ezért a keret visszahúzása is visszavon.
    // Az eredeti minden elem kijelöltségét elmenti (`[elem+0x5c]`,
    // `0x00719d80`–`0x00719d94`).
    property var lassoSnapshot: []
    // #897: az eredeti `[+0x2ce]` „lasszó aktív" jelzőjének megfelelője.
    // A gesztus kezdetét ez mondja meg — a keretsáv láthatósága NEM
    // megbízható jel (a sávot a rajzolás állítja, nem a modell).
    property bool lassoActive: false

    function beginLasso() {
        lassoSnapshot = appWindow.selectedIndexes.slice()
        lassoActive = true
    }

    /** `{ picked, sel }`: a keret találatai (ebből lesz a kurzor a gesztus
        végén), és a pillanatfelvétellel összefésült végleges kijelölés. */
    function _lassoResult(start, count, flowWidth, x1, y1, x2, y2, modifiers) {
        var picked = lassoIndexes(start, count, flowWidth, x1, y1, x2, y2)
        var mods = Number(modifiers)
        return {
            picked: picked,
            sel: Lasso.merged(grid.lassoSnapshot, picked,
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
        if (!grid.lassoActive) beginLasso()
        appWindow.selectedIndexes = _lassoResult(
            start, count, flowWidth, x1, y1, x2, y2, modifiers).sel
    }

    /** Felengedés: a kijelölés mellett a kurzor is a keret utolsó képére áll. */
    function applyLasso(start, count, flowWidth,
                        x1, y1, x2, y2, modifiers) {
        var r = _lassoResult(
            start, count, flowWidth, x1, y1, x2, y2, modifiers)
        appWindow.selectedIndexes = r.sel
        if (r.picked.length > 0)
            appWindow.selectedIndex = r.picked[r.picked.length - 1]
        grid.lassoActive = false
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
        var horgony = grid.selectionAnchor >= 0
                      ? grid.selectionAnchor : appWindow.selectedIndex
        if ((mods & Qt.ShiftModifier) && horgony >= 0) {
            grid.selectionAnchor = horgony
            // #1219: a tartomány a HORGONY mappacsoportján belül marad
            var veg = _csoportraVagva(horgony, i)
            appWindow.selectedIndexes = Selection.range(horgony, veg)
            // a kurzor a tartomány CSOPORTHATÁRRA VÁGOTT végpontjára ül
            // (a Shift+nyíl mintája) — így nem szökik át a szomszéd
            // mappába, ami a #1145 kijelölés-törlését hozná mozgásba
            appWindow.selectedIndex = veg
            return
        }
        appWindow.handleThumbClick(i, mods)
        grid.selectionAnchor = i
    }

    // #422: jobbklikk a rács ÜRES területén — a mappa-kontextusmenü első
    // megnyitási pontja. Az indexképek saját jobbklikk-kezelője (a
    // ThumbDelegate → openPhotoContextMenu) hamarabb elkapja az eseményt,
    // így ez tényleg csak a képek közötti/alatti üres részen fut le. A
    // célmappa a jelenleg kiválasztott (a hívó tölti ki üres útvonalnál).
    TapHandler {
        objectName: "feedEmptyAreaContextMenu"
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onSingleTapped: {
            if (grid.appWindow && grid.appWindow.openFolderContextMenu)
                grid.appWindow.openFolderContextMenu("")
        }
    }

    delegate: Column {
        id: groupCol
        required property var modelData
        width: grid.width
        spacing: 4
        // a képfolyam (Flow) függőleges eltolása a csoporton
        // belül — a sor-szintű görgetés (#96) számol vele
        readonly property real flowOffset: groupFlow.y

        LightboxHeader {
            width: parent.width
            folderName: groupCol.modelData.name
            dateText: groupCol.modelData.dateText
            description: grid.ctl
                ? (grid.ctl.descriptionRevision,
                   grid.ctl.folderDescriptionOf(groupCol.modelData.path))
                : ""
            onDescriptionEdited: function(text) {
                controller.setFolderDescriptionOf(
                    groupCol.modelData.path, text)
            }
            // #1823: a fejléc-gombok a KIJELÖLÉS darabszámát írják ki.
            selectedCount: grid.appWindow && grid.appWindow.selectedIndexes
                           ? grid.appWindow.selectedIndexes.length : 0
            // zöld ▸ (#8): a mappa vetítése az első képétől
            onPlayRequested: grid.slideshowRequested(
                groupCol.modelData.start)
            // #1823: a két új fejléc-gomb ugyanazon az úton jut a
            // gazdaablakhoz, mint a jobbklikkes mappa-menü — nem
            // vezetünk át új jelet a LightboxFeed-en, mert a művelet
            // nem a képfolyamé, hanem az ablaké.
            onSelectStarredRequested: {
                if (grid.appWindow && grid.appWindow.selectStarred)
                    grid.appWindow.selectStarred()
            }
            onSaveEditsRequested: {
                if (grid.appWindow && grid.appWindow.saveSelectedEdits)
                    grid.appWindow.saveSelectedEdits()
            }
            // #422: jobbklikk a mappa-fejlécen — a mappa-kontextusmenü
            // ARRA a mappára, amelyiknek a fejléce ez (nem a kijelöltre)
            onContextMenuRequested: {
                if (grid.appWindow && grid.appWindow.openFolderContextMenu)
                    grid.appWindow.openFolderContextMenu(
                        groupCol.modelData.path)
            }
        }

        // #142: csoporton belüli virtualizálás — a korábbi Flow +
        // Repeater { model: count } MINDEN cellát példányosított (3000
        // képes mappánál 3000 Image + thumbnail-kérés). Helyette a
        // magasság képletből adódik (sorok száma × cellHeight — így a
        // ListView becslése is pontos), és csak a látótér-közeli
        // rácssorok cellái élnek: az ablak a görgetéssel együtt csúszik,
        // a delegate-készlet mérete állandó (nincs create/destroy-vihar,
        // csak újrakötés a sorhatár-átlépéskor).
        Item {
            id: groupFlow
            width: parent.width
            readonly property int totalRows: Math.ceil(
                groupCol.modelData.count / grid.columns)
            height: totalRows * grid.cellHeight
            // a látótér teteje a csoport képfolyamának koordinátájában
            readonly property real viewTop:
                grid.contentY - groupCol.y - y
            // puffer-sorok a látótér felett/alatt — görgetés közben a
            // következő sor már készen áll
            readonly property int bufferRows: 2
            readonly property int firstRow: Math.max(0,
                Math.floor(viewTop / grid.cellHeight) - bufferRows)
            readonly property int lastRow: Math.min(totalRows - 1,
                Math.ceil((viewTop + grid.height) / grid.cellHeight)
                    + bufferRows)
            readonly property int windowStart: firstRow * grid.columns
            readonly property int windowCount: Math.max(0, Math.min(
                groupCol.modelData.count - windowStart,
                (lastRow - firstRow + 1) * grid.columns))
            // #1148: lasszó a képfolyam ÜRES részéről is. Az eredetiben a
            // lasszó ÉPP az üres területre való lenyomásra indul
            // (`0x00719d4b`) — a kijelölt képről indított húzás ott is
            // fogd-és-vidd (nálunk #455). Telített rácson a csonka utolsó
            // sor melletti sáv az egyetlen üres hely, ezért enélkül a
            // lasszó gyakorlatilag elérhetetlen volt.
            //
            // A Repeater ELŐTT áll, tehát a cellák FÖLÖTTE vannak: a
            // képre való lenyomást változatlanul a cella kezeli.
            MouseArea {
                id: flowLasso
                objectName: "feedFlowLasso"
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                // ⚠️ A ListView a függőleges húzást FLICK-nek veszi, és
                // elveheti a grabet a gyerek MouseArea-tól — a cellák
                // kezelője (ThumbDelegate) pontosan ezért `preventStealing`-el.
                preventStealing: true
                property real pressX: 0
                property real pressY: 0
                property bool huz: false
                onPressed: function(event) {
                    pressX = event.x; pressY = event.y; huz = false
                }
                onPositionChanged: function(event) {
                    if (!pressed) return
                    if (!huz && Math.abs(event.x - pressX)
                            + Math.abs(event.y - pressY) <= 8)
                        return
                    if (!huz) { huz = true; grid.beginLasso() }
                    lassoBand.update(
                        mapToItem(grid, pressX, pressY),
                        mapToItem(grid, event.x, event.y))
                    // #897: a kijelölés MÁR HÚZÁS KÖZBEN követi a keretet
                    // (a saját koordinátáink a groupFlow-éi — a terület
                    // kitölti a képfolyamot)
                    grid.updateLasso(
                        groupCol.modelData.start, groupCol.modelData.count,
                        groupFlow.width,
                        pressX, pressY, event.x, event.y, event.modifiers)
                }
                onReleased: function(event) {
                    if (!huz) {
                        // #1145/#1219: üres területre kattintva az
                        // eredeti a kijelölést TÖRLI (a mappa
                        // csomópontján), nem hagyja ott
                        grid.appWindow.clearSelection()
                        return
                    }
                    huz = false
                    lassoBand.visible = false
                    grid.applyLasso(
                        groupCol.modelData.start, groupCol.modelData.count,
                        groupFlow.width,
                        pressX, pressY, event.x, event.y, event.modifiers)
                }
            }
            Repeater {
                model: groupFlow.windowCount
                delegate: Item {
                    id: slot
                    objectName: "feedCell"
                    required property int index
                    // a cella VALÓDI helye a csoportban: az ablak eleje
                    // + a saját eltolás — görgetéskor az ablak csúszik,
                    // a delegate újrakötődik (nem újrapéldányosul)
                    readonly property int localIndex:
                        groupFlow.windowStart + slot.index
                    readonly property int row:
                        groupCol.modelData.start + slot.localIndex
                    x: (slot.localIndex % grid.columns) * grid.cellWidth
                    y: Math.floor(slot.localIndex / grid.columns)
                        * grid.cellHeight
                    // a photos.revision-nel együtt kötve:
                    // modell-frissüléskor újraértékelődik
                    // #305: null-őr — üres objektum, hogy a lenti
                    // `slot.info.X || ...` kötések ne dőljenek el
                    readonly property var info: grid.ctl
                        ? (grid.ctl.photos.revision,
                           grid.ctl.photos.itemAt(slot.row))
                        : ({})
                    width: grid.cellWidth
                    height: grid.cellHeight
                    ThumbDelegate {
                        anchors.fill: parent
                        index: slot.row
                        name: slot.info.name || ""
                        thumbUrl: slot.info.thumbUrl || ""
                        star: slot.info.star === true
                        caption: slot.info.caption || ""
                        isVideo: slot.info.isVideo === true
                        hasEdits: slot.info.hasEdits === true
                        // #463: a jelvények a ThumbDelegate-ben már
                        // megvoltak, de a FŐ RÁCS nem kötötte be őket —
                        // a geo-pin és a két arc-jelvény ezért sosem
                        // jelent meg. A mezőket a modell adja
                        // (models.py: hasGeo/hasFaces/hasFaceSuggestion).
                        hasGeo: slot.info.hasGeo === true
                        hasFaces: slot.info.hasFaces === true
                        hasFaceSuggestion: slot.info.hasFaceSuggestion === true
                        // #455: a tálcán tartott kép jelvénye — a
                        // `heldCount` a reaktív trigger (a `photos.
                        // revision` fenti mintája szerint), mert a
                        // tartott-halmaz külön jelzésen (heldChanged) fut.
                        held: grid.ctl
                              ? (grid.ctl.heldCount, grid.ctl.isHeldAt(slot.row))
                              : false
                        isHidden: slot.info.hidden === true
                        keywords: slot.info.keywords || ""
                        resolution: slot.info.resolution || ""
                        captionMode: grid.ctl ? grid.ctl.thumbCaptionMode : "none"
                        // #85/#83: a megjelenő kép a névleges
                        // méretre plafonozott, a kiegyenlítés
                        // többlete a térközbe megy.
                        maxContentWidth: grid.nominalCellWidth
                        maxContentHeight: grid.cellHeight
                        // #142: set-alapú lookup — O(1) cellánként
                        selected: grid.appWindow
                            .selectedSet[slot.row] === true
                        onChosen: function(i, mods) {
                            grid.forceActiveFocus()   // kurzorgombokhoz (#77)
                            // #897: a horgony kezelése a rácsé — a Shift
                            // EGÉRREL tartományt jelöl a horgonytól, és
                            // nem lépteti azt
                            grid.applyThumbClick(i, mods)
                        }
                        onOpened: function(i) {
                            grid.openRequested(i)
                        }
                        onLassoDragged: function(sx, sy, cx, cy, mods) {
                            // #1148/#897: a gesztus ELSŐ mozdulatánál
                            // pillanatfelvétel — a Shift/Ctrl ehhez
                            // viszonyít, ezért a keret visszahúzása is
                            // visszavon.
                            if (!grid.lassoActive) grid.beginLasso()
                            lassoBand.update(
                                mapToItem(grid, sx, sy),
                                mapToItem(grid, cx, cy))
                            // #897: a kijelölés húzás közben is követ
                            var a = mapToItem(groupFlow, sx, sy)
                            var b = mapToItem(groupFlow, cx, cy)
                            grid.updateLasso(
                                groupCol.modelData.start,
                                groupCol.modelData.count,
                                groupFlow.width,
                                a.x, a.y, b.x, b.y, mods)
                        }
                        onLassoFinished: function(sx, sy, cx, cy, mods) {
                            var a = mapToItem(groupFlow, sx, sy)
                            var b = mapToItem(groupFlow, cx, cy)
                            grid.applyLasso(
                                groupCol.modelData.start,
                                groupCol.modelData.count,
                                groupFlow.width,
                                a.x, a.y, b.x, b.y, mods)
                            lassoBand.visible = false
                        }
                        onContextMenuRequested: function(i, cx, cy) {
                            grid.appWindow.openPhotoContextMenu(
                                i, slot, cx, cy)
                        }
                    }
                }
            }

            // #1808: RÁCS-NAGYÍTÓ (`thumbui/loupehit`, „Click and drag
            // over photos to magnify them"). A cellák FÖLÖTT áll, tehát
            // amíg be van kapcsolva, ELNYELI a rács egéreseményeit — a
            // húzás így nem jelöl ki és nem lasszóz, ahogy az eredetiben
            // sem: a nagyító a nézés eszköze, nem a válogatásé.
            //
            // A cella-kiszámítás UGYANAZ az aritmetika, amit a lasszó is
            // használ (`columns`, `cellWidth/cellHeight`) — a képfolyamon
            // belül a hely egyértelműen adja a sorszámot.
            MouseArea {
                id: loupeArea
                objectName: "feedLoupeArea"
                anchors.fill: parent
                enabled: grid.appWindow ? grid.appWindow.loupeActive === true
                                        : false
                visible: loupeArea.enabled
                acceptedButtons: Qt.LeftButton
                preventStealing: true
                hoverEnabled: false

                //: A nagyítás mértéke. ⚠️ SAJÁT DÖNTÉS, nem mért érték: az
                //: eredeti nagyító arányait a bináris nem árulja el (a
                //: `0x0077be10` a két csomópontnévnél többet nem hivatkoz).
                //: Két és félszeres nagyítás annyi, hogy az élesség és a
                //: csukott szem eldönthető legyen, de a lencse még ne
                //: takarja el a fél rácsot.
                readonly property real nagyitas: 2.5

                property int aktivSor: -1
                property real kurzorX: 0
                property real kurzorY: 0

                function sorItt(x, y) {
                    if (grid.columns <= 0) return -1
                    var oszlop = Math.floor(x / grid.cellWidth)
                    if (oszlop < 0 || oszlop >= grid.columns) return -1
                    var sor = Math.floor(y / grid.cellHeight)
                    if (sor < 0) return -1
                    var helyi = sor * grid.columns + oszlop
                    if (helyi < 0 || helyi >= groupCol.modelData.count)
                        return -1
                    return groupCol.modelData.start + helyi
                }

                function frissits(x, y) {
                    loupeArea.kurzorX = x
                    loupeArea.kurzorY = y
                    loupeArea.aktivSor = loupeArea.sorItt(x, y)
                }

                onPressed: function (event) { loupeArea.frissits(event.x, event.y) }
                onPositionChanged: function (event) {
                    if (!pressed) return
                    loupeArea.frissits(event.x, event.y)
                }
                //: Elengedésre eltűnik — a nagyító nem hagy nyomot, és a
                //: képet NEM nyitja meg.
                onReleased: loupeArea.aktivSor = -1
                onCanceled: loupeArea.aktivSor = -1

                Item {
                    id: loupe
                    objectName: "feedLoupe"

                    //: #1951 (spec `racs-nagyito.md` 4.): a vászon MÉRT
                    //: mérete `loupe/docbounds` — **fix 103 × 103**, NEM a
                    //: rács cellájához kötött. A cellához kötött méret a
                    //: nagyítás-csúszkával együtt változna; az eredetiben
                    //: a lencse mérete állandó.
                    readonly property int vaszon: 103

                    //: Az áttűnés két időtartama (spec 3.1).
                    //:
                    //: ⚠️ Az EGYSÉG nincs mérve: az eredeti `0,4` és `1,2`
                    //: a saját órájának egységében értendő, és a
                    //: binárisból nem derül ki, hogy másodperc-e. **Ami
                    //: mérve van: az ARÁNY — az eltűnés pontosan
                    //: háromszor hosszabb.** Az abszolút ezredmásodperc a
                    //: MI választásunk; az arányt az őr-teszt rögzíti.
                    readonly property int megjelenesMs: 120
                    readonly property int eltunesMs: 360

                    //: #1951: a láthatóság ÁTTŰNÉSSEL vált — az eredeti
                    //: nem ugrasztja be a lencsét (spec 3.2: az
                    //: átlátszatlanság 0→256 skálán, 1 és 256 közé vágva).
                    readonly property bool kell:
                        loupeArea.pressed && loupeArea.aktivSor >= 0
                    visible: opacity > 0
                    opacity: kell ? 1.0 : 0.0
                    Behavior on opacity {
                        NumberAnimation {
                            duration: loupe.kell ? loupe.megjelenesMs
                                                 : loupe.eltunesMs
                            easing.type: Easing.InOutQuad
                        }
                    }

                    width: loupe.vaszon
                    height: loupe.vaszon
                    //: #1951: a lencse a kurzor KÖZEPÉN ül (`0x0077b780`:
                    //: a kapott téglalap két méretét 0,5-tel szorozza),
                    //: nem fölötte. A KÉPFOLYAMON belül marad — a rács
                    //: szélén sem lóg ki (#1808); a `clamp` mindkét
                    //: irányban dolgozik.
                    x: Math.max(0, Math.min(groupFlow.width - loupe.width,
                                            loupeArea.kurzorX - loupe.width / 2))
                    y: Math.max(0, Math.min(groupFlow.height - loupe.height,
                                            loupeArea.kurzorY - loupe.height / 2))

                    //: #1951: KÖR, nem téglalap — az eredeti egy
                    //: üveglencse (spec 4.: `loupe/loupe` 103 × 103,
                    //: belső átlátszó átmérő 65, NULLA teljesen fedő
                    //: képponttal, tehát végig áttetsző).
                    Rectangle {
                        objectName: "feedLoupeRing"
                        anchors.fill: parent
                        color: Theme.contentPanel
                        border.width: 1
                        border.color: Theme.chromeBorder
                        radius: width / 2
                    }
                    Image {
                        objectName: "feedLoupeImage"
                        anchors.fill: parent
                        //: a gyűrű vastagsága: a 103-as vászon és a mért
                        //: 65-ös belső átlátszó átmérő különbsége felezve
                        //:
                        //: ⚠️ Ez a margó tartja a képet a KÖRÖN BELÜL,
                        //: shader nélkül. A `QtQuick.Effects` (kör-maszk)
                        //: szándékosan nincs a projektben — ld.
                        //: `CollageSheet.qml`. Számolva: a 65 × 65-ös kép
                        //: sarka a középponttól `65/2·√2 = 46,0`-ra van, a
                        //: kör sugara `103/2 = 51,5` ⇒ a sarkok NEM lógnak
                        //: ki. A margó csökkentése ezt elrontaná: 73 fölötti
                        //: képméretnél a sarkok kibújnának a körből.
                        anchors.margins: (loupe.vaszon - 65) / 2
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        //: A nagyított kép NAGYOBB felbontással kérődik le,
                        //: különben a bélyegkép képpontjait nagyítanánk fel
                        //: (a nagyító épp az élesség eldöntésére való).
                        sourceSize.width: Math.round(loupe.width)
                        sourceSize.height: Math.round(loupe.height)
                        source: {
                            if (!grid.ctl || loupeArea.aktivSor < 0) return ""
                            var elem = (grid.ctl.photos.revision,
                                        grid.ctl.photos.itemAt(loupeArea.aktivSor))
                            return elem && elem.thumbUrl ? elem.thumbUrl : ""
                        }
                    }
                }
            }
        }
    }
    ScrollBar.vertical: PicasaScrollBar { objectName: "feedScrollBar" }

    // görgő-elfogó réteg (#77/#89): a wheel-eseményt egy a
    // rács fölött ülő átlátszó réteg kapja el (pointer-
    // handler Flickable-ben nem támogatott), és lapgörgetéssé
    // (wheelStep → contentY) alakítja; kattintás és lasszó
    // átmegy rajta (csak görgőt kezel).
    Item {
        parent: grid
        anchors.fill: parent
        z: 15
        WheelHandler {
            acceptedDevices: PointerDevice.Mouse
                             | PointerDevice.TouchPad
            onWheel: function(event) {
                grid.wheelStep(event.angleDelta.y)
            }
        }
    }

    // gumikeret-vizualizáció
    Rectangle {
        id: lassoBand
        visible: false
        z: 10
        color: "#33009eff"
        border.color: Theme.thumbSelection
        border.width: 1
        function update(a, b) {
            x = Math.min(a.x, b.x); y = Math.min(a.y, b.y)
            width = Math.abs(a.x - b.x)
            height = Math.abs(a.y - b.y)
            visible = true
        }
    }
}
