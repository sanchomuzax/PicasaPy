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
| **Lineáris gamma (2.2)** `ID_VIEW_LINEAR` | csatornánként egy LUT, amit a rutin **futásidőben tölt fel** `round(pow(c/255, 1/2,2) · 255)`-tel — tehát pontosan 2,2-es | `0x009e8b60` → `0x00aa3f80`, tábla `0x00d32cd0`, kitöltő `0x00aa3ff0` · 12.4 | MÉRVE |
| **Mac gamma (1.6)** `ID_VIEW_MAC` | csatornánként egy **beégetett 256 bájtos LUT** (a teljes tábla az 5.9-ben). **NEM `x^(1/1,6)`** — a legjobb illeszkedés ≈ gamma 1,44 | `0x009e8b40` → `0x00aa3f80`, tábla `0x00d32bd0` · 5.9 · 12.4 | MÉRVE (a tábla bájtra; a „miért 1,44” NYITOTT) |
| **Túlcsordult képpontok** `ID_VIEW_OV` | **kizárólag** a tökéletesen fehér képpontot (B=G=R=255) írja át **`#FF7F7F`**-re. Nincs tűrés, nincs csatornánkénti jelölés, a **fekete oldali levágás nincs jelölve** | `0x009e8810` · 5.6 | MÉRVE |
| **Projektor mód** `ID_VIEW_PROJECTOR` | mindhárom csatorna **×220/256** (≈ −14,1 % fényerő). **Nem** teljes képernyő, **nem** energiagazdálkodás, **nem** nagyítás | `0x009e8a10` · 5.5 | MÉRVE |

### A csoport további öt tagja (a jegy nem nevezte meg őket)

