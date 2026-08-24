import QtQuick

// A kijelölt kép GYŰRŰJE (#947).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **7.2** és **7.4**.
//
// ## Két dolog, amit könnyű elrontani
//
// 1. **A gyűrű mérete KÉPERNYŐ-egységben állandó: 132 × 132.** Nem
//    méreteződik a képpel, és nem forog vele — kódból rajzolt overlay,
//    ezért van kikommentezve a panelfából. Emiatt NEM lehet a csomópont
//    gyereke (az el van forgatva és a mérete a képé), hanem a vászon
//    testvér-rétege, a csomópont befoglaló téglalapjának közepére téve.
//
// 2. **Két érzékeny terület van, nem kettő fogantyú.** A gyűrű BELSEJE
//    mozgat (`RingMoveHandler`), a PEREME forgat és méretez egyszerre
//    (`RingKnobHandler`). Külön forgató és külön méretező fogantyú nincs
//    (spec 14.) — aki kettőt rajzol, más programot ír.
//
// ## A szög iránya
//
// A `szög = atan2(−dx, dy)` a képernyő koordinátáiban él (az y lefelé nő),
// ezért `theta = 0`-nál a fogantyú-jelölő a gyűrű ALJÁN áll: oda húzva
// nincs forgatás. A jelölő helye ebből következik:
//
//     dx = −R · sin(theta) ;  dy = +R · cos(theta)
//
// Ellenőrizhető: `theta = −π/2` → `dx = +R`, azaz a 3 óra iránya, és a
// felhasználó a `angle_caption_degrees` előjelváltása miatt „90"-et lát.
Item {
    id: ring

    property var sheet: null
    //: #1001: a „Megjelenítés és szerkesztés" parancshoz — a gyűrű a
    //: kijelölt kép FÖLÖTT ül, tehát a duplakattintás ide érkezik, nem a
    //: `CollageNode`-ra. A `CollageNode` mintájára kap saját property-t.
    property var controller: null
    property int nodeIndex: 0
    property real theta: 0

    objectName: "collageRing" + nodeIndex

    //: `respack` `#ring` — 132 × 132, képernyő-egységben.
    width: 132
    height: 132

    readonly property real outerRadius: width / 2
    //: A perem belső határa: eddig tart a mozgató terület.
    readonly property real innerRadius: 48

    // ------------------------------------------------------------------
    // A LÁTHATÓSÁG: hover + időzítő + elhalványítás (#1000)
    // ------------------------------------------------------------------
    //
    // Spec: `docs/specs/picasa-kollazs-felulet.md` **5.1/b**
    // (`RingNodeFadeHandler`, `0x007e6220`).
    //
    // ## A gyűrű LÉTE és LÁTHATÓSÁGA két külön dolog
    //
    // A lét a kijelöléshez kötött (`ringExists`), a láthatóság az
    // egérmutatóhoz. Ezért NEM a `visible`-t kapcsolgatjuk:
    //
    //   * az eredeti az eltűnéskor is csak **alfa 1**-ig (a 256-ból)
    //     halványít, nem 0-ig — a csomópont tehát ÉL;
    //   * a `visible: false` a Qt-ben az egéreseményeket is elvenné. Aki a
    //     gyűrűre kattintana (mozgatás, forgatás), attól a kattintás
    //     pillanatában venné el a fogantyút — az `opacity` nem: a Qt
    //     Quickben az átlátszó elem is fog egeret.
    //
    // ## A mechanizmus
    //
    //     látszik = hover  VAGY  zár  VAGY  (fut a 0,5 s-os késleltetés)
    //
    // Az eredeti ezt `most() − utolsó_hover < 0,5 s` alakban méri egy
    // ütemezett eseményben; a `Timer` ennek az élettartam-alapú
    // megfelelője. A késleltetést KIZÁRÓLAG a `hovered` / `fadeLocked`
    // IGAZ→HAMIS váltása indíthatja — ezért nem kell külön „látszott-e
    // eddig" állapotot vezetni.

    //: A találatvizsgálat tűrése (`0x007e62e3`: `push 0xc`).
    readonly property int hoverTolerancePx: 12
    //: Ennyi ideig látszik még a kurzor távozása után (`0xc72150 = 0.5`).
    readonly property int fadeDelayMs: 500
    //: A megjelenési animáció hossza (`0xc7c608 = 0.25f`).
    readonly property int fadeInMs: 250
    //: Az eltűnési animáció hossza (`0xc7dafc = 0.5f`).
    readonly property int fadeOutMs: 500
    //: Az eltűnés célértéke: alfa **1** a 256-ból — gyakorlatilag
    //: láthatatlan, de nem semmi.
    readonly property real fadedOpacity: 1 / 256

    //: A gyűrű LÉTE: a kijelöléshez kötött (a lap adja).
    property bool ringExists: false

    //: A csomópont doboza a találatvizsgálathoz. LAPEGYSÉGBEN érkezik, a
    //: `unit` vált képpontra — ugyanaz a szorzó, mint a `CollageNode`-nál.
    property real unit: 0
    property real centerX: 0
    property real centerY: 0
    property real nodeWidth: 0
    property real nodeHeight: 0

    //: Rajta van-e a mutató a KÉPEN, 12 képpont tűréssel.
    //:
    //: ⚠️ A doboz a csomóponttal EGYÜTT forog, ezért a mutatót előbb
    //: vissza kell forgatni a csomópont saját rendszerébe — ugyanaz a
    //: mátrix, mint a `CollageNode` árnyék-eltolásánál. Aki a
    //: TENGELYPÁRHUZAMOS befoglalóval mérne, ferde képnél a sarkok
    //: környékén hamis találatot adna.
    //:
    //: A `ringExists` szándékosan az ELSŐ tag: a rövidzár miatt a ki nem
    //: jelölt csomópontok gyűrűi hozzá sem kötődnek a mutató helyéhez,
    //: tehát 350 képnél sem számol egérmozgásonként 350 kötés.
    //:
    //: ⚠️ NYITOTT KÉRDÉS, MÉRÉSSEL (#1000). A találatvizsgálat a KÉPRE
    //: megy, nem a gyűrűre — így írja le a spec 5.1/b („ha az egér a
    //: csomópont fölött van"). Következmény: sok képnél a gyűrű 132
    //: képpontos rajza TÚLLÓG a kép + 12 képpontos zónán, tehát a
    //: forgató-méretező perem (r = 48…66) fölött állva a gyűrű
    //: elhalványul. Mérve, 933 képpont széles lapon, Képkupac témával:
    //:
    //:     10 kép → 90 px | 30 kép → 67 px | 60 kép → 57 px | 120 kép → 49 px
    //:     (a legkisebb csomópont fél-mérete + 12; a perem 57-nél van)
    //:
    //: Kb. 60 képtől a perem kikerül a zónából. Hogy az eredeti ilyenkor
    //: mit tesz, NEM megállapított: a `RingNodeFadeLockHandler`
    //: (`0x007e6390`) 1/2/3-as eseményágai csak részben feltártak, és a
    //: 2/3 épp az egérmozgás — elképzelhető, hogy a gyűrű fölötti mozgás
    //: állítja a zárat. Amíg ez nincs kimérve, NEM találunk ki hozzá
    //: viselkedést: a kattintás egyébként működik (az `opacity` nem veszi
    //: el az egeret), csak a rajz halványul.
    readonly property bool hovered: {
        if (!ring.ringExists || !ring.sheet || !ring.sheet.hoverActive)
            return false
        const dx = ring.sheet.hoverX - ring.centerX * ring.unit
        const dy = ring.sheet.hoverY - ring.centerY * ring.unit
        const lx = dx * Math.cos(ring.theta) + dy * Math.sin(ring.theta)
        const ly = -dx * Math.sin(ring.theta) + dy * Math.cos(ring.theta)
        return Math.abs(lx)
                   <= ring.nodeWidth * ring.unit / 2 + ring.hoverTolerancePx
            && Math.abs(ly)
                   <= ring.nodeHeight * ring.unit / 2 + ring.hoverTolerancePx
    }

    //: A ZÁR (`RingNodeFadeLockHandler`, `0x007e6390`) — húzás közben.
    readonly property bool fadeLocked:
        ring.sheet ? ring.sheet.ringFadeLocked : false

    Timer {
        id: fadeDelay
        objectName: "collageRingFadeDelay" + ring.nodeIndex
        interval: ring.fadeDelayMs
        repeat: false
    }

    //: Látszik-e MOST. A késleltetés alatt még igen.
    readonly property bool shown:
        ring.hovered || ring.fadeLocked || fadeDelay.running

    onHoveredChanged: {
        if (ring.hovered)
            fadeDelay.stop()
        else if (!ring.fadeLocked)
            fadeDelay.restart()
    }

    onFadeLockedChanged: {
        if (ring.fadeLocked)
            fadeDelay.stop()
        else if (!ring.hovered)
            fadeDelay.restart()
    }

    //: A kijelölés megszűnésével a késleltetésnek sincs értelme: a
    //: `Repeater` ugyanezt a delegáltat adja a következő kijelölésnek is,
    //: és egy futva hagyott időzítő ott hover nélkül mutatná a gyűrűt.
    onRingExistsChanged: if (!ring.ringExists) fadeDelay.stop()

    visible: ring.ringExists
    opacity: ring.ringExists && ring.shown ? 1.0 : ring.fadedOpacity

    Behavior on opacity {
        NumberAnimation {
            objectName: "collageRingFadeAnim" + ring.nodeIndex
            //: Az IRÁNY dönt: 0,25 s be, 0,5 s ki. A kötés a `Behavior`
            //: indulásakor értékelődik ki, amikorra a `shown` már az új
            //: állapotot mutatja.
            duration: ring.shown ? ring.fadeInMs : ring.fadeOutMs
        }
    }

    // A gyűrű rajza. A `respack` bitmapje nem szállítható, a MÉRETEI viszont
    // megerősítettek — a rajz ezért kódból készül, a méretek betartásával.
    //
    // ⚠️ Itt NINCS kézzel megadott `antialiasing` (#1010), és ez szándékos:
    // a Qt a `radius != 0` téglalapokon MAGÁTÓL bekapcsolja (enélkül a kör
    // széle fűrészfog lenne). A gyűrű ráadásul nem is forog a képpel — a
    // mérete képernyő-egységben állandó. A rákent élsimítás itt tiszta
    // rajzolási ráfizetés lenne; a `CollageNode` SZÖGLETES kerete a másik
    // eset, ott kézzel kell megadni.
    //
    // Az `objectName`-eket a #1010 tesztje olvassa: ha valaki a `radius`-t
    // kivenné vagy a kört szögletesre cserélné, az élsimítás némán elveszne.
    Rectangle {
        objectName: "collageRingOuter" + ring.nodeIndex
        anchors.fill: parent
        radius: ring.outerRadius
        color: "transparent"
        border.width: 1
        border.color: "#f0ffffff"
    }
    Rectangle {
        objectName: "collageRingInner" + ring.nodeIndex
        anchors.centerIn: parent
        width: 2 * ring.innerRadius
        height: 2 * ring.innerRadius
        radius: ring.innerRadius
        color: "transparent"
        border.width: 1
        border.color: "#80000000"
    }

    //: `#target_chicklet` 23 × 15 — a fogantyú jelölője a peremen, a
    //: pillanatnyi szögnél.
    Rectangle {
        objectName: "collageRingKnob" + ring.nodeIndex
        width: 23
        height: 15
        radius: 3
        color: Theme.thumbSelection
        border.width: 1
        border.color: "#f0ffffff"
        x: ring.outerRadius - width / 2
           - (ring.innerRadius + ring.outerRadius) / 2 * Math.sin(ring.theta)
        y: ring.outerRadius - height / 2
           + (ring.innerRadius + ring.outerRadius) / 2 * Math.cos(ring.theta)
    }

    //: `#angle_placemark` 9 × 10 — a 12 óra iránya a LAPHOZ képest, hogy a
    //: felhasználó lássa, mennyit forgatott.
    Rectangle {
        objectName: "collageRingPlacemark" + ring.nodeIndex
        width: 9
        height: 10
        color: "#a0ffffff"
        x: ring.outerRadius - width / 2
        y: ring.outerRadius - ring.outerRadius - height / 2 + 5
    }

    MouseArea {
        id: hit
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor

        //: A gyűrű KÖR alakú; a MouseArea téglalap. A sarkokat ezért
        //: átengedjük az alatta lévő elemeknek, különben a gyűrű egy
        //: láthatatlan négyzettel takarná el a szomszéd képeket.
        function zone(mouse) {
            const dx = mouse.x - ring.outerRadius
            const dy = mouse.y - ring.outerRadius
            const dist = Math.sqrt(dx * dx + dy * dy)
            if (dist > ring.outerRadius)
                return ""
            return dist >= ring.innerRadius ? "knob" : "move"
        }

        onPressed: function (mouse) {
            const mode = zone(mouse)
            if (mode === "" || !ring.sheet) {
                mouse.accepted = false
                return
            }
            const p = hit.mapToItem(ring.sheet, mouse.x, mouse.y)
            if (mode === "knob")
                ring.sheet.beginKnob(ring.nodeIndex, p.x, p.y)
            else
                ring.sheet.beginMove(ring.nodeIndex, p.x, p.y, mouse.modifiers)
        }

        onPositionChanged: function (mouse) {
            if (!ring.sheet)
                return
            const p = hit.mapToItem(ring.sheet, mouse.x, mouse.y)
            ring.sheet.updateDrag(p.x, p.y, mouse.modifiers)
        }

        onReleased: function (mouse) {
            if (!ring.sheet)
                return
            const p = hit.mapToItem(ring.sheet, mouse.x, mouse.y)
            ring.sheet.endDrag(p.x, p.y)
        }

        onCanceled: if (ring.sheet) ring.sheet.cancelDrag()

        // #1001: „Megjelenítés és szerkesztés" a rendszer dupla
        // kattintásán — ugyanaz a parancs, mint a `CollageNode`-on.
        //
        // ⚠️ Enélkül a duplakattintás a KIJELÖLT képen néma marad: a gyűrű
        // a kép FÖLÖTT ül (z: 10000+), az első lenyomás kijelöl, és
        // onnantól minden egéresemény ide érkezik — a `CollageNode`
        // kezelője már nem látja. A hiba pontosan így maradt észrevétlen.
        // Csak a BELSŐ (mozgató) zóna nyit szerkesztőt; a peremen a
        // forgató-méretező fogantyú van (spec 7.2).
        onDoubleClicked: function (mouse) {
            if (zone(mouse) !== "move" || !ring.controller)
                return
            ring.controller.viewAndEditSelection()
        }
    }
}
