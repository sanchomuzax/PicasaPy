import QtQml
import QtQuick
import PicasaPy
import "../selection.js" as Selection

// A könyvtár kijelölésének műveletei és mappaváltás-követése.
Item {
    id: root
    objectName: "mainLibrarySelectionState"
    visible: false
    width: 0
    height: 0

    required property var hostWindow
    required property var hostController
    required property var hostPhotoViewer
    required property var hostMainDialogs
    required property var hostPhotoContextMenu
    required property var hostFolderPane
    required property var hostScreensaverAlbumConfirmLoader
    required property var hostFaceScanDialog
    required property var hostFaceScanController
    required property string screensaverAddedMessage

    // a kijelölt sorok listája (#12) — több-kijelölés, vagy ha az nincs,
    // az utoljára kattintott kép
    function selectedRows() {
        return Selection.effectiveRows(
            hostWindow.selectedIndexes, hostWindow.selectedIndex)
    }

    // #5883: a mentés csak akkor írja lemezre a kijelölést, ha valamelyik
    // kép filters lánca eltér a lemezre mentett állapottól. A modell
    // `hasEdits` mezője ezt a `.picasa.ini`-ben tárolt láncból adja; a
    // `photos.revision` a QML-kötést a láncváltás után újraértékelteti.
    function vanMentetlenSzerkesztes(sorok) {
        if (!hostController || !hostController.photos || !sorok) return false
        for (var i = 0; i < sorok.length; ++i) {
            var foto = hostController.photos.itemAt(Number(sorok[i]))
            if (foto && foto.hasEdits === true) return true
        }
        return false
    }

    readonly property bool kijelolesbenVanMentetlenSzerkesztes:
        hostController
        ? (hostController.photos.revision,
           hostWindow.vanMentetlenSzerkesztes(hostWindow.selectedRows())) : false
    readonly property bool muveletiCelbanVanMentetlenSzerkesztes:
        hostController
        ? (hostController.photos.revision,
           hostWindow.vanMentetlenSzerkesztes(hostWindow.photoActionRows())) : false

    // A fotóhoz kötött menük célpontja nézőben a szerkesztett oldal, a
    // könyvtárban pedig a kijelölés. A kijelölés megmarad a néző mögött,
    // ezért ott nem használható a menü célpontjának.
    function photoActionRows() {
        if (hostWindow.viewerOpen) {
            var sor = Number(hostPhotoViewer._kijeloltSort())
            return sor >= 0 ? [sor] : []
        }
        return hostWindow.selectedRows()
    }

    function prepareRenameSelection(row, newName) {
        if (!hostController || !newName) return
        var oldPath = hostController.photos.filePathAt(Number(row))
        var separator = oldPath.lastIndexOf("/")
        if (separator < 0) return
        hostWindow._pendingRenamePhotoId = hostController.photos.idAt(Number(row))
        hostWindow._pendingRenameTargetPath = oldPath.substring(0, separator + 1) + newName
    }

    function photoActionIndex() {
        if (hostWindow.viewerOpen) return Number(hostPhotoViewer._kijeloltSort())
        if (hostWindow.selectedIndex >= 0) return hostWindow.selectedIndex
        var sorok = hostWindow.selectedRows()
        return sorok.length > 0 ? Number(sorok[0]) : -1
    }

    function photoActionPaths() {
        var rows = hostWindow.photoActionRows()
        var paths = []
        if (!hostController) return paths
        for (var k = 0; k < rows.length; ++k) {
            var path = hostController.photos.filePathAt(Number(rows[k]))
            if (path.length > 0) paths.push(path)
        }
        return paths
    }

    // #5835: mappa nélküli nézetben a kijelölt vagy fókuszban levő kép
    // mappája az üres album tárolási helye. Sima mappanézetben a #5812
    // szerinti aktuális mappa marad az elsődleges cél.
    function newAlbumFolderPath() {
        if (!hostController) return ""
        if (hostController.viewModeName === "folder" && hostController.currentFolder)
            return hostController.currentFolder

        var photoPath = ""
        var paths = hostWindow.photoActionPaths()
        if (paths.length > 0) {
            photoPath = paths[0]
        } else {
            var row = hostWindow.photoActionIndex()
            if (row >= 0 && hostController.photos)
                photoPath = hostController.photos.filePathAt(row)
        }
        var separator = Math.max(
            photoPath.lastIndexOf("/"), photoPath.lastIndexOf("\\")
        )
        return separator > 0 ? photoPath.substring(0, separator) : ""
    }

    function addPhotosToScreensaver(paths) {
        var added = hostController ? hostController.addScreensaverPhotos(paths) : 0
        hostWindow.errorBanner.notice = true
        hostWindow.errorBannerText.text = screensaverAddedMessage.arg(added)
    }

    function requestAddToScreensaver() {
        var paths = hostWindow.photoActionPaths()
        if (hostController && hostController.currentAlbumToken !== "") {
            hostScreensaverAlbumConfirmLoader.ensure().openFor(paths)
            return
        }
        hostWindow.addPhotosToScreensaver(paths)
    }

    // #4271: az eredeti megerősítési küszöb 30 fölött van; a kijelölést
    // pillanatfelvételként adjuk át, hogy a párbeszéd alatt ne változzon a cél.
    function addTagToRows(rowList, keyword) {
        if (!hostController || !rowList || rowList.length === 0) return
        var rows = rowList.slice()
        if (rows.length <= 30) {
            hostController.addKeywordToRows(rows, keyword)
            return
        }
        hostMainDialogs.bulkTagConfirmLoader.ensure().askFor(rows, keyword)
    }

    // a kijelölt képek abszolút útvonalai (#15/#16) — a fájlműveletek a
    // művelet ELŐTT gyűjtött útvonal-listán futnak, így a közben frissülő
    // rács-indexek nem tévesztenek célt
    function selectedPaths() {
        var rows = hostWindow.selectedRows()
        var paths = []
        for (var k = 0; k < rows.length; ++k) {
            var p = hostController.photos.filePathAt(Number(rows[k]))
            if (p.length > 0) paths.push(p)
        }
        return paths
    }

    function resetFacesForPaths(paths) {
        if (!hostFaceScanController || !paths || paths.length === 0)
            return
        if (hostFaceScanController.resetFacesForPhotos(paths) > 0) {
            if (hostController) hostController.refreshCollections()
            hostPhotoViewer.facesEditRevision += 1
            // A hiányzó modellről a meglévő Arckeresés ablak ad érthető
            // okot és letöltési lehetőséget; reset után ne maradjon néma.
            if (!hostFaceScanController.isAvailable())
                hostFaceScanDialog.open()
        }
    }

    // jobbklikk a rácson (#15): a klikkelt kép kerüljön kijelölésbe (ha még
    // nincs benne), majd a kontextusmenü a kattintás helyén nyílik
    function openPhotoContextMenu(index, item, x, y) {
        if (hostWindow.selectedIndexes.indexOf(index) === -1) {
            hostWindow.selectedIndexes = [index]
            hostWindow.selectedIndex = index
        }
        hostWindow.fileOpTargetRow = index
        hostPhotoContextMenu.popup(item, x, y)
    }

    // #4534: a mappacsoport aktuális rácssorrendjében a legelső kijelölt
    // képtől a csoport végéig kijelöl, majd megnyitja a mappa tulajdonságait.
    function splitFolderHere() {
        if (!hostController || hostController.currentFolder === ""
                || hostController.currentAlbumToken !== ""
                || hostController.currentPersonName !== "")
            return
        var rows = hostWindow.selectedRows()
        if (rows.length === 0) return
        var currentFolder = hostController.currentFolder
        var first = -1
        for (var i = 0; i < rows.length; ++i) {
            var row = Number(rows[i])
            var path = hostController.photos.filePathAt(row)
            if (path.substring(0, path.lastIndexOf("/")) === currentFolder
                    && (first < 0 || row < first))
                first = row
        }
        if (first < 0) return
        var range = hostController.photos.groupRange(first)
        if (range.length !== 2) return
        var paths = []
        var selected = []
        for (var row = first; row <= Number(range[1]); ++row) {
            var imagePath = hostController.photos.filePathAt(row)
            if (imagePath.substring(0, imagePath.lastIndexOf("/"))
                    !== currentFolder)
                return
            paths.push(imagePath)
            selected.push(row)
        }
        if (paths.length === 0) return
        var photo = hostController.photos.itemAt(first)
        var date = photo && photo.takenAt ? photo.takenAt.substring(0, 10) : ""
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return
        hostWindow.selectedIndexes = selected
        hostWindow.selectedIndex = first
        hostFolderPane.openSplitFolderHere(paths, date)
    }

    // Kijelölés-logika (Picasa): sima katt = egy kép; Ctrl = hozzávesz/
    // elvesz; Shift = tartomány a horgonytól. (Számítás: selection.js)
    function handleThumbClick(index, modifiers) {
        var i = Number(index)
        var mods = Number(modifiers)
        if (mods & Qt.ControlModifier) {
            hostWindow.selectedIndexes =
                Selection.toggled(hostWindow.selectedIndexes, i)
            hostWindow.selectedIndex = i
        } else if ((mods & Qt.ShiftModifier) && hostWindow.selectedIndex >= 0) {
            // #1219: a tartomány a HORGONY mappacsoportján belül marad —
            // az eredetiben a tartomány-mag mindig egyetlen album
            // kijelölés-csomópontján fut, nem tud mappahatárt átlépni.
            var hatar = hostController.photos.groupRange(hostWindow.selectedIndex)
            var veg = i
            if (hatar.length === 2)
                veg = Math.max(hatar[0], Math.min(hatar[1], i))
            hostWindow.selectedIndexes =
                Selection.range(hostWindow.selectedIndex, veg)
        } else {
            hostWindow.selectedIndexes = [i]
            hostWindow.selectedIndex = i
        }
    }
    // ⚠️ #1145: MAPPAVÁLTÁSKOR a kijelölés törlődik.
    //
    // Az eredetiben az előző mappa kijelölés-csomópontját a program
    // elengedi (`0x0056bc10` → `0x718a50`), és a helyére az újat teszi.
    // Nálunk a kijelölés túlélte a váltást — így egy másik mappában
    // végzett művelet (csillag, forgatás, törlés) a KORÁBBI mappa képeire
    // hatott volna.
    //
    // A `currentFolder` a `statusChanged`-en jelez, ezért a mappa saját
    // értékét figyeljük, nem a jelzést: így csak VALÓDI váltásra törlünk.
    property string _lastFolder: ""
    Connections {
        target: hostController
        function onStatusChanged() {
            var folder = hostController ? hostController.currentFolder : ""
            if (folder === root._lastFolder) return
            root._lastFolder = folder
            // #1183: ha a kijelölés MÁR az új mappában van, akkor a váltást
            // épp a rács fókusza okozta (a felhasználó ott kattintott) —
            // nincs mit elengedni, az előző mappáé úgyis lecserélődött.
            if (root._selectionInFolder(folder)) return
            root.clearSelection()
        }
    }

    // #1183: a fókuszsor mappája — a bal hasáb kiemelése ezt követi
    function _folderOfRow(row) {
        if (!hostController || row < 0) return ""
        var groups = hostController.feedGroups
        if (!groups) return ""
        for (var i = 0; i < groups.length; ++i) {
            var g = groups[i]
            if (row >= g.start && row < g.start + g.count) return g.path
        }
        return ""
    }

    function _selectionInFolder(path) {
        return path !== "" && hostWindow._folderOfRow(hostWindow.selectedIndex) === path
    }

    // A rács fókusza vezeti a jelenlegi mappát (az eredetiben `0x0056bc10`
    // → `0x56b910`, „a jelenlegi album megváltozott"). Egy helyen kötjük be,
    // így a kattintás, a nyilas léptetés és a programból állított fókusz is
    // ugyanígy viselkedik.
    Connections {
        target: hostWindow
        function onSelectedIndexChanged() {
            var folder = hostWindow._folderOfRow(hostWindow.selectedIndex)
            if (folder !== "" && hostController) hostController.focusFolder(folder)
        }
    }

    function clearSelection() {
        hostWindow.selectedIndexes = []
        hostWindow.selectedIndex = -1
    }
    // ⚠️ #1145: a kijelölés hatóköre a JELENLEGI MAPPA, nem a teljes feed.
    //
    // Az eredetiben az „Az összes kijelölése" (`0x9cb8`) kezelője
    // (`0x005e5070`) EGYETLEN kijelölés-csomóponton dolgozik, és az EGY
    // mappához tartozik (`CSelectionNode + 0x3c0`). A Picasában
    // egyáltalán nem létezik mappákon átnyúló kijelölés.
    //
    // Nálunk a Ctrl+A tízezres nagyságrendű sort jelölt ki — a tulajdonos
    // ezt jelentette (#1184), és emiatt „majdnem lefagyott az app".
    //
    // A csoportot a jelenlegi kijelölés/fókusz sora dönti el; ha nincs
    // ilyen, a jelenlegi mappa csoportja.
    function _currentGroup() {
        if (!hostController) return null
        var groups = hostController.feedGroups
        if (!groups || groups.length === 0) return null
        var row = hostWindow.selectedIndex
        if (row >= 0) {
            for (var i = 0; i < groups.length; ++i) {
                var g = groups[i]
                if (row >= g.start && row < g.start + g.count) return g
            }
        }
        var current = hostController.currentFolder
        for (var j = 0; j < groups.length; ++j)
            if (groups[j].path === current) return groups[j]
        return groups[0]
    }

    function _groupRows() {
        var g = hostWindow._currentGroup()
        if (!g) return Selection.allRows(hostController.photos.rowCount())
        var rows = []
        for (var i = g.start; i < g.start + g.count; ++i) rows.push(i)
        return rows
    }

    function selectAll() {
        var range = hostWindow._groupRows()
        hostWindow.selectedIndexes = range
        if (range.length > 0) hostWindow.selectedIndex = range[0]
    }
    // #422: „Kiválasztás megfordítása" (Ctrl+I) — a mappa-kontextusmenü és
    // a Szerkesztés menü tétele
    function invertSelection() {
        // #1145: a megfordítás is a jelenlegi mappán belül marad
        var scope = hostWindow._groupRows()
        var current = hostWindow.selectedIndexes
        var rows = []
        for (var i = 0; i < scope.length; ++i)
            if (current.indexOf(scope[i]) === -1) rows.push(scope[i])
        hostWindow.selectedIndexes = rows
        hostWindow.selectedIndex = rows.length > 0 ? rows[0] : -1
    }
    // #426: „Csillagozottak kijelölése" (Szerkesztés menü) — a jelenlegi
    // nézet csillagos képeit jelöli ki (NEM a Mappák panel nézet-szűrője).
    function selectStarred() {
        // #1145: a csillagozottak is a jelenlegi mappából
        var scope = hostWindow._groupRows()
        var rows = []
        for (var i = 0; i < scope.length; ++i)
            if (hostController.photos.starAt(scope[i])) rows.push(scope[i])
        hostWindow.selectedIndexes = rows
        hostWindow.selectedIndex = rows.length > 0 ? rows[0] : -1
    }
}
