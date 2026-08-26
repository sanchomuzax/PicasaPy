import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Nyomtatás (#32 RÉSZLEGES kör, bekötve a #1472-ben) — a `Fájl ▸
// Nyomtatás…` (Ctrl+P) és a képtálca „Nyomtatás" gombja ezt nyitja.
//
// ⚠️ Ez NEM a Picasa teljes nyomtatási sablonrendszere (`print.fen` /
// `reviewprint.fen`: kontaktlap, több kép egy oldalon, állítható margó).
// A `print_controller.py` egy képet tesz egy oldalra — a párbeszéd
// ennyit kínál, és nem ígér többet. A `Mappa ▸ Bélyegképek nyomtatása…`
// ezért marad helyfoglaló: az kontaktlap, ami mögött nincs motor.
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
    readonly property var ctl:
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

    property string lastError: ""
    property string lastResult: ""
    // a feladatból kimaradt képek nevei (videó/RAW: a `QImage` nem nyitja
    // meg őket, a rácsban viszont látszanak) — ld. `printSkipped`
    property var lastSkipped: []

    readonly property bool canPrint:
        printWindow.ctl !== null
        && printWindow.rows.length > 0
        && (!printWindow.pdfSelected || printWindow.pdfTarget.length > 0)

    function openForRows(targetRows) {
        printWindow.rows = targetRows ? targetRows : []
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
        printWindow.lastError = printWindow.ctl
            ? "" : qsTr("Printing is unavailable: the Qt print support "
                        + "module is missing. On Debian/Ubuntu you can "
                        + "install it with: "
                        + "sudo apt install python3-pyside6.qtprintsupport")
        printWindow.printers = printWindow.ctl ? printWindow.ctl.listPrinters() : []
        printWindow.visible = true
    }

    function startPrint() {
        if (!printWindow.ctl) return
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
            printWindow.ctl.renderPrintPreviewPdf(
                printWindow.rows, printWindow.fitMode,
                printWindow.orientation, printWindow.pdfTarget)
            return
        }
        printWindow.ctl.printRows(
            printWindow.rows, printWindow.printerName,
            printWindow.fitMode, printWindow.orientation)
    }

    Connections {
        target: printWindow.ctl
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
            text: qsTr("Pictures to print: %1 (one per page)")
                  .arg(printWindow.rows.length)
            font.pixelSize: Theme.fontSize
            color: Theme.ink
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
        ColumnLayout {
            Layout.fillWidth: true
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
