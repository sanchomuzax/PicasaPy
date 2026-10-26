# Forrás nélküli jegyek összevetése, 2. köteg (#5453)

Ez a lap a #5186 gyűjtő második, húsz jegyes kötegét veti össze a Picasa 3.9
eredeti forrásaival és a jelenlegi PicasaPy-forráskóddal. Az ítélet a
megnevezett viselkedés forráskód szerinti összevetése; ahol a jegy kattintásos
tesztet vagy mai renderelt képet kér, azt külön jelölöm, és nem tekintem
elvégzett mérésnek.

## Összesítő

| Jegy | Ítélet | Bizonyítottság | Eredeti forrás | Teendő |
|---|---|---|---|---|
| #3998 | ELTÉR | megerősített | `picasa-metaadat-tulajdonsagok.md` §16.H; `0x009ece70`, `0x009ecfb8`, `0x009ecdd2`; mérés: 186 export | A túl nagy EXIF-blokk miatti végső ágat rögzíteni tudatos eltérésként vagy hozzáigazítani. |
| #4313 | EGYEZIK | feltételes | `picasa-program-resources.md` §7.5; mérés: 41 katalógus; `i18n_build.py`, `application.py` | A hiányzó fordítás- és körbejárási ellenőrzéseket futtatni. |
| #4314 | ELTÉR | feltételes | `picasa-fo-ablak-elrendezes.md` §G; bináris `0x004060b0`, `0x00c7f2c8` | Ha teljes paritás a cél, az eredeti nyelvi feltételeket, szöveget és kulcsokat követni. |
| #4320 | EGYEZIK | feltételes | `options.fen`; bináris `0x007fad0a`, `0x007fadbb`; `picasa-create-features.md` | Kattintásos teszt kell az elfogadási ponthoz. |
| #4358 | EGYEZIK | feltételes | mérés: `research/testdata/screenshot/2026-07-17 21 00 20.png`; `options.fen` | A mai renderelt felületet a referenciaképpel mérni; a Google Címtár-sor feltételét külön lezárni. |
| #4377 | EGYEZIK | feltételes | mérés: `research/testdata/screenshot/2026-07-17 21 00 04.png`; bináris `0x007fad0a`, `0x007fadbb` | A renderelt elrendezést mérni. |
| #4385 | EGYEZIK | feltételes | mérés: `research/testdata/screenshot/2026-07-17 21 00 07.png`; bináris `0x006e5ab0`; `picasa-nyomtatas.md` §39 | A renderelt elrendezést mérni; az eredeti metrikus alapérték csak mentett felülírás nélkül érvényes. |
| #4440 | NEM DÖNTHETŐ EL | nyitott | NINCS MEG az eredeti látható visszajelzés négy műveletre | Colab-felvétel kell mentés, visszaállítás és fotóművelet sikeres és hibás végéről. |
| #4456 | EGYEZIK | feltételes | `album.fen`; mérés: `research/testdata/screenshot/2026-07-17 20 59 22.png`; bináris `0x008496c0`, `0x00849750` | A mai renderelt ablakot a referenciával mérni. |
| #4482 | NEM DÖNTHETŐ EL | nyitott | `album.fen` és a névmezőt mutató mérés; az eredeti sikeres átnevezés NINCS MEG | Colab-felvétel kell sikeres és már létező nevű célra végzett átnevezésről. |
| #4488 | EGYEZIK | feltételes | mérés: `research/testdata/screenshot/2026-07-17 21 00 00.png`; `options.fen` | A renderelt méreteket összevetni; a link és a kapcsolók kattintásos tesztjét futtatni. |
| #4494 | EGYEZIK | megerősített | `album.fen`; eredeti bináris `0x008d8070`, `0x008d9243`; a dátummező gombját mutató mérés | A mai QML megnyitja a naptárat; az eredeti vezérlő típusa és létrehozása statikusan igazolt. |
| #4531 | EGYEZIK | feltételes | `searchoptions.tre`; `picasa-kereses-modok.md` §2 | Kattintásos próbát kell rögzíteni. |
| #4534 | EGYEZIK | megerősített | `picasa-menu-parancsok-viselkedes.md` § `ID_PICTURE_SPLITALBUMHERE`; bináris `0x00730790`, `0x005cb990`, `0x005e8570` | A műveleti kattintásos és `.picasa.ini`-ellenőrzés még kell. |
| #4539 | EGYEZIK | feltételes | `picasa-create-features.md` §2.8/c; mérés: `research/testdata/screenshot/2026-07-17 20 54 38.png` | A filmkészítő megnyitását kattintással ellenőrizni. |
| #4542 | NEM DÖNTHETŐ EL | nyitott | bináris figyelmeztetőszöveg `0x00e063da`, xref `0x005f30e0`; a megjelenési feltétel NINCS MEG | Colab-felvétel kell kiegyenesített és kiegyenesítetlen képpel. |
| #4544 | NYITOTT | Picasa 3.7 bináris (`0x0060a980`, `0x00847880`, `0x00901110`, `0x00913960`, `0x00913420`); RTTI-név: 3.9-es index; mai `render/retouch.py` | Az eredeti út rekordból, illetve float-paraméterből téglalapnyi feldolgozási régiót képez és képsorokat másol; a látható peremképzés nem azonosított. Eredeti és mai mentett kimenet összehasonlítása hiányzik. |
| #4550 | EGYEZIK | feltételes | `customaspectratio.fen`; `editpanel.tre` | A jegy „élő példa” premisszáját statikus példára kell javítani; mai render nincs. |
| #4551 | EGYEZIK | feltételes | `editpanel.tre`; mérés: eredeti crop-panel erőforrásleltár | A mai renderelt panelt a referenciával összevetni. |
| #4557 | EGYEZIK | feltételes | `ui-audit-editor.md`; `filterdesc-registry.md` §162-163 | Kattintásos Shift+Ragyogás-próba kell. |

