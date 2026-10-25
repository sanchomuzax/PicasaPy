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

    // #5885: az eredeti menü a kipipált tételnél csak pipát rajzol; a
    // jelöletlen tételnél a jelölőhely üres. A Fusion alapjelölője 14×14-es,
    // ezt a méretet és a bal oldali helyét megtartjuk, hogy a felirat ne
    // mozduljon el. A rádiócsoport kijelölt eleme is ugyanilyen pipát kap.
    indicator: Item {
        x: control.mirrored
            ? control.width - width - control.rightPadding
            : control.leftPadding
        y: control.topPadding
            + (control.height - control.topPadding - control.bottomPadding - height) / 2
        width: 14
        height: 14

        readonly property color pipaSzin: !control.enabled ? Theme.textGray
            : control.down || control.highlighted
            ? control.palette.highlightedText : control.palette.text

        Rectangle {
            visible: control.checkable && control.checked
            x: 2
            y: 5.8
            width: 3.7
            height: 1.7
            radius: height / 2
            color: parent.pipaSzin
            antialiasing: true
            transformOrigin: Item.Left
            rotation: 50
        }
        Rectangle {
            visible: control.checkable && control.checked
            x: 4.6
            y: 8.1
            width: 7.5
            height: 1.7
            radius: height / 2
            color: parent.pipaSzin
            antialiasing: true
            transformOrigin: Item.Left
            rotation: -52
        }
    }

    contentItem: MenuCimke {
        readonly property real jeloloHely: control.checkable && control.indicator
            ? control.indicator.width + control.spacing : 0
        readonly property real nyilHely: control.subMenu && control.arrow
            ? control.arrow.width + control.spacing : 0
        leftPadding: !control.mirrored ? jeloloHely : nyilHely
        rightPadding: !control.mirrored ? nyilHely : jeloloHely
        text: control.text
        font: control.font
        //: #3537: a letiltott tétel SZÜRKE (spec `ui-audit-context-menus.md`
        //: 5.1) — ugyanaz a token, amivel a `PicasaMenuItem` a helyfoglalót
        //: szürkíti. A paletta tiltott színcsoportjára nem bízhatjuk: mérve
        //: a letiltott és az élő tétel ugyanolyan színű volt.
        color: !control.enabled ? Theme.textGray
            : control.down || control.highlighted
            ? control.palette.highlightedText : control.palette.text
    }
}
