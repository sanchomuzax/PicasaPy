import QtQuick
import QtQuick.Controls

// A Picasa 3.9 teljes menüszerkezete (a magyar 3.9-ből dokumentálva,
// ld. docs/specs/ui-audit-menus.md, #324/#327). A még nem implementált
// pontok szürkék — a szerkezet a dizájn része. A gyorsbillentyűk a
// feliratban `\t`-tal elválasztva jelennek meg (pl. "Rename...\tF2");
// a ténylegesen ható (élő) billentyűket vagy a lenti `Shortcut` elemek,
// vagy a Main.qml globális `Shortcut`-jai kötik be — az inaktív
// pontoknál a felirat csak vizuális, nincs mögötte élő billentyű.
MenuBar {
    id: bar
    // #305: null-őr a `controller` kötésekhez — a QML-engine leépítésekor
    // a context property átmenetileg null lehet, miközben a QML-kötések
    // utoljára kiértékelődnek.
    readonly property var ctl: controller
    // #1454: a bal hasáb NÉZETMÓDJA (Egyszerű / Fa / Egyszerűsített fa) a
    // `FolderHierarchyController`-ben él, ami ÖNÁLLÓ context property — nem
    // az `AppController` része. A `typeof`-őr azért kell, mert a menüsávot
    // önmagában betöltő próbák nem regisztrálják.
    readonly property var folderViewCtl:
        (typeof folderHierarchyController !== "undefined")
        ? folderHierarchyController : null

    // #423: a kék „Bejelentkezés Google Fiókkal" hivatkozás a menüsáv jobb
    // szélén — az eredeti Picasa ugyanabban a sorban tartja, mint a
    // Fájl/Szerkesztés/… menüket. A `background` felülírása szükséges,
    // mert a MenuBar tartalma (a menük listája) csak a saját szélességét
    // foglalja el balra — a jobb oldali üres sáv a háttérrétegen keresztül
    // látszik, oda kerül a felirat. A `Theme.canvasBg` a Main.qml
    // `palette.window`-jával megegyező szín (ld. Main.qml `palette {}`
    // blokkja), így a csere vizuálisan nem tér el az alap Fusion-nézettől.
    // Funkció még nincs mögötte (a Google-fiókos bejelentkezés nem cél) —
    // ez csak az elrendezés része, ezért nem interaktív.
    background: Rectangle {
        color: Theme.canvasBg
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width; height: 1
            color: Theme.chromeBorder
        }
        Text {
            objectName: "menuBarSignInLink"
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            text: qsTr("Sign in with your Google Account")
            color: Theme.linkBlue
            font.pixelSize: Theme.fontSize
            font.underline: true
        }
    }
    // van-e kijelölt kép — a fájlművelet- és export-menüpontok feltétele (#15/#16)
    property bool photoActionsEnabled: false
    // #922: a Létrehozás-tételek forrása a KÉPTÁLCA is lehet (#455), ezért
    // NEM a `photoActionsEnabled`-ből élnek — az a rácsbeli kijelöléshez
    // kötött 27 fotó-műveletet vezérli, és azoknak tényleg kijelölés kell.
    property bool createActionsEnabled: false
    // #444: van-e a kijelölésben MÁR mentett kép — enélkül a
    // „Visszaállítás" és az „Utolsó mentés visszavonása" értelmetlen
    property bool hasSavedBackup: false
    signal rescanRequested()
    signal aboutRequested()
    signal thumbSizePreset(int size)
    signal selectStarredRequested()
    signal selectAllRequested()
    signal clearSelectionRequested()
    signal folderManagerRequested()
    // #350: Eszközök → Beállítások... (options.fen) — az OptionsDialog
    // megnyitását a Main.qml köti be (forró fájl, az integrátor dolga)
    signal optionsRequested()
    // #287: Duplikátum-kereső ablak megnyitása
    signal dedupRequested()
    // #1473: Arckeresés — az `Eszközök` menü tétele. Az eredetiben ez nem
    // menüpont volt, hanem alapból bekapcsolt háttérszál
    // (`BgFaceDetectThread`, ld. docs/specs/picasa-arcfelismeres.md 1.1);
    // nálunk háttérmotor híján ez a belépési pont (FaceScanDialog.qml).
    signal faceScanRequested()
    // #368: Eszközök → Kísérleti → Adatbázis áthelyezése
    signal moveDatabaseRequested()
    signal compactDatabaseRequested()
    signal renameRequested()
    signal exportRequested()
    // #1472: Fájl ▸ Nyomtatás… (Ctrl+P) — a párbeszéd a Main.qml-ben él,
    // ugyanúgy, mint az exportnál; a képtálca „Nyomtatás" gombja
    // (TrayBar.printRequested) ugyanoda vezet
    signal printRequested()
    // #351: Mappa → Exportálás weboldalként… (webexport.fen)
    signal webExportRequested()
    // #530: Google Earth-export a kijelölt (geocímkézett) képekből
    signal earthExportRequested()
    // #29: Létrehozás → Képkollázs / Mozgófilm a kijelölésből
    signal collageRequested()
    signal movieRequested()
    signal locateRequested()
    signal deleteRequested()
    // #444: a NÉGY mentés-művelet közül három (a negyedik, az „Összes
    // szerkesztés visszavonása" a Kép menüben él, #465)
    signal saveRequested()
    signal revertRequested()
    signal undoSaveRequested()
    // #1527: a mentés-család két hiányzó tagja. Mérve (ld.
    // `picasapy.edit.save_copy`): az eredetiben MINDKETTŐ ugyanaz a
    // függvény, egyetlen kapcsolóval — a „Mentés másként…" fájlválasztót
    // nyit (ezért végződik a felirata pontokra), a „Másolat mentése"
    // nem kérdez, a nevet a `%s-%03lu` minta adja.
    signal saveAsRequested()
    signal saveCopyRequested()
    signal slideshowRequested()
    // #24: Időrend nézet (Ctrl+5)
    signal timelineRequested()
    // #12: a Címkék-panel állapota kívülről kötve, a menüpont csak kér
    property bool tagsPanelOpen: false
    signal tagsPanelRequested()
    // #30: Helyek-panel (térkép)
    property bool placesPanelOpen: false
    signal placesPanelRequested()
    // #26: Emberek-panel (a jobb fiók negyedik panelje)
    property bool peoplePanelOpen: false
    signal peoplePanelRequested()
    // #17: Kép → Elrejtés a kijelölésre
    signal hideToggleRequested()
    // #13: Tulajdonságok-panel
    property bool propertiesPanelOpen: false
    signal propertiesPanelRequested()
    // #426: „Az összes effektus másolása/beillesztése" — a Beillesztés
    // csak akkor engedélyezett, ha van másolt effektlánc (a
    // controller.hasAllEffectsClipboard-hoz kötve). A `photo_ops_
    // controller.PhotoOpsMixin` motorját hívja — SZÁNDÉKOSAN nem a
    // #152-es `effects_controller`-t, mert az a kép-specifikus
    // `crop64`-et is átvinné (ld. `docs/specs/filterdesc-registry.md`).
    property bool hasAllEffectsClipboard: false
    signal copyAllEffectsRequested()
    signal pasteAllEffectsRequested()
    // #1475: a KÉT kötegelt visszavonás vezérlője. Az eredetiben a
    // Szerkesztés menü ÉLÉN áll a visszavonás (`eMenuEdit::ID_UNDO`, ld.
    // `docs/specs/picasa-hu-terminology.md`), és a felirat megnevezi a
    // visszavonandó műveletet (a `CFilterStackUI` `undoname` kulcsa záró
    // szóközzel áll, ld. `app/edit_action_names.py`). Nálunk a #465 óta
    // HÁROM külön verem van, ezért nem EGY általános „Visszavonás" áll itt,
    // hanem művelet szerint nevesített tétel, mindegyik a SAJÁT
    // `canUndo…`-jától függően szürkülve. Kijelöléstől SZÁNDÉKOSAN nem
    // függenek: a visszavonandó köteg a művelet óta megjegyzett képekre
    // hat, nem a mostani kijelölésre.
    property bool canUndoPasteAllEffects: false
    property bool canUndoBatchEdit: false
    signal undoPasteAllEffectsRequested()
    signal undoBatchEditRequested()
    // #425: Kép ▸ Csoportos szerkesztés — a kijelölt N kép mindegyikére
    // egyszerre alkalmazott egykattintásos effekt (`controller.
    // applyEffectMany`); a `name` a `batch_effect_controller._KNOWN_EFFECTS`
    // egyike ("autolight"/"autocolor"/"redeye"/"enhance"/"unsharp"/
    // "grain2"/"warm"). A forgatás NEM ide tartozik — az a meglévő
    // `rotateRightMany`/`rotateLeftMany` úton fut, közvetlenül a Main.qml-ből.
    signal batchApplyEffectRequested(string name)
    // #465 3. pont: „Undo All Edits" — a kijelölt kép(ek) TELJES
    // szerkesztési láncát törli (a Csoportos szerkesztés almenün KÍVÜL, a
    // Kép menü saját tétele) — megerősítéssel, ld. Main.qml ConfirmDialog.
    signal undoAllEditsRequested()

    // #327: gyorsbillentyűk azoknak az AKTÍV menüpontoknak, amelyeknek
    // még nincs élő bekötésük máshol (a többi már a Main.qml globális
    // Shortcut-jain vagy a menüpont onTriggered-jén keresztül működik —
    // azokhoz itt csak a MENÜBEN LÁTSZÓ felirat tartozik, ld. lent).
    Shortcut {
        objectName: "shortcutSmallThumbnails"
        sequence: "Ctrl+1"
        onActivated: bar.thumbSizePreset(96)
    }
    Shortcut {
        objectName: "shortcutNormalThumbnails"
        sequence: "Ctrl+2"
        onActivated: bar.thumbSizePreset(144)
    }
    Shortcut {
        objectName: "shortcutLocateOnDisk"
        sequence: "Ctrl+Return"
        enabled: bar.photoActionsEnabled
        onActivated: bar.locateRequested()
    }
    Shortcut {
        objectName: "shortcutDeleteFromDisk"
        sequence: "Delete"
        enabled: bar.photoActionsEnabled
        onActivated: bar.deleteRequested()
    }
    // #1472: a Ctrl+P eddig SEHOL nem létezett — a menüfelirat hirdette,
    // de billentyű nem tartozott hozzá. A feliratot itt szó szerint
    // követjük (nem `StandardKey.Print`), hogy a kettő ne csúszhasson el.
    Shortcut {
        objectName: "shortcutPrint"
        sequence: "Ctrl+P"
        enabled: bar.photoActionsEnabled
        onActivated: bar.printRequested()
    }

    Menu {
        title: qsTr("&File")
        PicasaMenuItem {
            objectName: "menuFileNewAlbum"
            text: qsTr("New Album...") + "\tCtrl+N"
            placeholder: true
        }
        // ⚠️ #1200: ez NEM külön funkció és NEM mappaválasztó — az
        // eredetiben EZ A MENÜPONT nyitja meg a Mappakezelőt:
        // `eMenuFile::ID_TOOLS_INCLUDEEXCLUDEFOLDERS` (`stringres` 2648.)
        // → parancs `0x9caa` → `0x005cb990` szétosztó → `0x005ce590`.
        //
        // Korábban fordítva volt: a menüpont inaktív (placeholder), a
        // funkciót pedig egy gomb végezte magában a párbeszédben.
        MenuItem {
            objectName: "menuFileAddFolder"
            text: qsTr("Add Folder to Picasa...")
            onTriggered: bar.folderManagerRequested()
        }
        PicasaMenuItem { text: qsTr("Add File to Picasa...") + "\tCtrl+O"; placeholder: true }
        PicasaMenuItem { text: qsTr("Import From...") + "\tCtrl+M"; placeholder: true }
        // hiányzott (#324 audit): a Google Fotókból importálás menüpontja
        PicasaMenuItem { text: qsTr("Import From Google Photos..."); placeholder: false; retired: true }  // #638
        MenuSeparator {}
        // hiányzott (#324 audit): fájl(ok) megnyitása a szerkesztőben
        PicasaMenuItem { text: qsTr("Open File(s) in Editor") + "\tCtrl+Shift+O"; placeholder: true }
        MenuSeparator {}
        // hiányzott (#324 audit): mappa áthelyezés a fájlműveletek csoportjában
        PicasaMenuItem { text: qsTr("Move to New Folder..."); placeholder: true }
        MenuItem {
            objectName: "menuFileRename"
            text: qsTr("Rename...") + "\tF2"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.renameRequested()
        }
        // #444: a nem-destruktív mentés HÁROM fokozata. A „Mentés" beégeti
        // a szerkesztéseket a fájlba (előtte biztonsági másolattal), a
        // „Visszaállítás" az eredetit hozza vissza (a szerkesztések
        // elvesznek), az „Utolsó mentés visszavonása" pedig a köztes
        // fokozat: a fájl visszaáll, de a szerkesztések MEGMARADNAK.
        MenuItem {
            objectName: "menuFileSave"
            text: qsTr("Save") + "\tCtrl+S"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.saveRequested()
        }
        MenuItem {
            objectName: "menuFileRevert"
            text: qsTr("Revert")
            // csak akkor van mit visszaállítani, ha a kép már volt mentve
            enabled: bar.photoActionsEnabled && bar.hasSavedBackup
            onTriggered: bar.revertRequested()
        }
        MenuItem {
            objectName: "menuFileUndoSave"
            text: qsTr("Undo Save")
            enabled: bar.photoActionsEnabled && bar.hasSavedBackup
            onTriggered: bar.undoSaveRequested()
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
            text: qsTr("Save As...")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.saveAsRequested()
        }
        MenuItem {
            objectName: "menuFileSaveCopy"
            text: qsTr("Save a Copy")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.saveCopyRequested()
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuFileExport"
            text: qsTr("Export Picture to Folder...") + "\tCtrl+Shift+S"
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
            text: qsTr("Delete from Disk") + "\tDelete"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.deleteRequested()
        }
        MenuSeparator {}
        // #1472: ÉLŐ tétel — a `print_controller.py` 213 sora addig
        // elérhetetlen volt, mert ez a pont helyfoglaló maradt
        MenuItem {
            objectName: "menuFilePrint"
            text: qsTr("Print...") + "\tCtrl+P"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.printRequested()
        }
        PicasaMenuItem { text: qsTr("E-Mail...") + "\tCtrl+E"; placeholder: true }
        // hiányzott (#324 audit): nyomtatott képek online rendelése
        PicasaMenuItem { text: qsTr("Order Prints..."); placeholder: false; retired: true }  // #638
        MenuSeparator {}
        // #1527: a Fájl menü zárótétele. A jegy „nincs a menüben"-ként
        // írta le — MÉRVE megvolt (2026-08-24), csak `objectName` nélkül,
        // ezért egyetlen teszt sem érte el. A név most már fogja.
        MenuItem {
            objectName: "menuFileExit"
            text: qsTr("E&xit")
            onTriggered: Qt.quit()
        }
    }
    Menu {
        title: qsTr("&Edit")
        // #1475: a visszavonás a menü ÉLÉN — ide teszi az eredeti is
        // (`eMenuEdit::ID_UNDO`). A felirat megnevezi a műveletet, hogy a
        // felhasználó ne vaktában nyomja meg.
        MenuItem {
            objectName: "menuEditUndoPasteAllEffects"
            text: qsTr("Undo Paste All Effects")
            enabled: bar.canUndoPasteAllEffects
            onTriggered: bar.undoPasteAllEffectsRequested()
        }
        MenuItem {
            objectName: "menuEditUndoBatchEdit"
            text: qsTr("Undo Batch Edit")
            enabled: bar.canUndoBatchEdit
            onTriggered: bar.undoBatchEditRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): a szabvány vágólap-műveletek
        PicasaMenuItem {
            objectName: "menuEditCut"
            text: qsTr("Cut") + "\tCtrl+X"
            placeholder: true
        }
        PicasaMenuItem { text: qsTr("Copy") + "\tCtrl+C"; placeholder: true }
        PicasaMenuItem { text: qsTr("Paste") + "\tCtrl+V"; placeholder: true }
        MenuSeparator {}
        MenuItem {
            objectName: "menuEditCopyEffects"
            text: qsTr("Copy All Effects")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.copyAllEffectsRequested()
        }
        MenuItem {
            objectName: "menuEditPasteEffects"
            text: qsTr("Paste All Effects")
            enabled: bar.photoActionsEnabled && bar.hasAllEffectsClipboard
            onTriggered: bar.pasteAllEffectsRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): feliratszöveg vágólap-műveletei
        PicasaMenuItem { text: qsTr("Copy Text"); placeholder: true }
        PicasaMenuItem { text: qsTr("Paste Text"); placeholder: true }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Select All") + "\tCtrl+A"
            onTriggered: bar.selectAllRequested()
        }
        MenuItem {
            text: qsTr("Select Starred")
            onTriggered: bar.selectStarredRequested()
        }
        PicasaMenuItem { text: qsTr("Invert Selection") + "\tCtrl+I"; placeholder: true }
        MenuItem {
            text: qsTr("Clear Selection") + "\tCtrl+D"
            onTriggered: bar.clearSelectionRequested()
        }
    }
    Menu {
        title: qsTr("&View")
        MenuItem {
            objectName: "menuViewLibraryView"
            text: qsTr("Library View")
            checkable: true
            // A pipa ÁLLANDÓ (a könyvtárnézet mindig aktív, amíg az „Edit
            // View" helykitöltő). Kötés híján itt nincs mit újraértékelni,
            // ezért a kattintás imperatív `checked`-írását kézzel kell
            // visszavenni — különben egyetlen kattintás VÉGLEG leszedi.
            checked: true
            onTriggered: checked = true
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Small Thumbnails") + "\tCtrl+1"
            onTriggered: bar.thumbSizePreset(96)
        }
        MenuItem {
            text: qsTr("Normal Thumbnails") + "\tCtrl+2"
            onTriggered: bar.thumbSizePreset(144)
        }
        PicasaMenuItem { text: qsTr("Edit View") + "\tCtrl+3"; placeholder: true }
        MenuSeparator {}
        MenuItem {
            objectName: "menuViewProperties"
            text: qsTr("Properties")
            checkable: true
            checked: bar.propertiesPanelOpen
            onTriggered: bar.propertiesPanelRequested()
        }
        MenuItem {
            objectName: "menuViewTags"
            text: qsTr("Tags") + "\tCtrl+T"
            checkable: true
            checked: bar.tagsPanelOpen
            onTriggered: bar.tagsPanelRequested()
        }
        // #26: az Emberek-panel — a jobb fiók negyedik panelje
        MenuItem {
            objectName: "menuViewPeople"
            text: qsTr("People")
            checkable: true
            checked: bar.peoplePanelOpen
            onTriggered: bar.peoplePanelRequested()
        }
        MenuItem {
            objectName: "menuViewPlaces"
            text: qsTr("Places")
            checkable: true
            checked: bar.placesPanelOpen
            onTriggered: bar.placesPanelRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): a szerkesztő panel láthatóság-kapcsolója
        PicasaMenuItem { text: qsTr("Show Editing Controls"); checkable: true; placeholder: true }
        MenuItem {
            objectName: "menuViewSlideshow"
            text: qsTr("Slideshow") + "\tCtrl+4"
            onTriggered: bar.slideshowRequested()
        }
        MenuItem {
            objectName: "menuViewTimeline"
            text: qsTr("Timeline") + "\tCtrl+5"
            onTriggered: bar.timelineRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): keresési opciók
        PicasaMenuItem { text: qsTr("Search Options"); placeholder: true }
        // hiányzott (#324 audit): a jelentése a screenshotokból nem
        // egyértelmű — feltehetően mappacím nélküli indexkép-rács
        PicasaMenuItem {
            objectName: "menuViewThumbnailsOnly"
            text: qsTr("Thumbnails Only")
            checkable: true
            placeholder: true
        }
        MenuItem {
            objectName: "menuViewHidden"
            text: qsTr("Hidden Pictures")
            checkable: true
            // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
            // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
            checked: (bar.ctl && bar.ctl.showHidden !== undefined) ? bar.ctl.showHidden : false
            onTriggered: controller.toggleShowHidden()
        }
        // hiányzott (#324 audit): színprofil-kezelés kapcsoló
        PicasaMenuItem { text: qsTr("Use Color Management"); checkable: true; placeholder: true }
        MenuItem {
            // #28: opcionális sötét téma — az alapértelmezés a világos
            objectName: "menuViewDarkTheme"
            text: qsTr("Dark Theme")
            checkable: true
            checked: (bar.ctl && bar.ctl.darkTheme !== undefined) ? bar.ctl.darkTheme : false
            onTriggered: controller.toggleDarkTheme()
        }
        MenuSeparator {}
        // #1575: a Megjelenítési mód almenü — 11 tétel + 4 elválasztó
        // (15 rekord), a `docs/specs/picasa-megjelenitesi-modok.md` 1.
        // szakaszának SORRENDJÉBEN. A tartalom a binárisból mérve
        // (`0x0055ab62`–`0x0055abd4`); a korábbi „a screenshotokból nem
        // derül ki" komment 2026-08-27 óta elavult.
        //
        // Mind a tizenegy EGYETLEN kizáró csoport tagja (mérve,
        // `0x00575670`) — kapcsoló egy sincs köztük, tehát a
        // „Túlcsordult képpontok" és a „Projektor mód" sem kombinálható a
        // gammákkal. A pipa ezért végig a `bar.ctl.displayMode`-ra köt.
        //
        // ⚠️ RÁDIÓ-CSAPDA (ld. a `Thumbnail Caption` alatti magyarázatot és
        // a #1464/#1468-at): a valódi kattintás előbb IMPERATÍVAN átbillenti
        // a `checked`-et, és a `setDisplayMode` azonos értéknél
        // SZÁNDÉKOSAN nem jelez — a kötés tehát magától soha nem értékelődne
        // újra. Ezért minden tétel a jelzés után VISSZAKÖTI a `checked`-et.
        //
        // A VÁZ szintjén mind a tizenegy MŰKÖDIK: pipázódik, és a módot
        // beállítja a vezérlőn. A képpont-hatásuk külön jegyeké
        // (#1576/#1577/#1578); a `24 bites` és — 24 bites képernyőn — az
        // `Automatikus` az eredetiben is no-op.
        //
        // A `&`-gyorsítóbetűket a spec 1. szakasza tartalmazza; ide
        // SZÁNDÉKOSAN nem kerültek be: ebben a fájlban ma csak a hét
        // FŐMENÜ-cím visel mnemonikot, a 130+ tétel egyike sem, és egyetlen
        // almenüt kiemelni következetlenséget szülne. Ez külön jegy dolga.
        Menu {
            objectName: "menuViewDisplayMode"
            title: qsTr("Display Mode")
            MenuItem {
                objectName: "menuViewDisplayModeAuto"
                text: qsTr("Automatic")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "auto"
                onTriggered: {
                    controller.setDisplayMode("auto")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "auto"
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuViewDisplayModeNormal"
                text: qsTr("24-bit")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "normal"
                onTriggered: {
                    controller.setDisplayMode("normal")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "normal"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewDisplayMode16Bit"
                text: qsTr("16-bit (dithered)")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "dither16"
                onTriggered: {
                    controller.setDisplayMode("dither16")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "dither16"
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuViewDisplayModeRemoteDesktop"
                text: qsTr("Remote Desktop")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "rdesk"
                onTriggered: {
                    controller.setDisplayMode("rdesk")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "rdesk"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewDisplayModeLcd"
                text: qsTr("LCD Whitepoint")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "lcd"
                onTriggered: {
                    controller.setDisplayMode("lcd")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "lcd"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewDisplayModeProjector"
                text: qsTr("Projector Mode")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "projector"
                onTriggered: {
                    controller.setDisplayMode("projector")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "projector"
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuViewDisplayModeOverflow"
                text: qsTr("Show overflow pixels")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "overflow"
                onTriggered: {
                    controller.setDisplayMode("overflow")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "overflow"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewDisplayModeMacGamma"
                text: qsTr("Mac Gamma (1.6)")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "mac"
                onTriggered: {
                    controller.setDisplayMode("mac")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "mac"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewDisplayModeLinearGamma"
                text: qsTr("Linear Gamma (2.2)")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "linear"
                onTriggered: {
                    controller.setDisplayMode("linear")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "linear"
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuViewDisplayModeSepia"
                text: qsTr("Sepia")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "sepia"
                onTriggered: {
                    controller.setDisplayMode("sepia")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "sepia"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewDisplayModeBlackWhite"
                text: qsTr("Black and White")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "bw"
                onTriggered: {
                    controller.setDisplayMode("bw")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "bw"
                    })
                }
            }
        }
        // #1468: a valódi kattintás előbb IMPERATÍVAN átbillenti a `checked`-et,
        // és csak utána dördül el a `triggered`. Kizáró csoportban a MÁR AKTÍV
        // tételre kattintva a vezérlő állapota nem változik, tehát a kötés magától
        // soha nem értékelődik újra — a menü újranyitásakor egyik tételen sem
        // állna pipa. Ezért a jelzés után azonnal VISSZAKÖTJÜK a `checked`-et
        // (a #1464-ben bevezetett minta).
        //
        // Az öt felirat-mód kizáró csoport. FIGYELEM: a `setThumbCaptionMode`
        // ma FELTÉTEL NÉLKÜL jelez (`statusChanged.emit()`), ezért a hiba itt
        // épp nem látszik — ez azonban a setter véletlen mellékhatása, nem
        // szerződés. A visszakötés ettől függetlenné teszi a menüt.
        Menu {
            objectName: "menuViewThumbnailCaption"
            title: qsTr("Thumbnail Caption")
            MenuItem {
                objectName: "menuViewThumbCaptionNone"
                text: qsTr("None")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "none"
                onTriggered: {
                    controller.setThumbCaptionMode("none")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.thumbCaptionMode === "none"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewThumbCaptionFilename"
                text: qsTr("Filename")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "filename"
                onTriggered: {
                    controller.setThumbCaptionMode("filename")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.thumbCaptionMode === "filename"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewThumbCaptionCaption"
                text: qsTr("Caption")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "caption"
                onTriggered: {
                    controller.setThumbCaptionMode("caption")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.thumbCaptionMode === "caption"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewThumbCaptionTags"
                text: qsTr("Tags")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "tags"
                onTriggered: {
                    controller.setThumbCaptionMode("tags")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.thumbCaptionMode === "tags"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewThumbCaptionResolution"
                text: qsTr("Resolution")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "resolution"
                onTriggered: {
                    controller.setThumbCaptionMode("resolution")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.thumbCaptionMode === "resolution"
                    })
                }
            }
        }
        // #1454: a `Nézet ▸ Mappanézet` az eredetiben NEM rendez — a bal
        // hasáb GYÖKERÉT és HIERARCHIÁJÁT állítja. Korábban itt a
        // `Mappa ▸ Sort By` szó szerinti másolata állt, ugyanazzal a
        // `folderSort` bekötéssel; a rendezés oda (és az indexkép-helyi
        // menübe) tartozik, ide a szerkezet.
        //
        // A pipa-logika mérve (`0x00574b70`, `docs/specs/picasa-mappanezet.md`
        // 3.): az első kettő EGYETLEN bájt két állapota, tehát kizáró pár;
        // az „Egyszerűsített fanézet" ettől FÜGGETLEN, tartós kapcsoló.
        // A négy gyökér (Sajátgép / Képek / Dokumentumok / Asztal) külön
        // jegy (#1407), ezért itt még nem szerepel.
        Menu {
            id: folderViewMenu
            objectName: "menuViewFolderView"
            title: qsTr("Folder View")
            // A vezérlő állapota EGY helyen — a tételek pipái ezt olvassák,
            // és a kattintás utáni visszakötés is erre hivatkozik.
            readonly property bool treeMode:
                (bar.folderViewCtl && bar.folderViewCtl.treeView !== undefined)
                    ? bar.folderViewCtl.treeView : false
            readonly property bool simplifiedMode:
                (bar.folderViewCtl && bar.folderViewCtl.simplified !== undefined)
                    ? bar.folderViewCtl.simplified : false

            // MÉRT buktató (#1454): a valódi kattintás IMPERATÍVAN
            // átbillenti a `checked`-et, MIELŐTT a `triggered` eldördülne.
            // Ha a felhasználó a MÁR aktív tételre kattint, a vezérlő
            // állapota nem változik, a kötés tehát nem értékelődik újra —
            // és a menü újranyitásakor EGYIK tételen sem lenne pipa. Ezért
            // a jelzés után azonnal visszakötjük a `checked`-et.
            MenuItem {
                objectName: "menuViewFlatFolderView"
                text: qsTr("Flat Folder View")
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
                text: qsTr("Tree View")
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
            MenuItem {
                objectName: "menuViewSimplifiedTreeView"
                text: qsTr("Simplified Tree View")
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
    }
    Menu {
        title: qsTr("F&older")
        PicasaMenuItem { text: qsTr("Edit Description..."); placeholder: true }
        MenuItem {
            objectName: "menuFolderSlideshow"
            text: qsTr("View Slideshow") + "\tCtrl+4"
            onTriggered: bar.slideshowRequested()
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Refresh Thumbnails")
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
        Menu {
            objectName: "menuFolderSortBy"
            title: qsTr("Sort By")
            MenuItem {
                objectName: "menuFolderSortByDate"
                text: qsTr("Sort by creation date")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "date"
                onTriggered: {
                    controller.setFolderSort("date")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.folderSort === "date"
                    })
                }
            }
            MenuItem {
                objectName: "menuFolderSortByChanged"
                text: qsTr("Sort by recent changes")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "changed"
                onTriggered: {
                    controller.setFolderSort("changed")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.folderSort === "changed"
                    })
                }
            }
            MenuItem {
                objectName: "menuFolderSortBySize"
                text: qsTr("Sort by size")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "size"
                onTriggered: {
                    controller.setFolderSort("size")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.folderSort === "size"
                    })
                }
            }
            MenuItem {
                objectName: "menuFolderSortByName"
                text: qsTr("Sort by name")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "name"
                onTriggered: {
                    controller.setFolderSort("name")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.folderSort === "name"
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuFolderSortReverse"
                text: qsTr("Reverse sort")
                checkable: true
                checked: (bar.ctl && bar.ctl.folderSortReverse !== undefined)
                    ? bar.ctl.folderSortReverse : false
                onTriggered: controller.toggleFolderSortReverse()
            }
        }
        MenuSeparator {}
        // hiányzott (#324 audit): mappa szintű elrejtés/megjelenítés — más,
        // mint a Nézet ▸ Rejtett képek (kép-szintű) kapcsoló
        PicasaMenuItem { text: qsTr("Hide"); placeholder: true }
        PicasaMenuItem { text: qsTr("Show"); placeholder: true }
        MenuSeparator {}
        // hiányzott (#324 audit)
        // #1472: SZÁNDÉKOSAN marad helyfoglaló. Ez KONTAKTLAP (több
        // bélyegkép EGY oldalon), a `print_controller.py` viszont egy
        // képet tesz egy oldalra — mögötte nincs motor. Élővé téve a
        // felhasználó képenként egy teli lapot kapna, ami rosszabb a
        // szürke tételnél. A kontaktlap külön jegy (`print.fen` /
        // `reviewprint.fen` sablonrendszer).
        PicasaMenuItem { text: qsTr("Print Thumbnails...") + "\tCtrl+Shift+P"; placeholder: true }
        MenuItem {
            objectName: "menuFolderWebExport"
            text: qsTr("Export as HTML Page...")
            onTriggered: bar.webExportRequested()
        }
        MenuSeparator {}
        PicasaMenuItem { text: qsTr("Locate on Disk") + "\tCtrl+Enter"; placeholder: true }
        PicasaMenuItem { text: qsTr("Remove from Picasa..."); placeholder: true }
        MenuSeparator {}
        // hiányzott (#324 audit): mappa áthelyezése/törlése a lemezen
        PicasaMenuItem { text: qsTr("Move..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Delete..."); placeholder: true }
    }
    Menu {
        title: qsTr("&Picture")
        PicasaMenuItem { text: qsTr("View and Edit") + "\tCtrl+3"; placeholder: true }
        // #425 (K.1 szakasz, ui-audit-menus.md): az almenü teljes tartalma
        // az `eMenuPicture` osztályból ismert — a kijelölt N kép
        // MINDEGYIKÉRE egyszerre alkalmazott egykattintásos effekt
        // (`controller.applyEffectMany`, `batch_effect_controller`).
        Menu {
            objectName: "menuPictureBatchEdit"
            title: qsTr("Batch Edit")
            enabled: bar.photoActionsEnabled
            MenuItem {
                objectName: "menuBatchAutoContrast"
                text: qsTr("Auto Contrast")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("autolight")
            }
            MenuItem {
                objectName: "menuBatchAutoColor"
                text: qsTr("Auto Color")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("autocolor")
            }
            MenuItem {
                objectName: "menuBatchAutoRedeye"
                text: qsTr("Auto Redeye Fix")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("redeye")
            }
            MenuItem {
                objectName: "menuBatchEnhance"
                text: qsTr("I'm Feeling Lucky")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("enhance")
            }
            MenuItem {
                objectName: "menuBatchSharpen"
                text: qsTr("Sharpen")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("unsharp")
            }
            MenuItem {
                objectName: "menuBatchFilmGrain"
                text: qsTr("Film Grain")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("grain2")
            }
            MenuItem {
                objectName: "menuBatchWarmify"
                text: qsTr("Warmify")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("warm")
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuBatchRotateRight"
                text: qsTr("Rotate Right")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("rotate_cw")
            }
            MenuItem {
                objectName: "menuBatchRotateLeft"
                text: qsTr("Rotate Left")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("rotate_ccw")
            }
            MenuSeparator {}
            // #425 5. pont: a `docs/specs/` a szöveg-overlay index-
            // lefedettségét nem dokumentálja (van-e a kijelölésben szöveg-
            // réteges kép) — a feltételes engedélyezéshez szükséges adat
            // jelenleg nincs meg olcsón, ezért egyelőre placeholder
            // (ld. `batch_effect_controller` modul-docstring).
            PicasaMenuItem { text: qsTr("Show Text"); placeholder: true }
            PicasaMenuItem { text: qsTr("Hide Text"); placeholder: true }
        }
        // #465 3. pont: korábban placeholder — a kijelölt kép(ek) teljes
        // szerkesztési láncát törli, megerősítéssel (Main.qml)
        MenuItem {
            objectName: "menuPictureUndoAllEdits"
            text: qsTr("Undo All Edits")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.undoAllEditsRequested()
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuPictureHide"
            text: qsTr("Hide")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.hideToggleRequested()
        }
        // hiányzott (#324 audit): arc-négyzetek pozíciójának visszaállítása
        // (3. fázis, arcfelismerés-előkészítés)
        PicasaMenuItem { text: qsTr("Reset Face Positions"); placeholder: true }
        MenuItem {
            objectName: "menuPictureProperties"
            text: qsTr("Properties") + "\tAlt+Enter"
            onTriggered: bar.propertiesPanelRequested()
        }
    }
    Menu {
        title: qsTr("&Create")
        // hiányzott (#324 audit)
        PicasaMenuItem { text: qsTr("Set as Desktop Background..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Make a Poster..."); placeholder: true }
        MenuItem {
            objectName: "menuCreateCollage"
            text: qsTr("Picture Collage...")
            enabled: bar.createActionsEnabled
            onTriggered: bar.collageRequested()
        }
        // hiányzott (#324 audit): OS-integrációs funkciók
        PicasaMenuItem { text: qsTr("Add to Screensaver..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Make a Gift CD..."); placeholder: true }
        // #324 audit („eltérő"): eredetiben almenü — a valódi (működő)
        // filmkészítés a submenu egyetlen tételeként maradt életben
        Menu {
            title: qsTr("Movie")
            // #922: az ALMENÜ is kapuz — a benne lévő tétel hiába él, ha a
            // szülő szürke. A film ugyanúgy a tálcáról is dolgozik (#455).
            enabled: bar.createActionsEnabled
            MenuItem {
                objectName: "menuCreateMovie"
                text: qsTr("New Movie...")
                enabled: bar.createActionsEnabled
                onTriggered: bar.movieRequested()
            }
        }
        // hiányzott (#324 audit)
        PicasaMenuItem { text: qsTr("Publish to Blogger..."); placeholder: false; retired: true }  // #638
    }
    Menu {
        title: qsTr("&Tools")
        MenuItem {
            text: qsTr("Folder Manager...")
            onTriggered: bar.folderManagerRequested()
        }
        // hiányzott (#324 audit) — az auditban jelzett screenshot-időpontban
        // az eredetiben is inaktív volt
        PicasaMenuItem { text: qsTr("Upload Manager..."); placeholder: false; retired: true }  // #638
        PicasaMenuItem { text: qsTr("People Manager..."); placeholder: true }
        MenuSeparator {}
        MenuItem {
            objectName: "menuToolsDedup"
            text: qsTr("Find Duplicates...")
            onTriggered: bar.dedupRequested()
        }
        // #1473: az arckeresés a duplikátum-kereső mellé kerül, mert
        // ugyanaz a fajta munka: az egész könyvtárat végigolvasó, hosszú,
        // megszakítható keresés saját ablakkal. A tétel MINDIG él — ha a
        // modell hiányzik, azt a megnyíló ablak MONDJA MEG; egy szürke
        // menüpont nem tudja megmagyarázni magát (néma tiltás, #1473).
        MenuItem {
            objectName: "menuToolsFaceScan"
            text: qsTr("Find Faces...")
            onTriggered: bar.faceScanRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit)
        PicasaMenuItem { text: qsTr("Configure Photo Viewer..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Configure Screensaver..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Back Up Pictures..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Batch Upload..."); placeholder: false; retired: true }  // #638
        PicasaMenuItem { text: qsTr("Adjust Date and Time..."); placeholder: true }
        MenuSeparator {}
        // hiányzott (#324 audit): a tartalma a screenshotokból nem derül ki
        Menu { title: qsTr("Upload"); enabled: false }
        // #530: a Geocímke almenü élesedett — az export motorja kész
        // (export/kml.py + earth.py). A feliratok a bináris index szerint:
        // eMenuTools::Geotag = "&Geotag", ID_EXPORT_EARTH =
        // "Export to Google Earth File".
        Menu {
            title: qsTr("Geotag")
            MenuItem {
                objectName: "menuToolsExportEarth"
                text: qsTr("Export to Google Earth File")
                onTriggered: bar.earthExportRequested()
            }
        }
        Menu {
            title: qsTr("Experimental")
            // #368: az eredeti Picasa is a Kísérleti almenüből nyitotta
            MenuItem {
                objectName: "menuToolsMoveDatabase"
                text: qsTr("Move Database...")
                onTriggered: bar.moveDatabaseRequested()
            }
            // #449: adatbázis-tömörítés (`compacting.fen`) — az eredetiben
            // is a Kísérleti almenüben lakott, az áthelyezés mellett
            MenuItem {
                objectName: "menuToolsCompactDatabase"
                text: qsTr("Compact Database...")
                onTriggered: bar.compactDatabaseRequested()
            }
        }
        MenuSeparator {}
        PicasaMenuItem { text: qsTr("Configure Buttons..."); placeholder: true }
        MenuSeparator {}
        // #333: nyelvválasztás — alapértelmezés az angol, a magyar
        // választható; a döntés a QSettings-ben marad. A #305-ös null-őr
        // kötelező: a controller a QML-engine leépítésekor null lehet.
        // #1468: a valódi kattintás előbb IMPERATÍVAN átbillenti a `checked`-et,
        // és csak utána dördül el a `triggered`. Kizáró csoportban a MÁR AKTÍV
        // tételre kattintva a vezérlő állapota nem változik, tehát a kötés magától
        // soha nem értékelődik újra — a menü újranyitásakor egyik tételen sem
        // állna pipa. Ezért a jelzés után azonnal VISSZAKÖTJÜK a `checked`-et
        // (a #1464-ben bevezetett minta).
        //
        // Itt a hiba MÉRHETŐ volt: a `LanguageController.setLanguage` azonos
        // értéknél szándékosan NEM jelez, tehát a már aktív nyelvre kattintva
        // mindkét pipa eltűnt.
        Menu {
            objectName: "menuToolsLanguage"
            title: qsTr("Language")
            MenuItem {
                objectName: "menuLanguageEnglish"
                text: qsTr("English")
                checkable: true
                checked: controller ? controller.language === "en" : true
                onTriggered: {
                    if (controller) controller.setLanguage("en")
                    checked = Qt.binding(function () {
                        return controller ? controller.language === "en" : true
                    })
                }
            }
            MenuItem {
                objectName: "menuLanguageHungarian"
                text: qsTr("Hungarian")
                checkable: true
                checked: controller ? controller.language === "hu" : false
                onTriggered: {
                    if (controller) controller.setLanguage("hu")
                    checked = Qt.binding(function () {
                        return controller ? controller.language === "hu" : false
                    })
                }
            }
        }
        MenuSeparator {}
        // #350: az OptionsDialog.qml megépült (9/8 fülős options.fen
        // paritás) — a jelzés itt fut ki, a dialógus példányosítása és a
        // signal bekötése a Main.qml-ben (forró fájl) az integrátoré
        MenuItem {
            objectName: "menuToolsOptions"
            text: qsTr("Options...")
            onTriggered: bar.optionsRequested()
        }
    }
    Menu {
        title: qsTr("&Help")
        PicasaMenuItem { text: qsTr("Help Contents and Index") + "\tF1"; placeholder: true }
        PicasaMenuItem { text: qsTr("Keyboard Shortcuts"); placeholder: true }
        MenuSeparator {}
        // hiányzott (#324 audit): web-linkek
        PicasaMenuItem { text: qsTr("Picasa Forums"); placeholder: false; retired: true }  // #638
        PicasaMenuItem { text: qsTr("Online Information"); placeholder: false; retired: true }  // #638
        PicasaMenuItem { text: qsTr("Product Release Notes"); placeholder: false; retired: true }  // #638
        MenuSeparator {}
        PicasaMenuItem { text: qsTr("Privacy Policy"); placeholder: false; retired: true }  // #638
        PicasaMenuItem { text: qsTr("Terms of Service"); placeholder: false; retired: true }  // #638
        MenuSeparator {}
        PicasaMenuItem { text: qsTr("Check for Updates"); placeholder: true }
        MenuSeparator {}
        MenuItem {
            objectName: "menuHelpPerfMonitor"
            text: qsTr("Performance Monitor")
            checkable: true
            checked: (bar.ctl && bar.ctl.perfMonitorEnabled !== undefined)
                ? bar.ctl.perfMonitorEnabled : false
            onTriggered: controller.togglePerfMonitor()
        }
        MenuItem {
            text: qsTr("About PicasaPy")
            onTriggered: bar.aboutRequested()
        }
    }
}
