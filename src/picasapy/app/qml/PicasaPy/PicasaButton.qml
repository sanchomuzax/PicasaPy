import QtQuick
import QtQuick.Controls

// Picasa-stílusú gomb: lekerekített, finom gradiens, 1px szegély.
//
// #336: a színek TOKENBŐL jönnek, nem hardkódolva. A korábbi változat fix
// világos hátteret rajzolt (#fdfdfd → #e4e4e4), a feliratot viszont a
// témafüggő Theme.textDark-kal — sötét témában ez világos szöveget adott
// világos gombon, azaz a felhasználó ÜRES gombokat látott (Importálás,
// Vissza a könyvtárhoz, E-mail, Nyomtatás, Exportálás).
//
// A tényleges színek nevesített tulajdonságokban élnek, hogy a kontraszt
// tesztelhető legyen (tests/app/test_qml_button_contrast.py) és a logika
// egy helyen maradjon.
//
// #992: a MAGYAR feliratok kilógtak a gombból és ráfolytak a szomszédjukra.
// A felhasználó a 0.8.0 Kollázs-panelén látta; a „Megjelenítés és
// szerkesztés" felirat annyira túlért a gombján, hogy eltakarta a lap alatti
// „Véletlenszerű kollázs" gombot. Ok: a `contentItem` sima `Text` volt,
// tördelés, zsugorítás és vágás NÉLKÜL — a gombok szélessége viszont a
// `.tre`-ből örökölt FIX szám, ami az ANGOL feliratra készült.
//
// A megoldás az eredetit követi: a Picasa gombbetűje (`m_buttonfontC`,
// `picasa-gomb-es-menu-rendszer.md` 6.) `textwrap 1`-gyel van beállítva,
// 5 képpontos oldalmargóval, a gomb TELJES magasságában középre zárva —
// azaz a felirat TÖRDEL. Elidálni nem szabad: az néma csonkot adna
// („Megjelenítés és szerke…"), amit egyetlen teszt sem fog meg, csak a
// felhasználó szeme.
Button {
    id: control
    property color accent: "transparent"   // pl. Theme.picasaGreen

    // A felirat legkisebb betűmérete, ha tördelve sem fér el. A padló
    // RELATÍV: a betűméret platformfüggő (ugyanaz a szöveg Linuxon és
    // Windowson más széles), beégetett képpontszámhoz kötni hamis
    // biztonság lenne.
    property int minimumLabelPixelSize: Math.max(7, control.font.pixelSize - 5)

    font.pixelSize: Theme.fontSize
    // Az eredeti szövegmargója 5 képpont oldalt, függőlegesen pedig a
    // felirat a gomb TELJES magasságában ül. A korábbi 10/6-os kitöltés a
    // fix méretű gomboknál elvette azt a helyet, ahova tördelni lehetett
    // volna (a 26 képpontos gombból 14 maradt a szövegnek — egyetlen sor).
    //
    // ⚠️ A függőleges kitöltés a LEGSPECIFIKUSABB tulajdonságokkal megy
    // (`topPadding`/`bottomPadding`), nem a gyűjtő `padding`-gel. A `padding`
    // ugyanis csak TARTALÉK érték: ha a Controls-stílus a maga `Button`-jában
    // explicit `verticalPadding`-et ad, az erősebb nála. A Windows natív
    // stílusa pontosan ezt teszi — ott a `padding: 0` NEM érvényesült, a
    // 26 képpontos gombból csak 16 maradt a feliratnak, és a két sor nem
    // fért el. (A PR Windows-lába fogta meg; Linuxon egyik stílus sem
    // csinálja, ezért helyben láthatatlan volt.)
    //
    // A vízszintes marad `horizontalPadding`: azt egyetlen stílus sem
    // állítja explicit módon, és így a hívó oldalán felülírható maradhat
    // (a szűk kollázs-gombok élnek is ezzel).
    topPadding: 0
    bottomPadding: 0
    horizontalPadding: 5
    // …a gomb IMPLICIT mérete viszont marad a régi, bőkezűbb kitöltésé:
    // a tartalmukhoz igazodó gombok (amikre nincs `width`/`height` írva)
    // így nem zsugorodnak össze az egész alkalmazásban.
    implicitWidth: control.implicitContentWidth + 20
    implicitHeight: control.implicitContentHeight + 12

    readonly property bool accented: control.accent !== Qt.color("transparent")

    // --- a gomb tényleges színei (a background/contentItem ezeket használja) ---
    readonly property color surfaceTop: control.accented
        ? Qt.lighter(control.accent, 1.25)
        : (control.down ? Qt.darker(Theme.buttonBg, 1.12)
                        : Qt.lighter(Theme.buttonBg, 1.08))
    readonly property color surfaceBottom: control.accented
        ? control.accent
        : (control.down ? Qt.darker(Theme.buttonBg, 1.22) : Theme.buttonBg)
    // #893: a letiltott gomb felirata NEM kap külön szürkítést. Az
    // eredetiben a felirat a gomb gyerekcsomópontja, tehát ugyanazt a
    // negyedelt alfát örökli — a szín maga változatlan marad.
    readonly property color inkColor: control.accented ? "white" : Theme.ink

    // #893: a letiltott csomópont alfáját az eredeti rajzoló NÉGGYEL OSZTJA
    // (`0x009e3178: shr dword ptr [edx+0x5c], 2`), közvetlenül a rajzolás
    // előtt. Nincs külön „letiltott" kép a respack.yt-ben, mert nem kell —
    // és a rajzolóban NINCS kivétel az akcentusos (zöld) gombra sem.
    // A QML `opacity` a gyerekekre ugyanúgy szorzódva öröklődik, mint ott.
    opacity: control.enabled ? 1.0 : 0.25

    background: Rectangle {
        radius: 3
        border.width: 1
        border.color: control.accented
                      ? Qt.darker(control.accent, 1.3) : Theme.chromeBorder
        gradient: Gradient {
            GradientStop { position: 0.0; color: control.surfaceTop }
            GradientStop { position: 1.0; color: control.surfaceBottom }
        }
    }

    contentItem: Text {
        text: control.text
        font: control.font
        color: control.inkColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        // 1. TÖRDEL (az eredeti `textwrap 1`-e). A `Text.Wrap` a
        //    szóhatárt keresi, és csak akkor tör szó közben, ha egyetlen
        //    szó sem fér a sorba.
        wrapMode: Text.Wrap
        // 2. SOHA nem elidál: a néma csonkot semmi nem jelezné.
        elide: Text.ElideNone
        // 3. Ha tördelve sem fér el (100 képpontos gomb, 33 karakteres
        //    magyar felirat), a betű zsugorodik a padlóig — a szöveg így
        //    kisebb lesz, de OLVASHATÓ marad. A `Text.Fit` a megadott
        //    `font.pixelSize`-t tekinti felső korlátnak, tehát ahol a
        //    felirat elfér, ott semmi nem változik.
        fontSizeMode: Text.Fit
        minimumPixelSize: control.minimumLabelPixelSize
        // …a `minimumPointSize` is, mert a `Text.Fit` a betű megadási
        // módjához illő padlót nézi: ha a stílus pont-alapú betűt ad, a
        // képpontos padló nem érvényesülne.
        minimumPointSize: control.minimumLabelPixelSize
        // 3/b. A SORKÖZ az eredetié: az `m_buttonfontC` `fontsize 12`-höz
        //    `fontleading 10`-et ad, azaz a sormagasság a betűméret 10/12-e.
        //    Ez nem szépészet, hanem ez teremti meg a helyet a második
        //    sornak: nélküle a natúr sorköz mellett két sor NEM fér a 26
        //    képpontos gombba, és a felirat a `Text.Fit`-re szorulna —
        //    amiről a Windows-láb megmutatta, hogy nem támaszkodhatunk rá
        //    a magasságra. Így viszont a felirat TELJES méretben marad, és
        //    olvashatóbb, mint zsugorítva.
        lineHeightMode: Text.ProportionalHeight
        lineHeight: 10 / 12
        // 4. Végső fék: ha a padlón sem fér el, akkor sem folyhat a
        //    szomszéd gombra. Ez a `.tre` `*_clip` konténereinek megfelelője.
        clip: true
    }
}
