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
    // Az eredeti címkereső online geokódolását helyi szűrés váltja ki:
    // képfájlnév, felirat, kulcsszavak és mappanév alapján keresünk a már
    // indexelt GPS-es képek között; a mező nem küld hálózati kérést.
    property string searchDraft: ""
    property string searchTerm: ""
    readonly property var filteredMarkers: {
        var query = panel.searchTerm.trim().toLowerCase()
        if (!query) return panel.markers
        return panel.markers.filter(function(marker) {
            var haystack = [marker.name, marker.caption,
                            marker.keywords, marker.folder]
                .join(" ").toLowerCase()
            return haystack.indexOf(query) >= 0
        })
    }
    readonly property var mapTypeNames:
        mapLoader.item && mapLoader.item.mapTypeNames.length
            ? mapLoader.item.mapTypeNames : [qsTr("Map")]
    readonly property int mapTypeIndex:
        mapLoader.item ? mapLoader.item.activeMapTypeIndex : 0
    readonly property bool mapAvailable: mapLoader.status === Loader.Ready

    signal closeRequested()
    signal photoActivated(int row)
    //: #1404: a törlés VISSZAFORDÍTHATATLAN — a panel nem maga törli,
    //: hanem a gazdát kéri meg, hogy futtassa a megerősítést.
    signal clearGeotagRequested(var rows)
    //: #2013: a hely BEÁLLÍTÁSA is a gazdán megy át — 20 kijelölt elem
    //: fölött az eredeti megerősítést kér (`0x00652585`, `cmp ebx, 0x14`).
    signal setGeotagRequested(var rows, real latitude, real longitude)
    //: #4582: a jelölő buborékából a képcsoportot mutatjuk a rácsban.
    signal markerSearchRequested(var rows)

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
                text: qsTr("%1 pictures with a place")
                          .arg(panel.filteredMarkers.length)
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            Item { Layout.fillWidth: true }
            PicasaComboBox {
                objectName: "placesMapTypeMenu"
                Layout.preferredWidth: 104
                Layout.preferredHeight: 21
                model: panel.mapTypeNames
                currentIndex: panel.mapTypeIndex
                onActivated: function(index) {
                    if (mapLoader.item)
                        mapLoader.item.selectMapType(index)
                }
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
                item.markers = Qt.binding(function() {
                    return panel.filteredMarkers
                })
                item.markerActivated.connect(function(row) {
                    // Előbb jelöljük ki a képét, utána szűrjünk: a főablak a
                    // modellváltáskor az azonosítója alapján visszaállítja a
                    // kijelölést a geocímkézett rácsban.
                    panel.photoActivated(row)
                    if (controller) controller.showGeotagged()
                })
                item.markerSearchRequested.connect(panel.markerSearchRequested)
                item.markerEraseRequested.connect(panel.clearGeotagRequested)
                item.placePicked.connect(panel.placeSelection)
            }
        }

        Text {
            objectName: "placesSearchLabel"
            Layout.fillWidth: true
            text: qsTr("Search")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        Rectangle {
            objectName: "placesSearchGroup"
            Layout.fillWidth: true
            Layout.preferredHeight: 28
            color: Theme.contentPanel
            border.color: Theme.chromeBorder
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 1
                spacing: 4

                TextField {
                    id: placesSearchInput
                    objectName: "placesSearchInput"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: panel.searchDraft
                    onTextChanged: panel.searchDraft = text
                    onAccepted: panel.applyLocalSearch()
                    TextFieldContextArea {}
                }

                PicasaButton {
                    id: placesSearchButton
                    objectName: "placesSearchButton"
                    Layout.preferredWidth: 28
                    Layout.fillHeight: true
                    text: qsTr("Search")
                    Accessible.name: qsTr("Search")
                    ToolTip.text: qsTr("Search")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    contentItem: Image {
                        source: "icons/loupe.svg"
                        fillMode: Image.PreserveAspectFit
                        sourceSize.width: 16
                        sourceSize.height: 16
                    }
                    onClicked: panel.applyLocalSearch()
                }
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

    function applyLocalSearch() {
        panel.searchTerm = panel.searchDraft.trim()
    }
}
