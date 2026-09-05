# A Képkollázs TELJES átvilágítása — eredeti / nálunk / jegy (2026-08-19)

Ez a lap **nem új kutatás**, hanem **elszámolás**: a Kollázs funkció teljes
felületét egy táblában veszi végig, hogy ne apránként derüljön ki, mi
hiányzik. A felhasználó kérte, miután a hiányok több körön át, egyesével
kerültek elő.

**A módszer, amit a korábbi körök NEM követtek** (és emiatt maradtak
hiányok):

1. **Kívülről befelé.** Nem a panelből indulunk, hanem abból, amit a
   felhasználó lát és csinál — a panelen **kívüli** részekkel együtt.
2. **Külső, tételes lista.** A `collagepanel.tre` **100 élő** vezérlője, a
   128 `collage*` erőforrásnév és a vezérlő 41 slotja a kiindulás — nem a
   saját térképünk.
3. **Három oszlop**: *eredeti / nálunk / jegy*. Így a háromféle hiány
   külön látszik: nincs leírva · le van írva, de nincs megírva · meg van
   írva, de nem hat.
4. **Hat viselkedési kérdés vezérlőnként**: mikor **látszik**, mikor
   **aktív**, mit tesz **kattintásra**, mit **hoverre**, mit **húzás
   közben**, mi történik **utána**. A „hoverre" sort a korábbi körök
   egyszer sem tették fel — a gyűrű hibája (#1000) ezért maradt rejtve.

---

## 1. Belépési pontok — hogyan jutok a kollázshoz

*Forrás: `editpanel.tre:1350` (`editpanel/editcollage`) · `faceheaderpanel.tre:100` (`faceheaderpanel/create_collage`) · `headerpanel.tre:89` (`headerpanel/create_collage`).*

| # | eredeti | nálunk | jegy |
|---|---|---|---|
| 1.1 | **Létrehozás ▸ Képkollázs…** menü | ✅ megvan, a lapot nyitja | — |
| 1.2 | `headerpanel/create_collage` gomb a mappa-fejlécben (44, 53) 29×27 | ❌ **nincs** *(a lap első kiadása tévesen késznek jelölte)* | **#1006** |
| 1.3 | `faceheaderpanel/create_collage` az arc-fejlécben (115, 55) | ❌ **nincs** *(2026-08-19-én ellenőrizve)* | **#1006** |
| 1.4 | `outputlayout/button(collage)` a kimeneti sávban (2, 2) 55×36 | ✅ **megvan** — `TrayBar.qml` *(2026-08-19-én ellenőrizve)* | — |
| 1.5 | a **Kollázsok** album elemére duplakattintás → a `.cxf` visszatöltése | ❌ nincs | **#1002** (a `.cxf` írása: **#969**) |
| 1.6 | **`editpanel/editcollage`** — „Kollázs szerkesztése" a szerkesztő fejlécében (142, 9) 128×22 | ❌ nincs | **#1002** |
## 2. A bal hasáb — „Beállítások" lap

| # | eredeti | nálunk | jegy |
|---|---|---|---|
| 2.1 | téma-választó, hat téma ikonnal + leírással | ✅ vezérlő megvan, **de a választás nem hat a vászonra** | **#989** (P0) |
| 2.2 | három keretgomb (`border0/1/2`), saját felirattal és súgóval | ✅ megvan (`CollageBorderPicker`) | felirat/súgó: **#946** kommentje |
| 2.3 | térköz-csúszka (`spacing_group`), „Egyik sem"/„Maximális" | ✅ megvan | — |
| 2.4 | a keretsor és a térköz **ugyanazt a helyet** foglalja, sosem látszik együtt | ✅ maszkból vezérelve | — |
| 2.5 | háttér: egyszínű / kép + színválasztó + pipetta | ✅ megvan | — |
| 2.6 | **az átlagszín-háttér** (`collage::avgcolor`) felülír mindent | ❌ nincs | **#1004** |
| 2.7 | oldalformátum-lista (17 arány + egyéni) | ✅ megvan | — |
| 2.8 | tájolás (álló/fekvő) | ✅ megvan, **de nem rendez újra** | **#991** |
| 2.9 | árnyék-jelölő, képfelirat-jelölő, feliratra kattintva is kapcsol | ✅ megvan | — |
| 2.10 | „Beállítás képkockaközéppontként" + a **„Kötelező a kijelölés"** párbeszéd | ✅ gomb megvan; a párbeszéd szövege leírva | **#946** kommentje |
| 2.11 | négy alsó gomb (Asztali háttérkép, Kollázs létrehozása, Alaphelyzet, Bezárás) | ✅ megvan | — |

## 3. A vászon és a gyűrű

| # | eredeti | nálunk | jegy |
|---|---|---|---|
| 3.1 | kijelölés: kattintás, Ctrl, Shift, Ctrl+A/D, Del | ✅ megvan | — |
| 3.2 | **a gyűrű csak HOVERRE látszik** (+12 px), 0,5 s után elhalványul | ❌ mindig látszik | **#1000** |
| 3.3 | mozgatás **a gyűrűvel**, küszöb nélkül | ⚠️ a kép testével mozgatunk | **#990** |
| 3.4 | csere: a kép **testének** vonszolása 10 px-en túl + ejtés | ⚠️ ugyanaz a gesztus, ezért **visszaugranak a kártyák** | **#990** |
| 3.5 | `Ctrl`+kattintás **nem élesíti** a vonszolást | ❌ élesíti → **néma csere** | **#990** |
| 3.6 | forgatás+méretezés egy fogantyúval, `Ctrl`/`Alt` kikapcsol egyet | ✅ megvan | — |
| 3.7 | „Szög: %d" / „Méretarány: %d%%" húzás közben | ✅ **megvan és működik** | — |
| 3.8 | `Alt`+húzás: a kép a kupac tetejére | ✅ megvan | — |
| 3.9 | **árnyék** témánként külön paraméterekkel | ❌ kalibrálatlan | **#977** |
| 3.10 | Polaroid-**képfelirat** a keret alsó sávjában | ❌ nincs | **#978** |
| 3.11 | három helyi menü (1 kép / több kép / vászon) | ✅ megvan | — |

## 4. A lap körüli négy gombcsoport

| # | eredeti | nálunk | jegy |
|---|---|---|---|
| 4.1 | akciósor a lap fölött (4 gomb) | ✅ megvan, **de a magyar feliratok kilógnak** | **#992** |
| 4.2 | „Véletlenszerű kollázs" / „Képek összekeverése" / „Megjelenítés és szerkesztés" a lap alatt | ✅ megvan | — |
| 4.3 | **„Megjelenítés és szerkesztés"** megnyitja a képet a szerkesztőben | ❌ **a jelzésnek nincs fogadója** — némán nem történik semmi | **#1001** |
| 4.4 | forgatás-igazító oszlop (4 gomb), kijelöléskor | ✅ megvan | — |
| 4.5 | rétegsorrend-oszlop (4 gomb), `move_up/down` **autorepeat** | ✅ megvan | — |

## 5. „Klipek" lap

| # | eredeti | nálunk | jegy |
|---|---|---|---|
| 5.1 | fülfelirat futásidejű darabszámmal („Klipek (%d)") | ✅ megvan | — |
| 5.2 | „Továbbiak…" → vissza a könyvtárba, „Vissza a kollázshoz" gombbal | ✅ **megvan** — `Main.qml:1221` *(2026-08-19-én ellenőrizve)* | — |
| 5.3 | „+" / „–" klip-felvétel és -törlés | ✅ megvan | — |
| 5.4 | `addallclips` | **halott az eredetiben is** — ne épüljön meg | — |

## 6. Kimenet, mentés, piszkozat

| # | eredeti | nálunk | jegy |
|---|---|---|---|
| 6.1 | **fájlválasztó NINCS**: mappa és név automatikus | ❌ célfájlt kérünk | **#969** |
| 6.2 | `<Képek>/Picasa/Kollázsok`, név = a forrásmappa címe, `%s%lu` számozás | ❌ időbélyeges név | **#969** |
| 6.3 | a JPEG mellé **`.cxf`**, atomi írással, q90 | ❌ nincs | **#969** |
| 6.4 | mentés után a lap bezárul + `locate` a kész fájlra | ❌ nincs | **#949** kommentje |
| 6.5 | asztali háttérkép: BMP + registry (**0/0 = középre**) | ❌ nincs | **#1005** |
| 6.6 | folyamatjelző overlay, megszakítás megerősítéssel | ✅ megvan | — |
| 6.7 | piszkozat mentése bezáráskor | ✅ megvan | — |
| 6.8 | **időzített** automentés + helyreállítás induláskor | ❌ nincs | **#979** *(a #990 után!)* |

## 7. Elrendezés-algoritmusok

| # | eredeti | nálunk | jegy |
|---|---|---|---|
| 7.1 | hat pakoló | ✅ a **magban** kész | — |
| 7.2 | a panel a téma pakolóját használja | ❌ **mindig szórás** | **#989** |
| 7.3 | térköz-szabály (külső margó = belső rés; függőleges × `W/H`) | ✅ a magban helyes, **mérve igazolva** | — |
| 7.4 | Képkockamozaik kényszeres pakolója | ⚠️ közelítés | **#916** |

---

## 8. Amire az átvilágítás ELŐTT nem volt jegy

Az átvilágítás két olyan hiányt talált, ami eddig sehol nem szerepelt:

- **2.6 — az átlagszín-háttér** (`collage::avgcolor`): az eredetiben a
  háttér lehet a képek átlagszíne, és ez **felülír minden más
  háttérbeállítást**. Nálunk a mód nem is létezik.
- **6.5 — az „Asztali háttérkép" második fele**: a kollázs elmentése után
  a BMP kiírása és a registry-beállítás. Nálunk a gomb megvan, a
  háttérképpé tétel nem.

- **2.6 → #1004** (átlagszín-háttér)
- **6.5 → #1005** (tényleges háttérkép-beállítás)

## 9. ⚠️ Amit NEM néztem meg — kimondva

Hogy a lefedettség állítása ne legyen önigazoló, itt a lista arról, ami
**kívül maradt**. *(2026-08-21-i átvizsgálás: hat pontból **kettő
elavult volt** — a lap 1. szakasza már lezárta őket, csak itt maradtak
benne —, egy pedig azóta megmérve. A lista ennek megfelelően frissítve.)*

1. **A futó eredeti program viselkedése.** Minden bizonyíték álló
   (bináris, erőforrás, `.tre`, golden-kimenet). Ami csak mozgásban
   látszik — időzítők, animációk, fókusz-viselkedés —, azt csak akkor
   találjuk meg, ha valaki **nézi** a programot. A gyűrű (#1000) így
   került elő: a felhasználó vette észre, nem mi.
   **Ez állandó módszertani korlát, nem elvégezhető feladat** — nem
   „nyitott kérdés", hanem a bizonyítéktípusunk határa.

2. ~~**Az 1.3 és 1.4 belépési pont**~~ — **ELAVULT TÉTEL VOLT.** A lap
   **1. szakasza mindkettőt rögzíti**, 2026-08-19-i ellenőrzéssel:
   1.3 (`faceheaderpanel/create_collage`) ❌ nincs nálunk → **#1006**;
   1.4 (`outputlayout/button(collage)`) ✅ **megvan**, `TrayBar.qml`.
   *(A 9. szakasz egyszerűen nem lett átvezetve.)*

3. ~~**Az 5.2 „Vissza a kollázshoz" gomb**~~ — **ELAVULT TÉTEL VOLT.**
   Nálunk **megvan**: `app/qml/Main.qml` (a `collagepanel::back_to_collage`
   gomb a könyvtár lapján, a fájl 1397. sora körül; a `PhotoViewer.qml`
   490–491. sora külön ki is mondja, hogy a nézegető visszalépése **nem
   azonos** ezzel).

4. ~~Billentyűparancsok~~ — **LEZÁRVA (2026-08-19)**: a
   `collagepanel.tre` egyetlen billentyűt deklarál, a
   `Property escapekey 1`-et (492. sor). A Ctrl+A / Ctrl+D / Del a
   parancstáblából ismert, és nálunk megvan.

5. **A képek betöltési SORRENDJE éles, nagy albumon.** *(A „hiányzó
   képek" fele azóta megvan: a hat üzenetkulcs a
   `picasa-kollazs-felulet.md` 9.3-ban, hivatalos magyar szöveggel, és a
   mi `collage/autosave.py`-unk a „egyik kép sem található" esetet
   kezeli.)* Ami marad: **milyen sorrendben** tölti be a képeket egy
   több száz elemű albumnál, és mit mutat közben. Ehhez futó program
   és nagy album kell — ld. az 1. pontot.

6. ~~**A `.cxf` visszaolvasása**~~ — **MEGMÉRVE (2026-08-21).** Az
   olvasó osztály a **`CCollageParser`** (vtable `0x00cbf878`), három
   érdemi metódussal, és a **teljes elemkészlete** kiolvasható:

   | függvény | méret | felismert nevek |
   |---|---|---|
   | `0x00832830` | 3555 b | `collage`, `version`, `format` (`%d:%d`), `orientation` (`portrait`/`landscape`), `theme` (`picturepile`…), `shadows`, `captions`, `image`, `value`, `color` |
   | `0x00833620` | 757 b | `theme`, **`albumTitle`**, **`albumDate`** |
   | `0x00833920` | 911 b | `collage`, `background` |

   A fájlválasztós betöltő (`0x0087ed80`, 1052 b) a `*.cxf` szűrővel és
   a „Mentett kollázsok" mappával dolgozik; a hozzá tartozó hat
   üzenetkulcs a `picasa-kollazs-felulet.md` 9.3-ban már megvolt.
   *(Ez a betöltő a `savebutton`/`loadbutton` páros ága — a 11. szakasz
   szerint fejlesztői maradvány, nincs hozzá vezérlő a respackben.)*

   **A mi olvasónk lefedi a teljes szótárt.** A
   `src/picasapy/collage/cxf.py` `loads()`/`read_cxf()` mind a tizenhárom
   nevet ismeri (`version`, `format`, `orientation`, `theme`, `shadows`,
   `captions`, `background`, `color`, `image`, `albumTitle`, `albumDate`,
   `album_uid`, `album_id`) — **nincs olyan elem, amit az eredeti ért, mi
   pedig nem.**

---

## 10. Összesítő

| állapot | darab |
|---|---|
| ✅ megvan és működik | **29** |
| ⚠️ részleges vagy hibás | **7** |
| ❌ hiányzik | **13** |
| ❓ nem ellenőrzött | **2** |

**A hiányok mindegyikéhez tartozik jegyszám** (#916, #969, #977, #978,
#979, #989, #990, #991, #992, #1000, #1001, #1002, #1004, #1005, **#1006**).

*(2026-08-21: a 9. szakasz hat pontjából **kettő elavult volt** (a lap 1.
szakasza már lezárta őket), **egy** azóta lezárult (billentyűparancsok),
**egy** megmérve (a `.cxf` visszaolvasása), **egy** felére csökkent (a
hiányzó képek üzenetei megvannak, a betöltési sorrend nem). Ami **valóban**
nyitott: a **futó program** viselkedése és a **betöltési sorrend nagy
albumon** — mindkettő ugyanabba a korlátba ütközik.)*


---

## 11. ⚠️ A lap ELSŐ kiadásának hibái (2026-08-19, ugyanaznap javítva)

A felhasználó megkérdezte, hogy tényleg 100 %-os-e a feltárás. Az
ellenőrzés **öt perc alatt három hibát talált ebben a lapban**:

| sor | az első kiadás | a valóság |
|---|---|---|
| 1.2 | ✅ megvan | ❌ **nincs** — a fejléc-fájlokban egyetlen kollázs-hivatkozás sincs |
| 1.4 | ❓ nem ellenőrizve | ✅ **megvan** (`TrayBar.qml`) |
| 5.2 | ⚠️ részleges | ✅ **megvan** (`Main.qml:1221`) |

**A tanulság nem az, hogy „ellenőrizni kell".** Az, hogy a `✅` jelölést
**bizonyíték nélkül** tettem ki: az 1.2-nél a `kollazs-panel-ui-spec.md`
3.2-es táblája már 2026-08-18 óta írta, hogy a gomb hiányzik — csak nem
néztem meg. **Egy sor akkor kaphat `✅`-t, ha van mellé fájl+sor
hivatkozás**; enélkül `❓` a helyes jelölés.
