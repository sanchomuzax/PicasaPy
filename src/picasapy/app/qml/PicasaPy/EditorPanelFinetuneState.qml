import QtQml

// A Finomhangolás fül csúszkáinak állapota.
QtObject {
    required property var editorPanel

    property real fillLight: 0
    property real highlights: 0
    property real shadows: 0
    property real colorTemp: 0
    property bool suppressFinetune: false
}
