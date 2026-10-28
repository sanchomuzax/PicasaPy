import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: personAlbumFeedHeader
    required property var feed
    readonly property var ctl: typeof controller !== "undefined" ? controller : null
    objectName: "personAlbumFeedHeader"
    readonly property bool active: feed.appWindow
        && feed.appWindow.personAlbumName !== ""
    width: feed.width
    // A fejléc magasságát a Loader tartalma adja. A Column
    // childrenRect-jének visszaolvasása a ListView fejléc-elrendezésével
    // magasság-kötési hurkot okozott (#5363).
    height: active ? personAlbumLoader.height : 0
    implicitHeight: height
    visible: active
    // a fejléc magassága a Loader-es tartalom elrendezése után áll be,
    // és a lista eredete (originY) vele mozdul. Ezért magasságváltáskor
    // azonnal a fejléchez igazítunk: a késleltetett igazítás addig a
    // gombokat a látótéren kívülre tolja, és a kattintás mellé érne
    onHeightChanged: if (active)
        feed.alignPersonAlbumHeader()

    Column {
        id: personAlbumColumn
        width: parent.width
        spacing: 0

        // Személyalbum-módban épül a fejléc és az arcsáv. Mappa-nézetben
        // nem maradhat belőle példány a fában: a mappa-fejléc gombjait
        // objectName szerint kereső lekérdezés az elsőt találná meg, és
        // az rejtett lenne.
        Loader {
            id: personAlbumLoader
            active: personAlbumFeedHeader.active
            width: parent.width
            // Az item saját implicit magassága független a ListView
            // fejlécétől; ez ad stabil méretet az első elrendezéskor.
            height: active && item ? item.implicitHeight : 0
            sourceComponent: Component {
                Column {
                    width: parent.width
                    spacing: 0

                    LightboxHeader {
                        id: personAlbumHeader
                        objectName: "personAlbumHeader"
                        width: parent.width
                        personAlbumHeaderMode: true
                        personName: feed.appWindow.personAlbumName
                        personAvatarUrl: feed.appWindow.personAlbumAvatarUrl
                        personAlbumRemoveEnabled:
                            feed.appWindow.personAlbumCanRemoveSelection
                        personAlbumThumbnailEnabled:
                            feed.appWindow.personAlbumCanSetThumbnail
                        selectedCount: feed.appWindow.selectedIndexes
                            ? feed.appWindow.selectedIndexes.length : 0
                        hasPendingEdits:
                            feed.appWindow.kijelolesbenVanMentetlenSzerkesztes
                        suggestionCount: feed.appWindow.personSuggestionCount
                        selectedSuggestionCount:
                            feed.appWindow.personSelectedSuggestionIds.length
                        faceZoom: feed.appWindow.personFaceZoom
                        suggestionsOnly: feed.appWindow.personSuggestionsOnly
                        onPlayRequested: {
                                var photos = ctl ? ctl.personAlbumPhotos : []
                            if (photos.length > 0)
                                feed.slideshowRequested(Number(photos[0].row))
                        }
                        onCollageRequested: {
                            if (!feed.appWindow || !feed.appWindow.openCollageFromRows)
                                return
                                var photos = ctl ? ctl.personAlbumPhotos : []
                            var rows = []
                            for (var i = 0; i < photos.length; ++i)
                                rows.push(Number(photos[i].row))
                            feed.appWindow.openCollageFromRows(rows)
                        }
                        onPersonMovieRequested: {
                            if (feed.appWindow.openPersonAlbumMovie)
                                feed.appWindow.openPersonAlbumMovie()
                        }
                        onRemovePersonAlbumRequested: {
                            if (feed.appWindow.removePersonAlbumSelection)
                                feed.appWindow.removePersonAlbumSelection()
                        }
                        onSetPersonThumbnailRequested: {
                            if (feed.appWindow.setPersonAlbumThumbnailFromSelection)
                                feed.appWindow.setPersonAlbumThumbnailFromSelection()
                        }
                        onSelectSuggestionsRequested: {
                            if (feed.appWindow.selectPersonSuggestions)
                                feed.appWindow.selectPersonSuggestions()
                        }
                        onConfirmSuggestionsRequested: {
                            if (feed.appWindow.confirmPersonSuggestions)
                                feed.appWindow.confirmPersonSuggestions()
                        }
                        onRemoveSuggestionsRequested: {
                            if (feed.appWindow.removePersonSuggestions)
                                feed.appWindow.removePersonSuggestions()
                        }
                        onSuggestionsOnlyToggled: function(only) {
                            if (feed.appWindow.setPersonSuggestionsOnly)
                                feed.appWindow.setPersonSuggestionsOnly(only)
                        }
                        onFaceZoomToggled: function(face) {
                            if (feed.appWindow.setPersonFaceZoom)
                                feed.appWindow.setPersonFaceZoom(face)
                        }
                        onMoreSuggestionsRequested: {
                            if (feed.appWindow.findMoreSuggestions)
                                feed.appWindow.findMoreSuggestions()
                        }
                    }

                    Item {
                        width: parent.width
                        height: 215

                        ListView {
                            id: personAlbumFaceStrip
                            objectName: "personAlbumFaceStrip"
                            x: 16; y: 18
                            width: Math.max(0, parent.width - x)
                            height: 182
                            orientation: ListView.Horizontal
                            spacing: 0
                            clip: true
                                model: ctl ? ctl.personAlbumPhotos : []

                            delegate: Item {
                                required property var modelData
                                width: 162
                                height: 182

                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 122; height: 147
                                    color: Theme.thumbCard
                                    border.width: 1
                                    border.color: Theme.thumbBorder
                                    Image {
                                        objectName: "personAlbumFaceImage"
                                        readonly property bool imageReady:
                                            status === Image.Ready
                                        anchors.fill: parent
                                        anchors.margins: 1
                                        source: modelData.thumbUrl || ""
                                        fillMode: Image.PreserveAspectCrop
                                        asynchronous:
                                            Qt.platform.pluginName !== "offscreen"
                                        cache: true
                                        smooth: true
                                        mipmap: true
                                    }
                                }

                                TapHandler {
                                    onDoubleTapped: feed.openRequested(
                                        Number(modelData.row))
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
