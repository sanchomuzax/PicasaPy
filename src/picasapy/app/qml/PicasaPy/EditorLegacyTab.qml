import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő 7. füle: a Picasa ÖRÖKÖLT, ma már felület nélküli szűrői
// (#571).
//
// TUDATOS ELTÉRÉS AZ EREDETITŐL. A PicasaPy egyébként a Picasa felületét
// követi; itt szándékosan TÖBBET adunk. A motorban benne maradt egy csomó
// régi szűrő, amit a 3.9 felülete nem mutat — a felhasználó nem tudja
// előhívni, és egy régi `.picasa.ini`-ből mégis ott lehet a képén. Egy
// későbbi „hűségjavítás" ezt a fület NE vegye ki.
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

    // #571 2. pont: a fül teteje egy sorban mondja ki, mi ez a készlet
    Text {
        objectName: "legacyEffectsIntro"
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("These filters come from older versions of Picasa. They are not available in today's Picasa, but your old edits may contain them.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    GridLayout {
        objectName: "legacyEffectsGrid"
        columns: 3
        columnSpacing: 6
        rowSpacing: 6
        Layout.fillWidth: true

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

    Item { Layout.fillHeight: true }
}
