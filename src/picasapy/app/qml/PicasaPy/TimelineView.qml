pragma ComponentBehavior: Bound

import QtQuick

// A Picasa Időrendje: fekete teljes képernyőn egy fix, középre tett kártya.
Rectangle {
    id: view
    objectName: "timelineView"
    color: "#000000"
    focus: visible

    property var collectionsModel: []
    property var dataController: null
    property int currentIndex: 0
    // A job-217 képkockán az első kártya gombja a sín 30,5%-án áll.
    readonly property real sliderStartFraction: 0.305
    readonly property var currentCollection:
        currentIndex >= 0 && currentIndex < collectionsModel.length
            ? collectionsModel[currentIndex] : null

    signal closed()
    signal slideshowRequested(int index)

    function step(delta) {
        if (collectionsModel.length < 1)
            return
        currentIndex = Math.max(0, Math.min(
            collectionsModel.length - 1, currentIndex + delta))
    }

    onVisibleChanged: {
        if (visible) {
            currentIndex = 0
            forceActiveFocus()
        }
    }

    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_Right) {
            view.step(1)
            event.accepted = true
        } else if (event.key === Qt.Key_Left) {
            view.step(-1)
            event.accepted = true
        } else if (event.key === Qt.Key_Space) {
            if (view.currentCollection && view.currentCollection.count > 0)
                view.slideshowRequested(view.currentIndex)
            event.accepted = true
        } else if (event.key === Qt.Key_Escape) {
            view.closed()
            event.accepted = true
        }
    }

    Rectangle {
        id: panel
        objectName: "timelinePresentationPanel"
        width: 600
        height: 480
        anchors.centerIn: parent
        clip: true
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#909297" }
            GradientStop { position: 0.55; color: "#8d8f93" }
            GradientStop { position: 1.0; color: "#85868a" }
        }

        Canvas {
            objectName: "timelineBackgroundCurve"
            x: 0
            y: 0
            width: parent.width
            height: 400
            onPaint: {
                var context = getContext("2d")
                context.clearRect(0, 0, width, height)

                var ellipse = context.createLinearGradient(80, 0, 530, 300)
                ellipse.addColorStop(0, "#626a77")
                ellipse.addColorStop(0.55, "#737b89")
                ellipse.addColorStop(1, "#7c828c")
                context.fillStyle = ellipse
                context.beginPath()
                context.moveTo(174, 0)
                context.bezierCurveTo(98, 51, 55, 111, 64, 174)
                context.bezierCurveTo(75, 256, 174, 302, 306, 314)
                context.bezierCurveTo(420, 324, 535, 316, 600, 292)
                context.lineTo(600, 0)
                context.closePath()
                context.fill()

                context.globalAlpha = 0.38
                context.strokeStyle = "#e0dfdc"
                context.lineWidth = 8
                context.beginPath()
                context.moveTo(20, 141)
                context.bezierCurveTo(0, 222, 73, 291, 258, 333)
                context.stroke()
                context.globalAlpha = 1
            }
        }

        Text {
            objectName: "timelineCollectionName"
            x: 236
            y: 108
            width: 274
            height: 25
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            text: view.currentCollection ? view.currentCollection.name : ""
            color: "#ffffff"
            font.pixelSize: 19
            font.bold: true
        }
        Text {
            objectName: "timelineCollectionDate"
            x: 236
            y: 140
            width: 274
            height: 20
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            text: view.currentCollection ? view.currentCollection.date : ""
            color: "#f4f4f4"
            font.pixelSize: 14
        }

        Repeater {
            objectName: "timelineDottedArc"
            model: 14
            delegate: Rectangle {
                required property int index
                width: 5
                height: 5
                radius: 2.5
                color: "#07133f"
                x: 498 - index * (94 / 13)
                y: 183 + index * (89 / 13)
                    + Math.sin(index / 13 * Math.PI) * 10
            }
        }

        Item {
            id: thumbStack
            objectName: "timelineThumbStack"
            x: 354
            y: 306
            width: 186
            height: 92
            Repeater {
                model: view.currentCollection
                    ? Math.min(view.currentCollection.photos.length, 3) : 0
                delegate: Rectangle {
                    required property int index
                    width: 74
                    height: 84
                    x: 7 + index * 91
                    y: 4 + (index % 2) * 3
                    z: index
                    rotation: index % 2 === 0 ? -3 : 3
                    color: "#f2f2f2"
                    border.width: 1
                    border.color: "#717174"
                    Image {
                        anchors.fill: parent
                        anchors.margins: 4
                        source: view.currentCollection.photos[index].thumbUrl
                        fillMode: Image.PreserveAspectFit
                        asynchronous: Qt.platform.pluginName !== "offscreen"
                        cache: true
                        smooth: true
                        mipmap: true
                    }
                }
            }
        }

        Rectangle {
            x: 0
            y: 439
            width: parent.width
            height: 41
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#c3c3c5" }
                GradientStop { position: 1.0; color: "#b1b1b3" }
            }
        }

        Rectangle {
            x: 0
            y: 402
            width: parent.width
            height: 37
            z: 5
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#dedede" }
                GradientStop { position: 0.2; color: "#cbcbcd" }
                GradientStop { position: 1.0; color: "#aaaaac" }
            }
            border.width: 1
            border.color: "#b0b1b4"

            Item {
                objectName: "timelineListIcon"
                x: 9
                y: 3
                width: 42
                height: 27
                Rectangle {
                    anchors.fill: parent
                    radius: 5
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#ffffff" }
                        GradientStop { position: 1.0; color: "#d7d7d9" }
                    }
                    border.width: 1
                    border.color: "#8d8e91"
                }
                Canvas {
                    anchors.fill: parent
                    onPaint: {
                        var context = getContext("2d")
                        context.clearRect(0, 0, width, height)
                        context.fillStyle = "#142657"
                        context.fillRect(6, 7, 4, 4)
                        context.fillRect(6, 14, 4, 4)
                        context.fillRect(6, 21, 4, 3)
                        context.fillRect(12, 7, 6, 2)
                        context.fillRect(12, 15, 6, 2)
                        context.fillRect(12, 22, 6, 2)
                        context.beginPath()
                        context.moveTo(34, 6)
                        context.lineTo(26, 13.5)
                        context.lineTo(34, 21)
                        context.closePath()
                        context.fill()
                        context.fillRect(32, 12, 7, 3)
                    }
                }
            }
            Item {
                objectName: "timelinePreviousIcon"
                x: 229
                y: 2
                width: 30
                height: 30
                Rectangle {
                    anchors.fill: parent
                    radius: 15
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#ffffff" }
                        GradientStop { position: 1.0; color: "#d4d5d7" }
                    }
                    border.width: 1
                    border.color: "#a3a4a7"
                }
                Canvas {
                    anchors.fill: parent
                    onPaint: {
                        var context = getContext("2d")
                        context.clearRect(0, 0, width, height)
                        context.fillStyle = "#142657"
                        context.beginPath()
                        context.moveTo(9, 15)
                        context.lineTo(19, 7)
                        context.lineTo(19, 23)
                        context.closePath()
                        context.fill()
                        context.fillRect(18, 13, 6, 4)
                    }
                }
            }
            Item {
                objectName: "timelinePlayIcon"
                x: 280
                y: 3
                width: 42
                height: 28
                Rectangle {
                    anchors.fill: parent
                    radius: 5
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#ffffff" }
                        GradientStop { position: 1.0; color: "#d3d4d6" }
                    }
                    border.width: 1
                    border.color: "#a0a1a4"
                }
                Canvas {
                    anchors.fill: parent
                    onPaint: {
                        var context = getContext("2d")
                        context.clearRect(0, 0, width, height)
                        context.fillStyle = "#142657"
                        context.fillRect(9, 8, 12, 11)
                        context.fillStyle = "#f7f7f7"
                        context.fillRect(11, 10, 8, 7)
                        context.fillStyle = "#142657"
                        context.beginPath()
                        context.moveTo(27, 6)
                        context.lineTo(36, 14)
                        context.lineTo(27, 22)
                        context.closePath()
                        context.fill()
                    }
                }
            }
            Item {
                objectName: "timelineNextIcon"
                x: 344
                y: 2
                width: 30
                height: 30
                Rectangle {
                    anchors.fill: parent
                    radius: 15
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#ffffff" }
                        GradientStop { position: 1.0; color: "#d4d5d7" }
                    }
                    border.width: 1
                    border.color: "#a3a4a7"
                }
                Canvas {
                    anchors.fill: parent
                    onPaint: {
                        var context = getContext("2d")
                        context.clearRect(0, 0, width, height)
                        context.fillStyle = "#142657"
                        context.beginPath()
                        context.moveTo(21, 15)
                        context.lineTo(11, 7)
                        context.lineTo(11, 23)
                        context.closePath()
                        context.fill()
                        context.fillRect(6, 13, 6, 4)
                    }
                }
            }
        }

        Rectangle {
            objectName: "timelineDateSliderTrack"
            x: 184
            y: 465
            width: 246
            height: 2
            color: "#7b7c80"
        }
        Rectangle {
            objectName: "timelineDateSliderHandle"
            width: 17
            height: 17
            radius: 8.5
            y: 457
            x: 184 + (246 - width) * (view.collectionsModel.length > 1
                ? view.sliderStartFraction
                    + (1 - view.sliderStartFraction) * view.currentIndex
                        / (view.collectionsModel.length - 1)
                : view.sliderStartFraction)
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#ffffff" }
                GradientStop { position: 0.65; color: "#d3e0df" }
                GradientStop { position: 1.0; color: "#8a9899" }
            }
            border.width: 1
            border.color: "#a1a5a7"
        }
        Text {
            objectName: "timelineDateRangeStart"
            x: 114
            y: 452
            width: 100
            height: 22
            text: view.dataController
                ? view.dataController.dateRangeStartLabel : ""
            color: "#66676a"
            font.pixelSize: 11
            elide: Text.ElideRight
        }
        Text {
            objectName: "timelineDateRangeEnd"
            x: 420
            y: 452
            width: 90
            height: 22
            horizontalAlignment: Text.AlignRight
            text: view.dataController
                ? view.dataController.dateRangeEndLabel : ""
            color: "#66676a"
            font.pixelSize: 11
            elide: Text.ElideLeft
        }
    }
}
