# A `Nézet ▸ Megjelenítési mód` almenü — a tizenegy mód megfejtve

*A #1409 feltárása (2026-08-27). A jegy hat tételt nevezett meg; a
menüépítőből kiderült, hogy ezek **egyetlen, tizenegy tagú kizáró
rádiócsoport** részei, ezért a lap mind a tizenegyet leírja.*

> **Bizonyítottsági fok: MÉRVE** minden olyan állításra, amely mellett
> `0x…` cím áll — a `Picasa3.exe` (SHA-256 `644b7be…`) diszasszemblálásából,
> a `referencia/eszkozok/binaris/annot_disasm.py`-vel. Ahol
> **KÖVETKEZTETÉS** vagy **NYITOTT** áll, ott a szöveg kimondja, mi hiányzik
> és mi döntené el.

---

## 0. A verdikt egy táblában

A jegy négy kérdése tételenként. **A `fok` oszlop mondja meg, melyik
állítás MÉRT és melyik KÖVETKEZTETÉS** — a részletek a hivatkozott
szakaszban.

**A négy kérdés közül háromra minden tételnél UGYANAZ a válasz**, mert a
tizenegy mód egyetlen közös mechanizmuson ül; ezért ezek előre:

| kérdés | válasz | bizonyíték |
|---|---|---|
| rádió vagy kapcsoló? | **mind a tizenegy egyetlen kizáró rádiócsoport tagja; kapcsoló egy sincs** | MÉRVE · `0x00575670` (2. szakasz) |
| hol tárolódik? | **sehol** — se registry, se fájl; minden indításkor alaphelyzet | MÉRVE · a beállító `0x00575670` semmit nem ír (6. szakasz) |
| mi az alapértelmezés? | **`Automatikus`** (`ID_VIEW_AUTO`); távoli asztali munkamenetben a program rákérdez, és igenre `Távoli asztal` | MÉRVE · `0x0040bd90` (6. szakasz) |
| a kimenetre hat? | **nem — csak a képernyőre** | KÖVETKEZTETÉS (erős) · a hívás helye az ablak-újrarajzolás, `0x009e285d` (4. szakasz) |

### A jegyben megnevezett hat tétel

| tétel | mire hat (a képsor minden képpontjára) | bizonyíték | fok |
|---|---|---|---|
| **24 bites** `ID_VIEW_NORMAL` | **semmire** — nincs átalakító (`NULL` mutató) | `0x005cbc4f` · 5.1 | MÉRVE |
| **16 bites (szemcsézett)** `ID_VIEW_16` | véletlen zaj hozzáadása telítéssel: **B += 0…7, G += 0…3, R += 0…7**, alfa változatlan; a zaj MT19937-alakú generátorból, maszk `0x00070307` | `0x009e8b90` · 5.3 | MÉRVE (az „ez RGB565-höz illesztett szemcsézés” értelmezés: KÖVETKEZTETÉS) |
| **LCD fehérpont** `ID_VIEW_LCD` | mindhárom csatorna **×246/256** (≈ −3,9 % fényerő), **színeltolás nélkül** | `0x009e8a70` · 5.4 | MÉRVE |
| **Lineáris gamma (2.2)** `ID_VIEW_LINEAR` | csatornánként egy **beégetett 256 bájtos LUT** (a teljes tábla az 5.9-ben). **NEM `x^(1/2.2)`** — a legjobb illeszkedés ≈ gamma 1,44 | `0x009e8b60` → `0x00aa3f80`, tábla `0x00d32bd0` · 5.9 | MÉRVE (a tábla bájtra; a „miért 1,44” NYITOTT) |
| **Túlcsordult képpontok** `ID_VIEW_OV` | **kizárólag** a tökéletesen fehér képpontot (B=G=R=255) írja át **`#FF7F7F`**-re. Nincs tűrés, nincs csatornánkénti jelölés, a **fekete oldali levágás nincs jelölve** | `0x009e8810` · 5.6 | MÉRVE |
| **Projektor mód** `ID_VIEW_PROJECTOR` | mindhárom csatorna **×220/256** (≈ −14,1 % fényerő). **Nem** teljes képernyő, **nem** energiagazdálkodás, **nem** nagyítás | `0x009e8a10` · 5.5 | MÉRVE |

### A csoport további öt tagja (a jegy nem nevezte meg őket)

| tétel | mire hat | bizonyíték | fok |
|---|---|---|---|
| **Automatikus** `ID_VIEW_AUTO` | ha a képernyő **16 bites**, a 16 bites szemcsézést futtatja; egyébként **nem csinál semmit** | `0x009e8b80`, mélység `0x00d33958` ← `GetDeviceCaps(BITSPIXEL)` `0x0097e030` · 5.2 | MÉRVE |
| **Fekete-fehér** `ID_VIEW_BW` | `Y = (77·R + 151·G + 28·B) >> 8`, mindhárom csatornára | `0x009e89a0` · 5.7 | MÉRVE |
| **Szépia** `ID_VIEW_SEPIA` | luma → világosítás (`255 − (255−Y)·218/256`) → overlay a **`#9B7D63`** színnel | `0x009e8850` · 5.8 | a konstansok és a műveletsor MÉRVE; „ez overlay” KÖVETKEZTETÉS |
| **Távoli asztal** `ID_VIEW_RDESK` | `B+G+R < 96` → fekete, `> 672` → fehér, egyébként csatornánként `& 0xE0` (**3-3-3 bit**) | `0x009e8ad0` · 5.11 | MÉRVE |
| **Mac gamma (1.6)** `ID_VIEW_MAC` | **futásidő-függő** — a `0.0f` kulcs egy MEGOSZTOTT, lustán feltöltődő táblát választ | `0x009e8b40` → `0x00aa3f80`, tábla `0x00d32cd0` · 5.10 | **NYITOTT** (8. szakasz, `NY-3`) |

