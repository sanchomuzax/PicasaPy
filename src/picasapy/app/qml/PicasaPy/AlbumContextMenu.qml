import QtQuick
import QtQuick.Controls

// Az album jobbklikk-menüje — a Picasa `Album` menüosztálya (#422,
// 4. lépcső). Ez a mappa-menü album-változata: ugyanaz a szerep, más
// parancsokkal.
//
// A TELJESSÉG kérdése MEGOLDVA (#422, a tételsor végigvezetése). A
// `docs/specs/ui-audit-context-menus.md` A.2 szakasza 13 tételt említ, de
// a felsorolásában csak 11 nevesített felirat van — ez korábban úgy
// látszott, mintha két tétel hiányozna. A `Picasa3i18n.dll` string-táblája
// feloldja az ellentmondást: a 13-ból NÉGY feltöltés-azonosító
// (`ID_UPLOAD_ALBUM_TO_GOOGLE_PLUS_PHOTOS`, `ID_UPLOAD_ALBUM_TO_LIGHTHOUSE`,
// `ID_UPLOAD_TO_GOOGLE_PLUS_PHOTOS`, `ID_UPLOAD_TO_LIGHTHOUSE`), és ezek
// összesen KÉT különböző feliratot adnak: „Feltöltés a Google Fotókba…" és
// „Feltöltés a Picasa Webalbumokba…". Vagyis 11 KÜLÖNBÖZŐ felirat van, és
// a menü most mind a 11-et tartalmazza — kitalált tétel nélkül.
//
// #757: a tizenkettedik felirat mégis előkerült — az `Album::SortAlbumBy`
// („Album rendezésének alapja…"), amit a #422-es végigvezetés az `ID_`
// előtag hiánya miatt nem vett be a sorba. A feliratok azóta szó szerint (a
// `&`-mnemonikkal együtt) az eredetiek.
//
// A még be nem kötött parancsok `PicasaMenuItem { placeholder: true }`-ként
// szürkén LÁTSZANAK (#416, spec 5.1.). Az album törlése (#4598), a
// leírás szerkesztése (#3173) és a Névcímkék hozzáadása (#4535 — az adott
// album tagképein indít keresést) már valódi művelet. A webes műveletek
// nálunk nem értelmezhetők.
//
// Önálló, signal-alapú komponens: a bekötést a FolderPane.qml végzi.
PicasaMenu {
    id: menu
    objectName: "albumContextMenu"

    // a jobbklikkelt album azonosítója — a hívó állítja be popup() előtt
    property string albumToken: ""
    property string albumName: ""

    //: #3173: az album tulajdonságai (név, dátum, helyszín, leírás)
    signal editDescriptionRequested()
    signal deleteAlbumRequested()

    signal selectAllRequested()
    signal clearSelectionRequested()
    signal invertSelectionRequested()
    signal refreshThumbnailsRequested()
    signal exportAsHtmlRequested()
    signal addNameTagsRequested(string albumToken)
    //: #4599: az album egyszeri átrendezése — `mode`: date | name | size |
    //: reverse. A Shift (csökkenő sorrend) állapotát a vezérlő olvassa a
    //: kiválasztás pillanatában (a QML-nek nincs rá API-ja).
    signal sortAlbumRequested(string mode)

    // -- 1. blokk: album-műveletek ----------------------------------------

    MenuItem {
        objectName: "albumMenuDelete"
        text: qsTr("&Delete Album")
        onTriggered: menu.deleteAlbumRequested()
    }
    MenuItem {
        //: #3173: valódi tétel — az album tulajdonságai (`album.fen`)
        objectName: "albumMenuEditDescription"
        text: qsTr("&Edit Album Description...")
        onTriggered: menu.editDescriptionRequested()
    }
    PicasaMenuItem {
        objectName: "albumMenuAddNameTags"
        text: qsTr("&Add name tags")
        placeholder: false
        onTriggered: menu.addNameTagsRequested(menu.albumToken)
    }
    MenuSeparator {}

    // -- 2. blokk: kijelölés ------------------------------------------------

    MenuItem {
        objectName: "albumMenuSelectAll"
        text: qsTr("Select &All Pictures") + "\tCtrl+A"
        onTriggered: menu.selectAllRequested()
    }
    MenuItem {
        objectName: "albumMenuClearSelection"
        text: qsTr("&Clear Selection") + "\tCtrl+D"
        onTriggered: menu.clearSelectionRequested()
    }
    MenuItem {
        objectName: "albumMenuInvertSelection"
        text: qsTr("&Invert Selection") + "\tCtrl+I"
        onTriggered: menu.invertSelectionRequested()
    }
    MenuSeparator {}

    // -- 3. blokk: nézet -----------------------------------------------------

    MenuItem {
        objectName: "albumMenuRefreshThumbnails"
        text: qsTr("&Refresh Thumbnails")
        onTriggered: menu.refreshThumbnailsRequested()
    }
    // #757, #4599: az `Album::SortAlbumBy` — az eredetiben a mappa-menü
    // almenüjének (`Sort::`) album-párja, UGYANAZZAL a négy tétellel
    // (`0x007318a0`): Dátum · Név · Méret · Fordított sorrend. Egyszeri
    // átrendezés, nem tartós nézetmód (ezért nincs pipa): a kezelő a tárolt
    // sorrendet írja át (`PhotoOpsController.sortAlbum`, ADR-016). A Shift a
    // három kulcsnál csökkenővé teszi (a "Fordított" Shift nélkül és Shifttel
    // is megfordít). A tételek az eredeti funkciót adják, ezért NEM kapnak
    // kék saját-funkció jelölést — csak a tárolás helye saját (`ini/album_order.py`).
    PicasaMenu {
        objectName: "albumMenuSortAlbumBy"
        title: qsTr("Sort &Album By")

        MenuItem {
            objectName: "albumMenuSortByDate"
            text: qsTr("&Date")
            onTriggered: menu.sortAlbumRequested("date")
        }
        MenuItem {
            objectName: "albumMenuSortByName"
            text: qsTr("&Name")
            onTriggered: menu.sortAlbumRequested("name")
        }
        MenuItem {
            objectName: "albumMenuSortBySize"
            text: qsTr("&Size")
            onTriggered: menu.sortAlbumRequested("size")
        }
        MenuItem {
            objectName: "albumMenuSortReverse"
            text: qsTr("&Reverse order")
            onTriggered: menu.sortAlbumRequested("reverse")
        }
    }
    MenuSeparator {}

    // -- 4. blokk: megosztás / export -----------------------------------------

    PicasaMenuItem {
        objectName: "albumMenuOnlineActions"
        text: qsTr("Online Actions")
        placeholder: false
        // #422: megszűnt szolgáltatás — véglegesen szürke, nem hátralévő munka
        retired: true
    }
    PicasaMenuItem {
        objectName: "albumMenuUploadToGooglePhotos"
        text: qsTr("Upload to Google &Photos...")
        placeholder: false
        // #422: megszűnt szolgáltatás — véglegesen szürke, nem hátralévő munka
        retired: true
    }
    // `Album::ID_UPLOAD_TO_LIGHTHOUSE` — a Picasa félbehagyott átnevezése
    // miatt a régi felirat is ott maradt a menüben (spec 5.6.: a mappa-menü
    // már „Google Fotók", ez még „Picasa Webalbumok"). Ugyanúgy megszűnt
    // szolgáltatás, tehát véglegesen szürke.
    PicasaMenuItem {
        objectName: "albumMenuUploadToWebAlbums"
        text: qsTr("Upload to &Picasa Web Albums...")
        placeholder: false
        retired: true
    }
    MenuItem {
        objectName: "albumMenuExportAsHtml"
        text: qsTr("E&xport as HTML Page...")
        onTriggered: menu.exportAsHtmlRequested()
    }
}
