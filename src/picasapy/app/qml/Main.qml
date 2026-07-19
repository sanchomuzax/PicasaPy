import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import PicasaPy

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
    // a jobbklikkelt kép sora (#15) — a kontextusmenü egyedi műveleteinek
    // (átnevezés, fájlkezelő) célpontja
    property int fileOpTargetRow: -1

    // a kijelölt képek abszolút útvonalai (#15/#16) — a fájlműveletek a
    // művelet ELŐTT gyűjtött útvonal-listán futnak, így a közben frissülő
    // rács-indexek nem tévesztenek célt
    function selectedPaths() {
        var rows = window.selectedIndexes.length > 0
            ? window.selectedIndexes
            : (window.selectedIndex >= 0 ? [window.selectedIndex] : [])
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
    // elvesz; Shift = tartomány a horgonytól.
    function handleThumbClick(index, modifiers) {
        var i = Number(index)
        var mods = Number(modifiers)
        if (mods & Qt.ControlModifier) {
            var s = window.selectedIndexes.slice()
            var pos = s.indexOf(i)
            if (pos >= 0) s.splice(pos, 1); else s.push(i)
            window.selectedIndexes = s
            window.selectedIndex = i
        } else if ((mods & Qt.ShiftModifier) && window.selectedIndex >= 0) {
            var lo = Math.min(window.selectedIndex, i)
            var hi = Math.max(window.selectedIndex, i)
            var range = []
            for (var k = lo; k <= hi; ++k) range.push(k)
            window.selectedIndexes = range
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
        var range = []
        for (var k = 0; k < controller.photos.rowCount(); ++k) range.push(k)
        window.selectedIndexes = range
        if (range.length > 0) window.selectedIndex = 0
    }

    Shortcut { sequence: "Ctrl+A"; onActivated: window.selectAll() }
    Shortcut { sequence: "Ctrl+D"; onActivated: window.clearSelection() }

    // Picasa gyorsbillentyűk: Ctrl+R jobbra, Ctrl+Shift+R balra forgat
    Shortcut {
        sequence: "Ctrl+R"
        onActivated: if (trayStar.targetRow >= 0)
                         controller.rotateRight(trayStar.targetRow)
    }
    Shortcut {
        sequence: "Ctrl+Shift+R"
        onActivated: if (trayStar.targetRow >= 0)
                         controller.rotateLeft(trayStar.targetRow)
    }
    // Picasa: F2 = átnevezés, Ctrl+Shift+S = exportálás mappába
    Shortcut {
        sequence: "F2"
        onActivated: if (!window.viewerOpen && window.selectedIndex >= 0)
                         renameDialog.openFor(window.selectedIndex)
    }
    Shortcut {
        sequence: "Ctrl+Shift+S"
        onActivated: if (!window.viewerOpen) exportDialog.openForSelection()
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
        onRenameRequested: renameDialog.openFor(window.selectedIndex)
        onExportRequested: exportDialog.openForSelection()
        onLocateRequested: {
            var p = controller.photos.filePathAt(window.selectedIndex)
            if (p.length > 0) fileOpsController.revealPhoto(p)
        }
        onDeleteRequested: deleteConfirmDialog.openFor(window.selectedPaths())
    }

    FolderManagerDialog { id: folderManager }

    // első indítás: nincs még figyelt mappa → Mappakezelő felajánlása
    Component.onCompleted: {
        if (controller.watchedFolders.length === 0)
            folderManager.open()
    }

    // Eszköztár: Importálás | (szűrők középen) | kereső jobbra
    header: Rectangle {
        height: 34
        color: Theme.chromeBg
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width; height: 1
            color: Theme.chromeBorder
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 8; anchors.rightMargin: 8
            spacing: 10
            PicasaButton {
                text: qsTr("Import")
                enabled: false
                Layout.preferredWidth: 100
                Layout.preferredHeight: 24
            }
            Item { Layout.fillWidth: true }
            Column {
                Layout.alignment: Qt.AlignVCenter
                spacing: 0
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: qsTr("Filters")
                    font.pixelSize: 9
                    color: Theme.textGray
                }
                Row {
                    spacing: 3

                    // szűrő-kapcsolók (kézikönyv 09): ★ ☺ ⚲ ▤ + csúszka;
                    // a bekapcsolt szűrő tónusa jelölő kék
                    Rectangle {
                        width: 22; height: 20; radius: 2
                        color: controller.filterActive ? "#ffffff" : "transparent"
                        border.width: controller.filterActive ? 1 : 0
                        border.color: Theme.selectionBlue
                        Text {
                            anchors.centerIn: parent
                            text: "★"
                            font.pixelSize: 13
                            color: controller.filterActive
                                   ? Theme.selectionBlue
                                   : (starFilter.hovered ? Theme.starYellow : "#8f8b83")
                        }
                        HoverHandler { id: starFilter }
                        TapHandler {
                            onTapped: controller.filterActive
                                      ? controller.clearFilter()
                                      : controller.showStarred()
                        }
                    }
                    Text {   // arc-szűrő (3. fázis)
                        width: 22; height: 20
                        text: "☺"; font.pixelSize: 13; color: "#8f8b83"
                        opacity: 0.45
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    Text {   // geo-szűrő
                        width: 22; height: 20
                        text: "⚲"; font.pixelSize: 13; color: "#8f8b83"
                        opacity: 0.45
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    Text {   // mozgókép / méret
                        width: 22; height: 20
                        text: "▤"; font.pixelSize: 12; color: "#8f8b83"
                        opacity: 0.45
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    Item { width: 6; height: 1 }
                    Slider {
                        width: 90; height: 20
                        enabled: false
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
            Item { width: 20 }
            // Picasa-hű kereső: fehér mező nagyítóval, törlő ×-szel
            Rectangle {
                Layout.preferredWidth: 300
                Layout.preferredHeight: 24
                radius: 3
                color: "#ffffff"
                border.color: Theme.chromeBorder
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6
                    anchors.rightMargin: 6
                    spacing: 5
                    Item {   // rajzolt nagyító
                        width: 12; height: 12
                        Rectangle {
                            x: 0; y: 0; width: 9; height: 9; radius: 4.5
                            color: "transparent"
                            border.color: "#8f8b83"; border.width: 1.5
                        }
                        Rectangle {
                            x: 8; y: 8; width: 4; height: 1.5
                            rotation: 45; color: "#8f8b83"
                        }
                    }
                    TextInput {
                        id: searchField
                        objectName: "searchField"
                        Layout.fillWidth: true
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                        clip: true
                        verticalAlignment: TextInput.AlignVCenter
                        selectByMouse: true
                        onTextEdited: {
                            window.clearSelection()
                            controller.search(text)
                            suggestionsTimer.restart()
                        }
                        Text {
                            visible: searchField.text.length === 0
                                     && !searchField.activeFocus
                            anchors.verticalCenter: parent.verticalCenter
                            text: qsTr("Search")
                            color: "#8f8b83"
                            font.pixelSize: Theme.fontSize
                        }
                    }
                    Rectangle {   // törlő gomb, csak ha van mit törölni
                        objectName: "searchClear"
                        visible: searchField.text.length > 0
                        width: 14; height: 14; radius: 7
                        color: searchClearHover.hovered ? "#c94b3d" : "#b0b0b0"
                        Text {
                            anchors.centerIn: parent
                            text: "✕"; color: "white"; font.pixelSize: 8
                            font.bold: true
                        }
                        HoverHandler { id: searchClearHover }
                        TapHandler {
                            onTapped: {
                                searchField.clear()
                                window.clearSelection()
                                controller.search("")
                                searchSuggestionsBox.suggestions = []
                            }
                        }
                    }
                }
            }
            // Verzió + build a jobb felső sarokban — halványan, hogy
            // zavartalanul, de bármikor ellenőrizhető legyen, PONTOSAN
            // melyik commit fut (appVersion → version.version_string()).
            Text {
                objectName: "versionLabel"
                Layout.alignment: Qt.AlignVCenter
                text: appVersion
                font.pixelSize: 9
                color: Theme.textGray
                opacity: 0.6
                ToolTip.visible: versionHover.hovered
                ToolTip.text: qsTr("Verzió és build")
                HoverHandler { id: versionHover }
            }
        }
    }

    // Kereső-javaslatok (#7): gépelés után rövid szünettel (debounce)
    // kérjük le, hogy NAS-on se fusson lekérdezés minden billentyűre.
    function refreshSuggestions() {
        searchSuggestionsBox.suggestions =
            controller.searchSuggestions(searchField.text)
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
        query: searchField.text
        visible: suggestions.length > 0 && searchField.text.length > 0
                 && !window.viewerOpen
        onChosen: function(kind, name, param) {
            if (kind === "folder") {
                searchField.clear()
                window.clearSelection()
                controller.selectFolder(param)
            }
            suggestions = []
        }
    }

    PhotoViewer {
        id: photoViewer
        objectName: "photoViewer"
        anchors.fill: parent
        visible: window.viewerOpen
        photosModel: controller.photos
        onClosed: {
            window.viewerOpen = false
            window.selectedIndex = currentIndex   // a rács kövesse a nézőt
            window.selectedIndexes = [currentIndex]
            // a szerkesztések (filters=) azonnal látsszanak a rácson —
            // NAS-on a fájlfigyelő nem szól, nem várhatunk a rescanre (#59);
            // a feedben (#64) a néző át is léphetett másik mappába, ezért a
            // nézett kép mappáját frissítjük
            controller.resyncFolderOfRow(currentIndex)
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
                if (searchField.text.trim().length > 0) {
                    // #45: aktív keresésnél a szűrés megmarad, a
                    // találatok a mappára szűkülnek (Picasa-viselkedés)
                    controller.selectFolderKeepSearch(path)
                } else {
                    searchField.clear()
                    controller.selectFolder(path)
                }
            }
            onStarredChosen: {
                searchField.clear()
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

                // Könyvtár-feed (#64): az ÖSSZES kép egyetlen görgethető
                // folyamban, a bal hasáb mappa-sorrendjében — mappánként
                // fejléc + képfolyam, ahogy az eredeti Picasa lightboxa.
                ListView {
                    id: grid
                    objectName: "photoGrid"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    // kereséskor a #7-es csoportosított találat-nézet fut
                    visible: !controller.searchActive
                    model: controller.feedGroups
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
                    readonly property int nominalCellWidth: window.thumbSize + 18
                    readonly property int cellHeight: window.thumbSize + 18
                        + (controller.thumbCaptionMode !== "none" ? 16 : 0)
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
                        var t = controller.photos.navigate(
                            window.selectedIndex, direction, columns)
                        if (t < 0) return
                        window.selectedIndex = t
                        window.selectedIndexes = [t]
                        selectionAnchor = t
                        scrollToRow(t)
                    }
                    // Shift+nyíl (#96): a horgony és a cél-index közti
                    // tartomány kijelölése; visszafelé lépve szűkül
                    function extendSelection(direction) {
                        if (window.selectedIndex < 0) {
                            moveSelection(direction); return
                        }
                        if (selectionAnchor < 0)
                            selectionAnchor = window.selectedIndex
                        var t = controller.photos.navigate(
                            window.selectedIndex, direction, columns)
                        if (t < 0) return
                        window.selectedIndex = t
                        var lo = Math.min(selectionAnchor, t)
                        var hi = Math.max(selectionAnchor, t)
                        var sel = []
                        for (var r = lo; r <= hi; ++r) sel.push(r)
                        window.selectedIndexes = sel
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
                    }
                    // teszt-segéd (#95): az utolsó csoport aljának távolsága
                    // a viewport tetejétől (<=0 vagy null → üres lap látszik)
                    function feedEndGap() {
                        var it = itemAtIndex(count - 1)
                        if (!it) return null
                        return it.y + it.height - contentY
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
                    }

                    // -- görgetés: mappára ugrás + pozíció-megőrzés --------
                    // A feedGroups-frissítés (modell-csere) nullázná a
                    // contentY-t; mappa-kattintásnál viszont a választott
                    // csoporthoz ugrunk.
                    property real savedY: 0
                    property bool restoring: false
                    property string pendingPath: ""
                    onContentYChanged: {
                        if (!restoring && (contentY > 0 || moving))
                            savedY = contentY
                    }
                    onMovementEnded: savedY = contentY
                    function scrollToGroup(path) {
                        for (var i = 0; i < model.length; ++i)
                            if (model[i].path === path) {
                                positionViewAtIndex(i, ListView.Beginning)
                                savedY = contentY
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
                                grid.restoring = true
                                grid.contentY = Math.min(
                                    grid.savedY,
                                    Math.max(0, grid.contentHeight - grid.height))
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
                        var c0 = Math.max(0, Math.floor(left / pitch))
                        var c1 = Math.min(cols - 1, Math.floor(right / pitch))
                        var r0 = Math.max(0, Math.floor(top / cellHeight))
                        var r1 = Math.floor(bottom / cellHeight)
                        var result = []
                        for (var r = r0; r <= r1; ++r)
                            for (var c = c0; c <= c1; ++c) {
                                var idx = r * cols + c
                                if (idx >= 0 && idx < count)
                                    result.push(start + idx)
                            }
                        return result
                    }
                    function applyLasso(start, count, flowWidth,
                                        x1, y1, x2, y2, modifiers) {
                        var picked = lassoIndexes(
                            start, count, flowWidth, x1, y1, x2, y2)
                        if (Number(modifiers) & Qt.ControlModifier) {
                            var merged = window.selectedIndexes.slice()
                            for (var i = 0; i < picked.length; ++i)
                                if (merged.indexOf(picked[i]) < 0)
                                    merged.push(picked[i])
                            window.selectedIndexes = merged
                        } else {
                            window.selectedIndexes = picked
                        }
                        if (picked.length > 0)
                            window.selectedIndex = picked[picked.length - 1]
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
                            description: (controller.descriptionRevision,
                                controller.folderDescriptionOf(
                                    groupCol.modelData.path))
                            onDescriptionEdited: function(text) {
                                controller.setFolderDescriptionOf(
                                    groupCol.modelData.path, text)
                            }
                        }

                        Flow {
                            id: groupFlow
                            width: parent.width
                            Repeater {
                                model: groupCol.modelData.count
                                delegate: Item {
                                    id: slot
                                    required property int index
                                    readonly property int row:
                                        groupCol.modelData.start + slot.index
                                    // a photos.revision-nel együtt kötve:
                                    // modell-frissüléskor újraértékelődik
                                    readonly property var info:
                                        (controller.photos.revision,
                                         controller.photos.itemAt(slot.row))
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
                                        keywords: slot.info.keywords || ""
                                        resolution: slot.info.resolution || ""
                                        captionMode: controller.thumbCaptionMode
                                        // #85/#83: a megjelenő kép a névleges
                                        // méretre plafonozott, a kiegyenlítés
                                        // többlete a térközbe megy.
                                        maxContentWidth: grid.nominalCellWidth
                                        maxContentHeight: grid.cellHeight
                                        selected: window.selectedIndexes
                                            .indexOf(slot.row) !== -1
                                        onChosen: function(i, mods) {
                                            grid.forceActiveFocus()   // kurzorgombokhoz (#77)
                                            grid.selectionAnchor = i  // Shift+nyíl horgony (#96)
                                            window.handleThumbClick(i, mods)
                                        }
                                        onOpened: function(i) {
                                            window.viewerOpen = true
                                            photoViewer.show(i)
                                        }
                                        onLassoDragged: function(sx, sy, cx, cy) {
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
                                            window.openPhotoContextMenu(
                                                i, slot, cx, cy)
                                        }
                                    }
                                }
                            }
                        }
                    }
                    ScrollBar.vertical: ScrollBar {}

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

                // #7: keresési találatok mappánként csoportosítva (Picasa-
                // minta) — a GridView nem támogat szekció-fejlécet, ezért
                // csoportonként egy fejléc + egy nem-interaktív al-rács.
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
                            // #85: itt is kiegyenlített sor — az oszlopszám
                            // névleges méretből, a tényleges cellaWidth a
                            // szélességet tölti ki.
                            readonly property int nominalCellWidth: window.thumbSize + 18
                            readonly property int columns:
                                Math.max(1, Math.floor(width / nominalCellWidth))
                            cellWidth: columns > 0
                                ? Math.floor(width / columns) : nominalCellWidth
                            cellHeight: window.thumbSize + 18
                                + (controller.thumbCaptionMode !== "none" ? 16 : 0)
                            height: Math.ceil(
                                groupDelegate.modelData.photos.length / columns
                            ) * cellHeight
                            model: groupDelegate.modelData.photos

                            delegate: ThumbDelegate {
                                id: groupedThumb
                                required property var modelData
                                width: subgrid.cellWidth
                                height: subgrid.cellHeight
                                // #85/#83: a kép a névleges méretre plafonozott
                                maxContentWidth: subgrid.nominalCellWidth
                                maxContentHeight: subgrid.cellHeight
                                name: modelData.name
                                thumbUrl: modelData.thumbUrl
                                star: modelData.star
                                caption: modelData.caption
                                isVideo: modelData.isVideo
                                index: modelData.row
                                keywords: modelData.keywords
                                resolution: modelData.resolution
                                captionMode: controller.thumbCaptionMode
                                selected: window.selectedIndexes.indexOf(modelData.row) !== -1
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
    }

    footer: Column {
        width: parent.width

        // tömör acélkék infó-sáv; kijelöléskor a kép adatai
        Rectangle {
            width: parent.width; height: 20
            color: Theme.infoBar
            Text {
                anchors.centerIn: parent
                text: window.viewerOpen
                      ? controller.viewerInfo(photoViewer.currentIndex)
                      : (window.selectedIndexes.length === 1
                         ? controller.photoInfo(window.selectedIndex)
                         : controller.statusText)
                color: Theme.infoBarText
                font.pixelSize: Theme.fontSize
                font.bold: true
            }
        }

        Rectangle {
            width: parent.width; height: 52
            color: Theme.trayBg
            Rectangle {
                width: parent.width; height: 1
                color: Theme.trayBorder
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10; anchors.rightMargin: 10
                spacing: 8

                // kijelölés-tálca: a kijelölt képek miniatűrjei (Picasa)
                Item {
                    Layout.preferredWidth: 200
                    Layout.preferredHeight: 46
                    Flow {
                        anchors.fill: parent
                        spacing: 2
                        clip: true
                        Repeater {
                            model: window.selectedIndexes
                            delegate: Image {
                                required property var modelData
                                width: 20; height: 20
                                source: controller.photos.thumbUrlAt(
                                    Number(modelData))
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                            }
                        }
                    }
                    Text {
                        visible: window.selectedIndexes.length === 0
                        anchors.centerIn: parent
                        text: qsTr("Selection")
                        color: "#b8b8b8"
                        font.pixelSize: Theme.fontSize
                    }
                }

                PicasaButton {
                    id: trayStar
                    readonly property int targetRow: window.viewerOpen
                        ? photoViewer.currentIndex : window.selectedIndex
                    readonly property bool multi:
                        !window.viewerOpen && window.selectedIndexes.length > 1
                    enabled: window.viewerOpen || window.selectedIndex >= 0
                    Layout.preferredWidth: 34
                    onClicked: multi
                               ? controller.toggleStarMany(window.selectedIndexes)
                               : controller.toggleStar(targetRow)
                    contentItem: Text {
                        objectName: "trayStarLabel"
                        text: "★"
                        font.pixelSize: 15
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        // arany, ha a kiválasztott kép csillagos; egyébként
                        // világos kontúr-csillag (Picasa-minta, nem fekete!)
                        color: (controller.photos.revision,
                                controller.photos.starAt(trayStar.targetRow))
                               ? Theme.starYellow : "#ffffff"
                        style: Text.Outline
                        styleColor: "#9a9a9a"
                    }
                }
                PicasaButton {
                    text: "↺"
                    enabled: window.viewerOpen || window.selectedIndex >= 0
                    Layout.preferredWidth: 34
                    onClicked: trayStar.multi
                               ? controller.rotateLeftMany(window.selectedIndexes)
                               : controller.rotateLeft(trayStar.targetRow)
                }
                PicasaButton {
                    text: "↻"
                    enabled: window.viewerOpen || window.selectedIndex >= 0
                    Layout.preferredWidth: 34
                    onClicked: trayStar.multi
                               ? controller.rotateRightMany(window.selectedIndexes)
                               : controller.rotateRight(trayStar.targetRow)
                }
                Item { Layout.fillWidth: true }
                // nagyítás-csúszka − / + jelekkel (kézikönyv 06)
                Text { text: "−"; color: Theme.textGray; font.pixelSize: 13 }
                Slider {
                    id: sizeSlider
                    from: 72; to: 256; value: window.thumbSize
                    Layout.preferredWidth: 140
                    onMoved: window.thumbSize = value
                }
                Text { text: "+"; color: Theme.textGray; font.pixelSize: 13 }
                Item { width: 10 }
                PicasaButton { text: qsTr("E-Mail"); enabled: false }
                PicasaButton { text: qsTr("Print"); enabled: false }
                PicasaButton {
                    objectName: "trayExportButton"
                    text: qsTr("Export")
                    enabled: !window.viewerOpen
                             && window.selectedIndexes.length > 0
                    onClicked: exportDialog.openForSelection()
                }
                Item { width: 6 }
                // az egyetlen zöld elsődleges tett — jobbra igazítva,
                // a képernyő vizuális súlypontja (kézikönyv 01/08)
                PicasaButton {
                    text: qsTr("Upload to Google Photos")
                    enabled: false
                    accent: Theme.picasaGreen
                }
            }
        }
    }

    // -- fájlműveletek (#15): kontextusmenü + dialógusok --------------------

    PhotoContextMenu {
        id: photoContextMenu
        onRenameRequested: renameDialog.openFor(window.fileOpTargetRow)
        onMoveRequested: {
            moveFolderDialog.paths = window.selectedPaths()
            if (moveFolderDialog.paths.length > 0) moveFolderDialog.open()
        }
        onDeleteRequested: deleteConfirmDialog.openFor(window.selectedPaths())
        onLocateRequested: {
            var p = controller.photos.filePathAt(window.fileOpTargetRow)
            if (p.length > 0) fileOpsController.revealPhoto(p)
        }
    }

    Dialog {
        id: renameDialog
        objectName: "renameDialog"
        title: qsTr("Rename...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string targetPath: ""
        function openFor(row) {
            var p = controller.photos.filePathAt(row)
            if (p.length === 0) return
            targetPath = p
            renameField.text = controller.photos.itemAt(row).name || ""
            open()
            renameField.forceActiveFocus()
            renameField.selectAll()
        }
        onAccepted: {
            if (renameField.text.trim().length > 0)
                fileOpsController.renamePhoto(
                    targetPath, renameField.text.trim())
        }
        TextField {
            id: renameField
            objectName: "renameField"
            width: 300
            font.pixelSize: Theme.fontSize
        }
    }

    FolderDialog {
        id: moveFolderDialog
        objectName: "moveFolderDialog"
        title: qsTr("Move to Folder...")
        property var paths: []
        onAccepted: {
            var dest = selectedFolder.toString()
            for (var i = 0; i < paths.length; ++i)
                fileOpsController.movePhoto(paths[i], dest)
            window.clearSelection()
        }
    }

    Dialog {
        id: deleteConfirmDialog
        objectName: "deleteConfirmDialog"
        title: qsTr("Delete from Disk")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Yes | Dialog.No
        property var paths: []
        function openFor(pathList) {
            if (pathList.length === 0) return
            paths = pathList
            open()
        }
        onAccepted: {
            for (var i = 0; i < paths.length; ++i)
                fileOpsController.deletePhoto(paths[i])
            window.clearSelection()
        }
        Text {
            text: qsTr("%n picture(s) will be moved to the system trash.",
                       "", deleteConfirmDialog.paths.length)
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Dialog {
        id: fileOpsErrorDialog
        objectName: "fileOpsErrorDialog"
        title: qsTr("File operation failed")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        Text {
            width: 380
            text: fileOpsErrorDialog.message
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Connections {
        target: fileOpsController
        function onOperationFailed(operation, message) {
            fileOpsErrorDialog.message = message
            fileOpsErrorDialog.open()
        }
    }

    // -- exportálás mappába (#16, Ctrl+Shift+S) -----------------------------

    Dialog {
        id: exportDialog
        objectName: "exportDialog"
        title: qsTr("Export Picture to Folder...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string targetFolder: ""
        // a méret-lista indexei → leghosszabb oldal px-ben (0 = eredeti)
        readonly property var sizeOptions: [0, 2048, 1600, 1024, 800]
        function openForSelection() {
            if (window.selectedIndexes.length === 0) return
            open()
        }
        onOpened: standardButton(Dialog.Ok).enabled = Qt.binding(
            function() { return exportDialog.targetFolder.length > 0 })
        onAccepted: controller.exportRows(
            window.selectedIndexes, targetFolder,
            sizeOptions[exportSizeBox.currentIndex], exportQuality.value)
        ColumnLayout {
            spacing: 10
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Target folder:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                Text {
                    objectName: "exportTargetLabel"
                    Layout.preferredWidth: 240
                    elide: Text.ElideMiddle
                    text: exportDialog.targetFolder.length > 0
                          ? exportDialog.targetFolder
                          : qsTr("(not selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    text: qsTr("Browse...")
                    onClicked: exportTargetDialog.open()
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Image size:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                ComboBox {
                    id: exportSizeBox
                    objectName: "exportSizeBox"
                    Layout.preferredWidth: 160
                    model: [qsTr("Original size"), "2048 px", "1600 px",
                            "1024 px", "800 px"]
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Image quality:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                SpinBox {
                    id: exportQuality
                    objectName: "exportQuality"
                    from: 1; to: 100; value: 85
                }
            }
        }
    }

    FolderDialog {
        id: exportTargetDialog
        title: qsTr("Export Picture to Folder...")
        onAccepted: exportDialog.targetFolder = selectedFolder.toString()
    }

    Dialog {
        id: exportResultDialog
        objectName: "exportResultDialog"
        title: qsTr("Export")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        Text {
            text: exportResultDialog.message
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Connections {
        target: controller
        function onExportFinished(done, failed) {
            exportResultDialog.message = failed > 0
                ? qsTr("%1 pictures exported, %2 failed.")
                    .arg(done).arg(failed)
                : qsTr("%1 pictures exported.").arg(done)
            exportResultDialog.open()
        }
    }

    Dialog {
        id: aboutDialog
        title: qsTr("About PicasaPy")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        Column {
            spacing: 10
            Image {
                anchors.horizontalCenter: parent.horizontalCenter
                source: Qt.resolvedUrl("../assets/logo.svg")
                sourceSize.width: 320
                fillMode: Image.PreserveAspectFit
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "PicasaPy " + appVersion + " — "
                      + qsTr("A modern, open Picasa successor.")
                      + "\nGPL-3.0 · github.com/sanchomuzax/PicasaPy"
                font.pixelSize: Theme.fontSize
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
