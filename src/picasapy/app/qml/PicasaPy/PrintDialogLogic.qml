import QtQml

// A nyomtatási párbeszéd állapotműveletei; gazda- és nézetobjektumait
// kötelező tulajdonságokon kapja, a Window nyilvános metódusai delegálnak ide.
QtObject {
    id: printLogic
    required property var hostWindow
    required property var printController
    required property var settingsPanel
    required property var reviewPanel
    required property var removeAllDialog
    required property var optionsPanel

    function frissitsdAMinoseget() {
        if (!printController) return
        hostWindow.quality = printController.printQuality(
            hostWindow.rows, hostWindow.printSize)
        hostWindow.frissitsdAzElonezetet()
        if (hostWindow.reviewOpen) {
            hostWindow.reviewList = printController.reviewPictures(
                hostWindow.rows, hostWindow.printSize)
            reviewPanel.currentIndex = hostWindow.reviewList.length > 0 ? 0 : -1
        }
    }

    function removeReviewRows(eltavolitandoSorok) {
        var maradek = []
        for (var i = 0; i < hostWindow.rows.length; ++i) {
            var sor = Number(hostWindow.rows[i])
            if (eltavolitandoSorok.indexOf(sor) < 0)
                maradek.push(sor)
        }
        hostWindow.rows = maradek
        hostWindow.frissitsdAMinoseget()
    }

    function removeSelectedReviewPicture() {
        var index = reviewPanel.currentIndex
        if (index < 0 || index >= hostWindow.reviewList.length) return
        var kep = hostWindow.reviewList[index]
        var kepSor = Number(kep.row)
        if (kepSor >= 0) {
            hostWindow.removeReviewRows([kepSor])
        } else {
            printController.excludeReviewPictures([Number(kep.recordId)])
            hostWindow.frissitsdAMinoseget()
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
        for (var i = 0; i < hostWindow.reviewList.length; ++i) {
            var kep = hostWindow.reviewList[i]
            if (!kivalaszt(kep)) continue
            var sor = Number(kep.row)
            if (sor >= 0) sorok.push(sor)
            else rekordAzonositok.push(Number(kep.recordId))
        }
        if (rekordAzonositok.length > 0)
            printController.excludeReviewPictures(rekordAzonositok)
        if (sorok.length > 0) hostWindow.removeReviewRows(sorok)
        else hostWindow.frissitsdAMinoseget()
    }

    // #5682 / 0x0085cce0 („Remove Low Quality Pictures"): ha a listában van
    // legalább egy nem alacsony minőségű kép, nincs kérdés, csak az
    // alacsonyak törlődnek. Ha MINDEN kép alacsony, az eredeti megerősítést
    // kéri (removeAllConfirm): az Igen törli az összes képet és megszakítja
    // a nyomtatást, a Nem nem változtat a listán.
    function removeLowQualityReviewPictures() {
        var mindAlacsony = hostWindow.reviewList.length > 0
            && hostWindow.reviewList.every(hostWindow.isLowQualityReviewPicture)
        if (mindAlacsony) {
            removeAllDialog.open()
            return
        }
        hostWindow.removeReviewPicturesWhere(hostWindow.isLowQualityReviewPicture)
    }

    // Az Igen ága (0x0085cce0): minden kép törlése, majd a hívó a
    // `printpanel/pcancelbutton` műveletet küldi (0x00745726), ami nálunk a
    // nyomtatási ablak Close gombja: a nyomtatás nem készül el.
    function removeAllReviewPicturesAndCancel() {
        hostWindow.removeReviewPicturesWhere(function () { return true })
        hostWindow.cancelReview()
        hostWindow.visible = false
    }

    // A felülvizsgálat Mégse-ága (printReviewCancelButton): visszatér a
    // méretválasztóhoz, a nyomtatás elmarad.
    function cancelReview() {
        hostWindow.reviewOpen = false
    }

    function acceptReviewAndPrint() {
        if (Number(hostWindow.quality.total || 0) === 0) return
        hostWindow.reviewOpen = false
        hostWindow.startPrint()
    }

    //: #1819: az előnézeti lap újrarajzolása. Minden állítás (méret,
    //: illesztés, tájolás, példányszám, lapozás) ide fut be — így az
    //: előnézet SOSEM mutathat mást, mint amit a nyomtatás adna.
    //:
    //: A cache-buster (`?v=`) nem díszítés: a Qt a képeket URL szerint
    //: gyorstárazza, tehát ugyanarra a fájlnévre írt új tartalom a RÉGI
    //: képpontokkal jelenne meg (a #1186 hibaosztálya).
    function frissitsdAzElonezetet() {
        if (!printController) {
            hostWindow.previewPageCount = 0
            hostWindow.previewSource = ""
            hostWindow.printPageCount = 0
            return
        }
        // #3712: az indexképnek nincs lapozható előnézete — de a
        // darabszám-sornak MÉGIS a valódi lapszámot kell mondania, nem
        // ígérhet olyat, amit a nyomtatás nem tesz meg.
        if (hostWindow.contactSheet) {
            hostWindow.previewPageCount = 0
            hostWindow.previewSource = ""
            hostWindow.printPageCount = printController.contactPageCount(
                hostWindow.rows, hostWindow.contactColumns,
                hostWindow.printerName)
            return
        }
        // #3647: a lapszámot UGYANAZZAL a tájolással/nyomtatóval kérjük,
        // mint amivel a `renderPreviewPage` lentebb ténylegesen rajzol —
        // különben a lapozó számot mutatna, a rajzoló pedig mást.
        var lapok = printController.printPageCount(
            hostWindow.rows, hostWindow.copies, hostWindow.orientation,
            hostWindow.printerName)
        hostWindow.previewPageCount = lapok
        hostWindow.printPageCount = lapok
        if (lapok <= 0) {
            hostWindow.previewSource = ""
            return
        }
        if (hostWindow.previewPage >= lapok)
            hostWindow.previewPage = lapok - 1
        if (hostWindow.previewPage < 0)
            hostWindow.previewPage = 0
        var cel = hostWindow.elonezetiFajl()
        var ok = printController.renderPreviewPage(
            hostWindow.rows, hostWindow.fitMode, hostWindow.orientation,
            hostWindow.copies, hostWindow.previewPage, cel,
            hostWindow.printerName)
        hostWindow.elonezetValtozat += 1
        //: A cél MÁR URL (a vezérlő a `QUrl.fromLocalFile`-on át adja,
        //: #1019) — kézzel semmit nem fűzünk elé, csak a gyorstár-törő
        //: lekérdezést utána.
        hostWindow.previewSource =
            ok ? cel + "?v=" + hostWindow.elonezetValtozat : ""
    }

    //: Az előnézeti PNG helye URL-ként. Egyetlen fájl, felülírva — a
    //: párbeszéd életciklusán túl nincs rá szükség, és a lapozás így nem
    //: szemetel. ⚠️ A vezérlő adja, `QUrl.fromLocalFile`-on át (#1019).
    function elonezetiFajl() {
        return printController.previewImageUrl()
    }

    //: #1401: az útlevél-mód be- vagy kikapcsolása a vezérlőn ÉS a nézeten.
    //: Bekapcsoláskor az általános mód illesztése és példányszáma félre-
    //: kerül; Passport módba lépéskor a példányszám nem változik. A következő
    //: sima nyitás visszaadja az általános mód beállításait.
    function valtsdAzUtlevelet(utlevelUrl) {
        if (printController)
            printController.clearPassportSource()
        var be = utlevelUrl.length > 0 && printController !== null
                 && printController.setPassportSource(utlevelUrl)
        if (be) {
            if (hostWindow.mentettBeallitas === null)
                hostWindow.mentettBeallitas = {
                    fitMode: hostWindow.fitMode, copies: hostWindow.copies }
            hostWindow.fitMode = "fill"
        } else if (hostWindow.mentettBeallitas !== null) {
            hostWindow.fitMode = hostWindow.mentettBeallitas.fitMode
            hostWindow.copies = hostWindow.mentettBeallitas.copies
            hostWindow.mentettBeallitas = null
        }
        hostWindow.passport = be
    }

    function valasszNyomatmeretet(azonosito) {
        if (!azonosito || azonosito === "CDSIZE" || !printController) return
        if (azonosito === "CONTACT") {
            hostWindow.contactSheet = true
            hostWindow.printSize = azonosito
            settingsPanel.sizeBox.currentIndex = hostWindow.printSizeIds.indexOf(azonosito)
            hostWindow.frissitsdAMinoseget()
            return
        }
        if (!printController.setPresetPrintSize(azonosito)) return
        printController.setPrintSize(azonosito)
        hostWindow.contactSheet = false
        hostWindow.printSize = azonosito
        settingsPanel.sizeBox.currentIndex = hostWindow.printSizeIds.indexOf(azonosito)
        hostWindow.frissitsdAMinoseget()
    }

    function openForContactSheet(targetRows) {
        hostWindow.nyisd(targetRows, "", true)
    }

    function openForRows(targetRows) {
        hostWindow.nyisd(targetRows, "", false)
    }

    //: #1401: az Útlevélkép belépési pontja — a `url` a kivágott kép.
    function openForPassport(url) {
        hostWindow.nyisd([0], url, false)
    }

    function valasszNyomtatasiModot(optimized) {
        if (!printController) return
        hostWindow.optimizedPrintMode = !!optimized
        printController.setPrinterOptimized(!!optimized)
        // A specifikáció szerint a módváltás a nyomtatási előnézetet is
        // frissíti; a nyomatra gyakorolt tényleges hatás külön jegy.
        hostWindow.frissitsdAzElonezetet()
    }

    function nyisd(targetRows, utlevelUrl, contactMode) {
        hostWindow.valtsdAzUtlevelet(utlevelUrl)
        if (printController)
            printController.clearReviewExclusions()
        hostWindow.optimizedPrintMode = printController
            ? printController.printerOptimized() : false
        hostWindow.rows = targetRows ? targetRows : []
        hostWindow.reviewOpen = false
        hostWindow.reviewList = []
        // ⚠️ #1590/#3712: az elrendezés NEM élheti túl a bezárást — ezért a
        // MEGNYITÁS módja dönt (paraméter), nem egy külön, utólagos
        // állítás. Enélkül a Ctrl+P legközelebb szó nélkül indexképet
        // nyomtatna, a felhasználó pedig méret szerintit vár.
        hostWindow.contactSheet = !!contactMode
        // #1782: a megjegyzett méret visszatöltése, majd a minőség-mérés
        if (printController) {
            // #5683: a teljes, eredeti sorrendű `ytPrintSizes` lista.
            hostWindow.printSizeIds = printController.printSizes()
            hostWindow.printSizePresetIds = printController.printSizePresets()
            hostWindow.printSize = hostWindow.passport
                ? "PASSPORT" : printController.printSize()
        }
        settingsPanel.sizeBox.currentIndex = hostWindow.printSizeIds.indexOf(
            hostWindow.contactSheet ? "CONTACT" : hostWindow.printSize)
        hostWindow.previewPage = 0
        hostWindow.frissitsdAMinoseget()
        hostWindow.lastResult = ""
        hostWindow.lastSkipped = []
        // ⚠️ a célfájl NEM élheti túl a bezárást. Ha megmaradna, a
        // következő nyitáskor a gomb azonnal élő lenne, a `FileDialog` meg
        // sem nyílna — tehát a Qt felülírás-kérdése sem —, és az előző PDF
        // kérdés nélkül elveszne.
        hostWindow.pdfTarget = ""
        // #1472: ha a Qt nyomtatás-modulja hiányzik (Debian/Ubuntu külön
        // csomag, ld. `application.py`), a párbeszéd NEM néma: kimondja,
        // miért nem tud dolgozni, ahelyett hogy szürke gombot mutatna
        // ⚠️ a tulajdonos NEM programozó: a puszta „hiányzik egy modul"
        // neki zsákutca. Az üzenet ezért kimondja a telepítő parancsot is.
        hostWindow.lastError = printController
            ? "" : qsTr("Printing is unavailable: the Qt print support "
                        + "module is missing. On Debian/Ubuntu you can "
                        + "install it with: "
                        + "sudo apt install python3-pyside6.qtprintsupport")
        hostWindow.printers = printController ? printController.listPrinters() : []
        optionsPanel.visible = false
        hostWindow.visible = true
        optionsPanel.closeTextColorPicker()
    }

    function startPrint() {
        if (!printController) return
        hostWindow.lastError = ""
        hostWindow.lastResult = ""
        hostWindow.lastSkipped = []
        // a gomb ilyenkor szürke, tehát ide kattintással nem lehet eljutni —
        // de a néma elutasítás annyira visszatérő hibánk, hogy a
        // programozott hívás se maradhat szótlan
        if (hostWindow.rows.length === 0
                || Number(hostWindow.quality.total || 0) === 0) {
            hostWindow.lastError = qsTr("No pictures to print.")
            return
        }
        if (hostWindow.pdfSelected) {
            if (hostWindow.pdfTarget.length === 0) {
                hostWindow.lastError = qsTr("Choose the target file.")
                return
            }
            if (hostWindow.contactSheet) {
                printController.renderContactSheetPdf(
                    hostWindow.rows, hostWindow.contactColumns,
                    hostWindow.pdfTarget)
                return
            }
            printController.renderPrintPreviewPdf(
                hostWindow.rows, hostWindow.fitMode,
                hostWindow.orientation, hostWindow.pdfTarget,
                hostWindow.copies)
            return
        }
        if (hostWindow.contactSheet) {
            printController.printContactSheet(
                hostWindow.rows, hostWindow.printerName,
                hostWindow.contactColumns)
            return
        }
        printController.printRows(
            hostWindow.rows, hostWindow.printerName,
            hostWindow.fitMode, hostWindow.orientation, hostWindow.copies)
    }

}
