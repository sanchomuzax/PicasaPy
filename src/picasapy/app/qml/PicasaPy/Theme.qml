pragma Singleton
import QtQuick

// Dizájn-tokenek — forrás: „Picasa 3 Dizajnkezikonyv" (claude.ai/design,
// 2026-07-18) mint elsődleges rendszer, a valódi Picasa 3.9 screenshotok
// mint történeti referencia. Ld. docs/specs/design-guide.md.
//
// SAJÁT FUNKCIÓ (#28, jegyzékbe véve: #1364): a SÖTÉT TÉMA az eredeti Picasa
// 3.9-ben NEM létezik (`docs/specs/ui-audit-menus.md` — „Nálunk van, az
// eredetiben nincs"). A világos tokenek a Picasa-paritás mércéje; a sötét
// párjuk a mi hozzáadásunk, tehát rájuk a bináris-egyezés nem vonatkozik.
//
// #28: a tokenek PÁRBAN élnek — világos (alapértelmezés, a Picasa-paritás
// mércéje) és sötét. A `dark` kapcsolót a Main.qml köti a
// controller.darkTheme-hez; minden token kötése automatikusan követi, a
// felület nevei (canvasBg, ink…) változatlanok, így a hívó QML-ek nem
// tudnak a témáról. A márkaszínek (logó) mindkét témában azonosak.
QtObject {
    id: tema

    // Sötét mód — kívülről állítható (a többi token readonly marad).
    property bool dark: false

    // #3070: a MEGJELENÍTÉSI MÓD palettája — tokennév → átalakított szín.
    // A vezérlő tölti fel (`apply_display_mode`, egyetlen menetben), üresen
    // pedig a nyers értékek mennek ki változatlanul. Két rétegre azért van
    // szükség, mert a származtatott színek (`Qt.lighter`, `Qt.darker`) NEM
    // kommutálnak a gamma-alapú átalakítással: a származtatást a NYERS
    // értékekből kell számolni, és a kész színt átereszteni egyszer — a
    // naiv „mindent burkoljunk be" a módot kétszer alkalmazná.
    property var megjelenitesiPaletta: ({})

    /*! A tokenhez tartozó nyilvános szín: a paletta értéke, ha van, különben
        a nyers. A kereséshez a tokennév a kulcs — így a paletta összeállítása
        egyetlen Python-oldali menet, és a QML-ben nincs színműveletsor. */
    function _szin(nev, nyersSzin) {
        var p = megjelenitesiPaletta;
        if (p && p[nev] !== undefined)
            return p[nev];
        return nyersSzin;
    }

    // ------- a NYERS tokenek -------
    //
    // Itt élnek a MÉRT és a származtatott értékek; a származtatás mindig
    // nyersből nyersbe megy (`nyersTokenek.…`), soha nem a nyilvános
    // felületről — különben a mód kétszer hatna.
    readonly property QtObject nyers: QtObject {
        id: nyersTokenek

        // ------- márka (a logó színei — csak márka-kontextusban!) -------
        readonly property color brandRed: "#e04a3f"
        readonly property color brandYellow: "#ffd34e"
        readonly property color brandGreen: "#0dab62"
        readonly property color brandBlue: "#448afd"
        readonly property color brandPurple: "#9b479f"
        readonly property color brandSlate: "#4b5d5f"

        // ------- felület: semleges keret -------
        readonly property color canvasBg: tema.dark ? "#232323" : "#eaeaea"       // vászon (app-háttér)
        readonly property color contentPanel: tema.dark ? "#2e2e2e" : "#ffffff"   // tartalompanel (kártya)
        readonly property color panelBg: tema.dark ? "#282828" : "#f3f3f3"        // oldalsáv (mappafa)
        readonly property color chromeBg: tema.dark ? "#303030" : "#e2e2e2"       // eszköztár, sávok
        readonly property color chromeBorder: tema.dark ? "#4a4a4a" : "#cdcdcd"   // vezérlők, keretek
        readonly property color ink: tema.dark ? "#ececea" : "#1c1b19"            // tinta: szöveg, menük

        // kompatibilitási aliasok (fokozatos átállás)
        readonly property color lightboxBg: nyersTokenek.canvasBg
        readonly property color textDark: nyersTokenek.ink
        readonly property color thumbCard: nyersTokenek.contentPanel

        // ------- jelző színek -------
        // sötét háttéren a világos alap-zöld/kék beleolvadna: világosított pár
        readonly property color picasaGreen: tema.dark ? "#6cbf3f" : "#3b8f00"    // az EGYETLEN zöld tett
        readonly property color selectionBlue: tema.dark ? "#4d6b80" : "#83a7bd"  // jelölő kék (lista, szűrő)
        readonly property color panelSelection: nyersTokenek.selectionBlue
        // #384: a TÉNYLEGES kijelölés mélykékje (constants.ui alist_selcolor_win);
        // a sötét érték a selectionBlue világos/sötét arányából becsült — az
        // eredetiben nincs sötét változat (a Picasa mindig világos).
        readonly property color panelSelectionActive: tema.dark ? "#1b4a68" : "#25648b"
        readonly property color folderGold: tema.dark ? "#a98c53" : "#ebcc8f"     // mappa arany
        readonly property color folderGoldBorder: tema.dark ? "#8a7040" : "#d9b571"
        // #1132: a bal hasáb bejegyzés-TÍPUSAI külön ikont kapnak, mert az
        // eredetiben az ikon nem díszítés, hanem a típust kódolja (kilenc
        // erőforrás az `icons/` névtérben). A MÉRET és a JELENTÉS mért, a RAJZ
        // és a színérték a miénk (`docs/specs/design-guide.md`) — az eredeti
        // PNG-ket tilos a repóba másolni.
        //
        // A lemezes mappa az eredetiben KÉK (`icons/folder`, 17 × 15), nálunk
        // eddig arany volt; ez a jegy javítja.
        // #894: a LEGÖRDÜLŐ LISTA panelének MÉRT rajza (`listdecrect/listdecrect`,
        // 17 × 17-es nyújtható réteg, képpontból olvasva). A panel SÍK — nincs
        // benne színátmenet, ellentétben a gombokkal.
        //
        //   sor 2:   #D6D6D6  lágy árnyék (kívül)
        //   sor 3:   #BABABA  a keret, 1 px
        //   sor 4–12 #E8E8E8  a kitöltés
        //   sor 13:  #F8F8F8  belső fénykiemelés alul
        //   sor 14:  #F0F0F0
        //
        // ⚠️ A sötét módban a mért világos értékek nem használhatók (a panel
        // olvashatatlan lenne), ezért ott a saját króm-tónusaink állnak — a
        // VILÁGOS mód az, ami az eredetit követi.
        // #901: a buboréksúgó KÉSLELTETÉSE egy helyen. Nálunk eddig háromféle
        // volt (400 ms három helyen, 500 ms hatvanhaton, és sok helyen meg sem
        // adva); az egyesítés a többséget követte, 500-ra.
        //
        // ✅ 2026-09-15: az EREDETI értéke KIMÉRVE — **600 ms**. A `ytToolTip`
        // vtáblájának (`0x008909d4`) `+0x74` rekesze a `0x00a6de20`-ra megy, az
        // időmérés `QueryPerformanceCounter`/`…Frequency`, és a küszöb a
        // `0x00c7e304`-en tárolt `9a 99 19 3f` — IEEE-754 szerint
        // `0,6000000238418579` másodperc. (Ugyanebben a sávban olvassa a
        // `ShowTooltips` beállítást, `0x00a6e0fd`.)
        //
        // A korábbi komment ígérete szerint ez EGY szám átírása volt: 500 → 600.
        readonly property int tooltipDelay: 600

        readonly property color listPanelBg: tema.dark ? "#2e2e2e" : "#e8e8e8"
        readonly property color listPanelBorder: tema.dark ? "#5a5a5a" : "#bababa"
        readonly property color listPanelShadow: tema.dark ? "#1f1f1f" : "#d6d6d6"
        readonly property color listPanelInnerLight: tema.dark ? "#3a3a3a" : "#f8f8f8"
        readonly property color listPanelInnerLight2: tema.dark ? "#343434" : "#f0f0f0"
        // #894: a görgetősáv hüvelykjének MÉRT átmenete (`scrollart/base_win`,
        // 15 × 25: vízszintes átmenet, függőlegesen állandó).
        //   x0 #B6B6B6 · x1 #C7C7C7 → x7 #D9D9D9 → x13 #EDEDED · x14 #C8C8C8
        readonly property color scrollThumbEdgeDark: tema.dark ? "#3f3f3f" : "#b6b6b6"
        readonly property color scrollThumbMid: tema.dark ? "#5a5a5a" : "#d9d9d9"
        readonly property color scrollThumbLight: tema.dark ? "#6d6d6d" : "#ededed"
        readonly property color scrollThumbEdgeSoft: tema.dark ? "#454545" : "#c8c8c8"
        readonly property color folderBlue: tema.dark ? "#5b7fa6" : "#9dc0e0"
        readonly property color folderBlueBorder: tema.dark ? "#43607e" : "#7ba3c8"
        //: `icons/album` (16 × 18) — narancs könyv: rendes album
        readonly property color albumOrange: tema.dark ? "#b3762f" : "#eeae5e"
        readonly property color albumOrangeBorder: tema.dark ? "#8d5c24" : "#cf8f42"
        //: `icons/special_album` (16 × 18) — ZÖLD könyv csillaggal:
        //: különleges album (Csillagozott, Legutóbb frissítve)
        readonly property color specialAlbumGreen: tema.dark ? "#4f8a4a" : "#7fbe78"
        readonly property color specialAlbumGreenBorder: tema.dark ? "#3c6b38" : "#5d9d57"
        //: `icons/projects` (15 × 16) — LILA könyv csillaggal: projekt-mappa
        readonly property color projectPurple: tema.dark ? "#8a5f9e" : "#bb96ce"
        readonly property color projectPurpleBorder: tema.dark ? "#6b4a7b" : "#9a75ad"
        //: `icons/label` (15 × 12) — szürke címke
        readonly property color labelGray: tema.dark ? "#8d8d8d" : "#c7c7c7"
        readonly property color labelGrayBorder: tema.dark ? "#6f6f6f" : "#a6a6a6"
        readonly property color folderArrow: tema.dark ? "#d9a63a" : "#e0a92e"    // mappafa nyíl
        readonly property color linkBlue: tema.dark ? "#8ab4f8" : "#1a0dab"       // hivatkozások

        // ------- oldalsáv részletek -------
        readonly property color panelHeaderBg: tema.dark ? "#343a3e" : "#e1e4e7"
        readonly property color panelHeaderTop: tema.dark ? "#3d4448" : "#eef0f2"  // fejléc-átmenet teteje
        readonly property color panelHeaderText: tema.dark ? "#c9c9c9" : "#3a3a3a"
        readonly property color panelSelectionText: "#ffffff"
        readonly property color panelYearText: tema.dark ? "#9c988f" : "#7a776f"  // mono évszám-címke

        // #1488: a `constants.ui` lista-hasáb (`alist_*`) ÖT élő színe, ami a
        // #384 köréből kimaradt. Az értékek a szállított fájlból olvasva
        // (`0xAARRGGBB`, az alfa mindegyiknél FF).
        //
        // A SÖTÉT párok a mi kiegészítésünk (az eredetinek nincs sötét témája),
        // és NEM ízlésből születtek:
        //
        // * a három háttér-kitöltés (`listHighlightAlt`, `listCategoryBg`,
        //   `listStickyBg`) megtartja az eredeti színezetét és telítettségét,
        //   a világosságot pedig a MEGLÉVŐ sötét panel-fejlécétől veszi
        //   (`panelHeaderBg`: 22%) — így ugyanabba a rétegrendbe illik, amibe a
        //   világos oldalon tartozik. A tükrözött világosság (12%, 9%, 11%)
        //   itt majdnem feketét adna, tehát a `folderTitle` SZÖVEG-szabálya
        //   erre a célra nem jó.
        // * a `listDotMarker` nem kitöltés, hanem LÁTHATÓ jelölő: a sötét
        //   párja ugyanazt a kontrasztarányt tartja a sötét oldalsáv fölött
        //   (1,675), mint az eredeti a világos lista (#F3F3F3) fölött.
        // * a `listDragTarget` az eredetiben egy hajszállal a kiemelés alatt
        //   van (#82A6BD vs #83A7BD — mindhárom csatornán eggyel kisebb); a
        //   sötét pár ugyanezt a viszonyt tartja a `selectionBlue` sötét
        //   párjához (#4d6b80 → #4c6a7f). A különbség szándékos: az eredeti
        //   így jelzi, hogy a húzás célpontja NEM ugyanaz, mint a kijelölés.
        //
        //: `alist_hicolor2_win = #E5E2DA` — a lista MÁSODIK kiemelőszíne
        readonly property color listHighlightAlt: tema.dark ? "#423d2e" : "#e5e2da"
        //: `alist_dragcolor = #82A6BD` — a fogd-és-vidd célpont jelzése
        readonly property color listDragTarget: tema.dark ? "#4c6a7f" : "#82a6bd"
        //: `alist_catcolor = #EDEAE4` — kategória-fejléc (csoportsor) háttere
        readonly property color listCategoryBg: tema.dark ? "#433c2d" : "#edeae4"
        //: `alist_dotcolor = #BEBEBE` — a lista pont-jelölője
        readonly property color listDotMarker: tema.dark ? "#4a4a4a" : "#bebebe"
        //: `alist_stickycolor = #EAE7DC` — a rögzített (sticky) fejléc háttere
        readonly property color listStickyBg: tema.dark ? "#46402a" : "#eae7dc"

        // ------- lightbox / indexkép-csoport -------
        // #2043: az eredeti Picasa `runtime/constants.ui` fájljának „Album
        // Layout" blokkja — `alayout_titleColor = #634B45`, meleg sötétbarna.
        // Ugyanennek a blokknak a betűjét (Georgia) és méretét (20) már
        // korábban átvettük (`LightboxHeader.qml`), csak a szín maradt ki.
        // A sötét pár azonos színezet és telítettség, tükrözött világossággal
        // (32,9% -> 67,1%) — ugyanaz a meleg barna, nem elszürkítve.
        readonly property color folderTitle: tema.dark ? "#baa29c" : "#634b45"
        readonly property color folderDate: tema.dark ? "#b0aca4" : "#5a5750"
        readonly property color addDescription: tema.dark ? "#8b877f" : "#a29e96" // dőlt
        readonly property color thumbBorder: tema.dark ? "#454545" : "#d9d9d9"
        readonly property color thumbSelection: tema.dark ? "#2aa8ff" : "#009eff" // rács-kijelölés (3.9)
        readonly property color thumbHover: tema.dark ? "#3f5f75" : "#a8c8de"

        // ------- infó-sáv, tálca, néző -------
        readonly property color infoBar: tema.dark ? "#3c6382" : "#568fb7"
        readonly property color infoBarText: "#ffffff"
        readonly property color trayBg: tema.dark ? "#262626" : "#f8f8f8"
        readonly property color trayBorder: tema.dark ? "#3c3c3c" : "#d0d0c8"
        // #1420: a képtálca doboza (`thumbui/scratchback`) az eredetiben KÜLÖN,
        // világosabb panel a sáv hátterén — a valódi Picasa képernyőképén mérve
        // a sáv #eaeaea, a doboz #f8f8f8, a kerete #dfdfdf. Nálunk a sáv MÁR
        // #f8f8f8, ezért a dobozt egy fokkal világosabbra tesszük: a KÜLÖNBSÉG
        // iránya (a doboz világosabb a sávnál) marad az eredetié.
        readonly property color trayPanelBg: tema.dark ? "#303030" : "#ffffff"
        // #1919: az összecsukott mappa-/album-token feliratának pirulája
        // (`scratch/highlight`). MÉRVE a `…214629.jpg` felvételen: a fehér
        // tálcaháttér fölött RGB(107, 153, 186), és ÁTTETSZŐ — a borítókép
        // fölött sötétebb. Négy, függőlegesen sima képoszlopban mérve
        // `1 − α ≈ 0,34`, amiből az alapszín ≈ RGB(34, 104, 154) = #22689a,
        // az átlátszatlanság 0xa8 ≈ 0,66. A levezetés a `TrayAlbumToken.qml`
        // fejlécében áll.
        //
        // A respack a réteget `rect:`-ként adja (nincs bitképe), a
        // `constants.ui` pedig nem nevez hozzá színt — tehát a felvétel az
        // EGYETLEN forrás. Az eredetiben nincs sötét mód: a sötét pár saját
        // döntés (világosabb alapszín, hogy a fehér felirat a sötét
        // bélyegképen is olvasson).
        readonly property color trayTokenHighlight:
            tema.dark ? "#a83f83b6" : "#a822689a"
        //: `alabel_lighttext = #FFFFFF` — a felirat mindkét témán fehér, mert
        //: a pirula mindkettőn sötétkék
        readonly property color trayTokenHighlightText: "#ffffff"
        readonly property color viewerBg: tema.dark ? "#1a1a1a" : "#808080"

        // #2587: a képaláírás-sáv színei. MÉRVE a tulajdonos felvételén
        // (`research/felirat-ki-bekapcsolva/picasa3-felirat-bekapcsolva. 223224.jpg`,
        // a csík sora y 906…926): a sáv `#c6c6c6` — a KRÓM világosszürkéje, NEM
        // a fotó-terület szürkéje (`viewerBg`, ott 108) és nem sötét. A #2565
        // sötét csíkot adott, ami világos módban idegen testként ült a világos
        // króm alatt; a tulajdonos ezt jelentette.
        //
        // A sötét pár a saját krómunké: a `trayBg` sötét értékénél egy fokkal
        // világosabb, hogy a sáv a fotó alatt ELVÁLJON, ahogy világosban is.
        readonly property color captionBar: tema.dark ? "#333333" : "#c6c6c6"
        readonly property color captionBarText: tema.dark ? "#e8e8e8" : "#1a1a1a"
        //: a felirat-kapcsoló kis doboza — a felvételen FEHÉR, sötét kerettel
        readonly property color captionToggleBg: tema.dark ? "#d8d8d8" : "#ffffff"
        readonly property color captionToggleBorder: tema.dark ? "#555555" : "#5a5a5a"

        // #900: a kijelölésen KÍVÜLI terület elsötétítése a szerkesztő
        // eszközeiben (vágás, vörösszem, arc hozzáadása). Az eredeti `.tre`
        // öt elemen adja meg ugyanezt: `Property negativemode 8f2f2f2f` —
        // ARGB-ként olvasva alfa 143 (56,1%) + RGB 47/47/47.
        // NEM fekete: a fekete kioltja a képet, ez a semleges sötétszürke
        // viszont MEGTARTJA a kontúrokat, tehát a levágandó rész halványan,
        // de olvashatóan látszik. (A parszer alapértelmezése `0x7F000000`
        // volna — fekete, 50% —, de mind az öt elem felülírja.)
        // #2627: a CSÚSZKA SÁVJA — a `respack.yt`-ből képpontról képpontra.
        // A `scaleslider/sliderbase` (121 × 9) és az `editslider/sliderbase`
        // (191 × 27, a sáv a 8…16. sor) UGYANAZT a három színt adja:
        //
        //   belső kitöltés   RGB(202,213,229) = #cad5e5   (kékesszürke)
        //   felső szegély    RGB(154,162,174) = #9aa2ae
        //   jelölő-vonalak   RGB(243,245,249) = #f3f5f9   (két vég + a KÖZÉP)
        //
        // A sáv nálunk eddig `chromeBg`/`chromeBorder` volt — semleges szürke.
        // A kék nem díszítés: a csúszka így válik el a panel krómjától.
        //
        // A sötét pár a mért világos színek sötét megfelelője, AZONOS
        // színezettel (a kékes árnyalat megmarad, csak a világosság fordul) —
        // saját döntés, az eredetiben nincs sötét mód.
        readonly property color sliderGroove: tema.dark ? "#3b4553" : "#cad5e5"
        readonly property color sliderGrooveBorder: tema.dark ? "#5b6573" : "#9aa2ae"
        readonly property color sliderGrooveTick: tema.dark ? "#79838f" : "#f3f5f9"

        // #2641: a FOGANTYÚ közepére VÉSETT vonal két oszlopa — szintén a
        // `respack.yt`-ből, képpontról képpontra. A `scaleslider/thumb`
        // (16 × 22) és az `editslider/thumb` (16 × 26) UGYANAZT adja:
        //
        //   sötét oldal   199 → #c7c7c7   (a vésés árnyéka, a bal oszlop)
        //   világos oldal 244 → #f4f4f4   (a fény alulról, a jobb oszlop)
        //
        // A környező fogantyú-képpontok 232…240 között vannak, tehát a sötét
        // oszlop ~35 értékkel alattuk, a világos ~10-zel felettük áll — a
        // vésés a kettő KÜLÖNBSÉGÉBŐL látszik, nem az abszolút értékből.
        //
        // #2663: a fogantyú EGYÜTT lett témafüggővé ezzel a két színnel (a
        // #2641 code review pontosan ezt kérte). A világos ág VÁLTOZATLAN — az
        // eredeti mérés. A sötét ág SAJÁT DÖNTÉS (nincs sötét mód az
        // eredetiben): a #2663-mal bevezetett sötét fogantyú-kitöltés
        // (`sliderHandleTopLeft` … `sliderHandleBottomRight`, lent) a vésés
        // helyén, KIRAJZOLVA mérve, ~112 világosságú (`test_csuszka_veset_2641`
        // dark-témás próbája) — a sötét oldalt ehhez képest ~30-cal
        // sötétebbre, a világosat ~12-vel világosabbra hangoltuk, hogy a
        // különbség a #2641 review kritikáját (193/133 — „nem vésés, hanem
        // fekete perjel") elkerülje, ÉS a jegy kért ~40-es felső korlátjától
        // is biztos távolságot tartson.
        readonly property color sliderHandleGrooveDark: tema.dark ? "#525252" : "#c7c7c7"
        readonly property color sliderHandleGrooveLight: tema.dark ? "#7c7c7c" : "#f4f4f4"

        // #2656/#2663: a FOGANTYÚ kitöltése — négy sarok, mert az eredeti
        // átmenet ÁTLÓS (lefelé ÉS balról jobbra sötétedik), nem tisztán
        // függőleges. A `PicasaSlider.qml` ezért KÉT, egymás mellé állított,
        // fél szélességű, önállóan lekerekített Rectangle-lal rajzolja: a bal
        // fél a BAL oszlop színeivel fut felülről lefelé, a jobb fél a JOBB
        // oszlopéval — a látvány a kettő határán adja ki az átlós sötétedést.
        //
        // A világos ág a #2656 MÉRÉSE (`respack.yt`, `scaleslider/thumb` és
        // `editslider/thumb`, a tömör rajz 4…15. sorában, x = 4 a bal és x = 9
        // a jobb oldalon):
        //
        //   bal, teteje    245 → #f5f5f5      jobb, teteje    234 → #eaeaea
        //   bal, alja      225 → #e1e1e1      jobb, alja      211 → #d3d3d3
        //
        // A lenyomott állapot a korábbi kóddal azonos ELVET követi (a nyomott
        // fogantyú EGYSÉGESEN sötétebb) — a négy értéket fejenként 20-szal
        // toltuk lejjebb.
        //
        // A sötét ág SAJÁT DÖNTÉS: nincs mért eredeti. Az arányokat (bal
        // oszlop kevésbé, jobb oszlop jobban sötétedik lefelé; a jobb oldal
        // felül is sötétebb, mint a bal) a világos ágéból vettük át, a
        // `sliderGroove` sötét kitöltésénél (`#3b4553`, világosság ~70)
        // MINDIG világosabb szinten tartva — a fogantyú így akkor is elválik
        // a sávtól, ha a legsötétebb sarkán áll.
        readonly property color sliderHandleTopLeft: tema.dark ? "#7d828a" : "#f5f5f5"
        readonly property color sliderHandleBottomLeft: tema.dark ? "#646972" : "#e1e1e1"
        readonly property color sliderHandleTopRight: tema.dark ? "#71767f" : "#eaeaea"
        readonly property color sliderHandleBottomRight: tema.dark ? "#555a64" : "#d3d3d3"
        readonly property color sliderHandleTopLeftPressed: tema.dark ? "#696e76" : "#e1e1e1"
        readonly property color sliderHandleBottomLeftPressed: tema.dark ? "#50555e" : "#cdcdcd"
        readonly property color sliderHandleTopRightPressed: tema.dark ? "#5d626b" : "#d6d6d6"
        readonly property color sliderHandleBottomRightPressed: tema.dark ? "#414650" : "#bfbfbf"

        // A fogantyú KERETE — eddig fixen világos volt, a #2663 ezt is
        // témafüggővé teszi. A világos ág VÁLTOZATLAN. A sötét ág a
        // legsötétebb kitöltési saroknál (`sliderHandleBottomRight`,
        // világosság ~92) is sötétebb, hogy a szegély a kitöltéstől
        // MINDENHOL elváljon — ugyanaz a viszony, mint világos témában
        // (`#b5b5b5` = 181, a kitöltés legsötétebb sarka `#d3d3d3` = 211 —
        // a keret ~30-cal a kitöltés alatt van).
        readonly property color sliderHandleBorder: tema.dark ? "#373c44" : "#b5b5b5"
        readonly property color sliderHandleBorderPressed: tema.dark ? "#282c32" : "#8f8f8f"

        readonly property color selectionDim: "#8f2f2f2f"
        readonly property color starYellow: "#f5c518"
        readonly property color textGray: tema.dark ? "#a29e96" : "#7a776f"

        // ------- Qt Controls-paletta (Main.qml ablak-palettája) -------
        readonly property color controlBase: nyersTokenek.contentPanel        // beviteli mezők háttere
        readonly property color buttonBg: tema.dark ? "#3a3a3a" : "#e8e8e8"
        readonly property color placeholderText: "#8f8b83"       // mindkét témán olvasható
        readonly property color trackBg: tema.dark ? "#3a3a3a" : "#dddddd"     // haladásjelző sín
        readonly property color shadeLight: tema.dark ? "#3f3f3f" : "#ffffff"  // kiemelt él
        readonly property color shadeDark: tema.dark ? "#161616" : "#9a9a9a"   // árnyék-él

        // ------- #883: a gomb NÉGY állapota — MÉRVE a `respack.yt`-ből -------
        //
        // ⚠️ A világos ág értékei az EREDETI Picasa képpontjai
        // (`globalbuttons/b1_decrect_*`, spec: `picasa-gomb-es-menu-rendszer.md`).
        // A sötét ág SZÁRMAZTATOTT: az eredetinek nincs sötét témája, tehát ott
        // nincs mit átvenni — beégetni viszont TILOS. A #336 pontosan ezen bukott
        // meg: fix világos háttér + témafüggő felirat = üres gombok sötét témán.
        readonly property color buttonTopNormal:
            tema.dark ? Qt.lighter(nyersTokenek.buttonBg, 1.08) : "#f9f9f9"
        readonly property color buttonBottomNormal:
            tema.dark ? nyersTokenek.buttonBg : "#d0d0d0"
        // A lenyomott az eredetiben MELEGEBB (nem hidegebb): #A4A19D … #CBC6C2 —
        // a szürkék R>G>B irányba tolódnak. A korábbi `Qt.darker` hideg szürkét
        // adott, azaz ROSSZ IRÁNYBA tért el.
        readonly property color buttonTopDown:
            tema.dark ? Qt.darker(nyersTokenek.buttonBg, 1.15) : "#a4a19d"
        readonly property color buttonBottomDown:
            tema.dark ? Qt.darker(nyersTokenek.buttonBg, 1.05) : "#cbc6c2"
        // A rámutatás NEM külön kitöltés: a felső 2 képpontsor és a bal 2 oszlop
        // sötétedik (belső árnyék bal-felülről), a többi marad a normál.
        readonly property color buttonHoverShade:
            tema.dark ? Qt.darker(nyersTokenek.buttonBg, 1.25) : "#d6d6d6"
        readonly property color buttonBorder:
            tema.dark ? nyersTokenek.chromeBorder : "#bbbbbb"
        // A bekapcsolt állapot ARANY keretet kap, a kitöltése változatlan.
        // Ez SZÍNJELZÉS, nem téma-elem: mindkét témán ugyanaz.
        readonly property color buttonToggledBorder: "#c39b62"

        // ------- #314: sötét téma kozmetikai javítások -------
        // splash-logó háttérkorongja: az eredeti Picasa-logó is fehér korongon
        // ül (ld. #37 az app-ikonnál, tools/regenerate_icon.py) — sötét témán a
        // logó sötét eleme (navy "Picasa"-felirat, a pinwheel cikkelyei közti
        // rés) a sötét kártyaháttéren szinte eltűnik. Világos témán a kártya
        // (contentPanel) már amúgy is fehér, ott a korong láthatatlan plusz
        // szegély lenne — ezért itt (a színen keresztül, nem külön
        // visible-ágon) párosítjuk: sötétben fehér, világosban átlátszó. Így a
        // SplashScreen maga nem kérdezi a témát, csak a tokent használja (#28).
        readonly property color logoDisc: tema.dark ? "#ffffff" : "#00ffffff"

        // gomb-ikon tinta (TrayBar): a PicasaButton krómja (PicasaButton.qml)
        // SZÁNDÉKOSAN nem témavezérelt — a háttere mindig világos-szürke bevel
        // (Picasa-hűség), ezért a rajta lévő ikon/felirat sem követheti az
        // `ink`-et (ami sötét témán kivilágosodik, és a világos gombháttéren
        // eltűnne). Rögzített sötét tinta MINDKÉT témában — nem azért „pár",
        // mert a felület, amin ül, maga sem az.
        readonly property color iconInk: tema.dark ? "#2b2b2b" : "#2b2b2b"

        // --- Tipográfia (#526) -------------------------------------------
        //
        // A Picasa `runtime/` mappájában 12 előre renderelt betűtípus-
        // gyorsítótár (`.ytf`) van; a fájlnevek és a fejléceik együtt megadják
        // a felület TELJES betűkészletét:
        //
        //     Praxis Semi Bold / Heavy .......  11 12 13 14 16 18   (400, 700)
        //     HelveticaNeue MediumCond .......  14 28               (400)
        //     HelveticaNeue Condensed ........  20                  (400)
        //
        // A méret- és súlylétra ÁTVEHETŐ (ettől lesznek a felirat-magasságok és
        // a sorközök felismerhetően „picasásak"), a betűtípusok viszont
        // kereskedelmiek (Linotype), nem szállíthatók.
        readonly property var fontSizeLadder: [11, 12, 13, 14, 16, 18]
        readonly property int fontWeightNormal: 400
        readonly property int fontWeightBold: 700
        //: a nagy, KESKENY feliratokhoz (fejlécek/címsorok) — a Picasában
        //: HelveticaNeue Condensed 20 és MediumCond 28
        readonly property int headlineSize: 20
        readonly property int headlineLargeSize: 28

        readonly property int fontSize: 12              // felület: 11–13 px

        //: #2990: a SZERKESZTŐ-PANEL két felirat-fokozata, az eredeti ABSZOLÚT
        //: értékeivel. A `fontmacros_win.tre` mérve:
        //:
        //:   `m_fxlabel`           fontsize **11**, fontweight **700**
        //:                         → `editpanel/fxlabelN`, az effekt-csempék
        //:   `m_buttonfontCbelow`  fontsize **12**, fontweight 400
        //:                         → `editpanel/crop-label`, az eszköz-csempék
        //:   `m_buttonfontC`       fontsize **12**, fontweight 400
        //:                         → minden sima gombfelirat
        //:
        //: ⚠️ A két szám VISZONYA is követelmény, nem csak az értékük: a #422-ben
        //: a felhasználó kimondta, hogy az effekt-csempe felirata NE legyen
        //: nagyobb az eszköz-csempéénél. Az eredeti 11 < 12 ezt teljesíti — ha
        //: valaha megcserélődnének, a panasz visszajönne. Őr:
        //: `tests/app/qml_functional/test_felirat_fokozatok_2990.py`.
        //:
        //: Korábban mindkettő `fontSize - 2` = 10 volt (a #422 úgy tette őket
        //: egyenlővé); a döntés azóta ITT él, nem elemenként beírva.
        readonly property int tileLabelSize: 11
        readonly property int buttonLabelSize: 12

        //: A TÖBBSOROS feliratok sorköze, képpontban — az eredeti Picasa
        //: `fontleading` tulajdonsága (#2494/#2567). Nem becslés és nem a Qt
        //: betűtípus-metrikája: a `fontmacros_win.tre` MINDKÉT ide tartozó
        //: makrója ugyanezt a 10-et írja elő —
        //:   `m_buttonfontC`  (a Visszavonás/Újra és minden sima gombfelirat):
        //:       fontsize 12, textwrap 1, **fontleading 10**
        //:   `m_fxlabel`      (a csempefelirat, `ui-audit-editor.md` 3.3):
        //:       fontsize 11, fontweight 700, **fontleading 10**
        //: A tulajdonos képernyőmentésén (`141421.jpg`, 1920 × 1200, 1:1) az
        //: alapvonal-távolság mindkét helyen MÉRVE is 10 képpont — két
        //: független módszer, azonos érték.
        //:
        //: ⚠️ Ezért FIX képpont (`Text.FixedHeight`), nem arány: az arány a
        //: platform betűtípusának sormagasságát szorozná, tehát Windowson és
        //: Linuxon MÁS képpontszámot adna — épp azt veszítenénk el, amit
        //: átveszünk. A `Theme.fontSize` állandó (12), a felirat-fokozat
        //: (`fontSize - 2` = 10) tehát nem mozdul ki alóla.
        readonly property int lineLeading: 10
        readonly property int folderTitleSize: 16         // csoport-fejléc / 600
        readonly property string monoFamily: "IBM Plex Mono, monospace"

        // #526 2. pont: a szabad HELYETTESÍTŐ betűtípus kiválasztása MÉRÉSSEL
        // tartozik eldőlni (felirat-szélességek összevetése), és ahhoz a `.ytf`
        // glyph-táblája kellene — az még nincs megfejtve. Amíg nincs mérés,
        // SZÁNDÉKOSAN a rendszer alapértelmezett sans-serifjét használjuk (üres
        // családnév = a Qt alapértelmezése): egy találomra választott család
        // rosszabb, mint a semleges alap, és nehezebb is később cserélni.
        readonly property string uiFamily: ""
        readonly property string condensedFamily: ""
    }

    // ------- a NYILVÁNOS felület -------
    //
    // Minden nyers színt PONTOSAN EGYSZER ereszt át a megjelenítési
    // módon (`_szin`). A tokenek jelentése, mérése és a hozzájuk tartozó
    // bizonyítékok a `nyers` blokkban, a definíciók mellett állnak.

    readonly property color brandRed: tema._szin("brandRed", nyersTokenek.brandRed)
    readonly property color brandYellow: tema._szin("brandYellow", nyersTokenek.brandYellow)
    readonly property color brandGreen: tema._szin("brandGreen", nyersTokenek.brandGreen)
    readonly property color brandBlue: tema._szin("brandBlue", nyersTokenek.brandBlue)
    readonly property color brandPurple: tema._szin("brandPurple", nyersTokenek.brandPurple)
    readonly property color brandSlate: tema._szin("brandSlate", nyersTokenek.brandSlate)
    readonly property color canvasBg: tema._szin("canvasBg", nyersTokenek.canvasBg)
    readonly property color contentPanel: tema._szin("contentPanel", nyersTokenek.contentPanel)
    readonly property color panelBg: tema._szin("panelBg", nyersTokenek.panelBg)
    readonly property color chromeBg: tema._szin("chromeBg", nyersTokenek.chromeBg)
    readonly property color chromeBorder: tema._szin("chromeBorder", nyersTokenek.chromeBorder)
    readonly property color ink: tema._szin("ink", nyersTokenek.ink)
    readonly property color lightboxBg: tema._szin("lightboxBg", nyersTokenek.lightboxBg)
    readonly property color textDark: tema._szin("textDark", nyersTokenek.textDark)
    readonly property color thumbCard: tema._szin("thumbCard", nyersTokenek.thumbCard)
    readonly property color picasaGreen: tema._szin("picasaGreen", nyersTokenek.picasaGreen)
    readonly property color selectionBlue: tema._szin("selectionBlue", nyersTokenek.selectionBlue)
    readonly property color panelSelection: tema._szin("panelSelection", nyersTokenek.panelSelection)
    readonly property color panelSelectionActive: tema._szin("panelSelectionActive", nyersTokenek.panelSelectionActive)
    readonly property color folderGold: tema._szin("folderGold", nyersTokenek.folderGold)
    readonly property color folderGoldBorder: tema._szin("folderGoldBorder", nyersTokenek.folderGoldBorder)
    readonly property color listPanelBg: tema._szin("listPanelBg", nyersTokenek.listPanelBg)
    readonly property color listPanelBorder: tema._szin("listPanelBorder", nyersTokenek.listPanelBorder)
    readonly property color listPanelShadow: tema._szin("listPanelShadow", nyersTokenek.listPanelShadow)
    readonly property color listPanelInnerLight: tema._szin("listPanelInnerLight", nyersTokenek.listPanelInnerLight)
    readonly property color listPanelInnerLight2: tema._szin("listPanelInnerLight2", nyersTokenek.listPanelInnerLight2)
    readonly property color scrollThumbEdgeDark: tema._szin("scrollThumbEdgeDark", nyersTokenek.scrollThumbEdgeDark)
    readonly property color scrollThumbMid: tema._szin("scrollThumbMid", nyersTokenek.scrollThumbMid)
    readonly property color scrollThumbLight: tema._szin("scrollThumbLight", nyersTokenek.scrollThumbLight)
    readonly property color scrollThumbEdgeSoft: tema._szin("scrollThumbEdgeSoft", nyersTokenek.scrollThumbEdgeSoft)
    readonly property color folderBlue: tema._szin("folderBlue", nyersTokenek.folderBlue)
    readonly property color folderBlueBorder: tema._szin("folderBlueBorder", nyersTokenek.folderBlueBorder)
    readonly property color albumOrange: tema._szin("albumOrange", nyersTokenek.albumOrange)
    readonly property color albumOrangeBorder: tema._szin("albumOrangeBorder", nyersTokenek.albumOrangeBorder)
    readonly property color specialAlbumGreen: tema._szin("specialAlbumGreen", nyersTokenek.specialAlbumGreen)
    readonly property color specialAlbumGreenBorder: tema._szin("specialAlbumGreenBorder", nyersTokenek.specialAlbumGreenBorder)
    readonly property color projectPurple: tema._szin("projectPurple", nyersTokenek.projectPurple)
    readonly property color projectPurpleBorder: tema._szin("projectPurpleBorder", nyersTokenek.projectPurpleBorder)
    readonly property color labelGray: tema._szin("labelGray", nyersTokenek.labelGray)
    readonly property color labelGrayBorder: tema._szin("labelGrayBorder", nyersTokenek.labelGrayBorder)
    readonly property color folderArrow: tema._szin("folderArrow", nyersTokenek.folderArrow)
    readonly property color linkBlue: tema._szin("linkBlue", nyersTokenek.linkBlue)
    readonly property color panelHeaderBg: tema._szin("panelHeaderBg", nyersTokenek.panelHeaderBg)
    readonly property color panelHeaderTop: tema._szin("panelHeaderTop", nyersTokenek.panelHeaderTop)
    readonly property color panelHeaderText: tema._szin("panelHeaderText", nyersTokenek.panelHeaderText)
    readonly property color panelSelectionText: tema._szin("panelSelectionText", nyersTokenek.panelSelectionText)
    readonly property color panelYearText: tema._szin("panelYearText", nyersTokenek.panelYearText)
    readonly property color listHighlightAlt: tema._szin("listHighlightAlt", nyersTokenek.listHighlightAlt)
    readonly property color listDragTarget: tema._szin("listDragTarget", nyersTokenek.listDragTarget)
    readonly property color listCategoryBg: tema._szin("listCategoryBg", nyersTokenek.listCategoryBg)
    readonly property color listDotMarker: tema._szin("listDotMarker", nyersTokenek.listDotMarker)
    readonly property color listStickyBg: tema._szin("listStickyBg", nyersTokenek.listStickyBg)
    readonly property color folderTitle: tema._szin("folderTitle", nyersTokenek.folderTitle)
    readonly property color folderDate: tema._szin("folderDate", nyersTokenek.folderDate)
    readonly property color addDescription: tema._szin("addDescription", nyersTokenek.addDescription)
    readonly property color thumbBorder: tema._szin("thumbBorder", nyersTokenek.thumbBorder)
    readonly property color thumbSelection: tema._szin("thumbSelection", nyersTokenek.thumbSelection)
    readonly property color thumbHover: tema._szin("thumbHover", nyersTokenek.thumbHover)
    readonly property color infoBar: tema._szin("infoBar", nyersTokenek.infoBar)
    readonly property color infoBarText: tema._szin("infoBarText", nyersTokenek.infoBarText)
    readonly property color trayBg: tema._szin("trayBg", nyersTokenek.trayBg)
    readonly property color trayBorder: tema._szin("trayBorder", nyersTokenek.trayBorder)
    readonly property color trayPanelBg: tema._szin("trayPanelBg", nyersTokenek.trayPanelBg)
    readonly property color trayTokenHighlight: tema._szin("trayTokenHighlight", nyersTokenek.trayTokenHighlight)
    readonly property color trayTokenHighlightText: tema._szin("trayTokenHighlightText", nyersTokenek.trayTokenHighlightText)
    readonly property color viewerBg: tema._szin("viewerBg", nyersTokenek.viewerBg)
    readonly property color captionBar: tema._szin("captionBar", nyersTokenek.captionBar)
    readonly property color captionBarText: tema._szin("captionBarText", nyersTokenek.captionBarText)
    readonly property color captionToggleBg: tema._szin("captionToggleBg", nyersTokenek.captionToggleBg)
    readonly property color captionToggleBorder: tema._szin("captionToggleBorder", nyersTokenek.captionToggleBorder)
    readonly property color sliderGroove: tema._szin("sliderGroove", nyersTokenek.sliderGroove)
    readonly property color sliderGrooveBorder: tema._szin("sliderGrooveBorder", nyersTokenek.sliderGrooveBorder)
    readonly property color sliderGrooveTick: tema._szin("sliderGrooveTick", nyersTokenek.sliderGrooveTick)
    readonly property color sliderHandleGrooveDark: tema._szin("sliderHandleGrooveDark", nyersTokenek.sliderHandleGrooveDark)
    readonly property color sliderHandleGrooveLight: tema._szin("sliderHandleGrooveLight", nyersTokenek.sliderHandleGrooveLight)
    readonly property color sliderHandleTopLeft: tema._szin("sliderHandleTopLeft", nyersTokenek.sliderHandleTopLeft)
    readonly property color sliderHandleBottomLeft: tema._szin("sliderHandleBottomLeft", nyersTokenek.sliderHandleBottomLeft)
    readonly property color sliderHandleTopRight: tema._szin("sliderHandleTopRight", nyersTokenek.sliderHandleTopRight)
    readonly property color sliderHandleBottomRight: tema._szin("sliderHandleBottomRight", nyersTokenek.sliderHandleBottomRight)
    readonly property color sliderHandleTopLeftPressed: tema._szin("sliderHandleTopLeftPressed", nyersTokenek.sliderHandleTopLeftPressed)
    readonly property color sliderHandleBottomLeftPressed: tema._szin("sliderHandleBottomLeftPressed", nyersTokenek.sliderHandleBottomLeftPressed)
    readonly property color sliderHandleTopRightPressed: tema._szin("sliderHandleTopRightPressed", nyersTokenek.sliderHandleTopRightPressed)
    readonly property color sliderHandleBottomRightPressed: tema._szin("sliderHandleBottomRightPressed", nyersTokenek.sliderHandleBottomRightPressed)
    readonly property color sliderHandleBorder: tema._szin("sliderHandleBorder", nyersTokenek.sliderHandleBorder)
    readonly property color sliderHandleBorderPressed: tema._szin("sliderHandleBorderPressed", nyersTokenek.sliderHandleBorderPressed)
    readonly property color selectionDim: tema._szin("selectionDim", nyersTokenek.selectionDim)
    readonly property color starYellow: tema._szin("starYellow", nyersTokenek.starYellow)
    readonly property color textGray: tema._szin("textGray", nyersTokenek.textGray)
    readonly property color controlBase: tema._szin("controlBase", nyersTokenek.controlBase)
    readonly property color buttonBg: tema._szin("buttonBg", nyersTokenek.buttonBg)
    readonly property color placeholderText: tema._szin("placeholderText", nyersTokenek.placeholderText)
    readonly property color trackBg: tema._szin("trackBg", nyersTokenek.trackBg)
    readonly property color shadeLight: tema._szin("shadeLight", nyersTokenek.shadeLight)
    readonly property color shadeDark: tema._szin("shadeDark", nyersTokenek.shadeDark)
    readonly property color buttonTopNormal: tema._szin("buttonTopNormal", nyersTokenek.buttonTopNormal)
    readonly property color buttonBottomNormal: tema._szin("buttonBottomNormal", nyersTokenek.buttonBottomNormal)
    readonly property color buttonTopDown: tema._szin("buttonTopDown", nyersTokenek.buttonTopDown)
    readonly property color buttonBottomDown: tema._szin("buttonBottomDown", nyersTokenek.buttonBottomDown)
    readonly property color buttonHoverShade: tema._szin("buttonHoverShade", nyersTokenek.buttonHoverShade)
    readonly property color buttonBorder: tema._szin("buttonBorder", nyersTokenek.buttonBorder)
    readonly property color buttonToggledBorder: tema._szin("buttonToggledBorder", nyersTokenek.buttonToggledBorder)
    readonly property color logoDisc: tema._szin("logoDisc", nyersTokenek.logoDisc)
    readonly property color iconInk: tema._szin("iconInk", nyersTokenek.iconInk)

    // A nem-szín tokenek (méretek, betűcsaládok) változatlanul mennek át:
    // a megjelenítési mód SZÍNTRANSZFORMÁCIÓ, méretet nem érint.
    readonly property int tooltipDelay: nyersTokenek.tooltipDelay
    readonly property var fontSizeLadder: nyersTokenek.fontSizeLadder
    readonly property int fontWeightNormal: nyersTokenek.fontWeightNormal
    readonly property int fontWeightBold: nyersTokenek.fontWeightBold
    readonly property int headlineSize: nyersTokenek.headlineSize
    readonly property int headlineLargeSize: nyersTokenek.headlineLargeSize
    readonly property int fontSize: nyersTokenek.fontSize
    readonly property int tileLabelSize: nyersTokenek.tileLabelSize
    readonly property int buttonLabelSize: nyersTokenek.buttonLabelSize
    readonly property int lineLeading: nyersTokenek.lineLeading
    readonly property int folderTitleSize: nyersTokenek.folderTitleSize
    readonly property string monoFamily: nyersTokenek.monoFamily
    readonly property string uiFamily: nyersTokenek.uiFamily
    readonly property string condensedFamily: nyersTokenek.condensedFamily
}
