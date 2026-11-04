# Picasa indítóikon: erőforrások és méretválasztás

Mérés: 2026-11-04, #6509. A forrásfájl a helyi `Picasa3.exe`, SHA-256:
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti bináris és a kinyert képek nincsenek a repóban.

## Mérési módszer

Az EXE `RT_GROUP_ICON` és `RT_ICON` erőforrásait `pefile`-lal olvastam ki a
a kutatói Python-környezetben, a képkockákat
Pillow-val RGBA képpé dekódoltam. A fő indítóikon két csoportja a 105
(`0x9b4278` RVA) és a 320 (`0x9fde58` RVA), mindkettő 10 képkockával,
1033-as nyelvvel. A két csoport képkockáinak látható rajza méretenként és
színmélységenként azonos; a 256 px-es képkocka a 105-ös csoportban PNG, a
320-as csoportban DIB. A többi csoport vezérlő- vagy bővítményikon, nem a fő
indítójel.

A méret az alfa-csatornán teljesen fedett képpontok (`alpha == 255`)
befoglaló téglalapja. A koordináták bal felülről indulnak, a befoglaló
téglalap félig nyitott; a középpont a téglalap éleinek számtani közepe.
Ez közvetlen rasztermérés, nem illesztett kör. Az élsimítás és az árnyék
miatt az alfa-küszöb módosítása néhány szélső képpontot változtat. Ahol a
két tengely mérete eltér, mindkettőt közlöm, nem kerekítem egy átmérővé.

## Eredeti Picasa és PicasaPy ICO

Az eredeti fő ikoncsoportok tényleges méretei 16, 32, 48 és 256 px. Nincs
20, 24, 40, 64 vagy 128 px-es Picasa főikon-erőforrás. A PicasaPy
`src/picasapy/app/assets/icon.ico` méretei 16, 24, 32, 48, 64, 128 és 256 px.

| Méret | Eredeti Picasa alak | Eredeti teljesen fedett befoglaló méret és középpont | PicasaPy alak | PicasaPy teljesen fedett befoglaló méret és középpont |
|---:|---|---|---|---|
| 16 | Négyzetes, teljesen fedett csempe; nincs kör | 16×16, közép (8; 8), körátmérő nem értelmezhető | Kör | 14×14, közép (8; 8) |
| 20 | Nincs erőforrás | NINCS MEG | Nincs képkocka | NINCS MEG |
| 24 | Nincs erőforrás | NINCS MEG | Kör | 22×22, közép (12; 12) |
| 32 | Kör | 4/8 bpp: 32×31, közép (16; 15,5); 32 bpp: 30×30, közép (16; 16) | Kör | 30×30, közép (16; 16) |
| 40 | Nincs erőforrás | NINCS MEG | Nincs képkocka | NINCS MEG |
| 48 | Kör | 4/8 bpp: 45×45, közép (23,5; 23,5); 32 bpp: 44×44, közép (23; 23) | Kör | 44×44, közép (24; 24) |
| 64 | Nincs erőforrás | NINCS MEG | Kör | 60×60, közép (32; 32) |
| 128 | Nincs erőforrás | NINCS MEG | Kör | 120×120, közép (64; 64) |
| 256 | Kör | 226×226, közép (124; 126) | Kör | 243×243, közép (127,5; 127,5) |

Az eredeti 16 px-es kép nem a nagy ikon lekicsinyített változata: fedett,
négyzetes hátterű rajz. A nagyobb eredeti képkockák kör alakúak. A PicasaPy
16 px-es képe kerek, de az alfa 255 befoglaló mérete 14×14 px. A 48 px-es
32 bites színmélységű változatban a teljesen fedett körméret 44×44 px mindkét projektben.
Az eredeti kis színmélységű 48 px-es képkockán ez 45×45 px.

| Picasa csoport | Méret és színmélység | RT_ICON azonosítók |
|---|---|---|
| 105 | 16 px, 4/8/32 bpp | 15, 18, 22 |
| 105 | 32 px, 4/8/32 bpp | 14, 17, 21 |
| 105 | 48 px, 4/8/32 bpp | 13, 16, 20 |
| 105 | 256 px, 32 bpp PNG | 19 |
| 320 | 16 px, 4/8/32 bpp | 35, 38, 42 |
| 320 | 32 px, 4/8/32 bpp | 34, 37, 41 |
| 320 | 48 px, 4/8/32 bpp | 33, 36, 40 |
| 320 | 256 px, 32 bpp DIB | 39 |

A PicasaPy `icon.ico` mind a hét képkockája 32 bites színmélységű PNG; a fájl SHA-256-a
`6956385812c944f767148deb5436a33bef78f5bef8e8f37d25c1329e6a39bac5`. A
`src/picasapy/app/assets/icon.png` bitre azonos a 256 px-es ICO-képkockával
(SHA-256: `29d5bd8bf7029b61abfcc838411dc97efc4aa6caeb0a242bd957cc88430dbd70`).
A `src/picasapy/app/assets/logo.svg` 1271×371-es szólogó, külön, körlap nélküli bal oldali jellel;
ezért a teljes SVG-re nincs egyetlen, a táblával összevethető körátmérő.
Az ikon-jel alpha >= 250 befoglaló téglalapja 4× raszterezésből mérve
362,5×370,5 SVG-egység, középpontja (181,25; 185,25); ez a jel befoglaló
közepe, nem körközéppont.

## A Windows dokumentált méretválasztása

