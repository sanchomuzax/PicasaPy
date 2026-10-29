import QtQuick
import PicasaPy

FolderPane {
    id: folderPane
    required property var hostWindow
    required property var hostController
    required property var hostToolbar
    required property var hostBackupHost
    required property var hostFileOpsDialogs
    required property var hostCollectionPasswordDialog
    required property var hostFileOpsController
    required property var hostFaceScanController
    required property var hostFolderHierarchyController
    // A húzott szélesség mentése — késleltetve, hogy a húzás közbeni
    // pixelenkénti változás ne írja folyamatosan a QSettings-t.
    onWidthChanged: folderPaneWidthSaver.restart()

    Timer {
        id: folderPaneWidthSaver
        interval: 400
        onTriggered: {
            if (hostController && folderPane.width > 0) {
                hostController.setFolderPaneWidth(Math.round(folderPane.width))
            }
        }
    }
    // #305: null-őr — a hostController a QML-engine leépítésekor
    // átmenetileg null lehet, amikor ezek a kötések utoljára
    // kiértékelődnek
    foldersModel: hostController ? hostController.folders : null
    // #702: a bal hasáb hierarchikus (fa) mappanézete. A `typeof`-őr
    // NEM elhagyható: a hasábot vezérlő nélkül betöltő próbáknál egy
    // őrizetlen hivatkozás QML-szkripthibát dobna.
    // #1454: a nézetmódot (Egyszerű / Fa) is ez a vezérlő tartja — a
    // `FolderPane.treeViewMode` alapértelmezésben rá kötődik, ezért
    // itt NEM szabad felülírni (korábban `false` volt beégetve, és a
    // menü bekötése után is a lapos listán ragadt volna a hasáb).
    hierarchyController: (typeof hostFolderHierarchyController !== "undefined")
                         ? hostFolderHierarchyController : null
    selectedPath: hostController ? hostController.currentFolder : ""
    starredActive: hostController ? hostController.filterActive : false
    searchActive: hostController ? hostController.searchActive : false
    searchQuery: hostController ? hostController.searchQuery : ""
    searchResultCount: hostController ? hostController.searchResultCount : 0
    albumsModel: hostController ? hostController.albums : []
    selectedAlbumToken: hostController ? hostController.currentAlbumToken : ""
    // #26 (3. lépcső): az Emberek gyűjtemény + a „Névtelenek" sor
    peopleModel: hostController ? hostController.people : []
    selectedPersonName: hostController ? hostController.currentPersonName : ""
    unnamedFaceCount: (typeof hostFaceScanController !== "undefined" && hostFaceScanController)
                       ? (hostFaceScanController.unnamedCount ?? 0) : 0
    unnamedFacesActive: hostWindow.unnamedFacesOpen
                        && hostWindow.facesAlbumMode === "unnamed"
    // #449: a háttér-beolvasás haladása az albumlistában
    faceScanPercent: (typeof hostFaceScanController !== "undefined" && hostFaceScanController)
                      ? (hostFaceScanController.scanPercent ?? -1) : -1
    onFolderChosen: function(path) {
        hostWindow.clearSelection()
        hostWindow.unnamedFacesOpen = false
        if (hostToolbar.searchText.trim().length > 0) {
            // #45: aktív keresésnél a szűrés megmarad, a
            // találatok a mappára szűkülnek (Picasa-viselkedés)
            hostController.selectFolderKeepSearch(path)
        } else {
            hostToolbar.clearSearch()
            hostController.selectFolder(path)
        }
    }
    // #5704: a beépített és a felhasználói gyűjtemény jelszókezelése.
    onHiddenPasswordRequested:
        hostCollectionPasswordDialog.ensure().openForHiddenCollection()
    onCollectionPasswordRequested: function (collectionName) {
        hostCollectionPasswordDialog.ensure().openForCollection(
            collectionName)
    }
    onStarredChosen: {
        hostToolbar.clearSearch()
        hostWindow.clearSelection()
        hostWindow.unnamedFacesOpen = false
        hostController.showStarredAlbum()
    }
    onAlbumChosen: function(token) {
        if (!hostController) return
        hostToolbar.clearSearch()
        hostWindow.clearSelection()
        hostWindow.unnamedFacesOpen = false
        hostController.showAlbum(token)
    }
    onPersonChosen: function(name) {
        if (!hostController) return
        hostToolbar.clearSearch()
        hostWindow.clearSelection()
        hostWindow.unnamedFacesOpen = false
        hostController.showPerson(name)
    }
    onUnnamedFacesChosen: {
        hostToolbar.clearSearch()
        hostWindow.clearSelection()
        hostWindow.facesAlbumMode = "unnamed"
        hostWindow.unnamedFacesOpen = true
    }
    // #26: a „Mellőzött emberek" album — ugyanaz a nézet, más
    // tartalommal és művelettel (a mellőzés visszavonása)
    onIgnoredFacesChosen: {
        hostToolbar.clearSearch()
        hostWindow.clearSelection()
        hostWindow.facesAlbumMode = "ignored"
        hostWindow.unnamedFacesOpen = true
    }
    // #457: „Exportált képek" — a Projektek gyűjtemény alatt
    exportedFolders: hostController ? hostController.exportedFolders : []
    // #1029: a Projektek gyűjtemény mappái (P2category)
    projectFolders: hostController ? hostController.projectFolders : []
    ignoredFaceCount: (typeof hostFaceScanController !== "undefined" && hostFaceScanController)
                       ? (hostController ? hostController.photos.revision : 0,
                          hostFaceScanController.ignoredCount ?? 0)
                       : 0
    ignoredFacesActive: hostWindow.unnamedFacesOpen
                        && hostWindow.facesAlbumMode === "ignored"
    // #455: fogd-és-vidd — a húzott KIJELÖLÉS kerül albumba. Az új
    // album ugyanazt a névkérő párbeszédet kapja, mint a menüből
    // indított (Fájl → Új album), hogy ne legyen két, kicsit
    // másképp viselkedő út ugyanarra.
    onNewAlbumPhotosDropped: function(rows) {
        if (rows && rows.length > 0)
            hostFileOpsDialogs.ensure().openNewAlbum(rows)
    }
    onPhotosDroppedOnAlbum: function(token, rows) {
        if (hostController && rows && rows.length > 0)
            hostController.addRowsToAlbum(rows, token)
    }
    // #5007: a rácsból mappára húzott kijelölés áthelyezése. A
    // DropArea a forrássorokat még a célmappa megnyitása előtt
    // pillanatfelvételként adja át; a fájlokat és a .picasa.ini-t a
    // FileOpsController meglévő kötegelt útja mozgatja.
    onPhotosDroppedOnFolder: function(path, rows) {
        if (!hostController || !hostFileOpsController || !path
                || !rows || rows.length === 0)
            return
        var paths = []
        for (var i = 0; i < rows.length; ++i) {
            var photoPath = hostController.photos.filePathAt(
                Number(rows[i]))
            if (photoPath.length > 0) paths.push(photoPath)
        }
        if (paths.length > 0
                && hostFileOpsController.destinationFolderExists(path))
            hostFileOpsController.movePhotos(paths, path, "rename")
    }
    onFolderDroppedOnFolder: function(sourcePath, targetPath) {
        if (hostFileOpsController && sourcePath && targetPath)
            hostFileOpsController.moveFolder(sourcePath, targetPath)
    }
    // #3681: a mentés-panel közös szűrő-szerződése (ld.
    // `FolderPane.qml`) — amíg a mentés-panel LÁTSZIK, a hasáb a
    // MÉG EL NEM MENTETT mappákra szűkül, pipával. A `visible`
    // (nem a `nyitva`) a mérce: nézegető, időrend vagy másik lap
    // közben a panel nem látszik, a hasábnak sincs mit szűrnie.
    mentesSzuroAktiv: hostBackupHost.visible
    mentesMentetlenMappak: hostBackupHost.mentetlenek
    mentesPipaltMappak: hostBackupHost.pipaltMappak
    mentesToltodnek: hostBackupHost.mappakToltodnek
    mentesVanKeszlet: hostBackupHost.kivalasztott >= 0
    onMentesPipaldKert: function (mappa, be) { hostBackupHost.pipald(mappa, be) }
}