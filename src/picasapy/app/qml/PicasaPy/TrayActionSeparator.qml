import QtQuick

// #1345: a műveletsor csoportelválasztója (`outputlayout/separator`).
//
// A mért rétegfejléc (`docs/specs/picasa-keptalca.md` 11.): a vonal
// (28, 8)–(30, 35), azaz **2 × 27** képpont, EGY teljes 59 × 40-es
// cellán belül — vízszintesen középen, felülről 8, alulról 5 képpont
// behúzással. A cella méretét ezért a `TrayActionCell`-től örököljük,
// hogy a gombokéval ne csúszhasson szét.
TrayActionCell {
    id: separator

    //: a vonal mért mérete és helye — a CELLA koordinátarendszerében
    readonly property int ruleWidth: 2
    readonly property int ruleHeight: 27
    readonly property int ruleX: 28
    readonly property int ruleY: 8

    Rectangle {
        objectName: "trayActionSeparatorRule"
        // A `TrayActionCell` a gyerekeit az 55 × 36-os belső dobozába
        // teszi (ott ülnek a gombok); az elválasztó viszont a CELLÁHOZ
        // képest van kimérve, ezért a vizuális szülőt visszaállítjuk rá.
        parent: separator
        x: separator.ruleX
        y: separator.ruleY
        width: separator.ruleWidth
        height: separator.ruleHeight
        color: Theme.trayBorder
    }
}
