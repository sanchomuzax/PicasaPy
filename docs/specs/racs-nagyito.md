# A rács-nagyító (`thumbui/loupehit`, `loupe`)

**Mi ez:** a Picasa 3 könyvtárnézetében egy **nagyító**, amit a bélyegkép-rács
fölött **nyomva húzva** a képek nagyítva jelennek meg. Bekapcsolója az alsó
sávban, a nagyítás-csúszka mellett ül.

**A lap a MŰKÖDÉST írja le**, a geometria a végén áll. Kiváltó: a #1911
(„a rács-nagyító visszakapcsolása") két nyitott kérdése, és a
[`picasa-menu-parancsok-viselkedes.md`](picasa-menu-parancsok-viselkedes.md)
51.3 blokkolt tétele.

## 0. ⚠️ HELYESBÍTÉS — a „nálunk nincs" állítás elavult

A `picasa-menu-parancsok-viselkedes.md` 51.3 (2026-09-01) így szólt:
*„Nálunk mérve: nincs."*

**Ez a mai kódon már nem igaz.** Mérve a `eb42628d` main-en:

| réteg | hol | állapot |
|---|---|---|
| a nagyító rajza és húzás-kezelése | `LightboxFeed.qml:787–878` (`feedLoupeArea`, `feedLoupe`, `feedLoupeImage`) | **megvan** |
| a bekapcsolt állapot | `Main.qml:88` — `property bool loupeActive` | **megvan** |
| a **bekapcsoló gomb** | — | **hiányzik** (kikerült a v0.8.198-ban) |

**Az 51.3 a kimondása napján IGAZ volt** — a sorrend a git-naplóból:

| dátum | commit | mi történt |
|---|---|---|
| 2026-08-31 | `50c61fdd` (#1809) | az 51.3 megírása: *„Nálunk mérve: nincs"* |
| 2026-09-01 | `3070080c` (#1892) | a #1808 **megépíti** a rács-nagyítót |
| 2026-09-01 | v0.8.198 | a #1911 **kiveszi a bekapcsoló gombot** |

Tehát nem téves mérés, hanem **elavult** állítás: a funkció azóta
elkészült, csak **elérhetetlen** — a hiányzó darab a KAPCSOLÓ, nem a
nagyító.

## 1. MI AKTIVÁLJA

Egyetlen belépési pont, mérve: **`thumbui/loupehit`**, egy `vbutton` az alsó
vezérlősáv `scale_group`-jában (a nagyítás-csúszka mellett).

| | |
|---|---|
| elem | `layer:thumbui/vbutton: loupehit` — **25 × 19** |
| ikon | `layer:thumbui/loupe` — **23 × 16** (fénykép + nagyító + egérmutató piktogram) |
| kötés | `thumbui.tre:286–288` — `loupehit: thumbui/scale_group`, `m_offsetLT`; az ikon a gomb gyereke |
| buboréksúgó | *„Click and drag over photos to magnify them"* |

**A `.tre` semmilyen `Property`-t nem ad a gombra** — se `setpressed`, se
`mousedown`, se `showtarget`. A be-/kikapcsolt állapotot tehát **kód**
kezeli, nem a felületleíró.

**Egy kikommentezett sor** ugyanott:

```
#SharedHandler thumbui/tip hottip thumbui/output_label
```

⇒ a gombhoz **tartozott volna** egy „hottip", ami a súgót az alsó sáv
`output_label` sorába (502 × 13) írta volna. Ebben a kiadásban **ki van
kapcsolva**.

## 2. ⛔ NINCS külön egérmutató — mért NEGATÍV eredmény

A #1911 felveti, hogy a bekapcsolt állapotot az **egérmutató alakja**
jelezhetné. **Az eredetiben nem az jelzi.** Két, egymástól független
lekérdezés mondja ugyanezt:

1. a `respack.yt` teljes rétegkészletében **egyetlen** mutató-erőforrás van:
   `layer:thumbui/veccursor: circlecursor` (158 × 98) — a **retusáló** köre;
2. a bináris mutató-szókincse — `normalcursor`, `textcursor`, `scalecursor`,
   `rotatecursor`, `deletecursor`, `veccursor`, `textawarecursor`,
   `actascursor`, `thumbui/circlecursor` — **nem tartalmaz nagyító-mutatót**.

⇒ Ha nálunk mutató-váltás lesz a visszajelzés, az **tudatos eltérés**, nem
az eredeti átvétele.

## 3. MIT CSINÁL — a nagyító MEGJELENÉSE ÁTMENETES

A kezelő `0x0077be10` (1582 b) és négy testvérfüggvénye adja a viselkedést.
Mind capstone-nal olvasva (a gépi `objdump` itt ARM-célú, i386-ot nem tud).

### 3.1 Az áttűnés — két külön időállandó

`0x0077b6e0`: a láthatóság **animált**, és a be- és kikapcsolás **nem
szimmetrikus**:

```
0x0077b6e3  cmp byte ptr [edi+0x370], cl      ; már ebben az állapotban? → kilép
0x0077b6f6  mov byte ptr [edi+0x370], cl      ; az új állapot
0x0077b738  call 0x9a5210                     ; „most" (dupla pontosságú óra)
0x0077b748  je   0x77b765                     ; ha az új állapot 0 …
0x0077b74a  fld  qword ptr [0xcf3ae8]         ;   … BEKAPCSOLÁS:  + 0.4
0x0077b765  fld  qword ptr [0xcf4318]         ;   … KIKAPCSOLÁS:  + 1.2
0x0077b75b  call 0x9e6010                     ; animátor indítása
```

| | konstans | cím |
|---|---:|---|
| megjelenés | **0,4** | `0xcf3ae8` |
| eltűnés | **1,2** | `0xcf4318` |

⚠️ **Az EGYSÉG nincs mérve.** A két érték az `0x9a5210` órájának
egységében értendő; hogy ez másodperc-e, ebből a függvényből nem derül ki.
**Ami mérve van: az arány — az eltűnés PONTOSAN háromszor hosszabb, mint a
megjelenés.**

### 3.2 Amit az animátor hajt: az ÁTLÁTSZATLANSÁG

`0x0077b8e0` (a képkockánkénti lépés):

```
0x0077b8fb  call 0x9a5210        ; most
0x0077b90c  call 0x9e5e70        ; az animátor értéke
0x0077b936…0x77b966              ; VÁGÁS a [0 ; 1] tartományra
0x0077b981  fmul qword [0xcf39d8] ; × 256.0
0x0077b98f  fistp …               ; egészre
0x0077b99b  mov eax, 1            ; ha 0 lenne → 1
0x0077b9a2  cmp eax, 0x100 / 0x100; felső vágás 256
0x0077b9c0  mov [ecx+0x248], eax  ; a csomópont átlátszatlansága
```

⇒ **a nagyító nem ugrik be, hanem beúszik**: az átlátszatlanság
`0 → 256` skálán, **1 és 256 közé vágva**.

### 3.3 A nagyító a kurzor KÖZEPÉRE ül

`0x0077b780`: a kapott téglalap két egész mezőjét (`+8`, `+0xc`) **0,5-tel**
szorozza (`0xc72150`), és a csomópont `+0x144` / `+0x148` mezőibe írja;
ha valamelyik változott, beállítja a `[+8] |= 1` piszkos-bitet.

## 4. A NAGYÍTÓ RAJZA — két koncentrikus üveggyűrű

Nem téglalap, hanem **üveglencse**: átlátszó közép, körben áttetsző gyűrű
fénykiemeléssel.

| réteg | méret | belső ÁTLÁTSZÓ átmérő | teljesen fedő képpont |
|---|---:|---:|---:|
| `loupe/docbounds` (a vászon) | **103 × 103** | — | — |
| `loupe/loupe` | **103 × 103** | **65** | **0** (végig áttetsző) |
| `loupe/loupe_sm` | **51 × 51**, a vászon (26, 26) pontján | **32** | 5 |

*(Mérés: a réteg alfa-csatornája a középvonal mentén; a nagy gyűrű
alfa-csúcsa 219, a képpontok 4993/10609-e részlegesen fedő, 0 teljesen
fedő.)*

**A `loupe_sm` NEM alternatív méret, hanem a `loupe` dokumentum belső
rétege** — pontosan középen (`(103 − 51) / 2 = 26`). A kezelő külön
referenciát tart rá: a `"loupe"` sztringre (`0x00cb3fe4`) négy hivatkozás
van a függvényben (dokumentum-betöltés), a `"loupe/loupe_sm"`-re
(`0x00cb3fec`) **pontosan egy**, közvetlenül az objektum létrehozása után
(`0x0077bfc6`) — vagyis a belső gyűrűt külön kezeli.

## 5. Eredeti / nálunk / teendő

A „nálunk" oszlop **mérés** (`eb42628d`).

| | eredeti (mért) | nálunk (mért) | teendő |
|---|---|---|---|
| bekapcsoló | `loupehit` **25 × 19** az alsó sávban, a nagyítás-csúszka mellett | **nincs gomb** | #1911 |
| a lencse alakja | **kör**, áttetsző üveggyűrű, átlátszó középpel | **téglalap**, `Theme.contentPanel` kitöltés, 1 px keret, `radius: 3` (`LightboxFeed.qml:855–861`) | kör |
| a lencse mérete | **fix 103 × 103** (belső 65) | `cellWidth × 2,5` — a rács cellájához kötött (`:843–844`) | fix méret |
| a lencse helye | a kurzor **közepén** (`0x0077b780`: `w/2`, `h/2`) | a kurzor **fölött** (`kurzorY − magasság − 8`, `:851`) | középre |
| megjelenés | **áttűnés**, 0,4 be / 1,2 ki, alfa 1…256 | azonnali `visible` váltás (`:842`) | áttűnés |
| egérmutató | **nem változik** (2. szakasz) | nem változik | — (egyezik) |
| nagyítás mértéke | **NINCS MÉRVE** | **2,5** — a forrás kimondja, hogy SAJÁT DÖNTÉS (`:799–805`) | marad, amíg nincs mérés |

## 5/b ✅ A NAGYÍTÁS MÉRTÉKE — LEZÁRVA: nincs nagyítási arány, a lencse 1:1-ben mutat (2026-09-05)

> **Bizonyítottsági fok: megerősített.** A célrajz mérete és az 1:1 arány
> **a kód szerkezetéből** következik (a célterület szélessége azonos a kép
> szélességével), nem illesztésből. Ghidra nem kellett.

A 6. mérleg ezt a tételt „célzott dekompilációra vár" indoklással tartotta
blokkolva. **A rajzoló ág (`FUN_0077bb10`, 758 b) elolvasva megvan.**

### 5/b.1 Miért nem találta öt függvény: NINCS nagyítási arány

A korábbi kör hét függvényt nézett végig arányt keresve. Nincs, mert a
Picasa **nem méretez**: a lencse a **teljes méretű képet natív
képpontmérettel** rajzolja ki, csak **eltolva**, hogy a kurzor alatti
képpont a rajzterület közepére essen.

### 5/b.2 A rajzterület: **161 × 161**

```
0x0077c445  mov edx, 0xa1        ; 161
0x0077c44b  mov ecx, edx         ; 161
0x0077c44d  call 0x009a9c90      ; (161, 161)
```

⇒ A `FUN_0077c440` **161 × 161**-es célrajzot készít. A `loupe/docbounds`
103 × 103-as üveglencséje (4. szakasz) ennek a felületnek a **látható
kivágása**.

### 5/b.3 Az eltolás képlete — utasításról utasításra

`FUN_0077bb10`, `0x0077bc0f`–`0x0077bcad`. Bemenet: a bélyegkép
képernyő-téglalapja (`esi`: bal/felső/jobb/alsó), a kurzor pontja
(`[esp+0xb4]`, két `float`), és a **teljes kép** mérete
(`[obj+0x388]` = W, `[obj+0x38c]` = H, **előjel nélkül** olvasva — a
negatív ágon `fadd 4294967296.0`, `0x0077bc52` és `0x0077bca7`).

```
eltolásX = kerekít( (kurzorX − tgl.bal)  / (tgl.jobb − tgl.bal) × W ) − 80
eltolásY = kerekít( (kurzorY − tgl.felső)/ (tgl.alsó − tgl.felső) × H ) − 80
```

*(A `80.0` a `0x00cf4c30`-ból, `fld qword`; a **teljes binárisban egyetlen
hivatkozása** van, `0x0077bc5c` — tehát a nagyító saját konstansa. Mindkét
tengelyen ugyanaz a példány: az X-ág `fsub st(1),st(0)`-ja után az érték a
veremben marad, és az Y-ág `fsubrp`-je használja el.)*

⭐ **A 80 pontosan a 161 × 161 közepe** (0…160 ⇒ közép = 80). A kurzor
alatti képpont tehát **a rajzterület közepére** kerül.

### 5/b.4 A célterület: bizonyíték az 1:1-re

```
0x0077bcd1  [obj+0x1c] = −eltolásY
0x0077bcd8  [obj+0x18] = −eltolásX
0x0077bcf5… a célterület felépítése:
    bal   = −eltolásX
    felső = −eltolásY
    jobb  = W − eltolásX
    alsó  = H − eltolásY
```

⇒ **A célterület szélessége `(W − eltolásX) − (−eltolásX) = W`, magassága
`H`** — pontosan a kép saját mérete. **Nincs skálázás; az arány 1:1.**
Ez nem illesztés, hanem a kifejezés algebrai következménye.

### 5/b.5 Amit ez KIMOND

- **Nincs „nagyítási arány" konstans** az eredetiben — ezért nem találta
  meg a korábbi kör.
- A lencse a **teljes méretű kép** 161 × 161 képpontos ablakát mutatja,
  natív felbontásban, a kurzor alatti képpontra középezve.
- A **látszólagos** nagyítás tehát nem rögzített szám:
  `eredeti képpontméret ÷ a bélyegkép képernyőmérete` — vagyis annál
  nagyobb, minél kisebbre van állítva a rács. Ez éppen a funkció célja
  (élesség/csukott szem eldöntése).

### 5/b.6 Két konstans, ami NEM a nagyítás — kizárva

| konstans | hol | mi valójában |
|---|---|---|
| `2276,5556640625` | `0x00d35808`, `fld` a `0x0077bbac`-on | **megosztott globális**: a `.text`-ben **15** hivatkozása van (`0x568e4a`…`0xc2e2d3`), mind **olvasás**, író egy sincs; itt `fistp qword`-del **64 bites egésszé** alakul ⇒ idő/ütem jellegű, nem nagyítás |
| `0,5` | `0x00c72150`, `0x0077c489` | a kép **közepét** számolja (`W × 0,5`, `H × 0,5`) — a #1951 már így hivatkozza |

### 5/b.7 MIT AD MA — nálunk (mérve)

`src/picasapy/app/qml/PicasaPy/LightboxFeed.qml`:

| | eredeti (mért) | nálunk (mért) |
|---|---|---|
| mit mutat a lencse | a **teljes méretű kép** 161 × 161-es kivágata, **1:1** | a **bélyegkép EGÉSZÉT** (`source: elem.thumbUrl`, :963–:968), `PreserveAspectCrop`, 65 × 65-ös területen |
| nagyítás | nincs arány (1:1 natív képpont) | `readonly property real nagyitas: 2.5` (:846) — **saját döntés**, és **sehol nincs felhasználva** (a projekt egészében 1 előfordulás) |
| `sourceSize` | — | `Math.round(loupe.width)` = 103 (:961–:962) |

⛔ **Ebből következik: a mi nagyítónk NEM nagyít, hanem kicsinyít** — az
egész bélyegképet zsugorítja a lencsébe. Az élesség eldöntésére, amire a
funkció való, így alkalmatlan. A `nagyitas` **néma beállítás**
(`picasa-menu-parancsok-viselkedes.md` 48. tétel osztálya). Jegy: **#2399**.

## 6. Nyitott kérdések mérlege

`0 nyílt · 7 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| nálunk megvan-e (51.3) | **LEZÁRVA** — megvan, csak a gomb hiányzik (0.) |
| mekkora a `loupe_sm` (#1911) | **LEZÁRVA** — 51 × 51, a 103-as vászon belső rétege (4.) |
| a mutató alakja jelzi-e (#1911) | **LEZÁRVA, NEGATÍV** — nincs nagyító-mutató (2.) |
| követi-e az egeret (51.3) | **LEZÁRVA** — a kurzor közepére ül (3.3) |
| azonnal jelenik-e meg | **LEZÁRVA** — áttűnéssel, 0,4 / 1,2 (3.1–3.2) |
| a lencse alakja és mérete | **LEZÁRVA** — kör, 103 × 103, belső 65 (4.) |
| **a nagyítás MÉRTÉKE** | ✅ **LEZÁRVA (2026-09-05)** — **nincs nagyítási arány**: a lencse a teljes méretű képet **1:1**-ben rajzolja egy **161 × 161**-es felületre (`0x0077c445`), a kurzor alatti képpontot a **közepére** (a `80.0` a `0x00cf4c30`-ból, egyetlen hivatkozással) eltolva. A célterület szélessége algebrailag `W`, magassága `H` ⇒ skálázás nincs. Ezért nem találta öt függvény: nincs mit találni. 5/b |

## 7. Amit KIZÁRTAM

- **„a nagyító külön egérmutatót kap"** — nincs ilyen erőforrás, és a
  bináris mutató-szókincsében sincs (két független lekérdezés).
- **„a `loupe_sm` a kisebbik választható lencse"** — nem: a nagy lencse
  **belső** rétege, ugyanabban a dokumentumban.
- **„a nagyító téglalap"** — kör.
- **„nálunk nincs rács-nagyító"** (51.3) — **elavult**: a réteg megvan, a
  kapcsoló hiányzik.

*Bizonyítottsági fok: **megerősített** a geometriára, a rajzra, az
átlátszatlanság-animációra és a két időállandóra (utasításszinten
olvasva); **erős** a „nincs saját egérmutató" negatív eredményre (két
lekérdezés-alak); a nagyítás mértéke **NINCS MÉRVE**.*

---

Jegyek: **#1911** (a gomb visszakapcsolása) · **#460** (nagyító, pásztázó
navigátor, diavetítés-vezérlők) · **#1808** (az eredeti megépítés, lezárva).