⚠️ **Amit a jegy feltevéséből el kell dobni:** a jegy 1. kérdése azt
feltételezte, hogy a `24 bites` / `16 bites` / `LCD` / `Lineáris gamma`
négyes egy rádiócsoport, a `Túlcsordult képpontok` és a `Projektor mód`
pedig két független kapcsoló. **Ez MEGDŐLT** — mind a tizenegy egyetlen
csoport, tehát a túlcsordulás-jelölés és a projektor mód **nem
kombinálható** a gammákkal, és a bekapcsolásuk **kikapcsolja** az addigi
módot.

---

## 1. A menü szerkezete — 11 tétel, 4 elválasztó

**MÉRVE** (`0x0055ab62`–`0x0055abd4`): a `Nézet` menü `&Display Mode`
tétele almenüt nyit; az almenü-tömb a `0x00d6dc98` címen kezdődik és
**15 rekordja** van (`mov dword ptr [0xd6e12c], 0xf`). A rekordok 20
bájtosak; a négy csupa-nulla rekord az elválasztó.

**MÉRVE** (`0x00559c9e`–`0x0055a03e`) — a tényleges sorrend:

```
Automatikus                       (ID_VIEW_AUTO)
──────────────────────────────
24 bites                          (ID_VIEW_NORMAL)
16 bites (szemcsézett)            (ID_VIEW_16)
──────────────────────────────
Távoli asztal                     (ID_VIEW_RDESK)
LCD fehérpont                     (ID_VIEW_LCD)
Projektor mód                     (ID_VIEW_PROJECTOR)
──────────────────────────────
Túlcsordult képpontok megjelenítése (ID_VIEW_OV)
Mac gamma (1.6)                   (ID_VIEW_MAC)
Lineáris gamma (2.2)              (ID_VIEW_LINEAR)
──────────────────────────────
Szépia                            (ID_VIEW_SEPIA)
Fekete-fehér                      (ID_VIEW_BW)
```

### A feliratok és a magyar gyorsítóbetűk (MÉRVE, a szövegtárból)

A `stringres` és a `menu-mnemonikok.tsv` alapján — a `&` a gyorsítóbetűt
jelöli. **A `stringres` a tizenegy tételhez buboréksúgót NEM ad** (a
szövegtárnak nincs is súgó-oszlopa; külön bejegyzést sem találtam).

| parancs | angol | magyar | hu betű |
|---|---|---|---|
| `ID_VIEW_AUTO` | `&Automatic` | `&Automatikus` | A |
| `ID_VIEW_NORMAL` | `&24-bit` | `&24 bites` | 2 |
| `ID_VIEW_16` | `&16-bit (dithered)` | `&16 bites (szemcsézett)` | 1 |
| `ID_VIEW_RDESK` | `&Remote Desktop` | `&Távoli asztal` | T |
| `ID_VIEW_LCD` | `&LCD Whitepoint` | `&LCD fehérpont` | L |
| `ID_VIEW_PROJECTOR` | `&Projector Mode` | `&Projektor mód` | P |
| `ID_VIEW_OV` | `&Show overflow pixels` | `Túlcsordult &képpontok megjelenítése` | k |
| `ID_VIEW_MAC` | `&Mac Gamma (1.6)` | `&Mac gamma (1.6)` | M |
| `ID_VIEW_LINEAR` | `Linear &Gamma (2.2)` | `Lineáris &gamma (2.2)` | g |
| `ID_VIEW_SEPIA` | `&Sepia` | `&Szépia` | S |
| `ID_VIEW_BW` | `&Black and White` | `&Fekete-fehér` | F |

*(A magyar feliratok a hivatalos Picasa-honosításból valók — nem a mi
fordításunk. A gyorsbillentyű-mező (`+0x04`) mindegyik módnál nulla:
gyorsbillentyűjük nincs.)*

### A menürekord alakja (MÉRVE)

| eltolás | tartalom |
|---|---|
| `+0x00` | a lefordított felirat mutatója |
| `+0x04` | gyorsbillentyű-szöveg |
| `+0x08` (word) | ikon |
| `+0x0a` (word) | **parancsazonosító** |
| `+0x0c` | almenü-tömb mutatója |
| `+0x10` | almenü darabszáma |

⚠️ **A fordító a rekord `+0x04`…`+0x10` mezőit a KÖVETKEZŐ rekord
feliratának betöltése UTÁN írja ki.** Aki a `push "…kulcs"` és a rá
következő `mov word ptr […+0x0a], 0x…` párost olvassa össze, **egy
rekorddal elcsúszik**. A helyes társítás horgonya a `mov dword ptr
[<cím>], eax` — az azonosítja a rekord kezdőcímét, és a `+0x0a` ahhoz
tartozik.

---

## 2. A vezérlőmodell: EGY rádiócsoport, tizenegy taggal

