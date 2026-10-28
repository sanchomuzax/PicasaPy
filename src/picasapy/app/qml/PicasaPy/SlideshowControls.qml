import QtQuick
import QtQuick.Controls

// A képfelület fölötti vetítővezérlők, felirat és megjelenési időzítő.
Item {
    id: controlsLayer

    property var slideshow: null
    property alias controls: controlsBar
    property alias autoHideTimer: hideTimer

    anchors.fill: parent
    z: 1

    // vezérlő-overlay: egérmozgásra jelenik meg, pár másodperc múlva
    // magától eltűnik (Picasa-minta) — a vetítést nem takarja feleslegesen
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: slideshow.screensaverMode ? Qt.AllButtons : Qt.NoButton
        onPressed: if (slideshow.screensaverMode && slideshow.screensaverInputArmed)
                       slideshow.stop()
        onPositionChanged: {
            if (slideshow.screensaverMode) {
                if (slideshow.screensaverInputArmed) slideshow.stop()
            } else {
                controlsBar.shown = true
                hideTimer.restart()
            }
        }
    }
    // #5649: az eredeti `oneup/auto2` teljes szélességű, 14 px magas
    // kattintósávja a vetítő tetején. Ugyanazt a műveletet hívja, mint a
    // lejátszás gomb; a `MouseArea` átlátszó, a képet nem takarja el.
    MouseArea {
        objectName: "slideshowAuto2Area"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 14
        acceptedButtons: Qt.LeftButton
        onClicked: slideshow.togglePause()
    }
    WheelHandler {
        enabled: slideshow.screensaverMode && slideshow.screensaverInputArmed
        onWheel: slideshow.stop()
    }
    //: #433: a felirat vetítés közben (`captionmode`). A vezérlősáv fölött
    //: ül, hogy a sáv megjelenése ne takarja el.
    Text {
        id: feliratSzoveg
        objectName: "slideshowCaption"
        visible: slideshow.aktualisFelirat.length > 0
        text: slideshow.aktualisFelirat
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 72
        width: parent.width - 96
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        maximumLineCount: 2
        elide: Text.ElideRight
        color: "#ffffff"
        font.pixelSize: Theme.fontSize + 4
        style: Text.Outline
        styleColor: "#000000"
    }

    Timer {
        id: hideTimer
        objectName: "slideshowHideTimer"
        interval: 2500
        //: #2992: a mutató alatt NEM rejtünk el. A lejáró időzítő így nem
        //: kapja el a sávot épp akkor, amikor a felhasználó a gombot
        //: célozza — az újraindítás a `slideshowControlsHover` dolga.
        onTriggered: if (!savLebeges.hovered) controlsBar.shown = false
    }

    Rectangle {
        id: controlsBar
        objectName: "slideshowControls"
        property bool shown: false

        //: ⛔ #2992: a sávnak SAJÁT lebegés-figyelő kell.
        //:
        //: A megjelenítő `MouseArea` a teljes vetítőt fedi, a sáv viszont
        //: UTÁNA van deklarálva, tehát takarja. Amíg a mutató a sávon áll,
        //: a `MouseArea` nem kap `positionChanged`-et — a `hideTimer`
        //: lejár, és a sáv **eltűnik a kéz alól**. A tulajdonos szava a
        //: jegyben: „egérmozgatásra nem jelenik meg a kis lejátszó, ami az
        //: eredetiben ott van, FIXEN" — az „ott van, fixen" épp ezt írja
        //: le: az eredetiben a sáv nem szökik el a mutató elől.
        HoverHandler {
            id: savLebeges
            objectName: "slideshowControlsHover"
            //: amikor a mutató elhagyja a sávot, az elrejtés újraindul —
            //: enélkül a sáv a vetítés végéig kint maradna
            onHoveredChanged: if (!hovered) hideTimer.restart()
        }
        visible: !slideshow.screensaverMode && opacity > 0
        opacity: shown ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 200 } }
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        width: controlsRow.width + 24
        height: 40
        radius: 6
        color: "#2b2b2bd9"

        Row {
            id: controlsRow
            anchors.centerIn: parent
            spacing: 6
            // egységes gombmagasság: a csillag nagyobb glifje (15px) ne
            // növessze meg a saját gombját a többihez képest
            readonly property int buttonHeight: 28

            PicasaButton {
                objectName: "slideshowExitButton"
                text: "✕ " + qsTr("Exit")
                height: controlsRow.buttonHeight
                onClicked: slideshow.stop()
            }
            //: #5541: az eredetiben a `oneup.tre` 75-81. sorában a ◀ és a ▶▶ gombon
            //: `mousedown` van; a kezelőjük a `0x008032e0`. Ezért LENYOMÁSRA léptet,
            //: nyomva tartva nem ismétel.
            PicasaButton {
                objectName: "slideshowTimelineButton"
                text: qsTr("Timeline")
                height: controlsRow.buttonHeight
                visible: slideshow.timelineButtonVisible
                onClicked: slideshow.timelineRequested()
            }
            PicasaButton {
                objectName: "slideshowPrevButton"
                text: "◀"; width: 34
                height: controlsRow.buttonHeight
                lenyomasra: true
                onClicked: slideshow.goBack()
            }
            PicasaButton {
                objectName: "slideshowPlayButton"
                text: slideshow.playing ? "❚❚" : "▶"
                width: 34
                height: controlsRow.buttonHeight
                onClicked: slideshow.togglePause()
            }
            //: #5541: ld. fent, a ◀ gombnál.
            PicasaButton {
                objectName: "slideshowNextButton"
                text: "▶▶"; width: 38
                height: controlsRow.buttonHeight
                lenyomasra: true
                onClicked: slideshow.advance()
            }
            PicasaButton {
                objectName: "slideshowRotateLeftButton"
                text: "↺"; width: 34
                height: controlsRow.buttonHeight
                onClicked: slideshow.rotateCurrent(-1)
            }
            PicasaButton {
                objectName: "slideshowRotateRightButton"
                text: "↻"; width: 34
                height: controlsRow.buttonHeight
                onClicked: slideshow.rotateCurrent(1)
            }
            //: #433: az ÁTMENET-választó a vezérlősávban — az eredetiben is
            //: ott ül (`slideshowctrls/transtype`, a lebegő sáv alján).
            PicasaComboBox {
                objectName: "slideshowTransitionBox"
                height: controlsRow.buttonHeight
                width: 150
                visible: !slideshow.timelineButtonVisible
                //: a lista a képernyő alján álló sáv fölé nyílik
                popup.y: -popup.implicitHeight
                model: slideshow.atmenetek.map(function (a) { return a.nev })
                currentIndex: {
                    for (var i = 0; i < slideshow.atmenetek.length; ++i)
                        if (slideshow.atmenetek[i].kulcs === slideshow.transitionKind)
                            return i
                    return 0
                }
                onActivated: slideshow.transitionPicked(
                    slideshow.atmenetek[currentIndex].kulcs)
            }
            //: #433: a feliratmód körbejáró gombja (felirat → fájlnév →
            //: semmi). Az eredetiben a `captionmode` beállítás; a vetítés
            //: közbeni váltás nálunk kényelmi többlet.
            PicasaButton {
                objectName: "slideshowCaptionModeButton"
                width: 34
                height: controlsRow.buttonHeight
                text: slideshow.captionMode === "caption" ? "T"
                      : (slideshow.captionMode === "filename" ? "F" : "—")
                onClicked: {
                    var i = slideshow.feliratModok.indexOf(slideshow.captionMode)
                    slideshow.captionModePicked(
                        slideshow.feliratModok[(i + 1) % slideshow.feliratModok.length])
                }
            }
            PicasaButton {
                objectName: "slideshowStarButton"
                width: 34
                height: controlsRow.buttonHeight
                onClicked: slideshow.starCurrent()
                contentItem: Text {
                    text: "★"
                    font.pixelSize: 15
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: slideshow.photosModel
                           && (slideshow.photosModel.revision,
                               slideshow.photosModel.starAt(slideshow.currentIndex))
                           //: #3070: a diavetítés a hatókörön KÍVÜL van
                           //: (11.7/3., NY-4), ezért a NYERS tokent olvassa —
                           //: a megjelenítési mód a csillagot sem színezheti át
                           ? Theme.nyers.starYellow : "#ffffff"
                    style: Text.Outline
                    styleColor: "#9a9a9a"
                }
            }

            //: #2992: a DIAIDŐ-blokk — az eredeti sávján `tpslabel`
            //: („Display Time"), `minusone`, `tps` (a szám) és `plusone`.
            //: A tulajdonos jelezte, hogy nálunk nem volt állítható.
            Row {
                objectName: "slideshowTimeBlock"
                spacing: 2
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: qsTr("Display Time")
                    color: "#ffffff"
                    font.pixelSize: Theme.fontSize - 2
                    rightPadding: 4
                }
                PicasaButton {
                    objectName: "slideshowTimeMinus"
                    width: 26
                    height: controlsRow.buttonHeight
                    text: "−"
                    //: #2992: az eredeti `oneup/minusone`-ján ott a
                    //: `Property setautorepeat 1` — a gomb NYOMVA TARTHATÓ
                    //: (`picasa-create-features.md` 2/b). Enélkül 30 mp-re
                    //: állítani 29 kattintás.
                    //: ⚠️ Az ismétlés SEBESSÉGÉT a forrás nem adja meg (csak a
                    //: jelzőt), ezért a Qt alapértelmezése marad — ez nem
                    //: mért érték.
                    autoRepeat: true
                    enabled: slideshow.seconds > 1
                    onClicked: slideshow.secondsChosen(slideshow.seconds - 1)
                }
                Text {
                    objectName: "slideshowTimeValue"
                    anchors.verticalCenter: parent.verticalCenter
                    //: #3574: a mért `oneup/tps` mező 48 képpont széles, de a
                    //: kiírt „másodperc” szó abba csak olvashatatlanul apró
                    //: betűvel férne — a mező a LEGSZÉLESEBB értékhez nő, hogy
                    //: a számváltás ne rángassa a sort
                    TextMetrics {
                        id: diaidoMertek
                        font: diaidoErtek.font
                        text: "99 " + qsTr("seconds")
                    }
                    id: diaidoErtek
                    width: Math.max(48, Math.ceil(diaidoMertek.width) + 4)
                    horizontalAlignment: Text.AlignHCenter
                    //: másodperc-jelölés a szám után (az eredeti `tps` mezője)
                    //: #3574: `OneUpUI::Format` „%1$d %2$s” — a szó kiírva
                    //: #5546: az eredeti `0x0080304c` `cmp esi, 1` után `OneUpUI::second` / `OneUpUI::seconds`
                    text: slideshow.seconds + " " + (slideshow.seconds === 1
                        ? qsTr("second") : qsTr("seconds"))
                    color: "#ffffff"
                    font.pixelSize: Theme.fontSize - 2
                }
                PicasaButton {
                    objectName: "slideshowTimePlus"
                    width: 26
                    height: controlsRow.buttonHeight
                    text: "+"
                    //: #2992: `oneup/plusone` - ugyanaz az auto-ismétlés,
                    //: mint a párjánál (ld. ott az indoklást).
                    autoRepeat: true
                    //: #5544: a felső határ 20 (mérve). Ez a szám a
                    //: `controller.py` SLIDESHOW_SECONDS_MAX konstansával
                    //: egyezik; a vetítő nem lát vezérlőt, ezért nem onnan olvassa.
                    enabled: slideshow.seconds < 20
                    onClicked: slideshow.secondsChosen(slideshow.seconds + 1)
                }
            }
        }
    }
}
