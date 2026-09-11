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

    //: #2566: MELY SOROKRA hat a panel. Az alapértelmezés a főablak
    //: kijelölése, tehát a könyvtár-nézet használata képpontra
    //: változatlan. A nézőben viszont a rács kijelölése elavult — a néző
    //: léptetése csak a `selectedIndex`-et írja, a `selectedIndexes`-t nem
    //: —, ezért ott a NÉZETT kép sorát kapja.
    property var targetRows:
        panel.appWindow ? panel.appWindow.selectedIndexes : []

    readonly property var markers: controller ? controller.geoMarkers : []
    readonly property bool mapAvailable: mapLoader.status === Loader.Ready

    signal closeRequested()
    signal photoActivated(int row)
    //: #1404: a törlés VISSZAFORDÍTHATATLAN — a panel nem maga törli,
    //: hanem a gazdát kéri meg, hogy futtassa a megerősítést.
    signal clearGeotagRequested(var rows)
    //: #2013: a hely BEÁLLÍTÁSA is a gazdán megy át — 20 kijelölt elem
    //: fölött az eredeti megerősítést kér (`0x00652585`, `cmp ebx, 0x14`).
    signal setGeotagRequested(var rows, real latitude, real longitude)

    color: Theme.contentPanel
    border.color: Theme.chromeBorder

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        //: #754: a CÍM és a bezáró gomb a FIÓK közös fejlécében él
        //: (`RightDrawer`), nem a panelben. A darabszám-felirat a
        //: panelé marad — az a tartalomról szól, nem a fiókról.
        RowLayout {
            Layout.fillWidth: true
            Text {
                objectName: "placesCountLabel"
                text: qsTr("%1 pictures with a place").arg(panel.markers.length)
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            Item { Layout.fillWidth: true }
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
            // #1404: a MÉRT felirat — `GeotagPanel::clearbutton` =
            // „Clear %d Geotag(s)" / „%d geocímke törlése". A darabszám az
            // eredetiben is benne van; a korábbi „Remove Geotag" a mi
            // fogalmazásunk volt.
            //
            // ⚠️ A gomb NEM töröl közvetlenül: a művelet
            // visszafordíthatatlan, ezért ugyanazon a megerősítésen megy
            // át, mint a menüpont (`ClearGeoTag::warn`).
            PicasaButton {
                objectName: "placesClearButton"
                text: qsTr("Clear %1 Geotag(s)")
                          .arg(panel.targetRows.length)
                enabled: panel.targetRows.length > 0
                onClicked: panel.clearGeotagRequested(panel.targetRows)
            }
        }
    }

    // a térképen kiválasztott hely a KIJELÖLÉSRE kerül (Picasa-viselkedés:
    // a művelet mindig a kijelölt képekre hat)
    function placeSelection(latitude, longitude) {
        if (panel.targetRows.length === 0) return
        panel.setGeotagRequested(panel.targetRows, latitude, longitude)
    }
}
