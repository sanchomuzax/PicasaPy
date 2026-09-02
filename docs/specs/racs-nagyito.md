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

## 6. Nyitott kérdések mérlege

`0 nyílt · 6 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| nálunk megvan-e (51.3) | **LEZÁRVA** — megvan, csak a gomb hiányzik (0.) |
| mekkora a `loupe_sm` (#1911) | **LEZÁRVA** — 51 × 51, a 103-as vászon belső rétege (4.) |
| a mutató alakja jelzi-e (#1911) | **LEZÁRVA, NEGATÍV** — nincs nagyító-mutató (2.) |
| követi-e az egeret (51.3) | **LEZÁRVA** — a kurzor közepére ül (3.3) |
| azonnal jelenik-e meg | **LEZÁRVA** — áttűnéssel, 0,4 / 1,2 (3.1–3.2) |
| a lencse alakja és mérete | **LEZÁRVA** — kör, 103 × 103, belső 65 (4.) |
| **a nagyítás MÉRTÉKE** | **BLOKKOLT** — nincs a bejárt kódban. Amit végignéztem: `0x0077be10` (a kezelő, teljes diszasszemblátum), `0x0077b4b0` (konstruktor, 0x3d8 bájtos objektum), `0x0077b6e0`, `0x0077b780`, `0x0077b860`, `0x0077b8e0`, `0x0077ba60` — egyikben sem áll nagyítási arány. **Megszerzés:** a rajzoló ág, `0x0077bb10` (a `80.0` és a `2276,5556` konstansokkal) célzott dekompilációja. |

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
