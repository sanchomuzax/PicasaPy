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
    width: 480
    height: 420
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
    property string previewSource: ""
    // a rendszer nyomtatóinak neve; a választóban EGGYEL eltolva jelennek
    // meg, mert a 0. tétel a PDF-fájl
    property var printers: []
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

    property string fitMode: "fit"          // PrintFitMode.FIT / .FILL
    property string orientation: "auto"     // PrintOrientation

    // #1590: indexkép-elrendezés (több bélyegkép egy lapon). A rács
    // oszlopszáma a felhasználóé — az eredeti nyomtatási előnézetéből ez
    // nem volt kiolvasható, a `stringres`-ben sincs rá kulcs (DÖNTÉS).
    property bool contactSheet: false
    property int contactColumns: 4

    // #1782: a nyomatméret (`0x00743700`) és a hozzá tartozó
    // minőség-összegzés. A méret TARTÓS — az eredetiben a
    // `Preferences\PrintLastSize` őrzi; nálunk a vezérlő teszi el.
    property string printSize: "M4X6"
    //: a mért öt méret felirata, a vezérlő azonosítói sorrendjében
    readonly property var printSizeLabels: [
        qsTr("3.5 x 5 in"), qsTr("4 x 6 in"), qsTr("5 x 7 in"),
        qsTr("8 x 10 in"), qsTr("Wallet")
    ]
    property var printSizeIds: []
    //: {smallest, small, total, ready, threshold} — a vezérlőtől
    property var quality: ({})

    function frissitsdAMinoseget() {
        if (!printWindow.printCtl) return
        printWindow.quality = printWindow.printCtl.printQuality(
            printWindow.rows, printWindow.printSize)
        printWindow.frissitsdAzElonezetet()
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
        if (!printWindow.printCtl || printWindow.contactSheet) {
            printWindow.previewPageCount = 0
            printWindow.previewSource = ""
            return
        }
        var lapok = printWindow.printCtl.printPageCount(
            printWindow.rows, printWindow.copies)
        printWindow.previewPageCount = lapok
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
            printWindow.copies, printWindow.previewPage, cel)
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
    // a feladatból kimaradt képek nevei (videó/RAW: a `QImage` nem nyitja
    // meg őket, a rácsban viszont látszanak) — ld. `printSkipped`
    property var lastSkipped: []

    readonly property bool canPrint:
        printWindow.printCtl !== null
        && printWindow.rows.length > 0
        && (!printWindow.pdfSelected || printWindow.pdfTarget.length > 0)

    // #1590: a `Mappa ▸ Bélyegképek nyomtatása…` belépési pontja —
    // ugyanaz a párbeszéd, indexkép-elrendezésre állítva
    function openForContactSheet(targetRows) {
        printWindow.openForRows(targetRows)
        printWindow.contactSheet = true
    }

    function openForRows(targetRows) {
        printWindow.rows = targetRows ? targetRows : []
        // #1782: a megjegyzett méret visszatöltése, majd a minőség-mérés
        if (printWindow.printCtl) {
            printWindow.printSizeIds = printWindow.printCtl.printSizes()
            printWindow.printSize = printWindow.printCtl.printSize()
        }
        printWindow.frissitsdAMinoseget()
        printWindow.lastResult = ""
        printWindow.lastSkipped = []
        // ⚠️ #1590: az elrendezés NEM élheti túl a bezárást. Ha az
        // indexkép-mód megmaradna, a Ctrl+P legközelebb szó nélkül
        // indexképet nyomtatna — a felhasználó meg képenként egy lapot vár.
        printWindow.contactSheet = false
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
        printWindow.visible = true
    }

    function startPrint() {
        if (!printWindow.printCtl) return
        printWindow.lastError = ""
        printWindow.lastResult = ""
        printWindow.lastSkipped = []
        // a gomb ilyenkor szürke, tehát ide kattintással nem lehet eljutni —
        // de a néma elutasítás annyira visszatérő hibánk, hogy a
        // programozott hívás se maradhat szótlan
        if (printWindow.rows.length === 0) {
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
        }
        function onPrintFailed(message) {
            printWindow.lastResult = ""
            printWindow.lastError = message
        }
        function onPrintSkipped(names) {
            printWindow.lastSkipped = names
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Text {
            objectName: "printSelectionText"
            Layout.fillWidth: true
            text: printWindow.contactSheet
                  ? qsTr("Pictures to print: %1 (contact sheet)")
                        .arg(printWindow.rows.length)
                  : qsTr("Pictures to print: %1 (one per page)")
                        .arg(printWindow.rows.length)
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        // -- elrendezés (#1590) -------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: qsTr("Layout:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            RowLayout {
                spacing: 16
                RadioButton {
                    objectName: "printOnePerPageRadio"
                    text: qsTr("One picture per page")
                    checked: !printWindow.contactSheet
                    onClicked: printWindow.contactSheet = false
                }
                RadioButton {
                    objectName: "printContactSheetRadio"
                    text: qsTr("Contact sheet")
                    checked: printWindow.contactSheet
                    onClicked: printWindow.contactSheet = true
                }
                Text {
                    visible: printWindow.contactSheet
                    text: qsTr("Columns:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                SpinBox {
                    objectName: "printContactColumnsBox"
                    visible: printWindow.contactSheet
                    from: 1
                    to: 10
                    value: printWindow.contactColumns
                    onValueModified: printWindow.contactColumns = value
                }
            }
        }

        // -- nyomatméret + minőség-ellenőrzés (#1782) ---------------------
        // Az eredeti panel a választott mérethez kiszámolja minden kép
        // effektív felbontását, és nyomtatás ELŐTT szól, ha valamelyik túl
        // kicsi. Enélkül egy 640×480-as kép szó nélkül ment ki 8×10-re.
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            visible: !printWindow.contactSheet
            Text {
                text: qsTr("Print size:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ComboBox {
                id: printSizeBox
                objectName: "printSizeBox"
                Layout.fillWidth: true
                model: printWindow.printSizeLabels
                currentIndex: Math.max(
                    0, printWindow.printSizeIds.indexOf(printWindow.printSize))
                onActivated: {
                    var azonosito = printWindow.printSizeIds[currentIndex]
                    if (!azonosito) return
                    printWindow.printSize = azonosito
                    // a méret TARTÓS (`PrintLastSize`) — azonnal eltesszük
                    if (printWindow.printCtl)
                        printWindow.printCtl.setPrintSize(azonosito)
                    printWindow.frissitsdAMinoseget()
                }
            }
            // #1819: KÉPENKÉNTI példányszám. A felirat az `IDS_COPIES`
            // (`ThumbUIPrint::PrintCount`); a két gomb az `addprintsbutton`
            // és a `subprintsbutton`.
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
                    ToolTip.delay: 500
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
                        //: A mért `%d / %d` alak.
                        text: (printWindow.previewPage + 1) + " / "
                              + printWindow.previewPageCount
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
                    //: `ThumbUIPrint::Smallest`
                    var sor = qsTr("Smallest picture: %1 pixels/inch.")
                                  .arg(q.smallest)
                    if (q.small > 0) {
                        //: `ThumbUIPrint::ReviewPrompt` — az egyes/többes
                        //: szám az eredetiben is külön erőforrás
                        var db = q.small === 1
                            ? qsTr("%1 small picture found.").arg(q.small)
                            : qsTr("%1 small pictures found.").arg(q.small)
                        return sor + " " + db + " "
                               + qsTr("Please review before printing.")
                    }
                    return sor + " " + qsTr("You are ready to print.")
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
            ComboBox {
                id: printerBox
                objectName: "printPrinterBox"
                Layout.fillWidth: true
                model: [qsTr("Print to a PDF file...")].concat(printWindow.printers)
                // a `currentIndex` a választó SAJÁTJA — a párbeszéd innen
                // olvassa (`printerIndex`), nem fordítva (ld. ott)
            }
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
            ComboBox {
                id: orientationBox
                objectName: "printOrientationBox"
                readonly property var values: ["auto", "portrait", "landscape"]
                Layout.preferredWidth: 200
                model: [qsTr("Automatic"), qsTr("Portrait"), qsTr("Landscape")]
                currentIndex: 0
                onActivated: printWindow.orientation = values[currentIndex]
            }
        }

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

        Text {
            objectName: "printResultText"
            visible: printWindow.lastResult.length > 0
            text: qsTr("Finished: %1").arg(printWindow.lastResult)
            color: Theme.picasaGreen
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
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

    FileDialog {
        id: pdfTargetDialog
        title: qsTr("Print to a PDF file...")
        fileMode: FileDialog.SaveFile
        defaultSuffix: "pdf"
        nameFilters: [qsTr("PDF documents (*.pdf)")]
        onAccepted: printWindow.pdfTarget = selectedFile.toString()
    }
}
