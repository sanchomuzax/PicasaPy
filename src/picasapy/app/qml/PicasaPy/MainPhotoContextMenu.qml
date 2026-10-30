import QtQuick
import PicasaPy

// A főablak rácsának fotó-helyi menüje és annak gazda-bekötése (#6136).
PhotoContextMenu {
    id: root
    required property var hostWindow
    required property var hostController
    required property var hostFileOpsController
    required property var hostFileOpsDialogs
    required property var hostMainDialogs
    required property var hostMoveToNewPersonDialog
    required property var hostOpenWithDialog
    required property var hostRemoveFromAlbumDialog
    required property var hostRemovePeopleFacesDialog
    required property var hostSaveDialogs
    required property var hostToolbar
    // #1613: a lemezt CSAK a menü megnyitásakor kérdezzük meg — egy
    // kötés minden képkockán fájlrendszert olvasna.
    onAboutToShow: {
        var ut = hostController
            ? hostController.photos.filePathAt(hostWindow.fileOpTargetRow) : ""
        root.hasOriginalOnDisk =
            ut.length > 0 && hostFileOpsController.hasOriginalOnDisk(ut)
        // #3468: a „Keresés" almenü csak EGY kijelölt képnél jelenik meg
        var db = hostWindow.selectedRows().length
        root.kijeloltKepekSzama = db > 0 ? db : 1
        root.peopleThumbnailFaceAvailable = hostController
            ? hostController.canSetPersonThumbnail(
                Number(hostController.photos.idAt(hostWindow.fileOpTargetRow)),
                hostController.currentPersonName)
            : false
        // #5195: a „Társítás ▸" almenü listája a megnyitáskor készül
        root.nativeOpenWith = hostFileOpsController.hasNativeOpenWith()
        root.openWithApps = ut.length > 0
            ? hostFileOpsController.openWithChoices(ut) : []
    }
    // #17: pipa, ha a jobbklikkelt kép rejtett (photos.revision-nel
    // együtt kötve, hogy a menü újranyitáskor friss legyen)
    // #305: null-őr
    hideChecked: hostController
        ? (hostController.photos.revision,
           (hostController.photos.itemAt(hostWindow.fileOpTargetRow)
                .hidden === true))
        : false
    // #422: a mentés-parancsok aktív állapota — a jobbklikkelt képen
    // van-e szerkesztés, illetve van-e mentés-előtti másolat
    hasEdits: hostController
        ? (hostController.photos.revision,
           (hostController.photos.itemAt(hostWindow.fileOpTargetRow)
                .hasEdits === true))
        : false
    hasBackup: hostController
        ? hostController.hasSavedBackup(hostWindow.selectedRows()) : false
    onSaveRequested: hostSaveDialogs.ensure().openSave(hostWindow.selectedRows())
    onRevertRequested: hostSaveDialogs.ensure().openRevert(hostWindow.selectedRows())
    onUndoAllEditsRequested: hostMainDialogs.undoAllEditsDialog.ensure().openForLibrary(
        hostWindow.selectedRows())
    onResetFacesRequested: hostWindow.resetFacesForPaths(hostWindow.selectedPaths())
    onHideToggleRequested: hostWindow.toggleHiddenSelection()
    onMoveRequested: hostFileOpsDialogs.ensure().openMove(hostWindow.selectedPaths())
    onDeleteRequested: hostFileOpsDialogs.ensure().openDelete(hostWindow.selectedPaths())
    onLocateRequested: {
        var p = hostController.photos.filePathAt(hostWindow.fileOpTargetRow)
        if (p.length > 0) hostFileOpsController.revealPhoto(p)
    }
    // #1613: a „Keresés" almenü két új tétele.
    //
    // A `hasOriginalOnDisk` a menü MEGNYITÁSAKOR kérdez rá a lemezre
    // (`fileOpTargetRow` változásakor) — kötésben nem tehetnénk, mert
    // az minden képkockán fájlrendszert kérdezne.
    onLocateOriginalRequested: {
        var p = hostController.photos.filePathAt(hostWindow.fileOpTargetRow)
        if (p.length > 0) hostFileOpsController.revealOriginal(p)
    }
    // az eredeti `IDS_LOCATE_SOURCE_IMAGE`: a kép VALÓDI mappájára ugrik
    // (album-/Emberek-nézetből, ahol a kép nem a saját mappájában látszik)
    onLocateInPicasaRequested: {
        var p = hostController.photos.filePathAt(hostWindow.fileOpTargetRow)
        if (p.length === 0) return
        var mappa = p.substring(0, p.lastIndexOf("/"))
        if (mappa.length === 0) return
        hostToolbar.clearSearch()
        hostWindow.clearSelection()
        hostWindow.unnamedFacesOpen = false
        hostController.selectFolder(mappa)
    }
    // #422 (2. lépcső): az eredeti AlbumPhoto-menü többi parancsa
    onOpenRequested: {
        hostWindow.openPhotoViewer(hostWindow.fileOpTargetRow)
    }
    onRotateRightRequested: hostController.rotateRightMany(hostWindow.selectedRows())
    onRotateLeftRequested: hostController.rotateLeftMany(hostWindow.selectedRows())
    onOpenFileRequested: {
        var target = hostController.photos.filePathAt(hostWindow.fileOpTargetRow)
        if (target.length > 0) hostFileOpsController.openPhoto(target)
    }
    // #5195: a „Társítás ▸" almenü egy alkalmazása megnyitja a képet
    onOpenWithAppRequested: function(appId) {
        var target = hostController.photos.filePathAt(hostWindow.fileOpTargetRow)
        if (target.length > 0) hostFileOpsController.openWithApp(target, appId)
    }
    // #4533: Társítás… — Windowson a héj saját párbeszéde, Linuxon a mi választónk
    onOpenWithRequested: {
        var target = hostController.photos.filePathAt(hostWindow.fileOpTargetRow)
        if (target.length === 0) return
        if (hostFileOpsController.hasNativeOpenWith())
            hostFileOpsController.openWithNative(target)
        else
            hostOpenWithDialog.ensure().openFor(target)
    }
    onCopyFullPathRequested: {
        var full = hostController.photos.filePathAt(hostWindow.fileOpTargetRow)
        if (full.length > 0) hostFileOpsController.copyFullPath(full)
    }
    onPropertiesRequested: hostWindow.valtsFiokLapot("properties")
    // #9 (2. lépés): albumtagság — #305 null-őr
    albums: hostController ? hostController.albums : []
    currentAlbumToken: hostController ? hostController.currentAlbumToken : ""
    currentFolder: hostController ? hostController.currentFolder : ""
    onSplitFolderRequested: hostWindow.splitFolderHere()
    onAddToAlbumRequested: function(token) {
        if (hostController) hostController.addRowsToAlbum(hostWindow.selectedRows(), token)
    }
    // #3539: megerősítéssel — a "Remove from album without
    // confirmation" beállítással elnyomható (`hostRemoveFromAlbumDialog`)
    onRemoveFromAlbumRequested: {
        if (hostController) hostRemoveFromAlbumDialog.ensure().openFor(
            hostWindow.selectedRows(), hostController.currentAlbumToken)
    }
    onNewAlbumRequested: hostFileOpsDialogs.ensure().openNewAlbum(hostWindow.selectedRows())
    // #422 4. lépcső: az Emberek-album kép-szintű parancsai. A tételek
    // csak személy-albumban látszanak (üres `personName` = rejtve).
    personName: hostController ? hostController.currentPersonName : ""
    people: hostController ? hostController.people : []
    onRemoveFromPeopleAlbumRequested: {
        if (hostController) hostRemovePeopleFacesDialog.ensure().openFor(
            hostWindow.selectedRows(), hostController.currentPersonName)
    }
    // #3464: a „Hozzáadás az Emberek albumhoz" almenü egy meglévő
    // személyére kattintva a kijelölt képeken az arc ÁTKERÜL hozzá
    onMoveToPersonRequested: function (name) {
        if (hostController) hostController.movePersonOnRows(
            hostWindow.selectedRows(), hostController.currentPersonName, name)
    }
    onMoveToNewPersonRequested: {
        if (hostController) hostMoveToNewPersonDialog.ensure().openFor(
            hostWindow.selectedRows(), hostController.currentPersonName)
    }
    onSetPeopleAlbumThumbnailRequested: {
        if (hostController && hostController.setPersonThumbnail(
                Number(hostController.photos.idAt(hostWindow.fileOpTargetRow)),
                hostController.currentPersonName))
            hostWindow.peopleFaceRevision++
    }
}
