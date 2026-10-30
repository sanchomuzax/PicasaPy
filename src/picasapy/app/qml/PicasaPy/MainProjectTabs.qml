import QtQml

// A kollázs- és filmprojektlapok állapota, listája és navigációja.
QtObject {
    id: projectTabsState
    required property var hostWindow
    required property var hostController
    required property var hostDocumentTabStrip
    required property var hostSlideshow
    required property var hostCreateDialogs
    required property var collageTitle
    required property var movieMakerTitle

    // -- Dokumentum-lapok (#985; a sáv maga a #944) -------------------------
    //
    // Az eredetiben a kollázs NEM párbeszédablak, hanem SAJÁT LAP a fülsávban
    // (`panelroot/collagetab`), a „Könyvtár" lapja mellett — ld.
    // `docs/specs/kollazs-panel-ui-spec.md` 3.1. Ma egyetlen projekt-laptípus
    // van, a kollázs; a lista mégis lista, mert a sáv szerződése az.
    readonly property string collageTabId: "collage"
    readonly property string movieMakerTabId: "movieMaker"
    property bool movieMakerTabOpen: false
    readonly property real documentTabsBottom:
        hostDocumentTabStrip.y + hostDocumentTabStrip.height
    readonly property string activeDocumentTabId:
        hostDocumentTabStrip.activeTabId
    readonly property bool movieMakerActive:
        hostWindow.movieMakerTabOpen
        && hostDocumentTabStrip.activeTabId === hostWindow.movieMakerTabId
    property bool backToMovieMakerPrompted: false
    readonly property var openProjectTabs: {
        var tabs = []
        if (hostController && hostController.collageOpen) {
            tabs.push({
                id: hostWindow.collageTabId,
                title: collageTitle,
                modified: hostController.collageDirty === true
            })
        }
        if (hostWindow.movieMakerTabOpen) {
            tabs.push({
                id: hostWindow.movieMakerTabId,
                title: movieMakerTitle,
                modified: false
            })
        }
        return tabs
    }

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
        (hostDocumentTabStrip.libraryActive || hostWindow.viewerOpen)
        && !hostWindow.slideshowRunning

    //: #2987: MÉRVE — a vetítés eddig az `ApplicationWindow` contentItem-jét
    //: töltötte ki, vagyis a fejléc ÉS a lábléc KÖZÖTTI sávot, a menüsáv
    //: nélkül: 800 képpontos ablakban 626 px jutott neki, és mind a három
    //: sáv látszott. Az ablak teljes képernyőre váltott (a kérés kiment),
    //: a vetítés mégis dobozban maradt — a jegy 3. esete, platformfüggetlenül.
    //: Az eredetiben a vetítés alatt SEMMI MÁS nem látszik (#1903).
    readonly property bool slideshowRunning: hostSlideshow.visible

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
        if (!hostController) return []
        var held = hostController.heldPaths || []
        var rows = []
        for (var i = 0; i < held.length; ++i) {
            var row = hostController.photos.rowOfPath(String(held[i]))
            if (row >= 0) rows.push(row)
        }
        if (rows.length > 0) return rows
        return hostWindow.selectedRows()
    }

    /** A Kollázs LAP megnyitása — a Létrehozás menü és a tálca gombja is ide
        fut be (spec 3.2). Ha már nyitva van, csak visszaváltunk rá: a
        felhasználó munkáját újranyitással eldobni némán adatvesztés volna. */
    /** #1006: kollázs a MEGADOTT sorokból — a fejléc-gomb belépője.

        A `openCollageTab()` a tálcát vagy a kijelölést veszi
        (`collageSourceRows`); a fejléc viszont a SAJÁT csoportjához
        tartozik, tehát a sorokat ő adja meg. A többi lépés — a néző
        elhagyása, a lap aktiválása — ugyanaz, ezért egy helyen él. */
    function openCollageFromRows(rows) {
        if (!hostController) return
        if (!hostWindow.aaKapu(function () { hostWindow.openCollageFromRows(rows) })) return
        hostWindow.backToCollagePrompted = false
        hostWindow.viewerOpen = false
        if (!hostController.collageOpen)
            hostController.openCollage(rows)
        hostDocumentTabStrip.activateTab(hostWindow.collageTabId)
    }

    //: #4539: a mappa-fejléc film-gombja — a csoport sorait a meglévő
    //: Filmkészítőbe adja (a kijelölés nem számít, mint a kollázsnál).
    function openMovieFromRows(rows) {
        if (!hostController || rows.length === 0) return
        hostCreateDialogs.ensure().openMovieForRows(rows)
    }

    // A filmkészítő a kollázshoz hasonlóan saját dokumentumlap. A tartalom
    // a CreateDialogs.qml-ben marad, de a navigációt a főablak kezeli.
    function openMovieMakerTab() {
        hostWindow.viewerOpen = false
        hostWindow.backToMovieMakerPrompted = false
        hostWindow.movieMakerTabOpen = true
        hostDocumentTabStrip.activateTab(hostWindow.movieMakerTabId)
    }

    function openMovieClipCollector() {
        if (!hostWindow.movieMakerTabOpen) return
        hostWindow.backToMovieMakerPrompted = true
        hostDocumentTabStrip.activateTab(hostDocumentTabStrip.libraryTabId)
    }

    function returnToMovieMaker() {
        hostWindow.backToMovieMakerPrompted = false
        if (hostWindow.movieMakerTabOpen)
            hostDocumentTabStrip.activateTab(hostWindow.movieMakerTabId)
    }

    function closeMovieMakerTab() {
        hostWindow.movieMakerTabOpen = false
        if (hostDocumentTabStrip.activeTabId === hostWindow.movieMakerTabId)
            hostDocumentTabStrip.activateTab(hostDocumentTabStrip.libraryTabId)
    }

    function openCollageTab() {
        if (!hostController) return
        if (!hostWindow.aaKapu(hostWindow.openCollageTab)) return
        hostWindow.backToCollagePrompted = false
        // #1055: a NÉZŐT (és vele a szerkesztőt) el kell hagyni. A kollázs
        // panelje `!viewerOpen`-re látszik, a képtálca kollázs-gombja
        // viszont a nézőben IS ott van (`libraryFrameVisible`) — enélkül a
        // lap megnyílik, a kollázs elkészül, és a felhasználó közben a
        // mappanézetet látja. Pontosan ezt jelentette a v0.8.7-en.
        hostWindow.viewerOpen = false
        if (!hostController.collageOpen)
            hostController.openCollage(hostWindow.collageSourceRows())
        hostDocumentTabStrip.activateTab(hostWindow.collageTabId)
    }

    /** Egy KÉSZ kollázs újranyitása szerkesztésre (#1002).

        A tulajdonos jelentése a v0.8.17-ről: *„Jelenleg ennek hiányában nem
        szerkeszthető a kollázs."* — a kész képtől nem vezetett vissza út a
        panelra.

        A nézőt elhagyjuk (#1055): a kollázs panelje `!viewerOpen`-re
        látszik, tehát enélkül a lap megnyílna, és a felhasználó közben a
        képet nézné. */
    /** #2114: a FILM újranyitása a projektfájljából.

        Az eredeti „Mozgófilm szerkesztése" gombja a forrásprojektet nyitja
        meg; nálunk a filmkészítő párbeszéd a szerkesztő felülete, ezért a
        projekt képeit KIJELÖLJÜK, és a párbeszéd a projekt diaidejével jön
        fel. A forrásképek tipikusan nem a jelenlegi nézetben állnak — a
        `locateSavedCollage` mintájára előbb a mappájukra állunk. */
    function openSavedMovie(path) {
        if (!hostController) return
        if (!hostWindow.aaKapu(function () { hostWindow.openSavedMovie(path) })) return
        var cel = String(path || "")
        if (cel.length === 0) return
        var projekt = hostController.movieProject(cel)
        if (!projekt || !projekt.sources || projekt.sources.length === 0) return
        var elso = String(projekt.sources[0])
        if (hostController.photos.rowOfPath(elso) < 0) {
            var mappa = hostWindow.folderOfPath(elso)
            if (mappa.length > 0) hostController.selectFolder(mappa)
        }
        var sorok = []
        for (var i = 0; i < projekt.sources.length; ++i) {
            var sor = hostController.photos.rowOfPath(String(projekt.sources[i]))
            if (sor >= 0) sorok.push(sor)
        }
        //: ha egyetlen forráskép sincs meg (törölt/áthelyezett mappa), a
        //: párbeszéd megnyitása félrevezető volna — a gomb inkább ne
        //: csináljon semmit, mint hogy MÁS képekből ajánljon filmet (#936)
        if (sorok.length === 0) return
        hostWindow.viewerOpen = false
        hostDocumentTabStrip.activateTab(hostDocumentTabStrip.libraryTabId)
        hostWindow.selectedIndex = sorok[0]
        hostWindow.selectedIndexes = sorok
        hostCreateDialogs.ensure().openMovieProject(
            projekt.seconds, projekt.burstmodethresh, cel)
    }

    function openSavedCollage(path) {
        if (!hostController) return
        if (!hostWindow.aaKapu(function () { hostWindow.openSavedCollage(path) })) return
        var cel = String(path || "")
        if (cel.length === 0) return
        hostController.openCollageProject(cel)
        if (!hostController.collageOpen) return
        hostWindow.viewerOpen = false
        hostWindow.backToCollagePrompted = false
        hostDocumentTabStrip.activateTab(hostWindow.collageTabId)
    }

    /** A KÉSZ kollázs megkeresése a könyvtárban (#1028).

        Az eredeti mentő négy záró lépése közül ez a negyedik: `locate` az
        új fájlra. A lap bezárása (harmadik lépés) már megvan — az a
        `CollagePanel.finishSave` dolga; ide a NAVIGÁCIÓ tartozik.

        ⚠️ Nézőt szándékosan NEM nyit: az eredeti is csak kijelöl, a
        nagyban megnyitás a felhasználó kattintása az értesítésen. */
    function locateSavedCollage(path) {
        if (!hostController) return
        var cel = String(path || "")
        if (cel.length === 0) return
        var sor = hostController.photos.rowOfPath(cel)
        if (sor < 0) {
            // A Kollázsok mappa tipikusan NEM a jelenlegi nézet: előbb oda
            // állunk, aztán kérdezünk újra. (Az indexbe a mentés veszi fel,
            // #1048 — enélkül a mappa üres volna.)
            var mappa = hostWindow.folderOfPath(cel)
            if (mappa.length > 0) {
                hostController.selectFolder(mappa)
                sor = hostController.photos.rowOfPath(cel)
            }
        }
        hostDocumentTabStrip.activateTab(hostDocumentTabStrip.libraryTabId)
        if (sor >= 0) {
            hostWindow.selectedIndex = sor
            hostWindow.selectedIndexes = [sor]
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
        if (!hostController) return
        var cel = String(path || "")
        if (cel.length === 0) return
        var sor = hostController.photos.rowOfPath(cel)
        if (sor < 0) {
            // A kollázs képei mappákon átnyúlhatnak (a „+" gomb más mappából
            // is vehet fel klipet), a feed pedig szűrve/keresve szűkebb
            // lehet: előbb a kép mappájára állunk, aztán újra kérdezünk.
            var mappa = hostWindow.folderOfPath(cel)
            if (mappa.length > 0) {
                hostController.selectFolder(mappa)
                sor = hostController.photos.rowOfPath(cel)
            }
        }
        // Néma bukás helyett sem tehetünk mást: a kép nincs az indexben (pl.
        // időközben törölték). A kollázs lapja érintetlen marad.
        if (sor < 0) return

        hostWindow.backToCollagePrompted = true
        hostDocumentTabStrip.activateTab(hostDocumentTabStrip.libraryTabId)
        hostWindow.selectedIndex = sor
        hostWindow.selectedIndexes = [sor]
        hostWindow.openPhotoViewer(sor)
    }

}
