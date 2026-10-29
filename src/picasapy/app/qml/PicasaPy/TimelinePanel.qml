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
    clip: true

    readonly property var dotsModel: (typeof timelineController !== "undefined" && timelineController)
        ? timelineController.dotPositions(
              hostWindow.sliderValues(), 0, Math.max(0, sliderArea.width - 4), 7,
              28, 0, 10)
        : []
    readonly property bool currentCardsLoaded: {
        if (currentDeck.count === 0)
            return false
        for (var i = 0; i < currentDeck.count; ++i) {
            if (!currentDeck.itemAt(i).imageLoaded)
                return false
        }
        for (var j = 0; j < nextDeck.count; ++j) {
            if (!nextDeck.itemAt(j).imageLoaded)
                return false
        }
        return true
    }
    readonly property var currentPhotoCardGeometry: {
        var geometry = []
        for (var i = 0; i < currentDeck.count; ++i) {
            var card = currentDeck.itemAt(i)
            if (card) {
                geometry.push({
                    x: card.x,
                    y: card.y,
                    width: card.width,
                    height: card.height,
                    rotation: card.rotation
                })
            }
        }
        return geometry
    }

    readonly property real sliderAreaX: sliderArea.x
    readonly property real sliderAreaWidth: sliderArea.width

    Rectangle {
        anchors.fill: parent
        // A job-217 képkockán a panel alapja szürke; a fotók a kötegben
        // jelennek meg, nem teljes felületű háttérképként. Világoson a
        // mért alap marad, sötét témán a panel tokenje veszi át a helyét.
        color: Theme.dark ? Theme.panelBg : "#8a888b"
    }

    Canvas {
        id: cardArtwork
        objectName: "timelineCardArtwork"
        width: panel.width
        height: 400
        readonly property var dotArcPoints: {
            var values = hostWindow.sliderValues()
            var firstPhoto = currentDeck.count > 0
                ? currentDeck.itemAt(0) : null
            if (!(typeof timelineController !== "undefined" && timelineController) || values.length === 0 || !firstPhoto)
                return []

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

            context.beginPath()
            context.moveTo(178, 0)
            context.bezierCurveTo(108, 39, 48, 99, 63, 171)
            context.bezierCurveTo(78, 253, 204, 297, 600, 330)
            context.lineTo(600, 0)
            context.closePath()
            context.fillStyle = "#6b6f7d"
            context.fill()

            context.beginPath()
            context.moveTo(16, 150)
            context.bezierCurveTo(8, 228, 73, 302, 245, 359)
            context.strokeStyle = "rgba(255,255,255,0.22)"
            context.lineWidth = 8
            context.stroke()

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
        target: currentDeck
        function onCountChanged() { cardArtwork.requestPaint() }
    }

    // A jelenlegi gyűjtemény lapjai a mért görbe 0.94 paraméterén
    // fedik egymást; a sorozat egy csoport bélyegkötege.
    Repeater {
        id: currentDeck
        objectName: "timelineCurrentPhotoDeck"
        model: {
            var collection = hostWindow.collectionAt(hostWindow.currentIndex)
            return collection && collection.photos
                ? Math.min(4, collection.photos.length) : 0
        }
        delegate: Item {
            id: currentPhotoCard
            objectName: "timelinePhotoCard" + index
            required property int index
            property var photo: hostWindow.photoAt(hostWindow.currentIndex, index)
            property real curveParameter: 0.94
            property var curve: (typeof timelineController !== "undefined" && timelineController)
                ? timelineController.bezierAt(curveParameter)
                : ({ x: 0.5, y: 0.7, z: 1 })
            width: 82 * curve.z
            height: 90 * curve.z
            x: curve.x * panel.width - width / 2
               + index * 4
               + (hostWindow.frameTransforms.current.tx - 1) * panel.width
            y: curve.y * panel.height - height / 2
               - index * 3
               + (hostWindow.frameTransforms.current.ty - 1) * panel.height
            z: index
            rotation: index % 2 === 0 ? -7 : 5
            scale: hostWindow.frameTransforms.current.scale
            opacity: hostWindow.currentLayerOpacity
            readonly property bool imageLoaded: cardImage.status === Image.Ready

            Rectangle {
                objectName: "timelinePhotoShadow" + currentPhotoCard.index
                x: 4
                y: 5
                width: parent.width
                height: parent.height
                radius: 2
                color: "#55000000"
            }

            Rectangle {
                anchors.fill: parent
                color: "#eeeeee"
                border.width: 1
                border.color: "#555555"
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 3
                    color: "#777777"
                    Image {
                        id: cardImage
                        objectName: "timelinePhotoImage" + currentPhotoCard.index
                        anchors.fill: parent
                        source: currentPhotoCard.photo
                            ? currentPhotoCard.photo.thumbUrl : ""
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        smooth: true
                        mipmap: true
                    }
                }
            }
        }
    }

    Repeater {
        id: nextDeck
        objectName: "timelineNextPhotoDeck"
        model: {
            var collection = hostWindow.collectionAt(hostWindow.currentIndex + 1)
            return collection && collection.photos
                ? Math.min(4, collection.photos.length) : 0
        }
        delegate: Item {
            id: nextPhotoCard
            objectName: "timelineNextPhotoCard" + index
            required property int index
            property var photo: hostWindow.photoAt(hostWindow.currentIndex + 1, index)
            property real curveParameter: 1.0
            property var curve: (typeof timelineController !== "undefined" && timelineController)
                ? timelineController.bezierAt(curveParameter)
                : ({ x: 0.5, y: 0.7, z: 1 })
            width: 82 * curve.z
            height: 90 * curve.z
            x: curve.x * panel.width - width / 2 + index * 4
            y: curve.y * panel.height - height / 2 - index * 3
            z: index
            rotation: index % 2 === 0 ? -7 : 5
            readonly property bool imageLoaded: nextCardImage.status === Image.Ready

            Rectangle {
                x: 4
                y: 5
                width: parent.width
                height: parent.height
                radius: 2
                color: "#55000000"
            }

            Rectangle {
                anchors.fill: parent
                color: "#eeeeee"
                border.width: 1
                border.color: "#555555"
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 3
                    color: "#777777"
                    Image {
                        id: nextCardImage
                        anchors.fill: parent
                        source: nextPhotoCard.photo
                            ? nextPhotoCard.photo.thumbUrl : ""
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        smooth: true
                        mipmap: true
                    }
                }
            }
        }
    }

    Repeater {
        id: previousDeck
        objectName: "timelinePreviousPhotoDeck"
        model: {
            var collection = hostWindow.collectionAt(hostWindow.previousIndex)
            return hostWindow.previousIndex !== hostWindow.currentIndex
                    && collection && collection.photos
                ? Math.min(4, collection.photos.length) : 0
        }
        delegate: Item {
            id: previousPhotoCard
            required property int index
            property var photo: hostWindow.photoAt(hostWindow.previousIndex, index)
            property real curveParameter: 0.94
            property var curve: (typeof timelineController !== "undefined" && timelineController)
                ? timelineController.bezierAt(curveParameter)
                : ({ x: 0.5, y: 0.7, z: 1 })
            width: 82 * curve.z
            height: 90 * curve.z
            x: curve.x * panel.width - width / 2
               + index * 4
               + (hostWindow.frameTransforms.previous.tx - 1) * panel.width
            y: curve.y * panel.height - height / 2
               - index * 3
               + (hostWindow.frameTransforms.previous.ty - 1) * panel.height
            z: index
            rotation: index % 2 === 0 ? -7 : 5
            scale: hostWindow.frameTransforms.previous.scale
            opacity: hostWindow.previousLayerOpacity

            Rectangle {
                x: 4
                y: 5
                width: parent.width
                height: parent.height
                radius: 2
                color: "#55000000"
            }

            Rectangle {
                anchors.fill: parent
                color: "#eeeeee"
                border.width: 1
                border.color: "#555555"
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 3
                    color: "#777777"
                    Image {
                        anchors.fill: parent
                        source: previousPhotoCard.photo
                            ? previousPhotoCard.photo.thumbUrl : ""
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        smooth: true
                        mipmap: true
                    }
                }
            }
        }
    }

    Text {
        id: collectionNameText
        objectName: "timelineCollectionName"
        x: 330
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
        x: 330
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
        x: 228
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
        x: 280
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
        x: 340
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
        x: 78
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
        x: 188
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
        x: 437
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
