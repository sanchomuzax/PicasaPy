# Forrás nélküli jegyek összevetése, 1. köteg (#5455)

A húsz jegyet a Picasa 3.9.141.259 eredeti binárisával, erőforrásaival, Colab-felvételeivel és a jelenlegi PicasaPy forrással vetettem össze. A bináris verzióját a `VERSIONINFO` adja: bináris (fájl `0x9a88f8`). A GitHub-jegy nem volt elérhető; a jegyszöveget a munkakérés és a helyi munkacsomag adta. A jegy állítását önmagában nem tekintettem bizonyítéknak.

Az ítélet EGYEZIK, ha a forrás és a jelenlegi megvalósítás egyezik; ELTÉR, ha a mai kimenetben marad mérhető különbség vagy a PicasaPy szándékosan más formátumot használ; NEM DÖNTHETŐ EL, ha az eredeti viselkedéshez nincs megfelelő mérés. A nyitott esetek miatt a köteg bizonyítottsága feltételes.

## Összesítő

| Jegy | Ítélet | Eredeti forrás | Teendő |
|---|---|---|---|
| #1721 | ELTÉR | `album-sorrend.md` 2.1-2.6 és 3.; `wordhash.dat`; `0x00784100` | Válassza külön az eredeti formátum importját és a PicasaPy `priority=` kiterjesztését. |
| #3123 | EGYEZIK | `editpanel.tre`:21-33,1038-1056; `respack.yt` | Az állítás a kiegyenesítés kép fölötti sávjára igaz. |
| #3166 | EGYEZIK | eredeti golden-exportok; `chain_geometry.py` mérési táblája | A forrás-kimenet leképezés már megvan. |
| #3173 | EGYEZIK | `album.fen`; `picasa-fen-dialogs.md` 3.2 | Az album tulajdonságai és leírása szerkeszthető. |
| #3234 | EGYEZIK | `editpanel.tre`:869,962,1038-1052 | Ne helyezze át a retusáló ecsetet; a sáv a kiegyenesítésé. |
| #3263 | NEM DÖNTHETŐ EL | `editpanel/tabpanel1`: 277 px; eredeti örökölt-effektek fül NINCS MEG | A natív fülparitás nem mérhető, a saját fülre a jelenlegi magasságkorlát érvényes. |
| #3320 | EGYEZIK | `editpanel.tre`; `szerkeszto-panel-meretek.md` | A négy eszköz gombpárja a saját panelben van. |
| #3408 | EGYEZIK | `collagepanel.tre`; eredeti szövegleltár | A mai QML angol súgói az eredeti szöveget használják. |
| #3410 | EGYEZIK | `collagepaneltext.tre`; eredeti szövegleltár | A két súgószöveg javítva van. |
| #3420 | ELTÉR | `filterdesc.xml`:751-755; három Picasa-export; golden-mérés | A jegyben jelzett régi ΔE eltérés a mai méréssel nem igazolódik; a mai átlag 0,12-0,13 ΔE. |
| #3448 | EGYEZIK | Colab `job-190`, 13. kép | Az eredeti menüben a nem érvényes sorok hiányoznak. |
| #3537 | EGYEZIK | Colab EN 01, File menü | A mai letiltott menücímke szürke. |
| #3594 | NEM DÖNTHETŐ EL | `publish.tre`, `publish_text.tre`; induló pipákról NINCS MEG | Colabban mérje meg a még nem mentett mappák induló pipáit. |
| #3639 | EGYEZIK | `picasa-hu-terminology.md`; eredeti magyar erőforrás | A feliratok a saját Qt fordítási kontextusukban fordulnak. |
| #3661 | NEM DÖNTHETŐ EL | Colab `job-190`: 584 × 345 px; 480 px-es eredeti állapot NINCS MEG | Az eredeti rögzített ablaknak nincs megfelelő 480 px-es állapota. |
| #3663 | EGYEZIK | Colab EN 33-35; `editpanel.tre`:964-994,1160-1201; `0x00569af0` | A jelenlegi kettős nézet kódjában nincs további eltérés. |
| #3709 | EGYEZIK | `respack.yt`; `picasa-fo-ablak-elrendezes.md` | A sín 3 képpontot hagy a 127 px-es foglalat két végén; a nagyító keret nélküli. |
| #3729 | EGYEZIK | `respack.yt`; `scaleslider.tre` | A sín 9 px-es, a fogantyú 16 × 22 px. |
| #3756 | NEM DÖNTHETŐ EL STATIKUSAN | Colab EN 33-35; jelenlegi `PhotoViewer.qml` | A jelvény fókuszkövetése igazolt; az eredeti feliratsáv-kép hozzárendelése a felvételeken nem látható. |
| #3826 | EGYEZIK | bináris `0x008f86c8`, `0x008f86d1`; `filterdesc-registry.md` | A csúszka tartománya és alapértéke a natív paramétert követi. |

