# A hat szín szerinti keresés — MEGFEJTVE

*Picasa 3.9.141.259, mérve 2026-08-26. Image base `0x400000`.*

> ⛔ **A legfontosabb lelet: a színkeresés NEM az átlagszínt osztályozza.**
> Egy **telítettséggel súlyozott hue-hisztogramot** épít az egész
> képrasztról, hét vödörrel, és a **legnagyobb vödör** nyer. Az
> `avgcolor` ini-kulcsnak **semmi köze** hozzá.

---

## 1. MIT AD MA a PicasaPy

| | |
|---|---|
| `src/picasapy/color/classify.py` | **az átlagszínt** sorolja be egyetlen HSV-küszöbrendszerrel |
| ugyanott, 8–15. sor | a docstring **kimondja**: *„A PONTOS Picasa-besorolási szabály … **nincs dokumentálva és nem mérhető**"* |
| a küszöbök | `_ACHROMATIC_SAT_MAX = 0.12`, `_BLACK_VAL_MAX = 0.20`, `_WHITE_VAL_MIN = 0.85`, `_PINK_HUE_LO/HI = 330/355`, hat hue-határ (`45/70/170/255/345`) — **mind saját döntés** |
| kategóriák | **10** (`red, orange, yellow, green, blue, purple, pink, black, white, gray`), egyet választ |

⇒ **A „nem mérhető" állítás MEGDŐLT.** Az algoritmus egy 752 bájtos
függvényben áll, konstansostul.

---

## 2. A névtábla — `0x00424c20` (107 b)

Index → keresőtoken, `switch`-táblával (`0x00424c8c`):

| index | token |
|---:|---|
| 0 | `color:red` |
| 1 | `color:orange` |
| 2 | `color:yellow` |
| 3 | `color:green` |
| 4 | `color:blue` |
| 5 | `color:purple` |
| 6 | `color:pink` |
| **−1** | **`color:black color:white color:gray`** — mind a **három egyszerre** |

⚠️ **Ez már önmagában eltérés nálunk:** az akromatikus kép az eredetiben
**mindhárom** akromatikus tokenre illeszkedik; mi egyet választunk
(`black` VAGY `gray` VAGY `white`) a világosság szerint. Az eredeti a
fekete/szürke/fehér között **nem tesz különbséget**.

---

## 3. Az osztályozó — `0x009dbd10` (752 b)

Bemenete egy rasztert leíró rekord: `[+0x0c]` magasság, `[+0x08]`
szélesség, `[+0x04]` sorlépés, `[+0x10]` képpontok, **4 bájt/képpont**.

### 3.1 Csatornasorrend: **BGRA** *(megerősítve)*

A három hue-ág az `[+2]`, `[+1]`, `[+0]` bájtot pontosan a szabványos
HSV-képlet R-, G- és B-ágaként használja:

| ág | képlet a kódban | szabvány | ⇒ |
|---|---|---|---|
| `[+2]` a max (`0x009dbdfc`) | `(b1 − b0)·255/Δ`, eltolás **0** | `(G−B)/Δ` | `[+2]=R`, `[+1]=G`, `[+0]=B` |
| `[+1]` a max (`0x009dbe18`) | `(b0 − b2)·255/Δ` **+ 510** | `2 + (B−R)/Δ` | ✓ |
| `[+0]` a max (`0x009dbe38`) | `(b2 − b1)·255/Δ` **+ 1020** | `4 + (R−G)/Δ` | ✓ |

*(A két eltolás mérve: `0xcf41d0` = **510.0**, `0xcf41c8` = **1020.0** —
azaz 2×255 és 4×255. Ez egyben igazolja a **1530 egységes** hue-kört.)*

Ez egybevág a [`respack`-lappal](picasa-respack-format.md): a Picasa
végig **BGRA**-ban dolgozik.

### 3.2 Képpontonként

