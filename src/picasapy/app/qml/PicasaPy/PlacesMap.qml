import QtQuick
import QtLocation
import QtPositioning

// Térkép a Helyek-panelhez (#30) — KÜLÖN fájlban, mert a QtLocation modul
// nem minden PySide6-telepítésben van meg: a PlacesPanel Loaderrel tölti,
// és hiánya csak ezt a komponenst viszi el, az appot nem.
Item {
    id: root

    // jelölők: [{row, name, latitude, longitude}] — a controller.geoMarkers
    property var markers: []
    // a térképen kattintott hely (a „kép ide" művelethez)
    signal placePicked(real latitude, real longitude)
    // jelölőre kattintás → a kép sora
    signal markerActivated(int row)

    function centerOnMarkers() {
        if (!markers || markers.length === 0) return
        var lat = 0, lon = 0
        for (var i = 0; i < markers.length; ++i) {
            lat += markers[i].latitude
            lon += markers[i].longitude
        }
        map.center = QtPositioning.coordinate(lat / markers.length,
                                              lon / markers.length)
    }

    Plugin {
        id: osmPlugin
        name: "osm"
    }

    Map {
        id: map
        objectName: "placesMap"
        anchors.fill: parent
        plugin: osmPlugin
        zoomLevel: 4
        center: QtPositioning.coordinate(47.4979, 19.0402)  // alapnézet

        MapItemView {
            model: root.markers
            delegate: MapQuickItem {
                required property var modelData
                coordinate: QtPositioning.coordinate(modelData.latitude,
                                                     modelData.longitude)
                anchorPoint.x: pin.width / 2
                anchorPoint.y: pin.height
                sourceItem: Item {
                    id: pin
                    width: 18; height: 24
                    Rectangle {
                        width: 14; height: 14; radius: 7
                        anchors.horizontalCenter: parent.horizontalCenter
                        color: Theme.brandRed
                        border.color: "#ffffff"; border.width: 2
                    }
                    Rectangle {
                        width: 2; height: 10
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom
                        color: Theme.brandRed
                    }
                    TapHandler {
                        onTapped: root.markerActivated(pin.parent.modelData.row)
                    }
                }
            }
        }

        TapHandler {
            acceptedButtons: Qt.RightButton
            onTapped: function(point) {
                var coord = map.toCoordinate(point.position)
                root.placePicked(coord.latitude, coord.longitude)
            }
        }
    }

    onMarkersChanged: centerOnMarkers()
    Component.onCompleted: centerOnMarkers()
}
