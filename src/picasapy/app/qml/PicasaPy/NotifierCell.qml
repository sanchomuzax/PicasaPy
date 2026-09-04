import QtQuick

// EGY értesítés a lebegő sávban (#1129) — a `respack.yt` `notifier`
// moduljának `cell1` rétege.
//
// Spec: `docs/specs/picasa-lebego-ertesito.md` „Geometria — MÉRVE A
// BINÁRISBÓL". A méretek nem becslésből valók, hanem a bináris
// erőforráscsomag rétegfejléceiből:
//
//   docbounds / cell1   0,0 → 247 × 45     a cella
//   cellbase            0,0 →  13 × 45     bal oldali sáv
//   basedecrect       226,0 →  21 × 45     jobb oldali vezérlősáv
//   close             231,4 →  11 × 11     bezárás (jobb FELSŐ)
//   gripper          233,19 →   7 ×  7     fogantyú (jobb KÖZÉP)
//   collapse         231,30 →  11 × 11     összecsukás (jobb ALSÓ)
//
// ## Amiért a felirat NEM tördel
//
// A tulajdonos képernyőképén a magyar felirat ELVÁGÓDIK („A
// képernyőfelvétel mentése si…"). Ez nem hiba, hanem az ablak fix
// szélességének a következménye: 247 képpontba a hosszú mondat nem fér
// be, és az eredeti sem tördeli. Aki ide `wrapMode`-ot tesz, más
// programot ír — és a cella magassága sem 45 marad.
//
// ## Két sor: esemény + cselekvési tipp
//
// Az első sor MI történt, a második MIT LEHET TENNI (`CThumbUI::clickview`
// — „a megtekintéshez kattintson ide"). A tipp csak akkor jelenik meg, ha
// a hívó adott ilyet: az eredetiben is a hívó adja a tartalmat, az ablak
// általános tartály.
Rectangle {
    id: cella

    /** A cella sorszáma a sávban — az `objectName`-ek ebből épülnek. */
    property int cellIndex: 0
    /** Az esemény sora (első sor). */
    property string title: ""
    /** A cselekvési tipp (második sor) — üresen elmarad. */
    property string hint: ""
    /** Az eseményhez tartozó adat (nálunk útvonal) — a kattintás vinné. */
    property string payload: ""
    /** Meddig marad kint magától (ms) — a sáv adja. */
    property int lifetimeMs: 0

    // ------------------------------------------------------------------
    // #2157 — a cella CSÚSZIK, nem halványodik
    // ------------------------------------------------------------------
    //
    // A rajzoló két kulcskockás sávot értékel ki minden képkockán
    // (`0x00655950` → `0x009e5e70`). Az „A" sáv a cellaszélességet
    // (`[popup+0x1bc]` = 247) szorozza: élő cellán a célja **−1,0**,
    // elbocsátáskor **0,0**. Vagyis a cella egy TELJES cellaszélességet
    // tesz meg vízszintesen — nálunk ez a `[bent ? 0 : width]` pár, mert
    // a sáv ablaka pontosan egy cella széles, tehát a kilógó cella
    // magától eltűnik.

    /** Bent van-e a cella (a sáv ablakában), vagy kicsúszva. */
    property bool bent: false
    //: `0x00c7e304` — a becsúszás hossza.
    readonly property int beMs: 600
    //: `0x00c7dcc8` — a visszacsúszás FELEANNYI. Ez az eredeti
    //: aszimmetriája, nem elírás.
    readonly property int visszaMs: 300

    /** A kicsúszás lefutott — a sáv innen veheti ki a cellát. */
    signal kicsuszasKesz()

    /** Indítsd a kicsúszást; a `kicsuszasKesz` a végén jelez. */
    function kicsuszik() {
        cella.bent = false
        kicsuszasOra.restart()
    }

    x: cella.bent ? 0 : cella.width

    Behavior on x {
        NumberAnimation {
            objectName: "notifierSlideAnim" + cella.cellIndex
            duration: cella.bent ? cella.beMs : cella.visszaMs
            //: Az eredeti görbéje a saját `u = 8·t` skáláján
            //: exponenciális (`0x0072df60`). A Qt-görbék közül az
            //: `OutExpo` adja vissza ezt a jelleget — gyors indulás,
            //: lágy beállás. ⚠️ A pontos, képkockára menő egyezés
            //: **nincs mérve**: a bináris a saját skáláján számol, és a
            //: két görbe-család nem feleltethető meg egymásnak
            //: közvetlenül. A jelleg mért, a konkrét Qt-görbe választás.
            easing.type: Easing.OutExpo
        }
    }

    Component.onCompleted: cella.bent = true

    //: A kicsúszás órája — a jel csak azután megy ki, hogy a cella
    //: tényleg elhagyta az ablakot; enélkül a törlés levágná az
    //: animációt, és megint „ugrás" látszana.
    Timer {
        id: kicsuszasOra
        objectName: "notifierCellSlideOut" + cella.cellIndex
        interval: cella.visszaMs
        repeat: false
        onTriggered: cella.kicsuszasKesz()
    }

    /** A felhasználó a cellára kattintott: vigyen az eredményhez. */
    signal activated()
    /** A záró vezérlő. */
    signal closed()
    /** Lejárt az élettartam. */
    signal expired()

    objectName: "notifierCell" + cellIndex

    //: `docbounds` — 247 × 45, fix.
    width: 247
    height: 45

    color: Theme.chromeBg
    border.width: 1
    border.color: Theme.chromeBorder

    //: `cellbase` — a bal oldali, teljes magasságú sáv.
    Rectangle {
        objectName: "notifierCellBase" + cella.cellIndex
        x: 0
        y: 0
        width: 13
        height: cella.height
        color: Theme.picasaGreen
    }

    // A találati terület a bal sáv és a vezérlősáv KÖZÖTT: a záró
    // vezérlőre menő kattintás így nem szivárog át a navigációra.
    MouseArea {
        objectName: "notifierCellHit" + cella.cellIndex
        x: 13
        y: 0
        width: 226 - 13
        height: cella.height
        cursorShape: Qt.PointingHandCursor
        onClicked: cella.activated()

        Column {
            anchors.fill: parent
            anchors.leftMargin: 8
            anchors.rightMargin: 4
            anchors.topMargin: 6
            spacing: 2

            Text {
                objectName: "notifierCellTitle" + cella.cellIndex
                width: parent.width
                text: cella.title
                //: A fix szélességű ablakban a hosszú felirat elvágódik —
                //: az eredeti sem tördel.
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
                maximumLineCount: 1
                font.pixelSize: Theme.fontSize
                font.weight: Theme.fontWeightBold
                color: Theme.ink
            }

            Text {
                objectName: "notifierCellHint" + cella.cellIndex
                width: parent.width
                visible: cella.hint.length > 0
                text: cella.hint
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
                maximumLineCount: 1
                font.pixelSize: Theme.fontSize
                font.underline: true
                color: Theme.linkBlue
            }
        }
    }

    //: `basedecrect` — a jobb oldali vezérlősáv.
    Rectangle {
        objectName: "notifierCellControls" + cella.cellIndex
        x: 226
        y: 0
        width: 21
        height: cella.height
        color: "transparent"

        //: `close` — 231,4 → 11 × 11 a CELLA koordinátáiban, azaz 5,4 a
        //: sávon belül.
        Item {
            objectName: "notifierCellClose" + cella.cellIndex
            x: 5
            y: 4
            width: 11
            height: 11

            Canvas {
                anchors.fill: parent
                onPaint: {
                    const ctx = getContext("2d")
                    ctx.reset()
                    ctx.strokeStyle = Theme.ink
                    ctx.lineWidth = 1.5
                    ctx.beginPath()
                    ctx.moveTo(2.5, 2.5)
                    ctx.lineTo(width - 2.5, height - 2.5)
                    ctx.moveTo(width - 2.5, 2.5)
                    ctx.lineTo(2.5, height - 2.5)
                    ctx.stroke()
                }
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: cella.closed()
            }
        }
    }

    //: Az élettartam órája. A cella maga NEM tünteti el magát — jelez, és
    //: a sáv (a lista gazdája) veszi ki. Így a lista és a nézet nem
    //: csúszhat szét.
    Timer {
        objectName: "notifierCellLife" + cella.cellIndex
        interval: cella.lifetimeMs
        running: cella.lifetimeMs > 0
        repeat: false
        onTriggered: cella.expired()
    }
}
