import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Képek biztonsági mentése (#440, `ID_TOOLS_BACKUP`, `newbackupset.fen`):
// nevesített, újrafuttatható, INKREMENTÁLIS mentés-készletek.
//
// Az eredeti saját meghatározása: a készlet megjegyzi, hova mentett ÉS mit
// mentett már el, tehát újraindításkor csak az új fájlokat viszi át. A
// CD/DVD-ág szándékosan kimarad (a jegy döntése) — a cél külső meghajtó
// vagy hálózati megosztás.
//
// A New / Edit / Delete Set hármas az eredetié; a törlés megerősítést kér.
Window {
    id: backupWindow
    objectName: "backupDialog"
    title: qsTr("Back Up Pictures")
    modality: Qt.ApplicationModal
    width: 620
    height: 460
    minimumWidth: 520
    minimumHeight: 380
    color: Theme.canvasBg

    property var keszletek: []
    property int kivalasztott: -1          // a lista sorindexe
    property bool szerkesztes: false       // új/módosítás űrlap látszik-e
    property int szerkesztettId: -1        // -1 = új készlet
    property string urlapNev: ""
    property string urlapCel: ""
    property string urlapSzuro: "minden"
    property string uzenet: ""

    readonly property var szuroKulcsok: ["minden", "kepek", "fenykepezogep"]
    readonly property var szuroFeliratok: [
        qsTr("All file types"),
        qsTr("All pictures (no movies)"),
        qsTr("Only JPEGs with camera data"),
    ]

    function frissitsd() {
        if (typeof backupController === "undefined" || !backupController)
            return
        backupWindow.keszletek = backupController.keszletek()
        if (backupWindow.kivalasztott >= backupWindow.keszletek.length)
            backupWindow.kivalasztott = backupWindow.keszletek.length - 1
    }

    function open() {
        backupWindow.uzenet = ""
        backupWindow.szerkesztes = false
        backupWindow.frissitsd()
        backupWindow.visible = true
    }

    function ujKeszletUrlap() {
        backupWindow.szerkesztettId = -1
        backupWindow.urlapNev = ""
        backupWindow.urlapCel = ""
        backupWindow.urlapSzuro = "minden"
        backupWindow.szerkesztes = true
    }

    function szerkesztoUrlap() {
        if (backupWindow.kivalasztott < 0) return
        var k = backupWindow.keszletek[backupWindow.kivalasztott]
        backupWindow.szerkesztettId = k.id
        backupWindow.urlapNev = k.nev
        backupWindow.urlapCel = k.cel
        backupWindow.urlapSzuro = k.szuro
        backupWindow.szerkesztes = true
    }

    function mentsdAzUrlapot() {
        if (typeof backupController === "undefined" || !backupController)
            return
        var rendben = backupWindow.szerkesztettId < 0
            ? backupController.ujKeszlet(backupWindow.urlapNev,
                                         backupWindow.urlapCel,
                                         backupWindow.urlapSzuro)
            : backupController.modositsdAKeszletet(backupWindow.szerkesztettId,
                                                   backupWindow.urlapNev,
                                                   backupWindow.urlapCel,
                                                   backupWindow.urlapSzuro)
        if (rendben) {
            backupWindow.szerkesztes = false
            backupWindow.frissitsd()
        }
    }

    Connections {
        target: (typeof backupController !== "undefined") ? backupController : null
        function onHibatJelez(szoveg) { backupWindow.uzenet = szoveg }
        function onKeszletekValtoztak() { backupWindow.frissitsd() }
        function onFutasKesz(darab, bajt) {
            backupWindow.uzenet = darab === 0
                ? qsTr("Everything was already backed up.")
                : qsTr("Backup complete: %1 file(s).").arg(darab)
        }
    }

    FolderDialog {
        id: celValaszto
        title: qsTr("Choose the backup location")
        onAccepted: {
            backupWindow.urlapCel = (typeof fileOpsController !== "undefined"
                                     && fileOpsController)
                ? fileOpsController.toLocalPath(celValaszto.selectedFolder.toString())
                : celValaszto.selectedFolder.toString().replace(/^file:\/\//, "")
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            //: A készlet fogalma az eredeti saját meghatározása szerint.
            text: qsTr("A backup set remembers where it saves and what it has "
                       + "already saved, so the next run only copies what is new.")
        }

        // -- a készletek listája ------------------------------------------
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Theme.controlBase
            border.color: Theme.chromeBorder
            border.width: 1
            radius: 2
            visible: !backupWindow.szerkesztes

            ListView {
                id: keszletLista
                objectName: "backupSetList"
                anchors.fill: parent
                anchors.margins: 1
                clip: true
                model: backupWindow.keszletek
                delegate: Rectangle {
                    required property int index
                    required property var modelData
                    width: keszletLista.width
                    height: 40
                    color: index === backupWindow.kivalasztott
                           ? Theme.panelSelection : "transparent"
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 8
                        Text {
                            text: modelData.nev
                            font.pixelSize: Theme.fontSize
                            color: index === backupWindow.kivalasztott
                                   ? Theme.panelSelectionText : Theme.ink
                        }
                        Text {
                            text: modelData.utolsoFutas.length > 0
                                  ? qsTr("%1 — last run: %2").arg(modelData.cel)
                                        .arg(modelData.utolsoFutas)
                                  : qsTr("%1 — not run yet").arg(modelData.cel)
                            font.pixelSize: Theme.fontSize - 2
                            color: Theme.textGray
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: backupWindow.kivalasztott = index
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: backupWindow.keszletek.length === 0
                text: qsTr("No backup sets yet.")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
        }

        // -- új / módosítás űrlap ------------------------------------------
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            visible: backupWindow.szerkesztes
            columnSpacing: 8
            rowSpacing: 8

            Text {
                text: qsTr("Name:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                objectName: "backupSetName"
                Layout.fillWidth: true
                text: backupWindow.urlapNev
                font.pixelSize: Theme.fontSize
                onTextEdited: backupWindow.urlapNev = text
                // #422: jobbklikk-menü minden szövegmezőn (a `Address`
                // megfelelője az eredetiben)
                TextFieldContextArea {}
            }

            Text {
                text: qsTr("Save to:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                TextField {
                    objectName: "backupSetTarget"
                    Layout.fillWidth: true
                    text: backupWindow.urlapCel
                    font.pixelSize: Theme.fontSize
                    onTextEdited: backupWindow.urlapCel = text
                    // #422: jobbklikk-menü minden szövegmezőn
                    TextFieldContextArea {}
                }
                PicasaButton {
                    objectName: "backupChooseTarget"
                    text: qsTr("Browse...")
                    onClicked: celValaszto.open()
                }
            }

            Text {
                text: qsTr("Files:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ComboBox {
                objectName: "backupSetFilter"
                Layout.fillWidth: true
                model: backupWindow.szuroFeliratok
                currentIndex: backupWindow.szuroKulcsok.indexOf(backupWindow.urlapSzuro)
                onActivated: backupWindow.urlapSzuro =
                             backupWindow.szuroKulcsok[currentIndex]
            }
        }

        Text {
            objectName: "backupMessage"
            Layout.fillWidth: true
            visible: backupWindow.uzenet.length > 0
            text: backupWindow.uzenet
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            PicasaButton {
                objectName: "backupNewSet"
                visible: !backupWindow.szerkesztes
                text: qsTr("New Set...")
                onClicked: backupWindow.ujKeszletUrlap()
            }
            PicasaButton {
                objectName: "backupEditSet"
                visible: !backupWindow.szerkesztes
                enabled: backupWindow.kivalasztott >= 0
                text: qsTr("Edit Set...")
                onClicked: backupWindow.szerkesztoUrlap()
            }
            PicasaButton {
                objectName: "backupDeleteSet"
                visible: !backupWindow.szerkesztes
                enabled: backupWindow.kivalasztott >= 0
                text: qsTr("Delete Set")
                //: Az eredeti megerősítést kér a törlés előtt.
                onClicked: torlesMegerosites.ask(
                    "", qsTr("Delete this backup set? The saved files stay "
                             + "where they are."))
            }
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "backupRun"
                visible: !backupWindow.szerkesztes
                enabled: backupWindow.kivalasztott >= 0
                text: qsTr("Back Up")
                onClicked: {
                    if (typeof backupController === "undefined" || !backupController)
                        return
                    var k = backupWindow.keszletek[backupWindow.kivalasztott]
                    var terv = backupController.terv(k.id)
                    backupWindow.uzenet = terv.darab === 0
                        ? qsTr("Everything was already backed up.")
                        : qsTr("Copying %1 file(s)...").arg(terv.darab)
                    backupController.futtasdMost(k.id)
                }
            }
            PicasaButton {
                objectName: "backupFormSave"
                visible: backupWindow.szerkesztes
                text: qsTr("OK")
                onClicked: backupWindow.mentsdAzUrlapot()
            }
            PicasaButton {
                objectName: "backupFormCancel"
                visible: backupWindow.szerkesztes
                text: qsTr("Cancel")
                onClicked: backupWindow.szerkesztes = false
            }
            PicasaButton {
                objectName: "backupClose"
                visible: !backupWindow.szerkesztes
                text: qsTr("Close")
                onClicked: backupWindow.visible = false
            }
        }
    }

    ConfirmDialog {
        id: torlesMegerosites
        namePrefix: "backupDelete"
        title: qsTr("Delete Set")
        onConfirmed: {
            if (typeof backupController === "undefined" || !backupController)
                return
            backupController.torisdAKeszletet(
                backupWindow.keszletek[backupWindow.kivalasztott].id)
            backupWindow.kivalasztott = -1
        }
    }
}
