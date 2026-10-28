import QtQuick
import QtQuick.Window

Window {
    id: hoverPreviewWindow
    required property var feed
    readonly property var ctl: controller
    objectName: "ctrlAltHoverPreviewWindow"
    transientParent: feed.appWindow
    flags: Qt.ToolTip | Qt.WindowDoesNotAcceptFocus
            | Qt.WindowTransparentForInput
    modality: Qt.NonModal
    color: Theme.lightboxBg
    // A gyerekablak kliensszélességét a fő tartalomnézet adja; a spec
    // GetClientRect(child HWND).right értékének ez a QML-párja.
    readonly property real clientWidth: feed.width

    readonly property var photoSize: {
        const dimensions = (feed.currentPreviewPhoto.resolution || "")
            .split("x")
        return {
            width: Number(dimensions[0]) || 0,
            height: Number(dimensions[1]) || 0
        }
    }
    readonly property real imageScale: {
        if (photoSize.width <= 0 || photoSize.height <= 0) return 0
        return Math.min(1, 1200 / photoSize.width, 760 / photoSize.height)
    }
    readonly property int previewWidth: Math.round(
        photoSize.width * imageScale)
    readonly property int previewHeight: Math.round(
        photoSize.height * imageScale)
    readonly property int previewImageStatus: previewImage.status
    readonly property bool requested: feed.appWindow.active
        && ctl
        && ctl.enableHover !== undefined
        && ctl.enableHover === true
        && ctl.ctrlAltHeld === true
        && feed.currentPreviewRow >= 0
        && feed.currentPreviewPhoto.isVideo !== true
        && previewWidth > 0 && previewHeight > 0

    width: previewWidth + 24
    height: previewHeight + 24
    x: Math.round(feed.appWindow.x + (feed.appWindow.width - width) / 2)
    y: Math.round(feed.appWindow.y + (feed.appWindow.height - height) / 2)
    visible: requested && clientWidth > 1024
             && previewImage.status === Image.Ready

    Rectangle {
        anchors.fill: parent
        color: Theme.thumbCard
        border.color: Theme.thumbBorder
        border.width: 1

        Image {
            id: previewImage
            objectName: "ctrlAltHoverPreviewImage"
            anchors.fill: parent
            anchors.margins: 12
            source: hoverPreviewWindow.requested
                   && hoverPreviewWindow.clientWidth > 1024
                   ? feed.currentPreviewSource : ""
            sourceSize.width: hoverPreviewWindow.previewWidth
            sourceSize.height: hoverPreviewWindow.previewHeight
            fillMode: Image.PreserveAspectFit
            asynchronous: Qt.platform.pluginName !== "offscreen"
            cache: true
        }
    }
}
