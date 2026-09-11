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
    //: #2597: OPCIONÁLIS rögzített gombmagasság. 0 = kikapcsolva (minden
    //: eddigi hívó ezt kapja: a gomb a felirathoz igazodik).
    //:
    //: Aki megadja, azt kéri, hogy a gomb MÉRT magassága legyen a mérce, a
    //: felirat pedig igazodjon hozzá — ez az eredeti Picasa viselkedése: a
    //: rajzolt keretet az erőforrás adja meg (`m_buttonfontC`: `textwrap 1`),
    //: nem a szöveg. Enélkül a gombmagasság a PLATFORM betűmetrikáját
    //: hordozza: a fix sorköz (`Theme.lineLeading`) csak a MÁSODIK sortól
    //: érvényesül, az elsőt a betű natúr sormagassága adja. Ezen a gépen ez
    //: 14, a CI windows-lábán nagyobb — a Visszavonás-gomb ezért volt ott
    //: 32 képpont a mért eredeti 26 helyett (#2597), és ezért nőtt 36-ra a
    //: hosszabb effektnevek alatt itt is.
    property real rogzitettMagassag: 0
    readonly property bool rogzitett: pbtn.rogzitettMagassag > 0
    //: #2597: a betűillesztés padlója rögzített magasságnál — a
    //: `PicasaButton` `minimumLabelPixelSize`-ének mintája. A felirat
    //: legfeljebb ennyire zsugorodhat: olvashatatlanul kicsi szöveg helyett
    //: inkább vágunk (az eredeti `*_clip` konténereinek módja).
    property int minimumLabelPixelSize: Math.max(7, Theme.fontSize - 5)
    //: #422: a felirat alap-fokozata (a `ToolTile`-lel azonos szint).
    property int labelAlapFokozat: Theme.fontSize - 2
    //: #815: a felirat BETŰKÖZE — MÉRVE, `fonttrack -1`. Ugyanez az érték
    //: minden érintett makróban: `m_fxlabel` (a 12 effekt-csempe felirata),
    //: `m_buttonfontC`, `m_buttonfontCbelow`, `m_buttonfontLC` (a panel
    //: gombfeliratai) — vagyis a panel EGÉSZ tipográfiája szorosabb, nem
    //: csak a csempéké.
    readonly property real labelBetukoz: -1
    //: #2597: a mért eredeti KÉT sorban mutatja a „Visszavonás: <effektnév>"
    //: feliratot a 26 képpontos gombban.
    readonly property int rogzitettSorok: 2
    //: #2597: mennyi hely van az ELSŐ sor natúr betűdobozának: a gomb
    //: magasságából a keret és a további sorok fix sorköze marad ki. A
    //: `Text.FixedHeight` sorköz ugyanis csak a MÁSODIK sortól érvényesül —
    //: az elsőt a betű saját sormagassága adja (mérve: ezen a gépen 2 sor =
    //: 14 + 10 = 24 képpont).
    readonly property real elerhetoSorbox: Math.max(
        1,
        pbtn.rogzitettMagassag - 2 * pbtn.border.width
            - (pbtn.rogzitettSorok - 1) * Theme.lineLeading)
    //: #2597: a felirat TÉNYLEGES fokozata. Rögzített magasságnál a platform
    //: betűjéhez igazodik: ha a natúr sormagassága nem fér a fenti helybe, a
    //: fokozat arányosan kisebb lesz (padló: `minimumLabelPixelSize`). Ahol
    //: elfér — ezen a gépen —, ott az alap-fokozat marad, tehát a helyi
    //: kinézet NEM változik.
    //:
    //: ⚠️ Miért nem `Text.Fit`: MÉRVE (2026-09-08), a Qt betűillesztése
    //: `lineHeightMode: Text.FixedHeight` mellett NEM zsugorít — 20
    //: képpontos betűvel a rajzolt szöveg 38 képpont maradt egy 24 képpontos
    //: elemben. A fix sorköz viszont mért követelmény (#2494), tehát nem
    //: adhatjuk fel érte; a fokozatot ezért magunk számoljuk.
    //: #2759: a SZÉLESSÉG is korlát, nem csak a magasság. A CI windows-lábán
    //: a rendszerbetű SZÉLESEBB (a natúr sormagassága viszont ugyanaz), ezért
    //: a magasság-alapú fék nem lépett működésbe, a „Visszavonás: Automatikus
    //: kontraszt" pedig HÁROM sorra tört a mért 130 képpontos gombon — a
    //: harmadik sor a `maximumLineCount` miatt némán elmaradt.
    readonly property real elerhetoSorSzelesseg: Math.max(
        1, pbtn.width - 8 - 2 * pbtn.border.width)

    //: #2759: az a legnagyobb fokozat, amellyel a felirat MÉG BEFÉR
    //: `rogzitettSorok` sorba — a Qt mohó sortörését utánozva, szavanként.
    //:
    //: ⚠️ Miért nem egy arányos becslés (össz-szélesség / sorok): mérve nem
    //: elég. A „Visszavonás: Automatikus kontraszt" össz-szélessége 160,6
    //: képpont egy 119 képpontos sorban, tehát ARÁNYOSAN elférne két sorban —
    //: a HÁROM hosszú szó viszont nem pakolható be kettőbe („Visszavonás:
    //: Automatikus" magában 124 képpont). A csomagolást tehát végig kell
    //: játszani, nem megbecsülni; a tartalék-konstans épp azért nem
    //: megbízható, mert a szóhatárok döntenek, nem az átlag.
    //:
    //: A szélességek a BÁZIS fokozat metrikájából, lineárisan skálázva
    //: jönnek (a betűk előretolása jó közelítéssel arányos a mérettel) —
    //: körkötés nélkül, mert a `pbtnAlapMetrika` a fix alap-fokozaton áll.
    function fokozatSzelessegre() {
        var szelesseg = pbtn.elerhetoSorSzelesseg
        var szavak = String(pbtn.label).split(/\s+/).filter(function (sz) {
            return sz.length > 0
        })
        if (szavak.length === 0)
            return pbtn.labelAlapFokozat
        var szokoz = pbtnAlapMetrika.advanceWidth(" ")
        for (var meret = pbtn.labelAlapFokozat; meret > pbtn.minimumLabelPixelSize; meret--) {
            var arany = meret / pbtn.labelAlapFokozat
            var sorok = 1
            var jelen = 0
            var belefer = true
            for (var i = 0; i < szavak.length; i++) {
                var szo = pbtnAlapMetrika.advanceWidth(szavak[i]) * arany
                if (szo > szelesseg) {       // egyetlen szó sem fér ki
                    belefer = false
                    break
                }
                var ujHossz = jelen === 0 ? szo : jelen + szokoz * arany + szo
                if (ujHossz <= szelesseg) {
                    jelen = ujHossz
                } else {
                    sorok++
                    jelen = szo
                }
            }
            if (belefer && sorok <= pbtn.rogzitettSorok)
                return meret
        }
        return pbtn.minimumLabelPixelSize
    }

    //: #2597 + #2759: a felirat TÉNYLEGES fokozata. Rögzített magasságnál a
    //: platform betűjéhez igazodik KÉT irányban: a natúr sormagasság férjen a
    //: gombba, ÉS a szöveg férjen `rogzitettSorok` sorba (padló:
    //: `minimumLabelPixelSize`). Ahol elfér — ezen a gépen —, ott az
    //: alap-fokozat marad, tehát a helyi kinézet NEM változik.
    //:
    //: ⚠️ Miért nem `Text.Fit`: MÉRVE (2026-09-08), a Qt betűillesztése
    //: `lineHeightMode: Text.FixedHeight` mellett NEM zsugorít — 20 képpontos
    //: betűvel a rajzolt szöveg 38 képpont maradt egy 24 képpontos elemben. A
    //: fix sorköz viszont mért követelmény (#2494), tehát nem adhatjuk fel
    //: érte; a fokozatot ezért magunk számoljuk.
    readonly property int labelFokozat: pbtn.rogzitett
        ? Math.max(
            pbtn.minimumLabelPixelSize,
            Math.min(
                pbtn.labelAlapFokozat,
                Math.floor(pbtn.labelAlapFokozat * pbtn.elerhetoSorbox
                           / Math.max(1, pbtnAlapMetrika.height)),
                pbtn.fokozatSzelessegre()))
        : pbtn.labelAlapFokozat

    //: #2597: a felirat betűjének metrikája az ALAP fokozaton — ebből derül
    //: ki, hogy a platform sormagassága belefér-e a gombba. Külön elem, nem
    //: a `pbtnLabelMetrics`: az a felirat TÉNYLEGES betűjét méri, tehát a
    //: `labelFokozat`-tal körkötést adna.
    FontMetrics {
        id: pbtnAlapMetrika
        font.family: pbtnLabel.font.family
        font.bold: pbtnLabel.font.bold
        font.pixelSize: pbtn.labelAlapFokozat
        //: #815: a betűköz a MÉRŐELEMEN is — különben a #2597 fokozat-
        //: illesztése a betűköz nélküli, SZÉLESEBB szöveggel számolna, és a
        //: felirat a kelleténél kisebb fokozatra esne.
        font.letterSpacing: pbtn.labelBetukoz
    }
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
    // #2126: kék jelvény — a csempe szűrője EGYKATTINTÁSOS-e (`mode`).
    // Korábban (#704) az „alkalmazva" számláló kapcsolta, de a #1869 mérése
    // szerint az eredetiben a jelvénynek semmi köze a szerkesztési lánchoz:
    // a csempeépítő a szűrő-leíró `mode` mezőjét olvassa. A legtöbb
    // PanelButton-hívó (Undo/Redo/Apply/Cancel/vágás) sose ad meg ilyet.
    property bool badge: false
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
    //: #2494: a felirathoz szükséges magasság KIOLVASHATÓAN is — a hívó
    //: (pl. a Visszavonás/Újra pár) így egyeztetni tudja a sor magasságát,
    //: anélkül hogy a Layout viselkedésére hagyatkozna. A `fillHeight`
    //: erre nem jó: Qt-verziófüggő, hogy a sor magasságát a preferált
    //: érték vagy a másik elem szabja-e meg — a CI-n (Qt 6.8) a gomb 28
    //: maradt, miközben helyben (6.11) megnőtt.
    //: #2494 (VISSZAESÉS-javítás): a bélyegkép NÉLKÜLI ág kitöltése 10-ről
    //: 2-re. A 10 abból a korból való, amikor a sorköz a betűtípus saját
    //: 13,64 képpontos sormagassága volt: a kétsoros felirat 28 képpontot
    //: kért, a gomb 38-ra nőtt — a tulajdonos ezt jelentette. Most a
    //: `paintedHeight` maga hordozza a sor körüli üres sávot (két sorra 24,
    //: amiből a TINTA 18), tehát a mért 26 képpontos gombban pontosan a
    //: felvételen látható 4-4 képpontos rés marad fölötte-alatta.
    //:
    //: Az EGYSOROS eset alsó korlátja (24) SZÁNDÉKOSAN változatlan: azon a
    //: vágás- és paraméterpanel gombjai állnak, azokat ez a jegy nem méri.
    //: #2597: rögzített magasságnál a kért érték maga a mért szám — semmi
    //: betűmetrika nincs benne, tehát platformfüggetlen.
    readonly property real kertMagassag: pbtn.rogzitett
        ? pbtn.rogzitettMagassag
        : pbtn.thumbSource !== ""
        ? pbtnThumbBox.height + 2 * pbtnLabelMetrics.height + 12
        : Math.max(24, pbtnLabel.implicitHeight + 2)
    Layout.preferredHeight: pbtn.kertMagassag
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
        //: #2494: bélyegkép nélkül a doboz 0 magas ÉS 0 margós — így a
        //: felirat középre igazítása (lent) nem kényszerül arra, hogy ezt
        //: az 5-öt kivonja magából. Korábban kivonta, és a kivonás
        //: `Math.max(0, …)`-nál elakadt egy szűk (26 px-es) gombon: a
        //: felirat 5 képponttal lejjebb került, és alul kilógott.
        anchors.topMargin: pbtn.thumbSource !== "" ? 5 : 0
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
        // #2494: bélyegkép nélküli gombon a felirat KÖZÉPEN ül, nem a
        // tetőhöz tapadva. A `pbtnThumbBox` ilyenkor 0 magas, de a
        // `parent.top`-hoz kötött 5 képpontos margója így is elveszett a
        // tetején — a felirat 11 képponttal lejjebb kezdődött, mint az
        // eredetiben (MÉRVE, `235707.jpg`: nálunk 11, ott 4). A kétsoros
        // „Visszavonás: <effektnév>" ettől lelógott a gombról.
        //
        // ⚠️ NEM feltételes anchor `undefined`-ra (azt a #305/#338 tiltja):
        // a margó SZÁMÍTOTT, és mindig érvényes értéket ad.
        //
        // #2494 (VISSZAESÉS-javítás): itt korábban `… / 2 - 5` állt, mert a
        // `pbtnThumbBox` bélyegkép nélkül is 5 képponttal a gomb teteje
        // alatt kezdődött. A kivonás egy szűk gombon a `Math.max(0, …)`
        // padlójába ütközött, és a felirat 5 képponttal lejjebb csúszott.
        // A doboz margója most bélyegkép nélkül 0, tehát a képlet tiszta.
        anchors.topMargin: pbtn.thumbSource !== ""
            ? 4
            : Math.max(0, (pbtn.height - pbtnLabel.paintedHeight) / 2)
        anchors.horizontalCenter: parent.horizontalCenter
        text: pbtn.label
        // #422 (felhasználói visszajelzés): az effekt-csempék felirata
        // NAGYOBB volt, mint az 1. fül eszköz-csempéié — a kisebb a helyes,
        // ezért a `ToolTile`-lel azonos fokozatra állítva.
        font.pixelSize: pbtn.labelFokozat
        font.letterSpacing: pbtn.labelBetukoz
        // #704: az eredeti csempe-felirat FÉLKÖVÉR (`fontmacros_win.tre`
        // `#define m_fxlabel` → `fontweight 700`), középre zárva. A színe
        // ott #333333; nálunk a témafüggő `Theme.textDark` marad, hogy
        // sötét témában is olvasható legyen (a fix hexa ott elveszne).
        font.bold: pbtn.thumbSource !== ""
        //: #815: a MÉRT szövegszín ALFÁJA 80% (`CC`), nem átlátszatlan — a
        //: `m_buttontypecolor` (`CC000000`) a leggyakoribb gombszín-makró,
        //: **136 elemen** használva. A SZÍNT témafüggőnek hagyjuk
        //: (`Theme.textDark`): a fix `#000000` sötét témában elveszne.
        //:
        //: ⚠️ EGÉR ALATT NEM VÁLT SZÍNT, és ez mérés, nem kihagyás. A
        //: `typecolor` három állapota a `m_buttontypecolor`-ban azonos
        //: (`CC000000 CC000000 CC000000`). A fehérre váltó két makró
        //: (`m_buttontypecolor2`, `m_buttonfont12`) a teljes
        //: erőforráskészletben **nulla elemen** szerepel — csak a saját
        //: `#define`-juk hivatkozik rájuk, tehát halott erőforrás. A
        //: LENYOMOTT állapot minden makróban visszatér az alapszínre.
        color: pbtn.enabled
               ? Qt.rgba(Theme.textDark.r, Theme.textDark.g, Theme.textDark.b,
                         0.8)
               : Theme.textGray
        // #318: elide helyett tördelés — a panel szélessége nem nőhet,
        // de a szöveg soha nem vágódik "…"-ra; a Qt WordWrap szó-
        // határon tör, hosszú, tördelhetetlen szónál karakterhatáron.
        wrapMode: Text.WordWrap
        //: #2597: rögzített magasságnál a felirat a GOMBHOZ igazodik — a
        //: BETŰFOKOZATÁN keresztül (`pbtn.labelFokozat`, ld. ott, miért nem
        //: `Text.Fit`). Az elem magassága szándékosan a szöveghez simul
        //: (nincs saját `height`/`verticalAlignment`): a középre igazítást a
        //: lenti `anchors.topMargin` végzi, és a #2494 őre a felirat
        //: ELEMÉNEK helyzetét méri — egy gomb-magas, magában középező elem
        //: azt a mérést vakká tenné.
        //:
        //: ⚠️ A vágás a VÉGSŐ fék (#2597, a CI windows-lábán mérve): ha a
        //: platform betűje a legkisebb megengedett fokozaton sem fér el, a
        //: rajzolt szöveg egy képponttal túlnyúlhat a gombon. Vágás nélkül
        //: ez a szomszéd gombra folyna — a mért eredeti ugyanezt teszi (a
        //: `.tre` `*_clip` konténerei).
        clip: pbtn.rogzitett
        //: #2494: a sorköz. A `Text` alapértelmezése a betűtípus SAJÁT
        //: sormagassága (Nunito Sans 10 px-en 13,64) — a kétsoros
        //: „Visszavonás: <effektnév>" ettől 14 képpontos sorközzel rajzolódott
        //: a mért 10 helyett, és a gombot kellett megnövelni, hogy elférjen.
        //:
        //: ⚠️ HELYESBÍTÉS. A #2494 első köre azzal hagyta békén a sorközt,
        //: hogy „a #422-ben a Windows CI ugyanazt a szöveget HÁROM sorra
        //: törte, mert a sormagasság platformonként más". Ez TÉVES
        //: hivatkozás volt: a #422 a gombmagasság `fontSize * 1.35`-ös
        //: BECSLÉSÉRŐL szólt, a sorra törést pedig a betűk SZÉLESSÉGE dönti
        //: el, amire a sorköznek semmi hatása. A sorköz szorítása nem
        //: hozhat vissza egy harmadik sort.
        //:
        //: Az érték az EREDETI erőforrásból való (`m_buttonfontC`:
        //: `fontsize 12`, `textwrap 1`, `fontleading 10`), és a tulajdonos
        //: felvételén (`141421.jpg`) mérve is 10 képpont. Ld. `Theme.lineLeading`.
        lineHeightMode: Text.FixedHeight
        lineHeight: Theme.lineLeading
        width: parent.width - 8
        horizontalAlignment: Text.AlignHCenter
        // #422: a bélyegképes csempénél a felirat LEGFELJEBB két sor lehet
        // — pontosan annyi, amennyit a gomb magassága fenntart neki. Enélkül
        // egy hosszabb név (vagy egy szélesebb betűkép: a Windows CI-n
        // ugyanaz a szöveg HÁROM sorra tört) kilógna a gombból. A sima
        // (bélyegkép nélküli) gombokon nincs korlát: ott a #318 elve marad,
        // a felirat sosem vágódik.
        //
        // ⚠️ Ez a SZÉLESSÉG-eset (hány szó fér egy sorba), nem a sorközé:
        // a #2494 sorköz-javítása ezen semmit nem változtat.
        //: #2597: rögzített magasságnál is KETTŐ a felső korlát — a mért
        //: eredeti (`235707.jpg`) két sorban mutatja a „Visszavonás:
        //: <effektnév>" feliratot, és 26 képpontba a 10-es sorközzel
        //: pontosan ennyi fér. Enélkül a betűillesztés HÁROM apró sorra
        //: zsugorítaná a szöveget, ami rosszabb, mint két olvasható sor.
        maximumLineCount: pbtn.thumbSource !== "" || pbtn.rogzitett ? 2 : 2147483647
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
    // `YConstraint 1, 1, -19` — a jelvény jobb széle a CSEMPE jobb szélétől
    // 6 px-re, az alja a csempe aljától 19 px-re. Az 1920×1080-as
    // felvételen mérve: 13 × 12 px, kitöltés #379FFD, negyed-korong alak
    // (CSAK a bal felső sarka lekerekített).
    //
    // #809: A JELVÉNYEN NINCS SZÁM. Két, egymástól független forrás:
    //
    //  1. a `m_fxadorner` makró TELJES definíciója a fenti két megkötés —
    //     se szövegkötés, se betűtípus, se tartalom-tulajdonság; ilyen elem
    //     nem tud szöveget mutatni (a felirat külön elem: `m_fxlabel`);
    //  2. a csempe-kirakó (`0x005d7c20`) a jelvényen EGYETLEN műveletet
    //     végez: `vtbl[27]` megmutat vagy `vtbl[26]` elrejt
    //     (`0x005d8111`/`0x005d8116`), a láthatóság feltétele
    //     `állapot == 1` (`sete` a `0x005d7eca`-n). Semmi nem ír bele értéket.
    //
    // ⚠️ A #809 egy 08-30-i kommentje szerint a `FUN_005d7c20`-ban van egy
    // példányszám-számítás, és abból arra következtetett, hogy a jelvény azt
    // MUTATJA. A számítás megléte nem jelenti, hogy a jelvénybe kerül — a
    // makródefiníció szerint nem is kerülhet. A mechanizmus nem diagnózis.
    //
    // ⚠️ A FÜGGŐLEGES igazítás a BÉLYEGKÉP aljához megy, nem a csempéhez, és
    // ez SZÁNDÉKOS eltérés a nyers −19-től: az eredeti csempe 86 × 69
    // (a feliratsávja 18 px), ott tehát `69 − 19 = 50` PONTOSAN a bélyegkép
    // alsó éle. A mi csempénk ~87 magas (a feliratsávunk ~30 px, két sorra),
    // így a nyers −19 a feliratsáv KÖZEPÉRE esne — 15 px-rel lejjebb, mint
    // az eredetiben. A mért SZÁNDÉK a bélyegkép alsó éle; azt követjük.
    // (A csempe magasságának eltérése a #704 mérésének ismert nyitott pontja.)
    Item {
        id: pbtnBadge
        objectName: pbtn.objectName ? pbtn.objectName + "Badge" : ""
        visible: pbtn.badge && pbtn.thumbSource !== ""
        //: #809: a MÉRT vízszintes igazítás a CSEMPE jobb széléhez, −6 px —
        //: derivált érték nélkül. (A bélyegkép-dobozhoz igazítva 1 px-rel
        //: kijjebb ült: az eredetiben a jelvény 2 px-rel a bélyegkép jobb
        //: élén BELÜL van, nem simul rá.)
        anchors.right: pbtn.right
        anchors.rightMargin: 6
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
    }

    MouseArea {
        id: pbtnMouse
        anchors.fill: parent
        hoverEnabled: pbtn.tooltip.length > 0
        onClicked: pbtn.buttonClicked()
    }
    ToolTip.text: pbtn.tooltip
    ToolTip.visible: pbtn.tooltip.length > 0 && pbtnMouse.containsMouse
    ToolTip.delay: Theme.tooltipDelay
}
