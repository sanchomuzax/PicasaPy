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
    //: A kép URL-je a MODELLBŐL (#1019). A kézi `"file:" + útvonal` fűzés
    //: Windowson érvénytelen URL-t ad (a meghajtóbetű PORTNAK látszik),
    //: `#`-es fájlnévnél pedig Linuxon is elvágja a nevet — mindkét esetben
    //: NÉMÁN, üres képpel. A szabályt a Qt `fromLocalFile`-ja adja.
    property url fileUrl
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

    // --- A vetett árnyék (#1021) --------------------------------------------
    //
    // Minden adat a LAPRÓL jön (`CollageSheet`): egy csempe és egy geometria
    // 350 csomópontra közösen. A csomópont nem számol árnyék-paramétert — az
    // a mag dolga (`collage/shadow.py`), és a mentett kép ugyanazt használja.

    //: A csempe `data:` URL-je; üres szöveg = ennek a témának nincs árnyéka
    //: (Többszörös exponálás), vagy a jelölőnégyzet ki van kapcsolva.
    property string shadowSource: ""
    //: A haló képpontban: ennyivel lóg túl az árnyék a csomópont dobozán.
    property int shadowSupport: 0
    //: A `BorderImage.border` — a haló kétszerese (az átmenet a doboz éle
    //: KÖRÜL zajlik, befelé is, kifelé is egy halónyit).
    property int shadowBorder: 0
    //: Az eltolás jobbra-le, a VÁSZON tengelyei szerint, képpontban.
    property real shadowOffsetX: 0
    property real shadowOffsetY: 0

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

    // --- A vetett árnyék eltolása (#1021) -----------------------------------
    //
    // ⚠️ Az eltolást VISSZA kell forgatni a csomópont saját rendszerébe. A
    // mag az eltolást a forgatás UTÁN adja hozzá (`draw_shadow`: a maszkot
    // elforgatja, majd `x + offset_x`-re teszi), tehát az eltolás a vászon
    // tengelyei szerint értendő. A csempe viszont a csomóponttal EGYÜTT
    // fordul, mert a gyereke — a két forgatás így ejti ki egymást. Aki ezt
    // kihagyja, annál az árnyék iránya képenként más lesz (a Képkupac
    // 0…−5°-ánál épp csak annyira, hogy „valami nem stimmel" érzést adjon).
    readonly property real _shadowLocalX:
        node.shadowOffsetX * Math.cos(node.theta)
        + node.shadowOffsetY * Math.sin(node.theta)
    readonly property real _shadowLocalY:
        -node.shadowOffsetX * Math.sin(node.theta)
        + node.shadowOffsetY * Math.cos(node.theta)

    // --- A SIMÍTÓ RÉTEG (#1016) ---------------------------------------------
    //
    // A #1010 a keret `Rectangle`-jére tette az `antialiasing`-et, és attól a
    // keret éle tényleg sima lett. A felhasználó mégis szaggatottat látott —
    // két olyan él maradt, amire az `antialiasing` NEM hat:
    //
    //   1. a `Image` TEXTÚRÁZOTT csomópont: a Qt rajta figyelmen kívül hagyja
    //      az `antialiasing`-et (`noborder`-nél ez a KÜLSŐ él);
    //   2. a képen lévő `clip: true` a Qt Quickben olló-/stencil-alapú, tehát
    //      kemény — forgatott elemen ez lépcsőzik (a fehér keret BELSŐ éle,
    //      ahol a fotó találkozik a kerettel).
    //
    // Mérve, valódi OpenGL-en (V3D, 5°-kal forgatott csomópont, átmeneti
    // árnyalatok száma az élen):
    //
    // | él | előtte | utána |
    // |---|---|---|
    // | `noborder` külső (fotó) éle           | **0** | 516 |
    // | `whiteborder` külső (keret) éle       | 514 | 641 |
    // | `whiteborder` belső (fotó/keret) éle  | **0** | 819 |
    //
    // A megoldás: a rajzot a csomópont SAJÁT, forgatás előtti rendszerében
    // egy textúrába rajzoljuk (`layer`), és a kész textúrát forgatva tesszük
    // ki. A vágás így tengelyre állítva történik (nincs ferde stencil-él), az
    // él simítását pedig a textúra szűrése (`layer.smooth`) és a réteg
    // többmintavételezése (`layer.samples`) adja.
    //
    // ⚠️ MINDHÁROM feltétel kell, külön-külön egyik sem elég. Ugyanazon a
    // próbajeleneten, a beállításokat egyesével rákapcsolva mérve:
    //
    // | beállítás | `noborder` külső él |
    // |---|---|
    // | csak `layer.enabled`               | **0** (ROSSZABB a réteg nélkülinél) |
    // | `+ layer.smooth`                   | **0** |
    // | `+ átlátszó perem`, `smooth` nélkül | **0** |
    // | `+ layer.smooth` ÉS átlátszó perem | 310 |
    //
    // Az átlátszó perem azért kell, mert a réteg textúrájának SZÉLÉN a Qt
    // `clamp`-el: perem nélkül az utolsó képpontsor teljesen átlátszatlan, a
    // szűrés így nem tud mibe átmenni, és az él ugyanolyan kemény marad.
    //
    // ⚠️ A `layer.sourceRect` kiterjesztése NEM jó megoldás erre (kipróbálva,
    // mérve): a réteg geometriája a KIRAJZOLT ELEM dobozához igazodik, tehát
    // a nagyobb forrás-téglalap BELEZSUGORODIK a dobozba — a 168 képpont
    // széles csempe 134-re ment össze. Ezért kap a rajz egy KÜLÖN, a doboznál
    // NAGYOBB tartót: így a perem valódi méretben van meg.
    //
    // A tartónak azért is nagyobbnak kell lennie, mert a vetett árnyék (#1021)
    // TÚLLÓG a dobozon (haló + eltolás) — perem nélkül a réteg levágná, és a
    // javítás egy másik hibát okozna.

    //: A rajz-tartó pereme képpontban: befogadja az árnyékot, és marad legalább
    //: 2 képpont ÁTLÁTSZÓ sáv a textúra szélén (ebbe tud a szűrés átmenni).
    readonly property int _layerMargin: node.shadowSource === ""
        ? 2
        : node.shadowSupport + 2 + Math.ceil(Math.max(
              Math.abs(node._shadowLocalX), Math.abs(node._shadowLocalY)))

    //: A réteg-alapú simítás felső darabszám-határa (spec 6.3 lépcsőinek
    //: mintájára). Képkockaidő mérve ezen a gépen (V3D, függőleges szinkron
    //: KIKAPCSOLVA, 900 × 650 vászon, MINDEN csomópont mozog képkockánként —
    //: a legrosszabb eset), medián, réteg nélkül → réteggel:
    //:
    //:     9 kép   5,4 → 5,9 ms
    //:    30 kép   5,7 → 6,0 ms   (terhelt gépen 11,6-ig szórt)
    //:   350 kép  16,3 → 21,4…24,5 ms
    //:
    //: A tipikus, 9–30 képes kollázs tehát gyakorlatilag ingyen kapja a sima
    //: élt; a 350 képes már ~40%-ot fizet érte, és csomópontonként külön
    //: textúrát is tart. A határ fölött ezért kikapcsol — ott a csempe már
    //: úgyis 60 képpont alatti, ahol az él simasága nem látszik.
    readonly property int smoothLayerLimit: 100

    //: Kell-e a réteg. Lap nélkül (próbaablak, teszt) mindig igen.
    readonly property bool useSmoothLayer:
        node.sheet ? node.sheet.nodeCount <= node.smoothLayerLimit : true

    // --- A rajz -------------------------------------------------------------

    Item {
        id: rajz
        objectName: "collageNodeLayer" + node.nodeIndex

        // A doboznál minden irányban egy peremnyivel nagyobb; a gyerekek
        // ezért a peremmel ELTOLVA ülnek a helyükre.
        x: -node._layerMargin
        y: -node._layerMargin
        width: node.width + 2 * node._layerMargin
        height: node.height + 2 * node._layerMargin

        layer.enabled: node.useSmoothLayer
        // A textúra SZŰRVE kerül ki (bilineárisan): enélkül a forgatott
        // textúra legközelebbi szomszéddal mintázódna, azaz pontosan olyan
        // lépcsős maradna, mint a réteg nélküli rajz.
        layer.smooth: true
        // A rétegen belüli rajz többmintavételezése. A vágás és a keret éle
        // tengelyre állított, de TÖRT képpont-koordinátán van (a fotó doboza
        // `szélesség / 1,1`), ezért a részleges fedettség itt is számít:
        // mérve 246 → 493 átmeneti árnyalat a keret belső élén.
        layer.samples: 4

        // A VETETT ÁRNYÉK (#1021) — a rajz-tartó ELSŐ gyereke, tehát a saját
        // kerete és képe alá kerül, a LEJJEBB lévő csomópontok fölé. Pontosan
        // ezt teszi a rajzoló is: „minden csempének a saját árnyéka
        // közvetlenül előtte rajzolódik" (`collage/nodes.py` `draw_nodes`) —
        // ettől esik a felül lévő kép árnyéka az alatta lévőre, és ez adja a
        // Képkupac mélységét.
        BorderImage {
            objectName: "collageNodeShadow" + node.nodeIndex
            visible: node.shadowSource !== ""
            source: node.shadowSource
            // A csempét MINDEN csomópont osztja: az URL azonos szövege miatt a
            // Qt egyetlen textúrát tart belőle.
            cache: true
            x: node._layerMargin + node._shadowLocalX - node.shadowSupport
            y: node._layerMargin + node._shadowLocalY - node.shadowSupport
            width: node.width + 2 * node.shadowSupport
            height: node.height + 2 * node.shadowSupport
            border.left: node.shadowBorder
            border.right: node.shadowBorder
            border.top: node.shadowBorder
            border.bottom: node.shadowBorder
            // A sarkok VÁLTOZATLANUL, az élek egy tengelyen nyújtva: ott a
            // lecsengés profilja állandó, tehát a nyújtás nem torzít. `Repeat`
            // itt hibás volna — a haló mintázata ismétlődne.
            horizontalTileMode: BorderImage.Stretch
            verticalTileMode: BorderImage.Stretch
            z: -1
        }

        // A keret lapja. `noborder`-nél nincs mit rajzolni, de a Rectangle
        // átlátszóan ott marad, hogy a mérete egyetlen helyen éljen.
        //
        // ⚠️ `antialiasing: true` (#1010) — a csomópont EL VAN FORGATVA (a
        // Képkupacnál 0…−5°), a Qt Quick pedig a SZÖGLETES `Rectangle` élét
        // alapból élsimítás NÉLKÜL rajzolja. Egy 5°-kal forgatott fehér
        // téglalapon, valódi OpenGL-háttéren mérve: élsimítás nélkül **0**
        // átmeneti árnyalat az élen (tiszta lépcső — ezt jelezte a felhasználó
        // a 0.8.1-en), bekapcsolva **466**.
        //
        // A `smooth` ide NEM való: az a TEXTÚRA szűrését állítja, nem a
        // geometria élét — a `Rectangle`-nek nincs textúrája.
        //
        // `noborder`-nél sem költség: a teljesen átlátszó `Rectangle`-höz a Qt
        // egyáltalán nem épít rajzoló csomópontot.
        Rectangle {
            objectName: "collageNodeFrame" + node.nodeIndex
            x: node._layerMargin
            y: node._layerMargin
            width: node.width
            height: node.height
            antialiasing: true
            color: node.border === "polaroid" ? "#d9d9d9"       // POLAROID_PAPER
                 : node.border === "whiteborder" ? "#eeeeee"    // WHITE_BORDER
                 : "transparent"
        }

        Image {
            objectName: "collageNodeImage" + node.nodeIndex
            visible: !node.missing
            x: node._layerMargin + node._photoX
            y: node._layerMargin + node._photoY
            width: node._photoWidth
            height: node._photoHeight
            //: ⚠️ NEM `"file:" + útvonal` (#1019) — ld. a `fileUrl`
            //: property-t; az URL a modellből jön, nem kézi fűzésből.
            source: node.missing || node.path === ""
                    || node.fileUrl === undefined
                    ? "" : node.fileUrl
            // A kért felbontás a darabszámmal lépcsőzik (spec 6.3): ettől nem
            // fullad meg a 350 képes kollázs — a Qt már a dekódolásnál
            // lekicsinyít, nem a teljes képet tartja a memóriában.
            sourceSize.width: node.thumbnailSize
            sourceSize.height: node.thumbnailSize
            asynchronous: true
            cache: true
            // A miniatűr majdnem sosem pont akkora, mint a doboz, tehát MINDIG
            // méreteződik — `smooth: true` nélkül a nagyítás nearest-neighbour
            // lenne, azaz szemcsés. A Qt Quickben ez az alapértelmezés; itt
            // kimondva szándék, hogy egy későbbi „optimalizálás" ne
            // kapcsolhassa ki némán (#1010).
            //
            // `antialiasing` viszont ide hiába kerülne: a Qt a textúrázott
            // csomópontokon (`Image`, `Canvas`) figyelmen kívül hagyja. A
            // forgatott kép külső élét ezért NEM ez simítja, hanem a rajz-tartó
            // rétege (#1016) — ld. a „SIMÍTÓ RÉTEG" szakaszt föntebb.
            smooth: true
            // A rajzoló alapesete a `fill=True` (a doboz hézag nélkül tele, a
            // túllógó rész vágva) — `collage/nodes.py` `fit_to_frame`.
            fillMode: Image.PreserveAspectCrop
            // A vágás a rétegen BELÜL, tengelyre állítva történik (#1016): a
            // stencil-él így nem ferde, tehát nem lépcsőzik. Réteg nélkül
            // (a küszöb fölött) marad a régi, kemény él — ott a csempe már
            // olyan kicsi, hogy nem látszik.
            clip: true
        }

        // Nem található kép: HELYKITÖLTŐ csempe (spec 9.4) — a lyuk látszódjon,
        // különben a felhasználó azt hiszi, ő törölte. A színek a rajzoló
        // `_missing_tile`-jából valók (BGR 200/120 → #c8c8c8 / #787878).
        Canvas {
            objectName: "collageNodeMissing" + node.nodeIndex
            visible: node.missing
            x: node._layerMargin
            y: node._layerMargin
            width: node.width
            height: node.height
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
            x: node._layerMargin + node._photoX
            width: node._photoWidth
            y: node._layerMargin + node._photoY + node._photoHeight
            height: Math.max(0, node.height - node._photoY - node._photoHeight)
        }

        // A kijelölés jelölése. A gyűrű a KÜLÖN overlay (`CollageRing`), ez csak
        // a keret — a rácsos témáknál (ahol nincs gyűrű) ez az EGYETLEN jel.
        //
        // A 2 képpontos keret UGYANAZZAL a szöggel forgatva rajzolódik, tehát
        // ugyanúgy kell neki az élsimítás, mint a keret lapjának (#1010).
        Rectangle {
            objectName: "collageNodeSelection" + node.nodeIndex
            x: node._layerMargin
            y: node._layerMargin
            width: node.width
            height: node.height
            antialiasing: true
            visible: node.selected
            color: "transparent"
            border.width: 2
            border.color: Theme.thumbSelection
        }
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
