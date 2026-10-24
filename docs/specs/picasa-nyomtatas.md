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

## Az öt gyorsválasztó induló értéke - területi mérés, mentett `PrintSize` (#4394, #5489)

**Bináris eredmény:** a `0x006e5ab0` a `GetLocaleInfoA`-t hívja `0x400`
lokálazonosítóval, `0x0d` (`LOCALE_IMEASURE`) információtípussal és 2 bájtos
kimeneti pufferrel (`0x006e5acf`-`0x006e5b27`). Ha az első karakter `'0'`,
a metrikus alapérték-tömböt választja; minden más eredménynél, beleértve a
lekérdezési hibát, a hüvelyk-alapú tömböt (`0x006e5b31`-`0x006e5b5f`). Ez
területi mérési rendszer, nem felületnyelv- vagy országkód-választás.

A hiányzó `Preferences\PrintSize%d` kulcsok nyers alapértékei, majd az
`0x006e5d70` popup-index leképezésén és a `0x00775ce0` címkefüggvényen át
látható méretcímkék:

| `GetLocaleInfoA` eredmény | `PrintSize0`-`PrintSize4` nyers alapértéke | megjelenő `ytPrintSizes` címkék |
|---|---|---|
| `'0'` (`LOCALE_IMEASURE`, metrikus) | `[7, 8, 9, 10, 12]` | `e10x15cm` · `e13x18cm` · `e15x20cm` · `e20x25cm` · `eContact` |
| egyéb vagy lekérdezési hiba | `[0, 1, 2, 3, 4]` | `eWallet` · `e3x5` · `e4x6` · `e5x7` · `e8x10` |

A metrikus címkesor a #4394 korábbi táblájának helyesbítése. Az ott megadott
`e5x8cm`, `e9x13cm`, `e10x15cm`, `e13x18cm`, `e20x25cm` sor nem következik a
bináris leképezésből.

**A mentett beállítás felülírja az induló értéket.** A `0x006e5ab0`
`Preferences\PrintSize%d` kulcsokat olvas (`%d` = 0-4); a területi
alapértéket adja át hiányzó értéknél, és a beolvasott 0-15 közötti értéket
használja helyette (`0x006e5b66`-`0x006e5d0b`). A mentési út külön
`FUN_006e3990`: ugyanazokat a kulcsokat állítja elő (`0x006e42f4`) és a
`Preferences`-író segédnek adja át (`0x006e4366`-`0x006e438f`). A kiválasztott
nyomtatási méret külön kulcsa a `PrintLastSize` (`0x00744ba8`-`0x00744bba`);
ez nem az öt `PrintSize` gyorsválasztó listája.

### Két független út és cáfoló ellenőrzés

- **A út:** az `0x006e5ab0` utasításai olvassák a `GetLocaleInfoA` eredményét,
  választanak a két alapérték-tömb között, majd a `Preferences\PrintSize%d`
  kulcs értékét vagy hiányzó-kulcs alapértékét teszik a kimeneti listába.
- **B út:** a nyomtatási képernyő építője, `0x00743700`, ugyanezt az öt
  értéket olvassa, és mindegyiket a `0x006e5d70` és `0x00775ce0` függvényen
  keresztül jeleníti meg; emellett a `0x00775f30` függvényből kéri a
  `ytPrintTip` súgószöveget. Ez megerősíti a gyorsválasztók használatát és
  címkéit, de a popup teljes sorrendjéhez nem független út, mert ugyanazt a
  `0x006e5d70` leképezést használja.
- **Cáfoló kör:** a régi metrikus címkesort az `0x006e5ab0` fallback
  értékeivel, az `0x006e5d70` mind a 16 leképezésével és a `0x00775ce0`
  enum-címkéivel ellenőriztem. Az eredmény `10x15`, `13x18`, `15x20`,
  `20x25 cm`, majd `Contact Sheet`; a régi sor nem áll meg. Külön próbáltam
  a `ytPrintTip` táblát önálló sorrendforrásként használni, de csak a
  `0x00743700` hívja, és ez is a közös méretleképezésből kapja az enumot.
- **Bizonyítottság:** a hiányzó kulcs nyers számai binárisak. A popup
  címkéinek sorrendje **feltételes**, mert csak az `0x006e5d70` állítja elő
  a teljes listát. A második, képernyőbeli út ugyanazt a függvényt használja.

### Eredeti / nálunk / teendő

| Eredeti Picasa | PicasaPy (mért forrásviselkedés) | Teendő |
|---|---|---|
| A `LOCALE_IMEASURE` metrikus ága az öt alapértéket `10x15`, `13x18`, `15x20`, `20x25 cm`, `Contact Sheet` címkeként jeleníti meg; a másik ág Tárca, `3.5x5`, `4x6`, `5x7`, `8x10`. A hiányzó `PrintSize0`-`PrintSize4` kulcsok alapértékei binárisból jönnek. | A `src/picasapy/printing/dpi.py:171-186` jelenlegi metrikus alapértéke `5x8`, `9x13`, `10x15`, `13x18`, `20x25 cm`; a hüvelykes ág Tárca, `3.5x5`, `4x6`, `5x7`, `8x10`. A `src/picasapy/app/print_controller.py:262-265` a 17 elemű opciólistát adja vissza `TELJES_OLDAL` elemmel. | A hiányzó kulcs metrikus alapértékeit bináris viselkedésre igazítani. Az Opciók popuphoz külön 16 elemű listát adni, `FullPage` nélkül; a nyomtatási képernyő külön `fullbutton`-ját megtartani. A sorrend csak feltételesen igazolt, ezt a fejlesztői jegy és a komment is jelezze. |

**Fejlesztői kész, ha:**

- [ ] Azonos felületnyelv mellett a területi mérési rendszer váltása a
  megfelelő családot választja; azonos területi beállítás mellett a felület
  nyelvének váltása csak a feliratokat változtatja.
- [ ] A PicasaPy jelenlegi metrikus és hüvelykes katalógusa, sorrendje és
  `Teljes oldal` eleme megmarad; a korábban kijelölt méret külön, stabilan
  tárolódik.
- [ ] A tesztek lefedik legalább a magyar felület + hüvelykes terület és az
  angol felület + metrikus terület kereszt-eseteit.

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

### A Review lista DPI-sávjai (2026-10-05, #4280)

A `ThumbUIPrint::ReviewBest` / `ReviewGood` / `ReviewLow` sorcímkékhez a
panel két külön beállítást olvas; az értékek beállítással felülírhatók:

| beállítás | binárisbeli alapérték | összehasonlítás |
|---|---:|---|
| `Preferences\DPIWarning` | `0x96` = **150 DPI** (`0x0085c1fa`) | `DPI >= DPIWarning` → Best |
| `Preferences\DPISevere` | `0x64` = **100 DPI** (`0x0085c28a`) | ha nem Best, `DPI >= DPISevere` → Good |

`0x0085c1e0` és `0x0085c270` a képenkénti DPI-t a beállításból kapott
küszöbhöz hasonlítja. A `fcomp` után a `test ah, 0x41` / `jp` ág az
egyenlőséget is igaznak veszi: a küszöb alatti DPI-re a `jp` a hamis ágra
ugrik, a küszöbön vagy afölött nem. A hívó (`0x007451a0`) a két eredményt
Best → Good → Low sorrendben címkézi (`0x00745422`–`0x007454a7`).

| Review-sáv | binárisból következő feltétel | alapértékekkel |
|---|---|---|
| Best | `DPI >= DPIWarning` | `DPI >= 150` |
| Good | `DPI < DPIWarning` és `DPI >= DPISevere` | `100 <= DPI < 150` |
| Low | `DPI < DPISevere` | `DPI < 100` |

