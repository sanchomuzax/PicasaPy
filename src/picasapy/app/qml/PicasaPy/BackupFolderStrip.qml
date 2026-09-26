import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #3504/#3594: a mentés 2. lépésének MAPPALISTÁJA — a még el nem mentett
// mappák, pipával.
//
// ⚠️ ELTÉRÉS az eredetitől, kimondva: az eredetiben ezt a KÖNYVTÁR maga
// mutatja (a rács csak a még el nem mentett fájlokat, a mappák pipával —
// `backuptext2`: „A Picasa most azokat a fájlokat jeleníti meg…",
// `biztonsagi-mentes.md` 9.–10.). A mért 212 képpontos kiadás-panelen
// lista NINCS (a 2. lépés keretében csak a két szöveg és a
// `selectall`/`selectnone` gombpár ül). A mi könyvtárunknak nincs ilyen
// szűrő-módja, ezért a lista ebben a sávban látszik, KÖZVETLENÜL a panel
// fölött — a könyvtár ennyivel rövidebb, a mért vászon érintetlen.
//
// A sáv csak jelez (`pipaldKert`); a pipák állapotát a gazda tartja.
Rectangle {
    id: sav

    //: a még el nem mentett fájlok, mappánként (`BackupController`)
    property var mentetlenek: []
    //: a bepipált mappák útjai
    property var pipaltMappak: []
    //: a lista háttérszálon készül — amíg nem jön meg
    property bool toltodnek: false
    //: van-e kiválasztott készlet — nélküle a „minden el van mentve"
    //: felirat hamis volna
    property bool vanKeszlet: false

    //: egy mappa pipája vált
    signal pipaldKert(string mappa, bool be)

    //: egy sor magassága és az egyszerre látható sorok száma — a lista
    //: többi része görgethető
    readonly property int sorMagassag: 24
    readonly property int lathatoSorok: 4

    implicitHeight: lathatoSorok * sorMagassag + 2
    color: Theme.controlBase
    border.width: 1
    border.color: Theme.chromeBorder

    ListView {
        id: mappaLista
        objectName: "publishBackupFolderList"
        anchors.fill: parent
        anchors.margins: 1
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        model: sav.mentetlenek
        ScrollBar.vertical: ScrollBar {}
        delegate: RowLayout {
            id: mappaSor
            required property var modelData
            width: mappaLista.width
            height: sav.sorMagassag
            spacing: 6
            CheckBox {
                objectName: "publishBackupFolderCheck"
                Layout.preferredHeight: sav.sorMagassag
                Layout.leftMargin: 4
                topPadding: 0
                bottomPadding: 0
                text: mappaSor.modelData.nev
                font.pixelSize: Theme.fontSize
                //: a stílus alap feliratszíne a `controlBase` háttéren
                //: alig látszott (az átnézés képén a mappanév szürke
                //: árnyék volt) — a felirat a téma tintáját kapja
                contentItem: Text {
                    leftPadding: parent.indicator.width + parent.spacing
                    text: parent.text
                    font: parent.font
                    color: Theme.ink
                    verticalAlignment: Text.AlignVCenter
                }
                checked: sav.pipaltMappak.indexOf(mappaSor.modelData.mappa) >= 0
                onToggled: {
                    sav.pipaldKert(mappaSor.modelData.mappa, checked)
                    //: a kattintás elvágja a kötést — a `pipaltMappak` a
                    //: gazdából jön vissza
                    checked = Qt.binding(function () {
                        return sav.pipaltMappak
                            .indexOf(mappaSor.modelData.mappa) >= 0
                    })
                }
            }
            Text {
                objectName: "publishBackupFolderFiles"
                Layout.fillWidth: true
                Layout.rightMargin: 12
                elide: Text.ElideRight
                color: Theme.ink
                font.pixelSize: Theme.fontSize - 1
                text: "(" + mappaSor.modelData.darab + ")  "
                      + mappaSor.modelData.fajlok.join(", ")
                      + (mappaSor.modelData.darab
                         > mappaSor.modelData.fajlok.length ? ", …" : "")
            }
        }
    }

    //: #3594: amíg a háttérszál számol —
    //: `il_BurnPanel::calculating` (biztonsagi-mentes.md 15.7)
    Text {
        objectName: "publishBackupFolderLoading"
        anchors.centerIn: parent
        visible: sav.toltodnek
        text: qsTr("Calculating…")
        font.pixelSize: Theme.fontSize
        color: Theme.textGray
    }
    Text {
        objectName: "publishBackupFolderEmpty"
        anchors.centerIn: parent
        visible: sav.vanKeszlet && !sav.toltodnek
                 && sav.mentetlenek.length === 0
        text: qsTr("Everything was already backed up.")
        font.pixelSize: Theme.fontSize
        color: Theme.textGray
    }
}
