import QtQuick

// #1919: a képtálca ÖSSZECSUKOTT mappa-/album-tokenje.
//
// Az eredeti tálca egy egész mappát egyetlen elemként is tud tartani:
// bélyegkép-rács helyett egy borítókép, rajta kék hátterű, középre
// igazított felirattal — „Kiválasztott mappa - 82 fotó".
//
// ## A rétegkészlet (`referencia/tre-eroforrasok/scratch.tre`)
//
//     scratch/album:      root                m_scaleXY, m_hidden
//     scratch/albumsize:  scratch/album       mind a négy oldalon 8 px behúzás
//     scratch/albumcover: scratch/albumsize   m_centerXY, usealpha 1
//     scratch/albumlabel: scratch/album       m_centerXY, m_displayfont12
//     scratch/highlight:  scratch/albumlabel  X −4 … +4, Y 0 … +1,
//                                             round 2, predraw 1
//
// A `scratch/album` `m_scaleXY`-ja a `thumbui/clip(scratch): scratch`
// SÁVJÁRA feszíti a tokent — vagyis a token a bélyegkép-sor HELYÉT
// foglalja el, nem egy cellát benne. A `.tre` nem ad rétegkészletet
// „token egy cellában" esetre; ezért a nézetünk sem talál ki ilyet.
//
// ## Amit a képernyőképen MÉRTEM
//
// `research/Picasa3-also-talca-ikonok-viselkedese/…214629.jpg` (1920×1080),
// a tálca doboza x 7…643, y 949…1026; a sáv ebből 5 képponttal beljebb,
// tehát y 954…1021 — **68 képpont magas**.
//
// | mit | mért érték |
// |---|---|
// | `albumcover` | y 961…1012 ⇒ **52 magas** = 68 − 8 − 8, a sávra középre |
// | `albumcover` szélessége | 29 ⇒ 29/52 = 0,558 — a forráskép aránya (816/1456 = 0,560), tehát ARÁNYTARTÓ illesztés, nem vágás |
// | `highlight` | x 251…392, y 979…995 ⇒ **142 × 17**, a sáv közepén |
// | a felirat | fehér, `m_displayfont12` ⇒ 12 képpont |
//
// A pirula tehát 142 − 8 = 134 széles feliratot fog körül (±4), és
// 17 − 1 = 16 magasat (+1 alul) — pontosan a `.tre` kényszerei.
//
// ## A pirula SZÍNE — mért, nem választott
//
// A `scratch/highlight` a respackben `rect:` (nincs bitképe), a
// `constants.ui` pedig nem ad hozzá színt: a szín a kódban él, tehát
// csak a felvételről mérhető.
//
// - a fehér (248) tálcaháttér fölött a pirula **RGB(107, 153, 186)**;
// - a borítókép fölött ugyanez SÖTÉTEBB, tehát ÁTTETSZŐ. Négy olyan
//   oszlopban, ahol a kép függőlegesen sima (x = 310 · 312 · 313 · 331),
//   a háttér a pirula fölötti és alatti sorokból becsülve az áttetszőség
//   `1 − α ≈ 0,34`, vagyis **α ≈ 0,66**;
// - ebből az alapszín `((107,153,186) − 0,34·248) / 0,66 ≈ (34, 104, 154)`.
//
// ⚠️ Az α a JPEG-tömörítés miatt ±0,05 pontosságú; az alapszín ezzel
// együtt mozdul. Ami VÁLTOZATLAN — és amit az őr mér —, az a fehér fölötti
// eredmény: RGB(107, 153, 186). (Megjegyzés, nem állítás: ez közel esik a
// `constants.ui` `alist_selcolor_win = 0xFF25648B` értékéhez.)
Item {
    id: albumToken

    //: hány fotót képvisel a token — ez kerül a feliratba
    property int photoCount: 0
    //: album (`CThumbUI::UpdateAlbumAlbum`) vagy mappa
    //: (`CThumbUI::UpdateAlbumFolder`)
    property bool isAlbum: false
    //: a borítókép (`scratch/albumcover`) — üres, ha nincs
    property url coverSource: ""

    //: a `.tre` MÉRT kényszerei — egy helyen, hogy az őr is ezekre
    //: hivatkozhasson
    readonly property int sizeInset: 8      // `scratch/albumsize`
    readonly property int highlightPadX: 4  // `scratch/highlight` X −4 … +4
    readonly property int highlightPadY: 1  // `scratch/highlight` Y 0 … +1
    readonly property int highlightRadius: 2 // `Property round 2`

    //: A felirat a `CThumbUI::UpdateAlbumCover` formátumból épül fel,
    //: HÁROM külön honosított darabból — pontosan úgy, ahogy az eredeti
    //: (`referencia/stringres-en-hu.tsv`).
    //:
    //: ⚠️ Az eredeti magyar „Kiválasztott album " sztringjében van egy
    //: záró szóköz, amitől a kimenetben dupla szóköz lesz. Ezt NEM
    //: vesszük át: a hibát nem másoljuk, csak a szöveget.
    readonly property string labelText: {
        // NULLA elemnél az eredeti NEM a formátumot írja ki, hanem a
        // `CThumbUI::UpdateAlbumCoverNoSel`-t — UGYANARRA a feliratra
        // (`0x0056bbbf` ág: ugyanaz a `scratch/albumlabel` csomópont).
        if (albumToken.photoCount <= 0)
            //: `CThumbUI::UpdateAlbumCoverNoSel` — a token felirata, ha a
            //: kijelölésben egyetlen számításba jövő elem sincs
            return qsTr("No selection", "CThumbUI::UpdateAlbumCoverNoSel")
        var mi = albumToken.isAlbum
            //: `CThumbUI::UpdateAlbumAlbum` — az eredeti hivatalos magyar
            //: fordítása „Kiválasztott album"
            ? qsTr("Album Selected", "CThumbUI::UpdateAlbumAlbum")
            //: `CThumbUI::UpdateAlbumFolder` — „Kiválasztott mappa"
            : qsTr("Folder Selected", "CThumbUI::UpdateAlbumFolder")
        //: a MÉRT küszöb: `cmp ebp, 1` (`0x0056bb26`) — EGYNÉL egyes
        //: szám, kettőtől többes. (Magyarul mindkettő „fotó", de a
        //: két sztring az eredetiben is külön áll.)
        var egyseg = albumToken.photoCount === 1
            //: `CThumbUI::UpdateAlbumphoto` — egyes szám
            ? qsTr("photo", "CThumbUI::UpdateAlbumphoto")
            //: `CThumbUI::UpdateAlbumCoverphotos` — többes szám
            : qsTr("photos", "CThumbUI::UpdateAlbumCoverphotos")
        //: `CThumbUI::UpdateAlbumCover` — a token felirata: %1 a
        //: „Kiválasztott mappa"/„Kiválasztott album", %2 a darabszám,
        //: %3 a „fotó". Az eredeti formátuma `%1$s - %2$d %3$s`.
        return qsTr("%1 - %2 %3", "CThumbUI::UpdateAlbumCover")
            .arg(mi).arg(albumToken.photoCount).arg(egyseg)
    }

    // `scratch/albumsize` — a sáv mind a négy oldalán 8 képpont behúzás
    Item {
        id: albumSize
        objectName: "trayAlbumTokenSize"
        anchors.fill: parent
        anchors.margins: albumToken.sizeInset

        // `scratch/albumcover` — `m_centerXY`, `usealpha 1`.
        //
        // ARÁNYTARTÓ illesztés (`PreserveAspectFit`), nem vágás: a
        // felvételen a 0,560 arányú forrás 29 × 52-ként jelenik meg,
        // vagyis a magasság a korlát, és a szélesség az arányból jön.
        // (Ez pont ellentéte a tálca BÉLYEGKÉPEINEK, ahol a #1914 a
        // középre vágást mérte ki — ott négyzet a cella, itt nem.)
        Image {
            id: albumCover
            objectName: "trayAlbumTokenCover"
            anchors.centerIn: parent
            height: parent.height
            width: parent.width
            source: albumToken.coverSource
            fillMode: Image.PreserveAspectFit
            //: a tálca bélyegképeivel KÖZÖS textúra-gyorstár: eltérő
            //: mipmap-beállítás mellett a Qt figyelmeztet és visszaesik a
            //: korábbi szűrésre (#1600)
            smooth: true
            mipmap: true
            asynchronous: true
        }
    }

    // `scratch/albumlabel` — `m_centerXY` a SÁVBAN (nem az `albumsize`-ban),
    // `m_displayfont12`.
    //
    // A `.tre` saját megjegyzése erről a kényszerről: *„I chose this dumb
    // constraint because the tray can get so small that there's no room
    // for text"* — a felirat középre kerül, és a token annyira kicsi is
    // lehet, hogy nem fér ki. Ezért `elide`: kilógni nem lóghat.
    Text {
        id: albumLabel
        objectName: "trayAlbumTokenLabel"
        anchors.centerIn: parent
        width: Math.min(
            implicitWidth,
            Math.max(0, parent.width - 2 * albumToken.highlightPadX))
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        text: albumToken.labelText
        font.pixelSize: Theme.fontSize
        color: Theme.trayTokenHighlightText

        // `scratch/highlight` — a felirat MÖGÖTTI lekerekített pirula.
        // `Property predraw 1`: a felirat ALÁ rajzolódik, ezért `z: -1`.
        Rectangle {
            objectName: "trayAlbumTokenHighlight"
            z: -1
            x: -albumToken.highlightPadX
            y: 0
            width: parent.width + 2 * albumToken.highlightPadX
            height: parent.height + albumToken.highlightPadY
            radius: albumToken.highlightRadius
            color: Theme.trayTokenHighlight
        }
    }
}
