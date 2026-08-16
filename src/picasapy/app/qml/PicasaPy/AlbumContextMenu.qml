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
// szürkén LÁTSZANAK (#416, spec 5.1.). Az album törlése/leírása mögött
// nincs réteg (a `photo_ops_controller` csak létrehozni és tagságot írni
// tud), a webes műveletek pedig nálunk nem értelmezhetők.
//
// Önálló, signal-alapú komponens: a bekötést a FolderPane.qml végzi.
Menu {
    id: menu
    objectName: "albumContextMenu"

    // a jobbklikkelt album azonosítója — a hívó állítja be popup() előtt
    property string albumToken: ""
    property string albumName: ""

    signal selectAllRequested()
    signal clearSelectionRequested()
    signal invertSelectionRequested()
    signal refreshThumbnailsRequested()
    signal exportAsHtmlRequested()

    // -- 1. blokk: album-műveletek ----------------------------------------

    PicasaMenuItem {
        objectName: "albumMenuDelete"
        text: qsTr("&Delete Album")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "albumMenuEditDescription"
        text: qsTr("&Edit Album Description...")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "albumMenuAddNameTags"
        text: qsTr("&Add name tags")
        placeholder: true
    }
    MenuSeparator {}

    // -- 2. blokk: kijelölés ------------------------------------------------

    MenuItem {
        objectName: "albumMenuSelectAll"
        text: qsTr("Select &All Pictures")
        onTriggered: menu.selectAllRequested()
    }
    MenuItem {
        objectName: "albumMenuClearSelection"
        text: qsTr("&Clear Selection")
        onTriggered: menu.clearSelectionRequested()
    }
    MenuItem {
        objectName: "albumMenuInvertSelection"
        text: qsTr("&Invert Selection")
        onTriggered: menu.invertSelectionRequested()
    }
    MenuSeparator {}

    // -- 3. blokk: nézet -----------------------------------------------------

    MenuItem {
        objectName: "albumMenuRefreshThumbnails"
        text: qsTr("&Refresh Thumbnails")
        onTriggered: menu.refreshThumbnailsRequested()
    }
    // #757: az `Album::SortAlbumBy` a mappa-menü „Mappa rendezésének
    // alapja ▸" almenüjének album-párja. Az `ID_` előtag hiánya itt is
    // almenü-CÍMRE utal (a `Folder::SortFolderBy` nálunk is almenü), de az
    // album-rendezés mögött MÉG NINCS réteg: a `setFolderSort` a MAPPÁK
    // sorrendjét állítja, albumra a vezérlőnek nincs megfelelője. Ezért
    // egyelőre helyfoglaló sor — a réteg elkészültekor almenüvé nyílik,
    // ugyanazzal a négy `Sort::` tétellel, mint a mappa-menüé.
    PicasaMenuItem {
        objectName: "albumMenuSortAlbumBy"
        text: qsTr("Sort &Album By")
        placeholder: true
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
