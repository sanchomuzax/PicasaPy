import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Adatbázis áthelyezése (#368, `move_database.fen` + `moving_database.fen`):
// az index-SQLite + a thumbnail-cache átköltöztetése új mappába.
//
// A FEN-eredetiben KÉT külön ablak van (a választó + a haladásjelző) — itt
// EGY, önálló, mozgatható/átméretezhető Window-ba vonva (a DedupDialog/
// ImportSourceDialog mintája), a haladás-szakasz csak áthelyezés közben
// látszik. Az eredeti "ne hálózati/cserélhető meghajtóra helyezze át"
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
    height: relocating || lastResultLocation.length > 0 ? 360 : 300
    minimumWidth: 480
    minimumHeight: 260
    color: Theme.canvasBg

    // a `pathbox name="current_location"`/`name="new_location"` (FEN)
    // megfelelője — a jelenlegi hely a controllertől jön (csak-olvasható)
    readonly property string currentLocation:
        typeof relocateController !== "undefined"
            ? relocateController.currentLocation : ""
    // a `FolderDialog selectedFolder.toString()`-ja (file:// URL is lehet)
    property string newLocation: ""
    readonly property string newLocationDisplay:
        moveDatabaseWindow.newLocation.replace(/^file:\/\//, "")

    property bool relocating: false
    property string progressPhase: ""
    property int progressDone: 0
    property int progressTotal: 0

    property string lastError: ""
    property string lastResultLocation: ""  // sikeres áthelyezés után az új hely
    property bool lastCancelled: false

    function open() {
        moveDatabaseWindow.newLocation = ""
        moveDatabaseWindow.lastError = ""
        moveDatabaseWindow.lastResultLocation = ""
        moveDatabaseWindow.lastCancelled = false
        moveDatabaseWindow.visible = true
    }

    function startMove() {
        if (moveDatabaseWindow.newLocation.length === 0) return
        moveDatabaseWindow.lastError = ""
        moveDatabaseWindow.lastCancelled = false
        relocateController.startRelocate(moveDatabaseWindow.newLocation)
    }

    Connections {
        target: typeof relocateController !== "undefined" ? relocateController : null
        function onRelocateStarted() {
            moveDatabaseWindow.relocating = true
            moveDatabaseWindow.progressPhase = ""
            moveDatabaseWindow.progressDone = 0
            moveDatabaseWindow.progressTotal = 0
        }
        function onRelocateProgress(phase, done, total) {
            moveDatabaseWindow.progressPhase = phase
            moveDatabaseWindow.progressDone = done
            moveDatabaseWindow.progressTotal = total
        }
        function onRelocateFinished(newRoot) {
            moveDatabaseWindow.relocating = false
            moveDatabaseWindow.lastResultLocation = newRoot
        }
        function onRelocateFailed(message) {
            moveDatabaseWindow.relocating = false
            moveDatabaseWindow.lastError = message
        }
        function onRelocateCancelled() {
            moveDatabaseWindow.relocating = false
            moveDatabaseWindow.lastCancelled = true
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
            text: qsTr(
                "Move the photo index and thumbnail cache to a new folder. "
                + "A restart is required afterwards for the change to take "
                + "effect.")
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
            enabled: !moveDatabaseWindow.relocating
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
            objectName: "moveDatabaseCancelledText"
            visible: moveDatabaseWindow.lastCancelled
            text: qsTr("Move cancelled — nothing was changed.")
            color: Theme.textGray
            font.pixelSize: Theme.fontSize
        }

        // -- haladás-nézet (`moving_database.fen`) ---------------------------
        ColumnLayout {
            Layout.fillWidth: true
            visible: moveDatabaseWindow.relocating
            spacing: 6

            Text {
                text: qsTr("PicasaPy is moving the database.")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 8
                radius: 4
                color: Theme.trackBg
                border.color: Theme.chromeBorder

                Rectangle {
                    objectName: "moveDatabaseProgressFill"
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    radius: parent.radius
                    color: Theme.picasaGreen
                    width: moveDatabaseWindow.progressTotal > 0
                           ? parent.width * moveDatabaseWindow.progressDone
                                 / moveDatabaseWindow.progressTotal
                           : 0
                }
            }

            PicasaButton {
                objectName: "moveDatabaseCancelProgressButton"
                text: qsTr("Cancel")
                onClicked: relocateController.cancelRelocate()
            }
        }

        Text {
            objectName: "moveDatabaseResultText"
            visible: moveDatabaseWindow.lastResultLocation.length > 0
            text: qsTr("Database moved. Restart PicasaPy for the change to take effect.")
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
                         && !moveDatabaseWindow.relocating
                         && moveDatabaseWindow.lastResultLocation.length === 0
                onClicked: moveDatabaseWindow.startMove()
            }
            PicasaButton {
                objectName: "moveDatabaseCloseButton"
                text: qsTr("Close")
                enabled: !moveDatabaseWindow.relocating
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
