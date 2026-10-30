import QtQuick

// A néző billentyűeseményei külön objektumban maradnak; a PhotoViewer
// Keys.forwardTo kapcsolata továbbra is a fókuszált gyökérből irányítja őket.
Item {
    id: keyboard
    property var hostViewer: null
    width: 0
    height: 0

    function handleEscape() {
        var editorPanel = keyboard.hostViewer.editorPanel
        if (editorPanel.paramPanelActive)
            editorPanel.cancelParamPanel()
        else if (editorPanel.retouchActive && editorPanel.retouchPatchPending)
            editController.cancelRetouchPatch()
        else if (editorPanel.cropActive)
            editorPanel.cropCancelRequested()
        else if (keyboard.hostViewer.facesEditMode)
            keyboard.hostViewer.cancelManualFaceAdd()
        else
            keyboard.hostViewer.kerBezaras()
    }

    Keys.onEscapePressed: {
        if (!keyboard.hostViewer.textEntryHasFocus)
            keyboard.hostViewer.handleEscape()
    }
    Keys.onRightPressed: {
        if (!keyboard.hostViewer.textEntryHasFocus)
            keyboard.hostViewer.next()
    }
    Keys.onReturnPressed: keyboard.hostViewer.handleReturnPressed()
    Keys.onLeftPressed: {
        if (!keyboard.hostViewer.textEntryHasFocus)
            keyboard.hostViewer.previous()
    }
    Keys.onSpacePressed: {
        if (keyboard.hostViewer.textEntryHasFocus)
            return
        if (keyboard.hostViewer.isCurrentVideo
                && keyboard.hostViewer.videoLoader.item)
            keyboard.hostViewer.videoLoader.item.togglePlayback()
    }
    Keys.onPressed: function(event) {
        if (keyboard.hostViewer.textEntryHasFocus)
            return
        if (event.key === Qt.Key_F9
                && event.modifiers === Qt.ControlModifier) {
            if (!event.isAutoRepeat)
                keyboard.hostViewer.startCtrlF9AutoAdvance()
            event.accepted = true
        } else if (event.key === Qt.Key_F
                   && event.modifiers === Qt.NoModifier) {
            keyboard.hostViewer.toggleFaces()
            event.accepted = true
        } else if (event.key === Qt.Key_F
                   && event.modifiers === Qt.ShiftModifier) {
            keyboard.hostViewer.toggleFacesEdit()
            event.accepted = true
        } else if (event.key === Qt.Key_Delete
                   && event.modifiers === Qt.ControlModifier) {
            if (keyboard.hostViewer._aktivUt().length > 0)
                keyboard.hostViewer.deleteRequested()
            event.accepted = true
        }
    }
}
