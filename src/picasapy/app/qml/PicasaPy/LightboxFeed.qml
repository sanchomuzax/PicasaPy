import QtQuick
import QtQuick.Controls

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
    // dupla-katt egy képen: néző megnyitása a sorral
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
    // kijelölési horgony (#96): a Shift+nyíl tartomány
    // kezdőpontja; sima lépés/kattintás ide állítja vissza
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
    // Shift+nyíl (#96): a horgony és a cél-index közti
    // tartomány kijelölése; visszafelé lépve szűkül
    function extendSelection(direction) {
        if (appWindow.selectedIndex < 0) {
            moveSelection(direction); return
        }
        if (selectionAnchor < 0)
            selectionAnchor = appWindow.selectedIndex
        var t = controller.photos.navigate(
            appWindow.selectedIndex, direction, columns)
        if (t < 0) return
        appWindow.selectedIndex = t
        // #1219: a tartomány a horgony mappacsoportjára szorítva
        var hatar = controller.photos.groupRange(selectionAnchor)
        var vegpont = t
        if (hatar.length === 2)
            vegpont = Math.max(hatar[0], Math.min(hatar[1], t))
        var lo = Math.min(selectionAnchor, vegpont)
        var hi = Math.max(selectionAnchor, vegpont)
        var sel = []
        for (var r = lo; r <= hi; ++r) sel.push(r)
        appWindow.selectedIndexes = sel
        scrollToRow(t)
    }
    function groupOfRow(row) {
        for (var i = 0; i < model.length; ++i)
            if (row >= model[i].start
                && row < model[i].start + model[i].count)
                return i
        return -1
    }
    // a sor függőleges sávja content-koordinátában; null,
    // ha a csoport-delegate nincs példányosítva
    function rowBounds(row) {
        var g = groupOfRow(row)
        if (g < 0) return null
        var it = itemAtIndex(g)
        if (!it) return null
        var gridRow = Math.floor(
            (row - model[g].start) / columns)
        var top = it.y + it.flowOffset + gridRow * cellHeight
        return { top: top, bottom: top + cellHeight }
    }
    // #96: minimális görgetés — csak akkor és annyit mozdul
    // a nézet, hogy a cél-sor belógjon a látótérbe
    function scrollToRow(row) {
        var b = rowBounds(row)
        if (!b) {
            var g = groupOfRow(row)
            if (g < 0) return
            positionViewAtIndex(g, ListView.Contain)
            b = rowBounds(row)
            if (!b) { savedY = contentY; return }
        }
        if (b.bottom > contentY + height)
            contentY = b.bottom - height
        else if (b.top < contentY)
            contentY = b.top
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

    /** A művelet hatóköre: a fókuszsor csoportja; kijelölés híján a
        JELENLEGI mappáé (az eredetiben a `[+0x2e0]` album), végül az
        első csoport. */
    function _activeGroupRange() {
        var byRow = _groupRangeOfRow(appWindow.selectedIndex)
        if (byRow) return byRow
        var groups = grid.ctl ? grid.ctl.feedGroups : null
        if (!groups || groups.length === 0) return null
        var current = grid.ctl.currentFolder
        for (var i = 0; i < groups.length; ++i)
            if (groups[i].path === current)
                return [groups[i].start,
                        groups[i].start + groups[i].count - 1]
        return [groups[0].start, groups[0].start + groups[0].count - 1]
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
        var from, to
        if (anchor < 0 || anchor < g[0] || anchor > g[1]) {
            from = g[0]; to = g[1]          // horgony nélkül: az egész
        } else {
            from = Math.min(anchor, toEnd ? g[1] : g[0])
            to = Math.max(anchor, toEnd ? g[1] : g[0])
        }
        var sel = []
        for (var r = from; r <= to; ++r) sel.push(r)
        appWindow.selectedIndexes = sel
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
        }
    }

    Keys.onLeftPressed: function(ev) {
        (ev.modifiers & Qt.ShiftModifier)
            ? extendSelection("left") : moveSelection("left")
    }
    Keys.onRightPressed: function(ev) {
        (ev.modifiers & Qt.ShiftModifier)
            ? extendSelection("right") : moveSelection("right")
    }
    Keys.onUpPressed: function(ev) {
        (ev.modifiers & Qt.ShiftModifier)
            ? extendSelection("up") : moveSelection("up")
    }
    Keys.onDownPressed: function(ev) {
        (ev.modifiers & Qt.ShiftModifier)
            ? extendSelection("down") : moveSelection("down")
    }
    // görgő (#89): a LAPOT görgeti, mint egy dokumentumot —
    // a kijelölés nem mozdul; a rácssor-léptetés kizárólag
    // a nyilak (moveSelection) dolga. Egy görgő-kattanás
    // (120 delta) egy rácssornyit (cellHeight) mozgat, a
    // touchpad kis deltái arányosan simán görgetnek.
    function wheelStep(delta) {
        cancelRevealAfterViewer()  // #173: valódi görgetés
        var target = contentY - delta / 120 * cellHeight
        // #95: a contentHeight a nem-példányosított csopor-
        // toknál BECSLÉS — túllőhet a valós tartalom-végen,
        // és üres lapra engedne. Az utolsó csoport VALÓS
        // alja állít meg, amint példányosítva van.
        var last = itemAtIndex(count - 1)
        if (delta < 0 && last) {
            var stopY = Math.max(
                originY, last.y + last.height - height)
            if (contentY >= stopY - 1) return
            if (target > stopY) target = stopY
        }
        var maxY = originY + Math.max(0, contentHeight - height)
        contentY = Math.max(originY, Math.min(target, maxY))
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
        contentY = Math.min(
            revealTargetY, Math.max(0, contentHeight - height))
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
            contentY = Math.min(
                savedY, Math.max(0, contentHeight - height))
            savedY = contentY
            return
        }
        positionViewAtIndex(idx, ListView.Beginning)
        var it = itemAtIndex(idx)
        if (it) {
            var maxOffset = Math.max(0, it.height - height)
            contentY = it.y
                + Math.min(anchorOffset, maxOffset)
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
        var cols = Math.max(1, Math.floor(flowWidth / nominalCellWidth))
        var pitch = cols > 0 ? Math.floor(flowWidth / cols) : nominalCellWidth
        var left = Math.min(x1, x2), right = Math.max(x1, x2)
        var top = Math.min(y1, y2), bottom = Math.max(y1, y2)
        // #1148: az elemteszt METSZÉS, szigorúan pozitív területtel
        // (`0x0071bc90`, `0x0071bef7`–`0x0071bf25`) — nem cella-bucket.
        // A különbség a határon látszik: a cellahatárra PONTOSAN illesztett
        // keret a szomszédot nem fogja be (nulla területű érintés), egy
        // képpontnyi átlógás viszont igen.
        var c0 = Math.max(0, Math.floor(left / pitch))
        var c1 = Math.min(cols - 1, Math.floor(right / pitch))
        var r0 = Math.max(0, Math.floor(top / cellHeight))
        var r1 = Math.floor(bottom / cellHeight)
        var result = []
        for (var r = r0; r <= r1; ++r)
            for (var c = c0; c <= c1; ++c) {
                var idx = r * cols + c
                if (idx < 0 || idx >= count) continue
                var cellLeft = c * pitch, cellTop = r * cellHeight
                if (left < cellLeft + pitch && right > cellLeft
                        && top < cellTop + cellHeight && bottom > cellTop)
                    result.push(start + idx)
            }
        return result
    }

    // #1148/#897: a húzás INDULÁSAKOR mentett kijelölés — a Shift és a
    // Ctrl ehhez viszonyít, ezért a keret visszahúzása is visszavon.
    // Az eredeti minden elem kijelöltségét elmenti (`[elem+0x5c]`,
    // `0x00719d80`–`0x00719d94`).
    property var lassoSnapshot: []
    function beginLasso() {
        lassoSnapshot = appWindow.selectedIndexes.slice()
    }
    function applyLasso(start, count, flowWidth,
                        x1, y1, x2, y2, modifiers) {
        var picked = lassoIndexes(
            start, count, flowWidth, x1, y1, x2, y2)
        var mods = Number(modifiers)
        var base = grid.lassoSnapshot || []
        var sel
        if (mods & Qt.ShiftModifier) {
            // Shift: HOZZÁFŰZ a felvételkori kijelöléshez
            sel = base.slice()
            for (var i = 0; i < picked.length; ++i)
                if (sel.indexOf(picked[i]) < 0) sel.push(picked[i])
        } else if (mods & Qt.ControlModifier) {
            // Ctrl: a keretbe esők a FELVÉTELKORI állapotukhoz képest
            // fordulnak — visszahúzáskor visszaáll az eredeti (#897)
            sel = []
            for (var j = 0; j < base.length; ++j)
                if (picked.indexOf(base[j]) < 0) sel.push(base[j])
            for (var k = 0; k < picked.length; ++k)
                if (base.indexOf(picked[k]) < 0) sel.push(picked[k])
        } else {
            sel = picked
        }
        appWindow.selectedIndexes = sel
        if (picked.length > 0)
            appWindow.selectedIndex = picked[picked.length - 1]
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
            // zöld ▸ (#8): a mappa vetítése az első képétől
            onPlayRequested: grid.slideshowRequested(
                groupCol.modelData.start)
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
                            grid.selectionAnchor = i  // Shift+nyíl horgony (#96)
                            grid.appWindow.handleThumbClick(i, mods)
                        }
                        onOpened: function(i) {
                            grid.openRequested(i)
                        }
                        onLassoDragged: function(sx, sy, cx, cy) {
                            // #1148/#897: a gesztus ELSŐ mozdulatánál
                            // pillanatfelvétel — a Shift/Ctrl ehhez
                            // viszonyít, ezért a keret visszahúzása is
                            // visszavon. A keretsáv láthatatlansága a
                            // megbízható „most kezdődött" jel.
                            if (!lassoBand.visible) grid.beginLasso()
                            lassoBand.update(
                                mapToItem(grid, sx, sy),
                                mapToItem(grid, cx, cy))
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
        }
    }
    ScrollBar.vertical: PicasaScrollBar {}

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
