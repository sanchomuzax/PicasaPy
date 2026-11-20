pragma ComponentBehavior: Bound
import QtQuick
import "../selection.js" as Selection

// A rácsmodell sorváltozásai alatt megőrzi a felhasználó kijelölését.
Item {
    id: photoSelectionState
    anchors.fill: parent
    required property var hostWindow
    required property var hostController

    // #135: sorbeszúráskor és modell-resetkor az indexek elmozdulnak;
    // ezért a kijelölést fotóazonosító alapján állítjuk vissza.
    property var pendingSelectedIds: []
    property string pendingAnchorId: ""
    property var pendingRenameTargets: []

    function captureSelection() {
        var ids = []
        for (var k = 0; k < hostWindow.selectedIndexes.length; ++k) {
            var id = hostController.photos.idAt(
                Number(hostWindow.selectedIndexes[k]))
            if (id.length > 0) ids.push(parseInt(id, 10))
        }
        pendingSelectedIds = ids
        pendingAnchorId = hostWindow.selectedIndex >= 0
            ? hostController.photos.idAt(hostWindow.selectedIndex) : ""
    }

    function restoreSelection() {
        hostWindow.selectedIndexes = Selection.remapByIds(
            pendingSelectedIds, hostController.photos.rowOfId)
        hostWindow.selectedIndex = pendingAnchorId.length > 0
            ? hostController.photos.rowOfId(parseInt(pendingAnchorId, 10))
            : -1
    }

    Connections {
        target: hostController
        function onRenameBatchTargets(targets) {
            photoSelectionState.pendingRenameTargets = targets || []
        }
    }

    Connections {
        target: hostController ? hostController.photos : null
        function onRowsAboutToBeInserted(parent, first, last) {
            photoSelectionState.captureSelection()
        }
        function onRowsInserted(parent, first, last) {
            photoSelectionState.restoreSelection()
        }
        function onModelAboutToBeReset() {
            photoSelectionState.captureSelection()
        }
        function onModelReset() {
            photoSelectionState.restoreSelection()
            // Az átnevezett fájl új útvonal miatt új adatbázis-id-t kaphat.
            // Csak akkor helyettesítjük a régi azonosítót, ha az már eltűnt
            // a modellből és az új útvonal megjelent; sikertelen átnevezésnél
            // a régi ID-alapú állapot marad érvényben.
            if (hostWindow._pendingRenamePhotoId.length > 0
                    && hostWindow._pendingRenameTargetPath.length > 0) {
                var ujSor = hostController.photos.rowOfPath(
                    hostWindow._pendingRenameTargetPath)
                var regiId = parseInt(hostWindow._pendingRenamePhotoId, 10)
                if (ujSor >= 0
                        && hostController.photos.rowOfId(regiId) < 0
                        && photoSelectionState.pendingSelectedIds.indexOf(regiId) >= 0) {
                    var ujKijeloles = hostWindow.selectedIndexes.slice()
                    if (ujKijeloles.indexOf(ujSor) < 0)
                        ujKijeloles.push(ujSor)
                    ujKijeloles.sort(function (a, b) { return a - b })
                    hostWindow.selectedIndexes = ujKijeloles
                    if (photoSelectionState.pendingAnchorId === hostWindow._pendingRenamePhotoId)
                        hostWindow.selectedIndex = ujSor
                }
                hostWindow._pendingRenamePhotoId = ""
                hostWindow._pendingRenameTargetPath = ""
            }
            var renameTargets = photoSelectionState.pendingRenameTargets || []
            if (renameTargets.length > 0) {
                var kijelolt = hostWindow.selectedIndexes.slice()
                var horgony = hostWindow.selectedIndex
                for (var t = 0; t < renameTargets.length; ++t) {
                    var entry = renameTargets[t]
                    var regiId = Number(entry.photoId)
                    if (hostController.photos.rowOfId(regiId) >= 0
                            || photoSelectionState.pendingSelectedIds.indexOf(regiId) < 0)
                        continue
                    var ujSor = hostController.photos.rowOfPath(entry.targetPath)
                    if (ujSor < 0) continue
                    if (kijelolt.indexOf(ujSor) < 0) kijelolt.push(ujSor)
                    if (photoSelectionState.pendingAnchorId === String(regiId))
                        horgony = ujSor
                }
                kijelolt.sort(function (a, b) { return a - b })
                hostWindow.selectedIndexes = kijelolt
                hostWindow.selectedIndex = horgony
                photoSelectionState.pendingRenameTargets = []
            }
        }
    }
}
