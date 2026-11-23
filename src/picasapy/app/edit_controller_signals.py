"""A QML-jelzések sima Python-mixinben."""

from PySide6.QtCore import Signal


_TOOL_PROPERTY_NAMES = (
    "canUndo",
    "canRedo",
    "undoAction",
    "redoAction",
    "undoLabel",
    "redoLabel",
    "textDraft",
    "textSelectedIndex",
    "textOverlayItems",
    "hasTextOverlay",
    "textOverlayVisible",
    "textFillColor",
    "textOutlineColor",
    "textOutlineThickness",
    "textFillEnabled",
    "textOpacity",
    "textFontFamily",
    "textFontSize",
    "textBold",
    "textItalic",
    "textUnderline",
    "textAlign",
    "hasRetouch",
    "brushSize",
    "retouchBrushRadiusRatio",
    "chainValue",
    "tiltParam",
    "fillLight",
    "fixesFillLight",
    "highlights",
    "shadows",
    "colorTemp",
    "neutralColor",
    "hasFinetune",
    "hasSavedRedeye",
    "hasCrop",
    "cropSelection",
    "enhanceEnabled",
    "autolightEnabled",
    "autocolorEnabled",
)


class EditControllerSignalsMixin:
    """A végső QObject-vezérlő által örökölt jelzések."""

    revisionChanged = Signal()

    toolsChanged = Signal()

    # A hálózati állapot betöltése nem ébresztheti fel a szerkesztő összes
    # kötését. Ezek a mezőszintű értesítők csak a ténylegesen módosult
    # tulajdonságokhoz futnak; a régi toolsChanged-jel továbbra is a
    # hagyományos szerkesztési műveletek gyűjtőjele.
    toolStateChanges = Signal("QStringList")
    editSessionStarted = Signal()
    canUndoChanged = Signal()
    canRedoChanged = Signal()
    undoActionChanged = Signal()
    redoActionChanged = Signal()
    undoLabelChanged = Signal()
    redoLabelChanged = Signal()
    textDraftChanged = Signal()
    textSelectedIndexChanged = Signal()
    textOverlayItemsChanged = Signal()
    hasTextOverlayChanged = Signal()
    textOverlayVisibleChanged = Signal()
    textFillColorChanged = Signal()
    textOutlineColorChanged = Signal()
    textOutlineThicknessChanged = Signal()
    textFillEnabledChanged = Signal()
    textOpacityChanged = Signal()
    textFontFamilyChanged = Signal()
    textFontSizeChanged = Signal()
    textBoldChanged = Signal()
    textItalicChanged = Signal()
    textUnderlineChanged = Signal()
    textAlignChanged = Signal()
    hasRetouchChanged = Signal()
    brushSizeChanged = Signal()
    retouchBrushRadiusRatioChanged = Signal()
    chainValueChanged = Signal()
    tiltParamChanged = Signal()
    fillLightChanged = Signal()
    fixesFillLightChanged = Signal()
    highlightsChanged = Signal()
    shadowsChanged = Signal()
    colorTempChanged = Signal()
    neutralColorChanged = Signal()
    hasFinetuneChanged = Signal()
    hasSavedRedeyeChanged = Signal()
    hasCropChanged = Signal()
    cropSelectionChanged = Signal()
    enhanceEnabledChanged = Signal()
    autolightEnabledChanged = Signal()
    autocolorEnabledChanged = Signal()

    previewRevisionChanged = Signal()
    cameraSummaryChanged = Signal()
    cropSuggestionsChanged = Signal()

    textFontCatalogueChanged = Signal()

    pickerRecentColorsChanged = Signal()

    gpuRevisionChanged = Signal()

    shiftAktivChanged = Signal()

    editSaveReadOnly = Signal()

    editSaveFailed = Signal(str)

    editChainRejected = Signal(str)

    _previewRendered = Signal()

    chainSaved = Signal(str, str)

    def _tool_property_values(self) -> dict[str, object]:
        """Pillanatkép a QML által figyelt szerkesztőmezőkről."""
        return {name: getattr(self, name) for name in _TOOL_PROPERTY_NAMES}

    def _emit_all_tool_property_changes(self) -> None:
        """A régi gyűjtőjel kompatibilitása a mezőnkénti notify jelekkel."""
        for name in _TOOL_PROPERTY_NAMES:
            getattr(self, f"{name}Changed").emit()

    def _emit_changed_tool_properties(
        self, previous: dict[str, object]
    ) -> list[str]:
        """Csak az eltérő értékekhez jelezzen, hálózati betöltés után."""
        changed = [
            name
            for name in _TOOL_PROPERTY_NAMES
            if previous.get(name) != getattr(self, name)
        ]
        if not changed:
            return changed
        for name in changed:
            getattr(self, f"{name}Changed").emit()
        self.toolStateChanges.emit(changed)
        return changed

