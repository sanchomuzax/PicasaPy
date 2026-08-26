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

---

## 3. Amit KIZÁRTAM — három téves jelölt

| jelölt | miért nem |
|---|---|
| **`onlinechecksum`** | a korpuszban mind a **380** érték pontosan **8 hexa jegy**; a PMP-ben a típusa **`0x01` (u32)**. Egy 64 bites kulcsnál a felső dword 380-ból 380-szor nulla lenne — kizárt. **Ez 32 bites, más mennyiség.** |
| **`originhash`** (ini-kulcs) | 32 hexa jegy = teljes MD5, de **nyolc bemenet-változatot** próbáltam négy valódi fájlon (teljes fájl · fej+farok · méret32/64 elöl/hátul · nagy-endián · csak fej) — **0/32 találat**. Nem ez a függvény írja. |
| **`imagedata_backuphash`** | PMP típus **`0x05` (u16)** — 16 bit, nem lehet tartalom-kulcs. |

---

## 4. Eredeti / nálunk / teendő

| eredeti | nálunk MA | teendő |
|---|---|---|
| **fej+farok MD5**, 4+16834+16834 bájt olvasás | `dedup/exact.py:35` — **SHA-256 a TELJES fájlon** | átvenni a gyors kulcsot |
| a méret a hash **bemenetének része** | nincs | átvenni |
| 64 bites kulcs, `u64` oszlopban | nincs ilyen oszlopunk | tárolni |
| gyorstárazás (ha megvan, nem számol) | — | átvenni |

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
| Az `originhash` a párja? | **LEZÁRVA — NEM**, 0/32 (3.) |
| **Mi az `imagedata_originslow`?** | **ÚJ JEGY** — külön, u64 oszlop, más algoritmus (öt MD5-változat 0/4); a nevéből ítélve teljes tartalom vagy dekódolt képpont alapú |

```
Nyitott kérdések: 0 nyílt · 4 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```
