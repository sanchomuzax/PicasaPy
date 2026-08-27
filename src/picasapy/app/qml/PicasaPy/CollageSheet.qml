import QtQuick

// A LAP — a kollázs élő vászna (#947, a #920 6/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **6.** és **7.1–7.5**.
//
// ## Miért itt van a húzás logikája
//
// Három hely tud húzást indítani: a kép teste, a gyűrű belseje és a gyűrű
// pereme. Az eseményeket mindegyik ide továbbítja, de a GESZTUSUK különböző:
// a kép teste 10 px után cserét élesít, a gyűrű belseje küszöb nélkül mozgat,
// a pereme pedig forgat és méretez (spec 5.2–5.2/c). A két első út már
// lenyomáskor szétválik; felengedéskor sem futhatnak közös csereágba.
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
    // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
    // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
    readonly property int nodeCount: (controller && controller.collageClipCount !== undefined)
        ? controller.collageClipCount : 0
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
    //: ⚠️ #305-őr a `controller`-re is: a `shadowVisible` a `shadow` térképből
    //: dolgozik, ami a lebontás pillanatában még a RÉGI értéket tarthatja,
    //: miközben a `controller` már `null` — ilyenkor ez a kötés
    //: „Cannot read property 'collageShadowSprite'" hibát dobna a
    //: fixture-életciklusban (a #1260 őre ezt bukásként jelenti). A CI-n
    //: elő is jött, helyben nem: időzítésfüggő.
    readonly property var shadowSprite: (controller && shadowVisible)
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

    //: "" | "move" | "swap-pending" | "swap" | "knob"
    property string dragMode: ""
    property int dragIndex: -1
    //: Alt-tal a húzott kép már lenyomáskor vizuálisan legfelül van; a
    //: modellbeli sorrend a felengedéskor követi, hogy a Repeater szerepei
    //: ne cserélődjenek ki a még lenyomott MouseArea alatt.
    property bool _raiseMoveOnEnd: false
    readonly property int moveRaisedIndex:
        dragMode === "move" && _raiseMoveOnEnd ? dragIndex : -1

    //: A `CollageNodeHandler` cseregesztusának küszöbe. Bináris bizonyíték:
    //: `0xcf3b28 = 10.0f`, összehasonlítás `0x0086071b` (`0x008606d0`).
    //: Kizárólag a KÉP TESTÉRE vonatkozik; a gyűrűs mozgatásra nem.
    readonly property real dragStartThresholdPx: 10.0

    //: Fogási eltolás a csomópont KÖZEPÉHEZ képest, lapképpontban (7.3).
    property real _grabX: 0
    property real _grabY: 0
    //: A kép testén történt lenyomás helye LAP-KÉPPONTBAN. A csere küszöbe
    //: mindig ehhez mérődik, nem az előző egéreseményhez (spec 5.2/c).
    property real _swapPressX: 0
    property real _swapPressY: 0

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

    // --- Az egérmutató helye a gyűrűk elhalványításához (#1000) -------------
    //
    // Spec: `picasa-kollazs-felulet.md` **5.1/b** (`RingNodeFadeHandler`,
    // `0x007e6220`). A gyűrű LÉTE a kijelöléshez kötött, a LÁTHATÓSÁGA
    // viszont az egérmutatóhoz — hogy rajta van-e a mutató a képen, azt a
    // `CollageRing` maga dönti el (12 képpont tűréssel, a saját, forgatott
    // dobozára). A lap ehhez egyetlen dolgot ad: hol a mutató.
    //
    // ⚠️ EGY `HoverHandler` van, a lapon — nem csomópontonként egy. A
    // `HoverHandler` nem nyeli el a gombeseményeket, és a mutató alatti
    // `MouseArea`-k (a képeké, a gyűrűké) sem fogják el előle a hovert
    // (mérve: a szülőn ülő kezelő a gyerek `MouseArea` fölött is megkapja).
    // Csomópontonkénti kezelő 350 képnél 350 kezelőt jelentene ugyanezért.

    //: Az egérmutató helye LAP-KÉPPONTBAN.
    property real hoverX: 0
    property real hoverY: 0
    //: A lapon van-e egyáltalán a mutató. Ha nincs, egyetlen gyűrű sem
    //: számít „hoverelt"-nek — a `hoverX`/`hoverY` ilyenkor elavult.
    property bool hoverActive: false

    //: A ZÁR (`RingNodeFadeLockHandler`, `0x007e6390`): húzás közben az
    //: elhalványítás időzítője fel van függesztve, tehát a gyűrű látható
    //: marad akkor is, ha a mutató kifut a képből. Enélkül a felhasználó
    //: épp azt a fogantyút veszítené szem elől, amivel dolgozik.
    readonly property bool ringFadeLocked: dragMode !== ""

    HoverHandler {
        id: hoverFigyelo
        onPointChanged: {
            lap.hoverX = point.position.x
            lap.hoverY = point.position.y
        }
        onHoveredChanged: lap.hoverActive = hovered
    }

    //: A mutató helyének frissítése LENYOMOTT gombbal is.
    //:
    //: ⚠️ Amíg egy `MouseArea` fogja az egeret, a Qt `MouseMove`-ot küld,
    //: NEM `HoverMove`-ot: a `HoverHandler` ilyenkor nem frissül. A zár
    //: alatt ez nem baj (a gyűrű úgyis látszik) — a felengedés
    //: pillanatában viszont a zár feloldódik, és ha a mutató helye a húzás
    //: KEZDETÉN ragadt volna, a gyűrű a lap túlsó felén is „hoverelt"
    //: maradna, amíg a felhasználó meg nem mozdítja az egeret.
    function trackDragHover(sx, sy) {
        hoverX = sx
        hoverY = sy
        hoverActive = true
    }

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
            //: A gyűrű LÉTE — a kijelöléshez kötött. A LÁTHATÓSÁGA ettől
            //: külön él (#1000): azt a gyűrű `opacity`-je adja.
            ringExists: model.selected && lap !== null
                        && lap.capabilities.ring === true
            //: A csomópont doboza a hover találatvizsgálatához (#1000).
            unit: lap ? lap.unit : 0
            centerX: model.centerX
            centerY: model.centerY
            nodeWidth: model.width
            nodeHeight: model.height
            x: (lap ? model.centerX * lap.unit : 0) - width / 2
            y: (lap ? model.centerY * lap.unit : 0) - height / 2
            z: 10000 + index
        }
    }

    // A CSOPORT-ELEM (#1170) — a képesség-maszk 6. bitje az eredetiben is
    // KÜLÖN, overlay feldolgozási ágba teszi, a szülőhöz kötött bejárás
    // helyett. Ezért nem a csomópontok gyereke, hanem a legfelső réteg: a
    // saját `z`-je minden `CollageNode`-énál magasabb. A geometriát a
    // vezérlő adja lapegységben (`collageGroupRect`); a lap a
    // mértékegységet és a képesség-térképet adja hozzá.
    CollageGroupNode {
        sheet: lap
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

        _raiseMoveOnEnd = false
        if ((modifiers & Qt.AltModifier) && index !== nodeCount - 1) {
            // ⚠️ Az `Alt` NEM másol és nem klónoz (spec 14.): a kép a
            // legfelső rétegbe ugrik, és ONNAN mozog tovább. A `z` már
            // lenyomáskor ezt mutatja; a sorrend felengedéskor rögzül.
            _raiseMoveOnEnd = true
        }
        dragIndex = index
        dragMode = "move"
    }

    function updateMove(sx, sy, modifiers) {
        if (dragMode !== "move" || !controller)
            return
        // NINCS elhúzási küszöb (spec 5.2): az első egérmozdulat már mozgat.
        controller.moveNode(dragIndex, (sx - _grabX) / unit, (sy - _grabY) / unit)
    }

    // --- Csere a kép testének vonszolásával (5.2/b–c) ----------------------

    function beginSwap(index, sx, sy, modifiers) {
        if (!controller || index < 0 || index >= nodeCount) {
            cancelDrag()
            return
        }
        // A Ctrl+kattintás kijelölést billent, de a vonszolást kifejezetten
        // NEM élesíti (`node[0x5c] = 0`, `0x00860b31`).
        if (modifiers & Qt.ControlModifier) {
            cancelDrag()
            return
        }
        dragIndex = index
        dragMode = "swap-pending"
        _swapPressX = sx
        _swapPressY = sy
    }

    function updateSwap(sx, sy) {
        if (dragMode !== "swap-pending" && dragMode !== "swap")
            return
        if (dragMode === "swap")
            return
        const dx = sx - _swapPressX
        const dy = sy - _swapPressY
        // „10 képponton TÚL": maga a 10 px még nem indít vonszolást.
        if (Math.sqrt(dx * dx + dy * dy) > dragStartThresholdPx)
            dragMode = "swap"
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
        // #1000: a zár alatt is tudnunk kell, hol a mutató — a feloldás
        // pillanatában ebből dől el, marad-e látható a gyűrű.
        trackDragHover(sx, sy)
        if (dragMode === "move")
            updateMove(sx, sy, modifiers)
        else if (dragMode === "swap-pending" || dragMode === "swap")
            updateSwap(sx, sy)
        else if (dragMode === "knob")
            updateKnob(sx, sy, modifiers)
    }

    function endDrag(sx, sy) {
        // #1000: MÉG a zár feloldása (`cancelDrag`) ELŐTT — a gyűrű a
        // felengedés helyéből számol, nem a húzás kezdetéből.
        trackDragHover(sx, sy)
        if (dragMode === "move") {
            const huzott = dragIndex
            const emel = _raiseMoveOnEnd
            cancelDrag()
            if (emel && controller)
                controller.raiseNodeToTop(huzott)
        } else if (dragMode === "swap")
            endSwap(sx, sy)
        else
            cancelDrag()
    }

    function endSwap(sx, sy) {
        if (dragMode !== "swap" || !controller) {
            cancelDrag()
            return
        }
        const huzott = dragIndex
        const fogado = nodeIndexAt(sx, sy, huzott)
        cancelDrag()
        if (fogado < 0)
            return
        // A kép teste nem mozgatta el a csomópontot: csak a két útvonal
        // cserél helyet, a fogadó geometriája változatlan marad (5.2/b).
        controller.swapNodes(huzott, fogado)
    }

    function cancelDrag() {
        dragMode = ""
        dragIndex = -1
        _raiseMoveOnEnd = false
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
