# Benchmark: teljes effekt-export összevetés (#1143)

Dátum: 2026-08-24 · Picasa: 3.9 · PicasaPy-export: v0.8.27
(`2026-08-20 22:31`) · Minta: 178 kép, azonos forrásokból.

Ez a dokumentum a #1143-ban közölt teljes mérés géppel ismételt,
visszakövethető változata. A NAS-on lévő exportok csak bemenetek: a szkript
nem ír beléjük.

## Ismétlés

```sh
python3 scripts/compare_effect_exports.py \
  '/mnt/nas/My Pictures/PicasaPy meroszett/export-202608151229' \
  '/mnt/nas/My Pictures/PicasaPy meroszett/export-202608202231' \
  --json /tmp/picasapy-1143-effect-export.json
```

A szkript a közös relatív útvonalú JPEG/PNG-párokat rendezetten járja be,
bájtúton olvassa a fájlokat (ékezetes Windows-útvonalon is), majd az RGB
RGB/RGBA csatornák átlagos abszolút eltérését méri (PNG-n az alfa is része a
mérésnek). A 3,0 fölötti érték eltérés;
eltérő méret mindig eltérés. Hiányzó vagy olvashatatlan bemenetnél világos,
magyar hiba keletkezik. A mérési lelet önmagában nem hibakód: az eszköz
auditra való, nem CI-kapu.

## Eredmény

| Összes közös pár | Egyezik (<= 3) | Eltér | Hiányzik |
|---:|---:|---:|---:|
| 178 | 117 | **61** | 0 |

A #1143 termék-triage-a 34 effektet sorol fel. A szigorú, méretet is
eltérésnek tekintő szkript ezen felül a `border` és `dropshadow` keretek
már korábban ismert geometriai eltérését is jelzi; ezért a gépi listában
36 effektnek van legalább egy eltérő sora. Ez nem új, elhallgatott lelet:
a #1143 táblája mindkettő méretét kimondja, csak nem sorolja a 34 javítási
jelölt közé.

### A #1143 34 javítási jelöltje

Az értékek az eltérő változatok átlagos abszolút csatornaeltérései; `méret`
helyett a két kimenet dimenziója eltér.

| Effekt | Eltérő változatok |
|---|---|
| `polaroid` | alap/min/max: **méret** |
| `dir_tint` | alap 22,294; max 124,170 |
| `finetune2` | alap 119,850; max 83,452 |
| `finetune` | alap 8,666; max 91,549 |
| `quantizepalette` | alap 36,409; min 75,814 |
| `pixelate` | alap 13,441; min 59,486 |
| `tint` | hex4 58,822; hex8 58,822 |
| `twotone` | alap 17,066; min 39,315 |
| `holga` | alap 33,161; min 34,853 |
| `sixties` | alap 23,022; min 28,716 |
| `boost` | alap 6,420; max 28,030 |
| `picnikgrain` | alap 7,143; max 27,821 |
| `focalzoom` | alap 27,441; min 9,291 |
| `lomo` | alap 27,303; min 27,359 |
| `nightvision` | alap 16,276; min 25,260 |
| `heatmap` | alap 19,819; min 19,748 |
| `comicize` | alap 9,188; max 15,682; min 5,558 |
| `ir` | alap 15,504 |
| `radtint` | alap 10,787; max 5,176; min 14,308 |
| `autobacklight` | alap 12,866 |
| `linblur` | alap/max/min 12,147 |
| `dir_brite` | alap 10,302 |
| `radblur` | min 10,293 |
| `dir_sharp` | alap 10,100 |
| `grain` | alap 7,552 |
| `cinemascope` | alap 7,221 |
| `roundededges` | max 7,112 |
| `orton` | min 7,107 |
| `pencilsketch` | alap 7,059; min 3,094 |
| `crossprocess` | alap 6,789 |
| `grain2` | alap 6,379 |
| `soften` | alap 3,601 |
| `radsat` | max 3,205 |
| `ansel` | alap 3,162 |

## Mai kód- és jegyaudit

