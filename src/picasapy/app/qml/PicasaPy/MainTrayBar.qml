import QtQuick
import QtQuick.Controls
import PicasaPy

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
    viewerIndex: hostPhotoViewer.aktivSor
    // #2564: a nagyítás állapota a nézőé, a művelet jelzésként megy vissza.
    viewerZoomValue: hostPhotoViewer.zoomValue
    viewerZoomAvailable: hostWindow.viewerOpen && hostPhotoViewer.photoOverlaysUsable
    onZoomFitRequested: hostPhotoViewer.zoomFit()
    onZoomActualRequested: hostPhotoViewer.zoomActual()
    onZoomValueRequested: (ertek) => hostPhotoViewer.setZoomValue(ertek)
    onExportRequested: hostExportDialogs.ensure().openForSelection()
    // #1917: a tálca helyi menüje a főablak műveleteit hívja.
    onViewAndEditRequested: hostWindow.nezdEsSzerkeszd()
    onTrayRotateRightRequested:
        hostController.rotateRightMany(hostWindow.selectedRows())
    onTrayRotateLeftRequested:
        hostController.rotateLeftMany(hostWindow.selectedRows())
    onTrayLocateRequested: {
        var sorok = hostWindow.selectedRows()
        if (sorok.length === 0) return
        var ut = hostController.photos.filePathAt(sorok[0])
        if (ut.length > 0) hostFileOpsController.revealPhoto(ut)
    }
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
