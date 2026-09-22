import QtQuick
import QtQuick.Controls.Fusion as Fusion
import PicasaPy

// A KÖZÖS menütétel (#3455): a Fusion menütétele, amelynek a címkéje a
// felirat mellett a gyorsbillentyűt is kezeli — a `\t` utáni részt egy
// jobbra igazított oszlopba teszi (`MenuCimke`). Stílusként MINDEN sima
// `MenuItem`-re hat, a hívók változatlanok (ld. `ToolTip.qml`, #901).
//
// A jelölő és az almenü-nyíl helyét ugyanúgy hagyja ki, mint a Fusion
// alapértelmezett címkéje (#1750: a `PicasaMenuItem` ezt tanulta meg).
Fusion.MenuItem {
    id: control

    contentItem: MenuCimke {
        readonly property real jeloloHely: control.checkable && control.indicator
            ? control.indicator.width + control.spacing : 0
        readonly property real nyilHely: control.subMenu && control.arrow
            ? control.arrow.width + control.spacing : 0
        leftPadding: !control.mirrored ? jeloloHely : nyilHely
        rightPadding: !control.mirrored ? nyilHely : jeloloHely
        text: control.text
        font: control.font
        color: control.down || control.highlighted
            ? control.palette.highlightedText : control.palette.text
    }
}
