# Beviteli mezők és párbeszédpanelek a Picasában

A `respack.yt` **140 `.tre` elrendezésforrásából** és a réteg-névindexből.
A számok és a szerkezet a program saját forrásából valók, nem
képernyőkép-becslésből.

## A vezérlő-készlet (a teljes szótár)

A `.tre` rétegnevek zárójeles/kettőspontos előtagja adja meg a típust:

| típus | előfordulás | mi |
|---|---|---|
| `superbutton(sablon, id)` | 259 | a fő gombtípus, sablonnal |
| `text(id)` | 235 | szövegcímke (statikus) |
| `rect:` | 196 | színes/keretes téglalap |
| `button(...)` / `button:` | 145 | egyszerű gomb |
| `buttcon(...)` | 84 | ikonos gomb, három állapotképpel (`_n`, `_p`, `_h`) |
| `static(id)` | 71 | statikus felirat-tároló |
| `decrect(stílus)` | 43 | **süllyesztett/kiemelt keret** (`softbevel`, `flatbevel`) |
| **`window:`** | **37** | **natív, operációs rendszer szintű vezérlő** |
| `clip:` | 128 | vágókeret (görgethető tartalom) |
| `popuplist:` | 41 | **legördülő lista** |
| `vbutton:` | 25 | függőleges/összetett gomb |
| `buttcontainer:` | 21 | **rádiógomb-csoport** (egymást kizáró) |
| `listbox:` | 13 | listadoboz |
| `butlink(...)` | 11 | hivatkozásként viselkedő gomb |
| `colorpickerpanel(...)` | 7 | színválasztó panel |
| `colorwheel(...)` | 3 | színkorong |

**Nincs saját „szövegmező" típus.** A Picasa a beviteli mezőket **natív
vezérlőként** ágyazza be — ez a `window:` réteg.

## A beviteli mező mintája

Minden szövegbeviteli hely ugyanígy épül fel:

```
<panel>/rect(SZÍN): <nev>_base      ← a KERET (ARGB szín)
<panel>/window: <nev>               ← a natív beviteli vezérlő
[ <panel>/buttcon: <nev>_icon ]     ← opcionális ikon
[ <panel>/button: <nev>_clr ]       ← opcionális törlő gomb
[ <panel>/listbox: <nev>autocomplete ] ← opcionális kiegészítés
```

Példa — a keresőmező (`searchcontainer`):

```
rect(FF7F9DB9): searchbase     ← keret, #7F9DB9 (halvány kékesszürke)
window: search                 ← a mező maga
search_icon                    ← nagyító ikon
button: searchclr              ← törlő X (alapból rejtett!)
listbox: searchautocomplete    ← automatikus kiegészítés
```

A `searchclr` `m_hidden` alapállapotban — **csak akkor jelenik meg, ha van
beírt szöveg**.

## A program ÖSSZES beviteli mezője

| panel | mező | mire |
|---|---|---|
| `searchcontainer` | `search` | keresés (kiegészítéssel) |
| `tagpanel` | `taginput` | címke beírása |
| `keywords` | `addkeyword`, `keywordlist` | kulcsszó hozzáadása + lista |
| `quicktagconfig` | `edit_0` … `edit_9` | **a tíz gyorscímke** |
| `acquirepanel` | `subfolder` | importálás célmappája |
| `titledialog` | `line1` | szövegdia felirata |
| `publish` | `cdname`, `uploadaccount` | lemeznév, fiók |
| `geopanel` | `searchinput` | helykeresés a térképen |
| `makemoviepanel` | `inputtext` | szövegdia a filmben |
| `compose_mail` / `compose_share` | `to`, `subject`, `content` | e-mail |
| `buzzupload` | `title`, `description`, `comments` | feltöltés |
| `upload` | `title`, `description`, `contact_edit` | webalbum |
| `collab` | `contact_edit` | megosztás |

