import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #2054: a felhasználói súgó nézője — F1.
//
// A tartalom a csomagfa alól jön (`picasapy/help/`, ld. a
// `help_content.py` fejlécét), tehát NET NÉLKÜL is megvan, telepített
// programból is. A `controller` (HelpMixin) adja: `helpTopics`,
// `helpTopicText(nev)`, `helpSearch(kifejezes)`.
//
// A szöveg nyers Markdown. A `Text` `MarkdownText` formátuma a
// címsorokat, listákat és a félkövért megjeleníti — külön formázót nem
// építünk, mert a súgó szándékosan egyszerű szöveg.
Dialog {
    id: helpDialog
    objectName: "helpDialog"

    title: qsTr("Help Contents and Index")
    modal: true
    anchors.centerIn: parent
    standardButtons: Dialog.Close

    width: Math.min(parent ? parent.width - 80 : 900, 900)
    height: Math.min(parent ? parent.height - 80 : 620, 620)

    //: A megnyitandó fejezet. A Shift+F1 ezt állítja a mutató alatti
    //: elem `helpTopic`-jára; F1-re a főoldal nyílik.
    property string topic: ""

    function nyisdMeg(fejezet) {
        helpDialog.topic = fejezet && fejezet.length > 0
            ? fejezet
            : (controller ? controller.helpHomeTopic : "index.md")
        keresoMezo.text = ""
        helpDialog.open()
    }

    onTopicChanged: {
        if (!controller) return
        szovegNezo.text = controller.helpTopicText(helpDialog.topic)
        szovegGorgeto.contentY = 0
    }

    RowLayout {
        anchors.fill: parent
        spacing: 10

        // --- bal: kereső + fejezetlista ---
        ColumnLayout {
            Layout.preferredWidth: 260
            Layout.fillHeight: true
            spacing: 6

            TextField {
                id: keresoMezo
                objectName: "helpSearchField"
                Layout.fillWidth: true
                placeholderText: qsTr("Search in help")
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
                onTextChanged: {
                    if (!controller) return
                    // Üres keresésre a FEJEZETLISTA jön vissza — a néző
                    // sosem marad üresen.
                    talalatModell.clear()
                    if (text.trim().length === 0) return
                    var talalatok = controller.helpSearch(text)
                    for (var i = 0; i < talalatok.length; ++i)
                        talalatModell.append(talalatok[i])
                }
            }

            ListModel { id: talalatModell }

            ListView {
                objectName: "helpTopicList"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: keresoMezo.text.trim().length > 0
                    ? talalatModell
                    : (controller ? controller.helpTopics : [])
                // #2214: keresés közben a sor a CÍMET és a RÉSZLETET is
                // mutatja. Korábban csak a cím látszott, a részlet pedig
                // egérrámutatásra — mivel egy fejezet több sort is kapott,
                // a lista ugyanazt a címet ismételte, és a sorok
                // megkülönböztethetetlenek voltak. Ma egy fejezet egy sor,
                // és ha többször előfordul, a darabszám is kiírja.
                delegate: ItemDelegate {
                    objectName: "helpResultRow"
                    width: ListView.view.width
                    height: reszletSor.visible
                        ? cimSor.implicitHeight + reszletSor.implicitHeight + 12
                        : cimSor.implicitHeight + 12
                    onClicked: helpDialog.topic =
                        model.fejezet !== undefined ? model.fejezet : model.nev

                    contentItem: Column {
                        spacing: 1

                        Text {
                            id: cimSor
                            objectName: "helpResultTitle"
                            width: parent.width
                            elide: Text.ElideRight
                            color: Theme.ink
                            font.pixelSize: Theme.fontSize
                            // „Effektek listája (5)" — a darabszám csak
                            // akkor jelenik meg, ha tényleg több van.
                            text: {
                                var cim = model.cim !== undefined ? model.cim : ""
                                var db = model.db !== undefined ? model.db : 0
                                return db > 1 ? cim + " (" + db + ")" : cim
                            }
                        }

                        Text {
                            id: reszletSor
                            objectName: "helpResultSnippet"
                            width: parent.width
                            visible: model.reszlet !== undefined
                                     && model.reszlet.length > 0
                            elide: Text.ElideRight
                            color: Theme.textGray
                            font.pixelSize: Theme.fontSize - 2
                            text: model.reszlet !== undefined ? model.reszlet : ""
                        }
                    }
                }
            }
        }

        // --- jobb: a fejezet szövege ---
        ScrollView {
            id: szovegGorgeto
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            TextArea {
                id: szovegNezo
                objectName: "helpTopicText"
                readOnly: true
                wrapMode: TextArea.Wrap
                textFormat: TextArea.MarkdownText
                selectByMouse: true
                // #422: jobbklikk-menü a súgó szövegén is — a „Másolás"
                // itt valódi funkció (a felhasználó kimásol egy lépéssort).
                TextFieldContextArea {}

                // #2212: a nyitólap a súgó TARTALOMJEGYZÉKE — csupa
                // hivatkozás. Kezelő nélkül a linkek kékek, de a kattintás
                // nem csinál semmit: a fő navigációs felület halott.
                //
                // A feloldás a vezérlőn át megy (a HIVATKOZÓ fejezethez
                // képest relatív, és a súgó mappájából nem enged kilépni).
                // Üres válasz = nem fejezet (külső cím, nem létező lap):
                // ilyenkor SEM lépünk sehova, de a `console.warn` kiírja —
                // a néma nem-történik-semmi épp az a hiba, amit javítunk.
                onLinkActivated: function (link) {
                    if (!controller) return
                    var cel = controller.helpResolveLink(helpDialog.topic, link)
                    if (cel) {
                        helpDialog.topic = cel
                    } else {
                        console.warn("a súgó hivatkozása nem fejezetre mutat:", link)
                    }
                }

                // A kéz-kurzor a hivatkozás fölött: enélkül a felhasználó
                // nem is próbálja megnyomni. A `hoveredLink` a TextArea
                // saját tulajdonsága, nem kell külön találati vizsgálat.
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.NoButton   // csak a kurzorért
                    cursorShape: szovegNezo.hoveredLink
                        ? Qt.PointingHandCursor : Qt.IBeamCursor
                }
            }
        }
    }
}