## Tételek

### #1721 - Kézi sorrend

**Eredeti:** a kézi sorrend az album vagy mappa rendezett képlistájában él; a lista a `wordhash.dat`-ban tárolódik. Az `album-sorrend.md` 2.1-2.3 szakasza diszasszemblálással követi a lista olvasó/író útját és a húzás kezelőjét (`0x00784100`); a 2.6 szakasz három valódi adatbázis-készleten dekódolja a listákat. A 2.5 szakasz a lista sorrendjét elválasztja a 11-es prioritású rendezéstől. A jegyszöveg `albums_0.db` állítása nem igazolódik; a dokumentált bizonyíték `wordhash.dat`-ra mutat. A külön bináris ellenőrzés a `0x00415790` konstruktorban az `albums.db` és az `albumdata` külön regisztrációját mutatta, de a sorrendvektort és annak rekordmezőjét nem fejtette vissza; ez nem újabb pozitív bizonyíték a lista tartalmára.

**Nálunk:** a `src/picasapy/ini/priority.py` `priority=` értéket olvas és ír a kép `.picasa.ini` szakaszába. A `folder_photo_sort_controller.py` és a `ThumbDelegate.qml` kezeli a mappán belüli áthúzást, a tartós újrasorrendezést és a visszaolvasást; a rendezés menüben választható.

**Ítélet:** ELTÉR. A PicasaPy funkció elkészült, de tárolási formátuma tudatos saját kiterjesztés.

**Teendő:** A jegy nevezze meg a `priority=` tárolást PicasaPy-kiterjesztésként; a `wordhash.dat` sorrend importálása külön, még bizonyítandó fejlesztési kérdés.

### #3123 - Alkalmaz/Mégse a kép fölött

**Eredeti:** az `editpanel/tool_container` szülője az `editpanel/preview`, ezért a kiegyenesítés sávja a kép fölött lebeg. A `respack.yt` szerint a gombok 82 × 28 px-esek, sötét áttetsző háttérrel és fehér felirattal. Forrás: `szerkeszto-panel-meretek.md`, „Az Alkalmaz/Mégse a KÉP FÖLÖTT lebeg” szakasz; `editpanel.tre`:21-33,1038-1056.

**Nálunk:** az `EditorToolBar.qml` a `tilt` eszközhöz jeleníti meg a kép fölötti sávot; a sötét rajz és a fehér felirat ehhez kötött.

**Ítélet:** EGYEZIK a kiegyenesítés eszközén. A sáv nem tartozik a négy további eszközhöz.

**Teendő:** A jegyben a sávot nevezze a kiegyenesítés Alkalmaz/Mégse felületének.

### #3166 - Forrás-kimenet leképezés keretek után

