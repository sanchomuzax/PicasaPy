import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// A FolderPane helyi menüi és párbeszédablakai; a műveletek gazdája a folderPane.
Item {
    id: menus
    width: 0
    height: 0
    property var folderPane: null
    property var controller: null
    property var folderHierarchyController: null

    property alias albumContextMenu: albumContextMenu
    property alias deleteAlbumConfirm: deleteAlbumConfirm
    property alias peopleAlbumContextMenu: peopleAlbumContextMenu
    property alias peopleAlbumDeleteConfirmation: peopleAlbumDeleteConfirmation
    property alias folderListContextMenu: folderListContextMenu
    property alias moveFolderDialog: moveFolderDialog
    property alias folderContextMenu: folderContextMenu
    property alias deleteFolderConfirm: deleteFolderConfirm
    property alias removeFolderConfirm: removeFolderConfirm
    property alias closeCollectionConfirm: closeCollectionConfirm
    property alias folderPropertiesDialog: folderPropertiesDialog
    property alias newCollectionDialog: newCollectionDialog
    property alias collectionContextMenu: collectionContextMenu
    property alias removeCollectionConfirm: removeCollectionConfirm

    // #1637: a menü jelzését itt fogadjuk, ahol a menüpéldány is él.
    // A controller névazonos, explicit propertyként érkezik a hasábból.
    Connections {
        target: folderContextMenu
        function onHideFolderRequested(ut) {
            if (controller && ut.length > 0)
                controller.toggleFolderHidden(ut)
        }
    }

    AlbumContextMenu {
        id: albumContextMenu
        onAddNameTagsRequested: function(token) {
            if (typeof faceScanController !== "undefined" && faceScanController)
                faceScanController.scanAlbum(token)
        }
        onSelectAllRequested:
            if (folderPane.appWindow && folderPane.appWindow.selectAll) folderPane.appWindow.selectAll()
        onClearSelectionRequested:
            if (folderPane.appWindow && folderPane.appWindow.clearSelection)
                folderPane.appWindow.clearSelection()
        onInvertSelectionRequested:
            if (folderPane.appWindow && folderPane.appWindow.invertSelection)
                folderPane.appWindow.invertSelection()
        // az album tartalma a jelenlegi mappákból áll — a frissítés a
        // megnyitott mappa újraszinkronja (a mappa-menü mintája)
        onRefreshThumbnailsRequested:
            if (controller) controller.resyncFolder(controller.currentFolder)
        onExportAsHtmlRequested:
            if (folderPane.appWindow && folderPane.appWindow.openWebExport)
                folderPane.appWindow.openWebExport()
        //: #3173: a helyi menü ugyanarra az albumtulajdonság-útvonalra megy.
        onEditDescriptionRequested: folderPane.openAlbumDescription(
            albumContextMenu.albumToken, albumContextMenu.albumName)
        onDeleteAlbumRequested: folderPane._askDeleteAlbum(
            albumContextMenu.albumToken, albumContextMenu.albumName)
        //: #4599: „Sort Album By" — az album tárolt sorrendjének átrendezése
        onSortAlbumRequested: function(mode) {
            if (controller)
                controller.sortAlbum(albumContextMenu.albumToken, mode)
        }
    }

    ConfirmDialog {
        id: deleteAlbumConfirm
        namePrefix: "deleteAlbum"
        title: qsTr("Delete Album")
        yesText: qsTr("Delete Album")
        cancelVisible: false
        rememberVisible: false
        focusNoOnOpen: true
        property string pendingToken: ""
        onConfirmed: {
            if (controller && pendingToken)
                controller.deleteAlbum(pendingToken)
            pendingToken = ""
        }
        onDenied: pendingToken = ""
        onCanceled: pendingToken = ""
    }

    PeopleAlbumContextMenu {
        id: peopleAlbumContextMenu
        onDeleteRequested: function(name) {
            peopleAlbumDeleteConfirmation.personName = name
            peopleAlbumDeleteConfirmation.personId =
                peopleAlbumContextMenu.personId
            peopleAlbumDeleteConfirmation.open()
        }
        onEditRequested: function(name) {
            if (folderPane.appWindow && folderPane.appWindow.openPeopleManagerForPerson)
                folderPane.appWindow.openPeopleManagerForPerson(
                    name, peopleAlbumContextMenu.personId)
        }
        onSelectAllRequested:
            if (folderPane.appWindow && folderPane.appWindow.selectAll) folderPane.appWindow.selectAll()
        onClearSelectionRequested:
            if (folderPane.appWindow && folderPane.appWindow.clearSelection)
                folderPane.appWindow.clearSelection()
        onInvertSelectionRequested:
            if (folderPane.appWindow && folderPane.appWindow.invertSelection)
                folderPane.appWindow.invertSelection()
        // Ugyanaz a frissítési út, mint az album-menüben: az aktív mappa
        // újraszinkronja újratölti a látható rácsot.
        onRefreshThumbnailsRequested:
            if (controller) controller.resyncFolder(controller.currentFolder)
    }

    Dialog {
        id: peopleAlbumDeleteConfirmation
        objectName: "peopleAlbumDeleteConfirmation"
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        focus: true
        title: qsTr("Remove People")
        property string personName: ""
        property string personId: ""
        // #1599/#1748: rögzített szélesség, különben a tördelő felirat és a
        // Dialog egymás szélességéből számolna (kötési hurok)
        implicitWidth: 380 + leftPadding + rightPadding

        contentItem: ColumnLayout {
            focus: true
            Keys.onReturnPressed: peopleAlbumDeleteConfirmation.reject()
            Keys.onEnterPressed: peopleAlbumDeleteConfirmation.reject()
            width: 380
            spacing: 8

            Label {
                objectName: "peopleAlbumDeleteMessage"
                Layout.fillWidth: true
                text: qsTr("Are you sure you want to delete the people album \"%1\"?")
                    .arg(peopleAlbumDeleteConfirmation.personName)
                wrapMode: Text.WordWrap
            }

            CheckBox {
                objectName: "peopleAlbumDeleteOnlineFacesCheckBox"
                Layout.fillWidth: true
                text: qsTr("Delete tagged faces from synced Picasa Web albums, too")
                checked: false
            }
        }

        footer: RowLayout {
            spacing: 8

            Item { Layout.fillWidth: true }

            Button {
                objectName: "peopleAlbumDeleteConfirmButton"
                text: qsTr("Delete Album")
                Keys.priority: Keys.BeforeItem
                Keys.onReturnPressed: peopleAlbumDeleteConfirmation.reject()
                Keys.onEnterPressed: peopleAlbumDeleteConfirmation.reject()
                onClicked: peopleAlbumDeleteConfirmation.accept()
            }
            Button {
                id: peopleAlbumDeleteCancelButton
                objectName: "peopleAlbumDeleteCancelButton"
                text: qsTr("Cancel")
                focus: true
                Keys.priority: Keys.BeforeItem
                Keys.onReturnPressed: peopleAlbumDeleteConfirmation.reject()
                Keys.onEnterPressed: peopleAlbumDeleteConfirmation.reject()
                onClicked: peopleAlbumDeleteConfirmation.reject()
            }
        }

        onOpened: peopleAlbumDeleteCancelButton.forceActiveFocus()

        onAccepted: {
            if (controller)
                controller.savePeopleManagerChanges([
                    {
                        action: "remove_album",
                        oldName: peopleAlbumDeleteConfirmation.personName,
                        person_id: peopleAlbumDeleteConfirmation.personId
                    }
                ])
        }
    }

    FolderListContextMenu {
        id: folderListContextMenu
        // #1454: az „Egyszerűsített fanézet" ugyanazt a kapcsolót billenti,
        // mint a menüsáv `Nézet ▸ Mappanézet` harmadik tétele
        simplifiedTree:
            folderHierarchyController ? folderHierarchyController.simplified : false
        albumThumbs: folderPane.albumThumbs
        viewRoot: (folderHierarchyController
                && folderHierarchyController.viewRoot !== undefined)
            ? folderHierarchyController.viewRoot : ""
        // #1767: a Személyek lista rendezése — a `!== undefined` a
        // #1572-őr mintája (a próbák stub-vezérlőjén hiányozhat)
        peopleSort: (controller && controller.peopleSort !== undefined)
            ? controller.peopleSort : "name"
        onPeopleSortRequested: function(mode) {
            if (controller && controller.setPeopleSort !== undefined)
                controller.setPeopleSort(mode)
        }
        onSortModeRequested: function(mode) {
            if (controller) controller.setPaneSort(mode)
        }
        onSortReverseRequested: if (controller) controller.togglePaneSortReverse()
        onSimplifiedTreeRequested:
            if (folderHierarchyController) folderHierarchyController.toggleSimplified()
        onAlbumThumbnailsRequested:
            if (folderHierarchyController)
                folderHierarchyController.toggleAlbumThumbs()
        onViewRootRequested: function(token) {
            if (folderHierarchyController)
                folderHierarchyController.setViewRoot(token)
        }
    }

    // #457: melyik mappát mozgatjuk épp (a dialógus elfogadásakor kell)

    FolderDialog {
        id: moveFolderDialog
        objectName: "moveFolderDialog"
        title: qsTr("Move Folder")
        onAccepted: {
            if (folderPane._movingFolder.length > 0
                    && typeof fileOpsController !== "undefined"
                    && fileOpsController)
                fileOpsController.moveFolder(
                    folderPane._movingFolder, moveFolderDialog.selectedFolder)
            folderPane._movingFolder = ""
        }
    }

    FolderContextMenu {
        id: folderContextMenu
        onAddNameTagsRequested: function(path) {
            if (typeof faceScanController !== "undefined" && faceScanController)
                faceScanController.scanFolder(path)
        }
        // #457: „Mappa áthelyezése…” — a célmappát a rendszer
        // mappaválasztójával kérjük be, a mozgatás a kísérőfájlokkal
        // együtt megy (a `.picasa.ini` nálunk az igazságforrás)
        onMoveFolderRequested: {
            folderPane._movingFolder = folderContextMenu.folderPath
            moveFolderDialog.open()
        }

        // #1638: „Mappa törlése…" — a mappa a LOMTÁRBA kerül a
        // tartalmával együtt. A megerősítés az eredeti szövegével megy, és
        // a mappa NEVÉT tartalmazza, hogy ne lehessen véletlen mást
        // törölni.
        onDeleteFolderRequested: {
            var ut = folderContextMenu.folderPath
            if (ut === "") return
            deleteFolderConfirm.pendingPath = ut
            deleteFolderConfirm.message = qsTr(
                "Are you sure you want to move the folder \"%1\" and its "
                + "contents to the Recycle Bin?").arg(
                    ut.substring(ut.lastIndexOf("/") + 1))
            deleteFolderConfirm.open()
        }

        onMoveToCollectionRequested: function(collectionName) {
            if (controller) controller.moveFolderToCollection(
                folderContextMenu.folderPath, collectionName)
        }
        onNewCollectionRequested: {
            // #422: a létrehozás-ág — a _renamingCollection üresen marad,
            // az initialName is üres (a korábbi átnevezésből esetleg
            // bennragadt értéket felülírjuk)
            folderPane._renamingCollection = ""
            newCollectionDialog.initialName = ""
            newCollectionDialog.open()
        }

        // #422: az eredeti `album.fen` dialógusa — a mappa DÁTUMA is itt
        // lakik, ezért szűnt meg a külön „Mappa dátumának beállítása…"
        // menütétel
        onEditDescriptionRequested: folderPane.openFolderDescription(folderContextMenu.folderPath)

        onSelectAllRequested:
            if (folderPane.appWindow && folderPane.appWindow.selectAll) folderPane.appWindow.selectAll()
        onClearSelectionRequested:
            if (folderPane.appWindow && folderPane.appWindow.clearSelection)
                folderPane.appWindow.clearSelection()
        onInvertSelectionRequested:
            if (folderPane.appWindow && folderPane.appWindow.invertSelection)
                folderPane.appWindow.invertSelection()

        onRefreshThumbnailsRequested:
            if (controller) controller.resyncFolder(folderContextMenu.folderPath)
        // #4890: egyszer átrendezi a célmappát, és a kézi sorrendjét menti.
        onSortModeRequested: function(mode) {
            if (controller)
                controller.sortFolderBy(folderContextMenu.folderPath, mode)
        }
        onSortReverseRequested:
            if (controller)
                controller.sortFolderBy(folderContextMenu.folderPath, "reverse")

        onLocateRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController)
                fileOpsController.revealFolder(folderContextMenu.folderPath)
        }
        onRemoveFromPicasaRequested: folderPane._askRemoveFolder(
            folderContextMenu.folderPath)
        onExportAsHtmlRequested:
            if (folderPane.appWindow && folderPane.appWindow.openWebExport)
                folderPane.appWindow.openWebExport()
    }

    // #1249: az eredeti megerősítés — a MAPPA NEVÉVEL, és kimondja az
    // almappákat („Do you want to remove the folder %s and its
    // subfolders?", `CThumbUI::ManageAlbum`). A név a path utolsó tagja.
    // „Eltávolítás a Picasából…" — a fájlok a lemezen maradnak, csak a
    // könyvtárból kerül ki (#422 → #1249)
    // #1638: a mappa lomtárba tétele — a megerősítés az eredeti szövegével
    ConfirmDialog {
        id: deleteFolderConfirm
        namePrefix: "deleteFolderConfirm"
        property string pendingPath: ""
        title: qsTr("Delete Folder")
        yesText: qsTr("Delete Folder")
        onConfirmed: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                    && deleteFolderConfirm.pendingPath !== "")
                fileOpsController.deleteFolder(deleteFolderConfirm.pendingPath)
            deleteFolderConfirm.pendingPath = ""
        }
        onDenied: deleteFolderConfirm.pendingPath = ""
        onCanceled: deleteFolderConfirm.pendingPath = ""
    }

    ConfirmDialog {
        id: removeFolderConfirm
        namePrefix: "removeFolderConfirm"
        //: CThumbUI::ManageAlbumConfirm; job-348: a cím az eredetiben Confirm.
        title: qsTr("Confirm")
        // az eredeti igen-gombja: `CThumbUI:ManageAlbumYesButton`
        yesText: qsTr("Remove Folder")
        //: job-348: Remove Folder / Cancel; Enter az elfogadást választja.
        noVisible: false
        focusYesOnOpen: true
        onConfirmed: {
            // #1249: a removeWatchedFolder CSAK pontos figyelt-gyökérre
            // hatott — almappán némán semmit nem csinált (a jelentett
            // tünet). A removeFolder a széles változat: gyökérre a teljes
            // meglévő út, almappára index-takarítás + sírkő.
            if (controller && folderContextMenu.folderPath !== "")
                controller.removeFolder(folderContextMenu.folderPath)
        }
    }

    // #461: az utolsó gyűjtemény bezárásának figyelmeztetése — a címe és a
    // gombfelirata is az eredetiből (IDS_CLOSING_LAST_COLLECTION_TITLE,
    // CloseCollection::YesButon).
    ConfirmDialog {
        id: closeCollectionConfirm
        namePrefix: "closeCollectionConfirm"
        property string pendingName: ""
        title: qsTr("Close Last Collection?")
        yesText: qsTr("Close Collection")
        onConfirmed: {
            if (controller && closeCollectionConfirm.pendingName !== "")
                controller.setCollectionClosed(closeCollectionConfirm.pendingName, true)
            closeCollectionConfirm.pendingName = ""
        }
        onDenied: closeCollectionConfirm.pendingName = ""
        onCanceled: closeCollectionConfirm.pendingName = ""
    }

    FolderPropertiesDialog {
        id: folderPropertiesDialog
        renameFolderHandler: function(path, name) {
            if (typeof controller === "undefined" || !controller
                    || typeof controller.renameFolder !== "function")
                return null
            return controller.renameFolder(path, name)
        }
        onFolderPropertiesAccepted: function(path, isoDate, description) {
            if (!controller) return
            controller.setFolderDescriptionOf(path, description)
            // üres dátum = „automatikus dátum": a felülírás törlése
            if (isoDate.length > 0) controller.setFolderDate(path, isoDate)
            else controller.clearFolderDate(path)
        }
        onFolderMusicAccepted: function(path, useMusic, musicFile) {
            if (controller && controller.setFolderMusic)
                controller.setFolderMusic(path, useMusic, musicFile)
        }
        onSplitFolderAccepted: function(paths, name, isoDate, location,
                                        description, useMusic, musicFile) {
            if (typeof fileOpsController !== "undefined" && fileOpsController)
                fileOpsController.splitFolderHere(
                    paths, name, isoDate, location, description,
                    useMusic, musicFile)
        }
        //: #3173: album módban az ini-írás a `photo_ops_controller`-en megy,
        //: MINDEN olyan mappába, ahol az albumnak van tagja
        onAlbumPropertiesAccepted: function(token, name, isoDate, location, description) {
            if (!controller || !controller.editAlbumProperties) return
            controller.editAlbumProperties(
                token, name, isoDate, location, description)
            folderPane.refreshCustomCollections()
        }
        onAlbumMusicAccepted: function(token, useMusic, musicFile) {
            if (controller && controller.editAlbumMusic)
                controller.editAlbumMusic(token, useMusic, musicFile)
        }
    }

    NewCollectionDialog {
        id: newCollectionDialog
        onCreated: function(name) {
            if (!controller) return
            // #422: ugyanaz a dialógus szolgálja a létrehozást (a
            // FolderContextMenu "Új gyűjtemény…" ága) ÉS az átnevezést (a
            // CollectionContextMenu "Gyűjtemény átnevezése…" ága) — a két
            // használatot a folderPane._renamingCollection különbözteti meg.
            if (folderPane._renamingCollection !== "") {
                controller.renameCollection(folderPane._renamingCollection, name)
                folderPane._renamingCollection = ""
            } else {
                controller.createCollection(name)
                // Picasa-mintára: a "Move to Collection ▸ New Collection…"-ból
                // indított létrehozás a jobbklikkelt mappát rögtön bele is
                // sorolja az új gyűjteménybe.
                if (folderContextMenu.folderPath !== "")
                    controller.moveFolderToCollection(
                        folderContextMenu.folderPath, name)
            }
            folderPane.refreshCustomCollections()
        }
    }

    // #422: a gyűjtemény jobbklikk-menüje (átnevezés/eltávolítás/jelszó) —
    // a Collection menüosztály, a #476-ban készült CollectionHeader
    // fejlécre kötve (folderPane.openCollectionContextMenu).
    CollectionContextMenu {
        id: collectionContextMenu
        onPasswordRequested: {
            if (collectionContextMenu.hiddenCollection)
                folderPane.hiddenPasswordRequested()
            else
                folderPane.collectionPasswordRequested(
                    collectionContextMenu.collectionName)
        }
        onRenameRequested: {
            folderPane._renamingCollection = collectionContextMenu.collectionName
            newCollectionDialog.initialName = collectionContextMenu.collectionName
            newCollectionDialog.open()
        }
        // #461: az eredeti Picasa szövege kimondja, hogy a mappák NEM
        // vesznek el — az alapértelmezett gyűjteménybe kerülnek. Ez a
        // megnyugtató mondat a lényeg, ezért szó szerint átvesszük.
        onRemoveRequested: removeCollectionConfirm.ask(
            "removeCollection",
            qsTr("Are you sure you want to remove the collection \u201c%1\u201d? "
                 + "All folders in it will be moved to the collection "
                 + "\u201c%2\u201d.")
                .replace("%1", collectionContextMenu.collectionName)
                .replace("%2", qsTr("Folders on Disk")))
    }

    // „Gyűjtemény eltávolítása" megerősítése (#422) — egyedi namePrefix,
    // hogy ne ütközzön a removeFolderConfirm-mal
    ConfirmDialog {
        id: removeCollectionConfirm
        namePrefix: "removeCollectionConfirm"
        onConfirmed: {
            if (controller && collectionContextMenu.collectionName !== "")
                controller.deleteCollection(collectionContextMenu.collectionName)
            folderPane.refreshCustomCollections()
        }
    }
}
