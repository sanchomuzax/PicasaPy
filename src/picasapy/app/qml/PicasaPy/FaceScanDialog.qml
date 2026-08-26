import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Arckeresés (#1473) — a `FaceScanController` keresési oldalának belépési
// pontja.
//
// ## Miért kell ez az ablak egyáltalán
//
// Az EREDETI Picasában az arckeresésnek nem volt „indítsd el" menüpontja: a
// `BgFaceDetectThread` háttérszál alapból BE volt kapcsolva, és folyamatosan
// dolgozott; a felhasználó a Beállítások „Névcímkék" fülén tudta kikapcsolni
// (`docs/specs/picasa-arcfelismeres.md` 1.1). Nálunk ilyen háttérszál MA
// NINCS, és a keresés a felhasználó gépén percekig tartó, minden képet
// beolvasó munka — automatikusan elindítani a háta mögött rosszabb lenne,
// mint megkérdezni. Amíg a háttérmotor nem áll készen, ez az ablak a
// védhető hely: innen indul, itt szakítható meg, és itt derül ki, ha a
// modell hiányzik.
//
// ## Két szabály, amit ez az ablak betart
//
// 1. **NEM MODÁLIS** (#449). A beolvasás alatt semmi nem blokkolhatja a
//    felhasználót: az ablak bezárható, a munka fut tovább, a haladás pedig a
//    bal hasáb „Névtelenek" során is látszik (`FolderPane.faceScanPercent`).
// 2. **A tiltás nem néma** (#1473). Ha a modellfájl hiányzik, a gomb szürke
//    MARAD, de mellette ott áll, hogy mi hiányzik és hova kell tenni — a
//    szöveget a vezérlő adja (`unavailableReason()`), mert a modell helye
//    csak Python-oldalról ismert.
Window {
    id: faceScanWindow
    objectName: "faceScanDialog"
    title: qsTr("Find Faces")
    // #449: SZÁNDÉKOSAN nem modális — ld. a fenti 1. szabályt.
    modality: Qt.NonModal
    width: 560
    height: 420
    minimumWidth: 420
    minimumHeight: 320
    color: Theme.canvasBg

    // A vezérlő. A Main.qml az ablak-szintű álnéven adja át; a név
    // SZÁNDÉKOSAN nem `faceScanController` (#1236: az azonos nevű property
    // jobb oldala önmagára oldódna) és nem is `ctl` (#1490: azt a
    // rövidítést öt fájl használja más-más vezérlőre).
    property var faceScan: null

    // -- állapot ----------------------------------------------------------
    property bool scanning: false
    property bool grouping: false
    // Az elérhetőség SLOT-ból jön, nem NOTIFY-property-ből, ezért nem
    // magától frissül: megnyitáskor és minden befejezett munka után
    // kérdezzük újra.
    property bool detectorAvailable: false
    property bool embedderAvailable: false
    property string detectorReason: ""
    property string embedderReason: ""
    // az utolsó befejezett munka emberi nyelvű eredménye
    property string statusText: ""
    // a lenyomat-számítás haladása (a detektáláshoz `scanPercent` van)
    property int groupDone: 0
    property int groupTotal: 0
    // a „Névtelenek" album tartalma a keresés után (`unnamedAlbum()`)
    property var foundPhotos: []

    readonly property int scanPercent:
        faceScanWindow.faceScan ? faceScanWindow.faceScan.scanPercent : -1

    // ⚠️ A vezérlő tagjait MINDIG a `faceScanWindow.faceScan.<tag>` teljes
    // alakban hívjuk, soha nem egy `var ctlr = …` helyi változón át: a
    // képesség-őr (#1476, `scripts/kepesseg_or.py`) MINŐSÍTETT alakot keres,
    // és a helyi változón átmenő hívást — jogosan — nem látja bekötésnek.
    // Épp ez a hibaosztály szülte ezt a jegyet.
    function refreshAvailability() {
        if (!faceScanWindow.faceScan) {
            faceScanWindow.detectorAvailable = false
            faceScanWindow.embedderAvailable = false
            faceScanWindow.detectorReason = ""
            faceScanWindow.embedderReason = ""
            return
        }
        faceScanWindow.detectorAvailable = faceScanWindow.faceScan.isAvailable()
        faceScanWindow.embedderAvailable =
            faceScanWindow.faceScan.isEmbeddingAvailable()
        faceScanWindow.detectorReason = faceScanWindow.faceScan.unavailableReason()
        faceScanWindow.embedderReason =
            faceScanWindow.faceScan.embeddingUnavailableReason()
    }

    function refreshFound() {
        faceScanWindow.foundPhotos = faceScanWindow.faceScan
            ? faceScanWindow.faceScan.unnamedAlbum() : []
    }

    function open() {
        faceScanWindow.refreshAvailability()
        faceScanWindow.refreshFound()
        faceScanWindow.visible = true
    }

    function startScan() {
        if (!faceScanWindow.faceScan) return
        faceScanWindow.statusText = ""
        faceScanWindow.scanning = true
        faceScanWindow.faceScan.scanForFaces()
    }

    function cancelScan() {
        if (faceScanWindow.faceScan)
            faceScanWindow.faceScan.cancelScan()
    }

    function startGrouping() {
        if (!faceScanWindow.faceScan) return
        faceScanWindow.statusText = ""
        faceScanWindow.groupDone = 0
        faceScanWindow.groupTotal = 0
        faceScanWindow.grouping = true
        faceScanWindow.faceScan.computeEmbeddings()
    }

    function cancelGrouping() {
        if (faceScanWindow.faceScan)
            faceScanWindow.faceScan.cancelEmbedding()
    }

    Connections {
        // A `? :` őr KELL: vezérlő nélkül a property `undefined`, amit a
        // `target` nem tud felvenni („Unable to assign [undefined] to
        // QObject*"), és a #1260 őre ezt jogosan hibának veszi.
        target: faceScanWindow.faceScan ? faceScanWindow.faceScan : null
        function onScanStarted() { faceScanWindow.scanning = true }
        function onScanFinished(found, scanned) {
            faceScanWindow.scanning = false
            // A `scanned` az ÁTNÉZETT képek száma (a már névcímkés és a
            // videó kimarad belőle), nem azoké, amelyeken arc van — a
            // felirat ezért „átnézett képet" mond.
            faceScanWindow.statusText = found > 0
                ? qsTr("Finished: %1 face(s) found in %2 checked picture(s).")
                      .arg(found).arg(scanned)
                : qsTr("Finished: no faces were found in %1 checked picture(s).")
                      .arg(scanned)
            faceScanWindow.refreshFound()
        }
        function onScanCancelled() {
            faceScanWindow.scanning = false
            faceScanWindow.statusText = qsTr(
                "Search cancelled. The faces found so far are kept.")
            faceScanWindow.refreshFound()
        }
        function onScanFailed(message) {
            faceScanWindow.scanning = false
            faceScanWindow.statusText = qsTr("The search failed: %1").arg(message)
        }
        function onModelUnavailable() {
            faceScanWindow.scanning = false
            faceScanWindow.refreshAvailability()
        }
        function onEmbeddingStarted() { faceScanWindow.grouping = true }
        function onEmbeddingProgress(done, total) {
            faceScanWindow.groupDone = done
            faceScanWindow.groupTotal = total
        }
        function onEmbeddingFinished(embedded, grouped) {
            faceScanWindow.grouping = false
            faceScanWindow.statusText = qsTr(
                "Grouping finished: %1 face(s) compared, %2 sorted into groups.")
                .arg(embedded).arg(grouped)
        }
        function onEmbeddingCancelled() {
            faceScanWindow.grouping = false
            faceScanWindow.statusText = qsTr(
                "Grouping cancelled. The groups made so far are kept.")
        }
        function onEmbeddingFailed(message) {
            faceScanWindow.grouping = false
            faceScanWindow.statusText = qsTr("The grouping failed: %1").arg(message)
        }
        function onEmbeddingModelUnavailable() {
            faceScanWindow.grouping = false
            faceScanWindow.refreshAvailability()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr(
                "PicasaPy goes through the pictures of your library and looks "
                + "for faces. Pictures that already carry a name tag are left "
                + "untouched. You can close this window while the search runs: "
                + "the work continues, and the progress stays visible next to "
                + "the Unnamed album.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        // -- 1. lépés: keresés ------------------------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            PicasaButton {
                objectName: "faceScanStartButton"
                text: faceScanWindow.scanning ? qsTr("Searching...")
                                              : qsTr("Find Faces")
                enabled: !!faceScanWindow.faceScan
                         && faceScanWindow.detectorAvailable
                         && !faceScanWindow.scanning
                onClicked: faceScanWindow.startScan()
            }
            PicasaButton {
                objectName: "faceScanCancelButton"
                visible: faceScanWindow.scanning
                text: qsTr("Cancel")
                onClicked: faceScanWindow.cancelScan()
            }
            Item { Layout.fillWidth: true }
        }

        Text {
            objectName: "faceScanUnavailableText"
            visible: faceScanWindow.detectorReason.length > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: faceScanWindow.detectorReason
            font.pixelSize: Theme.fontSize - 1
            color: Theme.folderDate
        }

        // haladás — a bal hasáb sorával UGYANAZT a `scanPercent`-et mutatja
        ColumnLayout {
            objectName: "faceScanProgressPanel"
            visible: faceScanWindow.scanning
            Layout.fillWidth: true
            spacing: 4

            Text {
                objectName: "faceScanProgressLabel"
                Layout.fillWidth: true
                elide: Text.ElideRight
                text: faceScanWindow.scanPercent >= 0
                      ? qsTr("Scanning for faces... %1% complete")
                            .arg(faceScanWindow.scanPercent)
                      : qsTr("Scanning for faces...")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            // deklaratív (mindig renderelő) sáv — a DedupDialog mintája;
            // Canvas/requestPaint SZÁNDÉKOSAN nem
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 8
                radius: 4
                color: Theme.trackBg
                border.color: Theme.chromeBorder

                Rectangle {
                    objectName: "faceScanProgressFill"
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    radius: parent.radius
                    color: Theme.picasaGreen
                    width: faceScanWindow.scanPercent > 0
                           ? parent.width * faceScanWindow.scanPercent / 100
                           : 0
                }
            }
        }

        // -- 2. lépés: csoportosítás --------------------------------------
        Text {
            Layout.fillWidth: true
            topPadding: 6
            wrapMode: Text.WordWrap
            text: qsTr(
                "As a second step PicasaPy can compare the faces it found and "
                + "put the similar ones into the same group, so a whole group "
                + "can be given a name at once.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            PicasaButton {
                objectName: "faceScanGroupButton"
                text: faceScanWindow.grouping ? qsTr("Grouping...")
                                              : qsTr("Group Faces")
                enabled: !!faceScanWindow.faceScan
                         && faceScanWindow.embedderAvailable
                         && !faceScanWindow.grouping
                onClicked: faceScanWindow.startGrouping()
            }
            PicasaButton {
                objectName: "faceScanGroupCancelButton"
                visible: faceScanWindow.grouping
                text: qsTr("Cancel")
                onClicked: faceScanWindow.cancelGrouping()
            }
            Text {
                objectName: "faceScanGroupProgressLabel"
                visible: faceScanWindow.grouping
                    && faceScanWindow.groupTotal > 0
                Layout.fillWidth: true
                elide: Text.ElideRight
                text: qsTr("Grouping faces... %1 / %2")
                          .arg(faceScanWindow.groupDone)
                          .arg(faceScanWindow.groupTotal)
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            Item { Layout.fillWidth: true }
        }

        Text {
            objectName: "faceScanGroupUnavailableText"
            visible: faceScanWindow.embedderReason.length > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: faceScanWindow.embedderReason
            font.pixelSize: Theme.fontSize - 1
            color: Theme.folderDate
        }

        // -- eredmény ------------------------------------------------------
        Text {
            objectName: "faceScanStatusText"
            visible: faceScanWindow.statusText.length > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: faceScanWindow.statusText
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        Text {
            objectName: "faceScanFoundText"
            visible: (faceScanWindow.foundPhotos
                      ? faceScanWindow.foundPhotos.length : 0) > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Pictures with unnamed faces: %1 — they are waiting in "
                       + "the Unnamed album, in the left pane.")
                      .arg(faceScanWindow.foundPhotos
                           ? faceScanWindow.foundPhotos.length : 0)
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "faceScanCloseButton"
                text: qsTr("Close")
                onClicked: faceScanWindow.visible = false
            }
        }
    }
}
