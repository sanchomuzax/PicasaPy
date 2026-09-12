import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import PicasaPy.Gpu
import "aranykenyszer.js" as AranyKenyszer

// Egyképes néző — a Picasa 3.9 "Megjelenítés és szerkesztés" képernyője
// alapján (#808080 háttér, felső filmszalag nyilakkal, bal eszközpanel;
// a szerkesztő-gombok a 2. fázisig szürkék). Enter/Jobbra: következő,
// Balra: előző, Esc: vissza a könyvtárba.
Rectangle {
    id: viewer

    // #1816: látszik-e a felirat-sáv. A GYÖKÉREN áll, mert a sáv és a
    // „Make a caption!" helyőrző két külön szülő alatt él.
    // A `!== undefined` a #1572-őr mintája: a próbák stub-vezérlőjén a
    // tulajdonság hiányozhat.
    readonly property bool captionVisible:
        (controller && controller.captionVisible !== undefined)
            ? controller.captionVisible : true

    function billentsdAFeliratot() {
        if (controller && controller.toggleCaptionVisible !== undefined)
            controller.toggleCaptionVisible()
    }

    // #1072: a megnyitott kép útvonala és a KOLLÁZS-ÁLLAPOTA. A két gomb
    // (Kollázs szerkesztése / Létrehozás) ugyanezt kérdezi, ezért itt áll
    // egyszer — a `filePathAt` hívást háromszor beírni néma szétcsúszás.
    //
    // ⚠️ A `collageSavedPath` SZÁNDÉKOS függőség a kifejezésben: az
    // `isCollageDraft` egy slot, nem értesítő tulajdonság, tehát magától
    // soha nem értékelődne újra. A piszkozat befejezésekor viszont épp ez
    // a tulajdonos változik meg — enélkül a „Létrehozás" gomb a kész
    // kollázs fölött is ottmaradna. Kötési hurok nincs: a gomb nem írja.
    readonly property string currentFilePath:
        (viewer.currentIndex >= 0 && viewer.photosModel !== null)
            ? viewer.photosModel.filePathAt(viewer.currentIndex) : ""
    readonly property bool controllerReady:
        typeof controller !== "undefined" && controller ? true : false
    readonly property bool currentIsCollageDraft: {
        if (!viewer.controllerReady || viewer.currentFilePath.length === 0)
            return false
        return controller.collageSavedPath !== undefined
               && controller.isCollageDraft(viewer.currentFilePath) === true
    }
    readonly property bool currentIsSavedCollage: {
        if (!viewer.controllerReady || viewer.currentFilePath.length === 0)
            return false
        return controller.collageSavedPath !== undefined
               && controller.hasCollageProject(viewer.currentFilePath) === true
    }

    // #641: mekkora magasság kell ahhoz, hogy a bal panel TELJESEN elférjen
    // — a felső sáv plusz a panel saját igénye. Beégetett szám nincs benne:
    // mindkét tag a saját elemétől jön.
    readonly property real panelPreferredHeight:
        viewerTopBar.height + editorPanel.implicitHeight

    // #703: ennyi kell ahhoz, hogy a Visszavonás/Újra sornak MINDIG legyen
    // helye — a fülek tartalma nélkül. Ez a garancia alsó korlátja: a
    // képernyőhöz igazítás sem mehet ez alá.
    readonly property real minimumUsableHeight:
        viewerTopBar.height + editorPanel.chromeHeight

    // #703: a főablak azon sávjai, amelyek a nézőn KÍVÜL esnek (menüsor,
    // eszköztár-fejléc, alsó tálca) — a néző csak a maradékot kapja meg.
    // A `Main.qml` a menüsort külön hozzáadja az ablak minimumához, ezért
    // itt mindhármat le kell vonni a képernyő-költségvetésből.
    readonly property var hostWindow: viewer.Window.window
    readonly property real windowChromeHeight: {
        var w = viewer.hostWindow
        if (!w) return 0
        var extra = 0
        if (w.menuBar) extra += w.menuBar.height
        if (w.header) extra += w.header.height
        if (w.footer) extra += w.footer.height
        return extra
    }
    // Az ablakkeret és a címsor magassága: a Qt ezt az ablak megjelenése
    // ELŐTT nem közli, márpedig a minimumot már akkor be kell jelenteni.
    // Ezért fenntartott keret. Bőkezűen mérve: inkább vágódjon egy csempesor
    // egy alacsony kijelzőn, mint hogy olyan ablak-minimumot kérjünk, amit a
    // kijelző nem tud kiadni — abból a felhasználó a gombsort egyáltalán nem
    // látja (#703).
    readonly property real windowDecorationAllowance: 56

    // #703: A #641 az ablak minimális magasságára tette a „mindig elfér"
    // garanciát (Main.qml) — csakhogy ezt a bejelentést az ablakkezelő csak
    // akkor tudja teljesíteni, ha a kijelzőre ráfér. Élesben, bélyegképes
    // csempékkel a panel igénye 887 px (a legmagasabb fül, a #571 „Régi
    // effektek", egymaga 799), az ablak minimuma ebből 962 — ez egy 768 vagy
    // 900 képpontos laptop-kijelzőn KIADHATATLAN. Ilyenkor a garancia nem
    // „majdnem" teljesül, hanem sehogy.
    //
    // Ezért a kérés a képernyőhöz igazodik: sosem kérünk többet, mint amennyi
    // ténylegesen van, és sosem kevesebbet, mint amennyi a gombsorhoz kell.
    // Ha emiatt a fül tartalma nem fér ki, azt az EditorPanel a
    // `tabContentTruncated` ágán, vágással kezeli — a gombsor soha nem veszít.
    //
    // Property (nem readonly): a teszt felül tudja írni, hogy a „kicsi
    // kijelző" esetet a futtató gép képernyőjétől függetlenül lehessen mérni.
    property real screenHeightBudget:
        Screen.desktopAvailableHeight - viewer.windowChromeHeight
        - viewer.windowDecorationAllowance

    readonly property real requiredHeight:
        Math.min(viewer.panelPreferredHeight,
                 Math.max(viewer.minimumUsableHeight, viewer.screenHeightBudget))
    color: Theme.viewerBg

    property var photosModel: null
    // #305: null-őr — az editController a QML-engine leépítésekor
    // átmenetileg null lehet, miközben a lenti kötések utoljára
    // kiértékelődnek.
    readonly property var editCtl: editController

    // GPU élő-előnézet (#22): a finetune-csúszkák AKTÍV húzása alatt igaz —
    // az EditorPanel finetunePreview→finetuneCommit életciklusa keretezi
    // (ld. lent, az editorPanel bekötésénél). `gpuFinetuneEligible` a
    // KÉT feltétel: (a) a futtatókörnyezet RHI-alapú grafikai kontextust
    // ad (GPU-képtelen — pl. CI offscreen/software — környezetben ez
    // MINDIG false, néma és biztonságos fallback a rendes CPU-útra), és
    // (b) a jelenlegi szerkesztési lánc GPU-alkalmas
    // (`EditController.gpuPrefixSource` nem üres — ld. ott a feltételt).
    property bool gpuFinetuneActive: false
    // #551: a húzás alatti derítőfény-érték nulla-e. Nem nullánál a
    // finomhangolás nem fejezhető ki csatornánkénti LUT-tal (a Derítőfény
    // világosság-vezérelt), ezért a GPU-réteg ilyenkor NEM jelenhet meg —
    // a CPU-előnézet fut helyette, változatlanul.
    property bool gpuFinetunePointSafe: true
    readonly property bool gpuCapable: GraphicsInfo.api !== GraphicsInfo.Software
                                        && GraphicsInfo.api !== GraphicsInfo.Unknown
                                        && GraphicsInfo.api !== GraphicsInfo.Null
    readonly property bool gpuFinetuneEligible: viewer.gpuCapable
        && viewer.editCtl && viewer.editCtl.gpuPrefixSource !== ""

    property int currentIndex: -1
    // a ListView.count reaktív — a rowCount() hívást a QML nem követné
    property int photoCount: filmstrip.count
    // #14: az aktuális elem videó-e — a néző ekkor a lejátszó-nézetet
    // mutatja a fotó-Image helyett (a revision miatt modell-frissülésre
    // is újraértékelődik)
    readonly property bool isCurrentVideo: photosModel
        ? (photosModel.revision,
           photosModel.isVideoAt(currentIndex)) === true
        : false
    signal closed()
    // #8: a felső ▶ Lejátszás gomb — diavetítés az aktuális képtől
    signal playRequested()
    //: #1002: a megnyitott kollázs újranyitása SZERKESZTÉSRE. A néző
    //: csak JELEZ — a lapváltás és a panel feltöltése a gazdáé.
    signal editCollageRequested(string path)
    // #422: a néző kontextusmenüjének „Törlés lemezről" tétele — a
    // megerősítő dialógus a Main.qml-ben él (FileOpsDialogs), ezért a
    // kérés jelként megy kifelé
    signal deleteRequested(string path)
    // #422: a mentés-szemantika parancsai a nézőből — a gazda (Main.qml)
    // ugyanazokat a megerősítéseket nyitja, mint a rácsban
    signal saveRequested(int row)
    signal revertRequested(int row)
    signal undoAllEditsRequested(int row)
    signal resetFacesRequested()
    //: #2566: a Helyek-panel két művelete a nézőből is a GAZDA
    //: megerősítésén megy át — ugyanazok a párbeszédek, mint a
    //: könyvtár-nézetben (`panelClearGeotagDialog`, `setGeotagDialog`).
    signal clearGeotagRequested(var rows)
    signal setGeotagRequested(var rows, real latitude, real longitude)
    //: #2566: a fiók két KIVEZETŐ parancsa. Mindkettő a könyvtár tartalmát
    //: cseréli le (keresés, illetve személy-album), amit a néző eltakarna —
    //: ezért nem a néző hajtja végre, hanem a gazda: az zárja a nézőt, és
    //: utána vált nézetet.
    signal findTaggedRequested(string keyword)
    signal personChosen(string name)

    // #192: a Tulajdonságok-panel a nézőben is — a könyvtár-nézet közös
    // kapcsolóját (Main.qml: window.propertiesPanelOpen) követi. A fő
    // ablakot a Window attached property adja, így a (forró) Main.qml-hez
    // nem kell hozzányúlni; önálló (teszt-)példányosításnál a kapcsoló
    // hiányzik → a panel rejtve marad.
    readonly property var appWindow: Window.window
    readonly property bool propertiesOpen: appWindow
        && appWindow.propertiesPanelOpen === true

    //: #2566: a jobb fiók MÁSIK HÁROM lapja — a #192 mintája szerint. A
    //: négy kapcsolót a képtálca gombjai és a Nézet menü írják, de eddig
    //: csak a Tulajdonságok panelnek volt párja a nézőben; a másik három a
    //: könyvtár `SplitView`-jében ült, amit a néző elrejt, tehát a gomb
    //: benyomódott és nem történt semmi.
    //:
    //: MÉRVE (`thumbui.tre:526`, `:533`): a `right_drawer` a
    //: `mainuipanel` gyereke, és a szerkesztő-módot leíró
    //: `macros.tre:204` (`m_albumtoggle`) TÉTELESEN sorolja fel, mit rejt
    //: el — a `right_drawer` és a `mainuipanel` NINCS köztük. Az
    //: eredetiben tehát a jobb fiók a szerkesztőben is elérhető.
    //:
    //: ⚠️ TERNÁRIUS, nem `&&`: a JS `&&` a HAMIS operandust adja vissza
    //: (itt `null`-t), amit a Qt nem tud bool-ra kötni.
    readonly property bool tagsOpen: viewer.appWindow
        ? viewer.appWindow.tagsPanelOpen === true : false
    readonly property bool placesOpen: viewer.appWindow
        ? viewer.appWindow.placesPanelOpen === true : false
    readonly property bool peopleOpen: viewer.appWindow
        ? viewer.appWindow.peoplePanelOpen === true : false

    //: #2566: a fiók A NÉZETT KÉPRE hat, nem a rács kijelölésére. A néző
    //: léptetése csak a `selectedIndex`-et írja, a `selectedIndexes`-t nem
    //: (Main.qml `onCurrentIndexChanged`), ezért a rács kijelölésére kötött
    //: panel a nézőben elavult képet mutatna.
    readonly property var drawerRows:
        viewer.currentIndex >= 0 ? [viewer.currentIndex] : []

    // #147: csak-olvasás arc-keret overlay — alapból KIKAPCSOLVA (a teljes
    // felismerés/Emberek-panel a #26-ban). currentFaces: FacesHelper.facesFor()
    // eredménye; a photosModel.revision a forgatás-kötés mintájára triggerel
    // újraértékelést; facesHelper hiányában (régi teszt-fixture) üres lista.
    property bool facesVisible: false
    function toggleFaces() { viewer.facesVisible = !viewer.facesVisible }
    // #26 (2. kör): arc-téglalap SZERKESZTŐ mód — rajzolás/átnevezés/
    // törlés a nézőben. A szerkesztés bekapcsolása egyben láthatóvá is
    // teszi a kereteket (nincs értelme vakon szerkeszteni).
    property bool facesEditMode: false
    function toggleFacesEdit() {
        viewer.facesEditMode = !viewer.facesEditMode
        if (viewer.facesEditMode) viewer.facesVisible = true
    }
    // az overlay minden sikeres írás (facesOverlay.edited) után növeli —
    // az ini-módosítást a photosModel/index NEM látja, ez a kényszerített
    // újraértékelés-kapcsoló a facesFor() friss lekérdezéséhez
    property int facesEditRevision: 0
    readonly property var currentFaces: (!viewer.facesVisible || !photosModel
                                          || currentIndex < 0
                                          || typeof facesHelper === "undefined"
                                          || !facesHelper)
        ? []
        : (photosModel.revision, viewer.facesEditRevision,
           facesHelper.facesFor(photosModel.filePathAt(currentIndex)))

    // -- zoom-állapotgép (#6, #2492): fit / 1:1 / tetszőleges ------------
    //
    // ⚠️ #2492: az igazságforrás a NORMALIZÁLT csúszka-érték (`zoomValue`,
    // [0, 1]), nem a szorzó. Ez az eredeti Picasa mért működése
    // (`docs/specs/ui-audit-editor.md`, „A szerkesztő NAGYÍTÁS-HÁRMASA"):
    // a `FUN_005d1c70` a csúszka értékéből választja ki, melyik gomb az
    // aktív, `0.0` = illesztés és `0.5` = valódi méret. Korábban nálunk a
    // csúszka a SZORZÓT tárolta lineárisan (0,25…8), ezért az „1:1" nem
    // a felezőpontra esett — a tulajdonos ezt jelentette (v0.8.293).
    //
    // zoomValue: 0 = illesztés, 0,5 = valódi méret (100 %), 1 = 400 %.
    property real zoomValue: 0
    //: a MÉRT leképezés szerint számolt szorzó az ILLESZTETT mérethez képest
    //: #3013: a KETTŐS NÉZET üzemmódja — `editpanel/layout_2up_group`.
    //: `"1up"` (alapértelmezés, `Property setpressed 1`), `"aa"` (ugyanaz a
    //: kép kétszer: balra a szerkesztés ELŐTTI, jobbra a mai), `"ab"` (két
    //: különböző kép — a #3014 hozza).
    property string layoutMode: "1up"
    //: melyik oldal az aktív — a „Kijelölve" jelvény ezt mutatja
    property string aktivOldal: "jobb"

    readonly property real zoomFactor: viewer.skalaErtekbol(viewer.zoomValue)
    readonly property string zoomMode:
        viewer.zoomValue === 0 ? "fit"
        : viewer.zoomValue === 0.5 ? "actual" : "custom"
    property real panX: 0
    property real panY: 0

    //: #2564: „a fotón értelmezett vezérlők használhatók-e" — EGY helyen
    //: kimondva. Eddig a lebegő `zoomBar` `visible`-je hordozta ezt a
    //: szabályt; a nagyítás-hármas azóta az ALSÓ ESZKÖZSÁVBAN ül
    //: (`TrayBar.qml`), az arc-gombok pedig itt maradtak — a feltételt
    //: ezért a néző GYÖKERÉRŐL kell kiadni, hogy ne íródjon meg kétszer
    //: (#1486 osztálya). A két ág változatlan: videón nincs mit nagyítani
    //: és nincs arc-keret, vágás közben pedig a kép 1:1-re áll vissza.
    readonly property bool photoOverlaysUsable:
        !viewer.isCurrentVideo && !editorPanel.cropActive

    //: #2492: a csúszka BEAKAD a valódi méretnél. `FUN_005d1300`: a
    //: léptetés eredményét a 0,5-höz méri, és az azt átlépő lépés
    //: pontosan ott áll meg.
    readonly property real zoomDetent: 0.5

    //: #2492: a kép VALÓDI képpont-mérete a modellből — a `revision`
    //: referencia miatt képváltáskor és mentés után is újraértékelődik.
    readonly property int valodiSzelesseg: viewer.photosModel
        ? (viewer.photosModel.revision,
           viewer.photosModel.pixelWidthAt(viewer.currentIndex)) : 0
    readonly property int valodiMagassag: viewer.photosModel
        ? (viewer.photosModel.revision,
           viewer.photosModel.pixelHeightAt(viewer.currentIndex)) : 0

    function actualZoomFactor() {
        // Ez a MÉRT képlet `r`-je: a VALÓDI és az ILLESZTETT méret
        // aránya (`docs/specs/ui-audit-editor.md`, „A szerkesztő
        // NAGYÍTÁS-HÁRMASA"). Az eredeti `1to1` buboréksúgója is ezt
        // mondja: „Display Photo at actual size".
        //
        // ⚠️ #2492: KORÁBBAN `photo.sourceSize.width / photo.paintedWidth`
        // állt itt — HIBÁSAN. A Qt olvasáskor a BEÁLLÍTOTT `sourceSize`-t
        // adja vissza, ez az elem pedig 2560-as plafont kap
        // (`sourceSize.width: 2560` lent). Így a képlet a valódi mérettől
        // FÜGGETLENÜL 2560-cal számolt: egy 896 képpont széles képnél
        // ~3,7-es arányt az 1,28 helyett — mérve a tulajdonos
        // képernyőmentésén 3–4-szeres túlnagyítás.
        //
        // ⚠️ A FORGATÁS számít: `iniSteps % 2` esetén a rajzolt szélesség
        // a fájl MAGASSÁGÁNAK felel meg.
        if (photo.paintedWidth <= 0)
            return 1
        var forgatott = photo.iniSteps % 2 !== 0
        var vSzel = forgatott ? viewer.valodiMagassag : viewer.valodiSzelesseg
        if (vSzel > 0)
            return vSzel / photo.paintedWidth
        // Tartalék, ha az index nem tud méretet adni (frissen felvett kép,
        // vagy olvashatatlan fejléc): a BETÖLTÖTT raszter mérete. Ez a
        // `sourceSize`-plafon miatt legfeljebb kisebb lehet a valódinál —
        // tehát a nagyítás legrosszabb esetben kevesebb, sosem több.
        // NEM a `sourceSize`: az a beállított plafont adná vissza.
        return photo.implicitWidth > 0
            ? photo.implicitWidth / photo.paintedWidth : 1
    }

    //: A MÉRT leképezés (`0x00a601cf`–`0x00a60221`), két folytonos ágon:
    //:
    //:   0 ≤ v < 0,5 :  1 + (2^(2v) − 1) · (r − 1)
    //:   0,5 ≤ v ≤ 1 :  r · 2^(4·(v − 0,5))
    //:
    //: Rögzített pontok: v=0 → 1 (illesztés), v=0,5 → r (100 %),
    //: v=1 → 4r (400 %). A felső fél negyedenként pontosan duplázódik.
    function skalaErtekbol(v) {
        var r = viewer.actualZoomFactor()
        var t = Math.max(0, Math.min(1, v))
        return t < 0.5
            ? 1 + (Math.pow(2, 2 * t) - 1) * (r - 1)
            : r * Math.pow(2, 4 * (t - 0.5))
    }

    function setZoomValue(v) {
        // ⚠️ MÉRT vágás [0, 1]-re (`0x005d13a9` fldz / `0x005d13c6` fld1):
        // az illesztettnél kisebbre és a 400 %-nál nagyobbra nem lehet
        // állítani.
        viewer.zoomValue = Math.max(0, Math.min(1, v))
        if (viewer.zoomValue === 0) { panX = 0; panY = 0 }
        clampPan()
    }
    function zoomFit() { setZoomValue(0); panX = 0; panY = 0 }
    function zoomActual() { setZoomValue(viewer.zoomDetent) }

    //: #2492: a léptető út a 0,5-ös beakadással. Ha az érték MÁR pontosan
    //: a detenten áll, a lépés elmozdítja (`0x005d1383` — ugyanabban a
    //: lépésben nem mozdul el, tehát a következő lépés viszi tovább).
    function lepjZoom(delta) {
        var regi = viewer.zoomValue
        var uj = Math.max(0, Math.min(1, regi + delta))
        if (regi !== viewer.zoomDetent
                && (regi - viewer.zoomDetent) * (uj - viewer.zoomDetent) < 0)
            uj = viewer.zoomDetent
        setZoomValue(uj)
    }

    //: az egérgörgő egy „kattanása" (120 egység) a csúszka 1/20-a — a
    //: lépésköz a MI választásunk, a beakadás és a vágás a mért.
    function wheelZoom(delta) { lepjZoom((delta / 120) * 0.05) }
    // a kép széle ne szakadjon el a látótértől pásztázáskor
    function clampPan() {
        var w = (photo.iniSteps % 2 ? photo.paintedHeight
                                    : photo.paintedWidth) * zoomFactor
        var h = (photo.iniSteps % 2 ? photo.paintedWidth
                                    : photo.paintedHeight) * zoomFactor
        var maxX = Math.max(0, (w - photoArea.width) / 2)
        var maxY = Math.max(0, (h - photoArea.height) / 2)
        panX = Math.max(-maxX, Math.min(maxX, panX))
        panY = Math.max(-maxY, Math.min(maxY, panY))
    }

    function show(index) { currentIndex = index; forceActiveFocus() }

    // Vágás alkalmazása a kijelölésből. advance=true: Enter-flow —
    // következő kép, vágó-mód megtartva; false: Alkalmaz gomb — a panel
    // visszaáll az eszközrácsra (Picasa-viselkedés).
    function applyCrop(advance) {
        if (!cropOverlay.hasSelection) {
            if (!advance) editorPanel.cropActive = false
            return
        }
        var r = cropOverlay.cropRect
        editController.applyCrop(r.x, r.y, r.width, r.height)
        cropOverlay.resetSelection()
        if (advance) viewer.next()
        else editorPanel.cropActive = false
    }

    // -- szerkesztés (#19): EditController-életciklus --------------------
    // A nézőbe lépés = szerkesztési munkamenet az aktuális képre; kilépéskor
    // a munkamenet zárul. A panel kapcsoló-állapotait az EditController
    // igazságforrásából szinkronizáljuk (a kötést a panel belső átírása
    // megtörné, ezért imperatív sync a toolsChanged-re).
    function beginEditCurrent() {
        if (!(visible && currentIndex >= 0 && photosModel)) return
        // #218: a viewer.isCurrentVideo egy kötött property — a currentIndex
        // váltásakor NEM garantált, hogy már újraértékelődött, mire ez a
        // (szintén a currentIndexChanged-re futó) imperatív függvény lefut,
        // ezért a modellt itt KÖZVETLENÜL kérdezzük le (mindig friss),
        // nem a cache-elt property-t
        if (photosModel.isVideoAt(currentIndex)) {
            // videón nincs képszerkesztés (#14) — az előző kép nyitott
            // munkamenete záruljon, ne lógjon át az előnézete
            editController.endEdit()
            return
        }
        editController.beginEdit(photosModel.idAt(currentIndex),
                                 photosModel.filePathAt(currentIndex))
    }
    // #1598: a megjelenítési mód (`Nézet ▸ Megjelenítési mód`) KIZÁRÓLAG az
    // `editpreview` szolgáltatón át jut a képernyőre. A lenti `photo.source`
    // kötés viszont a NYERS fájl URL-jére esik vissza, ha nincs élő
    // szerkesztési munkamenet (`editCtl.previewSource` üres) — a nyers fájlon
    // pedig a mód nem látszik. Mérve (#1598, a kirajzolt képpontokon): ilyen
    // állapotban a módváltás NÉMÁN elveszik, vagyis a felület olyat kínál,
    // ami nem hat. A tulajdonos jelentése („egyáltalán nem működik egyik
    // sem") pontosan ilyen alakú.
    //
    // A `beginEditCurrent()` a néző megnyitásakor és lapozáskor amúgy is
    // lefut, tehát a visszaesés a rendes úton nem áll elő; a munkamenetet
    // viszont kívülről is le lehet zárni (`endEdit`), és a felhasználó
    // ilyenkor is a menüből vált módot. Ezért a váltás pillanatában
    // ÚJRANYITJUK a munkamenetet, ahelyett hogy a nyers fájl elnyelné.
    //
    // Nem tud körbe járni: a `beginEdit` után a `previewSource` nem üres, a
    // `displayModeChanged` pedig csak VALÓDI módváltásnál szól (ld.
    // `display_mode_controller.py` modul-docstring). Videón nem fut le — ott
    // a fotó-Image rejtett, és a `beginEditCurrent()` is `endEdit`-et hív.
    Connections {
        target: typeof controller !== "undefined" ? controller : null
        function onDisplayModeChanged() {
            if (viewer.visible && !viewer.isCurrentVideo
                    && viewer.editCtl && viewer.editCtl.previewSource === "")
                viewer.beginEditCurrent()
        }
    }

    // Döntés-csúszka szinkronja a mentett tilt-értékkel (#131): a value
    // beállítását elnyomjuk, hogy az onValueChanged NE váltson ki
    // previewTilt-et — a szinkron csak a csúszkát mozgatja, az előnézet
    // már a beginEditCurrent()/_register_preview() óta helyes.
    function syncTiltSlider() {
        tiltSlider.suppressPreview = true
        tiltSlider.value = editController.tiltParam
        tiltSlider.suppressPreview = false
        // #448: a Kiegyenesítés-figyelmeztetés a vágó-panelen — a
        // tiltParam a mentett döntés-paraméter, 0.0 = nincs aktív tilt
        editorPanel.straightenActive = editController.tiltParam !== 0
    }
    function syncPanelFromController() {
        // #445: a panel `redeyeActive`-ja a Vágás/Retusálás mintájára
        // ESZKÖZ-nyitást jelent (nem a `redeye` réteg meglétét) — ezért NEM
        // a vezérlő `hasSavedRedeye`-jének tükre; azt onnan felülírni
        // becsukná/kinyitná a panelt a mentett lánc alapján.
        // #2393: a vezérlő tagja korábban szintén `redeyeActive` volt — a
        // névazonosság félrevitte a #1485-öt, ezért kapott beszédes nevet.
        // #448: a tilt-szűrő a láncban változhatott (pl. a felhasználó
        // épp most alkalmazta a Kiegyenesítést) — a figyelmeztetés kövesse
        editorPanel.straightenActive = editController.tiltParam !== 0
        // egygombos javítások (#116): "nyomható-e" tükrözése — a gomb
        // tiltott, amíg ugyanez a szűrő a lánc utolsó eleme
        editorPanel.enhanceEnabled = editController.enhanceEnabled
        editorPanel.autolightEnabled = editController.autolightEnabled
        editorPanel.autocolorEnabled = editController.autocolorEnabled
        // Finomhangolás-csúszkák (#20): a panel binding már frissítette a
        // fillLight/highlights/shadows/colorTemp értékeket a kontrollerből —
        // ez a hívás azokat suppress mellett a csúszkákba is beírja
        editorPanel.syncFinetuneSliders()
        // #450: "Remove all existing text" gomb tiltási állapota
        editorPanel.hasTextOverlay = editController.hasTextOverlay
        // #450: szöveg-stílus — kitöltés+körvonal szín, körvonal-vastagság,
        // kitöltés ki/be, átlátszóság
        // #464: a Finomhangolás fül pipettája melletti színminta
        editorPanel.neutralColor = editController.neutralColor
        editorPanel.textFillColor = editController.textFillColor
        editorPanel.textOutlineColor = editController.textOutlineColor
        editorPanel.textOutlineThickness = editController.textOutlineThickness
        editorPanel.textFillEnabled = editController.textFillEnabled
        editorPanel.textOpacity = editController.textOpacity
        // #450 (2. lépcső): tipográfia — betűcsalád, méret, B/I/U, igazítás
        editorPanel.fontFamilyCatalogue = editController.textFontFamilies
        editorPanel.textFontFamily = editController.textFontFamily
        editorPanel.textFontSize = editController.textFontSize
        editorPanel.fontSizeChoices = editController.fontSizeChoices
        editorPanel.textBold = editController.textBold
        editorPanel.textItalic = editController.textItalic
        editorPanel.textUnderline = editController.textUnderline
        editorPanel.textAlign = editController.textAlign
    }
    onVisibleChanged: {
        if (visible) {
            zoomFit()   // #6: minden belépés illesztett nézetben indul
            beginEditCurrent()
        } else {
            // a cropActive/retouchActive/textActive lenullázása ELŐBB (még
            // aktív szerkesztés alatt) fut, hogy az onXActiveChanged->
            // exitXTool() még érvényes munkameneten hívódjon; utána zárja
            // az endEdit()
            editorPanel.cropActive = false
            editorPanel.tiltActive = false
            editorPanel.retouchActive = false
            editorPanel.textActive = false
            editorPanel.redeyeActive = false
            editController.endEdit()
        }
    }
    onCurrentIndexChanged: {
        if (visible) {
            zoomFit()   // #6: lapozáskor vissza illesztett nézetbe
            beginEditCurrent()
            // lapozáskor a csúszka az ÚJ kép mentett tilt-értékére áll —
            // suppressPreview miatt ez nem írja felül a preview-t (#131)
            syncTiltSlider()
            // ugyanígy a Finomhangolás-csúszkák is az új kép mentett
            // értékeire állnak (#20)
            editorPanel.syncFinetuneSliders()
            if (editorPanel.cropActive) {
                editController.enterCropTool()
                cropOverlay.loadSelection(editController.cropSelection)
            } else {
                cropOverlay.resetSelection()
            }
            // #148: a Retusálás/Szöveg mód lapozáson át is megtartható —
            // az új képhez újra kell nyitni (a puffer/piszkozat az ÚJ kép
            // mentett állapotával indul, a Vágás mintáját követve)
            if (editorPanel.retouchActive)
                editController.enterRetouchTool()
            if (editorPanel.redeyeActive)
                editController.enterRedeyeTool()
            if (editorPanel.textActive) {
                editController.enterTextTool()
                editorPanel.textDraftContent = editController.textDraft
            }
        }
    }
    Connections {
        target: editController
        function onToolsChanged() { viewer.syncPanelFromController() }
    }
    // Vágás eszköz nyitása/zárása (#71): nyitáskor a lánc crop64 nélküli
    // (teljes, vágatlan) előnézete + a meglévő kijelölés betöltése; záráskor
    // (Mégse) a rendes, crop64-et is tartalmazó előnézet visszaáll
    Connections {
        target: editorPanel
        function onCropActiveChanged() {
            if (editorPanel.cropActive) {
                viewer.zoomFit()   // #6: a vágó-overlay illesztett nézetet vár
                editController.enterCropTool()
                cropOverlay.loadSelection(editController.cropSelection)
            } else {
                editController.exitCropTool()
            }
        }
        // #148: a Retusálás/Szöveg mód nyitása/zárása — a Vágás mintáját
        // követve az enter/exit a puffer/piszkozat élő előnézetét kezeli,
        // Alkalmazásig nem ír inibe.
        function onRetouchActiveChanged() {
            if (editorPanel.retouchActive)
                editController.enterRetouchTool()
            else
                editController.exitRetouchTool()
        }
        // #445: a Vörösszem eszköz nyitása/zárása — nyitáskor az automatika
        // AZONNAL lefut az előnézeten (enterRedeyeTool), a kézi téglalapok
        // pedig az Alkalmazásig csak a pufferben élnek.
        function onRedeyeActiveChanged() {
            if (editorPanel.redeyeActive)
                editController.enterRedeyeTool()
            else
                editController.exitRedeyeTool()
        }
        function onTextActiveChanged() {
            if (editorPanel.textActive) {
                editController.enterTextTool()
                editorPanel.textDraftContent = editController.textDraft
            } else {
                editController.exitTextTool()
            }
        }
    }
    // A lapozás a #84 óta a modell mappán-belüli lépését használja: a
    // rács (feed) nézet mappaátlépő listáin (csillag-szűrő, keresés) sem
    // ugorhatunk át a szomszéd mappába — a folderNeighbor a saját mappa
    // határán a jelenlegi indexet adja vissza, tehát nem lép tovább.
    function next() {
        if (!photosModel) return
        currentIndex = photosModel.folderNeighbor(currentIndex, 1)
    }
    function previous() {
        if (!photosModel) return
        currentIndex = photosModel.folderNeighbor(currentIndex, -1)
    }
    // a ◀/▶ gombok (és Keys.onLeft/Right) enabled-je is a mappahatárt
    // tükrözi: nincs hova lépni, ha a folderNeighbor helyben marad
    function hasNext() {
        return photosModel
            ? photosModel.folderNeighbor(currentIndex, 1) !== currentIndex
            : false
    }
    function hasPrevious() {
        return photosModel
            ? photosModel.folderNeighbor(currentIndex, -1) !== currentIndex
            : false
    }
    // Egérgörgős lapozás (#77): a nagy nézőben a görgő a képek között
    // lép (Picasa-viselkedés). A touchpad kis deltáit egy teljes
    // görgő-fokozatig (120) gyűjtjük, hogy ne ugráljon több képet.
    property real wheelAccum: 0
    function wheelStep(delta) {
        wheelAccum += delta
        while (wheelAccum <= -120) { wheelAccum += 120; next() }
        while (wheelAccum >= 120) { wheelAccum -= 120; previous() }
    }
    function urlAt(index) {
        return photosModel ? photosModel.fileUrlAt(index) : ""
    }
    // elő-betöltéshez: videót NEM adunk az Image-nek (#14) — a képként
    // dekódolás hibát logolna, a videó elő-betöltése nem a mi dolgunk
    function preloadUrlAt(index) {
        if (!photosModel || photosModel.isVideoAt(index)) return ""
        return urlAt(index)
    }

    focus: visible
    // Az Esc az AKTÍV mód-eszközt szakítja meg, és csak ha nincs ilyen,
    // akkor zárja a nézőt — ez az eredeti Picasa viselkedése.
    //
    // #445: a retusálás félbehagyott foltját dobja el (a súgószöveg
    // szerinti irányított klónozás megszakítása).
    // #666: a vágást ugyanúgy meg kell szakítania, mint a panel Mégse
    // gombjának — korábban a néző BEZÁRULT, és a megkezdett vágás elveszett.
    //
    // A logika külön függvényben él, hogy tesztelhető legyen; a billentyű-
    // kötés csak továbbhív (a `test_viewer_escape_666.py` mindkettőt őrzi).
    function handleEscape() {
        if (editorPanel.retouchActive && editorPanel.retouchPatchPending)
            editController.cancelRetouchPatch()
        else if (editorPanel.cropActive)
            editorPanel.cropCancelRequested()
        else
            viewer.closed()
    }
    Keys.onEscapePressed: viewer.handleEscape()
    Keys.onRightPressed: next()
    Keys.onReturnPressed: next()
    Keys.onLeftPressed: previous()
    // szóköz: videónál lejátszás/szünet (#14) — Picasa-viselkedés
    Keys.onSpacePressed: {
        if (viewer.isCurrentVideo && videoLoader.item)
            videoLoader.item.togglePlayback()
    }
    // F: arc-keretek be/ki (#147) — szövegmezőben (pl. felirat) a saját
    // Keys-kezelés (gépelés) már elfogadja, ide nem buborékol.
    // Shift+F: arc-SZERKESZTŐ mód be/ki (#26, 2. kör).
    //
    // #1418: a törlés a nézőben — akárcsak a rácsban — Ctrl+Delete (a
    // helyi menük rekordjai, docs/specs/picasa-gyorsbillentyuk.md 4.).
    // Ugyanazt az utat hívja, mint a jobbklikk-menü "Törlés lemezről"
    // tétele (onDeleteRequested lent).
    //
    // A `Main.qml` `shortcutDeleteFromDiskViewer`-e ezzel egy irányba
    // mutat: ott is `Ctrl+Delete` (#1418). A korábbi, puszta `Delete`
    // a #422 azóta felülírt feltételezéséből jött.
    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_F && event.modifiers === Qt.NoModifier) {
            viewer.toggleFaces()
            event.accepted = true
        } else if (event.key === Qt.Key_F && event.modifiers === Qt.ShiftModifier) {
            viewer.toggleFacesEdit()
            event.accepted = true
        } else if (event.key === Qt.Key_Delete
                   && event.modifiers === Qt.ControlModifier) {
            if (viewer.currentPath.length > 0)
                viewer.deleteRequested(viewer.currentPath)
            event.accepted = true
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // felső sáv: vissza gomb + filmszalag nyilakkal
        Rectangle {
            id: viewerTopBar
            objectName: "viewerTopBar"
            Layout.fillWidth: true
            height: 46
            color: Theme.chromeBg
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8; anchors.rightMargin: 8
                spacing: 8
                // #1993: a MÉRT alak — ikonos, KÉTSOROS gomb.
                //
                // Az ikon az `editpanel/albumview_icon` (17 × 15), színe a
                // sprite domináns kékje, `#5A7BBB`. A felirat a felvételen
                // két sorban áll („Vissza a / könyvtárhoz"), ezért a gomb
                // szélessége kötött — a `PicasaButton` maga tördel (#992).
                //
                // ⚠️ A `◀` glif KIESETT: az ikon váltja ki, nem mellette
                // áll. A tesztek erre külön állítást tesznek.
                PicasaButton {
                    objectName: "viewerBackButton"
                    font.pixelSize: Theme.fontSize
                    text: qsTr("Back to Library")
                    Layout.preferredWidth: 118
                    Layout.preferredHeight: 34
                    leftPadding: 30
                    onClicked: viewer.closed()
                    Image {
                        objectName: "viewerBackIcon"
                        source: "icons/viewer-back-arrow.svg"
                        width: 17; height: 15
                        sourceSize.width: 17; sourceSize.height: 15
                        anchors.left: parent.left
                        anchors.leftMargin: 7
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                // #1002 — `editpanel/editcollage`. Az eredetiben `m_hidden`:
                // alapból REJTETT, és csak akkor jön elő, ha a megnyitott
                // képnek van kollázs-projektfájlja. A tulajdonos szava:
                // „Ez a gomb mindig megjelenik, ha megnyitom a kollázst."
                //
                // ⚠️ NEM azonos a `collagepanel::back_to_collage` =
                // „Vissza a kollázshoz" gombbal: az a KÖNYVTÁR lapján áll,
                // és a félbehagyott kollázshoz visz vissza.
                PicasaButton {
                    id: kollazsSzerkesztes
                    objectName: "viewerEditCollageButton"
                    //: `editpanel/editcollage-label`
                    text: qsTr("Edit Collage")
                    font.pixelSize: Theme.fontSize
                    //: `editpanel/editcollage` elemleírása
                    ToolTip.text: qsTr(
                        "Edit the collage from which this image was created")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    //: A null-őr a #305 szabálya: a vezérlő a lebontáskor és a
                    //: komponens-teszteknél hiányozhat (ld. a `viewer`
                    //: gyökerén a `controllerReady`-t).
                    //: #1072: a PISZKOZATON is látszik — a spec 6. szakasza
                    //: és a tulajdonos képernyőképe szerint a visszaút a
                    //: befejezetlen kollázsról is nyitva áll.
                    visible: viewer.currentIsSavedCollage
                             || viewer.currentIsCollageDraft
                    onClicked: viewer.editCollageRequested(viewer.currentFilePath)
                }
                Item { Layout.fillWidth: true }
                //: #3013: a kettős nézet háromszegmenses kapcsolója
                //: (`editpanel/layout_2up_group`), a mért sorrendben és a
                //: hivatalos magyar buboréksúgókkal.
                Row {
                    objectName: "viewerLayoutGroup"
                    spacing: 1
                    LayoutSegment {
                        objectName: "viewerLayoutOnly1up"
                        nezo: viewer
                        mod: "1up"
                        jel: "▭"
                        sugo: qsTr("Show only one picture")
                    }
                    LayoutSegment {
                        objectName: "viewerLayoutAa"
                        nezo: viewer
                        mod: "aa"
                        jel: "▯▯"
                        sugo: qsTr("Show the same picture twice")
                    }
                    LayoutSegment {
                        objectName: "viewerLayoutAb"
                        nezo: viewer
                        mod: "ab"
                        jel: "▯▮"
                        sugo: qsTr("Show two different pictures")
                        //: a #3014 hozza — addig LÁTHATÓ, de tiltott: a
                        //: néma no-op rosszabb volna, mert a felhasználó
                        //: nem tudná, hogy nem működik
                        enabled: false
                    }
                }

                //: #3013: `swap_2up_focus` — csak 2-up módban látszik
                LayoutSegment {
                    objectName: "viewerSwapFocus"
                    nezo: viewer
                    mod: ""
                    jel: "⇄"
                    sugo: qsTr("Switch focus between the pictures")
                    visible: viewer.layoutMode !== "1up"
                    function kattints() {
                        viewer.aktivOldal =
                            viewer.aktivOldal === "jobb" ? "bal" : "jobb"
                    }
                }

                PicasaButton {
                    objectName: "viewerPlayButton"
                    text: "▶ " + qsTr("Play")
                    font.pixelSize: Theme.fontSize
                    //: #1857: ehhez a négy gombhoz (lejátszás, előző,
                    //: következő, „Létrehozás most") NINCS kimért eredeti
                    //: felirat — a szöveg SAJÁT, leíró magyar, a mért
                    //: testvérek hangnemében. Ez tudatos eltérés.
                    ToolTip.text: qsTr("Start slideshow")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.playRequested()
                }
                // #1993: a MÉRT léptető — 30 × 31, KÖR alakú rajz.
                //
                // A kör alakot a `globalbuttons/lfs_n` sprite soronkénti
                // látható szélessége bizonyítja (…29, 30, 30, 30, 30, 30,
                // 30, 30, 29…) — korong, nem lekerekített téglalap.
                //
                // ⚠️ A jegy „kör alakú, KÉK" nyilakat írt. A kör igaz, a
                // kék NEM: a sprite és a felvétel is `#5C`–`#5F` szürkét
                // ad. A KÉK a „Vissza a könyvtárhoz" gomb nyila
                // (`#5A7BBB`) — két különböző elem.
                PicasaButton {
                    objectName: "viewerPrevButton"
                    //: #885: a kép-léptetés LENYOMÁSRA hat az eredetiben
                    //: (`oneup/prev`, `oneup/next` — `Property mousedown 1`).
                    lenyomasra: true
                    onClicked: viewer.previous()
                    enabled: viewer.hasPrevious()
                    Layout.preferredWidth: 30
                    Layout.preferredHeight: 31
                    width: 30; height: 31
                    padding: 0
                    background: null
                    contentItem: Item {
                        Image {
                            objectName: "viewerPrevIcon"
                            source: "icons/viewer-step-left.svg"
                            width: 30; height: 31
                            sourceSize.width: 30; sourceSize.height: 31
                            anchors.centerIn: parent
                        }
                    }
                    ToolTip.text: qsTr("Previous picture")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
                // #1905: a szalag CSAK a jelenlegi kép mappáját mutatja.
                //
                // Eddig a teljes rács-modellt listázta. A rács viszont
                // FEED: több mappa fotóit sorolja fel egymás után, a
                // csillag-szűrő és a keresés pedig végképp vegyít. A
                // tulajdonos ezért egy ötképes mappa szerkesztésekor
                // NYOLC elemet látott — köztük egy MÁSIK mappa
                // kollázs-képeit. Az eredetiben (egymás mellé tett
                // felvétel ugyanazon a mappán) pontosan a mappa képei
                // állnak itt.
                //
                // Ugyanaz a szerződés, mint a ◀/▶ léptetésé (#84,
                // `folderNeighbor`): a mappa fotói folytonos tartományt
                // alkotnak, tehát elég a kezdet és a darabszám.
                ListView {
                    id: filmstrip
                    objectName: "viewerFilmstrip"

                    //: [kezdet, darab] — a `revision` a modell-változásra köt
                    readonly property var mappaSav: (viewer.photosModel
                        && viewer.currentIndex >= 0)
                        ? (viewer.photosModel.revision,
                           viewer.photosModel.folderRowRange(viewer.currentIndex))
                        : [0, 0]
                    readonly property int mappaKezdet: mappaSav[0]
                    readonly property int mappaDarab: mappaSav[1]

                    Layout.preferredWidth: Math.min(7, mappaDarab) * 44
                    Layout.preferredHeight: 38
                    orientation: ListView.Horizontal
                    model: mappaDarab
                    currentIndex: viewer.currentIndex - mappaKezdet
                    highlightMoveDuration: 100
                    clip: true
                    delegate: Rectangle {
                        required property int index
                        //: a rács-modell VALÓDI sora (a mappa-eltolással)
                        readonly property int racsSor: filmstrip.mappaKezdet + index
                        width: 42; height: 38
                        color: racsSor === viewer.currentIndex
                               ? Theme.thumbSelection : "transparent"
                        Image {
                            anchors.fill: parent
                            anchors.margins: 2
                            source: viewer.photosModel
                                ? viewer.photosModel.thumbUrlAt(parent.racsSor)
                                : ""
                            // #1600: a bélyegkép-textúra a Qt gyorsítótárában KÖZÖS a
                            // ráccsal, ami mipmapot kér (#83). Eltérő beállítás mellett a
                            // Qt „Mipmap settings changed” figyelmeztetést ad, és
                            // VISSZAESIK a korábbi szűrésre — a kép nem azzal a szűréssel
                            // jelenik meg, amit kértünk (Windowson hatszor egy futásban).
                            smooth: true
                            mipmap: true
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: Qt.platform.pluginName !== "offscreen"
                        }
                        TapHandler {
                            onTapped: viewer.currentIndex = parent.racsSor
                        }
                    }
                }
                PicasaButton {
                    objectName: "viewerNextButton"
                    //: #885: a kép-léptetés LENYOMÁSRA hat az eredetiben
                    //: (`oneup/prev`, `oneup/next` — `Property mousedown 1`).
                    lenyomasra: true
                    onClicked: viewer.next()
                    enabled: viewer.hasNext()
                    Layout.preferredWidth: 30
                    Layout.preferredHeight: 31
                    width: 30; height: 31
                    padding: 0
                    background: null
                    contentItem: Item {
                        Image {
                            objectName: "viewerNextIcon"
                            source: "icons/viewer-step-right.svg"
                            width: 30; height: 31
                            sourceSize.width: 30; sourceSize.height: 31
                            anchors.centerIn: parent
                        }
                    }
                    ToolTip.text: qsTr("Next picture")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
                Item { Layout.fillWidth: true }
                // #6: A/AB/AA összehasonlító nézetek — placeholder (a
                // szerkesztő-összevetés a 2. fázisban élesedik)
                //
                // ⚠️ #1857: a buboréksúgó szövege KI VAN TÉVE, de amíg a
                // gomb `enabled: false`, a Qt nem ad neki `hovered`-et,
                // tehát a felhasználó nem látja. Ez nem hiba: a #434
                // élesítésekor a súgó magától megjelenik, és a mért
                // eredeti szöveg addig sem vész el.
                PicasaButton {
                    objectName: "compareButtonA"
                    text: "A"; enabled: false
                    Layout.preferredWidth: 28
                    //: Az eredeti `only_1up_toggle` felirata.
                    ToolTip.text: qsTr("View only one image")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
                PicasaButton {
                    objectName: "compareButtonAB"
                    text: "AB"; enabled: false
                    Layout.preferredWidth: 32
                    ToolTip.text: qsTr("View two different images")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
                PicasaButton {
                    objectName: "compareButtonAA"
                    text: "AA"; enabled: false
                    Layout.preferredWidth: 32
                    ToolTip.text: qsTr("View the same image twice")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // bal eszközpanel — Gyakori javítások élesben (#19); a
            // Retusálás/Szöveg és a finomhangolás a #20-ban élesedik
            Rectangle {
                id: leftDrawer
                objectName: "viewerLeftDrawer"
                // #411: az EditorPanel.qml implicitWidth-ével összhangban —
                // FIX 280px, nem ablakarányos (ld. az ottani kommentet)
                Layout.preferredWidth: 280
                Layout.fillHeight: true
                // #641: itt NINCS `Layout.minimumHeight`. A #628 azt tette ide,
                // de az visszafelé sült el: a doboz nem zsugorodott a cellára,
                // hanem TÚLNYÚLT rajta, és a panel aljához igazodó
                // Visszavonás/Újra sor kicsúszott a képernyőről. A „mindig
                // elfér" garanciát az ABLAK minimális magassága adja
                // (`Main.qml`, a `viewer.requiredHeight`-ből) — ha az mégsem
                // tartható, a doboz zsugorodik, és a fül TARTALMA veszít, nem
                // a gombsor.
                color: Theme.chromeBg

                EditorPanel {
                    id: editorPanel
                    objectName: "viewerEditorPanel"
                    // videónál a szerkesztő-eszközök nem értelmezettek (#14)
                    enabled: !viewer.isCurrentVideo
                    // #628: a panel a RENDELKEZÉSRE ÁLLÓ magasságot kapja.
                    // Korábban itt fix 420 képpont állt, akármekkora az
                    // ablak — a 3. fül 12 bélyegképes csempéje (3×4, ≈450
                    // px) ebbe soha nem fért bele, ezért lett a görgetés az
                    // alapállapot, és ezért lógott rá a gombsor a
                    // csempékre. A szülő `Layout.fillHeight: true`, tehát a
                    // hely rendelkezésre áll.
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left; anchors.right: parent.right
                    imageAspect: photo.paintedHeight > 0
                                 ? photo.paintedWidth / photo.paintedHeight
                                 : 4 / 3
                    // Visszavonás/Újra — a controller undo-verméből (#59).
                    // #465: a KÉSZ feliratot a controller adja
                    // (`edit_action_names` névtár), hogy a lánc minden
                    // eleme néven nevezhető legyen — a korábbi, itteni
                    // `switch` csak egy tucat effektet ismert, a többinél a
                    // nyers ini-kulcs került a gombra.
                    // #305: null-őr
                    undoAvailable: viewer.editCtl ? viewer.editCtl.canUndo : false
                    undoLabel: viewer.editCtl ? viewer.editCtl.undoLabel : qsTr("Undo")
                    redoAvailable: viewer.editCtl ? viewer.editCtl.canRedo : false
                    redoLabel: viewer.editCtl ? viewer.editCtl.redoLabel : qsTr("Redo")
                    // Finomhangolás (#20): a mentett értékek a kontrollerből —
                    // a syncFinetuneSliders() ezekből tölti a csúszkákat
                    fillLight: viewer.editCtl ? viewer.editCtl.fillLight : 0
                    highlights: viewer.editCtl ? viewer.editCtl.highlights : 0
                    shadows: viewer.editCtl ? viewer.editCtl.shadows : 0
                    colorTemp: viewer.editCtl ? viewer.editCtl.colorTemp : 0
                    // GPU élő-előnézet (#22): amíg a lánc GPU-alkalmas ÉS
                    // van RHI, a húzás a LUT-only gyors utat hívja (a
                    // `GpuPointFilterPreview` réteg jelenik meg a `photo`
                    // fölött) — máskülönben (nincs GPU, vagy a lánc nem
                    // GPU-alkalmas) a rendes, teljes CPU-előnézet fut,
                    // változatlanul.
                    onFinetunePreview: (f, h, s, t) => {
                        // #551: a Derítőfény MÉRT modellje a pixel
                        // VILÁGOSSÁGÁTÓL függ, tehát nem csatornánkénti
                        // LUT — a GPU pontonkénti útja csak f === 0 esetén
                        // adja pontosan ugyanazt a képet, mint a CPU.
                        viewer.gpuFinetuneActive = true
                        viewer.gpuFinetunePointSafe = (f === 0)
                        if (viewer.gpuFinetuneEligible && f === 0)
                            editController.previewFinetuneGpu(f, h, s, t)
                        else
                            editController.previewFinetune(f, h, s, t)
                    }
                    onFinetuneCommit: (f, h, s, t) => {
                        // a húzás végén MINDIG a normál CPU-út menti — az
                        // igazságforrás sosem a GPU-réteg (ld. #22 jegy)
                        viewer.gpuFinetuneActive = false
                        viewer.gpuFinetunePointSafe = true
                        editController.setFinetune(f, h, s, t)
                    }
                    onEffectRequested: (name) => editController.applyEffect(name)
                    // #551: a szín-varázspálca a finetune2 p4 mezőjét írja
                    onColorWandRequested: editController.applyColorWand()
                    onToolActivated: function(tool) {
                        // crop/tilt/retouch/text helyi mód (overlay/
                        // csúszka/kattintás-puffer); a többi azonnali
                        // ini-művelet az EditControlleren át
                        if (tool === "tilt") {
                            // eszköz-nyitáskor a csúszka a MENTETT
                            // tilt-értékről induljon, ne 0-ról (#131)
                            if (editorPanel.tiltActive)
                                viewer.syncTiltSlider()
                        } else if (tool === "crop" || tool === "retouch"
                                   || tool === "text" || tool === "redeye") {
                            // az enter/exit a Connections{target: editorPanel}
                            // blokk onXActiveChanged kezelőiben történik
                        } else {
                            editController.toggleTool(tool)
                        }
                    }
                    // #465: a retus és a vörösszem RÉGIÓ-ADATOT hordoz, és a
                    // visszavonás eldobja — az „Újra" nem hozza vissza.
                    // Az eredeti Picasa ezért külön rákérdez
                    // (IDS_CONFIRM_UNDO_RETOUCH / IDS_CONFIRM_UNDO_REDEYE).
                    onUndoRequested: {
                        var action = editController.undoAction
                        if (action === "retouch")
                            undoDataLossDialogLoader.ensure().askFor("retouch", qsTr(
                                "Retouch fixes cannot be recovered with redo."
                                + " Are you sure you want to undo?"))
                        else if (action === "redeye")
                            undoDataLossDialogLoader.ensure().askFor("redeye", qsTr(
                                "Redeye fixes cannot be recovered with redo."
                                + " Are you sure you want to undo?"))
                        else
                            editController.undo()
                    }
                    onRedoRequested: editController.redo()
                    onCropRotateRequested: {
                        // rögzített aránynál a fekvő↔álló kapcsoló forgat
                        // (a kijelölés az arány-követéssel formálódik át);
                        // kézi aránynál közvetlenül a kijelölést forgatjuk
                        if (editorPanel.currentAspect > 0)
                            editorPanel.aspectRotated =
                                !editorPanel.aspectRotated
                        else
                            cropOverlay.swapSelectionOrientation()
                    }
                    // arány-választás/Forgatás: a meglévő kijelölés kövesse,
                    // és a #448-as javaslatok is a KIVÁLASZTOTT arányban
                    // szülessenek (egyetlen kezelő — a QML-ben nem lehet
                    // két azonos nevű jel-kezelő ugyanazon az objektumon)
                    onCurrentAspectChanged: {
                        if (cropOverlay.hasSelection
                            && editorPanel.currentAspect > 0)
                            cropOverlay.applyAspect(editorPanel.currentAspect)
                        if (viewer.editCtl)
                            viewer.editCtl.setCropAspect(editorPanel.currentAspect)
                    }
                    onQuickCropRequested: (kind) => cropOverlay.selectPreset(kind)
                    onCropPreviewHold: (held) => cropOverlay.previewHold = held
                    // #1528: az „Alaphelyzet” az ALKALMAZOTT vágást veti
                    // el, nem csak a húzott kijelölést. A szemantika NEM
                    // következtetés: az eredeti Picasa saját szövegforrása
                    // mondja ki — `editpanel/cropdiscard` buboréksúgója
                    // „Discards any applied cropping” (editpaneltext.tre
                    // 234–235), magyarul „Az összes alkalmazott vágás
                    // elvetése” (panel-feliratok-hu.tsv 4982).
                    //
                    // A vágás nem vész el: a `clearCrop` undo-lépést tol,
                    // tehát a Visszavonás gomb visszahozza (#465).
                    onCropResetRequested: {
                        cropOverlay.resetSelection()
                        if (viewer.editCtl && viewer.editCtl.hasCrop)
                            editController.clearCrop()
                    }
                    // #1528: a gomb tiltott, ha nincs mit elvetni — se
                    // húzott kijelölés, se mentett vágás.
                    cropResetEnabled: cropOverlay.hasSelection
                        || (viewer.editCtl ? viewer.editCtl.hasCrop : false)
                    // #448: a három automatikus javaslat — a választott
                    // téglalap a KIJELÖLÉSBE kerül (nem alkalmazódik
                    // azonnal), hogy a felhasználó még igazíthasson rajta,
                    // és az Alkalmaz/Mégse útja változatlan maradjon.
                    cropSuggestions: viewer.editCtl
                        ? viewer.editCtl.cropSuggestions : []
                    onCropSuggestionChosen: (x, y, w, h) =>
                        cropOverlay.loadSelection(
                            { "x": x, "y": y, "width": w, "height": h })
                    onCropApplyRequested: viewer.applyCrop(false)
                    onCropCancelRequested: {
                        cropOverlay.resetSelection()
                        editorPanel.cropActive = false
                    }
                    // #148/#445: a retusálás pufferének mérete/az Alkalmaz-
                    // gomb engedélyezettsége, a félbehagyott folt ("Refining…")
                    // és a patch-enkénti Undo/Redo/ecsetméret a kontrollerből
                    retouchRegionCount: viewer.editCtl
                        ? viewer.editCtl.retouchPendingCount : 0
                    retouchPatchPending: viewer.editCtl
                        ? viewer.editCtl.retouchPatchPending : false
                    canUndoPatch: viewer.editCtl ? viewer.editCtl.canUndoPatch : false
                    canRedoPatch: viewer.editCtl ? viewer.editCtl.canRedoPatch : false
                    brushSize: viewer.editCtl ? viewer.editCtl.brushSize : 20
                    onBrushSizeEdited: (value) => editController.setBrushSize(value)
                    onRetouchUndoPatchRequested: editController.undoPatch()
                    onRetouchRedoPatchRequested: editController.redoPatch()
                    onRetouchResetRequested: editController.resetPatches()
                    onRetouchApplyRequested: {
                        editController.applyRetouch()
                        editorPanel.retouchActive = false
                    }
                    onRetouchCancelRequested: editorPanel.retouchActive = false
                    // #445: Vörösszem — a kézi régió-puffer és az automatika
                    // találat-száma a kontrollerből
                    redeyeRegionCount: viewer.editCtl
                        ? viewer.editCtl.redeyeRegionCount : 0
                    canUndoRedeyeRegion: viewer.editCtl
                        ? viewer.editCtl.canUndoRedeyeRegion : false
                    redeyeFoundCount: viewer.editCtl
                        ? viewer.editCtl.redeyeFoundCount : -1
                    onRedeyeAutoRequested: editController.runRedeyeAuto()
                    onRedeyeUndoRegionRequested: editController.undoRedeyeRegion()
                    onRedeyeResetRequested: editController.resetRedeyeRegions()
                    onRedeyeApplyRequested: {
                        editController.applyRedeye()
                        editorPanel.redeyeActive = false
                    }
                    onRedeyeCancelRequested: editorPanel.redeyeActive = false
                    // #148: a szöveg-eszköz Alkalmaz-gombja csak akkor
                    // engedélyezett, ha már van kattintott pozíció
                    textPlacementPending: viewer.editCtl
                        ? viewer.editCtl.textHasPlacement : false
                    // #450: "Copy Caption" gomb — a kép model.revision-re
                    // is frissülő mentett feliratát tükrözi (a captionField
                    // mintáját követve fent)
                    captionText: viewer.photosModel
                        ? (viewer.photosModel.revision,
                           viewer.photosModel.captionAt(viewer.currentIndex))
                        : ""
                    onTextDraftEdited: (content) => editController.setTextDraft(content)
                    onTextApplyRequested: {
                        editController.applyText()
                        editorPanel.textActive = false
                    }
                    onTextCancelRequested: editorPanel.textActive = false
                    // #450: a kép feliratát tölti a szövegmezőbe
                    // #465 4. pont: a felirat BEMÁSOLÁSA felülírja a
                    // szövegmező tartalmát — az eredeti Picasa erre
                    // kimondottan figyelmeztet („(This operation is not
                    // undoable)"), mert a beírt szöveg nem szerezhető
                    // vissza. Üres mezőnél nincs mit elveszíteni, ott
                    // szándékosan NEM kérdezünk (a jegy elve: csak ott
                    // ijesztgess, ahol tényleg végleges).
                    onTextCopyCaptionRequested: {
                        if (editorPanel.textDraftContent.length === 0) {
                            editorPanel.textDraftContent = editorPanel.captionText
                            return
                        }
                        copyCaptionConfirmLoader.ensure().ask(
                            "copyCaptionOverwrite",
                            qsTr("The caption will replace the text you have "
                                 + "typed. (This operation is not undoable)"))
                    }
                    // #450: az összes (ma: az egyetlen) szövegelem törlése —
                    // a meglévő clearText útvonalon, a szerkesztőeszköz is zárul
                    onTextRemoveAllRequested: {
                        editController.clearText()
                        editorPanel.textDraftContent = ""
                        editorPanel.textActive = false
                    }
                    // #464: a pipetta be/ki kapcsolása — a mintavétel a
                    // `neutralPickArea`-ban történik (a kép fölött)
                    onNeutralPickerToggled: editorPanel.neutralPickerActive =
                        !editorPanel.neutralPickerActive
                    onTextFillColorEdited: (hex) => editController.setTextFillColor(hex)
                    onTextOutlineColorEdited: (hex) => editController.setTextOutlineColor(hex)
                    // #2271: NINCS kerekítés. A körvonalvastagság `[0, 1]`
                    // FOLYTONOS az eredetiben (ugyanaz a `ytSliderHandler`,
                    // mint az átlátszatlanságé); a `Math.round` a régi,
                    // képpontos mértékegység maradványa volt, és minden
                    // 0,5 alatti értéket nullára — vagyis „nincs körvonal"-ra
                    // — vágott.
                    onTextOutlineThicknessEdited: (value) =>
                        editController.setTextOutlineThickness(value)
                    onTextFillEnabledEdited: (value) => editController.setTextFillEnabled(value)
                    onTextOpacityEdited: (value) => editController.setTextOpacity(value)
                    // #450 (2. lépcső): tipográfia — az ÉRTÉKEKET a
                    // syncEditorPanel() tölti (a többi szöveg-stílus
                    // mintájára), itt csak a jelzések mennek vissza
                    onTextFontFamilyEdited: (key) =>
                        editController.setTextFontFamily(key)
                    onTextFontSizeEdited: (value) =>
                        editController.setTextFontSize(value)
                    onTextBoldEdited: (value) => editController.setTextBold(value)
                    onTextItalicEdited: (value) => editController.setTextItalic(value)
                    onTextUnderlineEdited: (value) =>
                        editController.setTextUnderline(value)
                    onTextAlignEdited: (value) => editController.setTextAlign(value)
                }

                ColumnLayout {
                    anchors.top: editorPanel.bottom
                    anchors.left: parent.left; anchors.right: parent.right
                    anchors.margins: 10
                    spacing: 6
                    Label {
                        visible: editorPanel.tiltActive && editorPanel.activeTab === 0
                        text: qsTr("Straighten")
                        font.pixelSize: Theme.fontSize
                        color: Theme.textGray
                    }
                    // döntés-csúszka: −1..1 Picasa-egység (±11,5°); húzás
                    // közben élő előnézet (previewTilt, nincs ini-mentés,
                    // #72), elengedéskor ír + tol undo-lépést (setTilt)
                    PicasaSlider {
                        id: tiltSlider
                        objectName: "tiltSlider"
                        visible: editorPanel.tiltActive && editorPanel.activeTab === 0
                        from: -1; to: 1; value: 0
                        // programozott szinkronnál (nyitás/lapozás) NEM
                        // váltunk ki previewTilt-et — az felülírná a
                        // mentett érték előnézetét (#131)
                        property bool suppressPreview: false
                        Layout.fillWidth: true
                        onValueChanged: if (editorPanel.tiltActive && !suppressPreview)
                                            editController.previewTilt(value)
                        onPressedChanged: if (!pressed && editorPanel.tiltActive)
                                              editController.setTilt(value)
                    }
                }
                // élő RGB-hisztogram + fényképezőgép-adat sor (#25): a
                // korábbi placeholder-doboz élesítve — HistogramBox.qml
                // #1323: a panel a bal fiókON BELÜL dokkolt, nem a
                // képterület fölött lebeg. Az `editpanel.tre` szerint
                // (`nerdview_container`, XConstraint 0, 0, LEFTDRAWEROFFSET,
                // 20) a bal éle a fiók bal szélétől 20 px — a
                // `LEFTDRAWEROFFSET` a fiók BE-/KICSÚSZTATÁSÁT vezérlő
                // változó (0 ↔ −279, `editpanel.tre:1413`), nem a fiók
                // szélessége; a képterület `LEFTDRAWEROFFSET + 279`-nél
                // kezdődik (`insetleft`, 1421). A 238 × 144-es doboz így a
                // 280 px-es fiók sávján belülre esik.
                HistogramBox {
                    objectName: "viewerHistogramBox"
                    anchors.bottom: parent.bottom
                    // #1905/3: MÉRVE a tulajdonos egymás mellé tett
                    // felvételén — a doboz alsó szegélye 4 px-re van a bal
                    // panel aljától (Picasa 3: y=921, a panel alja y=925;
                    // nálunk y=830 volt, azaz 95 px lebegés).
                    //
                    // A 95 az `editpanel.tre` `nerdview_container`
                    // `YConstraint 1, 1, -95` sorából jött — CSAKHOGY annak
                    // a szülője `root`, nem a bal fiók. A fiók aljára
                    // ugyanazt a −95-öt alkalmazva nagy üres sáv marad
                    // alatta. A felvétel dönt.
                    anchors.bottomMargin: 4
                    anchors.left: parent.left
                    anchors.leftMargin: 20
                    width: 238
                    height: 144
                    // #305: null-őr
                    histogramData: viewer.editCtl
                        ? viewer.editCtl.histogram : ({ r: [], g: [], b: [] })
                    cameraSummary: viewer.editCtl ? viewer.editCtl.cameraSummary : ""
                }
            }

            // fő képterület
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Theme.viewerBg

                WheelHandler {
                    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                    // #6: Ctrl+görgő = zoom a kép fölött; sima görgő marad a
                    // képek közti lapozás (#77) — a két igény így fér össze
                    onWheel: function(event) {
                        if (event.modifiers & Qt.ControlModifier)
                            viewer.wheelZoom(event.angleDelta.y)
                        else
                            viewer.wheelStep(event.angleDelta.y)
                    }
                }

                Item {
                    id: photoArea
                    objectName: "viewerPhotoArea"
                    anchors.fill: parent
                    anchors.margins: 14
                    anchors.bottomMargin: 30
                    // #6 utójavítás (felhasználói hibajelzés): a nagyított
                    // kép NE lógjon ki a képterületből a bal panel / a
                    // felső sáv / a felirat-sor fölé — a QML alapból nem
                    // vág, a zoomhoz kötelező a clip
                    clip: true

                    //: #3013: a KETTŐS NÉZET bal oldala — a szerkesztés
                    //: ELŐTTI kép. A nyers fájl URL-je, a `filters=` lánc
                    //: nélkül: ez a „mi volt" oldal. Csak 2-up módban
                    //: látszik, és a fő képpel EGYFORMA méretet kap.
                    Image {
                        id: photoElotte
                        objectName: "viewerImageElotte"
                        visible: viewer.layoutMode !== "1up"
                                 && !viewer.isCurrentVideo
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: viewer.layoutMode === "1up"
                            ? 0 : Math.floor((parent.width - 8) / 2)
                        source: viewer.isCurrentVideo
                            ? "" : viewer.urlAt(viewer.currentIndex)
                        fillMode: Image.PreserveAspectFit
                        asynchronous: Qt.platform.pluginName !== "offscreen"
                        autoTransform: true
                        sourceSize.width: 2560
                    }

                    //: #3013: a „Kijelölve" jelvény az AKTÍV oldalon
                    Rectangle {
                        objectName: "viewerFocusBadge"
                        visible: viewer.layoutMode !== "1up"
                        width: jelvenySzoveg.implicitWidth + 12
                        height: 18
                        radius: 2
                        color: Theme.selectionBlue
                        anchors.top: parent.top
                        anchors.left: viewer.aktivOldal === "bal"
                            ? parent.left : undefined
                        anchors.right: viewer.aktivOldal === "jobb"
                            ? parent.right : undefined
                        Text {
                            id: jelvenySzoveg
                            anchors.centerIn: parent
                            text: qsTr("Selected")
                            font.pixelSize: Theme.fontSize - 2
                            color: "#ffffff"
                        }
                    }

                    Image {
                        id: photo
                        objectName: "viewerImage"
                        // videónál a fotó-Image üres és rejtett (#14) — a
                        // videofájlt nem próbáljuk képként dekódolni
                        visible: !viewer.isCurrentVideo
                        // a model.revision referencia miatt a kötés minden
                        // modell-frissítésnél újraértékelődik
                        readonly property int iniSteps: viewer.photosModel
                            ? (viewer.photosModel.revision,
                               viewer.photosModel.rotateAt(viewer.currentIndex))
                            : 0
                        anchors.centerIn: parent
                        // #6: zoom + pásztázás — a skála az illesztett
                        // mérethez képest, az eltolás a pan-állapotból
                        anchors.horizontalCenterOffset: viewer.panX
                        anchors.verticalCenterOffset: viewer.panY
                        scale: viewer.zoomFactor
                        transformOrigin: Item.Center
                        // 90°/270°-nál a befoglaló doboz oldalai cserélődnek
                        //: #3013: 2-up módban a fő kép a JOBB felet kapja
                        //: (ez a „mai" állapot), egy képen a teljes terület
                        width: iniSteps % 2
                            ? photoArea.height
                            : (viewer.layoutMode === "1up"
                               ? photoArea.width
                               : Math.floor((photoArea.width - 8) / 2))
                        height: iniSteps % 2 ? photoArea.width : photoArea.height
                        rotation: iniSteps * 90
                        // nyitott szerkesztésnél a filters= láncot alkalmazó
                        // editpreview provider rendereli a képet (?rev=
                        // cache-buster minden módosításnál)
                        // #305: null-őr
                        source: viewer.isCurrentVideo ? ""
                                : (viewer.editCtl && viewer.editCtl.previewSource !== ""
                                   ? viewer.editCtl.previewSource
                                   : viewer.urlAt(viewer.currentIndex))
                        fillMode: Image.PreserveAspectFit
                        // #53: offscreen (teszt) platformon szinkron betöltés —
                        // itt reprodukálódott a GIL-deadlock (a lapozás
                        // setProperty-je vs. az image-provider szál). Szinkron
                        // betöltésnél nincs provider-szál, így nincs holtpont;
                        // produkcióban marad az async.
                        asynchronous: Qt.platform.pluginName !== "offscreen"
                        autoTransform: true   // EXIF-orientáció
                        sourceSize.width: 2560
                    }

                    // GPU élő-előnézet (#22): a `photo` FÖLÖTT, csak akkor
                    // látható, ha `gpuFinetuneActive && gpuFinetuneEligible`
                    // (ld. a fenti property-k docsztringjét). A két rejtett
                    // `Image` a forrás (a finetune2 ELŐTTI kép) és a
                    // 256×1 LUT-textúra betöltője — `smooth: false` a
                    // LUT-on kötelező (egzakt indexelés, ld.
                    // GpuPointFilterPreview.qml). GPU-képtelen
                    // futtatókörnyezetben (`gpuFinetuneEligible` mindig
                    // false) ez a réteg SOSEM válik láthatóvá — a `photo`
                    // Image alatta változatlanul a rendes CPU-előnézetet
                    // mutatja, semmi nem törhet emiatt CI-ban.
                    Image {
                        id: gpuPrefixImage
                        objectName: "gpuPrefixImage"
                        visible: false
                        source: viewer.gpuFinetuneEligible
                                ? viewer.editCtl.gpuPrefixSource : ""
                        asynchronous: Qt.platform.pluginName !== "offscreen"
                        autoTransform: true
                        sourceSize.width: 2560
                    }
                    Image {
                        id: gpuLutImage
                        objectName: "gpuLutImage"
                        visible: false
                        smooth: false
                        cache: false
                        source: viewer.gpuFinetuneEligible
                                ? viewer.editCtl.gpuLutSource : ""
                    }
                    GpuPointFilterPreview {
                        id: gpuFinetunePreview
                        objectName: "gpuFinetunePreview"
                        // #415: NEM `anchors.fill: photo` — az a `photo`
                        // TELJES befoglaló dobozára igazítana (a
                        // rendelkezésre álló terület, `photo.width`/
                        // `photo.height`), nem a `PreserveAspectFit`
                        // fillMode által ténylegesen kirajzolt, letterboxolt
                        // téglalapra. Álló képnél a doboz szélesebb, mint a
                        // kirajzolt kép — a húzás alatt ez a réteg (a `photo`
                        // fölött) a doboz teljes szélességére nyúlt, majd
                        // elrejtésekor (elengedéskor) a helyesen illesztett
                        // `photo` vált újra láthatóvá: ez okozta a
                        // bejelentett "kiugrást". A helyes geometria a
                        // `cropOverlay`/`facesOverlay` mintáját követi —
                        // `paintedWidth`/`paintedHeight`, középre igazítva.
                        x: photo.x + (photo.width - photo.paintedWidth) / 2
                        y: photo.y + (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        rotation: photo.rotation
                        scale: photo.scale
                        transformOrigin: Item.Center
                        // #402: shader-hibánál (shaderOk=false) némán a
                        // CPU-előnézet marad
                        visible: viewer.gpuFinetuneActive && viewer.gpuFinetuneEligible
                                 && viewer.gpuFinetunePointSafe
                                 && gpuFinetunePreview.shaderOk
                        sourceItem: gpuPrefixImage
                        lutItem: gpuLutImage
                        satGain: 1.0
                        bwMix: 0.0
                    }

                    // #14: videó-lejátszó — csak videónál töltődik be, így
                    // a Qt Multimedia hiánya a fotó-nézetet nem érinti
                    Loader {
                        id: videoLoader
                        objectName: "videoLoader"
                        anchors.fill: parent
                        active: viewer.visible && viewer.isCurrentVideo
                        source: "VideoPlayerView.qml"
                    }
                    Binding {
                        target: videoLoader.item
                        property: "source"
                        value: viewer.urlAt(viewer.currentIndex)
                        when: videoLoader.status === Loader.Ready
                              && viewer.isCurrentVideo
                    }
                    //: #1838: a VÁGÁSPONTOK átadása a lejátszónak. A Picasából
                    //: örökölt `moviestart`/`movieend` a `filters=` láncban ül;
                    //: a modell ezredmásodpercre váltva adja, és a **−1
                    //: jelenti, hogy azon az oldalon nincs vágás** (a 0 a
                    //: nulla pontra állított kezdés lenne).
                    Binding {
                        target: videoLoader.item
                        property: "trimStartMs"
                        value: viewer.photosModel
                               ? viewer.photosModel.movieTrimAt(
                                     viewer.currentIndex).start : -1
                        when: videoLoader.status === Loader.Ready
                              && viewer.isCurrentVideo
                    }
                    Binding {
                        target: videoLoader.item
                        property: "trimEndMs"
                        value: viewer.photosModel
                               ? viewer.photosModel.movieTrimAt(
                                     viewer.currentIndex).end : -1
                        when: videoLoader.status === Loader.Ready
                              && viewer.isCurrentVideo
                    }
                    Text {
                        objectName: "videoUnavailableText"
                        visible: viewer.isCurrentVideo
                                 && videoLoader.status === Loader.Error
                        anchors.centerIn: parent
                        text: qsTr("Video playback requires the Qt Multimedia module.")
                        color: "#e8e8e8"
                        font.pixelSize: Theme.fontSize
                    }

                    // vágó-overlay a kép TÉNYLEGESEN kirajzolt (letterbox
                    // nélküli) területén. Enter: elfogad + következő kép a
                    // vágó-mód megtartásával (sorozat-vágás, UX-alapelv 1);
                    // Esc: kilép a vágásból. MVP-korlát: ini-forgatott
                    // (rotate=) képnél a koordináták a megjelenített térben
                    // értendők — a forgatás+vágás kombináció a #21-ben pontosodik.
                    CropOverlay {
                        id: cropOverlay
                        parent: photo
                        visible: editorPanel.cropActive
                        aspectRatio: editorPanel.currentAspect
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        onVisibleChanged: {
                            if (visible) forceActiveFocus()
                            else viewer.forceActiveFocus()
                        }
                        // Enter-flow: elfogad ÉS következő kép, a vágó-mód
                        // megtartásával (sorozat-vágás, UX-alapelv 1)
                        onAccepted: function(r) {
                            viewer.applyCrop(true)
                            if (visible) forceActiveFocus()
                        }
                        onCancelled: {
                            cropOverlay.resetSelection()
                            editorPanel.cropActive = false
                        }
                    }

                    // #147/#26: a mentett arc-régiók a kép kirajzolt
                    // (letterbox nélküli) területén — a cropOverlay
                    // mintájára. Szerkesztő módban (facesEditMode) itt
                    // rajzolható/nevezhető/törölhető egy régió.
                    FacesOverlay {
                        id: facesOverlay
                        parent: photo
                        visible: viewer.facesVisible && !editorPanel.cropActive
                                 && !viewer.isCurrentVideo
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        faces: viewer.currentFaces
                        editMode: viewer.facesEditMode
                        imagePath: viewer.photosModel && viewer.currentIndex >= 0
                            ? viewer.photosModel.filePathAt(viewer.currentIndex) : ""
                        onEdited: viewer.facesEditRevision += 1
                    }

                    // #445: a retusálás a Picasa súgószövege szerinti,
                    // KÉTKATTINTÁSOS, irányított klónozás — 1. kattintás a
                    // CÉL kijelölése, egérmozgatás a FORRÁS élő előnézete,
                    // 2. kattintás véglegesíti. `Ctrl`+húzás eközben a
                    // meglévő nagyítás-pásztázó (`viewer.panX`/`panY`/
                    // `clampPan()`, ld. lent a `viewerPanArea`-t) állapotára
                    // ül rá, hogy zoomolt nézetben kattintás nélkül lehessen
                    // odébb húzni a képet.
                    // #464: a „semleges szín" pipetta — amíg aktív, a képre
                    // kattintás színmintát vesz (nem navigál). A kattintás
                    // helyét a KIRAJZOLT képhez képest normálva adjuk át, így
                    // a nagyítástól/illesztéstől független.
                    MouseArea {
                        id: neutralPickArea
                        objectName: "neutralPickArea"
                        parent: photo
                        visible: editorPanel.neutralPickerActive
                        enabled: editorPanel.neutralPickerActive
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        cursorShape: Qt.CrossCursor
                        onClicked: function(mouse) {
                            if (!editController) return
                            editController.pickNeutralColor(
                                mouse.x / Math.max(1, width),
                                mouse.y / Math.max(1, height))
                            editorPanel.neutralPickerActive = false
                        }
                    }

                    MouseArea {
                        id: retouchClickArea
                        objectName: "retouchClickArea"
                        parent: photo
                        visible: editorPanel.retouchActive
                        enabled: editorPanel.retouchActive
                        hoverEnabled: true
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        cursorShape: Qt.CrossCursor
                        property bool ctrlPanning: false
                        property real panLastX: 0
                        property real panLastY: 0
                        onPressed: function(mouse) {
                            if (mouse.modifiers & Qt.ControlModifier) {
                                ctrlPanning = true
                                panLastX = mouse.x; panLastY = mouse.y
                            }
                        }
                        onPositionChanged: function(mouse) {
                            if (width <= 0 || height <= 0) return
                            if (ctrlPanning) {
                                viewer.panX += mouse.x - panLastX
                                viewer.panY += mouse.y - panLastY
                                panLastX = mouse.x; panLastY = mouse.y
                                viewer.clampPan()
                                return
                            }
                            if (editController.retouchPatchPending)
                                editController.previewRetouchSource(
                                    mouse.x / width, mouse.y / height)
                        }
                        onReleased: function(mouse) { ctrlPanning = false }
                        onClicked: function(mouse) {
                            if (width <= 0 || height <= 0) return
                            // Ctrl+húzás UTÁNi felengedés is "clicked"-et vált
                            // ki QML-ben — ez NEM patch-kattintás
                            if (mouse.modifiers & Qt.ControlModifier) return
                            if (editController.retouchPatchPending)
                                editController.commitRetouchPatch(
                                    mouse.x / width, mouse.y / height)
                            else
                                editController.beginRetouchPatch(
                                    mouse.x / width, mouse.y / height)
                        }
                    }
                    // #445: Vörösszem — kézi kijelölés téglalap-húzással
                    // („Click, hold, and drag the mouse around each eye
                    // separately to select it. A selection box appears over
                    // the area."). A már felvett régiókat a kontroller adja
                    // vissza normált [0..1] alakban, ezért a nagyítástól/
                    // illesztéstől függetlenül rajzolhatók. A
                    // `redeyeHideOutlines` a jegy „Preview changes without
                    // square outlines" jelölőnégyzete: csak a RAJZOT tünteti
                    // el, a javítást nem.
                    Item {
                        id: redeyeOverlay
                        objectName: "redeyeOverlay"
                        parent: photo
                        visible: editorPanel.redeyeActive
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight

                        Repeater {
                            model: editorPanel.redeyeHideOutlines
                                   ? []
                                   : (viewer.editCtl
                                      ? viewer.editCtl.redeyeRegions : [])
                            delegate: Rectangle {
                                required property var modelData
                                x: modelData.x * redeyeOverlay.width
                                y: modelData.y * redeyeOverlay.height
                                width: modelData.w * redeyeOverlay.width
                                height: modelData.h * redeyeOverlay.height
                                color: "transparent"
                                border.width: 1
                                border.color: Theme.selectionBlue
                            }
                        }

                        // #900: az `editpanel/redselection` a téglalapon
                        // KÍVÜLI területet ugyanazzal a
                        // `negativemode 8f2f2f2f` értékkel sötétíti, mint a
                        // vágó. Csak húzás közben — a már rögzített régiók
                        // körül nincs sötétítés, azokat csak keret jelöli.
                        SelectionDim {
                            objectName: "redeyeSelectionDim"
                            active: redeyeDragArea.dragging
                                    && !editorPanel.redeyeHideOutlines
                            selX: redeyeDragArea.selX
                            selY: redeyeDragArea.selY
                            selW: redeyeDragArea.selW
                            selH: redeyeDragArea.selH
                        }

                        // az ÉPP húzott téglalap (még nincs a pufferben)
                        Rectangle {
                            objectName: "redeyeDragRect"
                            visible: redeyeDragArea.dragging
                                     && !editorPanel.redeyeHideOutlines
                            x: redeyeDragArea.selX
                            y: redeyeDragArea.selY
                            width: redeyeDragArea.selW
                            height: redeyeDragArea.selH
                            color: "transparent"
                            border.width: 1
                            border.color: Theme.selectionBlue
                        }

                        // #891: a húzás közben lenyomott módosító a KÉP
                        // saját arányára (Shift), annak 4/3-ára (Ctrl) vagy
                        // 3/2-ére (Alt) kényszeríti a téglalapot — Alt üt
                        // Ctrl-t, Ctrl üt Shiftet. A `selX/selY/selW/selH` a
                        // MÁR KÉNYSZERÍTETT téglalap, ezt rajzoljuk és ezt
                        // adjuk át felengedéskor. Minden lépés újraszámol,
                        // ezért a billentyű felengedése azonnal felszabadít.
                        MouseArea {
                            id: redeyeDragArea
                            objectName: "redeyeDragArea"
                            anchors.fill: parent
                            enabled: editorPanel.redeyeActive
                            //: #604: a keret fölött a kurzor JELZI, hogy
                            //: kattintva törölhető — az eredeti mindhárom
                            //: útmutatója ezt ígéri. Húzás közben marad a
                            //: célkereszt, különben a kurzor a keret fölé
                            //: érve váltogatna.
                            cursorShape: (!dragging && keretenAll)
                                         ? Qt.PointingHandCursor
                                         : Qt.CrossCursor
                            hoverEnabled: editorPanel.redeyeActive
                            property bool keretenAll: false
                            property bool dragging: false
                            property real startX: 0
                            property real startY: 0
                            property real selX: 0
                            property real selY: 0
                            property real selW: 0
                            property real selH: 0
                            function frissit(mouse) {
                                var r = AranyKenyszer.huzottTeglalap(
                                    startX, startY, mouse.x, mouse.y,
                                    width, height,
                                    mouse.modifiers & Qt.ShiftModifier,
                                    mouse.modifiers & Qt.ControlModifier,
                                    mouse.modifiers & Qt.AltModifier)
                                selX = r.x; selY = r.y
                                selW = r.width; selH = r.height
                            }
                            onPressed: function(mouse) {
                                dragging = true
                                startX = mouse.x; startY = mouse.y
                                selX = mouse.x; selY = mouse.y
                                selW = 0; selH = 0
                            }
                            onPositionChanged: function(mouse) {
                                if (!dragging) {
                                    keretenAll = (width > 0 && height > 0
                                        && editController.redeyeRegionHitAt(
                                            mouse.x / width, mouse.y / height))
                                    return
                                }
                                frissit(mouse)
                            }
                            onExited: keretenAll = false
                            onReleased: function(mouse) {
                                dragging = false
                                if (width <= 0 || height <= 0) return
                                frissit(mouse)
                                //: #604: a nulla méretű kijelölés — vagyis a
                                //: puszta KATTINTÁS — a kereten TÖRLÉS, azon
                                //: kívül továbbra is néma no-op. A húzás
                                //: változatlanul új régiót ad, akkor is, ha
                                //: egy meglévő kereten indul.
                                if (selW <= 0 || selH <= 0) {
                                    editController.removeRedeyeRegionAt(
                                        mouse.x / width, mouse.y / height)
                                    keretenAll = editController
                                        .redeyeRegionHitAt(
                                            mouse.x / width, mouse.y / height)
                                    return
                                }
                                editController.addRedeyeRegion(
                                    selX / width, selY / height,
                                    selW / width, selH / height)
                            }
                        }
                    }
                    MouseArea {
                        id: textClickArea
                        objectName: "textClickArea"
                        parent: photo
                        visible: editorPanel.textActive
                        enabled: editorPanel.textActive
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        cursorShape: Qt.CrossCursor
                        onClicked: function(mouse) {
                            if (width <= 0 || height <= 0) return
                            editController.previewTextPlacement(
                                mouse.x / width, mouse.y / height)
                        }
                    }
                }
                // #6: nagyított képen húzással pásztázás; dupla katt = fit.
                // Illesztett nézetben inaktív — az események átmennek rajta.
                MouseArea {
                    objectName: "viewerPanArea"
                    anchors.fill: photoArea
                    enabled: viewer.zoomFactor > 1.01
                             && !editorPanel.cropActive
                             && !viewer.isCurrentVideo
                    cursorShape: enabled ? Qt.OpenHandCursor : Qt.ArrowCursor
                    property real lastX: 0
                    property real lastY: 0
                    onPressed: function(event) {
                        lastX = event.x; lastY = event.y
                    }
                    onPositionChanged: function(event) {
                        if (!pressed) return
                        viewer.panX += event.x - lastX
                        viewer.panY += event.y - lastY
                        lastX = event.x; lastY = event.y
                        viewer.clampPan()
                    }
                    onDoubleClicked: viewer.zoomFit()
                }

                BusyIndicator {
                    anchors.centerIn: parent
                    running: photo.status === Image.Loading
                }

                // #1072 — `editpanel/render_now` („Létrehozás"): a PISZKOZAT
                // külön befejező lépése. A `projectutils::draft_collage`
                // szövege erre a gombra hivatkozik: a megosztás és a
                // nyomtatás feltétele, hogy a felhasználó megnyomja.
                //
                // A HELYE mért, nem választott (spec 4.3, `editpanel.tre`):
                // az `overlay_group` gyereke, tehát a kép FÖLÖTTI réteg —
                // a bélyegképen nincs rajta, csak a JPEG-be égetett
                // „PISZKOZAT" felirat. Vízszintesen középen (`m_centerX`),
                // függőlegesen a saját közepe a szülő 87,5%-án
                // (`YConstraint 0.5, 0.875, 0`).
                //
                // ⚠️ Renderelés közben az eredeti ugyanide teszi a
                // „Folyamatban..." feliratot (`editpanel/in_progress_label`)
                // — a kettő EGYMÁS HELYÉRE lép, ezért egyetlen elem
                // felirata változik, nem két külön gomb.
                PicasaButton {
                    id: piszkozatLetrehozas
                    objectName: "viewerCreateNowButton"
                    //: `editpanel/render_now` / `editpanel/in_progress_label`
                    text: viewer.controllerReady && controller.collageRendering
                          ? qsTr("In Progress...") : qsTr("Create Now")
                    enabled: !(viewer.controllerReady
                               && controller.collageRendering)
                    font.pixelSize: Theme.fontSize
                    visible: viewer.currentIsCollageDraft
                    x: (parent.width - width) / 2
                    y: parent.height * 0.875 - height / 2
                    ToolTip.text: qsTr("Render the final collage from this draft")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: controller.finishCollageDraft(
                        viewer.currentFilePath)
                }

                // #2564: a nagyítás-hármas (illesztés · 1:1 · csúszka) ELKERÜLT
                // innen az ALSÓ ESZKÖZSÁVBA (`TrayBar.qml`,
                // `trayViewerZoomRow`) — mérve az `editpanel.tre:1288–1324`
                // horgonyai és a `respack.yt` x-tartományai szerint az
                // eredetiben a könyvtár nagyító + bélyegkép-csúszka
                // párjának a HELYÉN ül, nem a fotó fölött lebegve.
                //
                // Ez a doboz a MI KÉT arc-gombunké maradt (`☺` és `✎`):
                // ezek nincsenek az eredetiben (saját döntés, #147/#26), és
                // a #2564 kifejezetten hatókörön kívül hagyta őket. A
                // lebegő forma nekik marad, mert a fotón értelmezett
                // állapotot kapcsolnak.
                Rectangle {
                    id: facesBar
                    objectName: "viewerFacesBar"
                    //: VÁLTOZATLAN feltétel: ugyanaz, ami a korábbi
                    //: `zoomBar`-t vezérelte — videón nincs arc-keret,
                    //: vágás közben pedig a fotó fölötti réteg tiszta.
                    visible: viewer.photoOverlaysUsable
                    anchors.right: parent.right
                    anchors.rightMargin: 4
                    //: #2565: a felirat-sáv FÖLÉ, nem rá. A sáv a fotó
                    //: alján végigfut (mérve), és a lebegő doboz eddig
                    //: eltakarta a sáv jobb szélén ülő kukát — a kirajzolt
                    //: képen látszott, számolásból nem derült volna ki.
                    anchors.bottom: captionBar.visible
                                    ? captionBar.top : parent.bottom
                    anchors.bottomMargin: 4
                    width: facesRow.width + 12
                    height: 26
                    radius: 4
                    color: "#00000059"
                    Row {
                        id: facesRow
                        anchors.centerIn: parent
                        spacing: 4
                        // #147: arc-keretek be/ki (F billentyűvel egyenértékű)
                        PicasaButton {
                            objectName: "facesToggleButton"
                            text: "☺"
                            checkable: true
                            checked: viewer.facesVisible
                            width: 26; height: 20
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Show Faces")
                            onClicked: viewer.toggleFaces()
                        }
                        // #26 (2. kör): arc-SZERKESZTŐ mód be/ki
                        // (Shift+F billentyűvel egyenértékű) — videónál
                        // nincs értelme, ott letiltjuk.
                        PicasaButton {
                            objectName: "facesEditToggleButton"
                            text: "✎"
                            checkable: true
                            checked: viewer.facesEditMode
                            enabled: !viewer.isCurrentVideo
                            width: 26; height: 20
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Edit Faces")
                            onClicked: viewer.toggleFacesEdit()
                        }
                    }
                }
                // szerkeszthető felirat-sor — a model.revision referencia
                // miatt a kötés modell-frissítésnél (pl. mentés után)
                // újraértékelődik, ahogy a forgatás-kötés is (lásd fent).
                // Gépeléskor a Qt eltávolítja a deklaratív kötést a text
                // property-ről (közvetlen C++ írás), ezért elfogadás és
                // Esc után Qt.binding()-gel újra be kell kötni, különben a
                // mező a következő navigáláskor nem frissülne.
                // #1816: a felirat-sáv KÉT vezérlője. Az eredetiben a
                // `captionbutton` („Show/Hide Caption") és a `captiontrash`
                // („Delete this caption") — a `0x0057bb50` kezelő a
                // `captionbutton` · `caption` · `captiontrash` hármast
                // EGYÜTT kezeli.
                //
                // ⚠️ A jegy KÉT belépési pontot ír elő (`editpanel/` és
                // `editoneup/captionbutton`). Nálunk a szerkesztő panel a
                // NÉZŐN BELÜL él (`EditorPanel` ugyanebben a fájlban), tehát
                // ez az EGY sáv mindkét állapotot kiszolgálja — mérve, nem
                // feltételezve: a sáv `visible`-je csak a vágásra és a
                // videóra érzékeny, a szerkesztő nyitottságára nem.
                // #2565 + #2587: a KÉPALÁÍRÁS-SÁV. A mérce a tulajdonos NÉGY
                // felvétele (`research/felirat-ki-bekapcsolva/`, 1920 × 1080,
                // Picasa 3 és PicasaPy, felirat BE és KI állapotban).
                //
                // A `.tre` kényszerei (`editpanel.tre:1238–1266`):
                //   `captionbutton`  `XConstraint 0, 0, 3`   `Y 1, 1, -3`
                //   `caption`        `X 0, 0, 25` … `1, 1, -24`
                //   `captiontrash`   `XConstraint 1, 1, -3`  `Y 1, 1, -3`
                //   `captionbase` / `captionbasetop`: a sáv HÁTTERE
                //     (`predraw 1`), teljes szélességben.
                //
                // ⚠️ A `captionbutton` `hidetarget`-je a `caption` és a
                // `captiontrash` — **magát a gombot nem**. A felvételen ez
                // pontosan így látszik: kikapcsolt feliratnál a SÁV eltűnik,
                // a kapcsoló viszont OTT MARAD a kép bal alsó sarkában.
                // Ezért ül a gomb a fotó-terület rétegén, nem a sávban.
                Item {
                    id: captionBar
                    objectName: "captionBar"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    //: MÉRT magasság: a felvételen a csík y 906…926 (21 px).
                    height: 21
                    visible: viewer.captionVisible

                    //: `captionbase` + `captionbasetop` — a sáv saját
                    //: háttere. MÉRVE: a felvételen `#c6c6c6`, vagyis a
                    //: KRÓM világosszürkéje, nem a fotó-terület szürkéje és
                    //: nem sötét. Sötét témában a króm sötét párja.
                    Rectangle {
                        id: captionBarBackground
                        objectName: "captionBarBackground"
                        anchors.fill: parent
                        color: Theme.captionBar
                    }

                    TextInput {
                        id: captionField
                        objectName: "captionField"
                        //: `caption`: a két gomb KÖZÖTT, a sáv teljes
                        //: maradékán — az eredetin a felirat a sáv
                        //: közepén áll, FÉLKÖVÉREN és sötéten.
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.leftMargin: 25
                        anchors.rightMargin: 24
                        anchors.verticalCenter: parent.verticalCenter
                        horizontalAlignment: TextInput.AlignHCenter
                        color: Theme.captionBarText
                        font.pixelSize: Theme.fontSize
                        font.bold: true
                        selectByMouse: true
                        text: viewer.photosModel
                            ? (viewer.photosModel.revision,
                               viewer.photosModel.captionAt(viewer.currentIndex))
                            : ""

                        function rebind() {
                            text = Qt.binding(function () {
                                return viewer.photosModel
                                    ? (viewer.photosModel.revision,
                                       viewer.photosModel.captionAt(viewer.currentIndex))
                                    : ""
                            })
                        }

                        onAccepted: {
                            controller.setCaption(viewer.currentIndex, text)
                            rebind()
                            viewer.forceActiveFocus()
                        }
                        Keys.onEscapePressed: (event) => {
                            rebind()
                            viewer.forceActiveFocus()
                            event.accepted = true
                        }
                    }

                    //: A felszólítás a SÁVBAN áll, a felirat helyén — az
                    //: eredetin („Készítsen képaláírást!") ugyanott, ahol a
                    //: kész felirat lenne (a `235707.jpg` felvételen
                    //: közvetlenül összevethető).
                    Text {
                        objectName: "captionPlaceholder"
                        anchors.centerIn: parent
                        text: qsTr("Make a caption!")
                        color: Theme.captionBarText
                        opacity: 0.7
                        font.pixelSize: Theme.fontSize
                        visible: captionField.text.length === 0
                                 && !captionField.activeFocus
                    }

                    ToolButton {
                        objectName: "captionTrashButton"
                        anchors.right: parent.right
                        anchors.rightMargin: 3
                        anchors.verticalCenter: parent.verticalCenter
                        flat: true
                        implicitWidth: 17
                        implicitHeight: 13
                        text: "✕"
                        //: `captiontrash` — az eredeti buboréksúgója
                        ToolTip.text: qsTr("Delete this caption")
                        ToolTip.visible: hovered
                        ToolTip.delay: Theme.tooltipDelay
                        // üres feliratot nincs mit törölni
                        enabled: captionField.text.length > 0
                        contentItem: Text {
                            text: parent.text
                            color: Theme.captionBarText
                            opacity: parent.enabled ? (parent.hovered ? 1 : 0.7) : 0.3
                            font.pixelSize: Theme.fontSize - 2
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Item {}
                        // #1816 DÖNTÉS: NINCS megerősítés. Az eredetiben ez
                        // szemetes-ikon közvetlen hatással, és a művelet nem
                        // lemezromboló: a felirat egyetlen mező,
                        // újragépelhető. A projekt #459-es elve a
                        // megerősítést a lemezt érintő, visszafordíthatatlan
                        // műveletekre tartja fenn. (Az eredetiről ez NINCS
                        // mérve — saját döntés.)
                        onClicked: {
                            controller.setCaption(viewer.currentIndex, "")
                            captionField.rebind()
                        }
                    }
                }

                // #2587: a felirat-KAPCSOLÓ a fotó-terület BAL ALSÓ sarkában,
                // a sáv állapotától FÜGGETLENÜL. A `.tre` szerint a
                // `captionbutton` `hidetarget`-je csak a `caption` és a
                // `captiontrash`; a felvételen kikapcsolt feliratnál is ott
                // áll a kis világos négyzet — ez az EGYETLEN út vissza.
                //
                // MÉRT geometria (`picasa3-felirat-*.jpg`, mindkét állapotban
                // AZONOS): a fehér doboz x 287…303, y 910…922 — vagyis
                // **17 × 13**, a fotó-terület bal szélétől 1 képponttal, a
                // sáv függőleges közepén.
                //
                // KÉT ÁLLAPOT (`editoneup/caption_icon` és
                // `caption_yesicon`, `oneup.tre:112–124`): bekapcsolt
                // feliratnál a dobozban két vízszintes vonal, kikapcsoltnál
                // ÜRES a doboz. A felvételen pontosan ez látszik.
                Rectangle {
                    id: captionToggle
                    objectName: "captionToggleButton"
                    anchors.left: parent.left
                    anchors.leftMargin: 1
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: viewer.captionVisible
                                          ? (captionBar.height - height) / 2 : 4
                    width: 17
                    height: 13
                    radius: 2
                    visible: viewer.photoOverlaysUsable
                    color: Theme.captionToggleBg
                    border.width: 1
                    border.color: viewer.captionVisible
                                  ? Theme.captionToggleBorder : "transparent"

                    //: `caption_icon`: két vízszintes vonal — CSAK bekapcsolt
                    //: feliratnál (a kikapcsolt állapot doboza üres).
                    Column {
                        anchors.centerIn: parent
                        spacing: 3
                        visible: viewer.captionVisible
                        Repeater {
                            model: 2
                            Rectangle {
                                width: 9
                                height: 1
                                color: Theme.captionToggleBorder
                            }
                        }
                    }

                    ToolTip.text: qsTr("Show/Hide Caption")
                    ToolTip.visible: egerTerulet.containsMouse
                    ToolTip.delay: Theme.tooltipDelay
                    MouseArea {
                        id: egerTerulet
                        anchors.fill: parent
                        //: a MÉRT doboz 17 × 13 — kicsi a kényelmes
                        //: találathoz, ezért az érzékeny terület nagyobb, a
                        //: RAJZ viszont a mért méretű marad
                        anchors.margins: -5
                        hoverEnabled: true
                        onClicked: viewer.billentsdAFeliratot()
                    }
                }


                // elő-betöltés: a szomszédok már dekódolva, mire lépsz —
                // a #84 óta a mappán belüli szomszéd (folderNeighbor), nem
                // a nyers currentIndex±1, hogy ne a szomszéd mappa képét
                // töltsük elő feleslegesen a mappahatárnál
                Image {
                    visible: false
                    source: viewer.photosModel
                        ? viewer.preloadUrlAt(viewer.photosModel.folderNeighbor(viewer.currentIndex, 1))
                        : ""
                    asynchronous: Qt.platform.pluginName !== "offscreen"; autoTransform: true
                    sourceSize.width: 2560
                }
                Image {
                    visible: false
                    source: viewer.photosModel
                        ? viewer.preloadUrlAt(viewer.photosModel.folderNeighbor(viewer.currentIndex, -1))
                        : ""
                    asynchronous: Qt.platform.pluginName !== "offscreen"; autoTransform: true
                    sourceSize.width: 2560
                }
            }

            // #192: Tulajdonságok-panel jobb oldalt — ugyanaz a buta
            // komponens, mint a könyvtár-nézetben (Main.qml), a nézett
            // kép adataival; a bezárás a közös kapcsolót állítja le
            PropertiesPanel {
                objectName: "viewerPropertiesPanel"
                visible: viewer.propertiesOpen
                Layout.preferredWidth: 210
                Layout.minimumWidth: 160
                Layout.fillHeight: true
                hasSelection: viewer.currentIndex >= 0
                // a photos.revision-nel együtt kötve: modell-frissüléskor
                // (pl. forgatás, felirat-mentés) újraolvas; a controller
                // önálló példányosításnál (tesztek) hiányozhat
                entries: (viewer.propertiesOpen && viewer.photosModel
                          && typeof controller !== "undefined" && controller)
                    ? (viewer.photosModel.revision,
                       controller.propertiesOf(viewer.currentIndex))
                    : []
                onCloseRequested: viewer.zarjaAFiokot()
            }

            //: #2566: a másik három lap CSAK AKKOR létezik, ha a NÉZŐ
            //: LÁTSZIK, és épp az a lap aktív.
            //:
            //: ⚠️ Ez nem takarékosság, hanem HELYESSÉG. A három komponens a
            //: SAJÁT gyerekeire éget objectName-et (`placesClearButton`,
            //: `peoplePanelClose`, `tagInput` …), amit a példányosítás
            //: helyén nem lehet felülírni. Mohó példányosítással a
            //: `findChild` a nézőbeli MÁSODPÉLDÁNYT találná meg a
            //: könyvtárbeli helyett — a `test_qml_places.py` két őre
            //: azonnal el is bukott rá, mielőtt `Loader`-be került.
            //: Csukott néző mellett így egyetlen példány van, a könyvtáré.
            //:
            //: ⚠️ A `viewer.visible` NEM elhagyható: a fiók lapját a
            //: KÖNYVTÁRBAN is át lehet kapcsolni, és a `tagsOpen` akkor is
            //: igaz — a néző példánya enélkül a könyvtár-nézetben is
            //: felépülne.
            Loader {
                objectName: "viewerTagsPanelLoader"
                active: viewer.tagsOpen && viewer.visible
                visible: viewer.tagsOpen
                Layout.preferredWidth: 190
                Layout.minimumWidth: 150
                Layout.fillHeight: true
                //: Ugyanaz a buta komponens, mint a könyvtárban; a
                //: különbség csak az, hogy MIRE hat: ott a rács
                //: kijelölésére, itt a nézett képre (`drawerRows`).
                sourceComponent: TagsPanel {
                    objectName: "viewerTagsPanel"
                    hasSelection: viewer.currentIndex >= 0
                    //: a photos.revision-nel együtt kötve: címke-írás után
                    //: azonnal frissül (a könyvtári párja ugyanígy)
                    tags: (viewer.photosModel && viewer.controllerReady
                           && viewer.currentIndex >= 0)
                        ? (viewer.photosModel.revision,
                           controller.keywordsOfRows(viewer.drawerRows))
                        : []
                    onAddRequested: function(keyword) {
                        if (viewer.controllerReady)
                            controller.addKeywordToRows(
                                viewer.drawerRows, keyword)
                    }
                    onRemoveRequested: function(keyword) {
                        if (viewer.controllerReady)
                            controller.removeKeywordFromRows(
                                viewer.drawerRows, keyword)
                    }
                    //: a helyi menü „rátétel a kijelölésre" tétele: a
                    //: nézőben a kijelölés EGY kép, tehát ugyanoda fut,
                    //: mint a hozzáadás
                    onAddToSelectionRequested: function(keyword) {
                        if (viewer.controllerReady)
                            controller.addKeywordToRows(
                                viewer.drawerRows, keyword)
                    }
                    //: a találatok a KÖNYVTÁR rácsán jelennek meg, amit a
                    //: néző eltakarna — ezért a gazda zárja a nézőt, és
                    //: ő keres
                    onFindTaggedRequested: function(keyword) {
                        viewer.findTaggedRequested(keyword)
                    }
                    onCloseRequested: viewer.zarjaAFiokot()
                }
            }

            Loader {
                objectName: "viewerPlacesPanelLoader"
                active: viewer.placesOpen && viewer.visible
                visible: viewer.placesOpen
                Layout.preferredWidth: 320
                Layout.minimumWidth: 220
                Layout.fillHeight: true
                sourceComponent: PlacesPanel {
                    objectName: "viewerPlacesPanel"
                    appWindow: viewer.appWindow
                    //: a geocímkézés a NÉZETT képre hat, nem a rács
                    //: kijelölésére (ld. `drawerRows`)
                    targetRows: viewer.drawerRows
                    //: a térkép-jelölőre kattintva a néző lép oda — a
                    //: könyvtárban ugyanez a jel a rács kijelölését mozgatja
                    onPhotoActivated: function(row) { viewer.show(row) }
                    onClearGeotagRequested: function(rows) {
                        viewer.clearGeotagRequested(rows)
                    }
                    onSetGeotagRequested: function(rows, la, lo) {
                        viewer.setGeotagRequested(rows, la, lo)
                    }
                    onCloseRequested: viewer.zarjaAFiokot()
                }
            }

            Loader {
                objectName: "viewerPeoplePanelLoader"
                active: viewer.peopleOpen && viewer.visible
                visible: viewer.peopleOpen
                Layout.preferredWidth: 200
                Layout.minimumWidth: 160
                Layout.fillHeight: true
                //: A nézett kép nevesített emberei, és akikkel a vizsgált
                //: személy együtt szerepel.
                sourceComponent: PeoplePanel {
                    objectName: "viewerPeoplePanel"
                    selectionCount: viewer.drawerRows.length
                    currentPerson: viewer.controllerReady
                        ? controller.currentPersonName : ""
                    peopleHere: (viewer.photosModel && viewer.controllerReady)
                        ? (viewer.photosModel.revision,
                           controller.peopleOfRows(viewer.drawerRows))
                        : []
                    peopleWith: (viewer.photosModel && viewer.controllerReady
                                 && controller.currentPersonName.length > 0)
                        ? (viewer.photosModel.revision,
                           controller.peopleWith(controller.currentPersonName))
                        : []
                    //: a személy albuma a KÖNYVTÁR rácsán nyílik — a gazda
                    //: zárja a nézőt, és ő vált (ld. `findTaggedRequested`)
                    onPersonChosen: function(name) { viewer.personChosen(name) }
                    onCloseRequested: viewer.zarjaAFiokot()
                }
            }
        }
    }

    //: #2566: a fiók ürítésének EGYETLEN útja a nézőből. A négy fiók-jelző
    //: SZÁRMAZTATOTT (#1773), közvetlenül nem írható — az ablak függvénye
    //: üríti. A `!== undefined` a #1572-őr mintája: a próbák stub-ablakán
    //: nincs rajta a függvény.
    function zarjaAFiokot() {
        if (viewer.appWindow && viewer.appWindow.ureseidAFiokot !== undefined)
            viewer.appWindow.ureseidAFiokot()
    }

    // -- #422: jobbklikk-menü a nagy képen ---------------------------------
    // A nézőben eddig egyáltalán nem volt kontextusmenü (a Picasa `OneUp`
    // menüosztálya, 17 tétel — ld. ViewerContextMenu.qml). A parancsok a
    // globális context property-ken (controller, fileOpsController) át
    // futnak, a törlés dialógusa pedig jelként megy a Main.qml-nek — így a
    // forró Main.qml csak egyetlen bekötést kap.

    readonly property string currentPath: viewer.photosModel
        && viewer.currentIndex >= 0
        ? viewer.photosModel.filePathAt(viewer.currentIndex) : ""

    //: #1612: a menü HALASZTOTT — az `ensure()` az első jobbklikkre építi
    //: fel. Mérve: a `viewerContextMenu` 360 QObject, és a legtöbb
    //: munkamenetben a felhasználó egyszer sem jobbklikkel a nagy képen.
    function openContextMenu(x, y) { viewerMenuLoader.ensure().popup(viewer, x, y) }

    DeferredDialog {
        id: viewerMenuLoader
        objectName: "viewerContextMenuLoader"
        sourceComponent: Component {
        ViewerContextMenu {
        id: viewerMenu
        // a revision-nel együtt kötve, hogy a menü újranyitáskor friss
        // rejtett-állapotot mutasson (a PhotoContextMenu mintája)
        hidden: viewer.photosModel && viewer.currentIndex >= 0
            ? (viewer.photosModel.revision,
               viewer.photosModel.itemAt(viewer.currentIndex).hidden === true)
            : false
        // #305: null-őr — a controller a leépítéskor átmenetileg null lehet
        albums: typeof controller !== "undefined" && controller
            ? controller.albums : []

        // #422: a mentés-parancsok aktív állapota a NÉZETT képre
        hasEdits: viewer.photosModel && viewer.currentIndex >= 0
            ? (viewer.photosModel.revision,
               viewer.photosModel.itemAt(viewer.currentIndex).hasEdits === true)
            : false
        hasBackup: typeof controller !== "undefined" && controller
                   && viewer.currentIndex >= 0
            ? controller.hasSavedBackup([viewer.currentIndex]) : false

        onSaveRequested: viewer.saveRequested(viewer.currentIndex)
        onRevertRequested: viewer.revertRequested(viewer.currentIndex)
        onUndoAllEditsRequested: viewer.undoAllEditsRequested(viewer.currentIndex)
        onResetFacesRequested: viewer.resetFacesRequested()

        onBackToLibraryRequested: viewer.closed()
        onAddToAlbumRequested: function(token) {
            if (typeof controller !== "undefined" && controller)
                controller.addRowsToAlbum([viewer.currentIndex], token)
        }
        onRotateRightRequested: {
            if (typeof controller !== "undefined" && controller
                && viewer.currentIndex >= 0)
                controller.rotateRight(viewer.currentIndex)
        }
        onRotateLeftRequested: {
            if (typeof controller !== "undefined" && controller
                && viewer.currentIndex >= 0)
                controller.rotateLeft(viewer.currentIndex)
        }
        onHideToggleRequested: {
            if (typeof controller !== "undefined" && controller
                && viewer.currentIndex >= 0)
                controller.toggleHiddenRows([viewer.currentIndex])
        }
        onOpenFileRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                && viewer.currentPath.length > 0)
                fileOpsController.openPhoto(viewer.currentPath)
        }
        onLocateRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                && viewer.currentPath.length > 0)
                fileOpsController.revealPhoto(viewer.currentPath)
        }
        onCopyFullPathRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                && viewer.currentPath.length > 0)
                fileOpsController.copyFullPath(viewer.currentPath)
        }
        onDeleteRequested: {
            if (viewer.currentPath.length > 0)
                viewer.deleteRequested(viewer.currentPath)
        }
        onPropertiesRequested: {
            // #1773: a helyi menü a fiók Tulajdonságok lapjára VÁLT (az
            // eredetiben a négy lap kizáró csoport); ha már az látszik, a
            // nézőben a billentyűhöz hasonlóan zárja a fiókot.
            if (viewer.appWindow
                && viewer.appWindow.valtsFiokLapot !== undefined)
                viewer.appWindow.propertiesPanelOpen
                    ? viewer.appWindow.ureseidAFiokot()
                    : viewer.appWindow.valtsFiokLapot("properties")
        }
    }
        }
    }

    // jobbklikk BÁRHOL a nézőn — a Picasában a nagy kép és a körülötte lévő
    // szürke háttér is ugyanezt a menüt nyitja
    TapHandler {
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onSingleTapped: function(point) {
            viewer.openContextMenu(point.position.x, point.position.y)
        }
    }

    // #465 4. pont: a felirat-bemásolás megerősítése (ld.
    // `onTextCopyCaptionRequested`)
    //: #1612: halasztva — a felirat-átvétel megerősítése csak akkor kell, ha
    //: a felhasználó tényleg átveszi a feliratot (mérve: 74 QObject).
    DeferredDialog {
        id: copyCaptionConfirmLoader
        sourceComponent: Component {
            ConfirmDialog {
                namePrefix: "copyCaptionConfirm"
                onConfirmed: editorPanel.textDraftContent = editorPanel.captionText
            }
        }
    }

    // #465: a retus/vörösszem visszavonása ADATOT dob el (nincs „Újra") —
    // az eredeti Picasa két külön szövegével kérdez rá. A döntés-kulcs
    // eszközönként külön, hogy a „Ne kérdezze újra" a másikra ne hasson.
    //: #1612: halasztva — a retus/vörösszem visszavonásának megerősítése csak
    //: akkor kell, ha a felhasználó ilyet vissza is von (mérve: 76 QObject).
    DeferredDialog {
        id: undoDataLossDialogLoader
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "undoDataLossDialog"
                namePrefix: "undoDataLoss"
                title: qsTr("Undo")
                function askFor(key, text) { ask("undo-" + key, text) }
                onConfirmed: editController.undo()
            }
        }
    }

    // #2480: a MODÁLIS párbeszédek elhomályosító rétege. Az eredetiben ez
    // az `editpanel/modaldialogblur` (`editpanel.tre:1362`): a `root`
    // közvetlen gyereke (tehát a TELJES szerkesztő fölé kerül, nem a bal
    // panelen belülre), `m_scaleXY` (a teljes vászonra feszül) és
    // `m_hidden` (alapból rejtett — a modális párbeszéd kapcsolja be).
    //
    // A fájl UTOLSÓ gyereke, hogy a rétegrendben minden fölé kerüljön: a
    // bal panel, az előnézet és a felső sáv is alá esik. A Qt maga a
    // párbeszédet még ennél is fölé rajzolja (külön `QQuickOverlay`), tehát
    // a párbeszéd nem homályosodik el.
    //
    // ⚠️ A MÉRTÉK és a SZÍN a MI döntésünk: a `.tre` csak a réteg létét és
    // kiterjedését adja meg, a rajzot a `respack.yt` rétege adná — az nincs
    // kimérve. A választott érték a vászon-háttér 45%-a: elég ahhoz, hogy a
    // fókusz a párbeszédre kerüljön, de a szerkesztő tartalma átlátszik
    // (a felhasználónak látnia kell, mire válaszol).
    //
    // `enabled: false` — a réteg CSAK látvány: a modalitást a Qt biztosítja
    // (a párbeszéd `modal: true`), egy eseményt elnyelő réteg viszont a
    // párbeszéd bezárása utáni első kattintást is elvinné.
    Rectangle {
        objectName: "editorModalDialogBlur"
        anchors.fill: parent
        z: 1000
        enabled: false
        visible: editorPanel.modalDialogOpen
        color: Theme.canvasBg
        opacity: 0.45
    }

}