**Eredeti:** a golden-exportok mutatják, hogy a keret-effektek növelhetik, csökkenthetik, eltolhatják és forgathatják a képet. A `filterdesc-registry.md` #3166 lelete és a `chain_geometry.py` mérési táblája rögzíti a Border, MuseumMatte, DropShadow, Polaroid, Cinemascope és RoundedEdges különböző geometriáját.

**Nálunk:** a `src/picasapy/render/chain_geometry.py` effektenként számít forrás-kimenet affin leképezést. A Polaroid forgatása, a Cinemascope vágása és a méretet nem változtató effektek kezelése külön ágban szerepel.

**Ítélet:** EGYEZIK a leképezés elvében; a kód nem általános, szimmetrikus margót feltételez.

**Teendő:** A kutatási jegy fejlesztési hiányként ne ismételje meg a már megvalósított leképezést.

### #3173 - Albumleírás szerkesztése

**Eredeti:** az `album.fen` az album tulajdonságai között név-, dátum-, zene-, hely- és leírásmezőt definiál. A leírás mező neve `caption`, felirata `Description (optional)`. Forrás: `picasa-fen-dialogs.md` 3.2.

**Nálunk:** a `FolderPropertiesDialog.qml` album-módban kezeli a nevet, dátumot, helyet, leírást és zenét; a `FolderPane.qml` átadja az adatokat, a mentést a `photo_ops_controller.py` `editAlbumProperties` útja végzi. Az album menütétele valódi párbeszédet nyit.

**Ítélet:** EGYEZIK az album tulajdonságai szerkesztésében.

**Teendő:** A jegyben a korábbi hiány helyett rögzítse, hogy az album leírása már szerkeszthető.

### #3234 - A retusáló ecset csúszkájának helye

**Eredeti:** a `tool_slider_container` a `tool_container` gyereke a kiegyenesítési átfedésben (`editpanel.tre`:1038-1052). A retusáló ecset csúszkája külön elem: `editpanel/brushslider_container` szülője `editpanel/retouch_well` (:869), kezelője a `brushslider/scaleslider` (:962).

**Nálunk:** az `EditorToolBar.qml` csak tool === `tilt` esetén jelenít meg csúszkát; a retusáló ecset mérete az `EditorRetouchPanel.qml` panelben van.

**Ítélet:** EGYEZIK. A jegy címe tévesen rendeli a retusáló eszközhöz a kiegyenesítési sáv csúszkáját.

**Teendő:** A jegy szövegét helyesbítse; a retusáló ecsetet ne helyezze át a kép fölötti sávba.

### #3263 - Örökölt effektek fül magassága

**Eredeti:** az eredeti `editpanel/tabpanel1` mért magassága 277 px (`ui-audit-editor.md` 2.9). Az eredeti felületnek nincs örökölt-effektek füle; natív vizuális párja NINCS MEG.

**Nálunk:** az EditorLegacyTab.qml PicasaPy-kiegészítés. A bevezető legfeljebb két soros, a rács görgethető, a magasságszámítás a natív 277 px-es panelméretet használja.

**Ítélet:** NEM DÖNTHETŐ EL natív paritásként; a saját kiegészítés platformfüggetlen korlátozásának kódja jelen van.

**Teendő:** A 277 px-es korlátot platformhiba-javításként kezelje; natív egyezést nem lehet nem létező eredeti füllel mérni.

### #3320 - A négy eszköz Alkalmaz/Mégse párja

**Eredeti:** a vágás, retusálás és vörösszem gombpárja saját `*_well` szülő alatt szerepel az `editpanel.tre`-ben; a szöveg párja saját szövegpanelt kap. A `tool_container` a kiegyenesítés átfedése.

**Nálunk:** az `EditorCropPanel.qml`, `EditorRetouchPanel.qml`, `EditorTextPanel.qml` és `EditorRedeyePanel.qml` tartalmazza a saját gombpárokat. Az `EditorToolBar.qml` a kiegyenesítés sávját hagyja meg.

**Ítélet:** EGYEZIK.

