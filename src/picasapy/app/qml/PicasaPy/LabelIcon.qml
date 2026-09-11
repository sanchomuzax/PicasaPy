import QtQuick

// Rajzolt CÍMKE-ikon (#1132): szürke címke.
//
// Az eredetiben `icons/label` (15 × 12) — a címke-bejegyzés típusa. Nálunk
// eddig a mappa aranyát használta a címke-panel, tehát a címke ugyanúgy
// nézett ki, mint egy mappa.
Item {
    id: icon
    //: a MÉRT arány: 15 × 12
    property int size: 13
    width: size; height: Math.round(size * 12 / 15)

    Rectangle {   // a címke teste
        anchors.fill: parent
        radius: 1
        color: Theme.labelGray
        border.color: Theme.labelGrayBorder; border.width: 1
    }
    Rectangle {   // a fűzőlyuk
        x: Math.round(icon.width * 0.18)
        y: Math.round(icon.height * 0.3)
        width: Math.max(2, Math.round(icon.width * 0.18))
        height: width
        radius: width / 2
        color: Theme.labelGrayBorder
    }
}
