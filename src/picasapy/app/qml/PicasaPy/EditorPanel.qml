import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Szerkesztő eszközpanel — a néző bal oldali "Gyakori javítások" füle,
// Picasa-hű ikonos csempékkel (#51). Két mód:
//  - "tools": ikonrács + Derítőfény + Visszavonás/Újra
//  - "crop":  "Fotó vágása" — arány-lista, gyorsvágások, gombok
// Csak UI + állapot: a kép-feldolgozás a render/edit rétegben él.
Rectangle {
    id: panel
    objectName: "editorPanel"
    color: Theme.chromeBg
    // #411: FIX pixelszélesség — az eredeti Picasa szerkesztő-eszközpanelje
    // NEM skálázódik az ablakmérettel (ellentétben pl. a mappapanellel,
    // ahol az arányos levetítés helyénvaló). A #405-ös kör TÉVESEN
    // ablakarányosan skálázta le a design-guide screenshot-mért ~280px-es
    // referenciáját 1280px-es ablakra (280 × 1280/1920 ≈ 187 → 190) — a
    // felhasználó screenshot-összevetése bizonyította a hibát: ~955px
    // széles ablaknál az eredeti panel ~275px, a miénk csak ~195px volt,
    // AZONOS ablakméret mellett. A helyes érték tehát fix 280px, bármilyen
    // ablakszélességnél (ld. docs/specs/design-guide.md "Néző eszközpanel"
    // sorát — kifejezetten NEM skálázandó). A PhotoViewer.qml
    // `Layout.preferredWidth`-jét is EZZEL összhangban kell tartani (ott
    // állítva, nem itt).
    implicitWidth: 280

    // aktív fül: 0 = Gyakori javítások, 1 = Finomhangolás, 2 = Effektek,
    // 3 = 4. effekt-fül (zöld ecset), 4 = 5. effekt-fül (kék ecset) — #328,
    // az eredeti Picasa 5 ikonos füle (docs/specs/ui-audit-editor.md, 1. szak.)
    // (a vágó-mód a fülsávtól függetlenül, a cropColumn-on át él)
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
    // a szövegmező kezdő tartalma (eszköz-nyitáskor a hívó tölti a
    // controller mentett/piszkozat tartalmával); onTextDraftChanged jelzi
    // vissza a felhasználói gépelést
    property string textDraftContent: ""
    property bool textPlacementPending: false
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
                                            || panel.textActive
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
    // egygombos javítások (#116): nem módkapcsolók — a gomb mindig új
    // réteget fűz a láncra, és csak akkor tiltott, ha ugyanez a szűrő a
    // lánc utolsó eleme (a hívó/EditController tölti)
    property bool enhanceEnabled: true
    property bool autolightEnabled: true
    property bool autocolorEnabled: true

    // Visszavonás/Újra (jelenleg a vágásra): a hívó (PhotoViewer) tölti
    property bool undoAvailable: false
    property bool redoAvailable: false
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
    property bool hasFinetune: false
    // programozott szinkronnál (nyitás/lapozás/kontroller-frissítés) NEM
    // váltunk ki finetunePreview-t — a tiltSlider mintáját követve
    property bool suppressFinetune: false
    signal finetunePreview(real fill, real highlights, real shadows, real temp)
    signal finetuneCommit(real fill, real highlights, real shadows, real temp)

    // Effektek (#20): minden gomb új réteget fűz a láncra (append-only)
    signal effectRequested(string name)

    // Paraméteres effekt-alpanel (#316): a gombra kattintva NEM azonnal a
    // láncra kerül, ha az effektnek vannak csúszkái — helyette megnyílik ez
    // az alpanel, élő előnézettel, Apply/Cancel gombbal. A paraméter nélküli
    // effektek (Sepia, B&W, Warmify, Film Grain, Invert…) VÁLTOZATLANUL egy
    // kattintással, azonnal az effectRequested jelen át alkalmazódnak.
    property bool paramPanelActive: false
    property string paramEffectName: ""
    property var paramEffectParams: []   // editController.effectParams(name)
    property var paramEffectValues: []   // a csúszkák pillanatnyi értékei

    // #305 null-őr — de ITT szigorúbb annál: az EditorPanel-t önállóan (a
    // `PicasaPy 1.0` modulon át) betöltő tesztek (test_editor_tabs.py,
    // test_editor_effects.py, test_qml_editor_panel.py) az editController
    // kontextus-property-t EGYÁLTALÁN nem állítják be — ott a bare
    // `editController` hivatkozás ReferenceError-t dobna. A `typeof` ezt is
    // lekezeli (nem csak a null-esetet), ezért a régi izolált tesztek
    // változatlanul a sima effectRequested-útra esnek vissza.
    function hasEffectController() {
        return typeof editController !== "undefined" && editController !== null
    }

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

    // az adott effekt bélyegkép-URL-je, vagy "" ha nincs aktív szerkesztés
    // (a hívó PanelButton ilyenkor a régi sima kinézetére esik vissza). A
    // fotó ALAP állapotán mutatja az effektet (nem a jelenlegi szerkesztési
    // láncon) — ld. effect_thumbnails.py modul-docstringjének indoklását.
    // NINCS "?rev="-féle cache-buster: a bélyegkép csak a FOTÓTÓL függ, a
    // szerkesztési lánc (undo/redo/csúszka-húzás) nem érvényteleníti — ez
    // adja a kért "effektenként csak egyszer" gyorsítótárazást.
    function effectThumbSource(effectName) {
        if (panel.effectThumbPhotoId === "") return ""
        return "image://effectthumb/" + panel.effectThumbPhotoId + "/" + effectName
    }

    // #411: a "Gyakori javítások" fül csempéi a #405 óta a felhasználó
    // fotójának bélyegképét/effekt-előnézetét mutatták — sötét képnél ez
    // egyforma sötét foltokká olvadt, nem lehetett a csempéket ránézésre
    // megkülönböztetni (ld. #411 issue). Az eredeti Picasa is ezért
    // SAJÁT ikonokat használ ezen a fülön (ld. lent, ToolTile.iconFile) —
    // a korábbi `plainThumbSource()` fotó-bélyegkép-segédfüggvény ezért
    // megszűnt (a 3–5. effekt-fül VÁLTOZATLANUL a fenti
    // `effectThumbSource()`-t használja, az egy külön útvonal).

    // egy effekt-gomb kattintása: ha az effektnek vannak paraméterei,
    // megnyitja az alpanelt és true-t ad vissza — ilyenkor a hívó (a gomb
    // onButtonClicked-je) NEM küldi az effectRequested jelet. Egyébként
    // (vagy ha nincs editController — ld. fent) false-t ad vissza, és a
    // gomb VÁLTOZATLANUL a meglévő effectRequested jelet küldi tovább. Az
    // effectRequested hívás szó szerinti (nem változóból font) formája
    // minden gombnál megmarad, csak feltételesen fut le — a
    // test_effect_names.py #315-ös regex-alapú lefedettség-ellenőrzése
    // erre épít.
    function tryOpenParamPanel(name) {
        if (panel.hasEffectController() && editController.effectHasParams(name)) {
            panel.openParamPanel(name)
            return true
        }
        return false
    }

    // az alpanel megnyitása: csúszkák a katalógus alapértékein, azonnali
    // élő előnézettel.
    function openParamPanel(name) {
        if (!panel.hasEffectController()) return
        var params = editController.effectParams(name)
        var values = []
        for (var i = 0; i < params.length; i++) values.push(params[i].default)
        panel.paramEffectName = name
        panel.paramEffectParams = params
        panel.paramEffectValues = values
        panel.paramPanelActive = true
        editController.previewEffect(name, values)
    }

    // egy csúszka húzása: az értéklista frissítése + késleltetett előnézet —
    // a folderPaneWidthSaver mintája (Main.qml): ne hívjunk feleslegesen
    // minden pixelnyi elmozdulásnál, de az utolsó érték mindig átmegy.
    function updateParamValue(index, value) {
        panel.paramEffectValues[index] = value
        paramPreviewTimer.restart()
    }

    // Apply: a beállított értékekkel a láncra (undo + mentés), vissza a rácsra.
    function applyParamPanel() {
        paramPreviewTimer.stop()
        if (panel.hasEffectController())
            editController.applyEffectWithParams(panel.paramEffectName,
                                                  panel.paramEffectValues)
        panel.closeParamPanel()
    }

    // Cancel: az előnézet elvetése (a mentett lánc marad érintetlen),
    // vissza a rácsra.
    function cancelParamPanel() {
        paramPreviewTimer.stop()
        if (panel.hasEffectController())
            editController.discardEffectPreview()
        panel.closeParamPanel()
    }

    function closeParamPanel() {
        panel.paramPanelActive = false
        panel.paramEffectName = ""
        panel.paramEffectParams = []
        panel.paramEffectValues = []
    }

    // a csúszka-feliratok fordítása (#316): a `label` a Pythonból (
    // app/effect_params.py) angol kulcsszöveg jön — a lupdate ezt nem látja,
    // ezért itt statikus qsTr(...) hívásokkal soroljuk fel az ÖSSZES
    // lehetséges feliratot; az ismeretlent változatlanul adjuk vissza.
    function paramLabel(key) {
        switch (key) {
        case "Amount": return qsTr("Amount")
        case "Saturation": return qsTr("Saturation")
        case "Inner Radius": return qsTr("Inner Radius")
        case "Strength": return qsTr("Strength")
        case "Intensity": return qsTr("Intensity")
        case "Radius": return qsTr("Radius")
        case "Center X": return qsTr("Center X")
        case "Center Y": return qsTr("Center Y")
        case "Size": return qsTr("Size")
        case "Sharpness": return qsTr("Sharpness")
        case "Preserve Color": return qsTr("Preserve Color")
        case "Gradient": return qsTr("Gradient")
        case "Shade": return qsTr("Shade")
        case "Block Size": return qsTr("Block Size")
        case "Blur Radius": return qsTr("Blur Radius")
        case "Brightness": return qsTr("Brightness")
        case "Color Mix": return qsTr("Color Mix")
        case "Edge Strength": return qsTr("Edge Strength")
        case "Posterize": return qsTr("Posterize")
        case "Smoothness": return qsTr("Smoothness")
        case "Width": return qsTr("Width")
        case "Border Width": return qsTr("Border Width")
        case "Angle": return qsTr("Angle")
        case "Blur": return qsTr("Blur")
        case "Line Position": return qsTr("Line Position")
        default: return key
        }
    }

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
    signal cropApplyRequested()
    signal cropCancelRequested()

    // a négy csúszka aktuális értékét egyben küldi (élő előnézet)
    function emitFinetunePreview() {
        panel.finetunePreview(finetuneFillSlider.value,
                               finetuneHighlightsSlider.value,
                               finetuneShadowsSlider.value,
                               finetuneTempSlider.value)
    }
    // a csúszkák a mentett (kontroller) értékekre állnak — előnézet nélkül
    function syncFinetuneSliders() {
        panel.suppressFinetune = true
        finetuneFillSlider.value = panel.fillLight
        fixesFillSlider.value = panel.fillLight   // #337: a másik fül párja
        finetuneHighlightsSlider.value = panel.highlights
        finetuneShadowsSlider.value = panel.shadows
        finetuneTempSlider.value = panel.colorTemp
        panel.suppressFinetune = false
    }

    // #337: a Kitöltő fény KÉT helyen látszik (Gyakori javítások és
    // Finomhangolás), de EGY beállítás — amelyiket húzzák, a másik követi.
    // A visszacsatolást a suppressFinetune zárja ki: a párja beállítása nem
    // vált ki újabb előnézetet, csak a húzott csúszka.
    function fillLightMoved(value) {
        if (panel.suppressFinetune)
            return
        panel.suppressFinetune = true
        finetuneFillSlider.value = value
        fixesFillSlider.value = value
        panel.suppressFinetune = false
        panel.emitFinetunePreview()
    }

    function fillLightCommitted() {
        panel.finetuneCommit(finetuneFillSlider.value,
                             finetuneHighlightsSlider.value,
                             finetuneShadowsSlider.value,
                             finetuneTempSlider.value)
    }
    onFillLightChanged: panel.syncFinetuneSliders()
    onActiveTabChanged: panel.syncFinetuneSliders()
    // #448: a vágó-eszköz megnyitásakor a legutóbb használt arány töltődik
    // vissza (lastCropRatio)
    onCropActiveChanged: if (panel.cropActive) panel.restoreLastCropRatio()

    // Arány-lista (#448 — a Picasa BINÁRISÁBAN élő kulcskészlet szerint,
    // ld. a #448 jegy 2026-08-07-es javító kommentjét: "ha egyszer
    // implementáljuk, a KULCSNEVEKET használjuk, ne a magyarázatokat").
    // `key` = a bináris tényleges kulcsneve (perzisztenciához, lastCropRatio-
    // hoz); `label` = megjelenő felirat, a kulcsnevet követve (pl. "4x6"),
    // KIVÉVE ahol a kulcs maga nem arány-pár (Manual/CurrentRatio/Square/
    // FullPage) — ott a korábbi, leíró feliratot tartottuk meg.
    // ratio = szélesség/magasság fekvő tájolásban; 0 = kézi (szabad),
    // -1 = a kép jelenlegi aránya.
    //
    // KIHAGYVA (a jegy kommentje szerint az arányuk NEM vezethető le
    // egyértelműen a kulcsnévből, találgatás helyett kimaradtak — ld. a
    // feladat jelentése): `CurrentDisplay`, `WideFrame`, `Widescreen`, `Other`.
    // A `20x25` a MEGLÉVŐ listában volt, de a javított kulcslistában NEM
    // szerepel — nem törölve (a felhasználó dönt róla), csak jelezve.
    readonly property var aspectPresets: [
        { key: "Manual", label: qsTr("Manual"), ratio: 0 },
        { key: "CurrentRatio", label: qsTr("Current ratio"), ratio: -1 },
        { key: "4x4", label: "4x4", ratio: 1 },
        { key: "Desktop4x3", label: "4x3", ratio: 4 / 3 },
        { key: "4x6", label: "4x6", ratio: 6 / 4 },
        { key: "5x7", label: "5x7", ratio: 7 / 5 },
        { key: "8x10", label: "8x10", ratio: 10 / 8 },
        { key: "5x3", label: "5x3", ratio: 5 / 3 },
        { key: "9x13", label: "9x13", ratio: 13 / 9 },
        { key: "10x15", label: "10x15", ratio: 15 / 10 },
        { key: "13x18", label: "13x18", ratio: 18 / 13 },
        // ld. fent: nincs a #448 javított kulcslistában, megtartva
        { key: "20x25", label: "20x25", ratio: 25 / 20 },
        { key: "5x8", label: "5x8", ratio: 8 / 5 },
        { key: "16x10", label: "16x10", ratio: 16 / 10 },
        { key: "HDTV16x9", label: "16x9", ratio: 16 / 9 },
        { key: "Square", label: qsTr("Square"), ratio: 1 },
        { key: "FullPage", label: qsTr("Full page (A4)"), ratio: 297 / 210 }
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
        if (base < 1) base = 1 / base   // fekvő alapállás
        return panel.aspectRotated ? 1 / base : base
    }

    // #448 `lastCropRatio`: az eszköz megnyitásakor a legutóbb használt
    // arányt tölti vissza (QSettings-ből, `controller` közvetítésével) — a
    // hívó (`onCropActiveChanged` a fájl végén) hívja.
    function restoreLastCropRatio() {
        if (typeof controller === "undefined" || !controller) return
        var key = controller.lastCropRatio
        for (var i = 0; i < panel.aspectFullList.length; i++) {
            if (panel.aspectFullList[i].key === key) {
                panel.aspectIndex = i
                return
            }
        }
    }
    function selectAspect(index) {
        panel.aspectIndex = index
        panel.aspectRotated = false
        if (typeof controller !== "undefined" && controller) {
            var key = panel.aspectFullList[index].key
            if (key) controller.setLastCropRatio(key)
        }
    }

    // egy csempe-kattintás kezelése: mód-eszköznél kapcsoló-állapot váltása,
    // egygombos javításnál (#116) csak jelzés — tiltott gombnál no-op
    function handleToolClick(tool) {
        switch (tool) {
        case "crop": panel.cropActive = !panel.cropActive; break
        case "tilt": panel.tiltActive = !panel.tiltActive; break
        case "redeye": panel.redeyeActive = !panel.redeyeActive; break
        case "retouch": panel.retouchActive = !panel.retouchActive; break
        case "text": panel.textActive = !panel.textActive; break
        case "enhance": if (!panel.enhanceEnabled) return; break
        case "autolight": if (!panel.autolightEnabled) return; break
        case "autocolor": if (!panel.autocolorEnabled) return; break
        }
        panel.toolActivated(tool)
        if (tool === "crop") panel.cropRequested()
    }

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
    component ToolTile: Item {
        id: tile
        required property string toolName
        required property string label
        // a "icons/<iconFile>.svg" fájlnév (kiterjesztés nélkül) — a
        // panel.qmlDir szerinti "icons/" mappában, ld. #361/#411
        required property string iconFile
        property bool active: false
        property bool tileEnabled: true
        signal activated(string tool)

        Layout.fillWidth: true
        // #405/#411: nagyobb csempe — az ikon a Picasa-mintát követve
        // jóval nagyobb helyet foglal, mint a korábbi 40×30-as PNG-ikon
        Layout.preferredHeight: 84
        // az öröklött enabled is számít (#103): videónál a PhotoViewer az
        // egész panelt tiltja — a csempe ilyenkor vizuálisan is szürkül
        enabled: tile.tileEnabled
        opacity: tile.enabled ? 1 : 0.4

        Rectangle {
            anchors.fill: parent
            radius: 3
            // #314: sem "#cfe4f7", sem "#e8eef4" nem olvasható sötét
            // témában (fix világos árnyalatok) — a jelző-kék tokenből
            // (Theme.selectionBlue) származtatott áttetsző rétegre váltva
            // mindkét témán kontrasztos marad, a hover halványabb az aktívnál.
            color: tile.active
                   ? Qt.rgba(Theme.selectionBlue.r, Theme.selectionBlue.g,
                             Theme.selectionBlue.b, 0.45)
                   : (tileMouse.containsMouse && tile.tileEnabled
                      ? Qt.rgba(Theme.selectionBlue.r, Theme.selectionBlue.g,
                                Theme.selectionBlue.b, 0.18)
                      : "transparent")
            border.width: tile.active ? 1 : 0
            border.color: Theme.selectionBlue
        }

        // #411: az ikon területe — SAJÁT rajzú SVG, MINDIG betöltve (nincs
        // aszinkron várakozás/helyőrző-eset, mint a fotó-bélyegképeknél).
        Item {
            id: tileThumbBox
            anchors.top: parent.top
            anchors.topMargin: 4
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width - 8
            height: 54

            Image {
                id: tileIconImg
                objectName: tile.objectName ? tile.objectName + "Icon" : ""
                anchors.centerIn: parent
                // #411: az ikonok FEKVŐ (3:2) arányúak, mint az eredeti
                // Picasa 44x29-es gombképei — négyzetes dobozban a rajz
                // zsugorodna/torzulna, ezért 3:2 méret + PreserveAspectFit.
                width: 54; height: 36
                fillMode: Image.PreserveAspectFit
                source: "icons/" + tile.iconFile + ".svg"
                sourceSize: Qt.size(108, 72)
                smooth: true
            }
        }
        Text {
            anchors.top: tileThumbBox.bottom
            anchors.topMargin: 4
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width - 2
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            lineHeight: 0.9
            text: tile.label
            font.pixelSize: Theme.fontSize - 2
            color: Theme.textDark
        }
        MouseArea {
            id: tileMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: tile.activated(tile.toolName)
        }
    }

    // egyszerű panel-gomb (PicasaButton-színvilág). #338: opcionális
    // effekt-bélyegkép — ha a `thumbSource` üres (az Undo/Redo/Apply/
    // Cancel/vágás-gombak sose adnak meg ilyet), a gomb a korábbi, sima
    // kinézetét mutatja, VÁLTOZATLANUL — ez a legtöbb PanelButton-hívó.
    component PanelButton: Rectangle {
        id: pbtn
        property string label: ""
        property bool buttonEnabled: true
        // "" = sima gomb (korábbi kinézet); egyébként image://effectthumb/…
        property string thumbSource: ""
        // #450: opcionális hover-buboréksúgó (pl. "Copy Caption" gomb) —
        // üres stringnél nincs tooltip (a legtöbb PanelButton-hívó)
        property string tooltip: ""
        signal buttonClicked()
        Layout.fillWidth: true
        // #318: a felirat teljesen olvasható kell legyen. Bélyegképes
        // gombnál a kép + felirat együttes magassága számít, sima gombnál
        // (a régi mintát megtartva) csak a feliraté, 24px alsó korláttal.
        Layout.preferredHeight: pbtn.thumbSource !== ""
            ? pbtnThumbBox.height + pbtnLabel.implicitHeight + 12
            : Math.max(24, pbtnLabel.implicitHeight + 10)
        radius: 3
        border.width: 1
        border.color: Theme.chromeBorder
        // pbtn.enabled = buttonEnabled ÉS az öröklött (panel-)enabled (#103)
        enabled: pbtn.buttonEnabled
        // #314: fix világos hexák ("#fdfdfd"/"#d8d8d8"/"#ececec") helyett
        // téma-tokenekből — sötét témában a gomb is sötétedik, így a
        // (szintén témafüggő) Theme.textDark felirat olvasható marad rajta.
        color: !pbtn.enabled ? Theme.chromeBg
               : (pbtnMouse.pressed ? Qt.darker(Theme.buttonBg, 1.15) : Theme.buttonBg)

        // #338: a bélyegkép-terület — csak akkor foglal helyet, ha van
        // thumbSource. A KÉSZ bélyegképig (Image.status !== Ready) a
        // helyőrző-keret mutatja, hogy a gomb SOHA ne legyen üres/villogó.
        Item {
            id: pbtnThumbBox
            visible: pbtn.thumbSource !== ""
            anchors.top: parent.top
            anchors.topMargin: 5
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width - 10
            height: pbtn.thumbSource !== "" ? 56 : 0

            Rectangle {
                // helyőrző, amíg a bélyegkép még nem érkezett meg
                anchors.fill: parent
                radius: 2
                color: Theme.chromeBg
                border.width: 1
                border.color: Theme.chromeBorder
                visible: pbtnThumbImg.status !== Image.Ready
            }
            Image {
                id: pbtnThumbImg
                objectName: pbtn.objectName ? pbtn.objectName + "Thumb" : ""
                anchors.fill: parent
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                source: pbtn.thumbSource
                smooth: true
                // amíg nem kész (Loading/Null/Error), nem rajzol semmit —
                // a fenti helyőrző-Rectangle látszik helyette, nem üres folt
                visible: status === Image.Ready
            }
        }
        Text {
            id: pbtnLabel
            // a hívó objectName-jéből képzett saját objectName (pl.
            // "effectGrain2Label") — a tesztek ezen ellenőrzik a
            // tördelést/nem-vágást (#318), a histogramTitle mintája (#235).
            objectName: pbtn.objectName ? pbtn.objectName + "Label" : ""
            // #305/#338 mintája: SOHA ne kössünk anchort feltételesen
            // `undefined`-ra (a QML-figyelmeztetés-őr ezt buktatná) — a
            // pbtnThumbBox magassága 0, ha nincs thumbSource, így ez az
            // egyetlen, mindig érvényes anchor-készlet mindkét esetben jó
            // (sima gombnál csak néhány px-szel tér el a régi centerIn-től,
            // ami a szűk, tömören méretezett gombokon nem látszik).
            anchors.top: pbtnThumbBox.bottom
            anchors.topMargin: pbtn.thumbSource !== "" ? 4 : 3
            anchors.horizontalCenter: parent.horizontalCenter
            text: pbtn.label
            font.pixelSize: Theme.fontSize
            color: pbtn.enabled ? Theme.textDark : Theme.textGray
            // #318: elide helyett tördelés — a panel szélessége nem nőhet,
            // de a szöveg soha nem vágódik "…"-ra; a Qt WordWrap szó-
            // határon tör, hosszú, tördelhetetlen szónál karakterhatáron.
            wrapMode: Text.WordWrap
            width: parent.width - 8
            horizontalAlignment: Text.AlignHCenter
        }
        MouseArea {
            id: pbtnMouse
            anchors.fill: parent
            hoverEnabled: pbtn.tooltip.length > 0
            onClicked: pbtn.buttonClicked()
        }
        ToolTip.text: pbtn.tooltip
        ToolTip.visible: pbtn.tooltip.length > 0 && pbtnMouse.containsMouse
        ToolTip.delay: 400
    }

    // #450: kitöltés/körvonal szín-választó — rögzített, PicasaPy-saját
    // színpaletta (nincs a projektben natív ColorDialog-használat, ld.
    // #450 jelentés), a kijelölt szín kék kerettel jelölt. A `currentColor`
    // a controller mentett/piszkozat értékét tükrözi, `colorPicked` viszi
    // vissza a kattintást a hívóhoz.
    component TextColorSwatches: RowLayout {
        id: swatches
        property string currentColor: "#ffffff"
        signal colorPicked(string hex)
        // #506: a "palette" néven elnevezve elfedte az Item/Control
        // beépített `palette` tulajdonságát (Qt-figyelmeztetés induláskor)
        // — átnevezve `swatchColors`-ra.
        readonly property var swatchColors: [
            "#ffffff", "#000000", "#ff0000", "#ffff00",
            "#00a651", "#0072bc", "#ff7f27", "#a349a4"
        ]
        spacing: 3
        Repeater {
            model: swatches.swatchColors
            delegate: Rectangle {
                required property string modelData
                required property int index
                objectName: swatches.objectName + "Swatch" + index
                width: 16; height: 16; radius: 2
                color: modelData
                border.width: modelData.toLowerCase() === swatches.currentColor.toLowerCase() ? 2 : 1
                border.color: modelData.toLowerCase() === swatches.currentColor.toLowerCase()
                              ? Theme.selectionBlue : Theme.chromeBorder
                MouseArea {
                    anchors.fill: parent
                    onClicked: swatches.colorPicked(modelData)
                }
            }
        }
    }

    // #338: a fülsáv ikonja — Canvas-szal rajzolt egyszerű sziluett (nem
    // rendszer-emoji: a Linux-first célplatformon, ld. CLAUDE.md, nincs
    // garancia színes emoji-betűkészletre — RPi5 minimál-telepítésen a
    // csavarkulcs/nap/ecset glyph simán "tofu"-dobozként jelenhetne meg;
    // a saját rajz mindig ugyanúgy néz ki, és a színe is szabályozható —
    // ez adja a 3 ecset-fül "színben megkülönböztetve" követelményét is,
    // amit egy fix színű emoji-glyph nem tudna).
    component EditTabIcon: Canvas {
        id: icon
        property string kind: "wrench"   // "wrench" | "sun" | "brush"
        property color strokeColor: Theme.iconInk
        // ecset-füleknél a sörte színe (a 3./4./5. fül megkülönböztetése)
        property color accentColor: strokeColor
        // apró minta-pötty a sörtén (zöld/kék fülnél "levél"/"felhő" folt);
        // "transparent" = nincs
        property color fleckColor: "transparent"
        onKindChanged: requestPaint()
        onStrokeColorChanged: requestPaint()
        onAccentColorChanged: requestPaint()
        onFleckColorChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.clearRect(0, 0, width, height)
            ctx.lineCap = "round"
            ctx.lineJoin = "round"
            var w = width, h = height
            if (icon.kind === "wrench") {
                // nyél: bal-alsó → jobb-felső átló
                ctx.strokeStyle = icon.strokeColor
                ctx.lineWidth = Math.max(2, w * 0.14)
                ctx.beginPath()
                ctx.moveTo(w * 0.20, h * 0.85)
                ctx.lineTo(w * 0.58, h * 0.45)
                ctx.stroke()
                // fej: nyitott gyűrű (csavarkulcs-száj) a nyél végén
                ctx.beginPath()
                ctx.arc(w * 0.68, h * 0.32, w * 0.20, Math.PI * 0.15, Math.PI * 1.65)
                ctx.lineWidth = Math.max(2, w * 0.12)
                ctx.stroke()
            } else if (icon.kind === "sun") {
                ctx.fillStyle = icon.strokeColor
                ctx.beginPath()
                ctx.arc(w * 0.5, h * 0.5, w * 0.20, 0, Math.PI * 2)
                ctx.fill()
                ctx.strokeStyle = icon.strokeColor
                ctx.lineWidth = Math.max(1.5, w * 0.08)
                var rays = 8
                for (var i = 0; i < rays; i++) {
                    var a = (Math.PI * 2 * i) / rays
                    var innerR = w * 0.30
                    var outerR = w * 0.46
                    ctx.beginPath()
                    ctx.moveTo(w * 0.5 + Math.cos(a) * innerR, h * 0.5 + Math.sin(a) * innerR)
                    ctx.lineTo(w * 0.5 + Math.cos(a) * outerR, h * 0.5 + Math.sin(a) * outerR)
                    ctx.stroke()
                }
            } else if (icon.kind === "brush") {
                // nyél
                ctx.strokeStyle = icon.strokeColor
                ctx.lineWidth = Math.max(2, w * 0.12)
                ctx.beginPath()
                ctx.moveTo(w * 0.28, h * 0.14)
                ctx.lineTo(w * 0.56, h * 0.48)
                ctx.stroke()
                // sörte (ékalakú folt, a fül szín-tokenjével — plain/zöld/kék)
                ctx.fillStyle = icon.accentColor
                ctx.beginPath()
                ctx.moveTo(w * 0.56, h * 0.50)
                ctx.lineTo(w * 0.82, h * 0.60)
                ctx.lineTo(w * 0.86, h * 0.82)
                ctx.lineTo(w * 0.66, h * 0.90)
                ctx.lineTo(w * 0.50, h * 0.68)
                ctx.closePath()
                ctx.fill()
                if (icon.fleckColor.toString() !== "#00000000"
                        && icon.fleckColor.toString() !== "transparent") {
                    ctx.fillStyle = icon.fleckColor
                    ctx.beginPath()
                    ctx.arc(w * 0.70, h * 0.74, w * 0.06, 0, Math.PI * 2)
                    ctx.fill()
                }
            }
        }
    }

    // egy fülgomb (Gyakori javítások / Finomhangolás / Effektek / 4. / 5.
    // effekt-fül, #20, #328, #338): kattintásra panel.activeTab vált, az
    // aktív fül vastagabb kerettel/eltérő háttérrel emelkedik ki.
    //
    // #338: a szöveges fülcímkék a szűk (230px-es) panelen összeszorultak
    // ("Gyakori javítások" két sorba tört, "Finomhangol…" levágódott) — az
    // eredeti Picasa is 5 IKONOS fület használ (csavarkulcs / nap / 3×
    // ecset, ld. docs/specs/ui-audit-editor.md 1. szak.). A jelentést a
    // fenti EditTabIcon adja (saját Canvas-rajz, nem rendszer-glyph); a
    // teljes nevet a ToolTip mutatja hoverre. A `tbtnLabel` Text a
    // korábbi #318-as tördelés-teszt (test_editor_tabs.py) és a
    // hozzáférhetőség kedvéért MEGMARAD, de rejtve (`visible: false`) —
    // a bélyegkép-gomb (PanelButton) is hasonlóan viselkedik a felirata
    // alatt, csak ott a felirat látszik is, itt a hely a szűk fülsávon
    // nem engedi meg mindkettőt.
    component EditTabButton: Rectangle {
        id: tbtn
        required property int tabIndex
        required property string label
        // "wrench" | "sun" | "brush" — melyik ikont rajzolja az EditTabIcon
        required property string iconKind
        property color iconAccent: Theme.iconInk
        property color iconFleck: "transparent"
        Layout.fillWidth: true
        Layout.preferredHeight: 38
        color: panel.activeTab === tabIndex ? Theme.contentPanel : Theme.panelHeaderBg
        border.width: 1
        border.color: panel.activeTab === tabIndex ? Theme.selectionBlue : Theme.chromeBorder

        EditTabIcon {
            objectName: tbtn.objectName ? tbtn.objectName + "Icon" : ""
            anchors.centerIn: parent
            width: 22; height: 22
            kind: tbtn.iconKind
            strokeColor: Theme.iconInk
            accentColor: tbtn.iconAccent
            fleckColor: tbtn.iconFleck
        }
        // #318 kompatibilitás: rejtett, de a régi tördelés-logikával
        // számolt felirat-Text — a `truncated` így sosem igaz, mert a
        // szélessége nem szorítja a fülgomb keskeny sávjához.
        Text {
            id: tbtnLabel
            objectName: tbtn.objectName ? tbtn.objectName + "Label" : ""
            visible: false
            text: tbtn.label
            font.pixelSize: Theme.fontSize - 3
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            width: Math.max(120, implicitWidth)
        }
        MouseArea {
            id: tabMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: panel.activeTab = tbtn.tabIndex
        }
        ToolTip.text: tbtn.label
        ToolTip.visible: tabMouse.containsMouse
        ToolTip.delay: 400
    }

    // ---------------- fülsáv: Gyakori javítások / Finomhangolás / Effektek /
    // 4. effekt-fül / 5. effekt-fül (#20, #328) — csak "tools" módban,
    // vágásnál (cropColumn) nincs értelme. Öt egyenlő szélességű fül fér el
    // a panel szélességében (Layout.fillWidth mindegyiken, ld. #328 4. pont).
    RowLayout {
        id: tabBar
        objectName: "editTabBar"
        visible: !panel.modeToolActive
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 0

        // #338: csavarkulcs — az eredeti Picasa 1. füle
        EditTabButton {
            objectName: "editTabFixes"
            tabIndex: 0
            label: qsTr("Common Fixes")
            iconKind: "wrench"
        }
        // #338: nap — az eredeti Picasa 2. füle
        EditTabButton {
            objectName: "editTabFinetune"
            tabIndex: 1
            label: qsTr("Fine Tuning")
            iconKind: "sun"
        }
        // #338: sima ecset — a törzs-effektek (3. fül, nincs szín-minta)
        EditTabButton {
            objectName: "editTabEffects"
            tabIndex: 2
            label: qsTr("Effects")
            iconKind: "brush"
            iconAccent: Theme.iconInk
        }
        // #328/#338: 4. fül — ZÖLD ecset ("kreatív effektek"), a docs/specs/
        // ui-audit-editor.md leírása szerint zöld táj-mintával megkülönböztetve.
        EditTabButton {
            objectName: "editTabEffects2"
            tabIndex: 3
            label: qsTr("Creative")
            iconKind: "brush"
            iconAccent: Theme.picasaGreen
            iconFleck: Qt.darker(Theme.picasaGreen, 1.4)
        }
        // #328/#338: 5. fül — KÉK ecset ("művészi effektek"), kék ég-mintával.
        EditTabButton {
            objectName: "editTabEffects3"
            tabIndex: 4
            label: qsTr("Artistic")
            iconKind: "brush"
            iconAccent: Theme.brandBlue
            iconFleck: Qt.lighter(Theme.brandBlue, 1.6)
        }
    }

    // ---------------- "tools" mód: ikonrács ----------------
    ColumnLayout {
        objectName: "toolsColumn"
        visible: !panel.modeToolActive && panel.activeTab === 0
        // tiltott panel (videó a nézőben, #103): az egész oszlop halvány
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        // #405: a szöveges "Common Fixes"/"Gyakori javítások" fejléc TÖRÖLVE
        // — az eredeti Picasán a fül alatt NINCS ilyen felirat, a csempék
        // rögtön a fülsáv alatt kezdődnek (ld. #405 issue 4. pontja).

        // #464: a gombkészlet és a sorrend a jegy szövegéből (a tulajdonos
        // eredeti Picasa 3.9-en olvasta le): Kivágás -> Vörösszem -> Jó
        // napom van -> Kreatív Kit -> Automatikus szín -> Automatikus
        // kontraszt -> [Derítőfény-csúszka] -> Kiegyenesítés -> Szöveg ->
        // Retusálás. A Derítőfény a gombok KÖZÖTT ül (nem külön fülön),
        // ezért a rács két részre bomlik, a csúszka sora közéjük ékelve.
        GridLayout {
            columns: 3
            columnSpacing: 4
            rowSpacing: 10
            Layout.fillWidth: true

            ToolTile {
                objectName: "editToolCrop"
                toolName: "crop"; label: qsTr("Crop"); iconFile: "vagas"
                active: panel.cropActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolRedeye"
                toolName: "redeye"; label: qsTr("Redeye"); iconFile: "vorosszem"
                active: panel.redeyeActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            // egygombos javítások (#116): nincs "benyomva" állapot — a gomb
            // tiltott, amíg ugyanez a szűrő a lánc utolsó eleme
            ToolTile {
                objectName: "editToolEnhance"
                toolName: "enhance"; label: qsTr("I'm Feeling Lucky")
                iconFile: "jo-napom-van"
                tileEnabled: panel.enhanceEnabled
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            // #464: „Kreatív Kit" — a Picasa a Picnik külső szerkesztőt
            // első osztályú polgárként kezelte, negyedik helyen. A
            // projektnek nincs külső-szerkesztő integrációja (nincs
            // háttere), ezért a gomb egyelőre HELYŐRZŐ: a helye megvan,
            // letiltva jelenik meg (a PicasaMenuItem-placeholder mintát
            // követve, ToolTile-lel — nincs saját "placeholder" property).
            ToolTile {
                objectName: "editToolCreativeKit"
                toolName: "creativekit"; label: qsTr("Creative Kit")
                iconFile: "kreativ-kit"
                tileEnabled: false
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolAutocolor"
                toolName: "autocolor"; label: qsTr("Auto Color")
                iconFile: "auto-szin"
                tileEnabled: panel.autocolorEnabled
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolAutolight"
                toolName: "autolight"; label: qsTr("Auto Contrast")
                iconFile: "auto-kontraszt"
                tileEnabled: panel.autolightEnabled
                onActivated: (tool) => panel.handleToolClick(tool)
            }
        }

        // #337/#405/#411: Kitöltő fény — az eredeti Picasa Alapvető
        // javítások fülén az ikonrács alatt EZ AZ EGYETLEN csúszka, és a
        // napi használat egyik legfontosabb eszköze. Ugyanaz a beállítás,
        // mint a Finomhangolás fülén: a két csúszka egymást követi
        // (fillLightMoved). A címke a csúszka FÖLÖTT, kompakt (#405 6.
        // pont), a saját ikonnal kiegészítve (#411 9. ikonja: deritofeny).
        // #411 (felhasználói visszajelzés): az eredetiben az ikon és a
        // csúszka EGY EGYSÉG — a képecske közvetlenül a csúszka mellett,
        // azonos sorban ül, a felirat a csúszka fölött. Korábban nálunk a
        // 16x16-os ikon a felirat mellé volt tűzve, a csúszka pedig külön
        // sorban futott — az összetartozás nem látszott.
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Image {
                objectName: "fixesFillLightIcon"
                source: "icons/deritofeny.svg"
                fillMode: Image.PreserveAspectFit
                sourceSize: Qt.size(108, 72)
                Layout.preferredWidth: 54
                Layout.preferredHeight: 36
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: qsTr("Fill Light")
                    font.pixelSize: Theme.fontSize - 1
                    color: Theme.textGray
                }
                PicasaSlider {
                    id: fixesFillSlider
                    objectName: "fixesFillSlider"
                    Layout.fillWidth: true
                    from: 0; to: 1; value: 0
                    onValueChanged: panel.fillLightMoved(value)
                    onPressedChanged: if (!pressed) panel.fillLightCommitted()
                }
            }
        }

        // #464: a sorrend maradék három gombja a Derítőfény-csúszka UTÁN —
        // Kiegyenesítés -> Szöveg -> Retusálás.
        GridLayout {
            columns: 3
            columnSpacing: 4
            rowSpacing: 10
            Layout.fillWidth: true

            ToolTile {
                objectName: "editToolTilt"
                toolName: "tilt"; label: qsTr("Straighten"); iconFile: "kiegyenesites"
                active: panel.tiltActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolText"
                toolName: "text"; label: qsTr("Text"); iconFile: "szoveg"
                active: panel.textActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolRetouch"
                toolName: "retouch"; label: qsTr("Retouch"); iconFile: "retusalas"
                active: panel.retouchActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "editUndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "editRedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                // #405: a Visszavonás/Újra az eredetiben egyenlő szélességű
                // pár a panel alján (nem egy keskeny + egy kitöltő) — mindkét
                // gomb fillWidth-del osztozik a helyen.
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- "finetune" mód: Finomhangolás (#20) ----------------
    ColumnLayout {
        objectName: "finetuneColumn"
        visible: !panel.modeToolActive && panel.activeTab === 1
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Fine Tuning")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        Label {
            text: qsTr("Fill Light")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: finetuneFillSlider
            objectName: "finetuneFillSlider"
            Layout.fillWidth: true
            from: 0; to: 1; value: 0
            // #337: a Gyakori javítások fülön lévő párjával közös állapot
            onValueChanged: panel.fillLightMoved(value)
            onPressedChanged: if (!pressed) panel.fillLightCommitted()
        }

        Label {
            text: qsTr("Highlights")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: finetuneHighlightsSlider
            objectName: "finetuneHighlightsSlider"
            Layout.fillWidth: true
            from: 0; to: 1; value: 0
            onValueChanged: if (!panel.suppressFinetune) panel.emitFinetunePreview()
            onPressedChanged: if (!pressed)
                panel.finetuneCommit(finetuneFillSlider.value,
                                      finetuneHighlightsSlider.value,
                                      finetuneShadowsSlider.value,
                                      finetuneTempSlider.value)
        }

        Label {
            text: qsTr("Shadows")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: finetuneShadowsSlider
            objectName: "finetuneShadowsSlider"
            Layout.fillWidth: true
            from: 0; to: 1; value: 0
            onValueChanged: if (!panel.suppressFinetune) panel.emitFinetunePreview()
            onPressedChanged: if (!pressed)
                panel.finetuneCommit(finetuneFillSlider.value,
                                      finetuneHighlightsSlider.value,
                                      finetuneShadowsSlider.value,
                                      finetuneTempSlider.value)
        }

        Label {
            text: qsTr("Color Temperature")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: finetuneTempSlider
            objectName: "finetuneTempSlider"
            Layout.fillWidth: true
            from: -1; to: 1; value: 0
            onValueChanged: if (!panel.suppressFinetune) panel.emitFinetunePreview()
            onPressedChanged: if (!pressed)
                panel.finetuneCommit(finetuneFillSlider.value,
                                      finetuneHighlightsSlider.value,
                                      finetuneShadowsSlider.value,
                                      finetuneTempSlider.value)
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "finetuneUndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "finetuneRedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                // #405: a Visszavonás/Újra az eredetiben egyenlő szélességű
                // pár a panel alján (nem egy keskeny + egy kitöltő) — mindkét
                // gomb fillWidth-del osztozik a helyen.
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- "effects" mód: Effektek (#20) ----------------
    ColumnLayout {
        objectName: "effectsColumn"
        visible: !panel.modeToolActive && panel.activeTab === 2 && !panel.paramPanelActive
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Effects")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        GridLayout {
            objectName: "effectsGrid"
            columns: 2
            columnSpacing: 6
            rowSpacing: 6
            Layout.fillWidth: true

            // #315: az eredeti Picasa Effektek fülén az Élesítés az ELSŐ
            // gomb — a render/chain.py "unsharp" handlere ismeri, csak a
            // gombja hiányzott.
            PanelButton {
                objectName: "effectUnsharp"
                label: qsTr("Sharpen")
                onButtonClicked: if (!panel.tryOpenParamPanel("unsharp")) panel.effectRequested("unsharp")
                thumbSource: panel.effectThumbSource("unsharp")
            }
            PanelButton {
                objectName: "effectSepia"
                label: qsTr("Sepia")
                onButtonClicked: if (!panel.tryOpenParamPanel("sepia")) panel.effectRequested("sepia")
                thumbSource: panel.effectThumbSource("sepia")
            }
            PanelButton {
                objectName: "effectBw"
                label: qsTr("B&W")
                onButtonClicked: if (!panel.tryOpenParamPanel("bw")) panel.effectRequested("bw")
                thumbSource: panel.effectThumbSource("bw")
            }
            PanelButton {
                objectName: "effectWarm"
                label: qsTr("Warmify")
                onButtonClicked: if (!panel.tryOpenParamPanel("warm")) panel.effectRequested("warm")
                thumbSource: panel.effectThumbSource("warm")
            }
            PanelButton {
                objectName: "effectGrain2"
                label: qsTr("Film Grain")
                onButtonClicked: if (!panel.tryOpenParamPanel("grain2")) panel.effectRequested("grain2")
                thumbSource: panel.effectThumbSource("grain2")
            }
            PanelButton {
                objectName: "effectTint"
                label: qsTr("Tint")
                onButtonClicked: if (!panel.tryOpenParamPanel("tint")) panel.effectRequested("tint")
                thumbSource: panel.effectThumbSource("tint")
            }
            PanelButton {
                objectName: "effectSat"
                label: qsTr("Saturation")
                onButtonClicked: if (!panel.tryOpenParamPanel("sat")) panel.effectRequested("sat")
                thumbSource: panel.effectThumbSource("sat")
            }
            PanelButton {
                objectName: "effectRadblur"
                label: qsTr("Soft Focus")
                onButtonClicked: if (!panel.tryOpenParamPanel("radblur")) panel.effectRequested("radblur")
                thumbSource: panel.effectThumbSource("radblur")
            }
            PanelButton {
                objectName: "effectGlow2"
                label: qsTr("Glow")
                onButtonClicked: if (!panel.tryOpenParamPanel("glow2")) panel.effectRequested("glow2")
                thumbSource: panel.effectThumbSource("glow2")
            }
            PanelButton {
                objectName: "effectAnsel"
                label: qsTr("Filtered B&W")
                onButtonClicked: if (!panel.tryOpenParamPanel("ansel")) panel.effectRequested("ansel")
                thumbSource: panel.effectThumbSource("ansel")
            }
            PanelButton {
                objectName: "effectRadsat"
                label: qsTr("Focal Saturation")
                onButtonClicked: if (!panel.tryOpenParamPanel("radsat")) panel.effectRequested("radsat")
                thumbSource: panel.effectThumbSource("radsat")
            }
            PanelButton {
                objectName: "effectDirTint"
                label: qsTr("Graduated Tint")
                onButtonClicked: if (!panel.tryOpenParamPanel("dir_tint")) panel.effectRequested("dir_tint")
                thumbSource: panel.effectThumbSource("dir_tint")
            }
            // #315: a render/chain.py "vignette" kulcsot vár (kisbetűs,
            // casefold), noha az ini-ben a szűrő neve nagybetűs "Vignette"
            // — az EditController.applyEffect is casefold-ol, ezért itt is
            // kisbetűvel küldjük az effectRequested jelet.
            PanelButton {
                objectName: "effectVignette"
                label: qsTr("Vignette")
                onButtonClicked: if (!panel.tryOpenParamPanel("vignette")) panel.effectRequested("vignette")
                thumbSource: panel.effectThumbSource("vignette")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "effectsUndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "effectsRedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                // #405: a Visszavonás/Újra az eredetiben egyenlő szélességű
                // pár a panel alján (nem egy keskeny + egy kitöltő) — mindkét
                // gomb fillWidth-del osztozik a helyen.
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- "effects2" mód: 4. effekt-fül — zöld ecset,
    // "kreatív effektek" (#328, docs/specs/ui-audit-editor.md 4. fül) ------
    ColumnLayout {
        objectName: "effectsColumn2"
        visible: !panel.modeToolActive && panel.activeTab === 3 && !panel.paramPanelActive
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Creative")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        GridLayout {
            objectName: "effectsGrid2"
            columns: 2
            columnSpacing: 6
            rowSpacing: 6
            Layout.fillWidth: true

            PanelButton {
                objectName: "effectIr"
                label: qsTr("Infrared Film")
                onButtonClicked: if (!panel.tryOpenParamPanel("ir")) panel.effectRequested("ir")
                thumbSource: panel.effectThumbSource("ir")
            }
            PanelButton {
                objectName: "effectLomo"
                label: qsTr("Lomo-ish")
                onButtonClicked: if (!panel.tryOpenParamPanel("lomo")) panel.effectRequested("lomo")
                thumbSource: panel.effectThumbSource("lomo")
            }
            PanelButton {
                objectName: "effectHolga"
                label: qsTr("Holga-ish")
                onButtonClicked: if (!panel.tryOpenParamPanel("holga")) panel.effectRequested("holga")
                thumbSource: panel.effectThumbSource("holga")
            }
            PanelButton {
                objectName: "effectHdr"
                label: qsTr("HDR-ish")
                onButtonClicked: if (!panel.tryOpenParamPanel("hdr")) panel.effectRequested("hdr")
                thumbSource: panel.effectThumbSource("hdr")
            }
            PanelButton {
                objectName: "effectCinemascope"
                label: qsTr("Cinemascope")
                onButtonClicked: if (!panel.tryOpenParamPanel("cinemascope")) panel.effectRequested("cinemascope")
                thumbSource: panel.effectThumbSource("cinemascope")
            }
            PanelButton {
                objectName: "effectOrton"
                label: qsTr("Orton-ish")
                onButtonClicked: if (!panel.tryOpenParamPanel("orton")) panel.effectRequested("orton")
                thumbSource: panel.effectThumbSource("orton")
            }
            PanelButton {
                objectName: "effectSixties"
                label: qsTr("1960s")
                onButtonClicked: if (!panel.tryOpenParamPanel("sixties")) panel.effectRequested("sixties")
                thumbSource: panel.effectThumbSource("sixties")
            }
            PanelButton {
                objectName: "effectInvert"
                label: qsTr("Invert Colors")
                onButtonClicked: if (!panel.tryOpenParamPanel("invert")) panel.effectRequested("invert")
                thumbSource: panel.effectThumbSource("invert")
            }
            PanelButton {
                objectName: "effectHeatMap"
                label: qsTr("Heat Map")
                onButtonClicked: if (!panel.tryOpenParamPanel("heatmap")) panel.effectRequested("heatmap")
                thumbSource: panel.effectThumbSource("heatmap")
            }
            PanelButton {
                objectName: "effectCrossProcess"
                label: qsTr("Cross Process")
                onButtonClicked: if (!panel.tryOpenParamPanel("crossprocess")) panel.effectRequested("crossprocess")
                thumbSource: panel.effectThumbSource("crossprocess")
            }
            PanelButton {
                objectName: "effectQuantizePalette"
                label: qsTr("Posterize")
                onButtonClicked: if (!panel.tryOpenParamPanel("quantizepalette")) panel.effectRequested("quantizepalette")
                thumbSource: panel.effectThumbSource("quantizepalette")
            }
            PanelButton {
                objectName: "effectTwoTone"
                label: qsTr("Duo-Tone")
                onButtonClicked: if (!panel.tryOpenParamPanel("twotone")) panel.effectRequested("twotone")
                thumbSource: panel.effectThumbSource("twotone")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "effects2UndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "effects2RedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                // #405: a Visszavonás/Újra az eredetiben egyenlő szélességű
                // pár a panel alján (nem egy keskeny + egy kitöltő) — mindkét
                // gomb fillWidth-del osztozik a helyen.
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- "effects3" mód: 5. effekt-fül — kék ecset,
    // "művészi effektek" (#328, docs/specs/ui-audit-editor.md 5. fül) ------
    ColumnLayout {
        objectName: "effectsColumn3"
        visible: !panel.modeToolActive && panel.activeTab === 4 && !panel.paramPanelActive
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Artistic")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        GridLayout {
            objectName: "effectsGrid3"
            columns: 2
            columnSpacing: 6
            rowSpacing: 6
            Layout.fillWidth: true

            PanelButton {
                objectName: "effectBoost"
                label: qsTr("Boost")
                onButtonClicked: if (!panel.tryOpenParamPanel("boost")) panel.effectRequested("boost")
                thumbSource: panel.effectThumbSource("boost")
            }
            PanelButton {
                objectName: "effectSoften"
                label: qsTr("Soft Focus")
                onButtonClicked: if (!panel.tryOpenParamPanel("soften")) panel.effectRequested("soften")
                thumbSource: panel.effectThumbSource("soften")
            }
            PanelButton {
                objectName: "effectPixelate"
                label: qsTr("Pixelate")
                onButtonClicked: if (!panel.tryOpenParamPanel("pixelate")) panel.effectRequested("pixelate")
                thumbSource: panel.effectThumbSource("pixelate")
            }
            PanelButton {
                objectName: "effectFocalZoom"
                label: qsTr("Focal Zoom")
                onButtonClicked: if (!panel.tryOpenParamPanel("focalzoom")) panel.effectRequested("focalzoom")
                thumbSource: panel.effectThumbSource("focalzoom")
            }
            PanelButton {
                objectName: "effectPencilSketch"
                label: qsTr("Pencil Sketch")
                onButtonClicked: if (!panel.tryOpenParamPanel("pencilsketch")) panel.effectRequested("pencilsketch")
                thumbSource: panel.effectThumbSource("pencilsketch")
            }
            PanelButton {
                objectName: "effectNeon"
                label: qsTr("Neon")
                onButtonClicked: if (!panel.tryOpenParamPanel("neon")) panel.effectRequested("neon")
                thumbSource: panel.effectThumbSource("neon")
            }
            PanelButton {
                objectName: "effectComicize"
                label: qsTr("Comicize")
                onButtonClicked: if (!panel.tryOpenParamPanel("comicize")) panel.effectRequested("comicize")
                thumbSource: panel.effectThumbSource("comicize")
            }
            PanelButton {
                objectName: "effectBorder"
                label: qsTr("Border")
                onButtonClicked: if (!panel.tryOpenParamPanel("border")) panel.effectRequested("border")
                thumbSource: panel.effectThumbSource("border")
            }
            PanelButton {
                objectName: "effectDropShadow"
                label: qsTr("Drop Shadow")
                onButtonClicked: if (!panel.tryOpenParamPanel("dropshadow")) panel.effectRequested("dropshadow")
                thumbSource: panel.effectThumbSource("dropshadow")
            }
            PanelButton {
                objectName: "effectMuseumMatte"
                label: qsTr("Museum Matte")
                onButtonClicked: if (!panel.tryOpenParamPanel("museummatte")) panel.effectRequested("museummatte")
                thumbSource: panel.effectThumbSource("museummatte")
            }
            PanelButton {
                objectName: "effectPolaroid"
                label: qsTr("Polaroid")
                onButtonClicked: if (!panel.tryOpenParamPanel("polaroid")) panel.effectRequested("polaroid")
                thumbSource: panel.effectThumbSource("polaroid")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "effects3UndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "effects3RedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                // #405: a Visszavonás/Újra az eredetiben egyenlő szélességű
                // pár a panel alján (nem egy keskeny + egy kitöltő) — mindkét
                // gomb fillWidth-del osztozik a helyen.
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- effekt-paraméter alpanel (#316) ----------------
    // Bármelyik effekt-fülön (2./3./4.) megnyílhat — az adott fül rácsát
    // fedi el ugyanazon a helyen (tabBar.bottom-tól), a visszatérés
    // ugyanarra a fülre történik, mert az activeTab változatlan marad.
    ColumnLayout {
        objectName: "effectParamColumn"
        visible: !panel.modeToolActive && panel.paramPanelActive
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                objectName: "effectParamTitle"
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: panel.paramEffectName
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        Repeater {
            objectName: "effectParamRepeater"
            model: panel.paramEffectParams

            delegate: ColumnLayout {
                id: paramRow
                required property var modelData
                required property int index
                Layout.fillWidth: true
                spacing: 2

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        objectName: "effectParamLabel" + paramRow.index
                        Layout.fillWidth: true
                        text: panel.paramLabel(paramRow.modelData.label)
                        font.pixelSize: Theme.fontSize - 1
                        color: Theme.textGray
                    }
                    Label {
                        objectName: "effectParamValue" + paramRow.index
                        text: paramSlider.value.toFixed(2)
                        font.pixelSize: Theme.fontSize - 1
                        color: Theme.textGray
                    }
                }
                PicasaSlider {
                    id: paramSlider
                    objectName: "effectParamSlider" + paramRow.index
                    Layout.fillWidth: true
                    from: paramRow.modelData.minimum
                    to: paramRow.modelData.maximum
                    stepSize: paramRow.modelData.step
                    value: paramRow.modelData.default
                    // húzás/kattintás közben élő előnézet (#316) — a
                    // programozott kezdőérték-beállítás NEM vált ki `moved`
                    // jelet, csak a valódi felhasználói interakció
                    onMoved: panel.updateParamValue(paramRow.index, paramSlider.value)
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "effectParamApplyButton"
                label: qsTr("Apply")
                onButtonClicked: panel.applyParamPanel()
            }
            PanelButton {
                objectName: "effectParamCancelButton"
                label: qsTr("Cancel")
                onButtonClicked: panel.cancelParamPanel()
            }
        }
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

    // ---------------- "crop" mód: Fotó vágása ----------------
    ColumnLayout {
        objectName: "cropColumn"
        visible: panel.cropActive
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Image {
                Layout.preferredWidth: 40
                Layout.preferredHeight: 30
                source: "../../assets/tools/crop.png"
            }
            Text {
                Layout.fillWidth: true
                text: qsTr("Crop Photo")
                font.pixelSize: Theme.fontSize + 3
                color: Theme.ink
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Choose a size below, then drag on the picture to "
                       + "select the area you want to keep.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        // #448: a Kiegyenesítés-figyelmeztetés — az eredeti Picasa szó
        // szerinti szövege (a jegy idézi), csak akkor jelenik meg, ha a
        // képen MÁR van aktív kiegyenesítés (`straightenActive`, a hívó
        // tölti az editController.tiltParam-ből).
        Text {
            objectName: "cropStraightenWarning"
            visible: panel.straightenActive
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("This image's orientation has been modified by the "
                       + "Straighten tool and might not crop accurately… "
                       + "try undoing the Straighten fix, then recrop, and "
                       + "Straighten again if necessary.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        // arány-választó legördülő (Picasa-lista)
        Rectangle {
            objectName: "cropAspectCombo"
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            radius: 2
            color: Theme.contentPanel
            border.color: Theme.chromeBorder
            Text {
                anchors.left: parent.left; anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width - 28
                elide: Text.ElideRight
                text: panel.selectedPreset.label
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                anchors.right: parent.right; anchors.rightMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: "▼"; font.pixelSize: 8; color: Theme.textDark
            }
            MouseArea {
                anchors.fill: parent
                onClicked: aspectList.visible = !aspectList.visible
            }
        }
        Rectangle {
            id: aspectList
            objectName: "cropAspectList"
            visible: false
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? aspectColumn.height + 2 : 0
            color: Theme.contentPanel
            border.color: Theme.chromeBorder
            Column {
                id: aspectColumn
                x: 1; y: 1
                width: parent.width - 2
                Repeater {
                    model: panel.aspectFullList
                    Rectangle {
                        id: aspectRow
                        required property var modelData
                        required property int index
                        width: aspectColumn.width; height: 20
                        color: aspectRowHover.hovered ? Theme.panelSelection
                               : "transparent"
                        Text {
                            anchors.left: parent.left; anchors.leftMargin: 6
                            anchors.right: aspectDeleteBtn.visible
                                ? aspectDeleteBtn.left : parent.right
                            anchors.rightMargin: 4
                            anchors.verticalCenter: parent.verticalCenter
                            elide: Text.ElideRight
                            text: aspectRow.modelData.label
                            font.pixelSize: Theme.fontSize
                            // a kijelölő-kék (Theme.panelSelection) hátteren
                            // szándékosan téma-független fehér a token
                            // (Theme.panelSelectionText) — nem új hardkód
                            color: aspectRowHover.hovered ? Theme.panelSelectionText : Theme.ink
                        }
                        // #448: az EGYÉNI (felhasználó felvette) arányok
                        // törölhetők — a beépített preset-eknek nincs "×".
                        Text {
                            id: aspectDeleteBtn
                            objectName: "cropAspectDelete" + aspectRow.index
                            visible: aspectRow.modelData.isCustom === true
                            anchors.right: parent.right; anchors.rightMargin: 6
                            anchors.verticalCenter: parent.verticalCenter
                            text: "✕"
                            font.pixelSize: Theme.fontSize - 1
                            color: aspectDeleteMouse.containsMouse
                                   ? Theme.selectionBlue : Theme.textGray
                            MouseArea {
                                id: aspectDeleteMouse
                                anchors.fill: parent
                                anchors.margins: -4
                                hoverEnabled: true
                                onClicked: {
                                    deleteCustomAspectConfirm.pendingName =
                                        aspectRow.modelData.customName
                                    deleteCustomAspectConfirm.pendingWidth =
                                        aspectRow.modelData.customWidth
                                    deleteCustomAspectConfirm.pendingHeight =
                                        aspectRow.modelData.customHeight
                                    deleteCustomAspectConfirm.ask(
                                        "deleteCustomAspectRatio",
                                        qsTr("Delete this custom aspect ratio?"))
                                }
                            }
                        }
                        HoverHandler { id: aspectRowHover }
                        TapHandler {
                            onTapped: {
                                panel.selectAspect(aspectRow.index)
                                aspectList.visible = false
                            }
                        }
                    }
                }
                // #448: "AddCustomAspectRatio" — a beépítettek alatt, saját
                // sorban (a jegy szerint a dialógus szélesség × magasság +
                // nevet kér, a lista "<szél> x <mag>   <név>" alakban mutatja).
                Rectangle {
                    objectName: "cropAspectAddRow"
                    width: aspectColumn.width; height: 20
                    color: addAspectRowHover.hovered ? Theme.panelSelection
                           : "transparent"
                    Text {
                        anchors.left: parent.left; anchors.leftMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                        text: qsTr("Add Custom Aspect Ratio…")
                        font.pixelSize: Theme.fontSize
                        color: addAspectRowHover.hovered
                               ? Theme.panelSelectionText : Theme.ink
                    }
                    HoverHandler { id: addAspectRowHover }
                    TapHandler {
                        onTapped: {
                            aspectList.visible = false
                            addCustomAspectRatioDialog.open()
                        }
                    }
                }
            }
        }

        // gyorsvágások: bal-felső / fekvő / álló (Picasa három bélyegképe)
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "quickCropTopleft"
                label: qsTr("Top left")
                onButtonClicked: panel.quickCropRequested("topleft")
            }
            PanelButton {
                objectName: "quickCropLandscape"
                label: qsTr("Landscape")
                onButtonClicked: panel.quickCropRequested("landscape")
            }
            PanelButton {
                objectName: "quickCropPortrait"
                label: qsTr("Portrait")
                onButtonClicked: panel.quickCropRequested("portrait")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "cropRotateButton"
                label: qsTr("Rotate")
                onButtonClicked: panel.cropRotateRequested()
            }
            PanelButton {
                objectName: "cropPreviewButton"
                label: qsTr("Preview")
                // amíg nyomva tartják, a hívó a vágott képet mutatja
                MouseArea {
                    anchors.fill: parent
                    onPressed: panel.cropPreviewHold(true)
                    onReleased: panel.cropPreviewHold(false)
                    onCanceled: panel.cropPreviewHold(false)
                }
            }
        }

        PanelButton {
            objectName: "cropResetButton"
            label: qsTr("Reset")
            Layout.fillWidth: false
            Layout.preferredWidth: 120
            Layout.alignment: Qt.AlignHCenter
            onButtonClicked: panel.cropResetRequested()
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "cropApplyButton"
                label: qsTr("Apply") + " ✔"
                onButtonClicked: panel.cropApplyRequested()
            }
            PanelButton {
                objectName: "cropCancelButton"
                label: qsTr("Cancel") + " ✘"
                onButtonClicked: panel.cropCancelRequested()
            }
        }
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

    // #448: az egyéni arány törlésének megerősítése (a jegy szerint az
    // egyéni tételek törölhetők) — #422 mintája szerint EGYEDI namePrefix.
    ConfirmDialog {
        id: deleteCustomAspectConfirm
        namePrefix: "deleteCustomAspectConfirm"
        property string pendingName: ""
        property real pendingWidth: 0
        property real pendingHeight: 0
        onConfirmed: {
            if (typeof controller !== "undefined" && controller
                    && deleteCustomAspectConfirm.pendingName !== "") {
                controller.deleteCustomAspectRatio(
                    deleteCustomAspectConfirm.pendingName,
                    deleteCustomAspectConfirm.pendingWidth,
                    deleteCustomAspectConfirm.pendingHeight)
                // törlés után a kiválasztás védetten (selectedPreset)
                // tartományon belülre esik — nincs teendő itt
            }
        }
    }

    // ---------------- "retouch" mód: Retusálás (#148) ----------------
    // A Vágás mintáját követi: a kép TELJES panel-területét foglalja el a
    // fülsáv/rács helyett; a kattintások kezelését a hívó (PhotoViewer)
    // végzi a képen (ez a fájl nem ismeri a kép geometriáját), a puffer
    // méretét (retouchRegionCount) és az Alkalmaz/Mégse gombokat mutatja.
    ColumnLayout {
        objectName: "retouchColumn"
        visible: panel.retouchActive
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Image {
                Layout.preferredWidth: 40
                Layout.preferredHeight: 30
                source: "../../assets/tools/retouch.png"
            }
            Text {
                Layout.fillWidth: true
                text: qsTr("Retouch")
                font.pixelSize: Theme.fontSize + 3
                color: Theme.ink
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Click to select the area to fix. Then, move the"
                       + " mouse to see a preview of the replacement area."
                       + " Click on the image again to finalize. Lather,"
                       + " rinse, repeat.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        Label {
            text: qsTr("Brush Size")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: retouchBrushSizeSlider
            objectName: "retouchBrushSizeSlider"
            Layout.fillWidth: true
            from: 1; to: 100
            stepSize: 1
            value: panel.brushSize
            onMoved: panel.brushSizeEdited(Math.round(value))
        }

        Text {
            objectName: "retouchRegionCountLabel"
            Layout.fillWidth: true
            text: qsTr("Regions selected: %1").arg(panel.retouchRegionCount)
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        // #445: a Picasa súgószövege szerinti, számítás-alatti előnézetet
        // jelző felirat — a folt véglegesítéséig (cél kijelölve, forrás
        // mozgatás alatt) látszik az előnézet fölött.
        Text {
            objectName: "retouchRefiningLabel"
            Layout.fillWidth: true
            visible: panel.retouchPatchPending
            text: qsTr("Refining…")
            font.pixelSize: Theme.fontSize - 1
            font.italic: true
            color: Theme.textGray
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "retouchUndoPatchButton"
                label: qsTr("Undo Patch")
                buttonEnabled: panel.canUndoPatch
                onButtonClicked: panel.retouchUndoPatchRequested()
            }
            PanelButton {
                objectName: "retouchRedoPatchButton"
                label: qsTr("Redo Patch")
                buttonEnabled: panel.canRedoPatch
                onButtonClicked: panel.retouchRedoPatchRequested()
            }
            PanelButton {
                objectName: "retouchResetButton"
                label: qsTr("Reset")
                buttonEnabled: panel.retouchRegionCount > 0 || panel.retouchPatchPending
                onButtonClicked: panel.retouchResetRequested()
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "retouchApplyButton"
                label: qsTr("Apply") + " ✔"
                buttonEnabled: panel.retouchRegionCount > 0
                onButtonClicked: panel.retouchApplyRequested()
            }
            PanelButton {
                objectName: "retouchCancelButton"
                label: qsTr("Cancel") + " ✘"
                onButtonClicked: panel.retouchCancelRequested()
            }
        }
    }

    // ---------------- "text" mód: Szöveg-overlay (#148) ----------------
    // A pozicionálás is kattintással történik a képen (a hívó feladata,
    // ld. retouchColumn megjegyzése) — a szövegmező itt él, a tartalom
    // gépelését a textDraftEdited jel viszi a controllerhez.
    ColumnLayout {
        objectName: "textColumn"
        visible: panel.textActive
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Image {
                Layout.preferredWidth: 40
                Layout.preferredHeight: 30
                source: "../../assets/tools/text.png"
            }
            Text {
                Layout.fillWidth: true
                text: qsTr("Text")
                font.pixelSize: Theme.fontSize + 3
                color: Theme.ink
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Type your text, then click on the photo to place it.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        TextField {
            id: textContentField
            objectName: "textContentField"
            Layout.fillWidth: true
            text: panel.textDraftContent
            onTextChanged: panel.textDraftEdited(text)
        }

        // #450: a kép meglévő feliratát tölti a szövegmezőbe — feliratozatlan
        // képnél a gomb tiltott (a jegy szó szerinti szövege szerint)
        PanelButton {
            objectName: "textCopyCaptionButton"
            Layout.fillWidth: true
            label: qsTr("Copy Caption")
            tooltip: qsTr("Add text based on the picture's caption")
            buttonEnabled: panel.captionText.length > 0
            onButtonClicked: panel.textCopyCaptionRequested()
        }

        // #450: kitöltés-szín ÉS körvonal-szín, egymástól függetlenül — a
        // betűtípus-lista/méret/félkövér-dőlt-aláhúzott/igazítás ehhez a
        // lépcsőhöz NEM tartozik (valódi TrueType-rajzolót igényelne, ma
        // Hershey-fonttal rajzolunk — ld. #450 jegy).
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            ColumnLayout {
                spacing: 4
                Text {
                    text: qsTr("Text color")
                    font.pixelSize: Theme.fontSize - 1
                    color: Theme.textGray
                }
                TextColorSwatches {
                    objectName: "textFillColorSwatches"
                    currentColor: panel.textFillColor
                    onColorPicked: (hex) => panel.textFillColorEdited(hex)
                }
            }
            ColumnLayout {
                spacing: 4
                Text {
                    text: qsTr("Outline color")
                    font.pixelSize: Theme.fontSize - 1
                    color: Theme.textGray
                }
                TextColorSwatches {
                    objectName: "textOutlineColorSwatches"
                    currentColor: panel.textOutlineColor
                    onColorPicked: (hex) => panel.textOutlineColorEdited(hex)
                }
            }
        }

        CheckBox {
            id: textFillDisabledCheck
            objectName: "textFillDisabledCheck"
            Layout.fillWidth: true
            text: qsTr("Don't show the solid fill color (show outline only)")
            checked: !panel.textFillEnabled
            onToggled: panel.textFillEnabledEdited(!checked)
        }

        Label {
            text: qsTr("Outline thickness")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: textOutlineThicknessSlider
            objectName: "textOutlineThicknessSlider"
            Layout.fillWidth: true
            from: 0; to: 8
            stepSize: 1
            value: panel.textOutlineThickness
            onMoved: panel.textOutlineThicknessEdited(value)
        }

        Label {
            text: qsTr("Opacity")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: textOpacitySlider
            objectName: "textOpacitySlider"
            Layout.fillWidth: true
            from: 0; to: 1
            value: panel.textOpacity
            onMoved: panel.textOpacityEdited(value)
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "textApplyButton"
                label: qsTr("Apply") + " ✔"
                buttonEnabled: panel.textPlacementPending
                              && textContentField.text.length > 0
                onButtonClicked: panel.textApplyRequested()
            }
            PanelButton {
                objectName: "textCancelButton"
                label: qsTr("Cancel") + " ✘"
                onButtonClicked: panel.textCancelRequested()
            }
        }

        // #450: az összes szövegelem törlése — ma egyetlen szövegelem van,
        // a meglévő clearText (Visszavonás-verem NÉLKÜLI, azonnali) útvonalon
        PanelButton {
            objectName: "textRemoveAllButton"
            Layout.fillWidth: true
            label: qsTr("Remove all existing text")
            buttonEnabled: panel.hasTextOverlay
            onButtonClicked: panel.textRemoveAllRequested()
        }
    }
}