## Tételenként

### #3998 - EXIF-bélyegkép az exportált JPEG-ben

**Eredeti:** az új `IFD1`-bélyegkép feltétele, hogy a kép szélessége és
magassága is 300-nál nagyobb (`0x009ece70`-`0x009ece8c`). A cél a
160 × 160-as keret, Lanczos-3 mód (`0x009ecfb8`) és a 85-ös JPEG-minőség
(`0x009ecdd2`). A 186 export mérése alátámasztja a méretet és JPEG-kódolást.
Részletek: `picasa-metaadat-tulajdonsagok.md` §16.H-16.I.

**Nálunk:** `src/picasapy/metadata/exif_belyegkep.py` építi a bélyegképet;
a kicsinyítés `src/picasapy/render/glimmer_ops.py` Lanczos-3 útját használja.
Az egyező fő ág és a kivétel összevetése: `paritas-ellenorzes.md` #3998 sora.

**Ítélet: ELTÉR.** A küszöb, a méretezés, a Lanczos-3 és a 85-ös minőség
egyezik. Ha az EXIF-blokk 10-es minőségen sem fér el, az eredeti eldobja az
egész EXIF-et, a PicasaPy pedig a bélyegképet hagyja el és a többi EXIF-adatot
megtartja.

**Teendő:** A túl nagy EXIF-blokk végső ágát egyeztesse az eredetivel, vagy
rögzítse külön döntésként a tudatos eltérést.

**Kész, ha:** A címben felsorolt négy fő jellemző igazolt; a ritka túlméretes
EXIF-ág eltérése maradéktalanul fel van tüntetve. A valódi exporton végzett új
ellenőrzést ebben a körben nem futtattam.

### #4313 - Közös szótár 41 nyelvre

**Eredeti:** a Picasa erőforrás-leírása 41 nyelvi változatot tart nyilván
(`picasa-program-resources.md` §7.5). A korábbi jegy
1252 eredeti fordítás-párra hivatkozik, de ezt a számot ebben az auditban nem
ellenőriztem, ezért nem veszem át tényként.

**Nálunk:** 41 `picasapy_*.ts` fájl van. A katalógusmérésben mindegyik
2878 bejegyzésű, minden bejegyzés eredetjelölt, és a `missing_count` értéke
0. A `dictionary.py` kezeli a jelölést és a hiányzó sorok számlálását;
az `i18n_build.py` építi a `.qm` fájlokat, az `application.py` tölti be a
`QTranslator`-t.

**Ítélet: EGYEZIK.** A nyelvenként egy `TS`-katalógus az eredeti és saját
szövegek megkülönböztetésére, valamint a Qt-fordítási út jelen van.

**Teendő:** Nincs forrásból igazolt fejlesztési eltérés; az alább felsorolt
korábbi nyelvi adatok és futásidejű elfogadási próbák még ellenőrzendők.

**Kész, ha:**

- ✅ 41 katalógus, eredetjelölés és hiányzóbejegyzés-számláló: mérés a mai `TS`
  fájlokon és a `dictionary.py`-ban.
- ⛔ A magyar korábbi katalógushoz képesti veszteségmentesség: nincs ebben a
  körben független korábbi példánnyal végzett tartalmi diff.
- ⛔ A további nyelvek eredeti fordítás-párjainak teljessége: az eredeti
  nyelvi korpusz soronkénti összevetését és a gépi fordítás hiányának
  ellenőrzését nem végeztem el.
- ⛔ `.qm` előállítás, nyelvválasztás és következő indítás: a kódbeli út megvan,
  futó alkalmazásos próbát nem végeztem.
- ⛔ Beolvasás-visszaírás bájtpontos körbejárása: a számláló kódja megvan, a
  körbejáró őrt nem futtattam.

### #4314 - Induláskori nyelvfelajánlás

**Eredeti:** a `0x004060b0` rutin csak hiányzó `ytHLocal::lang` esetén,
Windows NT-n és az eredeti 11 támogatott rendszer-nyelv egyikén kérdez.
Angol rendszer-nyelvnél nem kérdez. A beágyazott angol prompt a
`0x00c7f2c8` címen, `Yes`/`No` gombokkal jelenik meg. Az elfogadás a rendszer
nyelvét, az elutasítás az angolt tárolja `lang`-ként; a rutin a
`langchange` értékét is beállítja. Forrás: `picasa-fo-ablak-elrendezes.md`
§G.

**Nálunk:** `src/picasapy/app/language_controller.py` minden első induláskor
felajánlja a rendszer nyelvét, ha a támogatott katalógus nem angol. Ez az
eredeti 11-nél tágabb kör. A `FirstRunLanguageDialog.qml` PicasaPy-nevet
tartalmazó szöveget használ; a választást `general/language` és
`general/language_pending` kulcsban tárolja.

