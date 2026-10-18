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
// is tétel, hogy a menü magassága és a tételek helye állandó maradjon). A
// Névcímkék hozzáadása (#4535) a kiválasztott mappa képeire indít keresést.
//
// Önálló, signal-alapú komponens: a controller-kötést a FolderPane.qml
// végzi (nem forró fájl).
PicasaMenu {
    id: menu
    objectName: "folderContextMenu"

    //: #3470: a befoglaló menü a `Repeater`-delegáltaknak. A delegáltban a
    //: `menu` név NEM ezt jelenti: ott a `MenuItem` saját `menu`
    //: tulajdonsága nyer (a beágyazott almenü), mert a delegált külön
    //: komponens-kontextus, és a hatókör-objektum tulajdonsága megelőzi a
    //: külső `id`-t. A delegált ezért ezen a néven hív.
    readonly property var helyiMenu: menu

    // a jobbklikkelt mappa útvonala — a hívó állítja be popup() előtt
    property string folderPath: ""
    // a felhasználó egyéni gyűjteményei: {name, folders} elemek listája
    property var customCollections: []
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

    //: #1637 — a mappa elrejtése/megjelenítése
    signal hideFolderRequested(string path)
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
    //: #1638: a mappa a LOMTÁRBA, a tartalmával együtt — nem véglegesen
    signal deleteFolderRequested()
    signal exportAsHtmlRequested()
    signal addNameTagsRequested(string folderPath)

    // -- 1. blokk: mappaleírás ---------------------------------------------

    MenuItem {
        objectName: "folderMenuEditDescription"
        text: qsTr("&Edit Folder Description...")
        onTriggered: menu.editDescriptionRequested()
    }
    MenuSeparator {}

    // -- 2. blokk: kijelölés + gyűjtemény ----------------------------------

    MenuItem {
        objectName: "folderMenuSelectAll"
        text: qsTr("Select &All Pictures") + "\tCtrl+A"
        onTriggered: menu.selectAllRequested()
    }
    MenuItem {
        objectName: "folderMenuClearSelection"
        text: qsTr("&Clear Selection") + "\tCtrl+D"
        onTriggered: menu.clearSelectionRequested()
    }
    MenuItem {
        objectName: "folderMenuInvertSelection"
        text: qsTr("&Invert Selection") + "\tCtrl+I"
        onTriggered: menu.invertSelectionRequested()
    }
    PicasaMenu {
        objectName: "folderContextMenuMoveToCollection"
        title: qsTr("Mo&ve to Collection")

        Repeater {
            objectName: "folderContextMenuMoveToCollectionRepeater"
            model: menu.customCollections
            delegate: MenuItem {
                required property var modelData
                objectName: "folderContextMenuMoveToCollectionItem_" + modelData.name
                text: modelData.name
                onTriggered: helyiMenu.moveToCollectionRequested(modelData.name)
            }
        }
        MenuSeparator {
            visible: menu.customCollections.length > 0
            height: visible ? implicitHeight : 0
        }
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
        text: qsTr("Refresh &Thumbnails")
        onTriggered: menu.refreshThumbnailsRequested()
    }
    PicasaMenu {
        objectName: "folderMenuSortBy"
        // az eredeti `Sort` menüosztálya: Dátum · Név · Méret · Fordított
        // sorrend (spec A.2)
        title: qsTr("S&ort Folder By")

        // #4890: ezek egyszeri parancsok. A rendezett lista marad meg,
        // ezért nincs aktív mód vagy kijelölt menütétel.
        MenuItem {
            objectName: "folderMenuSortByDate"
            text: qsTr("&Date")
            checkable: false
            onTriggered: menu.sortModeRequested("date")
        }
        MenuItem {
            objectName: "folderMenuSortByName"
            text: qsTr("&Name")
            checkable: false
            onTriggered: menu.sortModeRequested("name")
        }
        MenuItem {
            objectName: "folderMenuSortBySize"
            text: qsTr("&Size")
            checkable: false
            onTriggered: menu.sortModeRequested("size")
        }
        //: #467: a NEGYEDIK szempont — az eredeti rendezés-motorja ismerte
        //: („Rendezés szín alapján", `CSelectionNode` → `SortColor`), de a
        //: menübe sosem került be. Nálunk a #383 átlagszín-indexéből
        //: azonnal megvan.
        MenuItem {
            objectName: "folderMenuSortByColor"
            text: qsTr("&Color")
            checkable: false
            onTriggered: menu.sortModeRequested("color")
        }
        //: #1721 (ADR-014): az ÖTÖDIK szempont — a KÉZI sorrend. A rácson
        //: húzással átrendezett képek sorrendje; a mappa `.picasa.ini`-je
        //: hordozza (`priority=`). Az eredeti a manuális sorrendet a
        //: `db3`-ban tartja, a menüjében „Rendezés prioritás szerint"
        //: néven — a tárolás nálunk más, a szempont ugyanaz.
        MenuItem {
            objectName: "folderMenuSortByPriority"
            text: qsTr("&Manual order")
            checkable: false
            onTriggered: menu.sortModeRequested("priority")
        }
        MenuSeparator {}
        MenuItem {
            objectName: "folderMenuSortReverse"
            text: qsTr("&Reverse order")
            checkable: false
            onTriggered: menu.sortReverseRequested()
        }
    }
    MenuSeparator {}

    // -- 4. blokk: rejtés ----------------------------------------------------

    // #1637: ÉLŐ tétel — a tétel eddig `placeholder: true` volt, tehát
    // látszott, kattintható volt, és NEM CSINÁLT SEMMIT.
    MenuItem {
        objectName: "folderMenuHideFolder"
        // állapotfüggő felirat-váltás UGYANAZON a helyen (spec A.2) — nem
        // külön tétel, ezért nincs `folderMenuUnhideFolder`
        text: menu.folderHidden ? qsTr("&Unhide Folder") : qsTr("&Hide Folder")
        enabled: menu.folderPath.length > 0
        onTriggered: menu.hideFolderRequested(menu.folderPath)
    }
    MenuSeparator {}

    // -- 5. blokk: lemez ------------------------------------------------------

    MenuItem {
        objectName: "folderMenuLocate"
        text: qsTr("&Locate on Disk") + "\tCtrl+Enter"
        onTriggered: menu.locateRequested()
    }
    MenuItem {
        objectName: "folderMenuRemoveFromPicasa"
        text: qsTr("&Remove from PicasaPy...")
        onTriggered: menu.removeFromPicasaRequested()
    }
    MenuSeparator {}

    // -- 6. blokk: áthelyezés / törlés ----------------------------------------

    // #457: az eredeti `Folder::ID_MOVEFOLDER` — a mappa a
    // KÍSÉRŐFÁJLOKKAL (`.picasa.ini`) együtt költözik, különben a képek
    // elveszítenék a feliratukat és a címkéiket
    MenuItem {
        objectName: "folderMenuMoveFolder"
        text: qsTr("&Move Folder...")
        onTriggered: menu.moveFolderRequested()
    }
    MenuItem {
        objectName: "folderMenuDeleteFolder"
        text: qsTr("&Delete Folder...")
        // #1638: a mappa-menü három „nagy" parancsa közül ez volt az
        // egyetlen néma — épp a visszafordíthatatlan. A művelet a
        // LOMTÁRBA tesz (az eredeti megerősítő szövege mondja ki), tehát
        // visszaállítható.
        onTriggered: menu.deleteFolderRequested()
    }
    MenuSeparator {}

    // -- 7. blokk: megosztás ---------------------------------------------------

    PicasaMenuItem {
        objectName: "folderMenuUploadToGooglePhotos"
        text: qsTr("Upload to Google &Photos...")
        placeholder: false
        // #422: megszűnt szolgáltatás — véglegesen szürke, nem hátralévő munka
        retired: true
    }
    MenuSeparator {}

    // -- 8. blokk: export ------------------------------------------------------

    MenuItem {
        objectName: "folderMenuExportAsHtml"
        text: qsTr("E&xport as HTML Page...")
        onTriggered: menu.exportAsHtmlRequested()
    }
    PicasaMenuItem {
        objectName: "folderMenuAddNameTags"
        text: qsTr("&Add name tags")
        placeholder: false
        onTriggered: menu.addNameTagsRequested(menu.folderPath)
    }
}
