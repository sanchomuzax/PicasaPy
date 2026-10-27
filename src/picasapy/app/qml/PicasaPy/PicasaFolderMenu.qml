import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

PicasaMenu {
    id: menuFolder
    property var bar: null
    property var controllerRef: null
    title: bar.currentAlbumToken !== "" ? qsTr("&Album") : qsTr("F&older")
    onAboutToShow: {
        bar.folderUnhideEnabled = bar.folderLocateEnabled
            && controllerRef
            && controllerRef.isFolderHidden !== undefined
            && controllerRef.isFolderHidden(bar.currentFolder)
    }
    MenuItem {
        objectName: "menuFolderEditDescription"
        text: bar.currentAlbumToken !== ""
            ? qsTr("&Edit Album Description...")
            : qsTr("&Edit Description...")
        // #4883: a Csillagozott album (`]star`) nem létező album, nincs
        // `[.album:]star]` szakasza — leírása nincs (spec D.8). Album-
        // nézetben a mappa-ág nem érvényesül: a controller a mappát
        // album-nézetben is megőrzi.
        enabled: bar.currentAlbumToken !== ""
            ? bar.currentAlbumToken !== "]star"
            : (bar.currentFolder !== "" && bar.currentPersonName === "")
        onTriggered: bar.editFolderDescriptionRequested()
    }
    MenuItem {
        objectName: "menuFolderSlideshow"
        text: qsTr("&View Slideshow") + "\tCtrl+4"
        onTriggered: bar.slideshowRequested()
    }
    MenuSeparator {}
    MenuItem {
        text: qsTr("Refresh &Thumbnails")
        onTriggered: bar.rescanRequested()
    }
    // #324 audit („eltérő"): eredetiben aktív almenü — nálunk is az.
    // #1454: a mappák sorrendje EGYEDÜL itt (és az indexkép-helyi
    // menüben) állítható; a Nézet ▸ Mappanézetből kikerült, mert ott az
    // eredetiben szerkezeti tételek állnak, nem rendezés.
    // #1468: a valódi kattintás előbb IMPERATÍVAN átbillenti a `checked`-et,
    // és csak utána dördül el a `triggered`. Kizáró csoportban a MÁR AKTÍV
    // tételre kattintva a vezérlő állapota nem változik, tehát a kötés magától
    // soha nem értékelődik újra — a menü újranyitásakor egyik tételen sem
    // állna pipa. Ezért a jelzés után azonnal VISSZAKÖTJÜK a `checked`-et
    // (a #1464-ben bevezetett minta).
    //
    // A négy rendezési szempont kizáró csoport; a „Fordított sorrend"
    // ÖNÁLLÓ kapcsoló (az állapota minden kattintásra változik, a kötés
    // tehát magától helyreáll) — ott nem kell visszakötés.
    PicasaMenu {
        objectName: "menuFolderSortBy"
        // #1595: az eredetiben KÉT rendezés-készlet van, és mi a rosszat
        // tettük ide. Az `ID_*SORT` négyes (RÖVID felirat) a Mappa menüé
        // és a mappa helyi menüjéé; az `ID_VIEWBY*` ötös (HOSSZÚ felirat,
        // benne a „legutóbbi változtatások") a Nézet menüé és a bal
        // hasábé. A `FolderContextMenu.qml` végig a helyeset használta —
        // ugyanaz a rendezés két helyen, kétféle felirattal állt.
        title: qsTr("&Sort By")
        MenuItem {
            objectName: "menuFolderSortByDate"
            text: qsTr("&Date")
            checkable: true
            checked: controllerRef && controllerRef.folderSort === "date"
            onTriggered: {
                controller.setFolderSort("date")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.folderSort === "date"
                })
            }
        }
        MenuItem {
            objectName: "menuFolderSortByName"
            text: qsTr("&Name")
            checkable: true
            checked: controllerRef && controllerRef.folderSort === "name"
            onTriggered: {
                controller.setFolderSort("name")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.folderSort === "name"
                })
            }
        }
        MenuItem {
            objectName: "menuFolderSortBySize"
            text: qsTr("&Size")
            checkable: true
            checked: controllerRef && controllerRef.folderSort === "size"
            onTriggered: {
                controller.setFolderSort("size")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.folderSort === "size"
                })
            }
        }
        // SAJÁT FUNKCIÓ (#1595): a „legutóbbi változtatások" szerinti
        // rendezés — az eredeti négyes `ID_*SORT` készletben nincs ilyen
        // tétel, nálunk viszont működő rendezés (#1759 mérte ki, mit
        // rendez). A hűségért nem vesszük el; a `sajat` jelölés (kék
        // felirat + kötelező buboréksúgó) mondja meg, hogy ez a mi
        // többletünk. Jegyzék: docs/decisions/vedett-sajat-funkciok.md
        PicasaMenuItem {
            objectName: "menuFolderSortByChanged"
            text: qsTr("Recent &changes")
            placeholder: false
            sajat: true
            checkable: true
            checked: controllerRef && controllerRef.folderSort === "changed"
            onTriggered: {
                controller.setFolderSort("changed")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.folderSort === "changed"
                })
            }
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuFolderSortReverse"
            text: qsTr("&Reverse order")
            checkable: true
            checked: (controllerRef && controllerRef.folderSortReverse !== undefined)
                ? controllerRef.folderSortReverse : false
            onTriggered: {
                controller.toggleFolderSortReverse()
                // #2377: a `checkable` MenuItem kattintáskor MAGA billenti a
                // `checked`-et, és ez eldobja a fenti kötést. Ma azért nem
                // látszik, mert a művelet mindig átbillenti az állapotot —
                // ez szerencse, nem szerkezet (ld. #1471).
                checked = Qt.binding(function () {
                    return (controllerRef && controllerRef.folderSortReverse !== undefined)
                        ? controllerRef.folderSortReverse : false
                })
            }
        }
    }
    MenuSeparator {}
    // #4416/#4741: a kijelölt mappát ugyanazzal a vezérlőművelettel rejti
    // el, amelyet a FolderContextMenu hív. Album- és személynézetben a
    // vezérlő megőrzi az előző mappát, de ott nincs kijelölt mappa.
    MenuItem {
        objectName: "menuFolderHide"
        text: qsTr("&Hide")
        enabled: bar.folderLocateEnabled
        onTriggered: bar.setCurrentFolderHidden(true)
    }
    // #4416: a Rejtett mappák gyűjteményében kijelölt mappát hozza
    // vissza. A #5882 a valódi rejtett állapothoz köti az engedélyezést.
    MenuItem {
        objectName: "menuFolderShow"
        text: qsTr("&Unhide")
        enabled: bar.folderLocateEnabled && bar.folderUnhideEnabled
        onTriggered: bar.setCurrentFolderHidden(false)
    }
    MenuSeparator {}
    // hiányzott (#324 audit)
    // #1590: ÉLŐ tétel. A #1472 még szándékosan hagyta helyfoglalónak,
    // mert a `print_controller.py` egy képet tett egy oldalra; a
    // #1590-ben megépült az indexkép-rajzoló (`printing/contact_sheet.py`
    // + `PrintController.printContactSheet`), tehát a tétel mögött MOST
    // MÁR van motor. A rácsot a kollázs indexkép-elrendezése adja, a
    // fejlécet viszont az eredeti NYOMTATÓJA („Album:" / „Dátum:") —
    // a kettő az eredetiben sem azonos.
    MenuItem {
        objectName: "menuFolderPrintContactSheet"
        //: #2364: a forrásszöveg az EREDETI erőforrásé
        //: (`eMenuLabelFolder::ID_FILE_PRINTCONTACTSHEET`, a menüépítő
        //: a `0x00559150`-en). A „Thumbnails" a mi szavunk volt; a
        //: Picasa a `thumbnail`-t a KÖNYVTÁRNÉZET bélyegképeire
        //: használja, az itteni fogalom nála „contact sheet".
        text: qsTr("Print Contact Sheet...") + "\tCtrl+Shift+P"
        onTriggered: bar.printContactSheetRequested()
    }
    MenuItem {
        objectName: "menuFolderWebExport"
        text: qsTr("E&xport as HTML Page...")
        onTriggered: bar.webExportRequested()
    }
    MenuSeparator {}
    // #1595/#4620: a négy tétel a megnyitott mappára hat. Album- és
    // személynézetben a controller megtartja a korábbi mappát, ezért
    // ilyenkor ne lehessen a Mappa menüből arra műveletet indítani.
    MenuItem {
        objectName: "menuFolderLocate"
        text: qsTr("Locate on Disk") + "\tCtrl+Enter"
        enabled: bar.folderLocateEnabled
        onTriggered: bar.folderLocateRequested()
    }
    MenuItem {
        objectName: "menuFolderRemoveFromPicasa"
        text: qsTr("&Remove from PicasaPy...")
        enabled: bar.currentFolder !== "" && bar.currentAlbumToken === ""
                 && bar.currentPersonName === ""
        onTriggered: bar.folderRemoveFromPicasaRequested()
    }
    MenuSeparator {}
    // hiányzott (#324 audit): mappa áthelyezése/törlése a lemezen
    MenuItem {
        objectName: "menuFolderMove"
        text: qsTr("&Move...")
        enabled: bar.currentFolder !== "" && bar.currentAlbumToken === ""
                 && bar.currentPersonName === ""
        onTriggered: bar.folderMoveRequested()
    }
    MenuItem {
        objectName: "menuFolderDelete"
        text: qsTr("&Delete...")
        enabled: bar.currentFolder !== "" && bar.currentAlbumToken === ""
                 && bar.currentPersonName === ""
        onTriggered: bar.folderDeleteRequested()
    }
}