**Ítélet: ELTÉR.** A jelenlegi viselkedés a 39 nem angol katalógushoz
felajánlja a váltást, az eredeti 11 nyelvi feltételt és kulcsneveket követő
paritás helyett.

**Teendő:** Az indulási nyelvfelajánlás kövesse a Picasa 3.9 feltételeit,
üzenetét és tárolási kulcsait, vagy a bővítést nevezze meg tudatos termék-
eltérésként.

**Kész, ha:**

- ✅ A négy eredeti kérdésre - mikor, milyen szöveggel, milyen gombokkal és
  milyen tárolással kérdez - a §G utasításszintű választ ad.
- ✅ Az Eredeti / Nálunk / Teendő összevetés ebben a szakaszban szerepel.

### #4320 - Diavetítés ismétlés és zene

**Eredeti:** az `options.fen` megnevezi a két beállítást. A bináris
alapértékek: ismétlés ki (`LoopSlideshow`, `0x007fad0a`), zene be
(`PlayMP3Tracks`, `0x007fadbb`); a zenemappa a `MP3SlideshowPath` kulcson
keresztül tárolódik. Lásd `picasa-fen-dialogs.md` §3.11 és
`picasa-create-features.md` diavetítés szakasza.

**Nálunk:** `OptionsTabSlideshow.qml` a kapcsolókat és a mappát a
vezérlőhöz köti; `controller.py` false/true alapértéket ad; `Main.qml` és
`SlideshowView.qml` a beállításokat használja.

**Ítélet: EGYEZIK.** A két állapot perzisztens beállításon át jut el a
diavetítéshez.

**Teendő:** Nincs statikus forrásból igazolt eltérés.

**Kész, ha:**

- ✅ A vezérlő, a tárolt érték és a diavetítés közötti kódbeli út megvan.
- ⛔ Valódi kattintásos tesztet és zenelejátszást ebben a körben nem futtattam.

### #4358 - Névcímke-csúszkák és sorrend

**Eredeti:** a referencia `2026-07-17 21 00 20.png` mutatja a két csúszka
melletti `85` értéket, a beosztásokat, a jobb oldali címkéket és azt, hogy a
Google Címtár feltöltési sor ezen a felvételen nincs jelen. Az `options.fen`
leírja a csúszkákat és a `ticks=10` beosztást. A bináris az eredeti két
küszöbérték alapját `0x006e0ed5` és `0x006e0eed` címen adja meg. A képen
látható `85` mentett állapot is lehet, ezért a kép önmagában nem alapérték-
bizonyíték.

**Nálunk:** `OptionsTabNameTags.qml` mindkét értéket mutatja, a tickeket,
csúszkák hosszát és jobbra igazított feliratokat tartalmazza. A Google
Címtár-sor rejtett.

**Ítélet: EGYEZIK.** A kódbeli vezérlők és a felvételen látható szerkezet
egyeznek. A PicasaPy küszöb-alapértéke nem része ennek az elrendezési
ítéletnek.

**Teendő:** A Google Címtár-sor megjelenési feltételét az eredeti
`options.fen`-hez kell kötni, ha a feltételes sor láthatóságát is számon
kéri a jegy.

**Kész, ha:**

- ⛔ Renderelt PicasaPy-kép és mért pixel-összevetés nem készült.
- ⛔ A `uploadcontactphotos` eredeti megjelenési feltételét nem döntöttem el;
  a felvétel csak a vizsgált mentett állapotot mutatja.
- ⛔ A renderelt összevetési mérés hiányzik.

### #4377 - Diavetítés fül alapértékei és elrendezése

**Eredeti:** a `2026-07-17 21 00 04.png` képen az ismétlés nincs bejelölve,
a zene be van jelölve, a mappafelirat a mező fölött van. Az alapértékeket a
`0x007fad0a` és `0x007fadbb` bináris címek támasztják alá.

**Nálunk:** `OptionsTabSlideshow.qml` és a beállításvezérlő ugyanezeket a
false/true alapértékeket adja; a mappaválasztó felirata a mező fölött van.

**Ítélet: EGYEZIK.** Az alapérték és a forráson látható szerkezeti sorrend
egyezik.

**Teendő:** Nincs statikus forrásból igazolt eltérés.

**Kész, ha:**

- ✅ Mindkét alapérték bináris címmel igazolt, a jelenlegi kódértékek egyeznek.
- ⛔ A renderelt elrendezés képpontos összevetését nem végeztem el.

### #4385 - Nyomtatási alapméretek és elrendezés

**Eredeti:** a `2026-07-17 21 00 07.png` felvétel öt centiméteres méretet
mutat két oszlopban, de a beállított `Preferences\\PrintSize0`-`PrintSize4`
felülírás miatt a kép önmagában nem bizonyít alapértéket. Az eredeti
`0x006e5ab0` a `GetLocaleInfoA` `LOCALE_IMEASURE` értéke szerint választ
metrikus ötös alapértéket: `10x15`, `13x18`, `15x20`, `20x25 cm`, `Contact
Sheet`; a mentett értékek felülírják. A bináris levezetés: `picasa-nyomtatas.md`
§39.

**Nálunk:** `printing/dpi.py:176-204` a `QLocale.system().measurementSystem()`
alapján választ; a metrikus hiányzó-kulcs alapérték az eredeti ötös, a
`print_controller.py:259-276` pedig a mentett öt értéket tiszteletben tartja.
`OptionsTabPrinting.qml:74-92` a méretválasztót 3 soros, oszloponként
feltöltött rácsban építi fel: balra három, jobbra két mező.

