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
        target: printDialogContent.content
        function onImplicitHeightChanged() {
            if (printWindow.meretezesFuggoben)
                meretezesIdozito.restart()
        }
    }
    Connections {
        target: printDialogContent.statusPanel.statusBox
        function onImplicitHeightChanged() {
            if (printWindow.meretezesFuggoben)
                meretezesIdozito.restart()
        }
    }
    function kezdoMagassag() {
        // ⚠️ csak az ELSŐ elrendezés UTÁN hívandó (ld. `meretezesIdozito`):
        // rejtett ablakban a Layout nem rendeződik újra, az implicitHeight
        // elavult (az előző nyitás/mód tartalmát tükrözi).
        var statusMagassag = printDialogContent.statusPanel.visible
                             ? printDialogContent.statusPanel.Layout.preferredHeight : 0
        var kell = printDialogContent.content.implicitHeight + statusMagassag
                   + printDialogContent.buttonRow.implicitHeight
                   + 2 * keretMargo + printDialogContent.frame.spacing
                   + (printDialogContent.statusPanel.visible ? printDialogContent.frame.spacing : 0)
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
    readonly property int printerIndex: printDialogContent.printerPanel.currentIndex
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
    property int elonezetValtozat: 0

    function frissitsdAMinoseget() { printDialogLogic.frissitsdAMinoseget() }

    function removeReviewRows(eltavolitandoSorok) { printDialogLogic.removeReviewRows(eltavolitandoSorok) }

    function removeSelectedReviewPicture() { printDialogLogic.removeSelectedReviewPicture() }

    function isLowQualityReviewPicture(kep) { return printDialogLogic.isLowQualityReviewPicture(kep) }

    function removeReviewPicturesWhere(kivalaszt) { printDialogLogic.removeReviewPicturesWhere(kivalaszt) }

    function removeLowQualityReviewPictures() { printDialogLogic.removeLowQualityReviewPictures() }

    function removeAllReviewPicturesAndCancel() { printDialogLogic.removeAllReviewPicturesAndCancel() }

    function cancelReview() { printDialogLogic.cancelReview() }

    function acceptReviewAndPrint() { printDialogLogic.acceptReviewAndPrint() }

    function frissitsdAzElonezetet() { printDialogLogic.frissitsdAzElonezetet() }

    function elonezetiFajl() { return printDialogLogic.elonezetiFajl() }

    function valtsdAzUtlevelet(utlevelUrl) { printDialogLogic.valtsdAzUtlevelet(utlevelUrl) }

    function valasszNyomatmeretet(azonosito) { printDialogLogic.valasszNyomatmeretet(azonosito) }

    function openForContactSheet(targetRows) { printDialogLogic.openForContactSheet(targetRows) }

    function openForRows(targetRows) { printDialogLogic.openForRows(targetRows) }

    function openForPassport(url) { printDialogLogic.openForPassport(url) }

    function valasszNyomtatasiModot(optimized) { printDialogLogic.valasszNyomtatasiModot(optimized) }

    function nyisd(targetRows, utlevelUrl, contactMode) { printDialogLogic.nyisd(targetRows, utlevelUrl, contactMode) }

    function startPrint() { printDialogLogic.startPrint() }

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

    PrintDialogContent {
        id: printDialogContent
        anchors.fill: parent
        hostWindow: printWindow
        hostWindowHelp: printWindowHelp
        hostOptionsPanel: printOptionsPanel
        hostPdfTargetDialog: pdfTargetDialog
        hostReviewPanel: printReviewPanel
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

    PrintDialogLogic {
        id: printDialogLogic
        hostWindow: printWindow
        printController: printWindow.printCtl
        settingsPanel: printDialogContent.settingsPanel
        reviewPanel: printReviewPanel
        removeAllDialog: printRemoveAllDialog
        optionsPanel: printOptionsPanel
    }
}
