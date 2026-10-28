import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: trayScratchPanel
    property var trayRoot
    property var trayController
    property var trayBar
    anchors.fill: parent

    Rectangle {
        id: trayScratchBack
        objectName: "trayScratchBack"
        property var trayRoot: trayScratchPanel.trayRoot
        property var trayBar: trayScratchPanel.trayBar
        x: 5
        //: #1913: MÉRT térköz a kék csík alatt — `infotext` y 443-ig
        //: (nyílt), a `scratchback` y 449-től ⇒ HAT pont. (A #1914 itt
        //: ötöt írt, mert a 448-tól induló nagyító-/metaadat-csoportot
        //: mérte, nem a tálcát.)
        y: 6
        width: Math.max(0, trayBar.splitX - 15 - x)
        height: 81
        color: Theme.trayPanelBg
        border.width: 1
        border.color: Theme.trayBorder
        radius: 2
        clip: true

        //: #455: a tálca elemszáma (a gyökér `trayCount`-jából — egy
        //: helyen olvassuk a vezérlőt, hogy a null-őr se duplázódjon)
        readonly property int heldCount: trayRoot.trayCount

        //: #1919: az ÖSSZECSUKOTT mappa-/album-tokenek. Defenzív
        //: kötés: a QML-próbák stub-vezérlőjén nincs rajta ez a
        //: tulajdonság (`!== undefined` a #1572 mintája szerint).
        readonly property var albumTokens:
            (trayScratchPanel.trayController && trayScratchPanel.trayController.trayAlbumTokens !== undefined)
                ? trayScratchPanel.trayController.trayAlbumTokens : []
        readonly property int albumTokenCount: albumTokens.length

        // a bélyegképsor (`thumbui/scratch`): 5 képpont belső margó,
        // JOBBRÓL 50 képpont marad szabadon a három gombnak
        // #1904: a doboz magassága FIX, a bélyegképek ZSUGORODNAK és
        // TÖBB SORBA tördelődnek — nem tűnnek el némán.
        //
        // Húsz referencia-felvétel ugyanabban az 1920×1080-as
        // ablakban. A doboz külső mérete közben változatlan: nem
        // görgetősáv és nem levágás.
        //
        // Nálunk eddig egyetlen `Row` állt itt `clip: true`-val: a be
        // nem férő képek EGYSZERŰEN ELTŰNTEK. A kék infó-csík közben
        // a teljes darabszámot írta — a felület önmagának mondott
        // ellent.
        //
        // ## A MÉRT sorozat (spec `picasa-keptalca.md` 15.2)
        //
        //   kép | sorok | tartalom | osztásköz
        //     3 |   1   |   54     |  57,00
        //    12 |   1   |   48     |  51,00
        //    15 |   1   |   38     |  39,93
        //    19 |   1   |   29     |  31,00
        //    27 |   2   |   28     |  29,94
        //    49 |   2   |   22     |  24,00
        //    67 |   3   |  18–19   |  21,00
        //    82 |   3   |  18–19   |  21,00
        //
        // ⚠️ #1916 HELYESBÍTÉS: egy korábbi változat itt „h(2)=34 ·
        // h(3)=22 ← a mért érték"-et állított. **Ez téves volt** — a
        // 22 a KÉTSOROS, 49 képes eset tartalma, a háromsoros eseté
        // 18–19 (21-es osztásközzel). Mért értéknek nevezni valamit,
        // ami nem az, rosszabb, mint nem tudni.
        //
        // ⛔ A cellaméret pontos KÉPLETE: **NINCS MEG.** A spec 15.4
        // kimerítő keresést közöl a kézenfekvő modellre — ±1 tűréssel
        // 912 paraméterkészlet megy át a tizenhat megfigyelésen,
        // pontos egyezéssel NULLA. A tizenhat megfigyelés tehát nem
        // határozza meg a konstansokat, és a kézenfekvő modell rossz.
        //
        // Amit itt számolunk, az ezért NEM az eredeti képlete, hanem
        // egy VISELKEDÉS: fix doboz, semmi nem lóg ki, több sor nagyobb
        // darabszámnál — a felső korlát a mért 54. Az őr is ezt
        // rögzíti, nem képpontszámot.
        Flow {
            id: trayScratchStrip
            objectName: "trayScratchStrip"
            //: #1919: összecsukott token mellett a bélyegkép-sor nem
            //: rajzolódik ki — a `scratch/album` a sáv HELYÉT foglalja
            //: el (a `.tre` `m_scaleXY`-ja, és a mért felvétel).
            visible: trayScratchBack.albumTokenCount === 0
            x: 5
            y: 5
            width: Math.max(0, parent.width - 5 - 50)
            height: parent.height - 10
            spacing: 2
            clip: true

            //: MÉRT felső korlát: egy sornál a tartalom 54 képpont,
            //: 57 képpontos osztásközzel (spec `picasa-keptalca.md`
            //: 15.2, tizenhat felvétel; a kék csík darabszám-felirata
            //: kalibrálja).
            readonly property int maxThumbHeight: 54
            //: ez alatt a bélyegkép már nem mond semmit — inkább vágunk
            readonly property int minThumbHeight: 12
            //: A cella NÉGYZET — mérve (spec 15.1). A `…214634.jpg`
            //: csíkfelirata a forrás méretét is kiírja (816×1456,
            //: álló, 0,560), a tálcabeli bélyegkép mégis 54×54; a
            //: normalizált keresztkorreláció háromból háromszor a
            //: KÖZÉPRE VÁGÁST hozza ki (+0,587 / +0,900 / +0,902) a
            //: nyújtás és az aránytartó illesztés ellenében. Ezért
            //: nincs többé „névleges oldalarány" becslés: a szélesség
            //: a magassággal egyenlő.

            readonly property int thumbCount:
                trayScratchBack.heldCount > 0
                    ? trayScratchBack.heldCount
                    : (trayRoot && trayRoot.selectedIndexesOrEmpty)
                        ? trayRoot.selectedIndexesOrEmpty.length
                        : 0

            function sorMagassag(sorok) {
                return Math.floor(
                    (height - (sorok - 1) * spacing) / sorok)
            }

            readonly property int thumbHeight: {
                var n = thumbCount
                var maxSorok = Math.max(
                    1, Math.floor((height + spacing)
                                  / (minThumbHeight + spacing)))
                var h = maxThumbHeight
                for (var sorok = 1; sorok <= maxSorok; ++sorok) {
                    h = Math.min(maxThumbHeight, sorMagassag(sorok))
                    var soronkent = Math.max(
                        1, Math.floor((width + spacing)
                                      / (h + spacing)))
                    if (n <= soronkent * sorok)
                        return h
                }
                return Math.max(minThumbHeight, h)
            }
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
                // TypeError-ral bünteti.
                model: trayScratchBack.heldCount > 0
                    ? trayScratchBack.heldCount
                    : (trayRoot && trayRoot.selectedIndexesOrEmpty)
                        ? trayRoot.selectedIndexesOrEmpty.length
                        : 0
                delegate: Image {
                    id: trayThumb
                    objectName: "trayPreviewThumb"
                    required property int index

                    // 20 × 20-as rács a 81 képpontos dobozban holt
                    // helyet hagyott volna.
                    height: trayScratchStrip.thumbHeight
                    // #1914 (spec 15.1): a cella NÉGYZET, a fotó
                    // középre VÁGVA — nem aránytartó illesztés.
                    width: height
                    source: !trayScratchPanel.trayController || !trayRoot.appWindow ? ""
                        : (trayRoot.photoRevision,
                           trayScratchBack.heldCount > 0
                           ? trayScratchPanel.trayController.heldThumbUrlAt(index)
                           : trayScratchPanel.trayController.photos.thumbUrlAt(
                                 Number(trayRoot.appWindow.selectedIndexes[index])))
                    // #1600: a bélyegkép-textúra a Qt gyorsítótárában KÖZÖS a
                    // ráccsal, ami mipmapot kér (#83). Eltérő beállítás mellett a
                    // Qt „Mipmap settings changed” figyelmeztetést ad, és
                    // VISSZAESIK a korábbi szűrésre — a kép nem azzal a szűréssel
                    // jelenik meg, amit kértünk (Windowson hatszor egy futásban).
                    smooth: true
                    mipmap: true
                    //: `PreserveAspectCrop` = a rövidebbik oldalra
                    //: illeszt, a hosszabbikat levágja — a `clip`
                    //: nélkül a levágott rész kilógna a cellából.
                    fillMode: Image.PreserveAspectCrop
                    clip: true
                    asynchronous: true

                    // #2039: a tálcának SAJÁT kijelölése van — az
                    // eredetiben ugyanolyan `CSelectionNode`, mint a
                    // rácsé (`picasa-keptalca.md` 13.). A kattintás a
                    // VEZÉRLŐN megy át, a módosítókkal együtt.
                    readonly property bool trayCellSelected:
                        trayRoot.trayIndexSelected(trayThumb.index)

                    // A rács húzóforrásával azonos MIME-szerződés, de a
                    // tálca saját kiválasztott elemeiből összeállítva.
                    readonly property string payload: "photos"
                    readonly property var photoRows: {
                        if (!trayScratchPanel.trayController || !trayScratchPanel.trayController.photos) return []
                        var items = trayScratchPanel.trayController.trayItems || []
                        var indexes = trayRoot.traySelectedIndexes
                        var rows = []
                        for (var i = 0; i < indexes.length; ++i) {
                            var index = Number(indexes[i])
                            if (index < 0 || index >= items.length
                                    || !items[index].path)
                                continue
                            var row = trayScratchPanel.trayController.photos.rowOfPath(
                                String(items[index].path))
                            if (row >= 0) rows.push(row)
                        }
                        return rows
                    }
                    // #5105: a húzás „teste" külön, az egeret követő
                    // elem — a cella maga nem mozdul (target: null),
                    // ezért a DropArea-találat a követő helyzetét nézi,
                    // felengedéskor pedig kifejezetten leadjuk.
                    Item {
                        id: trayDragProxy
                        objectName: "trayDragProxy"
                        width: 1; height: 1
                        x: trayDragHandler.centroid.position.x
                        y: trayDragHandler.centroid.position.y
                        readonly property string payload: trayThumb.payload
                        readonly property var photoRows: trayThumb.photoRows
                        Drag.active: trayDragHandler.active
                        Drag.dragType: Drag.Internal
                        Drag.mimeData: ({
                            "text/uri-list": trayRoot.selectedTrayFileUriList()
                        })
                        Drag.supportedActions:
                            Qt.CopyAction | Qt.MoveAction | Qt.LinkAction
                    }

                    DragHandler {
                        id: trayDragHandler
                        objectName: "trayThumbDragHandler"
                        enabled: trayThumb.trayCellSelected
                        acceptedButtons: Qt.LeftButton
                        target: null
                        onActiveChanged: {
                            if (!active) trayDragProxy.Drag.drop()
                        }
                    }

                    TapHandler {
                        objectName: "trayThumbTap"
                        acceptedButtons: Qt.LeftButton
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onSingleTapped: function (eventPoint, button) {
                            if (!trayScratchPanel.trayController
                                || typeof trayScratchPanel.trayController.selectTrayIndex !== "function")
                                return
                            trayScratchPanel.trayController.selectTrayIndex(
                                trayThumb.index,
                                (point.modifiers & Qt.ControlModifier) !== 0,
                                (point.modifiers & Qt.ShiftModifier) !== 0)
                        }
                    }

                    // A kijelölés KÉTVONALAS kerete — ugyanaz a réteg,
                    // mint a rácsban (`ThumbDelegate.qml` 89–108.):
                    // kívül `Theme.thumbSelection` (#009EFF), belül a
                    // kártya színe. Nem új stílus, hanem a meglévő
                    // újrahasználása (`constants.ui` thumbsel_color1/2).
                    Rectangle {
                        objectName: "trayThumbSelectionOuter"
                        visible: trayThumb.trayCellSelected
                        z: -1
                        anchors.centerIn: parent
                        readonly property int outerWidth: 2
                        readonly property int innerWidth: 1
                        width: parent.width + 2 * (outerWidth + innerWidth)
                        height: parent.height + 2 * (outerWidth + innerWidth)
                        color: Theme.thumbSelection
                    }
                    Rectangle {
                        objectName: "trayThumbSelectionInner"
                        visible: trayThumb.trayCellSelected
                        z: -1
                        anchors.centerIn: parent
                        width: parent.width + 2
                        height: parent.height + 2
                        color: Theme.thumbCard
                    }
                    // #1420: az eredeti tálcáján a bélyegképek a doboz
                    // TELJES belső magasságát kitöltik (a képernyőképen
                    // ~70 képpont), oldalarányt tartva — a korábbi

                    // #1918: a MEGTARTOTT kép jelvénye a bélyegképen.
                    //
                    // Az eredetiben a `thumbui/#holdadorner` — az
                    // adorner-CSALÁD első eleme (a `0x007145c0`-on
                    // épülő gyorsítótár +0x00 eltolása, `0x00cad36c`),
                    // ugyanabból a családból, mint a csillag
                    // (`adorners/star`), a geocímke vagy az arcok
                    // jelvénye. Mérete a respack-rétegfejléc szerint
                    // 10×10.
                    //
                    // Nálunk a megtartás eddig CSAK SZÁMKÉNT létezett
                    // (`heldCount`); a képen semmi nem jelezte. A
                    // rács-cellán már megvolt (#455, `holdMark`) — a
                    // tálca bélyegképein nem.
                    //
                    // ⚠️ A jelvény a MEGLÉVŐ `hold-pin.svg`, nem a
                    // respackből kicsomagolt PNG: a projekt egyetlen
                    // kicsomagolt Picasa-képet sem szállít, és a
                    // rács-cella ugyanezt a rajzot használja — így a
                    // két hely ugyanazt jelenti ugyanazzal a jellel.
                    Image {
                        objectName: "trayHoldMark"
                        //: #1572-minta: a `!== undefined` a hiányzó
                        //: TULAJDONSÁGRA véd (a próbák stub-vezérlőjén
                        //: nincs rajta).
                        //: ⚠️ A `heldCount` olvasása NEM felesleges: a
                        //: `heldAtTrayIndex(...)` puszta FÜGGVÉNYHÍVÁS,
                        //: amire a QML nem tud kötést építeni. A
                        //: `heldCount` a `heldChanged` jelzésre notifyol,
                        //: és a „megtartás" épp ezt sütteti el — enélkül
                        //: a jelvény csak a következő elrendezéskor
                        //: jelenne meg. (Ugyanaz a minta, mint a
                        //: `photos.revision` a rácsban.)
                        visible: (trayScratchPanel.trayController
                                  && trayScratchPanel.trayController.heldAtTrayIndex !== undefined
                                  && trayScratchPanel.trayController.heldCount !== undefined
                                  && trayScratchBack.heldCount > 0)
                                 ? (trayScratchPanel.trayController.heldCount,
                                    trayScratchPanel.trayController.heldAtTrayIndex(parent.index))
                                 : false
                        source: "icons/hold-pin.svg"
                        width: 6; height: 10
                        sourceSize.width: 6; sourceSize.height: 10
                        anchors.left: parent.left
                        anchors.bottom: parent.bottom
                        anchors.margins: 2
                    }
                }
            }
        }

        DropArea {
            objectName: "trayDropArea"
            x: trayScratchStrip.x
            y: trayScratchStrip.y
            width: trayScratchStrip.width
            height: trayScratchStrip.height
            enabled: trayScratchBack.albumTokenCount === 0
            onDropped: function(drop) {
                var source = drop.source
                if (!source || source.payload !== "photos"
                        || !source.photoRows
                        || source.photoRows.length === 0)
                    return
                drop.accept()
                trayRoot.photosDroppedOnTray(source.photoRows.slice())
            }
        }

        // #1919: az ÖSSZECSUKOTT mappa-/album-tokenek sávja.
        //
        // A `scratch.tre`-ben a `scratch/album` `m_scaleXY`-jal ül a
        // `thumbui/clip(scratch): scratch` SÁVON — vagyis a token a
        // bélyegkép-sor HELYÉT foglalja el, nem egy cellát benne. A
        // `…214629.jpg` felvételen pontosan ez látszik: EGY token a
        // doboz közepén, bélyegkép-rács nélkül, miközben a kék
        // infó-csík 82 képet ír. Ezért a token megjelenésekor a
        // bélyegkép-sor nem rajzolódik ki.
        //
        // ⛔ A `.tre` NEM ad rétegkészletet arra, hogy kép és token
        // EGYSZERRE látsszon: az eredetiben ilyen elrendezés nincs
        // kimérve. A vegyes eset ezért a MODELLBEN él (a tálca
        // egyszerre tarthat képet és tokent, `tests/tray/`), a
        // nézetben pedig a mért, teljes sávot elfoglaló token nyer.
        // Több token esetén a sávot egyenlően osztjuk el köztük —
        // EGY tokennél ez pont a mért elrendezést adja.
        Row {
            id: trayAlbumTokenRow
            objectName: "trayAlbumTokenRow"
            x: trayScratchStrip.x
            y: trayScratchStrip.y
            width: trayScratchStrip.width
            height: trayScratchStrip.height
            visible: trayScratchBack.albumTokenCount > 0

            Repeater {
                objectName: "trayAlbumTokenRepeater"
                model: trayScratchBack.albumTokens
                delegate: TrayAlbumToken {
                    required property var modelData
                    width: trayAlbumTokenRow.width
                           / Math.max(1, trayScratchBack.albumTokenCount)
                    height: trayAlbumTokenRow.height
                    photoCount: modelData.photoCount
                    isAlbum: modelData.isAlbum
                    coverSource: modelData.coverThumbUrl
                }
            }
        }
        // `thumbui/scratchlabel` — „Kijelölés", `m_centerXY`: a doboz
        // KÖZEPÉN álló ÁLLANDÓ vízjel.
        //
        // #2179: az eredetiben ez NEM üres-állapot felirat. A tulajdonos
        // hat felvétele ugyanabban a mappában, növekvő elemszámmal: 1 és
        // 3 bélyegképnél a felirat LÁTSZIK, 11-nél eltakarva, 6-nál a
        // vége (`…lés`) KILÓG a képek jobb oldalán. Az utolsó dönti el a
        // rétegsorrendet is: a felirat bal része a képek ALATT van.
        // Ugyanezt mondja a `thumbui.tre` szülő-gyerek viszonya
        // (`scratchpadbase` — és rajta a `scratchlabel` — előbb
        // deklarálva, mint a `thumbui/scratch`).
        //
        // Ezért NINCS `visible` kötése, és `z: -1`-gyel a bélyegképsor
        // ALÁ kerül. (A `z` a deklarációs sorrend átrendezése helyett:
        // a felirat így a `scratchback` gyerekeként marad, ahogy az
        // eredetiben is a `scratchpadbase`-é.)
        Text {
            objectName: "trayScratchLabel"
            z: -1
            anchors.centerIn: parent
            text: qsTr("Selection")
            // #2179: a respackből MÉRVE — `thumbui/scratchlabel`
            // (13,480)–(218,499), szín `#C3C3C3`; a párosított Theme-token
            // világos értéke változatlan, sötét témában olvashatóbb.
            color: Theme.trayScratchLabel
            // `m_displayfont14` = 14 pt (`docs/specs/picasa-hisztogram.md`,
            // ugyanaz a betűcsalád), és a felirat mért magassága 19
            // képpont — a kettő egybevág.
            font.pixelSize: 14
        }

        // #455/#1420: a Picasa 3-gombos OSZLOPA a bélyegképsor jobbján
        // fenntartott 50 képpontban (`scratchhold` 34 × 22,
        // `scratchclear` 34 × 20, `addtobuttcon` 34 × 22 — mind
        // `m_offsetRT` a `scratchback`-en). A gombokon az eredetiben
        // NINCS felirat: a `thumbui_text.tre`-ben mindhárom `Label`
        // sora ki van kommentelve, csak a `Tooltip` él.
        PicasaButton {
            id: trayHoldBtn
            objectName: "trayHoldButton"
            //: #3602: 7 képpont a `scratchback` jobb szélétől, nem 5
            //: (`scratchhold`/`scratchclear`/`addtobuttcon` `m_offsetRT`,
            //: `thumbui.tre:317,326,337`).
            x: parent.width - 7 - width
            y: 5
            width: 34
            height: 22
            // #718: null-őr — ld. a fenti `ctl` docstringje.
            enabled: trayRoot.appWindow
                     ? (!trayRoot.appWindow.viewerOpen
                        && trayRoot.appWindow.selectedIndexes.length > 0)
                     : false
            onClicked: trayScratchPanel.trayController && trayRoot.appWindow && trayScratchPanel.trayController.holdRows(
                trayRoot.appWindow.selectedIndexes)
            ToolTip.text: qsTr("Hold selected items")
            ToolTip.visible: trayHoldBtn.hovered
            ToolTip.delay: Theme.tooltipDelay
            contentItem: Image {
                objectName: "trayHoldIcon"
                // #1188: a `Control` a contentItem geometriáját maga
                // állítja be (az `anchors.centerIn` ezért hatástalan
                // volt), a `fillMode` alapja pedig `Image.Stretch` —
                // a négyzetes SVG így a gomb tartalom-dobozára feszült.
                fillMode: Image.PreserveAspectFit
                source: "icons/hold-pin.svg"
                sourceSize: Qt.size(28, 28)
                opacity: trayHoldBtn.enabled ? 1.0 : 0.5
            }
        }
        PicasaButton {
            id: trayClearBtn
            objectName: "trayClearButton"
            //: #3602: 7 képpont a `scratchback` jobb szélétől, nem 5
            //: (`scratchhold`/`scratchclear`/`addtobuttcon` `m_offsetRT`,
            //: `thumbui.tre:317,326,337`).
            x: parent.width - 7 - width
            y: 27
            width: 34
            height: 20
            enabled: trayScratchBack.heldCount > 0
            onClicked: trayClearConfirm.open()
            ToolTip.text: qsTr("Clear items from the selection")
            ToolTip.visible: trayClearBtn.hovered
            ToolTip.delay: Theme.tooltipDelay
            contentItem: Image {
                objectName: "trayClearIcon"
                // #1188: ld. a `trayHoldBtn` indoklását fentebb.
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
        //
        // #1420: a gomb IKON-ONLY lett, mert az eredeti tálcájában a
        // 34 képpontos oszlopban ül, és ott sincs felirata — a jelentést
        // a buboréksúgó hordozza (`thumbui_text.tre`: *Add selected
        // items to an Album*).
        PicasaButton {
            id: trayAddToBtn
            objectName: "trayAddToButton"
            //: #3602: 7 képpont a `scratchback` jobb szélétől, nem 5
            //: (`scratchhold`/`scratchclear`/`addtobuttcon` `m_offsetRT`,
            //: `thumbui.tre:317,326,337`).
            x: parent.width - 7 - width
            y: 54
            width: 34
            height: 22
            // #718: null-őr — `trayScratchPanel.trayController` a leépítés végén lehet igaz úgy
            // is, hogy az `albums` lista már nem érhető el (undefined).
            // A `!!` a láncolt `&&` esetleges `undefined` eredményét
            // valódi bool-lá kényszeríti (a `bool`-property-hez az
            // `undefined` hozzárendelése önmagában is szkripthiba).
            // A kijelölt képek a tálcára is tükröződnek, ezért a
            // tartott elem továbbra is szükséges; saját album nélkül
            // viszont a három különleges cél is használható.
            enabled: !!(trayScratchBack.heldCount > 0 && trayScratchPanel.trayController)
            // #5846: az eredeti `addtobuttcon` felfelé nyíló menü
            // (`dropup_icon`): a gomb fölött nyílik, nem az egérnél.
            onClicked: trayAddToMenu.popup(
                trayAddToBtn, 0, -trayAddToMenu.implicitHeight)
            ToolTip.text: qsTr("Add selected items to an Album")
            ToolTip.visible: trayAddToBtn.hovered
            ToolTip.delay: Theme.tooltipDelay
            contentItem: Image {
                objectName: "trayAddToIcon"
                fillMode: Image.PreserveAspectFit
                source: "icons/tray-addto.svg"
                sourceSize: Qt.size(30, 20)
                opacity: trayAddToBtn.enabled ? 1.0 : 0.5
            }
        }
    }

    PicasaMenu {
        id: trayAddToMenu
        objectName: "trayAddToMenu"
        // #5846, job-259: a sorrend Screensaver, Starred Photos, a saját
        // albumok, végül New Album..., elválasztó nélkül. A saját
        // albumok ezért a két különleges sor UTÁN kerülnek a menübe.
        Instantiator {
            model: trayScratchPanel.trayController ? trayScratchPanel.trayController.albums : []
            delegate: MenuItem {
                required property var modelData
                objectName: "trayAddToAlbumItem"
                text: modelData.name
                onTriggered: trayScratchPanel.trayController.addHeldToAlbum(modelData.token)
            }
            onObjectAdded: function (index, object) {
                trayAddToMenu.insertItem(2 + index, object)
            }
            onObjectRemoved: function (index, object) {
                trayAddToMenu.removeItem(object)
            }
        }
        MenuItem {
            objectName: "trayAddToScreensaverItem"
            text: qsTr("Screensaver", "stringres:CThumbDB::ScreensaverAlbumName")
            onTriggered: trayRoot.addSelectedToScreensaverRequested()
        }
        MenuItem {
            objectName: "trayAddToStarredPhotosItem"
            text: qsTr("Starred Photos", "stringres:CThumbDB::starredphotos")
            onTriggered: trayRoot.starSelectedPhotosRequested()
        }
        MenuItem {
            objectName: "trayAddToNewAlbumItem"
            text: qsTr("New Album...", "stringres:il_NewAlbumName")
            onTriggered: trayRoot.newAlbumWithSelectionRequested()
        }
    }

    Dialog {
        id: trayClearConfirm
        objectName: "trayClearConfirmDialog"
        modal: true
        anchors.centerIn: parent ? Overlay.overlay : undefined
        title: qsTr("Clear Tray")
        Text {
            objectName: "trayClearConfirmText"
            Layout.preferredWidth: 280
            text: qsTr(
                "This will clear your entire tray."
                + " Are you sure you want to do this?")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        footer: RowLayout {
            spacing: 8
            Item { Layout.fillWidth: true }
            //: A megerősítő gomb hivatalos magyarja MÁS, mint a
            //: párbeszéd címéé: `IDS_CLEARTRAY_YES_BUTTON` = „Törlés a
            //: tálcáról". Ugyanaz a forrásszöveg, más fordítás — ezért
            //: kap megkülönböztető második paramétert.
            PicasaButton {
                objectName: "trayClearConfirmYesButton"
                text: qsTr("Clear Tray", "IDS_CLEARTRAY_YES_BUTTON")
                accent: Theme.picasaGreen
                onClicked: {
                    trayScratchPanel.trayController && trayScratchPanel.trayController.clearHeld()
                    trayClearConfirm.close()
                }
            }
            //: A visszalépő gomb felirata NEM az eredeti „Don't Clear" —
            //: az a 4.2 párbeszédhez tartozik (ld. fent). A teljes
            //: ürítés kérdésének nemleges gombja nincs kimérve, ezért a
            //: program általános „Mégse"-jét használjuk.
            PicasaButton {
                objectName: "trayClearConfirmNoButton"
                text: qsTr("Cancel")
                onClicked: trayClearConfirm.close()
            }
            Item { width: 8 }
        }
    }
}
