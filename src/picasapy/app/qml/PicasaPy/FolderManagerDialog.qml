import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Mappakezelő (Eszközök menü + első indítás), #231 — a Picasa 3.9
// mintájára ÖNÁLLÓ, mozgatható/átméretezhető ablak (nem a főablakba
// ékelt Dialog): bal oldalt a helyi fájlrendszer mappafája LUSTA
// betöltéssel (a fájlrendszer-olvasás a folderTreeController
// háttérszálán fut, ld. folder_tree_controller.py), jobb oldalt a
// kijelölt mappa háromállapotú (figyelt/egyszeri/nincs) választója —
// FolderStatePanel.qml —, alatta a figyelt mappák Picasa-kompatibilis
// összegző listája (a korábbi lapos Mappakezelő öröksége).
Window {
    id: folderManagerWindow
    objectName: "folderManagerDialog"
    title: qsTr("Folder Manager")
    modality: Qt.ApplicationModal
    width: 720
    height: 480
    minimumWidth: 540
    minimumHeight: 340
    color: Theme.canvasBg

    // a fa gyökere — alapból a teljes fájlrendszer (Linux-first: "/"),
    // tesztek felülírhatják (setProperty) egy ideiglenes könyvtárra
    property string rootPath: "/"
    property string selectedPath: ""
    // a kijelölt mappa TÉNYLEGES állapota (backend: watchedFolders +
    // kliens-oldali "épp elindított egyszeri keresés" jelző)
    readonly property string selectedState: folderManagerWindow.stateFor(folderManagerWindow.selectedPath)

    // kliens-oldali jelző: melyik mappára indítottunk „Keresés egyszer"-t
    // EBBEN a dialógus-munkamenetben. A valódi Picasa sem emlékszik erre
    // újraindítás/dialógus-újranyitás után (7. rögzített döntés szellemében
    // csak azt tükrözzük, amit a backend ténylegesen tud): a mappa fotói
    // véglegesen bekerülnek a könyvtárba, de a mappa nem marad figyelve.
    property var onceScanned: ({})

    property var rootChildren: []
    property bool rootLoaded: false

    function open() { folderManagerWindow.visible = true }

    function requestRootIfNeeded() {
        if (folderManagerWindow.rootLoaded) return
        folderManagerWindow.rootLoaded = true
        if (typeof folderTreeController !== "undefined")
            folderTreeController.requestChildren(folderManagerWindow.rootPath)
    }

    onVisibleChanged: if (folderManagerWindow.visible) folderManagerWindow.requestRootIfNeeded()
    onRootPathChanged: {
        folderManagerWindow.rootLoaded = false
        folderManagerWindow.rootChildren = []
        folderManagerWindow.selectedPath = ""
        if (folderManagerWindow.visible) folderManagerWindow.requestRootIfNeeded()
    }

    Connections {
        target: typeof folderTreeController !== "undefined"
                ? folderTreeController : null
        function onChildrenLoaded(path, children) {
            if (path === folderManagerWindow.rootPath) folderManagerWindow.rootChildren = children
        }
    }

    // a kijelölt mappa állapota: "always" (figyelt gyökér), "once"
    // (ebben a munkamenetben elindított egyszeri keresés), egyébként "none"
    function stateFor(path) {
        if (!path) return "none"
        if (folderManagerWindow.onceScanned[path] === true) return "once"
        // #305: null-őr — a `selectedState` kötés (fentebb) a QML-engine
        // leépítésekor is újraértékelődhet, amikor a `controller` már null
        if (controller && controller.watchedFolders.indexOf(path) !== -1) return "always"
        return "none"
    }

    // #543: az arcfelismerésből való kizártság — a fa-jelvényhez ÉS a
    // jobb oldali kapcsolóhoz is kell, ezért itt, a közös helyen él (a
    // `FolderStatePanel` innen hívja). Az ős-mappákra is kiterjedő
    // egyezés a Python `faceDetectionEnabledFor` tükre.
    function facesExcludedFor(path) {
        if (!path || typeof controller === "undefined" || !controller) return false
        var roots = controller.faceExcludedFolders
        for (var i = 0; i < roots.length; i++) {
            var root = roots[i]
            if (path === root) return true
            if (path.indexOf(root + "/") === 0) return true
            if (path.indexOf(root + "\\") === 0) return true
        }
        return false
    }

    // #543: teljes meghajtó-e az útvonal? Az eredeti Picasa ilyenkor
    // figyelmeztet („Watching an entire drive can slow down the system"),
    // mielőtt figyelésre állítaná.
    function isWholeDrive(path) {
        if (!path) return false
        if (path === "/") return true
        if (/^[A-Za-z]:[\\/]?$/.test(path)) return true
        return false
    }

    // a jobb oldali rádiógomb-szerű sorok hívják (FolderStatePanel.qml).
    // #543: két megerősítés ékelődik közé, a `stringres` eredeti szövegeivel
    // — teljes meghajtó figyelése, illetve figyelt mappa eltávolítása.
    function setState(path, state) {
        if (!path) return
        if (state === "always" && folderManagerWindow.isWholeDrive(path)) {
            driveWarning.pendingPath = path
            driveWarning.ask(
                "watchWholeDrive",
                qsTr("Watching an entire drive can slow down the system. "
                     + "It would be better to select several sub-folders."))
            return
        }
        if (state === "none"
                && controller && controller.watchedFolders.indexOf(path) !== -1) {
            removeWatchedConfirm.pendingPath = path
            removeWatchedConfirm.ask(
                "removeWatchedFolder",
                qsTr("If you remove this folder, new items that you add to "
                     + "that folder on disk will not be automatically added "
                     + "to your library."))
            return
        }
        folderManagerWindow.applyState(path, state)
    }

    // a tényleges állapotváltás — a megerősítő párbeszédek is ezt hívják
    function applyState(path, state) {
        if (!path) return
        var next = {}
        for (var key in folderManagerWindow.onceScanned)
            if (key !== path) next[key] = true
        if (state === "once") next[path] = true
        folderManagerWindow.onceScanned = next

        if (state === "always") controller.addWatchedFolder(path)
        else if (state === "once") controller.scanFolderOnce(path)
        else controller.removeFolder(path)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Text {
            Layout.fillWidth: true
            text: qsTr(
                "Choose which folders PicasaPy watches. New and changed "
                + "pictures in watched folders appear automatically.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            // bal oldal: a helyi fájlrendszer mappafája, lusta betöltéssel
            // #543: az eredeti `foldermgr.tre` PONTOSAN fele-fele oszt
            // (`XConstraint 1, .5, 0`) — nem fix 320/260 px
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Theme.contentPanel
                border.color: Theme.chromeBorder

                Flickable {
                    id: treeFlick
                    objectName: "folderManagerTree"
                    anchors.fill: parent
                    anchors.margins: 1
                    clip: true
                    contentWidth: width
                    contentHeight: treeColumn.height
                    ScrollBar.vertical: PicasaScrollBar {}

                    Column {
                        id: treeColumn
                        width: treeFlick.width

                        Repeater {
                            model: folderManagerWindow.rootChildren
                            delegate: FolderTreeItem {
                                required property var modelData
                                width: treeColumn.width
                                path: modelData.path
                                name: modelData.name
                                hasChildren: modelData.hasChildren
                                depth: 0
                                manager: folderManagerWindow
                            }
                        }
                    }
                }
            }

            // jobb oldal: állapot-választó + figyelt mappák összegzése
            FolderStatePanel {
                Layout.preferredWidth: 1
                Layout.fillWidth: true
                Layout.fillHeight: true
                manager: folderManagerWindow
                selectedPath: folderManagerWindow.selectedPath
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            PicasaButton {
                text: qsTr("Add folder...")
                onClicked: pickFolder.open()
            }
            // #146: a régi Picasa figyelt mappáinak felajánlása — a
            // PicasaImportDialog a Main.qml-ben él, a discoveryController
            // globális jelzésén (dialogRequested) keresztül nyílik meg
            PicasaButton {
                objectName: "adoptPicasaFoldersButton"
                text: qsTr("Adopt Picasa folders...")
                onClicked: discoveryController.openImportDialog()
            }
            Item { Layout.fillWidth: true }
            // az állapot-váltások AZONNAL érvénybe lépnek (setState a
            // rádiógomb-sor kattintásakor rögtön hívja a controllert) —
            // itt nincs mit "elfogadni" vagy "visszavonni", az OK/Mégse
            // párost csak a Picasa-mintájú ablakszerkezet kedvéért tartjuk,
            // mindkettő egyszerűen bezárja az ablakot
            PicasaButton {
                objectName: "folderManagerOkButton"
                text: qsTr("OK")
                onClicked: folderManagerWindow.visible = false
            }
            PicasaButton {
                objectName: "folderManagerCancelButton"
                text: qsTr("Cancel")
                onClicked: folderManagerWindow.visible = false
            }
            // #543: az eredeti `foldermgr.tre` jobb alsó sarkában OK /
            // Cancel MELLETT Help gomb is van
            PicasaButton {
                objectName: "folderManagerHelpButton"
                text: qsTr("Help")
                onClicked: folderManagerHelp.visible = true
            }
        }
    }

    // #543: „Watching an entire drive can slow down the system…"
    ConfirmDialog {
        id: driveWarning
        namePrefix: "folderManagerDriveWarning"
        property string pendingPath: ""
        onConfirmed: folderManagerWindow.applyState(driveWarning.pendingPath, "always")
    }

    // #543: IDS_HOTFOLDER_CONFIRM — figyelt mappa eltávolítása
    ConfirmDialog {
        id: removeWatchedConfirm
        namePrefix: "folderManagerRemoveWatchedConfirm"
        property string pendingPath: ""
        onConfirmed: folderManagerWindow.applyState(
                         removeWatchedConfirm.pendingPath, "none")
    }

    // #543: a Súgó gomb tartalma — az eredeti súgó weboldala nincs meg,
    // ezért a dialógus SAJÁT, rövid magyarázatát mutatjuk (az eredeti
    // `instructions_text` bővebb változata), nem hivatkozunk kifelé.
    Window {
        id: folderManagerHelp
        objectName: "folderManagerHelpWindow"
        title: qsTr("Folder Manager — Help")
        modality: Qt.ApplicationModal
        width: 420
        height: 240
        color: Theme.canvasBg
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 10
            Text {
                Layout.fillWidth: true
                Layout.fillHeight: true
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                text: qsTr(
                    "Scan Always keeps watching the folder: pictures you add "
                    + "to it later show up on their own.\n\n"
                    + "Scan Once takes the pictures that are in the folder now "
                    + "and then forgets about it.\n\n"
                    + "Remove from Picasa takes the folder out of your library. "
                    + "The pictures stay on your disk.\n\n"
                    + "Face detection is separate: you can watch a folder and "
                    + "still keep faces in it out of the library.")
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                PicasaButton {
                    objectName: "folderManagerHelpCloseButton"
                    text: qsTr("Close")
                    onClicked: folderManagerHelp.visible = false
                }
            }
        }
    }

    FolderDialog {
        id: pickFolder
        title: qsTr("Add folder...")
        onAccepted: controller.addWatchedFolder(selectedFolder.toString())
    }
}
