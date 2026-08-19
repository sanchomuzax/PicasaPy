import QtQuick

// A vászon-oldal: a lap, a körülötte lévő üres terület és a húzás közbeni
// visszajelzés (#947, a #920 6/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **6.**, **7.1** és **7.4**.
//
// ## A geometria NEM ezé a fájlé
//
// A vászon helyét és a lap téglalapját a `CollagePanel.qml` méretezési
// törvénye adja (#945): a bal hasáb fix, a vászon-oldal nyúlik, a lap az
// oldalformátum arányával a `previewinset`-be illesztve, középen. Ez a
// fájl azt a téglalapot KAPJA (`sheetRect`), nem számolja — így a #945
// 52 tesztje a helyén marad, és a törvény egyetlen helyen él.
//
// ## Amiért a billentyűk itt vannak
//
// A Ctrl+A / Ctrl+D / Del a vászon parancsai, de a fókusz a panelé (az
// Esc-hez kell, #945). A panel ezért `Keys.forwardTo`-val ide továbbít —
// így nincs két fókuszgazda, és az Esc továbbra is bezár.
Item {
    id: canvas

    property var controller: null

    //: A lap téglalapja a VÁSZON koordinátarendszerében (a paneltől).
    property rect sheetRect: Qt.rect(0, 0, 0, 0)

    // A kijelölés megszüntetése az ÜRES területen (`CollageDeselectHandler`,
    // spec 7.1). A legalsó rétegben ül, ezért a képek és a gyűrűk
    // elfogják előle az eseményt — csak az marad neki, amit tényleg senki
    // nem használ. A lapnak magának nincs egérterülete, tehát a lap üres
    // része is ide esik.
    MouseArea {
        objectName: "collageDeselectArea"
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onClicked: if (canvas.controller) canvas.controller.selectNoNodes()
    }

    // --- A VÁGÁS: `previewclip` (#1027) -------------------------------------
    //
    // A `.tre` a vászon-láncban KÜLÖN vágó konténert tart
    // (`collagepanel.tre` 160–164. és 238–250. sor):
    //
    //     previewcontainer            ; kitölti a jobb konténert
    //      └ previewclip              ; mind a négy élen 0 → PONTOSAN akkora
    //         └ previewinset          ; −(12, 35, 12, 35)
    //            ├ previewshadow      ; A LAP
    //            └ previewroot        ; a kép-CSOMÓPONTOK
    //
    // Két dolog dönti el, hogy a vágás ide, a VÁSZONKERET szintjére való:
    //
    // 1. a `previewroot` — amiben a képek ülnek — a lap TESTVÉRE, nem a
    //    gyereke: a lap tehát nem is tudná elvágni őket;
    // 2. a `previewclip` geometriailag AZONOS a `previewcontainer`-rel. Egy
    //    azonos méretű, külön elem egyetlen okból létezik: ez a vágás
    //    határa. (Közvetett megerősítés: az `enableclip` az egész fájlban
    //    egyszer szerepel, a `tabbase`-en, 0 értékkel — a vágás alapból be
    //    van, és ahol nem kellett, külön kimondták.)
    //
    // ⚠️ Aki a LAPNÁL vagy a `previewinset`-nél vágna, a 12/35 képpontos
    // behúzási sávot is levágná — az eredeti viszont a keret széléig
    // MUTATJA a lapról túllógó képet.
    //
    // ## Miért csak a lap van a vágóban, és nem a négy gombcsoport
    //
    // Az eredetiben a négy csoport a lap gyereke, tehát a `previewclip`-en
    // belül van. Nálunk viszont a VÁSZON gyerekei, a lap téglalapjából
    // számolva (ld. lent) — és ez itt kapóra jön: ha a vágó föléjük kerülne,
    // 800 × 534-es panelen a bal oldali oszlop 7 képponttal elvágódna. (Ott
    // a lap a `previewinset` teljes SZÉLESSÉGÉT kitölti, tehát a bal széle
    // 12 px-re van a kerettől, a 17 px széles oszlop pedig további 2 px
    // réssel elé kerül: 12 − 2 − 17 = −7. Ugyanez az eredetiben is
    // megtörténik — a mi eltérésünk tehát tudatos, és a felhasználó javára
    // szól.)
    //
    // ⚠️ A vágás TENGELYPÁRHUZAMOS téglalapra megy (a vászonkeret nincs
    // forgatva), tehát a Qt ollóval (scissor) intézi: nem hoz létre külön
    // rajzfelületet, és nem nyúl a csomópontok saját élsimításához (#1016).
    // ⚠️ A vágó a LAP téglalapjára megy, NEM a teljes vászonra (#1027 → javítva).
    //
    // Az első nekifutás a vászon egészét vágta (`anchors.fill: parent`), és a
    // felhasználó jogosan jelezte, hogy a képek TOVÁBBRA IS kilógnak: a lapon
    // kívülre csúszott csempe a vásznon belül maradt, tehát nem vágódott el.
    // Amit ő lát, az a LAP széle (a színes háttér), nem a vászonkeret.
    //
    // A négy lebegő gombcsoport ezt NEM sínyli meg: azok a vágó TESTVÉREI
    // (lentebb deklarálva), nem a gyerekei — a vágás elvi lehetőséggel sem
    // éri el őket.
    Item {
        objectName: "collageSheetClip"
        x: canvas.sheetRect.x
        y: canvas.sheetRect.y
        width: canvas.sheetRect.width
        height: canvas.sheetRect.height
        clip: true

        CollageSheet {
            id: sheet
            objectName: "collageSheet"
            controller: canvas.controller
            anchors.fill: parent
            visible: width > 0 && height > 0
        }
    }

    // --- A lap körüli négy gombcsoport (#948) -------------------------------
    //
    // A `.tre` szerint mind a négy a `previewshadow` (= a lap) GYEREKE, tehát
    // a lappal együtt mozog: oldalformátum- vagy ablakméret-váltáskor is a
    // lap szélén marad (spec 2.4). Nálunk nem gyerekként, hanem a lap
    // TÉGLALAPJÁBÓL számolva ülnek a helyükre — geometriailag ugyanaz, de a
    // lap egérkezelése és a `Repeater`-ei érintetlenek maradnak.
    //
    // A két oldalsó oszlop `m_hidden`: a láthatóságukat maguk döntik el a
    // kijelölésből (ld. `CollageSnapColumn.qml`).

    CollageActionRow {
        controller: canvas.controller
        // `m_centerX` + `YConstraint 1, 0, -2`: az ALSÓ éle 2 px-re a lap
        // teteje FÖLÖTT
        x: canvas.sheetRect.x + (canvas.sheetRect.width - width) / 2
        y: canvas.sheetRect.y - 2 - height
    }

    CollageRandomRow {
        controller: canvas.controller
        // `m_centerX` + `YConstraint 0, 1, 2`: a FELSŐ éle 2 px-re a lap
        // alja ALATT
        x: canvas.sheetRect.x + (canvas.sheetRect.width - width) / 2
        y: canvas.sheetRect.y + canvas.sheetRect.height + 2
    }

    CollageSnapColumn {
        controller: canvas.controller
        // `m_centerY` + `XConstraint 1, 0, -2`: a JOBB éle 2 px-re a lap bal
        // szélétől BALRA
        x: canvas.sheetRect.x - 2 - width
        y: canvas.sheetRect.y + (canvas.sheetRect.height - height) / 2
    }

    CollageZOrderColumn {
        controller: canvas.controller
        // `m_centerY` + `XConstraint 0, 1, 2`: a BAL éle 2 px-re a lap jobb
        // szélétől JOBBRA
        x: canvas.sheetRect.x + canvas.sheetRect.width + 2
        y: canvas.sheetRect.y + (canvas.sheetRect.height - height) / 2
    }

    // --- A három helyi menü (#948) ------------------------------------------

    CollageContextMenus {
        id: contextMenus
        controller: canvas.controller
    }

    // A jobb gomb ÚTJA. Egyetlen egérterület dönti el, melyik menü való a
    // kattintás alá — a `CollageNode` és a `CollageSheet` egy sort sem tud
    // róla, ahogy a húzásról sem.
    //
    // ⚠️ `acceptedButtons: Qt.RightButton`: a BAL gombos eseményeket ez a
    // terület nem fogadja el, tehát változatlanul lejutnak a képekre, a
    // gyűrűre és a kijelölés-megszüntető területre. Ha bal gombot is
    // elfogadna, a #947 teljes egérkezelése némán meghalna.
    MouseArea {
        objectName: "collageContextArea"
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        onPressed: function (mouse) {
            if (!canvas.controller)
                return
            const p = mapToItem(sheet, mouse.x, mouse.y)
            const index = sheet.nodeIndexAt(p.x, p.y, -1)
            if (index < 0) {
                contextMenus.openCanvasMenu(mouse.x, mouse.y)
                return
            }
            // A kijelöletlen képre kattintva a kép KIJELÖLŐDIK: különben a
            // menü parancsai egy másik képre hatnának, mint amelyikre a
            // felhasználó kattintott. A már kijelölt képnél a (több elemű)
            // kijelölés érintetlen marad.
            if (canvas.controller.collageSelection.indexOf(index) < 0)
                canvas.controller.setCollageSelection([index])
            contextMenus.openNodeMenu(mouse.x, mouse.y)
        }
    }

    // A húzás közbeni visszajelzés a vászon fölött (`collagepanel/angletext`
    // és `scaletext`). Felengedéskor mindkettő eltűnik.
    //
    // ⚠️ A szög kiírása ELŐJELET VÁLT (#921 `fchs`), és a méretarány a
    // lenyomás pillanatában 100 — mindkettőt a `collage/canvas.py` kész
    // formázói adják a vezérlőn át, itt csak a szöveg áll össze.
    Text {
        objectName: "collageAngleText"
        visible: sheet.dragFeedbackVisible
        //: A kép forgatása közben a vászon fölött megjelenő szög.
        text: qsTr("Angle: %1").arg(sheet.angleCaption)
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        x: canvas.sheetRect.x
        y: Math.max(0, canvas.sheetRect.y - height - 2)
    }
    Text {
        objectName: "collageScaleText"
        visible: sheet.dragFeedbackVisible
        //: A kép méretezése közben a vászon fölött megjelenő méretarány.
        text: qsTr("Scale: %1%").arg(sheet.scaleCaption)
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        x: canvas.sheetRect.x + canvas.sheetRect.width - width
        y: Math.max(0, canvas.sheetRect.y - height - 2)
    }

    // A vászon billentyűparancsai (spec 7.1). A buboréksúgók ki is mondják
    // őket: „Az összes kép kijelölése (Ctrl+A)", „…megszüntetése (Ctrl+D)",
    // „Kijelölt elemek eltávolítása a kollázsból (Del)".
    Keys.onPressed: function (event) {
        if (!canvas.controller)
            return
        if (event.key === Qt.Key_Delete) {
            canvas.controller.removeSelectedNodes()
            event.accepted = true
        } else if (event.key === Qt.Key_A && (event.modifiers & Qt.ControlModifier)) {
            canvas.controller.selectAllNodes()
            event.accepted = true
        } else if (event.key === Qt.Key_D && (event.modifiers & Qt.ControlModifier)) {
            canvas.controller.selectNoNodes()
            event.accepted = true
        }
    }
}
