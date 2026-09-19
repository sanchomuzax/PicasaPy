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
//     kitöltés #505050, alfa 229 · keret #CBCACA, alfa 229
//   felirat: m_buttontypecolor3 = FFFFFFFF · CCFFFFFF · FFFFFFFF
//
// ⇒ A gomb rajzának **egyetlen** állapota van (a csomagban nincs `_n`/`_h`/
// `_p` változat), tehát az egér alatt CSAK a felirat halványodik 80%-ra.
// A `Property escapekey 1` a Mégse gombon áll: az Esc azt süti el.
//
// #3234: a sávban egy PARAMÉTER-CSÚSZKA is ül (`tool_slider_container`
// 267 × 28, `toolslider/rect` 253 × 28 az x = 7-en, `thumb` 16 × 24).
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

    //: melyik eszköz sávja: "tilt" (kiegyenesítés) · "" (rejtett).
    //: #3320: a másik négy eszköz párja a SAJÁT paneljében ül.
    property string tool: ""
    property bool applyEnabled: true

    signal applyClicked()
    signal cancelClicked()

    //: MÉRT kitöltés és keret (`respack.yt`, alfa 229 = 0xE5). Itt, egy
    //: helyen — a gomb ezekre hivatkozik, és a próba is ezeket olvassa (a
    //: `border.color` a QObject-property-n nem olvasható ki).
    readonly property color kitoltesSzin: "#E5505050"
    readonly property color keretSzin: "#E5CBCACA"

    //: MÉRT gombméret (`respack.yt`), és a sáv magassága ugyanennyi
    readonly property int gombSzelesseg: 82
    readonly property int gombMagassag: 28
    //: a két gomb közti köz — az eredetiben a jobb szélhez igazodnak,
    //: egymás mellett; a rajzuk közt 4 képpont marad
    readonly property int koz: 4

    //: #3234: MÉRT csúszka-geometria (`respack.yt`). A konténer 267, a
    //: sáv 253 az x = 7-en (a két oldalon 7-7 képpont marad), a fogantyú
    //: 16 × 24 — a `toolslider` saját fogantyú-mérete, nem a többi csúszkáé.
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

    //: minden értékváltozás (élő előnézet), illetve az elengedés
    //: (véglegesítés) — a kettő szétválasztása a #72 döntése
    signal csuszkaMozgott(real ertek)
    signal csuszkaElengedve(real ertek)

    implicitWidth: (sav.vanCsuszka ? csuszkaKonteterSzelesseg + koz : 0)
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
        sequence: "Escape"
        enabled: sav.visible
        onActivated: sav.cancelClicked()
    }

    //: A gomb szerződése SZÁNDÉKOSAN ugyanaz, mint a panel-gomboké
    //: (`buttonEnabled`, `buttonClicked`, `enabled`): a rájuk épülő működés
    //: és annak ellenőrzése így változatlanul megszólítja őket, csak máshol
    //: találja meg.
    component SavGomb: Rectangle {
        id: gomb
        property string felirat: ""
        //: igaz = pipa (Alkalmaz), hamis = X (Mégse)
        property bool pipa: true
        property bool buttonEnabled: true
        signal buttonClicked()

        enabled: gomb.buttonEnabled

        width: sav.gombSzelesseg
        height: sav.gombMagassag
        radius: 2
        //: MÉRT kitöltés és keret — alfa 229 (0xE5)
        color: sav.kitoltesSzin
        border.width: 1
        border.color: sav.keretSzin
        opacity: gomb.buttonEnabled ? 1 : 0.55

        Text {
            anchors.centerIn: parent
            text: gomb.felirat
            font.pixelSize: Theme.fontSize
            //: a felirat FFFFFFFF, az egér alatt CCFFFFFF (80%)
            color: "#ffffff"
            opacity: terulet.containsMouse && gomb.buttonEnabled ? 0.8 : 1.0
        }

        //: #710: a pipa/X a KÖZÖS rajzolt jel (`EditorActionBadge`), a gomb
        //: jobb szélétől 9 képpontra (audit 7.4) — nem Unicode-glif, mert az
        //: betűtípusfüggő, és hiányzó glifnél NYOMTALANUL eltűnik. A jel a
        //: párral együtt költözött ide a panelekből (#3123).
        EditorActionBadge {
            tick: gomb.pipa
            anchors.right: parent.right
            anchors.rightMargin: 9
            anchors.verticalCenter: parent.verticalCenter
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

        //: #3234: a csúszka BALRA áll, a gombok jobbra (`m_offsetLTR` a
        //: konténeren, `m_offsetR` a gombokon).
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
                x: sav.csuszkaSavBehuzas
                width: sav.csuszkaSavSzelesseg
                height: sav.gombMagassag
                anchors.verticalCenter: parent.verticalCenter
                //: a `toolslider` TELJES MAGASSÁGÚ hátteret rajzol (a
                //: `scaleslider` vékony sávjával szemben) — mérve
                grooveThickness: sav.gombMagassag
                handleWidth: sav.csuszkaFogantyuSzelesseg
                handleHeight: sav.csuszkaFogantyuMagassag
                from: sav.csuszkaMin
                to: sav.csuszkaMax
                onValueChanged: sav.csuszkaMozgott(toolCsuszka.value)
                onPressedChanged: if (!toolCsuszka.pressed)
                                      sav.csuszkaElengedve(toolCsuszka.value)
            }
        }

        SavGomb {
            objectName: sav.tool + "CancelButton"
            felirat: qsTr("Cancel")
            pipa: false
            onButtonClicked: sav.cancelClicked()
        }
        SavGomb {
            objectName: sav.tool + "ApplyButton"
            felirat: qsTr("Apply")
            buttonEnabled: sav.applyEnabled
            onButtonClicked: sav.applyClicked()
        }
    }
}
