import QtQuick

// A kijelölésen KÍVÜLI terület elsötétítése — négy sáv a téglalap körül (#900).
//
// Az eredeti `.tre` a `Property negativemode 8f2f2f2f` sorral ÖT elemen adja
// meg ugyanezt az értéket (`editpanel/cropselection`, `redselection`,
// `addfaceselection`, `faces`, `nav/nav`), és a parszer (`0x009c79ce`) HEXAKÉNT,
// ARGB-ként olvassa. Ezért él a szín egy helyen (`Theme.selectionDim`), és
// ezért osztozik rajta mind a három eszközünk ugyanezen a komponensen.
//
// A sávok a KÜLSŐ területet fedik, tehát a kijelölés maga érintetlen marad.
// A `coveredArea` a fedett terület — mérhető állítás arra, hogy pontosan a
// külső rész van fedve, se több, se kevesebb.
Item {
    id: dim

    // a kijelölés téklalapja a komponens koordinátarendszerében
    property real selX: 0
    property real selY: 0
    property real selW: 0
    property real selH: 0
    // van-e egyáltalán mit körbesötétíteni
    property bool active: false
    property color dimColor: Theme.selectionDim

    anchors.fill: parent
    visible: dim.active

    readonly property real _bal: Math.max(0, Math.min(dim.selX, dim.width))
    readonly property real _teto: Math.max(0, Math.min(dim.selY, dim.height))
    readonly property real _jobb:
        Math.max(dim._bal, Math.min(dim.selX + dim.selW, dim.width))
    readonly property real _alj:
        Math.max(dim._teto, Math.min(dim.selY + dim.selH, dim.height))

    // a ténylegesen elsötétített terület — a teljes vászon mínusz a kijelölés
    readonly property real coveredArea:
        dim.width * dim.height - (dim._jobb - dim._bal) * (dim._alj - dim._teto)

    // fent
    Rectangle {
        color: dim.dimColor
        x: 0; y: 0
        width: dim.width; height: dim._teto
    }
    // lent
    Rectangle {
        color: dim.dimColor
        x: 0; y: dim._alj
        width: dim.width; height: Math.max(0, dim.height - dim._alj)
    }
    // balra (csak a kijelölés magasságában)
    Rectangle {
        color: dim.dimColor
        x: 0; y: dim._teto
        width: dim._bal; height: dim._alj - dim._teto
    }
    // jobbra (csak a kijelölés magasságában)
    Rectangle {
        color: dim.dimColor
        x: dim._jobb; y: dim._teto
        width: Math.max(0, dim.width - dim._jobb); height: dim._alj - dim._teto
    }
}
