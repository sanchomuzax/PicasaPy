import QtQuick

// Az Alkalmaz/Mégse gomb KÖR ALAKÚ ikonja — KÖZÖS komponens (#710).
//
// Az eredetiben ez két 15×15 képpontos bitkép (`editpanel/ok_icon`,
// `editpanel/cancel_icon`): tömör kör fehér pipával, illetve fehér X-szel;
// a színek a kicsomagolt képekből mérve (`docs/specs/ui-audit-editor.md`
// 7.4). Az audit szerint a vágás-panel és a csúszkás paraméter-alpanel
// UGYANAZT a gombot használja — nálunk viszont két külön megoldás élt:
//
//   * a paraméter-alpanel (#700) ezt a rajzot, panelen belüli
//     `component`-ként (a közös `PanelButton`-höz a párhuzamos #703/#704
//     ág miatt akkor nem lehetett nyúlni);
//   * a vágás-panel a felirat végére fűzött „✔" / „✘" karaktert.
//
// ⛔ **A Unicode-os megoldás nem egyenértékű**, ezért szűnik meg: a glif
// betűtípusfüggő, és ha hiányzik, NYOMTALANUL eltűnik — a gombon csak a
// felirat marad, hibaüzenet nélkül. Két elforgatott téglalap mindig
// ugyanazt adja, betűtípustól függetlenül.
//
// A jel a gomb jobb szélétől 9 képpontra ül (az audit mérése); a
// használó ezt a horgonyzással állítja be, hogy a komponens elhelyezés-
// független maradjon.
Rectangle {
    id: badge

    //: igaz = zöld pipa (Alkalmaz), hamis = indigó X (Mégse)
    property bool tick: true

    implicitWidth: 15
    implicitHeight: 15
    radius: 7.5
    antialiasing: true
    color: badge.tick ? "#4e904a" : "#524ba1"

    // a pipa rövid, lefelé tartó szára
    Rectangle {
        visible: badge.tick
        x: 4; y: 7
        width: 3.9; height: 2
        radius: 1
        color: "white"
        antialiasing: true
        transformOrigin: Item.Left
        rotation: 50
    }
    // a pipa hosszú, felfelé tartó szára
    Rectangle {
        visible: badge.tick
        x: 6.5; y: 10
        width: 8.2; height: 2
        radius: 1
        color: "white"
        antialiasing: true
        transformOrigin: Item.Left
        rotation: -52
    }
    // az X két szára
    Rectangle {
        visible: !badge.tick
        anchors.centerIn: parent
        width: 9; height: 2
        radius: 1
        color: "white"
        antialiasing: true
        rotation: 45
    }
    Rectangle {
        visible: !badge.tick
        anchors.centerIn: parent
        width: 9; height: 2
        radius: 1
        color: "white"
        antialiasing: true
        rotation: -45
    }
}
