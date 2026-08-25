import QtQuick
import QtQuick.Controls

// A bal panel SAJÁT jobbklikk-menüje — a Picasa `AlbumList` menüosztálya,
// 12 tétellel (#422, 3. lépcső; a 12. a #757-ben került elő).
//
// Forrás: `docs/specs/ui-audit-context-menus.md` A.2 szakasza. Ez a menü a
// képernyőképeken nem szerepelt: a `Picasa3i18n.dll` string-táblájából
// derült ki, hogy létezik — nálunk eddig teljesen hiányzott.
//
// #757: a spec kétszer is „11 tétel"-t ír (A.1, A.4), a string-táblában
// viszont TIZENKÉT `AlbumList::` sor van — a `Shortcuts` kimaradt a
// számolásból. A feliratok azóta szó szerint (a `&`-mnemonikkal együtt) az
// eredetiek.
//
// A rendezés-tételek ugyanarra a rétegre kötnek, mint a mappa-menü
// „Mappa rendezésének alapja ▸" almenüje (`setFolderSort` /
// `toggleFolderSortReverse`) — a Picasa is egyetlen parancskészletet
// használ, a menük abból válogatnak.
//
// A személyek rendezése, az „indexképek megjelenítése a könyvtárban" és
// az „Asztal" gyorsugrás mögött még nincs réteg — szürkén látszanak
// (#416, spec 5.1.). Az egyszerűsített fanézet a #1454-ben élővé vált: a
// `FolderHierarchyController.simplified` kapcsolóját billenti.
//
// A Windows-specifikus Sajátgép/Dokumentumok/Képek tételek szándékosan
// kimaradnak: a felmérés szerint is csak Windowson léteznek, a PicasaPy
// pedig Linux-first.
//
// Önálló, signal-alapú komponens: a bekötést a FolderPane.qml végzi.
Menu {
    id: menu
    objectName: "folderListContextMenu"

    // a jelenlegi rendezés — a pipákhoz
    property string sortMode: "date"
    property bool sortReverse: false
    // #1454: az „Egyszerűsített fanézet" pipája — a bal hasáb
    // fa-vezérlőjének állapota, a gazda köti be
    property bool simplifiedTree: false

    signal sortModeRequested(string mode)
    signal sortReverseRequested()
    signal simplifiedTreeRequested()

    // -- 1. blokk: a mappalista rendezése ---------------------------------

    MenuItem {
        objectName: "folderListMenuSortByDate"
        text: qsTr("Sort by &Date")
        checkable: true
        checked: menu.sortMode === "date"
        onTriggered: menu.sortModeRequested("date")
    }
    MenuItem {
        objectName: "folderListMenuSortByName"
        text: qsTr("Sort by &Name")
        checkable: true
        checked: menu.sortMode === "name"
        onTriggered: menu.sortModeRequested("name")
    }
    MenuItem {
        objectName: "folderListMenuSortBySize"
        text: qsTr("Sort by &Size")
        checkable: true
        checked: menu.sortMode === "size"
        onTriggered: menu.sortModeRequested("size")
    }
    MenuItem {
        objectName: "folderListMenuSortByChanged"
        text: qsTr("Sort by &Recent Changes")
        checkable: true
        checked: menu.sortMode === "changed"
        onTriggered: menu.sortModeRequested("changed")
    }
    MenuItem {
        objectName: "folderListMenuSortReverse"
        text: qsTr("Re&verse sort")
        checkable: true
        checked: menu.sortReverse
        onTriggered: menu.sortReverseRequested()
    }
    MenuSeparator {}

    // -- 2. blokk: a személyek rendezése ------------------------------------

    PicasaMenuItem {
        objectName: "folderListMenuSortPeopleByName"
        text: qsTr("Sort &People by Name")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "folderListMenuSortPeopleByCount"
        text: qsTr("Sort People by &Amount")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "folderListMenuSortPeopleByTopList"
        text: qsTr("Sort People by Top &10")
        placeholder: true
    }
    MenuSeparator {}

    // -- 3. blokk: nézet-kapcsolók -------------------------------------------

    // #1454: a menüsáv `Nézet ▸ Mappanézet` harmadik tételének MÁSIK
    // belépési pontja (`AlbumList::ID_VIEW_WATCHED`) — ugyanaz a kapcsoló,
    // ezért ugyanaz a vezérlő. A korábbi `folderListMenuFlatView`
    // objectName félrevezető volt: nem a lapos nézet tétele ez.
    MenuItem {
        objectName: "folderListMenuSimplifiedTree"
        text: qsTr("&Simplified Tree View")
        checkable: true
        checked: menu.simplifiedTree
        onTriggered: {
            menu.simplifiedTreeRequested()
            // a kattintás imperatívan átbillenti a `checked`-et, mielőtt a
            // jelzés eldördülne — ha a gazda nem váltott állapotot (nincs
            // bekötve, vagy elutasította), a pipa hazudna. Visszakötjük.
            checked = Qt.binding(function () { return menu.simplifiedTree })
        }
    }
    PicasaMenuItem {
        objectName: "folderListMenuShowThumbnails"
        text: qsTr("Show &Thumbnails in Library")
        placeholder: true
    }
    MenuSeparator {}

    // -- 4. blokk: gyors gyökér-váltás ----------------------------------------

    // #757: az `AlbumList::Shortcuts` az eredetiben ALMENÜ CÍME, nem sor —
    // a kulcsnak nincs `ID_` előtagja (mint a `Folder::SortFolderBy`-nak és
    // az `Album::SortAlbumBy`-nak sem), a `ui-audit-mainwindow.md` 1.7 pedig
    // ki is mondja: „a `Shortcuts` almenüben `AlbumListWin::ID_VIEW_ALL` =
    // »My &Computer«". Alatta a gyökérváltók ültek: Asztal · Sajátgép ·
    // Dokumentumok · Képek — utóbbi három Windows-specifikus, ezért nálunk
    // kimarad, és egyedül az Asztal maradna benne.
    //
    // Amíg egyik gyökérváltó mögött sincs réteg, egy egytételes almenü csak
    // üres kattintást adna, ezért mindkettő lapos, helyfoglaló sor — a
    // felirat és a HELY viszont már az eredeti. A magyar felirata a Picasa
    // saját fordítása: „Gyorsbillentyűk".
    PicasaMenuItem {
        objectName: "folderListMenuShortcuts"
        text: qsTr("&Shortcuts")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "folderListMenuDesktop"
        text: qsTr("&Desktop")
        placeholder: true
    }
}
