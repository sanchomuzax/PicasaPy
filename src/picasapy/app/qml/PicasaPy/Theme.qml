pragma Singleton
import QtQuick

// Picasa 3.9 dizájn-tokenek — a felhasználó saját magyar Picasa 3.9-éről
// készült 1920x1080-as screenshotokból mintavételezve (2026-07-18,
// research/testdata/screenshot/).
QtObject {
    // króm (menü, eszköztár, szűrősáv)
    readonly property color chromeBg: "#e8e8e8"
    readonly property color chromeBorder: "#d5d5d5"

    // bal oldali mappa-panel
    readonly property color panelBg: "#f3f3f3"
    readonly property color panelHeaderBg: "#e1e4e7"
    readonly property color panelHeaderText: "#3a3a3a"
    readonly property color panelSelection: "#83a7bd"
    readonly property color panelSelectionText: "#ffffff"
    readonly property color panelYearText: "#8a8a8a"

    // lightbox (rács)
    readonly property color lightboxBg: "#eaeaea"
    readonly property color folderTitle: "#634b45"      // barna szerif cím!
    readonly property color folderDate: "#444444"
    readonly property color addDescription: "#8f8f8f"
    readonly property color thumbCard: "#ffffff"
    readonly property color thumbBorder: "#d9d9d9"
    readonly property color thumbSelection: "#009eff"   // élénk azúr keret
    readonly property color thumbHover: "#a8c8de"

    // alsó info-sáv (tömör acélkék) és tálca
    readonly property color infoBar: "#568fb7"
    readonly property color infoBarText: "#ffffff"
    readonly property color trayBg: "#f8f8f8"
    readonly property color trayBorder: "#d0d0c8"

    // akcentusok
    readonly property color picasaGreen: "#3b8f00"
    readonly property color playGreen: "#43a047"
    readonly property color starYellow: "#f5c518"
    readonly property color textDark: "#333333"
    readonly property color textGray: "#767676"
    readonly property color linkBlue: "#2a5db0"

    readonly property int fontSize: 12
    readonly property int folderTitleSize: 17
    readonly property string serifFamily: "Georgia, 'Times New Roman', serif"
}
