# A nyomtatás — panel, méretek, beállítások

Az eredeti Picasa nyomtatási felülete három erőforrásból áll:
**`printpanel.tre`** (261 sor, **61 elem**), **`printoptions.tre`** és
**`printoptionstext.tre`** (80 sor, a feliratok).

A funkció a PicasaPy-ban a „később mérlegelendő" körbe tartozik
(`feature-map.md`), de a specifikációja ezzel megvan.

## A 17 nyomtatási méret — `ytPrintSizes`

| kulcs | EN | HU |
|---|---|---|
| `e3x4` | 3 x 4 | **3x4** |
| `e3x5` | 3.5 x 5 | **3,5x5** |
| `e4x5` | 4 x 5 | **4x5** |
| `e4x6` | 4 x 6 | **4x6** |
| `e5x7` | 5 x 7 | **5x7** |
| `e8x10` | 8 x 10 | **8x10** |
| `e5x8cm` | 5 x 8 cm | **5x8 cm** |
| `e9x13cm` | 9 x 13 cm | **9x13 cm** |
| `e10x15cm` | 10 x 15 cm | **10x15 cm** |
| `e13x18cm` | 13 x 18 cm | **13x18 cm** |
| `e15x20cm` | 15 x 20 cm | **15x20 cm** |
| `e20x25cm` | 20 x 25 cm | **20x25 cm** |
| `eWallet` | Wallet | **Tárcaméret** |
| `eCDSize` | CD Cover Size | **CD-borító mérete** |
| `ePassport` | Passport | **Útlevél** |
| `eContact` | Contact Sheet | **Indexképek** |
| `eFullPage` | FullPage | **FullPage** *(lefordítatlan az eredetiben is!)* |

> ⚠️ Az **`eFullPage`** magyar szövege maga is „FullPage" — a Google
> fordítói kihagyták. A `AspectRatioList::A4Page:Description` viszont
> **„Teljes oldal"**.

A panelen **öt** gyorsgomb van hozzájuk: `3x5button`, `4x6button`,
`5x7button`, `8x10button`, `walletbutton`, plus `fullbutton`.

## A panel elemei csoportonként

**Méret-gombok (6):** `3x5button` · `4x6button` · `5x7button` ·
`8x10button` · `walletbutton` · `fullbutton`

**Előnézet (7):** `preview` · `previewbase` · `previewclip` ·
`previewnumber` · `previewnumbercontainer` · `previewlabel_bg` ·
`printlayoutlabel` (+ `_bg`) — a felirat `m_displayfont18_Reg`

**Navigáció (3):** `navcontainer` · `prevbutton` · `nextbutton`

**Példányszám (4):** `numberprints` · `copieslabel` · `copiesicon` ·
`addprintsbutton` (+ ikon) · `subprintsbutton` (+ ikon)

**Vágás/illesztés (7):** `croptoggle` (+ ikon, felirat, alap) ·
`fittoggle` (+ ikon, felirat, alap) · `cropcontainer`

**Nyomtató (6):** `printerlabel` · `printername` · `selectprinterbutton`
(+ ikon) · `psetupbutton` (+ ikon) · `printsetuplabel` · `setuplabel` ·
`paperinfo`

**Cselekvés (8):** `pnowbutton` · `pnowbutton2` · `pcancelbutton` ·
`reviewnowbutton` · `reviewnowbutton2` (+ ikon) · `ok_icon` · `ok_icon2` ·
`cancel_icon`

**Egyéb:** `captionoptionsbutton` (+ ikon, felirat) · `statustext` ·
`leftcontainer` · `leftbuttcontainer` · `leftdivider` · `froogle` ·
`phelpbutton`

> A **`phelpbutton`** teljesen ki van kommentezva (ikon, felirat, horgony),
> csak `m_render_offscreen` maradt — vagyis a **súgó gomb elhagyott**.
> A **`froogle`** a Google vásárlás-keresőjére mutató gomb — szintén
> halott szolgáltatás.

## A minőség-visszajelzés: három sáv

| erőforrás | HU |
|---|---|
| `CPrintDlg::bestqual` | **Legjobb minőség (%d képpont/hüvelyk)** |
| `CPrintDlg::goodqual` | **Jó minőség (%d képpont/hüvelyk)** |
| `CPrintDlg::badqual` | **Rossz minőség (%d képpont/hüvelyk)** |

A Picasa tehát **képenként kiírta a tényleges DPI-t**, és három sávba
sorolta. Ehhez tartozik a figyelmeztetés:

> `CPrintDlg::toosmall` — „Néhány kép túl kicsi a jó minőségű
> nyomtatáshoz. Ezeket a képeket eltávolíthatja, kinyomtathatja, vagy
> visszavonhatja és módosíthatja a nyomtatási méretet."

## A nyomtatási beállítások párbeszéd

`printoptionstext.tre` — **21 felirat**, mind **angolul** (ez a fájl nem
került át a fordítható erőforrásokba):

| terület | feliratok |
|---|---|
| gombok | Apply · OK · Cancel (mindháromhoz súgóval) |
| keret | Border · Border width · None · Max. · Border color · **Even width border** |
| felirat | Captions · No text · Caption · File name · **Exif information** · Text Color · Font · Size · Wrap text |
| elhelyezés | Below image · On image · On border · **Bottom only** |
| tiltás | „Sorry, but these options cannot be used when printing contact sheets." |

**Négy feliratforrás közül lehet választani:** nincs szöveg · felirat ·
fájlnév · **EXIF-adatok**. Az elhelyezés: kép alatt · képen · kereten.

## A három nyomtatási beállítás-kulcs

| kulcs | hol | mit |
|---|---|---|
| `PrinterQuality` | `0x006e0cb0`, `0x006e1100` | a nyomtató minőségi módja |
| `PrintResamplerQuality` | ugyanott | az **átméretező** minősége nyomtatáskor |
| `PrintProxyPreview` | ugyanott, alapérték **1** | előnézet proxyval |

*Bizonyítottsági fok: megerősített* (a három erőforrásfájl teljes
tartalma és a 17 `ytPrintSizes` bejegyzés).
