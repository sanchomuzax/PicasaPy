import QtQuick
import QtQuick.Controls

// #1740: TARTALOMHOZ IGAZODÓ SZÉLESSÉGŰ menü.
//
// **A hiba.** A QtQuick.Controls `Menu`-je NEM méri meg a tételeit: a
// `contentWidth`-je 0 marad, a szélességét a háttér `implicitWidth`-je
// adja, ami a stílusban rögzített **200 képpont**. Mérve (PySide6 6.8.2.1,
// csupasz `Menu` két tétellel): `w=200`, `contentWidth=0`, miközben a
// hosszabb tétel `implicitWidth`-je 351. Angolul ez többnyire nem tűnik
// fel, magyarul viszont a feliratok fele kilóg — a menüsáv 18 menüjéből
// 12-ben, összesen 51 tételen (a bejelentés: #1740).
//
// **A javítás.** A menü a NYITÁS előtt megméri a tételeit, és a
// legszélesebbhez igazodik. Nem elég egyszer, induláskor: nyelvváltáskor
// (#333) a feliratok — és velük a tételek `implicitWidth`-je — megváltoznak,
// a QML-kötés viszont erre nem futna újra, mert az `itemAt(i)` hívás
// eredménye nem követhető tulajdonság. Ezért az `aboutToShow` az újramérés
// horgonya: a menü minden megnyitáskor a friss feliratokhoz igazodik.
//
// **A 200 képpont alsó korlát marad**, hogy a rövid menük (Nyelv,
// Mozgófilm) a megszokott szélességükben nyíljanak.
Menu {
    id: menu

    //: a leghosszabb tétel mért szélessége (a `_merd` frissíti)
    property real tetelSzelesseg: 0

    //: a menü szélességének alsó korlátja — a stílus alapértelmezése
    readonly property real alsoKorlat: 200

    //: Megméri a tételeket, és eltárolja a legszélesebb szélességét.
    //:
    //: ⚠️ A `visible` SZÁNDÉKOSAN nincs szűrve. Csukott menüben a tételek
    //: `visible`-je hamis — a szűrésre épített első változat ezért mindig
    //: 0-t mért, és némán hatástalan maradt. A ritka, feltételesen rejtett
    //: tétel így beleszámít a szélességbe: a menü néhány képponttal
    //: szélesebb lehet a kelleténél. Ez a rossz irányba téved.
    function _merd() {
        var szeles = 0
        for (var i = 0; i < menu.count; ++i) {
            var tetel = menu.itemAt(i)
            if (tetel)
                szeles = Math.max(szeles, tetel.implicitWidth)
        }
        menu.tetelSzelesseg = szeles
    }

    implicitWidth: Math.max(
        menu.alsoKorlat,
        menu.tetelSzelesseg + menu.leftPadding + menu.rightPadding)

    onCountChanged: menu._merd()
    onAboutToShow: menu._merd()
    Component.onCompleted: menu._merd()
}
