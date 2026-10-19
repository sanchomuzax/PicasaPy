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
// A csempék URL-je a saját arc-téglalapjukat adja át a közös
// bélyegkép-szolgáltatónak, így nem a fotó közepe jelenik meg.
ColumnLayout {
    id: root
    property var faceScanController: null
    signal showIgnoredRequested()
    signal showUnnamedRequested()
    signal nameSubmitted(int faceId, string name)
    signal namedSuggestionAccepted()
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
    property var facesModel: []
    property bool hasIgnoredFaces: false
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
    // A Picasa kibontott fejlécének és rácsának függőleges eltolása a
    // job-208 képe alapján; az alap és a Mellőzött nézet helye változatlan.
    Layout.topMargin: !root.ignoredMode && !root.grouped ? -10 : 0
    spacing: 8

    function reload() {
        if (!faceScanController) {
            root.groupsModel = []
            root.facesModel = []
            root.hasIgnoredFaces = false
            return
        }
        var ignored = faceScanController.ignoredGroups()
        root.hasIgnoredFaces = false
        for (var i = 0; i < ignored.length; ++i) {
            if (ignored[i].faces && ignored[i].faces.length > 0) {
                root.hasIgnoredFaces = true
                break
            }
        }
        var groups = (root.mode === "ignored")
            ? ignored : faceScanController.unnamedGroups(true, !root.grouped)
        root.groupsModel = groups
        var faces = []
        for (var j = 0; j < groups.length; ++j) {
            for (var k = 0; k < groups[j].faces.length; ++k)
                faces.push(groups[j].faces[k])
        }
        root.facesModel = faces
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

    function showWelcomeIfFirstOpen() {
        if (!root.faceScanController || root.ignoredMode
                || root.faceScanController.unnamedWelcomeHasBeenShown())
            return
        Qt.callLater(function() {
            if (root.visible && !root.ignoredMode
                    && !root.faceScanController.unnamedWelcomeHasBeenShown())
                welcomeDialog.open()
        })
    }

    // #5185: a „Learn more...” a Picasa súgóját nyitja az alapértelmezett
    // böngészőben (`instructionpanel/learn_more`, 19.2). A `hl` a felület
    // nyelvéből jön; az üdvözlőablak a kattintás után is nyitva marad.
    function learnMoreUrl() {
        return "http://picasa.google.com/support/bin/answer.py?hl="
            + (controller ? controller.helpLanguageCode : "")
            + "&answer=156272"
    }

    Component.onCompleted: reload()
    onModeChanged: {
        root.clearSelection()
        root.grouped = true
        root.reload()
    }
    onGroupedChanged: { clearSelection(); reload() }
    onVisibleChanged: if (visible) {
        root.grouped = true
        reload()
        root.showWelcomeIfFirstOpen()
    }

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

    // #5343: a fejléc sávja (`unknownfaceheaderpanel/headerbase`, #eaeaea,
    // 82 px; a bal széle 12 px-rel az ikon előtt, a teteje 7 px-rel az ikon
    // fölött). Nulla magasságú elemben él; a fejléc felső margója (-8)
    // kiegyenlíti a 8 px-es sorközt, így a fejléc helye nem változik. Az
    // árnyék nem látszik a mért képen: a sáv alja közvetlenül a törzs
    // színébe megy.
    Item {
        Layout.fillWidth: true
        Layout.preferredHeight: 0
        Layout.alignment: Qt.AlignTop
        Rectangle {
            objectName: "unnamedHeaderBandFill"
            x: -28
            y: -7
            width: root.width + 28
            height: 82
            color: Theme.canvasBg
        }
        // #5352: a sáv alatti törzs az eredeti szürke háttere (job-208:
        // #e2e2e2 = `chromeBg`); a sötét témában a mai szín marad.
        Rectangle {
            objectName: "unnamedBodyFill"
            visible: !Theme.dark
            x: -28
            y: 75
            width: root.width + 28
            height: Math.max(0, root.height - 75)
            color: Theme.chromeBg
        }
    }

    // A két eredeti fejléc-váltó ugyanazt a nézetet kapcsolja a két album
    // között (`unknownfaceheaderpanel.tre:38` és `:43`). A gazda állítja a
    // módot, így a bal oldali albumjelölés és a látható tartalom együtt vált.
    RowLayout {
        objectName: "unknownFaceViewHeader"
        Layout.fillWidth: true
        Layout.preferredHeight: 36
        Layout.topMargin: -root.spacing
        spacing: 5

        RowLayout {
            objectName: "unnamedTitleBlock"
            visible: true
            Layout.leftMargin: -16
            spacing: 4

            Image {
                objectName: "unnamedTitleIcon"
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                source: Qt.resolvedUrl("icons/person-silhouette.svg")
                fillMode: Image.PreserveAspectFit
                smooth: true
            }
            // #5343: az eredeti címe Georgia 24 (unknownfaceheaderpanel.tre:7-8)
            Text {
                objectName: "unnamedAlbumTitle"
                text: root.ignoredMode
                      ? qsTr("Ignored people") : qsTr("Unnamed people")
                font.family: "Georgia"
                font.pixelSize: 24
                color: "#68564f"
            }
        }
        Item { Layout.fillWidth: true }
        PicasaButton {
            id: clusterToggleButton
            objectName: "clusterToggleButton"
            visible: true
            Layout.preferredWidth: 120
            Layout.preferredHeight: 27
            font.pixelSize: Theme.buttonLabelSize
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
                enabled: root.hasIgnoredFaces
                font.pixelSize: Theme.buttonLabelSize
                text: qsTr("Show ignored faces")
                onClicked: root.showIgnoredRequested()
            }
            PicasaButton {
                objectName: "unknownfaceheaderpanel/showunknown"
                anchors.fill: parent
                visible: root.ignoredMode
                font.pixelSize: Theme.buttonLabelSize
                text: qsTr("Back to Unnamed")
                onClicked: root.showUnnamedRequested()
            }
        }
    }

    // #5324: a „N Face(s)” sor a fejléc alatt, az útmutató FÖLÖTT. A darabszám
    // bal széle az ikon bal széléhez igazodik; jobbra
    // kibontott módban a névmező és az „Ignore Selected” gomb, a felső
    // gombpár jobb szélére igazítva. Mellőzött módban a kijelölésszámláló és
    // a „Stop ignoring” ugyanitt marad.
    // #5343: a sor magassága mindkét állapotban 27 px (a kibontott sor
    // gombja adja), így a felirat és a rács helye nem ugrik a váltáskor; az
    // eredetiben sem ugrik (j1_csoportositott és j1_kibontott: a felirat y=170).
    RowLayout {
        objectName: "unnamedFaceRow"
        Layout.fillWidth: true
        Layout.preferredHeight: 27
        spacing: 6

        Text {
            objectName: "unnamedAlbumFaceCount"
            visible: true
            Layout.leftMargin: -16
            Layout.alignment: Qt.AlignVCenter
            text: root.ignoredMode
                  ? qsTr("%d Face(s)").replace("%d", String(root.facesModel.length))
                  : root.faceScanController
                    ? qsTr("%d Face(s)").replace(
                          "%d", String(root.faceScanController.unnamedCount))
                    : qsTr("%d Face(s)").replace("%d", "0")
            font.pixelSize: Theme.buttonLabelSize
            color: Theme.textGray
        }
        Item { Layout.fillWidth: true }
        Text {
            visible: root.ignoredMode && root.selectedCount > 0
            Layout.alignment: Qt.AlignVCenter
            text: root.selectedCount > 0
                  ? qsTr("%1 selected").arg(root.selectedCount)
                  : ""
            color: Theme.textDark
        }
        TextField {
            id: nameField
            objectName: "unnamedNameField"
            visible: !root.ignoredMode && !root.grouped
            Layout.alignment: Qt.AlignVCenter
            // #5343: az eredeti `addname` 163×20 (respack `0x0033b098`)
            Layout.preferredWidth: 163
            Layout.minimumWidth: 163
            Layout.preferredHeight: 20
            height: 20
            placeholderText: qsTr("Add a name")
            // #5214: az eredetiben (job-183) fehér, keretes mező, mint a csempéé
            background: Rectangle {
                color: "#ffffff"
                border.color: "#8a8a8a"
                border.width: 1
            }
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
            onAccepted: root.nameSelectedFaces(text)
            // #5343: az eredeti `unknownfaceheaderpanel/addname` súgója
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Assign a name to all of the selected faces")
            ToolTip.delay: Theme.tooltipDelay
        }
        // #26: „Ignore" - az eredetiben a mellőzés NEM törlés volt: a
        // személy a „Mellőzött emberek" albumba került
        // (`DeleteMessage::RemoveSingleUnknown`), külön megerősítéssel.
        // #26: a Mellőzött emberek albumban a mellőzés VISSZAVONÁSA a
        // művelet - az eredetiben is album volt, tehát vissza lehetett
        // nyúlni belőle, nem egyirányú szemetes
        Button {
            objectName: "unignoreFacesButton"
            visible: root.ignoredMode && root.selectedCount > 0
            Layout.alignment: Qt.AlignVCenter
            text: qsTr("Stop ignoring")
            enabled: root.selectedCount > 0 && !!root.faceScanController
            onClicked: root.unignoreSelected()
        }
        PicasaButton {
            id: ignoreButton
            objectName: "ignoreFacesButton"
            visible: !root.ignoredMode && !root.grouped
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: 120
            Layout.preferredHeight: 27
            font.pixelSize: Theme.buttonLabelSize
            text: qsTr("Ignore Selected")
            enabled: root.selectedCount > 0 && !!root.faceScanController
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Ignore all of the selected faces")
            ToolTip.delay: Theme.tooltipDelay
            onClicked: root.requestIgnore(root.selectedKeys())
        }
        // #3237: „További javaslatok keresése" - az eredeti `moresug`
        // parancsa (kezelő `0x00602890`). A felismerési küszöböt EGYSZERI
        // alkalommal lazítja (a lépcsőt tízzel), és a beállítást NEM írja
        // vissza - a mért viselkedés. A mellőzött nézetben nincs értelme,
        // ezért ott nem látszik.
        // #5135_c / #5183: a Név nélküliek albumában szándékosan nem látszik
        // (a közös névsor-műveletek kikerültek ebből a nézetből); a funkció a
        // menüből érhető el (Main.qml: findMoreSuggestions).
        Button {
            objectName: "moreSuggestionsButton"
            visible: false
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
    }

    Text {
        objectName: "unnamedInstructions"
        visible: true
        Layout.fillWidth: true
        Layout.leftMargin: -4
        // #5343: a felirat a sáv alatt, 12 px-rel a sáv alja után áll (y=170)
        Layout.topMargin: 4
        Layout.bottomMargin: 3
        wrapMode: Text.WordWrap
        text: root.instructionText
        font.pixelSize: Theme.fontSize
        color: Theme.textDark
    }

    GridView {
        id: unnamedFacesGrid
        objectName: "unnamedGroupsList"
        visible: !root.ignoredMode
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        cellWidth: root.grouped ? 194 : 162
        cellHeight: 198
        readonly property int columns: Math.max(1, Math.floor(width / cellWidth))
        height: Math.ceil(root.facesModel.length / columns) * cellHeight
        model: root.facesModel
        ScrollBar.vertical: PicasaScrollBar {}

        delegate: Item {
            id: faceCard
            required property var modelData
            objectName: "unnamedFaceCard_" + faceCard.modelData.faceId
            property var nameSuggestions: []
            width: unnamedFacesGrid.cellWidth
            height: unnamedFacesGrid.cellHeight

            function refreshNameSuggestions() {
                var needle = faceNameField.text.trim().toLocaleLowerCase()
                var ctl = typeof controller !== "undefined" ? controller : null
                if (!needle || !ctl) {
                    faceCard.nameSuggestions = []
                    return
                }
                var people = ctl.peopleManagerContacts()
                var matches = []
                for (var i = 0; i < people.length; ++i) {
                    if (String(people[i].name).toLocaleLowerCase()
                            .indexOf(needle) >= 0)
                        matches.push(people[i])
                }
                faceCard.nameSuggestions = matches
            }

            // #5285: a névadás egy útja Enterre és a javaslat kattintására
            // is: a mező kiürül, a javaslat-lista záródik
            function submitName(name) {
                faceNameField.text = ""
                faceCard.nameSuggestions = []
                root.nameSubmitted(faceCard.modelData.faceId, name)
            }

            Column {
                width: 172
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 2

                Rectangle {
                    id: faceTile
                    objectName: "faceTile_" + faceCard.modelData.faceId
                    width: root.grouped ? 146 : 120
                    height: root.grouped ? 172 : 145
                    x: root.grouped ? 0 : 13
                    color: "transparent"
                    border.width: 2
                    border.color: root.selectedFaceIds[faceCard.modelData.faceId]
                                  ? Theme.panelSelectionActive : "transparent"

                    Image {
                        objectName: "faceImage_" + faceCard.modelData.faceId
                        anchors.fill: parent
                        source: faceCard.modelData.thumbUrl
                        smooth: true
                        mipmap: true
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.toggleFace(faceCard.modelData.faceId)
                    }

                    Rectangle {
                        objectName: "faceIgnoreX_" + faceCard.modelData.faceId
                        visible: root.grouped
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.margins: 2
                        width: 13
                        height: 13
                        radius: 0
                        color: "#ffffff"
                        border.color: "#1b1b1b"
                        border.width: 1
                        Text {
                            anchors.centerIn: parent
                            text: "X"
                            font.pixelSize: 8
                            font.bold: true
                            color: "#111111"
                        }
                        MouseArea {
                            anchors.fill: parent
                            anchors.margins: -2
                            onClicked: root.requestIgnore(
                                [faceCard.modelData.faceId])
                        }
                    }

                    Rectangle {
                        objectName: "suggestionBar_" + faceCard.modelData.faceId
                        visible: (faceCard.modelData.suggestedName || "") !== ""
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
                                text: qsTr("%1?").arg(
                                    faceCard.modelData.suggestedName || "")
                                font.pixelSize: Theme.fontSize - 1
                                color: Theme.infoBarText
                            }
                            Text {
                                objectName: "suggestionYes_"
                                            + faceCard.modelData.faceId
                                anchors.verticalCenter: parent.verticalCenter
                                text: "✓"
                                color: Theme.infoBarText
                                MouseArea {
                                    anchors.fill: parent
                                    anchors.margins: -4
                                    onClicked: root.acceptSuggestion(
                                        faceCard.modelData.faceId)
                                }
                            }
                        }
                    }
                }

                TextField {
                    id: faceNameField
                    objectName: "unnamedFaceNameField_"
                                + faceCard.modelData.faceId
                    visible: root.grouped
                    width: 172
                    height: 20
                    x: (faceTile.width - width) / 2
                    padding: 1
                    horizontalAlignment: TextInput.AlignHCenter
                    verticalAlignment: TextInput.AlignVCenter
                    font.pixelSize: Theme.fontSize - 2
                    placeholderText: qsTr("Add a name")
                    background: Rectangle {
                        color: "#ffffff"
                        border.color: "#8a8a8a"
                        border.width: 1
                        radius: 0
                    }
                    TextFieldContextArea {}
                    onAccepted: {
                        var name = text.trim()
                        if (!name)
                            return
                        faceCard.submitName(name)
                    }
                    onTextEdited: faceCard.refreshNameSuggestions()
                }
            }

            Popup {
                id: nameSuggestionsPopup
                objectName: "unnamedNameSuggestionPopup_"
                            + faceCard.modelData.faceId
                parent: Overlay.overlay
                property var suggestions: faceCard.nameSuggestions
                readonly property point rootPosition:
                    root.mapToItem(parent, 0, 0)
                readonly property real nameFieldX:
                    rootPosition.x + unnamedFacesGrid.x
                    - unnamedFacesGrid.contentX + faceCard.x
                    + faceNameField.parent.x + faceNameField.x
                readonly property real nameFieldY:
                    rootPosition.y + unnamedFacesGrid.y
                    - unnamedFacesGrid.contentY + faceCard.y
                    + faceNameField.parent.y + faceNameField.y
                x: nameFieldX + (faceNameField.width - width) / 2
                y: nameFieldY + faceNameField.height
                width: 212
                height: Math.min(170, suggestions.length * 42 + 2)
                visible: faceNameField.activeFocus
                         && faceNameField.text.trim().length > 0
                         && suggestions.length > 0
                z: 1000
                padding: 0
                closePolicy: Popup.NoAutoClose

                background: Rectangle {
                    objectName: "unnamedNameSuggestions_"
                                + faceCard.modelData.faceId
                    color: "#ffffff"
                    border.color: "#8a8a8a"
                    border.width: 1
                }

                contentItem: ListView {
                    anchors.fill: parent
                    clip: true
                    model: nameSuggestionsPopup.suggestions
                    delegate: Item {
                        required property var modelData
                        required property int index
                        objectName: "unnamedFaceSuggestion_"
                                    + faceCard.modelData.faceId + "_" + index
                        property string personName: String(modelData.name)
                        property string thumbUrl: String(modelData.thumbUrl || "")
                        width: ListView.view.width
                        height: 40
                        Image {
                            objectName: "unnamedFaceSuggestionImage_"
                                        + faceCard.modelData.faceId + "_" + index
                            anchors.left: parent.left
                            anchors.leftMargin: 17
                            anchors.verticalCenter: parent.verticalCenter
                            width: 28
                            height: 30
                            source: parent.thumbUrl !== ""
                                    ? parent.thumbUrl
                                    : Qt.resolvedUrl(
                                          "icons/person-silhouette.svg")
                            fillMode: Image.PreserveAspectCrop
                            smooth: true
                            mipmap: true
                            asynchronous: true
                        }
                        Text {
                            anchors.left: parent.left
                            anchors.leftMargin: 58
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - 64
                            text: parent.personName
                            font.pixelSize: Theme.fontSize - 1
                            color: Theme.textDark
                            elide: Text.ElideRight
                        }
                        // #5285: a tételre kattintás a kattintott személy nevét
                        // nevezi meg, ugyanazon az úton, mint az Enter
                        MouseArea {
                            anchors.fill: parent
                            onClicked: faceCard.submitName(parent.personName)
                        }
                    }
                }
            }
        }
    }

    ListView {
        id: groupsList
        objectName: "ignoredGroupsList"
        visible: root.ignoredMode
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.leftMargin: -15
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
                visible: !root.ignoredMode
                text: groupDelegate.modelData.label
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.textDark
            }

            GridView {
                id: faceGrid
                objectName: "ignoredFaceGrid"
                Layout.fillWidth: true
                interactive: false
                cellWidth: 194
                cellHeight: 198
                readonly property int columns:
                    Math.max(1, Math.floor(width / cellWidth))
                height: Math.ceil(
                    groupDelegate.modelData.faces.length
                    / Math.max(1, columns)) * cellHeight
                model: groupDelegate.modelData.faces

                delegate: Item {
                    id: ignoredFaceCard
                    required property var modelData
                    width: faceGrid.cellWidth
                    height: faceGrid.cellHeight

                    Column {
                        width: 172
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: 2

                        Rectangle {
                            id: faceTile
                            objectName: "faceTile_" + ignoredFaceCard.modelData.faceId
                            width: 146
                            height: 172
                            x: (parent.width - width) / 2
                            color: "transparent"
                            border.width: 2
                            border.color: root.selectedFaceIds[ignoredFaceCard.modelData.faceId]
                                          ? Theme.panelSelectionActive : "transparent"

                            Image {
                                objectName: "ignoredFaceImage_"
                                            + ignoredFaceCard.modelData.faceId
                                anchors.fill: parent
                                source: ignoredFaceCard.modelData.thumbUrl
                                smooth: true
                                mipmap: true
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: root.toggleFace(ignoredFaceCard.modelData.faceId)
                            }

                            // A mellőzött nézetben az eredeti sem mutatja a mellőző X-et.
                            Rectangle {
                                objectName: "faceIgnoreX_"
                                            + ignoredFaceCard.modelData.faceId
                                visible: false
                                anchors.top: parent.top
                                anchors.right: parent.right
                                width: 18
                                height: 18
                                color: Theme.infoBar
                            }

                            Rectangle {
                                objectName: "suggestionBar_"
                                            + ignoredFaceCard.modelData.faceId
                                visible: (ignoredFaceCard.modelData.suggestedName || "") !== ""
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.bottom: parent.bottom
                                anchors.margins: 3
                                height: 20
                                color: Theme.infoBar
                                Text {
                                    anchors.centerIn: parent
                                    text: qsTr("%1?").arg(
                                        ignoredFaceCard.modelData.suggestedName || "")
                                    font.pixelSize: Theme.fontSize - 1
                                    color: Theme.infoBarText
                                }
                            }
                        }

                        TextField {
                            objectName: "ignoredFaceNameField_"
                                        + ignoredFaceCard.modelData.faceId
                            width: 172
                            height: 20
                            padding: 1
                            horizontalAlignment: TextInput.AlignHCenter
                            verticalAlignment: TextInput.AlignVCenter
                            font.pixelSize: Theme.fontSize - 2
                            placeholderText: qsTr("Add a name")
                            background: Rectangle {
                                color: "#ffffff"
                                border.color: "#8a8a8a"
                                border.width: 1
                            }
                            TextFieldContextArea {}
                            onAccepted: {
                                var cleanName = text.trim()
                                if (!cleanName)
                                    return
                                text = ""
                                root.nameSubmitted(
                                    ignoredFaceCard.modelData.faceId, cleanName)
                            }
                        }
                    }
                }
            }
        }
    }

    Popup {
        id: welcomeDialog
        objectName: "unnamedWelcomeDialog"
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
        width: 458
        height: 494
        padding: 15
        modal: true
        dim: true
        focus: true
        closePolicy: Popup.NoAutoClose
        background: Rectangle {
            color: "#606060"
            border.color: "#999999"
            border.width: 1
            radius: 6
        }
        onClosed: if (root.faceScanController)
            root.faceScanController.markUnnamedWelcomeShown()

        contentItem: ColumnLayout {
            spacing: 13

            Text {
                objectName: "unnamedWelcomeTitle"
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("Welcome to the Unnamed people album! ")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: "#ffffff"
            }
            Text {
                objectName: "unnamedWelcomeBody"
                Layout.fillWidth: true
                Layout.fillHeight: true
                wrapMode: Text.WordWrap
                text: qsTr(
                    "As PicasaPy scans your photos, the faces it finds are "
                    + "automatically grouped for easy naming.\n\n"
                    + "Things to know:\n\n"
                    + "To identify a person, click 'Add a name', then type "
                    + "in the person's name and press Enter.  A new People "
                    + "album will be created each time you name someone for "
                    + "the first time.\n\n"
                    + "(TIP: Sign in with your Google Account to gain access "
                    + "to all of your Google Account contacts while naming.)\n\n"
                    + "To ignore a person, click the 'X' button on the face "
                    + "thumbnail.\n\n"
                    + "Suggestions: After you name someone, PicasaPy may suggest "
                    + "more matching faces for that person. Click on a "
                    + "person's album to view and confirm (or reject) any "
                    + "suggestions.\n\n\n Click 'Learn More' for information "
                    + "about this feature.")
                font.pixelSize: Theme.fontSize - 2
                font.bold: true
                color: "#ffffff"
            }
            RowLayout {
                Layout.fillWidth: true
                Button {
                    objectName: "unnamedWelcomeLearnMoreButton"
                    text: qsTr("Learn more...")
                    Layout.preferredWidth: 86
                    Layout.preferredHeight: 28
                    onClicked: Qt.openUrlExternally(root.learnMoreUrl())
                    contentItem: Text {
                        text: parent.text
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: Theme.fontSize - 4
                        font.bold: true
                        color: "#ffffff"
                    }
                    background: Rectangle {
                        color: "transparent"
                        border.color: "#dddddd"
                        border.width: 1
                        radius: 6
                    }
                }
                Item { Layout.fillWidth: true }
                Button {
                    objectName: "unnamedWelcomeCloseButton"
                    text: qsTr("Close")
                    Layout.preferredWidth: 82
                    Layout.preferredHeight: 28
                    // A jelzőt a gomb maga is menti: Windowson a `closed` jel
                    // után sem volt mentve (#5183 CI).
                    onClicked: {
                        if (root.faceScanController)
                            root.faceScanController.markUnnamedWelcomeShown()
                        welcomeDialog.close()
                    }
                    contentItem: Text {
                        text: parent.text
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: Theme.fontSize - 4
                        font.bold: true
                        color: "#ffffff"
                    }
                    background: Rectangle {
                        color: "transparent"
                        border.color: "#dddddd"
                        border.width: 1
                        radius: 6
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
            root.namedSuggestionAccepted()
        }
        return ok
    }
    // #5214: a fejléc névmezőjének Enter-je a KIJELÖLT arcokat nevezi meg.
    // Egy arcnál a csempe mezőjének útja (`nameSubmitted` → Main.qml →
    // People-ablak). Többnél a tömeges névadás: a People-ablak egyszerre egy
    // arcot kezel (`pendingFaceId`), ciklusban a többi csendben elveszne.
    function nameSelectedFaces(name) {
        var cleanName = String(name || "").trim()
        var ids = root.selectedKeys()
        if (!cleanName || ids.length === 0 || !root.faceScanController)
            return false
        if (ids.length === 1) {
            nameField.text = ""
            root.nameSubmitted(ids[0], cleanName)
            return true
        }
        var ok = root.faceScanController.assignNameToFaces(ids, cleanName)
        if (ok) {
            nameField.text = ""
            root.clearSelection()
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
