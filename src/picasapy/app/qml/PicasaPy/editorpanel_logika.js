// Az `EditorPanel.qml` LOGIKÁJA — állapot-átmenetek és segédszámítások
// (#3220).
//
// Miért külön fájl (az `infosav.js` / `aranykenyszer.js` / `lasso.js`
// mintája): az `EditorPanel.qml` a szerkesztő gazdája, és 1295 sorra nőtt —
// a projekt saját 800-as korlátja fölé. A fájl a projekt egyik legforróbb
// helye, tehát minél nagyobb, annál gyakrabban ütközik két párhuzamos jegy
// ugyanabban a blokkban.
//
// ⚠️ A szétbontás **viselkedés-azonos**: a panel felülete (a metódusnevek
// és az `objectName`-ek) változatlan, a QML-ben vékony átjárók maradtak.
// Egyetlen meglévő őr-teszt sem változott — sem állítás, sem elemnév.
//
// ## Miért nem kell paramétereket átvezetni
//
// Ez NEM `.pragma library`: a QML-dokumentumba relatívan importált
// JavaScript a KOMPONENS hatókörében fut, tehát látja a `panel` azonosítót,
// a gyerekek id-jét (`finetunePanel`, `effectParamScroll`, …) és a
// kontextus-property-ket (`editController`) is. Mérve: egy próba-QML-ből
// importált JS-ben a kontextus-property `number`-ként, az id `object`-ként
// látszott. Ezért a függvények SZÓ SZERINT kerültek át.
//
// ## Ami SZÁNDÉKOSAN maradt a QML-ben
//
// A `cropSuggestionLabel` — `qsTr()`-t tartalmaz, és a fordítás kontextusa
// a FÁJL alapneve: ha ide kerülne, a `picasapy_hu.ts`-ben az öt javaslat-
// felirat új, üres kontextusba csúszna, és a honosítás némán elveszne.

function frissitsdAShiftAllapotot() {
    //: ⚠️ A #305 null-őr ITT NEM ELÉG. A QML-tesztek egy része CSONK
    //: vezérlőt ad (`_FakeEditController`), ami LÉTEZIK, csak ezt a
    //: metódust nem ismeri — a puszta `editController` vizsgálat
    //: átengedné, és a hívás `TypeError`-t dobna. A kivétel pedig
    //: MEGSZAKÍTANÁ az `onActiveTabChanged` kezelő hátralévő részét
    //: (a paraméter-panel bezárását!), tehát egy látszólag ártatlan
    //: új hívás vinne el egy egészen más funkciót. A CI ezt el is
    //: kapta (#2146).
    if (typeof editController === "undefined" || !editController)
        return
    if (typeof editController.shiftLenyomva !== "function")
        return
    //: #798: a kötést csak akkor írjuk felül, ha a vezérlő NEM adja
    //: az élő állapotot (régi csonk a próbákban). Élő vezérlőnél a
    //: kötés magától követ, és a felülírás pont azt törné el.
    if (editController.shiftAktiv !== undefined)
        return
    panel.shiftMasodlagos = editController.shiftLenyomva()
}

function allitsdAShiftFigyelest() {
    //: #798: a Shift-figyelés eseményszűrője MINDEN eseményre átlép
    //: Pythonba — mérve a `test_people_panel_26.py` 13 s-ról 25 s-ra
    //: nőtt tőle. Ezért csak a NÉGY effekt-fülön van fent (2–5); a
    //: Shift a kilenc csempe közül négyet ezeken vált át.
    if (typeof editController === "undefined" || !editController)
        return
    if (typeof editController.figyeldAShiftet !== "function")
        return
    editController.figyeldAShiftet(panel.activeTab >= 2
                                   && panel.activeTab <= 5)
}

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

function hasBadge(effectName) {
    return panel.oneClickEffects.indexOf(effectName) >= 0
}

function effectAppliedCount(effectName) {
    var count = panel.effectChainCounts[effectName]
    return count === undefined ? 0 : count
}

// egy effekt-gomb kattintása: ha az effektnek vannak paraméterei,
// megnyitja az alpanelt és true-t ad vissza — ilyenkor a hívó (a gomb
// onButtonClicked-je) NEM küldi az effectRequested jelet. Egyébként
// (vagy ha nincs editController — ld. fent) false-t ad vissza, és a
// gomb VÁLTOZATLANUL a meglévő effectRequested jelet küldi tovább. Az
// effectRequested hívás szó szerinti (nem változóból font) formája
// minden gombnál megmarad, csak feltételesen fut le — a
// test_effect_names.py #315-ös regex-alapú lefedettség-ellenőrzése
// erre épít.
//
// #700: a második paraméter a megnyitó csempe SAJÁT felirata — ebből
// lesz az alpanel címe (ld. `paramEffectLabel`). Elhagyható: régi,
// felirat nélküli hívónál a cím a belső kulcsra esik vissza.
function tryOpenParamPanel(name, displayLabel) {
    if (panel.hasEffectController() && editController.effectHasParams(name)) {
        panel.openParamPanel(name, displayLabel)
        return true
    }
    return false
}

// az alpanel megnyitása: csúszkák a katalógus alapértékein, azonnali
// élő előnézettel.
function openParamPanel(name, displayLabel) {
    if (!panel.hasEffectController()) return
    var params = editController.effectParams(name)
    // #516: a "color" vezérlők kezdőértéke a katalógus hex-alapértéke,
    // nem a (náluk értelmezetlen) numerikus `default` mező
    var values = []
    for (var i = 0; i < params.length; i++)
        values.push(params[i].kind === "color" ? params[i].color : params[i].default)
    panel.paramEffectName = name
    panel.paramEffectLabel = displayLabel ? displayLabel : ""
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
    panel.paramEffectLabel = ""
    panel.paramEffectParams = []
    panel.paramEffectValues = []
}

// #496: a csúszka-felirat-fordító switch (#316) az EditorParamPanel.qml-be
// került, az egyetlen hívója mellé; ez a vékony átjáró tartja meg a
// panel-szintű felületet (a meglévő tesztek a panelen hívják).
function paramLabel(key) {
    return effectParamScroll.paramLabel(key)
}

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
    // #876: ISMERETLEN kulcs → „Kézi". Ez nem elméleti eset: a lista
    // hat tétele (`CurrentDisplay`, `4x4`, `4x6`, `5x7`, `8x10`,
    // `8.5x11`) kikerült, és aki korábban ilyet választott, annak a
    // beállítása MOST is ott van a QSettingsben. A korábbi kód ilyenkor
    // csak visszatért, tehát az `aspectIndex` az ELŐZŐ képen használt
    // értéken maradt — a vágó néma, láthatatlan aránnyal nyílt volna.
    panel.aspectIndex = 0
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
function lathatoMagassag() {
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


function fulTartalomMagassag() {
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
