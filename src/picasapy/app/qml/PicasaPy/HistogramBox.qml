import QtQuick
import QtQuick.Layouts

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

    // {r: [0..1 belső magasság * 256 bin], g: [...], b: [...]}
    // — histogram_helper.py; 1,0 pontosan 70 belső képpont.
    property var histogramData: ({ r: [], g: [], b: [] })
    property string cameraSummary: ""

    readonly property int bucketCount: 256

    // #512: a #429-ben bevezetett meleg barna (`#a88974`) hibás volt — a
    // bejelentő ELEREDETI Picasa-képernyőképe világosszürke panelt mutat,
    // benne egy elkülönülő, világos rajzterülettel. A `respack.yt`-ből
    // idézett érték vagy nem ehhez a panelhez tartozott, vagy félreolvasás
    // volt; a képernyőkép az erősebb bizonyíték, ezért a barna literál
    // helyett a `Theme.chromeBg` tokent használjuk — pontosan ez a token
    // adja a szerkesztőpanel (EditorPanel.qml) saját krómhátterét is, és a
    // `nerdview` a Picasában ugyanennek a panelnek a része (ld.
    // docs/specs/picasa-respack-format.md 5.2). Így a hisztogram-doboz
    // témafüggően illeszkedik (világos/sötét), nem rögzített.
    // A szöveg ezért is követheti a Theme.ink tokent (nem kell rögzített
    // `#333333` olvashatósági kényszer-szín, mint a barna alapon).
    color: Theme.chromeBg
    border.color: Theme.chromeBorder
    radius: 3

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 5

        Text {
            id: titleLabel
            objectName: "histogramTitle"
            Layout.fillWidth: true
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

        // A hisztogram 213 × 59-es megjelenítési területe. A tartalom előbb
        // pontosan 256 × 70-es belső képként készül el (HistogramBitmap),
        // majd ez a réteg méreteződik le — egy bin tehát nem egy képernyő-
        // oszlop, ahogy a Picasában sem (#864).
        //
        // #512: a ColumnLayout gondoskodik róla, hogy a rajzterület és az
        // EXIF-szöveg ne fedje egymást. A #864 óta a plot nem a maradék
        // helyet tölti ki, hanem a bizonyított fix 213 × 59-es méretet kapja.
        Item {
            id: plot
            objectName: "histogramPlot"
            Layout.preferredWidth: 213
            Layout.minimumWidth: 213
            Layout.maximumWidth: 213
            Layout.preferredHeight: 59
            Layout.minimumHeight: 59
            Layout.maximumHeight: 59
            Layout.alignment: Qt.AlignHCenter
            clip: true

            // #512: a rajzterület (`histoback`/`histo` réteg) elkülönül a
            // panel hátterétől — a `Theme.contentPanel` a projekt szokásos
            // „elkülönülő világos tartalom" tokene (ld. pl. EditorPanel
            // fültartalma), világos témán fehér, sötét témán sötétszürke
            // kártyaháttér.
            Rectangle {
                id: plotBackground
                objectName: "histogramPlotBackground"
                anchors.fill: parent
                color: Theme.contentPanel
            }

            Item {
                id: scaledBitmap
                anchors.fill: parent

                HistogramBitmap {
                    histogramData: box.histogramData
                    transformOrigin: Item.TopLeft
                    transform: Scale {
                        origin.x: 0
                        origin.y: 0
                        xScale: scaledBitmap.width / 256
                        yScale: scaledBitmap.height / 70
                    }
                }
            }
        }

        // #235: a kameraadat az eredeti Picasa 2-oszlopos, címkézett
        // elrendezését követi. A cameraSummary soronként `bal\tjobb`
        // cellapárokat hordoz (formatting.camera_summary_text) — ha nincs
        // tab a szövegben (régi/egyszerű érték), egyoszloposan jelenik meg.
        Column {
            id: cameraLabel
            objectName: "cameraSummaryArea"
            Layout.fillWidth: true
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
                color: Theme.ink
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
                        color: Theme.ink
                    }
                    Text {
                        id: rightCell
                        anchors.right: parent.right
                        width: Math.floor(parent.width * 0.38)
                        text: parent.cells.length > 1 ? parent.cells[1] : ""
                        elide: Text.ElideRight
                        font.pixelSize: Theme.fontSize - 2
                        color: Theme.ink
                    }
                }
            }
        }
    }
}
