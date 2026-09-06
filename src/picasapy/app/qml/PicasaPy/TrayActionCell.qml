import QtQuick
import QtQuick.Layouts

// #1345: az alsó műveletsor egy CELLÁJA.
//
// A `respack.yt` rétegfejlécei (`docs/specs/picasa-keptalca.md` 11.) az
// eredeti kimeneti sávjának mind a kilenc gombjára BÁJTRA azonos
// befoglalót adnak:
//
//   docbounds (`outputlayout/docbounds`, `overflow`)  (0, 0)–(59, 40)
//   gomb      (`button(print)`, `(email)`, …)         (2, 2)–(57, 38)  55 × 36
//
// ⚠️ #1504: az 59 × 40 a `docbounds` cella-GRAFIKA mérete, NEM az
// osztásköz. A #1345 az 59-et léptetésnek olvasta; a #1420 viszont a
// KIRAJZOLT Picasa-képernyőképen 55-öt mért (a három felirat közepe
// 867,5 · 922,5 · 977,5), és a binárisban meg is van az oka: az elrendező
// (`0x00597f80`) a ciklus végén (`0x0059883e`–`0x00598863`) a gyerek
// ELRENDEZÉS UTÁNI befoglalójából számol szélességet (`x1 − x0`), és AZT
// adja az akkumulátorhoz — vagyis a lépés a gomb saját doboza: **55**.
// Ezért nincs hézag a gombok között az eredetiben.
//
// A cella tehát VÍZSZINTESEN pontosan akkora, mint a gomb (55), és csak
// FÜGGŐLEGESEN marad a 2-2 képpontos margó (40 − 36). Ez a komponens ezt
// a két dobozt valósítja meg, hogy a méret EGY helyen éljen: a hívó csak
// beleteszi a gombját, és az méret szerint garantáltan egységes lesz a
// szomszédaival.
//
// A méret SZÁNDÉKOSAN fix: a jegy mért képpontokat ír elő, tehát a
// cellának nem szabad az ablakkal skálázódnia. A `Layout.*` minimum/
// maximum párok éppen ezt zárják ki a szülő `RowLayout`-ban.
Item {
    id: cell

    //: a mért geometria — a hívók és a tesztek is innen olvashatják
    //: #1504: a cella SZÉLESSÉGE az OSZTÁSKÖZ (55), nem a `docbounds`
    //: grafika 59-e; a MAGASSÁGA marad a mért 40.
    readonly property int cellWidth: 55
    readonly property int cellHeight: 40
    readonly property int buttonWidth: 55
    readonly property int buttonHeight: 36
    //: a margó IRÁNYONKÉNT külön (#1504): vízszintesen (55 − 55) / 2 = 0,
    //: függőlegesen (40 − 36) / 2 = 2. Egyetlen `buttonMargin` mindkettőre
    //: hamis volna — a vízszintes rés épp az, ami az eredetiben NINCS.
    readonly property int buttonMarginX: (cell.cellWidth - cell.buttonWidth) / 2
    readonly property int buttonMarginY:
        (cell.cellHeight - cell.buttonHeight) / 2

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
        x: cell.buttonMarginX
        y: cell.buttonMarginY
        width: cell.buttonWidth
        height: cell.buttonHeight
    }
}
