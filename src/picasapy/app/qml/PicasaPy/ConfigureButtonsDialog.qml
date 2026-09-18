import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// „Gombok konfigurálása…" (#1792) — az album-fejléc gombsorának
// testreszabása.
//
// Az eredeti Picasa párbeszéde klasszikus KÉTLISTÁS választó volt
// (`docs/specs/picasa-menu-parancsok-viselkedes.md` 44.): „Rendelkezésre
// álló gombok:" ↔ „Jelenlegi gombok:", közte „Add >>" és „<< Remove", a
// jobb listán „Move Up" / „Move Down", alul „Reset to Defaults", és
// OK / Mégse.
//
// ⛔ Ami az eredetiben MÉG volt, és itt szándékosan NINCS: a „Find buttons
// online…" és a gombcsomag-telepítő ág. A kiszolgáló (`picasa.smo`) nem
// létezik — a jegy törzse ezt hatókörön kívülre teszi.
//
// A szerkesztés a párbeszéd SAJÁT másolatán folyik, és csak az OK ment:
// így a Mégse tényleg elvet (a „Kész, ha" külön pontja).
Dialog {
    id: root
    objectName: "configureButtonsDialog"
    title: qsTr("Configure Buttons")
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    standardButtons: Dialog.Ok | Dialog.Cancel

    //: a híd (`gombsav`); a próbák a sajátjukat adhatják be
    property var gombsavHid: (typeof gombsav !== "undefined") ? gombsav : null

    //: a SZERKESZTETT sor — a párbeszéd munkapéldánya
    property var jelenlegi: []
    onOpened: {
        root.jelenlegi = root.gombsavHid ? root.gombsavHid.sorrend.slice() : []
        jelenlegiLista.currentIndex = -1
        elerhetoLista.currentIndex = -1
    }
    onAccepted: {
        if (root.gombsavHid)
            root.gombsavHid.mentsd(root.jelenlegi)
    }

    //: A listákban megjelenő felirat. A híd a KULCSOT adja, a fordítás itt
    //: történik — így a `.ts`-ben a többi felirat mellé kerül.
    function felirata(nev) {
        switch (nev) {
        case "headerPlayButton": return qsTr("Play Fullscreen Slideshow")
        case "headerSelectStarredButton": return qsTr("Select starred photos")
        case "headerSaveEditsButton": return qsTr("Save edited photos to disk")
        case "headerCollageButton": return qsTr("Create Photo Collage")
        }
        return nev
    }

    //: a bal lista számolt tartalma a MUNKAPÉLDÁNYBÓL (nem a tárolóból):
    //: a párbeszéden belüli lépések azonnal látszanak
    readonly property var szabadok: {
        var mind = root.gombsavHid ? root.gombsavHid.sorrend : []
        var osszes = ["headerPlayButton", "headerSelectStarredButton",
                      "headerSaveEditsButton", "headerCollageButton"]
        var ki = []
        for (var i = 0; i < osszes.length; ++i)
            if (root.jelenlegi.indexOf(osszes[i]) < 0)
                ki.push(osszes[i])
        return ki
    }

    function hozzaad() {
        if (elerhetoLista.currentIndex < 0)
            return
        var nev = root.szabadok[elerhetoLista.currentIndex]
        var uj = root.jelenlegi.slice()
        uj.push(nev)
        root.jelenlegi = uj
        elerhetoLista.currentIndex = -1
    }
    function eltavolit() {
        if (jelenlegiLista.currentIndex < 0)
            return
        var uj = root.jelenlegi.slice()
        uj.splice(jelenlegiLista.currentIndex, 1)
        root.jelenlegi = uj
        jelenlegiLista.currentIndex = -1
    }
    function mozgat(irany) {
        var honnan = jelenlegiLista.currentIndex
        var hova = honnan + irany
        if (honnan < 0 || hova < 0 || hova >= root.jelenlegi.length)
            return
        var uj = root.jelenlegi.slice()
        var mit = uj[honnan]
        uj[honnan] = uj[hova]
        uj[hova] = mit
        root.jelenlegi = uj
        jelenlegiLista.currentIndex = hova
    }
    function alaphelyzet() {
        root.jelenlegi = root.gombsavHid
            ? root.gombsavHid.alapertelmezes() : []
        jelenlegiLista.currentIndex = -1
    }

    component GombLista: ListView {
        width: 220
        height: 150
        clip: true
        highlightMoveDuration: 0
        delegate: Text {
            required property string modelData
            required property int index
            width: ListView.view.width
            padding: 4
            text: root.felirata(modelData)
            font.pixelSize: Theme.fontSize
            color: ListView.view.currentIndex === index
                   ? Theme.panelSelectionText : Theme.ink
            TapHandler {
                onSingleTapped: parent.ListView.view.currentIndex = parent.index
            }
        }
        highlight: Rectangle { color: Theme.panelSelectionActive }
    }

    ColumnLayout {
        spacing: 8

        RowLayout {
            spacing: 8
            ColumnLayout {
                spacing: 4
                Text {
                    text: qsTr("Available buttons:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                Rectangle {
                    Layout.preferredWidth: 220
                    Layout.preferredHeight: 150
                    color: Theme.panelBg
                    border.color: Theme.chromeBorder
                    GombLista {
                        id: elerhetoLista
                        objectName: "configButtonsAvailableList"
                        anchors.fill: parent
                        anchors.margins: 1
                        model: root.szabadok
                    }
                }
            }
            ColumnLayout {
                spacing: 6
                Layout.alignment: Qt.AlignVCenter
                PanelButton {
                    objectName: "configButtonsAddButton"
                    label: qsTr("Add >>")
                    buttonEnabled: elerhetoLista.currentIndex >= 0
                    onButtonClicked: root.hozzaad()
                }
                PanelButton {
                    objectName: "configButtonsRemoveButton"
                    label: qsTr("<< Remove")
                    buttonEnabled: jelenlegiLista.currentIndex >= 0
                    onButtonClicked: root.eltavolit()
                }
            }
            ColumnLayout {
                spacing: 4
                Text {
                    text: qsTr("Current buttons:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                Rectangle {
                    Layout.preferredWidth: 220
                    Layout.preferredHeight: 150
                    color: Theme.panelBg
                    border.color: Theme.chromeBorder
                    GombLista {
                        id: jelenlegiLista
                        objectName: "configButtonsCurrentList"
                        anchors.fill: parent
                        anchors.margins: 1
                        model: root.jelenlegi
                    }
                }
            }
            ColumnLayout {
                spacing: 6
                Layout.alignment: Qt.AlignVCenter
                PanelButton {
                    objectName: "configButtonsUpButton"
                    label: qsTr("Move Up")
                    buttonEnabled: jelenlegiLista.currentIndex > 0
                    onButtonClicked: root.mozgat(-1)
                }
                PanelButton {
                    objectName: "configButtonsDownButton"
                    label: qsTr("Move Down")
                    buttonEnabled: jelenlegiLista.currentIndex >= 0
                        && jelenlegiLista.currentIndex < root.jelenlegi.length - 1
                    onButtonClicked: root.mozgat(1)
                }
            }
        }

        PanelButton {
            objectName: "configButtonsResetButton"
            label: qsTr("Reset to Defaults")
            //: a tárolóba NEM ír — a felhasználó a Mégsével még
            //: visszaléphet (az eredetiben is OK/Mégse zárja a párbeszédet)
            onButtonClicked: root.alaphelyzet()
        }
    }
}
