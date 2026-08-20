import QtQuick

// A LAP — a kollázs élő vászna (#947, a #920 6/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **6.** és **7.1–7.5**.
//
// ## Miért itt van a húzás logikája
//
// Három hely tud húzást indítani: a kép maga, a gyűrű belseje és a gyűrű
// pereme. Mindhárom UGYANAZT az állapotgépet használja, ami itt él. Ha
// mindegyik a sajátját vinné, a három út előbb-utóbb elválna — és a
// felhasználó azt látná, hogy a kép máshova kerül attól függően, hol
// fogta meg. Ezért a `CollageNode` és a `CollageRing` egyetlen sort sem
// tud a mozgatásról: eseményt továbbítanak, itt dől el, mi történik.
//
// ## Az egységváltó
//
//     képpont = lapegység * (lap.szélesség / 1024)
//
// MINDKÉT tengelyen ugyanaz az osztó (spec 6.1) — a lap méretez, de nem
// torzít. Aki a függőlegest a lap MAGASSÁGÁVAL osztaná, álló formátumban
// némán összenyomná a kollázst, és a mentett JPEG mást mutatna.
//
// ## Amit a vászon SOHA nem csinál
//
// Nem számol elrendezést és nem módosít modellt. Minden állapotváltozás a
// vezérlő slotjain megy át (`moveNode`, `transformNode`, `swapNodes`,
// `raiseNodeToTop`, `setCollageSelection`) — így a `.cxf` mentése, a
// visszavonás és a felület pontosan ugyanazt az adatot látja.
//
// ## ⚠️ A gyökér azonosítója `lap`, és NEM `sheet` — ez szándékos
//
// A `CollageNode` és a `CollageRing` saját `sheet` property-t visel, és a
// delegate-ben a SAJÁT property árnyékolja az azonos nevű külső azonosítót.
// Amíg a gyökér `sheet` volt, a `unit: sheet ? sheet.unit : 0` a delegate
// még be nem állított saját property-jére kötött: `unit` = 0 lett, minden
// csomópont az origóba, 1 × 1 képpont méretben. Fordítási hiba nélkül, néma
// hibaüzenet nélkül. Aki visszanevezi, ezt hozza vissza.
Item {
    id: lap

    property var controller: null

    readonly property var nodesModel: controller ? controller.collageNodes : null
    readonly property int nodeCount: controller ? controller.collageClipCount : 0
    readonly property var capabilities: controller ? controller.collageCapabilities : ({})

    //: Képpont / lapegység (spec 6.1). A lap belső szélessége 1024 EGYSÉG.
    readonly property real unit: width > 0 ? width / 1024 : 0

    // --- A vetett árnyék (#1021) --------------------------------------------
    //
    // A #977 az árnyékot a MAGBA tette, így a mentett kép azóta jó — az élő
    // vászon viszont nem rajzolt semmit, és a felhasználó a v0.8.4-en
    // jelezte, hogy a jelölőnégyzet kapcsolgatása nem csinál semmit.
    //
    // A vezérlő két dolgot ad: a geometriát LAPEGYSÉGBEN (`collageShadow` —
    // ugyanabból a `render_settings()`-ből, amivel a MENTÉS dolgozik) és a
    // kirajzolható CSEMPÉT (`collageShadowSprite`). A csempe egy elmosott
    // téglalap, amit a `BorderImage` kilenc szeletre bontva nyújt: az árnyék
    // szeparábilis, ezért ez nem közelítés, hanem pontos rekonstrukció
    // (`collage/shadow_sprite.py`, 2/255 alatti eltéréssel mérve).
    //
    // ⚠️ Shader (`MultiEffect`) SZÁNDÉKOSAN nincs: a `QtQuick.Effects` modul
    // a felhasználó gépén NINCS telepítve, a CI-n (pip-es PySide6) viszont
    // igen — egy shaderes megoldás zöld CI mellett hagyta volna árnyék
    // nélkül épp azt a gépet, ahonnan a bejelentés jött.

    //: Az árnyék paraméterei LAPEGYSÉGBEN; üres térkép = nincs árnyék.
    //:
    //: ⚠️ A `!== undefined` őr a #305 szabálya, és nem elmélet: a
    //: `test_collage_panel_layout_945.py` vezérlő-kettőse CSAK a geometriai
    //: property-ket viseli, ott a `collageShadow` `undefined`. Enélkül 52
    //: teszt bukott el „Cannot read property 'alpha' of undefined"-dal.
    readonly property var shadow:
        (controller && controller.collageShadow !== undefined)
        ? controller.collageShadow : ({})

    //: Van-e mit rajzolni. Az `alpha` egyben a térkép jelenlétének jelzője:
    //: üres térképnél `undefined`.
    readonly property bool shadowVisible: shadow.alpha !== undefined && unit > 0

    //: A csempe és a hozzá tartozó szegélyméret EGY kérésből — két külön
    //: forrásból a kettő elválna, és az árnyék elcsúszna a csempéjétől.
    readonly property var shadowSprite: shadowVisible
        ? controller.collageShadowSprite(shadow.blur * unit, shadow.alpha)
        : null

    //: A miniatűr kért éle a DARABSZÁMBÓL lépcsőzve (spec 6.3, `spec[0x30]`).
    //: Ez az, amitől a 350 képes kollázs nem fullad meg.
    readonly property int thumbnailSize:
          nodeCount <= 99 ? 2276
        : nodeCount <= 199 ? 256
        : nodeCount <= 349 ? 128
        : 64

    // --- A húzás állapota ---------------------------------------------------

    //: "" | "move" | "knob"
    property string dragMode: ""
    property int dragIndex: -1

    //: Volt-e VALÓDI egérmozdulat a lenyomás óta. A csere gesztusa az
    //: EJTÉS egy másik képre (7.3), nem a kattintás: a képkupac képei fedik
    //: egymást, tehát mozdulat-őr nélkül minden kijelölő kattintás némán
    //: kicserélne két fájlt, és a felhasználó azt látná, hogy a képei
    //: maguktól ugrálnak.
    property bool _dragMoved: false

    //: Fogási eltolás a csomópont KÖZEPÉHEZ képest, lapképpontban (7.3).
    property real _grabX: 0
    property real _grabY: 0
    //: A csomópont közepe a lenyomás pillanatában, LAPEGYSÉGBEN — a csere
    //: ide teszi vissza a rést (ld. `endDrag`).
    property real _pressCenterX: 0
    property real _pressCenterY: 0

    //: A fogantyú (7.4) kiinduló adatai.
    property real _knobCenterX: 0
    property real _knobCenterY: 0
    property real _knobPressDist: 1
    property real _knobPressScale: 1
    property real _knobScale: 1
    property real _knobTheta: 0

    //: A Shift-tartomány horgonya (`picasa-eger-es-kijeloles.md` 4/c).
    property int _selectionAnchor: -1

    //: A húzás közbeni feliratok (7.4). Csak a FOGANTYÚHOZ tartoznak.
    readonly property bool dragFeedbackVisible: dragMode === "knob"
    property int angleCaption: 0
    property int scaleCaption: 100

    // --- A háttér (spec 6.4) ------------------------------------------------

    Rectangle {
        objectName: "collageSheetBackground"
        anchors.fill: parent
        // A rajzoló (`picasa_render._canvas`) egyszínű lappal indul, tehát a
        // vászon is azt mutatja — így a WYSIWYG nem hazudik.
        color: lap.controller && lap.controller.collageBackgroundColor
               ? lap.controller.collageBackgroundColor : "#ffffff"
        border.width: 1
        border.color: "#9a9a9a"
    }

    Image {
        objectName: "collageSheetBackgroundImage"
        anchors.fill: parent
        anchors.margins: 1
        visible: lap.controller
                 && lap.controller.collageBackgroundMode === "image"
                 && lap.controller.collageBackgroundImage !== ""
        //: ⚠️ NEM `"file:" + útvonal`: a kézi fűzés `#`-es fájlnévnél Linuxon
        //: is levágja a nevet, Windowson pedig érvénytelen URL-t ad (#1009).
        //: A null-őr a #305 szabálya: a lebontáskor és a teszt-kettősöknél a
        //: hiányzó property `undefined`-ot adna, amit a `url` nem fogad el.
        source: visible && lap.controller.collageBackgroundImageUrl !== undefined
                ? lap.controller.collageBackgroundImageUrl : ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        clip: true
    }
    //: A háttérkép TOMPÍTVA jelenik meg (`DimmedBitmapTheme`, spec 6.4):
    //: fényerő −0,15 — az átlapolt fekete réteg ennek a felületi megfelelője.
    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        visible: lap.controller
                 && lap.controller.collageBackgroundMode === "image"
                 && lap.controller.collageBackgroundImage !== ""
        color: "#26000000"
    }

    // --- A csomópontok ------------------------------------------------------

    // ⚠️ A delegate-ekben MINDEN külső hivatkozás null-őrt kap (#305). Nem
    // védekező stílus: a lebontáskor a `Repeater` előbb semmisül meg, mint a
    // gyerekei, és a lap egy pillanatra `null`-ként látszik. Őr nélkül
    // ez a teszteket buktató „TypeError: Cannot read property … of null"
    // üzenet-özön, amit a #305-ös figyelő elkap.
    Repeater {
        id: nodeRepeater
        model: lap.nodesModel
        delegate: CollageNode {
            sheet: lap
            controller: lap ? lap.controller : null
            nodeIndex: index
            unit: lap ? lap.unit : 0
            path: model.path
            fileUrl: model.fileUrl !== undefined ? model.fileUrl : ""
            // #995: a Többszörös exponálás rétegsorrend szerinti keverése
            tileOpacity: model.tileOpacity !== undefined ? model.tileOpacity : 1.0
            centerX: model.centerX
            centerY: model.centerY
            nodeWidth: model.width
            nodeHeight: model.height
            theta: model.theta
            border: model.border
            caption: model.caption
            selected: model.selected
            missing: model.missing
            captionsVisible: (lap && lap.controller)
                             ? lap.controller.collageCaptions : true
            thumbnailSize: lap ? lap.thumbnailSize : 256
            // #1021 — az árnyék MINDEN adata a lapról jön: egy csempe,
            // egy geometria, 350 csomópontra közösen.
            shadowSource: (lap && lap.shadowSprite) ? lap.shadowSprite.url : ""
            shadowSupport: (lap && lap.shadowSprite) ? lap.shadowSprite.support : 0
            shadowBorder: (lap && lap.shadowSprite) ? lap.shadowSprite.border : 0
            shadowOffsetX: (lap && lap.shadowVisible) ? lap.shadow.offsetX * lap.unit : 0
            shadowOffsetY: (lap && lap.shadowVisible) ? lap.shadow.offsetY * lap.unit : 0
        }
    }

    // A gyűrűk KÜLÖN rétegben, a képek FÖLÖTT: a méretük képernyő-egységben
    // állandó, tehát nem lehetnek a (forgatott, méretezett) kép gyerekei.
    Repeater {
        id: ringRepeater
        model: lap.nodesModel
        delegate: CollageRing {
            sheet: lap
            controller: lap ? lap.controller : null
            nodeIndex: index
            theta: model.theta
            visible: model.selected && lap !== null
                     && lap.capabilities.ring === true
            x: (lap ? model.centerX * lap.unit : 0) - width / 2
            y: (lap ? model.centerY * lap.unit : 0) - height / 2
            z: 10000 + index
        }
    }

    // --- Kijelölés (7.1) ----------------------------------------------------

    function clickSelect(index, modifiers) {
        if (!controller)
            return
        const jelenlegi = controller.collageSelection.slice()
        if (modifiers & Qt.ControlModifier) {
            const helye = jelenlegi.indexOf(index)
            if (helye >= 0)
                jelenlegi.splice(helye, 1)
            else
                jelenlegi.push(index)
            controller.setCollageSelection(jelenlegi)
            _selectionAnchor = index
            return
        }
        if ((modifiers & Qt.ShiftModifier) && _selectionAnchor >= 0) {
            // Tartomány a RAJZOLÁSI sorrend szerint (spec 7.1).
            const eleje = Math.min(_selectionAnchor, index)
            const vege = Math.max(_selectionAnchor, index)
            let tartomany = []
            for (let i = eleje; i <= vege; ++i)
                tartomany.push(i)
            controller.setCollageSelection(tartomany)
            return
        }
        controller.setCollageSelection([index])
        _selectionAnchor = index
    }

    // --- Mozgatás (7.3) -----------------------------------------------------

    function beginMove(index, sx, sy, modifiers) {
        if (!controller || index < 0 || index >= nodeCount)
            return
        const elem = nodeRepeater.itemAt(index)
        if (!elem)
            return
        // A fogási eltolást MÉG az esetleges rétegváltás előtt vesszük: a
        // rétegváltás a csomópont helyzetét nem érinti, csak a sorszámát.
        _grabX = sx - elem.centerX * unit
        _grabY = sy - elem.centerY * unit
        _pressCenterX = elem.centerX
        _pressCenterY = elem.centerY

        let cel = index
        if (modifiers & Qt.AltModifier) {
            // ⚠️ Az `Alt` NEM másol és nem klónoz (spec 14.): a kép a
            // legfelső rétegbe ugrik, és ONNAN mozog tovább. Ha már ott
            // van, a vezérlő nem csinál semmit — nincs villanás.
            controller.raiseNodeToTop(index)
            cel = nodeCount - 1
        }
        dragIndex = cel
        dragMode = "move"
        _dragMoved = false
    }

    function updateMove(sx, sy, modifiers) {
        if (dragMode !== "move" || !controller)
            return
        // NINCS elhúzási küszöb (spec 7.3): az első egérmozdulat már mozgat.
        // A 10 képpontos küszöb a fájlrendszer felé menő OLE-vonszoláshoz
        // tartozik, nem ide. A jelző tehát NEM küszöb: azt jegyzi meg, hogy
        // volt-e egyáltalán mozdulat, mert csere csak EJTÉSKOR történhet.
        _dragMoved = true
        controller.moveNode(dragIndex, (sx - _grabX) / unit, (sy - _grabY) / unit)
    }

    // --- Forgatás + méretezés EGY fogantyúval (7.4) -------------------------

    function beginKnob(index, sx, sy) {
        if (!controller || index < 0 || index >= nodeCount)
            return
        const elem = nodeRepeater.itemAt(index)
        if (!elem)
            return
        _knobCenterX = elem.centerX * unit
        _knobCenterY = elem.centerY * unit
        const dx = sx - _knobCenterX
        const dy = sy - _knobCenterY
        _knobPressDist = Math.max(1e-6, Math.sqrt(dx * dx + dy * dy))
        const alap = controller.collageBaseNodeWidth
        _knobPressScale = alap > 0 ? elem.nodeWidth / alap : 1
        _knobScale = _knobPressScale
        _knobTheta = elem.theta
        dragIndex = index
        dragMode = "knob"
        _dragMoved = false
        angleCaption = controller.collageAngleCaption(_knobTheta)
        // „A méretarány a lenyomás pillanatában 100" (spec 7.4).
        scaleCaption = 100
    }

    function updateKnob(sx, sy, modifiers) {
        if (dragMode !== "knob" || !controller)
            return
        const dx = sx - _knobCenterX
        const dy = sy - _knobCenterY

        // ⚠️ A módosítót a húzás KÖZBEN kell kérdezni, nem a lenyomáskor
        // eltárolni (spec 7.4, `GetAsyncKeyState`). Aki elmenti, más
        // programot ír: aki húzás közben engedi el a Ctrl-t, annál a
        // forgatás onnantól él.
        //
        // A `Ctrl` a FORGATÁST, az `Alt` a MÉRETEZÉST kapcsolja ki. Egyik
        // sem „mód"; mindkettőt nyomva tartva a fogantyú nem csinál semmit.
        if (!(modifiers & Qt.ControlModifier)) {
            // `atan2(−dx, dy)` — a +y tengelytől mér, a 0° a 12 óra iránya.
            _knobTheta = Math.atan2(-dx, dy)
        }
        if (!(modifiers & Qt.AltModifier)) {
            const tav = Math.sqrt(dx * dx + dy * dy)
            _knobScale = _knobPressScale * tav / _knobPressDist
        }
        controller.transformNode(dragIndex, _knobScale, _knobTheta)
        // A feliratokat a KÉSZ formázók adják (`collage/canvas.py`) — a
        // szög kiírása előjelet vált, a kerekítés `floor(x + 0,5)`.
        angleCaption = controller.collageAngleCaption(_knobTheta)
        scaleCaption = controller.collageScaleCaption(_knobScale, _knobPressScale)
    }

    // --- Közös bejáratok ----------------------------------------------------

    function updateDrag(sx, sy, modifiers) {
        if (dragMode === "move")
            updateMove(sx, sy, modifiers)
        else if (dragMode === "knob")
            updateKnob(sx, sy, modifiers)
    }

    function endDrag(sx, sy) {
        if (dragMode === "move")
            endMove(sx, sy)
        else
            cancelDrag()
    }

    function endMove(sx, sy) {
        if (dragMode !== "move" || !controller) {
            cancelDrag()
            return
        }
        if (!_dragMoved) {
            // Kattintás ejtés nélkül: a kijelölés már megtörtént a
            // lenyomáskor, más dolgunk nincs.
            cancelDrag()
            return
        }
        const huzott = dragIndex
        const fogado = nodeIndexAt(sx, sy, huzott)
        cancelDrag()
        if (fogado < 0)
            return
        // Egy képet a másikra ejtve a kettő KICSERÉLŐDIK — és ez
        // kifejezetten NEM áthelyezés (spec 7.3). Ezért a húzott rést
        // visszatesszük oda, ahonnan indult: különben a saját képünk a
        // fogadó tetején maradna, ami nem csere, hanem takarás.
        controller.moveNode(huzott, _pressCenterX, _pressCenterY)
        controller.swapNodes(huzott, fogado)
    }

    function cancelDrag() {
        dragMode = ""
        dragIndex = -1
        _dragMoved = false
    }

    //: A megadott pont alatti LEGFELSŐ csomópont, a húzottat kihagyva.
    //: Felülről lefelé keres, mert a lista VÉGE van legfelül.
    function nodeIndexAt(sx, sy, exclude) {
        for (let i = nodeCount - 1; i >= 0; --i) {
            if (i === exclude)
                continue
            const elem = nodeRepeater.itemAt(i)
            if (!elem)
                continue
            const p = lap.mapToItem(elem, sx, sy)
            if (elem.contains(Qt.point(p.x, p.y)))
                return i
        }
        return -1
    }
}
