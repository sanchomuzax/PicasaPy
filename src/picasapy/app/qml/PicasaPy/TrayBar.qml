import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Alsó sáv (#150-ben kiemelve a Main.qml-ből): kék infó-sáv (busy-
// animációval, #70) + kijelölés-tálca a művelet-gombokkal (Picasa).
// A kijelölés-állapot a főablaké (appWindow); a néző aktuális sorát a
// viewerIndex tulajdonság hozza.
Column {
    id: tray

    // a főablak (kijelölés-állapot + rotateTargetsAllVideo őr gazdája)
    required property var appWindow
    // a néző aktuális sora (a Main köti a photoViewer.currentIndex-re)
    property int viewerIndex: -1
    // az Exportálás gomb (a dialógus a Main.qml-ben él)
    signal exportRequested()
    // #361: Kollázs/Film a tálcáról (a dialógusok a Main.qml-ben élnek)
    signal collageRequested()
    signal movieRequested()
    // #32 (RÉSZLEGES kör): Nyomtatás/E-mail — a dialógusok (nyomtató-
    // választó, tárgy/szöveg-bekérés) a Main.qml-ben élnének, ugyanúgy,
    // mint a fenti kettőnél (a bekötés az integrátor lépése, ld.
    // print_controller.py/email_controller.py docstringje).
    signal printRequested()
    signal emailRequested()

    // a forgatás/csillag célsora — a Main rotateTargetRow()-ja is ezt kéri
    readonly property int starTargetRow: trayStar.targetRow

    // #305: null-őr — a controller a QML-engine leépítésekor átmenetileg
    // null lehet, miközben ezek a kötések utoljára kiértékelődnek.
    readonly property var ctl: controller

    // tömör acélkék infó-sáv; kijelöléskor a kép adatai
    Rectangle {
        id: infoBar
        width: parent.width; height: 20
        color: Theme.infoBar
        clip: true

        // #70: lassan végigvonuló fény-hullám, amíg a PicasaPy a
        // háttérben dolgozik (indexelés, thumbnail-batch). XAnimator:
        // a render-szálon fut (a főszálat/GIL-t nem érinti, ld. #53),
        // idle-ben running=false → 0 CPU/GPU. Nem polloz: a
        // controller.isWorking jelzés-alapú (busyChanged).
        Rectangle {
            id: busySweep
            objectName: "busySweep"
            visible: tray.ctl ? tray.ctl.isWorking : false
            width: Math.max(80, infoBar.width / 5)
            height: infoBar.height
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "transparent" }
                GradientStop { position: 0.5; color: "#59ffffff" }
                GradientStop { position: 1.0; color: "transparent" }
            }
            XAnimator on x {
                running: busySweep.visible
                loops: Animation.Infinite
                from: -busySweep.width
                to: infoBar.width
                duration: 1800
            }
        }
        Text {
            anchors.centerIn: parent
            // #718: null-őr — a `ctl` mellett az `appWindow` is
            // átmenetileg null lehet az engine-leépítés utolsó kiértékelésekor.
            text: (!tray.ctl || !tray.appWindow) ? "" : (tray.appWindow.viewerOpen
                  ? tray.ctl.viewerInfo(tray.viewerIndex)
                  : (tray.appWindow.selectedIndexes.length === 1
                     ? tray.ctl.photoInfo(tray.appWindow.selectedIndex)
                     : tray.ctl.statusText))
            color: Theme.infoBarText
            font.pixelSize: Theme.fontSize
            font.bold: true
        }
    }

    Rectangle {
        id: trayMainBar
        objectName: "trayMainBar"
        // #422: jobbklikk a képtálcán — a Picasa `Tray` menüosztálya
        TapHandler {
            objectName: "trayContextMenuHandler"
            acceptedButtons: Qt.RightButton
            gesturePolicy: TapHandler.ReleaseWithinBounds
            onSingleTapped: trayContextMenu.popup()
        }
        TrayContextMenu {
            id: trayContextMenu
            // „Kijelölés megtartása": a kijelölés a jelenlegi
            // horgony-képre szűkül; „eltávolítása": az kikerül belőle
            onKeepSelectionRequested: {
                var row = tray.appWindow.selectedIndex
                if (row >= 0) tray.appWindow.selectedIndexes = [row]
            }
            onRemoveSelectionRequested: {
                var anchor = tray.appWindow.selectedIndex
                var rest = []
                var current = tray.appWindow.selectedIndexes
                for (var k = 0; k < current.length; ++k)
                    if (Number(current[k]) !== anchor) rest.push(current[k])
                tray.appWindow.selectedIndexes = rest
                tray.appWindow.selectedIndex = rest.length > 0 ? rest[0] : -1
            }
        }
        width: parent.width; height: 52
        color: Theme.trayBg

        // #406: szűk ablaknál (pl. fél képernyő) a szöveges gombok
        // (E-mail, Nyomtatás, Exportálás, Feltöltés) ne lógjanak ki —
        // a küszöb alatt ikon-only módra váltanak (tooltippel).
        //
        // A küszöb NEM fix pixelérték: a feliratok tényleges szélessége
        // betűkészlet- és NYELVFÜGGŐ (a windows-CI éppen ezen bukott el
        // — ott a szélesebb rendszerbetűvel 1280 px-en is kilógott a
        // sáv). Ezért a négy feliratot `TextMetrics`-szel MEGMÉRJÜK, és
        // a mért összeghez adjuk a fix elem-költségvetést (ikonok,
        // térközök, csúszka, kijelölés-előnézet). A TextMetrics nem függ
        // az elrendezéstől, így kötés-hurok sem keletkezik.
        TextMetrics {
            id: emailLabelMetrics
            font.pixelSize: Theme.fontSize
            text: qsTr("E-Mail")
        }
        TextMetrics {
            id: printLabelMetrics
            font.pixelSize: Theme.fontSize
            text: qsTr("Print")
        }
        TextMetrics {
            id: exportLabelMetrics
            font.pixelSize: Theme.fontSize
            text: qsTr("Export")
        }
        TextMetrics {
            id: uploadLabelMetrics
            font.pixelSize: Theme.fontSize
            text: qsTr("Upload to Google Photos")
        }
        // A fix (felirat-független) elemek helyigénye: kijelölés-előnézet,
        // ikonsorok, csúszka, térközök — mérve ~872 px, felfelé kerekítve
        // 900-ra. INVARIÁNS, amiért ez biztonságos: a feliratos elrendezés
        // tényleges igénye = fix + feliratok; a küszöb = 900 + feliratok.
        // Feliratos módba csak `width >= küszöb` esetén váltunk, és ekkor
        // width >= 900 + feliratok > fix + feliratok = igény — vagyis a
        // tartalom BIZONYÍTHATÓAN elfér, bármilyen betűszélesség mellett.
        readonly property real compactBudget: 900
        // A küszöb kívülről is olvasható (teszt), hogy a „széles ablak"
        // esetet ne fix pixelértékkel kelljen megadni — az platform- és
        // nyelvfüggő lenne (a windows-CI éppen ezen bukott el 1280-on).
        readonly property real compactThreshold: compactBudget
                                        + emailLabelMetrics.width
                                        + printLabelMetrics.width
                                        + exportLabelMetrics.width
                                        + uploadLabelMetrics.width
        readonly property bool compact: width < compactThreshold

        Rectangle {
            width: parent.width; height: 1
            color: Theme.trayBorder
        }
        RowLayout {
            id: trayRowLayout
            objectName: "trayRowLayout"
            anchors.fill: parent
            anchors.leftMargin: 10; anchors.rightMargin: 10
            spacing: trayMainBar.compact ? 4 : 8

            // kijelölés-tálca: a kijelölt képek miniatűrjei (Picasa) —
            // #406: kompakt módban zsugorodik (Layout.fillWidth), hogy
            // helyet adjon a jobb oldali gomboknak.
            // #455: ha a tálcán van MEGTARTOTT kép (a mappaváltást is
            // túlélő `TrayMixin`-halmaz), az előnézet AZOKAT mutatja —
            // mappától függetlenül (`heldThumbUrlAt`); tartott kép
            // híján a régi viselkedés (a jelenlegi kijelölés) marad.
            Item {
                id: trayPreview
                Layout.preferredWidth: trayMainBar.compact ? 70 : 200
                Layout.preferredHeight: 46
                readonly property int heldCount: tray.ctl ? tray.ctl.heldCount : 0
                Flow {
                    anchors.fill: parent
                    spacing: 2
                    clip: true
                    Repeater {
                        objectName: "trayPreviewRepeater"
                        // #718: null-őr — az appWindow (a Main.qml
                        // `window`-ja) az engine-leépítés közben átmenetileg
                        // null lehet, miközben ez a kötés utoljára
                        // kiértékelődik (ld. a fenti `ctl` docstringje).
                        model: trayPreview.heldCount > 0
                            ? trayPreview.heldCount
                            : (tray.appWindow ? tray.appWindow.selectedIndexes.length : 0)
                        delegate: Image {
                            objectName: "trayPreviewThumb"
                            required property int index
                            width: 20; height: 20
                            source: !tray.ctl || !tray.appWindow ? ""
                                : trayPreview.heldCount > 0
                                  ? tray.ctl.heldThumbUrlAt(index)
                                  : tray.ctl.photos.thumbUrlAt(
                                        Number(tray.appWindow.selectedIndexes[index]))
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                        }
                    }
                }
                Text {
                    // #718: ld. a Repeater fenti null-őrét — ugyanaz a
                    // teardown-ablak érinti ezt a kötést is.
                    visible: trayPreview.heldCount === 0
                             && (!tray.appWindow || tray.appWindow.selectedIndexes.length === 0)
                    anchors.centerIn: parent
                    text: qsTr("Selection")
                    color: Theme.placeholderText
                    font.pixelSize: Theme.fontSize
                }
            }
            // #455: a Picasa 3-gombos oszlopa (design-guide.md tálca-audit,
            // 5.2/5.3-2. pont) — a zöld pin ("Kijelölés megtartása" / Hold
            // Selection) és a piros kör ("Tálca ürítése" / Clear Tray) a
            // TrayMixin-t köti be. A HARMADIK gomb (kék könyv+nyíl,
            // "Add to" album) NEM készül el ebben a lépcsőben — a
            // tálcán tartott képek albumhoz adása külön jegy (a
            // modul-docstring "NINCS ebben a lépcsőben" szakasza).
            PicasaButton {
                id: trayHoldBtn
                objectName: "trayHoldButton"
                // #718: null-őr — ld. a fenti `ctl` docstringje.
                enabled: tray.appWindow
                         ? (!tray.appWindow.viewerOpen
                            && tray.appWindow.selectedIndexes.length > 0)
                         : false
                onClicked: tray.ctl && tray.appWindow && tray.ctl.holdRows(
                    tray.appWindow.selectedIndexes)
                Layout.preferredWidth: 26
                ToolTip.text: qsTr("Hold Selection")
                ToolTip.visible: trayHoldBtn.hovered
                ToolTip.delay: 500
                contentItem: Image {
                    objectName: "trayHoldIcon"
                    anchors.centerIn: parent
                    source: "icons/hold-pin.svg"
                    sourceSize: Qt.size(14, 14)
                    opacity: trayHoldBtn.enabled ? 1.0 : 0.5
                }
            }
            PicasaButton {
                id: trayClearBtn
                objectName: "trayClearButton"
                enabled: trayPreview.heldCount > 0
                onClicked: trayClearConfirm.open()
                Layout.preferredWidth: 26
                ToolTip.text: qsTr("Clear Tray")
                ToolTip.visible: trayClearBtn.hovered
                ToolTip.delay: 500
                contentItem: Image {
                    objectName: "trayClearIcon"
                    anchors.centerIn: parent
                    source: "icons/tray-clear.svg"
                    sourceSize: Qt.size(14, 14)
                    opacity: trayClearBtn.enabled ? 1.0 : 0.5
                }
            }
            // #455: „Add to" — a TÁLCA TARTALMA egyenesen albumhoz adható.
            // Az eredetiben felfelé nyíló menüből választható az album; itt
            // a meglévő album-listát (`controller.albums`) kínáljuk fel,
            // ugyanabban a sorrendben, mint a kép-kontextusmenü.
            PicasaButton {
                id: trayAddToBtn
                objectName: "trayAddToButton"
                text: qsTr("Add to")
                // #718: null-őr — `tray.ctl` a leépítés végén lehet igaz úgy
                // is, hogy az `albums` lista már nem érhető el (undefined).
                // A `!!` a láncolt `&&` esetleges `undefined` eredményét
                // valódi bool-lá kényszeríti (a `bool`-property-hez az
                // `undefined` hozzárendelése önmagában is szkripthiba).
                enabled: !!(trayPreview.heldCount > 0
                         && tray.ctl && tray.ctl.albums
                         && tray.ctl.albums.length > 0)
                onClicked: trayAddToMenu.popup()
                ToolTip.text: qsTr("Add the pictures in the tray to an album")
                ToolTip.visible: trayAddToBtn.hovered
                ToolTip.delay: 500
            }
            Menu {
                id: trayAddToMenu
                objectName: "trayAddToMenu"
                Repeater {
                    model: tray.ctl ? tray.ctl.albums : []
                    delegate: MenuItem {
                        required property var modelData
                        text: modelData.name
                        onTriggered: tray.ctl.addHeldToAlbum(modelData.token)
                    }
                }
            }

            // #455: a Picasa saját szövegű rákérdezése ürítéskor —
            // „Would you like to clear your old held items from the
            // tray?" → „Clear Tray" / „Don't Clear" (az issue kutatása
            // szerint ez a szöveg). Az általános `ConfirmDialog` Igen/
            // Nem/Mégse feliratai NEM egyeznek ezekkel, ezért itt egyedi,
            // egyszerű dialógus.
            Dialog {
                id: trayClearConfirm
                objectName: "trayClearConfirmDialog"
                modal: true
                anchors.centerIn: parent ? Overlay.overlay : undefined
                title: qsTr("Clear Tray")
                Text {
                    Layout.preferredWidth: 280
                    text: qsTr(
                        "Would you like to clear your old held items"
                        + " from the tray?")
                    wrapMode: Text.WordWrap
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                footer: RowLayout {
                    spacing: 8
                    Item { Layout.fillWidth: true }
                    PicasaButton {
                        objectName: "trayClearConfirmYesButton"
                        text: qsTr("Clear Tray")
                        accent: Theme.picasaGreen
                        onClicked: {
                            tray.ctl && tray.ctl.clearHeld()
                            trayClearConfirm.close()
                        }
                    }
                    PicasaButton {
                        objectName: "trayClearConfirmNoButton"
                        text: qsTr("Don't Clear")
                        onClicked: trayClearConfirm.close()
                    }
                    Item { width: 8 }
                }
            }

            PicasaButton {
                id: trayStar
                // #718: null-őr — ld. a fenti `ctl` docstringje; appWindow
                // hiányában a célsor -1 (nincs cél), a gomb letiltva.
                readonly property int targetRow: tray.appWindow
                    ? (tray.appWindow.viewerOpen
                       ? tray.viewerIndex : tray.appWindow.selectedIndex)
                    : -1
                readonly property bool multi: tray.appWindow
                    ? (!tray.appWindow.viewerOpen
                       && tray.appWindow.selectedIndexes.length > 1)
                    : false
                enabled: tray.appWindow
                         ? (tray.appWindow.viewerOpen
                            || tray.appWindow.selectedIndex >= 0)
                         : false
                Layout.preferredWidth: 34
                onClicked: multi
                           ? controller.toggleStarMany(
                                 tray.appWindow.selectedIndexes)
                           : controller.toggleStar(targetRow)
                contentItem: Text {
                    objectName: "trayStarLabel"
                    text: "★"
                    font.pixelSize: 15
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    // arany, ha a kiválasztott kép csillagos; egyébként
                    // világos kontúr-csillag (Picasa-minta, nem fekete!)
                    color: (tray.ctl
                            ? (tray.ctl.photos.revision,
                               tray.ctl.photos.starAt(trayStar.targetRow))
                            : false)
                           ? Theme.starYellow : "#ffffff"
                    style: Text.Outline
                    styleColor: "#9a9a9a"
                }
            }
            PicasaButton {
                id: trayRotateLeftBtn
                objectName: "trayRotateLeft"
                text: "↺"
                // #103: csak-videó kijelölésnél tiltva (photos.revision:
                // modell-frissüléskor újraértékelt kötés)
                // #718: null-őr — az appWindow (`window`) az engine-
                // leépítés közben átmenetileg null lehet (ld. a `ctl`
                // docstringje); ilyenkor a gomb egyszerűen letiltva marad.
                enabled: (tray.ctl ? tray.ctl.photos.revision : 0,
                          tray.appWindow
                          ? ((tray.appWindow.viewerOpen
                              || tray.appWindow.selectedIndex >= 0)
                             && !tray.appWindow.rotateTargetsAllVideo())
                          : false)
                Layout.preferredWidth: 34
                onClicked: trayStar.multi
                           ? controller.rotateLeftMany(
                                 tray.appWindow.selectedIndexes)
                           : controller.rotateLeft(trayStar.targetRow)
                // #314: a PicasaButton alap-krómja (PicasaButton.qml) nem
                // témavezérelt — mindig világos bevel-gomb. Az alapértelmezett
                // contentItem az `ink`-et használná, ami sötét témán
                // kivilágosodik és eltűnne a világos gombháttéren; itt a
                // fix `Theme.iconInk`-kel felülírjuk (letiltva marad a
                // PicasaButton eredeti, szintén rögzített szürkéje).
                contentItem: Text {
                    objectName: "trayRotateLeftLabel"
                    text: trayRotateLeftBtn.text
                    font: trayRotateLeftBtn.font
                    color: trayRotateLeftBtn.enabled ? Theme.iconInk : "#9a9a9a"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            PicasaButton {
                id: trayRotateRightBtn
                objectName: "trayRotateRight"
                text: "↻"
                // #718: null-őr — ld. trayRotateLeftBtn indoklása fentebb.
                enabled: (tray.ctl ? tray.ctl.photos.revision : 0,
                          tray.appWindow
                          ? ((tray.appWindow.viewerOpen
                              || tray.appWindow.selectedIndex >= 0)
                             && !tray.appWindow.rotateTargetsAllVideo())
                          : false)
                Layout.preferredWidth: 34
                onClicked: trayStar.multi
                           ? controller.rotateRightMany(
                                 tray.appWindow.selectedIndexes)
                           : controller.rotateRight(trayStar.targetRow)
                // #314: ld. trayRotateLeftBtn indoklása fentebb.
                contentItem: Text {
                    objectName: "trayRotateRightLabel"
                    text: trayRotateRightBtn.text
                    font: trayRotateRightBtn.font
                    color: trayRotateRightBtn.enabled ? Theme.iconInk : "#9a9a9a"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Item { Layout.fillWidth: true }
            // nagyítás-csúszka − / + jelekkel (kézikönyv 06) — #406:
            // kompakt módban a csúszka is keskenyebb, hogy jusson hely
            // a jobb oldali gomboknak
            Text { text: "−"; color: Theme.textGray; font.pixelSize: 13 }
            PicasaSlider {
                id: sizeSlider
                // #718: null-őr — ld. a fenti `ctl` docstringje; appWindow
                // hiányában egy tetszőleges, a [from, to] tartományba eső
                // érték (a csúszka úgyis leépülőben van ekkor).
                from: 72; to: 256
                value: tray.appWindow ? tray.appWindow.thumbSize : 128
                Layout.preferredWidth: trayMainBar.compact ? 90 : 140
                onMoved: tray.appWindow && (tray.appWindow.thumbSize = value)
            }
            Text { text: "+"; color: Theme.textGray; font.pixelSize: 13 }
            Item { width: trayMainBar.compact ? 4 : 10 }
            // #361: a kimeneti sáv gombjai saját SVG-ikonnal (PBZ-leltár:
            // outputlayout/ebutton, /pbutton) — a felirat objectName-jei
            // (label szöveg, iconInk-szín) VÁLTOZATLANOK, csak egy Image
            // került a Text mellé (icons/PicasaButtonWithIcon mintája
            // lentebb, trayExportBtn-nél).
            PicasaButton {
                id: trayEmailBtn
                objectName: "trayEmailButton"
                text: qsTr("E-Mail")
                // #32: kijelölés kell hozzá, néző-nézetben (egy kép) is
                // elérhető — a trayExportBtn/trayCollageBtn mintája
                // #718: null-őr — ld. a fenti `ctl` docstringje.
                enabled: tray.appWindow
                         ? (tray.appWindow.viewerOpen
                            ? tray.viewerIndex >= 0
                            : tray.appWindow.selectedIndexes.length > 0)
                         : false
                onClicked: tray.emailRequested()
                // #406: kompakt módban (szűk ablak) a felirat eltűnik,
                // csak az ikon marad — a szöveg tooltipként érhető el
                // (a MÁR fordított gombfeliratot használjuk, nem új
                // qsTr-t)
                ToolTip.text: trayEmailBtn.text
                ToolTip.visible: trayMainBar.compact && trayEmailBtn.hovered
                ToolTip.delay: 500
                contentItem: Row {
                    spacing: trayMainBar.compact ? 0 : 5
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        source: "icons/email.svg"
                        sourceSize: Qt.size(14, 14)
                        opacity: trayEmailBtn.enabled ? 1.0 : 0.5
                    }
                    Text {
                        objectName: "trayEmailLabel"
                        visible: !trayMainBar.compact
                        anchors.verticalCenter: parent.verticalCenter
                        text: trayEmailBtn.text
                        font: trayEmailBtn.font
                        color: trayEmailBtn.enabled ? Theme.iconInk : "#9a9a9a"
                    }
                }
            }
            PicasaButton {
                id: trayPrintBtn
                objectName: "trayPrintButton"
                text: qsTr("Print")
                // #718: null-őr — ld. a fenti `ctl` docstringje.
                enabled: tray.appWindow
                         ? (tray.appWindow.viewerOpen
                            ? tray.viewerIndex >= 0
                            : tray.appWindow.selectedIndexes.length > 0)
                         : false
                onClicked: tray.printRequested()
                ToolTip.text: trayPrintBtn.text
                ToolTip.visible: trayMainBar.compact && trayPrintBtn.hovered
                ToolTip.delay: 500
                contentItem: Row {
                    spacing: trayMainBar.compact ? 0 : 5
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        source: "icons/print.svg"
                        sourceSize: Qt.size(14, 14)
                        opacity: trayPrintBtn.enabled ? 1.0 : 0.5
                    }
                    Text {
                        objectName: "trayPrintLabel"
                        visible: !trayMainBar.compact
                        anchors.verticalCenter: parent.verticalCenter
                        text: trayPrintBtn.text
                        font: trayPrintBtn.font
                        color: trayPrintBtn.enabled ? Theme.iconInk : "#9a9a9a"
                    }
                }
            }
            PicasaButton {
                id: trayExportBtn
                objectName: "trayExportButton"
                text: qsTr("Export")
                // #718: null-őr — ld. a fenti `ctl` docstringje.
                enabled: tray.appWindow
                         ? (!tray.appWindow.viewerOpen
                            && tray.appWindow.selectedIndexes.length > 0)
                         : false
                onClicked: tray.exportRequested()
                // #314: a PicasaButton alap-krómja nem témavezérelt (ld.
                // trayRotateLeftBtn indoklása fentebb) — az ikon+felirat
                // tintája itt is a fix Theme.iconInk.
                ToolTip.text: trayExportBtn.text
                ToolTip.visible: trayMainBar.compact && trayExportBtn.hovered
                ToolTip.delay: 500
                contentItem: Row {
                    spacing: trayMainBar.compact ? 0 : 5
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        source: "icons/folder-export.svg"
                        sourceSize: Qt.size(14, 14)
                        opacity: trayExportBtn.enabled ? 1.0 : 0.5
                    }
                    Text {
                        objectName: "trayExportLabel"
                        visible: !trayMainBar.compact
                        anchors.verticalCenter: parent.verticalCenter
                        text: trayExportBtn.text
                        font: trayExportBtn.font
                        color: trayExportBtn.enabled ? Theme.iconInk : "#9a9a9a"
                    }
                }
            }
            Item { width: trayMainBar.compact ? 3 : 6 }
            // #361: Kollázs / Film / Megosztás — a PBZ-leltár szerint
            // (outputlayout/collage, /makemovie, /sharewith) az eredeti
            // kimeneti sávnak is részei; a tényleges Létrehozás-funkció
            // a Create-menü mellett innen is indítható (collage/movie
            // signal → Main.qml → CreateDialogs); a Megosztás backend
            // híján tiltott helyőrző marad. Nincs
            // qsTr-tooltip: a "Picture Collage..."/"Movie"/"Share" szöveg
            // MÁR fordított a CreateDialogs/PicasaMenuBar/Main kontextusban
            // — új kontextusban újra felvéve a lupdate "unfinished"-nek
            // látná (test_i18n_completeness.py), az integrátor a menü-
            // pontokkal egy körben veheti fel ide is a fordítást.
            PicasaButton {
                id: trayCollageBtn
                objectName: "trayCollageButton"
                // #718: null-őr — ld. a fenti `ctl` docstringje.
                enabled: tray.appWindow
                         ? (!tray.appWindow.viewerOpen
                            && tray.appWindow.selectedIndexes.length > 0)
                         : false
                onClicked: tray.collageRequested()
                Layout.preferredWidth: 30
                contentItem: Image {
                    objectName: "trayCollageIcon"
                    anchors.centerIn: parent
                    source: "icons/collage.svg"
                    sourceSize: Qt.size(16, 16)
                    opacity: trayCollageBtn.enabled ? 1.0 : 0.5
                }
            }
            PicasaButton {
                id: trayMovieBtn
                objectName: "trayMovieButton"
                // #718: null-őr — ld. a fenti `ctl` docstringje.
                enabled: tray.appWindow
                         ? (!tray.appWindow.viewerOpen
                            && tray.appWindow.selectedIndexes.length > 0)
                         : false
                onClicked: tray.movieRequested()
                Layout.preferredWidth: 30
                contentItem: Image {
                    objectName: "trayMovieIcon"
                    anchors.centerIn: parent
                    source: "icons/movie.svg"
                    sourceSize: Qt.size(16, 16)
                    opacity: trayMovieBtn.enabled ? 1.0 : 0.5
                }
            }
            PicasaButton {
                id: trayShareBtn
                objectName: "trayShareButton"
                enabled: false
                Layout.preferredWidth: 30
                contentItem: Image {
                    objectName: "trayShareIcon"
                    anchors.centerIn: parent
                    source: "icons/share.svg"
                    sourceSize: Qt.size(16, 16)
                    opacity: 0.5
                }
            }
            Item { width: trayMainBar.compact ? 3 : 6 }
            // az egyetlen zöld elsődleges tett — jobbra igazítva,
            // a képernyő vizuális súlypontja (kézikönyv 01/08) — #406:
            // kompakt módban ez is ikon-only (a leghosszabb felirat,
            // enélkül fér csak el a sáv szűk ablaknál)
            PicasaButton {
                id: trayUploadBtn
                objectName: "trayUploadButton"
                text: qsTr("Upload to Google Photos")
                enabled: false
                accent: Theme.picasaGreen
                ToolTip.text: trayUploadBtn.text
                ToolTip.visible: trayMainBar.compact && trayUploadBtn.hovered
                ToolTip.delay: 500
                contentItem: Row {
                    spacing: trayMainBar.compact ? 0 : 5
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        source: "icons/upload.svg"
                        sourceSize: Qt.size(14, 14)
                    }
                    Text {
                        objectName: "trayUploadLabel"
                        visible: !trayMainBar.compact
                        anchors.verticalCenter: parent.verticalCenter
                        text: trayUploadBtn.text
                        font: trayUploadBtn.font
                        color: "white"
                    }
                }
            }
        }
    }
}
