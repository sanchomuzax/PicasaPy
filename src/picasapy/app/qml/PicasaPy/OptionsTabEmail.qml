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
        text: qsTr("Choose your mail client:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }
    ButtonGroup { id: mailGroup }
    RadioButton {
        objectName: "optionsMailDefaultRadio"
        text: qsTr("Use this computer's default email program")
        ButtonGroup.group: mailGroup
        checked: root.mailCtl ? root.mailCtl.useDefaultClient : true
        onToggled: if (root.mailCtl && checked) root.mailCtl.setUseDefaultClient(true)
    }
    RadioButton {
        objectName: "optionsMailChooseRadio"
        text: qsTr("Let me choose each time I send a picture")
        ButtonGroup.group: mailGroup
        checked: root.mailCtl ? !root.mailCtl.useDefaultClient : false
        onToggled: if (root.mailCtl && checked) root.mailCtl.setUseDefaultClient(false)
    }

    RowLayout {
        spacing: 8
        Text { text: qsTr("Multiple photo size:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaSlider {
            objectName: "optionsMailMultiSizeSlider"
            from: 0; to: 4
            value: root.mailCtl ? root.mailCtl.multiSizeIndex : 2
            onMoved: if (root.mailCtl) root.mailCtl.setMultiSizeIndex(value)
        }
    }
    RowLayout {
        spacing: 8
        Text { text: qsTr("Single photo size:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaSlider {
            objectName: "optionsMailSingleSizeSlider"
            from: 0; to: 4
            value: root.mailCtl ? root.mailCtl.singleSizeIndex : 4
            onMoved: if (root.mailCtl) root.mailCtl.setSingleSizeIndex(value)
        }
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
