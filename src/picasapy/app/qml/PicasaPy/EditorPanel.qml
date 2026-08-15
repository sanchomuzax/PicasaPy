import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

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
    readonly property real tallestTabHeight: Math.max(
        fixesTab.implicitHeight, finetunePanel.implicitHeight,
        effectsTab1.implicitHeight, effectsTab2.implicitHeight,
        effectsTab3.implicitHeight, effectsTab4.implicitHeight,
        legacyTab.implicitHeight)

    // #703: a panel magasság-igénye a fülek tartalma NÉLKÜL — fülsáv,
    // gombsor és a margók. Ez az a magasság, ami alá menni már azt jelenti,
    // hogy a Visszavonás/Újra sornak sincs helye. A hívó (PhotoViewer) ezt
    // használja alsó korlátnak, amikor a képernyőhöz igazítja az ablak
    // minimumát — beégetett szám nélkül.
    readonly property real chromeHeight:
        10 + tabBar.height + 6 + globalUndoRow.height + 10
    implicitHeight: panel.chromeHeight + panel.tallestTabHeight

    // #641/#703: a panel TÉNYLEGES és LÁTHATÓ magassága eltérhet. Egy
    // layout-cella nem zsugorít a kért méret alá, hanem hagyja túlnyúlni a
    // gyereket — a panel aljához igazodó gombsor pedig vele együtt csúszik
    // ki a képernyőről.
    //
    // #641 ezt a KÖZVETLEN szülővel korlátozta. Az kevés: ha a túlnyúlás egy
    // távolabbi ősnél történik, a panel a saját dobozán belül rendben van, a
    // doboz viszont már az ablakon kívül. Ezért végigmegyünk a TELJES
    // ős-láncon a jelenetgyökérig, és minden szinten megnézzük, mennyi
    // maradt a panelnek — ez lényegében az ABLAK koordinátarendszerében mért
    // korlát. A ciklus a `y`/`height` tulajdonságokat olvassa, ezért a QML
    // mindegyikre kötés-függőséget vesz fel: ha bármelyik ős elmozdul vagy
    // átméreteződik, ez újraszámolódik.
    readonly property real visibleHeight: {
        var limit = panel.height
        var item = panel
        var offset = 0
        while (item.parent) {
            offset += item.y
            // A NULLA magasságú őst kihagyjuk: az nem szűk hely, hanem
            // „még nincs elrendezve" (a jelenetgyökér a megjelenítésig 0).
            // Ha egy ős tényleg nulla magas, a panelből úgysem látszik
            // semmi — a korlátozásnak ott nincs mit megvédenie.
            if (item.parent.height > 0)
                limit = Math.min(limit, item.parent.height - offset)
            item = item.parent
        }
        return Math.max(0, limit)
    }

    // #703: a látható fül tartalmának TELJES igénye (vágás nélkül), és
    // amennyi hely ebből ténylegesen jut neki a gombsor fölött. A kettő
    // eltérése a SZÜKSÉG-ÁG: ilyenkor — és kizárólag ilyenkor — vágunk.
    // Külön, olvasható állapotként, hogy a teszt tudja állítani, és ne csak
    // „valahogy" működjön (#703/4).
    //
    // #659: a fülek egy része FELSŐ MARGÓVAL ül (`anchors.margins`), ezért a
    // puszta `implicitHeight` kevesebb, mint a tényleges alsó szél — a
    // gyerek `y`-ját is bele kell számolni. Az `implicitHeight`-et (és nem a
    // `height`-et) használjuk, mert az nem függ a szülő magasságától — így
    // nincs kötési hurok.
    readonly property real tabContentHeight: {
        var tallest = 0
        var kids = tabArea.children
        for (var i = 0; i < kids.length; ++i) {
            if (!kids[i].visible)
                continue
            var also = kids[i].y + kids[i].implicitHeight
            if (also > tallest)
                tallest = also
        }
        return tallest
    }
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
    property real textFontScale: 1
    property bool textBold: false
    property bool textItalic: false
    property bool textUnderline: false
    property string textAlign: "left"
    signal textFontFamilyEdited(string key)
    signal textFontScaleEdited(real value)
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
        // #516: a "color" vezérlők kezdőértéke a katalógus hex-alapértéke,
        // nem a (náluk értelmezetlen) numerikus `default` mező
        var values = []
        for (var i = 0; i < params.length; i++)
            values.push(params[i].kind === "color" ? params[i].color : params[i].default)
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

    // #496: a csúszka-felirat-fordító switch (#316) az EditorParamPanel.qml-be
    // került, az egyetlen hívója mellé; ez a vékony átjáró tartja meg a
    // panel-szintű felületet (a meglévő tesztek a panelen hívják).
    function paramLabel(key) {
        return effectParamScroll.paramLabel(key)
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
    signal cropApplyRequested()
    signal cropCancelRequested()

    // a négy csúszka aktuális értékét egyben küldi (élő előnézet)
    function emitFinetunePreview() {
        panel.finetunePreview(finetunePanel.fillSlider.value,
                               finetunePanel.highlightsSlider.value,
                               finetunePanel.shadowsSlider.value,
                               finetunePanel.tempSlider.value)
    }
    // a csúszkák a mentett (kontroller) értékekre állnak — előnézet nélkül
    function syncFinetuneSliders() {
        panel.suppressFinetune = true
        finetunePanel.fillSlider.value = panel.fillLight
        fixesTab.fillSlider.value = panel.fillLight   // #337: a másik fül párja
        finetunePanel.highlightsSlider.value = panel.highlights
        finetunePanel.shadowsSlider.value = panel.shadows
        finetunePanel.tempSlider.value = panel.colorTemp
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
        finetunePanel.fillSlider.value = value
        fixesTab.fillSlider.value = value
        panel.suppressFinetune = false
        panel.emitFinetunePreview()
    }

    // a négy csúszka aktuális értékének MENTÉSE (a húzás végén) — a
    // Finomhangolás fül minden csúszkája és a Gyakori javítások fülön lévő
    // Derítőfény-párja is ezen az egy ponton megy ki
    function emitFinetuneCommit() {
        panel.finetuneCommit(finetunePanel.fillSlider.value,
                             finetunePanel.highlightsSlider.value,
                             finetunePanel.shadowsSlider.value,
                             finetunePanel.tempSlider.value)
    }
    function fillLightCommitted() { panel.emitFinetuneCommit() }
    onFillLightChanged: panel.syncFinetuneSliders()
    onActiveTabChanged: {
        panel.syncFinetuneSliders()
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

    // Arány-lista (#448 — a Picasa BINÁRISÁBAN élő kulcskészlet szerint,
    // ld. a #448 jegy 2026-08-07-es javító kommentjét: "ha egyszer
    // implementáljuk, a KULCSNEVEKET használjuk, ne a magyarázatokat").
    // `key` = a bináris tényleges kulcsneve (perzisztenciához, lastCropRatio-
    // hoz); `label` = megjelenő felirat, a kulcsnevet követve (pl. "4x6"),
    // KIVÉVE ahol a kulcs maga nem arány-pár (Manual/CurrentRatio/Square/
    // FullPage) — ott a korábbi, leíró feliratot tartottuk meg.
    //
    // #448: a listaelemek MAGYARÁZÓ ALCÍMET is kapnak — a `Picasa3i18n.dll`
    // szerint a legördülőben nem csak a szám állt, hanem a felismerést
    // segítő leírás is („Kisméretű nyomat", „CD-borító", „Letter méretű
    // papír"). A korábban kihagyott kulcsok arányát ugyanez a forrás
    // oldotta fel: `Widescreen` = 16:10, `WideFrame` = 5:3,
    // `CurrentDisplay` = a KÉPERNYŐ aktuális aránya.
    //
    // ratio = szélesség/magasság fekvő tájolásban; 0 = kézi (szabad),
    // -1 = a kép jelenlegi aránya, -2 = a képernyő aktuális aránya.
    readonly property var aspectPresets: [
        { key: "Manual", label: qsTr("Manual"), note: "", ratio: 0 },
        { key: "CurrentRatio", label: qsTr("Current ratio"), note: "", ratio: -1 },
        { key: "CurrentDisplay", label: qsTr("Current display"), note: "",
          ratio: -2 },
        { key: "4x4", label: "4x4", note: "", ratio: 1 },
        { key: "Desktop4x3", label: "4x3", note: qsTr("Standard screen"),
          ratio: 4 / 3 },
        { key: "4x6", label: "4x6", note: qsTr("Small print"), ratio: 6 / 4 },
        { key: "5x7", label: "5x7", note: qsTr("Large print"), ratio: 7 / 5 },
        { key: "8x10", label: "8x10", note: "", ratio: 10 / 8 },
        { key: "8.5x11", label: "8.5x11", note: qsTr("Letter paper"),
          ratio: 11 / 8.5 },
        { key: "5x3", label: "5x3", note: qsTr("Widescreen Photo Frame"),
          ratio: 5 / 3 },
        { key: "9x13", label: "9x13", note: qsTr("Small print"), ratio: 13 / 9 },
        { key: "10x15", label: "10x15", note: qsTr("Large print"),
          ratio: 15 / 10 },
        { key: "13x18", label: "13x18", note: "", ratio: 18 / 13 },
        { key: "20x25", label: "20x25", note: "", ratio: 25 / 20 },
        { key: "5x8", label: "5x8", note: "", ratio: 8 / 5 },
        { key: "16x10", label: "16x10", note: qsTr("Widescreen monitor"),
          ratio: 16 / 10 },
        { key: "HDTV16x9", label: "16x9", note: "HDTV", ratio: 16 / 9 },
        { key: "Square", label: qsTr("Square"), note: qsTr("CD Cover"),
          ratio: 1 },
        { key: "FullPage", label: qsTr("Full page (A4)"), note: qsTr("Full page"),
          ratio: 297 / 210 }
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
        anchors.margins: 10
    }

    // ---------------- a FÜLEK közös területe (NEM görgethető) ----------
    //
    // #628 — a #616 visszavonása. A #422 a felhasználó nyomatékos kérésére
    // levette a görgethető keretet az effekt-fülekről; a #616 aztán, a
    // kilógó gombsort orvosolva, VISSZATETTE. A valódi ok azonban nem a
    // fülek mérete volt, hanem egy beégetett szám: a PhotoViewer.qml fix
    // 420 képpontot adott a panelnek, akármekkora az ablak. A 3. fül 12
    // bélyegképes csempéje (3×4 ≈ 450 px) ennél MINDIG magasabb, ezért a
    // görgetés nem szélsőséges eset volt, hanem az alapállapot.
    //
    // Az eredetiben a panel FIX méretű, és a kényszer-alapú (.tre)
    // elrendezésben a rács mindig kifér — görgetés nincs. Nálunk ezt a
    // garanciát a panel `implicitHeight`-je adja (ld. lent): az a
    // LEGMAGASABB fület is elbírja, a gombsor pedig a tartalmat követi,
    // nem fix magasságon ül.
    Item {
        id: tabArea
        objectName: "editorTabArea"
        // a csúszkás alpanel a fülek HELYETT jelenik meg (nem föléjük)
        visible: !panel.modeToolActive && !panel.paramPanelActive
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        // a terület magassága a LÁTHATÓ fülé — egyszerre legfeljebb egy az.
        // ALAPÁLLAPOTBAN nincs vágás és nincs görgetősáv: a tartalomnak el
        // KELL férnie (#422/#628 — a görgethető keret levételét a felhasználó
        // nyomatékosan kérte, és a #616 visszahozta; nem harmadszor is).
        //
        // #703: EGYETLEN kivétel, a szükség-ág. Ha a kijelző annyira alacsony,
        // hogy a panel nem kaphatja meg az igényét (az ablak minimuma nem
        // lehet nagyobb a képernyőnél), akkor a fül tartalma veszít — soha nem
        // a gombsor. A vágás ilyenkor és csak ilyenkor kapcsol be, és a
        // `panel.tabContentTruncated`-en át MÉRHETŐ, hogy melyik ágon vagyunk.
        height: tabArea.visible
                ? Math.min(panel.tabContentHeight, panel.tabAreaAvailable) : 0
        clip: panel.tabContentTruncated


        // ---------------- 1. fül: "Gyakori javítások" ikonrács ----------------
        // #496: a fül tartalma önálló fájlban (EditorTabCommonFixes.qml) — a
        // láthatóság és a horgonyok itt, a testvér-fülek mintája szerint.
        EditorTabCommonFixes {
            id: fixesTab
            panel: panel
            visible: !panel.modeToolActive && panel.activeTab === 0
                     && !panel.paramPanelActive  // #583
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }

        // ---------------- "finetune" mód: Finomhangolás (#20/#464) ----------
        // #464/#496: a fül tartalma önálló fájlban, a tulajdonos négy
        // képernyőképe szerinti elrendezéssel (ld. ott).
        EditorFinetunePanel {
            id: finetunePanel
            panel: panel
            visible: !panel.modeToolActive && panel.activeTab === 1
                     && !panel.paramPanelActive  // #583
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }

        // ---------------- "effects" mód: Effektek (#20) ----------------
        EditorEffectsTab1 {
            id: effectsTab1
            panel: panel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }

        // ---------------- "effects2" mód: 4. effekt-fül — zöld ecset,
        // "kreatív effektek" (#328, docs/specs/ui-audit-editor.md 4. fül) ------
        EditorEffectsTab2 {
            id: effectsTab2
            panel: panel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }

        // ---------------- "effects3" mód: 5. effekt-fül — kék ecset,
        // "művészi effektek" (#328, docs/specs/ui-audit-editor.md 5. fül) ------
        EditorEffectsTab3 {
            id: effectsTab3
            panel: panel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }

        // ---------------- "retouch" mód: Retusálás (#148) ----------------
        // A Vágás mintáját követi: a kép TELJES panel-területét foglalja el a
        // fülsáv/rács helyett; a kattintások kezelését a hívó (PhotoViewer)
        // végzi a képen (ez a fájl nem ismeri a kép geometriáját), a puffer
        // méretét (retouchRegionCount) és az Alkalmaz/Mégse gombokat mutatja.

        // ---------------- "redeye" mód: Vörösszem (#445) ----------------
        // Az automatika a panel megnyitásakor lefut; a kézzel húzott
        // téglalapokat — a Retusálás mintájára — a hívó (PhotoViewer) veszi fel
        // a képen, ez a fájl a puffer-állapotot és a gombokat mutatja.

        // ---------------- "text" mód: Szöveg-overlay (#148) ----------------
        // A pozicionálás is kattintással történik a képen (a hívó feladata,
        // ld. retouchColumn megjegyzése) — a szövegmező itt él, a tartalom
        // gépelését a textDraftEdited jel viszi a controllerhez.

        // ---------------- 6. fül: a további Glimmer-effektek (#422) --------
        EditorEffectsTab4 {
            id: effectsTab4
            panel: panel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }

        // ---------------- 7. fül: örökölt, felület nélküli szűrők (#571) ---
        EditorLegacyTab {
            id: legacyTab
            panel: panel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }

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
    // #464 (felhasználói hibajelentés az effekt-fülekről, ugyanaz az
    // osztály): ezek a panelek a tartalmuktól függően MAGASABBAK lehetnek,
    // mint a rendelkezésre álló hely — vágás/görgetés nélkül rálógnának a
    // panel alján ülő, globális Visszavonás/Újra sorra. Ezért mind a négy
    // EGY közös, vágott görgethető területen ül, ami pontosan a gombsorig
    // ér. Egyszerre mindig legfeljebb egy látszik (a saját `visible`
    // kötése szerint), a görgethető magasság ezért a LÁTHATÓÉ.
    Flickable {
        id: modeToolScroll
        objectName: "editorModeToolScroll"
        visible: panel.modeToolActive
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: globalUndoRow.top
        anchors.bottomMargin: 6
        clip: true
        contentWidth: width
        contentHeight: Math.max(
            cropModePanel.visible ? cropModePanel.implicitHeight : 0,
            retouchModePanel.visible ? retouchModePanel.implicitHeight : 0,
            redeyeModePanel.visible ? redeyeModePanel.implicitHeight : 0,
            textModePanel.visible ? textModePanel.implicitHeight : 0)
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: PicasaScrollBar {}

        // ---- "crop" mód: Fotó vágása ----
        EditorCropPanel {
            id: cropModePanel
            panel: panel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }

        // ---- "retouch" mód: Retusálás (#148) ----
        // A kattintások kezelését a hívó (PhotoViewer) végzi a képen (ez a
        // fájl nem ismeri a kép geometriáját); a panel a puffer méretét és
        // az Alkalmaz/Mégse gombokat mutatja.
        EditorRetouchPanel {
            id: retouchModePanel
            panel: panel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }

        // ---- "redeye" mód: Vörösszem (#445) ----
        // Az automatika a panel megnyitásakor lefut; a kézzel húzott
        // téglalapokat a hívó (PhotoViewer) veszi fel a képen.
        EditorRedeyePanel {
            id: redeyeModePanel
            panel: panel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }

        // ---- "text" mód: Szöveg-overlay (#148) ----
        // A pozicionálás is kattintással történik a képen; a szövegmező itt
        // él, a gépelést a textDraftEdited jel viszi a controllerhez.
        EditorTextPanel {
            id: textModePanel
            panel: panel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
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

    // ---------------- párbeszédek (#448, #459) ----------------
    // #496: külön fájlban (EditorDialogs.qml).
    EditorDialogs {
        id: editorDialogs
        panel: panel
    }



    // ---------------- #464: GLOBÁLIS Visszavonás/Újra ----------------
    //
    // Az eredeti Picasában a pár a panel ALJÁN ül, és NEM fülhöz kötött —
    // minden eszközben elérhető. Korábban mind az öt fül saját (azonos)
    // gombpárt rajzolt; most egyetlen, a panel aljához horgonyzott sor van,
    // és a fül-oszlopok EFÖLÖTT érnek véget (`anchors.bottom`).
    // #641: a sor a LÁTHATÓ terület alján ül, mindig. A #628 „lejjebb
    // tolódik, ha nem fér el" ága MEGSZŰNT: az eredetiben nincs ilyen, és a
    // gyakorlatban azt eredményezte, hogy a sor kicsúszott a képernyőről —
    // a felhasználó egyáltalán nem látta a Visszavonás/Újra gombokat.
    //
    // Ha szűkös a hely, a FÜL TARTALMA veszít, nem a gombsor: a
    // Visszavonás/Újra a szerkesztés visszacsinálásának egyetlen útja, egy
    // levágott csempesor ennél sokkal kisebb baj. Hogy ez az ág egyáltalán
    // ne forduljon elő, az ablak minimális magassága elbírja a panel
    // `implicitHeight`-jét (Main.qml).
    RowLayout {
        id: globalUndoRow
        objectName: "editorGlobalUndoRow"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        y: Math.max(0, panel.visibleHeight - height - 10)
        spacing: 6
        opacity: panel.enabled ? 1 : 0.45

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
            // #405: egyenlő szélességű pár (nem egy keskeny + egy kitöltő)
            onButtonClicked: panel.redoRequested()
        }
    }
}
