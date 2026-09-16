import QtQuick

// Az Alkalmaz/Mégse gomb KÖR ALAKÚ ikonja — KÖZÖS komponens (#710).
//
// Az eredetiben ez két 15×15 képpontos bitkép (`editpanel/ok_icon`,
// `editpanel/cancel_icon`): tömör kör fehér pipával, illetve fehér X-szel.
// A színek a kicsomagolt képekből MÉRVE — ld. a `pipaSzin`/`xSzin`
// megjegyzését a csatorna-cseréről, ami miatt a Mégse jelvénye eddig indigó
// volt (`docs/specs/ui-audit-editor.md` 7.4). Az audit szerint a vágás-panel és a csúszkás paraméter-alpanel
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

    //: igaz = zöld pipa (Alkalmaz), hamis = SÖTÉTVÖRÖS X (Mégse)
    property bool tick: true

    //: ⭐ A KÖR színe MÉRVE (#710, 2026-09-16): a `respack.yt`
    //: `editpanel/ok_icon` és `editpanel/cancel_icon` rétegéből, a tömör
    //: (alfa 255), nem fehér képpontok mediánjaként —
    //:
    //:     ok_icon      15 × 15   #4A904E   (zöld)
    //:     cancel_icon  15 × 15   #A14B52   (sötétvörös)
    //:
    //: A két szám a `docs/specs/ui-audit-editor.md` 7.4 táblájáé (a #1160
    //: helyesbített kicsomagolásból). A mai kör ezt ÚJRAMÉRTE, a tömör
    //: (alfa 255), nem fehér képpontok mediánjaként: `#4a904e` és `#a24b51`
    //: — csatornánként legfeljebb 1 egység eltérés, tehát a spec értéke áll.
    //:
    //: ⛔ Eddig `#4e904a` / `#524ba1` állt itt — a BGR↔RGB cserés, HIBÁS
    //: leolvasásból (a zöldön észrevehetetlen, a Mégse jelvényét viszont
    //: INDIGÓvá tette). A #1160 a kicsomagolót MEGJAVÍTOTTA, és a spec
    //: táblája azóta a helyes színt írja — **a QML viszont a régi értéken
    //: maradt**, és semmi nem mérte. Ez a jelvény tehát nem „új döntés",
    //: hanem a spec és a kód szétcsúszásának a behozása; a próba
    //: (`test_param_panel_layout_700.py`) mostantól a mért színt állítja.
    readonly property color pipaSzin: "#4A904E"
    readonly property color xSzin: "#A14B52"

    implicitWidth: 15
    implicitHeight: 15
    radius: 7.5
    antialiasing: true
    color: badge.tick ? badge.pipaSzin : badge.xSzin

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
