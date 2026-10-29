import QtQml

// A szerkesztő eszközeinek kapcsoló- és műveletállapota.
QtObject {
    required property var editorPanel

    property bool cropActive: false
    property bool tiltActive: false
    property bool redeyeActive: false
    property bool retouchActive: false
    property bool textActive: false
    property int retouchRegionCount: 0

    property bool retouchPatchPending: false
    property bool canUndoPatch: false
    property bool canRedoPatch: false
    property int brushSize: 20

    property int redeyeRegionCount: 0
    property bool canUndoRedeyeRegion: false
    property bool redeyeResetAvailable: false
    property bool canReapplyRedeyeAuto: false
    property bool redeyeAutoReset: false
    property int redeyeFoundCount: -1
    property bool redeyeHideOutlines: false

    readonly property bool modeToolActive:
        cropActive || retouchActive || textActive || redeyeActive

    property bool enhanceEnabled: true
    property bool autolightEnabled: true
    property bool autocolorEnabled: true

    property bool undoAvailable: false
    property bool redoAvailable: false
    property bool neutralPickerActive: false
    property string neutralColor: ""
    property int effectColorPickerTarget: -1
    property bool straightenActive: false
}
