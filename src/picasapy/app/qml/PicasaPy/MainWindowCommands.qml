pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Controls
import PicasaPy
import "../selection.js" as Selection

// A főablak gyorsműveletei, súgója és billentyűparancsai.
Item {
    id: commandSurface
    objectName: "mainWindowCommands"
    anchors.fill: parent
    required property var hostWindow
    required property var hostController
    required property var hostRefs

    property alias exportConfigureButtonsContextMenu: configureButtonsContextMenu
    property alias exportKilepesDialog: kilepesDialog
    property alias exportMainKeyboardShortcuts: mainKeyboardShortcuts
    property alias exportShortcutSave: mainKeyboardShortcuts.shortcutSave
    property alias exportSaveSearchDialog: saveSearchDialog
    property alias exportShowTagAsAlbumDialog: showTagAsAlbumDialog

    property alias exportMainDialogs: mainDialogs
    property alias exportEmailChoiceDialog: emailChoiceDialog
    property alias exportOpenWithDialog: openWithDialog
    property alias exportFolderManager: folderManager
    property alias exportPeopleManagerLoader: peopleManagerLoader
    property alias exportDedupDialog: dedupDialog
    property alias exportFaceScanDialog: faceScanDialog
    property alias exportScreensaverDialog: screensaverDialog
    property alias exportScreensaverAlbumConfirmLoader: screensaverAlbumConfirmLoader
    property alias exportPhotoViewerSettingsDialog: photoViewerSettingsDialog
    property alias exportPicasaImportDialog: picasaImportDialog
    property alias exportImportSourceDialog: importSourceDialog
    property alias exportAddFileDialog: addFileDialog
    property alias exportTesztuzemNaploDialog: tesztuzemNaploDialog

    property alias exportSearchSuggestionsBox: searchSuggestionsBox
    property alias exportSuggestionsTimer: suggestionsTimer

    // A helyi gombsor-menü az ApplicationWindow része, nem a PicasaMenuBaré:
    // így a főmenü szerkezete és bejárási útvonalai változatlanok maradnak.
    Menu {
        id: configureButtonsContextMenu
        objectName: "configureButtonsContextMenu"
        MenuItem {
            objectName: "configureButtonsContextMenuItem"
            text: qsTr("Configure Buttons...")
            onTriggered: hostRefs.picasaMenuBar.configureButtonsRequested()
        }
    }

    // #135: a háttér-frissítés (5 perces rescan, watcher-jelzés) a
    // rács-modellt teljesen resetelheti — beszúrt/eltűnt fájloknál a
    // sor-indexek elcsúsznának, és a csillag/forgatás/elrejtés/export a
    // FELHASZNÁLÓ által kijelölttől eltérő képre hatna. A resetet
    // megelőzően elmentjük a kijelölt sorok fotó-id-it (a sor-index
    // ekkor még a RÉGI adatot tükrözi), majd a reset után az id-k
    // alapján képezzük újra a kijelölést — az eltűnt fotók kiesnek.
    property var _pendingSelectedIds: []
    property string _pendingAnchorId: ""
    Connections {
        // #305: engine-leépítéskor a `controller` context property null
        // lehet, miközben ez a kötés újra kiértékelődik — null-őr kell.
        target: hostController ? hostController.photos : null
        function onModelAboutToBeReset() {
            var ids = []
            for (var k = 0; k < hostWindow.selectedIndexes.length; ++k) {
                var id = hostController.photos.idAt(Number(hostWindow.selectedIndexes[k]))
                if (id.length > 0) ids.push(parseInt(id, 10))
            }
            hostWindow._pendingSelectedIds = ids
            hostWindow._pendingAnchorId = hostWindow.selectedIndex >= 0
                ? hostController.photos.idAt(hostWindow.selectedIndex) : ""
        }
        function onModelReset() {
            hostWindow.selectedIndexes = Selection.remapByIds(
                hostWindow._pendingSelectedIds, hostController.photos.rowOfId)
            hostWindow.selectedIndex = hostWindow._pendingAnchorId.length > 0
                ? hostController.photos.rowOfId(parseInt(hostWindow._pendingAnchorId, 10))
                : -1
            // Az átnevezett fájl új útvonal miatt új adatbázis-id-t kaphat.
            // Csak akkor helyettesítjük a régi azonosítót, ha az már eltűnt
            // a modellből és az új útvonal megjelent; sikertelen átnevezésnél
            // a régi ID-alapú állapot marad érvényben.
            if (hostWindow._pendingRenamePhotoId.length > 0
                    && hostWindow._pendingRenameTargetPath.length > 0) {
                var ujSor = hostController.photos.rowOfPath(
                    hostWindow._pendingRenameTargetPath)
                var regiId = parseInt(hostWindow._pendingRenamePhotoId, 10)
                if (ujSor >= 0
                        && hostController.photos.rowOfId(regiId) < 0
                        && hostWindow._pendingSelectedIds.indexOf(regiId) >= 0) {
                    var ujKijeloles = hostWindow.selectedIndexes.slice()
                    if (ujKijeloles.indexOf(ujSor) < 0)
                        ujKijeloles.push(ujSor)
                    ujKijeloles.sort(function (a, b) { return a - b })
                    hostWindow.selectedIndexes = ujKijeloles
                    if (hostWindow._pendingAnchorId === hostWindow._pendingRenamePhotoId)
                        hostWindow.selectedIndex = ujSor
                }
                hostWindow._pendingRenamePhotoId = ""
                hostWindow._pendingRenameTargetPath = ""
            }
        }
    }
    // A főablak gyorsbillentyűi önálló komponensben (#6136).
    MainKeyboardShortcuts {
        id: mainKeyboardShortcuts
        hostWindow: commandSurface.hostWindow
        hostController: commandSurface.hostController
        hostDocumentTabStrip: hostRefs.documentTabStrip
        hostExportDialogs: hostWindow.exportDialogs
        hostFileOpsController: typeof fileOpsController !== "undefined"
            ? fileOpsController : null
        hostFileOpsDialogs: hostWindow.fileOpsDialogs
        hostHelpDialog: hostWindow.helpDialog
        hostPhotoViewer: hostRefs.photoViewer
        hostPicasaMenuBar: hostRefs.picasaMenuBar
        hostSaveDialogs: hostWindow.saveDialogs
        hostSlideshow: hostRefs.slideshow
        hostTrayBar: hostRefs.trayBar
    }

    //: #3544: amíg egy külön ablakos párbeszéd látszik, a főablak két
    //: súgó-billentyűje HALLGAT. A Qt 6 az ablakszintű gyorsbillentyűt a
    //: főablak TRANZIENS gyermekablakaiban is illeszti (és a főablak `active`-ja
    //: is igaz marad), ott pedig a párbeszéd saját F1-e/Shift+F1-e
    //: (`WindowHelp`) áll: a kettő kétértelmű, és MEGMÉRVE egyik sem sül el.
    //: A párbeszédek alkalmazás-modálisak, a főablak addig úgysem kezelhető.
    readonly property bool _kulonAblakosParbeszedNyitva:
        [folderManager, importSourceDialog, optionsDialog, webExportDialog,
         printDialog].some(function (d) { return d.item !== null && d.item.visible })

    //: #2054: a mutató helye a Shift+F1-hez. A `HoverHandler` a teljes
    //: ablakot lefedi, de NEM nyel el eseményt (`acceptedButtons: NoButton`),
    //: tehát semmilyen meglévő vezérlőt nem zavar.
    property point helpCursor: Qt.point(-1, -1)

    HoverHandler {
        objectName: "helpCursorTracker"
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onPointChanged: hostWindow.helpCursor = point.position
    }

    //: #2054: a mutató alatti elemtől FELFELÉ sétálunk a szülőláncon az
    //: első olyan ősig, amelyik deklarál `helpTopic`-ot. Így nem kell
    //: minden gombot felcímkézni: elég a panelekre és a párbeszédekre,
    //: a többi öröklődik. Ha egyik sem deklarál, ÜRES jön vissza, és a
    //: néző a főoldalt nyitja — néma kudarc nincs.
    //:
    //: #3463: a `childAt()` CSAK a közvetlen, legfelső gyermeket adja — az
    //: pedig gyakran egy üres, az egész ablakot kitöltő réteg (pl. egy
    //: halasztott párbeszéd `DeferredDialog`-betöltője), amelyben nincs
    //: téma. A keresés ezért MÉLYSÉGI: felülről lefelé minden olyan látható
    //: gyermeket kipróbál, amelyik a pontot tartalmazza, és a legmélyebb
    //: témát adja; ha egy ág üres, az alatta fekvővel folytatja. A réteg
    //: (`overlay`) párbeszédei NEM itt kapnak témát: amíg egy modális
    //: párbeszéd nyitva van, a saját Shift+F1-e a saját fejezetét nyitja.
    function _temaAPontban(elem, x, y) {
        var gyerekek = elem.children
        for (var i = gyerekek.length - 1; i >= 0; --i) {
            var gyerek = gyerekek[i]
            if (!gyerek.visible || gyerek.width <= 0 || gyerek.height <= 0)
                continue
            var pont = elem.mapToItem(gyerek, x, y)
            if (!gyerek.contains(pont))
                continue
            var tema = hostWindow._temaAPontban(gyerek, pont.x, pont.y)
            if (tema.length > 0)
                return tema
        }
        if (elem.helpTopic !== undefined && String(elem.helpTopic).length > 0)
            return String(elem.helpTopic)
        return ""
    }

    //: #3463: a súgó megnyitása egy fejezettel — a modális
    //: réteg-párbeszédek Shift+F1-e is ezt hívja (üres fejezet = főoldal).
    function nyisdASugot(tema) {
        helpDialog.ensure().nyisdMeg(tema)
    }

    function helpTopicUnderCursor() {
        if (hostWindow.helpCursor.x < 0) return ""
        //: a `helpCursor` a `contentItem` koordinátáiban áll (a
        //: `HoverHandler` ott ül)
        return hostWindow._temaAPontban(
            hostWindow.contentItem, hostWindow.helpCursor.x, hostWindow.helpCursor.y)
    }

    // #1526/#1571: a fájl-vágólap billentyűi — FÓKUSZ-ÉRZÉKENYEN.
    //
    // ⚠️ A kézenfekvő megoldás valódi regressziót okozna: egy sima
    // `WindowShortcut` a Ctrl+C-t ELVENNÉ a szövegmezőktől, tehát
    // átnevezés, keresés vagy feliratszerkesztés közben a felhasználó nem
    // tudná a beírt szöveget másolni. Ez rosszabb volna a mai állapotnál
    // (#1571).
    //
    // A kapu: ha a fókusz szövegmezőn van, a billentyű a MEZŐÉ. A próba a
    // `selectedText` tulajdonság megléte — ezt a `TextInput`/`TextEdit`
    // (és minden rájuk épülő `TextField`/`TextArea`) hordozza, más elem
    // nem. Így nem kell felsorolni a mezőtípusokat, és a jövőbeli
    // mezőkre is magától áll.
    readonly property bool _szovegmezoneVanFokusz:
        hostWindow.activeFocusItem !== null
        && hostWindow.activeFocusItem.selectedText !== undefined
    readonly property bool _konyvtariGyorsbillentyuEngedelyezve:
        !hostWindow.viewerOpen && !hostWindow._szovegmezoneVanFokusz
    //: #1406: `ID_SEARCHTOKEN` — a megadott címke tartalmából rendes album.
    //: A HÁROM szöveg mind a saját helyén: a menüfelirat a menüsorban, a cím
    //: és a felszólítás itt (mérve, `0x005d8330`).
    DeferredDialog {
        id: showTagAsAlbumDialog
        objectName: "showTagAsAlbumDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            NameInputDialog {
                objectName: "showTagAsAlbumDialog"
                //: `ThumbUI::addsearchtoken`
                title: qsTr("Add search tag")
                //: `CAlbumState::addsearchprompt`
                prompt: qsTr("Please enter a tag to show as an album")
                onAccepted: {
                    if (hostController.showTagAsAlbum(enteredName) === "") {
                        hostWindow.errorBanner.notice = true
                        hostWindow.errorBannerText.text = qsTr("No pictures have that tag.")
                    }
                }
            }
        }
    }

    //: #1405: a keresés mentése albumként — a menütétel és a megerősítés is
    //: ezt hívja (egy hely, egy viselkedés).
    function mentsdAKeresest() {
        if (hostController.saveSearchAsAlbum() === "") {
            hostWindow.errorBanner.notice = true
            hostWindow.errorBannerText.text = qsTr("The search results could not be saved as an album.")
        }
    }

    //: #1405: a megerősítés CSAK 1000 találat felett nyílik, ezért halasztott
    //: (#1720): a legtöbb munkamenetben fel sem épül.
    DeferredDialog {
        id: saveSearchDialog
        objectName: "saveSearchDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "saveSearchConfirm"
                namePrefix: "saveSearch"
                title: qsTr("Save search results")
                //: `CThumbUI::SaveSearchBigBtn` — az eredeti gombfelirata NEM
                //: „Igen", hanem a művelet megnevezése
                yesText: qsTr("Create Album")
                onConfirmed: hostWindow.mentsdAKeresest()
            }
        }
    }

    //: #3644: a néző elhagyása ELŐTT az „aa" mód kapuja dönt a két fél
    //: szerkesztéséről (`PhotoViewer.aaKilepesKapu`, spec
    //: `ui-audit-editor.md` 4/c.1). `true`: folytatható MOST; `false`: a
    //: párbeszéd nyitva, a `folytatas` a VÁLASZ után fut, Mégsére elmarad.
    //: Az eredeti a programzáráskor is kérdez (`SC_CLOSE` → `0x0057c4e0` →
    //: `0x005e45c0` → `0x0056aad0`), és Mégsére nem zár be (`0x0057c59c`).
    function aaKapu(folytatas) {
        return !hostWindow.viewerOpen || hostRefs.photoViewer.aaKilepesKapu(folytatas)
    }

    //: #671 4. pont: a kilépés NEM kérdez — KIVÉVE, ha háttérmunka fut.
    //: Az eredeti Picasa sem blokkolja a kilépést („Uploads will resume next
    //: time"), de rákérdez; nálunk a háttérmunka NEM folytatódik legközelebb,
    //: ezért a szöveg a mi valóságunkat mondja, nem az eredetit fordítja.
    //:
    //: Egy helyen fut: a Fájl ▸ Kilépés menütétel és az ablak „X"-e is ezt
    //: hívja — különben az egyik út megkérdezné, a másik nem.
    function kilepes() {
        if (!hostWindow.aaKapu(hostWindow.kilepes)) return   // #3644
        //: #305: null-őr — a leépülő motor is újraértékelheti a kötést
        if (hostController && hostController.backgroundWorkRunning()) {
            kilepesDialog.askExit()
            return
        }
        Qt.quit()
    }

    //: #1720: halasztott — a legtöbb munkamenetben fel sem épül.
    DeferredDialog {
        id: kilepesDialog
        objectName: "exitConfirmDialogLoader"
        anchors.fill: parent
        function askExit() {
            //: a `decisionKey` SZÁNDÉKOSAN üres: az adatvesztéssel járó
            //: kérdést nem lehet „ne kérdezze újra"-val elnyomni
            ensure().ask("", qsTr(
                "Background work is still running (export, web export or "
                + "face scanning). If you exit now, it stops and does not "
                + "resume later."))
        }
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "exitConfirm"
                namePrefix: "exit"
                title: qsTr("Exit PicasaPy")
                //: az eredeti gombpárja „Exit Now" / „Keep Going" — a
                //: viselkedés (accept/deny) változatlan, csak a felirat
                yesText: qsTr("Exit Now")
                noText: qsTr("Keep Going")
                onConfirmed: Qt.quit()
            }
        }
    }

    //: #1526: a beillesztés EGY helyen — a menütétel és a billentyű is ezt
    //: hívja. (⚠️ A billentyű-őr a `Shortcut` törzsét egy szintig elemzi,
    //: tehát ott nem lehet ágas kód: ha a logika a `Shortcut`-ba kerül, az
    //: őr NEM LÁTJA meg a kötést, és a menütétel „néma hirdetőnek" látszik.)
    // #5877: „Copy Text" - a kijelölés első képének Text eszközös rétege.
    function masoldASzovegreteget() {
        if (!hostController) return
        var sorok = hostWindow.photoActionRows()
        if (sorok.length === 0) return
        hostController.copyTextLayer(sorok)
    }

    // #5877: „Paste Text" - a másolt Text eszközös réteg a kijelölés minden
    // képére kerül; a kijelölt réteg pufferként is használható.
    function illeszdBeASzovegreteget() {
        if (!hostController) return
        var sorok = hostWindow.photoActionRows()
        if (sorok.length === 0) return
        hostController.pasteTextLayer(sorok)
    }

    function beillesztAVagolaprol() {
        if (fileOpsController.pasteFilesFromClipboard(hostController.currentFolder))
            return
        hostWindow.errorBanner.notice = true
        hostWindow.errorBannerText.text = qsTr("There are no files on the clipboard to paste.")
    }

    // Picasa gyorsbillentyűk: Ctrl+R jobbra, Ctrl+Shift+R balra forgat.
    // Diavetítés közben (#8) a vetített kép a célpont, nem a rács-kijelölés.
    function rotateTargetRow() {
        if (hostRefs.slideshow.visible) return hostRefs.slideshow.currentIndex
        return hostRefs.trayBar.starTargetRow
    }
    // #103: csak-videó célpontnál a forgatás tiltott — a tálca ↺/↻
    // gombjainak őre (a controller-slotok defenzíven szintén kihagyják
    // a videókat, vegyes kijelölésnél csak a fotók forognak)
    function rotateTargetsAllVideo() {
        // #305: null-őr — a TrayBar `enabled:` kötése (ami ezt hívja)
        // a QML-engine leépítésekor is újraértékelődhet
        if (!hostController) return false
        var rows = hostWindow.viewerOpen
            ? [hostRefs.photoViewer.currentIndex]
            : hostWindow.selectedRows()
        if (rows.length === 0) return false
        for (var k = 0; k < rows.length; ++k)
            if (!hostController.photos.isVideoAt(Number(rows[k])))
                return false
        return true
    }
    //: #2902: tükrözés — az eredeti könyvtárnézeti kezelőjének két ága
    //: (`0x005e63d6` vízszintes, `0x005e6408` függőleges), a keymapben
    //: 35. *Flip Horizontal* / 36. *Flip Vertical*. MENÜPONT SZÁNDÉKOSAN
    //: NINCS hozzá: a 3.9 menüiben sem volt, a funkció csak billentyűvel
    //: érhető el (`docs/specs/picasa-gyorsbillentyuk.md` 10.3–10.4).
    //:
    //: A cél a KIJELÖLÉS (az eredeti ága is a panelre hat); nézőben a
    //: megnyitott kép, a forgatás `rotateTargetRow` mintája szerint.
    function tukrozesiSorok() {
        if (hostWindow.viewerOpen) return [hostRefs.photoViewer._kijeloltSort()]
        return hostWindow.selectedRows()
    }

    // Az Időrend főablaki belépői megőrzik az eddigi QML-neveket.
    function timelineCollectionForId(collectionId) {
        return hostRefs.timelineView.timelineCollectionForId(collectionId)
    }
    function selectTimelineCollection(collection) {
        return hostRefs.timelineView.selectTimelineCollection(collection)
    }
    function closeTimeline() { hostRefs.timelineView.closeTimeline() }
    function toggleTimeline() { hostRefs.timelineView.toggleTimeline() }
    function startTimelineSlideshow(collectionId) {
        hostRefs.timelineView.startTimelineSlideshow(collectionId)
    }

    // A teljes képernyős állapotot a vetítési komponens birtokolja; a régi
    // főablaki QML-nevek megmaradnak a hívóknak és a teszteknek.
    function toggleViewerFullscreen() { hostRefs.slideshow.toggleViewerFullscreen() }
    function startSlideshow(fromIndex) { hostRefs.slideshow.startSlideshow(fromIndex) }
    function startScreensaverPreview() { hostRefs.slideshow.startScreensaverPreview() }
    function exitSlideshow() { hostRefs.slideshow.exitSlideshow() }

    // #922: a képtálca tartalma ÁLLAPOTKÉNT, nem közvetlen kötésként. Egy
    // `controller.heldCount`-ra épülő kötés a `controller` null állapotában
    // ki tud értékelődni ELŐSZÖR — olyankor a QML nem regisztrálja a
    // függőséget, és a kötés soha többé nem frissül. Ez a `Connections`
    // ettől független.
    property bool trayHasPictures: false
    Connections {
        target: hostController
        function onHeldChanged() {
            hostWindow.trayHasPictures = hostController.heldCount > 0
        }
    }
    // A Súgó által használt főablak-tulajdonság neve változatlan.
    readonly property alias keyboardShortcutGroups:
        mainKeyboardShortcuts.keyboardShortcutGroups


    MainDialogs {
        id: mainDialogs
        anchors.fill: parent
    }

    // #17: Elrejtés/Megjelenítés a kijelölésre; elrejtés után a kijelölést
    // ürítjük — az elrejtett sorok kiesnek a rácsból, az indexek eltolódnak
    function toggleHiddenSelection() {
        var rows = hostWindow.photoActionRows()
        if (rows.length === 0) return
        hostController.toggleHiddenRows(rows)
        if (!hostWindow.viewerOpen) hostWindow.clearSelection()
    }

    // #1798: a kijelölés elküldése levélben. A tárgyat és a szöveget
    // SZÁNDÉKOSAN nem kérjük be: az eredeti Picasa sem kérdez, a levelet a
    // levelezőprogram szerkeszti meg — mi csak a csatolmányokkal nyitjuk meg.
    function sendSelectionByEmail() {
        if (typeof emailController === "undefined" || !emailController)
            return
        var sorok = hostWindow.photoActionRows()
        if (sorok.length === 0)
            return
        var csatolmanyok = emailController.prepareAttachments(
            sorok, sorok.length > 1)
        if (csatolmanyok.length === 0)
            return
        // A `sendRows` a beállítás szerint vagy küld, vagy a
        // `mailChoiceRequested`-del kérdést kér — a válasz lentebb.
        emailController.sendRows(csatolmanyok, "", "")
    }

    // #4330: a Fájl menü és a Ctrl+Shift+O ugyanazt a kijelölés-pillanatképet
    // adja a rendszer alapértelmezett fájlmegnyitójának.
    function openSelectionInDefaultEditor() {
        if (!fileOpsController) return
        var paths = hostWindow.photoActionPaths()
        if (paths.length > 0)
            fileOpsController.openPhotosInDefaultEditor(paths)
    }

    // #1798: a küldési út két visszajelzése. A `mailChoiceRequested` a
    // „minden küldéskor kérdezz" mód kérdése, az `emailFailed` a hibáé —
    // ez utóbbinak eddig SEHOL nem volt kezelője, tehát a hibaüzenet
    // („nincs levelezőprogram") némán elveszett.
    //: #1407: a három rendszermappa-tétel (Képek / Dokumentumok / Asztal)
    //: NEM gyökeret vált, hanem a teljes fára váltás UTÁN felfedi és
    //: kijelöli a mappát (spec 4.5/b: `push "all"` mindhárom ágban). A
    //: felfedés a hierarchia-vezérlő dolga, a KIJELÖLÉS a bekötőé — ezért
    //: jön ide a jelzés.
    //:
    //: ⚠️ Feloldhatatlan mappánál a vezérlő NEM jelez (spec 4.6: visszaesés
    //: a Sajátgép-gyökérre, nem hibaüzenet), tehát itt nincs hibaág.
    Connections {
        target: (typeof folderHierarchyController !== "undefined")
                ? folderHierarchyController : null
        function onRootFolderRevealed(utvonal) {
            folderHierarchyController.revealPath(utvonal)
            if (typeof hostController !== "undefined" && hostController)
                hostController.selectFolder(utvonal)
        }
    }

    Connections {
        target: (typeof emailController !== "undefined")
                ? emailController : null
        function onMailChoiceRequested(utvonalak, targy, szoveg) {
            var parbeszed = emailChoiceDialog.ensure()
            parbeszed.attachmentPaths = utvonalak
            parbeszed.subject = targy
            parbeszed.body = szoveg
            parbeszed.open()
        }
        // #1798b: az előkészítés jelzése. A `sendSelectionByEmail()` a
        // képeket a beállított méretre kicsinyíti, ami nagy fájloknál
        // másodpercekig tart — jelzés nélkül úgy tűnik, nem történik semmi.
        // A #459-es közös sávot használjuk, TÁJÉKOZTATÓ (borostyán)
        // tónussal: ez nem hiba.
        function onPreparingChanged(fut) {
            hostWindow.errorBanner.notice = true
            hostWindow.errorBannerText.text = fut
                ? qsTr("Preparing attachments...")
                : ""
        }
        function onEmailFailed(uzenet) {
            // a #459-es közös hibasáv — a levelezős hibának eddig SEHOL
            // nem volt kezelője, tehát némán elveszett
            hostWindow.errorBanner.notice = false
            hostWindow.errorBannerText.text = uzenet
        }
    }

    DeferredDialog {
        id: emailChoiceDialog
        anchors.fill: parent
        sourceComponent: Component {
            EmailChoiceDialog {
                objectName: "emailChoiceDialog"
                onAccepted: emailController.sendWithDefaultClient(
                    attachmentPaths, subject, body, rememberChoice)
            }
        }
    }

    // #4533: Társítás… — a fájltípushoz társított alkalmazások választója (Linux)
    DeferredDialog {
        id: openWithDialog
        anchors.fill: parent
        sourceComponent: Component {
            OpenWithDialog {
                objectName: "openWithDialog"
                onAccepted: fileOpsController.openWithApp(photoPath, selectedAppId)
            }
        }
    }

    // #1720: halasztott példányosítás — a párbeszéd csak az első
    // megnyitáskor épül fel (ld. `DeferredDialog.qml`).
    DeferredDialog {
        id: folderManager
        anchors.fill: parent
        sourceComponent: Component { FolderManagerDialog { } }
    }

    function openPeopleManagerForPerson(name) {
        var targetName = String(name || "").trim()
        if (peopleManagerLoader.status === Loader.Ready) {
            peopleManagerLoader.item.openForPerson(targetName)
        } else {
            hostWindow.pendingPeopleManagerPersonName = targetName
            peopleManagerLoader.active = true
        }
    }

    // #4334: a komponens csak az első menükattintásra töltődik be; a
    // külön fájl miatt a forró Main.qml-ben csak a bekötés marad.
    Loader {
        id: peopleManagerLoader
        objectName: "peopleManagerLoader"
        active: false
        source: Qt.resolvedUrl("PicasaPy/PeopleManagerDialog.qml")
        onLoaded: {
            item.controller = hostController
            var targetName = hostWindow.pendingPeopleManagerPersonName
            hostWindow.pendingPeopleManagerPersonName = ""
            if (targetName.length > 0)
                item.openForPerson(targetName)
            else
                item.open()
        }
    }
    // Duplikátum-kezelő (#287): a SAJÁT kezelő-párbeszéd. #1398 óta a
    // másodpéldány-mód eredménysávjáról nyílik („Manage Duplicates..."), nem
    // az Eszközök menüből — a mért menüparancs a keresési módot kapcsolja.
    // #294: az appWindow-bekötés a „kijelölt képek" hatókörhöz kell — enélkül
    // a dialógus a mappa-hatókörre esne vissza (integrátori bekötés).
    DeferredDialog {
        id: dedupDialog
        anchors.fill: parent
        sourceComponent: Component { DedupDialog { appWindow: hostWindow } }
    }
    // #1473: az arckeresés belépési pontja. A vezérlőt az ablak-szintű
    // álnéven kapja (#1236) — az ablak maga NEM modális, a keresés alatt a
    // felhasználó tovább dolgozhat (#449).
    DeferredDialog {
        id: faceScanDialog
        anchors.fill: parent
        sourceComponent: Component {
            FaceScanDialog {
                faceScan: typeof faceScanController !== "undefined"
                    ? faceScanController : null
            }
        }
    }
    DeferredDialog {
        id: screensaverDialog
        objectName: "screensaverDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ScreensaverDialog {
                saverController: hostController
                onPreviewRequested: hostWindow.startScreensaverPreview()
            }
        }
    }
    //: #4618: album-nézetben az eredeti rákérdez (`addtosaver::warning`);
    //: halasztva (#1612), a közös megerősítő párbeszéddel
    DeferredDialog {
        id: screensaverAlbumConfirmLoader
        objectName: "screensaverAlbumConfirmDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                namePrefix: "screensaverAlbumConfirm"
                title: qsTr("Confirm")
                property var pendingPaths: []
                function openFor(paths) {
                    pendingPaths = paths ? paths.slice() : []
                    if (pendingPaths.length > 0)
                        ask("", qsTr("Are you sure you want to add all of the"
                                     + " selected album's images?"))
                }
                onConfirmed: hostWindow.addPhotosToScreensaver(pendingPaths)
            }
        }
    }
    DeferredDialog {
        id: photoViewerSettingsDialog
        anchors.fill: parent
        sourceComponent: Component {
            PhotoViewerSettingsDialog { viewerController: hostController }
        }
    }
    // #146: meglévő Picasa-telepítés átvétele — nyitása a Mappakezelő
    // gombjából (discoveryController.dialogRequested) vagy induláskori
    // automatikus felajánlásból (integrátori bekötés: picasaImportDialog.openAndDiscover())
    PicasaImportDialog {
        id: picasaImportDialog
        //: #3463: modális réteg-párbeszéd — a főablak Shift+F1-ét a Qt
        //: letiltja, amíg nyitva van
        Shortcut {
            sequence: "Shift+F1"
            enabled: picasaImportDialog.opened
                     && !hostWindow._szovegmezoneVanFokusz
            onActivated: hostWindow.nyisdASugot(picasaImportDialog.helpTopic)
        }
    }
    // Import forrásból (#23): az eszköztár "Import" gombja nyitja
    DeferredDialog {
        id: importSourceDialog
        anchors.fill: parent
        sourceComponent: Component { ImportSourceDialog { } }
    }
    // #1633: Fájl ▸ Fájl felvétele a Picasába… / Ctrl+O — natív fájlválasztó
    AddFileDialog { id: addFileDialog }
    // #1654: a tesztüzem naplójának „Mentés másként…" tartaléka —
    // csak akkor nyílik meg, ha a NAS közös mappája nem érhető el
    TesztuzemNaploDialog { id: tesztuzemNaploDialog }


    // Kereső-javaslatok (#7): gépelés után rövid szünettel (debounce)
    // kérjük le, hogy NAS-on se fusson lekérdezés minden billentyűre.
    // #1515: null-őr (#305 mintája). A 150 ms-os debounce miatt a hívás a
    // gépeléstől ELVÁLIK: ha közben az ablak lebomlik, a `controller`
    // kontextus-tulajdonság már null, és a hívás QML-szkripthibát dobna.
    // Ez a felület egyetlen olyan pontja, ahol IDŐZÍTŐ hívja a
    // controllert — a #1515 tesztje volt az első, amely a valódi
    // (searchEdited → suggestionsTimer) úton ment végig, és kibukott.
    function refreshSuggestions() {
        if (!hostController)
            return
        searchSuggestionsBox.suggestions =
            hostController.searchSuggestions(hostRefs.toolbar.searchText)
    }
    Timer {
        id: suggestionsTimer
        interval: 150
        onTriggered: hostWindow.refreshSuggestions()
    }
    SearchSuggestions {
        id: searchSuggestionsBox
        objectName: "searchSuggestions"
        parent: hostRefs.toolbar
        z: 50
        x: hostRefs.toolbar.searchBoxItem.x
        y: hostRefs.toolbar.searchBoxItem.y + hostRefs.toolbar.searchBoxItem.height
        width: hostRefs.toolbar.searchBoxItem.width
        query: hostRefs.toolbar.searchText
        // #1026: a keresődoboz a könyvtár keretének része, tehát a buborék
        // sem úszhat rá a projekt-lapra (a beírt szöveg megmarad, ezért a
        // hosszra kötött feltétel önmagában igazat adna)
        visible: suggestions.length > 0 && hostRefs.toolbar.searchText.length > 0
                 && !hostWindow.viewerOpen && hostWindow.libraryFrameVisible
        onChosen: function(kind, name, param) {
            if (kind === "folder") {
                hostRefs.toolbar.clearSearch()
                hostWindow.clearSelection()
                hostController.selectFolder(param)
            } else if (kind === "album") {
                hostRefs.toolbar.clearSearch()
                hostWindow.clearSelection()
                hostWindow.unnamedFacesOpen = false
                hostController.showAlbum(param)
            }
            suggestions = []
        }
    }


    function onWindowCompleted() {
        if (hostController && hostController.attachHoverPreviewKeyState)
            hostController.attachHoverPreviewKeyState(hostWindow)
        //: #598: a kezdő cellaméret átadása a bélyegkép-tárnak — enélkül az
        //: induló rács a felső szintről dolgozna, pedig a 144-es fokozat a
        //: kisebb szintből tízszer olcsóbban áll elő.
        if (hostController) hostController.setThumbCellSize(hostWindow.thumbSize)
        //: #3070: a megjelenítési mód kezdőállapota a felület színein
        hostWindow.frissitsdAMegjelenitesiPalettat()
        if (hostWindow.quickViewerLaunch) {
            hostWindow.startQuickViewer()
            return
        }
        initialScanDialog.openIfNeeded()
        // #1051: ha az előző munkamenet piszkozatot hagyott, most kell
        // felajánlani — enélkül a lemezen ragad, ahogy a tulajdonosé is
        collageDraftDialog.openIfNeeded()
        // #922: a képtálca kezdőállapota (a Connections innentől frissíti)
        if (hostController) hostWindow.trayHasPictures = hostController.heldCount > 0
        // #1622: NÉMA felderítés korábbi telepítésből származó adatra —
        // az eredeti is magától megnézi (`0x00406770`, két `Windows.old`
        // útvonal). Találat nélkül semmi nem történik; találatnál a
        // PicasaImportDialog KÉRDEZ, mielőtt bármit átvennénk.
        if (typeof discoveryController !== "undefined" && discoveryController)
            discoveryController.discoverAtStartup()
    }
}
