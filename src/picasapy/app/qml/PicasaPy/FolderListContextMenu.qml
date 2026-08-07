import QtQuick
import QtQuick.Controls

// A bal panel SAJÁT jobbklikk-menüje — a Picasa `AlbumList` menüosztálya,
// 11 tétellel (#422, 3. lépcső).
//
// Forrás: `docs/specs/ui-audit-context-menus.md` A.2 szakasza. Ez a menü a
// képernyőképeken nem szerepelt: a `Picasa3i18n.dll` string-táblájából
// derült ki, hogy létezik — nálunk eddig teljesen hiányzott.
//
// A rendezés-tételek ugyanarra a rétegre kötnek, mint a mappa-menü
// „Mappa rendezésének alapja ▸" almenüje (`setFolderSort` /
// `toggleFolderSortReverse`) — a Picasa is egyetlen parancskészletet
// használ, a menük abból válogatnak.
//
// A személyek rendezése, az egyszerűsített fanézet, az „indexképek
// megjelenítése a könyvtárban" és az „Asztal" gyorsugrás mögött még nincs
// réteg — szürkén látszanak (#416, spec 5.1.). A Windows-specifikus
// Sajátgép/Dokumentumok/Képek tételek szándékosan kimaradnak: a felmérés
// szerint is csak Windowson léteznek, a PicasaPy pedig Linux-first.
//
// Önálló, signal-alapú komponens: a bekötést a FolderPane.qml végzi.
Menu {
    id: menu
    objectName: "folderListContextMenu"

    // a jelenlegi rendezés — a pipákhoz
    property string sortMode: "date"
    property bool sortReverse: false

    signal sortModeRequested(string mode)
    signal sortReverseRequested()

    // -- 1. blokk: a mappalista rendezése ---------------------------------

    MenuItem {
        objectName: "folderListMenuSortByDate"
        text: qsTr("Sort by Date")
        checkable: true
        checked: menu.sortMode === "date"
        onTriggered: menu.sortModeRequested("date")
    }
    MenuItem {
        objectName: "folderListMenuSortByName"
        text: qsTr("Sort by Name")
        checkable: true
        checked: menu.sortMode === "name"
        onTriggered: menu.sortModeRequested("name")
    }
    MenuItem {
        objectName: "folderListMenuSortBySize"
        text: qsTr("Sort by Size")
        checkable: true
        checked: menu.sortMode === "size"
        onTriggered: menu.sortModeRequested("size")
    }
    MenuItem {
        objectName: "folderListMenuSortByChanged"
        text: qsTr("Sort by Most Recent Changes")
        checkable: true
        checked: menu.sortMode === "changed"
        onTriggered: menu.sortModeRequested("changed")
    }
    MenuItem {
        objectName: "folderListMenuSortReverse"
        text: qsTr("Reverse Sort Order")
        checkable: true
        checked: menu.sortReverse
        onTriggered: menu.sortReverseRequested()
    }
    MenuSeparator {}

    // -- 2. blokk: a személyek rendezése ------------------------------------

    PicasaMenuItem {
        objectName: "folderListMenuSortPeopleByName"
        text: qsTr("Sort People by Name")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "folderListMenuSortPeopleByCount"
        text: qsTr("Sort People by Count")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "folderListMenuSortPeopleByTopList"
        text: qsTr("Sort People by Top List")
        placeholder: true
    }
    MenuSeparator {}

    // -- 3. blokk: nézet-kapcsolók -------------------------------------------

    PicasaMenuItem {
        objectName: "folderListMenuFlatView"
        text: qsTr("Simplified Tree View")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "folderListMenuShowThumbnails"
        text: qsTr("Show Thumbnails in Library")
        placeholder: true
    }
    MenuSeparator {}

    // -- 4. blokk: gyors gyökér-váltás ----------------------------------------

    PicasaMenuItem {
        objectName: "folderListMenuDesktop"
        text: qsTr("Desktop")
        placeholder: true
    }
}
