import QtQuick

// Rajzolt sárga mappa-ikon (emoji helyett — platformfüggetlen).
Item {
    id: icon
    property int size: 14
    width: size; height: size * 0.8

    // dizajnkézikönyv: „mappa arany" #ebcc8f — lapos, tömör forma
    Rectangle {   // fül
        x: 0; y: 0
        width: icon.size * 0.45; height: icon.height * 0.3
        radius: 1
        color: Theme.folderGold
        border.color: "#d9b571"; border.width: 1
    }
    Rectangle {   // test
        x: 0; y: icon.height * 0.18
        width: icon.size; height: icon.height * 0.82
        radius: 2
        color: Theme.folderGold
        border.color: "#d9b571"; border.width: 1
    }
}
