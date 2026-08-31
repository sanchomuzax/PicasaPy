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
//
// #1720 — HALASZTOTT PÉLDÁNYOSÍTÁS. A menü NEM épül fel induláskor, csak az
// első jobbklikkre. A fán ma **40** ilyen terület van, és mindegyik menüje
// ~123 QObjectet vitt: mérve **4920 objektum, a teljes indulási fa 23,9%-a**
// — a legnagyobb egyetlen tétel. A `Component` maga nem példányosít; a
// `createObject(area)` ugyanazt a szülőt (és ezzel ugyanazt a
// megjelenítési szülőt) adja a menünek, mint a korábbi beágyazott
// deklaráció, tehát a `popup()` viselkedése változatlan.
MouseArea {
    id: area

    //: a mező, amire a menü vonatkozik (alapból a szülő)
    property var field: parent

    //: az első jobbklikkre létrejövő menü (addig `null`) — az őr-teszt
    //: ezen méri, hogy induláskor tényleg nincs példány
    property var contextMenu: null

    anchors.fill: parent
    acceptedButtons: Qt.RightButton
    // a kurzor-alak a mezőé marad (a MouseArea alapból nem állítja)
    onClicked: {
        if (area.contextMenu === null)
            area.contextMenu = menuComponent.createObject(area)
        area.contextMenu.popupFor(area.field)
    }

    Component {
        id: menuComponent
        TextFieldContextMenu { }
    }
}
