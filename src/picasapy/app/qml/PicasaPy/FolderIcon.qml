import QtQuick

// Rajzolt mappa-ikon (emoji helyett — platformfüggetlen).
//
// #1132: az eredeti lemezes-mappa ikonja (`icons/folder`, 17 × 15) **KÉK**,
// nem arany — a tulajdonos „sárga" észrevétele a MI eltérésünk volt. A méret
// és a jelentés mért, a rajz a miénk (`docs/specs/design-guide.md`).
Item {
    id: icon
    property int size: 14
    width: size; height: size * 0.8

    // dizajnkézikönyv: „mappa arany" #ebcc8f — lapos, tömör forma
    Rectangle {   // fül
        x: 0; y: 0
        width: icon.size * 0.45; height: icon.height * 0.3
        radius: 1
        color: Theme.folderBlue
        border.color: Theme.folderBlueBorder; border.width: 1
    }
    Rectangle {   // test
        x: 0; y: icon.height * 0.18
        width: icon.size; height: icon.height * 0.82
        radius: 2
        color: Theme.folderBlue
        border.color: Theme.folderBlueBorder; border.width: 1
    }
}
