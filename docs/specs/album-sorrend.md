# A mappák és albumok képsorrendje — hol él, mi írja, mi rendezi

*Picasa 3.9 (`Picasa3.exe`, a bináris-index SHA-256-jával azonos példány),
mérve 2026-10-12, #4884 (a #4599 előfeltétele). Minden állítás mellett cím
(image base `0x400000`), mért adat vagy `NINCS MEG`. A diszasszemblálás helyi,
capstone-nal (`picasapy-agent/eszkozok/binaris/picasa_dis.py`); a negatív
állítások a teljes `.text` indextől független pásztázásán alapulnak (bájtminta
+ capstone-ellenőrzés, ill. darabolt `paszta.utasitasok()`).*

> **Ez a lap lezárja a `pmp-database.md` két korábbi állítását.**
> (1) A „kézi sorrend az `albums_0.db`-ben" (2026-08-30) — a #4591 már
> cáfolta (a fájl élő tartalma 41/41 borító-raszter). (2) A #4591 15.4
> szakaszának „a kézi sorrend tárolási helye NINCS MEG" állapota — **most
> MEGVAN**: a `wordhash.dat`, a keresőindex szótára.

---

## 1. A válasz egy bekezdésben

A Picasa a mappa és az album **képeinek sorrendjét nem kulccsal számolja,
hanem listaként tárolja**: minden mappa és album egy szó a keresőindexben
(`]album:<token>`, a `albumdata_token` értéke), és a szóhoz tartozó
**rekordindex-lista sorrendje maga a megjelenítési sorrend**. A lista a
`db3\wordhash.dat`-ba íródik, és onnan töltődik vissza, tehát **túléli az
újraindítást**. Ugyanezt a listát írja át
- a **kézi húzás** (eltávolít + pozícióra beszúr), és
- a **„Sort Album By" / „Sort Folder By"** menü — ami **egyszeri
  átrendezés**, nem tartós nézet-mód: a listát egyszer rendezi név, dátum
  vagy méret szerint (Shift-tel fordítva), vagy megfordítja, és utána a
  rendezett sorrend ugyanúgy kézi sorrendként él tovább.

Az album **rendezési módja sehol nincs tárolva** — nincs mit tárolni, mert
nincs mód, csak sorrend. A rács rendezési módja (`CSelectionNode+0x2c0`)
a könyvtár-nézetben **0 = „rendezés nélkül, a lista sorrendjében"**.

---

## 2. Bizonyítékok

### 2.1 A sorrend hordozója: a `CSlice` → a keresőindex szava

| lépés | cím | mit mutat |
|---|---|---|
| az album-rekord osztálya | `CSlice`, vtábla `0x00c81e94`, ktor `0x004133e0` | RTTI |
| a rekord kitöltése | `IThumbDB` vtábla (`0x00c81fa4`) `+0x2c` rése = **`0x004406f0`** | kiolvassa az album `token`-jét (`[db+0xaf0]`, a regisztráló `0x004158d5`–`0x004158f4` szerint a `token` oszlop), majd `0x004408ef` → `0x004dca40(token, slice)` |
| a keresés | **`0x004dca40`** | a `CIndexer` (`db+0x68`, ktor `0x004d8560`; `.\thumblab\CIndexer.cpp`) hash-táblájában (`[+0x60]`, `[+0x58]` vödörszám) `_stricmp`-pel (`0x004dcacf`) keresi a szót; találatnál **`slice+0x60` = a szó, `slice+0x64` = a szó listája** (`0x004dcb11`–`0x004dcb17`), `slice+0x5c` = az index |
| az index perzisztens | a regisztráló `0x004166c9`: `m_index` = `db+0x68`, a felülete `db+0xb0` (= `+0x48`), ugyanúgy, mint az `m_albumData`-é (`0x00416b45`, `db+0x988`/`+0x9d0`) | a perzisztált táblák közé tartozik |
| az író | `0x004db4f0` (a felület vtáblája `0x00c85fc4`, 1. rés) | csak ha a piszkos-jelző áll (`[felület+8]`, lekérdező `0x00a4a080`); `wordhash.dat`-ot nyit, a hash-táblát `0x00704500`-zal írja ki, utána nulláz (`0x004db6b0`) |
| az olvasó | `0x004db720` (2. rés) | `0x007046e0`-val tölti vissza; a listát `0x00891110` (lista-értékadás) másolja, **rendezés nélkül** |

