import QtQuick

// Rajzolt IGAZÍTÁS-ikon (#4547): négy vízszintes sor, balra, középre vagy
// jobbra igazítva.
//
// Az eredetiben a három igazító gomb saját ikont visel
// (`edittextpanel/leftalign_icon` · `centeralign_icon` · `rightalign_icon`,
// `edittextpanel.tre`). Nálunk eddig mindhárom gomb ugyanazt a `≡` jelet
// mutatta, és csak a buborék-súgó különböztette meg őket. Az ikon bitképe a
// respack-ban él; ez a rajzolt változat a három igazítást egymástól
// megkülönböztethetően ábrázolja.
Item {
    id: icon
    //: "left" | "center" | "right"
    property string align: "left"
    property int size: 18
    width: size
    height: 14

    //: a négy sor szélessége a teljes ikonhoz képest — különböző hosszúak,
    //: hogy az igazítás iránya látszódjon (egyforma sorokkal a három ikon
    //: egybeesne)
    readonly property var sorSzelessegek: [1.0, 0.6, 0.8, 0.45]

    Repeater {
        model: icon.sorSzelessegek
        Rectangle {
            required property real modelData
            required property int index
            width: Math.round(icon.width * modelData)
            height: 2
            y: index * 4
            x: icon.align === "center" ? Math.round((icon.width - width) / 2)
               : icon.align === "right" ? icon.width - width
               : 0
            color: Theme.ink
        }
    }
}
