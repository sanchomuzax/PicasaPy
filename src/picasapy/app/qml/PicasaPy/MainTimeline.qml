import QtQuick
import QtQuick.Window
import PicasaPy

// A főablak Időrend-bemutatójának állapota és ablakbeli bekötése (#6136).
TimelineView {
    id: timeline
    objectName: "timelineView"

    required property var hostWindow
    required property var hostController
    required property var hostTimelineController
    required property var hostToolbar
    required property var hostSlideshow

    property bool timelineOpen: false
    property bool timelineSlideshowActive: false
    property var timelineSlideshowModel: null

    visible: timelineOpen
    collectionsModel: hostTimelineController
        ? hostTimelineController.collections : []

    function timelineCollectionForId(collectionId) {
        if (!hostTimelineController || !hostTimelineController.collections)
            return null
        var keresett = String(collectionId || "")
        for (var i = 0; i < hostTimelineController.collections.length; ++i) {
            var collection = hostTimelineController.collections[i]
            if (collection.collectionId === keresett
                    || collection.folderPath === keresett)
                return collection
        }
        return null
    }

    function selectTimelineCollection(collection) {
        if (!hostController || !collection)
            return -1
        hostToolbar.clearSearch()
        hostWindow.clearSelection()
        hostWindow.unnamedFacesOpen = false
        if (collection.kind === "album")
            hostController.showAlbum(collection.albumToken)
        else
            hostController.selectFolder(collection.folderPath)
        var row = hostController.photos.rowOfPath(collection.firstPhotoPath)
        hostWindow.selectedIndex = row
        hostWindow.selectedIndexes = row >= 0 ? [row] : []
        return row
    }

    function closeTimeline() {
        var collection = timeline.collectionAt(timeline.currentIndex)
        if (collection)
            timeline.selectTimelineCollection(collection)
        timeline.timelineOpen = false
    }

    function toggleTimeline() {
        if (timeline.timelineOpen) {
            timeline.closeTimeline()
            return
        }
        if (hostTimelineController)
            hostTimelineController.reload()
        timeline.timelineOpen = true
    }

    function startTimelineSlideshow(collectionId) {
        if (!hostController || !collectionId || !hostTimelineController)
            return
        var collection = timeline.timelineCollectionForId(collectionId)
        if (!collection)
            return
        var collectionModel = hostTimelineController.slideshowModel(
            collection.collectionId)
        if (!collectionModel || collectionModel.rowCount() <= 0)
            return
        timeline.selectTimelineCollection(collection)
        timeline.timelineOpen = false
        timeline.timelineSlideshowModel = collectionModel
        timeline.timelineSlideshowActive = true
        hostWindow.visibilityBeforeSlideshow = hostWindow.visibility
        hostWindow.visibility = Window.FullScreen
        hostSlideshow.start(0)
        if (!hostSlideshow.visible)
            hostWindow.exitSlideshow()
    }

    onClosed: hostWindow.closeTimeline()
    onSlideshowRequested: function(collectionId) {
        hostWindow.startTimelineSlideshow(collectionId)
    }
}
