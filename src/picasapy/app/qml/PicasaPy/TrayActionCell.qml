import QtQuick
import QtQuick.Layouts

// #1345: az alsó műveletsor egy CELLÁJA.
//
// A `respack.yt` rétegfejlécei (`docs/specs/picasa-keptalca.md` 11.) az
// eredeti kimeneti sávjának mind a kilenc gombjára BÁJTRA azonos
// befoglalót adnak:
//
//   cella (`outputlayout/docbounds`, `overflow`)  (0, 0)–(59, 40)  59 × 40
//   gomb  (`button(print)`, `(email)`, …)         (2, 2)–(57, 38)  55 × 36
//
// azaz minden gomb 2-2 képpont margóval ül a cellájában. Ez a komponens
// pontosan ezt a két dobozt valósítja meg, hogy a méret EGY helyen éljen:
// a hívó csak beleteszi a gombját, és az méret szerint garantáltan
// egységes lesz a szomszédaival.
//
// A méret SZÁNDÉKOSAN fix: a jegy mért képpontokat ír elő, tehát a
// cellának nem szabad az ablakkal skálázódnia. A `Layout.*` minimum/
// maximum párok éppen ezt zárják ki a szülő `RowLayout`-ban.
Item {
    id: cell

    //: a mért geometria — a hívók és a tesztek is innen olvashatják
    readonly property int cellWidth: 59
    readonly property int cellHeight: 40
    readonly property int buttonWidth: 55
    readonly property int buttonHeight: 36
    //: a körbefutó margó: (59 − 55) / 2 = (40 − 36) / 2 = 2
    readonly property int buttonMargin: 2

    // a gomb a belső dobozba kerül, nem közvetlenül a cellába
    default property alias cellContent: slot.data

    implicitWidth: cell.cellWidth
    implicitHeight: cell.cellHeight
    Layout.preferredWidth: cell.cellWidth
    Layout.preferredHeight: cell.cellHeight
    Layout.minimumWidth: cell.cellWidth
    Layout.maximumWidth: cell.cellWidth
    Layout.minimumHeight: cell.cellHeight
    Layout.maximumHeight: cell.cellHeight
    Layout.alignment: Qt.AlignVCenter

    Item {
        id: slot
        x: cell.buttonMargin
        y: cell.buttonMargin
        width: cell.buttonWidth
        height: cell.buttonHeight
    }
}
