import QtQuick

// RGB-hisztogram + fényképezőgép-adat doboz (#25): a néző bal alsó,
// korábban placeholder dobozának élesítése, Picasa-mintára. Buta komponens
// — a hisztogramot és az EXIF-sort kívülről kapja (EditController.histogram
// / cameraSummary, ld. edit_controller.py).
Rectangle {
    id: box
    objectName: "histogramBox"

    // {r: [0..1 érték * 256 vödör], g: [...], b: [...]} — histogram_helper.py
    property var histogramData: ({ r: [], g: [], b: [] })
    property string cameraSummary: ""

    color: "#f2f2f0"
    border.color: Theme.chromeBorder

    // csúszka-húzás közben a histogramData gyakran (minden mozzanatra)
    // változhat — a Canvas újrarajzolását rövid debounce-szal ritkítjuk,
    // hogy az élő frissítés ne akaszthassa a GUI-t (#25)
    onHistogramDataChanged: redrawTimer.restart()

    Timer {
        id: redrawTimer
        interval: 120
        onTriggered: histCanvas.requestPaint()
    }

    Column {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 4

        Canvas {
            id: histCanvas
            objectName: "histogramCanvas"
            width: parent.width
            height: parent.height - cameraLabel.implicitHeight - 4

            readonly property var channels: [
                { key: "r", color: "rgba(224, 74, 63, 0.8)" },
                { key: "g", color: "rgba(13, 171, 98, 0.8)" },
                { key: "b", color: "rgba(68, 138, 253, 0.8)" }
            ]

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.clearRect(0, 0, width, height)
                for (var c = 0; c < channels.length; c++) {
                    var values = box.histogramData
                                 ? box.histogramData[channels[c].key] : null
                    if (!values || values.length === 0) continue
                    ctx.strokeStyle = channels[c].color
                    ctx.lineWidth = 1
                    ctx.beginPath()
                    var stepX = width / values.length
                    for (var i = 0; i < values.length; i++) {
                        var x = i * stepX
                        var y = height - values[i] * height
                        if (i === 0) ctx.moveTo(x, y)
                        else ctx.lineTo(x, y)
                    }
                    ctx.stroke()
                }
            }
        }

        Text {
            id: cameraLabel
            objectName: "cameraSummaryText"
            width: parent.width
            text: box.cameraSummary.length > 0
                  ? box.cameraSummary
                  : qsTr("No camera information available")
            elide: Text.ElideRight
            font.pixelSize: Theme.fontSize - 2
            font.italic: box.cameraSummary.length === 0
            color: Theme.textGray
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
