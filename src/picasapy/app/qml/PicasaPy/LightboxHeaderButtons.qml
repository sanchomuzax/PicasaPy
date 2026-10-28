import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A fénytábla fejlécének gombsora (#6104): a testreszabható gombok, a személy-album
// filmgombjai és a Feltöltés. A javaslat-vezérlők a LightboxHeaderSuggestionRow-ban
// vannak, a Feltöltés helyét az innen adja.
Item {
    id: gombSor
    required property var header
    Layout.leftMargin: header.personAlbumHeaderMode ? 80
        : (header.personAlbumFolderMode ? 12 : 28)
    Layout.topMargin: header.personAlbumHeaderMode ? -31
        : (header.personAlbumFolderMode ? -5 : 4)
    Layout.fillWidth: true
    //: a legmagasabb gomb (a kollázs 27) - a sor magassága ennyi
    Layout.preferredHeight: 27
    implicitHeight: 27

    Rectangle {
        id: playGomb
        objectName: "headerPlayButton"
        visible: gombLathato(objectName)
        x: gombX(objectName)
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset:
            header.personAlbumHeaderMode ? -5 : 0
        width: 26; height: 22; radius: 3
        color: headerPlayHover.hovered ? Theme.headerPlayButtonHoverBg
                                        : Theme.headerPlayButtonBg
        border.color: Theme.chromeBorder
        Text {
            anchors.centerIn: parent
            text: "▸"; color: Theme.picasaGreen; font.pixelSize: 13
        }
        HoverHandler { id: headerPlayHover }
        ToolTip.text: qsTr("Play Fullscreen Slideshow")
        ToolTip.visible: headerPlayHover.hovered
        ToolTip.delay: Theme.tooltipDelay
        //: #885: `headerpanel/play` - LENYOMÁSRA indul a diavetítés
        //: (`Property mousedown 1`). A `TapHandler` a felengedést
        //: jelzi, ezért a lenyomás-átmenetre kötjük; a `pressed`
        //: visszaváltása nem sülhet el másodszor.
        TapHandler {
            onPressedChanged: if (pressed) header.playRequested()
        }
    }
    // #1823: eddig ez egy néma díszcsempe volt - se neve, se
    // kezelője. Most a mért `select_star` gomb: a jelenlegi mappa
    // csillagozott képeit jelöli ki.
    PicasaButton {
        id: csillagGomb
        objectName: "headerSelectStarredButton"
        visible: gombLathato(objectName)
        x: gombX(objectName)
        anchors.verticalCenter: parent.verticalCenter
        height: 22
        //: #885: LENYOMÁSRA sül el - `headerpanel/select_star`
        //: mért `mousedown`-ja. Kijelölést vált, nem művelet.
        lenyomasra: true
        text: header.feliratSzammal("☆")
        Layout.preferredHeight: 22
        ToolTip.text: qsTr("Select starred photos")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        onClicked: header.selectStarredRequested()
    }
    // #1823: „szerkesztések mentése lemezre" (`save_edits`) - a
    // fejlécről eddig teljesen hiányzott, pedig a művelet megvan
    // (#444). Üres kijelölésnél tiltott: a mentés a KIJELÖLTEKRE hat.
    PicasaButton {
        id: mentesGomb
        objectName: "headerSaveEditsButton"
        visible: gombLathato(objectName)
        x: gombX(objectName)
        anchors.verticalCenter: parent.verticalCenter
        height: 22
        text: header.feliratSzammal(qsTr("Save"))
        enabled: header.selectedCount > 0 && header.hasPendingEdits
        Layout.preferredHeight: 22
        ToolTip.text: qsTr("Save edited photos to disk")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        onClicked: header.saveEditsRequested()
    }
    // #1006: `headerpanel/create_collage` - MÉRT 29 × 27
    // (`picasa-create-features.md` 1.10.5).
    //
    // ⚠️ Az eredetiben KÉT panel van: a mappa-fejléc
    // (`headerpanel`) és az ARC-fejléc (`faceheaderpanel`), mindkettőn
    // ugyanez a gomb. A mi felületünkön a személy képei UGYANEBBEN a
    // rácsban, ugyanezzel a fejléccel jelennek meg - nincs külön
    // arc-fejléc. Ez az egy gomb tehát mindkét belépési pontot
    // lefedi; külön arc-fejlécet építeni olyan felületet hozna létre,
    // ami nálunk nem létezik.
    //
    // #2187: ez a döntés maradt - az arc-fejléc SAJÁT vezérlői (a
    // javaslat-munkafolyamat) ezért ugyanebbe a fejlécbe kerültek, a
    // `personName` módjába, nem külön panelbe.
    PicasaButton {
        id: kollazsGomb
        objectName: "headerCollageButton"
        visible: gombLathato(objectName)
        x: gombX(objectName)
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset:
            header.personAlbumHeaderMode ? -5 : 0
        //: #885: LENYOMÁSRA sül el - `headerpanel/create_collage`
        //: mért `mousedown`-ja. ⚠️ Nem mond ellent a jegy
        //: táblázatának: ez a gomb a kollázs-PANELT NYITJA MEG
        //: (nézetváltás), a „Kollázs létrehozása" művelet-gomb
        //: a panelen belül marad felengedésre.
        lenyomasra: true
        width: 29; height: 27
        ToolTip.text: qsTr("Create Photo Collage")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        onClicked: header.collageRequested()
        contentItem: Item {
            Image {
                objectName: "headerCollageIcon"
                source: "icons/collage.svg"
                width: 16; height: 16
                sourceSize.width: 16; sourceSize.height: 16
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
            }
        }
    }
    //: #4539: a mappa-fejléc film-gombja. Az eredeti referencia-
    //: képernyőképén (`2026-07-17 20 54 38.png`) a kollázs UTÁN, alapból
    //: látszik: ▸ · [+kép] · [+film] · ☆ · mentés · Feltöltés ▾. A
    //: `headerpanel/create_movie` mért tulajdonsága `mousedown 1` -
    //: ugyanúgy LENYOMÁSRA sül el, mint a kollázs.
    //:
    //: Nem testreszabható elem (mint a Feltöltés): a sor UTÁN áll, és a
    //: `gombSorVege`-hez igazodik. Így egy régi, mentett gombsor nem
    //: rejti el, és a sorrend (kollázs → film) megmarad, ha a kollázs
    //: látszik. Mappa-nézetben él; a személy-album a saját film-gombjait
    //: használja (#4212).
    PicasaButton {
        id: mappaFilmGomb
        objectName: "headerMovieButton"
        visible: header.personName === ""
        x: gombSorVege
        anchors.verticalCenter: parent.verticalCenter
        lenyomasra: true
        width: 29; height: 27
        ToolTip.text: qsTr("Create Movie Presentation")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        onClicked: header.movieRequested()
        contentItem: Item {
            Image {
                objectName: "headerMovieIcon"
                source: "icons/movie.svg"
                width: 16; height: 16
                sourceSize.width: 16; sourceSize.height: 16
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
            }
        }
    }
    //: #4212: a `faceheaderpanel/create_movie` gombja. A személy-album
    //: külön fejlécpanelje nálunk a LightboxHeader személy-módja; a
    //: két filmgomb a meglévő Filmkészítőt nyitja meg az album összes
    //: képével, közös felbontás-beállítással.
    PicasaButton {
        id: szemelyFilmGomb
        objectName: "faceHeaderMovieButton"
        x: gombSorVege
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset:
            header.personAlbumHeaderMode ? -5 : 0
        visible: header.personName !== ""
        width: 29; height: 27
        hoverEnabled: true
        ToolTip.text: qsTr("Create Movie Presentation")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        onClicked: header.personMovieRequested()
        contentItem: Item {
            Image {
                source: "icons/movie.svg"
                width: 16; height: 16
                sourceSize.width: 16; sourceSize.height: 16
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
            }
        }
    }
    //: #4212: `faceheaderpanel/create_face_movie` - ugyanaz a
    //: személyalbum-képforrás és Filmkészítő, mint a szomszédos Movie
    //: gombnál; külön filmfelbontást nem tárolunk.
    PicasaButton {
        id: szemelyArcfilmGomb
        objectName: "faceHeaderFaceMovieButton"
        x: szemelyFilmGomb.x + szemelyFilmGomb.width
           + header.personHeaderExtraGap
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset:
            header.personAlbumHeaderMode ? -5 : 0
        visible: header.personName !== ""
        width: 29; height: 27
        hoverEnabled: true
        ToolTip.text: qsTr("Create Face Movie")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        onClicked: header.personMovieRequested()
        contentItem: Item {
            Image {
                source: "icons/movie.svg"
                width: 16; height: 16
                sourceSize.width: 16; sourceSize.height: 16
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
            }
            Image {
                source: "icons/faces-badge.svg"
                width: 9; height: 9
                sourceSize.width: 9; sourceSize.height: 9
                fillMode: Image.PreserveAspectFit
                anchors.right: parent.right
                anchors.bottom: parent.bottom
            }
        }
    }
    PicasaButton {
        id: szemelyAlbumkepGomb
        objectName: "headerSetPersonThumbnailButton"
        x: szemelyArcfilmGomb.x + szemelyArcfilmGomb.width
           + header.personHeaderExtraGap
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset:
            header.personAlbumHeaderMode ? -5 : 0
        visible: header.personAlbumHeaderMode
        width: 29; height: 27
        enabled: header.personAlbumThumbnailEnabled
        ToolTip.text: qsTr("Set as People Album Thumbnail")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        onClicked: header.setPersonThumbnailRequested()
        contentItem: Item {
            Image {
                source: "icons/person-silhouette.svg"
                width: 15; height: 15
                sourceSize.width: 15; sourceSize.height: 15
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
            }
        }
    }

    LightboxHeaderSuggestionRow {
        id: javaslatSor
        anchors.fill: parent
        header: gombSor.header
        baseX: szemelyGombSorVege
    }

    PicasaButton {
        id: feltoltesGomb
        x: javaslatSor.feltoltesX
        objectName: "headerUploadButton"
        //: #2187: a feltöltés a javaslat-vezérlők UTÁN áll - akármelyik
        //: állapot van érvényben (jóváhagyás-pár VAGY „További
        //: javaslatok"); a kettő kizárja egymást.
        anchors.verticalCenter: parent.verticalCenter
        visible: !header.personAlbumHeaderMode
        height: 22
        text: header.feliratSzammal(qsTr("Upload")) + " ▾"
        enabled: false
        Layout.preferredHeight: 22
    }

    // #1792: a testreszabott gombsor segédei.
    //
    // ⚠️ SZÁNDÉKOSAN a gombok UTÁN állnak. A `headerCollageButton` fölötti
    // indoklást egy őr olvassa (#1006), és az a horgony ELSŐ előfordulását
    // keresi - ha a név itt, feljebb is szerepelne, az őr a fájl fejlécét
    // vizsgálná, és némán mást mérne, mint amit állít.
    //: #1792: a testreszabott gombsor - a `gombsav` híd tölti (az
    //: eredetiben a `Preferences\Buttons\UserConfig` és `…\Exclude`
    //: tárolta). Ha a híd nincs (önálló komponens-teszt), a teljes,
    //: alapértelmezett készlet jön - a fejléc próbái így változatlanul
    //: minden gombot megtalálnak.
    readonly property var gombSorrend:
        header.personAlbumHeaderMode
            ? ["headerPlayButton", "headerCollageButton"]
            : ((typeof gombsav !== "undefined" && gombsav && gombsav.sorrend)
            ? gombsav.sorrend
            : ["headerPlayButton", "headerSelectStarredButton",
               "headerSaveEditsButton", "headerCollageButton"])

    //: Látszik-e ez a gomb? A készleten KÍVÜLI gomb (feltöltés,
    //: javaslat-vezérlők) nem testreszabható, az mindig a saját
    //: feltételét követi.
    function gombLathato(nev) {
        return gombSorrend.indexOf(nev) >= 0
    }

    //: #1792: a gomb HELYE a sorban - ebből lesz a megjelenítési
    //: sorrend. ⚠️ `RowLayout`-tal ez nem megoldható: az a gyerekeit a
    //: DEKLARÁCIÓ sorrendjében rakja ki. `Repeater`-rel sem: annak a
    //: delegáltjait a `findChild` nem találja meg, és a fejléc gombjaira
    //: épülő próbák pont azon a néven szólítják meg őket. Ezért marad a
    //: négy gomb a helyén, és a VÍZSZINTES pozíciót számoljuk.
    function gombX(nev, sajatSzelesseg) {
        if (header.personAlbumHeaderMode) {
            if (nev === "headerPlayButton") return 0
            if (nev === "headerCollageButton") return 36
            return 0
        }
        var helye = gombSorrend.indexOf(nev)
        if (helye < 0)
            return 0
        var x = 0
        for (var i = 0; i < helye; ++i)
            x += gombSzelessege(gombSorrend[i]) + header.gombKoz
        return x
    }

    //: a gombok közti hézag - a korábbi `RowLayout` `spacing`-je
    readonly property int gombKoz: 6
    readonly property int personHeaderExtraGap:
        header.personAlbumHeaderMode ? 2 : header.gombKoz

    //: a testreszabott gombsor jobb széle (a további elemek innen
    //: folytatódnak)
    readonly property real gombSorVege: {
        if (header.personAlbumHeaderMode)
            return 70
        var x = 0
        for (var i = 0; i < gombSorrend.length; ++i)
            x += gombSzelessege(gombSorrend[i]) + header.gombKoz
        return x
    }

    //: A személy-album saját filmgombjai után folytatódik a javaslat-sor.
    //: Mappa nézetben a testreszabott sor és a mappa film-gombja (#4539)
    //: után folytatódik a Feltöltés.
    readonly property real szemelyGombSorVege: header.personName !== ""
        ? (header.personAlbumHeaderMode
            ? szemelyAlbumkepGomb.x + szemelyAlbumkepGomb.width
              + header.personHeaderExtraGap
            : szemelyArcfilmGomb.x + szemelyArcfilmGomb.width
              + header.gombKoz)
        : mappaFilmGomb.x + mappaFilmGomb.width + header.gombKoz

    //: A gomb szélessége a sorrend-számításhoz. A `play` és a kollázs
    //: MÉRT, fix méretű; a másik kettő felirat-függő, azt az elemtől
    //: kérdezzük.
    function gombSzelessege(nev) {
        var elem = gombElem(nev)
        return elem ? elem.width : 0
    }

    //: azonosító → elem, a szélesség-lekérdezéshez
    function gombElem(nev) {
        switch (nev) {
        case "headerPlayButton": return playGomb
        case "headerSelectStarredButton": return csillagGomb
        case "headerSaveEditsButton": return mentesGomb
        case "headerCollageButton": return kollazsGomb
        }
        return null
    }
}
