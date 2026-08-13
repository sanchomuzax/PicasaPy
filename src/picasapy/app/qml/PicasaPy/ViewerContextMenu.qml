import QtQuick
import QtQuick.Controls

// A néző (egyképes nézet) jobbklikk-menüje — #422, 1. lépcső.
//
// Az eredeti Picasa `OneUp` menüosztálya, 17 tétellel; a tételsort, a
// csoportbontást és a hivatalos magyar feliratokat a
// `docs/specs/ui-audit-context-menus.md` 3. szakasza rögzíti. A nézőben
// eddig EGYÁLTALÁN nem volt kontextusmenü.
//
// A menü szándékosan majdnem azonos a rács `PhotoContextMenu`-jével, de a
// spec szerinti NÉGY eltéréssel:
//   1. az első, félkövér tétel „Visszatérés a könyvtárhoz" (`Esc`), nem
//      „Megjelenítés és szerkesztés" (`Enter`);
//   2. a mappa-műveletek (áthelyezés új mappába, mappa felosztása) itt
//      nincsenek — a nézőben nincs értelmük;
//   3. a lemezről törlés gyorsbillentyűje `Delete`, nem `Ctrl+Delete` (a
//      rácsban a puszta `Delete` = eltávolítás az albumból, itt nincs
//      ütközés);
//   4. a feltöltés „Gyors feltöltés", nem „Feltöltés a Webalbumokba…".
//
// A még be nem kötött parancsok `PicasaMenuItem { placeholder: true }`-ként
// jelennek meg (#416: halvány felirat + pont). Ez EGYBEN a spec 5.1.
// szabálya is: „az inaktív tétel is tétel" — a Picasa sem rejti el a nem
// elérhető parancsot, hogy a menü magassága és a tételek helye állandó
// maradjon.
//
// Önálló komponens (CONTRIBUTING.md mintája, ld. PhotoContextMenu.qml):
// csak jeleket bocsát ki, a bekötést a PhotoViewer.qml végzi.
Menu {
    id: menu
    objectName: "viewerContextMenu"

    // -- állapot, amit a hívó állít be popup() előtt ----------------------

    // igaz, ha a nézett kép rejtett — az Elrejtés/Megjelenítés tétel
    // UGYANAZON a helyen vált feliratot (spec A.2), nem külön tétel
    property bool hidden: false
    // #422: van-e szerkesztés a képen, illetve mentés-előtti másolat — az
    // inaktív tétel LÁTSZIK, csak szürke (az eredeti szabálya)
    property bool hasEdits: false
    property bool hasBackup: false
    // a felhasználó albumai: {token, name} elemek (a PhotoContextMenu
    // `albums` tulajdonságának mintája)
    property var albums: []

    // -- jelek ------------------------------------------------------------

    signal backToLibraryRequested()
    signal addToAlbumRequested(string token)
    signal rotateRightRequested()
    signal rotateLeftRequested()
    signal hideToggleRequested()
    signal openFileRequested()
    signal locateRequested()
    signal deleteRequested()
    signal copyFullPathRequested()
    signal propertiesRequested()
    // #422: a mentés-szemantika három parancsa a NÉZŐBEN is — ugyanaz a
    // motor (#444/#465), mint a rácsban és a menüsávban. Egy parancs, egy
    // út: nem lehet, hogy ugyanaz a menüpont máshol mást csinál.
    signal saveRequested()
    signal revertRequested()
    signal undoAllEditsRequested()
    signal resetFacesRequested()

    // -- teszt-/billentyű-belépők ----------------------------------------
    // A funkcionális teszt a menütételt nem tudja „megkattintani" offscreen,
    // ezért a parancsokat nevesített függvények is kiváltják (a jel és a
    // menütétel is ezeket hívja, így nincs két külön út).
    function triggerBackToLibrary() { menu.backToLibraryRequested() }
    function triggerRotateRight() { menu.rotateRightRequested() }
    function triggerRotateLeft() { menu.rotateLeftRequested() }
    function triggerDelete() { menu.deleteRequested() }

    // -- 1. blokk: az alapértelmezett művelet (félkövér) ------------------

    MenuItem {
        objectName: "viewerMenuBackToLibrary"
        text: qsTr("Back to Library") + "\tEsc"
        // a félkövér első tétel a dupla­kattintás alapértelmezett
        // művelete (spec 5.3.)
        font.bold: true
        onTriggered: menu.triggerBackToLibrary()
    }
    MenuSeparator {}

    // -- 2. blokk: albumtagság --------------------------------------------

    Menu {
        objectName: "viewerMenuAddToAlbum"
        title: qsTr("Add to Album")
        // album nélkül a Picasa is szürkén hagyja az almenüt
        enabled: menu.albums.length > 0

        Repeater {
            model: menu.albums
            delegate: MenuItem {
                required property var modelData
                objectName: "viewerMenuAddToAlbumItem_" + modelData.token
                text: modelData.name
                onTriggered: menu.addToAlbumRequested(modelData.token)
            }
        }
    }
    MenuSeparator {}

    // -- 3. blokk: forgatás ------------------------------------------------

    MenuItem {
        objectName: "viewerMenuRotateRight"
        text: qsTr("Rotate Right") + "\tCtrl+R"
        onTriggered: menu.triggerRotateRight()
    }
    MenuItem {
        objectName: "viewerMenuRotateLeft"
        text: qsTr("Rotate Left") + "\tCtrl+Shift+R"
        onTriggered: menu.triggerRotateLeft()
    }
    MenuSeparator {}

    // -- 4. blokk: szerkesztés visszavonása --------------------------------

    MenuItem {
        objectName: "viewerMenuUndoAllEdits"
        text: qsTr("Undo All Edits")
        enabled: menu.hasEdits
        onTriggered: menu.undoAllEditsRequested()
    }
    MenuSeparator {}

    // -- 5. blokk: rejtés --------------------------------------------------

    MenuItem {
        objectName: "viewerMenuHide"
        // állapotfüggő felirat-váltás UGYANAZON a helyen (spec A.2)
        text: menu.hidden ? qsTr("Unhide") : qsTr("Hide")
        onTriggered: menu.hideToggleRequested()
    }
    MenuSeparator {}

    // -- 6. blokk: megnyitás -----------------------------------------------

    MenuItem {
        objectName: "viewerMenuOpenFile"
        text: qsTr("Open File") + "\tCtrl+Shift+O"
        onTriggered: menu.openFileRequested()
    }
    PicasaMenuItem {
        // „Társítás ▸" — a társított alkalmazások listája még nincs meg
        objectName: "viewerMenuOpenWith"
        text: qsTr("Open With")
        placeholder: true
    }
    MenuSeparator {}

    // -- 7. blokk: mentés / visszaállítás ----------------------------------

    MenuItem {
        objectName: "viewerMenuSave"
        text: qsTr("Save") + "	Ctrl+S"
        enabled: menu.hasEdits
        onTriggered: menu.saveRequested()
    }
    MenuItem {
        objectName: "viewerMenuRevert"
        text: qsTr("Revert")
        enabled: menu.hasBackup
        onTriggered: menu.revertRequested()
    }
    MenuSeparator {}

    // -- 8. blokk: lemez ----------------------------------------------------

    MenuItem {
        objectName: "viewerMenuLocate"
        text: qsTr("Locate on Disk") + "\tCtrl+Enter"
        onTriggered: menu.locateRequested()
    }
    MenuItem {
        objectName: "viewerMenuDelete"
        // a nézőben PUSZTA Delete — a rácsban Ctrl+Delete (spec 3.)
        text: qsTr("Delete from Disk") + "\tDelete"
        onTriggered: menu.triggerDelete()
    }
    MenuItem {
        objectName: "viewerMenuCopyFullPath"
        text: qsTr("Copy Full Path")
        onTriggered: menu.copyFullPathRequested()
    }
    MenuSeparator {}

    // -- 9. blokk: megosztás -------------------------------------------------

    PicasaMenuItem {
        objectName: "viewerMenuQuickUpload"
        text: qsTr("Quick Upload")
        placeholder: true
    }
    PicasaMenuItem {
        objectName: "viewerMenuBlockUpload"
        text: qsTr("Block Upload")
        placeholder: true
    }
    MenuSeparator {}

    // -- 10. blokk: arcok ----------------------------------------------------

    MenuItem {
        objectName: "viewerMenuResetFaces"
        text: qsTr("Reset Faces")
        enabled: true
        onTriggered: menu.resetFacesRequested()
    }
    MenuSeparator {}

    // -- 11. blokk: tulajdonságok --------------------------------------------

    MenuItem {
        objectName: "viewerMenuProperties"
        text: qsTr("Properties") + "\tAlt+Enter"
        onTriggered: menu.propertiesRequested()
    }
}
