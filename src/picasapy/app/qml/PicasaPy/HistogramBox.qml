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

    // {r: [0..1 érték * 256 vödör], g: [...], b: [...]} — histogram_helper.py
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

        // A hisztogram rajzterülete: a három csatorna egymásra rajzolva,
        // áttetsző kitöltésű oszlopokkal.
        //
        // #512: KORÁBBAN a magasságot kézzel számoltuk (doboz-magasság
        // mínusz cím/EXIF-sor implicitHeight-je) — ez két okból is hibás
        // volt: (1) `box.anchors.margins` a `box` KÜLSŐ (a szülőhöz való
        // horgonyzási) margóját adta vissza, ami a PhotoViewer.qml-beli
        // példányosításnál VÉLETLENÜL nem-nulla (10), miközben a valódi,
        // itt számító belső margó 8 — a kettő összecserélése hibás
        // levonást adott; (2) a `Math.max(0, …)` alsó korlát miatt bőséges
        // (pl. magyar, több soros) EXIF-szöveg mellett a rajzterület
        // magassága NULLÁRA zuhant, és a `Column` a KÖVETKEZŐ elemet
        // (`cameraLabel`) ilyenkor a `plot` UTÁNI térköz hozzáadása
        // NÉLKÜL, közvetlenül a cím alá helyezte — mérve: 8 soros EXIF
        // mellett `plot.y === cameraLabel.y` (mindkettő 19px), azaz a
        // rajzterület és a szöveg doboza AZONOS pozícióból indult.
        // (A `cameraLabel.implicitHeight` „sortörés előtti" hipotézise
        // NEM igazolódott: a kötött szélesség miatt már a tördelt,
        // véglegesen soktornyú szöveg magasságát tükrözi.)
        //
        // A ROBUSZTUS megoldás: nem számolunk kézzel — a `ColumnLayout`
        // maga osztja el a helyet. A cím és az EXIF-sor a saját
        // (`implicitHeight`-ből származó) preferált magasságát kapja, a
        // rajzterület `Layout.fillHeight`-tel a MARADÉKOT — soha nem
        // csúszhat rá a szövegre, mert egy Layout elemei sosem fedik
        // egymást (legfeljebb szélsőségesen bőséges szöveg esetén a
        // rajzterület `Layout.minimumHeight: 0`-ra zsugorodik, ahelyett
        // hogy átfedne).
        Item {
            id: plot
            objectName: "histogramPlot"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 0
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
