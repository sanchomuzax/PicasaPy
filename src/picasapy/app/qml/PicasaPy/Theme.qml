pragma Singleton
import QtQuick

// Dizájn-tokenek — forrás: „Picasa 3 Dizajnkezikonyv" (claude.ai/design,
// 2026-07-18) mint elsődleges rendszer, a valódi Picasa 3.9 screenshotok
// mint történeti referencia. Ld. docs/specs/design-guide.md.
//
// #28: a tokenek PÁRBAN élnek — világos (alapértelmezés, a Picasa-paritás
// mércéje) és sötét. A `dark` kapcsolót a Main.qml köti a
// controller.darkTheme-hez; minden token kötése automatikusan követi, a
// felület nevei (canvasBg, ink…) változatlanok, így a hívó QML-ek nem
// tudnak a témáról. A márkaszínek (logó) mindkét témában azonosak.
QtObject {
    // Sötét mód — kívülről állítható (a többi token readonly marad).
    property bool dark: false

    // ------- márka (a logó színei — csak márka-kontextusban!) -------
    readonly property color brandRed: "#e04a3f"
    readonly property color brandYellow: "#ffd34e"
    readonly property color brandGreen: "#0dab62"
    readonly property color brandBlue: "#448afd"
    readonly property color brandPurple: "#9b479f"
    readonly property color brandSlate: "#4b5d5f"

    // ------- felület: semleges keret -------
    readonly property color canvasBg: dark ? "#232323" : "#eaeaea"       // vászon (app-háttér)
    readonly property color contentPanel: dark ? "#2e2e2e" : "#ffffff"   // tartalompanel (kártya)
    readonly property color panelBg: dark ? "#282828" : "#f3f3f3"        // oldalsáv (mappafa)
    readonly property color chromeBg: dark ? "#303030" : "#e2e2e2"       // eszköztár, sávok
    readonly property color chromeBorder: dark ? "#4a4a4a" : "#cdcdcd"   // vezérlők, keretek
    readonly property color ink: dark ? "#ececea" : "#1c1b19"            // tinta: szöveg, menük

    // kompatibilitási aliasok (fokozatos átállás)
    readonly property color lightboxBg: canvasBg
    readonly property color textDark: ink
    readonly property color thumbCard: contentPanel

    // ------- jelző színek -------
    // sötét háttéren a világos alap-zöld/kék beleolvadna: világosított pár
    readonly property color picasaGreen: dark ? "#6cbf3f" : "#3b8f00"    // az EGYETLEN zöld tett
    readonly property color selectionBlue: dark ? "#4d6b80" : "#83a7bd"  // jelölő kék (lista, szűrő)
    readonly property color panelSelection: selectionBlue
    // #384: a TÉNYLEGES kijelölés mélykékje (constants.ui alist_selcolor_win);
    // a sötét érték a selectionBlue világos/sötét arányából becsült — az
    // eredetiben nincs sötét változat (a Picasa mindig világos).
    readonly property color panelSelectionActive: dark ? "#1b4a68" : "#25648b"
    readonly property color folderGold: dark ? "#a98c53" : "#ebcc8f"     // mappa arany
    readonly property color folderGoldBorder: dark ? "#8a7040" : "#d9b571"
    readonly property color folderArrow: dark ? "#d9a63a" : "#e0a92e"    // mappafa nyíl
    readonly property color linkBlue: dark ? "#8ab4f8" : "#1a0dab"       // hivatkozások

    // ------- oldalsáv részletek -------
    readonly property color panelHeaderBg: dark ? "#343a3e" : "#e1e4e7"
    readonly property color panelHeaderTop: dark ? "#3d4448" : "#eef0f2"  // fejléc-átmenet teteje
    readonly property color panelHeaderText: dark ? "#c9c9c9" : "#3a3a3a"
    readonly property color panelSelectionText: "#ffffff"
    readonly property color panelYearText: dark ? "#9c988f" : "#7a776f"  // mono évszám-címke

    // ------- lightbox / indexkép-csoport -------
    readonly property color folderTitle: ink          // 16px / 600 sans
    readonly property color folderDate: dark ? "#b0aca4" : "#5a5750"
    readonly property color addDescription: dark ? "#8b877f" : "#a29e96" // dőlt
    readonly property color thumbBorder: dark ? "#454545" : "#d9d9d9"
    readonly property color thumbSelection: dark ? "#2aa8ff" : "#009eff" // rács-kijelölés (3.9)
    readonly property color thumbHover: dark ? "#3f5f75" : "#a8c8de"

    // ------- infó-sáv, tálca, néző -------
    readonly property color infoBar: dark ? "#3c6382" : "#568fb7"
    readonly property color infoBarText: "#ffffff"
    readonly property color trayBg: dark ? "#262626" : "#f8f8f8"
    readonly property color trayBorder: dark ? "#3c3c3c" : "#d0d0c8"
    readonly property color viewerBg: dark ? "#1a1a1a" : "#808080"
    readonly property color starYellow: "#f5c518"
    readonly property color textGray: dark ? "#a29e96" : "#7a776f"

    // ------- Qt Controls-paletta (Main.qml ablak-palettája) -------
    readonly property color controlBase: contentPanel        // beviteli mezők háttere
    readonly property color buttonBg: dark ? "#3a3a3a" : "#e8e8e8"
    readonly property color placeholderText: "#8f8b83"       // mindkét témán olvasható
    readonly property color trackBg: dark ? "#3a3a3a" : "#dddddd"     // haladásjelző sín
    readonly property color shadeLight: dark ? "#3f3f3f" : "#ffffff"  // kiemelt él
    readonly property color shadeDark: dark ? "#161616" : "#9a9a9a"   // árnyék-él

    // ------- #314: sötét téma kozmetikai javítások -------
    // splash-logó háttérkorongja: az eredeti Picasa-logó is fehér korongon
    // ül (ld. #37 az app-ikonnál, tools/regenerate_icon.py) — sötét témán a
    // logó sötét eleme (navy "Picasa"-felirat, a pinwheel cikkelyei közti
    // rés) a sötét kártyaháttéren szinte eltűnik. Világos témán a kártya
    // (contentPanel) már amúgy is fehér, ott a korong láthatatlan plusz
    // szegély lenne — ezért itt (a színen keresztül, nem külön
    // visible-ágon) párosítjuk: sötétben fehér, világosban átlátszó. Így a
    // SplashScreen maga nem kérdezi a témát, csak a tokent használja (#28).
    readonly property color logoDisc: dark ? "#ffffff" : "#00ffffff"

    // gomb-ikon tinta (TrayBar): a PicasaButton krómja (PicasaButton.qml)
    // SZÁNDÉKOSAN nem témavezérelt — a háttere mindig világos-szürke bevel
    // (Picasa-hűség), ezért a rajta lévő ikon/felirat sem követheti az
    // `ink`-et (ami sötét témán kivilágosodik, és a világos gombháttéren
    // eltűnne). Rögzített sötét tinta MINDKÉT témában — nem azért „pár",
    // mert a felület, amin ül, maga sem az.
    readonly property color iconInk: dark ? "#2b2b2b" : "#2b2b2b"

    readonly property int fontSize: 12              // felület: 11–13 px
    readonly property int folderTitleSize: 16         // csoport-fejléc / 600
    readonly property string monoFamily: "IBM Plex Mono, monospace"
}
