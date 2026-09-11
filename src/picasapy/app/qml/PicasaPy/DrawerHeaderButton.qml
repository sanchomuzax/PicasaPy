import QtQuick

//: #754: a jobb fiók fejléc-gombja — `size_toggle` és `close`, MINDKETTŐ
//: 14 × 14 (`rightdrawerpanel.tre:18`/`:21`). Egy komponens, mert a mért
//: méret és viselkedés azonos; csak a jel és a súgó tér el.
//:
//: A `kattints()` függvény a próbáknak is belépő: a vezérlőre KATTINTUNK,
//: nem a kezelő metódusát hívjuk (ld. a `vezerlore-kattints` tanulság).
Rectangle {
    id: gomb

    property string jel: ""
    property alias sugo: sugoSzoveg.text

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

    //: a súgó szövege a mért eredeti felirat; külön elem, hogy az `alias`
    //: fordítható maradjon
    Text { id: sugoSzoveg; visible: false }
}