**Ítélet: EGYEZIK.** Metrikus területi beállításnál és mentett méretfelülírás
nélkül az alapméret-készlet az eredeti szabályát követi. A kétoszlopos,
3+2-es szerkezet is a jelenlegi QML-ben van. A képernyőkép mentett méreteket
mutathat; a mai render képpontos összevetése nincs meg.

**Teendő:** Nincs kódbeli eltérés az eredeti metrikus alapérték-szabályhoz.

**Kész, ha:**

- ✅ A bináris területi szabály és a PicasaPy területi szabálya azonos irányú;
  a mentett értékek elsőbbsége dokumentált.
- ⛔ A mai renderelt elrendezés képpontos összevetése nincs; a szerkezeti
  kétoszlopos elrendezést a QML forrás igazolja.

### #4440 - Látható visszajelzés műveletvégén

**Eredeti:** NINCS MEG olyan forrás vagy felvétel, amely a négy említett
jelzés látható eredményét műveletenként bizonyítaná. A következő mérésnek az
eredeti Picasában mentés, visszaállítás és egy fotóművelet sikeres és hibás
ágát kell rögzítenie, a művelet befejezése után látható ablakkal.

**Nálunk:** a `save_controller.py` a mentés/visszaállítás befejezési
jelzéseit belső kezelőhöz köti, amely nézetet frissít és backup-revíziót
növel; ez önmagában nem bizonyít felhasználónak látható visszajelzést. A
korábbi `photoOpFinished` jelzés nincs meg a mai kódban; hibajelzések és
domain-specifikus jelek maradtak.

**Ítélet: NEM DÖNTHETŐ EL.** Az eredeti kimenet nincs meg, a mai némajelzés-
őr és QML-hatás tesztjét sem futtattam.

**Teendő:** A négy jelzés mindegyikének eredeti sikeres és hibás lezárását
rögzítsük, mielőtt látható akciót választunk.

**Kész, ha:**

- ⛔ A `nema_jelzesek.py` mérés eredménye nincs meg.
- ⛔ Sikeres és hibás ágra kattintásos QML-tesztet nem futtattam.
- ⛔ Törölt jelzés indoklását a négy jelzés azonosítása után lehet megadni.

### #4456 - Mappa tulajdonságai elrendezése

**Eredeti:** az `album.fen` Név-, Dátum-, Zene-, Hely- és Leírás-sorokat
definiál; a magyar felvételen látszik a „Mappa tulajdonságai” cím, a balra
álló feliratok, a kijelölt szerkeszthető Név és a Mégse gomb. A cím sztringjét
a bináris `CEditAlbum::folderTitle` állítja (`0x008496c0`, `0x00849750`;
sztring `0x00cc1be8`). Forrás: `picasa-fen-dialogs.md` §3.2 és a megnevezett
képernyőkép.

**Nálunk:** `FolderPropertiesDialog.qml` tartalmaz címet, bal oldali
mezőfeliratokat, engedélyezett Név-mezőt és Mégse gombot.

**Ítélet: EGYEZIK.** A megnevezett szerkezeti elemek forráskódban jelen
vannak; a mai pixelek összevetése nem történt meg.

**Teendő:** Nincs statikus forrásból igazolt eltérés.

**Kész, ha:**

- ✅ Cím, feliratok és gombszöveg forrás szerint egyezik.
- ✅ A Név-mező az eredeti FEN mezővel összhangban szerkeszthető.
- ⛔ Mai képernyőkép és ±5 px-es ablakmagasság-próba nincs.

### #4482 - Átnevezés a Név mezőből

**Eredeti:** az `album.fen` `filter="filename"` névmezőt ír elő, a
képernyőkép pedig szerkesztésre kijelölt nevet mutat. Az eredeti sikeres
átnevezés, a már létező cél kezelése és a mappafa frissülése NINCS MEG.

**Nálunk:** a `FolderPropertiesDialog.qml` mentési útja átnevező kezelőhöz
jut; a `FolderPane.qml` és a `library_controller.py` frissíti a mappát és
indexet. A `fileops/rename_folder.py` már létező cél esetén hibát ad, amit a
párbeszéd hibaablakban mutat meg.

**Ítélet: NEM DÖNTHETŐ EL.** A mai átnevezési út jelen van, de az eredeti
eredmény és a hibás célra adott válasz nincs összevetve.

**Teendő:** Az eredeti Picasában nevezzünk át egy mappát és próbáljunk ki
egy már létező nevet; rögzítsük a párbeszédet, a mappalistát és az útvonalat.

**Kész, ha:**

- ⛔ Az eredeti és a mai sikeres átnevezést kattintásos próbával nem
  ellenőriztem.
- ⛔ A mai kód a már létező célra hibát ad, de az eredeti válasz és a
  kattintásos próba nincs meg.
- ⛔ A renderelt összevetés nincs meg.

### #4488 - Fájltípusok fül

**Eredeti:** a `2026-07-17 21 00 00.png` képen a fájltípusok sorrendje,
felirata és sorköze látható. Az `options.fen` a fül vezérlőit írja le.

**Nálunk:** `OptionsTabFileTypes.qml` a megnevezett fájltípus-feliratokat,
sorokat és elrendezést tartalmazza; a `RAW`-formátumokra mutató hivatkozás
megnyitja a támogatott formátumok paneljét.

