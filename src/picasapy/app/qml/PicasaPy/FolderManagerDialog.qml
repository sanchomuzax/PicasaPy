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
        if (controller.watchedFolders.indexOf(path) !== -1) return "always"
        return "none"
    }

    // a fa-sorok állapot-ikonjához (FolderTreeItem.qml hívja)
    function stateGlyph(path) {
        var state = folderManagerWindow.stateFor(path)
        if (state === "always") return "●"   // teli kör — figyelt
        if (state === "once") return "◐"     // fél kör — egyszeri
        return ""
    }

    // a jobb oldali rádiógomb-szerű sorok hívják (FolderStatePanel.qml)
    function setState(path, state) {
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
            Rectangle {
                Layout.preferredWidth: 320
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#ffffff"
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
                Layout.preferredWidth: 260
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
        }
    }

    FolderDialog {
        id: pickFolder
        title: qsTr("Add folder...")
        onAccepted: controller.addWatchedFolder(selectedFolder.toString())
    }
}
