import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Az Útlevélkép (#1401) hibaablaka — a főablakhoz kötött, modális
// párbeszéd (a `Main.qml` halasztott betöltője a főablak tartalmában
// hozza létre, tehát a főablak FÖLÖTT jelenik meg).
//
// Élő mérés (picasa-colab-jobs #49/#50): a `CThumbUI::Passportfail`
// („Try another picture?") az ablak CÍME, nem igen/nem kérdés; benne a
// hibaszöveg (`Passport0` / `Passport1`) és EGYETLEN OK gomb.
//
// A két saját ág (olvashatatlan kép, ki nem írható kivágás) nem arc-hiba:
// ott a cím a parancs neve, és a szöveg a valódi okot mondja.
Dialog {
    id: root
    objectName: "passportErrorDialog"
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    // #1748: rögzített `implicitWidth`, különben a Fusion-stílus kötési
    // hurkot jelez a tartalomtól függő szélességre
    implicitWidth: 320 + leftPadding + rightPadding

    property string message: ""

    //: `kind`: "noFace" · "multipleFaces" · "read" · "write"
    function showError(kind) {
        if (kind === "noFace") {
            //: `CThumbUI::Passportfail`
            root.title = qsTr("Try another picture?")
            //: `CThumbUI::Passport0`
            root.message = qsTr("Can't find any faces")
        } else if (kind === "multipleFaces") {
            root.title = qsTr("Try another picture?")
            //: `CThumbUI::Passport1`
            root.message = qsTr("There appear to be multiple faces.")
        } else if (kind === "read") {
            //: `eMenuTools::ID_PASSPORT` menüfelirata, gyorsbillentyű nélkül
            root.title = qsTr("Passport photo")
            root.message = qsTr("The picture could not be read.")
        } else {
            root.title = qsTr("Passport photo")
            root.message = qsTr("The cropped picture could not be saved.")
        }
        root.open()
    }

    ColumnLayout {
        spacing: 12
        width: 320

        Text {
            objectName: "passportErrorMessage"
            Layout.preferredWidth: 320
            text: root.message
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        PicasaButton {
            objectName: "passportErrorOkButton"
            Layout.alignment: Qt.AlignRight
            text: qsTr("OK")
            onClicked: root.close()
        }
    }
}