A bináris index adatxref-útja külön is a helyére teszi a neveket: a
`DPIWarning` (`0x00cc3368`) xrefjei között szerepel a kis-kép figyelmeztető
`0x0085c060` és a Review-sáv `0x0085c1e0` segéd; a `DPISevere`
(`0x00cc3374`) xrefje a `0x0085c270`;
a három `ThumbUIPrint::Review*` címke pedig a `0x007451a0` függvényhez
vezet. A diszasszemblált hívó a két helper eredményét összeadja, és az
összeg szerint választ Review-feliratot (`0x0074523c`–`0x00745248`,
`0x00745422`–`0x007454a7`).

A `CPrintDlg::bestqual` / `goodqual` / `badqual` család ugyanennek a
képkategóriának a tárolt kódját olvassa: a két helper igaz értékeinek
összege `0` / `1` / `2`, amelyet a 20 bájtos rekord `+0x10` mezőjébe
írnak; az olvasó `2` → Best, `1` → Good, egyébként Bad. A bájt útja
`0x00745513` → `0x0085c640` → `0x0085d300`; a hívó `[esp+0x58]` forrása
a korábban elmentett összeg (`[esp+0x4c]` a `0x007454e6`, `0x007454e7`
és `0x007454fe` push előtt).
Részletes vtable- és rekordbizonyíték: a
[`picasa-menu-parancsok-viselkedes.md` 40.7. szakasza](picasa-menu-parancsok-viselkedes.md).

Az angol feliratok mégsem azonosak: a Review lista `Low Quality` szöveget,
a `CPrintDlg` olvasója `Bad quality` szöveget választ a `0` kódhoz.

