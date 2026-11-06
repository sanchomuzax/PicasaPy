import QtQuick
import QtQuick.Controls
import PicasaPy

Item {
    id: panel
    required property var hostWindow
    objectName: "timelinePanel"
    width: hostWindow.panelWidth
    height: hostWindow.panelHeight
    anchors.centerIn: parent
    scale: hostWindow.panelScale
    clip: true
    property int carouselCountRevision: 0

    readonly property var dotsModel: (typeof timelineController !== "undefined" && timelineController)
        ? timelineController.dotPositions(
              hostWindow.sliderValues(), 0, Math.max(0, sliderArea.width - 4), 7,
              28, 0, 10)
        : []
    readonly property bool currentCardsLoaded: {
        carouselCountRevision
        var card = carouselDeck.itemAt(hostWindow.currentIndex)
        return card ? card.imagesLoaded : false
    }
    readonly property var currentPhotoCardGeometry: {
        carouselCountRevision
        var card = carouselDeck.itemAt(hostWindow.currentIndex)
        return card ? card.photoGeometry : []
    }

    readonly property real sliderAreaX: sliderArea.x
    readonly property real sliderAreaWidth: sliderArea.width
    readonly property var selectedBackgroundPhoto:
        hostWindow.photoAt(hostWindow.currentIndex, 0)
    readonly property var previousBackgroundPhoto:
        hostWindow.photoAt(hostWindow.previousIndex, 0)

    // Amíg a háttérkép nincs kész (vagy nincs kijelölt fotó), a fedőréteg mért
    // átlátszatlan alapszíne látszik.
    Rectangle {
        anchors.fill: parent
        color: Theme.dark ? Theme.panelBg : "#8a8a8a"
    }

    Image {
        objectName: "timelinePreviousBackgroundImage"
        anchors.fill: parent
        source: panel.previousBackgroundPhoto
            ? panel.previousBackgroundPhoto.thumbUrl.replace(
                  "image://thumbs/", "image://timelinebackground/")
            : ""
        sourceSize: Qt.size(
            Math.max(1, panel.width * panel.scale),
            Math.max(1, panel.height * panel.scale))
        fillMode: Image.Stretch
        asynchronous: true
        cache: true
        smooth: true
        mipmap: true
        opacity: hostWindow.previousLayerOpacity
    }

    Image {
        id: backgroundImage
        objectName: "timelineBackgroundImage"
        anchors.fill: parent
        source: panel.selectedBackgroundPhoto
            ? panel.selectedBackgroundPhoto.thumbUrl.replace(
                  "image://thumbs/", "image://timelinebackground/")
            : ""
        sourceSize: Qt.size(
            Math.max(1, panel.width * panel.scale),
            Math.max(1, panel.height * panel.scale))
        fillMode: Image.Stretch
        asynchronous: true
        cache: true
        smooth: true
        mipmap: true
        opacity: hostWindow.currentLayerOpacity
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onPressed: function(mouse) {
            hostWindow.beginCarouselDrag(mouse.x)
        }
        onPositionChanged: function(mouse) {
            if (pressed)
                hostWindow.dragCarouselTo(mouse.x)
        }
        onReleased: hostWindow.endCarouselDrag()
    }

    WheelHandler {
        onWheel: function(event) {
            hostWindow.step(event.angleDelta.y > 0 ? 1 : -1)
            event.accepted = true
        }
    }

    Canvas {
        id: cardArtwork
        objectName: "timelineCardArtwork"
        width: panel.width
        height: 400
        readonly property var dotArcPoints: {
            var values = hostWindow.sliderValues()
            if (!(typeof timelineController !== "undefined" && timelineController) || values.length === 0)
                return []
            // #6595: a pontsor a rögzített fókuszhelyen álló kötegig fut
            // (görbe a t* paraméteren), nem a mozgó kártyáig: lapozás közben
            // a felvételeken is helyben marad.
            var focusCurve = timelineController.bezierAt(
                timelineController.focusParameter())
            var focusWidth = 76 * focusCurve.z
            var firstPhoto = {
                x: focusCurve.x * panel.width - focusWidth / 2,
                y: focusCurve.y * panel.height - 72 * focusCurve.z / 2,
                width: focusWidth
            }

            // A qshow mért A[i]/A[n-1] aránya és a duplikált pontok
            // 0/7/14 px y-ága vezérli a pontok sorrendjét/helyét. A natív
            // screen-space leképezés nincs mérve: ezért a pontokat a
            // fejléc és a mért racionális Bézieren álló első kártya közötti,
            // megnevezett képernyőíven helyezzük el.
            var curveSpan = Math.max(1, panel.width - 4)
            var measuredDots = timelineController.dotPositions(
                values, 0, curveSpan, 0, 0, 0, 0)
            var startX = collectionNameText.x
                + collectionNameText.width - 8
            var startY = collectionDateText.y + 42
            var endX = firstPhoto.x + firstPhoto.width * 0.38
            var endY = firstPhoto.y - 48
            var control1X = startX + 3
            var control1Y = startY + 50
            var control2X = endX + 38
            var control2Y = endY - 15
            var points = []
            for (var i = 0; i < measuredDots.length; ++i) {
                var dot = measuredDots[i]
                if (!dot.draw)
                    continue
                var parameter = 1 - dot.x / curveSpan
                var oneMinusT = 1 - parameter
                points.push({
                    x: oneMinusT * oneMinusT * oneMinusT * startX
                        + 3 * oneMinusT * oneMinusT * parameter * control1X
                        + 3 * oneMinusT * parameter * parameter * control2X
                        + parameter * parameter * parameter * endX,
                    y: oneMinusT * oneMinusT * oneMinusT * startY
                        + 3 * oneMinusT * oneMinusT * parameter * control1Y
                        + 3 * oneMinusT * parameter * parameter * control2Y
                        + parameter * parameter * parameter * endY
                        + dot.y
                })
            }
            return points
        }
        onDotArcPointsChanged: requestPaint()
        onPaint: {
            var context = getContext("2d")
            context.clearRect(0, 0, width, height)

            var points = dotArcPoints
            for (var i = 0; i < points.length; ++i) {
                context.beginPath()
                context.arc(points[i].x, points[i].y, 2.3, 0, 2 * Math.PI)
                context.fillStyle = "#172239"
                context.fill()
            }
        }
        Component.onCompleted: requestPaint()
    }

    Connections {
        target: carouselDeck
        function onCountChanged() {
            panel.carouselCountRevision += 1
            cardArtwork.requestPaint()
        }
    }

    // A teljes, időrendi gyűjteménysor egy-egy kötegét rajzolja.
    Repeater {
        id: carouselDeck
        objectName: "timelineCarouselDeck"
        model: hostWindow.collectionsModel
            ? hostWindow.collectionsModel.length : 0

        delegate: Item {
            id: collectionDeck
            property int deckIndex: index
            objectName: "timelineCarouselCard" + deckIndex
            property var collection: hostWindow.collectionsModel[deckIndex]
            readonly property var layout:
                hostWindow.carouselLayouts.length > deckIndex
                    ? hostWindow.carouselLayouts[deckIndex] : null
            readonly property real depthScale: layout ? Number(layout.w) : 0
            // A képek a fókusz közelében előre betöltődnek, és a láthatóság
            // elvesztése után is megmaradnak: lapozáskor ne villanjon szürke.
            property bool kepekKellenek: false
            readonly property bool fokuszKozeleben:
                Math.abs(deckIndex - hostWindow.currentIndex) <= 12
            onVisibleChanged: if (visible) kepekKellenek = true
            onFokuszKozelebenChanged: if (fokuszKozeleben) kepekKellenek = true
            Component.onCompleted: kepekKellenek = visible || fokuszKozeleben
            property int photoStackRevision: 0
            width: 76 * depthScale
            height: 72 * depthScale
            x: layout ? Number(layout.x) * panel.width - width / 2 : 0
            y: layout ? Number(layout.y) * panel.height - height / 2 : 0
            z: layout ? Number(layout.w) : 0
            visible: layout ? Boolean(layout.visible) : false
            opacity: layout ? Number(layout.alpha) / 256 : 0
            readonly property bool imagesLoaded: {
                photoStackRevision
                if (photoStack.count === 0)
                    return false
                for (var i = 0; i < photoStack.count; ++i) {
                    var photoCard = photoStack.itemAt(i)
                    if (!photoCard || !photoCard.imageLoaded)
                        return false
                }
                return true
            }
            readonly property var photoGeometry: {
                photoStackRevision
                var geometry = []
                for (var i = 0; i < photoStack.count; ++i) {
                    var photoCard = photoStack.itemAt(i)
                    if (photoCard) {
                        geometry.push({
                            x: collectionDeck.x + photoCard.x,
                            y: collectionDeck.y + photoCard.y,
                            width: photoCard.width,
                            height: photoCard.height,
                            rotation: photoCard.rotation
                        })
                    }
                }
                return geometry
            }

            Repeater {
                id: photoStack
                objectName: "timelineCarouselPhotoDeck" + collectionDeck.deckIndex
                model: collectionDeck.kepekKellenek && collectionDeck.collection.photos
                    ? Math.min(4, collectionDeck.collection.photos.length) : 0

                delegate: Item {
                    id: stackedPhoto
                    required property int index
                    objectName: "timelineCarouselPhoto_"
                        + collectionDeck.deckIndex + "_" + index
                    property var photo: collectionDeck.collection.photos[index]
                    width: collectionDeck.width
                    height: collectionDeck.height
                    x: index * 4 * collectionDeck.depthScale
                    y: -index * 3 * collectionDeck.depthScale
                    z: index
                    rotation: index % 2 === 0 ? -7 : 5
                    readonly property bool imageLoaded: photoImage.status === Image.Ready

                    Rectangle {
                        x: 4 * collectionDeck.depthScale
                        y: 5 * collectionDeck.depthScale
                        width: parent.width
                        height: parent.height
                        radius: 2
                        color: "#55000000"
                        // #6595: a ferde köteg széle sima legyen, ne recés
                        // (tulajdonosi kérés: az eredeti itt recés).
                        antialiasing: true
                    }

                    Rectangle {
                        anchors.fill: parent
                        color: "#eeeeee"
                        border.width: 1
                        border.color: "#555555"
                        antialiasing: true
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 3 * collectionDeck.depthScale
                            color: "#777777"
                            antialiasing: true
                            Image {
                                id: photoImage
                                objectName: "timelineCarouselImage_"
                                    + collectionDeck.deckIndex + "_" + stackedPhoto.index
                                anchors.fill: parent
                                source: collectionDeck.kepekKellenek && stackedPhoto.photo
                                    ? stackedPhoto.photo.thumbUrl : ""
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                                smooth: true
                                mipmap: true
                                antialiasing: true
                            }
                        }
                    }

                    MouseArea {
                        id: kotegKattintas
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton
                        onPressed: function(mouse) {
                            var point = stackedPhoto.mapToItem(panel, mouse.x, mouse.y)
                            hostWindow.beginCarouselDrag(point.x)
                        }
                        onPositionChanged: function(mouse) {
                            if (pressed) {
                                var point = stackedPhoto.mapToItem(panel, mouse.x, mouse.y)
                                hostWindow.dragCarouselTo(point.x)
                            }
                        }
                        onReleased: hostWindow.endCarouselDrag()
                        onClicked: {
                            if (!hostWindow.dragMoved)
                                hostWindow.animateTo(collectionDeck.deckIndex, 4000)
                        }
                    }
                    PressFeedbackOverlay { pressSource: kotegKattintas }
                }
            }

            Connections {
                target: photoStack
                function onCountChanged() {
                    collectionDeck.photoStackRevision += 1
                }
            }
        }
    }

    Text {
        id: collectionNameText
        objectName: "timelineCollectionName"
        x: panel.width - 270
        y: 108
        width: 180
        horizontalAlignment: Text.AlignRight
        text: {
            var collection = hostWindow.collectionAt(hostWindow.currentIndex)
            return collection ? collection.name : ""
        }
        color: "#ffffff"
        font.pixelSize: 18
        font.bold: true
        style: Text.Outline
        styleColor: "#252525"
    }

    Text {
        id: collectionDateText
        objectName: "timelineCollectionDate"
        x: panel.width - 270
        y: 143
        width: 180
        horizontalAlignment: Text.AlignRight
        text: {
            var collection = hostWindow.collectionAt(hostWindow.currentIndex)
            return collection ? collection.dateLabel : ""
        }
        color: "#ffffff"
        font.pixelSize: 14
        style: Text.Outline
        styleColor: "#252525"
    }

    Rectangle {
        objectName: "timelineControlBar"
        x: 0
        y: 403
        width: panel.width
        height: 38
        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: Theme.dark ? Theme.chromeBg : "#efefef"
            }
            GradientStop {
                position: 0.45
                color: Theme.dark ? Theme.chromeBg : "#d6d6d6"
            }
            GradientStop {
                position: 1.0
                color: Theme.dark ? Theme.chromeBg : "#b8b8b8"
            }
        }
        border.color: Theme.dark ? Theme.chromeBorder : "#8d8d8d"
        border.width: 1
    }

    Button {
        id: timelineExitButton
        objectName: "timelineCloseButton"
        x: 9
        y: 405
        width: 40
        height: 29
        padding: 0
        background: Rectangle {
            radius: 4
            color: timelineExitButton.down
                ? (Theme.dark ? Theme.selectionBlue : "#bfc7d4")
                : Theme.buttonBg
            border.color: Theme.dark ? Theme.chromeBorder : "#777777"
        }
        contentItem: Canvas {
            id: timelineExitIcon
            onPaint: {
                var c = getContext("2d")
                c.strokeStyle = Theme.dark ? Theme.ink : "#142348"
                c.fillStyle = Theme.dark ? Theme.ink : "#142348"
                c.lineWidth = 1.5
                c.strokeRect(4, 8, 4, 4)
                c.strokeRect(10, 8, 4, 4)
                c.strokeRect(4, 14, 4, 4)
                c.strokeRect(10, 14, 4, 4)
                c.beginPath()
                c.moveTo(27, 14)
                c.lineTo(15, 14)
                c.lineTo(19, 10)
                c.moveTo(15, 14)
                c.lineTo(19, 18)
                c.stroke()
            }
            Component.onCompleted: requestPaint()
        }
        onClicked: hostWindow.closed()
    }

    Button {
        id: timelineLeftButton
        objectName: "timelineLeftButton"
        x: panel.width / 2 - 72
        y: 405
        width: 30
        height: 30
        padding: 0
        background: Rectangle {
            radius: 15
            color: timelineLeftButton.down
                ? (Theme.dark ? Theme.selectionBlue : "#bec6d2")
                : Theme.buttonBg
            border.color: Theme.dark ? Theme.chromeBorder : "#777777"
        }
        contentItem: Canvas {
            id: timelineLeftIcon
            onPaint: {
                var c = getContext("2d")
                c.fillStyle = Theme.dark ? Theme.ink : "#142348"
                c.beginPath()
                c.moveTo(7, height / 2)
                c.lineTo(17, 6)
                c.lineTo(17, height - 6)
                c.closePath()
                c.fill()
                c.fillRect(16, height / 2 - 1.5, 8, 3)
            }
            Component.onCompleted: requestPaint()
        }
        onClicked: hostWindow.step(-1)
    }

    Button {
        id: timelinePlayButton
        objectName: "timelinePlayButton"
        x: panel.width / 2 - 20
        y: 405
        width: 40
        height: 30
        padding: 0
        background: Rectangle {
            radius: 4
            color: timelinePlayButton.down
                ? (Theme.dark ? Theme.selectionBlue : "#bec6d2")
                : Theme.buttonBg
            border.color: Theme.dark ? Theme.chromeBorder : "#777777"
        }
        contentItem: Canvas {
            id: timelinePlayIcon
            onPaint: {
                var c = getContext("2d")
                c.fillStyle = Theme.dark ? Theme.ink : "#142348"
                c.strokeStyle = Theme.dark ? Theme.ink : "#142348"
                c.lineWidth = 1
                c.strokeRect(5, 8, 14, 14)
                c.beginPath()
                c.moveTo(7, 19)
                c.lineTo(11, 14)
                c.lineTo(14, 17)
                c.lineTo(16, 14)
                c.lineTo(18, 19)
                c.stroke()
                c.beginPath()
                c.moveTo(24, 8)
                c.lineTo(24, height - 8)
                c.lineTo(33, height / 2)
                c.closePath()
                c.fill()
            }
            Component.onCompleted: requestPaint()
        }
        onClicked: hostWindow.startCurrentSlideshow()
    }

    Button {
        id: timelineRightButton
        objectName: "timelineRightButton"
        x: panel.width / 2 + 40
        y: 405
        width: 30
        height: 30
        padding: 0
        background: Rectangle {
            radius: 15
            color: timelineRightButton.down
                ? (Theme.dark ? Theme.selectionBlue : "#bec6d2")
                : Theme.buttonBg
            border.color: Theme.dark ? Theme.chromeBorder : "#777777"
        }
        contentItem: Canvas {
            id: timelineRightIcon
            onPaint: {
                var c = getContext("2d")
                c.fillStyle = Theme.dark ? Theme.ink : "#142348"
                c.beginPath()
                c.moveTo(23, height / 2)
                c.lineTo(13, 6)
                c.lineTo(13, height - 6)
                c.closePath()
                c.fill()
                c.fillRect(6, height / 2 - 1.5, 8, 3)
            }
            Component.onCompleted: requestPaint()
        }
        onClicked: hostWindow.step(1)
    }

    Text {
        objectName: "timelineFirstDate"
        x: sliderArea.x - 110
        y: 456
        width: 100
        horizontalAlignment: Text.AlignRight
        text: {
            var collection = hostWindow.collectionAt(hostWindow.currentIndex)
            return collection ? collection.firstDateLabel : ""
        }
        color: Theme.dark ? Theme.ink : "#3b3b3b"
        font.pixelSize: 10
    }

    Item {
        id: sliderArea
        objectName: "timelineSliderArea"
        x: panel.width / 2 - width / 2
        y: 452
        width: 244
        height: 28

        Rectangle {
            objectName: "timelineSliderTrack"
            x: 0
            y: 14
            width: parent.width
            height: 1
            color: Theme.dark ? Theme.textGray : "#969696"
        }

        Repeater {
            id: dateDots
            objectName: "timelineDateDots"
            model: panel.dotsModel
            delegate: Rectangle {
                required property var modelData
                objectName: "timelineDateDot"
                x: modelData.x
                y: modelData.y
                width: 7
                height: 10
                radius: 4
                visible: modelData.draw
                color: Theme.dark ? Theme.ink : "#142348"
            }
        }

        Rectangle {
            objectName: "timelineSliderThumb"
            width: 18
            height: 18
            radius: 9
            y: 5
            x: (typeof timelineController !== "undefined" && timelineController)
                ? timelineController.sliderThumbX(
                      hostWindow.draggingSlider ? hostWindow.dragX
                          : sliderArea.x
                            + hostWindow.selectedSliderPosition() * sliderArea.width,
                      sliderArea.x, sliderArea.width, width)
                  - sliderArea.x
                : 0
            gradient: Gradient {
                GradientStop {
                    position: 0.0
                    color: Theme.dark ? Theme.shadeLight : "#ffffff"
                }
                GradientStop {
                    position: 1.0
                    color: Theme.dark ? Theme.chromeBorder : "#7f9997"
                }
            }
            border.color: Theme.dark ? Theme.chromeBorder : "#858585"
            border.width: 1
        }

        MouseArea {
            objectName: "timelineSliderMouseArea"
            anchors.fill: parent
            hoverEnabled: true
            onPressed: function(mouse) {
                hostWindow.draggingSlider = true
                hostWindow.updateSliderFromX(sliderArea.x + mouse.x)
            }
            onPositionChanged: function(mouse) {
                if (pressed)
                    hostWindow.updateSliderFromX(sliderArea.x + mouse.x)
            }
            onReleased: hostWindow.releaseSlider()
        }
    }

    Text {
        objectName: "timelineLastDate"
        x: sliderArea.x + sliderArea.width + 5
        y: 456
        width: 120
        horizontalAlignment: Text.AlignLeft
        text: {
            var collection = hostWindow.collectionAt(hostWindow.currentIndex)
            return collection ? collection.lastDateLabel : ""
        }
        color: Theme.dark ? Theme.ink : "#3b3b3b"
        font.pixelSize: 10
    }

    Connections {
        target: Theme
        function onDarkChanged() {
            timelineExitIcon.requestPaint()
            timelineLeftIcon.requestPaint()
            timelinePlayIcon.requestPaint()
            timelineRightIcon.requestPaint()
        }
    }
}
