import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Indexkép-csoport fejléce — dizajnkézikönyv 08 + #423 (a Picasa saját
// `headerpanel.tre` respack-forrása szerinti tipográfia és elrendezés):
//   - cím: Georgia 20pt, a fejléc bal szélétől 50px behúzva (a mappa-ikon
//     UTÁN), jobbról a fejléc szélétől 20px-re levágva — hosszú névnél
//     halványuló kifutással, NEM "…"-tal;
//   - dátumsor: Georgia 14pt, ugyanaz a 50px-es bal behúzás;
//   - jobb-felső sarok: „Szinkronizálás az internettel" felirat + kapcsoló
//     (letiltott, funkció nélkül — csak az elrendezés része).
ColumnLayout {
    id: header
    property string folderName: ""
    property string dateText: ""
    property string description: ""
    signal descriptionEdited(string text)
    // zöld ▸: a mappa diavetítése (#8) — a bekötés a Main.qml-ben
    signal playRequested()
    // #422: a mappa-kontextusmenü HARMADIK megnyitási pontja — a felmérés
    // szerint a fejlécre jobbklikkelve UGYANAZ a 15 tételes menü jön elő,
    // mint a rács üres területén és a bal panel mappa-során
    signal contextMenuRequested()

    //: #1823: a fejléc-gombok DARABSZÁMOT írnak ki. A bináris erőforrásai
    //: minden fejléc-gombot két alakban tartanak — `albumbutton_save` és
    //: `albumbutton_save%d` —, vagyis üres kijelölésnél a szám nélküli,
    //: kijelölésnél a számos felirat megy ki.
    //:
    //: ⚠️ A `play` gombra ez NEM igaz: a mért listában (`save`, `sstar`,
    //: `sall`, `album`, `cd`, `menu`, `pubaction`) nincs `play%d`. A
    //: diavetítés ezért ikon marad, szám nélkül — a jegy „a play is"
    //: mondata a mérésnek mond ellent.
    property int selectedCount: 0

    //: „Szerkesztések mentése lemezre" (`save_edits`) — a kijelölt képek
    //: szerkesztéseit a FÁJLBA írja. A művelet maga a #444 mentés-
    //: párbeszédéé; ez a gomb csak egy újabb belépési pont hozzá.
    signal saveEditsRequested()

    //: „Csillagozottak kijelölése" (`select_star`) — ugyanaz a parancs,
    //: mint a menüsávban; itt is a jelenlegi mappára hat (#1145).
    signal selectStarredRequested()
    //: #1006: kollázs a fejléc csoportjából. Az eredetiben NÉGY belépési
    //: pont van; nálunk kettő működött (Létrehozás menü, kimeneti sáv), a
    //: két fejléc-gomb hiányzott.
    signal collageRequested()

    //: #2187: a SZEMÉLY-ALBUM módja. Az eredetiben a személy-album
    //: fejléce saját panel (`faceheaderpanel`), és rajta ül a
    //: javaslat-munkafolyamat; nálunk a személy képei ugyanebben a
    //: rácsban, ugyanezzel a fejléccel jelennek meg, ezért a vezérlők
    //: ide kerülnek, ebbe a módba. Üres név = nem személy-album.
    property string personName: ""
    //: hány MÉG EL NEM DÖNTÖTT javaslat tartozik ehhez a személyhez —
    //: a gazda tölti a vezérlő `personSuggestionCount`-jából
    property int suggestionCount: 0
    //: `confirmsug` — a javaslatok jóváhagyása
    signal confirmSuggestionsRequested()
    //: `removesel` — a javaslatok elvetése
    signal removeSuggestionsRequested()
    //: `moresug` — a felismerési lépcső lazítása, hogy több javaslat jöjjön
    signal moreSuggestionsRequested()

    //: a két javaslat-vezérlő együtt jelenik meg: nyitott személy-album ÉS
    //: van mit eldönteni
    readonly property bool javaslatokLatszanak:
        header.personName !== "" && header.suggestionCount > 0

    //: #2187: a `moresug` a jóváhagyás-pár TELJES helyét foglalja el
    //: (mérve: `confirmsug` (348,55)–(436,82), `removesel` (439,55)–(527,82),
    //: `moresug` (348,55)–(527,82)) — tehát akkor látszik, amikor nincs mit
    //: jóváhagyni. A két állapot kizárja egymást.
    readonly property bool tovabbiJavaslatLatszik:
        header.personName !== "" && header.suggestionCount === 0

    //: A számos/szám nélküli alak választása egy helyen, hogy minden
    //: fejléc-gomb ugyanúgy viselkedjen.
    function feliratSzammal(alap) {
        return header.selectedCount > 0
            ? alap + " (" + header.selectedCount + ")" : alap
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onSingleTapped: header.contextMenuRequested()
    }
    spacing: 3

    // -- címsor: mappa-ikon + cím (50px behúzás) + jobb-felső szinkron-kapcsoló --
    Item {
        id: titleRow
        Layout.fillWidth: true
        implicitHeight: Math.max(titleClip.height, syncRow.implicitHeight) + 4

        FolderIcon {
            id: folderIcon
            size: 20
            anchors.left: parent.left
            anchors.leftMargin: 8
            anchors.verticalCenter: titleClip.verticalCenter
        }

        // a cím levágó/halványító konténere: bal szél 50px, jobb szél a
        // fejléc szélétől 20px-re (a szinkron-sor előtt) — a `#423`
        // respack-kényszer (`album_title`, `album_title_clip`) tükre
        Item {
            id: titleClip
            objectName: "folderTitleClip"
            x: 50
            y: 2
            width: Math.max(
                0, titleRow.width - 50 - 20 - syncRow.implicitWidth - 8)
            height: titleText.implicitHeight
            clip: true

            Text {
                id: titleText
                objectName: "folderTitleText"
                text: header.folderName
                color: Theme.folderTitle
                font.family: "Georgia"
                font.pointSize: 20
                font.weight: Font.DemiBold
            }

            // halványuló kifutás hosszú mappanévnél — NEM "…" (a Picasa
            // eredeti `title_fade0/1` rétegeinek tükre)
            Rectangle {
                objectName: "folderTitleFade"
                visible: titleText.implicitWidth > titleClip.width
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: 24
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop {
                        position: 0.0
                        color: Qt.rgba(
                            Theme.lightboxBg.r, Theme.lightboxBg.g,
                            Theme.lightboxBg.b, 0.0)
                    }
                    GradientStop { position: 1.0; color: Theme.lightboxBg }
                }
            }
        }

        // jobb-felső: „Szinkronizálás az internettel" + kapcsoló — csak
        // elrendezés, letiltott (#423: funkció nélkül, funkció majd később)
        Row {
            id: syncRow
            objectName: "folderSyncRow"
            anchors.right: parent.right
            anchors.top: parent.top
            spacing: 4
            Text {
                objectName: "folderSyncLabel"
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Sync to the web")
                font.pixelSize: 10
                color: Theme.textGray
            }
            Switch {
                objectName: "folderSyncSwitch"
                anchors.verticalCenter: parent.verticalCenter
                enabled: false
                checked: false
            }
        }
    }

    Text {
        objectName: "folderDateText"
        visible: header.dateText !== ""
        text: header.dateText
        color: Theme.folderDate
        font.family: "Georgia"
        font.pointSize: 14
        Layout.leftMargin: 50
    }

    Item {
        id: gombSor
        Layout.leftMargin: 28
        Layout.topMargin: 4
        Layout.fillWidth: true
        //: a legmagasabb gomb (a kollázs 27) — a sor magassága ennyi
        Layout.preferredHeight: 27
        implicitHeight: 27

        Rectangle {
            id: playGomb
            objectName: "headerPlayButton"
            visible: header.gombLathato(objectName)
            x: header.gombX(objectName)
            anchors.verticalCenter: parent.verticalCenter
            width: 26; height: 22; radius: 3
            color: headerPlayHover.hovered ? "#f0f0ee" : "#ffffff"
            border.color: Theme.chromeBorder
            Text {
                anchors.centerIn: parent
                text: "▸"; color: Theme.picasaGreen; font.pixelSize: 13
            }
            HoverHandler { id: headerPlayHover }
            //: #885: `headerpanel/play` — LENYOMÁSRA indul a diavetítés
            //: (`Property mousedown 1`). A `TapHandler` a felengedést
            //: jelzi, ezért a lenyomás-átmenetre kötjük; a `pressed`
            //: visszaváltása nem sülhet el másodszor.
            TapHandler {
                onPressedChanged: if (pressed) header.playRequested()
            }
        }
        // #1823: eddig ez egy néma díszcsempe volt — se neve, se
        // kezelője. Most a mért `select_star` gomb: a jelenlegi mappa
        // csillagozott képeit jelöli ki.
        PicasaButton {
            id: csillagGomb
            objectName: "headerSelectStarredButton"
            visible: header.gombLathato(objectName)
            x: header.gombX(objectName)
            anchors.verticalCenter: parent.verticalCenter
            height: 22
            //: #885: LENYOMÁSRA sül el — `headerpanel/select_star`
            //: mért `mousedown`-ja. Kijelölést vált, nem művelet.
            lenyomasra: true
            text: header.feliratSzammal("☆")
            Layout.preferredHeight: 22
            ToolTip.text: qsTr("Select starred photos")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: header.selectStarredRequested()
        }
        // #1823: „szerkesztések mentése lemezre" (`save_edits`) — a
        // fejlécről eddig teljesen hiányzott, pedig a művelet megvan
        // (#444). Üres kijelölésnél tiltott: a mentés a KIJELÖLTEKRE hat.
        PicasaButton {
            id: mentesGomb
            objectName: "headerSaveEditsButton"
            visible: header.gombLathato(objectName)
            x: header.gombX(objectName)
            anchors.verticalCenter: parent.verticalCenter
            height: 22
            text: header.feliratSzammal(qsTr("Save"))
            enabled: header.selectedCount > 0
            Layout.preferredHeight: 22
            ToolTip.text: qsTr("Save edited photos to disk")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: header.saveEditsRequested()
        }
        // #1006: `headerpanel/create_collage` — MÉRT 29 × 27
        // (`picasa-create-features.md` 1.10.5).
        //
        // ⚠️ Az eredetiben KÉT panel van: a mappa-fejléc
        // (`headerpanel`) és az ARC-fejléc (`faceheaderpanel`), mindkettőn
        // ugyanez a gomb. A mi felületünkön a személy képei UGYANEBBEN a
        // rácsban, ugyanezzel a fejléccel jelennek meg — nincs külön
        // arc-fejléc. Ez az egy gomb tehát mindkét belépési pontot
        // lefedi; külön arc-fejlécet építeni olyan felületet hozna létre,
        // ami nálunk nem létezik.
        //
        // #2187: ez a döntés maradt — az arc-fejléc SAJÁT vezérlői (a
        // javaslat-munkafolyamat) ezért ugyanebbe a fejlécbe kerültek, a
        // `personName` módjába, nem külön panelbe.
        PicasaButton {
            id: kollazsGomb
            objectName: "headerCollageButton"
            visible: header.gombLathato(objectName)
            x: header.gombX(objectName)
            anchors.verticalCenter: parent.verticalCenter
            //: #885: LENYOMÁSRA sül el — `headerpanel/create_collage`
            //: mért `mousedown`-ja. ⚠️ Nem mond ellent a jegy
            //: táblázatának: ez a gomb a kollázs-PANELT NYITJA MEG
            //: (nézetváltás), a „Kollázs létrehozása" művelet-gomb
            //: a panelen belül marad felengedésre.
            lenyomasra: true
            width: 29; height: 27
            ToolTip.text: qsTr("Create Photo Collage")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: header.collageRequested()
            contentItem: Item {
                Image {
                    objectName: "headerCollageIcon"
                    source: "icons/collage-check.svg"
                    width: 16; height: 16
                    sourceSize.width: 16; sourceSize.height: 16
                    fillMode: Image.PreserveAspectFit
                    anchors.centerIn: parent
                }
            }
        }
        // #2187: a javaslat-munkafolyamat két vezérlője. MÉRT méret
        // mindkettőn 88 × 27 (`respack.yt`); az eredetiben a
        // `confirmsug` és a `confirmsel` UGYANAZON a téglalapon
        // váltakozik — a mérés szerint ugyanaz a kezelő (`0x00602640`),
        // egyetlen logikai argumentummal (`push 1` = mind, `push 0` = a
        // kijelöltek).
        //
        // ⚠️ Ebben a körben csak a TELJES hatókör van bekötve: a
        // kijelölt hatókörhöz a javaslatoknak látszaniuk kell a rácsban,
        // különben a „Jóváhagyás" üres halmazra hatna. A művelet maga
        // (`confirmPersonSuggestions`) mindkettőt tudja.
        //: #1792: a nem testreszabható elemek a négy gomb UTÁN állnak —
        //: a `gombSorVege` a testreszabott sor jobb széle.
        PicasaButton {
            id: jovahagyGomb
            objectName: "headerConfirmSuggestionsButton"
            x: header.gombSorVege
            anchors.verticalCenter: parent.verticalCenter
            visible: header.javaslatokLatszanak
            //: MÉRT felirat (`faceheaderpaneltext.tre:44`): „Confirm all"
            //: — magyarul „Az összes jóváhagyása". A darabszám a
            //: fejléc-gombok szokása szerint zárójelben (#1823).
            text: qsTr("Confirm all") + " (" + header.suggestionCount + ")"
            width: 88; height: 27
            //: MÉRT súgó: „Confirm all suggestions"
            ToolTip.text: qsTr("Confirm all suggestions")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: header.confirmSuggestionsRequested()
        }
        PicasaButton {
            id: elvetGomb
            objectName: "headerRemoveSuggestionsButton"
            x: jovahagyGomb.visible
                ? jovahagyGomb.x + jovahagyGomb.width + header.gombKoz
                : header.gombSorVege
            anchors.verticalCenter: parent.verticalCenter
            visible: header.javaslatokLatszanak
            //: MÉRT felirat (`faceheaderpaneltext.tre:50`): „Remove"
            text: qsTr("Remove")
            width: 88; height: 27
            //: ⚠️ A MÉRT súgó „Remove selected suggestions" — a KIJELÖLT
            //: hatókörről szól, ami nálunk még nincs bekötve (ld. fent).
            //: Amíg a hatókör a teljes, a súgó is azt mondja; a mért
            //: alakra a kijelölt hatókörrel EGYÜTT váltunk, különben a
            //: súgó mást ígérne, mint amit a gomb tesz.
            ToolTip.text: qsTr("Remove all suggestions")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: header.removeSuggestionsRequested()
        }
        //: #2187: „További javaslatok keresése" — a `moresug` mért helyén és
        //: méretében (179 × 27, a jóváhagyás-pár teljes sávja). A művelet a
        //: `FaceScanController.moreSuggestions()`: a javaslat-lépcsőt tízzel
        //: lazítja, és a beállítást SZÁNDÉKOSAN nem írja vissza — az eredeti
        //: `moresug` kezelője (`0x00602890`) sem írja.
        PicasaButton {
            id: tovabbiJavaslatGomb
            objectName: "headerMoreSuggestionsButton"
            x: header.gombSorVege
            anchors.verticalCenter: parent.verticalCenter
            visible: header.tovabbiJavaslatLatszik
            //: MÉRT felirat (`faceheaderpaneltext.tre:53`): „Find more
            //: suggestions" — magyarul „További javaslatok keresése".
            text: qsTr("Find more suggestions")
            width: 179; height: 27
            //: MÉRT súgó ugyanonnan
            ToolTip.text: qsTr("Lower the recognition threshold to get more suggestions")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: header.moreSuggestionsRequested()
        }
        PicasaButton {
            id: feltoltesGomb
            objectName: "headerUploadButton"
            //: #2187: a feltöltés a javaslat-vezérlők UTÁN áll — akármelyik
            //: állapot van érvényben (jóváhagyás-pár VAGY „További
            //: javaslatok"); a kettő kizárja egymást.
            x: elvetGomb.visible
                ? elvetGomb.x + elvetGomb.width + header.gombKoz
                : (jovahagyGomb.visible
                    ? jovahagyGomb.x + jovahagyGomb.width + header.gombKoz
                    : (tovabbiJavaslatGomb.visible
                        ? tovabbiJavaslatGomb.x + tovabbiJavaslatGomb.width
                          + header.gombKoz
                        : header.gombSorVege))
            anchors.verticalCenter: parent.verticalCenter
            height: 22
            text: header.feliratSzammal(qsTr("Upload")) + " ▾"
            enabled: false
            Layout.preferredHeight: 22
        }
    }

    // szerkeszthető leírás-sor — Esc/elfogadás után Qt.binding()-gel újra
    // be kell kötni, ahogy a PhotoViewer captionField-je is (a gépeléskor
    // a Qt eltávolítja a deklaratív kötést a text property-ről). A
    // placeholder-szöveg a mezőre fedve jelenik meg, amíg üres.
    Item {
        Layout.leftMargin: 28
        Layout.topMargin: 6
        Layout.fillWidth: true
        implicitHeight: descriptionField.implicitHeight

        TextInput {
            id: descriptionField
            objectName: "folderDescriptionField"
            anchors.left: parent.left
            anchors.right: parent.right
            text: header.description
            color: Theme.folderDate
            font.pixelSize: Theme.fontSize + 1
            selectByMouse: true

            function rebind() {
                text = Qt.binding(function () { return header.description })
            }

            onAccepted: {
                header.descriptionEdited(text)
                rebind()
                focus = false
            }
            Keys.onEscapePressed: (event) => {
                rebind()
                focus = false
                event.accepted = true
            }
        }
        Text {
            anchors.left: parent.left
            text: qsTr("Add a description")
            color: Theme.addDescription
            font.pixelSize: Theme.fontSize + 1
            font.italic: true
            visible: descriptionField.text.length === 0 && !descriptionField.activeFocus
        }
    }

    // #1792: a testreszabott gombsor segédei.
    //
    // ⚠️ SZÁNDÉKOSAN a gombok UTÁN állnak. A `headerCollageButton` fölötti
    // indoklást egy őr olvassa (#1006), és az a horgony ELSŐ előfordulását
    // keresi — ha a név itt, feljebb is szerepelne, az őr a fájl fejlécét
    // vizsgálná, és némán mást mérne, mint amit állít.
    //: #1792: a testreszabott gombsor — a `gombsav` híd tölti (az
    //: eredetiben a `Preferences\Buttons\UserConfig` és `…\Exclude`
    //: tárolta). Ha a híd nincs (önálló komponens-teszt), a teljes,
    //: alapértelmezett készlet jön — a fejléc próbái így változatlanul
    //: minden gombot megtalálnak.
    readonly property var gombSorrend:
        (typeof gombsav !== "undefined" && gombsav && gombsav.sorrend)
            ? gombsav.sorrend
            : ["headerPlayButton", "headerSelectStarredButton",
               "headerSaveEditsButton", "headerCollageButton"]

    //: Látszik-e ez a gomb? A készleten KÍVÜLI gomb (feltöltés,
    //: javaslat-vezérlők) nem testreszabható, az mindig a saját
    //: feltételét követi.
    function gombLathato(nev) {
        return header.gombSorrend.indexOf(nev) >= 0
    }

    //: #1792: a gomb HELYE a sorban — ebből lesz a megjelenítési
    //: sorrend. ⚠️ `RowLayout`-tal ez nem megoldható: az a gyerekeit a
    //: DEKLARÁCIÓ sorrendjében rakja ki. `Repeater`-rel sem: annak a
    //: delegáltjait a `findChild` nem találja meg, és a fejléc gombjaira
    //: épülő próbák pont azon a néven szólítják meg őket. Ezért marad a
    //: négy gomb a helyén, és a VÍZSZINTES pozíciót számoljuk.
    function gombX(nev, sajatSzelesseg) {
        var helye = header.gombSorrend.indexOf(nev)
        if (helye < 0)
            return 0
        var x = 0
        for (var i = 0; i < helye; ++i)
            x += header.gombSzelessege(header.gombSorrend[i]) + header.gombKoz
        return x
    }

    //: a gombok közti hézag — a korábbi `RowLayout` `spacing`-je
    readonly property int gombKoz: 6

    //: a testreszabott gombsor jobb széle (a további elemek innen
    //: folytatódnak)
    readonly property real gombSorVege: {
        var x = 0
        for (var i = 0; i < header.gombSorrend.length; ++i)
            x += header.gombSzelessege(header.gombSorrend[i]) + header.gombKoz
        return x
    }

    //: A gomb szélessége a sorrend-számításhoz. A `play` és a kollázs
    //: MÉRT, fix méretű; a másik kettő felirat-függő, azt az elemtől
    //: kérdezzük.
    function gombSzelessege(nev) {
        var elem = header.gombElem(nev)
        return elem ? elem.width : 0
    }

    //: azonosító → elem, a szélesség-lekérdezéshez
    function gombElem(nev) {
        switch (nev) {
        case "headerPlayButton": return playGomb
        case "headerSelectStarredButton": return csillagGomb
        case "headerSaveEditsButton": return mentesGomb
        case "headerCollageButton": return kollazsGomb
        }
        return null
    }

}
