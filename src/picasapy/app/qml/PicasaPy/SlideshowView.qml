import QtQuick
import QtQuick.Controls

// Diavetítés (#8) — a Picasa Ctrl+4-es teljes képernyős vetítése.
// Időzített léptetés (videókat kihagyva, körbefordulással), szóköz =
// szünet, Esc = kilépés, nyilak = kézi léptetés, Ctrl+R / Ctrl+Shift+R =
// forgatás vetítés közben. A léptetés-logika a controllertől független
// (csak a photosModel-t használja); a csillag/forgatás műveleteket
// jelekkel kéri — a bekötés a Main.qml dolga.
Rectangle {
    id: show
    color: "#000000"
    visible: false

    property var photosModel: null
    // #1640: az AKTÍV megjelenítési mód — a vetített kép URL-jének valódi
    // argumentuma (`displayUrlAt(index, mód)`). A hívó (Main.qml) köti a
    // `controller.displayMode`-hoz; így a kötés módváltáskor újraértékelődik.
    // Eldobott referenciával (`(controller.displayMode, url)`) MÉRVE nem
    // működött: a dia a nyers fájlnál maradt.
    property string displayMode: ""
    property int currentIndex: -1
    //: #2992: a diaidő MÁSODPERCBEN, a sáv ± gombjaival állítható
    //: (`tpslabel`/`minusone`/`tps`/`plusone`). Az alapérték 3 — mérve
    //: (`SlideshowEffectTime`, `0x007facd3`). A hívó a vezérlőhöz köti,
    //: hogy megmaradjon; kötés nélkül a mért alapérték marad.
    property int seconds: 3
    readonly property int intervalMs: Math.max(1, show.seconds) * 1000
    property bool playing: false

    //: #433: az ÁTMENET a diák között. Az eredeti diavetítése ugyanazt a
    //: 18-as készletet használja, mint a filmkészítő (`transtype`,
    //: `picasa-create-features.md` 2.1) — ebből az az öt van meg, amelyik a
    //: Picasa jellegzetes érzetét adja; a maradék 13 a filmkészítővel
    //: együtt jön (#432). A választó csak azt sorolja fel, ami MŰKÖDIK.
    //: A feliratok az eredeti HIVATALOS magyar szövegei
    //: (`CTransitions::*`, `picasa-create-features.md` 2.1): Kivágás ·
    //: Szétoszlás · Szétoszlás feketén át · Szétoszlás fehéren át ·
    //: Pásztázás és nagyítás — nem a mi fordításunk.
    readonly property var atmenetek: [
        { kulcs: "cut", nev: qsTr("Cut") },
        { kulcs: "dissolve", nev: qsTr("Dissolve") },
        { kulcs: "dissolveblack", nev: qsTr("Dissolve through black") },
        { kulcs: "dissolvewhite", nev: qsTr("Dissolve through white") },
        { kulcs: "kenburns", nev: qsTr("Pan and Zoom") }
    ]
    property string transitionKind: "dissolve"
    //: #2992: a diaidő a sáv ± gombjairól a HÍVÓNAK megy (Main.qml →
    //: vezérlő), hogy megmaradjon — a vetítő maga nem ír beállítást. Az
    //: átmenet és a feliratmód ugyanezt az utat járja (`transitionPicked`,
    //: `captionModePicked`).
    signal secondsChosen(int masodperc)
    //: az átmenet hossza (`SlideshowEffectTime`) — a dia-időnél rövidebb
    property int transitionMs: 700
    //: #433: a felirat megjelenítési módja vetítés közben (`captionmode`):
    //: a felirat, a fájlnév, vagy semmi — ugyanaz a hármas, mint a
    //: nyomtatás-opciókban.
    readonly property var feliratModok: ["caption", "filename", "none"]
    property string captionMode: "caption"

    //: a VETÍTETT felirat — a mód szerint felirat, fájlnév vagy üres
    readonly property string aktualisFelirat: {
        if (!show.photosModel || show.currentIndex < 0) return ""
        if (show.captionMode === "none") return ""
        show.photosModel.revision  // a kötés kövesse a szerkesztést
        if (show.captionMode === "filename") {
            var ut = show.photosModel.filePathAt(show.currentIndex)
            var perjel = ut.lastIndexOf("/")
            return perjel >= 0 ? ut.substring(perjel + 1) : ut
        }
        return show.photosModel.captionAt(show.currentIndex)
    }
    signal closed()
    signal starToggled(int index)
    signal rotateRequested(int index, int delta)
    //: #433: a választó nem ír közvetlenül a beállításba — a gazda dönti el,
    //: hova kerül (a `starToggled`/`rotateRequested` mintája).
    signal transitionPicked(string kulcs)
    signal captionModePicked(string mod)

    function count() {
        return photosModel ? photosModel.rowCount() : 0
    }

    // a következő FOTÓ indexe (a videókat kihagyjuk, #8/#14); -1, ha nincs
    function nextPhotoIndex(fromIndex, step) {
        var n = count()
        if (n === 0) return -1
        var idx = fromIndex
        for (var i = 0; i < n; ++i) {
            idx = ((idx + step) % n + n) % n
            if (!photosModel.isVideoAt(idx)) return idx
        }
        return -1
    }

    // az induló index fotóra igazítása (videón álló kijelölésről indítva
    // a következő fotóra ugrunk)
    function clampToPhoto(index) {
        if (photosModel && index >= 0 && index < count()
                && !photosModel.isVideoAt(index))
            return index
        return nextPhotoIndex(index >= 0 ? index : -1, 1)
    }

    function start(index) {
        var target = clampToPhoto(index)
        if (target < 0) return   // nincs vetíthető fotó
        currentIndex = target
        playing = true
        visible = true
        forceActiveFocus()
    }

    function stop() {
        playing = false
        visible = false
        show.closed()
    }

    function advance() {
        var target = nextPhotoIndex(currentIndex, 1)
        if (target < 0) { stop(); return }
        currentIndex = target
    }

    function goBack() {
        var target = nextPhotoIndex(currentIndex, -1)
        if (target >= 0) currentIndex = target
    }

    //: #433: a váltás pillanatában a `slide.source` MÉG a kimenő kép URL-je
    //: (a kötés csak a kezelő után fordul át) — ezt adjuk az áttűnésnek.
    //:
    //: ⚠️ #3018 — MÉRVE, és ez volt a hiba. Korábban egy külön `elozoUrl`
    //: tárolón át ment, és EGY LÉPÉSSEL eltolódott: az áttűnés a KÉT
    //: lépéssel korábbi képet mutatta. A tulajdonos ezt látta „bevillanó
    //: idegen képként". A mérés (három kép, két váltás): a második
    //: áttűnés kimenő képe az ELSŐ kép volt, pedig a MÁSODIKAT nézte.
    onCurrentIndexChanged: {
        var kimeno = slide.source
        if (show.visible && kimeno !== "")
            show._atmenetIndit(kimeno)
    }

    function togglePause() { playing = !playing }
    function starCurrent() { show.starToggled(currentIndex) }
    function rotateCurrent(delta) { show.rotateRequested(currentIndex, delta) }

    //: #433: az ÁTMENET motorja. A kimenő képet egy második `Image` tartja
    //: (`slideshowPrevImage`), a fekete/fehér áttűnést pedig egy fátyol —
    //: így a négy átmenet ugyanabból a két elemből épül, elágazás nélkül a
    //: rajzoló oldalon.
    //:
    //: ⚠️ A `cut` nem „nincs átmenet": az eredeti készletben SAJÁT tétel
    //: (`transtype` 1. eleme), ezért a választóban is szerepel — a
    //: viselkedése nulla hosszú áttűnés.
    //: #3023: a kimenő másolat GEOMETRIÁJA is a látott diáé. A tulajdonos
    //: jelentése: „az éppen eltűnő kép egy picit kisebb lesz, emiatt ugrálás
    //: hatás van" — a másolat ugyanis alapméreten (`scale` 1,0, elfordulás
    //: nélkül) jelent meg, tehát a váltás pillanatában visszaugrott.
    //:
    //: A kötések itt MÉG a kimenő diáé (ugyanaz a lusta újraértékelés, amin
    //: a #3018 kimenő URL-je is múlik), ezért a dia élő értékeit másoljuk.
    function _geometriatAtvesz() {
        elozoSlide.width = slide.width
        elozoSlide.height = slide.height
        elozoSlide.rotation = slide.rotation
        elozoSlide.scale = slide.scale
    }

    function _atmenetIndit(elozoUrl) {
        atmenetAnimacio.stop()
        show._geometriatAtvesz()
        //: a bejövő dia a pásztázás ELEJÉRŐL induljon: az előző dia
        //: nagyítása a másolaton él tovább, a diát visszaállítjuk
        slide.scale = 1.0
        if (show.transitionKind === "kenburns")
            kenBurns.restart()
        if (show.transitionKind === "cut" || !elozoUrl) {
            elozoSlide.opacity = 0
            slide.opacity = 1
            fatyol.opacity = 0
            return
        }
        elozoSlide.source = elozoUrl
        elozoSlide.opacity = 1
        slide.opacity = show.transitionKind === "dissolve" ? 0 : 1
        fatyol.color = show.transitionKind === "dissolvewhite"
            ? "#ffffff" : "#000000"
        fatyol.opacity = 0
        atmenetAnimacio.start()
    }

    SequentialAnimation {
        id: atmenetAnimacio
        objectName: "slideshowTransition"
        //: az egyszerű áttűnés PÁRHUZAMOS (a kimenő halványul, a bejövő
        //: erősödik), a fekete/fehér áttűnés SOROS (előbb a fátyol be, utána
        //: ki) — ezért van két, egymást kizáró szakasz.
        ParallelAnimation {
            NumberAnimation {
                target: elozoSlide; property: "opacity"; to: 0
                duration: show.transitionKind === "dissolve"
                          ? show.transitionMs : show.transitionMs / 2
            }
            NumberAnimation {
                target: slide; property: "opacity"; to: 1
                duration: show.transitionKind === "dissolve"
                          ? show.transitionMs : 1
            }
            NumberAnimation {
                target: fatyol; property: "opacity"
                to: show.transitionKind === "dissolve" ? 0 : 1
                duration: show.transitionKind === "dissolve"
                          ? 1 : show.transitionMs / 2
            }
        }
        NumberAnimation {
            target: fatyol; property: "opacity"; to: 0
            duration: show.transitionKind === "dissolve"
                      ? 1 : show.transitionMs / 2
        }
    }

    Timer {
        id: stepTimer
        objectName: "slideshowTimer"
        interval: show.intervalMs
        repeat: true
        running: show.visible && show.playing
        onTriggered: show.advance()
    }

    Keys.onEscapePressed: show.stop()
    Keys.onSpacePressed: show.togglePause()
    Keys.onRightPressed: show.advance()
    Keys.onReturnPressed: show.advance()
    Keys.onLeftPressed: show.goBack()
    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_R
                && (event.modifiers & Qt.ControlModifier)) {
            show.rotateCurrent(
                (event.modifiers & Qt.ShiftModifier) ? -1 : 1)
            event.accepted = true
        }
    }

    //: #433: a KIMENŐ dia — az átmenet alatt ez halványul el. A fő kép
    //: ALATT rajzolódik (előbb szerepel), tehát az áttűnés végén a bejövő
    //: kép van fölül.
    Image {
        id: elozoSlide
        objectName: "slideshowPrevImage"
        anchors.centerIn: parent
        //: a méretet/elfordulást a váltáskor a `_geometriatAtvesz` írja —
        //: ezek csak a kezdőértékek (első dia, még nincs mit másolni)
        width: parent.width
        height: parent.height
        opacity: 0
        fillMode: Image.PreserveAspectFit
        asynchronous: false
        autoTransform: true
        sourceSize.width: 2560
    }

    Image {
        id: slide
        objectName: "slideshowImage"
        // az ini-forgatást a nézővel azonos módon követi (revision-kötés)
        readonly property int iniSteps: show.photosModel
            ? (show.photosModel.revision,
               show.photosModel.rotateAt(show.currentIndex))
            : 0
        anchors.centerIn: parent
        width: iniSteps % 2 ? parent.height : parent.width
        height: iniSteps % 2 ? parent.width : parent.height
        rotation: iniSteps * 90
        // #1640: a megjelenítési mód (Projektor mód stb.) a NYERS fájl
        // URL-jén nem látszik — a `displayUrlAt` aktív módnál a
        // `displayphoto` szolgáltatóra vált, mód nélkül a sima file://-t adja
        // vissza.
        //
        // ⚠️ A mód VALÓDI ARGUMENTUM, nem eldobott referencia. Az első
        // változat `(controller.displayMode, …)` alakú vessző-kifejezés volt,
        // és MÉRVE nem hozott létre kötés-függőséget: módváltás után a dia
        // URL-je a nyers fájlé maradt, a mód némán elveszett.
        source: show.visible && show.photosModel && show.currentIndex >= 0
                ? show.photosModel.displayUrlAt(
                      show.currentIndex, show.displayMode)
                : ""
        fillMode: Image.PreserveAspectFit
        asynchronous: Qt.platform.pluginName !== "offscreen"
        autoTransform: true
        sourceSize.width: 2560

        //: #433 „Pan and Zoom" (`kenburns`): a dia a tartózkodása alatt
        //: LASSAN nagyít. Nem átmenet, hanem a diára rakott mozgás — ezért
        //: a dia-időhöz kötött, nem az átmenet-hosszhoz.
        NumberAnimation on scale {
            id: kenBurns
            objectName: "slideshowKenBurns"
            running: show.visible && show.transitionKind === "kenburns"
                     && show.currentIndex >= 0
            from: 1.0
            to: 1.08
            duration: Math.max(show.intervalMs, 1)
        }
        //: a nagyítás NEM ragadhat be: átmenet-váltáskor visszaáll
        onScaleChanged: if (show.transitionKind !== "kenburns" && scale !== 1.0)
                            scale = 1.0
    }

    //: #433: az áttűnés FÁTYLA (fekete vagy fehér) — a `dissolveblack` és a
    //: `dissolvewhite` ezen megy át. A diák FÖLÖTT, a vezérlősáv ALATT.
    Rectangle {
        id: fatyol
        objectName: "slideshowVeil"
        anchors.fill: parent
        color: "#000000"
        opacity: 0
        visible: opacity > 0
    }

    // elő-betöltés a következő fotóra (DoD): mire a timer lép, a kép
    // már dekódolva van
    Image {
        visible: false
        // #1640: az elő-betöltés is a mód-tudatos URL-t kérje — különben a
        // következő dia egy pillanatra a festetlen képet villantaná
        source: show.visible && show.photosModel
                ? show.photosModel.displayUrlAt(
                      show.nextPhotoIndex(show.currentIndex, 1), show.displayMode)
                : ""
        asynchronous: Qt.platform.pluginName !== "offscreen"
        autoTransform: true
        sourceSize.width: 2560
    }

    // vezérlő-overlay: egérmozgásra jelenik meg, pár másodperc múlva
    // magától eltűnik (Picasa-minta) — a vetítést nem takarja feleslegesen
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        onPositionChanged: {
            controlsBar.shown = true
            hideTimer.restart()
        }
    }
    //: #433: a felirat vetítés közben (`captionmode`). A vezérlősáv fölött
    //: ül, hogy a sáv megjelenése ne takarja el.
    Text {
        id: feliratSzoveg
        objectName: "slideshowCaption"
        visible: show.aktualisFelirat.length > 0
        text: show.aktualisFelirat
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
        interval: 2500
        onTriggered: controlsBar.shown = false
    }

    Rectangle {
        id: controlsBar
        objectName: "slideshowControls"
        property bool shown: false
        visible: opacity > 0
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
                onClicked: show.stop()
            }
            PicasaButton {
                text: "◀"; width: 34
                height: controlsRow.buttonHeight
                onClicked: show.goBack()
            }
            PicasaButton {
                objectName: "slideshowPlayButton"
                text: show.playing ? "❚❚" : "▶"
                width: 34
                height: controlsRow.buttonHeight
                onClicked: show.togglePause()
            }
            PicasaButton {
                text: "▶▶"; width: 38
                height: controlsRow.buttonHeight
                onClicked: show.advance()
            }
            PicasaButton {
                text: "↺"; width: 34
                height: controlsRow.buttonHeight
                onClicked: show.rotateCurrent(-1)
            }
            PicasaButton {
                text: "↻"; width: 34
                height: controlsRow.buttonHeight
                onClicked: show.rotateCurrent(1)
            }
            //: #433: az ÁTMENET-választó a vezérlősávban — az eredetiben is
            //: ott ül (`slideshowctrls/transtype`, a lebegő sáv alján).
            PicasaComboBox {
                objectName: "slideshowTransitionBox"
                height: controlsRow.buttonHeight
                width: 150
                model: show.atmenetek.map(function (a) { return a.nev })
                currentIndex: {
                    for (var i = 0; i < show.atmenetek.length; ++i)
                        if (show.atmenetek[i].kulcs === show.transitionKind)
                            return i
                    return 0
                }
                onActivated: show.transitionPicked(
                    show.atmenetek[currentIndex].kulcs)
            }
            //: #433: a feliratmód körbejáró gombja (felirat → fájlnév →
            //: semmi). Az eredetiben a `captionmode` beállítás; a vetítés
            //: közbeni váltás nálunk kényelmi többlet.
            PicasaButton {
                objectName: "slideshowCaptionModeButton"
                width: 34
                height: controlsRow.buttonHeight
                text: show.captionMode === "caption" ? "T"
                      : (show.captionMode === "filename" ? "F" : "—")
                onClicked: {
                    var i = show.feliratModok.indexOf(show.captionMode)
                    show.captionModePicked(
                        show.feliratModok[(i + 1) % show.feliratModok.length])
                }
            }
            PicasaButton {
                objectName: "slideshowStarButton"
                width: 34
                height: controlsRow.buttonHeight
                onClicked: show.starCurrent()
                contentItem: Text {
                    text: "★"
                    font.pixelSize: 15
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: show.photosModel
                           && (show.photosModel.revision,
                               show.photosModel.starAt(show.currentIndex))
                           ? Theme.starYellow : "#ffffff"
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
                    enabled: show.seconds > 1
                    onClicked: show.secondsChosen(show.seconds - 1)
                }
                Text {
                    objectName: "slideshowTimeValue"
                    anchors.verticalCenter: parent.verticalCenter
                    width: 34
                    horizontalAlignment: Text.AlignHCenter
                    //: másodperc-jelölés a szám után (az eredeti `tps` mezője)
                    text: show.seconds + qsTr(" s")
                    color: "#ffffff"
                    font.pixelSize: Theme.fontSize
                }
                PicasaButton {
                    objectName: "slideshowTimePlus"
                    width: 26
                    height: controlsRow.buttonHeight
                    text: "+"
                    enabled: show.seconds < 30
                    onClicked: show.secondsChosen(show.seconds + 1)
                }
            }
        }
    }
}