```
MAX = max(b0,b1,b2)          MIN = min(b0,b1,b2)          Δ = MAX − MIN
ha MAX == 0            → a képpont KIMARAD
S = Δ·255 / MAX                                   (0…255)
H1530 = <a fenti ág>   ; ha < 0 → += 1530
H = H1530 / 6                                     (0…254)
ha S <= 50             → a képpont KIMARAD        (0x009dbe8e)
b = H / 10                                        (0…25)
vödör[b] += S                                     ⇐ SÚLY a telítettség, nem 1
```

**Két küszöb, mindkettő mérve:**

| | érték | jelentése |
|---|---|---|
| `MAX == 0` | fekete képpont | kimarad |
| **`S <= 50`** (`0x009dbe8e  cmp ebp, 0x32`) | **19,6 %** telítettség | kimarad |

### 3.3 A hét vödör hue-tartománya

`b = H/10`, egy `b`-egység = 10 H-egység = **14,1°** *(360/255·10)*.

| vödör | `b` értékei | H | fok | szín |
|---:|---|---|---|---|
| 0 | **0 és 24** | 0–9, 240–249 | 0–12,7° **és** 338,8–352,9° | **piros** *(átfordul)* |
| 1 | 1–3 | 10–39 | 14,1–55,1° | narancs |
| 2 | 4 | 40–49 | 56,5–69,2° | sárga |
| 3 | 5–11 | 50–119 | 70,6–168,1° | zöld |
| 4 | 12–17 | 120–179 | 169,4–252,8° | kék |
| 5 | 18–21 | 180–219 | 254,1–309,3° | lila |
| 6 | 22–23 | 220–239 | 310,7–337,4° | rózsaszín |

**A vödrök sorrendje pontosan a 2. szakasz névtáblájáé** — ez független
megerősítés, nem következtetés.

### 3.4 ⚠️ Egy mért RÉS a tartományokban

`b == 25` (H 250–254, kb. **353,0–358,8°**) **egyetlen vödörbe sem kerül**:
a `0x009dbf31  add eax, -0x16; cmp eax, 1; ja` ág kihagyja, és a `b==24`
esetet a korábbi `cmp eax, 0x18` már elkapta.

⇒ A mélyvörös-rózsaszín határ egy keskeny sávja **elvész**. Ez az
eredeti viselkedése; ha reprodukáljuk, **reprodukáljuk a rést is**.

### 3.5 A döntés

A 16 dword (= **8 double**) vödörből a végső menet (`0x009dbf7d`–
`0x009dbfc4`) a **legnagyobbat** választja. Kezdőértékek mérve:
`0xcf3f08` = **−DBL_MAX** (futó maximum), `0xcf4038` = **+DBL_MAX**.

- a 7. vödörbe **soha nem ír senki** — a `cmp esi, 7 / jae` ág ezért
  gyakorlatilag csak az érintetlen `esi = −1`-et fogja el;
- **`−1` akkor és csak akkor**, ha **egyetlen képpont sem** lépte tút az
  `S > 50` küszöböt ⇒ a kép akromatikus ⇒ **mind a három** akromatikus
  token illeszkedik.

**Nincs abszolút küszöb**: elég egyetlen telített képpont, és a kép már
színes kategóriába kerül.

---

## 4. Hol fut le, és mit ír

A hívási lánc: `0x00425f60` (12 452 b, a kép-metaadat kezelője) →
`0x00424c20` → `0x009dbd10`. A hívás helye `0x00428566`, egy jelzőhöz
kötve (`0x00428559  cmp byte ptr [ebp+0x10], 0`).

Ugyanez a függvény írja az **`avgcolor`** kulcsot is (`0x004280d8`) —
de **1150 sorral korábban, teljesen külön ágon**. A kettőnek nincs
adatkapcsolata.

⇒ **Az `avgcolor` NEM a színkeresés bemenete.** Ez az ini-kulcs másra
való; a keresés a rasztert nézi.

---

## 5. Eredeti / nálunk / teendő