**Ítélet: EGYEZIK.** A forráskód feliratai és sorrendje megfelel a
referenciának; a pontos képpont-egyezést ez nem bizonyítja.

**Teendő:** Nincs statikus forrásból igazolt eltérés.

**Kész, ha:**

- ⛔ Mai render és ±5 px-es összevetés nem készült.
- ✅ A `RAW`-formátumra mutató hivatkozás a támogatott formátumok nézetéhez
  vezet a QML kódban.
- ⛔ A kapcsolók és mentés kattintásos tesztjét nem futtattam.

### #4494 - Dátummező naptárral

**Eredeti:** az `album.fen` `date` vezérlőt és Automatikus dátum gombot ír
le. A bináris `0x008d8070` rutinja a `SysDateTimePick32` osztályt hozza létre
`0x50810000` dátumstílussal; a `0x008d9243` ezt az osztálynevet külön
felismeri. A referencia (`2026-07-17 20 59 22.png`) a dátummező legördülő
gombját is mutatja.

**Nálunk:** `FolderPropertiesDialog.qml` naptárgombot és
`DateCalendarPopup.qml` naptárfelugrót tartalmaz; a kiválasztott dátum a
mezőbe kerül. A mező formázása a helyi nyelvhez igazodik.

**Ítélet: EGYEZIK a vezérlő forrás szerinti típusában és a mai útban.** Az
eredeti `SysDateTimePick32` dátumvezérlő és a mai gombból megnyíló naptár
forrásban jelen van; Colab-kattintás és pixel-összevetés nem készült.

**Teendő:** Forrás alapján nem indokolt javítás. Pontos vizuális paritás
igényénél a mai renderelt képet még össze kell vetni a referenciával.

**Kész, ha:**

- ✅ Az eredeti dátumvezérlő osztálya és a mai naptárnyitó út statikusan
  igazolt.
- ⛔ Az eredeti naptár tényleges kattintásos felvétele és a mai renderelt
  pixel-összevetés nincs.
- ⛔ Nyelvi dátumalak és kézi beírás kattintásos ellenőrzése nincs.
- ⛔ Az eredeti és mai kattintásos próba, valamint a renderelt összevetés
  nincs.

### #4531 - Vissza a teljes nézethez szöveges keresés után

**Eredeti:** a `searchoptions.tre` tartalmazza a `viewallbutton` elemet; a
felirat `Back to View All`, a súgó `Exit Search Mode` a
`picasa-kereses-modok.md` §2 szerint.

**Nálunk:** `search_controller.py` a szöveges keresést aktív szűrésként
jelöli; `Main.qml` a Vissza a teljes nézethez gombot mutatja, és visszaállítja
a teljes nézetet.

**Ítélet: EGYEZIK.** Az eredeti felirat/súgó és a jelenlegi vezérlési út
ugyanazt a kilépést írja le.

**Teendő:** Nincs statikus forrásból igazolt eltérés.

**Kész, ha:**

- ✅ A szöveges keresési állapothoz tartozó gomb és a teljes nézetre visszatérő
  mai út megvan.
- ⛔ A keresés-gomb kattintásos próba nincs.

### #4534 - Mappa felosztása a kijelölt képnél

**Eredeti:** a menüépítő és parancstábla a menüpontot a `0x005e8570`
kezelőhöz kapcsolja (`0x00730790`, `0x005cb990`). A kezelő az első
kijelölt képtől a mappa végéig terjedő tartományt választja, új testvérmappát
hoz létre, majd áthelyezi a képeket. A részletes utasításszintű leírás és
független parancsazonosító-ellenőrzés a
`picasa-menu-parancsok-viselkedes.md` `ID_PICTURE_SPLITALBUMHERE` szakaszában
van.

**Nálunk:** `Main.qml` az első kijelölt sortól átadja a kiválasztott
tartományt; `fileops_controller.py` létrehozza a mappát, mozgatja a képeket
és frissíti az állapotot.

**Ítélet: EGYEZIK.** A binárisban kiolvasott tartomány és a mai forráskód
mozgatási útja egyezik.

**Teendő:** Nincs statikus forrásból igazolt eltérés.

**Kész, ha:**

- ✅ A viselkedés specifikálva van, a mai forrás ugyanazt a tartományt
  valósítja meg.
- ⛔ Kattintásos mozgatást és a két mappa `.picasa.ini` fájljait nem
  ellenőriztem.

### #4539 - Film készítése gomb a mappafejlécben

**Eredeti:** a `headerpanel/create_movie` erőforrás a mappafejléc gombját
írja le; a `2026-07-17 20 54 38.png` referencián a gomb látható. A
`picasa-create-features.md` §2.8/c ezt rögzíti.

**Nálunk:** `LightboxHeader.qml` mappanézetben látható Film készítése gombot
és `movieRequested()` jelet ad.

**Ítélet: EGYEZIK.** Az eredeti alapállapot és a mai gomb feltétele egyezik.

**Teendő:** Nincs statikus forrásból igazolt eltérés.

**Kész, ha:**

- ✅ Az eredeti láthatósági kérdés kutatása és a spec rögzítése kész.
- ⛔ A filmkészítő megnyitását és a mai referenciaképet nem ellenőriztem.

