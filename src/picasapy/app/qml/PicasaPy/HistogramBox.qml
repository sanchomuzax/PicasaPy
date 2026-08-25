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
//
// #1344 ELRENDEZÉS: a panel MINDEN eleme ki van mérve a `respack.yt`
// rétegfejléceiből (`docs/specs/picasa-nerdview-panel.md`), a panel bal
// felső sarkához relatívan. A korábbi `ColumnLayout` + 8-as margó
// találgatás volt (a spec csak a hisztogram 213 × 59-ét tartalmazta),
// ezért a tartalom magasságával együtt mozgott minden. Most fix,
// koordinátás elrendezés van: a panel 238 × 144, és az elemek a mért
// helyükön ülnek — a tartalom mennyiségétől függetlenül.
Rectangle {
    id: box
    objectName: "histogramBox"

    // {r: [0..1 belső magasság * 256 bin], g: [...], b: [...]}
    // — histogram_helper.py; 1,0 pontosan 70 belső képpont.
    property var histogramData: ({ r: [], g: [], b: [] })
    property string cameraSummary: ""

    readonly property int bucketCount: 256

    // A mért panelméret (`nerdview/docbounds`, 0,0 → 238,144). A
    // PhotoViewer.qml explicit width/height-tal is ezt adja; az implicit
    // méret attól független használatnál (teszt, önálló beágyazás) is a
    // helyes dobozt hozza.
    implicitWidth: 238
    implicitHeight: 144

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

    // A tartalom sávja: a mért elemek mind a bal széltől 13-nál kezdődnek
    // és 226-nál érnek véget (13 + 213).
    readonly property int bandX: 13
    readonly property int bandWidth: 213

    // A felirat (`static(Histogram & Camera Information): nvhead`,
    // 13,4 → 113,15). A doboz 11 képpont magas: EGY sor.
    //
    // #1344: a #235-ben bevezetett `font.bold: true` + `pointSize: 14` +
    // kétsoros tördelés a mi kitalálásunk volt — a `nerdview.tre`-ben a
    // `nvhead`-nek EGYETLEN tulajdonsága van (`m_displayfont14`), és SEMMI
    // nem jelöl félkövéret. A mérvadó bizonyíték a réteg doboza: 11
    // képpont magas, tehát egysoros, normál vastagságú felirat.
    Text {
        id: titleLabel
        objectName: "histogramTitle"
        x: box.bandX
        y: 4
        width: box.bandWidth
        height: 11
        text: qsTr("Histogram and camera information")
        // A sormagasság a mérvadó (11 képpont), nem a Picasa font-tokene:
        // az `m_displayfont14` a Picasa erőforrás-nyelvének neve, nem
        // Qt-pontméret. A 11 képpontos betűméret egy sorba fér a 11
        // képpontos dobozba, és a hosszabb magyar fordítás is elfér a
        // 213 képpontos sávban.
        font.pixelSize: 11
        font.bold: false
        color: Theme.ink
        // egy sor, tördelés nélkül (`wrapMode` alapértéke `NoWrap`).
        //
        // ⚠️ A 11 képpont FELSŐ korlát, nem fix méret. A magyar fordítás
        // („Hisztogram és fényképezőgép-adatok") a windowsos alapbetűvel
        // 374 képpontot kérne a 213-as sávban — a CI windows-lába pontosan
        // ezen bukott el. Elidálni rossz válasz: a felirat közepét vágná ki.
        // A `HorizontalFit` ezért a betűt zsugorítja, ahol nem fér el; ahol
        // elfér (linuxi alapbetű), ott semmi nem változik.
        // Ugyanez a minta él a `PicasaButton`-ben (#992).
        fontSizeMode: Text.HorizontalFit
        //: A padló 7 képpont: a windowsos alapbetűvel a magyar felirat
        //: 11 képponton nem fér a 213-as sávba, és elidálva a VÉGE veszne el.
        //: A 7 még olvasható, és a mért 213-at nem lépi túl.
        minimumPixelSize: 7
        // az elide csak VÉGSZÜKSÉG-őr a 8 képpontos padló alatt
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
    }

    // A hisztogram 213 × 59-es megjelenítési területe (`rect: histoback`,
    // 13,25 → 226,84). A tartalom előbb pontosan 256 × 70-es belső képként
    // készül el (HistogramBitmap), majd ez a réteg méreteződik le — egy bin
    // tehát nem egy képernyő-oszlop, ahogy a Picasában sem (#864).
    Item {
        id: plot
        objectName: "histogramPlot"
        // #1344: a mért elrendezésben az EXIF-terület teteje (82) 2 képponttal
        // a hisztogram alja (25 + 59 = 84) fölé ér — ez az eredetiben is így
        // van. A rajzolási SORREND viszont nem mindegy: a #864 képpont-orákuluma
        // a plot minden képpontját ellenőrzi, és a fölé csorgó betűtalpak
        // (platformfüggő betűrajzolás!) hamis bukást adnának a másik CI-lábon.
        // Ezért a plot a szöveg FÖLÖTT rajzolódik; a 2 képpontos átfedés
        // megmarad, csak a takarás iránya rögzített.
        z: 1
        x: box.bandX
        y: 25
        width: box.bandWidth
        height: 59
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
    //
    // #1344: a két oszlop NEM egyforma. A mért rétegek: `text: detail1`
    // 13,82 → 151,123 (138 × 41) és `text: detail2` 157,82 → 226,123
    // (69 × 41) — köztük 151 → 157, azaz 6 képpont rés. A sáv 123-nál
    // véget ér, alatta 21 képpont üres térköz a panel aljáig. A `clip`
    // gondoskodik róla, hogy bőséges EXIF-blokk se nőjön ki a panelből.
    Column {
        id: cameraLabel
        objectName: "cameraSummaryArea"
        x: box.bandX
        y: 82
        width: box.bandWidth
        height: 41
        clip: true
        spacing: 1

        readonly property int leftColumnWidth: 138
        readonly property int columnGap: 6
        readonly property int rightColumnWidth: 69

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
                    objectName: "cameraCellLeft"
                    x: 0
                    width: cameraLabel.leftColumnWidth
                    text: parent.cells[0]
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                    font.pixelSize: Theme.fontSize - 2
                    color: Theme.ink
                }
                Text {
                    id: rightCell
                    objectName: "cameraCellRight"
                    x: cameraLabel.leftColumnWidth + cameraLabel.columnGap
                    width: cameraLabel.rightColumnWidth
                    text: parent.cells.length > 1 ? parent.cells[1] : ""
                    elide: Text.ElideRight
                    font.pixelSize: Theme.fontSize - 2
                    color: Theme.ink
                }
            }
        }
    }
}
