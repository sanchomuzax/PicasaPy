# A tartalom-kulcs (`originfast`) — MEGFEJTVE ÉS IGAZOLVA

*Picasa 3.9.141.259, mérve és **valódi adaton ellenőrizve** 2026-08-26.*

> ✅ **10/10 bitpontos egyezés** tíz valódi fényképen, a felhasználó saját
> `db3` adatbázisának `imagedata_originfast.pmp` oszlopával szemben.

---

## 1. Az algoritmus

```
h = CreateFileA(útvonal, GENERIC_READ, FILE_SHARE_READ, NULL,
                OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL)
méret = GetFileSizeEx(h)                 ; ha 0 → hiba (-1)

FEJ  = min(méret, 16834)                                  ; 0x41C2
FAROK = (méret > 33668) ? 16834 : méret − FEJ             ; 0x8384

puffer = uint32_le(méret & 0xFFFFFFFF)                    ; ⇐ a MÉRET a puffer ELEJÉN
       ‖ a fájl első FEJ bájtja
       ‖ a fájl utolsó FAROK bájtja

kulcs64 = MD5(puffer) első 8 bájtja, kis-endián uint64-ként
```

**Figyeld meg:** ha `méret ≤ 33668`, akkor `FEJ + FAROK = méret`, azaz a
**teljes fájl** kerül a pufferbe, átfedés nélkül.

---

## 2. Bizonyíték

### 2.1 A kód

| lépés | cím |
|---|---|
| `CreateFileA` | `0x00a4d243` (`[0xd69520]`), zászlók: `0x80000000`, `1`, `3`, `0x80` |
| `GetFileSizeEx` | `0x00a4d2a4` (`[0xc4048c]`) |
| üres fájl → `-1` | `0x00a4d2c7`–`0x00a4d2d6` |
| **FEJ = min(méret, `0x41C2`)** | `0x00a4d2ef  cmp ecx, 0x41c2` |
| **FAROK: `0x8384` a küszöb** | `0x00a4d30c  cmp ecx, 0x8384` |
| puffer = `FEJ + FAROK + 4` | `0x00a4d32c  lea edi, [esi+ebx+4]` |
| **a méret a puffer elejére** | `0x00a4d339`–`0x00a4d348` |
| `ReadFile` (fej) | `0x00a4d35d` (`[0xc4042c]`) |
| `SetFilePointerEx` (farok elé) | `0x00a4d3aa` (`0x99dd90`) |
| `ReadFile` (farok) | `0x00a4d3c5` |
| a hash hívása | `0x00a4d3f8  call 0xab3640` |
| forrásfájl | `.\yt\ytIO.cpp` (`0x00a4d266`), sor `0x1a1` = **417** |

### 2.2 Hogy MD5

A `0x00ab3640` (104 b) a négy szabványos MD5-kezdőállandót tölti be:

```
0x00ab3667  mov dword [esp+0xc],  0x67452301
0x00ab366f  mov dword [esp+0x10], 0xefcdab89
0x00ab3677  mov dword [esp+0x14], 0x98badcfe
0x00ab367f  mov dword [esp+0x18], 0x10325476
```

majd `0xab36f0` (Update) és `0xab37b0` (Final — a `0x80`-as
kitöltőbájt `0x00ab37c6`-nál).

### 2.3 Hogy az első 8 bájt

A hívó `0x00513730` a lezárás után **két dwordöt** vesz át:

```
0x00513794  mov ecx, [esp+0x10]     ; digest dword 0
0x00513798  mov eax, [esp+0x14]     ; digest dword 1
0x005137a4  mov [esi],   edx        ; ⇒ kulcs alsó 32 bit
0x005137a6  mov [esi+4], eax        ; ⇒ kulcs felső 32 bit
```

A hívó **gyorstáraz is**: ha `[ebp+0x10]|[ebp+0x14]` már nem nulla, ki sem
számolja újra (`0x00513741`).

### 2.4 ✅ A mérés — 10/10

A `research/testdata/Picasa2/db3` valódi adatbázisából:

- **`imagedata_originfast.pmp`** — PMP típus **`0x04` (u64)**, 140 755 sor;
- a sorindexhez a nevet a **`thumbindex.db`** adja;
- a windowsos útvonalak leképezése:
  `C:\Users\Sancho\Synology\My Pictures\` → `/mnt/photo/`.

Tíz elérhető fájlon a fenti algoritmus **mind a tízszer bitre azonos**
értéket adott a tárolttal (169 KB-tól 1,88 MB-ig, JPG és PNG vegyesen).

**Független újraellenőrzés (#1481 megvalósításakor, 2026-08-26):** ugyanez a
menet tizenkét elérhető fájlon **12/12** bitpontos egyezést adott, a
`picasapy.dedup.fastkey.picasa_fast_key` mai megvalósításától függetlenül
újraírt referencia-kóddal.

---

## 3. Amit KIZÁRTAM — három téves jelölt

| jelölt | miért nem |
|---|---|
| **`onlinechecksum`** | a korpuszban mind a **380** érték pontosan **8 hexa jegy**; a PMP-ben a típusa **`0x01` (u32)**. Egy 64 bites kulcsnál a felső dword 380-ból 380-szor nulla lenne — kizárt. **Ez 32 bites, más mennyiség.** |
| **`originhash`** (ini-kulcs) | 32 hexa jegy = teljes MD5, de **nyolc bemenet-változatot** próbáltam négy valódi fájlon (teljes fájl · fej+farok · méret32/64 elöl/hátul · nagy-endián · csak fej) — **0/32 találat**. Nem ez a függvény írja. ⭐ **2026-09-07 (#791) — a negatívum MAGYARÁZATA megvan: az `originhash` NEM egy 32 jegyű digest, hanem KÉT 16 jegyű szám összefűzése** — az első fele épp az `originfast`, a második az `originslow`. Ezért bukott mind a nyolc egy-digestes jelölt. Ld. „Az `originhash` — a két kulcs SZÖVEGES PÁRJA” lentebb. |
| **`imagedata_backuphash`** | PMP típus **`0x05` (u16)** — 16 bit, nem lehet tartalom-kulcs. |

---

## 4. Eredeti / nálunk / teendő

| eredeti | nálunk (#1481 után) | állapot |
|---|---|---|
| **fej+farok MD5**, 4+16834+16834 bájt olvasás | `dedup/fastkey.py` — `picasa_fast_key()` | ✅ átvéve |
| a méret a hash **bemenetének része** | ugyanúgy, `uint32_le` a puffer elején | ✅ átvéve |
| a kulcs MONDJA KI a másodpéldányságot | nálunk csak **előszűrő**, ld. lent | ⚠️ szándékos eltérés |
| 64 bites kulcs, `u64` oszlopban | nincs ilyen oszlopunk, futásidőben számol | ⬜ külön jegy (indexséma) |
| gyorstárazás (ha megvan, nem számol) | csak körön belül (`duplicate_paths`) | ⬜ külön jegy (indexséma) |

### A (b) döntés — a kulcs nálunk előszűrő, nem ítélet

A `dedup/exact.py` három lépcsőt futtat: **méret → gyors kulcs → teljes
SHA-256**. A kulcs csak *kizárni* tud (eltérő kulcs = biztosan eltérő
tartalom); a másodpéldányságot továbbra is a teljes hash mondja ki.

**Miért nem vettük át a gyengítést:** a rétegre két visszafordíthatatlan
funkció épül — a Duplikátum-kezelő törölni ajánl (#287), az importálás pedig
szótlanul kihagyja a jelöltet (#441). Egy 64 bites, csak a fájl két végét
néző kulcs téves egyezése ott egy elveszett fényképet jelentene. Az eredeti
Picasa ezt a kockázatot vállalta; nálunk a kulcs ára (~33 KB olvasás) így is
töredéke a teljes olvasásnak, a pontosság viszont megmarad.

**Miért számít:** egy 5 MB-os fényképnél az eredeti **33 KB-ot** olvas, mi
**5 MB-ot**. Hálózati megosztáson (a felhasználó gyűjteménye NAS-on van) ez
**150-szeres** különbség.

⚠️ **De: a fej+farok kulcs gyengébb.** Két fájl, amely csak a közepén tér
el és azonos méretű, **ütközik**. Az eredeti ezt elfogadja; nekünk el kell
döntenünk, hogy átvesszük-e a gyengítést, vagy a gyors kulcsot csak
**előszűrőnek** használjuk a teljes összehasonlítás előtt. **Ez tervezői
döntés, nem másolandó tény.**

---

## 5. Bizonyítottsági fok

**Megerősített, méréssel igazolva**: az egész algoritmus (10/10 valódi
fájlon). **Megerősített kódból**: a hívási lánc, az MD5, a csonkolás, a
gyorstárazás. **Elvetve, méréssel**: mindhárom téves jelölt a 3. pontban.

## 6. Nyitott kérdések mérlege

| kérdés | állapot |
|---|---|
| Mi a másodpéldány-kulcs algoritmusa? | **LEZÁRVA** — 1–2. szakasz, 10/10 |
| Melyik oszlop tárolja? | **LEZÁRVA** — `imagedata_originfast` (u64) |
| Az `onlinechecksum` a párja? | **LEZÁRVA — NEM** (3.) |
| Az `originhash` a párja? | **LEZÁRVA — NEM egy digest**, 0/32 (3.) — de ⭐ **2026-09-07 (#791): az `originhash` a két kulcs SZÖVEGES ÖSSZEFŰZÉSE** (`fmt16(originfast) + fmt16(originslow)`), 16/16 valódi fájlon, 0 részleges egyezéssel |
| **Mi az `imagedata_originslow`?** | **LEZÁRVA (2026-09-05, #1482)** — `MD5(teljes fájl)[0:8]` kis-endián, **18/18** valódi fájlon; a korábbi „0/4"/„0/8" olyan sorokon mért, ahol a fájl azóta megváltozott (kontroll: ott az `originfast` sem egyezik). Szerepe: a gyors kulcs **ütközésfeloldója** — 28,5× dúsulás. |

| **Mi az ini `originhash` kulcs?** | **LEZÁRVA (2026-09-07, #791)** — `fmt16(originfast) + fmt16(originslow)`, ld. lentebb |
| Melyik fájl bájtjait rögzíti az `originhash` a mentés pillanatában? | **NYITVA** — a lemezen lévő aktuálisét vagy az eredetiét/importforrásét; a 60-as mintában 44 sor nem egyezett a MAI fájllal, és ezt sem az mtime, sem szerkesztési kulcs jelenléte nem magyarázta |

```
Nyitott kérdések: 1 nyílt · 6 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

