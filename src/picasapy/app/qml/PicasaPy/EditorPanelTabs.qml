import QtQuick
import PicasaPy

// A szerkesztő fülsávja, a hét fül és a paraméteres effekt-alpanel (#6177).
// A panel állapotát a gazda adja át; a közös layout geometriája változatlan.
Item {
    id: tabSections
    required property var panel

    property alias tabBarItem: tabBar
    property alias tabAreaItem: tabArea
    property alias effectParamPanel: effectParamScroll
    property alias previewTimer: paramPreviewTimer
    readonly property Item finetunePanel: tabArea.finomhangoloLap
    readonly property Item fixesTab: tabArea.gyakoriLap

    // ---------------- fülsáv: Gyakori javítások / Finomhangolás / Effektek /
    // 4. effekt-fül / 5. effekt-fül (#20, #328) — csak "tools" módban,
    // vágásnál (cropColumn) nincs értelme. Öt egyenlő szélességű fül fér el
    // a panel szélességében (Layout.fillWidth mindegyiken, ld. #328 4. pont).
    EditorTabBar {
        id: tabBar
        objectName: "editTabBar"
        panel: tabSections.panel
        visible: !tabSections.panel.modeToolActive
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        // #741: a TARTALOM-OSZLOP a mért 276 képpont (x 3..279) — a
        // korábbi 10-10 képpontos margó 260-at hagyott, ettől lett a
        // fülsáv és minden alatta lévő rács keskenyebb az eredetinél.
        // (`docs/specs/szerkeszto-panel-meretek.md` 1.)
        anchors.leftMargin: 3
        anchors.rightMargin: 1
        anchors.topMargin: 10
    }

    //: #3220: a fülek önálló fájlban élnek; a gazda `finetunePanel` és
    //: `fixesTab` tükreit a komponens aliasai tartják meg.
    EditorTabHost {
        id: tabArea
        panel: tabSections.panel
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        // #741: a fülterület a fülsávval AZONOS 276 képpontos
        // tartalom-oszlop (x 3..279)
        anchors.leftMargin: 3
        anchors.rightMargin: 1
    }

    // #616: a csúszkás alpanel a fülek görgethető területén KÍVÜL
    // marad: maga is Flickable (saját vágással és görgetéssel), és egy
    // Flickable implicit magassága 0 — becsomagolva nulla magasságot
    // kapna, azaz eltűnne. A gombsorig érő horgony itt is megvan.
    // ---------------- effekt-paraméter alpanel (#316) ----------------
    // #496: a tartalom önálló fájlban (EditorParamPanel.qml).
    EditorParamPanel {
        id: effectParamScroll
        objectName: "editorEffectParamScroll"
        panel: tabSections.panel
        visible: !tabSections.panel.modeToolActive
                 && tabSections.panel.paramPanelActive
                 && !tabSections.panel.paramPanelSuspended
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
    }

    // #316: a húzás közbeni előnézetek rövid késleltetéssel összevonódnak;
    // az Apply közvetlenül küldi az utolsó értéket, nem függ ettől az időzítőtől.
    Timer {
        id: paramPreviewTimer
        interval: 60
        onTriggered: if (tabSections.panel.hasEffectController())
            editController.previewEffect(tabSections.panel.paramEffectName,
                                          tabSections.panel.paramEffectValues)
    }
}
