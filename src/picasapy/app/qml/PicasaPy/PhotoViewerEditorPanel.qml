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
    // #7383: a csúszkák NEM a mentett értékekre állnak: a Hangolás fül és az
    // 1. fül Derítőfénye mindig alaphelyzetben indul (syncFinetuneSliders),
    // a kép a láncot mutatja. A fülváltás lezárja a Hangolás-látogatást.
    onFinetuneVisitEnded: if (editorPanel.hostEditCtl) editorPanel.hostEditCtl.closeFinetuneVisit()
    // #7369: a Gyakori javítások Derítőfénye a `fill` réteg, nem a `finetune2`
    onFixesFillPreview: (v) => editController.previewFixesFill(v)
    onFixesFillCommit: (v) => editController.setFixesFill(v)
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
        if (typeof controller !== "undefined" && controller && typeof controller.setViewerInfoShort === "function")
            controller.setViewerInfoShort(true)
    }
    // #551: a szín-varázspálca a finetune2 p4 mezőjét írja
    onColorWandRequested: editController.applyColorWand()
    onToolActivated: function(tool) {
        // crop/tilt/retouch/text helyi mód (overlay/
        // csúszka/kattintás-puffer); a többi azonnali
        // ini-művelet az EditControlleren át
        if (tool === "tilt") {
            // #7393: eszköz-nyitáskor a csúszka MINDIG 0-ról
            // indul (a #131 a mentett értékről indította): a
            // kép a már alkalmazott lánc eredménye, az Alkalmaz
            // új tilt tagot fűz hozzá. A Mégse az előnézetet
            // veti el, a mentett láncot nem érinti.
            if (editorPanel.tiltActive)
                editorPanel.hostViewer.syncTiltSlider()
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
        if (typeof controller !== "undefined" && controller && typeof controller.setViewerInfoShort === "function")
            controller.setViewerInfoShort(false)
    }
    onRedoRequested: {
        editController.redo()
        if (typeof controller !== "undefined" && controller && typeof controller.setViewerInfoShort === "function")
            controller.setViewerInfoShort(false)
    }
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
    brushSize: editorPanel.hostEditCtl ? editorPanel.hostEditCtl.brushSize : 50
    onBrushSizeEdited: (value) => editController.setBrushSize(value)
    onRetouchUndoPatchRequested: editController.undoPatch()
    onRetouchRedoPatchRequested: editController.redoPatch()
    onRetouchResetRequested: editController.resetPatches()
    onRetouchApplyRequested: {
        editController.applyRetouch()
        editorPanel.retouchActive = false
    }
    onRetouchCancelRequested: {
        if (editorPanel.retouchPatchPending) {
            editController.cancelRetouchPatch()
        } else {
            editorPanel.retouchActive = false
        }
    }
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
    textCleared: editorPanel.hostEditCtl
        ? editorPanel.hostEditCtl.textCleared : false
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
    // #7407: a Clear All csak az eszközön belül veszi le a szöveget a képről,
    // az eszköz nyitva marad; az Apply véglegesíti, a Cancel visszahozza
    onTextRemoveAllRequested: {
        editController.clearText()
        editorPanel.textDraftContent = ""
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
    // A mentett Kiegyenesítés után az eredeti Picasa előbb ezt az Info
    // ablakot mutatja, és csak az OK után lép be a Vörösszem eszközbe.
    // Az Esc/kívül kattintás elvetése NINCS lemérve: az Esc bezárja az ablakot
    // és a panel nem nyílik meg; a kívül kattintás nem zárja (modális ablak).
    onRedeyeStraightenInfoRequested: redeyeStraightenInfoDialog.open()
    Dialog {
        id: redeyeStraightenInfoDialog
        objectName: "redeyeStraightenInfoDialog"
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape
        // A `job-837 __22` méréséből: a kliens-terület 320 x 132 px, a szöveg
        // 10 px-re a címsávtól, az OK gomb 48 x 24 px és vízszintesen középen.
        implicitWidth: 320
        topPadding: 10
        bottomPadding: 0
        leftPadding: 13
        //: picasapy-origin: picasa
        //: picasapy-origin-key: stringres:ytApp::InfoTitle
        title: qsTr("Info")

        onOpened: redeyeStraightenInfoOkButton.forceActiveFocus()
        onAccepted: editorPanel.redeyeActive = true

        footer: DialogButtonBox {
            objectName: "redeyeStraightenInfoButtonBox"
            alignment: Qt.AlignHCenter
            padding: 0
            topPadding: 9
            bottomPadding: 8

            Button {
                id: redeyeStraightenInfoOkButton
                objectName: "redeyeStraightenInfoOkButton"
                implicitWidth: 48
                implicitHeight: 24
                font.pixelSize: Theme.fontSize - 1
                //: picasapy-origin: picasa
                //: picasapy-origin-key: stringres:ContactManagerDlg::OK
                text: qsTr("OK")
                Keys.priority: Keys.BeforeItem
                Keys.onReturnPressed: function(event) {
                    redeyeStraightenInfoDialog.accept()
                    event.accepted = true
                }
                Keys.onEnterPressed: function(event) {
                    redeyeStraightenInfoDialog.accept()
                    event.accepted = true
                }
                onClicked: redeyeStraightenInfoDialog.accept()
            }
        }

        contentItem: Row {
            spacing: 11
            Image {
                objectName: "redeyeStraightenInfoIcon"
                anchors.verticalCenter: parent.verticalCenter
                source: "icons/dialog-info.svg"
                sourceSize: Qt.size(32, 32)
            }
            Label {
                objectName: "redeyeStraightenInfoText"
                width: 252
                anchors.verticalCenter: parent.verticalCenter
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize - 1
                //: picasapy-origin: picasa
                //: picasapy-origin-key: stringres:IDS_WARN_REDEYE_ACCURACY
                text: qsTr("This image's orientation has been modified by the Straighten tool, "
                           + "which can cause inaccuracies when selecting red eye  rectangles.\n"
                           + "If your redeye fixes appear to be misaligned (or non-existent), try "
                           + "undoing the Straighten fix, then reapply red eye fixes, and "
                           + "Straighten again if necessary.")
            }
        }
    }
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