| # | eredeti | nálunk MA | teendő |
|---:|---|---|---|
| 1 | hue-hisztogram az **egész rasztról** | az **átlagszín** egyetlen besorolása | algoritmuscsere |
| 2 | súly = a képpont **telítettsége** | — | átvenni |
| 3 | `S <= 50/255` képpont kimarad | `_ACHROMATIC_SAT_MAX = 0.12` **egészre** | átvenni |
| 4 | `MAX == 0` kimarad | nincs ilyen | átvenni |
| 5 | **7** színvödör | 7 szín + 3 akromatikus | a hetet átvenni |
| 6 | akromatikus ⇒ **mindhárom** token | egyet választ V szerint | átvenni |
| 7 | a piros **átfordul** (0–12,7° és 338,8–352,9°) | `_HUE_RED_MIN/MAX = 345/15` | pontosítani |
| 8 | **rés** 353,0–358,8°-nál | nincs | átvenni (az eredeti hibája is szerződés) |
| 9 | nincs abszolút küszöb — a legnagyobb vödör nyer | — | átvenni |

---

## 6. Kész, ha

- [ ] A besorolás **hisztogram-alapú**, nem az átlagszínből.
- [ ] A súly a képpont telítettsége (0–255), nem 1.
- [ ] `MAX == 0` és `S <= 50` képpont **kimarad**.
- [ ] Hét vödör, a 3.3 tábla **pontos** `b`-tartományaival.
- [ ] Akromatikus kép (nincs `S > 50` képpont) **mindhárom** akromatikus
      tokenre illeszkedik.
- [ ] A 353,0–358,8°-os **rés** reprodukálva, és **teszt őrzi** — különben
      egy későbbi „javítás" némán eltünteti.
- [ ] Egységteszt mindegyik vödörhatárra (`b` = 0/1, 3/4, 4/5, 11/12,
      17/18, 21/22, 23/24, 24/25) — **14 határeset**.

---

## 7. Bizonyítottsági fok

**Megerősített**: a névtábla és indexei; a BGRA-sorrend (három ág, három
eltolás); a `1530`-as hue-kör (két mért konstans); az `S <= 50` és a
`MAX == 0` küszöb; a `b = H/10` vödrözés és mind a hét tartomány; a rés;
a „legnagyobb vödör nyer" döntés; a `−1` jelentése; hogy az `avgcolor`
külön ágon készül.

**Erős**: hogy a bemeneti raszter a bélyegkép-gyorstárból jön — a hívás
előtt egy kritikus szakasszal védett, szál-tulajdonost ellenőrző
gyorstár-objektumot bontanak le (`0x004284fd`–`0x00428557`,
`GetCurrentThreadId` + `LeaveCriticalSection`). **Nem bizonyított.**

---

## 8. Nyitott kérdések mérlege

| kérdés | állapot |
|---|---|
| Mi a besorolás algoritmusa? | **LEZÁRVA** — 3. szakasz |
| Mik a küszöbök? | **LEZÁRVA** — `MAX==0`, `S<=50`, `b=H/10` |
| Hány kategória, milyen határokkal? | **LEZÁRVA** — 3.3 |
| Mit jelent a `−1`? | **LEZÁRVA** — 3.5, és mindhárom token |
| Az `avgcolor` a bemenet? | **LEZÁRVA — NEM** (4.) |
| **Melyik rasztert kapja?** | **HATÓKÖRÖN KÍVÜL** — nincs hozzá golden anyagunk (a Picasa 2016 óta nem szerezhető be), tehát a választás **sem így, sem úgy nem ellenőrizhető**; a saját bélyegképünkön futtatjuk. Eldöntötte: a 2026-08-26-i kutatói kör. |

```
Nyitott kérdések: 0 nyílt · 5 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

## 9. Amit KIZÁRTAM

- **Hogy az `avgcolor` lenne a bemenet.** Külön ágon készül, 1150 sorral
  előbb; a hisztogram a rasztert olvassa.
- **Hogy a besorolási szabály „nem mérhető"** — a `classify.py` docstringje
  ezt állította; egyetlen 752 bájtos függvény cáfolja.
- **Hogy a fekete/szürke/fehér három külön kategória volna.** Az eredeti
  egyetlen `−1` ágon mindhárom tokent visszaadja.
