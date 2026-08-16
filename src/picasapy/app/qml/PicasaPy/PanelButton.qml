import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Picasa-stílusú panel-gomb a szerkesztőben (#318/#338/#450): opcionális
// effekt-bélyegképpel, tördelt (sosem vágott) felirattal, opcionális
// buboréksúgóval.
//
// #496: kiemelve az EditorPanel.qml-ből (ld. ott a `ToolTile` megjegyzését).
Rectangle {
    id: pbtn
    property string label: ""
    property bool buttonEnabled: true
    // "" = sima gomb (korábbi kinézet); egyébként image://effectthumb/…
    property string thumbSource: ""
    // #448: a bélyegképnek megjelenítendő RÉSZE, relatív [0..1] téglalapként.
    // Alapértéke a TELJES kép — az effekt-csempék (#338) így változatlanul a
    // teljes bélyegképet mutatják, nekik nem kell tudniuk erről.
    //
    // A vágás-javaslat gombjai ezt a kép egészét ábrázoló előnézetből a
    // JAVASOLT téglalapra szűkítik: így a három javaslat három KÜLÖNBÖZŐ
    // képet mutat (az eredeti `cropsug_preview1..3`-ának megfelelője), új
    // képszolgáltató és újabb renderelés nélkül.
    property rect thumbSourceRect: Qt.rect(0, 0, 1, 1)
    // igaz, ha a `thumbSourceRect` nem a teljes kép — ekkor a kivágott
    // (számított geometriájú) bélyegkép-út fut a teljes képet mutató helyett
    readonly property bool thumbCropped:
        thumbSourceRect.x !== 0 || thumbSourceRect.y !== 0
        || thumbSourceRect.width !== 1 || thumbSourceRect.height !== 1
    // #450: opcionális hover-buboréksúgó (pl. "Copy Caption" gomb) —
    // üres stringnél nincs tooltip (a legtöbb PanelButton-hívó)
    property string tooltip: ""
    // #450: opcionális KAPCSOLÓ-állapot (félkövér/dőlt/aláhúzott,
    // igazítás) — a `ToolTile` „benyomott" mintáját követi, ugyanabból a
    // jelző-kék tokenből, hogy sötét témában is olvasható maradjon
    property bool active: false
    // #704: „alkalmazva" jelvény — hányszor szerepel ez az effekt a
    // szerkesztési láncban. 0 = nincs jelvény (a legtöbb PanelButton-hívó:
    // az Undo/Redo/Apply/Cancel/vágás-gombok sose adnak meg ilyet).
    property int appliedCount: 0
    // A jelvény kékje az EREDETI felvételen MÉRT érték (#379FFD,
    // `ui-audit-editor.md` 3.3), nem a témapaletta valamelyik közelítése.
    // Nem téma-token, mert a `Theme.qml` bővítése ehhez a körhöz nem
    // tartozott — INTEGRÁCIÓS IGÉNY: ennek `Theme.badgeBlue` néven a helye
    // a témában van (sötét témára is kell egy párja).
    readonly property color badgeBlue: "#379ffd"
    signal buttonClicked()
    Layout.fillWidth: true
    // #318: a felirat teljesen olvasható kell legyen. Bélyegképes
    // gombnál a kép + felirat együttes magassága számít, sima gombnál
    // (a régi mintát megtartva) csak a feliraté, 24px alsó korláttal.
    //
    // #422 (felhasználói hibajelentés): az effekt-fülek rácsa SZÉTCSÚSZOTT,
    // mert a kétsoros feliratú gomb (pl. „Infravörös film") magasabb lett a
    // többinél, és a rács sora hozzá igazodott — a szomszédos, egysoros
    // csempék képe pedig felnagyult. A bélyegképes gomb ezért MINDIG két
    // sornyi feliratot foglal: a rács így egyenletes, és a hosszabb nevek
    // sem vágódnak/nem lógnak a képre.
    //
    // A két sor magasságát a TÉNYLEGES betű-metrikából vesszük, nem
    // becslésből: a Windows CI megbukott egy `fontSize * 1.35`-ös
    // közelítésen (a felirat 105 px-re nőtt egy 102 px-es gombban), mert a
    // sormagasság platformonként más.
    FontMetrics {
        id: pbtnLabelMetrics
        font: pbtnLabel.font
    }
    Layout.preferredHeight: pbtn.thumbSource !== ""
        ? pbtnThumbBox.height + 2 * pbtnLabelMetrics.height + 12
        : Math.max(24, pbtnLabel.implicitHeight + 10)
    radius: 3
    border.width: 1
    border.color: Theme.chromeBorder
    // pbtn.enabled = buttonEnabled ÉS az öröklött (panel-)enabled (#103)
    enabled: pbtn.buttonEnabled
    // #314: fix világos hexák ("#fdfdfd"/"#d8d8d8"/"#ececec") helyett
    // téma-tokenekből — sötét témában a gomb is sötétedik, így a
    // (szintén témafüggő) Theme.textDark felirat olvasható marad rajta.
    //
    // #703: a tiltott gomb kitöltése KORÁBBAN `Theme.chromeBg` volt — vagyis
    // pontosan a panel háttérszíne (`EditorPanel.color`). Frissen megnyitott
    // képen (nincs mit visszavonni és nincs mit újrázni) a Visszavonás/Újra
    // sor helyén így két, a háttértől megkülönböztethetetlen folt maradt: a
    // felhasználó teljes joggal jelentette, hogy „az effektek alatt nincsenek
    // gombok". A tiltottságot a felirat szürkéje jelzi (ld. lent), nem a gomb
    // eltüntetése — ez az eredeti Picasa (és minden natív eszköztár) módja is.
    color: pbtnMouse.pressed ? Qt.darker(Theme.buttonBg, 1.15)
           : pbtn.active ? Qt.rgba(Theme.selectionBlue.r, Theme.selectionBlue.g,
                                   Theme.selectionBlue.b, 0.45)
           : Theme.buttonBg

    // #338: a bélyegkép-terület — csak akkor foglal helyet, ha van
    // thumbSource. A KÉSZ bélyegképig (Image.status !== Ready) a
    // helyőrző-keret mutatja, hogy a gomb SOHA ne legyen üres/villogó.
    Item {
        id: pbtnThumbBox
        visible: pbtn.thumbSource !== ""
        anchors.top: parent.top
        anchors.topMargin: 5
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width - 10
        // #704: az eredetin MÉRT bélyegkép 78 × 48 px egy 86 × 69 px-es
        // csempében (`ui-audit-editor.md` 3.2) — a korábbi 56 túl magas
        // volt. A csempe teljes magassága nálunk így is több a 69-nél,
        // mert a felirat KÉT sort foglal: azt a #422 kérte kifejezetten
        // (a hosszabb nevek nem vágódhatnak, és a rács sorai nem
        // csúszhatnak szét), az eredeti egysoros, 18 px-es feliratsávjával
        // szemben. Ez tudatos eltérés, nem tévedés.
        height: pbtn.thumbSource !== "" ? 48 : 0
        // #448: a kivágott bélyegkép a dobozon TÚLNYÚLIK (a teljes kép
        // nagyítva van, csak a kért része esik a dobozba) — ezt a doboz vágja
        // le. Nem-vágott (alapértelmezett) bélyegképnél a kép pontosan
        // illeszkedik, tehát nincs mit levágni: a régi megjelenés változatlan.
        clip: true

        Rectangle {
            // helyőrző, amíg a bélyegkép még nem érkezett meg
            anchors.fill: parent
            radius: 2
            color: Theme.chromeBg
            border.width: 1
            border.color: Theme.chromeBorder
            visible: !pbtnThumbImg.visible && !pbtnThumbCropImg.visible
        }
        // A TELJES bélyegkép (#338) — a `thumbSourceRect` alapértékén, azaz
        // minden eddigi hívónál (36 effekt-csempe, eszköz-gombok) ez az út
        // fut, VÁLTOZATLANUL. A #704 „alkalmazva" jelvénye a doboz sarkához
        // horgonyzott, és ez a kép tölti ki a dobozt — a mért elhelyezés
        // ezen a bindingen áll, ezért nem nyúlunk hozzá.
        Image {
            id: pbtnThumbImg
            objectName: pbtn.objectName ? pbtn.objectName + "Thumb" : ""
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            source: pbtn.thumbCropped ? "" : pbtn.thumbSource
            smooth: true
            // amíg nem kész (Loading/Null/Error), nem rajzol semmit —
            // a fenti helyőrző-Rectangle látszik helyette, nem üres folt
            visible: status === Image.Ready
        }
        // #448: a KIVÁGOTT előnézet — a kép a `thumbSourceRect` részét
        // mutatja, a doboz arányába illesztve, a doboz `clip`-jével levágva:
        //
        //   kivágás pixelben  = (natSzél · rect.width, natMag · rect.height)
        //   illesztő nagyítás = min(doboz / kivágás)  ← a KIVÁGÁS illeszkedik
        //   a teljes képet ezzel a nagyítással méretezzük, majd annyit
        //   tolunk rajta, hogy a kivágás kerüljön a doboz közepére.
        //
        // Miért KÜLÖN elem, és nem a fenti geometriájának általánosítása:
        // a fenti kép a dobozt tölti ki, a kivágott viszont túlnyúlik rajta.
        // A #704 jelvény-elhelyezés mérése (`test_effect_tile_grid_704.py`)
        // a `<név>Thumb` elem széleit veszi a bélyegkép széleinek — ha ezt
        // az elemet a rajzolt tartalomra zsugorítanánk, a mért geometria
        // csendben elcsúszna. Két elem, két tiszta eset.
        Image {
            id: pbtnThumbCropImg
            objectName: pbtn.objectName ? pbtn.objectName + "ThumbCrop" : ""
            // A természetes képméret. Amíg nincs kész kép, 0 — ilyenkor
            // 1-re esünk vissza, hogy SOHA ne osszunk nullával: a NaN
            // geometria QML-figyelmeztetést adna (a #305/#338 elve).
            readonly property real natWidth: implicitWidth > 0 ? implicitWidth : 1
            readonly property real natHeight: implicitHeight > 0 ? implicitHeight : 1
            readonly property real cropWidth:
                natWidth * Math.max(pbtn.thumbSourceRect.width, 0.001)
            readonly property real cropHeight:
                natHeight * Math.max(pbtn.thumbSourceRect.height, 0.001)
            // a doboz még lehet 0 méretű (elrendezés előtt) — a nagyítás
            // sosem lehet negatív, különben negatív méretet adnánk az elemnek
            readonly property real fitScale: Math.max(0, Math.min(
                pbtnThumbBox.width / cropWidth, pbtnThumbBox.height / cropHeight))
            // a méretet MI adjuk, egyenletes nagyítással — a Stretch itt nem
            // torzít, mert mindkét tényező ugyanaz a `fitScale`
            fillMode: Image.Stretch
            width: natWidth * fitScale
            height: natHeight * fitScale
            x: (pbtnThumbBox.width - cropWidth * fitScale) / 2
               - pbtn.thumbSourceRect.x * natWidth * fitScale
            y: (pbtnThumbBox.height - cropHeight * fitScale) / 2
               - pbtn.thumbSourceRect.y * natHeight * fitScale
            asynchronous: true
            source: pbtn.thumbCropped ? pbtn.thumbSource : ""
            smooth: true
            // A forrás a nagy szerkesztő-előnézet (több ezer pixel), amit
            // ~48 px-re kicsinyítünk — sima bilineáris szűréssel ez erősen
            // lépcsőzne. Csak ezen az úton kell: az effekt-bélyegkép 80 px-ről
            // indul, ott 36 csempényi mipmap felesleges GPU-memória lenne.
            mipmap: true
            visible: status === Image.Ready
        }
    }
    Text {
        id: pbtnLabel
        // a hívó objectName-jéből képzett saját objectName (pl.
        // "effectGrain2Label") — a tesztek ezen ellenőrzik a
        // tördelést/nem-vágást (#318), a histogramTitle mintája (#235).
        objectName: pbtn.objectName ? pbtn.objectName + "Label" : ""
        // #305/#338 mintája: SOHA ne kössünk anchort feltételesen
        // `undefined`-ra (a QML-figyelmeztetés-őr ezt buktatná) — a
        // pbtnThumbBox magassága 0, ha nincs thumbSource, így ez az
        // egyetlen, mindig érvényes anchor-készlet mindkét esetben jó
        // (sima gombnál csak néhány px-szel tér el a régi centerIn-től,
        // ami a szűk, tömören méretezett gombokon nem látszik).
        anchors.top: pbtnThumbBox.bottom
        anchors.topMargin: pbtn.thumbSource !== "" ? 4 : 3
        anchors.horizontalCenter: parent.horizontalCenter
        text: pbtn.label
        // #422 (felhasználói visszajelzés): az effekt-csempék felirata
        // NAGYOBB volt, mint az 1. fül eszköz-csempéié — a kisebb a helyes,
        // ezért a `ToolTile`-lel azonos fokozatra állítva.
        font.pixelSize: Theme.fontSize - 2
        // #704: az eredeti csempe-felirat FÉLKÖVÉR (`fontmacros_win.tre`
        // `#define m_fxlabel` → `fontweight 700`), középre zárva. A színe
        // ott #333333; nálunk a témafüggő `Theme.textDark` marad, hogy
        // sötét témában is olvasható legyen (a fix hexa ott elveszne).
        font.bold: pbtn.thumbSource !== ""
        color: pbtn.enabled ? Theme.textDark : Theme.textGray
        // #318: elide helyett tördelés — a panel szélessége nem nőhet,
        // de a szöveg soha nem vágódik "…"-ra; a Qt WordWrap szó-
        // határon tör, hosszú, tördelhetetlen szónál karakterhatáron.
        wrapMode: Text.WordWrap
        width: parent.width - 8
        horizontalAlignment: Text.AlignHCenter
        // #422: a bélyegképes csempénél a felirat LEGFELJEBB két sor lehet
        // — pontosan annyi, amennyit a gomb magassága fenntart neki. Enélkül
        // egy hosszabb név (vagy egy szélesebb betűkép: a Windows CI-n
        // ugyanaz a szöveg HÁROM sorra tört) kilógna a gombból. A sima
        // (bélyegkép nélküli) gombokon nincs korlát: ott a #318 elve marad,
        // a felirat sosem vágódik.
        maximumLineCount: pbtn.thumbSource !== "" ? 2 : 2147483647
        elide: pbtn.thumbSource !== "" ? Text.ElideRight : Text.ElideNone
    }
    // #704: „alkalmazva" jelvény — a BÉLYEGKÉP jobb alsó sarkában.
    //
    // Miért kell: a felhasználó a rácsról eddig egyáltalán nem tudta
    // megállapítani, mely effektek vannak már a képen — ez nem díszítés,
    // hanem a szerkesztő egyik alapvető visszajelzése.
    //
    // A HELYE, MÉRETE, ALAKJA és SZÍNE megerősített, nem becslés
    // (`docs/specs/ui-audit-editor.md` 3.3): az `macros.tre:301`
    // `#define m_fxadorner` szerint `XConstraint 1, 1, -6` /
    // `YConstraint 1, 1, -19`, azaz a jelvény jobb széle a csempe jobb
    // szélétől 6 px-re, az alja a csempe aljától 19 px-re van — mivel a
    // feliratsáv a csempe alsó 18 px-e, ez pontosan a BÉLYEGKÉP alsó élére
    // simul. Az 1920×1080-as felvételen mérve: 13 × 12 px, kitöltés
    // #379FFD, negyed-korong alak (CSAK a bal felső sarka lekerekített),
    // benne fehér, félkövér szám. Ezért horgonyozzuk a bélyegkép-doboz
    // jobb alsó sarkához, nem a gomb sarkához.
    //
    // ⚠️ A SZÁM JELENTÉSE NYITOTT KÉRDÉS (spec 3.4). Cáfolva, hogy a lánc
    // sorszáma lenne (egy felvételen három csempén egyszerre áll „1"), de a
    // „hányszor alkalmazták" olvasat sem áll össze: azon a felvételen a fotó
    // szerkesztetlen (a Visszavonás/Újra egyaránt letiltott). A kiírt érték
    // ezért EGYELŐRE a legvédhetőbb olvasat — a szűrő előfordulásainak száma
    // a láncban —, és a spec 3.4 N1 pontja szerint felülvizsgálandó
    // (célzott képernyőkép-kérés, illetve a `FUN_005d7c20` dekompilálása).
    // A jelvény SZÁMÁRA semmilyen viselkedés nem épül.
    Item {
        id: pbtnBadge
        objectName: pbtn.objectName ? pbtn.objectName + "Badge" : ""
        visible: pbtn.appliedCount > 0 && pbtn.thumbSource !== ""
        anchors.right: pbtnThumbBox.right
        anchors.bottom: pbtnThumbBox.bottom
        width: 13
        height: 12

        // negyed-korong: a lekerekítés CSAK a bal felső sarkon marad. A
        // két takaró-téglalap ugyanabból a színből dolgozik, ezért a
        // három alakzat egyetlen foltnak látszik. (Per-sarok `radius`-t
        // nem használunk: az Qt 6.7 fölött van csak meg, a projekt viszont
        // nem köti a Qt-verziót.)
        Rectangle {
            anchors.fill: parent
            radius: 6
            color: pbtn.badgeBlue
        }
        Rectangle {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 6
            color: pbtn.badgeBlue
        }
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 6
            color: pbtn.badgeBlue
        }

        Text {
            id: pbtnBadgeText
            objectName: pbtn.objectName ? pbtn.objectName + "BadgeText" : ""
            // a felvételen a szám a jelvény JOBB oldalán ül (a lekerekített
            // bal felső sarok elől kihúzódva)
            anchors.right: parent.right
            anchors.rightMargin: 2
            anchors.verticalCenter: parent.verticalCenter
            text: pbtn.appliedCount > 0 ? pbtn.appliedCount.toString() : ""
            font.pixelSize: Theme.fontSize - 3
            font.bold: true
            color: Theme.panelSelectionText
        }
    }

    MouseArea {
        id: pbtnMouse
        anchors.fill: parent
        hoverEnabled: pbtn.tooltip.length > 0
        onClicked: pbtn.buttonClicked()
    }
    ToolTip.text: pbtn.tooltip
    ToolTip.visible: pbtn.tooltip.length > 0 && pbtnMouse.containsMouse
    ToolTip.delay: 400
}
