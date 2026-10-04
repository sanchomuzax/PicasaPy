import QtQuick
import QtQuick.Window
import QtMultimedia

// A videó kirajzolási területe. Normál módban kitölti a rendelkezésre álló
// helyet; 1:1 módban a képkocka természetes méretét tartja meg, középre
// igazítja, és a nézőterületen kívül levágja.
Item {
    id: viewport

    property bool actualSizeEnabled: false
    property alias videoOutput: output
    readonly property size videoSize: output.videoSink.videoSize
    readonly property real displayPixelRatio: {
        var hostWindow = viewport.Window.window
        return hostWindow && hostWindow.devicePixelRatio > 0
               ? hostWindow.devicePixelRatio : 1
    }

    clip: true

    VideoOutput {
        id: output
        objectName: "videoOutput"
        anchors.centerIn: parent
        width: viewport.actualSizeEnabled && viewport.videoSize.width > 0
               ? viewport.videoSize.width / viewport.displayPixelRatio
               : viewport.width
        height: viewport.actualSizeEnabled && viewport.videoSize.height > 0
                ? viewport.videoSize.height / viewport.displayPixelRatio
                : viewport.height
        fillMode: VideoOutput.PreserveAspectFit
    }
}
