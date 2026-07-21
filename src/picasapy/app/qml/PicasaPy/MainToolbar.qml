import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Felső eszköztár (#150-ben kiemelve a Main.qml-ből):
// Importálás | szűrők középen | Picasa-hű kereső jobbra + verzió-címke.
// A keresés-változást jelekkel adja tovább — a debounce-olt javaslat-
// frissítés és a kijelölés-ürítés a Main.qml dolga marad.
Rectangle {
    id: toolbar
    height: 34
    color: Theme.chromeBg

    // a keresőmező tartalma (a Main a mappa-választásnál olvassa)
    readonly property alias searchText: searchField.text
    // gépelés a keresőben (már beírt szöveggel)
    signal searchEdited(string text)
    // a törlő × gomb: a mező már üres, a nézet álljon vissza
    signal searchCleared()

    function clearSearch() {
        searchField.clear()
    }

    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width; height: 1
        color: Theme.chromeBorder
    }
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8; anchors.rightMargin: 8
        spacing: 10
        PicasaButton {
            text: qsTr("Import")
            enabled: false
            Layout.preferredWidth: 100
            Layout.preferredHeight: 24
        }
        Item { Layout.fillWidth: true }
        Column {
            Layout.alignment: Qt.AlignVCenter
            spacing: 0
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: qsTr("Filters")
                font.pixelSize: 9
                color: Theme.textGray
            }
            Row {
                spacing: 3

                // szűrő-kapcsolók (kézikönyv 09): ★ ☺ ⚲ ▤ + csúszka;
                // a bekapcsolt szűrő tónusa jelölő kék
                Rectangle {
                    width: 22; height: 20; radius: 2
                    color: controller.filterActive ? "#ffffff" : "transparent"
                    border.width: controller.filterActive ? 1 : 0
                    border.color: Theme.selectionBlue
                    Text {
                        anchors.centerIn: parent
                        text: "★"
                        font.pixelSize: 13
                        color: controller.filterActive
                               ? Theme.selectionBlue
                               : (starFilter.hovered ? Theme.starYellow : "#8f8b83")
                    }
                    HoverHandler { id: starFilter }
                    TapHandler {
                        onTapped: controller.filterActive
                                  ? controller.clearFilter()
                                  : controller.showStarred()
                    }
                }
                Text {   // arc-szűrő (3. fázis)
                    width: 22; height: 20
                    text: "☺"; font.pixelSize: 13; color: "#8f8b83"
                    opacity: 0.45
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                Text {   // geo-szűrő
                    width: 22; height: 20
                    text: "⚲"; font.pixelSize: 13; color: "#8f8b83"
                    opacity: 0.45
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                Text {   // mozgókép / méret
                    width: 22; height: 20
                    text: "▤"; font.pixelSize: 12; color: "#8f8b83"
                    opacity: 0.45
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                Item { width: 6; height: 1 }
                PicasaSlider {
                    width: 90; height: 20
                    enabled: false
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
        Item { width: 20 }
        // Picasa-hű kereső: fehér mező nagyítóval, törlő ×-szel
        Rectangle {
            Layout.preferredWidth: 300
            Layout.preferredHeight: 24
            radius: 3
            color: "#ffffff"
            border.color: Theme.chromeBorder
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 6
                anchors.rightMargin: 6
                spacing: 5
                Item {   // rajzolt nagyító
                    width: 12; height: 12
                    Rectangle {
                        x: 0; y: 0; width: 9; height: 9; radius: 4.5
                        color: "transparent"
                        border.color: "#8f8b83"; border.width: 1.5
                    }
                    Rectangle {
                        x: 8; y: 8; width: 4; height: 1.5
                        rotation: 45; color: "#8f8b83"
                    }
                }
                TextInput {
                    id: searchField
                    objectName: "searchField"
                    Layout.fillWidth: true
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                    clip: true
                    verticalAlignment: TextInput.AlignVCenter
                    selectByMouse: true
                    onTextEdited: toolbar.searchEdited(text)
                    Text {
                        visible: searchField.text.length === 0
                                 && !searchField.activeFocus
                        anchors.verticalCenter: parent.verticalCenter
                        text: qsTr("Search")
                        color: "#8f8b83"
                        font.pixelSize: Theme.fontSize
                    }
                }
                Rectangle {   // törlő gomb, csak ha van mit törölni
                    objectName: "searchClear"
                    visible: searchField.text.length > 0
                    width: 14; height: 14; radius: 7
                    color: searchClearHover.hovered ? "#c94b3d" : "#b0b0b0"
                    Text {
                        anchors.centerIn: parent
                        text: "✕"; color: "white"; font.pixelSize: 8
                        font.bold: true
                    }
                    HoverHandler { id: searchClearHover }
                    TapHandler {
                        onTapped: {
                            searchField.clear()
                            toolbar.searchCleared()
                        }
                    }
                }
            }
        }
        // Verzió + build a jobb felső sarokban — halványan, hogy
        // zavartalanul, de bármikor ellenőrizhető legyen, PONTOSAN
        // melyik commit fut (appVersion → version.version_string()).
        Text {
            objectName: "versionLabel"
            Layout.alignment: Qt.AlignVCenter
            text: appVersion
            font.pixelSize: 9
            color: Theme.textGray
            opacity: 0.6
            ToolTip.visible: versionHover.hovered
            ToolTip.text: qsTr("Verzió és build")
            HoverHandler { id: versionHover }
        }
    }
}
