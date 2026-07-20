import QtQuick
import QtQuick.Controls

// Névjegy-dialógus (#150-ben kiemelve a Main.qml-ből): logó + verzió
// (appVersion → version.version_string()) + licenc-sor.
Dialog {
    title: qsTr("About PicasaPy")
    modal: true
    anchors.centerIn: parent
    standardButtons: Dialog.Ok
    Column {
        spacing: 10
        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            // a qml/PicasaPy/ mappából az app/assets a két szinttel feljebb van
            source: Qt.resolvedUrl("../../assets/logo.svg")
            sourceSize.width: 320
            fillMode: Image.PreserveAspectFit
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "PicasaPy " + appVersion + " — "
                  + qsTr("A modern, open Picasa successor.")
                  + "\nGPL-3.0 · github.com/sanchomuzax/PicasaPy"
            font.pixelSize: Theme.fontSize
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
