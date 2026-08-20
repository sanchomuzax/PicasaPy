# A kollázs ÉLETCIKLUSA — a teljes UI/UX folyamat

**Státusz:** a tulajdonos 2026-08-20-i, futó Picasa 3-on végigjátszott
menetének leírása, bináris és erőforrás-bizonyítékkal soronként.

⚠️ **Ez a lap NORMATÍV.** Ahol a bizonyíték hiányzik, azt kimondja — ott
tilos kitalálni. A tulajdonos kikötése: *„Minden UGYANÚGY működjön a
kollázs kapcsán, ahogy az eredeti Picasa tette. Semmi »kitaláljuk«
funkció ebben!"*

---

## 1. A három állapot

| állapot | mit lát a felhasználó | fájlok a Kollázsok mappában |
|---|---|---|
| **szerkesztés** | kollázs-lap a fülsávban, bal oldalt a Beállítások | — |
| **PISZKOZAT** | a Kollázsok albumban egy csempe „PISZKOZAT" felirattal | `<név>.jpg` (640 hosszú él) + `autosave.cxf` |
| **kész** | a kollázs képnézetben | `<név>.jpg` (5120 hosszú él) + `<név>.cxf` |

---

## 2. Az életciklus — állapotátmenetek

```
                    ┌──────────────────┐
   Kollázs ────────►│   SZERKESZTÉS    │◄──── „Kollázs szerkesztése"
   létrehozása      └───┬──────────┬───┘         (bármikor)
   a könyvtárból        │          │
                „Bezárás”      „Kollázs létrehozása”
                        │          │
                        ▼          ▼
              ┌─────────────┐   ┌──────────────────────────┐
              │ Jóváhagyás… │   │ Lecseréli a meglévőt,    │
              │  (3 gomb)   │   │ vagy újat hoz létre?     │
              └──┬───┬───┬──┘   └────┬──────────┬──────┬───┘
      Piszkozat  │   │   │ Mégse     │ Meglévő  │ Új   │ Mégse
       mentése   │   │   └──►vissza  │ cseréje  │      └──►vissza
                 │   │                └────┬─────┘
                 │   └─ Módosítások         │
                 │      elvetése ──►eldobás │
                 ▼                          ▼
           ┌───────────┐            ┌───────────────┐
           │ PISZKOZAT │──„Létrehozás”──►│  RENDERELÉS │──►│ KÉSZ │
           └───────────┘            └───────────────┘   (képnézet)
```

---

## 3. „Bezárás" — a piszkozat ága

### 3.1 A megerősítő párbeszéd

**Cím:** `CCollageUI::ConfirmCloseTitle` = `Please Confirm...` →
**„Jóváhagyás…"**

**Szöveg:** `CCollageUI::ConfirmCloseMsg` →
> „A jelenlegi kollázs nem mentett módosításokat is tartalmaz.
> A lap bezárása előtt menti vagy elveti ezeket? (Megjegyzés: A program a
> piszkozatokat a »Kollázsok« albumba menti.)
> A lap nyitva hagyásához kattintson a Mégse gombra."

**Három gomb, ebben a sorrendben:**

| gomb | kulcs | hatás |
|---|---|---|
| **Piszkozat mentése** | `CCollageUI::ButtonSaveDraft` | piszkozat-állapotba lép |
| **Módosítások elvetése** | `CCollageUI::ButtonDiscard` | eldobás, a lap bezárul |
| **Mégse** | — | a lap **nyitva marad** |

*Bizonyíték:* a négy erőforrás-kulcs a `stringres`-ből, a párbeszéd a
`0x006251f0` és `0x0082c0a0` függvényekben; és a tulajdonos képernyőképe.

### 3.2 Ami a piszkozat mentésekor a lemezre kerül

| fájl | tartalom |
|---|---|
| `<név>.jpg` | **maga a kollázs, 640 képpont hosszú élen**, rá a „PISZKOZAT" felirat |
| `autosave.cxf` | a projekt |

**A `<név>` a kollázs VÉGLEGES neve** — a forrásmappa/album nevéből, a
#969 elnevezési törvénye szerint, `%s%lu` alakban számozva
(`0x00993030`, `0x00cd8d5c`; elválasztó nélkül fűz: `AI` + `10` =
`AI10`).

**Mért példák a futó Picasából:**

| képernyőkép | fájlnév | méret | fájlméret |
|---|---|---|---|
| 2026-08-20 11:56 | `AI10.jpg` | 640 × 453 | 46 KB |
| 2026-08-20 14:47 | `lake.jpg` | 640 × 453 | 78 KB |

**640 a HOSSZABB él, az arány a lapé.** Az `AI10` kész változata
5120 × 3620 → `5120 / 640 = 8,0` és `640 × 3620/5120 = 452,5 → 453`.

