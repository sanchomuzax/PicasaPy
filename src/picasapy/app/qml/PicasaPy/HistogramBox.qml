import QtQuick

// RGB-hisztogram + fényképezőgép-adat doboz (#25, #228, #232): a néző
// bal alsó dobozának élesítése, Picasa-mintára. Buta komponens — a
// hisztogramot és az EXIF-sort kívülről kapja (EditController.histogram
// / cameraSummary, ld. edit_controller.py).
//
// #232 GYÖKÉROK: a korábbi (#25/#228) verzió QML `Canvas`-t használt,
// `requestPaint()`-tel. A Canvas a valós (GPU-hátterű, Windows) ablakban
// nem-determinisztikusan üresen maradt: a `requestPaint()` a scene graph
// inicializálása/threaded render loop időzítésén elveszhetett, és a vékony
// 1px-es áttetsző vonalak amúgy is alig látszottak. A megjelenített adat
// és a `paintCount>0` offscreen tesztben helyes volt, élesben mégsem
// rajzolódott görbe. Ezért a Canvas-t deklaratív, mindig-renderelő
// megoldásra cseréltük: vödrönként egy-egy `Rectangle`-oszlop (scene graph
// csomópont) — nincs `requestPaint`, nincs időzítés; amint a kötött adat
// vagy a méret érvényes, a kötések maguktól újraértékelődnek és az oszlopok
// megjelennek. A kitöltött oszlopok ráadásul a referencia-kinézetet is hozzák.
Rectangle {
    id: box
    objectName: "histogramBox"

    // {r: [0..1 érték * 256 vödör], g: [...], b: [...]} — histogram_helper.py
    property var histogramData: ({ r: [], g: [], b: [] })
    property string cameraSummary: ""

    readonly property int bucketCount: 256

    color: Theme.contentPanel
    border.color: Theme.chromeBorder
    radius: 3

    Column {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 5

        Text {
            id: titleLabel
            objectName: "histogramTitle"
            width: parent.width
            text: qsTr("Histogram and camera information")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
            // #235: keskeny doboznál a cím ne vágódjon `…`-ra — legfeljebb
            // két sorba törik (az eredeti Picasában a cím mindig teljes)
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }

        // A hisztogram rajzterülete: a három csatorna egymásra rajzolva,
        // áttetsző kitöltésű oszlopokkal. A magasságot a fennmaradó helyből
        // számoljuk (cím és EXIF-sor levonása után), így a doboz teljes
        // magasságát kitölti.
        Item {
            id: plot
            objectName: "histogramPlot"
            width: parent.width
            height: Math.max(
                0,
                box.height - box.anchors.margins * 2
                - titleLabel.implicitHeight - cameraLabel.implicitHeight
                - parent.spacing * 2)
            clip: true

            // egy csatorna oszlopsorozata — kitöltött, áttetsző (a három
            // egymásra keveredve adja a Picasa-hisztogram színvilágát)
            component ChannelBars : Repeater {
                id: bars
                required property var values
                required property color barColor
                model: box.bucketCount
                delegate: Rectangle {
                    required property int index
                    readonly property real v: (bars.values && index < bars.values.length)
                                              ? bars.values[index] : 0
                    width: Math.ceil(plot.width / box.bucketCount)
                    x: index * (plot.width / box.bucketCount)
                    height: v * plot.height
                    y: plot.height - height
                    color: bars.barColor
                    opacity: 0.55
                    visible: height > 0
                }
            }

            ChannelBars { values: box.histogramData ? box.histogramData.r : []; barColor: Theme.brandRed }
            ChannelBars { values: box.histogramData ? box.histogramData.g : []; barColor: Theme.brandGreen }
            ChannelBars { values: box.histogramData ? box.histogramData.b : []; barColor: Theme.brandBlue }
        }

        // #235: a kameraadat az eredeti Picasa 2-oszlopos, címkézett
        // elrendezését követi. A cameraSummary soronként `bal\tjobb`
        // cellapárokat hordoz (formatting.camera_summary_text) — ha nincs
        // tab a szövegben (régi/egyszerű érték), egyoszloposan jelenik meg.
        Column {
            id: cameraLabel
            objectName: "cameraSummaryArea"
            width: parent.width
            spacing: 1

            readonly property var summaryRows:
                box.cameraSummary.length > 0 ? box.cameraSummary.split("\n") : []

            Text {
                objectName: "cameraSummaryText"
                width: parent.width
                visible: cameraLabel.summaryRows.length === 0
                text: qsTr("No EXIF data available")
                font.pixelSize: Theme.fontSize - 2
                font.italic: true
                color: Theme.textGray
            }

            Repeater {
                model: cameraLabel.summaryRows
                delegate: Item {
                    required property string modelData
                    readonly property var cells: modelData.split("\t")
                    width: cameraLabel.width
                    height: Math.max(leftCell.implicitHeight,
                                     rightCell.implicitHeight)

                    Text {
                        id: leftCell
                        anchors.left: parent.left
                        width: Math.floor(parent.width * 0.6)
                        text: parent.cells[0]
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                        font.pixelSize: Theme.fontSize - 2
                        color: Theme.textGray
                    }
                    Text {
                        id: rightCell
                        anchors.right: parent.right
                        width: Math.floor(parent.width * 0.38)
                        text: parent.cells.length > 1 ? parent.cells[1] : ""
                        elide: Text.ElideRight
                        font.pixelSize: Theme.fontSize - 2
                        color: Theme.textGray
                    }
                }
            }
        }
    }
}