### #4542 - Vörösszem-figyelmeztetés kiegyenesítés után

**Eredeti:** az `IDS_WARN_REDEYE_ACCURACY` szövege a binárisban
`0x00e063da` címen van, a hivatkozó rutin indexelt címe `0x005f30e0`.
Ez a szöveg létezését bizonyítja, de nem dönti el, hogy a figyelmeztetés
pontosan mikor jelenik meg. A kiegyenesítéshez kötött eredeti feltétel NINCS
MEG; azt egyenes és kiegyenesített képen végzett Colab-felvétel döntheti el.

**Nálunk:** `EditorRedeyePanel.qml` az eredeti figyelmeztetést mutatja,
amikor `panel.straightenActive` igaz.

**Ítélet: NEM DÖNTHETŐ EL.** A szöveg forrása ismert, az eredeti megjelenési
feltétel nem.

**Teendő:** Mérjük meg az eredeti figyelmeztetést kiegyenesítés előtt és
után, majd a mai feltételt a felvételhez igazítsuk.

**Kész, ha:**

- ⛔ Az eredeti kiegyenesített és kiegyenesítetlen állapot közti
  figyelmeztetés-különbség nincs felvéve.
- ⛔ A mai kattintásos próba nincs.

### #4544 - Retusfolt szélének olvadása

