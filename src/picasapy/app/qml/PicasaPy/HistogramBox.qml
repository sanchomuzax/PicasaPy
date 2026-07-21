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

    // #228 GYÖKÉROK: a doboz a nézőben MINDIG a rejtett (visible: false)
    // állapotból indul — ilyenkor a PhotoViewer onVisibleChanged ága
    // egy üres endEdit()-hisztogrammal FUT LE MÁR AZ ALKALMAZÁS INDÍTÁSAKOR
    // is (üres → üres, nincs tényleges adat). Egy egyszerű "az első
    // változásra rajzolj azonnal" szabály ezt az üres, "semmilyen" váltást
    // sütné el azonnal, és a KÉP MEGNYITÁSAKORI, TÉNYLEGES adat utána már
    // a debounce-Timerre esne — pont úgy, ahogy a hibajelentés leírja
    // (görbe csak az első csúszka-mozdulat UTÁN jelenik meg, mert az a
    // frissítés a KÖVETKEZŐ debounce-ablakban fut le). A helyes feltétel
    // tehát nem "bármilyen változás", hanem "üresből valós adatra váltás":
    // ez mindig az azonnali (nem debounce-olt) rajzolást váltja ki, EXIF-
    // től és a kép megnyitási sorrendtől függetlenül. Csúszka-húzás közben
    // a histogramData ezután is gyakran (minden mozzanatra) változhat — az
    // EZUTÁNI Canvas-újrarajzolásokat rövid debounce-szal ritkítjuk, hogy
    // az élő frissítés ne akaszthassa a GUI-t (#25).
    function _hasRealData(data) {
        return !!(data && data.r && data.r.some(function (v) { return v > 0 }))
    }
    property bool _paintedRealData: false
    onHistogramDataChanged: {
        if (!_paintedRealData && _hasRealData(histogramData)) {
            _paintedRealData = true
            histCanvas.requestPaint()
        } else {
            if (!_hasRealData(histogramData)) _paintedRealData = false
            redrawTimer.restart()
        }
    }

    Timer {
        id: redrawTimer
        objectName: "histogramRedrawTimer"
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

            // #228: a requestPaint() a scene graph inicializálása előtt
            // (available === false) elveszhet — a canvas ilyenkor üres
            // marad, amíg valami MÁS (pl. csúszka-mozdulat) újra ki nem
            // váltja a rajzolást. Amint elérhetővé válik, pótoljuk a
            // (esetleg elveszett) kezdő rajzolást a MÁR aktuális adatból —
            // ez a #228-as hiba MÁSODIK, egymást erősítő oka.
            onAvailableChanged: if (available) requestPaint()

            // tesztelhetőség (#228): a funkcionális teszt ebből ellenőrzi,
            // hogy tényleg lefutott-e egy rajzolás, nem csak a kötött adat
            // a helyes — a korábbi hiba a kötésben nem, csak a rajzolás
            // kimaradásában jelentkezett.
            property int paintCount: 0

            onPaint: {
                paintCount += 1
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
