import QtQuick

// A KIEGYENESÍTÉS (Straighten) átfedése: csúszka + Alkalmaz/Mégse pár a
// kép fölött.
//
// ⭐ #3320 — SZÉTVÁLASZTÁS. A #3123 ide hozta a vágás, a retusálás, a
// szöveg és a vörösszem gombpárját is, `editpanel/tool_container` alapján.
// A #3234 mérése szerint ez a sáv NEM az ő közös sávjuk: az
// `editpanel.tre` a `tool_container`-t a `#---Straighen Overlay---`
// szakaszfejléc alá teszi (`:1038`–`:1052`), és mindegyik eszköznek SAJÁT
// párja van a saját `*_well`-jében (`cropapply: crop_well` `:821`,
// `retouchapply: retouch_well` `:894`, `redeyeapply: redeye_well` `:722`).
// A négy pár ezért visszakerült a saját paneljébe; ez a sáv a
// kiegyenesítésé maradt.
//
// #3123: a pár az eredetiben a KÉP FÖLÖTT lebeg, nem a bal panelben ül.
//
// A mérés (`respack.yt` + `editpanel.tre`, 2026-09-14/16):
//
//   editpanel/tool_container: editpanel/preview   ← a szülő a KÉP
//   m_centerX                                    ← vízszintesen középre
//   YConstraint 1, 1, -10                        ← 10 px-re a kép aljától
//   m_hidden                                     ← alapból rejtett
//
//   layer:editpanel/button(APPLY):  tool_ok      82 × 28
//   layer:editpanel/button(CANCEL): tool_cancel  82 × 28
//     kitöltés #505050, keret #CBCACA, mindkettőn kétszer hat a 229-es alfa
//   #4035 (#69): a látható keret 2 képpont, a lekerekítés sugara 7 képpont
//   #4029 (#69): a hatásos alfa round(229²/255) = 206 (0xCE); renderelt
//   minták: #F0 fölött kitöltés 111, #1E fölött 70, a keret #F0 fölött 210.
//   felirat: m_buttontypecolor3 = FFFFFFFF · CCFFFFFF · FFFFFFFF
//
// ⇒ A gomb rajzának **egyetlen** állapota van (a csomagban nincs `_n`/`_h`/
// `_p` változat), tehát az egér alatt CSAK a felirat halványodik 80%-ra.
// A `Property escapekey 1` a Mégse gombon áll: az Esc azt süti el.
//
// #3234: a sávban egy PARAMÉTER-CSÚSZKA is ül (`tool_slider_container`
// 267 × 28, a kattintható `toolslider/rect` 253 × 28 az x = 7-en,
// `thumb` 16 × 24). A kirajzolt sáv a teljes, 267 px-es konténert kitölti.
//
// ⭐ **A csúszka a KIEGYENESÍTÉS (Straighten) átfedéséé.** Az `editpanel.tre`
// a négy bejegyzést (`toolslider/thumb`, `toolslider/toolslider`,
// `tool_slider_container`, `tool_container`) a `#---Straighen Overlay---`
// szakaszfejléc alá teszi (`:1038`–`:1052`).
//
// ⛔ **A retusálás ecsetmérete NEM ide tartozik.** A #3234 törzse ezt
// feltételezte; a mérés az ellenkezőjét mondja:
// `editpanel/brushslider_container: editpanel/retouch_well` (`:869`), és a
// retusáló kezelője is a `brushslider/scaleslider`-t nevezi meg (`:962`).
// Az ecsetméret marad a bal panelben.
Item {
    id: sav

    // #4639: a súgó a ténylegesen bekötött Mégse-billentyűt olvassa.
    readonly property var keyboardShortcutSequences: [cancelStraightenShortcut.sequence]

    //: melyik eszköz sávja: "tilt" (kiegyenesítés) · "" (rejtett).
    //: #3320: a másik négy eszköz párja a SAJÁT paneljében ül.
    property string tool: ""
    property bool applyEnabled: true
    property bool textEntryHasFocus: false

    signal applyClicked()
    signal cancelClicked()

    //: #4029: a mért 229-es alfa kétszeri hatása `round(229²/255)` = 206.
    //: Így a renderelt kitöltés/keret képpontjai a #69 mintáihoz egyeznek.
    readonly property color kitoltesSzin: "#CE505050"
    readonly property color keretSzin: "#CECBCACA"

    //: MÉRT gombméret (`respack.yt`), és a sáv magassága ugyanennyi
    readonly property int gombSzelesseg: 82
    readonly property int gombMagassag: 28
    //: #4037: a #69 felvételen 5 háttérképpont marad a két gombkeret között.
    readonly property int koz: 5
    //: A job-69 4. képén a sáv és az Alkalmaz között 11 px mérhető; a két
    //: gomb közti, külön mért 5 px-es köz változatlan marad.
    readonly property int csuszkaAlkalmazKoz: 11

    //: #3234: MÉRT csúszka-geometria (`respack.yt`). A kattintható foglalat
    //: 253 px az x = 7-en, a 267 px-es konténerben; a sáv a teljes
    //: konténert tölti ki. A fogantyú 16 × 24 px.
    readonly property int csuszkaKonteterSzelesseg: 267
    readonly property int csuszkaSavSzelesseg: 253
    readonly property int csuszkaSavBehuzas: 7
    readonly property int csuszkaFogantyuSzelesseg: 16
    readonly property int csuszkaFogantyuMagassag: 24

    //: Melyik eszköznek VAN paramétere a sávban. A mérés szerint egy ilyen
    //: van: a kiegyenesítés. A vágásnak, a szövegnek és a vörösszemnek
    //: nincs (a retusálás ecsetmérete a bal panelben áll, ld. fent).
    readonly property bool vanCsuszka: sav.tool === "tilt"

    //: a csúszka tartománya — a hívó tölti (a döntésé −1…1 Picasa-egység)
    property real csuszkaMin: 0
    property real csuszkaMax: 1
    //: olvasható-írható hozzáférés a csúszkához: a hívó a mentett értéket
    //: tölti be rajta, és a próbák is ezen szólítják meg
    property alias csuszkaErtek: toolCsuszka.value
    property alias csuszkaLenyomva: toolCsuszka.pressed
    //: A néző a két gomb együttes befoglaló téglalapját kivágja a rácsból.
    property alias cancelButtonItem: cancelGomb
    property alias applyButtonItem: applyGomb

    //: minden értékváltozás (élő előnézet), illetve az elengedés
    //: (véglegesítés) — a kettő szétválasztása a #72 döntése
    signal csuszkaMozgott(real ertek)
    signal csuszkaElengedve(real ertek)

    implicitWidth: (sav.vanCsuszka
        ? csuszkaKonteterSzelesseg + csuszkaAlkalmazKoz : 0)
        + 2 * gombSzelesseg + koz
    implicitHeight: gombMagassag
    width: implicitWidth
    height: implicitHeight
    visible: sav.tool !== ""

    //: #3123: a Mégse gombot az Esc is elsüti (`Property escapekey 1`).
    //: #3320: a vágás-kivétel INNEN ELTŰNT, mert a vágás gombpárja
    //: visszakerült a saját paneljébe — ez a sáv már csak a
    //: kiegyenesítésé, ott pedig nincs másik Esc-kezelő.
    Shortcut {
        id: cancelStraightenShortcut
        sequence: "Escape"
        enabled: sav.visible && !sav.textEntryHasFocus
        onActivated: sav.cancelClicked()
    }

    //: A gomb szerződése SZÁNDÉKOSAN ugyanaz, mint a panel-gomboké
    //: (`buttonEnabled`, `buttonClicked`, `enabled`): a rájuk épülő működés
    //: és annak ellenőrzése így változatlanul megszólítja őket, csak máshol
    //: találja meg.
    component SavGomb: Rectangle {
        id: gomb
        property string felirat: ""
        property bool buttonEnabled: true
        signal buttonClicked()

        enabled: gomb.buttonEnabled

        width: sav.gombSzelesseg
        height: sav.gombMagassag
        radius: 7
        //: A #4029-es hatásos alfa már a fenti színekben szerepel.
        color: sav.kitoltesSzin
        border.width: 2
        border.color: sav.keretSzin
        opacity: gomb.buttonEnabled ? 1 : 0.55

        Text {
            anchors.centerIn: parent
            text: gomb.felirat
            //: #4052: a #69 felvétel mérése (ugyanazzal a ≥170-es küszöbbel):
            //: az eredeti APPLY 28×7, CANCEL 37×7 px, vonásszélesség ≈2,4 px.
            //: Az OpenSans csak Normal és Bold súlyban van csomagolva: a 12 px
            //: DemiBold(=Bold) 33×9 és +73% tinta (túl nagy), a 10 px Normal
            //: 26×8 és vonás 1,4 px (túl vékony); a 10 px Bold, −0,5 px
            //: betűközzel 29×8 / 36×8 és vonás 2,2 px — ez áll legközelebb.
            font.pixelSize: 10
            font.weight: Font.Bold
            font.letterSpacing: -0.5
            //: a felirat FFFFFFFF, az egér alatt CCFFFFFF (80%)
            color: "#ffffff"
            opacity: terulet.containsMouse && gomb.buttonEnabled ? 0.8 : 1.0
        }

        MouseArea {
            id: terulet
            anchors.fill: parent
            hoverEnabled: true
            enabled: gomb.buttonEnabled
            cursorShape: Qt.PointingHandCursor
            onClicked: gomb.buttonClicked()
        }
    }

    Row {
        anchors.fill: parent
        spacing: sav.koz
        layoutDirection: Qt.LeftToRight

        Item {
            objectName: "toolSliderContainer"
            width: sav.csuszkaKonteterSzelesseg
            height: sav.gombMagassag
            visible: sav.vanCsuszka

            PicasaSlider {
                id: toolCsuszka
                //: a NÉV az eszközt követi (`tiltSlider`) — a mai bekötés
                //: és a rá épülő próbák ezen a néven találják meg
                objectName: sav.tool + "Slider"
                //: #3865/#4058: az eszközsáv (kiegyenesítés) csúszkája a
                //: SAJÁT eszközén léptethető +/−-szal; a #4398 3–5. füles
                //: kapuja a szerkesztőpanel csúszkáira vonatkozik, nem erre.
                keyboardStepEnabled: !sav.textEntryHasFocus
                x: sav.csuszkaSavBehuzas
                width: sav.csuszkaSavSzelesseg
                height: sav.gombMagassag
                anchors.verticalCenter: parent.verticalCenter
                //: a `toolslider` TELJES MAGASSÁGÚ hátteret rajzol (a
                //: `scaleslider` vékony sávjával szemben) — mérve
                grooveThickness: sav.gombMagassag
                //: #4036: ugyanaz a már mért, áttetsző szín, mint a gombokon.
                //: A PicasaSlider más példányai az eredeti témaszínükön maradnak.
                grooveColor: sav.kitoltesSzin
                grooveBorderColor: sav.keretSzin
                grooveBorderWidth: 2
                grooveExtension: sav.csuszkaSavBehuzas
                //: A job-69 4. képének mért sarkai 7,0–7,5 px-es sugarat adnak.
                grooveRadius: 7
                showTicks: false
                handleWidth: sav.csuszkaFogantyuSzelesseg
                handleHeight: sav.csuszkaFogantyuMagassag
                from: sav.csuszkaMin
                to: sav.csuszkaMax
                onValueChanged: sav.csuszkaMozgott(toolCsuszka.value)
                //: #3865: a véglegesítés a KÖZÖS `veglegesult` jelen megy —
                //: az egérelengedéssel és a billentyűs léptetéssel egyaránt
                //: tüzel (a `pressed`-re épülő korábbi kezelő a billentyűt
                //: sosem érte el).
                onVeglegesult: (ertek) => sav.csuszkaElengedve(ertek)
            }
        }

        //: A sor alapköze 5 px, a közbetét 1 px; így a látható rés 11 px,
        //: és a csúszka, az Alkalmaz, valamint a Mégse egész pixelre esik.
        Item {
            objectName: "tiltApplyGapSpacer"
            width: sav.vanCsuszka
                ? sav.csuszkaAlkalmazKoz - 2 * sav.koz : 0
            height: sav.gombMagassag
            visible: sav.vanCsuszka
        }

        //: #4027: balról jobbra Alkalmaz, majd Mégse — ahogy a Picasában.
        SavGomb {
            id: applyGomb
            objectName: sav.tool + "ApplyButton"
            felirat: qsTr("APPLY")
            buttonEnabled: sav.applyEnabled
            onButtonClicked: sav.applyClicked()
        }

        SavGomb {
            id: cancelGomb
            objectName: sav.tool + "CancelButton"
            felirat: qsTr("CANCEL")
            onButtonClicked: sav.cancelClicked()
        }
    }
}
