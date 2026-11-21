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
    // #7341: a négy eredeti tétel egyszeri, kijelölt mappára ható
    // képrendezés. A mappasor helyi menüje ugyanezt a `sortFolderBy`
    // műveletet használja; a rendezési mód nem marad beállításként.
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
            onTriggered: controller.sortFolderBy(bar.currentFolder, "date")
        }
        MenuItem {
            objectName: "menuFolderSortByName"
            text: qsTr("&Name")
            onTriggered: controller.sortFolderBy(bar.currentFolder, "name")
        }
        MenuItem {
            objectName: "menuFolderSortBySize"
            text: qsTr("&Size")
            onTriggered: controller.sortFolderBy(bar.currentFolder, "size")
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
            onTriggered: controller.sortFolderBy(bar.currentFolder, "reverse")
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
        enabled: bar.folderMoveEnabled
        onTriggered: bar.folderMoveRequested()
    }
    MenuItem {
        objectName: "menuFolderDelete"
        text: qsTr("&Delete...")
        // #7181: ez a tétel a megnyitott mappát, felhasználói albumot vagy
        // személyalbumot törli. A korábbi mappaútvonal album- és
        // személynézetben megmarad, keresésnél pedig a találati lista nem
        // törlési cél, ezért a tényleges nézetet is ellenőrizzük.
        enabled: !(controllerRef && controllerRef.searchActive === true)
            && (bar.currentPersonName !== ""
                || (bar.currentAlbumToken !== ""
                    && bar.currentAlbumToken.charAt(0) !== "]")
                || (bar.currentAlbumToken === ""
                    && bar.currentPersonName === ""
                    && bar.currentFolder !== ""
                    && (!controllerRef
                        || controllerRef.viewModeName === undefined
                        || controllerRef.viewModeName === "folder")))
        onTriggered: bar.folderDeleteRequested()
    }
}
