# Forrás nélküli jegyek összevetése, 3. köteg (#5454)

Ez a lap a #5186 gyűjtő harmadik kötegének húsz lezárt jegyét veti össze az eredeti Picasa 3.9 viselkedésével. Vizsgálat dátuma: 2026-10-21. A kódállapot a `research/5454-haiku` ág kiindulási commitja (`3a81902a7`).

## Módszer és korlátok

- **Eredeti oldal:** a bináris sztring- és xref-index (`referencia/binary-index/picasa3-index.sqlite`, a privát `picasapy-agent` repóban), a magyar felirat-tábla (`referencia/stringres-en-hu.tsv`), a `.tre` erőforrások és a `docs/specs/` szakaszai. A jegy saját szövege nem forrás.
- **Mai oldal:** a `src/picasapy/` kódjának olvasása és `rg`-vel való ellenőrzése.
- **Nem történt meg ebben a körben:** kattintásos teszt, renderelés és Colab-felvétel. Ahol a jegy ilyen bizonyítékot kér, a tétel `NEM DÖNTHETŐ EL`, és a teendőben ki van írva a mérés.
- **Elavult állítások:** a jegyek „Nálunk ma” szakasza nagy részben már nem igaz. Húsz jegyből tizenhét „Nálunk ma” állítását a mai kód cáfolja vagy már megoldja. Ezeket a tételeknél megneveztem.
- **Kód:** nem változott. A kötelező CI-őrök ezért nem futottak.

Ítéletek jelentése: **EGYEZIK** = az eredeti forrás és a mai kód megegyezik a jegy elvárásával. **ELTÉR** = bizonyított különbség. **NEM DÖNTHETŐ EL** = a bizonyíték hiányzik, vagy élő mérés kell.

## Összesítő táblázat

| jegy | ítélet | forrás | teendő |
|---|---|---|---|
| #4558 Shift-csempék bélyegképe | EGYEZIK | `ui-audit-editor.md` 1375-1391; bináris `_mod%s` (`0x00c962e4`) | nincs |
| #4560 Háttérszín felirat | EGYEZIK | `picasa-effekt-feliratok.md` 75; `stringres-en-hu.tsv` 1823 | nincs |
| #4561 csempe-előnézet a frissített láncról | NEM DÖNTHETŐ EL | `ui-audit-editor.md` 2900; kód: `editorpanel_logika.js` 76-84 | élő próba: két egymás utáni effekt után a csempék bélyegképe |
| #4562 filmszalag hét férőhellyel | EGYEZIK | `szerkeszto-felso-sav.md` 5.1-5.3 | nincs |
| #4570 AutoPlayMovies kapcsoló | EGYEZIK | bináris `0x00c91f74`; `ui-audit-editor.md` #5466 szakasz | nincs: az eredeti kulcs is rejtett, alapértéke 1 |
| #4571 Névtelenek csempéi arcot mutatnak | EGYEZIK | `picasa-arcfelismeres.md` (Névtelenek nézet) | nincs |
| #4572 névtelen arc kattintásra keret | EGYEZIK | `picasa-arcfelismeres.md` 943-944; bináris `0x00ca0f44` | nincs |
| #4574 `Add a person manually` gomb | NEM DÖNTHETŐ EL | `picasa-arcfelismeres.md` 943 | Colab-felvétel: az Emberek panel kijelölés nélkül, névtelen és mellőzött arc kijelölésével, látszik-e a gomb |
| #4579 Tulajdonságok panel öt sora | EGYEZIK | `picasa-metaadat-tulajdonsagok.md` 2355, 2380 | nincs |
| #4584 Helyek térkép betöltésjelzés | EGYEZIK | `geopaneltext.tre`; `jobb-fiok-meretek.md` 158-160; `stringres-en-hu.tsv` 2982 | nincs |
| #4590 csatolt kártya és kamera | ELTÉR | bináris `0x00c87504`; `stringres-en-hu.tsv` 142; `picasa-importalas.md` (Forrásfajták) | Az importálás a csatolt fényképezőgépet is forrásként felkínálja |
| #4594 régi `Picasa.ini` fájl | NEM DÖNTHETŐ EL | bináris `0x00c8644c` (a név); az olvasási út NINCS MEG | Colab-felvétel: egy mappában csak `Picasa.ini` van, megjelennek-e a csillagok és feliratok |
| #4595 üres mappacím az importálásnál | EGYEZIK | `picasa-importalas.md` 54 | nincs |
| #4602 nyomtatás szerkesztett képpel | NEM DÖNTHETŐ EL | NINCS MEG | Colab-felvétel: rács, szerkesztett és elforgatott kép nyomtatása PDF-nyomtatóra |
| #4611 sablonok és videó-feltételek | EGYEZIK | `picasa-web-template-nyelv.md` 6. szakasz | nincs |
| #4616 film `Show Captions` kapcsoló | NEM DÖNTHETŐ EL | `picasa-create-features.md` 751; a film szövegének forrása NINCS MEG | Colab-felvétel: film képfelirattal és EXIF-leírással, melyik szöveg jelenik meg |
| #4846 fülikonok tükrözése | NEM DÖNTHETŐ EL | a jegy által hivatkozott referencia-képernyőkép | renderelt fülsáv a referencia mellett, öt ikonra, mért eltéréssel |
| #4881 szabványos gombok nyelve | EGYEZIK | `application.py` 1014-1044; `picasa-fen-dialogs.md` | nincs (a teszt ebben a körben nem futott) |
| #5007 húzás mappára | NEM DÖNTHETŐ EL | NINCS MEG (mozgatás vagy másolás) | Colab-felvétel: a húzott kép eltűnik-e az eredeti mappából |
| #5121 új album húzással | NEM DÖNTHETŐ EL | bináris `0x00cb283c`, hivatkozó függvény `0x00765d30` | Ghidra-kör: `0x00765d30` hívói és az albumpanel húzáskezelője |

