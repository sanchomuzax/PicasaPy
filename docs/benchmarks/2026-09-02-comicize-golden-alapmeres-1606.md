# Comicize: a golden referencia megjött — alapmérés a három csúszkán (#1606)

*Mérőkészlet: `research/comicize-sweep/` (a tulajdonos exportja a windowsos
Picasa 3-ból, 2026-09-02). Forráskép: 1600 × 1200.*

## 1. A készlet ÉRVÉNYES — belső ellenőrzéssel

A három almappa a Comicize három csúszkáját söpri végig (0/25/50/75/100),
a másik kettőt fixen tartva:

| mappa | `filters=Comicize=` |
|---|---|
| `effekt5_kepregeny_blurxy` | `1,<0…100>,50,50` |
| `effekt5_kepregeny_dotcontrast` | `1,20,<0…100>,50` |
| `effekt5_kepregeny_dotfade` | `1,20,50,<0…100>` |

⚠️ **Az exportok nem a kért `comicize-sweep\export` mappába kerültek**,
hanem a Picasa mindhárom forrásmappán BELÜL csinált egy saját `export`
almappát. Mind a 15 kép megvan — a kiadott útmutató volt pontatlan.

**Érvényesség-ellenőrzés (nem feltevés).** A `dotcontrast/050` és a
`dotfade/050` UGYANAZT a paraméterhármast hordozza (`20,50,50`), két külön
mappából exportálva. A két kimenet **képpontra azonos** (max eltérés
**0**), csak a JPEG-metaadatuk különbözik. ⇒ a Picasa rajza
**determinisztikus**, és a készlet mindhárom mappában ugyanúgy készült.

## 2. Az alapmérés — a mai `apply_comicize` vs. az eredeti

| tengely | érték | Δátlag | Δmax | eltérő képpont (>12) | mi átl. | eredeti átl. |
|---|---:|---:|---:|---:|---:|---:|
| blurxy | 0 | 4,90 | 62 | 20,8% | 127,5 | 127,5 |
| blurxy | 25 | 7,61 | 64 | 57,8% | 127,5 | 123,8 |
| blurxy | 50 | 7,61 | 62 | 57,8% | 127,5 | 123,8 |
| blurxy | 75 | 7,69 | 63 | 58,5% | 127,5 | 123,7 |
| blurxy | 100 | 7,68 | 63 | 58,4% | 127,5 | 123,8 |
| dotcontrast | 0 | 5,96 | 63 | 51,3% | 130,3 | 125,1 |
| dotcontrast | 50 | 7,48 | 64 | 56,4% | 127,5 | 124,0 |
| dotcontrast | 100 | 10,62 | 62 | 65,4% | 120,6 | 123,4 |
| dotfade | 0 | 10,92 | 110 | 58,0% | 124,6 | 122,0 |
| dotfade | 50 | 7,48 | 64 | 56,4% | 127,5 | 124,0 |
| dotfade | 100 | 4,50 | 27 | 42,4% | 130,4 | 127,0 |

## 3. A DÖNTŐ mérés: mennyit MOZDUL a kimenet a csúszkán?

A Δ-táblánál sokkal beszédesebb, hogy egy csúszka 0-ról 100-ra állítva
mennyit változtat a saját kimenetén:

| tengely | az EREDETI elmozdulása (Δátlag) | a MIÉNK | ítélet |
|---|---:|---:|---|
| **BlurXY** | **5,51** | **0,04** | ⛔ **gyakorlatilag NEM HAT** |
| **DotContrast** | **2,52** | **9,70** | ⛔ **~4× túl erős** |
| DotFade | 5,50 | 5,89 | ✅ közel helyes (+7%) |

### 3.1 A BlurXY néma — és tudjuk, MIÉRT