**MÉRVE** (`0x00575670`, 292 bájt). A tizenegy parancs **mindegyike**
ugyanabba a függvénybe fut, amely:

1. eltárolja a mód **képpont-átalakító függvényének mutatóját** a
   megjelenítő objektum `+0x254` mezőjébe (`0x00575695`),
2. újrarajzoltatja az ablakot (`call 0xa54b70`, `0x005756d5`),
3. végigmegy a tizenegy parancsazonosító **null-lezárt tömbjén**
   (`0x005756e0`–`0x00575738`), és mindegyikre `CheckMenuItem`-et hív
   (`0x00575777`) — a pipa (`MF_CHECKED = 8`) **pontosan arra az egyre**
   kerül, amelyik az imént választott parancs (`0x00575767`: `cmp` →
   `setne` → `sub 1` → `and 8`).

⇒ **Nincs köztük kapcsoló. Mind a tizenegy egy rádiócsoport tagja**, a
„Túlcsordult képpontok" és a „Projektor mód" is. A jegy feltevése
(négy rádió + két független kapcsoló) **MEGDŐLT**.

**A már aktív tételre kattintva** (MÉRVE, `0x00575689`): a függvény
összehasonlítja a régi és az új mutatót, és csak eltérés esetén állítja a
„piszkos" jelzőt — de a tárolást és a pipázó ciklust **mindig lefuttatja**.
Az eredetiben tehát **a pipa nem tűnik el az aktív tételre kattintva**.

⚠️ Épp ez az, amit a mi ismert `checkable` + kötött `checked`
**rádió-csapdánk** elrontana: a valódi kattintás előbb imperatívan
átbillenti a `checked`-et, és a már aktív tételnél az állapot nem
változik, tehát a kötés magától soha nem értékelődik újra — a menü
újranyitásakor **egyik tételen sem** állna pipa. A QML-oldali
megvalósításnak ugyanazt kell adnia, mint az eredetinek: a jelzés után
**azonnal vissza kell kötni** a `checked`-et (a #1464/#1468 mintája, ld. a
`Thumbnail Caption` almenüt a `PicasaMenuBar.qml`-ben).

---

## 3. A parancsazonosítók — javított tábla

**MÉRVE**, két úton: (a) a menürekord `+0x0a` mezője, (b) a főablak
parancs-diszpécserének (`0x005cb990`) két ugrótáblája
(`0x005cdb34`/`0x005cd9fc` és `0x005cde04`/`0x005cdc30`).

| parancs | azonosító | az ágra ugorva beállított átalakító |
|---|---|---|
| `ID_VIEW_16` | `0x9d18` | `0x009e8b90` |
| `ID_VIEW_PROJECTOR` | `0x9d19` | `0x009e8a10` |
| `ID_VIEW_MAC` | `0x9d1a` | `0x009e8b40` |
| `ID_VIEW_SEPIA` | `0x9d1b` | `0x009e8850` |
| `ID_VIEW_BW` | `0x9d1c` | `0x009e89a0` |
| `ID_VIEW_LINEAR` | `0x9d1d` | `0x009e8b60` |
| `ID_VIEW_NORMAL` | `0x9d1e` | **`NULL`** (`xor ecx,ecx`) |
| `ID_VIEW_AUTO` | `0x9d1f` | `0x009e8b80` |
| `ID_VIEW_LCD` | `0x9d20` | `0x009e8a70` |
| `ID_VIEW_OV` | `0x9d55` | `0x009e8810` |
| `ID_VIEW_RDESK` | `0x9dbc` | `0x009e8ad0` |

