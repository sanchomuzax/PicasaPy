import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő 7. füle: a Picasa ÖRÖKÖLT, ma már felület nélküli szűrői
// (#571).
//
// SAJÁT FUNKCIÓ (#571) — TUDATOS ELTÉRÉS AZ EREDETITŐL. A PicasaPy
// egyébként a Picasa felületét követi; itt szándékosan TÖBBET adunk. A
// motorban benne maradt egy csomó régi szűrő, amit a 3.9 felülete nem
// mutat — a felhasználó nem tudja előhívni, és egy régi `.picasa.ini`-ből
// mégis ott lehet a képén. Egy későbbi „hűségjavítás" ezt a fület NE vegye
// ki: a bináris-egyezés erre a fülre nem vonatkozik (lista:
// docs/decisions/vedett-sajat-funkciok.md, részletes indoklás: ADR-003,
// docs/decisions/legacy-effects-tab.md).
//
// A gombok a katalógusból jönnek (`editController.legacyEffects`), nem
// kézzel beírva; hogy melyik ÉL, azt a RENDERELŐ dönti el
// (`chain.can_render_filter`) — így nem lehet aktívnak látszó, de nem ható
// gomb. A csúszkák a szokásos `tryOpenParamPanel`-úton, a `filterdesc.xml`
// metaadatából generálódnak.
ColumnLayout {
    id: legacyTab

    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "legacyEffectsColumn"
    // #583: a nyitott paraméter-alpanel alatt a fül elrejtőzik — enélkül
    // a kettő EGYMÁSRA rajzolódott (a testvér effekt-fülek mintája)
    visible: !panel.modeToolActive && panel.activeTab === 6
             && !panel.paramPanelActive
    opacity: panel.enabled ? 1 : 0.45
    // #741: az effekt-rács MÉRT geometriája (`fx1..fx12`, x 8 / 96 / 184,
    // osztásköz 88, látható csempe 86) a #704 óta helyes — a tartalom-
    // oszlop 276-ra bővülésével ezért a fül margóit kell igazítani, hogy a
    // rács továbbra is 262 képpont széles maradjon (3 × 86 + 2 × 2), az
    // x 8-on kezdve. Szimmetrikus 10-10-es margóval a csempe 86-ról 84-re
    // zsugorodott volna.
    anchors.leftMargin: 5
    anchors.rightMargin: 9
    anchors.topMargin: 10
    spacing: 8

    //: #3263: mennyi hely marad a rácsnak a MÉRT lapon belül. A felső margó
    //: és a bevezető (legfeljebb két sor) levonása után maradó rész — így a
    //: fül `implicitHeight`-je (bevezető + sorköz + keret) sosem lépi túl a
    //: mért 277-et, akármilyen magas a platform betűje.
    readonly property real racsKeret:
        Math.max(0, panel.mertTabPanelHeight - legacyTab.anchors.topMargin
                    - bevezeto.implicitHeight - legacyTab.spacing)

    // a katalógus; controller nélkül (izolált QML-tesztek) üres marad
    readonly property var effects:
        panel.hasEffectController() ? editController.legacyEffects : []

    // #704: NINCS fejlécsáv a rács fölött. Az eredeti Picasa
    // elrendezés-forrásában (`editpanel.tre:428`) az effekt-fül panelének
    // (`editpanel/tabpanel3`) PONTOSAN EGY gyereke van: a rács konténere
    // (`editpanel/fxthumbs`). Szekciócím, fejlécsáv, cím-felirat az `fx*`
    // névtérben nincs — a fülre váltva azonnal a csempék jönnek. A korábbi
    // 22 képpontos, kiemelt hátterű sáv ráadásul abból a panelmagasságból
    // vett el, ami a #703 szerint amúgy is szűkös.

    // #571 2. pont: a fül teteje egy sorban mondja ki, mi ez a készlet.
    //
    // #3247: a szöveg RÖVIDEBB lett (három sor helyett kettő), mert ennek a
    // fülnek a magassága hajtotta meg az EGÉSZ panelt: a `tallestTabHeight`
    // a legmagasabb fülé, és ez a — SAJÁT, az eredetiben nem létező — fül
    // 298 képpontot kért a mért `editpanel/tabpanel1` = 277 helyett. A
    // tartalom nem vész el: ugyanaz a két állítás áll benne (honnan jönnek,
    // és hogy a mai Picasa csak felismeri őket).
    //: #3263: LEGFELJEBB KÉT SOR. A sormagasság platformfüggő (a windowsos
    //: alapbetű magasabb sort ad), és a szöveg ott három sorba tört — a fül
    //: magassága így a betűmetrikán múlt: Linuxon 274, Windowson 317, a mért
    //: `editpanel/tabpanel1` = 277 helyett. A sorszám rögzítése nélkül a
    //: keret alábbi számítása sem tartana.
    //: #3278: a bevezető RÖVID mondat. A korábbi, kétmondatos alak a
    //: fejlesztői gépen elfért, a CI (és egy nagyobb rendszerbetűvel a
    //: felhasználó) gépén viszont levágódott — az `elide` a törést
    //: hárította el, az olvashatóságot nem: a mondat vége „…"-szal
    //: elmaradt.
    //:
    //: ⛔ REFERENCIA NINCS: ez a fül a mi SAJÁT kiegészítésünk (ADR-003),
    //: az eredetiben nem létezik — a szöveg hossza tehát a mi döntésünk.
    //: A kivett fél mondat nem vész el: a buboréksúgóban ott van.
    //: ⛔ #3278: a felirat SAJÁT dobozban áll, és a doboz kéri a helyet.
    //:
    //: Egy tördelő `Text` a `ColumnLayout`-ban az implicit magasságát a
    //: tördelés ELŐTTI szélességből számolja, ezért egysoros helyet kap —
    //: és onnantól a második sor akkor sem fér el, ha a szöveg oda törne.
    //: Mérve (a CI ubuntu 2/4 lába): a doboz 246 × 13, `lineCount` 1,
    //: `truncated` igaz. Helyben, szűkebb panelen ugyanez: 186 × 16, egy
    //: sor, levágva.
    //:
    //: A megoldás: a `Text` szélessége a SZÜLŐ dobozáé (tehát a tördelés
    //: a tényleges szélességgel számol), a doboz magassága pedig a
    //: `contentHeight` — így a sorok száma után igazodik.
    Item {
        id: bevezetoDoboz
        Layout.fillWidth: true
        Layout.preferredHeight: bevezeto.contentHeight

        Text {
            id: bevezeto
            objectName: "legacyEffectsIntro"
            width: bevezetoDoboz.width
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
            text: qsTr("These filters come from older Picasa versions.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray

            //: A bővebb magyarázat. SAJÁT tulajdonságban is áll, nem csak a
            //: csatolt `ToolTip.text`-ben: a csatolt tulajdonságot a próba
            //: nem tudja kiolvasni (`property("ToolTip.text")` → null,
            //: mérve a #1701-ben), tehát a meglétét nem lehetne őrizni.
            readonly property string bovebbSugo: qsTr(
                "Today's Picasa only recognises them inside your old edits.")
            ToolTip.text: bevezeto.bovebbSugo
            ToolTip.visible: bevezetoEgér.hovered
            ToolTip.delay: Theme.tooltipDelay
            HoverHandler { id: bevezetoEgér }
        }
    }

    //: #3263: a rács GÖRGETHETŐ kereten belül él, és a keret a mért lapból
    //: maradó helyet kapja. Így a fül magassága konstrukcióból belefér a
    //: mért 277-be MINDEN platformon (a #703/#3247 őre ezt állítja), a
    //: tartalom mégsem vész el: ami nem fér ki, az elgörgethető. A korábbi
    //: alak a rács teljes implicit magasságát kérte, tehát egy magasabb
    //: betűkészlet némán túlnőtt a lapon, és a tartalom alja levágódott.
    Flickable {
        id: racsGorgeto
        objectName: "legacyEffectsScroll"
        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(racs.implicitHeight, legacyTab.racsKeret)
        contentWidth: width
        contentHeight: racs.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {
            //: csak akkor látszik, ha tényleg van mit görgetni
            policy: racs.implicitHeight > racsGorgeto.height
                    ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
        }

    GridLayout {
        id: racs
        objectName: "legacyEffectsGrid"
        columns: 3
        columnSpacing: 6
        rowSpacing: 6
        width: racsGorgeto.width

        Repeater {
            model: legacyTab.effects
            delegate: PanelButton {
                required property var modelData
                objectName: "legacyEffect_" + modelData.key
                // a felirat a vezérlőből MÁR fordítva jön (a katalógus
                // adat, nem forrás — ld. edit_controller.legacyEffects)
                label: modelData.label
                buttonEnabled: modelData.enabled
                // a még megfejtetlen (és a halott) nevek SZÜRKÉN, de
                // LÁTHATÓAN maradnak: egy régi képen ott lehet az effekt,
                // és a felhasználónak tudnia kell róla (#571 4. pont)
                opacity: modelData.enabled ? 1.0 : 0.45
                thumbSource: modelData.enabled
                             ? panel.effectThumbSource(modelData.key) : ""
                onButtonClicked: {
                    // #700: a csúszkás alpanel a gomb SAJÁT feliratát kapja
                    // címnek — itt a katalógusból már fordítva jövő
                    // `modelData.label`-t, nem a belső kulcsot
                    if (!panel.tryOpenParamPanel(modelData.key, modelData.label))
                        panel.effectRequested(modelData.key)
                }
                // a letiltott gombok megmondják, MIÉRT nem használhatók —
                // és a halott név más magyarázatot kap, mint a még
                // megfejtetlen (#567 kontra #568)
                tooltip: modelData.enabled ? "" : (modelData.dead
                    ? qsTr("This name is a leftover from an old configuration. Picasa 3.9 has no processor for it either, so it cannot be applied.")
                    : qsTr("Picasa can read this filter from an old .picasa.ini, but its exact pixel operation has not been decoded yet, so it cannot be applied."))
            }
        }
    }
    }

    // #3247: a korábbi `Item { Layout.fillHeight: true }` kitöltő eltűnt. A
    // fül a saját implicit magasságára áll (a gazda csak felül/oldalt
    // horgonyozza), tehát a kitöltő sosem kapott helyet — a ColumnLayout
    // sorköze viszont 8 képponttal növelte a fül magasságát, és ezzel az
    // EGÉSZ panelét.
}
