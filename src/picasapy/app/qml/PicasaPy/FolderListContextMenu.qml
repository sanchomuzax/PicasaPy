import QtQuick
import QtQuick.Controls

// A bal panel SAJÁT jobbklikk-menüje - a Picasa `AlbumList` menüosztályának
// 14 rekordos nézet- és rendezésmenüje (#7340; #422, 3. lépcső).
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
// A személyek rendezése, a nézetkapcsolók és a gyors gyökérváltók a
// vezérlők meglévő állapotát használják. A Shortcuts sorrendje és tartalma
// megegyezik a menüsáv Nézet ▸ Mappanézet almenüjével; a Windowsos
// rendszermappáknak Linuxon a megfelelő helyi gyökerek felelnek meg.
//
// Önálló, signal-alapú komponens: a bekötést a FolderPane.qml végzi.
PicasaMenu {
    id: menu
    objectName: "folderListContextMenu"
    // A toolbar külön példányt tart fenn; a nevei ne ütközzenek a jobbklikk
    // menü azonos nevű tételeivel a teljes ablak objektumfájában.
    property string objectNamePrefix: ""

    // a jelenlegi rendezés — a pipákhoz
    property string sortMode: "date"
    property bool sortReverse: false
    // #1454: az „Egyszerűsített fanézet" pipája — a bal hasáb
    // fa-vezérlőjének állapota, a gazda köti be
    property bool simplifiedTree: false
    property bool albumThumbs: false
    property string viewRoot: ""
    property bool treeMode: false

    //: #1767 — a Személyek lista rendezési módja: name / count / top
    property string peopleSort: "name"

    signal peopleSortRequested(string mode)
    signal sortModeRequested(string mode)
    signal sortReverseRequested()
    signal simplifiedTreeRequested()
    signal albumThumbnailsRequested()
    signal viewRootRequested(string token)

    // -- 1. blokk: a mappalista rendezése ---------------------------------

    // #1468: a valódi kattintás előbb IMPERATÍVAN átbillenti a `checked`-et,
    // és csak utána dördül el a `triggered`. Kizáró csoportban a MÁR AKTÍV
    // tételre kattintva a vezérlő állapota nem változik, tehát a kötés magától
    // soha nem értékelődik újra — a menü újranyitásakor egyik tételen sem
    // állna pipa. Ezért a jelzés után azonnal VISSZAKÖTJÜK a `checked`-et
    // (a #1464-ben bevezetett minta).
    //
    // A `menu.sortMode` itt is PILLANATFELVÉTEL (a gazda a nyitáskor írja),
    // ezért az azonos értékű visszaírás nem élesztené fel a kötést.
    MenuItem {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "SortByDate" : "folderListMenuSortByDate"
        text: qsTr("Sort by &Date")
        checkable: true
        checked: menu.sortMode === "date"
        onTriggered: {
            menu.sortModeRequested("date")
            checked = Qt.binding(function () {
                return menu.sortMode === "date"
            })
        }
    }
    MenuItem {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "SortByChanged" : "folderListMenuSortByChanged"
        text: qsTr("Sort by &Recent Changes")
        checkable: true
        checked: menu.sortMode === "changed"
        onTriggered: {
            menu.sortModeRequested("changed")
            checked = Qt.binding(function () {
                return menu.sortMode === "changed"
            })
        }
    }
    MenuItem {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "SortBySize" : "folderListMenuSortBySize"
        text: qsTr("Sort by &Size")
        checkable: true
        checked: menu.sortMode === "size"
        onTriggered: {
            menu.sortModeRequested("size")
            checked = Qt.binding(function () {
                return menu.sortMode === "size"
            })
        }
    }
    MenuItem {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "SortByName" : "folderListMenuSortByName"
        text: qsTr("Sort by &Name")
        checkable: true
        checked: menu.sortMode === "name"
        onTriggered: {
            menu.sortModeRequested("name")
            checked = Qt.binding(function () {
                return menu.sortMode === "name"
            })
        }
    }
    MenuItem {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "SortReverse" : "folderListMenuSortReverse"
        text: qsTr("Re&verse sort")
        checkable: true
        checked: menu.sortReverse
        onTriggered: {
            menu.sortReverseRequested()
            // #2377: a `checkable` MenuItem kattintáskor MAGA billenti a
            // `checked`-et, és ez eldobja a fenti kötést. Ma azért nem
            // látszik, mert a művelet mindig átbillenti az állapotot —
            // ez szerencse, nem szerkezet (ld. #1471).
            checked = Qt.binding(function () {
                return menu.sortReverse
            })
        }
    }
    MenuSeparator {}

    // -- 2. blokk: a személyek rendezése ------------------------------------

    // #1767: ÉLŐ tételek — eddig mindhárom `placeholder: true` volt,
    // tehát látszottak, kattinthatók voltak, és nem csináltak semmit.
    //
    // ⚠️ RÁDIÓ-CSAPDA (#1464/#1468): a valódi kattintás előbb IMPERATÍVAN
    // átbillenti a `checked`-et, és a `setPeopleSort` azonos értéknél nem
    // változtat állapotot — a kötés tehát magától soha nem értékelődne
    // újra. Ezért minden tétel a jelzés után VISSZAKÖTI a `checked`-et.
    MenuItem {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "SortPeopleByName"
            : "folderListMenuSortPeopleByName"
        text: qsTr("Sort &People by Name")
        checkable: true
        checked: menu.peopleSort === "name"
        onTriggered: {
            menu.peopleSortRequested("name")
            checked = Qt.binding(function () {
                return menu.peopleSort === "name"
            })
        }
    }
    MenuItem {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "SortPeopleByCount"
            : "folderListMenuSortPeopleByCount"
        text: qsTr("Sort People by &Amount")
        checkable: true
        checked: menu.peopleSort === "count"
        onTriggered: {
            menu.peopleSortRequested("count")
            checked = Qt.binding(function () {
                return menu.peopleSort === "count"
            })
        }
    }
    MenuItem {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "SortPeopleByTopList"
            : "folderListMenuSortPeopleByTopList"
        text: qsTr("Sort People by Top &10")
        checkable: true
        enabled: menu.treeMode
        checked: menu.peopleSort === "top"
        onTriggered: {
            menu.peopleSortRequested("top")
            checked = Qt.binding(function () {
                return menu.peopleSort === "top"
            })
        }
    }
    MenuSeparator {}

    // -- 3. blokk: gyors gyökér-váltás ----------------------------------------

    // #757: az `AlbumList::Shortcuts` az eredetiben ALMENÜ CÍME, nem sor —
    // a kulcsnak nincs `ID_` előtagja. A gyökerek sorrendje és tartalma
    // megegyezik a menüsáv Mappanézet almenüjével; a Windowsos
    // rendszermappák Linuxon a megfelelő helyi gyökerekre oldódnak fel.
    PicasaMenu {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "Shortcuts" : "folderListMenuShortcuts"
        title: qsTr("&Shortcuts")
        MenuItem {
            objectName: menu.objectNamePrefix
                ? menu.objectNamePrefix + "Desktop" : "folderListMenuDesktop"
            text: qsTr("&Desktop")
            checkable: true
            checked: menu.viewRoot === "desktop"
            onTriggered: {
                menu.viewRootRequested("desktop")
                checked = Qt.binding(function () {
                    return menu.viewRoot === "desktop"
                })
            }
        }
        MenuItem {
            objectName: menu.objectNamePrefix
                ? menu.objectNamePrefix + "MyDocuments" : "folderListMenuMyDocuments"
            text: qsTr("My Do&cuments")
            checkable: true
            checked: menu.viewRoot === "mydocs"
            onTriggered: {
                menu.viewRootRequested("mydocs")
                checked = Qt.binding(function () {
                    return menu.viewRoot === "mydocs"
                })
            }
        }
        MenuItem {
            objectName: menu.objectNamePrefix
                ? menu.objectNamePrefix + "MyPictures" : "folderListMenuMyPictures"
            text: qsTr("My &Pictures")
            checkable: true
            checked: menu.viewRoot === "mypics"
            onTriggered: {
                menu.viewRootRequested("mypics")
                checked = Qt.binding(function () {
                    return menu.viewRoot === "mypics"
                })
            }
        }
        MenuSeparator {}
        MenuItem {
            objectName: menu.objectNamePrefix
                ? menu.objectNamePrefix + "MyComputer" : "folderListMenuMyComputer"
            text: qsTr("My &Computer")
            checkable: true
            checked: menu.viewRoot === "all"
            onTriggered: {
                menu.viewRootRequested("all")
                checked = Qt.binding(function () {
                    return menu.viewRoot === "all"
                })
            }
        }
    }
    MenuSeparator {}

    // -- 4. blokk: nézet-kapcsolók -------------------------------------------
    MenuItem {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "ShowThumbnails" : "folderListMenuShowThumbnails"
        text: qsTr("Show &Thumbnails in Library")
        checkable: true
        enabled: !menu.treeMode
        checked: menu.albumThumbs
        onTriggered: {
            menu.albumThumbnailsRequested()
            checked = Qt.binding(function () { return menu.albumThumbs })
        }
    }
    // #1454: a menüsáv `Nézet ▸ Mappanézet` harmadik tételének MÁSIK
    // belépési pontja (`AlbumList::ID_VIEW_WATCHED`) - ugyanaz a kapcsoló,
    // ezért ugyanaz a vezérlő.
    MenuItem {
        objectName: menu.objectNamePrefix
            ? menu.objectNamePrefix + "SimplifiedTree" : "folderListMenuSimplifiedTree"
        text: qsTr("&Simplified Tree View")
        checkable: true
        checked: menu.simplifiedTree
        onTriggered: {
            menu.simplifiedTreeRequested()
            checked = Qt.binding(function () { return menu.simplifiedTree })
        }
    }
}
