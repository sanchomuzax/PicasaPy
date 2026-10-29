import QtQml

// Az effekt-csempék és a csúszkás effekt-alpanel állapota.
QtObject {
    required property var editorPanel
    required property var hostEditController

    // A Shift állapota a kilenc kétutas effektcsempén élő vezérlőérték.
    property bool shiftMasodlagos: hostEditController
        && hostEditController.shiftAktiv !== undefined
        ? hostEditController.shiftAktiv
        : false

    property bool paramPanelActive: false
    property bool paramPanelSuspended: false
    readonly property bool paramPanelContentBlurred:
        paramPanelSuspended && !editorPanel.tiltActive
    property string paramEffectName: ""
    property var paramEffectParams: []
    property var paramEffectValues: []
    property string paramEffectLabel: ""
    readonly property string paramEffectTitle:
        paramEffectLabel !== "" ? paramEffectLabel : paramEffectName

    readonly property bool legacyEffectsPresent: {
        if (!editorPanel.hasEffectController()) return false
        var inChain = hostEditController.legacyEffectsInChain
        return inChain !== undefined && inChain !== null && inChain.length > 0
    }

    readonly property string effectThumbPhotoId: {
        if (!editorPanel.hasEffectController()) return ""
        var src = hostEditController.previewSource
        var prefix = "image://editpreview/"
        if (!src || src.indexOf(prefix) !== 0) return ""
        var rest = src.substring(prefix.length)
        var q = rest.indexOf("?")
        return q >= 0 ? rest.substring(0, q) : rest
    }

    readonly property var effectChainCounts: {
        if (!editorPanel.hasEffectController()) return ({})
        var counts = hostEditController.effectChainCounts
        return (counts === undefined || counts === null) ? ({}) : counts
    }

    readonly property var oneClickEffects: {
        if (!editorPanel.hasEffectController()) return []
        var lista = hostEditController.oneClickEffects
        return (lista === undefined || lista === null) ? [] : lista
    }
}
