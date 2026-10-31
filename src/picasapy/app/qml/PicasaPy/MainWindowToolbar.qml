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
        hostWindow.clearSelection()
        if (typeof controller !== "undefined" && controller)
            controller.search(text)
        hostRefs.suggestionsTimer.restart()
    }
    onSearchCleared: {
        hostWindow.clearSelection()
        if (typeof controller !== "undefined" && controller)
            controller.search("")
        hostRefs.searchSuggestionsBox.suggestions = []
    }
    // #23: az "Import" gomb az Import forrásból ablakot nyitja
    onImportRequested: hostRefs.importSourceDialog.open()
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
