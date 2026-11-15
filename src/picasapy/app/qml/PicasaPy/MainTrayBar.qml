import QtQuick
import QtQuick.Controls
import PicasaPy
import "../selection.js" as Selection

// A főablak alsó sávjának bekötése; a tálca felületét továbbra is a TrayBar adja.
TrayBar {
    id: trayBar
    objectName: "trayBar"

    required property var hostWindow
    required property var hostController
    required property var hostPhotoViewer
    required property var hostExportDialogs
    required property var hostCreateDialogs
    required property var hostFileOpsDialogs
    required property var hostFileOpsController
    required property var hostDocumentTabStrip

    width: parent ? parent.width : 0
    height: visible ? implicitHeight : 0
    visible: hostWindow.libraryFrameVisible && !hostWindow.quickViewerLaunch
    appWindow: hostWindow

    onPhotosDroppedOnTray: function(rows) {
        if (hostController && rows && rows.length > 0)
            hostController.holdRows(rows)
    }
    // #4637: a testreszabható alsó kimeneti gombsor közös helyi menüje.
    onConfigureButtonsContextMenuRequested: function(anchorItem, x, y) {
        hostWindow.openConfigureButtonsContextMenu(anchorItem, x, y)
    }
    //: #3756: a kettős nézet aktív felét mutatja az alsó sáv.
    viewerIndex: hostPhotoViewer ? hostPhotoViewer.aktivSor : -1
    // #2564: a nagyítás állapota a nézőé, a művelet jelzésként megy vissza.
    viewerZoomValue: hostPhotoViewer ? hostPhotoViewer.zoomValue : 0
    viewerZoomAvailable: hostWindow.viewerOpen && hostPhotoViewer
                         && hostPhotoViewer.photoOverlaysUsable
    onZoomFitRequested: if (hostPhotoViewer) hostPhotoViewer.zoomFit()
    onZoomActualRequested: if (hostPhotoViewer) hostPhotoViewer.zoomActual()
    onZoomValueRequested: (ertek) => {
        if (hostPhotoViewer) hostPhotoViewer.setZoomValue(ertek)
    }
    onExportRequested: hostExportDialogs.ensure().openForSelection()
    // #1917: a tálca helyi menüje a főablak műveleteit hívja.
    onViewAndEditRequested: hostWindow.nezdEsSzerkeszd()
    onTrayRotateRightRequested:
        hostController.rotateRightMany(hostWindow.selectedRows())
    onTrayRotateLeftRequested:
        hostController.rotateLeftMany(hostWindow.selectedRows())
    // #6995: a tálca SAJÁT kijelölése (#2039, másik mappából tartott képek is
    // lehetnek benne) az elsőbbséget élvezi; ha a tálcán nincs kijelölés, a
    // rács kijelölése. Mappánként egy fájlkezelő-ablak nyílik.
    function locatePaths() {
        var elemek = ctl && ctl.trayItems ? ctl.trayItems : []
        var utak = []
        for (var i = 0; i < traySelectedIndexes.length; ++i) {
            var elem = elemek[Number(traySelectedIndexes[i])]
            if (elem && elem.path) utak.push(elem.path)
        }
        if (utak.length > 0) return utak
        return Selection.pathsInGridOrder(
            hostController.photos, hostWindow.selectedRows())
    }
    onTrayLocateRequested: hostFileOpsController.revealPhotos(locatePaths())
    onTrayPropertiesRequested: hostWindow.valtsFiokLapot("properties")
    onPrintRequested: hostWindow.openPrint()
    onCollageRequested: hostWindow.openCollageTab()
    onMovieRequested: hostCreateDialogs.ensure().openMovie()
    //: #1939: a klip-gyűjtő mód üzenetsávjának „Vissza” gombja.
    onBackToCollageRequested: {
        hostWindow.backToCollagePrompted = false
        hostDocumentTabStrip.activateTab(hostWindow.collageTabId)
    }
    onBackToMovieMakerRequested: hostWindow.returnToMovieMaker()
    onEmailRequested: hostWindow.sendSelectionByEmail()
    onAddSelectedToScreensaverRequested: hostWindow.requestAddToScreensaver()
    onStarSelectedPhotosRequested: {
        if (hostController)
            hostController.toggleStarMany(hostWindow.photoActionRows())
    }
    onNewAlbumWithSelectionRequested:
        hostFileOpsDialogs.ensure().openNewAlbumProperties(
            hostController ? hostController.currentFolder : "",
            hostWindow.photoActionRows())
}