### 2.2 Minden változtatás a lista **sorrend-érzékeny** ellenőrzőösszegén át jelöl

A `CSlice` zárolása a vtábla `+0x18`/`+0x1c` rése:

| rés | cím | mit tesz |
|---|---|---|
| `+0x18` (zárás) | **`0x006cb4b0`** | az első zárásnál ellenőrzőösszeget számol a listáról és elteszi (`[slice+0x8c]`, `0x006cb4fa`–`0x006cb513`) |
| `+0x1c` (oldás) | **`0x006cb520`** | az utolsó oldásnál újraszámolja; ha eltér → `0x004db8f0(szó, 1 vagy 2)` (`0x006cb597`) |
| a jelzés | **`0x004db8f0`** | `[index+0x4c]++`, **`[index+0x50] = 1`** (= a felület piszkos-jelzője) — ettől íródik ki a `wordhash.dat` |

Az ellenőrzőösszeg: `h = n+1; minden elemre h = rol(h,7) XOR elem`
(`0x006cb567`–`0x006cb57e`). A forgatás miatt **puszta átrendezés is más
összeget ad** — a kód tehát kifejezetten a sorrend változását is menti.

### 2.3 Kézi húzás (3. kérdés)

A `CAlbumSelectionNode` vtábla-rése `0x00784820` → **`0x00784100`** (1811 b)
a beejtés kezelője. A `CSlice` zárása (`0x007843e2`, `+0x18`) és oldása
(`0x007844f1`, `+0x1c`) között minden húzott elemre:

1. `0x006cb200(slice, rekord, &hely)` — **eltávolítja** a listából
   (`0x00784446`, ismételve, amíg talál: `0x0078447b`), és ha a régi hely a
   célpozíció előtt volt, a célt eggyel csökkenti (`0x00784454`–`0x0078445d`);
2. `0x006c9e80(slice, pozíció, elem, 0)` — **beszúrja a célpozícióra**
   (`0x00784490`), majd a pozíció eggyel nő (`0x0078449f`).

⇒ A húzás a `]album:<token>` szó listáját írja át, az oldás jelöl, a
`wordhash.dat` a következő perzisztáláskor kiíródik. Mappára és albumra
ugyanez az út (a mappa is album-rekord: `albumdata_category` = 2).

### 2.4 „Sort Album By" / „Sort Folder By" (2. kérdés)

**A menü.** Az album két helyi menüje (`0x00732160`: `0x007322dd`
„Album::SortAlbumBy" → `0x00732338`; `0x007359e0`: `0x00735b93` →
`0x00735be5`) és a mappáé (`0x007319f0`: `0x00731c8f` →
`0x00731cea`) **ugyanazt** a `Sort::` almenüt építi (`0x007318a0`,
tábla `0x00d6ead8`): `ID_NAMESORT` = `0x9cd3`, `ID_DATESORT` = `0x9cd4`,
`ID_SIZESORT` = `0x9cd5`, `ID_REVERSESORT` = `0xa0d0`
(`0x00731905`, `0x0073194f`, `0x00731999`, `0x007319cd`).

**A kezelő.** A fő parancskezelő (`0x005cb990`) ugrótáblája
(`0x005cba5d`: `id − 0x9c42`, bájttábla `0x005cdb34`, címtábla
`0x005cd9fc`; `0x005cd4fa`: `id − 0xa02e`, `0x005cdfe0`/`0x005cdefc`):

| parancs | célcím | hívás | mód |
|---|---|---|---:|
| `0x9cd3` Név | `0x005cc0c0` | `0x005e5ce0(ui, 6, shift)` | 6 |
| `0x9cd4` Dátum | `0x005cc07d` | `0x005e5ce0(ui, 3, shift)` | 3 |
| `0x9cd5` Méret | `0x005cc103` | `0x005e5ce0(ui, 5, shift)` | 5 |
| `0xa0d0` Fordított | `0x005cd868` | `0x005e5ce0(ui, 12, 0)` | 12 |

A harmadik argumentum a **Shift** állapota (`GetKeyState(0x10)` felső bitje,
`0x005cc09d`–`0x005cc0aa`), de csak ha a `[0x00d67849]` bájt nem nulla;
különben 0. *(A `[0x00d67849]` jelentése NINCS MEG; a megszerzés útja: a
bájt íróinak pásztázása.)*

**Az alkalmazó: `0x005e5ce0`.**

