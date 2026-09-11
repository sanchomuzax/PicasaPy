import QtQuick

// Rajzolt ALBUM-ikon (#1132): narancs könyv.
//
// Az eredetiben `icons/album` (16 × 18) — a rendes (virtuális) album
// bejegyzés-típusát kódolja. A méret és a jelentés mért, a rajz a miénk
// (`docs/specs/design-guide.md`); az eredeti PNG-t tilos a repóba másolni.
Item {
    id: icon
    //: a MÉRT arány: 16 × 18, tehát a magasság a szélesség 1,125-szöröse
    property int size: 13
    width: size; height: Math.round(size * 1.125)

    Rectangle {   // könyvtest
        anchors.fill: parent
        radius: 1
        color: Theme.albumOrange
        border.color: Theme.albumOrangeBorder; border.width: 1
    }
    Rectangle {   // gerinc
        x: 0; y: 0
        width: Math.max(2, icon.width * 0.25); height: icon.height
        color: Theme.albumOrangeBorder
    }
}
