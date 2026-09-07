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

### 17.10 ⭐ A SÁVON KÍVÜLI keresés LEFUTOTT — negatív (2026-09-06)

Az előző kör két utat nevezett meg. Mindkettő megjárva:

**a) Csomópont-alakú float-írók az EGÉSZ binárisban.** A szűrő: egy
függvény, amely a `+0x2c`-t float-tal írja, **és** a `+0x28`-at is, **és**
legalább három mezőt a `+0x18`…`+0x2c` sávból (esp/ebp-relatív alakok
kizárva). **16 találat**, ebből 6 a kollázs-sávban, **10 a sávon kívül**:
`0x0050bd70`, `0x0050be50`, `0x0050cdb0`, `0x0050d560`, `0x005c2350`,
`0x007e68f0`, `0x007e6930`, `0x007e69b0`, `0x00819f50`, `0x009d7a60`.

A tízből **egyet olvastam végig utasításonként** — a `0x00819f50`-et, mert
egyedül ezt hívja a kollázs-sávból egy függvény (`0x00873cb0`), tehát ez volt
az egyetlen valódi jelölt. Ez **nem a csomópont**, hanem **három (x, y) pont**:

```
0x00819f75  fld [eax+0x18] ; fmul [ecx]     ; ×sx
0x00819f7d  fld [eax+0x1c] ; fmul [ecx+4]   ; ×sy
0x00819f86  fld [eax+0x20] ; fmul [ecx]     ; ×sx
0x00819f8e  fld [eax+0x24] ; fmul [ecx+4]   ; ×sy
0x00819f97  fld [eax+0x28] ; fmul [ecx]     ; ×sx
0x00819f9f  fld [eax+0x2c] ; fmul [ecx+4]   ; ×sy
```

⇒ **három (x, y) pont**, nem `theta`+`scale`: a `+0x18`/`+0x20`/`+0x28`
`sx`-szel, a `+0x1c`/`+0x24`/`+0x2c` `sy`-nal szorzódik. A csomópontnál a
`+0x28` **szög**, amit `sy`-nal szorozni értelmetlen. Ugyanez az alak a
kollázs-sávbeli `0x00822230`-on is (`0x008222c0`–`0x008223ca`).

⚠️ **A hatókör kimondva:** a maradék kilenc sávon kívüli találatot
**nem** olvastam végig; egyiket sem hívja a kollázs-sáv **közvetlenül** (`xrefs`), ezért
kerültek ki a jelöltek közül — ez **kizárás hívási úton**, nem tartalmi.
Háromnak (`0x0050be50`, `0x0050cdb0`, `0x0050d560`) **egyáltalán nincs**
közvetlen hívója, tehát csak virtuális úton érhetők el: rájuk a kizárás
**gyengébb**.

**b) A burkoló `+0x68`-as rése az EGÉSZ binárisban.** Float-írás a
`+0x68`-ra (mutatós alak, esp/ebp nélkül): **öt** függvény az egész
programban — `0x004147d0`, `0x0066f470`, `0x007fb9f0`, `0x0082fab0`,
`0x00832830`. A kollázs-sávban **csak a beolvasó** (`0x00832830`); a
`0x0082fab0` **bájtminta-találat utasításhatáron belül** (a `0x0082fb72`
egy `push ebx` + `push 0x9dd5` közepe), tehát nem író.

⇒ **A sávon kívül sincs a `scale`-nek számoló írója.**

### 17.11 ⛔ HELYESBÍTÉS: az író csomópont-tömbje a MÁSODIK argumentum

A lap eddig úgy hivatkozott a `.cxf`-író olvasására, hogy `edx` a
csomópont-tömb bázisa — de nem mondta ki, **melyik** argumentumból. A
veremeltolás kiszámolva:

- `FUN_008347b0` bemenete: `sub esp, 0xc` · `push ebx` ⇒ `ebx = [esp+0x14]`
  = **1. argumentum**; `push ebp` ⇒ `ebp = [esp+0x1c]` = **2. argumentum**.
- A `0x00835096`-os `push` utáni `call 0x00985ff0` **`ret 4`**-gyel zár
  (`0x0098601d`), tehát a **hívott takarít** ⇒ a `0x008350ae`-nél
  `[esp+0x24]` = **2. argumentum** (`ebp`), nem az első.

⇒ `scale = tömb[ csomópont_bájteltolás + 0x2c ]`, ahol a **tömb a 2.
argumentum**, a bájteltolás pedig `[ebx+0x48]` — amit az író **tízszer
olvas és egyszer sem ír** (`0x00834c2d`, `0x00834d1f`, `0x00834e02`,
`0x00834ee5`, `0x00834fc8`, `0x008350ab`, `0x00835192`, `0x008351f5`,
`0x0083521e`, `0x00835296`): **a hívó állítja csomópontonként**
(`0x00834777`: `push ecx` · `push edx` · `call`).

### 17.12 ⭐ A BEOLVASÓ OBJEKTUMA NEM TÖMBELEM — itt a hiányzó láncszem

A beolvasó a `theta`-t `[ebx+0x64]`-be, a `scale`-t `[ebx+0x68]`-ba teszi;
a tömbelemben viszont ugyanez a `+0x28` és a `+0x2c`. A kettő **nem
ugyanaz az objektum** — a beolvasó egy **burkolóba** ír, és onnan valami
átviszi a tömbbe.

**Ez az átvitel az egyetlen hely, ahol a `scale` a modellbe kerülhet, és
még nincs azonosítva.** A dokumentum-objektum konstruktora
`FUN_00832500` (103 b, a `CCollageParser::vftable` = `0x00cbf878`
beírásával, `0x00832524`); ez adja a `+0x3c = 2`-t (a `version="2"`),
a `+0x48 = 0`-t és a `+0x54`/`+0x58`/`+0x5c`/`+0x60` nullákat.

**A következő lépés (konkrétan):** a `+0x64`/`+0x68` **olvasói** — azok
adják át a tömbnek. Ugyanaz a szűrő, mint fent, csak `fld` iránnyal.

### 17.13 ⭐ A LÁNC ÖSSZEÁLLT — és ezzel a `scale` KÉT lehetséges forrása marad

Az előző szakasz „hiányzó láncszemét" ugyanez a kör megtalálta. A
`+0x64`/`+0x68` **olvasói**: az egész binárisban a `fld dword [reg+0x68]`
alakra **két** függvény van, a `+0x64`-re **öt**; a kollázs-sávban
**mindkettőre pontosan egy és ugyanaz**: **`FUN_00833920`** (911 b) —
`0x008339aa` (`fld [ebx+0x64]` → `[esp+0x40]`) és `0x008339b7`
(`fld [ebx+0x68]` → `[esp+0x44]`).

**Ez a csomópont-tömb `push_back`-je:**

| lépés | cím | mit tesz |
|---|---|---|
| kapacitás-növelés | `0x00833a92` (`mul 0x38`) → `0x00833aad` (`operator new`) | **56 bájtos** elemek |
| a régi elemek átmásolása | `0x00833af0`–`0x00833b09` (`call 0x008341b0`, lépés `add edi, 0x38`) | a csomópont `operator=`-ével |
| **az új elem feltöltése** | `0x00833b3c`–`0x00833b54`: `[ebx+4] >> 1` = darabszám, `lea eax,[edx + ecx*8]` (= `adat + darab × 56`), majd `call 0x008341b0` egy **helyi** csomópontból | a `+0x64`/`+0x68`-ból staged `theta`/`scale`-lel |

⇒ **A teljes lánc:** `.cxf` szöveg → a beolvasó a gyűjtemény-objektum
**staging-mezőibe** ír (`+0x64` = `theta`, `+0x68` = `scale`) → a
`push_back` (`FUN_00833920`) ezekből épít egy helyi csomópontot, és a tömb
végére másolja (`+0x28`/`+0x2c`) → innen olvassa a `.cxf`-író.

### 17.14 ⛔ Amit ez KIMOND — és mi nem áll össze

A pásztázások együtt (17.7, 17.8, 17.10, 17.13) ezt adják: a `Picasa3.exe`-ben
a csomópont `scale`-je **csak két helyről** kaphat értéket —

1. a **téma-elrendezőktől**, és ott **állandó `1,0`**
   (`0x0088522d`, `0x008885bc`, mindkettő `fld1`);
2. a **beolvasótól**, azaz a **fájl saját értékéből** (a staging-mezőn át).

**Számoló írót egyik pásztázás sem talált.**

⚠️ **És itt egy ELLENTMONDÁS marad, amit ki kell mondani:** a mintáinkban
`313` és `330` áll, nem `1,0`. Vagyis vagy

- **(a)** a `.cxf`-jeink értéke egy korábbi fájlból származik, és a
  szerkesztő csak visszaírta *(ekkor egy FRISSEN létrehozott kollázs
  `scale`-je `1.000000` volna)*, vagy
- **(b)** van egy író, amit az eltolás-alapú pásztázás **nem lát** — például
  **mutatón** át (`lea r,[r+0x2c]`, 10 hely a sávban, 17.10/2.), vagy egy
  olyan tömb-báziscímen, amit nem ismerünk fel.

**A döntő, OLCSÓ mérés: egy ÚJONNAN létrehozott kollázs `.cxf`-je.** Ha ott
`scale="1.000000"` áll, az **(a)** igazolt, és a 313 kérdése átfordul arra,
hogy melyik korábbi program írta. Ha nem 1,0, akkor **(b)**, és a mutatós
utat kell végigvinni.

> **Bizonyítottság:** **megerősített** a lánc minden lépése (címekkel) és a
> két forrás; **kimondottan nyitott** az ellentmondás feloldása.

**Mi döntené el (kiegészítve 2026-09-05):** elsősorban a 17.10 két gépi
lépése; a **fekvő** tájolású `contactsheet`-minta (a meglévő AI6 álló)
független megerősítés maradna. → **#1412** (`ready` + `bináris-kutatható`).

*Bizonyítottsági fok: **megerősített** a hat téma aránytáblája, a
`scale` = rajzolt méret értelmezés és az 1024-es egységrendszer;
**feltételes** a felirat-magyarázat; **elvetve** a „beégetett konstans"
hipotézis.*

### 17.15 ⭐ A (b) ág NAGY RÉSZE LEZÁRVA — a pásztázóink VAKFOLTJA mérve (2026-09-07)

A 17.14 két lehetőséget hagyott: **(a)** a `scale` a fájlból öröklődik,
**(b)** van egy író, amit az eddigi szűrők nem látnak. Ez a kör a **(b)**
ág egy konkrét, addig ki nem mondott vakfoltját mérte ki és zárta le.

#### A vakfolt: float ÉRTÉK `mov`-val is tárolható

A 17.7 szűrője **csak `fstp`/`fst`** utasításra nézett, és ebből vonta le,
hogy „float-ot csak ez a hat ír". Ez a szűrő **hiányos**: az MSVC a
float-ot rendszeresen egész regiszteren át teszi a helyére —

```
0x00885205  fstp dword ptr [esp+0x38]      ; float a verembe
0x00885209  mov  ecx, dword ptr [esp+0x38] ; egész regiszterbe
0x0088520f  mov  dword ptr [eax+esi+0x18], ecx   ; ÍRÁS mov-val
```

⚠️ **A bizonyíték magában a 17.7 által idézett `FUN_00885060`-ban van:**
ez a függvény az `x`/`y`/`w`/`h`-t végig **`mov`**-val írja, és csak a
`scale`-t `fstp`-vel. Egy `fstp`-re szűrő pásztázó tehát ugyanennek a
függvénynek a négy mezőjét sem látta volna.

#### Pásztázás 1 — TÖMB-alakú (`bázis+index+0x2c`) írás, TELJES bináris

Minden alakot beleértve (`mov` és `fstp`), `esp`/`ebp` bázis kizárva.
**Pozitív kontroll:** a `FUN_00885060` `mov [eax+esi+0x18], ecx` írása
(`0x0088520f`) a találatok közt — megvan.

**Az egész programban 8 ilyen írás van:**

| cím | függvény | alak | mi ez |
|---|---|---|---|
| `0x0088522d` | `FUN_00885060` | `fstp` | **`regulargrid` elrendező — `fld1` ⇒ 1,0** |
| `0x008885bc` | `FUN_00888210` | `fstp` | **`contactsheet` elrendező — `fld1` ⇒ 1,0** |
| `0x009007e6` | `FUN_00900540` | `fstp` | ⛔ szűrő-csúszka felülete (`filter_%s_label%d`, `_sldrRadius`) |
| `0x006f464c` | `FUN_006f4210` | `mov` | ⛔ bázisa `[ebx+0xa8]`, nincs 56-os lépés |
| `0x00aab81e` | `FUN_00aab710` | `mov` | ⛔ állandó `0x2cc`-t ír, foglaló-rekesz |
| `0x00afcc23` | `FUN_00afcbc0` | `mov` | ⛔ lépésköz **0x30** (`add eax, 0x30`), nem 56 |
| `0x00afce3e` | `FUN_00afcd50` | `mov` | ⛔ `call 0xafc570`-en átvezetett érték, bázis `[ebx+8]` |
| `0x00c125e2` | `FUN_00c12477` | `mov` | ⛔ 56-os lépés (`imul esi,esi,0x38`), de a szomszédja (`+0x28`) egy `call 0xc165e0` fogantyúja — futásidejű tábla, nem csomópont |

⇒ **Tömb-alakban a csomópont `scale`-jét a két téma-elrendezőn kívül
senki nem írja az egész programban** — és mindkettő `fld1`.

#### Pásztázás 2 — MUTATÓS `mov [reg+0x2c], <float>` írás, TELJES `.text`

Az „float egész regiszteren át" idióma nyomon követve (`fstp [esp+N]` →
`mov r,[esp+N]` → `mov [obj+0x2c], r`). **Pozitív kontroll:** ugyanaz a
`0x0088520f` — megvan. **Kilenc találat, ebből négy a kollázs-sávban:**

| cím | eredmény |
|---|---|
| `0x00881b9a` (`FUN_00881900`) | ⛔ `[esi+0x2c]` **heap-mutató**: `test` → `push` → `call 0xc07738` (felszabadítás) → új mutató |
| `0x008824a0` (`FUN_00882100`) | ⛔ ugyanaz az idióma |
| `0x00889351`, `0x00889490` (`FUN_00888ec0`) | ⛔ ugyanaz az idióma, kétszer |
| `0x00892a58` (`FUN_008921a0`) | ⛔ `+0x10`-zel eltolt bázis (a 178. kör kikötése) ⇒ valójában `+0x3c` |

⇒ **A `mov`-os úton sincs float-író a csomópont `+0x2c`-jére.** A négy
kollázs-sávbeli találat mind ugyanaz a `free`-és-újraköt idióma, ahol a
`+0x2c` egy **tárolómutató**, nem méretarány.

#### Pásztázás 3 — a 313,0 mint LEBEGŐPONTOS literál, a TELJES fájlban

A 17.4 a **`313` egész immediate** négy alakját nézte a `.text`-ben. Ez a
kör a **lebegőpontos bitmintát** kereste a **teljes fájlban**:

| alak | bitminta | találat |
|---|---|---|
| `float32` 313,0 | `00 80 9c 43` | **0** |
| `double` 313,0 | `00 00 00 00 00 90 73 40` | **0** |

⇒ **A 313 semmilyen alakban nincs beégetve** — sem egészként (17.4), sem
lebegőpontosként (itt). A „konstans-tábla" hipotézis ezzel véglegesen
elvetve.

#### Pásztázás 4 — a `"scale"` sztring hivatkozói

