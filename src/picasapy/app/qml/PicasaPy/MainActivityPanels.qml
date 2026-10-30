import QtQuick
import PicasaPy

// A főablak lebegő háttérmunka- és folyamatjelzői (#6136).
Item {
    id: activityPanels
    objectName: "mainActivityPanels"
    required property var hostController
    required property var hostActivityCancelConfirm

    anchors.fill: parent
    z: 90

    // #209: lebegő „Importálás" folyamat-panel — jobb oldalt lebeg, húzható;
    // a néző felett is látszik (a szkennelés közben is lehet dolgozni),
    // csak a diavetítés (z:100) takarja.
    ImportProgressPanel {
        id: importPanel
        objectName: "importProgressPanel"
        z: 90
        visible: (hostController && hostController.importPanelVisible !== undefined)
            ? hostController.importPanelVisible : false
        folderName: hostController ? hostController.importFolderName : ""
        doneCount: hostController ? hostController.importDoneCount : 0
        totalCount: hostController ? hostController.importTotalCount : 0
        newCount: hostController ? hostController.importNewCount : 0
        onCloseRequested: {
            if (hostController) hostController.dismissImportPanel()
        }
        // induló hely: jobb felül, a kereső alatt; húzáskor a DragHandler
        // felülírja a kötést — a panel ott marad, ahova a felhasználó tette.
        x: parent.width - width - 24
        y: 56
    }

    // #2966: közös háttérmunka-jelző a jobb-felső sarokban. Alapból rejtve;
    // bármely nyilvántartott háttérmunka megjeleníti.
    ActivityBadge {
        id: activityBadge
        objectName: "activityBadge"
        z: 95
        working: (hostController && hostController.isWorking !== undefined)
            ? hostController.isWorking : false
        cancellable: (hostController && hostController.activityCancellable !== undefined)
            ? hostController.activityCancellable : false
        // a mért hely: felülről 5, jobbról 5 képpont (#3112)
        x: parent.width - width - 5
        y: 5
        onCancelRequested: hostActivityCancelConfirm.ask()
    }

    // #1403: az XMP-arcírás folyamat-panelje — MEGSZAKÍTHATÓ; a már kiírt
    // sidecarok érvényesek maradnak.
    XmpFacesProgressPanel {
        id: xmpFacesPanel
        objectName: "xmpFacesProgressPanel"
        z: 90
        visible: (hostController && hostController.xmpFacesActive !== undefined)
            ? hostController.xmpFacesActive : false
        folderName: hostController ? hostController.currentFolder : ""
        doneCount: hostController ? hostController.xmpFacesDone : 0
        totalCount: hostController ? hostController.xmpFacesTotal : 0
        onCancelRequested: {
            if (hostController) hostController.cancelXmpFaces()
        }
        x: parent.width - width - 24
        y: 56
    }

    // #425: lebegő „Csoportos szerkesztés" folyamat-panel — Mégse gombbal.
    BatchEditProgressPanel {
        id: batchEditPanel
        objectName: "batchEditProgressPanel"
        z: 90
        visible: (hostController && hostController.batchEditActive !== undefined)
            ? hostController.batchEditActive : false
        folderName: hostController ? hostController.batchEditFolderName : ""
        doneCount: hostController ? hostController.batchEditDoneCount : 0
        totalCount: hostController ? hostController.batchEditTotalCount : 0
        onCancelRequested: {
            if (hostController) hostController.cancelBatchEdit()
        }
        x: parent.width - width - 24
        y: 56 + importPanel.height + 12
    }

    // #1527/#5268: a mentés és a fájl-visszaállítás közös folyamatjelzője.
    SaveProgressPanel {
        id: saveProgressPanel
        objectName: "saveProgressPanel"
        z: 90
        visible: (hostController && hostController.saveProgressActive !== undefined)
            ? hostController.saveProgressActive : false
        fileCount: hostController ? hostController.saveProgressFileCount : 0
        percent: hostController ? hostController.saveProgressPercent : 0
        isReverting: hostController ? hostController.saveProgressIsReverting : false
        x: parent.width - width - 24
        y: 56 + importPanel.height + batchEditPanel.height + 24
    }

    // #211: lebegő teljesítmény-monitor; balra az importálás-paneltől.
    PerfMonitorPanel {
        id: perfPanel
        objectName: "perfMonitorPanel"
        z: 90
        visible: (hostController && hostController.perfMonitorEnabled !== undefined)
            ? hostController.perfMonitorEnabled : false
        cpuPercent: hostController ? hostController.perfCpuPercent : 0
        rssMb: hostController ? hostController.perfRssMb : 0
        topActivity: hostController ? hostController.perfTopActivity : ""
        onCloseRequested: {
            if (hostController) hostController.setPerfMonitorEnabled(false)
        }
        onSaveRequested: {
            if (hostController) perfPanel.lastSavedPath = hostController.saveDiagnostics()
        }
        x: 24
        y: 56
    }
}
