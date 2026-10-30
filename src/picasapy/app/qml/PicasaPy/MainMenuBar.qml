import PicasaPy

// A főablak felső menüsorának bekötései; az elemeket a PicasaMenuBar kezeli.
PicasaMenuBar {
    id: mainMenuBar

    required property var hostWindow
    required property var hostController
    required property var hostFileOpsController
    required property var hostPassportController
    required property var hostAboutDialog
    required property var hostAddFileDialog
    required property var hostBackupHost
    required property var hostCollectionPasswordDialog
    required property var hostCompactDatabaseDialog
    required property var hostConfigureButtonsDialog
    required property var hostCreateDialogs
    required property var hostDedupDialog
    required property var hostExportDialogs
    required property var hostFaceScanDialog
    required property var hostFileOpsDialogs
    required property var hostFolderManager
    required property var hostFolderPane
    required property var hostGiftCdHost
    required property var hostHelpDialog
    required property var hostImportSourceDialog
    required property var hostMainDialogs
    required property var hostMoveDatabaseDialog
    required property var hostOptionsDialog
    required property var hostPeopleManagerLoader
    required property var hostPhotoViewer
    required property var hostPhotoViewerSettingsDialog
    required property var hostPicasaDataImportDialog
    required property var hostRemoveFromAlbumDialog
    required property var hostRemovePeopleFacesDialog
    required property var hostSaveDialogs
    required property var hostSaveSearchDialog
    required property var hostScreensaverDialog
    required property var hostShowTagAsAlbumDialog
    required property var hostToolbar
    required property var hostTrayBar
    required property var hostWebExportDialog
    required property var hostXmpFacesWriteDialog

    textEntryHasFocus: hostWindow._szovegmezoneVanFokusz
    searchOptionsOpen: hostToolbar.searchOptionsOpen
    //: #2987: a vetítés alatt a menüsáv is eltűnik — enélkül a
    //: contentItem nem kapja meg a teljes ablakot.
    visible: !hostWindow.quickViewerLaunch
             && !hostWindow.slideshowRunning && !hostWindow.timelineOpen
    // #1619: a rács `Ctrl+Delete`-je is ezen a példányon át ágazik el
    //: #671: a Fájl ▸ Kilépés a KÖZÖS úton fut — ott dől el, kérdez-e
    onExitRequested: hostWindow.kilepes()
    // #4329: a felső Fájl ▸ E-Mail ugyanazt a küldési kaput hívja, mint
    // a tálca emailRequested jelzése.
    onEmailRequested: hostWindow.sendSelectionByEmail()
    onSearchOptionsToggleRequested: hostToolbar.toggleSearchOptions()
    onOpenInEditorRequested: hostWindow.openSelectionInDefaultEditor()
    onViewAndEditRequested: hostWindow.nezdEsSzerkeszd()
    // #4622: ugyanaz a kapuzott bezárás, amelyet a nézőből kilépő
    // visszatérési műveletek használnak; az onClosed frissíti a rácsot.
    onReturnToLibraryRequested: hostPhotoViewer.kerBezaras()
    onTimelineRequested: hostWindow.toggleTimeline()
    onUnhideRequested: hostWindow.unhideHiddenSelection()
    onWriteXmpFacesDialogRequested:
        hostXmpFacesWriteDialog.ensure().openFor(hostWindow.photoActionRows())
    onResetFacesRequested: hostWindow.resetFacesForPaths(hostWindow.photoActionPaths())
    // #4335: a fájlban tárolt állapotot a Picture menü nyitásakor
    // frissítjük, mert az index nem jelzi a `textactive=` változását.
    onTextOverlayStatesRefreshRequested: {
        var rows = hostWindow.photoActionRows()
        mainMenuBar.textOverlayShowEnabled = hostController
            ? hostController.hasTextOverlayStateInSelection(rows, false) : false
        mainMenuBar.textOverlayHideEnabled = hostController
            ? hostController.hasTextOverlayStateInSelection(rows, true) : false
    }
    photoActionsEnabled: hostWindow.photoActionRows().length > 0
    photoHasPendingEdits: hostWindow.muveletiCelbanVanMentetlenSzerkesztes
    // #5882: a fotómodell revíziója frissíti ezt a kötést a hidden
    // állapot változásakor; a kijelölés a könyvtár és a néző célpontját
    // egyaránt lefedi.
    hasHiddenPhotoSelection: {
        if (!hostController || !hostController.photos) return false
        var photos = hostController.photos
        var revision = photos.revision
        if (revision < 0) return false
        var rows = hostWindow.photoActionRows()
        for (var i = 0; i < rows.length; ++i) {
            var photo = photos.itemAt(Number(rows[i]))
            if (photo && photo.hidden === true) return true
        }
        return false
    }
    libraryPhotoActionsEnabled: !hostWindow.viewerOpen
                                && hostWindow.selectedIndexes.length > 0
    //: #1768: a Mappakezelő két belépési pontja szürke, amíg a
    //: szerkesztő-előnézet él. Nálunk a szerkesztőpanel a nézőben
    //: lakik, tehát a nyitott néző a megfelelője.
    editorActive: hostWindow.viewerOpen
    // #922: a kollázs/film a TÁLCA tartalmán is dolgozik (#455) —
    // a menüpontnak ezért tálcával, kijelölés nélkül is élnie kell
    createActionsEnabled: !hostWindow.viewerOpen
                          && (hostWindow.selectedIndexes.length > 0
                              || hostWindow.trayHasPictures)
    // #5704: a menüsor csak jelez; a gazda nyitja meg a beépített
    // Rejtett mappák gyűjtemény jelszókezelőjét.
    onHiddenUnlockRequested:
        hostCollectionPasswordDialog.ensure().openForHiddenCollection()
    onHiddenPasswordRequested:
        hostCollectionPasswordDialog.ensure().openForHiddenCollection()
    onRescanRequested: hostController.rescan()
    // #1526: a fájl-vágólap — a kijelölt képek fájljai kerülnek fel,
    // így egy fájlkezelőbe közvetlenül beilleszthetők
    onCopyFilesRequested: hostFileOpsController.copyFilesToClipboard(
        hostWindow.photoActionPaths())
    onCutFilesRequested: hostFileOpsController.cutFilesToClipboard(
        hostWindow.photoActionPaths())
    //: #1526: a Beillesztés célmappája a KIVÁLASZTOTT mappa. Ha a
    //: vágólap közben kiürült (más program írta át), a művelet nem
    //: indul el, és a sávon üzenetet adunk — némán nem tűnik el.
    clipboardHasFiles: hostFileOpsController
                       ? hostFileOpsController.clipboardHasFiles : false
    // #5877: a text= réteg állapotát a .picasa.ini-ből olvassa;
    // a textactive= láthatósága nem változtatja meg a réteg meglétét.
    hasSelectedTextLayer: (hostController
                           && hostController.hasTextLayerInSelection !== undefined)
                          ? hostController.hasTextLayerInSelection(
                                hostWindow.photoActionRows()) : false
    hasTextLayerClipboard: (hostController
                            && hostController.hasTextLayerClipboard !== undefined)
                           ? hostController.hasTextLayerClipboard : false
    onCopyTextRequested: hostWindow.masoldASzovegreteget()
    onPasteTextRequested: hostWindow.illeszdBeASzovegreteget()
    onPasteFilesRequested: hostWindow.beillesztAVagolaprol()
    // #1595: a Mappa menü négy tétele a MEGNYITOTT mappára hat. A
    // párbeszédek és a megerősítések a bal hasábon élnek (ott van a
    // mappa helyi menüje is), ezért onnan hívjuk: egy művelet, egy út.
    onFolderMoveRequested: {
        if (hostController) hostFolderPane.mozgatasMappara(hostController.currentFolder)
    }
    onFolderDeleteRequested: {
        if (hostController) hostFolderPane.torlesLomtarba(hostController.currentFolder)
    }
    onFolderRemoveFromPicasaRequested: {
        if (hostController)
            hostFolderPane.eltavolitasAPicasabol(hostController.currentFolder)
    }
    onFolderLocateRequested: {
        if (hostController && hostController.currentFolder.length > 0)
            hostFileOpsController.revealFolder(hostController.currentFolder)
    }
    onAboutRequested: hostAboutDialog.open()
    onConfigureButtonsRequested: hostConfigureButtonsDialog.open()
    onConfigureScreensaverRequested: hostScreensaverDialog.open()
    onConfigurePhotoViewerRequested: hostPhotoViewerSettingsDialog.open()
    onAddToScreensaverRequested: hostWindow.requestAddToScreensaver()
    onThumbSizePreset: function(size) { hostWindow.thumbSize = size }
    // #4623: a Nézet menü rádiócsoportja ebből számolja a pipát
    thumbSize: hostWindow.thumbSize
    // #426: „Csillagozottak kijelölése" (Szerkesztés menü) — kijelöl,
    // nem szűr (a Mappák panel „Csillagozott" nézete külön: onStarredChosen)
    onSelectStarredRequested: hostWindow.selectStarred()
    onSelectAllRequested: hostWindow.selectAll()
    onClearSelectionRequested: hostWindow.clearSelection()
    // #1686: UGYANAZ a belépő, amit a Ctrl+I és a mappahasáb helyi
    // menüje is hív — nincs másolt logika.
    onInvertSelectionRequested: hostWindow.invertSelection()
    onFolderManagerRequested: hostFolderManager.open()
    onPeopleManagerRequested: {
        if (hostPeopleManagerLoader.active)
            hostPeopleManagerLoader.item.open()
        else
            hostPeopleManagerLoader.active = true
    }
    onDedupRequested: hostDedupDialog.open()
    //: #1398: a MÉRT parancs keresési MÓDOT kapcsol (`dupesearch`), nem
    //: párbeszédet nyit — a kezelő-párbeszédhez a mód sávja vezet.
    onDuplicateSearchRequested: if (hostController) hostController.showDuplicateFiles()
    // #1473: Eszközök → Arcok keresése…
    onFaceScanRequested: hostFaceScanDialog.open()
    //: #1399: a szín-keresés a KERESŐMEZŐBE ír, ahogy az eredeti
    //: (`0x0065b7b0`) — a `color:` előtagot itt tesszük rá, mert a
    //: keresőmotor ezt a tokent érti (`index/search_color.py`, #383).
    onColorSearchRequested: (szin) => hostToolbar.keresesSzoveggel("color:" + szin)
    canSaveSearch: hostController ? hostController.canSaveSearch : false
    //: #1405: az eredeti CSAK 1000 találat FELETT kérdez (mérve,
    //: `0x005d86a0`); alatta csendben létrejön az album. A megerősítés
    //: gombja a mért „Create Album" felirat, nem Igen/Nem.
    //: #1406: a bekérő párbeszéd halasztott (#1720) — a legtöbb
    //: munkamenetben fel sem épül.
    onShowTagAsAlbumRequested: hostShowTagAsAlbumDialog.ensure().openEmpty()
    //: #1775: a KIJELÖLÉS ELSŐ képe lesz a háttér — a parancs egy képre
    //: szól (az eredeti is egyet tesz háttérképnek).
    onWallpaperRequested: {
        var sorok = hostWindow.photoActionRows()
        if (sorok.length > 0)
            hostMainDialogs.wallpaperConfirmDialog.ensure().openFor(
                Number(sorok[0]))
    }
    // #4268: a Picasa poszterpárbeszéde a kijelölés első képéből indul.
    onPosterRequested: {
        var paths = hostWindow.photoActionPaths()
        if (paths.length > 0)
            hostCreateDialogs.ensure().openPoster(String(paths[0]))
    }
    onSaveSearchRequested: {
        if (hostController.searchResultCount > 1000)
            //: `CThumbUI::SaveSearchBig` — az eredeti szövege (#3573)
            hostSaveSearchDialog.ensure().ask("", qsTr(
                "This will create an album with more than 1000 images."
                + "  Do you want to continue?"))
        else
            hostWindow.mentsdAKeresest()
    }
    // #350: Eszközök → Beállítások…
    onOptionsRequested: hostOptionsDialog.open()
    //: #2054
    onHelpRequested: function (topic) { hostHelpDialog.ensure().nyisdMeg(topic) }
    // #4639: a billentyűk listája ugyanebben a helyi súgóban jelenik
    // meg, és a kulcsokat a tényleges QML Shortcut-okból veszi.
    onKeyboardShortcutsRequested: {
        var sugo = hostHelpDialog.ensure()
        sugo.keyboardShortcutTitle = mainMenuBar.keyboardShortcutsTitle
        sugo.keyboardShortcutGroups = hostWindow.keyboardShortcutGroups
        sugo.nyisdMeg("features/billentyuk.md")
    }
    // #351: Exportálás weboldalként
    onWebExportRequested: hostWebExportDialog.open()
    // #5713: ugyanaz a webexport-párbeszéd FTP-közzétételi módban.
    onFtpPublishRequested: hostWebExportDialog.ensure().openFtp()
    // #530: Google Earth-export — a folyamat az ExportDialogs-ban él
    onEarthExportRequested: hostExportDialogs.ensure().openGoogleEarth()
    // #1589: ugyanaz a párbeszéd, de a kiírás után MEGNYITJA a fájlt
    onEarthViewRequested: hostExportDialogs.ensure().openGoogleEarth(true)
    //: #1404: a menüpont is a MEGERŐSÍTÉSEN át töröl
    onClearGeotagRequested:
        hostMainDialogs.clearGeotagDialog.ensure().openFor(hostWindow.photoActionRows())
    // #5396: egy és több kijelölt képnél is a mért `rename.fen`-dialógus
    // nyílik; a forrásfájl kiterjesztését és előnézetét az kezeli.
    onRenameRequested: hostFileOpsDialogs.ensure().openRenameMany(hostWindow.photoActionRows())
    // #368: adatbázis-áthelyezés a Kísérleti menüből
    onMoveDatabaseRequested: hostMoveDatabaseDialog.open()
    //: #3504: a kiadás-panel mentés-üzemmódja a könyvtár alján — a
    //: korábbi külön ablak (`BackupDialog`) helyett, a `hostGiftCdHost`
    //: mintájára.
    onBackupRequested: hostBackupHost.nyisd()
    // #449: adatbázis-tömörítés (`compacting.fen`)
    onCompactDatabaseRequested: hostCompactDatabaseDialog.open()
    //: #1401: az Útlevélkép — a KIJELÖLÉS ELSŐ képére szól (az eredeti
    //: is egyre), a `wallpaperRequested` mintájára.
    onPassportPhotoRequested: {
        var sorok = hostWindow.photoActionRows()
        if (sorok.length > 0
                && typeof hostPassportController !== "undefined" && hostPassportController)
            hostPassportController.preparePassportPhoto(Number(sorok[0]))
    }
    // #3132: Import a Picasából — a db3 átvétele (SAJÁT funkció)
    onPicasaDataImportRequested: hostPicasaDataImportDialog.open()
    // #936: a Létrehozás menü jelzésének NEM VOLT kezelője — a
    // menüpont elsütötte a jelzést, és az a semmibe ment. Az
    // egyetlen kezelő a képtálca sávján ült (`hostTrayBar`), ezért
    // onnan indítva működött, a menüből nem.
    // #985: a menüpont mostantól a KOLLÁZS LAPOT nyitja meg, nem a
    // korábbi modális párbeszédet (spec 3.2: „modálist nyit → a lapot
    // nyitja meg"). A `CreateDialogs` kollázs-ága egyelőre a helyén
    // marad — a leszerelése külön jegy.
    onCollageRequested: hostWindow.openCollageTab()
    onMovieRequested: hostCreateDialogs.ensure().openMovie()
    onFaceMovieRequested: hostCreateDialogs.ensure().openFaceMovie()
    onPeopleAlbumsMovieRequested: hostWindow.openPeopleAlbumsMovie()
    //: #3503: a kiadás-panel Ajándék-CD üzemmódja a könyvtár alján
    onGiftCdRequested: hostGiftCdHost.nyisd()
    onExportRequested: hostExportDialogs.ensure().openForSelection(
        hostWindow.viewerOpen ? hostWindow.photoActionRows() : undefined)
    // #1616: Fájl ▸ Új album… / Ctrl+N — UGYANAZT az `openNewAlbum`
    // belépőt hívja, amit a rács helyi menüjének „Új album…" tétele is
    // (a `PhotoContextMenu.onNewAlbumRequested` kötése lentebb, a
    // helyi menü példányán)
    onNewAlbumRequested: hostFileOpsDialogs.ensure().openNewAlbum(hostWindow.photoActionRows())
    // #1615: Fájl ▸ Importálás forrása… / Ctrl+M — UGYANAZ a példány,
    // amit az eszköztár „Import" gombja nyit (ld. `onImportRequested`)
    onImportSourceRequested: hostImportSourceDialog.open()
    // #1633: Fájl ▸ Fájl felvétele a Picasába… / Ctrl+O
    onAddFileRequested: hostAddFileDialog.open()
    // #1614: Fájl ▸ Áthelyezés új mappába… — a `moveToNewFolderDialog`
    // csak a NEVET kéri, a kijelölés útvonalait a hívás pillanatában
    // gyűjtjük (ugyanaz a minta, mint a `Move…`/`Törlés…` tételeknél).
    onMoveToNewFolderRequested:
        hostFileOpsDialogs.ensure().openMoveToNewFolder(hostWindow.photoActionPaths())
    // #1472: Fájl ▸ Nyomtatás… / Ctrl+P — a nyomtatás-párbeszéd
    onPrintRequested: hostWindow.openPrint()
    // #1590: Mappa ▸ Bélyegképek nyomtatása… (Ctrl+Shift+P)
    onPrintContactSheetRequested: hostWindow.openContactSheetPrint()
    onLocateRequested: {
        var p = hostController.photos.filePathAt(hostWindow.photoActionIndex())
        if (p.length > 0) hostFileOpsController.revealPhoto(p)
    }
    onDeleteRequested: hostFileOpsDialogs.ensure().openDelete(
        hostWindow.viewerOpen ? hostWindow.photoActionPaths()
                          : hostWindow.selectedPaths())
    // #1608: a `Delete` NÉZETFÜGGŐ — albumban/Emberek-albumban nem
    // lemezről töröl, csak kiveszi onnan (a helyi menü már meglévő
    // útjaira vezet, ld. lentebb a PhotoContextMenu ugyanezen kezelőit)
    currentAlbumToken: hostController ? hostController.currentAlbumToken : ""
    currentPersonName: hostController ? hostController.currentPersonName : ""
    // #3539: megerősítéssel — a "Remove from album without
    // confirmation" beállítással elnyomható (`hostRemoveFromAlbumDialog`)
    onRemoveFromAlbumRequested: {
        if (hostController) hostRemoveFromAlbumDialog.ensure().openFor(
            hostWindow.photoActionRows(), hostController.currentAlbumToken)
    }
    onRemoveFromPeopleAlbumRequested: {
        if (hostController) hostRemovePeopleFacesDialog.ensure().openFor(
            hostWindow.photoActionRows(), hostController.currentPersonName)
    }
    // #444: a nem-destruktív mentés három fokozata — a megerősítések és
    // a nem renderelhető láncelem figyelmeztetése a SaveDialogs-ban.
    // #5206: a befejezett mentés/visszaállítás léptetett számlálón át
    // újraértékeli a kötést (a `hasSavedBackup` lemezt néz, a QML nem látja)
    hasSavedBackup: hostController
        ? (hostController.savedBackupRevision,
           hostController.hasSavedBackup(hostWindow.photoActionRows())) : false
    // #4332: siker esetén a dátummódosítás az EXIF DateTimeOriginal
    // mezőt írja; ha az EXIF-írás nem lehetséges, indexfelülírásra esik vissza.
    onAdjustTimestampRequested:
        hostCreateDialogs.ensure().openTimestamp(hostWindow.photoActionRows())
    onSaveRequested: hostSaveDialogs.ensure().openSave(hostWindow.photoActionRows())
    onRevertRequested: hostSaveDialogs.ensure().openRevert(hostWindow.photoActionRows())
    // #1527: a mentés-család két új tagja
    onSaveAsRequested: hostSaveDialogs.ensure().openSaveAs(hostWindow.photoActionIndex())
    onSaveCopyRequested: hostSaveDialogs.ensure().openSaveCopy(hostWindow.photoActionRows())
    onSlideshowRequested: hostWindow.startSlideshow(-1)
    // #3460/#4630: a Mappa/Album menü a megnyitott hely leírását szerkeszti
    currentFolder: hostController ? hostController.currentFolder : ""
    onEditFolderDescriptionRequested: {
        if (hostController) {
            if (hostController.currentAlbumToken !== "")
                hostFolderPane.openAlbumDescription(hostController.currentAlbumToken)
            else
                hostFolderPane.openFolderDescription(hostController.currentFolder)
        }
    }
    tagsPanelOpen: hostWindow.tagsPanelOpen
    onTagsPanelRequested: hostWindow.valtsFiokLapot("tags")
    peoplePanelOpen: hostWindow.peoplePanelOpen
    onPeoplePanelRequested: hostWindow.valtsFiokLapot("people")
    placesPanelOpen: hostWindow.placesPanelOpen
    onPlacesPanelRequested: hostWindow.valtsFiokLapot("places")
    onHideToggleRequested: hostWindow.hideSelection()
    propertiesPanelOpen: hostWindow.propertiesPanelOpen
    onPropertiesPanelRequested: hostWindow.valtsFiokLapot("properties")
    // #426: „Az összes effektus másolása/beillesztése" — a menü
    // célképére, a rácsban pedig a kijelölésre hat
    // (hostWindow.photoActionRows() a
    // meglévő mintát követi, ld. toggleHiddenSelection). A
    // `photo_ops_controller.PhotoOpsMixin`-t hívja, NEM a #152-es
    // `effects_controller`-t (az a crop64-et is átvinné).
    // #305: null-őr — ld. fenti Connections
    hasAllEffectsClipboard: hostController ? hostController.hasAllEffectsClipboard : false
    onCopyAllEffectsRequested: hostController.copyAllEffects(hostWindow.photoActionRows())
    onPasteAllEffectsRequested: hostController.pasteAllEffects(hostWindow.photoActionRows())
    // #1475: a két kötegelt visszavonás — a Szerkesztés menü élén álló
    // tételek. Kijelölés-független: a köteg a SAJÁT, művelet idején
    // rögzített képlistáját állítja vissza.
    canUndoPasteAllEffects: hostController ? hostController.canUndoPasteAllEffects : false
    canUndoBatchEdit: hostController ? hostController.canUndoBatchEdit : false
    onUndoPasteAllEffectsRequested: hostController.undoPasteAllEffects()
    onUndoBatchEditRequested: hostController.undoBatchEdit()
    // #425: Kép ▸ Csoportos szerkesztés — a `batch_effect_controller.
    // BatchEffectMixin`-t hívja, ugyanazon a rács-sorindex mintán
    // a forgatás a MEGLÉVŐ (szinkron, gyors) rotateRightMany/
    // rotateLeftMany úton fut, nem az applyEffectMany háttérszálán —
    // a `filters=`-t bővítő 7 effekttől eltérően nem igényel ini-
    // láncbővítést, csak a rotate= kulcs cseréjét (ld. PhotoOpsMixin).
    // A köteg visszavonása a Szerkesztés menü „Csoportos szerkesztés
    // visszavonása" tételén megy (#1475) — a forgatás NEM kerül a
    // kötegelt undo-verembe, mert a rotate= külön kulcs.
    onBatchApplyEffectRequested: (name) => {
        if (hostWindow.viewerOpen) {
            if (hostPhotoViewer.selectMenuEffect(name)) return
            var row = hostWindow.photoActionIndex()
            if (row < 0) return
            if (name === "rotate_cw") hostController.rotateRight(row)
            else if (name === "rotate_ccw") hostController.rotateLeft(row)
            else hostController.applyEffectMany([row], name)
        } else if (name === "rotate_cw") {
            hostController.rotateRightMany(hostWindow.selectedRows())
        } else if (name === "rotate_ccw") {
            hostController.rotateLeftMany(hostWindow.selectedRows())
        } else {
            hostController.applyEffectMany(hostWindow.selectedRows(), name)
        }
    }
    // #4335: mindkét parancs ugyanazt a kötegelt INI-utat használja,
    // a különbség a kért végállapot.
    onTextOverlayVisibilityRequested: (visible) => {
        hostController.setTextOverlayVisibleMany(
            hostWindow.photoActionRows(), visible)
    }
    // #465 3. pont: „Undo All Edits" — megerősítéssel, a kijelölt
    // kép(ek) TELJES szerkesztési lánca törlődik (`clearAllEffectsMany`,
    // ugyanaz a kötegelt undo-verem mint a `applyEffectMany`-nál).
    onUndoAllEditsRequested: hostMainDialogs.undoAllEditsDialog.ensure().openForLibrary(
        hostWindow.photoActionRows())
    // #3555: nyelvváltás — a menütétel csak jelez (a `ConfirmDialog` nem
    // fér el a MenuBar gyermekeként), a kérdés és a `setLanguage`-hívás
    // itt fut ki.
    onLanguageConfirmRequested: function (code) {
        hostMainDialogs.languageConfirmDialog.ensure().askFor(code)
    }
}
