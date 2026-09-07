import QtQuick
import QtQuick.Controls

// Picasa-stílusú csúszka. A SÁV színe a #2627 óta MÉRT: a `respack.yt`
// `scaleslider/sliderbase` és `editslider/sliderbase` rétege kékesszürke
// (`Theme.sliderGroove`), nem a króm semleges szürkéje — a tokenek mellett
// a Theme.qml-ben ott a képpont-mérés is.
//
// A FOGANTYÚ színátmenete továbbra is a PicasaButton nem-akcentusos
// állapotát követi (a kézikönyv 06. fejezete: „Nagyítás csúszka − + / az
// indexképek méretét szabályozza; semleges szürke fogantyú"), és a mért
// eredetivel egybevág: a `scaleslider/thumb` képpontjai is semleges
// szürkék (162…247), egyetlen kékes csatorna sincs bennük.
//
// #2641: a fogantyú közepén ott a VÉSETT vonal — egy sötét és egy
// világos, egy-egy képpont széles oszlop. A geometriát nem érinti.
//
// Csak a vezérlő maga; a bekötés (pl. a nagyítás-csúszka a Main.qml
// tálcájában) az integrátoré — #3 issue.
Slider {
    id: control

    readonly property bool isHorizontal: orientation === Qt.Horizontal

    // ------------------------------------------------------------------
    // #2170: billentyűs léptetés a MÉRT karakterekkel
    // ------------------------------------------------------------------
    //
    // Az eredeti kezelője (`0x005d2290`) a `WM_CHAR`-t nézi, és NÉGY
    // karaktert ismer: `+` (0x2b) és `=` (0x3d) növel, `−` (0x2d) és `_`
    // (0x5f) csökkent. A lépés mindkét irányban **0,02** (a konstansok
    // `0x00cf50d8` / `0x00cf50d4`, kiolvasva), és a FÓKUSZBAN lévő
    // csúszkára hat (`editslider<N>`, ahol N a panel aktuális indexe).
    //
    // ⚠️ **Miért a tartomány 2 %-a, és nem az abszolút 0,02?** Az eredeti
    // csúszkája NORMALIZÁLT (0…1), ott a 0,02 pontosan 2 %. A mi
    // csúszkáink tartománya viszont vezérlőnként más (−1…1, 0…255, 0,25…8),
    // és az abszolút 0,02 ezeken értelmetlen lenne — egy 0…255-ös skálán
    // észrevehetetlen, egy −1…1-esen viszont a mértnél nagyobb ugrás. A
    // MÉRT ARÁNYT tartjuk meg. A jegy ezt a döntést kifejezetten kérte
    // kimondani.
    readonly property real leptetesAranya: 0.02
    readonly property real billentyuLepes:
        (control.to - control.from) * control.leptetesAranya

    /** Léptetés a mért aránnyal. `irany`: +1 növel, −1 csökkent. */
    function leptesd(irany) {
        var uj = control.value + irany * control.billentyuLepes
        control.value = Math.max(control.from, Math.min(control.to, uj))
        control.moved()
    }

    //: a léptetés a FÓKUSZBAN lévő csúszkára hat — enélkül a billentyű
    //: sosem ér célba
    focusPolicy: Qt.StrongFocus

    Keys.onPressed: function (event) {
        if (event.text === "+" || event.text === "=") {
            control.leptesd(1)
            event.accepted = true
        } else if (event.text === "-" || event.text === "_") {
            control.leptesd(-1)
            event.accepted = true
        }
    }

    // #700: a sín vastagsága és a fogantyú mérete a HÍVÓ helyen felülírható.
    // Az alapértékek változatlanok (kerek, 14 px-es fogantyú, 4 px-es sín),
    // ezért minden meglévő csúszka ugyanúgy néz ki, mint eddig; az
    // effekt-paraméter alpanel viszont az eredeti Picasa arányait kéri
    // (9 px-es sín, 16×26-os álló fogantyú — `docs/specs/ui-audit-editor.md`
    // 7.5). A `handleRadius` teszi kerekké vagy szögletessé a fogantyút.
    property real grooveThickness: 4
    property real handleWidth: 14
    property real handleHeight: 14
    property real handleRadius: Math.min(handleWidth, handleHeight) / 2

    // visszafelé kompatibilis alias a NÉGYZETES fogantyú méretére
    readonly property real handleSize: Math.max(handleWidth, handleHeight)

    // #659: a méret a FOGANTYÚVAL együtt értendő. Korábban csak a sín
    // vastagsága számított, ezért a vezérlő doboza 4 képpont magas volt, a
    // 14 képpontos, KÖZÉPRE igazított fogantyú pedig alul-felül 5-5
    // képponttal kilógott belőle — a gépi elrendezés-ellenőr (#656) pontosan
    // ennyit mért. A fogantyú látszólag eddig is ott volt; csak az
    // elrendezés nem foglalta le neki a helyet, ezért a szomszédjaira lógott.
    readonly property real vastagsag: Math.max(
        control.isHorizontal ? control.handleHeight : control.handleWidth,
        control.grooveThickness)

    implicitWidth: isHorizontal ? 120 : vastagsag + leftPadding + rightPadding
    implicitHeight: isHorizontal ? vastagsag + topPadding + bottomPadding : 120

    background: Rectangle {
        x: control.leftPadding + (control.isHorizontal
                                   ? 0 : (control.availableWidth - width) / 2)
        y: control.topPadding + (control.isHorizontal
                                  ? (control.availableHeight - height) / 2 : 0)
        width: control.isHorizontal ? control.availableWidth : control.grooveThickness
        height: control.isHorizontal ? control.grooveThickness : control.availableHeight
        radius: control.grooveThickness / 2

        // #2627: a sáv színe a `respack.yt`-ből, nem szemre. A
        // `scaleslider/sliderbase` és az `editslider/sliderbase` ugyanazt
        // adja: kitöltés `#cad5e5`, felső szegély `#9aa2ae` — kékesszürke,
        // nem a króm semleges szürkéje. A tokenek a Theme.qml-ben állnak,
        // ott a mérés is.
        color: Theme.sliderGroove
        border.width: 1
        border.color: Theme.sliderGrooveBorder

        // #2627: HÁROM jelölő-vonal — a két vég és a KÖZÉP. A mérés
        // (`scaleslider/sliderbase`, 121 képpont széles) a világos
        // oszlopokat x = 5, 60, 115-nél adja, tehát a két végtől 5
        // képpontra és pontosan középen; az `editslider/sliderbase`
        // (191 széles) ugyanezt x = 8, 95, 182-nél. A közép a
        // NEUTRÁLIS állás jelzése — a finomhangoló csúszkák nullája.
        //
        // ⚠️ Ez váltotta le a korábbi „bejárt szakasz" kitöltést. Az nem
        // az eredetiből jött: a respack sávja VÉGIG egyszínű, nincs benne
        // kitöltött és üres rész. A közép-jelölő az, amit az eredeti
        // tényleg mutat.
        Repeater {
            model: 3
            Rectangle {
                readonly property real arany: index / 2
                color: Theme.sliderGrooveTick
                width: control.isHorizontal ? 1 : parent.width - 2
                height: control.isHorizontal ? parent.height - 2 : 1
                x: control.isHorizontal
                   ? Math.round(1 + arany * (parent.width - 3)) : 1
                y: control.isHorizontal
                   ? 1 : Math.round(1 + arany * (parent.height - 3))
            }
        }
    }

    handle: Rectangle {
        x: control.leftPadding + (control.isHorizontal
               ? control.visualPosition * (control.availableWidth - width)
               : (control.availableWidth - width) / 2)
        y: control.topPadding + (control.isHorizontal
               ? (control.availableHeight - height) / 2
               : (1 - control.visualPosition) * (control.availableHeight - height))
        implicitWidth: control.handleWidth
        implicitHeight: control.handleHeight
        radius: control.handleRadius
        border.width: 1
        border.color: control.pressed ? "#8f8f8f" : "#b5b5b5"
        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: control.pressed ? "#d8d8d8" : "#fdfdfd"
            }
            GradientStop {
                position: 1.0
                color: control.pressed ? "#c8c8c8" : "#e4e4e4"
            }
        }
        opacity: control.enabled ? 1.0 : 0.55

        // #2641: a KÖZÉPRE VÉSETT vonal. A `respack.yt` mindkét fogantyú-
        // rétege ugyanazt adja (`scaleslider/thumb` 16 × 22 és
        // `editslider/thumb` 16 × 26): a rajz 14 képpont széles, és a
        // vésés a 6. (érték 199, sötét) meg a 7. (érték 244, világos)
        // oszlop — vagyis a rajz vízszintes közepére esik, a sötét oldal
        // BALRA, a fény alulról. Függőlegesen mindkét rétegen pontosan
        // 5-5 képpont marad ki felül és alul (19 tömör sorból az 5…13.,
        // 23-ból az 5…17.).
        //
        // ⚠️ EGY kimondott eltérés az eredetitől: a mi fogantyúnk doboza
        // a RÉTEG magasságát viszi (22 ill. 26 — így mérte a #2627/#2631),
        // az eredeti lágy árnyéka viszont ott van a réteg alján, és mi azt
        // nem rajzoljuk. Ezért a szimmetrikus 5-5 képpontos behúzást
        // tartjuk meg: az árnyékhoz igazított 5/8-as behúzás egy árnyék
        // NÉLKÜLI fogantyún szemre elcsúszottnak látszana.
        readonly property real vesesBehuzas: 5
        readonly property real vesesHossz: (control.isHorizontal
            ? height : width) - 2 * vesesBehuzas

        Repeater {
            model: 2
            Rectangle {
                // 0 = a vésés sötét oldala, 1 = a világos
                color: index === 0
                       ? Theme.sliderHandleGrooveDark
                       : Theme.sliderHandleGrooveLight
                // a fogantyú közepére eső KÉT képpont: a sötét a
                // középvonaltól balra (fent), a világos rajta
                width: control.isHorizontal ? 1 : parent.vesesHossz
                height: control.isHorizontal ? parent.vesesHossz : 1
                x: control.isHorizontal
                   ? Math.round(parent.width / 2) - 1 + index
                   : parent.vesesBehuzas
                y: control.isHorizontal
                   ? parent.vesesBehuzas
                   : Math.round(parent.height / 2) - 1 + index
                // egy 12 képpontnál alacsonyabb fogantyún a vésés már nem
                // fér ki értelmesen — inkább ne legyen, mint hogy a
                // fogantyú két végét összekösse
                visible: parent.vesesHossz >= 2
            }
        }
    }
}
