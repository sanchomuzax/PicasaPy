import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy
import "selection.js" as Selection

// Főablak (#150 után): a nagy nézet-blokkok külön komponensekben élnek
// (LightboxFeed = könyvtár-feed, MainToolbar = felső sáv, TrayBar = alsó
// sáv, FileOpsDialogs/ExportDialogs/AboutDialog = dialógusok, selection.js
// = kijelölés-logika) — itt csak az állapot és a bekötés marad.
ApplicationWindow {
    id: window
    width: 1280
    height: 800
    visible: true
    title: "PicasaPy"
    color: Theme.lightboxBg

    // #28: a téma a Theme-tokenekből jön, azok pedig a controller
    // kapcsolójából — az OS saját sötét módja sehol nem üthet át, a
    // váltás kizárólag a Nézet → Sötét téma menüponté (alapértelmezés:
    // világos; ld. design-guide).
    Binding {
        target: Theme
        property: "dark"
        value: controller ? controller.darkTheme : false
    }

    palette {
        window: Theme.canvasBg
        windowText: Theme.ink
        base: Theme.controlBase
        alternateBase: Theme.panelBg
        text: Theme.ink
        button: Theme.buttonBg
        buttonText: Theme.ink
        highlight: Theme.selectionBlue
        highlightedText: Theme.panelSelectionText
        placeholderText: Theme.placeholderText
        mid: Theme.chromeBorder
        light: Theme.shadeLight
        dark: Theme.shadeDark
    }

    property int thumbSize: 144
    property int selectedIndex: -1        // horgony (utoljára kattintott)
    property var selectedIndexes: []      // a teljes kijelölés
    // #142: a kijelölés set-alakban (sor → true) — a rács-cellák O(1)
    // lookupja; az indexOf-os kötés O(cellák × kijelöltek) volt, ami
    // Ctrl+A-nál minden cellán végigjárta a teljes kijelölés-listát
    property var selectedSet: ({})
    onSelectedIndexesChanged: {
        var s = {}
        for (var k = 0; k < selectedIndexes.length; ++k)
            s[selectedIndexes[k]] = true
        selectedSet = s
    }
    property bool viewerOpen: false
    property bool timelineOpen: false     // Időrend nézet (#24, Ctrl+5)
    property bool tagsPanelOpen: false    // Címkék-panel (#12, Ctrl+T)
    property bool placesPanelOpen: false  // Helyek-panel (#30, térkép)
    // Tulajdonságok-panel (#13, Alt+Enter)
    property bool propertiesPanelOpen: false
    // a jobbklikkelt kép sora (#15) — a kontextusmenü egyedi műveleteinek
    // (átnevezés, fájlkezelő) célpontja
    property int fileOpTargetRow: -1

    // a kijelölt sorok listája (#12) — több-kijelölés, vagy ha az nincs,
    // az utoljára kattintott kép
    function selectedRows() {
        return Selection.effectiveRows(
            window.selectedIndexes, window.selectedIndex)
    }

    // a kijelölt képek abszolút útvonalai (#15/#16) — a fájlműveletek a
    // művelet ELŐTT gyűjtött útvonal-listán futnak, így a közben frissülő
    // rács-indexek nem tévesztenek célt
    function selectedPaths() {
        var rows = window.selectedRows()
        var paths = []
        for (var k = 0; k < rows.length; ++k) {
            var p = controller.photos.filePathAt(Number(rows[k]))
            if (p.length > 0) paths.push(p)
        }
        return paths
    }

    // jobbklikk a rácson (#15): a klikkelt kép kerüljön kijelölésbe (ha még
    // nincs benne), majd a kontextusmenü a kattintás helyén nyílik
    function openPhotoContextMenu(index, item, x, y) {
        if (window.selectedIndexes.indexOf(index) === -1) {
            window.selectedIndexes = [index]
            window.selectedIndex = index
        }
        window.fileOpTargetRow = index
        photoContextMenu.popup(item, x, y)
    }

    // Kijelölés-logika (Picasa): sima katt = egy kép; Ctrl = hozzávesz/
    // elvesz; Shift = tartomány a horgonytól. (Számítás: selection.js)
    function handleThumbClick(index, modifiers) {
        var i = Number(index)
        var mods = Number(modifiers)
        if (mods & Qt.ControlModifier) {
            window.selectedIndexes =
                Selection.toggled(window.selectedIndexes, i)
            window.selectedIndex = i
        } else if ((mods & Qt.ShiftModifier) && window.selectedIndex >= 0) {
            window.selectedIndexes =
                Selection.range(window.selectedIndex, i)
        } else {
            window.selectedIndexes = [i]
            window.selectedIndex = i
        }
    }
    function clearSelection() {
        window.selectedIndexes = []
        window.selectedIndex = -1
    }
    function selectAll() {
        var range = Selection.allRows(controller.photos.rowCount())
        window.selectedIndexes = range
        if (range.length > 0) window.selectedIndex = 0
    }
    // #422: „Kiválasztás megfordítása" (Ctrl+I) — a mappa-kontextusmenü és
    // a Szerkesztés menü tétele
    function invertSelection() {
        var rows = Selection.inverted(
            window.selectedIndexes, controller.photos.rowCount())
        window.selectedIndexes = rows
        window.selectedIndex = rows.length > 0 ? rows[0] : -1
    }
    // #426: „Csillagozottak kijelölése" (Szerkesztés menü) — a jelenlegi
    // nézet csillagos képeit jelöli ki (NEM a Mappák panel nézet-szűrője).
    function selectStarred() {
        var rows = Selection.starredRows(
            controller.photos.rowCount(), controller.photos.starAt)
        window.selectedIndexes = rows
        window.selectedIndex = rows.length > 0 ? rows[0] : -1
    }
    // #422: „Exportálás HTML-oldalként…" a mappa-kontextusmenüből — a
    // dialógus itt él (a menüsáv is ezt nyitja)
    function openWebExport() { webExportDialog.open() }
    // #422: a mappa-kontextusmenünek HÁROM megnyitási pontja van (a rács
    // üres területe, a bal panel mappa-sora, a rács mappa-fejléce), és
    // mindhárom UGYANAZT a menüt nyitja. A menü a FolderPane-ben él; a
    // másik két hívó ezen az ablak-szintű átjárón éri el.
    function openFolderContextMenu(path) {
        var target = path && path.length > 0
            ? path : (controller ? controller.currentFolder : "")
        if (target.length > 0) folderPane.openFolderContextMenu(target)
    }

    // #135: a háttér-frissítés (5 perces rescan, watcher-jelzés) a
    // rács-modellt teljesen resetelheti — beszúrt/eltűnt fájloknál a
    // sor-indexek elcsúsznának, és a csillag/forgatás/elrejtés/export a
    // FELHASZNÁLÓ által kijelölttől eltérő képre hatna. A resetet
    // megelőzően elmentjük a kijelölt sorok fotó-id-it (a sor-index
    // ekkor még a RÉGI adatot tükrözi), majd a reset után az id-k
    // alapján képezzük újra a kijelölést — az eltűnt fotók kiesnek.
    property var _pendingSelectedIds: []
    property string _pendingAnchorId: ""
    Connections {
        // #305: engine-leépítéskor a `controller` context property null
        // lehet, miközben ez a kötés újra kiértékelődik — null-őr kell.
        target: controller ? controller.photos : null
        function onModelAboutToBeReset() {
            var ids = []
            for (var k = 0; k < window.selectedIndexes.length; ++k) {
                var id = controller.photos.idAt(Number(window.selectedIndexes[k]))
                if (id.length > 0) ids.push(parseInt(id, 10))
            }
            window._pendingSelectedIds = ids
            window._pendingAnchorId = window.selectedIndex >= 0
                ? controller.photos.idAt(window.selectedIndex) : ""
        }
        function onModelReset() {
            window.selectedIndexes = Selection.remapByIds(
                window._pendingSelectedIds, controller.photos.rowOfId)
            window.selectedIndex = window._pendingAnchorId.length > 0
                ? controller.photos.rowOfId(parseInt(window._pendingAnchorId, 10))
                : -1
        }
    }

    Shortcut { sequence: "Ctrl+A"; onActivated: window.selectAll() }
    Shortcut { sequence: "Ctrl+D"; onActivated: window.clearSelection() }
    Shortcut { sequence: "Ctrl+I"; onActivated: window.invertSelection() }

    // Picasa gyorsbillentyűk: Ctrl+R jobbra, Ctrl+Shift+R balra forgat.
    // Diavetítés közben (#8) a vetített kép a célpont, nem a rács-kijelölés.
    function rotateTargetRow() {
        if (slideshow.visible) return slideshow.currentIndex
        return trayBar.starTargetRow
    }
    // #103: csak-videó célpontnál a forgatás tiltott — a tálca ↺/↻
    // gombjainak őre (a controller-slotok defenzíven szintén kihagyják
    // a videókat, vegyes kijelölésnél csak a fotók forognak)
    function rotateTargetsAllVideo() {
        // #305: null-őr — a TrayBar `enabled:` kötése (ami ezt hívja)
        // a QML-engine leépítésekor is újraértékelődhet
        if (!controller) return false
        var rows = window.viewerOpen
            ? [photoViewer.currentIndex]
            : window.selectedRows()
        if (rows.length === 0) return false
        for (var k = 0; k < rows.length; ++k)
            if (!controller.photos.isVideoAt(Number(rows[k])))
                return false
        return true
    }
    Shortcut {
        sequence: "Ctrl+R"
        onActivated: {
            var row = window.rotateTargetRow()
            if (row >= 0) controller.rotateRight(row)
        }
    }
    Shortcut {
        sequence: "Ctrl+Shift+R"
        onActivated: {
            var row = window.rotateTargetRow()
            if (row >= 0) controller.rotateLeft(row)
        }
    }
    // #8: Ctrl+4 — diavetítés (Picasa-billentyű)
    Shortcut {
        sequence: "Ctrl+4"
        onActivated: window.startSlideshow(-1)
    }
    // #12: Ctrl+T — Címkék-panel (Picasa-billentyű); a könyvtár-nézetben él
    Shortcut {
        sequence: "Ctrl+T"
        onActivated: if (!window.viewerOpen)
                         window.tagsPanelOpen = !window.tagsPanelOpen
    }
    // #13: Alt+Enter — Tulajdonságok-panel (Picasa-billentyű)
    Shortcut {
        sequence: "Alt+Return"
        onActivated: if (!window.viewerOpen)
                         window.propertiesPanelOpen = !window.propertiesPanelOpen
    }

    // -- időrend nézet (#24, Ctrl+5) -----------------------------------------
    // A teljes könyvtár dátum szerinti, korszakokra bontott áttekintése
    // (TimelineView.qml) — a nézőt nem lehet vele egyszerre nyitva tartani,
    // a diavetítéshez hasonlóan (startSlideshow) teljes képernyős réteg.
    function toggleTimeline() {
        if (window.timelineOpen) {
            window.timelineOpen = false
            return
        }
        timelineController.reload()
        window.timelineOpen = true
    }
    Shortcut {
        sequence: "Ctrl+5"
        onActivated: window.toggleTimeline()
    }

    // -- diavetítés (#8) ----------------------------------------------------
    // Indítás: viszonyítási pont a néző képe / a rács-kijelölés / az első
    // kép; a vetítés valódi teljes képernyőn fut, kilépéskor az ablak
    // visszaáll, és a rács/néző követi a vetítés utolsó képét.
    property int visibilityBeforeSlideshow: Window.Windowed
    function startSlideshow(fromIndex) {
        var index = fromIndex
        if (index < 0)
            index = window.viewerOpen ? photoViewer.currentIndex
                                      : Math.max(0, window.selectedIndex)
        window.visibilityBeforeSlideshow = window.visibility
        window.visibility = Window.FullScreen
        slideshow.start(index)
        if (!slideshow.visible)   // nincs vetíthető fotó — állítsuk vissza
            window.exitSlideshow()
    }
    function exitSlideshow() {
        window.visibility =
            window.visibilityBeforeSlideshow === Window.FullScreen
                ? Window.Windowed : window.visibilityBeforeSlideshow
        if (slideshow.currentIndex >= 0) {
            if (window.viewerOpen) {
                photoViewer.show(slideshow.currentIndex)
            } else {
                window.selectedIndex = slideshow.currentIndex
                window.selectedIndexes = [slideshow.currentIndex]
            }
        }
    }
    // Picasa: F2 = átnevezés, Ctrl+Shift+S = exportálás mappába
    Shortcut {
        sequence: "F2"
        onActivated: if (!window.viewerOpen && window.selectedIndex >= 0)
                         fileOpsDialogs.openRename(window.selectedIndex)
    }
    Shortcut {
        sequence: "Ctrl+Shift+S"
        onActivated: if (!window.viewerOpen) exportDialogs.openForSelection()
    }
    // #422: a rács kontextusmenüje `Ctrl+Delete`-et hirdet a lemezről
    // törléshez (spec 3.) — a billentyű eddig nem élt, csak a Fájl menü
    // `Delete`-je (ld. ui-audit-menus.md). Mindkettő ugyanoda vezet.
    Shortcut {
        objectName: "shortcutDeleteFromDiskGrid"
        sequence: "Ctrl+Delete"
        enabled: !window.viewerOpen && window.selectedRows().length > 0
        onActivated: fileOpsDialogs.openDelete(window.selectedPaths())
    }
    // #422: a nézőben PUSZTA Delete törli a lemezről (spec 3.) — ott nincs
    // ütközés, mert a rács album-parancsai nem élnek
    Shortcut {
        objectName: "shortcutDeleteFromDiskViewer"
        sequence: "Delete"
        enabled: window.viewerOpen && photoViewer.currentIndex >= 0
        onActivated: {
            var p = controller.photos.filePathAt(photoViewer.currentIndex)
            if (p.length > 0) fileOpsDialogs.openDelete([p])
        }
    }

    menuBar: PicasaMenuBar {
        photoActionsEnabled: !window.viewerOpen
                             && window.selectedIndexes.length > 0
        onRescanRequested: controller.rescan()
        onAboutRequested: aboutDialog.open()
        onThumbSizePreset: function(size) { window.thumbSize = size }
        // #426: „Csillagozottak kijelölése" (Szerkesztés menü) — kijelöl,
        // nem szűr (a Mappák panel „Csillagozott" nézete külön: onStarredChosen)
        onSelectStarredRequested: window.selectStarred()
        onSelectAllRequested: window.selectAll()
        onClearSelectionRequested: window.clearSelection()
        onFolderManagerRequested: folderManager.open()
        onDedupRequested: dedupDialog.open()
        // #350: Eszközök → Beállítások…
        onOptionsRequested: optionsDialog.open()
        // #351: Exportálás weboldalként
        onWebExportRequested: webExportDialog.open()
        // #366: több kijelölt képnél a tömeges átnevezés-dialógus nyílik
        onRenameRequested: window.selectedIndexes.length > 1
            ? fileOpsDialogs.openRenameMany(window.selectedIndexes)
            : fileOpsDialogs.openRename(window.selectedIndex)
        // #368: adatbázis-áthelyezés a Kísérleti menüből
        onMoveDatabaseRequested: moveDatabaseDialog.open()
        onExportRequested: exportDialogs.openForSelection()
        onLocateRequested: {
            var p = controller.photos.filePathAt(window.selectedIndex)
            if (p.length > 0) fileOpsController.revealPhoto(p)
        }
        onDeleteRequested: fileOpsDialogs.openDelete(window.selectedPaths())
        onSlideshowRequested: window.startSlideshow(-1)
        onTimelineRequested: window.toggleTimeline()
        tagsPanelOpen: window.tagsPanelOpen
        onTagsPanelRequested: window.tagsPanelOpen = !window.tagsPanelOpen
        placesPanelOpen: window.placesPanelOpen
        onPlacesPanelRequested:
            window.placesPanelOpen = !window.placesPanelOpen
        onHideToggleRequested: window.toggleHiddenSelection()
        propertiesPanelOpen: window.propertiesPanelOpen
        onPropertiesPanelRequested:
            window.propertiesPanelOpen = !window.propertiesPanelOpen
        // #426: „Az összes effektus másolása/beillesztése" — a kijelölésre
        // hat, a rács sorindexein keresztül (window.selectedRows() a
        // meglévő mintát követi, ld. toggleHiddenSelection). A
        // `photo_ops_controller.PhotoOpsMixin`-t hívja, NEM a #152-es
        // `effects_controller`-t (az a crop64-et is átvinné).
        // #305: null-őr — ld. fenti Connections
        hasAllEffectsClipboard: controller ? controller.hasAllEffectsClipboard : false
        onCopyAllEffectsRequested: controller.copyAllEffects(window.selectedRows())
        onPasteAllEffectsRequested: controller.pasteAllEffects(window.selectedRows())
        // #425: Kép ▸ Csoportos szerkesztés — a `batch_effect_controller.
        // BatchEffectMixin`-t hívja, ugyanazon a rács-sorindex mintán
        // a forgatás a MEGLÉVŐ (szinkron, gyors) rotateRightMany/
        // rotateLeftMany úton fut, nem az applyEffectMany háttérszálán —
        // a `filters=`-t bővítő 7 effekttől eltérően nem igényel ini-
        // láncbővítést, csak a rotate= kulcs cseréjét (ld. PhotoOpsMixin).
        // A kötegelt visszavonás (`controller.undoBatchEdit`/
        // `canUndoBatchEdit`) egyelőre — a #426/#152 „Paste All Effects"
        // undóihoz hasonlóan — csak a vezérlőn elérhető, UI-gomb nélkül.
        onBatchApplyEffectRequested: (name) => {
            if (name === "rotate_cw") controller.rotateRightMany(window.selectedRows())
            else if (name === "rotate_ccw") controller.rotateLeftMany(window.selectedRows())
            else controller.applyEffectMany(window.selectedRows(), name)
        }
    }

    // #17: Elrejtés/Megjelenítés a kijelölésre; elrejtés után a kijelölést
    // ürítjük — az elrejtett sorok kiesnek a rácsból, az indexek eltolódnak
    function toggleHiddenSelection() {
        var rows = window.selectedRows()
        if (rows.length === 0) return
        controller.toggleHiddenRows(rows)
        window.clearSelection()
    }

    FolderManagerDialog { id: folderManager }
    // Duplikátum-kezelő (#287): Eszközök → "Find Duplicates..."
    // #294: az appWindow-bekötés a „kijelölt képek" hatókörhöz kell — enélkül
    // a dialógus a mappa-hatókörre esne vissza (integrátori bekötés).
    DedupDialog { id: dedupDialog; appWindow: window }
    // #146: meglévő Picasa-telepítés átvétele — nyitása a Mappakezelő
    // gombjából (discoveryController.dialogRequested) vagy induláskori
    // automatikus felajánlásból (integrátori bekötés: picasaImportDialog.openAndDiscover())
    PicasaImportDialog { id: picasaImportDialog }
    // Import forrásból (#23): az eszköztár "Import" gombja nyitja
    ImportSourceDialog { id: importSourceDialog }

    // első indítás: nincs még figyelt mappa → Mappakezelő felajánlása
    Component.onCompleted: {
        if (controller.watchedFolders.length === 0)
            folderManager.open()
    }

    // Eszköztár: Importálás | (szűrők középen) | kereső jobbra
    header: MainToolbar {
        id: toolbar
        onSearchEdited: function(text) {
            window.clearSelection()
            controller.search(text)
            suggestionsTimer.restart()
        }
        onSearchCleared: {
            window.clearSelection()
            controller.search("")
            searchSuggestionsBox.suggestions = []
        }
        // #23: az "Import" gomb az Import forrásból ablakot nyitja
        onImportRequested: importSourceDialog.open()
    }

    // Kereső-javaslatok (#7): gépelés után rövid szünettel (debounce)
    // kérjük le, hogy NAS-on se fusson lekérdezés minden billentyűre.
    function refreshSuggestions() {
        searchSuggestionsBox.suggestions =
            controller.searchSuggestions(toolbar.searchText)
    }
    Timer {
        id: suggestionsTimer
        interval: 150
        onTriggered: window.refreshSuggestions()
    }
    SearchSuggestions {
        id: searchSuggestionsBox
        objectName: "searchSuggestions"
        z: 50
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.rightMargin: 8
        width: 300
        query: toolbar.searchText
        visible: suggestions.length > 0 && toolbar.searchText.length > 0
                 && !window.viewerOpen
        onChosen: function(kind, name, param) {
            if (kind === "folder") {
                toolbar.clearSearch()
                window.clearSelection()
                controller.selectFolder(param)
            }
            suggestions = []
        }
    }

    // #8: diavetítés-réteg — minden más felett, csak vetítés alatt látszik
    SlideshowView {
        id: slideshow
        objectName: "slideshowView"
        anchors.fill: parent
        z: 100
        // #305: null-őr
        photosModel: controller ? controller.photos : null
        onClosed: window.exitSlideshow()
        onStarToggled: function(index) { controller.toggleStar(index) }
        onRotateRequested: function(index, delta) {
            if (delta > 0) controller.rotateRight(index)
            else controller.rotateLeft(index)
        }
    }

    PhotoViewer {
        id: photoViewer
        objectName: "photoViewer"
        anchors.fill: parent
        visible: window.viewerOpen
        // #305: null-őr
        photosModel: controller ? controller.photos : null
        onPlayRequested: window.startSlideshow(currentIndex)
        onClosed: {
            window.viewerOpen = false
            window.selectedIndex = currentIndex   // a rács kövesse a nézőt
            window.selectedIndexes = [currentIndex]
            // a szerkesztések (filters=) azonnal látsszanak a rácson —
            // NAS-on a fájlfigyelő nem szól, nem várhatunk a rescanre (#59);
            // a feedben (#64) a néző át is léphetett másik mappába, ezért a
            // nézett kép mappáját frissítjük
            // #173: a megnyitás előtti feed-pozíciót megőrizzük — a resync
            // modellcseréje után NE a mappa elejére ugorjunk. A rögzítés a
            // resync ELŐTT történik (a savedY még a megnyitáskori), az
            // alkalmazás pedig a modellcsere UTÁN (Qt.callLater), illetve az
            // onFeedChanged ágon.
            grid.beginRevealAfterViewer()
            controller.resyncFolderOfRow(currentIndex)
            Qt.callLater(grid.applyRevealAfterViewer)
        }
        onCurrentIndexChanged: if (visible) window.selectedIndex = currentIndex
        // #422: a néző kontextusmenüjének „Törlés lemezről" tétele — a
        // megerősítő dialógus itt él (a menü maga a PhotoViewer-ben)
        onDeleteRequested: function(path) { fileOpsDialogs.openDelete([path]) }
    }

    // #24: Időrend nézet (Ctrl+5) — a teljes könyvtár korszak-áttekintése;
    // egy bélyegképre kattintva a fő rácsban jelenítjük meg a képet
    // (mappaváltás a bekötő selectFolder-jén át, majd a néző az
    // odakerült sor alapján — rowOfId, a keresési-találat minta szerint).
    TimelineView {
        id: timelineView
        objectName: "timelineView"
        anchors.fill: parent
        visible: window.timelineOpen
        // #305: null-őr — a timelineController is null lehet átmenetileg
        // a QML-engine leépítésekor
        periodsModel: timelineController ? timelineController.periods : []
        onClosed: window.timelineOpen = false
        onPhotoChosen: function(photoId, folderPath) {
            window.timelineOpen = false
            controller.selectFolder(folderPath)
            var row = controller.photos.rowOfId(photoId)
            if (row >= 0) {
                window.viewerOpen = true
                photoViewer.show(row)
            }
        }
    }

    SplitView {
        id: mainSplit
        anchors.fill: parent
        visible: !window.viewerOpen && !window.timelineOpen
        orientation: Qt.Horizontal

        // #322: látható, fogható elválasztó. A Fusion alap-fogantyúja olyan
        // halvány, hogy a felhasználó meg sem találta — ez a delegate a
        // Picasa vékony sávját adja, hover/húzás közben kiemelkedve, és a
        // kurzort is átváltja, hogy a húzhatóság magától látsszon.
        handle: Rectangle {
            objectName: "folderPaneHandle"
            implicitWidth: 6
            implicitHeight: 6
            color: SplitHandle.pressed
                   ? Qt.darker(Theme.chromeBorder, 1.35)
                   : (SplitHandle.hovered
                      ? Qt.darker(Theme.chromeBorder, 1.15)
                      : Theme.chromeBorder)

            Behavior on color {
                ColorAnimation { duration: 100 }
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton  // csak a kurzorért
                cursorShape: Qt.SplitHCursor
            }
        }

        FolderPane {
            id: folderPane
            objectName: "folderPane"
            // #305: null-őr — a controller a leépítéskor átmenetileg null
            SplitView.preferredWidth: controller ? controller.folderPaneWidth : 230
            SplitView.minimumWidth: 160
            SplitView.maximumWidth: 600

            // A húzott szélesség mentése — késleltetve, hogy a húzás közbeni
            // pixelenkénti változás ne írja folyamatosan a QSettings-t.
            onWidthChanged: folderPaneWidthSaver.restart()

            Timer {
                id: folderPaneWidthSaver
                interval: 400
                onTriggered: {
                    if (controller && folderPane.width > 0) {
                        controller.setFolderPaneWidth(Math.round(folderPane.width))
                    }
                }
            }
            // #305: null-őr — a controller a QML-engine leépítésekor
            // átmenetileg null lehet, amikor ezek a kötések utoljára
            // kiértékelődnek
            foldersModel: controller ? controller.folders : null
            selectedPath: controller ? controller.currentFolder : ""
            starredActive: controller ? controller.filterActive : false
            searchActive: controller ? controller.searchActive : false
            searchQuery: controller ? controller.searchQuery : ""
            searchResultCount: controller ? controller.searchResultCount : 0
            albumsModel: controller ? controller.albums : []
            selectedAlbumToken: controller ? controller.currentAlbumToken : ""
            onFolderChosen: function(path) {
                window.clearSelection()
                if (toolbar.searchText.trim().length > 0) {
                    // #45: aktív keresésnél a szűrés megmarad, a
                    // találatok a mappára szűkülnek (Picasa-viselkedés)
                    controller.selectFolderKeepSearch(path)
                } else {
                    toolbar.clearSearch()
                    controller.selectFolder(path)
                }
            }
            onStarredChosen: {
                toolbar.clearSearch()
                window.clearSelection()
                controller.showStarred()
            }
            onAlbumChosen: function(token) {
                if (!controller) return
                toolbar.clearSearch()
                window.clearSelection()
                controller.showAlbum(token)
            }
        }

        Rectangle {
            color: Theme.lightboxBg
            SplitView.fillWidth: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // zöld eredménysáv aktív szűrőnél (Picasa-minta)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 26
                    // #305: null-őr
                    visible: controller ? controller.filterActive : false
                    color: "#5aa865"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        spacing: 10
                        Rectangle {
                            Layout.preferredHeight: 18
                            Layout.preferredWidth: viewAllText.width + 20
                            radius: 9
                            color: "#ffffff"
                            Text {
                                id: viewAllText
                                anchors.centerIn: parent
                                text: qsTr("View All")
                                font.pixelSize: Theme.fontSize - 1
                                font.bold: true
                                color: "#3b8f00"
                            }
                            TapHandler { onTapped: controller.clearFilter() }
                        }
                        Text {
                            // #305: null-őr
                            text: controller ? controller.filterStatusText : ""
                            color: "white"
                            font.pixelSize: Theme.fontSize
                            font.bold: true
                        }
                        Item { Layout.fillWidth: true }
                    }
                }

                // indexkép-csoport: fehér kártya a vásznon (kézikönyv 08)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: 12
                    color: Theme.contentPanel
                    border.color: Theme.chromeBorder

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 4

                        // Könyvtár-feed (#64) — a komponens a PicasaPy
                        // modulban él (LightboxFeed.qml, #150)
                        LightboxFeed {
                            id: grid
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            // kereséskor a #7-es csoportosított nézet fut
                            // #305: null-őr
                            visible: controller ? !controller.searchActive : true
                            appWindow: window
                            onOpenRequested: function(row) {
                                window.viewerOpen = true
                                photoViewer.show(row)
                            }
                            onSlideshowRequested: function(startRow) {
                                window.startSlideshow(startRow)
                            }
                        }

                        // #7: keresési találatok mappánként csoportosítva
                        // (Picasa-minta) — a GridView nem támogat szekció-
                        // fejlécet, ezért csoportonként egy fejléc + egy
                        // nem-interaktív al-rács.
                        ListView {
                            id: groupedResults
                            objectName: "groupedSearchResults"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            // #305: null-őr
                            visible: controller ? controller.searchActive : false
                            model: controller ? controller.searchGroups : []
                            spacing: 0

                            delegate: ColumnLayout {
                                id: groupDelegate
                                required property var modelData
                                width: groupedResults.width
                                spacing: 0

                                SearchGroupHeader {
                                    Layout.fillWidth: true
                                    section: groupDelegate.modelData.folderName
                                }

                                GridView {
                                    id: subgrid
                                    Layout.fillWidth: true
                                    interactive: false
                                    // #85: itt is kiegyenlített sor — az
                                    // oszlopszám névleges méretből, a tényleges
                                    // cellaWidth a szélességet tölti ki.
                                    readonly property int nominalCellWidth:
                                        window.thumbSize + 18
                                    readonly property int columns: Math.max(
                                        1, Math.floor(width / nominalCellWidth))
                                    cellWidth: columns > 0
                                        ? Math.floor(width / columns)
                                        : nominalCellWidth
                                    // #305: null-őr
                                    cellHeight: window.thumbSize + 18
                                        + ((controller ? controller.thumbCaptionMode : "none") !== "none"
                                           ? 16 : 0)
                                    height: Math.ceil(
                                        groupDelegate.modelData.photos.length
                                        / columns) * cellHeight
                                    model: groupDelegate.modelData.photos

                                    delegate: ThumbDelegate {
                                        id: groupedThumb
                                        required property var modelData
                                        width: subgrid.cellWidth
                                        height: subgrid.cellHeight
                                        // #85/#83: a kép a névleges méretre
                                        // plafonozott
                                        maxContentWidth: subgrid.nominalCellWidth
                                        maxContentHeight: subgrid.cellHeight
                                        name: modelData.name
                                        thumbUrl: modelData.thumbUrl
                                        star: modelData.star
                                        caption: modelData.caption
                                        isVideo: modelData.isVideo
                                        hasEdits: modelData.hasEdits
                                        isHidden: modelData.hidden === true
                                        index: modelData.row
                                        keywords: modelData.keywords
                                        resolution: modelData.resolution
                                        // #305: null-őr
                                        captionMode: controller ? controller.thumbCaptionMode : "none"
                                        // #142: set-alapú lookup
                                        selected: window.selectedSet[
                                            modelData.row] === true
                                        onChosen: function(i, mods) {
                                            window.handleThumbClick(i, mods)
                                        }
                                        onOpened: function(i) {
                                            window.viewerOpen = true
                                            photoViewer.show(i)
                                        }
                                        onContextMenuRequested: function(i, cx, cy) {
                                            window.openPhotoContextMenu(
                                                i, groupedThumb, cx, cy)
                                        }
                                    }
                                }
                            }
                            ScrollBar.vertical: PicasaScrollBar {}
                        }
                    }
                }
            }
        }

        // Címkék-panel (#12): jobb oldali hasáb, Ctrl+T / Nézet → Címkék
        TagsPanel {
            objectName: "tagsPanel"
            visible: window.tagsPanelOpen
            SplitView.preferredWidth: 190
            SplitView.minimumWidth: 150
            hasSelection: window.selectedRows().length > 0
            // a photos.revision-nel együtt kötve: címke-írás után frissül
            // #305: null-őr
            tags: controller
                ? (controller.photos.revision,
                   controller.keywordsOfRows(window.selectedRows()))
                : []
            onAddRequested: function(keyword) {
                controller.addKeywordToRows(window.selectedRows(), keyword)
            }
            onRemoveRequested: function(keyword) {
                controller.removeKeywordFromRows(window.selectedRows(), keyword)
            }
            onCloseRequested: window.tagsPanelOpen = false
            // #422: a címke jobbklikk-menüje (Picasa `Tags` menüosztály)
            onAddToSelectionRequested: function(keyword) {
                if (controller)
                    controller.addKeywordToRows(window.selectedRows(), keyword)
            }
            onFindTaggedRequested: function(keyword) {
                if (controller) controller.search(keyword)
            }
        }

        // Helyek-panel (#30): jobb oldali hasáb, Nézet → Helyek — a látszó
        // képek helyei térképen, és a kijelölés geocímkézése
        PlacesPanel {
            objectName: "placesPanel"
            visible: window.placesPanelOpen
            SplitView.preferredWidth: 320
            SplitView.minimumWidth: 220
            appWindow: window
            onCloseRequested: window.placesPanelOpen = false
            onPhotoActivated: function(row) {
                window.selectedIndexes = [row]
                window.selectedIndex = row
            }
        }

        // Tulajdonságok-panel (#13): jobb oldali hasáb, Alt+Enter /
        // Nézet → Tulajdonságok — csak olvasás
        PropertiesPanel {
            objectName: "propertiesPanel"
            visible: window.propertiesPanelOpen
            SplitView.preferredWidth: 210
            SplitView.minimumWidth: 160
            hasSelection: window.selectedIndex >= 0
            // a photos.revision-nel együtt kötve: modell-frissüléskor újraolvas
            // #305: null-őr
            entries: controller
                ? (controller.photos.revision,
                   controller.propertiesOf(window.selectedIndex))
                : []
            onCloseRequested: window.propertiesPanelOpen = false
        }
    }

    // #209: lebegő „Importálás" folyamat-panel — jobb oldalt lebeg, húzható;
    // a néző felett is látszik (a szkennelés közben is lehet dolgozni),
    // csak a diavetítés (z:100) takarja
    ImportProgressPanel {
        id: importPanel
        objectName: "importProgressPanel"
        z: 90
        // #305: null-őr
        visible: controller ? controller.importPanelVisible : false
        folderName: controller ? controller.importFolderName : ""
        doneCount: controller ? controller.importDoneCount : 0
        totalCount: controller ? controller.importTotalCount : 0
        newCount: controller ? controller.importNewCount : 0
        onCloseRequested: controller.dismissImportPanel()
        // induló hely: jobb felül, a kereső alatt; húzáskor a DragHandler
        // felülírja a kötést — a panel ott marad, ahova a felhasználó tette
        x: parent.width - width - 24
        y: 56
    }

    // #425: lebegő „Csoportos szerkesztés" folyamat-panel — az
    // ImportProgressPanel mintájára, Mégse gombbal (megszakítható köteg)
    BatchEditProgressPanel {
        id: batchEditPanel
        objectName: "batchEditProgressPanel"
        z: 90
        visible: controller ? controller.batchEditActive : false
        folderName: controller ? controller.batchEditFolderName : ""
        doneCount: controller ? controller.batchEditDoneCount : 0
        totalCount: controller ? controller.batchEditTotalCount : 0
        onCancelRequested: controller.cancelBatchEdit()
        x: parent.width - width - 24
        y: 56 + importPanel.height + 12
    }

    // #211: lebegő „Teljesítmény-monitor" panel — a Súgó menüből
    // kapcsolható; balra az importálás-paneltől, hogy ne fedjék egymást
    PerfMonitorPanel {
        id: perfPanel
        objectName: "perfMonitorPanel"
        z: 90
        // #305: null-őr
        visible: controller ? controller.perfMonitorEnabled : false
        cpuPercent: controller ? controller.perfCpuPercent : 0
        rssMb: controller ? controller.perfRssMb : 0
        topActivity: controller ? controller.perfTopActivity : ""
        onCloseRequested: controller.setPerfMonitorEnabled(false)
        onSaveRequested: perfPanel.lastSavedPath = controller.saveDiagnostics()
        x: 24
        y: 56
    }

    // #237: kép/mappa ablakra ejtése → a kép mappája figyelt gyökér lesz
    // (ImportDropArea → dropImportController). Egér-eseményt nem fog el;
    // z:95 — a lebegő panelek (90) fölött, a diavetítés (100) alatt, hogy
    // a visszajelzés-buborék látsszon
    ImportDropArea {
        objectName: "importDropArea"
        anchors.fill: parent
        z: 95
    }

    // alsó sáv: infó-sáv + kijelölés-tálca (TrayBar.qml, #150)
    footer: TrayBar {
        id: trayBar
        width: parent ? parent.width : 0
        appWindow: window
        viewerIndex: photoViewer.currentIndex
        onExportRequested: exportDialogs.openForSelection()
        // #361: kollázs/film a tálca ikonjairól is (CreateDialogs, #29)
        onCollageRequested: createDialogs.openCollage()
        onMovieRequested: createDialogs.openMovie()
    }

    // -- fájlműveletek (#15): kontextusmenü + dialógusok --------------------

    PhotoContextMenu {
        id: photoContextMenu
        // #17: pipa, ha a jobbklikkelt kép rejtett (photos.revision-nel
        // együtt kötve, hogy a menü újranyitáskor friss legyen)
        // #305: null-őr
        hideChecked: controller
            ? (controller.photos.revision,
               (controller.photos.itemAt(window.fileOpTargetRow)
                    .hidden === true))
            : false
        onHideToggleRequested: window.toggleHiddenSelection()
        onMoveRequested: fileOpsDialogs.openMove(window.selectedPaths())
        onDeleteRequested: fileOpsDialogs.openDelete(window.selectedPaths())
        onLocateRequested: {
            var p = controller.photos.filePathAt(window.fileOpTargetRow)
            if (p.length > 0) fileOpsController.revealPhoto(p)
        }
        // #422 (2. lépcső): az eredeti AlbumPhoto-menü többi parancsa
        onOpenRequested: {
            window.viewerOpen = true
            photoViewer.show(window.fileOpTargetRow)
        }
        onRotateRightRequested: controller.rotateRightMany(window.selectedRows())
        onRotateLeftRequested: controller.rotateLeftMany(window.selectedRows())
        onOpenFileRequested: {
            var target = controller.photos.filePathAt(window.fileOpTargetRow)
            if (target.length > 0) fileOpsController.openPhoto(target)
        }
        onCopyFullPathRequested: {
            var full = controller.photos.filePathAt(window.fileOpTargetRow)
            if (full.length > 0) fileOpsController.copyFullPath(full)
        }
        onPropertiesRequested:
            window.propertiesPanelOpen = !window.propertiesPanelOpen
        // #9 (2. lépés): albumtagság — #305 null-őr
        albums: controller ? controller.albums : []
        currentAlbumToken: controller ? controller.currentAlbumToken : ""
        onAddToAlbumRequested: function(token) {
            if (controller) controller.addRowsToAlbum(window.selectedRows(), token)
        }
        onRemoveFromAlbumRequested: {
            if (controller)
                controller.removeRowsFromAlbum(
                    window.selectedRows(), controller.currentAlbumToken)
        }
        onNewAlbumRequested: fileOpsDialogs.openNewAlbum(window.selectedRows())
    }

    // átnevezés / áthelyezés / törlés / hiba (FileOpsDialogs.qml, #150)
    FileOpsDialogs {
        id: fileOpsDialogs
        appWindow: window
    }

    // exportálás mappába (#16, Ctrl+Shift+S; ExportDialogs.qml, #150)
    ExportDialogs {
        id: exportDialogs
        appWindow: window
    }

    // kollázs és mozgófilm a kijelölésből (#29; CreateDialogs.qml)
    CreateDialogs {
        id: createDialogs
        appWindow: window
    }

    AboutDialog { id: aboutDialog }

    // #350: Beállítások-dialógus (options.fen)
    OptionsDialog { id: optionsDialog }

    // #351: webexport-dialógus (.tpl sablonmotor)
    WebExportDialog { id: webExportDialog }

    // #368: adatbázis-áthelyezés dialógus (relocateController hídon)
    MoveDatabaseDialog { id: moveDatabaseDialog }

    // Indítóképernyő (#189): a legfelső rétegen ül, a startupStatus hídból
    // kapja az állapotot, és ready-re magától kifakul/eltűnik.
    // A kötés defenzív: híd (context property) nélkül — pl. célzott
    // tesztkörnyezetben — a splash készre áll, azaz rejtve marad.
    SplashScreen {
        readonly property var statusBridge:
            typeof startupStatus !== "undefined" ? startupStatus : null
        anchors.fill: parent
        z: 10000
        version: appVersion
        statusText: statusBridge ? statusBridge.statusText : ""
        ready: statusBridge ? statusBridge.ready : true
        // #243: félkész-figyelmeztetés + OK a betöltés végén, amíg az
        // effekt-paritás nem teljes (a kapcsoló az application.py-ban él)
        confirmationRequired:
            statusBridge ? statusBridge.requiresConfirmation : false
    }
}