**Teendő:** Rögzítse, hogy a négy eszköz gombjai a saját paneljükben vannak; további visszahelyezés nem kell.

### #3408 - Kollázs Beállítások súgói

**Eredeti:** a `collagepanel.tre`, a `ui-leltar.csv` és a `stringres-en-hu.tsv` tartalmazza a hat angol forrásszöveget. Az eredeti alakok között az `Instant Camera`, a `Select the relative width and height of your design` és az ASCII három ponttal végződő `Add Custom Aspect Ratio...` szerepel.

**Nálunk:** a `CollageSettingsTab.qml`, `CollageBorderPicker.qml`, `CollageContextMenus.qml` és `CollageFormatMenu.qml` forrásai az eredeti alakokat használják.

**Ítélet:** EGYEZIK.

**Teendő:** A jegyben hagyja jóvá a mai angol súgóforrásokat; a javítás előtti spec-táblát frissítse külön.

### #3410 - Kollázs Klipek súgói

**Eredeti:** a `collagepaneltext.tre` alapján az eredeti szövegek `Remove selected clips from the tray` és `Get more clips from the Library`; a harmadik érintett súgó `Add selected clips to the collage`.

**Nálunk:** a `CollageClipsTab.qml` mindhárom eredeti angol súgóforrást használja.

**Ítélet:** EGYEZIK.

**Teendő:** A javítás előtti állapotot ne tekintse a mai QML mércéjének.

### #3420 - Polaroid keret

**Eredeti:** a `runtime/filterdesc.xml`:751-755 rögzített fehér keretet, szögparamétert és árnyékbeállítást ír le. A három eredeti Picasa-export a 684-es golden-készletből származik. A bemenet mért mérete 960 × 640 px; az eredeti kimenetek min/alap/max mérete 887 × 1004, 818 × 950, 887 × 1004 px.

**Nálunk:** a `src/picasapy/render/glimmer_frames.py` `apply_polaroid` futása ugyanazokat a kimeneti méreteket adta. A `tools/golden/compare_render.py` `pair` mérése az átlagos ΔE értékeket min/alap/max sorrendben 0,13, 0,12 és 0,13 értékre mérte; mindhárom eset közelítés. A jegyben jelzett nagy színeltérés a mai méréssel nem igazolódott. A `chain_geometry.py` a keret forrás-kimenet leképezését követi.

**Ítélet:** ELTÉR, mert a párosított kimenet nem pixelazonos, noha az átlagos ΔE jóval kisebb a jegy régi értékeinél.

**Teendő:** Cserélje a régi ΔE adatokat a három friss mérésre; a keret geometriáját rögzítse a golden kimenetekkel egyezőnek. A maradék megjelenítési különbség külön cél legyen.

### #3448 - Rejtett helyi menüsorok

**Eredeti:** a Colab `job-190` 13. képe mutatja az eredeti Picasa bélyegkép menüjét. Mappanézetben a nem odaillő album- és személytételek hiányoznak; nincs üres tömb az érvényes sorok között.

**Nálunk:** a `PhotoContextMenu.qml` a rejtett feltételes tételek magasságát nullára állítja.

**Ítélet:** EGYEZIK a `job-190`-en rögzített mappanézetben.

**Teendő:** Rögzítse, hogy a mai kód és az eredeti mappanézet egyezik. Más nézetek regresszióját ez a kutatás nem futtatta.

### #3537 - Letiltott menütételek színe

**Eredeti:** az eredeti angol Picasa Colab EN 01 - `File menu` képén a letiltott menütételek felirata szürke.

**Nálunk:** a `PicasaStyle/MenuItem.qml` és `PicasaMenuItem.qml` letiltott vagy helyőrző címkéje `Theme.textGray` színt használ.

**Ítélet:** EGYEZIK.

**Teendő:** Frissítse a hibaleírást a jelenlegi szürke megjelenésre. A QML-színőrt és új képernyőképet ebben a körben nem futtattam.