---

## Az `originhash` — a két kulcs SZÖVEGES PÁRJA (2026-09-07, #791)

A `.picasa.ini` `originhash` kulcsa **nem** önálló algoritmus: az
`originfast` és az `originslow` **szöveggé alakított, összefűzött**
alakja. Ezért bukott korábban mind a nyolc egy-digestes jelölt (fentebb,
`0/32`) — a 32 jegy nem egy hash, hanem **kétszer tizenhat**.

```
originhash = "%016I64x" % originfast  ‖  "%016I64x" % originslow

originfast = u64_le( MD5(uint32_le(méret) ‖ fájl[:16834] ‖ fájl[-16834:])[:8] )
originslow = u64_le( MD5(teljes fájl)[:8] )
```

Kisbetűs hexa, előtag nélkül, mindkét fél nulla-feltöltéssel pontosan 16
jegy.

### Bizonyíték a binárisból

| lépés | cím | mit mond |
|---|---|---|
| kiírás | `0x007d5e74` | `push 0xcb9254` (= `"originhash"`); az érték a rekord `+0x90` mezője, és csak nem üres sztringre íródik ki (`0x007d5e2a`–`0x007d5e40`) |
| **szétszedő** | `0x00414b40` | `cmp eax, 0x20` — **pontosan 32 karaktert vár**; az első 16-ot és a `[eax+0x10]`-től a második 16-ot külön sztringbe másolja (`0x00414bab`, `0x00414bce`), majd mindkettőt `sscanf(s, "%I64x")`-szel olvassa (`0x0049fb50`, formátum `0xc82fcc`) |
| **összerakó** | `0x00414c50` | `sprintf(out, "%016I64x", v1)` + hozzáfűzés `"%016I64x", v2` — a formátum `0xc80ce4`, **kisbetűs**; a digest→hexa segéd (`0x00a4d420`) a `0xcd8f5c` = `"0123456789abcdef"` táblát használja |
| a két hasher | `0x00a4cd00` diszpécser → `0xa4d210` (fej+farok, #1481) és `0xa4ce40` (teljes fájl, #1482) | a bemenet a **fájl bájtjai** |

**Melyik fél melyik — három független jel:**

1. `0x0070e58b`: ha az **első** fél nulla, a kód újraszámoltatja — de a
   diszpécsert úgy hívja, hogy a lassú célt kinullázza (`0x0070e594`
   `xor edi, edi`), vagyis csak a *gyors* ágat futtatja ⇒ az első fél az
   `originfast`;
2. `0x005b0b0e`: az összerakót `push 0; push 0`-val hívja a **második**
   értékpárra ⇒ a második fél az elhagyható ⇒ `originslow`;
3. `0x004386b6`: közvetlenül a `0x004353a0` (az `originslow` egyetlen
   előállítója, #1482) után áll, és az 1. értékpár az a rekesz, amelynek
   címét a `0x4353a0` a *gyors* célnak adja.

### Mérés valódi fájlokon (2026-09-07)

A korpusz 1 787 `originhash=` sorából 60 véletlen, ma is elérhető fájl:

| eredmény | db |
|---|---:|
| **teljes (32/32) egyezés** | **16** |
| ebből az első fél (`originfast`) egyezett | 16 |
| ebből a második fél (`originslow`) egyezett | 16 |
| **részleges egyezés (csak az egyik fél)** | **0** |

A **nulla részleges egyezés** a döntő jel: ha a felosztás vagy a képlet
téves volna, a két fél egymástól függetlenül tévedne, tehát akadna olyan
sor, ahol az egyik egyezik, a másik nem. Egy sem akadt. A 44
nem-egyező sor ugyanaz a jelenség, amit a #1482 „mintahibaként"
dokumentált: a fájl tartalma az ini írása óta megváltozott — ott
**egyik** fél sem egyezik.

### ⛔ Ami NYITVA marad

> ⛳ **2026-09-08 (#2675) — A KÉRDÉS ÁTFOGALMAZVA.** A `.picasa.ini`-író
> **nem hashel**: a `[rekord+0x90]` mezőt másolja ki (`0x007d5e2a`).
> A helyes kérdés tehát: ki és mikor tölti fel azt a mezőt. Részletek és
> a hashelő lánc teljes kimérése: „Az `originhash` ÍRÁSI LÁNCA — a kiíró
> NEM hashel" szakasz a lap végén.

**Melyik fájl bájtjait rögzíti a mentés pillanatában?** A kulcsnév
(„origin") és az `origloc` szomszédsága az *eredetit* sugallja, de ez
nincs bizonyítva, és a 44 nem-egyező sort sem a fájl módosítási ideje,
sem szerkesztési kulcs (`filters=`/`redo=`/`crop=`) jelenléte nem
magyarázta. Amíg ez nem dől el, **az `originhash` írása nálunk nem
javítható** — ld. `picasa-ini-format.md`, „A mi `originhash`-ünk ALAKJA
sem egyezik".

**Negatív lelet:** az `"originhash"` sztring a 8,6 MB-os binárisban
**pontosan egyszer** fordul elő (`0xcb9254`), és csak a kiírás hivatkozik
rá (`0x7d5e75`) — a Picasa 3.7 tehát a `.picasa.ini`-ből **név szerint
nem olvassa vissza** ezt a kulcsot.

*Bizonyítottsági fok: megerősített* (diszasszemblátum + 16/16 mért
egyezés, 0 részleges).

---

## A MÁSOLAT ÖRÖKLI a forrás `originfast`-ját — mérve (2026-08-27)

A tartalomkulcsot eddig úgy írtuk le, hogy a fájl **saját** bájtjaiból számol
(10/10 igazolva). Ez igaz a beolvasott fájlokra, de **nem a Picasa által
készített másolatokra**.

### A mérés

A tulajdonos leadta az élő `db3`-at
(`research/testdata/1557-masolat-mentese/db3.zip`), egy mappával, amelyben egy
eredeti kép és **három** „Másolat mentése" kimenete van.

| index | méret | `originfast` |
|---|---|---|
| 2896 | 5120×3840 | `0x438f292cd28e7862` |
| 2897 | 5120×3840 | `0x30a3a5cac3a177bb` |
| 2898 | 0×0 | `0x0` |
| **2899** | **1600×1200** | **`0x08637e41c12b8eaa`** |
| **2900** | **1600×1200** | **`0x08637e41c12b8eaa`** |
| **2901** | **1600×1200** | **`0x08637e41c12b8eaa`** |
| **2902** | **1600×1200** | **`0x08637e41c12b8eaa`** |

A négy utolsó rekord mérete pontosan a mi négy fájlunké (a szomszédok
5120×3840-esek), és **mind a négy ugyanazt a `originfast`-ot viseli**.

Az az érték a **forrásfájlé**: a `chart_color__b050.jpg` saját bájtjaiból
számolva `0x08637e41c12b8eaa` — a képlet tehát a forrásra **változatlanul
érvényes**.

### Miért ez lelet

A három másolat bájtjai **nem** azonosak a forráséval:

| fájl | méret | eltérés a forrástól |
|---|---|---|
| `…-001.jpg` | 144 796 B | újrakódolás (átlag 0,08) |
| `…-002.jpg` | 228 288 B | **beégetett `autolight`** (átlag 5,21; a képpontok 99,9 %-a) |
| `…-003.jpg` | 227 898 B | ua. |

Saját bájtjaikból számolva **három különböző** MD5 jönne ki. Egyetlen közös
érték csak úgy lehetséges, ha a Picasa **átmásolja** a forrás értékét a
másolat rekordjába.

### A következmény

Az `originfast` neve pontos: **„origin"**, nem „content". A mező a
**származást** azonosítja, nem a fájl pillanatnyi tartalmát — ezért marad
azonos egy szerkesztett másolaton is. Ez az, ami lehetővé teszi, hogy a
Picasa a másolatot a forrásához kösse.

⚠️ **A 10/10-es igazolásunk NEM dőlt meg** — az beolvasott, nem származtatott
fájlokra vonatkozott, és azokra érvényes marad. A leírás egészül ki: a
képlet a fájl **első** felvételekor fut, származtatott másolatnál a forrás
értéke öröklődik.

*Bizonyítottsági fok: **megerősített** — valódi, élő Picasa-adatbázison mérve,
a méret-oszloppal függetlenül azonosított rekordokon.*

### Miért nem elég ezt „bevezetni” (mérve, 2026-09-01, #1648)

Az öröklés megvalósítása nem egyetlen értékadás, két külön okból.

**1. Nincs hova eltenni.** Az SQLite indexünk sémájában **nincs**
`originfast` oszlop — a kulcsot mindig menet közben számoljuk
(`dedup/exact.py`, `importsource.py`). Öröklésről csak akkor lehet szó,
ha a származtatott értéket egyáltalán TÁROLNI tudjuk; ez sémaváltozás, és
a sávtérkép szerint az `index/` csomag dolga.

**2. A kulcs nálunk MÁS célt szolgál.** Az eredeti a származás
nyilvántartására használja; nálunk két helyen **azonosságot** jelent:

| hívóhely | mit jelent ma a kulcs egyezése |
|---|---|
| `dedup/exact.py` | a két fájl **másodpéldány** |
| `importsource.py` | a kép **már a könyvtárban van**, ne importáljuk |

Ha a másolat örökölné a forrás kulcsát, a duplikátum-kereső egy
**beleégetett szerkesztésű** másolatot a forrása pontos másodpéldányának
jelentene — pedig a képpontok 99,9%-ában eltér. Az importálás pedig
kihagyná a másolatot, mint „már megvan”.

⇒ Az öröklés bevezetése **együtt jár** azzal, hogy a két hívóhely ne a
származás-kulcson döntsön azonosságról. Enélkül a hűség egy valódi,
felhasználónak látszó hibát okozna.

### ✅ Az öröklés MEGVAN — és a két akadály MEGKERÜLVE (2026-09-02, #1648)

Az előző szakasz két akadályt nevezett meg. Mindkettőt úgy oldottuk meg,
hogy közben a `dedup/` viselkedése **bitre változatlan** maradt.

**1. „Nincs hova eltenni" → önálló, útvonalra kulcsolt tábla.**
`index/origin.py`, `origin_keys(path TEXT PRIMARY KEY, origin_key INTEGER)`,
lustán létrehozva (`CREATE TABLE IF NOT EXISTS`), tehát meglévő indexen is
azonnal működik. **Miért nem a `photos` oszlopa:** a „Másolat mentése"
előbb írja ki a fájlt, mint ahogy a szinkron felveszi a fotó-rekordot — egy
`photos`-oszlop írása versenyhelyzetbe kerülne a saját szinkronunkkal (vagy
elveszne az érték, vagy a szinkron írná felül). Az útvonalra kulcsolt tábla
**bármikor írható**, sorrendtől függetlenül.

⚠️ Ez az adat a `photo_hashes`-szel és a `photo_colors`-szal ellentétben
**nem származtatott**: a fájlból nem számolható újra, mert épp azt tartja
nyilván, amit a tartalom NEM árul el. Gyorsítótárként soha nem dobható el.

**2. „A kulcs nálunk mást jelent" → szétválasztott fogalmak.**

| kérdés | ki válaszol | mit használ |
|---|---|---|
| tartalmi azonosság (másodpéldány, importálás) | `dedup/exact.py`, `importsource.py` | a **számolt** `picasa_fast_key` — VÁLTOZATLAN |
| származás (melyik fájlból lett) | `index/origin.py` `origin_key()` | az **örökölt** érték, ha van; egyébként a számolt |

Így a duplikátum-kereső **nem** jelenti a beégetett szerkesztésű másolatot
másodpéldánynak, és az importálás sem hagyja ki — az előző szakasz
figyelmeztetése tehát nem következett be. Az eredeti Picasa a két fogalmat
egyetlen mezőben keverte; nálunk kettő van, és a hűséget a származás-oldal
hordozza.

**A lánc:** `save_copy` → `SaveCopyResult.inherited_origin_key` (a forrás
kulcsa, a másolat kiírása után olvasva) → `app/save_controller.py`
`_orokit_szarmazas_kulcsokat` → `index.origin.inherit_origin_key`. A mag
lemez- és adatbázis-független marad: `save_copy` csak visszaad, nem tárol.

**Előjel-kezelés:** a kulcs előjel NÉLKÜLI 64 bites, az SQLite INTEGER
előjeles — a tárolás kettes komplemensben megy, ahogy a `photo_hashes`
dHash-oszlopánál. Ez nem elméleti szélsőérték: a mért kulcsok fele a felső
felébe esik (a #1648 mérésének `0x8637e41c12b8eaa` értéke is ilyen). Őrizve:
`tests/test_index_origin_1648.py::test_a_teljes_64_bites_tartomany_visszaolvashato`.

**A takarítás (#2038).** A mappa-szinkron
(`index/sync.py::_sync_folder` → `forget_origin_keys_outside`) kiveszi az
eltűnt fájlok sorát. Ez a **minden utat lefedő** pont: a fájl eltűnhet kukába
dobással, átnevezéssel vagy a felhasználó fájlkezelőjéből — a szinkron
mindegyiket itt látja meg, ezért a `fileops/` külön kezelése nem kell.

A törlés feltétele **kettős**: a név hiányozzon a most látott fájlnevek közül
**és** a fájl tényleg ne legyen a lemezen. Ez az adat ugyanis nem
újraszámolható, tehát egy átmeneti hiba miatt üres scan nem vihet el létező
fájlhoz tartozó sort.

A szűrés Pythonban megy, nem SQL `LIKE`-kal: az útvonalban előforduló `%` és
`_` a `LIKE` joker-karakterei, tehát egy „100%_nyar" nevű mappa takarítása
idegen sorokat is elvinne.

**Mappaszintű takarítás szándékosan NINCS.** Egy lecsatolt hálózati megosztás
ugyanúgy „eltűntnek" látszik, mint egy véglegesen törölt mappa, és ezt az
adatot nem tudnánk visszaállítani. Ha a mappa visszatér, az öröklés helyes
marad; ha nem tér vissza, a bent maradt sorok tétlenek.

**Ami NYITOTT marad:** ha az eltűnt fájl helyére a KÖVETKEZŐ szinkron előtt új
fájl kerül ugyanazzal a névvel, a régi sor megmarad — a tábla ma nem tárol se
méretet, se mtime-ot, amiből a csere látszana. Külön jegy: **#2099**.

---

## A PMP-oszloptábla regisztrációja — a két tartalomkulcs HELYE és TÍPUSA (2026-09-04, #1482)

A `0x004127c0` regisztrálja a `imagedata_*` oszlopokat. A minta:
`push "<név>"`, majd `lea eax, [esi + OFFSZET]; call <regisztráló>` — **a
név a KÖVETKEZŐ regisztrációhoz tartozik**, nem az előzőhöz. (Ez a
sorrend félreolvasható; a #1482 jegye emiatt írt téves tagoffszetet.)

| név | tag | regisztráló | típus |
|---|---|---|---|
| `edited` | `+0x918` | `0x00496020` | bájt |
| `revertable` | `+0x978` | `0x00496020` | bájt |
| **`originslow`** | **`+0x9d8`** | `0x00495360` | **u64** |
| **`originfast`** | **`+0xa40`** | `0x00495360` | **u64** |
| `uid64` | `+0xaa8` | `0x00495360` | u64 |
| `aliasparents` | `+0xb10` | `0x00494c50` | *(más)* |

**A két regisztráló két oszlop-TÍPUS**, és a különbség a vtable **11.
résében** olvasható ki (a többi rés azonos):

| regisztráló | 11. rés | mit csinál |
|---|---|---|
| `0x00496020` | `0x00496180` (40 b) | `add eax, edx; movsx eax, byte ptr [eax]` ⇒ **1 bájt/elem** |
| `0x00495360` | `0x00495e90` (48 b) | `lea ecx, [eax + edx*8]`, majd `[ecx+4] XOR [ecx]` ⇒ **8 bájt/elem**, és 32 bites hasítást ad vissza |

⇒ **Az `originslow` és az `originfast` UGYANAZ az oszlop-osztály** — a
különbségük nem a tárolásban van, hanem az értéket előállító kódban.

### Mért NEGATÍV eredmény: tagoffszeten senki nem éri el őket

A bináris **összes** indexelt függvényét diszasszemblálva a `[reg + 0x9d8]`
és a `[reg + 0xa40]` alakra a lemez-/adatbázis-kódban **pontosan két**
találat van mindkettőre: a fenti regisztráló és a destruktor
(`0x00413020`, ugyanazt a takarítót hívja minden oszlop-tagra). A többi
találat más osztályok azonos offszete vagy veremcím.

⇒ **Az érték-írás az oszloplistán át megy**, nem literális tagoffszeten. Az
`originslow` képletét kereső kör ezért **ne** a tagra írókat keresse — az
az út bizonyítottan üres.

*(Az `originslow` és `originfast` sztringre is egyetlen hivatkozás van az
egész binárisban: ugyanez a regisztráló. Néven sem érhetők el.)*

## ✅ Az `originslow` MEGFEJTVE ÉS MEGMÉRVE — 18/18 (2026-09-05, #1482)

**A képlet:** `originslow = MD5(a TELJES fájl) első 8 bájtja, kis-endián.**
Nincs méret-előtag (ellentétben az `originfast`-tal), és 64 KB-os darabokban
streamel. A hasher: `0x00a4ce40` (421 b, `.\yt\ytIO.cpp`) — `CreateFileA`
`0x00a4ceb4`, 64 KB-os puffer `0x00a4cf0a`, `ReadFile`-ciklus `0x00a4cf49`,
`MD5Update` `0x00a4cf75`, `MD5Final` `0x00a4cfa8`.

**Bizonyítottsági fok: megerősített** — a kód kiolvasva ÉS **18 valódi
fényképen 18/18** reprodukálva a `db3` tárolt értékeivel szemben.

### ⛔ Miért mondta három korábbi kör, hogy „0/4" és „0/8"

Mert a mérés olyan sorokon futott, ahol **a fájl azóta megváltozott** — és
ezt senki nem ellenőrizte kontrollal. A kontroll a **saját `originfast`
mezőjük**: ha az sem egyezik, a fájl nem az, amit a Picasa indexelt.

| minta | `originfast` egyezik | `originslow` egyezik |
|---|---:|---:|
| **véletlen sorok** (bármilyen, `n = 25`) | **24/25 = 96%** | — (üres oszlop) |
| **`originslow`-os sorok** (véletlen, `n = 70`) | 1/70 | 1/70 |
| ugyanezen 70 sor **kereszttáblája** | `fast` OK & `slow` ELTÉR: **0** · `fast` ELTÉR & `slow` OK: **0** | |
| **`originslow`-os sorok, VÁLTOZATLAN fájllal** (`n = 18`, 900 sor átnézéséből) | 18/18 (szűrési feltétel) | **18/18** |

⇒ **Egyetlen ellenpélda sincs:** valahányszor a fájl változatlan, a
`MD5[0:8]` egyezik. A korábbi negatívumok a minta hibái voltak, nem a
képletéi. *(A `slow`-os soroknak mindössze **2 %-a** — 18 a 900-ból — mutat
változatlan fájlt; ezért volt olyan könnyű véletlenül csupa elavult sort
fogni.)*

**Módszertani tanulság:** egy „a képlet nem reprodukál" verdikt csak akkor
ér valamit, ha **ugyanazon a soron** egy már igazolt másik mennyiség
(itt: az `originfast`) egyezik. Enélkül nem a képletet mértük, hanem azt,
hogy a fájl azóta megváltozott-e.

### Ki állítja elő — a TELJES hívási lánc, kimerítően

| lépés | cím | megjegyzés |
|---|---|---|
| lassú hasher | `0x00a4ce40` | **egyetlen** hívója: a diszpécser |
| diszpécser | `0x00a4cd00` (113 b) | `eax` = a GYORS kulcs kimenő mutatója, **`edi` = a LASSÚ kulcsé**, `[esp+0x1c]` = az útvonal |
| a feltétel | `0x00a4cd3d` `test edi, edi` / `0x00a4cd44` `je` | **a lassú kulcs csak akkor számolódik, ha a hívó ad neki célt** |
| 1. hívó | `0x0070e080` | `0x0070e594` **`xor edi, edi`** ⇒ itt SOHA nem számolódik |
| 2. hívó | **`0x004353a0`** (2920 b) | `0x00435986` `mov edi, [esp+0x24]` — nem nulla ⇒ **ez az EGYETLEN előállító** |

A `0x004353a0`-nak **tíz** hívója van, és mind a tíz `lea ecx, [esp+N]`
alakkal, azaz **valódi verempuffert** ad át (`0x00438691`, `0x004563db`,
`0x0045cbdc`, `0x00464f05`, `0x00478336`, `0x0054114a`, `0x006bf6a7`,
`0x006ec3d1`, `0x007e4aac`, `0x0087f3d4`).

⛔ **Zsákutca, hogy ne járja újra senki:** a `0x00513730` **nem** ide
tartozik — az a **gyors** hashert (`0x00a4d210`) hívja közvetlenül, tehát
`originslow`-t nem tud előállítani. A jegy korábbi „a `0x00513730` hívói
felől" tanácsa ezért hibás irány volt.

### Mire jó — MÉRVE, nem következtetve

A `db3` (140 661 közös sor) alapján:

| a sor `originfast`-ja | `originslow` ki van töltve | üres | arány |
|---|---:|---:|---:|
| **osztott** (más sor is viseli) | **2 236** | 2 540 | **46,8 %** |
| egyedi | 2 116 | 126 510 | **1,65 %** |

⇒ **28,5-szeres dúsulás** az ütköző sorokon. A 2 316 duplikátum-csoportból
842-ben **minden** tag kap `originslow`-t, 446-ban csak egy részük, 1 028-ban
egy sem. A 4 352 nemnulla `originslow` **3 407 különböző** értéket vesz fel
(849 érték ismétlődik) — vagyis ott, ahol jelen van, **tovább is bont**.

**Az `originslow` tehát a gyors kulcs ütközésfeloldója.** Ez összecseng a
`#1648` mérésével: a másolat **örökli** a forrás `originfast`-ját, tehát a
másolatok szükségszerűen ütköznek — és épp őket kell egy valódi
tartalom-hash-sel megkülönböztetni. `originslow` sosem fordul elő
`originfast` nélkül (0 ilyen sor).

### Nálunk (mérve)

`src/picasapy/dedup/exact.py:35` — **SHA-256 a teljes fájlon**; a Picasa
`originslow`-jának megfelelő mennyiséget nem számoljuk, a `pmpimport` csak
olvassa az oszlopot. Ez **nem hiba**: a `.picasa.ini`/PMP round-triphez az
olvasás elég, írni nem írunk PMP-t.


## Az `originhash` ÍRÁSI LÁNCA — a kiíró NEM hashel (2026-09-08, #2675)

*206. kutatói kör.* A #2675 (és a lap „⛔ Ami NYITVA marad" szakasza) azt
kérdezi: **melyik fájl bájtjait rögzíti az `originhash` a mentés
pillanatában** — a most kiírt szerkesztett képét, vagy a szerkesztés
előtti eredetiét? A kör ezt a kérdést **átfogalmazza**, mert a
diszasszemblátum szerint rosszul volt feltéve.

### 1. ⭐ A `.picasa.ini`-író nem számol semmit — egy MEZŐT másol ki

A metaadat-író `FUN_007d55f0` (2681 b) **név szerint pontosan két
kulcsot** ír (a többi `push 0x00cb…` a benne lévő naplósorok szövege):

```
0x007d5e23  mov ecx, [esp + 0xadc]        ; a KÉP-REKORD (2. argumentum)
0x007d5e2a  mov eax, [ecx + 0x90]         ; ← az originhash SZTRING
0x007d5e32  je  0x007d5e8c                ; NULL        → a kulcs KIMARAD
0x007d5e3a  je  0x007d5e8c                ; nulla hossz → KIMARAD
0x007d5e40  je  0x007d5e8c                ; üres        → KIMARAD
0x007d5e46  lea ebp, [eax + 4]            ; a szöveg
0x007d5e74  push 0x00cb9254               ; "originhash"
0x007d5e7f  call [edx+8]                  ; az ini-író virtuális metódusa
```

és közvetlenül utána:

```
0x007d5f8a  cmp byte ptr [ebx + 0xf9], 0  ; kapu az 1. argumentum objektumán
0x007d5f91  je  0x007d604b                ; ha 0 → az origloc KIMARAD
0x007d5f9e  mov eax, [ecx + 4]            ; ← az origloc SZTRING (rekord +4)
0x007d5fde  push 0x00cb9260               ; "origloc"
```

⇒ **A kiírás pillanatában semmilyen hashelés nem történik.** A `+0x90`
mező tartalma korábban keletkezett; a kérdés tehát nem az, hogy a kiíró
mit hashel, hanem hogy **mikor és milyen útvonalból töltődik a
`[rekord+0x90]`**.

*A `FUN_007d55f0`-nak három hívója van (index-független `E8 rel32`
pásztázás): `0x007d9bb4`, `0x007d9dc0`, `0x007dba1e`.*

### 2. ⭐ A két kulcsot EGYETLEN burkoló állítja elő — és a lassú fél OPCIONÁLIS

`FUN_00a4cd00` (113 b):

```
eax  = a GYORS kulcs kimenete      (fej+farok, FUN_00a4d210, 0x00a4cd21)
[esp+0x18] = az ÚTVONAL
edi  = a LASSÚ kulcs kimenete      (teljes fájl, FUN_00a4ce40, 0x00a4cd4b)

0x00a4cd44  je 0x00a4cd68     ; ha edi == 0, a LASSÚ kulcs KI SEM SZÁMOLÓDIK
```

⇒ ez az egyetlen hely, ahol a **pár** (gyors + lassú) egyszerre
keletkezhet — márpedig az `originhash` pontosan ez a pár.

### 3. ⭐ A burkolónak KÉT hívója van, és az egyik csak a GYORS kulcsot kéri

Index-független `E8 rel32` pásztázás az egész `.text`-en:

| hívás | hol | `edi` (a lassú kimenet) |
|---|---|---|
| `0x0070e59a` | `FUN_0070e080` | **`0x0070e594 xor edi, edi`** ⇒ **csak a gyors kulcs** |
| `0x0043598d` | `FUN_004353a0` | argumentumból (`[esp+0x24]`) ⇒ lehet mindkettő |

⇒ **Az `originhash` párja KIZÁRÓLAG a `FUN_004353a0`-n át keletkezhet.**
*(A `0x0070e59a` a másodpéldány-/index-ág, ahol elég a gyors kulcs — ez
egyben megmagyarázza, miért látszik a gyors kulcs sokkal több helyen.)*

### 4. A `FUN_004353a0` ÁLTALÁNOS szolgáltatás — azt hasheli, amit kap

A hasholt útvonal a **saját argumentuma** (`0x004358f1
mov eax, [esp + 0xa58]`), nem a rekordból jön. Tíz hívója van
(index-független pásztázás), mindegyik azonosítva a sztringjeiről:

| hívás | függvény | miről ismerszik meg |
|---|---|---|
| `0x00438691` | `FUN_00437cf0` | `caption` |
| `0x004563db` | `FUN_00455ff0` | `keywords` |
| `0x0045cbdc` | `FUN_0045c870` | `Picasa`, `%016I64x` |
| `0x00464f05` | `FUN_00464990` | `filters`, `.\yt\ytIO.cpp` |
| `0x00478336` | `FUN_00477ff0` | `geotag`, `%lf,%lf` |
| `0x0054114a` | `FUN_0053fe30` | `runtime\filterdesc.xml` |
| `0x006bf6a7` | `FUN_006befa0` | `Preferences`, `ShowUnixPaths` |
| `0x006ec3d1` | `FUN_006ec280` | `%016I64x`, `%I64x` |
| `0x007e4aac` | `FUN_007e3210` | **`CPropertiesDlg::*`** — a Tulajdonságok párbeszéd |
| `0x0087f3d4` | `FUN_0087f220` | `runtime\missing.jpg` |

⇒ **A hashelő láncban semmi nem dönti el az „eredeti vagy szerkesztett"
kérdést** — azt kizárólag a **hívó által átadott útvonal** dönti el.

⚠️ Egy jelöltet ez ki is zár: a `0x007e4aac` (a `FUN_007e3210`-ben) a
**Tulajdonságok párbeszédé** — ott a `%016I64x`-es összefűzés
(`0x007e4acf`) a képernyőre megy, nem a `.picasa.ini`-be.

### 5. ⛳ Amit ez a #2675-re nézve KIMOND

1. A jegy 1. pontjának megfogalmazása — „melyik fájl bájtjait kell
   hashelni **a mentés pillanatában**" — **félrevezető**: a mentés
   pillanatában nem hashel senki. A helyes kérdés: **ki és mikor tölti
   fel a `[rekord+0x90]` mezőt, és milyen útvonallal.**
2. A hashelő oldal ettől függetlenül **teljesen kimérve**: egy burkoló,
   két hívó, ebből egy bizonyítottan csak a gyors kulcsot kéri.
3. **A tulajdonos kontrollált mintája EGYELŐRE NEM KELL.** A jegy 1.
   pontja `felhasználóra-vár`-t helyezett kilátásba; ez a kör
   **megnevezett gépi utat** hagy maga után (ld. 6.), tehát a kérés
   előrehozása korai lenne.

### 6. A KÖVETKEZŐ lépés, megnevezve

> **Ki írja a `[rekord+0x90]`-et?**

A pásztázás előkészítve, de **horgony kell hozzá**: a `+0x90`-re az
egész `.text`-ben **121** egész-értékadás megy (`mov [reg+0x90], reg`,
`esp`/`ebp` bázis kizárva), és sztring-értékadó idiómával
(`lea r,[obj+0x90]` + `call 0x005c2100`/`0x00401000` nyolc utasításon
belül) **7**. Ezek nagy része más osztályé, ezért a szűrés feltétele a
**rekord osztályának azonosítása** — a `FUN_007d55f0` három hívójából
(`0x007d9bb4`, `0x007d9dc0`, `0x007dba1e`) kiolvasva, melyik objektum
megy a 3. argumentumba.

*Bizonyítottsági fok: **megerősített** az 1–4. pont minden állítása
(utasításszinten, a pásztázások index-független `E8 rel32` alapon);
**nyitott** a `[rekord+0x90]` írója.*

## A rekord `+0x90`-e: az `originhash`-t a Picasa FOGYASZTJA, nem termeli (2026-09-08, #2675)

*207. kutatói kör.* Az előző kör megnevezett lépését viszi: **ki írja a
`[rekord+0x90]`-et?** A válasz felé vezető úton kiderült, hogy a mező
mindkét ismert érintője **olvasó** — és ez önmagában megválaszolja a
#2675 gyakorlati kérdését.

### 1. A rekord **304 bájtos** (`0x130`) tömbelem — és a mezőtérkép

A `.picasa.ini`-író hívója (`FUN_007d94c0`, 3602 b) a rekordot
`[ebx] + eltolás` alakban adja át (`0x007d9ba6 add ecx, ebp`), és a
ciklus lépésköze **`0x007d9f00 add ebp, 0x130`**. Ugyanez a lépésköz
`imul`-lal a `FUN_007d6db0`-ban (`0x007d6e3a imul eax, eax, 0x130`) —
**két független hely, ugyanaz a szám.**

Amit a rekordból eddig ismerünk:

| eltolás | mi | bizonyíték |
|---|---|---|
| `+0x04` | `origloc` (sztring) | `0x007d5f9e` → `push 0x00cb9260` |
| `+0x50`/`+0x54` | 64 bites szám, `%I64u`-val formázva | `0x007db9e0`–`0x007db9e8` (`0x00c82fbc`) |
| `+0x90` | **`originhash`** (sztring) | `0x007d5e2a` → `push 0x00cb9254` |

### 2. ⭐ A `+0x90`-et mindkét úton ugyanaz a metódus dolgozza fel — és SZÉTSZEDI

`FUN_007d8cf0` (291 b), `this` = **a mező CÍME** (`&rekord.originhash`):

```
0x007d8cf0  mov eax, [ecx]                 ; a sztring
0x007d8cfd  je  0x007d8df6                 ; NULL      → kilép
0x007d8d09  je  0x007d8df6                 ; nulla hossz → kilép
0x007d8d12  je  0x007d8df6                 ; üres      → kilép
0x007d8d33  call 0x00414b40                ; ← a SZÉTSZEDŐ (16+16 sscanf "%I64x")
0x007d8d45  or  eax, edx ; je 0x007d8df6   ; ha a pár 0, kilép
```

A `0x00414b40` pontosan az a függvény, amelyet a lap fentebb az
`originhash` **szétszedőjeként** azonosít (`cmp eax, 0x20`, majd 16+16
jegy külön `sscanf`-fal).

**Két hívási helye van**, mindkettő a `.picasa.ini`-modulban:

| cím | hol | mikor |
|---|---|---|
| `0x007d91e9` | `FUN_007d9160` (273 b, `image`) | rekordonkénti pász a betöltés után (`0x007d9225 add esi, 0x130`) |
| `0x007d9d13` | `FUN_007d94c0` (a kiíró vezérlője) | a kiírás előtt |

### 3. ⭐ …és a kapott párral KERES

A szétszedés után:

```
0x007d8d6f  call 0x004365b0        ; keresés a két kulccsal → lista
0x007d8d82  shr edi, 1 ; je …      ; a lista elemszáma
0x007d8db3  mov eax, [ebp + esi*4] ; végigmegy a találatokon
```

⇒ a mező tartalma **bemenet egy kereséshez** — az `origloc` szomszédsága
mellett ez azt a szerepet erősíti, hogy a pár az **eredeti fájl
azonosítója**, amit a program **visszakeres**, nem pedig frissen számol.

### 4. ⛔ ÖNHELYESBÍTÉS az előző körhöz — argumentum-számozás

Az előző szakasz („Az `originhash` ÍRÁSI LÁNCA…") a `FUN_007d55f0`
argumentumait elszámolta. A veremkeret: `0x007d55f0 sub esp, 0xac4`,
majd **négy** `push` ⇒ az argumentumok bázisa `0xac4 + 0x10 + 4 = 0xad8`.
Ebből:

| hely | argumentum | mi |
|---|---|---|
| `[esp+0xad8]` | **1.** | az az objektum, amelynek `byte +0xf9`-e az `origloc` kapuja (`0x007d5f8a`) |
| `[esp+0xadc]` | **2.** | a **kép-rekord** (`0x007d5e23`) |
| `[esp+0xaec]` | **6.** | az ini-író objektum (`0x007d5e7f call [edx+8]`) |

*(Az előző szakasz a rekordot 3., a kaput 2. argumentumnak írta. A
címek és a következtetések változatlanok — csak a sorszámozás volt
rossz.)*

### 5. ⛳ Amit ez a #2675-re nézve KIMOND

A kép teljes, ha a két kört együtt nézzük:

| lépés | mit csinál a `+0x90`-nel | cím |
|---|---|---|
| betöltés utáni pász | **olvassa**, szétszedi, keres | `0x007d91e9` |
| kiírás előtt | **olvassa**, szétszedi, keres | `0x007d9d13` |
| kiírás | **változatlanul kimásolja**, üresre kihagyja a kulcsot | `0x007d5e2a` |

⇒ **A mentési úton a Picasa nem számol és nem is számol újra
`originhash`-t.** Amit a rekord hordoz, azt írja ki; ha a rekord mezője
üres, a kulcs egyszerűen elmarad.

**Amit ez a mi megvalósításunkra nézve jelent** (a #2675 2. pontja):
a mentéskor **nem szabad újraszámolni** — a meglévő értéket kell
megőrizni (round-trip), és a képletet csak ott alkalmazni, ahol a
Picasa is előállítja (a lap „Ki állítja elő" szakasza szerint a
`FUN_004353a0` hívói közt).

Ez egyben **megmagyarázza a #791 mérésének 44 nem egyező sorát**: azok
az értékek egy korábbi Picasa-futásból származnak, és azóta
**érintetlenül öröklődnek** — nincs a mentésben olyan lépés, amely
hozzáigazítaná őket a mai fájlhoz. *(erős: a mechanizmus mérve, a
44 sor eredetét külön nem mértük)*

### 6. Ami NYITVA marad — és a következő lépés

**A `+0x90` ÍRÓJÁT továbbra sem találtuk meg.** A hatókör kimondva:

- pásztázás 1 — sztring-értékadó idióma (`lea r,[obj+0x90]` + `call`
  `0x005c2100`/`0x00401000`/`0x0040eab0`/`0x0040ea90` nyolc utasításon
  belül), **teljes `.text`**: 7 találat, egyik sem ebben a modulban;
- pásztázás 2 — `mov [reg+0x90], reg` (`esp`/`ebp` bázis kizárva),
  **teljes `.text`**: 121 találat, nagyrészt más osztályoké;
- pásztázás 3 — **`0x130`-as lépésköz ÉS `+0x90` érintés ugyanabban a
  függvényben**, teljes `.text`: **16 függvény**, ebből a
  `.picasa.ini`-modulban három (`FUN_007d6db0`, `FUN_007d9160`,
  `FUN_007d94c0`) — és mindhárom **olvasó**.

> **A KÖVETKEZŐ KÉRDÉS:** a rekord `+0x90`-ét nem közvetlen mezőírás
> tölti, hanem a **generikus kulcs→mező betöltő**. A menet: a
> `FUN_007d6db0` (4829 b) az egyetlen olyan `0x130`-lépésközű függvény,
> amely a `.picasa.ini` kulcsait **táblából** dolgozza fel — ki kell
> olvasni ezt a táblát (kulcsnév → rekord-eltolás), és megnézni, hogy a
> `+0x90` szerepel-e benne. Ez egyben eldöntené a lap korábbi negatív
> állítását is („a Picasa 3.7 az `originhash`-t **név szerint** nem
> olvassa vissza") — a `name szerint` kitétel ugyanis táblás
> feldolgozásnál nem zárja ki a visszaolvasást.

*Bizonyítottsági fok: **megerősített** az 1–4. pont (utasításszinten, a
lépésköz két független helyről); **erős** az 5. pont
(a mechanizmus mérve, a 44 sor eredete nem); **nyitott** a `+0x90` írója.*

## A tartalomkulcs egy TULAJDONSÁG (`0x68`), nem közvetlen mezőírás (2026-09-08, #2675)

*208. kutatói kör.* Az előző kör azt kérdezte, **ki írja a
`[rekord+0x90]`-et**, és a `FUN_007d6db0` kulcs→mező táblájának
kiolvasását nevezte meg útként. Az első lépés **megcáfolta a saját
tervét** — és közben előkerült a valódi mechanizmus.

### 1. ⛔ ÖNHELYESBÍTÉS: a `FUN_007d6db0` NEM név-vezérelt táblát futtat

A függvény (4829 b) **egyetlen** nyomtatható sztringre mutató
immediate operandust sem tartalmaz (a teljes törzs átfésülve). Nincs
benne kulcsnév, tehát nem lehet kulcs→mező tábla. Az előző kör
megnevezett lépése ezzel **tárgytalan**.

### 2. ⛔ A `0x130`-as lépésköz ÖNMAGÁBAN nem azonosít rekordot

A lépésköz az egész programban **40 függvényben** fordul elő. Hogy ez
mennyire nem bizonyíték, arra kimért ellenpélda van: a `FUN_0092f6d0`
(3341 b, a Web Albums Atom/RSS-elemzője — `gphoto:user`, `gphoto:id`,
`picasa:dbid`, `pubDate`) **szintén** ír egy `+0x90`-et
(`0x0092fa09`), de

```
0x0092f9d0  mov esi, 0x00cd3cdc      ; "gphoto:access"
0x0092fa06  mov edx, [ebx + 0x24]    ; MÁSIK objektum
0x0092fa09  mov [edx + 0x90], eax
```

⇒ **más rekord, más jelentés.** *(A lap „azonos méret ≠ azonos
szerkezet" tanulsága szerint a méret-egyezést külön mezőegyezéssel kell
alátámasztani.)*

### 3. ⭐ Ugyanaz a mező MÁSIK kulcsnéven is kimegy: `imageuniqueid`

A `FUN_007d61a0` (931 b) a `Picasa` szakasz kulcsait írja — `width`,
`height`, `imgdl=1`, `sizeparam`, `maxparam`, `imgmax`, `imagelink`,
`origlink`, `thumblink`, `InternetShortcut` —, és köztük:

```
0x007d641b  mov eax, [ebx + 0x90]
0x007d6421/2b/31  je 0x007d6452       ; NULL / nulla hossz / üres → kimarad
0x007d643f  push 0x00c937b0            ; "imageuniqueid"
```

Az ürességi próba **karakterről karakterre ugyanaz**, mint a
`.picasa.ini`-íróé az `originhash`-nél. ⇒ **a rekord `+0x90`-e a kép
tartalom-azonosítója**, amit a program két néven ír ki:
`originhash` (a `.picasa.ini`-be) és `imageuniqueid` (a `Picasa` /
`InternetShortcut` szakaszba).

### 4. ⭐ A VALÓDI mechanizmus: TULAJDONSÁG-TÁRBA megy, nem mezőbe

Ezért volt **minden** közvetlen mezőírás-pásztázás negatív (206.: 7 és
121 találat; 207.: 16 függvény — mind olvasó). Az érték egy **egész
kulcsú tulajdonságtárba** kerül:

```
0x0049c640  FUN_0049c640 (690 b)   ; hasítótáblás BESZÚRÁS
   0x0049c64f  add ebx, 0xc
   0x0049c660  div dword ptr [ebx + 4]      ; vödörszám
   0x0049c670  cmp dword ptr [esi + 8], edi ; láncbejárás a KULCSRA
```

és a kulcs a tartalomkulcsnál mindig **`0x68`**. A minta három
egymástól független kezelőben **bájtszomszédos**:

| kezelő | a kulcspár | a 32 jegyű alak | a beszúrás |
|---|---|---|---|
| `caption` (`FUN_00437cf0`) | `0x00438691` | `0x004386b6` | `0x004386c3 push 0x68` → `0x004386cd` |
| `keywords` (`FUN_00455ff0`) | `0x004563db` | `0x00456406` | `0x00456413 push 0x68` → `0x0045641d` |
| `geotag` (`FUN_00477ff0`) | `0x00478336` | `0x00478361` | `0x0047836e push 0x68` → `0x00478375` |

*(a `0x004353a0` a tartalomkulcs-szolgáltatás, a `0x00414c50` a
`%016I64x` ×2 összerakó — mindkettő a lap korábbi szakaszaiból)*

⇒ **A tartalomkulcs-sztringet a `.picasa.ini` szakaszkezelői állítják
elő fájlonként, és a `0x68` tulajdonságba teszik.**

### 5. ⭐ …és a `Picasa` szakasz OLVASÓJA ugyanide tölt vissza

`FUN_005af660` (4201 b) — ugyanaz a kulcskészlet, olvasói oldalról
(`width`, `height`, `videolink`, `imagelink`, `origlink`, `thumblink`,
**`imageuniqueid`**, `InternetShortcut`):

```
0x005afb28  mov esi, 0x00c937b0      ; "imageuniqueid"
0x005afb34  repe cmpsb               ; kulcsnév-egyezés
0x005afb6f  push edx                 ; az ÉRTÉK
0x005afb70  push 0x68                ; ← ugyanaz a tulajdonság
0x005afb72  add ecx, 0x130           ; a tár az objektum +0x130-ánál
0x005afb79  call 0x0049c640
```

⇒ **oda-vissza ugyanaz a rekesz**: amit `imageuniqueid` néven olvas,
azt a `0x68` tulajdonságba teszi; amit a `0x68`-ból vesz, azt
`originhash`/`imageuniqueid` néven írja ki.

### 5/b ⛔ MÉRVE: az `imageuniqueid` NEM `.picasa.ini`-kulcs

A 3. és 5. pont kulcsneve **nem** a `.picasa.ini`-é. A tulajdonos
**859 fájlos** élő korpuszán (`referencia/ini-korpusz/korpusz.txt`,
privát repó):

| minta | találat |
|---|---|
| `originhash=` sor | **1787** *(pozitív kontroll — egyezik a lap korábbi számával)* |
| `imageuniqueid` bárhol | **0** |

⇒ az `imageuniqueid` a `Picasa` / `InternetShortcut` szakaszé (generált
parancsikon-fájl), **nem** a `.picasa.ini`-é. A mi ini-olvasónkat és
-írónkat tehát **nem érinti** — nem kell új kulcsot kezelnünk. A lelet
attól még értékes: a két kimenet **közös forrását** azonosítja.

### 6. ⛳ Amit ez a #2675-re nézve hozzátesz

- A 207. kör állítása (**mentéskor nincs újraszámolás**) **áll**, sőt
  most a másik oldalról is alátámasztott: az érték egy tulajdonságtárban
  utazik, amit a szakaszkezelők töltenek fel — nem a mentés.
- **Új lelet, HATÓKÖRREL:** ugyanaz az érték `imageuniqueid` néven is
  megjelenik — de az 5/b mérés szerint **nem a `.picasa.ini`-ben**
  (859 fájl, 0 találat), hanem a generált parancsikon-fájlban. A mi
  ini-round-tripünket ez **nem érinti**.
- ⚠️ **Amit ez NEM mond ki:** hogy a `0x68` tulajdonság *hogyan* kerül
  a `[rekord+0x90]`-be. A tár egy `map<int, sztring>`; a materializálás
  helye nincs megmérve.

### 7. A KÖVETKEZŐ lépés, megnevezve

> **Hol OLVASSÁK ki a `0x68` tulajdonságot, és ki teszi a rekord
> `+0x90`-ébe?**

Menet: a `FUN_0049c640` (beszúrás) **párja**, a kulcs szerinti
lekérdezés — ugyanabban a hasítótábla-osztályban —, és annak `0x68`-cal
hívó helyei. A `push 0x68` teljes leltára már megvan (a beszúró ágon
hét hely: `0x004386c3`, `0x00456413`, `0x0047836e`, `0x005afb70`,
`0x005b018d`, `0x005b0b1b`, `0x006bf6e1`); a lekérdező ág ugyanígy
kilistázható.

*Bizonyítottsági fok: **megerősített** az 1–5. pont (utasításszinten, a
három kezelő bájtszomszédos mintájával); **nyitott** a `0x68` →
`[rekord+0x90]` materializálás.*

## A rekord-osztály HORGONYA: elem-ktor `0x00413740`, elem-dtor `0x00432270` (2026-09-08, #2675)

*209. kutatói kör.* Az előző kör horgonyt kért a `+0x90` írójának
kereséséhez. A horgony megvan — és közben egy saját kétértelműséget is
fel kell oldani.

### 1. ⛔ FELOLDÁS: két KÜLÖNBÖZŐ `0x130` van, ne keverjük

Az előző szakasz 5. pontja így idézte a `Picasa`-szakasz olvasóját:

```
0x005afb72  add ecx, 0x130           ; a tár az objektum +0x130-ánál
```

Ez a `0x130` **nem** a rekord mérete. A függvény fejéből:

```
0x005af67f  mov edi, ecx             ; edi = a THIS
0x005af689  mov dword ptr [esp+0x20], edi
…
0x005afb6b  mov ecx, dword ptr [esp+0x20]   ; ecx = a THIS
0x005afb72  add ecx, 0x130                  ; a THIS +0x130-as TAGJA
```

⇒ a tulajdonságtár a `FUN_005af660` **saját objektumának egy tagja**, és
semmi köze a 304 bájtos rekordhoz. A számegyezés véletlen. *(A lap
„azonos méret ≠ azonos szerkezet" tanulságának egy újabb esete —
ezúttal ugyanazon a lapon belül.)*

### 2. ⚠️ És a `0x68` sem egy dolog

| hol | mi |
|---|---|
| `push 0x68` a `FUN_0049c640` előtt | a tulajdonságtár **kulcsa** |
| a rekord `+0x68` mezője | egy **egész**, amit az elem-ktor `-1`-re állít (`0x00413790` `or edx,0xffffffff` → `0x00413793`) |

A kettő között nincs kapcsolat; a szám-egybeesés itt is véletlen.

### 3. ⭐ A HORGONY: a vektor-segédek kiadják az elem ktorát és dtorát

A `0x130`-as elemméretű tömb kezelői a `0x005a3000`–`0x005a5000`
modulban ülnek, és a **méret mellé a függvénymutatót is tolják**:

```
0x005a3404  push 0x00413740      ; az elem KONSTRUKTORA
0x005a340b  push 0x130           ; az elem MÉRETE
0x005a3414  call 0x004010e0      ; tömb-konstruálás

0x005a345d  push 0x00432270      ; az elem DESZTRUKTORA
0x005a3462  push 0x130
0x005a3467  call 0x00401110      ; tömb-lebontás
```

⇒ **az osztály azonosítva**: `sizeof = 0x130` (304), ktor
`FUN_00413740` (316 b), dtor `FUN_00432270` (402 b).

### 4. ⭐ És ezzel a `+0x90` MEZŐ-mivolta is bizonyított

- **A ktor nullázza:** `0x004137b5 mov dword ptr [eax + 0x90], ecx`
  (`ecx = 0`) — a mező NULL-ként születik, ami pontosan az a
  „nincs kulcs" állapot, amit a `.picasa.ini`-író üresre kihagy.
- **A dtor elengedi:** `0x00432316 lea …[+0x90]` → sztring-elengedés.
  ⚠️ Ez a függvény **már ott volt** a 206. kör hét találatos
  sztring-idióma-pásztázásában — akkor nem ismertük fel, mert nem volt
  meg a horgony.

⇒ **a `+0x90` a rekord-osztály hivatkozásszámlált SZTRING-tagja**,
konstrukciókor üres.

A ktor további, most kiolvasott alapértékei: `+0x20` és `+0x28`
**949998,0** (`double`, `0x00c7ccf8`), `+0x68` = **−1**, `+0x70` = **2**,
`+0x00`…`+0x64` és `+0x78`…`+0xa0` nullák.

### 5. ⛔ Amit NEM állítok — a hatókör kimondva

- A tulajdonságtár **lekérdező** oldalát **nem** azonosítottam. A
  `push 0x68` leltár (hét hely) **kizárólag** a beszúró (`FUN_0049c640`)
  ága. Egy `mov <reg>, 0x68` pásztázás 30-nál több találatot ad, de a
  `0x68` **gyakori kis konstans** (méret, index, eltolás), ezért abból
  **sem pozitív, sem negatív** következtetést nem vonok le.
- Tehát **nem** mondom ki, hogy „nincs lekérdező" — csak azt, hogy ezzel
  a két pásztázással nem található meg.

### 6. A KÖVETKEZŐ lépés, megnevezve

> **Melyik használó tölti fel a `+0x90`-et?**

Most már van szűrő: a `0x00413740` (ktor) és a `0x00432270` (dtor)
**index-független** `E8 rel32` hivatkozói adják az osztály használóinak
listáját. A menet: ezt a listát metszeni a 206. kör 121 találatos
`mov [reg+0x90], reg` leltárával — a metszet a valódi jelöltek halmaza,
és az már kézzel végigolvasható.

*Bizonyítottsági fok: **megerősített** az 1–4. pont (utasításszinten);
**kimondottan nyitott** az 5. pont szerinti lekérdező oldal és a `+0x90`
feltöltője.*

## A metszet lefutott — érdemben ÜRES, és egy saját szám helyesbítése (2026-09-08, #2675)

*210. kutatói kör.* Az előző kör lépését viszi: az osztály **használói**
(a ktor `0x00413740` / dtor `0x00432270` hivatkozói) metszve a `+0x90`
**íróival**.

### 1. A metszet: két találat — és mindkettő HAMIS POZITÍV

| pásztázás | találat |
|---|---|
| osztály-használó (`0x413740`/`0x432270` operandusként) | **29** függvény |
| `mov [reg(+reg)+0x90], reg` (`esp`/`ebp` bázis kizárva) | **104** függvény |
| **metszet** | **2** |

A kettő: `FUN_0092f6d0` (3341 b) és `FUN_009316c0` (622 b) — mindkettő a
**Web Albums Atom/RSS** modulból. Elolvasva **egyik sem** a rekordra ír:

`FUN_0092f6d0` **valóban** használja az osztályt — `0x009302db push 0x413740`,
`0x00930337 push 0x432270`, és a vektort is kezeli
(`0x00930268 imul ecx, ecx, 0x130`) —, de a két `+0x90`-írása a **saját**
elemző-objektumára megy:

```
0x0092fa06  mov edx, [ebx + 0x24]        ; MÁSIK objektum (gphoto:access ág)
0x0092fa09  mov [edx + 0x90], eax

0x00930232  mov edx, [ecx + 4]
0x00930235  shr edx, 1                   ; egy HOSSZ
0x0093023a  mov [ebx + 0x90], edx        ; a saját +0x90-e, EGÉSZ
```

⇒ **a metszet érdemben üres**: a rekord `+0x90`-ét egyszerű
mezőértékadással **senki** nem írja.

### 2. ⛔ ÖNHELYESBÍTÉS: a 206. kör „7 találat"-a a SZŰRŐ műterméke volt

A 206. kör így írta le a másik pásztázást: *„sztring-értékadó idiómával
(`lea r,[obj+0x90]` + `call 0x005c2100`/`0x00401000` nyolc utasításon
belül): **7**"*. A pásztázó azonban a következő nyolc utasításból az
**engedélyezett listára illeszkedő ELSŐ** hívást vette, nem a
**közvetlenül következőt** — így például a `0x007d91e3`-at
`call 0x00401000`-ként könyvelte, holott ott valójában
`0x007d91e9 call 0x007d8cf0` áll (a 207. kör szétszedője).

**A javított, szűretlen pásztázás** (a `lea` után a **közvetlenül**
következő hívás, előírt cél nélkül): **59 hely** az egész `.text`-en.
**Ez a helyes szám**; a 7 nem az.

### 3. ⭐ És az 59-ből egy sincs osztály-használóban

A javított listát a 29 osztály-használóval metszve: **nulla**.

### 4. ⚠️ A MÓDSZER KORLÁTJA — ezért nem mondom ki, hogy „senki nem írja"

Egy C++ osztály **`operator=`-a és másoló konstruktora nem hivatkozik**
a ktorára/dtorára. A „hivatkozik-e a ktorra/dtorra" szűrő tehát
**elvileg sem láthatja** a mezőnkénti másolót — pontosan azt, ami a
`+0x90`-be értéket vihet. Ez a kör negatívja ezért **szűk hatókörű**:

> a rekord `+0x90`-ét **közvetlen mezőírás** és **a mező címén át hívott
> sztring-metódus** sem tölti fel — a **másoló/értékadó** út nyitva marad.

### 5. ⛔ Negatív melléklelet: a `949998,0` NEM ujjlenyomat

A 209. kör a ktorból kiolvasta, hogy a `+0x20`/`+0x28` alapértéke
**949998,0** (`0x00c7ccf8`). Kézenfekvő lett volna ezzel horgonyozni a
rekordot — de nem lehet: a konstansra az egész programban **több tucat**
függvény hivatkozik (`FUN_0040d160`, `FUN_0040eef0`, `FUN_00425f60`,
`FUN_00441ed0`, `FUN_0045cfa0`, `FUN_00464990`, … ). Ez egy általános
**„nincs érték" őrszem**, nem osztály-jellemző.

### 6. A KÖVETKEZŐ lépés, megnevezve

> **A rekord MÁSOLÓ/ÉRTÉKADÓ metódusa** — az a függvény, amely
> `[forrás+0x90]`-et olvas **és** `[cél+0x90]`-be ír.

A pásztázás lefutott, a jelöltlista megvan (olvasás ÉS írás ugyanabban a
függvényben), de a **rekordhoz kötéshez második mező-horgony kell**, és
az nem a `949998,0` lehet (5. pont). Használható jelöltek a ktorból:
`+0x68 = −1` (`0x00413790`–`0x00413793`) és `+0x70 = 2` (`0x00413796`)
**együtt** — két szomszédos, szokatlan alapérték.

*Bizonyítottsági fok: **megerősített** az 1–3. és az 5. pont
(utasításszinten, a hamis pozitívok elolvasva); a 4. pont a módszer
kimondott korlátja, ezért a negatívot **nem** általánosítom.*

## MEGVAN a rekord `operator=`-a — és igenis írja a `+0x90`-et (2026-09-08, #2675)

*211. kutatói kör.* Az előző kör **kimondta**, hogy a „hivatkozik-e a
ktorra/dtorra" szűrő elvileg sem láthat egy `operator=`-t. Ez a kör
megkereste — és a hipotézis **pozitív találattal** igazolódott.

### 1. ⭐ A megtalálás útja: a vektor MÁSOLÓ ciklusa

A `0x130`-as elemméretű tömb kezelőjében (`FUN_005a3360`) a
tömb-növelés után egy elemenkénti ciklus áll:

```
0x005a3434  mov ecx, [esi]        ; a RÉGI tömb
0x005a3436  add ecx, edi
0x005a3438  push ecx              ; forrás
0x005a3439  lea edx, [edi + ebx]  ; cél (az ÚJ tömbben)
0x005a343c  push edx
0x005a343d  call 0x005a4f10       ; ← az elem MÁSOLÁSA
0x005a3442  add edi, 0x130        ; a lépésköz
```

⇒ **`FUN_005a4f10` (1452 b) a rekord `operator=`-a**, `dst` = 2. tolt
argumentum (`ebp`), `src` = 1. (`ebx`).

*(A segédfüggvények szerepe is kiolvasva: a `FUN_004010e0`
`eax` = darabszám, `ecx` = bázis, majd elemenként `call fn` előrefelé —
tömb-konstruálás; a `FUN_00401110` ugyanez visszafelé — tömb-lebontás.
Másoló segéd **nincs** köztük, a másolást ez a kézi ciklus végzi.)*

### 2. ⭐ És a `+0x90`-et a szokásos sztring-idiómával MÁSOLJA

```
0x005a5309  mov ecx, [ebp + 0x90]     ; a CÉL jelenlegi sztringje
0x005a530f  cmp ecx, [ebx + 0x90]     ; egyezik a FORRÁSÉVAL?
0x005a5315  lea edi, [ebp + 0x90]
0x005a531b  je  0x005a5353            ; ha igen, nincs teendő
0x005a531d  call 0x00401000           ; a régi elengedése
0x005a5322  mov eax, [ebx + 0x90]     ; ← a FORRÁS értéke
0x005a532a  mov [edi], eax            ; átkötés
0x005a534e  call 0x00985a60           ; hivatkozásszám növelése
```

⇒ **a rekord `+0x90`-ét a `operator=` írja** — és mivel az `operator=`
nem hivatkozik a ktorra/dtorra, a 210. kör szűrője **elvileg sem**
láthatta. A kimondott korlát ezzel **igazolt**, nem csak feltételezett.

### 3. ⭐ A rekord MEZŐTÉRKÉPE az `operator=`-ból

Az érintett eltolások teljes leltára (a 1452 bájt átfésülve):

```
+0x0c +0x10 +0x14 +0x18 +0x20 +0x24 +0x28 +0x2c +0x30 +0x34 +0x3c
+0x40 +0x44 +0x48 +0x4c +0x50 +0x54 +0x58 +0x5c +0x60 +0x64 +0x68
+0x70 +0x90 +0x94 +0x9c +0xa0 +0xa4 +0xa8 +0xb0 +0xf0 +0xf4 +0x110
```

A `+0x68`-at és a `+0x70`-et **egészként** másolja
(`0x005a52f7`/`0x005a5301`), a `+0x90`-et és a `+0x94`-et
**sztringként** (`0x005a5309`, `0x005a5353`).

### 4. ⭐ A vektor `push_back`-je: `FUN_007d53e0`

```
0x007d54c1  call 0x0097c5d0        ; operator new
0x007d54d0  push 0x00413740        ; elem-ktor
0x007d54d7  push 0x130
0x007d54e0  call 0x004010e0        ; az ÚJ tömb megkonstruálása
0x007d550a  call 0x005a4f10        ; a régi elemek átmásolása (lépés 0x130)
0x007d552b  push 0x00432270 ; 0x130 → 0x00401110   ; a régi tömb lebontása
0x007d555f  call 0x005a4f10        ; ← az ÚJ elem a végére, operator=-szal
0x007d5574  mov [ebp+4], ecx       ; a csomagolt darabszám +2-vel
```

### 5. ⭐ …és a `push_back` EGYETLEN hívója a Google Photos-letöltés

Index-független pásztázás: `0x006fa388` és `0x006fa78c`, mindkettő a
**`FUN_006f9cc0`** (6829 b) — sztringjei: `Download from Google Photos`,
`Picasa2RSS`, `CLighthouseConfirm::only_videos`, `photo`, `photos`.

⇒ **ez a rekord-vektor a web-album fotólistája**, és a `.picasa.ini`
metaadat-írója (`FUN_007d55f0`) ugyanennek az osztálynak a rekordjait
írja ki.

### 6. ⛔ DE ezen az úton a `+0x90` ÉRINTETLEN MARAD

A `0x006fa388`-as híváskor a forrás egy **verem-rekord**:

```
0x006fa371  lea ecx, [esp + 0x80]   ; a rekord
0x006fa378  push ecx
0x006fa388  call 0x007d53e0
```

Ha a rekord a `esp+0x80`-on ül, akkor a `+0x90` mezője az
`[esp+0x110]` — és erre a függvény **6829 bájtjában egyetlen
hivatkozás sincs**. *(A függvényben látható `[esp+0x90]`-ek a rekord
`+0x10`-ének felelnének meg, tehát nem a keresett mező.)*

⇒ **ezen az úton az `originhash` üres marad**, és a kiíró — a 206. kör
szerint — ilyenkor **ki is hagyja a kulcsot**. A letöltési ág tehát
**nem** az `originhash` forrása.

### 7. A KÖVETKEZŐ lépés, megnevezve

> **Az `operator=` MELYIK hívója hoz nem üres `+0x90`-et?**

Az `operator=`-nak (index-független pásztázás) **húsznál több** hívási
helye van; a most megnézett kettőn (`0x005a343d` — belső vektor-másolás,
`0x007d555f` — a letöltési `push_back`) kívül a jelöltek:
`0x0043219c`, `0x006df6c8`, `0x006f835e`, `0x006f83c8`, `0x0092f254`,
`0x0093031a`, `0x00930372`, `0x0093045d`, `0x00931875`, `0x009318cc`,
`0x0093219e`, `0x005a3591`, `0x005a3605`, `0x005a4489`, `0x005a45e0`,
`0x005a472f`, `0x005a4829`, `0x007d550a`. A menet: mindegyiknél a
**forrás** rekord eredetét kell megnézni — az elsőt, amelyiknél a
`+0x90` nem üresen születik.

*Bizonyítottsági fok: **megerősített** az 1–6. pont (utasításszinten, a
mezőtérkép a teljes törzs átfésüléséből); **nyitott** a nem üres `+0x90`
forrása.*
