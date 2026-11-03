import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő összevont Glimmer és örökölt effektfüle (#6443).
ColumnLayout {
    id: effectsTab4

    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "effectsColumn4"
    visible: !panel.modeToolActive && panel.activeTab === 5
             && !panel.paramPanelActive
    opacity: panel.enabled ? 1 : 0.45
    anchors.leftMargin: 5
    anchors.rightMargin: 9
    anchors.topMargin: 10
    spacing: 0

    // A mért csempeosztásból indul: a viewport mindig pontosan 4,5 sort
    // mutat, a rács további sorai pedig görgethetők.
    readonly property real rowPitch: effectRoundedEdges.y > effectMatte.y
        ? effectRoundedEdges.y - effectMatte.y
        : effectMatte.implicitHeight + effectsGrid4.rowSpacing

    Flickable {
        id: effectsGrid4Viewport
        objectName: "effectsGrid4Viewport"
        Layout.fillWidth: true
        Layout.preferredHeight: effectsTab4.rowPitch * 4.5
        Layout.minimumHeight: effectsTab4.rowPitch * 4.5
        contentWidth: width
        contentHeight: effectsGrid4.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {
            policy: effectsGrid4.implicitHeight > effectsGrid4Viewport.height
                    ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
        }

        GridLayout {
            id: effectsGrid4
            objectName: "effectsGrid4"
            width: effectsGrid4Viewport.width
            columns: 3
            columnSpacing: 2
            rowSpacing: 2

            // A Glimmer-effektek kerülnek előre.
            PanelButton {
                id: effectMatte
                objectName: "effectMatte"
                label: qsTr("Matte")
                tooltip: qsTr("Add a light glow to the edges of your photo")
                onButtonClicked: if (!panel.tryOpenParamPanel("matte", label)) panel.effectRequested("matte")
                thumbSource: panel.effectThumbSource("matte")
                badge: panel.hasBadge("matte")
            }
            PanelButton {
                objectName: "effectNightVision"
                label: qsTr("Night Vision")
                tooltip: qsTr("Mimics infrared night-vision cameras")
                onButtonClicked: if (!panel.tryOpenParamPanel("nightvision", label)) panel.effectRequested("nightvision")
                thumbSource: panel.effectThumbSource("nightvision")
                badge: panel.hasBadge("nightvision")
            }
            PanelButton {
                objectName: "effectLocalContrast"
                label: qsTr("Local Contrast")
                tooltip: qsTr("Brings out image details")
                onButtonClicked: if (!panel.tryOpenParamPanel("localcontrast", label)) panel.effectRequested("localcontrast")
                thumbSource: panel.effectThumbSource("localcontrast")
                badge: panel.hasBadge("localcontrast")
            }
            PanelButton {
                id: effectRoundedEdges
                objectName: "effectRoundedEdges"
                label: qsTr("Rounded Edges")
                tooltip: qsTr("Give your photo rounded corners")
                onButtonClicked: if (!panel.tryOpenParamPanel("roundededges", label)) panel.effectRequested("roundededges")
                thumbSource: panel.effectThumbSource("roundededges")
                badge: panel.hasBadge("roundededges")
            }
            PanelButton {
                objectName: "effectPicnikGrain"
                label: panel.shiftMasodlagos
                       ? qsTr("Film Grain (Old)") : qsTr("Film Grain")
                tooltip: panel.shiftMasodlagos
                         ? qsTr("Adds film grain") : qsTr("Simulate film grain")
                //: #2146: Shifttel a másodlagos szűrő előnézete jelenik meg.
                readonly property string szuro: panel.shiftMasodlagos
                                                ? "grain" : "picnikgrain"
                onButtonClicked: if (!panel.tryOpenParamPanel(szuro, label)) panel.effectRequested(szuro)
                thumbSource: panel.effectThumbSource("picnikgrain")
                thumbSourceAlt: panel.effectThumbSource("grain")
                thumbAltActive: panel.shiftMasodlagos
                badge: panel.hasBadge(szuro)
            }

            // A korábbi külön fül örökölt effektjei a Glimmer csempék után
            // kerülnek, ugyanabba a háromoszlopos, görgethető rácsba.
            EditorLegacyTab {
                panel: effectsTab4.panel
            }
        }
    }
}
