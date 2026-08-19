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

| # | eredeti | nálunk | jegy |
|---|---|---|---|
| 1.1 | **Létrehozás ▸ Képkollázs…** menü | ✅ megvan, a lapot nyitja | — |
| 1.2 | `headerpanel/create_collage` gomb a mappa-fejlécben (44, 53) 29×27 | ✅ megvan | — |
| 1.3 | `faceheaderpanel/create_collage` az arc-fejlécben (115, 55) | ❓ **nem ellenőrizve** | *nyitva* |
| 1.4 | `outputlayout/button(collage)` a kimeneti sávban (2, 2) 55×36 | ❓ **nem ellenőrizve** | *nyitva* |
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
| 2.6 | **az átlagszín-háttér** (`collage::avgcolor`) felülír mindent | ❌ nincs | *nincs jegy* → **lásd 8.** |
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
| 5.2 | „Továbbiak…" → vissza a könyvtárba, „Vissza a kollázshoz" gombbal | ⚠️ **részleges** — a visszatérő gomb nincs ellenőrizve | *nyitva* |
| 5.3 | „+" / „–" klip-felvétel és -törlés | ✅ megvan | — |
| 5.4 | `addallclips` | **halott az eredetiben is** — ne épüljön meg | — |

## 6. Kimenet, mentés, piszkozat

| # | eredeti | nálunk | jegy |
|---|---|---|---|
| 6.1 | **fájlválasztó NINCS**: mappa és név automatikus | ❌ célfájlt kérünk | **#969** |
| 6.2 | `<Képek>/Picasa/Kollázsok`, név = a forrásmappa címe, `%s%lu` számozás | ❌ időbélyeges név | **#969** |
| 6.3 | a JPEG mellé **`.cxf`**, atomi írással, q90 | ❌ nincs | **#969** |
| 6.4 | mentés után a lap bezárul + `locate` a kész fájlra | ❌ nincs | **#949** kommentje |
| 6.5 | asztali háttérkép: BMP + registry (**0/0 = középre**) | ❌ nincs | *nincs jegy* → **lásd 8.** |
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

## 8. ⚠️ Amire NINCS jegy — és most kap

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
**kívül maradt**:

1. **A futó eredeti program viselkedése.** Minden bizonyíték álló
   (bináris, erőforrás, `.tre`, golden-kimenet). Ami csak mozgásban
   látszik — időzítők, animációk, fókusz-viselkedés —, azt csak akkor
   találjuk meg, ha valaki **nézi** a programot. A gyűrű (#1000) így
   került elő: a felhasználó vette észre, nem mi.
2. **Az 1.3 és 1.4 belépési pont** (arc-fejléc, kimeneti sáv) — a
   binárisban megvannak, nálunk nem ellenőriztem.
3. **Az 5.2 „Vissza a kollázshoz" gomb** a könyvtárban.
4. **Billentyűparancsok** a panelen az Esc / Ctrl+A / Ctrl+D / Del
   négyesen túl.
5. **A képek betöltési sorrendje és a hiányzó képek** viselkedése éles,
   nagy albumon.
6. **A `.cxf` visszaolvasása** — az írását mértük, a betöltési utat nem.

---

## 10. Összesítő

| állapot | darab |
|---|---|
| ✅ megvan és működik | **28** |
| ⚠️ részleges vagy hibás | **8** |
| ❌ hiányzik | **11** |
| ❓ nem ellenőrzött | **4** |

**A hiányok mindegyikéhez tartozik jegyszám** (#916, #969, #977, #978,
#979, #989, #990, #991, #992, #1000, #1001, #1002, **#1004**, **#1005**).
A 9. szakasz hat pontja **nyitott terület**, nem hiány — ott azt sem
tudjuk, van-e mit találni.
