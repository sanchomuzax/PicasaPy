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
    readonly property real panelWidth: 480 * width / Math.max(1, height)
    readonly property real panelHeight: 480
    readonly property real panelScale: height / panelHeight
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
    property real carouselOffset: 0.0
    property real carouselVelocity: 0.0
    property real animatorBaseOffset: 0.0
    property real lastAnimatorPosition: 0.0
    property var animatorRecords: []
    property string motionMode: "idle"
    property bool draggingCarousel: false
    property real dragStartX: 0.0
    property real lastDragX: 0.0
    property bool dragMoved: false
    // A háttér átúszása a lapváltás mért kb. 1,4 mp-e (38.2.85, mérés;
    // a pontos időtartam binárisból nincs meg).
    property int backgroundFadeDurationMs: 1400

    signal closed()
    signal slideshowRequested(string collectionId)

    readonly property var carouselLayouts:
        (typeof timelineController !== "undefined" && timelineController
            && collectionsModel)
            ? timelineController.carouselLayout(carouselOffset, collectionsModel.length)
            : []

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
        if (target === currentIndex && motionMode === "idle"
                && Math.abs(carouselVelocity) < 0.000001)
            return

        beginCarouselMotion()
        var now = Date.now()
        updateCarouselAnimator(now / 1000)
        var targetOffset = (typeof timelineController !== "undefined" && timelineController)
            ? timelineController.clampOffset(
                  timelineController.focusParameter()
                      - target * timelineController.carouselCardStep,
                  collectionsModel.length)
            : carouselOffset
        var currentPosition = (typeof timelineController !== "undefined" && timelineController)
            ? timelineController.animatorPosition(
                  animatorBaseOffset, animatorRecords, now / 1000)
            : carouselOffset
        appendAnimatorRecord(targetOffset - currentPosition, duration, now)
    }

    function step(delta) {
        if (currentIndex < 0 || !collectionsModel || collectionsModel.length === 0)
            return
        pendingSliderIndex = -1
        beginCarouselMotion()
        var now = Date.now()
        updateCarouselAnimator(now / 1000)
        var direction = (typeof timelineController !== "undefined" && timelineController)
            ? timelineController.carouselCardStep : 0.05
        appendAnimatorRecord(-delta * direction, 2000, now)
    }

    function beginCarouselMotion() {
        if (motionMode === "background")
            finishBackgroundTransition()
        if (motionMode === "carousel")
            return
        motionMode = "carousel"
        animatorBaseOffset = carouselOffset
        lastAnimatorPosition = carouselOffset
        animatorRecords = []
        carouselVelocity = 0
        draggingCarousel = false
        previousIndex = currentIndex
        transitionProgress = 0
        animating = true
    }

    function updateCarouselAnimator(nowSeconds) {
        if (!animatorRecords || animatorRecords.length === 0)
            return
        var position = timelineController.animatorPosition(
            animatorBaseOffset, animatorRecords, nowSeconds)
        var delta = position - lastAnimatorPosition
        lastAnimatorPosition = position
        carouselOffset = timelineController.clampOffset(
            carouselOffset + delta + carouselVelocity,
            collectionsModel.length)
        carouselVelocity *= 0.95
    }

    function appendAnimatorRecord(delta, duration, nowMs) {
        animatorRecords = animatorRecords.concat([{
            delta: delta,
            started_at: nowMs / 1000,
            duration: duration / 1000
        }])
        animationDurationMs = duration
        animationStartedAt = nowMs
        animating = true
    }

    function beginCarouselDrag(x) {
        pendingSliderIndex = -1
        if (motionMode === "background")
            finishBackgroundTransition()
        if (motionMode === "carousel")
            updateCarouselAnimator(Date.now() / 1000)
        animatorBaseOffset = carouselOffset
        lastAnimatorPosition = carouselOffset
        animatorRecords = []
        carouselVelocity = 0
        draggingCarousel = true
        dragStartX = x
        lastDragX = x
        dragMoved = false
        motionMode = "drag"
        animationStartedAt = Date.now()
        animationDurationMs = 0
        transitionProgress = 1
        previousIndex = currentIndex
        animating = true
    }

    function dragCarouselTo(x) {
        if (!draggingCarousel || !timelineController)
            return
        var distance = x - lastDragX
        if (Math.abs(distance) < 0.5)
            return
        var parameter = carouselOffset + currentIndex * timelineController.carouselCardStep
        var curveBefore = timelineController.bezierAt(parameter - 0.001)
        var curveAfter = timelineController.bezierAt(parameter + 0.001)
        var derivative = (curveAfter.x - curveBefore.x) / 0.002
        if (Math.abs(derivative) < 0.001)
            derivative = 1
        var delta = -distance / (panelWidth * derivative)
        carouselOffset = timelineController.clampOffset(
            carouselOffset + delta, collectionsModel.length)
        carouselVelocity = delta
        lastDragX = x
        if (Math.abs(x - dragStartX) > 4)
            dragMoved = true
    }

    function endCarouselDrag() {
        if (!draggingCarousel)
            return
        draggingCarousel = false
        if (Math.abs(carouselVelocity)
                > (timelineController ? timelineController.carouselCardStep * 0.01 : 0.0005)) {
            motionMode = "inertia"
            animating = true
        } else {
            finishCarouselMotion()
        }
    }

    function finishCarouselMotion() {
        if (!collectionsModel || collectionsModel.length === 0) {
            pendingSliderIndex = -1
            motionMode = "idle"
            animating = false
            return
        }
        carouselOffset = timelineController
            ? timelineController.clampOffset(carouselOffset, collectionsModel.length)
            : carouselOffset
        animatorBaseOffset = carouselOffset
        lastAnimatorPosition = carouselOffset
        animatorRecords = []
        carouselVelocity = 0
        var focusedIndex = timelineController
            ? timelineController.focusIndex(carouselOffset, collectionsModel.length)
            : currentIndex
        if (focusedIndex >= 0 && focusedIndex !== currentIndex) {
            previousIndex = currentIndex
            currentIndex = focusedIndex
            pendingSliderIndex = -1
            motionMode = "background"
            animationStartedAt = Date.now()
            transitionProgress = 0.6800000071525574
            animating = true
            return
        }
        previousIndex = currentIndex
        pendingSliderIndex = -1
        transitionProgress = 1
        motionMode = "idle"
        animating = false
    }

    function finishBackgroundTransition() {
        previousIndex = currentIndex
        transitionProgress = 1
        motionMode = "idle"
        animating = false
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
        draggingCarousel = false
        pendingSliderIndex = -1
        currentIndex = collectionsModel && collectionsModel.length > 0 ? 0 : -1
        previousIndex = currentIndex
        transitionProgress = 1
        currentOffset = [0.0, 0.0]
        previousOffset = [0.0, 0.0]
        carouselOffset = timelineController ? timelineController.focusParameter() : 0
        carouselVelocity = 0
        animatorBaseOffset = carouselOffset
        lastAnimatorPosition = carouselOffset
        animatorRecords = []
        motionMode = "idle"
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
        var target = pendingSliderIndex
        if (target < 0)
            return
        if (target === currentIndex && motionMode === "idle"
                && Math.abs(carouselVelocity) < 0.000001) {
            pendingSliderIndex = -1
            return
        }
        // #6902: a bináris 0x00c7e4a4 konstansa szerinti 4,0 másodperc.
        show.animateTo(target, 4000)
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
            var now = Date.now()
            var elapsed = now - show.animationStartedAt
            var duration = Math.max(
                1,
                show.motionMode === "background"
                    ? show.backgroundFadeDurationMs : show.animationDurationMs)
            if (show.motionMode === "carousel") {
                show.updateCarouselAnimator(now / 1000)
                var progress = Math.max(0, Math.min(1, elapsed / duration))
                show.transitionProgress = timelineController
                    ? timelineController.easingAt(progress) : progress
                var pending = false
                var nowSeconds = now / 1000
                for (var i = 0; i < show.animatorRecords.length; ++i) {
                    var record = show.animatorRecords[i]
                    if (nowSeconds + 0.02
                            < record.started_at + record.duration)
                        pending = true
                }
                var velocityThreshold = timelineController
                    ? timelineController.carouselCardStep * 0.01 : 0.0005
                if (!pending && Math.abs(show.carouselVelocity) <= velocityThreshold)
                    show.finishCarouselMotion()
            } else if (show.motionMode === "inertia") {
                show.carouselOffset = timelineController
                    ? timelineController.clampOffset(
                          show.carouselOffset + show.carouselVelocity,
                          show.collectionsModel.length)
                    : show.carouselOffset + show.carouselVelocity
                show.carouselVelocity *= 0.95
                var inertiaThreshold = timelineController
                    ? timelineController.carouselCardStep * 0.01 : 0.0005
                if (Math.abs(show.carouselVelocity) <= inertiaThreshold)
                    show.finishCarouselMotion()
            } else if (show.motionMode === "background") {
                var fadeProgress = Math.max(0, Math.min(1, elapsed / duration))
                show.transitionProgress = 0.6800000071525574
                    + 0.3199999928474426 * fadeProgress
                if (fadeProgress >= 1) {
                    show.transitionProgress = 1
                    show.previousIndex = show.currentIndex
                    show.motionMode = "idle"
                    show.animating = false
                }
            } else if (show.motionMode === "drag") {
                show.transitionProgress = 1
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
            } else if (event.key === Qt.Key_Up) {
                show.step(-1)
                event.accepted = true
            } else if (event.key === Qt.Key_Space) {
                show.startCurrentSlideshow()
                event.accepted = true
            } else if (event.key === Qt.Key_Down) {
                show.step(1)
                event.accepted = true
            }
        }
    }

    TimelinePanel {
        id: timelinePanel
        hostWindow: show
    }
}