A `string_xrefs` szerint a `0x00cbf80c` (`"scale"`) sztringre az **egész
programban pontosan két** függvény hivatkozik: a **beolvasó**
(`0x00832830`) és a **kiíró** (`0x008347b0`). Harmadik hely, amely ezt a
mezőt névvel kezelné, **nincs**.

#### Amit ez a négy pásztázás EGYÜTT jelent

A 17.14 **(b)** ága — „van egy nem látott író" — a **tömb-alakú** és a
**mutatós `mov`-os** utakon **lezárva, negatívval**. Ami a (b)-ből
megmarad: a 17.10/2. pontban megnevezett **`lea r,[r+0x2c]`** út (10 hely
a sávban), ahol a mutató máshova kerül és ott írják.

⇒ Az **(a)** ág — *a `scale` a fájlból öröklődik* — most az egyetlen olyan
magyarázat, amelyet a bináris nem cáfol. **A döntő mérés változatlanul
egy FRISSEN létrehozott kollázs `.cxf`-je** (#1412 kérése a tulajdonoshoz).

*Bizonyítottsági fok: **megerősített** mind a négy pásztázás (mindegyik
pozitív kontrollal, a kizárások tételesen, címmel); **nyitva** a
`lea`-alapú út.*

### 17.16 ⭐ A `.cxf` BEOLVASÓ TELJES mezőtérképe és ALAPÉRTELMEZÉSEI

A 17.8 a beolvasóból csak a `theta`-t és a `scale`-t nevezte meg. Az
elemző (`FUN_00832830`, 3555 b, `0x00832830`–`0x00833613`) teljes
attribútum→mező leképezése, utasításszinten kiolvasva:

**Dokumentum-szint**

| attribútum | tárolás | cím |
|---|---|---|
| `version` | `[edi]` (int) | `0x00832949` |
| `format` | négy egymást követő int (`+0`, `+4`, `+8`, `+0xc`) — a lap téglalapja | `0x00832a26`–`0x00832a2e` |
| `orientation="portrait"` | `[+0x20] = 1` | `0x00832af2` |
| `orientation="landscape"` | `[+0x20] = 0` | `0x00832b3f`, `0x00832b5b` |
| `albumID` | `[+0x30]` | `0x00832eb2` |
| `background type="image"` | `[+0x24] = 1` | `0x0083341b`, `0x0083342e` |
| `background color` | `[+0x28]`, **alapérték `0xFF000000`** | `0x008334bd` |
| `spacing value` | `[+0x40]` (float) | `0x008335f4` |

Névvel felismert, de itt nem tárolt attribútumok: `collage`, `theme`,
`shadows`, `captions`, `albumUID`, `node`, `type`, `color`, `value`.

**Csomópont-szint (a staging-burkolóban, `ebx`)**

| attribútum | mező | cím |
|---|---|---|
| `x` | `[ebx+0x54]` | `0x00833068`, `0x0083307b` |
| `y` | `[ebx+0x58]` | `0x008330de`, `0x008330f1` |
| `w` | `[ebx+0x5c]` | `0x00833154`, `0x00833167` |
| `h` | `[ebx+0x60]` | `0x008331ca`, `0x008331dd` |
| `theta` | `[ebx+0x64]` | `0x00833240`, `0x00833250` |
| `scale` | `[ebx+0x68]` | `0x008332b7` |

**⭐ Az ALAPÉRTELMEZÉSEK — a `0x00832f88`–`0x00832fc8` blokk**, amely
minden `<node>` elején lefut, MIELŐTT az attribútumokat feldolgozná:

| mező | alapérték | bizonyíték |
|---|---|---|
| `x`, `y`, `w`, `h` | a `0x00c7dafc`-en álló `float` | `0x00832f88 fld dword ptr [0xc7dafc]` |
| `theta` | **0,0** | `0x00832fa2 fldz` → `0x00832fba fstp [ebx+0x64]` |
| **`scale`** | **1,0** | `0x00832fbd `**`fld1`** → `0x00832fc2 fstp [ebx+0x68]` |

Ezt követi a `[ebx+0x40]`, `[ebx+0x44]`, `[ebx+0x48]` **nullázása**
(`0x00832fd0`, `0x00832fde`, `0x00832ff1`) — három mutató, azaz egy
tárolókonténer a burkolón belül.

⇒ **Ha egy `<node>`-ból hiányzik a `scale`, az érték `1,0`** — nem 0 és
nem öröklődik az előző csomópontból. Ugyanígy a `theta` alapértéke `0,0`.
Ez a PicasaPy `.cxf`-olvasójára **közvetlenül átvehető szabály**.

#### A csomópont-rekord mérete: **56 bájt (0x38)** — a kiíró oldaláról mérve

A `.cxf`-író az elem-eltolást így számolja (`0x00834c30`–`0x00834c3f`):
`lea eax,[ecx*8]` → `sub eax,ecx` (=7·ecx) → háromszor `add eax,eax`
(=56·ecx). Ugyanez `imul`-lal a `push_back`-ben (`0x00833a92`, `mul 0x38`
— 17.13). **Két független hely, ugyanaz a szám.**

#### ⚠️ Egy BELSŐ ELLENTMONDÁS a lapon, feloldatlanul

A **17.11** azt mondja, hogy a `[ebx+0x48]` a csomópont **bájteltolása**,
a tömb bázisa pedig a 2. argumentum. A `0x00834c2d`–`0x00834c3f` blokk
viszont egyetlen alapblokkon belül úgy néz ki, hogy `edx = [ebx+0x48]` a
**bázis** és `eax = i·56` az index (más bázistag nincs az utasításban).

**Nem döntöttem el**, mert a hozzá szükséges verem-egyenleg
(`0x00834c56` → `0x008350ae`) **elágazásokon át** vezet, és a lineáris
`esp`-összegzés ilyenkor **érvénytelen** (nálam −116-ot adott, ami
nyilvánvalóan rossz). **Amit el kell dönteni és mivel:** a `FUN_008347b0`
veremkerete egy **dekompilátoros** körrel (`picasa-x86-research`) —
a Ghidra útvonalérzékenyen adja meg, melyik lokális melyik.
Ez a K1 következő konkrét lépése a munkasorban.


### 17.15 ⛔ A DRÁGA ÚT VÉGIGJÁRVA — és a belőle vont NEGATÍV MEGDŐLT (2026-09-06, #1412)

*A jegy maga nevezte meg ezt az utat: „marad a mutatós írási utak
egyenkénti végigolvasása (tíz hely), ami sokkal drágább." Végigolvasva —
és közben egy **rés is kiderült a korábbi szűrőben**, azt is bezártuk.*

#### a) A kilenc sávon kívüli jelölt — mind ELOLVASVA, mind NEGATÍV

A 17.10/a tíz sávon kívüli találatából egyet olvasott végig az előző kör
(`0x00819f50`). A maradék **kilencet** most utasításonként:

| cím | méret | mit csinál | számol `scale`-t? |
|---|---:|---|---|
| `0x0050bd70` | 146 b | konstans **0,333** (`0xcf4030`) a `+0x1c`/`+0x20`/`+0x24`-be, **0** a `+0x28`/`+0x2c`/`+0x30`-ba | **nem** — inicializáló |
| `0x0050be50` | 31 b | ugyanaz, rövidebb alak | **nem** — inicializáló |
| `0x0050cdb0` | 147 b | **másoló**: `[esi+X] → [eax+X]` a `+0x1c`…`+0x30` mezőkre | **nem** — másolás |
| `0x0050d560` | 468 b | egész osztása **255,0**-val (`0xcf39d0`) a `+0x1c`/`+0x20`/`+0x24`-be, majd összehasonlítások; sztringje **`editslider1/editslider`** | **nem** — a szerkesztő csúszkája |
| `0x005c2350` | 72 b | `fld1` a `+0x14`-be, **0** a `+0x18`…`+0x34`-be | **nem** — egységmátrix-init |
| `0x007e68f0` | 64 b | **0** a `+0xc`…`+0x2c`-be | **nem** |
| `0x007e6930` | 70 b | ua. | **nem** |
| `0x007e69b0` | 99 b | **0**, és `fld1` a `+0x1c`-be | **nem** |
| `0x009d7a60` | 129 b | konstans **−1,0** (`0xcf3ed0`) a `+0x10`…`+0x2c`-be, 0 a `+0x30`/`+0x34`-be | **nem** |

⇒ **egyik sem számol**: mind konstans-inicializáló, másoló, vagy másik
alrendszeré. A 17.10 „kizárás hívási úton" megszorítása ezzel
**tartalmi kizárássá** erősödött — a három gyengébben kizárt tétel
(`0x0050be50`, `0x0050cdb0`, `0x0050d560`) is benne van.

#### b) ⛔ A KORÁBBI SZŰRŐ RÉSE — és a bezárása

A 17.10/a szűrője **megkövetelte a `+0x28` írását is** (a csomópont-alak
`theta`+`scale` párja). Ha viszont a valódi író **csak a `scale`-t** írja,
a `theta`-t nem, akkor **kiesett volna a mintából**. Ez a rés eddig
kimondatlan volt.

**Bezárva.** Új, `+0x28`-tól független pásztázás a `.text` teljes
szakaszán (fájloffset `4096`, `8646656` bájt): `fst`/`fstp dword ptr
[reg + 0x2c]` **mutatós** alakban (`mod=01`, SIB és `ebp`-lokálisok
kizárva) — **63 írási hely, 50 különböző függvényben**.

Ezek közül a **kollázs-sávban** lévők, amelyeket a korábbi körök még nem
soroltak be, mind elolvasva:

| cím | mit csinál |
|---|---|
| `0x00829770` (95 b) | **0** a `+0x28`…`+0x3c`-be — inicializáló |
| `0x00860f60` (178 b) | **0** a `+0x20`…`+0x30`-ba; sztringjei `Picasa`, `Arial` — **nyomtatás** |
| `0x00861190` (292 b) | **0** a `+0x1c`…`+0x2c`-be; sztringje `Preferences` / **`PrinterQuality`** — nyomtatás |
| `0x0088e7e0` (71 b) | konstans **−1,0** a `+0x20`…`+0x2c`-be — inicializáló |
| `0x008910b0` (86 b) | ua. |

⇒ **a `+0x28` követelménye nem rejtett el semmit**: a `+0x2c`-t mutatón
át író 50 függvény között sincs olyan, amelyik a kollázs-csomópont
`scale`-jét **számolná**.

⚠️ **A pásztázás hatóköre kimondva:** a **SIB**-alakú írások
(`[reg + reg*8 + 0x2c]`) ebből a mintából kimaradnak — épp így ír a két
téma-elrendező (`0x00885060` `regulargrid`, `0x00888210` `contactsheet`),
amelyeket a 17.13 már kimért: **mindkettő `fld1`, tehát állandó 1,0**.
A két minta uniója fedi le a csomópont-írás mindkét címzési alakját.

#### ⛔ ÖNHELYESBÍTÉS (2026-09-06, ugyanaznap): a NEGATÍV MEGDŐLT

**Ez a szakasz eredetileg azt állította, hogy „a `Picasa3.exe`-ben nincs
olyan kód, amely a kollázs-csomópont `scale`-jét kiszámolná",
`megerősített` bizonyítottsági fokkal. Ez az állítás TÉVES.**

A szakasz a saját cáfolatának feltételét is leírta: *„Ha egy új, sosem
mentett kollázs `.cxf`-jében minden csomópont `scale="1.000000"`, az az
öröklődés ágát igazolja."* A tulajdonos **ugyanaznap** megmérte, és a
feltétel **nem teljesült**.

**A mérés** (a tulajdonos gépe, 2026-09-05-i, korábban soha nem mentett
kollázsok — `#1412` komment, 2026-09-06 12:57 CEST):

| minta | első szám | `scale` |
|---|---:|---:|
| AI27 | 4 | **500** |
| AI28 | 6 | **256** |
| `AI6` (a jegy eredeti mintája) | 9 | **313** |
| AI29 | 12 | **158** |

⚠️ **Mit jelent az első szám?** A tulajdonos a párokat jelölés nélkül
adta meg (`4→500, 6→256, 9→313, 12→158`). A **9 → 313** esetén ez a
SAJÁT mérésünkből azonosítható: az `AI6.cxf`-nek **pontosan kilenc**
csomópontja van, mindegyik `scale="313"` (17.6). A másik három esetében
az olvasat abból következik, hogy a jegy kifejezetten **„más
képszámmal"** kért mintát — tehát erős, de **nem külön mérve**. A
képlet illesztése előtt a három `.cxf`-ben **meg kell számolni a
csomópontokat**.

⇒ **Van írási út, amely SZÁMOL.** A fenti két lehetőség közül tehát a
**(2)** áll: egy olyan írási út, amit **egyik pásztázásunk mintája sem
fedett** — a `memcpy`-vel másolt csomópont-blokk, vagy a mentés-szervező
(`0x00834700`) hívóláncának egy még el nem olvasott ága.

**Amit a négy pont önmagában kizár** (számítás, nem feltevés): a `scale`
**nem monoton csökkenő** az első számban — 6 → 256, de 9 → **313**.
Egy egyszerű, monoton `f(n)` alak ezzel megdőlt; a képlet legalább egy
további bemenettől függ. A legkézenfekvőbb jelöltek a **rács oszlop-/
sorszáma**, a **lapméret** és a **képarány** — mindhárom **NINCS MÉRVE**,
és képletet illeszteni négy pontra addig **tilos**, amíg a bemenetek
nincsenek kiolvasva a három `.cxf`-ből.

**Mi maradt érvényben ebből a szakaszból:** a kilenc jelölt olvasata
(a)-ban és a `+0x28`-tól független pásztázás (c)-ben **tényként áll** —
azok a függvények tényleg nem számolnak, és a 63 írási hely tényleg
azok, amiket a minta megtalált. **A hiba a KÖVETKEZTETÉSBEN volt:** a
minták uniójából „a programban nincs ilyen kód"-ra ugrottam, holott a
két minta csak a **közvetlen `fst`/`fstp` írásokat** fedi. A blokk-másolás
(`memcpy`, `rep movsd`) és a többi közvetett út **kívül esett a
hatókörön, és ezt nem mondtam ki**.

> ⛳ **A tanulság, kimondva:** a „kimerítő negatív pásztázás" akkor ér
> valamit, ha a hatóköre a MEZŐ minden írási módjára kiterjed, nem csak
> arra az utasításfajtára, amit kerestem. A negatívot ki szabad mondani —
> de a hatókört a *mezőre* kell szabni, nem a mintára. (Vö. a
> `binaris-regeszet-modszertan.md` negatív-pásztázási szakasza.)

#### Ami ezzel eldőlt — és ami NEM (a helyesbítés UTÁN)

#### Ami ezzel eldőlt — és ami NEM

~~**Eldőlt:** a `Picasa3.exe`-ben **nincs olyan kód, amely a kollázs-csomópont
`scale`-jét kiszámolná**.~~ **MEGDŐLT** — ld. az önhelyesbítést fentebb.

**Ami ténylegesen eldőlt:** a `scale`-t **nem a közvetlen `fst`/`fstp
dword ptr [reg+0x2c]` alakok** (sem mutatós, sem SIB) írják számított
értékkel — a 63 írási hely mindegyike konstans, másolás vagy nyomtatás
(17.7, 17.8, 17.10, 17.13 és ez a szakasz együtt). Bizonyítottsági fok:
**megerősített** — de **kizárólag erre a két címzési alakra**.

**NEM dőlt el:** melyik írási út számol, és mi a képlet. A két korábbi
lehetőség közül a (2) maradt (az (1)-et a tulajdonos mérése kizárta):

1. a fájl egy **korábbi mentésből** hozza (a beolvasó `0x00832830`
   közvetlenül a csomópontba írja, `0x008332b7`);
2. egy olyan írási út, amit **egyik pásztázás mintája sem fed** (pl.
   `memcpy`-vel másolt csomópont-blokk).

~~⇒ A döntéshez EGY ÚJ, még sosem mentett kollázs `.cxf`-je kell.~~
**MEGKAPTUK** (AI27/AI28/AI29), és a válasz: **(2)**.

⇒ **A jegy visszakerült GÉPI munkába** (`ready`, a `felhasználóra-vár`-t
a tulajdonos vette le 2026-09-06 12:57-kor). A következő lépés a
**blokk-másoló és a közvetett írási utak** felderítése: `memcpy` /
`rep movsd` a csomópont-blokkra, és a mentés-szervező (`0x00834700`)
hívóláncának végigolvasása. A négy mérési pont (4→500, 6→256, 9→313,
12→158) **ellenőrző készlet** a megtalált képlethez.

⛔ **ÚJ MINTÁT KÉRNI TILOS ugyanerre** — a tulajdonos kifejezett
utasítása (`#1412`, 2026-09-06). A négy pont elég a hitelesítéshez.


---

## 18. Az Indexkép (`contactsheet`) elrendezése — TELJESEN KIMÉRVE (2026-09-06, #1412)

*168. kutatói kör. Négy minta: `AI6` (9 kép), `AI27` (4), `AI28` (6),
`AI29` (12) — összesen **31 csomópont**. A 17. szakasz „a `scale`
levezetése ismeretlen" állítását ez a szakasz **részben lezárja**: a
`scale` SZEREPE megvan és pontosan igazolt (18.5), az ÉRTÉKÉNEK képlete
nyitva marad (18.6).*

### 18.1 ⭐ ÖNHELYESBÍTÉS: a `scale` öt témában a befoglaló doboz HOSSZABB OLDALA

A 17.1 tábla „arány" oszlopa (`scale / (w × 1024)`) félrevezetett: az ott
látott 1,25000 · 1,20020 · 1,78431 értékek **nem témakonstansok**, hanem
egyszerűen **1 / képarány**. A helyes, egyszerű azonosság:

> **`scale` = max(w, h)** — a csomópont befoglaló dobozának hosszabb
> oldala, a `.cxf` vízszintes 1024-es egységrendszerében.

**Mérve** — `scale / max(w, h)` minden csomópontra (119 csomópont, 15 fájl):

| téma | minták | csomópont | `scale / max(w,h)` |
|---|---|---|---|
| `picturepile` | AI · AI1 · AI2 · AI8 · AI9 · AI10 · lake-allo-piszkozat | 57 | **0,9998 – 1,0000** |
| `regulargrid` | AI5 | 9 | **1,0000** (9/9) |
| `multiexp` | AI7 | 4 | 0,0010 — `scale=1`, **jelző**, nem méret |
| `picturegrid` | AI3 | 9 | 0,52 – 0,75 — **nem** ez |
| `framegrid` | AI4 | 9 | 0,66 – 0,89 — **nem** ez |
| `contactsheet` | AI6 · AI27 · AI28 · AI29 | 31 | 1,03 – 1,21 — **nem** ez (ld. 18.5) |

Ez visszamenőleg megmagyarázza a 17.2 rejtélyét is: az `AI1` álló képének
`scale/w` aránya **1,78431**, a forráskép `816 × 1456` ⇒
`1456/816 = 1,78431` — a hányados **maga a fordított képarány**, nem
külön jelenség. Ugyanígy a `polaroid` keretes csomópontok 1,20020-ja a
polaroid keret 0,83320-as arányának reciproka.

*Bizonyítottsági fok: **megerősített** — puszta számolás 119 csomóponton.*

### 18.2 ⭐ Az Indexkép elrendezője: `FUN_00888210` @ `0x00888210`

*Forrás: `referencia/dekompilalt-kollazs/script-DecompileCollage.log`
[177] — a `collage/contactsheet/title` és `…/subtitle` erőforrásnevek
ebben a törzsben állnak (`0x00888210`, 2337 bájt). A konstansok helyi
diszasszemblálásból: `eszkozok/pe_dis.py`.*

```
W = param_5 - param_3                       ; a lap szélessége képpontban
H = param_6 - param_4                       ; a lap magassága képpontban
[param_1+0x1c] = W / H

balMargó   = CSONK(W * 0.06)                ; 0x0088827c  fmul qword [0x00cf46d0]
felsőMargó = CSONK(H * 0.15)                ; 0x00888296  fld  qword [0x00cf3fd0]
rés        = CSONK([param_1+0x18] * 0.08)   ; 0x008882d4  fmul qword [0x00cf4df0]
cellaSzél  = CSONK(0.88 * W / [param_1+0x14])  ; 0x00888305 fld dword [0x00d3a140]
cellaMag   = CSONK(0.79 * H / [param_1+0x10])  ;           fld dword [0x00d3a144]
```

**Az öt konstans a binárisból kiolvasva**, nem illesztés (a `0,88` és a
`0,79` **nem új** — egy korábbi kör már kiolvasta őket, ld. 18.8):

| konstans | VA | nyers bájtok | érték |
|---|---|---|---|
| oldalmargó-tényező | `0x00cf46d0` | `000000e051b8ae3f` (double) | **0,06** |
| felsőmargó-tényező | `0x00cf3fd0` | `000000403333c33f` (double) | **0,15** |
| rés-tényező | `0x00cf4df0` | `00000040e17ab43f` (double) | **0,08** |
| cellaszélesség-tényező | `0x00d3a140` | `ae47613f` (float) | **0,88** |
| cellamagasság-tényező | `0x00d3a144` | `713d4a3f` (float) | **0,79** |

⚠️ **CSONK, nem kerekítés.** A dekompilátum `ROUND(...)`-ot mutat, de a
kód minden `fistp` elé beállítja az FPU vezérlőszavát:
`or eax, 0xc00` (`0x00888258`, `0x008882a7`, `0x008882e6`, `0x00888323`)
— a `0xC00` a kerekítési mezőben **nulla felé csonkolás**. A mérés ezt
igazolja: kerekítéssel a cellaszélesség 451 volna, csonkolással **450**,
és a minták 450-et adnak.

A struktúra egész mezői: `[param_1+0x10]` = **sorok száma**,
`[param_1+0x14]` = **oszlopok száma**, `[param_1+0x18]` = harmadik
rácsparaméter (18.6). A csomópont-tömb lépésköze `0x38` (56 bájt) —
ugyanaz a tömb, amelyből a `.cxf`-író (`FUN_008347b0`, 17.4) dolgozik.
Az elrendező ide ír: `+0x18` = `x`, `+0x1c` = `y`, `+0x20` = `w`,
`+0x24` = `h`.

### 18.3 A lap egységrendszere: 1024 × CSONK(1024 · H/W)

A 17.3-at (vízszintesen 1024 egység) a `h` mezőkkel kiegészítve: a
függőleges törtek nevezője a lap magassága **ugyanabban az egységben**,
egész számra csonkolva.

| minta | `format` | 1024·H/W | lapmagasság | ellenőrzés |
|---|---|---|---|---|
| AI6 | 4:3 álló | 1365,33 | **1365** | max\|h·P − w/képarány\| = **0,001** egység (9/9) |
| AI27 | 297:210 álló | 1448,23 | **1448** | ugyanaz, **0,001** (4/4) |
| AI28 | 4:3 fekvő | 768,00 | **768** | ugyanaz, **0,001** (6/6) |
| AI29 | 13:9 fekvő | 708,92 | **708** | *(csak `polaroid` csomópontjai vannak — így nem ellenőrizhető; az elrendezés-egyezés igazolja, 18.5)* |

Ebből egyben az is látszik, hogy a kirajzolt doboz **magassága nincs
külön tárolva**: `h = w / képarány`, ahol a `w` **egész** a vízszintes
egységben — az eltérés a forráskép arányától 10⁻³ egység alatt marad.

### 18.4 ⭐ A KÉT ELRENDEZÉSI KÉPLET — 31/31 · 31/31 csomóponton PONTOS

```
x = oszlopIndex × cellaSzél + (cellaSzél − w)     // 2 + balMargó
y = sorIndex    × cellaMag  + (cellaMag  − scale) // 2 + felsőMargó
```

egész osztással, a lap 1024 × P egységrendszerében:

| minta | oszlop × sor | balMargó | felsőMargó | cellaSzél | cellaMag | `scale` | x | y |
|---|---|---|---|---|---|---|---|---|
| AI6 | 3 × 3 | 61 | 204 | 300 | 359 | 313 | **9/9** | **9/9** |
| AI27 | 2 × 2 | 61 | 217 | 450 | 571 | 500 | **4/4** | **4/4** |
| AI28 | 3 × 2 | 61 | 115 | 300 | 303 | 256 | **6/6** | **6/6** |
| AI29 | 4 × 3 | 61 | 106 | 225 | 186 | 158 | **12/12** | **12/12** |

**Nulla eltérés mind a 62 jóslaton.** Ez azonosítja `FUN_00888210`-et
mint a mintáinkat előállító elrendezőt — nem hasonlóság, hanem egyezés.

*Bizonyítottsági fok: **megerősített**.*

### 18.5 ⭐ Mire VALÓ a `scale` az Indexképnél: a függőleges középre igazítás

Az Indexképnél a `scale` **nem** a doboz hosszabb oldala (18.1): a doboz
`w × h` a **kirajzolt kép**. A `scale` ehelyett a **lap-szintű
csomópontmagasság**, amellyel az elrendező a sorban középre igazít —
ezt a 18.4 `y`-képlete méri, 31/31 pontossággal.

**Két független megerősítés, hogy tényleg ez:**

1. **Az `y` a soron belül minden csomópontra AZONOS**, pedig a `h`-juk
   különbözik (`AI27` első sora: `h` = 446,08 és 449,75, `y` = 0,174033
   mindkettőnek). Ha az igazítás a saját `h`-val menne, eltérnének. ⇒ a
   használt magasság **lap-szintű** — és pontosan ezért lap-szintű
   állandó maga a `scale` is. **Ez a #1412 eredeti rejtélyének
   magyarázata.**
2. **A kirajzolt kép mindig belefér:** `max(w, h) ≤ scale` mind a 31
   Indexkép-csomópontra, és a legnagyobb 96,7 %-ig tölti ki.

### 18.6 Ami NYITVA marad: mi állítja be a `scale` ÉRTÉKÉT

Két külön kérdés, mindkettő nyitott:

**(a) Ki írja a `+0x2c`-t?** `FUN_00888210` a csomópontba
**`0x3f800000` = 1,0** értéket ír (`*(node + 0x2c) = 0x3f800000`) ⇒ az
Indexkép-elrendező **nem** a forrás. A mentett fájlban mégis
313 / 500 / 256 / 158 áll ⇒ **egy későbbi menet írja felül**. Ez a 17.14
„blokk-másoló / közvetett írási út" ágának **pontosított** alakja: nem
akárhol a kollázs-sávban kell keresni, hanem **a témalayout UTÁN futó
menetben**.

**(b) Mi a képlete?** A négy mérési pont a cellamérettel:

| minta | oszlop × sor | cellaSzél × cellaMag | `scale` | `scale` / cellaMag |
|---|---|---|---|---|
| AI6 | 3 × 3 | 300 × 359 | 313 | 0,872 |
| AI27 | 2 × 2 | 450 × 571 | 500 | 0,876 |
| AI28 | 3 × 2 | 300 × 303 | 256 | 0,845 |
| AI29 | 4 × 3 | 225 × 186 | 158 | 0,849 |

⚠️ **Nem illesztek konstanst** a négy pontra: a két álló lap 0,87 körül,
a két fekvő 0,85 körül van, de négy pont mellett ez **nem bizonyíték**
(szabad paraméter elnyeli a hibát).

**A konkrét következő lépés** (gépi, új mintát NEM igényel): a
`[param_1+0x18]` mező azonosítása. Ez a harmadik rácsparaméter, a `rés`
alapja (`CSONK(0,08 × [param_1+0x18])`), és a `scale` nagyságrendjében
mozog. Ha `[param_1+0x18]` maga a `scale`, a kérdés arra fordul át, hogy
**ki tölti ki a téma-struktúra `+0x18` mezőjét** — a `CContactSheetTheme`
konstruktora, illetve a `0x00887bd0` / `0x00887e50` testvérfüggvények.

⛔ **Új mintát kérni TILOS ugyanerre** (17.15).

### 18.7 Amit a kör KIZÁRT (hogy ne járják újra)

- **A `scale` nem a cella hosszabb oldala** és nem a cellaosztás: mind a
  négy mintán más az arány (18.6 tábla).
- **A kép nem egységes cellába illesztett**: `AI27` három különböző
  képarányú képe három **különböző** magasságot kap (446,08 · 449,75 ·
  432,00), miközben egy közös dobozba illesztésnél (contain vagy cover)
  legalább az egyik méretüknek meg kellene egyeznie. A `FUN_009b4aa0`
  (`0x009b4aa0`) arány-tartó illesztő tehát **nem a cellát** kapja
  célként.
- **A `.tre`/`respack` nem játszik**: az elrendezés végig a fenti öt
  numerikus konstansból jön.

### 18.8 ⭐ A MI kódunk MÁR MAJDNEM kiszámolja a `scale`-t — 0…2 egység a négyből

*Ez a szakasz a „MIT AD MA" mérés, és **megcáfol** egy évek óta álló
állítást a saját kódunkról.*

A `draft.scale_for_theme()` docstringje szerint a `contactsheet` ágon
„*nincs levezetve — marad a négyzetoldal*". A **tényleges elrendezőnk**
viszont (`collage/picasa_render.py`, `_contact_sheet_nodes`) már ma is a
bináris receptjét futtatja: `0,06` / `0,15` margó, `0,88` × `0,79`
hasznos terület (`collage/shadow.py`, `CONTACT_USABLE_WIDTH/HEIGHT` —
a `0x00d3a140` / `0x00d3a144` **már ki volt olvasva** egy korábbi körben),
és a `0,08 · k` belső ráhagyás.

**Mérve** — a saját elrendezőnket a négy arany minta lapméretével és
forráskép-arányaival futtatva (`layout_nodes_for_aspects`, `contactsheet`):

| minta | lap | kép | a mi csomópont-**magasságunk** | a fájl `scale`-je | eltérés |
|---|---|---|---|---|---|
| AI6 | 1024 × 1365 | 9 | **311** | 313 | −2 |
| AI27 | 1024 × 1448 | 4 | **500** | 500 | **0** |
| AI28 | 1024 × 768 | 6 | **255** | 256 | −1 |
| AI29 | 1024 × 708 | 12 | **156** | 158 | −2 |

⇒ **A `scale` értéke NEM idegen szám**: az Indexkép-csomópont
**magassága**, amit a cellába illesztés és a `0,08 · k` ráhagyás után
kapunk. A maradék 0–2 egység a kerekítési módokon és a `k` /
oszlopszám levezetésén múlik.

**Amit ez NEM jelent:** a képlet nincs lezárva. A
`cellaMag − 2 · CSONK(0,08 · k)` alak a négy mintából **egyikre sem ad
egyszerre** pontos találatot: az `AI6` és az `AI28` ugyanazt a `k = 300`
cellaélt kapja, mégis 23, illetve 24 egységnyi ráhagyás kellene hozzájuk.
Tehát vagy a `k` levezetése tér el az eredetitől, vagy a ráhagyás nem
a `k`-ból jön.

**A mi elrendezőnk mért eltérései az `AI27`-en** (lapegységben):

| | eredeti | nálunk | eltérés |
|---|---|---|---|
| `x` | 161 · 607 · 178 · 611 | 162 · 610 · 179,5 · 613 | +1 … +3 |
| `y` | 252 · 252 · 823 · 823 | 253 · 253 · 825 · 825 | +1 … +2 |
| `w` | 250 · 257 · 216 · 250 | 249 · 255 · 214 · 249 | −1 … −2 |
| `h` | 446,08 · 449,75 · 432,00 · 446,08 | **500** mind | ez a `scale`, nem a rajzolt kép |

⛳ **Két külön teendő látszik**, és mindkettő a fejlesztésé (#2583):

1. **kerekítés helyett csonkolás** a margó- és cellaszámításban
   (`picasa_round` → `math.trunc`) — a bináris `or eax, 0xc00`-t állít
   (18.2), és a mintákon a 450 nyer a 451-gyel szemben;
2. **a csomópont `h`-ja nem a cella magassága**: a `.cxf`-be a **kirajzolt
   kép** doboza megy (`h = w / képarány`), a cellamagasság pedig a
   `scale` mezőbe — ez a mai kódunkban össze van csúsztatva.

## 19. Az Indexkép RÁCSA: a `[this+0x18]` LEZÁRVA, és a `scale` írója tovább szűkítve (2026-09-06, #1412)

*169. kutatói kör. A 18.6 két örökölt kérdését viszi: (a) mi a
`CContactSheetTheme` `[this+0x18]` mezője, (b) ki írja a csomópont `+0x2c`-t
a témalayout UTÁN.*

### 19.1 ⭐ (a) LEZÁRVA — a `[this+0x18]` a CELLAÉL (`k`), nem a `scale`

*Forrás: `FUN_00887e50` @ `0x00887e50` (`script-DecompileCollage.log` [176]),
és helyi diszasszemblálás.*

A téma slot0 gyökere (`FUN_00887ad0` @ `0x00887ad0`) először ezt hívja, és csak
utána az elrendezőt. A függvény összegyűjti a látható képeket egy **ideiglenes**
csomópont-vektorba, majd kiszámolja a rácsot:

```
W' = CSONK(lapszélesség × 0,88)        ; 0x00d3a140
H' = CSONK(lapmagasság  × 0,79)        ; 0x00d3a144
k  = CSONK( sqrt( (W' × H') / n ) )    ; EGÉSZ osztás n-nel a gyök ELŐTT
                                       ; sqrt: FUN_0049fe60 (0x00888134)
oszlop = W' / k                        ; egész osztás
sor    = H' / k
amíg (sor × oszlop < n):  k--, oszlop és sor újraszámol
[this+0x10] = sor · [this+0x14] = oszlop · [this+0x18] = k
```

Érvényességi kapu (`0x008881ca` és `0x008881f1`): `lapszélesség / oszlop ≥ 8`
**és** `lapmagasság / sor ≥ 8`, különben a függvény `-1`-gyel tér vissza és az
Indexkép nem jön létre.

⚠️ **CSONKOLÁS itt is:** a gyök eredményét a `0x00888144` `or eax, 0xc00`
utáni `fistp` (`0x00888156`) nulla felé csonkolja.

**Mérés — mind a négy mintán, 4/4:**

| minta | lap | kép | `k` | oszlop × sor (számolt) | oszlop × sor (MÉRT a `.cxf`-ből) |
|---|---|---|---|---|---|
| AI6 | 1024 × 1365 | 9 | **300** | 3 × 3 | 3 × 3 ✅ |
| AI27 | 1024 × 1448 | 4 | **450** | 2 × 2 | 2 × 2 ✅ |
| AI28 | 1024 × 768 | 6 | **300** | 3 × 2 | 3 × 2 ✅ |
| AI29 | 1024 × 708 | 12 | **186** | 4 × 3 | 4 × 3 ✅ |

⇒ **A `[this+0x18]` a cellaél `k`**, amiből az elrendező a rést számolja
(`CSONK(0,08 · k)`). **NEM a `scale`** — a 18.6 (b) pontjának első
feltevése ezzel **megdőlt**.

Ez egyben a 18.4 cellaosztásának forrását is megadja: az `oszlop` és a `sor`
nem külön szabály, hanem ennek a ciklusnak a kimenete.

*Bizonyítottsági fok: **megerősített** — bináris + 4/4 mérés.*

### 19.2 (b) A `scale` írója: ÚJ, MOV-alakú pásztázás — NEGATÍV

A 17.7–17.15 pásztázásai **x87-tárolást** kerestek (`fst`/`fstp`), egy
korábbi kör pedig az SSE- és disp32-alakot zárta ki. **Kimaradt az egész
alakú `mov`** — pedig float bitminta `mov`-val is írható (a dekompilátum
`= 0x3f800000` alakja épp ilyet sugall). Ezt a kör bezárta.

**Pásztázás** (bájtminta a teljes `.text`-en, fájloffset 4096, 8 646 656
bájt, minden találat capstone-nal ellenőrizve):

| alak | találat összesen | ebből a kollázs-sávban (`0x00820000`–`0x008fffff`) |
|---|---|---|
| `mov [bázis + index + 0x2c], …` (SIB — a csomópont-tömb alakja) | **5** | **0** |
| `mov [reg + 0x2c], …` (disp8, `esp`/`ebp` kizárva) | **608** | **96** |

A 96-ból **26** csomópont-alakú (ugyanaz a bázisregiszter ±0x140 bájton
belül a `+0x20`-ba **és** a `+0x24`-be is ír — a csomópont `w` és `h`
mezője), és ebből **5** áll a 0x38-as lépésköz közelében. Mind az öt
elolvasva: **konstruktor / nullázás**, nem csomópont. Példa a
`0x00829d60`: `+0x1c`…`+0x4c` mind `ecx`-szel (= 0) nullázva, a `[eax]`-ba
vtábla (`0xcbf6a0`) kerül — ez nem csomópont (a csomópont `+0` és `+4`
mezője hivatkozásszámlált sztring).

⇒ **A `scale` értékét EGYETLEN közvetlen tárolás sem írja.** A négy alak —
x87 mutatós, x87 SIB, SSE/disp32 (korábbi kör) és most az egész `mov`
(disp8, SIB és nem-SIB) — együtt lefedi a közvetlen írás minden szokásos
alakját.

⚠️ **A hatókör kimondva** (a 166. kör tanulsága szerint a MEZŐRE kell
szabni, nem a mintára). **NEM fedi:** a disp32-alakú `mov` (`mod=10`), és
az az eset, amikor a fordító a `+0x2c`-t **beleolvasztja a regiszterbe**
(`lea reg,[node+0x2c]`, majd `mov [reg], …`).

### 19.3 ⭐ A SZERKEZETI lelet, ami megmondja, hol keressük tovább

Az elrendezés **ideiglenes** vektorba megy:

- `FUN_00887ad0` (`0x00887ad0`) két **lokálist** használ (`local_10`,
  `local_c` — a `{mutató, méret}` pár), ezt adja át a rácsszámolónak és az
  elrendezőnek, és a végén **elpusztítja** (`FUN_0062d010`).
- `FUN_00888210` ebbe a lokális vektorba írja az `x`/`y`/`w`/`h`-t és a
  `+0x2c = 1,0`-t, majd minden csomóponthoz **képernyő-elemet** hoz létre
  (`FUN_0040eab0("collagepanel/cnode_")`, `FUN_00888b40`).

**Mégis:** a mentett `.cxf` `x`/`y` értékei a 18.4 képleteivel **31/31
csomóponton pontosan** egyeznek ⇒ a mentett csomópontok geometriája
**ebből** a menetből származik.

⇒ **Kell lennie egy visszamásolásnak** a panel/ideiglenes csomópontokból a
dokumentum csomópontjaiba, és **ott** kapja a `scale` az értékét. A
csomópont értékadó operátora (`FUN_008341b0` @ `0x008341b0`) a `+0x2c`-t
**másolja** (a 14 dwordből a 11. index), tehát az érték egy másik
csomópont-objektumból jön.

**A következő lépés (gépi, új mintát nem igényel):** a
`collagepanel/cnode_` elemek **visszaolvasása** — ki olvassa ki az elemek
geometriáját a dokumentum csomópontjaiba, és mit tesz a `+0x2c`-be. Ez már
nem a téma-, hanem a **panel-kód**.

### 19.4 A mi `cell_edge()`-ünk — egy mért eltérés

A `collage/shadow.py` `cell_edge()` a fenti képletet valósítja meg, és mind
a négy mintán **ugyanazt a `k`-t** adja (300 · 450 · 300 · 186). Egy
eltérés viszont mérhető:

| | eredeti (bináris) | nálunk (mérve) |
|---|---|---|
| a gyök alatti osztás | **egész** osztás: `(W' × H') / n` egész eredménnyel, utána `sqrt` | `math.sqrt(hasznos_w * hasznos_h / count)` — **lebegőpontos** osztás |

A négy mintán ez nem változtat a `k`-n, de matematikailag eltérhet egy
egységgel. Átadva: **#2583**.

## 20. A `picturepile` `scale` képlete a BINÁRISBÓL — a #1059 mintaszabálya megerősítve (2026-09-06, #1412)

*170. kutatói kör. ⚠️ **Ez NEM új szabály a mi kódunkban:** a
`collage/pile.py` `pile_size()` 2026 óta pontosan ezt számolja, a #1059
óta csonkolással. Ami ÚJ: a képlet és mind a három konstansa **a bináris
kódból van kiolvasva, címmel** — eddig kilenc mintára illesztett szabály
volt. A projekt „nincs becsült érték" szabálya szerint ez a különbség
lényeges: a sor `mérés (9 minta)`-ról `bináris (0x0082ca29…)`-ra vált.*

### 20.1 ⭐ A képlet és a helye

⛔ **HELYESBÍTVE a 21.1-ben (171. kör):** a képlet és a konstansok
helyesek, de a **per-csomópont létrát nem ez a hely állítja elő** —
az a kupac-elrendező (`FUN_0087bcb0`), és ott a szorzó a **lap
szélessége**, nem a beégetett 1024,0. Olvasd a 21.1-et is.

*Forrás: `FUN_0082c9a0` (`0x0082c9a0`, 426 bájt), helyi diszasszemblálás.*

```
n  = a képek száma
ha n <= 1:  f = 1,0
különben:   f = 1 / sqrt( sqrt(n) − 1 )        ; 0x0082ca29 sqrt
                                               ; 0x0082ca2e fsub 1,0
                                               ; 0x0082ca3f sqrt
                                               ; 0x0082ca4b  1/x
            ha NEM (f < 1,0):  f = 1,0         ; 0x0082ca57 fcom + jnp
S  = CSONK( f × 1024,0 × 0,33 )                ; 0x0082caa6 ×1024
                                               ; 0x0082cab5 ×0,33
                                               ; 0x0082cac4 fldcw 0xc00 (CSONKOLÁS)
                                               ; 0x0082cac8 fistp  → EGÉSZ
[téma + 0x3c] = S                              ; 0x0082cad0
```

| konstans | VA | nyers bájtok | érték |
|---|---|---|---|
| a kivont egység | `0x00c7e328` | `000000000000f03f` | **1,0** |
| lapegység-szorzó | `0x00cf4218` | `0000000000009040` | **1024,0** |
| alaparány | `0x00cf46c0` | `00000060b81ed53f` | **0,33** |
| négyzetgyök | `FUN_0049fe60` | — | — |

⭐ **Itt jön a csonkolás, amit a #1059 a mintákból vezetett le:** a
`0x0082cac4` `fldcw` a `0xc00` (nulla felé csonkoló) FPU-módot állítja be
a `fistp` elé, és az eredmény **egész számként** kerül a téma `+0x3c`
mezőjébe. A #1059 „9/9 `floor`-ral, 1/9 kerekítéssel" mérése ezzel
**bináris megerősítést kapott**.

### 20.2 A mérés: 55/57 — és a két kivétel a KÉZI átméretezés

`S(1…12)` = 337 · 337 · 337 · 337 · 303 · 280 · 263 · 249 · 238 · 229 · 222 · 215

A tizenkét arany `.cxf` `picturepile` csomópontjai, **csomópont-sorrendben**:

| minta | n | fájl | jósolt `S(1…n)` | |
|---|---|---|---|---|
| AI | 9 | 337·337·337·337·303·280·263·249·238 | ugyanaz | **9/9** ✅ |
| AI1 | 9 | ugyanaz | ugyanaz | **9/9** ✅ |
| AI8 | 9 | ugyanaz | ugyanaz | **9/9** ✅ |
| AI9 | 8 | 337·337·337·337·303·280·263·249 | ugyanaz | **8/8** ✅ |
| lake-allo-piszkozat | 8 | ugyanaz | ugyanaz | **8/8** ✅ |
| AI10 | **5** | 337·337·337·337·303 | ugyanaz | **5/5** ✅ |
| AI2 | 9 | **295,392**·337·337·337·303·280·263·**267,608**·238 | — | **7/9** ⚠️ |

**Összesen 55/57.** A két eltérés az `AI2` két **kézzel átméretezett**
csomópontja — pontosan az a kettő, amelyet a 17.5 már azonosított („a kézi
átméretezés megkerüli a létrát"). ⇒ a két mérés **kölcsönösen igazolja
egymást**.

⭐ **A létra INDEX szerinti, nem darabszám szerinti:** az `AI10` öt
csomópontja `337·337·337·337·303` — ha a képlet a darabszámmal menne, mind
az öt `S(5) = 303` volna. Az `i`-edik csomópont `S(i)`-t kap.

*Bizonyítottsági fok: **megerősített** — bináris képlet + 55/57 mérés, a
két kivétel megmagyarázva.*

### 20.3 ⚠️ Amit a `Scale: %d%%` NEM jelent

A kollázspanelnek van `collagepanel/scaletext` és `collagepanel/angletext`
kijelzője, `#ring` / `#target_chicklet2` / `#angle_placemark`
fogantyúkkal (`0x007e6bf0` és `0x00868570`). A kijelzés formátuma
**`Scale: %d%%`** (`0x00cc4384`, kulcs `collage::scale_format`), és a
kiírt szám:

```
0x00868e03  fld dword ptr [esp+0x1c]        ; a nyers érték
0x00868e07  fmul qword ptr [0xcf3a08]       ; × 100,0
0x00868e0d  call 0xc29990                   ; float → int
0x00868e18  call 0x40eab0                   ; sprintf
```

⛔ **Ez NEM a csomópont `+0x2c` mezője.** A húzás kezdetén a kód
**beégetett `100`-at** ír ki (`0x00868992` `push 0x64`), tehát a kijelző a
**húzás-relatív** nagyítást mutatja (100 % = a húzás kezdete). A
`0x008685ca` `mov [edx+0x2c], eax` írás sem csomópontot ír: az `edx` ott a
**fogantyú-kezelő** állapotobjektuma (a `[edx+0x30]`-on át `+0x288`-ig
indexel, ami csomópontnál hivatkozásszámlált sztring volna).

⇒ **A `.cxf` `scale` NEM százalék.** Ha az volna, a 337 „33 700 %"-ot
jelentene. A mértékegysége **lapegység** (a lap szélessége / 1024) — ld. 20.5.

### 20.4 A `picturepile`-specifikus BETÖLTÉSI szorzás — ÚJ, és nem látszik a mintákon

*`FUN_00834520` (`0x00834520`, 472 bájt) = „`.cxf` betöltése kollázs-dokumentumba".
Hívói mind **betöltési** utak: `0x0062c680` (kollázs-fül), `0x0082a670`
(kollázspanel), `0x008419e0` (automatikus mentés / „Recovered Autosave"),
`0x0087ed80` (`CCollageManager`, `*.cxf`).*

A függvény tartalmaz egy **`picturepile`-ra szűkített** ágat (sztring-
összehasonlítás a `"picturepile"`-lal, `0x00cbea2c`), amely ugyanazt az
`f`-et számolja ki (`0x00834622`–`0x0083465f`), megszorozza `1024,0`-val
és `0,33`-dal (`0x0083466b`, `0x00834671`) — **csonkolás nélkül** —, majd
egy 56 bájtos lépésközű ciklusban **minden csomópont `+0x2c` mezőjét
megszorozza** vele:

```
0x00834683  mov eax, [ebx+0x48]              ; a csomópont-tömb bázisa
0x00834686  fld dword ptr [edx+eax+0x2c]     ; csomópont.scale
0x0083468a  lea eax, [edx+eax+0x2c]
0x0083468e  fmul st(1)                       ; × F
0x00834693  add edx, 0x38                    ; 56 bájtos lépésköz
0x00834696  fstp dword ptr [eax]
```

⛳ **Ez pontosan az az írási alak, amit a 19.2 hatóköre kimondottan NEM
fedett** („amikor a fordító a `+0x2c`-t beleolvasztja a regiszterbe:
`lea reg,[node+0x2c]`, majd tárolás `[reg]`-be"). A kimondott hatókör-
korlát tehát nem formalitás volt: pontosan ott volt a kimaradt eset.

⚠️ **De a mintáinkon NEM látszik.** Ha egy betöltés után a mentés
visszaírná a szorzott értéket, az `AI1` 337-e a következő mentésben
`337 × 238,95 ≈ 80 500` volna. A tizenkét arany fájl **egyikében sincs**
ilyen érték — köztük az `AI2`-ben sem, amely bizonyítottan **kézzel
szerkesztett**, és a `lake-allo-piszkozat`-ban sem, amely automatikus
mentés. A `.cxf`-író (17.4) pedig **nem alakít át semmit**.

⇒ **A körre nézve LEZÁRVA-NEGATÍV:** a betöltési szorzás a mentett
`scale` értékét a mintáinkban nem befolyásolja, tehát **a mi írónkra
nincs következménye**. A „mit ír a valódi Picasa egy betöltés UTÁNI
mentéskor" kérdés külön jegyet kapott (**#2593**) — annak eldöntéséhez
olyan minta kellene, amit ez a kör **szándékosan nem kért**.

### 20.5 ⭐ A `scale` egységes olvasata — mind a hat témára

A 18.1, a 18.5 és a 20.1 együtt egyetlen mondattá áll össze:

> **A `scale` a csomópont CSEMPEMÉRETE lapegységben** (a lap szélessége /
> 1024) — az a hossz, amit a téma az adott csomópontnak szán.

| téma | a csempeméret forrása | mérés |
|---|---|---|
| `picturepile` | `S(i)` = `CSONK(clamp₁(1/sqrt(sqrt(i)−1)) × 1024 × 0,33)` | **55/57** (20.2) |
| `regulargrid` | a cella szélessége = `max(w, h)` | 9/9 (18.1) |
| `contactsheet` | a lap-szintű csomópontmagasság (a függőleges igazításé) | 31/31 (18.5) |
| `multiexp` | **1,0** — jelző, nincs csempézés | 4/4 (17.10) |
| `picturegrid`, `framegrid` | a cella szélessége (keret nélkül) | 17.1, nem mérve újra |

⛔ **Ami ebből még NINCS meg:** a `contactsheet` csempeméretének
**képlete**. A 19.1 kizárta a `[this+0x18]`-at (az a cellaél `k`), és a
mai kódunk 0…2 egységre eltalálja (18.8), de zárt alak nincs. A keresés
helye innentől: a `CContactSheetTheme` **saját** csempeméret-írása, a
`0x0082cad0` (`[téma+0x3c]`) analógiájára.

## 21. A `scale` MÉRTÉKEGYSÉGE bizonyítva, és a 20.1 mechanizmus-helyesbítése (2026-09-06, #1412)

*171. kutatói kör. A meglévő kollázs-dekompilátumból (`referencia/dekompilalt-kollazs/`),
új Ghidra-futás nélkül.*

### 21.1 ⛔ ÖNHELYESBÍTÉS: a létrát a KUPAC-ELRENDEZŐ állítja elő, nem a `0x0082c9a0`

A 20.1 a `picturepile` létráját a `FUN_0082c9a0` (`0x0082c9a0`) helyre tette,
és a `[téma+0x3c]` írást nevezte meg. **A képlet és a három konstans helyes,
a mérés (55/57) áll — a HELY és a SZORZÓ viszont téves volt.**

A per-csomópont létrát a **kupac-elrendező** állítja elő:
**`FUN_0087bcb0`** (`0x0087bcb0`, 520 bájt; a `CPileTheme slot0`
`FUN_0087b4a0` hívja):

```c
local_1c = clamp₁( 1 / sqrt( sqrt(n) − 1 ) );          // n = a KÉPEK SZÁMA → a SZÓRÁSI SÁV
local_8  = (param_6 − param_4) * 0.33000001311302185;  // = LAPSZÉLESSÉG × 0,33
local_14 = 1;
do {
    f = 1.0;
    if (1 < local_14)                                   // ← a CSOMÓPONT INDEXE
        f = clamp₁( 1 / sqrt( sqrt(local_14) − 1 ) );
    meret = ROUND( f * local_8 );
    FUN_0087c470(panel, csomópont, &out, local_1c, meret);
    local_14 = local_14 + 1;
} while (...);
```

**Mi változik ezzel:**

| | 20.1 (téves) | 21.1 (helyes) |
|---|---|---|
| a létra helye | `FUN_0082c9a0` | **`FUN_0087bcb0`** |
| a szorzó | beégetett `1024,0` (`0x00cf4218`) | **a lap szélessége** (`param_6 − param_4`) |
| a bemenet | — | az elrendező **ciklusváltozója** = a csomópont 1-alapú indexe |
| a `[téma+0x3c]` | „ide megy `S`" | **más mennyiség**: a `0x0082c9a0` ugyanezt a kifejezést a **darabszámmal** számolja ki a panel beállítás-objektumába |

⚠️ **Miért egyezett mégis a szám?** Mert a `.cxf` lapszélessége épp
**1024 egység** (18.3) — a `lapszélesség × 0,33` és az `1024 × 0,33`
ugyanazt adja. A 20. kör ebből ugrott arra, hogy a `0x0082c9a0` a forrás.
**Ez pontosan a „a megfejtett mechanizmus nem diagnosztizált ok" csapdája**,
egy körrel azután, hogy a 19.2 hatóköre helyesen ki lett mondva.

⛳ **A per-INDEX olvasat viszont most már KÓDBÓL is igazolt**, nem csak a
mintákból: a `local_14` a ciklus számlálója. A 20.2 mérése (55/57, négy
különböző képszámon) ezzel **kétszeresen** áll.

### 21.2 ⭐ A `scale` MÉRTÉKEGYSÉGE — a fogyasztó oldaláról bizonyítva

*`FUN_0087c470` (`0x0087c470`, 932 bájt) = a kupac elem-létrehozója.*

```c
meret = csomópont[+0x2c];                      // a tárolt scale
if (meret == 0.0) meret = (float)param_5;      // TARTALÉK: az elrendező számolta méret
...
local_14 = (float)(lapJobb − lapBal) * 0.0009765625;   //  = LAPSZÉLESSÉG / 1024
FUN_009debd0( lapszélesség × csomópont[+0x18],
              csomópont[+0x1c] × lapmagasság );        // pozíció
FUN_009dec60( csomópont[+0x28] × 57,29578 );           // theta, radián → fok
meret = local_14 * meret;
FUN_009deca0( meret );                                  // az ELEM nagyítása
```

⭐ **`0,0009765625` = 1/1024 pontosan.** Az elemre alkalmazott nagyítás:

> **elem-nagyítás = `scale` × (lapszélesség / 1024)**

⇒ **A `scale` hossz, a lap szélességének 1024-ed részeiben.** A 20.5
egységes olvasata ezzel az **író** oldaláról (mért egyezések) és a
**fogyasztó** oldaláról (bináris konstans) is alá van támasztva.

⭐ **Melléklelet:** a tárolt `scale` **elsőbbséget élvez** — az elrendező
számolta méret csak akkor lép be, ha a csomópont `scale`-je **nulla**. Ez
magyarázza a 17.5 megfigyelését is: a kézzel átméretezett csomópont
(`AI2`) megtartja a saját, nem egész értékét.

### 21.3 ⭐ ASZIMMETRIA: az Indexkép eleme NEM használja a `scale`-t

A két elem-létrehozó összevetése:

| | `picturepile` — `FUN_0087c470` | `contactsheet` — `FUN_00888b40` |
|---|---|---|
| pozíció (`FUN_009debd0`) | ✅ | ✅ |
| forgatás (`FUN_009dec60`) | ✅ (`+0x28 × 57,29578`) | **NINCS** |
| nagyítás (`FUN_009deca0`) | ✅ (`+0x2c × lapszél/1024`) | **NINCS** |

Az Indexkép elem-létrehozója **kizárólag a pozíciót** állítja be; a méretet
a `FUN_00888210` által számolt `w`/`h` képpontérték hordozza
(`FUN_00888b40(csomópont, &out, w_px, h_px)`, 18.2).

⇒ **Az Indexképnél a `scale` a rajzolásba egyáltalán nem megy bele** — tisztán
**elrendezési** mennyiség, pontosan úgy, ahogy a 18.5 mérte (a függőleges
igazítás magassága). Ez megmagyarázza, miért nem lehetett a rajzolt dobozból
levezetni.

### 21.4 Amit a kör KIZÁRT

- **A `FUN_0087cb70`** (`0x0087cb70`, 2183 b, a kupac szórás-lezárója) **nem ír**
  a csomópont `+0x2c`-jébe (a dekompilátum teljes törzsében nulla ilyen írás).
- **A `FUN_0087c470` sem ír** — csak **olvas** és tartalékol.

⇒ **A kupac-fában sincs `+0x2c`-író.** ⚠️ Ez a 20. kör egy kimondatlan
következtetését is helyesbíti: abból, hogy a fájl `S(i)`-t tartalmaz, **nem**
következik, hogy a kupac-elrendező odaírta volna. **Ki írja a `+0x2c`-t —
mindkét témára — továbbra is nyitott.**

### 21.5 Melléklelet: a polaroid felirat MÁS egységet használ

`FUN_0087c820` (`0x0087c820`, 701 b; a `polaroid` csomópont-témára hívódik a
`FUN_0087c470`-ből) a saját egységét **`max(lapszélesség, lapmagasság) / 1024`**
alapon számolja (`0x0087c8…`, a `0,0009765625` második előfordulása) — nem a
szélességből, mint a csempeméret. Aki a polaroid feliratot építi meg, ezt vegye
figyelembe.

## 22. K1 — ki írja a csomópont `+0x2c`-jét? A `lea`-út KIMERÜLT, és a keresés iránya megfordult (2026-09-07, #1412)

*172. kutatói kör. A munkasor **K1** tétele. Helyi pásztázás + a meglévő
dekompilátum; új Ghidra-futás nélkül.*

### 22.1 ⭐ A `lea`-alakú közvetett írás — KIMERÜLT, pozitív kontrollal

A 19.2 kimondta, hogy a hatóköre **nem fedi** azt az esetet, amikor a
fordító a `+0x2c`-t **beleolvasztja a regiszterbe**
(`lea reg,[node+0x2c]`, majd tárolás `[reg]`-be). A 21. kör talált egy
ilyet, tehát az alak bizonyítottan használt. Ez a kör végigpásztázta.

**Pásztázás** (bájtminta a teljes `.text`-en, minden találat
capstone-nal ellenőrizve; `esp`/`ebp` bázis kizárva):

| lépés | találat |
|---|---|
| `lea reg, [… + 0x2c]` címképzés | **207** |
| …ebből 24 bájton belül **tárolás a kapott mutatóra** (`fstp`/`fst`/`mov`/`movss`) | **62** |
| …ebből a **kollázs-sávban** (`0x00820000`–`0x008fffff`) | **3** |

A három:

| cím | mi | értékelés |
|---|---|---|
| `0x0083468a` → `0x00834696` `fstp [eax]` | a **betöltési szorzás** (20.4) | ⛳ **POZITÍV KONTROLL** — a pásztázás megtalálta a már ismert példányt |
| `0x008300dc` → `0x008300e4` `mov [edi], 0` | hivatkozásszámlált **sztring** törlése (a következő sor `lea edi,[esi+0x28]`, ugyanaz az idióma) | nem csomópont |
| `0x00860032` → `0x0086003e` `mov [edi], ebp` | hivatkozásszámlált **sztring** értékadás (`cmp [esi+0x2c],ebp` → `call 0x401000` felszabadítás → tárolás → `movzx [ebp]`, `cmp 0x80` hivatkozásszám) | nem csomópont |

⇒ **A `lea`-út a kollázs-sávban nem ad új `scale`-írót.** A pozitív kontroll
miatt ez **érvényes negatív**, nem a minta hibája.

### 22.2 ⭐ Mindkét elrendező FELTÉTEL NÉLKÜL `1,0`-t ír — utasításszinten

A 17.10 ezt dekompilátumból állította. Most utasításszinten is megvan, és
az is, hogy **függvényenként pontosan EGY** csomópont-tömb `+0x2c` tárolás
létezik (a többi `[esp+0x2c]` lokális változó):

| elrendező | a tárolás | a betöltött érték |
|---|---|---|
| `contactsheet` `FUN_00888210` | `0x008885bc` `fstp dword ptr [ebx + eax + 0x2c]` | `0x008885ac` **`fld1`** |
| `regulargrid` `FUN_00885060` | `0x0088522d` `fstp dword ptr [eax + esi + 0x2c]` | `0x0088520d` **`fld1`** |

**Elágazás nincs** — mindkettőnél a `fld1` közvetlenül a tárolás előtt áll,
ugyanabban az alapblokkban.

### 22.3 A mentés-szervező nem alakít át

`FUN_00834700` (`0x00834700`, 174 bájt) csak puffert épít
(`0x009bfde0`, `0x00985ff0`, `0x009bfe70`), meghívja az XML-írót
(`0x008347b0`) és a fájlba írót (`0x009c15a0`). **Nulla `scale`-érintés** —
a 17.4 („az író nem alakít át") a szervező szintjén is áll.

### 22.4 ⭐ A hozzáadó VIRTUÁLIS metódus — és csak a BEOLVASÓ hívja

A 17.13 a `FUN_00833920`-at azonosította a csomópont-tömb `push_back`-jeként
(a staging `+0x64`/`+0x68` egyetlen olvasója). A hívóit kerestem:

```
közvetlen `call 0x00833920`:            0
a cím mint 32 bites ADAT a fájlban:     1 hely — VA 0x00cbf898
```

A `0x00cbf898` a **`CCollageParser` vtáblájában** van
(`0x00cbf878`, 17.12) — a **8. slot** (`0x00cbf898 − 0x00cbf878 = 0x20`).

⇒ **A `push_back` a `CCollageParser` virtuális metódusa, és kizárólag a
vtáblán át hívódik.** Ez egybevág a 17.11-gyel („a `+0x68`-ba a
kollázs-sávban csak a beolvasó ír"): **a staging → `push_back` út a
FÁJLBEOLVASÁSÉ**, nem az interaktív képhozzáadásé.

### 22.5 A keresés iránya ezzel MEGFORDUL

A 19.3 szerint a téma-elrendezők **ideiglenes** csomópont-vektorba
dolgoznak, amit a `FUN_00887ad0` a végén elpusztít. Ha ez így van — és a
22.2 szerint az elrendezők amúgy is csak `1,0`-t írnak —, akkor a
**dokumentum** csomópontjainak `scale`-jét sem a téma-elrendező, sem a
beolvasó nem adja egy ÚJ kollázsnál.

⇒ **A keresés helye: hogyan jön létre egy csomópont, amikor a felhasználó
képet ad a kollázshoz** (nem betöltéskor). Ez a `collagepanel/`
hozzáadási út, nem a téma- és nem a parser-kód.

*Bizonyítottsági fok: **erős** — a 22.4 megerősített (bináris), a 19.3
szerkezeti olvasata viszont két lépésből áll (ideiglenes vektor + az író
tömbje), és a kettő azonosságát a kör nem mérte ki.*

### 22.6 A `+0x2c`-írás KIZÁRT alakjai — a teljes lista

| alak | hol | kör |
|---|---|---|
| x87 `fst`/`fstp [reg+0x2c]` (mutatós) | teljes `.text` | 17.10, 17.15 |
| x87 `fst`/`fstp [bázis+index+0x2c]` (SIB) | teljes `.text` | 17.10 (a két elrendező, `fld1`) · 22.2 (utasításszinten) |
| SSE és disp32-alak | teljes `.text` | korábbi kör (00-index, 2026-09-01) |
| egész `mov [reg+0x2c]` (mutatós és SIB) | teljes `.text` | 19.2 |
| **`lea`-materializált mutató + tárolás** | teljes `.text`, **pozitív kontrollal** | **22.1** |
| a kupac-fa (`FUN_0087c470`, `FUN_0087cb70`) | olvasás igen, írás nem | 21.4 |
| a mentés-szervező | nem érinti | 22.3 |

**Ami MARADT** (egyik sincs kipróbálva):

1. **Futásidőben számolt eltolás:** `fstp [reg + reg]` / `mov [reg+reg], …`,
   ahol a `0x2c` **regiszterben** van (tulajdonság-beállító, „reflection"
   stílus). Minden eddigi pásztázásunk a **literál** `0x2c` eltolást
   követelte meg.
2. **Blokk-másolás** egész csomópontra (`memcpy` / `rep movsd`) olyan
   forrásból, amelyben az érték már benne van.
3. A kollázs-sávon **KÍVÜLI** kód.

## 23. K1 — az OLCSÓ lánc KIMERÜLT, és egy sáv-definíciós hiba a saját méréseinkben (2026-09-07, #1412)

*173. kutatói kör. A munkasor **K1** tétele, a 172. kör megfordult
irányával (képhozzáadási út).*

### 23.1 ⛔ ÖNHELYESBÍTÉS: a „kollázs-sáv" definíciója TÚL TÁG volt

A 169. és a 172. kör a `0x00820000`–`0x008fffff` tartományt nevezte
„kollázs-sávnak" — **ellenőrzés nélkül**. A `string_xrefs` szerint az alja
**nem kollázs**:

```sql
SELECT DISTINCT string FROM string_xrefs
WHERE function_address BETWEEN '0x00820000' AND '0x00826000';
→  Preferences · Tahoma
   conf(%f),pan(%f),leye(%f,%f),reye(%f,%f),mouth(%f,%f)
   SmartMultiPersonTrans
```

⇒ a `0x00820000`–`0x00826000` **arcfelismerés**. A valódi kollázs-kód
`0x00829…`-tól kezdődik (a `0x00829d40` a `contactsheet` téma-azonosítója,
20.x; a `0x0082a670` a kollázspanel).

**Mit jelent ez a korábbi eredményekre?** A negatívokat **nem gyengíti**,
hanem erősíti: egy túl tág sávban több jelöltet néztünk át, mint kellett
volna. A **SZÁMOK** viszont felfújtak voltak (pl. a 19.2 „96 a
kollázs-sávban" értéke idegen kódot is tartalmazott). A jövőbeli
pásztázások a `0x00829000`–`0x00895000` tartományt használják.

### 23.2 A `FUN_0087c470` NEM ír vissza — utasításszinten

A 21.2 dekompilátumból mondta ki; most a gépi kód:

```
0x0087c510  fld   dword ptr [ebx + 0x2c]     ; a csomópont scale-je
0x0087c513  fstp  dword ptr [esp + 0x38]     ; LOKÁLISBA
0x0087c517  fldz
0x0087c519  fcomp dword ptr [esp + 0x38]     ; == 0 ?
0x0087c522  jp    0x87c53a
0x0087c524  mov   ecx, [esp + 0x44]          ; param_5 = a számolt méret
0x0087c528  fild  dword ptr [esp + 0x44]
0x0087c536  fstp  dword ptr [esp + 0x38]     ; a LOKÁLIS lecserélése
```

**A tartalék csak a lokálisba megy** — a csomópont `+0x2c`-je érintetlen
marad. ⇒ a „visszaírja a tartalékot" feltevés **megdőlt**.

### 23.3 Futásidőben számolt eltolású FLOAT tárolás — 8 a tartományban, egyik sem csomópont-`scale`

`fstp dword ptr [bázis + index]` **nulla eltolással** (a `0x2c` regiszterben):

| | találat |
|---|---|
| teljes `.text` | **66** |
| a valódi kollázs-tartományban | **8** |

A nyolcból **öt** `*4`-es skálázású (`[reg + reg*4]`) — az **float tömb**
indexelés, nem struktúramező. A maradék három elolvasva:

- `0x008734bd` — `eax += eax; eax += eax` ⇒ `index*4`, szintén tömb;
- `0x0088cc70` és `0x0088cc95` — **polárkoordináta-átváltás** ugyanabban a
  törzsben (`FUN_0088c480`): `fild` → `sqrt` (`0x0049fe60`) → tárolás, majd
  `fild`,`fild` → `0x00c29cca` (arkusz tangens) → tárolás; az eltolás egy
  **mutató-dereferálásból** jön (`mov eax,[esp+0x28]; mov ecx,[eax]`).

⇒ **Egyik sem a csomópont `scale`-jének írása.** *(A `0x0088c480`
polárkonverziója önmagában érdekes — sugár és szög egy közös bázisra —, de
nem a hozzáadási úton van, és a törzs sztring nélküli.)*

### 23.4 Blokk-másolás — a kollázsban nincs

| minta | teljes `.text` | a valódi kollázs-tartományban |
|---|---|---|
| `mov ecx, 0xe` + `rep movsd` (56 bájt = 14 dword) | **15** | **0** — mind a 15 az **arcfelismerésben** (`0x00820…`–`0x00825…`) |
| `push 0x38` + `call` 16 bájton belül | 211 | a kollázs-kódban a `0x00833ac3` — a **már ismert** `push_back` foglalása (`FUN_00833920`, `mul 0x38` a `0x00833a92`-n) |

⇒ **Nincs 56 bájtos blokk-másolás a kollázs-csomópontokra**, a `push_back`
saját foglalásán kívül.

### 23.5 A K1 olcsó lánca KIMERÜLT — mi van hátra

**Kizárva** (a teljes lista; a 22.6 kiegészítve ezzel a körrel):

| alak / út | kör |
|---|---|
| x87 `fst`/`fstp [reg+0x2c]` (mutatós) és SIB | 17.10, 22.2 |
| SSE és disp32-alak | 2026-09-01 |
| egész `mov [reg+0x2c]` (mutatós és SIB) | 19.2 |
| `lea`-materializált mutató + tárolás (pozitív kontrollal) | 22.1 |
| **futásidőben számolt eltolású float tárolás** | **23.3** |
| **56 bájtos blokk-másolás** | **23.4** |
| a kupac-fa (`FUN_0087c470` olvas, nem ír — utasításszinten) | 21.4, **23.2** |
| a mentés-szervező (`FUN_00834700`) | 22.3 |
| a staging → `push_back` út (a `CCollageParser` vtáblájáé) | 22.4 |

⇒ **Az olcsó bizonyítéklánc (index → sztring/xref → helyi pásztázás →
meglévő dekompilátum) ezzel KIMERÜLT.**

**A következő lépés a DRÁGA út**, és pontosan megnevezhető: **célzott
Ghidra-dekompiláció a kollázspanel képhozzáadási ágára** — a `0x0082a670`
(a kollázspanel, `collagepanel/remove_node`, `rand_placement`,
`rand_order`, `picker_panel`, `filmstrip` sztringekkel) hívási fája, két
szint mélyen, azzal a konkrét kérdéssel: **hol kapja a frissen felvett
csomópont a `+0x2c` mezőjét**.

*Bizonyítottsági fok a kizárásokra: **megerősített** (bájtmintás pásztázás
capstone-ellenőrzéssel, a 22.1-ben pozitív kontrollal). A „hol van akkor"
kérdésre: **NINCS MEG**.*

## 24. K2 — a cellaél és a cellaosztás viszonya, és az Indexkép-illesztés KÉTÉRTELMŰSÉGE (2026-09-07, #1412)

*174. kutatói kör. A munkasor **K2** tétele: a `contactsheet` csempeméret
(a `.cxf` `scale`) zárt képlete.*

⛔ **A kör NEM illeszt számot a négy pontra.** A korábbi próbálkozások ezt
tették, és a projekt szabálya tiltja; a képletnek a kódból kell jönnie.

### 24.1 ⭐ `k = min(cellaSzél, cellaMag)` — 4/4 a mintákon

A 19.1 a cellaélt (`k`) a gyök-ciklusból vezette le, a 18.4 pedig a
cellaosztást külön mérte. A két szám viszonya:

| minta | cellaSzél | cellaMag | `min` | `k` (19.1) | |
|---|---|---|---|---|---|
| AI6 | 300 | 359 | 300 | **300** | ✅ |
| AI27 | 450 | 571 | 450 | **450** | ✅ |
| AI28 | 300 | 303 | 300 | **300** | ✅ |
| AI29 | 225 | 186 | 186 | **186** | ✅ |

**Miért nem véletlen:** a rácsképletben `oszlop = ⌊W'/k⌋` és
`sor = ⌊H'/k⌋` (19.1), a cellaosztás pedig `cellaSzél = CSONK(0,88·W/oszlop)`
és `cellaMag = CSONK(0,79·P/sor)` (18.2). Az egészosztásból következik, hogy
**mindkét cella legalább `k`** — az egyenlőség akkor áll, ha az adott irány
a szűk keresztmetszet.

⚠️ **Amit ez NEM mond:** hogy az egyenlőség **mindig** fennáll. Négy mintán
igaz; általános bizonyítás nincs. Aki erre épít, ellenőrizze.

*Bizonyítottsági fok: **erős** — 4/4 mérés + szerkezeti indoklás, de nem
általános levezetés.*

### 24.2 Az Indexkép-illesztés elágazása — utasításszinten

A `FUN_00888210` csomópont-ciklusának magja (`0x008883cd`–`0x0088846f`):

```
0x008883cd  mov ecx, [ebx + eax + 8]        ; csomópont+8 (a kép azonosítója)
0x008883d1  lea esi, [esp + 0x98]
0x008883dc  call 0x00835380                 ; kulcs-objektum feltöltése
0x008883ef  mov [esp+0x98], 0
0x008883e8  mov [esp+0x9c], edx             ; = csomópont+8
0x008883fa  mov ecx, [eax + 0x270]          ; eax = param_1 (a panel)
0x00888407  call [[ecx]]                    ; VIRTUÁLIS hívás a kulccsal
0x00888409  test eax, eax
0x0088840b  je  0x00888423                  ; ha 0 → a beállítás KIMARAD
0x0088840d  mov eax, [esp + 0x2c]           ;  \  csak ha != 0:
0x00888411  mov ecx, [esp + 0x44]           ;   > a doboz W/H-ja
0x00888415  mov [esp+0xf8], eax             ;  /
0x0088841c  mov [esp+0xfc], ecx
0x00888423  …                               ; közös ág
0x00888438  lea eax, [esp + 0x88]           ; az egyik rect
0x0088843f  lea esi, [esp + 0x78]           ; a másik rect
0x00888443  lea ecx, [esp + 0x60]           ; a KIMENET
0x0088844e  call 0x009b4aa0                 ; arány-tartó illesztés
0x00888463  sub eax, edi  ; W  -= rés       ; a kimenet BESZŰKÍTÉSE
0x00888465  add edx, edi  ; x0 += rés
0x0088846d  add esi, edi  ; y0 += rés
0x0088846f  sub ecx, edi  ; H  -= rés
```

⇒ **A tárolt `w`/`h` = az illesztett doboz mínusz 2 × rés** — ez most
utasításszinten is megvan (eddig csak a dekompilátumból).

### 24.3 ⛔ A KÉTÉRTELMŰSÉG, amit NEM szabad megtippelni

A `FUN_009b4aa0` (`0x009b4aa0`) két rectet kap: az **`EAX`** a méretezendő
(a kimenet ennek az arányát tartja), az **`ESI`** a célkeret. A hívás előtt:

- `lea eax, [esp + 0x88]` — ebbe a rectbe megy a `[esp+0x2c]` / `[esp+0x44]` pár;
- `lea esi, [esp + 0x78]` — ennek az eredete a törzs korábbi részéből jön.

**Két, egymásnak ellentmondó olvasat:**

| | ha `EAX` = a CELLA | ha `EAX` = a KÉP |
|---|---|---|
| a kimenet aránya | a celláé | a **képé** |
| a mérés (18.3) szerint a tárolt doboz aránya | — | **a forráskép aránya, 10⁻³ egység alatt** |
| az álló képek `h`-ja | mind `cellaMag − 2·rés` (lap-szintű állandó) | képenként eltérő |
| a mérés (`AI27`) | `h` = 446,08 · 449,75 · 432,00 — **ELTÉRNEK** | ✔ |

⇒ A **mérés** a „`EAX` = a kép" olvasatot támogatja, a **regiszter-hozzárendelés**
viszont a `[esp+0x2c]`/`[esp+0x44]` (számított egész) párt teszi az `EAX`-rectbe —
és azok a törzs korábbi `fistp`-jeiből jönnek, ami cellaméretre utal.

⛔ **Ezt a kör NEM dönti el.** A feloldáshoz a 2337 bájtos törzs
**verem-nyilvántartását** kell végigvinni (`[esp+0x2c]`, `[esp+0x44]`,
`[esp+0x78]`, `[esp+0x88]` eredete) — ez már **dekompilátor-munka**, nem
kézi diszasszemblálás.

### 24.4 A K2 olcsó lánca is a DRÁGA úthoz ér — a K1-gyel EGY menetben

A K2 megválaszolásához ugyanaz kell, mint a K1-hez (23.5): **célzott
Ghidra-dekompiláció**. A két kérdés ugyanabban a modulban van, tehát
**egyetlen futás mindkettőt fedi**:

| kérdés | mit kell dekompilálni |
|---|---|
| **K1** — ki írja a csomópont `+0x2c`-t | `0x0082a670` (kollázspanel) hívási fája, 2 szint |
| **K2** — az Indexkép csempeméretének képlete | `0x00888210` (`FUN_00888210`) teljes törzse, verem-nyilvántartással |

**Egy Ghidra-menet, két gyökér.** A `picasa-x86-research` skill szerint a
teljes autoanalízis ~450 mp; a két gyökér dekompilációja ehhez képest
elhanyagolható.

*Bizonyítottsági fok: a 24.1 **erős**, a 24.2 **megerősített**, a
csempeméret képletére **NINCS MEG**.*

## 25. A célkeret AZONOSÍTVA, a forrásrect NEM — és a drága út JOGOSULTSÁGON akadt el (2026-09-07, #1412)

*175. kutatói kör. A 174. kör egy Ghidra-menetre utalta a K1-et és a K2-t.*

### 25.1 ⛔ A felhős Ghidra-kör NEM INDÍTHATÓ — mérve, nem feltételezve

```
$ python3 scripts/codespace_re.py doctor
  ✓ Logged in to github.com account sanchomuzax
  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'
error getting codespaces: HTTP 403: Must have admin rights to Repository.
This API operation needs the "codespace" scope.
```

- A munkamenet GitHub-tokenjéből hiányzik a **`codespace`** jogosultság.
- A bot-token (`picasapy-claude-agent[bot]`) sem alkalmas rá.
- **Helyi Ghidra nincs** (`which ghidra ghidraRun analyzeHeadless` → semmi).
- **A költségkeret NEM akadály:** `GO | session 25% | weekly 60% | burn 0,64x`.

⇒ **Az akadály jogosultság, nem tudás és nem keret.** Üzemeltetési jegy:
`picasapy-agent` **#53**.

### 25.2 ⭐ A CÉLKERET azonosítva: a CELLA

A `FUN_00888210` teljes törzsének verem-rekesz-nyilvántartása (capstone,
minden `[esp+X]` írás) a `FUN_009b4aa0`-hívás (`0x0088844e`) két rectjére:

| rect | mező | az írás | mit kap |
|---|---|---|---|
| **`ESI`** (`lea esi,[esp+0x78]`) | [0] | `0x0088836a` `mov [esp+0x78], ebx` | 0 |
| | [1] | `0x0088836e` `mov [esp+0x7c], ebx` | 0 |
| | [2] | `0x0088835c` `mov [esp+0x80], ecx` | **= `[esp+0x2c]`** (`0x0088833f`) |
| | [3] | `0x0088839f` `mov [esp+0x84], eax` | **= `[esp+0x44]`** (`0x0088839b`) |
| **`EAX`** (`lea eax,[esp+0x88]`) | [0] | `0x008883b0` | 0 |
| | [1] | `0x008883b7` | 0 |
| | [2] | `0x00888447` `mov [esp+0x90], edx` | `[esp+0xf8]` |
| | [3] | `0x00888431` `mov [esp+0x94], eax` | `[esp+0xfc]` |

A `[esp+0x2c]` és a `[esp+0x44]` a **cellaSzél / cellaMag** — a 18.2
`fistp`-jeinek eredménye (`0x00888393` → `0x0088839b` → `0x0088839f`).

⇒ **Az `ESI`-rect = (0, 0, cellaSzél, cellaMag) = a CELLA**, és a
`FUN_009b4aa0`-ban az `ESI` a **célkeret**. A 24.3 kétértelműségének
**egyik fele eldőlt**.

*Bizonyítottsági fok: **megerősített** — az érintett írások mind a
push-ok utáni, azonos veremállapotban vannak.*

### 25.3 ⚠️ A FORRÁSRECT nem dőlt el — és a helyi módszer KORLÁTJA

Az `EAX`-rect mérete a `[esp+0xf8]` / `[esp+0xfc]` rekeszekből jön. A
pásztázás szerint ezeket **csak** a `0x00888415` / `0x0088841c` írja — a
virtuális hívás **nem nulla** ágán, és ott **ugyanazt a cellaSzél/cellaMag
párt** kapják. A nulla ágon tehát írás nélkül maradnának.

⛔ **De ez a következtetés NEM megbízható, és ki kell mondani, miért:** a
pásztázásom **nyers `esp`-eltolásra** illeszt, és **nem követi az `esp`
mozgását**. A törzs a belépéskor `sub esp, 0x124`, majd négy `push`
(`0x00888247`–`0x0088826a`) — onnantól ugyanaz a rekesz **más
eltolással** címezhető (`[esp+0xf8]` ↔ `[esp+0x108]`). Egy másik
veremállapotban írt érték a mintámból **kimarad**.

⇒ **A 174. kör ítélete áll: ez dekompilátor-munka.** A verem
normalizálása (esp-nyilvántartás minden ágon) pontosan az, amit egy
dekompilátor elvégez, és amit kézzel nem szabad megjátszani.

### 25.4 A mérés és a kódolvasat ELLENTMOND — kimondva

A 25.2 szerint a célkeret a cella. Ha a forrásrect a kép természetes
mérete volna, akkor egy álló kép a cellába illesztve **`cellaMag`
magasságot** kapna, és a tárolt `h` **lap-szintű állandó** lenne. A mérés
viszont (18.3, `AI27`) **három különböző** magasságot ad: 446,08 · 449,75
· 432,00.

**Számpélda** (`AI27`, cella 450 × 571, kép 816 × 1456):
`zx = (450+0,499)/816 = 0,55208`, `zy = (571+0,499)/1456 = 0,39251`,
`min = zy` ⇒ kimenet `(320, 571)`, rés levonva `(248, 499)`.
**Mért:** `(250, 446,08)`. ⇒ **nem egyezik.**

⛔ **Az ellentmondás áll**, és a kör nem oldja fel. A két lehetőség:

1. a forrásrect **nem** a kép természetes mérete (hanem valami, amit a
   `0x00835380` vagy a virtuális hívás tölt egy általam nem követett
   veremállapotban);
2. a tárolt `w`/`h` **nem** ennek az illesztésnek a kimenete (a 24.2
   olvasata hibás).

**Mindkettőt ugyanaz dönti el:** a `FUN_00888210` dekompilációja
verem-normalizálással.

*Bizonyítottsági fok: az ellentmondás **megerősített** (a számpélda
ellenőrizhető), a feloldás **NINCS MEG**.*

## 26. K2 LEZÁRVA, K1 pedig KIMERÍTŐ NEGATÍVOT kapott — a felhős dekompiláció (2026-09-07, #1412)

*A 175. körben megnevezett jogosultsági akadály (`picasapy-agent` #53)
elhárult; ez a szakasz az EBBŐL következő Ghidra-menet eredménye. Bináris:
`Picasa3.exe`, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`,
10 160 456 bájt; Ghidra **12.1.2**, image base `0x00400000`.*

### 26.1 A `.cxf` MEZŐTÉRKÉP most már a KIÍRÓ oldaláról is bizonyított

Eddig a csomópont-mezők jelentése a **fájl** elrendezéséből jött. A `.cxf`
XML-írója (`FUN_008347b0`, `0x008347b0`) a hat lebegőpontos attribútumot
**ebben a sorrendben** olvassa ki, mindig ugyanazzal a formázóval
(`FUN_0040eab0(&DAT_00c817c0, (double)…)`):

| a kiírás sorrendje | a kiolvasott mező | a `.cxf` attribútuma |
|---:|---|---|
| 1. | `csomópont + 0x18` | `x` |
| 2. | `csomópont + 0x1c` | `y` |
| 3. | `csomópont + 0x20` | `w` |
| 4. | `csomópont + 0x24` | `h` |
| 5. | `csomópont + 0x28` | `theta` |
| 6. | **`csomópont + 0x2c`** | **`scale`** |

A címzés mindenhol `param_2 + <eltolás> + *(int *)(param_1 + 0x48)` — a
`[param_1+0x48]` a csomópont-tömb bázisa, a `param_2` a csomópont eltolása.
A függvény sztringkészlete (`string_xrefs`) tartalmazza a `theta` és a
`scale` attribútumnevet, továbbá az `image`, `version`, `collage`, `theme`,
`shadows`, `captions`, `albumUID`, `background`, `spacing`, `albumTitle`,
`albumDate`, `orientation`, `portrait`, `landscape`, `solid` neveket.

*Bizonyítottsági fok: **megerősített**.* Ez az első alkalom, hogy a
mezőtérkép nem a fájlból visszafejtve, hanem a **kiíró kódjából** áll.

### 26.2 K2 — LEZÁRVA: az `EAX`-rect a MÉRETEZENDŐ, és a képlet KEREKÍT

A `FUN_009b4aa0` (`0x009b4aa0`, 184 bájt) teljes dekompilátuma:

```c
undefined4 * __fastcall FUN_009b4aa0(undefined4 *param_1)   // ECX = kimenet
{
  int *in_EAX;        // a MÉRETEZENDŐ (forrás) rect
  int *unaff_ESI;     // a CÉLKERET
  if ((in_EAX[2] - *in_EAX != 0) && (in_EAX[3] - in_EAX[1] != 0)) {
    fVar2 = (float)(in_EAX[2] - *in_EAX);                             // srcW
    fVar3 = ((float)(unaff_ESI[2] - *unaff_ESI) + 0.499) / fVar2;     // zx
    fVar4 = (float)(in_EAX[3] - in_EAX[1]);                           // srcH
    fVar1 = ((float)(unaff_ESI[3] - unaff_ESI[1]) + 0.499) / fVar4;   // zy
    if (fVar1 < fVar3) { fVar3 = fVar1; }                             // z = min
    *param_1 = 0;  param_1[1] = 0;
    param_1[2] = (int)ROUND(fVar3 * fVar2 + 1e-05);
    param_1[3] = (int)ROUND(fVar4 * fVar3 + 1e-05);
    return param_1;
  }
  *param_1 = 0; param_1[1] = 0; param_1[3] = 0; param_1[2] = 0;
  return param_1;
}
```

A két konstans a binárisból, **most kiolvasva** (mindkettő `double`):

| cím | fájloffszet | érték |
|---|---|---|
| `0x00cf4160` | `0x8f4160` | **0,499** |
| `0x00cf41e0` | `0x8f41e0` | **1e-05** |

⇒ **`z = min((célSzél + 0,499)/forrSzél ; (célMag + 0,499)/forrMag)`**, és a
kimenet `(0, 0, KEREK(z·forrSzél + 1e-5), KEREK(z·forrMag + 1e-5))` —
**kerekítés, nem csonkolás**. (A cellaméret-számítás ettől függetlenül
csonkol, 18.2.)

**A regiszter-szerepek a hívás helyén** (`0x00888438`–`0x0088844e`):

```asm
0x00888438  lea eax, [esp + 0x88]   ; EAX = a MÉRETEZENDŐ rect
0x0088843f  lea esi, [esp + 0x78]   ; ESI = a CÉLKERET
0x00888443  lea ecx, [esp + 0x60]   ; ECX = a kimenet (param_1)
0x0088844e  call 0x9b4aa0
```

⇒ a 175. kör ítélete (`ESI` = a cella = célkeret) **áll**, és az `EAX`
a méretezendő. Az `EAX`-rect szélessége/magassága a `[esp+0x90]`/`[esp+0x94]`
rekesz, amit közvetlenül a hívás előtt a `[esp+0xf8]`/`[esp+0xfc]`-ből
töltenek (`0x00888423`–`0x00888447`).

### 26.3 ⛔ ÖNHELYESBÍTÉS: a 24.2 olvasata FORDÍTOTT volt

A 174. kör így írta: *„**csak ha az nem nulla**, tölti a doboz W/H-ját."*
A dekompilátum és a diszasszembly szerint ez **fordítva** van:

```asm
0x00888404  mov eax, esi            ; ESI = &[esp+0x98] — a lekérdező szerkezet
0x00888406  push eax
0x00888407  call edx                ; virtuális hívás a panel [+0x270] objektumán
0x00888409  test eax, eax
0x0088840b  je  0x888423            ; ha NULLA -> a másolás KIMARAD
0x0088840d  mov eax, dword ptr [esp + 0x2c]   ; cellaSzél
0x00888411  mov ecx, dword ptr [esp + 0x44]   ; cellaMag
0x00888415  mov dword ptr [esp + 0xf8], eax
0x0088841c  mov dword ptr [esp + 0xfc], ecx
```

Vagyis a **cellaméret a TARTALÉK ág** (a virtuális hívás nem nulla
visszatérése = hiba), és a rendes úton a `[esp+0xf8]`/`[esp+0xfc]` azt
tartja, amit a virtuális hívás írt bele. A hívás a `&[esp+0x98]` mutatót
kapja, és **`0x98 + 0x60 = 0xf8`** — a két rekesz a kapott szerkezet
`+0x60`/`+0x64` mezője.

⇒ **az `EAX`-rect a FORRÁSKÉP mérete**, és ezzel a 25.4-ben kimondott
ellentmondás a **mérés** javára dől el (18.3: a tárolt doboz a forráskép
arányát viszi). A cellaméret-olvasat elvetve.

*Bizonyítottsági fok: a regiszter-szerepek és a tartalék-ág **megerősített**
(utasításszinten); az, hogy a virtuális hívott a KÉP méretét írja a
`+0x60`/`+0x64`-be, **erős** — az eltolás-egyezés és a kizárás támasztja alá
(a függvényben más nem írja ezt a két rekeszt), de a hívott függvényt nem
olvastuk el.*

### 26.4 K1 — KIMERÍTŐ NEGATÍV a kollázs-sávra, DEKOMPILÁTOR-szinten

Három, egymástól független pásztázás futott, mind a Ghidra
dekompilátumán (nem bájtmintán), a `+0x2c` bájteltolás **írására**:

| pásztázás | gyökér / tartomány | függvény | eredmény |
|---|---|---:|---|
| interaktív **képhozzáadás** | `0x0082a670`, 2 szint | **214** | **nulla** valódi `+0x2c`-írás (a 10 találat mind `+0x2c8`/`+0x2cd`/tömbindex/sztring-idióma) |
| **mentési** ág | `0x00834700`, 3 szint | **69** | **0 ÍRÓ · 1 OLVASÓ** — az egyetlen érintés a `FUN_008347b0` kiírása (26.1) |
| a **teljes kollázs-sáv** | `0x00829000`–`0x00895000` | **878** | 24 függvény ír `+0x2c`-re, és **egyik sem** csomópont-`scale`: két literál `0x3f800000` (= 1,0f) — `FUN_00885060` (`regulargrid`) és `FUN_00888210` (`contactsheet`) —, a többi egész, mutató vagy jelzőbit |

**A három „`+0x2c := +0x40`" másolás** (`FUN_0083d730:192`,
`FUN_0087b4a0:139`, `FUN_0088ac30:59`) **nem** csomópontra megy: mindhárom a
panel `[+0x270]` objektumán végez **állapot-mentést/visszaállítást**
(`+0x2c..+0x3c` ↔ `+0x40..+0x4c`), ld. `FUN_0087b4a0` a `FUN_0087bcb0`
hívása körül. A csomópont a fájlban 56 bájt (`0x38`) lépésközű, tehát
`+0x40` eleve kívül esne rajta.

⇒ **A kollázs-sávban EGYETLEN függvény sem ír számolt `scale`-t a
csomópont `+0x2c` mezőjébe.** Ez lényegesen erősebb, mint a 19./22./23. kör
bájtmintás negatívjai: ott a minta hibája is okozhatta a nullát (ezért
kellett pozitív kontroll), itt a dekompilátum szemantikai szintjén nézzük.

*Bizonyítottsági fok: **megerősített** a megnevezett hatókörre
(`0x00829000`–`0x00895000`, 878 függvény, Ghidra 12.1.2 dekompilátum).*

### 26.5 Ami ebből következik — és a KÖVETKEZŐ lépés, megnevezve

A három negatív együtt azt mondja, hogy **a `scale` írója a kollázs-sávon
KÍVÜL van**. A hatókör-számok:

- a program **20 608** függvényből áll (`binary-index`, `functions`);
- a sávban **878** van, azaz a program **4,3%-a** van kizárva;
- a sáv dekompilálása ≈ 20 perc ⇒ a teljes program ≈ **8 óra** — egy körbe
  nem fér bele.

**A következő, olcsóbb vágás** (ebben a sorrendben):

1. a **kollázspanel parancs-elosztójának** (`0x0082d570`) hívási fája 3
   szint mélyen — ide tartozik minden vezérlő kezelője, köztük a kézi
   átméretezés (17.5), ami a mintáinkban bizonyítottan `scale`-t módosít;
2. a **téma-objektumok** metódusai — az RTTI-tábla szerint
   `CContactSheetTheme`, `CPileTheme`, `CGridTheme`, `CFrameGridTheme`,
   `CMultiExposureTheme` (és a `CCollageUI` / `CHeadlessCollageUI`) —
   a `0x0082cad0`-analógia mentén;
3. csak ha ez sem hoz találatot: a teljes program pásztázása, több körre
   bontva (címtartományonként).

*Ez ÖRÖKÖLT nyitott kérdés (a 22. kör óta), a munkasorban marad.*

### 26.6 Nálunk (MÉRVE) — az illesztő BITRE egyezik

A `src/picasapy/collage/fitting.py:60–67` `fit_inside()`-ja pontosan a 26.2
képletét számolja, ugyanazokkal a konstansokkal (`_FIT_SLACK = 0.499`,
`_FIT_EPSILON = 1e-5`) és `picasa_round()`-dal (`floor(x + 0.5)`).

| | eredeti (`0x009b4aa0`) | nálunk (`fitting.py`) | teendő |
|---|---|---|---|
| nagyítás | `min((dstW+0,499)/srcW ; (dstH+0,499)/srcH)` | ugyanez | — |
| kimenet | `KEREK(z·srcW + 1e-5)` | `picasa_round(scale*src_width + 1e-5)` | — |
| kerekítés | `floor(x+0,5)` | `math.floor(value + 0.5)` | — |

⇒ **nincs teendő ezen a ponton.** A 26.2 értéke nem javítás, hanem az, hogy
a képlet mostantól **dekompilátumból** igazolt, nem mintából illesztett.

*Bizonyítottsági fok: **megerősített** (a kód olvasva, a konstansok a
binárisból kiolvasva).*

## 27. ⛔ ÖNHELYESBÍTÉS: a 26.4 negatívja TÚL ERŐS volt — a pásztázó VAK volt az index-alakra (2026-09-07, #1412)

*Ugyanaz a bináris és eszközkészlet, mint a 26.-ban (Ghidra 12.1.2,
`Picasa3.exe` SHA-256 `644b7bec…dc96`).*

### 27.1 Mi dőlt meg, és MI döntötte el

A 26.4 azt állította, hogy a kollázs-sáv **878 függvényéből egyik sem** ír
float-ot a csomópont `+0x2c` mezőjébe. **Ez nem áll.** A csomópont értékadó
operátora, `FUN_008341b0` (`0x008341b0`, 252 bájt) — a sávon **belül** —
pontosan ezt teszi:

```asm
0x00834258  fld  dword ptr [esi + 0x28]
0x0083425b  fstp dword ptr [ebx + 0x28]      ; theta
0x00834261  fld  dword ptr [esi + 0x2c]
0x00834264  fstp dword ptr [ebx + 0x2c]      ; scale
```

A 26.4 listája ezt **nem tartalmazza**, és nem is dekompilációs hiba miatt:
a `collage-band.txt`-ben a `008341b0` **nulla** alkalommal fordul elő, a
sikertelen dekompilációk száma pedig **0**.

**A mechanizmus:** a pásztázó szövegmintája csak a **bájteltolásos** alakot
ismerte (`+ 0x2c)`, `+ 0x2c +`, `0x2c + `). A Ghidra ezt a másolást
**index-alakban** írja ki — `0x2c / 4 = 11` —, szó szerint így:

```c
param_1[0xb] = unaff_ESI[0xb];
```

⛔ **A hiba gyökere módszertani, nem szövegtani:** a pásztázást **nem
ellenőriztem ismert pozitívval**, pedig a 19. kör óta tudjuk, hogy épp ez a
függvény másolja a `+0x2c`-t. A saját szabályunk („üres pásztázást ismert
pozitívval ellenőrizz") pontosan erre való, és kimaradt.

### 27.2 A JAVÍTOTT pásztázás — és most már ÉRVÉNYES

A detektor három írásalakot ismer: **BAJT** (`+ 0x2c`), **INDEX**
(`[0xb]` / `[11]`) és **MEZO** (`field_0x2c`). A futás csak akkor érvényes,
ha a kimenetben ott a `FUN_008341b0` — ez a **kötelező pozitív kontroll**.

| | 26.4 (régi) | **27. (javított)** |
|---|---:|---:|
| megnézett függvény | 878 | **878** |
| dekompilációs hiba | 0 | **0** |
| `+0x2c`-írás, BAJT-alak | (24 függvény) | **37 írás** |
| `+0x2c`-írás, INDEX-alak | **0 — VAK FOLT** | **37 írás** |
| `field_0x2c`-alak | nem nézte | **0** |
| pozitív kontroll | **nem volt** | **MEGVAN, a futás érvényes** |

⇒ **a keresés fele hiányzott.** A 26.4 negatívját ezért **visszavonom**; ami
belőle áll, az annyi, hogy a **bájteltolásos** alakban nincs számolt
`scale`-írás a sávban.

### 27.3 ⚠️ Az INDEX-alak NEM automatikusan `+0x2c` — a bázist ellenőrizni kell

A `[0xb]` csak akkor jelent `+0x2c`-t, ha a mutató a **tárgy bázisa**. A
`FUN_008921a0` (`0x008921a0`) ellenpélda: ott
`puVar17 = (undefined4 *)(iStack_84 + 0x10)`, tehát a `puVar17[0xb]`
valójában **`+0x3c`**. A 37 INDEX-találat tehát **jelölt, nem bizonyíték**;
mindegyiknél külön kell megnézni, mi a bázis.

### 27.4 ⛔ AMIT KIZÁRTAM — a `+0xf8 → +0x2c` másolás NEM a csomóponté

A javított lista legígéretesebb tétele a `FUN_008378c0` (`0x008378c0`,
1397 bájt) volt, mert **pont a keresett alakot** mutatta — egy számolt mező
átmásolása a `+0x2c`-be, „piszkos" jelzővel:

```c
param_2[0x16] = param_3[0x3f];          // +0x58 := +0xfc
if (param_2[0xb] != param_3[0x3e]) {    // +0x2c != +0xf8
  *(undefined1 *)(param_2 + 0x17) = 1;  // „megváltozott" jelző
  param_2[0xb] = param_3[0x3e];         // +0x2c := +0xf8
}
…
param_2[9]  = param_3[0x3b];            // +0x24 := +0xec
param_2[10] = param_3[0x3c];            // +0x28 := +0xf0
```

A mezősorrend (`+0x24`, `+0x28`, `+0x2c`) csábítóan egyezik a csomópontéval
(`h`, `theta`, `scale`) — **de a forrás nem geometria.** A `param_3`
osztályának `+0xf8` mezőjét a `FUN_00836510` (`0x00836510`, 424 bájt) tölti,
és az egy **gyorsítótár-kulcs hash**:

```c
uVar5 = 0x12345678;                       // a hash magja
while (cVar2 != '\0') { uVar5 = uVar5 ^ uVar5 * 0x20 + (uVar5 >> 2) + cVar2; … }
uVar4 = uVar4 ^ uVar5;
param_2[0x3e] = uVar4;                    // +0xf8 := a hash
```

ugyanabban a függvényben egy `"%d:%d:%d:%d"` kulcs-sztringgel
(`param_2[0x13]`, `[0x12]`, `[0x3b]`, `[0x3c]`). Mindkét objektum ugyanazt a
zárolási idiómát viseli (`[8]` = szálazonosító, `[9]` = rekurziószám,
`+0x28` = `CRITICAL_SECTION`) ⇒ a **bélyegkép-gyorsítótár** osztálya
(az RTTI-ban `CCollageBitmapProvider`), **nem** a kollázs-csomópont.

⇒ **elvetve**; a `+0x2c` ott egy gyorsítótárazott hash mezője, a
mezőegyezés véletlen.

### 27.5 Hol tart a K1, és mi a KÖVETKEZŐ lépés

**Ami áll:** a `.cxf` `scale`-jét a mentési ág csak **olvassa** (26.1), a két
elrendező feltétel nélkül `1,0`-t ír (22.), és a bájteltolásos alakban nincs
számolt író a sávban (26.4, szűkített hatókörrel).

**Ami MEGDŐLT:** hogy a sávban egyáltalán nincs `+0x2c`-író — 37 INDEX-alakú
írás van, amit a régi minta nem látott.

**A következő lépés, megnevezve:** a 37 INDEX-találat **bázisának**
egyenkénti tisztázása (27.3), és azok kiszűrése, amelyek nem 56 bájtos
csomópontra mutatnak. A `FUN_008341b0` (értékadó operátor), a
`FUN_00835520`, a `FUN_00838d10` és a `FUN_0084c7b0` **másol** — ezek a
láncot viszik tovább, nem az értéket állítják elő; a forrás felé kell menni.

*Bizonyítottsági fok: a 27.1 önhelyesbítés **megerősített** (a
diszasszembly és a régi kimenet együtt); a 27.2 javított számok
**megerősítettek** (pozitív kontrollal); a 27.4 kizárás **erős** (a hash
képlete és a közös zárolási idióma).*

## 28. A LÁTSZÓLAGOS ELLENTMONDÁS FELOLDVA: az elrendező IDEIGLENES vektorba ír (2026-09-07, #1412)

*Ez a szakasz **Codespace nélkül** készült: helyi capstone-pásztázás a
bináris-index függvényhatárain, `eszkozok/pe_dis.py`. A pásztázások
pozitív kontrollja külön ki van mondva.*

### 28.1 A kérdés, ami a 22. kör óta nyitva állt

A `contactsheet` elrendező **feltétel nélkül `1,0`-t** ír a csomópont
`+0x2c`-jébe (22.: `0x008885ac fld1` → `0x008885bc fstp [ebx+eax+0x2c]`), a
mentett `.cxf`-ben mégis `313` / `500` / `256` / `158` áll (17.15). Öt kör
kereste, ki írja felül — és a 26./27. kör kimutatta, hogy a sávban csak
**másolók** vannak.

**A feloldás: a kettő nem ugyanaz a tömb.**

### 28.2 A bizonyíték — utasításszinten

A `.cxf`-író (`FUN_008347b0`) a **dokumentum** `+0x48` mezőjéből veszi a
csomópont-tömb bázisát, és `bázis + csomópont-eltolás + mező` alakban olvas
(a 26.1 mezőtérképe így **címzés-szinten is** igazolt):

```asm
0x00834c2d  mov edx, dword ptr [ebx + 0x48]     ; ebx = a dokumentum
0x00834c3f  fld dword ptr [eax + edx + 0x18]    ; x
0x00834d26  fld dword ptr [edx + ecx + 0x1c]    ; y
0x00834e09  fld dword ptr [edx + ecx + 0x20]    ; w
0x00834eec  fld dword ptr [edx + ecx + 0x24]    ; h
```

⇒ **nincs eltolás-delta**: a `+0x2c` tényleg a `scale`.

Az elrendező hívója viszont **veremlokálist** ad át neki, és a hívás után
**el is pusztítja**:

```asm
0x00887b93  lea  ecx, [esp + 0x18]      ; a LOKÁLIS vektor
0x00887b97  push ecx                    ; -> FUN_00888210 param_2
0x00887b98  push esi                    ; -> param_1 (a téma-objektum)
0x00887b99  call 0x888210               ; a contactsheet-elrendező
0x00887b9e  lea  esi, [esp + 8]
0x00887ba4  call 0x62d010               ; a vektor PUSZTÍTÓJA
```

ugyanez a korábbi ágon is (`0x00887b48` `lea esi,[esp+8]` →
`0x00887b4c call 0x62d010`).

⇒ **az elrendező `1,0`-ja egy ideiglenes vektorba megy, és a függvényből
kilépve megsemmisül.** A mentés a dokumentum `[+0x48]` tömbjét írja ki —
**egy másik tömböt**.

*Bizonyítottsági fok: **megerősített** (mindkét idézet utasításszintű).*

### 28.3 Amit ez ÉRVÉNYTELENÍT, és amit MEGHAGY

| állítás | mi lett vele |
|---|---|
| „az elrendező `1,0`-t ír, a fájlban mégis `313` van ⇒ valami FELÜLÍRJA" | ⛔ **a következtetés hibás** — nem felülírás, hanem **két külön tömb** |
| a 22. `fld1` megfigyelés | ✅ **áll**, csak az ideiglenes vektorra vonatkozik |
| a 26.1 mezőtérkép (`+0x18` x … `+0x2c` scale) | ✅ **megerősítve**, most már címzés-szinten is |
| a 26.4/27. „nincs számolt `scale`-író a sávban" | ✅ **áll** (a 27. hatókör-javításával) — és most már **érthető is**: a keresés a rossz tömbre irányult |

⇒ **A 19. kör szerkezeti sejtése (»van egy visszamásolás«) IGAZOLT.**

### 28.4 A pásztázások és a kontrolljuk

| pásztázás | mit keresett | eredmény | pozitív kontroll |
|---|---|---:|---|
| `+0x48` **olvasói** a sávban (`esp`/`ebp` bázis kizárva) | a dokumentum-mező olvasói | **106** függvény | **`FUN_008347b0` MEGVAN** ⇒ a pásztázó helyes |
| `+0x48` **írói** | ki tölti a tömb-bázist | **47** függvény | (a kontroll itt helyesen HIÁNYZIK: az író nem olvasó) |
| `+0x48` ÉS `+0x38`/`+0x3c`/`+0x40` együtt | **dokumentum-alakú** tárgyra írók | **16** függvény | — |

A 16-ból a `+0x48`-at **dword**-ként írók (a `.cxf`-író így olvassa):
`0x00829d60`, `0x00829dc0`, `0x0082a250`, `0x00832500`, `0x00838ef0`,
`0x0084bb30`, `0x0085ff90`, `0x00865890`, `0x008833b0`, `0x0088b0a0`.
A `byte`-ként írók (`0x0083d730`, `0x0087b4a0`, `0x0088ac30`, `0x0088db10`,
`0x0088e4e0`, `0x008906e0`) **más osztályhoz** tartoznak.

### 28.5 A KÖVETKEZŐ lépés, megnevezve

A kérdés innentől **pontosabb**, mint eddig bármikor:

> **Ki tölti fel a dokumentum `[+0x48]` csomópont-tömbjét, és a `+0x2c`-t
> ott honnan veszi?**

A sorrend:

1. a 28.4 tíz `dword`-írójából azonosítani a **kollázs-dokumentum**
   konstruktorát/feltöltőjét (a `0x00832500` kiemelt jelölt: `+0x3c`-be
   nem nullát, hanem `2`-t ír, tehát verzió/típus mező);
2. onnan a **`collagepanel/cnode_` elemek visszaolvasása** — a 19. kör
   szerint ez a hiányzó láncszem, és a `FUN_00888b40` (az elemkészítő)
   maga is ír `[esi+0x48]`-at (`0x00888ce2`);
3. a csomópont értékadó operátorának (`FUN_008341b0`) **tizenkét hívója**
   közül az, amelyik a dokumentum tömbjébe másol — a lista:
   `0x00833920` · `0x00833cf0` · `0x008342b0` · `0x0083dfa0` · `0x0083e280` ·
   `0x0083e560` · `0x0087b4a0` · `0x0087dcd0` · `0x0087e960` · `0x00880580` ·
   `0x00884a90` · `0x00887e50`.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*
