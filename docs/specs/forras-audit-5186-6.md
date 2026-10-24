# #5186 negyedik kutatói szála - öt tétel (2026-10-24)

A teljes jegyszöveg a munkakérésből származik. Az eredeti referencia a Picasa
3.9.141.259. A mai állapotot a munkafa QML/Python forrásából ellenőriztem;
alkalmazás- vagy tesztfuttatás nem történt. Az eredeti Colab-képek közül az
EN 38 arc-felvételt, a vágópanelt és az ikonsort mutató képet közvetlenül
megnéztem. A #5121 korábbi Colab-eredményei a specben vannak feljegyezve, de
a nyers job-képek nem találhatók a helyi mérőadat-archívumban.

## Következtetés

A #4551 három megnevezett, rögzített vágásgombja nincs a mai kódban; a három
eredeti előnézet viszont megmaradt, és mellettük PicasaPy-saját címet és
stratégia-feliratot mutat. A #4572 és #4579 állítása a forrásfeltételek mellett
igazolt. A #4846 teljes képi állítása render-összevetésre vár; a #5121 meglévő
album melletti viselkedése a már dokumentált Colab-mérések szerint egyezik.

## Bizonyítottsági fok

**Feltételes.** A #4551, #4572 és #4579 állításához külön eredeti forrás és mai
forráskód egyezik. A #4846-nál nincs mai renderkép; a #5121 nyers Colab-képei
nem érhetők el helyben, az eredeti bináris listaépítési feltétele pedig nyitott.
Az alkalmazást és teszteket nem futtattam.

## Bizonyíték

| Érték/állítás | Forrás |
|---|---|
| #4551: az eredeti három `cropsug` előnézeténél nincs felirat vagy súgó; a képen sem látszik „Bal felső/Fekvő/Álló” vezérlő | mérés (eredeti Picasa vágópanel, `Képernyőkép 2026-07-18 195048.png`); bináris erőforrás (`editpanel.tre:772-782,795-830`, `ui-leltar.csv`) |
| #4551: ma három dinamikus javaslat van, nem a három rögzített méretarány-gomb | mai forrás (`EditorCropPanel.qml:290-328`, `EditorPanel.qml:475-482`) |
| #4572: nem mellőzött, névtelen arcra kattintva megjelenik a keret és a „Type a name” mező | mérés (Colab EN 38; `picasa-arcfelismeres.md:935-944`, `face_type_a_name_reference_en38.png`); bináris (keret/felirat adatút: `0x00642c10`, `0x00641960`, `picasa-arcfelismeres.md:946-949`); mai forrás (`FacesOverlay.qml:78-89,112-124,337-341,406-418`) |
| #4579: az öt panelsor eredeti sorrendje és megjelenési feltételei | bináris (`0x00633210`, `0x00a00120`, `0x00a34b50`, `0x009ea1e0`, `0x00a34b00`); `picasa-metaadat-tulajdonsagok.md:2339-2486` |
| #4579: mind az öt sor szerepel a mai listában, a forrásadat meglétekor | mai forrás (`PropertiesPanel.qml:55-80`, `formatting.py:499-501,518-584`, `tulajdonsag_sorok.py:27-74`, `reader.py:322-360`, `jpeg_quality.py:66-85`) |
| #4846: az eredeti ötös fülsáv ikonjainak iránya | mérés (eredeti Picasa-képernyőkép: `research/testdata/screenshot/2026-07-17 20 56 36.png`; a leltárt az `ui-audit-editor.md` hivatkozza) |
| #4846: a mai ikonok tényleges, renderelt képe és alakbeli eltérése | NINCS MEG (mai renderkép nincs; `EditTabIcon.qml` csak a rajzutasításokat rögzíti) |
| #5121: 4-es `newalbumprompt` rekord céljára ejtés albumot hoz létre | bináris (`0x00cb283c`, `0x00765d30`, `0x005e39a0`, `0x006dc030`); `picasa-konyvtar-eszkoztar-viselkedes.md:576-605` |
| #5121: meglévő album melletti húzások eredményei | mérés (korábbi feljegyzés szerint Colab job-155/-156/-159/-160; `paritas-ellenorzes.md` #5121 sora). A nyers felvételek NINCSENEK MEG a helyi `meroadat.tar`-ban. |
| #5121: a 4-es rekord megjelenik-e a Picasa eredeti listájában nem üres albumszám mellett | NINCS MEG statikusan (`picasa-konyvtar-eszkoztar-viselkedes.md:607-655`) |

