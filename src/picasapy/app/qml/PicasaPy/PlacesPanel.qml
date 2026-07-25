import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Helyek-panel (#30): a látszó képek helyei térképen, és a kijelölt képek
// geocímkézése.
//
// A térkép külön fájlban (PlacesMap.qml) él, és Loaderrel töltjük: a
// QtLocation modul nem minden telepítésben van meg, így a hiánya csak
// ennek a panelnek a tartalmát viszi el (érthető üzenettel), az appot nem.
// A Loader csak LÁTHATÓ panelnél aktív — rejtett panel nem tölt térképet
// és nem tölt le csempéket.
Rectangle {
    id: panel
    objectName: "placesPanel"

    // a főablak (a kijelölt sorok forrása)
    required property var appWindow

    readonly property var markers: controller ? controller.geoMarkers : []
    readonly property bool mapAvailable: mapLoader.status === Loader.Ready

    signal closeRequested()
    signal photoActivated(int row)

    color: Theme.contentPanel
    border.color: Theme.chromeBorder

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: qsTr("Places")
                font.pixelSize: Theme.folderTitleSize
                font.weight: Font.DemiBold
                color: Theme.ink
            }
            Item { Layout.fillWidth: true }
            Text {
                objectName: "placesCountLabel"
                text: qsTr("%1 pictures with a place").arg(panel.markers.length)
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            PicasaButton {
                objectName: "placesCloseButton"
                text: qsTr("Close")
                onClicked: panel.closeRequested()
            }
        }

        Loader {
            id: mapLoader
            objectName: "placesMapLoader"
            Layout.fillWidth: true
            Layout.fillHeight: true
            active: panel.visible
            source: "PlacesMap.qml"
            onLoaded: {
                item.markers = Qt.binding(function() { return panel.markers })
                item.markerActivated.connect(panel.photoActivated)
                item.placePicked.connect(panel.placeSelection)
            }
        }

        // A térkép hiányában is használható marad a panel: a hely-lista és
        // a címke-törlés nem függ a QtLocation-től.
        Text {
            objectName: "placesFallbackText"
            visible: mapLoader.status === Loader.Error
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("The map component (QtLocation) is not available. Geotags can still be edited.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                objectName: "placesHintText"
                Layout.fillWidth: true
                elide: Text.ElideRight
                text: panel.mapAvailable
                      ? qsTr("Right-click the map to place the selected pictures.")
                      : ""
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            PicasaButton {
                objectName: "placesClearButton"
                text: qsTr("Remove Geotag")
                enabled: panel.appWindow.selectedIndexes.length > 0
                onClicked: controller.clearGeotagRows(
                    panel.appWindow.selectedIndexes)
            }
        }
    }

    // a térképen kiválasztott hely a KIJELÖLÉSRE kerül (Picasa-viselkedés:
    // a művelet mindig a kijelölt képekre hat)
    function placeSelection(latitude, longitude) {
        if (appWindow.selectedIndexes.length === 0) return
        controller.setGeotagRows(appWindow.selectedIndexes, latitude, longitude)
    }
}
