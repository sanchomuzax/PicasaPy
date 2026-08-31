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
    // #361: Kollázs/Film a tálcáról (a dialógusok a Main.qml-ben élnek)
    signal collageRequested()
    signal movieRequested()
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
    // #1420: az eredetiben ez a `thumbui/infotext` — a 105 képpontos sáv
    // LEGTETEJE, 14 képpont magasan. Nálunk 20: szándékos és dokumentált
    // eltérés (olvashatóság, `design-guide.md`), és a 105-be pontosan
    // beleillik: 20 (csík) + 81 (képtálca) + 4 (alsó hézag) = 105.
    Rectangle {
        id: infoBar
        objectName: "trayInfoBar"
        width: parent.width; height: 20
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
            anchors.centerIn: parent
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
            onRemoveSelectionRequested: {
                if (tray.ctl && typeof tray.ctl.removeHeldRows === "function")
                    tray.ctl.removeHeldRows(tray.selectedIndexesOrEmpty)
            }
        }
        // #1420: 20 (infó-csík) + 85 = 105 — a `publishbottom` = −105.
        width: parent.width; height: 85
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
        readonly property int actionCellCount: 6
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
        readonly property real requiredWidth: windowWidthFor(actionCellCount)
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
            y: 0
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
            Row {
                id: trayScratchStrip
                objectName: "trayScratchStrip"
                x: 5
                y: 5
                width: Math.max(0, parent.width - 5 - 50)
                height: parent.height - 10
                spacing: 2
                clip: true
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
                        objectName: "trayPreviewThumb"
                        required property int index
                        // #1420: az eredeti tálcáján a bélyegképek a doboz
                        // TELJES belső magasságát kitöltik (a képernyőképen
                        // ~70 képpont), oldalarányt tartva — a korábbi
                        // 20 × 20-as rács a 81 képpontos dobozban holt
                        // helyet hagyott volna.
                        height: trayScratchStrip.height
                        width: implicitHeight > 0
                               ? Math.round(height * implicitWidth
                                            / implicitHeight)
                               : height
                        source: !tray.ctl || !tray.appWindow ? ""
                            : trayScratchBack.heldCount > 0
                              ? tray.ctl.heldThumbUrlAt(index)
                              : tray.ctl.photos.thumbUrlAt(
                                    Number(tray.appWindow.selectedIndexes[index]))
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                    }
                }
            }
            // `thumbui/scratchlabel` — „Kijelölés", `m_centerXY`: üres
            // tálcánál a felirat a doboz KÖZEPÉN áll, nem a bal szélén
            Text {
                objectName: "trayScratchLabel"
                // #718: ld. a Repeater fenti null-őrét — ugyanaz a
                // teardown-ablak érinti ezt a kötést is.
                visible: trayScratchBack.heldCount === 0
                         && tray.selectedIndexesOrEmpty.length === 0
                anchors.centerIn: parent
                text: qsTr("Selection")
                color: Theme.placeholderText
                font.pixelSize: Theme.fontSize
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
                ToolTip.text: qsTr("Hold Selection")
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
                ToolTip.text: qsTr("Clear Tray")
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
                ToolTip.text: qsTr("Add the pictures in the tray to an album")
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
            y: 0
            width: Math.max(
                0, trayMainBar.width - trayMainBar.rightMargin - x)
            height: parent.height

            // --- felső sor (a sáv tetejétől 20…42 → itt 0…22) ---
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
                        width: 36
                        height: 22
                        anchors.verticalCenter: parent.verticalCenter
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
                        contentItem: Text {
                            objectName: "trayStarLabel"
                            text: "★"
                            font.pixelSize: 15
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            // arany, ha a kiválasztott kép csillagos; egyébként
                            // világos kontúr-csillag (Picasa-minta, nem fekete!)
                            color: (tray.ctl
                                    ? (tray.ctl.photos.revision,
                                       tray.ctl.photos.starAt(trayStar.targetRow))
                                    : false)
                                   ? Theme.starYellow : "#ffffff"
                            style: Text.Outline
                            styleColor: "#9a9a9a"
                        }
                    }
                    //: a csillag utáni 5 képpontos hézag (a `spacing` 1-ből
                    //: már megvan egy)
                    Item { width: 4; height: 1 }
                    PicasaButton {
                        id: trayRotateLeftBtn
                        objectName: "trayRotateLeft"
                        text: "↺"
                        width: 36
                        height: 22
                        anchors.verticalCenter: parent.verticalCenter
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
                        contentItem: Text {
                            objectName: "trayRotateLeftLabel"
                            text: trayRotateLeftBtn.text
                            font: trayRotateLeftBtn.font
                            color: trayRotateLeftBtn.enabled
                                   ? Theme.iconInk : "#9a9a9a"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                    PicasaButton {
                        id: trayRotateRightBtn
                        objectName: "trayRotateRight"
                        text: "↻"
                        width: 36
                        height: 22
                        anchors.verticalCenter: parent.verticalCenter
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
                        contentItem: Text {
                            objectName: "trayRotateRightLabel"
                            text: trayRotateRightBtn.text
                            font: trayRotateRightBtn.font
                            color: trayRotateRightBtn.enabled
                                   ? Theme.iconInk : "#9a9a9a"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }

                // `scale_group` — nagyítás-csúszka − / + jelekkel
                // (kézikönyv 06), a sáv jobb felső sarkához zárva
                // (`m_offsetRT` a `basecontrolset`-en)
                Row {
                    id: trayZoomGroup
                    objectName: "trayZoomGroup"
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 6

                    Text {
                        text: "−"
                        color: Theme.textGray
                        font.pixelSize: 13
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    PicasaSlider {
                        id: sizeSlider
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
                // `outputlayout/sharewith` („Hello") — backend híján tiltott
                // helyőrző, de a HELYE az eredetié: az export után, a kollázs
                // előtt (a kimaradó `shop` és `blog` közé esne).
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
            }
        }
    }
}