**Eredeti bináris út - RetouchEdit és feldolgozási terület (#5975):** az `editpanel.tre:958-963` az `editpanel/retouchoverlay`-hez köti a `Handler retoucher`-t a körkurzorral és ecsetvezérlővel. A `RetoucherHandler::vftable` (`0x00c9b130`) a `0x0060a980` eseménykezelőre mutat; a dekompilált kód az egér-esemény koordinátáit képpont-/képkoordináta-útba viszi, a `retouchcheckpoint` erőforrást pedig a lezáró ágban használja.

A `RetouchEdit::vftable` (`0x00ca83c4`) a `0x00847880`, `0x00848030`, `0x00848a10` és `0x00847f30` függvényeket tartalmazza. A `0x00848030` és `0x00848a10` 40 bájtos (`0x28`) rekordokból álló tömböket bővít/ürít; pixelpuffert vagy peremkeverést nem számolnak. A `0x00847880` célzott diszasszemblyje a rekord négy mezőjéből 16 bájtos téglalapot állít elő: az eredmény `(r[0x18], r[0x1c], r[0x18]+r[0x08], r[0x1c]+r[0x0c])` (`0x0084799e`-`0x008479b6`). A `0x00847f30` a kiszámított téglalapot és a képkulcsot a `0x006bd580` régió-/frissítési útjára adja át. A `PatchEdit::vftable` (`0x00ca8344`) szintén tartalmazza a két rekordkezelő függvényt: ez cáfolja azt az erősebb olvasatot, hogy a két konténermetódus önmagában a Retouch-folt alakját vagy peremképletét írná le.

A további útban a 3.9-es binary-index szerint `CRetouchFilter`-hez tartozó `0x00901110` rutin 20 bájtos (`0x14`) rekordokon iterál, majd a `0x00913960`-at hívja (`0x009012a5`). A `0x00913960` a határkoordináták különbségeiből területet és sorcímeket számol (`0x009139e3`-`0x00913a16`), két alkalommal meghívja a `0x00913420`-at, majd a sorok másolásához a bináris-indexben `_memcpy` néven szereplő `0x00bf2350` címet hívja (`0x00913b44`-`0x00913b47`). A `0x00913420` float-paramétert ír az objektum `[+0x48]` mezőjébe, koordinátákból területhatárokat képez, majd ezeket a képméretekhez korlátozza (`0x0091346c`-`0x00913839`); ez téglalapnyi feldolgozási geometria, nem látható alfa- vagy színkeverési képlet. A sor-másolási út a téglalapnyi ROI feldolgozását támasztja alá, de nem mondja meg a perempixelek súlyát vagy a mentett kimenet látható alakját. A függvénycímekhez használt RTTI-nevek a helyi 3.9-es binary-indexből származnak; a fenti utasítások az eredeti 3.7-es EXE célzott diszasszemblyjéből valók. **A látható folthatár képlete és ecsetméret-függése NINCS MEG.**

A `retouch=1;` token nem hordoz foltkoordinátát (`filters-decoded.md`, „A `redeye` és a `retouch` sosem hordoz régiót”). A mérőadat-archívum tagneveiben `#5975`, `#4544`, `retouch`, `retus` vagy `ui_capture` egyezés nincs; a korábbi Colab-képleltár job #58-a sem tartalmaz retus-kimenetet. Eredeti mentett előtte-utána kép és új Colab job-szám **NINCS MEG**.

**Nálunk:** a `PhotoViewer.qml`/`edit_controller.py` út két kattintással rögzíti a cél- és forráspontot; a `render/retouch.py:68-71` a sugarat a kép rövidebb oldalához viszonyítja, a `:150-161` körmaszkot készít, a `:203` pedig `cv2.seamlessClone`-t hív (kivételkezelő Poisson-fallbackdel). Ez a jelenlegi forrás útja, nem azonos bemeneten mért eredmény.

#### Eredeti / nálunk / teendő

| | eredeti | nálunk | teendő |
|---|---|---|---|
| feldolgozási geometria | Bináris (`0x00847880`, `0x00913420`): rekordból, illetve koordináták és float-paraméter alapján téglalap és képszélhez korlátozott ROI; a filterút soronként másol | Forrás (`render/retouch.py:150-161`): körmaszk, `:203`: seamlessClone | Azonos kép és ecset mellett mentett eredeti és PicasaPy kimenet kell; a téglalap/ROI önmagában nem bizonyít látható alakot. |
| folthatár | A vizsgált bináris útból az alfa-/súlyozási képlet **NINCS MEG** | A mai körmaszk/Poisson-folyamat ismert | Pixelkülönbség-méréssel dönthető el, hogy a különböző belső utak láthatóan eltérnek-e. |

**Ítélet: NYITOTT.** A bináris feldolgozási terület útja a virtuális kezelőtől a koordináták/float-paraméter alapján képszélhez korlátozott téglalapig és a képsorok másolásáig részben feltárt. A látható perempixelek súlyozása és az eredeti kimenet nincs mérve; a belső módszerek különbözősége önmagában nem bizonyít képi eltérést.

**Teendő:** ugyanazon ismert kép, azonos ecsetméret és ecsetvonás mellett készítsen új eredeti Colab-felvételt a mentett kimenettel és valódi kattintásos PicasaPy-párt. A két fájl képpontkülönbségét mérje meg. A bináris feldolgozási út további bővítése helyett a konkrét folthatár viselkedését a mentett minták döntik el; a jelen munkamenetben ilyen eredeti/PicasaPy-felvétel nincs.

**Kész, ha (#5975):**

- ✅ Binárisból az egér-esemény és a feldolgozási régió útja részben azonosított (`0x0060a980` → RetouchEdit téglalapok → `0x00901110`/`0x00913960`/`0x00913420` ROI és képsor-másolás); ⛔ a látható perempixelek súlyozása **NYITOTT**.
- ⛔ Eredeti Colab-retusfelvétel és mentett kimenet: **NINCS MEG**.
- ⛔ PicasaPy valódi kattintásos párja és mentett kimenete: **NINCS MEG**.
- ⛔ Kimeneti pixelkülönbség, látható folthatár-ítélet: **NINCS MEG**.

### #4550 - Egyéni méretarány példa és törlés

**Eredeti:** a `customaspectratio.fen` `Example:` sora statikus szöveg:
`4 x 6 Small print`; nincs rajta adatkapcsolat. Az `editpanel.tre` a
`crop_delete_custom` törlést a legördülő mellé helyezi.

**Nálunk:** `AddCustomAspectRatioDialog.qml` statikusan mutatja a példát;
`EditorCropPanel.qml` a törlőgombot a méretarány-választó mellett tartja.

**Ítélet: EGYEZIK.** A jegy „élő példa” kérése téves premisszából indul:
az eredeti példa is statikus. A jelenlegi fő viselkedés a forrással egyezik.

**Teendő:** A fejlesztői kérést „statikus példa-sor” alakra kell pontosítani;
az eredeti forrás által nem igazolt lista-szakaszcím külön kérdés marad.

**Kész, ha:**

- ⛔ A jegyben kért élő példa nem eredeti viselkedés; a képernyőképes
  összevetés nincs.
- ⛔ A törlőgomb a legördülő mellett van, de az eredeti lista-szakaszcímre
  nincs bizonyíték.
- ⛔ Renderelt összevetés nincs.

### #4551 - Nem eredeti vágógombok

**Eredeti:** az `editpanel.tre` és a crop-panel erőforrásleltár a három
képes vágási javaslatot mutatja, a „Bal felső”, „Fekvő” és „Álló” feliratú
gombokat nem.

**Nálunk:** `EditorCropPanel.qml` nem tartalmazza a három kért feliratú
gombot; a három képes javaslat megmarad.

**Ítélet: EGYEZIK.** A jegy által kifogásolt három szöveges gomb hiányzik.
A mai javaslatok feliratai/címsora ettől külön, nem ebben a jegyben eldöntött
eltérés.

**Teendő:** Nincs további teendő a három megnevezett gomb eltávolítására.

**Kész, ha:**

- ✅ A három megnevezett szöveges gomb nincs a mai QML-ben.
- ⛔ A mai vágópanel renderelt összevetése nincs.

### #4557 - Shift+Ragyogás csúszkái

**Eredeti:** az eredeti Shift-pár a `glow` szűrő, két vezérlője
Intenzitás és Sugár (`ui-audit-editor.md`, `filterdesc-registry.md`
§162-163).

**Nálunk:** `EditorEffectsTab1.qml` Shift állapotban `glow`-t választ;
`effect_params.py` mind a `glow`, mind a `glow2` számára Intenzitás és Sugár
csúszkát ad.

**Ítélet: EGYEZIK.** A Shift-választás csúszkás paraméterpanelre mutat a két
megfelelő vezérlővel.

**Teendő:** Nincs statikus forrásból igazolt eltérés.

**Kész, ha:**

- ✅ A Shift-választó és a két csúszka a mai QML/katalógus útján megvan.
- ⛔ A kattintásos próba nincs.

## Bizonyítottság, független utak és cáfoló kísérlet

**Összesített bizonyítottsági fok: feltételes.** A 20 pontból többnél két
forrásréteg vagy pontos mérés támasztja alá az összevetést, de több
elfogadási pont renderelt/kattintásos próbát kér, négy eredeti működés pedig
nyitott. Ezért az egész köteg nem nevezhető megerősítettnek. A #3998 fő
exportútja és a #4534 parancsútja a két független út egyezése miatt
megerősített; a forráskódot vagy eredeti screenshotot egyedül felhasználó
állítások feltételesek.

**A két független út:**

- **A, #3998:** utasításszintű olvasat a 300 pixeles feltételről, resampler
  módjáról és JPEG-minőségről (`0x009ece70`, `0x009ecfb8`, `0x009ecdd2`).
- **B, #3998:** 186 export méret- és JPEG-mérése. A mért normál exportút az
  utasításolvasattal egyezik; a túlméretes EXIF végső ága ettől külön
  eltérés.
- **A, #4534:** a menüépítő és parancstábla `ID_PICTURE_SPLITALBUMHERE`
  parancs-hozzárendelése (`0x00730790`, `0x005cb990`).
- **B, #4534:** a `0x005e8570` utasításszintű kezelőolvasata és a mai
  `Main.qml`/`fileops_controller.py` tartománykezelése. A mozgatott
  képtartomány egyezik; futásidejű adatmozgatás nincs mérve.

**Cáfoló kísérlet:** megpróbáltam cáfolni azt az állítást, hogy a nyomtatási
képernyőkép önmagában bizonyítja az eredeti alapméreteket. Az eredeti
`Preferences\\PrintSize0`-`PrintSize4` tárolt értékei felülírják az alapot,
tehát a felvétel mentett állapotot is mutathat. A cáfolat sikeres a
képernyőképre, mint alapérték-bizonyítékra; az alapérték szabályát ettől
függetlenül a `0x006e5ab0` területi ág és a PicasaPy területi alapérték-útja
támasztja alá. A következtetést ezért a metrikus terület és mentett felülírás
hiánya esetére szűkítettem.

## Nyitott

- #4440: `Colab-felvétel kell: mentés, visszaállítás és fotóművelet sikeres és hibás lezárása, a látható eredménnyel.`
- #4482: `Colab-felvétel kell: eredeti mappa átnevezése, már létező név kipróbálása, a mappafa és az útvonal rögzítése.`
- #4542: `Colab-felvétel kell: azonos kép kiegyenesítés előtt és után, vörösszem-panellel és a figyelmeztetés láthatóságával.`
- #4544: `Colab-felvétel kell: azonos bemenet és retusáló vonás eredeti előtte-utána képével és kimeneti fájljával.`
- #4358, #4377, #4385, #4456, #4488, #4550, #4551: mai renderelt PicasaPy-képek és a megnevezett eredeti referenciák képpontos összevetése.
- #4313: a korábbi magyar katalógus és az eredeti 40 nyelvi forrás soronkénti összevetése, valamint Qt-futásidejű/körbejárási próba.
- #4320, #4531, #4534, #4539, #4557: jegyben kért kattintásos tesztek.

## Javasolt jegytörzs-bővítés

### #3998 - az eltérő végső ág rögzítése

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A >300 pixeles JPEG EXIF-bélyegképe 160 pixeles keretben, Lanczos-3 móddal és 85-ös minőséggel készül; ha az EXIF-blokk 10-es minőségen sem fér el, a teljes EXIF kiesik. Forrás: `0x009ece70`, `0x009ecfb8`, `0x009ecdd2`; 186 export mérése. | A fő út egyezik; a túlméretes EXIF végső ágában a bélyegkép marad el, a többi EXIF megmarad. | A ritka végső ág legyen külön tudatos eltérésként elfogadva, vagy készüljön fejlesztői jegy annak egyeztetésére. |

**Kész, ha:** a fő út négy kért jellemzője megmarad, a kivételes végső ág
pedig kifejezett termékdöntést kap.

### #4314 - az indulási nyelvfelajánlás paritása

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Hiányzó `ytHLocal::lang` és az eredeti 11 támogatott Windows-rendszernyelv esetén angol `Yes`/`No` promptot mutat; a `lang` és `langchange` kulcsot írja. Forrás: `0x004060b0`, `0x00c7f2c8`, `picasa-fo-ablak-elrendezes.md` §G. | 39 nem angol katalógusnál első indulási felajánlás, PicasaPy-szöveg és `general/language`/`general/language_pending` tárolás. | Ha az eredeti paritás a cél, a nyelvi kaput, promptot és tárolást a fenti forrás szerint kell módosítani. |

**Kész, ha:** az eredeti 11 nyelvi feltétel, a prompt szövege és gombjai,
valamint a tárolási kulcsok igazoltan egyeznek.

### #4550 - a jegy premisszájának javítása

Az eredeti példa sora statikus. A jegy „élő példa” követelményét javítsa
„statikus Példa sor” kérésre; a törlőgomb a legördülő mellett maradjon. A
lista szakaszcímét ne írja elő eredetinek forrásbizonyíték nélkül.

## Új kutatási jegyjavaslatok

Nincs külön új jegyjavaslat. A hiányzó eredeti mérések a #4440, #4482, #4542
és #4544 meglévő jegyeihez tartoznak.

## Módosított fájlok

- `docs/specs/forras-audit-5186-2.md` - az eredeti forrás, mai kód, ítélet,
  teendő és elfogadási pontok a húsz jegyhez.
- `docs/specs/00-index.md` - hivatkozás az új auditlapra.
- `.codex-jelentes.md` - összesítő táblázat és a következő mérések listája.
