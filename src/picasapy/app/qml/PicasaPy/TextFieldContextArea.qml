import QtQuick

// Jobbklikk-terület egy szövegmező fölé — a `TextFieldContextMenu`-t
// (Picasa `Address` menüosztály) nyitja meg (#422).
//
// Használat a mezőn BELÜL, egyetlen sorban:
//
//     TextField {
//         …
//         TextFieldContextArea {}
//     }
//
// A `field` alapból a szülő mező, tehát külön be sem kell kötni. Csak a
// JOBB gombot fogadja el, ezért a bal kattintás (kurzor-elhelyezés,
// kijelölés, húzás) változatlanul a mezőé marad — a beírás élményén nem
// változtat semmit.
MouseArea {
    id: area

    //: a mező, amire a menü vonatkozik (alapból a szülő)
    property var field: parent

    anchors.fill: parent
    acceptedButtons: Qt.RightButton
    // a kurzor-alak a mezőé marad (a MouseArea alapból nem állítja)
    onClicked: contextMenu.popupFor(area.field)

    TextFieldContextMenu { id: contextMenu }
}
