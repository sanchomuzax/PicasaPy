import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Az Útlevélkép (#1401) hibaablaka + nyomtatási nézete.
//
// Az eredeti a nulla/több arc esetét EGYETLEN, OK gombos hibaablakkal
// jelzi — élő méréssel helyesbítve (picasa-colab-jobs #49/#50): a
// `CThumbUI::Passportfail` („Try another picture?") az ablak CÍME, nem
// egy igen/nem kérdés, és mindkét hibaágon UGYANAZ; csak a SZÖVEG tér el
// (`Passport0` „Nem találhatók arcok" / `Passport1` „Úgy tűnik, több arc
// van a képen.").
//
// A sikeres ágon a nézet a MÁR arc-központúan kivágott (négyzet) képet
// mutatja, rögzített `ePassport` mérettel (2,0 × 2,0 hüvelyk) és 1-es
// kezdő példányszámmal (`docs/specs/picasa-nyomtatas.md`, „LEZÁRVA: hány
// útlevélkép kerül egy lapra"). A lapra rendezést (rács, laptörés,
// egyenletes térköz emelkedő példányszámnál) a `PrintController`/
// `grid_layout` végzi — ugyanaz az út, mint bármely más nyomatméretnél
// (#3647), ezért ez a nézet szándékosan NEM ismétli meg a lapozó
// előnézetet: a képet és a példányszám-vezérlőt mutatja, a nyomtatás
// gombja a tényleges rácsba rendezést a Python-oldalon váltja ki.
Window {
    id: passportWindow
    objectName: "passportPrintDialog"
    title: qsTr("Passport photo")
    modality: Qt.ApplicationModal
    width: 420
    height: 480
    color: Theme.canvasBg
    visible: false

    property string imagePath: ""
    property int copies: 1
    property string printerName: ""
    property string lastError: ""

    //: `preparePassportPhoto` nulla vagy több arcot talált — a hívó ezt a
    //: függvényt hívja a megfelelő szöveggel.
    function showError(message) {
        errorDialog.message = message
        errorDialog.open()
    }

    //: `preparePassportPhoto` pontosan egy arcot talált és kivágta a
    //: képet — a `path` az ideiglenes (gyorstár-) fájl URL-je.
    function showReady(path) {
        passportWindow.imagePath = path
        passportWindow.copies = 1
        passportWindow.lastError = ""
        passportWindow.visible = true
    }

    Dialog {
        id: errorDialog
        objectName: "passportErrorDialog"
        //: `CThumbUI::Passportfail` — a hibaablak CÍME mindkét hibaágon
        //: (nulla arc / több arc), ld. a fájl fejlécét
        title: qsTr("Try another picture?")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        Text {
            width: 380
            text: errorDialog.message
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12

        Image {
            objectName: "passportPreviewImage"
            Layout.fillWidth: true
            Layout.preferredHeight: 240
            fillMode: Image.PreserveAspectFit
            source: passportWindow.imagePath
            cache: false
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                text: qsTr("Printer:")
                color: Theme.ink
            }
            ComboBox {
                id: printerCombo
                objectName: "passportPrinterCombo"
                Layout.fillWidth: true
                model: (typeof printController !== "undefined" && printController)
                    ? printController.listPrinters() : []
                onCurrentTextChanged: passportWindow.printerName = currentText
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 8
            Text {
                //: az eredeti panel felirata („Copies per Photo") —
                //: ld. `PrintDialog.qml`
                text: qsTr("Copies per Photo:")
                color: Theme.ink
            }
            PicasaButton {
                objectName: "passportCopiesMinusButton"
                text: "-"
                enabled: passportWindow.copies > 1
                onClicked: passportWindow.copies -= 1
            }
            Text {
                objectName: "passportCopiesLabel"
                text: passportWindow.copies
                color: Theme.ink
            }
            PicasaButton {
                objectName: "passportCopiesPlusButton"
                text: "+"
                onClicked: passportWindow.copies += 1
            }
        }

        Text {
            objectName: "passportPrintError"
            Layout.fillWidth: true
            visible: passportWindow.lastError.length > 0
            wrapMode: Text.WordWrap
            text: passportWindow.lastError
            color: "#c0392b"
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8
            PicasaButton {
                objectName: "passportCancelButton"
                text: qsTr("Cancel")
                onClicked: passportWindow.visible = false
            }
            PicasaButton {
                objectName: "passportPrintButton"
                text: qsTr("Print")
                onClicked: {
                    if (typeof printController === "undefined" || !printController)
                        return
                    var ok = printController.printPassportPhoto(
                        passportWindow.imagePath, passportWindow.printerName,
                        passportWindow.copies)
                    if (ok)
                        passportWindow.visible = false
                }
            }
        }
    }

    Connections {
        target: typeof printController !== "undefined" ? printController : null
        function onPrintFailed(message) { passportWindow.lastError = message }
        function onPrintFinished(_target) { passportWindow.lastError = "" }
    }
}
