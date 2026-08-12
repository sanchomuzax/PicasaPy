import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Első indítás: mit olvassunk be (#449).
//
// A Picasa egyetlen kérdést tett fel, mielőtt bármit csinált volna: a
// teljes gép, vagy csak a Dokumentumok/Képek/Asztal. Két dolgot érdemes
// szó szerint átvenni:
//
//  1. **Két választás, semmi több** — nem kért mappalistát, nem nyitott
//     fát; a finomhangolás utána, a Mappakezelőben történik.
//  2. **Egyetlen OK gomb, Mégse nélkül** — enélkül a program üres lenne.
//
// És a megnyugtatás, ami az eredetin mindkét képernyőn ott volt: a
// keresés SOHA nem mozgat és nem másol fájlt. Ez bizalomépítés, nem
// dísz — a felhasználó a saját képeit engedi be egy ismeretlen programba.
//
// A „teljes számítógép" linuxos megfelelője a HOME-könyvtár: a teljes
// fájlrendszer végigolvasása itt rossz ötlet (csatolt hálózati meghajtók,
// konténerek, rendszermappák).
Dialog {
    id: initialScan
    objectName: "initialScanDialog"
    title: qsTr("Welcome to PicasaPy")
    modal: true
    anchors.centerIn: parent
    closePolicy: Popup.NoAutoClose   // nincs Mégse: dönteni kell
    standardButtons: Dialog.Ok

    property string choice: "narrow"

    function openIfNeeded() {
        if (controller && controller.needsInitialScan) open()
    }

    onAccepted: controller.applyInitialScan(initialScan.choice)

    ColumnLayout {
        spacing: 10

        Text {
            Layout.preferredWidth: 420
            wrapMode: Text.WordWrap
            text: qsTr("Where should PicasaPy look for your pictures?")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
        }

        RadioButton {
            objectName: "initialScanNarrow"
            text: qsTr("Only search Documents, Pictures, and the Desktop")
            checked: initialScan.choice === "narrow"
            onClicked: initialScan.choice = "narrow"
        }
        RadioButton {
            objectName: "initialScanWide"
            text: qsTr("Search my whole home folder for pictures")
            checked: initialScan.choice === "wide"
            onClicked: initialScan.choice = "wide"
        }

        // a hatókör ELŐRE látszik — az eredeti is kiírta, mit fog nézni
        Text {
            objectName: "initialScanScopeText"
            Layout.preferredWidth: 420
            wrapMode: Text.WordWrap
            text: controller
                  ? controller.initialScanFolders(initialScan.choice).join("\n")
                  : ""
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        Text {
            objectName: "initialScanReassuranceText"
            Layout.preferredWidth: 420
            wrapMode: Text.WordWrap
            //: az eredeti megnyugtatása — mindkét képernyőjén ott volt
            text: qsTr("Searching never moves or copies your files. You can "
                       + "change these folders later in the Folder Manager.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
    }
}
