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

    // #718: a kijelölés VÉDETT olvasata. A leépítésnek van egy köztes
    // állapota, amikor az `appWindow` már létezik, a `selectedIndexes`
    // viszont még/már `undefined` — a `.length` olvasása ilyenkor
    // TypeError. Az olvasó kötések ezért ezen a tulajdonságon át kérik a
    // kijelölést; az ÍRÁS (a kijelölés módosítása) marad közvetlenül az
    // `appWindow`-on, mert az csak felhasználói művelet közben fut, amikor
    // az ablak biztosan él.
    //: #1168 (spec 16.3): `CThumbUI::CreateCollageWait` (`0x007f7120`) — a
    //: főablak várakozó sora, amíg a kollázs készül. Külön tulajdonságban,
    //: hogy az infó-sáv hármas feltétele olvasható maradjon.
    readonly property string collageWaitText:
        qsTr("Waiting for the collage to be created…")

    readonly property var selectedIndexesOrEmpty:
        (tray.appWindow && tray.appWindow.selectedIndexes)
            ? tray.appWindow.selectedIndexes
            : []

    // tömör acélkék infó-sáv; kijelöléskor a kép adatai
    Rectangle {
        id: infoBar
        width: parent.width; height: 20
        color: Theme.infoBar
        clip: true

        // SAJÁT FUNKCIÓ (#70): lassan végigvonuló fény-hullám, amíg a
        // PicasaPy a háttérben dolgozik (indexelés, thumbnail-batch). Az
        // eredetiben nincs ilyen vizuális visszajelzés — saját UX-
        // kiegészítés (lista: docs/decisions/vedett-sajat-funkciok.md).
        // XAnimator: a render-szálon fut (a főszálat/GIL-t nem érinti, ld.
        // #53), idle-ben running=false → 0 CPU/GPU. Nem polloz: a
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
            objectName: "trayInfoText"
            anchors.centerIn: parent
            // #718: null-őr — a `ctl` mellett az `appWindow` is
            // átmenetileg null lehet az engine-leépítés utolsó kiértékelésekor.
            //
            // #1189: az eredeti `GetSelectionInfo` (`0x0056fbc0`) a
            // KIJELÖLÉSRŐL ír. Nálunk a „minden más" ág a mappa egészének
            // összesítését (`statusText`) mutatta, ezért több kijelölt
            // képnél a mappa adatai maradtak a sávban.
            //
            // #1168 (spec 16.3): a kollázs rajzolása alatt a FŐABLAK is
            // jelez — `CThumbUI::CreateCollageWait` (`0x007f7120`). A
            // várakozás MINDEN mást megelőz: a kollázs lapja közben be is
            // zárulhat, és a felhasználó máshol nézelődik, miközben a munka
            // fut — az eredeti éppen ezért a KÖNYVTÁRNÉZETBEN mondja ki.
            text: (!tray.ctl || !tray.appWindow) ? ""
                  : (tray.ctl.collageRendering === true ? tray.collageWaitText
                  : (tray.appWindow.viewerOpen
                  ? tray.ctl.viewerInfo(tray.viewerIndex)
                  : (tray.appWindow.selectedIndexes.length === 1
                     ? tray.ctl.photoInfo(tray.appWindow.selectedIndex)
                     : (tray.appWindow.selectedIndexes.length > 1
                        && typeof tray.ctl.selectionInfo === "function"
                        ? tray.ctl.selectionInfo(tray.appWindow.selectedIndexes)
                        : tray.ctl.statusText))))
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

        // #406: szűk ablaknál (pl. fél képernyő) a sáv ne lógjon ki — a
        // küszöb alatt a kijelölés-előnézet és a csúszka zsugorodik, a
        // zöld Feltöltés gomb ikon-only lesz, a csoportelválasztók pedig
        // elmaradnak.
        //
        // #1345: a KIMENETI GOMBOK feliratai kikerültek ebből a
        // számításból. A gombok azóta FIX 55 × 36 képpontosak (a felirat
        // az ikon alatt, a gombon BELÜL ül), tehát a feliratuk semmivel
        // nem szélesíti a sávot — hiába rejtenénk el, egyetlen képpontot
        // sem nyernénk vele, csak információt veszítenénk. Egyedül a zöld
        // Feltöltés gomb maradt tartalomhoz igazodó szélességű, ezért
        // csak annak a feliratát mérjük.
        //
        // A küszöb NEM fix pixelérték: a felirat tényleges szélessége
        // betűkészlet- és NYELVFÜGGŐ (a windows-CI éppen ezen bukott el
        // — ott a szélesebb rendszerbetűvel 1280 px-en is kilógott a
        // sáv). A `TextMetrics` nem függ az elrendezéstől, így
        // kötés-hurok sem keletkezik.
        TextMetrics {
            id: uploadLabelMetrics
            font.pixelSize: Theme.fontSize
            text: qsTr("Upload to Google Photos")
        }
        // A fix (felirat-független) elemek helyigénye: kijelölés-előnézet,
        // ikonsorok, a kimeneti gombok cellái, csúszka, térközök.
        // INVARIÁNS, amiért ez biztonságos: a bő elrendezés tényleges
        // igénye = fix + a Feltöltés felirata; a küszöb = költségvetés +
        // ugyanaz a felirat. Bő módba csak `width >= küszöb` esetén
        // váltunk, és ekkor width >= költségvetés + felirat >= fix +
        // felirat = igény — vagyis a tartalom elfér. A bizonyítás
        // annyiban nem teljes, hogy a „fix" részben is van néhány apró,
        // betűfüggő tétel (ld. lentebb); azokra a költségvetés ráhagyása
        // felel.
        //
        // #1345: újramérve a három képes kijelöléssel (a legdrágább eset,
        // mert ilyenkor látszik a 200 px-es kijelölés-előnézet). A bő sáv
        // tényleges igénye 1221 px, ebből a Feltöltés felirata 133 px,
        // tehát a fix rész 1088. Felfelé kerekítve 1120-ra: a 32 képpont
        // ráhagyás azokat az apró, szintén betűfüggő tételeket fedi,
        // amelyek nem külön mértek (az „Add to" gomb felirata, a ± jelek)
        // — ugyanaz a ráhagyás, mint a #1116 előtti 1040-es értéknél.
        readonly property real compactBudget: 1120
        // A küszöb kívülről is olvasható (teszt), hogy a „széles ablak"
        // esetet ne fix pixelértékkel kelljen megadni — az platform- és
        // nyelvfüggő lenne (a windows-CI éppen ezen bukott el 1280-on).
        readonly property real compactThreshold: compactBudget
                                        + uploadLabelMetrics.width
        readonly property bool compact: width < compactThreshold
        // #1345: a két csoportelválasztó két TELJES cellát (2 × 59 px)
        // tesz a sávba. Az eredetiben a `morebutton`/`overflow` gondozza
        // a helyhiányt; amíg az nincs meg, a legolcsóbb hű viselkedés az,
        // ha az elválasztók csak ott jelennek meg, ahol ez a többlet is
        // bizonyíthatóan elfér.
        readonly property int actionCellWidth: 59
        readonly property bool separatorsVisible:
            width >= compactThreshold + 2 * actionCellWidth

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
                        // NEM elég csak az appWindow-t vizsgálni: a
                        // leépítés egy köztes állapotában az ablak MÁR
                        // létezik, a `selectedIndexes` viszont még
                        // `undefined` — ezt a `.length` olvasása
                        // TypeError-ral bünteti. (Ez a maradék hiba a
                        // teszt lefutása UTÁN, a késleltetett törlési sor
                        // ürítésekor jelentkezett, ezért az őr sem látta.)
                        model: trayPreview.heldCount > 0
                            ? trayPreview.heldCount
                            : tray.selectedIndexesOrEmpty.length
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
                             && tray.selectedIndexesOrEmpty.length === 0
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
                    // #1188: a `Control` a contentItem geometriáját maga
                    // állítja be (az `anchors.centerIn` ezért hatástalan
                    // volt), a `fillMode` alapja pedig `Image.Stretch` —
                    // a négyzetes SVG így a gomb tartalom-dobozára feszült
                    // (mérve: 14×14-es forrás 16×26-ra nyúlva).
                    fillMode: Image.PreserveAspectFit
                    source: "icons/hold-pin.svg"
                    sourceSize: Qt.size(28, 28)
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
                    // #1188: a `Control` a contentItem geometriáját maga
                    // állítja be (az `anchors.centerIn` ezért hatástalan
                    // volt), a `fillMode` alapja pedig `Image.Stretch` —
                    // a négyzetes SVG így a gomb tartalom-dobozára feszült
                    // (mérve: 14×14-es forrás 16×26-ra nyúlva).
                    fillMode: Image.PreserveAspectFit
                    source: "icons/tray-clear.svg"
                    sourceSize: Qt.size(28, 28)
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
            // #1345: a cellák EGYMÁS MELLETT, külön térköz nélkül —
            // az eredetiben a 2-2 képpontos cellamargó ADJA a gombok
            // közötti hézagot (4 képpont), a sáv `spacing`-je nem adódik
            // hozzá. Ezért a csoport saját, nulla térközű sora.
            Row {
                objectName: "trayActionRow"
                Layout.alignment: Qt.AlignVCenter
                spacing: 0

                // #1345: a kimeneti sáv gombjai a `respack.yt` MÉRT
                // geometriájával — mindegyik **55 × 36** képpont, egy
                // **59 × 40**-es cellában (`TrayActionCell`, 2-2 képpont margó
                // körbe; `docs/specs/picasa-keptalca.md` 11.). A méret FIX: a
                // rétegfejlécek mind a kilenc gombra bájtra azonosak, tehát a
                // sáv nem skálázhatja őket az ablakkal.
                //
                // A sorrend a respack DEKLARÁCIÓS sorrendje (spec 7.):
                // print → email → export → [shop] → hello → [blog] → collage →
                // movie → [morebutton]. A szögletes zárójelben álló három gomb
                // nálunk MÉG NINCS MEG (`docs/specs/ui-lefedettseg.md`
                // `outputlayout` hiánylistája: `orderbutton`, `blogger`,
                // `morebutton`) — a meglévők egymáshoz képesti sorrendje
                // viszont az eredetié. A zöld „Feltöltés" (`webupload`) nem
                // tartozik a mért kilenc közé, ezért marad a saját méretén.
                //
                // #361: a gombok saját SVG-ikonnal (PBZ-leltár:
                // outputlayout/pbutton, /ebutton, /folderbutton, /sharewith,
                // /collage, /movie).
                TrayActionCell {
                    TrayActionButton {
                        id: trayPrintBtn
                        objectName: "trayPrintButton"
                        anchors.fill: parent
                        text: qsTr("Print")
                        iconSource: "icons/print.svg"
                        iconObjectName: "trayPrintIcon"
                        labelObjectName: "trayPrintLabel"
                        // #32: kijelölés kell hozzá, néző-nézetben (egy kép) is
                        // elérhető
                        // #718: null-őr — ld. a fenti `ctl` docstringje.
                        enabled: tray.appWindow
                                 ? (tray.appWindow.viewerOpen
                                    ? tray.viewerIndex >= 0
                                    : tray.appWindow.selectedIndexes.length > 0)
                                 : false
                        onClicked: tray.printRequested()
                        // #1345: a felirat a fix méretű gombon BELÜL ül,
                        // ezért minden ablakszélességen látszik. Ha nagyon
                        // szűk helyre szorul, a betű zsugorodik — a teljes
                        // szöveget ezért a buboréksúgó is kiírja (a MÁR
                        // fordított gombfeliratot használjuk, nem új qsTr-t).
                        ToolTip.text: trayPrintBtn.text
                        ToolTip.visible: trayPrintBtn.hovered
                        ToolTip.delay: 500
                    }
                }
                TrayActionCell {
                    TrayActionButton {
                        id: trayEmailBtn
                        objectName: "trayEmailButton"
                        anchors.fill: parent
                        text: qsTr("E-Mail")
                        iconSource: "icons/email.svg"
                        iconObjectName: "trayEmailIcon"
                        labelObjectName: "trayEmailLabel"
                        // #718: null-őr — ld. a fenti `ctl` docstringje.
                        enabled: tray.appWindow
                                 ? (tray.appWindow.viewerOpen
                                    ? tray.viewerIndex >= 0
                                    : tray.appWindow.selectedIndexes.length > 0)
                                 : false
                        onClicked: tray.emailRequested()
                        ToolTip.text: trayEmailBtn.text
                        ToolTip.visible: trayEmailBtn.hovered
                        ToolTip.delay: 500
                    }
                }
                TrayActionCell {
                    TrayActionButton {
                        id: trayExportBtn
                        objectName: "trayExportButton"
                        anchors.fill: parent
                        text: qsTr("Export")
                        iconSource: "icons/folder-export.svg"
                        iconObjectName: "trayExportIcon"
                        labelObjectName: "trayExportLabel"
                        // #718: null-őr — ld. a fenti `ctl` docstringje.
                        enabled: tray.appWindow
                                 ? (!tray.appWindow.viewerOpen
                                    && tray.appWindow.selectedIndexes.length > 0)
                                 : false
                        onClicked: tray.exportRequested()
                        ToolTip.text: trayExportBtn.text
                        ToolTip.visible: trayExportBtn.hovered
                        ToolTip.delay: 500
                    }
                }
                // `outputlayout/sharewith` („Hello") — backend híján tiltott
                // helyőrző, de a HELYE az eredetié: az export után, a kollázs
                // előtt (a kimaradó `shop` és `blog` közé esne).
                TrayActionCell {
                    TrayActionButton {
                        id: trayShareBtn
                        objectName: "trayShareButton"
                        anchors.fill: parent
                        enabled: false
                        iconSource: "icons/share.svg"
                        iconObjectName: "trayShareIcon"
                    }
                }
                // #1345: a csoportelválasztó (`outputlayout/separator`), 2 × 27
                // képpont a saját 59 × 40-es cellájában. Szűk ablakban elmarad:
                // a fix méretű cellák mellett ez a 118 képpont az, ami a
                // kompakt sávba már nem fér bele (az eredetiben erre való a
                // `morebutton`/`overflow`, ami nálunk még nincs meg).
                TrayActionSeparator { visible: trayMainBar.separatorsVisible }
                // #361: Kollázs / Film — a PBZ-leltár szerint
                // (outputlayout/collage, /makemovie) az eredeti kimeneti
                // sávnak is részei; a tényleges Létrehozás-funkció a
                // Create-menü mellett innen is indítható (collage/movie
                // signal → Main.qml → CreateDialogs).
                //
                // #1116: a Kollázs gomb felirata és buboréksúgója NEM új
                // fordítás, hanem átvétel a Picasa saját honosítási
                // táblájából (`outputlayout_text.tre`): „Collage" →
                // „Kollázs", `Create a Photo Collage with your selection` →
                // „Készítsen fotókollázst a kijelölt képekből".
                TrayActionCell {
                    TrayActionButton {
                        id: trayCollageBtn
                        objectName: "trayCollageButton"
                        anchors.fill: parent
                        text: qsTr("Collage")
                        iconSource: "icons/collage.svg"
                        iconObjectName: "trayCollageIcon"
                        labelObjectName: "trayCollageLabel"
                        // #718: null-őr — ld. a fenti `ctl` docstringje.
                        enabled: tray.appWindow
                                 ? (!tray.appWindow.viewerOpen
                                    && tray.appWindow.selectedIndexes.length > 0)
                                 : false
                        onClicked: tray.collageRequested()
                        // #1116: az eredeti súgója a művelet MONDATA, nem a
                        // gombfelirat ismétlése — ezért (a Nyomtatás/Exportálás
                        // gombtól eltérően) kompakt módon kívül is látszik.
                        ToolTip.text: qsTr("Create a Photo Collage with your selection")
                        ToolTip.visible: trayCollageBtn.hovered
                        ToolTip.delay: 500
                    }
                }
                TrayActionCell {
                    TrayActionButton {
                        id: trayMovieBtn
                        objectName: "trayMovieButton"
                        anchors.fill: parent
                        iconSource: "icons/movie.svg"
                        iconObjectName: "trayMovieIcon"
                        // #718: null-őr — ld. a fenti `ctl` docstringje.
                        enabled: tray.appWindow
                                 ? (!tray.appWindow.viewerOpen
                                    && tray.appWindow.selectedIndexes.length > 0)
                                 : false
                        onClicked: tray.movieRequested()
                    }
                }
                TrayActionSeparator { visible: trayMainBar.separatorsVisible }
            }
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
