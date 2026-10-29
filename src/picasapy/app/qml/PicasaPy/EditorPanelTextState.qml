import QtQml

// A képre helyezett felirat szöveg- és stílusállapota.
QtObject {
    required property var editorPanel

    property string textDraftContent: ""
    property bool textPlacementPending: false
    property string captionText: ""
    property bool hasTextOverlay: false
    property bool textOverlayVisible: true

    property string textFillColor: "#ffffff"
    property string textOutlineColor: "#000000"
    property real textOutlineThickness: 0
    property bool textFillEnabled: true
    property real textOpacity: 1

    property var fontFamilyCatalogue: []
    readonly property var fontFamilyKeys:
        editorPanel.fontFamilyCatalogue.map(function(f) { return f.key })
    readonly property var fontFamilyLabels:
        editorPanel.fontFamilyCatalogue.map(function(f) { return f.label })
    property string textFontFamily: ""
    property int textFontSize: 12
    property var fontSizeChoices: []
    property bool textBold: false
    property bool textItalic: false
    property bool textUnderline: false
    property string textAlign: "left"
}
