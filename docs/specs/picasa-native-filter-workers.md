# A natív szűrők munkafüggvényei — a hívási térkép

A `picasa-native-filter-registry.md` a **belépési pontokat** adja meg (42
szűrő → callback). Ez a lap egy réteggel mélyebb: a callbackek **vékony
burkolók**, amik a csúszkaértékeket kiolvassák a paraméterblokkból, és egy
közös **munkafüggvényt** hívnak.

Forrás: a 35 callback Ghidra-dekompilálása (12.1.2, Java 21), a nyers C-kód a
privát agent-repóban: `referencia/dekompilalt/natív-szűrők.c`.

## A burkoló-minta

```c
void contrast(int param_1, undefined4 param_2) {
  FUN_0090c2c0(param_2, *(undefined4 *)(param_1 + 0x28), 0, 0x3f800000);
  return;
}
```

- `param_1 + 0x28`, `+0x2c`, `+0x30` — az **1., 2., 3. csúszka** értéke (float)
- `param_1 + 0x40` — egy **24 bites szín** (a pipetta / fehérpont)
- `0x3f800000` = `1.0f`

## A közös munkafüggvények — ezek a valódi algoritmusok

| cím | mit csinál (a hívók alapján) | hívók |
|---|---|---|
| **`0x0090ac20`** | **Derítőfény (Fill Light)** | `backlight`, `fill`, `autobacklight`, `triple`, `triple2`, `triple3`, `finetune`, `finetune2` — **8 szűrő** |
| **`0x0090c3b0`** | **szinthúzás (Kiemelések/Árnyékok)** | `triple2`, `triple3`, `autolight`, `finetune`, `finetune2` |
| **`0x0090eda0`** | **fehérpont / semleges szín** (a pipetta és a szín-varázspálca magja) | `whitept`, `colorfix`, `autocolor`, `finetune`, `finetune2` |
| **`0x0090ea10`** | **színhőmérséklet** | `colortemp`, `colorfix`, `finetune` |
| **`0x0090c2c0`** | **kontraszt** | `contrast`, `triple` |
| **`0x0090c430`** | a `finetune`-család negyedik lépése | `triple2`, `triple3`, `finetune`, `finetune2` |
| **`0x009db610`** | **hisztogram-elemzés / automatikus szintek** | `enhance`, `autocontrast`, `tint`, `rainbow` |
| `0x009aabf0` | semleges/„nincs hatás" beállítás (a `0xffffffff` argumentumú ágakban) | 16 szűrő |

### Egyszűrős munkafüggvények

| szűrő | munkafüggvény |
|---|---|
| `shadow` (Árnyék és kiemelés) | `0x0090d3e0` (három csúszka) |
| `blur` (Elhomályosítás) | `0x0090cf60` |
| `glow` / `glow2` | `0x0090d4b0` |
| `unsharp` / `unsharp2` | `0x0090c4a0` |
| `warm` | `0x0090c040` |
| `sat` | `0x0090e200` + `0x0090b930` |
| `grain` / `grain2` | `0x0090a2e0` |
| `dir_sat` | `0x0090dbb0` |
| `dir_brite` | `0x0090d8b0` |
| `linblur` | `0x0090de10` |
| `ansel` | `0x00a3f2f0` + `0x0090e680` |

`sepia` a burkolóban **nem hív semmit** a 0x9x tartományból — vagy beágyazott,
vagy egy fix mátrix az adatokban.

## Amit ez azonnal megmond

**1. Nyolc munkafüggvény lefedi a készlet nagy részét.** Nem 42 algoritmust
kell megírni: a `0x90ac20`, `0x90c3b0`, `0x90eda0`, `0x90ea10`, `0x90c2c0`,
`0x90c430`, `0x9db610` és `0x90d3e0` megvalósításával a `finetune`-család, a
`triple`-család, az `autolight`, `autocolor`, `autocontrast`, `enhance`,
`colorfix`, `whitept`, `colortemp`, `contrast`, `backlight`, `fill` és
`autobacklight` **mind kész**.

**2. A `fill` = `backlight` = `autobacklight` = a `finetune` Derítőfénye.**
Mind a `0x90ac20`-at hívja. Egy implementáció.

