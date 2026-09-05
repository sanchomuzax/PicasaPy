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

> A **`phelpbutton`** ikonja, felirata és horgonya ki van kommentezva (a gomb maga NEM — ld. lent),
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

> ⛔ **HELYESBÍTÉS (2026-09-03).** Itt eddig ez állt: *„`printoptionstext.tre`
> — **21 felirat**, mind **angolul** (ez a fájl nem került át a fordítható
> erőforrásokba)"*. **Mindhárom állítás téves:**
>
> | korábbi állítás | a mérés |
> |---|---|
> | „21 felirat" | **26 bejegyzés**: 23 felirat + 3 buboréksúgó |
> | „mind angolul" | **mind MAGYARUL is megvan** — lásd a lenti táblát |
> | „nem került át a fordítható erőforrásokba" | **átkerült**: `i18n\printoptionstext.xml`, kicsomagolva `referencia/i18n-hu/printoptionstext.xml` (4 202 bájt) |
>
> Ez nem apróság: a téves mondat alapján egy fejlesztő **angol feliratokat**
> épített volna a magyar felületre. A **#1780** jegy — helyesen — már a
> hivatalos magyar feliratokkal dolgozik; a lap maradt le.

A párbeszéd **26 honosított szövege**, teljes listával (forrás:
`referencia/i18n-hu/printoptionstext.xml`).

**Szerkezeti horgony** — hol vannak deklarálva: az elemek a
`printoptions.tre`-ben (`printoptions.tre:45` = `border_color_label`,
`printoptions.tre:95` = `caption_label`, `printoptions.tre:115` =
`useexif_label`, `printoptions.tre:197` = `wrap_checkbox_label`), a
feliratok pedig a `printoptionstext.tre`-ben
(`printoptionstext.tre:33` = `border_color_label`,
`printoptionstext.tre:36` = `caption_label`).

