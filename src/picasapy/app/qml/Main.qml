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

    // explicit VILÁGOS paletta — az OS sötét módja sehol nem üthet át
    // (a sötét téma V3-feature; ld. design-guide)
    palette {
        window: Theme.canvasBg
        windowText: Theme.ink
        base: "#ffffff"
        alternateBase: Theme.panelBg
        text: Theme.ink
        button: "#e8e8e8"
        buttonText: Theme.ink
        highlight: Theme.selectionBlue
        highlightedText: "#ffffff"
        placeholderText: "#8f8b83"
        mid: Theme.chromeBorder
        light: "#ffffff"
        dark: "#9a9a9a"
    }

    property int thumbSize: 144
    property int selectedIndex: -1        // horgony (utoljára kattintott)
    property var selectedIndexes: []      // a teljes kijelölés
    property bool viewerOpen: false
    property bool tagsPanelOpen: false    // Címkék-panel (#12, Ctrl+T)
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

    Shortcut { sequence: "Ctrl+A"; onActivated: window.selectAll() }
    Shortcut { sequence: "Ctrl+D"; onActivated: window.clearSelection() }

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

    menuBar: PicasaMenuBar {
        photoActionsEnabled: !window.viewerOpen
                             && window.selectedIndexes.length > 0
        onRescanRequested: controller.rescan()
        onAboutRequested: aboutDialog.open()
        onThumbSizePreset: function(size) { window.thumbSize = size }
        onSelectStarredRequested: controller.showStarred()
        onSelectAllRequested: window.selectAll()
        onClearSelectionRequested: window.clearSelection()
        onFolderManagerRequested: folderManager.open()
        onRenameRequested: fileOpsDialogs.openRename(window.selectedIndex)
        onExportRequested: exportDialogs.openForSelection()
        onLocateRequested: {
            var p = controller.photos.filePathAt(window.selectedIndex)
            if (p.length > 0) fileOpsController.revealPhoto(p)
        }
        onDeleteRequested: fileOpsDialogs.openDelete(window.selectedPaths())
        onSlideshowRequested: window.startSlideshow(-1)
        tagsPanelOpen: window.tagsPanelOpen
        onTagsPanelRequested: window.tagsPanelOpen = !window.tagsPanelOpen
        onHideToggleRequested: window.toggleHiddenSelection()
        propertiesPanelOpen: window.propertiesPanelOpen
        onPropertiesPanelRequested:
            window.propertiesPanelOpen = !window.propertiesPanelOpen
        // #152: „Copy/Paste All Effects" — a kijelölésre hat, a rács
        // sorindexein keresztül (window.selectedRows() a meglévő mintát
        // követi, ld. toggleHiddenSelection)
        hasEffectsClipboard: controller.hasEffectsClipboard
        onCopyEffectsRequested: controller.copyEffects(window.selectedRows())
        onPasteEffectsRequested: controller.pasteEffects(window.selectedRows())
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
        photosModel: controller.photos
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
        photosModel: controller.photos
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
    }

    SplitView {
        anchors.fill: parent
        visible: !window.viewerOpen
        orientation: Qt.Horizontal

        FolderPane {
            objectName: "folderPane"
            SplitView.preferredWidth: 230
            SplitView.minimumWidth: 160
            foldersModel: controller.folders
            selectedPath: controller.currentFolder
            starredActive: controller.filterActive
            searchActive: controller.searchActive
            searchQuery: controller.searchQuery
            searchResultCount: controller.searchResultCount
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
                    visible: controller.filterActive
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
                            text: controller.filterStatusText
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
                            visible: !controller.searchActive
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
                            visible: controller.searchActive
                            model: controller.searchGroups
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
                                    cellHeight: window.thumbSize + 18
                                        + (controller.thumbCaptionMode !== "none"
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
                                        captionMode: controller.thumbCaptionMode
                                        selected: window.selectedIndexes
                                            .indexOf(modelData.row) !== -1
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
                            ScrollBar.vertical: ScrollBar {}
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
            tags: (controller.photos.revision,
                   controller.keywordsOfRows(window.selectedRows()))
            onAddRequested: function(keyword) {
                controller.addKeywordToRows(window.selectedRows(), keyword)
            }
            onRemoveRequested: function(keyword) {
                controller.removeKeywordFromRows(window.selectedRows(), keyword)
            }
            onCloseRequested: window.tagsPanelOpen = false
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
            entries: (controller.photos.revision,
                      controller.propertiesOf(window.selectedIndex))
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
        visible: controller.importPanelVisible
        folderName: controller.importFolderName
        doneCount: controller.importDoneCount
        totalCount: controller.importTotalCount
        newCount: controller.importNewCount
        onCloseRequested: controller.dismissImportPanel()
        // induló hely: jobb felül, a kereső alatt; húzáskor a DragHandler
        // felülírja a kötést — a panel ott marad, ahova a felhasználó tette
        x: parent.width - width - 24
        y: 56
    }

    // alsó sáv: infó-sáv + kijelölés-tálca (TrayBar.qml, #150)
    footer: TrayBar {
        id: trayBar
        width: parent ? parent.width : 0
        appWindow: window
        viewerIndex: photoViewer.currentIndex
        onExportRequested: exportDialogs.openForSelection()
    }

    // -- fájlműveletek (#15): kontextusmenü + dialógusok --------------------

    PhotoContextMenu {
        id: photoContextMenu
        // #17: pipa, ha a jobbklikkelt kép rejtett (photos.revision-nel
        // együtt kötve, hogy a menü újranyitáskor friss legyen)
        hideChecked: (controller.photos.revision,
                      (controller.photos.itemAt(window.fileOpTargetRow)
                           .hidden === true))
        onHideToggleRequested: window.toggleHiddenSelection()
        onRenameRequested: fileOpsDialogs.openRename(window.fileOpTargetRow)
        onMoveRequested: fileOpsDialogs.openMove(window.selectedPaths())
        onDeleteRequested: fileOpsDialogs.openDelete(window.selectedPaths())
        onLocateRequested: {
            var p = controller.photos.filePathAt(window.fileOpTargetRow)
            if (p.length > 0) fileOpsController.revealPhoto(p)
        }
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

    AboutDialog { id: aboutDialog }
}
