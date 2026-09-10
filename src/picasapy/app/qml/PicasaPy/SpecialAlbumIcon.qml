import QtQuick

// Rajzolt KÜLÖNLEGES ALBUM ikon (#1132): zöld könyv csillaggal.
//
// Az eredetiben `icons/special_album` (16 × 18) — a Csillagozott képek és a
// Legutóbb frissítve sorok típusa. A csillag maga is az erőforrás része,
// ezért itt is rajta van, nem külön glif a sorban.
Item {
    id: icon
    property int size: 13
    width: size; height: Math.round(size * 1.125)

    Rectangle {
        anchors.fill: parent
        radius: 1
        color: Theme.specialAlbumGreen
        border.color: Theme.specialAlbumGreenBorder; border.width: 1
    }
    Rectangle {
        x: 0; y: 0
        width: Math.max(2, icon.width * 0.25); height: icon.height
        color: Theme.specialAlbumGreenBorder
    }
    Text {
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: Math.round(icon.width * 0.12)
        text: "★"
        color: Theme.starYellow
        font.pixelSize: Math.round(icon.size * 0.72)
    }
}