1. Az aktuális nézet album-sorindexe `[[ui+0xeac]+0x3c0]`; a `CSlice`-t
   `0x004133e0` építi, `0x004b0190` tölti (`IThumbDB+0x2c`, ld. 2.1).
2. **Zárja a `CSlice`-t** (`0x005e5d53`–`0x005e5d72`, `+0x18`) — az
   ellenőrzőösszeg elmentődik.
3. Mód 12 → `0x00878720`: a lista **helyben megfordítva**.
   Különben `CThumbDB+0x554` = mód, `+0x558` = Shift (`0x005e5de2`,
   `0x005e5df7`), és `0x0049e1e0` **helyben összefésülve rendezi** a
   `slice+0x64` listát a `0x004efce0` hasonlítóval.
4. **Oldja a `CSlice`-t** (`0x005e5e75`–`0x005e5e98`, `+0x1c`) — a
   megváltozott összeg miatt jelöl (2.2).
5. Frissíti a nézetet: `0x0065b840(ui, 0, 0, 1)`.

⇒ **Nincs album-szintű rendezési beállítás.** Nincs ini-kulcs, db3-oszlop
vagy `Preferences`-kulcs, ami a módot hordozná — a mód csak a hasonlító
egyszeri paramétere. Ami megmarad, az a **rendezett lista** (a
`wordhash.dat`-ban), és az újraindítás után is az látszik.

**A kulcsok** (`0x004efce0` → `0x006b9b50`, ugrótábla `0x006b9db8`, csak
a 2–7. módra):

| mód | célcím | kulcs | egyenlőségnél |
|---:|---|---|---|
| 3 Dátum | `0x006b9be0` | a `thumbindex` rekord **1. FILETIME-ja** (`+4`/`+8`, a kép metaadat-dátuma, `pmp-database.md` 10.3) | a név-összevetés (`0x006b9bf2` → `0x006b9c28`) |
| 5 Méret | `0x006b9b69` | fájlméret (`+0x14`) | nincs: `a < b` → −1, különben +1 |
| 6 Név | `0x006b9c28` | a rekord neve, **természetes összevetéssel**: a számjegy-sorozat számértékként (`0x006b9cdc`–`0x006b9d06`), az ASCII `A–Z` kisbetűsítve (`0x006b9d0f`–`0x006b9d1a`), a számjegy-sorozat minden nem-számjegy elé kerül (a nem-számjegy `c − 0x100`, előjel nélkül hasonlítva, `0x006b9d22`, `0x006b9d71`) | 0 lehet (azonos szöveg `0x006b9ca8`; az egyik a másik előtagja `0x006b9d86`–`0x006b9d8e`) |

Irány: a kisebb kerül előre (`0x0049e298`: negatív eredménynél csere) —
**növekvő**, dátumnál a legrégebbi elöl. Shift: `+0x558` = 1 →
a `0x004efd84`–`0x004efd9b` ág a −1-et +1-re, minden mást −1-re fordítja
(csökkenő).

### 2.5 A 11-es „prioritás" mód nem a kézi sorrend (1. kérdés)

A `0x0071c650` (a rács listaépítője, `CSelectionNode` vtábla 49. rés) a
nézet elemeinek rekordindexét (`[elem+0xb4]`) gyűjti a `[+0x36c]` listába
(a `[elem+0x5a]`/`[elem+0x5b]` jelzős elemeket kihagyva), és

- **0-s módban nem rendez** (`0x0071c8a1`–`0x0071c8a5`): a nézet a lista
  sorrendjében áll;
- 12-es módban fordított sorrendben gyűjt (`0x0071c689`), rendezés nélkül;
- minden más módban `0x0071f030`-cal rendez, amelynek két hasonlítója
  (`0x0071f220`, `0x0071f270`) csak a `CThumbDB`-t kéri el (`0x007184e0`)
  és a `0x004efce0`-at hívja. **Ebben a láncban nincs más kulcsforrás.** A
  `0x004efce0` a `CThumbDB+0x554` módra ágazik (`0x004efd6b`–`0x004efd77`):
  a 2–7. módon kívül **állandó −1**, tehát a 8. és a 11. mód itt nem ad
  értelmes sorrendet.

