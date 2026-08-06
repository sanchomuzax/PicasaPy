import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Beállítások" (options.fen) — a Picasa legnagyobb preferencia-
// dialógusa, a docs/specs/picasa-fen-dialogs.md 3.11. szakaszában
// dokumentált 8 fül szerint (a forrás-doksi fejléce "9 fül"-et említ, de
// a widget-fa csak 8 fület ír le részletesen — ld. az issue jelentését).
//
// A dialógus a MoveDatabaseDialog.qml (#368) mintáját követi: önálló,
// mozgatható/átméretezhető Window, a Main.qml-be illesztés (Eszközök →
// Beállítások... menüpont bekötése) az integrátoré.
//
// MA csak az "General" fülön van élő vezérlő (nyelv, törlés-megerősítés
// elnyomása) — a többi fül a FEN-struktúra kedvéért épül fel, de tiltott,
// mert a mögöttes funkció nincs meg a PicasaPy-ban (ld. az egyes
// OptionsTab*.qml fájlok fejléc-kommentjeit).
Window {
    id: optionsWindow
    objectName: "optionsDialog"
    title: qsTr("Options")
    modality: Qt.ApplicationModal
    width: 560
    height: 460
    minimumWidth: 480
    minimumHeight: 360
    color: Theme.canvasBg

    function open() {
        optionsWindow.visible = true
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        TabBar {
            id: tabBar
            objectName: "optionsTabBar"
            Layout.fillWidth: true

            TabButton { objectName: "optionsTabGeneral"; text: qsTr("General") }
            TabButton { objectName: "optionsTabEmail"; text: qsTr("E-Mail") }
            TabButton { objectName: "optionsTabFileTypes"; text: qsTr("File Types") }
            TabButton { objectName: "optionsTabSlideshow"; text: qsTr("Slideshow") }
            TabButton { objectName: "optionsTabPrinting"; text: qsTr("Printing") }
            TabButton { objectName: "optionsTabNetwork"; text: qsTr("Network") }
            TabButton { objectName: "optionsTabWebAlbums"; text: qsTr("Web Albums") }
            TabButton { objectName: "optionsTabNameTags"; text: qsTr("Name Tags") }
        }

        StackLayout {
            id: tabStack
            objectName: "optionsTabStack"
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex
            clip: true

            OptionsTabGeneral { Layout.fillWidth: true }
            OptionsTabEmail { Layout.fillWidth: true }
            OptionsTabFileTypes { Layout.fillWidth: true }
            OptionsTabSlideshow { Layout.fillWidth: true }
            OptionsTabPrinting { Layout.fillWidth: true }
            OptionsTabNetwork { Layout.fillWidth: true }
            OptionsTabWebAlbums { Layout.fillWidth: true }
            OptionsTabNameTags { Layout.fillWidth: true }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Item { Layout.fillWidth: true }
            // a mostani élő beállítások (nyelv, törlés-megerősítés) azonnal
            // hatnak, ahogy a menüből is — nincs külön OK/Alkalmaz szükséges
            PicasaButton {
                objectName: "optionsCloseButton"
                text: qsTr("Close")
                accent: Theme.picasaGreen
                onClicked: optionsWindow.visible = false
            }
        }
    }
}
