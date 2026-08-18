import QtQuick

// Egy kép a kollázs-vásznon (#947, a #920 6/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **6.2–6.3**, **7.1**, **7.3**.
//
// ## Amit ez a fájl NEM csinál
//
// Nem tud a húzásról. A lenyomás, a mozgatás és a felengedés mind a
// `CollageSheet` közös függvényeire megy (`beginMove` / `updateMove` /
// `endMove`) — ugyanazokra, amelyeket a gyűrű belseje is hív. Ez
// szándékos: két külön mozgatás-megvalósítás előbb-utóbb elválik
// egymástól, és a felhasználó azt látná, hogy a kép máshova ugrik attól
// függően, hol fogta meg.
//
// ## A geometria
//
// Minden szám LAPEGYSÉGBEN érkezik (a lap belső szélessége 1024, spec
// 6.1); a képpontra váltás az `unit` szorzóval történik — MINDKÉT
// tengelyen ugyanazzal, ezért a lap méretez, de nem torzít.
//
// A `nodeWidth` / `nodeHeight` a KÜLSŐ, kerettel EGYÜTT értendő doboz
// (spec 6.2, `collage/nodes.py`). A fotó helyét ebből számoljuk vissza a
// `collage/frames.py` arányaival — a QML nem talál ki sajátot.
Item {
    id: node

    //: A vászon (`CollageSheet`) — innen jön az egységváltó és ide megy
    //: minden egérművelet.
    property var sheet: null
    property var controller: null

    //: A csomópont sorszáma a modellben = a RAJZOLÁSI sorrend (0 = legalul).
    property int nodeIndex: 0

    //: Képpont / lapegység.
    property real unit: 0

    property string path: ""
    property real centerX: 0
    property real centerY: 0
    property real nodeWidth: 0
    property real nodeHeight: 0
    property real theta: 0
    property string border: "noborder"
    property string caption: ""
    property bool selected: false
    property bool missing: false

    //: „Képfeliratok megjelenítése" — a Polaroid-keret alsó sávjának szövege
    //: CSAK ekkor látszik (a buboréksúgó ezt ki is mondja).
    property bool captionsVisible: true

    //: A kért miniatűr-él képpontban; a darabszámmal lépcsőzik (spec 6.3).
    property int thumbnailSize: 256

    objectName: "collageNode" + nodeIndex

    width: Math.max(1, nodeWidth * unit)
    height: Math.max(1, nodeHeight * unit)
    x: centerX * unit - width / 2
    y: centerY * unit - height / 2

    // A forgatás a doboz KÖZEPE körül: a `collage/nodes.py` is a
    // középpontból számolja a bal-felső sarkot, tehát a forgatás nem
    // mozdíthatja el a középpontot.
    transformOrigin: Item.Center
    rotation: theta * 180 / Math.PI

    // Húzás közben 0,9 (spec 7.3). A gazdája a vászon, mert az `Alt`
    // rétegváltása után a húzott csomópont INDEXE megváltozik — a jelzőt
    // ezért nem a saját lenyomásunk, hanem a vászon állapota adja.
    opacity: (node.sheet && node.sheet.dragIndex === node.nodeIndex
              && node.sheet.dragMode === "move") ? 0.9 : 1.0

    z: nodeIndex

    // --- A keret geometriája (a `collage/frames.py` arányaiból) -------------
    //
    // A rajzoló a KÜLSŐ dobozból számol vissza a fotóra (`nodes.photo_box`).
    // Ugyanazok az arányok, folytonos alakban — a rajzoló kerekítése
    // legfeljebb egy képpontot mozdít, ami az élő előnézeten nem látszik.

    readonly property real _photoWidth: {
        if (border === "polaroid")
            return width / 1.145                       // POLAROID_WIDTH_RATIO
        if (border === "whiteborder")
            return width <= height ? width / 1.1
                                   : width - 0.1 * (height / 1.1)
        return width
    }
    readonly property real _photoHeight: {
        if (border === "polaroid")
            return height / 1.374                      // POLAROID_HEIGHT_RATIO
        if (border === "whiteborder")
            return width <= height ? height - 0.1 * (width / 1.1)
                                   : height / 1.1
        return height
    }
    //: A Polaroid margója a fotó SZÉLESSÉGÉBŐL jön (nem a rövidebb
    //: oldalából) — ez eltér a fehér szegélytől, és könnyű elnézni.
    readonly property real _photoX: border === "polaroid"
        ? _photoWidth * 0.0725                         // POLAROID_MARGIN_RATIO
        : (width - _photoWidth) / 2
    readonly property real _photoY: border === "polaroid"
        ? _photoWidth * 0.0725
        : (height - _photoHeight) / 2

    // --- A rajz -------------------------------------------------------------

    // A keret lapja. `noborder`-nél nincs mit rajzolni, de a Rectangle
    // átlátszóan ott marad, hogy a mérete egyetlen helyen éljen.
    Rectangle {
        anchors.fill: parent
        color: node.border === "polaroid" ? "#d9d9d9"       // POLAROID_PAPER
             : node.border === "whiteborder" ? "#eeeeee"    // WHITE_BORDER
             : "transparent"
    }

    Image {
        objectName: "collageNodeImage" + node.nodeIndex
        visible: !node.missing
        x: node._photoX
        y: node._photoY
        width: node._photoWidth
        height: node._photoHeight
        source: node.missing || node.path === ""
                ? "" : "file:" + node.path
        // A kért felbontás a darabszámmal lépcsőzik (spec 6.3): ettől nem
        // fullad meg a 350 képes kollázs — a Qt már a dekódolásnál
        // lekicsinyít, nem a teljes képet tartja a memóriában.
        sourceSize.width: node.thumbnailSize
        sourceSize.height: node.thumbnailSize
        asynchronous: true
        cache: true
        // A rajzoló alapesete a `fill=True` (a doboz hézag nélkül tele, a
        // túllógó rész vágva) — `collage/nodes.py` `fit_to_frame`.
        fillMode: Image.PreserveAspectCrop
        clip: true
    }

    // Nem található kép: HELYKITÖLTŐ csempe (spec 9.4) — a lyuk látszódjon,
    // különben a felhasználó azt hiszi, ő törölte. A színek a rajzoló
    // `_missing_tile`-jából valók (BGR 200/120 → #c8c8c8 / #787878).
    Canvas {
        objectName: "collageNodeMissing" + node.nodeIndex
        visible: node.missing
        anchors.fill: parent
        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()
            ctx.fillStyle = "#c8c8c8"
            ctx.fillRect(0, 0, width, height)
            ctx.strokeStyle = "#787878"
            ctx.lineWidth = 1
            ctx.strokeRect(0.5, 0.5, width - 1, height - 1)
            ctx.beginPath()
            ctx.moveTo(0, 0); ctx.lineTo(width, height)
            ctx.moveTo(width, 0); ctx.lineTo(0, height)
            ctx.stroke()
        }
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }

    // A Polaroid-felirat az alsó sávban — CSAK Polaroid keretnél és csak
    // bekapcsolt képfeliratoknál.
    Text {
        objectName: "collageNodeCaption" + node.nodeIndex
        visible: node.captionsVisible && node.border === "polaroid"
                 && node.caption !== ""
        text: node.caption
        elide: Text.ElideRight
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        color: "#3c3c3c"                                   // _CAPTION_INK_BGR
        font.pixelSize: Math.max(6, Math.round(
            (node.height - node._photoY - node._photoHeight) * 0.55))
        x: node._photoX
        width: node._photoWidth
        y: node._photoY + node._photoHeight
        height: Math.max(0, node.height - node._photoY - node._photoHeight)
    }

    // A kijelölés jelölése. A gyűrű a KÜLÖN overlay (`CollageRing`), ez csak
    // a keret — a rácsos témáknál (ahol nincs gyűrű) ez az EGYETLEN jel.
    Rectangle {
        objectName: "collageNodeSelection" + node.nodeIndex
        anchors.fill: parent
        visible: node.selected
        color: "transparent"
        border.width: 2
        border.color: Theme.thumbSelection
    }

    // --- Az egér ------------------------------------------------------------

    MouseArea {
        id: hit
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        // A `pan_hand_drag` / `pan_hand_normal` megfelelője (spec 7.4).
        cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor

        //: A vászon koordinátáiban — a csomópont EL VAN FORGATVA, tehát a
        //: saját koordinátáiban mért egérpozíció nem összehasonlítható.
        function sheetPoint(mouse) {
            return hit.mapToItem(node.sheet, mouse.x, mouse.y)
        }

        // A kijelölés LENYOMÁSRA sül el (`picasa-eger-es-kijeloles.md` 2.):
        // enélkül a húzás egy ki nem jelölt képen indulna, és a gyűrű csak
        // a felengedés után jelenne meg.
        onPressed: function (mouse) {
            if (!node.sheet)
                return
            node.sheet.clickSelect(node.nodeIndex, mouse.modifiers)
            const p = sheetPoint(mouse)
            node.sheet.beginMove(node.nodeIndex, p.x, p.y, mouse.modifiers)
        }

        onPositionChanged: function (mouse) {
            if (!node.sheet)
                return
            const p = sheetPoint(mouse)
            node.sheet.updateDrag(p.x, p.y, mouse.modifiers)
        }

        onReleased: function (mouse) {
            if (!node.sheet)
                return
            const p = sheetPoint(mouse)
            node.sheet.endDrag(p.x, p.y)
        }

        onCanceled: if (node.sheet) node.sheet.cancelDrag()

        // „Megjelenítés és szerkesztés" — a rendszer dupla kattintásán
        // (`picasa-eger-es-kijeloles.md` 9.: a Picasa nem méri maga).
        onDoubleClicked: if (node.controller) node.controller.viewAndEditSelection()
    }
}
