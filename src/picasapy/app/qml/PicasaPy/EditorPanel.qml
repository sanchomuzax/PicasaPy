import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Szerkesztő eszközpanel — a néző bal oldali "Gyakori javítások" füle,
// Picasa-hű ikonos csempékkel (#51). Két mód:
//  - "tools": ikonrács + Derítőfény + Visszavonás/Újra
//  - "crop":  "Fotó vágása" — arány-lista, gyorsvágások, gombok
// Csak UI + állapot: a kép-feldolgozás a render/edit rétegben él.
Rectangle {
    id: panel
    objectName: "editorPanel"
    color: Theme.chromeBg
    implicitWidth: 230

    // aktív fül: 0 = Gyakori javítások, 1 = Finomhangolás, 2 = Effektek,
    // 3 = 4. effekt-fül (zöld ecset), 4 = 5. effekt-fül (kék ecset) — #328,
    // az eredeti Picasa 5 ikonos füle (docs/specs/ui-audit-editor.md, 1. szak.)
    // (a vágó-mód a fülsávtól függetlenül, a cropColumn-on át él)
    property int activeTab: 0

    // kapcsoló-állapotok — az aktív eszköz csempéje "benyomva" jelenik meg
    property bool cropActive: false
    property bool tiltActive: false
    property bool redeyeActive: false
    // egygombos javítások (#116): nem módkapcsolók — a gomb mindig új
    // réteget fűz a láncra, és csak akkor tiltott, ha ugyanez a szűrő a
    // lánc utolsó eleme (a hívó/EditController tölti)
    property bool enhanceEnabled: true
    property bool autolightEnabled: true
    property bool autocolorEnabled: true

    // Visszavonás/Újra (jelenleg a vágásra): a hívó (PhotoViewer) tölti
    property bool undoAvailable: false
    property bool redoAvailable: false
    property string undoLabel: qsTr("Undo")
    property string redoLabel: qsTr("Redo")

    // a kép aktuális szélesség/magasság aránya ("Jelenlegi méretarány"-hoz)
    property real imageAspect: 4 / 3

    // vágás-mód állapota
    property int aspectIndex: 0        // az aspectPresets lista indexe
    property bool aspectRotated: false // Forgatás: fekvő <-> álló

    // Finomhangolás (#20): a hívó (PhotoViewer) tölti a mentett értékekkel;
    // a csúszkák CSAK a syncFinetuneSliders()-en át íródnak, hogy húzás
    // közben ne törje meg a kötést (ld. tiltSlider minta, #131)
    property real fillLight: 0
    property real highlights: 0
    property real shadows: 0
    property real colorTemp: 0
    property bool hasFinetune: false
    // programozott szinkronnál (nyitás/lapozás/kontroller-frissítés) NEM
    // váltunk ki finetunePreview-t — a tiltSlider mintáját követve
    property bool suppressFinetune: false
    signal finetunePreview(real fill, real highlights, real shadows, real temp)
    signal finetuneCommit(real fill, real highlights, real shadows, real temp)

    // Effektek (#20): minden gomb új réteget fűz a láncra (append-only)
    signal effectRequested(string name)

    // tool: "crop"|"tilt"|"redeye"|"enhance"|"autolight"|"autocolor"
    signal toolActivated(string tool)
    // a vágás külön jelet is kap — a hívó ez alapján nyitja a CropOverlay-t
    signal cropRequested()
    signal undoRequested()
    signal redoRequested()
    // vágás-mód jelei a hívónak
    signal quickCropRequested(string kind)   // "topleft"|"landscape"|"portrait"
    signal cropRotateRequested()
    signal cropPreviewHold(bool held)
    signal cropResetRequested()
    signal cropApplyRequested()
    signal cropCancelRequested()

    // a négy csúszka aktuális értékét egyben küldi (élő előnézet)
    function emitFinetunePreview() {
        panel.finetunePreview(finetuneFillSlider.value,
                               finetuneHighlightsSlider.value,
                               finetuneShadowsSlider.value,
                               finetuneTempSlider.value)
    }
    // a csúszkák a mentett (kontroller) értékekre állnak — előnézet nélkül
    function syncFinetuneSliders() {
        panel.suppressFinetune = true
        finetuneFillSlider.value = panel.fillLight
        finetuneHighlightsSlider.value = panel.highlights
        finetuneShadowsSlider.value = panel.shadows
        finetuneTempSlider.value = panel.colorTemp
        panel.suppressFinetune = false
    }
    onFillLightChanged: panel.syncFinetuneSliders()
    onActiveTabChanged: panel.syncFinetuneSliders()

    // Arány-lista (Picasa-minta). ratio = szélesség/magasság fekvő
    // tájolásban; 0 = kézi (szabad), -1 = a kép jelenlegi aránya.
    readonly property var aspectPresets: [
        { label: qsTr("Manual"), ratio: 0 },
        { label: qsTr("Current aspect"), ratio: -1 },
        { label: "5x8", ratio: 8 / 5 },
        { label: "9x13", ratio: 13 / 9 },
        { label: "10x15", ratio: 15 / 10 },
        { label: "13x18", ratio: 18 / 13 },
        { label: "20x25", ratio: 25 / 20 },
        { label: qsTr("A4: Full page"), ratio: 297 / 210 },
        { label: qsTr("Square: CD cover"), ratio: 1 },
        { label: qsTr("4:3: Standard screen"), ratio: 4 / 3 },
        { label: qsTr("16:10: Widescreen"), ratio: 16 / 10 },
        { label: qsTr("16:9: HDTV"), ratio: 16 / 9 },
        { label: qsTr("5:3: Wide frame"), ratio: 5 / 3 }
    ]

    // a kiválasztott arány a Forgatással együtt — a CropOverlay-nek
    readonly property real currentAspect: {
        var base = aspectPresets[aspectIndex].ratio
        if (base === 0) return 0
        if (base === -1) base = panel.imageAspect
        if (base < 1) base = 1 / base   // fekvő alapállás
        return panel.aspectRotated ? 1 / base : base
    }

    // egy csempe-kattintás kezelése: mód-eszköznél kapcsoló-állapot váltása,
    // egygombos javításnál (#116) csak jelzés — tiltott gombnál no-op
    function handleToolClick(tool) {
        switch (tool) {
        case "crop": panel.cropActive = !panel.cropActive; break
        case "tilt": panel.tiltActive = !panel.tiltActive; break
        case "redeye": panel.redeyeActive = !panel.redeyeActive; break
        case "enhance": if (!panel.enhanceEnabled) return; break
        case "autolight": if (!panel.autolightEnabled) return; break
        case "autocolor": if (!panel.autocolorEnabled) return; break
        }
        panel.toolActivated(tool)
        if (tool === "crop") panel.cropRequested()
    }

    // ikonos eszköz-csempe: kis kép-ikon + felirat alatta (Picasa-minta)
    component ToolTile: Item {
        id: tile
        required property string toolName
        required property string label
        required property string icon
        property bool active: false
        property bool tileEnabled: true
        signal activated(string tool)

        Layout.fillWidth: true
        Layout.preferredHeight: 66
        // az öröklött enabled is számít (#103): videónál a PhotoViewer az
        // egész panelt tiltja — a csempe ilyenkor vizuálisan is szürkül
        enabled: tile.tileEnabled
        opacity: tile.enabled ? 1 : 0.4

        Rectangle {
            anchors.fill: parent
            radius: 3
            // #314: sem "#cfe4f7", sem "#e8eef4" nem olvasható sötét
            // témában (fix világos árnyalatok) — a jelző-kék tokenből
            // (Theme.selectionBlue) származtatott áttetsző rétegre váltva
            // mindkét témán kontrasztos marad, a hover halványabb az aktívnál.
            color: tile.active
                   ? Qt.rgba(Theme.selectionBlue.r, Theme.selectionBlue.g,
                             Theme.selectionBlue.b, 0.45)
                   : (tileMouse.containsMouse && tile.tileEnabled
                      ? Qt.rgba(Theme.selectionBlue.r, Theme.selectionBlue.g,
                                Theme.selectionBlue.b, 0.18)
                      : "transparent")
            border.width: tile.active ? 1 : 0
            border.color: Theme.selectionBlue
        }
        Image {
            anchors.top: parent.top
            anchors.topMargin: 4
            anchors.horizontalCenter: parent.horizontalCenter
            width: 40; height: 30
            source: "../../assets/tools/" + tile.icon + ".png"
            smooth: true
        }
        Text {
            anchors.top: parent.top
            anchors.topMargin: 37   // az ikon alatt, nem érhet össze vele
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width - 2
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            lineHeight: 0.9
            text: tile.label
            font.pixelSize: Theme.fontSize - 2
            color: Theme.textDark
        }
        MouseArea {
            id: tileMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: tile.activated(tile.toolName)
        }
    }

    // egyszerű panel-gomb (PicasaButton-színvilág)
    component PanelButton: Rectangle {
        id: pbtn
        property string label: ""
        property bool buttonEnabled: true
        signal buttonClicked()
        Layout.fillWidth: true
        // #318: a felirat teljesen olvasható kell legyen — a magasság a
        // (esetleg tördelt) feliratból számolt implicitHeight-hez igazodik,
        // 24px az alsó korlát (rövid egysoros feliratoknál, pl. Undo/Redo).
        Layout.preferredHeight: Math.max(24, pbtnLabel.implicitHeight + 10)
        radius: 3
        border.width: 1
        border.color: Theme.chromeBorder
        // pbtn.enabled = buttonEnabled ÉS az öröklött (panel-)enabled (#103)
        enabled: pbtn.buttonEnabled
        // #314: fix világos hexák ("#fdfdfd"/"#d8d8d8"/"#ececec") helyett
        // téma-tokenekből — sötét témában a gomb is sötétedik, így a
        // (szintén témafüggő) Theme.textDark felirat olvasható marad rajta.
        color: !pbtn.enabled ? Theme.chromeBg
               : (pbtnMouse.pressed ? Qt.darker(Theme.buttonBg, 1.15) : Theme.buttonBg)
        Text {
            id: pbtnLabel
            // a hívó objectName-jéből képzett saját objectName (pl.
            // "effectGrain2Label") — a tesztek ezen ellenőrzik a
            // tördelést/nem-vágást (#318), a histogramTitle mintája (#235).
            objectName: pbtn.objectName ? pbtn.objectName + "Label" : ""
            anchors.centerIn: parent
            text: pbtn.label
            font.pixelSize: Theme.fontSize
            color: pbtn.enabled ? Theme.textDark : Theme.textGray
            // #318: elide helyett tördelés — a panel szélessége nem nőhet,
            // de a szöveg soha nem vágódik "…"-ra; a Qt WordWrap szó-
            // határon tör, hosszú, tördelhetetlen szónál karakterhatáron.
            wrapMode: Text.WordWrap
            width: parent.width - 8
            horizontalAlignment: Text.AlignHCenter
        }
        MouseArea {
            id: pbtnMouse
            anchors.fill: parent
            onClicked: pbtn.buttonClicked()
        }
    }

    // egy fülgomb (Gyakori javítások / Finomhangolás / Effektek / 4. / 5.
    // effekt-fül, #20, #328): kattintásra panel.activeTab vált, az aktív fül
    // vastagabb betűvel és eltérő háttérrel emelkedik ki.
    // #328 — ikon vs. szöveg döntés: az eredeti Picasa 5 fülcíme ikonos
    // (csavarkulcs / nap / 3× ecset, ld. docs/specs/ui-audit-editor.md 1.
    // szak.), de a projektben NINCS ehhez kézenfekvő ikon-készlet — a
    // meglévő assets/tools/*.png csak az 1. fül (Gyakori javítások)
    // eszköz-csempéihez való (crop/tilt/redeye/…), a fülsávhoz sosem volt
    // ikon. Félkész/találgatott ikon rajzolása helyett a fülek SZÖVEGESEK
    // maradnak — ez a "működő, olvasható inkább, mint félkész" elv (ld. a
    // feladat 3. pontja). Öt fülnél a régi `elide`-es minta levágná a
    // feliratot (#318 lesson) — ezért a fülgomb is a PanelButton mintáját
    // követi: `wrapMode: Text.WordWrap` + a feliratból számolt magasság,
    // nem vágás.
    component EditTabButton: Rectangle {
        id: tbtn
        required property int tabIndex
        required property string label
        Layout.fillWidth: true
        Layout.preferredHeight: Math.max(22, tbtnLabel.implicitHeight + 8)
        color: panel.activeTab === tabIndex ? Theme.contentPanel : Theme.panelHeaderBg
        border.width: 1
        border.color: Theme.chromeBorder
        Text {
            id: tbtnLabel
            // a hívó objectName-jéből képzett saját objectName (pl.
            // "editTabFixesLabel") — a PanelButton mintáját követve (#318),
            // hogy a tesztek egyértelműen megtalálják a felirat-Text-et.
            objectName: tbtn.objectName ? tbtn.objectName + "Label" : ""
            anchors.centerIn: parent
            text: tbtn.label
            font.pixelSize: Theme.fontSize - 3
            font.bold: panel.activeTab === tbtn.tabIndex
            color: Theme.panelHeaderText
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            lineHeight: 0.9
            width: parent.width - 4
            horizontalAlignment: Text.AlignHCenter
        }
        MouseArea {
            anchors.fill: parent
            onClicked: panel.activeTab = tbtn.tabIndex
        }
    }

    // ---------------- fülsáv: Gyakori javítások / Finomhangolás / Effektek /
    // 4. effekt-fül / 5. effekt-fül (#20, #328) — csak "tools" módban,
    // vágásnál (cropColumn) nincs értelme. Öt egyenlő szélességű fül fér el
    // a panel szélességében (Layout.fillWidth mindegyiken, ld. #328 4. pont).
    RowLayout {
        id: tabBar
        objectName: "editTabBar"
        visible: !panel.cropActive
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 0

        EditTabButton {
            objectName: "editTabFixes"
            tabIndex: 0
            label: qsTr("Common Fixes")
        }
        EditTabButton {
            objectName: "editTabFinetune"
            tabIndex: 1
            label: qsTr("Fine Tuning")
        }
        EditTabButton {
            objectName: "editTabEffects"
            tabIndex: 2
            label: qsTr("Effects")
        }
        // #328: 4. fül (zöld ecset) — a docs/specs/ui-audit-editor.md
        // "kreatív effektek" leírása alapján rövid "Creative" felirat.
        EditTabButton {
            objectName: "editTabEffects2"
            tabIndex: 3
            label: qsTr("Creative")
        }
        // #328: 5. fül (kék ecset) — "művészi effektek" alapján "Artistic".
        EditTabButton {
            objectName: "editTabEffects3"
            tabIndex: 4
            label: qsTr("Artistic")
        }
    }

    // ---------------- "tools" mód: ikonrács ----------------
    ColumnLayout {
        objectName: "toolsColumn"
        visible: !panel.cropActive && panel.activeTab === 0
        // tiltott panel (videó a nézőben, #103): az egész oszlop halvány
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Common Fixes")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        GridLayout {
            columns: 3
            columnSpacing: 4
            rowSpacing: 10
            Layout.fillWidth: true

            ToolTile {
                objectName: "editToolCrop"
                toolName: "crop"; label: qsTr("Crop"); icon: "crop"
                active: panel.cropActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolTilt"
                toolName: "tilt"; label: qsTr("Straighten"); icon: "tilt"
                active: panel.tiltActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolRedeye"
                toolName: "redeye"; label: qsTr("Redeye"); icon: "redeye"
                active: panel.redeyeActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            // egygombos javítások (#116): nincs "benyomva" állapot — a gomb
            // tiltott, amíg ugyanez a szűrő a lánc utolsó eleme
            ToolTile {
                objectName: "editToolEnhance"
                toolName: "enhance"; label: qsTr("I'm Feeling Lucky"); icon: "lucky"
                tileEnabled: panel.enhanceEnabled
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolAutolight"
                toolName: "autolight"; label: qsTr("Auto Contrast"); icon: "contrast"
                tileEnabled: panel.autolightEnabled
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolAutocolor"
                toolName: "autocolor"; label: qsTr("Auto Color"); icon: "color"
                tileEnabled: panel.autocolorEnabled
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolRetouch"
                toolName: "retouch"; label: qsTr("Retouch"); icon: "retouch"
                tileEnabled: false   // 2. ütem
            }
            ToolTile {
                objectName: "editToolText"
                toolName: "text"; label: qsTr("Text"); icon: "text"
                tileEnabled: false   // 2. ütem
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "editUndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "editRedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                Layout.fillWidth: false
                Layout.preferredWidth: 64
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- "finetune" mód: Finomhangolás (#20) ----------------
    ColumnLayout {
        objectName: "finetuneColumn"
        visible: !panel.cropActive && panel.activeTab === 1
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Fine Tuning")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        Label {
            text: qsTr("Fill Light")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: finetuneFillSlider
            objectName: "finetuneFillSlider"
            Layout.fillWidth: true
            from: 0; to: 1; value: 0
            onValueChanged: if (!panel.suppressFinetune) panel.emitFinetunePreview()
            onPressedChanged: if (!pressed)
                panel.finetuneCommit(finetuneFillSlider.value,
                                      finetuneHighlightsSlider.value,
                                      finetuneShadowsSlider.value,
                                      finetuneTempSlider.value)
        }

        Label {
            text: qsTr("Highlights")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: finetuneHighlightsSlider
            objectName: "finetuneHighlightsSlider"
            Layout.fillWidth: true
            from: 0; to: 1; value: 0
            onValueChanged: if (!panel.suppressFinetune) panel.emitFinetunePreview()
            onPressedChanged: if (!pressed)
                panel.finetuneCommit(finetuneFillSlider.value,
                                      finetuneHighlightsSlider.value,
                                      finetuneShadowsSlider.value,
                                      finetuneTempSlider.value)
        }

        Label {
            text: qsTr("Shadows")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: finetuneShadowsSlider
            objectName: "finetuneShadowsSlider"
            Layout.fillWidth: true
            from: 0; to: 1; value: 0
            onValueChanged: if (!panel.suppressFinetune) panel.emitFinetunePreview()
            onPressedChanged: if (!pressed)
                panel.finetuneCommit(finetuneFillSlider.value,
                                      finetuneHighlightsSlider.value,
                                      finetuneShadowsSlider.value,
                                      finetuneTempSlider.value)
        }

        Label {
            text: qsTr("Color Temperature")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        PicasaSlider {
            id: finetuneTempSlider
            objectName: "finetuneTempSlider"
            Layout.fillWidth: true
            from: -1; to: 1; value: 0
            onValueChanged: if (!panel.suppressFinetune) panel.emitFinetunePreview()
            onPressedChanged: if (!pressed)
                panel.finetuneCommit(finetuneFillSlider.value,
                                      finetuneHighlightsSlider.value,
                                      finetuneShadowsSlider.value,
                                      finetuneTempSlider.value)
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "finetuneUndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "finetuneRedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                Layout.fillWidth: false
                Layout.preferredWidth: 64
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- "effects" mód: Effektek (#20) ----------------
    ColumnLayout {
        objectName: "effectsColumn"
        visible: !panel.cropActive && panel.activeTab === 2
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Effects")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        GridLayout {
            objectName: "effectsGrid"
            columns: 2
            columnSpacing: 6
            rowSpacing: 6
            Layout.fillWidth: true

            // #315: az eredeti Picasa Effektek fülén az Élesítés az ELSŐ
            // gomb — a render/chain.py "unsharp" handlere ismeri, csak a
            // gombja hiányzott.
            PanelButton {
                objectName: "effectUnsharp"
                label: qsTr("Sharpen")
                onButtonClicked: panel.effectRequested("unsharp")
            }
            PanelButton {
                objectName: "effectSepia"
                label: qsTr("Sepia")
                onButtonClicked: panel.effectRequested("sepia")
            }
            PanelButton {
                objectName: "effectBw"
                label: qsTr("B&W")
                onButtonClicked: panel.effectRequested("bw")
            }
            PanelButton {
                objectName: "effectWarm"
                label: qsTr("Warmify")
                onButtonClicked: panel.effectRequested("warm")
            }
            PanelButton {
                objectName: "effectGrain2"
                label: qsTr("Film Grain")
                onButtonClicked: panel.effectRequested("grain2")
            }
            PanelButton {
                objectName: "effectTint"
                label: qsTr("Tint")
                onButtonClicked: panel.effectRequested("tint")
            }
            PanelButton {
                objectName: "effectSat"
                label: qsTr("Saturation")
                onButtonClicked: panel.effectRequested("sat")
            }
            PanelButton {
                objectName: "effectRadblur"
                label: qsTr("Soft Focus")
                onButtonClicked: panel.effectRequested("radblur")
            }
            PanelButton {
                objectName: "effectGlow2"
                label: qsTr("Glow")
                onButtonClicked: panel.effectRequested("glow2")
            }
            PanelButton {
                objectName: "effectAnsel"
                label: qsTr("Filtered B&W")
                onButtonClicked: panel.effectRequested("ansel")
            }
            PanelButton {
                objectName: "effectRadsat"
                label: qsTr("Focal Saturation")
                onButtonClicked: panel.effectRequested("radsat")
            }
            PanelButton {
                objectName: "effectDirTint"
                label: qsTr("Graduated Tint")
                onButtonClicked: panel.effectRequested("dir_tint")
            }
            // #315: a render/chain.py "vignette" kulcsot vár (kisbetűs,
            // casefold), noha az ini-ben a szűrő neve nagybetűs "Vignette"
            // — az EditController.applyEffect is casefold-ol, ezért itt is
            // kisbetűvel küldjük az effectRequested jelet.
            PanelButton {
                objectName: "effectVignette"
                label: qsTr("Vignette")
                onButtonClicked: panel.effectRequested("vignette")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "effectsUndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "effectsRedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                Layout.fillWidth: false
                Layout.preferredWidth: 64
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- "effects2" mód: 4. effekt-fül — zöld ecset,
    // "kreatív effektek" (#328, docs/specs/ui-audit-editor.md 4. fül) ------
    ColumnLayout {
        objectName: "effectsColumn2"
        visible: !panel.cropActive && panel.activeTab === 3
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Creative")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        GridLayout {
            objectName: "effectsGrid2"
            columns: 2
            columnSpacing: 6
            rowSpacing: 6
            Layout.fillWidth: true

            PanelButton {
                objectName: "effectIr"
                label: qsTr("Infrared Film")
                onButtonClicked: panel.effectRequested("ir")
            }
            PanelButton {
                objectName: "effectLomo"
                label: qsTr("Lomo-ish")
                onButtonClicked: panel.effectRequested("lomo")
            }
            PanelButton {
                objectName: "effectHolga"
                label: qsTr("Holga-ish")
                onButtonClicked: panel.effectRequested("holga")
            }
            PanelButton {
                objectName: "effectHdr"
                label: qsTr("HDR-ish")
                onButtonClicked: panel.effectRequested("hdr")
            }
            PanelButton {
                objectName: "effectCinemascope"
                label: qsTr("Cinemascope")
                onButtonClicked: panel.effectRequested("cinemascope")
            }
            PanelButton {
                objectName: "effectOrton"
                label: qsTr("Orton-ish")
                onButtonClicked: panel.effectRequested("orton")
            }
            PanelButton {
                objectName: "effectSixties"
                label: qsTr("1960s")
                onButtonClicked: panel.effectRequested("sixties")
            }
            PanelButton {
                objectName: "effectInvert"
                label: qsTr("Invert Colors")
                onButtonClicked: panel.effectRequested("invert")
            }
            PanelButton {
                objectName: "effectHeatMap"
                label: qsTr("Heat Map")
                onButtonClicked: panel.effectRequested("heatmap")
            }
            PanelButton {
                objectName: "effectCrossProcess"
                label: qsTr("Cross Process")
                onButtonClicked: panel.effectRequested("crossprocess")
            }
            PanelButton {
                objectName: "effectQuantizePalette"
                label: qsTr("Posterize")
                onButtonClicked: panel.effectRequested("quantizepalette")
            }
            PanelButton {
                objectName: "effectTwoTone"
                label: qsTr("Duo-Tone")
                onButtonClicked: panel.effectRequested("twotone")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "effects2UndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "effects2RedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                Layout.fillWidth: false
                Layout.preferredWidth: 64
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- "effects3" mód: 5. effekt-fül — kék ecset,
    // "művészi effektek" (#328, docs/specs/ui-audit-editor.md 5. fül) ------
    ColumnLayout {
        objectName: "effectsColumn3"
        visible: !panel.cropActive && panel.activeTab === 4
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Artistic")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        GridLayout {
            objectName: "effectsGrid3"
            columns: 2
            columnSpacing: 6
            rowSpacing: 6
            Layout.fillWidth: true

            PanelButton {
                objectName: "effectBoost"
                label: qsTr("Boost")
                onButtonClicked: panel.effectRequested("boost")
            }
            PanelButton {
                objectName: "effectSoften"
                label: qsTr("Soft Focus")
                onButtonClicked: panel.effectRequested("soften")
            }
            PanelButton {
                objectName: "effectPixelate"
                label: qsTr("Pixelate")
                onButtonClicked: panel.effectRequested("pixelate")
            }
            PanelButton {
                objectName: "effectFocalZoom"
                label: qsTr("Focal Zoom")
                onButtonClicked: panel.effectRequested("focalzoom")
            }
            PanelButton {
                objectName: "effectPencilSketch"
                label: qsTr("Pencil Sketch")
                onButtonClicked: panel.effectRequested("pencilsketch")
            }
            PanelButton {
                objectName: "effectNeon"
                label: qsTr("Neon")
                onButtonClicked: panel.effectRequested("neon")
            }
            PanelButton {
                objectName: "effectComicize"
                label: qsTr("Comicize")
                onButtonClicked: panel.effectRequested("comicize")
            }
            PanelButton {
                objectName: "effectBorder"
                label: qsTr("Border")
                onButtonClicked: panel.effectRequested("border")
            }
            PanelButton {
                objectName: "effectDropShadow"
                label: qsTr("Drop Shadow")
                onButtonClicked: panel.effectRequested("dropshadow")
            }
            PanelButton {
                objectName: "effectMuseumMatte"
                label: qsTr("Museum Matte")
                onButtonClicked: panel.effectRequested("museummatte")
            }
            PanelButton {
                objectName: "effectPolaroid"
                label: qsTr("Polaroid")
                onButtonClicked: panel.effectRequested("polaroid")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "effects3UndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "effects3RedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                Layout.fillWidth: false
                Layout.preferredWidth: 64
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- "crop" mód: Fotó vágása ----------------
    ColumnLayout {
        objectName: "cropColumn"
        visible: panel.cropActive
        opacity: panel.enabled ? 1 : 0.45
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Image {
                Layout.preferredWidth: 40
                Layout.preferredHeight: 30
                source: "../../assets/tools/crop.png"
            }
            Text {
                Layout.fillWidth: true
                text: qsTr("Crop Photo")
                font.pixelSize: Theme.fontSize + 3
                color: Theme.ink
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Choose a size below, then drag on the picture to "
                       + "select the area you want to keep.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        // arány-választó legördülő (Picasa-lista)
        Rectangle {
            objectName: "cropAspectCombo"
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            radius: 2
            color: Theme.contentPanel
            border.color: Theme.chromeBorder
            Text {
                anchors.left: parent.left; anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width - 28
                elide: Text.ElideRight
                text: panel.aspectPresets[panel.aspectIndex].label
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Text {
                anchors.right: parent.right; anchors.rightMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: "▼"; font.pixelSize: 8; color: Theme.textDark
            }
            MouseArea {
                anchors.fill: parent
                onClicked: aspectList.visible = !aspectList.visible
            }
        }
        Rectangle {
            id: aspectList
            objectName: "cropAspectList"
            visible: false
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? aspectColumn.height + 2 : 0
            color: Theme.contentPanel
            border.color: Theme.chromeBorder
            Column {
                id: aspectColumn
                x: 1; y: 1
                width: parent.width - 2
                Repeater {
                    model: panel.aspectPresets
                    Rectangle {
                        required property var modelData
                        required property int index
                        width: aspectColumn.width; height: 20
                        color: aspectRowHover.hovered ? Theme.panelSelection
                               : "transparent"
                        Text {
                            anchors.left: parent.left; anchors.leftMargin: 6
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.label
                            font.pixelSize: Theme.fontSize
                            // a kijelölő-kék (Theme.panelSelection) hátteren
                            // szándékosan téma-független fehér a token
                            // (Theme.panelSelectionText) — nem új hardkód
                            color: aspectRowHover.hovered ? Theme.panelSelectionText : Theme.ink
                        }
                        HoverHandler { id: aspectRowHover }
                        TapHandler {
                            onTapped: {
                                panel.aspectIndex = index
                                panel.aspectRotated = false
                                aspectList.visible = false
                            }
                        }
                    }
                }
            }
        }

        // gyorsvágások: bal-felső / fekvő / álló (Picasa három bélyegképe)
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "quickCropTopleft"
                label: qsTr("Top left")
                onButtonClicked: panel.quickCropRequested("topleft")
            }
            PanelButton {
                objectName: "quickCropLandscape"
                label: qsTr("Landscape")
                onButtonClicked: panel.quickCropRequested("landscape")
            }
            PanelButton {
                objectName: "quickCropPortrait"
                label: qsTr("Portrait")
                onButtonClicked: panel.quickCropRequested("portrait")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "cropRotateButton"
                label: qsTr("Rotate")
                onButtonClicked: panel.cropRotateRequested()
            }
            PanelButton {
                objectName: "cropPreviewButton"
                label: qsTr("Preview")
                // amíg nyomva tartják, a hívó a vágott képet mutatja
                MouseArea {
                    anchors.fill: parent
                    onPressed: panel.cropPreviewHold(true)
                    onReleased: panel.cropPreviewHold(false)
                    onCanceled: panel.cropPreviewHold(false)
                }
            }
        }

        PanelButton {
            objectName: "cropResetButton"
            label: qsTr("Reset")
            Layout.fillWidth: false
            Layout.preferredWidth: 120
            Layout.alignment: Qt.AlignHCenter
            onButtonClicked: panel.cropResetRequested()
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "cropApplyButton"
                label: qsTr("Apply") + " ✔"
                onButtonClicked: panel.cropApplyRequested()
            }
            PanelButton {
                objectName: "cropCancelButton"
                label: qsTr("Cancel") + " ✘"
                onButtonClicked: panel.cropCancelRequested()
            }
        }
    }
}