## A két független út

| Jegy | A út: eredeti | B út: mai PicasaPy | Egyezés |
|---|---|---|---|
| #4551 | Eredeti `.tre`/UI-leltár és vágópanel-kép | Vágópanel QML | A rögzített Bal felső/Fekvő/Álló gombok hiánya egyezik. Az extra mai cím és felirat eltér. |
| #4572 | Colab EN 38 képernyőkép és a független bináris keret/felirat út (`0x00642c10`, `0x00641960`) | kattintás-, kijelölés-, popup- és helyőrzőkód | Igen, pozitív azonosítójú, nem mellőzött névtelen arcnál. |
| #4579 | Eredeti mezőleképezés, adatgyűjtő és sortábla | mai `exif_entries`, metadata reader és sorformázók | Igen a sorrend és feltételes megjelenés tekintetében. Az alacsony JPEG-minőség előjeles hibája tudatos eltérés. |
| #4846 | Eredeti Picasa képernyőkép | QML Canvas rajzutak | Az irányok egyeznek; a pontos alakra nincs mai renderkép, ezért teljes képi egyezés nem állapítható meg. |
| #5121 | Bináris `newalbumprompt`/drop út és korábban rögzített Colab-húzásmérések | `AlbumsSection.qml` üres listás célterülete és albumonkénti dropja | A rögzített Colab-esetek és a mai célterület-kezelés egyezik; a bináris listaépítési feltétel nyitott. |

## Cáfoló kísérlet

A #5121 azon olvasatát próbáltam cáfolni, hogy az eredeti Picasában az első
album után megszűnik az új albumot létrehozó drop-cél: a `0x00765d30` sorolvasó
és a `0x005e39a0` drop-ág útját vetettem össze. A sorolvasó egy már létező
listarekord `+0x30` típusából választ feliratot; a drop-ág ugyanezen típusú
célrekord esetén hív albumkészítést, de egyik vizsgált ág sem teszteli az
albumszámot. Ez nem cáfolja a célrekord hiányát, mert a listaépítő nem
azonosított. Ugyanezt az ellenpróbát a `picasa-konyvtar-eszkoztar-viselkedes.md`
7/b szakasza is rögzíti; a következtetés nyitva marad a bináris út, a Colab
feljegyzések és a mai QML eltérő mércéjével újraellenőrizve.

## A jegy „Kész, ha” pontjai

- **#4551 - ✅** A rögzített „Bal felső”, „Fekvő”, „Álló” vezérlők nincsenek a
  mai QML-ben; a három eredeti előnézet megmaradt. **Kiegészítés:** a mai
  „Suggested crops” cím és dinamikus stratégiacímkék az eredeti képen nem
  látszanak; a képi paritást célzó következő változtatásból ezeket is el kell
  távolítani.
- **#4572 - ✅** Az EN 38 szerinti arc kattintása keretet és „Type a name”
  mezőt ad; a pozitív azonosítójú arcra a mai kód ezt az utat köti.
- **#4579 - ✅** Mind az öt mező megfelelő sorrendben épül be, amikor a
  hozzá tartozó adat elérhető. A sorok hiánya adat nélküli képnél nem
  ellentmondás; a JPEG-minőség alacsony tartományának eltérése szándékos.
- **#4846 - ⛔** Az irányok a forrásképpel egyeznek; a forma „egyszerűsített”
  állítása csak a mai QML renderelt képével dönthető el.
- **#5121 - ✅** A korábban rögzített Colab-esetekben meglévő album mellett a
  fejléc, sorvége és `+` nem készít új albumot; az album saját sora abba az
  albumba adja a képeket. A mai QML ugyanígy választ külön új-album és
  meglévőalbum-drop utat.

