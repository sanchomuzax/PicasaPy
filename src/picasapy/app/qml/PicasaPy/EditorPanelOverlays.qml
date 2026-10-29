import QtQuick
import PicasaPy

// A szerkesztő mód-eszközeinek és párbeszédeinek gazdai kötései (#6177).
// A gazda adja át a panelt, a láthatóság és a méret a régi elrendezést követi.
Item {
    id: overlaySections
    required property var panel

    readonly property bool textApplyEnabled:
        modeToolScroll.szovegLap ? modeToolScroll.szovegLap.applyEngedve
                                 : false
    readonly property bool modalDialogOpen:
        editorDialogs.anyModalOpen || addCustomAspectRatioDialog.visible

    // ---------------- mód-eszközök (vágás/retusálás/vörösszem/szöveg) ----
    // A mód-panelek és a görgethető keretük önálló fájlban élnek (#3220).
    EditorModeTools {
        id: modeToolScroll
        panel: overlaySections.panel
        anchors.fill: parent
    }

    // #448: a hívó (a "Add Custom Aspect Ratio…" sor) nyitja a párbeszédet;
    // a created jel a controlleren át ment, majd kiválasztja az új arányt.
    AddCustomAspectRatioDialog {
        id: addCustomAspectRatioDialog
        onCreated: (newWidth, newHeight, newName) => {
            if (typeof controller === "undefined" || !controller) return
            controller.addCustomAspectRatio(newWidth, newHeight, newName)
            overlaySections.panel.selectAspect(
                overlaySections.panel.aspectPresets.length
                + overlaySections.panel.customAspectRatios.length - 1)
        }
    }

    // ---------------- párbeszédek (#448, #459) ----------------
    EditorDialogs {
        id: editorDialogs
        panel: overlaySections.panel
    }
}
