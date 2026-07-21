import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Meglévő Picasa-telepítés átvétele (#146): a discoveryController
// (scanner/discovery.py, #199) háttérszálon felderíti a korábbi Picasa
// figyelt mappáit, ez a dialógus emberi nyelven kérdez rá az átvételükre.
// Első induláskor (ha még nincs figyelt mappa) automatikusan nyithatja az
// integrátor (Main.qml, forró fájl); a Mappakezelő „Adopt Picasa
// folders..." gombja bármikor újranyitja (dialogRequested).
Dialog {
    id: importDialog
    objectName: "picasaImportDialog"
    title: qsTr("Import from Picasa")
    modal: true
    width: 480
    height: 420
    anchors.centerIn: parent
    standardButtons: Dialog.NoButton

    // igaz, amíg a háttérszálas felderítés fut (a lista helyén állapot-szöveg)
    property bool searching: false
    // igaz, ha a discoverPicasa() már lefutott legalább egyszer
    property bool searched: false

    // első induláskor (integrátori bekötés, Main.qml) és a Mappakezelő
    // gombjából is ez indítja a felderítést és nyitja meg a dialógust
    function openAndDiscover() {
        folderModel.clear()
        searching = true
        searched = false
        open()
        discoveryController.discoverPicasa()
    }

    onClosed: searching = false

    Connections {
        target: discoveryController
        function onDiscoveryFinished(folders, installationsFound) {
            folderModel.clear()
            for (var i = 0; i < folders.length; ++i)
                folderModel.append({ path: folders[i], picked: true })
            importDialog.searching = false
            importDialog.searched = true
        }
        function onDialogRequested() {
            importDialog.openAndDiscover()
        }
    }

    ListModel { id: folderModel }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Text {
            id: statusLabel
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            text: {
                if (importDialog.searching)
                    return qsTr("Looking for a previous Picasa installation…")
                if (!importDialog.searched)
                    return ""
                if (folderModel.count > 0)
                    return qsTr(
                        "We found your previous Picasa installation. It "
                        + "watched these folders — take them over?")
                return qsTr(
                    "We couldn't find a previous Picasa installation "
                    + "automatically. You can browse for its folder by hand.")
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: folderModel.count > 0
            color: "#ffffff"
            border.color: Theme.chromeBorder
            ListView {
                id: folderList
                objectName: "picasaImportFolderList"
                anchors.fill: parent
                anchors.margins: 1
                clip: true
                model: folderModel
                delegate: RowLayout {
                    required property string path
                    required property bool picked
                    required property int index
                    width: folderList.width
                    height: 26
                    spacing: 6
                    CheckBox {
                        checked: picked
                        onToggled: folderModel.setProperty(index, "picked", checked)
                    }
                    Text {
                        Layout.fillWidth: true
                        text: path
                        elide: Text.ElideMiddle
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                    }
                }
                ScrollBar.vertical: PicasaScrollBar {}
            }
        }

        BusyIndicator {
            Layout.alignment: Qt.AlignHCenter
            running: importDialog.searching
            visible: importDialog.searching
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            PicasaButton {
                text: qsTr("Browse manually...")
                onClicked: manualFolderDialog.open()
            }
            Item { Layout.fillWidth: true }
            PicasaButton {
                text: qsTr("Not now")
                onClicked: importDialog.close()
            }
            PicasaButton {
                objectName: "picasaImportAdoptButton"
                text: qsTr("Adopt")
                accent: Theme.picasaGreen
                enabled: folderModel.count > 0
                onClicked: {
                    var picked = []
                    for (var i = 0; i < folderModel.count; ++i) {
                        var item = folderModel.get(i)
                        if (item.picked) picked.push(item.path)
                    }
                    if (picked.length > 0)
                        discoveryController.adoptWatchedFolders(picked)
                    importDialog.close()
                }
            }
        }
    }

    // kézi tallózás, ha az automatikus felismerés nem talált semmit (vagy a
    // felhasználó másik mappát szeretne felvenni) — a meglévő
    // FolderManagerDialog Add folder gombjának mintája
    FolderDialog {
        id: manualFolderDialog
        title: qsTr("Browse manually...")
        onAccepted: {
            controller.addWatchedFolder(selectedFolder.toString())
            importDialog.close()
        }
    }
}