A fenti második export **v0.8.27**, nem a mai `main`. A 2026-08-20 utáni
forrásban például a TwoTone javítása (#966), a kis-/nagybetű érzékeny
szűrőnév-felismerés (#1141), a fölös paraméterű tagok eldobása (#910), az
`ansel` súlyozásának bináris igazolása (#939), valamint a `finetune2`
hőmérséklet-mérés (#956) már megtörtént. Ezért a régi exportból nem nyitunk
vak, duplikált termékhibákat: egy mai termékhiba csak friss PicasaPy-export
és ugyanezzel a mérővel igazolható.

Az alábbi térkép minden #1143-jelöltet felelőshöz vagy kimondott, ideiglenes
"nem javítjuk a régi export alapján" döntéshez köt. A *mai újramérés kell*
jelölés nem késznek nyilvánítás: a következő export-körben ezeket kell
elsőként ellenőrizni, és csak akkor nyílik külön P2/V2 hiba, ha továbbra is
3 fölött vannak.

| Effekt | Nyitott felelős vagy dokumentált döntés |
|---|---|
| `polaroid` | **#1144 nyitott**: külön méret-hiba, a három méretet tételesen tartalmazza. |
| `finetune`, `finetune2` | **#956 nyitott**; #879 közös-LUT javítása után a mai hőmérsékletmodellt méri. |
| `grain`, `grain2` | **#907 nyitott**: a zajmag ismételt alkalmazáskor nem lehet fix; a pixelazonos elvárás sem érvényes. |
| `linblur` | **#953 nyitott**: a középponti korai kilépés felbontásparitás-függő. |
| `tint` | **#1142 nyitott** a színmező-olvasás/lánc-kezelés hibacsaládjára; #872 a hatlépéses recept javítása. A hex4/hex8 a #1142 ellenőrző anyaga. |
| `ansel` | **#939 nyitott**: a fehér kontroll nem bizonyítja a színes súlyozást; a mai bináris-kutatás ehhez kötött. |
| `twotone` | #966 lezárt, a színmátrix és a hiányzó lépés javítása a régi export UTÁN ment be; **mai újramérés kell**. |
| `dir_tint` | #940 dokumentálta a görbét; **mai újramérés kell**, mert a v0.8.27-eredmény önmagában nem igazol aktuális hibát. |
| `dir_brite`, `dir_sharp` | #623 natív család-implementáció; a `dir_sharp` egy kalibrálandó skalárt még kimond. **Mai újramérés kell.** |
| `radblur`, `radsat` | #668 a közös natív IIR-magot és sugaras maszkot mérte; **mai újramérés kell** a régi min/max-sorokra. |
| `radtint` | #565 binárisból visszafejtett modellje; a Feather-leképezés volt nyitott. **Mai újramérés kell.** |
| `autobacklight` | #567 a natív, fix derítőfényt vezette be; **mai újramérés kell.** |
| `comicize` | #569 natív féltónusos raszterre váltott; a perem-mintavétel dokumentáltan nyitott. **Mai újramérés kell.** |
| `focalzoom` | #570 natív paramétersorrend és zoomkernel; a perem/interpoláció nyitott. **Mai újramérés kell.** |
| `ir` | #566 binárisból visszafejtett zöldcsatornás csővezeték; **mai újramérés kell.** |
| `quantizepalette`, `pixelate`, `holga`, `sixties`, `boost`, `picnikgrain`, `lomo`, `nightvision`, `heatmap`, `cinemascope`, `roundededges`, `orton`, `pencilsketch`, `crossprocess`, `soften` | #381 filterdesc-alapú Glimmer-csővezeték. Ez a csomag a régi export idején még közelítő részleteket tartalmazhatott; **nem nyitunk 15 duplikátumot, mai újramérés kell effektenként.** |

Ez a döntés nem „nem javítjuk soha”: csak azt mondja ki, hogy a v0.8.27-es
összevetés ma nem elegendő új, aktuális termékhiba létrehozásához. A
felfrissített PicasaPy-export után bármely 3 fölötti sor külön, `bug` + P2
címkés, V2 mérföldköves jegyet kap.

## Polaroid ellenőrzése

A külön jegy létezik: **#1144**. A mérés mindhárom méretét megismételte:
alap `818×950` vs `1053×1185`, min/max `887×1004` vs `1138×1255`.
Ez valódi, jelenleg nyitott geometriai hiba; a másik két kereteffekt
méretjelzése nem helyettesíti és nem fedheti el.