| Eredeti | Nálunk (#4280 előtt) | Teendő a fejlesztéshez |
|---|---|---|
| A két állítható küszöb igazságértékeinek összege (`0`/`1`/`2`) kerül a sor kódjába, és minden nyomtatandó kép Best/Good/Bad minősítést kap. | A #4275-ös ellenőrzőlista csak a Best-határ alatti képeket és a DPI-jüket mutatta; a Good/Bad határ nem volt bekötve. | Olvassuk a `DPIWarning` és `DPISevere` beállítást, őrizzük meg a régi kis-kép figyelmeztetést, és a teljes listán jelenítsük meg a minőségi kódot a hivatalos felirattal. |

**Bizonyítottsági fok: megerősített.** Az utasításszintű út: a két küszöböt
olvasó függvény összehasonlítása, a hívó összegzése, a rekordmásolás, majd a bájt
olvasója egymásra zár. B adatút: az index string-xrefjei a beállításkulcsokat
a két helperhez és a Review-címkéket a hívóhoz rendelik; az RTTI/vtable a
`CPrintDlg` olvasót ugyanahhoz a rekordvektorhoz köti. A két út egyezik.
**Cáfoló próba:** a szigorú `DPI > küszöb` változatot az egyenlőség cáfolja:
`0x0085c237`-nél a `fcomp` egyenlő értékeinél `C3=1`; a
`0x0085c23d` `test ah, 0x41` utasítása ekkor `AH & 0x41 = 0x40` értéket ad
(páratlan paritás), ezért a `jp` nem fut le, és a helper igazat ad.

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
`.tre`-ben **két gombpár** (`printpanel/pnowbutton` + `printpanel/pnowbutton2`,
`printpanel/reviewnowbutton` + `printpanel/reviewnowbutton2`): a panel a két állapot
között cserél.

### ⛔ ÖNHELYESBÍTÉS (2026-09-04): ez a két „melléklelet" DUPLIKÁTUM volt

*Forrás: `printpanel.tre:239` (`printpanel/phelpbutton`).*

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

⇒ Ez az ág a `GetDeviceCaps`-en át **lekérdezi** a nyomtatható és fizikai
méreteket; ebben a függvényben nem állítja át a nyomtató driver-DPI-jét.
Hogy a `PrinterQuality` hogyan változtatja a rajzolási rasztert, azt a
nyomtatási út alábbi, külön olvasása dönti el.

### A `PrinterQuality` hatása a tényleges nyomtatási rajzolásra

`0x00861190` a `ytPrinter` objektumot építi (vftable `0x00cc3dbc`, RTTI), és a `PrinterQuality`-t olvassa (`0x00861231`, alapérték `2`),
egész értékként a nyomtatási kontextus `+0x40` mezőjébe teszi
(`0x00861294`). A nyomtatási út a `0x00862000`-ban `+0x55=0` értékkel
indítja a rajzolást. A renderer `0x008623c0` ekkor a kontextus `+0x40`
mezőjéből képezi a `1/q` koordináta-szorzót (`0x0086240e`-`0x00862413`), és ezt
alkalmazza a négy átadott rajzolási méret-/koordinátaértékre
(`0x0086242b`-`0x0086244d`). Később a cél-téglalap négy értékét `q`-val
szorozza (`0x00862f82`-`0x00863001`); a kód tehát a kisebb raszterhez a
célkoordinátákon ellenirányú léptéket alkalmaz.

Az író által beállított értékekre ez pontosan:

| mód | `PrinterQuality` (`q`) | renderer-koordináta szorzója `1/q` | forrás |
|---|---:|---:|---|
| Normál | 2 | 1/2 koordináta-szorzó | bináris `0x007460c5`, `0x0086240e`-`0x0086244d` |
| Optimalizált | 1 | 1 koordináta-szorzó | bináris `0x007460fa`, `0x0086240e`-`0x0086244d` |

Egy ettől különálló nyomtatási útvonalon a `0x00861f50` ugyanezt a
`+0x40` mezőt olvassa (`0x00861f6f`), a négyelemű nyomtatási téglalap
méreteit `1/q` szerint alakítja (`0x00861f84`-`0x00861fed`), majd az
eredményt a `0x00864e60` terület-/munkamennyiség-segédnek adja. Ez a
nyomtatási munka területében `q=2` mellett tengelyenként felezést,
összterületben negyedelést jelent; `q=1` mellett nincs ilyen csökkentés.

**Bizonyítottság:** a kulcs → `ytPrinter+0x40` → renderer koordinátaút
utasításszintű olvasása és a `0x00861f50` külön munkamennyiség-útja egymástól
függetlenül ugyanazt az `1/q` skálát mutatja. Ez a bináris transzformáció
**megerősített**; hogy ez a PDF-ben milyen tényleges raszterfelbontást ad,
a `q=3`-as feliratkonfliktus miatt **nyitott**.

⇒ Statikusan biztosan állítható, hogy a renderer a Normál `q=2` módjában
`1/2`, az Optimalizált `q=1` módjában `1` koordináta-szorzót használ. Ez
a kód szintű skálázás; a végső PDF képpontszáma és a driver által jelzett
DPI **NINCS MEG**. Cáfoló ellenőrzésként összevetettem a Beállítások-lap
rádióinak független érték-hozzárendelését: ott `q=2` = `Compatible
(half-res)`, `q=3` = `High Quality (full-res)` (`0x006e23e7`,
`0x006e419f`, `runtime/options.fen`). Ugyanaz a renderer `q`-t közvetlenül
használja, így `q=3` esetén a statikus `1/q` koordináta-átalakítás nem
magyarázza a „full-res” feliratot. Emiatt a koordináta-skálát nem nevezem
PDF-felbontásnak; a tényleges kimeneti hatást azonos tesztképpel,
PDF-nyomtatón, mindkét módban végzett Colab-mérésnek kell eldöntenie.

### ⛔ KIMERÍTŐ NEGATÍV: a `PrinterUseTiles` nem kapcsol csempézett küldést

A `PrinterUseTiles` kulcsnak a bináris-index és a teljes `.text`-pásztázás
szerint is **két közvetlen hivatkozása** van: `0x00745f80` (a panel
állapotának olvasója) és `0x00746060` (az író). A `paszta.py` pásztázójának
memóriakapuján a pásztázás előtt át kellett mennie; a talált utasítások
`0x00745fa7` és `0x007460a3`. A motor frissítője (`0x008613b0`) csak a
`PrinterQuality`-t olvassa, a nyomtatási rendererben (`0x008623c0`) pedig
nincs `PrinterUseTiles`-olvasás.

⇒ A `PrinterUseTiles=1` az eredeti nyomtatási úton **nem kapcsol
csempézett küldést**. Ez a beállítás a panel állapotfeltételében és
eltárolásában vesz részt; a rajzolási raszter változását a `PrinterQuality`
adja.

*(Összevetésül: a `PrinterQuality`-nak nyolc hivatkozója van, köztük három
a motorban: `0x00861190`, `0x008613b0`, `0x008614a0`.)*

### Nálunk (forrás-olvasás, 2026-10-24)

A #5684 `83555b635` commitja bevezeti a párbeszéd rádiókapcsolóját és a
`printerOptimized()` / `setPrinterOptimized()` tárolót: az eredeti
`2/0` vagy `1/1` pár a `printing/jobPrinterQuality` és
`printing/jobPrinterUseTiles` beállításokba kerül, majd a párbeszéd
frissíti az előnézetet. A rajzoló út viszont a meglévő globális
`printerQuality()` értékéből számolt `_printer_output_scale()`-t kapja; a
per-job kulcsokat nem olvassa. Így a #5684 kapcsolója tárolja a módot, de a
nyomtatási raszterre még nincs hatása.

**Checkout-eltérés:** a jelen munkafa `HEAD`-je `f9f84e589`, és nem tartalmazza
a `83555b635` commitot. A jelenlegi forrásban ezért a #5684 kapcsoló sem
látható; a fenti PicasaPy-összevetés a megadott #5684 commitra vonatkozik.

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
| **papíradatok** | **`paperinfo`** | **megvan**: `PrintDialog.qml:142-152, 967-980` és `print_controller.py:631` (`paperInfo()`); a `#5663` újraellenőrzése javítja az előző, elavult „NINCS” állítást |
| állapotsor | `statustext` | megvan (a minőség-üzenet) |

## ⛳ A 17 nyomtatási méret FIZIKAI mérete — az ugrótáblából (2026-09-17, 318. kör, #1401)

*A lap eddig a 17 méretnek csak a NEVÉT és a magyar feliratát adta. A tényleges
méret enélkül találgatás volt — az Útlevélkép (#1401) megvalósításához viszont
szám kell.*

### A forrás: `FUN_00776e20` — méret-azonosító → két hüvelyk-érték

```
0x00776e20  cmp eax, 0x11
0x00776e31  jmp dword ptr [eax*4 + 0x007771ac]   ; 18 elemű ugrótábla
```

Minden ág két `float` konstanst tesz a `[esp+0xc]` (hosszabb oldal) és a
`[esp+0x10]` (rövidebb oldal) rekeszbe. A kiolvasott értékek:

| index | kulcs | `[esp+0xc]` | `[esp+0x10]` | ellenőrzés a NÉV ellen |
|---:|---|---:|---:|---|
| 1 | `e4x6` | **6,0** | **4,0** | ✅ 4×6 |
| 2 | `e3x5` | **5,0** | **3,5** | ✅ 3,5×5 |
| 3 | `e5x7` | **7,0** | **5,0** | ✅ 5×7 |
| 4 | `e8x10` | **10,0** | **8,0** | ✅ 8×10 |
| 5 | `eWallet` | **3,5** | **2,5** | — (a név nem mond méretet) |
| 6 | `e3x4` | **4,0** | **3,0** | ✅ 3×4 |
| 7 | `e4x5` | **5,0** | **4,0** | ✅ 4×5 |
| **15** | **`ePassport`** | **2,0** | **2,0** | **NÉGYZET** |

⭐ **A mérésnek saját kontrollja van:** öt méret neve számot is tartalmaz
(`e4x6`, `e3x5`, `e5x7`, `e8x10`, `e3x4`, `e4x5`), és **mind az öt** pontosan
a nevében álló számpárt adja vissza. Ha a tábla nem ez volna, ez nem jönne ki.

⇒ **Az egység HÜVELYK** (a `e4x6` = 6,0/4,0, nem 152,4/101,6).
Ez a #451 méretállítását is pontosítja: a listában az `e3x4` **3 × 4 hüvelyk**,
az `e4x5` **4 × 5 hüvelyk**; ezek nem centiméteres méretek és nem azonosak az
`ePassport`-tal. A centiméteres választások külön `cm` kulcsot viselnek
(`e5x8cm` … `e20x25cm`), míg az `ePassport` saját mérete **2 × 2 hüvelyk**.

### Az `ePassport` NÉGYZET — és ez egybevág a kivágással

A passport-ág **egyetlen** konstanst olvas, és ugyanazt teszi mindkét
rekeszbe:

```
0x00776ecb  fld  dword ptr [0x00cf3a48]   ; 2,0
0x00776ed1  fst  dword ptr [esp + 0xc]
0x00776ed5  fstp dword ptr [esp + 0x10]
```

⇒ **2,0 × 2,0 hüvelyk.** Ez független megerősítése a
`picasa-menu-parancsok-viselkedes.md` 24. szakaszának, amely a **kivágást is
NÉGYZETNEK** mérte ki (`0x00531faa`–`0x00531fc7`): a négyzet alakú kivágás és a
négyzet alakú nyomat ugyanaz a döntés, két helyről olvasva.

### A centiméteres méretek: külön ág, `0,3937`-es szorzóval

A nyolc cm-es tétel (`e5x8cm` … `e20x25cm`, `eCDSize`) **közös ágra** megy
(`0x00776f0a`): a méretet egy példány-tábla (`[objektum+0xa0]`) adja, és a kód
megszorozza a `0x00cf3fe0`-en álló **0,3937** (`double`) értékkel — ez a
**cm → hüvelyk** átváltás (1/2,54 = 0,3937008). ⇒ a tábla belül centiméterben
tárol, a kimenet itt is hüvelyk.

Az `eFullPage` (0) és az `eContact` (16) nem konstansból dolgozik: az előbbi a
`0x007767e0`-t hívja (a lapból számol), az utóbbi az alapértelmezett ágra megy.

### A `LayoutPassport` elrendező — ugyanaz a 2,0

Az osztály vtáblája **`0x00cb3f80`** (a `-4`-en a `0x00d0cbe0`-es
`RTTICompleteObjectLocator`, annak `+0x0c`-je a
`LayoutPassport@ytPrinterHelper@@` típusleíró, `0x00d428d4`). A 0. rekesz
(`0x00775660`) ugyanazt a **2,0**-t (`0x00cf3a48`) adja át **mindkét**
méretként az ősosztály elrendezőjének (`[vtbl+4]` = `0x00778190`):

```
0x00775660  fld dword ptr [0xcf3a48]      ; 2,0
0x00775672  fst  dword ptr [esp + 4]
0x00775676  fstp dword ptr [esp]
0x0077567a  call eax                      ; a slot-1 előkészítője
```

*(A szomszédos osztály — `0x00775680` — a `0x00cf3fd8` = **3,5**-öt adja: az
a Zsebméret elrendezője. Ugyanaz a minta, méretenként egy osztály.)*

### ~~Ami NYITVA marad~~ → LEZÁRVA, ld. a lap végén (2026-09-26, #1401)

~~**Hány példány fér egy lapra.**~~ A darabszámot nem a `LayoutPassport` mondja
meg: a `0x00775660` a közös slot-1 előkészítőre (`0x00778190`) lép, amely
kétszer hívja a tényleges slot-2 geometriai rutint (`0x00778640`). A célzott
kiolvasás szerint a darabszám kérdésének útja ezért a `0x00778640` törzse és
a lapméretet adó hívói állapot.

### ⛳ A passport-lap előkészítője és a tényleges csempéző — célzott dekompiláció (2026-09-19, #1401)

A helyi, SHA-256 szerint az indexelt binárissal azonos `Picasa3.exe`-ben a
`ytPrinterHelper::Layout*` RTTI-vtáblák teljes, bájtszintű mintája **11**
slot-1 címet és **11** slot-2 címet ad. Mind a 11 layout-osztály slot-1-e
`FUN_00778190` (`0x00778190`, **305 bájt**), és mind a 11 slot-2-je
`FUN_00778640` (`0x00778640`, **1960 bájt**). A slotok egymás utáni címei a
vtable-adatokban vannak (`0x008b3f14` … `0x008b3fb8`), tehát ez nem egyetlen
RTTI-példányból levont következtetés.

#### A passport-belépés továbbra is 2,0 × 2,0 hüvelyk

A `LayoutPassport` slot-1 burkolója (`0x00775660`, 31 bájt) a
`0x00cf3a48` címen lévő **2,0** konstans ugyanazon értékét teszi a két
méret-argumentumba (`0x00775672` és `0x00775676`), majd a vtable slot-1-re
ugrik (`0x0077567a`). Ez a korábbi négyzetes fizikai méret leletét
függetlenül megtartja.

#### A korábbi címke helyesbítése: `0x00778190` nem a darabszám-csempéző

A `FUN_00778190` törzse két helyi layout-rekordot készít a
`FUN_007782d0`-nal (`0x007781aa` és `0x007781b5`), majd a saját objektumának
vtable slot-2-jét (`+0x08`) hívja meg kétszer (`0x007781e1` és
`0x00778207`). A slot-2 célja a vtable-mintában **`FUN_00778640`**, tehát a
`0x00778190` előkészítő/elosztó, nem a tényleges geometriai csempéző.

A tényleges közös geometriai rutin, `FUN_00778640`, három argumentumot takarít
le (`ret 0xc`). A törzsben közvetlenül mérhető:

- a nyomtatási/oldal-állapotot a `this+0x50` objektumon keresztül olvassa
  (`0x0077864f`–`0x0077866b`);
- a layout állapotának `+0x20`…`+0x2c` mezőit lebegőpontos skálázásban
  használja (`0x0077866f`–`0x0077869f`);
- a meglévő rekordszámot a `this+0x1c` mezőből vizsgálja
  (`0x00778703`), majd a kimeneti rekordtömböt dinamikus allokációs úton
  bővíti (`0x00778ccf` → `0x00c0769f`).

⇒ A célzott dekompiláció megdöntötte a korábbi szerepattribúciót, de a
**laponkénti útlevélkép-darabszámot akkor még nem adta meg**: a
`FUN_00778640` nem útlevélhez égetett darabszámot olvas, hanem futásidejű
layout-állapotból épít rekordokat. A következő gépi lépés: a
`this+0x50`, `this+0x1c` és a lapméretet adó hívói állapotának
visszakövetése: a 2026-09-26-i #363 körben lezárult; a végső leletet lásd
az alábbi „LEZÁRVA” szakaszban.

### Eredeti / nálunk / teendő

| | eredeti, binárisból | PicasaPy, futó saját kód mérése | teendő |
|---|---|---|---|
| passport-méret | `0x00775660` → `0x00cf3a48` = **2,0 × 2,0 hüvelyk** | passport-layout nincs meg | a fizikai méret lelete használható |
| közös előkészítő | 11 layout-osztály slot-1-e: `FUN_00778190`, **305 bájt**; két slot-2-hívás | — | szerepe dokumentálva, nem csempézőként |
| tényleges geometriai csempéző | 11 layout-osztály slot-2-je: `FUN_00778640`, **1960 bájt** | — | `this+0x50` / `this+0x1c` és a lapméret-hívó visszakövetése |
| passport darabszám | 2026-09-19-én **NINCS MEG**; a #363 kör ezt később lezárta: friss munkánál 1, újrahasznált munkánál a beállított szám marad |: | történeti állapot; a részletes lelet az alábbi „LEZÁRVA” szakaszban |
| indexkép-rács | — | `DEFAULT_COLUMNS = 4`; az érintett nyomtatási próbák **65/65** zöldek; A4, 300 dpi, 17 kép, 4 oszlop mellett **20** hely/lap és 1 lap, 3 oszlop mellett **12** hely/lap és 2 lap (`[12, 5]`) | ez a jelenlegi saját indexkép-út, nem az eredeti passport-lelet |

**A 2026-09-19-i kör végállapota (történeti):** 1 nyílt kérdés maradt,
amelyet a 2026-09-26-i #363 kör az alábbiak szerint lezárt.

*Forrás: `FUN_00776e20` (`0x00776e20`–`0x00776f45`), az ugrótábla
`0x007771ac`; célzott dekompiláció: `0x00775660`, `0x00778190`,
`0x007782d0`, `0x00778440`, `0x00778640`; a konstansok `0x00cf39e8` = 6,0 ·
`0x00c7e4a4` = 4,0 · `0x00cf3a58` = 5,0 · `0x00cf3fd8` = 3,5 · `0x00cf3fec` = 7,0 ·
`0x00cf3b28` = 10,0 · `0x00c7cf84` = 8,0 · `0x00cf3fe8` = 2,5 ·
`0x00c49618` = 3,0 · **`0x00cf3a48` = 2,0**; a cm-szorzó `0x00cf3fe0` =
0,3937. A `LayoutPassport` vtáblája `0x00cb3f80`.*

### ⛳ LEZÁRVA: hány útlevélkép kerül egy lapra — a példányszám dönti el, alapból EGY (2026-09-26, 363. kör, #1401)

*Forrás: `0x00744d00` (az útlevél-út nyomtatási előkészítője) · `0x00860f60` (a nyomtatási beállításcsomag konstruktora) · `0x007782d0` (a rekordépítő) · `0x00778190` (slot-1) · `0x00778640` (slot-2, a rácselrendező).*

A kérdés nem egy útlevélhez égetett darabszám. Az elrendező annyi cellát rak le, amennyit a **képenkénti példányszám × a képek száma** kér. Az útlevél-út ezt a példányszámot nem állítja, a kezdőértéke pedig **1**.

1. **A nyomtatási munka.** A `0x00744d00` a munkát (`[ebp+0xec4]`, 0xa8 bájt) csak akkor hozza létre, ha még nincs (`0x00744d0c`–`0x00744d39`). A képlistába az egy képet teszi (`0x00744d69`). A méret-mezőt `[munka+0x1c]` a paraméterre, útlevélnél `0xf`-re írja (`0x00744dd1`–`0x00744dda`). A példányszámhoz nem nyúl.
2. **A beállításcsomag kezdőértékei.** A munka `+0x14`-én álló csomagot a `0x00860f60` tölti fel: `[+0x08] = 1` (a méret, munkában `+0x1c`) és **`[+0x0c] = 1`** (a példányszám, munkában `+0x20`; `0x00860f70`–`0x00860f78`). A panel `IDS_COPIES` kijelzője ugyanezt a `[munka+0x20]`-at olvassa (`0x00745ac4`, ld. fent). ⚠️ Mivel a munka objektum újrahasznosul (`[ebp+0xec4]`), a munkamenetben korábban beállított példányszám megmarad.
3. **A rekord.** A `0x007782d0` a csomagot mezőnként másolja a helyi elrendezés-rekordba: `+0x08`, `+0x0c` (példányszám), `+0x18/+0x1c` (a képlista), `+0x20…+0x50` (a lap- és margó-állapot; `0x007782ea`–`0x00778366`).
4. **Tájolás.** A `0x00778190` a rácselrendezőt kétszer hívja, egyszer `(szélesség, magasság)`, egyszer felcserélve (`0x007781e1`, `0x00778207`), és a két eredményből választ (`0x00778238`–`0x00778276`). A 2,0 × 2,0-s útlevélnél a két eset azonos.
5. **A rács.** A `0x00778640` a képlistán (`[rekord+0x1c] >> 1` kép) és képenként a példányszámon (`[rekord+0x0c]`) megy végig (`0x0077896e`–`0x0077899a`). Minden cella egy 0x1c bájtos rekord (`0x0077892a`, `rep movsd`, 7 duplaszó: kép, téglalap, sor, oszlop). A cellákat sorfolytonosan rakja a nyomtatható területre: vízszintesen, amíg a következő cella belefér (0,999-es tűréssel, `0xcf4a38`), aztán új sort kezd. Ha a következő sor már nem fér el, a menet kilép (`0x00778809` → `0x007789ba`). A második menetben a maradék helyet egyenletes térközként osztja szét. Ha a rés 0,2 alatti (`0xcf4748`, `0xc7e4b0`), a cellákat 0,975-szörösre kicsinyíti (`0xcf4a30`; `0x00778a46`–`0x00778aa7`). A végén a lap téglalapjára normalizál.

⇒ **Az Útlevélkép parancs alapból EGY 2 × 2 hüvelykes képet tesz a lapra.** Többet a nyomtatási panel példányszámával (`numberprints`) lehet kérni; ekkor a képek sorfolytonos rácsban, egyenletes térközzel kerülnek a lapra. A lapszámot a panel a munka lap-tömbjéből számolja (`0x00745b52`, ld. fent); a ki nem férő cellák a következő lapra kerülnek — ld. a következő szakaszt (#3646). A laponkénti **befogadóképesség** a nyomtatható terület függvénye (nyomtatófüggő), állandó szám nincs.

⛔ **A nyomtató külső margójának pontos fizikai értéke NINCS MEG.** A
geometriai út futásidejű lap-/layout-állapotból dolgozik; ez a binárislelet
nem ad minden nyomtatóra érvényes margószámot. A margót csak egy Windowsos,
konkrét nyomtatóval végzett előnézet-/nyomatmérés döntheti el.

⛔ **Élőben nem mérhető (2026-09-26).** A Colab-gépen nincs telepített nyomtató: a Print gombra „A printer must be installed in order to print.” jön (picasa-colab-jobs #51). A tesztkönyvtárban arc sincs, amit az útlevél-felismerő elfogadna (#49, #50: négy képből négy „Can't find any faces”). Gépház-jegy: picasapy-agent #159. A vizuális egyezés tehát NINCS mérve; a fenti lánc a binárisból megerősített.

*Bizonyítottsági fok: megerősített* (a példányszám kezdőértéke, a mezők útja, a két tájolás, a sorfolytonos rács); *erős* (a 0,2 / 0,975 térköz-szabály pontos alakja, amely a vizuális egyezés nélkül csak utasításszinten olvasott).

### 🔁 Független újralevezetés
- **bíráló:** friss opus-ügynök (Agent, nem fork) (friss kontextus, a kutató magyarázata nélkül)
- **címek:** `0x00744d00`, `0x00860f60`, `0x007782d0`, `0x00778640`
- **eredmény:** EGYEZIK
- **a bíráló tényei:** a példányszám kezdőértéke 1 (0x00860f78, [+0xc]); a 0x00744d00 csak a méretet (0xf, [munka+0x1c]) írja; a rácselrendező a képlistát (+0x18/+0x1c) és a példányszámot (+0xc) a beállításcsomagból veszi, képenként példányszám darab cellát rak; 0xf → LayoutPassport a 0x00775890 táblájában (0x00775b24–0x00775b36); a következő sor túlcsordulásakor kilép (0x00778809 → 0x007789ba).
- **költség:** 125761 token

### ⛳ A rácselrendező LAPTÖRÉSE — a túlcsorduló cella a következő lapra kerül (2026-09-26, 364. kör, #3646)

*Forrás: `0x00778640` vége (`0x00778c58`–`0x00778de5`) · `0x00778190` (`0x00778238`–`0x00778276`) · `0x007774b0` · `0x00745b52`.*

Az előző szakasz nyitva hagyta, mi lesz a cellákkal, ha a következő sor már nem fér el. A válasz: **új lap kezdődik, és ott folytatódik, ahol abbamaradt.**

1. **A kimeneti tömb eleme LAP, nem cella.** A rendező egy lapon belül a cellákat helyi tömbbe gyűjti (0x1c bájtos cellarekordok, `0x0077892a`). A lap lezárásakor ezt a helyi tömböt egy 12 bájtos lap-rekordként fűzi a beállításcsomag kimeneti tömbjéhez (`[csomag+0x00]`/`[+0x04]`; `0x00778d7a`–`0x00778da5`). A panel ennek az elemszámát mutatja lapszámként (`[munka+0x18] >> 1`, `0x00745b52`; a munkában a csomag `+0x14`-en kezdődik).
2. **Túlcsordulás.** Ha a következő sor már nem fér el (`0x00778809` → `0x007789ba`), a rendező az aktuális cellát nem helyezi el. A példányszámlálót nem lépteti, és a laphoz a második menet következik: térköz, kicsinyítés, normalizálás.
3. **Új lap.** A lap hozzáfűzése után, ha a képindex még kisebb a képek számánál (`0x00778dbd`–`0x00778dc9`: `[esp+0x2c] < [csomag+0x1c] >> 1`), visszaugrik a lap-ciklus elejére (`0x00778dd5` → `0x0077871a`). Ott új x/y, új sorszámláló és új oszlopindex indul, a **kép- és a példányszámláló viszont megmarad**. A túlcsorduló cella tehát a következő lap első cellája.
4. **Sorrend.** Kívül a képek, belül a példányok (`0x0077896e`–`0x0077899a`). Két kép két példánnyal: A, A, B, B, sorfolytonosan, lapról lapra folytatva.
5. **Tájolás a lapszám szerint.** A `0x00778190` a két tájolás eredményét a lapok számával veti össze (`[rekord+0x04] >> 1`). A felcserélt tájolást (`h, w`) **csak akkor** választja, ha az kevesebb lapot ad; döntetlennél az eredeti (`w, h`) marad (`0x00778238`–`0x00778276`). Ha az egyik tájolás nulla lapot adott, a másikat veszi; ha mindkettő nullát, a slot-1 `−1`-gyel tér vissza (`0x0077825f`, `0x0077827b`–`0x007782be`).
6. **Ha egy cella sem fér el.** Ha a cella már egy üres lapra sem fér (`0x007786a3`–`0x007786ff`), a rendező `−1`-gyel tér vissza. Ekkor a `0x007774b0` a 0. indexű elrendezővel próbálja újra (`0x007775f1`–`0x00777602`). A lapméretet és a nyomtatható területet a kiválasztott nyomtató objektumából veszi (`0x00777551`–`0x007775e5`).

Minden lap a saját második menetével kapja a térközét: a részben teli utolsó lap cellái a maradék helyen egyenletesen oszlanak el.

#### Eredeti / nálunk / teendő

| | eredeti | nálunk (`app/print_controller.py`) | teendő |
|---|---|---|---|
| egy lapon | a nyomatméretű cellák (pl. 4 × 6 hüvelyk) rácsba rendezve a nyomtató papírján | **több nyomatméretű cella egy papírlapon**, `grid_pages()` és `_paint_pages()` (`printing/grid_layout.py:130-199`, `print_controller.py:1874-1933`) | **EGYEZIK** szerkezetileg; az alábbi élő minták ellenőrzik |
| laptörés | a túlcsorduló cella a következő lap első cellája | a következő lapra folytatja a `grid_pages()` (`printing/grid_layout.py:140-145,159-199`) | **EGYEZIK** |
| sorrend | A, A, B, B | A, A, B, B: a lap cellái `first + offset` sorrendben készülnek (`print_controller.py:1899-1904`) | **EGYEZIK**; az élő minták: Colab EN 29/30 |
| tájolás | amelyik kevesebb lapot ad, döntetlennél az eredeti | `choose_page_orientation()` a két cellatájolás közül a kevesebb lapút választja (`printing/grid_layout.py:202-229`) | **EGYEZIK** a kiválasztási szabály; az oldal tájolását nem forgatja el |

**A #3647 megvalósítása jelenleg a forrásban megvan.** A fenti régi
„minden példány külön oldal” összehasonlító cellák a megvalósítás előtti
állapotot írták le; a `_grid_for_job()`/`grid_layout` alapú kód a lapra
rendezett rácsot, a laptörést és a példánysorrendet használja. A táblázat
most a jelenlegi kódot rögzíti. A PicasaPy által renderelt Passport-nyomat
teljes képi egyezése az eredetivel azonos nyomtatón továbbra sincs mérve.

#### ✅ Élőben mérve (2026-09-26, picasa-colab-jobs #55; PDF-nyomtató, A4, 300 dpi)

Eredeti angol Picasa 3.9.141, egy négyzetes tesztkép (`color_patches.jpg`), Crop to Fit:

| beállítás | mért eredmény | a szabály szerint |
|---|---|---|
| 4 × 6, 1 példány | 1 lap, egy cella, a lapon középen | 1 cella; a térköz a maradék helyen egyenletes ✅ |
| 4 × 6, 5 példány | **„1 of 3”**: 2 + 2 + 1 cella, egymás alatt; a 3. lapon az egy cella középen | túlcsordulás → új lap, folytatott számláló, laponkénti térköz ✅ |
| Wallet, 5 példány | 1 lap, sorfolytonos rács: 3 + 2 | sorfolytonos rakás, sortörés ✅ |

Kulcsképek: `research/testdata/screenshot/Colab EN 29 - Print, 4x6, 5 copies (1 of 3).png` és `Colab EN 30 - Print, Wallet, 5 copies.png` (a leltárban). A nyomtatási nézet méretgombjai angolul: Wallet · 3.5 x 5 · 4 x 6 · 5 x 7 · 8 x 10 · Full Page; az alapállás Full Page, Crop to Fit, „Copies per Photo” = 1.

*Bizonyítottsági fok: megerősített* (utasításszinten, független újralevezetéssel ld. lent, és élő méréssel).

### 🔁 Független újralevezetés
- **bíráló:** friss opus-ügynök (Agent, nem fork) (friss kontextus, a kutató magyarázata nélkül)
- **címek:** `0x00778640`, `0x00778190`, `0x007774b0`
- **eredmény:** EGYEZIK
- **a bíráló tényei:** a túlcsorduló sor nem vész el: a lap lezárása és hozzáfűzése után (0x00778c58–0x00778da5) 0x00778dd5 jb 0x0077871a új lapot indít az érintetlen kép- és példányszámlálóval; a kimeneti tömb eleme egy lap (12 bájt, cellavektor); a 0x00778190 a kevesebb lapot adó tájolást választja, döntetlennél az eredetit, nulla lapnál a másikat, mindkettő nulla → −1.
- **költség:** 116881 token

## #5663: a teljes nyomtatási út összevetése

**Hatókör:** menübelépés, párbeszéd, méret- és minőségbeállítások, alapértékek,
alacsony minőségű képek eltávolítása és a lapokra rendezett kimenet.
A vizsgált `Picasa3.exe` PE-verzióadata `ProductVersion=3.9.141`,
`FileVersion=3.9.141.259`. Az eredeti bináris címei RVA-címek. A PicasaPy-hivatkozások
forráskód-olvasásból származnak; az itt jelzett nyitott kimeneti kérdésekhez
nem következtetek vizuális egyezésre a kód szerkezete alapján.

**Bizonyítottsági fok:** a `removeall` bináris ága **megerősített** (két
független bináris út és külön felülvizsgálat egyezik; az élő UI-viselkedés
nem futott). A forrásoldali alapértékek és vezérlők összevetése **feltételes**
(bináris/spec-erőforrás és aktuális forráskód közvetlen egyezése; nincs élő
futtatás). A párbeszéd teljes geometriája és a nyomtatási raszter **nyitott**,
az alábbi megszerzési utakkal.

### Eredeti | Nálunk | Teendő

| Eredeti Picasa 3.9 (bináris cím) | PicasaPy (forrás) | Teendő |
|---|---|---|
| **Fájl ▸ Nyomtatás / Ctrl+P:** `cmd 0xe107`, menü-adat `0x00d6db18`; a nyomtatási képernyő építője `0x00743700` | **EGYEZIK:** `PicasaMenuBar.qml:630-636,847-851`; `Main.qml:1191-1198` nyitja meg a párbeszédet és rögzíti a célképsorokat | Nincs teendő a menübelépőn. A néző/slideshow célkép-bináris útjának teljes egyezése **NINCS MEG**; megszerzés: a `0x00743700` hívóinak és a kijelölést előállító hívóláncnak célzott diszasszembly-összevetése. |
| **Mappa/Album ▸ Indexképek nyomtatása / Ctrl+Shift+P:** `cmd 0x9c94`, menü-adat `0x00d6e274`; parancs-elosztó `0x00559150` | **EGYEZIK:** `PicasaMenuBar.qml:637-647`; a kontaktmód `Main.qml:1199-1209` ugyanazt a nyomtatási párbeszédet nyitja indexkép-módban | Nincs teendő a belépőn; a lapelrendezés a contact sheet külön szabálya, nem a méretcellás rács. |
| **Nyomatméret-lista:** 17 azonosító; a leképező `0x00776e20`, az eredeti képernyő építője `0x00743700` | A méretválasztó `PrintDialog.qml:652-676`; a vezérlő a területi 7/8 tételes készletet adja (`print_controller.py:355-398`), benne Full Page-dzsel; QML ehhez `CONTACT`-ot fűz (`PrintDialog.qml:453-461`). Nem az eredeti 17-es katalógus. | Bővítsük az eredeti ismert méretekkel. A CD-borító mérete **NINCS MEG**: a `0x00776f0a` `[objektum+0xa0]` táblájának pontos példányértékét és inicializálóját kell visszafejteni; becsült dimenziót ne adjunk hozzá. |
| **Eredeti induló méret:** Full Page, Crop to Fit, egy példány; ez a Picasa 3.9.141 PDF-nyomtatós felvételen látható (Colab EN 29/30); példányszám-alapérték `0x00860f78` | Méret: az első megnyitáskor Full Page (`print_controller.py:359-398`); példányszám 1 (`PrintDialog.qml:104-108`). A példányszám **EGYEZIK**; a méret induló felvétele alapján **EGYEZIK**. | Nincs teendő az alapméret/példányszám páron. A bináris `PrintLastSize` tartós felülírása továbbra is elsődleges; a felvétel csak az első indítási állapotot bizonyítja. |
| **Vágás/illesztés:** `printpanel/croptoggle` alapállapot `setpressed 1` (`printpanel.tre:155-158`), frissítés `0x00745aa4` | `PrintDialog.qml:154` alapértéke `fit` = „Whole picture”; a Crop választó `fill` (`:1018-1028`). **ELTÉR.** | Első megnyitáskor a Picasa Crop to Fit módjával egyező `fill` legyen az alapérték; a felhasználó továbbra is választhasson teljes képet. |
| **Nyomtatólista és telepítő-beállítás:** az aktuális nyomtatónév `0x00745bcc`; a `printpanel/psetupbutton` a driver `DocumentProperties`-útját nyitja (`0x00861750`) | Választható rendszer-nyomtatók és PDF (`PrintDialog.qml:920-963`); a beállítógomb `openPrinterSetup()`-ot hívja. A kódút eltér, de a tényleges párbeszéd és driver-beállítások egyezése **NINCS MEG**. | Megszerzés: Windows alatt ugyanarra a kiválasztott nyomtatóra nyissa meg mindkét Setup gombot; vesse össze az elérhető tulajdonságlapokat és a mentés utáni papíradatot. |
| **`printoptions` belépő:** a `printpanel/captionoptionsbutton` ága a panel építőjéhez vezet (`0x00743980`); kezelő `0x0085e800` | **EGYEZIK** a panel jelenlétében és különállásában: `PrintDialog.qml:617-623,1158-1165`; a PicasaPy `PrintOptionsPanel.qml` nyílik | Nincs teendő a belépőn; a tizenegy alapértéket lásd alább, a Cancel tartós hatása nyitott. |
| **Minőségi sávok:** `DPIWarning=150` (`0x0085c1fa`), `DPISevere=100` (`0x0085c28a`); minősítő `0x0085c1e0`, `0x0085c270` | `printing/dpi.py:32-55` ugyanazt a 150/100 alapértéket és a két küszöb összeadásából kapott kódot használja. **EGYEZIK.** | Nincs teendő az osztályozási alapértékeken. |
| **Képenkénti minőségi mód:** állapotvizsgáló `0x00745f80`; író `0x00746060`. Az író alapértékei Normál `PrinterQuality=2` (`0x0074609a`) és `PrinterUseTiles=0` (`0x007460b8`); Normál mód írása `2/0` (`0x007460c5`, `0x007460de`), Optimalizált mód írása `1/1` (`0x007460fa`, `0x0074610b`); a módjelző feltétele `PrinterQuality != 1001` és `PrinterUseTiles != 0` (`0x00745f80`). | A #5684 `83555b635` commitja a párbeszédben tárolja a `2/0` és `1/1` párokat (`printerOptimized()` / `setPrinterOptimized()`), és frissíti az előnézetet; a nyomtatás továbbra is a globális `printerQuality()` alapján választ léptéket. A jelen checkout `f9f84e589` nem tartalmazza a #5684 commitot. **ELTÉR**: a per-job mód nincs a tényleges kimenetre kötve. | Kössük a per-job `PrinterQuality`-t az előnézet és a nyomtatási rajzolás közös minőségi léptékére: Normál `q=2` → `1/q` renderer-koordináta-szorzó, Optimalizált `q=1` → `1` szorzó. A `PrinterUseTiles` ne vezessen be csempézett küldést, mert az eredeti renderer nem olvassa. Kész, ha a `2/0` és `1/1` állapot megmarad és visszaolvasható, a két mód renderer-koordináta léptékét a bináris `1/q` szerint köti be, és azonos tesztképes PDF-összevetés rögzíti a cél-téglalap, az oldalméret és a kimeneti raszter eredetihez viszonyított értékét. |
| **Alacsony minőségű képek eltávolítása:** műveleti kezelő `0x0085cce0`; a kérdés szövegkulcsa `0x00cc3450`, Igen `0x00cc33d4`, Nem `0x00cc33a0`. Csak ha minden sor alacsony minőségű, kérdez rá; vegyes listánál csendben csak az alacsonyakat törli. Igen: töröl és megszakítja a nyomtatást (`0x00745726`-`0x0074572b`); Nem: érintetlenül hagyja. | **ELTÉR:** `PrintDialog.qml:269-283,1265-1270` azonnal törli az összes alacsony minőségű sort; nincs megerősítés. Ha minden kép eltűnt, a `:285-289,1277-1286` nem nyomtat és nem zárja be a párbeszédet. | Vegyes listánál csak az alacsonyakat távolítsa el, megerősítés nélkül. Ha mind alacsony, jelenjen meg az eredeti figyelmeztetés; Nem ne változtasson, Igen ürítse a sort, szakítsa meg és zárja a nyomtatási párbeszédet. |
| **Papíradat:** `printpanel/paperinfo`, feltöltés `0x00745bde` (`0x00745980` állapotfrissítő) | `PrintDialog.qml:142-152,967-980`, `PrintController.paperInfo()`: kijelzi a kiválasztott lap adatait. **EGYEZIK** a mező jelenlétében. | Nincs teendő a mező jelenlétén; a szöveg/tördelés pixelpontos egyezése nincs mérve. |
| **Lapokra rendezés:** elrendező `0x00778640`, tájolás-választó `0x00778190`, lapgeneráló hívó `0x007774b0`; a túlcsorduló cella a következő lapra kerül. | `grid_layout.py:130-229`, `_paint_pages()` `print_controller.py:1874-1933`. **EGYEZIK** a lap/túlcsordulás/sorrend/tájolás szabálya; az A4-es 4×6 és Wallet minták egyezését Colab EN 29/30 méri. | Nincs teendő a rácsszabályon. Más nyomtató- és papírméreteken a pixeles kimeneti egyezés **NINCS MEG**; megszerzés: azonos forrásképek, méret, Crop to Fit, példányszám és PDF/nyomtató beállítás mellett eredeti/PicasaPy kimenet raszteres összevetése. |
| **Lapon belüli térköz/kicsinyítés:** a konstansok 0,2 (`0x00cf4748`/`0x00c7e4b0`) és 0,975 (`0x00cf4a30`); a 0,2 viszonyítási alapja **NINCS MEG** | `grid_layout.py:42-56` a cellamérethez viszonyított arányként használja a 0,2-t, amit a kód saját döntésként jelöl | NINCS MEG; megszerzés: a `0x00778640` összes konstans-xrefjénél kövesd végig, milyen méret és mértékegység a 0,2 alapja; addig ne állítsunk teljes térköz-paritást. |
| **Párbeszéd teljes képi elrendezése és kimeneti raszter:** a panel erőforrása `printpanel.tre`; a GDI `StartDocA`/`EndDoc` import-hivatkozások `0x00861bb0`, `StartPage`/`EndPage` `0x00862000` | `PrintDialog.qml` saját modális ablaka, a panelgeometria pontos vizuális egyezése nincs mérve; kimenet `QPrinter`/`QPainter` (`print_controller.py:857-908,1874-1933`). Az elemek és az eltérő backend ellenére a teljes vizuális paritás **NINCS MEG**. | Megszerzés: eredeti Picasa 3.9.141 és PicasaPy képernyőkép- és PDF-kimenet egymás mellé tétele azonos DPI/papír/nyomtató beállítással; geometria és raszter külön jegyzendő. |

### A `printoptions` tizenegy alapértéke

Az eredeti címek a `0x0085f7a0` betöltő alapérték-ágai; a PicasaPy
alapértékei a `printing/options.py:43-57` `PrintOptions` mezői. Mindegyik
sor **EGYEZIK** a mai forrás alapértékével:

| Beállítás | Eredeti alapérték (bináris cím) | PicasaPy alapérték | Teendő |
|---|---|---:|---|
| `text` / szövegforrás | 0 (`0x0085f8c7`) | 0 | **EGYEZIK** |
| `textplacement` | 0 (`0x0085f8fa`) | 0 | **EGYEZIK** |
| `textfont` | Arial (`0x0085f9db`) | Arial | **EGYEZIK** |
| `textsize` | 12 (`0x0085f963`) | 12 | **EGYEZIK** |
| `textcolor` | 0 (`0x0085f994`) | 0 | **EGYEZIK** |
| `wrap` | 0 (`0x0085f927`) | hamis | **EGYEZIK** |
| `border` | 0 (`0x0085f7b2`) | hamis | **EGYEZIK** |
| `bordersize` | 10 (`0x0085f7f0`) | 10 | **EGYEZIK** |
| `bordercolor` | 0 (`0x0085f827`) | 0 | **EGYEZIK** |
| `borderedge` | 0 (`0x0085f85a`) | hamis | **EGYEZIK** |
| `evenborder` | 1 (`0x0085f88d`) | igaz | **EGYEZIK** |

### `removeall`: bináris megerősítő ág

A címben megadott `CPrintDlg::removedall`, `removedallnobutton` és
`removedallyesbutton` címek a binárisban **sztring-/erőforráskulcsok**, nem
függvények; az xrefjük a `0x0085cce0` műveletkezelőre vezet. Ez a kezelő
végigiterálja a minőségi rekordokat (`this+0x104`, 0x14-es rekordköz, minőségi
jelző `+0x10`). Ha akár egy nem alacsony minőségű kép van, nincs párbeszéd,
és csak a nulla jelzőjű képek törlődnek. Ha minden kép alacsony minőségű,
megerősítést kér a `0x009bac20` segéddel:

- Nem: „Don't Remove” (`0x00ca7190`), nincs törlés.
- Igen: „Remove and Cancel” (`0x00cc33c0`), törlés, majd a hívó a
  `printpanel/pcancelbutton` műveletet küldi (`0x00745726`-`0x0074572b`).
- Kérdés: „This will remove all of your pictures and cancel printing.
  Would you like to continue?” (`0x00cc33f8`), kulcsa `0x00cc3450`.

**Független utak:** (A) a `0x0085cce0` utasításai megmutatják az összes
alacsony minőségű kontra kevert-listás ágat; (B) az xref-/adatút és a
`0x007451a0` minőségi rekordot előállító útja ugyanahhoz a `+0x10` jelzőhöz
vezet, majd az `0x00745726` kimeneti ág a nyomtatás megszakítását mutatja.
Ezek a bináris utak egyeznek; a független felülvizsgálat is ugyanerre jutott.

**Cáfoló kísérlet:** a vegyes (egy Low + egy Best/Good) ellenpéldát a ciklus
ágain végigkövettem: a számlálófeltétel átugorja a megerősítést, a törlőhívás
csak a nulla jelzőjű rekordokat kapja. Az „összes rossz esetén minden
eltávolítás rákérdez” értelmezés ezért nem áll meg. Élő UI-futtatás nem volt.

### Javasolt jegytörzs-bővítések

#### A Nyomtatás első megnyitáskor Crop to Fit módot válasszon

- **Eredeti:** `printpanel/croptoggle` `setpressed=1` (`printpanel.tre:155-158`), állapotfrissítő `0x00745aa4`.
- **Nálunk:** a `PrintDialog.qml:154` `fit`/Whole picture módot állít alapnak; a `fill`/Fill the page (crop) külön rádió (`:1025-1028`).
- **Teendő:** a friss párbeszéd Crop to Fit módban induljon; a felhasználó kézzel továbbra is választhassa a teljes képet.
- **Kész, ha:** első megnyitáskor a vágás módja aktív; a választás és a tényleges nyomtatási előnézet/kimenet ugyanazt az illesztési módot használja; az útlevél külön alapállapotát a meglévő útlevél-ág nem veszíti el.

#### Az összes alacsony minőségű kép eltávolítása kérdezzen rá és szakítsa meg a nyomtatást

- **Eredeti:** kezelő `0x0085cce0`, kérdés `0x00cc3450`, Nem `0x00cc33a0`, Igen `0x00cc33d4`, megszakítás `0x00745726`.
- **Nálunk:** `PrintDialog.qml:269-283,1265-1270` azonnal töröl; üres listán `:285-289` nem indít nyomtatást, de nem is zárja a párbeszédet.
- **Teendő:** vegyes minőségnél a Low képek némán törlődjenek; ha minden kép Low, a Picasa kérdésével egyező Igen/Nem döntés történjen. Igen ürítse a listát és szakítsa meg a munkát; Nem hagyja változatlanul.
- **Kész, ha:** vegyes lista nem kérdez rá és a jó képek megmaradnak; minden-Low lista pontosan egyszer kérdez; Nem után a lista változatlan; Igen után a lista üres, a nyomtatás az eredeti `pcancelbutton` műveleti ágán megszakad, és nem készül nyomat.

#### Tegyük elérhetővé az eredeti Picasa nyomatméreteit

- **Eredeti:** `ytPrintSizes` 17 azonosítója; méretleképező `0x00776e20`, panel építője `0x00743700`. Az `eCDSize` táblázata a `0x00776f0a` ágon, `[objektum+0xa0]`-nél van.
- **Nálunk:** `PrintDialog.qml:453-461,652-676` a területi 7/8 tételes készletet és `CONTACT`-ot mutatja, a többi ismert eredeti méretet nem.
- **Teendő:** az eredeti méretazonosítókat és azok sorrendjét tegye választhatóvá; az `eCDSize` maradjon letiltva, amíg a pontos méretérték és initializer nincs kiolvasva.
- **Kész, ha:** minden fizikai méret az eredeti `0x00776e20` értékeiből számolt méretet használ; Full Page a nyomtatható területhez igazodik; CD-borító mérete becslés nélkül, az `[objektum+0xa0]` pontos értékéből jön; az indexkép és az Útlevél külön útja nem keveredik össze a fizikai nyomatméretekkel.

#### Kösse a Normál/Optimalizált módot a nyomtatási raszterhez

- **Eredeti:** módállapot `0x00745f80`, író `0x00746060`; a renderer Normál `PrinterQuality=2` mellett `1/2`, Optimalizált `PrinterQuality=1` mellett `1` koordináta-szorzót használ (`0x0086240e`-`0x0086244d`). `PrinterUseTiles` módosítja a panelállapotot és tárolt párt, de nincs rajzoló-út olvasója (`paszta.py`, `0x00745fa7`, `0x007460a3`). A végső PDF-felbontás nyitott a `q=3` feliratkonfliktus miatt.
- **Nálunk:** a #5684 `83555b635` commit tárolja és visszaolvassa a `2/0` és `1/1` per-job párt, az előnézetet frissíti; a nyomtatási rajzoló `_printer_output_scale()`-ja viszont a globális `printerQuality()`-t használja, nem a per-job értéket. A jelen checkout `HEAD=f9f84e589` nem tartalmazza a #5684 commitot.
- **Teendő:** a per-job `PrinterQuality`-t kösse be a nyomtatási rajzolóba és az előnézetbe. A `PrinterUseTiles` értéket tárolja vissza az eredeti pár részeként, de ne rendelje hozzá csempézett küldéshez.
- **Kész, ha:** a `2/0` és `1/1` állapot tartós és visszaolvasható; teszt rögzíti a két renderer-skála kimeneti hatását; azonos forrásképes, azonos PDF-nyomtatós mérés összeveti az eredeti és PicasaPy cél-téglalapját, oldalméretét és kimeneti raszterét mindkét módban.

### Nyitott

- **NINCS MEG:** `eCDSize` pontos fizikai mérete; kiolvasási út: `0x00776f0a` `[objektum+0xa0]` példánytábla, initializer és hívó.
- **NINCS MEG:** a teljes panel pixelszintű elrendezésének egyezése; út: eredeti Windows futás képernyőképe és a `printpanel.tre`/PicasaPy QML ugyanazon állapotú geometriájának összevetése.
- **NINCS MEG:** a nyomtatás célképe viewer/slideshow állapotban; út: `0x00743700` hívói és a kiválasztott/listázott képek előállítási útjának diszasszembly-összevetése.
- **NINCS MEG:** a kiválasztott nyomtató Setup gombjának pontos UI- és mentési egyezése; út: az eredeti `0x00861750` DocumentProperties-út és a PicasaPy `openPrinterSetup()` ugyanazon Windows-nyomtatón való egymás melletti futtatása, a `paperInfo()` értékének utólagos összevetésével.
- **NINCS MEG:** az eredeti 0,2 térköz-küszöb viszonyítási alapja (`0x00cf4748`, `0x00c7e4b0`); út: a `0x00778640` konstans-xrefek operandusláncának további diszasszembly-olvasása, és csak ha az nem dönti el, célzott dekompilálás.
- **NINCS MEG:** a GDI és QPrinter kimenet pontos raszteregyezése, ezen belül a Normál `2/0` és Optimalizált `1/1` mód PDF-kimenete; út: ugyanaz a tesztkép, méret, papír, felbontás, Crop to Fit és példányszám mellett mindkét mód eredeti/PicasaPy PDF-raszterének és célgeometriájának összevetése.
- **NINCS MEG:** a Beállítások-lap globális `PrinterQuality=3` („High Quality (full-res)”) értékének tényleges kimeneti felbontása: a renderer statikusan `1/q` koordináta-skálát alkalmaz, ami `q=3`-nál nem magyarázza a feliratot. Ez külön kérdés a per-job `q=2/1` módtól; megszerzés: ugyanazon tesztképet `q=2` és `q=3` beállítással PDF-nyomtatóra küldeni, majd összevetni a kimeneti rasztert és a célgeometriát.
- **NINCS MEG:** a `printoptions` „Mégse” gomb ténylegesen visszaállítja-e a tartós értékeket az eredeti programban. A bináris a `0x0085f7a0` betöltőt hívja (`0x0085e8a1`-`0x0085e8e5`), de a vezérlők korábbi azonnali írása miatt a nettó hatás **NINCS MEG**. Út: eredeti Windows futásban állíts egy beállítást, kattints a Mégse gombra, majd olvasd vissza a Preferences értékét.