### 3.3 ⛔ TILOS: `autosave.jpg`

**A `autosave.jpg` név NEM létezik.** Háromszorosan igazolva:

1. **A binárisban nulla találat** `autosave.jpg`-re. A teljes
   `autosave`-család: `autosave` (`0x00c9be68`), `autosave.mxf`
   (`0x00ca7770`, film), **`autosave.cxf`** (`0x00ca77ac`, kollázs),
   `Recovered Autosave`, `CollageAutosave`, `collage::autosave`,
   `collage::lastautosave`, `CAutosaveCollageThread`. **Kép-kiterjesztésű
   tag nincs.**
2. A tulajdonos **valódi**, 11 páros Kollázsok mappájában nincs
   `autosave.*` — csak `AI*.jpg`, `AI*.cxf` és `.picasa.ini`.
3. A futó Picasa két képernyőképén a piszkozat neve `AI10.jpg`, illetve
   `lake.jpg`.

### 3.4 ⛔ TILOS: egyszínű szürke helykitöltő

A helykitöltő **nem** szürke téglalap: **a kollázs látszik rajta**, a
felhasználó saját háttérszínével, a csempéivel és a keretekkel — csak
kicsiben. A tulajdonos szó szerint: *„a kollázs beállításaiban
állítottam be azt a színt… a kép közepén kicsiben a kollázs látszik."*

⚠️ A `0xFF3F3F3F` konstans (`0x0068a7c6`) **nem a háttérszín** — a
háttér a projektből jön. Hogy mi, az nincs megfejtve.

### 3.5 A „PISZKOZAT" felirat

**Szöveg:** `projectutils::draft` = `DRAFT` → **„PISZKOZAT"**
(`0x00c9cefc`, függvény `0x0061d350`).

**Helye: BELE VAN RAJZOLVA A KÉPBE**, nagy fehér betűkkel, középen. Nem
az album neve, nem a lap címe, nem csempe-felirat: a bélyegképen is
ott van, tehát a JPEG tartalma.

⚠️ A `projectutils::draft_format` = `DRAFT -- %s` → `PISZKOZAT -- %s`
**máshol** használatos. **Ne kössük ide.**

*Megjegyzés:* ugyanezt a `0x0061d350`-et **a mentési ág
(`0x0068a6a0`) ÉS a helyreállító ág (`0x008419e0`) is hívja** — a
felirat rajzolása közös kód.

---

## 4. A PISZKOZAT-állapot

### 4.1 Amit a felhasználó lát

- a **Kollázsok albumban** csempe a „PISZKOZAT" felirattal;
- megnyitva a **kicsinyített kollázs**, rajta a felirat;
- **a kép fölött egy „Létrehozás" gomb** — ez **élő felületi elem**,
  nem a JPEG része (a bélyegképen nincs rajta);
- fent balra a **„Kollázs szerkesztése"** gomb **aktív**;
- a bal oldali fotószerkesztő eszközök (Vágás, Kiegyensúlyozás,
  Vörösszem, Retusálás…) **halványak**.

*Bizonyíték:* a tulajdonos két képernyőképe és a leírása.

### 4.2 A piszkozat korlátozásai

`projectutils::draft_collage` →
> „Ez a kollázs még nem készült el teljesen. A kollázs befejezéséhez
> (ami a megosztás és a nyomtatás feltétele) kattintson a »Létrehozás«
> gombra. Megjegyzendő, hogy később bármikor módosíthatja a kollázst,
> akár még a mentése után is."

Ebből **normatív**: a piszkozat **nem osztható meg és nem nyomtatható**.

### 4.3 A „Létrehozás" gomb

Megnyomására a gomb helyén **„Folyamatban…"** felirat jelenik meg, majd
lefut a renderelés.

