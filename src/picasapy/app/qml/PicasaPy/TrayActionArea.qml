import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: actionArea
    property var trayRoot
    property var actionController
    property var trayBar
    anchors.fill: parent

        // `thumbui/separator`: 2 képpont, `0, .365, -3` … `1, 1, -17`,
        // y 50…52 a sáv tetejétől — nálunk (a 20-as infó-csík alatt)
        // y 30…32.
        Rectangle {
            objectName: "traySeparator"
            x: -3
            y: 30
            width: Math.max(0, parent.width - 4)
            height: 2
            color: Theme.trayBorder
        }

        // `thumbui/webupload_rect`: 145 × 44 az osztóponttól 5
        // képponttal balra, benne a 141 × 35-ös gomb.
        //
        // 145 = a kényszerek (`0, .365, -5` … `1, .365, 140`); a
        // respack-fejléc 147-e nem a doboz szélessége.
        Item {
            id: trayUploadSlot
            objectName: "trayUploadSlot"
            x: -5
            y: 36
            width: 145
            height: 44

            // az egyetlen zöld elsődleges tett (kézikönyv 01/08)
            PicasaButton {
                id: trayUploadBtn
                objectName: "trayUploadButton"
                anchors.centerIn: parent
                width: 141
                height: 35
                //: picasapy-origin: picasa
                //: picasapy-origin-key: stringres:CThumbUI::ShareButtonLabelEs
                text: qsTr("Upload to Google Photos")
                enabled: (actionArea.actionController
                    && actionArea.actionController.googlePhotosUploadEnabled !== undefined)
                    ? actionArea.actionController.googlePhotosUploadEnabled : false
                onClicked: {
                    googlePhotosUploadDialog.open()
                    actionArea.actionController.uploadGooglePhotosTray()
                }
                accent: Theme.picasaGreen
                //: picasapy-origin: picasa
                //: picasapy-origin-key: stringres:CThumbUI::ShareButtonTipEs
                ToolTip.text: qsTr("Upload photos in the Photo Tray to Google Photos")
                ToolTip.visible: trayUploadBtn.hovered
                ToolTip.delay: Theme.tooltipDelay
                // #1420: a gomb FIX 141 × 35, a felirat pedig KÉT SORBA
                // tördel benne — pontosan úgy, ahogy az eredetin
                // („Feltöltés a Google / Fotókba"). A `PicasaButton`
                // `Text.Wrap` + `Text.Fit` + `clip` hármasa (#992) itt
                // is véd: elidálni nem elidál, és a gombon kívülre sem
                // folyhat. Ezért nincs többé ikon-only kompakt mód: a
                // gomb szélessége már nem az ablakszélesség függvénye.
                contentItem: Row {
                    spacing: 5
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        source: "icons/upload.svg"
                        sourceSize: Qt.size(18, 14)
                    }
                    Text {
                        objectName: "trayUploadLabel"
                        width: trayUploadBtn.width - 2 * 5 - 18 - 5
                        // ⚠️ EXPLICIT magasság kell: enélkül a `Text`
                        // magassága a saját `contentHeight`-je, a
                        // `Text.Fit` pedig ebbe a körbe futva a
                        // ZSUGORÍTOTT, EGYSOROS megoldást választja
                        // (mérve: 9 képpontos betű, egy sor) a
                        // teljes méretű, kétsoros helyett.
                        height: parent.height
                        verticalAlignment: Text.AlignVCenter
                        text: trayUploadBtn.text
                        font: trayUploadBtn.font
                        color: "white"
                        wrapMode: Text.Wrap
                        elide: Text.ElideNone
                        fontSizeMode: Text.Fit
                        minimumPixelSize: trayUploadBtn.minimumLabelPixelSize
                        minimumPointSize: trayUploadBtn.minimumLabelPixelSize
                        horizontalAlignment: Text.AlignHCenter
                        lineHeightMode: Text.ProportionalHeight
                        lineHeight: 10 / 12
                        clip: true
                    }
                }
            }
        }

        Dialog {
            id: googlePhotosUploadDialog
            objectName: "googlePhotosUploadDialog"
            title: qsTr("Upload to Google Photos")
            modal: true
            width: 390
            standardButtons: Dialog.NoButton

            contentItem: ColumnLayout {
                spacing: 12

                Text {
                    objectName: "googlePhotosUploadStatus"
                    Layout.fillWidth: true
                    text: trayRoot.photosUploadMessage()
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.WordWrap
                }

                Text {
                objectName: "googlePhotosUploadFailedFile"
                    visible: !!actionArea.actionController
                        && actionArea.actionController.photosUploadError !== undefined
                        && actionArea.actionController.photosUploadCurrentName !== undefined
                        && actionArea.actionController.photosUploadError
                        && actionArea.actionController.photosUploadError !== "cancelled"
                        && actionArea.actionController.photosUploadCurrentName.length > 0
                    Layout.fillWidth: true
                    text: visible
                        //: picasapy-origin: picasa
                        //: picasapy-origin-key: stringres:QuickUploader::errorMsg
                        ? qsTr("Failed to upload %1").arg(actionArea.actionController.photosUploadCurrentName)
                        : ""
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.WordWrap
                }

                ProgressBar {
                    objectName: "googlePhotosUploadProgress"
                    Layout.fillWidth: true
                    from: 0
                    to: (actionArea.actionController && actionArea.actionController.photosUploadTotal !== undefined)
                        ? Math.max(1, actionArea.actionController.photosUploadTotal) : 1
                    value: (actionArea.actionController && actionArea.actionController.photosUploadDone !== undefined)
                        ? actionArea.actionController.photosUploadDone : 0
                    visible: (actionArea.actionController
                        && actionArea.actionController.photosUploadRunning !== undefined)
                        ? actionArea.actionController.photosUploadRunning : false
                }

                RowLayout {
                    Layout.fillWidth: true
                    Item { Layout.fillWidth: true }
                    PicasaButton {
                        objectName: "googlePhotosUploadCancelButton"
                        text: actionArea.actionController && actionArea.actionController.photosUploadRunning
                            ? qsTr("Cancel") : qsTr("Close")
                        onClicked: {
                            if (actionArea.actionController && actionArea.actionController.photosUploadRunning)
                                actionArea.actionController.cancelGooglePhotosUpload()
                            else
                                googlePhotosUploadDialog.close()
                        }
                    }
                }
            }
        }

        // `thumbui/outputs`: `XConstraint 0, .365, 140` … `1, 1, -10`
        //
        // #1345: a cellák EGYMÁS MELLETT, külön térköz nélkül — az
        // eredetiben a 2-2 képpontos cellamargó ADJA a gombok közötti
        // hézagot, a sáv `spacing`-je nem adódik hozzá.
        Row {
            id: trayActionRow
            objectName: "trayActionRow"
            // #4637: a testreszabható alsó gombsor jobb klikkjére a
            // gazda ugyanazt a menüt nyitja, mint az Eszközök menü.
            TapHandler {
                objectName: "trayConfigureButtonsContextMenuHandler"
                acceptedButtons: Qt.RightButton
                gesturePolicy: TapHandler.ReleaseWithinBounds
                onSingleTapped: function (point) {
                    trayRoot.configureButtonsContextMenuRequested(
                        trayActionRow,
                        point.position.x,
                        point.position.y)
                }
            }
            // a 40 képpontos cellák a zöld gomb 44-es helyére
            // függőlegesen középre: 36 + (44 − 40) / 2 = 38
            x: trayBar.outputsOffset
            y: 38
            spacing: 0

            // ---- #2191: túlcsordulás ------------------------------
            //
            // Az eredetiben a sor konténere `overflow:` típusú, és a
            // ki nem férő tételek egy dedikált gomb mögé kerülnek
            // (`outputlayout/morebutton`, 55 × 36 — mint a másik
            // nyolc). A gombok NEM nyomódnak össze: a mért méret
            // kötelező, épp ezért kell a túlcsordulás.
            //
            //: a sávban maradó hely a sor kezdetétől a jobb margóig
            //: A kimeneti gomboknak jutó hely. ⚠️ NEM a sor `x`-éből
            //: számol: a sáv szélesség-modellje a #1420 óta a
            //: `windowWidthFor()`-ban van levezetve (osztópont, jobb
            //: margó, 140-es eltolás, kerekítési ráhagyás) — ez itt
            //: annak az INVERZE, hogy egyetlen igazságforrás legyen.
            //: A kivezetett gombok és a csoportelválasztók helyét le
            //: kell vonni, mert azok a sorban a kimenetiek ELŐTT ülnek.
            readonly property int elerhetoSzelesseg: Math.max(
                0,
                (1 - trayBar.splitRatio) * trayBar.width
                    - trayBar.rightMargin
                    - trayBar.outputsOffset
                    - trayBar.roundingReserve
                    - (trayBar.retiredVisible
                       ? trayBar.retiredCellCount
                         * trayBar.actionCellWidth
                       : 0)
                    - (trayBar.separatorsVisible
                       ? 2 * trayBar.actionCellWidth
                       : 0))
            //: egy cella teljes szélessége — a MÉRT osztásköz, 55
            //: (#1504; a `docbounds` 59-e csak a cella-grafika)
            readonly property int cellaSzelesseg:
                trayBar.actionCellWidth
            //: a kimeneti gombok felirata, a respack deklarációs
            //: sorrendjében — a rejtett tételek listája ebből épül
            //: ⚠️ A feliratokat a GOMBOK adják, nem külön `qsTr()`
            //: hívások: két igazságforrásból a felugró lista némán
            //: elcsúszna a gombokétól (az első változatom „Email"-t és
            //: „Movie"-t írt, a gombokon „E-Mail" és „Mozgófilm" áll),
            //: és a fordítás-őr is két új, sosem látott szöveget kért
            //: volna számon.
            readonly property var gombFeliratok: [
                trayPrintBtn.text, trayEmailBtn.text, trayExportBtn.text,
                trayCollageBtn.text, trayMovieBtn.text
            ]
            //: hány cella fér ki. Ha nem mind, EGY helyet a
            //: túlcsordulás-gomb foglal el.
            readonly property int kiferoCellak: {
                var osszes = trayActionRow.gombFeliratok.length
                var fer = Math.floor(
                    trayActionRow.elerhetoSzelesseg
                    / trayActionRow.cellaSzelesseg)
                if (fer >= osszes) return osszes
                return Math.max(0, fer - 1)   // egy hely a „További…"-nak
            }
            readonly property bool vanRejtett:
                trayActionRow.kiferoCellak < trayActionRow.gombFeliratok.length
            //: a ki NEM férő gombok feliratai — ebből épül a felugró
            //: lista. A tesztek is ezt mérik: a lista PONTOS kinézete
            //: nincs mérve (a respack csak a gombot adja), a TARTALMA
            //: viszont ellenőrizhető.
            readonly property var rejtettFeliratok:
                trayActionRow.gombFeliratok.slice(trayActionRow.kiferoCellak)
            // a ki nem férő gombok ikonja és engedélyezettsége — a
            // felugró ugyanazt mutatja, mint a sávbeli gomb (#4537)
            readonly property var gombIkonok: [
                trayPrintBtn.iconSource, trayEmailBtn.iconSource,
                trayExportBtn.iconSource, trayCollageBtn.iconSource,
                trayMovieBtn.iconSource
            ]
            readonly property var gombEngedelyezett: [
                trayPrintBtn.enabled, trayEmailBtn.enabled,
                trayExportBtn.enabled, trayCollageBtn.enabled,
                trayMovieBtn.enabled
            ]
            readonly property var rejtettIkonok:
                trayActionRow.gombIkonok.slice(trayActionRow.kiferoCellak)
            readonly property var rejtettEngedelyezett:
                trayActionRow.gombEngedelyezett.slice(trayActionRow.kiferoCellak)

            //: a hívó cellák ezzel kérdezik meg, látszanak-e
            function cellaLatszik(index) {
                return index < trayActionRow.kiferoCellak
            }

            //: a felugró listából indított művelet ugyanazt a jelet
            //: küldi, mint a sorbeli gomb — a rejtett tétel nem
            //: „másik" funkció, csak máshol érhető el
            function rejtettMuveletInditasa(menuIndex) {
                var i = trayActionRow.kiferoCellak + menuIndex
                if (i === 0) trayRoot.printRequested()
                else if (i === 1) trayRoot.emailRequested()
                else if (i === 2) trayRoot.exportRequested()
                else if (i === 3) trayRoot.collageRequested()
                else if (i === 4) trayRoot.movieRequested()
            }

            // #1345: a kimeneti sáv gombjai a `respack.yt` MÉRT
            // geometriájával — mindegyik **55 × 36** képpont, egy
            // **59 × 40**-es cellában (`TrayActionCell`;
            // `docs/specs/picasa-keptalca.md` 11.).
            //
            // A sorrend a respack DEKLARÁCIÓS sorrendje (spec 7.):
            // print → email → export → [shop] → hello → [blog] →
            // collage → movie → [morebutton]. A szögletes zárójelben
            // álló három gomb nálunk MÉG NINCS MEG
            // (`docs/specs/ui-lefedettseg.md` `outputlayout`
            // hiánylistája).
            TrayActionCell {
                //: #2191: a 0. cella — a sor számolja, kifér-e
                visible: trayActionRow.cellaLatszik(0)
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
                    enabled: trayRoot.appWindow
                             ? (trayRoot.appWindow.viewerOpen
                                ? trayRoot.viewerIndex >= 0
                                : trayRoot.appWindow.selectedIndexes.length > 0)
                             : false
                    onClicked: trayRoot.printRequested()
                    // #1345: a felirat a fix méretű gombon BELÜL ül,
                    // ezért minden ablakszélességen látszik.
                    ToolTip.text: trayPrintBtn.text
                    ToolTip.visible: trayPrintBtn.hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
            }
            TrayActionCell {
                //: #2191: a 1. cella — a sor számolja, kifér-e
                visible: trayActionRow.cellaLatszik(1)
                TrayActionButton {
                    id: trayEmailBtn
                    objectName: "trayEmailButton"
                    anchors.fill: parent
                    text: qsTr("E-Mail")
                    iconSource: "icons/email.svg"
                    iconObjectName: "trayEmailIcon"
                    labelObjectName: "trayEmailLabel"
                    // #718: null-őr — ld. a fenti `ctl` docstringje.
                    enabled: trayRoot.appWindow
                             ? (trayRoot.appWindow.viewerOpen
                                ? trayRoot.viewerIndex >= 0
                                : trayRoot.appWindow.selectedIndexes.length > 0)
                             : false
                    onClicked: trayRoot.emailRequested()
                    ToolTip.text: trayEmailBtn.text
                    ToolTip.visible: trayEmailBtn.hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
            }
            TrayActionCell {
                //: #2191: a 2. cella — a sor számolja, kifér-e
                visible: trayActionRow.cellaLatszik(2)
                TrayActionButton {
                    id: trayExportBtn
                    objectName: "trayExportButton"
                    anchors.fill: parent
                    text: qsTr("Export")
                    iconSource: "icons/folder-export.svg"
                    iconObjectName: "trayExportIcon"
                    labelObjectName: "trayExportLabel"
                    // #718: null-őr — ld. a fenti `ctl` docstringje.
                    enabled: trayRoot.appWindow
                             ? (!trayRoot.appWindow.viewerOpen
                                && trayRoot.appWindow.selectedIndexes.length > 0)
                             : false
                    onClicked: trayRoot.exportRequested()
                    ToolTip.text: trayExportBtn.text
                    ToolTip.visible: trayExportBtn.hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
            }
            // #1672: `outputlayout/shop` — „Papírképek rendelése".
            // KIVEZETETT (`retired`), nem helyfoglaló: a Picasa
            // nyomat-rendelő partnerszolgáltatásai megszűntek, tehát
            // nem ígérünk mögé jövőbeli funkciót. A HELYE viszont az
            // eredetié, a mért sorrend szerint: export UTÁN, „Hello"
            // ELŐTT.
            TrayActionCell {
                visible: trayBar.retiredVisible
                TrayActionButton {
                    id: trayOrderBtn
                    objectName: "trayOrderButton"
                    anchors.fill: parent
                    enabled: false
                    iconSource: "icons/share.svg"
                    iconObjectName: "trayOrderIcon"
                    //: kivezetett: a nyomat-rendelő szolgáltatás megszűnt
                    ToolTip.text: qsTr("Order Prints (service discontinued)")
                    ToolTip.visible: trayOrderBtn.hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
            }
            // `outputlayout/sharewith` („Hello") — backend híján tiltott
            // helyőrző, de a HELYE az eredetié: az export után, a kollázs
            // előtt (a `shop` és a `blog` közé esik).
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
            // #1672: `outputlayout/blog` — „Közzététel a Bloggeren".
            // Szintén KIVEZETETT: a Picasa Blogger-integrációja
            // megszűnt. A mért sorrendben a „Hello" UTÁN, a
            // csoportelválasztó ELŐTT áll.
            TrayActionCell {
                visible: trayBar.retiredVisible
                TrayActionButton {
                    id: trayBlogBtn
                    objectName: "trayBlogButton"
                    anchors.fill: parent
                    enabled: false
                    iconSource: "icons/share.svg"
                    iconObjectName: "trayBlogIcon"
                    //: kivezetett: a Blogger-integráció megszűnt
                    ToolTip.text: qsTr("Publish to Blogger (service discontinued)")
                    ToolTip.visible: trayBlogBtn.hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
            }
            // #1345: a csoportelválasztó (`outputlayout/separator`),
            // 2 × 27 képpont a saját 59 × 40-es cellájában. Szűk
            // ablakban elmarad: a fix méretű cellák mellett ez a 118
            // képpont az, ami már nem fér be. A kiesett GOMBOK a
            // „További…" mögé kerülnek (#2191); az elválasztó nem —
            // az puszta tagolás, nincs mit előhozni belőle.
            TrayActionSeparator { visible: trayBar.separatorsVisible }
            // #361: Kollázs / Film — a PBZ-leltár szerint
            // (outputlayout/collage, /makemovie) az eredeti kimeneti
            // sávnak is részei.
            //
            // #1116: a Kollázs gomb felirata és buboréksúgója NEM új
            // fordítás, hanem átvétel a Picasa saját honosítási
            // táblájából (`outputlayout_text.tre`).
            TrayActionCell {
                //: #2191: a 3. cella — a sor számolja, kifér-e
                visible: trayActionRow.cellaLatszik(3)
                TrayActionButton {
                    id: trayCollageBtn
                    objectName: "trayCollageButton"
                    //: #885: LENYOMÁSRA sül el — a `headerpanel/create_collage`
                    //: mért `Property mousedown 1`-e.
                    lenyomasra: true
                    anchors.fill: parent
                    text: qsTr("Collage")
                    iconSource: "icons/collage.svg"
                    iconObjectName: "trayCollageIcon"
                    labelObjectName: "trayCollageLabel"
                    // #718: null-őr — ld. a fenti `ctl` docstringje.
                    enabled: trayRoot.appWindow
                             ? (!trayRoot.appWindow.viewerOpen
                                && trayRoot.appWindow.selectedIndexes.length > 0)
                             : false
                    onClicked: trayRoot.collageRequested()
                    // #1116: az eredeti súgója a művelet MONDATA, nem a
                    // gombfelirat ismétlése.
                    ToolTip.text: qsTr(
                        "Create a Photo Collage with your selection")
                    ToolTip.visible: trayCollageBtn.hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
            }
            TrayActionCell {
                //: #2191: a 4. cella — a sor számolja, kifér-e
                visible: trayActionRow.cellaLatszik(4)
                TrayActionButton {
                    id: trayMovieBtn
                    objectName: "trayMovieButton"
                    Accessible.name: qsTr("Movie Maker")
                    //: #885: LENYOMÁSRA sül el — a `headerpanel/create_movie`
                    //: mért `Property mousedown 1`-e.
                    lenyomasra: true
                    anchors.fill: parent
                    iconSource: "icons/movie.svg"
                    iconObjectName: "trayMovieIcon"
                    // #718: null-őr — ld. a fenti `ctl` docstringje.
                    enabled: trayRoot.appWindow
                             ? (!trayRoot.appWindow.viewerOpen
                                && trayRoot.appWindow.selectedIndexes.length > 0)
                             : false
                    onClicked: trayRoot.movieRequested()
                    HoverHandler {
                        id: trayMovieHover
                        objectName: "trayMovieHoverHandler"
                    }
                    ToolTip.text: qsTr("Create Movie Presentation")
                    ToolTip.visible: trayMovieHover.hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
            }
            TrayActionSeparator { visible: trayBar.separatorsVisible }

            // #2191: `outputlayout/morebutton` — a ki nem férő gombok
            // mögötte, felugró listában. Csak akkor látszik, ha van
            // rejtett tétel.
            TrayActionCell {
                objectName: "trayMoreCell"
                visible: trayActionRow.vanRejtett
                //: ⚠️ #1672: a MECHANIZMUS itt SZÁNDÉKOSAN más, mint az
                //: eredetiben. A mérés szerint (`picasa-keptalca.md` 22.)
                //: a gomb nem menüt nyit, hanem a túlcsordulás-konténert
                //: BILLENTI: a `0x005fe090` a `morebutton` állapotbájtját
                //: invertálva írja a főablakba, és az
                //: `outputlayout/overflowcontainer` vtable 14. rését
                //: hívja.
                //:
                //: ⭐ #2973: azt, hogy a billentés MIT MUTAT, a 305. kör
                //: KIMÉRTE (`picasa-keptalca.md` 23.): a kifért gombok
                //: **egymás alá kerülnek, egy függőleges oszlopba** — nem
                //: második sorba, nem szélesedő sávba. A cellás
                //: elrendezés-ágban az X halmozó a ciklus ELŐTT áll be és
                //: nem változik (`0x0059868e`), az Y viszont minden
                //: gyerekre nő (`0x00598858`); a lépésköz a `Property`-ből
                //: jön (`cellwidth` → `+0x274`, `cellheight` → `+0x278`,
                //: a `.tre` 50 / 52, `outputlayout.tre:143–150`).
                //:
                //: ⇒ A felugró listánk **ugyanazt a fajtát** adja, amit az
                //: eredeti mutat: a rejtett gombok függőleges oszlopban,
                //: egymás alatt. Az eltérés a MEGVALÓSÍTÁSBAN van (nálunk
                //: felugró, ott a konténer saját oszlopa), nem abban, amit a
                //: felhasználó lát — ez tehát MÉRT döntés, nem feltevés.
                //:
                //: ⚠️ Ami továbbra sincs mérve: a nyílás iránya (le- vagy
                //: felfelé) és a takarása. A látvány egyeztetése külön
                //: kört kér; a mai döntéshez nem kell.
                TrayActionButton {
                    id: trayMoreBtn
                    objectName: "trayMoreButton"
                    anchors.fill: parent
                    //: `outputlayout_text` — angolul „More...”
                    text: qsTr("More...")
                    // #2537: az ikon a MÉRT rajzot követi. Az eredetiben
                    // ez az `outputlayout/export7_icon` (a `.tre` szerint
                    // a `morebutton` gyereke): **13 × 7**, egyetlen tömör,
                    // FELFELE mutató háromszög (soronként 1, 3, 5, 7, 9,
                    // 11, 13 képpont), egyetlen színnel — `#69729B`,
                    // élsimítás nélkül. A `respack.yt` rétegképéből
                    // kicsomagolva mérve; levezetés:
                    // `docs/specs/picasa-keptalca.md` 21.3.
                    //
                    // ⚠️ A #2493 óta a gomb ikon NÉLKÜL állt: az akkori
                    // hivatkozás egy SOSEM LÉTEZETT `icons/export.svg`-re
                    // mutatott (a `export7_icon` név félrevezet — a
                    // Picasa sorszámozott gombjaira utal, nem
                    // exportálásra), és minden induláskor
                    // `QQuickImage: Cannot open` hibát írt a konzolra.
                    iconSource: "icons/tray-more.svg"
                    iconObjectName: "trayMoreIcon"
                    labelObjectName: "trayMoreLabel"
                    enabled: true
                    onClicked: trayMoreMenu.open()
                    //: `Click here for more options`
                    ToolTip.text: qsTr("Click here for more options")
                    ToolTip.visible: trayMoreBtn.hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
            }
        }

        // #2191: a rejtett tételek listája. #4537: a felugró a MÉRT
        // formát követi — függőleges oszlop, a sávbeli gombokkal azonos
        // 55 × 36-os gombok, ikonnal és felirattal. A nyílás iránya
        // NINCS mérve (`picasa-keptalca.md` 23.5); a tálca az ablak alján
        // ül, ezért fölfelé nyílik, hogy a látható területen maradjon.
        Popup {
            id: trayMoreMenu
            objectName: "trayMoreMenu"
            parent: trayMoreBtn
            x: 0
            y: -height - 2
            padding: 0
            // a gombok mért 36-os lépésben, egymás alatt állnak
            width: trayActionRow.cellaSzelesseg
            height: trayActionRow.rejtettFeliratok.length * 36
            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
            background: Rectangle {
                color: Theme.trayPanelBg
                border.color: Theme.trayBorder
            }
            Repeater {
                model: trayActionRow.rejtettFeliratok
                delegate: TrayActionButton {
                    objectName: "trayMoreItem"
                    x: 0
                    y: index * 36
                    width: trayActionRow.cellaSzelesseg
                    height: 36
                    text: modelData
                    // a modell és a tömbök átmenetileg eltérhetnek
                    // (a cellaszám változásakor): a hiányzó érték
                    // ne törje el a kötést
                    iconSource: trayActionRow.rejtettIkonok[index] || ""
                    enabled: trayActionRow.rejtettEngedelyezett[index] === true
                    onClicked: {
                        trayMoreMenu.close()
                        trayActionRow.rejtettMuveletInditasa(index)
                    }
                }
            }
        }
}
