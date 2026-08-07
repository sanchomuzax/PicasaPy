# Dizájn-kézikönyv — Picasa 3.9 hűség-referencia

**Rétegek (2026-07-18-tól):** az elsődleges dizájn-forrás a felhasználó
**„Picasa 3 Dizajnkezikonyv"** brandbookja, helyi másolatban:
`docs/assets/brandbook/2026-07-20-picasapy-dizajnkezikonyv.html`
(14 fejezet: alapelvek, logó, szín, tipográfia, ikonográfia, gombok,
elrendezés, komponensek, szűrők, arcfelismerés, mappakezelő, feltöltés,
nyelvezet, indítóképernyő). Ha a felhasználó frissített változatot ad,
az új dátumozott fájl kerül a helyére, és ez a hivatkozás frissítendő.
Ahol a kézikönyv rendelkezik, az felülírja az alábbi
screenshot-mintavételeket; ahol hallgat, a screenshotok maradnak a mérce.

A kézikönyv fő döntései (implementálva):
- **Vászon** #EAEAEA-n úszó **fehér tartalomkártya** (#FFFFFF, 1px #CDCDCD).
- Csoport-fejléc: **16px/600 sans, tinta** (#1C1B19) — a 3.9-es Georgia
  szerif helyett, tudatos modernizálás; „Leírás hozzáadása" dőlt #A29E96.
- **Mappa arany** #EBCC8F ikonok, amber ▸ nyilak (#E0A92E); évszám-címkék
  mono betűvel (#7A776F).
- Eszköztár/sávok #E2E2E2; tinta #1C1B19; hivatkozás #1A0DAB.
- Szűrősor: ★ ☺ ⚲ ▤ + csúszka; **aktív szűrő tónusa jelölő kék** #83A7BD.
- Tálca: nagyítás-csúszka −/+ jelekkel; az **egyetlen zöld gomb jobbra**
  igazítva — képernyőnként egy elsődleges tett (alapelv 04).
- Márka-színek (csak márka-kontextus): #E04A3F / #FFD34E / #0DAB62 /
  #448AFD / #9B479F, szójel pala #4B5D5F.

Történeti forrás: a felhasználó **magyar nyelvű Picasa 3.9-éről** készült 35 db
1920×1080-as screenshot (`research/testdata/screenshot/`, 2026-07-17,
gitignore-olt — személyes tartalom!). Minden szín pixelmintavétellel, minden
méret pixelméréssel került ide. A QML-oldali tokenek:
`src/picasapy/app/qml/PicasaPy/Theme.qml`.

## Hiteles forrás: `runtime/constants.ui` (2026-08-06)

A screenshot-mintavétel mellé előkerült a Picasa **saját UI-konstansfájlja**
(`research/copy_Picasa_3_7/Picasa3/runtime/constants.ui`, `[Picasa2]`
szekció). Ezek nem mintavett, hanem **eredeti, deklarált** értékek — ahol
eltérés van, ez a mérvadó. Az eddigi mintavételünket **megerősítik**
(`#f3f3f3` panelháttér, `#83a7bd` kijelölés, `#009eff` indexkép-keret,
`#634b45` Georgia mappa-cím 20 pt) — és kiegészítik:

| `constants.ui` kulcs | Érték | Mit ad hozzá |
|---|---|---|
| `alist_height` | 22 | mappa-panel sormagasság (egyezik a mérésünkkel) |
| `alist_indent` | 17 | **fa-behúzás szintenként** — eddig nem volt adatunk |
| `alist_bgcolor` | `#F3F3F3` | panelháttér ✅ |
| `alist_hicolor_win` | `#83A7BD` | **hover/jelölő** tónus ✅ |
| `alist_hicolor2_win` | `#E5E2DA` | **másodlagos kiemelés** (meleg szürke) — új |
| `alist_selcolor_win` | `#25648B` | **valódi kijelölés** (sötétkék) — a `#83A7BD` ennél világosabb; a kettő külön állapot! |
| `alist_dragcolor` | `#82A6BD` | húzás-célpont jelzése |
| `alist_catcolor` | `#EDEAE4` | kategória-fejléc háttere |
| `alist_scatcolor` | `#25648B` | kijelölt kategória |
| `alist_stickycolor` | `#EAE7DC` | „ragadós" (rögzített) fejléc |
| `alist_dotcolor` | `#BEBEBE` | elválasztó pontok |
| `alabel_fldrcol` / `alabel_albumcol` | `#e2e2e2` | mappa- és album-címke alap |
| `alabel_fldrhicol` / `alabel_albumhicol` | `#f2f2f2` | ugyanaz hoverben |
| `alabel_buttfont_win` | Praxis Semi Bold/Heavy, 12 | a gombfelirat betűje |
| `alabel_subhead` | 20 | alcím-sáv magassága |
| `alayout_gutter` | 24 | lightbox külső margó |
| `alayout_thumbGutterX` / `Y` | 12 / 22 | **indexkép-rács térközei** — a függőleges nagyobb (felirat helye) |
| `alayout_titleFont` / `Size` / `Color` | Georgia / 20 / `#634B45` | mappa-cím ✅ |
| `alayout_titleOffsetX` | 28 | a cím bal behúzása |
| `alayout_bodyFont` / `Size` | Georgia / 14 | **a dátumsor is Georgia** ✅ |
| `thumbsel_color1` / `color2` | `#009EFF` / `#FFFFFF` | **a kijelölt indexkép kerete KÉTSZÍNŰ**: kívül azúr, belül fehér — a mostani egyszínű keretünk ezzel pontosítható |
| `publishtoweb_color` | `#0000FF` | a „Feltöltés a webre" hivatkozás színe |

Két tanulság: (1) a mappalista **három** kékárnyalattal dolgozik
(hover `#83A7BD`, kijelölés `#25648B`, húzás `#82A6BD`), nem eggyel;
(2) a kijelölt indexkép kerete kétszínű — ez az a részlet, amitől a Picasa
rácsa „ropogósnak" hat.

**Implementálva (2026-08-06, #384):** a mappafa/albumlista (`FolderPane.qml`,
`FolderTreeItem.qml`) mostantól különválasztja a hover-tónust
(`Theme.panelSelection`/`Theme.selectionBlue`, `#83a7bd`) a valódi
kijelöléstől (`#25648b`); az indexkép kijelölt kerete (`ThumbDelegate.qml`)
kétrétegű (kívül `Theme.thumbSelection` `#009eff`, belül `Theme.thumbCard`
fehér); a fa-behúzás `17px`/szint. A `#25648b` egyelőre **nem** önálló
Theme-token — a `Theme.qml` forró fájl, csak az integrátor módosíthatja;
a komponensek egy helyi, kommentelt állandót (`__selectionActiveColor`)
használnak addig. Integrátor-teendő: felvenni a `Theme.panelSelectionActive`
tokent (világos `#25648b`; sötét témára a `constants.ui`-ban nincs adat,
a `selectionBlue` világos/sötét arányából becsülve kb. `#1b4a68`), és a
fenti helyi állandókat erre cserélni. A rács-térközök
(`alayout_thumbGutterX/Y`) és a többi méret-pontosítás (`alayout_gutter`,
`alist_hicolor2_win`, `alist_catcolor` stb.) ezen a jegyen kívül maradt —
a `LightboxFeed.qml` rács-matematikája (dinamikus oszlopszám, egyenletes
cellaszélesség) egyben változna, ezért külön jegyet érdemel.

## Színtokenek

| Token | Érték | Hol |
|---|---|---|
| chromeBg | `#e8e8e8` | eszköztár, menük, néző-oldalpanel |
| panelBg | `#f3f3f3` | bal mappa-panel háttér |
| panelHeaderBg | `#e1e4e7` | szekció-fejléc sáv (enyhe gradiens fölfelé `#eef0f2`-ig) |
| panelSelection | `#83a7bd` | kijelölt mappa-sor (teljes szélesség, fehér szöveg) |
| lightboxBg | `#eaeaea` | rács-háttér |
| folderTitle | `#634b45` | mappa-cím a lightboxban — **Georgia szerif!** |
| thumbCard | `#ffffff` | indexkép fehér kerete (5px padding) |
| thumbBorder | `#d9d9d9` | indexkép 1px szegélye |
| thumbSelection | `#009eff` | kijelölt indexkép kerete (2–3px, élénk azúr) |
| infoBar | `#568fb7` | alsó kék infó-sáv (tömör szín, fehér félkövér szöveg) |
| trayBg | `#f8f8f8` | alsó tálca |
| picasaGreen | `#3b8f00` | zöld akciógomb (Feltöltés a Google Fotókba) |
| viewerBg | `#808080` | egyképes néző képterülete (tiszta középszürke) |
| filmstripBg | `#dcdcdc` | néző felső filmszalag-sávja |
| toolTabBg | `#cac5bc` | néző eszközpanel fül-sávja |

## Tipográfia

- Alap UI: rendszer sans (Picasán: Segoe UI), ~12px.
- **Mappa-cím: Georgia (szerif), ~17px, `#634b45`** — a Picasa
  legfelismerhetőbb tipográfiai jegye. Alatta a dátumsor is Georgia, ~12px.
- Infó-sáv: félkövér, fehér, ~12px.
- Évszám-elválasztók a mappa-panelen: szürke `#8a8a8a`, sima, ~12px.

## Elrendezés-méretek (1920×1080 alapon; arányosítva viendő át)

| Elem | Pixel @1920×1080 | Megjegyzés |
|---|---|---|
| Menüsor | ~20px magas | natív |
| Eszköztár | ~37px | Importálás gomb + nézetváltók balra, Szűrők középen, kereső jobbra |
| Bal panel szélessége | 386px (~20%) | 1280-as ablaknál ≈ 250px — **arányosan skálázandó** |
| Panel-sor magasság | 22px | szekció-fejléc és mappa-sor egyaránt |
| Infó-sáv | ~15px | nálunk 20px (olvashatóság) |
| Tálca | ~85px | 800 magas ablaknál ≈ 64px |
| Néző felső sáv | ~30px | filmszalag ~38px magas thumbokkal |
| Néző eszközpanel | **FIX 280px széles** | fülek + gombrács + hisztogram alul — **NEM skálázandó** (ld. lábjegyzet) |

> **#411 — a Néző eszközpanel szélessége FIX, nem ablakarányos.** A
> táblázat többi sora ("arányosítva viendő át" fejléc) az ablakmérethez
> igazodó értékeket ad meg (pl. a Bal panel szélessége 1280px-es ablaknál
> ≈250px-re vetítendő) — a szerkesztő-eszközpanel viszont az EREDETI
> Picasában is fix pixelszélességű, minden ablakméretnél 280px. A #405-ös
> kör tévesen ablakarányosan skálázta le 190px-re; a felhasználó
> screenshot-összevetése (~955px széles ablaknál ~275px-es eredeti panel)
> bizonyította a hibát. `EditorPanel.qml` `implicitWidth: 280` és
> `PhotoViewer.qml` `Layout.preferredWidth: 280` — mindkettő állandó,
> semmilyen ablakszélesség-számítás nem érintheti.

## Komponens-leltár és állapotok

- **Mappa-panel**: szekciók („Albumok (n)", „Projektek (n)", „Mappák (n)")
  lenyíló háromszöggel; alattuk **évszám-csoportok** (2026, 2025, …) sima
  szürke sorként; mappa-sorok sárga mappa-ikonnal, névvel és `(darabszám)`-mal.
  Kijelölés: teljes soros `#83a7bd` háttér, fehér szöveg.
- **Lightbox**: mappánként fejléc (ikon + szerif cím + hosszú dátum +
  műveletsor: zöld ▶ lejátszó, kis gombok, „Feltöltés" legördülő) és
  „Leírás hozzáadása" szürke sor; a rács fehér-kártyás thumbokkal.
  Geo-címkés képen piros pin jelvény a jobb alsó sarokban.
- **Indexkép-állapotok**: alap = fehér kártya + 1px `#d9d9d9`; kijelölt =
  2–3px `#009eff`; hover: nincs látványos effekt az eredetiben (mi finoman
  jelöljük). Csillag: sárga ★ jelvény. Videó: ▶ overlay.
- **Infó-sáv szövegformátumok** (pontosan ezek!):
  - mappa: `25 képek   2026. január 2., péntek-2026. május 18., hétfő   37,5 MB a lemezen`
    (mi szándékosan a helyes „25 kép" alakot írjuk)
  - kijelölés: `fájlnév.jpg   2026. 02. 20. 3:28:06   1920x1080 képpont   1,4 MB`
  - néző: `mappa > fájlnév.jpg   dátum   4080x3060 képpont   3,6 MB   (199 / 10)`
- **Néző**: „Vissza a könyvtárhoz" gomb balra fent; középen „Lejátszás" +
  filmszalag ◀ ▶ nyilakkal (aktuális thumb azúr kerettel); jobbra A/AB/AA
  összehasonlító gombok; kép alatt „Készítsen képaláírást!"; bal panel
  fülekkel (Gyakori javítások: Vágás, Kiegyenesítés, Vörösszem, **Jó napom
  van**, Automatikus kontraszt, Automatikus szín, Retusálás, Szöveg,
  Derítőfény-csúszka, Visszavonás/Újra) és lent „Hisztogram és
  fényképezőgép-adatok" doboz.
- **Tálca**: balra tray-halom + címke; középen kis gomb-oszlop; zöld
  „Feltöltés a Google Fotókba"; E-mail/Nyomtatás/Exportálás ikon+felirat;
  jobbra méret-csúszka + kör ikongombok (személy, hely, címke, infó).

## Réteg-geometria: a Picasa saját méretei (2026-08-07)

A `respack.yt` rétegeinek **határoló dobozai** képpontra megadják az eredeti
elrendezést. **Fontos fenntartás:** a fő ablak tervezési vászna **800×534** volt
(nem élő ablakméret) — az abszolút számok helyett az **arányok** és a
**sávmagasságok** az érvényesek, mert azok nem skálázódtak.

### Sávmagasságok (ezek abszolút értékek)

| sáv | magasság | a mi guide-unk |
|---|---|---|
| felső fül-sáv | 29 px | — |
| **eszköztár** | **37 px** | ~37 px ✅ **egyezik** |
| kereső/szűrő sor | 25 px | — |
| **mappa-fejléc** | 86 px + 4 px árnyék | — |
| alsó vezérlő-sáv (tálca) | 105 px | ~85 px (közeli) |

### Panelszélességek (a 800 px-es vászonhoz viszonyítva)

bal mappa-panel **210 px ≈ 26%** (benne az albumlista 196 px) · jobb fiók
**276 px** · a teljes jobb terület 388 px. A mi 20%-os bal panelünk ehhez képest
**keskenyebb** — érdemes 25% körülre vinni.

### Tömör kitöltések — HÁROM tokenünk igazolva

| réteg | szín | tokenünk |
|---|---|---|
| `thumbui/basepanel` | `#e8e8e8` | `chromeBg` ✅ |
| `thumbui/scratchpadbase` | `#f8f8f8` | `trayBg` ✅ |
| `headerpanel/headerbase0` | `#eaeaea` | `lightboxBg` ✅ |

**Új, eddig nem ismert:** a mappa-fejléc **két rétegű** — `headerbase0` `#eaeaea`
és `headerbase1` `#f8f8f8` —, vagyis **finom átmenet** van benne, nem egyszínű.
Erre nincs tokenünk. Az „Emberek" panel alapja `#e2e2e2`.

> **Óvatosan a rétegszínekkel:** csak a valódi háttér-rétegek (`rect`,
> `decrect`, `static`) színe hiteles. A `clip`/`superbutton`/`buttcontainer`
> típusoknál a szín gyakran csak találat-teszt maszk (pl. lila, mustársárga
> értékek) — ezeket **nem szabad** UI-színként átvenni.

### Gombméretek

A leggyakoribb kettő: **14×14 px** (kis ikongombok) és **55×36 px** (a tálca
alatti műveletgombok). A fejléc gombjai egységesen **29×27 px**, a lista-fejléc
gombjai **29×22 px**.

## A néző és a diavetítés — két KÜLÖN modul (pontosítás, 2026-08-07)

Forrás-ellenőrzés után egyértelmű, hogy a Picasa két külön felületet használt,
és ezt korábban összemostuk:

- **`editpanel`** = a **szerkesztő/egyképes nézet**: bal oldalt az eszközpanel,
  **fent FILMSZALAG** (`editpanel/filmstrip`, `filmclip`, `filmcontainer`,
  `indicator`). A dizájn-kézikönyv filmszalag-leírása tehát **helyes**.
- **`oneup`** = a **teljes képernyős diavetítés** overlay-e: kilépés, előző/
  következő, forgatás, csillag, **átmenettípus-választó**, felirat-gomb,
  idővonal és „Display Time" +/−. Ebben **nincs** filmszalag — nem is kell.

## Ikonok

Az eredeti sárga mappa-, szűrő- és tálca-ikonok bitmap-ek. Nálunk:
rajzolt/vektoros megfelelők (NEM emoji — az platformfüggő és offscreen
fontban hiányzik). Ikonjegyzék a screenshotokon; portolás fokozatosan.

## Ismert hűség-hiányok (2026-07-18)

1. Qt alap widget-króm (gombok, csúszkák, görgetősávok) ≠ Picasa lekerekített
   gradienses stílusa → egyedi QML-stílus kell (MVP-végi polírozás).
2. Szűrősáv csak vizuális; dátum-csúszka hiányzik.
3. Mappa-panel: fa-nézet és Projektek/Albumok letöltése szekciók hiányoznak.
4. Néző: A/AB/AA gombok, zoom-csúszka és 1:1 gomb hiányzik.
5. Tálca tray-halom vizualizáció és címke-buborék hiányzik.

## Téma-politika (2026-07-18, kiegészítve 2026-07-25 / #28)

A PicasaPy **alapból világos** — az OS sötét módját sehol nem veszi át:
Fusion stílus + explicit paletta (Main.qml), világos színséma-kérés,
és nem-natív (QML) dialógusok, hogy a rendszer sötét mappaválasztója se
üssön át. Az ablakkeret (címsor) a kompozitoré — az követheti az OS-t.

**Sötét téma (#28, V3).** A váltás kizárólag a felhasználó döntése:
Nézet → Sötét téma. A kapcsoló a `controller.darkTheme` (QSettings
`view/darkTheme`, perzisztens), ehhez van kötve a `Theme.dark` — minden
szín-token abból számol. **A hívó QML-ek nem tudnak a témáról:** a
tokennevek (`canvasBg`, `ink`, `panelBg`…) változatlanok, csak az
értékük párosodott. Ezért a szabály: **új felületen tilos hardkódolt
szín** — ami nem token, az sötét módban fehér foltként marad ott.

| Token | Világos | Sötét |
|---|---|---|
| canvasBg | `#eaeaea` | `#232323` |
| contentPanel | `#ffffff` | `#2e2e2e` |
| panelBg | `#f3f3f3` | `#282828` |
| chromeBg | `#e2e2e2` | `#303030` |
| chromeBorder | `#cdcdcd` | `#4a4a4a` |
| ink | `#1c1b19` | `#ececea` |
| picasaGreen | `#3b8f00` | `#6cbf3f` |
| selectionBlue | `#83a7bd` | `#4d6b80` |
| linkBlue | `#1a0dab` | `#8ab4f8` |
| infoBar | `#568fb7` | `#3c6382` |
| trayBg | `#f8f8f8` | `#262626` |
| viewerBg | `#808080` | `#1a1a1a` |
| trackBg | `#dddddd` | `#3a3a3a` |
| buttonBg | `#e8e8e8` | `#3a3a3a` |

A **márkaszínek** (a logó pirosa/sárgája/kékje…) és a fotó fölé kerülő
rétegek (néző-feliratok, arckeretek, sötét fátyol) mindkét témában
azonosak — azok nem a felület, hanem a kép kontextusa.
