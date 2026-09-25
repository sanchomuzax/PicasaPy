import QtQuick
import QtQuick.Controls

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

    // ------- biztonsági mentés (`backup_group`) — 3 elem -------
    Item {
        objectName: "publishBackupGroup"
        anchors.fill: parent
        visible: panel.uzemmod === "backup"

        MertKeret {
            objectName: "publishBackupRect2"
            x: 448; y: 37; width: 324; height: 166
        }
        MertFelirat {
            objectName: "publishLabelBackupName"
            x: 148; y: 134; width: 108; height: 16
            text: qsTr("Backup Set")
        }
        MertFelirat {
            objectName: "publishBackupInfo"
            x: 420; y: 2; width: 197; height: 25
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
