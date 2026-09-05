import QtQuick
import QtQuick.Window

// A LEBEGŐ ÉRTESÍTŐSÁV — `CNotifierPopup`, „Picasa Értesítő" (#1129).
//
// Spec: `docs/specs/picasa-lebego-ertesito.md`.
//
// A Picasa 3 a háttérműveletek végét nem a főablakban jelzi, hanem egy
// önálló, keret nélküli kis ablakban a képernyő jobb szélén. Nálunk ez a
// felület eddig EGYÁLTALÁN nem létezett: a háttérműveleteink némán futottak
// le, vagy egy haldokló folyamatjelzőbe írtak.
//
// ## Amit a binárisból MÉRTÜNK (nem becslés)
//
// | mi | érték | forrás |
// |---|---|---|
// | ablaknév | `Picasa Notifier` / „Picasa Értesítő" | `CNotifierPopup::window_name` |
// | ablakstílus | `WS_EX_TOPMOST \| TOOLWINDOW \| WINDOWEDGE` | `0x0065743c` |
// | elhelyezés | `SPI_GETWORKAREA` — MUNKATERÜLET, nem képernyő | `0x00657353` |
// | függőleges horgony | a munkaterület alja **− 144** képpont | `0x00657369` |
// | cella | 247 × 45 | `respack.yt` `notifier/docbounds` |
//
// A `local_4 + -0x90` a `SPI_GETWORKAREA` RECT NEGYEDIK mezőjén dolgozik
// (`left, top, right, bottom` sorrendben a `local_10 … local_4` rekeszek),
// tehát az eltolás az ALSÓ élhez képest értendő, és a kapott érték az
// ablak FELSŐ éle lesz (`local_1c = local_4`).
//
// ## Az ablak SINGLETON — a cellák nem azok
//
// A létrehozója (`0x00657300`) egyetlen helyről, az alkalmazás indításából
// hívódik (`0x0040bf70`). Az ablak tehát egyszer jön létre és végig él; az
// egyes értesítések CELLÁK benne (`cellbase`, `cell1`). Ezért van itt
// lista és `Repeater`, nem eseményenkénti ablak.
//
// ## Az élettartam és az átmenet
//
// SAJÁT FUNKCIÓ (#1129): a cella magától eltűnik `cellLifetimeMs` után. Az
// eredeti élettartama NINCS kimérve — a spec ezt nyitott kérdésként tartja
// nyilván, és a bináris importtáblája alapján bizonyítottan NEM Win32
// időzítő méri (a `SetTimer`/`KillTimer`/`timeSetEvent` egyik hívója sincs
// a notifier moduljában). A magától eltűnés viszont a #1168 kimondott
// igénye: enélkül a kész-értesítés csak kattintásra tűnne el. A választott
// érték a mi döntésünk, nem az eredeti mérése.
//
// Az átmenet HOSSZAI viszont mért értékek — a `yt` keretrendszer ugyanazon
// konstansai, amelyeket a #1000 (gyűrű-elhalványulás) is használ: 0,25 s
// megjelenés, 0,5 s eltűnés. Szándékosan ugyanaz az alak is (olvasható
// `readonly property int` konstansok + `Timer` + `Behavior on opacity`,
// iránytól függő hosszal): két versengő időzítés-minta helyett egy.
//
// ## A tartalmat a HÍVÓK adják
//
// Az ablaknak nincs saját esemény-katalógusa: egyetlen saját rekordja van
// (`il_PopupNotifierRec`), minden más szöveget a hívó ad át. Ezért általános
// a `notify()` API, és ezért élnek a konkrét események a `Connections`
// blokkokban — a sáv KERET, az események rákötése külön jegyeké.
Window {
    id: notifier
    objectName: "picasaNotifier"

    // ------------------------------------------------------------------
    // Mért geometria
    // ------------------------------------------------------------------

    //: `respack.yt` `notifier/docbounds` — az ablak FIX szélessége.
    readonly property int cellWidth: 247
    //: Egy cella magassága.
    readonly property int cellHeight: 45
    //: `0x00657369` — eltolás a munkaterület ALSÓ élétől.
    readonly property int anchorOffsetPx: 144

    //: A munkaterület (`SPI_GETWORKAREA`), nem a teljes képernyő — a
    //: tálcát tiszteletben tartjuk, ahogy az eredeti is.
    readonly property int munkateruletSzelesseg: Screen.desktopAvailableWidth
    readonly property int munkateruletMagassag: Screen.desktopAvailableHeight

    // ------------------------------------------------------------------
    // Időzítés
    // ------------------------------------------------------------------

    //: SAJÁT FUNKCIÓ (#1129): a cella magától eltűnik ennyi idő után — az
    //: eredeti élettartama nincs kimérve (ld. a fenti magyarázatot).
    readonly property int cellLifetimeMs: 6000
    //: A megjelenés hossza (a #1000-rel közös, mért `yt` konstans).
    readonly property int fadeInMs: 250
    //: Az eltűnés hossza (a #1000-rel közös, mért `yt` konstans).
    readonly property int fadeOutMs: 500

    // ------------------------------------------------------------------
    // API
    // ------------------------------------------------------------------

    /** A felhasználó egy cellára kattintott. A `kind` az eseményfajta, az
        `payload` a hozzá tartozó adat (nálunk útvonal). A sáv annyit tesz
        magától, amennyit a vezérlőn át elér (a mappára navigálást); a
        további célzás — például a kép kijelölése a rácsban — az ablak
        állapota, tehát a gazdáé. */
    signal activated(string kind, string payload)

    /** Új értesítés a sáv aljára. Üres címre nem csinálunk semmit: a
        tartalmatlan felvillanás rosszabb a hiányzó értesítésnél. */
    function notify(kind, title, hint, payload) {
        const cim = String(title || "")
        if (cim.length === 0)
            return
        cellak.append({
            "kind": String(kind || ""),
            "title": cim,
            "hint": String(hint || ""),
            "payload": String(payload || "")
        })
    }

    /** Egy cella elvétele — kattintás, zárás vagy lejárat után. */
    function dismissAt(index) {
        if (index >= 0 && index < cellak.count)
            cellak.remove(index)
    }

    /** Minden cella elvétele. */
    function dismissAll() {
        cellak.clear()
    }

    /** Egy útvonal mappája. A QML-ben nincs `Path`, és az útvonal a
        PLATFORM elválasztóját hozza — mindkettőt vágjuk. */
    function folderOfPath(path) {
        const szoveg = String(path)
        const vago = Math.max(szoveg.lastIndexOf("/"), szoveg.lastIndexOf("\\"))
        return vago > 0 ? szoveg.substring(0, vago) : ""
    }

    // ------------------------------------------------------------------
    // Állapot
    // ------------------------------------------------------------------

    ListModel { id: cellak }

    readonly property bool hasCells: cellak.count > 0
    //: A sávban álló értesítések száma. A `Repeater` delegáltjait
    //: `findChild` NEM találja meg, ezért a sáv állapotát a gazda (és a
    //: teszt) ezen a két olvasón át kérdezi, nem a vizuális fából.
    readonly property int cellCount: cellak.count

    //: A legutóbb felvett értesítés hasznos adata (nálunk útvonal), vagy
    //: üres sztring, ha a sáv üres. Property, nem függvény: így a gazda
    //: kötni is tudja, és a teszt egyszerűen olvassa.
    readonly property string lastPayload:
        cellak.count > 0 ? cellak.get(cellak.count - 1).payload : ""

    //: #1566: a legutóbbi értesítés két SZÖVEGSORA. Ugyanaz az ok, mint a
    //: `lastPayload`-nál: a `Repeater` delegáltjait a `findChild` nem
    //: találja meg, tehát a MEGJELENŐ feliratot csak innen lehet mérni —
    //: márpedig a #1566 tétje épp a felirat, nem a jelzés kibocsátása.
    readonly property string lastTitle:
        cellak.count > 0 ? cellak.get(cellak.count - 1).title : ""
    readonly property string lastHint:
        cellak.count > 0 ? cellak.get(cellak.count - 1).hint : ""

    // ------------------------------------------------------------------
    // Az ablak
    // ------------------------------------------------------------------

    //: `CNotifierPopup::window_name`
    title: qsTr("Picasa Notifier")

    //: `0x0065743c`: `WS_EX_TOPMOST | WS_EX_TOOLWINDOW`. A
    //: `WindowDoesNotAcceptFocus` a `TOOLWINDOW` következménye: az
    //: értesítés nem veheti el a fókuszt a munkától.
    flags: Qt.FramelessWindowHint
           | Qt.Tool
           | Qt.WindowStaysOnTopHint
           | Qt.WindowDoesNotAcceptFocus

    //: Az ablak a FŐABLAKTÓL FÜGGETLEN (`0x00657300` az alkalmazás
    //: indításából hozza létre, nem a főablakból). A gazdában
    //: példányosítva a Qt magától a főablakot tenné tranziens szülőnek,
    //: amitől az értesítő a főablakkal együtt tűnne el (minimalizálás) —
    //: az eredeti nem így viselkedik.
    transientParent: null

    width: cellWidth
    height: Math.max(cellHeight, cellak.count * cellHeight)
    //: A jobb szélre, a MUNKATERÜLET aljától 144 képponttal feljebb.
    x: munkateruletSzelesseg - width
    y: munkateruletMagassag - anchorOffsetPx
    color: Theme.chromeBg

    //: Az eltűnés animációja alatt még kint kell lennie, különben az
    //: ablak a kihalványulás első képkockájánál eltűnne.
    visible: notifier.hasCells || elhalvanyulas.running

    Component.onCompleted: NotifierBus.attached = true
    Component.onDestruction: NotifierBus.attached = false

    Column {
        id: oszlop
        width: parent.width

        //: #2157: a „B" sáv a cella SORSZÁMÁT szorozza a cellamagassággal
        //: (`[popup+0x1c0]` = 45), és ez is kulcskockás — vagyis ha egy
        //: fölöttes cella eltűnik, a többi ODACSÚSZIK az új helyére, nem
        //: ugrik. A `Column` `move` átmenete pontosan ezt adja, ugyanazzal
        //: az időzítéssel és görbével, mint a vízszintes csúszás.
        move: Transition {
            NumberAnimation {
                objectName: "notifierStackAnim"
                properties: "y"
                duration: 600
                easing.type: Easing.OutExpo
            }
        }

        opacity: notifier.hasCells ? 1.0 : 0.0

        Behavior on opacity {
            NumberAnimation {
                id: elhalvanyulas
                objectName: "notifierFadeAnim"
                //: Az IRÁNY dönt: 0,25 s be, 0,5 s ki — ugyanaz az alak,
                //: mint a #1000 gyűrűjénél.
                //:
                //: ⚠️ #2157: az EREDETIBEN nincs átlátszóság-animáció, ott
                //: a cellák csúsznak. Ez a halványítás mégis MARAD, de
                //: már nem a cellákra: az ablak EGÉSZÉRE vonatkozik, és
                //: csak akkor fut le, amikor az utolsó cella is elment
                //: (`hasCells` false). Enélkül a `visible` váltása egy
                //: képkocka alatt kapná el az ablakot — a mi ablakunk a
                //: cellák konténere is, az eredetié nem. A cellák saját
                //: mozgása mostantól TISZTÁN csúszás.
                duration: notifier.hasCells
                          ? notifier.fadeInMs : notifier.fadeOutMs
            }
        }

        Repeater {
            model: cellak

            //: A `model.` előtag SZÁNDÉKOS: a cellának saját `title`,
            //: `hint` és `payload` tulajdonsága van, és a csupasz név
            //: önmagára kötné őket (kötési hurok).
            delegate: NotifierCell {
                cellIndex: index
                title: model.title
                hint: model.hint
                payload: model.payload
                lifetimeMs: notifier.cellLifetimeMs

                //: ⚠️ A cella elvétele a LEGUTOLSÓ lépés, és előtte
                //: mindent lokálisba mentünk: a `dismissAt` lebontja a
                //: delegált saját környezetét, utána a `notifier` és a
                //: `model` már nem hivatkozható („notifier is not
                //: defined").
                onActivated: {
                    const sav = notifier
                    const sorszam = index
                    const cel = model.payload
                    const fajta = model.kind
                    const mappa = sav.folderOfPath(cel)
                    if (mappa.length > 0 && typeof controller !== "undefined"
                            && controller)
                        controller.selectFolder(mappa)
                    sav.activated(fajta, cel)
                    //: #2157: a navigáció AZONNAL megy (a felhasználó
                    //: arra kattintott), a cella pedig közben kicsúszik;
                    //: a `kicsuszasKesz` veszi ki a listából.
                    kicsuszik()
                }
                //: #2157: nem azonnali törlés — előbb a 300 ms-os
                //: visszacsúszás, különben az animáció levágódna.
                onClosed: kicsuszik()
                onExpired: kicsuszik()
                onKicsuszasKesz: notifier.dismissAt(index)
            }
        }
    }

    // ------------------------------------------------------------------
    // A rákötött események
    // ------------------------------------------------------------------
    //
    // Kettő van, mindkettő MEGLÉVŐ, ma némán lefutó műveleté. A többi
    // esemény (képernyőfelvétel, „N kép érkezett") külön jegyé: az
    // előbbihez nálunk maga a funkció hiányzik, az utóbbihoz mappafigyelő
    // kell.

    //: `CAcquireUI::donenotifer` / `errornotifer` — az importálás két záró
    //: állapota. A nevük a binárisban maga mondja ki, hogy értesítőbe
    //: megy; ma a párbeszéden kívül semmi nem jelzi a végét.
    Connections {
        target: typeof importSourceController !== "undefined"
                ? importSourceController : null
        function onImportFinished(imported, failed) {
            if (failed > 0)
                notifier.notify("import-error", qsTr("Error Importing"), "", "")
            else
                notifier.notify("import", qsTr("Completed Importing"),
                                qsTr("click to view"), "")
        }
    }

    //: #1168 → #1129: az „Asztali háttérkép" ág kész-értesítése. A #1168
    //: a `CollageDoneNotice`-ba kötötte, ami a főablak alján ül és csak
    //: kattintásra tűnik el — az eredetiben ez a sáv egyik valódi
    //: eseménye. A régi értesítés a `NotifierBus.attached` kapun át
    //: magától elhallgat, amint ez a sáv jelen van.
    Connections {
        target: typeof controller !== "undefined" ? controller : null
        function onCollageDesktopBackgroundReady(path) {
            //: Útvonal nélkül nincs mire navigálni — a #1168 őre is ezt
            //: méri: üres útvonalra NEM villan fel semmi.
            if (!path)
                return
            //: `collage::done` — a szöveg a kattintási tippet MAGA
            //: tartalmazza, ezért nincs külön második sora.
            notifier.notify("collage",
                            qsTr("The collage is ready (click here)"),
                            "", path)
        }

        //: #1566: a „Mentés másként…" és a „Másolat mentése" vége. Eddig a
        //: két parancsnak SEMMILYEN felületi visszajelzése nem volt: a
        //: `saveCopyFinished` egyetlen fogyasztója a #1539 gépies
        //: újraolvasás-kötése, ami a nyilvántartást frissíti, nem a
        //: felhasználót tájékoztatja.
        //:
        //: ⚠️ A FELIRAT A MI DÖNTÉSÜNK, nem hivatalos Picasa-erőforrás. A
        //: `stringres` mentés-családja (25 bejegyzés, `CThumbUI::FileSave*`
        //: + `CFileSave*`) folyamatjelzést (`progprep`, `progress`,
        //: `progfile`, `progfiles`), megerősítést, formátumváltást és
        //: hibaágakat tartalmaz — BEFEJEZÉS-ÜZENETET NEM. (A „Mentés kész"
        //: / „A mentés elkészült" magyar mondatok hamis barátok: az
        //: `il_BurnPanel::Backup*`, azaz a CD-s biztonsági mentés
        //: feliratai.) A mondat alakja mégis az eredetit követi: külön
        //: egyes és többes szám, ahogy a `progfile`/`progfiles` és a
        //: `messagetag1`/`messagetagX` páros is.
        //:
        //: A második sor viszont HIVATALOS: `CThumbUI::clickview` — ugyanaz
        //: a felirat, amit az importálás kész-értesítése is használ.
        //: #1755: a forgatás két jelző ága. MINDKÉT szöveg HIVATALOS
        //: Picasa-erőforrás (`IDS_ROT_TYPEFAILED`, `IDS_MUST_SELECT_TO_ROT`)
        //: — a magyar is a szövegtárból való, nem a mi fogalmazásunk.
        //:
        //: Eddig mindkét eset néma volt: vegyes fotó+videó kijelölésnél a
        //: videók kimaradtak (#103), a felhasználó pedig csak annyit
        //: látott, hogy nem forgott el minden.
        function onRotationTypeFailed(skipped) {
            if (skipped <= 0)
                return
            notifier.notify(
                "rotate-failed",
                qsTr("One or more images could not be rotated because of the file type."),
                "", "")
        }

        function onRotationNeedsSelection() {
            notifier.notify(
                "rotate-noselection",
                qsTr("Must have selected images to rotate."), "", "")
        }

        function onSaveCopyReady(saved, targetPath) {
            //: Egyetlen sikeres mentés sem volt: a művelet vagy meg lett
            //: szakítva, vagy elbukott — az utóbbit a `SaveDialogs.qml`
            //: hibaágai mondják el. „Kész" értesítés ilyenkor hazugság.
            if (saved <= 0)
                return
            notifier.notify("save-copy",
                            saved === 1
                                ? qsTr("Copy saved")
                                : qsTr("%1 copies saved").arg(saved),
                            qsTr("click to view"), targetPath)
        }
    }
}
