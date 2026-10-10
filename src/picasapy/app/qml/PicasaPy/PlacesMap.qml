import QtQuick
import QtLocation
import QtPositioning

// Térkép a Helyek-panelhez (#30) — KÜLÖN fájlban, mert a QtLocation modul
// nem minden PySide6-telepítésben van meg: a PlacesPanel Loaderrel tölti,
// és hiánya csak ezt a komponenst viszi el, az appot nem.
Item {
    id: root

    // jelölők: [{row, name, thumbUrl, latitude, longitude}] — controller.geoMarkers
    property var markers: []
    readonly property var groupedMarkers: {
        var groups = []
        var byPosition = {}
        if (!markers) return groups
        for (var i = 0; i < markers.length; ++i) {
            var marker = markers[i]
            // A geotag írása hat tizedesjegyű; ez a pontosság egy helyen
            // tartja az azonos helyre mentett képeket.
            var key = Number(marker.latitude).toFixed(6) + ","
                    + Number(marker.longitude).toFixed(6)
            var group = byPosition[key]
            if (!group) {
                group = {
                    latitude: marker.latitude,
                    longitude: marker.longitude,
                    rows: [],
                    thumbUrl: marker.thumbUrl || ""
                }
                byPosition[key] = group
                groups.push(group)
            }
            group.rows.push(marker.row)
        }
        return groups
    }
    readonly property bool mapLoading: !map.mapReady && map.error === Map.NoError
    readonly property bool offline: map.error === Map.ConnectionError
    readonly property var mapTypeNames: {
        var names = []
        for (var i = 0; i < map.supportedMapTypes.length; ++i)
            names.push(map.supportedMapTypes[i].name)
        return names
    }
    readonly property int activeMapTypeIndex: {
        for (var i = 0; i < map.supportedMapTypes.length; ++i) {
            if (map.supportedMapTypes[i] === map.activeMapType) return i
        }
        return 0
    }
    // a térképen kattintott hely (a „kép ide" művelethez)
    signal placePicked(real latitude, real longitude)
    // jelölőre kattintás → az első kép sora
    signal markerActivated(int row)
    // a rácsból érkezett kijelölés és az ejtési pont koordinátája
    signal photosDropped(var rows, real latitude, real longitude)
    // buborékműveletek: az azonos helyen álló összes képsor
    signal markerSearchRequested(var rows)
    signal markerEraseRequested(var rows)

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

    function selectMapType(index) {
        if (index < 0 || index >= map.supportedMapTypes.length) return
        map.activeMapType = map.supportedMapTypes[index]
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
            model: root.groupedMarkers
            delegate: MapQuickItem {
                id: markerItem
                required property var modelData
                coordinate: QtPositioning.coordinate(modelData.latitude,
                                                     modelData.longitude)
                sourceItem: PlacesMarker {
                    id: markerVisual
                    markerData: markerItem.modelData
                    onMarkerActivated: function(row) {
                        root.markerActivated(row)
                    }
                    onMarkerSearchRequested: function(rows) {
                        root.markerSearchRequested(rows)
                    }
                    onMarkerEraseRequested: function(rows) {
                        root.markerEraseRequested(rows)
                    }
                }
                anchorPoint.x: markerVisual.width / 2
                anchorPoint.y: markerVisual.height
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

    DropArea {
        id: mapDropArea
        objectName: "placesMapDropArea"
        anchors.fill: parent
        z: 1

        onDropped: function(drop) {
            var source = drop.source
            if (!source || source.payload !== "photos") return
            var rows = source.photoRows
            if (!rows || rows.length === 0) return
            var mapPoint = map.mapFromItem(mapDropArea, drop.x, drop.y)
            var coordinate = map.toCoordinate(mapPoint)
            drop.acceptProposedAction()
            root.photosDropped(rows, coordinate.latitude,
                               coordinate.longitude)
        }
    }

    Rectangle {
        objectName: "placesDropHint"
        anchors.centerIn: parent
        z: 2
        visible: mapDropArea.containsDrag
                 && mapDropArea.drag.source
                 && mapDropArea.drag.source.payload === "photos"
        readonly property int padding: 8
        implicitWidth: dropHintLabel.implicitWidth + padding * 2
        implicitHeight: dropHintLabel.implicitHeight + padding * 2
        color: Theme.contentPanel
        border.color: Theme.chromeBorder
        radius: 3
        Text {
            id: dropHintLabel
            objectName: "placesDropHintLabel"
            anchors.centerIn: parent
            text: {
                var source = mapDropArea.drag.source
                if (!source) return ""
                var rows = source.photoRows
                return qsTr("Place %d photos here")
                    .replace("%d", String(rows ? rows.length : 1))
            }
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    onMarkersChanged: centerOnMarkers()
    Component.onCompleted: centerOnMarkers()
}