| Felület | A Microsoft által dokumentált méret | Következmény az ikonforrásra |
|---|---|---|
| Értesítési terület | A rendszer kis ikonmérete: 16×16 px 96 DPI-n, 24×24 px 144 DPI-n, 32×32 px 192 DPI-n | 96 DPI-n a Picasa 16 px-es, négyzetes főikonja illeszkedik a kéréshez. A PicasaPy 16 px-es kerek képkockáját használhatja. |
| Tálcaablak kis ikon nézete | `SM_CXSMICON`: 16×16 px 96 DPI-n; DPI-vel nő | Az ikon kis osztályikonja használatos. A Microsoft leírása nem rögzíti minden Windows-verzió és tálcabeállítás tényleges nézetét. |
| Tálcaablak nagy ikon nézete | `SM_CXICON`: 32×32 px 96 DPI-n, 48×48 px 144 DPI-n, 64×64 px 192 DPI-n | A nagy osztályikon használatos. Az ICO-erőforrás választása a kért mérettől és színmélységtől függ. |
| Asztal nagy ikonnézet | `SHIL_EXTRALARGE`: 48×48 px 96 DPI-n, 72×72 px 144 DPI-n, 96×96 px 192 DPI-n | 96 DPI-n a Picasa 48 px-es, kerek képkockáját kérheti a rendszer. Az asztali nézet és a DPI módosíthatja a kérést. |
| Explorer extra nagy ikonnézet | `SHIL_JUMBO`: rögzített 256×256 fizikai px | A 256 px-es erőforrás választható. Ez nem az asztal alapértelmezett nézetére vonatkozó állítás. |
| Feladatkezelő | NINCS MEG: a vizsgált Microsoft ikon-dokumentáció nem adja meg a kért méretet vagy ikonválasztási útját | A felhasználói megfigyelés, hogy ott a Picasa ikonja négyzetes, önmagában nem bizonyítja a 16 px-es erőforrás kiválasztását. Futó Windows-verzión, DPI-vel és Feladatkezelő-nézettel végzett rögzítés szükséges. |

A Windows ikonerőforrásból a kért mérethez legközelebbi, azt meg nem haladó
képet választja, az azonos méretű változatok közül pedig a kijelző
színmélységéhez illőt. Emiatt a felület megnevezése önmagában nem elég a
kiválasztott RT_ICON azonosításához: a kért méret és színmélység is számít.
PicasaPy Windowsos alkalmazásánál a forráskód a PNG-képkockákat Qt `QIcon`
objektumba tölti. A Microsoft natív erőforrás-választási leírása önmagában
nem bizonyítja, hogy a Qt az adott futásban melyik képkockát adja a tálcának.
A helyi bekötés: `application_platform.py` Windowson az ICO-t választja,
és a hét PNG-képkockát adja a `QIcon`-nak; `application_startup_prepare.py`
beállítja ezt ablakikonként. A Windows csomagoló és a telepítő parancsikonja
is ugyanezt az ICO-t hivatkozza.
Források: [About Icons](https://learn.microsoft.com/en-us/windows/win32/menurc/about-icons),
[LookupIconIdFromDirectoryEx](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-lookupiconidfromdirectoryex),
[About Window Classes, Class Icons](https://learn.microsoft.com/en-us/windows/win32/winmsg/about-window-classes).

## Bizonyítottság és nyitott kérdés

A fő ikoncsoportok leltára és az alak szerinti besorolás két független úton
egyezik: `pefile`-os erőforrás-bejárás, valamint külön nyers PE-erőforrás
olvasó és `llvm-readobj` leltár. A teljesen fedett pixel-befoglalók közvetlen
rasztermérések; az összehasonlíthatóságukhoz megadott alfa-szabály nem
matematikai körillesztés. A 105-ös és 320-as csoport azonos alakját a két
dekódolt képkészlet összevetése is megerősíti.

Nyitott: a Feladatkezelő aktuális Windows-verzión, DPI-n és nézetben kért
ikonmérete, valamint az ahhoz rendelt RT_ICON-képkocka. Ezt a helyi
Linux-mérés és az áttekintett Microsoft Win32 dokumentáció nem dönti el.

## A PicasaPy ikonrajzának előállítása (#6514)

A közös színes jel a `src/picasapy/app/assets/logo.svg` fájl
`picasapy-icon-mark` csoportja. A logó ezt a csoportot közvetlenül használja,
az `scripts/generate_app_icon.py` pedig ugyanebből a csoportból rajzolja újra
az ikonokat. Az eredeti Picasa képei és útvonalai nem részei a forrásnak.

A színes jel átmérője az eredeti képkockákon (telített képpontok befoglalója):
16 px-en 14, 32 px-en 29, 48 px-en 42, 256 px-en 210 px. A PicasaPy ikonja
ugyanezeket a méreteket veszi át: a fehér körlap átmérője és középpontja a
fenti alfa-befoglaló adatokat követi (32: 30, 48: 44, 256: 226 px), a színes
jel pedig akkora, mint az eredetiben. A 24, 64 és 128 px-es képkockák a
256 px-es méreteket `méret / 256` arányban követik.

A 16 px-es változat világos (`#f9f9f9`), teljesen fedett, négyzetes csempe,
mint az eredeti, rajta a 14 px-es színes jel. A SVG-kör sugara a kívánt
átmérő felénél 1 px-lel nagyobb, mert a raszterezés szélső élsimított
pixelei nem teljesen fedettek; így a `alpha == 255` befoglaló a célméretet adja.
Mind a hét ICO-képkocka ugyanabból a közös SVG-jelből készül; az `icon.png`
képpontjai a 256 px-es ICO-képkockával azonosak.