> 🔴 **A `picasa-menu-leltar.md` 7. szakaszának példatáblája HIBÁS volt** —
> pontosan a fenti elcsúszás miatt (`ID_VIEW_RDESK` = `0x9d18` stb.). A lap
> maga figyelmeztetett rá, hogy a gépi kinyerés megbukott, de a példatábla
> bent maradt. **Ebben a körben javítva.**
>
> **A javítás négy független szemantikai horgonyon nyugszik**, nem a
> szabályon: `0x9d55` átalakítója a tiszta fehér képpontokat színezi át
> (⇒ „túlcsordult képpontok"); `0x9d18`-é véletlen zajt kever
> (⇒ „16 bites szemcsézett"); `0x9d1e`-hez **nincs** átalakító
> (⇒ „24 bites" = változatlan); `0x9dbc`-t a **távoli asztal** észlelése
> állítja be (`0x0040be6e`, a `RemoteDesktopTest` üzenet mellett).

### A társítási szabály KONTROLL-MÉRÉSE — 4/4 a független horgonyokon

A `picasa-menu-leltar.md` és a `picasa-menu-parancsok-viselkedes.md` azért
mondta a leképezést „szabálytalannak", mert egy **másik** szabállyal
(„az azonosító az előző kulcsé") a `picasa-konyvtar-eszkoztar-viselkedes.md`
négy, más úton szerzett horgonyából csak 1-et talált el.

**Ugyanezt a négy horgonyt a helyes szabállyal újramértem** (a rekord
kezdőcímét a `mov dword ptr [<cím>], eax` adja, a `+0x0a` ahhoz tartozik):

| horgony (független forrásból) | a rekord kezdőcíme | `+0x0a` | egyezik? |
|---|---|---|---|
| `ID_VIEW_MYPICTURES` = `0x9db7` | `0x00d6de44` | `0x00d6de4e` = `0x9db7` (`0x0055a26d`) | ✅ |
| `ID_VIEW_FOLDERS` = `0x9db6` | `0x00d6de98` | `0x00d6dea2` = `0x9db6` (`0x0055a385`) | ✅ |
| `ID_VIEW_ALL` = `0x9db9` | `0x00d6deac` | `0x00d6deb6` = `0x9db9` (`0x0055a3cf`) | ✅ |
| `ID_VIEW_WATCHED` = `0x9db8` | `0x00d6df88` | `0x00d6df92` = `0x9db8` (`0x0055a671`) | ✅ |

⇒ **4/4.** A leképezés tehát **nem szabálytalan** — az előző két kör
**rossz horgonyt** használt. A négy külső horgony és a 3. szakasz négy
szemantikai ellenőrzése együtt **nyolc független megerősítés**.

*(Ez nem jogosít fel arra, hogy az egész menüsor azonosítóit kinyertnek
tekintsük: a szabály ellenőrzött, de a teljes kinyerést nem futtattam le.
Erre külön jegy való.)*

**Ugyanaz a fordítási kulcs két külön parancson.** A `ID_VIEW_BW` és
`ID_VIEW_SEPIA` kulcs a **Kép menüben is** szerepel, ott viszont más
azonosítóval és más viselkedéssel (`0x9d4c` és `0x9d4a` → `0x005cca71`
és `0x005cca47`: a szerkesztő 3. fülére vált, vagy kötegelten írja a
`filters` ini-kulcsot). A `picasa-menu-parancsok-viselkedes.md` 23.
szakasza ezt a **Kép menüs** előfordulást írja le helyesen; a
Megjelenítési mód almenü azonos nevű tételei **valódi megjelenítési
módok**, nem effektusok.

---

## 4. Hol hat: a képernyő-rajzolás, képsoronként

**MÉRVE.** A `+0x254` mező egy **általános, képsoronkénti utófeldolgozó
horog** a rajzfelület-osztályon (más felületek is állítanak bele, pl.
`0x009e8750`). A meghívás helye a rajzoló rutin:

```
0x009e285d  mov  eax, dword ptr [edx + 0x254]
0x009e2864  call eax                    ; (képsor-mutató, képpontszám)
```

a `0x009e1c40` képsor-ciklusában, amelynek **egyetlen** hívója
(`0x009e2a60`) az ablak-újrarajzolás láncán ül (`0x00a54b70` /
`0x009e16d0`).

Az átalakító **helyben módosítja a célbitmap képsorát**; az alfa-bájtot
minden mód érintetlenül hagyja (az egy `ID_VIEW_RDESK` kivételével, ld.
lent).

**KÖVETKEZTETÉS (erős): a mód csak a képernyőre hat, az exportra és a
nyomtatásra nem.** Amit ez alátámaszt: a mutatót kizárólag a
Nézet-menü kezelője (`0x005cb990`), az indulási távoli-asztal-próba
(`0x0040bd90`) és a felület-csatoló (`0x00a51e90`) írja — mind UI-út —,
és a hívási helye az ablak újrarajzolása. **Amit NEM mértem:** hogy az
export/nyomtatás sosem ugyanazt a felület-objektumot használja.
**Ez döntené el:** a windowsos Picasában `Projektor mód`-ban exportálni
egy képet, és összevetni a `24 bites` módban exportálttal — ha bitre
azonos, a kérdés lezárult.

---

## 5. A tizenegy mód algoritmusa

A képpont a memóriában **B, G, R, A** bájtsorrendű (32 bites dword,
`0xAARRGGBB`).

### 5.1 `ID_VIEW_NORMAL` — 24 bites

**MÉRVE** (`0x005cbc4f`): az átalakító mutatója **`NULL`** ⇒ **nincs
utófeldolgozás**. Ez az „eredeti kép" mód.

### 5.2 `ID_VIEW_AUTO` — Automatikus

**MÉRVE** (`0x009e8b80`, 15 bájt):

```asm
cmp dword ptr [0xd33958], 0x10   ; a képernyő színmélysége bitben
jne  vissza
jmp  0x009e8b90                  ; = a 16 bites szemcsézés
```

A `0x00d33958` globális a képernyő színmélysége: `GetDeviceCaps(GetDC(0),
BITSPIXEL)` (**MÉRVE**, `0x0097e030`); a bináris kezdőértéke `32`.

⇒ **Automatikus = „16 bites képernyőn szemcsézz, egyébként ne csinálj
semmit".** Ez a mód alapértelmezése (ld. 6.).

### 5.3 `ID_VIEW_16` — 16 bites (szemcsézett)

**MÉRVE** (`0x009e8b90`, 147 bájt). Képpontonként:

1. Egy **MT19937-alakú** álvéletlen-generátorból kér egy 32 bites értéket
   (állapottömb `0x00d6c4b4`, index `0x00d6c4ac`, újratöltés 624-nél —
   `cmp …, 0x270`). A temperálás lépései a szokásosak
   (`y ^= y>>11`, `y ^= (y & 0xFF3A58AD) << 7`, `y ^= (y & 0xFFFFDF8C) << 15`,
   `y ^= y>>18`), de a **két maszk nem az MT19937 szabványos
   `0x9D2C5680`/`0xEFC60000` értéke** — Picasa-saját változat.
2. `zaj = tempered & 0x00070307`
3. `pixel = paddusb(pixel, zaj)` — bájtonkénti, **telítő** összeadás
   (MMX, `0x009e8c0f`).

A maszk bájtonként: **B += 0…7 · G += 0…3 · R += 0…7 · A += 0**.

**KÖVETKEZTETÉS (nyilvánvaló):** ez pontosan az **RGB565** rácsához
illesztett, egyenletes eloszlású véletlen szemcsézés — a 16 bites
képernyőn az R és a B lépésköze 8, a G-é 4, és a hozzáadott zaj épp egy
lépésköznyi. Nem rendezett (Bayer) és nem hibaterjesztéses (Floyd–
Steinberg) szemcsézés.

*(Melléklelet, MÉRVE: ugyanezt a rutint egy önálló út is hívja,
`0x009db4b0`, szintén csak `[0xd33958] == 16` esetén — a szemcsézés tehát
16 bites képernyőn a menütől függetlenül is fut valahol a láncban.)*

### 5.4 `ID_VIEW_LCD` — LCD fehérpont

**MÉRVE** (`0x009e8a70`, 87 bájt): **mindhárom csatorna** ×`0xF6`, majd
`>> 8`.

```
B' = (B · 246) >> 8      G' = (G · 246) >> 8      R' = (R · 246) >> 8      A' = A
```

Egyenletes **≈ 3,9 %-os sötétítés**, színeltolás **nélkül** (a három
szorzó azonos).

⚠️ A felirat („fehérpont") **színhőmérséklet-korrekciót sugallna** — a kód
nem azt csinálja. A `.tre`/`stringres` sem ad hozzá buboréksúgót, tehát a
felirat mögött nincs több információ; a **kód az igazságforrás**.

### 5.5 `ID_VIEW_PROJECTOR` — Projektor mód

**MÉRVE** (`0x009e8a10`, 87 bájt): ugyanaz a rutin, szorzó `0xDC`:

```
B' = (B · 220) >> 8      G' = (G · 220) >> 8      R' = (R · 220) >> 8      A' = A
```

Egyenletes **≈ 14,1 %-os sötétítés**. **Nem** teljes képernyő, **nem**
energiagazdálkodás, **nem** nagyítás: kizárólag képpont-szintű
fényerő-csökkentés a képen. *(A jegy 5. kérdése ezzel megválaszolva.)*

### 5.6 `ID_VIEW_OV` — Túlcsordult képpontok megjelenítése

**MÉRVE** (`0x009e8810`, 49 bájt):

```asm
mov esi, [pixel]
and esi, 0xffffff
cmp esi, 0xffffff          ; B == G == R == 255 ?
jne tovabb
mov dword ptr [pixel], 0xffff7f7f
```

- **Küszöb:** kizárólag a **tökéletesen fehér** képpont (mindhárom
  csatorna pontosan 255). Nincs tűrés, nincs csatornánkénti jelölés, és a
  **fekete oldali** levágás **nincs** jelölve.
- **Jelölőszín:** a beírt dword `0xFFFF7F7F` ⇒ bájtonként `B=0x7F`,
  `G=0x7F`, `R=0xFF`, `A=0xFF` ⇒ **RGB(255, 127, 127) = `#FF7F7F`**,
  világos lazacpiros.

*(A jegy 4. kérdése ezzel megválaszolva. Figyelem: ez nem
„túlcsordulás-figyelmeztetés" a szó szokásos, csatornánkénti értelmében —
csak a kifehéredett foltokat festi át.)*

### 5.7 `ID_VIEW_BW` — Fekete-fehér (megjelenítési mód)

**MÉRVE** (`0x009e89a0`, 90 bájt):

```
Y = (77·R + 151·G + 28·B) >> 8          (77+151+28 = 256)
B' = G' = R' = Y                          A' = A
```

Egész, 8 bites BT.601-közeli luma. *(A szorzók: `0x4D`, `0x97`, és a
`lea edx,[edi + ebx*4]` + `lea ebx,[edx*8]; sub ebx,edx` páros adja a
28-at.)*

### 5.8 `ID_VIEW_SEPIA` — Szépia (megjelenítési mód)

**MÉRVE** — a konstansok és a műveletsor (`0x009e8850`, 336 bájt):

1. `Y` az 5.7 képletével, mindhárom csatornára szétterítve.
2. `xor 0xFFFFFF` → `×0xDA` (218) csatornánként, `>>8` → `xor 0xFFFFFF`
   ⇒ **`v1 = 255 − ((255 − Y) · 218) >> 8`** (világosítás, a feketék
   37-re emelkednek).
3. `maszk = ((v1 >> 7) & 0x010101) · 0xFF` — csatornánként `0xFF`, ha az
   érték ≥ 128.
4. `v2 = (v1 xor maszk) · 2`, majd szorzás a **`0x9B7D63 xor maszk`**
   színnel csatornánként `>>8`, végül `xor maszk`.

**KÖVETKEZTETÉS (a kompozícióra):** a 3–4. lépés a klasszikus
**overlay** (átfedés) keverés kifejtése; a keverőszín tehát
**`#9B7D63` = RGB(155, 125, 99)** — barna szépia. A **konstansok mértek**,
a „ez overlay" **az én olvasatom**; ha valaki pixelhű megvalósítást ír,
a fenti lépéssort kövesse, ne a nevet.

### 5.9 `ID_VIEW_LINEAR` — Lineáris gamma (2.2)

**MÉRVE** (`0x009e8b60` → `0x00aa3f80`): a mód a `2.2f` konstanssal
(`0x00cf4140`) hívja a közös gamma-alkalmazót, amely csatornánként egy
**256 bájtos keresőtáblát** alkalmaz B-re, G-re és R-re (az alfa marad).

A `2.2` ág táblája a `0x00d32bd0` címen **előre kitöltve** érkezik a
binárisban (az első bájtja `0` ⇒ a lusta feltöltés `cmp byte ptr [edi],
0xFF` őre nem lép működésbe). A **mért** tábla:

```
    0:   0   5   9  11  14  16  19  21  23  25  27  29  30  32  34  36
   16:  37  39  40  42  44  45  47  48  49  51  52  54  55  56  58  59
   32:  60  62  63  64  66  67  68  69  71  72  73  74  75  77  78  79
   48:  80  81  82  84  85  86  87  88  89  90  91  92  94  95  96  97
   64:  98  99 100 101 102 103 104 105 106 107 108 109 110 111 112 113
   80: 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129
   96: 129 130 131 132 133 134 135 136 137 138 139 140 140 141 142 143
  112: 144 145 146 147 148 149 149 150 151 152 153 154 155 155 156 157
  128: 158 159 160 161 161 162 163 164 165 166 166 167 168 169 170 171
  144: 171 172 173 174 175 176 176 177 178 179 180 180 181 182 183 184
  160: 184 185 186 187 188 188 189 190 191 192 192 193 194 195 195 196
  176: 197 198 199 199 200 201 202 202 203 204 205 205 206 207 208 208
  192: 209 210 211 211 212 213 214 214 215 216 217 217 218 219 220 220
  208: 221 222 223 223 224 225 225 226 227 228 228 229 230 231 231 232
  224: 233 233 234 235 236 236 237 238 238 239 240 241 241 242 243 243
  240: 244 245 245 246 247 248 248 249 250 250 251 252 252 253 254 255
```

⚠️ **A tábla NEM `x^(1/2.2)`.** A legjobb hatványillesztés
`out = round((i/255)^p · 255)` mellett **p = 0,6944**, azaz **gamma ≈ 1,44**
(256 értékből 37 tér el, mindegyik ±1-gyel — kerekítési zaj). A `2.2`
float itt tehát **a tábla kiválasztó kulcsa**, nem a kitevő. Pixelhű
megvalósításhoz **a fenti táblát kell beépíteni**, nem képletet illeszteni.

*(Az általános kitöltő ág — ha egyszer mégis lefut — `LUT[i] =
round(pow(i/255, 1/gamma) · 255)`; MÉRVE `0x00aa3ff0`–`0x00aa404a`,
a `1/255` és `255` konstansokkal `0x00cf4138`, `0x00cf39d0`.)*

### 5.10 `ID_VIEW_MAC` — Mac gamma (1.6) ⚠️ gyanús

**MÉRVE** (`0x009e8b40`): a mód **`0.0f`**-fel (`fldz`) hívja ugyanazt a
gamma-alkalmazót. A `0.0` ág a **`0x00d32cd0`** táblát választja, amely a
binárisban **kitöltetlen** (`FF 00 00 …` — az `0xFF` épp a „még nincs
kitöltve" őrszem). Ha ez a tábla még nem épült fel, a rutin **`1/0.0` =
+∞ kitevővel** tölti ki, amiből minden bemenetre 0 adódik (kivéve a
255-öt) — **azaz szinte fekete képernyő**.

A `0x00d32cd0` táblát viszont **egy másik, általános gamma-alkalmazó is
használja** (`0x00aa40a0`, nyolc hívóval), méghozzá épp a `2.2`
paraméterre — ha az előbb fut le, a Mac gamma az ő
`pow(x, 1/2.2)`-táblájával fog dolgozni.

⇒ **NYITOTT.** A mód tényleges hatása **futásidő-függő**, statikusan nem
dönthető el; a `0x00aa40a0` hívói a gammát egy struktúramezőből
(`[eax+0x28]`) veszik, nem konstansból. **Ez döntené el:** a windowsos
Picasában a `Mac gamma (1.6)` bekapcsolása egy semleges szürke ékre, és
képernyőkép róla — közvetlenül indítás után, illetve néhány kép
megnyitása után is. *(A `Mac gamma` nem tagja a #1409 hat tételének, és
Linuxon amúgy sincs értelme — a mi teendőnk itt legfeljebb a kihagyás
indoklása.)*

### 5.11 `ID_VIEW_RDESK` — Távoli asztal

**MÉRVE** (`0x009e8ad0`, 104 bájt). Képpontonként `s = B + G + R`:

| feltétel | eredmény |
|---|---|
| `s < 0x60` (96) | a teljes dword **0** (fekete, **az alfa is nullázódik**) |
| `s > 0x2A0` (672) | a dword **`0x00FFFFFF`** (fehér, az alfa nullázódik) |
| egyébként | mindhárom csatorna `& 0xE0` — **3-3-3 bites** kvantálás |

Sávszélesség-takarékos poszterizálás RDP-munkamenetre. *(Linuxon
értelmezhető megfelelője nincs; nálunk kihagyandó.)*

---

## 6. Tárolás, alapértelmezés, indulási állapot

**MÉRVE — a mód NEM tárolódik el sehol.** A `0x00575670` (az egyetlen
beállító) semmilyen registry- vagy fájlírást nem végez, és a tizenegy
parancs ága a diszpécserben mást nem hív. **Minden indításkor
alaphelyzetbe áll.**

Az indulási állapotot a `0x0040bd90` adja (a főablak-építő
`0x0040bf70`-ből hívva, `0x0040c881`) — **MÉRVE**:

```
Preferences\RemoteDesktopCheck   (alapérték: 1)
  ├─ 0  → nem állít semmit  (a felület alap-mutatója marad)
  └─ ≠0 → GetSystemMetrics(SM_REMOTESESSION)
            ├─ nem távoli munkamenet → ID_VIEW_AUTO (0x9d1f)
            └─ távoli munkamenet → kérdés a felhasználónak
                 (`RemoteDesktopTestTitle` / `RemoteDesktopTest`)
                 ├─ igen → ID_VIEW_RDESK (0x9dbc)
                 └─ nem  → ID_VIEW_AUTO  (0x9d1f)
```

⇒ **Alapértelmezés: „Automatikus".** A registry-gyökér
`SOFTWARE\Google\Picasa\Picasa2\Preferences\`; **az egyetlen kapcsolódó
beállítás a `RemoteDesktopCheck`**, és az sem a módot tárolja, hanem azt,
hogy a program megkérdezze-e a távoli asztalt.

Melléklelet (**MÉRVE**, `0x00a51e90`): amikor egy megjelenítő felület
hozzákötődik a főablakhoz, és a képernyő színmélysége **nem** 32 bit, a
felület mutatója szintén `ID_VIEW_AUTO`-ra áll — vagyis „Automatikus" a
tényleges alapállapot minden nem 32 bites képernyőn is.

---

## 7. „eredeti / nálunk / teendő"

| tétel | eredeti (mérve) | nálunk ma | teendő |
|---|---|---|---|
| **Megjelenítési mód** almenü | 11 tétel + 4 elválasztó, egy rádiócsoport | a `Nézet ▸ Display Mode` almenü **létezik, de üres és `enabled: false`** (`PicasaMenuBar.qml:471`) | almenü feltöltése, kizáró csoportként |
| `24 bites` | nincs átalakítás | nincs | **rádió alapértelmezettje**, no-op |
| `16 bites (szemcsézett)` | MT-zaj +0…7/0…3/0…7, telítő | nincs | megvalósítható, de **16 bites képernyő ma nincs** → alacsony érték |
| `LCD fehérpont` | ×246/256 mindhárom csatornán | nincs | egyszerű, megvalósítandó |
| `Lineáris gamma (2.2)` | fix 256 bájtos LUT (5.9) | nincs | a LUT bemásolható, pixelhű |
| `Túlcsordult képpontok` | tiszta fehér → `#FF7F7F` | nincs | egyszerű, **felhasználónak hasznos** (levágás-jelzés) |
| `Projektor mód` | ×220/256 mindhárom csatornán | nincs | egyszerű, megvalósítandó |
| `Automatikus` | 16 bites képernyőn szemcsézés, egyébként no-op | nincs | Linuxon gyakorlatilag no-op → felvehető, de üres |
| `Fekete-fehér` (nézet) | luma 77/151/28 | a **szerkesztő** B&W effektje megvan; **megjelenítési módként nincs** | megfontolandó |
| `Szépia` (nézet) | luma → világosítás → overlay `#9B7D63` | a **szerkesztő** szépia effektje megvan; **megjelenítési módként nincs** | megfontolandó |
| `Távoli asztal` | 3-3-3 bit + fekete/fehér levágás | nincs | **hatókörön kívül** (RDP-specifikus) |
| `Mac gamma (1.6)` | futásidő-függő, ld. 5.10 | nincs | **hatókörön kívül**, amíg nincs referencia-mérés |
| tárolás | **nincs**, minden indításkor „Automatikus" | – | nálunk se tárolja |
| hatókör | képernyő; export/nyomtatás **nem** (követk.) | – | a megvalósítás **csak a nézetre** tegye |

---

## 8. Nyitott kérdések — és mi döntené el

Ezekre **nincs bizonyítékom**, ezért nem döntök. Mindegyiknél ott van a
javasolt referencia-mérés a windowsos Picasából (a családi NAS közös
mappáján át, ld. `tesztkepek-nas-mappan-at`).

| # | a kérdés | miért nem dőlt el statikusan | mi döntené el |
|---|---|---|---|
| **NY-1** | **Hat-e a mód az exportra / nyomtatásra?** | A hívási helye az ablak-újrarajzolás (`0x009e285d`), és a mutatót csak UI-utak írják — de nem jártam végig, hogy az export sosem ugyanazt a felület-objektumot kapja. | Ugyanazt a képet exportálni `Projektor mód`-ban és `24 bites`-ben, majd a két JPEG-et **bájtra összevetni**. Ha azonos: lezárva. Ugyanez nyomtatásnál PDF-be. |
| **NY-2** | **Miért ≈ gamma 1,44 a „Lineáris gamma (2.2)" táblája?** | A `2.2` float itt csak a tábla **kiválasztó kulcsa**; a tábla a binárisban előre kitöltve érkezik, a generátora nincs a kódban. | Nem kell eldönteni a megvalósításhoz: **a mért 256 bájtos tábla a szerződés** (5.9). Csak akkor számít, ha valaki képletet akar illeszteni — akkor egy szürkeék képernyőképe a windowsos Picasából ellenőrizné a táblát. |
| **NY-3** | **Mit csinál valójában a `Mac gamma (1.6)`?** | A `0.0f` kulcs egy **megosztott, lustán feltöltődő** táblát (`0x00d32cd0`) választ, amit egy másik gamma-alkalmazó (`0x00aa40a0`, 8 hívó) is használhat, futásidőben kapott gammával. Ha az fut előbb, a Mac gamma az ő tábláját kapja; ha nem, a saját feltöltése `1/0.0 = +∞` kitevővel megy. | Semleges **szürkeékre** kapcsolni a `Mac gamma (1.6)`-ot **közvetlenül indítás után**, majd **néhány kép megnyitása után is**, és képernyőkép mindkettőről. Ha a két kép eltér, a mód futásidő-függő ⇒ nálunk **nem reprodukálandó**. |
| **NY-4** | **Látszik-e a mód diavetítésben / teljes képernyőn?** | Nem néztem meg, hogy a `0x009e1c40` rajzolóút szolgálja-e azokat a nézeteket. | `Projektor mód` bekapcsolása, majd diavetítés indítása — látszik-e a sötétítés. *(Ez a mód gyakorlati értelme is: vetítéskor kellene hatnia.)* |
| **NY-5** | **Mit csinál a `Színkezelés használata` (`ID_VIEW_COLOR_MANAGED`)?** | Külön menütétel a Nézet menü törzsében (`0x0055aaff`), **nem** tagja a rádiócsoportnak; nem tártam fel. | Önálló kör; nálunk ma placeholder (`PicasaMenuBar.qml`). |
| **NY-6** | **A 16 bites szemcsézés pixelhű reprodukálhatósága.** | Az MT19937-változat vetőmagozását (`0x00aa2930`) nem néztem meg. | Csak akkor kell, ha valaki bitre egyező szemcsét akar — a **statisztika** (egyenletes 0…7 / 0…3 / 0…7) ehhez nem szükséges, az mérve van. |

⚠️ **Amit szándékosan NEM állítok:** hogy az „LCD fehérpont" fehérpontot
állítana. A kód mindhárom csatornát **azonos** szorzóval sötétíti, tehát
színhőmérséklet-korrekció nincs benne. A felirat ellentmond a kódnak; a
`.tre`/`stringres` nem ad hozzá buboréksúgót, ami eldöntené a szándékot.
**A kód az igazságforrás.**

## 9. Amit NEM vizsgáltam

*(Ami ide tartozna, de már a 8. szakasz nyitott kérdései közt szerepel a
javasolt méréssel: export/nyomtatás · diavetítés · `ID_VIEW_COLOR_MANAGED`
· a `0x00aa40a0` nyolc hívója · az MT-vetőmagozás.)*

1. **A megjelenítő objektum osztálya és életciklusa.** A `+0x254` horog
   egy általános rajzfelület-osztályon ül (más felületek is állítanak
   bele, pl. `0x009e8750`); nem derítettem ki, hány ilyen felület él
   egyszerre, és a mód csak a főnézetre vagy minden felületre hat-e.
2. **A `Picasa Photo Viewer`** (külön `.exe`, saját bináris-indexe van:
   `binary-index-photoviewer`) — van-e ott is megjelenítési mód.
3. **A menü ikonjai és gyorsbillentyűi** — a rekordok `+0x04`/`+0x08`
   mezője mindegyik módnál nulla, de ezt csak a Megjelenítési mód almenüre
   néztem meg.
4. **Buboréksúgó.** A `stringres` a tizenegy tételhez **nem** ad
   magyarázó szöveget; ezt kereséssel ellenőriztem, nem találtam.

## 10. Hivatkozások

- Menüépítő: `0x00559150` · almenü-tömb `0x00d6dc98` · almenü-hivatkozás `0x0055abca`
- Parancs-diszpécser: `0x005cb990` · ugrótáblák `0x005cdb34`/`0x005cd9fc`, `0x005cde04`/`0x005cdc30`
- Mód-beállító + pipázó: `0x00575670`
- Indulási állapot: `0x0040bd90` (hívó `0x0040bf70`, `0x0040c881`)
- Rajzolóút: `0x009e1c40` (hívó `0x009e2a60`)
- Átalakítók: `0x009e8810` · `0x009e8850` · `0x009e89a0` · `0x009e8a10` · `0x009e8a70` · `0x009e8ad0` · `0x009e8b40` · `0x009e8b60` · `0x009e8b80` · `0x009e8b90`
- Gamma-alkalmazók: `0x00aa3f80`, `0x00aa40a0` · táblák `0x00d32bd0`, `0x00d32cd0`
- Képernyő-színmélység: `0x00d33958` (feltöltő `0x0097e030`)
- Kapcsolódó lapok: [picasa-menu-leltar.md](picasa-menu-leltar.md) ·
  [picasa-menu-parancsok-viselkedes.md](picasa-menu-parancsok-viselkedes.md) ·
  [ui-audit-menus.md](ui-audit-menus.md)
