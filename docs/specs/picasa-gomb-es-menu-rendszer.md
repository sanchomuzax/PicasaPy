# A Picasa gomb- és menürendszere — a teljes vizuális nyelv (2026-08-17)

Ez a lap a Picasa **saját** vezérlő-készletét írja le: miből épül egy gomb,
milyen állapotai vannak, pontosan milyen színekkel, milyen betűvel, és hol
kezdődik a Windows saját felülete.

Források: `runtime/respack.yt` (269 `globalbuttons/*` réteg + 140 `.tre`
stílusleírás), `Picasa3.exe` (importtábla, RTTI), `stringres-en-hu.tsv`.

---

## 1. A legfontosabb megállapítás: KÉT menürendszer van

| mi | hogyan készül | következmény |
|---|---|---|
| **menüsor + jobbklikkes helyi menük** | **natív Windows-menü** (`CreatePopupMenu` × 36 hívóhely, `TrackPopupMenu`/`Ex`, `AppendMenuW`, `CheckMenuItem` × 13, `EnableMenuItem` × 17, `SetMenuDefaultItem`) | **a Picasa NEM rajzolja őket** — pontosan úgy néznek ki, ahogy az operációs rendszer menüi |
| **panelen belüli legördülők** (`popuplist`) | **saját** rajzolás (`CPopupList`, `ytPopupListNode`, `ytTextPopupListItem`, `ytSimpleSeparatorPopupListItem`, `CMixedPopupList`, `ButtconPopupCreator`) | a Picasa saját vizuális nyelvét követi |

**Bizonyíték:**

- `LoadMenuW` **nincs** az importtáblában → a menük futásidőben épülnek, nem
  erőforrás-sablonból.
- A menüépítő (`0x0056c5a0`, 6816 b) `MF_OWNERDRAW` (0x100) jelző **nélkül**
  fűz be tételeket → **nincs saját rajzolás**.
- `GetMenuInfo` egyetlen hívása (`0x005e7c20`) `cbSize = 0x1c`,
  `fMask = 8` (`MIM_STYLE`) — csak a **stílust olvassa**, nem ír színt.
- `GetDoubleClickTime` **nincs** importálva → a dupla kattintás küszöbe a
  rendszeré (`WM_LBUTTONDBLCLK`).

> **Amit ez a megvalósításra jelent:** a menüsort és a helyi menüket **nem
> kell Picasa-stílusúra festeni** — a platform natív menüje a hiteles
> megoldás. A panelen belüli legördülők viszont a saját stílust követik.

