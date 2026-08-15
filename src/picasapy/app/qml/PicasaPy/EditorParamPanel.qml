import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Az effekt-paraméter alpanel (#316): bármelyik effekt-fülön megnyílhat, és
// az adott fül rácsát fedi el ugyanazon a helyen — a visszatérés ugyanarra
// a fülre történik, mert az `activeTab` változatlan marad.
//
// #464 (ugyanaz a túlcsordulás-osztály, mint az effekt-füleknél): a sok
// paraméteres effektek (pl. Vignetta) alpanelje magasabb lehet a
// rendelkezésre álló helynél — ezért görgethető.
//
// #496: az `EditorPanel.qml`-ből kiemelve, viselkedés-semlegesen. A
// láthatóságot és a horgonyokat — a fülek mintája szerint — a gazda adja
// meg a használat helyén.
Flickable {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    // A csúszka-feliratok fordítása (#316): a `label` a Pythonból
    // (`app/effect_params.py`) angol kulcsszövegként érkezik — a lupdate ezt
    // nem látja, ezért itt statikus `qsTr(...)` hívásokkal soroljuk fel az
    // ÖSSZES lehetséges feliratot; az ismeretlent változatlanul adjuk vissza.
    //
    // #496: ez a segéd ide, az EGYETLEN hívója mellé került (korábban az
    // `EditorPanel.qml`-ben állt, ami a 800 soros korlát fölé nőtt). A gazda
    // vékony `paramLabel()`-je ezt hívja tovább, hogy a meglévő tesztek
    // változatlanul a panelen szólíthassák meg.
    function paramLabel(key) {
        switch (key) {
        case "Amount": return qsTr("Amount")
        case "Saturation": return qsTr("Saturation")
        case "Inner Radius": return qsTr("Inner Radius")
        case "Strength": return qsTr("Strength")
        case "Intensity": return qsTr("Intensity")
        case "Radius": return qsTr("Radius")
        case "Center X": return qsTr("Center X")
        case "Center Y": return qsTr("Center Y")
        case "Size": return qsTr("Size")
        case "Sharpness": return qsTr("Sharpness")
        case "Preserve Color": return qsTr("Preserve Color")
        case "Gradient": return qsTr("Gradient")
        case "Shade": return qsTr("Shade")
        case "Block Size": return qsTr("Block Size")
        case "Blur Radius": return qsTr("Blur Radius")
        case "Brightness": return qsTr("Brightness")
        case "Color Mix": return qsTr("Color Mix")
        case "Edge Strength": return qsTr("Edge Strength")
        case "Posterize": return qsTr("Posterize")
        case "Smoothness": return qsTr("Smoothness")
        case "Width": return qsTr("Width")
        case "Border Width": return qsTr("Border Width")
        case "Angle": return qsTr("Angle")
        case "Line Position": return qsTr("Line Position")
        // #516: a filterdesc-registry.md 4.2 táblázatából átvezetett
        // vezérlők feliratai
        case "Grain": return qsTr("Grain")
        case "Contrast": return qsTr("Contrast")
        case "Bloom": return qsTr("Bloom")
        case "Impact": return qsTr("Impact")
        case "Blend Mode": return qsTr("Blend Mode")
        case "Hue": return qsTr("Hue")
        case "Rotate": return qsTr("Rotate")
        case "Fade": return qsTr("Fade")
        case "Outer Color": return qsTr("Outer Color")
        case "Inner Color": return qsTr("Inner Color")
        case "Outer Thickness": return qsTr("Outer Thickness")
        case "Inner Thickness": return qsTr("Inner Thickness")
        case "Corner Radius": return qsTr("Corner Radius")
        case "Caption Height": return qsTr("Caption Height")
        case "Distance": return qsTr("Distance")
        case "Shadow Color": return qsTr("Shadow Color")
        case "Background Color": return qsTr("Background Color")
        case "Lighten": return qsTr("Lighten")
        // #600: a Picasa saját szótárából (`Picasa3i18n.dll`,
        // `ImageFilters`) átvett feliratok — ld.
        // `docs/specs/picasa-effekt-feliratok.md`
        case "Vignette Color": return qsTr("Vignette Color")
        case "Matte Color": return qsTr("Matte Color")
        case "Number of Colors": return qsTr("Number of Colors")
        case "Detail": return qsTr("Detail")
        case "First Color": return qsTr("First Color")
        case "Second Color": return qsTr("Second Color")
        case "Rounded Corners": return qsTr("Rounded Corners")
        case "Edge Hardness": return qsTr("Edge Hardness")
        // #717: az `ansel`/`tint`/`dir_tint`/`radtint` (és a `finetune*`/
        // `colorfix`) közös natív színkerekének felirata MINDIG „Pick
        // Color" — mérve, nem kitalálva (ld. `effect_params.py`
        // modul-docsztringje)
        case "Pick Color": return qsTr("Pick Color")
        default: return key
        }
    }
    objectName: "editorEffectParamScroll"
    anchors.bottomMargin: 6
    clip: true
    contentWidth: width
    contentHeight: effectParamColumn.implicitHeight + 20
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: PicasaScrollBar {}

    // #700: az Apply/Cancel gomb kör alakú ikonja. Az eredetiben ez két
    // 15×15 képpontos bitkép (`editpanel/ok_icon`, `editpanel/cancel_icon`),
    // tömör kör fehér pipával, illetve fehér X-szel; a színek a
    // kicsomagolt képekből mérve (`docs/specs/ui-audit-editor.md` 7.4).
    //
    // A jelet SZÁNDÉKOSAN nem Unicode-karakter rajzolja: a vágás-panel
    // „✔"/„✘" megoldása betűtípusfüggő, és hiányzó glifánál nyomtalanul
    // eltűnik. Két elforgatott téglalap mindig ugyanazt adja.
    component ActionBadge: Rectangle {
        id: badge

        // igaz = zöld pipa (Alkalmaz), hamis = indigó X (Mégse)
        property bool tick: true

        implicitWidth: 15
        implicitHeight: 15
        radius: 7.5
        antialiasing: true
        color: badge.tick ? "#4e904a" : "#524ba1"

        // a pipa rövid, lefelé tartó szára
        Rectangle {
            visible: badge.tick
            x: 4; y: 7
            width: 3.9; height: 2
            radius: 1
            color: "white"
            antialiasing: true
            transformOrigin: Item.Left
            rotation: 50
        }
        // a pipa hosszú, felfelé tartó szára
        Rectangle {
            visible: badge.tick
            x: 6.5; y: 10
            width: 8.2; height: 2
            radius: 1
            color: "white"
            antialiasing: true
            transformOrigin: Item.Left
            rotation: -52
        }
        // az X két szára
        Rectangle {
            visible: !badge.tick
            anchors.centerIn: parent
            width: 9; height: 2
            radius: 1
            color: "white"
            antialiasing: true
            rotation: 45
        }
        Rectangle {
            visible: !badge.tick
            anchors.centerIn: parent
            width: 9; height: 2
            radius: 1
            color: "white"
            antialiasing: true
            rotation: -45
        }
    }

    ColumnLayout {
        id: effectParamColumn
        objectName: "effectParamColumn"
        opacity: panel.enabled ? 1 : 0.45
        // #700: a tartalom a panel TELJES szélességét kapja. Korábban az
        // oszlopnak nem volt horgonya, ezért a Flickable tartalom-elemében
        // a saját implicit szélességére zsugorodott, és minden a bal
        // szélre tapadt — a bejelentő ezt látta („a bal szélére szorul a
        // területnek"). A többi fül (pl. EditorFinetunePanel) azért volt
        // rendben, mert azoknak a GAZDA adja a bal/jobb horgonyt.
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 10
        spacing: 8

        // #700: a panel címe az effekt EMBERI, lefordított neve — ugyanaz,
        // ami a megnyitó csempén áll (`panel.paramEffectTitle`). Az
        // eredetiben ez az `editpanel/filter_name` réteg: balra igazított,
        // 18 képpontos REGULAR (nem félkövér) szedés a panel hátterén,
        // kiemelt fejléc-sáv nélkül — ld. az audit 7.1 pontját.
        Label {
            objectName: "effectParamTitle"
            Layout.fillWidth: true
            Layout.topMargin: 2
            Layout.bottomMargin: 2
            text: panel.paramEffectTitle
            horizontalAlignment: Text.AlignLeft
            elide: Text.ElideRight
            font.pixelSize: Math.round(Theme.fontSize * 1.5)
            font.bold: false
            color: Theme.textGray
        }

        Repeater {
            objectName: "effectParamRepeater"
            model: panel.paramEffectParams

            // #516: a katalógus 3 vezérlő-fajtát ismer — "slider" (számtar-
            // tomány), "checkbox" (jelölőnégyzet) és "color" (színválasztó,
            // a #450 szöveg-eszköz `TextColorSwatches`-ának mintájára). Egy
            // delegate-en belül mindhárom ág megvan, csak a `kind` szerint
            // látszik az egyik — így a Repeater indexelése (és vele a
            // `panel.updateParamValue(index, …)` pozíció-egyeztetés)
            // változatlan marad, akármilyen a vezérlő-keverék.
            delegate: ColumnLayout {
                id: paramRow
                required property var modelData
                required property int index
                Layout.fillWidth: true
                spacing: 2

                // #650: a `kind` szerinti láthatóság. A delegate mindhárom
                // ágat TARTALMAZZA (ez adja a Repeater stabil indexelését),
                // de egyszerre pontosan EGY látszik. A kötés korábban
                // hiányzott: minden csúszkás paraméter alatt megjelent egy
                // oda nem való jelölőnégyzet ÉS egy színpaletta is — és mivel
                // mindhárom ugyanarra az indexre ír, a színpalettára
                // kattintva egy hex STRING került a numerikus paraméter
                // helyére, egészen a `filters=` láncig.
                //
                // Az ismeretlen/hiányzó `kind` a csúszkára esik vissza: ez a
                // katalógus túlnyomó többsége, és így egy jövőbeli, még nem
                // ismert fajta sem tünteti el a vezérlőt nyomtalanul.
                readonly property string controlKind:
                    paramRow.modelData.kind === "checkbox"
                    || paramRow.modelData.kind === "color"
                        ? paramRow.modelData.kind : "slider"

                // #700: a felirat a csúszka FÖLÖTT, KÖZÉPRE igazítva áll —
                // az eredeti `editlabel1..4` rétegek stílusa (`m_fxlabel2`)
                // kimondottan `textalign center`. A korábbi megoldás a
                // csúszka MELLÉ tette, balra, és jobbról odaírta a nyers
                // értéket is; az eredeti panel teljes rétegleltárában
                // NINCS érték-kijelző (audit 7.2–7.3), ezért az a Label
                // megszűnt — nem elrejtve, hanem elhagyva.
                //
                // A felirat DOBOZA a szövegére zsugorodik, és a doboz kerül
                // középre (`Layout.alignment`) — nem teljes szélességű doboz
                // belsejében igazítjuk a szöveget. Így a középre igazítás a
                // kirajzolt geometriából mérhető: a doboz középpontja a
                // panel középvonalán van. Hosszú felirat a rendelkezésre
                // álló szélességig nőhet és tördelődik.
                Label {
                    objectName: "effectParamLabel" + paramRow.index
                    Layout.fillWidth: false
                    Layout.alignment: Qt.AlignHCenter
                    Layout.maximumWidth: paramRow.width
                    visible: paramRow.controlKind === "slider"
                    text: panel.paramLabel(paramRow.modelData.label)
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    font.pixelSize: Theme.fontSize - 1
                    color: Theme.textGray
                }
                PicasaSlider {
                    id: paramSlider
                    objectName: "effectParamSlider" + paramRow.index
                    visible: paramRow.controlKind === "slider"
                    Layout.fillWidth: true
                    // #700: az eredeti `editslider` arányai — 9 képpontos
                    // sín, 16×26-os ÁLLÓ, enyhén lekerekített fogantyú
                    // (a bitképekből mérve, audit 7.5). A közös
                    // `PicasaSlider` alapértéke (4 px-es sín, 14 px-es kerek
                    // fogantyú) változatlan marad a többi csúszkánál.
                    grooveThickness: 9
                    handleWidth: 16
                    handleHeight: 26
                    handleRadius: 3
                    from: paramRow.modelData.minimum
                    to: paramRow.modelData.maximum
                    stepSize: paramRow.modelData.step
                    value: paramRow.modelData.default
                    // húzás/kattintás közben élő előnézet (#316) — a
                    // programozott kezdőérték-beállítás NEM vált ki `moved`
                    // jelet, csak a valódi felhasználói interakció
                    onMoved: panel.updateParamValue(paramRow.index, paramSlider.value)
                }
                CheckBox {
                    id: paramCheckbox
                    objectName: "effectParamCheckbox" + paramRow.index
                    visible: paramRow.controlKind === "checkbox"
                    text: panel.paramLabel(paramRow.modelData.label)
                    checked: paramRow.modelData.default !== 0
                    onToggled: panel.updateParamValue(paramRow.index, paramCheckbox.checked ? 1 : 0)
                }
                TextColorSwatches {
                    id: paramColorSwatches
                    objectName: "effectParamColor" + paramRow.index
                    visible: paramRow.controlKind === "color"
                    // #305 null-őr: régebbi/fake vezérlők (pl. teszt-dupla)
                    // "color" mező nélküli payloadot is küldhetnek
                    currentColor: paramRow.modelData.color ? paramRow.modelData.color : "#000000"
                    onColorPicked: (hex) => panel.updateParamValue(paramRow.index, hex)
                }
            }
        }

        // #700: a gombsor KÖZÉPRE igazítva, az eredeti ikonjaival. Az
        // eredetiben a két gomb a terület vízszintes közepéhez van kötve,
        // szimmetrikusan ±52 képponttal (`XConstraint 0.5, 0.5, ∓52`) —
        // vagyis nem a panel szélességére feszülnek, hanem középen ülnek,
        // egymástól 104 képpontnyi középpont-távolságra. Innen a 100
        // képpontos gombszélesség és a 4 képpontos köz.
        RowLayout {
            objectName: "effectParamButtonRow"
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 4
            spacing: 4
            PanelButton {
                objectName: "effectParamApplyButton"
                label: qsTr("Apply")
                Layout.fillWidth: false
                Layout.preferredWidth: 100
                onButtonClicked: panel.applyParamPanel()
                ActionBadge {
                    objectName: "effectParamApplyIcon"
                    tick: true
                    anchors.right: parent.right
                    anchors.rightMargin: 9
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            PanelButton {
                objectName: "effectParamCancelButton"
                label: qsTr("Cancel")
                Layout.fillWidth: false
                Layout.preferredWidth: 100
                onButtonClicked: panel.cancelParamPanel()
                ActionBadge {
                    objectName: "effectParamCancelIcon"
                    tick: false
                    anchors.right: parent.right
                    anchors.rightMargin: 9
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}
