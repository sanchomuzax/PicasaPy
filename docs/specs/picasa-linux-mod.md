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
