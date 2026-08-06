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
    // #152: „Copy/Paste All Effects" — a Beillesztés csak akkor engedélyezett,
    // ha van másolt effektlánc (a controller.hasEffectsClipboard-hoz kötve)
    property bool hasEffectsClipboard: false
    signal copyEffectsRequested()
    signal pasteEffectsRequested()

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
        MenuItem { text: qsTr("New Album...") + "\tCtrl+N"; enabled: false }
        MenuItem { text: qsTr("Add Folder to Picasa..."); enabled: false }
        MenuItem { text: qsTr("Add File to Picasa...") + "\tCtrl+O"; enabled: false }
        MenuItem { text: qsTr("Import From...") + "\tCtrl+M"; enabled: false }
        // hiányzott (#324 audit): a Google Fotókból importálás menüpontja
        MenuItem { text: qsTr("Import From Google Photos..."); enabled: false }
        MenuSeparator {}
        // hiányzott (#324 audit): fájl(ok) megnyitása a szerkesztőben
        MenuItem { text: qsTr("Open File(s) in Editor") + "\tCtrl+Shift+O"; enabled: false }
        MenuSeparator {}
        // hiányzott (#324 audit): mappa áthelyezés a fájlműveletek csoportjában
        MenuItem { text: qsTr("Move to New Folder..."); enabled: false }
        MenuItem {
            objectName: "menuFileRename"
            text: qsTr("Rename...") + "\tF2"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.renameRequested()
        }
        MenuItem { text: qsTr("Save") + "\tCtrl+S"; enabled: false }
        MenuItem { text: qsTr("Revert"); enabled: false }
        MenuSeparator {}
        // hiányzott (#324 audit): eltérő mentés-változatok
        MenuItem { text: qsTr("Save As..."); enabled: false }
        MenuItem { text: qsTr("Save a Copy"); enabled: false }
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
        MenuItem { text: qsTr("Print...") + "\tCtrl+P"; enabled: false }
        MenuItem { text: qsTr("E-Mail...") + "\tCtrl+E"; enabled: false }
        // hiányzott (#324 audit): nyomtatott képek online rendelése
        MenuItem { text: qsTr("Order Prints..."); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("E&xit"); onTriggered: Qt.quit() }
    }
    Menu {
        title: qsTr("&Edit")
        // hiányzott (#324 audit): a szabvány vágólap-műveletek
        MenuItem { text: qsTr("Cut") + "\tCtrl+X"; enabled: false }
        MenuItem { text: qsTr("Copy") + "\tCtrl+C"; enabled: false }
        MenuItem { text: qsTr("Paste") + "\tCtrl+V"; enabled: false }
        MenuSeparator {}
        MenuItem {
            objectName: "menuEditCopyEffects"
            text: qsTr("Copy All Effects")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.copyEffectsRequested()
        }
        MenuItem {
            objectName: "menuEditPasteEffects"
            text: qsTr("Paste All Effects")
            enabled: bar.photoActionsEnabled && bar.hasEffectsClipboard
            onTriggered: bar.pasteEffectsRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): feliratszöveg vágólap-műveletei
        MenuItem { text: qsTr("Copy Text"); enabled: false }
        MenuItem { text: qsTr("Paste Text"); enabled: false }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Select All") + "\tCtrl+A"
            onTriggered: bar.selectAllRequested()
        }
        MenuItem {
            text: qsTr("Select Starred")
            onTriggered: bar.selectStarredRequested()
        }
        MenuItem { text: qsTr("Invert Selection") + "\tCtrl+I"; enabled: false }
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
        MenuItem { text: qsTr("Edit View") + "\tCtrl+3"; enabled: false }
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
        MenuItem { text: qsTr("People"); enabled: false }
        MenuItem {
            objectName: "menuViewPlaces"
            text: qsTr("Places")
            checkable: true
            checked: bar.placesPanelOpen
            onTriggered: bar.placesPanelRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): a szerkesztő panel láthatóság-kapcsolója
        MenuItem { text: qsTr("Show Editing Controls"); checkable: true; enabled: false }
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
        MenuItem { text: qsTr("Search Options"); enabled: false }
        // hiányzott (#324 audit): a jelentése a screenshotokból nem
        // egyértelmű — feltehetően mappacím nélküli indexkép-rács
        MenuItem { text: qsTr("Thumbnails Only"); checkable: true; enabled: false }
        MenuItem {
            objectName: "menuViewHidden"
            text: qsTr("Hidden Pictures")
            checkable: true
            checked: bar.ctl ? bar.ctl.showHidden : false
            onTriggered: controller.toggleShowHidden()
        }
        // hiányzott (#324 audit): színprofil-kezelés kapcsoló
        MenuItem { text: qsTr("Use Color Management"); checkable: true; enabled: false }
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
        MenuItem { text: qsTr("Edit Description..."); enabled: false }
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
        MenuItem { text: qsTr("Hide"); enabled: false }
        MenuItem { text: qsTr("Show"); enabled: false }
        MenuSeparator {}
        // hiányzott (#324 audit)
        MenuItem { text: qsTr("Print Thumbnails...") + "\tCtrl+Shift+P"; enabled: false }
        MenuItem { text: qsTr("Export as HTML Page..."); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Locate on Disk") + "\tCtrl+Enter"; enabled: false }
        MenuItem { text: qsTr("Remove from Picasa..."); enabled: false }
        MenuSeparator {}
        // hiányzott (#324 audit): mappa áthelyezése/törlése a lemezen
        MenuItem { text: qsTr("Move..."); enabled: false }
        MenuItem { text: qsTr("Delete..."); enabled: false }
    }
    Menu {
        title: qsTr("&Picture")
        MenuItem { text: qsTr("View and Edit") + "\tCtrl+3"; enabled: false }
        // #324 audit („eltérő"): eredetiben almenü — a tartalma a
        // screenshotokból nem derül ki, egyelőre üres/inaktív almenü
        Menu {
            title: qsTr("Batch Edit")
            enabled: false
        }
        MenuItem { text: qsTr("Undo All Edits"); enabled: false }
        MenuSeparator {}
        MenuItem {
            objectName: "menuPictureHide"
            text: qsTr("Hide")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.hideToggleRequested()
        }
        // hiányzott (#324 audit): arc-négyzetek pozíciójának visszaállítása
        // (3. fázis, arcfelismerés-előkészítés)
        MenuItem { text: qsTr("Reset Face Positions"); enabled: false }
        MenuItem {
            objectName: "menuPictureProperties"
            text: qsTr("Properties") + "\tAlt+Enter"
            onTriggered: bar.propertiesPanelRequested()
        }
    }
    Menu {
        title: qsTr("&Create")
        // hiányzott (#324 audit)
        MenuItem { text: qsTr("Set as Desktop Background..."); enabled: false }
        MenuItem { text: qsTr("Make a Poster..."); enabled: false }
        MenuItem {
            objectName: "menuCreateCollage"
            text: qsTr("Picture Collage...")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.collageRequested()
        }
        // hiányzott (#324 audit): OS-integrációs funkciók
        MenuItem { text: qsTr("Add to Screensaver..."); enabled: false }
        MenuItem { text: qsTr("Make a Gift CD..."); enabled: false }
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
        MenuItem { text: qsTr("Publish to Blogger..."); enabled: false }
    }
    Menu {
        title: qsTr("&Tools")
        MenuItem {
            text: qsTr("Folder Manager...")
            onTriggered: bar.folderManagerRequested()
        }
        // hiányzott (#324 audit) — az auditban jelzett screenshot-időpontban
        // az eredetiben is inaktív volt
        MenuItem { text: qsTr("Upload Manager..."); enabled: false }
        MenuItem { text: qsTr("People Manager..."); enabled: false }
        MenuSeparator {}
        MenuItem {
            objectName: "menuToolsDedup"
            text: qsTr("Find Duplicates...")
            onTriggered: bar.dedupRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit)
        MenuItem { text: qsTr("Configure Photo Viewer..."); enabled: false }
        MenuItem { text: qsTr("Configure Screensaver..."); enabled: false }
        MenuItem { text: qsTr("Back Up Pictures..."); enabled: false }
        MenuItem { text: qsTr("Batch Upload..."); enabled: false }
        MenuItem { text: qsTr("Adjust Date and Time..."); enabled: false }
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
        MenuItem { text: qsTr("Configure Buttons..."); enabled: false }
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
        MenuItem { text: qsTr("Help Contents and Index") + "\tF1"; enabled: false }
        MenuItem { text: qsTr("Keyboard Shortcuts"); enabled: false }
        MenuSeparator {}
        // hiányzott (#324 audit): web-linkek
        MenuItem { text: qsTr("Picasa Forums"); enabled: false }
        MenuItem { text: qsTr("Online Information"); enabled: false }
        MenuItem { text: qsTr("Product Release Notes"); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Privacy Policy"); enabled: false }
        MenuItem { text: qsTr("Terms of Service"); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Check for Updates"); enabled: false }
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
