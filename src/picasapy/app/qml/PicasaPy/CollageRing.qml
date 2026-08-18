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
    property int nodeIndex: 0
    property real theta: 0

    objectName: "collageRing" + nodeIndex

    //: `respack` `#ring` — 132 × 132, képernyő-egységben.
    width: 132
    height: 132

    readonly property real outerRadius: width / 2
    //: A perem belső határa: eddig tart a mozgató terület.
    readonly property real innerRadius: 48

    // A gyűrű rajza. A `respack` bitmapje nem szállítható, a MÉRETEI viszont
    // megerősítettek — a rajz ezért kódból készül, a méretek betartásával.
    Rectangle {
        anchors.fill: parent
        radius: ring.outerRadius
        color: "transparent"
        border.width: 1
        border.color: "#f0ffffff"
    }
    Rectangle {
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
    }
}
