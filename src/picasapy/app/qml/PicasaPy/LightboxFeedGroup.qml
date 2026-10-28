import QtQuick
import QtQuick.Controls
import "groups.js" as Groups
import "lasso.js" as Lasso
import "scroll.js" as Scroll
import "../selection.js" as Selection

Column {
    id: groupCol
    required property var feed
    readonly property var ctl: typeof controller !== "undefined" ? controller : null
    required property var lassoOverlay
    required property var modelData
    width: feed.width
    spacing: 4
    function visiblePhotoRange() {
        var viewTop = feed.contentY - groupCol.y - groupFlow.y
        var visibleTop = Math.max(0, viewTop)
        var visibleBottom = Math.min(
            groupFlow.height, viewTop + feed.height)
        if (visibleBottom <= visibleTop || feed.cellHeight <= 0)
            return null
        var firstRow = Math.floor(visibleTop / feed.cellHeight)
        var lastRow = Math.max(
            firstRow,
            Math.ceil(visibleBottom / feed.cellHeight) - 1)
        return {
            first: groupCol.modelData.start
                + firstRow * feed.columns,
            last: Math.min(
                groupCol.modelData.start + groupCol.modelData.count - 1,
                groupCol.modelData.start
                    + (lastRow + 1) * feed.columns - 1)
        }
    }
    // a képfolyam (Flow) függőleges eltolása a csoporton
    // belül — a sor-szintű görgetés (#96) számol vele
    readonly property real flowOffset: groupFlow.y

    LightboxHeader {
        width: parent.width
        folderName: groupCol.modelData.name
        dateText: groupCol.modelData.dateText
        personAlbumFolderMode: feed.personAlbumMode
        description: ctl
            ? (ctl.descriptionRevision,
               ctl.folderDescriptionOf(groupCol.modelData.path))
            : ""
        onDescriptionEdited: function(text) {
            controller.setFolderDescriptionOf(
                groupCol.modelData.path, text)
        }
        // #1823: a fejléc-gombok a KIJELÖLÉS darabszámát írják ki.
        selectedCount: feed.appWindow && feed.appWindow.selectedIndexes
                       ? feed.appWindow.selectedIndexes.length : 0
        hasPendingEdits: feed.appWindow
            ? feed.appWindow.kijelolesbenVanMentetlenSzerkesztes : false
        // zöld ▸ (#8): a mappa vetítése az első képétől
        onPlayRequested: feed.slideshowRequested(
            groupCol.modelData.start)
        // #1823: a két új fejléc-gomb ugyanazon az úton jut a
        // gazdaablakhoz, mint a jobbklikkes mappa-menü — nem
        // vezetünk át új jelet a LightboxFeed-en, mert a művelet
        // nem a képfolyamé, hanem az ablaké.
        onSelectStarredRequested: {
            if (feed.appWindow && feed.appWindow.selectStarred)
                feed.appWindow.selectStarred()
        }
        //: #1006: a fejléc a SAJÁT csoportjának képeiből nyit
        //: kollázst — nem a kijelölésből és nem a tálcából. Az
        //: eredeti is a panelhez tartozó halmazzal dolgozik.
        onCollageRequested: {
            if (!feed.appWindow || !feed.appWindow.openCollageFromRows)
                return
            var sorok = []
            var kezdet = groupCol.modelData.start
            for (var i = 0; i < groupCol.modelData.count; ++i)
                sorok.push(kezdet + i)
            feed.appWindow.openCollageFromRows(sorok)
        }
        //: #4539: a mappa-fejléc film-gombja — a kollázzsal azonos
        //: halmazt adja át (a csoport sorait), nem a kijelölést.
        onMovieRequested: {
            if (!feed.appWindow || !feed.appWindow.openMovieFromRows)
                return
            var sorok = []
            var kezdet = groupCol.modelData.start
            for (var i = 0; i < groupCol.modelData.count; ++i)
                sorok.push(kezdet + i)
            feed.appWindow.openMovieFromRows(sorok)
        }
        onPersonMovieRequested: {
            if (feed.appWindow && feed.appWindow.openPersonAlbumMovie)
                feed.appWindow.openPersonAlbumMovie()
        }
        onSaveEditsRequested: {
            if (feed.appWindow && feed.appWindow.saveSelectedEdits)
                feed.appWindow.saveSelectedEdits()
        }
        //: #2187: személy-album módban a fejléc a javaslat-vezérlőket
        //: is mutatja. A nevet és a darabszámot a gazdaablak tölti —
        //: a képfolyam nem ismeri az arc-vezérlőt, ahogy a
        //: mentés/csillagozás esetében sem.
        personName: ""
        suggestionCount: feed.appWindow
                         && feed.appWindow.personSuggestionCount !== undefined
                         ? feed.appWindow.personSuggestionCount : 0
        selectedSuggestionCount: feed.appWindow
            && feed.appWindow.personSelectedSuggestionIds !== undefined
            ? feed.appWindow.personSelectedSuggestionIds.length : 0
        onSelectSuggestionsRequested: {
            if (feed.appWindow && feed.appWindow.selectPersonSuggestions)
                feed.appWindow.selectPersonSuggestions()
        }
        onConfirmSuggestionsRequested: {
            if (feed.appWindow && feed.appWindow.confirmPersonSuggestions)
                feed.appWindow.confirmPersonSuggestions()
        }
        onRemoveSuggestionsRequested: {
            if (feed.appWindow && feed.appWindow.removePersonSuggestions)
                feed.appWindow.removePersonSuggestions()
        }
        //: #2187: `sug_filter` — a szűrő állását a vezérlő tartja, a
        //: fejléc csak mutatja és kéri az átkapcsolást
        suggestionsOnly: feed.appWindow
                         && feed.appWindow.personSuggestionsOnly !== undefined
                         ? feed.appWindow.personSuggestionsOnly : false
        onSuggestionsOnlyToggled: function (csak) {
            if (feed.appWindow && feed.appWindow.setPersonSuggestionsOnly)
                feed.appWindow.setPersonSuggestionsOnly(csak)
        }
        //: #2187: `face_zoom` ↔ `picture_zoom` — az állást a vezérlő
        //: tartja, a fejléc csak mutatja és kéri a váltást
        faceZoom: feed.appWindow
                  && feed.appWindow.personFaceZoom !== undefined
                  ? feed.appWindow.personFaceZoom : false
        onFaceZoomToggled: function (arc) {
            if (feed.appWindow && feed.appWindow.setPersonFaceZoom)
                feed.appWindow.setPersonFaceZoom(arc)
        }
        //: #2187: `moresug` — a lazítás az egész készletre újraszámol
        onMoreSuggestionsRequested: {
            if (feed.appWindow && feed.appWindow.findMoreSuggestions)
                feed.appWindow.findMoreSuggestions()
        }
        // #422: jobbklikk a mappa-fejlécen — a mappa-kontextusmenü
        // ARRA a mappára, amelyiknek a fejléce ez (nem a kijelöltre)
        onContextMenuRequested: {
            if (feed.appWindow && feed.appWindow.openFolderContextMenu)
                feed.appWindow.openFolderContextMenu(
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
        x: feed.personAlbumMode ? 4 : 0
        width: Math.max(0, parent.width - x)
        readonly property int totalRows: Math.ceil(
            groupCol.modelData.count / feed.columns)
        height: totalRows * feed.cellHeight
        // a látótér teteje a csoport képfolyamának koordinátájában
        readonly property real viewTop:
            feed.contentY - groupCol.y - y
        // puffer-sorok a látótér felett/alatt — görgetés közben a
        // következő sor már készen áll
        readonly property int bufferRows: 2
        readonly property int firstRow: Math.max(0,
            Math.floor(viewTop / feed.cellHeight) - bufferRows)
        readonly property int lastRow: Math.min(totalRows - 1,
            Math.ceil((viewTop + feed.height) / feed.cellHeight)
                + bufferRows)
        readonly property int windowStart: firstRow * feed.columns
        readonly property int windowCount: Math.max(0, Math.min(
            groupCol.modelData.count - windowStart,
            (lastRow - firstRow + 1) * feed.columns))
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
                if (!huz) { huz = true; feed.beginLasso() }
                lassoOverlay.update(
                    mapToItem(grid, pressX, pressY),
                    mapToItem(grid, event.x, event.y))
                // #897: a kijelölés MÁR HÚZÁS KÖZBEN követi a keretet
                // (a saját koordinátáink a groupFlow-éi — a terület
                // kitölti a képfolyamot)
                feed.updateLasso(
                    groupCol.modelData.start, groupCol.modelData.count,
                    groupFlow.width,
                    pressX, pressY, event.x, event.y, event.modifiers)
            }
            onReleased: function(event) {
                if (!huz) {
                    // #1145/#1219: üres területre kattintva az
                    // eredeti a kijelölést TÖRLI (a mappa
                    // csomópontján), nem hagyja ott
                    feed.appWindow.clearSelection()
                    return
                }
                huz = false
                lassoOverlay.visible = false
                feed.applyLasso(
                    groupCol.modelData.start, groupCol.modelData.count,
                    groupFlow.width,
                    pressX, pressY, event.x, event.y, event.modifiers)
            }
        }
        //: #1721: a kézi sorrend ejtési területe. A `DropArea` NEM
        //: fogyaszt egéresemenyt, tehát a lasszó és a cellák kezelése
        //: érintetlen marad — csak a húzás-ejtés érkezik ide.
        DropArea {
            id: reorderDrop
            objectName: "feedReorderDropArea"
            anchors.fill: parent
            onDropped: function(drop) {
                if (!feed.acceptsPhotoDrag(drop)) return
                drop.accept()
                feed.photoRowsDroppedOnReorder(
                    groupCol.modelData.start, groupCol.modelData.count,
                    groupFlow.width, drop.x, drop.y,
                    drop.source.photoRows ? drop.source.photoRows.slice() : [])
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
                x: (slot.localIndex % feed.columns) * feed.cellWidth
                y: Math.floor(slot.localIndex / feed.columns)
                    * feed.cellHeight
                // a photos.revision-nel együtt kötve:
                // modell-frissüléskor újraértékelődik
                // #305: null-őr — üres objektum, hogy a lenti
                // `slot.info.X || ...` kötések ne dőljenek el
                readonly property var info: feed.ctl
                    ? (feed.ctl.photos.revision,
                       feed.ctl.photos.itemAt(slot.row))
                    : ({})
                width: feed.cellWidth
                height: feed.cellHeight
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
                    held: feed.ctl
                          ? (feed.ctl.heldCount, feed.ctl.isHeldAt(slot.row))
                          : false
                    isHidden: slot.info.hidden === true
                    keywords: slot.info.keywords || ""
                    resolution: slot.info.resolution || ""
                    captionMode: feed.ctl ? feed.ctl.thumbCaptionMode : "none"
                    dragMimeData: ({
                        "text/uri-list": feed.selectedFileUriList()
                    })
                    dragRows: feed.appWindow
                        && feed.appWindow.selectedIndexes
                        ? feed.appWindow.selectedIndexes.slice()
                        : [slot.row]
                    // #85/#83: a megjelenő kép a névleges
                    // méretre plafonozott, a kiegyenlítés
                    // többlete a térközbe megy.
                    maxContentWidth: feed.nominalCellWidth
                    maxContentHeight: feed.cellHeight
                    // #142: set-alapú lookup — O(1) cellánként
                    selected: feed.appWindow
                        .selectedSet[slot.row] === true
                    onChosen: function(i, mods) {
                        feed.forceActiveFocus()   // kurzorgombokhoz (#77)
                        // #897: a horgony kezelése a rácsé — a Shift
                        // EGÉRREL tartományt jelöl a horgonytól, és
                        // nem lépteti azt
                        feed.applyThumbClick(i, mods)
                    }
                    onOpened: function(i) {
                        feed.openRequested(i)
                    }
                    onLassoDragged: function(sx, sy, cx, cy, mods) {
                        // #1148/#897: a gesztus ELSŐ mozdulatánál
                        // pillanatfelvétel — a Shift/Ctrl ehhez
                        // viszonyít, ezért a keret visszahúzása is
                        // visszavon.
                        if (!feed.lassoActive) feed.beginLasso()
                        lassoOverlay.update(
                            mapToItem(grid, sx, sy),
                            mapToItem(grid, cx, cy))
                        // #897: a kijelölés húzás közben is követ
                        var a = mapToItem(groupFlow, sx, sy)
                        var b = mapToItem(groupFlow, cx, cy)
                        feed.updateLasso(
                            groupCol.modelData.start,
                            groupCol.modelData.count,
                            groupFlow.width,
                            a.x, a.y, b.x, b.y, mods)
                    }
                    onLassoFinished: function(sx, sy, cx, cy, mods) {
                        var a = mapToItem(groupFlow, sx, sy)
                        var b = mapToItem(groupFlow, cx, cy)
                        feed.applyLasso(
                            groupCol.modelData.start,
                            groupCol.modelData.count,
                            groupFlow.width,
                            a.x, a.y, b.x, b.y, mods)
                        lassoOverlay.visible = false
                    }
                    onContextMenuRequested: function(i, cx, cy) {
                        feed.appWindow.openPhotoContextMenu(
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
            enabled: feed.appWindow ? feed.appWindow.loupeActive === true
                                    : false
            visible: loupeArea.enabled
            acceptedButtons: Qt.LeftButton
            preventStealing: true
            hoverEnabled: false

            //: #2399: NINCS nagyítási arány. Az eredeti a teljes
            //: méretű képet 1:1-ben rajzolja (a célterület `W` × `H`,
            //: `0x0077bcf5`–`0x0077bd19`), csak eltolva, hogy a
            //: kurzor alatti képpont a felület közepére essen — a
            //: látszólagos nagyítás ebből adódik. A korábbi arány-
            //: tulajdonság (2.5) a projekt egészében EGYSZER fordult
            //: elő, a saját deklarációjában: holt volt, ezért törölve.

            property int aktivSor: -1
            property real kurzorX: 0
            property real kurzorY: 0

            function sorItt(x, y) {
                if (feed.columns <= 0) return -1
                var oszlop = Math.floor(x / feed.cellWidth)
                if (oszlop < 0 || oszlop >= feed.columns) return -1
                var sor = Math.floor(y / feed.cellHeight)
                if (sor < 0) return -1
                var helyi = sor * feed.columns + oszlop
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
                    id: feedLoupeImage
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
                    asynchronous: true

                    //: #2399: a lencse a TELJES felbontású képből vág
                    //: ki egy 65 × 65-es darabot, 1:1-ben — nem a
                    //: bélyegképet zsugorítja. A `sourceClipRect` a
                    //: DEKÓDOLT képből vág, átméretezés nélkül; ez adja
                    //: az eredeti 1:1 arányát.
                    readonly property int kivagatMeret: 65

                    //: a kurzor alatti KÉPPONT a teljes kép
                    //: koordinátáiban — a cellán belüli arányos helyet
                    //: vetítjük a valódi felbontásra
                    readonly property var kepAdat: {
                        if (!feed.ctl || loupeArea.aktivSor < 0)
                            return null
                        return (feed.ctl.photos.revision,
                                feed.ctl.photos.itemAt(loupeArea.aktivSor))
                    }
                    readonly property size kepMeret: {
                        var e = feedLoupeImage.kepAdat
                        if (!e || !e.resolution)
                            return Qt.size(0, 0)
                        var reszek = String(e.resolution).split("x")
                        if (reszek.length !== 2)
                            return Qt.size(0, 0)
                        return Qt.size(parseInt(reszek[0], 10),
                                       parseInt(reszek[1], 10))
                    }

                    source: {
                        var e = feedLoupeImage.kepAdat
                        return e && e.fileUrl ? e.fileUrl : ""
                    }

                    //: ⚠️ Ha a kép mérete ismeretlen (nincs `resolution`
                    //: az indexben), NEM vágunk: üres téglalappal a Qt a
                    //: teljes képet mutatná, ami rosszabb, mint a régi
                    //: viselkedés. Ilyenkor a bélyegkép-szerű illesztés
                    //: marad, csak a teljes képből.
                    sourceClipRect: {
                        var m = feedLoupeImage.kepMeret
                        if (m.width <= 0 || m.height <= 0)
                            return Qt.rect(0, 0, 0, 0)
                        var cella = feed.cellWidth > 0 ? feed.cellWidth : 1
                        var cellaM = feed.cellHeight > 0 ? feed.cellHeight : 1
                        //: a kurzor helye a CELLÁN belül, 0…1
                        var ax = (loupeArea.kurzorX % cella) / cella
                        var ay = (loupeArea.kurzorY % cellaM) / cellaM
                        var felM = feedLoupeImage.kivagatMeret / 2
                        var kx = Math.max(0, Math.min(
                            m.width - feedLoupeImage.kivagatMeret,
                            Math.round(ax * m.width) - felM))
                        var ky = Math.max(0, Math.min(
                            m.height - feedLoupeImage.kivagatMeret,
                            Math.round(ay * m.height) - felM))
                        return Qt.rect(kx, ky, feedLoupeImage.kivagatMeret,
                                       feedLoupeImage.kivagatMeret)
                    }
                }
            }
        }
    }
}