### #3594 - Mentéskor mappajelölés és mentetlen képek

**Eredeti:** a `publish.tre` és `publish_text.tre` mentésmódú felülete mentetlen fájlokat, mappakijelölést, `Select All` és `Select None` műveletet nevez meg. A `job-190` 24. képe már mentett állapotot mutat, így a vegyes állapotú mappák induló pipáiról NINCS MEG az eredeti mérés.

**Nálunk:** a `BackupHost.qml`, `PublishPanel.qml` és `FolderPane.qml` mentetlen mappalistát, mappapipát, összes kijelölése/törlése gombot és készlet alapján szűrt fájllistát ad. A jelenlegi pipált mappák üres kezdőértékéből indulnak; az eredeti alapállapot nem dönthető el.

**Ítélet:** NEM DÖNTHETŐ EL az induló pipaállapot egyezésében; a kért vezérlők ma jelen vannak.

**Teendő:** Készüljön eredeti Colab-felvétel vegyesen mentett és mentetlen mappákról, még az első kattintás előtt.

### #3639 - A Tulajdonságok feliratainak fordítási kontextusa

**Eredeti:** az eredeti `Picasa3i18n.dll`-ből kinyert hivatalos magyar szövegek a `picasa-hu-terminology.md` lapban szerepelnek.

**Nálunk:** a `formatting.py` a címkéket üres Qt kontextussal fordítja; a `controller.py` és `PropertiesPanel.qml` ezt a formázott feliratot adja tovább.

**Ítélet:** EGYEZIK a jelenlegi kód fordítási útján.

**Teendő:** A jegy javítását rögzítse lezártként. Az éles .qm-et használó fordítási próbát ebben a kutatási körben nem futtattam.

### #3661 - Beállítások ablak legkisebb szélessége

**Eredeti:** az `options.fen` írja le a beállítási ablak füleit. A Colab `job-190` 26. képe az eredeti 584 × 345 px-es ablakot mutatja. Az eredeti 480 px-es állapot NINCS MEG; a felvétel szerint az eredeti ablak mérete rögzített.

**Nálunk:** az `OptionsDialog.qml` 480 px minimumot, görgethető fülsort és fül-navigációt definiál. A mai forráskód kezeli a magyar címkék túlcsordulását, de a 480 px-es kirajzolt állapotot ebben a körben nem ellenőriztem.

**Ítélet:** NEM DÖNTHETŐ EL eredeti paritásként; az eredeti felületen nincs 480 px-es összevetési állapot.

**Teendő:** A PicasaPy 480 px-es használhatósági feltételét saját kirajzolt méréssel értékelje; az eredeti állapotnak nincs közvetlen párja.

### #3663 - Kettős nézet és kijelölt kép

**Eredeti:** a Colab EN 33-35 rögzíti a kétképes nézetet, a fókuszváltást, a jelvényt és az elrendezést; az `editpanel.tre`:964-994,1160-1201 leírja a jelvény és segédgombok elhelyezését. A vezérlő bináris horgonya `0x00569af0`.

**Nálunk:** a `PhotoViewer.qml` tartalmazza az A/AB/AA váltókat, az oldal fókuszát és a kijelölt sorból működő interakciót. A jelvény az aktív oldalhoz kötődik.

**Ítélet:** EGYEZIK a kettős nézet fő funkcióiban.

**Teendő:** A jegy állítását frissítse a jelenlegi kód szerint. Renderelt összevetési próbát ebben a körben nem futtattam.

### #3709 - Alsó sáv nagyítója és csúszkája

**Eredeti:** a `respack.yt` szerint a `scalecontainer` foglalata 127 px, a rajzolt `sliderbase` 121 px széles; a sín középen, kétoldalt 3 px behúzással áll. A `loupehit` és ikon külön keret nélküli rajz.

**Nálunk:** a `TrayBar.qml` 127 px-es foglalatot, 3 px `grooveInset`-et és keret nélküli nagyító ikont ad.

