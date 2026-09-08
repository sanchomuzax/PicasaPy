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

## 29. K1 — a staging `+0x68` SIB-alakú írása is kizárva, és egy ÖNHELYESBÍTÉS a kör módszeréről (2026-09-07, #1412)

*181. kutatói kör. A kör a munkasor K1 tételét vette elő. **A leletek
zöme NEM új** — ezt a szakasz elején ki kell mondani, mert a kör
módszertani hibát követett el (29.3).*

### 29.1 ⭐ A `+0x68` (staging `scale`) írásának SIB-alakja — 1 találat, KIZÁRVA

A 17.10/b pásztázása a burkoló `+0x68` mezőjének **mutatós** alakját
mérte ki (`[reg + 0x68]`, `esp`/`ebp` nélkül), és a hatókörét ki is
mondta. A **SIB-alak** (`[reg + reg + 0x68]`) abból a mintából kimaradt —
ugyanaz a rés, amit a `+0x2c`-nél a 17.15 zárt be.

**Most bezárva.** Utasításszintű pásztázás (capstone, a bináris-index
20 608 `.text`-függvénye, ~28 mp), `fst`/`fstp dword ptr` bármely
`+0x64`/`+0x68` memóriaoperandusra, `esp`/`ebp` bázis kizárva:

| cím | függvény | alak | ítélet |
|---|---|---|---|
| `0x00832fc2` | `FUN_0082fab0`-tartomány | `fstp [ebx+0x68]` | az **alapérték** 1,0 (17.16) |
| `0x008332b7` | a `.cxf`-beolvasó | `fstp [ebx+0x68]` | **pozitív kontroll** ✅ |
| `0x0088de20` | `FUN_0088dde0` (177 b) | **`fst [edx+eax+0x68]`** | **KIZÁRVA**, ld. lent |
| `0x00414821` · `0x007fba19` | — | mutatós | sávon kívül (17.10/b) |

**A `0x0088de20` kizárása tartalmi, nem hívási úton.** A `FUN_0088dde0`
egy `fldz`-vel kezdődő, négyszeresen kigöngyölt nullázó ciklus: a
lépésköz `0x50` (**80 bájt**, `0x0088de2b add edx, 0x140` = 4 × 0x50),
és minden menetben a `+0x18` / `+0x1c` / `+0x20` / `+0x24` mezőket írja
nullára. A `+0x68` ott a **következő elem `+0x18`-a**
(`0x50 + 0x18 = 0x68`). A kollázs-csomópont lépésköze **56 bájt**
(`0x38`, 26.1) ⇒ **más tömb, más osztály**.

⇒ A 17.10/b negatívja ezzel a SIB-alakra is áll: **a `scale` staging
mezőjének sincs számoló írója.**

*Bizonyítottsági fok: **megerősített** (utasításszintű pásztázás pozitív
kontrollal + a jelölt teljes törzsének elolvasása).*

### 29.2 A friss `.cxf`-minták csomópontszáma FÁJLBÓL ellenőrizve

A 17.15 figyelmeztetése — *„a képlet illesztése előtt a három `.cxf`-ben
meg kell számolni a csomópontokat"* — teljesítve. A NAS közös mappájából
(`1412-kollazs-index-kepek/`, 2026-09-05) beolvasva:

| minta | `format` / tájolás | csempe | csomópont | `scale` |
|---|---|---|---|---|
| `AI27.cxf` | `297:210` álló | `noborder` | **4** | 500 |
| `AI28.cxf` | `4:3` fekvő | `whiteborder` | **6** | 256 |
| `AI29.cxf` | `13:9` fekvő | `polaroid` | **12** | 158 |
| `AI6.cxf` | `4:3` álló | `whiteborder` | **9** | 313 |

A 18.4/18.6 táblái ezekkel egyeznek — a tulajdonos jelöletlen
`4→500, 6→256, 9→313, 12→158` párosítása **helyes volt**. A minták
mellett a rendereltek is megvannak (`AI27.jpg` 3621 × 5120,
`AI28.jpg` 5120 × 3840, `AI29.jpg` 5120 × 3544) — a hosszabb oldal
mindháromnál **5120 = 5 × 1024** képpont.

### 29.3 ⛔ ÖNHELYESBÍTÉS — a kör a MEGLÉVŐ ANYAGOT nem nézte meg elsőnek

A kör a `.cxf`-mintákból önállóan levezette a rácsképletet
(0,06 / 0,15 margó, 0,88 / 0,79 cella), a `scale` szerepét (a cellába
való függőleges középre igazítás magassága) és a lapmagasság
`CSONK(1024·H/W)` egységét — **mind a három már benne állt a 18.2 · 18.4 ·
18.5 szakaszban**, ugyanezen a négy mintán, ugyanezekkel a címekkel.