⚠️ **NEM IGAZOLT**: a „Létrehozás" és a „Folyamatban…" erőforrás-kulcsa.
A binárisban nincs `Create Now` string; a `draft_collage` szövege
hivatkozik rá („kattintson a »Létrehozás« gombra"), és létezik egy
`eMenuCreate` = `&Create` → `&Létrehozás` menü-kulcs, de hogy a gomb ezt
használja-e, **nem tudom**. A feliratokat a képernyőkép igazolja, a
kulcsuk nyitott kérdés.

---

## 5. „Kollázs létrehozása" — a befejező ág

### 5.1 A párbeszéd, ha a kollázs már létezik

**Cím:** `CCollageUI::ConfirmTitle` = `Replace Existing or Create New?` →
**„Lecseréli a meglévőt, vagy újat hoz létre?"**

**Szöveg:** `CCollageUI::ConfirmMsg` →
> „Eddig egy korábban készült kollázst szerkesztett.
> Lecseréli a meglévő kollázst, vagy teljesen újat hoz létre?
> (Megjegyzés: a program az összes kollázst a »Kollázsok« albumban tárolja.)
> A Mégse gombra kattintva mentés nélkül folytathatja a kollázs szerkesztését."

| gomb | kulcs | hatás |
|---|---|---|
| **Meglévő cseréje** | `CCollageUI::ButtonReplace` | **ugyanaz a fájlnév**, felülírva |
| **Új létrehozása** | `CCollageUI::ButtonCreateNew` | új sorszám |
| **Mégse** | — | vissza a szerkesztésbe, mentés nélkül |

*Bizonyíték:* `0x0083ba60` és `0x0061df10`, plusz a tulajdonos
képernyőképe.

**Mért igazolás a felülírásra:** az `AI10.jpg` a piszkozat **46 KB**-járól
**ugyanazon a néven** nőtt **2440 KB**-ra (5120 × 3620). Nincs
újraszámozás, nem marad árva helykitöltő.

### 5.2 Renderelés közben

A kicsinyített, PISZKOZAT-feliratos kép látszik, amíg a renderelés fut.
A folyamatjelzés szövege: `collage::initializing` =
`Creating Collage...initializing` → **„Kollázs létrehozása…
inicializálás"** (`0x0088b220`).

### 5.3 A renderelés UTÁN — ez a legfontosabb pont

**A kollázs KÉPNÉZETBEN nyílik meg, NEM szerkesztő üzemmódban.**

A tulajdonos szó szerint: *„létrejön a kollázs. De nem szerkesztés
üzemmódban, hanem nézem mint egy képet."*

Fent balra a **„Kollázs szerkesztése"** gomb látszik, azzal lehet
visszatérni a szerkesztéshez.

⚠️ **Automatikus odaugrás/értesítés a folyamat része NEM lehet** —
a felhasználó a képnézetben találja magát, nem kap kattintható
értesítést. (A `collage::done` = „A kollázs kész (kattintson ide)"
string létezik (`0x00cc4e44`), de a tulajdonos szerint ebben a
folyamatban nem jelenik meg; a `0x0088b220` szálbelépési pontnak
nincs statikus hívója, ami feltételes/tálcás értesítésre utalhat.
**Nyitott kérdés**, nem normatíva.)

---

## 6. „Kollázs szerkesztése" — a visszaút

**Vezérlő:** `editpanel/editcollage` — a **szerkesztőpanel** eleme, nem a
kollázs-panelé.

`editpanel.tre:1350`:
```
editpanel/editcollage: root
m_offsetLT
m_buttontypecolor
m_hidden
```
gyerekei: `editpanel/collage_icon` (`m_buttoniconleft`),
`editpanel/editcollage-label` (`m_buttonfontRC`).

**Feliratok** (`editpaneltext.tre:23-27`):
- `Edit Collage` → **„Kollázs szerkesztése"**
- tooltip: `Edit the collage from which this image was created` →
  **„A kép alapjául szolgáló kollázs szerkesztése"**

**Mikor látszik:** ha a megnyitott kép egy kollázs kimenete (van
`.cxf` párja). **Piszkozaton is** — a tulajdonos képernyőképe mutatja.
Alapból rejtett (`m_hidden`).

⚠️ Ne keverjük a `collagepanel::back_to_collage` = **„Vissza a
kollázshoz"** felirattal — az MÁSIK vezérlő.

---

## 7. A kör

A tulajdonos leírása szerint a folyamat **ciklikus**: a kész kollázst a
„Kollázs szerkesztése" gombbal újranyitja, szerkeszti, és ha megint
„Bezárás"-t nyom, **elölről kezdődik** a 3. szakasz.

---

## 8. Amit NEM tudunk — kimondva

1. **A „Létrehozás" és a „Folyamatban…" gomb erőforrás-kulcsa.**
2. **A helykitöltő pontos tipográfiája**: betűméret, a felirat pontos
   pozíciója, van-e árnyék/sáv mögötte.
3. **A `0xFF3F3F3F` szerepe** — nem a háttérszín; hogy mi, nyitott.
4. **A `480` konstans** (`0x0068a79c`) szerepe: a mért képek 640 × 453-asak,
   tehát nem fix magasság.
5. **A `collage::done` értesítés** melyik folyamathoz tartozik.
6. **Mi történik két egymás utáni piszkozat-mentésnél** — erős
   következtetés szerint az 5.1 párbeszéd jön, de nem mért.

---

## 9. Kapcsolódó jegyek

| jegy | tárgy |
|---|---|
| #1072 | a PISZKOZAT-állapot és a látható helykitöltő |
| #1002 | „Kollázs szerkesztése" gomb |
| #1028 | a létrehozás utáni műveletsor (`question`) |
| #969 | az elnevezési törvény |
| #979 | az árva automentés helyreállítása |
| #1097 | a rejtett `.picasa.ini` írása (P0) |
