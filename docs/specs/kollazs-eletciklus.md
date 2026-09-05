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

### 3.5/b A létrehozás közbeni ANIMÁCIÓ — a `respack.yt`-ból (2026-08-23, #1072)

A tulajdonos megfigyelése („a létrehozás alatt egy »Piszkozat« felirattal
és egy **animációval** mutatja, hogy készül") második fele is megvan, és
**nem kellett hozzá képernyőkép** — a `respack.yt` megadja:

```
layer:collagepanel/decrect(overlaydecrect): collageprog_base
layer:collagepanel/#collageprog_spinner_orig      (1 243 B)
layer:collagepanel/collageprog_spinner            (1 748 B)
```

A hozzájuk tartozó vezérlők: `collageprog_clip`, `collageprog_status`,
`collageprog_title`, `collageprog_spinner` (`0x00887390`, `0x00887580`,
`0x00887920`).

⇒ Az „animáció" egy **pörgő** (`spinner`) egy `overlaydecrect` alapon —
ugyanaz a minta, mint az `activity/spinner` és az `activitycapture/spinner`
a csomag más részein. A `#`-os `_orig` változat a kikommentezett, korábbi
grafika.

A felirat oldala a **4.3**-ban: `editpanel/render_now` („Létrehozás") és
`editpanel/in_progress_label` („Folyamatban...") **ugyanazon a helyen**
váltják egymást.

*Bizonyítottsági fok: **megerősített** a rétegek létére és nevére
(`respack.yt` névindex); a pörgés **animációs paraméterei** (képkockaszám,
sebesség) nincsenek mérve.*

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

### 4.4 A megvalósítás és EGY MEGDŐLT elvárás (2026-08-24, #1072)

*Forrás: `editpanel.tre:686` (`editpanel/render_now`).*

A PISZKOZAT-állapot ezzel a körrel a kódban is létezik:

| a jegy elvárása | mi lett belőle |
|---|---|
| jelölés az albumban | **a képbe rajzolt „PISZKOZAT" felirat** — ld. lent |
| megosztás/nyomtatás tiltása | a nyomtatás és az e-mail-csatolás visszautasítja a piszkozatot, a `projectutils::draft_collage` szövegével |
| külön befejező lépés | „Létrehozás" gomb a kép fölött (`editpanel/render_now`), rendereléskor „Folyamatban..." |
| a piszkozat szerkeszthető | a „Kollázs szerkesztése" a piszkozaton is nyit — a projektje az `autosave.cxf` |

**Az állapot forrása a lemez**, nem külön nyilvántartás: a kép PISZKOZAT,
ha nincs `<név>.cxf` párja, de a mappában ott az `autosave.cxf` — pontosan
az 1. szakasz táblája. Kód: `picasapy/collage/draft_state.py`. Emiatt SQL
séma- vagy oszlopváltozás nem kellett, és a jelzés magától követi, ha a
fájlok kívülről változnak.

⚠️ **A `PISZKOZAT -- <név>` cím-előtag NEM készült el, és nem is szabad
megcsinálni.** A #1072 leírása még azt kérte, hogy a piszkozat az albumban
`draft_format` (`DRAFT -- %s`) szerinti címmel jelenjen meg. A 3.5 azóta
kimondta, hogy ez a formátumsztring **máshol** használatos, a piszkozatot
pedig a KÉPBE rajzolt felirat jelöli — amit a tulajdonos képernyőképe is
így mutat. A két jelölés együtt kétszeres volna.

✅ **A korábbi korlát megszűnt (2026-08-26, #1387):** a befejezés utáni
takarítás (`_discard_draft_after_render`) korábban a BEÁLLÍTOTT
Kollázsok-mappából dobta el az `autosave.cxf`-et. Ha a felhasználó a
piszkozat mentése után átállította a kimeneti mappát, a régi automentés
árván maradt — és a valódi Picasa arra `autosave.jpg`-t gyártott (8.3,
#1100).

A javítás: a vezérlő eltárolja, honnan jött a MOST NYITOTT piszkozat
TÉNYLEGESEN (`_collage_panel_draft_source_dir` — a `saveCollageDraft`
sikeres írása, az `openCollageProject` piszkozat-ága, illetve a
`restoreCollageDraft` állítja be). A takarítás EZT a mappát használja, a
beállítottat csak akkor, ha a menetben még nem volt ismert tényleges hely
(friss panel). Kód: `picasapy/app/collage_save.py`
(`_discard_draft_after_render`, `saveCollageDraft`, `openCollageProject`,
`restoreCollageDraft`); a `picasapy/app/collage_controller.py`
`_ensure_collage_panel`-je hozza létre a mezőt.

**Az `autosave.jpg` döntése változatlan (#1100 alapján):** ha a régi
helyen a valódi Picasa már ráírta a saját szürke helykitöltőjét, az NEM a
mi fájlunk — a takarítás csak az `autosave.cxf`-et törli néven, az
`autosave.jpg`-hez nem nyúl.

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

### ✅ Az ÁLLÓ eset MEGMÉRVE (2026-08-20)

A tulajdonos készített egy **A4 álló** piszkozatot. A Picasa
státuszsora:

```
Kollázsok > lake.jpg   2026. 08. 20. 14:47:10   453x640 képpont   65 KB
```

a `lake.cxf` fejléce pedig `format="297:210" orientation="portrait"`.

**453 × 640.** Ellenőrzés: `640 × 210/297 = 452,5 → 453`. ✔

➡️ **A „640 a hosszabb élen" szabály IGAZOLT, a doboz-hipotézis
MEGDŐLT** (az 339 × 480-at adott volna). A mai megvalósításunk helyes.

⚠️ Megjegyzés a 8.3-hoz: a `480` ott **fix** magasság (az árva-ágé), itt
**véletlen egybeesés** a 4:3-as lapnál. A két 480 **nem ugyanaz** — ez a
szám-egyezés egyszer már félrevitt minket.

### 8.5 A „PISZKOZAT" felirat — a szöveg KILÓG és LEVÁGÓDIK álló lapon

Két mért eset ugyanabból a kollázsból:

| tájolás | kép | a felirat |
|---|---|---|
| **fekvő** | 640 × 453 | teljesen kifér, oldalt margóval |
| **álló** | 453 × 640 | **kilóg és levágódik MINDKÉT oldalon** — a „P" és a „T" a kép szélén elvágva |

**Ebből következik:** a betűméret **nem a szélességhez** igazodik. A két
eset akkor áll össze, ha a méret a kép **magasságához** kötött: fekvőn a
magasság 453 (a felirat kifér), állón 640 (ugyanaz az arány már
szélesebb, mint a 453-as kép).

**Becsült arány:** a felirat szélessége ≈ **0,94 × a kép magassága**.

⚠️ **Bizonyítottsági fok: erős, de nem pontos.** A 0,94 két
képernyőképről, szemmértékkel becsült érték — a betűméret és a pontos
pozíció **képpont-pontosan csak a fájlból** mérhető, és a
`.tre`-erőforrásokban nincs benne (a feliratot kód rajzolja).

⚠️ **NORMATÍVA: a levágódás az EREDETI viselkedése.** Álló lapon a
feliratnak **ki KELL lógnia**. Aki „javításként" a szélességhez
igazítaná, **eltérést** épít be — ugyanaz a hibaalak, mint a #1045
beszorítása.

### 8.6 A fájlnév a FORRÁSMAPPA neve — megerősítve

A `lake.cxf` eldönt egy eddig kétértelmű pontot:

```
<albumTitle>Kollázsok</albumTitle>
<src>$My Pictures\lake\262_size_1366x768_26.jpg</src>
       ↑ a forrásmappa: „lake"
fájlnév: lake.jpg
```

Az **albumTitle „Kollázsok"**, a forrásmappa **„lake"**, a fájl
**`lake.jpg`** → **a név a FORRÁSMAPPÁBÓL jön, nem az albumTitle-ből.**

A korábbi `AI`-mintákban a kettő megegyezett, ezért nem lehetett
megkülönböztetni. **A mi megvalósításunk helyes**
(`collage_controller.py:339 _title_from_sources` a közös forrásmappa
nevét adja).

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

---

## 15. A `.cxf` KÓDOLT ÚTVONALAI — mért invariánsok (2026-08-20)

A `<src>` mezők (csomópont ÉS háttér) nem nyers útvonalak. A #1096
megvalósításához mért tények, hogy a következő kör ne vezesse le újra.

### 15.1 Melyik alak fordul elő ténylegesen

12 valódi Picasa-`.cxf`, **101 hivatkozás** (a tulajdonos 11 páros
Kollázsok mappája + az álló `lake.cxf`):

| alak | darab | arány |
|---|---:|---:|
| **`$My Pictures\…`** | **101** | **100,0%** |
| `$UNC…` | 0 | 0% |
| `[betű]\…` | 0 | 0% |
| nyers `C:\…` | 0 | 0% |

Egyetlen változónév fordul elő: **`My Pictures`**.

⚠️ **Vakfolt:** a 12 minta egyetlen felhasználótól, egyetlen gépről van,
és a képek mind a Képek mappa alól. **A nulla előfordulás nem bizonyítja
a nemlétezést** — a másik két alak a kódoló formátumsztringjeiből ismert.

### 15.2 Az OLVASÁSHOZ a `%s%s%s` bontás KÖZÖMBÖS

A két formátumsztring:

```
0x00cd8f44   $UNC%s%s%s
0x00cd8f50   [%c]%s%s%s
```

**A három `%s` között nincs literál** — se elválasztó, se semmi. Bárhogy
is bontja szét az ÍRÓ, a három darab hézag nélkül kerül a fájlba.

➡️ **Az olvasónak ezért az előtag utáni MINDEN a maradék útvonal.** A
bontás nem tud belezavarni.

**Ebből következik:**

- a **`[betű]\`** alak nyugodtan feloldható: `[C]` + `\mappa\kep.jpg`
  → `C:\mappa\kep.jpg` — nincs mit rosszul összefűzni;
- a **`$UNC`** esetében a bizonytalanság **NEM a bontás**, hanem hogy a
  maradék `\\`-sal kezdődik-e, vagy az író levágja. **Ezért ott
  felismerés igen, feloldás nem** — a nyers szöveg megy tovább, és
  látható helykitöltő lesz belőle, nem néma üresség.

⚠️ Egy korábbi kommentem általánosabb aggályt fogalmazott meg
(„a `%s%s%s` bontása nem igazolt") — az **túl széles volt**; a bontás
csak az ÍRÁS oldalán kérdés.

### 15.3 Két külön NÉVRÉTEG van

A string-tábla szomszédsága (`0x00cd8f14` … `0x00cd8f50`):

```
'Personal'  ·  'Local AppData'  ·  'Common AppData'  ·  '$UNC%s%s%s'  ·  '[%c]%s%s%s'
```

Ezek a Windows **registry „Shell Folders"** nevei — a **feloldás belső
oldala**. A `.cxf` ezzel szemben a **`WinSystemPaths` megjelenítési
neveit** használja (`My Pictures`), amit a `0x00994a60` tábla ad.

➡️ **A `.cxf` dekódolásához a `WinSystemPaths` a helyes tábla.** Ha
valaha `$Personal\…` alak kerül elő, az ÚJ információ.

### 15.4 A háttérkép MINDIG a kollázs saját képeinek egyike

Négy képhátteres, Picasával készült minta:

| fájl | háttér | a csomópontok között |
|---|---|---|
| AI2.cxf | `$My Pictures\AI\2a655925-….png` | **igen, index 0** |
| AI5.cxf | `$My Pictures\AI\2a655925-….png` | **igen, index 0** |
| AI8.cxf | `$My Pictures\AI\38ae21c1-….png` | **igen, index 8** |
| lake.cxf | `$My Pictures\lake\262_size_….jpg` | **igen, index 0** |

**4/4.** Ez megerősíti a #1009 alapfeltevését (a képháttér a kollázs
saját képe), és azt is, hogy az **indexes** visszaállítás a helyes
modell.

⚠️ **Következmény a feloldásra:** a háttér `src`-jének **ugyanazon a
leképezésen** kell átmennie, mint a csomópontokénak — különben a
`_node_index_of_path` sosem talál egyezést, és a háttér **némán színre
esik**. Ugyanaz a hibaosztály, mint a #1103 (ott a sorrend, itt a
kódolás miatt nem találna).

### 15.5 A Többszörös exponálásnak IS vannak csomópontjai (#1248)

Kézenfekvő feltevés, hogy a `multiexp` — mivel nem *helyez el* képeket —
csomópont nélküli `.cxf`-et ír. **A mérés cáfolja.**

`referencia/kollazs-golden/AI7.cxf` (valódi Picasa-minta, `theme="multiexp"`):

```xml
<node x="0.000000" y="0.000000" w="1.000000" h="1.000000" theta="0.000000" scale="1.000000">
 <theme>noborder</theme>
 <src>$My Pictures\AI\10e4bb2c-….png</src>
 <uid>cc58d08b44001ed30000000000000000</uid>
</node>
```

**Képenként egy csomópont, mind azonos: a TELJES lap, forgatás és keret
nélkül.** A geometria tényleg nem hordoz információt — a `src` viszont
igen, és nélküle a fájl nem tudja, miből készült.

⚠️ A `scale` itt **1,0**, nem a doboz nagyobbik oldala lapegységben. Ez
nem kozmetika: a #1071 mérte ki, hogy a nem szabványos `scale` a VALÓDI
Picasát viszi szét szerkesztéskor (óriási, felnagyított töredékek).

**Mibe került a hiánya:** a tulajdonos gépén (v0.8.45) a többszörös
exponálású kollázs újraszerkesztéskor **fekete lapot** adott, mentéskor
pedig azt jelentette, hogy „az összes képet eltávolították" (#1248). A
jegy UNC-útvonalra gyanakodott; a beküldött `AI15.cxf` ezt **kizárta** —
a háttér `src`-je szabályos `$My Pictures\…`, tehát a kódolás rendben
volt, csak `<node>` nem volt a fájlban.

⚠️ **A már mentett, csomópont nélküli `.cxf`-ek nem állíthatók helyre** —
nincs bennük semmi, amiből a forrásképek kiderülnének.

---

## 16. A kilenc kérdés — a NÉGY hiányzó darab (2026-08-21)

A kollázs négy spec-lapja (3532 sor) a felületet, az életciklust, a
`.cxf`-et és a kimenetet lefedi. A `picasapy-research` 2/b kilenc
kérdésén végigmenve **négy dolog derült ki, ami egyik lapon sem
szerepelt.**

**Leltár:** a binárisban **112 függvény** hivatkozik kollázs-sztringre. Ez
a szakasz ebből hetet nyit meg (`0x0088a020`, `0x0088a340`, `0x0088b220`,
`0x00889f40`, `0x0083ce90`, `0x007f7120`, `0x00415790`); a többi a korábbi
körökből ismert vagy továbbra sem vizsgált (ld. `kollazs-atvilagitas.md`
9. szakasz).

### 16.1 A folyamat NÉGY állapota — és a kész értesítés KATTINTHATÓ

| állapot | kulcs | angol | magyar | cím |
|---|---|---|---|---|
| indulás | `collage::initializing` | Creating Collage...initializing | Kollázs létrehozása… inicializálás | `0x0088b220` |
| haladás | `collage::refining_format` | Creating Collage - %d%% | Kollázs létrehozása - %d%% | `0x0088a340` |
| megszakítás | `collage::cancelling` | Creating Collage...cancelling | Kollázs létrehozása… leállítás | `0x00889f40` |
| **kész** | **`collage::done`** | **Collage Finished! (click to view)** | **A kollázs kész (kattintson ide)** | **`0x0088a020`** |

> ⭐ **A befejezés egy KATTINTHATÓ értesítés** — „(click to view)" /
> „(kattintson ide)". A hívási lánc `0x0088b220` → `0x0088a020`, tehát az
> „inicializálás" állapotot kezelő rutin indítja a „kész" üzenetet is.
> **Ez a lebegő értesítősáv** (`picasa-lebego-ertesito.md`) egyik valódi
> eseménye — az a lap eddig nem tudott konkrét eseményt megnevezni.
>
> **Nálunk a kollázs elkészülte után nincs kattintható értesítés**, csak a
> `locateSavedCollage()` navigáció (`Main.qml`).

### 16.2 KÉT figyelmeztetés, ami egyik lapon sem volt (`0x0083ce90`)

**a) „Mentés mellőzve"** — `collageUI::noimages_title` / `collageUI::noimages`

> **A kollázs nem menthető, mert az összes képet eltávolították. Vegyen
> fel legalább egy képet, és próbálkozzon újra.**

Ez a **piszkozat-mentés** ága: ha a felhasználó minden klipet kivett, a
mentés **csendben elmarad**, és ez a doboz szól róla. *(A hívó a
`0x0082d570`, a panel fő szétosztója.)*

**b) „Figyelmeztetés: eltérő formátumok"** — `collage::formatmismatch`

> **A kollázs jelenlegi oldalformátuma nem egyezik az asztal aktuális
> méretével.** Emiatt az asztal háttérképe nem várt módon jelenhet meg.
>
> (TIPP: Az Oldalformátum legördülő menüben a **„Jelenlegi megjelenítés"**
> elemet választva biztosíthatja a tökéletes illeszkedést.)
>
> Biztosan folytatja a műveletet?

Gombok: **„Beállítás ennek ellenére"** (`collage::formatwarningyesbutton`)
és **„Beállítás mellőzése"** (`collage::formatwarningnobutton`).

Ez az **„Asztali háttérkép"** kimeneti ág védelme: ha az oldalformátum nem
egyezik a képernyőmérettel, a Picasa **rákérdez, és javaslatot is tesz**
(a formátumlista „Jelenlegi megjelenítés" tétele).

### 16.3 A várakozó állapot — `CThumbUI::CreateCollageWait`

> **Várakozás a kollázs elkészítésére…** (`0x007f7120`, hívja `0x007f7b50`)

Külön állapot a **főablakban** (a `CThumbUI`-ban), nem a kollázspanelban —
tehát a kollázs indítása után a **könyvtárnézet** is jelez.

### 16.4 A `hascollage` — a kollázs NYOMOT HAGY A FORRÁSKÉPEKEN

A PMP-adatbázis oszloplistáját a `0x00415790` (7851 bájt) tartalmazza,
és köztük van a **`hascollage`** oszlop — a `token`, `filename`,
`category`, `description`, `location`, `inisync`,
`albumcontactids`, `albumpeoplechecksum` társaságában.

**Élő adat** (`research/testdata/Picasa2/db3/`):

| fájl | típus | sorok | méret |
|---|---|---:|---:|
| `albumdata_filename.pmp` | `0x0000` (sztring) | 2371 | 169 472 |
| `albumdata_token.pmp` | `0x0000` | 2371 | 93 958 |
| **`albumdata_hascollage.pmp`** | **`0x0003`** | **2370** | **2390** |
| `albumdata_inisync.pmp` | `0x0004` | 2371 | 18 988 |

- A `hascollage` **1 bájt/sor** (2390 = 20 bájtos fejléc + 2370) —
  logikai oszlop, típuskód **`0x0003`**.
- Ebben a mintában **mind a 2370 érték nulla** (ez a felhasználó nem
  készített kollázst), tehát **a `hascollage` = 1 esetre nincs mintánk**.
- ⚠️ **A PMP-oszlopok NEM egyforma hosszúak**: a fotótábla 2371 soros, a
  `hascollage` 2370 — a hiányzó vég alapértelmezett. Ezt a
  `pmp-database.md` eddig nem mondta ki; egy szigorúan egyenlő hosszt
  feltételező parszer **elhasal** valódi adaton.

> **Amit ez a PicasaPy-nak jelent:** a kollázs nem csak kimeneti fájlt ír,
> hanem **megjelöli a forrásképeket** is az indexben. Nálunk ilyen mező
> nincs. A #1033 („egy projekt-mappa két gyűjteményben is látszik") és a
> #1131 (gyári projekt-mappák) szempontjából ez a jelölés az, amiből az
> eredeti tudja, mely képek szerepelnek kollázsban.

*Bizonyítottsági fok: **megerősített** a négy folyamatállapotra, a két
figyelmeztetésre (szó szerinti szöveg + kulcs + cím), a várakozó
állapotra, és a `hascollage` oszlop létére, típusára és
sorhosszára (valódi adat) · **nincs mintánk** `hascollage = 1` értékre,
és **nem követtük végig**, mikor írja a program.


### 16.5 Mi valósult meg belőle (#1168, 2026-08-24)

A fenti négy lelet átvezetése után az „Eredeti / nálunk" tábla több sora
elavult. A pontos mai állapot:

| lelet | mai állapot a PicasaPy-ban |
|---|---|
| négy folyamatállapot, %-os haladás | **már megvolt** (#949) — a szövegek és a magyar honosítás is |
| a kész értesítés KATTINTHATÓ | a `CollageDoneNotice` megvolt (#1028), de **bekötetlen** volt; a #1168 bekötötte az **„Asztali háttérkép"** ágra (`collageDesktopBackgroundReady`) |
| a RENDES létrehozás utáni értesítés | **szándékosan nincs** — #1119: a `collage::done` a háttérkép-ághoz tartozik, a tulajdonos háromszor jelezte |
| „Mentés mellőzve" a végleges mentésnél | **már megvolt** (#949) |
| „Mentés mellőzve" a PISZKOZAT ágán | **új** (#1168): a `saveCollageDraft()` eddig némán tért vissza; most `collageNoImages`, és a lap NYITVA marad |
| formátum-figyelmeztetés két gombbal + tipp | **már megvolt** (#949); a #1168 a hivatalos magyar szövegre cserélte, a hiányzó **záró kérdéssel** együtt |
| várakozás a főablakban | **új** (#1168): `collageRendering` property + az alsó infó-sáv felirata |
| `hascollage` | **nem képjelölés** — ld. `pmp-database.md` K6: album-szintű, a `PicasaCollage.cxf` LÉTEZÉSÉBŐL származtatva. Nálunk `index/album_collage.py`, séma-oszlop NÉLKÜL |
| a PMP-parszer tűri a rövidebb oszlopot | **már megvolt** (`table.py` kipótol); a #1168 az élő alakra (2371 vs 2370) írt őrt |

**Nyitva marad:** a lebegő értesítősáv (#1129) — a kész-értesítés ma egy
saját, a főablak aljára horgonyzott doboz, nem a sáv eleme; és a
`hascollage`-nak nincs hívója, amíg a #1033/#1131 nem kéri.

## 17. A `.cxf` `scale` mezője témánként — hat téma átmérve (2026-09-01)

*A #1412 kérdése: az Indexkép (`contactsheet`) `scale`-je lap-szintű
állandó (313), a levezetése ismeretlen. Ez a szakasz a **mérést** rögzíti
mind a hat témára — a levezetés továbbra sem teljes, és ez ki is van
mondva.*

### 17.1 A mérés: `scale / (w × 1024)` minden csomópontra

| téma | minta | arány | konstans? |
|---|---|---|---|
| **`regulargrid`** | AI5 | **1,00000** (9/9) | **IGEN** |
| **`picturepile`** | AI1 | **1,25000** (hat különböző méreten) | **IGEN** |
| `picturegrid` | AI3 | 0,97510 … 0,98791 | nem |
| `framegrid` | AI4 | 0,82682 · 0,89007 · 0,91146 | nem |
| **`contactsheet`** | AI6 | 1,29339 **és** 2,01936 | **nem — node-független** |
| `multiexp` | AI7 | `scale=1` | — (jelző, nem méret) |

### 17.2 ⭐ A `scale` a RAJZOLT méret, nem a befoglaló dobozé

Az AI1-ben (`picturepile`) egy csomópont **188,87** széles, mégis
`scale=337` — ugyanaz, mint a **269,60** széleseké (arány 1,78431 a
konstans 1,25000 helyett). Ez **álló** kép a kupacban: azonos `scale`,
keskenyebb befoglaló doboz.

⇒ **A `scale` a kép rajzolt mérete**, a `w`/`h` a **befoglaló doboz** —
és forgatott/álló képnél a kettő szétválik. Ez magyarázza, miért nem
lehet a `contactsheet` `scale`-jét a doboz-méretekből kihozni.

### 17.3 A `.cxf` a lap SZÉLESSÉGÉT osztja 1024 egységre

Mérve (AI5 és AI6 minden mennyiségén): a **vízszintes** törtek × 1024
kivétel nélkül **egész** számot adnak (doboz-szélességek 242 · 155 · 330,
oszlop-osztások 300 · 339), a **függőlegesek** egyike sem.

⇒ A vízszintes mennyiségek egész egységben tárolódnak; a függőlegesek a
lap magasságához viszonyított törtek.

### 17.4 Ami a `contactsheet`-ből MEGMARAD nyitva

A **313** node-független, tehát a témából vagy a lapból jön. A mérés
ennyire szűkíti:

- **függőleges** hossz a fenti egységben (a vízszintesek mind egészek, ez nem az);
- a mért kép-magasság (**302,6**) és a sor-osztás (**359,1**) **közé** esik;
- **nem beégetett konstans**: a teljes `.text` bájtmintás átvizsgálása a
  `313` immediate négy alakjára (`push`/`mov eax|ecx|edx`) **nulla**
  találatot ad ⇒ **számított** érték.

**Feltevés — NEM mérés:** a `contactsheet` cellája feliratot is tartalmaz
(ez a téma lényege), tehát a 313 a **kép + felirat** együttes magassága
lehet; a különbség ekkor ≈ 10,4 egység. A `.cxf` ezt nem tartalmazza.

✅ **2026-09-05 — az ÍRÓ megvan, és nem alakít át semmit.** A `.cxf`
`scale` attribútumát a `FUN_008347b0` írja: `0x00835096` (`"scale"`) →
`0x008350b2` `fld dword ptr [edx+ecx+0x2c]` → `%f` (`0x00c817c0`). ⇒ a
fájlban álló szám **pontosan** a csomópont `+0x2c` mezője a mentéskor;
a hat tizedes (`scale="337.000000"`) ezt a mintáinkon is igazolja.
**Ez nem vezeti le a 313-at**, de kizárja, hogy az írás közben történne
átszámítás — a kérdés tisztán az, mi írja felül a layout `1,0`-ját.
*(Részletek: `picasa-create-features.md`, „A MEZŐ AZONOSSÁGA az ÍRÓ
oldaláról is megerősítve".)*

### 17.5 ⭐ A `scale` EGÉSZ SZÁMRA KVANTÁLT — 95/97 (2026-09-05, #1412)

A tizenkét arany `.cxf` **97** `scale` értékéből **95 pontosan egész**. A
kivétel **kettő**, mindkettő az `AI2.cxf`-ben: `267,607788` és `295,392395`.

Ráadásul a `picturepile` hat értéke — **238 · 249 · 263 · 280 · 303 · 337** —
**betű szerint ugyanaz** hat független kollázsban (`AI1`, `AI2`, `AI8`, `AI9`,
`AI10`, `AI`, `lake-allo-piszkozat`), más képekkel és más elrendezéssel.

⇒ **A `scale` előállítója egész értéket ad**, és a kollázs mérete egy
**diszkrét létrán** mozog. A két tört érték az `AI2`-ben a létrán kívül esik ⇒
**a kézi átméretezés megkerüli a létrát** — ez az egyetlen minta, amelyben a
tulajdonos csomópontot húzott át.

*(Bizonyítottsági fok: **megerősített** — puszta számolás a mintákon.)*

### 17.6 ⭐ Az AI6 vízszintes rácsa PONTOS EGÉSZEKBŐL áll

| mennyiség | érték (1024-es egység) |
|---|---|
| bal margó (`x` az 1. oszlopban) | **90,000** |
| oszlop-osztás | **300,000** (90 · 390 · 690) |
| cella-szélesség (`w`) | **242,000** |
| a keskeny kép `w`-je | **155,000** |
| a keskeny kép `x`-e | **733,000** = 690 + **43** |

A keskeny kép **vízszintesen KÖZÉPRE** kerül a 242-es cellában:
`(242 − 155) / 2 = 43,5` → **43** (lefelé kerekítve). Függőlegesen viszont
**nem** középre: mind a három első sorbeli csomópont `y`-a azonos
(**227,055**), a magasságok eltérnek (302,574 és 276,636) ⇒ **felülre
igazítva**. A sor-osztás **359,088**.

*(Bizonyítottsági fok: **megerősített** — az `AI6.cxf` mind a kilenc
csomópontján kiszámolva.)*

### 17.7 ⛔ MEGDŐLT: „a 313-at a kollázs-sáv egyik mutatós írója adja"

A 2026-09-02-i kör azt a következtetést hagyta hátra, hogy a végleges
`scale`-t a kollázs-sáv **37 mutatós `+0x2c`-írója** közül valamelyik adja.
**Ez nem igaz**, és a pásztázás számai sem álltak meg.

**A hiba oka:** a `+0x2c` eltolású írások túlnyomó többsége
**`[esp + 0x2c]` lokális változó**, nem struktúramező. A helyes szűrő a
ModRM/SIB alakra néz: SIB-nél a `base == 100b` (esp), mutatós alaknál az
`rm ∈ {100b, 101b}` (SIB, illetve `disp32`) esetet **ki kell hagyni**.

Ezzel újramérve, a kollázs-sávban (`0x820000`–`0x896000`) **47** valódi
`+0x2c`-író van, és közülük **float**-ot csak ez a hat ír:

| cím | mit csinál |
|---|---|
| `0x00822230` (3 írás) | hat egymást követő float (`+0x18`…`+0x2c`) skálázása — **nem a csomópont**, egy általános geometria-segéd (hívói: `0x0081fc30`, `0x00823620`) |
| `0x00823620` (`0x00823dd3`) | ugyanaz a modul (`AlignedImageCollection` ág, `0x00699cd0`) |
| `0x008341b0` (`0x00834264`) | a **csomópont `operator=`** — másol (a teljes 56 bájtos mezőlista végigolvasva) |
| `0x0087b830` (`0x0087b898`) | csomópontok közti másolás |
| `0x00885060` (`0x0088522d`) | a **`regulargrid` elrendezője** — `fld1` ⇒ **1,0** |
| `0x00888210` (`0x008885bc`) | a **`contactsheet` elrendezője** — `fld1` ⇒ **1,0** |

⇒ **A kollázs-sávban a csomópont `scale`-jét CSAK a két elrendező (mindkettő
állandó 1,0) és a másolók írják.** Egyetlen olyan hely sincs, ami 313-at vagy
330-at számolna.

### 17.8 ⭐ A HARMADIK író: a `.cxf` BEOLVASÓJA — közvetlenül a csomópontba

A `0x00832830`-as elemző az attribútumokat `atof`-fal (`0x00c080d7`) olvassa,
és **közvetlenül** a csomópont mezőibe teszi:

```
0x00833240  fstp dword ptr [ebx + 0x64]   ; theta
0x008332b7  fstp dword ptr [ebx + 0x68]   ; scale
```

A `0x64 − 0x28 = 0x68 − 0x2c = 0x3c` ⇒ az `ebx` egy **burkoló**, amelyben a
csomópont a **`+0x3c`**-nél kezdődik. Ugyanezt a `+0x68` eltolást a
kollázs-sávban rajta kívül **senki nem írja** float-tal (kimerítő pásztázás).

⇒ **A `scale` három forrása a sávban: a két elrendező (1,0), a beolvasó (a
fájl saját értéke), és a másolók.** Semmi más.

### 17.9 ⛳ POZITÍV KONTROLL: a `multiexp` 1,0-ja végigmegy

Az `AI7.cxf` (`multiexp`) `scale="1.000000"` — **pontosan az elrendező
`fld1`-je**. Tehát az „elrendező → fájl" út egy témán **végig igazolt**, és a
mezőazonosság sem kérdéses. A többi témánál viszont valami **felülírja** —
és az a valami a mérés szerint **nincs a kollázs-sávban**.

### 17.10 A KÖVETKEZŐ lépés (a korábbi helyett)

1. **A sávon KÍVÜL kell keresni** az írót — a fenti szűrővel, az egész
   `.text`-en, a csomópont-alakra (`+0x28` és `+0x2c` float egy függvényben).
2. **Vagy mutatón át ír**: a sávban **10** `lea r, [r+0x2c]` hely van
   (`0x00823c21`, `0x008300dc`, `0x0083198a`, `0x00834af3`, `0x00860032`,
   `0x00879909`, `0x00879b7b`, `0x00879d18`, `0x0087e0cd`, `0x008831c8`,
   `0x0088ab66`) — eltolás-alapú pásztázás ezeket **nem látja**.
3. A fekvő `contactsheet`-minta továbbra is **független** ellenőrzés lenne,
   de a kérdést már nem ez dönti el elsőként.

**Mi döntené el (kiegészítve 2026-09-05):** elsősorban a 17.10 két gépi
lépése; a **fekvő** tájolású `contactsheet`-minta (a meglévő AI6 álló)
független megerősítés maradna. → **#1412** (`ready` + `bináris-kutatható`).

*Bizonyítottsági fok: **megerősített** a hat téma aránytáblája, a
`scale` = rajzolt méret értelmezés és az 1024-es egységrendszer;
**feltételes** a felirat-magyarázat; **elvetve** a „beégetett konstans"
hipotézis.*
