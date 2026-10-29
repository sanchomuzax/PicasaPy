import QtQuick
import PicasaPy

RightDrawer {
    id: drawerRoot

    required property var hostWindow
    required property var hostController
    required property var hostToolbar
    required property var hostPhotoViewer
    required property var hostMainSplit
    required property var hostMainLibraryCanvas
    required property var hostMainDialogs
    property string propertiesLabel: ""
    property string tagsLabel: ""
    property string peopleLabel: ""
    property string placesLabel: ""
    property alias peoplePanel: peoplePanelItem

    //: #3035: a fiók ANIMÁLVA tolódik be és ki (`thumbui.tre:700`:
    //: `varbutton RIGHTDRAWEROFFSET -280 0 1` — a harmadik érték az
    //: animáció jelzője; az időtartam 0,4 s, `0x00cf4ce0`). A csukott
    //: állapot NULLA széles, tehát a könyvtár visszakapja a helyet —
    //: és mivel a `drawerRoot.hostMainSplit` jobb széle a fiók bal éléhez van kötve,
    //: a szerkesztő előnézete is EGYÜTT méreteződik vele, ahogy a mért
    //: kapcsoló két elemet értesít (`editpanel/previewimage…`).
    //: nyitáskor AZONNAL látszik (a tartalom nem késik), záráskor
    //: pedig a kitolás végéig marad látható
    visible: (drawerRoot.hostWindow.activeDrawerTab !== "" || drawerRoot.width > 0)
             && drawerRoot.hostMainSplit.visible
    ablakSzelesseg: drawerRoot.hostWindow.width
    anchors.top: drawerRoot.hostMainSplit.top
    anchors.bottom: drawerRoot.hostMainSplit.bottom
    anchors.right: parent.right
    width: drawerRoot.hostWindow.activeDrawerTab !== "" ? drawerRoot.kivantSzelesseg : 0
    Behavior on width {
        NumberAnimation {
            duration: drawerRoot.animacioMs
            easing.type: Easing.InOutQuad
        }
    }
    //: a négy felirat UGYANAZ a szöveg, mint a Nézet menü tételei
    //: (#754) — a gyorsítót és a billentyű-tippet levágva
    cim: drawerRoot.hostWindow.activeDrawerTab === "properties" ? propertiesLabel
         : drawerRoot.hostWindow.activeDrawerTab === "tags" ? tagsLabel
         : drawerRoot.hostWindow.activeDrawerTab === "people" ? peopleLabel
         : drawerRoot.hostWindow.activeDrawerTab === "places" ? placesLabel : ""
    onCloseRequested: drawerRoot.hostWindow.ureseidAFiokot()

// Címkék-panel (#12): a fiók egyik lapja, Ctrl+T / Nézet → Címkék
TagsPanel {
    objectName: "tagsPanel"
    visible: drawerRoot.hostWindow.tagsPanelOpen
    anchors.fill: parent
    hasSelection: drawerRoot.hostWindow.selectedRows().length > 0
    selectedPhotoName: {
        var rows = drawerRoot.hostWindow.selectedRows()
        if (!drawerRoot.hostController || rows.length !== 1) return ""
        var path = drawerRoot.hostController.photos.filePathAt(Number(rows[0]))
        var separator = Math.max(path.lastIndexOf("/"), path.lastIndexOf("\\"))
        return path.substring(separator + 1)
    }
    wholeAlbumSelected: {
        var rows = drawerRoot.hostWindow.selectedRows()
        return drawerRoot.hostController && rows.length > 1
               && rows.length === drawerRoot.hostController.photos.rowCount()
    }
    //: #2998: írásvédett elem a kijelölésben — a panel ELŐRE szól.
    //: A `photos.revision` a kötés kiváltója, ahogy a `tags`-nél is;
    //: a `!== undefined` a próbák stub-vezérlőjére véd (#1572).
    readOnlySelection: (drawerRoot.hostController
                        && drawerRoot.hostController.selectionReadOnly !== undefined)
        ? (drawerRoot.hostController.photos.revision,
           drawerRoot.hostController.selectionReadOnly(drawerRoot.hostWindow.selectedRows()))
        : false
    // a photos.revision-nel együtt kötve: címke-írás után frissül
    // #305: null-őr
    tags: drawerRoot.hostController
        ? (drawerRoot.hostController.photos.revision,
           drawerRoot.hostController.keywordsOfRows(drawerRoot.hostWindow.selectedRows()))
        : []
    onAddRequested: function(keyword) {
        drawerRoot.hostWindow.addTagToRows(drawerRoot.hostWindow.selectedRows(), keyword)
    }
    onRemoveRequested: function(keyword) {
        drawerRoot.hostController.removeKeywordFromRows(drawerRoot.hostWindow.selectedRows(), keyword)
    }
    onCloseRequested: drawerRoot.hostWindow.ureseidAFiokot()
    // #422: a címke jobbklikk-menüje (Picasa `Tags` menüosztály)
    onAddToSelectionRequested: function(keyword) {
        drawerRoot.hostWindow.addTagToRows(drawerRoot.hostWindow.selectedRows(), keyword)
    }
    onFindTaggedRequested: function(keyword) {
        if (drawerRoot.hostController) drawerRoot.hostToolbar.keresesSzoveggel(keyword)
    }
}

// Helyek-panel (#30): jobb oldali hasáb, Nézet → Helyek — a látszó
// képek helyei térképen, és a kijelölés geocímkézése
PlacesPanel {
    objectName: "placesPanel"
    //: #2013: a PANEL a saját, mért küszöbén megy át (5 GEOCÍMKÉZETT
    //: elem fölött kérdez) — az eredetiben ez külön erőforrás a
    //: menüparancsétól (`ClearGeoTag::warn`), ami feltétel nélkül
    //: kérdez. A menüpont változatlanul azon megy át.
    onClearGeotagRequested: (rows) => drawerRoot.hostMainDialogs.panelClearGeotagDialog.ensure().futtasd(rows)
    onSetGeotagRequested: (rows, la, lo) => drawerRoot.hostMainDialogs.setGeotagDialog.ensure().futtasd(rows, la, lo)
    onPhotosDroppedRequested: (rows, la, lo) => drawerRoot.hostMainDialogs.dropGeotagDialog.ensure().futtasd(rows, la, lo)
    visible: drawerRoot.hostWindow.placesPanelOpen
    anchors.fill: parent
    appWindow: drawerRoot.hostWindow
    onCloseRequested: drawerRoot.hostWindow.ureseidAFiokot()
    onPhotoActivated: function(row) {
        drawerRoot.hostWindow.selectedIndexes = [row]
        drawerRoot.hostWindow.selectedIndex = row
    }
    onMarkerSearchRequested: function(rows) {
        if (!rows || rows.length === 0) return
        drawerRoot.hostWindow.selectedIndexes = rows.slice(0)
        drawerRoot.hostWindow.selectedIndex = rows[0]
    }
}

// Tulajdonságok-panel (#13): jobb oldali hasáb, Alt+Enter /
// Nézet → Tulajdonságok — csak olvasás
PropertiesPanel {
    objectName: "propertiesPanel"
    visible: drawerRoot.hostWindow.propertiesPanelOpen
    anchors.fill: parent
    hasSelection: drawerRoot.hostWindow.selectedIndex >= 0
    appController: drawerRoot.hostController
    selectedRows: drawerRoot.hostWindow.selectedRows()
    focusRow: drawerRoot.hostWindow.selectedIndex
    // a photos.revision-nel együtt kötve: modell-frissüléskor újraolvas
    // #305: null-őr
    entries: drawerRoot.hostController
        ? (drawerRoot.hostController.photos.revision,
           drawerRoot.hostController.propertiesOf(drawerRoot.hostWindow.selectedIndex))
        : []
    onCloseRequested: drawerRoot.hostWindow.ureseidAFiokot()
    onEditTagsRequested: drawerRoot.hostWindow.valtsFiokLapot("tags")
}

// Emberek-panel (#26): a jobb fiók negyedik panelje. EGY fejléc és
// EGY lista (#3566): a kijelölt képek nevesített emberei; a fejlécet
// a panel választja a spec 9/b fája szerint.
PeoplePanel {
    id: peoplePanelItem
    objectName: "peoplePanel"
    visible: drawerRoot.hostWindow.peoplePanelOpen
    anchors.fill: parent
    manualAddActive: drawerRoot.hostWindow.viewerOpen && drawerRoot.hostPhotoViewer.facesEditMode
    headerRefreshKey: drawerRoot.hostController
        ? [drawerRoot.hostWindow.selectedRows().join(","),
           drawerRoot.hostWindow.unnamedFacesOpen
               ? drawerRoot.hostMainLibraryCanvas.unnamedFacesView.selectedCount : 0,
           drawerRoot.hostWindow.unnamedFacesOpen ? drawerRoot.hostWindow.peopleFaceRevision : 0,
           drawerRoot.hostWindow.unnamedFacesOpen, drawerRoot.hostWindow.facesAlbumMode,
           drawerRoot.hostWindow.activeDrawerTab, drawerRoot.hostWindow.viewerOpen, drawerRoot.hostWindow.timelineOpen,
           drawerRoot.hostController.searchActive, drawerRoot.hostController.currentPersonName,
           drawerRoot.hostMainLibraryCanvas.unnamedFacesView.grouped, drawerRoot.hostWindow._selectionPending > 0]
              .join("|")
        : ""
    // #3585: a „Név nélküliek" albumban a kijelölés az arcoké, és a
    // fejléc a csoportosítás-váltógombot követi
    selectionCount: drawerRoot.hostWindow.unnamedFacesOpen
        ? drawerRoot.hostMainLibraryCanvas.unnamedFacesView.selectedCount : drawerRoot.hostWindow.selectedRows().length
    faceScanController: drawerRoot.hostWindow._faceScanController
    // #4586: a háttér-arckeresés állapota (spec 9/b: betöltés, ellenőrizetlen
    // fájlok, adatok rendezése)
    // A kapu a KIJELÖLÉSRE vonatkozik: csak a még nem átvizsgált
    // kijelölt képek számítanak (egy már átvizsgált képnél nincs betöltés).
    loading: drawerRoot.hostWindow._selectionPending > 0
    uncheckedCount: drawerRoot.hostWindow._selectionPending
    sortingPercent: drawerRoot.hostWindow._faceScanController
        ? (drawerRoot.hostWindow._faceScanController.sortingPercent ?? -1) : -1
    folderSelected: drawerRoot.hostController ? drawerRoot.hostController.currentFolder.length > 0 : false
    unnamedAlbumMode: drawerRoot.hostWindow.unnamedFacesOpen
    unnamedGrouped: drawerRoot.hostMainLibraryCanvas.unnamedFacesView.grouped
    // #4585: a Névtelenek GYŰJTEMÉNYE üres (az Ignored album nem ide tartozik)
    unnamedCollectionEmpty: drawerRoot.hostWindow.facesAlbumMode === "unnamed"
                            && drawerRoot.hostMainLibraryCanvas.unnamedFacesView.groupsModel.length === 0
    // #3585: a Névtelenek-album nem vált nézetet a controllerben, így a
    // `currentPersonName` az előző személyé marad — az albumban nincs
    // „nézett személy", tehát a „Szintén" lista sem
    currentPerson: drawerRoot.hostController && !drawerRoot.hostWindow.unnamedFacesOpen
        ? drawerRoot.hostController.currentPersonName : ""
    // a photos.revision-nel együtt kötve: arc-írás után frissül
    peopleHere: drawerRoot.hostController
        ? (drawerRoot.hostWindow.peopleFaceRevision, drawerRoot.hostController.photos.revision,
           drawerRoot.hostController.peopleOfRows(drawerRoot.hostWindow.selectedRows()))
        : []
    unnamedFacesHere: drawerRoot.hostController && !drawerRoot.hostWindow.unnamedFacesOpen
        ? (drawerRoot.hostWindow.peopleFaceRevision, drawerRoot.hostWindow.unnamedFaceRevision,
           drawerRoot.hostController.photos.revision,
           drawerRoot.hostController.unnamedFacesOfRows(drawerRoot.hostWindow.selectedRows()))
        : []
    onPersonChosen: function(name) {
        if (!drawerRoot.hostController) return
        drawerRoot.hostWindow.clearSelection()
        drawerRoot.hostWindow.unnamedFacesOpen = false
        drawerRoot.hostController.showPerson(name)
    }
    onManualAddRequested: {
        if (!drawerRoot.hostWindow.viewerOpen) drawerRoot.hostWindow.nezdEsSzerkeszd()
        if (drawerRoot.hostWindow.viewerOpen) drawerRoot.hostPhotoViewer.beginManualFaceAdd()
    }
    onManualCancelRequested: drawerRoot.hostPhotoViewer.cancelManualFaceAdd()
    onCloseRequested: drawerRoot.hostWindow.ureseidAFiokot()
}

}
