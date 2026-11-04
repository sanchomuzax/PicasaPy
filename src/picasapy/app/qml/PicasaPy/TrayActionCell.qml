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
// #6499: a mért 55-ös LÉPÉS megmarad, de a gomb vízszintesen 53 képpont,
// 1-1 képpont margóval mindkét oldalon. Így a szomszédos gombok keretei
// között 2 képpont háttér van. Az eredeti kirajzolás szerint a gombok
// érintkeztek; a tulajdonos ezt hibás elrendezésnek jelezte, nem
// Picasa-viselkedésnek, ezért tértünk el tőle. A cella-lépés (55) és az
// ablakszélesség-modell változatlan, a sáv többi eleme nem mozdul.
// Függőlegesen a 2-2 képpontos margó marad (40 - 36). Ez a komponens ezt
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
    //: #6499: a gomb 53 széles (nem 55), hogy a szomszédos gombok között
    //: legyen rés; a lépés (cellWidth) 55 marad.
    readonly property int cellWidth: 55
    readonly property int cellHeight: 40
    readonly property int buttonWidth: 53
    readonly property int buttonHeight: 36
    //: a margó IRÁNYONKÉNT külön: vízszintesen (55 - 53) / 2 = 1 (#6499),
    //: függőlegesen (40 - 36) / 2 = 2 (#1504). Egyetlen `buttonMargin`
    //: mindkettőre hamis volna.
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