| tétel | mire hat | bizonyíték | fok |
|---|---|---|---|
| **Automatikus** `ID_VIEW_AUTO` | ha a képernyő **16 bites**, a 16 bites szemcsézést futtatja; egyébként **nem csinál semmit** | `0x009e8b80`, mélység `0x00d33958` ← `GetDeviceCaps(BITSPIXEL)` `0x0097e030` · 5.2 | MÉRVE |
| **Fekete-fehér** `ID_VIEW_BW` | `Y = (77·R + 151·G + 28·B) >> 8`, mindhárom csatornára | `0x009e89a0` · 5.7 | MÉRVE |
| **Szépia** `ID_VIEW_SEPIA` | luma → világosítás (`255 − (255−Y)·218/256`) → overlay a **`#9B7D63`** színnel | `0x009e8850` · 5.8 | a konstansok és a műveletsor MÉRVE; „ez overlay” KÖVETKEZTETÉS |
| **Távoli asztal** `ID_VIEW_RDESK` | `B+G+R < 96` → fekete, `> 672` → fehér, egyébként csatornánként `& 0xE0` (**3-3-3 bit**) | `0x009e8ad0` · 5.11 | MÉRVE |
| ~~**Mac gamma (1.6)** `ID_VIEW_MAC` — „futásidő-függő”~~ | ⛔ **MEGDŐLT (#2816):** a `0.0f` kulcs az ELŐRE KITÖLTÖTT `0x00d32bd0` táblát választja (`0x00aa3fd2`), tehát a mód determinisztikus. A sor fent, a mért táblázatban áll. | `0x00aa3fd2` · 12.4 | LEZÁRVA |

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
| `+0x08` (word) | ~~ikon~~ → **gyorsítóbillentyű-módosítók bitmaszkja** (`Ctrl+`/`Shift+`/`Alt+`); helyesbítve 2026-09-09, #2821 — ld. [picasa-menu-leltar.md](picasa-menu-leltar.md) 8.5 |
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

> ⚠️ **A 11. szakasz (2026-09-09, #2813) két ponton HELYESBÍTI ezt a
> bekezdést:** a mező nem „rajzfelület"-osztályon, hanem a **`yt`
> jelenetgráf-csomópont** alaposztályán ül (RTTI-vel igazolva), és a
> `0x009e8750` **nem felület**, hanem maga egy képsor-átalakító.

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

### 5.3/b A szemcse VETŐMAGJA — determinisztikus (2026-09-10, #2865)

**Bizalmi fok: megerősített** a mechanizmusra és a determinizmusra;
**feltételes** a konkrét konstansra (5.3/b.5).

#### 5.3/b.1 ⛔ HELYESBÍTÉS: a `0x00aa2930` NEM a magozás

A 8. szakasz **NY-6** tétele így szólt: *„Az MT19937-változat vetőmagozását
(`0x00aa2930`) nem néztem meg."* A cím **rossz**: a `0x00aa2930` (157 bájt) a
**twist**, azaz az állapottömb újratöltése — `N = 624`, `M = 397`, a
`mag01` tábla a `0xc782c0`-n, kiolvasott értéke **`{0, 0x9908B0DF}`**, azaz a
**szabványos** MT19937-konstans. A végén `mov dword ptr [esi+4], 0` — az index
nullázása.

⇒ a magozás máshol van, és az alábbi szakasz megtalálta.

#### 5.3/b.2 Az inicializáló: `FUN_00aa28f0` — és egy MÁSODIK eltérés

```
0x00aa28f7  mov dword ptr [edx + 0xc], eax          ; állapot[0] = mag
0x00aa2900  mov ecx, dword ptr [edx + eax*4 + 8]    ; állapot[i-1]
0x00aa2906  shr esi, 0x1e                           ; >> 30
0x00aa290b  imul esi, esi, 0x19660d                 ; ⭐ szorzó
0x00aa2911  add esi, eax                            ; + i
0x00aa291a  cmp eax, 0x270                          ; i < 624
0x00aa2921  mov dword ptr [edx + 4], 0x270          ; index = 624 ⇒ első
                                                    ; használatkor twist
```

Ez az `init_genrand`, de a szorzó **`0x19660D`**, nem a szabványos
`0x6C078965`. ⇒ a Picasa MT-változata **két** ponton tér el a szabványtól: az
5.3-ban leírt két temperálási maszkban, és itt az inicializáló szorzójában.
A twist ellenben szabványos.

#### 5.3/b.3 ⭐ A magozás helye: egy CRT-STATIKUS INICIALIZÁLÓ

```
0x00c33f90  push esi ; push edi
0x00c33f92  call 0xc08221        ; _rand   → r1
0x00c33f99  shl  edi, 0xc        ; r1 << 12
0x00c33f9c  call 0xc08221        ; _rand   → r2
0x00c33fa3  xor  esi, edi
0x00c33fa5  shl  esi, 0xc
0x00c33fa8  call 0xc08221        ; _rand   → r3
0x00c33fad  xor  eax, esi
0x00c33faf  mov  edx, 0xd6c4a8   ; ⭐ a SZEMCSE generátorának objektuma
0x00c33fb4  call 0xaa28f0        ; init_genrand(mag)
```

⇒ **mag = r3 ^ ((r2 ^ (r1 << 12)) << 12)**, ahol `r1..r3` három egymást
követő CRT-`rand()`.

Az objektum kiosztása ezzel megvan: `+0x4` = index (`0x00d6c4ac`),
`+0xc` = állapot[0] (`0x00d6c4b4`) — pontosan az 5.3-ban mért két cím.

#### 5.3/b.4 ⭐ NINCS entrópiaforrás a láncban

- A `_rand` (`0x00c08221`) a szokásos MSVC-LCG: `mag = mag·0x343FD + 0x269EC3`,
  visszaadva `(mag >> 16) & 0x7FFF`; a mag a szálankénti adatban, `[ptd+0x14]`.
- Az `srand` (`0x00c08214`) **10 helyről** hívott — mind **alkalmazáskód**
  (`0x00423a6c`, `0x00565cc5`, `0x006804c4`, `0x0071d993`, `0x0071e23b`,
  `0x0085b76d`, `0x0087cb85`, `0x0088fed7`, `0x009180df`, `0x009902b8`),
  egyik sem a CRT-inicializáló tartományban.
- A magozó láncban **nincs** `GetTickCount`, `QueryPerformanceCounter` vagy
  `time` — csak a három `rand()`.

⇒ **a szemcse vetőmagja determinisztikus**, tehát a szemcsézés elvben
**bitre reprodukálható**, és golden-teszt írható rá.

#### 5.3/b.5 A konkrét konstans — és a feltétele

A CRT-inicializáló tartományban (`0x00c30000`–`0x00c40000`) **pontosan
kilenc** `rand()`-hívóhely van: **három** ilyen magozó blokk, egyenként
hárommal. A CRT-tábla bejegyzései és a magozott objektumok:

| tábla-bejegyzés | magozó | a generátor objektuma |
|---|---|---|
| `0xc416b0` | `0x00c32520` | `0x00d67f70` |
| **`0xc41870`** | **`0x00c33f90`** | **`0x00d6c4a8` — a SZEMCSE** |
| `0xc41884` | `0x00c34070` | `0x00d6ce80` |

A szemcséé tehát a **második**, azaz a 4–6. `rand()`-hívás. Az MSVC
alapértelmezett CRT-magjával (**1**) a sorozat első kilenc értéke
`41, 18467, 6334, 26500, 19169, 15724, 11478, 29358, 26962`, ebből:

**a szemcse-generátor vetőmagja = `0x80AE2D6C`** (2 158 898 540).

**Ellenőrzés:** ezzel a maggal, a **kiolvasott** inicializáló szorzóval, a
szabványos twisttel és az 5.3-beli **kiolvasott** temperálási maszkokkal
számolt első nyolc zajérték `B/G/R` bontásban
`(5,3,3) (4,2,0) (2,2,6) (4,0,7) (2,0,1) (5,3,0) (4,2,2) (7,1,0)` — mind a
mért `B 0…7 · G 0…3 · R 0…7` tartományban.

✅ **A feltétel BETELJESÜLT (2026-09-10, #2868).** A CRT-inicializáló tábla
(`0xc40af0`…`0xc418bc`, nullákkal határolva, **884** bejegyzés; a szemcséé
előtt **864** áll) teljes felsorolása:

- **közvetlenül** `rand`/`srand`-ot hívó bejegyzés: **pontosan 3** — a három
  ismert magozó (`0xc416b0`, `0xc41870`, `0xc41884`);
- **egy szinttel mélyebben**: a bejegyzésekből hívott **23** egyedi függvény
  közül **egy sem** ér el `rand`-ot vagy `srand`-ot;
- a bejegyzések **791**-e kizárólag `_atexit`-et hív (destruktor-regisztráció),
  79-nek egyetlen hívása sincs.

**Kontrollpozitív mindkét szinten:** a `0xc41870` bejegyzés közvetlenül
hívónak, a `0x00c33f90` pedig CÉLKÉNT vizsgálva is `rand`-ot látónak
mutatkozott.

⇒ a **`0x80AE2D6C`** ezzel **bizonyított** — a kimondott hatókör: közvetlen és
egy szint mély hívási gráf.

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

> ⛔ **ÖNHELYESBÍTÉS (2026-09-09, #2816): EZ A SZAKASZ ÉS AZ 5.10 FEL VOLT
> CSERÉLVE.** A `0.0`-ág a `0x00d32bd0` (előre kitöltött, ≈1,44) táblát
> választja, a `2.2`-ág a `0x00d32cd0`-et (őrszemes, futásidőben töltődik
> `pow(x, 1/2,2)`-vel). Az alábbi tábla tehát **a Mac gammáé**, nem a
> lineárisé. A levezetés és a bizonyíték: **12. szakasz.**

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

> ⛔ **ÖNHELYESBÍTÉS (2026-09-09, #2816): az alábbi „kitöltetlen tábla ⇒
> szinte fekete képernyő" levezetés HAMIS PREMISSZÁRA épül.** A `0.0`-ág
> **nem** a `0x00d32cd0`-et választja, hanem a `0x00d32bd0`-et, amely
> előre ki van töltve. A Mac gamma tehát **mindig** az ≈1,44 kitevőjű
> táblával dolgozik, és a hatása **nem futásidő-függő**. A levezetés:
> **12. szakasz.**

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

⚠️ **ELAVULT JELÖLÉS (2026-09-10, #2825):** a kérdést a tulajdonos
felvételeinek képpont-mérése **eldöntötte** (#1580 → **#1730**, 2026-08-30):
a `Mac gamma (1.6)` **világosít** — teljes képernyős luma +3,32%, a központi
fotó +15,7% —, és a mért görbe az **`x^(1/1,6)`** gammával konzisztens. Ezzel
az alábbi „szinte fekete képernyő" ág **MEGDŐLT**, és a kért képernyőkép is
megvan; ami hátramaradt, az a MEGVALÓSÍTÁS (a mód a teljes kompozícióra hat),
és annak élő gazdajegye a **#1730**. A bekezdés szövege történeti okból marad.

⚠️ **ELAVULT JELÖLÉS (#2825).**
⇒ ~~**NYITOTT.** A mód tényleges hatása **futásidő-függő**, statikusan nem
dönthető el;~~ a `0x00aa40a0` hívói a gammát egy struktúramezőből
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

## 5.12 `ID_VIEW_COLOR_MANAGED` — Színkezelés használata (LEZÁRVA 2026-08-30, #1582)

*NY-5 megválaszolva az olcsó lánccal (menürekord → parancsazonosító →
diszpécser-ugrótábla → kezelő tartalma → pipa-szinkron), dekompiláció
nélkül.*

**A kapcsoló életciklusa:**

| kérdés | válasz | bizonyíték |
|---|---|---|
| kapcsoló-e | **IGEN, önálló kapcsoló** — nem tagja a 11-es rádiócsoportnak (a #1409 kizárása helyes) | kezelő `0x005c95a0`, a diszpécser `0x005cb990` külön ága hívja (`0x005cc615`) |
| hol tárolódik | `Preferences\EnableColorManagement` (a `SOFTWARE\Google\Picasa\Picasa2\Preferences\` gyökéren) | a 0x005c95a0: `push "EnableColorManagement"+"Preferences"` → Get/SetPreference (`0x407a20`/`0x401900`) |
| alapértelmezés | **0 = ki** | a GetPreference default-ja `0` (`0x005c95bf`) |
| mit csinál a kezelő | beolvas → beállít → **pipa-szinkron** (`0x5c90f0`) → **a szerkesztő-előnézet újraépítése** | `[0xd67920]` (a színkezelés-objektum) `+0x5c` mezőjébe ír; `editpanel/previewclip2` (`0x005c966a`); a `[esi+0x327c/0x3280]` struktúrák nullázása; `[esi+0xdbd]=1` dirty-jelző (`0x005c9719`) |
| ICC-profil forrása | **a JPEG-be beágyazott metaadat-tagok**: `icc_camera_profile` és `icc_camera_to_tone_matrix` (3×3 float-mátrix), a `CaptProf_color_matrix` mellett | a `0x008bfb10` tag-feloldó `repe cmpsb` névhasonlításai (`0x008bfc09`, `0x008bfd12`); a mezők `[+0x360]/[+0x37c]` |

**A pipa-állapot-szinkron** (`0x5c90f0`, a CheckMenuItem import `0xc40810`):

| mező/kulcs | pipa az ID-n |
|---|---|
| `[ebp+0x3188]` (ShowHidden) | `0x9c9e` |
| `Preferences\Show only big images` | `0x9cd8` |
| `Preferences\EnableColorManagement` | **`0x9d72`** |
| `editpanel/preview`-feltétel | `0x9d2a` |
| a `searchcontainer/searchbutton`-feltétel | `0x9d2b` |
| `thumbui/fullview`-feltétel | `0x9c8f` |

**❗ Két váratlan melléklelet — óvatosan a menü-felirat ↔ ID párosítással:**

1. A `Use Color Management` menürekordhoz a menüépítőben levezetett
   `0x9c9e` funkcionálisan a **`Preferences\ShowHidden`** kapcsolót
   kapcsolja (`0x5c9300`), **nem** az EnableColorManagement-et. A kezelő
   literálja dönt: a 0x9c9e ága `ShowHidden` get/set-et hív (`0x005c9304`).
2. Az EnableColorManagement pipája a **`0x9d72`**-n ül (`0x5c90f0` 3.
   blokkjában, `0x005c9197`–`0x005c91cc`); a 0x9d72 a menüépítőben a
   `&Display Mode` rekordján tűnik fel — de a #1581 szerint a menüépítő
   felirata a KÖVETKEZŐ rekordba csúszhat, a felirat↔ID párosításnak ez a
   sávja megbízhatatlan.

**A két megbízható horgony** (a kezelő tartalma és a pipa-szinkron)
függetlenül ugyanazt a párt adja: `0x9c9e`↔ShowHidden és `0x9d72`↔
EnableColorManagement. Ami mégis képernyőképet igényelt: a látható
menü-feliratok és a pipák pontos párosítása.

#### ✅ A párosítás LEZÁRVA a tulajdonos képeivel (2026-08-30)

*Forrás: `searchcontainer.tre:19` (`searchcontainer/searchbutton`) · `thumbui.tre:375` (`thumbui/newalbum`).*

A tulajdonos két képernyőképet küldött (`1852-nezet-menu` mappa,
`/mnt/nas/My Pictures/1852-nezet-menu/`):

| tétel | alap kép | bekapcsolt kép |
|---|---|---|
| „Kis képek" | nincs pipa | **van pipa** |
| „Rejtett képek" | **van pipa** (mindkettőn) | van pipa |
| **„Színkezelés használata"** | **nincs pipa** | **van pipa** |
| „Megjelenítési mód ›" | nincs | nincs |

(Leolvasás: helyi codex agent, csak olvasás — a futó kutatási modell nem
támogatja a képbemenetet.)

⇒ **A pipa a „Színkezelés használata" SAJÁT során jelenik meg**, nem a
`ShowHidden`-soron túl. A `0x9d72` (EnableColorManagement) tehát tényleg a
„Színkezelés használata" felirathoz tartozik a képernyőn; a `0x9c9e` a
„Rejtett képek"-hez (ShowHidden). A #1581-es elcsúszás-tanulság itt **nem**
érinti a megvalósítást: a #1725-ben a „Színkezelés használata" tétel
checkable, és a pipa azon a soron jelenik meg.

*A párosítás bizonyítottsági foka ezzel **megerősített** a képernyőképpel.*

**A diszpécser teljes kezelő-térképe (módszertanilag értékes melléktermék):**

*1. switch (byte-tábla `0x5cdb34`, dword-tábla `0x5cd9fc`, lefedés 0x9c42–0x9d40):*

| ID | bit | kezelő | tartalom |
|---|---|---|---|
| `0x9c8f` | 68 | `0x5cbb50` | `searchcontainer/searchbutton` → `0x5c90f0` |
| `0x9c9e` | 9 | `0x5cbbad` | **`0x5c9300` = ShowHidden** |
| `0x9cd8` | 55 | `0x5cbbb9` | `0x5c94e0` = Show only big images |
| `0x9d1f` | 65 | `0x5cbc3e` | AUTO (átalakító-setter, lásd 6. szakasz) |
| `0x9d2a` | – | – | SMALLTHUMBNAILS (pipa-szinkron, 0x5c90f0) |
| `0x9d2b` | – | – | SMALL (pipa-szinkron) |
| `0x9d72` | – | – | **Display Mode felirat / EnableColorManagement pipa** |

*2. switch (byte-tábla `0x5cde04`, dword-tábla `0x5cdc30`, lefedés 0x9d44–0xa02c — a teljes menüsáv-diszpécser):*

| ID | bit |
|---|---|
| `0x9d5d` | `0x5cc5bb` `thumbui/newalbum` (Új album) |
| `0x9d5e` | `0x5cc5ca` `0x5e9940` |
| `0x9d5f` | `0x5cc609` `0x65ab50` |
| `0x9d60` | `0x5cc5d5` `0x5fecd0(0)` |
| `0x9d61` | `0x5cc5e2` `0x5fefc0(0)` |
| **`0x9d62`** | **`0x5cc615` → `0x5c95a0` = EnableColorManagement** |
| `0x9d63` | `0x5cccc3` |
| `0x9d64` | `0x5cc4f3` |
| `0x9d65` | `0x5cccfc` |
| `0x9d66` | `0x5cccf2` |
| `0x9d67` | `0x5cc88b` |

**Eredeti / nálunk / teendő:**

| | eredeti | nálunk ma | teendő |
|---|---|---|---|
| menütétel | „Színkezelés használata" kapcsoló, pipa | placeholder (`PicasaMenuBar.qml`) | kapcsoló a `Preferences\EnableColorManagement`-re (alap 0) |
| hatás | bekapcsoláskor a szerkesztő-előnézet újraépül; a beágyazott ICC / 3×3 mátrix hatályosul | nincs | az előnézet-újraépítés a `filters=`-lánchoz hasonló érvényesítés |
| tárolás | `Preferences\EnableColorManagement` | – | a beállítás-tárolónkba |

*Bizonyítottsági fok: **megerősített** minden állítás, ami mellett `0x…`
cím áll (a függvénytörzsek szó szerinti tartalma); a menü-felirat ↔
azonosító párosítás — **megerősített** (a tulajdonos képeivel, 2026-08-30).*
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

> 🟢 **FRISSÍTVE 2026-09-01 (#1579).** Ez a tábla korábban minden sorában
> `nincs`-et mondott — a #1575 / #1656 / #1658 / #1730 körök óta **nem volt
> igaz**. A hatókör-döntés (mit valósítunk meg és mit nem) mostantól ADR:
> [`../decisions/megjelenitesi-modok-hatokore.md`](../decisions/megjelenitesi-modok-hatokore.md).

| tétel | eredeti (mérve) | nálunk ma | teendő |
|---|---|---|---|
| **Megjelenítési mód** almenü | 11 tétel + 4 elválasztó, egy rádiócsoport | ✅ **él**, kizáró rádiócsoportként (`PicasaMenuBar.qml`) | – |
| `24 bites` | nincs átalakítás | ✅ no-op, a rádió alapértelmezettje | – |
| `16 bites (szemcsézett)` | MT-zaj +0…7/0…3/0…7, telítő | 🟡 **helyfoglaló** — a szabály mérve, de 16 bites képernyő ma nincs | ha értelmet nyer, bekötni |
| `LCD fehérpont` | ×246/256 mindhárom csatornán | ✅ megvalósítva | – |
| `Lineáris gamma (2.2)` | fix 256 bájtos LUT (5.9) | ✅ a LUT bemásolva, pixelhű | – |
| `Túlcsordult képpontok` | tiszta fehér → `#FF7F7F` | ✅ megvalósítva | – |
| `Projektor mód` | ×220/256 mindhárom csatornán | ✅ megvalósítva | – |
| `Automatikus` | 16 bites képernyőn szemcsézés, egyébként no-op | ✅ no-opként megvalósítva | – |
| `Fekete-fehér` (nézet) | luma 77/151/28 | ✅ **nézetmódként is** megvalósítva (a szerkesztő effektjétől függetlenül) | – |
| `Szépia` (nézet) | luma → világosítás → overlay `#9B7D63` | ✅ **nézetmódként is** megvalósítva | – |
| `Távoli asztal` | 3-3-3 bit + fekete/fehér levágás | ⛔ **hatókörön kívül** (RDP-specifikus) — nyugdíjazott menütétel | nincs |
| `Mac gamma (1.6)` | futásidő-függő, ld. 5.10 | ✅ megvalósítva a **mért** kitevővel (0,7743), nem az `1/1,6`-tal | – |
| tárolás | **nincs**, minden indításkor „Automatikus" | nálunk sem tárolódik | – |
| hatókör | képernyő; export/nyomtatás **nem** (NY-1: lezárva) | rács, idővonal, keresés, tálca (#1656) | a szerkesztő-előnézet és a teljes képernyő nyitott |

⚠️ **A `Mac gamma` kitevője nem `1/1,6`.** A #1580 mérése szerint a
központi fotó lumája 133,5 → 154,5; ebből `ln(154,5/255)/ln(133,5/255) =
0,7743` (gamma 1,292). Az `1/1,6 = 0,625` kitevő 170,2-t adna. A felirat
a Picasa saját elnevezése — **a mérés a szerződés**, nem a felirat.

---

## 8. Nyitott kérdések — és mi döntené el

*(NY-1, NY-3, NY-4 a #1580 képeivel/méréseivel 2026-08-30-án lezárultak;*
*NY-5 az 5.12-ben. A tábla az aktuális állapotot mutatja.)*

Ez a szakasz nem dönt, csak azt mondja meg, mi döntené el. Az itt lezárt
NY-5 az **5.12**-ben kapott választ.

> ⛔ **2026-09-09 (#2816): az NY-2 és az NY-3 sora ELAVULT.** Mindkettő a
> két gamma-tábla FELCSERÉLT hozzárendelésére épült. A helyes állapot a
> **12.5** pontban áll: az NY-3 futásidő-függése LEZÁRULT (a Mac gamma
> mindig az előre kitöltött táblát kapja), az NY-2 pedig ÁTKERÜLT a Mac
> gamma módra (1,44 vs. a feliratban ígért 1,6).

| # | a kérdés | miért nem dőlt el statikusan | mi döntené el |
|---|---|---|---|
| **NY-1** | **Hat-e a mód az exportra / nyomtatásra?** | **LEZÁRVA 2026-08-30 (#1580)** — a tulajdonos exportjai és nyomtatásai **bájtszinten azonosak**: a `chart_color__b050-001-24bit.jpg` vs `…-projektor-mod.jpg` csak **4 bájtban** tér el (a fejléc időbérjegye `"20"→"47"`, offset 116–117 és 2916–2917), a **pixel-adat azonos**; a `print-24bit.pdf` vs `print-projektor-mod.pdf` csak **6 bájtban** (a fájl végén, PDF `/ID`+`CreationDate`). ⇒ a mód **nem hat sem az exportra, sem a nyomtatásra** (a test `0x009e285d`-hoz kötött, csak képernyős). | lezárva (nem hat) |
| **NY-2** | **Miért ≈ gamma 1,44 a „Lineáris gamma (2.2)" táblája?** | **MEGERŐSÍTVE 2026-08-30 (matematika):** a `2.2` float itt csak a tábla **kiválasztó kulcsa**; a tábla a binárisban előre kitöltve érkezik. A mért 256 bájt illesztése: **p = 0,6944** hatványkitevő a legjobb (`round(255·(i/255)^p)`, **219/256 bájt azonos, a maradék ±1**), azaz a tábla **gamma 1/0,6944 = 1,440**. Az adatpont-gammák (i=1…4): 1,409 / 1,450 / 1,413 / 1,432 — konzisztens 1,44 körül. **A „miért épp 1,44" a generátor hiányában képernyőképet igényelne, de a megvalósításhoz NEM kell: a mért 256 bájtos tábla a szerződés (5.9).** | lezárva (a tábla a szerződés) |
| **NY-3** | **Mit csinál valójában a `Mac gamma (1.6)`?** | **MÉRVE 2026-08-30 (#1580)**: a tulajdonos teljes képernyős felvételei (24bit / gamma / automatikus) + codex-pixel-mérés — a gamma kép **VILÁGOSABB**: teljes képernyős luma **+3,32%** (RGB +7,1/255), a központi **fotó +15,7%** (133,5→154,5), a felület is +1,3…+4,2%. A világosítás iránya **konzisztens az `x^(1/1,6)` (0,625) LUT-tal**, a korábbi „1/0 → fekete képernyő" feltételezés **MEGDŐLT** (az adott futásban a tábla egy normál gamma-táblával töltődött). | reprodukálható a `pow(x,1/1,6)` LUT-tel; a futásidő-függés két indítási képpel továbbra is csak közvetetten zárható ki (de a mérés szerint nem a hibás 0-s ág fut) |
| **NY-4** | **Látszik-e a mód diavetítésben / teljes képernyőn?** | **LEZÁRVA 2026-08-30 (#1580)** — a tulajdonos megfigyelése (a `1580-megjelenitesi-mod/NY-4` README-je): **diavetítésben NEM látszik** a mód hatása. Ugyanakkor a **teljes képernyős** felületen IGEN (a NY-3 képei teljes képernyősek és a gamma hat rajtuk, a README: „a teljes felületre, még a menükre is"). | a diavetítés eltérő rajzolóúton fut; a mi implementációnk a NORMÁL nézetre tegye a módot |
| **NY-5** | **Mit csinál a `Színkezelés használata` (`ID_VIEW_COLOR_MANAGED`)?** | **LEZÁRVA (2026-08-30, #1582)** — lásd az **5.12** szakaszt: önálló kapcsoló, `Preferences\EnableColorManagement`, alap 0; bekapcsoláskor a szerkesztő-előnézet újraépül; a beágyazott `icc_camera_profile`/`icc_camera_to_tone_matrix` metaadat-tagok a forrás. | **a kapcsoló megvalósítása → #1725**; a felirat↔pipa párosítás a tulajdonos képeivel MEGERŐSÍTVE (a pipa a „Színkezelés használata" során) |
| **NY-6** | **A 16 bites szemcsézés pixelhű reprodukálhatósága.** | **LEZÁRVA 2026-09-10 (#2865, ld. 5.3/b).** ⛔ A cím téves volt: a `0x00aa2930` a **twist**, nem a magozás. A magozás a `0x00c33f90` CRT-statikus inicializálóban van: `mag = r3 ^ ((r2 ^ (r1<<12)) << 12)` három `rand()`-ból. **Nincs entrópiaforrás** a láncban ⇒ a szemcse **determinisztikus**. | lezárva — a vetőmag `0x80AE2D6C` (a feltétele az 5.3/b.5-ben), a szemcsézés bitre reprodukálható |

⚠️ **Amit szándékosan NEM állítok:** hogy az „LCD fehérpont" fehérpontot
állítana. A kód mindhárom csatornát **azonos** szorzóval sötétíti, tehát
színhőmérséklet-korrekció nincs benne. A felirat ellentmond a kódnak; a
`.tre`/`stringres` nem ad hozzá buboréksúgót, ami eldöntené a szándékot.
**A kód az igazságforrás.**

## 9. Amit NEM vizsgáltam

*(Ami ide tartozna, de már a 8. szakasz nyitott kérdései közt szerepel a
javasolt méréssel: export/nyomtatás · diavetítés · a `0x00aa40a0` nyolc
hívója · az MT-vetőmagozás — és az 5.12-ben az EnableColorManagement
felirathoz rendelt parancsazonosító kérdése, amely a #1582 képeivel
lezárult.)*

1. ~~**A megjelenítő objektum osztálya és életciklusa.** A `+0x254` horog
   egy általános rajzfelület-osztályon ül (más felületek is állítanak
   bele, pl. `0x009e8750`); nem derítettem ki, hány ilyen felület él
   egyszerre, és a mód csak a főnézetre vagy minden felületre hat-e.~~
   ⭐ **LEZÁRVA a 11. szakaszban (2026-09-09, #2813).** A horgot a
   **yt jelenetgráf-csomópont** alaposztálya viseli, és a Nézet-menü módja
   **pontosan EGY csomópontra** kerül. *(Két pontatlanság a fenti
   megfogalmazásban: a `0x009e8750` nem felület, hanem maga az egyik
   átalakító; és a mező nem „rajzfelület"-osztályon, hanem csomóponton
   van.)*
2. ~~**A `Picasa Photo Viewer`** (külön `.exe`, saját bináris-indexe van:
   `binary-index-photoviewer`) — van-e ott is megjelenítési mód.~~
   ⭐ **LEZÁRVA a 12. szakaszban (2026-09-09, #2816):** mód-MENÜ nincs, de
   a gamma-táblapár bájtra ott van és kód hivatkozik rá, a színkezelés
   pedig ugyanazzal a kulccsal él. Mellékesen kiderült, hogy az 5.9 és az
   5.10 tábla-hozzárendelése fel volt cserélve.
3. ~~**A menü ikonjai és gyorsbillentyűi** — a rekordok `+0x04`/`+0x08`
   mezője mindegyik módnál nulla, de ezt csak a Megjelenítési mód almenüre
   néztem meg.~~
   ⭐ **LEZÁRVA (2026-09-09, #2819):** a teljes menüsorra kimérve. A 173
   rekordból **24 hordoz gyorsbillentyű-szöveget** és **5 ikonszámot** — a
   Megjelenítési mód almenü tehát nem kivétel, hanem a többség. A táblázat
   a [picasa-menu-leltar.md](picasa-menu-leltar.md) **8.** szakaszában.
4. ~~**Buboréksúgó.** A `stringres` a tizenegy tételhez **nem** ad
   magyarázó szöveget; ezt kereséssel ellenőriztem, nem találtam.~~
   ⭐ **LEZÁRVA a 13. szakaszban (2026-09-10, #2838).** A negatív állítás
   igaz volt, de **rossz forrásban** keresett: a buboréksúgók nem a
   `stringres`-ben élnek, hanem a `TOOLTIPS.XML`-ben. Ott sincsenek — de
   nem „nem találtam", hanem **szerkezetileg lehetetlen**.

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

---

## 11. A `+0x254` horog HATÓKÖRE — a 9.1 pont lezárva (2026-09-09, #2813)

**Bizalmi fok: megerősített** (utasításszintű pásztázás + RTTI + két
független hívóhely-számlálás). A kérdés az volt: *hány rajzfelület viseli
a `+0x254` horgot, és a Nézet-menü módja a főnézetre hat-e csak, vagy
mindenre?* A #1730 kompozíciós rétegének hatóköre múlik rajta.

### 11.1 A teljes `.text` pásztázása a `0x254` eltolásra

A pásztázás **nem opkódra, hanem az eltolásra** szűrt — a `mov`-ra
szűkített keresés hamis negatívot ad (bitmaszk-mezőket csak `or`/`and`
ír). Eszköz: `eszkozok/binaris/paszta.py`, memóriaplafon alatt.

| mérőszám | érték |
|---|---|
| összes `0x254`-eltolású utasítás | **118** |
| ebből `[esp + 0x254]` (veremlokális, NEM a mező) | **16** |
| opkód-megoszlás | `mov` 81 · `cmp` 15 · `test` 10 · `and` 4 · `lea` 3 · `fild` 2 · `fstp`/`fisub`/`sub` 1-1 |

**Kontroll (a hibás minta ellen):** a spec 4. szakaszában megnevezett
olvasó, `0x009e285d`, szerepel a találati listában. A pásztázás tehát
nem üresre futott.

**Függvénymutató-konstans mindössze kettő kerül a mezőbe:**

| érték | hova írja | hányszor |
|---|---|---|
| `0x009e8750` | `[esi + 0x254]` | **4** írás: `0x00a6276d`, `0x00a63946`, `0x00a63a01`, `0x00a63b2f` (mindegyik előtt egy `cmp` ugyanerre az értékre: `0x00a6275e`, `0x00a6393d`, `0x00a639f8`, `0x00a63b20` — összesen 8 hivatkozás) |
| `0x009d56f0` | `[esi + 0x254]` | **1** írás: `0x009d5a67`. A második hivatkozása (`0x009d556f`: `mov dword ptr [eax + 0x10], 0x9d56f0`) **más mezőbe** megy, nem a horogba |

⚠️ **Helyesbítés a 4. és 9.1 szakaszhoz:** a `0x009e8750` **nem egy másik
felület**, hanem maga egy képsor-átalakító — ugyanabba a mezőbe kerül,
mint a Nézet-menü módjai.

### 11.2 Az osztály-aláírás: `cmp` → dirty-jelző → `mov`

A mezőt író helyek **egy** jól felismerhető idiómát követnek:

```
cmp dword ptr [this + 0x254], X
je  tovabb
or  dword ptr [this + 8], 2        ; ⭐ ÚJRARAJZOLÁS-JELZŐ
mov dword ptr [this + 0x254], X
```

A 14 `cmp`-helyből **12 hordozza** ezt az alakot. A két kivétel:

- `0x009e27bf` — a rajzoló null-ellenőrzése (`cmp …, 0` → átlép), nem író;
- `0x00a6c356` — **ír, de NEM állítja a dirty-jelzőt** (`0x00a6c35e`). A
  hívója (`0x00a6c240`) hat szövegcsomópont-osztály 17. vtábla-résében ül.
  ⭐ **LEZÁRVA a 14. szakaszban (2026-09-10, #2840): ez nem anomália** — az
  írás **nem a `this`-en** történik, hanem egy másik objektumon
  (`[this + 0x314]`), tehát a `this` piszkosítása hibás lenne.

A `+0x8` dirty-jelző az osztály-azonosság **legerősebb jele**: minden író
ugyanazt a szomszédos mezőt bolygatja meg.

### 11.3 Az osztály: a **yt jelenetgráf-csomópont**, nem „rajzfelület"

Két mezőíró **virtuális**, és ez adja meg az osztályt:

| függvény | vtábla-rés | osztályok (RTTI) |
|---|---|---|
| `0x00a63340` | **17** | `ytButtonNode` (31 rés) · `ytColorWheelNode` (31) · `ytPopupListNode` (33) |
| `0x00a6c240` | **17** | `CButtonText` · `CTextEditNode` · `ytFPSNode` · `ytTextEditNode` · `ytTextNode` · `ytToolTip` (mind 30 rés) |

Hogy `esi` valóban a `this`, az a prológusból olvasható:

```
0x00a6334b  mov esi, ecx        ; FUN_00a63340 — this
0x00a63998  mov esi, ecx        ; FUN_00a63990 — ugyanaz az osztály, nem virtuális tag
```

⇒ **A horog a respack/`yt` jelenetgráf csomópont-alaposztályán ül**, azon
a családon, amelyből a Picasa felülete fel van építve (377 `yt*` osztály
van RTTI-vel a binárisban). Nem egy dedikált „megjelenítő felület"
osztályon.

### 11.4 ⭐ A Nézet-menü módja PONTOSAN EGY csomópontra kerül

A tíz átalakító-konstans a **teljes `.text`-ben egyetlen** függvényben
szerepel közvetlen értékként — `0x005cb990`, a parancs-diszpécser —, és
mindegyik ág ugyanoda ad tovább:

```
0x005cbc40  mov ecx, 0x9e8b80        ; a mód átalakítója
0x005cbc45  call 0x575670            ; a mód-beállító
```

A mód-beállító (`0x00575670`) törzse **nem iterál**:

```
0x00575674  mov ebx, dword ptr [esp + 0x3c]   ; a TÁROLÓ (a hívó ebx-e)
0x00575678  mov eax, dword ptr [ebx + 0x14c]  ; EGYETLEN csomópont
0x00575683  je  0x575788                      ; ha nincs, nem tesz semmit
0x00575689  cmp dword ptr [eax + 0x254], ecx
0x00575691  or  dword ptr [eax + 8], 2
0x00575695  mov dword ptr [eax + 0x254], ecx  ; ⭐ A MÓD IDE KERÜL
0x005756a1  or  dword ptr [eax + 8], 7        ; teljes érvénytelenítés
0x005756d5  call 0xa54b70                     ; és újrarajzolás
```

**Nincs lista, nincs ciklus, nincs második csomópont.** A `+0x14c` egyetlen
slot; a `0x00a51e90` tanúsága szerint a tárolóban **két** csomópont-slot van
(`+0x14c` és `+0x150`), és a mód-beállító csak az elsőt írja.

**A hívóhely-készlet zárt** — indextől független pásztázással (nem a
függvényindexből, mert az lyukas):

| célfüggvény | hívóhely | hol |
|---|---|---|
| `0x00575670` mód-beállító | **13** | `0x0040be79`, `0x0040bea3` (indulási RDP-próba, `0x0040bd90`) + **11** a `0x005cb990`-ben = a tizenegy mód |
| `0x009e1c40` képsor-ciklus | **2** | mindkettő a `0x009e2a60`-ban (`0x009e3184`, `0x009e3323`) — a 4. szakasz „egyetlen hívó" állítása ÁLL |
| `0x009e2a60` rajzoló | **3** | `0x009e1a68` (`0x009e16d0`) + `0x00a55877`, `0x00a558aa` (`0x00a54b70`) |

### 11.5 A 16 bites tartalék MÁS út — és az 7 felületre megy

A `0x00a51e90` felület-csatoló a képernyő-színmélységtől függően **magától**
telepít horgot, a Nézet-menütől függetlenül:

```
0x00a51f45  cmp dword ptr [0xd33958], 0x20   ; a képernyő 32 bites?
0x00a51f4c  mov byte  ptr [esi + 0x213], 1
0x00a51f53  mov dword ptr [esi + 0x244], ebp ; a csomópont szülője = a tároló
0x00a51f59  je  0xa51f72                     ; 32 bit → nincs horog
0x00a51f5b  mov eax, 0x9e8b80                ; egyébként a 16 bites átalakító
0x00a51f6c  mov dword ptr [esi + 0x254], eax
```

Ennek **8 hívóhelye van 7 függvényben** (`0x0053010d`, `0x0062b25c`,
`0x0080fc47`, `0x00810401`, `0x0088af20`, `0x009c6b18`, `0x00a58857`,
`0x00a588fc`). Az egyik hívó, `0x0062b1e0`, a `CCaptureMoviePanelPopup`
vtáblájának 34. rése ⇒ **önálló, felbukkanó felület**.

⇒ **Két hatókör van, és nem ugyanaz:**

| út | mit telepít | hány csomópontra |
|---|---|---|
| Nézet ▸ Megjelenítési mód (`0x00575670`) | a választott átalakító | **1** (tároló `+0x14c`) |
| képernyő-mélység tartalék (`0x00a51e90`) | `0x009e8b80` (16 bites) | **7 csatolási pont** |

### 11.6 A #1580 mérésével való feszültség — kimondva, nem elsimítva

A #1580 képei szerint a `Mac gamma` **a teljes felületet** világosítja,
„még a menüket is". A bináris viszont **egyetlen** csomópontra teszi a
horgot. A kettő akkor és csak akkor egyeztethető össze, ha a `+0x14c`
csomópont a **fő ablak jelenetgráfjának GYÖKERE** — a Picasa menüi és
paneljei is `yt*` csomópontok, tehát a gyökér festése rájuk is kihat.

⚠️ **Ez KÖVETKEZTETÉS, nem mérés.** Amit a bináris ad: egy slot, egy írás.
Hogy a slot a gyökér-e, nincs kiolvasva.

**Falszifikálható előrejelzés (a megvalósítás előtt érdemes ellenőrizni):**
mivel a felbukkanó felületek (pl. `CCaptureMoviePanelPopup`) **külön**
csatolási ponton élnek és csak a mélység-tartalékot kapják, `Mac gamma`
bekapcsolt állapotában egy ilyen felbukkanó panelnek **változatlanul** kell
megjelennie. Ha a tulajdonos képén a felbukkanó panel is világosodik, akkor
a `+0x14c` nem gyökér, hanem valami közös kompozíciós cél — és a 11.4
egyetlen-írás lelete akkor is áll, csak más jelentéssel.

**Ez döntené el:** egyetlen képernyőkép a windowsos Picasából `Mac gamma`
módban, **nyitott felbukkanó panellel** (pl. a filmfelvevő panel).

### 11.7 Amit a #1730 ebből kap — hatókör-szerződés

1. A módot **egy** helyre kell alkalmazni, a jelenetgráf gyökerére —
   nem elemenként, nem képenként.
2. Az érvényesítés két lépés az eredetiben: `or flags, 7` (teljes
   érvénytelenítés) **és** egy explicit újrarajzolás-hívás. Nálunk is
   kell egy „mindent újrafest" jelzés, nem elég a LUT beállítása.
3. A **felbukkanó, önálló felületek** nem részei a hatókörnek (11.6
   előrejelzés) — a megvalósítás ne próbálja őket bevonni, amíg a
   képernyőkép nem mondja meg az ellenkezőjét.
4. A **16 bites tartalék NEM a Nézet-menü része** (`0x009e8b80` a
   mélységből jön) — a `dither16` kihagyása (#1579) tehát a menütételre
   igaz, a tartalék-útra nem értelmezendő.

---

## 12. A kísérő nézegető, és egy ÖNHELYESBÍTÉS a két gamma-táblán (2026-09-09, #2816)

**Bizalmi fok: megerősített.** A 9.2 pont („van-e megjelenítési mód a
`Picasa Photo Viewer`-ben") vizsgálata közben a nézegető **egyszerűbb**
kódja láthatóvá tette, hogy az 5.9 és az 5.10 tábla-hozzárendelése fel
volt cserélve. A kettő ugyanaz a lelet, ezért egy szakaszban áll.

### 12.1 A kontroll, amely a negatív állítást hitelesíti

A nézegető (`PicasaPhotoViewer.exe`, 4 806 984 bájt, belső neve
*Slingshot*) **nyers bájtjaiban** kerestem, nem az indexben — az index
`string_xrefs` táblája a fő binárison 26 %-ban hiányosnak bizonyult
(225. kör). Kontrollnak a #453-ban megnevezett, biztosan létező
feliratokat használtam:

| minta | ASCII-találat |
|---|---|
| `Launch Picasa` | **0x4174e7** ✅ |
| `More Options` | **0x417275** ✅ |

⇒ a pásztázás lát szöveget; a lenti nulla-találatok nem a minta hibái.

### 12.2 Megjelenítési mód MENÜ a nézegetőben NINCS

| minta | ASCII | UTF-16LE |
|---|---|---|
| `Projector` · `Sepia` · `Remote Desktop` · `Mac gamma` · `Linear gamma` · `Display Mode` · `Overexposed` · `Black and White` · `ID_VIEW_` | **NINCS** | **NINCS** |
| `LCD` | 0x1d0488 | NINCS |

⚠️ A `LCD` **hamis pozitív**: négybetűs formátumazonosítók táblájában ül
(`RLCC`, `RLCD`, `RLCE`, ` YMC`, ` VSH`, `YARG`) — a szomszédja dönti el,
nem a minta.

**A negatív állítás HATÓKÖRE:** a `PicasaPhotoViewer.exe` **teljes fájlját**
pásztáztam ASCII és UTF-16LE alakban a fenti mintákra. Ebből az következik,
hogy a nézegető **nem hordozza a fő program mód-feliratait**. Az **nem**
következik, hogy a felület semmilyen módváltót nem kínál: a feliratok a
Picasánál `.tre`/`stringres` erőforrásból is jöhetnek (a nézegető saját
`i18n\setuptext.xml`-t nevez meg).

### 12.3 ⭐ De a GAMMA-GÉPEZET ott van — bájtra ugyanaz

A fő program 256 bájtos, előre kitöltött táblája (`0x00d32bd0`) a
nézegetőben **bájtra azonosan**, pontosan **egyszer** megvan:

| | fő program | nézegető |
|---|---|---|
| fájloffset | 0x932bd0 | **0x377b58** |
| VA | 0x00d32bd0 | **0x00777b58** (`.data`) |
| különböző bájtértékek | 222 / 256 | ugyanaz |
| utána +256-on | `FF 00 00 …` őrszemes tábla | ugyanaz |

*(A 222 különböző bájtérték miatt a 256 bájtos egyezés nem lehet
véletlen. A **második** tábla önmagában `0xFF` + 255 nulla, tehát annak a
puszta megtalálása értéktelen — az bizonyít, hogy a PÁR ugyanabban a
sorrendben, +256 távolságra áll mindkét binárisban.)*

És **kód hivatkozik rájuk**: a nézegető `.text`-jében a `0x00777b58`
címre egy, a `0x00777c58`-ra egy hivatkozás van, mindkettő a
`FUN_00512fb0`-ban.

### 12.4 A nézegető kódja olvashatóbb — és ez buktatta le a felcserélést

```
0x00512fca  fldz                          ; 0.0
0x00512fcd  fld  dword ptr [ebp + 0xc]    ; a paraméter
0x00512fd3  fucom st(1)
0x00512feb  jp   0x512ff2                 ; jp = NEM egyenlő
0x00512fed  mov  edi, 0x777b58            ; ⭐ P == 0.0  →  ELŐRE KITÖLTÖTT tábla
0x00512ff2  fcom qword ptr [0x7522a0]     ; a konstans kiolvasva: 2.2
0x00512ffd  jp   0x513004
0x00512fff  mov  edi, 0x777c58            ; ⭐ P == 2.2  →  ŐRSZEMES tábla
0x00513004  cmp  byte ptr [edi], 0xff     ; kitöltetlen?
0x00513009  fld1 / fdivrp                 ; ha igen: 1/P a kitevő
```

**Az `x87` ág-polaritás**, hogy ne kelljen elhinni: `fucom` után
`fnstsw ax`, majd `test ah, 0x44` — a maszk a `C3` (0x40) és a `C2`
(0x04) bitre megy. Egyenlőségnél `C3=1, C2=0` ⇒ az eredmény `0x40`, egy
beállított bit ⇒ **páratlan** ⇒ `PF = 0` ⇒ a `jp` **NEM** ugrik.
Tehát: `jp` ugrik ⇔ **nem** egyenlő.

**Ugyanez a fő programban** (`0x00aa3f80`), veremkövetéssel:

```
0x00aa3f80  fld dword [0xcf4140]   ; 2.2 (kiolvasva)      verem: [2.2]
0x00aa3f89  fld st(0)                                     [2.2, 2.2]
0x00aa3f8c  fld dword [esp+0x18]   ; P                    [P, 2.2, 2.2]
0x00aa3f95  fucom st(1) / fstp st(1)                      [P, 2.2]
0x00aa3fa2  fldz                                          [0.0, P, 2.2]
0x00aa3fa4  jnp 0xaa3fb5           ; jnp = EGYENLŐ (P==2.2) → ugrik
   ... a másik ág fucomp-pal ellenőrzi, hogy P == 0.0, különben kiugrik
0x00aa3fb5  fxch st(2)                                    [2.2, P, 0.0]
0x00aa3fb9  fucomp st(1)           ; 2.2 vs P             [P, 0.0]
0x00aa3fc0  jp 0xaa3fc7
0x00aa3fc2  mov edi, 0xd32cd0      ; ⭐ P == 2.2  →  ŐRSZEMES tábla
0x00aa3fc7  fucom st(1)            ; P vs 0.0
0x00aa3fd0  jp 0xaa3fd9
0x00aa3fd2  mov edi, 0xd32bd0      ; ⭐ P == 0.0  →  ELŐRE KITÖLTÖTT tábla
0x00aa3fd9  test edi, edi / je     ; más érték nincs megengedve
```

És hogy melyik mód melyiket adja át, az a két átalakítóból olvasható:

| mód | átalakító | mit ad át | melyik tábla |
|---|---|---|---|
| `ID_VIEW_MAC` — Mac gamma (1.6) | `0x009e8b40` (`fldz`) | **0.0** | `0x00d32bd0` — **előre kitöltött** |
| `ID_VIEW_LINEAR` — Lineáris gamma (2.2) | `0x009e8b60` (`fld [0xcf4140]`) | **2.2** | `0x00d32cd0` — őrszemes, futásidőben töltődik |

### 12.5 Mi dől el ezzel — és mi NEM

**LEZÁRVA: NY-3 („mit csinál valójában a Mac gamma?") futásidő-függése.**
A „kitöltetlen tábla ⇒ `1/0` ⇒ szinte fekete képernyő" félelem **hamis
premisszán** állt: a Mac gamma ága az ELŐRE KITÖLTÖTT táblát választja,
amelynek első bájtja `0`, tehát az őrszem-ellenőrzés (`cmp byte ptr
[edi], 0xff`) sosem lép be rajta. A mód hatása **determinisztikus** — nem
függ attól, mi futott előtte. Ez összhangban van a #1580 mérésével
(világosodás), csak most már ok is tartozik hozzá.

**ÁTHELYEZVE: NY-2 („miért ≈1,44?").** A kérdés nem a `2.2` módra
vonatkozik — az a `pow(x, 1/2,2)`-t **futásidőben** számolja, tehát pontosan
2,2. Az ≈1,44 tábla a **Mac gamma (1.6)** módé. A felirat és a tábla
tehát eltér, és ez MÉRT, nem becsült:

| kitevő | egyező bájt (256-ból) | max. eltérés |
|---|---|---|
| **0,6945** (a legjobb illesztés) | **219** | 1 |
| 0,6944 (a korábbi illesztés) | 219 | 1 |
| 0,6250 = 1/1,6 (a felirat ígérete) | **4** | **10** |
| 0,4545 = 1/2,2 | 2 | 40 |

⇒ a `Mac gamma (1.6)` tábla effektív gammája **1,44**, nem 1,6. A
„miért épp 1,44" továbbra is **NYITOTT**, de a rés most 1,44 vs 1,6, nem
1,44 vs 2,2 — és a megvalósításhoz nem kell: a szerződés a 256 bájtos
tábla (5.9).

### 12.6 Színkezelés a nézegetőben — VAN, ugyanazzal a kulccsal

| lelet | bizonyíték |
|---|---|
| `EnableColorManagement` beállítás-kulcs | 0x327898, közvetlenül a `ViewerFullscreenStartup` mellett |
| valódi ICC-kezelés, nem csak kulcs | import: **`mscms.dll` / `GetColorDirectoryA`** |
| beépített profilnevek | `RSWOP.ICM`, `Photoshop5DefaultCMYK.icc`, `CMYKProfile`, `DebugDisplayProfile`, `(Picasa internal)` |

⇒ a fő program 5.12-ben leírt `EnableColorManagement` kapcsolója
**ugyanazzal a névvel** él a nézegetőben is. A #453 „négy kapcsolója"
közül a beállítás-blokkban ezek látszanak: `ViewerFullscreenStartup`,
`EnableColorManagement`, valamint a társítás-varázsló `setup/ui_option1`
… `ui_option5` elemei.

### 12.7 Amit a #1730 ebből kap — a LUT képlete ROSSZ a jegyben

A #1730 „Kész, ha" listája ma azt írja: *„a `mac` LUT `pow(x, 1/1,6)`"*.
**Ez mérhetően téves** — a fenti tábla szerint 256-ból 4 bájt egyezne, a
legnagyobb eltérés 10 szint. A megvalósítás **a `0x00d32bd0` 256 bájtos
tábláját** vegye át (az 5.9-ben teljes egészében ki van írva), vagy a
`p = 0,6945` kitevőt.


---

## 13. A buboréksúgó SZERKEZETILEG nem érhet menütételt (2026-09-10, #2838)

**Bizalmi fok: megerősített** a kulcsolásra és a menürekord alakjára; a
negatív állítás hatóköre a 13.4-ben.

A 9.4 pont azt írta, hogy a `stringres` nem ad magyarázó szöveget a
tizenegy módhoz. Ez igaz, de **nem a `stringres` a súgók helye.**

### 13.1 A súgószövegek helye és KULCSOLÁSA

A buboréksúgók a **`TOOLTIPS.XML`** erőforrásban élnek (a
`picasa-gyorsbillentyuk.md` 2.3 szerint **41 nyelvi változatban**, köztük
magyar). A magyar példány megvan a kutatási anyagban
(`referencia/i18n-hu/tooltips.xml`, 1002 sor, 55 678 bájt), és az angol
`.tre` oldala is (`referencia/tre-eroforrasok/tooltips.tre`, 174 sor).

Mérve a magyar példányon:

| mérőszám | érték |
|---|---|
| `<action>` elem | **333** |
| különböző **célelem** | **245** |
| ezekből `Tooltip` típusú | **146** |
| `type` értékek | `Tooltip` 152 · `Label` 136 · `Text` 29 · `Text1…Text7` 16 |
| a célnév alakja `panel/elem`? | **mind a 245-nél igen** |

A `.tre` oldal ugyanígy kulcsol, csak sorpárokban:

```
Tooltip printpanel/walletbutton
Print wallet-sized photos
```

⇒ **a kulcs a respack-ELEMNÉV**, semmi más.

### 13.2 ⭐ A döntő próba: NULLA menü-szerű kulcs

```python
[b for _,b in t if re.search(r'menu|cmd|ID_|view_', b, re.I)]   # → []
```

A 333 elem közül **egyetlen** célnév sem menüre utal. A tizenegy mód
egyetlen neve sem szerepel a fájlban (`projektor`, `gamma`, `szépia`,
`LCD`, `túlcsordul`, `16 bit`, `24 bit`, `távoli`, `fekete-fehér` — mind
**0 találat**; az „automatikus" 5 találata más panelekhez tartozik).

**KONTROLL** (a hibás minta ellen): a `printpanel/walletbutton` célnév
megvan, és 152 `Tooltip` típusú elem létezik ⇒ a minta lát adatot, a
nulla-találat valódi.

### 13.3 ⭐ MIÉRT lehetetlen: a menürekordban nincs elemnév

A menütételek **natív Win32-menübe** kerülnek (`InsertMenuItem`,
`picasa-menu-leltar.md` 8.4/d), és a 20 bájtos menürekord **hat mezője**
(uo. 7. szakasz) ez:

| mező | tartalom |
|---|---|
| `+0x00` | a lefordított felirat |
| `+0x04` | gyorsbillentyű-szöveg |
| `+0x08` | módosító-maszk |
| `+0x0a` | parancsazonosító |
| `+0x0c` | almenü-mutató |
| `+0x10` | almenü-darabszám |

**Elemnév-mező nincs.** A `TOOLTIPS.XML` viszont kizárólag elemnévre
kulcsol ⇒ **nincs mit hozzárendelni**. Ez nem keresési kudarc, hanem a
mechanizmus szerkezetéből következő kizárás — és ugyanezért **egyetlen**
menütételnek sem lehet buboréksúgója, nem csak a tizenegy módnak.

### 13.4 A negatív állítás HATÓKÖRE — kimondva

- **Mérve:** a magyar `tooltips.xml` (333 elem) és az angol `tooltips.tre`
  (45 kulcssor). Mindkettő `panel/elem` alakra kulcsol, menü-kulcs nincs.
- **NEM mérve:** a további 40 nyelvi változat. Azok ugyanabban a
  kulcstérben élnek (a célnév a nyelvtől független elemnév), de ezt nem
  mértem — ha valaki mégis menü-kulcsot talál bármelyikben, ez a szakasz
  megdől.
- **NEM állítom**, hogy a Picasa menüjén sosem jelenik meg magyarázó
  szöveg: az állapotsor-súgó (Win32 `WM_MENUSELECT`) más mechanizmus, és
  **nem vizsgáltam**.

### 13.5 Amit ez a NÁLUNK állapotra mond

A mi menüsorunkban sincs menü-tooltip ⇒ **ez helyes**, nem hiány. Ezt
azért írom ide, hogy ne kelljen újra felfedezni: a „hiányzik a menü
buboréksúgója" észrevétel az eredetivel szemben **nem valódi eltérés**.


---

## 14. A dirty-jelző nélküli `+0x254`-írás NEM anomália (2026-09-10, #2840)

**Bizalmi fok: megerősített** a szerkezetre; a célobjektum osztálya NINCS
meghatározva (14.4).

A 11.2 azt találta, hogy a 14 `cmp`-helyből 12 beállítja az
`or [this+8], 2` újrarajzolás-jelzőt, egy viszont nem. A magyarázat egy
mondat: **az az egy nem a `this`-re ír.**

### 14.1 A `0x00a6c240` MÁS objektum mezőjét írja

```
0x00a6c342  mov eax, dword ptr [edi + 0x314]   ; edi = this ; eax = egy MÁSIK objektum
0x00a6c348  test eax, eax
0x00a6c34a  je  0xa6c406                       ; ha nincs, kilép
0x00a6c350  mov ecx, dword ptr [edi + 0x294]   ; az ÉRTÉK a this-ből
0x00a6c356  cmp dword ptr [eax + 0x254], ecx   ; ⭐ a CÉL mezője
0x00a6c35c  je  0xa6c364
0x00a6c35e  mov dword ptr [eax + 0x254], ecx
```

⇒ a függvény a **saját `+0x294` értékét másolja** a `+0x314`-ben tárolt
másik csomópont horog-mezőjébe. A `this` **nem változik**, tehát a
`this + 8` piszkosítása **hibás lenne** — a kivétel nem hiba, hanem
következmény.

**Szembeállítás** a másik slot-17 megvalósítással (`0x00a63340`, 652 bájt,
`ytButtonNode` / `ytColorWheelNode` / `ytPopupListNode`):

| | `0x00a63340` (vezérlő-csomópont) | `0x00a6c240` (szövegcsomópont) |
|---|---|---|
| a bázis | `esi` = **`this`** (`0x00a6334b mov esi, ecx`) | `eax` = **`[this+0x314]`** |
| dirty-jelző | **igen**, `0x00a634da or [esi+8], 2` | **nincs** |
| null-őr a bázisra | nincs (a `this` mindig él) | **van**, `0x00a6c34a` |

### 14.2 Jelző helyett VIRTUÁLIS HÍVÁS a célobjektumon

```
0x00a6c3c3  mov ecx, dword ptr [edi + 0x314]   ; a cél
0x00a6c3c9  mov edi, dword ptr [ecx]           ; a cél VTÁBLÁJA
   …
0x00a6c3ff  mov edx, dword ptr [edi + 0x2c]    ; 0x2c / 4 = a 11. rés
0x00a6c404  call edx
```

⇒ a szövegcsomópont **nem bitet állít, hanem megkéri** a célobjektumot: a
saját osztályának **11. virtuális rését** hívja. Ez a „máshol kéri az
újrarajzolást" konkrét alakja.

### 14.3 ⚠️ Amitől ez nem „hiányból vont következtetés"

A függvényben a `[reg + 8]` alak **hatszor** előfordul, és könnyű lenne
jelző-írásnak olvasni. Elolvasva **egyik sem az**: mind egy 16 bájtos
szerkezet **veremre másolása** egy hívás előtt, felismerhető alakban:

```
0x00a6c3b0  sub esp, 0x10
0x00a6c3b3  mov edx, esp
0x00a6c3b5  mov dword ptr [edx],       ebx
0x00a6c3ba  mov dword ptr [edx + 4],   ebx
0x00a6c3cb  mov dword ptr [edx + 8],   ebx   ; ← ez NEM jelzőmező
0x00a6c3ce  mov dword ptr [edx + 0xc], eax
```

Így a „a függvény semmit nem piszkosít" állítás **elolvasott utasításokon**
áll, nem azon, hogy nem találtam jelző-írást.

### 14.4 Ami NYITVA marad — pontos következő lépéssel

**A célobjektum osztálya nincs meghatározva**, ezért a **11. rés** sem
nevezhető meg: az a cél *dinamikus* típusától függ.

⚠️ A `+0x314` eltolás **nem osztályspecifikus**: a `.text`-ben **22** írása
van, szétszórva (`0x0062d4e4`-tól `0x00b98059`-ig), és több osztályhoz
tartozik — köztük `byte` méretű írások is (`0x0067c2ac`), tehát ott biztosan
más mező. **Ebből az eltolásból osztályt következtetni tilos.**

**A megszerzés útja:** a szövegcsomópont-modulban **egyetlen** `+0x314`-írás
van, `0x00a6b75c` (`mov dword ptr [ebp + 0x314], esi`) — ez a jelölt.

> ⛔ **A jelölt KIESETT (2026-09-10, #2842).** Nem hozzárendelés, hanem
> nullázás: nyolc egymást követő mező kap `esi`-t, és az `esi` **bizonyítottan
> 0**. A részletek és ami helyette kiderült: **15. szakasz.**


---

## 15. A célmutató NULLÁZOTT, és nincs mért hozzárendelése (2026-09-10, #2842)

> ⛔ **ELAVULT — a 16. szakasz helyesbíti.** Ez a szakasz a konstruktor
> `+0x314`-ét azonosította a célmutatóval; **rossz mező**. Az olvasó a
> MÁSODLAGOS vtáblából jön, tehát `this+4`-et kap, és a mezője a valódi
> `+0x318`. A célmutatót a `0x00a6bdfa` állítja be minden olvasás előtt,
> a cél osztálya `ytFontCache`. Az alábbi 15.4 „valószínűleg soha nem fut
> le" állítása MEGDŐLT.

**Bizalmi fok: megerősített** a nullázásra és az osztálynévre; a
„soha nem fut" állítás **feltételes** (15.4).

### 15.1 A jelölt kiesett: nullázás, nem hozzárendelés

A 14.4 a `0x00a6b75c`-t nevezte meg jelöltként. Elolvasva **nem** az:

```
0x00a6b6a9  xor esi, esi                       ; ⭐ esi = 0
   …
0x00a6b732  mov dword ptr [ebp + 0x2f8], esi
0x00a6b738  mov dword ptr [ebp + 0x2fc], esi
0x00a6b73e  mov dword ptr [ebp + 0x300], esi
0x00a6b744  mov dword ptr [ebp + 0x304], esi
0x00a6b74a  mov dword ptr [ebp + 0x308], esi
0x00a6b750  mov dword ptr [ebp + 0x30c], esi
0x00a6b756  mov dword ptr [ebp + 0x310], esi
0x00a6b75c  mov dword ptr [ebp + 0x314], esi   ; ⭐ a „jelölt": NULLÁZÁS
```

**Nyolc egymást követő mező** kap ugyanazt a nullát. Ez konstruktor-kezdő
tisztítás, nem célmutató-beállítás.

### 15.2 ⭐ Az osztály MEGVAN: `ytTextNode`

A tartalmazó `0x00a6b680` (623 bájt) **konstruktor**, és a vtábla-írásai
megnevezik az osztályt:

| cím | a beírt vtábla | RTTI-név |
|---|---|---|
| `0x00a6b68e` | `0xc9432c` a `[ebp]`-be | **`ITextSettings::vftable`** |
| `0x00a6b69c` | `0xce4bb4` a `[esi]` = `this+4`-be | **`ytTextNode::vftable`** |
| `0x00a6b6a2` | `0xce4b04` a `[ebp]` = `this+0`-ba | **`ytTextNode::vftable`** |

⇒ a `+0x314` mező a **`ytTextNode`** (és a vele egy vtábla-alakot osztó öt
társ) tagja, és a konstruktor **nullára** állítja.

### 15.3 Az ÉRTÉK forrása viszont ÉL

Nem szimmetrikus a helyzet: a `+0x294` (amit a `0x00a6c350` beolvas)
**valódi, írt mező**. A `.text`-ben 18 írása van, és **kettő ugyanebben a
modulban**:

```
0x00a6b7f5  mov dword ptr [ebp + 0x294], eax   ; ugyanebben a konstruktorban
0x00a6ba7a  mov dword ptr [esi + 0x294], ecx
```

⇒ az érték oldala rendben van; **csak a célmutató marad nullán**.

### 15.4 ⚠️ Amit ebből következtetni SZABAD — és amit nem

**Mérve:** a `+0x314`-nek **22** írása van a `.text`-ben, és **egyik sem** a
`ytTextNode` vtábla-slotjaiban (mind az **55** rekesz átnézve a két
vtáblából).

**Feltételes állítás:** a `0x00a6c35e` írása a szállított építésben
**valószínűleg soha nem fut le**, mert a `0x00a6c34a` null-őr kilép, amikor
a `+0x314` nulla.

⛔ **Ez NEM bizonyítás.** A `ytTextNode` **nem virtuális** tagfüggvényei
nincsenek a vtáblában, tehát egy nem virtuális tag vagy egy külső gyár
beállíthatja a mezőt anélkül, hogy a fenti metszet megfogná.

⛔ **A szomszéd-eltolás alapú keresés NEM bizonyíték.** Végigpróbáltam
(`+0x294`, `+0x2ef`, `+0x2f8`…`+0x310`), és hét jelölt jött ki — de
közülük több **`byte` méretű** hozzáférést használ ugyanazokon az
eltolásokon (`0x00b97c7b byte ptr [ebx + 0x300], 0`), ami **más
szerkezetet** jelent. Az eltolás-egyezés önmagában nem osztályazonosság.

### 15.5 A megszerzés útja — pontos következő lépés

A `ytTextNode` **nem virtuális** tagjait kell összeszedni, és bennük keresni
a `+0x314`-írást. Két járható út:

1. **A konstruktor hívói** (`0x00a6b680` xref-jei): a gyár vagy a szülő
   csatolója, amely a példányt létrehozza — ott dőlhet el, ki kapja meg a
   mutatót.
2. **Az osztály jellemző mezőpárja**: olyan függvényt keresni, amely a
   `+0x314`-et **és** a `+0x294`-et is érinti — ez erősebb szűrő, mint a
   puszta szomszédság, mert a `+0x294` a `ytTextNode`-on bizonyítottan élő
   mező.

## 16. A célmutató MEGVAN — `ytFontCache`, és a 15. szakasz ÖNHELYESBÍTÉSE (2026-09-10, #2842)

**Bizalmi fok: megerősített.** Minden állítás mellett cím és kiolvasott alak
áll; a pásztázások a lyukas függvényindextől FÜGGETLENÜL, a teljes `.text`-en
futottak (`eszkozok/binaris/paszta.py`, csúcs-RSS 86–87 MiB).

### 16.1 ⛔ ÖNHELYESBÍTÉS: a 15. szakasz ROSSZ MEZŐT vizsgált

A 15. szakasz abból indult ki, hogy a `0x00a6c342` által olvasott
`[edi + 0x314]` ugyanaz a mező, amit a konstruktor a `0x00a6b75c`-en nulláz
(`[ebp + 0x314]`). **Nem ugyanaz.** A két bázis négy bájttal eltér:

| hely | bázis | mi ez |
|---|---|---|
| konstruktor `0x00a6b680` | `ebp` | az objektum **valódi** kezdete — ide megy a `0xce4b04` elsődleges vtábla (`0x00a6b6a2`) |
| olvasó `0x00a6c240` | `edi = ecx` | a **MÁSODLAGOS** alobjektum: a `0xce4bb4` vtábla a `this+4`-en ül (`0x00a6b68b lea esi,[ebp+4]`, `0x00a6b69c mov [esi], 0xce4bb4`) |

Az index megnevezi, melyik vtáblában áll az olvasó: a `0x00a6c240` a
**`ytTextNode::vftable` `0x00ce4bb4`** tábla **17.** rekesze, a `0x00a6c4b0`
ugyanennek a 8. rekesze. A `0x00ce4bb4` a `this+4`-re írt tábla ⇒ mindkét
metódus `this+4`-et kap.

**Bizonyíték a kódból, két helyen**, mindkettő a segédhívás előtt:

```
0x00a6c32e  lea esi, [edi - 4]      ; olvasó A: vissza az objektum elejére
0x00a6c335  call 0xa6bd80
…
0x00a6c75d  lea esi, [ebx - 4]      ; olvasó B: ugyanaz
0x00a6c760  call 0xa6bd80
```

⇒ az olvasók `[+0x314]`-e az objektum **valódi `+0x318`** mezője, a
konstruktor nullázott `+0x314`-e pedig a **szomszédja**. A 15.4 „a
`0x00a6c35e` írása valószínűleg soha nem fut le" állítása ezzel **MEGDŐL**.

### 16.2 A célmutatót a `0x00a6bdfa` állítja be — minden olvasás ELŐTT

```
0x00a6bdea  mov  eax, dword ptr [esi + 0x2a0]
0x00a6bdf0  call 0xa48e10                      ; ⭐ betűkészlet-gyorstár lekérése
0x00a6bdf5  add  esp, 8
0x00a6bdf8  test eax, eax
0x00a6bdfa  mov  dword ptr [esi + 0x318], eax  ; ⭐ A CÉLMUTATÓ
0x00a6be00  je   0xa6be37                      ; NULL -> 4-es hibakód, a rajzolás elmarad
0x00a6be08  mov  dword ptr [eax + 0x258], ecx  ; cél +0x258 <- [esi+0x2a4]
0x00a6be1a  mov  dword ptr [edx + 0x250], eax  ; cél +0x250 <- [esi+0x29c]
0x00a6be2c  mov  byte  ptr [ecx + 0x210], dl   ; cél +0x210 <- byte [esi+0x2f0]
```

A `0x00a48e10` (309 bájt) **közös gyár, 25 hívóval** — nem a szövegcsomópont
sajátja. A mutató tehát **lustán frissített gyorstár**, nem halott mező.

A második írás, `0x00a6bb37` (`FUN_00a6b9e0`), **másolás**: ugyanabban a
menetben viszi át a `+0x318`, `+0x2a4`, `+0x2a8`, `+0x24c` mezőket.

### 16.3 A cél osztálya: `ytFontCache` — két független mérés

**(a) A veremméret ujjlenyomata.** A `0x00a6c3ff` hívóhely `0x38` bájtot tol
be (4+4+16+16+4+4+4+4), és utána `mov esp, ebp`-vel áll helyre ⇒ a hívott
`ret 0x38`. Az RTTI **150 különböző 11. rekesze** közül **pontosan egy**
ilyen: `0x00a46bb0` = **`ytFontCache::vftable` (`0x00ce400c`)** 11. rekesze.

**(b) A `+0x254` mező létezése.** A cél `+0x254`-ét a `0x00a6c35e` írja. A
`ytFontCache` konstruktora (`FUN_00a43f80`, a `0xce400c`-t a `[edi]`-be írja)
**maga is írja ezt a mezőt**: `0x00a4407e mov dword ptr [edi + 0x254], eax`.

### 16.4 Amit a 11. rekesz csinál — és a 12.

| hívóhely | rekesz | cím | hogyan |
|---|---|---|---|
| `0x00a6c3ff` | **11** (`[vtbl+0x2c]`) | `0x00a46bb0` (581 b) | `mov edi,[ecx]` (a cél vtáblája), `call [edi+0x2c]`, `this=ecx` |
| `0x00a6c7c5` | **12** (`[vtbl+0x30]`) | `0x00a48240` | `mov edx,[ecx]`, `mov edx,[edx+0x30]` |

Mindkettő két 16 bájtos veremblokkot kap (a `[ebx+0x60]` négy dwordje és egy
`[esp+0x38]`-tól másolt négyes) ⇒ két téglalap/négyes, plusz jelzők.

### 16.5 A `+0x254`-be írt ÉRTÉK — mérve, de a JELENTÉSE nyitott

```
0x00a6c350  mov ecx, dword ptr [edi + 0x294]   ; = valódi +0x298
0x00a6c356  cmp dword ptr [eax + 0x254], ecx
0x00a6c35e  mov dword ptr [eax + 0x254], ecx
```

A forrás a szövegcsomópont **valódi `+0x298`** mezője. A konstruktor
`0x00a6b7ec mov eax, 0xc` / `0x00a6b7ff mov [ebp+0x298], eax` ⇒ az
**alapértéke 12**. A teljes `.text`-en a valódi `+0x298`-nak **89 írása** van,
ebből a szövegmodulban kettő: a konstruktor és a másoló (`0x00a6ba86`).

⛔ **NEM állítjuk, hogy ez a megjelenítési mód.** A 11. szakasz `+0x254`-e a
`yt` **jelenetgráf-csomópont** mezője; a `ytFontCache` **más osztály**, az ő
`+0x254`-e külön kérdés. A hatókör: a fenti mérés a `+0x298` ÍRÓIRA vonatkozik,
nem a mező jelentésére.

### 16.6 A negatív állítások pontos hatóköre

- A teljes `.text`-en **27** írás megy a `+0x314`-re; ebből **egy** a
  `ytTextNode`-é (`0x00a6b75c`), és az **nulláz**. Kontrollpozitív: igen.
- Az **eltolt bázisú** (`lea r,[b+K]` / `add r,K`) pásztázás eredőre `+0x314`:
  **23** találat, a szövegmodulban egy sem; a `0x00a62a65` a
  `ytButtonNode` (`0x00a62982` írja a `0xce4874`-et) alstruktúra-nullázása.
  Kontrollpozitív: igen.
- ⛔ **Az index lyukas, mérve:** a függvényindexre alapozott futás **két**
  írást nem látott (`0x00b7160e`, `0x00b71946`) — egyik indexelt függvénybe
  sem esik. Mindkettő egy `malloc(0x320)`+`memset` C-struktúráé
  (`0x00b71898`), nem C++ objektumé.

## 17. A `ytFontCache` `+0x254` a SORELŐTOLÁS (2026-09-10, #2845)

**Bizalmi fok: megerősített** a szerepre; **feltételes** arra, hogy ez a
`.tre` `fontleading` attribútuma (17.5).

### 17.1 A mező egész szám, és a szövegtördelő Y-tengelyén dolgozik

A `ytFontCache` `+0x254`-ének a teljes `.text`-ben nyolc hivatkozása van a
`0x00a43000`–`0x00a4a000` tartományban (indextől független pásztázás,
kontrollpozitív `0x00a4407e`): négy írás és négy olvasás. Mind a négy olvasás
**egész-műveletként** használja (`fild` / `fisub` / `sub`), a
`FUN_00a47410`-ben — ez a szövegtördelő.

**A döntő hely: az új sor Y-előtolása.**

```
0x00a47b65  fild  dword ptr [ebp + 0x254]
0x00a47b6b  mov   edi, dword ptr [esp + 0x474]   ; a toll {x:+0, y:+4}
0x00a47b72  fadd  dword ptr [edi + 4]            ; y = y + sorelőtolás
0x00a47b75  fstp  dword ptr [edi + 4]
```

**A férőképesség-vizsgálat ugyanezzel:**

```
0x00a47a22  fild  dword ptr [ebp + 0x254]
0x00a47a2f  fadd  dword ptr [edx + 4]            ; a KÖVETKEZŐ sor alja
0x00a47a32  fild  dword ptr [esp + 0x494]        ; a korlát
0x00a47a39  fcompp                               ; belefér-e még?
…
0x00a47b7e  fld   dword ptr [edi + 4]
0x00a47b81  fisub dword ptr [ebp + 0x254]        ; vissza az előző alapvonalra
```

⇒ a `+0x254` **egy sor függőleges előtolása képpontban**.

### 17.2 A sorváltó ág ELŐTT a `\n` és a `\r` kezelése áll

`0x00a479f2 cmp si, 0xa` (LF) és `0x00a479fc cmp si, 0xd` (CR) — mindkettő a
`0xa47b20` karakter-léptetőre ugrik, és a ciklus kifutása után jön a fenti
sorzáró blokk. A `+0x254` tehát a **sortörés** ára, nem a betű magassága.

### 17.3 Egysoros ág: MÁSIK két mező

Ha a `[esp+0x11]` jelző nulla (`0x00a47b43`), az egysoros út fut, és ott az
Y-előtolás **nem** a `+0x254`:

```
0x00a47bd7  mov  edx, dword ptr [ebp + 0x1d0]
0x00a47bdd  add  edx, dword ptr [ebp + 0x1c0]    ; magasság + ráadás
0x00a47be9  fild dword ptr [esp + 0x30]
0x00a47bf5  fadd dword ptr [ecx + 4]
```

⇒ a `+0x1c0` + `+0x1d0` a **természetes** sormagasság, a `+0x254` a
**megadott** sorelőtolás. Ezért két külön mező.

### 17.4 Az alapérték 12 — ugyanabban az utasításban, mint a `+0x1c0`-é

```
0x00a45b00  mov   eax, 0xc
0x00a45b24  mov   dword ptr [esi + 0x1c0], eax   ; = 12
0x00a45b30  mov   dword ptr [esi + 0x250], ebx   ; = 0
0x00a45b36  mov   dword ptr [esi + 0x254], eax   ; = 12
```

A `FUN_00a45ac0` (a `ytFontCache` 5. vtábla-rekesze) minden újratöltésnél
visszaállítja ezt a hármat.

### 17.5 A kapcsolat a `.tre`-vel — EGYBEESÉS, nem bizonyíték

A `picasa-gomb-es-menu-rendszer.md` 6. szakasza a `fontmacros_win.tre`-ből
olvasva közli, hogy a leggyakoribb gombfelirat-makró (`m_buttonfontC`)
`fontsize 12`, `fontleading 10`, `fonttrack -1`. A binárisban a
**`fontleading`** literál egyetlen helyen szerepel (`0xc7c9c0`, a
`FUN_009ca5e0` attribútum-feldolgozóban), ott viszont a feldolgozó
**virtuális kezelőt hív** (`call [edx+8]` a `0x009c6f60` feloldása után), nem
közvetlenül ír mezőt.

⛔ **Ezért NEM állítjuk bizonyítottnak, hogy a `+0x254` == `fontleading`.**
A szerep (sorelőtolás) mérve van; a `.tre`-attribútum és a mező összekötése
egy további lépés: a `0x009ca5e0` `fontleading`-ágának kezelőjét kell
végigkövetni a `0x009c6f60`-on át.

### 17.6 Aki beleírja: a szövegcsomópont, MINDEN rajzolás előtt

A 16. szakasz menete szerint a szövegcsomópont a saját valódi `+0x298`-át
másolja ide (`0x00a6c35e`, `0x00a6c77b`), és ugyanabban a menetben még hármat:

| a gyorstár mezője | forrás | hol |
|---|---|---|
| `+0x250` | `[esi+0x29c]` | `0x00a6be1a` |
| `+0x254` | `[edi+0x294]` = valódi `+0x298` | `0x00a6c35e` |
| `+0x258` | `[esi+0x2a4]` | `0x00a6be08` |
| `+0x210` (bájt) | `byte [esi+0x2f0]` | `0x00a6be2c` |

Ez azért kell, mert a gyorstár **közös**: a `0x00a48e10` gyárnak **25 hívója**
van, tehát minden használó a saját szövegbeállításait tolja bele rajzolás
előtt.

**A `+0x250` szerepe is mérve** (ugyanaz a pásztázás): egész, és a
glifa-léptetésben adódik hozzá (`0x00a4661b fiadd`, `0x00a467b5 fild`,
`0x00a4720b`, `0x00a4738f`), alapértéke **0** (`0x00a45b30`). Ez a
**betűköz**-szerepre illik (a `.tre`-ben `fonttrack`), de a `.tre`-hez kötése
ugyanaz a nyitott lépés, mint 17.5-ben.

## 18. A `.tre` attribútum → mező kötés MEGVAN (2026-09-10, #2847)

**Bizalmi fok: megerősített.** A lánc mindkét fele mérve, cím szerint.

### 18.1 A két közvetlen mezőírás

A `.tre` `Property`-feldolgozó (`FUN_009ca5e0`) a legtöbb attribútumot
feloldó függvényen át adja tovább, **hármat viszont közvetlenül ír**:

```
0x009ca93d  call 0x9c6f10
0x009ca94a  mov  dword ptr [eax + 0x29c], edi   ; ⭐ fonttrack
…
0x009ca9bf  call 0x9c6f10
0x009ca9cc  mov  dword ptr [eax + 0x298], edi   ; ⭐ fontleading
…
0x009caa40  call 0x9c6f10
0x009caa4d  mov  dword ptr [eax + 0x2a8], edi   ; virtualfontsize
```

A `0x009c6f10` a szövegcsomópontot adja vissza (a `+0x298` ott a konstruktor
`0x00a6b7ff`-e szerint alapból 12).

### 18.2 A teljes lánc, két körből összerakva

| `.tre` attribútum | csomópont-mező | gyorstár-mező | szerep |
|---|---|---|---|
| `fontleading` | `+0x298` (`0x009ca9cc`) | `+0x254` (`0x00a6c35e`) | **sorelőtolás** (17.1) |
| `fonttrack` | `+0x29c` (`0x009ca94a`) | `+0x250` (`0x00a6be1a`) | **betűköz** (17.6) |

⇒ a 17. szakasz hipotézise (17.5) **beigazolódott**, immár méréssel: a
`+0x254` valóban a `fontleading`, a `+0x250` valóban a `fonttrack`.

### 18.3 A `fontsize`/`fontname`/`fontweight` MÁS úton megy

Ez a három nem közvetlen mezőírás, hanem `0x009c6f60` + virtuális hívás
(`call [edx+8]`): `0x009ca79d`, `0x009ca82e`, `0x009ca8b4`. Ez egybevág a
`picasa-respack-format.md` 7. szakaszával: a `.ytf` fájlnév a
**család–méret–skála–súly–stílus** ötöst kódolja, tehát ezek a gyorstár
**azonosságához** tartoznak — a sorköz és a betűköz nem, azokat használatonként
tolja be a rajzoló (16.6).

### 18.4 Értékkészlet a `.tre`-ből (kontroll)

`referencia/tre-eroforrasok/fontmacros_win.tre`, 308 sor: `fontleading` = 10
(15 helyen) és 15 (1 helyen); `fonttrack` = −1 (34 helyen) és −2 (1 helyen).
Mindkettő elfér a mért egész mezőben, és a `fonttrack` negatív értéke
megmagyarázza, miért **hozzáadás** a glifa-léptetésnél (`0x00a4661b fiadd`):
a negatív szám szűkíti a betűközt.
