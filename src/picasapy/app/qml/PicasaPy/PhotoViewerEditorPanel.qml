import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

EditorPanel {
    id: editorPanel
    property var hostViewer: null
    readonly property var hostEditCtl:
        (typeof editController !== "undefined") ? editController : null
    property var hostPhotoArea: null
    property var hostCropOverlay: null
    property var hostCopyCaptionConfirmLoader: null
    property var hostUndoDataLossDialogLoader: null
    objectName: "viewerEditorPanel"
    // videónál a szerkesztő-eszközök nem értelmezettek (#14),
    // a fülsáv helyén a videó-panel (#4566) áll
    enabled: !editorPanel.hostViewer.isCurrentVideo
    visible: !editorPanel.hostViewer.isCurrentVideo
    // #628: a panel a RENDELKEZÉSRE ÁLLÓ magasságot kapja.
    // Korábban itt fix 420 képpont állt, akármekkora az
    // ablak — a 3. fül 12 bélyegképes csempéje (3×4, ≈450
    // px) ebbe soha nem fért bele, ezért lett a görgetés az
    // alapállapot, és ezért lógott rá a gombsor a
    // csempékre. A szülő `Layout.fillHeight: true`, tehát a
    // hely rendelkezésre áll.
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    width: 280
    x: editorPanel.hostViewer.editorDrawerOffset
    //: #3741: a fókuszban lévő fél képéé
    imageAspect: editorPanel.hostPhotoArea.fokuszKep.paintedHeight > 0
                 ? editorPanel.hostPhotoArea.fokuszKep.paintedWidth
                   / editorPanel.hostPhotoArea.fokuszKep.paintedHeight
                 : 4 / 3
    // #4549: a vágó felirata a valódi, EXIF szerint
    // megjelenített képméretből és az overlay kijelöléséből
    // áll össze; a `sourceSize` csak betöltési plafon lenne.
    imagePixelWidth: editorPanel.hostViewer.valodiSzelesseg
    imagePixelHeight: editorPanel.hostViewer.photosModel
        ? (editorPanel.hostViewer.photosModel.revision,
           editorPanel.hostViewer.photosModel.pixelHeightAt(editorPanel.hostViewer.aktivSor))
        : 0
    cropRect: editorPanel.hostCropOverlay.cropRect
    cropHasSelection: editorPanel.hostCropOverlay.hasSelection
    // Visszavonás/Újra — a controller undo-verméből (#59).
    // #465: a KÉSZ feliratot a controller adja
    // (`edit_action_names` névtár), hogy a lánc minden
    // eleme néven nevezhető legyen — a korábbi, itteni
    // `switch` csak egy tucat effektet ismert, a többinél a
    // nyers ini-kulcs került a gombra.
    // #305: null-őr
    undoAvailable: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.canUndo : false
    undoLabel: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.undoLabel : qsTr("Undo")
    redoAvailable: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.canRedo : false
    redoLabel: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.redoLabel : qsTr("Redo")
    // Finomhangolás (#20): a mentett értékek a kontrollerből —
    // a syncFinetuneSliders() ezekből tölti a csúszkákat
    fillLight: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.fillLight : 0
    highlights: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.highlights : 0
    shadows: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.shadows : 0
    colorTemp: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.colorTemp : 0
    // GPU élő-előnézet (#22): amíg a lánc GPU-alkalmas ÉS
    // van RHI, a húzás a LUT-only gyors utat hívja (a
    // `GpuPointFilterPreview` réteg jelenik meg a
    // `editorPanel.hostPhotoArea.fokuszKep` — kettős nézetben a kijelölt
    // fél — fölött, #3755) — máskülönben (nincs GPU, vagy
    // a lánc nem GPU-alkalmas) a rendes, teljes
    // CPU-előnézet fut, változatlanul.
    onFinetunePreview: (f, h, s, t) => {
        // #551: a Derítőfény MÉRT modellje a pixel
        // VILÁGOSSÁGÁTÓL függ, tehát nem csatornánkénti
        // LUT — a GPU pontonkénti útja csak f === 0 esetén
        // adja pontosan ugyanazt a képet, mint a CPU.
        editorPanel.hostViewer.gpuFinetuneActive = true
        editorPanel.hostViewer.gpuFinetunePointSafe = (f === 0)
        if (editorPanel.hostViewer.gpuFinetuneEligible && f === 0)
            editController.previewFinetuneGpu(f, h, s, t)
        else
            editController.previewFinetune(f, h, s, t)
    }
    onFinetuneCommit: (f, h, s, t) => {
        // a húzás végén MINDIG a normál CPU-út menti — az
        // igazságforrás sosem a GPU-réteg (ld. #22 jegy)
        editorPanel.hostViewer.gpuFinetuneActive = false
        editorPanel.hostViewer.gpuFinetunePointSafe = true
        editController.setFinetune(f, h, s, t)
    }
    onEffectRequested: (name) => {
        editorPanel.hostViewer.forceFitForFilter(name)
        editController.applyEffect(name)
    }
    // #551: a szín-varázspálca a finetune2 p4 mezőjét írja
    onColorWandRequested: editController.applyColorWand()
    onToolActivated: function(tool) {
        // crop/tilt/retouch/text helyi mód (overlay/
        // csúszka/kattintás-puffer); a többi azonnali
        // ini-művelet az EditControlleren át
        if (tool === "tilt") {
            // eszköz-nyitáskor a csúszka a MENTETT
            // tilt-értékről induljon, ne 0-ról (#131)
            if (editorPanel.tiltActive) {
                // #3234: a Mégse ehhez az értékhez tér vissza
                editorPanel.hostViewer.tiltErtekNyitaskor =
                    editController.tiltParam
                editorPanel.hostViewer.syncTiltSlider()
            }
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
    // (IDS_CONFIRM_UNDO_RETOUCH / IDS_CONFIRM_UNDO_REDEYE) —
    // a két mondat között sortöréssel, ahogy ott (#3573).
    onUndoRequested: {
        var action = editController.undoAction
        if (action === "retouch")
            editorPanel.hostUndoDataLossDialogLoader.ensure().askFor("retouch", qsTr(
                "Retouch fixes cannot be recovered with redo.\n"
                + "Are you sure you want to undo?"))
        else if (action === "redeye")
            editorPanel.hostUndoDataLossDialogLoader.ensure().askFor("redeye", qsTr(
                "Redeye fixes cannot be recovered with redo.\n"
                + "Are you sure you want to undo?"))
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
            editorPanel.hostCropOverlay.swapSelectionOrientation()
    }
    // arány-választás/Forgatás: a meglévő kijelölés kövesse,
    // és a #448-as javaslatok is a KIVÁLASZTOTT arányban
    // szülessenek (egyetlen kezelő — a QML-ben nem lehet
    // két azonos nevű jel-kezelő ugyanazon az objektumon)
    onCurrentAspectChanged: {
        if (editorPanel.hostCropOverlay.hasSelection
            && editorPanel.currentAspect > 0)
            editorPanel.hostCropOverlay.applyAspect(editorPanel.currentAspect)
        if (editorPanel.hostEditCtl)
            editorPanel.hostEditCtl.setCropAspect(editorPanel.currentAspect)
    }
    onCropPreviewHold: (held) => editorPanel.hostCropOverlay.previewHold = held
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
        editorPanel.hostCropOverlay.resetSelection()
        if (editorPanel.hostEditCtl && editorPanel.hostEditCtl.hasCrop)
            editController.clearCrop()
    }
    // #1528: a gomb tiltott, ha nincs mit elvetni — se
    // húzott kijelölés, se mentett vágás.
    cropResetEnabled: editorPanel.hostCropOverlay.hasSelection
        || (editorPanel.hostEditCtl ? editorPanel.hostEditCtl.hasCrop : false)
    // #448: a három automatikus javaslat — a választott
    // téglalap a KIJELÖLÉSBE kerül (nem alkalmazódik
    // azonnal), hogy a felhasználó még igazíthasson rajta,
    // és az Alkalmaz/Mégse útja változatlan maradjon.
    cropSuggestions: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.cropSuggestions : []
    onCropSuggestionChosen: (x, y, w, h) =>
        editorPanel.hostCropOverlay.loadSelection(
            { "x": x, "y": y, "width": w, "height": h })
    onCropApplyRequested: editorPanel.hostViewer.applyCrop(false)
    onCropCancelRequested: {
        editorPanel.hostCropOverlay.resetSelection()
        editorPanel.cropActive = false
    }
    // #148/#445: a retusálás pufferének mérete/az Alkalmaz-
    // gomb engedélyezettsége, a félbehagyott folt ("Refining…")
    // és a patch-enkénti Undo/Redo/ecsetméret a kontrollerből
    retouchRegionCount: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.retouchPendingCount : 0
    retouchPatchPending: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.retouchPatchPending : false
    canUndoPatch: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.canUndoPatch : false
    canRedoPatch: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.canRedoPatch : false
    brushSize: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.brushSize : 20
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
    redeyeRegionCount: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.redeyeRegionCount : 0
    canUndoRedeyeRegion: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.canUndoRedeyeRegion : false
    redeyeResetAvailable: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.redeyeResetAvailable : false
    canReapplyRedeyeAuto: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.canReapplyRedeyeAuto : false
    redeyeAutoReset: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.redeyeAutoReset : false
    redeyeFoundCount: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.redeyeFoundCount : -1
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
    textPlacementPending: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.textHasPlacement : false
    // #450: "Copy Caption" gomb — a kép model.revision-re
    // is frissülő mentett feliratát tükrözi (a captionField
    // mintáját követve fent). #4525: kettős nézetben a
    // kijelölt oldal feliratát mutatja.
    captionText: editorPanel.hostViewer.photosModel
        ? (editorPanel.hostViewer.photosModel.revision,
           editorPanel.hostViewer.photosModel.captionAt(editorPanel.hostViewer._kijeloltSort()))
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
        editorPanel.hostCopyCaptionConfirmLoader.ensure().ask(
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
    onTextOverlayVisibleEdited: (visible) =>
        editController.setTextOverlayVisible(visible)
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
