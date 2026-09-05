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
//     │ képtálca (81 px magas)   │ ★ ↺ ↻ … − nagyítás +            │
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
    // #32 (RÉSZLEGES kör): Nyomtatás/E-mail — a dialógusok (nyomtató-
    // választó, tárgy/szöveg-bekérés) a Main.qml-ben élnének, ugyanúgy,
    // mint a fenti kettőnél (a bekötés az integrátor lépése, ld.
    // print_controller.py/email_controller.py docstringje).
    signal printRequested()
    signal emailRequested()

    // a forgatás/csillag célsora — a Main rotateTargetRow()-ja is ezt kéri
    readonly property int starTargetRow: trayStar.targetRow

    // #305: null-őr — a controller a QML-engine leépítésekor átmenetileg
    // null lehet, miközben ezek a kötések utoljára kiértékelődnek.
    readonly property var ctl: controller

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

    readonly property var selectedIndexesOrEmpty:
        (tray.appWindow && tray.appWindow.selectedIndexes)
            ? tray.appWindow.selectedIndexes
            : []

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
    onSelectedIndexesOrEmptyChanged: tray.syncTraySelection()
    Component.onCompleted: tray.syncTraySelection()

    //: A tálca elemszáma (a rögzített ÉS a kijelölésből tükrözött együtt).
    //: Ez a KÖTÉSI FÜGGŐSÉG is: a `trayInfo()`/`isHeldAt()` függvényhívások
    //: önmagukban nem hoznak létre függőséget, a `heldCount` olvasása igen.
    readonly property int trayCount:
        (tray.ctl && tray.ctl.heldCount !== undefined) ? tray.ctl.heldCount : 0

    //: #455: a kék infó-sáv a TÁLCÁRÓL ír (`il_GetSelectionInfo`). A
    //: műveletsor a tálca tartalmán dolgozik, tehát a darabszámnak, a
    //: dátumtartománynak és az összméretnek is azt kell összesítenie —
    //: a más mappából tartott képekkel együtt, amiket a rács nem is mutat.
    readonly property string trayInfoText:
        (tray.trayCount > 0 && tray.ctl
         && typeof tray.ctl.trayInfo === "function")
            ? tray.ctl.trayInfo() : ""

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
    Rectangle {
        id: infoBar
        objectName: "trayInfoBar"
        width: parent.width; height: 14
        color: Theme.infoBar
        clip: true

        // SAJÁT FUNKCIÓ (#70): lassan végigvonuló fény-hullám, amíg a
        // PicasaPy a háttérben dolgozik (indexelés, thumbnail-batch). Az
        // eredetiben nincs ilyen vizuális visszajelzés — saját UX-
        // kiegészítés (lista: docs/decisions/vedett-sajat-funkciok.md).
        // XAnimator: a render-szálon fut (a főszálat/GIL-t nem érinti, ld.
        // #53), idle-ben running=false → 0 CPU/GPU. Nem polloz: a
        // controller.isWorking jelzés-alapú (busyChanged).
        Rectangle {
            id: busySweep
            objectName: "busySweep"
            // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
            // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
            visible: (tray.ctl && tray.ctl.isWorking !== undefined) ? tray.ctl.isWorking : false
            width: Math.max(80, infoBar.width / 5)
            height: infoBar.height
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "transparent" }
                GradientStop { position: 0.5; color: "#59ffffff" }
                GradientStop { position: 1.0; color: "transparent" }
            }
            XAnimator on x {
                running: busySweep.visible
                loops: Animation.Infinite
                from: -busySweep.width
                to: infoBar.width
                duration: 1800
            }
        }
        Text {
            objectName: "trayInfoText"
            // #1934 (spec `kek-info-sav.md` 6.): a szövegnek SAJÁT clipje
            // van — `thumbui/clip: infotext_clip`, kényszere
            // `XConstraint 0, 0, 20` / `1, 1, -20` a sávon. A kék HÁTTÉR
            // ettől függetlenül teljes szélességű marad (mérve: a csík
            // sorában a kék x 0…1919, nem-kék képpont 0).
            //
            // A `respack.yt` ugyanerre az elemre `x 183…664`-et tárol, de
            // az MEGDŐLT: az a téglalap nem szimmetrikus (balra 183,
            // jobbra 136, közepe 423,5 a 800-as vásznon), márpedig a
            // szöveg közepe mind a 20 felvételen az ablak közepén áll
            // (|Δ| ≤ 0,5 képpont). A tárolt téglalap a tervezővászon
            // szerzői értéke; ahol az elem kényszert kap, az elrendező
            // felülírja.
            //
            // `clip`, nem `elide`: az eredeti elem CLIP, a levágás helye
            // mért, a „…" hárompont viszont a MI döntésünk lenne — arra
            // nincs bizonyítékunk, ezért nem vezetjük be.
            x: 20
            width: Math.max(0, parent.width - 40)
            anchors.verticalCenter: parent.verticalCenter
            horizontalAlignment: Text.AlignHCenter
            clip: true
            // #718: null-őr — a `ctl` mellett az `appWindow` is
            // átmenetileg null lehet az engine-leépítés utolsó kiértékelésekor.
            //
            // #1189: az eredeti `GetSelectionInfo` (`0x0056fbc0`) a
            // KIJELÖLÉSRŐL ír. Nálunk a „minden más" ág a mappa egészének
            // összesítését (`statusText`) mutatta, ezért több kijelölt
            // képnél a mappa adatai maradtak a sávban.
            //
            // #1168 (spec 16.3): a kollázs rajzolása alatt a FŐABLAK is
            // jelez — `CThumbUI::CreateCollageWait` (`0x007f7120`). A
            // várakozás MINDEN mást megelőz: a kollázs lapja közben be is
            // zárulhat, és a felhasználó máshol nézelődik, miközben a munka
            // fut — az eredeti éppen ezért a KÖNYVTÁRNÉZETBEN mondja ki.
            //
            // #455: a nézőn kívül a TÁLCA az elsődleges forrás — a tálca a
            // kijelölés tükre, plusz a máshonnan MEGTARTOTT képek, amiket a
            // rács sorindexei nem is tudnak leírni. Üres tálcánál minden
            // marad a mai ágakon (a `trayInfoText` ilyenkor üres).
            text: (!tray.ctl || !tray.appWindow) ? ""
                  : (tray.ctl.collageRendering === true ? tray.collageWaitText
                  : (tray.appWindow.viewerOpen
                  ? tray.ctl.viewerInfo(tray.viewerIndex)
                  : (tray.trayInfoText !== "" ? tray.trayInfoText
                  : (tray.appWindow.selectedIndexes.length === 1
                     ? tray.ctl.photoInfo(tray.appWindow.selectedIndex)
                     : (tray.appWindow.selectedIndexes.length > 1
                        && typeof tray.ctl.selectionInfo === "function"
                        ? tray.ctl.selectionInfo(tray.appWindow.selectedIndexes)
                        : tray.ctl.statusText)))))
            color: Theme.infoBarText
            font.pixelSize: Theme.fontSize
            font.bold: true
        }
    }

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
        //: #1345: egy kimeneti gomb cellája (`outputlayout/docbounds`)
        readonly property int actionCellWidth: 59
        //: a MEGLÉVŐ hat kimeneti gomb (nyomtatás, e-mail, exportálás,
        //: megosztás, kollázs, film) — a hiányzó `shop`/`blog`/`morebutton`
        //: nélkül (`docs/specs/ui-lefedettseg.md`)
        // #1672: hat MINDIG látszó cella (nyomtatás, e-mail, exportálás,
        // Hello, kollázs, film) + két KIVEZETETT (Rendelés, Blogger),
        // amelyek szűk ablakban elsőként esnek ki. Az eredetiben erre a
        // `morebutton`/`overflow` való — az nálunk még nincs meg (#1672).
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
        //: A tényleges szélességeket használjuk, nem beégetett számot: a
        //: csúszka − / + jelei BETŰFÜGGŐK (#1420), tehát a platformonként
        //: eltérő igényt csak a mért érték adja vissza. Hurok nincs: egyik
        //: csoport szélessége sem függ az ablakétól.
        readonly property real felsoSorIgenye: Math.ceil(
            (trayMainBar.rightMargin
             + trayStarGroup.width + 12
             + trayZoomGroup.width + 12
             + trayMetadataGroup.width
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
        Rectangle {
            id: trayScratchBack
            objectName: "trayScratchBack"
            x: 5
            //: #1913: MÉRT térköz a kék csík alatt — `infotext` y 443-ig
            //: (nyílt), a `scratchback` y 449-től ⇒ HAT pont. (A #1914 itt
            //: ötöt írt, mert a 448-tól induló nagyító-/metaadat-csoportot
            //: mérte, nem a tálcát.)
            y: 6
            width: Math.max(0, trayMainBar.splitX - 15 - x)
            height: 81
            color: Theme.trayPanelBg
            border.width: 1
            border.color: Theme.trayBorder
            radius: 2
            clip: true

            //: #455: a tálca elemszáma (a gyökér `trayCount`-jából — egy
            //: helyen olvassuk a vezérlőt, hogy a null-őr se duplázódjon)
            readonly property int heldCount: tray.trayCount

            // a bélyegképsor (`thumbui/scratch`): 5 képpont belső margó,
            // JOBBRÓL 50 képpont marad szabadon a három gombnak
            // #1904: a doboz magassága FIX, a bélyegképek ZSUGORODNAK és
            // TÖBB SORBA tördelődnek — nem tűnnek el némán.
            //
            // Húsz referencia-felvétel ugyanabban az 1920×1080-as
            // ablakban. A doboz külső mérete közben változatlan: nem
            // görgetősáv és nem levágás.
            //
            // Nálunk eddig egyetlen `Row` állt itt `clip: true`-val: a be
            // nem férő képek EGYSZERŰEN ELTŰNTEK. A kék infó-csík közben
            // a teljes darabszámot írta — a felület önmagának mondott
            // ellent.
            //
            // ## A MÉRT sorozat (spec `picasa-keptalca.md` 15.2)
            //
            //   kép | sorok | tartalom | osztásköz
            //     3 |   1   |   54     |  57,00
            //    12 |   1   |   48     |  51,00
            //    15 |   1   |   38     |  39,93
            //    19 |   1   |   29     |  31,00
            //    27 |   2   |   28     |  29,94
            //    49 |   2   |   22     |  24,00
            //    67 |   3   |  18–19   |  21,00
            //    82 |   3   |  18–19   |  21,00
            //
            // ⚠️ #1916 HELYESBÍTÉS: egy korábbi változat itt „h(2)=34 ·
            // h(3)=22 ← a mért érték"-et állított. **Ez téves volt** — a
            // 22 a KÉTSOROS, 49 képes eset tartalma, a háromsoros eseté
            // 18–19 (21-es osztásközzel). Mért értéknek nevezni valamit,
            // ami nem az, rosszabb, mint nem tudni.
            //
            // ⛔ A cellaméret pontos KÉPLETE: **NINCS MEG.** A spec 15.4
            // kimerítő keresést közöl a kézenfekvő modellre — ±1 tűréssel
            // 912 paraméterkészlet megy át a tizenhat megfigyelésen,
            // pontos egyezéssel NULLA. A tizenhat megfigyelés tehát nem
            // határozza meg a konstansokat, és a kézenfekvő modell rossz.
            //
            // Amit itt számolunk, az ezért NEM az eredeti képlete, hanem
            // egy VISELKEDÉS: fix doboz, semmi nem lóg ki, több sor nagyobb
            // darabszámnál — a felső korlát a mért 54. Az őr is ezt
            // rögzíti, nem képpontszámot.
            Flow {
                id: trayScratchStrip
                objectName: "trayScratchStrip"
                x: 5
                y: 5
                width: Math.max(0, parent.width - 5 - 50)
                height: parent.height - 10
                spacing: 2
                clip: true

                //: MÉRT felső korlát: egy sornál a tartalom 54 képpont,
                //: 57 képpontos osztásközzel (spec `picasa-keptalca.md`
                //: 15.2, tizenhat felvétel; a kék csík darabszám-felirata
                //: kalibrálja).
                readonly property int maxThumbHeight: 54
                //: ez alatt a bélyegkép már nem mond semmit — inkább vágunk
                readonly property int minThumbHeight: 12
                //: A cella NÉGYZET — mérve (spec 15.1). A `…214634.jpg`
                //: csíkfelirata a forrás méretét is kiírja (816×1456,
                //: álló, 0,560), a tálcabeli bélyegkép mégis 54×54; a
                //: normalizált keresztkorreláció háromból háromszor a
                //: KÖZÉPRE VÁGÁST hozza ki (+0,587 / +0,900 / +0,902) a
                //: nyújtás és az aránytartó illesztés ellenében. Ezért
                //: nincs többé „névleges oldalarány" becslés: a szélesség
                //: a magassággal egyenlő.

                readonly property int thumbCount:
                    trayScratchBack.heldCount > 0
                        ? trayScratchBack.heldCount
                        : tray.selectedIndexesOrEmpty.length

                function sorMagassag(sorok) {
                    return Math.floor(
                        (height - (sorok - 1) * spacing) / sorok)
                }

                readonly property int thumbHeight: {
                    var n = thumbCount
                    var maxSorok = Math.max(
                        1, Math.floor((height + spacing)
                                      / (minThumbHeight + spacing)))
                    var h = maxThumbHeight
                    for (var sorok = 1; sorok <= maxSorok; ++sorok) {
                        h = Math.min(maxThumbHeight, sorMagassag(sorok))
                        var soronkent = Math.max(
                            1, Math.floor((width + spacing)
                                          / (h + spacing)))
                        if (n <= soronkent * sorok)
                            return h
                    }
                    return Math.max(minThumbHeight, h)
                }
                Repeater {
                    objectName: "trayPreviewRepeater"
                    // #718: null-őr — az appWindow (a Main.qml
                    // `window`-ja) az engine-leépítés közben átmenetileg
                    // null lehet, miközben ez a kötés utoljára
                    // kiértékelődik (ld. a fenti `ctl` docstringje).
                    // NEM elég csak az appWindow-t vizsgálni: a
                    // leépítés egy köztes állapotában az ablak MÁR
                    // létezik, a `selectedIndexes` viszont még
                    // `undefined` — ezt a `.length` olvasása
                    // TypeError-ral bünteti.
                    model: trayScratchBack.heldCount > 0
                        ? trayScratchBack.heldCount
                        : tray.selectedIndexesOrEmpty.length
                    delegate: Image {
                        id: trayThumb
                        objectName: "trayPreviewThumb"
                        required property int index

                        // 20 × 20-as rács a 81 képpontos dobozban holt
                        // helyet hagyott volna.
                        height: trayScratchStrip.thumbHeight
                        // #1914 (spec 15.1): a cella NÉGYZET, a fotó
                        // középre VÁGVA — nem aránytartó illesztés.
                        width: height
                        source: !tray.ctl || !tray.appWindow ? ""
                            : trayScratchBack.heldCount > 0
                              ? tray.ctl.heldThumbUrlAt(index)
                              : tray.ctl.photos.thumbUrlAt(
                                    Number(tray.appWindow.selectedIndexes[index]))
                        //: `PreserveAspectCrop` = a rövidebbik oldalra
                        //: illeszt, a hosszabbikat levágja — a `clip`
                        //: nélkül a levágott rész kilógna a cellából.
                        fillMode: Image.PreserveAspectCrop
                        clip: true
                        asynchronous: true

                        // #2039: a tálcának SAJÁT kijelölése van — az
                        // eredetiben ugyanolyan `CSelectionNode`, mint a
                        // rácsé (`picasa-keptalca.md` 13.). A kattintás a
                        // VEZÉRLŐN megy át, a módosítókkal együtt.
                        readonly property bool trayCellSelected:
                            tray.trayIndexSelected(trayThumb.index)

                        TapHandler {
                            objectName: "trayThumbTap"
                            acceptedButtons: Qt.LeftButton
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onSingleTapped: function (eventPoint, button) {
                                if (!tray.ctl
                                    || typeof tray.ctl.selectTrayIndex !== "function")
                                    return
                                tray.ctl.selectTrayIndex(
                                    trayThumb.index,
                                    (point.modifiers & Qt.ControlModifier) !== 0,
                                    (point.modifiers & Qt.ShiftModifier) !== 0)
                            }
                        }

                        // A kijelölés KÉTVONALAS kerete — ugyanaz a réteg,
                        // mint a rácsban (`ThumbDelegate.qml` 89–108.):
                        // kívül `Theme.thumbSelection` (#009EFF), belül a
                        // kártya színe. Nem új stílus, hanem a meglévő
                        // újrahasználása (`constants.ui` thumbsel_color1/2).
                        Rectangle {
                            objectName: "trayThumbSelectionOuter"
                            visible: trayThumb.trayCellSelected
                            z: -1
                            anchors.centerIn: parent
                            readonly property int outerWidth: 2
                            readonly property int innerWidth: 1
                            width: parent.width + 2 * (outerWidth + innerWidth)
                            height: parent.height + 2 * (outerWidth + innerWidth)
                            color: Theme.thumbSelection
                        }
                        Rectangle {
                            objectName: "trayThumbSelectionInner"
                            visible: trayThumb.trayCellSelected
                            z: -1
                            anchors.centerIn: parent
                            width: parent.width + 2
                            height: parent.height + 2
                            color: Theme.thumbCard
                        }
                        // #1420: az eredeti tálcáján a bélyegképek a doboz
                        // TELJES belső magasságát kitöltik (a képernyőképen
                        // ~70 képpont), oldalarányt tartva — a korábbi

                        // #1918: a MEGTARTOTT kép jelvénye a bélyegképen.
                        //
                        // Az eredetiben a `thumbui/#holdadorner` — az
                        // adorner-CSALÁD első eleme (a `0x007145c0`-on
                        // épülő gyorsítótár +0x00 eltolása, `0x00cad36c`),
                        // ugyanabból a családból, mint a csillag
                        // (`adorners/star`), a geocímke vagy az arcok
                        // jelvénye. Mérete a respack-rétegfejléc szerint
                        // 10×10.
                        //
                        // Nálunk a megtartás eddig CSAK SZÁMKÉNT létezett
                        // (`heldCount`); a képen semmi nem jelezte. A
                        // rács-cellán már megvolt (#455, `holdMark`) — a
                        // tálca bélyegképein nem.
                        //
                        // ⚠️ A jelvény a MEGLÉVŐ `hold-pin.svg`, nem a
                        // respackből kicsomagolt PNG: a projekt egyetlen
                        // kicsomagolt Picasa-képet sem szállít, és a
                        // rács-cella ugyanezt a rajzot használja — így a
                        // két hely ugyanazt jelenti ugyanazzal a jellel.
                        Image {
                            objectName: "trayHoldMark"
                            //: #1572-minta: a `!== undefined` a hiányzó
                            //: TULAJDONSÁGRA véd (a próbák stub-vezérlőjén
                            //: nincs rajta).
                            //: ⚠️ A `heldCount` olvasása NEM felesleges: a
                            //: `heldAtTrayIndex(...)` puszta FÜGGVÉNYHÍVÁS,
                            //: amire a QML nem tud kötést építeni. A
                            //: `heldCount` a `heldChanged` jelzésre notifyol,
                            //: és a „megtartás" épp ezt sütteti el — enélkül
                            //: a jelvény csak a következő elrendezéskor
                            //: jelenne meg. (Ugyanaz a minta, mint a
                            //: `photos.revision` a rácsban.)
                            visible: (tray.ctl
                                      && tray.ctl.heldAtTrayIndex !== undefined
                                      && tray.ctl.heldCount !== undefined
                                      && trayScratchBack.heldCount > 0)
                                     ? (tray.ctl.heldCount,
                                        tray.ctl.heldAtTrayIndex(parent.index))
                                     : false
                            source: "icons/hold-pin.svg"
                            width: 6; height: 10
                            sourceSize.width: 6; sourceSize.height: 10
                            anchors.left: parent.left
                            anchors.bottom: parent.bottom
                            anchors.margins: 2
                        }
                    }
                }
            }
            // `thumbui/scratchlabel` — „Kijelölés", `m_centerXY`: a doboz
            // KÖZEPÉN álló ÁLLANDÓ vízjel.
            //
            // #2179: az eredetiben ez NEM üres-állapot felirat. A tulajdonos
            // hat felvétele ugyanabban a mappában, növekvő elemszámmal: 1 és
            // 3 bélyegképnél a felirat LÁTSZIK, 11-nél eltakarva, 6-nál a
            // vége (`…lés`) KILÓG a képek jobb oldalán. Az utolsó dönti el a
            // rétegsorrendet is: a felirat bal része a képek ALATT van.
            // Ugyanezt mondja a `thumbui.tre` szülő-gyerek viszonya
            // (`scratchpadbase` — és rajta a `scratchlabel` — előbb
            // deklarálva, mint a `thumbui/scratch`).
            //
            // Ezért NINCS `visible` kötése, és `z: -1`-gyel a bélyegképsor
            // ALÁ kerül. (A `z` a deklarációs sorrend átrendezése helyett:
            // a felirat így a `scratchback` gyerekeként marad, ahogy az
            // eredetiben is a `scratchpadbase`-é.)
            Text {
                objectName: "trayScratchLabel"
                z: -1
                anchors.centerIn: parent
                text: qsTr("Selection")
                // #2179: a respackből MÉRVE — `thumbui/scratchlabel`
                // (13,480)–(218,499), szín `#C3C3C3`. A `Theme`
                // `placeholderText`-je (`#8f8b83`) sötétebb ennél, és más
                // helyeken is használatban van, ezért itt a mért érték áll.
                color: "#C3C3C3"
                // `m_displayfont14` = 14 pt (`docs/specs/picasa-hisztogram.md`,
                // ugyanaz a betűcsalád), és a felirat mért magassága 19
                // képpont — a kettő egybevág.
                font.pixelSize: 14
            }

            // #455/#1420: a Picasa 3-gombos OSZLOPA a bélyegképsor jobbján
            // fenntartott 50 képpontban (`scratchhold` 34 × 22,
            // `scratchclear` 34 × 20, `addtobuttcon` 34 × 22 — mind
            // `m_offsetRT` a `scratchback`-en). A gombokon az eredetiben
            // NINCS felirat: a `thumbui_text.tre`-ben mindhárom `Label`
            // sora ki van kommentelve, csak a `Tooltip` él.
            PicasaButton {
                id: trayHoldBtn
                objectName: "trayHoldButton"
                x: parent.width - 5 - width
                y: 5
                width: 34
                height: 22
                // #718: null-őr — ld. a fenti `ctl` docstringje.
                enabled: tray.appWindow
                         ? (!tray.appWindow.viewerOpen
                            && tray.appWindow.selectedIndexes.length > 0)
                         : false
                onClicked: tray.ctl && tray.appWindow && tray.ctl.holdRows(
                    tray.appWindow.selectedIndexes)
                ToolTip.text: qsTr("Hold selected items")
                ToolTip.visible: trayHoldBtn.hovered
                ToolTip.delay: 500
                contentItem: Image {
                    objectName: "trayHoldIcon"
                    // #1188: a `Control` a contentItem geometriáját maga
                    // állítja be (az `anchors.centerIn` ezért hatástalan
                    // volt), a `fillMode` alapja pedig `Image.Stretch` —
                    // a négyzetes SVG így a gomb tartalom-dobozára feszült.
                    fillMode: Image.PreserveAspectFit
                    source: "icons/hold-pin.svg"
                    sourceSize: Qt.size(28, 28)
                    opacity: trayHoldBtn.enabled ? 1.0 : 0.5
                }
            }
            PicasaButton {
                id: trayClearBtn
                objectName: "trayClearButton"
                x: parent.width - 5 - width
                y: 27
                width: 34
                height: 20
                enabled: trayScratchBack.heldCount > 0
                onClicked: trayClearConfirm.open()
                ToolTip.text: qsTr("Clear items from the selection")
                ToolTip.visible: trayClearBtn.hovered
                ToolTip.delay: 500
                contentItem: Image {
                    objectName: "trayClearIcon"
                    // #1188: ld. a `trayHoldBtn` indoklását fentebb.
                    fillMode: Image.PreserveAspectFit
                    source: "icons/tray-clear.svg"
                    sourceSize: Qt.size(28, 28)
                    opacity: trayClearBtn.enabled ? 1.0 : 0.5
                }
            }
            // #455: „Add to" — a TÁLCA TARTALMA egyenesen albumhoz adható.
            // Az eredetiben felfelé nyíló menüből választható az album; itt
            // a meglévő album-listát (`controller.albums`) kínáljuk fel,
            // ugyanabban a sorrendben, mint a kép-kontextusmenü.
            //
            // #1420: a gomb IKON-ONLY lett, mert az eredeti tálcájában a
            // 34 képpontos oszlopban ül, és ott sincs felirata — a jelentést
            // a buboréksúgó hordozza (`thumbui_text.tre`: *Add selected
            // items to an Album*).
            PicasaButton {
                id: trayAddToBtn
                objectName: "trayAddToButton"
                x: parent.width - 5 - width
                y: 54
                width: 34
                height: 22
                // #718: null-őr — `tray.ctl` a leépítés végén lehet igaz úgy
                // is, hogy az `albums` lista már nem érhető el (undefined).
                // A `!!` a láncolt `&&` esetleges `undefined` eredményét
                // valódi bool-lá kényszeríti (a `bool`-property-hez az
                // `undefined` hozzárendelése önmagában is szkripthiba).
                enabled: !!(trayScratchBack.heldCount > 0
                         && tray.ctl && tray.ctl.albums
                         && tray.ctl.albums.length > 0)
                onClicked: trayAddToMenu.popup()
                ToolTip.text: qsTr("Add selected items to an Album")
                ToolTip.visible: trayAddToBtn.hovered
                ToolTip.delay: 500
                contentItem: Image {
                    objectName: "trayAddToIcon"
                    fillMode: Image.PreserveAspectFit
                    source: "icons/tray-addto.svg"
                    sourceSize: Qt.size(30, 20)
                    opacity: trayAddToBtn.enabled ? 1.0 : 0.5
                }
            }
        }

        PicasaMenu {
            id: trayAddToMenu
            objectName: "trayAddToMenu"
            Repeater {
                model: tray.ctl ? tray.ctl.albums : []
                delegate: MenuItem {
                    required property var modelData
                    text: modelData.name
                    onTriggered: tray.ctl.addHeldToAlbum(modelData.token)
                }
            }
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
        Dialog {
            id: trayClearConfirm
            objectName: "trayClearConfirmDialog"
            modal: true
            anchors.centerIn: parent ? Overlay.overlay : undefined
            title: qsTr("Clear Tray")
            Text {
                objectName: "trayClearConfirmText"
                Layout.preferredWidth: 280
                text: qsTr(
                    "This will clear your entire tray."
                    + " Are you sure you want to do this?")
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            footer: RowLayout {
                spacing: 8
                Item { Layout.fillWidth: true }
                //: A megerősítő gomb hivatalos magyarja MÁS, mint a
                //: párbeszéd címéé: `IDS_CLEARTRAY_YES_BUTTON` = „Törlés a
                //: tálcáról". Ugyanaz a forrásszöveg, más fordítás — ezért
                //: kap megkülönböztető második paramétert.
                PicasaButton {
                    objectName: "trayClearConfirmYesButton"
                    text: qsTr("Clear Tray", "IDS_CLEARTRAY_YES_BUTTON")
                    accent: Theme.picasaGreen
                    onClicked: {
                        tray.ctl && tray.ctl.clearHeld()
                        trayClearConfirm.close()
                    }
                }
                //: A visszalépő gomb felirata NEM az eredeti „Don't Clear" —
                //: az a 4.2 párbeszédhez tartozik (ld. fent). A teljes
                //: ürítés kérdésének nemleges gombja nincs kimérve, ezért a
                //: program általános „Mégse"-jét használjuk.
                PicasaButton {
                    objectName: "trayClearConfirmNoButton"
                    text: qsTr("Cancel")
                    onClicked: trayClearConfirm.close()
                }
                Item { width: 8 }
            }
        }

        // ===============================================================
        // JOBB OLDAL — az osztóponttól a jobb szélig (`bcenterright`:
        //   `XConstraint 0, .365, 0`; `outputs`: `1, 1, -10`)
        // Két sor: fent a csillag/forgatás/nagyítás, lent — az y 50…52-es
        // elválasztó alatt — a zöld gomb és a műveletsor.
        // ===============================================================
        Item {
            id: trayRightPane
            objectName: "trayRightPane"
            x: trayMainBar.splitX
            //: #1913: ugyanaz a 6 pontos MÉRT térköz, mint a
            //: `scratchback`-en — a csillag és a két forgatás
            //: (`startoggle`, `rotateleft`, `rotateright`) is y **449**-től
            //: indul, nem 448-tól.
            y: 6
            width: Math.max(
                0, trayMainBar.width - trayMainBar.rightMargin - x)
            height: parent.height - y

            // --- felső sor (a sáv tetejétől 449…471 → itt 0…22) ---
            Item {
                id: trayTopRow
                objectName: "trayTopRow"
                width: parent.width
                height: 22

                // `startoggle` · `rotateleft` · `rotateright`: 36 × 22
                // egyenként, a csillag után 5 képpont hézag, a két forgatás
                // 37 képpontos osztásközzel (mérve: 697…732 · 738…773 ·
                // 775…810 egy 1918 képpontos ablakban).
                Row {
                    id: trayStarGroup
                    objectName: "trayStarGroup"
                    x: 0
                    height: parent.height
                    spacing: 1

                    PicasaButton {
                        id: trayStar
                        //: #1224: SAJÁT név a gombnak. Eddig a tesztek a
                        //: feliratának (`trayStarLabel`) a SZÜLŐJÉN át
                        //: találták meg — a #1438 tesztje ezt panaszolta is
                        //: („a gombnak magának nincs objectName-je"). Amint
                        //: a felirat képre cserélődött és konténerbe került,
                        //: a szülő-lánc eltört. Egy név stabilabb, mint egy
                        //: hierarchia-feltevés.
                        objectName: "trayStarButton"
                        width: 36
                        height: 22
                        anchors.verticalCenter: parent.verticalCenter
                        //: #1929: `thumbui/startoggle` — az EREDETI súgója,
                        //: szó szerint (`referencia/ui-leltar.csv`). Eddig
                        //: nem volt súgója.
                        ToolTip.text: qsTr("Add/Remove Star")
                        ToolTip.visible: trayMoreBtn.hovered
                        ToolTip.delay: 500
                        // #718: null-őr — ld. a fenti `ctl` docstringje;
                        // appWindow hiányában a célsor -1 (nincs cél).
                        readonly property int targetRow: tray.appWindow
                            ? (tray.appWindow.viewerOpen
                               ? tray.viewerIndex : tray.appWindow.selectedIndex)
                            : -1
                        readonly property bool multi: tray.appWindow
                            ? (!tray.appWindow.viewerOpen
                               && tray.appWindow.selectedIndexes.length > 1)
                            : false
                        enabled: tray.appWindow
                                 ? (tray.appWindow.viewerOpen
                                    || tray.appWindow.selectedIndex >= 0)
                                 : false
                        onClicked: multi
                                   ? controller.toggleStarMany(
                                         tray.appWindow.selectedIndexes)
                                   : controller.toggleStar(targetRow)
                        //: #1224: KÉP, nem betűjel. A `Text`-es `★` alakja a
                        //: rendszer betűkészletétől függött (Windowson más
                        //: glifa, mint Linuxon) — a tulajdonos ezt is
                        //: „eltorzultnak" látta (#1188). Az eredeti
                        //: raszterikont rajzol (`thumbui/startoggle_icon0`,
                        //: MÉRT 17 × 17 a #1914 réteg-leltárából); a RAJZ a
                        //: sajátunk.
                        //:
                        //: ⚠️ KÉT SVG, nem egy színezett: a QML `Image`
                        //: shader nélkül nem színezhető, a `QtQuick.Effects`
                        //: pedig szándékosan nincs a projektben.
                        contentItem: Item {
                        Image {
                            objectName: "trayStarIcon"
                            source: (tray.ctl
                                     ? (tray.ctl.photos.revision,
                                        tray.ctl.photos.starAt(trayStar.targetRow))
                                     : false)
                                    ? "icons/tray-star-on.svg"
                                    : "icons/tray-star.svg"
                            width: 17; height: 17
                            sourceSize.width: 17; sourceSize.height: 17
                            fillMode: Image.PreserveAspectFit
                            anchors.centerIn: parent
                        }
                        }
                    }
                    //: a csillag utáni 5 képpontos hézag (a `spacing` 1-ből
                    //: már megvan egy)
                    Item { width: 4; height: 1 }
                    PicasaButton {
                        id: trayRotateLeftBtn
                        objectName: "trayRotateLeft"
                        //: #1224: a felirat KIÜRÜL — a gomb tartalma kép
                        text: ""
                        width: 36
                        height: 22
                        anchors.verticalCenter: parent.verticalCenter
                        //: #1929: `thumbui/rotateleft` — az EREDETI súgója.
                        ToolTip.text: qsTr("Rotate counter-clockwise")
                        ToolTip.visible: hovered
                        ToolTip.delay: 500
                        // #103: csak-videó kijelölésnél tiltva (photos.revision:
                        // modell-frissüléskor újraértékelt kötés)
                        // #718: null-őr — az appWindow (`window`) az engine-
                        // leépítés közben átmenetileg null lehet.
                        enabled: (tray.ctl ? tray.ctl.photos.revision : 0,
                                  tray.appWindow
                                  ? ((tray.appWindow.viewerOpen
                                      || tray.appWindow.selectedIndex >= 0)
                                     && !tray.appWindow.rotateTargetsAllVideo())
                                  : false)
                        onClicked: trayStar.multi
                                   ? controller.rotateLeftMany(
                                         tray.appWindow.selectedIndexes)
                                   : controller.rotateLeft(trayStar.targetRow)
                        // #314: a PicasaButton alap-krómja nem témavezérelt —
                        // mindig világos bevel-gomb. Az alapértelmezett
                        // contentItem az `ink`-et használná, ami sötét témán
                        // kivilágosodik és eltűnne a világos gombháttéren.
                        //: #1224: KÉP, nem betűjel (`thumbui/rotateleft_icon`,
                        //: MÉRT 11 × 15). A letiltott állapotot `opacity`
                        //: jelzi — képre a `color` nem érvényes.
                        contentItem: Item {
                        Image {
                            objectName: "trayRotateLeftIcon"
                            source: "icons/tray-rotate-left.svg"
                            width: 11; height: 15
                            sourceSize.width: 11; sourceSize.height: 15
                            fillMode: Image.PreserveAspectFit
                            anchors.centerIn: parent
                            opacity: trayRotateLeftBtn.enabled ? 1.0 : 0.4
                        }
                        }
                    }
                    PicasaButton {
                        id: trayRotateRightBtn
                        objectName: "trayRotateRight"
                        //: #1224: a felirat KIÜRÜL — a gomb tartalma kép
                        text: ""
                        width: 36
                        height: 22
                        anchors.verticalCenter: parent.verticalCenter
                        //: #1929: `thumbui/rotateright` — az EREDETI súgója.
                        ToolTip.text: qsTr("Rotate clockwise")
                        ToolTip.visible: hovered
                        ToolTip.delay: 500
                        // #718: null-őr — ld. trayRotateLeftBtn indoklása.
                        enabled: (tray.ctl ? tray.ctl.photos.revision : 0,
                                  tray.appWindow
                                  ? ((tray.appWindow.viewerOpen
                                      || tray.appWindow.selectedIndex >= 0)
                                     && !tray.appWindow.rotateTargetsAllVideo())
                                  : false)
                        onClicked: trayStar.multi
                                   ? controller.rotateRightMany(
                                         tray.appWindow.selectedIndexes)
                                   : controller.rotateRight(trayStar.targetRow)
                        // #314: ld. trayRotateLeftBtn indoklása fentebb.
                        //: #1224: KÉP, nem betűjel (`thumbui/rotateright_icon`,
                        //: MÉRT 11 × 15) — a balra-forgatás párja.
                        contentItem: Item {
                        Image {
                            objectName: "trayRotateRightIcon"
                            source: "icons/tray-rotate-right.svg"
                            width: 11; height: 15
                            sourceSize.width: 11; sourceSize.height: 15
                            fillMode: Image.PreserveAspectFit
                            anchors.centerIn: parent
                            opacity: trayRotateRightBtn.enabled ? 1.0 : 0.4
                        }
                        }
                    }
                }

                // #1927: `thumbui/rect: metadata_group` — a NÉGY
                // panelkapcsoló (Emberek · Helyek · Címkék · Tulajdonságok).
                //
                // Mérve a `respack.yt` rétegfejléceiből (#1914; a tálca
                // függőleges méretei 1:1-ben képpontok):
                //
                //   metadata_group     545..785 × 448..472  →  240×24
                //   people_toggle      545..605             →   60×24
                //   places_toggle      605..665             →   60×24
                //   tags_toggle        665..725             →   60×24
                //   properties_toggle  725..785             →   60×24
                //
                // A négy gomb ÉRINTKEZIK (545→605→665→725→785, nincs rés),
                // és a típusneveik a szegmens-szerepet is megadják:
                // `buttcon_LS_` (bal szélső) · `_MS_` (két középső) ·
                // `_RS_` (jobb szélső) ⇒ ÖSSZEFÜGGŐ SZEGMENSSÁV, nem négy
                // különálló gomb. A `_text_RC` utótag: az ikon balra, a
                // felirat tőle jobbra, függőlegesen középre.
                //
                // A panelek MEGVANNAK (`activeDrawerTab`: people/places/
                // tags/properties) — itt csak a MÁSODIK belépési pont
                // hiányzott; a menüből eddig is el lehetett érni őket.
                //
                // ⚠️ Az ikonok SAJÁT RAJZOK. A méretük az eredetiből mért
                // (`people_icon` 19×17, `places_icon` 14×19, `tags_icon`
                // 19×15, `properties_icon` 17×18), de a projekt egyetlen
                // kicsomagolt Picasa-képet sem szállít — minden ikonunk
                // kézzel rajzolt SVG.
                //
                // ⛔ NINCS MEG: hogy a négy kapcsoló KIZÁRÓ csoport-e. A
                // #1773 a jobb fiók négy LAPJÁRA mérte ki a kizárólagosságot,
                // és nálunk egyetlen `activeDrawerTab` írja le mind a
                // négyet — a gombok ezt tükrözik. Hogy az EREDETI is így
                // viselkedik-e, nincs megmérve; a #1927 nyitott kérdése.
                Row {
                    id: trayMetadataGroup
                    objectName: "trayMetadataGroup"
                    //: #2305: a MÉRT sorrend a `respack.yt` x-tartományaiból
                    //: — `loupehit` 366…391 < `scalecontainer` 398…525 <
                    //: `metadata_group` 545…785. Vagyis a csúszka MEGELŐZI a
                    //: négy kapcsolót; korábban fordítva állt.
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 0            // a gombok ÉRINTKEZNEK (mérve)

                    readonly property var kapcsolok: [
                        { nev: "people", ikon: "panel-emberek.svg",
                          felirat: qsTr("People"),
                          sugo: qsTr("Show/Hide People Panel") },
                        { nev: "places", ikon: "panel-helyek.svg",
                          felirat: qsTr("Places"),
                          sugo: qsTr("Show/Hide Places Panel") },
                        { nev: "tags", ikon: "panel-cimkek.svg",
                          felirat: qsTr("Tags"),
                          sugo: qsTr("Show/Hide Tags Panel") },
                        { nev: "properties", ikon: "panel-tulajdonsagok.svg",
                          felirat: qsTr("Properties"),
                          sugo: qsTr("Show/Hide Properties Panel") }
                    ]

                    Repeater {
                        model: trayMetadataGroup.kapcsolok
                        delegate: PicasaButton {
                            required property var modelData
                            required property int index
                            objectName: "trayPanelToggle_" + modelData.nev
                            width: 60
                            height: 24
                            //: a szegmens-szerep: a szélsők lekerekítve, a
                            //: középsők nem — így áll össze az összefüggő sáv
                            readonly property bool balSzelso: index === 0
                            readonly property bool jobbSzelso:
                                index === trayMetadataGroup.kapcsolok.length - 1
                            //: #718-minta: a főablak átmenetileg null lehet
                            //: az engine leépítésekor.
                            //:
                            //: ⚠️ TERNÁRIUS, nem `&&`: a JS `&&` a HAMIS
                            //: OPERANDUST adja vissza (itt `null`-t), nem
                            //: bool-t, és a Qt ilyenkor „Unable to assign
                            //: [undefined] to bool" hibát ír. A #1260-as
                            //: fixture-őr ezt a CI-n el is kapta.
                            readonly property bool aktiv: tray.appWindow
                                ? tray.appWindow.activeDrawerTab === modelData.nev
                                : false
                            accent: aktiv ? Theme.selectionBlue : "transparent"
                            ToolTip.text: modelData.sugo
                            ToolTip.visible: hovered
                            ToolTip.delay: 500
                            //: ⚠️ a #1773 rádió-csapdája: az AKTÍV gombra
                            //: kattintva a fiók BEZÁRUL, nem marad
                            //: állapot nélkül
                            onClicked: {
                                if (!tray.appWindow) return
                                tray.appWindow.activeDrawerTab =
                                    aktiv ? "" : modelData.nev
                            }
                            //: #2305: a felirat NEM a gombon van. Az
                            //: eredeti négy gombja kizárólag ikonos (a
                            //: `buttcon_*` típusnevek is ikon-gombot
                            //: jelölnek), és a 60 × 24-es cellába az ikon
                            //: MELLETT a szöveg csak levágva fért volna be —
                            //: a tulajdonos képernyőmentésén „Ember" és
                            //: „Tulajdon:" látszott. A szöveg nem vész el:
                            //: buboréksúgó és akadálymentesítési név.
                            Accessible.name: modelData.felirat
                            contentItem: Item {
                                Image {
                                    source: "icons/" + modelData.ikon
                                    width: 16; height: 16
                                    fillMode: Image.PreserveAspectFit
                                    anchors.centerIn: parent
                                }
                            }
                        }
                    }
                }

                // `scale_group` — nagyítás-csúszka − / + jelekkel
                // (kézikönyv 06), a sáv jobb felső sarkához zárva
                // (`m_offsetRT` a `basecontrolset`-en)
                Row {
                    id: trayZoomGroup
                    objectName: "trayZoomGroup"
                    //: #2305: a négy panelkapcsoló ELŐTT (ld. ott a mért
                    //: x-tartományokat).
                    anchors.right: trayMetadataGroup.left
                    anchors.rightMargin: 12
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 6

                    // #1911: a rács-nagyító KAPCSOLÓJA. A #1808 megépítette
                    // a nagyítót, de a gombja a v0.8.198-ban kikerült az
                    // eszköztárból, és a funkció ezzel elérhetetlenné vált —
                    // a tulajdonos élesben jelentette, hogy „semmit nem
                    // csinál". A lánc működik, csak nem volt mit megnyomni.
                    //
                    // Az ALSÓ SÁVBA kerül vissza, nem az eszköztárba: mérve
                    // (`docs/specs/racs-nagyito.md` 1. és 5.) az eredeti
                    // belépési pontja a `thumbui/loupehit`, egy 25 × 19-es
                    // gomb a `scale_group`-ban, a nagyítás-csúszka ELŐTT
                    // (`loupehit` x 366…391, `scalecontainer` x 398…525).
                    PicasaButton {
                        id: trayLoupeButton
                        objectName: "trayLoupeButton"
                        //: MÉRT méret (`thumbui/loupehit`)
                        width: 25
                        height: 19
                        anchors.verticalCenter: parent.verticalCenter
                        //: ⚠️ NEM `checkable` + kötött `checked` — az a
                        //: projekt ismert rádió-csapdája (#1773): a gomb
                        //: kattintáskor MAGA is átírja a `checked`-et, és
                        //: ezzel eltöri a kötést, amiből olvassuk. A
                        //: bekapcsolt állapotot ezért — a panelkapcsolók
                        //: mintájára — az `accent` jelzi, a `loupeActive`
                        //: pedig az EGYETLEN igazságforrás.
                        //:
                        //: A saját tesztje ezt élesben fogta meg: a
                        //: kikapcsolás nem jutott el a rács rétegéhez.
                        readonly property bool aktiv: tray.appWindow
                            ? tray.appWindow.loupeActive === true : false
                        accent: aktiv ? Theme.selectionBlue : "transparent"
                        //: ⚠️ A felfedezhetőség a MI döntésünk: az eredeti
                        //: nem ad rá támpontot — mérve (spec 2. szakasz)
                        //: külön egérmutatót SEM használ. A #1911 viszont
                        //: kiköti, hogy kipróbálás nélkül is kiderüljön:
                        //: nyomva HÚZNI kell. A legkisebb ilyen jelzés a
                        //: buboréksúgó — nem foglal helyet, és nem talál ki
                        //: új viselkedést.
                        ToolTip.text: qsTr("Loupe — drag over the photos")
                        ToolTip.visible: hovered
                        ToolTip.delay: 500
                        onClicked: {
                            if (!tray.appWindow) return
                            tray.appWindow.loupeActive =
                                !tray.appWindow.loupeActive
                        }
                        contentItem: Image {
                            objectName: "trayLoupeIcon"
                            source: "icons/loupe.svg"
                            //: `thumbui/loupe` — MÉRT 23 × 16 a 25 × 19-es
                            //: gombon belül
                            width: 23; height: 16
                            sourceSize.width: 23; sourceSize.height: 16
                            fillMode: Image.PreserveAspectFit
                            anchors.centerIn: parent
                            //: a kikapcsolt állapot halványabb — a bekapcsolt
                            //: állapotot a gomb saját `checked` háttere jelzi
                            opacity: trayLoupeButton.aktiv ? 1.0 : 0.65
                        }
                    }
                    Text {
                        text: "−"
                        color: Theme.textGray
                        font.pixelSize: 13
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    PicasaSlider {
                        id: sizeSlider
                        objectName: "traySizeSlider"
                        // #718: null-őr — appWindow hiányában egy
                        // tetszőleges, a [from, to] tartományba eső érték.
                        from: 72; to: 256
                        value: tray.appWindow ? tray.appWindow.thumbSize : 128
                        //: `thumbui/scalecontainer` — FIX 127 képpont
                        width: 127
                        anchors.verticalCenter: parent.verticalCenter
                        onMoved: tray.appWindow
                                 && (tray.appWindow.thumbSize = value)
                    }
                    Text {
                        text: "+"
                        color: Theme.textGray
                        font.pixelSize: 13
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }

            // `thumbui/separator`: 2 képpont, `0, .365, -3` … `1, 1, -17`,
            // y 50…52 a sáv tetejétől — nálunk (a 20-as infó-csík alatt)
            // y 30…32.
            Rectangle {
                objectName: "traySeparator"
                x: -3
                y: 30
                width: Math.max(0, parent.width - 4)
                height: 2
                color: Theme.trayBorder
            }

            // `thumbui/webupload_rect`: 147 × 44 az osztóponttól 5
            // képponttal balra, benne a 141 × 35-ös gomb.
            //
            // ⚠️ A kényszerek (`0, .365, -5` … `1, .365, 140`) 145
            // képpontot adnak, a respack rétegfejléce 147-et. A KETTŐ
            // KÖZÖTTI 2 képpont a hely ÜRES jobb margója: a benne
            // középre zárt 141-es gomb jobb széle így is az osztópont +
            // 139-nél van, tehát a +140-nél kezdődő műveletsorral nem
            // ütközik. A képernyőképen a gomb 697…837 — az osztópont
            // (700,07) − 3-tól, pontosan 141 képpont szélesen.
            Item {
                id: trayUploadSlot
                objectName: "trayUploadSlot"
                x: -5
                y: 36
                width: 147
                height: 44

                // az egyetlen zöld elsődleges tett (kézikönyv 01/08)
                PicasaButton {
                    id: trayUploadBtn
                    objectName: "trayUploadButton"
                    anchors.centerIn: parent
                    width: 141
                    height: 35
                    text: qsTr("Upload to Google Photos")
                    enabled: false
                    accent: Theme.picasaGreen
                    ToolTip.text: trayUploadBtn.text
                    ToolTip.visible: trayUploadBtn.hovered
                    ToolTip.delay: 500
                    // #1420: a gomb FIX 141 × 35, a felirat pedig KÉT SORBA
                    // tördel benne — pontosan úgy, ahogy az eredetin
                    // („Feltöltés a Google / Fotókba"). A `PicasaButton`
                    // `Text.Wrap` + `Text.Fit` + `clip` hármasa (#992) itt
                    // is véd: elidálni nem elidál, és a gombon kívülre sem
                    // folyhat. Ezért nincs többé ikon-only kompakt mód: a
                    // gomb szélessége már nem az ablakszélesség függvénye.
                    contentItem: Row {
                        spacing: 5
                        Image {
                            anchors.verticalCenter: parent.verticalCenter
                            source: "icons/upload.svg"
                            sourceSize: Qt.size(18, 14)
                        }
                        Text {
                            objectName: "trayUploadLabel"
                            width: trayUploadBtn.width - 2 * 5 - 18 - 5
                            // ⚠️ EXPLICIT magasság kell: enélkül a `Text`
                            // magassága a saját `contentHeight`-je, a
                            // `Text.Fit` pedig ebbe a körbe futva a
                            // ZSUGORÍTOTT, EGYSOROS megoldást választja
                            // (mérve: 9 képpontos betű, egy sor) a
                            // teljes méretű, kétsoros helyett.
                            height: parent.height
                            verticalAlignment: Text.AlignVCenter
                            text: trayUploadBtn.text
                            font: trayUploadBtn.font
                            color: "white"
                            wrapMode: Text.Wrap
                            elide: Text.ElideNone
                            fontSizeMode: Text.Fit
                            minimumPixelSize: trayUploadBtn.minimumLabelPixelSize
                            minimumPointSize: trayUploadBtn.minimumLabelPixelSize
                            horizontalAlignment: Text.AlignHCenter
                            lineHeightMode: Text.ProportionalHeight
                            lineHeight: 10 / 12
                            clip: true
                        }
                    }
                }
            }

            // `thumbui/outputs`: `XConstraint 0, .365, 140` … `1, 1, -10`
            //
            // #1345: a cellák EGYMÁS MELLETT, külön térköz nélkül — az
            // eredetiben a 2-2 képpontos cellamargó ADJA a gombok közötti
            // hézagot, a sáv `spacing`-je nem adódik hozzá.
            Row {
                id: trayActionRow
                objectName: "trayActionRow"
                // a 40 képpontos cellák a zöld gomb 44-es helyére
                // függőlegesen középre: 36 + (44 − 40) / 2 = 38
                x: trayMainBar.outputsOffset
                y: 38
                spacing: 0

                // ---- #2191: túlcsordulás ------------------------------
                //
                // Az eredetiben a sor konténere `overflow:` típusú, és a
                // ki nem férő tételek egy dedikált gomb mögé kerülnek
                // (`outputlayout/morebutton`, 55 × 36 — mint a másik
                // nyolc). A gombok NEM nyomódnak össze: a mért méret
                // kötelező, épp ezért kell a túlcsordulás.
                //
                //: a sávban maradó hely a sor kezdetétől a jobb margóig
                //: A kimeneti gomboknak jutó hely. ⚠️ NEM a sor `x`-éből
                //: számol: a sáv szélesség-modellje a #1420 óta a
                //: `windowWidthFor()`-ban van levezetve (osztópont, jobb
                //: margó, 140-es eltolás, kerekítési ráhagyás) — ez itt
                //: annak az INVERZE, hogy egyetlen igazságforrás legyen.
                //: A kivezetett gombok és a csoportelválasztók helyét le
                //: kell vonni, mert azok a sorban a kimenetiek ELŐTT ülnek.
                readonly property int elerhetoSzelesseg: Math.max(
                    0,
                    (1 - trayMainBar.splitRatio) * trayMainBar.width
                        - trayMainBar.rightMargin
                        - trayMainBar.outputsOffset
                        - trayMainBar.roundingReserve
                        - (trayMainBar.retiredVisible
                           ? trayMainBar.retiredCellCount
                             * trayMainBar.actionCellWidth
                           : 0)
                        - (trayMainBar.separatorsVisible
                           ? 2 * trayMainBar.actionCellWidth
                           : 0))
                //: egy cella teljes szélessége (a mért 59; a gomb 55 + 2-2)
                readonly property int cellaSzelesseg:
                    trayMainBar.actionCellWidth
                //: a kimeneti gombok felirata, a respack deklarációs
                //: sorrendjében — a rejtett tételek listája ebből épül
                //: ⚠️ A feliratokat a GOMBOK adják, nem külön `qsTr()`
                //: hívások: két igazságforrásból a felugró lista némán
                //: elcsúszna a gombokétól (az első változatom „Email"-t és
                //: „Movie"-t írt, a gombokon „E-Mail" és „Mozgófilm" áll),
                //: és a fordítás-őr is két új, sosem látott szöveget kért
                //: volna számon.
                readonly property var gombFeliratok: [
                    trayPrintBtn.text, trayEmailBtn.text, trayExportBtn.text,
                    trayCollageBtn.text, trayMovieBtn.text
                ]
                //: hány cella fér ki. Ha nem mind, EGY helyet a
                //: túlcsordulás-gomb foglal el.
                readonly property int kiferoCellak: {
                    var osszes = trayActionRow.gombFeliratok.length
                    var fer = Math.floor(
                        trayActionRow.elerhetoSzelesseg
                        / trayActionRow.cellaSzelesseg)
                    if (fer >= osszes) return osszes
                    return Math.max(0, fer - 1)   // egy hely a „További…"-nak
                }
                readonly property bool vanRejtett:
                    trayActionRow.kiferoCellak < trayActionRow.gombFeliratok.length
                //: a ki NEM férő gombok feliratai — ebből épül a felugró
                //: lista. A tesztek is ezt mérik: a lista PONTOS kinézete
                //: nincs mérve (a respack csak a gombot adja), a TARTALMA
                //: viszont ellenőrizhető.
                readonly property var rejtettFeliratok:
                    trayActionRow.gombFeliratok.slice(trayActionRow.kiferoCellak)

                //: a hívó cellák ezzel kérdezik meg, látszanak-e
                function cellaLatszik(index) {
                    return index < trayActionRow.kiferoCellak
                }

                //: a felugró listából indított művelet ugyanazt a jelet
                //: küldi, mint a sorbeli gomb — a rejtett tétel nem
                //: „másik" funkció, csak máshol érhető el
                function rejtettMuveletInditasa(menuIndex) {
                    var i = trayActionRow.kiferoCellak + menuIndex
                    if (i === 0) tray.printRequested()
                    else if (i === 1) tray.emailRequested()
                    else if (i === 2) tray.exportRequested()
                    else if (i === 3) tray.collageRequested()
                    else if (i === 4) tray.movieRequested()
                }

                // #1345: a kimeneti sáv gombjai a `respack.yt` MÉRT
                // geometriájával — mindegyik **55 × 36** képpont, egy
                // **59 × 40**-es cellában (`TrayActionCell`;
                // `docs/specs/picasa-keptalca.md` 11.).
                //
                // A sorrend a respack DEKLARÁCIÓS sorrendje (spec 7.):
                // print → email → export → [shop] → hello → [blog] →
                // collage → movie → [morebutton]. A szögletes zárójelben
                // álló három gomb nálunk MÉG NINCS MEG
                // (`docs/specs/ui-lefedettseg.md` `outputlayout`
                // hiánylistája).
                TrayActionCell {
                    //: #2191: a 0. cella — a sor számolja, kifér-e
                    visible: trayActionRow.cellaLatszik(0)
                    TrayActionButton {
                        id: trayPrintBtn
                        objectName: "trayPrintButton"
                        anchors.fill: parent
                        text: qsTr("Print")
                        iconSource: "icons/print.svg"
                        iconObjectName: "trayPrintIcon"
                        labelObjectName: "trayPrintLabel"
                        // #32: kijelölés kell hozzá, néző-nézetben (egy kép) is
                        // elérhető
                        // #718: null-őr — ld. a fenti `ctl` docstringje.
                        enabled: tray.appWindow
                                 ? (tray.appWindow.viewerOpen
                                    ? tray.viewerIndex >= 0
                                    : tray.appWindow.selectedIndexes.length > 0)
                                 : false
                        onClicked: tray.printRequested()
                        // #1345: a felirat a fix méretű gombon BELÜL ül,
                        // ezért minden ablakszélességen látszik.
                        ToolTip.text: trayPrintBtn.text
                        ToolTip.visible: trayPrintBtn.hovered
                        ToolTip.delay: 500
                    }
                }
                TrayActionCell {
                    //: #2191: a 1. cella — a sor számolja, kifér-e
                    visible: trayActionRow.cellaLatszik(1)
                    TrayActionButton {
                        id: trayEmailBtn
                        objectName: "trayEmailButton"
                        anchors.fill: parent
                        text: qsTr("E-Mail")
                        iconSource: "icons/email.svg"
                        iconObjectName: "trayEmailIcon"
                        labelObjectName: "trayEmailLabel"
                        // #718: null-őr — ld. a fenti `ctl` docstringje.
                        enabled: tray.appWindow
                                 ? (tray.appWindow.viewerOpen
                                    ? tray.viewerIndex >= 0
                                    : tray.appWindow.selectedIndexes.length > 0)
                                 : false
                        onClicked: tray.emailRequested()
                        ToolTip.text: trayEmailBtn.text
                        ToolTip.visible: trayEmailBtn.hovered
                        ToolTip.delay: 500
                    }
                }
                TrayActionCell {
                    //: #2191: a 2. cella — a sor számolja, kifér-e
                    visible: trayActionRow.cellaLatszik(2)
                    TrayActionButton {
                        id: trayExportBtn
                        objectName: "trayExportButton"
                        anchors.fill: parent
                        text: qsTr("Export")
                        iconSource: "icons/folder-export.svg"
                        iconObjectName: "trayExportIcon"
                        labelObjectName: "trayExportLabel"
                        // #718: null-őr — ld. a fenti `ctl` docstringje.
                        enabled: tray.appWindow
                                 ? (!tray.appWindow.viewerOpen
                                    && tray.appWindow.selectedIndexes.length > 0)
                                 : false
                        onClicked: tray.exportRequested()
                        ToolTip.text: trayExportBtn.text
                        ToolTip.visible: trayExportBtn.hovered
                        ToolTip.delay: 500
                    }
                }
                // #1672: `outputlayout/shop` — „Papírképek rendelése".
                // KIVEZETETT (`retired`), nem helyfoglaló: a Picasa
                // nyomat-rendelő partnerszolgáltatásai megszűntek, tehát
                // nem ígérünk mögé jövőbeli funkciót. A HELYE viszont az
                // eredetié, a mért sorrend szerint: export UTÁN, „Hello"
                // ELŐTT.
                TrayActionCell {
                    visible: trayMainBar.retiredVisible
                    TrayActionButton {
                        id: trayOrderBtn
                        objectName: "trayOrderButton"
                        anchors.fill: parent
                        enabled: false
                        iconSource: "icons/share.svg"
                        iconObjectName: "trayOrderIcon"
                        //: kivezetett: a nyomat-rendelő szolgáltatás megszűnt
                        ToolTip.text: qsTr("Order Prints (service discontinued)")
                        ToolTip.visible: trayOrderBtn.hovered
                        ToolTip.delay: 500
                    }
                }
                // `outputlayout/sharewith` („Hello") — backend híján tiltott
                // helyőrző, de a HELYE az eredetié: az export után, a kollázs
                // előtt (a `shop` és a `blog` közé esik).
                TrayActionCell {
                    TrayActionButton {
                        id: trayShareBtn
                        objectName: "trayShareButton"
                        anchors.fill: parent
                        enabled: false
                        iconSource: "icons/share.svg"
                        iconObjectName: "trayShareIcon"
                    }
                }
                // #1672: `outputlayout/blog` — „Közzététel a Bloggeren".
                // Szintén KIVEZETETT: a Picasa Blogger-integrációja
                // megszűnt. A mért sorrendben a „Hello" UTÁN, a
                // csoportelválasztó ELŐTT áll.
                TrayActionCell {
                    visible: trayMainBar.retiredVisible
                    TrayActionButton {
                        id: trayBlogBtn
                        objectName: "trayBlogButton"
                        anchors.fill: parent
                        enabled: false
                        iconSource: "icons/share.svg"
                        iconObjectName: "trayBlogIcon"
                        //: kivezetett: a Blogger-integráció megszűnt
                        ToolTip.text: qsTr("Publish to Blogger (service discontinued)")
                        ToolTip.visible: trayBlogBtn.hovered
                        ToolTip.delay: 500
                    }
                }
                // #1345: a csoportelválasztó (`outputlayout/separator`),
                // 2 × 27 képpont a saját 59 × 40-es cellájában. Szűk
                // ablakban elmarad: a fix méretű cellák mellett ez a 118
                // képpont az, ami már nem fér be (az eredetiben erre való
                // a `morebutton`/`overflow`, ami nálunk még nincs meg).
                TrayActionSeparator { visible: trayMainBar.separatorsVisible }
                // #361: Kollázs / Film — a PBZ-leltár szerint
                // (outputlayout/collage, /makemovie) az eredeti kimeneti
                // sávnak is részei.
                //
                // #1116: a Kollázs gomb felirata és buboréksúgója NEM új
                // fordítás, hanem átvétel a Picasa saját honosítási
                // táblájából (`outputlayout_text.tre`).
                TrayActionCell {
                    //: #2191: a 3. cella — a sor számolja, kifér-e
                    visible: trayActionRow.cellaLatszik(3)
                    TrayActionButton {
                        id: trayCollageBtn
                        objectName: "trayCollageButton"
                        anchors.fill: parent
                        text: qsTr("Collage")
                        iconSource: "icons/collage.svg"
                        iconObjectName: "trayCollageIcon"
                        labelObjectName: "trayCollageLabel"
                        // #718: null-őr — ld. a fenti `ctl` docstringje.
                        enabled: tray.appWindow
                                 ? (!tray.appWindow.viewerOpen
                                    && tray.appWindow.selectedIndexes.length > 0)
                                 : false
                        onClicked: tray.collageRequested()
                        // #1116: az eredeti súgója a művelet MONDATA, nem a
                        // gombfelirat ismétlése.
                        ToolTip.text: qsTr(
                            "Create a Photo Collage with your selection")
                        ToolTip.visible: trayCollageBtn.hovered
                        ToolTip.delay: 500
                    }
                }
                TrayActionCell {
                    //: #2191: a 4. cella — a sor számolja, kifér-e
                    visible: trayActionRow.cellaLatszik(4)
                    TrayActionButton {
                        id: trayMovieBtn
                        objectName: "trayMovieButton"
                        anchors.fill: parent
                        iconSource: "icons/movie.svg"
                        iconObjectName: "trayMovieIcon"
                        // #718: null-őr — ld. a fenti `ctl` docstringje.
                        enabled: tray.appWindow
                                 ? (!tray.appWindow.viewerOpen
                                    && tray.appWindow.selectedIndexes.length > 0)
                                 : false
                        onClicked: tray.movieRequested()
                    }
                }
                TrayActionSeparator { visible: trayMainBar.separatorsVisible }

                // #2191: `outputlayout/morebutton` — a ki nem férő gombok
                // mögötte, felugró listában. Csak akkor látszik, ha van
                // rejtett tétel.
                TrayActionCell {
                    objectName: "trayMoreCell"
                    visible: trayActionRow.vanRejtett
                    TrayActionButton {
                        id: trayMoreBtn
                        objectName: "trayMoreButton"
                        anchors.fill: parent
                        //: `outputlayout_text` — angolul „More...”
                        text: qsTr("More...")
                        iconSource: "icons/export.svg"
                        iconObjectName: "trayMoreIcon"
                        labelObjectName: "trayMoreLabel"
                        enabled: true
                        onClicked: trayMoreMenu.popup()
                        //: `Click here for more options`
                        ToolTip.text: qsTr("Click here for more options")
                        ToolTip.visible: trayMoreBtn.hovered
                        ToolTip.delay: 500
                    }
                }
            }

            // #2191: a rejtett tételek listája. ⚠️ A felugró PONTOS
            // kinézete NINCS mérve — a `respack.yt` csak a gombot adja, a
            // tartalom futásidőben épül —, ezért a legegyszerűbb, a
            // többi helyi menünkkel egyező alakot használjuk.
            Menu {
                id: trayMoreMenu
                objectName: "trayMoreMenu"
                Repeater {
                    model: trayActionRow.rejtettFeliratok
                    delegate: MenuItem {
                        objectName: "trayMoreItem"
                        text: modelData
                        onTriggered: trayActionRow.rejtettMuveletInditasa(index)
                    }
                }
            }
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
        Rectangle {
            id: traySingleActionBar
            objectName: "traySingleActionBar"
            //: a `basecontrolset` tetejétől +45; a 14-es infó-csík már
            //: nem része ennek a sávnak, ezért 45 − 14
            y: 45 - 14
            x: trayMainBar.splitX + 2
            width: Math.max(
                0, trayMainBar.width - trayMainBar.rightMargin * 2 - x)
            //: alul −2 a készlet aljától
            height: Math.max(0, trayMainBar.height - 2 - y)
            //: `decrect(softbevel/flatbevel)` — átlátszatlan, ezért TAKAR
            color: Theme.trayPanelBg
            border.width: 1
            border.color: Theme.trayBorder
            radius: 2
            //: a kimeneti gombsor FÖLÉ kerül (spec 2.4)
            z: 50

            //: #718-minta: az appWindow átmenetileg null lehet.
            //:
            //: A ✕ CSAK ELREJT (spec 2.3: `Property hidetarget`, más
            //: hívás nélkül) — a mód jelzőjéhez NEM nyúl, a projekt lapja
            //: nyitva marad, és a lapsávból tovább lehet visszatérni.
            property bool elrejtve: false
            visible: tray.appWindow
                     ? (tray.appWindow.backToCollagePrompted === true
                        && !traySingleActionBar.elrejtve)
                     : false
            //: újbóli belépéskor megint látszódjon
            Connections {
                //: ⚠️ TERNÁRIUS, nem csupasz hivatkozás (#1260): a
                //: `tray.appWindow` az engine felépítése/leépítése közben
                //: `undefined` lehet, és a Qt ilyenkor „Unable to assign
                //: [undefined] to QObject*" hibát ír — a fixture-életciklus
                //: őre ezt BUKÁSNAK veszi. A `null` érvényes cél (a
                //: kapcsolat egyszerűen nem él), az `undefined` nem.
                target: tray.appWindow ? tray.appWindow : null
                ignoreUnknownSignals: true
                function onBackToCollagePromptedChanged() {
                    traySingleActionBar.elrejtve = false
                }
            }

            Text {
                objectName: "traySingleActionMessage"
                //: MÉRT: 335 × 26, JOBBRA igazítva (`textalign right`)
                width: 335
                height: 26
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: traySingleActionReturn.left
                anchors.rightMargin: 9
                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                color: Theme.ink
                font.pixelSize: Theme.fontSize
                //: a `thumbui/single_action_message` HIVATALOS magyar
                //: fordítása (`referencia/panel-feliratok-hu.tsv:5187`)
                text: qsTr("Select the items you want to add to the "
                           + "project clip tray, then click \"Back\" to "
                           + "return to the project")
            }

            PicasaButton {
                id: traySingleActionReturn
                objectName: "traySingleActionReturn"
                //: MÉRT: 109 × 43
                width: 109
                height: 43
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: traySingleActionClose.left
                anchors.rightMargin: 3
                accent: Theme.picasaGreen
                // #2438: az eredetiben ez a `thumbui/single_action_return`, a
                // 13 pulzáló elem egyike — a klip-gyűjtő módban EZ a fő
                // cselekvés, tehát ez mutatja meg, hol lehet visszalépni.
                throbbing: true
                text: qsTr("Back to Collage")
                ToolTip.text: qsTr("Go back to what you were editing")
                ToolTip.visible: hovered
                ToolTip.delay: 500
                onClicked: tray.backToCollageRequested()
            }

            PicasaButton {
                id: traySingleActionClose
                objectName: "traySingleActionClose"
                //: MÉRT: 18 × 18
                width: 18
                height: 18
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: 16
                text: "\u2715"
                ToolTip.text: qsTr("Cancel \"Get more\"")
                ToolTip.visible: hovered
                ToolTip.delay: 500
                //: CSAK elrejt — a módból NEM lép ki (spec 2.3)
                onClicked: traySingleActionBar.elrejtve = true
            }
        }
    }
}
