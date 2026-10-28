import QtQuick
import QtQuick.Controls
import "groups.js" as Groups
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
    //: #3463: a Shift+F1 fejezete (ld. `Main.qml` `helpTopicUnderCursor`)
    property string helpTopic: "features/konyvtar.md"

    // a főablak (kijelölés-állapot + kijelölés-logika gazdája)
    required property var appWindow
    // dupla-katt vagy Enter (#1417) egy képen: néző megnyitása a sorral
    signal openRequested(int row)
    // zöld ▸ a mappa-fejlécen: vetítés a csoport első képétől
    signal slideshowRequested(int startRow)
    // #5008: a forrásból érkező képsorokat rendezzük, ne a pillanatnyi
    // kijelölést; album-feedben ugyanez az albumorder kulcsot írja.
    signal photoRowsDroppedOnReorder(
        int start, int count, real flowWidth, real x, real y, var photoRows)
    onPhotoRowsDroppedOnReorder: function(
        start, count, flowWidth, x, y, photoRows) {
        grid.ejtsdAzAtrendezest(
            start, count, flowWidth, x, y, photoRows)
    }

    // Ctrl+Alt alatt a kijelölt (aktuális) kép lesz a külön PopDisplay-ablak
    // képe. A mutató alatti cella nem módosítja ezt a képforrást.
    readonly property int currentPreviewRow:
        grid.appWindow && grid.appWindow.selectedIndex !== undefined
        ? Number(grid.appWindow.selectedIndex) : -1
    readonly property var currentPreviewPhoto: {
        if (!grid.ctl || !grid.ctl.photos || grid.currentPreviewRow < 0)
            return ({})
        return grid.ctl.photos.itemAt(grid.currentPreviewRow) || ({})
    }
    readonly property string currentPreviewSource: {
        if (!grid.ctl || !grid.ctl.photos || grid.currentPreviewRow < 0)
            return ""
        return grid.ctl.hoverPreviewFileUrlAt(grid.currentPreviewRow)
    }

    // #305: null-őr — a controller a QML-engine leépítésekor átmenetileg
    // null lehet, miközben ezek a kötések utoljára kiértékelődnek.
    readonly property var ctl: controller
    readonly property bool personAlbumMode:
        grid.appWindow && grid.appWindow.personAlbumName !== ""

    function alignPersonAlbumHeader() {
        grid.restoring = true
        grid.contentY = grid.originY
        grid.savedY = grid.contentY
        grid.captureAnchor()
        grid.restoring = false
    }
    onPersonAlbumModeChanged: Qt.callLater(function() {
        grid.alignPersonAlbumHeader()
    })

    // A külső fájlhúzás a kijelölés teljes fájllistáját adja át, nem csak
    // azt az indexképet, amelyről a mozdulat elindult.
    function selectedFileUriList() {
        if (!grid.ctl || !grid.ctl.photos || !grid.appWindow
            || !grid.appWindow.selectedIndexes
            || typeof grid.ctl.fileUriList !== "function")
            return ""
        var paths = []
        var indexes = grid.appWindow.selectedIndexes
        for (var i = 0; i < indexes.length; ++i) {
            var path = grid.ctl.photos.filePathAt(Number(indexes[i]))
            if (path) paths.push(path)
        }
        return grid.ctl.fileUriList(paths)
    }

    // #3751: a mentés-üzemmód — a `BackupHost` állítja (`Main.qml`-en át),
    // amíg a mentés-panel látszik. A rács TARTALMÁT nem itt szűrjük: a
    // vezérlő szűkíti a `photos`/`feedGroups` párost a még el nem mentett
    // fájlokra (`setBackupFilter`), így a sorindexek, a navigáció és a néző
    // lapozása is a szűrt listán dolgozik. Ez a három bemenet csak a rács
    // közepén álló feliratot dönti el.
    property bool mentesSzuroAktiv: false
    //: a mentetlen fájlok listája háttérszálon készül — addig a vezérlő a
    //: rács RÉGI tartalmát hagyja állni (`BackupHost.racsSzurod`), a felirat
    //: pedig nem mondhatja, hogy minden el van mentve
    property bool mentesToltodnek: false
    //: van-e kiválasztott mentési készlet — nélküle a „minden el van
    //: mentve" felirat hamis volna (a `FolderPane` azonos bemenete)
    property bool mentesVanKeszlet: false

    // A görgetés utáni irányt és célterületet a rövid késleltetésű előtöltő
    // használja. A Timer az utolsó mozdulás után egyszer indít egy teljes
    // képernyőnyi háttérmunkát, nem minden képpontra külön.
    property real prefetchLastContentY: 0
    property int prefetchScrollDirection: 1

    LightboxFeedHoverPreview { feed: grid }


    clip: true
    model: grid.ctl ? grid.ctl.feedGroups : []

    LightboxFeedEmptyState { feed: grid }

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

    function prefetchInScrollDirection() {
        if (!grid.ctl || grid.columns <= 0 || grid.cellHeight <= 0)
            return
        var firstVisible = Number.MAX_VALUE
        var lastVisible = -1
        var middleIndex = grid.indexAt(grid.width / 2, grid.height / 2)
        var radius = Math.ceil(grid.height / grid.cellHeight) + 2
        var firstGroup = Math.max(0, middleIndex - radius)
        var lastGroup = Math.min(grid.count - 1, middleIndex + radius)
        for (var i = firstGroup; i <= lastGroup; ++i) {
            var group = grid.itemAtIndex(i)
            if (!group || !group.visiblePhotoRange)
                continue
            var visible = group.visiblePhotoRange()
            if (!visible)
                continue
            firstVisible = Math.min(firstVisible, visible.first)
            lastVisible = Math.max(lastVisible, visible.last)
        }
        if (lastVisible < 0)
            return

        var screenCount = Math.ceil(grid.height / grid.cellHeight)
            * grid.columns
        if (grid.prefetchScrollDirection > 0) {
            grid.ctl.prefetchThumbnails(lastVisible + 1, screenCount, false)
        } else {
            var start = Math.max(0, firstVisible - screenCount)
            grid.ctl.prefetchThumbnails(
                start, firstVisible - start, true)
        }
    }

    Timer {
        id: thumbnailPrefetchTimer
        interval: 100
        repeat: false
        onTriggered: grid.prefetchInScrollDirection()
    }

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
    //: #857: ugrás a szomszédos albumra (mappára). A feed MODELLJE maga a
    //: csoportlista (`feedGroups`), tehát az ugrás a szomszédos csoport
    //: elejére pozicionál — nem sorral lépünk, hanem albumot váltunk.
    //:
    //: A „hol állunk" kérdésre a LÁTHATÓ tető válaszol: az a csoport, amelyik
    //: még belelóg a nézetbe. Lefelé ennek a KÖVETKEZŐJE a cél, felfelé pedig
    //: — ha már a tetején állunk — az ELŐZŐ; különben a saját eleje. Így a
    //: „fel" gomb először a jelenlegi album elejére visz, ahogy az eredeti
    //: görgetősávján is.
    function aktualisCsoport() {
        if (!model || model.length === 0)
            return -1
        for (var i = 0; i < model.length; i++) {
            var it = itemAtIndex(i)
            if (it && it.y + it.height > contentY + 1)
                return i
        }
        return model.length - 1
    }

    function ugrasAlbumra(irany) {
        if (!model || model.length === 0)
            return
        var most = aktualisCsoport()
        if (most < 0)
            return
        var cel = most
        if (irany > 0) {
            cel = Math.min(model.length - 1, most + 1)
        } else {
            var it = itemAtIndex(most)
            var tetejen = it && Math.abs(it.y - contentY) <= 1
            cel = tetejen ? Math.max(0, most - 1) : most
        }
        positionViewAtIndex(cel, ListView.Beginning)
        savedY = contentY
    }

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
    //: #3751: a csoportok közti térköz (`spacing`) a FELETTE álló csoporthoz
    //: tartozik — enélkül a térközben álló nézet horgonya a régi (vagy üres)
    //: maradt, és a visszaállás rossz helyre ugrott. Mérve: DejaVu betűvel
    //: a csoportok `305+291`, `610+…` helyen álltak, a 600 a résbe esett.
    function captureAnchor() {
        for (var i = 0; i < count; ++i) {
            var it = itemAtIndex(i)
            if (it && contentY >= it.y
                    && contentY < it.y + it.height + spacing) {
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
        if (contentY !== prefetchLastContentY) {
            prefetchScrollDirection = contentY > prefetchLastContentY ? 1 : -1
            prefetchLastContentY = contentY
            thumbnailPrefetchTimer.restart()
        }
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
            if (grid.personAlbumMode) {
                Qt.callLater(function() { grid.alignPersonAlbumHeader() })
                return
            }
            if (grid.pendingPath !== "")
                return   // mappaválasztás — oda ugrunk úgyis
            // #3751: a mentés-szűrő új tartalma (bekapcsolás, másik
            // készlet, újraszámolás) a rács tetejéről indul
            var tetejere = grid.mentesTetejere
            grid.mentesTetejere = false
            Qt.callLater(function() {
                if (tetejere) {
                    grid.restoring = true
                    grid.contentY = grid.vagottY(grid.originY)
                    grid.savedY = grid.contentY
                    grid.captureAnchor()
                    grid.restoring = false
                    return
                }
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

    // -- mentés-üzemmód: a görgetési helyzet megőrzése (#3751) ----
    // A mentés-szűrő modellcsere: az új szűrt tartalom (bekapcsolás, másik
    // készlet, újraszámolás) a tetejéről indul, bezáráskor pedig a MEGNYITÁS
    // ELŐTTI helyzet áll vissza — nem a szűrt rácson utoljára látott
    // horgony. A vezérlő új szűrőnél a `feedChanged` ELŐTT, kikapcsoláskor
    // UTÁNA jelez; a visszaállítás ezért a `feedChanged` saját
    // visszaállítása után fut (`Qt.callLater` sorrend).
    property bool mentesTetejere: false
    property var mentesElottiHelyzet: null
    function mentesSzuroValtott(aktiv) {
        if (aktiv) {
            cancelRevealAfterViewer()
            if (!mentesElottiHelyzet)
                mentesElottiHelyzet = {
                    path: anchorPath, offset: anchorOffset, y: savedY }
            // a jelzőt a `feedChanged` szinkron kezelője fogyasztja el; ha
            // a szűrő nem változtatott a rácson, ne maradjon élesítve
            mentesTetejere = true
            Qt.callLater(function() { grid.mentesTetejere = false })
            return
        }
        mentesTetejere = false
        var helyzet = mentesElottiHelyzet
        mentesElottiHelyzet = null
        if (!helyzet) return
        Qt.callLater(function() { grid.mentesHelyzetVissza(helyzet) })
    }
    //: A `restoreAnchor` a horgony-eltolást a csoport magasságára vágja
    //: (#1335) — rövid mappánál ettől a csoport tetejére ugrana. Itt a
    //: rács tartalma ugyanaz, mint a megnyitás előtt, tehát a teljes
    //: eltolás visszaállítható; a görgethető tartományra a `vagottY` vág.
    //:
    //: A vágás előtt a nézet a nyers célra áll: a ListView csak a látótérben
    //: álló csoportokat példányosítja azonnal, a többi magasságát átlagból
    //: BECSLI, így a `contentHeight` a visszaállás pillanatában jóval kisebb
    //: lehet a valódinál. Mérve (DejaVu betűvel, a 48 képes csoport még nem
    //: élt): `contentHeight` 901 a valódi 2035 helyett, a vágás a 600-as
    //: célt 439-re tette, és a delegate-ek beérkezése után is ott maradt
    //: (a CI ubuntu-lábán ugyanígy 428). A célra
    //: állás a cél körüli csoportokat szinkron példányosítja — utána a
    //: `vagottY` már a valódi magasságra vág.
    function mentesHelyzetVissza(helyzet) {
        restoring = true
        var idx = -1
        for (var i = 0; i < model.length; ++i)
            if (model[i].path === helyzet.path) { idx = i; break }
        var cel = helyzet.y
        if (idx >= 0) {
            positionViewAtIndex(idx, ListView.Beginning)
            var it = itemAtIndex(idx)
            if (it) cel = it.y + helyzet.offset
        }
        contentY = cel
        contentY = vagottY(cel)
        savedY = contentY
        captureAnchor()
        restoring = false
    }
    Connections {
        target: grid.ctl
        //: a próbák stub-vezérlőjén a jelzés nincs meg
        ignoreUnknownSignals: true
        function onBackupFilterChanged() {
            grid.mentesSzuroValtott(grid.ctl.backupFilterActive === true)
        }
    }

    // A lasszó és a kézi sorrend kezelése külön komponensben él; a meglévő
    // QML-nevek és hívófelület a rácson maradnak.
    property alias lassoSnapshot: feedSelection.lassoSnapshot
    property alias lassoActive: feedSelection.lassoActive
    LightboxFeedSelection { id: feedSelection; feed: grid }
    function lassoIndexes(start, count, flowWidth, x1, y1, x2, y2) {
        return feedSelection.lassoIndexes(start, count, flowWidth, x1, y1, x2, y2)
    }
    function acceptsPhotoDrag(drop) {
        return feedSelection.acceptsPhotoDrag(drop)
    }
    function ejtesiCelSor(start, count, flowWidth, x, y) {
        return feedSelection.ejtesiCelSor(start, count, flowWidth, x, y)
    }
    function sajatHelyereEjtes(sorok, celSor) {
        return feedSelection.sajatHelyereEjtes(sorok, celSor)
    }
    function ejtsdAzAtrendezest(start, count, flowWidth, x, y, photoRows) {
        return feedSelection.ejtsdAzAtrendezest(
            start, count, flowWidth, x, y, photoRows)
    }
    function beginLasso() { feedSelection.beginLasso() }
    function _lassoResult(start, count, flowWidth, x1, y1, x2, y2, modifiers) {
        return feedSelection._lassoResult(
            start, count, flowWidth, x1, y1, x2, y2, modifiers)
    }
    function updateLasso(start, count, flowWidth,
                         x1, y1, x2, y2, modifiers) {
        feedSelection.updateLasso(
            start, count, flowWidth, x1, y1, x2, y2, modifiers)
    }
    function applyLasso(start, count, flowWidth,
                        x1, y1, x2, y2, modifiers) {
        feedSelection.applyLasso(
            start, count, flowWidth, x1, y1, x2, y2, modifiers)
    }
    function applyThumbClick(index, modifiers) {
        feedSelection.applyThumbClick(index, modifiers)
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

    delegate: LightboxFeedGroup {
        feed: grid
        lassoOverlay: lassoBand
    }


    // A személyalbum saját fejlécet és arcsávot kap; utána a normál feed
    // mappacsoportjai következnek, ezért minden kép a mappájában marad.
    header: LightboxFeedPersonHeader { feed: grid }


    //: #857 (ADR-015): a rács sávja az EGYETLEN, ahol az album-ugrásnak
    //: értelme van — a mappafa és a párbeszédek sávja változatlan marad.
    ScrollBar.vertical: PicasaScrollBar {
        objectName: "feedScrollBar"
        albumUgras: true
        onElozoAlbum: grid.ugrasAlbumra(-1)
        onKovetkezoAlbum: grid.ugrasAlbumra(1)
    }

    LightboxFeedWheelArea { feed: grid }
    LightboxFeedLassoBand { id: lassoBand }

}
