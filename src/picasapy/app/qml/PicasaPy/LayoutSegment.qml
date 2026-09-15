import QtQuick
import QtQuick.Controls

//: #3013: egy szegmens a kettős nézet háromállású kapcsolójában
//: (`editpanel/layout_2up_group`).
//:
//: ⚠️ A kizárás NEM `checked`-kötés, hanem `uptarget`-szemantika: a
//: lenyomott gomb a MÁSIK KETTŐT engedi fel, önmagát nem. Ezért az aktív
//: szegmensre kattintva az lenyomva MARAD — a `checkable + kötött checked`
//: rádió-csapda (#1468) itt elő sem jöhet.
Rectangle {
    id: szegmens

    //: melyik üzemmódot kapcsolja („1up" · „aa" · „ab")
    required property string mod
    //: a gazda néző — tőle kérdezzük az aktív módot, és neki állítjuk
    required property var nezo
    property string jel: ""
    property string sugo: ""

    //: a próbáké is: a VEZÉRLŐRE kattintunk, nem a kezelőt hívjuk
    function kattints() {
        if (!szegmens.enabled) return
        szegmens.nezo.layoutMode = szegmens.mod
    }

    readonly property bool aktiv: szegmens.nezo.layoutMode === szegmens.mod

    width: 26
    height: 22
    radius: 2
    color: szegmens.aktiv ? Theme.buttonBg
                          : (lebegés.hovered ? Theme.chromeBorder : "transparent")
    border.width: szegmens.aktiv ? 1 : 0
    border.color: Theme.buttonToggledBorder
    opacity: szegmens.enabled ? 1 : 0.45

    Text {
        anchors.centerIn: parent
        text: szegmens.jel
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }

    //: #885: LENYOMÁSRA sül el — a `.tre` a három elrendezés-váltóra
    //: (`only_1up_toggle`, `ab_2up_toggle`, `aa_2up_toggle`) `Property
    //: mousedown 1`-et ad; nézetváltás, tehát azonnal hat.
    //:
    //: ⚠️ KIVÉTEL, és ez is mért: a `swap_2up_focus` és a
    //: `swap_2up_layout` elemen NINCS `mousedown` — azok felengedésre
    //: sülnek el, ezért a használó `lenyomasra: false`-t ad.
    property bool lenyomasra: true

    HoverHandler { id: lebegés }
    TapHandler {
        onPressedChanged: if (pressed && szegmens.lenyomasra) szegmens.kattints()
        onTapped: if (!szegmens.lenyomasra) szegmens.kattints()
    }

    ToolTip.text: szegmens.sugo
    ToolTip.visible: lebegés.hovered && szegmens.sugo !== ""
    ToolTip.delay: Theme.tooltipDelay
}
