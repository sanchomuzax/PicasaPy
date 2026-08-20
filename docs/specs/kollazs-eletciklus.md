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

### 4.3 A „Létrehozás" gomb és a „Folyamatban…" felirat — MEGFEJTVE

Mindkettő az **`editpanel`** vezérlője, és **ugyanazon a helyen** ül: az
egyik a másik helyére lép.

| vezérlő | felirat (EN) | **magyar** |
|---|---|---|
| **`editpanel/render_now`** | `Create Now` | **„Létrehozás"** |
| **`editpanel/in_progress_label`** | `In Progress...` | **„Folyamatban..."** |

*Forrás:* `editpaneltext.tre:367-371`, a magyar a honosítási táblából.

**A deklaráció** (`editpanel.tre:679-690`):

```
editpanel/in_progress_base: editpanel/in_progress_label
XConstraint 0, 0, -17
XConstraint 1, 1,  15
YConstraint 0, 0,  -3
YConstraint 1, 1,   5
Property predraw 1

editpanel/in_progress_label: editpanel/overlay_group
m_systemfont16
m_centerX
YConstraint 0.5, 0.875, 0
m_hidden

editpanel/render_now: editpanel/overlay_group
m_centerX
YConstraint 0.5, 0.875, 0
m_hidden
```

**Amit ez kimond:**

1. **Mindkettő az `editpanel/overlay_group` gyereke** — vagyis a **kép
   FÖLÖTTI réteg**, nem a JPEG része. Ez független megerősítése annak,
   amit a bélyegképből következtettünk.
2. **Vízszintesen középre** (`m_centerX`).
3. **Függőlegesen a saját közepük a szülő 87,5%-ára** kerül
   (`YConstraint 0.5, 0.875, 0`) — mindkettő **ugyanoda**, ezért lép az
   egyik a másik helyére.
4. A „Folyamatban…" felirat **16 pontos rendszer-betű**
   (`m_systemfont16`), és van mögötte egy **háttérlap**
   (`in_progress_base`), `predraw`-val, körben **−17 / +15 / −3 / +5**
   képpont ráhagyással.
5. Mindkettő **alapból rejtett** (`m_hidden`).

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
a felhasználó a képnézetben találja magát.

### 5.4 A `collage::done` értesítés az ASZTALI HÁTTÉRKÉP ágé — MEGFEJTVE

A „A kollázs kész (kattintson ide)" (`collage::done`, `0x00cc4e44`)
sokáig nyitott kérdés volt: a string létezik, a tulajdonos szerint
mégsem jelenik meg a rendes létrehozáskor.

**A hívási gráf eldönti.** Az értesítő függvény (`0x0088a020`) hívja a
`0x0057aa10`-et, amiben ez van:

```
Picasa
Backgrounds
CThumbUI::BackgroundsFolder
picasabackground.bmp
Control Panel\Desktop\
```

