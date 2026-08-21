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
    width: 550
    height: 450
    minimumWidth: 0
    minimumHeight: 0
    color: Theme.canvasBg

    // a fa gyökere — alapból a teljes fájlrendszer (Linux-first: "/"),
    // tesztek felülírhatják (setProperty) egy ideiglenes könyvtárra
    // Üresen a Picasa-sorrendű többgyökeres nézetet kérjük; a tesztek és
    // célzott tallózók továbbra is adhatnak egyetlen rootPath-ot.
    property string rootPath: ""
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
    // A Picasa a módosításokat csak az OK megnyomásakor írja ki. A két
    // lista a megnyitáskori és a párbeszédben látható (már szerkesztett)
    // állapot; a mapek a fa öröklődő felülbírálásait és az arc-kapcsolót
    // tartják a munkamenet végéig.
    property var initialWatched: []
    property var visibleWatched: []
    property var pendingStates: ({})
    property var pendingFaces: ({})
    property bool acceptingChanges: false

    property var rootChildren: []
    property bool rootLoaded: false

    Component.onCompleted: beginSession()

    function open() {
        beginSession()
        folderManagerWindow.visible = true
    }

    function beginSession() {
        initialWatched = controller ? controller.watchedFolders.slice() : []
        visibleWatched = initialWatched.slice()
        pendingStates = ({})
        pendingFaces = ({})
        onceScanned = ({})
        acceptingChanges = false
    }

    function cancelChanges() {
        beginSession()
        folderManagerWindow.visible = false
    }

    function _isAtOrBelow(path, root) {
        return path === root || path.indexOf(root + "/") === 0
               || path.indexOf(root + "\\") === 0
    }

    function _containsPath(paths, path) {
        for (var i = 0; i < paths.length; ++i)
            if (paths[i] === path) return true
        return false
    }

    function _coveredByVisibleRoot(path) {
        for (var i = 0; i < visibleWatched.length; ++i)
            if (_isAtOrBelow(path, visibleWatched[i])) return true
        return false
    }

    function _finishAccept() {
        for (var i = 0; i < initialWatched.length; ++i)
            if (!_containsPath(visibleWatched, initialWatched[i]))
                controller.removeFolder(initialWatched[i])
        for (var j = 0; j < visibleWatched.length; ++j)
            if (!_containsPath(initialWatched, visibleWatched[j]))
                controller.addWatchedFolder(visibleWatched[j])
        for (var path in pendingStates)
            controller.setFolderManagerState(path, pendingStates[path])
        for (var path in pendingStates)
            if (pendingStates[path] === "once") controller.scanFolderOnce(path)
            else if (pendingStates[path] === "none"
                     && !_containsPath(initialWatched, path)) controller.removeFolder(path)
        for (var facePath in pendingFaces)
            controller.setFaceDetectionEnabled(facePath, pendingFaces[facePath])
        acceptingChanges = false
        folderManagerWindow.visible = false
    }

    function acceptChanges() {
        // A Picasa a destruktív arctörlési kérdést az OK-fázisban teszi fel.
        for (var path in pendingFaces) {
            if (pendingFaces[path] === false) {
                acceptingChanges = true
                faceExclusionConfirm.ask(
                    "removeFacesFromExcludedFolder",
                    qsTranslate(
                        "FolderStatePanel",
                        "Are you sure you want to remove all faces "
                        + "and name tags from excluded folders?"))
                return
            }
        }
        _finishAccept()
    }

    function requestRootIfNeeded() {
        if (folderManagerWindow.rootLoaded) return
        folderManagerWindow.rootLoaded = true
        if (typeof folderTreeController !== "undefined") {
            if (folderManagerWindow.rootPath.length > 0)
                folderTreeController.requestChildren(folderManagerWindow.rootPath)
            else
                folderTreeController.requestRoots()
        }
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
        function onRootsLoaded(roots) {
            if (folderManagerWindow.rootPath.length === 0)
                folderManagerWindow.rootChildren = roots
        }
    }

    // a kijelölt mappa állapota: "always" (figyelt gyökér), "once"
    // (ebben a munkamenetben elindított egyszeri keresés), egyébként "none"
    function stateFor(path) {
        if (!path) return "once"
        var chosen = ""
        var chosenLength = -1
        for (var changedPath in folderManagerWindow.pendingStates) {
            if (_isAtOrBelow(path, changedPath) && changedPath.length > chosenLength) {
                chosen = folderManagerWindow.pendingStates[changedPath]
                chosenLength = changedPath.length
            }
        }
        if (chosen !== "") return chosen
        if (controller && controller.folderManagerStateFor) {
            var storedState = controller.folderManagerStateFor(path)
            if (storedState === "none" || storedState === "once") return storedState
        }
        if (folderManagerWindow.onceScanned[path] === true) return "once"
        // #305: null-őr — a `selectedState` kötés (fentebb) a QML-engine
        // leépítésekor is újraértékelődhet, amikor a `controller` már null
        for (var i = 0; i < folderManagerWindow.visibleWatched.length; ++i)
            if (_isAtOrBelow(path, folderManagerWindow.visibleWatched[i])) return "always"
        return "none"
    }

    // #543: az arcfelismerésből való kizártság — a fa-jelvényhez ÉS a
    // jobb oldali kapcsolóhoz is kell, ezért itt, a közös helyen él (a
    // `FolderStatePanel` innen hívja). Az ős-mappákra is kiterjedő
    // egyezés a Python `faceDetectionEnabledFor` tükre.
    function facesExcludedFor(path) {
        if (!path || typeof controller === "undefined" || !controller) return false
        var pending = ""
        var pendingLength = -1
        for (var changedPath in folderManagerWindow.pendingFaces) {
            if (_isAtOrBelow(path, changedPath) && changedPath.length > pendingLength) {
                pending = folderManagerWindow.pendingFaces[changedPath]
                pendingLength = changedPath.length
            }
        }
        if (pending !== "") return pending === false
        var roots = controller.faceExcludedFolders
        for (var i = 0; i < roots.length; i++) {
            var root = roots[i]
            if (path === root) return true
            if (path.indexOf(root + "/") === 0) return true
            if (path.indexOf(root + "\\") === 0) return true
        }
        return false
    }

    function parentFacesExcludedFor(path) {
        if (!path) return false
        var normalized = path.replace(/[\\/]+$/, "")
        var slash = Math.max(normalized.lastIndexOf("/"), normalized.lastIndexOf("\\"))
        if (slash <= 0) return false
        return facesExcludedFor(normalized.substring(0, slash))
    }

    function setFaceDetectionEnabled(path, enabled) {
        if (!path || parentFacesExcludedFor(path)) return
        var next = {}
        for (var key in pendingFaces) next[key] = pendingFaces[key]
        next[path] = enabled
        pendingFaces = next
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
        folderManagerWindow.stageState(path, state)
    }

    // a tényleges állapotváltás — a megerősítő párbeszédek is ezt hívják
    function stageState(path, state) {
        if (!path) return
        var changes = {}
        for (var changedPath in folderManagerWindow.pendingStates)
            changes[changedPath] = folderManagerWindow.pendingStates[changedPath]
        changes[path] = state
        folderManagerWindow.pendingStates = changes

        var next = {}
        for (var key in folderManagerWindow.onceScanned)
            if (key !== path) next[key] = true
        if (state === "once") next[path] = true
        folderManagerWindow.onceScanned = next

        var watched = folderManagerWindow.visibleWatched.slice()
        var index = watched.indexOf(path)
        if (state === "always" && index === -1
                && !folderManagerWindow._coveredByVisibleRoot(path))
            watched.push(path)
        else if (state !== "always" && index !== -1) watched.splice(index, 1)
        folderManagerWindow.visibleWatched = watched
    }

    Shortcut {
        sequence: StandardKey.Cancel
        context: Qt.WindowShortcut
        enabled: folderManagerWindow.visible
        onActivated: folderManagerWindow.cancelChanges()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 4
        spacing: 4

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            // bal oldal: a helyi fájlrendszer mappafája, lusta betöltéssel
            // #543: az eredeti `foldermgr.tre` PONTOSAN fele-fele oszt
            // (`XConstraint 1, .5, 0`) — nem fix 320/260 px
            ColumnLayout {
                Layout.preferredWidth: 1
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 3

                Text {
                    text: qsTranslate("FolderPane", "Folders")
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.ink
                }

                Rectangle {
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
            }

            // jobb oldal: állapot-választó + figyelt mappák összegzése
            ColumnLayout {
                Layout.preferredWidth: 1
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 4

                Text {
                    Layout.preferredWidth: 232
                    Layout.preferredHeight: 73
                    text: qsTr(
                        "Choose which folders PicasaPy watches. New and changed "
                        + "pictures in watched folders appear automatically.")
                    wrapMode: Text.WordWrap
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }

                FolderStatePanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    manager: folderManagerWindow
                    selectedPath: folderManagerWindow.selectedPath
                }
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
                implicitWidth: 98
                implicitHeight: 28
                onClicked: folderManagerWindow.acceptChanges()
            }
            PicasaButton {
                objectName: "folderManagerCancelButton"
                text: qsTr("Cancel")
                implicitWidth: 98
                implicitHeight: 28
                onClicked: folderManagerWindow.cancelChanges()
            }
            // #543: az eredeti `foldermgr.tre` jobb alsó sarkában OK /
            // Cancel MELLETT Help gomb is van
            PicasaButton {
                objectName: "folderManagerHelpButton"
                text: qsTr("Help")
                implicitWidth: 98
                implicitHeight: 28
                onClicked: folderManagerHelp.visible = true
            }
        }
    }

    // #543: „Watching an entire drive can slow down the system…"
    ConfirmDialog {
        id: driveWarning
        namePrefix: "folderManagerDriveWarning"
        property string pendingPath: ""
        onConfirmed: folderManagerWindow.stageState(driveWarning.pendingPath, "always")
        onDenied: folderManagerWindow.stageState(driveWarning.pendingPath, "none")
    }

    // #543: IDS_HOTFOLDER_CONFIRM — figyelt mappa eltávolítása
    ConfirmDialog {
        id: removeWatchedConfirm
        namePrefix: "folderManagerRemoveWatchedConfirm"
        property string pendingPath: ""
        onConfirmed: folderManagerWindow.stageState(
                         removeWatchedConfirm.pendingPath, "none")
    }

    ConfirmDialog {
        id: faceExclusionConfirm
        namePrefix: "faceDetectionConfirm"
        onConfirmed: if (folderManagerWindow.acceptingChanges)
                         folderManagerWindow._finishAccept()
        onDenied: folderManagerWindow.acceptingChanges = false
        onCanceled: folderManagerWindow.acceptingChanges = false
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
        onAccepted: folderManagerWindow.stageState(selectedFolder.toString(), "always")
    }
}
