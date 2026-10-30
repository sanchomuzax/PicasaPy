pragma ComponentBehavior: Bound
import QtQuick
import PicasaPy

// A lebegő folyamatjelzők, műveleti sávok és a főablak fölötti rétegek.
Item {
    id: layers
    objectName: "mainWindowPeripheralLayers"
    anchors.fill: parent
    required property var hostWindow
    required property var hostController
    required property var hostRefs

    property alias exportDialogStack: mainWindowDialogStack
    property alias exportErrorBanner: mainErrorBanner
    property alias exportGiftCdHost: giftCdHost
    property alias exportBackupHost: backupHost
    property alias exportPhotoContextMenu: photoContextMenu
    property alias exportErrorBannerText: mainErrorBanner.messageText
    property alias exportActivityCancelConfirm: mainWindowDialogStack.exportActivityCancelConfirm
    property alias exportXmpFacesWriteDialog: mainWindowDialogStack.exportXmpFacesWriteDialog
    property alias exportBrokenPhotoDialog: mainWindowDialogStack.exportBrokenPhotoDialog
    property alias exportBrokenPhotoBatchTimer: mainWindowDialogStack.exportBrokenPhotoBatchTimer
    property alias exportRemoveFromAlbumDialog: mainWindowDialogStack.exportRemoveFromAlbumDialog
    property alias exportRemovePeopleFacesDialog: mainWindowDialogStack.exportRemovePeopleFacesDialog
    property alias exportMoveToNewPersonDialog: mainWindowDialogStack.exportMoveToNewPersonDialog
    property alias exportInitialScanDialog: mainWindowDialogStack.exportInitialScanDialog
    property alias exportCollectionPasswordDialog: mainWindowDialogStack.exportCollectionPasswordDialog
    property alias exportHiddenPasswordOfferDialog: mainWindowDialogStack.exportHiddenPasswordOfferDialog
    property alias exportCollageDraftDialog: mainWindowDialogStack.exportCollageDraftDialog
    property alias exportSaveDialogs: mainWindowDialogStack.exportSaveDialogs
    property alias exportFileOpsDialogs: mainWindowDialogStack.exportFileOpsDialogs
    property alias exportExportDialogs: mainWindowDialogStack.exportExportDialogs
    property alias exportCreateDialogs: mainWindowDialogStack.exportCreateDialogs
    property alias exportHelpDialog: mainWindowDialogStack.exportHelpDialog
    property alias exportConfigureButtonsDialog: mainWindowDialogStack.exportConfigureButtonsDialog
    property alias exportAboutDialog: mainWindowDialogStack.exportAboutDialog
    property alias exportOptionsDialog: mainWindowDialogStack.exportOptionsDialog
    property alias exportWebExportDialog: mainWindowDialogStack.exportWebExportDialog
    property alias exportPrintDialog: mainWindowDialogStack.exportPrintDialog
    property alias exportMoveDatabaseDialog: mainWindowDialogStack.exportMoveDatabaseDialog
    property alias exportCompactDatabaseDialog: mainWindowDialogStack.exportCompactDatabaseDialog
    property alias exportPicasaDataImportDialog: mainWindowDialogStack.exportPicasaDataImportDialog

    // A lebegő háttérmunka- és folyamatjelzők önálló komponensben (#6136).
    MainActivityPanels {
        id: activityPanels
        hostController: layers.hostController
        hostActivityCancelConfirm: mainWindowDialogStack.exportActivityCancelConfirm
    }
    MainWindowDialogStack {
        id: mainWindowDialogStack
        anchors.fill: parent
        hostWindow: layers.hostWindow
        hostPhotoViewer: hostRefs.photoViewer
        hostDocumentTabStrip: hostRefs.documentTabStrip
        hostUnnamedFaceRefreshTimer: hostRefs.unnamedFaceRefreshTimer
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

    MainErrorBanner {
        id: mainErrorBanner
        hostController: layers.hostController
        hostTestLogDialog: hostRefs.tesztuzemNaploDialog
        hostBrokenPhotoDialog: hostRefs.brokenPhotoDialog
        hostBrokenPhotoBatchTimer: hostRefs.brokenPhotoBatchTimer
    }





    //: #3503: „Létrehozás ▸ Ajándék CD készítése…" — a kiadás-panel
    //: Ajándék-CD üzemmódja a könyvtár ALJÁN (az eredetiben is ott ül).
    //: Csak a könyvtár lapján látszik, ugyanazzal a feltétellel, mint a
    //: könyvtár maga.
    GiftCdHost {
        id: giftCdHost
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        appController: hostController
        fileOps: typeof fileOpsController !== "undefined" ? fileOpsController : null
        visible: nyitva && !hostWindow.viewerOpen && !hostWindow.timelineOpen
                 && hostWindow.libraryFrameVisible
        //: #3504: a kiadás-panel EGYSZERRE egy üzemmódban látszik — az
        //: Ajándék-CD nyitása becsukja a mentést (az eredetiben is egy sáv
        //: vált módot, `biztonsagi-mentes.md` 10.)
        onNyitvaChanged: if (nyitva) backupHost.nyitva = false
    }

    //: #3504: „Eszközök ▸ Képek biztonsági mentése…" — a kiadás-panel
    //: mentés-üzemmódja, ugyanúgy a könyvtár alján, mint az Ajándék-CD.
    BackupHost {
        id: backupHost
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        visible: nyitva && !hostWindow.viewerOpen && !hostWindow.timelineOpen
                 && hostWindow.libraryFrameVisible
        //: #3751: a rács-szűrő csak a panel melletti könyvtár-rácsra hat —
        //: keresésben, időrendben, más lapon a teljes lista látszik
        racsLatszik: visible && !(hostController && hostController.searchActive)
        nezoNyitva: hostWindow.viewerOpen || hostWindow.slideshowRunning
        //: a mentés nyitása becsukja az Ajándék-CD-t (ld. fent)
        onNyitvaChanged: if (nyitva) giftCdHost.nyitva = false
    }

    // -- fájlműveletek (#15): kontextusmenü + dialógusok --------------------

    MainPhotoContextMenu {
        id: photoContextMenu
        hostWindow: layers.hostWindow
        hostController: layers.hostController
        hostFileOpsController: typeof fileOpsController !== "undefined"
            ? fileOpsController : null
        hostFileOpsDialogs: hostRefs.fileOpsDialogs
        hostMainDialogs: hostRefs.mainDialogs
        hostMoveToNewPersonDialog: hostRefs.moveToNewPersonDialog
        hostOpenWithDialog: hostRefs.openWithDialog
        hostRemoveFromAlbumDialog: hostRefs.removeFromAlbumDialog
        hostRemovePeopleFacesDialog: hostRefs.removePeopleFacesDialog
        hostSaveDialogs: hostRefs.saveDialogs
        hostToolbar: hostRefs.toolbar
    }









    // #1129: a lebegő értesítősáv (Picasa Notifier) — önálló, keret nélküli
    // ablak a munkaterület jobb alsó részén. Az alkalmazás indítása hozza
    // létre, nem a főablak, ezért nincs `transientParent`-je.
    //
    // A `NotifierBus.attached` kapun át a `CollageDoneNotice` MAGÁTÓL
    // elhallgat, amint a sáv jelen van — így ugyanaz az esemény nem szólal
    // meg kétszer, két helyen. A `CollageDoneNotice` SZÁNDÉKOSAN marad a
    // fában: a #1119 őre a jelenlétét állítja, és a törlése önálló döntés
    // (a sáv nélküli üzemmód tartaléka).
    PicasaNotifier {
        id: picasaNotifier
        onActivated: function (kind, payload) {
            if (kind === "collage")
                hostWindow.openCollageNodeInEditor(payload)
        }
    }

    // #1028: „A kollázs kész (kattintson ide)" — a lapzárás UTÁN is látszik,
    // ezért a gazdában él, nem a panelben, ami közben bezárul.
    CollageDoneNotice {
        id: collageDoneNotice
        z: 100
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        onClicked: {
            var cel = collageDoneNotice.path
            collageDoneNotice.dismiss()
            hostWindow.openCollageNodeInEditor(cel)
        }
    }


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
