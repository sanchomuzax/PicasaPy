import QtQuick

// A főablak gyorsbillentyűi és a Súgó billentyűlistájának adatforrása.
Item {
    id: keyboardShortcuts
    required property var hostWindow
    required property var hostController
    required property var hostDocumentTabStrip
    required property var hostExportDialogs
    required property var hostFileOpsController
    required property var hostFileOpsDialogs
    required property var hostHelpDialog
    required property var hostPhotoViewer
    required property var hostPicasaMenuBar
    required property var hostSaveDialogs
    required property var hostSlideshow
    required property var hostTrayBar

    // A régi Main.qml-azonosító továbbra is elérhető a főablakban.
    property alias shortcutSave: shortcutSaveObject


    // #2054: a súgó billentyűi. Az F1 a MÉRT eredeti gyorsbillentyű (a
    // `SHORTCUTS.xml`-ben a *Help Contents and Index* `VK_F1`, módosító
    // nélkül); a Shift+F1 a MIÉNK — az eredeti táblájában nincs, a
    // súgó maga is új.
    //: #2163: az eredeti könyvtárnézeti kezelője (`0x005e60d0`) 34
    //: billentyűt kezel; ez a három a leképezhetők közül való.
    Shortcut {
        id: shortcutToggleRightDrawer
        objectName: "toggleRightDrawerShortcut"
        sequence: "Ctrl+0"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        //: `thumbui/toggle_right_drawer` (`0x005e6206`)
        onActivated: hostWindow.billentsdAFiokot()
    }

    Shortcut {
        id: shortcutSearch
        objectName: "searchShortcut"
        sequence: "Ctrl+F"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        //: `searchcontainer/searchbutton` (`0x005e63bb`) — az eredetiben a
        //: keresőgombot kattintja; nálunk a keresőmező a gomb szerepét is
        //: viszi, ezért oda megy a fókusz.
        onActivated: hostWindow.fokuszAKeresore()
    }

    Shortcut {
        id: shortcutSearchF3
        objectName: "searchF3Shortcut"
        sequence: "F3"
        //: A keresősáv a nézőben nincs jelen (ld. `fokuszAKeresore`), ezért
        //: az F3 a könyvtári őrön marad; diavetítés alatt nem fut.
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
                 && !hostWindow.slideshowRunning
        //: #4600: `0x005e69a4` — módosító nélküli ág, ugyanaz a
        //: `searchcontainer/searchbutton`, mint a `Ctrl+F`-é.
        onActivated: hostWindow.fokuszAKeresore()
    }

    Shortcut {
        id: shortcutStarToggle
        objectName: "starToggleShortcut"
        sequence: "F4"
        //: A kezelő a könyvtárban ÉS a szerkesztőben közös (spec 10.11/10.13),
        //: ezért a nézőben is él; a gomb saját őrét a `kapcsoldACsillagot` adja.
        enabled: !hostWindow._szovegmezoneVanFokusz && !hostWindow.slideshowRunning
        //: #4600: `0x005e696c` — a `thumbui/startoggle`-t kattintja, ha az
        //: nem tiltott; a tálca gombja ugyanezt a kijelölést/nézőt követi.
        onActivated: hostTrayBar.kapcsoldACsillagot()
    }

    Shortcut {
        id: shortcutRefreshCurrentFolder
        objectName: "refreshCurrentFolderShortcut"
        sequence: "F5"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
                 && hostDocumentTabStrip.libraryActive
                 && hostController && hostController.currentFolder.length > 0
        //: #4697: a mért eredeti F5-ág a mappa frissítési jelzőjét állítja
        //: (`picasa-gyorsbillentyuk.md`, 10.10); az idle út utána frissíti
        //: a listát. A mappapontos szinkron a lemez változásait is felveszi,
        //: majd a syncFinished meglévő útja újratölti a nézetet és a
        //: keresési állapotot. Ez nem teljes újraolvasás (`hostController.rescan()`).
        onActivated: hostController.resyncFolder(hostController.currentFolder)
    }

    Shortcut {
        id: shortcutTagsPanelAlt
        objectName: "tagsPanelAltShortcut"
        sequence: "Ctrl+K"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        //: Az eredetiben UGYANAZ az ág, mint a `Ctrl+T`-é (`0x005e650e`).
        onActivated: hostWindow.valtsFiokLapot("tags")
    }

    Shortcut {
        id: shortcutEditView
        objectName: "editViewShortcut"
        sequence: "Ctrl+3"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        //: `thumbui/fullview` (`0x005e624f`) — Nézet ▸ Szerkesztési nézet
        //: (`cmd 0x9c8f`) és Kép ▸ Megjelenítés és szerkesztés (`cmd 0x9ca0`)
        //: ugyanezen a billentyűn (a lap 10.3 és a keymap 21. rekesze).
        onActivated: hostWindow.nezdEsSzerkeszd()
    }

    Shortcut {
        id: shortcutDuplicateSearch
        objectName: "dupeSearchShortcut"
        sequence: "Ctrl+F6"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        //: `searchoptions/dupesearch` (`0x005e62bb`) — ugyanaz a
        //: másodpéldány-MÓD, amit a menüparancs kapcsol (#1398).
        onActivated: hostWindow.masodpeldanyokMutatasa()
    }

    Shortcut {
        id: shortcutFindSimilar
        objectName: "findSimilarShortcut"
        sequence: "Ctrl+F7"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        //: `searchoptions/loadsim` (`0x005e62e8`, azonosító `0x15`).
        onActivated: hostWindow.keressHasonlot()
    }

    Shortcut {
        id: shortcutClearSimilar
        objectName: "clearSimilarShortcut"
        sequence: "Ctrl+F8"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        //: `searchoptions/clearsim` (`0x005e631d`, azonosító `0x16`).
        onActivated: hostWindow.torolAHasonlosagMintat()
    }

    Shortcut {
        id: shortcutBatchBlackWhite
        objectName: "batchBwShortcut"
        sequence: "Ctrl+Shift+B"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        //: `0x005fe370(panel, "bw")` (`0x005e6370`) — a fekete-fehér szűrő a
        //: KIJELÖLÉSRE. Az eredetiben ehhez nincs kiírt menütétel (keymap
        //: 31.), a billentyű mégis él.
        onActivated: hostWindow.kotegEffekt("bw")
    }

    Shortcut {
        id: shortcutBatchEnhance
        objectName: "batchEnhanceShortcut"
        sequence: "Ctrl+Shift+E"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        //: `0x005fe370(panel, "enhance")` (`0x005e638b`) — a „Jó napom van"
        //: (keymap 32.) a kijelölésre; ugyanaz az út, mint a
        //: Köteg-szerkesztés menütételé.
        onActivated: hostWindow.kotegEffekt("enhance")
    }

    Shortcut {
        id: shortcutHelp
        objectName: "helpShortcut"
        sequence: "F1"
        enabled: !hostWindow._szovegmezoneVanFokusz
                 && !hostWindow._kulonAblakosParbeszedNyitva
        onActivated: hostHelpDialog.ensure().nyisdMeg("")
    }

    Shortcut {
        id: shortcutHelpContext
        objectName: "helpContextShortcut"
        sequence: "Shift+F1"
        enabled: !hostWindow._szovegmezoneVanFokusz
                 && !hostWindow._kulonAblakosParbeszedNyitva
        //: A mutató alatti elem súgója. A leképezés a `helpTopic`
        //: tulajdonságon át megy; ha a mutató alatt egyik ős sem
        //: deklarál ilyet, a FŐOLDAL nyílik — néma kudarc nincs.
        //:
        //: #3463: amíg a főablak rétegében MODÁLIS párbeszéd áll nyitva, a
        //: Qt ezt a gyorsbillentyűt letiltja — ezért a témát deklaráló
        //: réteg-párbeszédek maguk is hordoznak egy Shift+F1-et, CSAK
        //: nyitott állapotban, a SAJÁT fejezetükkel (`nyisdASugot`).
        onActivated: hostWindow.nyisdASugot(hostWindow.helpTopicUnderCursor())
    }


    Shortcut {
        id: shortcutSelectAll
        sequence: "Ctrl+A"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        onActivated: hostWindow.selectAll()
    }

    Shortcut {
        id: shortcutClearSelection
        sequence: "Ctrl+D"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        onActivated: hostWindow.clearSelection()
    }

    Shortcut {
        id: shortcutInvertSelection
        sequence: "Ctrl+I"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        onActivated: hostWindow.invertSelection()
    }

    // #444: „Mentés" — a Fájl menü ígéri a Ctrl+S-t, tehát élnie is kell
    // (a menü-audit teszt épp ezt kéri számon). Kijelölés nélkül nem tesz
    // semmit: a `openSave` üres listára visszatér.
    Shortcut {
        id: shortcutSaveObject
        objectName: "shortcutSave"
        sequence: "Ctrl+S"
        enabled: !hostWindow._szovegmezoneVanFokusz
                 && hostWindow.muveletiCelbanVanMentetlenSzerkesztes
        onActivated: hostSaveDialogs.ensure().openSave(hostWindow.photoActionRows())
    }


    Shortcut {
        // A `StandardKey.Copy` linuxon ugyanez, de a menü-audit a
        // szekvenciát SZÖVEGES alakban keresi — és joggal: a menü szó
        // szerint Ctrl+C-t hirdet, tehát az ígéret is szó szerinti.
        // (⚠️ A komment maga sem tartalmazhatja a keresett mintát: az
        // első változatom épp ezzel vezette félre a mérést.)
        id: shortcutCopyFiles
        objectName: "shortcutCopyFiles"
        sequence: "Ctrl+C"
        enabled: !hostWindow._szovegmezoneVanFokusz
                 && hostWindow.photoActionRows().length > 0
        onActivated: hostFileOpsController.copyFilesToClipboard(
            hostWindow.photoActionPaths())
    }

    Shortcut {
        id: shortcutCutFiles
        objectName: "shortcutCutFiles"
        sequence: "Ctrl+X"
        enabled: !hostWindow._szovegmezoneVanFokusz
                 && hostWindow.photoActionRows().length > 0
        onActivated: hostFileOpsController.cutFilesToClipboard(
            hostWindow.photoActionPaths())
    }


    Shortcut {
        //: #1526: a Beillesztés billentyűje — ugyanaz a fókusz-kapu, mint a
        //: másoláson: szövegmezőben a mezőé a billentyű (különben átnevezés
        //: közben nem lehetne beilleszteni a szövegbe).
        id: shortcutPasteFiles
        objectName: "shortcutPasteFiles"
        sequence: "Ctrl+V"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        onActivated: hostWindow.beillesztAVagolaprol()
    }

    Shortcut {
        id: shortcutRotateRight
        sequence: "Ctrl+R"
        enabled: !hostWindow._szovegmezoneVanFokusz
        onActivated: {
            var row = hostWindow.rotateTargetRow()
            if (row >= 0) hostController.rotateRight(row)
        }
    }

    Shortcut {
        id: shortcutRotateLeft
        sequence: "Ctrl+Shift+R"
        enabled: !hostWindow._szovegmezoneVanFokusz
        onActivated: {
            var row = hostWindow.rotateTargetRow()
            if (row >= 0) hostController.rotateLeft(row)
        }
    }

    Shortcut {
        id: shortcutFlipHorizontal
        objectName: "flipHorizontalShortcut"
        sequence: "Ctrl+Shift+H"
        enabled: !hostWindow._szovegmezoneVanFokusz
        onActivated: hostController.flipHorizontalMany(hostWindow.tukrozesiSorok())
    }

    Shortcut {
        id: shortcutFlipVertical
        objectName: "flipVerticalShortcut"
        sequence: "Ctrl+Shift+V"
        enabled: !hostWindow._szovegmezoneVanFokusz
        onActivated: hostController.flipVerticalMany(hostWindow.tukrozesiSorok())
    }


    // #8: Ctrl+4 — diavetítés (Picasa-billentyű)
    Shortcut {
        id: shortcutSlideshow
        sequence: "Ctrl+4"
        enabled: !hostWindow._szovegmezoneVanFokusz
        onActivated: hostWindow.startSlideshow(-1)
    }

    // #12: Ctrl+T — Címkék-panel (Picasa-billentyű); a könyvtár-nézetben él
    Shortcut {
        id: shortcutTagsPanel
        sequence: "Ctrl+T"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        onActivated: if (!hostWindow.viewerOpen)
                         // #1773: a billentyű BILLENT (a menütétel nem) —
                         // a Ctrl+T nyitja, és zárja is a fiókot
                         hostWindow.tagsPanelOpen ? hostWindow.ureseidAFiokot()
                                              : hostWindow.valtsFiokLapot("tags")
    }

    // #13: Alt+Enter — Tulajdonságok-panel (Picasa-billentyű)
    Shortcut {
        id: shortcutPropertiesPanel
        sequence: "Alt+Return"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        onActivated: if (!hostWindow.viewerOpen)
                         hostWindow.propertiesPanelOpen
                             ? hostWindow.ureseidAFiokot()
                             : hostWindow.valtsFiokLapot("properties")
    }

    Shortcut {
        id: shortcutViewerFullscreen
        objectName: "viewerFullscreenShortcut"
        sequence: "F11"
        enabled: hostWindow.viewerOpen && !hostSlideshow.visible
        onActivated: hostWindow.toggleViewerFullscreen()
    }


    // Az Időrend kijelölés nélkül is megnyitható.
    Shortcut {
        sequence: "Ctrl+5"
        enabled: !hostWindow._szovegmezoneVanFokusz && !hostWindow.viewerOpen && !hostSlideshow.visible
        onActivated: hostWindow.toggleTimeline()
    }

    // Picasa: F2 = átnevezés, Ctrl+Shift+S = exportálás mappába
    Shortcut {
        id: shortcutRename
        sequence: "F2"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        onActivated: if (!hostWindow.viewerOpen && hostWindow.photoActionRows().length > 0)
                         hostFileOpsDialogs.ensure().openRenameMany(
                             hostWindow.photoActionRows())
    }

    Shortcut {
        id: shortcutExportSelection
        sequence: "Ctrl+Shift+S"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
        onActivated: if (!hostWindow.viewerOpen) hostExportDialogs.ensure().openForSelection()
    }

    // #422: a rács kontextusmenüje `Ctrl+Delete`-et hirdet a lemezről
    // törléshez (spec 3.) — a billentyű eddig nem élt, csak a Fájl menü
    // `Delete`-je (ld. ui-audit-menus.md). Mindkettő ugyanoda vezet.
    Shortcut {
        id: shortcutDeleteFromDiskGrid
        objectName: "shortcutDeleteFromDiskGrid"
        sequence: "Ctrl+Delete"
        enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
                 && hostWindow.selectedRows().length > 0
        // #1619: a `Ctrl+Delete` UGYANAZ a parancs (`0x9c9a`), csak másik
        // belépő — ezért a #1608-ban készült KÖZÖS elágazáson megy át,
        // nem másolt logikán. Albumban/Emberek-albumban eltávolít, nem
        // lemezről töröl (spec 5.); mappában változatlanul töröl.
        onActivated: hostPicasaMenuBar.activateDeleteCommand()
    }

    // #422/#4621: a nézőben `Ctrl+Delete` (#1418; a puszta `Delete` nem
    // töröl) — nézetfüggő: mappában lemezről töröl, albumban eltávolít
    Shortcut {
        id: shortcutDeleteFromDiskViewer
        objectName: "shortcutDeleteFromDiskViewer"
        // #1418: a nézőben (jobbklikk-menüs felület) `Ctrl+Delete` a helyes,
        // nem a puszta `Delete` — a #1154 mérése szerint a `0x9c9a` parancs
        // felület szerint válik szét: menüsávban `Delete`, helyi menükben
        // `Ctrl+Delete`. A korábbi `Delete` a #422 azóta felülírt feltevése
        // volt.
        sequence: "Ctrl+Delete"
        enabled: hostWindow.viewerOpen && !hostWindow._szovegmezoneVanFokusz
                 && hostPhotoViewer._kijeloltSort() >= 0
        // #4621: a nézőben is a KÖZÖS, nézetfüggő elágazáson megy át
        // (albumból megnyitott képen eltávolít, nem lemezről töröl)
        onActivated: hostPicasaMenuBar.activateDeleteCommand()
    }


    Shortcut {
        id: shortcutOpenInEditor
        objectName: "openInEditorShortcut"
        sequence: "Ctrl+Shift+O"
        enabled: !!hostPicasaMenuBar && hostPicasaMenuBar.photoActionsEnabled
                 && !hostWindow._szovegmezoneVanFokusz
        onActivated: hostWindow.openSelectionInDefaultEditor()
    }


    // #4329: a billentyűnek ugyanaz a kijelölési kapuja és kezelője, mint a
    // Fájl ▸ E-Mail menüpontnak.
    Shortcut {
        id: shortcutEmail
        objectName: "emailShortcut"
        sequence: "Ctrl+E"
        enabled: !!hostPicasaMenuBar && hostPicasaMenuBar.photoActionsEnabled
                 && !hostWindow._szovegmezoneVanFokusz
        onActivated: hostPicasaMenuBar.emailRequested()
    }

    // #4639: a Súgó ▸ Billentyűkódok listájának adatforrása a működő
    // Shortcut-objektumok sequence tulajdonsága. Kötésváltozás után a súgó
    // automatikusan az új értéket mutatja.
    readonly property var keyboardShortcutGroups: [
        {
            title: hostPicasaMenuBar.keyboardShortcutGroupTitles.file,
            sequences: hostPicasaMenuBar.keyboardShortcutSequences.file.concat([
                shortcutSaveObject.sequence, shortcutRename.sequence,
                shortcutExportSelection.sequence, shortcutDeleteFromDiskGrid.sequence,
                shortcutOpenInEditor.sequence, shortcutEmail.sequence
            ])
        },
        {
            title: hostPicasaMenuBar.keyboardShortcutGroupTitles.edit,
            sequences: [shortcutSelectAll.sequence, shortcutClearSelection.sequence,
                shortcutInvertSelection.sequence, shortcutCopyFiles.sequence,
                shortcutCutFiles.sequence, shortcutPasteFiles.sequence]
        },
        {
            title: hostPicasaMenuBar.keyboardShortcutGroupTitles.view,
            sequences: hostPicasaMenuBar.keyboardShortcutSequences.view.concat([
                shortcutToggleRightDrawer.sequence, shortcutSearch.sequence,
                shortcutSearchF3.sequence, shortcutStarToggle.sequence,
                shortcutTagsPanelAlt.sequence, shortcutEditView.sequence,
                shortcutDuplicateSearch.sequence, shortcutFindSimilar.sequence,
                shortcutClearSimilar.sequence, shortcutSlideshow.sequence,
                shortcutTagsPanel.sequence, shortcutPropertiesPanel.sequence,
                shortcutViewerFullscreen.sequence
            ]).concat(hostDocumentTabStrip.keyboardShortcutSequences)
                .concat(hostPhotoViewer.keyboardShortcutSequences)
        },
        {
            title: hostPicasaMenuBar.keyboardShortcutGroupTitles.folder,
            sequences: hostPicasaMenuBar.keyboardShortcutSequences.folder.concat([
                shortcutRefreshCurrentFolder.sequence
            ])
        },
        {
            title: hostPicasaMenuBar.keyboardShortcutGroupTitles.picture,
            sequences: [shortcutRotateRight.sequence, shortcutRotateLeft.sequence,
                shortcutFlipHorizontal.sequence, shortcutFlipVertical.sequence,
                shortcutBatchBlackWhite.sequence, shortcutBatchEnhance.sequence]
                .concat(hostTrayBar.keyboardShortcutSequences)
        },
        {
            title: hostPicasaMenuBar.keyboardShortcutGroupTitles.help,
            sequences: [shortcutHelp.sequence, shortcutHelpContext.sequence]
        }
    ]
}