## Tételenként

### #4558 Shift-re a csempék bélyegképe is a másodlagos effektet mutatja

- **Eredeti:** a `_mod%s` utótag a bináris `0x00c962e4` címen van, a `0x005d7c20` függvény hivatkozza. A kilenc kétmódú csempe párosítását a `docs/specs/ui-audit-editor.md` 1375-1391. sora adja: a csempe felirata és bélyegképe is a másodlagos effektre vált.
- **Nálunk:** mind a kilenc csempén van másodlagos bélyegkép. `EditorEffectsTab1.qml` 70-71, 113-114, 132-133, 163-164, 196-197; `EditorEffectsTab2.qml` 129-131 (`heatmap` / `nightvision`); `EditorEffectsTab3.qml` 90-92, 111-113, 160-161. A másodlagos kulcsok a `_EFFECT_NAMES` listában vannak (`edit_controller.py`, 160. sortól).
- **Ítélet:** EGYEZIK. A jegy „Nálunk ma” szakasza elavult: a másodlagos bélyegkép már be van kötve, és a kulcsok a katalógusban vannak.
- **Teendő:** nincs. A renderelt kép és a kattintásos teszt ebben a körben nem futott.

### #4560 A Sixties, Polaroid és Lekerekített szél színmintájának felirata Háttérszín

