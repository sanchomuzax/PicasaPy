import QtQuick
import QtQuick.Controls

// A mappa-kontextusmenü — a Picasa `Folder` menüosztálya, 15 tétellel
// (#320 kezdte 2 tétellel, #422 tölti fel a teljes listára).
//
// A tételsort, a csoportbontást és a hivatalos magyar feliratokat a
// `docs/specs/ui-audit-context-menus.md` 1. szakasza rögzíti. A felmérés
// legfontosabb megállapítása: ez a menü HÁROM helyről nyílik, bájtra
// azonos tartalommal — a rács üres területéről, a bal panel mappa-sorából
// és a rács tetején ülő mappa-fejlécből. Ezért EGY komponens van, három
// hívóval (FolderPane.qml, LightboxFeed.qml, LightboxHeader.qml).
//
// Ami az eredetiben NINCS ebben a menüben, az innen KIKERÜLT: a „Mappa
// dátumának beállítása…" az `album.fen` („Mappaleírás szerkesztése…")
// dialógusba költözött, ahol a Picasában is lakik — ld.
// FolderPropertiesDialog.qml.
//
// A még be nem kötött parancsok `PicasaMenuItem { placeholder: true }`-ként
// szürkén LÁTSZANAK (#416, illetve a spec 5.1. szabálya: az inaktív tétel
// is tétel, hogy a menü magassága és a tételek helye állandó maradjon).
//
// Önálló, signal-alapú komponens: a controller-kötést a FolderPane.qml
// végzi (nem forró fájl).
Menu {
    id: menu
    objectName: "folderContextMenu"

    // a jobbklikkelt mappa útvonala — a hívó állítja be popup() előtt
    property string folderPath: ""
    // a felhasználó egyéni gyűjteményei: {name, folders} elemek listája
    property var customCollections: []
    // a rács jelenlegi rendezése (date/name/size/changed) és iránya — a
    // „Mappa rendezésének alapja ▸" almenü pipáihoz
    property string sortMode: "date"
    property bool sortReverse: false
    // #422: rejtett-e a jobbklikkelt mappa. A spec A.2 kimondja, hogy a
    // `Folder::ID_HIDEENTIREALBUM` „Mappa elrejtése" és a
    // `Folder::ID_UNHIDEENTIREALBUM` „Mappa megjelenítése" NEM két külön
    // tétel, hanem UGYANANNAK a sornak a két állapota — pontosan úgy, ahogy
    // a kép-szintű Elrejtés ↔ Megjelenítés már működik (PhotoContextMenu,
    // ViewerContextMenu).
    //
    // A mappa-szintű rejtés mögött nálunk MÉG NINCS réteg: az indexben csak
    // a képnek van `hidden` oszlopa, a mappának nincs. Ezért a tétel
    // helyfoglaló marad, és ez a tulajdonság az a varrat, amit a rejtett-
    // mappa réteg elkészültekor a hívó feltölt — a felirat-váltás magától
    // helyes lesz.
    property bool folderHidden: false

    signal editDescriptionRequested()
    signal selectAllRequested()
    signal clearSelectionRequested()
    signal invertSelectionRequested()
    signal moveToCollectionRequested(string collectionName)
    signal newCollectionRequested()
    signal refreshThumbnailsRequested()
    signal sortModeRequested(string mode)
    signal sortReverseRequested()
    signal locateRequested()
    signal removeFromPicasaRequested()
    signal moveFolderRequested()
    signal exportAsHtmlRequested()

    // -- 1. blokk: mappaleírás ---------------------------------------------

    MenuItem {
        objectName: "folderMenuEditDescription"
        text: qsTr("Edit Folder Description...")
        onTriggered: menu.editDescriptionRequested()
    }
    MenuSeparator {}

    // -- 2. blokk: kijelölés + gyűjtemény ----------------------------------

    MenuItem {
        objectName: "folderMenuSelectAll"
        text: qsTr("Select All Pictures") + "\tCtrl+A"
        onTriggered: menu.selectAllRequested()
    }
    MenuItem {
        objectName: "folderMenuClearSelection"
        text: qsTr("Clear Selection") + "\tCtrl+D"
        onTriggered: menu.clearSelectionRequested()
    }
    MenuItem {
        objectName: "folderMenuInvertSelection"
        text: qsTr("Invert Selection") + "\tCtrl+I"
        onTriggered: menu.invertSelectionRequested()
    }
    Menu {
        objectName: "folderContextMenuMoveToCollection"
        title: qsTr("Move to Collection...")

        Repeater {
            objectName: "folderContextMenuMoveToCollectionRepeater"
            model: menu.customCollections
            delegate: MenuItem {
                required property var modelData
                objectName: "folderContextMenuMoveToCollectionItem_" + modelData.name
                text: modelData.name
                onTriggered: menu.moveToCollectionRequested(modelData.name)
            }
        }
        MenuSeparator { visible: menu.customCollections.length > 0 }
        MenuItem {
            objectName: "folderContextMenuNewCollection"
            text: qsTr("New Collection...")
            onTriggered: menu.newCollectionRequested()
        }
    }
    MenuSeparator {}

    // -- 3. blokk: nézet ----------------------------------------------------

    MenuItem {
        objectName: "folderMenuRefreshThumbnails"
        text: qsTr("Refresh Thumbnails")
        onTriggered: menu.refreshThumbnailsRequested()
    }
    Menu {
        objectName: "folderMenuSortBy"
        // az eredeti `Sort` menüosztálya: Dátum · Név · Méret · Fordított
        // sorrend (spec A.2)
        title: qsTr("Sort Folder By")

        MenuItem {
            objectName: "folderMenuSortByDate"
            text: qsTr("Date")
            checkable: true
            checked: menu.sortMode === "date"
            onTriggered: menu.sortModeRequested("date")
        }
        MenuItem {
            objectName: "folderMenuSortByName"
            text: qsTr("Name")
            checkable: true
            checked: menu.sortMode === "name"
            onTriggered: menu.sortModeRequested("name")
        }
        MenuItem {
            objectName: "folderMenuSortBySize"
            text: qsTr("Size")
            checkable: true
            checked: menu.sortMode === "size"
            onTriggered: menu.sortModeRequested("size")
        }
        MenuSeparator {}
        MenuItem {
            objectName: "folderMenuSortReverse"
            text: qsTr("Reverse Order")
            checkable: true
            checked: menu.sortReverse
            onTriggered: menu.sortReverseRequested()
        }
    }
    MenuSeparator {}

    // -- 4. blokk: rejtés ----------------------------------------------------

    PicasaMenuItem {
        objectName: "folderMenuHideFolder"
        // állapotfüggő felirat-váltás UGYANAZON a helyen (spec A.2) — nem
        // külön tétel, ezért nincs `folderMenuUnhideFolder`
        text: menu.folderHidden ? qsTr("Unhide Folder") : qsTr("Hide Folder")
        placeholder: true
    }
    MenuSeparator {}

    // -- 5. blokk: lemez ------------------------------------------------------

    MenuItem {
        objectName: "folderMenuLocate"
        text: qsTr("Locate on Disk") + "\tCtrl+Enter"
        onTriggered: menu.locateRequested()
    }
    MenuItem {
        objectName: "folderMenuRemoveFromPicasa"
        text: qsTr("Remove from Picasa...")
        onTriggered: menu.removeFromPicasaRequested()
    }
    MenuSeparator {}

    // -- 6. blokk: áthelyezés / törlés ----------------------------------------

    // #457: az eredeti `Folder::ID_MOVEFOLDER` — a mappa a
    // KÍSÉRŐFÁJLOKKAL (`.picasa.ini`) együtt költözik, különben a képek
    // elveszítenék a feliratukat és a címkéiket
    MenuItem {
        objectName: "folderMenuMoveFolder"
        text: qsTr("Move Folder...")
        onTriggered: menu.moveFolderRequested()
    }
    PicasaMenuItem {
        objectName: "folderMenuDeleteFolder"
        text: qsTr("Delete Folder...")
        placeholder: true
    }
    MenuSeparator {}

    // -- 7. blokk: megosztás ---------------------------------------------------

    PicasaMenuItem {
        objectName: "folderMenuUploadToGooglePhotos"
        text: qsTr("Upload to Google Photos...")
        placeholder: false
        // #422: megszűnt szolgáltatás — véglegesen szürke, nem hátralévő munka
        retired: true
    }
    MenuSeparator {}

    // -- 8. blokk: export ------------------------------------------------------

    MenuItem {
        objectName: "folderMenuExportAsHtml"
        text: qsTr("Export as HTML Page...")
        onTriggered: menu.exportAsHtmlRequested()
    }
    PicasaMenuItem {
        objectName: "folderMenuAddNameTags"
        text: qsTr("Add Name Tags")
        placeholder: true
    }
}
