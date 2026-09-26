import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Képek biztonsági mentése (#440, `ID_TOOLS_BACKUP`, `newbackupset.fen`):
// nevesített, újrafuttatható, INKREMENTÁLIS mentés-készletek.
//
// Az eredeti saját meghatározása: a készlet megjegyzi, hova mentett ÉS mit
// mentett már el, tehát újraindításkor csak az új fájlokat viszi át. A
// CD/DVD-ág szándékosan kimarad (a jegy döntése) — a cél külső meghajtó
// vagy hálózati megosztás.
//
// A New / Edit / Delete Set hármas az eredetié; a törlés megerősítést kér.
//
// #3594: a kiválasztott készlet alatt az eredeti mentés-üzemmódjának 2.
// lépése (`backuprect2`, `biztonsagi-mentes.md` 10.3): csak a még el nem
// mentett fájlok látszanak, mappánként pipával, „Az összes kijelölése" /
// „Az összes kijelölés megszüntetése" gombbal, és a futás csak a bepipált
// mappákat viszi. A mért szöveg („Jelölje ki…") szerint alapból nincs pipa.
Window {
    id: backupWindow
    objectName: "backupDialog"
    //: #3009: fut-e éppen másolás — ilyenkor látszik a haladás-sáv és a
    //: Megszakítás gomb, és a Mentés gomb tiltott
    property bool fut: false
    property int keszFajl: 0
    property int osszesFajl: 0
    title: qsTr("Back Up Pictures")
    modality: Qt.ApplicationModal
    //: #3593: a gombsor (három készlet-gomb, a CD/DVD-választó, a Mentés és
    //: a Bezárás) magyarul ennyi helyet kér — keskenyebben kilóg
    //: #3594: a mappa-lista (2. lépés) a készlet-lista alá kerül
    width: 760
    height: 600
    minimumWidth: 720
    minimumHeight: 520
    color: Theme.canvasBg
    //: #3593: a külön `Window` NEM örökli a főablak `palette`-jét — enélkül
    //: a mezők a rendszer (sötét) színeit kapták, a rádiógombok felirata
    //: pedig olvashatatlan volt. Ugyanaz a készlet, mint a `Main.qml`-é.
    palette {
        window: Theme.canvasBg
        windowText: Theme.ink
        base: Theme.controlBase
        alternateBase: Theme.panelBg
        text: Theme.ink
        button: Theme.buttonBg
        buttonText: Theme.ink
        highlight: Theme.selectionBlue
        highlightedText: Theme.panelSelectionText
        placeholderText: Theme.placeholderText
        mid: Theme.chromeBorder
        light: Theme.shadeLight
        dark: Theme.shadeDark
    }

    property var keszletek: []
    property int kivalasztott: -1          // a lista sorindexe
    property bool szerkesztes: false       // új/módosítás űrlap látszik-e
    property int szerkesztettId: -1        // -1 = új készlet
    property string urlapNev: ""
    property string urlapCel: ""
    property string urlapSzuro: "minden"
    //: #3593: a készlet TÍPUSA (`newbackupset.fen`): "cddvd" · "lemez"
    property string urlapTipus: "lemez"
    //: #3593: a kiválasztott készlet típusa — ettől függ, mit ír a futás
    readonly property string valasztottTipus:
        backupWindow.kivalasztott >= 0
        && backupWindow.kivalasztott < backupWindow.keszletek.length
        ? (backupWindow.keszletek[backupWindow.kivalasztott].tipus || "lemez")
        : "lemez"
    property string uzenet: ""

    //: #3594: a kiválasztott készlet még el nem mentett fájljai, mappánként
    //: (`backupController.mentetlenMappakLekerese` → `mentetlenMappakKeszek`)
    property var mentetlenek: []
    //: #3594: a bepipált mappák útjai — csak ezeket viszi a futás
    property var pipaltMappak: []
    //: #3594: a lista háttérszálon készül (nagy gyűjteménynél percekig);
    //: amíg nem jön meg, a „Számítás…" felirat látszik
    property bool mappakToltodnek: false
    //: a legutóbbi lekérdezés sorszáma — a régebbi válasz nem írja felül
    property int mappaKeres: 0
    //: #3594: a 2. lépés csak kiválasztott készletnél, űrlapon kívül él
    readonly property bool mappaLepes:
        !backupWindow.szerkesztes && backupWindow.kivalasztott >= 0
        && backupWindow.kivalasztott < backupWindow.keszletek.length

    //: másik készlet = más nyilvántartás, a régi pipák nem érvényesek
    onKivalasztottChanged: {
        backupWindow.pipaltMappak = []
        backupWindow.frissitsdAMappakat()
    }

    function frissitsdAMappakat() {
        if (typeof backupController === "undefined" || !backupController
                || backupWindow.kivalasztott < 0
                || backupWindow.kivalasztott >= backupWindow.keszletek.length) {
            //: a függő válasz se érkezzen meg később
            backupWindow.mappaKeres = -1
            backupWindow.mappakToltodnek = false
            backupWindow.mentetlenek = []
            backupWindow.pipaltMappak = []
            return
        }
        //: a régi lista elavult (pl. futás után a már elmentett mappa is
        //: benne van) — ne lehessen belőle pipálni, amíg az új nem jön meg.
        //: A pipák maradnak; a válasz a még élő mappákra szűkíti őket.
        backupWindow.mentetlenek = []
        backupWindow.mappakToltodnek = true
        backupWindow.mappaKeres = backupController.mentetlenMappakLekerese(
            backupWindow.keszletek[backupWindow.kivalasztott].id)
    }

    //: a háttérszál válasza — csak a legutóbbi kérésé számít
    function fogadjAMappakat(keres, keszletId, sorok) {
        if (keres !== backupWindow.mappaKeres) return
        backupWindow.mentetlenek = sorok
        backupWindow.mappakToltodnek = false
        //: a már elmentett (eltűnt) mappa pipája sem maradhat meg
        var elo = sorok.map(function (sor) { return sor.mappa })
        backupWindow.pipaltMappak = backupWindow.pipaltMappak.filter(
            function (mappa) { return elo.indexOf(mappa) >= 0 })
    }

    function pipald(mappa, be) {
        var uj = backupWindow.pipaltMappak.filter(
            function (m) { return m !== mappa })
        if (be) uj.push(mappa)
        backupWindow.pipaltMappak = uj
    }

    //: `publish/selectall` — „Az összes kijelölése"
    function mindetPipald() {
        backupWindow.pipaltMappak = backupWindow.mentetlenek.map(
            function (sor) { return sor.mappa })
    }

    //: `publish/selectnone` — „Az összes kijelölés megszüntetése"
    function egyiketSemPipald() {
        backupWindow.pipaltMappak = []
    }

    readonly property var szuroKulcsok: ["minden", "kepek", "fenykepezogep"]
    readonly property var szuroFeliratok: [
        qsTr("All file types"),
        qsTr("All pictures (no movies)"),
        qsTr("Only JPEGs with camera data"),
    ]

    function frissitsd() {
        if (typeof backupController === "undefined" || !backupController)
            return
        backupWindow.keszletek = backupController.keszletek()
        var elozo = backupWindow.kivalasztott
        if (backupWindow.kivalasztott >= backupWindow.keszletek.length)
            backupWindow.kivalasztott = backupWindow.keszletek.length - 1
        //: ha a kiválasztás átállt, az `onKivalasztottChanged` már kért
        //: listát — még egy lekérdezés fölösleges bejárás volna
        if (backupWindow.kivalasztott === elozo)
            backupWindow.frissitsdAMappakat()
    }

    function open() {
        backupWindow.uzenet = ""
        backupWindow.szerkesztes = false
        backupWindow.frissitsd()
        backupWindow.visible = true
    }

    function ujKeszletUrlap() {
        backupWindow.szerkesztettId = -1
        //: #3189: az eredeti NEM üres mezővel indít — a panel feltöltője
        //: (`0x006706d0`) a szövegtárból veszi az alapnevet
        //: (`il_BurnPanel::bksetname`, „My Backup Set" /
        //: „Saját mentési készlet"), ld. `biztonsagi-mentes.md` 9.
        backupWindow.urlapNev = qsTr("My Backup Set")
        backupWindow.urlapCel = ""
        backupWindow.urlapSzuro = "minden"
        backupWindow.urlapTipus = "lemez"
        backupWindow.szerkesztes = true
    }

    function szerkesztoUrlap() {
        if (backupWindow.kivalasztott < 0) return
        var k = backupWindow.keszletek[backupWindow.kivalasztott]
        backupWindow.szerkesztettId = k.id
        backupWindow.urlapNev = k.nev
        backupWindow.urlapCel = k.cel
        backupWindow.urlapSzuro = k.szuro
        backupWindow.urlapTipus = k.tipus || "lemez"
        backupWindow.szerkesztes = true
    }

    function mentsdAzUrlapot() {
        if (typeof backupController === "undefined" || !backupController)
            return
        var rendben = backupWindow.szerkesztettId < 0
            ? backupController.ujKeszlet(backupWindow.urlapNev,
                                         backupWindow.urlapCel,
                                         backupWindow.urlapSzuro,
                                         backupWindow.urlapTipus)
            : backupController.modositsdAKeszletet(backupWindow.szerkesztettId,
                                                   backupWindow.urlapNev,
                                                   backupWindow.urlapCel,
                                                   backupWindow.urlapSzuro,
                                                   backupWindow.urlapTipus)
        if (rendben) {
            backupWindow.szerkesztes = false
            backupWindow.frissitsd()
        }
    }

    Connections {
        target: (typeof backupController !== "undefined") ? backupController : null
        function onHibatJelez(szoveg) { backupWindow.uzenet = szoveg }
        function onKeszletekValtoztak() { backupWindow.frissitsd() }
        function onMentetlenMappakKeszek(keres, keszletId, sorok) {
            backupWindow.fogadjAMappakat(keres, keszletId, sorok)
        }
        function onFutasKesz(darab, bajt) {
            backupWindow.fut = false
            //: #3189, #3573: a mért záró üzenet `il_BurnPanel::BackupCopy::3`
            //: („Backup Complete" / „A mentés elkészült") — az eredeti EGY
            //: záró üzenetet ismer, akkor is, ha nem volt mit másolni. A
            //: darabszám a másolás közbeni sorban látszik, ezért itt nem kell.
            backupWindow.uzenet = qsTr("Backup Complete")
        }
        //: #2074: a lemezkép-ág vége — a felhasználó SZÁMOKAT kap: hány
        //: lemezkép készült és hány fájl van rajtuk.
        function onLemezkepekKeszek(lemezek, fajlok) {
            backupWindow.fut = false
            backupWindow.uzenet = lemezek === 0
                ? qsTr("Everything was already backed up.")
                : qsTr("Done: %1 file(s) in %2 disc image(s).")
                    .arg(fajlok).arg(lemezek)
        }
        //: #3009: a másolás háttérszálon megy, és végig beszél — az
        //: eredeti is („Copying (%d/%d) files").
        function onFutasIndult(osszes) {
            backupWindow.fut = osszes > 0
            backupWindow.osszesFajl = osszes
            backupWindow.keszFajl = 0
        }
        function onHaladas(kesz, osszes) {
            backupWindow.keszFajl = kesz
            backupWindow.osszesFajl = osszes
            backupWindow.uzenet =
                qsTr("Copying (%1/%2) files").arg(kesz).arg(osszes)
        }
    }

    FolderDialog {
        id: celValaszto
        title: qsTr("Choose the backup location")
        onAccepted: {
            backupWindow.urlapCel = (typeof fileOpsController !== "undefined"
                                     && fileOpsController)
                ? fileOpsController.toLocalPath(celValaszto.selectedFolder.toString())
                : celValaszto.selectedFolder.toString().replace(/^file:\/\//, "")
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            //: A készlet fogalma az eredeti saját meghatározása szerint.
            text: qsTr("A backup set remembers where it saves and what it has "
                       + "already saved, so the next run only copies what is new.")
        }

        // -- a készletek listája ------------------------------------------
        Rectangle {
            Layout.fillWidth: true
            //: #3594: a mappa-lépés mellett a készlet-lista csak sávnyi
            Layout.fillHeight: !backupWindow.mappaLepes
            Layout.preferredHeight: backupWindow.mappaLepes ? 128 : -1
            color: Theme.controlBase
            border.color: Theme.chromeBorder
            border.width: 1
            radius: 2
            visible: !backupWindow.szerkesztes

            ListView {
                id: keszletLista
                objectName: "backupSetList"
                anchors.fill: parent
                anchors.margins: 1
                clip: true
                model: backupWindow.keszletek
                delegate: Rectangle {
                    required property int index
                    required property var modelData
                    width: keszletLista.width
                    height: 40
                    color: index === backupWindow.kivalasztott
                           ? Theme.panelSelection : "transparent"
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 8
                        Text {
                            text: modelData.nev
                            font.pixelSize: Theme.fontSize
                            color: index === backupWindow.kivalasztott
                                   ? Theme.panelSelectionText : Theme.ink
                        }
                        Text {
                            text: modelData.utolsoFutas.length > 0
                                  ? qsTr("%1 — last run: %2").arg(modelData.cel)
                                        .arg(modelData.utolsoFutas)
                                  : qsTr("%1 — not run yet").arg(modelData.cel)
                            font.pixelSize: Theme.fontSize - 2
                            color: Theme.textGray
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: backupWindow.kivalasztott = index
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: backupWindow.keszletek.length === 0
                text: qsTr("No backup sets yet.")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
        }

        // -- #3594: 2. lépés — a mentetlen mappák, pipával ------------------
        //: a MÉRT feliratok (`publish/backupcdheader2`, `backuptext2`,
        //: `backuptext3`, `selectall`, `selectnone`; `biztonsagi-mentes.md`
        //: 10.3, `ui-lefedettseg.md`)
        Text {
            objectName: "backupFolderHeader"
            Layout.fillWidth: true
            visible: backupWindow.mappaLepes
            text: qsTr("Choose folders & albums to back up")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
        }
        Text {
            objectName: "backupFolderText"
            Layout.fillWidth: true
            visible: backupWindow.mappaLepes
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            text: qsTr("Picasa is now showing the files you have not previously backed up.")
                  + " "
                  + qsTr("Check the folders you want to back up, or choose 'Select All' to choose everything.")
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: backupWindow.mappaLepes
            color: Theme.controlBase
            border.color: Theme.chromeBorder
            border.width: 1
            radius: 2

            ListView {
                id: mappaLista
                objectName: "backupFolderList"
                anchors.fill: parent
                anchors.margins: 1
                clip: true
                model: backupWindow.mentetlenek
                ScrollBar.vertical: ScrollBar {}
                delegate: RowLayout {
                    id: mappaSor
                    required property var modelData
                    width: mappaLista.width
                    spacing: 6
                    CheckBox {
                        objectName: "backupFolderCheck"
                        text: mappaSor.modelData.nev
                        font.pixelSize: Theme.fontSize
                        checked: backupWindow.pipaltMappak
                                 .indexOf(mappaSor.modelData.mappa) >= 0
                        onToggled: {
                            backupWindow.pipald(mappaSor.modelData.mappa,
                                                checked)
                            //: a kattintás elvágja a kötést — vissza kell
                            //: kötni, különben a „kijelölés megszüntetése"
                            //: nem venné le ezt a pipát
                            checked = Qt.binding(function () {
                                return backupWindow.pipaltMappak
                                    .indexOf(mappaSor.modelData.mappa) >= 0
                            })
                        }
                    }
                    //: a mappa még el nem mentett fájljai — ez a „rács".
                    //: A vezérlő csak az első néhány nevet adja; ha több
                    //: van, a darabszám mellett „…" jelzi a folytatást.
                    Text {
                        objectName: "backupFolderFiles"
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        font.pixelSize: Theme.fontSize - 1
                        color: Theme.textGray
                        text: "(" + mappaSor.modelData.darab + ")  "
                              + mappaSor.modelData.fajlok.join(", ")
                              + (mappaSor.modelData.darab
                                 > mappaSor.modelData.fajlok.length
                                 ? ", …" : "")
                    }
                }
            }

            //: #3594: amíg a háttérszál számol — `il_BurnPanel::calculating`
            //: („Calculating…" / „Számítás…", `biztonsagi-mentes.md` 15.7)
            Text {
                objectName: "backupFolderLoading"
                anchors.centerIn: parent
                visible: backupWindow.mappakToltodnek
                text: qsTr("Calculating…")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }

            Text {
                anchors.centerIn: parent
                visible: !backupWindow.mappakToltodnek
                         && backupWindow.mentetlenek.length === 0
                text: qsTr("Everything was already backed up.")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
        }
        RowLayout {
            Layout.fillWidth: true
            visible: backupWindow.mappaLepes
            spacing: 8
            PicasaButton {
                objectName: "backupSelectAll"
                text: qsTr("Select All")
                enabled: backupWindow.mentetlenek.length > 0
                onClicked: backupWindow.mindetPipald()
            }
            PicasaButton {
                objectName: "backupSelectNone"
                text: qsTr("Select None")
                enabled: backupWindow.pipaltMappak.length > 0
                onClicked: backupWindow.egyiketSemPipald()
            }
            Item { Layout.fillWidth: true }
        }

        // -- új / módosítás űrlap ------------------------------------------
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            visible: backupWindow.szerkesztes
            columnSpacing: 8
            rowSpacing: 8

            //: #3189: a MÉRT felirat — `publish/label_backupname`
            //: (`publish_text.tre:93`, „Backup Set" / „Mentési készlet").
            //: A korábbi „Name:" saját fogalmazás volt.
            Text {
                text: qsTr("Backup Set")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                objectName: "backupSetName"
                Layout.fillWidth: true
                text: backupWindow.urlapNev
                font.pixelSize: Theme.fontSize
                onTextEdited: backupWindow.urlapNev = text
                // #422: jobbklikk-menü minden szövegmezőn (a `Address`
                // megfelelője az eredetiben)
                TextFieldContextArea {}
            }

            //: #3593: MÉRT (`newbackupset.fen`): „Backup type:" és a két
            //: rádió. A „Choose…" csak a lemez-lemez típusnál él (a
            //: `.fen` `bind attr="enabled" source="type"` sora).
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
                    checked: backupWindow.urlapTipus === "cddvd"
                    onClicked: backupWindow.urlapTipus = "cddvd"
                }
                RadioButton {
                    objectName: "backupTypeDisk"
                    text: qsTr("Disk-to-disk backup (for external and network drives)")
                    font.pixelSize: Theme.fontSize
                    checked: backupWindow.urlapTipus === "lemez"
                    onClicked: {
                        //: a CD/DVD-típus helye (a lemezkép-alaphely) nem
                        //: maradhat itt mappának — a mező üresen vár
                        if (backupWindow.urlapTipus === "cddvd"
                                && typeof backupController !== "undefined"
                                && backupController
                                && backupWindow.urlapCel
                                   === backupController.lemezkepAlapHely())
                            backupWindow.urlapCel = ""
                        backupWindow.urlapTipus = "lemez"
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
                //: CD/DVD-típusnál a lemezkép a vezérlő alaphelyére kerül —
                //: a mező azt mutatja, és nem szerkeszthető
                TextField {
                    objectName: "backupSetTarget"
                    Layout.fillWidth: true
                    enabled: backupWindow.urlapTipus === "lemez"
                    text: backupWindow.urlapTipus === "lemez"
                          ? backupWindow.urlapCel
                          : ((typeof backupController !== "undefined"
                              && backupController)
                             ? backupController.lemezkepAlapHely() : "")
                    font.pixelSize: Theme.fontSize
                    onTextEdited: backupWindow.urlapCel = text
                    // #422: jobbklikk-menü minden szövegmezőn
                    TextFieldContextArea {}
                }
                PicasaButton {
                    objectName: "backupChooseTarget"
                    //: MÉRT felirat: `newbackupset/disk` („Choose...")
                    text: qsTr("Choose...")
                    enabled: backupWindow.urlapTipus === "lemez"
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
                model: backupWindow.szuroFeliratok
                currentIndex: backupWindow.szuroKulcsok.indexOf(backupWindow.urlapSzuro)
                onActivated: backupWindow.urlapSzuro =
                             backupWindow.szuroKulcsok[currentIndex]
            }
        }

        Text {
            objectName: "backupMessage"
            Layout.fillWidth: true
            visible: backupWindow.uzenet.length > 0
            text: backupWindow.uzenet
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        //: #3009: haladás-sáv — csak a másolás alatt látszik
        Rectangle {
            objectName: "backupProgressTrack"
            visible: backupWindow.fut
            Layout.fillWidth: true
            Layout.preferredHeight: 6
            radius: 3
            color: Theme.chromeBorder
            Rectangle {
                objectName: "backupProgressFill"
                height: parent.height
                radius: parent.radius
                color: Theme.selectionBlue
                width: backupWindow.osszesFajl > 0
                    ? parent.width * backupWindow.keszFajl
                      / backupWindow.osszesFajl
                    : 0
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            PicasaButton {
                objectName: "backupNewSet"
                visible: !backupWindow.szerkesztes
                text: qsTr("New Set...")
                onClicked: backupWindow.ujKeszletUrlap()
            }
            PicasaButton {
                objectName: "backupEditSet"
                visible: !backupWindow.szerkesztes
                enabled: backupWindow.kivalasztott >= 0
                text: qsTr("Edit Set...")
                onClicked: backupWindow.szerkesztoUrlap()
            }
            PicasaButton {
                objectName: "backupDeleteSet"
                visible: !backupWindow.szerkesztes
                enabled: backupWindow.kivalasztott >= 0
                text: qsTr("Delete Set")
                onClicked: {
                    var k = backupWindow.kivalasztott >= 0
                        ? backupWindow.keszletek[backupWindow.kivalasztott] : null
                    //: `il_NewBkDialog_delete` — az eredeti szövege, a
                    //: készlet nevével (#3573)
                    torlesMegerosites.ask(
                        "", qsTr("Are you sure you want to delete the backup set \"%1\"?")
                                .arg(k ? k.nev : ""))
                }
            }
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "backupCancelRun"
                //: #3009: a megszakított mentés nem veszít el munkát — a
                //: már átmásolt fájlok a nyilvántartásba kerülnek, a
                //: következő futás pontosan a hiányzókat viszi.
                visible: backupWindow.fut
                text: qsTr("Stop")
                onClicked: {
                    if (typeof backupController !== "undefined"
                            && backupController)
                        backupController.szakitsdMeg()
                }
            }
            //: #2074: a lemezkép MÉRETE. A tulajdonos döntése (2026-09-18):
            //: a mentés mehet lemezképbe is, és ha nem fér el egyre, több,
            //: sorszámozott képre oszlik. Fizikai lemezírás NINCS.
            //: #3593: a kimenet fajtáját a KÉSZLET TÍPUSA dönti el (mappa a
            //: lemez-lemez, lemezkép a CD/DVD-típusnál); itt csak az marad
            //: választható, amit lemez híján nem lehet tudni: CD vagy DVD.
            ComboBox {
                //: az `id` hiányzott: a Mentés gomb erre hivatkozott, és a
                //: feloldatlan név miatt a futás el sem indult
                id: backupOutputMode
                objectName: "backupOutputMode"
                visible: !backupWindow.szerkesztes && !backupWindow.fut
                         && backupWindow.valasztottTipus === "cddvd"
                //: a legszélesebb felirathoz méreteződik — különben levágódik
                implicitContentWidthPolicy: ComboBox.WidestText
                model: [
                    qsTr("To CD image (ISO)"),
                    qsTr("To DVD image (ISO)"),
                ]
                //: a `burn` modul médiatípus-kulcsai — a felirat sorrendjével
                readonly property var mediak: ["cd", "dvd"]
            }
            PicasaButton {
                objectName: "backupRun"
                visible: !backupWindow.szerkesztes && !backupWindow.fut
                //: #3594: pipa nélkül nincs mit menteni
                enabled: backupWindow.kivalasztott >= 0
                         && backupWindow.pipaltMappak.length > 0
                text: qsTr("Back Up")
                onClicked: {
                    if (typeof backupController === "undefined" || !backupController)
                        return
                    var k = backupWindow.keszletek[backupWindow.kivalasztott]
                    //: #3594: csak a bepipált mappák
                    var mappak = backupWindow.pipaltMappak
                    var terv = backupController.terv(k.id, mappak)
                    //: #2074: a lemezszám-becslés is látszik, ahogy az
                    //: eredetiben („Est. %d CDs or %d DVDs") — a kapacitás
                    //: a mért képletből jön.
                    //: #3573: nincs mit másolni — az eredeti ilyenkor is a
                    //: záró „Backup Complete" üzenetet mutatja.
                    backupWindow.uzenet = terv.darab === 0
                        ? qsTr("Backup Complete")
                        : qsTr("Copying %1 file(s)... (%2 CD or %3 DVD)")
                            .arg(terv.darab).arg(terv.cd).arg(terv.dvd)
                    if (backupWindow.valasztottTipus !== "cddvd") {
                        backupController.futtasdMost(k.id, mappak)
                        return
                    }
                    //: a lemezkép-ág a MÉRT kapacitással oszt lemezekre
                    backupWindow.uzenet = terv.darab === 0
                        ? qsTr("Backup Complete")
                        : qsTr("Writing %1 file(s) to disc image(s)...")
                            .arg(terv.darab)
                    backupController.futtasdLemezkepbe(
                        k.id,
                        backupOutputMode.mediak[backupOutputMode.currentIndex],
                        mappak)
                }
            }
            PicasaButton {
                objectName: "backupFormSave"
                visible: backupWindow.szerkesztes
                //: #3189: SZERKESZTÉSKOR a mért felirat „Change"
                //: (`il_NewBkDialog::EditOKButton` / „Módosítás"); ÚJ
                //: készletnél az eredetinek nincs mért felirata, ott
                //: marad az „OK".
                text: backupWindow.szerkesztettId >= 0
                    ? qsTr("Change") : qsTr("OK")
                onClicked: backupWindow.mentsdAzUrlapot()
            }
            PicasaButton {
                objectName: "backupFormCancel"
                visible: backupWindow.szerkesztes
                text: qsTr("Cancel")
                onClicked: backupWindow.szerkesztes = false
            }
            PicasaButton {
                objectName: "backupClose"
                visible: !backupWindow.szerkesztes
                text: qsTr("Close")
                onClicked: backupWindow.visible = false
            }
        }
    }

    ConfirmDialog {
        id: torlesMegerosites
        namePrefix: "backupDelete"
        title: qsTr("Delete Set")
        onConfirmed: {
            if (typeof backupController === "undefined" || !backupController)
                return
            backupController.torisdAKeszletet(
                backupWindow.keszletek[backupWindow.kivalasztott].id)
            backupWindow.kivalasztott = -1
        }
    }
}
