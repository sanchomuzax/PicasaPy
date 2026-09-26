import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// #3504: „Eszközök ▸ Képek biztonsági mentése…" — a kiadás-panel MENTÉS-
// üzemmódja a könyvtár alján, ugyanott, ahol a `GiftCdHost` az Ajándék-CD
// módot nyitja. A korábbi, külön ablakban futó `BackupDialog` helyét
// veszi át: a készlet-kezelés (Új/Módosítás/Törlés), a mappánkénti
// kijelölés (#3594) és a mappa/lemezkép kimenet (#3593, #2074) — az
// eredeti mind megvan, csak a MÉRT `backup_group` vezérlőin át.
//
// A `PublishPanel` csak jelez; ez a gazda tartja az állapotot és hívja a
// `backupController`-t (globális kontextus-tulajdonság), ugyanúgy, ahogy
// korábban a `BackupDialog` tette.
Rectangle {
    id: host
    objectName: "backupHost"

    //: a panel nyitva van-e (a gazda nyitja a menüből)
    property bool nyitva: false
    visible: nyitva
    //: a mért panel (212) + fölötte a mappalista sávja (#3594) — a lista
    //: az eredetiben a könyvtárban látszik, a mért vásznon nincs helye
    //: (`BackupFolderStrip` fejkommentje)
    height: mappaSav.y + mappaSav.height + panel.height
    color: Theme.chromeBg
    clip: true

    property var keszletek: []
    property int kivalasztott: -1          // a lista sorindexe
    property bool szerkesztes: false       // az új/módosítás párbeszéd látszik-e
    property int szerkesztettId: -1        // -1 = új készlet
    property string urlapNev: ""
    property string urlapCel: ""
    property string urlapSzuro: "minden"
    //: #3593: a készlet TÍPUSA (`newbackupset.fen`): "cddvd" · "lemez"
    property string urlapTipus: "lemez"
    property string uzenet: ""
    //: az űrlap saját hibasora — ha a vezérlő elutasítja a készletet, az
    //: űrlap NYITVA marad, a beírt adat megmarad, és ez mondja meg, miért
    property string urlapHiba: ""
    //: #3009: fut-e éppen másolás, és a haladás-sáv számlálói
    property bool fut: false
    property int keszFajl: 0
    property int osszesFajl: 0

    //: #3594: a kiválasztott készlet még el nem mentett fájljai, mappánként
    property var mentetlenek: []
    //: #3594: a bepipált mappák útjai
    property var pipaltMappak: []
    //: #3594: a lista háttérszálon készül
    property bool mappakToltodnek: false
    property int mappaKeres: 0

    readonly property var szuroKulcsok: ["minden", "kepek", "fenykepezogep"]
    readonly property var szuroFeliratok: [
        qsTr("All file types"),
        qsTr("All pictures (no movies)"),
        qsTr("Only JPEGs with camera data"),
    ]

    function nyisd() {
        host.uzenet = ""
        host.szerkesztes = false
        host.frissitsd()
        host.nyitva = true
    }

    //: másik készlet = más nyilvántartás, a régi pipák nem érvényesek;
    //: a régi üzenet sem róla szól — az állapotsor a választott készlet
    //: célhelyét és utolsó futását mutatja helyette
    onKivalasztottChanged: {
        host.pipaltMappak = []
        if (!host.fut)
            host.uzenet = ""
        host.frissitsdAMappakat()
    }

    function frissitsdAMappakat() {
        if (typeof backupController === "undefined" || !backupController
                || host.kivalasztott < 0
                || host.kivalasztott >= host.keszletek.length) {
            host.mappaKeres = -1
            host.mappakToltodnek = false
            host.mentetlenek = []
            host.pipaltMappak = []
            return
        }
        host.mentetlenek = []
        host.mappakToltodnek = true
        host.mappaKeres = backupController.mentetlenMappakLekerese(
            host.keszletek[host.kivalasztott].id)
    }

    function fogadjAMappakat(keres, keszletId, sorok) {
        if (keres !== host.mappaKeres) return
        host.mentetlenek = sorok
        host.mappakToltodnek = false
        var elo = sorok.map(function (sor) { return sor.mappa })
        host.pipaltMappak = host.pipaltMappak.filter(
            function (mappa) { return elo.indexOf(mappa) >= 0 })
    }

    function pipald(mappa, be) {
        var uj = host.pipaltMappak.filter(function (m) { return m !== mappa })
        if (be) uj.push(mappa)
        host.pipaltMappak = uj
    }

    function mindetPipald() {
        host.pipaltMappak = host.mentetlenek.map(
            function (sor) { return sor.mappa })
    }

    function egyiketSemPipald() {
        host.pipaltMappak = []
    }

    function frissitsd() {
        if (typeof backupController === "undefined" || !backupController)
            return
        host.keszletek = backupController.keszletek()
        var elozo = host.kivalasztott
        if (host.kivalasztott >= host.keszletek.length)
            host.kivalasztott = host.keszletek.length - 1
        if (host.kivalasztott === elozo)
            host.frissitsdAMappakat()
    }

    function ujKeszletUrlap() {
        host.szerkesztettId = -1
        //: #3189: az eredeti NEM üres mezővel indít (`il_BurnPanel::bksetname`)
        host.urlapNev = qsTr("My Backup Set")
        host.urlapCel = ""
        host.urlapSzuro = "minden"
        host.urlapTipus = "lemez"
        host.urlapHiba = ""
        host.szerkesztes = true
    }

    function szerkesztoUrlap() {
        if (host.kivalasztott < 0) return
        var k = host.keszletek[host.kivalasztott]
        host.szerkesztettId = k.id
        host.urlapNev = k.nev
        host.urlapCel = k.cel
        host.urlapSzuro = k.szuro
        host.urlapTipus = k.tipus || "lemez"
        host.urlapHiba = ""
        host.szerkesztes = true
    }

    function mentsdAzUrlapot() {
        if (typeof backupController === "undefined" || !backupController)
            return
        var rendben = host.szerkesztettId < 0
            ? backupController.ujKeszlet(host.urlapNev, host.urlapCel,
                                         host.urlapSzuro, host.urlapTipus)
            : backupController.modositsdAKeszletet(host.szerkesztettId,
                                                   host.urlapNev, host.urlapCel,
                                                   host.urlapSzuro, host.urlapTipus)
        if (rendben) {
            host.urlapHiba = ""
            host.szerkesztes = false
            host.frissitsd()
        }
    }

    //: #3594: a még el nem mentett mappák, pipával — a panel FÖLÖTT, a
    //: 2. lépés alatt kezdődő és a két lépés-keret szélességét követő
    //: sávban (`backuprect` 128 … `backuprect2` 772)
    BackupFolderStrip {
        id: mappaSav
        x: 128
        y: 6
        width: 772 - 128
        height: implicitHeight
        mentetlenek: host.mentetlenek
        pipaltMappak: host.pipaltMappak
        toltodnek: host.mappakToltodnek
        vanKeszlet: host.kivalasztott >= 0
        onPipaldKert: function (mappa, be) { host.pipald(mappa, be) }
    }

    PublishPanel {
        id: panel
        y: mappaSav.y + mappaSav.height
        uzemmod: "backup"
        mentesKeszletek: host.keszletek
        mentesKivalasztottIndex: host.kivalasztott
        mentesMentetlenek: host.mentetlenek
        mentesPipaltMappak: host.pipaltMappak
        mentesFut: host.fut
        mentesKeszFajl: host.keszFajl
        mentesOsszesFajl: host.osszesFajl
        mentesUzenet: host.uzenet

        onMentesUjKeszletKert: host.ujKeszletUrlap()
        onMentesSzerkesztKert: host.szerkesztoUrlap()
        onMentesTorolKert: torlesMegerosites.ask(
            "", qsTr("Delete this backup set? The saved files stay where they are."))
        onMentesKeszletValasztva: function (index) { host.kivalasztott = index }
        onMentesMindetPipaldKert: host.mindetPipald()
        onMentesSenkitSePipaldKert: host.egyiketSemPipald()
        onMentesMegszakitasKert: {
            if (typeof backupController !== "undefined" && backupController)
                backupController.szakitsdMeg()
        }
        onMentesMegseKert: host.nyitva = false
        onMentesFuttatasKert: function (media) {
            if (typeof backupController === "undefined" || !backupController
                    || host.kivalasztott < 0)
                return
            var k = host.keszletek[host.kivalasztott]
            var mappak = host.pipaltMappak
            //: #2074: a lemezszám-becslés is látszik, ahogy az eredetiben
            //: („Est. %d CDs or %d DVDs") — a kapacitás a mért képletből jön
            var terv = backupController.terv(k.id, mappak)
            if (media === "") {
                host.uzenet = terv.darab === 0
                    ? qsTr("Everything was already backed up.")
                    : qsTr("Copying %1 file(s)... (%2 CD or %3 DVD)")
                        .arg(terv.darab).arg(terv.cd).arg(terv.dvd)
                backupController.futtasdMost(k.id, mappak)
                return
            }
            host.uzenet = terv.darab === 0
                ? qsTr("Everything was already backed up.")
                : qsTr("Writing %1 file(s) to disc image(s)...").arg(terv.darab)
            backupController.futtasdLemezkepbe(k.id, media, mappak)
        }
    }

    Connections {
        target: (typeof backupController !== "undefined") ? backupController : null
        function onHibatJelez(szoveg) {
            //: nyitott űrlapnál a hiba az ŰRLAPRA megy — a modális
            //: párbeszéd mögötti állapotsort a felhasználó nem nézi
            if (host.szerkesztes)
                host.urlapHiba = szoveg
            else
                host.uzenet = szoveg
        }
        function onKeszletekValtoztak() { host.frissitsd() }
        function onMentetlenMappakKeszek(keres, keszletId, sorok) {
            host.fogadjAMappakat(keres, keszletId, sorok)
        }
        function onFutasKesz(darab, bajt) {
            host.fut = false
            host.uzenet = darab === 0
                ? qsTr("Everything was already backed up.")
                //: #3189: `il_BurnPanel::BackupCopy::3`
                : qsTr("Backup Complete")
        }
        //: #2074: a lemezkép-ág vége
        function onLemezkepekKeszek(lemezek, fajlok) {
            host.fut = false
            host.uzenet = lemezek === 0
                ? qsTr("Everything was already backed up.")
                : qsTr("Done: %1 file(s) in %2 disc image(s).")
                    .arg(fajlok).arg(lemezek)
        }
        //: #3009: a másolás háttérszálon megy, és végig beszél
        function onFutasIndult(osszes) {
            host.fut = osszes > 0
            host.osszesFajl = osszes
            host.keszFajl = 0
        }
        function onHaladas(kesz, osszes) {
            host.keszFajl = kesz
            host.osszesFajl = osszes
            //: #3189: `il_BurnPanel::BackupCopy::1`
            host.uzenet = qsTr("Copying (%1/%2) files").arg(kesz).arg(osszes)
        }
    }

    FolderDialog {
        id: celValaszto
        title: qsTr("Choose the backup location")
        onAccepted: {
            host.urlapCel = (typeof fileOpsController !== "undefined"
                             && fileOpsController)
                ? fileOpsController.toLocalPath(celValaszto.selectedFolder.toString())
                : celValaszto.selectedFolder.toString().replace(/^file:\/\//, "")
        }
    }

    //: `newbackupset.fen` — az Új/Módosítás párbeszéd. Az eredetiben is
    //: KÜLÖN erőforrás (nem a `publish` sáv része), ezért itt is felugró
    //: `Dialog` marad, a mért `backup_group` mellett.
    Dialog {
        id: urlapDialog
        objectName: "backupSetDialog"
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        visible: host.szerkesztes
        //: `il_NewBkDialogTitle` / `il_NewBkDialog::EditTitle`
        //: (`biztonsagi-mentes.md` 10.2)
        title: host.szerkesztettId >= 0
            ? qsTr("Edit Backup Set") : qsTr("Backup Set")
        implicitWidth: 420 + leftPadding + rightPadding
        onClosed: host.szerkesztes = false

        contentItem: GridLayout {
            columns: 2
            columnSpacing: 8
            rowSpacing: 8

            //: #3189: a MÉRT felirat — `publish/label_backupname`
            Text {
                text: qsTr("Backup Set")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                objectName: "backupSetName"
                Layout.fillWidth: true
                text: host.urlapNev
                font.pixelSize: Theme.fontSize
                onTextEdited: host.urlapNev = text
                TextFieldContextArea {}
            }

            //: #3593: MÉRT (`newbackupset.fen`): „Backup type:" és a két
            //: rádió; a „Choose…" csak a lemez-lemez típusnál él
            Text {
                Layout.alignment: Qt.AlignTop
                text: qsTr("Backup type:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                RadioButton {
                    objectName: "backupTypeCdDvd"
                    text: qsTr("CD or DVD backup")
                    font.pixelSize: Theme.fontSize
                    checked: host.urlapTipus === "cddvd"
                    onClicked: host.urlapTipus = "cddvd"
                }
                RadioButton {
                    objectName: "backupTypeDisk"
                    text: qsTr("Disk-to-disk backup (for external and network drives)")
                    font.pixelSize: Theme.fontSize
                    checked: host.urlapTipus === "lemez"
                    onClicked: {
                        if (host.urlapTipus === "cddvd"
                                && typeof backupController !== "undefined"
                                && backupController
                                && host.urlapCel === backupController.lemezkepAlapHely())
                            host.urlapCel = ""
                        host.urlapTipus = "lemez"
                    }
                }
            }

            Text {
                text: qsTr("Save to:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                TextField {
                    objectName: "backupSetTarget"
                    Layout.fillWidth: true
                    enabled: host.urlapTipus === "lemez"
                    text: host.urlapTipus === "lemez"
                          ? host.urlapCel
                          : ((typeof backupController !== "undefined"
                              && backupController)
                             ? backupController.lemezkepAlapHely() : "")
                    font.pixelSize: Theme.fontSize
                    onTextEdited: host.urlapCel = text
                    TextFieldContextArea {}
                }
                PicasaButton {
                    objectName: "backupChooseTarget"
                    text: qsTr("Choose...")
                    enabled: host.urlapTipus === "lemez"
                    onClicked: celValaszto.open()
                }
            }

            Text {
                text: qsTr("Files:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ComboBox {
                objectName: "backupSetFilter"
                Layout.fillWidth: true
                model: host.szuroFeliratok
                currentIndex: host.szuroKulcsok.indexOf(host.urlapSzuro)
                onActivated: host.urlapSzuro = host.szuroKulcsok[currentIndex]
            }

            //: a vezérlő elutasításának oka — az űrlap ilyenkor nyitva marad
            Text {
                objectName: "backupFormError"
                Layout.columnSpan: 2
                Layout.fillWidth: true
                visible: host.urlapHiba !== ""
                text: host.urlapHiba
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.brandRed
            }
        }
        //: ⚠️ A mentés gombja NEM `AcceptRole`: az a párbeszédet a mentés
        //: ELŐTT bezárná, és ha a vezérlő elutasítja a készletet (üres név,
        //: hiányzó hely, foglalt név), a beírt adat elveszne. Az
        //: `ActionRole` csak jelez; a párbeszédet a `mentsdAzUrlapot`
        //: zárja, és csak SIKERES mentés után — ahogy a régi ablak is.
        footer: DialogButtonBox {
            Button {
                objectName: "backupFormSave"
                //: #3189: SZERKESZTÉSKOR a mért felirat „Change"
                //: (`il_NewBkDialog::EditOKButton`); ÚJ készletnél „OK"
                text: host.szerkesztettId >= 0 ? qsTr("Change") : qsTr("OK")
                DialogButtonBox.buttonRole: DialogButtonBox.ActionRole
                onClicked: host.mentsdAzUrlapot()
            }
            Button {
                objectName: "backupFormCancel"
                text: qsTr("Cancel")
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
        onRejected: host.szerkesztes = false
    }

    ConfirmDialog {
        id: torlesMegerosites
        namePrefix: "backupDelete"
        title: qsTr("Delete Set")
        onConfirmed: {
            if (typeof backupController === "undefined" || !backupController)
                return
            backupController.torisdAKeszletet(host.keszletek[host.kivalasztott].id)
            host.kivalasztott = -1
        }
    }
}
