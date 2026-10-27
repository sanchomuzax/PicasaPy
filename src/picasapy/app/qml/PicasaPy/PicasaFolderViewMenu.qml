import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

PicasaMenu {
    id: folderViewMenu
    property var bar: null
    readonly property var controllerRef:
        (typeof controller !== "undefined" && controller)
            ? controller : null
    objectName: "menuViewFolderView"
    title: qsTr("&Folder View")
    // A vezérlő állapota EGY helyen — a tételek pipái ezt olvassák,
    // és a kattintás utáni visszakötés is erre hivatkozik.
    readonly property bool treeMode:
        (bar.folderViewCtl && bar.folderViewCtl.treeView !== undefined)
            ? bar.folderViewCtl.treeView : false
    readonly property bool simplifiedMode:
        (bar.folderViewCtl && bar.folderViewCtl.simplified !== undefined)
            ? bar.folderViewCtl.simplified : false
    //: #1407: a választott gyökér tokenje — a négy gyökér-tétel pipája
    //: ezt olvassa. A `!== undefined` a próbák stub-vezérlőjére véd
    //: (#1572, `scripts/qml_undefined_or.py`).
    readonly property string viewRootToken:
        (bar.folderViewCtl && bar.folderViewCtl.viewRoot !== undefined)
            ? bar.folderViewCtl.viewRoot : ""
    //: #2049: a mappa-borítók kapcsolójának állapota. A
    //: `!== undefined` a próbák stub-vezérlőjére véd (#1572).
    readonly property bool albumThumbsMode:
        (bar.folderViewCtl && bar.folderViewCtl.albumThumbs !== undefined)
            ? bar.folderViewCtl.albumThumbs : false
    //: #1766: a lista-rendezés állapota — ugyanaz a forrás, mint a
    //: bal hasáb helyi menüjéé, hogy a két menü pipája EGYÜTT
    //: mozogjon. A `!== undefined` a próbák stub-vezérlőjére véd
    //: (#1572, `scripts/qml_undefined_or.py`).
    readonly property string rendezes:
        (controllerRef && controllerRef.paneSort !== undefined)
            ? controllerRef.paneSort : ""
    readonly property bool rendezesForditott:
        (controllerRef && controllerRef.paneSortReverse !== undefined)
            ? controllerRef.paneSortReverse : false
    // #4528: az Emberek lista három rendezésének közös állapota.
    readonly property string peopleSort:
        (controllerRef && controllerRef.peopleSort !== undefined)
            ? controllerRef.peopleSort : "name"

    // MÉRT buktató (#1454): a valódi kattintás IMPERATÍVAN
    // átbillenti a `checked`-et, MIELŐTT a `triggered` eldördülne.
    // Ha a felhasználó a MÁR aktív tételre kattint, a vezérlő
    // állapota nem változik, a kötés tehát nem értékelődik újra —
    // és a menü újranyitásakor EGYIK tételen sem lenne pipa. Ezért
    // a jelzés után azonnal visszakötjük a `checked`-et.
    MenuItem {
        objectName: "menuViewFlatFolderView"
        text: qsTr("&Flat Folder View")
        checkable: true
        checked: !folderViewMenu.treeMode
        onTriggered: {
            if (bar.folderViewCtl) bar.folderViewCtl.setTreeView(false)
            checked = Qt.binding(function () {
                return !folderViewMenu.treeMode
            })
        }
    }
    MenuItem {
        objectName: "menuViewTreeView"
        text: qsTr("&Tree View")
        checkable: true
        checked: folderViewMenu.treeMode
        onTriggered: {
            if (bar.folderViewCtl) bar.folderViewCtl.setTreeView(true)
            checked = Qt.binding(function () {
                return folderViewMenu.treeMode
            })
        }
    }
    MenuSeparator {}
    // #1407: a NÉGY gyökér-tétel. Az eredetiben ezek a mappa-hasáb
    // HELYI menüjében vannak (`thumbui/folderviewpopup`,
    // `0x00733480`, spec 2.2) — nálunk a `folderviewpopup` gomb
    // UGYANEZT a menüt nyitja, ezért egy helyen élnek.
    //
    // ⚠️ A spec 4.5/b helyesbítése szerint csak a Sajátgép valódi
    // gyökér: a másik három ELŐBB a teljes fára vált, és csak utána
    // ugrik a mappára (`push "all"` mindhárom ágban). Rádiógomb-pipát
    // mégis mind a négy kap, mert a natív `[+0x2e0]`/`[+0x2f0]`
    // rekesz a rendszermappa-tokent tárolja.
    //
    // A pipa-visszakötés ugyanaz a MÉRT buktató, mint a fenti két
    // rádiótételnél (#1454): a valódi kattintás imperatívan
    // átbillenti a `checked`-et, MIELŐTT a `triggered` eldördülne.
    //: ⚠️ A négy tétel SZÁNDÉKOSAN ki van írva, nem `Repeater`: a
    //: `Menu` a `Repeater` delegáltjait nem veszi fel a tételei közé
    //: (ugyanaz a buktató, amit az `EditorTextPanel` igazítás-gombjai
    //: is kimondanak). Elsőre `Repeater`-rel írtam meg, és a próba
    //: mind a négy tételt „nem található"-nak látta.
    MenuItem {
        objectName: "menuViewRootMyComputer"
        text: qsTr("My &Computer")
        //: a KÉT valódi gyökér egyike: a teljes fa. Bekapcsolt
        //: „Egyszerűsített fanézet" mellett a vezérlő `watched`-et
        //: ad — az a kapcsoló FÜGGETLEN (spec 3.).
        checkable: true
        checked: folderViewMenu.viewRootToken === "all"
        onTriggered: {
            if (bar.folderViewCtl) bar.folderViewCtl.setViewRoot("all")
            checked = Qt.binding(function () {
                return folderViewMenu.viewRootToken === "all"
            })
        }
    }
    MenuItem {
        objectName: "menuViewRootMyPictures"
        text: qsTr("My &Pictures")
        //: `CSIDL_MYPICTURES` (0x27) → `QStandardPaths.PicturesLocation`.
        //: Feloldhatatlan mappánál a vezérlő a Dokumentumokra, majd a
        //: Sajátgép-gyökérre esik vissza (`0x00996747`, spec 4.6).
        checkable: true
        checked: folderViewMenu.viewRootToken === "mypics"
        onTriggered: {
            if (bar.folderViewCtl) bar.folderViewCtl.setViewRoot("mypics")
            checked = Qt.binding(function () {
                return folderViewMenu.viewRootToken === "mypics"
            })
        }
    }
    MenuItem {
        objectName: "menuViewRootMyDocuments"
        text: qsTr("My Do&cuments")
        //: `CSIDL_PERSONAL` (0x05) → `QStandardPaths.DocumentsLocation`.
        checkable: true
        checked: folderViewMenu.viewRootToken === "mydocs"
        onTriggered: {
            if (bar.folderViewCtl) bar.folderViewCtl.setViewRoot("mydocs")
            checked = Qt.binding(function () {
                return folderViewMenu.viewRootToken === "mydocs"
            })
        }
    }
    MenuItem {
        objectName: "menuViewRootDesktop"
        text: qsTr("&Desktop")
        //: `CSIDL_DESKTOP` (0x00) → `QStandardPaths.DesktopLocation`.
        checkable: true
        checked: folderViewMenu.viewRootToken === "desktop"
        onTriggered: {
            if (bar.folderViewCtl) bar.folderViewCtl.setViewRoot("desktop")
            checked = Qt.binding(function () {
                return folderViewMenu.viewRootToken === "desktop"
            })
        }
    }
    MenuSeparator {}
    // #1766: az ÖT lista-rendezés tétel. A helyüket a tulajdonos
    // képernyőképe döntötte el (`research/#1766-nezet-mappanezet-almenu.png`):
    // ebben az ALMENÜBEN vannak, nem a Nézet menü felső szintjén.
    //
    // A jegy eredeti bizonyítéka (`GetSubMenu(GetMenu(hwnd), 2)`) a
    // menü-HOVATARTOZÁST igazolta, a menün belüli HELYET nem — a
    // spec 49.1 ezt ki is mondta, és emiatt állt a jegy hónapokig.
    //
    // ⚠️ Ez a `eMenuView::` ötös, HOSSZÚ feliratokkal. A Mappa menü
    // NÉGYES, rövid feliratú `ID_*SORT` készlete (#1595) MÁS — a
    // kettő összekeverése épp az a hiba, amit a #1595 javított.
    //
    // A sorrend is a felvételről jön: dátum · legutóbbi
    // változtatások · méret · név · megfordítás.
    //
    // A négy mód KIZÁRÓ csoport, ezért a #1464/#1468 rádió-csapdája
    // ellen a jelzés után azonnal VISSZAKÖTJÜK a `checked`-et; a
    // megfordítás önálló kapcsoló, ott erre nincs szükség.
    MenuItem {
        objectName: "menuViewSortByDate"
        text: qsTr("Sort by &Creation Date")
        checkable: true
        checked: folderViewMenu.rendezes === "date"
        onTriggered: {
            if (controllerRef) controllerRef.setPaneSort("date")
            checked = Qt.binding(function () {
                return folderViewMenu.rendezes === "date"
            })
        }
    }
    MenuItem {
        objectName: "menuViewSortByRecent"
        text: qsTr("Sort by &Recent Changes")
        checkable: true
        checked: folderViewMenu.rendezes === "changed"
        onTriggered: {
            if (controllerRef) controllerRef.setPaneSort("changed")
            checked = Qt.binding(function () {
                return folderViewMenu.rendezes === "changed"
            })
        }
    }
    MenuItem {
        objectName: "menuViewSortBySize"
        text: qsTr("Sort by &Size")
        checkable: true
        checked: folderViewMenu.rendezes === "size"
        onTriggered: {
            if (controllerRef) controllerRef.setPaneSort("size")
            checked = Qt.binding(function () {
                return folderViewMenu.rendezes === "size"
            })
        }
    }
    MenuItem {
        objectName: "menuViewSortByName"
        text: qsTr("Sort by &Name")
        checkable: true
        checked: folderViewMenu.rendezes === "name"
        onTriggered: {
            if (controllerRef) controllerRef.setPaneSort("name")
            checked = Qt.binding(function () {
                return folderViewMenu.rendezes === "name"
            })
        }
    }
    MenuItem {
        objectName: "menuViewSortReverse"
        text: qsTr("Re&verse sort")
        checkable: true
        checked: folderViewMenu.rendezesForditott
        onTriggered: {
            if (controllerRef) controllerRef.togglePaneSortReverse()
            // #2377: a `checkable` MenuItem kattintáskor MAGA billenti a
            // `checked`-et, és ez eldobja a fenti kötést. Ma azért nem
            // látszik, mert a művelet mindig átbillenti az állapotot —
            // ez szerencse, nem szerkezet (ld. #1471).
            checked = Qt.binding(function () {
                return folderViewMenu.rendezesForditott
            })
        }
    }
    MenuSeparator {}
    // #4528: az eredeti folderviewpopup a név-, darabszám- és Top 10
    // szerinti Emberek-rendezést közvetlenül a lista rendezése után
    // kínálja. A pipa és a tényleges sorrend is az AppController
    // PeopleMixinjéből jön.
    MenuItem {
        objectName: "menuViewSortPeopleByName"
        text: qsTr("Sort &People by Name")
        checkable: true
        checked: folderViewMenu.peopleSort === "name"
        onTriggered: {
            if (controllerRef) controllerRef.setPeopleSort("name")
            checked = Qt.binding(function () {
                return folderViewMenu.peopleSort === "name"
            })
        }
    }
    MenuItem {
        objectName: "menuViewSortPeopleByAmount"
        text: qsTr("Sort People by &Amount")
        checkable: true
        checked: folderViewMenu.peopleSort === "count"
        onTriggered: {
            if (controllerRef) controllerRef.setPeopleSort("count")
            checked = Qt.binding(function () {
                return folderViewMenu.peopleSort === "count"
            })
        }
    }
    MenuItem {
        objectName: "menuViewSortPeopleByTop10"
        text: qsTr("Sort People by Top &10")
        checkable: true
        checked: folderViewMenu.peopleSort === "top"
        onTriggered: {
            if (controllerRef) controllerRef.setPeopleSort("top")
            checked = Qt.binding(function () {
                return folderViewMenu.peopleSort === "top"
            })
        }
    }
    MenuSeparator {}
    // #4528: az AlbumList::Shortcuts almenü. A gyökérválasztók
    // ugyanazokat a vezérlőműveleteket használják, mint a közvetlen
    // tételek, ezért a két belépési pont pipája együtt mozog.
    PicasaMenu {
        objectName: "menuViewFolderViewShortcuts"
        title: qsTr("&Shortcuts")
        MenuItem {
            objectName: "menuViewShortcutMyComputer"
            text: qsTr("My &Computer")
            checkable: true
            checked: folderViewMenu.viewRootToken === "all"
            onTriggered: {
                if (bar.folderViewCtl)
                    bar.folderViewCtl.setViewRoot("all")
                checked = Qt.binding(function () {
                    return folderViewMenu.viewRootToken === "all"
                })
            }
        }
        MenuItem {
            objectName: "menuViewShortcutMyPictures"
            text: qsTr("My &Pictures")
            checkable: true
            checked: folderViewMenu.viewRootToken === "mypics"
            onTriggered: {
                if (bar.folderViewCtl)
                    bar.folderViewCtl.setViewRoot("mypics")
                checked = Qt.binding(function () {
                    return folderViewMenu.viewRootToken === "mypics"
                })
            }
        }
        MenuItem {
            objectName: "menuViewShortcutMyDocuments"
            text: qsTr("My Do&cuments")
            checkable: true
            checked: folderViewMenu.viewRootToken === "mydocs"
            onTriggered: {
                if (bar.folderViewCtl)
                    bar.folderViewCtl.setViewRoot("mydocs")
                checked = Qt.binding(function () {
                    return folderViewMenu.viewRootToken === "mydocs"
                })
            }
        }
        MenuItem {
            objectName: "menuViewShortcutDesktop"
            text: qsTr("&Desktop")
            checkable: true
            checked: folderViewMenu.viewRootToken === "desktop"
            onTriggered: {
                if (bar.folderViewCtl)
                    bar.folderViewCtl.setViewRoot("desktop")
                checked = Qt.binding(function () {
                    return folderViewMenu.viewRootToken === "desktop"
                })
            }
        }
    }
    MenuSeparator {}
    // #2049: „Indexképek megjelenítése a könyvtárban" — a bal
    // hasáb fasorain a sárga mappaikon helyett a mappa első
    // legfeljebb négy fotójából álló kupac. Az eredeti kulcsa
    // `ShowAlbumThumbnails2`, alapértéke 0, ezért kikapcsolva
    // indul; a listaépítő (`0x00761870`) olvassa be.
    //
    // A #1464/#1468 rádió-csapdája ide is vonatkozik: a valódi
    // kattintás előbb billenti a `checked`-et, mint ahogy a
    // `triggered` eldördül, ezért a jelzés után visszakötjük.
    MenuItem {
        objectName: "menuViewAlbumThumbnails"
        text: qsTr("Show &Thumbnails in Library")
        //: #2989: fastruktúrájú nézetben SZÜRKE. A tulajdonos 3.
        //: felvételén a tétel letiltva áll, a bélyegképek mégis
        //: látszanak — ott a kapcsoló nem szabályoz semmit.
        enabled: !folderViewMenu.treeMode
        checkable: true
        checked: folderViewMenu.albumThumbsMode
        onTriggered: {
            if (bar.folderViewCtl) bar.folderViewCtl.toggleAlbumThumbs()
            checked = Qt.binding(function () {
                return folderViewMenu.albumThumbsMode
            })
        }
    }

    //: #2019: az „Egyszerűsített fanézet" az almenü LEGALJÁN áll,
    //: az „Indexképek megjelenítése a könyvtárban" UTÁN — így méri
    //: a tulajdonos felvétele (`research/#1766-nezet-mappanezet-almenu.png`).
    //: Nálunk a #1454 óta a nézet-hármas együtt állt, holott az
    //: eredetiben a harmadik el van választva a pártól.
    MenuItem {
        objectName: "menuViewSimplifiedTreeView"
        text: qsTr("&Simplified Tree View")
        checkable: true
        checked: folderViewMenu.simplifiedMode
        onTriggered: {
            if (bar.folderViewCtl) bar.folderViewCtl.toggleSimplified()
            checked = Qt.binding(function () {
                return folderViewMenu.simplifiedMode
            })
        }
    }
}