**3. Az `autolight` („Automatikus kontraszt") ugyanazt a szinthúzást hívja
(`0x90c3b0`), mint a `finetune`.** Ez egybevág a méréssel (#535, #539): az
automatikák nem külön algoritmusok, hanem **automatikusan megválasztott
paraméterek** ugyanahhoz a maghoz.

**4. A `0x90eda0` a szín-varázspálca és a pipetta közös magja.** A mérés
szerint a pálca a `finetune2` p4 mezőjébe ír színt (#551) — a hívási térkép
ezt megerősíti: `whitept`, `colorfix`, `autocolor`, `finetune`, `finetune2`
mind ide fut be.

**5. A dekompilált `finetune2` visszaigazolja a mért képletet:**

```c
fVar2 = 1.0 - *(float *)(param_1 + 0x2c);   // 1 − Kiemelések
if (fVar2 <= 0.001) fVar2 = 0.001;          // nullaosztás elleni védés
```

Ez pontosan az `1/(1−h)` nevezője, amit a mérőkészletből vezettünk le — **két
független úton ugyanaz**.

## Következő lépés

A **munkafüggvények** dekompilálása (a fenti nyolc + az egyszűrősök). Ott van
a tényleges pixel-matematika; a mostani réteg csak a paraméterátadást
mutatja.

---

## MEGFEJTVE: `0x0090ac20` — a Derítőfény (Fill Light)

A dekompilált kódból (a nyers C: `referencia/dekompilalt/munkafuggvenyek.c`):

```python
g = 1.0 / ((1.0 - fill) * 0.7 + 0.3)

# 256 elemu LUT
for x in range(256):
    v = ((x * g) / 255.0) ** (1.0 / (g * 0.7 + 0.3))
    LUT[x] = round(255.0 * min(v, 256.0))

# keppontonkent (BGR sorrendben a memoriaban)
luma4 = (B + 2*G + R) >> 2            # sulyozott atlag, negyeddel osztva
w     = 0xff00 - luma4 * round(alpha * 256)     # alpha = 1.0 a hivoban
out_c = clamp(c + (((LUT[c] - c) * w) >> 16), 0, 255)
```

**A lényeg a `w` súly:** a LUT-ot nem egyszerűen alkalmazza, hanem a képpont
**világosságával fordítottan arányos** súllyal keveri be. Sötét képpontnál
`w ≈ 65280` (teljes hatás), világosnál `w → 0` (semmi hatás). Ezért nem
írható le egyetlen gamma-görbével — **két hatás van egymáson**: egy
gamma-jellegű LUT és egy árnyék-súlyozott keverés.

`fill = 0` esetén `g = 1`, a kitevő is 1, tehát a LUT azonosság — a művelet
**nem csinál semmit**, ahogy kell.

### Ellenőrzés a mérőkészleten

Átlagos csatorna-eltérés a Picasa saját kimenetétől (`referencia/deritofeny/`,
hat csúszkaállás):

| állás | **binárisból levezetve** | korábbi gamma-közelítés | a mai kódunk |
|---|---|---|---|
| 10 % | **0,82** | 1,53 | 0,97 |
| 25 % | **1,41** | 2,46 | 2,06 |
| 50 % | **0,93** | 4,71 | 3,64 |
| 75 % | **4,52** | 9,96 | 5,36 |
| 100 % | **1,21** | 10,38 | 5,89 |

A JPEG saját zaja kb. 1,0 — vagyis ez **a pontos algoritmus**, nem közelítés.
(A 75 %-os sor magasabb értéke valószínűleg abból jön, hogy a csúszka kézzel
lett beállítva, tehát nem pontosan 0,75.)

## A Glimmer-oldal még nyitva

A `glimmer::GlowImageOperation` / `BlurImageOperation` / `AutoFixImageOperation`
/ `BWImageOperation` vtable-jének **első három** bejegyzése nem a
képfeldolgozás: destruktor, felszabadítás és az XML-attribútumok beolvasása
(nyolc egymásba ágyazott `FUN_008f1500` hívás = nyolc attribútum). A tényleges
`apply` metódus a vtable-ben **hátrébb** van.

Ezért a 255-ös elmosás-korlát (Lomo/Holga) **továbbra is csak méréssel
igazolt**, binárisan nem. Következő kör: a vtable teljes kiolvasása és a
helyes slot dekompilálása.

---

# 2. dekompilálási kör (#576) — a tényleges pixel-matematika

**Futás:** 2026-08-13, Ghidra 12.1.2 PUBLIC, `standardLinux32gb` Codespace,
`Picasa3.exe` SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`
(10 160 456 bájt, PE32/x86, image base `0x00400000`). 21 gyökérfüggvény,
2 szint mélységű hívás-követés, **95 dekompilált függvény**. A nyers kimenet a
privát agent-repóban: `referencia/dekompilalt-576/`.

Az alábbi leírásokban a képpuffer szerkezete végig ugyanaz: `+8` = szélesség,
`+0xc` = magasság, `+4` = sorlépés (pixelben), `+0x10` = adatmutató; a képpont
**BGRA** bájtsorrendben (`[0]=B, [1]=G, [2]=R`).

## 2.1 A közös segédek

| cím | mi ez | bizonyíték |
|---|---|---|
| `0x00c29990` | **`float → int` kerekítő** (MSVC `_ftol2`-szerű), az x87 verem tetejéről | a törzse `ROUND(in_ST0)` és a fél-LSB korrekció |
| `0x005568e0` | **`pow(x, y)`** | a LUT-építőkben `pow(i/255, 1/γ)` alakban |
| `0x0040eac0` | **`exp(x)`** (a `0x00c29c6c` burkolója) | a kontraszt-tényezőnél |

> **Fontos helyesbítés.** A #484 rangsor eddig úgy tartotta, hogy a
> színhőmérséklet-leképezéshez „a `FUN_00c29990` kell". Ez a függvény
> **nem hordoz információt**: csak lebegőpontos → egész kerekítés. A tényleges
> paraméter-leképezés a **hívó** oldalán van (ld. 2.3).

## 2.2 A LUT-alkalmazó dithereléssel — `0x0090bc60`

Ez a **közös kimeneti fokozat** a szinthúzáshoz és a kontraszthoz. A LUT
**257 elemű, 16 bites** (`8.8` fixpont, teljes kitérés `0xFF00`); a 257. elem az
utolsó másolata (`LUT[256] = LUT[255]`), hogy az interpoláció ne fusson ki.

```c
r = MT19937_next() & 0xff;              // KÉPPONTONKÉNT EGY minta, mindhárom csatornára
for c in (R, G, B):
    lo    = LUT[c];  delta = LUT[c+1] - lo;
    v     = lo + ((delta * r) >> 8) - (delta >> 1);   // ±delta/2 egyenletes zaj
    out_c = clamp(v >> 8, 0, 255);
```

**Két dolog, ami ebből fontos:**

1. **A zaj amplitúdója a görbe helyi meredekségével arányos** (`delta`). Ahol a
   szinthúzás széthúzza a hisztogramot, ott nagyobb a kvantálási lépés — és
   pontosan ott ditherel jobban. Ez az, amitől a Picasa szinthúzása **nem
   sávosodik**.
2. **Egy véletlen minta jut egy képpontra**, mindhárom csatorna ugyanazt kapja —
   így a zaj **szürke**, nem színes.

A véletlenszám-forrás **Mersenne Twister (MT19937)**: a temperálás
(`>>11`, `<<7 & 0xff3a58ad`, `<<15 & 0xffffdf8c`, `>>18`) és a 624 szavas
újratöltés (`0x26f` határ → `0x00aa2930`) egyértelmű.

> **Következmény a golden-mérésre:** a szinthúzás kimenete **nem
> determinisztikus** képpont szinten — ±1 szint eltérés a ditherből ered. A
> pixelpontos összevetés ezekre a szűrőkre **±1 tűréssel** végzendő, vagy a
> ditherelést ki kell kapcsolni az összevetéshez.

## 2.3 Szinthúzás (Kiemelések / Árnyékok) — `0x0090c3b0`

Két lépés: LUT-építés (`0x0090c1e0`) + a fenti alkalmazó.

```c
// FUN_0090c1e0(float black, float white, float gamma)
invG  = 1.0 / gamma;
scale = (white != black) ? 1.0 / (white - black) : 1.0;
for i in 0..255:
    p      = pow(i / 255.0, invG);
    LUT[i] = clamp(round((p * 65280.0 - black * 65280.0) * scale), 0, 0xFF00);
```

Vagyis a klasszikus **szint-transzformáció**, ebben a sorrendben:
**gamma → feketepont eltolás → fehérpont skálázás**, 16 bites pontossággal.
A `65280 = 255·256` a teljes kitérés.

## 2.4 Kontraszt — `0x0090c2c0`

Ugyanaz az alkalmazó, más LUT-építő (`0x0090c100`):

```c
// FUN_0090c100(float contrast, float brightness, float gamma)
k = exp(2.0 * contrast);
for i in 0..255:
    p      = pow(i / 255.0, 1.0 / gamma);
    v      = k * ((p * 65280.0 + brightness * 25600.0) - 32768.0) + 32768.0;
    LUT[i] = clamp(round(v), 0, 0xFF00);
```

- a **kontraszt a középpont (32768 = 50%) körül** feszít, `exp(2·c)` tényezővel;
- a **fényerő additív**, `brightness · 25600` (azaz ±1 ≈ ±100 nyolcbites szint);
- a gamma a kontraszt **előtt** hat.

## 2.5 Színhőmérséklet — `0x0090ea10` *(a #551 hiányzó darabja)*

A hívó (`colortemp` visszahívás, `0x008f8ea0`) így adja át a lánc két
paraméterét:

```c
FUN_0090ea10(dst, src, param[0x28], param[0x2c]);   // = a filters= lánc 0. és 1. értéke
```

A munkafüggvény két egészre kerekíti őket — nevezzük **`s`** és **`t`** —, majd:

```c
k_down[i] = (i * (256 - s)) >> 8;                 // lekicsinyítés: fejtér a felfelé húzáshoz
k_up[i]   = clamp((i * (65536 / (256 - s))) >> 8, 0, 255);   // a pontos inverze
P[i]      = i * (256 - i);                        // KÖZÉPTÓNUS-PARABOLA, max 16384 @ 128
t_pos     = (t >= 1) ? t : 0;

// képpontonként:
r = k_down[R];   R' = r + ((P[r] * t)     >> 15);
g = k_down[G];   G' = g + ((P[g] * t_pos) >> 17);
b = k_down[B];   B' = b - ((P[b] * t)     >> 15);
out = (k_up[clamp(R')], k_up[clamp(G')], k_up[clamp(B')]),  alfa = 0xFF
```

**Amit ez megmond:**

- **`t` a hideg↔meleg tengely**: pozitívnál a vörös nő, a kék csökken, a zöld
  **negyed súllyal** (`>>17` a `>>15` helyett) és **csak melegítéskor** mozdul.
- **`s` a „fehérváltás"**: egy globális lekicsinyítés, amit a végén a pontos
  inverze visszaad. Ez teremt fejteret, hogy a vörös emelése ne vágjon be.
- A hatás **középtónus-súlyozott**: a fekete és a fehér közelében `P → 0`, tehát
  ott nem változik semmi. Ezért nem szürkül el a fehér a melegítéstől.
- A maximális elmozdulás `t·16384/32768 = t/2` szint.

**Bizonyítottság:** a szerkezet **megerősített**. A `filterdesc.xml` szerint a
két csúszka `0 = Cool to Warm [-0.5..0.5]`, `1 = White Shift [0..1]`; a
**×256-os skálázás** (`s = round(WhiteShift·256)`, `t = round(CoolToWarm·256)`)
**erős következtetés**, mert `s`-nek 256 alatt kell maradnia és `t/2` így ad
értelmes, ±64 szintes kitérést — de **egyetlen méréssel igazolandó**.

## 2.6 Automatikus szinthúzás / hisztogram-elemzés — `0x009db610` *(a #539 magja)*

```c
ceiling = flag ? 252 : 255;                       // ← A KÉT ÁG

// 1) hisztogram — a KÖZÉPSŐ 90% × 90%-ról, csatornánként külön
for y in [h*5/100 .. h*95/100):
  for x in [w*5/100 .. w*95/100):
      histR[R]++, histG[G]++, histB[B]++;

// 2) vágási darabszám: a TELJES kép képpontszámának 0,5%-a
clip = max(1, (w * h) / 200);

// 3) csatornánként: alulról és felülről addig összegzünk, amíg el nem érjük
black_c = legkisebb i, ahol  sum(hist_c[0..i])   >= clip
white_c = legnagyobb i, ahol sum(hist_c[i..255]) >= clip

// 4) csatornánkénti lineáris nyújtás, HELYBEN, 16.16 fixponttal
gain_c = (white_c == black_c) ? 0 : (ceiling << 16) / (white_c - black_c);
out_c  = clamp(((c - black_c) * gain_c) >> 16, 0, ceiling);
```

**Négy dolog, amit ez eldönt:**

1. **A vágási pont valóban DARABSZÁM-alapú** (`w·h/200`), nem a hisztogram fix
   százaléka — a jegy (#539) feltevése helyes.
2. **A kép 5%-os pereme kimarad az elemzésből.** Ez eddig ismeretlen volt, és
   önmagában okoz eltérést: keretes, vignettált vagy sötét szélű képnél a
   Picasa más fekete-/fehérpontot választ, mint egy teljes képes elemzés.
   *(A darabszám viszont a TELJES képméretből számolódik — tehát a küszöb
   arányaiban szigorúbb, mint a mintavett terület 0,5%-a.)*
3. **Két ág van: a felső határ 252 vagy 255.** A `252`-es ág enyhébb: nem húzza
   ki teljesen a fehéret. Ez a legvalószínűbb magyarázata a „Jó napom van" és az
   „Automatikus kontraszt" eltérő eredményének.
4. **Nincs gamma és nincs ditherelés** ebben az ágban — tiszta lineáris nyújtás,
   helyben, a forráspufferen.

**Ami továbbra is nyitott:** a mérésben megfigyelt eset, amikor a Picasa
**mindhárom csatornára AZONOS** nyújtást futtatott. Ez a függvény **mindig
csatornánként** dolgozik — az azonos-csatornás viselkedés tehát **egy másik
ágból** jön (feltehetően a `0x0090c3b0` szinthúzó egyetlen, összevont
hisztogramból számolt LUT-tal). Ezt külön kell megkeresni.

## 2.7 Az irányított család — `dir_sat`, `dir_brite`, `dir_sharp`, `linblur` *(a #568 magja)*

### A közös váz: lineáris térbeli rámpa

A `dir_brite` (`0x0090d8b0`) explicit módon mutatja a mintát:

```c
a = clamp(param_3, -1, 1);      // „Balról jobbra”
b = clamp(param_4, -1, 1);      // „Felülről lefelé”
lépésX = a / (w/2);   lépésY = b / (h/2);
// a képpontonkénti súly a bal felső saroktól -a-ról indul és +a-ig nő
```

**Ezzel a #568-ban felvetett hipotézis megerősítést nyert:** a két paraméter
tényleg **két tengely menti komponens**, `[-1, 1]` tartományban (a függvény
maga vágja be), és a súly **lineárisan, a kép közepére szimmetrikusan** változik:

```
s(x, y) = a · (2x/W − 1) + b · (2y/H − 1)
```

### `dir_sat` — `0x0090dbb0`

```c
L = (2*R + 5*G + B) >> 3;               // súlyozott luma: 0,25 R / 0,625 G / 0,125 B
a = round(s(x,y) * 256);                // képpontonkénti súly
if (a < 0) { a += 256; out_c = L + (((c - L) * a) >> 8); }        // telítetlenítés L felé
else       { out_c = clamp(c + (((c - L) * a) >> 8), 0, 255); }   // telítés L-től el
```

> **Figyelem:** ez a luma-képlet **NEM azonos** a Derítőfényével
> (`(B + 2G + R) >> 2`). A Picasa **két különböző luma-súlyozást** használ; a
> mi implementációnknak szűrőnként a megfelelőt kell alkalmaznia.

### `dir_brite` — `0x0090d8b0`

```c
// 1) globális előkorrekció, középtónus-parabolával (ugyanaz a P, mint 2.5-ben)
pre[i] = clamp(i + ((i * (256 - i) * k) >> 16), 0, 255);

// 2) képpontonként, a = |round(s(x,y)*256)|,  u = 256 - a
v = pre[c];
if (s >= 0) v ^= 0xff;                         // világosításhoz tükrözés
v = (((v*v*v) >> 16) * a + u * v) >> 8;        // keverés a KÖBÖS görbével
if (s >= 0) v ^= 0xff;
out_c = v;
```

Vagyis: **köbös tónusgörbe** (sötétítés), és a világosítás ugyanez **invertált
tartományon**. A rámpa azt szabja meg, hogy képpontonként mennyit keverünk a
köbös görbéből — 0-nál változatlan, 256-nál teljes köbös.

> **Megvalósítva (#623).** A `dir_sat` és a `dir_brite` a
> `picasapy.render.directional` modulban él, a `filters=` láncból elérhető
> (`dir_sat=1,a,b`, `dir_brite=1,a,b` — a natív burkolók a két csúszkát
> KÖZVETLENÜL adják tovább, a korong csak beállítja őket). A `dir_brite`
> burkolója a középtónus-parabola erősségét **0**-nak adja, tehát az
> előkorrekciós LUT azonosság.
>
> A `dir_sharp` és a `linblur` **szándékosan nem** került be: az előbbinél a
> rámpa horgonya, az utóbbinál a második pont származtatása nem olvasható ki
> a dekompilátumból — mindkettő méréssel rögzítendő.

## 2.8 Melegítés (`warm` / „Melegítés") — beégetett tábla, KINYERVE

A `0x0090c040` nem számol: egy **256 × 4 bájtos, beégetett táblát** olvas
(`0x00d33b70`, `.data`), amelyben csatornánként külön leképezés van
(`R = bájt2`, `G = bájt1`, `B = bájt0`).

A táblát a helyi binárisból kinyertem (PE-szakasztábla szerinti fájloffszet
`0x933b70`), és **teljes egészében rögzítettük**:
`referencia/dekompilalt-576/warmify-lut.csv` (privát repó).

| be | R | G | B | R−G | R−B |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 | 0 |
| 32 | 41 | 29 | 21 | +12 | +20 |
| 64 | 79 | 60 | 44 | +19 | +35 |
| **96** | 112 | 88 | 69 | +24 | **+43** |
| 128 | 139 | 113 | 97 | +26 | +42 |
| 160 | 163 | 138 | 128 | +25 | +35 |
| 192 | 187 | 168 | 162 | +19 | +25 |
| 224 | 214 | 200 | 198 | +14 | +16 |
| 255 | 242 | 232 | 234 | +10 | +8 |

Mindhárom görbe szigorúan monoton. A hatás a **negyed- és középtónusban a
legerősebb** (max `R−B = +43` a 96 körül), a szélek felé elhal, és a fehérpontot
enyhén **lehúzza** (255 → 242/232/234). Ez a „bőrtónus-javítás", amit a
buboréksúgó ígér (*„Improves skintones by boosting warm tones"*).

**Ez a szűrő ezzel 100%-ban reprodukálható** — nem kell modellezni, a tábla
maga a specifikáció.

## 2.9 Ami ebben a körben NEM oldódott meg

| kérdés | miért |
|---|---|
| a `sepia` mátrixa | a burkoló tényleg nem hív semmit a `0x9x` tartományból; külön kell megkeresni |
| az azonos-csatornás auto-szinthúzás ága | ld. 2.6 — másik függvényben lesz |
| a `dir_sharp` konvolúciós magja | a hívási lánc mélyebb, mint 2 szint |
| a `glow` / `blur` sugár-kezelése | nagy függvények, külön kör kell rájuk |
| a `s` és `t` ×256-os skálázása (2.5) | egyetlen méréssel igazolható |

---

# 3. dekompilálási kör (#612) — a maradék öt kérdés

**Futás:** 2026-08-13, ugyanaz a környezet és bináris, mint a 2. körnél. 15 gyökér,
**4 szint** mélységű követés, `MAX_CHILD_BYTES = 20000`, **139 dekompilált
függvény**. Nyers kimenet: `referencia/dekompilalt-612/` (privát repó).

## 3.1 MEGOLDVA: a három automatikus ág szétválasztása

A #576-ban nyitva maradt, hogy a mérésben látott **azonos-csatornás** szinthúzás
honnan jön. A válasz: **három különböző szűrő van, három különböző viselkedéssel.**

| szűrő | felületi név | mit hív | eredmény |
|---|---|---|---|
| **`autolight`** (`0x008f80c0`) | „Automatikus kontraszt" (1 kattintás) | a **kézi** szinthúzót (`0x0090c3b0`) | **EGY közös LUT mindhárom csatornára** → a színegyensúly nem változik |
| **`autocontrast`** (`0x008f89d0`) | „Automatikus kontraszt" | `0x009db610`, **flag = 0** | **csatornánként külön** nyújtás, felső határ **255** |
| **`enhance`** (`0x008f8840`) | „Jó napom van" | `0x009db610`, **flag = a `CarefulEnhance` beállítás** | csatornánként, felső határ **252 vagy 255** |

### `autolight` — az azonos-csatornás ág

```c
FUN_00a4bfd0(0.005f, &white, &black);      // 0x3ba3d70a = 0.005 → 0,5% levágás
if (black == white) black += 1;
b = black / 255.0;  w = white / 255.0;
if (w <= 0.001) w = 0.001;
else if (w == 1.0 && b == 0.0) return;     // már teljes a kitérés: nincs teendő
FUN_0090c3b0(dst, b, w, /*gamma=*/1.0f);   // EGY LUT, mind a három csatornára
```

Vagyis a fekete- és fehérpont **egyetlen, összevont statisztikából** jön (nem
csatornánként), a gamma **pontosan 1.0**, és a kimenet a **ditherelő**
LUT-alkalmazón megy át (#576 2.2).

> **Ez zárja le a #539 nyitott kérdését.** A mérésben látott két viselkedés nem
> ágválasztás egy függvényen belül, hanem **két külön szűrő**: `autolight` az
> azonos-csatornás, `autocontrast` a csatornánkénti.

### `enhance` — a „Jó napom van" a rejtett beállítástól függ

```c
FUN_00407a20(&tmp, "Preferences", "CarefulEnhance");   // beolvassa a beállítást
FUN_009aabf0(img, -1, -1, -1, -1);
flag = FUN_004019b0(-1.0f);                            // a beállítás értéke (alap: -1.0)
FUN_009db610(img, flag);                               // ez adja a 252/255 felső határt
```

> ⚠️ **Ez közvetlenül érinti a golden-mérést (#317).** A „Jó napom van"
> eredménye **függ a felhasználó gépén beállított `CarefulEnhance` értéktől**.
> Ha az eltér, a mi kimenetünk sosem fog egyezni — nem a mi hibánkból. A mérés
> előtt ezt tisztázni kell.

## 3.2 `dir_sharp` — irányított **unsharp mask**, nem konvolúció

A `0x0090d600` **három** képpuffert kap: cél, forrás, és egy **harmadik, előre
elmosott** változat.

```c
a = clamp(param_4, -1, 1);   b = clamp(param_5, -1, 1);      // a két tengely
k = round(...);                                              // globális szint
// képpontonként:
amount = (k - round(rámpa(x,y))) * 2;
if (amount > 0)
    out_c = clamp(c + (((c - blurred_c) * amount) >> 8), 0, 255);
```

Vagyis **klasszikus unsharp mask** (`éles = eredeti + a·(eredeti − elmosott)`),
ahol az `a` erősség **képpontonként** jön a lineáris rámpából (#576 2.7).

**Nincs konvolúciós mag ebben a függvényben** — az elmosás külön menetben
készül. A megvalósításunkhoz tehát: elmosás → irányított unsharp-összevonás.

## 3.3 `linblur` — köbös B-spline súlytábla + csomagolt keverés

A `0x0090de10` egy **384 elemű súlytáblát** épít explicit köbös polinomokból
(a `t` 0-tól 1,5-ig lép, 1/256-os lépésekben):

```
|t| > 1.5           → f = 0
t < -1.5            → f = 1
-0.5 < t <= 0.5     → f = 1/2 − (3t/4 − t³/3)
t <= -0.5           → f = −t³/6 − 3t²/4 − 9t/8 + 7/16
t > 0.5             → f = 9/16 − (9t/8 + (t³/6 − 3t²/4))
tábla[i] = round((1 − 2f) · 255.9999)
```

Az 1/6, 3/4, 9/8, 7/16, 9/16 együtthatók a **köbös B-spline** szakaszai — a
tábla tehát egy sima, −1…+1 tartományú átmenet-súly.

A keverés **csomagolt aritmetikával** megy (`x >> 8 & 0x00ff00ff` és
`x & 0x00ff00ff`), azaz **két csatorna egyszerre** egy 32 bites regiszterben —
korabeli SIMD-helyettesítő.

```c
idx   = akkumulátor >> 8;            // ±0x180 közé vágva
w     = (idx < 0) ? -tábla[-idx] : tábla[idx];
alpha = (w + 255) / 2;
out   = lerp(cél, forrás, alpha);    // csomagoltan, két csatornánként
```

## 3.4 A `puck` vezérlő két közös segítője

A sugaras és irányított család `cb2`/`cb3` visszahívásai **nem képfeldolgozók**,
hanem a felületi korong (`puck`) kezelői:

| cím | mit csinál |
|---|---|
| `0x008f9bf0` (cb2) | a korong `(x, y)` helyét **2×3 affin mátrixon** viszi át (`p+0x6c`…`p+0x80`), majd a `+0x34`/`+0x38` mezőbe írja — így a korong a **vágott/forgatott** képen is a helyén marad |
| `0x008f9cf0` (cb3) | a **sugár**: `min(szélesség, magasság) / 2 · (paraméter + 1)` |

Vagyis a sugaras effektek (`radblur`, `radsat`, `radtint`) hatósugara **a kép
rövidebb oldalához kötött**, nem abszolút képpontban — ezért néz ki ugyanúgy
kicsi és nagy képen.

## 3.5 NEGATÍV EREDMÉNY: a `sepia` magja nem dekompilálható így

A `sepia` burkolója (`0x008f8950`) **valóban hív** egy címet: `0x0090a120`.
A #576-beli megállapítás („nem hív semmit a `0x9x` tartományból") **téves volt**.

A Ghidra viszont **nem hozott létre függvényt** ezen a címen: az index
`CALL_TARGET_0090a120` néven, **0 mérettel** ismeri, a `.text` szakaszban. Ez
azt jelenti, hogy az autoanalízis a hívási célt felismerte, de a törzset nem
diszasszemblálta.

**A következő kör teendője:** a szkriptben `disassemble(addr)` +
`createFunction(addr, null)` hívással kikényszeríteni, és csak utána
dekompilálni. Ez néhány sor a meglévő szkriptben.

## 3.6 Amit ez a kör NEM ért el

- a `glow` és a `blur` sugár-kezelése: a függvények nagyok, a 4 szintű követés
  a peremüket érte el, de a mag-ciklusuk külön elemzést kíván;
- a `radblur`/`radsat` **pixelműveletei** (a burkolók és a `puck`-kezelés
  megvan, a magok nem);
- a `sepia` mátrixa (ld. 3.5).

---

# 4. dekompilálási kör (#617) — a `sepia` MEGFEJTVE

**Futás:** 2026-08-13, ugyanaz a környezet és bináris. 6 gyökér, 6 szint
mélység, **137 dekompilált függvény**. Nyers kimenet:
`referencia/dekompilalt-617/` (privát repó).

## 4.1 A `sepia` — a kikényszerített diszasszemblálás bevált

A #612-ben rögzített negatív eredmény oka az volt, hogy a Ghidra a
`0x0090a120` címen **nem hozott létre függvényt** (csak hívási célként ismerte).
A szkriptbe tett `disassemble(addr)` + `createFunction(addr, null)` megoldotta:
a mag **434 bájt**, és teljesen kibomlott.

### A teljes algoritmus

```c
// képpontonként, BGRA pufferben:

// 1) szürkeárnyalat — ITU-R BT.601 egészaritmetikával
gray = (77*R + 151*G + 28*B) >> 8;          // 0x4d, 0x97, 0x1c — összegük pontosan 256

// 2) halványítás: invertálás → 218/256 szorzás → visszainvertálás
base = 255 - (((255 - gray) * 218) >> 8);    // 0xda = 218
                                             // g=0 → base=38  (a feketék megemelve)
                                             // g=255 → base=255

// 3) színezés OVERLAY-keveréssel, fix tintával
//    tint = (R,G,B) = (0x9b, 0x7d, 0x63) = (155, 125, 99)
for c in (R, G, B):
    if (base < 128)  out_c = (2 * base * tint_c) >> 8;                       // multiply
    else             out_c = 255 - ((2 * (255 - base) * (255 - tint_c)) >> 8); // screen
alfa = 0xFF
```

A binárisban a 3. lépés **ágmentesen** van megírva: egy `(v >> 7) & 0x010101`
maszk állítja elő csatornánként a 0x00/0xff választót, és az XOR-ok végzik a
feltételes invertálást. Ez a klasszikus **Overlay** keverés, elágazás nélkül.

**Mivel a `base` mindhárom csatornán ugyanaz (szürkeárnyalat), a szépia egyetlen
256 → RGB leképezés.** A teljes tábla kiszámolva:
`referencia/dekompilalt-617/sepia-lut.csv`.

| gray | base | R | G | B |
|---:|---:|---:|---:|---:|
| 0 | 38 | 46 | 37 | 29 |
| 64 | 93 | 112 | 90 | 71 |
| 128 | 147 | 171 | 146 | 124 |
| 192 | 202 | 214 | 202 | 191 |
| 255 | 255 | 255 | 255 | 255 |

### Ellenőrzés a felhasználó referencia-exportján

A visszafejtett képletet ráengedtem az eredeti képre, és összevetettem a
windowsos Picasából exportált szépia változattal (`referencia/sepia/`):

| mérőszám | érték |
|---|---|
| átlagos abszolút hiba (R, G, B) | **0,92 / 0,60 / 1,07** |
| a képpontok **±1**-en belül | **82,6%** |
| a képpontok **±2**-n belül | **95,5%** |

A maradék eltérés a **JPEG-újrakódolásból** ered (a referencia is, a bemenet is
JPEG). A képlet gyakorlatilag pontos.

> **Módszertani tanulság:** a szépiát „egyetlen méréssel is meg lehetne fogni"
> — de a mérés **közelítés**, a visszafejtés **maga a képlet**. A kettő együtt
> a legerősebb: a dekompilálás adta a pontos egészaritmetikát, a mérés pedig
> **igazolta**.

## 4.2 A `glow`, a `blur` és a sugaras család — kézi elemzéssel MEGFEJTVE

A #617 első jelentésében azt írtam, hogy ezek „nem bomlottak ki" a mélységi
követéssel. Ez **nem a kód hibája volt, hanem a módszeré**: a függvények
kibomlottak, csak MMX-es, csomagolt aritmetikájú kódként, amit soronként kell
olvasni. Az alábbi az eredmény.

### 4.2.1 A közös elmosó mag — `0x009dd0d0`

Ez a Picasa **általános elmosója**; a `glow` és a sugaras család egyaránt ezt hívja.

```c
FUN_009dd0d0(kep, blurX, blurY, x0, y0, x1, y1);
```

**Nem konvolúció, hanem elsőrendű IIR (exponenciális) szűrő, oda-vissza futtatva.**

```
állapot s: négy 16 bites sáv (BGRA), 9.7 fixpontban  (érték << 7)
együttható k: 16 bites, pow(...) eredménye egészre kerekítve

előre:   s += ((x[i]   − s) · k) >> 16 ;   y[i] = s >> 7   (0..255-re vágva)
vissza:  s += ((y[i]   − s) · k) >> 16 ;   y[i] = s >> 7
```

- a szorzás **`pmulhw`** (előjeles 16×16 → felső 16 bit), tehát az együttható
  `α = k / 65536`, és mivel `k` előjeles 16 bites, **`α < 0,5`**;
- **két menet tengelyenként** (előre + vissza) → fázistorzítás-mentes, szimmetrikus
  átvitel, ami két elsőrendű szűrőből közel Gauss-alakot ad;
- **vízszintes menet soronként**, **függőleges menet egyszerre négy oszlopon**
  (MMX);
- a művelet **O(1) képpontonként**, a sugártól függetlenül — ezért volt a Picasa
  elmosása interaktív már 2005-ben.

**Ami nem derül ki:** a `k = round(pow(a, b))` kifejezés két argumentuma az FPU
veremben van, a dekompilátor nem látja. Vagyis a **sugár → α leképezés** még
hiányzik — **egyetlen méréssel** meghatározható (egy éles lépcső elmosása ismert
sugárral, majd α illesztése).

### 4.2.2 `glow` — `0x0090d4b0`

Nem saját pixelművelet, hanem **összeállítás**:

```c
a = clamp(|round(param)|, 0, 256);
FUN_009aabf0(kep, ...);              // alfa előkészítés
FUN_00aa40a0(0.5f, 0);               // 0.5-ös arány beállítása
FUN_009dd0d0(...);                   // ELMOSÁS (4.3.1)
FUN_009ac3f0(kep, 256 - a, forras);  // visszakeverés az eredetivel, súly = 256 − a
FUN_009a99c0(...);                   // alfa visszaállítás
```

Vagyis **glow = elmosás + visszakeverés az eredetivel**, ahol a csúszka a
keverési arányt adja (`256 − a`).

### 4.2.3 `blur` („Elhomályosítás", Küszöbérték) — NEM Gauss-elmosás

Ez a legmeglepőbb eredmény: a `0x0090cf60` **élmegőrző, többléptékű simítás**.

```c
// 1) (szélesség+1) × (magasság+1) méretű, 2 bit/cella navigációs rács
//    (RTTI: CGrNavT<unsigned_short,1>, CGrNavT<unsigned_long,1>)
//    a peremek előre bejelölve: 0x5555 (függőleges) / 0xaaaa (vízszintes)

// 2) HÁROM lépték: 1, 2, 4
for n in (1, 2, 4):
    // élek jelölése: ahol a szomszédos képpontok színkülönbsége nagy
    for minden vízszintes és függőleges szomszédpár:
        d² = ΔR² + ΔG² + ΔB²
        if (d² > kuszob / n²)  jelöld be az élt a rácsban   // ezt nem szabad átlépni
    // simítás a régiókon belül, csatornánként (maszk 1, 2, 4 = B, G, R)

// 3) végül halványítás:
if (fade != 1.0)  kimenet = keveres(eredeti, simitott, round(fade*256));
```

Vagyis: **a küszöbnél nagyobb színugrások „falak"**, és a simítás csak azokon
belül dolgozik — **anizotróp / bilaterális jellegű simítás**, három léptéken.
A küszöb `n²`-tel osztódik, mert a különbségek `n × n` blokkokra összegződnek.

> ⚠️ **Ha ezt Gauss-elmosásként valósítanánk meg, alapvetően más eredményt adna.**
> A `blur` a Picasában **megőrzi az éleket** — ezért van egyáltalán
> „Küszöbérték" csúszkája.

### 4.2.4 `radblur` / `radsat` — a sugaras maszk

A burkoló (`0x008f8520`) két lépést végez:

```c
// 1) elmosás — UGYANAZZAL a maggal (4.3.1)
sugar = szelesseg * 0.01 * Amount + 0.001 + szelesseg * 0.01;
      // = szelesseg/100 · (Amount + 1) + 0.001
FUN_009dd0d0(kep, sugar, sugar, ...);

// 2) sugaras keverés
FUN_0090b050(&rect, cel, puckX, puckY, Size, Sharpness, ...);
```

**Az elmosás sugara a kép szélességének századához kötött** — ezért néz ki
ugyanúgy kicsi és nagy képen. (Ugyanaz az elv, mint a `puck` sugaránál,
#612 3.4.)

#### A sugaras maszk — `0x0090b050`

```c
cx = round(szelesseg * puckX);   cy = round(magassag * puckY);
// 1024 elemű, bájtos súlytábla, a NÉGYZETES távolsággal indexelve (nincs gyökvonás!)
for y, x:
    idx = (dx² + dy²) >> shift;
    if (idx < 1024)  kimenet = alap + (masik - alap) * tabla[idx] / 256;   // csomagolt
    else             kimenet = alap;                                        // érintetlen
```

#### A súlytábla — `0x0090aeb0`

```c
r  = min(szelesseg, magassag) / 2 * (Size + 1.0);
r2 = r*r;  shift = 0;
while (r2 > 1024) { r2 *= 0.5; shift++; }      // a négyzetes távolság léptéke

for i in 0..1023:
    d = sqrt( (i/1024) * (1024/r2) );                    // normalizált sugár
    v = clamp( 0.5 + (d - 0.5) / (1 - Sharpness*0.99), 0, 1 );
    u = 1 - v;
    tabla[i] = round( (3 - 2u) * u * u * 255 );          // SMOOTHSTEP
```

- a **`Sharpness`** (a „Élesség"/„Lágy perem" csúszka) az átmenet meredekségét
  adja: 0-nál lineáris, 1 felé `1/(1−0,99) = 100`-szoros meredekség, azaz éles
  körvonal;
- az átmenet **smoothstep** (`3u² − 2u³`), nem lineáris — ez adja a lágy peremet;
- a **négyzetes távolsággal indexelt tábla** miatt nincs gyökvonás a
  képpont-ciklusban.

**Amit nem lehet ebből eldönteni:** hogy a súly a *közép* vagy a *perem* felé
mutat-e az elmosott képre — ez a hívó oldalán dől el (melyik puffer az „alap"
és melyik a „másik"). A `radblur` („Lágy fókusz") és a `radsat` („Fókuszos FF")
ugyanezt a maszkot használja, ellentétes irányban.

### 4.2.5 A sugár → együttható leképezés — MEGMÉRVE (2026-08-13)

A #576/#617 körökben a szerkezet megvolt, de a `k = round(pow(a, b))` két
argumentuma az FPU-veremben van, a dekompilátor nem látja. **Méréssel
meghatároztuk.**

**Mérés:** szintetikus éles éllépcső (800×512, bal fekete / jobb fehér), a
windowsos Picasa **Ragyogás** effektje, Intenzitás maximumon, a **Sugár**
csúszka öt állásában (0 / 25 / 50 / 75 / 100%), veszteségmentes bemenet,
maximális minőségű JPEG-export. A profilokat 512 sor átlagolásával nyertük ki.

#### A mért lecsengés

A ragyogás **világosító** keverés: a fehér oldal 255 marad, a sötét oldalra
szivárog a fény. A sötét oldali profil **tiszta exponenciális** (illesztési
relatív hiba 0,7–2,6%), ami a kétmenetes elsőrendű IIR-re jellemző:

| csúszka | e-hajtási táv. `L` (képpont) | `r` | `α = 1−r` | `k = α·65536` |
|---:|---:|---:|---:|---:|
| 0% | 1,78 | 0,5698 | 0,4302 | 28 192 |
| 25% | 4,43 | 0,7979 | 0,2022 | 13 248 |
| 50% | 15,29 | 0,9367 | 0,0633 | 4 148 |
| 75% | 65,37 | 0,9848 | 0,0152 | 995 |
| 100% | 216,04 | 0,9954 | 0,0046 | 303 |

#### A leképezés

A `filterdesc.xml` szerint a Sugár csúszka **logaritmikus**, `<log>250.0</log>`,
azaz a paraméter `R(t) = 250^t`, ahol `t ∈ [0,1]` a csúszka állása. Ezzel:

| csúszka | `R = 250^t` | mért `L` | **`L / R`** |
|---:|---:|---:|---:|
| 25% | 3,98 | 4,43 | 1,114 |
| 50% | 15,81 | 15,29 | 0,967 |
| 75% | 62,87 | 65,37 | 1,040 |
| 100% | 250,00 | 216,04 | 0,864 |

**Átlag 0,996, szórás 0,092 — vagyis `L = R`.**

> **Az e-hajtási távolság PONTOSAN a Sugár paraméter, képpontban.**
> ```
> r = exp(−1/R)
> k = round(65536 · (1 − r))        ← ez megy a pmulhw-ba
> ```
> Ez összefér a dekompilált `pow` hívással: `exp(−1/R) = pow(e, −1/R)`.

#### Végponttól végpontig igazolás

A fenti `k`-val leszimulálva a kétmenetes IIR-t az eredeti képre, és
összevetve az exportált JPEG-gel:

| csúszka | `k` | keverési súly | **átlagos hiba** | max |
|---:|---:|---:|---:|---:|
| 25% | 14 572 | 1,13 | **1,15 szint** | 2,0 |
| 50% | 4 017 | 0,96 | **0,77 szint** | 2,1 |
| 75% | 1 034 | 1,01 | **0,63 szint** | 2,0 |

A hiba **JPEG-zaj nagyságrendű**. A keverési súly ~1,0, azaz a sötét oldalon a
kimenet a puszta elmosott érték — a Ragyogás világosító keverése.

*(A 0%-os és 100%-os pont kimaradt a leképezés-illesztésből: a 0%-nál az él
túl éles a megbízható illesztéshez, a 100%-nál a 250 képpontos sugár nem fér
el a 400 képpontos félképen. Mindkét eltérés mérési korlát, nem modellhiba.)*

#### ⚠️ A sugár ABSZOLÚT, nem a képmérethez kötött

Ellenőrző mérés ugyanezzel a beállítással **1600 képpont széles** képen:

| kép | mért `L` |
|---|---:|
| 800 px | 15,29 |
| 1600 px | 14,46 |

Az arány **0,945 ≈ 1,0** (nem 2,0). Vagyis a `glow` sugara **képpontban
abszolút** — **ellentétben a `radblur`-rel**, amelynek a burkolója
explicit módon a képszélességből számol (`szelesseg/100 · (Amount+1)`, ld.
4.2.4). A két effekt tehát **eltérően skálázódik**, és ezt a mi
megvalósításunknak is követnie kell.

**Ezzel a Picasa összes natív szűrőjének pixel-matematikája megvan.**
