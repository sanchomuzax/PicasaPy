import QtQuick

// Rajzolt PROJEKT-ikon (#1132): lila könyv csillaggal.
//
// Az eredetiben `icons/projects` (15 × 16) — a Projektek gyűjtemény
// mappáinak típusa. Eddig ezek is a mappa-ikont kapták, tehát a felületen
// nem lehetett megkülönböztetni a projekt-mappát a lemezes mappától.
//
// ⚠️ NYITOTT (a jegyben is): az eredetiben `icons/movie` és `icons/collage`
// is létezik — nem tudjuk, hogy a Projektek alatt TÍPUSONKÉNT más ikon jár-e
// (film-mappa → filmszalag, kollázs-mappa → kollázs), vagy mindegyikre az
// egységes `projects`. Amíg ez nem dőlt el, EGYSÉGES ikont adunk: a
// típusonkénti szétosztás találgatás lenne.
Item {
    id: icon
    //: a MÉRT arány: 15 × 16
    property int size: 13
    width: size; height: Math.round(size * 16 / 15)

    Rectangle {
        anchors.fill: parent
        radius: 1
        color: Theme.projectPurple
        border.color: Theme.projectPurpleBorder; border.width: 1
    }
    Rectangle {
        x: 0; y: 0
        width: Math.max(2, icon.width * 0.25); height: icon.height
        color: Theme.projectPurpleBorder
    }
    Text {
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: Math.round(icon.width * 0.12)
        text: "★"
        color: Theme.starYellow
        font.pixelSize: Math.round(icon.size * 0.72)
    }
}
