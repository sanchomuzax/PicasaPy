pragma Singleton
import QtQuick

// Picasa 3.9 dizájn-tokenek — a Wikipedia Picasa_3.9.jpg screenshotból
// mintavételezett színek (2026-07-17); a felhasználói screenshotokkal
// finomítandó.
QtObject {
    // króm (eszköztár, menük)
    readonly property color chromeBg: "#ededed"
    readonly property color chromeBorder: "#d5d5d5"

    // bal oldali mappa-panel
    readonly property color panelBg: "#e9eaef"
    readonly property color panelHeaderBg: "#e1e2e7"
    readonly property color panelHeaderText: "#44506b"
    readonly property color panelSelection: "#84a9bc"
    readonly property color panelSelectionText: "#ffffff"

    // lightbox (rács)
    readonly property color lightboxBg: "#f2f2f2"
    readonly property color folderTitle: "#3c6ea5"
    readonly property color thumbBorder: "#d9d9d9"
    readonly property color thumbSelection: "#4786b1"
    readonly property color thumbHover: "#a8c4d6"

    // alsó info-sáv (acélkék gradiens) és tálca
    readonly property color infoBarTop: "#639dc3"
    readonly property color infoBarBottom: "#4786b1"
    readonly property color infoBarText: "#ffffff"
    readonly property color trayBg: "#f4f4f0"
    readonly property color trayBorder: "#d0d0c8"

    // akcentusok
    readonly property color picasaGreen: "#3c9100"
    readonly property color starYellow: "#f5c518"
    readonly property color textDark: "#333333"
    readonly property color textGray: "#767676"

    readonly property int fontSize: 12
    readonly property int folderTitleSize: 15
}
