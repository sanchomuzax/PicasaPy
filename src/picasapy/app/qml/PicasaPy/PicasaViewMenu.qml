import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

PicasaMenu {
    id: menuView
    property var bar: null
    property var controllerRef:
        (typeof controller !== "undefined" && controller)
            ? controller : null
    function openFolderViewMenu(anchorItem) {
        folderViewMenu.popup(anchorItem, 0, anchorItem.height)
    }
    objectName: "menuView"
    title: qsTr("&View")
    MenuItem {
        objectName: "menuViewLibraryView"
        text: qsTr("&Library View")
        checkable: true
        // A pipa állandó. A tétel a könyvtárban inaktív, nézőben pedig
        // visszakéri a gazdától a szokásos kilépési utat. Kattintáskor a
        // Qt előbb leveszi a pipát, ezért a kezelő visszaállítja.
        enabled: bar.editorActive
        checked: true
        onTriggered: {
            checked = true
            bar.returnToLibraryRequested()
        }
    }
    MenuSeparator {}
    // #4623: a 2. csoport rádiócsoport (spec: egy pipa a háromból). A
    // pipa a gazda `thumbSize`-ából számolódik, így a csúszkától
    // állított méret is pontosan látszik. A már aktív tételre kattintva
    // a `toggle()` elveszi a pipát (#1468), ezért a kötés visszaáll.
    MenuItem {
        objectName: "menuViewSmallThumbnails"
        text: qsTr("S&mall Thumbnails") + "\tCtrl+1"
        checkable: true
        checked: !bar.editorActive && bar.thumbSize === 96
        onTriggered: {
            bar.thumbSizePreset(96)
            checked = Qt.binding(function () {
                return !bar.editorActive && bar.thumbSize === 96
            })
        }
    }
    MenuItem {
        objectName: "menuViewNormalThumbnails"
        text: qsTr("&Normal Thumbnails") + "\tCtrl+2"
        checkable: true
        checked: !bar.editorActive && bar.thumbSize === 144
        onTriggered: {
            bar.thumbSizePreset(144)
            checked = Qt.binding(function () {
                return !bar.editorActive && bar.thumbSize === 144
            })
        }
    }
    MenuItem {
        objectName: "menuViewEditView"
        text: qsTr("&Edit View") + "\tCtrl+3"
        checkable: true
        checked: bar.editorActive
        enabled: bar.libraryPhotoActionsEnabled
        onTriggered: {
            bar.viewAndEditRequested()
            checked = Qt.binding(function () {
                return bar.editorActive
            })
        }
    }
    MenuSeparator {}
    MenuItem {
        objectName: "menuViewProperties"
        text: qsTr("Properties")
        checkable: true
        checked: bar.propertiesPanelOpen
        onTriggered: {
            bar.propertiesPanelRequested()
            // #1471: a `checkable` MenuItem kattintáskor MAGA billenti
            // a `checked`-et, és ez az imperatív írás eldobja a fenti
            // kötést. A fiók-lapoknál ez látszik is: az AKTÍV lapra
            // kattintva a panel — helyesen (#1773) — nyitva marad, a
            // pipa viszont lekapcsolna. A kötés visszaállítása
            // ugyanaz a minta, mint a FolderListContextMenu.qml-ben.
            checked = Qt.binding(function () {
                return bar.propertiesPanelOpen
            })
        }
    }
    MenuItem {
        objectName: "menuViewTags"
        text: qsTr("&Tags") + "\tCtrl+T"
        checkable: true
        checked: bar.tagsPanelOpen
        onTriggered: {
            bar.tagsPanelRequested()
            // #1471: a `checkable` MenuItem kattintáskor MAGA billenti
            // a `checked`-et, és ez az imperatív írás eldobja a fenti
            // kötést. A fiók-lapoknál ez látszik is: az AKTÍV lapra
            // kattintva a panel — helyesen (#1773) — nyitva marad, a
            // pipa viszont lekapcsolna. A kötés visszaállítása
            // ugyanaz a minta, mint a FolderListContextMenu.qml-ben.
            checked = Qt.binding(function () {
                return bar.tagsPanelOpen
            })
        }
    }
    // #26: az Emberek-panel — a jobb fiók negyedik panelje
    MenuItem {
        objectName: "menuViewPeople"
        text: qsTr("People")
        checkable: true
        checked: bar.peoplePanelOpen
        onTriggered: {
            bar.peoplePanelRequested()
            // #1471: a `checkable` MenuItem kattintáskor MAGA billenti
            // a `checked`-et, és ez az imperatív írás eldobja a fenti
            // kötést. A fiók-lapoknál ez látszik is: az AKTÍV lapra
            // kattintva a panel — helyesen (#1773) — nyitva marad, a
            // pipa viszont lekapcsolna. A kötés visszaállítása
            // ugyanaz a minta, mint a FolderListContextMenu.qml-ben.
            checked = Qt.binding(function () {
                return bar.peoplePanelOpen
            })
        }
    }
    MenuItem {
        objectName: "menuViewPlaces"
        text: qsTr("&Places")
        checkable: true
        checked: bar.placesPanelOpen
        onTriggered: {
            bar.placesPanelRequested()
            // #1471: a `checkable` MenuItem kattintáskor MAGA billenti
            // a `checked`-et, és ez az imperatív írás eldobja a fenti
            // kötést. A fiók-lapoknál ez látszik is: az AKTÍV lapra
            // kattintva a panel — helyesen (#1773) — nyitva marad, a
            // pipa viszont lekapcsolna. A kötés visszaállítása
            // ugyanaz a minta, mint a FolderListContextMenu.qml-ben.
            checked = Qt.binding(function () {
                return bar.placesPanelOpen
            })
        }
    }
    MenuSeparator {}
    // #5878: a Picasa csak a szerkesztőnézetben engedte ezt a tételt;
    // könyvtárnézetben a tartósan nyitott fiók se mutasson pipát.
    // #4336: a szerkesztőnézet pipája a PhotoViewer tartós állapotát követi.
    PicasaMenuItem {
        objectName: "menuViewEditControls"
        text: qsTr("Show Edit Controls")
        placeholder: false
        checkable: true
        enabled: bar.editorActive
        checked: bar.editorActive
            && ((controllerRef && controllerRef.editorControlsVisible !== undefined)
                ? controllerRef.editorControlsVisible : true)
        onTriggered: {
            if (controllerRef && controllerRef.setEditorControlsVisible !== undefined)
                controllerRef.setEditorControlsVisible(!controllerRef.editorControlsVisible)
            checked = Qt.binding(function () {
                return bar.editorActive
                    && ((controllerRef && controllerRef.editorControlsVisible !== undefined)
                        ? controllerRef.editorControlsVisible : true)
            })
        }
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    MenuItem {
        objectName: "menuViewSlideshow"
        text: qsTr("&Slideshow") + "\tCtrl+4"
        onTriggered: bar.slideshowRequested()
    }
    // A teljes képernyős bemutató belépési pontja (#5377).
    MenuItem {
        objectName: "menuViewTimeline"
        text: qsTr("Ti&meline") + "\tCtrl+5"
        enabled: true
        onTriggered: bar.timelineRequested()
    }
    MenuSeparator {}
    // hiányzott (#324 audit): keresési opciók
    PicasaMenuItem {
        objectName: "menuViewSearchOptions"
        text: qsTr("Search &Options")
        placeholder: false
        checkable: true
        checked: bar.searchOptionsOpen
        onTriggered: {
            bar.searchOptionsToggleRequested()
            checked = Qt.binding(function() { return bar.searchOptionsOpen })
        }
    }
    // #4346: az eredeti `Show only big images` láthatósági kapcsolója.
    PicasaMenuItem {
        objectName: "menuViewThumbnailsOnly"
        text: qsTr("Small &Pictures")
        checkable: true
        placeholder: false
        // #4346: az eredeti `Show only big images` preferenciájának
        // fordított pipaállása — pipálva a kisebb képek is látszanak.
        checked: (controllerRef && controllerRef.showOnlyBigImages !== undefined)
            ? !controllerRef.showOnlyBigImages : false
        onTriggered: {
            if (controllerRef && controllerRef.showOnlyBigImages !== undefined) {
                controllerRef.setShowOnlyBigImages(!controllerRef.showOnlyBigImages)
            }
            checked = Qt.binding(function () {
                return (controllerRef && controllerRef.showOnlyBigImages !== undefined)
                    ? !controllerRef.showOnlyBigImages : false
            })
        }
    }
    MenuItem {
        objectName: "menuViewHidden"
        text: qsTr("&Hidden Pictures")
        checkable: true
        // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
        // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
        checked: (controllerRef && controllerRef.showHidden !== undefined) ? controllerRef.showHidden : false
        // #1637: ha van beállított jelszó és még nincs feloldva, a
        // kapcsoló NEM némán marad ki — a gazda jelszót kér. Enélkül a
        // menüpont hatástalannak látszana (a projekt visszatérő kára).
        onTriggered: {
            var zarva = controllerRef && controllerRef.hiddenPasswordSet === true
                        && controllerRef.hiddenUnlocked !== true
            if (zarva && !controllerRef.showHidden) {
                bar.hiddenUnlockRequested()
            } else {
                controllerRef.toggleShowHidden()
            }
            // #2377: a `checkable` MenuItem kattintáskor MAGA billenti a
            // `checked`-et, és ez eldobja a fenti kötést. A jelszó-kérés
            // ágán ez különösen fontos: ott a `showHidden` NEM változik,
            // tehát a pipa hazudna a következő megnyitásig (#1471).
            checked = Qt.binding(function () {
                return (controllerRef && controllerRef.showHidden !== undefined)
                    ? controllerRef.showHidden : false
            })
        }
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    // #1725: színkezelés — a beágyazott ICC-profil érvényesítése.
    // MÉRVE (spec 5.12): perzisztens kapcsoló, alapból KI, és
    // bekapcsoláskor a szerkesztő-előnézet újraépül.
    MenuItem {
        objectName: "menuViewColorManagement"
        text: qsTr("Use Color Management")
        checkable: true
        checked: (controllerRef && controllerRef.colorManagement !== undefined)
            ? controllerRef.colorManagement : false
        onTriggered: {
            controllerRef.toggleColorManagement()
            // #2377: a `checkable` MenuItem kattintáskor MAGA billenti a
            // `checked`-et, és ez eldobja a fenti kötést — a jelzés utáni
            // visszakötés nélkül a pipa a következő megnyitásig hazudna.
            checked = Qt.binding(function () {
                return (controllerRef && controllerRef.colorManagement !== undefined)
                    ? controllerRef.colorManagement : false
            })
        }
    }
    // SAJÁT FUNKCIÓ (#28, #4638): a sötét téma az eredeti Picasa 3.9-ben
    // nincs meg (`docs/specs/ui-audit-menus.md`), ezért kék jelölést kap.
    PicasaMenuItem {
        // #28: opcionális sötét téma — az alapértelmezés a világos
        objectName: "menuViewDarkTheme"
        placeholder: false
        sajat: true
        text: qsTr("Dark Theme")
        checkable: true
        checked: (controllerRef && controllerRef.darkTheme !== undefined) ? controllerRef.darkTheme : false
        onTriggered: {
            controllerRef.toggleDarkTheme()
            // #2377: a `checkable` MenuItem kattintáskor MAGA billenti a
            // `checked`-et, és ez eldobja a fenti kötést. Ma azért nem
            // látszik, mert a művelet mindig átbillenti az állapotot —
            // ez szerencse, nem szerkezet (ld. #1471).
            checked = Qt.binding(function () {
                return (controllerRef && controllerRef.darkTheme !== undefined)
                    ? controllerRef.darkTheme : false
            })
        }
    }
    // #1774 (mérve): a Megjelenítési mód UGYANEBBEN a csoportban van,
    // mint a Színkezelés használata — nincs közte elválasztó.
    // #1575: a Megjelenítési mód almenü — 11 tétel + 4 elválasztó
    // (15 rekord), a `docs/specs/picasa-megjelenitesi-modok.md` 1.
    // szakaszának SORRENDJÉBEN. A tartalom a binárisból mérve
    // (`0x0055ab62`–`0x0055abd4`); a korábbi „a screenshotokból nem
    // derül ki" komment 2026-08-27 óta elavult.
    //
    // Mind a tizenegy EGYETLEN kizáró csoport tagja (mérve,
    // `0x00575670`) — kapcsoló egy sincs köztük, tehát a
    // „Túlcsordult képpontok" és a „Projektor mód" sem kombinálható a
    // gammákkal. A pipa ezért végig a `controllerRef.displayMode`-ra köt.
    //
    // ⚠️ RÁDIÓ-CSAPDA (ld. a `Thumbnail Caption` alatti magyarázatot és
    // a #1464/#1468-at): a valódi kattintás előbb IMPERATÍVAN átbillenti
    // a `checked`-et, és a `setDisplayMode` azonos értéknél
    // SZÁNDÉKOSAN nem jelez — a kötés tehát magától soha nem értékelődne
    // újra. Ezért minden tétel a jelzés után VISSZAKÖTI a `checked`-et.
    //
    // A VÁZ szintjén mind a tizenegy MŰKÖDIK: pipázódik, és a módot
    // beállítja a vezérlőn. A képpont-hatást módonként a
    // #1576/#1577/#1578/#4412 tesztek őrzik; a `24 bites` és — 24 bites
    // képernyőn — az `Automatikus` az eredetiben is no-op.
    //
    // A `&`-gyorsítóbetűket a spec 1. szakasza tartalmazza; ide
    // SZÁNDÉKOSAN nem kerültek be: ebben a fájlban ma csak a hét
    // FŐMENÜ-cím visel mnemonikot, a 130+ tétel egyike sem, és egyetlen
    // almenüt kiemelni következetlenséget szülne. Ez külön jegy dolga.
    PicasaMenu {
        objectName: "menuViewDisplayMode"
        title: qsTr("&Display Mode")
        MenuItem {
            objectName: "menuViewDisplayModeAuto"
            text: qsTr("&Automatic")
            checkable: true
            checked: controllerRef && controllerRef.displayMode === "auto"
            onTriggered: {
                controllerRef.setDisplayMode("auto")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.displayMode === "auto"
                })
            }
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuViewDisplayModeNormal"
            text: qsTr("&24-bit")
            checkable: true
            checked: controllerRef && controllerRef.displayMode === "normal"
            onTriggered: {
                controllerRef.setDisplayMode("normal")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.displayMode === "normal"
                })
            }
        }
        MenuItem {
            objectName: "menuViewDisplayMode16Bit"
            text: qsTr("&16-bit (dithered)")
            checkable: true
            checked: controllerRef && controllerRef.displayMode === "dither16"
            onTriggered: {
                controllerRef.setDisplayMode("dither16")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.displayMode === "dither16"
                })
            }
        }
        MenuSeparator {}
        PicasaMenuItem {
            objectName: "menuViewDisplayModeRemoteDesktop"
            text: qsTr("&Remote Desktop")
            // #1658: a spec 7. táblázata szerint HATÓKÖRÖN KÍVÜL (RDP-specifikus,
            // 3-3-3 bites levágás) — sosem kötjük be, tehát nyugdíjazott.
            placeholder: false
            retired: true
        }
        MenuItem {
            objectName: "menuViewDisplayModeLcd"
            text: qsTr("&LCD Whitepoint")
            checkable: true
            checked: controllerRef && controllerRef.displayMode === "lcd"
            onTriggered: {
                controllerRef.setDisplayMode("lcd")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.displayMode === "lcd"
                })
            }
        }
        MenuItem {
            objectName: "menuViewDisplayModeProjector"
            text: qsTr("&Projector Mode")
            checkable: true
            checked: controllerRef && controllerRef.displayMode === "projector"
            onTriggered: {
                controllerRef.setDisplayMode("projector")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.displayMode === "projector"
                })
            }
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuViewDisplayModeOverflow"
            text: qsTr("&Show overflow pixels")
            checkable: true
            checked: controllerRef && controllerRef.displayMode === "overflow"
            onTriggered: {
                controllerRef.setDisplayMode("overflow")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.displayMode === "overflow"
                })
            }
        }
        // #1730: ÉLŐ tétel. A #1658 „hatókörön kívül, amíg nincs
        // referencia-mérés" indoka MEGSZŰNT: a #1580 képpont-mérése
        // megvan (a tulajdonos felvételeiről), és a mag a mért
        // világosítást reprodukálja (`render/display_modes.py`,
        // `apply_mac_gamma`).
        MenuItem {
            objectName: "menuViewDisplayModeMacGamma"
            text: qsTr("&Mac Gamma (1.6)")
            checkable: true
            checked: controllerRef && controllerRef.displayMode === "mac"
            onTriggered: {
                controllerRef.setDisplayMode("mac")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.displayMode === "mac"
                })
            }
        }
        MenuItem {
            objectName: "menuViewDisplayModeLinearGamma"
            text: qsTr("Linear &Gamma (2.2)")
            checkable: true
            checked: controllerRef && controllerRef.displayMode === "linear"
            onTriggered: {
                controllerRef.setDisplayMode("linear")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.displayMode === "linear"
                })
            }
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuViewDisplayModeSepia"
            text: qsTr("Sepia")
            checkable: true
            checked: controllerRef && controllerRef.displayMode === "sepia"
            onTriggered: {
                controllerRef.setDisplayMode("sepia")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.displayMode === "sepia"
                })
            }
        }
        MenuItem {
            objectName: "menuViewDisplayModeBlackWhite"
            text: qsTr("&Black and White")
            checkable: true
            checked: controllerRef && controllerRef.displayMode === "bw"
            onTriggered: {
                controllerRef.setDisplayMode("bw")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.displayMode === "bw"
                })
            }
        }
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
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
    PicasaMenu {
        objectName: "menuViewThumbnailCaption"
        title: qsTr("Thumbnail &Caption")
        MenuItem {
            objectName: "menuViewThumbCaptionNone"
            text: qsTr("None")
            checkable: true
            checked: controllerRef && controllerRef.thumbCaptionMode === "none"
            onTriggered: {
                controllerRef.setThumbCaptionMode("none")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.thumbCaptionMode === "none"
                })
            }
        }
        MenuItem {
            objectName: "menuViewThumbCaptionFilename"
            text: qsTr("&Filename")
            checkable: true
            checked: controllerRef && controllerRef.thumbCaptionMode === "filename"
            onTriggered: {
                controllerRef.setThumbCaptionMode("filename")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.thumbCaptionMode === "filename"
                })
            }
        }
        MenuItem {
            objectName: "menuViewThumbCaptionCaption"
            text: qsTr("&Caption")
            checkable: true
            checked: controllerRef && controllerRef.thumbCaptionMode === "caption"
            onTriggered: {
                controllerRef.setThumbCaptionMode("caption")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.thumbCaptionMode === "caption"
                })
            }
        }
        MenuItem {
            objectName: "menuViewThumbCaptionTags"
            text: qsTr("&Tags")
            checkable: true
            checked: controllerRef && controllerRef.thumbCaptionMode === "tags"
            onTriggered: {
                controllerRef.setThumbCaptionMode("tags")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.thumbCaptionMode === "tags"
                })
            }
        }
        MenuItem {
            objectName: "menuViewThumbCaptionResolution"
            text: qsTr("&Resolution")
            checkable: true
            checked: controllerRef && controllerRef.thumbCaptionMode === "resolution"
            onTriggered: {
                controllerRef.setThumbCaptionMode("resolution")
                checked = Qt.binding(function () {
                    return controllerRef && controllerRef.thumbCaptionMode === "resolution"
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
    // A négy gyökér (Sajátgép / Képek / Dokumentumok / Asztal) a #1407-ben
    // került be, a két nézetváltó UTÁN — a spec 2.2 sorrendjében.
        PicasaFolderViewMenu {
            id: folderViewMenu
            bar: menuView.bar
        }
}
