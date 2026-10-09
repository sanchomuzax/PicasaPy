import QtQuick

// A filmkészítő előnézetének egy képkockája: fénykép vagy szöveges dia.
Item {
    id: frame
    clip: true

    property var photoSources: []
    property var slides: []
    property int itemIndex: -1
    property real aspectRatio: 4 / 3
    property real outputHeight: 480
    property bool actualSizeEnabled: false
    property string imageObjectName: "moviePreviewImage"
    signal imageSizeChanged(int width, int height)

    readonly property bool isTextSlide:
        itemIndex >= photoSources.length
        && itemIndex - photoSources.length >= 0
        && itemIndex - photoSources.length < slides.length
    readonly property bool isPhoto:
        itemIndex >= 0 && itemIndex < photoSources.length
    readonly property var slideData: isTextSlide
        ? slides[itemIndex - photoSources.length] : ({})
    readonly property string displayText:
        isTextSlide ? String(slideData.text || "") : ""
    readonly property string imageSource:
        isPhoto ? String(photoSources[itemIndex]) : ""
    readonly property int imageSourceWidth: previewImage.sourceSize.width
    readonly property int imageSourceHeight: previewImage.sourceSize.height
    readonly property int styleIndex:
        isTextSlide ? Number(slideData.style || 0) : 0
    readonly property bool hasBand: [4, 5, 6, 7].indexOf(styleIndex) >= 0

    Rectangle {
        objectName: frame.objectName + "/canvas"
        id: canvas
        width: frame.isTextSlide
            ? Math.min(frame.width, frame.height * frame.aspectRatio)
            : frame.width
        height: frame.isTextSlide && frame.aspectRatio > 0
            ? width / frame.aspectRatio : frame.height
        anchors.centerIn: parent
        clip: true
        color: frame.isTextSlide
            ? String(frame.slideData.backgroundColor || "#000000")
            : "transparent"

        Image {
            id: previewImage
            objectName: frame.imageObjectName
            visible: frame.isPhoto
            anchors.centerIn: parent
            width: frame.actualSizeEnabled && sourceSize.width > 0
                ? sourceSize.width : parent.width
            height: frame.actualSizeEnabled && sourceSize.height > 0
                ? sourceSize.height : parent.height
            source: frame.imageSource
            fillMode: Image.PreserveAspectFit
            cache: false
            onSourceSizeChanged: frame.imageSizeChanged(
                sourceSize.width, sourceSize.height
            )
        }

        Rectangle {
            objectName: "moviePreviewTextStyleBand"
            visible: frame.isTextSlide && frame.hasBand
            x: 0
            y: previewText.y - 5
            width: parent.width
            height: previewText.height + 10
            color: [4, 6].indexOf(frame.styleIndex) >= 0
                ? "#b4000000" : "#b4ffffff"
        }

        Text {
            id: previewText
            objectName: "moviePreviewText"
            visible: frame.isTextSlide
            x: 8
            width: parent.width - 16
            text: frame.displayText
            y: [2, 3, 11].indexOf(frame.styleIndex) >= 0
                ? parent.height - height - 6
                : (parent.height - height) / 2
            wrapMode: Text.WordWrap
            horizontalAlignment: frame.styleIndex === 9
                ? Text.AlignLeft
                : frame.styleIndex === 10 ? Text.AlignRight : Text.AlignHCenter
            color: [4, 6].indexOf(frame.styleIndex) >= 0
                ? "#ffffff"
                : [5, 7].indexOf(frame.styleIndex) >= 0
                    ? "#000000"
                    : String(frame.slideData.textColor || "#ffffff")
            font.family: String(frame.slideData.font || "DejaVu Sans")
            font.pixelSize: Math.max(
                1,
                Number(frame.slideData.size || 16) * parent.height
                    / Math.max(1, frame.outputHeight)
            )
            font.weight: frame.slideData.bold ? Font.Bold : Font.Normal
            font.italic: !!frame.slideData.italic
            style: frame.slideData.outline
                    || [3, 11].indexOf(frame.styleIndex) >= 0
                ? Text.Outline : Text.Normal
            styleColor: color === "#000000" ? "#ffffff" : "#000000"
        }
    }
}
