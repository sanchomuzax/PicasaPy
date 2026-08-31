import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy
import "selection.js" as Selection

// Főablak (#150 után): a nagy nézet-blokkok külön komponensekben élnek
// (LightboxFeed = könyvtár-feed, MainToolbar = felső sáv, TrayBar = alsó
// sáv, FileOpsDialogs/ExportDialogs/AboutDialog = dialógusok, selection.js
// = kijelölés-logika) — itt csak az állapot és a bekötés marad.
ApplicationWindow {
    id: window
    width: 1280
    height: 800
    // #641: az ablak nem mehet olyan kicsire, hogy a szerkesztő bal panelje
    // ne férjen el — különben a Visszavonás/Újra sor kicsúszik a látható
    // területről, és a felhasználó egyáltalán nem látja. A #628 a panel
    // `implicitHeight`-jét már kiszámolta, de a garanciát egy
    // `Layout.minimumHeight`-re bízta, amit semmi nem érvényesít az ablak
    // szintjén — ez az a hely, ahol érvényesíteni kell.
    minimumHeight: photoViewer.requiredHeight
                   + (window.menuBar ? window.menuBar.height : 0)
    // #1367: az ablak nem mehet olyan keskenyre, hogy az alsó
    // műveletsáv kilógjon — a #1345 fix gombcellái óta a sáv nem
    // zsugorodik tovább. Az igény MÉRT (ld. `TrayBar.requiredWidth`),
    // és őr-teszt méri újra élőben.
    minimumWidth: trayBar.requiredWidth
    visible: true
    title: "PicasaPy"
    color: Theme.lightboxBg

    // #28: a téma a Theme-tokenekből jön, azok pedig a controller
    // kapcsolójából — az OS saját sötét módja sehol nem üthet át, a
    // váltás kizárólag a Nézet → Sötét téma menüponté (alapértelmezés:
    // világos; ld. design-guide).
    Binding {
        target: Theme
        property: "dark"
        value: controller ? controller.darkTheme : false
    }

    palette {
        window: Theme.canvasBg
        windowText: Theme.ink
        base: Theme.controlBase
        alternateBase: Theme.panelBg
        text: Theme.ink
        button: Theme.buttonBg
        buttonText: Theme.ink
        highlight: Theme.selectionBlue
        highlightedText: Theme.panelSelectionText
        placeholderText: Theme.placeholderText
        mid: Theme.chromeBorder
        light: Theme.shadeLight
        dark: Theme.shadeDark
    }

    // #985: a globális `controller` egy KONTEXTUS-property, a `CollagePanel`
    // viszont saját `controller` property-t deklarál (hogy a komponens-
    // tesztekben becserélhető legyen). A `controller: controller` sor ezért
    // önmagára kötne (kötési hurok) — ez az álnév oldja fel, egy helyen.
    readonly property var appController: controller

    property int thumbSize: 144
    property int selectedIndex: -1        // horgony (utoljára kattintott)
    property var selectedIndexes: []      // a teljes kijelölés
    // #142: a kijelölés set-alakban (sor → true) — a rács-cellák O(1)
    // lookupja; az indexOf-os kötés O(cellák × kijelöltek) volt, ami
    // Ctrl+A-nál minden cellán végigjárta a teljes kijelölés-listát
    property var selectedSet: ({})
    onSelectedIndexesChanged: {
        var s = {}
        for (var k = 0; k < selectedIndexes.length; ++k)
            s[selectedIndexes[k]] = true
        selectedSet = s
    }
    property bool viewerOpen: false
    property bool timelineOpen: false     // Időrend nézet (#24, Ctrl+5)
    // #1773: a jobb fiók négy lapja KIZÁRÓ csoport — egyszerre pontosan
    // egy látszik, vagy a fiók üres. Ezért EGYETLEN állapot írja le mind a
    // négyet; négy független billenőből a mérés szerint nem előfordulható
    // állapotok álltak elő (négy panel egyszerre nyitva).
    //
    // MÉRVE (`0x005d9760`, mind a négy ág): a vezérlő elrejti a másik
    // hármat, kikapcsolja a másik három fejléc-gombot, bekapcsolja a
    // sajátját, majd megjeleníti a saját panelt.
    //
    // Az érvényes értékek: "" (a fiók üres) · "tags" · "places" ·
    // "properties" · "people".
    property string activeDrawerTab: ""

    // A négy régi jelző SZÁRMAZTATOTT — a kötések és a menüpipák
    // változatlanul rájuk hivatkoznak, de már nem írhatók külön-külön.
    readonly property bool tagsPanelOpen:
        window.activeDrawerTab === "tags"        // Címkék-panel (#12, Ctrl+T)
    readonly property bool placesPanelOpen:
        window.activeDrawerTab === "places"      // Helyek-panel (#30, térkép)
    // Tulajdonságok-panel (#13, Alt+Enter)
    readonly property bool propertiesPanelOpen:
        window.activeDrawerTab === "properties"
    // Emberek-panel (#26) — a jobb fiók negyedik panelje
    // (`rightdrawerpanel/peoplepanel`), a Címkék/Helyek/Tulajdonságok mellett
    readonly property bool peoplePanelOpen:
        window.activeDrawerTab === "people"

    // #1773: a lapváltás EGYETLEN útja. Az aktív lapra kattintás
    // SZÁNDÉKOSAN nem zár be: a bináris a vizsgált ágon feltétel nélkül
    // 1-re állítja a saját gombját (a jegy „nyitott" pontja, ez az
    // alapértelmezés). A fiók ürítése az `ureseidAFiokot()`.
    function valtsFiokLapot(nev) {
        window.activeDrawerTab = nev
    }
    function ureseidAFiokot() {
        window.activeDrawerTab = ""
    }
    // #26 (3. lépcső): a „Névtelenek" nézet — a fő rács helyén jelenik
    // meg, amíg be van kapcsolva (ld. UnnamedFacesView.qml)
    property bool unnamedFacesOpen: false
    // #26: melyik arc-album van nyitva — „unnamed" vagy „ignored"
    // (`CAlbumLabel::Ignored` = „Mellőzött emberek")
    property string facesAlbumMode: "unnamed"
    // #1236: külön ablak-szintű név kell. Az UnnamedFacesView azonos nevű
    // property-jének jobb oldalán a `faceScanController` önmagára oldódna.
    readonly property var _faceScanController:
        typeof faceScanController !== "undefined" ? faceScanController : null
    // a jobbklikkelt kép sora (#15) — a kontextusmenü egyedi műveleteinek
    // (átnevezés, fájlkezelő) célpontja
    property int fileOpTargetRow: -1

    // -- Dokumentum-lapok (#985; a sáv maga a #944) -------------------------
    //
    // Az eredetiben a kollázs NEM párbeszédablak, hanem SAJÁT LAP a fülsávban
    // (`panelroot/collagetab`), a „Könyvtár" lapja mellett — ld.
    // `docs/specs/kollazs-panel-ui-spec.md` 3.1. Ma egyetlen projekt-laptípus
    // van, a kollázs; a lista mégis lista, mert a sáv szerződése az.
    readonly property string collageTabId: "collage"
    readonly property var openProjectTabs:
        (controller && controller.collageOpen)
            ? [{
                id: window.collageTabId,
                title: qsTr("Collage"),
                modified: controller.collageDirty === true
              }]
            : []

    // #1026: a KÖNYVTÁR PANELJE — EGYETLEN kapcsoló, nem sávonkénti elrejtés.
    //
    // Az eredetiben a `panelroot/collagepanel` a `panelroot/mainuipanel`
    // TESTVÉRE, nem melléje kerül: a felső éle a fülsáv alatt van
    // (`YConstraint 0, 0, tabdiv`), az alsó az ablak alján
    // (`YConstraint 1, 1, 0`). A könyvtár teljes kerete viszont a
    // `mainuipanel` GYEREKE (`thumbui.tre`: `importbutton`, `sbutton`,
    // `timelinebutton`, `globalmode`, `bottombevel_base`, és a kimeneti sáv
    // az `outputlayout.tre`-ből). Vagyis a projekt-lapon nem két sáv
    // „rejtőzik el", hanem a könyvtár panelja tűnik el EGÉSZBEN — és a
    // vászon ezért kapja meg a fülsáv alatti TELJES területet, az ablak
    // aljáig (a felhasználó két képernyőképe ezt a különbséget mutatta).
    //
    // Ezért egy kapcsoló és nem három külön kötés: aki új darabot tesz a
    // könyvtár keretébe, erre köti — így nem maradhat ott egy elfelejtett
    // sáv. A menüsor és a fülsáv MINDKÉT panelen kívül van (`panelroot`),
    // azokat ez nem érinti.
    //
    // A néző/szerkesztő NEM projekt-lap: az a mai módon fedi le a
    // könyvtárat a saját kötéseivel, azon ez a kapcsoló nem változtat.
    readonly property bool libraryFrameVisible:
        documentTabStrip.libraryActive || window.viewerOpen

    // A „Vissza a kollázshoz" gomb csak a „Továbbiak..." után jelenik meg
    // (spec 4.3/13.): az eredeti is AKKOR rakja a könyvtár lapjára.
    property bool backToCollagePrompted: false

    // A kollázs forrása a mai `_sources_for` szabályt követi (#455): ha a
    // képtálcán van kép, AZ a forrás, egyébként a rács kijelölése.
    //
    // ⚠️ A tálca mappákon átnyúlik, a `openCollage` viszont RÁCS-SOROKAT vár
    // (#943 API). A jelenlegi mappán kívüli tálcaképeket ezért nem tudjuk
    // átadni — olyankor a kijelölésre esünk vissza. Az útvonal-alapú
    // megnyitás külön jegy; itt szándékosan nem építünk mellé második
    // forrás-szabályt.
    function collageSourceRows() {
        if (!controller) return []
        var held = controller.heldPaths || []
        var rows = []
        for (var i = 0; i < held.length; ++i) {
            var row = controller.photos.rowOfPath(String(held[i]))
            if (row >= 0) rows.push(row)
        }
        if (rows.length > 0) return rows
        return window.selectedRows()
    }

    /** A Kollázs LAP megnyitása — a Létrehozás menü és a tálca gombja is ide
        fut be (spec 3.2). Ha már nyitva van, csak visszaváltunk rá: a
        felhasználó munkáját újranyitással eldobni némán adatvesztés volna. */
    function openCollageTab() {
        if (!controller) return
        window.backToCollagePrompted = false
        // #1055: a NÉZŐT (és vele a szerkesztőt) el kell hagyni. A kollázs
        // panelje `!viewerOpen`-re látszik, a képtálca kollázs-gombja
        // viszont a nézőben IS ott van (`libraryFrameVisible`) — enélkül a
        // lap megnyílik, a kollázs elkészül, és a felhasználó közben a
        // mappanézetet látja. Pontosan ezt jelentette a v0.8.7-en.
        window.viewerOpen = false
        if (!controller.collageOpen)
            controller.openCollage(window.collageSourceRows())
        documentTabStrip.activateTab(window.collageTabId)
    }

    /** Egy KÉSZ kollázs újranyitása szerkesztésre (#1002).

        A tulajdonos jelentése a v0.8.17-ről: *„Jelenleg ennek hiányában nem
        szerkeszthető a kollázs."* — a kész képtől nem vezetett vissza út a
        panelra.

        A nézőt elhagyjuk (#1055): a kollázs panelje `!viewerOpen`-re
        látszik, tehát enélkül a lap megnyílna, és a felhasználó közben a
        képet nézné. */
    function openSavedCollage(path) {
        if (!controller) return
        var cel = String(path || "")
        if (cel.length === 0) return
        controller.openCollageProject(cel)
        if (!controller.collageOpen) return
        window.viewerOpen = false
        window.backToCollagePrompted = false
        documentTabStrip.activateTab(window.collageTabId)
    }

    /** A KÉSZ kollázs megkeresése a könyvtárban (#1028).

        Az eredeti mentő négy záró lépése közül ez a negyedik: `locate` az
        új fájlra. A lap bezárása (harmadik lépés) már megvan — az a
        `CollagePanel.finishSave` dolga; ide a NAVIGÁCIÓ tartozik.

        ⚠️ Nézőt szándékosan NEM nyit: az eredeti is csak kijelöl, a
        nagyban megnyitás a felhasználó kattintása az értesítésen. */
    function locateSavedCollage(path) {
        if (!controller) return
        var cel = String(path || "")
        if (cel.length === 0) return
        var sor = controller.photos.rowOfPath(cel)
        if (sor < 0) {
            // A Kollázsok mappa tipikusan NEM a jelenlegi nézet: előbb oda
            // állunk, aztán kérdezünk újra. (Az indexbe a mentés veszi fel,
            // #1048 — enélkül a mappa üres volna.)
            var mappa = window.folderOfPath(cel)
            if (mappa.length > 0) {
                controller.selectFolder(mappa)
                sor = controller.photos.rowOfPath(cel)
            }
        }
        documentTabStrip.activateTab(documentTabStrip.libraryTabId)
        if (sor >= 0) {
            window.selectedIndex = sor
            window.selectedIndexes = [sor]
        }
        // #1119: a RENDES létrehozás után NINCS értesítés. A
        // `collage::done` értesítő a binárisban az „Asztali háttérkép"
        // ágához tartozik (a `0x0057aa10` a `Control Panel\\Desktop\\`
        // registrykulcsot és a `picasabackground.bmp`-t mozgatja), nem a
        // rendes kollázs-készítéshez. A tulajdonos háromszor jelezte, hogy
        // ilyen gomb a Picasa 3-ban nincs.
        //
        // ⚠️ A `CollageDoneNotice` komponens SZÁNDÉKOSAN marad: az
        // „Asztali háttérkép" ágé, aminek a bekötése külön jegy (ma a
        // `collageDesktopBackgroundReady` jelzésnek nincs fogadója).
        // A törlése visszafejlesztés volna.
    }

    /** Egy fájl útvonalának a mappája. A QML-ben nincs `Path`, a
        csomópont-útvonal pedig a PLATFORM elválasztóját hozza (a kollázs
        `Path`-ból építi, tehát Windowson fordított perjellel). */
    function folderOfPath(path) {
        var szoveg = String(path)
        var vago = Math.max(szoveg.lastIndexOf("/"), szoveg.lastIndexOf("\\"))
        return vago > 0 ? szoveg.substring(0, vago) : ""
    }

    /** #1001: a kollázs „Megjelenítés és szerkesztés" parancsa — a képet a
        SZERKESZTŐBEN nyitja meg.

        A vezérlő csak az ÚTVONALAT ismeri (`collageEditRequested`), a
        szerkesztő — nálunk a néző bal panelje — viszont SORINDEXET vár; a
        fordítás itt történik. A jelzésnek eddig egyetlen fogadója sem volt,
        ezért mindhárom belépési pont (gomb, duplakattintás, helyi menü)
        hatástalan maradt.

        Az eredetiben a `view_and_edit` a képet a KÖNYVTÁRBAN nyitja meg
        (`picasa-kollazs-felulet.md` 5.), a kollázs lapja pedig NYITVA marad
        — ezért váltunk a Könyvtár lapjára, és ott nyílik a szerkesztő. A
        visszautat a már meglévő „Vissza a kollázshoz" gomb adja (a
        „Továbbiak..." mintája, `kollazs-panel-ui-spec.md` 4.3/13.): a
        szerkesztő bezárása után ott áll a könyvtár lapján. */
    function openCollageNodeInEditor(path) {
        if (!controller) return
        var cel = String(path || "")
        if (cel.length === 0) return
        var sor = controller.photos.rowOfPath(cel)
        if (sor < 0) {
            // A kollázs képei mappákon átnyúlhatnak (a „+" gomb más mappából
            // is vehet fel klipet), a feed pedig szűrve/keresve szűkebb
            // lehet: előbb a kép mappájára állunk, aztán újra kérdezünk.
            var mappa = window.folderOfPath(cel)
            if (mappa.length > 0) {
                controller.selectFolder(mappa)
                sor = controller.photos.rowOfPath(cel)
            }
        }
        // Néma bukás helyett sem tehetünk mást: a kép nincs az indexben (pl.
        // időközben törölték). A kollázs lapja érintetlen marad.
        if (sor < 0) return

        window.backToCollagePrompted = true
        documentTabStrip.activateTab(documentTabStrip.libraryTabId)
        window.selectedIndex = sor
        window.selectedIndexes = [sor]
        window.viewerOpen = true
        photoViewer.show(sor)
    }

    // a kijelölt sorok listája (#12) — több-kijelölés, vagy ha az nincs,
    // az utoljára kattintott kép
    function selectedRows() {
        return Selection.effectiveRows(
            window.selectedIndexes, window.selectedIndex)
    }

    // a kijelölt képek abszolút útvonalai (#15/#16) — a fájlműveletek a
    // művelet ELŐTT gyűjtött útvonal-listán futnak, így a közben frissülő
    // rács-indexek nem tévesztenek célt
    function selectedPaths() {
        var rows = window.selectedRows()
        var paths = []
        for (var k = 0; k < rows.length; ++k) {
            var p = controller.photos.filePathAt(Number(rows[k]))
            if (p.length > 0) paths.push(p)
        }
        return paths
    }

    // jobbklikk a rácson (#15): a klikkelt kép kerüljön kijelölésbe (ha még
    // nincs benne), majd a kontextusmenü a kattintás helyén nyílik
    function openPhotoContextMenu(index, item, x, y) {
        if (window.selectedIndexes.indexOf(index) === -1) {
            window.selectedIndexes = [index]
            window.selectedIndex = index
        }
        window.fileOpTargetRow = index
        photoContextMenu.popup(item, x, y)
    }

    // Kijelölés-logika (Picasa): sima katt = egy kép; Ctrl = hozzávesz/
    // elvesz; Shift = tartomány a horgonytól. (Számítás: selection.js)
    function handleThumbClick(index, modifiers) {
        var i = Number(index)
        var mods = Number(modifiers)
        if (mods & Qt.ControlModifier) {
            window.selectedIndexes =
                Selection.toggled(window.selectedIndexes, i)
            window.selectedIndex = i
        } else if ((mods & Qt.ShiftModifier) && window.selectedIndex >= 0) {
            // #1219: a tartomány a HORGONY mappacsoportján belül marad —
            // az eredetiben a tartomány-mag mindig egyetlen album
            // kijelölés-csomópontján fut, nem tud mappahatárt átlépni.
            var hatar = controller.photos.groupRange(window.selectedIndex)
            var veg = i
            if (hatar.length === 2)
                veg = Math.max(hatar[0], Math.min(hatar[1], i))
            window.selectedIndexes =
                Selection.range(window.selectedIndex, veg)
        } else {
            window.selectedIndexes = [i]
            window.selectedIndex = i
        }
    }
    // ⚠️ #1145: MAPPAVÁLTÁSKOR a kijelölés törlődik.
    //
    // Az eredetiben az előző mappa kijelölés-csomópontját a program
    // elengedi (`0x0056bc10` → `0x718a50`), és a helyére az újat teszi.
    // Nálunk a kijelölés túlélte a váltást — így egy másik mappában
    // végzett művelet (csillag, forgatás, törlés) a KORÁBBI mappa képeire
    // hatott volna.
    //
    // A `currentFolder` a `statusChanged`-en jelez, ezért a mappa saját
    // értékét figyeljük, nem a jelzést: így csak VALÓDI váltásra törlünk.
    property string _lastFolder: ""
    Connections {
        target: controller
        function onStatusChanged() {
            var folder = controller ? controller.currentFolder : ""
            if (folder === window._lastFolder) return
            window._lastFolder = folder
            // #1183: ha a kijelölés MÁR az új mappában van, akkor a váltást
            // épp a rács fókusza okozta (a felhasználó ott kattintott) —
            // nincs mit elengedni, az előző mappáé úgyis lecserélődött.
            if (window._selectionInFolder(folder)) return
            window.clearSelection()
        }
    }

    // #1183: a fókuszsor mappája — a bal hasáb kiemelése ezt követi
    function _folderOfRow(row) {
        if (!controller || row < 0) return ""
        var groups = controller.feedGroups
        if (!groups) return ""
        for (var i = 0; i < groups.length; ++i) {
            var g = groups[i]
            if (row >= g.start && row < g.start + g.count) return g.path
        }
        return ""
    }

    function _selectionInFolder(path) {
        return path !== "" && window._folderOfRow(window.selectedIndex) === path
    }

    // A rács fókusza vezeti a jelenlegi mappát (az eredetiben `0x0056bc10`
    // → `0x56b910`, „a jelenlegi album megváltozott"). Egy helyen kötjük be,
    // így a kattintás, a nyilas léptetés és a programból állított fókusz is
    // ugyanígy viselkedik.
    onSelectedIndexChanged: {
        var folder = window._folderOfRow(window.selectedIndex)
        if (folder !== "" && controller) controller.focusFolder(folder)
    }

    function clearSelection() {
        window.selectedIndexes = []
        window.selectedIndex = -1
    }
    // ⚠️ #1145: a kijelölés hatóköre a JELENLEGI MAPPA, nem a teljes feed.
    //
    // Az eredetiben az „Az összes kijelölése" (`0x9cb8`) kezelője
    // (`0x005e5070`) EGYETLEN kijelölés-csomóponton dolgozik, és az EGY
    // mappához tartozik (`CSelectionNode + 0x3c0`). A Picasában
    // egyáltalán nem létezik mappákon átnyúló kijelölés.
    //
    // Nálunk a Ctrl+A tízezres nagyságrendű sort jelölt ki — a tulajdonos
    // ezt jelentette (#1184), és emiatt „majdnem lefagyott az app".
    //
    // A csoportot a jelenlegi kijelölés/fókusz sora dönti el; ha nincs
    // ilyen, a jelenlegi mappa csoportja.
    function _currentGroup() {
        if (!controller) return null
        var groups = controller.feedGroups
        if (!groups || groups.length === 0) return null
        var row = window.selectedIndex
        if (row >= 0) {
            for (var i = 0; i < groups.length; ++i) {
                var g = groups[i]
                if (row >= g.start && row < g.start + g.count) return g
            }
        }
        var current = controller.currentFolder
        for (var j = 0; j < groups.length; ++j)
            if (groups[j].path === current) return groups[j]
        return groups[0]
    }

    function _groupRows() {
        var g = window._currentGroup()
        if (!g) return Selection.allRows(controller.photos.rowCount())
        var rows = []
        for (var i = g.start; i < g.start + g.count; ++i) rows.push(i)
        return rows
    }

    function selectAll() {
        var range = window._groupRows()
        window.selectedIndexes = range
        if (range.length > 0) window.selectedIndex = range[0]
    }
    // #422: „Kiválasztás megfordítása" (Ctrl+I) — a mappa-kontextusmenü és
    // a Szerkesztés menü tétele
    function invertSelection() {
        // #1145: a megfordítás is a jelenlegi mappán belül marad
        var scope = window._groupRows()
        var current = window.selectedIndexes
        var rows = []
        for (var i = 0; i < scope.length; ++i)
            if (current.indexOf(scope[i]) === -1) rows.push(scope[i])
        window.selectedIndexes = rows
        window.selectedIndex = rows.length > 0 ? rows[0] : -1
    }
    // #426: „Csillagozottak kijelölése" (Szerkesztés menü) — a jelenlegi
    // nézet csillagos képeit jelöli ki (NEM a Mappák panel nézet-szűrője).
    function selectStarred() {
        // #1145: a csillagozottak is a jelenlegi mappából
        var scope = window._groupRows()
        var rows = []
        for (var i = 0; i < scope.length; ++i)
            if (controller.photos.starAt(scope[i])) rows.push(scope[i])
        window.selectedIndexes = rows
        window.selectedIndex = rows.length > 0 ? rows[0] : -1
    }
    // #422: „Exportálás HTML-oldalként…" a mappa-kontextusmenüből — a
    // dialógus itt él (a menüsáv is ezt nyitja)
    function openWebExport() { webExportDialog.open() }
    // #1472: nyomtatás — HÁROM belépési pont vezet ide (Fájl ▸ Nyomtatás…,
    // Ctrl+P, és a képtálca „Nyomtatás" gombja), ahogy az exportnál is.
    // A célpont ugyanaz a HÁROM ág, mint a `rotateTargetRow()`-nál:
    // diavetítés közben a VETÍTETT kép, a nézőben a MEGJELENÍTETT kép, a
    // rácsban a kijelölés.
    //
    // ⚠️ A diavetítés ága nem elhagyható: a `startSlideshow()` NEM állítja
    // a `viewerOpen`-t, tehát a menü és a Ctrl+P vetítés közben is
    // engedélyezett marad — enélkül a felhasználó egy képet néz, és a
    // RÁCS kijelölése menne nyomtatásra.
    function printTargetRows() {
        if (slideshow.visible)
            return slideshow.currentIndex >= 0 ? [slideshow.currentIndex] : []
        if (window.viewerOpen)
            return photoViewer.currentIndex >= 0
                ? [photoViewer.currentIndex] : []
        return window.selectedRows()
    }
    function openPrint() { printDialog.ensure().openForRows(window.printTargetRows()) }
    // #1590: Mappa ▸ Bélyegképek nyomtatása… — ugyanaz a párbeszéd,
    // indexkép-elrendezésre állítva. Kijelölés nélkül a MEGNYITOTT MAPPA
    // egésze a célpont: az eredetiben ez a parancs a mappa/album tétele,
    // nem a kijelölésé.
    function openContactSheetPrint() {
        var sorok = window.printTargetRows()
        // a `_groupRows` a MEGNYITOTT mappa sorai (nem az egész rácsé,
        // ha az több mappát mutat) — pontosan az, amire a mappa-menü
        // tétele vonatkozik
        if (sorok.length === 0) sorok = window._groupRows()
        printDialog.ensure().openForContactSheet(sorok)
    }
    // #422: a mappa-kontextusmenünek HÁROM megnyitási pontja van (a rács
    // üres területe, a bal panel mappa-sora, a rács mappa-fejléce), és
    // mindhárom UGYANAZT a menüt nyitja. A menü a FolderPane-ben él; a
    // másik két hívó ezen az ablak-szintű átjárón éri el.
    function openFolderContextMenu(path) {
        var target = path && path.length > 0
            ? path : (controller ? controller.currentFolder : "")
        if (target.length > 0) folderPane.openFolderContextMenu(target)
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
        target: controller ? controller.photos : null
        function onModelAboutToBeReset() {
            var ids = []
            for (var k = 0; k < window.selectedIndexes.length; ++k) {
                var id = controller.photos.idAt(Number(window.selectedIndexes[k]))
                if (id.length > 0) ids.push(parseInt(id, 10))
            }
            window._pendingSelectedIds = ids
            window._pendingAnchorId = window.selectedIndex >= 0
                ? controller.photos.idAt(window.selectedIndex) : ""
        }
        function onModelReset() {
            window.selectedIndexes = Selection.remapByIds(
                window._pendingSelectedIds, controller.photos.rowOfId)
            window.selectedIndex = window._pendingAnchorId.length > 0
                ? controller.photos.rowOfId(parseInt(window._pendingAnchorId, 10))
                : -1
        }
    }

    Shortcut { sequence: "Ctrl+A"; onActivated: window.selectAll() }
    Shortcut { sequence: "Ctrl+D"; onActivated: window.clearSelection() }
    Shortcut { sequence: "Ctrl+I"; onActivated: window.invertSelection() }
    // #444: „Mentés" — a Fájl menü ígéri a Ctrl+S-t, tehát élnie is kell
    // (a menü-audit teszt épp ezt kéri számon). Kijelölés nélkül nem tesz
    // semmit: a `openSave` üres listára visszatér.
    Shortcut {
        sequence: "Ctrl+S"
        onActivated: saveDialogs.ensure().openSave(window.selectedIndexes)
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
        window.activeFocusItem !== null
        && window.activeFocusItem.selectedText !== undefined

    Shortcut {
        // A `StandardKey.Copy` linuxon ugyanez, de a menü-audit a
        // szekvenciát SZÖVEGES alakban keresi — és joggal: a menü szó
        // szerint Ctrl+C-t hirdet, tehát az ígéret is szó szerinti.
        // (⚠️ A komment maga sem tartalmazhatja a keresett mintát: az
        // első változatom épp ezzel vezette félre a mérést.)
        sequence: "Ctrl+C"
        enabled: !window._szovegmezoneVanFokusz
        onActivated: fileOpsController.copyFilesToClipboard(
            window.selectedPaths())
    }
    Shortcut {
        sequence: "Ctrl+X"
        enabled: !window._szovegmezoneVanFokusz
        onActivated: fileOpsController.cutFilesToClipboard(
            window.selectedPaths())
    }

    // Picasa gyorsbillentyűk: Ctrl+R jobbra, Ctrl+Shift+R balra forgat.
    // Diavetítés közben (#8) a vetített kép a célpont, nem a rács-kijelölés.
    function rotateTargetRow() {
        if (slideshow.visible) return slideshow.currentIndex
        return trayBar.starTargetRow
    }
    // #103: csak-videó célpontnál a forgatás tiltott — a tálca ↺/↻
    // gombjainak őre (a controller-slotok defenzíven szintén kihagyják
    // a videókat, vegyes kijelölésnél csak a fotók forognak)
    function rotateTargetsAllVideo() {
        // #305: null-őr — a TrayBar `enabled:` kötése (ami ezt hívja)
        // a QML-engine leépítésekor is újraértékelődhet
        if (!controller) return false
        var rows = window.viewerOpen
            ? [photoViewer.currentIndex]
            : window.selectedRows()
        if (rows.length === 0) return false
        for (var k = 0; k < rows.length; ++k)
            if (!controller.photos.isVideoAt(Number(rows[k])))
                return false
        return true
    }
    Shortcut {
        sequence: "Ctrl+R"
        onActivated: {
            var row = window.rotateTargetRow()
            if (row >= 0) controller.rotateRight(row)
        }
    }
    Shortcut {
        sequence: "Ctrl+Shift+R"
        onActivated: {
            var row = window.rotateTargetRow()
            if (row >= 0) controller.rotateLeft(row)
        }
    }
    // #8: Ctrl+4 — diavetítés (Picasa-billentyű)
    Shortcut {
        sequence: "Ctrl+4"
        onActivated: window.startSlideshow(-1)
    }
    // #12: Ctrl+T — Címkék-panel (Picasa-billentyű); a könyvtár-nézetben él
    Shortcut {
        sequence: "Ctrl+T"
        onActivated: if (!window.viewerOpen)
                         // #1773: a billentyű BILLENT (a menütétel nem) —
                         // a Ctrl+T nyitja, és zárja is a fiókot
                         window.tagsPanelOpen ? window.ureseidAFiokot()
                                              : window.valtsFiokLapot("tags")
    }
    // #13: Alt+Enter — Tulajdonságok-panel (Picasa-billentyű)
    Shortcut {
        sequence: "Alt+Return"
        onActivated: if (!window.viewerOpen)
                         window.propertiesPanelOpen
                             ? window.ureseidAFiokot()
                             : window.valtsFiokLapot("properties")
    }

    // -- időrend nézet (#24, Ctrl+5) -----------------------------------------
    // A teljes könyvtár dátum szerinti, korszakokra bontott áttekintése
    // (TimelineView.qml) — a nézőt nem lehet vele egyszerre nyitva tartani,
    // a diavetítéshez hasonlóan (startSlideshow) teljes képernyős réteg.
    function toggleTimeline() {
        if (window.timelineOpen) {
            window.timelineOpen = false
            return
        }
        timelineController.reload()
        window.timelineOpen = true
    }
    Shortcut {
        sequence: "Ctrl+5"
        onActivated: window.toggleTimeline()
    }

    // -- diavetítés (#8) ----------------------------------------------------
    // Indítás: viszonyítási pont a néző képe / a rács-kijelölés / az első
    // kép; a vetítés valódi teljes képernyőn fut, kilépéskor az ablak
    // visszaáll, és a rács/néző követi a vetítés utolsó képét.
    property int visibilityBeforeSlideshow: Window.Windowed
    function startSlideshow(fromIndex) {
        var index = fromIndex
        if (index < 0)
            index = window.viewerOpen ? photoViewer.currentIndex
                                      : Math.max(0, window.selectedIndex)
        window.visibilityBeforeSlideshow = window.visibility
        window.visibility = Window.FullScreen
        slideshow.start(index)
        if (!slideshow.visible)   // nincs vetíthető fotó — állítsuk vissza
            window.exitSlideshow()
    }
    function exitSlideshow() {
        window.visibility =
            window.visibilityBeforeSlideshow === Window.FullScreen
                ? Window.Windowed : window.visibilityBeforeSlideshow
        if (slideshow.currentIndex >= 0) {
            if (window.viewerOpen) {
                photoViewer.show(slideshow.currentIndex)
            } else {
                window.selectedIndex = slideshow.currentIndex
                window.selectedIndexes = [slideshow.currentIndex]
            }
        }
    }
    // Picasa: F2 = átnevezés, Ctrl+Shift+S = exportálás mappába
    Shortcut {
        sequence: "F2"
        onActivated: if (!window.viewerOpen && window.selectedIndex >= 0)
                         fileOpsDialogs.openRename(window.selectedIndex)
    }
    Shortcut {
        sequence: "Ctrl+Shift+S"
        onActivated: if (!window.viewerOpen) exportDialogs.ensure().openForSelection()
    }
    // #422: a rács kontextusmenüje `Ctrl+Delete`-et hirdet a lemezről
    // törléshez (spec 3.) — a billentyű eddig nem élt, csak a Fájl menü
    // `Delete`-je (ld. ui-audit-menus.md). Mindkettő ugyanoda vezet.
    Shortcut {
        objectName: "shortcutDeleteFromDiskGrid"
        sequence: "Ctrl+Delete"
        enabled: !window.viewerOpen && window.selectedRows().length > 0
        // #1619: a `Ctrl+Delete` UGYANAZ a parancs (`0x9c9a`), csak másik
        // belépő — ezért a #1608-ban készült KÖZÖS elágazáson megy át,
        // nem másolt logikán. Albumban/Emberek-albumban eltávolít, nem
        // lemezről töröl (spec 5.); mappában változatlanul töröl.
        onActivated: picasaMenuBar.activateDeleteCommand()
    }
    // #422: a nézőben PUSZTA Delete törli a lemezről (spec 3.) — ott nincs
    // ütközés, mert a rács album-parancsai nem élnek
    Shortcut {
        objectName: "shortcutDeleteFromDiskViewer"
        // #1418: a nézőben (jobbklikk-menüs felület) `Ctrl+Delete` a helyes,
        // nem a puszta `Delete` — a #1154 mérése szerint a `0x9c9a` parancs
        // felület szerint válik szét: menüsávban `Delete`, helyi menükben
        // `Ctrl+Delete`. A korábbi `Delete` a #422 azóta felülírt feltevése
        // volt.
        sequence: "Ctrl+Delete"
        enabled: window.viewerOpen && photoViewer.currentIndex >= 0
        onActivated: {
            var p = controller.photos.filePathAt(photoViewer.currentIndex)
            if (p.length > 0) fileOpsDialogs.openDelete([p])
        }
    }

    // #922: a képtálca tartalma ÁLLAPOTKÉNT, nem közvetlen kötésként. Egy
    // `controller.heldCount`-ra épülő kötés a `controller` null állapotában
    // ki tud értékelődni ELŐSZÖR — olyankor a QML nem regisztrálja a
    // függőséget, és a kötés soha többé nem frissül. Ez a `Connections`
    // ettől független.
    property bool trayHasPictures: false
    Connections {
        target: controller
        function onHeldChanged() {
            window.trayHasPictures = controller.heldCount > 0
        }
    }
    menuBar: PicasaMenuBar {
        // #1619: a rács `Ctrl+Delete`-je is ezen a példányon át ágazik el
        id: picasaMenuBar
        photoActionsEnabled: !window.viewerOpen
                             && window.selectedIndexes.length > 0
        // #922: a kollázs/film a TÁLCA tartalmán is dolgozik (#455) —
        // a menüpontnak ezért tálcával, kijelölés nélkül is élnie kell
        createActionsEnabled: !window.viewerOpen
                              && (window.selectedIndexes.length > 0
                                  || window.trayHasPictures)
        onRescanRequested: controller.rescan()
        // #1526: a fájl-vágólap — a kijelölt képek fájljai kerülnek fel,
        // így egy fájlkezelőbe közvetlenül beilleszthetők
        onCopyFilesRequested: fileOpsController.copyFilesToClipboard(
            window.selectedPaths())
        onCutFilesRequested: fileOpsController.cutFilesToClipboard(
            window.selectedPaths())
        // #1595: a Mappa menü négy tétele a MEGNYITOTT mappára hat. A
        // párbeszédek és a megerősítések a bal hasábon élnek (ott van a
        // mappa helyi menüje is), ezért onnan hívjuk: egy művelet, egy út.
        onFolderMoveRequested: {
            if (controller) folderPane.mozgatasMappara(controller.currentFolder)
        }
        onFolderDeleteRequested: {
            if (controller) folderPane.torlesLomtarba(controller.currentFolder)
        }
        onFolderRemoveFromPicasaRequested: {
            if (controller)
                folderPane.eltavolitasAPicasabol(controller.currentFolder)
        }
        onFolderLocateRequested: {
            if (controller && controller.currentFolder.length > 0)
                fileOpsController.revealFolder(controller.currentFolder)
        }
        onAboutRequested: aboutDialog.open()
        onThumbSizePreset: function(size) { window.thumbSize = size }
        // #426: „Csillagozottak kijelölése" (Szerkesztés menü) — kijelöl,
        // nem szűr (a Mappák panel „Csillagozott" nézete külön: onStarredChosen)
        onSelectStarredRequested: window.selectStarred()
        onSelectAllRequested: window.selectAll()
        onClearSelectionRequested: window.clearSelection()
        // #1686: UGYANAZ a belépő, amit a Ctrl+I és a mappahasáb helyi
        // menüje is hív — nincs másolt logika.
        onInvertSelectionRequested: window.invertSelection()
        onFolderManagerRequested: folderManager.open()
        onDedupRequested: dedupDialog.open()
        // #1473: Eszközök → Arcok keresése…
        onFaceScanRequested: faceScanDialog.open()
        // #350: Eszközök → Beállítások…
        onOptionsRequested: optionsDialog.open()
        // #351: Exportálás weboldalként
        onWebExportRequested: webExportDialog.open()
        // #530: Google Earth-export — a folyamat az ExportDialogs-ban él
        onEarthExportRequested: exportDialogs.ensure().openGoogleEarth()
        // #1589: ugyanaz a párbeszéd, de a kiírás után MEGNYITJA a fájlt
        onEarthViewRequested: exportDialogs.ensure().openGoogleEarth(true)
        // #366: több kijelölt képnél a tömeges átnevezés-dialógus nyílik
        onRenameRequested: window.selectedIndexes.length > 1
            ? fileOpsDialogs.openRenameMany(window.selectedIndexes)
            : fileOpsDialogs.openRename(window.selectedIndex)
        // #368: adatbázis-áthelyezés a Kísérleti menüből
        onMoveDatabaseRequested: moveDatabaseDialog.open()
        // #449: adatbázis-tömörítés (`compacting.fen`)
        onCompactDatabaseRequested: compactDatabaseDialog.open()
        // #936: a Létrehozás menü jelzésének NEM VOLT kezelője — a
        // menüpont elsütötte a jelzést, és az a semmibe ment. Az
        // egyetlen kezelő a képtálca sávján ült (`trayBar`), ezért
        // onnan indítva működött, a menüből nem.
        // #985: a menüpont mostantól a KOLLÁZS LAPOT nyitja meg, nem a
        // korábbi modális párbeszédet (spec 3.2: „modálist nyit → a lapot
        // nyitja meg"). A `CreateDialogs` kollázs-ága egyelőre a helyén
        // marad — a leszerelése külön jegy.
        onCollageRequested: window.openCollageTab()
        onMovieRequested: createDialogs.openMovie()
        onExportRequested: exportDialogs.ensure().openForSelection()
        // #1616: Fájl ▸ Új album… / Ctrl+N — UGYANAZT az `openNewAlbum`
        // belépőt hívja, amit a rács helyi menüjének „Új album…" tétele is
        // (a `PhotoContextMenu.onNewAlbumRequested` kötése lentebb, a
        // helyi menü példányán)
        onNewAlbumRequested: fileOpsDialogs.openNewAlbum(window.selectedRows())
        // #1615: Fájl ▸ Importálás forrása… / Ctrl+M — UGYANAZ a példány,
        // amit az eszköztár „Import" gombja nyit (ld. `onImportRequested`)
        onImportSourceRequested: importSourceDialog.open()
        // #1633: Fájl ▸ Fájl felvétele a Picasába… / Ctrl+O
        onAddFileRequested: addFileDialog.open()
        // #1614: Fájl ▸ Áthelyezés új mappába… — a `moveToNewFolderDialog`
        // csak a NEVET kéri, a kijelölés útvonalait a hívás pillanatában
        // gyűjtjük (ugyanaz a minta, mint a `Move…`/`Törlés…` tételeknél).
        onMoveToNewFolderRequested:
            fileOpsDialogs.openMoveToNewFolder(window.selectedPaths())
        // #1472: Fájl ▸ Nyomtatás… / Ctrl+P — a nyomtatás-párbeszéd
        onPrintRequested: window.openPrint()
        // #1590: Mappa ▸ Bélyegképek nyomtatása… (Ctrl+Shift+P)
        onPrintContactSheetRequested: window.openContactSheetPrint()
        onLocateRequested: {
            var p = controller.photos.filePathAt(window.selectedIndex)
            if (p.length > 0) fileOpsController.revealPhoto(p)
        }
        onDeleteRequested: fileOpsDialogs.openDelete(window.selectedPaths())
        // #1608: a `Delete` NÉZETFÜGGŐ — albumban/Emberek-albumban nem
        // lemezről töröl, csak kiveszi onnan (a helyi menü már meglévő
        // útjaira vezet, ld. lentebb a PhotoContextMenu ugyanezen kezelőit)
        currentAlbumToken: controller ? controller.currentAlbumToken : ""
        currentPersonName: controller ? controller.currentPersonName : ""
        onRemoveFromAlbumRequested: {
            if (controller)
                controller.removeRowsFromAlbum(
                    window.selectedRows(), controller.currentAlbumToken)
        }
        onRemoveFromPeopleAlbumRequested: {
            if (controller) removePeopleFacesDialog.openFor(
                window.selectedRows(), controller.currentPersonName)
        }
        // #444: a nem-destruktív mentés három fokozata — a megerősítések és
        // a nem renderelhető láncelem figyelmeztetése a SaveDialogs-ban
        hasSavedBackup: controller
            ? controller.hasSavedBackup(window.selectedIndexes) : false
        onSaveRequested: saveDialogs.ensure().openSave(window.selectedIndexes)
        onRevertRequested: saveDialogs.ensure().openRevert(window.selectedIndexes)
        onUndoSaveRequested: saveDialogs.ensure().openUndoSave(window.selectedIndexes)
        // #1527: a mentés-család két új tagja
        onSaveAsRequested: saveDialogs.ensure().openSaveAs(window.selectedIndex)
        onSaveCopyRequested: saveDialogs.ensure().openSaveCopy(window.selectedIndexes)
        onSlideshowRequested: window.startSlideshow(-1)
        onTimelineRequested: window.toggleTimeline()
        tagsPanelOpen: window.tagsPanelOpen
        onTagsPanelRequested: window.valtsFiokLapot("tags")
        peoplePanelOpen: window.peoplePanelOpen
        onPeoplePanelRequested: window.valtsFiokLapot("people")
        placesPanelOpen: window.placesPanelOpen
        onPlacesPanelRequested: window.valtsFiokLapot("places")
        onHideToggleRequested: window.toggleHiddenSelection()
        propertiesPanelOpen: window.propertiesPanelOpen
        onPropertiesPanelRequested: window.valtsFiokLapot("properties")
        // #426: „Az összes effektus másolása/beillesztése" — a kijelölésre
        // hat, a rács sorindexein keresztül (window.selectedRows() a
        // meglévő mintát követi, ld. toggleHiddenSelection). A
        // `photo_ops_controller.PhotoOpsMixin`-t hívja, NEM a #152-es
        // `effects_controller`-t (az a crop64-et is átvinné).
        // #305: null-őr — ld. fenti Connections
        hasAllEffectsClipboard: controller ? controller.hasAllEffectsClipboard : false
        onCopyAllEffectsRequested: controller.copyAllEffects(window.selectedRows())
        onPasteAllEffectsRequested: controller.pasteAllEffects(window.selectedRows())
        // #1475: a két kötegelt visszavonás — a Szerkesztés menü élén álló
        // tételek. Kijelölés-független: a köteg a SAJÁT, művelet idején
        // rögzített képlistáját állítja vissza.
        canUndoPasteAllEffects: controller ? controller.canUndoPasteAllEffects : false
        canUndoBatchEdit: controller ? controller.canUndoBatchEdit : false
        onUndoPasteAllEffectsRequested: controller.undoPasteAllEffects()
        onUndoBatchEditRequested: controller.undoBatchEdit()
        // #425: Kép ▸ Csoportos szerkesztés — a `batch_effect_controller.
        // BatchEffectMixin`-t hívja, ugyanazon a rács-sorindex mintán
        // a forgatás a MEGLÉVŐ (szinkron, gyors) rotateRightMany/
        // rotateLeftMany úton fut, nem az applyEffectMany háttérszálán —
        // a `filters=`-t bővítő 7 effekttől eltérően nem igényel ini-
        // láncbővítést, csak a rotate= kulcs cseréjét (ld. PhotoOpsMixin).
        // A köteg visszavonása a Szerkesztés menü „Csoportos szerkesztés
        // visszavonása" tételén megy (#1475) — a forgatás NEM kerül a
        // kötegelt undo-verembe, mert a rotate= külön kulcs.
        onBatchApplyEffectRequested: (name) => {
            if (name === "rotate_cw") controller.rotateRightMany(window.selectedRows())
            else if (name === "rotate_ccw") controller.rotateLeftMany(window.selectedRows())
            else controller.applyEffectMany(window.selectedRows(), name)
        }
        // #465 3. pont: „Undo All Edits" — megerősítéssel, a kijelölt
        // kép(ek) TELJES szerkesztési lánca törlődik (`clearAllEffectsMany`,
        // ugyanaz a kötegelt undo-verem mint a `applyEffectMany`-nál).
        onUndoAllEditsRequested: undoAllEditsDialog.openFor(window.selectedRows())
    }

    // #465 3. pont: az általános ConfirmDialog mintáját követi (ld.
    // FileOpsDialogs.qml deleteConfirmDialog) — a döntés-kulcs
    // "undoAllEdits" a „Don't ask again" jelölő eltárolásához.
    ConfirmDialog {
        id: undoAllEditsDialog
        objectName: "undoAllEditsDialog"
        namePrefix: "undoAllEdits"
        title: qsTr("Undo All Edits")
        property var rows: []
        // #465: az eredeti Picasa KÉT külön szöveget használ egy, illetve
        // több képre (IDS_CONFIRMREVERT / IDS_CONFIRMREVERT_MULTIPLE) — a
        // többesszámúban a „MINDEGYIK" nagybetűs. Ha a kijelölésben van
        // vörösszem-javítás, az eredeti KÜLÖN is figyelmeztet rá
        // (IDS_CONFIRM_REDEYE_REVERT): az régió-adat, és a törléssel
        // véglegesen elvész.
        function openFor(rowList) {
            if (rowList.length === 0) return
            rows = rowList
            var text = rowList.length === 1
                ? qsTr("This will remove all edits you have made to the"
                       + " current picture.")
                : qsTr("This will remove all edits you have made to ALL of"
                       + " the selected pictures.")
            if (controller.selectionHasRedeye(rowList))
                text += "\n\n" + qsTr("Red eye fixes have been applied. If you"
                                      + " remove all edits, your red eye fixes"
                                      + " cannot be recovered.")
            ask("undoAllEdits", text)
        }
        onConfirmed: controller.clearAllEffectsMany(rows)
    }

    // #17: Elrejtés/Megjelenítés a kijelölésre; elrejtés után a kijelölést
    // ürítjük — az elrejtett sorok kiesnek a rácsból, az indexek eltolódnak
    function toggleHiddenSelection() {
        var rows = window.selectedRows()
        if (rows.length === 0) return
        controller.toggleHiddenRows(rows)
        window.clearSelection()
    }

    // #1798: a kijelölés elküldése levélben. A tárgyat és a szöveget
    // SZÁNDÉKOSAN nem kérjük be: az eredeti Picasa sem kérdez, a levelet a
    // levelezőprogram szerkeszti meg — mi csak a csatolmányokkal nyitjuk meg.
    function sendSelectionByEmail() {
        if (typeof emailController === "undefined" || !emailController)
            return
        var sorok = window.selectedRows()
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

    // #1798: a küldési út két visszajelzése. A `mailChoiceRequested` a
    // „minden küldéskor kérdezz" mód kérdése, az `emailFailed` a hibáé —
    // ez utóbbinak eddig SEHOL nem volt kezelője, tehát a hibaüzenet
    // („nincs levelezőprogram") némán elveszett.
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
        function onEmailFailed(uzenet) {
            // a #459-es közös hibasáv — a levelezős hibának eddig SEHOL
            // nem volt kezelője, tehát némán elveszett
            errorBanner.notice = false
            errorBannerText.text = uzenet
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

    // #1720: halasztott példányosítás — a párbeszéd csak az első
    // megnyitáskor épül fel (ld. `DeferredDialog.qml`).
    DeferredDialog {
        id: folderManager
        anchors.fill: parent
        sourceComponent: Component { FolderManagerDialog { } }
    }
    // Duplikátum-kezelő (#287): Eszközök → "Find Duplicates..."
    // #294: az appWindow-bekötés a „kijelölt képek" hatókörhöz kell — enélkül
    // a dialógus a mappa-hatókörre esne vissza (integrátori bekötés).
    DeferredDialog {
        id: dedupDialog
        anchors.fill: parent
        sourceComponent: Component { DedupDialog { appWindow: window } }
    }
    // #1473: az arckeresés belépési pontja. A vezérlőt az ablak-szintű
    // álnéven kapja (#1236) — az ablak maga NEM modális, a keresés alatt a
    // felhasználó tovább dolgozhat (#449).
    DeferredDialog {
        id: faceScanDialog
        anchors.fill: parent
        sourceComponent: Component {
            FaceScanDialog { faceScan: window._faceScanController }
        }
    }
    // #146: meglévő Picasa-telepítés átvétele — nyitása a Mappakezelő
    // gombjából (discoveryController.dialogRequested) vagy induláskori
    // automatikus felajánlásból (integrátori bekötés: picasaImportDialog.openAndDiscover())
    PicasaImportDialog { id: picasaImportDialog }
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

    // első indítás: nincs még figyelt mappa → Mappakezelő felajánlása
    // #449: első indítás — az eredeti EGYETLEN kérdést tett fel (teljes gép
    // vs. Dokumentumok/Képek/Asztal), és nem nyitott mappalistát. Eddig
    // nálunk üres könyvtárnál rögtön a Mappakezelő nyílt ki: az egy fát és
    // egy jóval nagyobb döntést tett a felhasználó elé az első percben.
    Component.onCompleted: {
        initialScanDialog.openIfNeeded()
        // #1051: ha az előző munkamenet piszkozatot hagyott, most kell
        // felajánlani — enélkül a lemezen ragad, ahogy a tulajdonosé is
        collageDraftDialog.openIfNeeded()
        // #922: a képtálca kezdőállapota (a Connections innentől frissíti)
        if (controller) window.trayHasPictures = controller.heldCount > 0
    }

    // Eszköztár: Importálás | (szűrők középen) | kereső jobbra
    header: MainToolbar {
        id: toolbar
        // #741/4: a nézőben (és így a szerkesztőben) NINCS alkalmazás-szintű
        // eszköztár. A binárisban a szerkesztő felső 40 képpontos sávjában
        // egyetlen elem van, az `editpanel/albumview` („Vissza a
        // könyvtárhoz", 122 × 22) — az nálunk már megvan a
        // `PhotoViewer.qml`-ben. Az Importálás+kereső sáv itt csak lefelé
        // tolta az egész panelt, és ezzel a mért geometria sem jöhetett ki.
        // A tulajdonosi döntés (`docs/decisions/szerkeszto-bal-panel.md`):
        // a felület PONTOSAN az eredetit kövesse.
        //
        // #1026: az eszközsáv a KÖNYVTÁR panelének gyereke (`thumbui.tre`:
        // `importbutton`/`sbutton`/`timelinebutton`/`globalmode`) — a
        // projekt-lapon a panellel EGYÜTT tűnik el, nem külön szabályból.
        visible: !window.viewerOpen && window.libraryFrameVisible
        onSearchEdited: function(text) {
            window.clearSelection()
            controller.search(text)
            suggestionsTimer.restart()
        }
        onSearchCleared: {
            window.clearSelection()
            controller.search("")
            searchSuggestionsBox.suggestions = []
        }
        // #23: az "Import" gomb az Import forrásból ablakot nyitja
        onImportRequested: importSourceDialog.open()
    }

    // Kereső-javaslatok (#7): gépelés után rövid szünettel (debounce)
    // kérjük le, hogy NAS-on se fusson lekérdezés minden billentyűre.
    // #1515: null-őr (#305 mintája). A 150 ms-os debounce miatt a hívás a
    // gépeléstől ELVÁLIK: ha közben az ablak lebomlik, a `controller`
    // kontextus-tulajdonság már null, és a hívás QML-szkripthibát dobna.
    // Ez a felület egyetlen olyan pontja, ahol IDŐZÍTŐ hívja a
    // controllert — a #1515 tesztje volt az első, amely a valódi
    // (searchEdited → suggestionsTimer) úton ment végig, és kibukott.
    function refreshSuggestions() {
        if (!controller)
            return
        searchSuggestionsBox.suggestions =
            controller.searchSuggestions(toolbar.searchText)
    }
    Timer {
        id: suggestionsTimer
        interval: 150
        onTriggered: window.refreshSuggestions()
    }
    SearchSuggestions {
        id: searchSuggestionsBox
        objectName: "searchSuggestions"
        z: 50
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.rightMargin: 8
        width: 300
        query: toolbar.searchText
        // #1026: a keresődoboz a könyvtár keretének része, tehát a buborék
        // sem úszhat rá a projekt-lapra (a beírt szöveg megmarad, ezért a
        // hosszra kötött feltétel önmagában igazat adna)
        visible: suggestions.length > 0 && toolbar.searchText.length > 0
                 && !window.viewerOpen && window.libraryFrameVisible
        onChosen: function(kind, name, param) {
            if (kind === "folder") {
                toolbar.clearSearch()
                window.clearSelection()
                controller.selectFolder(param)
            }
            suggestions = []
        }
    }

    // #8: diavetítés-réteg — minden más felett, csak vetítés alatt látszik
    SlideshowView {
        id: slideshow
        objectName: "slideshowView"
        anchors.fill: parent
        z: 100
        // #305: null-őr
        photosModel: controller ? controller.photos : null
        onClosed: window.exitSlideshow()
        onStarToggled: function(index) { controller.toggleStar(index) }
        onRotateRequested: function(index, delta) {
            if (delta > 0) controller.rotateRight(index)
            else controller.rotateLeft(index)
        }
    }

    PhotoViewer {
        id: photoViewer
        objectName: "photoViewer"
        anchors.fill: parent
        visible: window.viewerOpen
        // #305: null-őr
        photosModel: controller ? controller.photos : null
        // #422: a mentés-parancsok a nézőből — ugyanazok a megerősítések,
        // mint a rácsból (egy parancs, egy út)
        onSaveRequested: function(row) { saveDialogs.ensure().openSave([row]) }
        onRevertRequested: function(row) { saveDialogs.ensure().openRevert([row]) }
        onUndoAllEditsRequested: function(row) {
            if (typeof batchEffectController !== "undefined"
                    && batchEffectController)
                batchEffectController.clearAllEffectsMany([row])
        }
        onResetFacesRequested: resetFacesConfirm.open()
        onPlayRequested: window.startSlideshow(currentIndex)
        // #1002: a néző csak JELEZ — a panel feltöltése és a lapváltás
        // a gazdáé, ugyanúgy, ahogy a `CollagePanel` jelzéseinél.
        onEditCollageRequested: function(path) {
            window.openSavedCollage(path)
        }
        onClosed: {
            window.viewerOpen = false
            window.selectedIndex = currentIndex   // a rács kövesse a nézőt
            window.selectedIndexes = [currentIndex]
            // a szerkesztések (filters=) azonnal látsszanak a rácson —
            // NAS-on a fájlfigyelő nem szól, nem várhatunk a rescanre (#59);
            // a feedben (#64) a néző át is léphetett másik mappába, ezért a
            // nézett kép mappáját frissítjük
            // #173: a megnyitás előtti feed-pozíciót megőrizzük — a resync
            // modellcseréje után NE a mappa elejére ugorjunk. A rögzítés a
            // resync ELŐTT történik (a savedY még a megnyitáskori), az
            // alkalmazás pedig a modellcsere UTÁN (Qt.callLater), illetve az
            // onFeedChanged ágon.
            grid.beginRevealAfterViewer()
            controller.resyncFolderOfRow(currentIndex)
            Qt.callLater(grid.applyRevealAfterViewer)
        }
        onCurrentIndexChanged: if (visible) window.selectedIndex = currentIndex
        // #422: a néző kontextusmenüjének „Törlés lemezről" tétele — a
        // megerősítő dialógus itt él (a menü maga a PhotoViewer-ben)
        onDeleteRequested: function(path) { fileOpsDialogs.openDelete([path]) }
    }

    // #24: Időrend nézet (Ctrl+5) — a teljes könyvtár korszak-áttekintése;
    // egy bélyegképre kattintva a fő rácsban jelenítjük meg a képet
    // (mappaváltás a bekötő selectFolder-jén át, majd a néző az
    // odakerült sor alapján — rowOfId, a keresési-találat minta szerint).
    TimelineView {
        id: timelineView
        objectName: "timelineView"
        anchors.fill: parent
        visible: window.timelineOpen
        // #305: null-őr — a timelineController is null lehet átmenetileg
        // a QML-engine leépítésekor
        periodsModel: timelineController ? timelineController.periods : []
        onClosed: window.timelineOpen = false
        onPhotoChosen: function(photoId, folderPath) {
            window.timelineOpen = false
            controller.selectFolder(folderPath)
            var row = controller.photos.rowOfId(photoId)
            if (row >= 0) {
                window.viewerOpen = true
                photoViewer.show(row)
            }
        }
    }

    // #985: a dokumentum-fülsáv (#944) a tartalomterület TETEJÉN, az
    // eszköztár alatt. Nyitott projekt-lap nélkül a magassága 0, tehát a mai
    // elrendezés egyetlen képponttal sem csúszik el — ezt a
    // `test_collage_panel_wiring_985.py` külön állítja.
    DocumentTabStrip {
        id: documentTabStrip
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        projectTabs: window.openProjectTabs

        // A néző és az Időrend a TELJES ablakot fedi; ilyenkor a sáv se ne
        // látsszon, se ne foglaljon helyet (a komponens `height`-kötését
        // ezért írjuk felül, nem csak a `visible`-t).
        visible: documentTabStrip.hasProjectTabs
                 && !window.viewerOpen && !window.timelineOpen
        height: documentTabStrip.visible ? documentTabStrip.savMagassag : 0

        onCloseAccepted: function(tabId, saveDraft) {
            if (!controller || tabId !== window.collageTabId) return
            // A háromgombos kérdés már eldőlt (#944); itt csak a
            // következményt hajtjuk végre — a piszkozat a Kollázsok albumba
            // megy (#949), majd a lap bezárul.
            if (saveDraft) controller.saveCollageDraft()
            controller.closeCollage()
        }
    }

    SplitView {
        id: mainSplit
        objectName: "mainSplit"
        // #985: a `anchors.fill: parent` négy horgonyra bomlik, hogy a
        // tartalom a fülsáv ALATT kezdődjön. Üres sávnál a sáv magassága 0,
        // tehát `documentTabStrip.bottom === parent.top` — a mai elrendezés
        // képpontra ugyanaz marad.
        anchors.top: documentTabStrip.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        // A Könyvtár lapjának tartalma. NEM `Loader.active`: a lap váltásakor
        // a feed nem semmisülhet meg, különben elveszne a görgetési helye és
        // a kijelölése (a #944 kimérte, a #985 tesztje állítja).
        // #1026: a KERET közös kapcsolójára kötve (a `libraryFrameVisible`
        // a `documentTabStrip.libraryActive`-ot hordozza) — így a könyvtár
        // tartalma, az eszközsáv és az alsó sáv EGYSZERRE megy.
        visible: !window.viewerOpen && !window.timelineOpen
                 && window.libraryFrameVisible
        orientation: Qt.Horizontal

        // #322: látható, fogható elválasztó. A Fusion alap-fogantyúja olyan
        // halvány, hogy a felhasználó meg sem találta — ez a delegate a
        // Picasa vékony sávját adja, hover/húzás közben kiemelkedve, és a
        // kurzort is átváltja, hogy a húzhatóság magától látsszon.
        handle: Rectangle {
            objectName: "folderPaneHandle"
            implicitWidth: 6
            implicitHeight: 6
            color: SplitHandle.pressed
                   ? Qt.darker(Theme.chromeBorder, 1.35)
                   : (SplitHandle.hovered
                      ? Qt.darker(Theme.chromeBorder, 1.15)
                      : Theme.chromeBorder)

            Behavior on color {
                ColorAnimation { duration: 100 }
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton  // csak a kurzorért
                cursorShape: Qt.SplitHCursor
            }
        }

        FolderPane {
            id: folderPane
            objectName: "folderPane"
            // #305: null-őr — a controller a leépítéskor átmenetileg null
            SplitView.preferredWidth: controller ? controller.folderPaneWidth : 240
            SplitView.minimumWidth: 160
            SplitView.maximumWidth: 600

            // A húzott szélesség mentése — késleltetve, hogy a húzás közbeni
            // pixelenkénti változás ne írja folyamatosan a QSettings-t.
            onWidthChanged: folderPaneWidthSaver.restart()

            Timer {
                id: folderPaneWidthSaver
                interval: 400
                onTriggered: {
                    if (controller && folderPane.width > 0) {
                        controller.setFolderPaneWidth(Math.round(folderPane.width))
                    }
                }
            }
            // #305: null-őr — a controller a QML-engine leépítésekor
            // átmenetileg null lehet, amikor ezek a kötések utoljára
            // kiértékelődnek
            foldersModel: controller ? controller.folders : null
            // #702: a bal hasáb hierarchikus (fa) mappanézete. A `typeof`-őr
            // NEM elhagyható: a hasábot vezérlő nélkül betöltő próbáknál egy
            // őrizetlen hivatkozás QML-szkripthibát dobna.
            // #1454: a nézetmódot (Egyszerű / Fa) is ez a vezérlő tartja — a
            // `FolderPane.treeViewMode` alapértelmezésben rá kötődik, ezért
            // itt NEM szabad felülírni (korábban `false` volt beégetve, és a
            // menü bekötése után is a lapos listán ragadt volna a hasáb).
            hierarchyController: (typeof folderHierarchyController !== "undefined")
                                 ? folderHierarchyController : null
            selectedPath: controller ? controller.currentFolder : ""
            starredActive: controller ? controller.filterActive : false
            searchActive: controller ? controller.searchActive : false
            searchQuery: controller ? controller.searchQuery : ""
            searchResultCount: controller ? controller.searchResultCount : 0
            albumsModel: controller ? controller.albums : []
            selectedAlbumToken: controller ? controller.currentAlbumToken : ""
            // #26 (3. lépcső): az Emberek gyűjtemény + a „Névtelenek" sor
            peopleModel: controller ? controller.people : []
            selectedPersonName: controller ? controller.currentPersonName : ""
            unnamedFaceCount: (typeof faceScanController !== "undefined" && faceScanController)
                               ? faceScanController.unnamedCount : 0
            unnamedFacesActive: window.unnamedFacesOpen
                                && window.facesAlbumMode === "unnamed"
            // #449: a háttér-beolvasás haladása az albumlistában
            faceScanPercent: (typeof faceScanController !== "undefined" && faceScanController)
                              ? faceScanController.scanPercent : -1
            onFolderChosen: function(path) {
                window.clearSelection()
                window.unnamedFacesOpen = false
                if (toolbar.searchText.trim().length > 0) {
                    // #45: aktív keresésnél a szűrés megmarad, a
                    // találatok a mappára szűkülnek (Picasa-viselkedés)
                    controller.selectFolderKeepSearch(path)
                } else {
                    toolbar.clearSearch()
                    controller.selectFolder(path)
                }
            }
            onStarredChosen: {
                toolbar.clearSearch()
                window.clearSelection()
                window.unnamedFacesOpen = false
                controller.showStarred()
            }
            onAlbumChosen: function(token) {
                if (!controller) return
                toolbar.clearSearch()
                window.clearSelection()
                window.unnamedFacesOpen = false
                controller.showAlbum(token)
            }
            onPersonChosen: function(name) {
                if (!controller) return
                toolbar.clearSearch()
                window.clearSelection()
                window.unnamedFacesOpen = false
                controller.showPerson(name)
            }
            onUnnamedFacesChosen: {
                toolbar.clearSearch()
                window.clearSelection()
                window.facesAlbumMode = "unnamed"
                window.unnamedFacesOpen = true
            }
            // #26: a „Mellőzött emberek" album — ugyanaz a nézet, más
            // tartalommal és művelettel (a mellőzés visszavonása)
            onIgnoredFacesChosen: {
                toolbar.clearSearch()
                window.clearSelection()
                window.facesAlbumMode = "ignored"
                window.unnamedFacesOpen = true
            }
            // #457: „Exportált képek" — a Projektek gyűjtemény alatt
            exportedFolders: controller ? controller.exportedFolders : []
            // #1029: a Projektek gyűjtemény mappái (P2category)
            projectFolders: controller ? controller.projectFolders : []
            ignoredFaceCount: (typeof faceScanController !== "undefined" && faceScanController)
                               ? (controller ? controller.photos.revision : 0,
                                  faceScanController.ignoredCount())
                               : 0
            ignoredFacesActive: window.unnamedFacesOpen
                                && window.facesAlbumMode === "ignored"
            // #455: fogd-és-vidd — a húzott KIJELÖLÉS kerül albumba. Az új
            // album ugyanazt a névkérő párbeszédet kapja, mint a menüből
            // indított (Fájl → Új album), hogy ne legyen két, kicsit
            // másképp viselkedő út ugyanarra.
            onNewAlbumDropped: fileOpsDialogs.openNewAlbum(window.selectedIndexes)
            onPhotosDroppedOnAlbum: function(token) {
                if (controller && window.selectedIndexes.length > 0)
                    controller.addRowsToAlbum(window.selectedIndexes, token)
            }
        }

        Rectangle {
            color: Theme.lightboxBg
            SplitView.fillWidth: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // zöld eredménysáv aktív szűrőnél (Picasa-minta)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 26
                    // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
                    // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
                    visible: (controller && controller.filterActive !== undefined)
                        ? controller.filterActive : false
                    color: "#5aa865"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        spacing: 10
                        Rectangle {
                            Layout.preferredHeight: 18
                            Layout.preferredWidth: viewAllText.width + 20
                            radius: 9
                            color: "#ffffff"
                            Text {
                                id: viewAllText
                                anchors.centerIn: parent
                                text: qsTr("View All")
                                font.pixelSize: Theme.fontSize - 1
                                font.bold: true
                                color: "#3b8f00"
                            }
                            TapHandler { onTapped: controller.clearFilter() }
                        }
                        Text {
                            // #305: null-őr
                            text: controller ? controller.filterStatusText : ""
                            color: "white"
                            font.pixelSize: Theme.fontSize
                            font.bold: true
                        }
                        Item { Layout.fillWidth: true }
                    }
                }

                // indexkép-csoport: fehér kártya a vásznon (kézikönyv 08)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: 12
                    color: Theme.contentPanel
                    border.color: Theme.chromeBorder

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 4

                        // Könyvtár-feed (#64) — a komponens a PicasaPy
                        // modulban él (LightboxFeed.qml, #150)
                        LightboxFeed {
                            id: grid
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            // kereséskor a #7-es csoportosított nézet fut,
                            // a „Névtelenek" nézetnél (#26) az UnnamedFacesView
                            // #305: null-őr
                            visible: controller
                                ? (!controller.searchActive && !window.unnamedFacesOpen)
                                : true
                            appWindow: window
                            onOpenRequested: function(row) {
                                window.viewerOpen = true
                                photoViewer.show(row)
                            }
                            onSlideshowRequested: function(startRow) {
                                window.startSlideshow(startRow)
                            }
                        }

                        // #7: keresési találatok mappánként csoportosítva
                        // (Picasa-minta) — a GridView nem támogat szekció-
                        // fejlécet, ezért csoportonként egy fejléc + egy
                        // nem-interaktív al-rács.
                        ListView {
                            id: groupedResults
                            objectName: "groupedSearchResults"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            // #305/#1572: null-őr
                            visible: (controller && controller.searchActive !== undefined)
                                ? (controller.searchActive && !window.unnamedFacesOpen) : false
                            model: controller ? controller.searchGroups : []
                            spacing: 0

                            delegate: ColumnLayout {
                                id: groupDelegate
                                required property var modelData
                                width: groupedResults.width
                                spacing: 0

                                SearchGroupHeader {
                                    Layout.fillWidth: true
                                    section: groupDelegate.modelData.folderName
                                }

                                GridView {
                                    id: subgrid
                                    Layout.fillWidth: true
                                    interactive: false
                                    // #85: itt is kiegyenlített sor — az
                                    // oszlopszám névleges méretből, a tényleges
                                    // cellaWidth a szélességet tölti ki.
                                    readonly property int nominalCellWidth:
                                        window.thumbSize + 18
                                    readonly property int columns: Math.max(
                                        1, Math.floor(width / nominalCellWidth))
                                    cellWidth: columns > 0
                                        ? Math.floor(width / columns)
                                        : nominalCellWidth
                                    // #305: null-őr
                                    cellHeight: window.thumbSize + 18
                                        + ((controller ? controller.thumbCaptionMode : "none") !== "none"
                                           ? 16 : 0)
                                    height: Math.ceil(
                                        groupDelegate.modelData.photos.length
                                        / columns) * cellHeight
                                    model: groupDelegate.modelData.photos

                                    delegate: ThumbDelegate {
                                        id: groupedThumb
                                        required property var modelData
                                        width: subgrid.cellWidth
                                        height: subgrid.cellHeight
                                        // #85/#83: a kép a névleges méretre
                                        // plafonozott
                                        maxContentWidth: subgrid.nominalCellWidth
                                        maxContentHeight: subgrid.cellHeight
                                        name: modelData.name
                                        thumbUrl: modelData.thumbUrl
                                        star: modelData.star
                                        caption: modelData.caption
                                        isVideo: modelData.isVideo
                                        hasEdits: modelData.hasEdits
                                        hasGeo: modelData.hasGeo === true
                                        // #463: arc-jelvények
                                        hasFaces: modelData.hasFaces === true
                                        hasFaceSuggestion:
                                            modelData.hasFaceSuggestion === true
                                        // #455: a tálcán tartott kép
                                        // jelvénye — a `heldCount` a
                                        // reaktív trigger (a `photos.
                                        // revision` mintája, ld. TrayBar).
                                        held: controller
                                              ? (controller.heldCount,
                                                 controller.isHeldAt(modelData.row))
                                              : false
                                        isHidden: modelData.hidden === true
                                        index: modelData.row
                                        keywords: modelData.keywords
                                        resolution: modelData.resolution
                                        // #305: null-őr
                                        captionMode: controller ? controller.thumbCaptionMode : "none"
                                        // #142: set-alapú lookup
                                        selected: window.selectedSet[
                                            modelData.row] === true
                                        onChosen: function(i, mods) {
                                            window.handleThumbClick(i, mods)
                                        }
                                        onOpened: function(i) {
                                            window.viewerOpen = true
                                            photoViewer.show(i)
                                        }
                                        onContextMenuRequested: function(i, cx, cy) {
                                            window.openPhotoContextMenu(
                                                i, groupedThumb, cx, cy)
                                        }
                                    }
                                }
                            }
                            ScrollBar.vertical: PicasaScrollBar {}
                        }

                        // #26 (3. lépcső): a „Névtelenek" album — a bal
                        // hasáb új sorára kattintva jelenik meg, a fő rács
                        // helyén (ld. UnnamedFacesView.qml docstring)
                        UnnamedFacesView {
                            id: unnamedFacesView
                            objectName: "unnamedFacesView"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: window.unnamedFacesOpen
                            mode: window.facesAlbumMode
                            faceScanController: window._faceScanController
                        }
                    }
                }
            }
        }

        // Címkék-panel (#12): jobb oldali hasáb, Ctrl+T / Nézet → Címkék
        TagsPanel {
            objectName: "tagsPanel"
            visible: window.tagsPanelOpen
            SplitView.preferredWidth: 190
            SplitView.minimumWidth: 150
            hasSelection: window.selectedRows().length > 0
            // a photos.revision-nel együtt kötve: címke-írás után frissül
            // #305: null-őr
            tags: controller
                ? (controller.photos.revision,
                   controller.keywordsOfRows(window.selectedRows()))
                : []
            onAddRequested: function(keyword) {
                controller.addKeywordToRows(window.selectedRows(), keyword)
            }
            onRemoveRequested: function(keyword) {
                controller.removeKeywordFromRows(window.selectedRows(), keyword)
            }
            onCloseRequested: window.ureseidAFiokot()
            // #422: a címke jobbklikk-menüje (Picasa `Tags` menüosztály)
            onAddToSelectionRequested: function(keyword) {
                if (controller)
                    controller.addKeywordToRows(window.selectedRows(), keyword)
            }
            onFindTaggedRequested: function(keyword) {
                if (controller) controller.search(keyword)
            }
        }

        // Helyek-panel (#30): jobb oldali hasáb, Nézet → Helyek — a látszó
        // képek helyei térképen, és a kijelölés geocímkézése
        PlacesPanel {
            objectName: "placesPanel"
            visible: window.placesPanelOpen
            SplitView.preferredWidth: 320
            SplitView.minimumWidth: 220
            appWindow: window
            onCloseRequested: window.ureseidAFiokot()
            onPhotoActivated: function(row) {
                window.selectedIndexes = [row]
                window.selectedIndex = row
            }
        }

        // Tulajdonságok-panel (#13): jobb oldali hasáb, Alt+Enter /
        // Nézet → Tulajdonságok — csak olvasás
        PropertiesPanel {
            objectName: "propertiesPanel"
            visible: window.propertiesPanelOpen
            SplitView.preferredWidth: 210
            SplitView.minimumWidth: 160
            hasSelection: window.selectedIndex >= 0
            // a photos.revision-nel együtt kötve: modell-frissüléskor újraolvas
            // #305: null-őr
            entries: controller
                ? (controller.photos.revision,
                   controller.propertiesOf(window.selectedIndex))
                : []
            onCloseRequested: window.ureseidAFiokot()
        }

        // Emberek-panel (#26): a jobb fiók negyedik panelje. Két szakasza
        // az eredeti szövegforrásából jön — „In this photo:" (a kijelölt
        // képek nevesített emberei) és „Also in these photos:" (akik a
        // nézett SZEMÉLLYEL együtt szerepelnek).
        PeoplePanel {
            objectName: "peoplePanel"
            visible: window.peoplePanelOpen
            SplitView.preferredWidth: 200
            SplitView.minimumWidth: 160
            selectionCount: window.selectedRows().length
            currentPerson: controller ? controller.currentPersonName : ""
            // a photos.revision-nel együtt kötve: arc-írás után frissül
            peopleHere: controller
                ? (controller.photos.revision,
                   controller.peopleOfRows(window.selectedRows()))
                : []
            peopleWith: controller && controller.currentPersonName.length > 0
                ? (controller.photos.revision,
                   controller.peopleWith(controller.currentPersonName))
                : []
            onPersonChosen: function(name) {
                if (!controller) return
                window.clearSelection()
                window.unnamedFacesOpen = false
                controller.showPerson(name)
            }
            onCloseRequested: window.ureseidAFiokot()
        }
    }

    // #985: a Kollázs LAP tartalma — a Könyvtár lapjának TESTVÉRE, ugyanazon
    // a helyen. Az eredetiben a `panelroot/collagetab` a `panelroot/picasatab`
    // testvére, tehát a kollázs a mappapanellel EGYÜTT váltja le a könyvtárat
    // (`picasa-kollazs-felulet.md` 8.: a „Továbbiak..." visszavált a
    // `picasatab`-ra). A panel a saját bal hasábját hozza magával.
    CollagePanel {
        id: collagePanel
        anchors.top: documentTabStrip.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        visible: !window.viewerOpen && !window.timelineOpen
                 && documentTabStrip.activeTabId === window.collageTabId
        // az álnév a kötési hurkot kerüli ki (ld. `appController`)
        controller: window.appController
        librarySelection: window.selectedIndexes

        // #1028: a mentés VÉGE — a panel jelez, a navigáció a gazdáé
        onCollageSaved: function(path) { window.locateSavedCollage(path) }

        // spec 4.3/13.: a panel csak JELEZ, a fülváltás a gazdáé
        onGetMoreClipsRequested: {
            window.backToCollagePrompted = true
            documentTabStrip.activateTab(documentTabStrip.libraryTabId)
        }
    }

    // #1001: a „Megjelenítés és szerkesztés" FOGADÓJA. A parancs három
    // helyről indul (a `CollageRandomRow` gombja, a `CollageNode`
    // duplakattintása és a `CollageContextMenus` tétele), de mind a három a
    // vezérlő `viewAndEditSelection()`-jébe fut, tehát EGY fogadó elég — és
    // egy is kell, mert a lapváltás meg a néző a gazdáé, nem a panelé.
    Connections {
        target: controller
        function onCollageEditRequested(path) {
            window.openCollageNodeInEditor(path)
        }
    }

    // A „Vissza a kollázshoz" gomb (`collagepanel::back_to_collage`): a
    // „Továbbiak..." után a KÖNYVTÁR lapján jelenik meg, a kollázs lapja
    // közben nyitva marad (`picasa-kollazs-felulet.md` 8.).
    PicasaButton {
        objectName: "backToCollageButton"
        z: 80
        visible: window.backToCollagePrompted
                 && documentTabStrip.hasProjectTabs
                 && documentTabStrip.libraryActive
                 && !window.viewerOpen && !window.timelineOpen
        text: qsTr("Back to Collage")
        accent: Theme.picasaGreen
        anchors.top: documentTabStrip.bottom
        anchors.topMargin: 8
        anchors.right: parent.right
        anchors.rightMargin: 24
        onClicked: {
            window.backToCollagePrompted = false
            documentTabStrip.activateTab(window.collageTabId)
        }
    }

    // #209: lebegő „Importálás" folyamat-panel — jobb oldalt lebeg, húzható;
    // a néző felett is látszik (a szkennelés közben is lehet dolgozni),
    // csak a diavetítés (z:100) takarja
    ImportProgressPanel {
        id: importPanel
        objectName: "importProgressPanel"
        z: 90
        // #305/#1572: null-őr
        visible: (controller && controller.importPanelVisible !== undefined)
            ? controller.importPanelVisible : false
        folderName: controller ? controller.importFolderName : ""
        doneCount: controller ? controller.importDoneCount : 0
        totalCount: controller ? controller.importTotalCount : 0
        newCount: controller ? controller.importNewCount : 0
        onCloseRequested: controller.dismissImportPanel()
        // induló hely: jobb felül, a kereső alatt; húzáskor a DragHandler
        // felülírja a kötést — a panel ott marad, ahova a felhasználó tette
        x: parent.width - width - 24
        y: 56
    }

    // #425: lebegő „Csoportos szerkesztés" folyamat-panel — az
    // ImportProgressPanel mintájára, Mégse gombbal (megszakítható köteg)
    BatchEditProgressPanel {
        id: batchEditPanel
        objectName: "batchEditProgressPanel"
        z: 90
        visible: (controller && controller.batchEditActive !== undefined)
            ? controller.batchEditActive : false
        folderName: controller ? controller.batchEditFolderName : ""
        doneCount: controller ? controller.batchEditDoneCount : 0
        totalCount: controller ? controller.batchEditTotalCount : 0
        onCancelRequested: controller.cancelBatchEdit()
        x: parent.width - width - 24
        y: 56 + importPanel.height + 12
    }

    // #1527: a mentés folyamatjelzője. A mentés eddig is háttérszálon
    // ment, de NÉMÁN — sok képnél a felhasználó nem tudta, dolgozik-e a
    // program. A szöveg az eredeti két hivatalos alakja (egy fájl /
    // több fájl), a százalék egy tizedesjegyre.
    SaveProgressPanel {
        id: saveProgressPanel
        objectName: "saveProgressPanel"
        z: 90
        visible: (controller && controller.saveProgressActive !== undefined)
            ? controller.saveProgressActive : false
        fileCount: controller ? controller.saveProgressFileCount : 0
        percent: controller ? controller.saveProgressPercent : 0
        x: parent.width - width - 24
        y: 56 + importPanel.height + batchEditPanel.height + 24
    }

    // #211: lebegő „Teljesítmény-monitor" panel — a Súgó menüből
    // kapcsolható; balra az importálás-paneltől, hogy ne fedjék egymást
    PerfMonitorPanel {
        id: perfPanel
        objectName: "perfMonitorPanel"
        z: 90
        // #305/#1572: null-őr
        visible: (controller && controller.perfMonitorEnabled !== undefined)
            ? controller.perfMonitorEnabled : false
        cpuPercent: controller ? controller.perfCpuPercent : 0
        rssMb: controller ? controller.perfRssMb : 0
        topActivity: controller ? controller.perfTopActivity : ""
        onCloseRequested: controller.setPerfMonitorEnabled(false)
        onSaveRequested: perfPanel.lastSavedPath = controller.saveDiagnostics()
        x: 24
        y: 56
    }

    // #237: kép/mappa ablakra ejtése → a kép mappája figyelt gyökér lesz
    // (ImportDropArea → dropImportController). Egér-eseményt nem fog el;
    // z:95 — a lebegő panelek (90) fölött, a diavetítés (100) alatt, hogy
    // a visszajelzés-buborék látsszon
    ImportDropArea {
        objectName: "importDropArea"
        anchors.fill: parent
        z: 95
    }

    // #459: globális, látható hibasáv. AUDIT-lelet: a `syncFailed`
    // (photoOpFailed IDE fut be, ld. photo_ops_controller.py
    // `_on_photo_write_failed`), `albumWriteFailed`, `geoWriteFailed` és
    // `faceWriteFailed` jelzések korábban SEHOVA nem voltak bekötve a
    // QML-oldalon — a felhasználó néma bukást látott, a hiba csak a
    // naplóba (`_log.exception`/hallgatólagos emit) került. Ez az
    // egyetlen, közös felület mind a négy csatornának.
    Rectangle {
        id: errorBanner
        objectName: "errorBanner"
        z: 1000
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 8
        radius: 4
        // #459/5: az „offline mappa" NEM hiba, hanem tájékoztatás — ugyanaz
        // a sáv, de borostyán tónussal, hogy ne keveredjen az írás- és
        // szinkron-hibákkal.
        property bool notice: false
        // #1500: épp a színkeresés feltöltéséről szól-e a sáv (csak ekkor
        // frissítik a haladásjelzések a szövegét)
        property bool colorNoticeActive: false
        color: errorBanner.notice ? "#b7791f" : "#c0392b"
        visible: errorBannerText.text.length > 0
        implicitWidth: errorBannerRow.implicitWidth + 16
        implicitHeight: errorBannerRow.implicitHeight + 12

        RowLayout {
            id: errorBannerRow
            anchors.centerIn: parent
            spacing: 12
            Text {
                id: errorBannerText
                objectName: "errorBannerText"
                text: ""
                color: "white"
                font.pixelSize: Theme.fontSize
                wrapMode: Text.WordWrap
                Layout.maximumWidth: 480
            }
            // #1500/#1476: a színkeresés előkészítése akár egy órányi
            // processzoridő — MUSZÁJ tudni leállítani. A gomb csak a
            // színkeresés tájékoztatóján jelenik meg; a többi üzenetnek
            // nincs mit leállítania.
            PicasaButton {
                objectName: "errorBannerStopButton"
                visible: errorBanner.colorNoticeActive
                text: qsTr("Stop")
                onClicked: {
                    controller.cancelColorIndex()
                    errorBanner.colorNoticeActive = false
                    errorBannerText.text = ""
                }
            }
            PicasaButton {
                objectName: "errorBannerCloseButton"
                text: qsTr("Close")
                onClicked: errorBannerText.text = ""
            }
        }

        Timer {
            interval: 8000
            running: errorBannerText.text.length > 0
            onTriggered: errorBannerText.text = ""
        }
    }

    Connections {
        target: controller
        function onSyncFailed(message) {
            errorBanner.notice = false
            errorBannerText.text = message
        }
        function onAlbumWriteFailed(message) {
            errorBanner.notice = false
            errorBannerText.text = message
        }
        function onGeoWriteFailed(message) {
            errorBanner.notice = false
            errorBannerText.text = message
        }
        // #1500: a színkeresés (`color:`/`szín:`) gyorsítótára még hiányos.
        // TÁJÉKOZTATÁS (borostyán), nem hiba: az üres találati lista
        // ilyenkor nem azt jelenti, hogy nincs ilyen színű kép, hanem hogy
        // még nem számoltuk ki. A szöveget a vezérlő adja (számok vannak
        // benne), a sáv csak megjeleníti.
        function onColorIndexIncomplete(done, total) {
            errorBanner.notice = true
            errorBanner.colorNoticeActive = true
            errorBannerText.text = controller.colorIndexNoticeText(done, total)
        }
        // A sáv számai ÉLŐBEN követik a háttérmunkát, amíg látszik. A
        // `text.length > 0` őr azért kell, mert a sávot a saját időzítője
        // (és a Bezárás gomb) kiüríti — egy későbbi haladásjelzés nem
        // támaszthatja fel a felhasználó által eltüntetett üzenetet.
        function onColorIndexProgress(done, total) {
            if (errorBanner.colorNoticeActive && errorBannerText.text.length > 0)
                errorBannerText.text = controller.colorIndexNoticeText(done, total)
        }
        function onColorIndexFinished(done, total) {
            errorBanner.colorNoticeActive = false
        }
        // #459/5: nem elérhető mappa — tájékoztató üzenet néma bukás helyett
        // #1654: a tesztüzem visszajelzései. TÁJÉKOZTATÁS (borostyán),
        // nem hiba: a bekapcsolás („a naplózás a következő indításnál
        // kezdődik"), a napló átadása és a mentés eredménye jár erre.
        function onTesztuzemUzenet(uzenet) {
            errorBanner.notice = true
            errorBannerText.text = uzenet
        }
        // A közös mappa nem érhető el — a felhasználó nem maradhat üres
        // kézzel: az üzenet mellé azonnal nyílik a „Mentés másként…".
        function onTesztuzemMentesMaskentKert(uzenet) {
            errorBanner.notice = true
            errorBannerText.text = uzenet
            tesztuzemNaploDialog.open()
        }
        function onFolderUnavailable(path) {
            errorBanner.notice = true
            errorBannerText.text = qsTr("This folder is currently unavailable (for example a disconnected drive or network share). Its photos stay in the database and thumbnails come from the cache, but the original files cannot be opened or edited right now.")
        }
        function onBrokenPhotosDetected(items) {
            var ids = brokenPhotoDialog.pendingIds.slice()
            for (var i = 0; i < items.length; i++) ids.push(items[i].id)
            brokenPhotoDialog.pendingIds = ids
            // #459: rövid összegyűjtés — több törött kép is felbukkanhat
            // egymás után görgetés közben, ezeket EGY dialógusba fűzzük
            // ("this file(s)"), nem fotónként külön felugró ablakot.
            brokenPhotoBatchTimer.restart()
        }
    }
    Connections {
        target: typeof facesHelper !== "undefined" ? facesHelper : null
        function onFaceWriteFailed(message) {
            errorBanner.notice = false
            errorBannerText.text = message
        }
    }

    // #459: sérült/betölthetetlen kép — ELREJTÉS felajánlása (nem törlés),
    // a felhasználó döntésével. A "Hide Files" a MEGLÉVŐ elrejtés-úton fut
    // (`controller.hidePhotosByIds` → `_apply_batch`, a `toggleHiddenRows`
    // mintája, `photo_ops_controller.py`) — itt NEM íródott újra.
    ConfirmDialog {
        id: brokenPhotoDialog
        namePrefix: "brokenPhoto"
        yesText: qsTr("Hide Files")
        noText: qsTr("Don't Hide")
        property var pendingIds: []
        onConfirmed: {
            controller.hidePhotosByIds(brokenPhotoDialog.pendingIds)
            brokenPhotoDialog.pendingIds = []
        }
        onDenied: brokenPhotoDialog.pendingIds = []
    }

    Timer {
        id: brokenPhotoBatchTimer
        interval: 400
        onTriggered: {
            if (brokenPhotoDialog.pendingIds.length > 0) {
                brokenPhotoDialog.ask("", qsTr(
                    "Picasa had a problem loading this file(s). Would you "
                    + "like to hide the files on disk?"))
            }
        }
    }

    // alsó sáv: infó-sáv + kijelölés-tálca (TrayBar.qml, #150)
    footer: TrayBar {
        id: trayBar
        objectName: "trayBar"
        width: parent ? parent.width : 0
        // #1026: az alsó tálca- és kimeneti sáv a KÖNYVTÁR panelének
        // gyereke (`thumbui/bottombevel_base` + `outputlayout.tre`), tehát a
        // projekt-lapon a panellel együtt tűnik el — a felszabaduló sávot a
        // vászon kapja meg.
        visible: window.libraryFrameVisible
        appWindow: window
        viewerIndex: photoViewer.currentIndex
        onExportRequested: exportDialogs.ensure().openForSelection()
        // #1472: a tálca „Nyomtatás" gombja — a jelzésnek eddig SEHOL nem
        // volt kezelője, a gomb kattintható volt, és nem történt semmi
        onPrintRequested: window.openPrint()
        // #361: kollázs/film a tálca ikonjairól is; #985: a kollázs innen is
        // a LAPOT nyitja (spec 3.2) — egy belépési út, nem kettő
        onCollageRequested: window.openCollageTab()
        onMovieRequested: createDialogs.openMovie()
        // #1798: a tálca „E-Mail" gombja engedélyezve volt és kattintható,
        // a jelzését viszont SEHOL nem fogta el senki — a testvérei
        // (Kollázs, Exportálás, Nyomtatás) mind be voltak kötve. Ez volt a
        // valódi oka annak, hogy a Beállítások e-mail-módja némának
        // látszott: az egész küldési út néma volt.
        onEmailRequested: window.sendSelectionByEmail()
    }

    // -- fájlműveletek (#15): kontextusmenü + dialógusok --------------------

    PhotoContextMenu {
        id: photoContextMenu
        // #1613: a lemezt CSAK a menü megnyitásakor kérdezzük meg — egy
        // kötés minden képkockán fájlrendszert olvasna.
        onAboutToShow: {
            var ut = controller
                ? controller.photos.filePathAt(window.fileOpTargetRow) : ""
            photoContextMenu.hasOriginalOnDisk =
                ut.length > 0 && fileOpsController.hasOriginalOnDisk(ut)
        }
        // #17: pipa, ha a jobbklikkelt kép rejtett (photos.revision-nel
        // együtt kötve, hogy a menü újranyitáskor friss legyen)
        // #305: null-őr
        hideChecked: controller
            ? (controller.photos.revision,
               (controller.photos.itemAt(window.fileOpTargetRow)
                    .hidden === true))
            : false
        // #422: a mentés-parancsok aktív állapota — a jobbklikkelt képen
        // van-e szerkesztés, illetve van-e mentés-előtti másolat
        hasEdits: controller
            ? (controller.photos.revision,
               (controller.photos.itemAt(window.fileOpTargetRow)
                    .hasEdits === true))
            : false
        hasBackup: controller
            ? controller.hasSavedBackup(window.selectedRows()) : false
        onSaveRequested: saveDialogs.ensure().openSave(window.selectedRows())
        onRevertRequested: saveDialogs.ensure().openRevert(window.selectedRows())
        onUndoAllEditsRequested: {
            if (typeof batchEffectController !== "undefined"
                    && batchEffectController)
                batchEffectController.clearAllEffectsMany(window.selectedRows())
        }
        onResetFacesRequested: resetFacesConfirm.open()   // mindig kérdez
        onHideToggleRequested: window.toggleHiddenSelection()
        onMoveRequested: fileOpsDialogs.openMove(window.selectedPaths())
        onDeleteRequested: fileOpsDialogs.openDelete(window.selectedPaths())
        onLocateRequested: {
            var p = controller.photos.filePathAt(window.fileOpTargetRow)
            if (p.length > 0) fileOpsController.revealPhoto(p)
        }
        // #1613: a „Keresés" almenü két új tétele.
        //
        // A `hasOriginalOnDisk` a menü MEGNYITÁSAKOR kérdez rá a lemezre
        // (`fileOpTargetRow` változásakor) — kötésben nem tehetnénk, mert
        // az minden képkockán fájlrendszert kérdezne.
        onLocateOriginalRequested: {
            var p = controller.photos.filePathAt(window.fileOpTargetRow)
            if (p.length > 0) fileOpsController.revealOriginal(p)
        }
        // az eredeti `IDS_LOCATE_SOURCE_IMAGE`: a kép VALÓDI mappájára ugrik
        // (album-/Emberek-nézetből, ahol a kép nem a saját mappájában látszik)
        onLocateInPicasaRequested: {
            var p = controller.photos.filePathAt(window.fileOpTargetRow)
            if (p.length === 0) return
            var mappa = p.substring(0, p.lastIndexOf("/"))
            if (mappa.length === 0) return
            toolbar.clearSearch()
            window.clearSelection()
            window.unnamedFacesOpen = false
            controller.selectFolder(mappa)
        }
        // #422 (2. lépcső): az eredeti AlbumPhoto-menü többi parancsa
        onOpenRequested: {
            window.viewerOpen = true
            photoViewer.show(window.fileOpTargetRow)
        }
        onRotateRightRequested: controller.rotateRightMany(window.selectedRows())
        onRotateLeftRequested: controller.rotateLeftMany(window.selectedRows())
        onOpenFileRequested: {
            var target = controller.photos.filePathAt(window.fileOpTargetRow)
            if (target.length > 0) fileOpsController.openPhoto(target)
        }
        onCopyFullPathRequested: {
            var full = controller.photos.filePathAt(window.fileOpTargetRow)
            if (full.length > 0) fileOpsController.copyFullPath(full)
        }
        onPropertiesRequested: window.valtsFiokLapot("properties")
        // #9 (2. lépés): albumtagság — #305 null-őr
        albums: controller ? controller.albums : []
        currentAlbumToken: controller ? controller.currentAlbumToken : ""
        onAddToAlbumRequested: function(token) {
            if (controller) controller.addRowsToAlbum(window.selectedRows(), token)
        }
        onRemoveFromAlbumRequested: {
            if (controller)
                controller.removeRowsFromAlbum(
                    window.selectedRows(), controller.currentAlbumToken)
        }
        onNewAlbumRequested: fileOpsDialogs.openNewAlbum(window.selectedRows())
        // #422 4. lépcső: az Emberek-album kép-szintű parancsai. A tételek
        // csak személy-albumban látszanak (üres `personName` = rejtve).
        personName: controller ? controller.currentPersonName : ""
        onRemoveFromPeopleAlbumRequested: {
            if (controller) removePeopleFacesDialog.openFor(
                window.selectedRows(), controller.currentPersonName)
        }
        onMoveToNewPersonRequested: {
            if (controller) moveToNewPersonDialog.openFor(
                window.selectedRows(), controller.currentPersonName)
        }
    }

    // #422: „Eltávolítás az Emberek albumból" — a kijelölt képekről leveszi
    // az ADOTT személy arc-címkéjét (a régió is eltűnik: a Picasa is az
    // arcot veszi le, nem csak a nevet). Megerősítéssel: a névcímke
    // visszaállítása csak újbóli felismeréssel/kézi felvétellel lehetséges.
    ConfirmDialog {
        id: removePeopleFacesDialog
        objectName: "removePeopleFacesDialog"
        namePrefix: "removePeopleFaces"
        title: qsTr("Remove from People Album")
        property var rows: []
        property string person: ""
        function openFor(rowList, name) {
            if (rowList.length === 0 || name.length === 0) return
            rows = rowList
            person = name
            ask("removePeopleFaces", qsTr(
                "The face tag \"%1\" will be removed from %n selected"
                + " picture(s).", "", rowList.length).arg(name))
        }
        onConfirmed: controller.removePersonFromRows(rows, person)
    }

    // #422: „Áthelyezés új személyhez…" — az adott személy arc-címkéje a
    // kijelölt képeken ÁTKERÜL egy másik névre (a régió marad).
    NameInputDialog {
        id: moveToNewPersonDialog
        objectName: "moveToNewPersonDialog"
        title: qsTr("Move to New Person")
        prompt: qsTr("New person's name:")
        property var rows: []
        property string person: ""
        function openFor(rowList, name) {
            if (rowList.length === 0 || name.length === 0) return
            rows = rowList
            person = name
            openEmpty()
        }
        onAccepted: controller.movePersonOnRows(rows, person, enteredName)
    }

    // #449: első indítás — a kérdés az ablak megjelenése UTÁN jön elő, hogy
    // a felhasználó lássa, mibe kerül bele
    InitialScanDialog {
        id: initialScanDialog
        objectName: "initialScanDialog"
        // #1167: a migrációs „frissítés" ág a meglévő Picasa-átvételt
        // nyitja (#146) — a felderítést a PicasaImportDialog végzi újra
        onImportRequested: {
            if (typeof discoveryController !== "undefined" && discoveryController)
                discoveryController.openImportDialog()
        }
    }

    // #1051: a kollázs-piszkozat visszaállításának felajánlása. A LAPRA
    // váltás a gazdáé — a párbeszéd csak jelez, ahogy a `CollagePanel` is.
    CollageDraftDialog {
        id: collageDraftDialog
        onRestored: documentTabStrip.activateTab(window.collageTabId)
    }

    // #1129: a lebegő értesítősáv (Picasa Notifier) — önálló, keret nélküli
    // ablak a munkaterület jobb alsó részén. Az alkalmazás indítása hozza
    // létre, nem a főablak, ezért nincs `transientParent`-je.
    //
    // A `NotifierBus.attached` kapun át a `CollageDoneNotice` MAGÁTÓL
    // elhallgat, amint a sáv jelen van — így ugyanaz az esemény nem szólal
    // meg kétszer, két helyen. A `CollageDoneNotice` SZÁNDÉKOSAN marad a
    // fában: a #1119 őre a jelenlétét állítja, és a törlése önálló döntés
    // (a sáv nélküli üzemmód tartaléka).
    PicasaNotifier {
        id: picasaNotifier
        onActivated: function (kind, payload) {
            if (kind === "collage")
                window.openCollageNodeInEditor(payload)
        }
    }

    // #1028: „A kollázs kész (kattintson ide)" — a lapzárás UTÁN is látszik,
    // ezért a gazdában él, nem a panelben, ami közben bezárul.
    CollageDoneNotice {
        id: collageDoneNotice
        z: 100
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        onClicked: {
            var cel = collageDoneNotice.path
            collageDoneNotice.dismiss()
            window.openCollageNodeInEditor(cel)
        }
    }

    // #444: Mentés / Visszaállítás / Utolsó mentés visszavonása
    // #1720: halasztott példányosítás — a párbeszéd csak az első
    // megnyitáskor épül fel (ld. `DeferredDialog.qml`).
    DeferredDialog {
        id: saveDialogs
        // ⚠️ Az `objectName` a BECSOMAGOLT párbeszédé marad, nem a
        // `Loader`-é: a `findChild(objectName)` így a megnyitás után a
        // VALÓDI komponenst adja vissza, nem a burkot.
        objectName: "saveDialogsLoader"
        anchors.fill: parent
        sourceComponent: Component {
            SaveDialogs { objectName: "saveDialogs"; appWindow: window }
        }
    }

    // átnevezés / áthelyezés / törlés / hiba (FileOpsDialogs.qml, #150)
    FileOpsDialogs {
        id: fileOpsDialogs
        objectName: "fileOpsDialogs"
        appWindow: window
    }

    // exportálás mappába (#16, Ctrl+Shift+S; ExportDialogs.qml, #150)
    // #1720: halasztott példányosítás — a párbeszéd csak az első
    // megnyitáskor épül fel (ld. `DeferredDialog.qml`).
    DeferredDialog {
        id: exportDialogs
        anchors.fill: parent
        sourceComponent: Component {
            ExportDialogs { appWindow: window }
        }
    }

    // #1743: A HALLGATÓK MINDIG ÁLLNAK, a párbeszéd nem.
    //
    // A #1720 óta a mentés- és export-párbeszéd halasztott: csak az első
    // megnyitáskor épül fel. A vezérlő eredmény- és hibajelzéseit viszont
    // EDDIG a párbeszéden BELÜLI `Connections` fogadta — ami addig nem is
    // létezett. Amíg minden belépő az `ensure()`-ön át megy, ez nem okoz
    // bajt; egy ÚJ belépő (gyorsbillentyű, tálcagomb, kötegelt művelet)
    // viszont némán elnyelné a hibaüzenetet, és semmilyen teszt nem bukna
    // el rá.
    //
    // Ezért a hallgató ide került, a mindig felépülő ablakba: pár objektum,
    // a #1720 nyeresége érintetlen. Az `ensure()` a jelzés pillanatában
    // építi fel a párbeszédet — pontosan akkor, amikor tényleg kell.
    Connections {
        target: controller
        function onSaveFailedDetails(details) {
            saveDialogs.ensure().jelezdAbukottMentest(details)
        }
        function onSaveErrorOccurred(kind, fileName, code) {
            saveDialogs.ensure().jelezdAmentesiHibat(kind, fileName, code)
        }
        function onExportFailedDetails(details) {
            exportDialogs.ensure().jegyezdAbukottFajlokat(details)
        }
        function onExportFinished(done, failed) {
            exportDialogs.ensure().jelezdAzExportVeget(done, failed)
        }
        function onEarthExportFinished(kmlPath, placemarks, skipped) {
            exportDialogs.ensure().jelezdAzEarthExportVeget(
                kmlPath, placemarks, skipped)
        }
        function onEarthViewReady(kmlPath, placemarks, skipped) {
            exportDialogs.ensure().nyisdMegAzEarthFajlt(
                kmlPath, placemarks, skipped)
        }
    }

    // kollázs és mozgófilm a kijelölésből (#29; CreateDialogs.qml)
    CreateDialogs {
        id: createDialogs
        appWindow: window
    }

    DeferredDialog {
        id: aboutDialog
        anchors.fill: parent
        // az `objectName` a BECSOMAGOLT párbeszédé — enélkül a #1720
        // őre üres halmazt vizsgálna, azaz némán mindig zöld lenne
        sourceComponent: Component { AboutDialog { objectName: "aboutDialog" } }
    }

    // #350: Beállítások-dialógus (options.fen)
    DeferredDialog {
        id: optionsDialog
        anchors.fill: parent
        sourceComponent: Component { OptionsDialog { } }
    }

    // #351: webexport-dialógus (.tpl sablonmotor)
    DeferredDialog {
        id: webExportDialog
        anchors.fill: parent
        sourceComponent: Component { WebExportDialog { } }
    }

    // #1472: nyomtatás-párbeszéd (nyomtató-választó + PDF-fájlba nyomtatás)
    DeferredDialog {
        id: printDialog
        anchors.fill: parent
        sourceComponent: Component { PrintDialog { } }
    }

    // #368: adatbázis-áthelyezés dialógus (relocateController hídon)
    // #422: „Arcok alaphelyzetbe állítása" — az eredeti szó szerinti
    // figyelmeztetésével (`CThumbUI::ResetAllFaces`). A `.picasa.ini`
    // névcímkéihez NEM nyúlunk: azt az eredeti is KÜLÖN kérdezte meg, és
    // az ember által adott név nálunk szent.
    ConfirmDialog {
        id: resetFacesConfirm
        objectName: "resetFacesConfirm"
        namePrefix: "resetFaces"
        title: qsTr("Reset Faces")
        message: qsTr("WARNING! This will move all the faces back to the "
                      + "unnamed album and delete the face groups. Name tags "
                      + "you have written into the photos are NOT touched. "
                      + "Do you want to do this?")
        onConfirmed: {
            if (typeof faceScanController !== "undefined" && faceScanController)
                faceScanController.resetAllFaces()
        }
    }

    DeferredDialog {
        id: moveDatabaseDialog
        anchors.fill: parent
        sourceComponent: Component { MoveDatabaseDialog { } }
    }
    // #644: figyelmeztetés, ha egy másik program felülírta a szerkesztéseinket
    DeferredDialog {
        id: editOverwriteDialog
        anchors.fill: parent
        sourceComponent: Component { EditOverwriteDialog { } }
    }
    Connections {
        target: controller
        function onEditsOverwritten(lost) { editOverwriteDialog.ensure().show(lost) }
    }
    DeferredDialog {
        id: compactDatabaseDialog
        anchors.fill: parent
        sourceComponent: Component { CompactDatabaseDialog { } }
    }

    // Indítóképernyő (#189): a legfelső rétegen ül, a startupStatus hídból
    // kapja az állapotot, és ready-re magától kifakul/eltűnik.
    // A kötés defenzív: híd (context property) nélkül — pl. célzott
    // tesztkörnyezetben — a splash készre áll, azaz rejtve marad.
    SplashScreen {
        readonly property var statusBridge:
            typeof startupStatus !== "undefined" ? startupStatus : null
        anchors.fill: parent
        z: 10000
        version: appVersion
        statusText: statusBridge ? statusBridge.statusText : ""
        ready: statusBridge ? statusBridge.ready : true
        // #243: félkész-figyelmeztetés + OK a betöltés végén, amíg az
        // effekt-paritás nem teljes (a kapcsoló az application.py-ban él)
        confirmationRequired:
            statusBridge ? statusBridge.requiresConfirmation : false
    }
}