**Ítélet:** EGYEZIK. A jegy címe megfordította az eredeti állapotot: van behúzás, a nagyító keret nélküli.

**Teendő:** Frissítse a jegy törzsét a mért erőforrás geometriájára; további rajzi változtatást ne kérjen.

### #3729 - Alsó sáv csúszkája és fogantyúja

**Eredeti:** a `respack.yt` `scaleslider/sliderbase` és `thumb` rétegei, valamint a `scaleslider.tre` adja a sín és fogantyú rajzát. A képernyőmérés a sínt 9 képpontosnak, a fogantyút 16 × 22 képpontosnak méri.

**Nálunk:** az `EditorSlider.qml` scaleslider ága ugyanezt a méretet használja; a `TrayBar.qml` a bélyegképméret csúszkájához ezt a komponenst köti.

**Ítélet:** EGYEZIK.

**Teendő:** Zárja le a jegyet a jelenlegi méretek alapján. A regressziós és renderelt próbák nem futottak ebben a kutatási körben.

### #3756 - Jelvény és feliratsáv kettős nézetben

**Eredeti:** a Colab EN 33-35 felvételei (job #58) bal és jobb fókuszt is rögzítenek; a `ui-audit-editor.md` 3/b kiméri, hogy a „Selected” jelvény a fókuszált kép mellett, a margóban áll. Mindhárom képen a feliratsáv üres „Make a caption!” helyőrzőt mutat, ezért a kép-hozzárendelést nem bizonyítják.

**Bináris út:** az index `editpanel/previewclip`, `editpanel/previewclip2` és `editpanel/selection_label` sztring-xrefjei a `0x00569720` (967 bájt) és `0x00569af0` (1434 bájt) rutinokat jelölik; az utóbbi hívói `0x00569720`, `0x0056a160` és `0x0056a680`. Ez a fókuszjelvény útja. Az `editpanel/caption` erőforrás külön megjelenik a `0x00566a70` (2908 bájt) és `0x005f8ac0` (310 bájt) rutinokban; `0x005683a0` a `CaptionState` és a `previewclip2` sztringet is használja, és meghívja `0x00566a70`-et. A xref-lánc azonosítja a kezelőterületet, de nem mondja meg, hogy bal vagy jobb fókusznál melyik fotó feliratát olvassa. A korábbi Ghidra-fájlokban ezekhez csak hívóhelylista van, a függvények dekompilált kódja nincs meg.

**Nálunk:** a `PhotoViewer.qml:882-886` bal fókusznál a `currentIndex`, jobb fókusznál a másik sort választja; a feliratsáv a `:4813-4846` sorokban ezt a sort olvassa és írja. A jelvény aktuális elhelyező útja a `:4237-4298` tartományban van.

**Ítélet: NYITOTT.** A fókuszjelvény eredeti útja és a mai feliratkötés külön-külön azonosított. Az eredeti felirat-hozzárendelés futás közbeni képe nincs meg, ezért a két megvalósítás egyezése vagy eltérése nem állítható.

**Teendő:** két eltérő, nem üres Picasa-feliratú képpel készítsen Colab `ui_capture` felvételt bal, majd jobb fókusznál; ugyanezt rögzítse PicasaPy-ban valódi kattintásokkal, majd egymás mellé tett képkockával hasonlítsa össze a feliratsávot. A függvényadatút lezárásához Ghidra-dekompiláció kell `0x00566a70` és `0x005f8ac0` címekre. A jelen munkamenetben nincs Colab/PicasaPy felület, ezért mérési eredmény és job-szám **NINCS MEG**.

**Kész, ha (#5975):**

- ✅ A fókuszjelvény bináris rutinjai és a feliratvezérlő xref-útja azonosított.
- ⛔ Eredeti, két eltérő nem üres feliratú kép Colab-felvétele: **NINCS MEG**.
- ⛔ PicasaPy valódi kattintásos párja: **NINCS MEG**.
- ⛔ Képkocka-összevetés és egyező/eltérő ítélet: **NINCS MEG**.

### #3826 - Fókuszos FF méretcsúszka

**Eredeti:** a bináris paraméter-leírás (`0x008f86c8`, `0x008f86d1`) és a `filterdesc-registry.md` szerint a `radsat` `Size` értéke -1 és 1 között jár, alapértéke 0.

**Nálunk:** a `src/picasapy/app/effect_params.py` `radsat` paramétere ugyanezt a -1 és 1 tartományt, 0 alapértéket adja meg. Az ini olvasóút a `filters-decoded.md` 2485-2559 szakaszában szerepel.

**Ítélet:** EGYEZIK.

**Teendő:** A tartományt érintő javítást tekintse megvalósítottnak. A szélső állásokat és régi `.picasa.ini` fájlokat ellenőrző próbák nem futottak.

## A két független út és a cáfoló kísérlet

**A út:** az eredeti Picasa bináris pozitív címei és adatai, .fen/.tre erőforrásai, `respack.yt` rétegei, runtime `filterdesc.xml` és Colab-felvételei. Negatív bináris-index találatból nem következtettem hiányra.

**B út:** a mai Python/QML implementáció közvetlen forrásolvasása. A #3420 esetén további, külön út az eredeti export és a közvetlen jelenlegi renderer-kimenet páros golden-mérése. Az A és B út az eredeti erőforrást, illetve a külön implementációt hasonlítja.

**#1721 külön:** az `album-sorrend.md` 2.1-2.3 bináris diszasszemblálása az író/olvasó útját és a húzás lista-módosítását követi; a 2.6 ettől függetlenül valódi `wordhash.dat` fájlokat dekódol. Ezek egyeznek abban, hogy a sorrend lista, nem kulccsal számolt nézetmód. A jelen kör specifikációtól független bináris próbája a `0x00415790` konstruktorban az adatbázis-regisztrációt erősítette meg, a sorrendvektort nem. Emiatt ezt nem számítottam további megerősítő útnak.

**Cáfoló kísérlet:** a #3234 állítását próbáltam cáfolni, miszerint a retusáló ecsetméret a kép fölötti sávhoz tartozik. Az `editpanel.tre`-ben ellenőriztem a `brushslider_container` szülőjét és a `toolslider` szekcióját, majd ugyanezt az elem/szülő-hozzárendelést a mai `EditorRetouchPanel.qml` és `EditorToolBar.qml` forrásában. Az ecset a `retouch_well` gyereke, a `toolslider` a kiegyenesítési átfedésé, a mai sávcsúszka pedig `tilt` módhoz kötött. A cáfolót mindkét oldalon azonos szülő- és elem-hozzárendelési mércével ellenőriztem; a jegy feltevése cáfolódott.

## Nyitott kérdések

- NINCS MEG: az eredeti Picasa mentésmódjában a még nem mentett mappák induláskor pipáltak-e. Colab-felvétel kell vegyes mappákkal, a panel megnyitása után, kattintás előtt.
- NINCS MEG: az eredeti Picasa 480 px-es Options ablaka. A job-190 felvétele szerint az ablak rögzített méretű, ezért nincs közvetlen összevetési állapot.
- NINCS MEG: a #3263 örökölt-effektek fül eredeti vizuális párja; ez a PicasaPy saját kiegészítése.
- A #3420 golden-összevetés közelítés, nem pixelazonos egyezés. További eltérést külön célként csak megadott mérési küszöb mellett érdemes kezelni.

## Módosított fájlok

- docs/specs/forras-audit-5186-1.md - a húsz tétel eredeti forrása, mai állapota, ítélete és teendője.
- .codex-jelentes.md - összefoglaló, bizonyítékok, elfogadási pontok és következő mérések.