- **Eredeti:** a három effekt színmintájának felirata `Background Color`, magyarul `Háttérszín`. A `docs/specs/picasa-effekt-feliratok.md` 75. sora a bináris `0x008feed8` címet adja. A magyar respack-tábla is így írja: `stringres-en-hu.tsv` 1823. sor (`ImageFilters::BackgroundColor`).
- **Nálunk:** a három effekt `Background Color` feliratú színparamétert kap (`src/picasapy/app/effect_params.py` 319, 403, 408). A panel `EditorParamPanel.qml` 82. sorában fordítja, a `picasapy_hu.ts` fájl szerkesztőpanel-kontextusában a fordítás `Háttérszín`.
- **Ítélet:** EGYEZIK. A jegy „Nálunk ma” szakasza (`Külső szín`) a javítás előtti állapotot írja le. A javítás a `0218fbbd0` commit (#4781), és benne van a `HEAD`-ben.
- **Teendő:** nincs.

### #4561 Effekt alkalmazása után a csempék előnézete a frissített láncot mutatja

- **Eredeti:** a `docs/specs/ui-audit-editor.md` 2900. sora szerint a csempe-előnézet a saját effektjét a szerkesztési lánc aktuális tetejére alkalmazza (#2061).
- **Nálunk:** a csempe URL-je tartalmazza az aktuális láncot (`src/picasapy/app/qml/PicasaPy/editorpanel_logika.js` 76-84, `?filters=` paraméter). Az `effectChain` property `revisionChanged` jelzésre frissül (`src/picasapy/app/edit_controller.py` 738. sor; a jelzés kiadása a 3296. sorban). Ezért alkalmazás után az URL megváltozik, és a QML új képet kér. A jegy gyanúja (az URL nem változik) statikusan nem igazolódik.
- **Ítélet:** NEM DÖNTHETŐ EL. A kódolvasás szerint a gyanú valószínűleg téves, de a jegy élő próbát kér, és ilyen próba nem futott.
- **Teendő:** élő próba: két egymás utáni effekt alkalmazása után a csempék bélyegképe a második effektet is mutatja-e.

### #4562 A filmszalag hét férőhelyes, az aktuális kép középen van, kétszínű kerettel

- **Eredeti:** a `docs/specs/szerkeszto-felso-sav.md` 5. szakasza (5.1-5.3): hét fix férőhely, 31 px osztásköz, az aktuális kép a középső férőhelyen, a keret `#009EFF` és `#D4D4D4`. A szakasz a `CFilmstrip` eseménykezelőjét a bináris alapján írja le (bizalmi fok: megerősített).
- **Nálunk:** `src/picasapy/app/qml/PicasaPy/PhotoViewer.qml` 1925-1927. sorában `preferredHighlightBegin: (width - 28) / 2`, `preferredHighlightEnd` +31 és `highlightRangeMode: ListView.StrictlyEnforceRange`. A keret színei az 1992. és 1999. sorban vannak. A jegy „Nálunk ma” szakasza (`42 × 38`-as delegate, `Math.min(7, ...) * 44`) elavult.
- **Ítélet:** EGYEZIK a középre igazítás, az osztásköz és a keretszínek tekintetében.
- **Teendő:** nincs. A 28 × 28-as bélyegméret és a ±3 px-es renderelt összevetés ebben a körben nem futott. A #4317 lap szerint a méretek az 1955-1957. sorban vannak.

### #4570 Az AutoPlayMovies beállítás szabályozza, hogy a videó megnyitáskor magától elindul-e

- **Eredeti:** a `0x00593880` és `0x00594820` két külön kódútból olvassa a `Preferences\AutoPlayMovies` kulcsot. Mindkettő 1-es alapértéket ad át (`0x00593ff0`, `0x00594c54`); a kulcs a `0x00c91f74` címen van. A teljes `.text` közvetlen hivatkozás-keresése csak e két használatot találta. A `runtime/*.fen`, a menü és a stringres ellenőrzése nem talált hozzá felhasználói vezérlőt vagy feliratot. Részletes bizonyíték: `ui-audit-editor.md`, „Az `AutoPlayMovies` rejtett Preferences-kulcs” szakasz.
- **Nálunk:** a beállítás be van kötve. `src/picasapy/app/appearance_controller.py` 26-28 (kulcs `view/autoPlayMovies`, a kódkomment szerint alapérték igaz), 97-98 (olvasás), 176-190 (property és `setAutoPlayMovies`). A `VideoPlayerView.qml` 21-24. sora és 106. sora a megnyitáskor elindítja a lejátszást. Felhasználói felület nincs: a `setAutoPlayMovies`-nek nincs QML-hívója, így a beállítás csak a beállítások fájlján keresztül érhető el.
- **Ítélet:** EGYEZIK a kapcsoló láthatósága szempontjából: az eredetiben sincs felhasználói vezérlő. A „Nálunk ma” leírása a beállítás bekötéséről továbbra is érvényes.
- **Teendő:** nincs. Az eredetihez sem tartozik felirat vagy beállításlap, ezért fejlesztői jegy nem indokolt.

### #4571 A Névtelenek album csempéi az arcot mutatják, nem a fotó közepét

- **Eredeti:** a `docs/specs/picasa-arcfelismeres.md` Névtelenek nézetről szóló szakasza (a #4317 lap szerint a 2346. sor körül) a csoportosított nézetben az arc kivágását írja le.
- **Nálunk:** a csempe URL-je arc kivágásával készül: `src/picasapy/app/people_controller.py` 133, 697, 905, 927. sor (`_thumb_url(photo, arc=...)`). A QML a `thumbUrl`-t használja (`src/picasapy/app/qml/PicasaPy/UnnamedFacesView.qml` 483, 655-673). A forgatás: `src/picasapy/app/arc_nagyitas_url.py` 22. sora szerint a kivágás a megjelenített, forgatott képre vonatkozik.
- **Ítélet:** EGYEZIK. A jegy „Nálunk ma” szakasza (a teljes fotó bélyegképe) elavult.
- **Teendő:** nincs. A forgatott fotón végzett kattintásos teszt ebben a körben nem futott.

### #4572 A nézőben a felismert, még névtelen arcra kattintva keret és `Type a name` mező jelenik meg

- **Eredeti:** a `docs/specs/picasa-arcfelismeres.md` 943-944. sora szerint a mellőzött arcon nincs keret és nincs `Type a name` mező. A nem mellőzött névtelen arcra kattintva keret és `Type a name` jelenik meg. Az alapállapotban nincs keret, így az alapértelmezett láthatóság is igazolt. A `Type a name` sztring a bináris `0x00ca0f44` címen van, három függvény hivatkozza.
- **Nálunk:** a névtelen, indexből jövő arcokat a nézet is kéri: `src/picasapy/app/faces_helper.py` 4-6. sor (az indexből kérés), 111-112. sor. A keret kattintásra jelenik meg (`src/picasapy/app/qml/PicasaPy/FacesOverlay.qml` 20-21. sor). A `Type a name` mező a `FacesOverlay.qml` 414. sorában van.
- **Ítélet:** EGYEZIK. A jegy „Nálunk ma” szakasza (csak az ini-arcokat olvassa) elavult.
- **Teendő:** nincs. A kattintásos teszt és a renderelt összevetés ebben a körben nem futott.

### #4574 Az Emberek panelben megjelenik az `Add a person manually` gomb és útmutatója

- **Eredeti:** a `docs/specs/picasa-arcfelismeres.md` 943. sora szerint a mellőzött arc kijelölésekor a panelben megjelenik az `Add a person manually` gomb. A nem mellőzött névtelen arc sora a gombot nem említi; ebből a hiánya nem következik. A `peoplepanel.tre` 24-32. sora (a #4317 lap szerint) a gombot kezdetben rejtettnek írja le.
- **Nálunk:** a gomb a `src/picasapy/app/qml/PicasaPy/PeoplePanel.qml` 390-399. sorában van: `visible: !panel.manualAddActive`, `enabled: panel.selectionCount > 0`. Kijelölés nélkül is látszik, de tiltva. Az útmutató szövege (414-431. sor) a #4317 lap szerint megegyezik a respack-szöveggel.
- **Ítélet:** NEM DÖNTHETŐ EL. A gomb megvan; az, hogy az eredetiben kijelölés nélkül vagy névtelen arcnál is látszik-e, a felvételekből nem derül ki. A jegy „Nálunk ma” szakasza (nincs gomb a panelben) elavult.
- **Teendő:** Colab-felvétel az Emberek panelről kijelölés nélkül, névtelen arc és mellőzött arc kijelölésével: mikor látszik az `Add a person manually` gomb.

### #4579 A Tulajdonságok panel mutatja a Fájl dátuma, CCD szélessége, Rekesz, JPEG minőség és Személycímkék sort

- **Eredeti:** a `docs/specs/picasa-metaadat-tulajdonsagok.md` 17. szakasza a `properties.xml` sorait és kulcsait adja (9. FileDate, 15. CCDWidth, 17. ApertureValue, 28. Quality, 30. Regions). A kulcs-hozzárendelés a bináris `0x00633210` függvényből van (2355. sor).
- **Nálunk:** `src/picasapy/app/formatting.py` 519 (`File Date`), 535 (`CCD Width`), 543 (`Aperture`), 571 (`JPEG Quality`), 579 (`People Tags`). A magyar feliratok a `picasapy_hu.ts` fájlban vannak (a #4317 lap szerint).
- **Ítélet:** EGYEZIK. A jegy „Nálunk ma” szakasza (hiányzó sorok) elavult.
- **Teendő:** nincs. A reprezentatív értékek tesztjét ebben a körben nem ellenőriztem.

### #4584 A Helyek térkép betöltés közben `Loading` jelzést, hálózat nélkül érthető üzenetet mutat

- **Eredeti:** a `geopaneltext.tre` a betöltésfelirat szövegét adja: `Loading Map...` (`geopanel/loading_title`). A méreteket a `docs/specs/jobb-fiok-meretek.md` 158-160. sora adja (`loading_icon` 64 × 52). A hibaüzenet a `stringres-en-hu.tsv` 2982. sorában van (`geo::init_err`), szövege: `Picasa failed to initialize Google Maps. Please make sure that you are connected to the Internet.`
- **Nálunk:** `src/picasapy/app/qml/PicasaPy/PlacesPanel.qml` 145-170: a betöltő blokk `Loading Map...` felirattal és `loading_icon.png` ikonnal. A hálózati hiba szövege a `PlacesPanel.qml` `offline` ágán van, ugyanazzal a szöveggel.
- **Ítélet:** EGYEZIK. A jegy „Nálunk ma” szakasza (nincs betöltésjelzés és üzenet) már nem igaz.
- **Teendő:** nincs. Az ikon mérete (64 × 52 az eredetinél) nincs ellenőrizve. Ez vizuális kérdés, nem működési.

### #4590 Az importálás felismeri a csatolt memóriakártyát és a kamerát, és forrásként felkínálja

- **Eredeti:** a bináris `Removable Drive(%s)` sztring a `0x00c87504` címen van, a kulcs `CAcquireUI::Removeable` (`0x00c87518`). A magyar felirat `Cserélhető meghajtó (%s)` (`stringres-en-hu.tsv` 142. sor). A `docs/specs/picasa-importalas.md` „Forrásfajták” szakasza a kamerát (`WiaDev`, „Wia-”) is forrásként sorolja fel.
- **Nálunk:** a csatolt kártya megvan. `src/picasapy/app/import_source_controller.py` 150 (`/media`, `/run/media`), 179 (a csatolási listából csak ezek). A QML feliratát a `src/picasapy/app/qml/PicasaPy/ImportSourceDialog.qml` 77. sora adja. A PTP/MTP kamera szándékosan kimarad (`import_source_controller.py` 261. sor).
- **Ítélet:** ELTÉR a kamera miatt. A kártya rész EGYEZIK. A kamera nálunk tudatos kihagyás, az eredetiben van. A jegy „Nálunk ma” szakasza (csak a `Browse` gomb van) elavult: a csatolt kártya felkínálódik.
- **Teendő:** Az importálás a csatolt fényképezőgépet is forrásként felkínálja. A PTP/MTP kérdést a jegyen kell kimondani, mert termékdöntés.

### #4594 A régi `Picasa.ini` nevű fájlból is beolvassa a program a csillagokat és feliratokat

- **Eredeti:** a név megvan: a bináris `Picasa.ini` sztring a `0x00c8644c` címen van, több függvényből hivatkozott (az indexben 10 sor). A korai verzió nevét a `picasa-ini-format.md` említi (a #4317 lap szerint). Az olvasási út NINCS MEG: a név létezését nem követi igazolt olvasás.
- **Nálunk:** a régi fájl csak olvasási forrás. `src/picasapy/ini/names.py` 8. sor (`LEGACY_INI_NAME`), `src/picasapy/ini/io.py` 146-148. sor. A jegy állítása („ez az ág nincs”) elavult.
- **Ítélet:** NEM DÖNTHETŐ EL. A mi oldalunk megvan, az eredeti olvasási útja nincs igazolva.
- **Teendő:** Colab-felvétel kell: egy mappában csak `Picasa.ini` van. Kimondani, megjelennek-e a csillagok és feliratok. A teszt mindkét fájlnévre a jegy része.

### #4595 Az importálás nem indul cím nélküli kézi mappanévvel

- **Eredeti:** a tipp-sor 1. állapota: `Enter new folder title or choose existing folder to continue` (`docs/specs/picasa-importalas.md` 54. sor). A folytatáshoz cím vagy meglévő mappa kell.
- **Nálunk:** a tipp-sor a `src/picasapy/app/qml/PicasaPy/ImportSourceDialog.qml` 834. sorában van, ugyanazzal a szöveggel. A kontroller a cím nélküli kézi módot nem indítja (`import_source_controller.py` 859-860, a #4317 lap szerint; ezt most nem ellenőriztem újra).
- **Ítélet:** EGYEZIK. A jegy „Nálunk ma” szakasza (a célgyökérbe másol) elavult.
- **Teendő:** nincs. Megjegyzés: az Import gomb engedélyezett marad, kattintásra csendben nem történik semmi (a #4317 lap szerint). Ha ez zavaró, külön jegy kell hozzá.

### #4602 A Nyomtatás a rácson látott, szerkesztett és helyesen elforgatott képet nyomtatja

- **Eredeti:** NINCS MEG. A `docs/specs/picasa-nyomtatas.md` nem írja le, hogy a nyomtatás szerkesztett képet használ-e. A jegy hivatkozása (export, e-mail, webexport) más funkcióra vonatkozik.
- **Nálunk:** a fő nyomtatási út a `_render_photo` függvényt használja (`src/picasapy/app/print_controller.py` 769. sor; hívások: 1033, 1191, 1501). Ez a `render_photo_pixels`-t hívja (788. sor), vagyis az export renderelőjét. A nyers `QImage(str(path))` a 892. sorban az útlevélfotó útvonalához tartozik, nem a rácsnyomtatáshoz. A jegy „nyers QImage” állítása a fő útra elavult.
- **Ítélet:** NEM DÖNTHETŐ EL. A mi oldalunk szerkesztett képet renderel, de az eredeti viselkedés nincs igazolva.
- **Teendő:** Colab-felvétel kell: mit kattintson (rács, szerkesztett és elforgatott kép, PDF-nyomtató), mit rögzítsen (a nyomtatott kimenet). A jegy EXIF-6 mintáját is be kell venni.

### #4611 A weboldal-export a felhasználó saját `.tpl` sablonjait is felajánlja

- **Eredeti:** a `docs/specs/picasa-web-template-nyelv.md` 6. szakasza három feltételt ír le a videóhoz: `isImage`, `isSimpleEmbed`, `isExtendedEmbed`. A sablonok a `web/templates/<név>/` mappákban vannak (a #4317 lap szerint).
- **Nálunk:** a felhasználói sablonmappa a `src/picasapy/webexport/catalog.py` 30. sorában van, a listázás a gyári sablonok után a sajátokat is adja (44-51. sor). A három videó-feltétel definiált: `src/picasapy/webexport/context.py` 140-142. sor. Az `isExtendedEmbed` mindig hamis, az eredeti kiválasztási szabályt a specifikáció nem írja le.
- **Ítélet:** EGYEZIK a jegy elfogadási feltételeivel (listázás, definiált videó-feltételek). A jegy „Nálunk ma” szakasza elavult.
- **Teendő:** nincs. A saját sablonnal készült teszt ebben a körben nem futott.

### #4616 A film Show Captions kapcsolója a Picasa-feliratot mutatja, nem csak a fájlba ágyazott leírást

- **Eredeti:** a kapcsoló megvan: `docs/specs/picasa-create-features.md` 751. sora (`caption_checkbox_label`, „Képfeliratok megjelenítése”). A film szövegének forrása NINCS MEG: a `.picasa.ini` `caption=` és az EXIF-leírás közül melyik kerül a filmre, nincs mérve.
- **Nálunk:** a `src/picasapy/movie/slideshow.py` 549-558. sorában a `_picasa_caption` a `.picasa.ini` `caption` kulcsot olvassa (607. és 701. sor hívja). Ennek hiányában a 647. sor az EXIF 270-es mezőt használja. A jegy „slideshow.py 389-426, csak EXIF” állítása elavult.
- **Ítélet:** NEM DÖNTHETŐ EL. A mi kódunk már a feliratot használja, az eredeti viselkedés nincs igazolva.
- **Teendő:** Colab-felvétel kell: egy kép, amelynek van `.picasa.ini` felirata és EXIF-leírása, film Show Captions bekapcsolva. Kimondani, melyik szöveg jelenik meg.

### #4846 A szerkesztő fülikonjainak rajza tükrözött és egyszerűsített az eredetihez képest

- **Eredeti:** a jegy által hivatkozott referencia-képernyőkép (`research/testdata/screenshot/`, 2026-07-17-i felvétel). Ebben a körben nem lett összevetve.
- **Nálunk:** `src/picasapy/app/qml/PicasaPy/EditTabIcon.qml` (a #338 rajza). A csavarkulcs feje és az ecset sörtéje a jegy által kért oldalon van (kódolvasás szerint, a #4317 lap szerint). A napkorong formáját és a 4-5. fül tájképét nem néztem meg.
- **Ítélet:** NEM DÖNTHETŐ EL. A tükrözés iránya a kódolvasás szerint megfelel a kérésnek, a forma és a renderelt kép összevetése nincs elvégezve.
- **Teendő:** renderelt fülsáv a referencia mellett, öt ikonra, mért eltéréssel. A jegy tesztfájlja (`tests/app/qml_functional/test_fulikon_rajz_4846.py`) ebben a körben nem futott.

### #4881 A párbeszédek szabványos gombjai a rendszer nyelvén jelennek meg a választott felületi nyelv helyett

- **Eredeti:** a Picasa saját párbeszédei a saját gombfeliratukat használják (`docs/specs/picasa-fen-dialogs.md`, a #4317 lap szerint 106-107. és 37. sor: OK, Cancel, Igen, Nem, Mégse).
- **Nálunk:** a Qt saját fordítása a választott nyelvhez töltődik be (`src/picasapy/app/application.py` 1014-1029, `_install_qt_translator`), a területet a `QLocale.setDefault` a választott nyelvvel állítja (1044. sor). A jegy tesztfájlja megvan: `tests/app/test_dialog_gombok_nyelve_4881.py`.
- **Ítélet:** EGYEZIK a kód és a jegy elvárása alapján. A jegy „Nálunk ma” szakasza (a rendszernyelv határozza meg a gombokat) elavult: a kód a választott nyelvet követi. A tesztet ebben a körben nem futtattam, az ítélet a kódolvasáson alapul.
- **Teendő:** nincs. A teszt futtatása a kör lezárása előtt még hátravan.

### #5007 A mappára húzott indexképek nem kerülnek át a mappába, és a Másolás/Beillesztés sem visz át képet

- **Eredeti:** a húzás szemantikája (mozgatás vagy másolás) NINCS MEG. A `docs/specs/picasa-eger-es-kijeloles.md` 582. sora a külső húzás engedett műveleteit adja (COPY, MOVE, LINK), nem a mappára húzást.
- **Nálunk:** a húzás megvan. `src/picasapy/app/qml/PicasaPy/FolderPane.qml` 922 és 1062 (`folderDropArea`), 1218 (`photosDroppedOnFolder`). A `src/picasapy/app/qml/Main.qml` 3465. sora fogadja, a 3477. sor hívja a `movePhotos`-t a `rename` szabállyal, ami áthelyezés. A másolás és a beillesztés: `src/picasapy/app/fileops_controller.py` 203 (`copyPhotos`), 590 (`copyFilesToClipboard`), 622 (`pasteFilesFromClipboard`). A jegy tesztfájlja (`tests/app/qml_functional/test_folder_file_transfer_5007.py`) ebben a körben nem futott.
- **Ítélet:** NEM DÖNTHETŐ EL. A „nincs ejtési terület” állítás elavult, a funkció megvan. A jegy szerinti áthelyezés az eredetiben nincs igazolva.
- **Teendő:** Colab-felvétel kell: egy képet a bal sáv mappájára húzni, és megnézni, az eredeti mappában megmarad-e a kép (másolás) vagy eltűnik (áthelyezés).

### #5121 Az első album után ráhúzással már nem lehet új albumot készíteni

- **Eredeti:** a `You can drag and drop pictures here to make a new album.` sztring a bináris `0x00cb283c` címen van, egyetlen függvény (`0x00765d30`) hivatkozza. Ennek elejét disszasszemblálva csak egy statikus CString-inicializálás és egy táblázat-keresés látszik. A húzás-kezelő logikája ebből nem azonosítható. A bináris index statikus hívásokat lát, a táblán keresztül érkező hívásokat nem. A `docs/specs/paritas-ellenorzes.md` #5121 sora Colab-feladatokra hivatkozik, ezt ebben a körben nem ellenőriztem.
- **Nálunk:** `src/picasapy/app/qml/PicasaPy/AlbumsSection.qml` 67. sor (`section.albumsModel.length === 0`), 94-95. sor (`albumDropArea`). A terület csak üres albumlistánál látszik.
- **Ítélet:** NEM DÖNTHETŐ EL. A bináris ebben a körben nem bizonyítja az eredeti viselkedést.
- **Teendő:** Ghidra-kör kell: `0x00765d30` hívói és az albumpanel húzáskezelője, ahol a drop-cél feltétele eldől. Kimondani, hol fogad az eredeti képet új album készítéséhez meglévő albumok mellett.

## Ellenőrizetlen állítások

- Nem futott le egyetlen teszt sem ebben a körben (sem a jegyek tesztfájljai, sem a kötelező CI-őrök).
- A `docs/specs/paritas-ellenorzes.md` (#4317 lap) sorait részben átvettem, ahol jelöltem. Ezeket nem ellenőriztem újra a forrásig.
- Colab-eredményeket nem olvastam.
