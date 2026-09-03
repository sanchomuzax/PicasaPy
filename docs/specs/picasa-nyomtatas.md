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
