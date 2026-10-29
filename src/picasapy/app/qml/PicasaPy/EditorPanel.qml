import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "editorpanel_logika.js" as Logika

// A PhotoViewer bal oldali szerkesztőpanelje. A fülek, módok, párbeszédek,
// állapotcsoportok és elmosott rétegek külön komponensekben élnek; a panel
// megtartja a hívók által használt tulajdonságokat, jeleket és függvényeket.
Rectangle {
    id: panel
    objectName: "editorPanel"
    //: #3463: a Shift+F1 fejezete (ld. `Main.qml` `helpTopicUnderCursor`)
    property string helpTopic: "features/szerkeszto.md"
    color: Theme.chromeBg
    // #411: FIX pixelszélesség — az eredeti panel NEM skálázódik az
    // ablakmérettel (a #405 tévesen levetítette; a felhasználó
    // screenshot-összevetése bizonyította a hibát). Ld.
    // docs/specs/design-guide.md „Néző eszközpanel" sorát. A
    // PhotoViewer.qml `Layout.preferredWidth`-jét EZZEL összhangban kell
    // tartani (ott állítva, nem itt).
    implicitWidth: 280

    // A panel a mért 277 px-es fülmagasságot használja; az aktív fültől
    // független állandó méretet a #703/#3247 őrzi.
    readonly property real mertTabPanelHeight: 277

    // A fülek tartalma nélküli panelmagasságot a PhotoViewer alsó korlátként használja.
    readonly property real chromeHeight:
        10 + panelTabs.tabBarItem.height + 6 + globalUndoRow.height + 10
    implicitHeight: panel.chromeHeight + panel.mertTabPanelHeight

    //: #3220: a látható magasság számítása az `editorpanel_logika.js`-ben él.
    readonly property real visibleHeight: Logika.lathatoMagassag()

    //: #3220: a fül tartalmának magassága az `editorpanel_logika.js`-ben él.
    readonly property real tabContentHeight: Logika.fulTartalomMagassag()

    readonly property real tabAreaAvailable:
        Math.max(0, globalUndoRow.y - 6 - panelTabs.tabAreaItem.y)
    readonly property bool tabContentTruncated:
        panelTabs.tabAreaItem.visible
            && panel.tabContentHeight > panel.tabAreaAvailable + 0.5

    // #641: a Visszavonás/Újra sor alja a panelen belül.
    readonly property real undoRowBottom: globalUndoRow.y + globalUndoRow.height

    // 0–4: eredeti fülek; 5–6: saját fülek (#1187).
    // SAJÁT FUNKCIÓ (#1187): a szerkesztő 7 fülből csak 5 (0-4. index) van meg
    // az eredeti Picasában; az 5. (#422) és a 6. (#571) index a MI hozzáadásunk. A
    // bináris-egyezés erre a két fülre NEM vonatkozik: hogy az eredetiben
    // nincs ilyen fül, nem hiba. Lista: docs/decisions/vedett-sajat-funkciok.md
    property int activeTab: 0

    property alias cropActive: toolsState.cropActive
    property alias tiltActive: toolsState.tiltActive
    property alias redeyeActive: toolsState.redeyeActive
    property alias retouchActive: toolsState.retouchActive
    property alias textActive: toolsState.textActive
    property alias retouchRegionCount: toolsState.retouchRegionCount
    property alias retouchPatchPending: toolsState.retouchPatchPending
    property alias canUndoPatch: toolsState.canUndoPatch
    property alias canRedoPatch: toolsState.canRedoPatch
    property alias brushSize: toolsState.brushSize
    signal brushSizeEdited(int value)
    signal retouchUndoPatchRequested()
    signal retouchRedoPatchRequested()
    signal retouchResetRequested()
    property alias redeyeRegionCount: toolsState.redeyeRegionCount
    property alias canUndoRedeyeRegion: toolsState.canUndoRedeyeRegion
    property alias redeyeResetAvailable: toolsState.redeyeResetAvailable
    property alias canReapplyRedeyeAuto: toolsState.canReapplyRedeyeAuto
    property alias redeyeAutoReset: toolsState.redeyeAutoReset
    property alias redeyeFoundCount: toolsState.redeyeFoundCount
    property alias redeyeHideOutlines: toolsState.redeyeHideOutlines
    signal redeyeAutoRequested()
    signal redeyeUndoRegionRequested()
    signal redeyeResetRequested()
    signal redeyeApplyRequested()
    signal redeyeCancelRequested()
    property alias textDraftContent: textState.textDraftContent
    property alias textPlacementPending: textState.textPlacementPending
    //: #3123: a kép fölötti eszköz-sáv ebből tudja, mikor alkalmazható a
    //: szöveg (a szövegmező a `EditorTextPanel`-ben él).
    readonly property bool textApplyEnabled:
        panelOverlays.textApplyEnabled
    property alias captionText: textState.captionText
    property alias hasTextOverlay: textState.hasTextOverlay
    property alias textOverlayVisible: textState.textOverlayVisible
    property alias textFillColor: textState.textFillColor
    property alias textOutlineColor: textState.textOutlineColor
    property alias textOutlineThickness: textState.textOutlineThickness
    property alias textFillEnabled: textState.textFillEnabled
    property alias textOpacity: textState.textOpacity
    readonly property bool modeToolActive: toolsState.modeToolActive
    signal retouchApplyRequested()
    signal retouchCancelRequested()
    signal textDraftEdited(string content)
    signal textApplyRequested()
    signal textCancelRequested()
    signal textCopyCaptionRequested()
    signal textRemoveAllRequested()
    signal textOverlayVisibleEdited(bool visible)
    signal textFillColorEdited(string hex)
    signal textOutlineColorEdited(string hex)
    signal textOutlineThicknessEdited(real value)
    signal textFillEnabledEdited(bool value)
    signal textOpacityEdited(real value)
    property alias fontFamilyCatalogue: textState.fontFamilyCatalogue
    readonly property var fontFamilyKeys: textState.fontFamilyKeys
    readonly property var fontFamilyLabels: textState.fontFamilyLabels
    property alias textFontFamily: textState.textFontFamily
    property alias textFontSize: textState.textFontSize
    property alias fontSizeChoices: textState.fontSizeChoices
    property alias textBold: textState.textBold
    property alias textItalic: textState.textItalic
    property alias textUnderline: textState.textUnderline
    property alias textAlign: textState.textAlign
    signal textFontFamilyEdited(string key)
    signal textFontSizeEdited(int value)
    signal textBoldEdited(bool value)
    signal textItalicEdited(bool value)
    signal textUnderlineEdited(bool value)
    signal textAlignEdited(string value)
    property alias enhanceEnabled: toolsState.enhanceEnabled
    property alias autolightEnabled: toolsState.autolightEnabled
    property alias autocolorEnabled: toolsState.autocolorEnabled

    property alias undoAvailable: toolsState.undoAvailable
    property alias redoAvailable: toolsState.redoAvailable
    property alias neutralPickerActive: toolsState.neutralPickerActive
    property alias neutralColor: toolsState.neutralColor
    signal neutralPickerToggled()
    property alias effectColorPickerTarget: toolsState.effectColorPickerTarget
    // #551: a szín-varázspálca NEM az autocolor szűrőt teszi a láncra: a
    // finetune2 „semleges szín" (p4) mezőjét állítja be automatikusan
    // választott színnel — a Picasa saját .picasa.ini-je bizonyítja
    // (finetune2=1,0,0,0,006b8088,0). Ezért külön jelzés, nem toolActivated.
    signal colorWandRequested()

    property string undoLabel: qsTr("Undo")
    property string redoLabel: qsTr("Redo")

    // a kép aktuális szélesség/magasság aránya ("Jelenlegi méretarány"-hoz)
    property real imageAspect: 4 / 3
    // A vágó méretarány-sorai az eredeti, megjelenített kép pixeleiből
    // számolnak; a `cropRect` relatív értékeit ezekre vetítjük (#4549).
    property int imagePixelWidth: 0
    property int imagePixelHeight: 0
    property rect cropRect: Qt.rect(0, 0, 0, 0)
    property bool cropHasSelection: false

    property alias straightenActive: toolsState.straightenActive
    property alias aspectIndex: cropState.aspectIndex
    property alias aspectRotated: cropState.aspectRotated

    property alias fillLight: finetuneState.fillLight
    property alias highlights: finetuneState.highlights
    property alias shadows: finetuneState.shadows
    property alias colorTemp: finetuneState.colorTemp
    property alias suppressFinetune: finetuneState.suppressFinetune
    signal finetunePreview(real fill, real highlights, real shadows, real temp)
    signal finetuneCommit(real fill, real highlights, real shadows, real temp)

    property alias shiftMasodlagos: effectState.shiftMasodlagos

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

    property alias paramPanelActive: effectState.paramPanelActive
    property alias paramPanelSuspended: effectState.paramPanelSuspended
    readonly property bool paramPanelContentBlurred:
        effectState.paramPanelContentBlurred
    property alias paramEffectName: effectState.paramEffectName
    property alias paramEffectParams: effectState.paramEffectParams
    property alias paramEffectValues: effectState.paramEffectValues
    property alias paramEffectLabel: effectState.paramEffectLabel
    readonly property string paramEffectTitle: effectState.paramEffectTitle
    readonly property bool legacyEffectsPresent: effectState.legacyEffectsPresent
    readonly property string effectThumbPhotoId: effectState.effectThumbPhotoId
    readonly property var effectChainCounts: effectState.effectChainCounts
    readonly property var oneClickEffects: effectState.oneClickEffects

    function hasEffectController() { return Logika.hasEffectController() }

    // A fülsáv kattintása nyitott effektpanelnél nem vált fület és nem
    // dobja el az előnézetet: a Picasa az első fül letiltott tartalmát
    // mutatja. A kijelölt fül az eredeti effekt füle marad.
    function selectTab(tabIndex) {
        if (panel.paramPanelSuspended) return
        if (panel.paramPanelActive) {
            panel.paramPanelSuspended = true
            // #5674: a felfüggesztett alpanel pipettája nem marad élesen
            panel.effectColorPickerTarget = -1
            return
        }
        panel.activeTab = tabIndex
    }

    function effectThumbSource(effectName) { return Logika.effectThumbSource(effectName) }

    function hasBadge(effectName) { return Logika.hasBadge(effectName) }

    function effectAppliedCount(effectName) { return Logika.effectAppliedCount(effectName) }

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
    signal cropRotateRequested()
    signal cropPreviewHold(bool held)
    signal cropResetRequested()
    property alias cropResetEnabled: cropState.resetEnabled
    property alias cropSuggestions: cropState.suggestions
    signal cropSuggestionChosen(real x, real y, real w, real h)
    function cropSuggestionLabel(key) {
        return cropState.suggestionLabel(key)
    }
    readonly property string cropSuggestionThumbSource:
        cropState.suggestionThumbSource
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
        // #583: ha az aktív fül állapota közvetlenül megváltozik, a nyitott
        // effekt-paraméter alpanel BEZÁRUL, és
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

    readonly property var aspectPresets: cropState.aspectPresets
    readonly property var customAspectRatios: cropState.customAspectRatios
    readonly property var aspectFullList: cropState.aspectFullList
    readonly property var selectedPreset: cropState.selectedPreset
    readonly property real currentAspect: cropState.currentAspect

    function formatCropPixelSize(width, height) {
        return cropState.formatCropPixelSize(width, height)
    }

    function restoreLastCropRatio() { return Logika.restoreLastCropRatio() }
    function selectAspect(index) { return Logika.selectAspect(index) }

    function handleToolClick(tool) { return Logika.handleToolClick(tool) }

    EditorPanelToolsState {
        id: toolsState
        editorPanel: panel
    }
    EditorPanelTextState {
        id: textState
        editorPanel: panel
    }
    EditorPanelFinetuneState {
        id: finetuneState
        editorPanel: panel
    }
    EditorPanelEffectState {
        id: effectState
        editorPanel: panel
        hostEditController: typeof editController !== "undefined"
            ? editController : null
    }
    EditorPanelCropState {
        id: cropState
        editorPanel: panel
        hostController: typeof controller !== "undefined" ? controller : null
        hostEditController: typeof editController !== "undefined"
            ? editController : null
    }

    // A fülsáv, a hét fül és a paraméterpanel önálló layout-komponensben él.
    EditorPanelTabs {
        id: panelTabs
        panel: panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: globalUndoRow.top
        anchors.bottomMargin: 6
    }
    readonly property Item finetunePanel: panelTabs.finetunePanel
    readonly property Item fixesTab: panelTabs.fixesTab

    // A mód-eszközök és párbeszédgazdák önálló komponensbe kerültek.
    EditorPanelOverlays {
        id: panelOverlays
        panel: panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: globalUndoRow.top
        anchors.bottomMargin: 6
    }

    //: #2480: nyitva van-e a szerkesztő valamelyik MODÁLIS párbeszéde. A
    //: gazda (`PhotoViewer`) ebből teszi ki az elhomályosító réteget —
    //: az eredetiben ez a `editpanel/modaldialogblur` (`editpanel.tre:1362`),
    //: ami a `root` gyereke, tehát a TELJES szerkesztő fölé kerül, nem a bal
    //: panelen belülre.
    readonly property bool modalDialogOpen: panelOverlays.modalDialogOpen



    // ---------------- #464: GLOBÁLIS Visszavonás/Újra ----------------
    //
    // A sor önálló fájlban él (#3220) — az indoklások és a mért
    // geometria ott olvashatók (`EditorUndoRow.qml`).
    EditorUndoRow {
        id: globalUndoRow
        panel: panel
        tabArea: panelTabs.tabAreaItem
        anchors.left: parent.left
        anchors.right: parent.right
        // #741: a MÉRT geometria — a két gomb x 7..139 és x 144..276
        anchors.leftMargin: 7
        anchors.rightMargin: 4
    }

    EditorPanelBlurEffects {
        editorPanel: panel
        tabs: panelTabs
        tabArea: panelTabs.tabAreaItem
        undoRow: globalUndoRow
    }
}
