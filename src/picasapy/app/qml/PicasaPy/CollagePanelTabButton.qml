import QtQuick
import QtQuick.Controls

// Egy fül a Kollázs-panel fülsávjában (#945).
//
// A rajz a `picasa-gomb-es-menu-rendszer.md` állapotszíneit követi: a
// kiválasztott fül a laptartalommal AZONOS hátteret kap és nincs alsó
// szegélye, tehát vizuálisan összeér a lappal; a nem választott fül
// visszahúzódik.
AbstractButton {
    id: control

    property bool selected: control.checked

    contentItem: Text {
        text: control.text
        font.pixelSize: Theme.fontSize
        font.bold: control.selected
        color: control.enabled ? Theme.ink : Theme.textGray
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        color: control.selected ? Theme.contentPanel : Theme.chromeBg
        border.width: 1
        border.color: Theme.chromeBorder
        // a kiválasztott fül alja „kinyílik" a lap felé: a szegélyt egy
        // azonos színű csík takarja el
        Rectangle {
            visible: control.selected
            color: Theme.contentPanel
            height: 1
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 1
            anchors.rightMargin: 1
        }
    }
}
