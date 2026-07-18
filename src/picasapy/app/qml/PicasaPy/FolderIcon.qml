import QtQuick

// Rajzolt sárga mappa-ikon (emoji helyett — platformfüggetlen).
Item {
    id: icon
    property int size: 14
    width: size; height: size * 0.8

    Rectangle {   // fül
        x: 0; y: 0
        width: icon.size * 0.45; height: icon.height * 0.3
        radius: 1
        color: "#e8b64c"
        border.color: "#c69a3a"; border.width: 1
    }
    Rectangle {   // test
        x: 0; y: icon.height * 0.18
        width: icon.size; height: icon.height * 0.82
        radius: 2
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#f7d47c" }
            GradientStop { position: 1.0; color: "#e8b64c" }
        }
        border.color: "#c69a3a"; border.width: 1
    }
}
