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
    // #368: Eszközök → Kísérleti → Adatbázis áthelyezése
    signal moveDatabaseRequested()
    signal renameRequested()
    signal exportRequested()
    // #351: Mappa → Exportálás weboldalként… (webexport.fen)
    signal webExportRequested()
    // #29: Létrehozás → Képkollázs / Mozgófilm a kijelölésből
    signal collageRequested()
    signal movieRequested()
    signal locateRequested()
    signal deleteRequested()
    signal slideshowRequested()
    // #24: Időrend nézet (Ctrl+5)
    signal timelineRequested()
    // #12: a Címkék-panel állapota kívülről kötve, a menüpont csak kér
    property bool tagsPanelOpen: false
    signal tagsPanelRequested()
    // #30: Helyek-panel (térkép)
    property bool placesPanelOpen: false
    signal placesPanelRequested()
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

    Menu {
        title: qsTr("&File")
        PicasaMenuItem {
            objectName: "menuFileNewAlbum"
            text: qsTr("New Album...") + "\tCtrl+N"
            placeholder: true
        }
        PicasaMenuItem { text: qsTr("Add Folder to Picasa..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Add File to Picasa...") + "\tCtrl+O"; placeholder: true }
        PicasaMenuItem { text: qsTr("Import From...") + "\tCtrl+M"; placeholder: true }
        // hiányzott (#324 audit): a Google Fotókból importálás menüpontja
        PicasaMenuItem { text: qsTr("Import From Google Photos..."); placeholder: true }
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
        PicasaMenuItem { text: qsTr("Save") + "\tCtrl+S"; placeholder: true }
        PicasaMenuItem { text: qsTr("Revert"); placeholder: true }
        MenuSeparator {}
        // hiányzott (#324 audit): eltérő mentés-változatok
        PicasaMenuItem { text: qsTr("Save As..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Save a Copy"); placeholder: true }
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
        PicasaMenuItem { text: qsTr("Print...") + "\tCtrl+P"; placeholder: true }
        PicasaMenuItem { text: qsTr("E-Mail...") + "\tCtrl+E"; placeholder: true }
        // hiányzott (#324 audit): nyomtatott képek online rendelése
        PicasaMenuItem { text: qsTr("Order Prints..."); placeholder: true }
        MenuSeparator {}
        MenuItem { text: qsTr("E&xit"); onTriggered: Qt.quit() }
    }
    Menu {
        title: qsTr("&Edit")
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
        MenuItem { text: qsTr("Library View"); checkable: true; checked: true }
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
        PicasaMenuItem { text: qsTr("People"); placeholder: true }
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
            checked: bar.ctl ? bar.ctl.showHidden : false
            onTriggered: controller.toggleShowHidden()
        }
        // hiányzott (#324 audit): színprofil-kezelés kapcsoló
        PicasaMenuItem { text: qsTr("Use Color Management"); checkable: true; placeholder: true }
        MenuItem {
            // #28: opcionális sötét téma — az alapértelmezés a világos
            objectName: "menuViewDarkTheme"
            text: qsTr("Dark Theme")
            checkable: true
            checked: bar.ctl ? bar.ctl.darkTheme : false
            onTriggered: controller.toggleDarkTheme()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): a tartalma a screenshotokból nem derül ki
        Menu {
            title: qsTr("Display Mode")
            enabled: false
        }
        Menu {
            title: qsTr("Thumbnail Caption")
            MenuItem {
                text: qsTr("None")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "none"
                onTriggered: controller.setThumbCaptionMode("none")
            }
            MenuItem {
                text: qsTr("Filename")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "filename"
                onTriggered: controller.setThumbCaptionMode("filename")
            }
            MenuItem {
                text: qsTr("Caption")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "caption"
                onTriggered: controller.setThumbCaptionMode("caption")
            }
            MenuItem {
                text: qsTr("Tags")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "tags"
                onTriggered: controller.setThumbCaptionMode("tags")
            }
            MenuItem {
                text: qsTr("Resolution")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "resolution"
                onTriggered: controller.setThumbCaptionMode("resolution")
            }
        }
        Menu {
            title: qsTr("Folder View")
            MenuItem {
                text: qsTr("Sort by creation date")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "date"
                onTriggered: controller.setFolderSort("date")
            }
            MenuItem {
                text: qsTr("Sort by recent changes")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "changed"
                onTriggered: controller.setFolderSort("changed")
            }
            MenuItem {
                text: qsTr("Sort by size")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "size"
                onTriggered: controller.setFolderSort("size")
            }
            MenuItem {
                text: qsTr("Sort by name")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "name"
                onTriggered: controller.setFolderSort("name")
            }
            MenuSeparator {}
            MenuItem {
                text: qsTr("Reverse sort")
                checkable: true
                checked: bar.ctl ? bar.ctl.folderSortReverse : false
                onTriggered: controller.toggleFolderSortReverse()
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
        // #324 audit („eltérő"): eredetiben aktív almenü — most valódi
        // almenü, a Nézet ▸ Mappanézet almenüvel MEGEGYEZŐ bekötéssel
        Menu {
            objectName: "menuFolderSortBy"
            title: qsTr("Sort By")
            MenuItem {
                text: qsTr("Sort by creation date")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "date"
                onTriggered: controller.setFolderSort("date")
            }
            MenuItem {
                text: qsTr("Sort by recent changes")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "changed"
                onTriggered: controller.setFolderSort("changed")
            }
            MenuItem {
                text: qsTr("Sort by size")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "size"
                onTriggered: controller.setFolderSort("size")
            }
            MenuItem {
                text: qsTr("Sort by name")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "name"
                onTriggered: controller.setFolderSort("name")
            }
            MenuSeparator {}
            MenuItem {
                text: qsTr("Reverse sort")
                checkable: true
                checked: bar.ctl ? bar.ctl.folderSortReverse : false
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
        // #324 audit („eltérő"): eredetiben almenü — a tartalma a
        // screenshotokból nem derül ki, egyelőre üres/inaktív almenü
        Menu {
            title: qsTr("Batch Edit")
            enabled: false
        }
        PicasaMenuItem { text: qsTr("Undo All Edits"); placeholder: true }
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
            enabled: bar.photoActionsEnabled
            onTriggered: bar.collageRequested()
        }
        // hiányzott (#324 audit): OS-integrációs funkciók
        PicasaMenuItem { text: qsTr("Add to Screensaver..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Make a Gift CD..."); placeholder: true }
        // #324 audit („eltérő"): eredetiben almenü — a valódi (működő)
        // filmkészítés a submenu egyetlen tételeként maradt életben
        Menu {
            title: qsTr("Movie")
            enabled: bar.photoActionsEnabled
            MenuItem {
                objectName: "menuCreateMovie"
                text: qsTr("New Movie...")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.movieRequested()
            }
        }
        // hiányzott (#324 audit)
        PicasaMenuItem { text: qsTr("Publish to Blogger..."); placeholder: true }
    }
    Menu {
        title: qsTr("&Tools")
        MenuItem {
            text: qsTr("Folder Manager...")
            onTriggered: bar.folderManagerRequested()
        }
        // hiányzott (#324 audit) — az auditban jelzett screenshot-időpontban
        // az eredetiben is inaktív volt
        PicasaMenuItem { text: qsTr("Upload Manager..."); placeholder: true }
        PicasaMenuItem { text: qsTr("People Manager..."); placeholder: true }
        MenuSeparator {}
        MenuItem {
            objectName: "menuToolsDedup"
            text: qsTr("Find Duplicates...")
            onTriggered: bar.dedupRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit)
        PicasaMenuItem { text: qsTr("Configure Photo Viewer..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Configure Screensaver..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Back Up Pictures..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Batch Upload..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Adjust Date and Time..."); placeholder: true }
        MenuSeparator {}
        // hiányzott (#324 audit): a tartalma a screenshotokból nem derül ki
        Menu { title: qsTr("Upload"); enabled: false }
        Menu { title: qsTr("Geotag"); enabled: false }
        Menu {
            title: qsTr("Experimental")
            // #368: az eredeti Picasa is a Kísérleti almenüből nyitotta
            MenuItem {
                objectName: "menuToolsMoveDatabase"
                text: qsTr("Move Database...")
                onTriggered: bar.moveDatabaseRequested()
            }
        }
        MenuSeparator {}
        PicasaMenuItem { text: qsTr("Configure Buttons..."); placeholder: true }
        MenuSeparator {}
        // #333: nyelvválasztás — alapértelmezés az angol, a magyar
        // választható; a döntés a QSettings-ben marad. A #305-ös null-őr
        // kötelező: a controller a QML-engine leépítésekor null lehet.
        Menu {
            objectName: "menuToolsLanguage"
            title: qsTr("Language")
            MenuItem {
                objectName: "menuLanguageEnglish"
                text: qsTr("English")
                checkable: true
                checked: controller ? controller.language === "en" : true
                onTriggered: if (controller) controller.setLanguage("en")
            }
            MenuItem {
                objectName: "menuLanguageHungarian"
                text: qsTr("Hungarian")
                checkable: true
                checked: controller ? controller.language === "hu" : false
                onTriggered: if (controller) controller.setLanguage("hu")
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
        PicasaMenuItem { text: qsTr("Picasa Forums"); placeholder: true }
        PicasaMenuItem { text: qsTr("Online Information"); placeholder: true }
        PicasaMenuItem { text: qsTr("Product Release Notes"); placeholder: true }
        MenuSeparator {}
        PicasaMenuItem { text: qsTr("Privacy Policy"); placeholder: true }
        PicasaMenuItem { text: qsTr("Terms of Service"); placeholder: true }
        MenuSeparator {}
        PicasaMenuItem { text: qsTr("Check for Updates"); placeholder: true }
        MenuSeparator {}
        MenuItem {
            objectName: "menuHelpPerfMonitor"
            text: qsTr("Performance Monitor")
            checkable: true
            checked: bar.ctl ? bar.ctl.perfMonitorEnabled : false
            onTriggered: controller.togglePerfMonitor()
        }
        MenuItem {
            text: qsTr("About PicasaPy")
            onTriggered: bar.aboutRequested()
        }
    }
}
