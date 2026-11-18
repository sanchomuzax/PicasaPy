import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy

// A főablak eszköztár-fejléce, explicit gazda- és testvérhivatkozásokkal.
MainToolbar {
    property var hostWindow
    property var hostRefs: ({})
    id: toolbar
    objectName: "mainToolbar"
    updateOwnerWindow: hostWindow
    property bool activityWorking: false
    property bool activityCancellable: false
    signal activityCancelRequested()
    // #6946: a verziócímke háttérmunka közben is látszik az activityBadge mellett.
    versionHidden: false
    activityBadgeReserve: activityBadge.visible ? (activityBadge.width + 5) : 0
    // #6474 / #6946: a keresőmező a jelző és a verziócímke előtt ér véget
    activityReserve: activityBadge.visible ? (activityBadge.width + 5 + 47) : 47

    // #6405: a háttérmunka-jelző a keresőmezőtől jobbra, vele egy sorban, az
    // eszközsáv jobb szélén (az eredeti képernyőkép szerint, ld. ActivityBadge.qml).
    ActivityBadge {
        id: activityBadge
        objectName: "activityBadge"
        z: 3
        working: toolbar.activityWorking
        cancellable: toolbar.activityCancellable
        x: toolbar.width - width - 5
        y: toolbar.searchBoxItem.y
            + Math.round((toolbar.searchBoxItem.height - height) / 2)
        onCancelRequested: toolbar.activityCancelRequested()
    }
    // #741/4: a nézőben (és így a szerkesztőben) NINCS alkalmazás-szintű
    // eszköztár. A binárisban a szerkesztő felső 40 képpontos sávjában
    // egyetlen elem van, az `editpanel/albumview` („Vissza a
    // könyvtárhoz", 122 × 22) - az nálunk már megvan a
    // `PhotoViewer.qml`-ben. Az Importálás+kereső sáv itt csak lefelé
    // tolta az egész panelt, és ezzel a mért geometria sem jöhetett ki.
    // A tulajdonosi döntés (`docs/decisions/szerkeszto-bal-panel.md`):
    // a felület PONTOSAN az eredetit kövesse.
    //
    // #1026: az eszközsáv a KÖNYVTÁR panelének gyereke (`thumbui.tre`:
    // `importbutton`/`sbutton`/`timelinebutton`/`globalmode`) - a
    // projekt-lapon a panellel EGYÜTT tűnik el, nem külön szabályból.
    visible: !hostWindow.viewerOpen && hostWindow.libraryFrameVisible
    // #7081: a keresés gépelés közben NULLA késleltetéssel fut, de a
    // közbülső lenyomásokat összevonja. Eredeti (`0x0097fb90`,
    // `0x005e4e0d`): az `EN_CHANGE` azonnal keres, és csak akkor hagyja ki,
    // ha a billentyűsorban még vár egy `WM_KEYDOWN`; időzítő nincs. A Qt
    // megfelelője a `Qt.callLater`: az egy eseményhurok-körön belül érkező
    // leütések EGY keresést adnak, a gépelés szünetében pedig azonnal fut.
    property string pendingSearchText: ""
    property bool searchPending: false

    // #7216: a keresés előtti mappa- és képkijelölés pillanatképe. Sorindex
    // helyett fotóazonosítókat tárolunk, mert a keresés és a mappaváltás
    // közben a modell új sorrendet kap.
    property var _searchOrigin: null
    property bool _restoringSearchOrigin: false

    function captureSearchOrigin() {
        if (_searchOrigin !== null || !hostWindow || !controller
                || !controller.photos)
            return
        var photoIds = []
        var selected = hostWindow.selectedIndexes || []
        for (var i = 0; i < selected.length; ++i) {
            var id = controller.photos.idAt(Number(selected[i]))
            if (id.length > 0)
                photoIds.push(id)
        }
        var anchorId = hostWindow.selectedIndex >= 0
            ? controller.photos.idAt(hostWindow.selectedIndex) : ""
        _searchOrigin = {
            folder: controller.currentFolder,
            photoIds: photoIds,
            anchorId: anchorId
        }
    }

    function restoreSearchOrigin() {
        var origin = _searchOrigin
        _restoringSearchOrigin = true
        hostWindow.clearSelection()
        if (typeof controller !== "undefined" && controller) {
            if (typeof controller.clearFilter === "function")
                controller.clearFilter()
            else
                controller.search("")
            if (origin && origin.folder
                    && controller.currentFolder !== origin.folder)
                controller.selectFolder(origin.folder)
        }
        if (origin && controller && controller.photos) {
            var rows = []
            for (var i = 0; i < origin.photoIds.length; ++i) {
                var row = controller.photos.rowOfId(Number(origin.photoIds[i]))
                if (row >= 0)
                    rows.push(row)
            }
            rows.sort(function (a, b) { return a - b })
            var anchor = origin.anchorId.length > 0
                ? controller.photos.rowOfId(Number(origin.anchorId)) : -1
            hostWindow.selectedIndexes = rows
            hostWindow.selectedIndex = anchor >= 0
                ? anchor : (rows.length > 0 ? rows[0] : -1)
            if (hostWindow.selectedIndex >= 0 && hostRefs.revealSearchPhoto) {
                var selectedRow = hostWindow.selectedIndex
                Qt.callLater(function () {
                    hostRefs.revealSearchPhoto(selectedRow)
                })
            }
        }
        _searchOrigin = null
        _restoringSearchOrigin = false
    }

    function runPendingSearch() {
        if (!searchPending)
            return
        searchPending = false
        if (typeof controller === "undefined" || !controller)
            return
        var text = pendingSearchText
        // Azonos szövegre nem keres újra (`0x0065b906`-`0x0065b988`). A
        // legutóbbi keresést a vezérlő nézetállapotából olvassuk, így a
        // kihagyás nem marad meg olyan nézetben, ahol a keresés már nem él
        // (mappaválasztás, szűrő): ott ugyanaz a szöveg újra keres.
        if (controller.searchActive && controller.searchQuery === text.trim())
            return
        controller.search(text)
    }
    searchSuggestionsVisible: hostRefs.searchSuggestionsBox.visible
    onSearchSuggestionKeyPressed: function(key) {
        if (key === Qt.Key_Down)
            hostRefs.searchSuggestionsBox.moveSelection(1)
        else if (key === Qt.Key_Up)
            hostRefs.searchSuggestionsBox.moveSelection(-1)
        else if (key === Qt.Key_Return || key === Qt.Key_Enter)
            hostRefs.searchSuggestionsBox.chooseSelected()
        else if (key === Qt.Key_Escape)
            hostRefs.searchSuggestionsBox.dismiss()
    }
    onSearchEdited: function(text) {
        if (text.trim().length > 0)
            toolbar.captureSearchOrigin()
        hostWindow.clearSelection()
        pendingSearchText = text
        searchPending = true
        Qt.callLater(runPendingSearch)
        hostRefs.suggestionsTimer.restart()
    }
    onSearchCleared: {
        searchPending = false
        pendingSearchText = ""
        toolbar.restoreSearchOrigin()
        if (hostRefs.suggestionsTimer)
            hostRefs.suggestionsTimer.stop()
        hostRefs.searchSuggestionsBox.suggestions = []
    }
    Connections {
        target: typeof controller !== "undefined" ? controller : null
        function onStatusChanged() {
            if (!toolbar._restoringSearchOrigin && !toolbar.searchPending
                    && controller && !controller.searchActive)
                toolbar._searchOrigin = null
        }
    }
    // #7206: az "Import" gomb a főablak Import paneljét nyitja meg.
    onImportRequested: hostRefs.importSourceDialog.openImportSourcePanel()
    // #5812: az eszköztár az Album Properties ablakot nyitja.
    // #5835: mappa nélküli nézetben a kijelölt vagy fókuszban levő kép
    // mappáját adja át; a többi albumút külön él.
    onNewAlbumRequested:
        hostRefs.fileOpsDialogs.ensure().openNewAlbumProperties(
            hostWindow.newAlbumFolderPath())
    // #1421: az eszköztár `timelinebutton`-ja UGYANAZT a váltást
    // végzi, mint a Nézet ▸ Időrend és a Ctrl+5.
    // #1421: a nézetváltó pár UGYANAZT a vezérlőt hívja, mint a
    // Nézet ▸ Mappanézet almenü (#1454) - egy állapot, két felület.
    //: #1956: KÉT őr kell, mert KÉT külön hiba fenyeget:
    //:   `typeof …`  - a NÉV nincs regisztrálva (pl. szűkített
    //:                 teszt-összeállítás) ⇒ ReferenceError;
    //:   `&& x`      - a név megvan, de az ÉRTÉKE `null` az engine
    //:                 fel-/leépítése közben ⇒ TypeError. A `typeof`
    //:                 EZT NEM fogja: `typeof null === "object"`.
    //: A korábbi alak csak az elsőt fogta, ezért volt tele minden
    //: QML-futás „Cannot read property 'treeView' of null"-lal.
    treeViewActive: (typeof folderHierarchyController !== "undefined"
                     && folderHierarchyController)
                    ? (folderHierarchyController.treeView === true)
                    : false
    onFlatViewRequested: if (typeof folderHierarchyController !== "undefined"
                             && folderHierarchyController)
                             folderHierarchyController.setTreeView(false)
    onTreeViewRequested: if (typeof folderHierarchyController !== "undefined"
                             && folderHierarchyController)
                             folderHierarchyController.setTreeView(true)
    //: #1421: a ▾ gomb a menüsor MEGLÉVŐ Mappanézet-almenüjét nyitja -
    //: nincs második menüdefiníció (a tételek pipái így sem tudnak
    //: szétcsúszni a két belépési pont között).
    onFolderViewMenuRequested: function (anchorItem) {
        hostRefs.picasaMenuBar.openFolderViewMenu(anchorItem)
    }
}
