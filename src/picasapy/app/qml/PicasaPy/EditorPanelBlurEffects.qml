import QtQuick

// Az effekt-alpanel alatt elmosott fület és Visszavonás/Újra sort rajzolja.
Item {
    id: blurEffects
    required property var editorPanel
    required property var tabs
    required property var tabArea
    required property var undoRow

    anchors.fill: parent

    ShaderEffectSource {
        id: paramTabBlur
        objectName: "paramPanelTabBlur"
        x: blurEffects.tabs.x + blurEffects.tabArea.x
        y: blurEffects.tabs.y + blurEffects.tabArea.y
        width: blurEffects.tabArea.width
        height: blurEffects.tabArea.height
        sourceItem: blurEffects.tabArea
        sourceRect: Qt.rect(0, 0, blurEffects.tabArea.width,
                            blurEffects.tabArea.height)
        textureSize: Qt.size(
            Math.max(1, Math.round(blurEffects.tabArea.width / 4)),
            Math.max(1, Math.round(blurEffects.tabArea.height / 4)))
        live: blurEffects.editorPanel.paramPanelContentBlurred
        smooth: true
        hideSource: blurEffects.editorPanel.paramPanelContentBlurred
        visible: blurEffects.editorPanel.paramPanelContentBlurred
        enabled: false
        z: 1
    }

    ShaderEffectSource {
        id: paramUndoBlur
        objectName: "paramPanelUndoBlur"
        x: blurEffects.undoRow.x
        y: blurEffects.undoRow.y
        width: blurEffects.undoRow.width
        height: blurEffects.undoRow.height
        sourceItem: blurEffects.undoRow
        sourceRect: Qt.rect(0, 0, blurEffects.undoRow.width,
                            blurEffects.undoRow.height)
        textureSize: Qt.size(
            Math.max(1, Math.round(blurEffects.undoRow.width / 4)),
            Math.max(1, Math.round(blurEffects.undoRow.height / 4)))
        live: blurEffects.editorPanel.paramPanelContentBlurred
        smooth: true
        hideSource: blurEffects.editorPanel.paramPanelContentBlurred
        visible: blurEffects.editorPanel.paramPanelContentBlurred
        enabled: false
        z: 1
    }
}
