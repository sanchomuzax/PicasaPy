import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350/#32: "E-Mail" fül (options.fen). A PicasaPy-ban nincs beépített
// SMTP-kliens ("Email this photo" = a rendszer levelezőjének indítása,
// ld. `picasapy.mailer`/`email_controller.py`), DE a méret-beállítások és
// a kliens-választás élőben az `emailController`-hez kötve (#32,
// RÉSZLEGES kör — az integrátor teendője az `emailController`
// context-property regisztrálása, ld. `email_controller.py` docstringje;
// amíg az hiányzik, a null-őr miatt a mezők a mentett/alapértékkel
// jelennek meg, csak írás nem történik).
//
// A "Send movies as"/HTML-jelölő MARADT tiltott placeholder: ezek csak
// Windows/Outlook alatt értelmezettek voltak az eredetiben, és a
// PicasaPy-nak nincs videó-e-mail vagy Outlook-integrációja.
ColumnLayout {
    id: root
    spacing: 12

    // #305 mintája: a controller átmenetileg null lehet (QML-engine
    // leépítés) — és amíg az integrátor nem regisztrálja, mindig az
    readonly property var mailCtl: (typeof emailController !== "undefined")
        ? emailController : null

    Text {
        // #2432: az eredeti felirata „Levelezőprogram:”
        // (`options/labelgroup38.title`) — a korábbi „Choose your mail
        // client:” a mi fogalmazásunk volt.
        text: qsTr("Mail program:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }
    ButtonGroup { id: mailGroup }
    RadioButton {
        objectName: "optionsMailDefaultRadio"
        text: qsTr("Use this computer's default email program")
        ButtonGroup.group: mailGroup
        // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
        // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
        checked: (root.mailCtl && root.mailCtl.useDefaultClient !== undefined)
            ? root.mailCtl.useDefaultClient : true
        onToggled: if (root.mailCtl && checked) root.mailCtl.setUseDefaultClient(true)
    }
    RadioButton {
        objectName: "optionsMailChooseRadio"
        text: qsTr("Let me choose each time I send a picture")
        ButtonGroup.group: mailGroup
        checked: root.mailCtl ? !root.mailCtl.useDefaultClient : false
        onToggled: if (root.mailCtl && checked) root.mailCtl.setUseDefaultClient(false)
    }
    // #2432: az eredetiben HÁROM gomb van (`options/radio42.title` = „A
    // Google Fiók használata”). A PicasaPy-nak nincs Google-fiók-
    // integrációja, ezért TILTOTT HELYŐRZŐ — ugyanaz a bevett alak, mint a
    // „Send movies as” két gombjánál és az Outlook-jelölőnél lent.
    //
    // ⚠️ Miért helyőrző, és nem elhagyás: a fül szerkezete így hű marad, és
    // a tiltás kimondja, hogy nem működik. Egy engedélyezett, de kattintásra
    // semmit nem tevő gomb volna a rossz megoldás (#1895).
    //
    // ⚠️ A SORRENDRŐL a jegy nem állít semmit: az `options` panel
    // respack-geometriája nincs meg, tehát a képernyőn hol áll a három gomb,
    // az NINCS MÉRVE. A harmadik helye itt a mienk, nem az eredetié.
    RadioButton {
        objectName: "optionsMailGoogleRadio"
        text: qsTr("Use my Google Account")
        ButtonGroup.group: mailGroup
        enabled: false
    }

    // #2020: EGY méret-csúszka, NYOLC MÉRT fokozattal, mellette a
    // pillanatnyi érték szövegként — az eredetiben is így van
    // („Több kép mérete  [--|----]  480 képpont"). A csúszka INDEXET
    // mozgat, de a vezérlő KÉPPONTOT tárol: a mező az eredetiben is
    // képpontszám, nem fokozat-sorszám.
    readonly property var meretFokozatok: [160, 320, 480, 640, 800, 1024, 1200, 1600]

    readonly property int meretIndex: {
        const meret = root.mailCtl && root.mailCtl.emailSize !== undefined
            ? root.mailCtl.emailSize : 480
        const i = root.meretFokozatok.indexOf(meret)
        // ismeretlen (más Picasa-verzióból örökölt) méretnél a legközelebbi
        // fokozatra állunk — a TÁROLT érték viszont változatlan marad, amíg
        // a felhasználó hozzá nem nyúl a csúszkához
        if (i >= 0)
            return i
        let legjobb = 0
        for (let j = 1; j < root.meretFokozatok.length; ++j)
            if (Math.abs(root.meretFokozatok[j] - meret)
                < Math.abs(root.meretFokozatok[legjobb] - meret))
                legjobb = j
        return legjobb
    }

    readonly property int aktualisMeret: root.meretFokozatok[root.meretIndex]

    RowLayout {
        spacing: 8
        Text {
            text: qsTr("Multiple photo size")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        PicasaSlider {
            objectName: "optionsMailSizeSlider"
            from: 0
            to: 7
            stepSize: 1
            value: root.meretIndex
            onMoved: if (root.mailCtl)
                root.mailCtl.setEmailSize(root.meretFokozatok[value])
        }
        Text {
            objectName: "optionsMailSizeValue"
            //: A csúszka mellett a pillanatnyi érték — az eredetiben is
            //: kiírt szöveg („480 képpont").
            text: qsTr("%1 pixels").arg(root.aktualisMeret)
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    // #2020: az „egyedülálló kép" NEM méret, hanem KAPCSOLÓ. Az eredetiben
    // két választógomb, és az elsőbe bele van írva a csúszka aktuális
    // értéke — ezért él a kötés a fenti `aktualisMeret`-re.
    Text {
        text: qsTr("Single picture size:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }
    ButtonGroup { id: singleGroup }
    RadioButton {
        objectName: "optionsMailSingleSameRadio"
        text: qsTr("Same as multiple (%1 pixels)").arg(root.aktualisMeret)
        ButtonGroup.group: singleGroup
        checked: (root.mailCtl && root.mailCtl.singlePictureOriginal !== undefined)
            ? !root.mailCtl.singlePictureOriginal : true
        onToggled: if (root.mailCtl && checked)
            root.mailCtl.setSinglePictureOriginal(false)
    }
    RadioButton {
        objectName: "optionsMailSingleOriginalRadio"
        text: qsTr("Original size")
        ButtonGroup.group: singleGroup
        checked: (root.mailCtl && root.mailCtl.singlePictureOriginal !== undefined)
            ? root.mailCtl.singlePictureOriginal : false
        onToggled: if (root.mailCtl && checked)
            root.mailCtl.setSinglePictureOriginal(true)
    }

    Text {
        text: qsTr("Send movies as:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }
    ButtonGroup { id: movieGroup }
    RadioButton {
        objectName: "optionsMailMovieFirstFrameRadio"
        text: qsTr("First frame")
        ButtonGroup.group: movieGroup
        checked: true
        enabled: false
    }
    RadioButton {
        objectName: "optionsMailMovieFullRadio"
        text: qsTr("Full movie")
        ButtonGroup.group: movieGroup
        enabled: false
    }

    // csak Windows/Outlook alatt volt értelmezve az eredetiben
    CheckBox {
        objectName: "optionsMailUseHtmlCheck"
        text: qsTr("Send embedded pictures and captions (Outlook only)")
        enabled: false
    }

    Item { Layout.fillHeight: true }
}
