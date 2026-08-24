import QtQuick

// A Picasa visszafejtett belső hisztogram-bittérképe (#864): pontosan
// 256 × 70 képpont, binenként egy oszlop. Az SVG csak alap téglalapokat
// használ (a Qt SVG Tiny motorja ezeket megbízhatóan támogatja), és egyetlen
// Image scene-graph csomóponttá raszterizálódik. Nincs Canvas/requestPaint
// időzítés (#232), és nincs több száz élő Rectangle sem.
Image {
    id: bitmap
    objectName: "histogramBitmap"
    width: 256
    height: 70
    sourceSize: Qt.size(256, 70)
    fillMode: Image.Stretch
    smooth: false
    asynchronous: false
    cache: false

    property var histogramData: ({ r: [], g: [], b: [] })

    function pixelHeight(values, index) {
        if (!values || index >= values.length)
            return 0
        return Math.max(0, Math.min(70, Math.round(Number(values[index]) * 70)))
    }

    function maskAbove(red, green, blue, level) {
        return (red > level ? 1 : 0)
             | (green > level ? 2 : 0)
             | (blue > level ? 4 : 0)
    }

    function additiveFill(mask) {
        switch (mask) {
        case 1: return "#ff0000"
        case 2: return "#00ff00"
        case 3: return "#808000"
        case 4: return "#0000ff"
        case 5: return "#800080"
        case 6: return "#008080"
        case 7: return "#555555"
        default: return "#000000"
        }
    }

    function additiveOpacity(mask) {
        var count = ((mask & 1) ? 1 : 0)
                  + ((mask & 2) ? 1 : 0)
                  + ((mask & 4) ? 1 : 0)
        return count / 3
    }

    function segment(x, lower, upper, mask) {
        if (upper <= lower || mask === 0)
            return ""
        return "<rect x='" + x + "' y='" + (70 - upper)
             + "' width='1' height='" + (upper - lower)
             + "' fill='" + additiveFill(mask)
             + "' fill-opacity='" + additiveOpacity(mask) + "'/>"
    }

    function makeSvg(data) {
        var svg = "<svg xmlns='http://www.w3.org/2000/svg' width='256' "
                + "height='70' viewBox='0 0 256 70'>"
        var redValues = data && data.r ? data.r : []
        var greenValues = data && data.g ? data.g : []
        var blueValues = data && data.b ? data.b : []
        for (var x = 0; x < 256; ++x) {
            var red = pixelHeight(redValues, x)
            var green = pixelHeight(greenValues, x)
            var blue = pixelHeight(blueValues, x)
            var first = Math.min(red, green, blue)
            var third = Math.max(red, green, blue)
            var second = red + green + blue - first - third
            svg += segment(x, 0, first, maskAbove(red, green, blue, 0))
            svg += segment(x, first, second,
                           maskAbove(red, green, blue, first))
            svg += segment(x, second, third,
                           maskAbove(red, green, blue, second))
        }
        return "data:image/svg+xml," + encodeURIComponent(svg + "</svg>")
    }

    source: makeSvg(histogramData)
}
