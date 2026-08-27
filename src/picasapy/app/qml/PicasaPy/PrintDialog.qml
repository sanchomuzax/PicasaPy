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
                printWindow.orientation, printWindow.pdfTarget)
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
            printWindow.fitMode, printWindow.orientation)
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
