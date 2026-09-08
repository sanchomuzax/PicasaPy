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
0x007d5e23  mov ecx, [esp + 0xadc]        ; a KÉP-REKORD (3. argumentum)
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
0x007d5f8a  cmp byte ptr [ebx + 0xf9], 0  ; kapu a 2. argumentum objektumán
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