A rács módja a konstruktorban **0** (`0x00714b95`, `CSelectionNode`
ktor `0x00714990`); a `CAlbumSelectionNode` ktor (`0x0077fd80`) nem írja
felül. A beállító (`0x0071c4f0`) csak virtuálisan érhető el (közvetlen
hívása a teljes `.text`-ben 0); a `[vtábla+0xc0]` virtuális hívások
pásztázása (38 hívóhely) állandó argumentumot csak `0xc`-vel talált
(`0x0061397a`, `0x006170b9`, `0x006183c2`, `0x006218b1` — Film;
`0x00831308`, `0x00831fe8` — kollázs). A `CThumbDB+0x554` íróinak
pásztázása (14 találat): a menü (`0x005e5de2`, 3/5/6), állandó 3
(`0x0048aeed`, `0x0055fb94`, `0x005e9004`), 0 az inicializáláskor
(`0x004e459e`) és a beállító (`0x0071c525`); 11-et egyik sem ír.

⇒ **A kézi sorrend a 0-s mód + a tárolt lista sorrendje; a 11-es mód
kulcsa nem kell hozzá.** Hogy a 11-es módot egyáltalán beállítja-e valami,
az hat, regiszter-argumentumú `[vtábla+0xc0]` hívóhelyen múlik
(`0x007b235d`, `0x008de46a`, `0x0094fbd8`, `0x0094fc58`, `0x00972884`,
`0x00ab903d`; az osztályuk NINCS MEG) — a sorrend tárolásának kérdését ez
nem érinti.

### 2.6 Mérés: a `wordhash.dat` formátuma és a tárolt listák

**Formátum** (az olvasó ellenőrzéseivel egyezően; három valódi fájlon
**0 bájt maradékkal** parszolva):

```
float32  verzió            = 1.6 (0x3FCCCCCD)
uint32   entitásszám       (= a thumbindex rekordszáma: 3 338 / 2 903 / 140 755)
uint32   poolszám          (1 / 1 / 28)
uint32   poolméret         = 0x10000  (az olvasó ellenőrzi: 0x004db78a)
uint32   az utolsó pool foglalt bájtjai
poolszám × poolméret bájt  — a szótár: NUL-végű szavak, folytonosan
uint32   szószám
szavanként: uint32 eltolás a szótárba · uint32 n · n × uint32 thumbindex-sorindex
```

**A mappák és albumok listái** (`albumdata_token` → szó; a token minden
nem üres soron megtalálható a szótárban):

| adatbázis | `]album:` lista | ebből **nem növekvő** sorindex-sorrend |
|---|---:|---:|
| kisebb (3 338 rekord) | 126 | 66 |
| nagy (140 755 rekord), mappák (kategória 2) | 2 063 | 915 |
| nagy, egyéb kategóriák | 290 | 91 |

A nem növekvő lista önmagában nem bizonyít kézi átrendezést (az új rekord
felszabadult indexet is kaphat), de azt igen, hogy **a tárolt sorrend nem
normalizált**: a fájl a listát úgy őrzi, ahogy a memóriában állt.

**A #1557 mappája** (`research/testdata/1557-masolat-mentese/db3-utana`,
a négy kép a 2899–2902. sor, a `thumbindex.db`-ben névsorrendben):

| | sorrend |
|---|---|
| a `wordhash.dat` listája | **2899, 2902, 2901, 2900** |
| név / sorindex | 2899, 2900, 2901, 2902 |
| 1. FILETIME | mind a négy egyenlő (`2026-07-16T18:04:11`) |
| 2. FILETIME | 2899, 2900, 2901, 2902 |
| méret | 2900, 2899, 2902, 2901 |

