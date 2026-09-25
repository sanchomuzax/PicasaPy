import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

// #3503: „Létrehozás ▸ Ajándék CD készítése…" — a kiadás-panel
// Ajándék-CD üzemmódja a könyvtár ALJÁN, ahol az eredetiben is ül
// (`publish/publishback`, 1024 × 212). A panel csak jelez; ez a gazda
// kéri be a lemezkép helyét, indítja a vezérlő háttérmunkáját, és mutatja
// a befejező visszajelzést.
//
// ⚠️ Linuxon nincs lemezíró-szolgáltatás (az eredetiben IMAPI2, spec 13.):
// a kimenet a lemezkép, amit bármely lemezíró program kiír. Ezért a
// befejező párbeszéd a mért „CD kész" címet és a „CD megjelenítése"
// gombot viszi át (a kép helye a fájlkezelőben), a „CD kiadása" gombot
// nem — kiadni való lemez ezen az úton nincs.
Rectangle {
    id: host
    objectName: "giftCdHost"

    //: az `AppController` — a tálca darabszáma és a lemezkép-írás
    property var appController: null
    //: a `FileOpsController` — a kész lemezkép megmutatása a fájlkezelőben
    property var fileOps: null
    //: a panel nyitva van-e (a gazda nyitja a menüből)
    property bool nyitva: false
    //: a lemezkép épp készül
    property bool dolgozik: false
    //: a legutóbb elkészült lemezkép útja
    property string keszUt: ""
    //: hány elem maradt le a legutóbbi lemezképről
    property int keszHibas: 0
    property int _meretIndex: 0
    property string _cdNev: ""

    visible: nyitva
    height: panel.height
    color: Theme.chromeBg
    clip: true

    function nyisd() { host.nyitva = true }

    function indit(cel) {
        if (!host.appController)
            return
        host.dolgozik = true
        host.appController.ajandekCdIrasa(host._meretIndex, host._cdNev, cel)
    }

    PublishPanel {
        id: panel
        uzemmod: "cd"
        elemekSzama: host.appController && host.appController.heldCount !== undefined
                     ? host.appController.heldCount : 0
        dolgozik: host.dolgozik
        onLemezreIrasKert: function (meretIndex, cdNev) {
            host._meretIndex = meretIndex
            host._cdNev = cdNev
            celValaszto.open()
        }
        onMegseKert: host.nyitva = false
        onTovabbiakKert: host.nyitva = false
    }

    FileDialog {
        id: celValaszto
        objectName: "giftCdTargetDialog"
        title: qsTr("Create a Gift CD...")
        fileMode: FileDialog.SaveFile
        defaultSuffix: "iso"
        //: MÉRT szűrőnév: `il_BurnPanel::ISOFilter` („ISO Files")
        nameFilters: [qsTr("ISO Files") + " (*.iso)"]
        currentFolder: host.appController
                       ? host.appController.ajandekCdAlapHely() : ""
        onAccepted: host.indit(selectedFile.toString())
    }

    Connections {
        target: host.appController
        ignoreUnknownSignals: true
        function onAjandekCdKesz(ut, darab, hibas) {
            host.dolgozik = false
            host.keszUt = ut
            host.keszHibas = hibas
            if (ut !== "")
                keszParbeszed.open()
            else
                hibaParbeszed.open()
        }
    }

    //: MÉRT: `il_BurnPanel::DoneDialogTitle` („CD Done") és
    //: `il_BurnPanel::HandleDone::2` („Show CD")
    Dialog {
        id: keszParbeszed
        objectName: "giftCdDoneDialog"
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        title: qsTr("CD Done")
        contentItem: Column {
            spacing: 6
            Label {
                objectName: "giftCdDonePath"
                width: 420
                text: host.keszUt
                wrapMode: Text.WrapAnywhere
            }
            //: ha elemek maradtak le, azt nem csak a napló tudja
            Label {
                objectName: "giftCdDoneMissing"
                width: 420
                visible: host.keszHibas > 0
                wrapMode: Text.WordWrap
                text: qsTr("%1 item(s) could not be added to the disc.")
                      .arg(host.keszHibas)
            }
        }
        footer: DialogButtonBox {
            Button {
                objectName: "giftCdShowButton"
                text: qsTr("Show CD")
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Button {
                text: qsTr("Close")
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
        onAccepted: {
            if (host.fileOps && host.keszUt !== "")
                host.fileOps.revealPhoto(host.keszUt)
        }
    }

    Dialog {
        id: hibaParbeszed
        objectName: "giftCdErrorDialog"
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        title: qsTr("Create a Gift CD...")
        contentItem: Label {
            text: qsTr("The disc image could not be created.")
        }
        standardButtons: Dialog.Ok
    }
}
