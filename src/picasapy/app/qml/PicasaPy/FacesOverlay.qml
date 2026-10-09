import QtQuick
import QtQuick.Controls
import "aranykenyszer.js" as AranyKenyszer

// #147: a mentett faces= régiók megjelenítése a nézőben. #26 (2. kör):
// SZERKESZTŐ mód — új arc-téglalap húzása egérrel, név hozzárendelése
// (meglévő személy-listából vagy új névvel), régió törlése/átnevezése.
// Az írás a `facesHelper`-en (QML-kontextus) át, útvonalanként soros,
// best-effort konkurenciakezelésű ini-írással
// történik (picasapy.app.faces_helper.FacesHelper) — az overlay maga
// állapotmentes a mentett adatra nézve, csak a MEGRAJZOLÁS/POPUP saját
// átmeneti állapotát tartja.
Item {
    id: overlay
    objectName: "facesOverlay"

    // {left, top, right, bottom, name} elemek relatív [0..1] koordinátákkal
    // — a FacesHelper.facesFor() visszatérési formátuma.
    property var faces: []
    // A facesVisible kapcsoló a mentett ini-kereteket mutatja. Az indexből
    // jövő, még névtelen keret kattintásig rejtett, de a helyén fogad kattintást.
    property bool showSavedFaces: false
    property int selectedDetectedFaceId: -1
    // szerkesztő mód: a mentett ini-arcok rajzolása/törlése/átnevezése csak
    // ekkor aktív; a DB-beli névtelen felismerés kattintása nézetmódban is él.
    property bool editMode: false
    // a facesHelper hívásaihoz szükséges fájlrendszer-útvonal (a
    // PhotoViewer tölti ki: photosModel.filePathAt(currentIndex))
    property string imagePath: ""
    // az EGYETLEN globális facesHelper elérhetősége teszt-fixture nélkül
    // (a régi, önálló QML-betöltésű tesztek — pl. test_folder_pane_people —
    // mintájára) is biztonságos legyen
    readonly property bool hasHelper: typeof facesHelper !== "undefined" && facesHelper
    property var knownNames: []
    readonly property int minSelectionPx: 16

    // sikeres írás után a hívó (PhotoViewer) ezt figyelve olvashatja újra
    // a facesFor()-t (a modell maga nem tudja, hogy az ini megváltozott)
    signal edited()
    signal manualCancelRequested()

    function refreshKnownNames() {
        overlay.knownNames = overlay.hasHelper && overlay.imagePath
            ? facesHelper.knownNames(overlay.imagePath) : []
    }
    onImagePathChanged: refreshKnownNames()
    onEditModeChanged: if (editMode) refreshKnownNames()

    function cancelManualAdd() {
        overlay.closeEditor()
        overlay.pendingRect = Qt.rect(0, 0, 0, 0)
        overlay.pendingIsNew = false
        overlay.manualCancelRequested()
    }

    function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }

    Repeater {
        model: overlay.faces
        delegate: Item {
            id: faceItem
            required property var modelData
            required property int index
            readonly property real relLeft: modelData.left
            readonly property real relTop: modelData.top
            readonly property real relRight: modelData.right
            readonly property real relBottom: modelData.bottom
            readonly property string personName: modelData.name || ""
            readonly property bool detectedFace: modelData.detected === true
            readonly property int detectedFaceId: detectedFace
                ? Number(modelData.faceId) : -1

            x: relLeft * overlay.width
            y: relTop * overlay.height
            width: Math.max(0, (relRight - relLeft) * overlay.width)
            height: Math.max(0, (relBottom - relTop) * overlay.height)

            Rectangle {
                visible: faceItem.detectedFace
                    ? overlay.showSavedFaces
                        || overlay.selectedDetectedFaceId === faceItem.detectedFaceId
                    : overlay.showSavedFaces
                anchors.fill: parent
                color: "transparent"
                // A fotó fölötti Picasa-keret nem témaszínű: a #4572
                // referenciáján #d0d1d0 színű, egypixeles, éles sarkú vonal.
                border.color: "#d0d1d0"
                border.width: 1
                radius: 0
            }
            Rectangle {
                visible: overlay.showSavedFaces && nameLabel.text.length > 0
                anchors.top: parent.bottom
                anchors.topMargin: 2
                anchors.horizontalCenter: parent.horizontalCenter
                width: nameLabel.implicitWidth + 8
                height: nameLabel.implicitHeight + 4
                radius: 3
                color: "#00000099"

                Text {
                    id: nameLabel
                    anchors.centerIn: parent
                    text: personName
                    color: "#ffffff"
                    font.pixelSize: Theme.fontSize - 1
                }
            }

            // szerkesztő módban: kattintás a régióra = átnevezés (a popup a
            // meglévő névvel nyílik), a sarok "×"-je pedig törli
            MouseArea {
                objectName: "faceRegionArea_" + faceItem.index
                anchors.fill: parent
                visible: overlay.editMode || faceItem.detectedFace
                enabled: overlay.editMode || faceItem.detectedFace
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (faceItem.detectedFace) {
                        overlay.selectedDetectedFaceId = faceItem.detectedFaceId
                        overlay.openEditorForDetected(
                            faceItem.relLeft, faceItem.relTop,
                            faceItem.relRight, faceItem.relBottom,
                            faceItem.detectedFaceId)
                    } else {
                        overlay.openEditorFor(
                            faceItem.relLeft, faceItem.relTop,
                            faceItem.relRight, faceItem.relBottom,
                            faceItem.personName, false)
                    }
                }
            }
            Rectangle {
                objectName: "faceDeleteButton_" + faceItem.index
                visible: overlay.editMode && !faceItem.detectedFace
                width: 16; height: 16
                anchors.top: parent.top; anchors.right: parent.right
                anchors.margins: -6
                radius: 8
                color: "#c0392b"
                border.color: "#ffffff"; border.width: 1
                Text {
                    anchors.centerIn: parent
                    text: "×"
                    color: "#ffffff"
                    font.pixelSize: 11
                    font.bold: true
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: overlay.removeFace(
                        faceItem.relLeft, faceItem.relTop,
                        faceItem.relRight, faceItem.relBottom)
                }
            }
        }
    }

    // -- új régió húzása egérrel (szerkesztő módban, a CropOverlay mintája,
    // egyszerűsítve: nincs arány-rögzítés/fogantyú, csak létrehozás) ------
    MouseArea {
        id: createArea
        objectName: "facesCreateArea"
        anchors.fill: parent
        visible: overlay.editMode
        enabled: overlay.editMode
        property real startX: 0
        property real startY: 0
        property bool creating: false
        onPressed: function(event) {
            startX = event.x; startY = event.y
            creating = true
            overlay.draftRect = Qt.rect(event.x, event.y, 0, 0)
        }
        onPositionChanged: function(event) {
            if (!creating) return
            // #891: a lenyomott módosító a KÉP saját arányára (Shift), annak
            // 4/3-ára (Ctrl) vagy 3/2-ére (Alt) kényszeríti a téglalapot —
            // Alt üt Ctrl-t, Ctrl üt Shiftet. Minden lépés újraszámol,
            // ezért a billentyű felengedése azonnal felszabadít.
            var r = AranyKenyszer.huzottTeglalap(
                startX, startY, event.x, event.y,
                overlay.width, overlay.height,
                event.modifiers & Qt.ShiftModifier,
                event.modifiers & Qt.ControlModifier,
                event.modifiers & Qt.AltModifier)
            overlay.draftRect = Qt.rect(r.x, r.y, r.width, r.height)
        }
        onReleased: function(event) {
            if (!creating) return
            creating = false
            // #26: az eredeti KÉTLÉPÉSES volt („1) a négyszöget alakítsa
            // úgy, hogy illeszkedjen… 2) kattintson a négyszög alatt
            // látható »Név hozzáadása« feliratra") — a húzás után a
            // téglalap MEGMARAD és igazítható, a név külön lépés.
            if (overlay.draftRect.width < overlay.minSelectionPx
                || overlay.draftRect.height < overlay.minSelectionPx)
                overlay.draftRect = Qt.rect(0, 0, 0, 0)
        }
    }
    // a húzás közbeni draft-téglalap (pixel-koordináták)
    property rect draftRect: Qt.rect(0, 0, 0, 0)

    // #900: az `editpanel/addfaceselection` a téglalapon KÍVÜLI területet
    // ugyanazzal a `negativemode 8f2f2f2f` értékkel sötétíti, mint a vágó.
    // A sötétítés a fogantyúk ALATT rajzolódik, hogy azok olvashatók
    // maradjanak.
    SelectionDim {
        objectName: "faceSelectionDim"
        active: overlay.editMode
                && overlay.draftRect.width > 0 && overlay.draftRect.height > 0
        selX: overlay.draftRect.x
        selY: overlay.draftRect.y
        selW: overlay.draftRect.width
        selH: overlay.draftRect.height
    }

    Rectangle {
        objectName: "faceDraftRect"
        visible: overlay.editMode
                 && overlay.draftRect.width > 0 && overlay.draftRect.height > 0
        x: overlay.draftRect.x; y: overlay.draftRect.y
        width: overlay.draftRect.width; height: overlay.draftRect.height
        color: "#ffd34e33"
        border.color: "#ffd34e"; border.width: 1
    }

    readonly property bool hasDraft:
        overlay.draftRect.width >= overlay.minSelectionPx
        && overlay.draftRect.height >= overlay.minSelectionPx

    // #26: a draft-téglalap oldalai/sarkai húzhatók — az eredeti utasítása
    // szerint („oldalainak mozgatásával pedig pontosíthatja az alakját").
    // A CropOverlay fogantyú-mintáját követi.
    Repeater {
        model: ["nw", "n", "ne", "w", "e", "sw", "s", "se"]
        delegate: Rectangle {
            id: faceHandle
            required property string modelData
            objectName: "faceDraftHandle_" + modelData
            visible: overlay.editMode && overlay.hasDraft
            width: 10; height: 10
            radius: 5
            color: "#ffffff"
            border.width: 1; border.color: "#333333"
            x: overlay.draftHandleX(modelData) - width / 2
            y: overlay.draftHandleY(modelData) - height / 2

            MouseArea {
                anchors.fill: parent
                drag.target: faceHandle
                onPositionChanged: if (drag.active)
                    overlay.resizeDraft(faceHandle.modelData,
                                        faceHandle.x + faceHandle.width / 2,
                                        faceHandle.y + faceHandle.height / 2)
            }
        }
    }

    function draftHandleX(pos) {
        if (pos.indexOf("w") >= 0) return overlay.draftRect.x
        if (pos.indexOf("e") >= 0) return overlay.draftRect.x + overlay.draftRect.width
        return overlay.draftRect.x + overlay.draftRect.width / 2
    }
    function draftHandleY(pos) {
        if (pos.indexOf("n") >= 0) return overlay.draftRect.y
        if (pos.indexOf("s") >= 0) return overlay.draftRect.y + overlay.draftRect.height
        return overlay.draftRect.y + overlay.draftRect.height / 2
    }
    function clampTo(value, low, high) {
        return Math.max(low, Math.min(high, value))
    }
    function resizeDraft(pos, mouseX, mouseY) {
        var left = overlay.draftRect.x
        var top = overlay.draftRect.y
        var right = left + overlay.draftRect.width
        var bottom = top + overlay.draftRect.height
        if (pos.indexOf("w") >= 0)
            left = overlay.clampTo(mouseX, 0, right - overlay.minSelectionPx)
        if (pos.indexOf("e") >= 0)
            right = overlay.clampTo(mouseX, left + overlay.minSelectionPx, overlay.width)
        if (pos.indexOf("n") >= 0)
            top = overlay.clampTo(mouseY, 0, bottom - overlay.minSelectionPx)
        if (pos.indexOf("s") >= 0)
            bottom = overlay.clampTo(mouseY, top + overlay.minSelectionPx, overlay.height)
        overlay.draftRect = Qt.rect(left, top, right - left, bottom - top)
    }

    // „Név hozzáadása" a téglalap ALATT — szó szerint az eredeti
    // utasításának 2. lépése (`peoplepanel/addname` = „Add a name")
    Rectangle {
        objectName: "faceDraftAddName"
        visible: overlay.editMode && overlay.hasDraft
        x: overlay.draftRect.x
        y: Math.min(overlay.height - height,
                    overlay.draftRect.y + overlay.draftRect.height + 4)
        width: Math.max(96, overlay.draftRect.width)
        height: 22
        color: Theme.infoBar
        Text {
            anchors.centerIn: parent
            text: qsTr("Add a name")
            font.pixelSize: Theme.fontSize
            color: Theme.infoBarText
        }
        MouseArea {
            anchors.fill: parent
            onClicked: overlay.openDraftEditor()
        }
    }

    function openDraftEditor() {
        if (!overlay.hasDraft) return
        var r = overlay.draftRect
        overlay.openEditorFor(
            r.x / overlay.width, r.y / overlay.height,
            (r.x + r.width) / overlay.width, (r.y + r.height) / overlay.height,
            "", true)
    }

    // Az eredeti utasítása (`manual_add::instructions`) — a gesztus
    // önmagában nem felfedezhető, ezért ki kell írni.
    Text {
        objectName: "faceEditInstructions"
        visible: overlay.editMode && !overlay.hasDraft
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 8
        wrapMode: Text.WordWrap
        //: #3574: a hivatalos szöveg (`manual_add::instructions`)
        text: qsTr("Instructions:\n\n1) Manipulate the rectangle to fit the face of the person you want to add.\n\nYou can drag the rectangle to position it, and move its sides to refine the shape.\n\n2) Click on \"Add a name\" under the rectangle and type in the person's name.\n\n(Be sure to either press Enter or click on an autocompleted name to indicate that you are done)")
        font.pixelSize: Theme.fontSize
        color: "#ffffff"
        style: Text.Outline
        styleColor: "#000000"
    }

    PicasaButton {
        objectName: "faceManualCancelButton"
        visible: overlay.editMode
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 8
        width: 96
        height: 28
        text: qsTr("Cancel")
        onClicked: overlay.cancelManualAdd()
    }

    // -- névhozzárendelő popup: közös az új régióhoz és az átnevezéshez --
    property rect pendingRect: Qt.rect(0, 0, 0, 0)   // relatív [0..1]
    property bool pendingIsNew: false
    property int pendingDetectedFaceId: -1

    function openEditorFor(relLeft, relTop, relRight, relBottom, currentName, isNew) {
        overlay.pendingRect = Qt.rect(relLeft, relTop, relRight - relLeft, relBottom - relTop)
        overlay.pendingIsNew = isNew
        overlay.pendingDetectedFaceId = -1
        overlay.refreshKnownNames()
        nameField.text = currentName || ""
        editorPopup.visible = true
        nameField.forceActiveFocus()
        nameField.selectAll()
    }
    function openEditorForDetected(relLeft, relTop, relRight, relBottom, detectedFaceId) {
        var candidateDetectedFaceId = Number(detectedFaceId)
        if (!(candidateDetectedFaceId > 0)) return
        overlay.openEditorFor(relLeft, relTop, relRight, relBottom, "", false)
        overlay.pendingDetectedFaceId = candidateDetectedFaceId
    }
    function closeEditor() {
        editorPopup.visible = false
        overlay.pendingDetectedFaceId = -1
        overlay.selectedDetectedFaceId = -1
        overlay.draftRect = Qt.rect(0, 0, 0, 0)
    }
    function commitEditor() {
        if (!overlay.hasHelper) { overlay.closeEditor(); return }
        var r = overlay.pendingRect
        var name = (nameField.text || "").trim()
        var ok
        if (overlay.pendingIsNew && !name) {
            overlay.closeEditor()
            return
        }
        if (overlay.pendingDetectedFaceId >= 0) {
            if (!name || typeof faceScanController === "undefined"
                    || !faceScanController) {
                overlay.closeEditor()
                return
            }
            ok = faceScanController.assignNameToFaces(
                [overlay.pendingDetectedFaceId], name)
        } else if (overlay.pendingIsNew)
            ok = facesHelper.addFace(overlay.imagePath, r.x, r.y, r.x + r.width, r.y + r.height, name)
        else
            ok = facesHelper.renameFace(overlay.imagePath, r.x, r.y, r.x + r.width, r.y + r.height, name)
        overlay.closeEditor()
        if (ok) overlay.edited()
    }
    function removeFace(relLeft, relTop, relRight, relBottom) {
        if (!overlay.hasHelper) return
        var ok = facesHelper.removeFace(overlay.imagePath, relLeft, relTop, relRight, relBottom)
        if (ok) overlay.edited()
    }

    Rectangle {
        id: editorPopup
        objectName: "faceNameEditor"
        visible: false
        readonly property real nameBarHeight: overlay.width * 20 / 538
        width: overlay.width * 204 / 538
        height: nameBarHeight
                + (suggestionsColumn.visible
                   ? suggestionsColumn.implicitHeight + 4 : 0)
        radius: 0
        color: "#101010e8"
        border.width: 0
        x: overlay.clamp(
                          (overlay.pendingRect.x
                           + overlay.pendingRect.width / 2) * overlay.width
                          - width / 2,
                          0, Math.max(0, overlay.width - width))
        // A névsáv a keret alsó élénél indul, hézag nélkül.
        y: (overlay.pendingRect.y + overlay.pendingRect.height) * overlay.height
        z: 10

        Row {
            id: nameRow
            anchors.top: parent.top
            anchors.left: parent.left; anchors.right: parent.right
            height: editorPopup.nameBarHeight
            TextField {
                id: nameField
                objectName: "faceNameField"
                anchors.fill: parent
                leftPadding: 4
                rightPadding: 4
                topPadding: 0
                bottomPadding: 0
                placeholderText: qsTr("Type a name")
                font.pixelSize: Theme.fontSize - 1
                color: "#ffffff"
                placeholderTextColor: "#d0d0d0"
                selectionColor: "#3096f3"
                selectedTextColor: "#ffffff"
                background: Rectangle {
                    color: "transparent"
                    border.width: 0
                }
                Keys.onReturnPressed: overlay.commitEditor()
                Keys.onEnterPressed: overlay.commitEditor()
                Keys.onEscapePressed: overlay.closeEditor()
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }
        // ismert nevek gyors-választása (legfeljebb 5, a beírt szöveget
        // tartalmazó, kis-nagybetű-tűrő találat) — kattintásra kitölti a
        // mezőt ÉS azonnal megerősít
        Column {
            id: suggestionsColumn
            objectName: "faceNameSuggestions"
            visible: matches.length > 0
            // #402: a nameField a Row gyereke, nem testvér — a horgony a
            // testvér nameRow-ra kell mutasson (QML-anchor-szabály)
            anchors.top: nameRow.bottom
            anchors.left: parent.left; anchors.right: parent.right
            anchors.topMargin: 4
            anchors.leftMargin: 6; anchors.rightMargin: 6
            spacing: 2
            readonly property var matches: {
                var text = (nameField.text || "").toLowerCase()
                if (!text) return []
                return overlay.knownNames.filter(function(n) {
                    return n.toLowerCase().indexOf(text) >= 0 && n !== nameField.text
                }).slice(0, 5)
            }
            Repeater {
                model: suggestionsColumn.matches
                delegate: Text {
                    required property string modelData
                    required property int index
                    objectName: "faceNameSuggestion_" + index
                    text: modelData
                    color: "#ffffff"
                    font.pixelSize: Theme.fontSize - 2
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            nameField.text = modelData
                            overlay.commitEditor()
                        }
                    }
                }
            }
        }
    }
}