*(A horgony nem díszítés: a lefedettségi mérő CSAK olyan szakaszt fogad el
bizonyítékként, amiben van `0x…` cím vagy `fájl:sor` — a
`binaris-regeszet-modszertan.md` 22.4 pontja írja elő. A `.xml`-hivatkozás
sorszám nélkül nem elég, és emiatt e tábla **tizenkét** eleme évekig
„feltáratlannak" látszott. Ld. a 22.5 pontot.)*

| elem (teljes név) | típus | **hivatalos magyar** |
|---|---|---|
| `printoptions/apply` | felirat | **Alkalmaz** |
| `printoptions/apply` | buboréksúgó | *A kijelölt beállítások alkalmazása a Google Fotókra* ⚠️ |
| `printoptions/ok` | felirat | **OK** |
| `printoptions/ok` | buboréksúgó | *A kijelölt beállítások alkalmazása a Google Fotókra, és a párbeszédpanel bezárása* ⚠️ |
| `printoptions/cancel` | felirat | **Mégse** |
| `printoptions/cancel` | buboréksúgó | A párbeszédpanel bezárása mentés nélkül |
| `printoptions/border_label` | felirat | **Szegély** |
| `printoptions/border_size_label` | felirat | Szegély szélessége |
| `printoptions/border_none_label` | felirat | Egyik sem |
| `printoptions/border_max_label` | felirat | Maximális |
| `printoptions/border_color_label` | felirat | Szegély színe |
| `printoptions/caption_label` | felirat | **Képfeliratok** |
| `printoptions/usenotext_label` | felirat | Nincs szöveg |
| `printoptions/usecaption_label` | felirat | Képfelirat |
| `printoptions/usefilename_label` | felirat | Fájlnév |
| `printoptions/useexif_label` | felirat | Exif-adatok |
| `printoptions/caption_color_label` | felirat | Szöveg színe |
| `printoptions/caption_font_label` | felirat | Betűtípus |
| `printoptions/caption_size_label` | felirat | Méret |
| `printoptions/wrap_checkbox_label` | felirat | Szöveg tördelése |
| `printoptions/textbelowimage_label` | felirat | A kép alatt |
| `printoptions/textonimage_label` | felirat | A képen |
| `printoptions/textonborder_label` | felirat | A szegélyen |
| `printoptions/bottomonly_checkbox_label` | felirat | Csak alul |
| `printoptions/evenwidth_checkbox_label` | felirat | Egyenletes szélességű szegély |
| `printoptions/disabled_label` | felirat | Ezek a beállítások indexképek nyomtatásakor nem használhatók. |

⚠️ **A három gomb-buboréksúgóból kettő HIBÁS az eredeti magyar fordításban:**
az `apply` és az `ok` súgója **„a Google Fotókra"** alkalmazásról beszél,
miközben a párbeszéd a **nyomat szegélyét és feliratát** állítja — a Google
Fotókhoz semmi köze. (Az angol eredeti is „the selected photos"-t mond, tehát
a magyar fordító a *photos*-t vette Google Fotóknak.) **Javaslat:**
nálunk a helyes szöveg — *„A kijelölt beállítások alkalmazása a kijelölt
képekre"* —, és a jegyben mondjuk ki, hogy ez **szándékos eltérés az
eredetitől**, mert az eredeti fordítás hibás.

**Négy feliratforrás közül lehet választani:** nincs szöveg · képfelirat ·
fájlnév · **Exif-adatok**. Az elhelyezés: a kép alatt · a képen · a szegélyen.

## A három nyomtatási beállítás-kulcs

| kulcs | hol | mit |
|---|---|---|
| `PrinterQuality` | `0x006e0cb0`, `0x006e1100` | a nyomtató minőségi módja |
| `PrintResamplerQuality` | ugyanott | az **átméretező** minősége nyomtatáskor |
| `PrintProxyPreview` | ugyanott, alapérték **1** | előnézet proxyval |

*Bizonyítottsági fok: megerősített* (a három erőforrásfájl teljes
tartalma és a 17 `ytPrintSizes` bejegyzés).

---

## A panel ALSÓ AKCIÓGOMBJAI — mit csinálnak (2026-09-03)

A „A panel elemei csoportonként" szakasz **felsorolta** ezeket, de a
működésüket nem írta le. A hat elem teljes nevén (a lefedettségi mérő ezt
keresi):

### `printpanel/psetupbutton` + `printpanel/setuplabel` — „Nyomtató telepítése"

A gomb a **Windows nyomtató-tulajdonságok párbeszédét** nyitja meg, a
klasszikus háromlépéses mintával (`0x00861750`, 302 b):

```
0x00861778  call OpenPrinterA          (WINSPOOL.DRV, IAT 0x00c409f0)
0x008617b9  call DocumentPropertiesA   (méretlekérdezés)
0x00861816  call DocumentPropertiesA   (a párbeszéd megjelenítése)
```

A `ClosePrinter` külön függvényben (`0x008612e0`, 205 b, hívás
`0x00861311`); egy további `DocumentPropertiesA`-hívás a `0x00861880`-ban
(152 b).

⇒ **Ez nem Picasa-párbeszéd, hanem az illesztőprogramé.** Linuxon a
megfelelője a Qt/CUPS nyomtató-tulajdonságok — a felirat („Nyomtató
telepítése") megtartható, a tartalom a rendszeré.

✅ **Megvalósítva (#2103, 2026-09-04).** A nyomtatóválasztó mellett ott a
gomb (`printPrinterSetupButton`), a mért feliratokkal:

| | angol (`ui-leltar.csv`) | magyar (`tooltips.xml`) |
|---|---|---|
| felirat | `Printer Setup` | **Nyomtató telepítése** |
| buboréksúgó | `Open printer setup controls for the selected printer` | **Nyomtató beállításvezérlőinek megnyitása a kijelölt nyomtatóhoz** |

A gomb a `QPageSetupDialog`-ot nyitja a kiválasztott nyomtatóra, és az
**elfogadott oldalelrendezést a következő nyomtatás használja**
(`PrintController._oldalelrendezes`). PDF-célnál **inaktív** — ott nincs
illesztőprogram, tehát nincs mit beállítani.

⚠️ A tartalom továbbra sem másolható: a `DocumentProperties` a Windows
illesztőprogramé. Ami átvehető, az a **belépési pont** — a gomb helye és
felirata.

Őr: `tests/app/qml_functional/test_nyomtato_telepites_2103.py`. Külön
próba méri, hogy a nyomtatás tényleg a beállítóban elfogadott elrendezéssel
indul — enélkül a párbeszéd díszlet lenne (ezt a hiányt magvetés fedte fel:
a bekötés törlésére előbb egyetlen próba sem bukott el).

### `printpanel/captionoptionsbutton` + `printpanel/captionoptionslabel`

Felirat: **„Szegély- és szövegopciók"**, buboréksúgó: *„Configure borders and
text for Photos to be printed"*. Ez nyitja a fenti **`printoptions`**
párbeszédet (26 honosított szöveg, 11 tartós beállítás — **#1780**).

Deklaráció: `printpanel.tre:54` (a gomb), `:46` (a felirat), `:51` (az ikon);
a panel vezérlő-listájában: `0x00743980`. A rajza rendes gomb-hármas
(`globalbuttons/ppaction_n` / `_p` / `_h`), tehát **látható és él**.

### `printpanel/froogle` — „Tartozékok keresése a Froogle-en"

**Megerősítést kér, majd böngészőt nyit.** Mérve (`0x00743980`, `0x00744a00`):

| mit | érték |
|---|---|
| megerősítő szöveg | `ThumbUIPrint::FrooglePrompt` — **„Ez a funkció nyomtatókellékeket keres a Froogle szolgáltatásban. A következőt küldjük: \"%s\". Ezt szeretné?"** |
| a `%s` | a **nyomtató neve** |
| a megnyitott cím | **`https://uploader.picasa.com/froogle.php?q=%s`** |

Deklaráció: `printpanel.tre:246` (a gomb), `:244` (a felirat) — **nincs
kikommentezve**, a respackben `superbutton(button_text_center,froogle)`,
tehát látható.

⇒ **Adatvédelmi szempontból nem semleges gomb** (a nyomtató nevét elküldi egy
Google-kiszolgálóra), és a Froogle **megszűnt** (2013). **HATÓKÖRÖN KÍVÜL** —
eldöntötte: ez a kör, 2026-09-03; a megszűnt szolgáltatás miatt nem
építjük meg.

### `printpanel/phelpbutton` — „Súgó": a gomb ÉL, de nincs se ikonja, se felirata

> ⛔ **HELYESBÍTÉS (2026-09-03).** A lap eddig azt írta, hogy a gomb
> „**teljesen** ki van kommentezva (ikon, felirat, horgony)". A `.tre` sorai
> ennél pontosabbak (`printpanel.tre:235–241`):
>
> ```
> #printpanel/phelpbutton_icon: printpanel/phelpbutton      <- kikommentezve
> #printpanel/phelpbutton-label: printpanel/phelpbutton     <- kikommentezve
> printpanel/phelpbutton: root                              <- ÉL
> #m_buttontypecolor                                        <- kikommentezve
> #m_offsetLB                                               <- kikommentezve
> m_render_offscreen                                        <- él
> ```
>
> ⇒ **Maga az elem NINCS kikommentezva** — csak az ikonja, a felirata, a
> színe és a horgonya. A `respack.yt` szerint **`vbutton`** (rajz nélküli,
> láthatatlan találati terület), horgony nélkül, tehát a szülő bal-felső
> sarkában ül.
>
> **A gyakorlati következtetés ugyanaz** (nincs használható Súgó gomb), de a
> mechanizmus más: nem törölték, hanem **lecsupaszították**. Ugyanaz a minta,
> mint a `thumbui/prev`/`next`-nél
> ([`konyvtar-ablak-meretek.md`](konyvtar-ablak-meretek.md) 4.1) — és ott is
> a `.tre` sorainak EGYENKÉNTI olvasása döntötte el, nem a blokk egészének
> ránézése.

## KÉT minőségszöveg-család, nem egy

A lap eddig a `CPrintDlg::*qual` hármast írta le. A binárisban **másik,
teljesebb** készlet is van, saját névtérrel — és **ez** tartalmazza az
áttekintő párbeszéd szövegeit:

| erőforrás | angol | **hivatalos magyar** |
|---|---|---|
| `ThumbUIPrint::ReadyPrompt` | You are ready to print. | **Készen áll a nyomtatásra.** |
| `ThumbUIPrint::ReviewPrompt` | Please review before printing.\n%1$d small %2$s found. | **Nézze át nyomtatás előtt.\n%1$d kis %2$s van.** |
| `ThumbUIPrint::ReviewBest` | Best Quality: %s | **Legjobb minőség: %s** |
| `ThumbUIPrint::ReviewGood` | Good Quality: %s | **Jó minőség: %s** |
| `ThumbUIPrint::ReviewLow` | Low Quality: %s | **Alacsony minőség: %s** |
| `ThumbUIPrint::Smallest` | Smallest picture: %d pixels/inch.\n | **Legkisebb kép: %d képpont/hüvelyk\n** |
| `ThumbUIPrint::PrintCount` | %1$d of %2$d | **%2$d / %1$d** *(fordított sorrend!)* |
| `ThumbUIPrint::picture` · `::pictures` | picture · pictures | **kép · kép** |

⚠️ **Két különbség, ami megvalósításkor számít:**

1. A `ThumbUIPrint::ReviewLow` magyarul **„Alacsony minőség"**, míg a
   `CPrintDlg::badqual` **„Rossz minőség"** — a két készlet **nem
   szinonima**, két külön helyen jelenik meg.
2. A `PrintCount` magyar alakja **megcseréli az argumentumokat**
   (`%2$d / %1$d`) — ez ugyanaz a minta, amit a `BackupCopy::1`-nél is
   mértünk ([`biztonsagi-mentes.md`](biztonsagi-mentes.md)). A
   pozicionális argumentumok tehát a magyar fordításban rendszeresen
   cserélődnek: **a formátumsztringet a fordításból kell venni, nem az
   angolból.**

> *Bizonyítottsági fok: **megerősített*** — minden szöveg a
> `referencia/stringres-en-hu.tsv` 2286–2295. és a
> `referencia/i18n-hu/printoptionstext.xml` soraiból, minden cím a
> binárisból kiolvasva.

---

## A „kis kép" KÜSZÖBE: `Preferences\DPIWarning`, alapérték **150** (2026-09-04)

**Bizalmi fok: megerősített** (bináris).

A `printing/dpi.py` modulunk fejléce eddig ezt mondta: *„a küszöb a
hívóláncban van… a **mechanizmust** vesszük át, a **küszöböt** magunk
választjuk"* — és 150-et választott. **Most kimérve: az eredeti
alapértéke is pontosan 150**, és ráadásul **állítható**.

### A számoló: `0x0085c060` (378 b)

| cím | mit tesz |
|---|---|
| `0x0085c076`–`0x0085c07b` | a `Preferences` (`0x00c7eafc`) / **`DPIWarning`** (`0x00cc3368`) kulcs |
| **`0x0085c08b`** | **`mov dword ptr [esp+0x1c], 0x96`** — az **alapérték 150**, ezt kapja a beállításolvasó (`0x00407a20`) |
| `0x0085c098` | `fld dword ptr [0x00cf4900]` = **`1000000.0`** — a minimum-keresés „+végtelen" magva |
| `0x0085c0b2`–`0x0085c120` | a képeken végigmenő ciklus; `0x0085c0cd` `fcom st(1)` tartja a **legkisebb** DPI-t |

⇒ **A küszöb rejtett beállítás**, nem beégetett szám: aki átírja a
`DPIWarning` értéket, más határnál kap figyelmeztetést.

### A panel döntése DARABSZÁM-alapú, nem DPI-alapú

Az állapotsor (`0x00745980`) már **kész számokat** kap:

| cím | mit tesz |
|---|---|
| `0x00745cee` | `call 0x0085c060` — a fenti számoló |
| `0x00745cf3`–`0x00745d0d` | a legkisebb DPI `float`-ból egészre kerekítve (`fistp`) |
| **`0x00745d15`** | **`cmp esi, 0xf4240`** (= 1 000 000) — ha egyenlő, **kimarad** a „Legkisebb kép: …" sor (nem mértünk képet) |
| `0x00745d5c` | ha a kis képek **száma nulla** → **`ThumbUIPrint::ReadyPrompt`** |
| `0x00745d5e` | `cmp edi, 1` — egyes/többes szám (`::picture` / `::pictures`) |
| `0x00745da4` | különben **`ThumbUIPrint::ReviewPrompt`** a darabszámmal |

⇒ A „Készen áll a nyomtatásra" / „Nézze át nyomtatás előtt" váltás
**egyetlen feltétel**: van-e legalább egy küszöb alatti kép. Ezért van a
`.tre`-ben **két gombpár** (`printpanel/pnowbutton` + `pnowbutton2`,
`printpanel/reviewnowbutton` + `reviewnowbutton2`): a panel a két állapot
között cserél.

### ⛔ ÖNHELYESBÍTÉS (2026-09-04): ez a két „melléklelet" DUPLIKÁTUM volt

Itt eddig két állítás állt a `phelpbutton`-ról és a `froogle`-ról. **Mindkettőt
a lap KORÁBBI, pontosabb szakasza már tartalmazta** (2026-09-03, „A panel ALSÓ
AKCIÓGOMBJAI"), és a `phelpbutton`-é ráadásul **pontatlan** volt:

- azt írtam, hogy a gomb „letiltott vezérlő", mert a makrói ki vannak
  kommentezve. A helyes olvasat: **maga az elem NEM** kikommentezett — csak az
  ikonja, a felirata, a színe és a horgonya; a `respack.yt` szerint
  **`vbutton`** (rajz nélküli találati terület). Ld. a „`printpanel/phelpbutton`
  — a gomb ÉL" szakaszt fent, amely ezt már 2026-09-03-án helyesbítette.
- a `froogle`-ról írt „NINCS mérve, hova navigál" ugyanígy elavult: a
  megnyitott cím a lapon **már szerepelt**.

**A tanulság a következő köröknek:** ugyanannak a panelnek a kutatása előtt a
**meglévő spec-szakaszt kell végigolvasni**, nem csak a saját kódunkat
grepelni. Két kör (2026-09-04) ezt kihagyta, és részben újra levezette azt,
ami már le volt írva.

---

## A `printpanel/froogle` KATTINTÁS-ÚTJA (2026-09-04, kiegészítés)

> A gomb **mit csinál**-ja és a **hatókörön kívül** döntés a fenti
> „`printpanel/froogle` — Tartozékok keresése a Froogle-en" szakaszban áll
> (2026-09-03). Ez a szakasz **csak azt teszi hozzá**, amit az nem tartalmazott:
> a kattintás pontos útját és egy önhelyesbítést.

**A kattintás-út:** `0x00743980` (a panel gomb-elosztója) a
`0x0074444e`/`0x00744460`-nál veti össze a kattintott elem nevét a
`printpanel/froogle` literállal (19 bájt, `0x13`), és egyezésnél
`0x007444a4`-nél hívja a **`0x00744750`**-t (326 b):

| cím | mit tesz |
|---|---|
| `0x00744750`–`0x0074475d` | a nyomtató-objektum (`[eax+0xec4]`); ha nincs → `-1` |
| `0x0074475f`–`0x00744774` | nyomtatólista (`[eax+4]`, elemszám `[eax+8]>>1`, index `[eax+0x10]`) ⇒ a kiválasztott nyomtató neve |
| `0x007447e1` | `ThumbUIPrint::FrooglePrompt` |
| `0x00744828` | `call 0x009bac20` — igen/nem; nemre kilép |
| `0x00744848` | `https://uploader.picasa.com/froogle.php?q=%s` |
| `0x0074486b` | `call 0x00981860` — megnyitás |

⛔ **Önhelyesbítés:** a `0x00744a00` **NEM** a gomb kezelője (egy korábbi
mondat annak nevezte). Az a panel **megnyitási/nyomtató-ellenőrző** ága
(`IDS_MUST_INSTALL_PRINTER`), és a froogle-elemre ott csak egy **általános
elem-metódus** fut (`0x00744aaf`: `mov eax,[edx+0x68]; call eax`) — ez a rés a
binárisban **181 helyen, 90 függvényben** fordul elő.

## Két REJTETT nyomtatási beállítás: `PrinterQuality` és `PrinterUseTiles` (2026-09-04)

**Bizalmi fok: megerősített** (bináris; az import IAT-résen át azonosítva).

A panelen van egy eddig dokumentálatlan **minőség-kapcsoló**
(`printpanel/optimizebutton` ↔ `printpanel/normalbutton` /
`printpanel/standardbutton`). Mögötte két `Preferences`-kulcs áll.

### Az állapot eldöntése — `0x00745f80` (212 b)

| cím | mit tesz |
|---|---|
| `0x00745f85`–`0x00745f9a` | **`PrinterQuality`** (`0x00ca9a18`), **alapérték `2`** |
| `0x00745fa7`–`0x00745fbe` | **`PrinterUseTiles`** (`0x00cb0cb4`), **alapérték `0`** |
| `0x00745fd0` | `cmp eax, 0x3e9` (**1001**) — egyezésnél **hamis** |
| `0x00745fe0` | `test eax, eax` — nullánál **hamis** |
| `0x00746014` | különben **igaz** (`mov al, 1`) |

⇒ **„Optimalizált" állapot csak akkor, ha `PrinterQuality ≠ 1001` ÉS
`PrinterUseTiles ≠ 0`.** Mivel a `PrinterUseTiles` alapértéke **0**, a
panel **alapból a „normál" gombot** mutatja.

### A kapcsoló írója — `0x00746060` (270 b)

`0x0074609e` és `0x007460bc`: **mindkét kulcsot** kiírja, majd
`0x0074612e`: `call 0x008613b0` — vagyis a változást **azonnal
érvényesíti** a nyomtatási motorban.

### Hova jut el a `PrinterQuality` — a nyomtató KÉPESSÉG-lekérdezésébe

`0x008614a0` (390 b) beolvassa a `PrinterQuality`-t (`0x008614aa`,
alapérték szintén **2**: `0x008613e9`), majd `0x00861536`-nál
`mov edi, dword ptr [0x00c40108]` — ez az IAT-rés, amely a mérés szerint a
**`GetDeviceCaps`**-re mutat *(a „GetDeviceCaps” hint/name RVA `0x009234c4`
épp ebben a résben áll)*. Az `edi`-n át átadott indexek sorban:

| index | a Windows dokumentált jelentése |
|---:|---|
| `0x0a` = **10** | `VERTRES` |
| `0x58` = **88** | `LOGPIXELSX` |
| `0x5a` = **90** | `LOGPIXELSY` |
| `0x6e` = **110** | `PHYSICALWIDTH` |
| `0x6f` = **111** | `PHYSICALHEIGHT` |
| `0x70` = **112** | `PHYSICALOFFSETX` |
| `0x71` = **113** | `PHYSICALOFFSETY` |

⇒ A `PrinterQuality` a **nyomtatható terület és a felbontás**
kiszámításában vesz részt — tehát azt befolyásolja, **milyen felbontáson
rajzolódik a lap**.

### ⛔ KIMERÍTŐ NEGATÍV: a `PrinterUseTiles` nem jut el a rajzolásig

A `PrinterUseTiles` kulcsnak a binárisban **pontosan két** hivatkozója van:
`0x00745f80` (a panel állapota) és `0x00746060` (az író). **Egyik sem a
nyomtatási motor.** A neve ellenére tehát ebben a kiadásban a
csempézett rajzolást **nem** kapcsolja — csak a panel gombállapotát.

*(Összevetésül: a `PrinterQuality`-nak nyolc hivatkozója van, köztük három
a motorban: `0x00861190`, `0x008613b0`, `0x008614a0`.)*

### Nálunk (mérve, 2026-09-04)

`app/print_controller.py:531`, `:816` — a `QPrinter.resolution()` és a
`pageRect(DevicePixel)` adja a lapméretet; **minőség-kapcsoló nincs**, és a
`PrintDialog.qml` `quality` tulajdonsága a **DPI-figyelmeztetésé**, nem
ezé a beállításé.

---

## Az INDEXKÉP (Contact Sheet) — három belépési pont és a hivatalos feliratok (2026-09-04)

**Bizalmi fok: megerősített** (bináris + `stringres-en-hu.tsv`).

Az indexkép nem egy funkció, hanem **három külön belépési pont** ugyanarra a
fogalomra. A `printpanel/photoindexbutton` eddig sehol nem szerepelt a
lapon és a lefedettségi leltárban sem.

### 1. Nyomtatási MÉRET a panelen

`ytPrintSizes::eContact` (`0x00775ce0`) a többi méret mellett; a súgója
`ytPrintTip::eContact` (`0x00775f30`): *„Print pictures as a Contact
Sheet"*. A panel gombja: **`printpanel/photoindexbutton`** (a
`0x00743980` gomb-elosztójában).

### 2. KOLLÁZS-típus

`0x0082e8b0` (2165 b) hat kollázstípust regisztrál — `picturepile`,
`picturegrid`, `regulargrid`, `multiexp`, **`contactsheet`**, `framegrid` —
ikonnal és leírással: `collagepanel/#contact_sheet_icon`,
`collage::csheet_desc`.

### 3. MENÜPARANCS

`eMenuLabelFolder::ID_FILE_PRINTCONTACTSHEET` — a menüépítőben
(`0x00559150`) **`&Print Contact Sheet...`**.

### ⛳ A hivatalos MAGYAR feliratok (a `stringres-en-hu.tsv`-ből)

| erőforráskulcs | angol | **hivatalos magyar** |
|---|---|---|
| `eMenuLabelFolder::ID_FILE_PRINTCONTACTSHEET` | `&Print Contact Sheet...` | **`&Indexképek nyomtatása...`** |
| `ytPrintSizes::eContact` | Contact Sheet | **Indexképek** |
| `CollageType::eContactSheet` | Contact Sheet | **Indexképek** |
| `collage::csheet_desc` | Contact Sheet:  Thumbnails with an informative header | **Indexkép: Miniatűr tájékoztató jellegű fejléccel** |
| `buttonlabel:{BB850B65-96B6-4e41-A2AE-77DE38A82D24}` | Contact Sheet | **Indexképek** |
| `buttontooltip:{BB850B65-…}` | Print a contact sheet | **Indexkép nyomtatása** |
| `IDS_CONFIRM_CONTACTSHEET` | This will create a contact sheet of all the images in the album as a new image.\r\nDo you want to continue? | **Ezzel a művelettel az összes képből egy indexképet hoz létre az albumban új képként.\r\nFolytatja?** |

⚠️ **A magyar szó mindenütt „indexkép", soha nem „bélyegkép".**

### Egy kuriózum: a `ginormous.jpg` út

`0x0057b050` (1225 b, egyetlen hívóval: `0x005e652c`) képet állít elő,
**`ginormous.jpg`** néven kiírja (`0x0057b3f6`), majd
`0x0057b471`–`0x0057b477`: `"open"` + `ShellExecute` (`0x00c405e0`) —
megnyitja. A folyamatjelző szövege *„Making The Ginormous Contact
Sheet!"*, és a **kulcs-névtere `UNUSED!`** (`0x0057b1ce`) — vagyis a
szövegtár maga jelöli használaton kívülinek.

*(Hogy a `0x9c94` menüparancs melyik ághoz tartozik, NINCS mérve: a
parancsazonosító a `0x0056e1c0` elosztóban áll, a `ginormous`-út hívója
viszont a `0x005e60d0`-ban — két külön elosztó.)*

---

## A panel INFORMÁCIÓS mezői — mit ír ki és miből (`0x00745980`, 2026-09-04)

**Bizalmi fok: megerősített** (bináris). Ezt a szakaszt a lap eddig **nem
tartalmazta**: a `numberprints`, `previewnumber`, `printername`, `paperinfo`
és `statustext` elemekről sehol nem volt szó.

A panel állapotfrissítője (`0x00745980`, 1484 b) **egyetlen menetben**
állítja be a következőket:

| cím | elem / erőforrás | segédfüggvény |
|---|---|---|
| `0x00745aa4` | `printpanel/croptoggle` | `0x009cd9a0` |
| `0x00745ac4` | **`IDS_COPIES`** (erőforrás-azonosító **`0x3b` = 59**), az érték a `[ecx+0x20]`-ból | — |
| `0x00745af5` | **`printpanel/numberprints`** | `0x009cd080` |
| `0x00745b7c` | **`ThumbUIPrint::PrintCount`** = **`%d of %d`** | — |
| `0x00745bba` | **`printpanel/previewnumber`** | `0x009cd870` |
| `0x00745bcc` | **`printpanel/printername`** | `0x009cd870` |
| `0x00745bde` | **`printpanel/paperinfo`** | `0x009cd870` |
| `0x00745c05` | `printpanel/nextbutton` | `0x009cd7e0` |
| `0x00745c29` | `printpanel/prevbutton` | `0x009cd7e0` |
| `0x00745e01` + `0x00745e10` | **`printpanel/statustext`** | `0x009cd760`, majd `0x009cd870` |
| `0x00745e1d`–`0x00745e46` | `pnowbutton`, `pnowbutton2`, `reviewnowbutton`, `reviewnowbutton2` | `0x009cd110` |

**A segédfüggvények csoportosítanak** (ez maga is bizonyíték): a
`printername`, `paperinfo`, `previewnumber` és `statustext` **ugyanazt a
`0x009cd870`-et** kapja ⇒ ez a **szövegbeállító**; a négy akciógomb
mind a `0x009cd110`-et ⇒ az a **gomb-állapot**; a két lapozógomb a
`0x009cd7e0`-et.

### A lapszámlálás és a lapozó KORLÁTOZÁSA

`0x00745b52`–`0x00745b76`:

- a lapok száma **`[esi+0x18] >> 1`** (csomagolt elemszám, `edi`);
- ha **nulla**, a program meghívja a `0x007774b0(objektum, 1)`-et — vagyis
  előállít egy lapot;
- az **aktuális lapindex** (`[ebp+0xec8]`) **a lapszám−1-re korlátozódik**
  (`0x00745b73`: `lea eax, [edi-1]`), ha kifutna a tartományból.

⇒ A `%d of %d` tehát **aktuális lap + 1 / összes lap**, és a panel a
lapszám csökkenésekor **magától visszaigazítja** a lapozót.

### Nálunk (mérve, 2026-09-04)

| mező | eredeti | nálunk (`PrintDialog.qml`) |
|---|---|---|
| példányszám | `IDS_COPIES` + `numberprints` | megvan (`:373`, #1819) |
| lapszám | `%d of %d` → `previewnumber` | megvan (`:466`, `%1 / %2`, magyar cserével) |
| nyomtató neve | `printername` | megvan (`printerName`, `:72`) |
| **papíradatok** | **`paperinfo`** | **NINCS** — a `PrintDialog.qml`-ben nincs papírméret-kijelző (a `print_controller.py:314` `pageLayout()`-ja megvan, de nem jelenik meg) |
| állapotsor | `statustext` | megvan (a minőség-üzenet) |
