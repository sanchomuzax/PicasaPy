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
                delegate: ItemDelegate {
                    width: ListView.view.width
                    // keresés közben a találat CÍME + részlete, egyébként
                    // a fejezet címe
                    text: model.cim !== undefined ? model.cim : ""
                    onClicked: helpDialog.topic =
                        model.fejezet !== undefined ? model.fejezet : model.nev
                    ToolTip.visible: hovered && model.reszlet !== undefined
                    ToolTip.text: model.reszlet !== undefined ? model.reszlet : ""
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
            }
        }
    }
}