A csúszka végigmozgatása **0,04 szürkeszintet** mozdít a kimeneten. Ez a
**néma vezérlő** hibaosztálya (#1798): a paraméter él, a kód olvassa, a
felhasználó mégsem lát különbséget.

A mechanizmus a mai csővezetékből következik: az elő-elmosás
(`sigma = 1 + 20·BlurXY/100`, legfeljebb ~21) után **pixelesítés** jön a
csempeméretre — ami ennél a képnél `round(1600/70)+1 = 24` képpont. Egy
24 × 24-es blokk ÁTLAGÁT egy szimmetrikus elmosás alig változtatja meg,
tehát a blur hatása a pixelesítésben elvész.

⇒ Az elmosásnak **máshol** kell hatnia a láncban (vagy a sorrend rossz).
Ez a #1606 négy leletéből az elsőnek a mérhető megerősítése.

### 3.2 A DotContrast túlszabályoz

A mi küszöbgörbénk felső kontrollpontja `90 + DotContrast·1,5`, ami
0→100-on 90-ről 240-re visz. Az eredeti ugyanezen a szakaszon **2,52**
szürkeszintet mozdul, a miénk **9,70**-et. A képlet iránya jó (nagyobb
kontraszt → sötétebb átlag), a **meredeksége** nem.

## 4. Amit ez a lap NEM állít

- **Nem** ad javított képletet: ehhez a raszter szerkezetét kell a
  referenciához illeszteni (csempeméret, maszk-alak, keverés), nem elég a
  globális átlagot hangolni. Egy átlagra illesztett konstans a
  „szabad paraméter elnyeli a hibát" csapdája lenne.
- **Nem** méri a fekete ragyogást és a két küszöbgörbét külön — azok a
  #1606 másik két lelete, és a szétválasztásukhoz a raszter-ág izolált
  összevetése kell.
- A mérés **egyetlen forrásképen** készült. A készlet ezt adja; több
  motívumra a #684 golden-mappája való.

## 5. KÍSÉRLET: a négy eltérés NEM javítható egyenként (negatív eredmény)

A `filterdesc.xml` Comicize-blokkja teljes egészében elolvasva
(`research/copy_Picasa_3_7/Picasa3/runtime/filterdesc.xml:772`), és a
jegy négy lelete szó szerint visszaigazolódott:

| lelet | a leíróban |
|---|---|
| szorzás, nem sötétítés | `_opColorSpots` `BlendMode="multiply"`, `BlendAlpha="{0.5-_sldrDotFade.value/200}"` |
| fekete ragyogás | `GlowImageOperation color="0" innerglow="true" strength="1.1"`, sugár `35·0,02·max(W,H)/2` |
| küszöbgörbe 1 | `MasterCurve = [{0,0},{24,24},{48,48},{90+DotContrast·1,5, 254},{255,255}]` |
| küszöbgörbe 2 | ágankénti `[{0,0},{150,0},{160,255},{255,255}]`, majd `GetVar(pixelated) BlendMode="add"` |

**Két javítást kipróbáltam, és MÉRTEM az eredményt.** Egyik sem ment ki:

| változat | DotContrast elmozdulás (cél: 2,52) | DotFade (cél: 5,50) | Δátlag (50-es pont) |
|---|---:|---:|---:|
| mai kód | 9,70 | 5,89 | 7,48 |
| + ötpontos görbe | 7,05 | 7,39 | 7,69 |
| + görbe és szorzás | 7,70 | 8,38 | — |

⇒ **Az ötpontos görbe közelebb viszi a DotContrastot (9,70 → 7,05), de
elrontja a DotFade-et (5,89 → 7,39), és a képpont-eltérés is ROMLIK.**
A szorzás önmagában tovább ront.

### Miért — és mit jelent ez a megvalósító körnek

A szorzás a leíró szerint helyes, **de csak a hiányzó `add` lépéssel
együtt**: az eredeti mindkét ágban VISSZAADJA a pixelesített SZÍNES képet
(`GetVarImageOperation … BlendMode="add"`), ami jelentősen világosítja a
rasztert. A mi raszterünk enélkül sötétebb, ezért a szorzás túl erős.

⇒ **A négy eltérés CSATOLT. Egyenként javítva mindegyik ront.** A
megvalósítás csak úgy mehet, hogy a teljes ág-szerkezet (két görbe +
`add` + belső ragyogás) egyszerre áll össze, és a mérce a fenti tábla.

*A kísérleti kód nem ment ki — ez a szakasz azért van itt, hogy a
következő kör ne fusson bele ugyanebbe.*
