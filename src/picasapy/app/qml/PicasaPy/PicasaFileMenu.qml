import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

PicasaMenu {
    id: menuFile
    property var bar: null
    title: qsTr("&File")
    // #1616: a tétel `PicasaMenuItem { placeholder: true }` volt, az #416
    // óta. A Ctrl+M/Ctrl+O mintáját követjük: a Fájl-menü tétele és a Ctrl+N
    // UGYANAZT a dialógust nyitja (`openNewAlbum`, FileOpsDialogs.qml).
    // #7164: ÜRES albumot készít, a kijelölt képeket nem adja át.
    // #7180: a tétel kijelölés nélkül is engedélyezett, ezért nincs `enabled`
    // feltétele: az eredeti Fájl-menü állapotfrissítője (`0x0056e1c0`) a
    // `0x9d67` (New Album...) azonosítót sehol nem szürkíti, és a `0x005eb810`
    // kezelő nem vizsgál kijelölést.
    MenuItem {
        objectName: "menuFileNewAlbum"
        text: qsTr("&New Album...") + "\tCtrl+N"
        onTriggered: bar.newAlbumRequested()
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    // ⚠️ #1200: ez NEM külön funkció és NEM mappaválasztó — az
    // eredetiben EZ A MENÜPONT nyitja meg a Mappakezelőt:
    // `eMenuFile::ID_TOOLS_INCLUDEEXCLUDEFOLDERS` (`stringres` 2648.)
    // → parancs `0x9caa` → `0x005cb990` szétosztó → `0x005ce590`.
    //
    // Korábban fordítva volt: a menüpont inaktív (placeholder), a
    // funkciót pedig egy gomb végezte magában a párbeszédben.
    MenuItem {
        objectName: "menuFileAddFolder"
        text: qsTr("Add Folder to PicasaPy...")
        //: #1768: szürke, amíg a szerkesztő nyitva — az eredeti sem
        //: üzen, csak nem engedi. A könyvtár szerkezetének
        //: átrendezése félbehagyott szerkesztés mellett kockázatos.
        enabled: !bar.editorActive
        onTriggered: bar.folderManagerRequested()
    }
    // #1633: ÉLŐ tétel. A fájlválasztó nem függ kijelöléstől, ezért
    // nincs `enabled` feltétele — ugyanúgy, mint az Importálás forrása…
    MenuItem {
        objectName: "menuFileAddFile"
        text: qsTr("Add &File to PicasaPy...") + "\tCtrl+O"
        onTriggered: bar.addFileRequested()
    }
    // #1615: ÉLŐ tétel. Az importálás nem függ kijelöléstől (a forrást
    // maga a párbeszéd kérdezi meg), ezért — a Nyomtatás…-tól eltérően
    // — nincs `enabled` feltétele.
    MenuItem {
        objectName: "menuFileImportFrom"
        text: qsTr("&Import From...") + "\tCtrl+M"
        onTriggered: bar.importSourceRequested()
    }
    // #638/#5570: nyugdíjazott Google Fotók-import; az eredeti „from” kisbetűs.
    PicasaMenuItem {
        objectName: "menuFileImportFromGooglePhotos"
        text: qsTr("Import from Google Photos...")
        placeholder: false
        retired: true
    }  // #5570
    MenuSeparator {}
    // #4330: a kijelölt fájlokat a rendszer alapértelmezett
    // alkalmazásában nyitja meg; a billentyű a Main.qml-ben ugyanide fut.
    MenuItem {
        objectName: "menuFileOpenInEditor"
        text: qsTr("&Open File(s) in an Editor") + "\tCtrl+Shift+O"
        enabled: bar.photoActionsEnabled
        onTriggered: bar.openInEditorRequested()
    }
    MenuSeparator {}
    // #1614: ÉLŐ tétel — MÉRVE (`git log -S'ID_FILE_NEWFOLDER'`) a
    // tétel a #324 audit óta helyfoglaló volt, holott a parancs neve
    // ELLENÉRE nem mappa-létrehozás, hanem a kijelölt képek áthelyezése
    // (ld. a `moveToNewFolderRequested` jelzés fenti megjegyzését). A
    // kijelölés-függés (`photoActionsEnabled`) itt indokolt: kijelölés
    // nélkül nincs mit áthelyezni. (Az „Új album…" a #7180 óta nem függ
    // kijelöléstől.)
    MenuItem {
        objectName: "menuFileMoveToNewFolder"
        text: qsTr("Mo&ve to New Folder...")
        enabled: bar.photoActionsEnabled
        onTriggered: bar.moveToNewFolderRequested()
    }
    MenuItem {
        objectName: "menuFileRename"
        text: qsTr("&Rename...") + "\tF2"
        enabled: bar.photoActionsEnabled
        onTriggered: bar.renameRequested()
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    // #444/#1791: a nem-destruktív mentés HÁROM fokozata, de a
    // menüben csak KETTŐ látszik. A „Mentés" beégeti a
    // szerkesztéseket a fájlba (előtte biztonsági másolattal), a
    // „Visszaállítás" az eredetit hozza vissza (a szerkesztések
    // elvesznek). A harmadik fokozat — a fájl visszaáll, de a
    // szerkesztések MEGMARADNAK — az eredetiben NEM menütétel, hanem
    // a Visszaállítás párbeszéd „Undo Save" gombja
    // (`CThumbUI::FileRevert::undosave`); ld. SaveDialogs.qml.
    MenuItem {
        objectName: "menuFileSave"
        text: qsTr("&Save") + "\tCtrl+S"
        enabled: bar.photoActionsEnabled && bar.photoHasPendingEdits
        onTriggered: bar.saveRequested()
    }
    MenuItem {
        objectName: "menuFileRevert"
        text: qsTr("Rever&t")
        // csak akkor van mit visszaállítani, ha a kép már volt mentve
        enabled: bar.photoActionsEnabled && bar.hasSavedBackup
        onTriggered: bar.revertRequested()
    }
    MenuSeparator {}
    // #1527: a mentés-család két további tagja — ÉLŐ tételek. A
    // különbségük MÉRT (`picasapy.edit.save_copy` modul-docstring):
    // a „Mentés másként…" fájlválasztót nyit (ellipszis a
    // feliratban), és az AKTUÁLIS képre hat, mert egy választó egy
    // célt tud megnevezni; a „Másolat mentése" nem kérdez, a nevet
    // a mért `-001` minta adja, és a teljes kijelölésre hat.
    MenuItem {
        objectName: "menuFileSaveAs"
        text: qsTr("Save &As...")
        enabled: bar.photoActionsEnabled && bar.hasPhotoSelection
        onTriggered: bar.saveAsRequested()
    }
    MenuItem {
        objectName: "menuFileSaveCopy"
        text: qsTr("Save a Cop&y")
        enabled: bar.photoActionsEnabled && bar.hasPhotoSelection
        onTriggered: bar.saveCopyRequested()
    }
    // #1774 (mérve): az exportálás UGYANEBBEN a csoportban van, mint a
    // „Mentés másként…” és a „Másolat mentése” — nincs közte elválasztó.
    MenuItem {
        objectName: "menuFileExport"
        text: qsTr("Export Pi&cture to Folder...") + "\tCtrl+Shift+S"
        enabled: bar.photoActionsEnabled
        onTriggered: bar.exportRequested()
    }
    MenuSeparator {}
    MenuItem {
        objectName: "menuFileLocate"
        text: qsTr("Locate on Disk") + "\tCtrl+Enter"
        enabled: bar.photoActionsEnabled
        onTriggered: bar.locateRequested()
    }
    MenuItem {
        objectName: "menuFileDelete"
        // #1608: a felirat a nézettel EGYÜTT vált
        text: bar.deleteCommandText + "\tDelete"
        enabled: bar.photoActionsEnabled
        onTriggered: bar.activateDeleteCommand()
    }
    MenuSeparator {}
    // #1472: ÉLŐ tétel — a `print_controller.py` 213 sora addig
    // elérhetetlen volt, mert ez a pont helyfoglaló maradt
    MenuItem {
        objectName: "menuFilePrint"
        text: qsTr("&Print...") + "\tCtrl+P"
        enabled: bar.photoActionsEnabled
        onTriggered: bar.printRequested()
    }
    // #4329: ugyanaz a Main.qml-beli küldési út, mint a tálca E-Mail
    // gombján; Ctrl+E a `emailShortcut`-on át ezt a jelzést küldi.
    MenuItem {
        objectName: "menuFileEmail"
        text: qsTr("&E-Mail...") + "\tCtrl+E"
        enabled: bar.photoActionsEnabled
        onTriggered: bar.emailRequested()
    }
    // hiányzott (#324 audit): nyomtatott képek online rendelése
    PicasaMenuItem { text: qsTr("Order Prin&ts..."); placeholder: false; retired: true }  // #638
    MenuSeparator {}
    // #1527: a Fájl menü zárótétele. A jegy „nincs a menüben"-ként
    // írta le — MÉRVE megvolt (2026-08-24), csak `objectName` nélkül,
    // ezért egyetlen teszt sem érte el. A név most már fogja.
    MenuItem {
        objectName: "menuFileExit"
        text: qsTr("E&xit")
        //: #671: a kilépés EGY helyen dől el (`Main.qml` `kilepes()`) —
        //: ott van a háttérmunka-kérdés. A `Qt.quit()` közvetlen hívása
        //: megkerülte volna.
        onTriggered: bar.exitRequested()
    }
}