Ebből **PicasaPy-releváns**: `search`, `taginput`, `addkeyword`,
`edit_0…9` (gyorscímkék), `subfolder` (import), `line1` (szövegdia),
`searchinput` (geo). A többi a halott online szolgáltatásokhoz tartozik.

## A párbeszédpanelek szerkezeti mintája

A `foldermgr` (ld. #543) példáján, ami az összesre jellemző:

```
base: root                       ← m_offsetB + m_scaleX (alul rögzít, vízszintesen nyúlik)
├── left_side   x: 4 … 50%
├── right_side  x: 50% … jobb−4
│   ├── <magyarázó szöveg>       (14-es font)
│   ├── decrect(softbevel)       ← SÜLLYESZTETT csoportkeret
│   │   ├── static: <cím>
│   │   ├── buttcontainer        ← rádiógomb-csoport
│   │   └── line                 ← elválasztó vonal (m_scaleX)
│   └── listbox
├── size                         ← ÁTMÉRETEZŐ SAROK (Property winsize 1)
└── ok / cancel / help           ← m_offsetRB (jobb alsó sarok)
```

**Négy visszatérő elem, amit nálunk általában nem használunk:**

1. **`decrect(softbevel/flatbevel)`** — süllyesztett csoportkeret a logikailag
   összetartozó vezérlők körül.
2. **`line`** — vízszintes elválasztó a csoporton belül, `m_scaleX`-szel.
3. **`size`** — átméretező sarok, `Property winsize 1`.
4. **Súgó gomb** az OK/Mégse mellett, jobb alsó sarokban.

## Rádiógombok és jelölőnégyzetek

- **Rádiógomb**: `buttcontainer:` a csoport, benne `buttcon(...)` elemek a
  közös `globalbuttons/rb2_n|p|h` képekkel. Az alapértelmezettre
  `Property setpressed 1` kerül.
- **Jelölőnégyzet**: `buttcon_checkbox` sablonnal.
- **A felirat is kattintható**: `m_hit_childlabel` — a címke a gomb
  gyermeke, és a rákattintás a gombot nyomja.

## Legördülő listák

`popuplist:` (41 előfordulás). A tételek térközét
`Property itempadding <bal> <fent> <jobb> <lent>` adja meg — a
`titledialog`-ban pl. `2 2 10 2` a betűtípus-választónál és `2 2 5 2` a
méretnél.

## Teendő

Ez a lap a **szerkezetet** rögzíti. A konkrét eltérések panelenkénti
végigvezetése külön munka; a `foldermgr` már megvan (#543), a többi
párbeszédpanel `.tre`-je ugyanígy kiolvasható:

`acquirepanel` · `keywords` · `quicktagconfig` · `titledialog` ·
`printoptions` · `printpanel` · `outputlayout` · `publish` ·
`searchoptions` · `propertiespanel` · `peoplepanel` · `tagpanel`

## A „Visszaállítás" párbeszéd — darabokból épül (2026-08-16)

A visszaállítás megerősítő szövege **nem egyetlen sztring**, hanem
**darabokból** áll össze, a fájl állapotától függően. A teljes összeállító
a `0x0053b2e0` (3 372 bájt), és mind a tizenkét darab ott van a
sztring-táblájában.

### A darabok, összeállítási sorrendben

| # | erőforrás | mikor kerül bele | HU |
|---:|---|---|---|
| 1a | `CThumbUI::FileRevert::message1` | **egy** fájl | Visszatér a fájl eredeti változatához? |
| 1b | `CThumbUI::FileRevert::messageX` | **több** fájl | Visszatér a fájlok eredeti változatához? |
| 2a | `CThumbUI::FileRevert::changed1` | ha a fájl **kívülről módosult** (egy) | Ez a fájl a Picasán kívül módosult. Ha a visszaállítást választja, a módosítások elvesznek. |
| 2b | `CThumbUI::FileRevert::changedX` | ugyanez, több fájlra | Ezek a fájlok a Picasán kívül módosultak. … |
| 3 | `CThumbUI::FileRevert::message2` | **mindig** | ⏎⏎Ez a művelet nem vonható vissza, és az összes módosítás elvész. |
| 4 | `CThumbUI::FileRevert::message1undo` | ha van **visszavonható mentés** | ⏎⏎Az utolsó mentés visszavonásához és a szerkesztések megtartásához kattintson a „Mentés visszavonása" gombra. |
| 5 | `CThumbUI::FileRevert::continue` | a „kívülről módosult" ág végén | ⏎⏎Vissza szeretne térni? |

Az összeállító **két állapotjelzőt** használ a veremben — `[esp+0x22]` és
`[esp+0x23]` (`0x0053b46a`, `0x0053b48d`, `0x0053b4c5`, `0x0053b4e3`) —, és
mindkettő egy-egy feltételes darabot kapcsol. Ez pontosan a két feltételes
szövegrésznek felel meg: a **„kívülről módosult"** és a **„van
visszavonható mentés"**.

### A gombok

| erőforrás | HU | mikor |
|---|---|---|
| `CThumbUI::FileRevert::revert` | **Visszaállítás** | alap |
| `CThumbUI::FileRevert::undosave` | **Mentés visszavonása** | ha van visszavonható mentés |
| `CThumUI::FileRevert::yesbutton` | **Visszaállítás ennek ellenére** | a „kívülről módosult" ágon |
| `CThumUI::FileRevert::nobutton` | **Mégse** | mindig |
| `CThumbUI::FileRevert::title` | **Visszaállítás** | az ablak címe |

> ⚠️ Két erőforrás-előtag van, és **elgépelt** az egyik:
> `CThumbUI::FileRevert::*` (helyes) és **`CThumUI::FileRevert::*`**
> (hiányzó `b`) a két gombnál. Aki az eredeti erőforrásokból dolgozik,
> mindkettőt keresse.

### Folyamat és hiba

| erőforrás | HU |
|---|---|
| `CThumbUI::FileRevert::progress` | Fájlok visszaállítása |
| `FileRevert::fileerr` | Lemezhiba miatt nem lehetséges az összes fájl visszaállítása. Lehet, hogy a lemez megtelt vagy írásvédett. |
| `CEditRevertUpdate::progress` | Szerkesztések feljavítása |

### A NÉGY művelet magyar neve — egy helyen

| művelet | menü-erőforrás | HU |
|---|---|---|
| a **fájl** visszaállítása | `AlbumPhoto::ID_FILE_REVERT` | **Visszaállítás** |
| az **összes szerkesztés** visszavonása | `AlbumPhoto::ID_PICTURE_REVERT`, `FolderPhoto::ID_PICTURE_REVERT` | **Összes szerkesztés visszavonása** |
| az utolsó **mentés** visszavonása | `CThumbUI::FileRevert::undosave` | **Mentés visszavonása** |
| a lánc utolsó **lépésének** visszavonása | (dinamikus felirat) | „Visszavonás: <lépés neve>" |

### A „szerkesztések eltávolítása" külön megerősítés

| erőforrás | HU |
|---|---|
| `IDS_CONFIRMREVERT` | Ezzel a művelettel eltávolít minden módosítást, amelyet eddig az aktuális képre alkalmazott. Folytatja? |
| `IDS_CONFIRMREVERT_MULTIPLE` | …amelyet az **ÖSSZES** kijelölt képre alkalmazott. Folytatja? |
| `IDS_CONFIRMREVERT_YES_BUTTON` és `_MULTIPLE_YES_BUTTON` | **Szerkesztések eltávolítása** |

*Bizonyítottsági fok: megerősített* (a tizenkét darab egyetlen összeállító
függvény sztring-táblájában, és a két állapotjelző a veremben).

## A Címkék panel és a tíz gyorscímke (2026-08-16)

Négy erőforrás írja le: `tagpanel_text.tre`, `keywordstext.tre`,
`quicktagconfig.tre` (**31 elem**) és `quicktagconfig_text.tre`.

### A Címkék panel

*Forrás: `tagpanel.tre:20` (`tagpanel/add_tag_label`) · `tagpanel.tre:17` (`tagpanel/addtag`) · `tagpanel.tre:51` (`tagpanel/quick_config`) — és további 1 elem ugyanott.*

| elem | felirat / súgó |
|---|---|
| `tagpanel/add_tag_label` | **Type in a tag to add:** |
| `tagpanel/addtag` (súgó) | Add tag to the currently selected items |
| `tagpanel/quick_label` | **Quick Tags:** |
| `tagpanel/quick_config` (súgó) | Configure Quick Tags |

A panel címke- és súgófeliratai az eredeti angol szöveggel és a magyar
fordítással (`TagPanel::*`):

| erőforrás | eredeti (EN) | magyar (HU) |
|---|---|---|
| `TagPanel::tags` | `Tags` | **Címkék** |
| `TagPanel::tag_info_single` | `Tags in %s:` | **%s címkéi:** |
| `TagPanel::tag_info_multiple` | `Tags in the current selection:` | **Címkék az aktuális kijelölésben:** |
| `TagPanel::tag_info_whole_album` | `Tags in the current selection (whole album):` | **Címkék az aktuális kijelölésben (teljes album):** |
| `TagPanel::tip_fmt` | `Add tag: %s` | **Címke hozzáadása: %s** |
| `TagPanel::remove_tip` | `Remove this tag from the selected items` | **A címke eltávolítása a kijelölt elemekről** |
| `TagPanel::emptytip` | `Click to configure quick tags` | **Ide kattintva konfigurálhatja a gyorscímkéket** |
| `TagPanel::empty` | `?` | `?` *(az üres gyorscímke-gomb felirata)* |
| `TagPanel::notify_some_errors` | `Some of the text you entered could not be added as a tag.` | **A beírt szöveg egy része nem adható hozzá címkeként.** |

*Forrás: a bináris `.rdata`-sztringjei és `stringres-en-hu.tsv`; a
fejlécek címei rendre `0x00ca0658`, `0x00ca06d0`, `0x00ca0680`, a
kulcscímek `0x00ca0664`, `0x00ca06f0`, `0x00ca06b0`.*

### A „nincs beírt szöveg" tanító súgója

`TagPanel::notify_notext` — eredeti (`0x00ca0718`, kulcs:
`0x00ca0820`):

> Type in a tag (word or phrase) in the text box to the left of the button
> you just pressed.
>
> Then press the button again to add the tag to the selected items.
>
> (TIP: Press `<ENTER>` after you type in your tag to automatically add
> the tag without pressing the button)

Magyar fordítás:

> Írjon be egy címkét (szót vagy kifejezést) a szövegmezőbe attól a
> gombtól balra, amelyre az imént kattintott.
>
> Ezután ismét kattintson a gombra, így hozzáadja a címkét a kijelölt
> elemekhez.
>
> (TIPP: Ha automatikusan, a gombra kattintás nélkül szeretné hozzáadni a
> megadott címkét, nyomja le az `<ENTER>` billentyűt.)

### A címkepanel viselkedése a binárisban

**Fejlécváltás** — `0x0063ae00` választ a három fordítási kulcs között. Ha
a belső kijelölésvektor hossza a jelzőbit levétele után `2`, az egyetlen
kijelölt elem ága fut (`TagPanel::tag_info_single`). Minden más esetben a
`0x0065abe0` teljesalbum-predikátum igaz eredménye a
`TagPanel::tag_info_whole_album`, hamis eredménye a
`TagPanel::tag_info_multiple` kulcsot választja. A predikátum a
`[this+0xea4]` és `[this+0xea8]` állapotot, majd a `0x7176a0` kétféle
szűrésének üres/nem üres eredményét vizsgálja. A két mező és a szűrési
módok szemantikai nevét a feltárt kód nem adja meg; ezért a
„teljes album" feltétel nem egyszerűsíthető bizonyíték nélkül „a
kijelölés elemszáma egyenlő az album elemszámával" állításra.

**Üres mező és gyorscímke-súgó** — az `0x0063bb30` hozzáadási út üres
szöveg esetén a `TagPanel::notify_notext` üzenetet jeleníti meg. Az
üres gyorscímke gombhoz tartozó buboréksúgó a `TagPanel::emptytip`
(`0x00ca08dc`, kulcs: `0x00ca08fc`); a sztringet a
`0x0063c120` és `0x0063c7d0` gombkezelő is hivatkozza.

**Tömeges címkézés megerősítése** — a `CThumbUI::keyword_warning_fmt`
eredeti felirata `0x00ca2970`, kulcsa `0x00ca29dc`:

> You have a fairly large number of items selected.
>
> Are you sure you want to apply this tag to all %d items?

Magyar fordítás:

> Meglehetősen nagy számú elemet jelölt ki.
>
> Biztosan az összes (%d) elemre alkalmazni szeretné ezt a címkét?

A `0x0065b160` a kijelölés elemszámát hasonlítja `0x1e`-hez, és csak
`30` fölött jeleníti meg a megerősítést (`jbe` esetén átugorja). A
`0x0063bed0` hozzáadási út hívja ezt a CThumbUI-vtable `+0x04` helyéről.
Nem válasz esetén a függvény `0xF4242` értékkel tér vissza az elemek
alkalmazása előtt; a hívó ezt a visszatérést nem számolja részleges
beviteli hibának.

**Részleges bevitel hibája** — a `0x0063bb30` a nem üres bevitelt
vesszőnél (`0x2c`) tokenizálja, és minden tokent a `0x0063bed0`
hozzáadási útnak ad át. A nulla és a Mégse `0xF4242` visszatérésen kívül
minden nem nulla eredmény növeli a hibaszámlálót; ha a számláló nem nulla,
megjelenik a `TagPanel::notify_some_errors` (`0x00ca0838`, kulcs:
`0x00ca0874`) üzenet. Az elutasítás konkrét bemeneti okát a feltárt
híváslánc nem nevezi meg: a panelút a CThumbUI-vtable `+0x14` metódusáig
(`0x0065b4b0`) jut, amely a `0x0065b590`/`0x004d9aa0` módosító út
eredményét adja vissza. **Nincs bizonyíték** arra, hogy minden hibát
szintaktikailag hibás vagy már létező címke okoz.

Nyitott, célzott folytatás:

- `Ghidra-kör kell: 0x0065abe0 — a [this+0xea4]/[this+0xea8] állapot és a 0x7176a0 két szűrési módja mely kijelölésnél választja a „whole album” fejlécet? [blokkoló]`
- `Ghidra-kör kell: 0x004d9aa0 — milyen token- vagy elemtulajdonság miatt ad vissza nem nulla eredményt a 0x0063bed0 → 0x0065b4b0 → 0x0065b590 hozzáadási út, és ez váltja-e ki a részleges hibaüzenetet? [blokkoló]`
- `Ghidra-kör kell: 0x00437550 - az egyképes ág [this+0x48] objektumának +0x54 virtuális gettere melyik implementációra mutat, és az honnan tölti fel a címkelistát (IPTC, .picasa.ini vagy adatbázis)? [blokkoló]`
- `Ghidra-kör kell: 0x005c76b0 - a 0x005c7710-nél hívott [this+0xeac] vtable +0xdc callback konkrét osztálya/célja, és ez indítja-e a címke tartós IPTC/INI-írását? A 2026-10-21-idorend-12 dekompilátum csak az indirekt hívást mutatja. [blokkoló]`

*Binárishelyek: `0x0063ae00` (fejléc), `0x0065abe0` (teljesalbum-
predikátum), `0x0063bb30` (üres/hibás bevitel), `0x0063bed0` (token
hozzáadása és megerősítési hívás), `0x0065b160` (küszöb és megerősítés),
`0x0065b4b0`/`0x0065b590` (hozzáadási eredmény). A küszöb mérése:
`mérés (QEMU-i386, izolált 0x0065b160; szintetikus kijelölésszám,
„Nem” párbeszéd-válasz): count=30 → `NO_WARNING result=0`; count=31 →
`WARNING cancel=1 apply=0`. Ez függvényszintű mérés, nem Picasa
GUI-kattintásos teszt.*

**Bizonyítottsági fok:** a feliratok és magyar fordításaik kulcsonként
egyeznek a bináris sztringjeivel és a helyi fordítási táblával;
megerősített. A `>30` megerősítési küszöb és a Mégse előtti visszatérés
utasításszintű olvasással és a fenti QEMU-méréssel egyezik;
megerősített. A fejléc-, súgó- és részlegeshiba-megjelenítés feltételei
egyetlen statikus hívásláncból származnak; feltételesek, mert a Picasa
GUI-ban nem futott kattintásos ellenőrzés. A részleges hiba valamennyi
konkrét elutasítási oka nyitott.

#### A címkelista sorrendje és adatforrása (#5814, 2026-10-25)

**Listaépítés és sorrend.** A `0x0063ae00` előbb a kijelölt képek címkéiből
név-számláló párokat állít elő a `0x00437550` hívással, majd a
`0x004cd0c0` rendezőnek adja át a párokat; a rendező indexvektort készít,
amely alapján a panel az eredményből építi újra a `this+0x2b8` listát.
A `0x0063b5a0` soronként a vektor sorrendjét követi, nem rendez újra. A
rendező összehasonlítója a `0x004bd7b0`: előbb a számlálót veti össze,
a nagyobb érték kerül előre; egyező számlálónál az ASCII `A`-`Z` betűket
kisbetűsíti, majd a címkeneveket fordított byte-sorrendben adja ki. Egyetlen
kijelölt képnél minden címke számlálója `1`, tehát a név szerinti fordított
sorrend látszik. A `0x004cd2e0` összeolvasó ágai igazolják, hogy mindkét
kulcsnál a rendezési szempont szerinti nagyobb elem kerül előre.

**Több kijelölt kép.** A `0x00437550` külön ága minden kijelölt kép
címkelistáját beolvassa, vesszőknél elemekre bontja, címkénként számlálót
képez (`0x004d9570`, majd `0x004dbaf0`), és ugyanazt a `0x004cd0c0`
rendezőt használja. Ez a sorrend tehát számláló szerint csökkenő, azon belül
címkenév szerint fordított; a fejléc „current selection” vagy „whole album”
választása nem választ külön rendezési ágat. Az egyedi címke melletti
`[n]` számláló formázását a `0x0063ae00` végzi, ha az érték nagyobb `1`-nél.

**Adatforrás.** A listaépítő a `0x00437550`-ben egy, a címkeadatot szolgáltató
objektum virtuális getterét hívja (`0x004375ae`-`0x004375cc`, az
`[this+0x48]` objektum `+0x54` slotja). A bináris út azt mutatja meg, hogy a
listaépítő ezt a kapott címkelistát használja; nem nevezi meg, hogy a
getter mögötti adatot eredetileg a kép IPTC-mezője, a `.picasa.ini` vagy
valamelyik adatbázis tölti-e fel: **NINCS MEG**.

**Összevetés a job-242-vel.** A `paritas-ellenorzes.md` futás-összevetése
(`## Futás közbeni összevetés (#5396, 1. kör)`, a `proba` címkesor) rögzíti,
hogy a `kepernyo__12.png` állapotban a
`proba` az `AI image` fölött van. Ez egyezik az egyedi képnél levezetett
fordított névsorrenddel (`proba` a `p` betű miatt előzi meg az `AI image`
`a` betűjét), ezért önmagában nem bizonyítja, hogy az új címke időrendben a
lista elejére kerül. A job-242 JPEG nincs a helyi mérőcsomagban; az eredeti
IPTC Keywords mezőjének értékei és sorrendje, így az eredeti író elejére
vagy végére illesztése **NINCS MEG**. A `0x0063bed0` a címkét a
`CThumbUI::IKeywordUpdate` `+0x284` interfész `+0x14` metódusához küldi
(`0x00c906d8` → `0x0065b4b0`), amely a `0x005c76b0` kijelölési/listaépítő útba
lép; a feltárt lánc nem jut el az IPTC- vagy INI-szerializálóig.

**PicasaPy-összevetés (forráskód, nem futásmérés).** A
`keywordsOfRows()` a címkék unióját kisbetűsített név szerint növekvőre
rendezi (`src/picasapy/app/keywords_controller.py:99-109`), és nem őrzi a
kijelölésbeli gyakoriságot. Az `addKeywordToRows()` a címkét a sor végére
fűzi (`:150-163`); a JPEG-író a kapott sorrendben adja át az
IPTC `2:25` értékeket (`src/picasapy/metadata/iptc_writer.py:48-58`,
`:195-222`), így nálunk az új IPTC érték a keyword-mezők végére kerül.
Sikertelen JPEG-íráskor az INI-fallback ugyanennek a sorrendnek a
vesszővel összefűzött alakját írja. Ez a PicasaPy kódútja, nem élő
fájlmérés.

**Bizonyítottsági fok.** A Picasa listájának számláló- és névsorrendje
`feltételes`: a teljes szabály az utasításszintű bináris útból következik,
a job-242 felvétel csak az egyező, kétcímkés egyedi mintát ellenőrzi. A
fájl/DB eredet és az eredeti IPTC-beillesztés iránya **NINCS MEG**; ezek
eldöntéséhez a `0x005c7710` indirekt callback feloldása vagy címkézés előtti
és utáni eredeti JPEG-metaadat szükséges.

### A gyorscímke-beállító — pontosan TÍZ

`quicktagconfig.tre`, 31 elem: `edit_0` … **`edit_9`** és `base_0` …
**`base_9`**, plus `tag_group`, `tag_icon`, `divider`, `autofill`,
`recent_checkbox`, `ok`, `cancel`, `instructions`, `base`.

Az ablak címe: `QuickTagConfigDlg::title` → **„Gyorscímkék
konfigurálása"**.

#### A két viselkedési szabály

*Forrás: `quicktagconfig.tre:7` (`quicktagconfig/instructions`).*

`quicktagconfig/instructions` (angolul az erőforrásban):

> „You can use Quick Tags to apply a tag with a single click. Type in tags
> below that you want to have one-click access to. **By default, the top
> two Quick Tags are used to track recently applied tags.** Uncheck the
> checkbox below to manually set the top two tags."

| vezérlő | felirat | jelentés |
|---|---|---|
| `quicktagconfig/recent_checkbox` | Reserve top two buttons for recently used tags | **alapból BE** — a felső két gomb a legutóbb használt címkéket követi |
| `autofill` | Autofill empty boxes above with commonly used tags | az üres mezők feltöltése a gyakori címkékkel |

> **A felső kettő tehát alapból automatikus**, és csak a jelölő
> kikapcsolásával állítható be kézzel. Ez a Picasa saját, apró
> ergonómiája — a tíz gombból nyolc a felhasználóé, kettő a rendszeré.

### A Címkék párbeszéd (`keywords`)

*Forrás: `keywords.tre:52` (`keywords/addbutton`) · `keywords.tre:13` (`keywords/addkeywords_label`) · `keywords.tre:67` (`keywords/closebutton`) — és további 3 elem ugyanott.*

| elem | felirat |
|---|---|
| `keywords/keywords_label` | **Tags:** |
| `keywords/addkeywords_label` | **Add Tag:** |
| `keywords/addbutton` | Add |
| `keywords/removebutton` | Remove |
| `keywords/closebutton` | **Done** |
| `keywords/readonly_label` | Tags cannot be modified because one or more items are read-only. |

> A **csak olvasható** eset külön feliratot kap — ez NAS-on és
> írásvédett köteten valós helyzet.

*Bizonyítottsági fok: megerősített* (a négy erőforrásfájl teljes tartalma
és a tizenkét `TagPanel::*` bejegyzés).
