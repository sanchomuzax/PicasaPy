import QtQuick
import QtQuick.Controls

// A Kollázs-panel „Beállítások" lapja (#946, a #920 5/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **4.2** (elemenkénti tábla,
// 17 sor) és **5.** (a képesség-maszk mátrixa). A feliratok forrása a
// `picasa-create-features.md` **1.10.6** — mind az 52 felirat és
// buboréksúgó hivatalos magyarral; az angol itt a `qsTr` forrásszövege, a
// magyar a `picasapy_hu.ts`-ben áll, SZÓ SZERINT úgy, ahogy az eredeti
// erőforrás adja.
//
// ## A lap koordinátarendszere
//
// Minden szám a LAP bal-felső sarkához mért, azaz a `picasa-create-
// features.md` 1.10.2-es abszolút értékéből 13 / 55 levonva. A lap
// tervezői mérete 266 × 351 (spec 4.1) — a `CollagePanel.qml` ekkora
// tartót ad neki, és a tartó geometriája SZERZŐDÉS.
//
// ## A lap egyetlen szabálya
//
//     Ami látszik, azt a képesség-maszk dönti el — nem témánkénti `if`.
//
// A maszk egyetlen forrása a `collage.themes.capabilities_for`, amit a
// vezérlő `collageCapabilities` térképként ad ide. Két csoport — a
// keretsor (0, 67) 266 × 89 és a térköz-csúszka (6, 68) 250 × 81 —
// UGYANAZT a helyet foglalja, tehát ha valaki mégis témánkénti `if`-et
// írna, a két csoport egy elgépelésnél átfedne. Ez a lap legkönnyebben
// elrontható tulajdonsága, és pontosan ezért méri KIRAJZOLT teszt.
//
// ⚠️ Egyetlen kivétel van, és az nem lustaság: a „Beállítás
// képkockaközéppontként" gomb **csak `framegrid`-nél** látszik (spec
// 4.2/17.), és erre NINCS bit a maszkban. A 12. bit közeli, de az a
// `picturegrid`-en is áll — tehát a maszkkal nem fejezhető ki. Amint
// előkerül a valódi bit, ez a hasonlítás cserélhető.
//
// ## Amit ez a lap NEM csinál
//
// Nem tart saját állapotot: minden vezérlő a `controller` property-jét
// olvassa, és minden kattintás a vezérlő slotját hívja. A „nulla térköznél
// bekapcsol az árnyék" szabály (spec 5./1.) ezért is a vezérlőben él
// (`_apply_zero_spacing_shadow_rule`) — itt párhuzamos logika nem
// születhet.
Item {
    id: tab

    // A lap tervezői mérete (spec 4.1).
    implicitWidth: 266
    implicitHeight: 351

    //: A vezérlő (AppController + CollageMixin + CustomAspectRatiosMixin).
    property var controller: null

    // --- A vezérlő állapota, egy helyen kiolvasva ---------------------------

    // Mindegyik kötés kibírja a HIÁNYOS vezérlőt is: a panel váza (#945)
    // olyan próba-vezérlővel is felépül, ami csak két property-t ismer, és a
    // #305 őre a néma „Unable to assign [undefined]" hibát is bukásnak veszi.
    readonly property string theme:
        tab.controller && tab.controller.collageTheme !== undefined
            ? tab.controller.collageTheme : ""

    readonly property string orientation:
        tab.controller && tab.controller.collageOrientation !== undefined
            ? tab.controller.collageOrientation : "landscape"

    readonly property bool shadows:
        tab.controller ? tab.controller.collageShadows === true : false

    readonly property bool captions:
        tab.controller ? tab.controller.collageCaptions === true : false

    readonly property real spacing:
        tab.controller && tab.controller.collageSpacing !== undefined
            ? tab.controller.collageSpacing : 0

    //: A képesség-térkép (`themes.capability_map`). Vezérlő nélkül üres —
    //: ilyenkor a maszkfüggő csoportok rejtve maradnak, mert a lap NEM
    //: találgat téma helyett.
    readonly property var capabilities:
        tab.controller && tab.controller.collageCapabilities
            ? tab.controller.collageCapabilities : ({})

    function can(name) {
        return tab.capabilities[name] === true
    }

    //: A `framegrid` kulcsa — az egyetlen hely, ahol témát hasonlítunk (ld.
    //: a fejléc figyelmeztetését).
    readonly property string frameGridKey: "framegrid"

    //: A lenyílók egymás fölé kerülési sorrendje. A nyitott lenyíló MINDIG
    //: a lap összes többi vezérlője fölé kerül — enélkül a később
    //: deklarált, teljes lapot kitöltő csoportok elnyelnék a kattintást.
    readonly property int zOpen: 300
    readonly property int zClosed: 20

    // --- 1. A téma-választó -------------------------------------------------

    CollageThemePopup {
        id: themePopup
        objectName: "collageThemePopup"
        x: 0
        y: 8
        width: 266
        height: 56
        controller: tab.controller
        z: expanded ? tab.zOpen : tab.zClosed
    }

    // --- 2–3. A keretsor (maszk 9. bitje) -----------------------------------

    CollageBorderPicker {
        objectName: "collageBorderPicker"
        anchors.fill: parent
        visible: tab.can("borders")
        controller: tab.controller
    }

    // --- 4. A térköz-csoport (maszk 10. bitje) ------------------------------

    Item {
        objectName: "collageSpacingGroup"
        x: 6
        y: 68
        width: 250
        height: 81
        visible: tab.can("spacing")

        Text {
            objectName: "collageSpacingLabel"
            // (21, 76) a laphoz mérve
            x: 15
            y: 8
            width: 225
            height: 21
            text: qsTr("Grid Spacing")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }

        // A csúszka 0…1-et ad a vezérlőnek — NEM képpontot (spec 8.1). A
        // képpontra váltás a mag dolga, mert az a lap méretétől függ.
        Slider {
            id: spacingSlider
            objectName: "collageSpacingSlider"
            // (35, 98) a laphoz mérve
            x: 29
            y: 30
            width: 191
            height: 27
            padding: 0
            from: 0.0
            to: 1.0
            value: tab.spacing

            //: A vezérlő az igazságforrás: amikor ő változik, a csúszka
            //: követi. (A `value` kötése az első felhasználói mozgatáskor
            //: elszakadna, ezért kell ez a visszaírás.)
            Connections {
                target: tab.controller
                function onCollageSpacingChanged() {
                    spacingSlider.value = tab.controller.collageSpacing
                }
            }

            //: Csak felhasználói mozgatás után szólunk a vezérlőnek — a
            //: `ready` nélkül a lap felépülése maga küldene egy hívást.
            property bool ready: false
            Component.onCompleted: spacingSlider.ready = true
            onValueChanged: {
                if (!spacingSlider.ready || !tab.controller)
                    return
                if (Math.abs(spacingSlider.value - tab.controller.collageSpacing)
                        > 0.0005)
                    tab.controller.setCollageSpacing(spacingSlider.value)
            }

            background: Rectangle {
                x: 0
                y: (spacingSlider.height - height) / 2
                width: spacingSlider.width
                height: 4
                radius: 2
                color: Theme.trackBg
                border.width: 1
                border.color: Theme.chromeBorder
            }

            handle: Rectangle {
                x: spacingSlider.visualPosition
                   * (spacingSlider.width - width)
                y: (spacingSlider.height - height) / 2
                width: 12
                height: 20
                radius: 2
                color: spacingSlider.pressed ? Theme.buttonBg : Theme.controlBase
                border.width: 1
                border.color: Theme.chromeBorder
            }
        }

        Text {
            objectName: "collageSpacingMinLabel"
            // (35, 125) a laphoz mérve
            x: 29
            y: 57
            width: 83
            height: 14
            text: qsTr("None")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
            verticalAlignment: Text.AlignVCenter
        }

        Text {
            objectName: "collageSpacingMaxLabel"
            // (140, 125) a laphoz mérve
            x: 134
            y: 57
            width: 86
            height: 14
            text: qsTr("Max.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
        }
    }

    // --- 5. Az elválasztó ---------------------------------------------------

    Rectangle {
        objectName: "collageLeftDivider"
        x: 0
        y: 154
        width: 256
        height: 3
        color: Theme.chromeBorder
    }

    // --- 6–10. A háttér-beállítások (maszk 0. bitje) ------------------------

    CollageBackgroundBox {
        id: backgroundBox
        objectName: "collageBackgroundBox"
        anchors.fill: parent
        visible: tab.can("background")
        controller: tab.controller
        // a felugró paletta a lap tetejére nyílik (48, 9) — nyitva a téma-
        // választó fölé kell kerülnie, különben a színmintát az nyelné el
        z: paletteOpen ? tab.zOpen + 1 : 10
    }

    // --- 11–13. Oldalformátum ----------------------------------------------

    Text {
        objectName: "collageFormatTitle"
        x: 3
        y: 235
        width: 239
        height: 15
        text: qsTr("Page Format")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
        verticalAlignment: Text.AlignVCenter
    }

    CollageFormatMenu {
        id: formatMenu
        objectName: "collageFormatMenu"
        x: 3
        y: 255
        width: 243
        height: 21
        controller: tab.controller
        z: expanded ? tab.zOpen : tab.zClosed
        onAddCustomRequested: customAspectDialog.open()
    }

    //: A jelenleg aktív EGYÉNI arány, vagy `null`, ha beépített formátum áll
    //: a menüben. A kulcs alakját a menü adja (`customKey`) — két írásmód ne
    //: szülessen belőle.
    readonly property var activeCustomRatio: {
        const lista = tab.controller
                      && tab.controller.customAspectRatios !== undefined
            ? tab.controller.customAspectRatios : []
        const kulcs = tab.controller
                      && tab.controller.collageFormatKey !== undefined
            ? tab.controller.collageFormatKey : ""
        for (var i = 0; i < lista.length; i++)
            if (formatMenu.customKey(lista[i]) === kulcs)
                return lista[i]
        return null
    }

    // A kuka a lap JOBB széléhez igazodik (`.tre`: `X 1,1,-4`), nem beégetett
    // x-hez — így keskenyebb lapon is a helyén marad.
    Image {
        objectName: "collageDeleteCustomAspect"
        anchors.right: parent.right
        anchors.rightMargin: 4
        y: 259
        width: 14
        height: 14
        sourceSize.width: 14
        sourceSize.height: 14
        source: "icons/collage-trash.svg"
        visible: tab.activeCustomRatio !== null

        HoverHandler { id: trashHover }
        //: `delete_custom_aspect` buboréksúgó.
        ToolTip.text: qsTr("Delete the current aspect ratio")
        ToolTip.visible: trashHover.hovered
        ToolTip.delay: 500

        MouseArea {
            anchors.fill: parent
            onClicked: {
                const arany = tab.activeCustomRatio
                // a MEGLÉVŐ #448-as út; második megvalósítás ne szülessen
                if (arany && tab.controller)
                    tab.controller.deleteCustomAspectRatio(
                        arany.name, arany.width, arany.height)
            }
        }
    }

    // --- 14. Tájolás --------------------------------------------------------

    // A két gomb `checkable: false`, és a `checked` a VEZÉRLŐBŐL számolódik.
    // Checkable gombnál a kattintás maga írná felül a `checked`-et, ezzel
    // elszakítva a kötést — a felület és a vezérlő az első kattintás után
    // szétcsúszhatna. (Ugyanez a megfontolás áll a háttér-rádiógomboknál.)
    Item {
        objectName: "collageOrientation"
        x: 88
        y: 280
        width: 74
        height: 22

        PicasaButton {
            objectName: "collageLandscapeButton"
            x: 0
            y: 0
            width: 37
            height: 22
            padding: 0
            horizontalPadding: 0
            checkable: false
            checked: tab.orientation === "landscape"
            down: checked || pressed
            contentItem: Item {
                Image {
                    // `landscape_icon` (109, 340) a gomb (101, 335)-höz mérve
                    x: 8
                    y: 5
                    width: 23
                    height: 12
                    source: "icons/collage-orient-landscape.svg"
                    sourceSize.width: 23
                    sourceSize.height: 12
                    fillMode: Image.PreserveAspectFit
                }
            }
            //: `landscape` buboréksúgó.
            ToolTip.text: qsTr("Landscape: orient the collage horizontally")
            ToolTip.visible: hovered
            ToolTip.delay: 500
            onClicked: if (tab.controller)
                           tab.controller.setCollageOrientation("landscape")
        }

        PicasaButton {
            objectName: "collagePortraitButton"
            // (125, 280) a laphoz mérve
            x: 37
            y: 0
            width: 37
            height: 22
            padding: 0
            horizontalPadding: 0
            checkable: false
            checked: tab.orientation === "portrait"
            down: checked || pressed
            contentItem: Item {
                Image {
                    // `portrait_icon` (149, 338) a gomb (138, 335)-höz mérve
                    x: 11
                    y: 3
                    width: 11
                    height: 16
                    source: "icons/collage-orient-portrait.svg"
                    sourceSize.width: 11
                    sourceSize.height: 16
                    fillMode: Image.PreserveAspectFit
                }
            }
            //: `portrait` buboréksúgó.
            ToolTip.text: qsTr("Portrait: orient the collage vertically")
            ToolTip.visible: hovered
            ToolTip.delay: 500
            onClicked: if (tab.controller)
                           tab.controller.setCollageOrientation("portrait")
        }
    }

    // --- 15–16. A két jelölőnégyzet -----------------------------------------

    // A `.tre` `m_hit_childlabel`-je szerint a FELIRATRA kattintva is kapcsol,
    // és a felirat KÜLÖN elem (a 14 × 14-es négyzet mellett 109 × 24). A
    // kattintható felület ezért mindkettőn rajta van — enélkül a kód
    // „működne", de a felhasználó hiába kattintana a szövegre.
    component CheckSquare: Item {
        id: doboz
        property bool checked: false
        signal toggled()
        width: 14
        height: 14

        Rectangle {
            anchors.fill: parent
            color: Theme.controlBase
            border.width: 1
            border.color: Theme.chromeBorder
        }

        // ⚠️ A pipa SVG, nem betű és nem `Canvas`.
        //
        // Betű („✓") azért nem, mert hiányzó glifánál néma üres négyzetre
        // váltana. `Canvas` azért nem, mert a rajza külön festési körben
        // készül el: egy korai képernyőkép-mentés ÜRES jelölőnégyzeteket
        // mutatott, mert a festés még nem futott le. A rajz helyessége nem
        // függhet attól, mikor néz rá valaki.
        //
        // Hogy a pipa tényleg LÁTSZIK is, azt a
        // `test_a_bekapcsolt_jelolon_latszik_is_a_pipa` képpont-szintű őre
        // méri — a `checked` property önmagában erről semmit nem mond.
        Image {
            anchors.fill: parent
            visible: doboz.checked
            source: "icons/collage-check.svg"
            sourceSize.width: 14
            sourceSize.height: 14
            fillMode: Image.PreserveAspectFit
        }

        MouseArea {
            anchors.fill: parent
            onClicked: doboz.toggled()
        }
    }

    // ⚠️ A felirat TÖRDEL, nem elidál. A `.tre` 109 × 24-es dobozába az angol
    // („Show Captions") belefér, a hivatalos magyar („Képfeliratok
    // megjelenítése") viszont nem — elidálva a felhasználó néma
    // „Képfeliratok megjelen…"-t látna, és ezt egyetlen teszt sem fogná meg.
    // A szélesség marad 109, hogy a felirat ne csússzon a „Beállítás
    // képkockaközéppontként" gomb alá; a magasság a szöveghez nő.
    component CheckLabel: Text {
        id: felirat
        signal toggled()
        width: 109
        height: Math.max(24, felirat.implicitHeight)
        font.pixelSize: Theme.fontSize
        color: Theme.ink
        wrapMode: Text.Wrap
        verticalAlignment: Text.AlignTop

        MouseArea {
            anchors.fill: parent
            onClicked: felirat.toggled()
        }
    }

    CheckSquare {
        objectName: "collageShadowCheckbox"
        x: 5
        y: 303
        visible: tab.can("shadow")
        checked: tab.shadows
        onToggled: if (tab.controller)
                       tab.controller.setCollageShadows(!tab.shadows)
    }

    CheckLabel {
        objectName: "collageShadowLabel"
        // (22, 302) a laphoz mérve
        x: 22
        y: 302
        visible: tab.can("shadow")
        text: qsTr("Draw Shadows")
        onToggled: if (tab.controller)
                       tab.controller.setCollageShadows(!tab.shadows)
    }

    CheckSquare {
        objectName: "collageCaptionCheckbox"
        x: 4
        y: 328
        checked: tab.captions
        onToggled: if (tab.controller)
                       tab.controller.setCollageCaptions(!tab.captions)
    }

    CheckLabel {
        objectName: "collageCaptionLabel"
        // (22, 327) a laphoz mérve
        x: 22
        y: 327
        text: qsTr("Show Captions")
        //: `caption_checkbox` buboréksúgó.
        ToolTip.text: qsTr("Show picture captions as text on pictures with the "
                           + "Polaroid Camera border")
        ToolTip.visible: captionHover.hovered
        ToolTip.delay: 500
        HoverHandler { id: captionHover }
        onToggled: if (tab.controller)
                       tab.controller.setCollageCaptions(!tab.captions)
    }

    // --- 17. „Beállítás képkockaközéppontként" ------------------------------

    PicasaButton {
        objectName: "collageSetFrameCenter"
        x: 137
        y: 310
        width: 124
        height: 30
        padding: 2
        horizontalPadding: 2
        visible: tab.theme === tab.frameGridKey
        text: qsTr("Set as Frame Center")
        // A hivatalos magyar felirat két sor a 124 képpontos gombon — a
        // tördelést #992 óta a KÖZÖS `PicasaButton` végzi.
        // Kijelölés nélkül a vezérlő adja a „Kötelező a kijelölés" üzenetet
        // (`collageNeedsSelection`) — a lap nem dönti el helyette.
        onClicked: if (tab.controller)
                       tab.controller.setFrameCenterFromSelection()
    }

    // --- Az egyéni arány felvétele: a MEGLÉVŐ #448-as párbeszéd -------------

    AddCustomAspectRatioDialog {
        id: customAspectDialog
        onCreated: function (ujSzelesseg, ujMagassag, ujNev) {
            if (tab.controller)
                tab.controller.addCustomAspectRatio(ujSzelesseg, ujMagassag,
                                                    ujNev)
        }
    }
}
