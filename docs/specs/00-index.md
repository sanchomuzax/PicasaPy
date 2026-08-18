# A specifikációk tartalomjegyzéke

**Ez a lap a belépési pont a `docs/specs/`-be.** Alább előbb a **valóban
nyitott kérdések** listája (ebből válasszon témát egy kutatói kör), majd a
34 spec-lap témakörönként.

**A lenti „Nyitott kérdések" lista kézzel ellenőrzött**, nem gépi
szó-számlálás. Egy 2026-08-16-i átvilágítás kimutatta, hogy a
`Nyitva`/`dekódolatlan` szavak **kétharmada hivatkozás** egy máshol már
megválaszolt pontra — a gépi számlálás tehát háromszorosára fújta a
képet (pl. `filterdesc-registry.md`: 6 találat, **0** valódi nyitott
kérdés).

*Utolsó átvilágítás: 2026-08-16 (a második, tízkörös menet után).*

## 🔶 Nyitott kérdések — innen válassz kutatói kört

### [filters-decoded.md](filters-decoded.md) — 1 kérdés

1. ~~**`autocolor` pontos gain-képlete** (Nyitva 1)~~ — **TELJESEN MEGVAN**
   (#759, 2026-08-18): `M · diag(g) · M⁻¹`, és a becslő egész-osztásai
   **nulla felé csonkolnak** (C-szemantika). Kimérve **0,614** (a mai kód
   2,352, a JPEG-zajszint ~0,69) — nincs nyitott kérdés, csak bekötés
2. ~~**`unsharp` kernel finomítása** (Nyitva 3)~~ — **MEGVAN** (#762):
   köbös B-spline, `× 1,5` szélesítéssel, σ ≈ 0,87. A mérés szerint a mai
   Gauss már „JÓ" (0,47) — finomítás, nem hiba
3. **Render-pontosítás** — ⭐ **a rangsor alapja a mért korpusz-gyakoriság**
   (`filters-decoded.md`, „A szűrők TÉNYLEGES gyakorisága").
   **A rangsor 2026-08-18-án ÚJRAÍRVA**, mert a régi alak nyolc áthúzott
   beszúrástól olvashatatlanná vált, és a tételei nagyrészt elavultak.

   | tétel | régi verdikt | MA | jegy |
   |---|---|---|---|
   | `finetune2` hőmérséklet | 55,94 ΔE · 561 kép | **megfejtve, bekötésre vár** — feketetest-tábla + `autocolor`-mátrix | #879 |
   | `tint` | 20,6 | megfejtve (`preserve` skálája −1…255) | #872 |
   | `sat` pozitív ág | 12 | ✅ **kész és kimérve: 0,74** | #693 |
   | `dir_tint` | 9 | ✅ **teljesen megvan** — az átmenet-görbe is (2026-08-18) | #874 |
   | `fill` | 6,5 | ✅ **eredeti exportokhoz mérve 1,20–1,77** (2026-08-18) | #938 |
   | `ansel` | 5,6 | ✅ **fehér szűrővel 0,53**; a SZÍNES szűrő igazolatlan | #939 |
   | `Vignette` | 4,6 | ✅ a zóna **ELLIPSZIS** — eredeti exportokkal igazolva (2026-08-18) | #859 |

   **Vagyis a rangsorból egyetlen valódi rendermunka maradt: a `finetune2`
   hőmérséklet bekötése (#879).** A többi vagy kész, vagy külső exportra
   vár.

   - **Korábban megválaszolva:** a `tint` (és a `rainbow`, `autocontrast`)
     **szinthúzással kezd** — a `0x009db610` helyben módosítja a képet, nem
     csak elemez (#872)
4. ~~**A `tint` virtuális színátalakítása**~~ — **GYAKORLATILAG LEZÁRVA** (#872): a `ctx` a **lánc-építő objektum**, a `[ctx+8]` egy függvénymutató-**mező** (nem vtable-slot), és a szokásos renderelési úton nem áll be. A recept teljes nélküle
5. ~~**A `ytResampler` utolsó, nem 2-hatvány lépése**~~ — **MEGVAN** (#871,
   #762): kilenc szűrőmag, a `ResampleFilter2` beállítás választ, alapérték
   **6 = Lanczos-4**; az `unsharp` a 2-est (köbös B-spline) használja.
   Maradék: ~~a **4-es mód** pontos alakja~~ **MEGVAN (#871): háromlebenyes
   köbös konvolúció, 11/209-es törtekkel, két matematikai ellenőrzéssel
   igazolva** · ~~a **10-es** mód~~ **MEGVAN (#871): MMX-es bilineáris,
   8 bites súlyokkal, `>> 8` osztással** → **a `ytResampler` mind a
   tizenegy módja feltárva**

### [picasa-create-features.md](picasa-create-features.md) — nincs nyitott kérdés

1. ~~**A Képkockamozaik kényszeres vágási szabálya**~~ — **TELJESEN MEGVAN**
   (#431/#916, 1.9.14, 2026-08-18): a kényszeres levél a téglalapot
   változatlanul átveszi és nem darabol tovább; a „nincs kényszer" jelölés
   mind a négy koordináta −1,0. A „melyik részfába irányítja" kérdés
   **tárgytalan**: nincs irányítás — a keresés körönként, képenként
   stempeli be a kényszert a csomópontba, és elutasításos mintavétellel
   találja meg a jó elrendezést. Ugyanitt megvan a pakoló **célfüggvénye**
   is (`0x00893570`, mindhárom rácsos témára közös): az **elpazarolt
   terület** minimalizálása
2. ~~**A Képkupac kezdeti (x, y) szórása**~~ — **elavult jelölés volt**: a
   szórás az 1.9.12-ben már 2026-08-14 óta megvan („legjobb jelölt"
   mintavételezés). A 2026-08-17-i átvilágítás vette le.

### [picasa-kollazs-felulet.md](picasa-kollazs-felulet.md) — 1 kérdés

*(A 2026-08-18-i két kör az eredeti hét kérdést **mind** lezárta — az
elszámolás a lap **12.** szakaszában. Ami lezárult: az `Alt`+vonszolás =
a képet a kupac **tetejére** hozza (klónozás nincs); a 11. esemény =
**két kép cseréje**; a `collage_adapt` = névvel küldött parancs; az
`addclips`/`deleteclips`; a négy hiányzó oldalarány; a gyűrűnek **nincs**
vonszolási küszöbe; a maszk megfejtett bitjei 5-ről 11-re nőttek. Az itt
maradt három kérdés mind a második körben NYÍLT, és egyik sem igényel
futó Picasát.)*

1. A képesség-maszk **6. bitje** mit kapcsol? A helye megvan: a
   kollázs-csomópont `+0x219` tulajdonságát állítja (`0x00860470`), amit a
   keretrendszer a `0x009e2aa5`-nél olvas. *(A többi öt bit 2026-08-18-án
   lezárult: 12. = a téma megvalósítja a 9. vtable-slotot, 13. = automata
   `collage_adapt`, 14. = a `collage::shadows` alapértéke, 15./16. =
   halott bitek.)*


### [vagas-eszkoz-allapot.md](vagas-eszkoz-allapot.md) — nincs nyitott kérdés

~~A **kollázs Oldalformátum** legördülőjének sorrendje~~ — **MEGVAN**
(#876): a felépítő `0x007cc990` két kapcsolója adja; a kollázs esete az,
amikor **mindkettő hamis**. Ugyanitt derült ki, hogy a nyomatméretek
**metrikus/angolszász** ágra oszlanak.

### [picasa-gomb-es-menu-rendszer.md](picasa-gomb-es-menu-rendszer.md) — 1 kérdés

1. ~~a **letiltott** gomb rajza~~ — **MEGVAN** (#893): a rajzoló az alfát
   **néggyel osztja** (`0x009e3178`), kivétel nélkül
2. ~~a `popuplist` **lenyíló panel** színei~~ — **MEGVAN** (#894):
   `listdecrect`, sík `#E8E8E8` kitöltés, `#BABABA` keret
3. **A kiemelt sor SZÍNE** — a `respack`-ben nincs hozzá réteg, kódból jön.
   *(2026-08-18: négy helyen kerestük, nincs ott — a negatív eredmény és a
   folytatás helye a lap 8. szakaszában. A legolcsóbb út egy
   színmérés a felhasználó képernyőképéről.)*
4. **A buboréksúgó rajza** — saját osztály (`ytToolTip`), de nincs hozzá
   képréteg; a háttér/keret/árnyék kódból jön (#901)

### [picasa-eger-es-kijeloles.md](picasa-eger-es-kijeloles.md) — nincs nyitott kérdés

*(Mind a négy lezárult; a maradék apró pontok — a `WM_*` leképezés és az
egyes menük tételsora — a lap saját szakaszaiban vannak jelölve.)*

1. ~~A **gumikeretes kijelölés** szabálya~~ — a `ytSelectionDragHandler` a
   **szerkesztő** téglalapjaié, nem a rácsé: **arányt kényszerít**
   (Shift 1,0 · Ctrl 4/3 · Alt 3/2, #891). ~~A RÁCS lasszójának szabálya~~ — **MEGVAN**
   (2026-08-18, 4/e): **metszés-teszt**, nem tartalmazás; a metszetnek
   szigorúan pozitív területűnek kell lennie.
2. ~~A **Shift-tartomány horgonya**~~ — **MEGVAN** (#892): a horgony a
   `[this+0x390]`, és Shifttel **egyesével bővít**, a horgony **továbblép**
   (nem Intéző-féle tartomány)
3. ~~A **26 belső eseménykód** jelentése~~ — **A GYAKORLATHOZ ELÉG MEGVAN**
   (2026-08-18, 4.2/b): a harmadik nekifutás megfordította az irányt, és
   nem az ablakeljárás felől, hanem a **84 `*Handler` viselkedéséből**
   olvasta ki. Nyolc kód jelentése megerősítve (1 = bal le, 2/3 = mozgás,
   4 = fel, 5 = jobb le, 0x0b = ejtés, 0x13 = találat-vizsgálat,
   0x1b = elrendezés, 0x1f/0x20 = be/ki), a visszatérési értékekkel együtt
   (`0xF4240` = kezeltem, `0xF4241` = add tovább). **Maradék:** a `WM_*` →
   belső leképezés — de a megvalósításhoz nem kell
4. ~~A **jobbklikk útja**~~ — **MEGVAN** (2026-08-18, 4/f): tizenhat helyi
   menü erőforrásneve a birtokló függvénnyel; a rácsnak album- és
   mappanézetben **külön** menüje van

### [picasa-ini-format.md](picasa-ini-format.md) — 1 kérdés

1. Mit tesz a Picasa, ha külső program **írja az inifájlt ÉS megérinti a kép `mtime`-ját** (537. sor) — ⚠️ **windowsos próbára vár**, gépi úton nem eldönthető

### Nincs nyitott kérdés

`filterdesc-registry.md` · `ui-audit-context-menus.md` · `ui-audit-mainwindow.md` · `picasa-native-filter-registry.md` · **`ui-audit-editor.md`** · és a lenti táblák
minden további lapja.

## Formátum-specifikációk (adatfájlok, erőforrások)

| lap | miről szól |
|---|---|
| [picasa-ini-format.md](picasa-ini-format.md) | A `.picasa.ini` — az igazságforrás, round-trip szabályokkal |
| [pmp-database.md](pmp-database.md) | A központi adatbázis (`db3` / PMP) |
| [picasa-imagedata-rekord.md](picasa-imagedata-rekord.md) | Az `imagedata` rekord — belső kép-nyilvántartás |
| [picasa-respack-format.md](picasa-respack-format.md) | `respack.yt` — a bináris erőforráscsomag (megfejtve) |
| [picasa-program-resources.md](picasa-program-resources.md) | Erőforrás- és formátum-leltár (gombok, web-export, plugin-ök) |
| [picasa-fen-dialogs.md](picasa-fen-dialogs.md) | A `.fen` dialógus-definíciók |
| [picasa-web-template-nyelv.md](picasa-web-template-nyelv.md) | A web-export sablonnyelve |
| [picasa-exe-strings.md](picasa-exe-strings.md) | Bináris string-bányászat |
| [picasa-beepitett-konyvtarak.md](picasa-beepitett-konyvtarak.md) | A Picasa beépített nyílt forráskódú könyvtárai |
| [picasa-linux-mod.md](picasa-linux-mod.md) | **A Picasa Linux-módja** — mit tiltott le maga a Google Wine alatt, és miért |

## Képfeldolgozás (szűrők, render)

| lap | miről szól |
|---|---|
| [filters-decoded.md](filters-decoded.md) | A szűrők visszafejtett modelljei + golden-verdiktek |
| [filterdesc-registry.md](filterdesc-registry.md) | A `filterdesc.xml` — csúszkanevek, tartományok, alapértékek |
| [picasa-native-filter-registry.md](picasa-native-filter-registry.md) | A natív szűrő-tábla: 49 név → kezelő + képen belüli vezérlők |
| [picasa-native-filter-workers.md](picasa-native-filter-workers.md) | A natív szűrők munkafüggvényei — hívási térkép |
| [histogram-reference.md](histogram-reference.md) | Hisztogram-referencia és összevetés |

## Felület — KÖTELEZŐ méretspecifikációk

Ezek **normatívak**: a felületnek pontosan ezeket kell követnie.

| lap | miről szól |
|---|---|
| [szerkeszto-panel-meretek.md](szerkeszto-panel-meretek.md) | A szerkesztő bal panelje (201 elem) — **az 1. fül gombsorrendjének EGYETLEN érvényes forrása** |
| [konyvtar-ablak-meretek.md](konyvtar-ablak-meretek.md) | A könyvtár-ablak (156 elem) |
| [jobb-fiok-meretek.md](jobb-fiok-meretek.md) | A jobb oldali fiók („Metaadatok", 80 elem) |
| [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) | A fő ablak elrendezése — a forrásból |

## Felület — auditok és lefedettség

| lap | miről szól |
|---|---|
| [ui-audit-editor.md](ui-audit-editor.md) | A szerkesztőpanel: fülek, effekt-csempék, dialógusok |
| [ui-audit-mainwindow.md](ui-audit-mainwindow.md) | Főablak: mappafa, eszköztár, tálca, görgetősáv |
| [ui-audit-menus.md](ui-audit-menus.md) | A teljes menürendszer |
| [ui-audit-context-menus.md](ui-audit-context-menus.md) | Jobbklikkes helyi menük |
| [ui-lefedettseg.md](ui-lefedettseg.md) | Az eredeti panelek ↔ a mi QML-fánk megfeleltetése |
| [picasa-beviteli-mezok.md](picasa-beviteli-mezok.md) | Beviteli mezők és párbeszédpanelek |

## Viselkedés és funkciók

| lap | miről szól |
|---|---|
| [picasa-create-features.md](picasa-create-features.md) | A „Létrehozás" menü funkciói |
| [picasa-kollazs-felulet.md](picasa-kollazs-felulet.md) | A Kollázs teljes működése — parancstábla, gyűrű, helyi menük, kimenet |
| [picasa-bezaras-es-kilepes.md](picasa-bezaras-es-kilepes.md) | Mit zár be az „X" — bezárás és kilépés |
| [picasa-nyomtatas.md](picasa-nyomtatas.md) | A nyomtatás — panel (61 elem), 17 méret, beállítások |
| [picasa-email-kuldes.md](picasa-email-kuldes.md) | E-mail-küldés — választó, beépített Gmail-szerkesztő, beállítások |
| [picasa-importalas.md](picasa-importalas.md) | Az importálás panelje — tipp-sor, kártyatörlés-figyelmeztetés, hibák |
| [vorosszem-eszkoz-terve.md](vorosszem-eszkoz-terve.md) | A vörösszem-eszköz terve |
| [vagas-eszkoz-allapot.md](vagas-eszkoz-allapot.md) | A vágás-eszköz állapota — 19 arány, egyéni arányok, 3 javaslat |

## Nyelv és megjelenés

| lap | miről szól |
|---|---|
| [picasa-hu-terminology.md](picasa-hu-terminology.md) | Hivatalos Picasa-magyar terminológia |
| [picasa-effekt-nevek.md](picasa-effekt-nevek.md) | Az effektek nevei és buboréksúgói |
| [picasa-effekt-feliratok.md](picasa-effekt-feliratok.md) | Az effekt-vezérlők feliratai |
| [picasa-gomb-es-menu-rendszer.md](picasa-gomb-es-menu-rendszer.md) | **A gomb- és menürendszer** — 9-szeletes gombok, állapotszínek, tipográfia, a kétféle menü |
| [picasa-eger-es-kijeloles.md](picasa-eger-es-kijeloles.md) | **Egér, kijelölés, kattintás-viselkedés** — a `.tre` interakciós szótár, a Ctrl/Shift-modell |
| [design-guide.md](design-guide.md) | Dizájn-kézikönyv — hűség-referencia |
| [ux-principles.md](ux-principles.md) | UX-alapelvek — „a Picasa lelke" |

## Módszertan és tervezés

| lap | miről szól |
|---|---|
| [binaris-regeszet-modszertan.md](binaris-regeszet-modszertan.md) | **A szerszámosláda**: mit hoz ki egy eszköz, és mit NEM lát |
| [feature-map.md](feature-map.md) | Funkciótérkép és fázisterv |

## Mikor kell ezt a lapot frissíteni

| mikor | mit |
|---|---|
| **Új spec-lap születik** | egy sor a témakör táblájába — **ugyanabban a PR-ban** |
| **Egy kör nyitott kérdést ZÁR LE** | a kérdés kikerül a „Nyitott kérdések" listáról; ha a lapon nem marad több, a lap fejléce is |
| **Egy kör ÚJ nyitott kérdést talál** | egy sor a lap listájába, **egy mondatban megfogalmazva** — ne csak „Nyitva" szót írj a spec-lapra |
| **Egy lap átnevezése/összevonása** | a hivatkozás javítása |
| **Kutatói kör INDULÁSAKOR** | csak olvasod — innen választasz témát |

**A frissítés nem külön kör.** Aki hozzányúl egy spec-laphoz, ugyanabban a
PR-ban hozza rendbe ezt a listát is — így az index nem tud elavulni.

⚠️ **Ne gépi szó-számlálással tartsd karban.** A `Nyitva`/`dekódolatlan`
szavak nagy része **hivatkozás** egy máshol megválaszolt pontra; a
számlálás háromszorosára fújja a képet. A lista **kézzel írt kérdésekből**
áll, mert egy kutatói kör kérdést választ, nem szót.

A gyanús helyek gyors előkeresésére (ellenőrzésre, nem karbantartásra):

```bash
grep -n 'Nyitva\|NYITOTT\|dekódolatlan\|uncalibrated' docs/specs/*.md \
  | grep -v '~~' | grep -v 'LEZÁRVA\|MEGVÁLASZOLVA\|MEGOLDVA\|MEGDŐLT'
```
