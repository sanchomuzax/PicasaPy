import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Adatbázis áthelyezése (#368, `move_database.fen` + `moving_database.fen`):
// az index-SQLite + a thumbnail-cache átköltöztetése új mappába.
//
// A FEN-eredetiben KÉT külön ablak van, és NEM egyszerre: ez itt a VÁLASZTÓ
// (`move_database.fen`), a haladásjelző (`moving_database.fen`) pedig a
// KÖVETKEZŐ induláskor jelenik meg — a mért eredeti a gombra csak szándékot
// rögzít, és a másolás indulásnál fut (#3214, `StartupRelocateWindow.qml`).
// Ez az ablak ezért soha nem költöztet: kiválaszt, ellenőriztet, előjegyez.
// Az eredeti "ne hálózati/cserélhető meghajtóra helyezze át"
// figyelmeztetés NÁLUNK NEM igaz — a PicasaPy-nál a NAS/hálózati mappa a
// NORMÁL használati eset (CLAUDE.md 7. döntés, "ismételhető migráció"), a
// szöveg ezért erre a tényre hívja fel a figyelmet ahelyett, hogy
// lebeszélne róla.
Window {
    id: moveDatabaseWindow
    objectName: "moveDatabaseDialog"
    title: qsTr("Move Database")
    modality: Qt.ApplicationModal
    width: 560
    height: scheduledLocation.length > 0 ? 340 : 300
    minimumWidth: 480
    minimumHeight: 260
    color: Theme.canvasBg

    // a `pathbox name="current_location"`/`name="new_location"` (FEN)
    // megfelelője — a jelenlegi hely a controllertől jön (csak-olvasható)
    readonly property string currentLocation:
        //: #1956: `typeof` a NÉVRE, `&&` az ÉRTÉKRE
        (typeof relocateController !== "undefined" && relocateController)
            ? relocateController.currentLocation : ""
    // a `FolderDialog selectedFolder.toString()`-ja (file:// URL is lehet)
    property string newLocation: ""
    //: #1629: OS-natív alak — ld. az `ImportSourceDialog` azonos kötését.
    readonly property string newLocationDisplay:
        (typeof fileOpsController !== "undefined" && fileOpsController)
            ? fileOpsController.toLocalPath(moveDatabaseWindow.newLocation)
            : moveDatabaseWindow.newLocation.replace(/^file:\/\//, "")

    property string lastError: ""
    //: a KÖVETKEZŐ indulásra előjegyzett cél (#3214) — üres, ha nincs ilyen
    property string scheduledLocation: ""

    function open() {
        moveDatabaseWindow.newLocation = ""
        moveDatabaseWindow.lastError = ""
        moveDatabaseWindow.scheduledLocation = ""
        moveDatabaseWindow.visible = true
    }

    function startMove() {
        if (moveDatabaseWindow.newLocation.length === 0) return
        moveDatabaseWindow.lastError = ""
        relocateController.startRelocate(moveDatabaseWindow.newLocation)
    }

    Connections {
        target: typeof relocateController !== "undefined" ? relocateController : null
        function onRelocateScheduled(newRoot) {
            moveDatabaseWindow.scheduledLocation = newRoot
        }
        function onRelocateFailed(message) {
            moveDatabaseWindow.scheduledLocation = ""
            moveDatabaseWindow.lastError = message
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        // -- magyarázó szöveg (a FEN két figyelmeztető labelje helyett,
        // átfogalmazva — nálunk a NAS/hálózati hely a NORMÁL eset) --------
        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            //: #3214: a költözés a KÖVETKEZŐ induláskor fut le — ezért NEM
            //: kérünk külön újraindítást, ahogy a mért eredeti sem.
            text: qsTr(
                "Move the photo index and thumbnail cache to a new folder. "
                + "PicasaPy moves them the next time it starts.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }
        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr(
                "Network drives (e.g. a NAS) are fully supported and are "
                + "the normal setup for PicasaPy — make sure the drive "
                + "stays connected while the app is running.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        // -- jelenlegi hely (csak olvasható) -------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: qsTr("Current database location:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                objectName: "moveDatabaseCurrentPathText"
                Layout.fillWidth: true
                elide: Text.ElideMiddle
                text: moveDatabaseWindow.currentLocation
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
        }

        // -- új hely --------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: qsTr("New database location:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text {
                    objectName: "moveDatabaseNewPathText"
                    Layout.fillWidth: true
                    elide: Text.ElideMiddle
                    text: moveDatabaseWindow.newLocationDisplay.length > 0
                          ? moveDatabaseWindow.newLocationDisplay
                          : qsTr("(none selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                PicasaButton {
                    objectName: "moveDatabaseBrowseButton"
                    text: qsTr("Browse...")
                    onClicked: newLocationDialog.open()
                }
                PicasaButton {
                    objectName: "moveDatabaseDefaultButton"
                    text: qsTr("Default")
                    onClicked: moveDatabaseWindow.newLocation =
                        moveDatabaseWindow.currentLocation
                }
            }
        }

        Text {
            objectName: "moveDatabaseErrorText"
            visible: moveDatabaseWindow.lastError.length > 0
            text: moveDatabaseWindow.lastError
            color: Theme.brandRed
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Text {
            objectName: "moveDatabaseResultText"
            visible: moveDatabaseWindow.scheduledLocation.length > 0
            //: #3214: a költözés a KÖVETKEZŐ induláskor fut le — a mért
            //: eredeti is így teszi, és így a másolás nem fut olyankor,
            //: amikor a program még a régi helyet használja.
            text: qsTr("PicasaPy will move the database the next time it starts.")
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
                objectName: "moveDatabaseMoveButton"
                text: qsTr("Move on next restart")
                accent: Theme.picasaGreen
                enabled: moveDatabaseWindow.newLocation.length > 0
                         && moveDatabaseWindow.scheduledLocation.length === 0
                onClicked: moveDatabaseWindow.startMove()
            }
            PicasaButton {
                objectName: "moveDatabaseUndoScheduleButton"
                text: qsTr("Cancel the move")
                visible: moveDatabaseWindow.scheduledLocation.length > 0
                onClicked: {
                    relocateController.cancelScheduledRelocate()
                    moveDatabaseWindow.scheduledLocation = ""
                }
            }
            PicasaButton {
                objectName: "moveDatabaseCloseButton"
                text: qsTr("Close")
                onClicked: moveDatabaseWindow.visible = false
            }
        }
    }

    FolderDialog {
        id: newLocationDialog
        title: qsTr("Choose new database location...")
        onAccepted: moveDatabaseWindow.newLocation = selectedFolder.toString()
    }
}