**Konkrét példa a natív menüre:** a könyvtár-eszköztár `folderviewpopup`
(„Nézet-beállítások ▾") gombja is ezt az utat követi — a kattintáskezelő
csak `EnableMenuItem`-szerű hívásokkal állítja be a tételek engedélyezett
állapotát, nem rajzol semmit. A gomb teljes viselkedése (a menü öt
tétele, mit ír, mivel egyezik meg a másik négy fejléc-gomb közül) a
[`picasa-konyvtar-eszkoztar-viselkedes.md`](picasa-konyvtar-eszkoztar-viselkedes.md)
lapon van.

---

## 1/b Miért néz ki ma is XP-nek — mert NEM XP

A Picasa **soha nem kéri meg az operációs rendszert**, hogy vezérlőt
rajzoljon. Az importtáblában:

| API | hívások |
|---|---:|
| `OpenThemeData` | **0** |
| `DrawThemeBackground` | **0** |
| `IsThemeActive` · `IsAppThemed` | **0** |
| `SetWindowTheme` · `GetThemeColor` | **0** |
| `DrawFrameControl` · `DrawEdge` | **0** |
| `GetSysColor` | 7 (csak natív részekhez) |

A **`uxtheme.dll` nincs a 24 importált könyvtár között.** A gombok, fülek,
csúszkák és panelek **kizárólag a `respack.yt` bitképeiből** készülnek,
amiket a Picasa saját megjelenítője másol a képernyőre.

**Ebből következik:** a kinézet nem „XP-téma", hanem **lefagyasztott
képpont** — ezért azonos XP-n, Windows 11-en és Wine alatt is. Aki az
eredetit másolja, **nem az XP témamotorját** kell utánoznia, hanem ezeket a
konkrét színeket és méreteket.

⚠️ **Ami viszont követi a rendszert:** a menüsor, a helyi menük, a fájl- és
üzenetablakok (a manifest `Microsoft.Windows.Common-Controls` v6-ot kér).
Ezek Windows 11-en **Windows 11-esek** — a „a Picasa XP-s maradt" csak a
**saját** vezérlőire igaz.

## 2. Egy gomb anatómiája — `b1_decrect`

A Picasa minden „rendes" gombja **ugyanabból a 27 × 27-es rétegből**
nyúlik ki. A `decrect` = *decorated rect*, azaz nyújtható (9-szeletes) kép.

### 2.1 A nyújtás szabálya — MÉRVE

| minta | méret | azonos oszlop-futam |
|---|---|---|
| `b1_decrect_n` | 27 × 27 | **8 … 18** |
| `b48_n` | 49 × 28 | **8 … 40** |
| `b88_n` | 88 × 28 | **8 … 79** |

Mindháromnál a futam a **8. oszlopnál kezdődik**, és a jobb szélétől
számítva is **8 oszlop** marad ki. Vagyis:

> **A vízszintes sapkák pontosan 8 képpont szélesek, a köztük lévő rész
> EGYETLEN, ismételt oszlop.**

Ezért azonos a `b32`, `b48`, `b72`, `b88`, `b98`, `b132`, `b150` rögzített
méretű változat képpontra a nyújtott `b1_decrect`-tel — ezek csak
gyorsítótárazott példányok.

**Függőlegesen NEM ismétlődik**: a `b1_decrect_n` egyetlen azonos
sor-futama a 8–9. sor, a többi folytonos színátmenet. A gombmagasság tehát
gyakorlatilag rögzített (a családtól függően 17 / 21 / 27 / 28 px).

### 2.2 A keret és a sarkok

```
 0. sor / 0. oszlop   #DEDEDE (fent) · #E0E0E0 (balra)   külső térköz
 1. sor / 1. oszlop   #BBBBBB                             ← a KERET, 1 px
25. sor / 25. oszlop  #BBBBBB                             ← a keret alul/jobbra
26. sor / 26. oszlop  #F8F8F8 (alul) · #F4F4F4 (jobbra)   külső fénykiemelés
```

A **sarkok lekerekítettek és élsimítottak**: a legkülső képpont
`alfa = 0`, majd 72 → 156 → 174 → 229 → 255 fut fel. A lekerekítés
sugara ≈ **2,5 px**.

### 2.3 A kitöltés — a négy állapot pontos színe

**Normál (`_n`)** — függőleges színátmenet:

| sor | szín |
|---|---|
| 2 | `#F9F9F9` |
| 6 | `#F1F1F1` |
| 12 | `#EAEAEA` |
| 18 | `#DDDDDD` |
| 24 | `#D0D0D0` |

**Rámutatás (`_h`)** — a normáltól **mindössze 229 képpontban** tér el
(2464-ből): a **felső két belső sor** és a **bal oldali két belső oszlop**
sötétedik be. Ez egy finom, bal-felülről érkező **belső árnyék**:

| sor | normál | rámutatás |
|---|---|---|
| 2 | `#F9F9F9` | **`#D6D6D6`** |
| 3 | `#F8F8F8` | **`#EBEBEB`** |
| 4-től | azonos | azonos |

Vízszintesen ugyanez: a 2. oszlop `#F1F1F1` → **`#C9C9C9`**, a 3. `#E3E3E3`.

**Lenyomott (`_p`)** — a teljes kitöltés **melegebb** és sötétebb lesz, a
felső belső árnyék pedig sokkal erősebb:

| sor | szín |
|---|---|
| 2 | `#A4A19D` |
| 3 | `#B5B1AE` |
| 4 | `#CBC6C2` |
| 6 | `#E5E1DC` |
| 8 | `#E9E4DF` |
| 16 | `#E0DAD6` |
| 24 | `#CBC6C2` |

Figyeld meg: a normál átmenet **semleges szürke** (R = G = B), a lenyomotté
**meleg** (R > G > B, kb. +4 … +7 eltéréssel) — a Picasa nem sötétíti,
hanem *melegíti* a lenyomott gombot.

**Bekapcsolt (`_t`)** — a kitöltés a normállal azonos, de a **keret arany**:

```
keret:  #C39B62      (a #BBBBBB helyett)
a keret melletti belső sor/oszlop:  #DFCAAC (felül) · #D9C09C (balra) · #BF9860 (alul/jobbra)
```

Csak öt réteg visel `_t` változatot: `b1_decrect_t`, `b48_t`, `b88_t`,
`b98_t`, `b132_t`, `b88ck_t`, `b98ck_t`, `b88cn_t`, `b98cn_t`, `wl_t`,
`cb_t`.

> **Nincs külön `_d` (letiltott) réteg.** A letiltott állapotot a program
> rajzolja (`Property disable 1`) — a módja **nyitott kérdés**.

---

## 3. A `decrect`-családok

| család | méret | mire |
|---|---|---|
| `b1_decrect` | 27 × 27 | **a szabvány gomb** (9 stílus használja) |
| `b2_decrect` | 19 × 17 | **mini gomb** (`buttonmini_text_center`, `button_header_option`) |
| `b3_decrect` | 15 × 21 | **lista-fejléc gomb** (`listheader_button`, `quicktag_button`) |
| `ob1_decrect` | 11 × 11 | **körvonalas gomb** (`outline_button_text`) |
| `checkbox2` | 15 × 15 | **jelölőnégyzet** (`buttcon_checkbox`) |
| `left/mid/right_segment` | 23 × 23 · 19 × 23 · 23 × 23 | **szegmentált gombsor** (bal / közép / jobb tag) |
| `thin_left/right_segment` | 23 × 19 | vékony szegmens |
| `b1_left/right_decrect` | 23 × 27 | fél-lekerekített gomb (sorban álló) |

---

## 4. A 28 gomb-stílus

Minden stílus egy külön `.tre` bejegyzés. A szerkezetük azonos:
három `button_state_decrect_{n,p,h}` tulajdonság + egy szövegszín-makró +
egy betű-makró.

| stílus | előfordulás | rajz | szöveg |
|---|---:|---|---|
| `button_text_center` | 76 | `b1_decrect` | `m_buttonfontC` (középre) |
| `listheader_button` | 51 | `b3_decrect` | **nincs felirat** (kikommentezve) |
| `button_notext` | 32 | `b1_decrect` | nincs |
| `button_text_LC` | 21 | `b1_decrect` | `m_buttonfontLC` (bal 8 / jobb 32 — ikonnak hely) |
| `buttcon_checkbox` | 16 | `checkbox2` | nincs (`button_buttcon`) |
| `buttonmini_text_center` | 13 | `b2_decrect` | `m_buttonfontC` |
| `quicktag_button` | 11 | `b3_decrect` | `m_quicktag_buttonfont`, 5 px oldalt, 2 px fent/lent |
| `drawer_tab` | 9 | `drawertab/{n,p,h}` | — |
| `button_text_center_throb` | 7 | `b1_decrect` + **`_t`** | `m_buttonfontC` |
| `button_tab` | 7 | `tab/{n,p,h}` | `m_displayfont14`, bal 28 / jobb −18 |
| `buttcon_plain` | 6 | `b1_decrect` | nincs |
| `button_text_LC_throb` | 6 | `b1_decrect` | `m_buttonfontLC` |
| `buttcon_MS/LS/RS_text_RC` | 3+2+2 | `mid/left/right_segment` | `m_buttonfontRCsegment` |
| `button_text_center_green` | 2 | **`b1_decrect_green_n` mindhárom állapotra** | `m_buttontypecolor3` (**fehér** szöveg) |
| `outline_button_text` | 2 | `ob1_decrect` | `m_buttonfontL` |
| `button_icon_left` | 2 | `b1_decrect` | `m_buttonfontRC` (bal 28) |
| `toggle_icon_left` | 2 | — | — |
| `button_header_option` | 1 | `b2_decrect` | `m_buttonfontC` |

### ⭐ A „throb" (villogó) stílus — MELYIK 13 elem villog, és MIÉRT (2026-09-05)

A táblázat két `_throb` sora (7 + 6 előfordulás) eddig csak **szám** volt.
A `runtime/respack.yt` teljes `superbutton(<stílus>, …)` kötéslistájából a
**13 elem név szerint** megvan — ez a **teljes** lista, nem minta
(171 `superbutton`-kötésből 13):

| panel | stílus | elem |
|---|---|---|
| `acquirepanel` | `button_text_LC_throb` | `anowbutton` *(Importálás)* |
| `printpanel` | `button_text_LC_throb` | `pnowbutton` *(Nyomtatás)* |
| `publish` | `button_text_LC_throb` | `backup_go` *(Burn Disc — biztonsági mentés)* |
| `publish` | `button_text_LC_throb` | `replicate_go` *(go)* |
| `publish` | `button_text_LC_throb` | `presentcd_go` *(Burn Disc — Ajándék CD)* |
| `publish` | `button_text_LC_throb` | `webpublish_go` *(Web Publish)* |
| `collab` | `button_text_center_throb` | `ok` *(Upload)* |
| `collagepanel` | `button_text_center_throb` | `sharebutton` |
| `compose_share` | `button_text_center_throb` | `send` *(Send)* |
| `makemoviepanel` | `button_text_center_throb` | `render` *(make_movie)* |
| `printoptions` | `button_text_center_throb` | `ok` |
| `thumbui` | `button_text_center_throb` | **`single_action_return`** |
| `upload` | `button_text_center_throb` | `ok` *(Upload)* |

**A minta egy mondatban:** minden panelen **a fő cselekvés gombja** villog —
Importálás, Nyomtatás, Lemezírás, Feltöltés, Küldés, Film készítése, OK,
Megosztás —, a többi gomb nem.

#### A villogás FELTÉTELE — mérve, dekompiláció nélkül

A `ytPopupListNodeCreator` (`FUN_00608da0`) a csomópont építésekor
**négy 40 bájtos képobjektumot** másol az elemből, egymás után, ugyanazzal a
másoló operátorral (`0x009a8ca0`, `rep movsd` `ecx=0xa` ⇒ pontosan 40 bájt):

| forrás | állapot |
|---|---|
| `elem + 0x264` | `_n` (nyugalmi) |
| `elem + 0x28c` | `_p` (lenyomott) |
| `elem + 0x2b4` | `_h` (rámutatott) |
| `elem + 0x2dc` | **`_t` (throb)** |

majd — **mindkét hívóhelyen azonos alakban** (`0x00609248` és `0x006095fc`) —
megnézi a **negyedik** kép egyik mezőjét, és ha nem nulla, bekapcsolja a
villogást:

```
lea  <r>, [elem + 0x2dc]      ; a negyedik állapotkép
push <r>
lea  eax, [esp + N]
call 0x009a8ca0               ; másolás
cmp  dword ptr [esp + N + 4], ebx   ; ebx = 0
je   tovább
mov  byte ptr [elem + 0x35b], 1     ; THROB BE
```

**A vizsgált mező a kép SZÉLESSÉGE.** A képosztály 40 bájtos kiosztása a
konstruktoraiból olvasva: `+4` és `+8` = szélesség, `+0xc` = magasság
(`0x009a8a80`: `mov [esi+4],ecx` / `mov [esi+8],ecx` / `mov [esi+0xc],ecx2`;
`0x009a8b60` téglalapból: `+4 = jobb − bal`, `+0xc = alsó − felső`;
`0x009a8bc0` a felszabadításnál `imul [esi+0xc]` az `[esi+8]`-cal ⇒
szélesség × magasság).

⇒ **Egy elem akkor és csak akkor villog, ha a stílusa ad neki negyedik
(`_t`) állapotképet.** Nincs futásidejű vagy felhasználói feltétel: a
villogás a csomópont megépítésekor indul, és az **`eThrobOff`** parancs
kapcsolja ki (`0x00601eb0`).

**Kimerítő ellenőrzés a stílusokon:** a 141 `.tre` erőforrásból **pontosan
kettő** deklarál `button_state_decrect_t`-t —
`button_text_center_throb.tre` és `button_text_LC_throb.tre`. A közönséges
párjuk (`button_text_LC.tre`) csak a `_n`/`_p`/`_h` hármast adja.

⚠️ **Szerkezeti megjegyzés, ami két kört félrevitt:** a stílus↔elem kötés
**nincs benne a `.tre` szövegekben**. A 141 fájlból 89-et soha semmi nem
`#include`-ol, és a stílusnevekre (`button_text_LC`, `buttcon_LS_text_RC`, …)
**nulla** hivatkozás van a `.tre` halmazban. *(Kontroll: a panel-fájlok
nevére VAN hivatkozás — a nulla tehát nem a keresés hibája.)* A kötés a
`respack.yt` `layer:<panel>/superbutton(<stílus>, <arg>): <név>` rekordjaiban
él, és **csak onnan** olvasható ki.

**Két nem nyilvánvaló részlet:**

1. A **zöld gomb** (`button_text_center_green`) **mindhárom állapotában
   ugyanazt a képet** használja (`b1_decrect_green_n`) — nincs
   rámutatás- vagy lenyomás-visszajelzése, csak a szövege fehér.
2. A `listheader_button` (51 előfordulás!) **feliratot egyáltalán nem
   rajzol** — a `.tre`-ben a `cd -label` blokk ki van kommentezve. Ami
   rajta látszik, az külön gyerekelem.

---

## 5. Szövegszínek — `Property typecolor`

Három ARGB érték: **normál · rámutatás · lenyomott**.

| makró | értékek | jelentés |
|---|---|---|
| `m_buttontypecolor` | `CC000000 CC000000 CC000000` | **80 %-os fekete, mindhárom állapotban ugyanaz** |
| `m_buttontypecolor2` | `CC000000 FFFFFFFF CC000000` | rámutatásra **fehérre vált** |
| `m_buttontypecolor3` | `FFFFFFFF CCFFFFFF FFFFFFFF` | fehér szöveg (zöld gombon) |
| `m_buttontypecolor4` | `99000000 99000000 99000000` | 60 %-os fekete (halványabb) |
| `m_buttonfont12` beépítve | `FF000000 FFFFFFFF FF000000` | teli fekete |

> **A gombfelirat alapból NEM teli fekete, hanem `#000000` 80 %-os
> átlátszatlansággal** (`CC` = 204/255). A világosszürke gombháton ez
> érezhetően lágyabb, mint a tiszta fekete.

---

## 6. Tipográfia — a teljes létra

Betűcsaládok (`fontmacros_win.tre`):

| család | hol |
|---|---|
| **`Praxis Semi Bold/Heavy`** | 52 makróban — a felület alapbetűje |
| `Praxis LT Regular` | 4 makróban (16 és 18 px, súly 400) |
| `Georgia` | 4 makróban |
| `Arial Bold` | 1 makróban (24 px) |

**A gombfelirat pontos beállítása** (`m_buttonfontC`, a leggyakoribb):

```
fontname   Praxis Semi Bold/Heavy
fontsize   12
fontweight 400
fonttrack  -1          ← betűköz −1 px
fontleading 10         ← sorköz 10 px
textalign  center
textwrap   1
XConstraint 0, 0,  5   ← bal margó  5 px
XConstraint 1, 1, -5   ← jobb margó 5 px
YConstraint 0.5, 0.5, 0 ← függőlegesen középre
```

**A szövegmargók stílusonként** (ez adja meg, hova fér ikon vagy nyíl):

| makró | bal | jobb | mire |
|---|---:|---:|---|
| `m_buttonfontC` | 5 | 5 | sima középre zárt gomb |
| `m_buttonfontL` | 3 | 3 | balra zárt |
| `m_buttonfontLC` | 8 | **32** | jobb oldali ikonnak hely |
| `m_buttonfontRC` | **28** | 6 | bal oldali ikonnak hely |
| `m_buttonfontRCsegment` | 22 | 6 | szegmentált gomb |
| `m_buttonfontRCmenu` | 28 | **19** | bal ikon + jobb menünyíl |
| `m_buttonfontLmenu` | 10 | **19** | jobb menünyíl |
| `m_tabfontC` | 4 | 4 | fül (és `YConstraint .5,.5,**2**` — 2 px-szel lejjebb) |

**Rendszerbetűk** (nem Praxis): `m_systemfont11` (11 px / 400) ·
`m_systemfont14` (14 / **700**, sorköz 15) · `m_systemfont16` (16 / 700) ·
`m_systemfont17` (17 / 700).

**Ikon-pozicionálók:** `m_buttonicon` = jobbra −11 px, függőlegesen
középre · `m_buttoniconleft` = balra 9 px · `m_buttonicon_menu` = jobbra
−10 px, +1 px lejjebb.

---

## 7. Fülek — külön, hideg-szürke család

A fül **nem** a gomb-decrectből készül, hanem saját, **rögzített méretű**
(185 × 25) rétegekből, és a színe **kékes-szürke**, nem semleges:

| állapot | felül | alul |
|---|---|---|
| `tab/n` (inaktív) | `#CAD1D5` | `#9CA3A7` |
| `tab/h` (rámutatás) | `#E1E4E6` | `#C2C6C8` |
| `tab/p` (**aktív**) | `#F7F7F7` | (a panel színébe olvad) |

Vagyis az **aktív fül majdnem fehér** — összeolvad a panellel —, az
inaktív pedig hűvös szürke. A fül feliratának betűje **`m_displayfont14`**
(14 px), nem a 12-es gombbetű, és a szöveg **2 px-szel lejjebb** ül
(`m_tabfontC`).

A fülhöz tartozik egy **10 × 10-es bezáró glif** (`tab/close_{n,h,p}`).

A **fiók-fül** (`drawertab/{n,h,p}`) 56 × 25.

---

## 8. Panelen belüli legördülők (`popuplist`)

*Forrás: `collagepanel.tre:343` (`collagepanel/format_menu`) · `editpanel.tre:784` (`editpanel/crop_aspect_menu`) · `makemoviepanel.tre:287` (`makemoviepanel/fontfamily`) — és további 3 elem ugyanott.*

A vezérlő maga **21 px magas** (a 43 `popuplist` rétegből 30 pontosan 21;
a többi 19, 22 vagy 23).

**A lista-tételek beállítása** (`Property itempadding` = bal fent jobb lent):

> ⚠️ **Az alábbi tábla HIÁNYOS — a 8/d helyesbíti.** Hat értéket sorol
> (31 sor), a korpuszban viszont **tíz** különböző érték áll **36** aktív
> soron. A „bal fent jobb lent" sorrend ellenben IGAZOLÓDOTT, immár a
> binárisból (8/d.2).


| érték | hány helyen | jelentés |
|---|---:|---|
| `2 2 22 2` | 15 | a leggyakoribb — **22 px jobb margó** a pipának/nyílnak |
| `1 1 21 1` | 4 | szűkebb |
| `2 2 10 2` | 4 | betűtípus-listák (nincs jobb oldali jelölő) |
| `0 0 20 0` | 4 | margó nélküli |
| `2 2 5 2` | 3 | méret-listák (keskeny) |
| `2 3 23 4` | 1 | a kollázs Oldalformátuma |

**`Property maxrows`** — hány sor látszik görgetés nélkül:

| legördülő | maxrows |
|---|---:|
| `makemoviepanel/templatelist` | 17 |
| `editpanel/crop_aspect_menu` | **16** |
| `makemoviepanel/fontfamily` | 9 |
| `makemoviepanel/sizelist`, `printoptions/*` | 7 |
| `collagepanel/format_menu`, `thumbui/addtobuttcon` | **0** (= korlátlan) |

---
## 8/b A LETILTOTT állapot: alfa / 4 (2026-08-17, #893)

Nincs `_d` réteg, mert nem kell — a csomópont-rajzoló (`0x009e2a60`) az
alfát osztja:

```asm
0x009e3145  cmp byte ptr [esi+0x210], 0   ; „saját alfa felülír" jelző
0x009e314e  ha 1 → [rajz+0x5c] = [esi+0x248]        (a saját alfa)
0x009e315c  ha 0 → [rajz+0x5c] = ([rajz+0x5c] * [esi+0x248] + 128) >> 8
0x009e316f  cmp byte ptr [esi+0x20e], 0   ; ← LETILTVA (a Property disable)
0x009e3178  shr dword ptr [rajz+0x5c], 2  ; ← ALFA / 4  = 25 %
0x009e3180  ha 0 → egyáltalán nem rajzol
```

| mező | jelentés |
|---|---|
| `[csomópont+0x248]` | a saját alfa, 0…255 |
| `[csomópont+0x210]` | 1 → felülír, 0 → **szorzódik** a szülőével |
| `[csomópont+0x20e]` | letiltva → `>> 2` |

**Az öröklés szorzó**, 8 bites fixponttal és `+128`-as kerekítéssel — egy
50 %-os panelben lévő 50 %-os gomb 25 %-ot kap. **Kivétel nincs**: a `>> 2`
minden csomópontra fut, a zöld gombra is.

## 8/c A legördülő PANEL és a görgetősáv (2026-08-17, #894)

*Forrás: `scratch.tre:20` (`scratch/highlight`).*

**`listdecrect/listdecrect`** (17 × 17, nyújtható):

| sor | szín | mi ez |
|---|---|---|
| 0–1 | `#E8E8E8` | külső térköz |
| 2 | `#D6D6D6` | lágy árnyék |
| **3** | **`#BABABA`** | **a keret, 1 px** |
| 4–12 | **`#E8E8E8`** | **a kitöltés — SÍK, nem átmenetes** |
| 13–14 | `#F8F8F8` → `#F0F0F0` | belső fénykiemelés alul |

Vízszintesen az árnyék `#DDDDDD` → `#C7C7C7` (a bal él sötétebb, mint a
felső — ugyanaz a bal-felüli fényforrás, mint a gomboknál).

**A görgetősáv saját rajz**, és **platformonként külön**:

| réteg | méret |
|---|---|
| `scrollart/base_win` | 15 × 25 — vízszintes átmenet `#B6B6B6` → `#EDEDED`, jobb szélen `#C8C8C8` |
| `scrollart/base_mac` · `base_mac_rounded` | 15 × 25 · 16 × 25 |
| `scrollart/nextalbum_{n,h,p}_win` / `_mac` | 16 × 24 / 15 × 19 |

A **kiemelt sor** a `.tre`-ben `Property round 2`, a felirat dobozánál
**±4 px vízszintesen** és **+1 px lent** nagyobb (`scratch/highlight`).

**A SZÍNE MEGVAN (2026-08-21): `#7D8397`** — kódkonstans, a binárisban
**`0xFF7D8397`** alakban.

> ⚠️ **A 2026-08-18-i negatív eredmény TÉVES VOLT.** Az akkori kör azt
> írta: *„a `.text` egészében **nincs** `0x7D8397` immediate — a bináris
> nem erősíti meg [a képernyőképről mért értéket]"*. **A keresés volt
> hibás:** a konstans **32 bites, alfával** (`0xFF7D8397`), nem 24 bites.
> A helyes alakra **négy találat** van. *(A bájtsorrendet külön
> kalibráltuk: a fordított alak, `0xFF97837D`, a binárisban **egyszer sem**
> fordul elő — ld. `picasa-kollazs-felulet.md` 2/b.3.)*

### A rajzolási minta — háromszor, szó szerint ugyanaz

```asm
test byte ptr [sor + 4], 2        ; << a sor-rekord +4 mezőjének 2-es bitje = KIJELÖLT
mov  ecx, <alapértelmezett háttér>
je   <marad az alapértelmezett>
mov  ecx, 0xff7d8397              ; << KIJELÖLVE
```

### A négy hely — és melyik lista

| cím | osztály / lista | bizonyíték |
|---|---|---|
| `0x006084e2` | **`ytTextPopupListItem`** és **`ytTextSeparatorPopupListItem`** vtable **2. rekesze** — a **legördülő listák tételei** | RTTI (`0x00c80574`, `0x00c9e994`) |
| `0x00665bc9` | **`CAddToList`** vtable **1. rekesze** | RTTI (`0x00ca2db8`) |
| `0x007af034` | a **feltöltés album-listájának** stílusblokkja (`[obj+0x98c]`) | `upload/#folder`, `upload/#album` |
| `0x007cea13` | a webalbum-panel sorrajzolója | a `0x007aa080` szomszédságában |

Mindhárom rajzoló a **`Praxis Semi Bold/Heavy`** betűt használja —
ugyanaz, amit a Mappakezelő fája (`picasa-mappakezelo.md` 4.4).

### Független megerősítés

A tulajdonos képernyőképén a **Mappakezelő kijelölt sorára mért**
`#7D8397` (`picasa-mappakezelo.md` 4.4) **bitre egyezik** a binárisban
talált konstanssal. A képernyőkép-mérés és a bináris tehát **egymást
igazolja** — a 2026-08-18-i kör azért nem látta így, mert rossz alakra
keresett.

### Bónusz: a szomszédos színek és metrikák

A `CAddToList` sorrajzolójából (`0x00665bc2`): a **nem kijelölt** sor
háttere **`#FDFDFD`**.

A feltöltés-lista stílusblokkjából (`0x007af010`) egy egész készlet:

| mező | érték |
|---|---|
| `[+0x960]` | `0x17` = 23 |
| `[+0x964]` | `0x0f` = 15 |
| `[+0x968]` | 5 |
| `[+0x96c]` | 2 |
| `[+0x974]` | **`#6D6D6D`** |
| `[+0x98c]` | **`#7D8397`** (a kiemelés) |
| `[+0x99c]` | `0x0e` = 14 |
| `[+0x9a0]` | **`#000000`** |
| `[+0x9ac]` | 2 |
| `[+0x9b0]` | −2 |

### 8/b A buboréksúgó rajza — hol NINCS (2026-08-21, G2 + kiegészítés)

A `ytToolTip` **megjelenése** (háttér, keret, árnyék) továbbra sem
mérhető ki a binárisból az olcsó lánccal. Hogy a következő kör ne járja
újra ugyanezt, itt a **teljes negatív leltár** — a kör elején (G2) hét
helyen kerestük, a felhasználó kérésére **négy továbbival** bővítve:

| hol kerestük | eredmény |
|---|---|
| a `ytToolTip` **csomópont-vtable**-je (`0x00c909d4`, 30 rekesz) | **egyetlen saját rajzoló-felülírás sincs** — mind a 30 rekesz általános (`0x009e0…`, `0x00a6…`, `0x0051…`) |
| a **konstruktor** (`0x00563060`, 224 b, teljes egészében kiolvasva) | **csak pozíció (`ecx`-ből 4 dword) és két IDŐBÉLYEG** (`[0xc40298]`-hívás, kétszer, `+0x328`/`+0x330`-ba) — **szín-paraméter EGYÁLTALÁN nem érkezik hívóból**, és nincs is beégetve |
| az `IToolTip` felület (`0x00c90408`, 3 rekesz) | slot 0 = `0x00563040` (31 b, csak a vtable beállítása), a másik kettő `_purecall` |
| a **`0x00562000`–`0x00564500`** kódtartomány (az osztály környéke) | ARGB-konstans **nincs**: csak `0xFF000000`, `0xFFFFFFFF` és `-1`/`-2` őrértékek |
| a **respack**, teljes réteglista (nem csak a `.tre`-k) | **nincs** `tooltip`/`balloon`/`hint`/`callout`/`bubble` nevű `decrect`-réteg — a `listdecrect`, `tooldecrect`, `overlaydecrect` stb. mind MÁS elemé; van `tre:tooltips` (3595 b), de az **szövegforrás** (`Tooltip <vezérlő>` + felirat), nem elrendezés |
| a **`.tre`-k** | a `thumbui.tre` `#include tooltips.tre` — ugyanaz a szövegforrás |
| a létrehozó (`0x005733f0`, a `"tooltip"` névvel, `0x0057351e`) | a nevet a `0x009ccdf0`-nak adja át — **ez NEM csomópont-gyár, hanem egy globális NÉV-INTERNÁLÓ hashtábla** (39 hívó, `[0xd67914]` globális objektum) — szín ott sem lehet, mert a függvény semmilyen szín-adatot nem kezel |
| **⭐ ÚJ: a megosztott, öröklött rajzoló-metódusok TÖRZSE** (`0x009e0660`, `0x009e0700`, `0x009e08b0`, `0x009e0ad0`, `0x009e0990`, `0x009e0ed0` [a legnagyobb, 2028 b], `0x009e0b50`, `0x009e3970/90/b00`, `0x00a6be80`, `0x00a6c4b0`, `0x00a6be40`, `0x00a6bca0`) | végigpásztázva **32 bites `0xFF…`/`0xFE…` ARGB-mintára** (a G1 tanulsága szerint) — **egyetlen valódi találat sincs**, csak a `and esp, 0xfffffff8` verem-igazítás és hasonló bitmaszk-műveletek |
| **⭐ ÚJ: natív Win32 tooltip vezérlő** | a `COMCTL32.dll` importja **nem** tartalmaz tooltip-függvényt (csak `InitCommonControlsEx`, `PropertySheetA/W`, két ordinál — property sheet/wizard máshoz); a `"tooltips_class32"` / `"TOOLTIPS_CLASS"` szó **sehol nincs** a binárisban. **A buboréksúgó tehát biztosan a saját `ytToolTip`, nem az OS natív tooltipje.** |
| **⭐ ÚJ: `GetSysColor`** (rendszerszín-lekérdezés, pl. `COLOR_INFOBK` a klasszikus sárga tooltip-háttérhez) | **hat hívási helye van a binárisban, egyik sincs** a tooltip létrehozási/rajzolási láncban (`0x005733f0`, `0x00563060`, a fenti generikus rajzolók) — a szín tehát **nem az operációs rendszertől** jön futásidőben |

**Amit ez kizár:** a buboréksúgó megjelenése **nem** `.tre`-tulajdonság,
**nem** respack-réteg, **nem** az osztály saját kódjában ülő konstans,
**nem** az öröklött rajzoló-metódusok konstansa, **nem** natív Win32
vezérlő, és **nem** rendszerszín. Az egyetlen megmaradó lehetőség egy
futásidőben, más forrásból (pl. egy meg nem talált globális
„skin"/paletta-objektum) összeállított érték — ennek nyomon követése
már **bizonytalan kimenetelű, drága dekompiláció** lenne, hetekre
visszamenő adatfolyam-követéssel, konkrét célcím nélkül.

### 8/c A megjelenés MEGVAN — a tulajdonos képernyőképéből mérve (2026-08-21)

A tulajdonos beküldött egy buboréksúgót mutató képernyőképet
(`#901`, a „Finomhangolás" fül `Alapszínválasztás` pipettájáról). A
kép **képpontonként** kimérve — ez a projekt szabálya szerint önmagában
bizonyíték, a fenti negatív lelet pedig most már **meg is magyarázza**,
miért nincs egy csepp kód sem hozzá.

| tulajdonság | mért érték | hogyan |
|---|---|---|
| **kitöltés** | **`#F4F1E5`** (244, 241, 229) — meleg, halványkrém | képpontminta, szöveg- és élmentes belső terület |
| **keret** | **`#B7B5AC`** (183, 181, 172), **1 képpont**, teljes körben | a kitöltés és a panelháttér közti egyetlen sornyi/oszlopnyi eltérő pixel |
| **sarkok** | **DERÉKSZÖGŰEK** — nincs lekerekítés | a bal-felső és jobb-alsó sarok pixel-rácsa éles L-alakot ad, nincs átmeneti ívpixel |
| **szöveg** | tiszta **fekete** (`#000000` a betűmag) | a legsötétebb képpontok a szövegdobozban |
| **árnyék** | **VAN, de csak a JOBB és ALSÓ élen** — ~4–5 képpontos, sima (nem lépcsős) szürke elhalványulás a panel hátteréig; a **bal és felső élen NINCS árnyék** (éles átmenet panel→keret) | vízszintes/függőleges metszet mindkét párra |
| **a panel háttere** (amin a buborék ül) | `#E8E8E8` — összhangban a #894-ben mért legördülő-panel-színnel | referenciapont a fentiekhez |

**A csak-jobb/alsó árnyék a döntő nyom.** Egy alkalmazás-rajzolt árnyék
tetszőleges alakú lehetne; egy **kétoldalas, éles vágású, azonos
mélységű** árnyék pontosan az, amit a Win32 **`CS_DROPSHADOW`**
ablakosztály-stílus ad automatikusan a felugró ablakoknak (a rendszer
rajzolja, az alkalmazás kódja nem lát belőle semmit). **Ez összhangban
van a 8/b teljes negatív lelettel**: nem azért nincs árnyék-kód a
binárisban, mert nem találtuk meg, hanem mert **nincs is** — az
operációs rendszer rajzolja rá.

**Következtetés a kitöltésre és a keretre:** ha ezek sem
alkalmazáskódból jönnek (a 8/b tizenegy pontja ezt kizárta), a
legvalószínűbb magyarázat egy **Windows rendszerszín-pár**, amit a
korábbi `GetSysColor`-keresésünk **nem** talált meg a tooltip-lánc
közelében — vagyis vagy egy **közvetett** hívási úton jut oda (amit nem
követtünk végig), vagy egy **futásidőben betöltött, statikusan nem
látható** skin-objektumból. *(A klasszikus Win32 `COLOR_INFOBK`
alapértéke `#FFFFE1` lenne — közel, de NEM egyezik a mért `#F4F1E5`-tel,
tehát ez feltehetően egy egyéni, nem rendszer-alapértelmezett szín.)*

**Kész, ha** (a PicasaPy megvalósításának): a buboréksúgó kitöltése
`#F4F1E5`, kerete `#B7B5AC` 1 px, derékszögű sarkokkal, és — ha a
platform/Qt engedi — árnyék csak a jobb és alsó élen.

**Jegy: #901** — a leltár most már **pozitív mérési eredménnyel**
zárható; a nyitva maradó rész csak a *miért éppen ez a szín* kérdés
(nem befolyásolja a megvalósítást).

> *A színmérésnél a G1 tanulságát alkalmaztuk: a Picasa a színeket
> **32 bites `0xAARRGGBB`** alakban tárolja — de ez a kép önmagában
> 24 bites RGB-ként mérhető, a csomagolás csak a bináris-oldali
> kereséshez számított.*

## 8/d A legördülő-tételek beállításai a BINÁRISBÓL (2026-09-10, #2856)

**Bizalmi fok: megerősített.** A 8. szakasz a `.tre`-ből következtetett; ez a
szakasz a feldolgozó kódból igazolja, és két hibát javít.

### 8/d.1 A feldolgozó és a formátum

A `FUN_00609680` (1352 bájt) kezeli a `popuplist` négy tulajdonságát. Az
`itempadding` ága négy egészet olvas:

```
0x00609727  mov dword ptr [esp+0x18], ebx    ; mind a négy tag 0-ra
0x0060972b  mov dword ptr [esp+0x1c], ebx
0x0060972f  mov dword ptr [esp+0x20], ebx
0x00609733  mov dword ptr [esp+0x24], ebx
…
0x00609784  push 0xc9af74                    ; a formátum: "%d %d %d %d"
0x0060978a  call _sscanf
0x00609796  lea ecx, [esp+0x18]              ; a négyes címe
0x0060979a  call 0x6081d0                    ; a beállító
```

⇒ **hiányzó szám = 0**, mert az előtöltés nullázza mind a négyet.

A `0x006081d0` (83 bájt) a négy értéket a lista `+0x404`, `+0x408`, `+0x40c`,
`+0x410` tagjába teszi, és ha bármelyik változott, `or dword ptr [eax+8], 7`
— ugyanaz az újrarajzolás-jelző, mint a `megjelenitesi-modok.md` 11. pontjában.

### 8/d.2 ⭐ A sorrend IGAZOLVA: bal · fent · jobb · lent

A fogyasztó `0x00608a00`-ban a négyesből téglalapot épít:

```
0x00608af8  mov eax, dword ptr [esi + 0x404]        ; x  = p1          (BAL)
0x00608afe  mov ecx, dword ptr [esi + 0x408]        ; y  = p2          (FENT)
0x00608b04  mov edx, dword ptr [esi + 0x26c]
0x00608b0a  sub edx, dword ptr [esi + 0x40c]        ; jobb = szél − p3 (JOBB)
0x00608b1c  mov eax, dword ptr [esp + 0x14]
0x00608b20  sub eax, dword ptr [esi + 0x410]        ; alj  = mag − p4  (LENT)
```

A méretszámoló (`0x00608820`) ugyanezt a párosítást használja: a **szélességből**
a `p3` és a `p1`, a **magasságból** a `p4` és a `p2` vonódik le
(`0x0060890d`, `0x00608913`, `0x00608919`, `0x0060891f`).

⇒ a 8. szakasz „bal fent jobb lent" olvasata **helyes**, és most mérve is van.

### 8/d.3 ⛔ HELYESBÍTÉS: a 8. értéktáblája hiányos

A korpuszban **37** `Property itempadding` sor van, ebből **1 kikommentezett**
⇒ 36 aktív, **tíz** különböző értékkel:

| érték | db |
|---|---:|
| `2 2 22 2` | 15 |
| `2 2 10 2` · `1 1 21 1` · `0 0 20 0` | 4 · 4 · 4 |
| `2 2 5 2` | 3 |
| `1 2 21 1` | 2 |
| `2 3 23 4` · `2 2 20 4` · `2 2 20 2` · `2 1 23 2` | 1 · 1 · 1 · 1 |

A 8. szakasz hat értéket sorolt (31 sor) — a hiányzó négy érték öt sora
maradt ki.

### 8/d.4 A másik három tulajdonság

| `.tre` | mit ír | hol | megjegyzés |
|---|---|---|---|
| `maxrows N` | `[lista+0x290] = N` | `0x0060988d` | az `sscanf` kimeneti helye előre **10**-re van töltve (`0x00609817`), tehát olvashatatlan érték esetén 10 marad |
| `customwidth N` | `[lista+0x280] = 2` **és** `[lista+0x28c] = N` | `0x00609981`, `0x00609987` | a `+0x280` **méretezési MÓD**; a `2` a „megadott szélesség" — tehát más módok is vannak |
| `handlealphakeys` | `byte [lista+0x275] = 1` | `0x00609b89` | **értéket nem olvas** — ezért áll a `.tre`-ben szám nélkül |

Mindhárom `or dword ptr [eax+8], 7`-tel jelzi az újrarajzolást, ha az érték
változott.

⚠️ A `+0x280` méretezési mód többi értéke (`0`, `1`, …) **NINCS feltárva** —
ez a `customwidth` nélküli legördülők útja.

## 8/e A legördülő SZÉLESSÉGE — négy méretezési mód (2026-09-10, #2859)

**Bizalmi fok: megerősített.** Minden szám kiolvasott immediate vagy cím
szerinti utasítás; a pásztázások indextől függetlenül futottak
(`eszkozok/binaris/paszta.py`, csúcs-RSS 86–87 MiB, kontrollpozitívval).

### 8/e.1 A két osztály, és hol lakik a beállítás

A `.tre`-elem a **`ytPopupListNode`** (`vftable 0xc9afb4`, konstruktor
`FUN_00608700`). Ez a konstruktorában **`0x294` bájtot foglal**
(`0x0060876c push 0x294`), és a benne épített listát a **`+0x3f8`** tagjába
teszi (`0x00608793`). A belső osztály a **`CPopupListContainer`**
(`vftable 0xca7f34`, konstruktor `FUN_0069d970`, `0x0069d994`).

A 8/d.4 „listaobjektum" tehát pontosan ez: a `CPopupListContainer`.

### 8/e.2 Az alapértékek — a konstruktorból kiolvasva

```
0x0069d9bb  mov dword ptr [ebp + 0x280], ebx      ; méretezési MÓD  = 0
0x0069d9c1  mov byte  ptr [ebp + 0x284], 1        ; egy logikai jelző = 1
0x0069d9c8  mov dword ptr [ebp + 0x288], ebx      ; a 3-as mód forrása = 0
0x0069d9ce  mov dword ptr [ebp + 0x28c], ebx      ; customwidth = 0
0x0069d9d4  mov dword ptr [ebp + 0x290], 0xa      ; maxrows = 10
0x0069d9b5  mov byte  ptr [ebp + 0x275], bl       ; handlealphakeys = 0
```

A `ytPopupListNode` konstruktora ezt még egyszer megerősíti: `0x0060878e
mov ecx, 0xa` → `0x006087a5 mov [eax+0x290], ecx`. ⇒ a 8/d.4-ben az
`sscanf` előtöltéséből következtetett **10-es alapérték immár a
konstruktorból is mérve van**.

### 8/e.3 ⭐ A NÉGY mód — a szélességszámító `FUN_0069e010`-ből

```
0x0069e163  mov ecx, dword ptr [esi + 0x280]      ; a mód
0x0069e16f  cmp ecx, edi                          ; edi = 0
0x0069e171  jne 0x69e1ac
0x0069e173  add eax, 8                            ; ⭐ MÓD 0
…
0x0069e1ac  cmp ecx, 2
0x0069e1af  lea edx, [eax + eax*2 + 8]            ; ⭐ MÓD 1 (a nem-0 alapja)
0x0069e1b7  jne 0x69e1c1
0x0069e1b9  mov eax, dword ptr [esi + 0x28c]      ; ⭐ MÓD 2
0x0069e1c1  cmp ecx, 3
0x0069e1c4  jne 0x69e1d0
0x0069e1c7  call 0x69e390                         ; ⭐ MÓD 3
```

| mód | a lista szélessége | ki állítja be |
|---:|---|---|
| **0** | a tételek mért szélessége **+ 8** | az **alapértelmezés** (konstruktor) |
| **1** | a mért szélesség **× 3 + 8** | kódból, nem `.tre`-ből |
| **2** | a **`customwidth`** értéke | `Property customwidth N` (8/d.4) |
| **3** | a `0x0069e390` számolja a `+0x288` gyűjteményből | kódból |

⇒ a korpuszban a `customwidth` **egyetlen** helyen áll, tehát a legördülők
**túlnyomó többsége a 0-s módban fut**: mért szélesség + 8 képpont.

### 8/e.4 A mód a VÍZSZINTES IGAZÍTÁST is átkapcsolja

Ugyanez a függvény kétszer külön vizsgálja az **1**-es módot, és más
x-képletet használ:

```
0x0069e23d  cmp dword ptr [esi + 0x280], 1
0x0069e24a  lea eax, [eax + eax + 4]              ; 1-es mód
0x0069e25c  sub ecx, eax ; add ecx, 4             ; minden más
…
0x0069e273  cmp dword ptr [esi + 0x280], 1
0x0069e27c  mov ecx, 0xfffffffe ; sub ecx, eax ; add ecx, ecx
0x0069e28f  sub eax, [esp+0x20] ; sub eax, 4
```

A `+0x284` bájt (alapból **1**) választ a két ág-pár között
(`0x0069e1ff cmp byte ptr [esi + 0x284], 0`).

### 8/e.5 Ami NYITVA marad

A **3-as mód** forrása, a `+0x288` gyűjtemény: a `0x0069e390` a
`[eax+0x10]` darabszámmal iterál rajta (`0x0069e3ed`). Hogy **mit** tárol
ez a gyűjtemény, és melyik kód állítja be, nincs feltárva. A `+0x284`
jelző jelentése szintén nyitott.

## 8/f A modell és a `justify` — a 8/e.5 két nyitott mezője (2026-09-10, #2862)

**Bizalmi fok: megerősített.** Minden állítás mellett cím; a pásztázások
indextől függetlenül futottak, kontrollpozitívval.

### 8/f.1 A `+0x288` a lista ADATMODELLJE

Az író a **`FUN_00608b70`** (141 bájt) — a `ytPopupListNode` modell-beállítója:

```
0x00608b93  mov eax, dword ptr [ebx + 0x3f8]     ; a belső lista
0x00608b9d  mov dword ptr [eax + 0x288], 0       ; a RÉGI modell leválasztva
…
0x00608bb3  mov dword ptr [ebx + 0x400], edi     ; a node saját mutatója
0x00608bde  mov ecx, dword ptr [ebx + 0x400]
0x00608be4  mov dword ptr [eax + 0x288], ecx     ; ⭐ az ÚJ modell
```

A régi modellt a **3.** vtábla-rekeszén értesíti (`0x00608b8a`–`0x00608b91`,
argumentum `1`), az újat a **4.**-en (`0x00608bbb`–`0x00608bc2`) — leválasztás
és becsatolás.

⇒ a `+0x288` ugyanaz az objektum, amit a csomópont a `+0x400`-ban tart: a
lista **tételforrása**. Elrendezése a használatból kiolvasva:
`+0xc` = mutatótömb, `+0x10` = a tételszám **kétszerese** (a bejáró
`shr ecx, 1`-gyel osztja, `0x0069e3fe` és `0x0069e46f`).

### 8/f.2 ⭐ A 3-as méretezési mód: a LEGSZÉLESEBB tételhez igazít

A `FUN_0069e390` (241 bájt) teljes menete:

```
0x0069e3a5  push 0xc95ebc                    ; "Praxis Semi Bold/Heavy"
0x0069e3aa  mov  eax, 0x190                  ; súly 400
0x0069e3af  mov  edi, 0xc                    ; méret 12
0x0069e390  fld  dword ptr [0xc7dbbc]        ; skála 1,4
0x0069e3b4  call 0xa48e10                    ; ⭐ a KÖZÖS betűgyorstár-gyár
…
0x0069e3e0  mov edi, [eax+8] ; sub edi, [eax] ; a JELENLEGI szélesség
0x0069e407  mov eax, dword ptr [edx + esi*4] ; a modell esi-edik tétele
0x0069e41d  call 0xc07db2                    ; __RTDynamicCast (0xd3b75c → 0xd3b71c)
0x0069e427  je  0x69e475                     ; ha nem illik: kihagyva
0x0069e453  call edx                         ; a gyorstár 12. rekesze: szövegmérés
0x0069e45a  add ecx, 0x10                    ; a mért szélesség + 16
0x0069e45f  jbe 0x69e463 ; mov edi, ecx      ; MAXIMUM
0x0069e475  mov eax, edi                     ; a visszaadott szélesség
```

⇒ **3-as mód = a modell azon tételeinek legszélesebbje + 16 képpont**, amelyek
a `0xd3b71c` típusra `dynamic_cast`-olhatók — és **soha nem szűkebb**, mint a
vezérlő jelenlegi szélessége.

A használt betű ugyanaz, mint a 6. szakasz „a felület alapbetűje": **Praxis
Semi Bold/Heavy**, 12 px, súly 400. A gyár a `0x00a48e10`, ugyanaz, amit a
`picasa-megjelenitesi-modok.md` 16. szakasza azonosított (25 hívó).

### 8/f.3 ⭐ A `+0x284` a `Property justify` — és ⛔ ÖNHELYESBÍTÉS

A `+0x284` egyetlen írója a `0x00609a91`, a legördülő `Property`-feldolgozójában:

```
0x00609a12  push 0xc939b8                    ; "right"  ← az ÉRTÉK
…
0x00609a7e  sete cl
0x00609a81  cmp byte ptr [eax + 0x284], cl
0x00609a89  or  dword ptr [eax + 8], 7       ; újrarajzolás, ha változott
0x00609a91  mov byte ptr [eax + 0x284], cl
```

⇒ **`Property justify right` → `+0x284 = 1`**, bármi más → `0`. A konstruktor
alapértéke **1** (`0x0069d9c1`), tehát a legördülő **alapból jobbra igazít**.

⛔ **Helyesbítés a #2856 lezáró kommentjéhez:** ott az szerepelt, hogy a
`justify` „érték, nem kulcs". A `center`/`left`/`right` valóban értékek (az
`align`-é), de a **`justify` KULCS** — a `right` az ő értéke.

⚠️ A korpuszban **egyetlen `Property justify` sor sincs** (`grep`), tehát ezt
a kulcsot a szállított `.tre` nem használja — a bináris viszont támogatja.
Ugyanaz a kategória, mint a `picasa-respack-format.md` 8.2 „csak a binárisban"
listája, csak itt az elemtípus-függő feldolgozóban.

### 8/f.4 Amit a jelző CSINÁL

A `FUN_0069e010` a `0x0069e1ff cmp byte ptr [esi + 0x284], 0` alapján két
teljesen külön x-számítási ág-párt futtat (8/e.4). A `.tre`-név szerint ez a
jobbra igazítás; a két ág **képlete** ki van írva a 8/e.4-ben, a
**vizuális** hatás mérése (renderelt kimenet vs. referencia) nincs meg.

## 9. A gomb-rétegek teljes leltára

269 réteg a `globalbuttons/` névtérben. A névadás **kivétel nélkül**
`<alap>_<állapot>`, ahol az állapot:

| utótag | jelentés |
|---|---|
| `_n` | normál |
| `_h` | rámutatás (hover) |
| `_p` | lenyomott (pressed) |
| `_t` | **bekapcsolt** (toggled) — csak 11 rétegnél |

Néhány régebbi réteg a teljes szót írja ki: `wnormal`/`whover`/`wpress`/
**`wthrob`**, `mb_normal`/`mb_hover`/`mb_press`,
`prevnormal`/`prevhover`/`prevpress`, `roundnormal`/`roundhover`/
`roundpress`, `walletnormal`/…, `3x5normal`/`4x6normal`/`5x7normal`/
`8x10normal`/`fullnormal` (a nyomtatási méretválasztó 70 × 59-es lapkái).

**Méretcsalád szerint** (mind 28 px magas, ha nincs jelölve):
`b32` 32 · `b38` 40 · `b38a/b38l/b38r` 37 × **21** · `b48` 49 ·
`b72` 71 · `b88` 88 · `b98` 98 · `b132` 132 · `b150` 150.

A `#`-tel kezdődő nevek (`#chip_public`, `#chip_circle`, …)
**kikommentezettek** — nem jelennek meg.

---

## Bizonyítottsági fok

**Megerősített**: a 9-szeletes nyújtás 8 px-es sapkája (három mintán
mérve), minden állapotszín (képpontból olvasva), a stílus- és
betű-makrók (a `.tre` szó szerinti tartalma), a kétféle menürendszer (az
importtábla és a menüépítő).

**Nyitott**: hogyan rajzolja a program a **letiltott** gombot (nincs `_d`
réteg); a `popuplist` legördülő **panel** háttérszíne és keretszíne (a
rétegek csak a bezárt vezérlőt tartalmazzák, a lenyíló listát kód rajzolja).
