import QtQuick
import QtQuick.Templates as T
import PicasaPy

// A KÖZÖS buboréksúgó (#901) — a felület MIND a 24 `ToolTip`-használata
// ezen az egy komponensen jelenik meg.
//
// ## Miért stílus, és nem külön komponens a hívóknál
//
// Mérve: a 24 fájl MINDEGYIKE a Qt csatolt alakját használja
// (`ToolTip.text` / `ToolTip.visible` / `ToolTip.delay`) — ennek az
// alakja EGYETLEN, megosztott példányt jelenít meg, amit a Quick Controls
// STÍLUSA ad. Ha a hívókat írnánk át saját komponens-példányokra, a
// lebegtetés, a pozicionálás és a kizárólagosság logikáját is mi
// vinnénk — 253 helyen, mérhető haszon nélkül. A stílus-út ugyanazt az
// „egy hely"-et adja, a viselkedés érintése nélkül.
//
// ## Ami MÉRT
//
// * a késleltetés **600 ms** (`ytToolTip` vtábla `0x008909d4` → `+0x74`,
//   küszöb `0x00c7e304` = `0,6000000238418579 s`) — a `Theme.tooltipDelay`
//   ezt hordozza, és a hívók is arra hivatkoznak;
// * hogy az eredeti buborék **saját rajzolású**, nem a Windows
//   `tooltips_class32` vezérlője (a névre nulla előfordulás a binárisban;
//   RTTI: `ytToolTip`, `IToolTip`, `ytHotTip`).
//
// * a KRÓM a tulajdonos képernyőképéről képpontonként leolvasva:
//   kitöltés `#F4F1E5`, keret `#B7B5AC` 1 képpont, derékszögű sarok,
//   fekete szöveg, és árnyék **csak a jobb és az alsó élen** (#901);
// * a betű alapCSALÁDJA `Arial` — a konstruktor-lánc közvetlenül
//   tartalmazza (`0x00a6b6ed` → `0x00c80a64`).
//
// ## Ami NEM mért — és ezért nem is állítás
//
// * **Az árnyék belső mechanizmusa.** A képen ott van, de a binárisban
//   nincs a tooltip példányára kötve: a generikus `useshadow` út
//   paraméterei (`0x00c49618` = 3,0; `0x00c7dcc8` = 0,3) ismertek, a
//   KAPCSOLAT nem. Ezért a mért KÉPI alakot utánozzuk, és a korábbi
//   `CS_DROPSHADOW`-magyarázatot nem állítjuk bizonyítottnak.
// * **A betű pontos képpontmérete.** A bináris csak a családot adja; a
//   12 képpont a MI mércénk marad.
// * **A sötét mód színei.** Az eredetinek nincs sötét témája — ott nincs
//   mit mérni, a `Theme` sötét értéke a mi döntésünk.
T.ToolTip {
    id: sugo
    objectName: "picasaToolTip"

    x: parent ? (parent.width - implicitWidth) / 2 : 0
    y: -implicitHeight - 4

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            contentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             contentHeight + topPadding + bottomPadding)

    //: a MÉRT 600 ms (#901) — a hívók is erre hivatkoznak, itt az
    //: alapértelmezés, hogy egy új hívónak ne kelljen újra megadnia
    delay: Theme.tooltipDelay
    closePolicy: T.Popup.CloseOnEscape | T.Popup.CloseOnPressOutsideParent
                 | T.Popup.CloseOnReleaseOutsideParent

    padding: 6
    topPadding: 3
    bottomPadding: 3

    contentItem: Text {
        objectName: "picasaToolTipText"
        text: sugo.text
        //: a MÉRT alapcsalád `Arial` (`0x00a6b6ed` → `0x00c80a64`).
        //: ⚠️ Ahol nincs telepítve (Linuxon jellemzően nincs), a Qt
        //: metrikailag rokon családra helyettesít — jellemzően Liberation
        //: Sans. Ez SZÁNDÉKOS: a kért család a mért, a helyettesítés a
        //: rendszeré. (A `font.families` listás alak ezen a Qt-n nem
        //: létező tulajdonság — mérve: „Cannot assign to non-existent
        //: property", Qt 6.8.2.)
        font.family: "Arial"
        font.pixelSize: Theme.fontSize
        color: Theme.ink
        wrapMode: Text.WordWrap
    }

    background: Item {
        implicitWidth: keret.implicitWidth
        implicitHeight: keret.implicitHeight

        //: a képen MÉRT árnyék: csak a JOBB és az ALSÓ élen látszik, tehát
        //: egy azonos méretű, eltolt téglalap a buborék ALATT — bal és
        //: felső élen így nem marad belőle semmi
        Rectangle {
            objectName: "picasaToolTipArnyek"
            x: 2
            y: 2
            width: parent.width
            height: parent.height
            color: Qt.rgba(0, 0, 0, 0.3)
        }

        Rectangle {
            id: keret
            objectName: "picasaToolTipHatter"
            anchors.fill: parent
            color: Theme.tooltipBg
            border.color: Theme.tooltipBorder
            border.width: 1
        }
    }
}
