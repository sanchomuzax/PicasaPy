import QtQuick
import QtQuick.Controls

//: #754: a jobb fiók fejléc-gombja — `size_toggle` és `close`, MINDKETTŐ
//: 14 × 14 (`rightdrawerpanel.tre:18`/`:21`). Egy komponens, mert a mért
//: méret és viselkedés azonos; csak a jel és a súgó tér el.
//:
//: A `kattints()` függvény a próbáknak is belépő: a vezérlőre KATTINTUNK,
//: nem a kezelő metódusát hívjuk (ld. a `vezerlore-kattints` tanulság).
Rectangle {
    id: gomb

    property string jel: ""
    property alias sugo: sugoTooltip.text

    signal kattintva()

    function kattints() { gomb.kattintva() }

    width: 14
    height: 14
    radius: 2
    color: lebegés.hovered ? Theme.chromeBorder : "transparent"

    Text {
        anchors.centerIn: parent
        text: gomb.jel
        font.pixelSize: 9
        color: Theme.textGray
    }

    HoverHandler { id: lebegés }
    TapHandler { onTapped: gomb.kattintva() }

    ToolTip {
        id: sugoTooltip
        objectName: "drawerHeaderTooltip"
        parent: gomb
        visible: lebegés.hovered && text.length > 0
        delay: Theme.tooltipDelay
    }
}
