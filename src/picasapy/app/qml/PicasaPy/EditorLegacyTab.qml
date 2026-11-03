import QtQuick

// SAJÁT FUNKCIÓ (#571) - TUDATOS ELTÉRÉS AZ EREDETITŐL. A motorban benne
// maradt egy sor régi szűrő, amit a 3.9 felülete nem mutat; mi tudatosan
// előhívhatóvá tesszük őket (#6443 óta a Glimmer effektekkel közös fülön).
// Egy későbbi „hűségjavítás" ezt NE vegye ki. Lista:
// docs/decisions/vedett-sajat-funkciok.md, indoklás: ADR-003.
// A korábbi külön fül csempéi most az összevont rácsban jelennek meg.
// A renderelő dönti el, melyik bejegyzés használható; a natív regiszterben
// nem létező focalpixelate csak a régi lánc figyelésében marad meg.
Repeater {
    id: legacyTab

    //: az összevont effekt-rács gazdája
    required property var panel

    objectName: "legacyEffectsColumn"
    readonly property var effects:
        panel.hasEffectController()
            ? (editController.legacyEffects || []).filter(function(effect) {
                  return effect.key !== "focalpixelate"
              })
            : []
    model: legacyTab.effects

    delegate: PanelButton {
        required property var modelData
        objectName: "legacyEffect_" + modelData.key
        label: modelData.label
        buttonEnabled: modelData.enabled
        opacity: modelData.enabled ? 1.0 : 0.45
        thumbSource: modelData.enabled
                     ? legacyTab.panel.effectThumbSource(modelData.key) : ""
        onButtonClicked: {
            if (!legacyTab.panel.tryOpenParamPanel(modelData.key, modelData.label))
                legacyTab.panel.effectRequested(modelData.key)
        }
    }
}
