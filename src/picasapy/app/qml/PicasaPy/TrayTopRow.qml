import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: trayTopRow
    objectName: "trayTopRow"
    property var trayRoot
    property var trayBar
    readonly property int starTargetRow: trayStar.targetRow
    readonly property bool starEnabled: trayStar.enabled
    readonly property real starGroupWidth: trayStarGroup.width
    readonly property real zoomGroupWidth: trayZoomGroup.width
    readonly property real metadataGroupWidth: trayMetadataGroup.width
    width: parent.width
    height: 22

    function activateStar() {
        trayStar.clicked()
    }

    // `startoggle` · `rotateleft` · `rotateright`: 36 × 22
    // egyenként, a csillag után 5 képpont hézag, a két forgatás
    // 37 képpontos osztásközzel (mérve: 697…732 · 738…773 ·
    // 775…810 egy 1918 képpontos ablakban).
    Row {
        id: trayStarGroup
        objectName: "trayStarGroup"
        //: #3602: `thumbui/startoggle` bal széle `S − 3`
        //: (`m_offsetRT` a 2 px széles `bcenterright`-on,
        //: `thumbui.tre:225`; a tulajdonos 1920 px-es
        //: képernyőképén 698 = 700,07 − 3).
        x: -3
        height: parent.height
        spacing: 1

        PicasaButton {
            id: trayStar
            //: #1224: SAJÁT név a gombnak. Eddig a tesztek a
            //: feliratának (`trayStarLabel`) a SZÜLŐJÉN át
            //: találták meg — a #1438 tesztje ezt panaszolta is
            //: („a gombnak magának nincs objectName-je"). Amint
            //: a felirat képre cserélődött és konténerbe került,
            //: a szülő-lánc eltört. Egy név stabilabb, mint egy
            //: hierarchia-feltevés.
            objectName: "trayStarButton"
            //: #885: LENYOMÁSRA sül el — a `headerpanel/select_star`
            //: mért `Property mousedown 1`-e.
            lenyomasra: true
            width: 36
            height: 22
            anchors.verticalCenter: parent.verticalCenter
            //: #1929: `thumbui/startoggle` — az EREDETI súgója,
            //: szó szerint (`referencia/ui-leltar.csv`). Eddig
            //: nem volt súgója.
            ToolTip.text: qsTr("Add/Remove Star")
            ToolTip.visible: trayStar.hovered
            ToolTip.delay: Theme.tooltipDelay
            // #718: null-őr — ld. a fenti `ctl` docstringje;
            // appWindow hiányában a célsor -1 (nincs cél).
            readonly property int targetRow: trayRoot.appWindow
                ? (trayRoot.appWindow.viewerOpen
                   ? trayRoot.viewerIndex : trayRoot.appWindow.selectedIndex)
                : -1
            readonly property bool multi: trayRoot.appWindow
                ? (!trayRoot.appWindow.viewerOpen
                   && trayRoot.appWindow.selectedIndexes.length > 1)
                : false
            enabled: trayRoot.appWindow
                     ? (trayRoot.appWindow.viewerOpen
                        || trayRoot.appWindow.selectedIndex >= 0)
                     : false
            onClicked: multi
                       ? controller.toggleStarMany(
                             trayRoot.appWindow.selectedIndexes)
                       : controller.toggleStar(targetRow)
            //: #1224: KÉP, nem betűjel. A `Text`-es `★` alakja a
            //: rendszer betűkészletétől függött (Windowson más
            //: glifa, mint Linuxon) — a tulajdonos ezt is
            //: „eltorzultnak" látta (#1188). Az eredeti
            //: raszterikont rajzol (`thumbui/startoggle_icon0`,
            //: MÉRT 17 × 17 a #1914 réteg-leltárából); a RAJZ a
            //: sajátunk.
            //:
            //: ⚠️ KÉT SVG, nem egy színezett: a QML `Image`
            //: shader nélkül nem színezhető, a `QtQuick.Effects`
            //: pedig szándékosan nincs a projektben.
            contentItem: Item {
            Image {
                objectName: "trayStarIcon"
                source: (trayRoot.ctl && trayRoot.ctl.photos
                         ? (trayRoot.ctl.photos.revision,
                            trayRoot.ctl.photos.starAt(trayStar.targetRow))
                         : false)
                        ? "icons/tray-star-on.svg"
                        : "icons/tray-star.svg"
                width: 17; height: 17
                sourceSize.width: 17; sourceSize.height: 17
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
            }
            }
        }
        //: #3602: a csillag utáni rés `S+38 − (S−3) − 36 = 5`
        //: (a `spacing` 1-ből kettő már megvan a két oldalán)
        Item { width: 3; height: 1 }
        PicasaButton {
            id: trayRotateLeftBtn
            objectName: "trayRotateLeft"
            //: #1224: a felirat KIÜRÜL — a gomb tartalma kép
            text: ""
            width: 36
            height: 22
            anchors.verticalCenter: parent.verticalCenter
            //: #1929: `thumbui/rotateleft` — az EREDETI súgója.
            ToolTip.text: qsTr("Rotate counter-clockwise")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            // #103: csak-videó kijelölésnél tiltva (photos.revision:
            // modell-frissüléskor újraértékelt kötés)
            // #718: null-őr — az appWindow (`window`) az engine-
            // leépítés közben átmenetileg null lehet.
            enabled: (trayRoot.ctl ? trayRoot.ctl.photos.revision : 0,
                      trayRoot.appWindow
                      ? ((trayRoot.appWindow.viewerOpen
                          || trayRoot.appWindow.selectedIndex >= 0)
                         && !trayRoot.appWindow.rotateTargetsAllVideo())
                      : false)
            onClicked: trayStar.multi
                       ? controller.rotateLeftMany(
                             trayRoot.appWindow.selectedIndexes)
                       : controller.rotateLeft(trayStar.targetRow)
            // #314: a PicasaButton alap-krómja nem témavezérelt —
            // mindig világos bevel-gomb. Az alapértelmezett
            // contentItem az `ink`-et használná, ami sötét témán
            // kivilágosodik és eltűnne a világos gombháttéren.
            //: #1224: KÉP, nem betűjel (`thumbui/rotateleft_icon`,
            //: MÉRT 11 × 15). A letiltott állapotot `opacity`
            //: jelzi — képre a `color` nem érvényes.
            contentItem: Item {
            Image {
                objectName: "trayRotateLeftIcon"
                source: "icons/tray-rotate-left.svg"
                width: 11; height: 15
                sourceSize.width: 11; sourceSize.height: 15
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
                opacity: trayRotateLeftBtn.enabled ? 1.0 : 0.4
            }
            }
        }
        PicasaButton {
            id: trayRotateRightBtn
            objectName: "trayRotateRight"
            //: #1224: a felirat KIÜRÜL — a gomb tartalma kép
            text: ""
            width: 36
            height: 22
            anchors.verticalCenter: parent.verticalCenter
            //: #1929: `thumbui/rotateright` — az EREDETI súgója.
            ToolTip.text: qsTr("Rotate clockwise")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            // #718: null-őr — ld. trayRotateLeftBtn indoklása.
            enabled: (trayRoot.ctl ? trayRoot.ctl.photos.revision : 0,
                      trayRoot.appWindow
                      ? ((trayRoot.appWindow.viewerOpen
                          || trayRoot.appWindow.selectedIndex >= 0)
                         && !trayRoot.appWindow.rotateTargetsAllVideo())
                      : false)
            onClicked: trayStar.multi
                       ? controller.rotateRightMany(
                             trayRoot.appWindow.selectedIndexes)
                       : controller.rotateRight(trayStar.targetRow)
            // #314: ld. trayRotateLeftBtn indoklása fentebb.
            //: #1224: KÉP, nem betűjel (`thumbui/rotateright_icon`,
            //: MÉRT 11 × 15) — a balra-forgatás párja.
            contentItem: Item {
            Image {
                objectName: "trayRotateRightIcon"
                source: "icons/tray-rotate-right.svg"
                width: 11; height: 15
                sourceSize.width: 11; sourceSize.height: 15
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
                opacity: trayRotateRightBtn.enabled ? 1.0 : 0.4
            }
            }
        }
    }

    // #1927: `thumbui/rect: metadata_group` — a NÉGY
    // panelkapcsoló (Emberek · Helyek · Címkék · Tulajdonságok).
    //
    // Mérve a `respack.yt` rétegfejléceiből (#1914; a tálca
    // függőleges méretei 1:1-ben képpontok):
    //
    //   metadata_group     545..785 × 448..472  →  240×24
    //   people_toggle      545..605             →   60×24
    //   places_toggle      605..665             →   60×24
    //   tags_toggle        665..725             →   60×24
    //   properties_toggle  725..785             →   60×24
    //
    // A négy gomb ÉRINTKEZIK (545→605→665→725→785, nincs rés),
    // és a típusneveik a szegmens-szerepet is megadják:
    // `buttcon_LS_` (bal szélső) · `_MS_` (két középső) ·
    // `_RS_` (jobb szélső) ⇒ ÖSSZEFÜGGŐ SZEGMENSSÁV, nem négy
    // különálló gomb. A `_text_RC` utótag: az ikon balra, a
    // felirat tőle jobbra, függőlegesen középre.
    //
    // A panelek MEGVANNAK (`activeDrawerTab`: people/places/
    // tags/properties) — itt csak a MÁSODIK belépési pont
    // hiányzott; a menüből eddig is el lehetett érni őket.
    //
    // ⚠️ Az ikonok SAJÁT RAJZOK. A méretük az eredetiből mért
    // (`people_icon` 19×17, `places_icon` 14×19, `tags_icon`
    // 19×15, `properties_icon` 17×18), de a projekt egyetlen
    // kicsomagolt Picasa-képet sem szállít — minden ikonunk
    // kézzel rajzolt SVG.
    //
    // ⛔ NINCS MEG: hogy a négy kapcsoló KIZÁRÓ csoport-e. A
    // #1773 a jobb fiók négy LAPJÁRA mérte ki a kizárólagosságot,
    // és nálunk egyetlen `activeDrawerTab` írja le mind a
    // négyet — a gombok ezt tükrözik. Hogy az EREDETI is így
    // viselkedik-e, nincs megmérve; a #1927 nyitott kérdése.
    Row {
        id: trayMetadataGroup
        objectName: "trayMetadataGroup"
        //: #2305: a MÉRT sorrend a `respack.yt` x-tartományaiból
        //: — `loupehit` 366…391 < `scalecontainer` 398…525 <
        //: `metadata_group` 545…785. Vagyis a csúszka MEGELŐZI a
        //: négy kapcsolót; korábban fordítva állt.
        //:
        //: #3602: a jobb szél `W − 15`, NEM a `trayTopRow`
        //: (`W − 10`-es) szélét örökli — a `metadata_group`-nak
        //: saját, 15-ös eltolása van a `.tre`-ben, a `rightMargin`
        //: (10) az `outputs` soré.
        anchors.right: parent.right
        anchors.rightMargin: 5
        anchors.verticalCenter: parent.verticalCenter
        spacing: 0            // a gombok ÉRINTKEZNEK (mérve)

        readonly property var kapcsolok: [
            { nev: "people", ikon: "panel-emberek.svg",
              felirat: qsTr("People"),
              sugo: qsTr("Show/Hide People Panel") },
            { nev: "places", ikon: "panel-helyek.svg",
              felirat: qsTr("Places"),
              sugo: qsTr("Show/Hide Places Panel") },
            { nev: "tags", ikon: "panel-cimkek.svg",
              felirat: qsTr("Tags"),
              sugo: qsTr("Show/Hide Tags Panel") },
            { nev: "properties", ikon: "panel-tulajdonsagok.svg",
              felirat: qsTr("Properties"),
              sugo: qsTr("Show/Hide Properties Panel") }
        ]

        Repeater {
            model: trayMetadataGroup.kapcsolok
            delegate: PicasaButton {
                required property var modelData
                required property int index
                objectName: "trayPanelToggle_" + modelData.nev
                //: #885: LENYOMÁSRA sül el — mind a négy
                //: (`properties_toggle`, `tags_toggle`,
                //: `places_toggle`, `people_toggle`) mért
                //: `Property mousedown 1`-et visel: panelt nyit,
                //: tehát azonnal hat.
                lenyomasra: true
                width: 60
                height: 24
                //: a szegmens-szerep: a szélsők lekerekítve, a
                //: középsők nem — így áll össze az összefüggő sáv
                readonly property bool balSzelso: index === 0
                readonly property bool jobbSzelso:
                    index === trayMetadataGroup.kapcsolok.length - 1
                //: #3709: a sáv KÜLSŐ kerete 1 képponttal
                //: beljebb fut, mint a 60 × 24-es cella. A
                //: `globalbuttons/left_segment_n`,
                //: `mid_segment_n`, `right_segment_n` képein
                //: (`respack.yt`) a keretvonal felül és alul az
                //: 1. és az utolsó előtti sorban áll, oldalt a
                //: bal szélső elem 1., a jobb szélső utolsó
                //: előtti oszlopában; a belső határokon a keret
                //: a cella szélén van. Mérve a tulajdonos 1920
                //: px-es képernyőképén is: a cellák 1665 · 1725 ·
                //: 1785 · 1845 · 1905, a keret oszlopai 1666 és
                //: 1903, az osztók 1724/1725, 1784/1785,
                //: 1844/1845, a keret 22 sor magas a 24-ből.
                topInset: 1
                bottomInset: 1
                leftInset: balSzelso ? 1 : 0
                rightInset: jobbSzelso ? 1 : 0
                //: #718-minta: a főablak átmenetileg null lehet
                //: az engine leépítésekor.
                //:
                //: ⚠️ TERNÁRIUS, nem `&&`: a JS `&&` a HAMIS
                //: OPERANDUST adja vissza (itt `null`-t), nem
                //: bool-t, és a Qt ilyenkor „Unable to assign
                //: [undefined] to bool" hibát ír. A #1260-as
                //: fixture-őr ezt a CI-n el is kapta.
                readonly property bool aktiv: trayRoot.appWindow
                    ? trayRoot.appWindow.activeDrawerTab === modelData.nev
                    : false
                accent: aktiv ? Theme.selectionBlue : "transparent"
                ToolTip.text: modelData.sugo
                ToolTip.visible: hovered
                ToolTip.delay: Theme.tooltipDelay
                //: ⚠️ a #1773 rádió-csapdája: az AKTÍV gombra
                //: kattintva a fiók BEZÁRUL, nem marad
                //: állapot nélkül
                onClicked: {
                    if (!trayRoot.appWindow) return
                    trayRoot.appWindow.activeDrawerTab =
                        aktiv ? "" : modelData.nev
                }
                //: #2305: a felirat NEM a gombon van. Az
                //: eredeti négy gombja kizárólag ikonos (a
                //: `buttcon_*` típusnevek is ikon-gombot
                //: jelölnek), és a 60 × 24-es cellába az ikon
                //: MELLETT a szöveg csak levágva fért volna be —
                //: a tulajdonos képernyőmentésén „Ember" és
                //: „Tulajdon:" látszott. A szöveg nem vész el:
                //: buboréksúgó és akadálymentesítési név.
                Accessible.name: modelData.felirat
                contentItem: Item {
                    Image {
                        source: "icons/" + modelData.ikon
                        width: 16; height: 16
                        fillMode: Image.PreserveAspectFit
                        anchors.centerIn: parent
                    }
                }
            }
        }
    }

    // `scale_group` — nagyítás-csúszka − / + jelekkel
    // (kézikönyv 06), a sáv jobb felső sarkához zárva
    // (`m_offsetRT` a `basecontrolset`-en)
    // #2564: ÁLLANDÓ SZÉLESSÉGŰ rés, két egymást váltó
    // tartalommal — szándékosan `Item`, nem `Row`.
    //
    // ⚠️ Ez nem stílusdöntés. `Row`-ként a néző megnyitásakor a
    // tartalomcsere ÁTRENDEZTE a felső sort, és az átrendeződés
    // alatt érkező EGYETLEN kattintás elveszett: a #2566 őre
    // élesben fogta meg, hogy a fiók bal szélső gombja
    // („Emberek") a néző megnyitása után az első kattintásra
    // nem nyílt ki. Rögzített szélességgel a váltás nem mozgat
    // semmit.
    //
    // A rögzített szélesség a MÉRÉSSEL is egybevág: a két mód
    // sávja UGYANOTT ÉR VÉGET (`thumbui/scalecontainer` 525,
    // `editpanel/zoomslider_container` 526), csak balra nyúlik
    // különbözőt — ezért mindkét sor a JOBB SZÉLHEZ zár.
    Item {
        id: trayZoomGroup
        objectName: "trayZoomGroup"
        //: #2305: a négy panelkapcsoló ELŐTT (ld. ott a mért
        //: x-tartományokat).
        //: #3602: a rés MÉRT 20 képpont (nem 12) — a
        //: `scale_group` és a `metadata_group` közti térköz a
        //: tulajdonos képernyőképén.
        anchors.right: trayMetadataGroup.left
        anchors.rightMargin: 20
        anchors.verticalCenter: parent.verticalCenter
        width: Math.max(trayLibraryZoomRow.width,
                        trayViewerZoomRow.width)
        height: Math.max(trayLibraryZoomRow.height,
                         trayViewerZoomRow.height)

        // #2564: KÖNYVTÁR-módú tartalom. Ugyanez a rés a
        // nézőben a nagyítás-hármast hordozza (lásd alább) —
        // az eredetiben is egyetlen sáv, cserélt tartalommal.
        Row {
            id: trayLibraryZoomRow
            objectName: "trayLibraryZoomRow"
            visible: !trayRoot.viewerZoomAvailable
            //: #3602: a nagyító ↔ csúszka rés MÉRT 7 képpont.
            //: A korábbi `−`/`+` felirat-pár nem az eredetié
            //: (a `scale_group`-ban nincs ilyen elem) — a jelek
            //: eltűntek, a rés a kettő nélkül közvetlenül 7.
            spacing: 7
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter

            // #1911: a rács-nagyító KAPCSOLÓJA. A #1808 megépítette
            // a nagyítót, de a gombja a v0.8.198-ban kikerült az
            // eszköztárból, és a funkció ezzel elérhetetlenné vált —
            // a tulajdonos élesben jelentette, hogy „semmit nem
            // csinál". A lánc működik, csak nem volt mit megnyomni.
            //
            // Az ALSÓ SÁVBA kerül vissza, nem az eszköztárba: mérve
            // (`docs/specs/racs-nagyito.md` 1. és 5.) az eredeti
            // belépési pontja a `thumbui/loupehit`, egy 25 × 19-es
            // gomb a `scale_group`-ban, a nagyítás-csúszka ELŐTT
            // (`loupehit` x 366…391, `scalecontainer` x 398…525).
            // #3709: KERET NÉLKÜLI ikon. A `loupehit` az eredetiben
            // `vbutton` (`respack.yt`: tömör, átlátszó réteg), a
            // látható rajz csak a `thumbui/loupe` ikon — ezért
            // sima `Item` + `TapHandler`, gombkeret nélkül.
            Item {
                id: trayLoupeButton
                objectName: "trayLoupeButton"
                //: MÉRT méret (`thumbui/loupehit`)
                width: 25
                height: 19
                anchors.verticalCenter: parent.verticalCenter
                //: ⚠️ NEM `checkable` + kötött `checked` — az a
                //: projekt ismert rádió-csapdája (#1773): egy
                //: `Button` kattintáskor MAGA írná át a
                //: `checked`-et, és ezzel eltörné a kötést,
                //: amiből olvassuk. A `loupeActive` marad az
                //: EGYETLEN igazságforrás; a bekapcsolt
                //: állapotot egyedül az ikon opacitása jelzi
                //: (ld. lentebb) — KERET vagy kitöltés nélkül.
                //:
                //: A saját tesztje ezt élesben fogta meg: a
                //: kikapcsolás nem jutott el a rács rétegéhez.
                readonly property bool aktiv: trayRoot.appWindow
                    ? trayRoot.appWindow.loupeActive === true : false
                readonly property bool hovered: loupeHover.hovered
                //: ⚠️ A felfedezhetőség a MI döntésünk: az eredeti
                //: nem ad rá támpontot — mérve (spec 2. szakasz)
                //: külön egérmutatót SEM használ. A #1911 viszont
                //: kiköti, hogy kipróbálás nélkül is kiderüljön:
                //: nyomva HÚZNI kell. A buboréksúgó ezt mondja ki —
                //: #3476: az eredeti SAJÁT szövegével
                //: (`thumbui/loupehit`, hivatalos magyarral).
                ToolTip.text: qsTr("Click and drag over photos to magnify them")
                ToolTip.visible: trayLoupeButton.hovered
                ToolTip.delay: Theme.tooltipDelay
                Accessible.role: Accessible.Button
                Accessible.name: qsTr("Click and drag over photos to magnify them")
                Accessible.checkable: true
                Accessible.checked: aktiv
                Accessible.onPressAction: {
                    if (!trayRoot.appWindow) return
                    trayRoot.appWindow.loupeActive =
                        !trayRoot.appWindow.loupeActive
                }
                HoverHandler { id: loupeHover }
                //: felengedésre sül el, mint a `PicasaButton`
                //: alapesete (nem `lenyomasra`)
                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    gesturePolicy: TapHandler.ReleaseWithinBounds
                    onSingleTapped: {
                        if (!trayRoot.appWindow) return
                        trayRoot.appWindow.loupeActive =
                            !trayRoot.appWindow.loupeActive
                    }
                }
                Image {
                    objectName: "trayLoupeIcon"
                    source: "icons/loupe.svg"
                    //: `thumbui/loupe` — MÉRT 23 × 16, a 25 × 19-es
                    //: `loupehit`-en belül x 2, y 1 (`respack.yt`:
                    //: `loupehit` 366…391 × 451…470, `loupe`
                    //: 368…391 × 452…468) — a jobb szélhez zár,
                    //: nem középre
                    x: 2; y: 1
                    width: 23; height: 16
                    sourceSize.width: 23; sourceSize.height: 16
                    fillMode: Image.PreserveAspectFit
                    //: a kikapcsolt állapot halványabb, a
                    //: bekapcsoltat az opacitás jelzi
                    opacity: trayLoupeButton.aktiv ? 1.0 : 0.65
                }
            }
            //: #3729: a `scaleslider` CSALÁD (`respack.yt`
            //: `scaleslider/sliderbase`+`thumb`) — ugyanaz a
            //: mért geometria, amit az `EditorSlider`
            //: `scaleCsalad` ága már használ (9 képpontos sín,
            //: 16 × 22-es fogantyú). Eddig a sima
            //: `PicasaSlider` alapértéke (4 / 14 × 14) rajzolt
            //: ide.
            EditorSlider {
                id: sizeSlider
                objectName: "traySizeSlider"
                csalad: "scaleslider"
                // #718: null-őr — appWindow hiányában egy
                // tetszőleges, a [from, to] tartományba eső érték.
                from: 72; to: 256
                value: trayRoot.appWindow ? trayRoot.appWindow.thumbSize : 128
                //: `thumbui/scalecontainer` — FIX 127 képpont
                width: 127
                //: #3709: a RAJZOLT sáv (`scaleslider/sliderbase`,
                //: 121) mindkét végén 3 képponttal beljebb áll —
                //: a foglalat (127) nem szűkül
                grooveInset: 3
                anchors.verticalCenter: parent.verticalCenter
                onMoved: trayRoot.appWindow
                         && (trayRoot.appWindow.thumbSize = value)
            }
        }

        // #2564: NÉZŐ-módú tartalom — a szerkesztő
        // nagyítás-hármasa. Mérve (`respack.yt` +
        // `editpanel.tre`): `fit` x 286…323, `1to1` x 323…360,
        // `zoomup_icon` x 368…392, `zoomslider_container`
        // x 399…526 — vagyis a fenti könyvtári nagyító és
        // csúszka helyén, ugyanabban a sávban, a négy
        // panelkapcsoló ELŐTT.
        Row {
            id: trayViewerZoomRow
            objectName: "trayViewerZoomRow"
            visible: trayRoot.viewerZoomAvailable
            spacing: 6
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter

            // #2311: a `fit` és az `1to1` ÖSSZERAGASZTOTT
            // szegmenspár — mérve `editpanel/fit` x 286…323 és
            // `editpanel/1to1` x 323…360 (nincs rés köztük), a
            // sminkjük `globalbuttons/b38l_*` / `b38r_*`, azaz
            // bal és jobb szegmens. Ezért van saját `Row`
            // nulla térközzel: a külső sor 6 képpontos rése a
            // párt is szétvágná.
            Row {
                id: zoomSegmentPair
                objectName: "zoomSegmentPair"
                spacing: 0
                anchors.verticalCenter: parent.verticalCenter
                PicasaButton {
                    objectName: "zoomFitButton"
                    //: MÉRT méret (`editpanel/fit`)
                    width: 37; height: 22
                    //: Az eredeti kimért felirata.
                    ToolTip.text: qsTr("Fit Photo inside viewing area")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    //: `Property mousedown 1` — LENYOMÁSRA sül
                    //: el, nem felengedésre.
                    onPressed: trayRoot.zoomFitRequested()
                    contentItem: Item {
                        Image {
                            //: MÉRT ikonméret (`fit_icon` 14 × 12)
                            source: "icons/zoom-fit.svg"
                            width: 14; height: 12
                            fillMode: Image.PreserveAspectFit
                            anchors.centerIn: parent
                        }
                    }
                }
                PicasaButton {
                    objectName: "zoomActualButton"
                    //: MÉRT méret (`editpanel/1to1`)
                    width: 37; height: 22
                    //: Az eredeti kimért felirata.
                    ToolTip.text: qsTr("Display Photo at actual size")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onPressed: trayRoot.zoomActualRequested()
                    contentItem: Item {
                        Image {
                            //: MÉRT ikonméret (`1to1_icon` 17 × 12)
                            source: "icons/zoom-actual.svg"
                            width: 17; height: 12
                            fillMode: Image.PreserveAspectFit
                            anchors.centerIn: parent
                        }
                    }
                }
            }
            // `editpanel/zoomup_icon` — a csúszka melletti
            // nagyító. A `.tre` (`:1288`) a `zoomsliderrect`
            // GYEREKEKÉNT, `m_offsetLB`-vel horgonyozza, és
            // NEM ad neki `Property mousedown`-t (a `fit` és az
            // `1to1` kapott) — tehát DÍSZÍTŐ IKON, nem vezérlő.
            //
            // ⛔ NINCS MEG: a MAGASSÁGA. A mérés csak a
            // 24 képpontos szélességet adja (x 368…392); a
            // 16 képpontos magasság a könyvtári nagyítónkéval
            // egyezik, hogy a két mód ne ugráljon. Ha egyszer
            // kiderül, hogy vezérlő, az külön jegy.
            Image {
                objectName: "viewerZoomUpIcon"
                source: "icons/loupe.svg"
                width: 24; height: 16
                sourceSize.width: 24; sourceSize.height: 16
                fillMode: Image.PreserveAspectFit
                anchors.verticalCenter: parent.verticalCenter
                opacity: 0.65
            }
            //: #3729: ugyanaz a mért `scaleslider` család, mint
            //: a könyvtár-mód `traySizeSlider`-jé (a két mód
            //: UGYANAZT a sávot tölti ki cserélt tartalommal,
            //: ld. a #2564 kommentjét fentebb) — a fogantyú nem
            //: ugorhat a mód váltásakor.
            EditorSlider {
                id: zoomSlider
                objectName: "zoomSlider"
                csalad: "scaleslider"
                //: MÉRT szélesség (`editpanel/zoomslider_container`
                //: x 399…526).
                //:
                //: #2492: az ÉRTÉKKÉSZLET is a mért:
                //: **normalizált [0, 1]**, ahol 0 = illesztés és
                //: 0,5 = valódi méret. A köztes leképezést a
                //: néző `skalaErtekbol()`-ja végzi.
                width: 127
                //: #3709/#3729: a RAJZOLT sáv itt is 3 képponttal
                //: beljebb áll mindkét végén, mint a könyvtári
                //: `traySizeSlider`-nél — különben a sáv vége a
                //: módváltáskor 3 képpontot ugrana
                grooveInset: 3
                anchors.verticalCenter: parent.verticalCenter
                from: 0; to: 1
                onMoved: trayRoot.zoomValueRequested(value)
                // húzás közben a kéz vezet; egyébként az állapot
                Binding on value {
                    when: !zoomSlider.pressed
                    value: trayRoot.viewerZoomValue
                }
            }
        }
    }
}
