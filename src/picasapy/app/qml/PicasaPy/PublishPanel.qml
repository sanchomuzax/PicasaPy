import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A Picasa `publish` panelje — a MÉRT vezérlők (#2508).
//
// ## Mit ad ez a fájl, és mit NEM
//
// A panel **vezérlőit** építi meg a mért helyeken és a hivatalos magyar
// feliratokkal (`docs/specs/ajandek-cd-kimenet.md` 13. szakasz).
//
// Az **Ajándék-CD** üzemmód él (#3503): a „Létrehozás ▸ Ajándék CD
// készítése…" nyitja, és a „Lemezre írás" a képtálca elemeiből lemezképet
// készít. A panel csak JELEZ (`lemezreIrasKert`, `megseKert`,
// `tovabbiakKert`); a munkát a gazda végzi. A biztonsági mentés és a
// feltöltés üzemmódja nincs bekötve.
//
// ## A mért vászon
//
// A `respack.yt` rétegfejlécei **1024 × 212**-es vászonhoz adnak
// koordinátát. A panel ezt a vásznat viseli, tehát a gyerekek `x`/`y`-ja
// SZÓ SZERINT a mért érték — nincs átszámolás, amit el lehetne rontani.
//
// ⭐ A két lépés-keret azonos méretű (311 × 166), és a mentés-üzemmódban a
// `backuprect2` ugyanarra a helyre, szélesebben (324) kerül: a panel
// LÉPÉSEKRE osztott, és az üzemmód a keretek tartalmát cseréli.
//
// ⛔ A `web_group` hét eleme SZÁNDÉKOSAN nem készül el: a `.tre`-ben
// `m_hidden`, és online szolgáltatáshoz tartozik (hatókörön kívül).
Item {
    id: panel
    objectName: "publishPanel"

    //: a MÉRT vászon (`respack.yt`) — a gyerekek koordinátái ehhez szólnak
    readonly property int vaszonSzelesseg: 1024
    readonly property int vaszonMagassag: 212
    implicitWidth: vaszonSzelesseg
    implicitHeight: vaszonMagassag
    width: implicitWidth
    height: implicitHeight

    //: melyik üzemmód látszik: "cd" · "backup" · "upload"
    property string uzemmod: "cd"

    //: a `namelimitext` MÉRT felirata mondja ki: legfeljebb 16 karakter
    readonly property int cdNevHossz: 16

    //: #3503: hány elem van a képtálcán — üres tálcával nincs mit írni
    property int elemekSzama: 0
    //: #3503: amíg a lemezkép készül, a „Lemezre írás" nem nyomható újra
    property bool dolgozik: false
    //: #3503: a „Lemezre írás" — a választott méretfokozat indexe
    //: (0 = eredeti · 640 · 800 · 1600, spec 12.4) és a CD neve
    signal lemezreIrasKert(int meretIndex, string cdNev)
    //: #3503: `publish/presentcd_cancel` — vissza a könyvtárba
    signal megseKert()
    //: #3503: `publish/addmore` — vissza a könyvtárba, hogy a tálcára
    //: további elemek kerülhessenek
    signal tovabbiakKert()

    // ---- #3504: mentés-üzemmód — a panel BEMENETEI (a `BackupHost` tölti) ----
    //: a készletek QML-alakban (`BackupController.keszletek()`)
    property var mentesKeszletek: []
    //: a kiválasztott készlet SORINDEXE a `mentesKeszletek`-ben, -1 = nincs
    property int mentesKivalasztottIndex: -1
    //: #3594: a kiválasztott készlet még el nem mentett fájljai, mappánként
    property var mentesMentetlenek: []
    //: #3594: a bepipált mappák útjai
    property var mentesPipaltMappak: []
    //: #3594: a mappa-lista háttérszálon készül — amíg nem jön meg
    property bool mentesMappakToltodnek: false
    //: #3009: fut-e éppen másolás
    property bool mentesFut: false
    //: #3009: a haladás-sáv számlálói
    property int mentesKeszFajl: 0
    property int mentesOsszesFajl: 0
    //: állapotsor / haladás-üzenet (`publishBackupInfo`)
    property string mentesUzenet: ""
    readonly property bool mentesVanKivalasztva:
        panel.mentesKivalasztottIndex >= 0
        && panel.mentesKivalasztottIndex < panel.mentesKeszletek.length
    //: #3593: a kiválasztott készlet típusa — ettől függ, kell-e a
    //: lemezkép-méret választó
    readonly property string mentesValasztottTipus:
        panel.mentesVanKivalasztva
        ? (panel.mentesKeszletek[panel.mentesKivalasztottIndex].tipus || "lemez")
        : "lemez"

    // ---- #3504: mentés-üzemmód — a panel KIMENETEI (a `BackupHost` fogadja) ----
    //: `publish/newbackupset`
    signal mentesUjKeszletKert()
    //: `publish/editbackupset`
    signal mentesSzerkesztKert()
    //: `publish/deletebackupset`
    signal mentesTorolKert()
    //: `publish/backup_set_menu` — a felhasználó másik készletet választott
    signal mentesKeszletValasztva(int index)
    //: egy mappa pipája vált
    signal mentesPipaldKert(string mappa, bool be)
    //: `publish/selectall`
    signal mentesMindetPipaldKert()
    //: `publish/selectnone`
    signal mentesSenkitSePipaldKert()
    //: `publish/backup_go` — `media`: "" (mappa) vagy "cd"/"dvd" (lemezkép)
    signal mentesFuttatasKert(string media)
    //: #3009: a futó másolás megszakítása
    signal mentesMegszakitasKert()
    //: `publish/backup_cancel`
    signal mentesMegseKert()

    component MertFelirat: Text {
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    component MertKeret: Rectangle {
        color: "transparent"
        border.width: 1
        border.color: Theme.chromeBorder
    }

    // ------- Ajándék-CD (`presentation_group`) — 11 elem -------
    Item {
        objectName: "publishPresentationGroup"
        anchors.fill: parent
        visible: panel.uzemmod === "cd"

        MertKeret {
            objectName: "publishStep1"
            x: 15; y: 37; width: 311; height: 166
        }
        MertKeret {
            objectName: "publishStep2"
            x: 337; y: 37; width: 311; height: 166
        }
        MertFelirat {
            objectName: "publishSelectionText"
            x: 55; y: 43; width: 251; height: 18
            text: qsTr("Selection and Settings")
        }
        MertFelirat {
            objectName: "publishPicSizeText"
            x: 35; y: 169; width: 137; height: 18
            text: qsTr("Photo Size")
        }
        //: #3503: `publish/giftcdtext` (35,74 – 306,125) — a MÉRT
        //: útmutató szöveg (`publish_text.tre:5`)
        MertFelirat {
            objectName: "publishGiftCdText"
            x: 35; y: 74; width: 271; height: 51
            wrapMode: Text.WordWrap
            elide: Text.ElideNone
            verticalAlignment: Text.AlignTop
            //: a hivatalos magyar szöveg hosszabb az angolnál — a mért
            //: 271 × 51-es dobozba kicsinyítve fér, nem lóg a gombra
            fontSizeMode: Text.Fit
            minimumPixelSize: 8
            text: qsTr("The items selected with a checkmark above will be included on your Gift CD.   To add more items click the \"Add More\" button below.")
        }
        //: #3503: `publish/addmore` (35,130 – 123,158), `b88` gomb
        PicasaButton {
            objectName: "publishAddMore"
            x: 35; y: 130; width: 88; height: 28
            text: qsTr("Add More...")
            onClicked: panel.tovabbiakKert()
        }
        //: #3503: `publish/picsizemenu` (177,168 – 306,189) — a négy MÉRT
        //: fokozat (`0x0066f658`–`0x0066f670`), a `CPublishSizeList`
        //: feliratokkal
        ComboBox {
            id: meretValaszto
            objectName: "publishPicSizeMenu"
            x: 177; y: 168; width: 129; height: 21
            font.pixelSize: Theme.fontSize
            model: [qsTr("Original Size"), qsTr("640 x 480"),
                    qsTr("800 x 600"), qsTr("1600 x 1200")]
        }
        MertFelirat {
            objectName: "publishCdNameText"
            x: 377; y: 43; width: 251; height: 18
            text: qsTr("Name the Gift CD")
        }
        MertFelirat {
            objectName: "publishLabelCdName"
            x: 357; y: 81; width: 93; height: 14
            text: qsTr("CD Name")
        }
        TextField {
            id: cdNevMezo
            objectName: "publishCdName"
            x: 458; y: 83; width: 167; height: 14
            font.pixelSize: Theme.fontSize
            //: #3503: a mért mező csak 14 képpont magas — a stílus alap
            //: belső margója mellett a beírt szöveg félig kilógna belőle
            topPadding: 0
            bottomPadding: 0
            leftPadding: 2
            rightPadding: 2
            verticalAlignment: TextInput.AlignVCenter
            //: a `namelimitext` MÉRT felirata szerint 16 karakter a korlát
            maximumLength: panel.cdNevHossz
            //: minden szövegmezőnek jár a jobbklikk-menü (#422) — a
            //: forrás-szintű őr ezt meg is követeli
            TextFieldContextArea {}
        }
        MertFelirat {
            objectName: "publishNameLimitText"
            x: 455; y: 101; width: 173; height: 14
            text: qsTr("Limit 16 Characters")
        }
        //: #3503: a két felirat jelölőnégyzete (`optionbox3`, `optionbox2`)
        //: SZÁNDÉKOSAN nincs meg: a telepítő a lemezre és az újraírható
        //: lemez törlése lemezkép-kimenetnél nem értelmezhető (spec 6.,
        //: 13.). Négyzet nélkül a felirat olyan funkciót ígérne, ami nincs
        //: — ezért a feliratok is rejtve állnak, a mért helyükön.
        MertFelirat {
            objectName: "publishLabelOptionBox3"
            x: 390; y: 140; width: 227; height: 16
            visible: false
            text: qsTr("Include Picasa")
        }
        MertFelirat {
            objectName: "publishLabelOptionBox2"
            x: 390; y: 172; width: 227; height: 16
            visible: false
            text: qsTr("Erase Media")
        }
        //: állapotsor — a tartalmát a működés adja majd (külön jegy)
        MertFelirat {
            objectName: "publishOriginInfo"
            x: 307; y: 2; width: 197; height: 25
        }
        //: #3503: `publish/presentcd_go` (664,37 – 762,65) — „Lemezre írás"
        PicasaButton {
            objectName: "publishPresentCdGo"
            x: 664; y: 37; width: 98; height: 28
            text: qsTr("Burn Disc")
            enabled: panel.elemekSzama > 0 && !panel.dolgozik
            onClicked: panel.lemezreIrasKert(meretValaszto.currentIndex,
                                             cdNevMezo.text)
        }
        //: #3503: `publish/presentcd_cancel` (664,111 – 762,139) — „Mégse"
        PicasaButton {
            objectName: "publishPresentCdCancel"
            x: 664; y: 111; width: 98; height: 28
            text: qsTr("Cancel")
            onClicked: panel.megseKert()
        }
    }

    // ------- biztonsági mentés (`backup_group`) — #3504 -------
    //
    // A csoport két lépés-keretre oszlik, ahogy az eredetiben (12.4. kép a
    // jegyben, `docs/specs/ajandek-cd-kimenet.md` 13. és
    // `docs/specs/biztonsagi-mentes.md` 10.–15.):
    //
    //   1. lépés (`backuprect`, 128,37 311×166): melyik KÉSZLETET mentjük —
    //      legördülő + Új/Módosítás/Törlés.
    //   2. lépés (`backuprect2`, 448,37 324×166, #3594): MELYIK MAPPÁK —
    //      a még el nem mentett mappák, pipával.
    //
    // A panel itt is csak JELEZ; az állapotot és a `backupController`
    // hívásait a `BackupHost.qml` tartja (a `GiftCdHost` mintája).
    Item {
        objectName: "publishBackupGroup"
        anchors.fill: parent
        visible: panel.uzemmod === "backup"

        // -- 1. lépés: melyik készlet ---------------------------------
        MertKeret {
            objectName: "publishBackupRect"
            x: 128; y: 37; width: 311; height: 166
        }
        //: `publish/backupcdheader` — kétállapotú (15.3/4. pont): a
        //: hivatalos magyar mindkét állapotra mérve (`Text1`/`Text2`)
        MertFelirat {
            objectName: "publishBackupCdHeader"
            x: 168; y: 43; width: 250; height: 13
            font.bold: true
            text: panel.mentesVanKivalasztva
                ? qsTr("Create a Set or use an existing one")
                : qsTr("Create a Backup CD")
        }
        //: `publish/backup_set_menu` (269,134 – 420,155) — rejtve, ha
        //: nincs egyetlen készlet sem (15.3/3. pont)
        ComboBox {
            id: keszletValaszto
            objectName: "publishBackupSetMenu"
            x: 269; y: 134; width: 151; height: 21
            font.pixelSize: Theme.fontSize
            visible: panel.mentesKeszletek.length > 0
            model: panel.mentesKeszletek.map(function (k) { return k.nev })
            currentIndex: panel.mentesKivalasztottIndex
            onActivated: panel.mentesKeszletValasztva(currentIndex)
        }
        //: `publish/newbackupset` (150,162 – 238,190)
        PicasaButton {
            objectName: "publishNewBackupSet"
            x: 150; y: 162; width: 88; height: 28
            text: qsTr("New Set...")
            onClicked: panel.mentesUjKeszletKert()
        }
        //: `publish/editbackupset` (241,162 – 329,190)
        PicasaButton {
            objectName: "publishEditBackupSet"
            x: 241; y: 162; width: 88; height: 28
            text: qsTr("Edit Set...")
            enabled: panel.mentesVanKivalasztva
            onClicked: panel.mentesSzerkesztKert()
        }
        //: `publish/deletebackupset` (332,162 – 420,190) — rejtve, ha a
        //: készletek száma legfeljebb egy (15.3/2. pont)
        PicasaButton {
            objectName: "publishDeleteBackupSet"
            x: 332; y: 162; width: 88; height: 28
            text: qsTr("Delete Set")
            visible: panel.mentesKeszletek.length > 1
            enabled: panel.mentesVanKivalasztva
            onClicked: panel.mentesTorolKert()
        }
        MertFelirat {
            objectName: "publishLabelBackupName"
            x: 148; y: 134; width: 108; height: 16
            text: qsTr("Backup Set")
        }

        // -- 2. lépés: mely mappák (#3594) ----------------------------
        MertKeret {
            objectName: "publishBackupRect2"
            x: 448; y: 37; width: 324; height: 166
        }
        //: `publish/backupcdheader2` (490,43 – 740,56)
        MertFelirat {
            objectName: "publishBackupCdHeader2"
            x: 490; y: 43; width: 250; height: 13
            font.bold: true
            text: qsTr("Choose folders & albums to back up")
        }
        //: `publish/backuptext2` — a tartalma mérve
        //: (`biztonsagi-mentes.md` 10.3), a pontos y-sora a 14.1 táblából
        //: hiányzik: a fejléc (43…56) és a `backuptext3` (108…143) közé
        //: illesztve, becsült magassággal.
        MertFelirat {
            objectName: "publishBackupText2"
            x: 460; y: 60; width: 300; height: 32
            wrapMode: Text.WordWrap
            text: qsTr("Picasa is now showing the files you have not previously backed up.")
        }
        //: `publish/backuptext3` (470,108 – 741,143)
        MertFelirat {
            objectName: "publishBackupText3"
            x: 470; y: 108; width: 271; height: 35
            wrapMode: Text.WordWrap
            text: qsTr("Check the folders you want to back up, or choose 'Select All' to choose everything.")
        }
        Rectangle {
            x: 460; y: 145; width: 300; height: 40
            color: Theme.controlBase
            border.width: 1
            border.color: Theme.chromeBorder

            ListView {
                id: mappaLista
                objectName: "publishBackupFolderList"
                anchors.fill: parent
                anchors.margins: 1
                clip: true
                model: panel.mentesMentetlenek
                ScrollBar.vertical: ScrollBar {}
                delegate: RowLayout {
                    id: mappaSor
                    required property var modelData
                    width: mappaLista.width
                    spacing: 6
                    CheckBox {
                        objectName: "publishBackupFolderCheck"
                        text: mappaSor.modelData.nev
                        font.pixelSize: Theme.fontSize
                        checked: panel.mentesPipaltMappak
                                 .indexOf(mappaSor.modelData.mappa) >= 0
                        onToggled: {
                            panel.mentesPipaldKert(mappaSor.modelData.mappa,
                                                   checked)
                            //: a kattintás elvágja a kötést — a
                            //: `mentesPipaltMappak` a hosztból jön vissza
                            checked = Qt.binding(function () {
                                return panel.mentesPipaltMappak
                                    .indexOf(mappaSor.modelData.mappa) >= 0
                            })
                        }
                    }
                    Text {
                        objectName: "publishBackupFolderFiles"
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        color: Theme.ink
                        font.pixelSize: Theme.fontSize - 1
                        text: "(" + mappaSor.modelData.darab + ")  "
                              + mappaSor.modelData.fajlok.join(", ")
                              + (mappaSor.modelData.darab
                                 > mappaSor.modelData.fajlok.length
                                 ? ", …" : "")
                    }
                }
            }

            //: #3594: amíg a háttérszál számol —
            //: `il_BurnPanel::calculating` (biztonsagi-mentes.md 15.7)
            Text {
                objectName: "publishBackupFolderLoading"
                anchors.centerIn: parent
                visible: panel.mentesMappakToltodnek
                text: qsTr("Calculating…")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            Text {
                anchors.centerIn: parent
                visible: !panel.mentesMappakToltodnek
                         && panel.mentesMentetlenek.length === 0
                text: qsTr("Everything was already backed up.")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
        }
        RowLayout {
            x: 460; y: 187; width: 300; height: 16
            spacing: 8
            PicasaButton {
                objectName: "publishBackupSelectAll"
                text: qsTr("Select All")
                enabled: panel.mentesMentetlenek.length > 0
                onClicked: panel.mentesMindetPipaldKert()
            }
            PicasaButton {
                objectName: "publishBackupSelectNone"
                text: qsTr("Select None")
                enabled: panel.mentesPipaltMappak.length > 0
                onClicked: panel.mentesSenkitSePipaldKert()
            }
        }

        // -- gombsor (777,37…203) — a `_go`/`_eject`/`_cancel`/`_help`
        //    négyes MÓD-FÜGGŐ RÉSE (spec 11.4); a fizikai kiadás és a
        //    súgó Linuxon nincs bekötve (mint a CD-üzemmódban, spec 6.,
        //    13.) — a réseiket a lemezkép-méret és a Megszakítás kapja.
        MertFelirat {
            objectName: "publishBackupInfo"
            x: 420; y: 2; width: 197; height: 25
            text: panel.mentesUzenet
        }
        //: #3009: haladás-sáv — csak a másolás alatt látszik
        Rectangle {
            objectName: "publishBackupProgressTrack"
            x: 420; y: 28; width: 197; height: 4
            radius: 2
            color: Theme.chromeBorder
            visible: panel.mentesFut
            Rectangle {
                radius: parent.radius
                height: parent.height
                color: Theme.selectionBlue
                width: panel.mentesOsszesFajl > 0
                    ? parent.width * panel.mentesKeszFajl
                      / panel.mentesOsszesFajl
                    : 0
            }
        }
        //: `publish/backup_go` (777,37 – 875,65) — „Lemezre írás". Ugyanaz
        //: a felirat, mint a CD-üzemmódban (`publishPresentCdGo`).
        PicasaButton {
            objectName: "publishBackupGo"
            x: 777; y: 37; width: 98; height: 28
            text: qsTr("Burn Disc")
            enabled: panel.mentesPipaltMappak.length > 0 && !panel.mentesFut
            onClicked: panel.mentesFuttatasKert(
                panel.mentesValasztottTipus === "cddvd"
                ? lemezkepMeret.mediak[lemezkepMeret.currentIndex] : "")
        }
        //: #2074: a `backup_eject` réshelye — lemezkép-kimenetnél nincs
        //: kiadni való lemez (spec 6., 13.), a rést a lemezkép MÉRETE
        //: (CD/DVD) kapja, csak CD/DVD-típusú készletnél
        ComboBox {
            id: lemezkepMeret
            objectName: "publishBackupOutputMode"
            x: 777; y: 73; width: 98; height: 28
            visible: panel.mentesValasztottTipus === "cddvd" && !panel.mentesFut
            implicitContentWidthPolicy: ComboBox.WidestText
            model: [qsTr("To CD image (ISO)"), qsTr("To DVD image (ISO)")]
            readonly property var mediak: ["cd", "dvd"]
        }
        //: `publish/backup_cancel` (777,111 – 875,139) — „Mégse"
        PicasaButton {
            objectName: "publishBackupCancel"
            x: 777; y: 111; width: 98; height: 28
            text: qsTr("Cancel")
            onClicked: panel.mentesMegseKert()
        }
        //: #3009: a `backup_help` réshelye — a futó másolás megszakítása
        //: (a súgó, mint a CD-üzemmódban, nincs bekötve)
        PicasaButton {
            objectName: "publishBackupStop"
            x: 777; y: 175; width: 98; height: 28
            text: qsTr("Stop")
            visible: panel.mentesFut
            onClicked: panel.mentesMegszakitasKert()
        }
    }

    // ------- feltöltés (`replication_group`) — 7 elem -------
    Item {
        objectName: "publishReplicationGroup"
        anchors.fill: parent
        visible: panel.uzemmod === "upload"

        MertKeret {
            objectName: "publishRpOptions"
            x: 36; y: 93; width: 199; height: 99
        }
        ComboBox {
            objectName: "publishUploadAllSize"
            x: 431; y: 106; width: 139; height: 21
        }
        ComboBox {
            objectName: "publishUploadAllAccess"
            x: 431; y: 138; width: 139; height: 21
        }
        MertFelirat {
            objectName: "publishUploadSize3"
            x: 330; y: 107; width: 94; height: 16
            text: qsTr("Size:")
        }
        MertFelirat {
            objectName: "publishUploadAccess3"
            x: 330; y: 139; width: 94; height: 16
            text: qsTr("Visibility:")
        }
        MertFelirat {
            objectName: "publishUploadSync3"
            x: 330; y: 170; width: 94; height: 16
            text: qsTr("Sync:")
        }
        //: a tárhely-csík KITÖLTÉSE (a csík maga szerkezeti elem)
        Rectangle {
            objectName: "publishStorageFill"
            x: 636; y: 122; width: 253; height: 11
            color: Theme.brandBlue
        }
    }
}
