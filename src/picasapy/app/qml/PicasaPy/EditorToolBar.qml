import QtQuick

// #3123: az eszköz-sáv — az Alkalmaz/Mégse gombpár az eredetiben a KÉP
// FÖLÖTT lebeg, nem a bal panelben ül.
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
// ⚠️ Amit ez a komponens MÉG nem visz: a sávban az eredetiben egy
// paraméter-csúszka is ül (`tool_slider_container` 267 × 28, `toolslider/rect`
// 253 × 28, `thumb` 16 × 24) — az eszköz paramétere (pl. a retusálás
// ecsetmérete) ott áll, nem a bal panelben. A csúszka átköltöztetése önálló
// lépés; a mért méretek itt vannak, hogy ne kelljen újramérni.
Item {
    id: sav

    //: melyik eszköz sávja: "crop" · "retouch" · "text" · "redeye" · "" (rejtett)
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

    implicitWidth: 2 * gombSzelesseg + koz
    implicitHeight: gombMagassag
    width: implicitWidth
    height: implicitHeight
    visible: sav.tool !== ""

    //: #3123: a Mégse gombot az Esc is elsüti (`Property escapekey 1`).
    //: A vágásnál NEM: ott a `CropOverlay` maga kezeli az Esc-et, és a
    //: kettős kezelő kétszer mondaná le ugyanazt.
    Shortcut {
        sequence: "Escape"
        enabled: sav.visible && sav.tool !== "crop"
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