**A hiba helye pontosan megnevezhető:** a kör a 2. szakasz lépéssorát
(„meglévő anyag → index → dekompiláció") nem a `docs/specs/` **aznapi**
állapotán kezdte, hanem a munkasor és a `HOL-TARTUNK.md` összefoglalóján —
azok viszont a 17. szakasz állapotát tükrözik, a 18–28. szakaszét nem.
Egy `grep -n "^## " docs/specs/kollazs-eletciklus.md` másodpercekbe telt
volna.

**Amit ez a jövőre nézve előír:** ha a munkasor egy tétele egy
spec-lapra mutat, a kör **a lap tartalomjegyzékét olvassa el elsőnek**, ne
az összefoglalót. Az összefoglaló elavulhat; a lap nem.

### 29.4 A K1 állapota változatlan — a következő lépés a DRÁGA út

A 23.5 kizárás-táblája a 29.1-gyel egészül ki (SIB-alakú `+0x68`-írás).
Az olcsó lánc **kimerült**; a megnevezett következő lépés
(`HOL-TARTUNK.md` / 28.5) továbbra is a **dekompilátoros kör**:
a `FUN_008347b0` veremkerete (a 17.11 ↔ `0x00834c2d` ellentmondás), majd
a `0x0082a670` kollázspanel képhozzáadási ága.

## 30. K1 — a 18.4 képlete UTASÍTÁSSZINTEN megvan, és ebből ÚJ, éles ellentmondás lett (2026-09-07, #1412)

*182. kutatói kör. A 18.4 két elrendezési képlete eddig **mérésből** jött
(31/31 csomópont); ez a szakasz a `FUN_00888210` csomópont-ciklusát olvassa
végig utasításonként, és a képletet a **kódból** adja meg. A melléktermék
fontosabb, mint a fő eredmény: kiderül, hogy a kód ugyanazzal a mennyiséggel
igazít középre, amit `h`-ként el is tárol — a mintáink viszont **nem**
ezzel igazítanak.*

### 30.1 ⭐ A csomópont-ciklus, utasításonként (`0x008883c0`–`0x008885c0`)

Bemenetek a cikluson kívülről: `[esp+0x2c]` = cellaSzél, `[esp+0x44]` =
cellaMag, `[esp+0x40]` = balMargó, `[esp+0x3c]` = felsőMargó,
`[esp+0x18]` = **rés** (`CSONK(0,08 · k)`, 18.2), `[esp+0x48]` = W,
`[esp+0x4c]` = H.

```
edi = rés                                   ; 0x008883c0
call 0x9b4aa0                               ; 0x0088844e — arány-tartó illesztés
                                            ; kimenet: [esp+0x60..0x6c] = (0, 0, wf, hf)
[esp+0x60] += rés ; [esp+0x64] += rés       ; 0x00888465 / 0x0088846d
[esp+0x68] -= rés ; [esp+0x6c] -= rés       ; 0x00888463 / 0x0088846f
w_kép = wf − 2·rés                          ; 0x0088846b  sub eax, edx
h_kép = hf − 2·rés                          ; 0x00888484  sub ecx, esi
ecx = (cellaSzél − w_kép) >> 1              ; 0x008884a1  sar ecx, 1
esi = (cellaMag  − h_kép) >> 1              ; 0x008884a9  sar esi, 1
sor, oszlop = div( csomópontIndex, oszlopszám )   ; 0x008884bc
x_px = oszlop·cellaSzél + ecx + balMargó    ; 0x008884c7–0x008884ce
y_px = sor·cellaMag    + esi + felsőMargó   ; 0x00888512–0x0088851d
csomópont+0x18 = x_px / W                   ; 0x00888556
csomópont+0x1c = y_px / H                   ; 0x00888568
csomópont+0x20 = w_kép / W                  ; 0x008885ae
csomópont+0x24 = h_kép / H                  ; 0x008885b6
csomópont+0x2c = 1,0  (fld1)                ; 0x008885ac → 0x008885bc
```

⇒ **A 18.4 két képlete ezzel kódra van vezetve.** A `(cellaMag − X) / 2`
tag szó szerint a `sar esi, 1` a `0x008884a9`-en; az egészosztás nem
feltevés, hanem aritmetikai jobbra tolás. Ugyanígy a vízszintes tag a
`sar ecx, 1` a `0x008884a1`-en.

*Bizonyítottsági fok: **megerősített** — helyi diszasszemblálás
(`eszkozok/pe_dis.py` + capstone), minden lépés címmel.*

### 30.2 ⛔ AZ ÚJ ELLENTMONDÁS: a kód ugyanazzal igazít, amit tárol — a fájl NEM

A ciklusban **egyetlen** `h_kép` van, és **kétszer** használódik: egyszer a
függőleges középre igazításhoz (`esi`), egyszer a csomópont `h` mezőjéhez.
Ha a mintáink ebből a menetből származnának, akkor a `.cxf` `y`-ját a
tárolt `h`-val vissza lehetne számolni.

**Nem lehet.** A `scale`-lel viszont igen — 10/10 sorra, kivétel nélkül:

| minta | sor | cellaMag | felsőMargó | y a `scale`-lel | y a tárolt `h`-val | MÉRT y |
|---|---:|---:|---:|---:|---:|---:|
| AI6 | 0 · 1 · 2 | 359 | 204 | **227 · 586 · 945** | 232 · 591 · 950 | 227 · 586 · 945 |
| AI27 | 0 · 1 | 571 | 217 | **252 · 823** | 279 · 850 | 252 · 823 |
| AI28 | 0 · 1 | 303 | 115 | **138 · 441** | 156 · 459 | 138 · 441 |
| AI29 | 0 · 1 · 2 | 186 | 106 | **120 · 306 · 492** | 123 · 309 · 495 | 120 · 306 · 492 |

Az eltérés a `h`-s ágon **3–27 lapegység** — nagyságrendekkel a kerekítési
zaj fölött. *(Mérőszkript: a kör `kozepre_igazitas.py`-ja; a bemenet a négy
arany `.cxf`, a képletek a 18.2/18.3 csonkolásaival.)*

**Független második jel, ugyanerre:** a rés-levonás **elrontja a
képarányt** (`(wf−2r)/(hf−2r) ≠ wf/hf`), a tárolt dobozok viszont a
forráskép arányát **0,001 lapegység** pontossággal viszik (18.3). Tehát a
tárolt `w`/`h` nem lehet a rés-levont téglalap.

### 30.3 ⭐ Amit ez KIMOND — és az ÚJ keresési kulcs

A két jel együtt csak egyféleképpen áll össze:

> **Az elrendezés UTÁN egy másik menet ÁTÍRJA a csomópont `w`/`h` mezőjét**
> (a rés nélküli, arány-tartó dobozra), **az elrendező saját
> doboz-magassága pedig a `+0x2c`-be kerül** — ezt látjuk `scale`-ként.
> Az `y` közben változatlan marad, ezért őrzi az EREDETI magasságot.

Ez megmagyarázza a 18.5 „lap-szintű magasság" megfigyelését is: a
`scale` azért csomópont-független, mert az elrendező **cellánként azonos**
doboz-magassággal dolgozik, a kép viszont csomópontonként más.

⇒ **ÚJ KERESÉSI KULCS a hiányzó íróhoz.** Minden eddigi pásztázás a
`+0x2c`-t **magában** kereste (17.7, 17.10, 19.2, 22.1, 23.3, 26.4, 27.2,
29.1). A keresett menet viszont **együtt** írja a `+0x20`-at, a `+0x24`-et
és a `+0x2c`-t ugyanazon az 56 bájtos elemen. Ez a **konjunkció** eddig
egyetlen pásztázásban sem szerepelt — sem bájtmintásban, sem a
dekompilátumon (26.4 a `+0x2c`-írókat listázta, nem a hármas együttállást).

*Bizonyítottsági fok: a 30.2 két jele **megerősített** (számolás a
mintákon, illetve a 18.3 mérése); a 30.3 következtetése **erős** — a két
jelet egyszerre más magyarázat nem fedi, de az átíró menetet még nem
azonosítottuk.*

### 30.4 ⭐ A HÁRMAS KONJUNKCIÓ PÁSZTÁZÁSA LEFUTOTT — és NEGATÍV

*A 30.3 új kulcsát ugyanez a kör le is futtatta, nem hagyta következő
körre.* Pásztázás a bináris-index **20 608** `.text`-függvényén (capstone,
~30 mp): olyan függvény, amely `+0x20`, `+0x24` **és** `+0x2c` mind a
hármat írja 4 bájtos memóriaoperandusra, `esp`/`ebp` bázis nélkül.
**Pozitív kontroll: a `FUN_00888210` szerepel a találatok közt** ✅
(`0x008885ae` · `0x008885b6` · `0x008885bc`).

| szűrő | darab |
|---|---:|
| hármas konjunkció, bármilyen írásmóddal | **212** |
| ebből a `+0x2c` **lebegőpontos** (`fst`/`fstp`/`movss`) | **36** |
| ebből a kollázs-sávban (`0x00829000`–`0x00895000`) | **9** |
| ebből a sávon kívül, de a **sávból hívva** (`xrefs`) | **1** |

**A kilenc sávbeli mind besorolt** (egyik sem számol `scale`-t): a két
téma-elrendező (`0x00885060`, `0x00888210` — `fld1`), két **másoló**
(`0x008341b0` értékadó, és lásd lent), a nyomtatás két függvénye
(`0x00860f60`, `0x00861190` — 17.15), valamint három nullázó/−1,0
inicializáló (`0x00829770`, `0x0088e7e0`, `0x008910b0` — 17.15).

**A 27 sávon kívüliből `xrefs` szerint EGYETLENT hív a sáv:**
`FUN_009dd800` (926 b; hívói `0x0085fd60`, `0x0087c820`, `0x0088ae30`).
**Elolvasva, tartalmilag KIZÁRVA:** konstruktor, amely a `[esi]`-be a
`0xcda8cc` vtáblát írja, és két ciklusban nulláz — a lépésköz
`0x4c` (**76 bájt**, `0x009dd859` / `0x009dd8a8` `add …, 0x4c`), tehát a
`+0x2c` ott a 76 bájtos elem saját mezője. A kollázs-csomópont **56**
bájtos (26.1) ⇒ más osztály.

⇒ **A hármas kulcs sem hoz számoló írót.** Ez a 26.4 dekompilátoros
negatívjától független megerősítés, és a sávon kívülre is kiterjed
(hívási úton).

### 30.5 ⭐ Melléklelet: `FUN_0087b830` = a csomópont MÁSOLÓ KONSTRUKTORA

A pásztázás egy eddig be nem sorolt sávbeli függvényt is felszínre hozott.
Végigolvasva (141 b, `0x0087b830`–`0x0087b8bc`): mezőről mezőre másol a
`[edi]`-ből a `[esi]`-be — `+0` · `+4` · `+8` · `+0x10` · `+0x14` ·
`+0x18` · `+0x1c` · `+0x20` · `+0x24`, majd `fld`/`fstp` a `+0x28` és a
`+0x2c` párra, végül `+0x30` és `+0x34`. A `+0`, `+4` és `+0x30`
mezőkre **hivatkozásszám-növelés** fut (`movzx`/`cmp 0x80`/`call [0xc40560]`)
⇒ ezek **hivatkozásszámlált sztringek**.

⇒ Ez a **csomópont másoló konstruktora**, és harmadik oldalról igazolja a
26.1 mezőtérképét: az elem `0x38` (56) bájtos, a `+0x28`/`+0x2c`
lebegőpontos (`theta`/`scale`), a `+0`/`+4`/`+0x30` sztring.
**Nem számol** — a láncot viszi, mint a `FUN_008341b0`.

### 30.6 A KÖVETKEZŐ lépés, megnevezve

A 30.4 negatívja után a keresés iránya: **nem a mezőt kell keresni, hanem
a FORRÁS-csomópontot.** A sávban két másoló van (`0x008341b0` értékadó,
`0x0087b830` másoló konstruktor); ha a `scale` a modellbe kerül, valamelyik
**forrás-oldalán** kell megjelennie.

1. A `0x0087b830` **hívóinak** végigolvasása (`xrefs`) — melyikük épít
   olyan ideiglenes csomópontot, amelynek a `+0x2c`-je nem 1,0;
2. utána a 26.5 két vágása (`0x0082d570` parancs-elosztó három szinten,
   illetve a téma-objektumok metódusai).

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

**Eszközök** (privát `picasapy-agent`): a konjunkció-pásztázó
`eszkozok/binaris/mezo_konjunkcio.py`, a középre-igazítás mérője
`eszkozok/binaris/kozepre_igazitas.py`.

## 31. K1 — a `scale` KÉPLETE a bináris saját aritmetikájával, és három lezárt kizárás (2026-09-07, #1412)

*183. kutatói kör. A 30.6 megnevezett lépését viszi (a másoló konstruktor
hívói), és közben három olyan kizárást zár le, amit eddig senki nem
ellenőrzött.*

### 31.1 ⭐ Az elrendezés-konstansoknak PONTOSAN két hivatkozója van

Ha egy KÉSŐBBI menet **újraszámolná** a doboz-magasságot, ugyanezekre a
konstansokra kellene hivatkoznia. Bájtmintás keresés a teljes `.text`-en
(fájloffszet `4096`, `8 646 656` bájt), minden találat capstone-nal
ellenőrizve, hogy valódi operandus-e:

| konstans | VA | valódi hivatkozás | hol |
|---|---|---:|---|
| **0,88** | `0x00d3a140` | **2** | `0x008880a0` (`FUN_00887e50`) · `0x00888305` (`FUN_00888210`) |
| **0,79** | `0x00d3a144` | **2** | `0x008880ef` (`FUN_00887e50`) · `0x00888347` (`FUN_00888210`) |
| **0,08** (rés) | `0x00cf4df0` | **1** | `0x008882d4` (`FUN_00888210`) |
| 0,15 | `0x00cf3fd0` | 8 | ebből egy a `FUN_00888210` |
| 0,06 | `0x00cf46d0` | 2 | `FUN_00888210` és `FUN_00b148e0` |

⇒ **A cellaméretet és a rést a programban csak a rácsszámoló és az
elrendező állítja elő.** Ha a `scale` egyenlő a doboz-magassággal
(30.2), akkor azt **nem lehet máshol újraszámolni** — az értéket
**vinni** kell.

*Bizonyítottsági fok: **megerősített** (teljes `.text`, utasításszintű
ellenőrzéssel).*

### 31.2 A `FUN_00888210` MINDEN vermen kívüli írása — a teljes lista

| cím | írás |
|---|---|
| `0x00888556` · `0x00888568` | csomópont `+0x18` (`x`) · `+0x1c` (`y`) |
| `0x008885ae` · `0x008885b6` | csomópont `+0x20` (`w`) · `+0x24` (`h`) |
| `0x008885bc` | csomópont `+0x2c` ← **`fld1`** (1,0) |
| `0x0088883b`–`0x0088885b`, `0x0088897b`–`0x00888989` | két 4-dwordös téglalap (`[ecx]`…`[ecx+0xc]`) — cím/alcím |
| `0x0088894f`, `0x00888ac3` | `byte [esi+0x33d] = 1` — jelzőbit |

⇒ **A doboz-magasság a függvényből csak a `+0x24` és a `+0x1c` mezőn át
juthat ki.** Más kimenete nincs.

### 31.3 A „`+0x24`-et olvas ÉS `+0x2c`-t ír" pásztázás — NEGATÍV

A 30.3 alakja konstans nélkül is megvalósítható: a menet a csomópont
**saját `+0x24`**-éből (ami akkor még a doboz-magasság) veszi a `scale`-t.
Pásztázás a 20 608 `.text`-függvényen erre a konjunkcióra (olvas `+0x24`,
ír `+0x2c`, és írja a `+0x20`/`+0x24`-et is): **42 jelölt**, jelenléti
próbával (a másoló konstruktor `FUN_0087b830` szerepel ✅). Ebből **9 a
kollázs-sávban**, és mind besorolt:

- **lebegőpontos `+0x2c`-írás a sávban összesen NÉGY függvényben van:**
  a két téma-elrendező (`0x00885060`, `0x00888210` — konstans 1,0) és a
  két másoló (`0x008341b0` értékadó, `0x0087b830` másoló konstruktor).
  A többi sávbeli találat (`0x0088e4e0`, `0x008906e0`, `0x00891060`,
  `0x008921a0`, `0x0083d730`, `0x0084c7b0`) a `+0x2c`-be **egészet** ír.
- **Az egyetlen új sávbeli jelölt, `FUN_00839200` (282 b), elolvasva és
  KIZÁRVA:** egy nagyobb objektum másoló konstruktora (`+0`…`+0x45`, majd
  a `+0x48`-as vektor másolása a `0x0083dfa0`-val); a `+0x2c` ott
  **hivatkozásszámlált sztring** — a `0x00839298`-on ref-count hívás megy rá.

### 31.4 ⭐ A „talán másik modulban van" kifogás LEZÁRVA

Eddig kimondatlanul feltettük, hogy a kollázs kódja a `Picasa3.exe`-ben
van. A tulajdonos telepítési mappájának mentése (NAS, 2026-09-05) szerint
a teljes futtatható készlet:

| fájl | méret | mi |
|---|---:|---|
| `Picasa3.exe` | 10 160 456 | a program (a 26. szakasz SHA-jával egyező méret) |
| `Picasa3i18n.dll` | 26 904 904 | honosítási **erőforrás**-DLL |
| `PicasaPhotoViewer.exe` | 4 806 984 | külön képnézegető |
| `MovieThumb.exe` | 715 080 | videó-bélyegkép |
| `uninstall.exe` | 212 240 | eltávolító |
| `qtsupport.dll` | 100 680 | QuickTime-támogatás |
| `npPicasa3.dll` | 59 720 | böngésző-bővítmény |
| `plugins/Red.dll` | — | vörösszem-bővítmény |

⇒ **Nincs olyan modul, amelybe a kollázs-elrendezés kiszervezhető volna.**
A keresés hatóköre helyes; a negatívokat nem magyarázza el egy DLL.

### 31.5 ⭐ A `scale` A BINÁRIS SAJÁT ARITMETIKÁJÁVAL — 0…2 egység, és a maradék NEM a mi hibánk

A 26.2 illesztő-képletét **egyszeres pontosságú** (float32) aritmetikával,
a **valódi forrásképek** méretével kiszámolva, a 30.1 rés-levonásával:

| minta | cella | rés | illesztett magasság | doboz = illesztett − 2·rés | fájl `scale` | eltérés |
|---|---|---:|---:|---:|---:|---:|
| AI6 | 300 × 359 | 24 | 359 (9/9 csomóponton) | **311** | 313 | −2 |
| AI27 | 450 × 571 | 36 | 571 (4/4) | **499** | 500 | −1 |
| AI28 | 300 × 303 | 24 | 303 (6/6) | **255** | 256 | −1 |
| AI29 | 225 × 186 | 14 | 186 | **158** | 158 | **0** |

**Két dolog derül ki ebből, és mindkettő új:**

1. ⭐ **A doboz-magasság csomópont-FÜGGETLEN — és most már tudjuk, MIÉRT.**
   A 19 kimért csomópont forrásképe hat különböző méretű
   (`960×1200`, `816×1456`, `832×1456`, `768×1536`, `896×1344`), és az
   illesztett magasság **mindegyiknél ugyanaz**. Az ok: mind **álló**, tehát
   az illesztés **magasság-korlátos**, és ilyenkor `z·forrMag = cellaMag +
   0,499` — a forrásképtől függetlenül. Ez magyarázza a 18.5 „lap-szintű
   magasság" megfigyelését, és **előrejelzés is:** egy **fekvő** képet is
   tartalmazó Indexképnél a `scale` csomópontonként ELTÉRNE.
   *(Mind a 31 mintacsomópontunk álló — az előrejelzést a meglévő anyag nem
   dönti el.)*
2. ⛔ **A 0…2 egységes maradék NEM a mi megvalósításunk hibája.** A 18.8 még
   nyitva hagyta, hogy „a kerekítési módokon és a `k`/oszlopszám levezetésén
   múlik" — a 18.8 a MI kódunkat futtatta. Ez a kör a **bináris saját
   képletét** számolta ki, és **ugyanazt a 0…2 egységet** kapta. ⇒ a hiba a
   `k`/rés levezetésében vagy egy még nem azonosított ±1-ben van, **nem a
   PicasaPy oldalán**. A #2583-nak ez a különbség a tényleges mércéje.

*Bizonyítottsági fok: **megerősített** a csomópont-függetlenség (19
csomópont, hat forrásméret) és a maradék nagysága; **NINCS MEG** a maradék
oka.*

### 31.6 Hol tart a K1, és mi a KÖVETKEZŐ lépés

**Három állítás áll, és együtt nem fér meg:**

| # | állítás | honnan |
|---|---|---|
| (a) | a `scale` = az elrendező doboz-magassága | 30.2 (10/10) + 31.5 (0…2 egység) |
| (b) | a doboz-magasságot csak a `FUN_00888210` állítja elő | **31.1** |
| (c) | a `FUN_00888210` a `+0x2c`-be feltétel nélkül 1,0-t ír | 22.2 + **31.2** |

A mentett fájlban mégsem 1,0 áll. A leggyengébb láncszem **nem** (a), (b)
vagy (c) — hanem a kimondatlan negyedik: **hogy a mentett csomópont
ugyanaz az objektum, amelybe az elrendező ír.** A 28. szakasz már kimondta,
hogy az elrendező IDEIGLENES vektorba dolgozik.

⇒ **A következő lépés:** a `0x00888210` **hívójának** (a téma slot0
gyökere, `FUN_00887ad0`, 19.1) végigolvasása — mit csinál az elrendező
kimenetével, és **melyik függvény másolja át a dokumentum-tömbbe**. Ez már
nem pásztázás, hanem egy megnevezett hívási lánc kiolvasása.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

**Eszközök** (privát `picasapy-agent`): `eszkozok/binaris/konst_xref.py`
(konstans-hivatkozás kereső), `eszkozok/binaris/h_to_scale.py`,
`eszkozok/binaris/scale_keplet.py`.

## 32. K1 — az Indexkép-elrendezés kimenetét MINDKÉT hívó ELDOBJA (2026-09-07, #1412)

*184. kutatói kör. A 31.6 megnevezett lépését viszi: a `FUN_00888210`
hívójának végigolvasása. A 28. szakasz EGY hívási helyre mutatta ki, hogy
az elrendező ideiglenes vektorba ír — ez a kör **mindkét** hívóra kimutatja,
és az elem-méretet a PUSZTÍTÓBÓL is igazolja.*

### 32.1 A téma slot0 gyökere (`FUN_00887ad0`, 242 b) — PRÓBA-út

```
[esi+4] = param1 (a panel) · [esi+8] = param2 (a dokumentum) · [esi+0xc] = jelzőbájt
[esi+0x20] = szövegszín: ha ([param2+0x160] & 0xffffff) < 0x7f7f7f  →  0xffffffff,
             különben 0xff4a4a4a          ; 0x00887b0b–0x00887b23
&vec = &[esp+…], két dwordje NULLÁZVA     ; 0x00887b2d / 0x00887b35
call 0x887e50 (gyűjtés + rács)            ; 0x00887b3d
  ha nem nulla  →  vec pusztítása, hibakód vissza
  ha nulla:
     darab = vec.méret >> 1               ; 0x00887b67
     a DOKUMENTUM virtuális metódusa:  [[esi+8]] + 0x28, argumentum: darab
                                          ; 0x00887b62–0x00887b6a
     a lap téglalapja: [param1+0x188..0x194] a veremre   ; 0x00887b6f–0x00887b90
     call 0x888210 (elrendezés)           ; 0x00887b99
     call 0x62d010 (a vec PUSZTÍTÁSA)     ; 0x00887ba4
```

⇒ **A geometria itt nem hagyja el a függvényt.** A visszatérési érték
csak a siker/hiba kód.

### 32.2 A MÁSIK hívó (`FUN_00887bd0`, 639 b) — és a menete

A `FUN_00888210`-nek az egész binárisban **pontosan két** hivatkozója van
(`xrefs`): a `0x00887ad0` és a `0x00887bd0`. A második menete:

| cím | hívás | mit tesz |
|---|---|---|
| `0x00887d5a` | `0x008342b0` (620 b) | egy nagy, előre nullázott szerkezet felépítése |
| `0x00887d6c` | `0x0087dcd0` (3206 b) | a téma-beállítások beolvasása (`collage::theme`, `noborder`, `picturepile`, `collage::shadows`, `collage::showcaptions`) |
| `0x00887d80` | `0x00880580` (1889 b) | `avgcolor` / `noborder` — a paraméterblokk kiegészítése |
| `0x00887d89` | `0x00831bc0` (295 b) | a panel gyerekeinek osztályozása (`dynamic_cast` + jelzőbájtok) — **nem** csomópont-író |
| `0x00887da1` | `0x00887e50` | gyűjtés + rács a **helyi** vektorba (`&[esp+0x18]`) |
| `0x00887dfa` | **`0x00888210`** | elrendezés **ugyanabba a helyi vektorba** (`sub esp,0x10` után `[esp+0x28]` = ugyanaz) |
| `0x00887e0b` | **`0x0062d010`** | **a vektor PUSZTÍTÁSA** |
| `0x00887e3f` | `0x00888dd0` (136 b) | újrarajzolás-jelzés |

### 32.3 ⭐ A PUSZTÍTÓ igazolja az elem-méretet: 56 bájt

`FUN_0062d010` (46 b) — a `[esi]`-ben álló tömböt bontja le:

```
0x0062d016  mov eax,[ecx-4]          ; elemszám a fejlécből
0x0062d01d  push 0x40e980            ; ELEM-pusztító
0x0062d022  push 0x38                ; ELEM-MÉRET = 56 bájt
0x0062d024  call 0x401110            ; tömb-lebontó
0x0062d02a  call 0xc07738            ; free
0x0062d037  mov dword ptr [esi], 0
```

⇒ **a helyi vektor a kollázs-csomópontokat ÉRTÉK szerint tartja** (56 bájt,
26.1), és a kör végén **felszabadul**. A 28. szakasz megállapítása ezzel
**mindkét** hívási helyre igazolt, és nem a hívási minta, hanem a
**pusztító paraméterei** bizonyítják.

### 32.4 A `FUN_00888dd0` (136 b) — újrarajzolás, nem író

Végigolvasva: a `[param+4]` objektum `[+0x198]` gyerektömbjén iterál
(`darab = [+0x19c] >> 1`), `dynamic_cast`-tal szűr (`0xc07db2`,
`0xd3c9c0` típusleíró), és a találatokra `or dword ptr [edi+8], 7`
(piszkos-bitek), illetve `byte [eax+0x20] = 0`. **Csomópont-mezőt nem ír.**

### 32.5 ⛔ AZ ELLENTMONDÁS ÉLESEBB LETT — és most már számszerű

| állítás | honnan |
|---|---|
| a `.cxf` geometriája a `FUN_00888210` aritmetikájából jön | 18.4: **62/62** jóslat nulla eltéréssel |
| a `FUN_00888210` kimenetét MINDKÉT hívója eldobja | **32.1–32.3** |
| ugyanezt az aritmetikát a programban más nem tudja elvégezni | 31.1: a `0,88`/`0,79` konstansnak 2-2, a `0,08`-nak 1 hivatkozója van |

A három együtt nem állhat fenn. **A leggyengébb láncszem nem nevezhető
meg találgatás nélkül**, ezért a kör nem is nevezi meg — de a
maradék lehetőségek listája most már rövid, és mindegyik gépi úton
eldönthető:

1. **a dokumentum virtuális metódusa** (`[vtábla+0x28]`, `0x00887b6a`),
   amit a darabszámmal hívnak az elrendezés ELŐTT — ha ez nem
   „méret beállítása", hanem maga építi a csomópontokat, akkor a
   geometria útja máshol fut;
2. **a `FUN_00887e50` írásai a dokumentumba** — a 19.1 csak a
   `[this+0x10]`/`[+0x14]`/`[+0x18]` rács-mezőket mérte ki;
3. **a `FUN_008342b0`** (620 b) — a menet első hívása, a csomópont
   értékadó operátorának egyik hívója (17.13 listája).

*Bizonyítottsági fok: **megerősített** a 32.1–32.4 minden állítása
(utasításszinten, címekkel); az ellentmondás **kimondva**, a feloldása
**NINCS MEG**.*

### 32.6 A KÖVETKEZŐ lépés, megnevezve

A 32.5 három tétele, ebben a sorrendben — mindhárom olvasás, nem
pásztázás. Az (1) a legolcsóbb: a `[esi+8]` objektum vtáblájának
azonosítása az RTTI-táblából, majd a `+0x28`-as bejegyzés kiolvasása.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 33. K1 — az RTTI feloldja a virtuális hívást, és a 32.5 MINDHÁROM lehetősége kizárva (2026-09-07, #1412)

*185. kutatói kör. A 32.6 megnevezett lépését viszi, és a 32.5-ben
felsorolt három maradék lehetőséget végigméri. Új eszköz nem kellett: a
bináris-index `rtti` táblája a vtáblák TELJES bejegyzés-listáját tartja.*

### 33.1 ⭐ A virtuális hívás FELOLDVA: `CCollageUI::vftable[10]` = `FUN_0082c9a0`

A 32.1-ben megnevezett hívás (`0x00887b6a`: `[[esi+8]] + 0x28`, argumentum a
csomópontszám) az `rtti` tábla alapján egyértelmű:

```
CCollageUI::vftable @ 0x00cbf450
  [0] 0x00750cb0   [1] 0x005baa00   [2] 0x0082a670 (a kollázspanel)
  [3] 0x0082c360   [4] 0x0082cb50   [5] 0x0082d570 (parancs-elosztó)
  [6] 0x00830a00   [7] 0x00831750   [8] 0x00831b50   [9] 0x0087dc00
  [10] → +0x28 →  0x0082c9a0
```

**És a `FUN_0082c9a0` viselkedése MÁR KI VAN MÉRVE** (21.1): a
`clamp(1/sqrt(sqrt(n)−1)) × lapszélesség × 0,33` kifejezést számolja ki a
**darabszámmal** a panel beállítás-objektumába. A teljes, vermen kívüli
írás-listája ezt igazolja:

| cím | írás |
|---|---|
| `0x0082ca7b` | `[eax+0x30]` |
| `0x0082cad0` · `0x0082cadf` | `[edx+0x3c]` · `[eax+0x3c] = 0` |
| `0x0082cb1a` | `byte [ecx+0x36] = 1` |

⇒ **csomópont-mezőt nem ír.** A 32.5 (1) lehetősége **KIZÁRVA**.

### 33.2 A `FUN_00887e50` (gyűjtés + rács) — a TELJES írás-listája

| cím | írás | mi |
|---|---|---|
| `0x00887f6b` · `0x00887fd5` · `0x0088800c` | `[eax]` · `[edi]` · `[edi+4]` | a vektor két mutatója |
| `0x0088819b` · `0x0088819e` · `0x008881a1` | `[eax+0x10]` · `[+0x14]` · `[+0x18]` | **sor · oszlop · k** (19.1) |

⇒ **csomópont-mezőt nem ír.** A 32.5 (2) lehetősége **KIZÁRVA**, és a 19.1
mérése harmadszor is megerősítve.

### 33.3 A `FUN_008342b0` — csak mutató-rekeszek

`0x008342ce` · `0x008342f7` · `0x0083434a` · `0x0083444d` · `0x008344f2` ·
`0x008344fc` · `0x00834508` — mind `[edi]` vagy `[eax]`, eltolás nélkül
(tároló-könyvelés). ⇒ **csomópont-mezőt nem ír.** A 32.5 (3) lehetősége
**KIZÁRVA**.

### 33.4 ⭐ Az RTTI-tábla mint FÜGGETLEN bizonyíték a 32.1/32.2-re

```
CContactSheetTheme::vftable @ 0x00cbf670
  [0] 0x00887ad0   ← a 32.1 „próba-út"
  [2] 0x00887bd0   ← a 32.2 „valódi menet"
```

A két szerep tehát nem a hívási mintából következtetett, hanem a
vtábla-sorrendből is látszik. A teljes témacsalád, egy helyen:

| osztály | vtábla | slot0 |
|---|---|---|
| `CContactSheetTheme` | `0x00cbf670` | `0x00887ad0` |
| `CPileTheme` | `0x00cbf5ac` | `0x0087b4a0` |
| `CRegularGridTheme` | `0x00cbf610` | `0x00884040` |
| `CGridTheme` | `0x00cbf5dc` | `0x00880e30` |
| `CFrameGridTheme` | `0x00cbf6a0` | `0x00880e30` |
| `CMultiExposureTheme` | `0x00cbf640` | `0x00887110` |

és a **csempe**-osztályok: `NoBorderTheme` (`0x00cbf934`),
`WhiteBorderTheme` (`0x00cbf928`), `PolaroidBitmapTheme` (`0x00cbf91c`),
`DimmedBitmapTheme` (`0x00cbf940`) — mindegyik kétbejegyzéses.

### 33.5 ⭐ ÚJ, eddig nem nevesített osztály: `CHeadlessCollageUI` — és a kizárása

Az `rtti` tábla szerint a kollázs-felületnek **két** megvalósítása van:
`CCollageUI` (`0x00cbf450`) és **`CHeadlessCollageUI`** (`0x00cc4eec`) —
az utóbbi a spec eddigi szakaszaiban egyszer sem szerepelt. Kézenfekvő
gyanú volt, hogy a mentés/renderelés ezen fut, és a csomópontokat ez írja.

**Megmérve — nem.** A vtábla mind a kilenc saját bejegyzését átnézve
(csomópont-mező `+0x18`…`+0x2c` írása, `esp`/`ebp` bázis nélkül):

| függvény | találat | ítélet |
|---|---|---|
| `0x0088a430` (1400 b) | `+0x20`, `+0x24` | **kritikus szakasz**: `[+0x20]` = birtokló szál (`GetCurrentThreadId`, `[0xc40284]`), `[+0x24]` = rekurziószám, `[+0x28]` = a `CRITICAL_SECTION` (`EnterCriticalSection`, `[0xc4055c]`) |
| `0x0088ac30` (500 b) | `+0x2c` | a panel `[ebx+0x270]` beállítás-objektuma: `+0x40 → +0x2c`, `+0x44 → +0x30`, `+0x48…+0x4a → +0x34…+0x36` — **állapot-visszaállítás** (a 26.4 ítélete, most utasításszinten újra igazolva) |
| a többi hét | — | nincs |

⇒ **a headless felület sem ír csomópont-mezőt.**

### 33.6 Hol tart a K1 — a lánc MINDEN eleme kizárva

A 32.5 három állítása áll, és a hozzájuk tartozó három lehetőség
mostanra mind kizárva. Az elrendezési út **egyetlen** függvénye sem ír a
dokumentum csomópontjaiba: az elrendező a helyi vektorba (32.1–32.3), a
rácsszámoló a saját rács-mezőibe (33.2), a virtuális hívás a panel
beállításaiba (33.1), az előkészítő a tárolójába (33.3), a headless
felület sehova (33.5).

⇒ **A `.cxf`-be kerülő geometria NEM a téma-elrendezési úton keletkezik.**
Ez erős, mert nem egy pásztázás negatívja, hanem az út **összes**
függvényének tételes írás-listája.

**A KÖVETKEZŐ lépés, megnevezve:** a keresést át kell vinni a **mentési**
oldalra. A `.cxf`-írót (`FUN_008347b0`) a mentés-szervező
(`FUN_00834700`, 22.3) hívja; annak a hívási fájában kell megkeresni, ki
tölti fel a dokumentum `[+0x48]` tömbjét **közvetlenül a kiírás előtt**.
A 26.4 ezt az ágat 3 szint mélyen már pásztázta `+0x2c`-írásra
(0 író, 1 olvasó) — de a 30.3 óta tudjuk, hogy **a hármas
együttállást** (`+0x20`/`+0x24`/`+0x2c`) kell keresni, és a 26.4 nem erre
szűrt.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 34. K1 — a HÁRMAS kulcs a maradék három hívási fán, és egy megdőlt ötlet (2026-09-07, #1412)

*186. kutatói kör. A 33.6 lépését viszi (mentési oldal), és mellé a 26.5
két olcsóbb vágását — most már a **hármas együttállásra** szűrve, amit a
26.4 még nem használt. Módszer: a `xrefs` tábla `call` éleiből épített
hívási fa, metszve a 30.4 pásztázásának 212 találatával.*

### 34.1 A MENTÉSI ág — a metszet ÜRES

`FUN_00834700` hívási fája 3 szint mélyen: **63** függvény.
**Pozitív kontroll:** a `.cxf`-író (`FUN_008347b0`) az 1. szinten benne van ✅.

A fa 1. szintje: `0x00401000` · **`0x008347b0`** · `0x00985ff0` ·
`0x009bfcc0` · `0x009bfde0` · `0x009bfe70` · `0x009c15a0` — a 2. szint
19 tétele pedig szinte kivétel nélkül futásidejű könyvtár
(`0x0040eab0` = `sprintf`, `0x00c07a30`, `0x00bf37c0`, …).

**Metszet a hármas konjunkcióval: 0.**

⇒ **A mentési ág nem építi a csomópontokat — csak sorosít.** A dokumentum
`[+0x48]` tömbje a mentés pillanatában már kész.

### 34.2 A kollázspanel fája (`0x0082a670`, 3 szint) — negatív

**317** függvény, a metszet **12** — de közülük a `+0x2c`-t
**lebegőpontosan** csak három írja, és mind a három besorolt:

| függvény | ítélet |
|---|---|
| `0x00829770` | nullázó inicializáló (17.15) |
| `0x008341b0` | a csomópont **értékadó operátora** (másoló) |
| `0x009dd800` | **76 bájtos** lépésközű konstruktor (30.4-ben kizárva) |

A maradék kilenc a `+0x2c`-be **egészet** ír. ⇒ negatív — és ez a 26.4
azonos hatókörű negatívjának megerősítése **a hármas kulccsal**, amit a
26.4 nem használt.

### 34.3 A parancs-elosztó fája (`0x0082d570`, 3 szint) — negatív

**282** függvény, a metszet **5**, ebből lebegőpontos `+0x2c`-író
ugyanaz a három. ⇒ **a 26.5 (1) vágása LEZÁRVA, negatívval.**

### 34.4 ⛔ MEGDŐLT ÖTLET: „egy második megvalósítás a MARGÓKBÓL számol"

A kör felvetette, hogy a `0,88` és a `0,79` **levezethető** a margókból
(`0,88 = 1 − 2·0,06`, `0,79 = 1 − 0,15 − 0,06`), tehát egy második
megvalósítás a `0,06`/`0,15` konstansokra hivatkozna — és a 31.1 szerint a
`0,06`-nak **két** hivatkozója van, a második a `FUN_00b148e0`.

**Elolvasva (213 b) — az ötlet MEGDŐLT.** A függvény a
`0x00b14957`–`0x00b149a9` szakaszon nyolc `double`-t tesz a veremre egy
hívás argumentumaként:

| érték | mi ez |
|---|---|
| `0,3127` · `0,3290` | a **D65 fehérpont** (`0x00cf46a8`, `0x00cf46b0`) |
| `0,64` · `0,33` | az sRGB **vörös** primer (`0x00cf46b8`, `0x00cf46c0`) |
| `0,30` · `0,60` | az sRGB **zöld** primer (`0x00cf4228`, `0x00cf46c8`) |
| **`0,15`** · **`0,06`** | az sRGB **kék** primer (`0x00cf3fd0`, `0x00cf46d0`) |
| `0,45455` | **1/2,2** — a gamma (`0x00cf46d8`) |

⇒ **színprofil-beállítás, nem elrendezés.** A `0,06`/`0,15` együttes
előfordulása az sRGB kék primerének koordinátája — puszta egybeesés.

**Amit ez visszamenőleg jelent:** a 31.1 táblájában a `0,06` „2
hivatkozó" sora **elrendezési szempontból 1** (csak a `FUN_00888210`), a
`0,15` nyolc hivatkozójából pedig szintén csak egy az elrendezőé.
A 31.1 következtetése — „a doboz-magasságot nem lehet újraszámolni" —
ezzel **erősebb** lett, nem gyengébb.

### 34.5 Hol tart a K1 — és a maradék EGYETLEN szerkezeti tölcsér

Ami eddig kizárva: az elrendezési út teljesen (33.6), a mentési ág (34.1),
a kollázspanel és a parancs-elosztó fája (34.2, 34.3), a témák és a
headless felület (33.4, 33.5), a sávon kívüli mező-írók (29.1, 30.4,
31.3), és a „második megvalósítás" ötlete (34.4).

**Ami marad, és most már tényleg egyetlen tétel:** a csomópont
**értékadó operátora**, a `FUN_008341b0` — ez mindhárom fában benne van, és
ez az egyetlen olyan besorolt függvény, amely a `+0x2c`-t
lebegőpontosan írja **és** a láncot viszi. A kérdés innentől nem az, hogy
*hol írják*, hanem hogy **honnan MÁSOLJÁK**:

> A `FUN_008341b0` **tizenkét** hívója (17.13 listája) közül melyik ad
> olyan FORRÁS-csomópontot, amelynek a `+0x2c`-je nem 1,0 — és az a
> forrás hol kapta?

Ez zárt, megszámolható feladat: tizenkét megnevezett cím
(`0x00833920` · `0x00833cf0` · `0x008342b0` · `0x0083dfa0` · `0x0083e280` ·
`0x0083e560` · `0x0087b4a0` · `0x0087dcd0` · `0x0087e960` · `0x00880580` ·
`0x00884a90` · `0x00887e50`), és a 30.5 óta a **másoló konstruktor**
(`FUN_0087b830`) három hívója is ide tartozik.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

**Eszköz:** `eszkozok/binaris/fa_metszet.py` — hívási fa adott gyökértől
adott mélységig, metszve a hármas konjunkció találataival, pozitív
kontrollal.

## 35. K1 — a MÁSOLÁS IRÁNYA kiolvasva, és ebből: a csomópontok az elrendezés ELŐTT már megvannak (2026-09-07, #1412)

*187. kutatói kör. A 34.5 megnevezett lépését viszi: a csomópont
értékadó operátorának tizenkét hívója. A lelet nem az, amit a kör keresett
— hanem ennél lényegesebb.*

### 35.1 ⭐ A két másoló hívási megállapodása — a KÓDBÓL

**`FUN_008341b0` (értékadó operátor):**

```
0x008341b2  mov ebx, [esp+0xc]     ; a VEREMRE TOLT argumentum = CÉL
0x008341b6  mov eax, [ebx]
0x008341b8  cmp eax, [esi]         ; ESI = FORRÁS
0x008341cb  mov eax, [esi]  →  0x008341cf  mov [ebx], eax
```

⇒ **`ESI` = forrás, a tolt argumentum = cél.** (A 30.5 másoló
konstruktoránál fordítva: `EDI` = forrás, `ESI` = cél.)

Ez a megállapodás eddig sehol nem volt kimondva, és nélküle a hívási
helyek olvasata **megfordítható** — épp az a fajta hiba, amit a 26.3 már
egyszer helyesbített.

### 35.2 A tizenöt hívási hely — a FORRÁS mindig TÖMBELEM

A tizenkét hívó tizenöt helyen hívja az operátort. A minta **kivétel
nélkül** ugyanaz:

```
mov esi, [<objektum> + 0x48]   (vagy  mov esi, [edi])   ; a tömb bázisa
add esi, <eltolás>                                      ; → FORRÁS elem
lea ecx, [<másik bázis> + <eltolás>]                    ; → CÉL elem
push ecx
call 0x8341b0
```

Példák: `0x00833fa9`, `0x00834109`, `0x0083417f` (`FUN_00833cf0`),
`0x0083447c` (`FUN_008342b0`), `0x0083e098` · `0x0083e1f8` · `0x0083e266`
(`FUN_0083dfa0`), `0x0083e368` · `0x0083e4c8` (`FUN_0083e280`),
`0x0083e648` · `0x0083e749` (`FUN_0083e560`), `0x00833afc` · `0x00833b54`
(`FUN_00833920`).

⇒ **Egyetlen hívási hely sem ad frissen ÉPÍTETT csomópontot forrásként** —
mind a tizenöt tömbelem→tömbelem másolás. A `scale` értéke tehát ezeken
az utakon **nem keletkezik, csak vándorol.**

### 35.3 ⭐ A másoló konstruktor HÁROM helye: a forrás a DOKUMENTUM tömbje

```
0x0087b54e  (FUN_0087b4a0)  mov edi,[edi+0x48] · add edi,esi · lea esi,[esp+0x30]
0x00884ae8  (FUN_00884a90)  mov edi,[ebp+0x48] · add edi,esi · lea esi,[esp+0x30]
0x00887ea6  (FUN_00887e50)  mov edi,[ebp+0x48] · add edi,esi · lea esi,[esp+0x28]
```

`EDI` = forrás (35.1) ⇒ mindhárom helyen a forrás a **dokumentum `[+0x48]`
csomópont-tömbjének egy eleme**, a cél pedig egy **verem-helyi** csomópont.

**A `FUN_00887e50` a téma gyűjtés+rács függvénye** (19.1) — tehát az
ideiglenes vektort, amelybe később az elrendező ír, **a dokumentum MÁR
MEGLÉVŐ csomópontjainak MÁSOLATAI** töltik fel.

### 35.4 ⛳ Amit a 32. szakasszal EGYÜTT kimond

| lépés | forrás |
|---|---|
| a téma másolatot készít a dokumentum csomópontjairól | **35.3** |
| az elrendező a másolatokba ír | 30.1 |
| a másolatokat a hívó elpusztítja | 32.1–32.3 |

⇒ **A dokumentum csomópontjai az elrendezés ELŐTT megvannak, és az
elrendezés NEM módosítja őket.** A `.cxf`-be tehát a dokumentum saját
értékei kerülnek — azok, amelyek a téma futása előtt már ott álltak.

### 35.5 ⭐ Hogyan kerülnek be a csomópontok? Csak a BEOLVASÓN át

- A `push_back` (`FUN_00833920`, 17.13) hivatkozóinak száma az `xrefs`
  szerint **nulla** — csak virtuálisan hívható.
- A 22.4 már kimérte: **a hozzáadó virtuális metódust csak a BEOLVASÓ
  hívja.**
- A `FUN_00833cf0` (1192 b) viszont **dokumentum → dokumentum** másolás:
  a `0x0083417f`-en `mov ecx,[ebp+0x48]` (cél) és `mov esi,[eax+0x48]`
  (forrás) — **két külön dokumentum tömbje**. Hét hívója van, köztük a
  kollázspanel (`0x0082a670`) és a panel vezérlő-kezelője (`0x00831750`).

### 35.6 A KÖVETKEZŐ lépés, megnevezve

A kép ezzel megfordul: nem azt kell keresni, ki **írja** a `+0x2c`-t az
elrendezés után, hanem azt, **honnan való az a dokumentum, amelyből a
panel másol** (`FUN_00833cf0`), illetve **melyik `.cxf` beolvasása tölti
fel** a csomópontokat egy ÚJONNAN létrehozott kollázsnál.

A 3.2 szerint a piszkozat mentésekor `.cxf` kerül a lemezre. Ha egy új
kollázs is beolvasáson át kapja a csomópontjait, akkor a `scale` a
**piszkozat írásakor** keletkezik — és ott kell keresni.

Két megnevezett, még nem olvasott hely:

1. a `FUN_00833cf0` **hét hívója** (`0x0082a670` · `0x00831420` ·
   `0x00831750` · `0x00838ef0` · `0x0083d090` · `0x00889e00` ·
   `0x0088b0a0`) — melyikük épít fel egy forrás-dokumentumot;
2. az `rtti` szerinti **`CAutosaveCollageThread`** (`vftable`
   `0x00cbfed0`, slot0 `0x00839440`) — a spec eddig nem használta; ez
   írja a piszkozatot.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

**Eszköz:** `eszkozok/binaris/atadok.py` — egy függvény hívási HELYEIT
(utasításcím) és a hívás előtti hat utasítást listázza.

## 36. K1 — a kollázspanel KÉT dokumentumot tart, és az autosave csak sorosít (2026-09-07, #1412)

*188. kutatói kör. A 35.6 két megnevezett helyét viszi: a `FUN_00833cf0`
hét hívóját és a `CAutosaveCollageThread`-et.*

### 36.1 ⭐ A dokumentum-másoló hívási megállapodása — a KÓDBÓL

`FUN_00833cf0` (1192 b) feje:

```
0x00833cf9  mov ebp, [esp+0x10]   ; három belső push után → az 1. argumentum
0x00833cfe  mov esi, [esp+0x18]   ; négy belső push után → a 2. argumentum
0x00833d02  mov al, [esi]  →  0x00833d05  mov [ebp], al
```

⇒ **az 1. argumentum (az utoljára tolt) a CÉL, a 2. a FORRÁS.**
A 35.1 tanulsága szerint ezt ki kell olvasni, mert a hívási helyek
olvasata enélkül megfordítható.

### 36.2 ⭐ A kollázspanel KÉT kollázs-dokumentumot tart: `[+0x138]` és `[+0x1b0]`

A hét hívási hely a fenti megállapodással:

| hely | hívó | CÉL | FORRÁS | irány |
|---|---|---|---|---|
| `0x0082bffb` | `FUN_0082a670` (kollázspanel) | `[ebx+0x1b0]` | `[ebx+0x138]` | **+0x138 → +0x1b0** |
| `0x00831ab0` | `FUN_00831750` (vezérlő-kezelő) | `[ebx+0x1b0]` | `[ebx+0x138]` | **+0x138 → +0x1b0** |
| `0x0083d0a7` | `FUN_0083d090` | `[esi+0x138]` | `[esi+0x1b0]` | **+0x1b0 → +0x138** |
| `0x008315b8` | `FUN_00831420` | `[ebp+0x138]` | **verem-helyi** | kívülről → `+0x138` |
| `0x00838f67` | `FUN_00838ef0` (autosave-ktor) | a beágyazott dok. | verem-helyi (érték szerinti argumentum) | kívülről |
| `0x0088b139` | `FUN_0088b0a0` | `esi` | verem-helyi | kívülről |
| `0x00889e54` | `FUN_00889e00` | (a hívás előtti mező-nullázás után) | — | — |

⇒ **A panel két dokumentumot tart, és MINDKÉT irányban másol közöttük** —
ez a klasszikus „munkapéldány + rögzített példány" (vagy visszavonás)
pár. Ez a szerkezet eddig nem szerepelt a specben, és megmagyarázza,
miért nem találtuk a csomópont-írót egyetlen úton sem: **a dokumentumok
kívülről, kész állapotban érkeznek a panelbe.**

### 36.3 ⭐ A belépési pont: `FUN_00831420`

A `0x008315b8` a panel `[+0x138]`-as dokumentumába másol egy
**verem-helyi** dokumentumot — vagyis itt lép be egy kész, feltöltött
dokumentum a panelbe. A `FUN_00831750` (vezérlő-kezelő) közvetlenül
ez után rögzíti a másolatot (`0x00831a9d call 0x831420`, majd
`0x00831ab0` a `+0x138 → +0x1b0` másolás).

### 36.4 A `CAutosaveCollageThread` — LEZÁRVA, csak sorosít

*`rtti`: `vftable 0x00cbfed0`; a névsztring a `FUN_00839320`-ban.*

- **konstruktor `FUN_00838ef0`** (148 b): egy ≥ `0x14d0` bájtos objektumot
  épít, amelyben `[+0xc]`-nél egy kollázs-dokumentum ül; azt a
  `0x008342b0`-nal inicializálja, majd a `0x00838f67`-en a
  `FUN_00833cf0`-nal **beléje másolja** a kapott dokumentumot.
  A `ret 0x54` mutatja, hogy a dokumentum **érték szerint** érkezik.
- **futtató metódus `FUN_00839330`** (267 b): útvonalat épít
  (`0x00839369`, formátum `0xc81a34`), majd a `0x008393aa`-n meghívja a
  **mentés-szervezőt** (`FUN_00834700`) az `[esi+0x48]` dokumentummal.

⇒ **az autosave csak SOROSÍT egy kész dokumentum-másolatot** — csomópontot
nem épít. A 35.6 (2) lehetősége **KIZÁRVA**.

### 36.5 ⛔ BLOKKOLT részkérdés: mit tartalmaz a PISZKOZAT `.cxf`-je?

A 35.6 döntő mérése az volna, hogy egy **még soha nem mentett** kollázs
piszkozat-`.cxf`-jében áll-e már a `scale`. **Helyi anyagból nem
eldönthető:**

- a repóban nincs `.cxf` (`find . -iname '*.cxf'` → 0);
- a tulajdonos `Picasa2` mappájának mentése (NAS, 2026-08-22, **124
  fájl**) sem tartalmaz `.cxf`-et — a kiterjesztés-eloszlás: 65 `.pmp`,
  15 `.ytf`, 14 `.db`, 7 `.txt`, 3 `.ioq`, 3 `.dat`, 2 `.log`, 1 `.zip`,
  1 `.xml`.

**Új mintát ezért sem kérünk** (17.15): a kérdésnek van gépi útja
(36.6), és a tulajdonosi mérés a legdrágább erőforrás. Ha a gépi út
kimerül, ez a kérés lesz a következő — akkor a jegy törzsébe kerül, a
kötelező szakasszal.

### 36.6 A KÖVETKEZŐ lépés, megnevezve

**`FUN_00831420`** (534 b) — honnan való a `0x008315b8`-on `[esp+0x10]`-en
álló, verem-helyi dokumentum? Ez az egyetlen olyan hely, ahol egy
**feltöltött** dokumentum kívülről lép a panelbe, és a 36.2 táblája
szerint innen terjed tovább a `+0x1b0`-as példányba is.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 37. K1 — az ELSŐ nem-beolvasó csomópont-építő, és benne egy `scale`-alakú SZÁMÍTÁS (2026-09-08, #1412)

*189. kutatói kör. A 36.6 lépését viszi: honnan való a `FUN_00831420`
verem-helyi dokumentuma. A válasz egy olyan függvényhez vezet, amelyet
minden eddigi pásztázás átengedett — mert a `+0x2c`-t nem eltolással írja.*

### 37.1 `FUN_00831420` (534 b) = „a panel `[+0x138]` dokumentumának ÚJRAÉPÍTÉSE"

```
[ebp] = a panel;  kapu:  ha [ebp+0x130] == 0  →  nem csinál semmit   ; 0x0083142b
verem-helyi dokumentum:  mezők nullázása  →  call 0x008342b0          ; 0x00831472
call 0x0087dcd0(panel, &helyi, 0, 0)                                  ; 0x0083147f
a panel négy sztringmezőjének átvétele: [ebp+0x13c] · [ebp+0x168] ·
   [ebp+0x170] · [ebp+0x174]                                          ; 0x00831484–0x00831566
call 0x00833cf0(&[ebp+0x138], &helyi)   ; a helyi → a panel dokumentuma; 0x008315b8
```

⇒ a dokumentum **tartalmát a `FUN_0087dcd0` adja**.

### 37.2 ⭐ `FUN_0087dcd0` (3206 b) — az ELSŐ nem-beolvasó csomópont-építő

A függvény sztringkészlete a téma-beállításoké (`collage::theme`,
`collage::shadows`, `collage::showcaptions`, `collage::orientation`,
`collage::bgcolor`, `noborder`, `picturepile`, `multiexp`, `avgcolor`).
**Négy** helyen hívja a csomópont értékadó operátorát:

| cím | forrás | cél |
|---|---|---|
| `0x0087e390` · `0x0087e7a0` | `[[esp+0x174]+0x48] + eltolás` (másik dokumentum tömbeleme) | `[edi+ebp]` |
| **`0x0087e3f2`** · **`0x0087e802`** | **verem-helyi csomópont** | `[[ebx+0x48] + n × 56]` — **hozzáfűzés** |

A hozzáfűzés a **56 bájtos elem-idióma**: `0x0087e3e1` `lea ecx,[eax*8]` →
`0x0087e3e8` `sub ecx,eax` (= 7·n) → `0x0087e3ea` `lea eax,[edx+ecx*8]`
(= 56·n). Ugyanez a `0x0087e7f1`–`0x0087e7fa`-n.

⇒ **Ez az első olyan út, amelyen csomópont a BEOLVASÓN KÍVÜL kerül egy
dokumentum `[+0x48]` tömbjébe.** A 22.4 megállapítása („a hozzáadó
virtuális metódust csak a beolvasó hívja") **a virtuális metódusra** áll —
ez a függvény **közvetlenül** fűz hozzá, az értékadó operátorral.

**Miért engedte át minden eddigi pásztázás:** a `+0x2c`-t nem
`[reg+0x2c]` alakban írja, hanem a **verem-helyi csomópont** egyik
rekeszébe — a hármas konjunkció (30.4) és minden eltolás-alapú minta
`esp`/`ebp` bázissal kizárta.

### 37.3 ⭐ Egy `scale`-ALAKÚ SZÁMÍTÁS a második blokkban

`0x0087e500`–`0x0087e55a`:

```
fld  [edi+0x168]        →  fstp [esp+0x100]      ; egy float tagváltozó
eax = [esp+0x8c] − [esp+0x84]                    ; téglalap SZÉLESSÉG
ecx = [esp+0x88] − [esp+0x80]                    ; téglalap MAGASSÁG
[esp+0x14] = MIN(szélesség, magasság)            ; 0x0087e52d–0x0087e531
fild [esp+0x14]  ·  fmul [esp+0x100]             ; MIN × [edi+0x168]
fstp [esp+0x58]                                  ; → a helyi csomópont egyik float mezője
```

**`MIN(szélesség, magasság) × egy float tagváltozó`** — pontosan olyan
alakú mennyiség, amilyen a `scale` (a 24.1 szerint `k = min(cellaSzél,
cellaMag)`). Az első blokkban ugyanennek a hatféle float rekesznek egyikébe
`fld1` megy (`0x0087e229` → `0x0087e22f`).

### 37.4 ⛔ Amit NEM mondok ki: MELYIK mezőbe megy

A két blokk írásai `[esp+0x40]`…`[esp+0x5c]` rekeszekbe mennek, a
csomópont hat float mezője (`+0x18` … `+0x2c`, 26.1) pedig hat egymást
követő rekesz — **de a hozzárendelés a veremmélységtől függ**, és a két
blokk között `push`-ok vannak (`0x0087e4fb`, `0x0087e559`), amelyeket a
közbeeső `call`-ok fogyasztanak el.

**Horgony van:** a hozzáfűzésnél `0x0087e3ee` és `0x0087e7fe`
`lea esi,[esp+0x2c]` **közvetlenül egy `push eax` után** — ebből a
csomópont bázisa a push előtti kereten `[esp+0x30]`. Az írások kerete
viszont ettől eltérhet.

⇒ **A mező-hozzárendelést a kör NEM tippeli meg.** Ez pontosan az a
verem-normalizálási feladat, amit a 17.11 és a 25.4 is dekompilátorhoz
kötött.

### 37.5 A KÖVETKEZŐ lépés, megnevezve

**A `FUN_0087dcd0` verem-keretének normalizálása** — utána mind a két blokk
minden float írása egyértelműen a csomópont egy mezőjéhez rendelhető, és
azonnal eldől, hogy a `MIN(sz, m) × [edi+0x168]` a `scale`-be megy-e.

Két út: (a) célzott Ghidra-dekompiláció erre az egy függvényre (a 25.1
jogosultsági akadálya a 26. szakasz szerint elhárult); (b) helyi
push-mélység-követés a függvény teljes vezérlési gráfján.

Ha a válasz „igen", akkor a `scale` forrása megvan, és a `[edi+0x168]`
tagváltozó kiolvasása adja a szorzót.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 38. K1 — a verem-keret NORMALIZÁLVA, és a válasz: ezen az úton a `scale` = 1,0 (2026-09-08, #1412)

*190. kutatói kör. A 37.5 lépését viszi. A verem-mélység lineáris követése
**nem** vezetett célra (a saját mérőnk 20 ütközést jelzett elágazásoknál) —
helyette **MEZŐMINTA-ILLESZTÉS** döntötte el a kérdést, ami nem függ a
veremmélységtől.*

### 38.1 ⭐ A módszer: mezőminta-illesztés, nem mélységszámolás

A kollázs-csomópont 56 bájtos alakja ismert (26.1 + 30.5): `+0`, `+4`,
`+0x30` **hivatkozásszámlált sztring**, `+8` és `+0x34` mutató, `+0x18` …
`+0x2c` **hat float** (`x`, `y`, `w`, `h`, `theta`, `scale`).

A `FUN_0087dcd0` első blokkjában (`0x0087e1b0`–`0x0087e239`) tizenkét
rekesz íródik, és **mind a tizenkettő illeszkedik** erre az alakra, ha a
csomópont bázisa `[esp+0x28]`:

| rekesz | node-mező | mit kap | cím |
|---|---|---|---|
| `[esp+0x28]` | `+0` sztring | **0** | `0x0087e1cb` |
| `[esp+0x2c]` | `+4` sztring | **0** | `0x0087e1d3` |
| `[esp+0x30]` | `+8` mutató | `eax` | `0x0087e1db` |
| `[esp+0x40]` … `[esp+0x4c]` | `+0x18`…`+0x24` = `x,y,w,h` | **0,0** (`fldz`) | `0x0087e1bb`–`0x0087e1cf` |
| `[esp+0x50]` | `+0x28` = `theta` | **0,0** (`fldz`) | `0x0087e225` |
| **`[esp+0x54]`** | **`+0x2c` = `scale`** | **1,0** (`fld1`) | **`0x0087e229` → `0x0087e22f`** |
| `[esp+0x58]` | `+0x30` sztring | **0** | `0x0087e1d7` |
| `[esp+0x5c]` | `+0x34` mutató | `ecx` | `0x0087e233` |

A **második** blokk (`0x0087e4b0`–) ugyanezt a három sztring-rekeszt
nullázza (`0x0087e4c1` `[esp+0x28]`, `0x0087e4c5` `[esp+0x2c]`,
`0x0087e4c9` `[esp+0x58]`) ⇒ **ugyanaz a helyi csomópont, ugyanaz a
keret.**

*Bizonyítottsági fok: **megerősített** — tizenkét egymást követő rekesz
egyidejű illeszkedése egy ismert, tizenkét mezős alakra; a keret
mélységétől független.*

### 38.2 ⭐ A VÁLASZ: ezen az úton a `scale` = **1,0**

- Az első blokk `fld1`-gyel **1,0**-t ír a `+0x2c`-be (`0x0087e229` →
  `0x0087e22f`).
- A második blokk **soha nem írja** a `[esp+0x54]`-et: a
  `0x0087e4b0`–`0x0087e830` tartomány teljes átvizsgálása szerint a
  `[esp+0x50]`, `[esp+0x58]`, `[esp+0x5c]` íródik, a `[esp+0x54]` **nem**
  (egyetlen olvasás sincs rá) ⇒ **örökli az 1,0-t.**

⇒ **Mindkét hozzáfűzési út `scale = 1,0`-val teszi a csomópontot a
dokumentumba.**

### 38.3 A `MIN(sz, m) × [edi+0x168]` NEM a `scale`-be megy

A 37.3 számítása a `0x0087e55a`-n `fstp [esp+0x58]`-cal zárul, és ott
**egy `push` él** (`0x0087e559`), tehát a belépési kerethez képest
`[esp+0x5c]` = a csomópont **`+0x34`** mezője — az a mutató-rekesz,
amit az első blokk `ecx`-szel tölt. A `.cxf` ezt a mezőt **nem hordozza**
(26.1: hat float `+0x18`…`+0x2c`).

⚠️ **Ez a besorolás `erős`, nem megerősített:** a `0x0087e4fe`-en egy
**virtuális** hívás áll (`call edx`), amelynek a takarítási
megállapodását nem olvastuk ki. Ha az nem `stdcall`, a rekesz eggyel
tovább csúszik — de a `+0x2c`-t akkor **sem** érinti, mert az
`[esp+0x54]`-hez ±4-nél nagyobb csúszás kellene.

### 38.4 Melléklelet: a `theta` forrása

`0x0087e4e1` `fld [edi+0x15c]` → `0x0087e4e9` `fstp [esp+0x50]` =
csomópont **`+0x28` = `theta`**, egy float tagváltozóból. (Ez az első
hely, ahol a `theta` nem nulla lehet.)

### 38.5 ⛳ Amit ez KIMOND — és a KÖVETKEZŐ lépés

Az eddig megtalált **összes** nem-beolvasó út `1,0`-t ír a `scale`-be:
a két téma-elrendező (22.2), a `.cxf`-beolvasó alapértéke (17.16), és
most a panel dokumentum-építője is (38.2). A mintáink viszont
**313 / 500 / 256 / 158**-at hordoznak.

⇒ **Marad egyetlen út, amelyről EMPIRIKUSAN tudjuk, hogy megváltoztatja a
`scale`-t: a KÉZI ÁTMÉRETEZÉS.** A 17.5 mérése szerint a tizenkét arany
`.cxf` 97 `scale`-értékéből 95 egész, és a **két tört kivétel** épp abban
az `AI2`-ben van, amelyben a tulajdonos csomópontot húzott át.

**A következő lépés:** a `CollageNodeHandler` (`rtti` `0x00cc3bcc`)
fogantyú-ága. A 20.3 a `0x008685ca` (`mov [edx+0x2c], eax`) írást a
fogantyú-kezelő állapotobjektumára tette — **ezt az ítéletet a 38.1
mezőminta-módszerével újra kell ellenőrizni**, mert a korábbi olvasat a
`[edx+0x30]`-on át indexelésre támaszkodott, nem a tizenkét mezős alakra.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

**Eszköz:** `eszkozok/binaris/verem.py` — `[esp+N]` hivatkozások
normalizálása a belépési kerethez, a hívott függvények `ret N`-je alapján;
**az elágazásoknál keletkező ütközéseket hangosan jelzi**, nem hallgatja el.

## 39. K1 — a FOGANTYÚ-ág átvizsgálva: a 20.3 ítélete áll, de az egyik ÉRVE megdőlt (2026-09-08, #1412)

*191. kutatói kör. A 38.5 lépését viszi: a kézi átméretezés útja — az
egyetlen, amelyről EMPIRIKUSAN tudjuk, hogy megváltoztatja a `scale`-t
(17.5).*

### 39.1 ⭐ A `[edx+0x28]`/`[edx+0x2c]` pár POZITÍVAN azonosítva: egy (x, y) PONT

`FUN_00868570` (2326 b) a fogantyú-kezelő; sztringkészlete
`pan_hand_normal`, `pan_hand_drag`, `collagepanel/angletext`,
`collagepanel/scaletext`, `collage_adapt`, `Angle: %d`,
`collage::angle_format`, `Scale: %d%%`, `collage::scale_format`.

A 20.3 által kizárt írás:

```
0x008685c1  mov eax,[esi+0x54]  →  0x008685c4  mov [edx+0x28], eax
0x008685c7  mov eax,[esi+0x58]  →  0x008685ca  mov [edx+0x2c], eax
```

**Ugyanaz a két mező VISSZAOLVASVA, lebegőpontosan, és téglalapra
illesztve:**

```
0x008686c8  fld  [edx+0x28]  ·  fild [ecx]      ·  fcompp   ; bal
0x008686de  fld  [eax+0x28]  ·  fild [ecx+8]    ·  fcompp   ; jobb
0x008686f1  fld  [edx+0x2c]  ·  fild [ecx+4]    ·  fcompp   ; felső
0x00868702  fld  [eax+0x2c]  ·  fild [ecx+0xc]  ·  fcompp   ; alsó
```

⇒ a `+0x28` a téglalap **bal/jobb**, a `+0x2c` a **felső/alsó** határához
mérődik ⇒ **a pár egy `(x, y)` PONT, találat-vizsgálathoz** — nem a
csomópont `theta`/`scale` párja. **A 20.3 ítélete áll**, és ez az érv
lényegesen erősebb: a `fcompp` négyese pozitívan megnevezi a mezőket.

### 39.2 ⛔ ÖNHELYESBÍTÉS: a 20.3 MÁSIK érve nem áll

A 20.3 azzal is érvelt, hogy „a `[edx+0x30]`-on át `+0x288`-ig indexel,
ami csomópontnál hivatkozásszámlált sztring volna", és a
`mov edx,[edx+0x20]`-ra hivatkozott. **A második hivatkozás téves:**
a `0x008685f6`-on az `edx`-et **ÚJRATÖLTIK** (`mov edx,[ecx]` = a
vtábla-mutató), tehát a `0x008685f8` `mov edx,[edx+0x20]` egy
**virtuális metódus kikeresése**, nem csomópont-mező. A következtetés
nem változik — az érv viszont nem használható.

### 39.3 A fogantyú-kezelő aritmetikája SZÖG, nem `scale`

| konstans | cím(ek) | mi |
|---|---|---|
| **57,29578** (= 180/π) | `0x008685de`, `0x008688b6`, `0x00868b8a`, `0x00868c68`, `0x00868d62` | radián → fok |
| −57,29578 | `0x008688e1` | ellenkező irány |
| 3,0 · 15,0 · 7,0 · 45,0 | `0x00868c0f`–`0x00868c2d` | szög-besnappelés |
| 0,25 · 0,8 | `0x00868697`, `0x00868b1d` | küszöb, illetve arány |
| 100,0 | `0x00868e07` | a `Scale: %d%%` kijelzés (20.3) |

A két kollázs-sávbeli segédfüggvénye (`FUN_00867ff0` 256 b,
`FUN_00867f70` 124 b) **egyetlen csomópont-float mezőt sem ír** (az
utóbbiban egy `mov +0x18` egész írás van).

⇒ **A fogantyú-kezelő nem írja a csomópont `scale`-jét.**

### 39.4 Mérés az `AI2`-n — a két tört érték, és ami hiányzik

| # | `w` (lapegység) | `scale` |
|---:|---:|---:|
| 0 | 246,12 | **295,392395** |
| 1–3 | 280,8 | 337 |
| 4 | 252,46 | 303 |
| 5 | 233,30 | 280 |
| 6 | 219,13 | 263 |
| 7 | 222,97 | **267,607788** |
| 8 | 198,30 | 238 |

A hat elemű létrából (17.5: 238 · 249 · 263 · 280 · 303 · 337) a **249
hiányzik** a fájlból — összhangban a 17.5 olvasatával, hogy a kézi
átméretezés **létra-értéket vált ki**.

⚠️ **Képletet a két pontra NEM illesztünk.** (A két érték összege
`563,000183`; ez érdekes, de két számból semmi nem következik, és a
„szabad paraméter elnyeli a hibát" csapdája ide is érvényes.)

### 39.5 Hol tart a K1, és a KÖVETKEZŐ lépés

A kézi átméretezés **bizonyítottan** megváltoztatja a `scale`-t (39.4), a
fogantyú-kezelő viszont **nem írja** (39.3). ⇒ az átméretezés
**parancson/visszavonáson át** érvényesül, nem közvetlen mezőírással.

**Következő, megnevezve:**

1. a `FUN_00868570` **húzás-VÉGE** ága — hol állítja vissza a
   `pan_hand_normal` kurzort, és **milyen parancsot ad ki** ott;
2. a `CollageNodeHandler::vftable` (`rtti` `0x00cc3bcc`) tizenkettedik
   bejegyzése, `0x007e6bf0` — a 20.3 ezt nevezte meg a fogantyúk
   gazdájaként, de a saját írásait nem mértük ki.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 40. K1 — az átméretezés PARANCSA megvan (`collage_adapt`), és benne az 1/1024 átváltás (2026-09-08, #1412)

*192. kutatói kör. A 39.5 (1) lépését viszi: a húzás-vége ág és az ott
kiadott parancs.*

### 40.1 ⭐ A húzás VÉGE egy NEVESÍTETT üzenetet ad ki

`FUN_00868570` (a fogantyú-kezelő) záró ága:

```
0x00868a88  mov edx, 0xcb9d60   ; collagepanel/angletext  — a kijelzés elrejtése
0x00868a9a  mov edx, 0xcb9d84   ; collagepanel/scaletext  — ua.
0x00868aa4  push 0xcbeeb0       ; "collage_adapt"
0x00868aa9  mov eax, 0xd        ; = 13 = a sztring hossza
0x00868aba  call 0x00985ff0     ; sztring-objektum építése
0x00868ac2  push ebx            ; a panel  ([ebp+8])
0x00868ace  call 0x00591560     ; üzenet-objektum építése
0x00868ad8  mov eax,[ebx] · mov edx,[eax+0x70] · call edx   ; VIRTUÁLIS hívás a panelen
```

⇒ a húzás végén a kezelő a **panel `vtable + 0x70`** bejegyzését hívja egy
`"collage_adapt"` nevű üzenettel. A `CollagePanel::vftable`
(`rtti`, `0x00c9e664`) **28. bejegyzése** (offset `0x70`) =
**`FUN_0062cda0`**.

### 40.2 ⭐ A kezelő-lánc — a sztring HÁROM hivatkozója

| függvény | szerep |
|---|---|
| `0x00868570` (2326 b) | a **küldő** (fogantyú-kezelő) |
| **`0x0082cb50`** (2581 b) | **`CCollageUI::vftable[4]`** — az üzenet-elosztó |
| `0x008860e0` (642 b) | `CollagePreviewHandler::vftable[3]` |

Az elosztóban a `collage_adapt` ága azonosítható: `0x0082d40b`
`mov esi, 0xcbeeb0` · `0x0082d410` `mov ecx, 0xe` (14 bájt) ·
`0x0082d417` `repe cmpsb`, és egyezés esetén

```
0x0082d43c  mov ecx,[esp+0x10] · push ecx
0x0082d441  call 0x0083d730          ; ← a PARANCS VÉGREHAJTÓJA
```

### 40.3 ⭐ A végrehajtó megépíti az 1024-es EGYSÉGET

`FUN_0083d730` (1215 b), `0x0083d788`–`0x0083d7b8`:

```
call eax                        ; → egy RECT mutatója
fld  [eax+8]  ·  fsub [eax]     ; = a téglalap SZÉLESSÉGE
fstp [esp+0x14]  ·  fld [esp+0x14]
fmul qword [0x00cf3f68]         ; = 0,0009765625  =  1/1024
fstp [esp+0x4c]                 ; → egy LAPEGYSÉG mérete képpontban
```

⇒ **Ez az első hely az egész vizsgálatban, ahol a `.cxf` 1024-es
egységrendszere a KÓDBAN ÉPÜL FEL**, nem a fájlokból következtetve
(a 17.3 méréssel állapította meg). A konstans a `0x00cf3f68`-on áll.

*Bizonyítottsági fok: **megerősített** — a konstans kiolvasva, a művelet
utasításonként.*

### 40.4 A 26.4 ítélete a `FUN_0083d730`-ról ÁLL — most pozitív okkal

A 26.4 a függvény „`+0x2c := +0x40`" másolását a panel állapot-mentésének
minősítette. Ez **áll**, és most meg is nevezhető, miért: a függvény **két
párhuzamos, hatelemű mezőcsoportot** ír, egymástól `0x14` eltolással —

| csoport | mezők | cím |
|---|---|---|
| A | `+0x2c` · `+0x30` · `+0x34` · `+0x35` · `+0x36` · `+0x3c` | `0x0083dbc6`–`0x0083dbe5` |
| B | `+0x40` · `+0x44` · `+0x48` · `+0x49` · `+0x4a` · `+0x4c` | `0x0083d74d`–`0x0083d76a` |

Ez **mentés/visszaállítás pár**, nem az 56 bájtos csomópont (amelyben a
`+0x34`/`+0x35`/`+0x36` nem külön bájtmezők).

### 40.5 A KÖVETKEZŐ lépés, megnevezve

**A `[esp+0x4c]` (a lapegység képpontban) útjának végigkövetése** a
`FUN_0083d730` ciklusán, amely a `[[esi+0xe8]+0x19c] >> 1` gyerekeken megy
végig (`0x0083d792`–`0x0083d7d7`): hol szorozzák/osztják vele, és eljut-e
az eredmény egy csomópont `+0x2c` mezőjéig.

Ez az első olyan nyom, amely **egyszerre** kapcsolódik (a) az
átméretezéshez, amelyről empirikusan tudjuk, hogy változtat (39.4), és
(b) a `.cxf` egységrendszeréhez.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 41. K1 — a `collage_adapt` BÉLYEGKÉP-SZINTET vált, nem geometriát (2026-09-08, #1412)

*193. kutatói kör. A 40.5 lépését viszi: a lapegység (`[esp+0x4c]`) útja a
`FUN_0083d730` gyerek-ciklusán.*

### 41.1 A ciklus törzse, utasításonként

A lapegység **kétszer** szerepel a függvényben: `0x0083d7b8` (előállítás)
és `0x0083d830` (felhasználás) — más sehol.

```
U = [esp+0x4c]                  ; a lapegység képpontban (40.3)
A = [ebx+0x168]  ·  B = [ebx+0x16c]      ; a csomópont-objektum két float tagja
0x0083d836  [esp+0x20] = A × U
0x0083d84c  [esp+0x18] = U × B
0x0083d856  h  = [esp+0x44] − [esp+0x3c]         ; a téglalap egyik oldala
0x0083d86a  ecx = (int)( h × (U × B) )           ; csonkolva (or eax,0xc00)
0x0083d87e  w  = [esp+0x40] − [esp+0x38]         ; a másik oldal
0x0083d89c  eax = (int)( w × (A × U) )
0x0083d8b0  eax = MAX(eax, ecx)                  ; a NAGYOBB oldal képpontban
```

### 41.2 ⭐ És a MAX-ból BÉLYEGKÉP-SZINT lesz

```
0x0083d8c0  esi = 0
            amíg  eax > [esi*4 + 0x00c7da84]  és  esi < 4:  esi++
0x0083d8d1  … majd a panel [+0x270] objektumán  call 0x008366c0
```

⇒ **A `collage_adapt` parancs a csomópont KÉPPONTBAN mért méretéből
bélyegkép-SZINTET választ, és azt kéri be.** Geometriát **nem** ír: a
40.4 szerinti mezőírásai a mentés/visszaállítás párt érintik, nem a
csomópontot.

*Bizonyítottsági fok: **megerősített** — a ciklus utasításonként, a
küszöbtábla kiolvasva.*

### 41.3 ⭐ A BÉLYEGKÉP-SZINTEK kiolvasva: 72 · 144 · 288 · 640 · 1024

A `0x00c7da84`-en álló tábla első öt `dword`-je:

| index | küszöb (képpont) |
|---:|---:|
| 0 | **72** |
| 1 | **144** |
| 2 | **288** |
| 3 | **640** |
| 4 | **1024** |

A ciklus az első **négyet** hasonlítja (`esi < 4`), és ha mindnél nagyobb,
a `esi = 4` marad ⇒ **öt szint**, a legnagyobb az 1024.

*(A tábla utáni két érték — `0,33` és `1024,0` — más célú konstans;
a szintekhez nem tartoznak.)*

### 41.4 ⛔ Amit ez a K1-re nézve kimond

A húzás végén kiadott parancs (40.1) tehát **nem** alkalmazza a
`scale`-t — bélyegképet vált. ⇒ a kézi átméretezés hatása a `scale`-re
vagy **húzás közben** érvényesül, vagy **másik parancson** át.

**A KÖVETKEZŐ lépés:** a `FUN_00868570` **húzás-KÖZBENI** ága —
a `pan_hand_drag` (`0xc7ed28`) beállítása körül (`0x008687ae`): mit ír a
kezelő minden egérmozgásra, és eljut-e valami a csomópont `+0x2c`-jéig.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 42. K1 — a fogantyú-kezelő TELJES írás-listája, és egy bizonyítottsági fok helyesbítése (2026-09-08, #1412)

*194. kutatói kör. A 41.4 lépését viszi: a húzás-KÖZBENI ág.*

### 42.1 A `FUN_00868570` MINDEN vermen kívüli írása — egyik sem csomópont

| cím | írás | mi |
|---|---|---|
| `0x008685c4` · `0x008685ca` | `[edx+0x28]` · `[edx+0x2c]` | a húzási **pont** (x, y) — 39.1 |
| `0x00868750` · `0x0086875c` | `fstp **qword** [esi+0x10]` · `[edx+0x20]` | **`double`**-ök — a csomópont mezői 4 bájtos `float`-ok (26.1) ⇒ nem csomópont |
| `0x008687bb` | `[eax]` | mutató |
| `0x00868826` · `0x008689f8` · `0x00868a8d` · `0x00868a91` · `0x00868b30` | bájtjelzők (`+8`, `+9`) | kijelzés-állapot |
| `0x008688b3` · `0x008688bc` · `0x008688de` · `0x008688e7` · `0x00868912` | `[edi+0x18]` · `[+0x14]` · `[+0x10]` · `[+0xc]` · `[+0x1c]` | **öt egymást követő float** `+0xc`-től `+0x1c`-ig |
| `0x00868e65` · `0x00868e6c` | `[eax+0x196]` · `[eax+0x194]` | kurzor-jelzők |

Az `[edi+0xc … +0x1c]` ötös **nem** a csomópont: annak hat float mezője
`+0x18`-tól `+0x2c`-ig tart (26.1), a `+0xc`/`+0x10`/`+0x14` pedig ott
**mutató/egész** (37.2 mezőtérképe). ⇒ **a fogantyú-kezelő sem húzás
közben, sem a végén nem ír kollázs-csomópontot.**

*Bizonyítottsági fok: **megerősített** — a függvény teljes írás-listája,
nem minta.*

### 42.2 A CollagePreviewHandler sem — és egy új sztring

A `CollagePreviewHandler::vftable` (`rtti` `0x00cbf554`) tizenhárom saját
bejegyzése és a `CollageDeselectHandler` (`0x00cbf598`) átvizsgálva:
**egyik sem ír csomópont-mezőt** (`+0x18`…`+0x2c`).

⭐ Melléklelet: a `FUN_008860e0` (642 b) sztringkészlete **`collage_adapt`
ÉS `collage_autosave`** — az utóbbi a specben eddig nem szerepelt; ez a
piszkozat-mentés kiváltó üzenete.

### 42.3 ⛔ HELYESBÍTÉS: a 17.5 ok-tulajdonítása `erős`, nem `megerősített`

A 17.5 két állítást tesz:

1. **a `scale` 95/97 esetben egész, és a `picturepile` hat értéke hat
   független kollázsban betű szerint azonos** — ez **számolás**, tehát
   **megerősített**;
2. **a két tört érték az `AI2`-ben a KÉZI ÁTMÉRETEZÉSTŐL van** — ez
   **következtetés** („ez az egyetlen minta, amelyben a tulajdonos
   csomópontot húzott át"), nem mérés.

A 39.–42. kör a húzási utat végig kimérte, és **egyetlen kódút sem írja a
csomópont `scale`-jét**. Ezért a 2. állítás bizonyítottsági foka
**`erős`**, nem `megerősített`.

**Egy versenyző magyarázat KIZÁRVA, méréssel:** a betöltéskori szorzás
(20.4, `#2593`) **egységes** tényezővel hatna, tehát mind a kilenc értéket
mozdítaná. A mérés (39.4) szerint **hét érték pontos létra-egész**, és a
két tört értéknek nincs közös aránya egyetlen létra-értékhez sem
(`295,392395 / 337 = 0,876535` vs `267,607788 / 249 = 1,074730`).
⇒ a változás **csomópontonkénti**, nem lapszintű.

### 42.4 A KÖVETKEZŐ lépés, megnevezve

A panel **két** dokumentumot tart (36.2: `[+0x138]` munkapéldány,
`[+0x1b0]` rögzített példány), és mindkét irányban másol közöttük — ez
**visszavonás-pár**. Ha a csomópontonkénti változás nem a rajzoló
kezelőkön át megy, akkor a **parancs/visszavonás** nyilvántartásban kell
lennie.

**Konkrétan:** a `FUN_0083d090` (534 b) — az egyetlen hívási hely, amely a
**`+0x1b0` → `+0x138`** irányban másol (36.2), tehát a *visszaállítás*
oldala. A hívóláncát kell kiolvasni: ki és mikor rögzít, illetve állít
vissza, és hol keletkezik a rögzítendő ÚJ állapot.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 43. K1 — a kollázspanel KÉT dokumentumának állapotgépe: alap és munkapéldány (2026-09-08, #1412)

*195. kutatói kör. A 42.4 lépését viszi: a `FUN_0083d090` hívólánca.*

### 43.1 ⭐ A visszaállítót a **RESET gomb** hívja

A `FUN_0083d090`-nek **egyetlen** hivatkozója van: a parancs-elosztó
`FUN_0082d570` (4721 b). A hívás előtti sztring-összehasonlítás:

```
0x0082e2a8  mov esi, 0xcbefac      ; "collagepanel/resetbutton"
0x0082e2ad  mov ecx, 0x19          ; 25 bájt (24 karakter + lezáró)
0x0082e2b4  repe cmpsb
0x0082e2d1  cmp eax, 0xcbefac      ; a rövidebb ág: azonosság-összevetés
0x0082e2e1  call 0x0083d090
```

és a `FUN_0083d090` első érdemi művelete:

```
0x0083d099  lea ecx,[esi+0x1b0]   ·  0x0083d09f  lea eax,[esi+0x138]
0x0083d0a5  push ecx  ·  0x0083d0a6  push eax   ; 1. arg = CÉL (36.1)
0x0083d0a7  call 0x00833cf0                     ;  +0x1b0  →  +0x138
```

⇒ **`[+0x1b0]` az ALAPÁLLAPOT, `[+0x138]` a MUNKAPÉLDÁNY**, és a
`collagepanel/resetbutton` az alapot másolja vissza a munkapéldányba.

### 43.2 A másik irány: RÖGZÍTÉS, és mi váltja ki

| hely | hívó | irány | közvetlenül előtte |
|---|---|---|---|
| `0x00831ab0` | `FUN_00831750` (vezérlő-kezelő) | `+0x138 → +0x1b0` | **`0x00831a9d call 0x00831420`** — a munkapéldány ÚJRAÉPÍTÉSE a panel beállításaiból (37.1) |
| `0x0082bffb` | `FUN_0082a670` (kollázspanel) | `+0x138 → +0x1b0` | `[ebx+0xc] = 1`, `[ebx+0x18] = 0` jelzők |

⇒ a menet: **beállítás változik → a munkapéldány újraépül a
beállításokból → rögzítés az alapba.**

### 43.3 ⭐ Amit ez MEGMAGYARÁZ: a 38.2 `scale = 1,0`-ja nem ellentmondás

A 38.2 kimérte, hogy az újraépítő (`FUN_0087dcd0`) minden csomópontot
`scale = 1,0`-val fűz hozzá. A 43.2 fényében ez **nem** ellentmondás,
hanem a **regenerálás** szemantikája: egy beállítás megváltoztatása a
kollázst **nulláról** építi újra, és ilyenkor minden csomópont
alaphelyzetből indul.

⇒ **A mintáinkban álló 313 / 500 / 256 / 158 tehát olyan állapotból
való, amelyet a beállítás-változás UTÁN már nem regeneráltak.**

*Bizonyítottsági fok: **megerősített** a két irány és a kiváltó
(címekkel); **erős** a „regenerálás" olvasat — a `FUN_00831420` kapuja
(`[ebp+0x130]`) mögötti feltételt nem olvastuk ki.*

### 43.4 A KÖVETKEZŐ lépés, megnevezve

**Melyik dokumentumot MENTI a program?** A mentés-szervezőt
(`FUN_00834700`) a 36.4 szerint az autosave-szál a **saját másolatával**
hívja, amit a konstruktora érték szerint kapott. A kérdés tehát:

> a panel melyik mezőjéből (`[+0x138]` munkapéldány vagy `[+0x1b0]` alap)
> készül az a másolat, amely a mentőhöz eljut?

Ez zárt kérdés: a `FUN_00838ef0` (az autosave-ktor, `ret 0x54`) hívóit
kell kiolvasni — ki tolja fel a dokumentumot érték szerint, és melyik
mezőből.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 44. K1 — a mentett dokumentum egy HARMADIK példány: a kezelő `[+0x64]`-e (2026-09-08, #1412)

*196. kutatói kör. A 43.4 lépését viszi: melyik dokumentumot menti a
program.*

### 44.1 ⭐ Az autosave-lánc, és amit ÉRTÉK SZERINT visz

`FUN_008390e0` (283 b) — az autosave-szál létrehozója:

```
0x008390e9  call 0x0097c5d0(0x28)          ; 40 bájtos objektum
0x008390f7  [eax] = 0x00c81db4             ; ytProgress::vftable  (rtti)
0x00839122  [ebp+0xbc] = eax               ; eltárolva a gazdában
0x00839133  call 0x00c0769f(0x14d4)        ; az autosave-szál objektuma
0x00839141  sub esp, 0x50                  ; hely a dokumentum ÉRTÉK SZERINTI másolatának
0x00839144  lea eax, [ebp+0x64]            ; ← a FORRÁS
0x0083914a  call 0x00839200                ; a dokumentum másoló konstruktora
0x0083915b  push [ebp+0xb4]  ·  0x0083915c  call 0x00838ef0   ; az autosave-ktor (36.4)
```

⇒ **a mentésre kerülő dokumentum a gazda `[+0x64]` mezője** — nem a panel
`[+0x138]` munkapéldánya és nem a `[+0x1b0]` alapja (43.1).

### 44.2 ⭐ Ki a gazda: a kollázs-KEZELŐ / feladat

A `FUN_008390e0` **két** hivatkozója:

| hívó | sztringjei |
|---|---|
| `FUN_0083ba60` (2887 b) | `Picasa` · `locate` · `Cancel` · `il_CancelButton` · `collage` · `indexonlyreadonly` |
| `FUN_008419e0` (1974 b) | `autosave` · **`Recovered Autosave`** · `collage::autosave` · `collage::recoveredautosave` |

és a dokumentum-másoló konstruktor (`FUN_00839200`) hívóinak családja:

| hívó | sztringjei |
|---|---|
| `FUN_0083dbf0` (546 b) | `Picasa` · `autosave` · `Collages` · **`CCollageManager::CollagesFolder`** · `CollageAutosave` |
| `FUN_0083c5b0` (2260 b) | `Picasa` · `collage` · `indexonly` · `autosave` · `Collages` |
| `FUN_0088a020` (740 b) | **`Collage Finished! (click to view)`** · `collage::done` |
| `FUN_00884040` · `FUN_008844d0` | (a `CRegularGridTheme` slot0/slot2) |

⇒ **Létezik egy HARMADIK kollázs-dokumentum**: a **kezelő/feladat**
objektumának `[+0x64]` mezője, és a mentés/autosave **ezt** sorosítja.

*Bizonyítottsági fok: **megerősített** a lánc (címekkel) és a
`ytProgress` vtábla; **erős** a „kezelő" megnevezés — a `[+0x64]`-et
tartó osztályt az `rtti` nem nevezi meg közvetlenül, a sztringkészlet
azonosítja (`CCollageManager::CollagesFolder`).*

### 44.3 ⛳ Amit ez a K1-re nézve KIMOND

A 38.2 (`scale = 1,0` a panel dokumentum-építőjében) és a 43.3
(regenerálás) **a panel dokumentumaira** vonatkozik. A `.cxf`-be viszont a
**kezelő `[+0x64]`-e** kerül.

⇒ **A K1 kérdését erre a példányra kell feltenni:** hogyan kapja a kezelő
dokumentuma a csomópontjait, és mi kerül ott a `+0x2c`-be?

**A KÖVETKEZŐ lépés, zárt halmazon:**

1. a `FUN_00839200` (dokumentum-másoló ktor) **nyolc** hívója közül
   azonosítani, melyik tölti fel a kezelő `[+0x64]`-ét, és **honnan**;
2. a `FUN_00833cf0` (dokumentum-értékadás) két még be nem sorolt
   célpontja: `0x0088b139` (`esi`) és `0x00889e54` — ezek valamelyike a
   `[+0x64]` is lehet.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 45. K1 — a dokumentum-másoló KILENC helye besorolva, és a headless felület `[+0x138]`-a (2026-09-08, #1412)

*197. kutatói kör. A 44.3 ZÁRT halmazát viszi végig: a `FUN_00839200`
hívóit és a `FUN_00833cf0` két be nem sorolt célpontját.*

### 45.1 A dokumentum-másoló konstruktor iránya — a KÓDBÓL

`FUN_00839200` feje: `0x00839201` `mov ebx,[esp+8]` (a **tolt**
argumentum), `0x00839205` `mov al,[ebx]` → `0x00839207` `mov [esi],al`.

⇒ **a tolt argumentum a FORRÁS, az `ESI` a CÉL.** (A 35.1 és a 36.1
tanulsága szerint ezt minden másolónál külön ki kell olvasni.)

### 45.2 A kilenc hívási hely

| cím | hívó | FORRÁS | CÉL |
|---|---|---|---|
| `0x0083914a` | `FUN_008390e0` | **`[ebp+0x64]`** (a kezelő doksija, 44.1) | verem (érték szerinti argumentum) |
| `0x0083c17d` | `FUN_0083ba60` | `[esp+0x60]` | `[esp+0xc4]` |
| `0x0083c43f` | `FUN_0083ba60` | `[esp+0xb0]` | verem |
| **`0x0083cb13`** | **`FUN_0083c5b0`** (mentés: `Collages`, `autosave`, `indexonly`) | **`[esp+0x20] + 0x138`** | `[esp+0x54]` |
| `0x0083dd7f` | `FUN_0083dbf0` | `[esp+0x18]` | **`[edi+0x48]`** |
| `0x008420db` | `FUN_008419e0` (`Recovered Autosave`) | `[esp+0xb8]` | verem |
| `0x0088407e` | `FUN_00884040` (`CRegularGridTheme` slot0) | **`eax + 0x138`** | `[esp+0x24]` |
| `0x0088497b` | `FUN_008844d0` (`CRegularGridTheme` slot2) | **`[edi+8] + 0x138`** | `[esp+0x24]` |
| `0x0088a07d` | `FUN_0088a020` (`collage::done`) | `[ebp+0xc]` | verem |

⇒ **három hely másol egy objektum `+0x138`-asából** — a mentési út és a
`regulargrid` téma két slotja.

### 45.3 ⭐ Az autosave-szál dokumentuma a `[+0x48]`-ra kerül — a kör bezárul

`FUN_0083dbf0` (546 b, sztringjei `CCollageManager::CollagesFolder`,
`CollageAutosave`):

```
0x0083dd76  lea esi, [edi + 0x48]          ; CÉL
0x0083dd79  mov dword ptr [edi], 0xcbfed0  ; CAutosaveCollageThread::vftable (rtti)
0x0083dd7f  call 0x00839200                ; a dokumentum bemásolása
```

⇒ pontosan az a mező, amit a szál futtató metódusa ment
(`0x008393a6 lea edx,[esi+0x48]` → a mentés-szervező, 36.4). **A lánc
zárt.**

### 45.4 ⭐ `FUN_00889e00` = a `CHeadlessCollageUI` KONSTRUKTORA — és neki is van `[+0x138]`-a

```
0x00889e10  [edi]   = 0x00cc4eec     ; CHeadlessCollageUI::vftable   (33.5)
0x00889e16  [edi+4] = 0x00cc4f2c     ; ua. (második altábla)
0x00889e1d  [edi+8] = 0x00cc4f34     ; ua. (harmadik)
0x00889e2f  lea edx, [edi + 0x138]   ; CÉL
0x00889e54  call 0x00833cf0          ; FORRÁS: [esp+0x18] — érték szerinti argumentum
```

⇒ **a headless felület ugyanazt a `+0x138` elrendezést használja, mint az
interaktív panel** (43.1), és a dokumentumát **kívülről, érték szerint**
kapja a konstrukciókor.

A `FUN_0088b0a0` (207 b) ugyanilyen alakú: beágyazott dokumentumot
inicializál (`0x0088b0f4 call 0x008342b0`), majd a `0x0088b139`-en
belemásol egy érték szerint kapott dokumentumot.

⇒ **a 44.3 zárt halmaza ezzel KIMERÜLT** — mindkét addig be nem sorolt
`FUN_00833cf0`-célpont konstruktor.

### 45.5 A KÖVETKEZŐ lépés, megnevezve

A mentési út (`FUN_0083c5b0`, `0x0083cb13`) egy objektum **`+0x138`**-asából
másol — és a `+0x138` **mindkét** felületnek a munkapéldánya (az
interaktívnak 43.1, a headlessnek 45.4). ⇒ a következő kérdés:

> **melyik objektum áll a `FUN_0083c5b0`-ban a `[esp+0x20]`-on** — az
> interaktív panel, vagy egy headless felület?

Ez zárt kérdés: a `FUN_0083c5b0` (2260 b) elejétől követni kell, mi kerül
a `[esp+0x20]`-ra.

⚠️ **Amit ez már most kimond:** a mentett dokumentum **nem** feltétlenül
a kezelő `[+0x64]`-e (44.1) — az az **autosave** útja. A **kifejezett
mentés** egy felület **munkapéldányából** dolgozik.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 46. K1 — a mentési utat a BEZÁRÁS-MEGERŐSÍTÉS hívja, és a mentett doksi az 1. argumentum `+0x138`-asa (2026-09-08, #1412)

*198. kutatói kör. A 45.5 lépését viszi: melyik objektum áll a
`FUN_0083c5b0`-ban a `[esp+0x20]`-on.*

### 46.1 ⭐ A mentési útnak EGYETLEN hívója van — a bezárás-megerősítés

`FUN_0083c5b0` (2260 b) hivatkozóinak száma az `xrefs` szerint **1**:
**`FUN_0082c0a0`** (699 b), amelynek sztringkészlete

`Cancel` · `il_CancelButton` · **`Discard Changes`** · `autosave` ·
**`Please Confirm...`** · **`CCollageUI::ConfirmCloseTitle`**

⇒ **a `.cxf` a BEZÁRÁS-MEGERŐSÍTÉS ágán íródik** — pontosan az a
párbeszéd, amit a 3.1 szakasz ír le („Bezárás" — a piszkozat ága). Ez az
első hely, ahol az életciklus 3. szakasza és a mentési lánc **összeér**.

### 46.2 ⭐ A mentett dokumentum: az 1. argumentum `+0x138`-asa

**A hívás** (`FUN_0082c0a0`):

```
0x0082c2ef  mov eax,[ebp+0xc]     ; a 2. argumentum lesz
0x0082c2f2  mov ecx,[esp+0x18]    ; az 1. argumentum lesz
0x0082c2f6  push eax  ·  0x0082c2f7  push ecx   ; az UTOLJÁRA tolt az 1.
0x0082c2f8  call 0x0083c5b0
```

**A hívottban** (`FUN_0083c5b0`):

```
0x0083c5c9  mov ebx,[esp+0x3d94]  ; = az 1. argumentum
0x0083c5d3  mov [esp+0x20], ebx   ; eltéve
…
0x0083cb05  mov eax,[esp+0x20]  ·  0x0083cb09  add eax, 0x138
0x0083cb0e  push eax  ·  0x0083cb13  call 0x00839200   ; FORRÁS (45.1)
```

⇒ **a mentésre kerülő dokumentum az 1. argumentumként kapott objektum
`+0x138` MUNKAPÉLDÁNYA** (43.1 / 45.4).

*Bizonyítottsági fok: **megerősített** — a hívás és a hívott oldala is
utasításonként, a 45.1 megállapodásával.*

### 46.3 ⚠️ Amit a kör NEM mond ki

Hogy a `FUN_0082c0a0`-beli `[esp+0x18]` **azonos-e** a függvény saját
1. argumentumával (`[ebp+8]`, amit a `0x0082c0ce` tesz el egy
`push 0xcbecf8` UTÁN). A két hivatkozás **eltérő veremmélységen** áll, és
a 38.1 tanulsága szerint az ilyet **nem szabad megtippelni**.

### 46.4 A KÖVETKEZŐ lépés, megnevezve

A `FUN_0082c0a0` (699 b) saját keretének feloldása a `[esp+0x18]`-ra —
onnan derül ki, **melyik felület** (az interaktív `CCollageUI` vagy egy
`CHeadlessCollageUI`, 45.4) munkapéldánya kerül a fájlba.

A függvény kicsi és a `[esp+0x18]`-at csak **két** helyen érinti
(`0x0082c2f2` és `0x0082c32e`), tehát a keret a 38.1
mezőminta-módszerével vagy a hívási helyek összevetésével feloldható.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 47. K1 — a mentett dokumentum az INTERAKTÍV PANEL munkapéldánya, és a bezárás előbb ÚJRAÉPÍTHETI (2026-09-08, #1412)

*199. kutatói kör. A 46.4 lépését viszi: a `FUN_0082c0a0` kerete.*

### 47.1 ⭐ A keret feloldva — nem mélységszámolással, hanem a HÍVÁS-TAKARÍTÁSBÓL

A saját verem-normalizálónk ezen a függvényen **öt ütközést** jelzett,
tehát a lineáris követés **nem** megbízható (a mérő ezt ki is írja). A
kérdés mégis eldönthető, két horgonyból:

1. **A függvény vége:** `0x0082c30d`–`0x0082c321`
   (`pop edi` · `pop esi` · `pop ebx` … `ret 8`) ⇒ a `0x0082c2f2`-nél a
   verem a **prológus-mélységen** áll (a `0x0082c2f8`-as hívás két tolt
   argumentumát a hívott takarítja).
2. **A prológus:** a `0x0082c0c0` `push 0xcbecf8`-at a `0x0082c0da`
   `call 0x00985ff0` (sztring-konstruktor) **elfogyasztja** ⇒ a
   `0x0082c0ce`-nél a mélység prológus **+4**, tehát az ottani
   `[esp+0x1c]` **ugyanaz a rekesz**, mint a `0x0082c2f2`-nél a
   `[esp+0x18]`.

⇒ **a mentési út 1. argumentuma = a `FUN_0082c0a0` saját 1. argumentuma**
(`[ebp+8]`, amit a `0x0082c0bb` tesz `ebx`-be).

*Bizonyítottsági fok: **megerősített** — mindkét horgony utasításszinten.*

### 47.2 ⭐ És a `[ebp+8]` a kollázs-PANEL

Ugyanez az `ebx` megy a `0x0082c109`-en a **`FUN_00831420`**-ba
(`0x0082c106 push 0` · `0x0082c108 push ebx`) — abba a függvénybe, amely a
**panel `[+0x138]` dokumentumát építi újra** a panel `[+0x130]`,
`[+0x13c]`, `[+0x168]`, `[+0x170]`, `[+0x174]` mezőiből (37.1).

⇒ **a mentett dokumentum az INTERAKTÍV panel (`CCollageUI`) `[+0x138]`
munkapéldánya** (43.1) — nem egy headless felületé (45.4).

### 47.3 ⭐ A bezárás ELŐBB újraépítheti a munkapéldányt

```
0x0082c0fc  cmp byte ptr [ebp+0xc], 0     ; a 2. argumentum (jelző)
0x0082c104  jne 0x0082c10e                ; ha NEM nulla → kihagyja
0x0082c106  push 0  ·  0x0082c108  push ebx
0x0082c109  call 0x00831420               ; a munkapéldány ÚJRAÉPÍTÉSE
…
0x0082c2ef  mov eax,[ebp+0xc]             ; ugyanez a jelző megy tovább
0x0082c2f8  call 0x0083c5b0               ; …a mentési út 2. argumentumaként
```

⇒ **ha a 2. argumentum nulla, a bezárás a mentés ELŐTT újraépíti a
munkapéldányt** — és a 38.2 szerint az újraépítés minden csomópontnak
`scale = 1,0`-t ad.

### 47.4 ⛳ Amit ez KIMOND, és amit NEM

**Kimondja:** a `.cxf` a bezárás ágán, az interaktív panel
munkapéldányából íródik, és ezen az ágon van egy **feltételes
újraépítés**, amely a `scale`-t `1,0`-ra állítaná.

**Nem mondja ki**, hogy az újraépítés a valóságban lefut-e: a
`FUN_00831420`-nak **saját kapuja** van (`0x0083142b`
`cmp [ebp+0x130], 0` → ha nulla, nem csinál semmit, 37.1), és ezt a
mezőt még nem olvastuk ki. A mintáink `313 / 500 / 256 / 158` értékei
azt mutatják, hogy legalább az ő esetükben **nem** futott le.

**A KÖVETKEZŐ lépés:** a panel `[+0x130]` mezőjének azonosítása — ki
állítja, mikor, és mit jelent. Ez a kapu dönti el, hogy a bezárás
regenerál-e; és ha a mintáinkban nem regenerált, akkor a `scale` értéke
egy **korábbi** állapotból való, amit a K1-nek meg kell találnia.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 48. K1 — a bezárási kapu (`[panel+0x130]`) egy ALOBJEKTUM-MUTATÓ, nem jelzőbit (2026-09-08, #1412)

*200. kutatói kör. A 47.4 lépését viszi: mi a panel `[+0x130]` mezője.*

### 48.1 ⭐ Nem jelző: birtokolt MUTATÓ, amit felszabadítanak

A kollázs-sávban a `+0x130`-at **60-nál több** hely érinti, és a
túlnyomó többség `mov ecx,[X+0x130]` **közvetlenül egy virtuális hívás
előtt** — tehát objektum-mutató. A birtoklást a
`FUN_0082c360` (`collagepanel/addclips`, `collagepanel/addallclips`)
mutatja meg:

```
0x0082c3f7  mov ecx,[esi+0x130]
0x0082c408  mov eax,[esi+0x130]  ·  0x0082c40e  push eax
0x0082c40f  call 0x0097caf0  ·  0x0082c414  add esp, 4      ; cdecl felszabadítás
0x0082c417  mov dword ptr [esi+0x130], ebx                  ; kinullázás
```

⇒ **`[+0x130]` egy birtokolt alobjektum mutatója**, nem „piszkos" jelző.

### 48.2 ⭐ Egyszerű `mov`-val SENKI nem ad neki nem-nulla értéket

Pásztázás az **egész** `.text`-en `mov dword ptr [reg+0x130], reg`
alakra (`esp`/`ebp` bázis kizárva): **24** találat az egész programban, és
ebből **kettő** érint kollázs-objektumot — **mindkettő `ebx`-et
(nullát) ír**:

| cím | hol | mit |
|---|---|---|
| `0x0082a352` | `FUN_0082a250` (a közös alap-konstruktor, a `+0x128`…`+0x134` mezőkkel együtt) | **inicializálás nullára** |
| `0x0082c417` | `FUN_0082c360` | **kinullázás a felszabadítás után** |

⇒ az értékadás **`lea`-materializált** mutatón át megy. A sávban két ilyen
hely van: `0x00830645` (`FUN_00830530` — a téma/beállítás-vezérlők
kezelője: `collagepanel/theme_popup`, `collagepanel/shadow_checkbox`,
`collage::theme`) és `0x0088ab2e` (`FUN_0088aae0`, headless ág).

### 48.3 ⛳ Amit ez a 47.4-re nézve KIMOND

A `FUN_00831420` kapuja (`0x0083142b` `cmp [panel+0x130], 0` → ha nulla,
nem csinál semmit) tehát azt kérdezi, hogy **létezik-e ez az alobjektum** —
vagyis hogy a panel **fel van-e építve**. Ez **nem** „változott-e a
beállítás" jellegű kapu.

⇒ egy normál bezárásnál a kapu **nyitva** van, tehát az újraépítés
lefutna — a mintáink viszont **nem** `1,0`-t hordoznak.

### 48.4 A KÖVETKEZŐ lépés, megnevezve

A 47.3 szerint az újraépítés **másik** feltételtől is függ: a bezárás-kezelő
**2. argumentumától** (`0x0082c0fc` `cmp byte [ebp+0xc], 0` → ha **nem
nulla**, a `FUN_00831420` hívása **kimarad**).

> **Ki hívja a `FUN_0082c0a0`-t, és mit ad át 2. argumentumként?**

Ez zárt kérdés (a függvény `ret 8`, tehát pontosan két argumentuma van), és
**ez dönti el**, hogy a valós bezárási úton regenerálódik-e a
munkapéldány. Ha a jelző nem nulla, akkor nincs regenerálás, és a `scale`
a bezárás előtti állapotból megy a fájlba — ezzel a 38.2 `1,0`-ja és a
mintáink `313 / 500 / 256 / 158`-a **összefér**.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 49. K1 — a bezárás 2. argumentuma egy PANEL-ÁLLAPOTJELZŐ, és ezzel a 38.2 ellentmondása feloldódik (2026-09-08, #1412)

*201. kutatói kör. A 48.4 lépését viszi: ki hívja a bezárás-kezelőt, és
mit ad át 2. argumentumként.*

### 49.1 ⭐ A hívó egy 36 bájtos thunk — és megmondja MINDKÉT argumentumot

`FUN_0062c650` (36 b), a bezárás-kezelő **egyetlen** hivatkozója:

```
0x0062c651  mov eax,[ecx+0x288]      ; ← az 1. argumentum lesz
0x0062c657  test eax, eax  ·  je 0x62c670   ; ha NINCS, a bezárás NO-OP (0-t ad vissza)
0x0062c65b  mov cl, byte ptr [ecx+0x20c]    ; ← a 2. argumentum lesz (BÁJT)
0x0062c667  push edx  ·  0x0062c668  push eax
0x0062c669  call 0x0082c0a0
```

⇒ két dolog egyszerre:

1. **az 1. argumentum a `[ytPanel + 0x288]`** — vagyis a `CCollageUI`
   objektum. Ez **második oldalról igazolja a 47.2-t** (ott a
   `FUN_00831420`-hívásból következtettünk rá);
2. **a 2. argumentum a `byte [ytPanel + 0x20c]`** — egy **panel-állapot
   jelzőbájt**.

### 49.2 A jelzőbájt írói — kilenc az egész programban

Pásztázás `mov byte ptr [reg+0x20c], …` alakra (`esp`/`ebp` nélkül):
**9 találat**, és a lényegesek apró, sztring nélküli 1/0 párok:

| cím | függvény | mit ír |
|---|---|---|
| `0x009e397d` · `0x009e399d` | `FUN_009e3970` · `FUN_009e3990` (21-21 b) | **1**, illetve **0** |
| `0x00a68b26` · `0x00a68bf6` | `FUN_00a68b10` · `FUN_00a68be0` (31-31 b) | **1**, illetve **0** |
| `0x00a692d0` | **`FUN_00a69250`** (137 b) = **`CollagePanel::vftable[26]`** (`rtti`) | **1** |

⇒ **állapot-jelző**, amit egy vtábla-metódus és két apró
beállító/törlő pár kapcsol.

*Bizonyítottsági fok: **megerősített** az írók listája és a vtábla-index;
**NINCS MEG** a jelző pontos jelentése (a beállítók sztring nélküliek).*

### 49.3 ⛳ És ezzel a 38.2 „ellentmondása" FELOLDÓDIK

A 47.3 szerint a bezárás-kezelő a `FUN_00831420` (újraépítés) hívását
**kihagyja**, ha a 2. argumentum **nem nulla**
(`0x0082c0fc` `cmp byte [ebp+0xc], 0` · `0x0082c104` `jne`).

⇒ **ha a panel a jelzett állapotban van, a bezárás NEM regenerál** — a
munkapéldány úgy megy a fájlba, ahogy áll.

Ezzel a 38.2 mérése (`scale = 1,0` az újraépítőben) és a mintáink
`313 / 500 / 256 / 158`-a **összefér**: az újraépítés egyszerűen **nem fut
le** azon az úton, amelyen a mintáink készültek. A 43.3 „regenerálás"
olvasata így pontosabb alakot kap: **a regenerálás feltételes, és a
bezárási úton kihagyható.**

### 49.4 Ami MARAD, és a KÖVETKEZŐ lépés

Ha a bezárás nem regenerál, akkor a `+0x138` munkapéldány tartalma
**korábbról** való. A 36.2 szerint a munkapéldányba **két** helyről kerül
adat:

| hova | honnan | hol |
|---|---|---|
| `+0x138` | verem-helyi, újraépített (`scale = 1,0`) | `0x008315b8` |
| `+0x138` | a `+0x1b0` **alapállapotból** | `0x0083d0a7` (Reset) |

és a `+0x1b0`-ba csak a `+0x138`-ból (`0x0082bffb`, `0x00831ab0`). **A két
példány tehát csak egymásból és az újraépítésből táplálkozik** — kivéve a
**konstrukciót**.

> **A KÖVETKEZŐ KÉRDÉS:** a `CCollageUI` (a `[ytPanel+0x288]` objektum)
> **konstrukciója** tölti-e fel a `+0x138`-at, és ha igen, honnan?
> A headless felületnél ez bizonyítottan így van (45.4: a ktor **érték
> szerint** kapja a dokumentumot); az interaktívra ez még nincs kimérve.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 50. K1 — az interaktív felület ktora ÜRES dokumentumot épít, ezzel a 49.4 zárt halmaza kimerült (2026-09-08, #1412)

*202. kutatói kör. A 49.4 megnevezett lépését viszi: tölti-e fel a
`CCollageUI` konstrukciója a `+0x138`-at, és ha igen, honnan.*

### 50.1 ⭐ Az interaktív `CCollageUI` LUSTÁN jön létre — és a ktor nem kap dokumentumot

A `[ytPanel+0x288]` objektum (47.2, 49.1) egyetlen helyen születik:

```
0x0062c9f6  cmp dword ptr [ebx + 0x288], 0   ; van már?
0x0062c9fd  jne 0x0062ca3a                   ; ha igen, kész
0x0062c9ff  push 0x278                       ; 632 bájt
0x0062ca04  call 0x0097c5d0                  ; operator new
0x0062ca0c  test eax, eax
0x0062ca0e  je  0x0062ca19
0x0062ca10  mov edi, eax
0x0062ca12  call 0x0082a250                  ; a konstruktor — SEMMILYEN tolt argumentummal
0x0062ca1d  mov dword ptr [ebx + 0x288], eax
```

Két mért tény:

- **az objektum mérete `0x278` = 632 bájt** (`0x0062c9ff`), tehát a
  `+0x138` és a `+0x1b0` dokumentum (43.1) beleér;
- a `0x0062ca12` hívás előtt **egyetlen `push` sincs** — a ktor csak a
  `this`-t kapja (`edi`). ⇒ **az interaktív felület konstrukciója
  kívülről NEM kap dokumentumot.**

*Bizalmi fok: megerősített* (a hívási hely utasításonként kiolvasva).

### 50.2 ⭐ A ktor a `+0x138`-at NULLÁZZA, majd `Untitled` dokumentumot épít rá

`FUN_0082a250` (651 b) érintett szakasza — `ebx = 0` végig:

```
0x0082a34c  lea eax, [edi + 0x138]      ; eax = a munkapéldány
0x0082a35e  mov [eax+4],  ebx           ; …és további tizenkét mező
   …        mov [eax+0x08 … +0x4c], ebx ; (+8 +0xc +0x10 +0x14 +0x18 +0x1c
                                        ;  +0x2c +0x34 +0x38 +0x3c +0x48 +0x4c)
0x0082a37f  push eax
0x0082a386  call 0x008342b0             ; a dokumentum-KONSTRUKTOR
```

és ugyanez a `+0x1b0` alapállapotra: `0x0082a3bd lea eax,[edi+0x1b0]` →
`0x0082a3eb call 0x008342b0`.

**A `FUN_008342b0` egyargumentumú, és nincs forrása:**

```
0x008342b2  mov ebp, [esp+0xc]          ; az EGYETLEN argumentum: a doksi
0x008342bb  mov byte ptr [ebp], 0
0x008342c4  push 0xcbf854               ; "CollageSpec::Untitled"  (erőforráskulcs)
0x008342c9  mov  eax, 0xcbf848          ; "Untitled"               (tartalék felirat)
0x008342ce  mov dword ptr [edi], 0      ; [ebp+4] = üres
0x008342d4  call 0x009ae560             ; honosított szöveg lekérése
```

A két sztring a `.rdata`-ból kiolvasva:
`0x00cbf848` = `Untitled`, `0x00cbf854` = `CollageSpec::Untitled`.

⇒ **a frissen konstruált dokumentum ÜRES és névtelen** („Untitled”).
Csomópontot nem tartalmaz, tehát `scale` mezője sincs.

*Bizalmi fok: megerősített.*

### 50.3 ⛔ Pontosítás: a `FUN_0082a500` a DESZTRUKTOR, nem második konstruktor

A `CCollageUI` három vtábla-mutatóját (`0xcbf450` / `0xcbf480` /
`0xcbf488`) **két** függvény írja: `FUN_0082a250` (`0x0082a26e`…) és
`FUN_0082a500` (`0x0082a507`…). A második **nem** konstruktor:

```
0x0082a51b  call 0x0082c360             ; a leszármazott-rész lebontása
0x0082a53f  call 0x0097caf0             ; free()
0x0082a57c  lea esi, [ebx + 0x1b0]
0x0082a588  call 0x0062c900             ; a dokumentum DESZTRUKTORA
0x0082a598  lea esi, [ebx + 0x138]
0x0082a59e  call 0x0062c900             ; ua. a munkapéldányra
```

A `0x0062c900` ugyanaz a függvény, amit a headless ktor a saját
ideiglenes dokumentumára hív (45.4, `0x00889e6d`) — tehát a
dokumentum-desztruktor. ⇒ **a `CCollageUI`-nak EGYETLEN konstruktora van**
(`FUN_0082a250`), és az az 50.1 szerint argumentum nélküli.

### 50.4 ⛳ A VÁLASZ a 49.4-re: NEM — és amit ez a K1-re nézve kimond

| kérdés (49.4) | válasz |
|---|---|
| tölti-e fel az interaktív ktor a `+0x138`-at? | **NEM** — nullázza, majd üres `Untitled` doksit épít rá (50.2) |
| a headless ktor? | **IGEN**, érték szerint (45.4) — de az egy MÁSIK osztály (`0x00889e00`) |

Ezzel a `+0x138` munkapéldány **teljes** táplálási listája
(index-független `E8 rel32` pásztázással ellenőrizve — a `FUN_00833cf0`
mind a hét hívási helye besorolva, 43.1 / 45.4 / ez a kör):

| honnan | hol | mit ad |
|---|---|---|
| konstrukció | `0x0082a386` | **üres** doksi, nulla csomópont |
| újraépítés (verem-helyi doksi) | `0x008315b8` | `scale = 1,0` (38.2) |
| `+0x1b0` alapállapot (Reset) | `0x0083d0a7` | ami korábban a `+0x138` volt |
| — és a `+0x1b0` csak a `+0x138`-ból | `0x0082bffb`, `0x00831ab0` | ua. |

⇒ **A mintáinkban mért `scale` = 313 / 500 / 256 / 158 EGYETLEN
dokumentum-szintű értékadással sem magyarázható.** A `+0x138`-ba
*egészben* csak üres doksi, `1,0`-s újraépítés, vagy önmaga másolata
kerül.

**Amiből következik — ez a kör legfontosabb állítása:** a nem-`1,0`
érték **nem dokumentum-cserével**, hanem a már élő dokumentum egy
csomópontjának **helyben történő módosításával** kerül be. A K1 keresési
tere ezzel átbillen: nem azt kell keresni, *ki adja értékül a
dokumentumot*, hanem *ki ír bele egy meglévő csomópont `+0x2c`-jébe*.

*Bizalmi fok: erős.* (A dokumentum-szintű lista mérve és kimerítő; a
„helyben módosítás" a maradék — logikai, nem közvetlenül mért állítás.)

⚠️ **Amit ez NEM mond ki:** azt sem, hogy a `.cxf` **beolvasása** hova
tölt. A 37.2 a `FUN_0087dcd0`-t kifejezetten „az ELSŐ **nem-beolvasó**
csomópont-építőnek" nevezi — a beolvasó ág tehát létezik, és mivel a
fenti listában nincs benne, csakis helyben tölthet. Ez a következő kör
első jelöltje.

### 50.5 A KÖVETKEZŐ lépés, megnevezve

> **A KÖVETKEZŐ KÉRDÉS:** ki írja a `.cxf`-BEOLVASÓ ágon a csomópont
> `+0x2c` mezőjét, és honnan veszi az értéket?

Zárt kérdés, mert a horgony megvan: a csomópont 56 bájtos (`0x38`,
32.2), a `+0x2c` a hatodik lebegőpontos mező, és a beolvasót a
`FUN_0087dcd0` „nem-beolvasó" minősítése (37.2) **negatív úton**
azonosítja. A menet: a 56 bájtos elemű vektor `push 0x38`-as
foglalói közül azok, amelyek **XML-/attribútum-sztringet** is érintenek.

*Ez ÖRÖKÖLT nyitott kérdés; a munkasorban marad.*

## 51. K1 — az UTOLSÓ nyitott út (`lea`) is negatív; a gépi keresés KIMERÜLT (2026-09-08, #1412)

*203. kutatói kör. A 17.15 által nyitva hagyott egyetlen utat viszi végig —
a `lea r,[r+0x2c]` mutatós ágat —, és tartalmi alapra helyezi a 17.10
kilenc, addig csak hívási úton kizárt találatát.*

⚠️ **A kör NEM az 50.5-öt vitte.** Az 50.5 a `.cxf`-beolvasó ágat nevezte
meg következő lépésnek — a lap **17.8** / **17.12** / **17.13** / **17.16**
szakaszai viszont ezt már teljesen kimérték (a beolvasó a `+0x68` staging-
mezőbe ír, a `push_back` onnan viszi a csomópont `+0x2c`-jébe). Az 50.5
kérdése tehát **már meg volt válaszolva**, csak az előző kör az összefoglaló
felől nézte. A kör ezért a lap szerinti *valódi* maradékra állt át.

### 51.1 A pásztázás és a POZITÍV KONTROLL

Szűrő: `lea <reg>, [<reg> + 0x2c]` a kollázs-sávban
(`0x00829000`–`0x00895000`, a 23.1 szerinti javított tartomány),
**függvényenként** diszasszemblálva (nem bájtmintával), a `functions`
indexből.

- lefedettség: **879 függvény · 434 786 / 442 368 bájt (98,3 %)**;
  index-hézag 829 darab, összesen **10 218 bájt** — ezekre a pásztázás
  **nem** nyilatkozik;
- **pozitív kontroll:** ugyanez a pásztázó `0x138` eltolással a
  `0x0082a000`–`0x0082b000` szakaszon megtalálja a `0x0082a34c`
  `lea eax,[edi+0x138]`-at (az 50.2-ben utasításonként elolvasott hely) —
  **MEGVAN**, tehát az illesztés és az igazítás jó.

Találat: **130 hely**, ebből `esp`-bázisú (verem-lokális) **119** ⇒ a
vizsgálandó halmaz **11 hely**.

### 51.2 A tizenegy hely, tételesen — mind SZTRING vagy MUTATÓ

A `FUN_00401000` a **hivatkozásszámlált sztring elengedése**
(`mov esi,[edi]` → első bájt < 0x80 vizsgálat → `[0xc40558]`), a
`FUN_005c2100` pedig a sztring **értékadása** (`mov eax,[edi]` /
`cmp eax,[esi]` → átkötés). Ez a két idióma azonosítja a `+0x2c` mezők
valódi típusát:

| cím | függvény | mi történik a `+0x2c`-vel | ítélet |
|---|---|---|---|
| `0x008300dc` | `FUN_008300c0` | `call 0x401000` → `mov [edi],0` | ⛔ sztring elengedése |
| `0x0083198a` | `FUN_00831750` | `test dword [eax],0xffffff00` · `cmp byte [eax+4],0` | ⛔ sztring-tartalom vizsgálat |
| `0x00833de6` | `FUN_00833cf0` | egész `cmp`, majd `mov [edi],eax` | ⛔ sztring átkötése (a dokumentum neve) |
| `0x00834af3` | `FUN_008347b0` | `mov ecx,esi` → `call 0x999170` → `push 0xcb1fb8` | ⛔ sztring/adatfolyam-metódus |
| `0x00860032` | `FUN_0085ff90` | `mov [edi],ebp` → `movzx edx,byte [ebp]` | ⛔ sztring átkötése |
| `0x00879909` | `FUN_008798d0` | `push esi` → `call 0x9732b0` | ⛔ sztring betétele konténerbe |
| `0x00879b7b` | `FUN_008798d0` | `shr edx,1` · `lea esi,[eax+edx*8]` · `call 0x9732b0` | ⛔ **8 bájt** lépésközű vektor `push_back`-je (a csomóponté 56) |
| `0x00879d18` | `FUN_00879d10` | `lea edi,[esi+4]` · két `call 0x401000` | ⛔ két szomszédos sztring lebontása |
| `0x0087e0cd` | `FUN_0087dcd0` | `lea esi,[esp+0x28]` · `call 0x5c2100` | ⛔ sztring **értékadás** (a forrást egy virtuális név-lekérés töltötte) |
| `0x008831c8` | `FUN_00882f20` | `mov eax,[ebx]` · `call 0xc07738` | ⛔ heap-mutató felszabadítása |
| `0x0088ab66` | `FUN_0088aae0` | `test dword [eax],0xffffff00` · `cmp byte [eax+4],0` | ⛔ sztring-tartalom vizsgálat |

⇒ **A mutatós (`lea`) úton a csomópont `+0x2c`-jére a kollázs-sávban
NINCS lebegőpontos írás.** A tizenegyből egyik sem csomópont: mindegyik
sztring vagy heap-mutató.

*Bizalmi fok: megerősített* (mind a tizenegy hely utasításonként
elolvasva; a hatókör a fenti 98,3 %-os lefedettség).

### 51.3 ⭐ A 17.10 kilenc találata is kizárva — most TARTALMI alapon

A 17.10 kimondta, hogy a tíz sávon kívüli csomópont-alakú float-íróból
csak egyet olvasott végig, a többit **hívási úton** zárta ki, és hogy
háromra (`0x0050be50`, `0x0050cdb0`, `0x0050d560`) ez a kizárás
**gyengébb**. Ez a kör mind a kilencet elolvasta:

| cím | mi ez (RTTI / sztring) | miért nem csomópont |
|---|---|---|
| `0x0050bd70` | **`CDesaturateFilter` ktora** (`Filtered B&W`, `desat`, `CDesaturateFilter::name`) | `+0x1c/+0x20/+0x24 = 0,333` (fénysúlyok), `+0x28…+0x30 = 0` — **eltolt** elrendezés, hét float |
| `0x0050be50` | ugyanez beágyazva (31 b) | ua. |
| `0x0050cdb0` | ugyanennek a **klónozója** (`+0x1c`…`+0x30` + a `+0x14` bájt átmásolása) | ua. |
| `0x0050d560` | `editslider1/editslider` | szerkesztő-csúszka, nem csomópont |
| `0x005c2350` | **`TextCursorHandler`** ktora (`0x00c94b2c`) | `+0x14 = 1,0`, `+0x18`…`+0x34` nullák, `+0x44`…`+0x50` egészek |
| `0x007e68f0` | **`GroupRingMoveHandler`** ktora (`0x00cb9e2c`) | `+0xc`…`+0x2c` nullák, `+0x20` **`qword`** (double) |
| `0x007e6930` | **`GroupRingMoveEdgeHandler`** ktora (`0x00cb9e44`) | ua. |
| `0x007e69b0` | **`GroupRingKnobHandler`** ktora (`0x00cb9e5c`) | `+0xc`…`+0x18` nullák, `+0x1c` = **1,0**, `+0x20` **`qword`**, `+0x28/+0x2c` nullák |
| `0x009d7a60` | **`ytSelectionDragHandler`** ktora (`0x00cda768`) | `+0x10`…`+0x2c` = **−1,0**, `+0x30`…`+0x48` = 0, `+0x4c` = 0,9 |

⇒ Mindegyik **konstruktor**, mindegyik **állandót** ír, és egyiknek sincs
meg a csomópont hat-float / 56 bájt lépésközű alakja. **A 17.10 gyengébb
kizárása ezzel tartalmi kizárássá erősödött.**

### 51.4 ⭐ A beolvasó NEM alakítja át az értéket — és egy finomítás a 17.16-hoz

A `scale` attribútum ága, utasításonként:

```
0x008332a0  mov eax, [edx + 4]        ; az attribútum ÉRTÉKE
0x008332a5  je  0x8332ac              ; ha nincs érték…
0x008332a7  add eax, 4
0x008332ac  mov eax, 0xc7f979         ; …akkor az ÜRES sztring
0x008332b1  push eax
0x008332b2  call 0xc080d7             ; atof
0x008332b7  fstp dword ptr [ebx + 0x68]
```

⇒ az `atof` eredménye **változatlanul**, szorzás és eltolás nélkül kerül a
staging-mezőbe. **A beolvasó nem szoroz** — ez a `.cxf` csomópont-`scale`-re
nézve kizárja a „betöltéskori átszámítás" magyarázatot. *(A `0x00c7f979`
tartalma kiolvasva: üres sztring.)*

**Finomítás a 17.16-hoz.** A 17.16 helyesen írja, hogy a `<node>` eleji
alapérték-blokk `fld1`-gyel **1,0**-t tesz a `+0x68`-ba. Az itt kiolvasott
ág viszont azt mutatja, hogy **jelen lévő, de érték nélküli** `scale`
attribútum esetén az `atof("")` = **0,0** ezt felülírja. A két eset tehát
különbözik:

| a `.cxf`-ben | a staging `+0x68` értéke |
|---|---|
| `scale` attribútum **nincs** | **1,0** (`0x00832fbd fld1`) |
| `scale=""` (jelen, üres) | **0,0** (`atof("")`) |
| `scale="…"` | a szám, **változatlanul** |

### 51.5 ⛳ A (b) ág LEZÁRVA — és egy ÖNHELYESBÍTÉS az 50.4-hez

A 17.14 két magyarázatot hagyott: **(a)** a `scale` a fájlból öröklődik,
**(b)** van egy nem látott író. A (b) ág **minden** alakja megjárva:

| alak | hol zárult le | eredmény |
|---|---|---|
| tömb-alakú (`bázis+index+0x2c`), `mov` és `fstp` | 17.15/1. pásztázás | negatív (8 találat, egyik sem csomópont) |
| mutatós `mov [reg+0x2c], <float>` | 17.15/2. pásztázás | negatív (9 találat) |
| **mutatós `lea r,[r+0x2c]`** | **51.2 (ez a kör)** | **negatív (11 hely)** |
| sávon kívüli csomópont-alakú írók | 17.10 + **51.3** | negatív, most tartalmi alapon |
| `313,0` beégetett literál (egész és float) | 17.15/3. | negatív |
| a `"scale"` sztring hivatkozói | 17.15/4. | csak a beolvasó és a kiíró |

⇒ **A (b) ág teljes egészében lezárva, negatívval.**

⛔ **ÖNHELYESBÍTÉS.** Az 50.4 abból, hogy a `+0x138` dokumentum *egészben*
csak üres/`1,0`-s/önmagából kaphat értéket, azt vezette le, hogy a
nem-`1,0` érték **„helyben, egy élő csomópont módosításával"** kerül be.
Ez az olvasat **megdőlt**: helyben módosító sem létezik — a mostani kör
zárta le az utolsó ilyen utat. A helyes következtetés ezzel:

> a `scale` **egyetlen** nem-`1,0` forrása a **beolvasó**, azaz **maga a
> fájl** ⇒ a 17.14 **(a)** ága az egyetlen, amit a bináris nem cáfol.

*(Az 50.4 többi állítása — a `+0x138` táplálási listája és a
konstrukció kizárása — áll; csak a belőle levont „helyben" olvasat esik.)*

### 51.6 ⛳ A GÉPI ÚT KIMERÜLT — a jegy állapota

A K1 gépi eszközökkel **nem vihető tovább**: minden író-alak,
minden hatókör és a beolvasó átalakítás-mentessége is mérve van. Ami az
(a) ág igazolásához kell, az **egy mérés a tulajdonos gépén** — egy
**frissen létrehozott** kollázs `.cxf`-je: ha ott `scale="1.000000"` áll,
az (a) igazolt, és a `313` kérdése átfordul arra, hogy melyik **korábbi**
program írta a mintáink értékeit.

⚠️ Ez a kérés **már ott áll a #1412 törzsében** („📋 Neked szóló kérés”),
tehát **nem kérjük újra** — a jegy állapota változik: `bináris-kutatható`
**le**, `felhasználóra-vár` **fel**.

*Állapot: **BLOKKOLT** (a tulajdonos gépe kell). Ez a K1 harmadik
megengedett végállapota — nem „csak nyitva".*
