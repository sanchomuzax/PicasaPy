import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Adatbázis-tömörítés (#449, `compacting.fen`).
//
// Az eredeti ablak (`title="Compacting"`) három dolgot csinált, és semmi
// mást: megmondta, hogy MIÉRT vár a felhasználó, kiírta, hogy ez PERCEKIG
// tarthat, és adott egy **Mégse** gombot. Ez a három marad itt is.
//
// Haladás-sáv van, de SZÁNDÉKOSAN határozatlan (busy): az SQLite `VACUUM`
// nem mond százalékot, kitalálni pedig hazugság lenne. A vezérlő
// „szívverést" küld — abból látszik, hogy dolgozik, nem fagyott le.
Window {
    id: compactWindow
    objectName: "compactDatabaseDialog"
    title: qsTr("Compacting")
    modality: Qt.ApplicationModal
    width: 460
    height: 240
    color: Theme.canvasBg

    // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
    // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
    readonly property bool running:
        (typeof compactController !== "undefined" && compactController
            && compactController.running !== undefined)
                ? compactController.running : false

    property string lastError: ""
    property bool lastCancelled: false
    property bool finished: false
    property bool nothingToDo: false
    property int savedBytes: 0

    // Az eredeti Picasa NEM tömörített minden alkalommal: volt egy
    // `compactpercentage` küszöb, ami alatt a művelet meg sem indult. Ezt
    // átvesszük — percekig tartó munkát nem indítunk el azért, hogy a
    // végén „0 bájt megtakarítva" legyen az eredmény.
    function open() {
        compactWindow.lastError = ""
        compactWindow.lastCancelled = false
        compactWindow.finished = false
        compactWindow.nothingToDo = false
        compactWindow.savedBytes = 0
        compactWindow.visible = true
        if (typeof compactController === "undefined" || !compactController) return
        if (compactController.isWorthCompacting())
            compactController.startCompact()
        else
            compactWindow.nothingToDo = true
    }

    // az ablak bezárása futás közben = megszakítás (nem hagyunk gazdátlan
    // munkát a háttérben, amiről a felhasználó már nem lát semmit)
    onClosing: if (compactWindow.running) compactController.cancelCompact()

    Connections {
        target: typeof compactController !== "undefined" ? compactController : null
        function onCompactFinished(saved) {
            compactWindow.finished = true
            compactWindow.savedBytes = saved
        }
        function onCompactFailed(message) { compactWindow.lastError = message }
        function onCompactCancelled() { compactWindow.lastCancelled = true }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            //: az eredeti `compacting.fen` magyarázó szövege
            text: qsTr("PicasaPy is compacting its database to save disk "
                       + "space. This may take several minutes.")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        // `label name="status"` — behúzva, ahogy az eredetin
        Text {
            objectName: "compactStatusText"
            Layout.fillWidth: true
            Layout.leftMargin: 16
            wrapMode: Text.WordWrap
            text: compactWindow.lastError.length > 0
                  ? compactWindow.lastError
                  : compactWindow.nothingToDo
                    ? qsTr("The database is already compact — nothing to do.")
                    : compactWindow.lastCancelled
                      ? qsTr("Compacting cancelled. Your database is unchanged.")
                      : compactWindow.finished
                        ? qsTr("Done.")
                        : qsTr("Compacting...")
            font.pixelSize: Theme.fontSize
            color: compactWindow.lastError.length > 0
                   ? Theme.brandRed : Theme.textGray
        }

        ProgressBar {
            objectName: "compactProgressBar"
            Layout.fillWidth: true
            Layout.leftMargin: 16
            indeterminate: true
            visible: compactWindow.running
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            // egyetlen gomb, ahogy az eredetin — futás közben Mégse, utána
            // Bezárás (nincs mit megszakítani)
            Button {
                objectName: "compactCancelButton"
                text: compactWindow.running ? qsTr("Cancel") : qsTr("Close")
                onClicked: {
                    if (compactWindow.running) {
                        if (typeof compactController !== "undefined"
                                && compactController)
                            compactController.cancelCompact()
                    } else {
                        compactWindow.visible = false
                    }
                }
            }
        }
    }
}
