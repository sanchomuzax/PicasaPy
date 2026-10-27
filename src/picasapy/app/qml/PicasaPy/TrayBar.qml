import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Alsó sáv (#150-ben kiemelve a Main.qml-ből): kék infó-sáv (busy-
// animációval, #70) + kijelölés-tálca a művelet-gombokkal (Picasa).
// A kijelölés-állapot a főablaké (appWindow); a néző aktuális sorát a
// viewerIndex tulajdonság hozza.
//
// #1420: a sáv az EREDETI geometriáját kapta meg. A `thumbui.tre`
// `publishbottom`-ja **−105**, tehát a sáv 105 képpont magas — de a
// magasságot ÖNMAGÁBAN emelni hiba lett volna, mert holt sávot adott
// volna. Az eredetiben a 105 képpontot tartalom tölti ki, és a sáv az
// ablakszélesség **0,365-szörösénél** válik ketté:
//
//     ┌────────────────────────── 105 px ──────────────────────────┐
//     │ kék infó-csík (nálunk 20, az eredetiben 14 — szándékos)     │
//     ├───────────── 36,5 % ─────┬─────────────────────────────────┤
//     │ képtálca (81 px magas)   │ ★ ↺ ↻ … nagyító ▭nagyítás▭      │
//     │  bélyegképsor + 3 gomb   ├─ elválasztó (y 50…52) ──────────┤
//     │                          │ [zöld 141×35] [Nyomtatás/E-mail…]│
//     └──────────────────────────┴─────────────────────────────────┘
//
// Minden szám a Picasa saját elrendezés-forrásából jön (`respack.yt` →
// `thumbui.tre`), és VISSZA VAN MÉRVE egy valódi Picasa-képernyőképen
// (`research/testdata/screenshot/Képernyőkép 2026-07-18 145027.png`,
// 1918 px széles ablak; 0,365 × 1918 = 700,07):
//
//   scratchback   x 5…684        (kényszer: 5 … .365−15)   y 947…1027 = 81
//   separator     x 697…1902     (kényszer: .365−3 … −17)  y 977…978
//   webupload     x 697…837 =141                            y 988…1022 = 35
//   outputs 1. gomb közepe x 867,5 = (.365·W + 140) + 55/2
//   startoggle/rotateleft/rotateright  x 697…732 · 738…773 · 775…810 (36×22)
//
// A normatív lap: `docs/specs/konyvtar-ablak-meretek.md` 5. fejezet.
Column {
    id: tray

    // #4639: a súgó a tálca valódi Shortcut.sequence értékét olvassa.
    readonly property var keyboardShortcutSequences: [
        trayKeepSelectionShortcut.sequence
    ]

    // #1367: a sáv MÉRT szélesség-igénye — a `Main.qml` erre köti az ablak
    // `minimumWidth`-ét. A gyökéren át érhető el, mert a főablak a
    // komponenst látja, nem a belső `trayMainBar`-t.
    readonly property real requiredWidth: trayMainBar.requiredWidth

    // a főablak (kijelölés-állapot + rotateTargetsAllVideo őr gazdája)
    required property var appWindow
    // a néző aktuális sora (a Main köti a photoViewer.currentIndex-re)
    property int viewerIndex: -1
    // az Exportálás gomb (a dialógus a Main.qml-ben él)
    signal exportRequested()
    // #1917: a tálca helyi menüjének ÖRÖKÖLT tételei — a vezérlők a
    // Main.qml-ben élnek, ide csak a jelzés jut el.
    signal viewAndEditRequested()
    signal trayRotateRightRequested()
    signal trayRotateLeftRequested()
    signal trayLocateRequested()
    signal trayPropertiesRequested()
    // #361: Kollázs/Film a tálcáról (a dialógusok a Main.qml-ben élnek)
    signal collageRequested()
    signal movieRequested()
    //: #1939: a klip-gyűjtő mód üzenetsávjának „Vissza" gombja
    signal backToCollageRequested()
    signal backToMovieMakerRequested()
    // #32 (RÉSZLEGES kör): Nyomtatás/E-mail — a dialógusok (nyomtató-
    // választó, tárgy/szöveg-bekérés) a Main.qml-ben élnének, ugyanúgy,
    // mint a fenti kettőnél (a bekötés az integrátor lépése, ld.
    // print_controller.py/email_controller.py docstringje).
    signal printRequested()
    signal emailRequested()
    signal addSelectedToScreensaverRequested()
    signal starSelectedPhotosRequested()
    signal newAlbumWithSelectionRequested()
    // #4637: a kimeneti gombsor jobbklikkje a gazda közös gombmenüjét kéri.
    signal configureButtonsContextMenuRequested(var anchorItem, real x, real y)
    // #5008: a rácsból húzott képeket rögzítjük a képtálcán.
    signal photosDroppedOnTray(var rows)

    // #2564: a SZERKESZTŐ nagyítás-hármasa ebben a sávban él, a könyvtár
    // bélyegkép-csúszkájának a helyén — mérve (`editpanel.tre:1288–1324` +
    // `respack.yt`): az eredetiben az `editpanel/zoomup_icon` x 368…392 és
    // az `editpanel/zoomslider_container` x 399…526 PONTOSAN a `thumbui`
    // `loupehit` 366…391 / `scalecontainer` 398…525 rését foglalja el.
    // Egy sáv, módonként cserélt tartalom — nem két külön hely.
    //
    // A vezérlők maguk a nézőé (`PhotoViewer.qml`), ezért az állapot
    // ideérkezik, a művelet pedig jelzésként megy vissza. A `Main.qml`
    // köti össze a kettőt.
    //: a néző nagyítás-értéke (normalizált 0…1, #2492)
    property real viewerZoomValue: 0
    //: látszik-e egyáltalán a hármas: nyitott néző, nem videó, nem vágás
    property bool viewerZoomAvailable: false
    signal zoomFitRequested()
    signal zoomActualRequested()
    signal zoomValueRequested(real ertek)

    // #4600: az `F4` a csillag-gomb kattintása, ha a gomb engedélyezett
    // (az eredetiben `[eax+0x20e] == 0` őr) — tiltottan nem tesz semmit.
    function kapcsoldACsillagot() {
        if (tray.visible && trayRightPane.starEnabled)
            trayRightPane.activateStar()
    }

    // a forgatás/csillag célsora — a Main rotateTargetRow()-ja is ezt kéri
    readonly property int starTargetRow: trayRightPane.starTargetRow

    function photosUploadMessage() {
        if (!tray.ctl)
            return ""
        var code = tray.ctl.photosUploadError
        if (code === "network")
            return qsTr("Network error. Check your connection and try again.")
        if (code === "token_expired")
            return qsTr("Your Google Photos sign-in has expired. Sign in again.")
        if (code === "quota")
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:UploadError::RateLimit
            return qsTr("Maximum Upload Rate Exceeded")
        if (code === "service_unavailable")
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:Lighthouse::ServiceUnavailableES
            return qsTr("Google Photos is temporarily unavailable")
        if (code === "cancelled")
            return qsTr("Upload cancelled")
        if (code === "invalid_image")
            return qsTr("A photo could not be prepared for upload.")
        if (code === "file_too_large")
            return qsTr("This photo is too large to upload.")
        if (code === "empty_tray")
            return qsTr("There are no photos in the Photo Tray.")
        if (code)
            return qsTr("Google Photos could not complete the upload. Try again.")
        if (tray.ctl.photosUploadFinished)
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:uploadmgr::complete
            return qsTr("Upload complete")
        if (tray.ctl.photosUploadPhase === "preparing")
            return qsTr("Preparing photo %1 of %2").arg(
                tray.ctl.photosUploadDone).arg(tray.ctl.photosUploadTotal)
        if (tray.ctl.photosUploadPhase === "uploading")
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:QuickUploader::progress
            return qsTr("Uploading %1").arg(tray.ctl.photosUploadCurrentName)
        if (tray.ctl.photosUploadPhase === "creating")
            return qsTr("Adding photo %1 of %2").arg(
                tray.ctl.photosUploadDone).arg(tray.ctl.photosUploadTotal)
        return qsTr("Preparing photos for upload")
    }

    // #305: null-őr — a controller a QML-engine leépítésekor átmenetileg
    // null lehet, miközben ezek a kötések utoljára kiértékelődnek.
    readonly property var ctl: controller
    // A `photoInfo`/`viewerInfo` invokálható függvény eredménye nem QML-
    // kötésfüggőség önmagában. A címkeírás utáni model-változásnak ezért
    // külön újra kell értékeltetnie az alsó infósávot.
    readonly property int photoRevision:
        tray.ctl && typeof tray.ctl.photos !== "undefined" && tray.ctl.photos
        ? tray.ctl.photos.revision : 0

    // #718: a kijelölés VÉDETT olvasata. A leépítésnek van egy köztes
    // állapota, amikor az `appWindow` már létezik, a `selectedIndexes`
    // viszont még/már `undefined` — a `.length` olvasása ilyenkor
    // TypeError. Az olvasó kötések ezért ezen a tulajdonságon át kérik a
    // kijelölést; az ÍRÁS (a kijelölés módosítása) marad közvetlenül az
    // `appWindow`-on, mert az csak felhasználói művelet közben fut, amikor
    // az ablak biztosan él.
    //: #1168 (spec 16.3): `CThumbUI::CreateCollageWait` (`0x007f7120`) — a
    //: főablak várakozó sora, amíg a kollázs készül. Külön tulajdonságban,
    //: hogy az infó-sáv hármas feltétele olvasható maradjon.
    readonly property string collageWaitText:
        qsTr("Waiting for the collage to be created…")

    // #2039: a tálca SAJÁT kijelölése (tálca-indexek). #1572 null-őr: a
    // próbák csonk-vezérlőjén ez a tulajdonság nem is létezik.
    readonly property var traySelectedIndexes: {
        if (!tray.ctl || tray.ctl.traySelectedIndexes === undefined) return []
        var lista = tray.ctl.traySelectedIndexes
        return (lista === null) ? [] : lista
    }
    readonly property bool trayHasSelection: tray.traySelectedIndexes.length > 0

    function trayIndexSelected(index) {
        return tray.traySelectedIndexes.indexOf(index) >= 0
    }

    // A tálcáról induló húzás kizárólag a tálca saját kijelölését viszi.
    // A tálca elemei tartalmazhatnak másik mappából rögzített képeket is,
    // ezért itt nem szabad a fő rács sorindexeit használni.
    function selectedTrayFileUriList() {
        if (!tray.ctl || typeof tray.ctl.fileUriList !== "function")
            return ""
        var items = tray.ctl.trayItems || []
        var paths = []
        var indexes = tray.traySelectedIndexes
        for (var i = 0; i < indexes.length; ++i) {
            var index = Number(indexes[i])
            if (index >= 0 && index < items.length && items[index].path)
                paths.push(items[index].path)
        }
        return tray.ctl.fileUriList(paths)
    }

    readonly property var selectedIndexesOrEmpty:
        (tray.appWindow && tray.appWindow.selectedIndexes)
            ? tray.appWindow.selectedIndexes
            : []

    // #4329: a Ctrl+H ugyanazt a jelzést küldi, mint a helyi menü
    // „Hold Selection” tétele; így egyetlen út tartja meg a kijelölést.
    Shortcut {
        id: trayKeepSelectionShortcut
        objectName: "trayKeepSelectionShortcut"
        sequence: "Ctrl+H"
        enabled: !!tray.appWindow
                 && !tray.appWindow.viewerOpen
                 && !tray.appWindow._szovegmezoneVanFokusz
                 && tray.selectedIndexesOrEmpty.length > 0
        onActivated: trayContextMenu.keepSelectionRequested()
    }

    // =====================================================================
    // #455: A KIJELÖLÉS AUTOMATIKUSAN A TÁLCÁBA KERÜL
    // =====================================================================
    // Az eredeti tálcája **a kijelölés meghosszabbítása** volt, nem külön
    // kosár: alapból a kijelölést mutatta, és a „Hold" fagyasztotta be,
    // hogy másik mappából is lehessen hozzátenni
    // (`thumbui/single_action_message` köre, `docs/specs/picasa-keptalca.md`).
    //
    // A tükrözés ITT történik, nem a `Main.qml`-ben: a tálca a sáv
    // felelőssége, és így a forró főablak-fájl érintetlen marad. A
    // `typeof`-őr azért kell, mert a sáv teszt-kettős vezérlőkkel is
    // betöltődik (`scripts/qml_undefined_or.py`).
    function syncTraySelection() {
        if (tray.ctl && typeof tray.ctl.syncSelection === "function")
            tray.ctl.syncSelection(tray.selectedIndexesOrEmpty)
    }
    // =====================================================================
    // #2741: MIKOR LÁTSZIK az összecsukott ALBUM-TOKEN — a mért szabály
    // =====================================================================
    // Az eredetiben ez sem parancs: a `scratch/album` réteg küldöttje
    // (`0x00572ba4` → `0x00563530`) minden frissítéskor újraértékel, és
    // akkor mutat, ha van album-/mappa-kijelölés, annak van eleme, ÉS a
    // KÉP-kijelölés üres.
    //
    // A 230. kutatói kör (PR #2789) fordította le a mi fogalmainkra: az
    // eredeti `+0xeac` EXPLICIT kijelölés (hét hívója közt a kollázs és a
    // feltöltési kijelölés), nem „hol vagyok" állapot — nálunk ez a
    // `controller.currentAlbumToken`. A megnyitott MAPPÁRA a szabály
    // szándékosan nem szól: ott a kép-kijelölés szinte mindig üres, tehát a
    // tálca megszokott kinézete változna meg.
    readonly property string albumTokenOrEmpty:
        (typeof controller !== "undefined" && controller
         && controller.currentAlbumToken !== undefined)
            ? controller.currentAlbumToken : ""
    // #5331: a SZEMÉLY-album is album-kijelölés az eredetiben (job-213, 29.
    // kép: „Album Selected - 2 photos" a személy arcképével). Személy módban
    // az album-token üres, ezért külön bemenet. A két mód nem él egyszerre.
    readonly property string personNameOrEmpty:
        (typeof controller !== "undefined" && controller
         && controller.currentPersonName !== undefined)
            ? controller.currentPersonName : ""

    function syncAlbumToken() {
        if (!tray.ctl
            || typeof tray.ctl.showSelectedAlbumToken !== "function")
            return
        var mutat = tray.selectedIndexesOrEmpty.length === 0
        if (mutat && tray.personNameOrEmpty !== ""
            && typeof tray.ctl.showSelectedPersonToken === "function") {
            tray.ctl.showSelectedPersonToken(tray.personNameOrEmpty)
            return
        }
        tray.ctl.showSelectedAlbumToken(mutat ? tray.albumTokenOrEmpty : "")
    }
    // MIND A HÁROM bemenetre (kijelölés, album, személy) újra kell
    // értékelni: egyetlen kötésre figyelve a token hazug állapotban
    // ragadna. A kijelölés-tükrözés MEGY ELŐRE: a `syncSelection` söpri el
    // a nem megtartott elemeket, és a token utána kerül vissza, ha a
    // szabály szerint kint kell lennie.
    onAlbumTokenOrEmptyChanged: tray.syncAlbumToken()
    onPersonNameOrEmptyChanged: tray.syncAlbumToken()

    onSelectedIndexesOrEmptyChanged: {
        tray.syncTraySelection()
        tray.syncAlbumToken()
    }
    Component.onCompleted: {
        tray.syncTraySelection()
        tray.syncAlbumToken()
    }

    //: A tálca elemszáma (a rögzített ÉS a kijelölésből tükrözött együtt).
    //: Ez a KÖTÉSI FÜGGŐSÉG is: a `trayInfo()`/`isHeldAt()` függvényhívások
    //: önmagukban nem hoznak létre függőséget, a `heldCount` olvasása igen.
    readonly property int trayCount:
        (tray.ctl && tray.ctl.heldCount !== undefined) ? tray.ctl.heldCount : 0

    //: #455: a kék infó-sáv a TÁLCÁRÓL ír (`il_GetSelectionInfo`). A
    //: műveletsor a tálca tartalmán dolgozik, tehát a darabszámnak, a
    //: dátumtartománynak és az összméretnek is azt kell összesítenie —
    //: a más mappából tartott képekkel együtt, amiket a rács nem is mutat.
    // A rekord mezőinek módosulása nem változtatja a `trayCount`-ot; a
    // modellverzió a tálca adatait is újra lekéri (pl. új címkék után).
    readonly property string trayInfoText:
        (tray.photoRevision,
         (tray.trayCount > 0 && tray.ctl
          && typeof tray.ctl.trayInfo === "function")
             ? tray.ctl.trayInfo() : "")

    // tömör acélkék infó-sáv; kijelöléskor a kép adatai
    //
    // #1914: a MÉRT függőleges felosztás. A tálca függőleges méretei
    // 1:1-ben képpontok — ezt a #1914 két független méréssel igazolta
    // (kék csík 15 px ↔ 14 tervezőpont; teljes tálca 104 ↔ 105; és a
    // `scratch` 60 pontos magassága a 67 képes felvételen képpontra
    // kijött: 3 sor × 18 + 2 rés × 3 = 60).
    //
    //     thumbui/rect: basecontrolset   y 429…534   105 magas
    //     thumbui/text( ): infotext      y 429…443    14 magas
    //     thumbui/rect: scratchback      y 449…530    81 magas
    //     a sáv alja                     y 534
    //
    //     14 (csík) + 6 (térköz) + 81 (doboz) + 4 (alsó) = 105 ✓
    //
    // ⚠️ #1913 HELYESBÍTÉS: a #1914 az összeget eltalálta, a kettévágást
    // nem — 5+5 helyett 6+4 a mért érték. A tévedés forrása, hogy „az
    // első vezérlők felső éle y 448"; ez IGAZ, de MÁS vezérlőkre:
    //
    //     thumbui/rect: scale_group      y 448…475   (nagyító)
    //     thumbui/rect: metadata_group   y 448…472   (Személyek/Helyek/…)
    //     thumbui/rect: scratchback      y 449…530   ← a TÁLCA doboza
    //     …: rotateleft / startoggle     y 449…471   ← és a gombsora
    //
    // A rétegfejléc `y1`-e NYÍLT (a képpontszám igazolja: a
    // `scratchclear_icon` 255,480,266,491 blobja 484 bájt = 11×11×4
    // BGRA), tehát az `infotext` a 442. sorig tart, az első tálca-sor a
    // 449. — közte 443…448, azaz HAT pont.
    //
    // ⚠️ VISSZAVONT ELTÉRÉS: a #1420 óta a csík nálunk 20 képpont volt,
    // „szándékos és dokumentált eltérés (olvashatóság,
    // `design-guide.md`)" — és épp ettől ÉRTEK a gombok a kék csíkhoz,
    // amit a tulajdonos élesben jelentett. A mért felosztásban a
    // különbség nem az olvashatóságé, hanem az 5 pontos TÉRKÖZÉ: a 20-as
    // csík felette azt is felette elnyelte. A mérés felülírja a saját
    // döntésünket.
    TrayInfoBar { trayRoot: tray; trayController: tray.ctl }

    Rectangle {
        id: trayMainBar
        objectName: "trayMainBar"
        // #422: jobbklikk a képtálcán — a Picasa `Tray` menüosztálya
        TapHandler {
            objectName: "trayContextMenuHandler"
            acceptedButtons: Qt.RightButton
            gesturePolicy: TapHandler.ReleaseWithinBounds
            onSingleTapped: trayContextMenu.popup()
        }
        TrayContextMenu {
            id: trayContextMenu
            // #455: a `Tray` helyi menü két parancsa a TÁLCÁRA hat, nem a
            // rács kijelölésére. Korábban a „megtartás" a horgony-képre
            // SZŰKÍTETTE a kijelölést, az „eltávolítás" pedig kivette
            // belőle — a `Tray::ID_PICTURE_HOLDINPICTURETRAY` belső neve
            // („tartsd a képtálcán") és a spec 3. szakasza szerint viszont
            // ez a tálca rögzítése, illetve a tálcáról való levétel.
            onKeepSelectionRequested: {
                if (tray.ctl && typeof tray.ctl.holdRows === "function")
                    tray.ctl.holdRows(tray.selectedIndexesOrEmpty)
            }
            // #2039: ha a TÁLCÁN van kijelölés, arra hat — az eredetiben a
            // tálca saját `CSelectionNode`-ja dönt, nem a rácsé. Ha a
            // tálcán nincs kijelölve semmi, marad a régi út (a rács
            // kijelöléséből vesz ki), hogy a parancs ne legyen néma.
            onRemoveSelectionRequested: {
                if (!tray.ctl) return
                if (tray.trayHasSelection
                    && typeof tray.ctl.removeTraySelected === "function") {
                    tray.ctl.removeTraySelected()
                } else if (typeof tray.ctl.removeHeldRows === "function") {
                    tray.ctl.removeHeldRows(tray.selectedIndexesOrEmpty)
                }
            }
            // #1917: az öt ÖRÖKÖLT tétel — más névterekből, de ugyanarra a
            // kijelölésre hat, mint a rács helyi menüjének párja. A jelzést
            // a gyökér adja tovább a `Main.qml`-nek, ahol a vezérlők élnek.
            onViewAndEditRequested: tray.viewAndEditRequested()
            onRotateRightRequested: tray.trayRotateRightRequested()
            onRotateLeftRequested: tray.trayRotateLeftRequested()
            onLocateRequested: tray.trayLocateRequested()
            onPropertiesRequested: tray.trayPropertiesRequested()
        }
        // #1914: 14 (infó-csík) + 91 = 105 — a `publishbottom` = −105.
        width: parent.width; height: 91
        color: Theme.trayBg

        // ---------------------------------------------------------------
        // #1420: a sáv MÉRT szerkezeti állandói (`thumbui.tre`)
        // ---------------------------------------------------------------
        //: az osztópont: a sáv öt eleménél ismétlődő `.365` szorzó
        readonly property real splitRatio: 0.365
        //: az osztópont képpontban (kerekítve, hogy a doboz-szélek élesek
        //: maradjanak) — a mérő őr ezt olvassa vissza
        readonly property real splitX: Math.round(width * splitRatio)
        //: `outputs` / `separator` jobb margója: `XConstraint 1, 1, -10`
        readonly property int rightMargin: 10
        //: `outputs`: `XConstraint 0, .365, 140` — a zöld gomb helye után
        readonly property int outputsOffset: 140
        //: #1345/#1504: egy kimeneti gomb OSZTÁSKÖZE. A `docbounds`
        //: cella-grafika 59 × 40, de a lépés a gomb saját doboza: **55** —
        //: az eredeti elrendezője a gyerek elrendezés utáni befoglalójából
        //: számol (`0x0059883e`–`0x00598863`), és a #1420 a kirajzolt
        //: képernyőképen is 55-öt mért. Ezért nincs hézag a gombok között.
        readonly property int actionCellWidth: 55
        // #1672: hat MINDIG látszó cella (nyomtatás, e-mail, exportálás,
        // Hello, kollázs, film) + két KIVEZETETT (Rendelés, Blogger),
        // amelyek szűk ablakban elsőként esnek ki. A ki nem férő tételeket
        // a „További…" (`morebutton`) hozza elő — az a #2191 óta MEGVAN
        // (`trayMoreButton` lentebb), tehát a sor nem veszít el gombot.
        //
        // A kivezetett gombok a legjobb jelöltek a kiesésre: nem
        // kattinthatók, tehát semmit nem vesznek el a felhasználótól.
        readonly property int actionCellCount: 6
        //: hány cella fér ki, ha a kivezetettek is elférnek
        readonly property int retiredCellCount: 2
        readonly property bool retiredVisible:
            width >= windowWidthFor(actionCellCount + retiredCellCount + 2)
        //: a `splitX` kerekítése és a szegélyek fél képpontjai miatti
        //: ráhagyás — enélkül a küszöb pontosan a határon állna
        readonly property int roundingReserve: 4

        //: hány képpont széles ablak kell ahhoz, hogy az osztóponttól
        //: jobbra `cellak` darab cella elférjen. Levezetés: a jobb sáv
        //: szélessége `(1 − .365)·W − 10`, ebbe kell beleférnie a 140-es
        //: eltolásnak és a celláknak.
        function windowWidthFor(cellak) {
            return Math.ceil(
                (trayMainBar.rightMargin + trayMainBar.outputsOffset
                 + cellak * trayMainBar.actionCellWidth
                 + trayMainBar.roundingReserve)
                / (1 - trayMainBar.splitRatio))
        }

        // #1367 ÚJRAMÉRVE (#1420): a sáv szélesség-igénye. A #1345 óta
        // minden kimeneti gomb FIX 55 × 36 egy 59 × 40-es cellában, a zöld
        // gomb pedig (#1420) fix 141 × 35 — vagyis a sáv igénye TISZTA
        // GEOMETRIA lett: feliratszélesség NINCS benne.
        //
        // Ez érdemi javulás a korábbi, betűfüggő becsléshez képest: a
        // #1367 kommentje azt rögzítette, hogy a régi érték a fejlesztői
        // gépen 850, a CI ubuntu-futóján 860 volt, és ezért kellett rá egy
        // 900-as ráhagyásos padló. Most a szám levezethető, és az őr
        // (`test_also_sav_elrendezes_1420.py`) ÉLŐBEN visszaméri, hogy a
        // minimumra állított ablakban tényleg nem lóg ki semmi — ha egy
        // betűfüggő elem (a − / + jelek) mégis megnőne, ott bukik el.
        //: #2305: a FELSŐ sor igénye. A sorrendcsere (csúszka -> négy
        //: kapcsoló) után a felső sor lett a szűk keresztmetszet: a
        //: kapcsolók 240 pontja a csúszka MÖGÜL a csúszka ELÉ került, és a
        //: csillag/forgatás csoport belelógott a csúszkába a 800 pontos
        //: minimumon (a #1367 őre ezt el is kapta).
        //:
        //: A csúszka sora a #3602 óta betűfüggetlen; a mért szélességet a
        //: viewer-sorral közös `max()` miatt használjuk. Hurok nincs: egyik
        //: csoport szélessége sem függ az ablakétól.
        //:
        //: #3602: a `trayZoomGroup` ↔ `trayMetadataGroup` rés MÉRT 20 (nem
        //: 12), és a `trayMetadataGroup` jobb széle `W − 15` — 5 képponttal
        //: BELJEBB, mint a `trayTopRow` (`W − rightMargin`) szélé. Az 5
        //: képpontos maradék hely ezért itt is szerepel, különben a
        //: minimumra állított ablakban a kapcsolók 5 képponttal kilógnának.
        readonly property real felsoSorIgenye: Math.ceil(
            (trayMainBar.rightMargin
             + trayRightPane.starGroupWidth + 12
             + trayRightPane.zoomGroupWidth + 20
             + trayRightPane.metadataGroupWidth + 5
             + trayMainBar.roundingReserve)
            / (1 - trayMainBar.splitRatio))
        readonly property real requiredWidth: Math.max(
            windowWidthFor(actionCellCount), felsoSorIgenye)
        // #1345 ÚJRAMÉRVE (#1420): a két csoportelválasztó két TELJES
        // cellát tesz a sorba; a küszöb az a szélesség, ahol ez a többlet
        // is elfér. A korábbi `compactBudget = 1120` a RÉGI, egysoros
        // elrendezésre volt mérve (a bő sáv igénye 1221, ebből a Feltöltés
        // felirata 133) — az a szám az új sávban értelmét vesztette, mert
        // a felirat többé nem szélesíti a sávot.
        readonly property real separatorThreshold:
            windowWidthFor(actionCellCount + 2)
        readonly property bool separatorsVisible: width >= separatorThreshold
        // A `compact` mostantól EGYETLEN dolgot jelent: a sáv szűk ahhoz,
        // hogy a két csoportelválasztó is elférjen. Minden más elem FIX
        // méretű lett (#1345 gombcellák, #1420 zöld gomb és csúszka), ezért
        // nincs több zsugorodó tétel — és nincs több betűfüggő küszöb sem.
        //
        // ⚠️ A csúszka szélessége SZÁNDÉKOSAN nem függ ettől: amíg függött,
        // a jobb felső sarokhoz zárt csoport szélessége a küszöb átlépésekor
        // egy képfrissítésnyi időre elavult maradt, és a csúszka kilógott a
        // sávból (a #1420 szigorított kilógás-őre fogta meg). A `.tre`
        // amúgy is FIX 127 × 27-es `scalecontainer`-t ad.
        readonly property real compactThreshold: separatorThreshold
        readonly property bool compact: width < compactThreshold

        Rectangle {
            width: parent.width; height: 1
            color: Theme.trayBorder
        }

        // ===============================================================
        // BAL OLDAL — a képtálca (`thumbui/scratchback`)
        //   XConstraint 0, 0, 5 · XConstraint 1, .365, -15 · m_offsetB
        //   81 képpont magas: a sáv tetejétől 20, aljától 4
        // ===============================================================
        TrayScratchPanel {
            trayRoot: tray
            trayController: tray.ctl
            trayBar: trayMainBar
        }



        // #455: a Picasa saját szövegű rákérdezése a TELJES ürítésre.
        //
        // ⚠️ JAVÍTVA (2026-08-27): itt korábban a MÁSIK párbeszéd szövege
        // állt („Would you like to clear your old held items from the
        // tray?" → „Clear Tray" / „Don't Clear"). A `picasa-keptalca.md` 4.
        // szakasza kimutatta, hogy **két, egymástól különböző** párbeszéd
        // van, és ez itt a másik:
        //
        //   4.1 TELJES ürítés — `IDS_CLEARTRAY`: „This will clear your
        //       entire tray. Are you sure you want to do this?", igen-gomb
        //       `IDS_CLEARTRAY_YES_BUTTON` = „Clear Tray" („Törlés a
        //       tálcáról"). **EZ tartozik a Törlés gombhoz.**
        //   4.2 a RÉGÓTA tartott elemek — `il_ClearFromTray`: nem a Törlés
        //       gomb megerősítése, hanem külön FELKÍNÁLT takarítás, aminek
        //       a küszöbe darabszám-növekedés (spec 13.). A szabálya kész
        //       és tesztelt a magban (`tray.needs_old_items_prompt`), de a
        //       megjelenés pillanata nincs kimérve, ezért nem építjük meg.
        //
        // Az általános `ConfirmDialog` Igen/Nem/Mégse feliratai nem
        // egyeznek az eredetivel, ezért itt egyedi, egyszerű dialógus.


        // ===============================================================
        // JOBB OLDAL — az osztóponttól a jobb szélig (`bcenterright`:
        //   `XConstraint 0, .365, 0`; `outputs`: `1, 1, -10`)
        // Két sor: fent a csillag/forgatás/nagyítás, lent — az y 50…52-es
        // elválasztó alatt — a zöld gomb és a műveletsor.
        // ===============================================================
        TrayRightPane {
            id: trayRightPane
            trayRoot: tray
            trayController: tray.ctl
            trayBar: trayMainBar
        }

        // #1939: a „Továbbiak…" KLIP-GYŰJTŐ MÓD üzenetsávja
        // (`thumbui/single_action_container`). A mód nálunk eddig is
        // működött, de a visszaút egy lebegő gomb volt a jobb felső
        // sarokban; az eredetiben egy teljes sáv ül az alsó
        // vezérlőkészletben, és ELTAKARJA a kimeneti gombsort.
        //
        // A méret KÉNYSZER-vezérelt (spec `getmore-klipgyujto-mod.md` 3.1):
        //   XConstraint 0, .365,  2   → bal  = az osztópont + 2
        //   XConstraint 1, 1,   -20   → jobb = a sáv jobb széle − 20
        //   YConstraint 0, 0,    45   → felül = a készlet tetejétől + 45
        //   YConstraint 1, 1,    -2   → alul  = a készlet aljától − 2
        //
        // ⚠️ A respack-ben tárolt 502 × 40 NEM normatív — az a
        // tervezővászon pillanatképe, a kényszerek felülírják. Ugyanaz a
        // tanulság, mint a #1934-nél az `infotext_clip`-nél.
        TraySingleActionBar { trayRoot: tray; trayBar: trayMainBar }
    }
}
