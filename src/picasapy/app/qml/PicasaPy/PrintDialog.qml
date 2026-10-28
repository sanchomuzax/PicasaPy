import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Nyomtatás (#32 RÉSZLEGES kör, bekötve a #1472-ben) — a `Fájl ▸
// Nyomtatás…` (Ctrl+P) és a képtálca „Nyomtatás" gombja ezt nyitja.
//
// ⚠️ Ez NEM a Picasa teljes nyomtatási sablonrendszere (`print.fen` /
// `reviewprint.fen`, állítható margó). A méretválasztó a #5683 óta az
// eredeti `ytPrintSizes` katalógust mutatja; az indexkép (`eContact`) külön
// elrendezési úton marad, a Passport pedig az útlevélkép-parancs forrásával.
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
        target: printStatusPanel.statusBox
        function onImplicitHeightChanged() {
            if (printWindow.meretezesFuggoben)
                meretezesIdozito.restart()
        }
    }
    function kezdoMagassag() {
        // ⚠️ csak az ELSŐ elrendezés UTÁN hívandó (ld. `meretezesIdozito`):
        // rejtett ablakban a Layout nem rendeződik újra, az implicitHeight
        // elavult (az előző nyitás/mód tartalmát tükrözi).
        var statusMagassag = printStatusPanel.visible
                             ? printStatusPanel.Layout.preferredHeight : 0
        var kell = printContent.implicitHeight + statusMagassag
                   + printButtonRow.implicitHeight
                   + 2 * keretMargo + printFrame.spacing
                   + (printStatusPanel.visible ? printFrame.spacing : 0)
        // ⚠️ többmonitoros gépen a `Screen` az ablak képernyőjét adja, ami
        // nyitáskor még nem biztos, hogy a végleges — a plafon közelítés.
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
    readonly property int printerIndex: printPrinterPanel.currentIndex
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

    // #5681: a Picasa első megnyitáskor Crop to Fit módot választott.
    property string fitMode: "fill"         // PrintFitMode.FIT / .FILL
    property string orientation: "auto"     // PrintOrientation

    // #1590: indexkép-elrendezés (több bélyegkép egy lapon). A rács
    // oszlopszáma a felhasználóé — az eredeti nyomtatási előnézetéből ez
    // nem volt kiolvasható, a `stringres`-ben sincs rá kulcs (DÖNTÉS).
    property bool contactSheet: false
    property int contactColumns: 4

    // #5684: az eredeti nyomtatási mód az ablak megnyitásakor a vezérlőtől
    // töltődik be, váltáskor pedig a 2/0 vagy 1/1 állapotpárt menti. A mód
    // tényleges hatása a nyomatra külön mérés tárgya.
    property bool optimizedPrintMode: false

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
    //: A feliratok a hivatalos `ytPrintSizes::` szövegcsaládból valók;
    //: minden eredeti azonosítóhoz az eredeti angol cím tartozik.
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
        "CDSIZE": qsTr("CD Cover Size"),
        "PASSPORT": qsTr("Passport"),
        //: Az eredeti címke része a katalógusnak; a nyomtatási út külön van.
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
    readonly property var printSizeOptions: printWindow.printSizeIds.map(
        function (azonosito) {
            return {
                id: azonosito,
                label: printWindow.printSizeLabelById[azonosito] || azonosito,
                enabled: azonosito !== "CDSIZE"
            }
        })
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
            printReviewPanel.currentIndex = printWindow.reviewList.length > 0 ? 0 : -1
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
        var index = printReviewPanel.currentIndex
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

    function isLowQualityReviewPicture(kep) {
        return Number(kep.qualityCode) === 0
    }

    // A `kivalaszt` szerinti képek kivétele a felülvizsgálatból: a sor-
    // indexesek a `rows`-ból mennek ki, a rekordosak (tálca, útlevél) a
    // vezérlő kizárási listájába.
    function removeReviewPicturesWhere(kivalaszt) {
        var sorok = []
        var rekordAzonositok = []
        for (var i = 0; i < printWindow.reviewList.length; ++i) {
            var kep = printWindow.reviewList[i]
            if (!kivalaszt(kep)) continue
            var sor = Number(kep.row)
            if (sor >= 0) sorok.push(sor)
            else rekordAzonositok.push(Number(kep.recordId))
        }
        if (rekordAzonositok.length > 0)
            printWindow.printCtl.excludeReviewPictures(rekordAzonositok)
        if (sorok.length > 0) printWindow.removeReviewRows(sorok)
        else printWindow.frissitsdAMinoseget()
    }

    // #5682 / 0x0085cce0 („Remove Low Quality Pictures"): ha a listában van
    // legalább egy nem alacsony minőségű kép, nincs kérdés, csak az
    // alacsonyak törlődnek. Ha MINDEN kép alacsony, az eredeti megerősítést
    // kéri (removeAllConfirm): az Igen törli az összes képet és megszakítja
    // a nyomtatást, a Nem nem változtat a listán.
    function removeLowQualityReviewPictures() {
        var mindAlacsony = printWindow.reviewList.length > 0
            && printWindow.reviewList.every(printWindow.isLowQualityReviewPicture)
        if (mindAlacsony) {
            printRemoveAllDialog.open()
            return
        }
        printWindow.removeReviewPicturesWhere(printWindow.isLowQualityReviewPicture)
    }

    // Az Igen ága (0x0085cce0): minden kép törlése, majd a hívó a
    // `printpanel/pcancelbutton` műveletet küldi (0x00745726), ami nálunk a
    // nyomtatási ablak Close gombja: a nyomtatás nem készül el.
    function removeAllReviewPicturesAndCancel() {
        printWindow.removeReviewPicturesWhere(function () { return true })
        printWindow.cancelReview()
        printWindow.visible = false
    }

    // A felülvizsgálat Mégse-ága (printReviewCancelButton): visszatér a
    // méretválasztóhoz, a nyomtatás elmarad.
    function cancelReview() {
        printWindow.reviewOpen = false
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
    //: Bekapcsoláskor az általános mód illesztése és példányszáma félre-
    //: kerül; Passport módba lépéskor a példányszám nem változik. A következő
    //: sima nyitás visszaadja az általános mód beállításait.
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
        } else if (printWindow.mentettBeallitas !== null) {
            printWindow.fitMode = printWindow.mentettBeallitas.fitMode
            printWindow.copies = printWindow.mentettBeallitas.copies
            printWindow.mentettBeallitas = null
        }
        printWindow.passport = be
    }

    function valasszNyomatmeretet(azonosito) {
        if (!azonosito || azonosito === "CDSIZE" || !printWindow.printCtl) return
        if (azonosito === "CONTACT") {
            printWindow.contactSheet = true
            printWindow.printSize = azonosito
            printSettingsPanel.sizeBox.currentIndex = printWindow.printSizeIds.indexOf(azonosito)
            printWindow.frissitsdAMinoseget()
            return
        }
        if (!printWindow.printCtl.setPresetPrintSize(azonosito)) return
        printWindow.printCtl.setPrintSize(azonosito)
        printWindow.contactSheet = false
        printWindow.printSize = azonosito
        printSettingsPanel.sizeBox.currentIndex = printWindow.printSizeIds.indexOf(azonosito)
        printWindow.frissitsdAMinoseget()
    }

    //: #1401: a bezárt nézet nem hagyhatja a vezérlőt útlevél-módban —
    //: a következő nyomtatás különben a kivágott képet nyomtatná.
    onVisibleChanged: {
        if (printWindow.visible) {
            printWindow.meretezesFuggoben = true  // #4795
            meretezesIdozito.restart()
        }
        if (!printWindow.visible) {
            meretezesIdozito.stop()
            printWindow.meretezesFuggoben = false
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

    function valasszNyomtatasiModot(optimized) {
        if (!printWindow.printCtl) return
        printWindow.optimizedPrintMode = !!optimized
        printWindow.printCtl.setPrinterOptimized(!!optimized)
        // A specifikáció szerint a módváltás a nyomtatási előnézetet is
        // frissíti; a nyomatra gyakorolt tényleges hatás külön jegy.
        printWindow.frissitsdAzElonezetet()
    }

    function nyisd(targetRows, utlevelUrl, contactMode) {
        printWindow.valtsdAzUtlevelet(utlevelUrl)
        if (printWindow.printCtl)
            printWindow.printCtl.clearReviewExclusions()
        printWindow.optimizedPrintMode = printWindow.printCtl
            ? printWindow.printCtl.printerOptimized() : false
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
            // #5683: a teljes, eredeti sorrendű `ytPrintSizes` lista.
            printWindow.printSizeIds = printWindow.printCtl.printSizes()
            printWindow.printSizePresetIds = printWindow.printCtl.printSizePresets()
            printWindow.printSize = printWindow.passport
                ? "PASSPORT" : printWindow.printCtl.printSize()
        }
        printSettingsPanel.sizeBox.currentIndex = printWindow.printSizeIds.indexOf(
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
            Layout.minimumHeight: 60
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

            PrintSelectionPanel {
                Layout.fillWidth: true
                printWindow: printWindow
            }

            PrintSettingsPanel {
                id: printSettingsPanel
                Layout.fillWidth: true
                printWindow: printWindow
                printOptionsPanel: printOptionsPanel
                printAreaVisible: !printWindow.contactSheet

                // #1819: KÉPENKÉNTI példányszám.
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

                PrintPreviewPanel {
                    printWindow: printWindow
                }

                Text {
                    objectName: "printQualityText"
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    font.pixelSize: Theme.fontSize
                    color: printWindow.quality.ready === false
                           && printWindow.quality.total > 0
                           ? Theme.brandRed : Theme.ink
                    text: {
                        var q = printWindow.quality
                        if (!q || !q.total) return ""
                        var sor = qsTr("Smallest picture: %1 pixels/inch.")
                                      .arg(q.smallest)
                        if (q.small > 0) {
                            var mi = q.small === 1 ? qsTr("picture") : qsTr("pictures")
                            return sor + "\n"
                                   + qsTr("Please review before printing.\n%1 small %2 found.")
                                         .arg(q.small).arg(mi)
                        }
                        return sor + "\n" + qsTr("You are ready to print.")
                    }
                }

                PicasaButton {
                    objectName: "printReviewButton"
                    text: qsTr("Review")
                    font.pixelSize: Theme.fontSize
                    ToolTip.text: qsTr(
                        "Make sure your photos are ready to print")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    visible: printWindow.quality.small > 0
                    onClicked: {
                        if (!printWindow.printCtl) return
                        printWindow.reviewList = printWindow.printCtl.reviewPictures(
                            printWindow.rows, printWindow.printSize)
                        printWindow.reviewOpen = true
                        printReviewPanel.currentIndex =
                            printWindow.reviewList.length > 0 ? 0 : -1
                    }
                }
            }

            PrintPrinterPanel {
                id: printPrinterPanel
                Layout.fillWidth: true
                printWindow: printWindow
                pdfTargetDialog: pdfTargetDialog
            }

            PrintPrinterPanel {
                id: printPrinterDetailsPanel
                Layout.fillWidth: true
                printWindow: printWindow
                pdfTargetDialog: pdfTargetDialog
                details: true
            }

            PrintFitPanel {
                Layout.fillWidth: true
                printWindow: printWindow
            }
        }
        }

        // #4795: a hiba/haladás/eredmény a RÖGZÍTETT részben van (a görgetett
        // tartalmon kívül), hogy a Nyomtatás után mindig látsszon.
        // Felső korlát (az ablak harmada): hosszú kihagyott-lista se tolja
        // ki a gombsort — a szövegek ekkor a saját területükön görgethetők.
        PrintStatusPanel {
            id: printStatusPanel
            printWindow: printWindow
        }

        PrintButtonRow {
            id: printButtonRow
            printWindow: printWindow
            printWindowHelp: printWindowHelp
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

    PrintReviewPanel {
        id: printReviewPanel
        printWindow: printWindow
    }

    PrintRemoveAllDialog {
        id: printRemoveAllDialog
        printWindow: printWindow
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
