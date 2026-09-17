import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "editorpanel_logika.js" as Logika

// Szerkesztő eszközpanel — a néző bal oldali panelje, Picasa-hű ikonos
// csempékkel (#51). Két mód:
//  - "tools": fülsáv + a kiválasztott fül tartalma + Visszavonás/Újra
//  - eszköz-mód: vágás / retusálás / vörösszem / szöveg — teljes panelt foglal
// Csak UI + állapot: a kép-feldolgozás a render/edit rétegben él.
//
// #496: ez a fájl a KÖZÖS ÁLLAPOT és a FÜL-VÁLTÓ gazdája; a tartalom
// önálló fájlokban él (a projekt bevett mintája, ahogy az `OptionsTab*.qml`
// fájlok is): `EditorTabBar` + `EditTabButton`/`EditTabIcon` a fülsáv,
// `EditorTabCommonFixes`/`EditorFinetunePanel`/`EditorEffectsTab1–4`/
// `EditorLegacyTab` a fülek, `EditorParamPanel` a csúszkás alpanel (#316),
// `EditorCrop`/`Retouch`/`Redeye`/`TextPanel` az eszköz-módok,
// `EditorDialogs` a párbeszédek (#448, #459).
//
// A gyerekek a `panel` tulajdonságon át érik el az állapotot és a jelzéseket;
// a láthatóságot és a horgonyokat MINDIG a gazda adja meg a használat helyén,
// hogy a fülek egymáshoz képest ne csússzanak el.
Rectangle {
    id: panel
    objectName: "editorPanel"
    color: Theme.chromeBg
    // #411: FIX pixelszélesség — az eredeti panel NEM skálázódik az
    // ablakmérettel (a #405 tévesen levetítette; a felhasználó
    // screenshot-összevetése bizonyította a hibát). Ld.
    // docs/specs/design-guide.md „Néző eszközpanel" sorát. A
    // PhotoViewer.qml `Layout.preferredWidth`-jét EZZEL összhangban kell
    // tartani (ott állítva, nem itt).
    implicitWidth: 280

    // #628: „mindig elfér" garancia. Az eredetiben a panel FIX méretű, és a
    // kényszer-alapú elrendezésben a tartalom mindig kifér — görgetésre
    // nincs szükség. Átméretezhető ablakban ennek a megfelelője a panel
    // implicit magassága: fülsáv + a LEGMAGASABB fül + a Visszavonás/Újra
    // sor. Nem az AKTÍV fülé, hogy a panel magassága fülváltáskor ne
    // ugráljon. A néző ezt a magasságot kapja meg alsó korlátként.
    // #3247: a fül lapjának magassága a MÉRT szám, nem a mi tartalmunk
    // maximuma. Az eredeti `editpanel/tabpanel1` **273 × 277** képpont
    // (`docs/specs/ui-audit-editor.md`, a `respack.yt`-ből képpontról
    // képpontra), és a #3247 óta MINDEN fülünk belefér (a legmagasabb a
    // Finomhangolás, 272; őr: `test_ful_magassag_3247.py`).
    //
    // Miért jobb ez, mint a fülek maximuma:
    //
    // * a #703 szerződése („a panel magassága fülváltáskor ne ugráljon")
    //   ERŐSEBBEN teljesül — a szám állandó, nem a tartalomtól függ;
    //   ⚠️ a paritás is javul: eddig a MI legmagasabb fülünk határozta meg,
    //   mekkora a panel, nem az eredeti mérete;
    // * és a fülek ezzel HALASZTHATÓVÁ válnak (#3244): a magasság nem
    //   olvassa többé mind a hét fül `implicitHeight`-jét, tehát egy
    //   `Loader` mögé tett, még létre nem jött fül nem rontja el.
    //
    // A VÁGÁS-logika változatlan, és továbbra is a LÁTHATÓ fülből dolgozik
    // (`tabContentHeight`) — tehát ha egy fül mégis túlnő a 277-en, a
    // `tabContentTruncated` jelzi, nem némán vágódik le.
    readonly property real mertTabPanelHeight: 277

    // #703: a panel magasság-igénye a fülek tartalma NÉLKÜL — fülsáv,
    // gombsor és a margók. Ez az a magasság, ami alá menni már azt jelenti,
    // hogy a Visszavonás/Újra sornak sincs helye. A hívó (PhotoViewer) ezt
    // használja alsó korlátnak, amikor a képernyőhöz igazítja az ablak
    // minimumát — beégetett szám nélkül.
    readonly property real chromeHeight:
        10 + tabBar.height + 6 + globalUndoRow.height + 10
    implicitHeight: panel.chromeHeight + panel.mertTabPanelHeight

    //: #3220: a számítás a `editorpanel_logika.js`-ben (`lathatoMagassag`)
    //: — az ős-lánc bejárása és az indoklása ott olvasható. A kötés-
    //: függőségek változatlanok: a függvény ugyanazokat a `y`/`height`
    //: tulajdonságokat olvassa, tehát a QML ugyanúgy újraszámol.
    readonly property real visibleHeight: Logika.lathatoMagassag()

    //: #3220: a számítás a `editorpanel_logika.js`-ben
    //: (`fulTartalomMagassag`) — a #659/#703 indoklás ott olvasható.
    readonly property real tabContentHeight: Logika.fulTartalomMagassag()

    readonly property real tabAreaAvailable:
        Math.max(0, globalUndoRow.y - 6 - tabArea.y)
    readonly property bool tabContentTruncated:
        tabArea.visible && panel.tabContentHeight > panel.tabAreaAvailable + 0.5

    // #641: a gombsor alja a panelen belül — az őr-teszt ebből számolja ki,
    // hogy a sor a néző LÁTHATÓ területén belül maradt-e. (A sor a panel
    // gyereke, kívülről id-vel nem érhető el.)
    readonly property real undoRowBottom: globalUndoRow.y + globalUndoRow.height

    // aktív fül: 0 = Gyakori javítások, 1 = Finomhangolás, 2–4 = a három
    // eredeti effekt-fül (#328), 5 = további effektek (#422), 6 = Régi
    // effektek (#571). Az eszköz-módok a fülsávtól függetlenül élnek.
    //
    // SAJÁT FUNKCIÓ (#1187): a fenti 7 fülből csak 5 (0–4. index) van meg
    // az eredeti Picasában — az 5. és a 6. index a MI hozzáadásunk. A
    // bináris-egyezés erre a két fülre NEM vonatkozik: hogy az eredetiben
    // nincs ilyen fül, nem hiba. Lista: docs/decisions/vedett-sajat-funkciok.md
    property int activeTab: 0

    // kapcsoló-állapotok — az aktív eszköz csempéje "benyomva" jelenik meg
    property bool cropActive: false
    property bool tiltActive: false
    property bool redeyeActive: false
    // Retusálás/Szöveg (#148): a Vágás mintáját követő mód-eszközök —
    // kattintással jelölnek a képen, Alkalmaz/Mégse gombbal zárulnak. A
    // hívó (PhotoViewer) tölti a puffer-állapotot (retouchRegionCount,
    // textPlacementPending) az EditControllerből.
    property bool retouchActive: false
    property bool textActive: false
    property int retouchRegionCount: 0
    // #445: kétkattintásos, irányított klónozás — a hívó (PhotoViewer) a
    // controllerből tölti: van-e félbehagyott folt (cél kijelölve, forrás
    // még mozgatás alatt — a "Refining…" felirathoz), a patch-enkénti
    // Undo/Redo elérhetősége, és az ecset mérete [1..100].
    property bool retouchPatchPending: false
    property bool canUndoPatch: false
    property bool canRedoPatch: false
    property int brushSize: 20
    signal brushSizeEdited(int value)
    signal retouchUndoPatchRequested()
    signal retouchRedoPatchRequested()
    signal retouchResetRequested()
    // #445: Vörösszem — a hívó (PhotoViewer) tölti a controllerből a kézi
    // régiók számát, a régiónkénti Visszavonás elérhetőségét és az
    // automatika találat-számát (-1: még nem futott). A
    // `redeyeHideOutlines` tisztán NÉZET-állapot: csak a kijelölő-
    // négyzetek rajzát kapcsolja ki, a javításon nem változtat.
    property int redeyeRegionCount: 0
    property bool canUndoRedeyeRegion: false
    property int redeyeFoundCount: -1
    property bool redeyeHideOutlines: false
    signal redeyeAutoRequested()
    signal redeyeUndoRegionRequested()
    signal redeyeResetRequested()
    signal redeyeApplyRequested()
    signal redeyeCancelRequested()
    // a szövegmező kezdő tartalma (eszköz-nyitáskor a hívó tölti a
    // controller mentett/piszkozat tartalmával); onTextDraftChanged jelzi
    // vissza a felhasználói gépelést
    property string textDraftContent: ""
    property bool textPlacementPending: false
    //: #3123: a kép fölötti eszköz-sáv ebből tudja, mikor alkalmazható a
    //: szöveg (a szövegmező a `EditorTextPanel`-ben él).
    readonly property bool textApplyEnabled:
        //: #3220: a szöveg-panel a mód-eszközök fájljában él
        modeToolScroll.szovegLap ? modeToolScroll.szovegLap.applyEngedve
                                 : false
    // #450: a kép mentett felirata ("Copy Caption" gombhoz) — a hívó
    // (PhotoViewer) tölti a photosModel.captionAt()-ból; üresnél a gomb
    // tiltott. A hasTextOverlay ("Remove all existing text" gombhoz) a
    // controller.hasTextOverlay tükre, a többi (redeyeActive stb.) mintáját
    // követve.
    property string captionText: ""
    property bool hasTextOverlay: false
    // #450: szöveg-stílus — kitöltés+körvonal szín, körvonal-vastagság,
    // kitöltés ki/be, átlátszóság; a hívó tölti a controller mentett
    // értékeivel, az onXChanged jelek viszik vissza a felhasználói módosítást
    property string textFillColor: "#ffffff"
    property string textOutlineColor: "#000000"
    property real textOutlineThickness: 0
    property bool textFillEnabled: true
    property real textOpacity: 1
    // közös őr: crop/retouch/text bármelyike a fülsáv+rács helyett a saját
    // teljes-panelnyi tartalmát mutatja (a cropColumn mintáját folytatva)
    readonly property bool modeToolActive: panel.cropActive || panel.retouchActive
                                            || panel.textActive || panel.redeyeActive
    signal retouchApplyRequested()
    signal retouchCancelRequested()
    signal textDraftEdited(string content)
    signal textApplyRequested()
    signal textCancelRequested()
    signal textCopyCaptionRequested()
    signal textRemoveAllRequested()
    signal textFillColorEdited(string hex)
    signal textOutlineColorEdited(string hex)
    signal textOutlineThicknessEdited(real value)
    signal textFillEnabledEdited(bool value)
    signal textOpacityEdited(real value)
    // #450 (2. lépcső): tipográfia — a hívó (PhotoViewer) tölti a
    // controller mentett értékeivel, az *Edited jelek viszik vissza
    property var fontFamilyCatalogue: []
    readonly property var fontFamilyKeys:
        panel.fontFamilyCatalogue.map(function(f) { return f.key })
    readonly property var fontFamilyLabels:
        panel.fontFamilyCatalogue.map(function(f) { return f.label })
    property string textFontFamily: ""
    //: #2287: a betűméret az eredeti 16 elemű listájából (8…96),
    //: abszolút egészként — nem százalék.
    property int textFontSize: 12
    property var fontSizeChoices: []
    property bool textBold: false
    property bool textItalic: false
    property bool textUnderline: false
    property string textAlign: "left"
    signal textFontFamilyEdited(string key)
    signal textFontSizeEdited(int value)
    signal textBoldEdited(bool value)
    signal textItalicEdited(bool value)
    signal textUnderlineEdited(bool value)
    signal textAlignEdited(string value)
    // egygombos javítások (#116): nem módkapcsolók — a gomb mindig új
    // réteget fűz a láncra, és csak akkor tiltott, ha ugyanez a szűrő a
    // lánc utolsó eleme (a hívó/EditController tölti)
    property bool enhanceEnabled: true
    property bool autolightEnabled: true
    property bool autocolorEnabled: true

    // Visszavonás/Újra (jelenleg a vágásra): a hívó (PhotoViewer) tölti
    property bool undoAvailable: false
    property bool redoAvailable: false
    // #464: a pipetta („semleges szín") aktív-e — a néző ilyenkor a
    // kattintást színmintavételként adja tovább, nem navigációként
    property bool neutralPickerActive: false
    // #464: a pipetta melletti korong színe — a kontroller mentett
    // semleges színe `#rrggbb` alakban, üres string = nincs kijelölve
    property string neutralColor: ""
    signal neutralPickerToggled()
    // #551: a szín-varázspálca NEM az autocolor szűrőt teszi a láncra: a
    // finetune2 „semleges szín" (p4) mezőjét állítja be automatikusan
    // választott színnel — a Picasa saját .picasa.ini-je bizonyítja
    // (finetune2=1,0,0,0,006b8088,0). Ezért külön jelzés, nem toolActivated.
    signal colorWandRequested()

    property string undoLabel: qsTr("Undo")
    property string redoLabel: qsTr("Redo")

    // a kép aktuális szélesség/magasság aránya ("Jelenlegi méretarány"-hoz)
    property real imageAspect: 4 / 3

    // #448: a Kiegyenesítés-figyelmeztetés bekapcsolója — a hívó (PhotoViewer)
    // tölti az `editController.tiltParam !== 0` állapotból (a panel maga NEM
    // ismeri az editControllert, a többi mód-állapot mintáját folytatva).
    property bool straightenActive: false

    // vágás-mód állapota
    property int aspectIndex: 0        // az aspectFullList lista indexe
    property bool aspectRotated: false // Forgatás: fekvő <-> álló

    // Finomhangolás (#20): a hívó (PhotoViewer) tölti a mentett értékekkel;
    // a csúszkák CSAK a syncFinetuneSliders()-en át íródnak, hogy húzás
    // közben ne törje meg a kötést (ld. tiltSlider minta, #131)
    property real fillLight: 0
    property real highlights: 0
    property real shadows: 0
    property real colorTemp: 0
    // #1487: a `hasFinetune` QML-property TÖRÖLVE (2026-09-09) — mérve
    // SENKI nem állította be és senki nem olvasta: a panel deklarált egy
    // tükröt a vezérlő ugyanilyen nevű property-jéhez, de a kötés soha nem
    // készült el. Két holt dolog mutatott egymásra.
    // programozott szinkronnál (nyitás/lapozás/kontroller-frissítés) NEM
    // váltunk ki finetunePreview-t — a tiltSlider mintáját követve
    property bool suppressFinetune: false
    signal finetunePreview(real fill, real highlights, real shadows, real temp)
    signal finetuneCommit(real fill, real highlights, real shadows, real temp)

    // ------------------------------------------------------------------
    // #2146 + #798: a Shift MÁSODLAGOS szűrőt ad kilenc csempén
    // ------------------------------------------------------------------
    //
    // A Shift bitjét a `FUN_005d7c20` olvassa ki (`0x005d7c91`:
    // `push 0x10` → `GetAsyncKeyState` → `mov [ecx+0x33a8], al`).
    //
    // ⚠️ #798 — HELYESBÍTÉS. A #2146 ezt „a fül felépülésekor egyszer"
    // olvasatnak vette, és a panel tényleg csak kétszer kérdezte meg:
    // felépüléskor és fülváltáskor. A tulajdonos jelentette, hogy a
    // Shift ÉLESBEN nem működik — aki az effekt-fülön áll és lenyomja,
    // semmit nem lát. A mérés az olvasat ellen szól: ugyanez a függvény
    // `LoadCursorA`-t és `SetCursor`-t is hív (`imports.csv`), ami
    // mutató-eseményhez tartozik, nem egyszeri felépítéshez.
    //
    // Mostantól a vezérlő ÉLŐ állapotot ad (`shiftAktiv`, eseményszűrő),
    // és ez a kötés követi. A `frissitsdAShiftAllapotot()` megmarad a
    // felépülés pillanatára: akkor még nem volt billentyű-esemény,
    // amiből a szűrő tudhatna (a felhasználó már előtte is nyomhatja).
    //: ⚠️ A `typeof` NEM elhagyható: a QML-próbák egy része vezérlő
    //: NÉLKÜL építi fel a panelt, és a csupasz név ilyenkor
    //: `ReferenceError`-t dob (a CI ezt el is kapta, #798). A
    //: `qml_undefined_or.py` a csupasz alakot átengedte — a `!== undefined`
    //: záradékot látta őrzésnek.
    property bool shiftMasodlagos: (typeof editController !== "undefined"
                                    && editController
                                    && editController.shiftAktiv !== undefined)
        ? editController.shiftAktiv
        : false

    function frissitsdAShiftAllapotot() { return Logika.frissitsdAShiftAllapotot() }

    function allitsdAShiftFigyelest() { return Logika.allitsdAShiftFigyelest() }

    Component.onCompleted: {
        panel.allitsdAShiftFigyelest()
        panel.frissitsdAShiftAllapotot()
    }
    Component.onDestruction: {
        if (typeof editController !== "undefined" && editController
                && typeof editController.figyeldAShiftet === "function")
            editController.figyeldAShiftet(false)
    }

    // Effektek (#20): minden gomb új réteget fűz a láncra (append-only)
    signal effectRequested(string name)

    // Paraméteres effekt-alpanel (#316): a gombra kattintva NEM azonnal a
    // láncra kerül, ha az effektnek vannak csúszkái — helyette megnyílik ez
    // az alpanel, élő előnézettel, Apply/Cancel gombbal. A paraméter nélküli
    // effektek (Sepia, B&W, Warmify, Film Grain, Invert…) VÁLTOZATLANUL egy
    // kattintással, azonnal az effectRequested jelen át alkalmazódnak.
    // #571: van-e a megnyitott kép láncában örökölt (a 7. fülre tartozó)
    // effekt — ettől kap jelzőpontot a fül. Controller nélkül (izolált
    // QML-tesztek) mindig hamis.
    // #305 null-őr: a QML-tesztek egy része CSONK editControllert ad, amin
    // ez a property nem is létezik — az `undefined.length` szkripthibát
    // dobna, amit a #305-ös figyelő hibának vesz.
    readonly property bool legacyEffectsPresent: {
        if (!panel.hasEffectController()) return false
        var inChain = editController.legacyEffectsInChain
        return inChain !== undefined && inChain !== null && inChain.length > 0
    }

    property bool paramPanelActive: false
    property string paramEffectName: ""
    property var paramEffectParams: []   // editController.effectParams(name)
    property var paramEffectValues: []   // a csúszkák pillanatnyi értékei

    // #700: az alpanel CÍME — az effekt emberi, lefordított neve, nem a
    // `filters=` lánc kulcsa (`editpanel/filter_name`, ld.
    // `docs/specs/ui-audit-editor.md` 7.1). Nem külön névtábla: a CSEMPE
    // adja át a saját feliratát (`tryOpenParamPanel(kulcs, felirat)`), így a
    // kettő nem tud elcsúszni. A regiszter (`registry_data.py`) neve erre
    // NEM jó: 7 effektnél eltér a fülön használttól (`unsharp` ott
    // „Sharpen (Old)", a csempén „Sharpen"). Üresen — felirat nélküli,
    // programozott megnyitásnál — a kulcsra esik vissza.
    property string paramEffectLabel: ""
    readonly property string paramEffectTitle:
        panel.paramEffectLabel !== "" ? panel.paramEffectLabel
                                      : panel.paramEffectName

    function hasEffectController() { return Logika.hasEffectController() }

    // #338: az effekt-gombok bélyegképéhez (image://effectthumb/<id>/<effekt>)
    // szükséges fotó-azonosító. Nincs rá külön EditController-property — az
    // editController.previewSource ("image://editpreview/<id>?rev=<n>") már
    // tartalmazza, innen olvassuk ki, hogy ne kelljen az EditController
    // felületét bővíteni (a feladat scope-ja csak ezt a fájlt + a Python
    // bélyegkép-providert engedi). Üres, ha nincs aktív szerkesztés — ekkor
    // az effekt-gombok a korábbi, sima kinézetüket mutatják (thumbSource "").
    readonly property string effectThumbPhotoId: {
        if (!panel.hasEffectController()) return ""
        var src = editController.previewSource
        var prefix = "image://editpreview/"
        if (!src || src.indexOf(prefix) !== 0) return ""
        var rest = src.substring(prefix.length)
        var q = rest.indexOf("?")
        return q >= 0 ? rest.substring(0, q) : rest
    }

    function effectThumbSource(effectName) { return Logika.effectThumbSource(effectName) }

    // #704: melyik szűrő HÁNYSZOR szerepel a szerkesztési láncban — ebből
    // kapja a csempe az „alkalmazva" jelvényt. A `revision`-re frissül (a
    // kontroller `revisionChanged` jele köti), tehát minden lánc-módosítás
    // után újraszámolódik.
    //
    // #305 null-őr: a QML-tesztek egy része CSONK editControllert ad, amin
    // ez a property nem is létezik — üres objektumra esünk vissza.
    readonly property var effectChainCounts: {
        if (!panel.hasEffectController()) return ({})
        var counts = editController.effectChainCounts
        return (counts === undefined || counts === null) ? ({}) : counts
    }

    // #2126: a kék jelvényt a szűrő MÓDJA kapcsolja, nem az alkalmazottság.
    // Az eredetiben a csempeépítő (`0x005d7c20`) a szűrő-leíró `+4` mezőjét
    // olvassa (`mode` egésszé fordítva, `oneclick` → 1), és arra teszi
    // láthatóvá az `fx%d_adorn` vezérlőt. A tulajdonos ott is látott
    // jelvényt, ahol egyetlen effekt sem volt alkalmazva.
    //
    // A forrás EGYETLEN hely: `render.registry.one_click_keys()`, a
    // vezérlőn át. #1572 null-őr: a csonk editController-en nincs rajta.
    readonly property var oneClickEffects: {
        if (!panel.hasEffectController()) return []
        var lista = editController.oneClickEffects
        return (lista === undefined || lista === null) ? [] : lista
    }

    function hasBadge(effectName) { return Logika.hasBadge(effectName) }

    function effectAppliedCount(effectName) { return Logika.effectAppliedCount(effectName) }

    // #411: a "Gyakori javítások" fül csempéi a #405 óta a felhasználó
    // fotójának bélyegképét/effekt-előnézetét mutatták — sötét képnél ez
    // egyforma sötét foltokká olvadt, nem lehetett a csempéket ránézésre
    // megkülönböztetni (ld. #411 issue). Az eredeti Picasa is ezért
    // SAJÁT ikonokat használ ezen a fülön (ld. lent, ToolTile.iconFile) —
    // a korábbi `plainThumbSource()` fotó-bélyegkép-segédfüggvény ezért
    // megszűnt (a 3–5. effekt-fül VÁLTOZATLANUL a fenti
    // `effectThumbSource()`-t használja, az egy külön útvonal).

    function tryOpenParamPanel(name, displayLabel) { return Logika.tryOpenParamPanel(name, displayLabel) }

    function openParamPanel(name, displayLabel) { return Logika.openParamPanel(name, displayLabel) }

    function updateParamValue(index, value) { return Logika.updateParamValue(index, value) }

    function applyParamPanel() { return Logika.applyParamPanel() }

    function cancelParamPanel() { return Logika.cancelParamPanel() }

    function closeParamPanel() { return Logika.closeParamPanel() }

    function paramLabel(key) { return Logika.paramLabel(key) }

    // tool: "crop"|"tilt"|"redeye"|"enhance"|"autolight"|"autocolor"
    signal toolActivated(string tool)
    // a vágás külön jelet is kap — a hívó ez alapján nyitja a CropOverlay-t
    signal cropRequested()
    signal undoRequested()
    signal redoRequested()
    // vágás-mód jelei a hívónak
    signal quickCropRequested(string kind)   // "topleft"|"landscape"|"portrait"
    signal cropRotateRequested()
    signal cropPreviewHold(bool held)
    signal cropResetRequested()
    // #1528: van-e mit alaphelyzetbe állítani — a húzott kijelölés VAGY a
    // mentett vágás megléte. A hívó (PhotoViewer) tölti: a panel sem az
    // overlayt, sem a kontrollert nem ismeri.
    property bool cropResetEnabled: false
    // #448: automatikus vágás-javaslatok — a hívó (PhotoViewer) tölti a
    // kontrollerből (`{key, x, y, w, h}` elemek), és a `cropSuggestionChosen`
    // jelre alkalmazza a kijelölést.
    property var cropSuggestions: []
    signal cropSuggestionChosen(real x, real y, real w, real h)
    // a javaslat felirata a stratégia kulcsából — a stratégiát a kontroller
    // választja (a képtől függ), ezért a felület csak feloldja a nevét
    function cropSuggestionLabel(key) {
        switch (key) {
        case "faces_tight": return qsTr("Close crop to faces")
        case "faces_compose": return qsTr("Compose around faces")
        case "horizon": return qsTr("Crop by horizon")
        case "red_green": return qsTr("Crop by color")
        case "variance": return qsTr("Crop by detail")
        default: return key
        }
    }
    // #448: a javaslat-gombok ELŐNÉZETI bélyegképének forrása — az eredetin
    // mindegyik javaslatnak saját előnézete volt (`editpanel/cropsug_preview%d`).
    //
    // Nem kell hozzá új képszolgáltató: a vágó-eszközben a nagy előnézet
    // (`editController.previewSource`) amúgy is a VÁGATLAN képet mutatja
    // (`enterCropTool` a crop64 nélküli láncot regisztrálja), vagyis pontosan
    // azt a képet, amire a javaslatok számoltak. A gombok ugyanezt az URL-t
    // kérik — a Qt kép-gyorsítótára URL szerint kulcsol, tehát a bélyegképek
    // a MÁR betöltött képet használják, újabb dekódolás és renderelés nélkül.
    // A vágást a `PanelButton.thumbSourceRect` végzi, a megjelenítésben.
    //
    // Üres, ha nincs aktív szerkesztés — ekkor a gombok a felirat-only
    // kinézetükre esnek vissza (a `thumbSource: ""` régi útja).
    // #448: a `hasEffectController()` csak azt mondja meg, hogy VAN vezérlő —
    // azt nem, hogy a `previewSource` már értelmezett. Próba-környezetben (és
    // az indulás egy pillanatában) a vezérlő létezik, a tulajdonsága viszont
    // még `undefined`, amit egy `string` tulajdonság nem tud felvenni
    // („Unable to assign [undefined] to QString" — ezt a CI fogta el, helyben
    // nem jött elő). A kifejezett üres-alapérték ezt zárja.
    readonly property string cropSuggestionThumbSource: {
        if (!panel.hasEffectController())
            return ""
        var forras = editController.previewSource
        return forras ? String(forras) : ""
    }
    signal cropApplyRequested()
    signal cropCancelRequested()

    function emitFinetunePreview() { return Logika.emitFinetunePreview() }
    function syncFinetuneSliders() { return Logika.syncFinetuneSliders() }

    function fillLightMoved(value) { return Logika.fillLightMoved(value) }

    function emitFinetuneCommit() { return Logika.emitFinetuneCommit() }
    function fillLightCommitted() { return Logika.fillLightCommitted() }
    onFillLightChanged: panel.syncFinetuneSliders()
    onActiveTabChanged: {
        panel.syncFinetuneSliders()
        // #2146/#798: az effekt-füleken kell a Shift — ott kapcsoljuk BE a
        // figyelést, máshol KI. A tartalék-olvasás megmarad azoknak a
        // vezérlőknek, amelyek nem ismerik az élő állapotot.
        panel.allitsdAShiftFigyelest()
        panel.frissitsdAShiftAllapotot()
        // #583: fülváltáskor a nyitott effekt-paraméter alpanel BEZÁRUL, és
        // az élő előnézete elvész (a mentett lánc érintetlen marad — ez a
        // Mégse ága). Enélkül nyitva maradt, és mivel a láthatósága csak a
        // `paramPanelActive`-tól függött, RÁRAJZOLÓDOTT a másik fül
        // tartalmára (a felhasználó képernyőképén a vignette-panel a
        // „Gyakori javítások" csúszkái közé keveredve).
        if (panel.paramPanelActive) panel.cancelParamPanel()
    }
    // #448: a vágó-eszköz megnyitásakor a legutóbb használt arány töltődik
    // vissza (lastCropRatio)
    onCropActiveChanged: if (panel.cropActive) panel.restoreLastCropRatio()

    // Arány-lista — a VÁGÓ-eszközé, a #876 mérése szerint PONTOSAN 13 tétel.
    //
    // #448 vezette be, de a lista 19 tételre hízott: hat olyan tétel került
    // bele, ami az eredeti VÁGÓ-listájában nincs. A #876 a `Picasa3.exe`
    // erőforrás-tábláját (9143180–9144420. fájloffszet) és a
    // `stringres-en-hu.tsv`-t vetette össze a mienkkel.
    //
    // ⚠️ A törölt hat NEM tévedés volt, hanem MÁS lista tételei vagy
    // félreolvasott kulcsok:
    //   * `CurrentDisplay` — a KOLLÁZS „Oldalformátum" menüjéé, nem a vágóé;
    //   * `4x4` — nem tétel: a `Desktop4x3` LEÍRÁS-kulcsa
    //     (`AspectRatioList:4x4:Description`), ráadásul 1:1, tehát a
    //     `Square` duplikátuma lett volna;
    //   * `4x6`, `5x7`, `8x10`, `8.5x11` (`FullPage`) — a nyomtatás
    //     méretlistájában vannak, a vágóéban nincsenek.
    //
    // ⚠️ A leírás-sorok kulcsneve FÉLREVEZETŐ: az `AspectRatioList:16x10`,
    // `:5x3`, `:16x9`, `:4x4` sorok a `Widescreen`, `WideFrame`,
    // `HDTV16x9`, `Desktop4x3` tételek leírásai. Aki a kulcsnévből
    // következtet, külön tételnek hiszi őket — nálunk pont ez történt.
    //
    // A négy képernyő-arány felirata KETTŐSPONTOS az eredetiben (`4:3`,
    // `16:10`, `16:9`, `5:3`), a nyomat-méreteké `x`-es (`9x13`) — a
    // hivatalos magyar oszlop szerint.
    //
    // ⚠️ A KOLLÁZS Oldalformátum-menüje ugyanebből az erőforrásból válogat,
    // de MÁS részhalmazt (ott van a `CurrentDisplay` és az `A4PageCollage`).
    // Amikor az sorra kerül (#431), SAJÁT definíciót kapjon — ne ezt.
    //
    // ratio = szélesség/magasság fekvő tájolásban; 0 = kézi (szabad),
    // -1 = a kép jelenlegi aránya.
    readonly property var aspectPresets: [
        { key: "Manual", label: qsTr("Manual"), note: "", ratio: 0 },
        { key: "CurrentRatio", label: qsTr("Current ratio"), note: "", ratio: -1 },
        { key: "5x8m", label: "5x8", note: "", ratio: 8 / 5 },
        { key: "9x13m", label: "9x13", note: qsTr("Small print"), ratio: 13 / 9 },
        { key: "10x15m", label: "10x15", note: qsTr("Large print"),
          ratio: 15 / 10 },
        { key: "Crop13x18m", label: "13x18", note: "", ratio: 18 / 13 },
        { key: "::Crop20x25m", label: "20x25", note: "", ratio: 25 / 20 },
        { key: "::A4", label: "A4", note: qsTr("Full page"), ratio: 297 / 210 },
        { key: "Square", label: qsTr("Square"), note: qsTr("CD Cover"),
          ratio: 1 },
        { key: "Desktop4x3", label: "4:3", note: qsTr("Standard screen"),
          ratio: 4 / 3 },
        { key: "Widescreen", label: "16:10", note: qsTr("Widescreen monitor"),
          ratio: 16 / 10 },
        { key: "HDTV16x9", label: "16:9", note: "HDTV", ratio: 16 / 9 },
        { key: "WideFrame", label: "5:3", note: qsTr("Widescreen Photo Frame"),
          ratio: 5 / 3 }
    ]

    // #448: a beépített lista + a felhasználó egyéni arányai (QSettings-en
    // át, `controller.customAspectRatios`) — EGY listaként, hogy a legördülő
    // és az `aspectIndex` egységesen kezelje mindkettőt.
    readonly property var customAspectRatios:
        (typeof controller !== "undefined" && controller)
            ? controller.customAspectRatios : []

    readonly property var aspectFullList: {
        var list = panel.aspectPresets.slice()
        for (var i = 0; i < panel.customAspectRatios.length; i++) {
            var c = panel.customAspectRatios[i]
            list.push({
                key: "custom:" + c.name + ":" + c.width + "x" + c.height,
                label: c.width + " x " + c.height + "   " + c.name,
                ratio: c.width / c.height,
                isCustom: true,
                customName: c.name,
                customWidth: c.width,
                customHeight: c.height
            })
        }
        return list
    }

    // az aktuálisan kiválasztott tétel — védve az esetleges (törlés utáni)
    // tartomány-túllépéstől
    readonly property var selectedPreset:
        panel.aspectFullList[Math.max(0, Math.min(panel.aspectIndex,
                                               panel.aspectFullList.length - 1))]

    // a kiválasztott arány a Forgatással együtt — a CropOverlay-nek
    readonly property real currentAspect: {
        var base = panel.selectedPreset.ratio
        if (base === 0) return 0
        if (base === -1) base = panel.imageAspect
        // #448 „Jelenlegi megjelenítés": a KÉPERNYŐ aránya (a Picasa
        // ugyanezt a dinamikus tételt kínálta a kép aránya mellett)
        if (base === -2)
            base = (Screen.height > 0) ? Screen.width / Screen.height
                                       : panel.imageAspect
        if (base < 1) base = 1 / base   // fekvő alapállás
        return panel.aspectRotated ? 1 / base : base
    }

    function restoreLastCropRatio() { return Logika.restoreLastCropRatio() }
    function selectAspect(index) { return Logika.selectAspect(index) }

    function handleToolClick(tool) { return Logika.handleToolClick(tool) }

    // #411: SAJÁT rajzú SVG-ikonos eszköz-csempe — a "Gyakori javítások"
    // fülön a #405-ös kör a felhasználó fotójának bélyegképét/effekt-
    // előnézetét tette a csempékre, ez viszont sötét képnél egyforma
    // sötét foltokká olvadt össze (ld. #411 issue). Az eredeti Picasa
    // ezért NEM a fotót mutatja ezen a fülön, hanem saját, világos
    // ikonkészletet (a #361-es icons/ mappa stílusában, ld. lent az
    // `iconFile`-eket) — ezek sötét képnél is ránézésre
    // megkülönböztethetők. A 3–5. effekt-fül (PanelButton, nem ToolTile)
    // VÁLTOZATLANUL a felhasználó fotójának effekt-előnézetét mutatja
    // (image://effectthumb/…) — az egy teljesen külön komponens/útvonal.

    // egyszerű panel-gomb (PicasaButton-színvilág). #338: opcionális
    // effekt-bélyegkép — ha a `thumbSource` üres (az Undo/Redo/Apply/
    // Cancel/vágás-gombak sose adnak meg ilyet), a gomb a korábbi, sima
    // kinézetét mutatja, VÁLTOZATLANUL — ez a legtöbb PanelButton-hívó.

    // #450: kitöltés/körvonal szín-választó — rögzített, PicasaPy-saját
    // színpaletta (nincs a projektben natív ColorDialog-használat, ld.
    // #450 jelentés), a kijelölt szín kék kerettel jelölt. A `currentColor`
    // a controller mentett/piszkozat értékét tükrözi, `colorPicked` viszi
    // vissza a kattintást a hívóhoz.

    // ---------------- fülsáv: Gyakori javítások / Finomhangolás / Effektek /
    // 4. effekt-fül / 5. effekt-fül (#20, #328) — csak "tools" módban,
    // vágásnál (cropColumn) nincs értelme. Öt egyenlő szélességű fül fér el
    // a panel szélességében (Layout.fillWidth mindegyiken, ld. #328 4. pont).
    EditorTabBar {
        id: tabBar
        objectName: "editTabBar"
        panel: panel
        visible: !panel.modeToolActive
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        // #741: a TARTALOM-OSZLOP a mért 276 képpont (x 3..279) — a
        // korábbi 10-10 képpontos margó 260-at hagyott, ettől lett a
        // fülsáv és minden alatta lévő rács keskenyebb az eredetinél.
        // (`docs/specs/szerkeszto-panel-meretek.md` 1.)
        anchors.leftMargin: 3
        anchors.rightMargin: 1
        anchors.topMargin: 10
    }

    //: #3220: a fülek önálló fájlba kerültek, a `editorpanel_logika.js`
    //: viszont NÉVVEL hivatkozik kettőre — ez a két tükör tartja a
    //: logikát változatlanul (a nevek szándékosan a RÉGIEK).
    readonly property Item finetunePanel: tabArea.finomhangoloLap
    readonly property Item fixesTab: tabArea.gyakoriLap

    // ---------------- a FÜLEK közös területe (NEM görgethető) ----------
    //
    // A terület és a hét fül önálló fájlban él (#3220) — az indoklások
    // (#422/#616/#628/#703) ott olvashatók (`EditorTabHost.qml`).
    EditorTabHost {
        id: tabArea
        panel: panel
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        // #741: a fülterület a fülsávval AZONOS 276 képpontos
        // tartalom-oszlop (x 3..279)
        anchors.leftMargin: 3
        anchors.rightMargin: 1
    }








    // #616: a csúszkás alpanel a fülek görgethető területén KÍVÜL
    // marad: maga is Flickable (saját vágással és görgetéssel), és egy
    // Flickable implicit magassága 0 — becsomagolva nulla magasságot
    // kapna, azaz eltűnne. A gombsorig érő horgony itt is megvan.
    // ---------------- effekt-paraméter alpanel (#316) ----------------
    // #496: a tartalom önálló fájlban (EditorParamPanel.qml).
    EditorParamPanel {
        id: effectParamScroll
        objectName: "editorEffectParamScroll"
        panel: panel
        visible: !panel.modeToolActive && panel.paramPanelActive
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: globalUndoRow.top
        anchors.bottomMargin: 6
    }

    // #316: húzás közben az egyes csúszka-változásokat nem küldjük azonnal
    // (élő előnézetenként) az editControllernek — kis késleltetéssel
    // összefogjuk (a Main.qml folderPaneWidthSaver-mintája), de az Apply
    // előtt az utolsó érték mindenképp átmegy (applyParamPanel közvetlenül
    // a friss paramEffectValues-t küldi, nem a timertől függ).
    Timer {
        id: paramPreviewTimer
        interval: 60
        onTriggered: if (panel.hasEffectController())
            editController.previewEffect(panel.paramEffectName,
                                          panel.paramEffectValues)
    }

    // ---------------- mód-eszközök (vágás/retusálás/vörösszem/szöveg) ----
    //
    // A négy mód-panel és a görgethető keretük önálló fájlban él
    // (#3220) — az indoklások (#778 és társai) ott olvashatók
    // (`EditorModeTools.qml`).
    EditorModeTools {
        id: modeToolScroll
        panel: panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: globalUndoRow.top
        anchors.bottomMargin: 6
    }

    // #448: "AddCustomAspectRatio" — szélesség × magasság + név bekérő; a
    // hívó (fent, a "Add Custom Aspect Ratio…" sor) nyitja, a `created`
    // jelre a controlleren át QSettings-be ír (CustomAspectRatiosMixin) és
    // rögtön ki is választja az újonnan felvett arányt.
    AddCustomAspectRatioDialog {
        id: addCustomAspectRatioDialog
        onCreated: (newWidth, newHeight, newName) => {
            if (typeof controller === "undefined" || !controller) return
            controller.addCustomAspectRatio(newWidth, newHeight, newName)
            // az új tétel a lista VÉGÉN jelenik meg (a beépítettek után) —
            // a customAspectRatios friss hosszából számolható az indexe
            // (a hozzáadás óta +1 hosszú lista utolsó eleme)
            panel.selectAspect(panel.aspectPresets.length
                + panel.customAspectRatios.length - 1)
        }
    }

    // ---------------- párbeszédek (#448, #459) ----------------
    // #496: külön fájlban (EditorDialogs.qml).
    EditorDialogs {
        id: editorDialogs
        panel: panel
    }

    //: #2480: nyitva van-e a szerkesztő valamelyik MODÁLIS párbeszéde. A
    //: gazda (`PhotoViewer`) ebből teszi ki az elhomályosító réteget —
    //: az eredetiben ez a `editpanel/modaldialogblur` (`editpanel.tre:1362`),
    //: ami a `root` gyereke, tehát a TELJES szerkesztő fölé kerül, nem a bal
    //: panelen belülre.
    readonly property bool modalDialogOpen:
        editorDialogs.anyModalOpen || addCustomAspectRatioDialog.visible



    // ---------------- #464: GLOBÁLIS Visszavonás/Újra ----------------
    //
    // A sor önálló fájlban él (#3220) — az indoklások és a mért
    // geometria ott olvashatók (`EditorUndoRow.qml`).
    EditorUndoRow {
        id: globalUndoRow
        panel: panel
        tabArea: tabArea
        anchors.left: parent.left
        anchors.right: parent.right
        // #741: a MÉRT geometria — a két gomb x 7..139 és x 144..276
        anchors.leftMargin: 7
        anchors.rightMargin: 4
    }
}
