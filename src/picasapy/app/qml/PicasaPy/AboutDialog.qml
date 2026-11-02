import QtQuick
import QtQuick.Controls

// Névjegy-dialógus (#150-ben kiemelve a Main.qml-ből): logó + verzió
// (appVersion → version.version_string()) + licenc-sor.
Dialog {
    id: root
    title: qsTr("About PicasaPy")
    modal: true
    anchors.centerIn: parent
    standardButtons: Dialog.Ok
    // #6402: a külső hivatkozások a `appLinks` kontextusból (ld. external_links.py)
    readonly property var links: typeof appLinks !== "undefined" ? appLinks : ({})
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
            text: "PicasaPy " + appVersion + " - "
                  + qsTr("A modern, open Picasa successor.")
                  + "\n" + qsTr("Location: %1").arg(appLocation)
                  + "\nGPL-3.0 · github.com/sanchomuzax/PicasaPy"
            font.pixelSize: Theme.fontSize
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            width: 480
        }
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 18
            ExternalLinkText {
                objectName: "aboutWebsiteLink"
                text: qsTr("Website")
                url: root.links.website || ""
            }
            ExternalLinkText {
                objectName: "aboutPrivacyLink"
                text: qsTr("Privacy Policy")
                url: root.links.privacy || ""
            }
            ExternalLinkText {
                objectName: "aboutTermsLink"
                text: qsTr("Terms of Service")
                url: root.links.terms || ""
            }
        }
    }
}
