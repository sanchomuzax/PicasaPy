import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #26 (3. lépcső): a „Névtelenek" album felülete — SAJÁT (YuNet/SFace)
// arcfelismerés, a Picasa munkamenete szerint: csoportosítás-váltógomb,
// arconkénti kijelölés, „Add a name" tömeges névadás.
//
// Szándékosan ÖNÁLLÓ komponens (nem a fő rács/`controller._show()` útján),
// mert a `FaceScanController` is önálló QObject, NEM az `AppController`
// mixinje (ld. face_scan_controller.py modul-docstring) — a Main.qml csak
// egy Loader-szerű látszás/rejtés kapcsolót kap.
//
// Egyszerűsítés (jelentve az issue-ban): a bélyegkép a TELJES fotó, nem az
// arc-téglalapra vágott index-kép — a Picasa-hű arc-vágás egy későbbi
// kör finomítása.
ColumnLayout {
    id: root
    property var faceScanController: null
    signal showIgnoredRequested()
    signal showUnnamedRequested()
    // #26: „unnamed" = a Névtelenek album, „ignored" = a Mellőzött emberek
    // album (`CAlbumLabel::Ignored`). Az eredetiben ez két ALBUM volt
    // ugyanabban a listában, ezért ugyanaz a nézet szolgálja ki — csak a
    // tartalom és a művelet-gombok mások.
    property string mode: "unnamed"
    readonly property bool ignoredMode: root.mode === "ignored"
    // #3585 (spec 9/d): az eredetiben EGY váltógomb két arca
    // (`unknownfaceheaderpanel/cluster` ↔ `showall`, egymást rejtik), nem
    // két független kapcsoló. Csoportosítva a csoportok előnézete látszik,
    // kibontva minden arcuk. Az album megnyitásakor csoportosítva indul
    // (`0x0074cbbb`).
    property bool grouped: true
    // a csoportosítás (lenyomat + csoportba sorolás) épp fut — ilyenkor a
    // fejléc-utasítás várakozást kér (`CAlbumLabel::LoadingGrouped`)
    property bool groupingInProgress: false
    property var groupsModel: []
    property var selectedFaceIds: ({})
    property int selectedCount: 0
    // #3670: a megerősítésre váró mellőzés arcai — a bélyegkép X-e EGY
    // arcot kérdez meg (a kijelöléstől függetlenül), a Mellőzés gomb a
    // kijelölést
    property var pendingIgnoreIds: []
    // #3670: a „Ne kérdezzen újból" jelölő döntés-kulcsa a közös
    // `confirmSettings` tárban (#367). Az eredeti beállításkulcs neve
    // nincs kimérve; a viselkedés a mért jelölőé.
    readonly property string ignoreConfirmKey: "ignoreFaces"
    spacing: 8

    function reload() {
        if (!faceScanController) {
            root.groupsModel = []
            return
        }
        root.groupsModel = (root.mode === "ignored")
            ? faceScanController.ignoredGroups()
            : faceScanController.unnamedGroups(true, !root.grouped)
    }

    function toggleFace(faceId) {
        var current = root.selectedFaceIds
        if (current[faceId]) {
            delete current[faceId]
        } else {
            current[faceId] = true
        }
        root.selectedFaceIds = current
        root.selectedCount = Object.keys(current).length
    }

    function clearSelection() {
        root.selectedFaceIds = ({})
        root.selectedCount = 0
    }

    // a kijelölés kulcsai: a saját arc száma, a csak a `.picasa.ini`-ben
    // mellőzött arc (#3670) `ini:` kezdetű szöveges kulcsa
    function selectedKeys() {
        var keys = []
        for (var key in root.selectedFaceIds)
            keys.push(/^[0-9]+$/.test(key) ? parseInt(key) : key)
        return keys
    }

    // #3585: a fejléc-utasítás a `0x0074c200` választása szerint — a
    // `stringres` négy szövege (`CAlbumLabel::*`)
    readonly property string instructionText:
        root.grouped && root.groupingInProgress
            ? qsTr("Grouping faces, please wait...")
            : root.grouped && root.ignoredMode
              ? qsTr("Select someone you know and add a name.")
              : root.grouped
                ? qsTr("Select someone you know and add a name, or click "
                       + "the \"x\" to ignore that person.")
                : qsTr("Select someone you know and add a name")

    Component.onCompleted: reload()
    onModeChanged: {
        root.clearSelection()
        root.grouped = true
        root.reload()
    }
    onGroupedChanged: { clearSelection(); reload() }
    onVisibleChanged: if (visible) { root.grouped = true; reload() }

    Connections {
        target: root.faceScanController || null
        ignoreUnknownSignals: true
        function onEmbeddingStarted() { root.groupingInProgress = true }
        function onEmbeddingFinished() {
            root.groupingInProgress = false
            if (root.visible) root.reload()
        }
        function onEmbeddingCancelled() { root.groupingInProgress = false }
        function onEmbeddingFailed() { root.groupingInProgress = false }
        function onEmbeddingModelUnavailable() {
            root.groupingInProgress = false
        }
    }

    Text {
        objectName: "unnamedInstructions"
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: root.instructionText
        font.pixelSize: Theme.fontSize
        color: Theme.textDark
    }

    // A két eredeti fejléc-váltó ugyanazt a nézetet kapcsolja a két album
    // között (`unknownfaceheaderpanel.tre:38` és `:43`). A gazda állítja a
    // módot, így a bal oldali albumjelölés és a látható tartalom együtt vált.
    RowLayout {
        objectName: "unknownFaceViewHeader"
        Layout.fillWidth: true
        spacing: 5

        Item { Layout.fillWidth: true }
        Button {
            id: clusterToggleButton
            objectName: "clusterToggleButton"
            visible: !root.ignoredMode
            Layout.preferredWidth: 120
            Layout.preferredHeight: 27
            // #3585: a felirat a KÖVETKEZŐ állapotot nevezi meg —
            // csoportosítva a részletes nézet, kibontva a csoportosítás.
            text: root.grouped ? qsTr("Expand groups") : qsTr("Group by face")
            onClicked: root.grouped = !root.grouped
        }
        Item {
            objectName: "unknownFaceViewTypeContainer"
            Layout.preferredWidth: 120
            Layout.preferredHeight: 27

            PicasaButton {
                objectName: "unknownfaceheaderpanel/showignored"
                anchors.fill: parent
                visible: !root.ignoredMode
                text: qsTr("Show ignored faces")
                onClicked: root.showIgnoredRequested()
            }
            PicasaButton {
                objectName: "unknownfaceheaderpanel/showunknown"
                anchors.fill: parent
                visible: root.ignoredMode
                text: qsTr("Back to Unnamed")
                onClicked: root.showUnnamedRequested()
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 14

        Item { Layout.fillWidth: true }
        Text {
            text: root.selectedCount > 0
                  ? qsTr("%1 selected").arg(root.selectedCount)
                  : ""
            color: Theme.textDark
        }
        TextField {
            id: nameField
            objectName: "unnamedNameField"
            visible: !root.ignoredMode
            Layout.preferredWidth: 180
            placeholderText: qsTr("Name")
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
        // #26: „Ignore" — az eredetiben a mellőzés NEM törlés volt: a
        // személy a „Mellőzött emberek" albumba került
        // (`DeleteMessage::RemoveSingleUnknown`), külön megerősítéssel.
        // #26: a Mellőzött emberek albumban a mellőzés VISSZAVONÁSA a
        // művelet — az eredetiben is album volt, tehát vissza lehetett
        // nyúlni belőle, nem egyirányú szemetes
        Button {
            objectName: "unignoreFacesButton"
            visible: root.ignoredMode
            text: qsTr("Stop ignoring")
            enabled: root.selectedCount > 0 && !!root.faceScanController
            onClicked: root.unignoreSelected()
        }
        Button {
            id: ignoreButton
            objectName: "ignoreFacesButton"
            visible: !root.ignoredMode
            text: qsTr("Ignore")
            enabled: root.selectedCount > 0 && !!root.faceScanController
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Ignore all of the selected faces")
            ToolTip.delay: Theme.tooltipDelay
            onClicked: root.requestIgnore(root.selectedKeys())
        }
        // #3237: „További javaslatok keresése" — az eredeti `moresug`
        // parancsa (kezelő `0x00602890`). A felismerési küszöböt EGYSZERI
        // alkalommal lazítja (a lépcsőt tízzel), és a beállítást NEM írja
        // vissza — a mért viselkedés. A mellőzött nézetben nincs értelme,
        // ezért ott nem látszik.
        Button {
            objectName: "moreSuggestionsButton"
            visible: !root.ignoredMode
            text: qsTr("Look for more suggestions")
            enabled: !!root.faceScanController
            ToolTip.visible: hovered
            ToolTip.text: qsTr(
                "Lowers the recognition threshold once, so more names are "
                + "suggested. The stored setting is left unchanged.")
            ToolTip.delay: Theme.tooltipDelay
            onClicked: {
                root.faceScanController.moreSuggestions()
                root.reload()
            }
        }
        Button {
            id: addNameButton
            objectName: "addNameButton"
            visible: !root.ignoredMode
            text: qsTr("Add a name")
            enabled: root.selectedCount > 0
                     && nameField.text.trim().length > 0
                     && !!root.faceScanController
            ToolTip.visible: hovered
            ToolTip.text: qsTr(
                "Assign a name to all of the selected faces")
            ToolTip.delay: Theme.tooltipDelay
            onClicked: {
                var ids = []
                var key
                for (key in root.selectedFaceIds) {
                    ids.push(parseInt(key))
                }
                var ok = root.faceScanController.assignNameToFaces(
                    ids, nameField.text.trim())
                if (ok) {
                    nameField.text = ""
                    root.clearSelection()
                    root.reload()
                    if (typeof controller !== "undefined" && controller) {
                        controller.refreshCollections()
                    }
                }
            }
        }
    }

    ListView {
        id: groupsList
        objectName: "unnamedGroupsList"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 12
        model: root.groupsModel
        ScrollBar.vertical: PicasaScrollBar {}

        delegate: ColumnLayout {
            id: groupDelegate
            required property var modelData
            width: groupsList.width
            spacing: 4

            Text {
                text: groupDelegate.modelData.label
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.textDark
            }

            GridView {
                id: faceGrid
                objectName: "unnamedFaceGrid"
                Layout.fillWidth: true
                interactive: false
                cellWidth: 96
                cellHeight: 96
                readonly property int columns:
                    Math.max(1, Math.floor(width / cellWidth))
                height: Math.ceil(
                    groupDelegate.modelData.faces.length
                    / Math.max(1, columns)) * cellHeight
                model: groupDelegate.modelData.faces

                delegate: Rectangle {
                    id: faceTile
                    required property var modelData
                    objectName: "faceTile_" + faceTile.modelData.faceId
                    width: faceGrid.cellWidth - 6
                    height: faceGrid.cellHeight - 6
                    color: "transparent"
                    border.width: 2
                    border.color: root.selectedFaceIds[faceTile.modelData.faceId]
                                  ? Theme.panelSelectionActive : "transparent"

                    Image {
                        anchors.fill: parent
                        anchors.margins: 3
                        source: faceTile.modelData.thumbUrl
                        // #1600: a bélyegkép-textúra a Qt gyorsítótárában KÖZÖS a
                        // ráccsal, ami mipmapot kér (#83). Eltérő beállítás mellett a Qt
                        // „Mipmap settings changed" figyelmeztetést ad, és VISSZAESIK a
                        // korábbi szűrésre — a kép nem azzal a szűréssel jelenik meg,
                        // amit kértünk (a tulajdonos Windowson hatszor látta).
                        smooth: true
                        mipmap: true
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.toggleFace(faceTile.modelData.faceId)
                    }

                    // #3670: a bélyegkép „X"-e a mellőzés — az eredeti
                    // tájékoztatója: „To ignore a person, click the 'X'
                    // button on the face thumbnail." Ugyanazt a kérdést és
                    // ugyanazt a `.picasa.ini`-írást adja, mint a fejléc
                    // Mellőzés gombja (spec 15.3/b.1).
                    Rectangle {
                        objectName: "faceIgnoreX_" + faceTile.modelData.faceId
                        visible: !root.ignoredMode
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.margins: 4
                        width: 18
                        height: 18
                        radius: 9
                        color: Theme.infoBar
                        Text {
                            anchors.centerIn: parent
                            text: "✕"
                            font.pixelSize: Theme.fontSize - 1
                            color: Theme.infoBarText
                        }
                        MouseArea {
                            anchors.fill: parent
                            anchors.margins: -2
                            onClicked: root.requestIgnore(
                                [faceTile.modelData.faceId])
                        }
                    }

                    // #26: név-javaslat — az eredeti KÉRDÉSKÉNT vetette
                    // fel („Anna?", `PeoplePanel::SuggestionFmt` = „%s?"),
                    // és a felhasználó pipával erősítette meg
                    // (`PeopleAlbum::ConfirmText`: „Press checkmark to
                    // confirm match, press "x" to ignore."). Az „x" a
                    // csempe sarkában ülő mellőzés (#3670) — a javaslat
                    // csendes elvetése nem az eredeti művelete.
                    Rectangle {
                        objectName: "suggestionBar_" + faceTile.modelData.faceId
                        visible: (faceTile.modelData.suggestedName || "") !== ""
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 3
                        height: 20
                        color: Theme.infoBar

                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 4
                            spacing: 4
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width - 22
                                elide: Text.ElideRight
                                //: a javasolt név kérdésként — az eredeti
                                //: formátuma egyszerűen „%s?"
                                text: qsTr("%1?").arg(
                                    faceTile.modelData.suggestedName || "")
                                font.pixelSize: Theme.fontSize - 1
                                color: Theme.infoBarText
                            }
                            Text {
                                objectName: "suggestionYes_"
                                            + faceTile.modelData.faceId
                                anchors.verticalCenter: parent.verticalCenter
                                text: "✓"
                                color: Theme.infoBarText
                                MouseArea {
                                    anchors.fill: parent
                                    anchors.margins: -4
                                    onClicked: root.acceptSuggestion(
                                        faceTile.modelData.faceId)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Az eredeti megerősítés — szó szerinti szövegekkel
    // (`PeoplePanel::ConfirmRemoveTitle` / `ConfirmRemoveMsg` /
    // `ConfirmRemoveYesButton` / `ConfirmRemoveCheck`, spec 15.3/b.1).
    Dialog {
        id: ignoreConfirm
        objectName: "ignoreFacesDialog"
        title: qsTr("Ignore People")
        modal: true
        anchors.centerIn: Overlay.overlay
        standardButtons: Dialog.Yes | Dialog.Cancel
        onOpened: standardButton(Dialog.Yes).text =
            root.pendingIgnoreIds.length > 1 ? qsTr("Ignore People")
                                             : qsTr("Ignore Person")
        onAccepted: {
            if (dontAskCheck.checked && typeof confirmSettings !== "undefined"
                    && confirmSettings)
                confirmSettings.setSuppressed(root.ignoreConfirmKey, true)
            root.ignorePending()
        }
        onRejected: root.pendingIgnoreIds = []

        ColumnLayout {
            spacing: 12
            // Label: a párbeszéd palettáját örökli (a CheckBox is), így
            // sötét párbeszéd-háttéren sem sötét a szöveg
            Label {
                objectName: "ignoreFacesMessage"
                Layout.preferredWidth: 380
                wrapMode: Text.WordWrap
                text: root.pendingIgnoreIds.length > 1
                      ? qsTr("Are you sure you want to move the %1 selected "
                             + "people to the ignored people album?")
                        .arg(root.pendingIgnoreIds.length)
                      : qsTr("Are you sure you want to move this person to the "
                             + "ignored people album?")
                font.pixelSize: Theme.fontSize
            }
            CheckBox {
                id: dontAskCheck
                objectName: "ignoreFacesDontAskCheck"
                //: `PeoplePanel::ConfirmRemoveCheck`
                text: qsTr("Don't ask again, always ignore")
                font.pixelSize: Theme.fontSize
            }
        }
    }

    // #3670: a mellőzés belépési pontja (X és Mellőzés gomb) — kérdez,
    // hacsak a felhasználó korábban be nem pipálta a „Ne kérdezzen
    // újból"-t
    function requestIgnore(ids) {
        if (!root.faceScanController || !ids || ids.length === 0) return
        root.pendingIgnoreIds = ids
        if (typeof confirmSettings !== "undefined" && confirmSettings
                && confirmSettings.isSuppressed(root.ignoreConfirmKey)) {
            root.ignorePending()
            return
        }
        dontAskCheck.checked = false
        ignoreConfirm.open()
    }

    // #26: a javaslat elfogadása — külön, hívható függvényben
    // (tesztelhetőség: a GridView delegate-jei nem érhetők el findChild-dal)
    function acceptSuggestion(faceId) {
        if (!root.faceScanController) return false
        var ok = root.faceScanController.acceptSuggestion(faceId)
        if (ok) {
            root.reload()
            if (typeof controller !== "undefined" && controller)
                controller.refreshCollections()
        }
        return ok
    }
    // a mellőzés visszavonása — külön, hívható függvényben
    function unignoreSelected() {
        if (!root.faceScanController) return 0
        var ids = root.selectedKeys()
        if (ids.length === 0) return 0
        var count = root.faceScanController.unignoreFaces(ids)
        root.clearSelection()
        root.reload()
        return count
    }

    // a tényleges mellőzés — külön, hívható függvényben (tesztelhetőség)
    function ignoreSelected() {
        root.pendingIgnoreIds = root.selectedKeys()
        return root.ignorePending()
    }

    function ignorePending() {
        var ids = root.pendingIgnoreIds
        root.pendingIgnoreIds = []
        if (!root.faceScanController || ids.length === 0) return 0
        var count = root.faceScanController.ignoreFaces(ids)
        root.clearSelection()
        root.reload()
        return count
    }
}
