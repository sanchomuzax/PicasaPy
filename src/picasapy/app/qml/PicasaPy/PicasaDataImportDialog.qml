import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Import a Picasából (#3132) — a db3 kulcsszavainak, helyadatának és
// arcainak átvétele a `.picasa.ini`-be.
//
// SAJÁT FUNKCIÓ: az eredeti Picasának nincs mit másolni ezen a ponton — ő
// MAGA a db3 gazdája, nekünk viszont át kell vennünk tőle. A helyét a
// tulajdonos választotta (2026-09-18): menüpont, tehát KÉRÉSRE fut és
// megismételhető.
//
// A haladás SZÁNDÉKOSAN határozatlan: a mag mappánként dolgozik, és a
// mappák számát csak a db3 végigolvasása után tudnánk — kitalálni hazugság
// lenne (ugyanaz a döntés, mint a CompactDatabaseDialog-nál).
//
// A VÉGÉN a felhasználó SZÁMOKAT kap: hány mappát érintettünk, hány fotóra
// került kulcsszó / hely / név, és hányat hagytunk ki azért, mert ott már
// állt adat. Az utolsó szám nélkül a „miért nem lett meg mind?" kérdésre
// nincs válasz — ezért van kiírva külön.
Window {
    id: importWindow
    objectName: "picasaDataImportDialog"
    title: qsTr("Import from Picasa")
    modality: Qt.ApplicationModal
    width: 460
    height: 280
    color: Theme.canvasBg

    // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
    // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
    readonly property bool running:
        (typeof picasaImportController !== "undefined" && picasaImportController
            && picasaImportController.running !== undefined)
                ? picasaImportController.running : false

    property bool finished: false
    property bool nothingFound: false
    property string lastError: ""
    property int mappak: 0
    property int kulcsszo: 0
    property int hely: 0
    property int arc: 0
    property int kihagyott: 0

    function open() {
        importWindow.finished = false
        importWindow.nothingFound = false
        importWindow.lastError = ""
        importWindow.mappak = 0
        importWindow.kulcsszo = 0
        importWindow.hely = 0
        importWindow.arc = 0
        importWindow.kihagyott = 0
        importWindow.visible = true
        if (typeof picasaImportController === "undefined"
                || !picasaImportController)
            return
        picasaImportController.startImport()
    }

    Connections {
        target: (typeof picasaImportController !== "undefined")
            ? picasaImportController : null
        function onImportFinished(mappak, kulcsszo, hely, arc, kihagyott) {
            importWindow.mappak = mappak
            importWindow.kulcsszo = kulcsszo
            importWindow.hely = hely
            importWindow.arc = arc
            importWindow.kihagyott = kihagyott
            importWindow.finished = true
        }
        function onImportFailed(message) { importWindow.lastError = message }
        function onNoInstallationFound() { importWindow.nothingFound = true }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        Label {
            objectName: "picasaImportHeadline"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Theme.ink
            text: importWindow.lastError !== ""
                ? qsTr("The import could not finish: %1").arg(importWindow.lastError)
                : importWindow.nothingFound
                    ? qsTr("No Picasa data found on this computer.")
                    : importWindow.finished
                        ? qsTr("Done.")
                        : qsTr("Copying names, keywords and places from Picasa...")
        }

        BusyIndicator {
            running: importWindow.running
            visible: importWindow.running
            Layout.alignment: Qt.AlignHCenter
        }

        Label {
            objectName: "picasaImportResult"
            visible: importWindow.finished && importWindow.lastError === ""
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Theme.ink
            //: %1 mappa, %2 kulcsszó, %3 hely, %4 név
            text: qsTr("%1 folder(s) updated: %2 keyword(s), %3 place(s), %4 name(s).")
                .arg(importWindow.mappak).arg(importWindow.kulcsszo)
                .arg(importWindow.hely).arg(importWindow.arc)
        }

        Label {
            objectName: "picasaImportSkipped"
            visible: importWindow.finished && importWindow.kihagyott > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Theme.ink
            //: azért maradt ki, mert a képnél MÁR volt adat — nem írjuk felül
            text: qsTr("%1 photo(s) were left untouched because they already had data.")
                .arg(importWindow.kihagyott)
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Button {
                objectName: "picasaImportCloseButton"
                text: importWindow.running ? qsTr("Close") : qsTr("OK")
                enabled: !importWindow.running
                onClicked: importWindow.visible = false
            }
        }
    }
}
