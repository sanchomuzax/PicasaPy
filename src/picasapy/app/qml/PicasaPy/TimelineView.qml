import QtQuick
import QtQuick.Controls
import QtQuick.Window
import PicasaPy

// A Picasa Időrendje önálló, teljes képernyős bemutatóablak. A kártya mérete
// a job-217 1280x1024-es felvételén mért 600x480 px, ezért nem skálázódik az
// ablakhoz. A mozgásképletek a timelineController Qt-mentes segédeit hívják.
Window {
    id: show
    objectName: "timelineView"
    color: "#000000"
    flags: Qt.Window | Qt.FramelessWindowHint
    visible: false

    readonly property int fullscreenVisibility: Window.FullScreen
    readonly property int windowedVisibility: Window.Windowed
    readonly property int panelWidth: 600
    readonly property int panelHeight: 480
    property var collectionsModel: []
    property int currentIndex: -1
    property int previousIndex: -1
    property int animationDurationMs: 0
    property real transitionProgress: 1.0
    property bool animating: false
    property bool draggingSlider: false
    property real dragX: 0
    property int pendingSliderIndex: -1
    property real animationStartedAt: 0
    property var currentOffset: [0.0, 0.0]
    property var previousOffset: [0.0, 0.0]

    signal closed()
    signal slideshowRequested(string collectionId)

    function collectionAt(index) {
        if (!collectionsModel || index < 0 || index >= collectionsModel.length)
            return null
        return collectionsModel[index]
    }

    function photoAt(collectionIndex, photoIndex) {
        var collection = show.collectionAt(collectionIndex)
        if (!collection || !collection.photos
                || photoIndex < 0 || photoIndex >= collection.photos.length)
            return null
        return collection.photos[photoIndex]
    }

    function sliderValues() {
        var values = []
        for (var i = 0; i < collectionsModel.length; ++i)
            values.push(Number(collectionsModel[i].sliderPosition || 0))
        return values
    }

    function selectedSliderPosition() {
        var collection = show.collectionAt(currentIndex)
        return collection ? Number(collection.sliderPosition || 0) : 0
    }

    function animateTo(index, duration) {
        if (!collectionsModel || collectionsModel.length === 0)
            return
        var target = Math.max(0, Math.min(collectionsModel.length - 1, index))
        if (target === currentIndex)
            return

        previousIndex = currentIndex
        currentIndex = target
        animationDurationMs = duration
        transitionProgress = 0
        animationStartedAt = Date.now()
        if ((typeof timelineController !== "undefined" && timelineController)) {
            var nextOffsets = timelineController.randomOffsets(
                currentOffset[0], currentOffset[1],
                Math.floor(Math.random() * 32768),
                Math.floor(Math.random() * 32768),
                panelWidth, panelHeight)
            currentOffset = nextOffsets.current
            previousOffset = nextOffsets.previous
        }
        animating = true
    }

    function step(delta) {
        if (currentIndex < 0)
            return
        show.animateTo(currentIndex + delta, 2000)
    }

    function startCurrentSlideshow() {
        var collection = show.collectionAt(currentIndex)
        if (collection) {
            var collectionId = collection.collectionId || collection.folderPath
            if (collectionId)
                show.slideshowRequested(collectionId)
        }
    }

    function resetForOpen() {
        animating = false
        draggingSlider = false
        pendingSliderIndex = -1
        currentIndex = collectionsModel && collectionsModel.length > 0 ? 0 : -1
        previousIndex = currentIndex
        transitionProgress = 1
        currentOffset = [0.0, 0.0]
        previousOffset = [0.0, 0.0]
    }

    function updateSliderFromX(x) {
        dragX = x
        var ratio = Math.max(0, Math.min(1,
            (x - timelinePanel.sliderAreaX)
                / Math.max(1, timelinePanel.sliderAreaWidth)))
        pendingSliderIndex = (typeof timelineController !== "undefined" && timelineController)
            ? timelineController.sliderIndex(show.sliderValues(), ratio) : -1
    }

    function releaseSlider() {
        draggingSlider = false
        if (pendingSliderIndex >= 0)
            show.animateTo(pendingSliderIndex, 4000)
    }

    readonly property var frameTransforms: (typeof timelineController !== "undefined" && timelineController)
        ? timelineController.frameAt(
              transitionProgress,
              currentOffset[0], currentOffset[1],
              previousOffset[0], previousOffset[1],
              previousIndex !== currentIndex)
        : ({
            current: { scale: 1, tx: 1, ty: 1 },
            previous: { scale: 1, tx: 1, ty: 1 },
            alpha: 256
        })
    readonly property int currentLayerAlpha: Math.max(
        0, Math.min(255, Number(frameTransforms.alpha) - 1))
    readonly property real currentLayerOpacity: currentLayerAlpha / 256.0
    readonly property real previousLayerOpacity:
        (255 - currentLayerAlpha) / 256.0
    readonly property var dotsModel: timelinePanel.dotsModel
    readonly property bool currentCardsLoaded: timelinePanel.currentCardsLoaded
    readonly property var currentPhotoCardGeometry:
        timelinePanel.currentPhotoCardGeometry
    onCollectionsModelChanged: {
        if (collectionsModel && collectionsModel.length > 0 && currentIndex < 0) {
            currentIndex = 0
            previousIndex = 0
            transitionProgress = 1
        }
    }
    onVisibleChanged: {
        if (visible) {
            visibility = Window.FullScreen
            resetForOpen()
            show.requestActivate()
            keyboardTarget.forceActiveFocus()
        } else {
            // A Window.Windowed érték ismét láthatóvá tenné az ablakot;
            // bezáráskor a láthatóságot a `visible` kötés intézi.
            animating = false
            draggingSlider = false
        }
    }

    Timer {
        interval: 16
        repeat: true
        running: show.animating && show.visible
        onTriggered: {
            var elapsed = Date.now() - show.animationStartedAt
            var progress = Math.max(0, Math.min(1,
                elapsed / Math.max(1, show.animationDurationMs)))
            show.transitionProgress = (typeof timelineController !== "undefined" && timelineController)
                ? timelineController.easingAt(progress) : progress
            if (progress >= 1) {
                show.transitionProgress = 1
                show.animating = false
                show.previousIndex = show.currentIndex
            }
        }
    }

    Item {
        id: keyboardTarget
        objectName: "timelineKeyboardTarget"
        anchors.fill: parent
        focus: true
        Keys.onPressed: function(event) {
            if (event.key === Qt.Key_Escape) {
                show.closed()
                event.accepted = true
            } else if (event.key === Qt.Key_Right) {
                show.step(1)
                event.accepted = true
            } else if (event.key === Qt.Key_Left) {
                show.step(-1)
                event.accepted = true
            } else if (event.key === Qt.Key_Space) {
                show.startCurrentSlideshow()
                event.accepted = true
            }
        }
    }

    TimelinePanel {
        id: timelinePanel
        hostWindow: show
    }
}
