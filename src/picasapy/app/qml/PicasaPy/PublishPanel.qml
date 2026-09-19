import QtQuick
import QtQuick.Controls

// A Picasa `publish` panelje — a MÉRT vezérlők (#2508).
//
// ## Mit ad ez a fájl, és mit NEM
//
// A panel **vezérlőit** építi meg a mért helyeken és a hivatalos magyar
// feliratokkal (`docs/specs/ajandek-cd-kimenet.md` 13. szakasz). A három
// üzemmód MŰKÖDÉSE — az Ajándék-CD kiírása, a biztonsági mentés, a
// feltöltés — külön jegy; ez a panel ezért egyelőre **nincs bekötve** a
// menübe: egy tétlen felület rosszabb volna, mint a mai, egyértelmű hiány.
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
            objectName: "publishCdName"
            x: 458; y: 83; width: 167; height: 14
            font.pixelSize: Theme.fontSize
            //: a `namelimitext` MÉRT felirata szerint 16 karakter a korlát
            maximumLength: panel.cdNevHossz
        }
        MertFelirat {
            objectName: "publishNameLimitText"
            x: 455; y: 101; width: 173; height: 14
            text: qsTr("Limit 16 Characters")
        }
        MertFelirat {
            objectName: "publishLabelOptionBox3"
            x: 390; y: 140; width: 227; height: 16
            text: qsTr("Include Picasa")
        }
        MertFelirat {
            objectName: "publishLabelOptionBox2"
            x: 390; y: 172; width: 227; height: 16
            text: qsTr("Erase Media")
        }
        //: állapotsor — a tartalmát a működés adja majd (külön jegy)
        MertFelirat {
            objectName: "publishOriginInfo"
            x: 307; y: 2; width: 197; height: 25
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
