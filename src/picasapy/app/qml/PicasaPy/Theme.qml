pragma Singleton
import QtQuick

// Dizájn-tokenek — forrás: „Picasa 3 Dizajnkezikonyv" (claude.ai/design,
// 2026-07-18) mint elsődleges rendszer, a valódi Picasa 3.9 screenshotok
// mint történeti referencia. Ld. docs/specs/design-guide.md.
QtObject {
    // ------- márka (a logó színei — csak márka-kontextusban!) -------
    readonly property color brandRed: "#e04a3f"
    readonly property color brandYellow: "#ffd34e"
    readonly property color brandGreen: "#0dab62"
    readonly property color brandBlue: "#448afd"
    readonly property color brandPurple: "#9b479f"
    readonly property color brandSlate: "#4b5d5f"

    // ------- felület: semleges keret -------
    readonly property color canvasBg: "#eaeaea"       // vászon (app-háttér)
    readonly property color contentPanel: "#ffffff"   // tartalompanel (kártya)
    readonly property color panelBg: "#f3f3f3"        // oldalsáv (mappafa)
    readonly property color chromeBg: "#e2e2e2"       // eszköztár, sávok
    readonly property color chromeBorder: "#cdcdcd"   // vezérlők, keretek
    readonly property color ink: "#1c1b19"            // tinta: szöveg, menük

    // kompatibilitási aliasok (fokozatos átállás)
    readonly property color lightboxBg: canvasBg
    readonly property color textDark: ink
    readonly property color thumbCard: contentPanel

    // ------- jelző színek -------
    readonly property color picasaGreen: "#3b8f00"    // az EGYETLEN zöld tett
    readonly property color selectionBlue: "#83a7bd"  // jelölő kék (lista, szűrő)
    readonly property color panelSelection: selectionBlue
    readonly property color folderGold: "#ebcc8f"     // mappa arany
    readonly property color folderArrow: "#e0a92e"    // mappafa nyíl
    readonly property color linkBlue: "#1a0dab"       // hivatkozások

    // ------- oldalsáv részletek -------
    readonly property color panelHeaderBg: "#e1e4e7"
    readonly property color panelHeaderText: "#3a3a3a"
    readonly property color panelSelectionText: "#ffffff"
    readonly property color panelYearText: "#7a776f"  // mono évszám-címke

    // ------- lightbox / indexkép-csoport -------
    readonly property color folderTitle: ink          // 16px / 600 sans
    readonly property color folderDate: "#5a5750"
    readonly property color addDescription: "#a29e96" // dőlt
    readonly property color thumbBorder: "#d9d9d9"
    readonly property color thumbSelection: "#009eff" // rács-kijelölés (3.9)
    readonly property color thumbHover: "#a8c8de"

    // ------- infó-sáv, tálca, néző -------
    readonly property color infoBar: "#568fb7"
    readonly property color infoBarText: "#ffffff"
    readonly property color trayBg: "#f8f8f8"
    readonly property color trayBorder: "#d0d0c8"
    readonly property color viewerBg: "#808080"
    readonly property color starYellow: "#f5c518"
    readonly property color textGray: "#7a776f"

    readonly property int fontSize: 12                // felület: 11–13 px
    readonly property int folderTitleSize: 16         // csoport-fejléc / 600
    readonly property string monoFamily: "IBM Plex Mono, monospace"
}
