import QtQuick
import QtQuick.Controls

// #147: a mentett faces= régiók megjelenítése a nézőben. #26 (2. kör):
// SZERKESZTŐ mód — új arc-téglalap húzása egérrel, név hozzárendelése
// (meglévő személy-listából vagy új névvel), régió törlése/átnevezése.
// Az írás a `facesHelper`-en (QML-kontextus) át, ütközésbiztos ini-írással
// történik (picasapy.app.faces_helper.FacesHelper) — az overlay maga
// állapotmentes a mentett adatra nézve, csak a MEGRAJZOLÁS/POPUP saját
// átmeneti állapotát tartja.
Item {
    id: overlay
    objectName: "facesOverlay"

    // {left, top, right, bottom, name} elemek relatív [0..1] koordinátákkal
    // — a FacesHelper.facesFor() visszatérési formátuma.
    property var faces: []
    // szerkesztő mód: a rajzolás/törlés/átnevezés csak ekkor aktív — a
    // sima megtekintésnél (facesVisible, F billentyű) az overlay csak
    // mutat, nem fogad egérműveletet
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

    function refreshKnownNames() {
        overlay.knownNames = overlay.hasHelper && overlay.imagePath
            ? facesHelper.knownNames(overlay.imagePath) : []
    }
    onImagePathChanged: refreshKnownNames()
    onEditModeChanged: if (editMode) refreshKnownNames()

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

            x: relLeft * overlay.width
            y: relTop * overlay.height
            width: Math.max(0, (relRight - relLeft) * overlay.width)
            height: Math.max(0, (relBottom - relTop) * overlay.height)

            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.color: "#ffd34e"
                border.width: 2
                radius: 2
            }
            Rectangle {
                visible: nameLabel.text.length > 0
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
                visible: overlay.editMode
                enabled: overlay.editMode
                cursorShape: Qt.PointingHandCursor
                onClicked: overlay.openEditorFor(
                    faceItem.relLeft, faceItem.relTop,
                    faceItem.relRight, faceItem.relBottom,
                    faceItem.personName, false)
            }
            Rectangle {
                objectName: "faceDeleteButton_" + faceItem.index
                visible: overlay.editMode
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
            var left = Math.min(startX, event.x)
            var top = Math.min(startY, event.y)
            var w = Math.abs(event.x - startX)
            var h = Math.abs(event.y - startY)
            overlay.draftRect = Qt.rect(left, top, w, h)
        }
        onReleased: function(event) {
            if (!creating) return
            creating = false
            if (overlay.draftRect.width < overlay.minSelectionPx
                || overlay.draftRect.height < overlay.minSelectionPx) {
                overlay.draftRect = Qt.rect(0, 0, 0, 0)
                return
            }
            var r = overlay.draftRect
            overlay.openEditorFor(
                r.x / overlay.width, r.y / overlay.height,
                (r.x + r.width) / overlay.width, (r.y + r.height) / overlay.height,
                "", true)
        }
    }
    // a húzás közbeni draft-téglalap (pixel-koordináták)
    property rect draftRect: Qt.rect(0, 0, 0, 0)
    Rectangle {
        visible: overlay.editMode
                 && overlay.draftRect.width > 0 && overlay.draftRect.height > 0
        x: overlay.draftRect.x; y: overlay.draftRect.y
        width: overlay.draftRect.width; height: overlay.draftRect.height
        color: "#ffd34e33"
        border.color: "#ffd34e"; border.width: 1
    }

    // -- névhozzárendelő popup: közös az új régióhoz és az átnevezéshez --
    property rect pendingRect: Qt.rect(0, 0, 0, 0)   // relatív [0..1]
    property bool pendingIsNew: false

    function openEditorFor(relLeft, relTop, relRight, relBottom, currentName, isNew) {
        overlay.pendingRect = Qt.rect(relLeft, relTop, relRight - relLeft, relBottom - relTop)
        overlay.pendingIsNew = isNew
        overlay.refreshKnownNames()
        nameField.text = currentName || ""
        editorPopup.visible = true
        nameField.forceActiveFocus()
        nameField.selectAll()
    }
    function closeEditor() {
        editorPopup.visible = false
        overlay.draftRect = Qt.rect(0, 0, 0, 0)
    }
    function commitEditor() {
        if (!overlay.hasHelper) { overlay.closeEditor(); return }
        var r = overlay.pendingRect
        var name = nameField.text
        var ok
        if (overlay.pendingIsNew)
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
        width: 190
        height: suggestionsColumn.visible ? 96 : 40
        radius: 4
        color: "#2b2b2bee"
        border.color: "#555555"
        x: overlay.clamp(overlay.pendingRect.x * overlay.width,
                          0, Math.max(0, overlay.width - width))
        y: overlay.clamp(overlay.pendingRect.y * overlay.height + overlay.pendingRect.height * overlay.height + 4,
                          0, Math.max(0, overlay.height - height))
        z: 10

        Row {
            id: nameRow
            anchors.top: parent.top
            anchors.left: parent.left; anchors.right: parent.right
            anchors.margins: 6
            spacing: 4
            TextField {
                id: nameField
                objectName: "faceNameField"
                width: parent.width - 56
                placeholderText: qsTr("Name")
                font.pixelSize: Theme.fontSize - 1
                Keys.onReturnPressed: overlay.commitEditor()
                Keys.onEscapePressed: overlay.closeEditor()
            }
            Button {
                objectName: "faceNameOk"
                text: "✓"
                width: 24
                onClicked: overlay.commitEditor()
            }
            Button {
                objectName: "faceNameCancel"
                text: "×"
                width: 24
                onClicked: overlay.closeEditor()
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
