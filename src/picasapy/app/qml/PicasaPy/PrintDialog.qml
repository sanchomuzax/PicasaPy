import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Nyomtatás (#32 RÉSZLEGES kör, bekötve a #1472-ben) — a `Fájl ▸
// Nyomtatás…` (Ctrl+P) és a képtálca „Nyomtatás" gombja ezt nyitja.
//
// ⚠️ Ez NEM a Picasa teljes nyomtatási sablonrendszere (`print.fen` /
// `reviewprint.fen`, a `ytPrintSizes` mind a 17 mérete, állítható margó).
// KÉT elrendezést kínál: „képenként egy lap" és — #1590 óta — „indexkép"
// (több bélyegkép egy lapon). Az eredetiben az indexkép sem külön ablak,
// hanem NYOMTATÁSI MÉRET (`ytPrintSizes::eContact` = „Indexképek"), ezért
// itt is elrendezés-választó, nem másik párbeszéd.
//
// A nyomtató-választó SAJÁT lista, nem a natív `QPrintDialog`: az app
// `QGuiApplication`-t használ, a natív párbeszéd viszont `QWidget`-alapú,
// tehát meg sem nyitható (ld. a `print_controller.py` docstringjét). A
// lista ELSŐ tétele a PDF-fájlba nyomtatás — enélkül a párbeszéd egy
// nyomtató nélküli gépen semmit nem tudna csinálni.
Window {
    id: printWindow
    objectName: "printDialog"
    title: qsTr("Print...")
    modality: Qt.ApplicationModal

    //: #3544: a Shift+F1 fejezete. Külön ablakos, modális párbeszéd: a
    //: főablak súgója mögé kerülne, ezért a `WindowHelp` a párbeszéd FÖLÖTT,
    //: külön ablakban nyitja.
    property string helpTopic: "features/nyomtatas.md"
    WindowHelp {
        id: printWindowHelp
        tema: printWindow.helpTopic
    }
    width: 480
    height: alapMagassag
    // #4795: a kezdőmagasság a tartalomhoz igazodik, de legfeljebb a
    // képernyő elérhető magassága (kis ráhagyással). Nyitáskor számoljuk,
    // hogy a felhasználó utólagos átméretezését ne írja felül kötés.
    readonly property int kepernyoRahagyas: 48
    readonly property int keretMargo: 12
    readonly property int alapMagassag: 420
    // A nyitás utáni elrendezés lecsengéséig (az utolsó magasság-változás
    // után `meretezesIdozito.interval` ms) a méretezés függőben van.
    property bool meretezesFuggoben: false
    Timer {
        id: meretezesIdozito
        interval: 100
        onTriggered: {
            printWindow.meretezesFuggoben = false
            printWindow.height = printWindow.kezdoMagassag()
        }
    }
    Connections {
        target: printContent
        function onImplicitHeightChanged() {
            if (printWindow.meretezesFuggoben)
                meretezesIdozito.restart()
        }
    }
    Connections {
        target: printStatusBox
        function onImplicitHeightChanged() {
            if (printWindow.meretezesFuggoben)
                meretezesIdozito.restart()
        }
    }
    function kezdoMagassag() {
        // ⚠️ csak az ELSŐ elrendezés UTÁN hívandó (ld. `meretezesIdozito`):
        // rejtett ablakban a Layout nem rendeződik újra, az implicitHeight
        // elavult (az előző nyitás/mód tartalmát tükrözi).
        var kell = printContent.implicitHeight + printStatusBox.implicitHeight
                   + printButtonRow.implicitHeight
                   + 2 * keretMargo + printFrame.spacing
                   + (printStatusBox.visible ? printFrame.spacing : 0)
        var plafon = Math.max(minimumHeight,
                              Screen.desktopAvailableHeight - kepernyoRahagyas)
        return Math.round(Math.min(Math.max(alapMagassag, kell), plafon))
    }
    minimumWidth: 420
    minimumHeight: 380
    color: Theme.canvasBg

    // #305 mintája: null-őr. A vezérlőt az `application.py` regisztrálja;
    // a menüsávot/ablakot önmagában betöltő próbák nem.
    // ⚠️ A név SZÁNDÉKOSAN nem `ctl` (#1476): azt a rövidítést öt másik
    // QML-fájl is használja, mindegyik MÁS vezérlőre. A képesség-őr az
    // álneveket ma globálisan oldja fel, tehát egy hatodik jelentés
    // kétértelművé tenné, és az őr — konzervatívan — mind a hat fájl
    // hivatkozásait eldobná. Mérve: a `ctl` alakkal 441-ről 424-re esett
    // az élő hivatkozások száma. Az őr saját hibája (külön jegy), de a
    // beszédesebb név itt amúgy is jobb.
    readonly property var printCtl:
        (typeof printController !== "undefined") ? printController : null

    // a nyomtatandó sorok (a `controller.photos` modell sorindexei) — a
    // megnyitáskor rögzülnek, hogy a párbeszéd alatt módosuló kijelölés ne
    // írja át a feladatot
    property var rows: []
    //: #1819: KÉPENKÉNTI példányszám (`addprintsbutton`/`subprintsbutton`,
    //: „Add another copy of each Photo to be printed"). NEM a nyomtató saját
    //: példányszám-mezője: a +/− minden képhez ad egy további másolatot,
    //: tehát két kép × két példány négy lap.
    property int copies: 1
    //: #1819: a lapozó előnézet állapota. A lapszámot a vezérlő adja
    //: (`printPageCount`) — csak a DEKÓDOLHATÓ képek számítanak, tehát a
    //: kihagyott videó/sérült fájl lapot sem kap.
    property int previewPage: 0
    property int previewPageCount: 0
    //: #3712: a darabszám-sor EZT mondja — méret szerinti nyomtatásnál a
    //: `previewPageCount`-tal azonos, indexképnél a `contactPageCount()`-ból
    //: jön. Külön property, mert a `previewPageCount` indexkép-módban
    //: mindig 0 (nincs lapozható előnézet), a darabszám-sornak viszont
    //: MINDKÉT módban a valódi lapszámot kell mondania.
    property int printPageCount: 0
    property string previewSource: ""
    // a rendszer nyomtatóinak neve; a választóban EGGYEL eltolva jelennek
    // meg, mert a 0. tétel a PDF-fájl
    property var printers: []
    // #4318: az options.fen öt, felhasználó által kiosztható gyorsmérete.
    property var printSizePresetIds: []
    // ⚠️ EGYETLEN igazságforrás: amit a választó MUTAT, oda megy a feladat.
    // Korábban ez saját, írható property volt, a `ComboBox.currentIndex`-szel
    // egyirányban szinkronizálva — és a Qt a modell rövidülésekor
    // IMPERATÍVAN visszaállítja a `currentIndex`-et (felülütve a kötést),
    // a saját property viszont a régi értéken maradt. Ha közben egy
    // hálózati nyomtató lecsatlakozott, a párbeszéd „PDF-fájlba"-t mutatott,
    // a `printRows` viszont lefutott az ALAPÉRTELMEZETT nyomtatóra: papír
    // ment ki, magyarázat nélkül. A származtatott property ezt kizárja.
    readonly property int printerIndex: printerBox.currentIndex
    readonly property bool pdfSelected: printWindow.printerIndex === 0
    readonly property string printerName:
        printWindow.pdfSelected
        || printWindow.printerIndex - 1 >= printWindow.printers.length
            ? "" : printWindow.printers[printWindow.printerIndex - 1]
    property string pdfTarget: ""

    //: #2368: a pillanatnyi lapbeállítás emberi olvasásra. NEM kötés: a
    //: `paperInfo()` a vezérlő mentett elrendezését olvassa, ami a
    //: nyomtató oldalbeállítójában változhat — ezért kimondott
    //: frissítéssel jár (nyomtatóváltás és oldalbeállítás után).
    property string papiradat: ""
    function frissitsdAPapiradatot() {
        if (typeof printController !== "undefined" && printController)
            printWindow.papiradat = printController.paperInfo(printWindow.printerName)
    }
    onPrinterNameChanged: printWindow.frissitsdAPapiradatot()
    Component.onCompleted: printWindow.frissitsdAPapiradatot()

    property string fitMode: "fit"          // PrintFitMode.FIT / .FILL
    property string orientation: "auto"     // PrintOrientation

    // #1590: indexkép-elrendezés (több bélyegkép egy lapon). A rács
    // oszlopszáma a felhasználóé — az eredeti nyomtatási előnézetéből ez
    // nem volt kiolvasható, a `stringres`-ben sincs rá kulcs (DÖNTÉS).
    property bool contactSheet: false
    property int contactColumns: 4

    //: #1401: az Útlevélkép nyitotta a nézetet — a nyomtatandó kép a
    //: kivágott, ideiglenes fájl (`printController.setPassportSource`), a
    //: méret `ePassport`. Az élő mérés (picasa-colab-jobs #54) szerint
    //: ilyenkor Crop to Fit, 1 példány, és egyik kész méret sincs
    //: kijelölve. A felhasználó ELŐZŐ illesztését és példányszámát a
    //: következő sima nyitás visszakapja.
    property bool passport: false
    property var mentettBeallitas: null

    // #1782: a nyomatméret (`0x00743700`) és a hozzá tartozó
    // minőség-összegzés. A méret TARTÓS — az eredetiben a
    // `Preferences\PrintLastSize` őrzi; nálunk a vezérlő teszi el. Ez a
    // kezdőérték csak a nyisd()-előtti pillanatra vonatkozik — a
    // `nyisd()` minden megnyitáskor felülírja a vezérlő `printSize()`-
    // ával (#3733: az alapállás Teljes oldal, ld. ott).
    property string printSize: "TELJES_OLDAL"
    //: #1961: a feliratok a HIVATALOS `ytPrintSizes::` szövegcsaládból
    //: valók (`stringres` 3478–3494), nem saját fogalmazás. A készletet a
    //: vezérlő adja a felület nyelve szerint (magyarul a metrikus készlet),
    //: ezért a felirat nem pozíció, hanem AZONOSÍTÓ szerint jön — a
    //: korábbi rögzített tömb a metrikus készleten minden tételre rossz
    //: szöveget adott volna.
    //:
    //: ⚠️ A `TELJES_OLDAL` felirata magyarul is „FullPage": az eredeti
    //: szövegtár `eFullPage` sora mindkét nyelven ezt adja. Nem
    //: fordítjuk le magunktól — a hűség erősebb, mint a szépség.
    readonly property var printSizeLabelById: ({
        "M3X4": qsTr("3 x 4"),
        "M3_5X5": qsTr("3.5 x 5"),
        "M4X5": qsTr("4 x 5"),
        "M4X6": qsTr("4 x 6"),
        "M5X7": qsTr("5 x 7"),
        "M8X10": qsTr("8 x 10"),
        "TARCA": qsTr("Wallet"),
        "M5X8CM": qsTr("5 x 8 cm"),
        "M9X13CM": qsTr("9 x 13 cm"),
        "M10X15CM": qsTr("10 x 15 cm"),
        "M13X18CM": qsTr("13 x 18 cm"),
        "M15X20CM": qsTr("15 x 20 cm"),
        "M20X25CM": qsTr("20 x 25 cm"),
        "TELJES_OLDAL": qsTr("FullPage"),
        //: `ytPrintSizes::ePassport` — csak az Útlevélkép parancs állítja be
        //: (#1401), a kész méretek listájában nincs
        "PASSPORT": qsTr("Passport"),
        //: #3712: az eredetiben az Indexképek (`ytPrintSizes::eContact`) a
        //: méretlista egyik tétele — nem külön kapcsoló. A `CONTACT` a
        //: vezérlőtől kapott `printSizeIds`-en KÍVÜLI, csak a QML-nek
        //: ismert azonosító (a `NyomatMeret`-nek nincs, és nem is lehet
        //: ilyen tagja — az indexkép nem CELLAMÉRET, ld. #1961).
        //: #3712-review: a felirat a HIVATALOS szöveg ("Contact Sheet",
        //: `stringres` 3491) — a korábbi kisbetűs "Contact sheet" saját
        //: fogalmazás volt.
        "CONTACT": qsTr("Contact Sheet")
    })
    property var printSizeIds: []
    //: #4280: az „Ellenőrzés" gomb eredménye — minden kép {name, dpi,
    //: qualityCode} adata, a legrosszabbal elöl.
    property var reviewList: []
    property bool reviewOpen: false
    //: A választó modellje: a vezérlőtől kapott azonosítók feliratai.
    //: Ismeretlen azonosítónál MAGA az azonosító látszik — néma üres sor
    //: helyett legyen látható, hogy felirat hiányzik.
    readonly property var printSizeLabels: printWindow.printSizeIds.map(
        function (azonosito) {
            return printWindow.printSizeLabelById[azonosito] || azonosito
        })
    //: {smallest, small, total, ready, threshold, bestThreshold,
    //: goodThreshold} — a vezérlőtől
    property var quality: ({})

    function frissitsdAMinoseget() {
        if (!printWindow.printCtl) return
        printWindow.quality = printWindow.printCtl.printQuality(
            printWindow.rows, printWindow.printSize)
        printWindow.frissitsdAzElonezetet()
        if (printWindow.reviewOpen) {
            printWindow.reviewList = printWindow.printCtl.reviewPictures(
                printWindow.rows, printWindow.printSize)
            printReviewList.currentIndex = printWindow.reviewList.length > 0 ? 0 : -1
        }
    }

    function removeReviewRows(eltavolitandoSorok) {
        var maradek = []
        for (var i = 0; i < printWindow.rows.length; ++i) {
            var sor = Number(printWindow.rows[i])
            if (eltavolitandoSorok.indexOf(sor) < 0)
                maradek.push(sor)
        }
        printWindow.rows = maradek
        printWindow.frissitsdAMinoseget()
    }

    function removeSelectedReviewPicture() {
        var index = printReviewList.currentIndex
        if (index < 0 || index >= printWindow.reviewList.length) return
        var kep = printWindow.reviewList[index]
        var kepSor = Number(kep.row)
        if (kepSor >= 0) {
            printWindow.removeReviewRows([kepSor])
        } else {
            printWindow.printCtl.excludeReviewPictures([Number(kep.recordId)])
            printWindow.frissitsdAMinoseget()
        }
    }

    function removeLowQualityReviewPictures() {
        var sorok = []
        var rekordAzonositok = []
        for (var i = 0; i < printWindow.reviewList.length; ++i) {
            var kep = printWindow.reviewList[i]
            if (Number(kep.qualityCode) !== 0) continue
            var sor = Number(kep.row)
            if (sor >= 0) sorok.push(sor)
            else rekordAzonositok.push(Number(kep.recordId))
        }
        if (rekordAzonositok.length > 0)
            printWindow.printCtl.excludeReviewPictures(rekordAzonositok)
        if (sorok.length > 0) printWindow.removeReviewRows(sorok)
        else printWindow.frissitsdAMinoseget()
    }

    function acceptReviewAndPrint() {
        if (Number(printWindow.quality.total || 0) === 0) return
        printWindow.reviewOpen = false
        printWindow.startPrint()
    }

    //: #1819: az előnézeti lap újrarajzolása. Minden állítás (méret,
    //: illesztés, tájolás, példányszám, lapozás) ide fut be — így az
    //: előnézet SOSEM mutathat mást, mint amit a nyomtatás adna.
    //:
    //: A cache-buster (`?v=`) nem díszítés: a Qt a képeket URL szerint
    //: gyorstárazza, tehát ugyanarra a fájlnévre írt új tartalom a RÉGI
    //: képpontokkal jelenne meg (a #1186 hibaosztálya).
    property int elonezetValtozat: 0
    function frissitsdAzElonezetet() {
        if (!printWindow.printCtl) {
            printWindow.previewPageCount = 0
            printWindow.previewSource = ""
            printWindow.printPageCount = 0
            return
        }
        // #3712: az indexképnek nincs lapozható előnézete — de a
        // darabszám-sornak MÉGIS a valódi lapszámot kell mondania, nem
        // ígérhet olyat, amit a nyomtatás nem tesz meg.
        if (printWindow.contactSheet) {
            printWindow.previewPageCount = 0
            printWindow.previewSource = ""
            printWindow.printPageCount = printWindow.printCtl.contactPageCount(
                printWindow.rows, printWindow.contactColumns,
                printWindow.printerName)
            return
        }
        // #3647: a lapszámot UGYANAZZAL a tájolással/nyomtatóval kérjük,
        // mint amivel a `renderPreviewPage` lentebb ténylegesen rajzol —
        // különben a lapozó számot mutatna, a rajzoló pedig mást.
        var lapok = printWindow.printCtl.printPageCount(
            printWindow.rows, printWindow.copies, printWindow.orientation,
            printWindow.printerName)
        printWindow.previewPageCount = lapok
        printWindow.printPageCount = lapok
        if (lapok <= 0) {
            printWindow.previewSource = ""
            return
        }
        if (printWindow.previewPage >= lapok)
            printWindow.previewPage = lapok - 1
        if (printWindow.previewPage < 0)
            printWindow.previewPage = 0
        var cel = printWindow.elonezetiFajl()
        var ok = printWindow.printCtl.renderPreviewPage(
            printWindow.rows, printWindow.fitMode, printWindow.orientation,
            printWindow.copies, printWindow.previewPage, cel,
            printWindow.printerName)
        printWindow.elonezetValtozat += 1
        //: A cél MÁR URL (a vezérlő a `QUrl.fromLocalFile`-on át adja,
        //: #1019) — kézzel semmit nem fűzünk elé, csak a gyorstár-törő
        //: lekérdezést utána.
        printWindow.previewSource =
            ok ? cel + "?v=" + printWindow.elonezetValtozat : ""
    }

    //: Az előnézeti PNG helye URL-ként. Egyetlen fájl, felülírva — a
    //: párbeszéd életciklusán túl nincs rá szükség, és a lapozás így nem
    //: szemetel. ⚠️ A vezérlő adja, `QUrl.fromLocalFile`-on át (#1019).
    function elonezetiFajl() {
        return printWindow.printCtl.previewImageUrl()
    }

    property string lastError: ""
    property string lastResult: ""
    // #3016: a haladás-jelzés állapota. `printTotalPages === 0` = nincs futó
    // feladat (ilyenkor a sor sem látszik).
    property int printDonePages: 0
    property int printTotalPages: 0
    // a feladatból kimaradt képek nevei (videó/RAW: a `QImage` nem nyitja
    // meg őket, a rácsban viszont látszanak) — ld. `printSkipped`
    property var lastSkipped: []

    readonly property bool canPrint:
        printWindow.printCtl !== null
        && printWindow.rows.length > 0
        && (!printWindow.pdfSelected || printWindow.pdfTarget.length > 0)

    //: #1401: az útlevél-mód be- vagy kikapcsolása a vezérlőn ÉS a nézeten.
    //: Bekapcsoláskor a felhasználó illesztése és példányszáma félre-
    //: kerül; a következő sima nyitás visszaadja őket.
    function valtsdAzUtlevelet(utlevelUrl) {
        if (printWindow.printCtl)
            printWindow.printCtl.clearPassportSource()
        var be = utlevelUrl.length > 0 && printWindow.printCtl !== null
                 && printWindow.printCtl.setPassportSource(utlevelUrl)
        if (be) {
            if (printWindow.mentettBeallitas === null)
                printWindow.mentettBeallitas = {
                    fitMode: printWindow.fitMode, copies: printWindow.copies }
            printWindow.fitMode = "fill"
            printWindow.copies = 1
        } else if (printWindow.mentettBeallitas !== null) {
            printWindow.fitMode = printWindow.mentettBeallitas.fitMode
            printWindow.copies = printWindow.mentettBeallitas.copies
            printWindow.mentettBeallitas = null
        }
        printWindow.passport = be
    }

    function valasszNyomatmeretet(azonosito) {
        if (!azonosito || !printWindow.printCtl) return
        if (azonosito === "CONTACT") {
            printWindow.contactSheet = true
            printWindow.printSize = azonosito
            printSizeBox.currentIndex = printWindow.printSizeIds.indexOf(azonosito)
            printWindow.frissitsdAMinoseget()
            return
        }
        if (!printWindow.printCtl.setPresetPrintSize(azonosito)) return
        printWindow.printCtl.setPrintSize(azonosito)
        printWindow.contactSheet = false
        printWindow.printSize = azonosito
        printSizeBox.currentIndex = printWindow.printSizeIds.indexOf(azonosito)
        printWindow.frissitsdAMinoseget()
    }

    //: #1401: a bezárt nézet nem hagyhatja a vezérlőt útlevél-módban —
    //: a következő nyomtatás különben a kivágott képet nyomtatná.
    onVisibleChanged: {
        if (printWindow.visible) {
            printWindow.meretezesFuggoben = true  // #4795
            meretezesIdozito.restart()
        }
        if (!printWindow.visible && printWindow.printCtl)
            printWindow.printCtl.clearPassportSource()
    }

    // #1590: a `Mappa ▸ Bélyegképek nyomtatása…` belépési pontja — ugyanaz
    // a párbeszéd, indexkép-móddal nyitva (#3712: a méretlista egyik
    // tétele, nem külön elrendezés-választó)
    function openForContactSheet(targetRows) {
        printWindow.nyisd(targetRows, "", true)
    }

    function openForRows(targetRows) {
        printWindow.nyisd(targetRows, "", false)
    }

    //: #1401: az Útlevélkép belépési pontja — a `url` a kivágott kép.
    function openForPassport(url) {
        printWindow.nyisd([0], url, false)
    }

    function nyisd(targetRows, utlevelUrl, contactMode) {
        printWindow.valtsdAzUtlevelet(utlevelUrl)
        if (printWindow.printCtl)
            printWindow.printCtl.clearReviewExclusions()
        printWindow.rows = targetRows ? targetRows : []
        printWindow.reviewOpen = false
        printWindow.reviewList = []
        // ⚠️ #1590/#3712: az elrendezés NEM élheti túl a bezárást — ezért a
        // MEGNYITÁS módja dönt (paraméter), nem egy külön, utólagos
        // állítás. Enélkül a Ctrl+P legközelebb szó nélkül indexképet
        // nyomtatna, a felhasználó pedig méret szerintit vár.
        printWindow.contactSheet = !!contactMode
        // #1782: a megjegyzett méret visszatöltése, majd a minőség-mérés
        if (printWindow.printCtl) {
            // #3712: a `CONTACT` (Indexképek) a méretlista egyik tétele —
            // a vezérlő `printSizes()`-e csak a valódi `NyomatMeret`-eket
            // adja (#1961), a QML fűzi hozzá ezt az egyet.
            printWindow.printSizeIds = printWindow.printCtl.printSizes().concat(["CONTACT"])
            printWindow.printSizePresetIds = printWindow.printCtl.printSizePresets()
            printWindow.printSize = printWindow.passport
                ? "PASSPORT" : printWindow.printCtl.printSize()
        }
        printSizeBox.currentIndex = printWindow.printSizeIds.indexOf(
            printWindow.contactSheet ? "CONTACT" : printWindow.printSize)
        printWindow.previewPage = 0
        printWindow.frissitsdAMinoseget()
        printWindow.lastResult = ""
        printWindow.lastSkipped = []
        // ⚠️ a célfájl NEM élheti túl a bezárást. Ha megmaradna, a
        // következő nyitáskor a gomb azonnal élő lenne, a `FileDialog` meg
        // sem nyílna — tehát a Qt felülírás-kérdése sem —, és az előző PDF
        // kérdés nélkül elveszne.
        printWindow.pdfTarget = ""
        // #1472: ha a Qt nyomtatás-modulja hiányzik (Debian/Ubuntu külön
        // csomag, ld. `application.py`), a párbeszéd NEM néma: kimondja,
        // miért nem tud dolgozni, ahelyett hogy szürke gombot mutatna
        // ⚠️ a tulajdonos NEM programozó: a puszta „hiányzik egy modul"
        // neki zsákutca. Az üzenet ezért kimondja a telepítő parancsot is.
        printWindow.lastError = printWindow.printCtl
            ? "" : qsTr("Printing is unavailable: the Qt print support "
                        + "module is missing. On Debian/Ubuntu you can "
                        + "install it with: "
                        + "sudo apt install python3-pyside6.qtprintsupport")
        printWindow.printers = printWindow.printCtl ? printWindow.printCtl.listPrinters() : []
        printOptionsPanel.visible = false
        printWindow.visible = true
        printOptionsPanel.closeTextColorPicker()
    }

    function startPrint() {
        if (!printWindow.printCtl) return
        printWindow.lastError = ""
        printWindow.lastResult = ""
        printWindow.lastSkipped = []
        // a gomb ilyenkor szürke, tehát ide kattintással nem lehet eljutni —
        // de a néma elutasítás annyira visszatérő hibánk, hogy a
        // programozott hívás se maradhat szótlan
        if (printWindow.rows.length === 0
                || Number(printWindow.quality.total || 0) === 0) {
            printWindow.lastError = qsTr("No pictures to print.")
            return
        }
        if (printWindow.pdfSelected) {
            if (printWindow.pdfTarget.length === 0) {
                printWindow.lastError = qsTr("Choose the target file.")
                return
            }
            if (printWindow.contactSheet) {
                printWindow.printCtl.renderContactSheetPdf(
                    printWindow.rows, printWindow.contactColumns,
                    printWindow.pdfTarget)
                return
            }
            printWindow.printCtl.renderPrintPreviewPdf(
                printWindow.rows, printWindow.fitMode,
                printWindow.orientation, printWindow.pdfTarget,
                printWindow.copies)
            return
        }
        if (printWindow.contactSheet) {
            printWindow.printCtl.printContactSheet(
                printWindow.rows, printWindow.printerName,
                printWindow.contactColumns)
            return
        }
        printWindow.printCtl.printRows(
            printWindow.rows, printWindow.printerName,
            printWindow.fitMode, printWindow.orientation, printWindow.copies)
    }

    Connections {
        target: printWindow.printCtl
        function onPrintFinished(target) {
            printWindow.lastError = ""
            printWindow.lastResult = target
            // a feladat véget ért: a haladás-sor eltűnik
            printWindow.printTotalPages = 0
            printWindow.printDonePages = 0
        }
        function onPrintFailed(message) {
            printWindow.lastResult = ""
            printWindow.lastError = message
            printWindow.printTotalPages = 0
            printWindow.printDonePages = 0
        }
        function onPrintSkipped(names) {
            printWindow.lastSkipped = names
        }
        // #3016: laponkénti haladás a nyomtatás közben
        function onPrintProgress(done, total) {
            printWindow.printDonePages = done
            printWindow.printTotalPages = total
        }
    }

    // #4795: a gombsor (Súgó/Nyomtatás/Bezárás) az ablak alján RÖGZÍTETT, a
    // fölötte lévő tartalom görgethető — kis képernyőn sem lóg ki a gomb.
    ColumnLayout {
        id: printFrame
        anchors.fill: parent
        anchors.margins: printWindow.keretMargo
        spacing: 10

        Flickable {
            id: printContentFlick
            objectName: "printContentFlick"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: printContent.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.VerticalFlick
            ScrollBar.vertical: ScrollBar {
                id: printScrollBar
                policy: size < 1.0 ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
            }

        ColumnLayout {
        id: printContent
        width: printContentFlick.width - (printScrollBar.visible ? printScrollBar.width : 0)
        spacing: 10

        Text {
            objectName: "printSelectionText"
            Layout.fillWidth: true
            //: #3712: a felirat NEM ígéri, hogy hány kép kerül egy lapra —
            //: azt a tényleges lapszám mondja meg (méret szerinti
            //: nyomtatásnál a rácselrendező, indexképnél a
            //: `contactPageCount()` adja, ld. `frissitsdAzElonezetet()`).
            //: #3712-review: a lapszám `%n`-es TÖBBES SZÁM — korábban a
            //: szó szerinti "pages" mindig többes számban állt, tehát egy
            //: lapnál is "(1 pages)" jelent meg.
            text: qsTr("Pictures to print: %1 (%n page(s))", "",
                       printWindow.printPageCount)
                  .arg(printWindow.rows.length)
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        // #4608: nyomtató nélküli gépen kimondja, mit kell tenni. Az
        // eredeti őre (`IDS_MUST_INSTALL_PRINTER`) ugyanezt mondja. A
        // PDF-cél a választóban marad, ezért ez tájékoztat, nem tilt.
        // A tartalom tetején van: kis ablakban a nyomtatóválasztóhoz
        // görgetni kell, a figyelmeztetésnek viszont azonnal látszania kell.
        Text {
            objectName: "printNoPrinterText"
            Layout.fillWidth: true
            visible: !!printWindow.printCtl && printWindow.printers.length === 0
            //: IDS_MUST_INSTALL_PRINTER — a nyomtató-őr üzenete
            text: qsTr("A printer must be installed in order to print.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
            wrapMode: Text.WordWrap
        }

        // -- szegély és felirat (#1780) -----------------------------------
        PicasaButton {
            id: printOptionsButton
            objectName: "printOptionsButton"
            Layout.fillWidth: true
            text: qsTr("Border and Text Options")
            enabled: printWindow.printCtl !== null
            hoverEnabled: true
            onClicked: printOptionsPanel.showOptions()

            ToolTip {
                objectName: "printOptionsTooltip"
                parent: printOptionsButton
                text: qsTr("Configure borders and text for Photos to be printed")
                visible: printOptionsButton.hovered
                delay: Theme.tooltipDelay
            }
        }

        // -- nyomatméret + minőség-ellenőrzés (#1782) ---------------------
        // Az eredeti panel a választott mérethez kiszámolja minden kép
        // effektív felbontását, és nyomtatás ELŐTT szól, ha valamelyik túl
        // kicsi. Enélkül egy 640×480-as kép szó nélkül ment ki 8×10-re.
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: qsTr("Print size:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            //: #3712: EGYETLEN méretlista — az eredeti szerkezet szerint az
            //: Indexképek (`ytPrintSizes::eContact`) a méretlista egyik
            //: tétele, nem külön elrendezés-választó. A `printSizeIds`
            //: ezért a vezérlő méretei UTÁN a QML-only `CONTACT` azonosítót
            //: is tartalmazza (ld. `nyisd()`).
            PicasaComboBox {
                id: printSizeBox
                objectName: "printSizeBox"
                Layout.fillWidth: true
                model: printWindow.printSizeLabels
                currentIndex: printWindow.printSizeIds.indexOf(
                    printWindow.contactSheet ? "CONTACT" : printWindow.printSize)
                //: #1401: az Útlevél nincs a kész méretek között — ilyenkor
                //: egyik tétel sincs kijelölve, a mező a méret nevét mutatja
                displayText: currentIndex < 0
                    ? (printWindow.printSizeLabelById[printWindow.printSize] || "")
                    : currentText
                onActivated: {
                    var azonosito = printWindow.printSizeIds[currentIndex]
                    if (!azonosito) return
                    if (azonosito === "CONTACT") {
                        // #3712: az Indexképek nem CELLAMÉRET — a
                        // `setPrintSize` a #1961 készletén kívüli nevet
                        // úgyis elutasítaná, ezért nem is hívjuk.
                        printWindow.contactSheet = true
                    } else {
                        printWindow.valasszNyomatmeretet(azonosito)
                    }
                    if (azonosito === "CONTACT")
                        printWindow.frissitsdAMinoseget()
                }
            }

            // #4318 / options.fen: a beállítás öt nyomtatható méretgombhoz
            // rendel méretet; ezek a gombok közvetlenül a vezérlőn választják
            // ki és mentik az adott nyomatméretet.
            RowLayout {
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    objectName: "printSizePresetRepeater"
                    model: printWindow.printSizePresetIds.length
                    delegate: PicasaButton {
                        objectName: "printPresetSize" + index
                        Layout.fillWidth: true
                        text: printWindow.printSizeLabelById[
                            printWindow.printSizePresetIds[index]]
                        enabled: printWindow.printCtl !== null
                            && printWindow.printCtl.canUsePrintSizePreset(
                                printWindow.printSizePresetIds[index])
                        onClicked: printWindow.valasszNyomatmeretet(
                            printWindow.printSizePresetIds[index])
                    }
                }
                PicasaButton {
                    objectName: "printPresetFullPage"
                    Layout.fillWidth: true
                    text: printWindow.printSizeLabelById["TELJES_OLDAL"]
                    enabled: printWindow.printCtl !== null
                    onClicked: printWindow.valasszNyomatmeretet("TELJES_OLDAL")
                }
            }

            // #1590/#3712: az indexkép rácsának oszlopszáma — csak akkor
            // látszik, ha a fenti listában az Indexképek van kijelölve.
            RowLayout {
                Layout.fillWidth: true
                visible: printWindow.contactSheet
                spacing: 6
                Text {
                    text: qsTr("Columns:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                SpinBox {
                    objectName: "printContactColumnsBox"
                    from: 1
                    to: 10
                    value: printWindow.contactColumns
                    onValueModified: {
                        printWindow.contactColumns = value
                        printWindow.frissitsdAzElonezetet()
                    }
                }
                Item { Layout.fillWidth: true }
            }

            // -- méret szerinti nyomtatás kizárólagos vezérlői -----------
            // Az indexképnél nincs értelme: ott MINDIG a teljes kép
            // látszik a cellában, és nincs képenkénti minőség-ellenőrzés.
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                visible: !printWindow.contactSheet
                // #1819: KÉPENKÉNTI példányszám. A felirat az `IDS_COPIES`
                // (`ThumbUIPrint::PrintCount`); a két gomb az
                // `addprintsbutton` és a `subprintsbutton`.
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        text: qsTr("Copies of each picture:")
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                    }
                    PicasaButton {
                        objectName: "printCopiesMinusButton"
                        text: "–"
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 22
                        //: Egy alá nem mehet: nulla példány nem nyomtatás,
                        //: hanem a párbeszéd értelmetlen állapota.
                        enabled: printWindow.copies > 1
                        onClicked: {
                            printWindow.copies -= 1
                            printWindow.frissitsdAzElonezetet()
                        }
                    }
                    Text {
                        objectName: "printCopiesText"
                        text: printWindow.copies
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                        Layout.minimumWidth: 20
                        horizontalAlignment: Text.AlignHCenter
                    }
                    PicasaButton {
                        objectName: "printCopiesPlusButton"
                        text: "+"
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 22
                        //: Buboréksúgó az eredetiből (`addprintsbutton`).
                        ToolTip.text: qsTr(
                            "Add another copy of each Photo to be printed")
                        ToolTip.visible: hovered
                        ToolTip.delay: Theme.tooltipDelay
                        onClicked: {
                            printWindow.copies += 1
                            printWindow.frissitsdAzElonezetet()
                        }
                    }
                    Item { Layout.fillWidth: true }
                }

                // #1819: LAPOZHATÓ előnézet. A párbeszédnek eddig egyáltalán
                // nem volt előnézete — a felhasználó vakon nyomott nyomtatást.
                ColumnLayout {
                    objectName: "printPreviewBlock"
                    Layout.fillWidth: true
                    spacing: 4
                    visible: printWindow.previewPageCount > 0
                    Image {
                        objectName: "printPreviewImage"
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredHeight: 150
                        Layout.preferredWidth: 150
                        fillMode: Image.PreserveAspectFit
                        source: printWindow.previewSource
                        asynchronous: true
                        //: A gyorstár KIKAPCSOLVA: ugyanaz a fájlnév kap új
                        //: tartalmat minden lapozáskor.
                        cache: false
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 8
                        PicasaButton {
                            objectName: "printPreviewPrevButton"
                            text: "◀"
                            Layout.preferredWidth: 26
                            Layout.preferredHeight: 22
                            //: Az első lapon nincs hova visszalépni.
                            enabled: printWindow.previewPage > 0
                            onClicked: {
                                printWindow.previewPage -= 1
                                printWindow.frissitsdAzElonezetet()
                            }
                        }
                        Text {
                            objectName: "printPreviewPageText"
                            //: #1960: a SORREND a fordításé, nem a kódé. Az
                            //: eredeti angol erőforrása `%1$d of %2$d`
                            //: (aktuális / összes), a magyar `%2$d / %1$d`
                            //: (összes / aktuális) — `ThumbUIPrint::PrintCount`,
                            //: `stringres` 2287. Ezért összefűzés helyett
                            //: pozíció-argumentumos sablon: a `.ts` dönti el,
                            //: melyik nyelv melyik sorrendet kapja.
                            text: qsTr("%1 / %2")
                                  .arg(printWindow.previewPage + 1)
                                  .arg(printWindow.previewPageCount)
                            font.pixelSize: Theme.fontSize
                            color: Theme.ink
                        }
                        PicasaButton {
                            objectName: "printPreviewNextButton"
                            text: "▶"
                            Layout.preferredWidth: 26
                            Layout.preferredHeight: 22
                            enabled: printWindow.previewPage
                                     < printWindow.previewPageCount - 1
                            onClicked: {
                                printWindow.previewPage += 1
                                printWindow.frissitsdAzElonezetet()
                            }
                        }
                    }
                }

                Text {
                    objectName: "printQualityText"
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    font.pixelSize: Theme.fontSize
                    //: figyelmeztetés esetén hangsúlyos, egyébként semleges
                    color: printWindow.quality.ready === false
                           && printWindow.quality.total > 0
                           ? Theme.brandRed : Theme.ink
                    text: {
                        var q = printWindow.quality
                        if (!q || !q.total) return ""
                        // #3573: az eredeti sorrendje és tördelése — a
                        // `Smallest` sor végén sortörés, a `ReviewPrompt`
                        // előbb felszólít, és csak új sorban mondja a számot
                        //: `ThumbUIPrint::Smallest`
                        var sor = qsTr("Smallest picture: %1 pixels/inch.")
                                      .arg(q.smallest)
                        if (q.small > 0) {
                            //: `ThumbUIPrint::picture` / `::pictures` — az
                            //: egyes/többes szám az eredetiben is külön erőforrás
                            var mi = q.small === 1 ? qsTr("picture") : qsTr("pictures")
                            //: `ThumbUIPrint::ReviewPrompt` — %1 a darabszám,
                            //: %2 a „picture"/„pictures" szó
                            return sor + "\n"
                                   + qsTr("Please review before printing.\n%1 small %2 found.")
                                         .arg(q.small).arg(mi)
                        }
                        //: `ThumbUIPrint::ReadyPrompt`
                        return sor + "\n" + qsTr("You are ready to print.")
                    }
                }

                // #1953: az üzenet megvolt, a GOMB nem — a felhasználó
                // megtudta, hogy VAN kis felbontású kép, azt viszont nem,
                // hogy MELYIK.
                //
                // Az eredetiben `printpanel/reviewnowbutton` (és `…button2`),
                // felirat „Review", súgó „Make sure your photos are ready to
                // print" (`ui-leltar.csv:1434–1437`). ⚠️ Hogy MIÉRT kettő, az
                // NINCS mérve (a #1953 blokkolt kérdése); egy gomb elég.
                PicasaButton {
                    objectName: "printReviewButton"
                    //: `printpanel/reviewnowbutton` felirata
                    text: qsTr("Review")
                    font.pixelSize: Theme.fontSize
                    //: `printpanel/reviewnowbutton` elemleírása
                    ToolTip.text: qsTr(
                        "Make sure your photos are ready to print")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    // Az eredetiben a „You are ready to print." ágon nincs
                    // mit ellenőrizni.
                    visible: printWindow.quality.small > 0
                    onClicked: {
                        if (!printWindow.printCtl) return
                        printWindow.reviewList = printWindow.printCtl.reviewPictures(
                            printWindow.rows, printWindow.printSize)
                        printWindow.reviewOpen = true
                        printReviewList.currentIndex =
                            printWindow.reviewList.length > 0 ? 0 : -1
                    }
                }
            }
        }

        // -- nyomtató (vagy PDF-fájl) ------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: qsTr("Printer:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: printerBox
                objectName: "printPrinterBox"
                Layout.fillWidth: true
                model: [qsTr("Print to a PDF file...")].concat(printWindow.printers)
                // a `currentIndex` a választó SAJÁTJA — a párbeszéd innen
                // olvassa (`printerIndex`), nem fordítva (ld. ott)
            }
            // #2103: belépési pont a nyomtató SAJÁT beállításaihoz
            // (`printpanel/psetupbutton`). Az eredetiben az illesztőprogram
            // tulajdonságlapját nyitja (`OpenPrinter` →
            // `DocumentProperties` ×2, `0x00861750`); nálunk a Qt
            // oldalbeállítóját, mert a `DocumentProperties` a Windows
            // illesztőprogramé. A gomb HELYE és FELIRATA az, ami átvehető.
            PicasaButton {
                id: nyomtatoBeallitas
                objectName: "printPrinterSetupButton"
                //: `printpanel/setuplabel`
                text: qsTr("Printer Setup")
                //: A PDF-cél nem illesztőprogram: nincs mit beállítani.
                enabled: !printWindow.pdfSelected
                ToolTip.text: qsTr(
                    "Open printer setup controls for the selected printer")
                ToolTip.visible: nyomtatoBeallitas.hovered
                ToolTip.delay: Theme.tooltipDelay
                onClicked: {
                    if (typeof printController !== "undefined" && printController) {
                        printController.openPrinterSetup(printWindow.printerName)
                        // #2368: az oldalbeállító elfogadott elrendezése a
                        // papíradat FORRÁSA — a mezőt tehát a párbeszéd
                        // bezárása után frissíteni kell, különben a régi
                        // lapot mutatná.
                        printWindow.frissitsdAPapiradatot()
                    }
                }
            }
        }

        // -- papíradat (#2368) -------------------------------------------
        // Az eredeti panel `printpanel/paperinfo` mezője: tisztán SZÖVEGES
        // kijelző a nyomtató neve mellett (az állapotfrissítő, `0x00745980`,
        // mind a négy információs mezőt ugyanazzal a szövegbeállítóval
        // tölti). Innen látja a felhasználó, MILYEN LAPRA fog nyomtatni —
        // a nyomat mérete és a „kis kép" figyelmeztetés is ettől függ.
        Text {
            objectName: "printPaperInfoText"
            Layout.fillWidth: true
            elide: Text.ElideRight
            text: printWindow.papiradat
            font.pixelSize: Theme.fontSizeLadder[0]
            color: Theme.textGray
        }

        // -- a PDF célfájlja (csak PDF-módban) ----------------------------
        RowLayout {
            Layout.fillWidth: true
            visible: printWindow.pdfSelected
            spacing: 8
            Text {
                objectName: "printPdfTargetText"
                Layout.fillWidth: true
                elide: Text.ElideMiddle
                text: printWindow.pdfTarget.length > 0
                      ? printWindow.pdfTarget : qsTr("(not selected)")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            PicasaButton {
                objectName: "printPdfBrowseButton"
                text: qsTr("Browse...")
                onClicked: pdfTargetDialog.open()
            }
        }

        // -- illesztés ----------------------------------------------------
        // #1590: az indexképnél nincs értelme — ott MINDIG a teljes kép
        // látszik a cellában (ez az indexkép lényege), és a tájolást sem a
        // képek szabják meg, mert egy lapon sok kép van
        ColumnLayout {
            Layout.fillWidth: true
            visible: !printWindow.contactSheet
            spacing: 2
            Text {
                text: qsTr("Fit to page:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            RowLayout {
                spacing: 16
                RadioButton {
                    objectName: "printFitRadio"
                    text: qsTr("Whole picture")
                    checked: printWindow.fitMode === "fit"
                    onClicked: printWindow.fitMode = "fit"
                }
                RadioButton {
                    objectName: "printFillRadio"
                    text: qsTr("Fill the page (crop)")
                    checked: printWindow.fitMode === "fill"
                    onClicked: printWindow.fitMode = "fill"
                }
            }
        }

        // -- tájolás ------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            visible: !printWindow.contactSheet
            spacing: 2
            Text {
                text: qsTr("Orientation:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: orientationBox
                objectName: "printOrientationBox"
                readonly property var values: ["auto", "portrait", "landscape"]
                Layout.preferredWidth: 200
                model: [qsTr("Automatic"), qsTr("Portrait"), qsTr("Landscape")]
                currentIndex: 0
                onActivated: printWindow.orientation = values[currentIndex]
            }
        }

        }
        }

        // #4795: a hiba/haladás/eredmény a RÖGZÍTETT részben van (a görgetett
        // tartalmon kívül), hogy a Nyomtatás után mindig látsszon.
        ColumnLayout {
            id: printStatusBox
            Layout.fillWidth: true
            visible: printWindow.lastSkipped.length > 0
                     || printWindow.lastError.length > 0
                     || printWindow.printTotalPages > 0
                     || printWindow.lastResult.length > 0
            spacing: 10

            Text {
                objectName: "printSkippedText"
                visible: printWindow.lastSkipped.length > 0
                text: qsTr("These pictures could not be printed: %1")
                      .arg(printWindow.lastSkipped.join(", "))
                color: Theme.brandRed
                font.pixelSize: Theme.fontSize
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Text {
                objectName: "printErrorText"
                visible: printWindow.lastError.length > 0
                text: printWindow.lastError
                color: Theme.brandRed
                font.pixelSize: Theme.fontSize
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            // #3016: LAPONKÉNTI haladás. A festés a GUI-szálon fut (a mérés
            // szerint nem tolható háttérszálra: az a munka kétharmada, és a Qt
            // festő-API-ja a GUI-szálhoz kötött), ezért a vezérlő laponként
            // enged vissza a felületnek — enélkül a párbeszéd a feladat teljes
            // idejére befagyna, és a felhasználó nem tudná, dolgozik-e még.
            Text {
                objectName: "printProgressText"
                visible: printWindow.printTotalPages > 0
                text: qsTr("Printing: %1 / %2")
                    .arg(printWindow.printDonePages).arg(printWindow.printTotalPages)
                color: Theme.textDark
                font.pixelSize: Theme.fontSize
                Layout.fillWidth: true
            }

            Text {
                objectName: "printResultText"
                visible: printWindow.lastResult.length > 0
                text: qsTr("Finished: %1").arg(printWindow.lastResult)
                color: Theme.picasaGreen
                font.pixelSize: Theme.fontSize
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }

        RowLayout {
            id: printButtonRow
            Layout.fillWidth: true
            spacing: 8
            PicasaButton {
                objectName: "printHelpButton"
                text: qsTr("Help")
                onClicked: printWindowHelp.nyisdASugot(printWindow.helpTopic)
            }
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "printStartButton"
                text: qsTr("Print")
                accent: Theme.picasaGreen
                enabled: printWindow.canPrint
                onClicked: printWindow.startPrint()
            }
            PicasaButton {
                objectName: "printCloseButton"
                text: qsTr("Close")
                onClicked: printWindow.visible = false
            }
        }
    }

    PrintOptionsPanel {
        id: printOptionsPanel
        objectName: "printOptionsPanel"
        anchors.fill: parent
        controller: printWindow.printCtl
        contactSheet: printWindow.contactSheet
        onOptionsApplied: printWindow.frissitsdAzElonezetet()
        onCloseRequested: printOptionsPanel.visible = false
    }

    // #4280: az „Ellenőrzés" listája képenként mutatja a DPI-sávot és az
    // effektív felbontást; a legrosszabb kerül előre.
    Rectangle {
        objectName: "printReviewPanel"
        anchors.fill: parent
        visible: printWindow.reviewOpen
        color: Theme.canvasBg
        z: 100

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8
            Text {
                //: `printpanel/reviewnowbutton` felirata — a lap címe is ez
                text: qsTr("Review")
                font.pixelSize: Theme.fontSize + 3
                font.bold: true
                color: Theme.ink
            }
            Text {
                objectName: "printReviewWarningText"
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                //: `CPrintDlg::toosmall`; eredeti figyelmeztetés a
                //: `picasa-nyomtatas.md` 40.7 szerint.
                visible: printWindow.reviewList.length > 0
                text: qsTr("Some of your pictures are too small to print well.  You can remove these pictures, print them anyway, or cancel and change the print size.")
            }
            ListView {
                objectName: "printReviewList"
                id: printReviewList
                Layout.fillWidth: true
                Layout.fillHeight: printWindow.reviewList.length > 0
                clip: true
                model: printWindow.reviewList
                currentIndex: printWindow.reviewList.length > 0 ? 0 : -1
                delegate: Item {
                    required property var modelData
                    required property int index
                    objectName: "printReviewListRow"
                    width: ListView.view.width
                    height: reviewListRowText.implicitHeight + 8
                    Rectangle {
                        anchors.fill: parent
                        color: ListView.isCurrentItem ? Theme.surfaceAlt : "transparent"
                    }
                    Text {
                        id: reviewListRowText
                        objectName: "printReviewListRowText"
                        anchors.fill: parent
                        anchors.margins: 4
                        elide: Text.ElideMiddle
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                        //: A `CPrintDlg::bestqual` / `goodqual` / `badqual`
                        //: hivatalos angol feliratai a fordításból jönnek.
                        text: {
                            var label = modelData.qualityCode === 2
                                ? qsTr("Best quality (%1 pixels/inch)")
                                : modelData.qualityCode === 1
                                    ? qsTr("Good quality (%1 pixels/inch)")
                                    : qsTr("Bad quality (%1 pixels/inch)")
                            return modelData.name + "   —   "
                                   + label.arg(modelData.dpi)
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: printReviewList.currentIndex = index
                    }
                }
            }
            Text {
                objectName: "printReviewEmptyText"
                Layout.fillWidth: true
                visible: printWindow.reviewList.length === 0
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                text: printWindow.rows.length > 0
                      && Number(printWindow.quality.total || 0) > 0
                      ? qsTr("All of your pictures are ready to print.")
                      : qsTr("There are no pictures left to print.")
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                PicasaButton {
                    objectName: "printReviewRemoveSelectedButton"
                    Layout.fillWidth: true
                    enabled: printReviewList.currentIndex >= 0
                    text: qsTr("Remove Selected Items")
                    onClicked: printWindow.removeSelectedReviewPicture()
                }
                PicasaButton {
                    objectName: "printReviewRemoveLowButton"
                    Layout.fillWidth: true
                    enabled: printWindow.reviewList.length > 0
                    text: qsTr("Remove Low Quality Pictures")
                    onClicked: printWindow.removeLowQualityReviewPictures()
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                Item { Layout.fillWidth: true }
                PicasaButton {
                    objectName: "printReviewAcceptButton"
                    text: qsTr("OK")
                    enabled: Number(printWindow.quality.total || 0) > 0
                    onClicked: printWindow.acceptReviewAndPrint()
                }
                PicasaButton {
                    objectName: "printReviewCancelButton"
                    text: qsTr("Cancel")
                    onClicked: printWindow.reviewOpen = false
                }
            }
        }
    }

    FileDialog {
        id: pdfTargetDialog
        title: qsTr("Print to a PDF file...")
        fileMode: FileDialog.SaveFile
        defaultSuffix: "pdf"
        nameFilters: [qsTr("PDF documents (*.pdf)")]
        onAccepted: printWindow.pdfTarget = selectedFile.toString()
    }
}
