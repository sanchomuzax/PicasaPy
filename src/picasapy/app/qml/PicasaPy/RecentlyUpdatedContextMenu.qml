import QtQuick
import QtQuick.Controls

// A Legutóbb frissítve (Recently Updated) különleges album jobbklikk-menüje (#6851).
// Eredeti forrás: Colab #615, 2026-11-12-recently-updated-helyi-menu.png.
// Sorrend: Edit Album Description... | Select All Pictures, Clear Selection, Invert Selection |
// Refresh Thumbnails, Sort Album By ▸ | Delete Album (szürke) |
// Upload to Google Photos... | Export as HTML Page..., Add name tags.
PicasaMenu {
    id: menu
    objectName: "recentlyUpdatedContextMenu"

    // A különleges album nem törölhető (az eredetiben is szürke/tiltott).
    readonly property bool canDelete: false

    signal editDescriptionRequested()
    signal selectAllRequested()
    signal clearSelectionRequested()
    signal invertSelectionRequested()
    signal refreshThumbnailsRequested()
    signal sortAlbumRequested(string mode)
    signal deleteAlbumRequested()
    signal exportAsHtmlRequested()
    signal addNameTagsRequested()

    // 1. blokk: leírás szerkesztése
    MenuItem {
        objectName: "recentMenuEditDescription"
        text: qsTr("&Edit Album Description...")
        onTriggered: menu.editDescriptionRequested()
    }
    MenuSeparator {
        objectName: "recentMenuSeparator1"
    }

    // 2. blokk: kijelölés
    MenuItem {
        objectName: "recentMenuSelectAll"
        text: qsTr("Select &All Pictures") + "\tCtrl+A"
        onTriggered: menu.selectAllRequested()
    }
    MenuItem {
        objectName: "recentMenuClearSelection"
        text: qsTr("&Clear Selection") + "\tCtrl+D"
        onTriggered: menu.clearSelectionRequested()
    }
    MenuItem {
        objectName: "recentMenuInvertSelection"
        text: qsTr("&Invert Selection") + "\tCtrl+I"
        onTriggered: menu.invertSelectionRequested()
    }
    MenuSeparator {
        objectName: "recentMenuSeparator2"
    }

    // 3. blokk: nézet / rendezés
    MenuItem {
        objectName: "recentMenuRefreshThumbnails"
        text: qsTr("&Refresh Thumbnails")
        onTriggered: menu.refreshThumbnailsRequested()
    }
    PicasaMenu {
        objectName: "recentMenuSortAlbumBy"
        title: qsTr("Sort &Album By")

        MenuItem {
            objectName: "recentMenuSortByDate"
            text: qsTr("&Date")
            onTriggered: menu.sortAlbumRequested("date")
        }
        MenuItem {
            objectName: "recentMenuSortByName"
            text: qsTr("&Name")
            onTriggered: menu.sortAlbumRequested("name")
        }
        MenuItem {
            objectName: "recentMenuSortBySize"
            text: qsTr("&Size")
            onTriggered: menu.sortAlbumRequested("size")
        }
        MenuItem {
            objectName: "recentMenuSortReverse"
            text: qsTr("&Reverse order")
            onTriggered: menu.sortAlbumRequested("reverse")
        }
    }
    MenuSeparator {
        objectName: "recentMenuSeparator3"
    }

    // 4. blokk: törlés (különleges albumnál tiltott / szürke)
    MenuItem {
        objectName: "recentMenuDelete"
        text: qsTr("&Delete Album")
        enabled: menu.canDelete
        onTriggered: menu.deleteAlbumRequested()
    }
    MenuSeparator {
        objectName: "recentMenuSeparator4"
    }

    // 5. blokk: online megosztás (megszűnt)
    PicasaMenuItem {
        objectName: "recentMenuUploadToGooglePhotos"
        text: qsTr("Upload to Google &Photos...")
        placeholder: false
        retired: true
    }
    MenuSeparator {
        objectName: "recentMenuSeparator5"
    }

    // 6. blokk: export és címkék
    MenuItem {
        objectName: "recentMenuExportAsHtml"
        text: qsTr("E&xport as HTML Page...")
        onTriggered: menu.exportAsHtmlRequested()
    }
    PicasaMenuItem {
        objectName: "recentMenuAddNameTags"
        text: qsTr("&Add name tags")
        placeholder: false
        onTriggered: menu.addNameTagsRequested()
    }
}
