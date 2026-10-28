import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

    Item {
        id: quickViewerToolbar
        property var hostViewer: null
        readonly property var viewer: hostViewer
        objectName: "viewerQuickToolbar"
        anchors.fill: parent
        visible: viewer.quickViewerMode
        z: 100

        PicasaButton {
            objectName: "viewerQuickZoomInButton"
            x: (parent.width - 1024) / 2 + 253
            y: parent.height - 800 + 744
            width: 29; height: 19
            padding: 0
            text: "+"
            autoRepeat: true
            ToolTip.text: qsTr("Zoom In")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.lepjZoom(0.05)
        }
        PicasaButton {
            objectName: "viewerQuickZoomOutButton"
            x: (parent.width - 1024) / 2 + 283
            y: parent.height - 800 + 744
            width: 28; height: 19
            padding: 0
            text: "−"
            autoRepeat: true
            ToolTip.text: qsTr("Zoom Out")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.lepjZoom(-0.05)
        }
        PicasaButton {
            objectName: "viewerQuickZoomActualButton"
            x: (parent.width - 1024) / 2 + 312
            y: parent.height - 800 + 744
            width: 28; height: 19
            padding: 0
            text: "1:1"
            ToolTip.text: qsTr("Zoom to 1:1")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.zoomActual()
        }
        PicasaButton {
            objectName: "viewerQuickLaunchPicasaButton"
            x: (parent.width - 1024) / 2 + 351
            y: parent.height - 800 + 744
            width: 119; height: 19
            leftPadding: 30
            text: qsTr("Edit in PicasaPy")
            ToolTip.text: qsTr("Launch PicasaPy")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.kerBezaras()
            Image {
                source: "icons/viewer-back-arrow.svg"
                width: 17; height: 15
                sourceSize.width: 17; sourceSize.height: 15
                anchors.left: parent.left
                anchors.leftMargin: 7
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        PicasaButton {
            objectName: "viewerQuickPrevButton"
            x: (parent.width - 1024) / 2 + 473
            y: parent.height - 800 + 739
            width: 29; height: 30
            padding: 0
            background: null
            autoRepeat: true
            enabled: viewer.hasPrevious()
            onClicked: viewer.previous()
            ToolTip.text: qsTr("Previous Photo")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            contentItem: Image {
                source: "icons/viewer-step-left.svg"
                width: 30; height: 31
                sourceSize.width: 30; sourceSize.height: 31
                anchors.centerIn: parent
            }
        }
        PicasaButton {
            objectName: "viewerQuickPlayButton"
            x: (parent.width - 1024) / 2 + 494
            y: parent.height - 800 + 733
            width: 39; height: 35
            padding: 0
            background: null
            text: "▶"
            Accessible.name: qsTr("Play Slideshow")
            ToolTip.text: qsTr("Play Slideshow")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.playRequested()
        }
        PicasaButton {
            objectName: "viewerQuickNextButton"
            x: (parent.width - 1024) / 2 + 523
            y: parent.height - 800 + 738
            width: 28; height: 30
            padding: 0
            background: null
            autoRepeat: true
            enabled: viewer.hasNext()
            onClicked: viewer.next()
            ToolTip.text: qsTr("Next Photo")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            contentItem: Image {
                source: "icons/viewer-step-right.svg"
                width: 30; height: 31
                sourceSize.width: 30; sourceSize.height: 31
                anchors.centerIn: parent
            }
        }
        PicasaButton {
            objectName: "viewerQuickUploadButton"
            x: (parent.width - 1024) / 2 + 555
            y: parent.height - 800 + 744
            width: 76; height: 19
            padding: 0
            enabled: viewer.quickUploadAvailable
            Accessible.name: qsTr("Quick Upload")
            ToolTip.text: qsTr("Quick Upload")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            contentItem: Image {
                source: "icons/upload.svg"
                width: 17; height: 17
                sourceSize.width: 17; sourceSize.height: 17
                fillMode: Image.PreserveAspectFit
            }
        }
        PicasaButton {
            objectName: "viewerQuickRotateLeftButton"
            x: (parent.width - 1024) / 2 + 639
            y: parent.height - 800 + 744
            width: 28; height: 19
            padding: 0
            ToolTip.text: qsTr("Rotate counter-clockwise")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.rotateRequested(viewer._kijeloltSort(), -1)
            contentItem: Image {
                source: "icons/tray-rotate-left.svg"
                width: 15; height: 17
                sourceSize.width: 15; sourceSize.height: 17
                fillMode: Image.PreserveAspectFit
            }
        }
        PicasaButton {
            objectName: "viewerQuickRotateRightButton"
            x: (parent.width - 1024) / 2 + 668
            y: parent.height - 800 + 744
            width: 28; height: 19
            padding: 0
            ToolTip.text: qsTr("Rotate clockwise")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.rotateRequested(viewer._kijeloltSort(), 1)
            contentItem: Image {
                source: "icons/tray-rotate-right.svg"
                width: 15; height: 17
                sourceSize.width: 15; sourceSize.height: 17
                fillMode: Image.PreserveAspectFit
            }
        }
        PicasaButton {
            objectName: "viewerQuickStarButton"
            x: (parent.width - 1024) / 2 + 702
            y: parent.height - 800 + 744
            width: 28; height: 19
            padding: 0
            ToolTip.text: qsTr("Star")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.starRequested(viewer._kijeloltSort())
            contentItem: Image {
                source: viewer.photosModel && viewer.currentIndex >= 0
                    ? (viewer.photosModel.revision,
                       viewer.photosModel.starAt(viewer.currentIndex)
                         ? "icons/tray-star-on.svg"
                         : "icons/tray-star.svg")
                    : "icons/tray-star.svg"
                width: 17; height: 17
                sourceSize.width: 17; sourceSize.height: 17
                fillMode: Image.PreserveAspectFit
            }
        }
        PicasaButton {
            id: quickViewerMoreOptionsButton
            objectName: "viewerQuickMoreOptionsButton"
            x: (parent.width - 1024) / 2 + 737
            y: parent.height - 800 + 743
            width: 34; height: 21
            padding: 0
            Accessible.name: qsTr("More Options")
            ToolTip.text: qsTr("Click to see more options")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: {
                var point = quickViewerMoreOptionsButton.mapToItem(
                    viewer, 0, quickViewerMoreOptionsButton.height)
                viewer.openContextMenu(point.x, point.y)
            }
            contentItem: Image {
                source: "icons/tray-more.svg"
                width: 16; height: 16
                sourceSize.width: 16; sourceSize.height: 16
                fillMode: Image.PreserveAspectFit
            }
        }
    }
