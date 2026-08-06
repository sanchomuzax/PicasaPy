import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "E-Mail" fül (options.fen) — a PicasaPy-ban nincs beépített
// levelezőprogram-integráció ("Email this photo"), ezért a teljes fül
// tiltott: a widget-fa a FEN-paritás kedvéért épül fel, funkció nélkül.
ColumnLayout {
    id: root
    spacing: 12
    enabled: false

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
        checked: true
    }
    RadioButton {
        objectName: "optionsMailChooseRadio"
        text: qsTr("Let me choose each time I send a picture")
        ButtonGroup.group: mailGroup
    }

    RowLayout {
        spacing: 8
        Text { text: qsTr("Multiple photo size:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaSlider { objectName: "optionsMailMultiSizeSlider"; from: 0; to: 4 }
    }
    RowLayout {
        spacing: 8
        Text { text: qsTr("Single photo size:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaSlider { objectName: "optionsMailSingleSizeSlider"; from: 0; to: 4 }
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
    }
    RadioButton {
        objectName: "optionsMailMovieFullRadio"
        text: qsTr("Full movie")
        ButtonGroup.group: movieGroup
    }

    // csak Windows/Outlook alatt volt értelmezve az eredetiben
    CheckBox {
        objectName: "optionsMailUseHtmlCheck"
        text: qsTr("Send embedded pictures and captions (Outlook only)")
    }

    Item { Layout.fillHeight: true }
}
