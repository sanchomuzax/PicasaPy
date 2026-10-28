import QtQuick
import QtQuick.Controls

// A fénytábla fejlécének javaslat-sora (#6104): a személy-album javaslat-munkafolyamata
// (kijelölés, szűrő, jóváhagyás, elvetés, további javaslatok). A `baseX` a sor
// kezdete, a `header` a LightboxHeader.
Item {
    required property var header
    required property real baseX

    // a Feltöltés gombjának vízszintes helye: a javaslat-sor utáni első szabad hely
    readonly property real feltoltesX: elvetGomb.visible
        ? elvetGomb.x + elvetGomb.width + header.gombKoz
        : (jovahagyGomb.visible
            ? jovahagyGomb.x + jovahagyGomb.width + header.gombKoz
            : (tovabbiJavaslatGomb.visible
                ? tovabbiJavaslatGomb.x + tovabbiJavaslatGomb.width
                  + header.gombKoz
                : baseX))

    // #2187: a javaslat-munkafolyamat két vezérlője. MÉRT méret
    // mindkettőn 88 × 27 (`respack.yt`); az eredetiben a
    // `confirmsug` és a `confirmsel` UGYANAZON a téglalapon
    // váltakozik - a mérés szerint ugyanaz a kezelő (`0x00602640`),
    // egyetlen logikai argumentummal (`push 1` = mind, `push 0` = a
    // kijelöltek).
    //
    // Nálunk a váltás feltétele: van-e a kijelölésen e személyre
    // szóló függő javaslat (`kijeloltJavaslatHatokor`).
    //: #1792: a nem testreszabható elemek a négy gomb UTÁN állnak -
    //: a `gombSorVege` a testreszabott sor jobb széle.
    //: #2187: `sug_filter` - MÉRT méret 29 × 27, és a mért helye a
    //: jóváhagyás-pár BAL oldala ((316,55) vs. (348,55)). A hézag
    //: nálunk a ház szokása (`gombKoz`), nem az eredeti 3 képpontja:
    //: a fejléc minden gombja így áll egymás mellett (#1792).
    PicasaButton {
        id: javaslatKijeloloGomb
        objectName: "headerSelectSuggestionsButton"
        x: baseX
        anchors.verticalCenter: parent.verticalCenter
        visible: header.javaslatokLatszanak
        width: 29; height: 27
        hoverEnabled: true
        onClicked: header.selectSuggestionsRequested()
        contentItem: Item {
            Image {
                objectName: "headerSelectSuggestionsIcon"
                source: "icons/collage-check.svg"
                width: 16; height: 16
                sourceSize.width: 16; sourceSize.height: 16
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
            }
        }
    }
    PicasaButton {
        id: javaslatSzuroGomb
        objectName: "headerSuggestionFilterButton"
        x: javaslatKijeloloGomb.visible
            ? javaslatKijeloloGomb.x + javaslatKijeloloGomb.width
              + header.gombKoz
            : baseX
        anchors.verticalCenter: parent.verticalCenter
        visible: header.javaslatSzuroLatszik
        width: 29; height: 27
        checkable: true
        checked: header.suggestionsOnly
        //: MÉRT súgó (`faceheaderpaneltext.tre:35`): „Show only
        //: suggestions (when toggled on)"
        ToolTip.text: qsTr("Show only suggestions (when toggled on)")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        //: a kötést a kattintás UTÁN vissza kell állítani, különben a
        //: gomb a saját, belső állapotát mutatná a vezérlőé helyett
        //: (#1468 rádió-csapda)
        onClicked: {
            header.suggestionsOnlyToggled(!header.suggestionsOnly)
            checked = Qt.binding(function () {
                return header.suggestionsOnly
            })
        }
        contentItem: Item {
            Image {
                objectName: "headerSuggestionFilterIcon"
                source: "icons/face-suggestion-badge.svg"
                width: 16; height: 16
                sourceSize.width: 16; sourceSize.height: 16
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
            }
        }
    }
    PicasaButton {
        id: jovahagyGomb
        objectName: "headerConfirmSuggestionsButton"
        x: javaslatSzuroGomb.visible
            ? javaslatSzuroGomb.x + javaslatSzuroGomb.width + header.gombKoz
            : baseX
        anchors.verticalCenter: parent.verticalCenter
        visible: header.javaslatokLatszanak
        //: MÉRT feliratok (`faceheaderpaneltext.tre:44`): „Confirm all"
        //: - magyarul „Az összes jóváhagyása" -, a kijelölt hatókörben
        //: „Confirm" („Jóváhagyás"). A darabszám a fejléc-gombok
        //: szokása szerint zárójelben (#1823).
        text: header.kijeloltJavaslatHatokor
            ? qsTr("Confirm")
            : qsTr("Confirm all") + " (" + header.suggestionCount + ")"
        width: 88; height: 27
        //: MÉRT súgók: „Confirm all suggestions" / „Confirm selected
        //: suggestions"
        property string sugoSzoveg: header.kijeloltJavaslatHatokor
            ? qsTr("Confirm selected suggestions")
            : qsTr("Confirm all suggestions")
        ToolTip.text: sugoSzoveg
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        onClicked: header.confirmSuggestionsRequested()
    }
    PicasaButton {
        id: elvetGomb
        objectName: "headerRemoveSuggestionsButton"
        x: jovahagyGomb.visible
            ? jovahagyGomb.x + jovahagyGomb.width + header.gombKoz
            : baseX
        anchors.verticalCenter: parent.verticalCenter
        visible: header.javaslatokLatszanak
        //: MÉRT felirat (`faceheaderpaneltext.tre:50`): „Remove"
        text: qsTr("Remove")
        width: 88; height: 27
        //: MÉRT súgó: „Remove selected suggestions". Kijelölt javaslat
        //: nélkül a gomb nálunk az összesre hat, és a súgó is ezt
        //: mondja - különben mást ígérne, mint amit a gomb tesz.
        property string sugoSzoveg: header.kijeloltJavaslatHatokor
            ? qsTr("Remove selected suggestions")
            : qsTr("Remove all suggestions")
        ToolTip.text: sugoSzoveg
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        onClicked: header.removeSuggestionsRequested()
    }
    //: #2187: „További javaslatok keresése" - a `moresug` mért helyén és
    //: méretében (179 × 27, a jóváhagyás-pár teljes sávja). A művelet a
    //: `FaceScanController.moreSuggestions()`: a javaslat-lépcsőt tízzel
    //: lazítja, és a beállítást SZÁNDÉKOSAN nem írja vissza - az eredeti
    //: `moresug` kezelője (`0x00602890`) sem írja.
    PicasaButton {
        id: tovabbiJavaslatGomb
        objectName: "headerMoreSuggestionsButton"
        x: javaslatSzuroGomb.visible
            ? javaslatSzuroGomb.x + javaslatSzuroGomb.width + header.gombKoz
            : baseX
        anchors.verticalCenter: parent.verticalCenter
        visible: header.tovabbiJavaslatLatszik
        //: MÉRT felirat (`faceheaderpaneltext.tre:53`): „Find more
        //: suggestions" - magyarul „További javaslatok keresése".
        text: qsTr("Find more suggestions")
        width: 179; height: 27
        //: MÉRT súgó ugyanonnan
        ToolTip.text: qsTr("Lower the recognition threshold to get more suggestions")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
        onClicked: header.moreSuggestionsRequested()
    }
}
