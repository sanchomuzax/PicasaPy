import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Első indítás: az `initialscan` panel (#449 → #1167).
//
// Az eredeti Picasa első indításakor nem a Mappakezelő nyílik, hanem ez a
// panel (`tre:initialscan`, kezelő `0x005b77c0`). Teljes levezetés:
// `docs/specs/picasa-elso-inditas.md`. A hűség pontjai:
//
// - KÉT teljes szövegkészlet ugyanarra a felületre: MIGRÁCIÓS (`Text1`,
//   ha van korábbi Picasa-telepítés — `0x0040d450`) és TISZTA TELEPÍTÉS
//   (`Text2`); a szövegek az EREDETI Picasa szövegei (a magyar a
//   Picasa3i18n.dll fordítása);
// - a MIGRÁCIÓS változat KÉTLÉPCSŐS (`0x005b7eeb`): a „frissítés"
//   választás után ugyanez a felület átvált a keresési kérdésre, és csak
//   a következő „Continue" zár — a frissítés-ág a meglévő
//   Picasa-átvételt nyitja (#146);
// - a Mégse gomb az eredetiben REJTETT (`initialscan/cancel: m_hidden`):
//   egyetlen „Continue" van. Az ABLAK bezárása viszont az eredetiben is
//   megszakítás (−1, `0x005b7e69`): nincs mappa-felvétel, és a panel a
//   következő induláskor újra megjelenik — ezért NEM zárjuk le a
//   kihagyás útját erőszakkal, hanem ugyanezt tesszük;
// - a rádiók 100 képpontos osztása és a 640-es vászonszélesség a mért
//   geometriát követi (`docbounds` 640×463).
//
// A „teljes gép" leképezése (kötetek; a /mnt kihagyása) az
// `initial_scan.py` docstringjében van kimondva.
Dialog {
    id: initialScan
    objectName: "initialScanDialog"
    title: qsTr("Picasa")
    modal: true
    anchors.centerIn: parent
    // az eredetiben nincs Mégse gomb, de az ablak bezárható (Esc is) —
    // a bezárás megszakítás: nem veszünk fel semmit, és a panel a
    // következő induláskor újra jön (`needsInitialScan` marad igaz)
    closePolicy: Popup.CloseOnEscape
    standardButtons: Dialog.NoButton

    // true = a migrációs szövegkészlet (`Text1`) van a felületen
    property bool migrationStep: false
    // a migrációs első lépcső „frissítés" választása — a végső Continue
    // után ebből nyílik a Picasa-átvétel (#146)
    property bool updateChosen: false
    // #146: a migrációs ág kéri a PicasaImportDialog megnyitását
    signal importRequested()

    property string choice: "narrow"

    // #305: null-őr — a kontextus-property az engine fel-/leépítésekor
    // átmenetileg hiányozhat
    readonly property var ctl:
        typeof controller !== "undefined" ? controller : null

    function openIfNeeded() {
        if (!initialScan.ctl || !initialScan.ctl.needsInitialScan) return
        initialScan.migrationStep = initialScan.ctl.initialScanMigration()
        initialScan.updateChosen = false
        initialScan.choice = "narrow"
        open()
    }

    // a „Continue" — az eredeti kezelő (`0x005b7e80`) fordítása
    function acceptChoice() {
        if (initialScan.migrationStep) {
            if (initialScan.choice === "narrow") {
                // „A meglévő képtár frissítése": átváltás a keresési
                // kérdésre (`0x005b7eeb`) — az ablak NYITVA marad
                initialScan.updateChosen = true
                initialScan.migrationStep = false
                initialScan.choice = "narrow"
                return
            }
            // „Képek ismételt keresése": az eredeti a teljes-gép kóddal
            // zár (`0x005b7ee9` → `0x5b7f3f`)
            initialScan.ctl.applyInitialScan("wide")
            initialScan.close()
            return
        }
        initialScan.ctl.applyInitialScan(initialScan.choice)
        initialScan.close()
        if (initialScan.updateChosen)
            initialScan.importRequested()
    }

    ColumnLayout {
        spacing: 10

        // `text2` — a kérdés (az eredeti 600 széles hasábja)
        Text {
            objectName: "initialScanQuestionText"
            Layout.preferredWidth: 600
            wrapMode: Text.WordWrap
            text: initialScan.migrationStep
                  ? qsTr("There is an older version of Picasa installed.  Would you like to update your existing picture library, or search your computer for pictures again?")
                  : qsTr("Picasa is ready to search for pictures on your computer")
            font.pixelSize: Theme.fontSize + 3
            font.bold: true
            color: Theme.ink
        }

        RadioButton {
            objectName: "initialScanNarrow"
            text: initialScan.migrationStep
                  ? qsTr("Update my existing picture library")
                  : qsTr("Only search Documents, Pictures, and the Desktop")
            font.bold: true
            checked: initialScan.choice === "narrow"
            onClicked: initialScan.choice = "narrow"
        }
        Text {
            objectName: "initialScanNarrowDetail"
            Layout.preferredWidth: 549
            Layout.leftMargin: 36
            wrapMode: Text.WordWrap
            text: initialScan.migrationStep
                  ? qsTr("Choose this option if you use keywords or custom albums in Picasa 1, and you want to preserve these in Picasa 3.")
                  : qsTr("Choose this option if you only store your pictures in these folders.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        RadioButton {
            objectName: "initialScanWide"
            text: initialScan.migrationStep
                  ? qsTr("Search my computer for pictures again")
                  : qsTr("Search my whole computer for pictures")
            font.bold: true
            checked: initialScan.choice === "wide"
            onClicked: initialScan.choice = "wide"
        }
        Text {
            objectName: "initialScanWideDetail"
            Layout.preferredWidth: 549
            Layout.leftMargin: 36
            wrapMode: Text.WordWrap
            text: initialScan.migrationStep
                  ? qsTr("Choose this option for a more complete search of your computer, which includes extended picture information.  It will preserve your existing edits and organization, but it will not preserve keywords.  This search may take several minutes.")
                  : qsTr("Choose this option if you have pictures stored in various folders across your computer, especially if you have pictures stored on more than one hard drive.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        // a hatókör ELŐRE látszik (#449) — a keresési kérdésnél marad
        Text {
            objectName: "initialScanScopeText"
            visible: !initialScan.migrationStep
            Layout.preferredWidth: 600
            wrapMode: Text.WordWrap
            text: initialScan.ctl
                  ? initialScan.ctl.initialScanFolders(initialScan.choice).join("\n")
                  : ""
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        // `text5` — az eredeti lábjegyzet-ígérete, mindkét változatban
        Text {
            objectName: "initialScanReassuranceText"
            Layout.preferredWidth: 600
            wrapMode: Text.WordWrap
            text: qsTr("Searching for pictures never moves or copies files to new locations. You can choose which folders are displayed by Picasa by using the Folder Manager tool (available from the Tools menu)")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        // „Continue" jobbra (522,423 a 640-es vásznon) — Mégse nincs
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Button {
                objectName: "initialScanContinue"
                text: qsTr("Continue")
                onClicked: initialScan.acceptChoice()
            }
        }
    }
}
