# Dizájn-kézikönyv — Picasa 3.9 hűség-referencia

Forrás: a felhasználó **magyar nyelvű Picasa 3.9-éről** készült 35 db
1920×1080-as screenshot (`research/testdata/screenshot/`, 2026-07-17,
gitignore-olt — személyes tartalom!). Minden szín pixelmintavétellel, minden
méret pixelméréssel került ide. A QML-oldali tokenek:
`src/picasapy/app/qml/PicasaPy/Theme.qml` — **ez a doksi az igazságforrás**,
a Theme ebből származik.

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
| Bal panel szélessége | 386px (~20%) | 1280-as ablaknál ≈ 250px |
| Panel-sor magasság | 22px | szekció-fejléc és mappa-sor egyaránt |
| Infó-sáv | ~15px | nálunk 20px (olvashatóság) |
| Tálca | ~85px | 800 magas ablaknál ≈ 64px |
| Néző felső sáv | ~30px | filmszalag ~38px magas thumbokkal |
| Néző eszközpanel | ~280px széles | fülek + gombrács + hisztogram alul |

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
