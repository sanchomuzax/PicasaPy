import QtQuick
import QtQuick.Controls

// Az indexkép (rács) jobbklikk-menüje — a Picasa `AlbumPhoto` menüosztálya,
// 19 tétellel (#15 kezdte 7 tétellel, #422 tölti fel a teljes listára).
//
// A tételsort, a csoportbontást és a hivatalos magyar feliratokat a
// `docs/specs/ui-audit-context-menus.md` 2. szakasza rögzíti.
//
// PARITÁS: az „Átnevezés…" KIKERÜLT ebből a menüből — az eredetiben nincs
// itt, hanem a Fájl menüben (`F2`), ahol nálunk is megvan és működik.
// Az „Eltávolítás az albumból" viszont MARAD: a spec szerint az eredetiben
// is csak album-nézetben jelenik meg, és nálunk is csak ott látszik
// (`currentAlbumToken`).
//
// A néző menüje (ViewerContextMenu.qml) szándékosan MÁS: az első tétel ott
// „Visszatérés a könyvtárhoz", a mappa-műveletek elmaradnak, a törlés
// gyorsbillentyűje pedig `Delete` — itt `Ctrl+Delete` (spec 3.).
//
// A még be nem kötött parancsok `PicasaMenuItem { placeholder: true }`-ként
// szürkén LÁTSZANAK (#416, illetve a spec 5.1. szabálya: az inaktív tétel
// is tétel, hogy a menü magassága és a tételek helye állandó maradjon).
//
// Önálló, signal-alapú komponens: a bekötést a Main.qml végzi.
Menu {
    id: menu
    objectName: "photoContextMenu"

    // #17: igaz, ha a jobbklikkelt kép rejtett — a tétel felirata VÁLT
    // (Elrejtés ↔ Megjelenítés), nem pipát kap (spec A.2)
    property bool hideChecked: false

    // #9: albumtagság — a Main.qml köti be a `controller.albums` listáját
    // és az aktív album tokent (#305 null-őr, ld. ott).
    property var albums: []
    property string currentAlbumToken: ""
    //: a jelenleg mutatott személy neve (üres, ha nem személy-album)
    property string personName: ""

    signal openRequested()
    signal addToAlbumRequested(string token)
    signal removeFromAlbumRequested()
    // #422: az Emberek-album kép-szintű parancsai — a hívó (Main.qml) tölti
    // a `personName`-et a `peopleController.currentPersonName`-ből; üres
    // string = a rács nem személy-albumot mutat, a tételek rejtve maradnak
    signal removeFromPeopleAlbumRequested()
    signal moveToNewPersonRequested()
    signal newAlbumRequested()
    signal rotateRightRequested()
    signal rotateLeftRequested()
    signal hideToggleRequested()
    signal moveRequested()
    signal openFileRequested()
    signal locateRequested()
    signal deleteRequested()
    signal copyFullPathRequested()
    signal propertiesRequested()

    // -- 1. blokk: az alapértelmezett művelet (félkövér) + album ----------

    MenuItem {
        objectName: "contextMenuOpen"
        text: qsTr("View and Edit") + "\tEnter"
        // a félkövér első tétel a dupla­kattintás alapértelmezett
        // művelete (spec 5.3.)
        font.bold: true
        onTriggered: menu.openRequested()
    }
    Menu {
        id: addToAlbumMenu
        objectName: "contextMenuAddToAlbum"
        title: qsTr("Add to Album")

        Repeater {
            id: addToAlbumRepeater
            objectName: "contextMenuAddToAlbumRepeater"
            model: menu.albums
            delegate: MenuItem {
                id: addToAlbumItem
                required property var modelData
                objectName: "contextMenuAddToAlbumItem_" + modelData.token
                text: modelData.name
                onTriggered: menu.addToAlbumRequested(modelData.token)
            }
        }
        MenuSeparator { visible: menu.albums.length > 0 }
        MenuItem {
            objectName: "contextMenuNewAlbum"
            text: qsTr("New Album...")
            onTriggered: menu.newAlbumRequested()
        }
    }
    MenuItem {
        objectName: "contextMenuRemoveFromAlbum"
        text: qsTr("Remove from Album")
        // csak album-nézetben (#9): a rács ott az adott album tagjait
        // mutatja, ott van értelme a kijelölés kivételének
        visible: menu.currentAlbumToken !== ""
        onTriggered: menu.removeFromAlbumRequested()
    }

    // #422 4. lépcső: az Emberek-album KÉP-szintű parancsai (`PplAlbumPhoto`,
    // ld. `ui-audit-context-menus.md` A.2). Csak akkor látszanak, ha a rács
    // épp egy személy albumát mutatja — ott van értelmük.
    MenuItem {
        objectName: "contextMenuRemoveFromPeopleAlbum"
        text: qsTr("Remove from People Album")
        visible: menu.personName !== ""
        onTriggered: menu.removeFromPeopleAlbumRequested()
    }
    MenuItem {
        objectName: "contextMenuMoveToNewPerson"
        text: qsTr("Move to New Person...")
        visible: menu.personName !== ""
        onTriggered: menu.moveToNewPersonRequested()
    }
    // A negyedik `PplAlbumPhoto` parancs („Beállítás az Emberek album
    // indexképeként") HELYŐRZŐ: a személyenkénti indexkép-választásnak nincs
    // tárolója (sem a `.picasa.ini`-ben, sem az indexünkben), tehát a
    // bekötése nem UI-, hanem adatmodell-kérdés (#26).
    PicasaMenuItem {
        objectName: "contextMenuSetAsPeopleAlbumThumbnail"
        text: qsTr("Set as People Album Thumbnail")
        visible: menu.personName !== ""
    }
    MenuSeparator {}

    // -- 2. blokk: forgatás ------------------------------------------------

    MenuItem {
        objectName: "contextMenuRotateRight"
        text: qsTr("Rotate Right") + "\tCtrl+R"
        onTriggered: menu.rotateRightRequested()
    }
    MenuItem {
        objectName: "contextMenuRotateLeft"
        text: qsTr("Rotate Left") + "\tCtrl+Shift+R"
        onTriggered: menu.rotateLeftRequested()
    }
    MenuSeparator {}

    // -- 3. blokk: szerkesztés visszavonása --------------------------------

    PicasaMenuItem {
        objectName: "contextMenuUndoAllEdits"
        text: qsTr("Undo All Edits")
        placeholder: true
    }
    MenuSeparator {}

    // -- 4. blokk: rejtés ---------------------------------------------------

    MenuItem {
        objectName: "contextMenuHide"
        // állapotfüggő felirat-váltás UGYANAZON a helyen (spec A.2):
        // ID_PICTURE_HIDE „Elrejtés" ↔ ID_PICTURE_UNHIDE „Megjelenítés"
        text: menu.hideChecked ? qsTr("Unhide") : qsTr("Hide")
        onTriggered: menu.hideToggleRequested()
    }
    MenuSeparator {}

    // -- 5. blokk: mappa-műveletek -------------------------------------------

    MenuItem {
        objectName: "contextMenuMove"
        text: qsTr("Move to New Folder...")
        onTriggered: menu.moveRequested()
    }
    PicasaMenuItem {
        objectName: "contextMenuSplitFolder"
        text: qsTr("Split Folder Here...")
        placeholder: true
    }
    MenuSeparator {}

    // -- 6. blokk: megnyitás -------------------------------------------------

    MenuItem {
        objectName: "contextMenuOpenFile"
        text: qsTr("Open File") + "\tCtrl+Shift+O"
        onTriggered: menu.openFileRequested()
    }
    PicasaMenuItem {
        // „Társítás ▸" — a társított alkalmazások listája még nincs meg
        objectName: "contextMenuOpenWith"
        text: qsTr("Open With")
        placeholder: true
    }
    MenuSeparator {}

    // -- 7. blokk: mentés / visszaállítás -------------------------------------

    PicasaMenuItem {
        objectName: "contextMenuSave"
        text: qsTr("Save") + "\tCtrl+S"
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "contextMenuRevert"
        text: qsTr("Revert")
        placeholder: true
    }
    MenuSeparator {}

    // -- 8. blokk: lemez --------------------------------------------------------

    MenuItem {
        objectName: "contextMenuLocate"
        text: qsTr("Locate on Disk") + "\tCtrl+Enter"
        onTriggered: menu.locateRequested()
    }
    MenuItem {
        objectName: "contextMenuDelete"
        // a rácsban Ctrl+Delete — a nézőben puszta Delete (spec 3.)
        text: qsTr("Delete from Disk") + "\tCtrl+Delete"
        onTriggered: menu.deleteRequested()
    }
    MenuItem {
        objectName: "contextMenuCopyFullPath"
        text: qsTr("Copy Full Path")
        onTriggered: menu.copyFullPathRequested()
    }
    MenuSeparator {}

    // -- 9. blokk: megosztás -----------------------------------------------------

    PicasaMenuItem {
        objectName: "contextMenuUploadToWebAlbums"
        text: qsTr("Upload to Picasa Web Albums...")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "contextMenuBlockUpload"
        text: qsTr("Block Upload")
        placeholder: true
    }
    MenuSeparator {}

    // -- 10. blokk: arcok ---------------------------------------------------------

    PicasaMenuItem {
        objectName: "contextMenuResetFaces"
        text: qsTr("Reset Faces")
        placeholder: true
    }
    MenuSeparator {}

    // -- 11. blokk: tulajdonságok --------------------------------------------------

    MenuItem {
        objectName: "contextMenuProperties"
        text: qsTr("Properties") + "\tAlt+Enter"
        onTriggered: menu.propertiesRequested()
    }
}