Egyik rendezési kulcs és annak fordítottja sem adja ki a tárolt sorrendet —
ez **tárolt, nem számolt** sorrend. *(Hogy pontosan melyik művelet hozta
létre — a #1557 „másolat mentése" vagy a #1645-ben leírt húzás —, abból az
egy pillanatképből nem dönthető el: „előtte" állapot nincs, ld.
`pmp-database.md`, a #4591 helyesbítése.)*

---

## 3. Eredeti / PicasaPy ma

| | eredeti (mérve) | PicasaPy ma |
|---|---|---|
| a sorrend tárolása | mappánként és albumonként egy lista a `wordhash.dat`-ban (2.1) | mappán belül: `.picasa.ini` `priority=` (ADR-014, `ini/priority.py`) — az ADR premisszája az `albums_0.db` volt, ami megdőlt; az ini-ben tartás mint SAJÁT döntés áll (az ADR-014 ennek megfelelően kiegészítve); albumra: **nincs** — a döntés: `albumorder=` a kép szakaszában (ADR-016, 4.3) |
| a mappa „Sort Folder By" | **egyszeri** átrendezés a mappa saját listáján, mappánként (2.4) | **tartós, globális nézet-mód** (`view/folderPhotoSort` + `…Reverse`, QSettings, `folder_photo_sort_controller.py:68`), minden mappára egyszerre; öt szempont (Dátum, Név, Méret + saját: Szín, Kézi sorrend; `FolderContextMenu.qml:137–239`) |
| az album „Sort Album By" | ugyanaz az almenü és kezelő, mint a mappáé (2.4) | **kész (#4599):** négy tételes almenü (`AlbumContextMenu.qml`), egyszeri átrendezés (`PhotoOpsController.sortAlbum`, `index/album_sort.py`) |
| az album képeinek sorrendje | a tárolt lista | **kész (#4599):** `album_photos` hely szerint rendez (`albumorder=`, `ini/album_order.py`); hely nélkül a régi `f.path, p.name` |
| kézi húzás albumban | eltávolít + beszúr a listában (2.3) | albumra nincs |
| a név-összevetés | természetes (számjegy-sorozat számként, ASCII kisbetűsítve; 2.4) | `name.casefold()` (`photo_sort.py:199`) — nem természetes |
| az átvétel (`pmpimport/`) | — | a `wordhash.dat`-ot nem olvassa; a kézi sorrend ma elvész |

---

## 4. A megvalósítandó viselkedés

### 4.1 #4599 — az album „Sort Album By" almenüje

**Kész, ha:**

- [x] az album helyi menüjében a „Sort Album By ▸" almenü él, és
      **ugyanaz a négy tétel** áll benne, mint az eredeti `Sort::`
      almenüben: Dátum · Név · Méret · Fordított sorrend (`0x007318a0`);
- [x] egy tétel kiválasztása az album képeinek **tárolt sorrendjét egyszer
      átrendezi** — nem kapcsol be tartós nézet-módot; utána a rács a
      tárolt sorrendet mutatja, és egy későbbi kézi húzás ebből indul;
- [x] a kulcsok a 2.4 táblája szerint: Dátum = a kép metaadat-dátuma
      (`taken_at`, az ottani felülírással együtt), egyenlőségnél név; Név =
      természetes összevetés (számjegy-sorozat számértékként, ASCII
      kisbetűsítve, számjegy-sorozat a betűk előtt); Méret = fájlméret;
      mindhárom **növekvő**;
- [x] Shift-tel kiválasztva a három kulcs **csökkenő** irányban rendez;
      a „Fordított sorrend" a tárolt sorrendet megfordítja (Shift nélkül
      is, kulcs nélkül);
- [x] a rendezés eredménye a tag képek **saját szakaszába**, az
      `albumorder=` kulcsba íródik (ADR-016, 4.3): minden tag új helyet kap
      (`1.0 … n`), mappánként EGY `update_document`-tel, kizárólag az `ini/`
      API-n át; a rendezési mód sehova nem íródik;
- [x] a sorrend **újraindítás és index-újraépítés után is megmarad** — az
      index a helyet csak gyorsítótárazza (a szinkron a kulcsból tölti), és
      az `album_photos` hely szerint rendez: hely nélküliek a végén, utána
      mappa útvonala, fájlnév;
- [x] **csak az érintett album** sorrendje változik: a kép más albumokhoz
      tartozó párjai, a `priority=` (mappa-sorrend) és a szakasz minden más
      sora bájtra változatlan;
- [x] **több mappára szóró album**: a rendezés a tagokat mappákon át
      összefésülve rendezi, és mindegyik érintett mappa ini-jébe ír; ha egy
      mappa írása bukik, a hiba hangos (megnevezi a mappát), a művelet
      megismételhető;
- [x] egy hely nélküli album sorrendje **pontosan a mai** (meglévő album a
      bevezetéstől nem változik), és a hely nélküli új tag a végére kerül;
- [x] a kép kivétele az albumból (`without_album`) és az album törlése
      (`without_album_everywhere`) az `albumorder=` párt is kiveszi,
      ugyanabban az írásban; az elárvult vagy romlott pár olvasáskor
      kimarad, nem dob;
- [x] a kulcs a kódban a saját-funkció jelölővel áll (a megvalósításkor, a jegyzék-tétellel együtt), és bekerül a
      `vedett-sajat-funkciok.md` jegyzékébe; a menütételek kék jelölést NEM
      kapnak (az eredeti funkció, csak a tárolás saját);
- [x] az ADR-016 `## Kötés` szakaszában a `Megvalósítja` és az `Őrzi` a
      tényleges modult és tesztet nevezi meg;
- [x] kattintásos teszt: a menütételre KATTINT (nem a metódust hívja),
      majd a rács sorrendjét, a lemezen lévő `.picasa.ini`-k `albumorder=`
      sorait és egy újranyitott index sorrendjét is nézi, köztük egy két
      mappára szóró albumon;
- [x] a szomszédos tételek (a többi helyi menüpont, a mappa saját
      „Sort Folder By" almenüje) regresszió-ellenőrzése lefut.

### 4.2 Az átvétel (a kézi sorrend tartós, tehát átvehető)

**Kész, ha:**

- [ ] a `pmpimport` beolvassa a `wordhash.dat`-ot a 2.6 formátuma szerint
      (a poolméretet és a 0 maradékot ellenőrizve; hibás fájlnál
      hangos hiba, nem csendes üres eredmény);
- [ ] minden `albumdata` sorra a `token` szavának listáját a
      `thumbindex` sorindexein át fájlútvonalakra képezi, a sorrendet
      megtartva; a lista nem létező vagy nem fájl típusú indexét kihagyja,
      és a kihagyottakat a jelentés számolja;
- [ ] **mappánál** (kategória 2) a sorrendet a PicasaPy kézi sorrendjeként
      veszi át (ma: `priority=`, ADR-014), és csak ha a mappában még nincs
      kézi sorrend (az „A" szabály: meglévőt nem ír felül);
- [ ] **albumnál** (kategória 0) a sorrendet a tag képek `albumorder=`
      kulcsába veszi át (ADR-016, 4.3; helyek `1.0 … n` a lista sorrendjében),
      és csak ha az album egyetlen tagja sem hordoz még helyet (az „A”
      szabály);
- [ ] teszt **szintetikus `wordhash.dat`-tal**: egy mappa nem növekvő
      listával → az átvett sorrend egyezik; egy üres token → kihagyva;
      egy csonka fájl → hiba.

### 4.3 Döntés: az album sorrendje a kép saját szakaszában, `albumorder=` (ADR-016)

**Eldöntve** (2026-10-12): `docs/decisions/album-sorrend-a-kep-szakaszaban.md`
(ADR-016). Röviden:

- **Hol:** minden tag kép a **saját** szakaszában, az `albums=` mellett,
  egyetlen `albumorder=` kulcsban hordozza a helyét, tagságonként egy
  `<token>:<hely>` párral, pl.
  `albumorder=604c294a68b0de9cc9222c4714f289d5:3.0`. A hely tizedes szám,
  pont tizedesjellel, mindig tizedes alakban.
- **A tagságot továbbra is az `albums=` adja**; az `albumorder=` csak
  sorrend. Az `albums=`-ben nem szereplő tokenű pár figyelmen kívül marad.
- **Az album sorrendje:** a tagok helye szerint növekvő; a hely nélküliek a
  végén; egyenlőségnél mappa útvonala, majd fájlnév. Hely nélküli albumnál
  ez pontosan a mai `ORDER BY f.path, p.name` — meglévő album nem változik.
- **A több mappára szóró album** tagjai a saját mappájuk ini-jében tartják a
  helyüket, egy közös számtérben, tehát a mappák képei összefésülhetők.
- **Átnevezés, áthelyezés:** a kulcs a szakasszal együtt mozog
  (`fileops/rename.py`, `fileops/move.py`), új teendő nincs.
- **A mappa sorrendje** külön marad (`priority=`, ADR-014): az eredetiben is
  két független lista.
- **Miért nem az album-szakasz vagy mellékfájl:** az `[.album:<token>]`
  szakasz mappánként megismétlődik (szétcsúszó példányok, mappákon átnyúló
  írás), és a Picasa a saját album-adatbázisából írja; a mellékfájl az
  igazságforrás-elvet sérti, és a Picasa fájlműveleteit nem követi.
- **Nyitott (nem mérve):** megőrzi-e az eredeti az ismeretlen képszakasz-
  kulcsot, amikor ugyanabba a szakaszba ír (NY1), és elviseli-e
  mellékhatás nélkül (NY2) — ugyanaz a kockázat, amit a `priority=` az
  ADR-014 óta hordoz. Kedvezőtlen NY1 esetén csak a sorrend vész el (a képek
  a végére esnek); kedvezőtlen NY2 esetén a két kulcs együtt költözik
  mellékfájlba. A mérés útja az ADR-ben; ebben a körben nem indult.

---

## 5. Élő megfigyeléssel megerősíthető pont (Colab-végrehajtó — NEM indítva)

A bináris lánc teljes; a viselkedést egy élő futás **megerősítheti**:
az átrendezés túléli-e a bezárást és az újraindítást.

⚠️ A végrehajtó v3-as lépései között **nincs húzás** és nincs
módosítóbillentyűs kattintás, a kimenetek között **nincs `db3`**. A húzás
mérése ezért új lépéstípust (`huz: [x1, y1, x2, y2]`) és `db3` kimenetet
kívánna — ezt a tulajdonos veszi fel a Colabon. A **„Fordított sorrend"**
viszont menüből kattintható:

```json
{"v": 3, "tipus": "ui_capture",
 "cel": "A Mappa > Sort Folder By > Reverse order egyszeri, tartós átrendezés-e (újraindítás után is fordított-e a sorrend).",
 "indulas": "friss",
 "lepesek": [
   {"picasa": "indit"}, {"var": 10},
   {"kattint": ["<a C:\\PicasaTeszt mappa a bal hasábban>"]}, {"var": 2},
   {"kattint": ["<a Folder menü>"]}, {"var": 1},
   {"kattint": ["<Sort Folder By>"]}, {"var": 1},
   {"kattint": ["<Reverse order>"]}, {"var": 3},
   {"picasa": "leallit"}, {"var": 5},
   {"picasa": "indit"}, {"var": 10},
   {"kattint": ["<a C:\\PicasaTeszt mappa>"]}, {"var": 3}
 ],
 "kimenet": ["kepernyokep", "allapot"], "keret": {"perc": 15}}
```

- A koordinátákat a felmérő (`colab_felmero.py`) egy előző futása adja;
  a fenti `<…>` helyek kitöltés nélkül nem adhatók fel.
- **Feltétel:** a `picasa leallit` rendes bezárás legyen (nem
  folyamatölés), különben a `wordhash.dat` nem íródik ki, és a mérés
  hamis negatívot ad.
- **Elfogadás:** az újraindítás utáni képernyőkép bélyegkép-sorrendje az
  átrendezés utánival egyezik, és az átrendezés előttinek a fordítottja.

---

## 6. Bizonyítottsági fok

- **Megerősített** (utasításszint): a hordozó (`CSlice` → `CIndexer` szó
  listája, 2.1), a perzisztálás jelölése (2.2), a menü → mód → egyszeri
  rendezés lánca és a kulcsok (2.4), a 0-s mód rendezésmentessége (2.5).
- **Megerősített** (mérés): a `wordhash.dat` formátuma (3 fájl, 0 bájt
  maradék), a listák nem normalizált sorrendje, a #1557 mappájának tárolt,
  egyik kulccsal sem kiadható sorrendje (2.6).
- **Kódszintű**: hogy a rács elemlistája a `CSlice` listájának sorrendjében
  épül — a 2.3 húzás a pozíciót közvetlenül a listába írja, ami ezzel
  egyezik; élőben a 5. pont futása erősíti meg.

## 7. Nyitott kérdések mérlege

`2 nyílt · 3 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| hol tárolódik a kézi (húzott) sorrend | **LEZÁRVA** — a `]album:<token>` szó listája a `wordhash.dat`-ban (2.1, 2.3) |
| mit állít a „Sort Album By", és megmarad-e | **LEZÁRVA** — egyszeri átrendezés (mód 6/3/5, Shift = csökkenő, 12 = megfordítás); a lista marad meg, mód nem tárolódik (2.4) |
| a 11-es mód kulcsa | **LEZÁRVA** a kérdés szempontjából — a kézi sorrendhez nem kell kulcs (2.5) |
| a `[0x00d67849]` (a Shift-figyelés feltétele) jelentése | **NYITOTT** — út: a bájt íróinak pásztázása |
| ki állítja a rács 11-es módját (ha valami) | **NYITOTT** — út: a hat regiszter-argumentumú `[vtábla+0xc0]` hívóhely osztályának azonosítása (2.5) |