## Javasolt jegytörzs-bővítés

Az alábbi szöveg pontosítja az eredeti/nálunk viszonyt; a #4551-nél a
meglévő jegy bővítéseként használható, a #4846-nál render-ellenőrzés előtt
nem indokol automatikus rajzjavítást.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| #4551: három `cropsug` előnézet felirat és súgó nélkül; nincs Bal felső/Fekvő/Álló rögzített gomb. | Három dinamikus crop-javaslat és saját előnézeti kép, de „Suggested crops” cím és a stratégiák feliratai is látszanak. | A három rögzített gomb maradjon távol. Ha szoros paritás a cél, távolítsuk el a címet és a látható stratégiacímkéket, az előnézeteket és kiválasztást tartsuk meg. |
| #4846: az eredeti ikonok tájolása és rajza a Picasa 3.9 fülsáv-képén látható. | A mai Canvas kód tájolása ezt követi; a jelenlegi render nem áll rendelkezésre. | Először készítsünk mai képernyőképet az öt fülről az eredetihez azonos méretben; csak a mért alakeltérést rajzoljuk újra. |

**Kész, ha:** #4551 esetén nincs a három nem eredeti rögzített méretarány-gomb,
és a három előnézet fölött nincs az eredetiben nem látható cím vagy
stratégiafelirat. #4846 esetén az öt mai ikon az eredeti méretben összevetett; a
tájolás és a rajzeltérések külön vannak rögzítve.

## Új kutatási jegyjavaslatok

- **#4846 képi összevetés:** az öt mai ikon renderelt képének rögzítése az
  eredeti `2026-07-17 20 56 36.png` ikonjaival azonos méretben; a cél annak
  eldöntése, hogy az irányok helyessége mellett marad-e alakbeli eltérés.

## Nyitott

- #4846: mai, ténylegesen renderelt ikoncsík - **NINCS MEG**. Döntő mérés: a
  jelenlegi öt fülről képernyőkép az eredeti képpel azonos méretben.
- #5121: a Picasa listájában mikor és hová kerül a 4-es típusú sor nem üres
  albumlistánál; a listaelem és a képernyőn elérhető drop-cél összerendelése.
  A korábbi Ghidra-kimenetekben a címekhez hívási/xref-sorok vannak, teljes
  függvénytest nincs; a két kérdés a
  `picasa-konyvtar-eszkoztar-viselkedes.md:653-655` alatt már nyitva áll:
  - Ghidra-kör kell: 0x00762540 - a `CAlbumList` mely ága és hová teszi be a `+0x30 = 4` sort, ha már van album, és a sor mely területe fogadja a dropot? [blokkoló]
  - Ghidra-kör kell: 0x00565920 - a konstruktor melyik hívási útja tölti fel a `+0x2c0` albumlistát, és a 4-es sor beszúrása függ-e az albumok számától? [blokkoló]
- #5121: a korábbi Colab-felvételek nyers képei helyben nem elérhetők; ha a
  jegy döntéséhez újbóli vizsgálat kell, rögzítsük a listát nulla és egy saját
  albummal, majd húzzunk ugyanazt a képet a `newalbumprompt` sorra, fejlécére,
  sorok közé/alá, valamint a `+` céljára; ellenőrizzük az új album nevét,
  sorát és a képek célalbumát.

## Módosított fájlok

- `docs/specs/forras-audit-5186-6.md` - e kör öt tételes kutatási eredménye.
- `docs/specs/paritas-ellenorzes.md` - a #4551, #4572, #4579, #4846, #5121
  forrás- és mai-kód állapota.
- `docs/specs/picasa-metaadat-tulajdonsagok.md` - a #4579 G táblájának öt
  elavult „nincs” celláját a mai mezőkre és feltételeikre javítottam.
- `docs/specs/vagas-eszkoz-allapot.md` - a három crop-előnézet bekötését és a
  cím/felirat eltérését rögzítettem.
- `docs/specs/00-index.md` - a kutatási lap indexbevétele.
