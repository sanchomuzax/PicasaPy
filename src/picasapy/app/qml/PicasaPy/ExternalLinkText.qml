import QtQuick

// Külső hivatkozás szövegként (#6402): kattintásra az alapértelmezett
// böngészőben nyílik. A címet a hívó adja meg (`url`).
Text {
    id: root
    property string url: ""
    color: Theme.linkBlue
    font.pixelSize: Theme.fontSize
    font.underline: true
    Accessible.role: Accessible.Link
    Accessible.name: root.text

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: Qt.openUrlExternally(root.url)
    }
}
