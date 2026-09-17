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
// ## Ami NEM mért — és ezért nem is utánzás
//
// A buborék tényleges RAJZA (háttérszín, keret, árnyék, betűméret): a
// `respack.yt`-ben nincs tooltip-réteg, tehát kódból rajzolódik, és a
// konstansai nincsenek kiolvasva. Amíg ez így van, a saját
// `Theme`-tokenjeinket használjuk — ugyanazokat, amikkel a többi krómunk
// rajzolódik. **Ez a mi döntésünk, nem a Picasa mérése.** Ha a rajz egyszer
// kiolvasható lesz, EBBEN a fájlban kell átírni; a #901 emiatt marad nyitva.
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
        font.pixelSize: Theme.fontSize
        color: Theme.ink
        wrapMode: Text.WordWrap
    }

    background: Rectangle {
        objectName: "picasaToolTipHatter"
        color: Theme.panelBg
        border.color: Theme.chromeBorder
        border.width: 1
    }
}
