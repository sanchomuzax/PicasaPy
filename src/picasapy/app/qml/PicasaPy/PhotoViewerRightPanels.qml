import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    id: viewerRightPanels
    property var hostViewer: null
    readonly property var viewer: hostViewer
    spacing: 0
    visible: viewer.propertiesOpen || viewer.tagsOpen
             || viewer.placesOpen || viewer.peopleOpen
    Layout.fillHeight: true

    // #192: Tulajdonságok-panel jobb oldalt — ugyanaz a buta
    // komponens, mint a könyvtár-nézetben (Main.qml), a nézett
    // kép adataival; a bezárás a közös kapcsolót állítja le
    PropertiesPanel {
        objectName: "viewerPropertiesPanel"
        visible: viewer.propertiesOpen
        Layout.preferredWidth: 210
        Layout.minimumWidth: 160
        Layout.fillHeight: true
        hasSelection: viewer.currentIndex >= 0
        appController: (typeof controller !== "undefined")
                       ? controller : null
        selectedRows: viewer.currentIndex >= 0
                      ? [viewer.currentIndex] : []
        focusRow: viewer.currentIndex
        // a photos.revision-nel együtt kötve: modell-frissüléskor
        // (pl. forgatás, felirat-mentés) újraolvas; a controller
        // önálló példányosításnál (tesztek) hiányozhat
        entries: (viewer.propertiesOpen && viewer.photosModel
                  && typeof controller !== "undefined" && controller)
            ? (viewer.photosModel.revision,
               controller.propertiesOf(viewer.currentIndex))
            : []
        onCloseRequested: viewer.zarjaAFiokot()
        onEditTagsRequested: {
            if (viewer.appWindow
                    && viewer.appWindow.valtsFiokLapot !== undefined)
                viewer.appWindow.valtsFiokLapot("tags")
        }
    }

    //: #2566: a másik három lap CSAK AKKOR létezik, ha a NÉZŐ
    //: LÁTSZIK, és épp az a lap aktív.
    //:
    //: ⚠️ Ez nem takarékosság, hanem HELYESSÉG. A három komponens a
    //: SAJÁT gyerekeire éget objectName-et (`placesClearButton`,
    //: `peoplePanelClose`, `tagInput` …), amit a példányosítás
    //: helyén nem lehet felülírni. Mohó példányosítással a
    //: `findChild` a nézőbeli MÁSODPÉLDÁNYT találná meg a
    //: könyvtárbeli helyett — a `test_qml_places.py` két őre
    //: azonnal el is bukott rá, mielőtt `Loader`-be került.
    //: Csukott néző mellett így egyetlen példány van, a könyvtáré.
    //:
    //: ⚠️ A `viewer.visible` NEM elhagyható: a fiók lapját a
    //: KÖNYVTÁRBAN is át lehet kapcsolni, és a `tagsOpen` akkor is
    //: igaz — a néző példánya enélkül a könyvtár-nézetben is
    //: felépülne.
    Loader {
        objectName: "viewerTagsPanelLoader"
        active: viewer.tagsOpen && viewer.visible
        visible: viewer.tagsOpen
        Layout.preferredWidth: 190
        Layout.minimumWidth: 150
        Layout.fillHeight: true
        //: Ugyanaz a buta komponens, mint a könyvtárban; a
        //: különbség csak az, hogy MIRE hat: ott a rács
        //: kijelölésére, itt a nézett képre (`drawerRows`).
        sourceComponent: TagsPanel {
            objectName: "viewerTagsPanel"
            hasSelection: viewer.currentIndex >= 0
            //: a photos.revision-nel együtt kötve: címke-írás után
            //: azonnal frissül (a könyvtári párja ugyanígy)
            tags: (viewer.photosModel && viewer.controllerReady
                   && viewer.currentIndex >= 0)
                ? (viewer.photosModel.revision,
                   controller.keywordsOfRows(viewer.drawerRows))
                : []
            onAddRequested: function(keyword) {
                if (viewer.controllerReady)
                    controller.addKeywordToRows(
                        viewer.drawerRows, keyword)
            }
            onRemoveRequested: function(keyword) {
                if (viewer.controllerReady)
                    controller.removeKeywordFromRows(
                        viewer.drawerRows, keyword)
            }
            //: a helyi menü „rátétel a kijelölésre" tétele: a
            //: nézőben a kijelölés EGY kép, tehát ugyanoda fut,
            //: mint a hozzáadás
            onAddToSelectionRequested: function(keyword) {
                if (viewer.controllerReady)
                    controller.addKeywordToRows(
                        viewer.drawerRows, keyword)
            }
            //: a találatok a KÖNYVTÁR rácsán jelennek meg, amit a
            //: néző eltakarna — ezért a gazda zárja a nézőt, és
            //: ő keres
            onFindTaggedRequested: function(keyword) {
                viewer.findTaggedRequested(keyword)
            }
            onCloseRequested: viewer.zarjaAFiokot()
        }
    }

    Loader {
        objectName: "viewerPlacesPanelLoader"
        active: viewer.placesOpen && viewer.visible
        visible: viewer.placesOpen
        Layout.preferredWidth: 320
        Layout.minimumWidth: 220
        Layout.fillHeight: true
        sourceComponent: PlacesPanel {
            objectName: "viewerPlacesPanel"
            appWindow: viewer.appWindow
            //: a geocímkézés a NÉZETT képre hat, nem a rács
            //: kijelölésére (ld. `drawerRows`)
            targetRows: viewer.drawerRows
            //: a térkép-jelölőre kattintva a néző lép oda — a
            //: könyvtárban ugyanez a jel a rács kijelölését mozgatja
            onPhotoActivated: function(row) { viewer.show(row) }
            onMarkerSearchRequested: function(rows) {
                if (!rows || rows.length === 0) return
                viewer.appWindow.selectedIndexes = rows.slice(0)
                viewer.show(rows[0])
            }
            onClearGeotagRequested: function(rows) {
                viewer.clearGeotagRequested(rows)
            }
            onSetGeotagRequested: function(rows, la, lo) {
                viewer.setGeotagRequested(rows, la, lo)
            }
            onPhotosDroppedRequested: function(rows, la, lo) {
                viewer.dropGeotagRequested(rows, la, lo)
            }
            onCloseRequested: viewer.zarjaAFiokot()
        }
    }

    Loader {
        objectName: "viewerPeoplePanelLoader"
        active: viewer.peopleOpen && viewer.visible
        visible: viewer.peopleOpen
        Layout.preferredWidth: 280
        Layout.minimumWidth: 200
        Layout.fillHeight: true
        //: A nézett kép nevesített emberei.
        sourceComponent: PeoplePanel {
            objectName: "viewerPeoplePanel"
            headerRefreshKey: [viewer.drawerRows.join(","),
                viewer.currentIndex, viewer.peopleOpen,
                viewer.facesEditMode,
                viewer.manualFaceAddRevision,
                viewer.controllerReady
                    ? controller.currentPersonName : "",
                pendingCount() > 0].join("|")
            selectionCount: viewer.drawerRows.length
            faceScanController: viewer.appWindow
                ? viewer.appWindow._faceScanController : null
            currentPerson: viewer.controllerReady
                ? controller.currentPersonName : ""
            //: #4586: a háttér-arckeresés állapota (spec 9/b)
            loading: uncheckedCount > 0
            uncheckedCount: pendingCount()
            sortingPercent: faceScanController
                ? faceScanController.sortingPercent : -1
            peopleHere: (viewer.photosModel && viewer.controllerReady)
                ? (viewer.appWindow
                   ? viewer.appWindow.peopleFaceRevision : 0,
                   viewer.photosModel.revision,
                   controller.peopleOfRows(viewer.drawerRows))
                : []
            unnamedFacesHere:
                (viewer.photosModel && viewer.controllerReady)
                ? (viewer.appWindow
                   ? viewer.appWindow.peopleFaceRevision : 0,
                   viewer.appWindow
                   ? viewer.appWindow.unnamedFaceRevision : 0,
                   viewer.photosModel.revision,
                   controller.unnamedFacesOfRows(viewer.drawerRows))
                : []
            function pendingCount() {
                if (!viewer.peopleOpen || !faceScanController
                        || !viewer.photosModel)
                    return 0
                // a függés az `uncheckedFiles`-en: haladásra újraszámol
                if (faceScanController.uncheckedFiles <= 0)
                    return 0
                var paths = []
                for (var i = 0; i < viewer.drawerRows.length; ++i) {
                    var path = viewer.photosModel.filePathAt(
                        Number(viewer.drawerRows[i]))
                    if (path.length > 0) paths.push(path)
                }
                return faceScanController.pendingAmong(paths)
            }
            //: #3566: a szerkesztőben mindig az egyképes ág fut
            //: (az eredetiben az `editpanel/preview` látszik)
            editorView: true
            manualAddActive: viewer.facesEditMode
            //: a személy albuma a KÖNYVTÁR rácsán nyílik — a gazda
            //: zárja a nézőt, és ő vált (ld. `findTaggedRequested`)
            onPersonChosen: function(name) { viewer.personChosen(name) }
            onManualAddRequested: viewer.beginManualFaceAdd()
            onManualCancelRequested: viewer.cancelManualFaceAdd()
            onCloseRequested: viewer.zarjaAFiokot()
        }
    }
}
