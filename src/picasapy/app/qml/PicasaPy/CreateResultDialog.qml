import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

Dialog {
    id: createResultDialog
    objectName: "createResultDialog"
    title: qsTr("Create")
    modal: true
    anchors.centerIn: parent
    standardButtons: Dialog.Ok
    property string message: ""
    // #918: a csupasz, tördelő `Text` `width: 360`-cal kötési hurkot
    // okozott (a `Dialog` az `implicitWidth`-jét a contentItem
    // `implicitWidth`-jéből számolja, a tördelő `Text` `implicitWidth`-
    // je viszont a saját szélességétől függ). A fájl többi dialógusa
    // (`collageDialog`, `movieDialog`) ugyanígy egy szimpla
    // `ColumnLayout`-gyerekbe csomagolja a tartalmát (a `Dialog` ezt
    // teszi meg `contentItem`-nek egyetlen gyerekként) — ehhez a
    // mintához igazodunk, NEM `contentItem:`-ként explicit kötve; a
    // szélesség a `Layout`-on rögzítve, nem a `Text`-en.
    ColumnLayout {
        Text {
            objectName: "createResultText"
            text: createResultDialog.message
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            wrapMode: Text.WordWrap
            Layout.preferredWidth: 360
            Layout.fillWidth: true
        }
    }
}
