import QtQuick
import QtQuick.Controls

// Picasa-stílusú görgetősáv: keskeny, lapos, szürke fogantyú a Qt
// alap-króm (Fusion) helyett — kézikönyv 06. fejezet, „Görgetősáv
// #CDCDCD — Vezérlők, keretek" (ld. docs/specs/design-guide.md).
//
// Csak a vezérlő maga; a `ScrollBar.vertical: PicasaScrollBar {}` /
// `ScrollBar.horizontal: PicasaScrollBar {}` bekötés az integrátoré
// (Main.qml és a többi meglévő QML forró fájl — #3 issue).
ScrollBar {
    id: control

    //: #857 (ADR-015): az eredeti sávján NÉGY gomb van — a fel/le mellett egy
    //: `prevalbum` és egy `nextalbum` album-ugró (`respack.yt` `scrollart/` +
    //: `throttle/`, mind 16 × 24, mind `m_autorepeat`). A tulajdonos
    //: 2026-09-18-án kérte a két album-ugrót; a fel/le nyílgombok, a lapozó
    //: féltér és a pozíciójelző NEM épül meg, és a sáv 10 képpontos, lapos
    //: stílusa marad (a döntés indoklása a `docs/decisions/`-ben).
    //:
    //: ALAPBÓL KI: a mappafa és a párbeszédek sávján az album-ugrásnak nincs
    //: értelme — ott a mai sáv változatlan marad.
    property bool albumUgras: false
    //: az album-ugró gomb mért magassága (`prevalbum` / `nextalbum`: 16 × 24).
    //: A SZÉLESSÉG a mi sávunké, a MAGASSÁG a mért érték.
    readonly property real albumGombMagassag: 24
    signal elozoAlbum()
    signal kovetkezoAlbum()

    // a sín (background) és a fogantyú (contentItem) közös vastagsága;
    // mindkét irányban ugyanaz az érték — a ScrollBar belső elrendezése
    // a görgetés-tengely mentén automatikusan nyújtja a hosszt.
    readonly property real barThickness: 10
    readonly property real handleMargin: 2

    // #323: a sáv NYUGALMI állapotban is látszik, ha van mit görgetni.
    // Korábban az `active`-hoz volt kötve a láthatóság (Qt-alapértelmezés:
    // csak görgetés/hover közben villan fel), ezért a felhasználó gyakorlatilag
    // soha nem látta a görgetősávot. A Picasa sávja állandóan ott van; ez a
    // kötés csak akkor rejti el, ha nincs mit görgetni (size >= 1) vagy a
    // hívó kifejezetten AlwaysOff-ot kért.
    readonly property bool barVisible:
        policy !== ScrollBar.AlwaysOff
        && (policy === ScrollBar.AlwaysOn || size < 1.0)

    policy: ScrollBar.AsNeeded
    minimumSize: 0.06
    padding: 0
    //: a két gomb a sín KÉT VÉGÉN ül, ezért a fogantyú sávja rövidül —
    //: ugyanúgy, ahogy az eredetiben a sín a gombok között kezdődik
    topPadding: control.albumUgras && !control.horizontal
                ? control.albumGombMagassag : 0
    bottomPadding: control.albumUgras && !control.horizontal
                   ? control.albumGombMagassag : 0

    // #894: a fogantyú a MÉRT átmenetet kapja (`scrollart/base_win`, 15 × 25:
    // VÍZSZINTES átmenet, függőlegesen állandó — tehát egy függőleges sáv
    // hüvelykje):
    //
    //   x0 #B6B6B6 (sötét bal él) · x1 #C7C7C7 → x7 #D9D9D9 → x13 #EDEDED
    //   · x14 #C8C8C8 (jobb él)
    //
    // ⚠️ A Picasa SAJÁT görgetősávot rajzol, és a platformot a RAJZON át
    // követi (külön `_win` és `_mac` réteg, a Mac-változat kisebb). Mi egy
    // rajzot adunk: a windowsos mérést, mert a fejlesztés Linuxon fut, és a
    // `_mac` rétegre nincs platformunk. Ezt itt kimondjuk, hogy ne látsszon
    // kimaradásnak.
    //
    // Az átmenet TENGELYE a sáv irányához igazodik: függőleges sávnál
    // vízszintes (a mérés szerint), vízszintes sávnál elfordítva.
    contentItem: Rectangle {
        //: ⚠️ Az `id` NEM formaság: a `GradientStop`-on belül a `parent` NULL
        //: (a gradiens-lépések nem a Rectangle gyerekei a láthatósági fában),
        //: ezért a `tonus`-t nevén kell hivatkozni. A `huvelyk.tonus` alak a CI
        //: #1260-as QML-szkripthiba-őrén bukott meg — némán annyit jelentett
        //: volna, hogy a hover/press tónus nem érvényesül.
        id: huvelyk
        implicitWidth: control.barThickness - control.handleMargin * 2
        implicitHeight: implicitWidth
        radius: width / 2
        objectName: "picasaScrollThumb"
        //: a nyomott/hover állapot a mért átmenetet SÖTÉTÍTI, nem cseréli —
        //: az eredeti is ugyanazt a rajzot használja minden állapotban
        readonly property real tonus: control.pressed ? 1.25
                                      : (control.hovered ? 1.1 : 1.0)
        gradient: Gradient {
            orientation: control.horizontal
                         ? Gradient.Vertical : Gradient.Horizontal
            GradientStop {
                position: 0.0
                color: Qt.darker(Theme.scrollThumbEdgeDark, huvelyk.tonus)
            }
            GradientStop {
                position: 0.07
                color: Qt.darker(Theme.scrollThumbEdgeSoft, huvelyk.tonus)
            }
            GradientStop {
                position: 0.5
                color: Qt.darker(Theme.scrollThumbMid, huvelyk.tonus)
            }
            GradientStop {
                position: 0.9
                color: Qt.darker(Theme.scrollThumbLight, huvelyk.tonus)
            }
            GradientStop {
                position: 1.0
                color: Qt.darker(Theme.scrollThumbEdgeSoft, huvelyk.tonus)
            }
        }
        opacity: control.barVisible ? 1.0 : 0.0

        Behavior on opacity {
            NumberAnimation { duration: 150 }
        }
    }

    // sín: halványan mindig ott van a fogantyú mögött, interakció közben
    // valamivel erősebb (#323)
    background: Rectangle {
        id: sin
        implicitWidth: control.barThickness
        implicitHeight: control.barThickness
        color: Theme.chromeBg
        opacity: !control.barVisible ? 0.0 : (control.active ? 0.9 : 0.6)

        Behavior on opacity {
            NumberAnimation { duration: 150 }
        }

        //: #857: a két album-ugró gomb. Csak akkor létezik, ha a hívó kérte —
        //: a `Loader` nélkül minden sávon ott ülne két láthatatlan elem.
        Loader {
            active: control.albumUgras && !control.horizontal
            anchors.fill: parent
            sourceComponent: Item {
                AlbumUgroGomb {
                    objectName: "scrollPrevAlbum"
                    anchors { top: parent.top; left: parent.left; right: parent.right }
                    height: control.albumGombMagassag
                    felfele: true
                    //: buboréksúgó — az eredeti `prevalbum` gombja
                    magyarazat: qsTr("Previous album")
                    onAktivalva: control.elozoAlbum()
                }
                AlbumUgroGomb {
                    objectName: "scrollNextAlbum"
                    anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
                    height: control.albumGombMagassag
                    felfele: false
                    //: buboréksúgó — az eredeti `nextalbum` gombja
                    magyarazat: qsTr("Next album")
                    onAktivalva: control.kovetkezoAlbum()
                }
            }
        }
    }
}
