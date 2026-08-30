# Az ELSŐ INDÍTÁS panelje — `initialscan` (2026-08-21)

Az eredeti Picasa 3.9.141.259 első indításakor **nem a Mappakezelő nyílik
meg**, hanem egy külön, teljes felületű panel: az **`initialscan`**. Ez a
lap azt írja le teljesen.

**Források:** `runtime/respack.yt` → `tre:initialscan` (3167 bájt) és 18
rajzi rétege · `Picasa3.exe` (`0x005b77c0`).

*(A kérdés a Mappakezelő-kör **M4** tételéből jött: „mi az első indítás
belépési útja a Mappakezelőhöz?" — a válasz: **nincs ilyen út**, ld. 4.)*

---

## 1. KÉT változat, egy panel

A `tre:initialscan` **két teljes szövegkészletet** tartalmaz ugyanarra a
felületre (`Text1` és `Text2` előtaggal) — a program a helyzet szerint
választ:

### 1.1 `Text1` — MIGRÁCIÓ (van korábbi Picasa)

| elem | szöveg |
|---|---|
| `text1` | Picasa |
| `text2` | There is an older version of Picasa installed.  Would you like to update your existing picture library, or search your computer for pictures again? |
| `text2a` | Please choose from the following options: |
| `text3` | **Update my existing picture library** |
| `text3a` | Choose this option if you use keywords or custom albums in Picasa 1, and you want to preserve these in Picasa 3. |
| `text4` | **Search my computer for pictures again** |
| `text4a` | Choose this option for a more complete search of your computer, which includes extended picture information.  It will preserve your existing edits and organization, but it will not preserve keywords.  This search may take several minutes. |
| `text5` | Searching for pictures never moves or copies files to new locations. You can choose which folders are displayed by Picasa by using the Folder Manager tool (available from the Tools menu) |
| `ok-label` | **Continue** |

### 1.2 `Text2` — TISZTA TELEPÍTÉS (lemez-beolvasás)

| elem | szöveg |
|---|---|
| `text2` | Picasa is ready to search for pictures on your computer |
| `text2a` | Please choose from the following options: |
| `text3` | **Only search Documents, Pictures, the Desktop, and iPhoto Library** |
| `text3a` | Choose this option if you only store your pictures in these folders. |
| `text4` | **Search my whole computer for pictures** |
| `text4a` | Choose this option if you have pictures stored in various folders across your computer, especially if you have pictures stored on more than one hard drive. |
| `text5` | *(ua., „displayed **in** Picasa" szórenddel)* |
| `ok-label` | **Continue** |

> **A `text5` mindkét változatban ugyanazt ígéri:** a keresés **soha nem
> mozgat és nem másol fájlt**, és a megjelenített mappák a
> **Mappakezelőből** állíthatók („available from the Tools menu").

---

## 2. Geometria (tervezővászon: **640 × 463**)

| elem | x0 | y0 | x1 | y1 | méret |
|---|---:|---:|---:|---:|---|
| `docbounds` / `baseclip` | 0 | 0 | **640** | **463** | a panel mérete |
| `base` | 0 | 0 | 19 | 463 | 19×463 — bal oldali sáv (RLE) |
| `title` (`globalbuttons/logo_n`) | 15 | 13 | 39 | 37 | 24×24 — a Picasa-logó |
| `text1` | 48 | 9 | 620 | 36 | `m_displayfont24` |
| `text2` | 20 | 63 | 620 | 93 | `m_systemfont16` |
| `text2a` | 20 | 103 | 620 | 133 | `m_displayfont14`, **`m_hidden`** |
| `radiogroup` | 20 | 134 | 620 | 337 | 600×203 |
| **`radio_limited`** | 35 | **136** | 65 | 166 | 30×30 |
| `text3` | 71 | 138 | 620 | 161 | `m_systemfont14` |
| `text3a` | 71 | 163 | 620 | 231 | `m_displayfont14` |
| **`radio_complete`** | 35 | **236** | 65 | 266 | 30×30 |
| `text4` | 71 | 238 | 620 | 261 | `m_systemfont14` |
| `text4a` | 71 | 263 | 620 | 337 | `m_displayfont14` |
| **`connector`** | 21 | 150 | 30 | 252 | 9×102 — a két rádiót összekötő rajz |
| `text5` | 20 | 339 | 620 | 408 | `m_displayfont14` |
| **`ok`** („Continue") | **522** | 423 | 620 | 452 | 98×29 |
| `cancel` („No") | 414 | 423 | 512 | 452 | 98×29 — **`m_hidden`** |

**Négy dolog, amit ez kimond:**

1. **A rádiók 100 képpont osztásban** vannak (136 → 236), 30×30-asak, és a
   felirat a rádió jobb szélétől **+6** képponttal kezdődik (65 → 71).
2. Van egy **`connector`** grafika (9×102) a két rádió közt a bal
   szélen — vizuális kapocs, nem szöveg.
3. **A Mégse gomb REJTETT** (`initialscan/cancel: root m_hidden`) — az
   első indításnál **nem lehet kihagyni a választást**, csak a
   „Continue".
4. A `text2a` („Please choose from the following options:") **alapból
   rejtett**, tehát csak az egyik változatban jelenik meg.

A rádiók `m_hit_childlabel`-t viselnek: **a feliratra kattintva is
elsülnek**.

---

## 3. A kód

A tiszta telepítés „csak ezek a mappák" szövegének régebbi alakja
(`"Only search My Documents, My Pictures, and the Desktop"`) a
**`0x005b77c0`** függvényben van — ez a panel kezelője.

*(A két rádió pontos hatása — mit ír a `scanlist.txt` `+` szakaszába a
„whole computer", és mit a szűkített — a `0x005b77c0` végigolvasásán
múlik; ld. 5.)*

---

## 4. Az M4 válasza: az első indítás NEM a Mappakezelőt nyitja

A Mappakezelőnek **két** belépési pontja van, mindkettő menü
(`ID_TOOLS_INCLUDEEXCLUDEFOLDERS`, parancs `0x9caa` — ld.
`picasa-mappakezelo.md` 10/b.1). Az első indítás **külön panelt** mutat,
és a Mappakezelőre csak **szövegben** utal.

*Bizonyítottsági fok: **megerősített** — a `tre:initialscan` szó szerinti
tartalma és a rétegek mért geometriája; a Mappakezelő-oldali negatívum a
parancsazonosító teljes menü-leltárából.*

---

## 5. Ami NYITVA marad

1. ~~Mit ír a két rádió~~ — **TELJESEN LEZÁRVA** (6.1 és 6.5): a panel
   −1/1/2 kódot ad vissza, az indulás-rutin ebből
   `0x004fdd10(lista, teljesGép)`-et hív, és a lista a Mappakezelővel
   **közös** `+0xf8` tároló, amit a `scanlist.txt` írója ment ki.
2. ~~Mi dönti el, melyik szövegkészlet jelenik meg~~ — **LEZÁRVA** (6.6):
   a konstruktor `[dlg+0x274] = (*rekesz == 0)`; a rekeszt az
   indulás-rutin tölti a felderített régi telepítés sztringjéből
   (`0x00406c00`: Lifescape-registry, `#db2\`, `p1/p2/p3import`).
3. ~~Hol jelenik meg a panel, és mi történik bezáráskor?~~ — **LEZÁRVA**
   (6.7): saját **modális** ablak a főablak szülővel; **bezárásra −1**
   kerül a kimeneti rekeszbe, és az indulási lépés **megszakítottként**
   végződik (`0xF4242`).

---

## 6. A panel SZERZŐDÉSE — mit ad vissza, és hogyan (2026-08-21, U1)

### 6.1 A panel nem ír fájlt — egy KÓDOT ad vissza

A megjelenítő a `0x0040e410`: foglal egy **0x278 bájtos** objektumot,
megépíti (`0x005b7610`), majd **modálisként** mutatja
(`0x009d4a80(dlg, "initialscan", szuloAblak, 0)`).

Az eredményt a hívó által adott **egész-rekeszbe** írja
(`CInitialScanDialog + 0x270` → az indulás-rutin `[ebx]`-e):

```asm
; 0x005b7e80 — az OK gomb kezeloje
0x005b7f29  ecx = [esi+0x270]           ; a kimeneti rekesz
0x005b7f31  cmp byte [edi+0x359], al    ; a radio_complete BE van nyomva?
0x005b7f37  setne al
0x005b7f3a  add eax, 1
0x005b7f3d  [ecx] = eax                 ; 1 vagy 2
```

| érték | jelentés | ki állítja |
|---:|---|---|
| **−1** | **megszakítva** | az indulás-rutin `0x0040d56d`-nél nézi, és `0xF4242`-vel kilép |
| **1** | a **szűkített** választás (`radio_limited`) | `0x005b7f3a` |
| **2** | a **teljes gép** (`radio_complete`) | `0x005b7f3a` |

> **Vagyis a panel maga NEM ír `scanlist.txt`-et.** Egy 1/2 kódot ad
> vissza, és a **beolvasási lista összeállítása a hívó dolga** — az
> indulás-rutin (`0x0040d3c0`) a `0x0040d5ac`-nál ágazik el az értékre
> (`cmp dword [ebx], 0` → `jne 0x0040d6e3`).

### 6.2 A migrációs változat KÉTLÉPCSŐS

Ha a migrációs jelző (`[dlg+0x274]`) áll, a „Continue" **nem feltétlenül
zárja be az ablakot**:

```asm
0x005b7ed9  cmp byte [esi+0x274], 0     ; migracios valtozat?
0x005b7ee0  je  0x5b7f29                ;   nem -> a valasz kiirasa, bezaras
0x005b7ee2  cmp byte [edi+0x359], 0     ; a radio_complete be van nyomva?
0x005b7ee9  jne 0x5b7f3f                ;   igen -> tovabb (bezaras)
0x005b7eeb  call 0x5b76d0               ;   nem  -> a MASIK szovegkeszlet betoltese
0x005b7ef9  "initialscan/base" -> ujrarajzolas (|= 7)
0x005b7f0b  [esi+0x274] = 0             ;   a migracios jelzo torlese
0x005b7f20  return 0xF4241              ;   NEM kezeltem -> az ablak NYITVA marad
```

**Vagyis: migrációs esetben, ha a felhasználó nem a „Search my computer
for pictures again" tételt választja, ugyanaz az ablak átvált a MÁSODIK
szövegkészletre** (a beolvasási kérdésre), és csak a következő „Continue"
zár be. A jelző törlődik, tehát a második képernyőn már az 1/2 kód íródik.

*(Hogy a két lépés melyik felhasználói döntéshez tartozik pontosan, a
`0x005b76d0` argumentumán múlik — a mechanizmus utasításszinten
megerősített, a szemantikai olvasat ennyiben következtetés.)*

### 6.3 HELYESBÍTÉS: Windowson MÁS a szűkített választás felirata

A lap 1.2 szakasza a `.tre`-ből idézte:
„Only search Documents, Pictures, the Desktop, and **iPhoto Library**".
**Windowson ez nem ez a szöveg.** A panel felépítője (`0x005b77c0`)
futásidőben **felülírja** a `text3`-at:

| kulcs | szöveg | magyar |
|---|---|---|
| `CInitialScanDialog::OnlySearchWin` | Only search My Documents, My Pictures, and the Desktop | **Keresés csak a Dokumentumok és a Képek mappában, valamint az asztalon** |
| `CInitialScanDialog::OnlySearchMac` | Only search Documents, Pictures, the Desktop, and iPhoto Library | Keresés csak a Dokumentumok és a Képek mappában, az asztalon és az iPhoto könyvtárban |

A `.tre`-ben a **Mac**-es változat áll; a kód a `0x005b77c0`-nál cseréli
Windowson. **A `.tre` szövege tehát nem mindig az, amit a felhasználó
lát** — ezt a `picasa-respack-format.md` figyelmeztetéséhez hasonlóan
kezelni kell.

### 6.4 A panel kihagyható — `skipinitialscan`

Az indulás-rutin (`0x0040d3c0`) `Preferences` kulcsai közt ott a
**`skipinitialscan`** — a panel megkerülhető beállításból. *(Ugyanitt:
`ConfiguredSlingshot`, `LastViewRoot`, `LastAlbumSelected`,
`ReportStats`, `RIGHTDRAWEROFFSET`.)*


### 6.5 A választástól a beolvasási listáig — a teljes lánc (U4)

```
initialscan panel (0x005b7e80)
    -> a hivo rekeszebe: -1 (megszakitva) / 1 (szukitett) / 2 (teljes gep)

indulas-rutin (0x0040d3c0), 0x0040d77a-tol:
    ha az ertek 1 vagy 2:
        dl = (ertek == 2)                              ; 0x0040d793  "teljes gep"
        0x004fdd10( [ [this+0x2bc] + 0xf8 ], dl )      ; 0x0040d79d
        0x00418930( [this+0x2bc] )                     ; 0x0040d7a9
    egyebkent (0 vagy egyeb): kihagyja
```

**`0x004fdd10` (3415 bájt) a beolvasási lista felállítója**, és **egyetlen
hívója az indulás-rutin**. Belül:

| cím | mi történik |
|---|---|
| `0x004fdd36` | `0x009966a0` — a **„My Pictures"** rendszermappa feloldása |
| — | `0x00994a60` a teljes Windows-rendszermappa-táblát tartja: `WinSystemPaths::MyPictures`, `::Desktop`, `::MyDocuments`, `::MyMusic`, `::MyVideos`, `::ApplicationData`, `::CommonApplicationData` |
| **`0x004fe460`** | **`cmp byte ptr [esp+0x5c], 0` → a „teljes gép" jelző szerinti ELÁGAZÁS** (`je 0x004fe57e`) |
| `0x004fe3f9` | `0x004efde0` — `Preferences\DSChangeDetect` |

> ⭐ **A `+0xf8` alobjektum UGYANAZ**, amit a **Mappakezelő** alkalmazója is
> használ (`0x005cef2e`: `esi = [arg1+0x2bc] + 0xf8`), és amire a
> `0x007bfec0` dolgozik. Vagyis **egyetlen közös tároló** kapja a
> beolvasási listát az első indításból ÉS a Mappakezelőből — és ezt menti
> ki a `scanlist.txt` írója (`0x004f61c0`,
> `picasa-mappakezelo.md` 11.3).

**A két ág — DEKOMPILÁLVA végigolvasva (2026-08-30):** a `0x004fdd10`
dekompilált kódja (`script-DecompileInitialscan.log`, [165] függvény)
**megerősíti** a teljes szerkezetet:

1. **Bevezető** (`0x004fdd36`–): `FUN_009966a0(&local_38)` = **My Pictures**,
   majd `FUN_00996230(&local_40)` = **My Documents** feloldása és
   **kis-nagybetű-független összehasonlító rendezése** (a `0x004fe1a0`
   tájékán `cVar3 + ' '`/`cVar2 + ' '` ág — `_stricmp`-szerű).
2. **A „teljes gép" jelző elágazása** (`param_2` = a hívó `dl` jelzője):
   ```c
   if ((char)param_2 == '\0') {   // SZŰKÍTETT: a szűkített ág — a feloldott mappák
       ... 3 rendszermappa a listaban ...
   } else {                       // TELJES GÉP: dinamikusan bővülő lista
       GetLogicalDrives();        // 0x004fde0x: a meghajtó-lekérdezés
       FUN_006dabf0(&local_c,3,1);  // FIXED (3) meghajtók, FAT/FAT32/NTFS szűrő
       FUN_006dabf0(&local_14,4,1);  // REMOTE (4) meghajtók, ugyanaz a szűrő
   }
   ```
3. **`FUN_006dabf0` (a meghajtó-felsoroló, 1092 bájt)** — a `GetLogicalDrives()`
   biteket `C:`-tól lépteti, `GetDriveTypeA`-val szűr (paraméter: 3=FIXED,
   4=REMOTE), és a `param_3 == 1` esetén `GetVolumeInformationA` +
   `__stricmp(..., "FAT"/"FAT32"/"NTFS")`-sel a fájlrendszert is ellenőrzi.
4. **A befejező ciklus** a `+0x364..0x368` feladat-mezőket tölti
   (`FUN_004ef8f0`, típuskód 9 = `FUN_004e5210`), és a meghajtó-gyökereket
   (`+C:\`, `+L:\`… alakú bejegyzéseket) a `scanlist.txt`-író
   (`0x004f61c0`) menti ki.

> **A valódi `scanlist.txt`-mintánkban** (`research/testdata/Picasa2/db3/`)
> éppen **négy `+` sor** áll, mind **meghajtó-gyökér** (`+C:\`, `+L:\`,
> `+E:\`, `+D:\`) — ez a „teljes gép" választás lenyomata, és a dekompilált
> kód most pontosan ezt az alakot ígéri (a `FUN_006dabf0` a
> `X:\` formátumú gyökereket adja, a `"X:\"` sztring a `0xc87530`-n).

*Bizonyítottsági fok: **megerősített** a láncra (a kód minden lépése,
a közös `+0xf8` tároló, az elágazás helye) és **megerősített** a két ágra
(a szűkített = három rendszermappa, a teljes = FIXED+REMOTE
meghajtó-gyökerek FAT/FAT32/NTFS szűrővel) — a `0x004fdd10` és a
`FUN_006dabf0` dekompilált végigolvasása alapján, a felirat- és
mintafájl-bizonyítékokkal együtt.*

### 6.6 Mi dönti el, MELYIK szövegkészlet jelenik meg (U2)

A döntés a **konstruktorban** (`0x005b7610`, 84 bájt) születik:

```asm
0x005b764f  [dlg+0x270] = esi          ; a hivo kimeneti rekesze
0x005b7655  cmp dword ptr [esi], eax   ; eax = 0 -> a rekesz TARTALMA nulla?
0x005b7657  sete al
0x005b765a  [dlg+0x274] = al           ; ← a MIGRACIOS jelzo
```

**`migrációs jelző = (a kimeneti rekesz tartalma == 0)`** — vagyis a hívó
a panel megnyitása **előtt** beleír egy értéket, és ez választja ki a
szövegkészletet:

| a rekesz előre beírt értéke | jelző | szövegkészlet |
|---:|---:|---|
| **0** | 1 | **`Text1` — MIGRÁCIÓ** |
| **1** | 0 | **`Text2` — TISZTA TELEPÍTÉS** |

Az indulás-rutin (`0x0040d3c0`) így tölti fel — **az assembly igazolja**
(`script-DecompileAssembly.log`, „indulas-rutin: sztringvizsgalat", és a
koordinátor-hívás `00403ebe LEA EDX,[EBX+0x101c]`):

```asm
; a koordinátor (0x004039f0) hívása:
00403eb4  mov ecx, [ebx+0x102c]   ; param_1 = a fő objektum
00403ebe  lea edx, [ebx+0x101c]   ; param_2 = a +0x101c blokk címe ★
00403ec4  call 0x0040d3c0

; az indulás-rutin eleje:
mov edi, ecx                      ; EDI = param_1 (a fő objektum)
mov esi, edx                      ; ESI = param_2 (a +0x101c blokk)
...
cmp byte ptr [esi], 0x0           ; [+0x101c] == 0?  (nincs #db3\ találat)
; a döntés:
mov eax, [esi+0x4]                ; eax = [+0x1020] — a VIZSGÁLT SZTRING
test eax, eax        / jz 0x40d458
test dword ptr [eax], 0xffffff00 / jz 0x40d458   ; érvényes sztring-csomag?
cmp byte ptr [eax+0x4], 0  / jz 0x40d458         ; nem üres?
mov dword ptr [ebx], 0            ; ← VAN ilyen -> MIGRÁCIÓ
jmp 0x40d45e
mov dword ptr [ebx], 1            ; ← nincs   -> TISZTA TELEPÍTÉS
```

**A vizsgált sztring a `+0x1020`**, amit a `0x00406c00` (1362 bájt) — az
**adatbázis- és migráció-felderítő** — tölt a p1import ágon, **a feltöltés
pontos helye (2026-08-30, dekompilált + assembly):**

```asm
; 0x00406ee9 — a p1import ág végén (az AppPath-ellenőrzés SIKERÁGA):
lea eax, [ebp+0x1020]             ; ★ a CÉL = +0x1020
lea esi, [esp+0x18]               ; a forrás (a felderített út)
call 0x005c2100                   ; a sztring-másolás a +0x1020-ba
```

A p1import ág logikája (a dekompilált `FUN_00406c00`-ból):

| lépés | utasítás | mi történik |
|---|---|---|
| 1 | `FUN_00981c30()` → `FUN_00406770()` | **Windows Vista+** (GetVersionExA, major 6) → a **Windows.old**-felderítő is fut |
| 2 | `FUN_00992db0("#db3\\")` → `[+0x101c]` | a **`#db3\` mappa megléte** a `[+0x101c]` bájtba |
| 3 | Ctrl+Shift+Alt → `IDS_DB_DELETE_WARNING` → `[+0x101d]` | a törlés-jelző (nem a panel része) |
| 4 | **p1import**: ha nincs `Preferences\p1import` **és** `[+0x101c]==0` | Lifescape-registry (`SOFTWARE\Lifescape Solutions Inc.\Picasa\Runtime\`) → `AppPath` beolvasása → ha érvényes és a felderített út létezik → **`[+0x1020] = az út`** |
| 5 | **p2import**: ha nincs `Preferences\p2import` **és** `[+0x101c]==0` | `FUN_00994400(...)` → `[+0x101c] = (eredmény == 0)` — a `#db2\` megléte |
| 6 | **p3import**: ugyanaz a minta | `[+0x101c] = (eredmény == 0)` |

A felderítés forrásai:

| forrás | mi ez |
|---|---|
| **`SOFTWARE\Lifescape Solutions Inc.\Picasa\Runtime\`** | a **Picasa 1** (Lifescape) registry-ága + `AppPath` |
| **`#db2\`** | a **régi** adatbázismappa (a mai a `#db3\`) |
| **`p1import` / `p2import` / `p3import`** | `Preferences`-jelzők: Picasa 1 / 2 / 3 importja |
| **`C:\Windows.old\Documents and Settings\$$\Local Settings\Application Data\Google\`** (+ `Picasa2Albums`) | **Windows.old-migráció** (Vista-fejlesztői felderítés, a `FUN_00406770` — **új a specben**) |
| `index-thumbs.db`, `thumbs_index.db` | a régi indexfájlok |

*(Ugyanitt lakik az `IDS_DB_DELETE_WARNING` az **„Adatbázis törlése" /
„Ne törölje"** gombokkal, és egy „special key combination" indítási
mód szövege — ezek nem az `initialscan` részei.)*

> **A `skipinitialscan` kihagyás a SZŰKÍTETT választással egyenértékű:**
> az indulás-rutin ilyenkor `[ebx] = 1`-et ír (`0x0040d506`), és ugyanaz
> az ág fut, mint a felhasználó „csak ezek a mappák" választásánál.

*Bizonyítottsági fok: **megerősített** a döntési szabályra (a konstruktor
és az indulás-rutin minden utasítása — dekompilálva
`script-DecompileInitialscan.log` [659] és az assembly
`00403ebe LEA EDX,[EBX+0x101c]`), a felderítő forrásaira (a
`0x00406c00` sztringkészlete) **és** a `+0x1020` feltöltésének pontos
helyére (`0x00406ee9`–`0x00406ef3`: `LEA EAX,[EBP+0x1020]` +
`call 0x005c2100`). Új, korábban nem dokumentált részlet: a
**Windows.old**-felderítő (`FUN_00406770`, `C:\Windows.old\...\Google\`
+ `Picasa2Albums`), ami **csak Windows Vista+** rendszereken fut
(`FUN_00981c30` = `GetVersionExA`, major 6).*

### 6.7 Hol jelenik meg, és mi történik bezáráskor (U3)

**Saját, MODÁLIS ablak** — nem a főablakba ágyazott panel:

```asm
; 0x0040e410
0x0040e433  push 0x278 / 0x97c5d0        ; 0x278 bajtos objektum foglalasa
0x0040e45c  call 0x5b7610                ; konstruktor
0x0040e46e  ... [eax+0x6c]               ; a FOABLAK HWND-je (szulo)
0x0040e476  push "initialscan"
0x0040e47c  call 0x9d4a80                ; a kozos MODALIS megjelenito (11 hivo)
```

A `0x005b75c0` (a vtábla 30. slotja) az ablak **nevét** adja vissza
(`[dlg+0x260]`, alapértelmezés üres sztring), a `[dlg+0x258]` pedig a
modális hurok objektuma.

#### Bezárásra a panel −1-et ír — és az indulás MEGSZAKÍTOTTNAK számít

A `0x005b7da0` (a vtábla 22. slotja) az értesítéseket kezeli. A
**`0x08000002`** osztályban a nevet a **`"CloseModal"`** sztringgel veti
össze, és egyezés esetén:

```asm
0x005b7e2d  [dlg+0x268] = 0            ; a "fut" jelzo torlese
0x005b7e3f  [dlg+0x258]->vt[5](0, 0)   ; a MODALIS HUROK leallitasa
0x005b7e47  0x9dfa10( [dlg+0x14c] )
0x005b7e56  *[dlg+0x25c] = 0
0x005b7e63  eax = [dlg+0x270]          ; a KIMENETI REKESZ
0x005b7e69  *eax = 0xFFFFFFFF          ; ← −1 = MEGSZAKITVA
0x005b7e6f  return 0xF4241
```

és az indulás-rutin pontosan ezt nézi:

```asm
0x0040d56d  cmp dword ptr [ebx], -1
0x0040d570  jne 0x40d58c
0x0040d572  mov eax, 0xf4242           ; "megszakitva" visszateres
```

> **Vagyis a Mégse gomb rejtett (2. szakasz), de az ABLAK BEZÁRÁSA mégis
> megszakít** — és az indulás **nem folytatódik** a beolvasás-beállítással
> (`0x0040d572`, `0xF4242`). A választás tehát nem „kikényszerített",
> hanem: **vagy választasz, vagy az indulási lépés megszakad.**

*Bizonyítottsági fok: **megerősített** — a megjelenítés útja, a
`CloseModal` ág minden utasítása, és az indulás-rutin −1-ellenőrzése.*