A `Control Panel\Desktop\` a Windows **asztali háttérkép**
registry-kulcsa, a `picasabackground.bmp` pedig a Picasa saját
háttérkép-fájlja.

**Tehát a `collage::done` értesítés az „Asztali háttérkép" ághoz
tartozik**, nem a sima „Kollázs létrehozása"-hoz. A tulajdonos
megfigyelése és a bináris ezzel **összeér**.

⚠️ **Normatíva:** a rendes létrehozás után **NE tegyünk ki kattintható
értesítést**. Ha az „Asztali háttérkép" gombot építjük meg, **oda**
tartozik.

*(Bizonyítottsági fok: erős. A hívási él és a háttérkép-stringek
mérve; hogy az értesítés kizárólag ezen az ágon fut, dekompilációval
volna bizonyítható.)*

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

## 8. A hat nyitott kérdés elszámolása (2026-08-20, második kör)

| # | kérdés | állapot |
|---|---|---|
| 1 | a „Létrehozás"/„Folyamatban…" kulcsa | ✅ **MEGFEJTVE** — 4.3 |
| 2 | a helykitöltő tipográfiája | ⚠️ részben — ld. lent |
| 3 | a `0xFF3F3F3F` szerepe | ⚠️ szűkítve — ld. lent |
| 4 | a `480` konstans szerepe | 💡 **új hipotézis** — ld. lent |
| 5 | a `collage::done` hova tartozik | ✅ **MEGFEJTVE** — 5.4 |
| 6 | két egymás utáni piszkozat-mentés | ⚠️ erős következtetés |

### 8.2 A helykitöltőbe rajzolt „PISZKOZAT" tipográfiája

**A `.tre`-erőforrásokban NINCS ilyen vezérlő** — végigkerestem, `draft`
nevű elem egyik panel-fájlban sem szerepel. Ebből következik, hogy a
feliratot **kód rajzolja a JPEG-be**, nem a felületleíró.

Ezért a `.tre` ezt **nem is fogja megmondani**; csak a bináris
dekompilációja vagy a kész fájl **képpont-mérése**.

### 8.3 A `0xFF3F3F3F` és a `480` — MEGFEJTVE: MÁSIK helykitöltőé

⚠️ **Ez a két konstans NEM a piszkozat-helykitöltőé.** Korábban ide
soroltam őket — **tévesen**. Az **árva-automentés** helyreállító ágához
tartoznak.

**A Picasának KÉT helykitöltője van:**

| | mikor keletkezik | név | méret | tartalom |
|---|---|---|---|---|
| **piszkozat** | a Picasa maga ment piszkozatot | **a kollázs neve** (`AI10.jpg`, `lake.jpg`) | **a lap arányát követi** (A4 fekvőn 640 × 453) | **a kollázs kicsiben** |
| **árva** | a Picasa **árva `autosave.cxf`-et** talál | **`autosave.jpg`** | **640 × 480 FIX** | **egyszínű `0xFF3F3F3F`** |

**Az árva-ág paraméterei** (`0x008419e0`, `collage::recoveredautosave`):

| konstans | cím | érték |
|---|---|---|
| szélesség | `0x0068a767` | `0x280` = 640 |
| magasság | `0x0068a79c` | `0x1e0` = **480** |
| szín | `0x0068a7c6` | `0xFF3F3F3F` = RGB(63, 63, 63) |
| minőség | `0x0068a7f6` | q85 |

**A bizonyíték, hogy ez a helyes hozzárendelés:** a tulajdonos
Kollázsok mappájában megjelent egy `autosave.jpg` — **egyszínű
sötétszürke, 640 × 480**, PISZKOZAT felirattal. A PicasaPy ezt a nevet
**sehol nem írja**; a fájlt a **valódi Picasa** hozta létre, a
PicasaPy által árván hagyott `autosave.cxf`-re válaszul. Mind a négy
paraméter egyezik. → **#1100**

*(A `.tre`-kben van egy hasonló alakú, de MÁS konstans:
`Property negativemode 8f2f2f2f` — nem szabad összekeverni.)*

### 8.4 A piszkozat-helykitöltő mérete — a lap arányát követi

A `640` a **hosszabb él**, a másik oldal a **lap arányából**:

| lapformátum | tájolás | méret |
|---|---|---|
| A4 | fekvő | **640 × 453** ← a két mért képernyőkép |
| Desktop 4:3 | fekvő | 640 × 480 |
| Négyzet | — | 640 × 640 |
| HDTV 16:9 | fekvő | 640 × 360 |
| A4 | álló | **453 × 640** ⚠️ ellenőrizetlen |

⚠️ **Az ÁLLÓ eset ellenőrizetlen.** Egy versengő olvasat szerint a lap
egy **640 × 480-as dobozba** illeszkedne, ami álló A4-en **339 × 480**-at
adna. **Fekvő lapon a két szabály egybeesik**, ezért a méréseink nem
különböztetik meg őket — és minden mintánk fekvő.

**Amivel eldőlne:** egy **álló lapú** piszkozat mérete az eredeti
Picasából (elég a szám a státuszsorból).

⚠️ Megjegyzés a 8.3-hoz: a `480` ott **fix** magasság (az árva-ágé), itt
**véletlen egybeesés** a 4:3-as lapnál. A két 480 **nem ugyanaz**.

### 8.5 Két egymás utáni piszkozat-mentés

A tulajdonos leírása a **kész → szerkesztés → Bezárás → megint
piszkozat** kört igazolja. Mivel a kollázsnak ilyenkor **már van neve**,
a helykitöltő ugyanarra a névre íródik.

**Erős következtetés**, nem mérés: a névadó (`%s%lu`) a
piszkozat-mentő ágban fut (`0x006251f0`), de a már névvel bíró kollázs
az 5.1 párbeszédhez tartozik.

---

## 8/b Amit továbbra sem tudunk

1. A helykitöltő **betűmérete és a felirat pontos pozíciója** a képen
   belül (kód rajzolja, `.tre` nem írja le).
2. A `0xFF3F3F3F` **tényleges szerepe**.
3. A helykitöltő mérete **álló lapon** (8.4).
4. Hogy a `collage::done` **kizárólag** a háttérkép-ágon fut-e.

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
