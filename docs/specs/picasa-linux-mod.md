# A Picasa 3.9 LINUX-módja — amit maga a Google letiltott

A windowsos `Picasa3.exe` **tartalmazza a Linux-változat ágait is**: ugyanaz
a forrás fordult mindkét platformra, és a különbség **futásidőben** dől el.
Ez a lap azt gyűjti össze, mit tesz a program másképp Linuxon — ez egy
Linux-first újraírásnál közvetlenül hasznos, mert megmutatja, **mit tartott
maga a Google megvalósíthatatlannak** azon a platformon.

## Hogyan ismeri fel, hogy Linuxon fut

A Picasa Linuxon **Wine alatt** futott. A felismerés:

```
GetProcAddress(GetModuleHandle("kernel32"), "wine_get_unix_file_name")
```

A `wine_get_unix_file_name` sztringre a binárisban **tizenhárom** függvény
hivatkozik: `0x00403640`, `0x0040d3c0`, `0x004b1c80`, `0x005643e0`,
`0x00678be0`, `0x00678e80`, `0x006e0410`, `0x00738c00`, `0x0073a140`,
`0x0097e1e0`, `0x00981ea0`, `0x00982060`, `0x00990ee0`.

Ha az eljárás megvan → Wine → **Linux-mód**.

## Amit Linuxon LETILT

Egyetlen üzenet fedi mindkét esetet:

| erőforrás | EN | HU |
|---|---|---|
| `LinuxNomovie` | This feature is not supported for Linux | **A program ezt a funkciót Linux rendszeren nem támogatja** |

### 1. Klip-export (`0x0053a460`, 805 bájt)

A videóklipek exportálása. A célmappa neve:
`CThumbUI::MovieClipFolder` → „Exported Videos" / **„Exportált videoklipek"**.

### 2. Film készítése (`0x0057cb60`, 327 bájt)

A `panelroot/makemoviepanel` és a `panelroot/makemovietab` megnyitása.
**Ugyanez a függvény egy MÁSIK platformot is kizár:**

| erőforrás | EN | HU |
|---|---|---|
| `Win2kNomovie` | This feature is not supported for Windows 2000 | **A program ezt a funkciót Windows 2000 rendszeren nem támogatja** |

## A kiskapu: `EnableLinuxMovie`

A tiltás **feloldható** egy rejtett beállítással:

| kulcs | hol olvassák |
|---|---|
| `EnableLinuxMovie` | `0x005643e0` (a rejtett beállítások olvasója), `0x00794460` (az export útvonala) |

Vagyis a Google maga is tudta, hogy a funkció **elvileg működne** Linuxon —
csak nem vállalta a támogatását.

## Öt további rejtett beállítás, ami a 39-es listán nincs rajta

A `0x005643e0` (3 562 bájt) a `Preferences` alatt ezeket is olvassa:

| kulcs | mire utal |
|---|---|
| `ShowHidden` | rejtett képek mutatása (a Nézet menü `ID_VIEW_SHOWHIDDEN` tétele: **„Rejtett képek"**) |
| `SlideshowEffectTime` | a diavetítés áttűnési ideje |
| `captionmode` | a felirat megjelenítési módja |
| `EnableHover` | egér-alatti kiemelés |
| `EXEPath` | a program útvonala |

*(A `SingleClickExit` már szerepelt a `0x006e0cb0` regisztrálójában.)*

Ugyanez a függvény olvassa a `SOFTWARE\Google\Picasa\PicasaNet\`
registry-ágat is.

## Külön About-szöveg Linuxra

| erőforrás | tartalom |
|---|---|
| `IDS_ABOUT_LINUX` | „Picasa %s Linux rendszerhez." + a teljes szerzői jogi blokk (Copyright 2003–**2013**) |
| `IDS_BUILDNUMBER_LINUX` | „ (Build %s)" |
| `Linux_%s`, `Linux_Unknown`, `%s (linux)` | a platform jelentése a statisztikában |

## Amit ebből a PicasaPy visz

| | Picasa Linuxon | PicasaPy |
|---|---|---|
| klip-export | **letiltva** | nincs okunk letiltani — natív Linux-alkalmazás vagyunk |
| film készítése | **letiltva** | ugyanez |
| a tiltás oka | Wine-korlát (kodek/DirectShow) | nálunk nem áll fenn |

**Ez a lap tehát nem követendő minta, hanem magyarázat:** ha valaki azt
mondja, „az eredeti Picasában Linuxon nem volt filmkészítés", az igaz — de
platform-korlát volt, nem tervezési döntés. A funkció a Windows-változatban
teljes értékű, és a `.mxf` projektfájl formátuma is ugyanaz.

*Bizonyítottsági fok: megerősített* (a két tiltó függvény, a feloldó
beállítás mindkét olvasóhelye, és a Wine-felismerés tizenhárom hivatkozása).

## A Wine-felismerés mechanikája és a `ShowUnixPaths` (2026-08-16)

### A felismerés egyszer fut le, és eltárolódik

```asm
0x0073a17f  test byte ptr [0xd6fc64], 1     ; már megvizsgáltuk?
0x0073a186  mov  esi, 1
0x0073a18b  jne  0x73a1b3                    ; igen → ugrás a gyorsítótárazott értékre
0x0073a18d  or   dword ptr [0xd6fc64], esi   ; jelöljük, hogy megvizsgáltuk
0x0073a193  push 0xca99b4                    ; "wine_get_unix_file_name"
0x0073a198  push 0xca99a8                    ; "kernel32"
0x0073a19d  call dword ptr [0xc40238]        ; GetModuleHandleA
0x0073a1a4  call dword ptr [0xc40234]        ; GetProcAddress
0x0073a1ac  setne byte ptr [0xd6fc60]        ; ← a gyorsítótárazott „Wine?" jelző
```

| cím | jelentés |
|---|---|
| `0xd6fc60` | **a gyorsítótárazott „Wine alatt futunk" jelző** (1 bájt) |
| `0xd6fc64` bit 0 | „a vizsgálat már lefutott" |

A vizsgálat tehát **egyszer** fut le a program életében, utána a
`0xd6fc60`-ból olvassák. Ez magyarázza, miért hivatkozik a sztringre
tizenhárom függvény: mindegyik ugyanezt a mintát tartalmazza (inline-olt
segédfüggvény).

Egy tizennegyedik hely (`0x006e0410`) egy **második** Wine-API-t is keres:
`wine_get_unix_real_name`.

### `ShowUnixPaths` — Linuxon alapból BE

```asm
0x0073a1b3  cmp  byte ptr [0xd6fc60], 0
0x0073a1ba  je   0x73a1ef                    ; NEM Wine → az egész ág kimarad
0x0073a1bc  push 0xca4cc8                    ; "ShowUnixPaths"
0x0073a1c1  push 0xc7eafc                    ; "Preferences"
0x0073a1d1  mov  dword ptr [esp+0x1c], esi   ; esi = 1  → ALAPÉRTÉK: 1
0x0073a1d5  mov  dword ptr [esp+0x20], esi
0x0073a1d9  call 0x407a20                    ; a beállítás olvasása
0x0073a1e2  call 0x4019b0                    ; sztring → logikai
```

Két dolog derül ki:

1. **Windowson a beállítást meg sem nézi** — a `ShowUnixPaths` kizárólag
   Wine alatt számít.
2. **Wine alatt az alapérték `1`**: a Picasa Linuxon **alapból UNIX-os
   útvonalakat mutat**, nem `Z:\home\…` alakot.

A kulcsot még két helyen olvassák: `0x00678e80` (a biztonsági mentés
párbeszéde) és `0x00738c00` (az exportálás beállításai) — vagyis az
útvonal-megjelenítés **következetesen** végigmegy a felületen.

### Egy Wine-kompatibilitási megkerülés

`0x0097e1e0` (189 bájt): a Wine-vizsgálat után **kihagyja** a
`Rasapi32.dll` / `RasEnumEntriesA` hívást (a betárcsázós kapcsolatok
felsorolását) — az Wine alatt nem működik.

### A statisztika is jelenti a platformot

`0x00990ee0` (818 bájt): a jelentésbe `%s (linux)` vagy **`%s (wine)`**
kerül, a `proddisplay`, `distro`, `track`, `adminuser`, `appstate` mezők
mellé. A **`distro`** mező szerint a Picasa a Linux-disztribúció nevét is
elküldte.

### Amit ebből a PicasaPy visz

Semmit közvetlenül — natív Linux-alkalmazásként nálunk **nincs kérdés**:
mindig UNIX-útvonalat mutatunk. A lelet értéke az, hogy megerősíti:
**a felhasználó a Picasában is UNIX-útvonalat látott**, tehát ez nem
eltérés az „eredetihez" képest, hanem éppen az egyezés.

*Bizonyítottsági fok: megerősített* (a felismerés és a beállítás-olvasás
teljes egészében kiolvasva, az alapérték a `mov esi, 1`-ből).
