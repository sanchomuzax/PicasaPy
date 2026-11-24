# A szerkesztő Alapjavítások eszközeinek folyamata (#7327)

**Státusz: nyitott, feltételes.** Az eredeti menü- és eszközutak több részlete a binárisból azonosítható, a jelenlegi PicasaPy útjai forrásból követhetők, és a #798, #807-814 mérések részfolyamatokat rögzítenek. A `Ctrl+Shift+E` szerkesztői használatánál igazolt eltérés van: az eredeti működést a bináris és a #810 kép mutatja, míg a PicasaPy kötése csak könyvtárnézetben él. A `job-813` új képen lezárja a Crop Apply/Undo/Redo sort; a `job-814` lezárja az alkalmazás nélküli Reset/Cancel sort. A bináris alapján egymást közvetlenül követő Crop Apply esetén az eredeti a lánc végén álló `crop64` rekordot frissíti, míg a PicasaPy mindig új rekordot fűz hozzá; erre fejlesztői javaslat került a lapra. A `job-813` második, „már vágott” képes szakasza nem igazolta az elővágott induló állapotot; az ismételt Apply utáni látható Undo/Redo állapotot a `job-821` helyes, azonos munkamenetű újrafelvétele méri: egy Undo mindkét vágást visszaveszi, a Redo a második téglalapot hozza vissza (lezárt, a bináris-olvasattal egyező). A `job-836`..`job-839` (9-12. feladat) lezárta a Kiegyenesítés, a Retusálás és a Szöveg panel felépítését és működését, valamint a Vörösszem tilt-figyelmeztetésének feltételét. A `job-917`..`job-925` és `job-939`..`job-943` után a `job-949` és `job-950` lezárta a Retusálás Mégse működését függő kijelöléssel és anélkül, a semleges panelkattintást, az újranyitáskori ecsetméret megőrzését (W jegytörzs), valamint a Szöveg forgatásának teljes szögtérképét és geometriáját (az L jegytörzs véglegesítve). A 19 pontból 15 lezárt, 1 blokkolt (Vörösszem, vörösszemes képre vár), 3 hatókörön kívül.

## Hatókör és bizonyítékmérce

A jegy kilenc Alapjavítások műveletet kér: vágás, kiegyenesítés, vörösszem, retusálás, szöveg, Jó napom van, automatikus kontraszt, automatikus szín és a külön Derítőfény-csúszka. A belépési pontok, a panel, alkalmazás, megszakítás, visszavonás, mentés, a fájlokra és a felületre gyakorolt hatás, illetve a hibák ugyanennek a folyamatnak a részei.

Minden átadott eredeti adat `bináris (0x...)`, `mérés (job-...)` vagy `NINCS MEG` jelölésű. A PicasaPy-hivatkozás forráskódot dokumentál, futásidejű PicasaPy-mérést nem. Eltérést csak akkor állítok, ha a kód létezése mellett az eredeti, felhasználó számára látható viselkedés is bizonyított.

A `Nálunk` oszlopban a QML-fájlok rövid útjának prefixe `src/picasapy/app/qml/PicasaPy/`, a Python controller-fájloké `src/picasapy/app/`. A specifikációk rövid útjai a `docs/specs/` alatt vannak.

## Belépési pontok és kijelölés

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A szerkesztő első, Gyakori javítások füle tartalmazza a `crop`, `horizonadjust`, `redeye`, `enhance`, `autolighting`, `autocolor`, `retouch` és `edittext` vezérlőket. A mód 2-es belépői közt szerepel a crop `0x005efa30`, red-eye `0x005f30e0`, retouch `0x005f7140`, text `0x005f5b30` (`ui-audit-editor.md:1892-1903,2467-2469`). A menüben az Automatikus kontraszt `0x9d49`, Automatikus szín `0x9d48`, Jó napom van `0x9d5e`; a menüépítő `0x00559150`, a közös batch-alkalmazó út `0x005fe370` (`picasa-menu-parancsok-viselkedes.md:1535-1590`). A keymap-táblában szereplő `Ctrl+Shift+E` tényleges szerkesztői indítását a bináris `0x005e638b` és a `mérés (job-810)` is alátámasztja. | A csempék a `EditorTabCommonFixes.qml:87-200` fájlban vannak. A Kép menü batch tételei: `PicasaPictureMenu.qml:44-59,93-98`; a kódjuk például `onTriggered: bar.batchApplyEffectRequested("autolight")`. A mai `Ctrl+Shift+E` kötés a `MainKeyboardShortcuts.qml:166-174` sorokon van, de a `MainWindowCommands.qml:171-172` könyvtárnézeti kapuja letiltja nézőben. | A `job-807` a Kép menü batch tételeit nulla, egy és két kijelölt képnél mutatja; a `job-810` szerkesztői kép megerősíti az eredeti shortcut hatását. A PicasaPy kódja alapján a szerkesztői shortcut hiányzik. `NINCS MEG`: a toolbar súgója, valamint a könyvtári shortcut utáni fájl/ini-hatás; ezekre a képek nem adnak választ. |
| A batch Auto Red Eye külön út: `0x00559150` menütétel `0x9df1` → diszpécser `0x005ccb36` → kijelöléskeret `0x00602100` → kezelő `0x005f39d0`. A kezelő a kijelölést és az `editpanel/preview` állapotát vizsgálja, `Applying RedEye...` állapotjelzést ad, és a mozgóképekhez tartozó kihagyásról szöveget tartalmaz (`picasa-menu-parancsok-viselkedes.md:1550,1637-1654`; bináris `0x005f39d0`). | A batch Auto Red Eye sor `PicasaPictureMenu.qml:93-98`, szó szerinti bekötése: `onTriggered: bar.batchApplyEffectRequested("redeye")`. A feldolgozó a `batch_effect_controller.py:130-156,340-378` sorokon képenként módosítja a `filters` láncot, mappánként írja az ini-t, indexet szinkronizál és folyamatjelzést küld. | A belső utak eltérnek: az eredeti előnézeti kijelöléskeretbe delegál, a mai batch vezérlő `redeye` láncelemet ír. A felhasználói kimenet, hiba, kijelölés és rács és oldalsáv végállapotának eltérése nincs mérve; ez önmagában nem igazolt paritáshiba és nem fejlesztési teendő. |
| A billentyűleltár a `Ctrl+Shift+E`-t Jó napom van műveletként azonosítja. A tényleges editor-hatást a `mérés (job-810)` mutatja: a csempe elszürkül és megjelenik az Undo felirat. A többi eszközre a leltár nem nevez meg külön eszközbillentyűt. | A mai Alapjavítások csempéi a szerkesztő panelhez kötődnek; crop, tilt, redeye, retouch és text kattintása `PhotoViewerEditorPanel.qml:95-109` alatt eszközmódot nyit. A `Ctrl+Shift+E` egyetlen kötése a könyvtári `batchEnhanceShortcut` (`MainKeyboardShortcuts.qml:166-174`), a `viewerOpen` állapotot kizáró kapuval (`MainWindowCommands.qml:171-172`). | **Igazolt eltérés:** az eredeti szerkesztőben a `Ctrl+Shift+E` a Jó napom van eszközt aktiválja, a mai egyetlen binding nézőben letiltott. A fejlesztési javaslatot lásd a „Mérési eredmény (Colab)” szakaszban. A többi eredeti gyorsbillentyű és helyi menü útja `NINCS MEG`. |

## Eszközönkénti folyamat

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Vágás.** Eredeti eszközbelépő `0x005efa30`; az Apply út `FUN_005ecd60` (`0x005ece75`: `editpanel/cropapply`; `0x005ecece`: `FUN_005d4b60`), majd a Crop-kijelölés ága `FUN_006b0200` → `FUN_006b4300` (`0x006b0302`). A `FUN_006b4300` a lista utolsó rekordját vizsgálja: ha `crop64`, a négy koordinátát a meglévő rekordba írja (`0x006b43bd`-`0x006b447b`); egyébként új rekordot ad hozzá (`0x006b452e`-`0x006b4662`). Az Undo/Redo felület a `filters`/`redo` listát tölti (`FUN_006ad530`, `0x006ad55f`-`0x006ad58c`). Új képen a Crop Apply/Undo/Redo látható állapotát a `job-813` méri: `kepernyo__14`: „Undo Crop”, 415×187; `__16`: 1024×256 és „Redo Crop”; `__18`: ismét 415×187. A Reset/új kijelölés/Cancel sort a `job-814` `__12`, `__14`, `__16`, `__18` képei mutatják; a záró ini-ben nincs crop. | A csempe: `EditorTabCommonFixes.qml:91-99`, a panel és figyelmeztetés: `EditorCropPanel.qml:54-85`, gombok: `EditorCropPanel.qml:356-402`. A gombos Apply útja `PhotoViewerGeometryActions.qml:384-394`, a controller `edit_controller_crop_mixin.py:92-124`; az új réteg hozzáfűzése `edit/session_core.py:80-124`. Reset/Cancel: `PhotoViewerEditorPanel.qml:167-188`. | **Egyező, lezárt rész:** üres láncból végzett Crop Apply után az eredetiben a kép/Undo/Redo állapot vált; az alkalmazás nélküli Reset lenullázza a kijelölést, majd Cancel visszatér a teljes képhez. **Igazolt eltérés:** az eredeti Apply a lánc végén álló `crop64` rekordot frissíti, ha ilyen a farok, különben új rekordot fűz hozzá; a PicasaPy az 1.0.171 előtt minden megváltozott Cropnál hozzáfűzött (a pontos forrásidézet és jegytörzs lent; a #7367 javította). **A futtatott mérés:** a `job-813 kepernyo__20` a `color_patches.jpg`-nél „Crop” csempét és letiltott Undo/Redo gombokat mutatott, így az elővágott induló állapot ott nem igazolt. A helyes, azonos képen és munkamenetben végzett újrafelvétel a `job-821` (`gray_ramp.jpg`): az első Apply után „Recrop” és aktív „Undo Crop” (`__14`), a második Apply után ugyanez 415×188-ra (`__20`), **egyetlen** Undo után vágatlan kép, „Crop” csempe, letiltott Undo és „Redo Crop” (`__22`), a Redo a második vágást hozza vissza (`__24`, a képterület képpontra azonos a `__20`-szal). A záró ini egyetlen `crop64` elemet tartalmaz a `redo=` sorban, `filters=` nincs. **Nálunk (1.0.171 óta, #7367):** a lánc végi `crop64` helyben frissül (`recrop.py:25-39`, `edit_controller_crop_mixin.py:111-123`), a látható Undo/Redo-lánc egyezik; a „Recrop” csempefelirat hiányzik (#7376); a `redo=` az eredetiben újranyitáskor eldobott, átmeneti sor, a látható viselkedés egyezik (`job-829`..`job-832`) (lásd „Job-821 nyomán”). |
| **Kiegyenesítés.** Eredeti vezérlőneve `horizonadjust`; a `ui-audit-editor.md` a `job-70` 4. képéből az eszköz közbeni szürke panelállapotot dokumentálja (`:653`). A kiegyenesítés és a vörösszem-javítás kölcsönhatására vonatkozó red-eye figyelmeztetést a `0x005f30e0` út kezeli, lásd lent. | Csempe: `EditorTabCommonFixes.qml:100-112`; csúszka-előnézet és mentés: `edit_controller_effects_finetune_mixin.py:74-98`; a mód belépése és a korábbi paraméter visszatöltése: `PhotoViewerEditorPanel.qml:95-107`. | **Lezárva a `job-836`-tal** (lásd „Job-836..839”): az alapállás a sáv közepe, a húzás élő előnézetet ad, a Cancel pixelre az eredeti képet adja és a csúszkát nem őrzi meg, az Apply „Undo Straighten”-t ad, az Undo és a Redo a képet és a feliratot váltja; az ini `filters=tilt=1,0.391249,0.000000;`. A sáv, a rács és az elhalványítás kódolvasás szerint egyezik; a felirat angol alakja eltér (F jegytörzs). **Blokkolt (`7327-9`, `7327-9b`):** a Mentés megerősítése utáni fájl/ini/index, az újranyitás Apply után, a Crop-figyelmeztetés alakja és az `Escape` hatása. |
| **Vörösszem.** A panel elemei és eredeti szövegei már dokumentáltak: Auto, Preview, Reset, Apply, Cancel, találati/üres/Reset utáni szövegek (`ui-audit-editor.md:1186-1263`). A koordináták a szerkesztés idején élnek; az eredeti vörösszem-javítás a mentett képpontokba kerül és nem nyerhető vissza a réteg ismételt alkalmazásával (`ui-audit-editor.md:1230-1257`; `IDS_CONFIRM_UNDO_REDEYE`, bináris `0x00752ae0`). | Csempe: `EditorTabCommonFixes.qml:114-125`; panel: `EditorRedeyePanel.qml`; Apply/Cancel kötése: `PhotoViewerEditorPanel.qml:211-230`; puffer, egyedi keret-Undo, Reset és Apply: `edit_controller_redeye_mixin.py:298-465`. | **Igazolt, látható eltérés (A jegytörzs):** az eredeti a kiegyenesítés-figyelmeztetést felugró „Info” ablakban adja a csempekattintásra (`job-837 __22`), a panel címe „Redeye Repair”, találat nélkül nincs „No red eye was found automatically.” mondat; nálunk a figyelmeztetés a panelben áll (`EditorRedeyePanel.qml:84-96`). A panel alapállapota és a Cancel lezárt. A batch belépő belső útjának eltérése fent szerepel, látható kimeneti eltérés nem bizonyított. **Blokkolt (`7327-10`):** az Apply, az Undo-megerősítés és a mentett fájl, mert a felvétel képén nincs vörösszem (a PicasaTeszt mappában ismert vörösszemes kép nincs). |
| **Retusálás.** Eredeti eszközbelépő `0x005f7140`; a felületi erőforrás `retouchapply`, `retouchcancel`, `retouchoverlay` (`ui-audit-editor.md:2467-2469`). A `job-315` összefoglaló retusált kép mentésekor eredeti-biztonsági másolatot és ini-hatást említ; a nyers ini hiányzik, a `filters` helyéről a job-253 és a bináris spec ellentmond a job-315 leírásának (`paritas-ellenorzes-archiv-1.md:851-883`). | Csempe: `EditorTabCommonFixes.qml:171-183`; panel, ecset és foltgombok: `EditorRetouchPanel.qml:80-187`; Apply/Cancel: `PhotoViewerEditorPanel.qml:193-208`; puffer, helyi Undo/Redo és Apply: `edit_controller_retouch_mixin.py:74-223`. | **Lezárva a `job-838`, `job-917`, `job-918`, `job-939` és `job-949`-cel:** a panel elemei és állapotai, a kétkattintásos folt (első kattintás cél, második forrás), az ecsetméret lineáris leképezése (`R = 100·s·z`), az 1:1 gomb (100%), a Cancel függő kijelölés nélkül azonnal kilép az Alapjavítások fülre, függő kijelölés mellett a kijelölést dobja el, a panel semleges kattintása szintén eldobja a függő kijelölést, újranyitáskor a csúszka és az ecsetméret megmarad; helyi Undo/Redo/Reset, Apply („Undo Retouches”), megerősítő ablak és a záró ini (`filters=retouch=1;`). **Igazolt eltérések:** megerősítő ablak, panelcím és felépítés, ecsetméret-osztó (G jegytörzs), Cancel függő kijelöléssel és panelkattintás (W jegytörzs). |
| **Szöveg.** Eredeti eszközbelépő `0x005f5b30`; a szerkesztő mód váltásakor a `edittextapply`/`edittextcancel` gombok zárják az eszközt (`ui-audit-editor.md:2467`). Az eredeti felirat tárolása és fájlba írása a `picasa-ini-format.md` szöveges rétegről szóló szakaszában szerepel. | Csempe: `EditorTabCommonFixes.qml:185-200`; panel mezői és gombjai: `EditorTextPanel.qml:1-430`; Apply/Cancel: `PhotoViewerEditorPanel.qml:233-248`; a controller az `applyText()` során blokkot módosít vagy új blokkot hoz létre: `edit_controller_text_mixin.py:501-545`. A szöveg külön `text=`/`textactive=` kulcspárja: `edit_controller_save_mixin.py:213-253`. | **Lezárva a `job-839`, `job-919`..`job-921`, `job-941`, `job-942` és `job-950`-nel:** a panel felépítése, képre gépelés, Cancel, Apply, Undo hiánya, Undo Save hatása szövegnél (N jegytörzs), Clear All eszközön belüli piszkozat (M jegytörzs), helyben szerkesztés nem változtat geometriát, a forgatókorong (24 osztás, R = 81) és a forgatás folytonos szögtérképe 15°-os snap zónával (7°, 17,2°, 30,0°, 38,4°), a negyedik mező radián, az y lineáris eltolódása (`dy/rad ≈ -0,115`). **Igazolt eltérések:** közvetlen képre gépelés (E jegytörzs), Clear All (M jegytörzs), Undo Save (N jegytörzs), forgatókorong és geometriaváltozás (L jegytörzs, véglegesítve). |
| **Jó napom van.** Eredeti `editpanel/enhance` vezérlő; könyvtári batch parancs `0x9d5e`, kezelője `0x005cc97b`; a bináris batch minta szerkesztőnyitáskor a megfelelő csempére navigál, könyvtárban a kijelölt képekre alkalmaz (`picasa-menu-parancsok-viselkedes.md:1535-1625`). A `Ctrl+Shift+E` eredeti editor-hatását a bináris `0x005e638b` és a `job-810` méri; egyképes paneles hatásról a `job-812` ad képet. | A csempe: `EditorTabCommonFixes.qml:127-141`. A batch menü: `PicasaPictureMenu.qml:56-59`. Az effektmentés: `edit_controller_effects_mixin.py:72-88`; batch írás és háttérszál: `batch_effect_controller.py:130-156,340-378`. | A szerkesztői gyorsbillentyű hiánya igazolt, lásd a fejlesztői javaslatot lent. `NINCS MEG`: PicasaPy futásképe az eredetihez párosítva, a könyvtári shortcut adat-/fájlhatása, Save utáni index/rács/állapotsor és a teljes kijelölési feltétel. |
| **Automatikus kontraszt és automatikus szín.** Eredeti menüparancsok: Auto Contrast `0x9d49` / kezelő `0x005cc917`; Auto Color `0x9d48` / kezelő `0x005cc949`; a panelvezérlők `editpanel/autolighting` és `editpanel/autocolor` (`picasa-menu-parancsok-viselkedes.md:1535-1590,1610-1632`). A menü a szerkesztőben a csempére visz, könyvtárban a kijelölt képeken batch műveletet indít (`0x00579330`, `0x005fe370`); a batch utáni rácsot a `job-809`, az egyképes Undo/Redo feliratot a `job-812` mutatja. | Csempék: `EditorTabCommonFixes.qml:143-169`; batch parancsok: `PicasaPictureMenu.qml:44-53`; lánc-hozzáfűzés: `edit_controller_effects_mixin.py:72-88`; háttérmunka: `batch_effect_controller.py:340-378`. | A mérések az eredeti látható műveleti állapotot és a kijelölést igazolják. `NINCS MEG`: PicasaPy futásképe, fájl/ini/DB kimenet, Cancel/Save, index/rács/oldalsáv/állapotsor páros összevetése. |
| **Derítőfény.** A szerkesztő bal paneljének csúszkája a mért Picasa UI auditban a Gyakori javítások fül alatt szerepel (`ui-audit-editor.md:294-310`). A `job-812` képe a csúszka mozgatása utáni képernyőt és Undo feliratot rögzíti. Külön eredeti belépési billentyűt vagy batch menüparancsot itt nem azonosítottunk. | Ikon, cím és csúszka: `EditorTabCommonFixes.qml:273-326`; a panel-érték változása a finomhangoló controllerhez fut (`edit_controller_effects_finetune_mixin.py`). | A `job-812` nem adja meg a csúszka pontos koordinátáit, induló értékét vagy mentési következményét. `NINCS MEG`: az eredeti tárolt érték, PicasaPy-val párosított fájlhatás, valamint a teljes UI-utóhatás. |

## Közös Alkalmazás, kilépés, visszavonás és mentés

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Az eredeti szerkesztő módváltáskor a `0x005f8d80` lezáró kapun átmegy. Módosított eszköznél az „Apply changes to the current image?” kérdést adja; az Apply, Discard és Cancel ág különbözik. Cancelnél a fókuszváltás nem történik meg. A `DoNotAskOnEndEditModality` beállítás kérdés nélkül alkalmazást választ (`ui-audit-editor.md:2421-2464`). Ez külön módváltási kérdés, nem az egyes eszközök saját panel-gombja. | PicasaPy eszközmód-váltása: `PhotoViewerEditorPanel.qml:95-109`; eszközönkénti panel Cancel az egyes sorokban; közös Undo/Redo: `edit_controller_history_mixin.py:60-84`. | Az eredeti oldali kapu binárisból ismert, de a teljes kérdés és válaszút PicasaPy-hoz viszonyított minden eszközre kiterjedő futó összevetése `NINCS MEG`. A meglévő UI audit a fókuszváltási esetre ad eredeti bizonyítékot; az Enter/Escape és egyes eszközönkénti kilépés további mérést igényel. |
| Red Eye Undo saját megerősítő szövege jelzi, hogy a kijavított szemek nem állíthatók vissza a javítás ismételt alkalmazásával (`IDS_CONFIRM_UNDO_REDEYE`, `0x00752ae0`). Retouch mentésről részleges mérés a `job-315`. Egyéb eszközök teljes undo/redo és mentési mellékhatásai itt nincsenek végigmérve. | A globális Undo/Redo a korábbi szerkesztési láncot visszaállítja és a `_save()` útján kiírja (`edit_controller_history_mixin.py:60-84`). A lánc, `crop`, `backuphash` ini-frissítése, írási hibák és háttérben futó újrarajzolás: `edit_controller_save_mixin.py:145-210`. A szöveg külön ini-kulcsokon mentődik: `:213-253`. | `NINCS MEG`: az eredeti és mai műveleti lépések pontos megfelelése, az Undo egyes eszközöknél réteg- vagy fájlszintű hatása, mentés utáni eredeti fájl és biztonsági másolat, DB/index, bal panel, rács, kijelölés, háttérmunka és állapotsor közvetlen összevetése. A `job-315` nyers ini- és profilmelléklete nélkül a retus-ini eltérés nem eldönthető. |
| A `0x005f30e0` kód a `filters` lánc beolvasása után a `tilt` tokent összeveti; találatkor az `IDS_WARN_REDEYE_ACCURACY` feliratot jelenítő hívást végzi (`0x005f3370-0x005f3438`). Ugyanitt `redeye.tmp` néven fájlt nyit `CreateFile`-lel `GENERIC_READ|GENERIC_WRITE` és `OPEN_ALWAYS` paraméterrel. Sikertelen nyitáskor a hiba szövege: “Unable to write redeye due to a disk error. The disk may be full or read-only.” (bináris `0x005f30e0`, string xrefek `0x00c984e0-0x00c98550`). A `mérés (job-811)` tilt nélküli és tervezetten `tilt=1,0.18` bemenetű Redeye panelt mutat; egyik képen sincs látható figyelmeztetés. | A mai vörösszem figyelmeztetés feltétele `panel.straightenActive`: `EditorRedeyePanel.qml:81-96`. A mentés előtti írásvédettség-ellenőrzés `edit_controller_save_mixin.py:256-270`; az ini-írás hibája `:186-198`. | **A `tilt` feltétel lezárva a `job-837`-tel:** mentett kiegyenesítés mellett a Vörösszem csempére kattintva az eredeti felugró „Info” ablakot ad (`__22`), tilt nélkül nem (`__10`, az `allapot.json` csak a főablakot sorolja); az ablak szövege az `IDS_WARN_REDEYE_ACCURACY` szövegével betűre egyezik (a „red eye  rectangles” közt két szóköz). A `job-811` ezzel összefér: ott a betöltött ini nem volt igazolva. Az ablak alakja nálunk eltér (A jegytörzs). Az eredeti teljes hibaablak (`redeye.tmp` írási hiba), fájlrendszer-állapot, megszakítás és hálózati hely összevetése `NINCS MEG`. |

## A `0x005f30e0` figyelmeztetés cáfoló vizsgálata

**Feltételes állítás:** a vörösszem figyelmeztetés nem feltétlenül minden eszköznyitáskor jelenik meg. A helyi függvény-diszasszemblálás szerint a `filters` tagokat végigjáró ciklus csak a `tilt` token találatakor jut a figyelmeztetés-híváshoz. A folytató ág találat nélkül a következő láncelemre, illetve a figyelmeztetést elkerülő folytatásra ugrik.

**Cáfoló kísérlet:** megpróbáltam cáfolni azt a lehetséges következtetést, hogy a figyelmeztetés feltétel nélküli, vagyis minden Red Eye nyitásnál megjelenik. A disassembly ellenpélda-ágat mutat a `tilt` nélküli láncra. Az eredeti spec `forras-audit-5186-2.md:28,413-430` korábban a megjelenési feltételt nyitottnak hagyta, ezért ez a viselkedés valódi pontosítás, nem korábbi mérésből másolt állítás.

**A cáfoló ellenőrzése:** a függvény címe, a figyelmeztetés string-xrefje és a lépésenkénti disassembly összeköti a sztringet és az ágat. A keresett címet a meglévő Ghidra-fájlokban is ellenőriztem; ott erre a kérdésre használható teljes, független dekompilált törzset nem találtam. Nincs második, futásidejű eredeti felvétel, ezért a feltételt **nem** emelem megerősítettre. A Colab-próba két azonos képen, egyiken tilt nélkül, másikon kiegyenesítés alkalmazása után rögzítse a vörösszem eszköz megnyitását.

**Colab-kiegészítés:** a `job-811` `kepernyo__11.png` és `kepernyo__19.png` képein nem látszik figyelmeztető ablak. A feladatleírás szerint a második képhez ini-előkészítés adta a `tilt=1,0.18` elemet, de a `allapot.json` nem tartalmaz ini-visszaolvasást. Ez a kép cáfolja azt, hogy a figyelmeztetés minden panelnyitáskor látható, de önmagában nem cáfolja a `tilt` feltételre vonatkozó bináris állítást, mert a betöltött lánc nincs függetlenül igazolva.

**Colab-kiegészítés (`job-837`, lezárja a feltételt):** a Kiegyenesítés alkalmazása után (a záró ini-ben `filters=tilt=1,0.391249,0.000000;`) a Vörösszem csempére kattintva megjelenik az „Info” ablak (`kepernyo__22`, az `allapot.json` ablaklistája: „Info”), Return után a panel nyílik meg (`__24`); a megelőző, tilt nélküli megnyitás (`__10`) nem ad ablakot. A bináris `tilt`-token feltétele és a futásidejű kép tehát egyezik: a feltétel **megerősített**, a figyelmeztetés alakja felugró ablak az OK gombbal, a szövege szó szerint az `IDS_WARN_REDEYE_ACCURACY` szövege. A `job-811` hiányzó ini-igazolása ezzel megoldott, a megismétlése nem kell.

## Független utak és bizonyítottsági fok

**A út:** a Picasa3.exe indexe és célzott függvény-diszasszemblálása, valamint attól független eredeti képernyőmérés. A `Ctrl+Shift+E` esetében a bináris `0x005e638b` útja és a `job-810` szerkesztői képe egyezik. A `0x005f30e0` red-eye `tilt` feltételhez a `job-811` képe nem mutat figyelmeztetést, de a betöltött ini hiányában nem ad cáfoló bizonyítékot.

**B út:** a jelenlegi PicasaPy forrásának teljes `src/picasapy` keresése és a kötés feltételének követése. A `Ctrl+Shift+E`-hez egy bindinget találtam (`MainKeyboardShortcuts.qml:166-174`), a kapu `!hostWindow.viewerOpen` (`MainWindowCommands.qml:171-172`), ezért a mérésen látható eredeti szerkesztői működés nincs bekötve. Ez az út az eredeti bináris útjától függetlenül ugyanarra az eltérésre jut.

**Crop - A út:** a binárisban az `editpanel/cropapply` ág (`FUN_005ecd60`, `0x005ece75`-`0x005ecece`) eljut a panelkezelőhöz (`FUN_005d4b60`). A `cropselection` panel aktív állapotában ez a `FUN_006b0200`-n keresztül meghívja a `FUN_006b4300`-at. Ez a függvény a lánc utolsó elemének nevét a bináris `crop64` literáljához hasonlítja (`0x00c80adc`): egyezéskor a koordinátamezőket írja át (`0x006b4472`-`0x006b447b`), eltéréskor új `crop64` rekordot készít és a lista végéhez adja (`0x006b452e`-`0x006b4662`).

**Crop - B út:** a PicasaPy `applyCrop()`-ja minden ténylegesen változó kijelölésnél hívja az `append_crop()`-ot (`edit_controller_crop_mixin.py:119-124`). Az `EditSession.append_crop()` új `crop64` rekordot épít, majd feltétel nélkül a teljes lánc végére fűzi (`session_core.py:123-124`). A két forrás egymástól függetlenül igazolta az eltérést abban az esetben, amikor az előző művelet is Crop volt (a #7367 az 1.0.171-ben javította: `recrop.py` és `edit_controller_crop_mixin.py:111-123`; ez a bekezdés a javítás előtti állapotot rögzíti). A `job-813 kepernyo__20` hibás előfeltétele miatt az ismételt Apply utáni eredeti Undo/Redo gombfelirat és képi végállapot külön mérést kért; ezt a `job-821` elvégezte (lásd „Mérési eredmény (Colab)”).

**Cáfoló kísérlet a korábbi „az eredeti mindig halmoz” állításra:** a közvetlen bináris út ellenőrzi a lista farkát, és csak akkor írja át a meglévő rekordot, ha annak neve `crop64`; más végrekord mellett új bejegyzést ad hozzá. Ez cáfolja a feltétel nélküli halmozást, de nem cáfolja a közbeeső effekttel elválasztott Crop műveletek hozzáfűzését. A dokumentált több-`crop64`-es láncok és a `scan0016.png` `redo=crop64;enhance;crop64` sora ilyen közbeeső műveletet tartalmaz, tehát a feltételes szabállyal összeférnek. A `filters-decoded.md`-ben idézett Alkalmaz-mérés (`crop64;bw;crop64` előtte, `crop64;bw` utána) a PicasaPy régi, összevonó kódját mérte Picasa-eredetű bemeneten; ez PicasaPy-viselkedésről szól, nem az eredeti Picasa Apply-ról. A korábbi eredeti korpusz- és render-mérések a hatályos vágást, illetve a közbeeső műveletekkel elválasztott láncok olvasását igazolják; közvetlenül egymást követő eredeti Apply-t nem mérnek. A cáfoló ellenőrzése ezért a binárisban a két ágat és a `crop64` literált is visszaköveti; a futásidejű képernyő-ellenőrzést a hibás `job-813` szakasz helyett a `job-821` újrafelvétele végezte el.

**Az ellentmondás feloldása (két forrás, egy szabály).** A `filters-decoded.md` korábbi „az újravágás HALMOZ (#1553)" szakasza és ez a lap ugyanarra a `0x006b4300`-ra támaszkodik, és a két állítás csak a „lánc vége `crop64`" esetben ütközött. A bináris dönt: a `0x006b4300` az utolsó elem nevét hasonlítja a `crop64` literálhoz, egyezésnél (érvényes téglalapnál) a rekordot helyben írja át, különben hozzáfűz és kiüríti a redo-listát. A #1553 három érve közül egyik sem a lánc végi `crop64` esetről szólt (a „Recrop" felirat csak a vágás meglétét jelzi), a korpusz pedig a feltételes szabályt támogatja: 38 több-`crop64`-es láncból 37-ben közbeeső szűrő áll, csak 1-ben szomszédos a két rekord. A két szabály összefér: a feltételes szabály az egyetlen, a #1553 hozzáfűzése annak egyik ága. A Visszavonás (`0x006ad860`) elemenként bont, tehát a helyben frissített rekord egyetlen visszavonási lépés, amely a levétel után az előző `crop64` téglalapját állítja vissza, vagy ha nincs, megszünteti a vágást. Ez kódolvasás volt; a látható Undo/Redo állapotot a `job-821` megerősítette (a `job-815` mind a 29 képkockája fekete volt, a mappalistájában nem volt `.picasa.ini`, a módosítási idők a futás előttiek voltak, ezért nem bizonyított semmit). A részletes táblázat és a címek: `filters-decoded.md`, „Az ÍRÁS oldala".

**Vörösszem-figyelmeztetés (A út és B út):** az A út (a `0x005f30e0` bináris feltétele) és a `job-837` mérése egymástól függetlenül ugyanarra a feltételre jut: mentett `tilt` jelenlétére. A B út (a PicasaPy forrása) ugyanezt a feltételt használja (`tiltParam !== 0`, `PhotoViewerEditWorkflow.qml:582,600`), tehát a feltétel egyezik; az alak (felugró ablak az eredetiben, panelsor nálunk) tér el.

**Egyezés:** a `Ctrl+Shift+E` szerkesztői eltérésnél A és B egymástól függetlenül ugyanarra jut; ez a részállítás **megerősített**. A Crop írási szabály és a PicasaPy-eltérés szintén a bináris híváslánc és a mai forráskód külön útjából igazolt; az ismételt Apply látható Undo/Redo végállapotát a `job-821` megerősíti. A teljes jegyre a bizonyítottsági fok **feltételes**, mert a többi eszköz panel-, fájl-, ini-, index-, hiba- és mentési folyamata nincs végigmérve.

## A jegy „Kész, ha” pontjai

- ⛔ A belépési pontok részben összevetve: `job-807` menüállapotokat rögzít nulla, egy és két kijelölt képnél; `job-808` helyi menüket a könyvtárban és szerkesztőben; `job-810` a szerkesztői `Ctrl+Shift+E`-t. A teljes toolbar-súgó és minden eszköz összes belépője `NINCS MEG`.
- ⛔ Ablakok és mezők részben felmérve: a `job-798` csak a Crop panelt és az Escape utáni szerkesztőnézetet mutatta; a `job-836`..`job-839` a Kiegyenesítés, Vörösszem, Retusálás és Szöveg panel felépítését, alapállapotát, a Cancel és az Apply hatását és a felugró ablakok (`Info`, `Confirm`, `Save`) szövegét mérte. A `job-812` a gyors javító csempék, Undo/Redo és Derítőfény egyképes állapotát mutatja. Hiányzik: a megjegyzett állapot Apply után (Kiegyenesítés), a vörösszemes kép Apply/Undo útja, a retus megerősítő ablakának két ága, a szöveg formázásának megjegyzése és a meglévő blokk szerkesztése (javított lépéssorok: `7327-9`..`7327-12b`).
- ✅ A Vörösszem tilt-figyelmeztetés futásidejű feltétele és alakja lezárt (`job-837`): mentett kiegyenesítésnél a csempekattintás után felugró „Info” ablak, szó szerinti szöveggel; tilt nélkül nincs ablak. A PicasaPy panelsora eltér (A jegytörzs).
- ⛔ A műveleti képek megvannak (`job-809`, `job-812`), de a fájl, `.picasa.ini`, index/DB, bal hasáb, háttérmunka és állapotsor teljes összevetése nincs igazolva a megtekintett képekből és `allapot.json`-okból. A `job-315` továbbra is részleges.
- ⛔ A `job-812` Undo/Redo feliratot mutat; a Redeye Undo-kérdés, írási hiba, megszakítás, hálózati és írásvédett hely összevetése `NINCS MEG`.
- ✅ A Crop friss képen végzett Apply/Undo/Redo sorrendje (`job-813`, `kepernyo__14`, `__16`, `__18`) és az alkalmazás nélküli Reset/új kijelölés/Cancel sorrendje (`job-814`, `kepernyo__14`, `__16`, `__18`) lezárt. A bináris az ismételt Apply írási szabályát is eldönti; a `job-813 kepernyo__20` nem igazolta a kért elővágott állapotot, ezért az utána látható Undo/Redo viselkedést a `job-821` mérte újra: ✅ a második Apply után EGY Undo mindkét vágást viszi (`__22`: vágatlan kép, „Crop”, letiltott Undo, „Redo Crop”), a Redo a második téglalapot hozza vissza (`__24` képpontra azonos a `__20`-szal), a további Undo a letiltott gombon nem változtat (`__26`, `__28` bájtra azonos `__22`-vel).
- ✅ Az Eredeti/Nálunk/Teendő táblázat, a mért eredmények és a nyitott kérdések dokumentáltak; a `Ctrl+Shift+E` és a feltételes Crop-végrekord frissítése külön fejlesztői javaslatot kapott.

## Colab-felvételi terv a fennmaradó nyitott pontokhoz

A következő mérést az eredeti Picasa 3.9-en, külön tesztprofilban és visszaállítható másolatokon kell futtatni. A `picasapy-agent/eszkozok/colab_felmero.py` feladata a lépéssor rögzítése és a `kepernyokep`, `ablakmeret`, `allapot`, `picasa_ini`, `db3`, `export` kimenetek letöltése. A tesztmappában a képek legyenek előtte-utána összevethetőek; az eredeti fájlok ne legyenek munkabemenetek.

1. Friss Picasa-profilban indíts, és rögzítsd a főablak alapállapotát. Ugyanazon tesztmappán rögzítsd a könyvtárnézetet kijelölés nélkül, egy kijelölt képpel és két kijelölt képpel.
2. Minden kijelölési állapotban nyisd meg a Kép menü batch tételeit és a kijelölt kép helyi menüjét. Rögzítsd, melyik aktív, melyik tiltott, és a Jó napom van, Auto Contrast, Auto Color, Auto Red Eye Correction művelet előtti és utáni ablakot, állapotot, ini-t, DB-t, exportot és kijelölést. Ahol a menüpont tiltott, ne kényszeríts kattintást. A képes eszköztáron azonosítsd és rögzítsd a szerkesztőhöz vezető gombokat és súgóikat.
3. Egyképes állapotból nyisd meg a nézőt, majd az Alapjavítások fület. Rögzítsd az eszközök és szerkesztő eszköztár látható gyorsbillentyűit; próbáld külön az eredeti keymapből ismert `Ctrl+Shift+E`-t. Minden kért eszköznél külön képen rögzítsd a panel megnyitása előtti és utáni mezőket, alapértéket, aktív eszközt, mezőírást vagy egérműveletet, majd az Apply és Cancel ág külön kimenetét.
4. Cropnál használj új és már `crop64` réteget tartalmazó tesztképet. Készíts vágást, Resetet, Undo-t, Redo-t, Cancel-t és Apply-t külön indulásokból; minden lépés után rögzíts ini-t és képkimenetet.
5. Straighten és Red Eye figyelmeztetéshez használd ugyanazt a képet tilt nélkül, majd aktív kiegyenesítéssel. Nyisd meg a Red Eye eszközt, mentsd mindkét képernyőállapotot, és rögzítsd az Undo kérdést.
6. Retouch esetén rögzítsd a célkattintást, forráspont mozgatását, folt véglegesítését, folt-Undo/Redo/Reset, panel-Cancel, Apply és külön Save lépéseit. A szövegnél egy meglévő blokk módosítását és új blokkot is mérj, külön Cancel és Apply ággal.
7. Derítőfény, Auto Contrast, Auto Color és Jó napom van esetén rögzítsd a panelen történő egyképes alkalmazást, majd külön a könyvtári batch utat. Figyeld a haladásjelzőt, állapotsort, index/rács frissülését, bal hasábot és kijelölést a kattintás alatt és után.
8. A hálózati és írásvédett próbához csak külön, eldobható tesztmappát használj; az állapotot a mérés előtt külön rögzítsd. Futtasd le a műveletet és mentsd a teljes hibaüzenetet, a változatlan/módosult fájlt, ini-t, DB-t és kijelölést.

A 3., 5. és 6. pont első köre lefutott (`job-836`..`job-839`); a maradék javított lépéssorai a „Job-836..839” szakaszban vannak. A 8. pont ezen a csatornán nem végezhető: a Wine-ban csak a `C:` meghajtó látszik, a végrehajtónak nincs hálózati vagy írásvédett helye.

## Javasolt jegytörzs-bővítés

„A #7327 futtatott köre részben lezárta a belépési pontokat, panelállapotokat és egyképes automatikus javításokat (`docs/specs/paritas-folyamat-7327.md`, `Mérési eredmény (Colab)`). A bináris `0x005e638b` útja és a `job-810` szerkesztői felvétele igazolja, hogy az eredeti `Ctrl+Shift+E` a Jó napom van csempét aktiválja; a PicasaPy egyetlen kötése a `MainKeyboardShortcuts.qml:166-174` fájlban a `!viewerOpen` kapu miatt nem érhető el a szerkesztőben. A Crop Apply eredeti írója (`0x006b4300`) a láncvégi `crop64` rekordot frissíti, ha az a lista utolsó eleme, egyébként új Cropot fűz hozzá; az `EditSession.append_crop` (`session_core.py:123-124`) feltétlen hozzáfűzés maradt, az Apply útját a #7367 (1.0.171) a `recrop.py`-n át vezeti. A `job-813` `color_patches.jpg`-s szakasza hibás előfeltételű volt; az ismételt Apply utáni látható Undo/Redo állapotot a `job-821` helyes újrafelvétele mérte, és egyezik a bináris-olvasattal. A fájl/ini/index-utóhatás, a többi panel Apply/Cancel, a red-eye figyelmeztetés tilt-bemenettel, valamint a hiba- és hálózati/írásvédett ágak nyitottak.”

## Új kutatási jegyjavaslatok

Nincs külön új kérdés: a futtatott hiányok a #7327 céljához tartoznak, és a Colab-felvételi tervben szerepelnek.

## Nyitott

- A teljes eszközfolyamatok és minden belépési pont élő összevetése: `NINCS MEG`, megszerzés a fenti Colab-felvételi tervvel.
- Az eredeti Auto Red Eye módosított fájltípusokra vonatkozó élő kezelése, a fájlírási hiba ablakának pontos alakja, a `redeye.tmp` életciklusa és az állapotsor/időzítés: `NINCS MEG`, a 2., 3. és 8. Colab-lépéssel.
- Az eredeti hálózati és írásvédett mentési ágak minden eszköz esetén: `NINCS MEG`, a 8. Colab-lépéssel.
- `Ghidra-kör kell` pont nincs: a jelenlegi nyitott kérdések látható viselkedésre és futásidejű fájl-/UI-hatásra vonatkoznak; a feltárt diszasszemblálás elegendő volt az ismert statikus ágak megnevezéséhez.

## Módosított fájlok

- `docs/specs/paritas-folyamat-7327.md`: a #798 és #807-812 futtatott eredményei, a #821 ismételt Apply utáni Undo/Redo mérése, a koordinátakimenet, a megerősített editor-gyorsbillentyű eltérés és a fennmaradó mérési kérdések. A `job-917`..`job-925` kiértékelése és az L, M, N jegytörzs, a G véglegesítése. A `job-939`..`job-943` (T és V jegytörzs). A `job-949` és `job-950` kiértékelése: Retusálás Mégse függő kijelöléssel és anélkül, újranyitáskori ecsetméret megőrzése és semleges kattintás a panelen (W jegytörzs); Szöveg forgatási szögtérképe három új szöggel (7°, 30°, 38,4°), folytonos szög snap-pel, geometriaváltozás, az L jegytörzs véglegesítése; a mérleg lezárása (15 lezárva, 1 blokkolt, 3 hatókörön kívül).

## Mérési eredmény (Colab)

Az alábbi megállapítások a mért képekre és az `allapot.json` képernyő/ablak rekordjaira támaszkodnak. A `allapot.json` OCR-mezői üresek, az ini és DB tartalmát ezek nem közlik. A feladatjegyzet szerint a #809 négy képe nem töltődött fel; a jelenleg olvasható helyi eredménykönyvtárban 35 számozott PNG és 35 állapotrekord található.

| Feladat | Mért kép és megfigyelés | Következtetés |
|---|---|---|
| #7327-1, job-807: Kép menü, batch almenü | `kepernyo__09` nulla képkijelölésnél, `__11` a Batch Edit almenüvel, `__20` egy kijelölt képnél, `__30` két kijelölt képnél. Az Auto Contrast, Auto Color, I'm Feeling Lucky és Auto Red Eye Correction sorok a felvételeken nem szürke szövegűek. | Vizuálisan elérhetőnek látszanak nulla, egy és két kijelölt képnél. A nulla kijelölés melletti futtatás eredménye és a menüpontok mögötti adatírás a mérésből nem dől el. |
| #7327-2, job-808: helyi menük | `kepernyo__11` egy kijelölt kép, `__17` két kijelölt kép könyvtárnézetben; `__23` a szerkesztői kép helyi menüje. A menük általános kép- és fájlműveleteket mutatnak, közvetlen Crop/Straighten/Redeye/Retouch/Text panelindítót nem. | A helyi menü nem bizonyít közvetlen Alapjavítások-eszközindítást. A toolbar-gombok és súgóik hover-lépés nélkül nem mérhetők. |
| #7327-3, job-809: batch műveletek | `kepernyo__12`, `__18`, `__24` az Auto Contrast, Auto Color és I'm Feeling Lucky utáni képeket; `__34-35` a két képen futtatott Auto Red Eye utáni állapotot mutatja. A kijelölés a rácson látható marad. | A látható batch-hatás és a kijelölés végállapota igazolt. Fájl, `.picasa.ini`, DB/index, állapotsor és háttérmunka nem állapítható meg a megtekintett képekből és `allapot.json`-ból. |
| #7327-4, job-810: `Ctrl+Shift+E` | Könyvtárban a `kepernyo__10` és `__11` képe bájtra azonos, így látható változás nincs. Szerkesztőben `__13` előtt és `__15` után az I'm Feeling Lucky csempe halvány, az Undo felirat `Undo I'm Feeling Lucky`. | Eredetiben a szerkesztői gyorsbillentyű aktiválja a Jó napom van műveletet. Könyvtárnézetben a billentyű utáni fájl-/ini-hatás a képből nem dönthető el. |
| #7327-5, job-798: panel-felmérés | A feladatleltár a `__11`, `__15`, `__19`, `__23`, `__27` képeket öt panelnek jelölte. A tényleges PNG-k SHA-256 alapján `__11`, `__15`, `__19` bájtra azonosak; `__23` és `__27` továbbra is a Crop panelt mutatják. `__33` Escape után a szerkesztő Basic Fixes csempéi látszanak. | Csak Crop és Escape utáni nézet bizonyított. A Straighten, Redeye, Retouch és Text panel mezői, alapértékei és állapota `NINCS MEG`; a panelváltó lépésekhez új felvétel kell. |
| #7327-6, job-811: red-eye és tilt-figyelmeztetés | `kepernyo__11` tilt nélküli, `__19` a feladatleírás szerint `tilt=1,0.18` előkészítés utáni Redeye panelt mutat; egyik képen sincs figyelmeztető ablak. | Nem igazolható, hogy a tilt lánc betöltődött, mert az `allapot.json` nem tartalmaz ini-visszaolvasást. Ebből még nem következik fejlesztési eltérés; további méréshez a betöltött `filters=tilt=1,0.180000,0.000000;` állapotot és az eszköznyitás képernyőjét együtt kell menteni. |
| #7327-7, job-812: Auto Contrast, Auto Color, Lucky, Fill Light | `kepernyo__11-15`, `__19`, `__23` az automatikus javítások után Undo/Redo gombot mutat; `__27` a Fill Light csúszka elmozdulását és az Undo Fill Light feliratot. | Az egyképes paneles művelet képernyőhatása és Undo/Redo felirata látható. A mentett ini, fájl, index, bal hasáb, rács és állapotsor változása nem bizonyított. |
| #7327-8a, job-813: Crop Apply/Undo/Redo | `__14` Apply után „Undo Crop”, méret 415×187; `__16` Undo után 1024×256 és „Redo Crop”; `__18` Redo után ismét 415×187. A `color_patches.jpg` képen `__20` „Crop” csempét és letiltott Undo/Redo-t mutat; `__24` új kijelölés (400×180), `__26` Apply utáni kép (400×180). | Az új képen végzett Apply/Undo/Redo lezárt. A color_patches elővágott induló állapota nem igazolt, ezért ez a szakasz nem élő bizonyíték az ismételt Apply-ról. A bináris külön bizonyítja az írási szabályt: a lánc végi `crop64` rekord koordinátáinak frissítése, más végrekord esetén új rekord hozzáfűzése. A második Apply utáni eredeti Undo/Redo gomb- és képi állapotot a `job-821` méri (következő sor). |
| #7327-8b, job-814: Reset és Cancel Apply nélkül | `__12`-n kijelölés és engedélyezett Apply/Reset; Reset után `__14`-en nincs kijelölés, az Apply/Reset tiltott; új kijelölés `__16`-on, majd `__18`-on a teljes kép és az Alapjavítások eszközrácsa látszik. A záró `picasa.ini` csak `backuphash`-t tartalmaz, cropot nem. | A Reset csak a félkész kijelölést törölte; a következő kijelölést a Cancel elvetette. A lépéssor helyes ablakban futott és a kért hatást mutatja; ehhez az esethez nem kell új felvétel. |
| #7327-8c, job-821: két egymás utáni Crop Apply, majd Undo, Redo, Undo, Undo | `gray_ramp.jpg` (1024×256), azonos munkamenet, 29 képkocka (kockánkénti tábla a „job-821” alszakaszban). Első Apply után `__14`: „Recrop”, „Undo Crop” aktív, „Redo” tiltott, 415×187. Második Apply után `__20`: ugyanaz a három felirat, 415×188, a kép a ramp világosabb részét mutatja. Undo után `__22`: 1024×256, „Crop”, „Undo” tiltott, „Redo Crop” aktív. Redo után `__24`: a képterület pixelre azonos a `__20`-szal, „Recrop”, „Undo Crop” aktív, „Redo” tiltott. Undo után `__26` és a tiltott gombra kattintott Undo után `__28`: bájtra azonos `__22`-vel. Záró `picasa.ini`: `backuphash=28489` és `redo=crop64=1,84bf4400ec7fffff;`, `filters=`/`crop=` nincs. | A helyes előfeltétel teljesült (az első Apply után látszik a vágott kép, a „Recrop” és az aktív Undo). **Egyezik a bináris-olvasattal:** két közvetlenül egymás utáni Apply után EGY Undo mindkét vágást visszaveszi, a Redo a MÁSODIK téglalapot hozza vissza. A `redo=` hash dekódolva 531..946 × 68..256 (415×188), a második téglalap; az ini egyetlen elemet tart, tehát a lánc egyetlen `crop64` rekordot tartalmazott. Nyitott: a `redo=` írásának időpontja, az újranyitás utáni Redo, és az 187→188 átállás oka. |
| #7327-9, job-836: Kiegyenesítés | `__10` a sáv és a háló, `__12` húzás után az előnézet (fogantyú 733-744), `__14` Cancel után az eredeti kép, `__16` újranyitás: a fogantyú középen, `__20` Apply után „Undo Straighten”, `__22` Undo után „Redo Straighten”, `__24` Redo után, `__26` „Save” ablak. Záró ini: `filters=tilt=1,0.391249,0.000000;`, a kép változatlan. | A panel és a működés lezárt; a Mentés megerősítése utáni állapot, az újranyitás Apply után és a Crop-figyelmeztetés nyitott (`7327-9`, `7327-9b`). |
| #7327-10, job-837: Vörösszem, tilt-figyelmeztetés | `__10` a panel tilt nélkül, ablak nélkül; `__22` mentett kiegyenesítés mellett „Info” ablak; `__24` Return után a panel; a húzás, az Apply és az Undo hatástalan (a képen nincs vörösszem). | A figyelmeztetés feltétele és alakja lezárt; az Apply és az Undo-megerősítés nyitott (`7327-10`, vörösszemes kép kell). |
| #7327-11, job-838: Retusálás | `__10` a panel; `__12`-`__14` két kattintás, folt; `__16`, `__18`, `__20` helyi Undo, Redo, Reset; `__26` Cancel; `__34` Apply után „Undo Retouches”; `__36` „Confirm” ablak. Záró fájlok: módosított kép (32 178 bájt), `.picasaoriginals` másolat, `filters=retouch=1;` mindkét ini-ben. | A panel, a foltműveletek, a megerősítő ablak és a végállapot lezárt; a fájlírás ideje és az ablak két ága nyitott (`7327-11`, `7327-11b`). |
| #7327-12, job-839: Szöveg | `__10` a panel, `__12` kattintás után kurzor, `__14` begépelt szöveg dobozban, `__18` Cancel után tiszta kép, `__26` Apply után a szöveg a képen, „Undo”/„Redo” letiltott, `__32` „Save” ablak. Záró ini: `text=…` és `textactive=1`. | A panel, a képre gépelés, a Cancel és az Apply, az Undo hiánya és az ini-sor lezárt; a formázás megjegyzése, a meglévő blokk, a „Clear All” és a Mentés nyitott (`7327-12`, `7327-12b`). |

### job-821: két egymás utáni vágás, majd Undo, Redo, Undo, Undo (kockánként)

**Bemenet és olvasat.** A lépéssor 28 elemű (a `var` várakozásokkal), a felvétel 29 `kepernyo__NN.png`-t és 29 `allapot.json` rekordot ad, mind 1280×1024. Az `allapot.json` OCR-mezője mind a 29 rekordban üres, az ablaklista végig egyetlen „Picasa 3”, ezért a feliratokat és a méreteket a képekből olvastam (mind a tizenegy egyedi képkockát megnéztem). A hozzárendelés: a `kepernyo__NN` az (NN-1). lépés utáni állapot, az `__01` az induló. Ezt a végrehajtó kódja és a tartalom is igazolja: a végrehajtó minden lépés ELŐTT rögzít, és a lépéssor után még egyet (28 lépés, 29 kocka); az `__07` még a könyvtár, az `__08` az első kocka, amelyen a dupla kattintás utáni szerkesztő látszik. Minden `var` utáni kocka bájtra azonos az előzővel, ezért a döntő kockák a páros első tagjai.

| Kocka | Előtte végrehajtott lépés | Kép, eszközfelirat, Undo/Redo gomb |
|---|---|---|
| `__01-05` | induló állapot, négy `var 10` | Könyvtárnézet, PicasaTeszt mappa (24 kép), kijelölés nincs; az öt kocka bájtra azonos. |
| `__06-07` | `kattint (80,215)` | Ugyanaz a könyvtárnézet; az `__01`-hez képest csak a bal sáv mappasora tér el (464 képpont). |
| `__08-09` | `dupla (340,272)` | Szerkesztő, `gray_ramp.jpg`, 1024×256; csempe „Crop”; „Undo” és „Redo” tiltott (nincs műveletnév a feliraton). |
| `__10-11` | `kattint (55,167)` (Crop) | „Crop Photo” panel, „Manual”; Apply, Reset, Preview tiltott, Cancel aktív; a kép teljes. |
| `__12-13` | `huz (500,400)-(900,580)` | Kijelölés „Manual: 415 x 187”; Apply, Reset, Preview aktív. |
| `__14-15` | `kattint (84,403)` (Apply 1) | Vágott kép, a státuszsorban 415x187; csempe **„Recrop”**; **„Undo Crop” aktív**, „Redo” tiltott. |
| `__16-17` | `kattint (55,167)` (Recrop) | Crop panel a TELJES, vágatlan képpel, a korábbi kijelöléssel előtöltve; a panelen „Manual: 415 x 188”, a státuszsor még 415x187. |
| `__18-19` | `huz (550,420)-(850,560)` | A húzás a meglévő kijelölésen belül indult, ezért a kijelölés ELMOZDULT (+300, +140 képernyőpont, a kép aljához szorítva: 800,430-1200,610), nem készült új téglalap; „Manual: 415 x 188”. |
| `__20-21` | `kattint (84,403)` (Apply 2) | Vágott kép, 415x188, a ramp világosabb részével; csempe „Recrop”; „Undo Crop” aktív, „Redo” tiltott. |
| `__22-23` | `kattint (70,380)` (Undo 1) | **Vágatlan kép**, 1024x256; csempe **„Crop”**; **„Undo” tiltott**; **„Redo Crop” aktív**. |
| `__24-25` | `kattint (207,380)` (Redo) | A képterület pixelre azonos az `__20`-szal; csempe „Recrop”; „Undo Crop” aktív; „Redo” tiltott. |
| `__26-27` | `kattint (70,380)` (Undo 2) | Bájtra azonos az `__22`-vel. |
| `__28-29` | `kattint (70,380)` (Undo 3, tiltott gombon) | Bájtra azonos az `__22`-vel: a tiltott gomb nem hat. |

**Képpontos ellenőrzés (a szemrevételezés mellett).** `__08` és `__22` képterülete (x 283-1280, y 80-895) 0 képpontban tér el, tehát egy Undo után a kép az induló, vágatlan kép. `__20` és `__24` képterülete 0 képpontban tér el, tehát a Redo a második vágást hozta vissza; az `__14`-hez viszonyítva 80 138 képpont tér el, tehát nem az elsőt. Teljes kockán az `__20` és `__24` között 310 képpont különbözik, mind a Redo gomb területén (két letiltott gomb, szemmel azonos); az `__08` és `__22` között a bal panel Undo/Redo gombjai (a Redo Crop aktív) és a tálca bélyegképe (1134 képpont, szemmel alig látszik, az oka nem dönthető el) térnek el.

**A fájlállapot.** A felvétel `picasa.ini` és `kepmappa__.picasa.ini` fájlja azonos (68 bájt); a végrehajtó a lépéssor és az utolsó kocka után, a Picasa bezárása nélkül olvasta:

```
[gray_ramp.jpg]
backuphash=28489
redo=crop64=1,84bf4400ec7fffff;
```

A `redo=` hash 16 bites törtkoordinátái (`84bf 4400 ec7f ffff`) a 1024×256 képen a 531..946 × 68..256 téglalapot adják (415×188): ez a MÁSODIK vágás (a képernyőn elmozdított kijelölés a forráskép pontjaira átszámolva 531..946 × 68..255), és a lánc egyetlen `crop64` elemet tartott, különben a `redo=` két elemet kapna, vagy az egyetlen Undo az első vágást hagyná látszani. `filters=` és `crop=` nincs. A `kepmappa` lista 92 fájlja közt a `.picasa.ini` (68 bájt) szerepel, a `gray_ramp.jpg` 32 017 bájtos és a futás előtti időbélyegű, tehát a vágás nem íródott a képfájlba. A felvétel csak a záró ini-t adja, lépésenkénti ini nincs, ezért a `redo=` írásának időpontja nem rendelhető lépéshez.

**Előfeltétel (2. pont).** Teljesül: az első Apply után látszik a vágott kép (`__14`), a „Recrop” csempe és az aktív „Undo Crop”. A `job-813`/`job-815` hibáival szemben ez a felvétel bizonyít.

**Döntés (3. pont): egyezik a bináris-olvasattal, nagy bizalommal.** Három független jel mutat ugyanarra: (1) a kép és a gombok (`__22`: vágatlan kép, letiltott Undo, aktív „Redo Crop”), (2) a Redo képe pixelre a második vágás (`__24` = `__20`), (3) a `redo=` egyetlen, a második téglalapnak megfelelő eleme. Az „első vágásra áll vissza” olvasatot a `__22` közvetlenül cáfolja (az első vágás 415×187-es képe nem jelent meg), és a „két elem a redo-listában” olvasatot az ini. Korlát: egy képen, egy téglalap-párral, egyetlen futásban mért; a „két vágás közt más művelet áll” ág (az Undo az előző vágást hozza vissza) ebből a felvételből nem dönthető el, az továbbra is bináris-olvasat.

**Összevetés a mi megvalósításunkkal (4. pont).** Az `applyCrop` (`edit_controller_crop_mixin.py:111-123`) a lánc végi `crop64`-et a `recrop()`-pal (`recrop.py:25-39`) helyben frissíti, és ilyenkor nem hív `_push_undo`-t, tehát egy Undo a vágás előtti láncot állítja vissza, a Redo a másodikat hozza (`edit_controller_history_mixin.py:60-85`); a `tests/app/test_edit_controller_recrop_7367.py` `test_egy_visszavonas_mindket_vagast_visszaveszi` és `test_az_ujra_a_masodik_teglalapot_hozza_vissza` ugyanezt állítja. Az `enterCropTool` (`:298-305`) a vágatlan képet és a meglévő kijelölést mutatja, mint az `__16`. A tesztet nem futtattam (kódolvasás). **A látható Undo/Redo-lánc egyezik.** Két eltérés marad, mindkettő kimondva a jegytörzsekkel:

1. **Csempefelirat (látható):** az eredeti „Recrop”-ra vált, ha van vágás (`__14`, `__20`, `__24`), és „Crop”-ra, ha nincs (`__08`, `__22`, `__26`, `__28`); nálunk a csempe felirata fix `qsTr("Crop")` (`EditorTabCommonFixes.qml:91`). Jegytörzs lent (A).
2. **`redo=` az ini-ben (fájl), lezárva:** az eredeti az Undo-val levett vágást a szerkesztés alatt a `redo=` sorba írja, de a kép újranyitásakor eldobja, és a Redo is letilt (`job-830`, `job-831`). Nálunk a redo-verem csak memóriában él, és a kép újratöltésekor ürül, tehát a látható viselkedés egyezik; fejlesztői jegy nem kell.

#### Job-821 nyomán (A): a Crop csempe „Recrop” felirata (jegy: #7376)

> **Mi a hiba:** a szerkesztő Alapjavítások Crop csempéje mindig a „Crop” (magyarul „Vágás”) feliratot mutatja. Az eredeti Picasa 3.9 a csempét „Recrop”-ra (magyarul „Vágás megismétlése”) cseréli, amíg a képnek hatályos vágása van.
>
> **Eredeti:** a `0x007533b0` a `0x006b0140` visszatérési értéke (van-e érvényes vágás-téglalap) szerint választ az `IDS_CROP_LABEL` és az `IDS_RECROP_LABEL` között (`filters-decoded.md`, „Miért volt téves a #1553 három érve”, 2. pont). Mérés (job-821): „Recrop” az `__14` (Apply 1 után), `__20` (Apply 2 után) és `__24` (Redo után) képeken; „Crop” az `__08` (induló), `__22` (Undo után), `__26` és `__28` képeken. A váltás tehát követi az Undo/Redo-t is.
>
> **Nálunk:** `src/picasapy/app/qml/PicasaPy/EditorTabCommonFixes.qml:91`: `label: qsTr("Crop")`, fix. A `hasCrop` tulajdonság (`edit_controller_crop_mixin.py:36-39`) létezik, de a csempe nem használja; a `picasapy_hu.ts`-ben nincs „Recrop” szöveg.
>
> **Teendő:** a csempe felirata `hasCrop` szerint váltson: nincs vágás: „Crop” / „Vágás”; van hatályos vágás: „Recrop” / „Vágás megismétlése”. A váltásnak követnie kell az Apply, Undo és Redo hatását (ellenőrizd, hogy a `hasCropChanged` jelzés megérkezik-e az Undo/Redo után, mert az `undo()`/`redo()` csak a `toolsChanged`-et adja). A tooltip és az ikon változatlan marad (az eredeti tooltipje „Recrop” állapotban nincs mérve). Az új szövegek a `picasapy_hu.ts`-be kerülnek (forró fájl: szerializáld a többi fordítási változtatással). A magyar „Vágás megismétlése” alakot a repó két helyen állítja (`filters-decoded.md`, `session_core.py:101`), de a `picasapy_hu.ts`-ben nincs `IDS_RECROP_LABEL` eredetű bejegyzés, ezért a fejlesztő a magyar eredeti erőforrásból igazolja a szöveget, mielőtt beírja.
>
> **Kész, ha:** (1) vágás nélküli képen a csempe „Crop”; (2) Apply után „Recrop”; (3) két egymás utáni Apply, majd egy Undo után ismét „Crop”, a Redo után „Recrop” (az `__22` és `__24` párja); (4) a renderelt próbának a csempe KÉPÉT is ellenőriznie kell a két állapotban (referencia: job-821 `__08` és `__14`, a bal panel első csempéje, a felirat a (56,167) pont körül), nem csak a szöveget; (5) a szomszédos csempék (Straighten, Redeye) és a Fill Light sor képe változatlan. Megnyitáskor már vágott képnél a „Recrop” a bináris-olvasat (`0x006b0140`), nem mért állapot: ezt a kiadás kimondja.

#### Job-821 nyomán (B): a `redo=` ini-kulcs (mérés előbb, nem fejlesztői jegy)

A `docs/specs/picasa-ini-format.md` „A `redo=` keletkezésének nyitott része” pontja a nem üres `redo=` értéket előállító felhasználói műveletet nem ismerte. A `job-821` első közvetlen mérése: **Undo után a levett vágás a `redo=` sorba kerül, és ez a szerkesztő megnyitva tartása közben (Back to Library nélkül) is megjelent az ini-ben**, `filters=` és `crop=` nélkül. Ez egyezik a bináris-olvasattal (a `CFilterStackUI` a visszavonás-listát a `filters`, az újra-listát a `redo` kulcsból építi, `0x006ad530`; az Undo az utolsó elemet a redo-vektorba teszi, `0x006ad860`; a `redo` kulcs szerializálása `0x0069f777`-`0x0069f799`). Nyitott marad (egyik sem dönthető el a felvételből): (a) melyik lépésnél íródik az ini (csak a záró állapot ismert); (b) az újranyitás után a Redo gomb használható-e a `redo=` sorból; (c) a `redo=` sor sorrendje több elemnél; (d) miért 415x188 az újranyitott kijelölés, miközben az Apply utáni kép 415x187 (az ini `crop64` hash-e az első Apply után nincs meg: a rekord 16 bites törtkoordinátát tárol, az átállás oka ebből a felvételből nem látható).

**A `job-829`..`job-832` eredménye (2026-11-23, az eredeti Picasa 3.9, a `job-821` lépéssora, a második húzás a kijelölésen kívülről indítva, ini-olvasás a feladat végén).** (1) Két Apply után (`job-829`): `filters=crop64=1,840110091bfcaff;` és `crop=rect64(840110091bfcaff)`, vagyis egyetlen `crop64` a második téglalappal: a helyben frissítés a fájlban is megerősítve. (2) Két Apply és egy Undo után (`job-830`): nincs `filters=` és `crop=`, viszont `redo=crop64=1,840110091bfcaff;`: az eredeti a levett vágást a szerkesztés alatt azonnal kiírja a `redo=` sorba. (3) Undo után kilépés a könyvtárba és a kép újranyitása (`job-831`): a `redo=` sor törlődik, a képkockán (`kepernyo__27`) a Visszavonás és az Újra is letiltott, a csempe „Crop”: a Redo az újranyitást nem éli túl. (4) Undo, majd Redo után (`job-832`): a `filters=` és a `crop=` visszakerül, `redo=` nincs. **Következtetés:** a `redo=` az eredetiben átmeneti, a szerkesztés idejére szóló tükör; az újranyitás eldobja. A PicasaPy a Redo-vermet csak memóriában tartja és a kép újratöltésekor üríti (`edit_controller_session_mixin.py:121`, `:258`), tehát a látható viselkedés egyezik; a `redo=` ki nem írása az eredeti szerint sem hagy nyomot az újranyitott képen. **Fejlesztői jegy nem kell.** Nyitva marad: az újranyitott kijelölés 415×188-as mérete a 415×187-es vágott kép mellett (`job-821` `__16`); ez a vágás eredményét nem érinti.

### Job-836..839 (9-12. feladat): Kiegyenesítés, Vörösszem, Retusálás, Szöveg

**Bemenet és olvasat.** Négy felvétel, mind 1280×1024, mind a `PicasaTeszt` mappa `gray_ramp.jpg` képén (1024×256, 32 017 bájt). A közös bevezető (négy `var 10`, a mappasor kattintása, a kép dupla kattintása) után a lépéssor az adott eszközt járja végig. A `kepernyo__NN` az (NN-1). lépés utáni állapot: a végrehajtó minden lépés ELŐTT rögzít, és a lépéssor után még egyet (job-836: 26 lépés, 27 kocka; job-837: 32 és 33; job-838: 40 és 41; job-839: 32 és 33). Az `allapot.json` OCR-mezője mind a négyben üres, ezért a feliratokat, a gombállapotokat és a párbeszédek szövegét a képekből olvastam (a párbeszédeket háromszoros nagyításban). A `var` utáni kockák többnyire bájtra azonosak az előzővel, ezért a döntők a páros első tagjai. Az `allapot.json` ablaklistája jelzi a felugró ablakokat: `Save` (836 `__26-27`, 839 `__32-33`), `Info` (837 `__22-23`), `Confirm` (838 `__36-41`). A képpontos összevetések a képterületen (x 283-1280, y 364-612) készültek; egy eszközből kilépés után a kép 3 705 képpontban tér el az induló képtől, legfeljebb 1 (836) illetve 3 (838) szintnyi RGB-összeggel: újrarajzolási kerekítés, nem tartalmi eltérés. A koordináták a képből mértek (a vezérlők befoglaló dobozának közepe, árnyékkal együtt, kb. ±2 képpont).

#### Job-836: Kiegyenesítés (kockánként)

| Kocka | Előtte végrehajtott lépés | Kép, panel, Undo/Redo |
|---|---|---|
| `__01-07` | induló állapot, `kattint (80,215)` | Könyvtárnézet, PicasaTeszt (24 kép), kijelölés nincs; a hét kocka bájtra azonos. |
| `__08-09` | `dupla (340,272)` | Szerkesztő, `gray_ramp.jpg`; a csempék aktívak, az „Undo” és a „Redo” letiltott. |
| `__10-11` | `kattint (138,160)` (Straighten) | Kiegyenesítés mód: a képen 44 képpontos négyzetháló; a bal panel csempéi, a Fill Light és a felső eszköztár halvány, az Undo/Redo gombok nincsenek; a kép alatt sáv: csúszka x 557-823, „APPLY” x 835-916, „CANCEL” x 922-1003 (mind y 850-877); a fogantyú közepe x=689,5, a sáv közepén. |
| `__12-13` | `huz (680,863)-(740,863)` | Fogantyú x 733-744 (közép 738,5); a kép előnézete elforgatva és kitöltésre nagyítva (a bal széle már nem fekete), a bal panel hisztogramja megváltozott. |
| `__14-15` | `kattint (962,863)` (CANCEL) | Alapjavítások; a képterület és a bal panel az `__08`-cal azonos (0 képpont), „Undo”/„Redo” letiltott; csak az állapotsor szövege rövidebb (elmarad a „PicasaTeszt >” előtag és a „(1 of 24)”). |
| `__16-17` | `kattint (138,160)` (újranyitás) | Ismét Kiegyenesítés mód; a fogantyú 684-695 (középen), a kép az eredeti, az `__10`-zel azonos: a Cancel elvetett értéke nem maradt meg. |
| `__18-19` | `huz (680,863)-(740,863)` | Azonos az `__12`-vel (a képterület 0 képpontban tér el): ugyanaz a húzás ugyanazt a fogantyúhelyet és előnézetet adja. |
| `__20-21` | `kattint (875,863)` (APPLY) | Alapjavítások, kiegyenesített kép; **„Undo Straighten”** aktív, „Redo” letiltott. |
| `__22-23` | `kattint (70,380)` (Undo) | Az eredeti kép (az `__08`-tól 3 705 képpontban tér el, legfeljebb 1 szint); „Undo” letiltott, **„Redo Straighten”** aktív. |
| `__24-25` | `kattint (207,380)` (Redo) | Kiegyenesített kép (az `__20`-tól a képterületen 14 képpont); „Undo Straighten” aktív, „Redo” letiltott. |
| `__26-27` | `billentyu ctrl+s` | „Save” ablak, a háttérben az „Undo Straighten” aktív. Szöveg: cím „Save”, „Save changes to disk?”, „A backup of this file will be made.”, jelölő „Do not ask me again.” (nincs bejelölve), gombok „Save” (ezen a fókusz) és „Cancel”. A végrehajtó az ablakot nem erősítette meg. |

**A záró fájlállapot.** `picasa.ini` (= `kepmappa__.picasa.ini`, 70 bájt):

```
[gray_ramp.jpg]
backuphash=17619
filters=tilt=1,0.391249,0.000000;
```

A `gray_ramp.jpg` 32 017 bájtos, módosítási ideje a futás előtti (04:43:44), `.picasaoriginals` nincs: a Save ablak megerősítetlen volt, a kép nem íródott. A `filters=tilt=…` sor viszont a Mentés megerősítése nélkül, a szerkesztő nyitva tartása mellett már az ini-ben van (legkésőbb a Ctrl+S-ig; lépésenkénti ini nincs, ezért az írás pontos ideje nem rendelhető lépéshez). A `job-837` ugyanazzal a húzással (680 → 740) ugyanezt az értéket adta: `tilt=1,0.391249,0.000000;`, tehát a húzás-érték leképezés két futásban azonos (egy pont: a +49 képpontnyi elmozdulás 0,391249-et ad; az összefüggés további pontok nélkül nem általánosítható).

**Kattintás-ellenőrzés.** Minden kattintás oda ment, ahova szánták. A húzás kezdőpontja (680) a fogantyútól (684-695) balra, a sávon van, a fogantyú mégis a kurzorhoz ugrott (738,5 az 740 helyett).

**Eldőlt (836):** a sáv felépítése és helye, az alapállás (közép), a húzás élő előnézete, a Cancel hatása (pixelre az eredeti kép, csúszka nem marad meg), az Apply hatása és az Undo/Redo felirata, az ini-sor. **Nem dőlt el:** a Mentés megerősítése utáni fájl, biztonsági másolat, ini, index; az újranyitás Apply után (a csúszka induló értéke); a Crop figyelmeztetésének alakja aktív kiegyenesítésnél; a második csúszkaérték. Javított lépéssor: `7327-9`, `7327-9b` (lent).

#### Job-837: Vörösszem, tilt nélkül és után

| Kocka | Előtte végrehajtott lépés | Kép, panel, ablak |
|---|---|---|
| `__01-09` | mint a 836-ban | Bájtra azonos a 836 `__01-09`-cel. |
| `__10-13` | `kattint (217,160)` (Redeye), `huz (500,400)-(550,450)` | Panel **„Redeye Repair”** (szem-ikon). Szöveg: „Click, hold, and drag the mouse around each eye separately to select it. A selection box appears over the area.  Release the mouse to complete your selection. The Photo is displayed with the red-eye removed.” és külön sorban „Note: You can click on a box to delete a change.” (az „area.” után két szóköz). „Auto”, „Preview”, „Reset” és „Apply” letiltott, „Cancel” aktív (piros X); a felső eszköztár, az aktív kivételével a lapfülek és az alsó tálca halvány. A húzás után a kép és a panel bájtra azonos az előzővel: nincs kijelölő négyzet, az Apply tiltott marad. Tilt nélkül nincs felugró ablak (`allapot.json`: csak „Picasa 3”). |
| `__14-15` | `kattint (188,403)` (Cancel) | Alapjavítások, a teljes kocka bájtra azonos a 836 `__14`-gyel. |
| `__16-17` | `kattint (138,160)` | Kiegyenesítés mód, a teljes kocka azonos a 836 `__16`-tal. |
| `__18-19` | `huz (680,863)-(740,863)` | Kiegyenesítés előnézet (a fogantyú 739 körül). |
| `__20-21` | `kattint (875,863)` (APPLY) | Alapjavítások, kiegyenesített kép, „Undo Straighten” aktív. |
| `__22-23` | `kattint (217,160)` (Redeye, aktív kiegyenesítésnél) | **„Info” ablak** (lásd lent); a panel még nem váltott, a bal oldalon az Alapjavítások csempéi és az „Undo Straighten” látszik. |
| `__24-25` | `billentyu Return` | Az ablak bezárult, a Vörösszem panel megnyílt a kiegyenesített képpel. A panelszöveg azonos a tilt nélkülivel, külön figyelmeztető sor nincs; a gombállapotok ugyanazok. |
| `__26-33` | `huz (500,400)-(550,450)`, `kattint (84,403)`, `kattint (70,380)`, `billentyu Return` | Mind bájtra azonos az `__26`-tal; az `__24`-től csak a Cancel gomb fókuszkerete tér el (249 képpont). |

**Az „Info” ablak szó szerint** (`__22`, háromszoros nagyításból): cím „Info”; kék „i” ikon; szöveg: „This image's orientation has been modified by the Straighten tool, which can cause inaccuracies when selecting red eye  rectangles.” (a „red eye” és a „rectangles” között két szóköz), új sorban „If your redeye fixes appear to be misaligned (or non-existent), try undoing the Straighten fix, then reapply red eye fixes, and Straighten again if necessary.”; egyetlen gomb: „OK” (fókuszban, a Return zárja). Az ablak a (481..800, 436..586) téglalapban áll, az „OK” közepe (643,566). A szöveg az `IDS_WARN_REDEYE_ACCURACY` szövegével betűre egyezik.

**A záró fájlállapot.** `picasa.ini` (70 bájt): `backuphash=52798` és `filters=tilt=1,0.391249,0.000000;`; `redeye` bejegyzés nincs, a `gray_ramp.jpg` 32 017 bájtos és változatlan.

**Kattintás-ellenőrzés.** A `huz (500,400)-(550,450)` a képen belül ment (a kép x 288-1275, y 364-611), de a szürke ramp képen nem keletkezett kijelölés: vagy nincs rajta vörös képpont, vagy a húzást nem ismerte fel; ezt a felvétel nem dönti el. A `kattint (84,403)` a Redeye panelben a letiltott Apply-ra esett, a `kattint (70,380)` pedig a panel üres részére: Vörösszem módban nincs Undo gomb (a panel „Auto/Preview”, „Reset”, „Apply/Cancel” sorokból áll). Ezek a lépések tehát nem bizonyítanak.

**Eldőlt (837):** a Vörösszem panel alapállapota, szövege és gombjai tilt nélkül; **a tilt-figyelmeztetés futásidejű feltétele és alakja** (mentett kiegyenesítésnél a csempekattintás után felugró „Info” ablak, a panel az OK után nyílik meg, a panelben nincs külön figyelmeztető sor; tilt nélkül nincs ablak); a Cancel hatása. **Nem dőlt el:** az Apply, az Undo megerősítő ablaka és a mentett fájl (nincs vörösszem a képen), a kézi húzás hatása vörösszemes képen. Javított lépéssor: `7327-10` (lent; előfeltétele egy vörösszemes tesztkép).

#### Job-838: Retusálás

| Kocka | Előtte végrehajtott lépés | Kép, panel, ablak |
|---|---|---|
| `__10-11` | `kattint (55,275)` (Retouch) | Panel: cím **„Retouch blemishes”** (középre igazítva, ikon nélkül); útmutató: „Click to select the area to fix. Then, move the mouse to see a preview of the replacement area. Click on the image again to finalize. Lather, rinse, repeat. Note: you can use ctrl-drag to pan.”; „Brush Size” csúszka (fogantyú közepe x=134, a sáv 74-196, vagyis középen); „Reset”, „Undo Patch”, „Redo Patch”, „Apply” letiltott, „Cancel” aktív; a kép sarkában „Zoomed to 97%” jelző és navigátor; a felső eszköztár és az alsó tálca halvány. |
| `__12-13` | `kattint (600,450)` | A kattintás helyén ecsetkör (átmérő 50 képpont: a fehér gyűrű külső széle x 575-624, y 425-474); a panel nem változott, minden gomb letiltott: az első kattintás csak a javítandó területet jelöli. |
| `__14-15` | `kattint (660,450)` | „Reset”, „Undo Patch”, „Apply” aktív, „Redo Patch” letiltott; az ecsetkör az egérrel (660,450) mozog; a bal panel hisztogramja megváltozott. |
| `__16-17` | `kattint (77,340)` (helyi Undo) | „Undo Patch”, „Reset” és „Apply” letiltott, **„Redo Patch” aktív**; a képterület az `__10`-zel azonos (0 képpont). |
| `__18-19` | `kattint (202,340)` (helyi Redo) | „Reset”, „Undo Patch”, „Apply” aktív, „Redo Patch” letiltott. |
| `__20-21` | `kattint (140,305)` (Reset) | Mind a négy gomb letiltott (a „Redo Patch” is: a visszaállítható lista kiürül), „Cancel” aktív; a képterület az `__10`-zel azonos. |
| `__22-25` | `kattint (600,450)`, `kattint (660,450)` | Mint az `__12-15`: a folt újra létrejön (az `__14` és az `__24` képterülete 2 képpontban tér el). |
| `__26-27` | `kattint (188,403)` (Cancel) | Alapjavítások; „Undo”/„Redo” letiltott (nincs „Undo Retouches”); a kép az induló képpel a kerekítési zajon belül azonos. |
| `__28-29` | `kattint (55,275)` (újranyitás) | A panel friss: minden gomb letiltott, a folt nem maradt meg. |
| `__30-33` | `kattint (600,450)`, `kattint (660,450)` | A folt létrejön (`__32`: „Reset”, „Undo Patch”, „Apply” aktív). |
| `__34-35` | `kattint (84,403)` (Apply) | Alapjavítások; **„Undo Retouches”** (többes szám) aktív, „Redo” letiltott; a kép az induló képtől 2 264 képpontban tér el (x 572-642, y 408-489, legfeljebb 9 szintnyi RGB-összeggel: a folt a (600,450) körül). |
| `__36-41` | `kattint (70,380)` (Undo) | **„Confirm” ablak** (lásd lent); a háttérben az „Undo Retouches” még aktív, a kép változatlan. A további lépések (`kattint (207,380)`, `billentyu ctrl+s`) nem hatottak: a hat kocka bájtra azonos. |

**A „Confirm” ablak szó szerint** (`__36`): cím „Confirm”; színes Picasa-logó ikon; szöveg: „Retouch fixes cannot be recovered with redo.” új sorban „Are you sure you want to undo?”; két gomb: „Undo” (x 651-724) és „No” (x 731-803), mindkettő y 534-552; a fókusz (pontozott keret) a „No”-n áll; jelölőnégyzet és „Cancel” nincs. Az ablak a (467..813, 456..563) téglalapban áll.

**A záró fájlállapot.** A `gray_ramp.jpg` 32 017-ről **32 178 bájtra** változott (módosítás 05:22:48); `.picasaoriginals/gray_ramp.jpg` 32 017 bájt, az eredeti 04:43:44 módosítási idővel; `.picasaoriginals/.picasa.ini` 101 bájt (05:22:48); `.picasa.ini` 55 bájt (05:22:50). A két ini szó szerint:

```
.picasa.ini
[gray_ramp.jpg]
backuphash=24536
filters=retouch=1;

.picasaoriginals/.picasa.ini
[gray_ramp.jpg]
filters=retouch=1;
moddate=ea3589ad0a7bdd01
width=1024
height=256
textactive=0
```

**Következtetések.** (1) A `filters=retouch=1;` MINDKÉT ini-ben ott van: ez a `paritas-ellenorzes-archiv-1.md` job-315 szerinti állítását (a forrás-szakaszban is megmarad) nyers adattal megerősíti, és ellentmond annak az olvasatnak, hogy a `filters` a fájlírás után csak az eredeti-mappa ini-jében marad. (2) Egyetlen Save ablak sem jelent meg a `__34-41` kockákon, és a Ctrl+S-t a modális „Confirm” ablak elnyelte, mégis megvan a módosított kép és a biztonsági másolat. Ezért a fájl írása kizárásos alapon az Apply-hoz vagy az Undo-kattintáshoz rendelhető, nem a Ctrl+S-hez; a lépésenkénti fájlidő nincs felvéve (a lista csak a végállapotot adja), ezért az Apply és az Undo-kattintás közti választás nem dönthető el. A megerősítő szöveg („Retouch fixes cannot be recovered with redo.”) az Apply-kori beégetéssel összefér, de önmagában nem bizonyítja. (3) A folt hatása kicsi (legfeljebb 9 szint), mert a ramp a (660,450) és a (600,450) pont közt alig változik.

**Kattintás-ellenőrzés.** Minden kattintás oda ment. Az `Apply (84,403)` és a `Cancel (188,403)` a gombok alsó szélén van (a gombok y 378-404 között állnak), a két kattintás mégis hatott. A `kattint (207,380)` és a `ctrl+s` a nyitva álló „Confirm” ablak miatt hatástalan volt: a „Redo” és a Mentés ebből a felvételből nem mérhető.

**Eldőlt (838):** a panel elemei és állapotai, a kétkattintásos folt működése (az első kattintás a javítandó terület, a második a javítás forrása és véglegesítése), a helyi Undo/Redo/Reset, a Cancel, a megjegyzett állapot hiánya, az Apply feliratai, a megerősítő ablak szövege és alakja, a végső fájl- és ini-állapot. **Nem dőlt el:** a fájlírás ideje (Apply vagy Undo-kattintás), a megerősítő ablak két ágának hatása („Undo”, „No”), az Újra az Undo után, a Mentés, az ecsetméret szabálya (csak az alapállás van mérve: 50 képpont átmérő a 987×247 képpontos megjelenített képen, 97%-os nagyításnál). Javított lépéssor: `7327-11`, `7327-11b` (lent).

#### Job-839: Szöveg

| Kocka | Előtte végrehajtott lépés | Kép, panel, ablak |
|---|---|---|
| `__01-07` | induló állapot, `kattint (80,215)` | Könyvtárnézet; az induló kockán a bal oldali mappafa más, mint a többi felvételé (5 158 képpont, x 4-235), a mappa kattintása után a kép a többiekével egyező; az `__08-09` bájtra azonos a 836 `__08`-cal. |
| `__10-11` | `kattint (138,275)` (Text) | Panel: ikon és **„Edit Text”**; „Font:” legördülő (üres), „Size:” legördülő (12), „Style:” B, I, U gomb, „Alignment:” három gomb (a bal aktív); sor: fehér kör (szövegszín), áthúzott négyzet, fekete kör és vastagság-csúszka; „Transparency” csúszka (a fogantyú a jobb végén); „Copy Caption” és „Clear All” (letiltott), „Apply” (letiltott) és „Cancel”. A kép közepén kis felirat: „Type anywhere to add text”. |
| `__12-13` | `kattint (600,400)` | A felirat eltűnt; a kép a (600,405) körül I-beam jelet mutat; „Clear All” aktív, az „Apply” még letiltott. |
| `__14-15` | `gepel PicasaProba` | A szöveg közvetlenül a képen: fehér betű sötét, átlátszó, lekerekített dobozban, vastag világos kerettel ((569..679, 370..440)); a kurzor a szöveg után; „Apply” aktív. |
| `__16-17` | `billentyu ctrl+b` | Bájtra azonos az `__14`-gyel: a Ctrl+B nem változtat, a „B” gomb nem vált állapotot. |
| `__18-19` | `kattint (188,403)` (Cancel) | Alapjavítások, a szöveg eltűnt, megerősítő kérdés nincs; a teljes kocka bájtra azonos a 836 `__14`-gyel. |
| `__20-21` | `kattint (138,275)` | A panel alapállapotban (12-es méret, bal igazítás, ugyanazok a színek): a Cancel semmit nem őrzött meg. A formázás megjegyzése így nem dől el, mert az első körben a lépéssor semmit nem formázott (a Ctrl+B hatástalan volt). |
| `__22-25` | `kattint (600,400)`, `gepel PicasaPy7327` | Mint az `__12-14`: a szöveg a képen, „Apply” aktív. |
| `__26-31` | `kattint (84,403)` (Apply), `kattint (70,380)`, `kattint (207,380)` | Alapjavítások, a doboz eltűnt, a szöveg a képen marad (a betűk pixelei x 601-651, y 402-407, a kattintott (600,400) pont ALATT, bal széle a ponton); **„Undo” és „Redo” letiltott**: az Apply nem hozott létre visszavonási lépést. A hat kocka bájtra azonos. |
| `__32-33` | `billentyu ctrl+s` | „Save” ablak, azonos az `__26` (836) ablakával; a végrehajtó nem erősítette meg. |

**A záró fájlállapot.** `picasa.ini` (196 bájt), szó szerint:

```
[gray_ramp.jpg]
backuphash=54990
text=1;133;12;PicasaPy7327;Times;0.316406,0.144531,0.033333,0.000000;v1,4294967295,4278190080,128.000000,1.000000,0.000000,1.000000,400,0,49152;;
textactive=1
```

Egyetlen blokk van: az első kör szövege („PicasaProba”) a Cancel után nem maradt meg. A `gray_ramp.jpg` 32 017 bájtos és változatlan (a Save ablak megerősítetlen). A pozíció a kattintás normalizált helye, egész forrás-képpontra kerekítve (324/1024 és 37/256; a képernyőn (600-288)/987 ≈ 0,316 és (400-364)/248 ≈ 0,145); a méret 12 pt → `0.033333` (12/360); a stílus: kitöltő `4294967295` (`0xFFFFFFFF`, fehér), körvonal `4278190080` (`0xFF000000`, fekete), súly `400`, a záró `49152`. A `blokkhossz` (133) a `picasa-ini-format.md` képletével egyezik (2+1+12+1+5+1+35+1+74+1 = 133). **A `textactive=1` az első mért érték** (a spec eddig csak `0`-t ismert). A betűtípus `Times`, miközben a panel „Font:” mezője üresen áll.

**Kattintás-ellenőrzés.** A `kattint (600,400)` a képre ment, és működött. A `billentyu ctrl+b` hatástalan volt. A `kattint (70,380)` és a `kattint (207,380)` letiltott gombokra esett, ezért az Undo/Redo a szövegnél nem mérhető (de a letiltott állapot maga látszik). A Ctrl+S ablakát a lépéssor nem zárta le.

**Eldőlt (839):** a panel felépítése és helye (mérhető vezérlőközéppontokkal), a szöveg képre gépelése és a doboz alakja, a Cancel (eldobás, nincs kérdés), az Apply (a szöveg az ini-be kerül, nem a `filters` láncba), **az Undo/Redo hiánya a szövegnél**, az ini-sor, a `textactive=1`, a Ctrl+B hatástalansága. **Nem dőlt el:** a formázás megjegyzése Cancel után, meglévő blokk szerkesztése, a „Clear All” hatása, a Mentés megerősítése utáni fájl és ini. Javított lépéssor: `7327-12`, `7327-12b` (lent).

#### Összevetés a mai PicasaPy-val (kódolvasás, futtatás nélkül)

| Eredeti (mérés) | Nálunk (fájl:sor) | Ítélet |
|---|---|---|
| Kiegyenesítés: sáv 557-823 / 835-916 / 922-1003 × 850-877, 44 képpontos háló, halvány csempék, rejtett Undo/Redo, „Undo Straighten” az Apply után | `EditorToolBar.qml:83-87` (267 széles konténer), `PhotoViewerStraightenGrid.qml:5-8` (44×44-es minta), `EditorTabCommonFixes.qml:94,108,121` (`dimmedByTiltModal`), `EditorUndoRow.qml:73-77` (tilt alatt rejtett), `PhotoViewerTiltToolBar.qml:102-123` (Apply csak változásnál ír, Cancel a nyitáskori állapotot hagyja) | Egyezik (kód alapján, renderelt összevetés nem készült). |
| Undo/Redo felirat: „Undo Straighten”, „Redo Straighten”, „Undo Retouches” (job-821: „Undo Crop”) | `edit_action_names.py:250-255`: `f"{label}: {name}"` minden nyelven; a név a `:81-82` táblából | **Eltérés angol felületen** (kettőspont): „Undo: Straighten”. Magyarban a „Visszavonás: <név>” az eredeti erőforrás alakja. F jegytörzs. |
| Vörösszem tilt mellett: felugró „Info” ablak a csempekattintásra, a panelben nincs figyelmeztető sor; tilt nélkül nincs ablak | `EditorRedeyePanel.qml:84-96` (a figyelmeztetés a panelben), `PhotoViewerEditorPanel.qml:99-119` (nincs ablak), `PhotoViewerEditWorkflow.qml:582,600` (feltétel: `tiltParam !== 0`) | A feltétel egyezik, **az alak eltér** (A jegytörzs). |
| Vörösszem panel: cím „Redeye Repair”; találat nélkül csak az útmutató és „Note: You can click on a box to delete a change.” | `EditorRedeyePanel.qml:55` („Redeye”), `:117` (saját angol Note), `:124-131` („No red eye was found automatically.”, a `ui-tobblet-besorolas.tsv:105` szerint saját státuszjelzés) | **Eltérés** (A jegytörzs). |
| Retusálás: útmutató, „Undo Patch”/„Redo Patch”, a helyi Undo/Redo/Reset állapotai, „Undo Retouches” | `EditorRetouchPanel.qml:59-70,119-148`, `edit_action_names.py:82` („Retouches”), `PhotoViewerEditorPanel.qml:194-212` | Egyezik. |
| Retusálás megerősítő ablak: „Confirm”, Picasa-ikon, két sor, „Undo”/„No”, fókusz a „No”-n, nincs jelölő és Cancel | `PhotoViewerContextActions.qml:244-255` (cím „Undo”, a `ConfirmDialog.qml:43-60` alapértékei: Yes/No/Cancel, „Do not ask again”), a szöveg `PhotoViewerEditorPanel.qml:125-130` | A szöveg egyezik, **az ablak alakja eltér** (B jegytörzs). |
| Retusálás panel: cím „Retouch blemishes” ikon nélkül; nincs „Regions selected” sor; az ecsetcsúszka középen áll; az alapkör átmérője 50 képpont a 987×247-es képen | `EditorRetouchPanel.qml:40-48` (ikon + „Retouch”), `:95-103` („Regions selected: %1”), `:84-92` (csúszka 1-100), `edit_controller_shared.py:372` (alapérték 20, a sáv 19%-án), `edit_controller_retouch_mixin.py:64-70` és `PhotoViewerRetouchArea.qml:43-47` (sugár: 0,02 × a megjelenített kép rövidebb oldala, ugyanezen a képen kb. 4,9 képpont sugár) | **Eltérés** (C jegytörzs). |
| Retusálás után: `filters=retouch=1;` a fő ini-ben ÉS az eredeti-mappa ini-jében; a kép és a `.picasaoriginals` másolata megvan | `save_operations.py:121-130` (a fő ini `filters` és `redo` kulcsát törli, `backuphash`-t ír), `:132-143` (a láncot csak az eredeti-mappa ini-jébe teszi); `edit_controller_retouch_mixin.py:207-222` (az Apply csak az ini-láncot írja, képfájlt nem) | **Fájl-szintű eltérés**, a felhasználó számára látható következménye nem mért (D jegytörzs). |
| Szöveg: nincs visszavonási lépés, az ini-sor alapstílusa (fehér, fekete, 400, `49152`, 12 pt = `0.033333`) | `edit_controller_text_mixin.py:501-545` (`applyText` nem tol undo-lépést), `:586-598`, `edit_controller_shared.py:380,407-410`, `ini/text_overlay.py:94` (osztó 360) | Egyezik. |
| Szöveg: a szöveget a képre kell gépelni, a panelben nincs szövegmező, a betűk a kattintott pont ALATT állnak, „Clear All” felirat | `EditorTextPanel.qml:55-66` (útmutató és `textContentField` a panelben), `:446` („Remove all existing text” mint gombfelirat), `PhotoViewerPhotoArea.qml:632-653` (`textClickArea`: csak a pontot adja), `render/text_overlay.py:112` (`anchor` `"ls"`: a pont az alapvonal) | **Eltérés** (E jegytörzs). |
| Mentés ablak: „Save” / „Save changes to disk?” / „A backup of this file will be made.” / „Do not ask me again.” | `SaveDialogs.qml:111,132,144,157` | Egyezik. |

#### Fejlesztői jegyek (job-836..839): #7378, #7379, #7380, #7381

**(A) Vörösszem: a kiegyenesítés-figyelmeztetés felugró „Info” ablak, és a panel szövegei (jegy: #7378)**

> **Mi a hiba:** ha a képen mentett kiegyenesítés van, az eredeti Picasa a Vörösszem csempére kattintva felugró „Info” ablakot ad, és a panelt csak az „OK” után nyitja meg; a panelben nincs külön figyelmeztető sor. Nálunk nincs ablak: a figyelmeztetés szürke szövegként áll a panelben. Ezen felül a panel címe és két szövege is eltér.
>
> **Eredeti:** `job-837 __22` (az ablak: cím „Info”, kék „i” ikon, a szöveg lent szó szerint, egyetlen „OK” gomb, az (481..800, 436..586) téglalapban); `__24` (Return után a Vörösszem panel nyílik, benne nincs figyelmeztető sor); `__10` (tilt nélkül a csempekattintásra nincs ablak, az `allapot.json` csak a főablakot sorolja). A panel címe `__10`-en és `__24`-en „Redeye Repair” (szem-ikonnal); találat nélküli állapotban az útmutató után a „Note: You can click on a box to delete a change.” áll, „No red eye was found automatically.” mondat nincs; „Auto”, „Preview”, „Reset” és „Apply” letiltott, „Cancel” aktív. Az ablak szövege: „This image's orientation has been modified by the Straighten tool, which can cause inaccuracies when selecting red eye  rectangles.” (két szóköz a „red eye” és a „rectangles” közt) + új sorban „If your redeye fixes appear to be misaligned (or non-existent), try undoing the Straighten fix, then reapply red eye fixes, and Straighten again if necessary.”
>
> **Nálunk:** `EditorRedeyePanel.qml:84-96` (a figyelmeztetés a panelben, `visible: panel.straightenActive`), `PhotoViewerEditorPanel.qml:99-119` (a csempe eszközmódot nyit, ablak nincs), `PhotoViewerEditWorkflow.qml:582,600` (`straightenActive = tiltParam !== 0`), `EditorRedeyePanel.qml:55` (cím: „Redeye”), `:117` („Note: click inside the box to undo the change.”), `:124-131` („No red eye was found automatically.”).
>
> **Teendő:** (1) a Vörösszem csempe kattintására, ha `tiltParam !== 0`, a panel megnyitása ELŐTT felugró „Info” ablak jelenjen meg a fenti szöveggel, egyetlen „OK” gombbal (fókuszban, a Return zárja); a panel az „OK” után nyíljon; a panelből a `redeyeStraightenWarning` sor kerüljön ki. (2) Tilt nélkül ne legyen ablak. (3) A panel címe angolul „Redeye Repair” (a magyar az eredeti erőforrásból igazolandó, mielőtt beírod). (4) A „No red eye was found automatically.” mondat ne jelenjen meg; a Note angolul „Note: You can click on a box to delete a change.” legyen. A Crop figyelmeztetéséhez ne nyúlj: annak eredeti alakja nincs mérve (`7327-9b`).
>
> **Kész, ha:** (1) mentett kiegyenesítésű képen a Vörösszem csempe után az „Info” ablak a megadott szöveggel látszik, a bal oldalon még az Alapjavítások; (2) az „OK”/Return után a Vörösszem panel nyílik, figyelmeztető sor nélkül; (3) tilt nélkül nincs ablak; (4) a renderelt próba az ablakot és a panelt is megnézi, és a `job-837 __22` (ablak) és `__24` (panel) képkockával veti össze, mért eltéréssel; (5) a szomszédos Kiegyenesítés-sáv és a Crop panel képe változatlan.

**(B) Retusálás visszavonásának megerősítő ablaka (jegy: #7379)**

> **Mi a hiba:** a „Undo Retouches” gombra az eredeti „Confirm” ablakot ad, két gombbal („Undo”, „No”), jelölőnégyzet és „Cancel” nélkül, a fókusz a „No”-n. Nálunk az ablak „Undo” címmel, Yes/No/Cancel gombokkal és „Do not ask again” jelölővel jön.
>
> **Eredeti:** `job-838 __36`: cím „Confirm”; színes Picasa-logó; „Retouch fixes cannot be recovered with redo.” / „Are you sure you want to undo?”; gombok „Undo” (x 651-724) és „No” (x 731-803), y 534-552; pontozott fókuszkeret a „No”-n; az ablak a (467..813, 456..563) téglalapban áll. A háttérben az „Undo Retouches” és a kép változatlan; az ablak modális (a további kattintás és a Ctrl+S nem hatott, `__36-41`).
>
> **Nálunk:** `PhotoViewerContextActions.qml:244-255` (`ConfirmDialog` `title: qsTr("Undo")`), a `ConfirmDialog.qml:43-60` alapértékei (`yesText` „Yes”, `cancelVisible` és `rememberVisible` igaz, `focusNoOnOpen` hamis, `iconType` „none”); a szöveg `PhotoViewerEditorPanel.qml:125-130` (egyezik).
>
> **Teendő:** a retusálás ágán az ablak címe „Confirm”, az ikon a Picasa-logó (`iconType: "picasa"`), a Yes gomb felirata „Undo”, a No felirata „No”, `cancelVisible: false`, `rememberVisible: false`, `focusNoOnOpen: true`. A Vörösszem ága ugyanezt a komponenst használja: az eredeti Vörösszem-megerősítő alakja nincs mérve (`7327-10`), ezért arra csak akkor terjeszd ki, ha az a felvétel ugyanezt az alakot mutatja.
>
> **Kész, ha:** (1) a „Undo Retouches” gomb után az ablak a megadott címmel, ikonnal, szöveggel és két gombbal áll, a fókusz a „No”-n; (2) a „No” az állapotot nem változtatja, az „Undo” visszavon; (3) a renderelt próba az ablakot a `job-838 __36` megfelelő téglalapjával veti össze, mért eltéréssel; (4) a háttér (a bal panel „Undo Retouches” gombja és a kép) változatlan.

**(C) Retusálás panel: cím, többletsor, ecset alapállása (jegy: #7379)**

> **Mi a hiba:** a megnyitott Retusálás panelben három látható eltérés van: a cím, egy többletsor, és az ecsetcsúszka alapállása.
>
> **Eredeti:** `job-838 __10`: cím „Retouch blemishes” (a magyar erőforrás szerint „Szennyeződések retusálása”, `picasa-hu-terminology.md:172`), középre igazítva, ikon nélkül (`retouch_label` 256×16, x 14-270, y 80, `szerkeszto-panel-meretek.md:279`); az útmutató szó szerint egyezik a mienkkel; „Regions selected” sor NINCS; a „Brush Size” csúszka fogantyúja a sáv közepén áll (közép x=134, sáv 74-196); „Reset”, „Undo Patch”, „Redo Patch”, „Apply” letiltott, „Cancel” aktív. `__12`: az alapállású ecset köre 50 képpont átmérőjű (a fehér gyűrű külső széle x 575-624, y 425-474) a 987×247 képpontos megjelenített képen, 97%-os nagyításnál.
>
> **Nálunk:** `EditorRetouchPanel.qml:40-48` (ikon + „Retouch”, magyarul „Retusálás”), `:95-103` („Regions selected: %1”), `:84-92` (`from: 1; to: 100`), `edit_controller_shared.py:372` (`_DEFAULT_BRUSH_SIZE = 20`, a sáv 19%-án), `edit_controller_retouch_mixin.py:64-70` és `PhotoViewerRetouchArea.qml:43-47` (a kör sugara 0,02 × a megjelenített kép rövidebb oldala: ugyanezen a képen kb. 4,9 képpont sugár, 9,9 átmérő).
>
> **Teendő:** (1) a cím „Retouch blemishes” / „Szennyeződések retusálása”, ikon nélkül, a mért helyen; (2) a „Regions selected” sor ne jelenjen meg; (3) az ecsetcsúszka alapállása a sáv közepe; (4) az alapállású kör átmérője a `job-838 __12` szerint 50 képpont legyen ugyanezen a megjelenítésen. **Nem része:** az ecsetméret-szabály általánosítása (a rövidebb oldalhoz, a szélességhez vagy a nagyításhoz mért-e, és a csúszka két vége): ehhez a `7327-11` felvétel kell, addig a (4) pont csak erre az egy képre és nagyításra szól, a leképezést ne általánosítsd.
>
> **Kész, ha:** (1) a megnyitott panel a `job-838 __10` bal paneljével képpontra összevethető (cím, útmutató, csúszka, gombok), mért eltéréssel; (2) a „Regions selected” sor nincs; (3) a gombállapotok az `__10`, `__14`, `__16`, `__20` szerint váltanak; (4) a szomszéd panelek (Vörösszem, Szöveg) képe változatlan.

**(D) Retusált kép mentése után a fő ini-ben marad a `filters=retouch=1;` (fájl-szintű, nem látható eltérés) (jegy: #7379)**

> **Mi a hiba:** az eredeti a retusált kép mentése (fájlírása) után a `filters=retouch=1;` sort a fő `.picasa.ini`-ben és az eredeti-mappa ini-jében is megtartja; nálunk a mentés a fő ini `filters=` kulcsát törli. A felhasználó számára látható következmény nem mért.
>
> **Eredeti:** `job-838` záró állapot: `.picasa.ini`: `backuphash=24536`, `filters=retouch=1;`; `.picasaoriginals/.picasa.ini`: `filters=retouch=1;`, `moddate=ea3589ad0a7bdd01`, `width=1024`, `height=256`, `textactive=0`; a `gray_ramp.jpg` 32 017 → 32 178 bájt, `.picasaoriginals/gray_ramp.jpg` 32 017 bájt az eredeti módosítási idővel. A fájlírás időpontja (Apply vagy Undo-kattintás) nem dönthető el (`7327-11`).
>
> **Nálunk:** `save_operations.py:121-130` (a fő ini `filters=` és `redo=` kulcsának törlése, `backuphash` írása), `:132-143` (a lánc csak az eredeti-mappa ini-jébe kerül); `edit_controller_retouch_mixin.py:207-222` (az Apply képfájlt nem ír).
>
> **Teendő:** retusálás (és a hasonló, beégetett `redeye`) mentése után a fő ini szakaszában maradjon a `filters=retouch=1;` (illetve a beégetett tokenek), a többi szerkesztési token (amelyek a képbe beleégtek vagy a Mentéskor kikerülnek) kerüljön ki. Hogy az eredeti mely más tokeneket tart meg a fő ini-ben, nincs mérve; a jegy csak a retus-tokent vigye. A fájlírás idejét (Apply-kor vagy Mentéskor) ez a jegy ne változtassa.
>
> **Kész, ha:** egy retusált kép mentése után a két ini tartalma a fenti két szakasszal sorra egyezik (a `backuphash` és a `moddate` értékét kivéve), és a `.picasaoriginals/gray_ramp.jpg` az eredeti bájtokat és módosítási időt őrzi. Látható összevetés nincs (a jegy fájl-szintű): ezt a kimondott korlátot a kiadás jegyezze.

**(E) Szöveg panel: a szöveg közvetlenül a képre gépelendő, a betűk a pont alatt állnak (jegy: #7380)**

> **Mi a hiba:** az eredeti Szöveg eszközben a szöveget közvetlenül a képre kell gépelni (a kattintás után a hely I-beammel jelölt, a szöveg lekerekített dobozban jelenik meg), a panelben nincs szövegmező. Nálunk a panel tetején szövegmező van, és a képre külön kattintással kell helyezni a szöveget. Ezen felül a betűk a kattintott pont ALATT állnak, és a „Clear All” felirat is más.
>
> **Eredeti:** `job-839 __10`: a panelben nincs szövegmező; a kép közepén „Type anywhere to add text”; vezérlők: „Font:” (170,173), „Size:” (93,203), „Style:” B/I/U (185/215/245, 202), „Alignment:” (185/215/245, 233), szövegszín (40,276), áthúzott négyzet (69,276), körvonalszín (124,276) és vastagság-csúszka (192,278), „Transparency” (149,337), „Copy Caption” (86,372) és „Clear All” (189,372), „Apply” (88,406), „Cancel” (191,406). `__12`: a kattintás (600,400) után a hint eltűnik, I-beam látszik a (600,405) körül, „Clear All” aktív. `__14`: a begépelt szöveg a képen, lekerekített, átlátszó sötét dobozban, vastag világos kerettel (569..679, 370..440), „Apply” aktív. `__26`: Apply után a betűk pixelei x 601-651, y 402-407, a kattintott (600,400) pont alatt. Az ini: `text=1;133;12;PicasaPy7327;Times;0.316406,0.144531,0.033333,0.000000;v1,4294967295,4278190080,128.000000,1.000000,0.000000,1.000000,400,0,49152;;` és `textactive=1`.
>
> **Nálunk:** `EditorTextPanel.qml:55` (útmutató: „Type your text, then click on the photo to place it.”), `:60-66` (`textContentField` a panelben), `:75` („Copy Caption” a panel tetején), `:446` („Remove all existing text” a gomb felirataként, a panel alján), `PhotoViewerPhotoArea.qml:632-653` (`textClickArea`: csak a pozíciót adja), `render/text_overlay.py:112` (`anchor` `"ls"`: a pont a betűk alapvonala, így a betűk a pont FÖLÖTT állnak), `edit_controller_text_mixin.py:501-545` (Apply).
>
> **Teendő:** (1) a szöveg közvetlenül a képre gépelhető: a kattintás után a hely jelölt, a begépelt szöveg a képen jelenik meg lekerekített dobozban, és az „Apply” a szöveg megléte után aktív; a panel szövegmezője és a magyarázó sor kerüljön ki; (2) a kép közepén álljon a „Type anywhere to add text” hint a kattintásig; (3) a „Clear All” a gomb felirata (a „Remove all existing text” a tooltip legyen, ha az eredetiben az; ennek forrása a `.tre`); (4) a betűk a kattintott pont ALATT álljanak (a mért glifsorok y 402-407 a 400-as pontnál, 12 pt-nál), a bal szél a ponton. **Nem része:** a panel többi vezérlőjének átrendezése, az áthúzott négyzet és a vastagság-csúszka viselkedése (ezek funkcióját a felvétel nem mérte; a mai funkciót kell megtartani a mért helyre téve).
>
> **Kész, ha:** (1) a Szöveg csempe után a kép közepén a hint látszik, a panelben nincs szövegmező; (2) a képre kattintva és gépelve a szöveg a képen jelenik meg a dobozban, az „Apply” aktív; (3) az Apply után a szöveg a kép pontja alatt áll, az ini-sor a mért alakú (pozíció, méret, stílus), az Undo/Redo letiltott marad; (4) a renderelt próba a `job-839 __10`, `__14` és `__26` képkockával veti össze a panelt, a dobozt és a kész szöveget, mért eltéréssel; (5) a szomszéd panelek képe változatlan.

**(F) Undo/Redo felirat angol felületen: „Undo Straighten”, kettőspont nélkül (jegy: #7381)**

> **Mi a hiba:** angol felületen az Undo/Redo gomb felirata „Undo: Straighten”; az eredetiben „Undo Straighten”.
>
> **Eredeti:** `job-836 __20` („Undo Straighten”), `__22` („Redo Straighten”), `job-838 __34` („Undo Retouches”), `job-821 __14` és `__22` („Undo Crop”, „Redo Crop”): kettőspont nélkül, szóközzel; üres veremnél „Undo” és „Redo”. A bináris `undoname`/`redoname` angolul „Undo ”/„Redo ” (`paritas-folyamat-7346.md:548`), magyarul „Visszavonás: ” (`picasa-menusor-csoportok.md:215`).
>
> **Nálunk:** `edit_action_names.py:250-255`: `f"{label}: {name}"` minden nyelven.
>
> **Teendő:** az angol felületen az alak „<Undo> <név>” és „<Redo> <név>” legyen, kettőspont nélkül; a magyar „Visszavonás: <név>” marad. A többi nyelvnél az alakot az eredeti nyelvi erőforrásból kell kiolvasni, mielőtt nyelvenként döntesz; addig a mai alak marad.
>
> **Kész, ha:** angol felületen a gombok „Undo Straighten”, „Redo Straighten”, „Undo Retouches”, „Undo Crop” szövegűek; a magyar „Visszavonás: Kiegyenesítés” változatlan; a `tests/app/test_undo_labels_465.py` ezt őrzi; a renderelt próba a gombot a `job-836 __20` és `__22` képkockával veti össze.

#### Javított lépéssorok (job-836..839)

A javított lépéssorok a munkafa `.tmp/javitott-lepesek/` mappájában vannak (`7327-8d`, `7327-9`, `7327-9b`, `7327-10`, `7327-11`, `7327-11b`, `7327-12`, `7327-12b`); a közös bevezető (négy `var 10`, `kattint (80,215)`, `var 4`, `dupla (340,272)`, `var 4`) után:

| Fájl | Lépések | Mit dönt el |
|---|---|---|
| `7327-9` (24 lépés) | Straighten, húzás 680 → 740, APPLY (875,863); újranyitás (138,160) és rögzítés; húzás 740 → 640, APPLY; `ctrl+s`, a „Save” ablak „Save” gombja (687,553); kimenet: ini, képmappa, `db3` | a csúszka induló értéke Apply után; második pont a csúszka és az ini-szám összefüggéséhez; a Mentés utáni kép, biztonsági másolat, ini és index |
| `7327-9b` (18) | Straighten + APPLY, majd a Crop csempe (55,167), `Escape` | a Crop-figyelmeztetés alakja aktív kiegyenesítésnél (ablak vagy panelszöveg), és az `Escape` hatása |
| `7327-10` (16) | a bevezető a rács utolsó sorának utolsó képére (1150,770) kattint; Redeye (217,160), Apply (83,400), Undo (70,380), Return | az Apply, az Undo-megerősítés (szöveg, gombok, alapértelmezett gomb) és a fájlállapot vörösszemes képen. **Előfeltétel:** a képnek valódi vörösszeme legyen, és az Auto találjon; a `PicasaTeszt` mappában ilyen kép nincs igazolva, a hívó tegyen oda vörösszemes tesztképet (stockfotó-tárból), és a dupla kattintás helyét cserélje a kép rácshelyére |
| `7327-11` (24) | Retouch, a „Brush Size” fogantyú húzása a bal végére (134 → 78), két kattintás (folt), húzás a jobb végére (78 → 192), két kattintás, APPLY (74,391); a futás azonnal véget ér; kimenet: ini, képmappa, `db3` | az ecsetkör mérete a csúszka két végén; a fájl írása az Apply-kor megtörténik-e (a végállapot módosított kép és `.picasaoriginals` esetén igen) |
| `7327-11b` (28) | Retouch, folt, APPLY, Undo (70,380), „No” (766,543), Undo, „Undo” (687,543), Redo (207,380), `ctrl+s` | a megerősítő ablak két ága, az Újra az Undo után, a Mentés párbeszéd |
| `7327-12` (32) | Text, szöveg, B (185,202), középre igazítás (215,233), Cancel, Text újranyitás, új szöveg, APPLY, `ctrl+s`, „Save” (687,553) | a formázás megjegyzése Cancel után; a Mentés utáni kép és ini |
| `7327-8d` (14) | Crop (55,167), húzás (500,400)-(900,580), APPLY (84,403); a futás az első Apply után véget ér, a kimenet az ini | az első Apply után mentett `crop64` téglalap mérete: 187 vagy 188 képpont magas-e (a `job-821` 187→188 kérdése) |
| `7327-12b` (30) | Text, szöveg, APPLY; újranyitás, kattintás a meglévő szövegre (620,405), gépelés, APPLY; újranyitás, „Clear All” (189,372), APPLY | meglévő blokk szerkesztése, a „Clear All” hatása és az utána következő ini |

### Job-907..913 (a javított lépéssorok kiértékelése: Retusálás, Szöveg, Vágás, Kiegyenesítés)

**Bemenet és olvasat.** Hét felvétel (1280×1024), mind a `PicasaTeszt` mappa `gray_ramp.jpg` képén (1024×256): `job-907` = `7327-11b`, `job-908` = `7327-11`, `job-909` = `7327-12b`, `job-910` = `7327-12`, `job-911` = `7327-8d`, `job-912` = `7327-9b`, `job-913` = `7327-9`. Lépés/kocka: 28/29, 24/25, 30/31, 32/33, 14/15, 18/19, 24/25; a `kepernyo__NN` az (NN-1). lépés utáni állapot. Az `allapot.json` OCR-mezője mind a hétben üres, ezért a feliratokat és a gombállapotokat a képekből olvastam: a döntő kockákat egyenként megnéztem, az azonosakat md5-tel csoportosítottam, a képpontos összevetések a képterületen (x 283-1280, y 364-612) készültek. Az ablaklista két fajta felugró ablakot jelez: `Confirm` (907 `__18-19`, `__22-23`) és `Save` (910 `__30-31`, 913 `__22-23`). A fájlállapotot a `picasa.ini`, a `kepmappa__*` és a `db3__*` fájlokból olvastam; lépésenkénti fájlállapot nincs, csak a záró.

#### Job-907 (`7327-11b`): a Retusálás visszavonásának megerősítése, két ág

| Kocka | Előtte végrehajtott lépés | Kép, panel, ablak |
|---|---|---|
| `__10-11` | `kattint (55,275)` (Retouch) | A friss Retusálás panel, bájtra azonos a `job-908 __10`-zel. |
| `__12-13` | `kattint (600,450)` | Alapállású ecsetkör a kattintás helyén (külső széle x 575-624, y 425-474, 50 képpont). |
| `__14-15` | `kattint (660,450)` | A folt létrejött: „Reset”, „Undo Patch”, „Apply” aktív. |
| `__16-17` | `kattint (74,391)` (Apply) | Alapjavítások; **„Undo Retouches”** aktív, „Redo” tiltott. |
| `__18-19` | `kattint (70,380)` (Undo) | **„Confirm” ablak** (az ablaklistán „Confirm”), a `job-838 __36` ablakával azonos szöveg és alak: „Retouch fixes cannot be recovered with redo.” / „Are you sure you want to undo?”, gombok „Undo” és „No”, a fókuszkeret a „No”-n. |
| `__20-21` | `kattint (766,543)` („No”) | Az ablak bezárult; az `__16`-hoz képest a képterület **0 képpontban** tér el, az „Undo Retouches” aktív, a „Redo” tiltott (a bal panelen csak az Undo gomb fókuszkerete, 315 képpont, és az állapotsor szövege változik). |
| `__22-23` | `kattint (70,380)` | A „Confirm” ablak ismét, az `__18`-cal azonos (csak az állapotsor szövege tér el). |
| `__24-25` | `kattint (687,543)` („Undo”) | Az ablak bezárult; a kép visszaállt (az `__08`-tól 3 705 képpont, legfeljebb 3 szint: ugyanaz a kerekítési zaj, mint a korábbi felvételeken); **az „Undo” és a „Redo” tiltott, a feliratuk csupasz** („Undo”, „Redo”), „Redo Retouches” nem jelenik meg. |
| `__26-29` | `kattint (207,380)` (Redo), `billentyu ctrl+s` | A hat kocka bájtra azonos az `__24`-gyel: a tiltott Redo nem hat, és a Ctrl+S nem hoz „Save” ablakot (nincs mit menteni). |

**A záró fájlállapot.** `gray_ramp.jpg` 32 017 bájt, módosítási ideje a futás előtti (04:43:44), állapotváltozás-ideje 09:31:00 (a futás közben); `.picasaoriginals/gray_ramp.jpg` **nincs**; `.picasaoriginals/.picasa.ini` 0 bájt (09:31:00). A fő `.picasa.ini` (61 bájt, 09:31:02) szó szerint:

```
[gray_ramp.jpg]
backuphash=21665
moddate=0d7b6c38057bdd01
```

A `moddate` FILETIME-értéke 2026-11-23 04:43:44,27, vagyis a visszaállított képfájl módosítási ideje; `filters=` és `redo=` nincs. A `db3` `imagedata_filters`, `imagedata_edited`, `imagedata_redo`, `imagedata_revertable` oszlopa üres (30 bájt), az `imagedata_backuphash` oszlopban 21665 áll (az ini értéke).

**Eldőlt (907), nagy bizalommal:** a „No” ág semmit nem változtat (kép 0 képpont, gombállapot azonos); az „Undo” ág visszaállítja az eredeti képet és a fájlt (a módosítási idő az eredeti, a `.picasaoriginals` másolata eltűnik, az eredeti-mappa ini-je kiürül, a fő ini-be a visszaállított fájl `moddate`-je kerül), és **az Undo után az Újra nem érhető el**: letiltott, a felirata csupasz „Redo”. A Ctrl+S ezután nem ad „Save” ablakot. **Közepes bizalommal:** hogy a fájlt az Apply írta és az Undo állította vissza (a `job-908` az Apply-írást külön bizonyítja, a 907-ben az időrend lépésenként nincs felvéve; a fájl állapotváltozás-ideje 09:31:00, az `imagedata` oszlopok időbélyege 09:31:10).

#### Job-908 (`7327-11`): az ecsetméret két széle, két folt, azonnal Apply

| Kocka | Előtte végrehajtott lépés | Kép, panel |
|---|---|---|
| `__10-11` | `kattint (55,275)` | Friss panel; a fogantyú közepe x=134 (a sáv 74-196). |
| `__12-13` | `huz (134,277)-(78,277)` | A fogantyú a bal végén (x 73-88, közép 80,5); minden gomb letiltott a „Cancel” kivételével. |
| `__14-15` | `kattint (600,450)` | **A legkisebb ecsetkör**: külső széle x 596-603, y 446-453 (8 képpont). |
| `__16-17` | `kattint (660,450)` | Folt a legkisebb ecsettel (a gombok az `__18`-on: „Reset”, „Undo Patch”, „Apply” aktív). |
| `__18-19` | `huz (78,277)-(192,277)` | A fogantyú a jobb végén (x 180-195, közép 187,5); a kör nincs a képen (az egér a csúszkán). |
| `__20-21` | `kattint (600,450)` | **A legnagyobb ecsetkör**: külső széle x 502-697, y 352-547 (196 képpont); a kör a kép felső szélén túlnyúlik (y 352-363 a képen kívül esik). |
| `__22-23` | `kattint (660,450)` | A kör az egérrel (660,450) mozog; a második folt. Az infosáv még „31 KB”. |
| `__24-25` | `kattint (74,391)` (Apply) | Alapjavítások, **„Undo Retouches”** aktív; **az infosáv már „29 KB”** (az Apply-kattintás utáni kockán). |

**A záró fájlállapot** (a futás az Apply után 4 másodperccel véget ér, Mentés és Undo nélkül): `gray_ramp.jpg` **30 189 bájt** (módosítás 09:35:47), `.picasaoriginals/gray_ramp.jpg` 32 017 bájt (az eredeti módosítási idővel), `.picasaoriginals/.picasa.ini` 101 bájt (09:35:47), fő `.picasa.ini` 55 bájt (09:35:49). A két ini szó szerint:

```
.picasa.ini
[gray_ramp.jpg]
backuphash=27462
filters=retouch=1;

.picasaoriginals/.picasa.ini
[gray_ramp.jpg]
filters=retouch=1;
moddate=817321052e7bdd01
width=1024
height=256
textactive=0
```

A `moddate` (2026-11-23 09:35:47,58) az új képfájl módosítási ideje. A `db3`-ban csak bélyegkép-adatbázisok vannak (`imagedata_0` 4 bájt, `imagedata_*.pmp` nincs): az index ebből nem olvasható.

**Eldőlt (908), nagy bizalommal:** (1) **a retusált kép fájlírása az Apply-kor történik**, nem a Mentéskor és nem az Undo-kor: a futás az Apply-jal véget ér, mégis megvan a módosított kép, a biztonsági másolat és a két ini, és az infosáv az Apply-kattintás utáni kockán már az új méretet mutatja (`__22`: 31 KB, `__24`: 29 KB). (2) A két ini tartalma a `job-838` állapotával egyezik (`filters=retouch=1;` mindkettőben). (3) Az ecsetméret három pontja (lent).

##### KIEMELT: az ecsetméret leképezése a `job-908` alapján

A fehér gyűrű (egy képpontos vonal, belül sötét árnyékkal) vonalának középpontjait mértem: a gyűrű két képpontos fehér párokból áll, az átmérő a két átellenes pár közepének távolsága; a vízszintes és a függőleges átmérő mindhárom esetben azonos. A képen a „Zoomed to 97%” jelző áll, a megjelenített kép 988×248 képpont a 1024×256-os forrásból.

| Csúszka állása | Fogantyú közepe (x) | Fogantyú a futásban (t) | Kör külső átmérője (képpont) | Gyűrűvonal-átmérő (2R) | R (képernyő) | R a forráson (R/0,97) | R a megjelenített rövidebb oldalhoz (248) |
|---|---|---|---|---|---|---|---|
| bal vég | 80,5 | 0 | 8 (x 596-603) | 6,0 | **3,0** | 3,1 | 1,2% |
| alap (közép) | 134 | 0,5 | 50 (x 575-624) | 48,0 | **24,0** | 24,7 | 9,7% |
| jobb vég | 187,5 | 1 | 196 (x 502-697) | 194,0 | **97,0** | 100,0 | 39,1% |

(A fogantyú futásának két vége a `job-908` `__12` és `__18` fogantyúdobozaiból mért: 80,5 és 187,5; az alapállás 134, éppen a futás fele. Az alap-kör a `job-907 __12` képén is 50 képpont külső átmérőjű, R = 24,0; a `job-838 __12` korábbi mérése (külső x 575-624) ezzel egyezik.)

**Egy független második mérés.** A #4544 mérőadatai közt van a job #314 képernyőképe (1024×1024-es kép, „Zoomed to 80%”, alapállású csúszka): a gyűrűvonal-középpontok távolsága ott vízszintesen és függőlegesen is 40,0, vagyis **R = 20,0 képpont, R/0,80 = 25,0 a forráson**. Az alapállású csúszkán tehát a forrásképi sugár 25,0 (job #314: 1024×1024 képen, 80%-nál) és 24,7 (itt: 1024×256 képen, 97%-nál): **négyszeres rövidebb oldal és eltérő nagyítás mellett ugyanaz**.

**Az illesztés a korábban kiolvasott bináris képlethez** (`forras-audit-5186-2.md`, #5975, `0x0060b430`; ebben a körben a képletet nem olvastam újra): `R_képernyő = max(3·max(z,1), min(100, min(w,h)/2)·s·z)`, `R_forrás = R_képernyő/z`, ahol `z` a nagyítás, `s` a csúszka mezője (a konstruktor kezdőértéke `0.25`, `0x0060a763`), `w,h` a nézet téglalapja. Ha a nézet rövidebb oldala legalább 200 képpont (itt igen), akkor `R_képernyő = max(3, 100·s·z)`. A három mért pont ebbe **szabad paraméter nélkül** illik (`z` = 0,97, a képernyőn olvasható):

- bal vég: R = 3,0, tehát a 3 képpontos minimum dominál (`3·max(z,1) = 3`); ebből `s ≤ 0,031`;
- alap: R = 24,0, `s = 24,0/97 = 0,247`, vagyis a konstruktor-érték `0,25` (a számolt 24,25 a mérés ±0,5 képpontos pontosságán belül);
- jobb vég: R = 97,0, `s = 1,000`;
- a job #314-en: `s = 0,25`, `z = 0,80` esetén R = 20,0, egyezik a mérttel.

**Mit mond ki ez, és mit nem.**

1. **Nem a kép rövidebb oldalához mért.** Az alapállás sugara 25 forrásképpont egy 1024×1024-es és egy 1024×256-os képen is (négyszeres rövidebb oldal), a jobb vég 100 forrásképpont. A mai leképezés (`sugár = érték/1000 × rövidebb oldal`) és a #7379-es változat (`érték/494 × rövidebb oldal`) is a rövidebb oldalhoz mér: **mindkettő olyan modellt használ, amelyet a mérés nem támaszt alá**.
2. **A megjelenített kör a nagyítással arányos** (R_képernyő = R_forrás·z): az alapállású kör R-je 24,0 (z = 0,97) és 20,0 (z = 0,80), aránya 0,833, a nagyítások aránya 0,825. Ez két képen, két nagyításon mért, nem külön nagyítás-sorozat.
3. **A kép szélességéhez mértség nincs kizárva az adatokból**: mindkét mért kép 1024 képpont széles. A bináris képletben nincs képméret (csak a nézet téglalapja a 200 képpontos kapun át). Eldönti: `7327-11d` (a 768×512-es `rgb_gradient.jpg`). **Eldöntve a `job-918`-cal (768×512-es kép, z = 1,07): a kép szélességétől és rövidebb oldalától független (lásd „Job-917 és job-918”).**
4. **A csúszka-állás és `s` közti alak nem bizonyított.** Három állás van mérve: a bal vég (csak felső korlát: `s ≤ 0,031`), a közép (`s = 0,25`), a jobb vég (`s = 1`). A legegyszerűbb illeszkedő alak `s = t²` (`t` a fogantyú helye a futásban, 0..1), de pl. az `s = 1,5·t - 0,5` (a bal végen negatív, a 3 képpontos minimumra vágva) is átmegy mindhárom ponton. A két alak t = 0,25-nél 6,1 illetve 3,0 képpontos, t = 0,75-nél 54,6 illetve 60,6 képpontos R-t ad (z = 0,97), tehát **két köztes állással eldönthető**: `7327-11c`. **Eldöntve a `job-917`-tel: a leképezés lineáris (`s = t`), az `s = t²` és az `s = 1,5·t - 0,5` cáfolt.**

**A #7379 ecsetméret-változata: a 908 NEM igazolja.** A javasolt 494-es osztó és az 50-es alapállás az alapállást egy pontból találta el (R = 25,1 a 988×248-as képen, mért 24,0), de a két végén és más képméreten cáfolja a mérés:

| | min (érték 1) | alap (érték 50) | max (érték 100) | job #314 (1024×1024, 80%), alap |
|---|---|---|---|---|
| **eredeti, mért R (képernyő)** | 3,0 | 24,0 | 97,0 | 20,0 |
| #7379 (`érték/494 × rövidebb megjelenített oldal`) | 0,5 | 25,1 | 50,2 | 83,0 |
| mai main (`érték/1000`, alap 20) | 0,2 | 4,96 (érték 20) | 24,8 | 16,4 (érték 20) |

A #7379 a jobb végen fele akkora kört ad, a bal végen hatodannyit, és egy négyzetes 1024×1024-es képen az alapállás kb. négyszeres (83,0 a mért 20,0 helyett). **Ez dönti el:** a #7379 ecsetméret-változtatása ebben az alakban **nem adható ki**; a #7379 többi része (cím, „Regions selected” sor, megerősítő ablak) a 908-tól független. Két járható út: (a) az ecsetméret-leképezés kimarad a #7379-ből (a mai 20/1000 marad, kimondott eltérésként), vagy (b) a lent megadott G jegytörzs szerinti leképezés kerül be, a `7327-11c` és `7327-11d` mérése után (addig a köztes állások és a képméret-függés nem bizonyított, és félkész dolog nem megy ki). **Mindkét mérés megvan (`job-917`, `job-918`): a (b) út járható, a G jegytörzs véglegesítve.**

#### Job-909 (`7327-12b`): meglévő szövegblokk szerkesztése és a Clear All

| Kocka | Előtte végrehajtott lépés | Kép, panel |
|---|---|---|
| `__10-11` | `kattint (138,275)` (Text) | Az „Edit Text” panel, bájtra azonos a `job-839 __10`-zel. |
| `__12-13` | `kattint (600,400)` | I-beam a (600,405) körül; „Clear All” aktív, „Apply” még tiltott. |
| `__14-15` | `gepel PicasaPy7327` | A szöveg a képen, lekerekített dobozban; „Apply” aktív. |
| `__16-17` | `kattint (88,406)` (Apply) | Alapjavítások, a szöveg a képen (betűpixelek y 402-407), „Undo” és „Redo” tiltott. |
| `__18-19` | `kattint (138,275)` (újranyitás) | A panel szerkesztő állapotban, **a meglévő szöveg a képen marad**, a „Type anywhere to add text” felirat nincs; **„Clear All” és „Apply” aktív**, „Copy Caption” tiltott. |
| `__20-21` | `kattint (620,405)` (a meglévő szövegre) | **A blokk kijelölődik**: vastag lekerekített keret, köré **forgatókorong** (osztásokkal, jobb szélén piros pontos fogantyúval, a pont közepe (708,405)); a szövegkurzor a „PicasaPy7327” szövegben, az ötödik betű után áll. |
| `__22-23` | `gepel Plusz` | A szöveg **a kurzorhoz szúródik be**: „PicasPluszaPy7327”; a doboz 10 képponttal szélesebb, a korong fogantyúja (718,405). |
| `__24-25` | `kattint (88,406)` (Apply) | A szöveg a képen, **egyetlen sor** („PicasPluszaPy7327”), „Undo” és „Redo” tiltott. |
| `__26-27` | `kattint (138,275)` | Szerkesztő panel, a szöveg a képen, „Clear All” és „Apply” aktív. |
| `__28-29` | `kattint (189,372)` (Clear All) | **A szöveg azonnal eltűnik a képről**, a „Type anywhere to add text” felirat visszajön (x 733-829, y 485-493); **„Clear All” tiltott, „Apply” AKTÍV marad**, a panel nyitva. |
| `__30-31` | `kattint (88,406)` (Apply) | Alapjavítások; a képterület az induló `__08`-cal **0 képpontban** tér el (a szöveg nyomtalanul eltűnt); „Undo” és „Redo” tiltott. |

**A záró fájlállapot.** `picasa.ini` (35 bájt): `[gray_ramp.jpg]`, `backuphash=36994`; **`text=` és `textactive=` nincs**. A `gray_ramp.jpg` 32 017 bájt és változatlan, `.picasaoriginals` nincs (Mentés nem volt).

**Eldőlt (909), nagy bizalommal:** a meglévő blokk újranyitáskor a képen marad; kattintásra kijelölődik (forgatókoronggal), a kurzor a kattintás helyére kerül, a gépelés oda szúr be, az Apply a blokkot helyben cseréli (egy sor, nincs ismétlődés); a Clear All a szöveget azonnal leveszi a képről, de az eszközben marad és az Apply aktív; a Clear All + Apply után a kép nyomtalanul az induló, az ini-szakaszban se `text=`, se `textactive=` nincs. **Nem dőlt el:** az ini a szerkesztett blokk után (a `text=` pontos tartalma: lépésenkénti ini nincs; vizuálisan egy blokk), a forgatókorong hatása (a `text=` negyedik pozíciómezője, a mért értékekben mindig `0.000000`), és hogy a Clear All utáni „Cancel” visszahozza-e a szöveget (a kérdéses sor `7327-12e`, `7327-12f`).

#### Job-910 (`7327-12`): a formázás megjegyzése Cancel után, Mentés

| Kocka | Előtte végrehajtott lépés | Kép, panel, ablak |
|---|---|---|
| `__14-15` | `gepel PicasaProba` | A szöveg a képen, „B”, „I”, „U” nem nyomott, bal igazítás. |
| `__16-17` | `kattint (185,202)` (B) | A „B” nyomott, a szöveg félkövér. |
| `__18-19` | `kattint (215,233)` (közép igazítás) | A „B” és a középre igazítás nyomott. |
| `__20-21` | `kattint (190,406)` (Cancel) | Alapjavítások, a szöveg eltűnt, kérdés nincs; „Undo” és „Redo” tiltott. |
| `__22-23` | `kattint (138,275)` (újranyitás) | **A „B” és a középre igazítás NYOMVA marad**; az üres kép közepén a „Type anywhere to add text” felirat **félkövér**; „Clear All” és „Apply” tiltott. |
| `__24-25` | `kattint (600,400)` | I-beam; „Clear All” aktív, „Apply” tiltott. |
| `__26-27` | `gepel PicasaPy7327` | A szöveg félkövéren a dobozban, „B” és középre igazítás nyomott, „Apply” aktív. |
| `__28-29` | `kattint (88,406)` (Apply) | A félkövér szöveg a képen; „Undo” és „Redo” tiltott. |
| `__30-31` | `billentyu ctrl+s` | „Save” ablak (ablaklista: „Save”), a `job-836 __26` ablakával azonos. |
| `__32-33` | `kattint (687,553)` („Save”) | Az ablak bezárult; **az Undo gomb „Undo Save” feliratú és aktív**, a „Redo” tiltott; az infosáv „20 KB”; a képterület az Apply utánitól csak a szöveg környezetében tér el (681 képpont, x 597-657, y 393-412: a fájlba égetett szöveg újrarajzolása). |

**A záró fájlállapot.** `gray_ramp.jpg` 20 613 bájt (09:44:25), `.picasaoriginals/gray_ramp.jpg` 32 017 bájt (az eredeti módosítási idővel). A fő `.picasa.ini` (35 bájt) csak `backuphash=26742`; **a `text=` és a `textactive=` a fő ini-ből eltűnt**. Az eredeti-mappa ini-je (230 bájt) szó szerint:

```
[gray_ramp.jpg]
moddate=f06c8b392f7bdd01
width=1024
height=256
text=1;135;12;PicasaPy7327;Times;0.316406,0.144531,0.033333,0.000000;v1,4294967295,4278190080,128.000000,1.000000,0.000000,1.000000,700,256,49152;;
textactive=1
```

**Eldőlt (910), nagy bizalommal:** (1) **a formázás Cancel után megmarad**: a panel a „B”-t és a középre igazítást nyomva mutatja, a következő szöveg ezzel készül (ini: súly `700`, a 8. mező `256`), a szöveg tartalma viszont nem marad meg. A `700` a félkövér súly; a `256` (`0x100`) a `picasa-ini-format.md` bináris-olvasatával egyezik (bit 8-15 = vízszintes igazítás, 1 = közép): **a bináris-olvasat első futásidejű igazolása**. (2) A szöveg Mentéskor a fő ini-ből az eredeti-mappa ini-jébe költözik (`text=`, `textactive=1`, mellé `moddate`, `width`, `height`), a fő ini-be csak a `backuphash` marad. (3) A Mentés megerősítése után az Undo gomb „Undo Save” (a Mentés visszavonható lépés). **Nem dőlt el:** az „Undo Save” gomb hatása (nem nyomták meg): `7327-12d`; az „I”, „U” és a jobb igazítás ini-kódja (a binárisból ismert, futásban nincs mérve).

#### Job-911 (`7327-8d`): a Crop első Apply után mentett téglalap

A `job-821` lépéssorának első fele: Crop (55,167), `huz (500,400)-(900,580)`: `__12-13` a kijelölés „Manual: 415 x 187”, Apply aktív; `__14-15` az Apply után vágott kép, csempe „Recrop”, „Undo Crop” aktív, „Redo” tiltott (a `job-821 __12`, `__14` kockáival egyező). A záró ini (a futás az Apply után 3 másodperccel véget ér):

```
[gray_ramp.jpg]
backuphash=29739
crop=rect64(370025009ebfdfff)
filters=crop64=1,370025009ebfdfff;
```

A `370025009ebfdfff` négy 16 bites törtkoordinátája (`0x3700`, `0x2500`, `0x9ebf`, `0xdfff`) a 1024×256 képen **220,003 · 37,001 · 634,994 · 223,9995**, vagyis a téglalap **414,99 × 186,999 képpont: 415 × 187**.

**Döntés (nagy bizalom): az első Apply után mentett `crop64` téglalap 187 képpont magas, nem 188.** A `job-821 __16` újranyitott kijelölésének „415 x 188” felirata ezért **nem a tárolt érték**: az újranyitás utáni megjelenítési úton keletkezik (a tárolt tört 37,0006 és 223,9995 képpontot ad, egy egyszerű lefelé/felfelé kerekítés a 187-et adja, a 188 oka ebből nem adódik). Az ini-oldalnak nincs tennivalója: a mai `encode_rect64` ugyanazt a törtet írja (kerekítéssel, nem csonkolással, `ini/rect64.py:42-48`: a 37/256 tört 9471,99, amit a Picasa is `0x2500`-ra, vagyis 9472-re ír). A felirat egy képpontos eltérése funkcióhatás nélküli, ezért nem vállalt.

#### Job-912 (`7327-9b`): a Vágás csempe aktív kiegyenesítés mellett, Escape

| Kocka | Előtte végrehajtott lépés | Kép, panel, ablak |
|---|---|---|
| `__10-13` | Straighten, `huz (680,863)-(740,863)` | Kiegyenesítés mód, majd a húzás utáni előnézet; bájtra azonos a `job-913 __10-13`-mal (fogantyú 689,5, illetve 738,5). |
| `__14-15` | `kattint (875,863)` (APPLY) | Alapjavítások, kiegyenesített kép, „Undo Straighten” aktív. |
| `__16-17` | `kattint (55,167)` (Crop) | **A „Crop Photo” panel nyílik meg, felugró ablak nélkül** (az ablaklista végig csak „Picasa 3”), **figyelmeztető szöveg nélkül**: a panel a tilt nélküli Crop panelhez (`job-911 __10`) képest csak a három arány-bélyegkép tartalmában tér el (azok a kiegyenesített képet mutatják, 4 728 képpont a y 267-286 sávban). „Apply”, „Reset”, „Preview” tiltott, „Cancel” aktív. |
| `__18-19` | `billentyu Escape` | Alapjavítások; a képterület az Apply utánival **0 képpontban** azonos, „Undo Straighten” aktív: az Escape a Crop eszközt Cancel-ként zárja, a kiegyenesítést nem vonja vissza. |

A záró ini (70 bájt): `filters=tilt=1,0.391249,0.000000;`, `backuphash=27090`.

**Eldőlt (912), nagy bizalommal:** aktív (frissen alkalmazott) kiegyenesítés mellett a Vágás csempére **nincs se felugró ablak, se figyelmeztető szöveg a panelben a megnyitáskor**; az Escape Cancel-ként zárja az eszközt. Ez ellentmond a PicasaPy mai viselkedésének (a panel a figyelmeztetést mindig mutatja: I jegytörzs). **Nem dőlt el:** hogy az eredeti a figyelmeztetést (`IDS_WARN_CROP_ACCURACY`) a megnyitás UTÁN (a kijelölés húzásakor vagy az Apply-kor) mutatja-e; a lépéssor Crop-húzást nem tartalmazott: `7327-9c`.

#### Job-913 (`7327-9`): a Kiegyenesítés újranyitása Apply után, második érték, Mentés

| Kocka | Előtte végrehajtott lépés | Kép, panel, ablak |
|---|---|---|
| `__10-15` | Straighten, `huz (680,863)-(740,863)`, APPLY | Bájtra azonos a `job-912 __10-15`-tel (fogantyú 738,5; Apply után „Undo Straighten”). |
| `__16-17` | `kattint (138,160)` (újranyitás) | Kiegyenesítés mód; **a fogantyú a sáv KÖZEPÉN (x 683-696, közép 689,5)**, az előző érték (738,5) nem töltődik vissza; **az alapkép a már kiegyenesített kép** (a friss `__10`-től a képterület szinte teljes egészében eltér). |
| `__18-19` | `huz (740,863)-(640,863)` | A fogantyú 638,5-nél (x 632-645); az előnézet a második forgatást mutatja a már kiegyenesített képen. |
| `__20-21` | `kattint (875,863)` (APPLY) | Alapjavítások; „Undo Straighten” aktív, „Redo” tiltott; a kép a két forgatás egymás utáni eredménye (a képterület középső sorának szürkeszintje a bal szélen 5-ről 55-re, a jobb szélen 248-ról 196-ra változott; az első Apply után 33 és 219). |
| `__22-23` | `billentyu ctrl+s` | „Save” ablak (ablaklista: „Save”). |
| `__24-25` | `kattint (687,553)` („Save”) | Az ablak bezárult; **az Undo gomb „Undo Save”**, a „Redo” tiltott; a képterület a Mentés előttitől legfeljebb 3 szintre tér el (átlagos eltérés 0,67). |

**A záró fájlállapot.** `gray_ramp.jpg` 23 239 bájt (09:55:10), `.picasaoriginals/gray_ramp.jpg` 32 017 bájt (az eredeti módosítási idővel). A fő `.picasa.ini` (35 bájt) csak `backuphash=37010` (nincs `filters=`). Az eredeti-mappa ini-je (142 bájt) szó szerint:

```
[gray_ramp.jpg]
filters=tilt=1,0.391249,0.000000;tilt=1,-0.399233,0.000000;
moddate=3c9121ba307bdd01
width=1024
height=256
textactive=0
```

**A csúszka és az ini-szám összefüggése, második pontból.** Az első húzás (egér x=740) `0,391249`-et adott (négy felvételben azonosat), a második (egér x=640) `-0,399233`-at. A két pontra illeszkedő egyenes: `tilt = (x - 690,505)/126,505` (meredekség 0,00790482 /képpont), és mindkét mért érték a `(x - 690,5)/126,5` képlettől 0,0001 alatt tér el (0,391304 és -0,399209). A **126,5 az 253/2**: az eredeti csúszka kattintható foglalata 253 képpont (`EditorToolBar.qml:83-86`), vagyis az érték a **foglalat teljes 253 képpontján át** fut a ±1-ig, és a fogantyú KÖZEPE jár végig rajta (nem a 253-16 képponton). A nulla a foglalat közepe (690,5). A végállás (±1) közvetlenül nincs mérve (`7327-9d`), a két pontra illesztett egyenes linearitása sem több ponttal ellenőrzött.

**Eldőlt (913), nagy bizalommal:** (1) az **újranyitott Kiegyenesítés a csúszkát a KÖZÉPEN indítja** (0 érték), az Apply-kor mentett érték nem töltődik vissza, az alapkép a már kiegyenesített kép; (2) a **második Apply ÚJ `tilt` tagot fűz a lánchoz** (két tag az ini-ben, mindkettő a saját csúszkaértékével), nem cseréli az elsőt; (3) a Mentés megerősítése után: a kép újraírva (23 239 bájt), biztonsági másolat megvan, a lánc az eredeti-mappa ini-jébe költözik (mindkét `tilt` taggal, `moddate`, `width`, `height`, `textactive=0`), a fő ini-ben csak a `backuphash` marad, az Undo gomb „Undo Save”. **Nem dőlt el:** a csúszka végállása (±1) és linearitása (`7327-9d`); a két `tilt` tagú lánc Undo/Redo-ja (`7327-9e`); az index (a `db3`-ban nincsenek `imagedata_*.pmp` oszlopok: a Picasa leállítása kell, `7327-9f`).

#### Összevetés a mai PicasaPy-val (kódolvasás, futtatás nélkül)

| Eredeti (mérés) | Nálunk (fájl:sor) | Ítélet |
|---|---|---|
| Ecsetméret: R = 3,0 / 24,0 / 97,0 képernyő-képpont (z = 0,97), a forráson 3,1 / 24,7 / 100, a kép méretétől független, a nagyítással arányos | `edit_controller_shared.py:372-373` (alap 20, osztó 1000), `edit_controller_retouch_mixin.py:64-70`, `:234` (relatív sugár), `PhotoViewerRetouchArea.qml:43-47` (`arány × min(szélesség, magasság)`), `render/retouch.py:68-71` (`round(sugár × rövidebb oldal)`) | **Eltérés** (G jegytörzs); a #7379 változata (494/50) sem igazolt. |
| A retusálás visszavonása után az Újra letiltott, csupasz „Redo” felirattal | `edit_controller_history_mixin.py:60-70` (`undo()` minden műveletet a redo-verembe tol, a retus-lépést is), `:26` (`canRedo`), `edit_action_names.py:82` (`Retouches` név); a megerősítés `PhotoViewerEditorPanel.qml:119-130`, `PhotoViewerContextActions.qml:244-255` (`onConfirmed: editController.undo()`) | **Eltérés**: nálunk a megerősített visszavonás után „Redo: Retouches” aktív marad (H jegytörzs). |
| Retusálás Apply: a fájl és a `.picasaoriginals` másolata azonnal megíródik, az infosáv mérete frissül | `edit_controller_retouch_mixin.py:207-222` (az Apply csak az ini-láncot írja, képfájlt nem) | **Fájl-szintű eltérés** (a D jegytörzs része, lent); látható nyoma az infosáv mérete az Apply után. |
| Aktív kiegyenesítés mellett a Vágás csempe figyelmeztetés nélkül nyílik | `EditorCropPanel.qml:71-87` (`cropStraightenWarning`, `visible: panel.straightenActive`), `PhotoViewerEditWorkflow.qml:582,600` | **Eltérés** (I jegytörzs). |
| Kiegyenesítés újranyitása: a csúszka a közepén indul, az alapkép a kiegyenesített kép, a második Apply új `tilt` tagot fűz | `PhotoViewerEditWorkflow.qml:578` (`csuszkaErtek = tiltParam`: a mentett érték töltődik vissza), `edit/session_effects.py:22-34` (`set_tilt`: „beállítása vagy cseréje, a láncban legfeljebb egy lehet”), `edit_controller_effects_finetune_mixin.py:80-92` | **Eltérés** (J jegytörzs). |
| A csúszka foglalata 253 képpont, a fogantyú KÖZEPE járja végig; érték = (x - 690,5)/126,5 | `PicasaSlider.qml:234-236` (a fogantyú x-e `visualPosition × (availableWidth - width)`, vagyis a középpont útja 253-16 = 237 képpont), `EditorToolBar.qml:83-86,215-216` (253 széles sáv, 16 széles fogantyú) | **Eltérés** (J jegytörzs): ugyanarra az egérmozgatásra nálunk 6,7%-kal nagyobb érték (0,418 a mért 0,391 helyett, +49,5 képpontos húzásnál). Egéresemény-próba nem készült. |
| A formázás (B, igazítás) Cancel után megmarad | `edit_controller_text_mixin.py:426-436` (`exitTextTool` a stílust nem nullázza), `:395-406` (`enterTextTool` csak meglévő blokkból tölt stílust) | Egyezik (kódolvasás, futás nélkül). |
| Clear All: a szöveg azonnal eltűnik a képről, az eszköz nyitva marad, az Apply aktív | `edit_controller_text_mixin.py:586-607` (`clearText`: azonnali, végleges, az ini-t ír, „Mégse” nem hozza vissza) | **Kérdéses**: a Clear All utáni Cancel hatása nincs mérve (`7327-12f`), ezért jegytörzs még nincs. |
| Mentés után az Undo gomb „Undo Save” | `edit_action_names.py` (nincs „save” művelet), `_push_undo` hívások (nincs „save”); az „Undo Save” csak a Revert ablakban él (`SaveDialogs.qml:253-268`) | **Eltérés a felirat/állapot szintjén**; a gomb hatása nincs mérve (`7327-12d`), ezért jegytörzs még nincs. |
| Mentéskor a `text=`, `textactive=` (és `width`, `height`) az eredeti-mappa ini-jébe költözik | `edit/save_operations.py:132-143` (az eredeti-mappa ini-jébe csak `filters=` és `moddate` kerül) | **Fájl-szintű eltérés** (a D jegytörzs kiegészítése). |

#### Új fejlesztői jegytörzsek (job-907..913): G, H, I, J

**(G) Retusálás ecsetméret: a kör és a folt sugara az eredeti szerint (jegy: #7379 helyett/mellett; a mérés kész: `job-917`, `job-918`; VÉGLEGESÍTVE)**

> **Mi a hiba:** a Retusálás ecsetkör mérete a kép rövidebb oldalához arányos nálunk (`érték/1000 × rövidebb oldal`; a #7379 ágán a `main` 20/1000-es változata maradt, a 494-es osztó nem került be). Az eredeti sugara forrásképi képpont, a kép méretétől független, a megjelenített kör a nagyítással arányos, és a csúszka LINEÁRISAN szabályozza; a mérés a csúszka két végén és két köztes pontján, három képméreten és három nagyításon egyezik.
>
> **Eredeti:** `job-908 __14` (bal vég: R = 3,0), `job-917 __14` (a fogantyú a futás 24,2%-án: R = 23,0), `job-917 __20` (73,5%-án: R = 71,0), `job-908 __20` (jobb vég: R = 97,0, z = 0,97), `job-918 __18` (jobb vég, 768×512-es kép, z = 1,07: R = 107,0), `job-918 __24` (bal vég: R = 3,0); induláskor (a csúszka érintetlen, a fogantyú középen): `job-907 __12` R = 24,0 (z = 0,97), `job-918 __12` R = 27,0 (z = 1,07), a job #314 képernyőképe R = 20,0 (1024×1024-es kép, z = 0,80). Bináris: `0x0060b430` `R_képernyő = max(3·max(z,1), min(100, min(w,h)/2)·s·z)`, `0x0060a980` `R_forrás = R_képernyő/z`, `0x0060a700`/`0x0060a763` induló `s = 0,25`, `0x0060b350` a csúszka-esemény írja `s`-t (`forras-audit-5186-2.md`, #5975).
>
> **Nálunk:** `edit_controller_shared.py:377-378` (`_DEFAULT_BRUSH_SIZE = 20`, `_BRUSH_SIZE_TO_RELATIVE_DIVISOR = 1000.0`), `edit_controller.py:278` (a kezdőérték), `edit_controller_retouch_mixin.py:70` és `:234` (a relatív sugár), `PhotoViewerRetouchArea.qml:43-47` (a kör sugara `arány × min(szélesség, magasság)`), `render/retouch.py:68-71` (`round(sugár × rövidebb oldal)`), `EditorRetouchPanel.qml:84-92` (`from: 1; to: 100`).
>
> **Teendő:** (1) a csúszka `t ∈ [0,1]` helyzetéből (a fogantyú KÖZEPÉNEK helye a futásban) `s = t`: lineáris (MÉRT: két köztes pont és mindkét vég; az `s = t²` és az `s = 1,5·t - 0,5` cáfolt). (2) A kör sugara a képernyőn `R = max(3, 100·s·z)` képpont (`z` a nézet nagyítása, 1,0 = 100%), a forrásképi sugár `r = R/z`; a kép méretétől (szélesség, magasság, rövidebb oldal) NEM függ. A bináris minimuma `3·max(z,1)`: z ≤ 1-nél azonos, z = 1,07-nél a különbség 0,21 képpont, a mérés ezt nem választja szét. (3) **Induláskor `s = 0,25`** (R = 24,25 z = 0,97-nél, 25 forrásképpont), miközben a csúszka fogantyúja a KÖZEPÉN áll (t = 0,5): a csúszka megérintéséig az induló `s` él, megérintés után `s = t` (a mai 20/1000-es kezdőérték nem marad). (4) A mentett folt `retouch=2` tokenje relatív sugarat tárol (`ini/retouch.py`): a létrehozáskor `r / a kép rövidebb oldala` legyen, hogy a round-trip formátum ne változzon; a folt képpontsugara így az előnézeti gyűrű forrásképi sugarával egyezik. (5) A #7379 494-es osztója és a mai 1000-es osztó nem marad. **Nem része:** a folt belső keverése, a csúszka megjelenése. **Nincs mérve, ne általánosítsd:** a gyűrű kis képen (a nézet rövidebb oldala 200 képpont alatt: a bináris `min(100, rövidebb/2)` kapuja), a csúszka állása és az ecsetméret a Retusálás ÚJRANYITÁSAKOR (a mai viselkedés marad: `7327-11e`), a középállás pontos értéke húzás után (a lineáris illesztésből R = 48,5 z = 0,97-nél: `7327-11e`), az 1:1 nagyítás.
>
> **Kész, ha:** (1) a renderelt próba a kört a `job-908 __14`, `job-917 __14`, `job-917 __20` és `job-908 __20` kockájával veti össze ugyanazon a képen és nagyításon (a fehér képpontpárok távolsága 6, 46, 142 és 194, ±1 képpont); (2) a 768×512-es képen z = 1,07-nél a `job-918 __12`, `__18` és `__24` kockájával (54, 214 és 6, ±1); (3) induláskor R = 24,0 (z = 0,97) és a fogantyú középen; (4) a mentett folt képpontsugara a kép rövidebb oldalától független (két eltérő képméreten ugyanaz a csúszkaérték ugyanazt a forrásképi sugarat adja); (5) a szomszéd panelek (Vörösszem, Szöveg) képe változatlan.

**(H) Retusálás visszavonása után az Újra letiltott marad (jegy: #7379 mellett vagy külön)**

> **Mi a hiba:** az eredetiben a „Undo Retouches” megerősített visszavonása után az „Undo” és a „Redo” egyaránt tiltott, a felirat csupasz („Undo”, „Redo”); nálunk a megerősített visszavonás a redo-verembe tolja a lépést, így „Redo: Retouches” aktív marad.
>
> **Eredeti:** `job-907 __24` (a megerősített „Undo” után mindkét gomb tiltott, „Redo Retouches” nincs), `__26`-`__29` (a tiltott Redo kattintása és a Ctrl+S hatástalan, a kocka bájtra azonos az `__24`-gyel); a „No” ág (`__20`) semmit nem változtat (a képterület az `__16`-tal 0 képpontban azonos).
>
> **Nálunk:** `edit_controller_history_mixin.py:60-70` (`undo()` minden műveletet, a „retouch”-ot is, a `_redo_stack`-re tol), `:26` és `:36-38` (`canRedo`, `redoAction`), `edit_action_names.py:82`; a megerősítés `PhotoViewerEditorPanel.qml:119-130` és `PhotoViewerContextActions.qml:244-255`.
>
> **Teendő:** a megerősített retusálás-visszavonás után a redo-verem NE kapjon bejegyzést (az Újra tiltott, csupasz „Redo”); a „No” ág és a többi művelet visszavonása változatlan. A Vörösszem ugyanezt a komponenst használja, de annak eredeti viselkedése nincs mérve (`7327-10`), arra ne terjeszd ki.
>
> **Kész, ha:** (1) retusálás Apply, Undo, „Undo” után az „Undo” és a „Redo” tiltott, a feliratuk csupasz; (2) a „No” után a kép és a gombok az Undo előttivel azonosak; (3) a renderelt próba a bal panelt a `job-907 __24`-gyel veti össze; (4) más művelet (pl. Crop) Undo-ja után a Redo továbbra is aktív.

**(I) Vágás panel: aktív kiegyenesítés mellett nincs figyelmeztetés a megnyitáskor (jegy: külön)**

> **Mi a hiba:** a Vágás panel mindig kiírja a Kiegyenesítés-figyelmeztetést, ha a képen van kiegyenesítés; az eredetiben a Vágás csempére aktív kiegyenesítés mellett nincs se ablak, se panelszöveg.
>
> **Eredeti:** `job-912 __16` (a Vágás csempe után a „Crop Photo” panel figyelmeztetés nélkül; az `allapot.json` ablaklistája végig csak „Picasa 3”), a panel a tilt nélküli `job-911 __10`-től csak a bélyegképek tartalmában tér el; `__18` (az Escape Cancel-ként zárja az eszközt, a kiegyenesítés megmarad).
>
> **Nálunk:** `EditorCropPanel.qml:71-87` (`cropStraightenWarning`, `visible: panel.straightenActive`), `PhotoViewerEditWorkflow.qml:582,600` (`straightenActive = tiltParam !== 0`). Védőteszt: `tests/app/qml_functional/test_aa_kilepesi_utak_3014.py` (említi a `cropStraightenWarning` elemet; a módosítással igazítandó).
>
> **Teendő:** a Vágás panel megnyitásakor ne jelenjen meg a figyelmeztetés (a `cropStraightenWarning` sor kerüljön ki a megnyitás állapotából). **Nem része:** hogy az eredeti a figyelmeztetést a megnyitás UTÁN (húzáskor vagy Apply-kor) kiírja-e: ez a `7327-9c` kérdése, addig se új figyelmeztetést ne adj hozzá, se a szöveget ne töröld a forrásból (a `IDS_WARN_CROP_ACCURACY` szövege a `.ts` fordításokban marad).
>
> **Kész, ha:** (1) mentett kiegyenesítésű képen a Vágás csempe után a panel figyelmeztető sor nélkül nyílik; (2) a renderelt próba a panelt a `job-912 __16`-tal veti össze (a bélyegképek kivételével képpontra egyezik); (3) az Escape a kiegyenesítést megtartva zár (`__18`); (4) a Vörösszem „Info” ablakához (A jegytörzs) nem nyúltál.

**(J) Kiegyenesítés: újranyitáskor a csúszka közepén indul, a második Apply új `tilt` tagot fűz, és a csúszka 253 képpontos skálája (jegy: külön)**

> **Mi a hiba:** (1) az eredeti Kiegyenesítés újranyitáskor a csúszkát a KÖZEPÉN (0 érték) indítja a már kiegyenesített képen, és a második Apply új `tilt` tagot fűz a lánchoz; nálunk az újranyitott csúszka a mentett értéket veszi fel, és az Apply a meglévő tagot cseréli. (2) Az eredeti csúszka értéke `(x - 690,5)/126,5` (a foglalat teljes 253 képpontján át fut); nálunk a fogantyú középpontja csak 237 képpontot fut be.
>
> **Eredeti:** `job-913 __16` (újranyitás: a fogantyú közepe 689,5, az alapkép a kiegyenesített kép), `__18` (a második húzás a fogantyút 638,5-re viszi), a záró eredeti-mappa ini `filters=tilt=1,0.391249,0.000000;tilt=1,-0.399233,0.000000;` (két tag); a csúszka-érték mérése: a 740 és 640 egérpozíció `0,391249` és `-0,399233`, a két pontra illesztett meredekség 2/253 /képpont.
>
> **Nálunk:** `PhotoViewerEditWorkflow.qml:578` (`editorToolBar.csuszkaErtek = hostEditController.tiltParam`), `edit/session_effects.py:22-34` (`set_tilt`: csere, legfeljebb egy tag), `edit_controller_effects_finetune_mixin.py:80-92` (`setTilt`), `PicasaSlider.qml:234-236` és `EditorToolBar.qml:83-86,215-216` (253 széles sáv, 16 széles fogantyú: a középpont útja 237).
>
> **Teendő:** (1) a Kiegyenesítés eszköz minden megnyitáskor 0 értékről induljon, az alapkép a már alkalmazott lánc eredménye; (2) az Apply új `tilt` tagot fűzzön a lánc végére (a nulla értékű Apply ne írjon tagot, ha az eredeti ezt így teszi: ez nincs mérve, ne általánosítsd); ellenőrizd, hogy a render-lánc két `tilt` tagot sorban alkalmaz-e. (3) A csúszka értéke `(x - 690,5)/126,5` legyen a mért 253 képpontos foglalaton (a fogantyú KÖZEPE járja végig a teljes 253 képpontot). **Nem része:** az Undo/Redo viselkedése két `tilt` tagnál (`7327-9e`), a csúszka végállása (±1, `7327-9d`).
>
> **Kész, ha:** (1) kiegyenesített képen az újranyitott eszköz fogantyúja középen áll; (2) két Apply után két `tilt` tag van az ini-ben (a `job-913` értékeivel, `0,391249` és `-0,399233`, ha ugyanazt az egérmozdulatot adjuk); (3) egéreseménnyel a 740-es x-re húzva a csúszka értéke `0,3913 ± 0,001`; (4) a renderelt próba az újranyitott eszközt a `job-913 __16` és `__18` képkockával veti össze; (5) a Vágás panel és a Vörösszem „Info” ablaka változatlan.

**(K) Lezárva a `job-919`-cel, jegytörzs: N („Job-917..925”).** A Mentés után az Undo gomb „Undo Save” feliratú (`job-910 __32`, `job-913 __24`, `job-925 __18`), és a gomb hatása mért: az utolsó Mentés visszavonása a szerkesztések megtartásával (`job-919`). A **D jegytörzs kiegészítése** (fájl-szintű): a retusálás fájlírása az Apply-kor történik (908), és a szöveg Mentéskor a fő ini-ből az eredeti-mappa ini-jébe költözik (910: `text=`, `textactive=1`, `width`, `height`); a kiegyenesítés láncát a mai kód is az eredeti-mappa ini-jébe teszi (913-mal egyezik), a retus-tokent a fő ini-ben meg kell tartani (D szerint). Az „Undo Save” a Mentéskor az eredeti-mappa ini-jébe költözött kulcsokat (`text=`, `textactive=`) visszahozza a fő ini-be, a `.picasaoriginals` másolatot törli (`job-919`).

#### Javított lépéssorok (job-907..913 nyomán)

A javított lépéssorok a munkafa `.tmp/javitott-lepesek2/` mappájában vannak; a közös bevezető (négy `var 10`, `kattint (80,215)`, `var 4`, `dupla (340,272)` vagy a megadott, `var 4`) után:

| Fájl | Lépések | Mit dönt el |
|---|---|---|
| `7327-11c` (26) | Retouch; a „Brush Size” fogantyú húzása 134 → 107 (t ≈ 0,25), két kattintás; 107 → 160 (t ≈ 0,75), két kattintás; görgő (780,490) +5; kattintás (600,450) | az ecsetkör mérete két köztes csúszkaállásnál (az `s = t²` és az `s = 1,5·t - 0,5` alak elválasztása: R 6,1 vagy 3,0, illetve 54,6 vagy 60,6 képpont z = 0,97-nél), és a nagyítással arányosság egy másik z-n (a „Zoomed to” jelző olvasható) |
| `7327-11d` (24) | a rács 3. képe (664,272), a 768×512-es `rgb_gradient.jpg`; Retouch; alap, jobb vég (192), bal vég (78): mindháromnál kör | a kép szélességétől vagy rövidebb oldalától függés (768 széles, 512 rövidebb oldal; z = 100% vagy a jelző szerint): abszolút forrásképpont esetén R = 25 / 100 / 3 (z = 1) |
| `7327-12d` (24) | Text, szöveg, Apply, `ctrl+s`, „Save” (687,553); Undo (70,380); Redo (207,380); kimenet: ini, képmappa | az „Undo Save” gomb hatása (a fájl, a `.picasaoriginals`, az ini, a szöveg sorsa) és a Redo utána |
| `7327-12e` (32) | Text, `PicasaPy7327`, Apply; újranyitás, kattintás (620,405), „Plusz”, Apply; újranyitás, kattintás, a forgatókorong fogantyújának húzása (718,405 → 718,445), Apply; kimenet: ini | a `text=` a helyben szerkesztett blokk után (egy blokk-e), és a forgatókorong hatása (a pozíciómező negyedik száma) |
| `7327-12f` (24) | Text, `PicasaCancelProba`, Apply; újranyitás, „Clear All” (189,372), „Cancel” (191,406); újranyitás | a Clear All utáni Cancel visszahozza-e a szöveget (nálunk a `clearText` azonnali és végleges) |
| `7327-9c` (20) | Straighten, húzás 680 → 740, APPLY; Crop (55,167), húzás (500,400)-(900,580), Apply (84,403) | a Vágás-figyelmeztetés a megnyitás UTÁN (húzáskor, Apply-kor ablak vagy szöveg) |
| `7327-9d` (20) | Straighten, húzás 690 → 540 (a bal vég túl), APPLY; újranyitás, húzás 690 → 850, APPLY; kimenet: ini | a csúszka két végállása (a feltevés: `-1,000000` és `1,000000`), a két `tilt` tag az ini-ben |
| `7327-9e` (28) | a `job-913` két Apply-ja, majd `Undo`, `Undo`, `Redo`, `Redo` | a két `tilt` tagú lánc Undo/Redo-ja (feliratok, kép, ini) |
| `7327-9f` (20) | Straighten, húzás 680 → 740, APPLY, `ctrl+s`, „Save”, `picasa leallit`; kimenet: `db3` | az index (`imagedata_*.pmp`) a Mentés után; a 908 és 913 `db3`-ja csak bélyegkép-adatbázist tartalmazott |

**Állapot (job-917..925):** mind a kilenc sor lefutott és kiértékelt (lásd „Job-917..925”); a megmaradt hiányokhoz öt új sor készült (`7327-11e`, `7327-12g`, `7327-12h`, `7327-12i`, `7327-9g`), a `7327-10` pedig vörösszemes tesztképre vár.

### Job-917..925 (a harmadik javított kör: Retusálás ecsetméret, Szöveg, Vágás és Kiegyenesítés)

**Bemenet és olvasat.** Kilenc felvétel (1280×1024): `job-917` = `7327-11c`, `job-918` = `7327-11d`, `job-919` = `7327-12d`, `job-920` = `7327-12e`, `job-921` = `7327-12f`, `job-922` = `7327-9c`, `job-923` = `7327-9d`, `job-924` = `7327-9e`, `job-925` = `7327-9f`. Lépés/kocka: 26/27, 24/25, 24/25, 32/33, 24/25, 20/21, 20/21, 28/29, 20/21; a `kepernyo__NN` az (NN-1). lépés utáni állapot. Az `allapot.json` OCR-mezője mind a kilencben üres, ezért a feliratokat és a gombállapotokat a képekből olvastam: a döntő kockákat egyenként megnéztem, az azonosakat md5-vel csoportosítottam. A köröket és a csúszkafogantyúkat képpontosan mértem (a `job-907`/`job-908` módszerével: a gyűrű két-két képpontos fehér párjának közepe; a fogantyú világos testének oszlopai), a módszert a `job-907 __12` (R = 24,0), a `job-908 __14` (R = 3,0) és `__20` (R = 97,0) kockáján újra lefuttatva az eredmény azonos. A felugró ablakok: `Save` (919 `__18-19`, 925 `__16-17`); a többi felvételben végig csak „Picasa 3”. A fájlállapot a futás VÉGÉN készül, lépésenkénti fájlállapot nincs.

#### Job-917 és job-918 (`7327-11c`, `7327-11d`): az ecsetméret leképezése

**Job-917** (a 1024×256-os `gray_ramp.jpg`, „Zoomed to 97%”):

| Kocka | Előtte végrehajtott lépés | Kép, panel |
|---|---|---|
| `__10-11` | `kattint (55,275)` (Retouch) | Friss panel; a fogantyú a sáv KÖZEPÉN (közép 133,5). |
| `__12-13` | `huz (134,277)-(107,277)` | A fogantyú közepe 105,5 (a futás 24,2%-a). |
| `__14-15` | `kattint (600,450)` | **Gyűrű R = 23,0** (fehér párok x 576,5 és 622,5, y 426,5 és 472,5: 2R = 46,0). |
| `__16-17` | `kattint (660,450)` | Folt; a gyűrű az egér körül ugyanakkora (R = 23,0). |
| `__18-19` | `huz (107,277)-(160,277)` | A fogantyú közepe 158,5 (a futás 73,5%-a). |
| `__20-21` | `kattint (600,450)` | **Gyűrű R = 71,0** (x 528,5 és 670,5, y 378,5 és 520,5: 2R = 142,0). |
| `__22-23` | `kattint (660,450)` | Második folt, a gyűrű az egér körül R = 71,0. |
| `__24-25` | `gorget (780,490,5)` | **A görgő nem hatott**: a megjelenített kép mérete változatlan (a képterület magassága 250 képpont mindkét kockán, a szélessége csak a keretvonal miatt 992 és 990), a „Zoomed to” jelző eltűnt, a gyűrű az egér körül R = 71,5 (±0,5, a gyűrű részben kitakart). |
| `__26-27` | `kattint (600,450)` | R = 71,0: a görgő a Retusálás eszközben sem nagyít, sem méretet nem állít. |

**Job-918** (a 768×512-es `rgb_gradient.jpg`, „Zoomed to 107%”, a képterület 824×547 képpont: a Retusálás a képet a nézethez illesztve 107%-ra NAGYÍTJA):

| Kocka | Előtte végrehajtott lépés | Kép, panel |
|---|---|---|
| `__10-11` | `kattint (55,275)` | Friss panel, a fogantyú középen (133,5). |
| `__12-13` | `kattint (600,450)` | **Indulóméret: R = 27,0** (x 572,5 és 626,5, y 422,5 és 476,5), a csúszka még érintetlen. |
| `__14-15` | `kattint (660,450)` | Folt; a gyűrű az egér körül R = 27,0. |
| `__16-17` | `huz (134,277)-(192,277)` | A fogantyú a jobb végén (közép 187,0). |
| `__18-19` | `kattint (600,450)` | **Jobb vég: R = 107,0** (x 492,5 és 706,5). |
| `__20-21` | `kattint (660,450)` | Folt. |
| `__22-23` | `huz (192,277)-(78,277)` | A fogantyú a bal végén (közép 79,5). |
| `__24-25` | `kattint (600,450)` | **Bal vég: R = 3,0** (x 596,5 és 602,5, y 446,5 és 452,5). |

##### KIEMELT: az eredeti Retusálás-ecset leképezése, LEZÁRVA (nagy bizalom)

A fogantyú helyzete `t = (közép - 79,5)/107,5` (a futás két vége a `job-918 __24` és `__18` fogantyújából, a `job-908` 80,5-ös és 187,5-ös fogantyúdobozával azonos eljárással: ott 16 képpontos doboz, itt a 14 képpontos test; a különbség fél képpont). `z` a „Zoomed to” jelzőn olvasható egész százalék.

| Pont | Kép | z | t | R mért | 100·t·z | R/z |
|---|---|---|---|---|---|---|
| bal vég (`job-908 __14`; `job-918 __24`) | 1024×256; 768×512 | 0,97; 1,07 | 0 | 3,0; 3,0 | 0 (a 3 képpontos minimum dominál) | |
| `job-917 __14` | 1024×256 | 0,97 | 0,242 | **23,0** | 23,5 | 23,7 |
| `job-917 __20` | 1024×256 | 0,97 | 0,735 | **71,0** | 71,3 | 73,2 |
| jobb vég (`job-908 __20`; `job-918 __18`) | 1024×256; 768×512 | 0,97; 1,07 | 1 | 97,0; 107,0 | 97,0; 107,0 | 100,0; 100,0 |
| **indulás, a csúszka érintetlen, a fogantyú KÖZÉPEN** (`job-907 __12`; `job-918 __12`; job #314) | 1024×256; 768×512; 1024×1024 | 0,97; 1,07; 0,80 | (0,5) | 24,0; 27,0; 20,0 | 24,25; 26,75; 20,0 | 24,7; 25,2; 25,0 |

**Mit mond ki:**

1. **A csúszka-állás és az `s` mező viszonya LINEÁRIS: `s = t`** (a bináris képlet `R = 100·s·z`-ben). A két köztes pont (R = 23,0 és 71,0) a lineáris `97·t`-től 0,5 képponton belül tér el (23,5 és 71,3); a két köztes pontra illesztett egyenes `R = 97,4·t - 0,6`, a két végpont (3 és 97) rajta van. A `job-908`-ban jelölt két alak mindkettő cáfolt: az `s = t²` 5,7 és 52,4 képpontot adna, az `s = 1,5·t - 0,5` 3 (minimum) és 58,4 képpontot.
2. **Az indulóméret NEM a csúszka állásából jön.** A fogantyú induláskor a KÖZÉPEN áll (t = 0,5), a lineáris leképezés ehhez R = 48,5-et adna (z = 0,97); a mért indulókör mégis R = 24,0 (s = 0,25, a konstruktor kezdőértéke, `0x0060a763`). Az eredeti tehát a csúszka megérintéséig `s = 0,25`-tel dolgozik, megérintés után `s = t`. A korábbi „az alap a csúszka közepe (R = 23,8)” sor ezzel **helyesbítve**: a középállás húzás UTÁNI értéke (R = 48,5, `s = 0,5`) nincs közvetlenül mérve, csak a lineáris illesztésből következik (`7327-11e`).
3. **A kép méretétől független.** A forrásképi sugár az induló csúszkával 24,7 (1024×256, z = 0,97), 25,2 (768×512, z = 1,07) és 25,0 (1024×1024, z = 0,80, job #314), a jobb végen 100,0 és 100,0: négyszeres rövidebb oldal (256 és 1024), eltérő szélesség (768 és 1024) mellett azonos. **A #7379 494-es osztója és a mai 1000-es osztó is a rövidebb oldalhoz mér, mindkettő cáfolt.**
4. **A megjelenített kör a nagyítással arányos**: `R_képernyő = 100·s·z`, három nagyításon (0,80; 0,97; 1,07) 0,3 képponton belül egyezik (a jobb végen pontosan: 97,0 és 107,0). A jobb vég sugara pontosan `100·z` a jelzőn olvasható egész százalékkal (97,0 és 107,0). A 3 képpontos minimum mindkét nagyításon 3,0; a bináris `3·max(z,1)` alakja z = 1,07-nél 3,21-et adna, ami a mérés (egész képpontos gyűrű, 2R = 6) pontosságán belül nem választható el a 3,0-tól.
5. **Nincs mérve (és a jegytörzs kimondja):** a gyűrű kis képen (a bináris `min(100, rövidebb/2)` kapuja: mindhárom mért kép nézete 200 képpont fölött van); a Retusálás újranyitáskori csúszka- és ecsetállapota; a csúszka pontos középállása húzás után; az 1:1 nagyítás. A görgő a Retusálás eszközben nem nagyít, ezért a nagyítás-sorozat egy futáson belül nem végezhető.

#### Job-919 (`7327-12d`): az „Undo Save” gomb hatása

| Kocka | Előtte végrehajtott lépés | Kép, panel, ablak |
|---|---|---|
| `__10-15` | Text, `kattint (600,400)`, `gepel PicasaUndoSave` | A szöveg a képen (a `job-909` útja). |
| `__16-17` | `kattint (88,406)` (Apply) | Alapjavítások, a szöveg a képen, „Undo” és „Redo” tiltott. |
| `__18-19` | `billentyu ctrl+s` | „Save” ablak („Save changes to disk? A backup of this file will be made.”, a `job-910` ablakával azonos). |
| `__20-21` | `kattint (687,553)` („Save”) | Az ablak bezárult; **az Undo gomb „Undo Save” és aktív**, a „Redo” tiltott; a szöveg a képen (a fájlba égetve). |
| `__22-23` | `kattint (70,380)` („Undo Save”) | **Nincs felugró ablak** (az ablaklista végig „Picasa 3”); **„Undo” és „Redo” tiltott, csupasz felirattal**; a szöveg a képen marad; a képterület az `__16` (Apply után, Mentés előtt) állapotától legfeljebb 1 szintre tér el (3 700 képpont: dekódolási zaj), az `__20` (Mentés után) állapotától 4 379 képponton (ebből 309 képpont 8 szintnél nagyobb eltéréssel: a beégetett szöveg élei másként renderelődnek). |
| `__24-25` | `kattint (207,380)` (Redo) | Nincs változás: az `__22`, `__24`, `__25` bájtra azonos. |

**A záró fájlállapot.** `gray_ramp.jpg` **32 017 bájt**, módosítási ideje a futás előtti (az eredeti, a képmappa többi fájljával azonos), állapotváltozás-ideje a futás közben; `.picasaoriginals/gray_ramp.jpg` **nincs**; `.picasaoriginals/.picasa.ini` **0 bájt**; a fő `.picasa.ini` (224 bájt) szó szerint:

```
[gray_ramp.jpg]
backuphash=45713
text=1;135;14;PicasaUndoSave;Times;0.316406,0.144531,0.033333,0.000000;v1,4294967295,4278190080,128.000000,1.000000,0.000000,1.000000,400,0,49152;;
textactive=1
moddate=c479b1b73e7bdd01
```

**Eldőlt (919), nagy bizalommal:** az „Undo Save” **az utolsó Mentést vonja vissza, a szerkesztéseket megtartva**, megerősítés nélkül: a kép a Mentés előtti fájl (az eredeti méret és módosítási idő), a `.picasaoriginals` másolata eltűnik, az eredeti-mappa ini kiürül, a Mentéskor oda költözött `text=` és `textactive=1` VISSZAKERÜL a fő ini-be (mellé `moddate`), a szöveg élő marad a képen (hogy az eszközben megnyitva újra szerkeszthető-e, nincs külön mérve). Az Undo és a Redo utána tiltott, „Redo Save” nincs, a tiltott Redo kattintása hatástalan. **Nem dőlt el:** a láncszerkesztés (Kiegyenesítés) „Undo Save”-je (gombfelirat és ini: `7327-12g`); a Mentés előtti ini lépésenként nincs felvéve (a visszakerült `text=` mezői a beírt szöveggel és az alapgeometriával egyeznek, mint a `job-921` ini-je).

#### Job-920 (`7327-12e`): meglévő blokk szerkesztése és a forgatókorong

A `job-909` útja (a 17 karakteres „PicasPluszaPy7327” szöveg), majd `__26-27` újranyitás, `__28-29` kattintás (620,405) (kijelölés, forgatókorong), `__30-31` `huz (718,405)-(718,445)`, `__32-33` Apply.

| Kocka | Előtte végrehajtott lépés | Kép |
|---|---|---|
| `__28` | `kattint (620,405)` | A blokk kijelölve: vastag lekerekített keret (134×71 képpont), köré **forgatókorong**: gyűrű (külső sugár kb. 65, belső kb. 50) a keret közepén (637,405), **24 osztással (15°-onként)**, jobb szélén nyíl a kerettől a piros pontos fogantyúig (közép (718,405), 81 képpontra a középponttól). |
| `__30-31` | `huz (718,405)-(718,445)` | A blokk elfordult, **a szöveg jobbra lejt** (óramutató járásával egyező); a korong eltűnt, a forgatott kijelölőkeret marad. |
| `__32-33` | `kattint (88,406)` (Apply) | A forgatott szöveg a képen, egyetlen sor; „Undo” és „Redo” tiltott. |

A záró `picasa.ini` szó szerint:

```
[gray_ramp.jpg]
text=1;138;17;PicasPluszaPy7327;Times;0.320979,0.063553,0.037176,0.523599;v1,4294967295,4278190080,128.000000,1.000000,0.000000,1.000000,400,0,49152;;
backuphash=12600
textactive=1
```

**Eldőlt (920):** (1) **egyetlen blokk** van az ini-ben, a szerkesztett szöveggel (blokkok száma `1`, a helyben szerkesztés a blokkot cseréli; nagy bizalom). (2) **A forgatás a geometria negyedik mezőjébe kerül, radiánban: `0.523599` = π/6 = 30,000°**; óramutató szerinti pozitív (nagy bizalom). (3) **A szög RÁSZALAD**: a húzás nyers szöge `atan(40/81)` = 26,3° (a korong közepe a keret közepe), a tárolt érték pontosan 30,000°. A korong 15°-onkénti osztásai és az ini-formátum-lap három valódi szöge (0°, 75°, -270°) mind a 15° többszöröse: **a 15°-os lépés az egyetlen, ami a 26,3° → 30° és a 75° mintát együtt magyarázza** (a 10° és a 30° a 75°-ot, az 5° a 30°-ot nem adná). Közepes-nagy bizalom (egy futásbeli minta; a `7327-12i` 20,3°-os nyers szöggel dönti el: 15° → `0.261799`, 10° → `0.349066`, rászaladás nélkül `0.354`). **Nem dőlt el:** a geometria többi három mezője: a blokk geometriája a szerkesztés előtt `(0,316406; 0,144531; 0,033333)` volt (a `job-919`/`job-921` azonos kattintású ini-je), a szerkesztés és forgatás után `(0,320979; 0,063553; 0,037176)`: a `y` 20,7 képponttal feljebb, a méret 11,5%-kal nagyobb. A szerkesztés és a forgatás hatása egy futásban nem választható szét (ok: egy záró ini van), ezért a döntés előtt `7327-12h` (csak szerkesztés) és `7327-12i` (csak forgatás) kell. Az `x`, `y` jelentése forgatott blokknál (a forgatás a keret KÖZEPE körül történik, a tárolt pont a forgatott szöveg bal felső sarka: ez a hipotézis a mért elmozdulást durva számolással néhány képponton belül adja, de nem bizonyított). **HELYESBÍTVE (`job-942`, `job-941`):** a 15°-os rászaladás NEM általános szabály (a `job-942` tárolt szöge 17,234°), és a geometria `x`, `y`, méret változása a FORGATÁSBÓL jön (a `job-941` szerint a szerkesztés önmagában nem változtat rajta).

#### Job-921 (`7327-12f`): a Clear All utáni Cancel

| Kocka | Előtte végrehajtott lépés | Kép, panel |
|---|---|---|
| `__16-17` | `kattint (88,406)` (Apply) | Alapjavítások, szöveg a képen, „Undo” és „Redo” tiltott. |
| `__18-19` | `kattint (138,275)` (újranyitás) | Szerkesztő panel, a szöveg a képen, „Clear All” és „Apply” aktív. |
| `__20-21` | `kattint (189,372)` (Clear All) | **A szöveg eltűnik a képről**, a „Type anywhere to add text” felirat visszajön, „Clear All” tiltott, az eszköz nyitva (a `job-909 __28` állapota). |
| `__22-23` | `kattint (191,406)` (Cancel) | Alapjavítások; **a szöveg VISSZAJÖTT a képen** (az `__18`-tól 15 képpont, legfeljebb 22 szint: nem a szöveg). |
| `__24-25` | `kattint (138,275)` (újranyitás) | A szöveg a képen, „Clear All” és „Apply” aktív; a képterület az `__18`-cal **0 képpontban** azonos. |

A záró `picasa.ini`: `text=1;138;17;PicasaCancelProba;Times;0.316406,0.144531,0.033333,0.000000;v1,...,400,0,49152;;`, `textactive=1`, `backuphash=13102`: a szöveg megvan.

**Eldőlt (921), nagy bizalommal:** **a Clear All az eszközön BELÜLI piszkozat-művelet**: a szöveget a képről azonnal leveszi, de a Cancel visszahozza (a szöveg és az ini a megnyitáskori), az Apply véglegesíti (a `job-909`: `text=` és `textactive=` kikerül az ini-ből). Az eszköz a Clear All után nyitva marad. A Clear All és az Apply közötti ini-állapot nincs felvéve (csak a záró ini).

#### Job-922 (`7327-9c`): a Vágás aktív kiegyenesítés mellett, húzás és Apply

| Kocka | Előtte végrehajtott lépés | Kép, panel, ablak |
|---|---|---|
| `__10-15` | Straighten, `huz (680,863)-(740,863)`, APPLY | A `job-912 __10-15` útja (fogantyú 738,5; „Undo Straighten”). |
| `__16-17` | `kattint (55,167)` (Crop) | „Crop Photo” panel, ablak és figyelmeztetés nélkül (a `job-912 __16`-tal egyező). |
| `__18-19` | `huz (500,400)-(900,580)` | **Nincs figyelmeztető szöveg a panelben, nincs ablak**: a panel a tilt nélküli `job-911 __12`-vel egyezően a „Manual: 415 x 187” feliratot, aktív „Preview”, „Reset” és „Apply” gombot mutatja; a kijelölés 400×180 képernyő-képpont. |
| `__20-21` | `kattint (84,403)` (Apply) | Alapjavítások; a csempe **„Recrop”**, „Undo Crop” aktív, „Redo” tiltott; **nincs ablak**; az állapotsor **„371x167 pixels”** (a kiegyenesítés utáni „1024x256 pixels” helyett). |

A záró ini: `filters=tilt=1,0.391249,0.000000;crop64=1,418029009e3fcfff;`, `crop=rect64(418029009e3fcfff)`, `backuphash=10718`. A `418029009e3fcfff` törtkoordinátái (`0x4180`, `0x2900`, `0x9e3f`, `0xcfff`) az 1024×256 képen **262,0 · 41,0 · 633,0 · 208,0**, vagyis a téglalap **371 × 167**, és ez egyezik az állapotsorral.

**Eldőlt (922):** (1) **a Vágás-figyelmeztetés (`IDS_WARN_CROP_ACCURACY`) aktív kiegyenesítés mellett SEHOL nem jelenik meg**: sem a megnyitáskor (`job-912`), sem a kijelölés húzásakor, sem az Apply-kor; nincs ablak és nincs panelszöveg (nagy bizalom). Az elrejtés tehát (#7392) a megfigyelt teljes úton helyes. (2) A lánc: a `crop64` a `tilt` UTÁN új tagként kerül a láncba (a #7367 szabálya szerint: a lánc végén nem `crop64` állt), a `crop=` az új tag tükre. (3) **Az alkalmazott téglalap NEM a húzott**: a panel „415 x 187”-et mutat, a tárolt téglalap és a kimenet 371×167. A tilt nélküli `job-911` ugyanazzal a húzással a `370025009ebfdfff` téglalapot adta (220,0 · 37,0 · 635,0 · 224,0, 415×187): a kiegyenesített képen a bal él +42, a felső +4, a jobb -2, az alsó -16 képponttal tér el. Az összefüggés (a kiegyenesítés szöge, a kép beillesztése a nézetbe) egy mintából nem olvasható ki: `7327-9g`.

#### Job-923 (`7327-9d`): a Kiegyenesítés csúszka két vége

| Kocka | Előtte végrehajtott lépés | Kép, panel |
|---|---|---|
| `__10-11` | `kattint (138,160)` (Straighten) | Kiegyenesítés mód, fogantyú közepe 689,5. |
| `__12-13` | `huz (690,863)-(540,863)` (a bal végen túl) | **A fogantyú a bal végállásban: közép 562,5** (a sávon belül marad). |
| `__14-15` | `kattint (875,863)` (APPLY) | Alapjavítások, „Undo Straighten”. |
| `__16-17` | `kattint (138,160)` (újranyitás) | **A fogantyú újra a KÖZEPÉN (689,5)**, az előző végállás nem töltődik vissza. |
| `__18-19` | `huz (690,863)-(850,863)` (a jobb végen túl) | **A fogantyú a jobb végállásban: közép 815,5.** |
| `__20-21` | `kattint (875,863)` (APPLY) | Alapjavítások, „Undo Straighten”. |

A záró ini (mindkét helyen): `filters=tilt=1,-1.000000,0.000000;tilt=1,1.000000,0.000000;`, `backuphash=12121`.

**Eldőlt (923), nagy bizalommal:** (1) **a végállások pontosan `-1,000000` és `1,000000`**; a foglalatot túlhúzva az érték a határra vágódik. (2) **A csúszka lineáris a teljes tartományon**: a fogantyú KÖZEPE a `689,0 + 126,5·érték` egyenesen áll mind az öt mért pontban: -1 → 562,5 (a képlet 562,5), 0 → 689,5 (689,0), 0,391249 → 738,5 (738,49), -0,399233 → 638,5 (638,50), 1 → 815,5 (815,5); a fogantyú KÖZEPE tehát a teljes 253 képpontot bejárja (562,5-től 815,5-ig), a J jegytörzs (3) pontja ezzel igazolt. (3) A második Apply a végállásnál is ÚJ `tilt` tagot fűz (két tag, `-1,000000` és `1,000000`), és az újranyitott eszköz a végállás után is középről indul.

#### Job-924 (`7327-9e`): két Apply után kétszeri Undo és kétszeri Redo

| Kocka | Előtte végrehajtott lépés | Gombok és kép |
|---|---|---|
| `__14-15` | APPLY (1.) | „Undo Straighten” aktív, „Redo” tiltott. |
| `__20-21` | újranyitás, `huz (740,863)-(640,863)`, APPLY (2.) | „Undo Straighten” aktív, „Redo” tiltott. |
| `__22-23` | `kattint (70,380)` (Undo 1.) | **„Undo Straighten” ÉS „Redo Straighten” aktív**; a kép az `__14`-gyel azonos (legfeljebb 1 szint, 14 képpont): **csak a második `tilt` ment vissza**. |
| `__24-25` | `kattint (70,380)` (Undo 2.) | „Undo” tiltott (csupasz), „Redo Straighten” aktív; a kép az eredetivel (`__09`) **0 képpontban** azonos. |
| `__26-27` | `kattint (207,380)` (Redo 1.) | „Undo Straighten” és „Redo Straighten” aktív; a kép az `__22`-vel azonos (0 képpont): az ELSŐ `tilt` jön vissza. |
| `__28-29` | `kattint (207,380)` (Redo 2.) | „Undo Straighten” aktív, „Redo” tiltott; a kép az `__20`-szal azonos (legfeljebb 1 szint, 19 képpont); az `__29` bájtra azonos az `__28`-cal. |

A záró ini: `filters=tilt=1,0.391249,0.000000;tilt=1,-0.399233,0.000000;`, `backuphash=49664`, **`redo=` nincs**.

**Eldőlt (924), nagy bizalommal:** **minden Apply külön visszavonási lépés**: két `tilt` tagnál két Undo kell az eredeti képhez, a lépések a láncban sorban jönnek vissza (a második megy el először, az első jön vissza először), a feliratok „Undo Straighten” / „Redo Straighten”, a végállapotban (két Redo után) a mentett lánc mindkét tagot tartalmazza és `redo=` nem marad.

#### Job-925 (`7327-9f`): a Mentés és a Picasa leállítása után az index

A `job-913` útja egy Apply-val (`huz (680,863)-(740,863)`, APPLY), `ctrl+s`, Save, `picasa leallit`. A fő ini csak `backuphash=63262`; az eredeti-mappa ini: `filters=tilt=1,0.391249,0.000000;`, `moddate=3c3a8ac6457bdd01`, `width=1024`, `height=256`, `textactive=0` (a `job-913` alakjával egyező: **második felvétel ugyanarra az ini-alakra**). A `db3` 10 fájlja: az `imagedata_0`, `albumdata_0`, `catdata_0`, `albums_0.db`, `facetemplatesV2_0.db`, `profilephotos_0.db` mind 4 bájt, a Picasa indításakor (12:23:03-04) írva, azóta nem módosult; a `thumbs_0.db`, `bigthumbs_0.db`, `previews_0.db` a Mentéssel egy időben (12:25:50, ekkor íródott a `gray_ramp.jpg` is) frissült, a leállítás semmit nem írt; **`imagedata_*.pmp` oszlopfájl nincs**, a Picasa ablaka a leállítás után eltűnt (a `__20-21` kocka fekete). A `job-907` db3-ában 24 `imagedata_*.pmp` volt (a futás végén, 09:31:10), a `job-908`, `job-913` és `job-925` db3-ában nincs.

**Döntés:** az eredeti saját PMP-indexe a Mentés és a leállítás után sem kapott oszlopfájlt, a `job-907` egyetlen eltérő futása (Undo, megerősítő ablak) mást váltott ki; a kiváltó ok nem olvasható ki. **Ez a PicasaPy viselkedését nem érinti**: a PicasaPy saját SQLite indexet ír, az eredeti PMP/db3 adatbázist a `pmpimport/` csak OLVASSA (`importer.py`: „Windowsos Picasa-adatbázis ismételhető olvasása”), írási időzítésének paritása nincs mit megvalósítson. **HATÓKÖRÖN KÍVÜL** (lásd a mérlegben).

#### Összevetés a mai PicasaPy-val (kódolvasás, futtatás nélkül) és a kiadott jegyekkel

| Eredeti (mérés) | Nálunk (fájl:sor) | Ítélet |
|---|---|---|
| Ecsetméret: `R_képernyő = 100·t·z` (t: csúszka, z: nagyítás), induláskor `s = 0,25` a középen álló csúszka mellett | `edit_controller_shared.py:377-378` (alap 20, osztó 1000), `edit_controller_retouch_mixin.py:70`, `:234`, `PhotoViewerRetouchArea.qml:43-47` (`arány × min(szélesség, magasság)`), `render/retouch.py:68-71` (`round(sugár × rövidebb oldal)`), `EditorRetouchPanel.qml:84-92` (`from: 1; to: 100`) | **Eltérés** (G jegytörzs, véglegesítve). |
| A Clear All az eszközön belüli piszkozat: a szöveg lekerül a képről, a Cancel visszahozza, az Apply véglegesíti; az eszköz nyitva marad | `edit_controller_text_mixin.py:621-643` (`clearText`: azonnali, végleges, `_save_text()`), `PhotoViewerEditorPanel.qml:278-288` (a Clear All után az eszköz is zárul), `edit_controller_text_mixin.py:461-472` (`exitTextTool`: piszkozat eldobása, nem állít vissza) | **Eltérés** (M jegytörzs). |
| Mentés után az Undo gomb „Undo Save” és aktív; kattintásra az utolsó Mentés visszavonódik a szerkesztések megtartásával | `edit_action_names.py` (nincs „save” művelet); `edit/save_operations.py:192` (`undo_save` kész), a gomb csak a Visszaállítás-párbeszédben él (`SaveDialogs.qml:325-334`, `save_controller.py:239-243`); a mentés utáni szerkesztő a fő ini `filters=` láncából épül (`edit_controller_session_mixin.py:120,261,397`): a lánc a Mentéskor az eredeti-mappa ini-jébe költözik, tehát az Undo üres | **Eltérés** (N jegytörzs). |
| Meglévő szövegblokk: kijelölve forgatókorong (24 osztás), a szög 15°-ra szalad, a `text=` negyedik mezője radián | `PhotoViewerPhotoArea.qml:667-722` (a kijelölt blokk 1 képpontos kék kerete, `rotation` csak a fájlból olvasva, korong és fogantyú nincs), `ini/text_overlay.py:123-137,406-415` (a forgatás parszolva és írva) | **Eltérés** (L jegytörzs; előfeltétele `7327-12h`, `7327-12i`). |
| Vágás kiegyenesített képen: nincs figyelmeztetés sehol (megnyitás, húzás, Apply) | `EditorCropPanel.qml:71-87` (`cropStraightenWarning`, `visible: false`, #7392) | **Egyezik** (a #7392 a teljes megfigyelt úton helyes). |
| Vágás kiegyenesített képen: a húzott téglalap 415×187, az alkalmazott 371×167 | nincs összevetve: a mai render- és vágásláncban a `crop64` és a `tilt` viszonyát nem olvastam át, a mérés nem elég a modellhez | **Nyitott** (`7327-9g`). |
| A Kiegyenesítés csúszka -1..1 lineáris, a fogantyú KÖZEPE a teljes 253 képpontot bejárja, a végállás `±1,000000`; minden Apply új `tilt` tag, két tag két Undo | a #7393 ága (`origin/fix/7393-claude`, `6aad46405`): `session_effects.py` `append_tilt` (mindig a lánc végére), `edit_controller_effects_finetune_mixin.py` `setTilt` (`_push_undo("tilt")` minden Apply-nál), `PicasaSlider.qml` `handleCenterOverhang` (a fogantyú középpontja a teljes foglalatot járja) | **Nem cáfolja**: a második tag, a csúszka útja és a lépésenkénti Undo egyezik a felvétellel (kódolvasás a nem beolvasztott ágon, futtatás nélkül; a #7393 ennek a fának a `main`-jében még nincs). |
| A retusálás megerősített visszavonása után az Újra tiltott | `edit_controller_history_mixin.py:20,81-83` (#7391: `_REDO_NELKULI_MUVELETEK = {"retouch"}`) | **Nem cáfolja** (a `job-907`-tel egyezik; a 917-925 nem érinti). |
| A Vágás csempe „Recrop” felirata, a lánc `crop64` után `tilt`-től függetlenül | a #7376, #7367 (kiadva) | **Egyezik**: a `job-922 __20` „Recrop” felirata és a `tilt` után új `crop64` tag a #7367 szabályával egyezik. |

**A kiadott jegyek közül egyiket sem cáfolja a felvétel.** A #7379 ecsetméret-leképezése (a mai `main` 20/1000-e marad benne) a 917/918 szerint is hibás, de ez nem új: a `job-908` óta ismert, a G jegytörzs viszi.

#### Fejlesztői jegytörzsek (job-917..925): G (véglegesítve), L, M, N

A **G** jegytörzs a fenti „Új fejlesztői jegytörzsek (job-907..913): G, H, I, J” szakaszban, véglegesített alakban áll. Az **L**, **M** és **N** itt következik.

**(L) Szöveg: a kijelölt blokk forgatókorongja (jegy: külön; előfeltétel: `7327-12h` és `7327-12i`, addig félkész dolog nem megy ki) - FELFÜGGESZTVE a `job-942` után: a 15°-os rászaladás és a (2)/(Kész, ha 2) pont cáfolt, lásd „Job-939..943”; a jegytörzs a `7327-12j` kiértékelése után írandó át**

> **Mi a hiba:** az eredeti Szöveg eszközben a képen kattintással kijelölt blokk köré forgatókorong rajzolódik, amelynek fogantyúját húzva a blokk elfordul; a szög 15°-onként szalad rá, és a `text=` sor geometriájának negyedik mezőjébe kerül radiánban. Nálunk a kijelölt blokk csak egy vékony kék keretet kap, forgatni nem lehet.
>
> **Eredeti:** `job-920 __28` (a kijelölt blokk, a korong 24 osztással, a fogantyú (718,405)-nél, 81 képpontra a korong közepétől (637,405)), `__30-31` (a `huz (718,405)-(718,445)` után a szöveg jobbra lejt, a korong eltűnt), `__32-33` (Apply: a forgatott szöveg a képen, „Undo” és „Redo” tiltott), a záró ini `0.320979,0.063553,0.037176,0.523599` (π/6 = 30,000°; a húzás nyers szöge 26,3°); az ini-formátum-lap valódi szögei (0°, 75°, -270°) mind a 15° többszörösei.
>
> **Nálunk:** `PhotoViewerPhotoArea.qml:667-722` (a kijelölt blokk 1 képpontos kék kerete; a `rotation` a fájlból olvasott érték, `transformOrigin: Item.TopLeft`), `edit_controller_text_mixin.py:446-459` (`selectTextOverlay`), `ini/text_overlay.py:123-137,406-415` (a forgatás radiánban parszolva és írva).
>
> **Teendő:** (1) a kijelölt blokk köré forgatókorong: 24 osztás (15°), a fogantyú a vízszintes tengelyen a középponttól 81 képpontra (a keret jobb szélén túl, nyíllal a kerettől), a korong a keret közepén; (2) a fogantyú húzása a blokkot a korong közepe körül forgatja, a szög a legközelebbi 15°-ra szalad (a `7327-12i` mérése dönti el, hogy 15° vagy 10°, ezért a lépés a mérés után véglegesíthető); (3) pozitív szög = óramutató járásával egyező, a `text=` negyedik mezőjébe radiánban kerül; (4) a forgatás és az Apply után az Undo és a Redo tiltott marad (mint minden szövegműveletnél). **Nem része:** a geometria `x`, `y`, méret mezőinek változása szerkesztéskor és forgatáskor (`7327-12h`, `7327-12i`: addig a mai tárolás marad, és ezt a jegy kimondja), a korong rajza képpontra (mérni csak a fenti méretekig mértem).
>
> **Kész, ha:** (1) a renderelt próba a korongot a `job-920 __28`-cal veti össze (osztások, fogantyú helye ±2 képpont); (2) a (718,405)-ről (718,445)-re húzott fogantyú után a `text=` negyedik mezője `0.523599`; (3) a forgatott blokk Apply után a `job-920 __32` képével egyező irányban lejt; (4) a szomszéd panelek (Vörösszem, Retusálás) képe változatlan.

**(M) Szöveg: a Clear All az eszközön belüli piszkozat, a Cancel visszahozza (jegy: külön)**

> **Mi a hiba:** az eredeti Szöveg eszközben a „Clear All” csak az eszközön belül veszi le a szöveget a képről: az eszköz nyitva marad („Type anywhere to add text”, „Clear All” tiltott, „Apply” aktív), a „Cancel” visszahozza a szöveget, az „Apply” véglegesíti (a `text=` és a `textactive=` kikerül az ini-ből). Nálunk a „Clear All” azonnali és végleges, és az eszközt is bezárja.
>
> **Eredeti:** `job-921 __20` (Clear All után a szöveg lekerült a képről, a felirat visszajött, „Clear All” tiltott), `__22` (a Cancel után az Alapjavítások, a szöveg a képen: az `__18`-tól 15 képpont), `__24` (újranyitva a szöveg a képen, „Clear All” és „Apply” aktív, az `__18`-cal 0 képpont), a záró ini `text=1;138;17;PicasaCancelProba;...`, `textactive=1`; `job-909 __28-31` (Clear All + Apply: a szöveg nyomtalanul eltűnt, ini-ben `text=` és `textactive=` nincs).
>
> **Nálunk:** `edit_controller_text_mixin.py:621-643` (`clearText`: `_text_overlay = None`, `_save_text()`: azonnali, végleges, az ini-t írja, „Mégse” nem hozza vissza), `PhotoViewerEditorPanel.qml:278-288` (a Clear All után az eszköz is zárul), `edit_controller_text_mixin.py:461-472` (`exitTextTool`: a piszkozatot eldobja, a törölt szöveget nem állítja vissza).
>
> **Teendő:** a „Clear All” az eszköz piszkozatából vegye le a szöveget (a kép azonnal a szöveg nélküli), de az ini-t NE írja; az eszköz maradjon nyitva, a „Clear All” tiltott, az „Apply” aktív; a „Cancel” állítsa vissza a megnyitáskori állapotot (a szöveg a képen, az ini változatlan); az „Apply” a piszkozatot véglegesítse (szöveg nélküli piszkozatnál a `text=` és a `textactive=` kerüljön ki az ini-ből, mint a `job-909`-ben). **Nem része:** a Clear All Visszavonás-verme (az eredetiben az Apply utáni Undo és Redo tiltott), a „Copy Caption” gomb.
>
> **Kész, ha:** (1) meglévő szövegnél Clear All, Cancel, újranyitás után a szöveg és az ini azonos a megnyitásival; (2) Clear All, Apply után a kép a szöveg nélküli, az ini-ben nincs `text=` és `textactive=`, az „Undo” és „Redo” tiltott; (3) Clear All után az eszköz nyitva, „Apply” aktív, „Clear All” tiltott; (4) a renderelt próba a Clear All utáni panelt a `job-921 __20`-szal veti össze.

**(N) Mentés után az Undo gomb „Undo Save” és aktív (jegy: külön)**

> **Mi a hiba:** az eredeti szerkesztő a Mentés (Ctrl+S, „Save” ablak) után az Undo gombot „Undo Save” felirattal aktívra teszi, és a kattintás az utolsó Mentést visszavonja a szerkesztések megtartásával, megerősítés nélkül. Nálunk Mentés után az Undo tiltott, az „Undo Save” csak a Visszaállítás-párbeszédben érhető el.
>
> **Eredeti:** `job-910 __32`, `job-913 __24`, `job-919 __20`, `job-925 __18` (Mentés után „Undo Save” aktív, „Redo” tiltott); `job-919 __22` (az „Undo Save” után nincs ablak, „Undo” és „Redo” tiltott, csupasz; a szöveg a képen marad), `__24-25` (a tiltott Redo hatástalan); záró fájlállapot: `gray_ramp.jpg` 32 017 bájt az eredeti módosítási idővel, `.picasaoriginals/gray_ramp.jpg` nincs, `.picasaoriginals/.picasa.ini` 0 bájt, a fő ini `backuphash`, `text=`, `textactive=1`, `moddate`.
>
> **Nálunk:** `edit_action_names.py` (nincs „save” művelet), `edit_controller_session_mixin.py:120,261,397` (a verem a fő ini `filters=` láncából épül, Mentés után üres), `edit/save_operations.py:192` (`undo_save`: kész, a Visszaállítás-párbeszéd hívja: `SaveDialogs.qml:325-334`, `save_controller.py:239-243`).
>
> **Teendő:** (1) minden sikeres Mentés után a szerkesztőben az Undo gomb felirata „Undo Save” (nyelvenként az eredeti alak, a #7381 szerint), aktív, a „Redo” tiltott; (2) a kattintás az utolsó Mentést a meglévő `undo_save` útján vonja vissza, megerősítő ablak nélkül: a kép a Mentés előtti bájtokat és módosítási időt kapja vissza, a `.picasaoriginals` másolat eltűnik, az eredeti-mappa ini kiürül, a Mentéskor oda költözött kulcsok (`text=`, `textactive=`, és ahogy a mai `undo_save` már teszi, a `filters=`) visszakerülnek a fő ini-be; (3) az „Undo Save” után az Undo és a Redo tiltott, csupasz felirattal (szövegszerkesztésnél mért). **Nem része:** a láncszerkesztés (pl. Kiegyenesítés) „Undo Save” utáni gombállapota (`7327-12g`: nem mért, ne általánosítsd; a mai `undo_save` a `filters=`-t visszaállítja, a gombfeliratot a szokásos módon a visszaállított láncból számolja), egymás utáni többszöri Mentés és Undo Save (nincs mérve), a Mentés eredeti-mappa ini-kulcsai (a D jegytörzs része).
>
> **Kész, ha:** (1) Szöveg, Apply, Mentés után az Undo gomb „Undo Save” és aktív, a „Redo” tiltott; (2) az Undo Save után a kép a Mentés előtti bájtokkal egyezik, a `.picasaoriginals/gray_ramp.jpg` nincs, a fő ini-ben `text=` és `textactive=1` áll, az Undo és a Redo tiltott, ablak nincs; (3) a renderelt próba a bal panelt a `job-919 __20`-szal és `__22`-vel veti össze; (4) Mentés nélküli szerkesztésnél (Apply után) az Undo gomb nem „Undo Save”.

#### Javított lépéssorok (job-917..925 nyomán)

A javított lépéssorok a munkafa `.tmp/javitott-lepesek4/` mappájában vannak (közös bevezető: négy `var 10`, `kattint (80,215)`, `var 4`, `dupla (340,272)`, `var 4`, a 1024×256-os `gray_ramp.jpg`):

| Fájl | Lépések | Mit dönt el |
|---|---|---|
| `7327-11e` (28) | Retouch; fogantyú 134 → 107, kattintás; Cancel; újranyitás, kattintás; fogantyú 107 → 134 (a pontos közép), kattintás (900,450); az `1:1` gomb (820,947), kattintás | az újranyitáskori fogantyú- és ecsetállapot (megmarad-e a 107-es állás: R = 23,0, vagy a közép és R = 24,0); az ecsetméret a középállás húzás UTÁN (a lineáris illesztés szerint R = 48,5); az 1:1 gomb a Retusálásban nagyít-e (z = 1,0: R = 50 a középállásnál) |
| `7327-12g` (22) | Straighten, húzás 680 → 740, APPLY, `ctrl+s`, „Save”; Undo (70,380); Redo (207,380); kimenet: ini, képmappa | a láncszerkesztés „Undo Save”-je: gombfelirat, a `filters=` hová kerül, kép, a Redo utána |
| `7327-12h` (24) | Text, `PicasaPy7327`, Apply; újranyitás, kattintás (620,405), „Plusz”, Apply (forgatás NÉLKÜL); kimenet: ini | a `text=` geometriája (x, y, méret) csak a helyben szerkesztés után |
| `7327-12i` (24) | Text, `PicasaPy7327`, Apply; újranyitás, kattintás (620,405), a fogantyú húzása (708,405) → (708,435) (nyers szög 20,3°), Apply (szerkesztés NÉLKÜL); kimenet: ini | a geometria csak forgatás után; a szög rászaladása és lépése (15° → `0.261799`, 10° → `0.349066`, rászaladás nélkül `0.354`) |
| `7327-9g` (36) | Straighten, húzás 680 → 740, APPLY; három vágás: (500,400)-(900,580), (350,420)-(650,520), (700,380)-(1100,600): mindegyik Apply, az állapotsor mérete, Undo; kimenet: ini | a húzott és az alkalmazott téglalap viszonya kiegyenesített képen (a három húzás más-más élt metsz) |

A `7327-10` (Vörösszem Apply, Undo, Mentés) lépéssora változatlanul a `.tmp/javitott-lepesek/` mappában vár, és a PicasaTeszt mappa mesterpéldányába vörösszemes tesztkép kell hozzá (a hiány: valódi, vörösszemes fénykép).

### Job-939..943 (a negyedik javított kör: Retusálás, Undo Save láncszerkesztésnél, Szöveg szerkesztés és forgatás, Vágás kiegyenesített képen)

**Bemenet és olvasat.** Öt felvétel (1280×1024): `job-939` = `7327-11e`, `job-940` = `7327-12g`, `job-941` = `7327-12h`, `job-942` = `7327-12i`, `job-943` = `7327-9g`. Lépés/kocka: 28/29, 22/23, 24/25, 24/25, 36/37; a `kepernyo__NN` az (NN-1). lépés utáni állapot. A döntő kockákat egyenként megnéztem, az azonosakat md5-vel csoportosítottam; a feliratokat és gombállapotokat a képekből olvastam. A köröket és a fogantyúkat képpontosan mértem: a gyűrűnél a világos csúcs sugara 0,5 képponttal nagyobb a `job-917` lapon használt „fehér pár közepénél" (a `job-917 __14` és a `job-939 __14` ugyanazon az állapoton azonos mérést ad: világos csúcsok x 576 és 623, y 426 és 473, vagyis a lap szerinti R = 23,0), ezért az alábbi R-ek a lap konvenciójában értendők. A fájlállapot a futás VÉGÉN készül, lépésenkénti nincs.

#### Job-939 (`7327-11e`): a Cancel függő kijelöléssel, a középállás húzás után, az 1:1 gomb

| Kocka | Előtte végrehajtott lépés | Kép, panel |
|---|---|---|
| `__10-11` | `kattint (55,275)` (Retouch) | Friss panel, a fogantyú KÖZEPE x = 133,5. „Zoomed to 97%". |
| `__12-13` | `huz (134,277)-(107,277)` | A fogantyú közepe 105,5 (a futás 24,2%-a). |
| `__14-15` | `kattint (600,450)` | Gyűrű R = 23,0, panel változatlan (a `job-917 __14`-gyel azonos állapot és azonos mérés): az ELSŐ kattintás, folt nincs, „Undo Patch" tiltott. |
| `__16-17` | `kattint (200,391)` (Cancel) | **Az eszköz NYITVA marad**: a Retouch panel áll, a gyűrű eltűnt, a Cancel fölött súgó („Exit Retouch tool without applying edits"); a két kocka bájtra azonos, tehát 3 másodperc múlva is nyitva. |
| `__18-19` | `kattint (55,275)` | A (55,275) a nyitott panel üres részére esik: a kocka bájtra azonos az `__12`-vel. |
| `__20-21` | `kattint (600,450)` | Bájtra azonos az `__14`-gyel: ismét ELSŐ kattintás, nincs folt. Az `__14` függő kijelölését tehát a Cancel eldobta (ha megmaradt volna, ez a kattintás véglegesítette volna a foltot, és az „Undo Patch" aktív lenne). |
| `__22-23` | `huz (107,277)-(134,277)` | A fogantyú közepe 132,5 (t = (132,5 - 79,5)/107,5 = 0,493). |
| `__24-25` | `kattint (900,450)` | A kijelölés 2. kattintása: **folt jön létre** (Reset, Undo Patch, Apply aktív, a hisztogram megváltozott), a gyűrű az egér körül, világos csúcsok x 851 és 948, y 401 és 498: **R = 48,0** (z = 0,97). |
| `__26-27` | `kattint (820,947)` (1:1) | **„Zoomed to 100%"**: a kép natív méretben áll (256 képpont magas: y 360..616), a nagyítás-csúszka a 100%-nál; a fogantyú (132,5) és a folt megmaradt. |
| `__28-29` | `kattint (600,450)` | Gyűrű: világos csúcsok x 549 és 650, y 399 és 500: **R = 50,0** (z = 1,00). |

**Eldőlt (939):**

1. **Az 1:1 gomb a Retusálásban működik**: a nézet 100%-ra áll, a kép natív méretben látszik (nagy bizalom, `__26`).
2. **Az ecsetméret a csúszka-állással és a nagyítással arányos az 1:1-nél is**: R = 48,0 (z = 0,97) és R = 50,0 (z = 1,00), a fogantyú 132,5-nél. A `100·s·z` képlet `s = 0,5`-tel 48,5 és 50,0, `s = 0,493`-mal (a fogantyú képpontos helyéből) 47,8 és 49,3; a mért értékek ezektől legfeljebb 0,7 képpontra vannak, ami az egész képpontos gyűrű mérési pontosságán belül van. A csúszka pontos mezőértéke (0,493 vagy 0,5) ebből nem dönthető el. A `job-917` lineáris leképezését (`s = t`) a két új pont nem cáfolja (nagy bizalom a lineárisra, a pontos `s`-re nem).
3. **A Cancel gomb függő kijelölés mellett NEM lép ki az eszközből**: a panel nyitva marad, a kijelölés eldobódik, a következő kattintás újra első kattintás (közepes bizalom: egy futás, két független jel: az `__16-17` nyitott panele és az `__20` bájtazonossága az `__14`-gyel). A `job-838 __26`-ban a Cancel függő kijelölés NÉLKÜL (két kattintással véglegesített folt után) kilépett: a két eset együtt azt adja, hogy a Cancel először a függő kijelölést dobja el.

**Nem dőlt el (939), a pontos hiánnyal:** (a) **a Retusálás újranyitáskori csúszka- és ecsetállapota**: az `__16-19` miatt az újranyitás ebben a futásban nem történt meg (az eszköz végig nyitva volt), tehát a megjegyzett állás kérdése érintetlen. (b) **a Cancel-kattintás vagy az egér képről való távozása dobja-e el a kijelölést** (a Colab-lépéskészletben nincs egérmozgatás, ezért egy semleges, nem gombra eső kattintás kell a panelen). (c) a Cancel kilép-e második kattintásra. Mind a három a `7327-11f` lépéssorral mérhető (lent).

#### Job-940 (`7327-12g`): az Undo Save láncszerkesztés (Kiegyenesítés) után

| Kocka | Előtte végrehajtott lépés | Kép, panel, ablak |
|---|---|---|
| `__14-15` | Straighten, `huz (680,863)-(740,863)`, APPLY | „Undo Straighten" aktív, „Redo" tiltott; állapotsor „31 KB". |
| `__16-17` | `billentyu ctrl+s` | „Save" ablak („Save changes to disk? A backup of this file will be made.", „Do not ask me again.", „Save", „Cancel"). |
| `__18-19` | `kattint (687,553)` („Save") | Az ablak bezárult; **az Undo gomb „Undo Save" és aktív**, a „Redo" tiltott; az állapotsor „23 KB". |
| `__20-21` | `kattint (70,380)` („Undo Save") | **Nincs felugró ablak; az Undo gomb „Undo Straighten" és aktív, a „Redo" tiltott**; az állapotsor újra „31 KB"; a kép a kiegyenesített (az `__14` képterületétől legfeljebb 3 szint az RGB-összegben, 16 253 képpont: dekódolási zaj). |
| `__22-23` | `kattint (207,380)` (Redo) | Az `__20`-tól csak az Undo gomb egér-kiemelésében tér el (315 képpont, x 6..133, y 366..393): felirat és állapot változatlan, a tiltott Redo hatástalan. |

A záró fő ini (96 bájt, a képmappa-lista `.picasa.ini`-je azonos vele) szó szerint:

```
[gray_ramp.jpg]
backuphash=30630
filters=tilt=1,0.391249,0.000000;
moddate=67eb71776d7bdd01
```

A `.picasaoriginals/.picasa.ini` 0 bájt, a `.picasaoriginals/gray_ramp.jpg` nincs a képmappa-listában, a `gray_ramp.jpg` 32 017 bájt az eredeti módosítási idővel (a mappa többi fájljával azonos), állapotváltozás-ideje a futás közben. Mind a 23 kocka és az ini/képmappa-kimenet megvan.

**Eldőlt (940), nagy bizalommal:** (1) a Mentés után az Undo gomb láncszerkesztésnél is „Undo Save" és aktív (a `job-919` szövegesével egyezően). (2) Az Undo Save a szerkesztést megtartja: a `filters=tilt=...` és a `moddate` visszakerül a fő ini-be, az eredeti-mappa ini kiürül, az eredeti fájl és időbélyege visszajön. (3) **Az Undo Save utáni gombállapot láncszerkesztésnél más, mint szövegnél: az Undo „Undo Straighten" és AKTÍV (a `job-919 __22`-ben szövegnél tiltott és csupasz volt).** A kettő egy szabállyal írható le: az Undo-gombot az Undo Save után is a visszaállított lánc adja, a szövegnek nincs lánc-eleme; ez magyarázat, külön nem mért (a többelemű lánc nincs felvéve). A #7408 ezt nem teszi (lent: V jegytörzs).

#### Job-941 (`7327-12h`): meglévő szövegblokk szerkesztése forgatás nélkül

Útvonal: Text, kattintás (600,400), `PicasaPy7327`, Apply; újranyitás, `kattint (620,405)` (a blokk kijelölése: forgatókorong, a `job-920 __28` alakja), `Plusz` begépelve, Apply. A `__20` a kijelölt blokkot mutatja, rajta a forgatókorong és a (708,0; 405,0) fogantyú; a kurzor a szövegben áll. A záró ini:

```
[gray_ramp.jpg]
text=1;138;17;PicasPluszaPy7327;Times;0.316406,0.144531,0.033333,0.000000;v1,4294967295,4278190080,128.000000,1.000000,0.000000,1.000000,400,0,49152;;
backuphash=34611
textactive=1
```

**Eldőlt (941), nagy bizalommal:** (1) **A szerkesztés ÖNMAGÁBAN nem változtatja a geometriát**: `0.316406,0.144531,0.033333,0.000000` ugyanaz, mint a `job-919`/`job-921` újraszerkesztés nélküli blokkjáé, miközben a tartalom 12-ről 17 karakterre nőtt. A `job-920`-ban látott `y` (-0,080978 a kiinduló 0,144531-hez), méret (+11,5%) és `x` változás tehát a FORGATÁSBÓL jön. (2) **A kijelölő kattintás a kurzort a kattintott karakterhatárra teszi**: a (620,405) kattintás után begépelt `Plusz` a `Picas` és az `aPy7327` közé került (a `job-920` útja, amely ugyanezt a `PicasPluszaPy7327` szöveget adta, második független előfordulás). (3) Egyetlen blokk marad az ini-ben.

#### Job-942 (`7327-12i`): meglévő szövegblokk forgatása szerkesztés nélkül

Útvonal: mint a `job-941`, de a kijelölés után `huz (708,405)-(708,435)`, Apply (szerkesztés nélkül).

| Kocka | Előtte végrehajtott lépés | Kép |
|---|---|---|
| `__20-21` | `kattint (620,405)` | A blokk kijelölve; a korong közepe kb. (627,405), a piros fogantyú közepe **(708,0; 405,0)** (13 képpont), tehát 81 képpontra a középponttól és pontosan a húzás kezdőpontján. |
| `__22-23` | `huz (708,405)-(708,435)` | A blokk elfordult, a szöveg jobbra lejt; a fogantyú közepe **(703,3; 429,2)**. A két kocka a fogantyúra azonos. |
| `__24-25` | Apply | A forgatott szöveg a képen, egyetlen sor (kb. x 600..653, y 394..416). |

A záró ini: `text=1;133;12;PicasaPy7327;Times;0.317762,0.110521,0.035546,0.300780;v1,4294967295,4278190080,128.000000,1.000000,0.000000,1.000000,400,0,49152;;`, `backuphash=884`, `textactive=1`.

**Eldőlt (942):** (1) **A forgatás a geometria negyedik mezőjébe kerül radiánban: `0.300780` = 17,234°** (óramutató szerint pozitív, a szöveg jobbra lejt; nagy bizalom). (2) **A 15°-os rászaladás mint általános szabály CÁFOLT**: a 17,234° nem a 15° többszöröse (a `job-920` egy mintájából, 26,3° → 30,000°, vont következtetés nem tartható). (3) A megrajzolt fogantyú szöge a kijelölő korong középpontjából (627,405) mérve 17,6° (a középpont ±1 képpontos bizonytalanságával ±0,7°), tehát a tárolt szöggel egyezik; a húzás végpontjának nyers szöge viszont `atan(30/81)` = 20,3°: **3,1°-kal más, mint a tárolt**. A `job-920`-ban a nyers 26,3° a tárolt 30,000°-nál 3,7°-kal KISEBB volt, itt a nyers 20,3° a tároltnál 3,1°-kal NAGYOBB: az egér-szög → tárolt szög leképezés nem egyszerű `atan2`, és a mágneses rászaladás (a 30°-os osztás körül) csak az egyik mintát magyarázza. (4) **A geometria többi mezője csak forgatásra változik** (a `job-941` szerint a szerkesztés nem érinti): a kiinduló `(0.316406; 0.144531; 0.033333)` után a `job-942` (17,234°): `x` +0,001356, `y` -0,034010, méret ×1,0664; a `job-920` (30,000°, 17 karakteres blokk): `x` +0,004573, `y` -0,080978, méret ×1,1153. A méret-szorzó mínusz 1 és a szög (radián) hányadosa 0,2207 és 0,2202: a két mintán a szorzó a szögben lineáris és a blokk szélességétől (12 és 17 karakter) független; képlet nincs belőle (két minta).

**Nem dőlt el (942), a pontos hiánnyal:** az egér-szög → tárolt szög leképezés (nyers 20,3° → 17,234° és nyers 26,3° → 30,000°), valamint az `x`, `y`, méret képlete forgatott blokknál. Ok: két minta, mindkettő csak a végpontot adja. Három újabb nyers szöggel (kb. 12°, 26,6°, 33,5°) a megrajzolt fogantyúból és a záró ini-ből a leképezés kimérhető: `7327-12j`. A forgatott blokk Apply utáni olvasata (az `x`, `y` a forgatott szöveg melyik pontja) szintén ettől függ: a `job-942 __24` képéből az első betű bal felső sarka kb. (601; 394), a tárolt pont (601,8; 391,6).

#### Job-943 (`7327-9g`): a Vágás kiegyenesített képen (a kiegyenesítés `tilt=1,0.391249,0.000000`)

| Kocka | Előtte végrehajtott lépés | Kép, panel |
|---|---|---|
| `__18-19` | `huz (500,400)-(900,580)` | „Manual: 415 x 187" (a `job-922 __18` és a `job-911 __12` panelje). |
| `__20-21` | `kattint (84,403)` (Apply) | „Recrop", „Undo Crop" aktív; állapotsor **„371x167 pixels"** (a `job-922 __20` állapota). |
| `__22-23` | `kattint (70,380)` (Undo) | „Undo Straighten" és „Redo Crop"; állapotsor „1024x256 pixels". |
| `__26-27` | `huz (350,420)-(650,520)` (újranyitás után) | „Manual: 312 x 104". |
| `__28-29` | Apply | „Recrop"; állapotsor **„293x98 pixels"**. |
| `__30-33` | Undo, újranyitás | Bájtra azonos az `__22-25`-tel (az Undo a második vágást veszi vissza, a kiegyenesítés marad). |
| `__34-35` | `huz (700,380)-(1100,600)` | „Manual: 415 x 228". |
| `__36-37` | Apply | „Recrop"; állapotsor **„361x199 pixels"**. |

A záró ini: `filters=tilt=1,0.391249,0.000000;crop64=1,6a402600c47fecff;`, `crop=rect64(6a402600c47fecff)`, `backuphash=19910`. A `6a402600c47fecff` az 1024×256 forrásképen **425,0 · 38,0 · 786,0 · 237,0**, vagyis 361 × 199, és ez egyezik az állapotsorral. (A `job-922` ugyanazon az első húzáson a `418029009e3fcfff` = 262 · 41 · 633 · 208 = 371 × 167 téglalapot adta: az első húzás reprodukálódott.)

**Eldőlt (943), nagy bizalommal:**

1. **A panel a húzás méretét mutatja a kijelzett (kiegyenesített) képen, az alkalmazott méret kisebb**: 415×187 → 371×167, 312×104 → 293×98, 415×228 → 361×199; **az oldalarány megmarad** (2,22; 3,0; 1,82 mindkét oldalon).
2. **A `crop64` a FORRÁSKÉP törtkoordinátájában áll, és az eredmény a kivágott forrásablakra ÚJRA alkalmazott kiegyenesítés.** Mérés: a `6a402600c47fecff` és a `418029009e3fcfff` téglalapját az 1024×256-os szürke rámpán (vízszintes lineáris átmenet) kivágva és a PicasaPy saját `apply_tilt`-jét a KIVÁGOTT ablakra (a szög 0,391249 × 0,2 radián) alkalmazva a kapott 361×199 és 371×167 képpontos kép a felvétel képterületétől az egész ablakon legfeljebb 1 szintre tér el (átlagos eltérés 0,011 és 0,024; a 3 képpontos szélt kihagyva). Kontrollként a tilt nélküli kivágás ettől 8 és 9 szintig tér el (átlag 2,8 és 3,4), tehát a próba érzékeny a kiegyenesítésre. A másik két olvasat nem egyezik: ha a téglalap a kiegyenesített kép törtkoordinátája (kivágás a tilt UTÁN), a bal él fényereje 80 a mért 72 helyett (`418029...`).
3. **A húzott téglalap → tárolt téglalap szabály**, három mintára (A: `job-943 __18-20`, B: `__26-28`, C: `__34-36`), a kijelzett kép képpontjaira a nézet 0,966-os nagyításával számolva: a húzás négy sarkát a kiegyenesítés cél → forrás mátrixával (`ops_geometry.tilt_matrix`) a forrásra vetíteni; a befoglaló magassága `hb` (A 166,7; B 97,4; C 198,3); `k = hb / húzás magassága` (0,8937; 0,9401; 0,8697); a tárolt téglalap mérete = a húzás mérete × k felfelé kerekítve (A 370,2×166,7 → 371×167, C 360,2×198,3 → 361×199, B magassága 97,4 → 98; B szélessége 292,0, a mért 293: itt a kerekítés 1 képpontnyit eltér), a felső él a befoglaló teteje (A 41,3 → 41, C 37,9 → 38), a bal él a befoglaló közepe mínusz a fél szélesség (A 262,2 → 262, C 424,8 → 425). A tárolt téglalap A-ra és C-re ±0 képponton belül egyezik a mért `crop64`-gyel; B-nél csak a méret ismert (a köztes ini nincs felvéve). **A kerekítés három mintára illeszkedik, nem bizonyított**, és egyetlen szögre (0,391249) és egyetlen képre (1024×256) mért.
4. **A mai PicasaPy ugyanazt az ini-t másként rendereli**: `tilt=1,0.391249,0.000000;crop64=1,418029009e3fcfff;` → **501×180**, `...crop64=1,6a402600c47fecff;` → **492×222** (a felvételen 371×167 és 361×199); a bal/jobb szél fényereje a középső sorban 64/159 és 104/197 a mért 72/150 és 111/189 helyett (futtatva a szürke rámpán, `render.chain.apply_filters`).

**Nem dőlt el (943):** a téglalap-leképezés képlete más szögön és más képméreten (egy szög, egy kép mérve), a kerekítés pontos szabálya, a `crop64` utáni `tilt` (a lánc fordított sorrendje), a Vágás eszköz újranyitása kiegyenesített képen (a meglévő kijelölés visszatöltése nincs felvéve). Ezek a jegytörzs „Nem része" pontjai; a viselkedés a felvett esetre teljes.

#### Összevetés a mai PicasaPy-val (kódolvasás és egy futtatott render) és a kiadott jegyekkel

| Eredeti (mérés) | Nálunk (fájl:sor) | Ítélet |
|---|---|---|
| Az Undo Save után az Undo gomb a visszaállított láncból épül: Kiegyenesítésnél „Undo Straighten" aktív, szövegnél tiltott (`job-940 __20`, `job-919 __22`) | `edit_controller_history_mixin.py:108-114` (`_finish_save_undo`: siker esetén mindkét verem üres), `save_feedback.py:89-102` | **Eltérés** (V jegytörzs): a #7408 az Undo-t láncszerkesztésnél is letiltja. |
| Vágás kiegyenesített képen: a `crop64` forrásképi törtkoordináta, az eredmény a kivágott ablakra újra alkalmazott kiegyenesítés (`job-943`) | `edit_controller_crop_mixin.py:93-123` (a kijelzett kép törtkoordinátái változtatás nélkül), `render/chain_ops.py:49-89` (a téglalap a tilt mátrixával a kiegyenesített képre vetítve) | **Eltérés** (T jegytörzs). |
| A Retusálás Cancel gombja függő kijelölés mellett csak a kijelölést dobja el (`job-939 __16-21`) | `PhotoViewerEditorPanel.qml:216` (`onRetouchCancelRequested: retouchActive = false`: mindig kilép), `edit_controller_retouch_mixin.py:157-164` (`cancelRetouchPatch` csak az Esc-úton) | **Valószínű eltérés**, de egy futás, az ok nincs szétválasztva: jegytörzs nincs, `7327-11f` kell. |
| Meglévő szövegblokk kattintására a kurzor a kattintott karakterhatárra kerül (`job-941`, `job-920` útja) | `edit_controller_text_mixin.py:457-470` (`selectTextOverlay`: kurzorpozíciót nem ad át), `PhotoViewerPhotoArea.qml` (nincs `positionAt`) | **Valószínű eltérés, futtatással nem ellenőrizve**: az `L` jegytörzs része lesz, ha a forgatás feloldódik. |
| Az 1:1 gomb a Retusálásban 100%-ra nagyít, a gyűrű R = 100·s·z (`job-939 __26-28`) | `retouch_brush.py` (`screen_radius`: `max(3, 100·s·z)`), `PhotoViewerRetouchArea.qml:74` (`setRetouchViewZoom`) | **A #7406 nem cáfolt**: ha a csúszka értéke az 1..100 skálán 50 (`t = 0,495`), a képlet 48,0 és 49,5, a mért 48,0 és 50,0 ellen 0,5 képponton belül (hogy a PicasaPy csúszkája a fogantyú ezen helyén 50-et ad-e, nincs futtatva); hogy az 1:1 gomb a PicasaPy Retusálásában tényleg 100%-ot állít-e, nincs futtatva. |
| A Kiegyenesítés: ugyanaz a húzás `tilt=1,0.391249,0.000000`; az Undo/Redo felirata „Undo Straighten"/„Redo Crop" a vágás visszavonása után (`job-940`, `job-943`) | `session_effects.py` `append_tilt`, `tests/edit/test_session_tilt_halmozas_7393.py`, `tests/app/qml_functional/test_kiegyenesites_ujranyitas_7393.py` (a `0.391249`-et rögzítik) | **A #7393 nem cáfolt** (a 0,391249 negyedik független előfordulása). |
| A Clear All gomb kijelölt meglévő blokknál aktív, a „Copy Caption" tiltott (`job-941 __20`, `job-942 __20`) | #7407 (`edit_controller_text_mixin.py`) | **A #7407 nem cáfolt**; a Clear All hatásáról a négy új felvétel nem tartalmaz kockát. |

**A kiadott jegyek közül a #7408-at cáfolja részben a felvétel** (az Undo Save utáni verem láncszerkesztésnél); a #7393, #7406, #7407 egyikét sem.

#### Fejlesztői jegytörzsek (job-939..943): T, V; L felfüggesztve, a Retusálás-Cancel nincs jegytörzsként

**(T) Vágás kiegyenesített képen: a `crop64` forrásképi, az eredmény a kivágott ablakra alkalmazott kiegyenesítés (jegy: külön)**

> **Mi a hiba:** az eredeti Vágás eszköz kiegyenesített (`tilt`) képen a húzott téglalapot visszavetíti a forrásképre, és a `crop64`-et a FORRÁSKÉP törtkoordinátájában tárolja; a megjelenített eredmény a kivágott forrásablakra újra alkalmazott kiegyenesítés (az ablak saját méretéhez számolt kitöltő skálával). Nálunk a kijelzett (már kiegyenesített) kép törtkoordinátái kerülnek a `crop64`-be változtatás nélkül, a renderelő pedig a téglalapot a `tilt` mátrixával a kiegyenesített képre vetíti, ezért ugyanaz az ini más méretű és más tartalmú képet ad (501×180 a 371×167 helyett), és az eredeti által írt ini sem renderelődik helyesen.
>
> **Eredeti:** `job-943 __18` (húzás `(500,400)-(900,580)`: „Manual: 415 x 187"), `__20` („Recrop", állapotsor „371x167 pixels"), `__26` és `__28` („Manual: 312 x 104" → „293x98 pixels"), `__34` és `__36` („Manual: 415 x 228" → „361x199 pixels"; záró ini `crop64=1,6a402600c47fecff;` = 425 · 38 · 786 · 237); `job-922 __18-20` (ugyanaz az első húzás: `418029009e3fcfff` = 262 · 41 · 633 · 208, 371×167). A megjelenített kép a kivágott forrásablakra alkalmazott kiegyenesítés: az egész ablak ≤ 1 szinten egyezik a PicasaPy `apply_tilt`-jével a kivágott ablakra (371×167: átlagos eltérés 0,024; 361×199: 0,011), a tilt nélküli kivágás 9, ill. 8 szintig tér el. Bináris belépési pontok (`string_xrefs`): `editpanel/cropapply` `0x00c97624` (függvények `0x005ecd60`, `0x005e45c0`, `0x005f4130`, `0x005f90f0`, `0x005fa770`), `editpanel/cropselection` `0x00c95ae4` (többek közt `0x005ecd60`, `0x005d4b60`); a rekordlánc a lap szerint `0x005ecd60` → `0x005d4b60` → `0x006b0200` → `0x006b4300`. **A téglalap-leképezés (befoglaló + oldalarány) konkrét bináris helye nincs azonosítva**: a szabály három mintán mért, a jegy első lépése a `0x006b4300` és a `0x005d4b60` hívói közti leképezés olvasása.
>
> **Nálunk:** `src/picasapy/app/edit_controller_crop_mixin.py:93-123` (`applyCrop`: a [0..1] kijelölés változtatás nélkül `recrop`-ba), `:298-305` (`enterCropTool`: az előnézet a lánc `crop64` NÉLKÜLI, kiegyenesített képe), `src/picasapy/render/chain_ops.py:49-89` (`_apply_crop_op_lekepezve`: a téglalap az eredeti-kép koordinátája, a tilt mátrixával a kiegyenesített képre vetítve, két sarokból vágva), `src/picasapy/render/chain.py:640-655` (a mért sorrend ága). Futtatva a szürke rámpán: `tilt=1,0.391249,0.000000;crop64=1,418029009e3fcfff;` → 501×180, `...crop64=1,6a402600c47fecff;` → 492×222.
>
> **Teendő:** (1) a Vágás Apply a kiegyenesített képen húzott téglalapot a `tilt` cél → forrás mátrixával (`ops_geometry.tilt_matrix`) vetítse a forrásképre, és a `crop64`-et forrásképi törtkoordinátában írja: a téglalap magassága a visszavetített négyszög befoglalójának magassága, mérete a húzás méretének `k = befoglaló magasság / húzás magassága`-szerese felfelé kerekítve, a felső él a befoglaló teteje, vízszintesen a befoglaló közepére illesztve (a szabály A-ra és C-re a mért téglalapot adja, B-re a mért méretet 1 képponton belül). (2) a renderelő a `tilt` utáni `crop64`-et úgy alkalmazza, ahogy az eredeti: a téglalapot a forrásképen vágja ki, és erre az ablakra alkalmazza a kiegyenesítést (`tilt_scale` az ablak méretével, nem a teljes kép méretével); a kimenet mérete a `crop64` mérete. (3) a panel „Manual: W x H" felirata marad a húzás kijelzett mérete (ez egyezik az eredetivel). **Nem része:** a `crop64` utáni `tilt` (fordított lánc), más szög és más képméret képlete (egy szög, egy kép mérve), a kerekítés pontos szabálya (három mintára illeszkedik), a Vágás eszköz újranyitása kiegyenesített képen (a meglévő kijelölés visszatöltése), oldalarány-zárolt választások.
>
> **Kész, ha:** (1) a kiegyenesített 1024×256-os szürke rámpán a `(500,400)-(900,580)` húzás Apply-ja után az állapotsor 371×167 és a `crop64` `418029009e3fcfff` ±1 képpont; a `(350,420)-(650,520)` húzásé 293×98; a `(700,380)-(1100,600)` húzásé 361×199 és `6a402600c47fecff` ±1 képpont; (2) az eredeti által írt `tilt=1,0.391249,0.000000;crop64=1,418029009e3fcfff;` és `...6a402600c47fecff;` ini renderelt kimenete 371×167 és 361×199, és a `job-943 __20`, `__36` képterületétől ≤ 1 szinten tér el (a tilt nélküli vágás 9 és 8 szintig tér el, tehát a próba érzékeny); (3) tilt nélküli képen a vágás változatlan (a `job-911` húzása `370025009ebfdfff` = 415×187); (4) a szomszéd panelek (Kiegyenesítés, Vörösszem) képe változatlan.

**(V) Az Undo Save után az Undo gomb a visszaállított láncból épül (a #7408 pontosítása; jegy: külön)**

> **Mi a hiba:** az eredeti szerkesztő az Undo Save UTÁN a lánc szerint állítja be az Undo gombot: láncszerkesztésnél (Kiegyenesítés) „Undo Straighten" és aktív, a Redo tiltott; szövegnél (nincs lánc-eleme) tiltott és csupasz. Nálunk az Undo Save után mindkét verem üres és tiltott (#7408), ezért a láncszerkesztés visszavonása elvész.
>
> **Eredeti:** `job-940 __18` (Mentés után: „Undo Save", aktív, „Redo" tiltott, „23 KB"), `__20` (az „Undo Save" kattintása után: nincs ablak, „Undo Straighten" aktív, „Redo" tiltott, „31 KB", a kép a kiegyenesített: az `__14` képterületétől legfeljebb 3 szint az RGB-összegben), `__22` (a tiltott Redo hatástalan); záró fő ini `backuphash=30630`, `filters=tilt=1,0.391249,0.000000;`, `moddate=67eb71776d7bdd01`; `.picasaoriginals/.picasa.ini` 0 bájt, `.picasaoriginals/gray_ramp.jpg` nincs, `gray_ramp.jpg` 32 017 bájt az eredeti módosítási idővel. Szöveges ellenpélda: `job-919 __22` (Undo és Redo tiltott, csupasz). Bináris (`string_xrefs`): `Undo Save` `0x00c8a864`, `CThumbUI::FileRevert::undosave` `0x00c8a870` és a „To undo the last save and keep edits click 'Undo Save'." `0x00c8a804` (függvény `0x0053b2e0`), `Undo save and keep edits` `0x00cb1e5c` (függvény `0x007533b0`). A gombállapot újraszámításának bináris helye nincs azonosítva.
>
> **Nálunk:** `src/picasapy/app/edit_controller_history_mixin.py:108-114` (`_finish_save_undo`: siker esetén `_undo_stack.clear()` és `_redo_stack.clear()`), `src/picasapy/app/save_feedback.py:89-102` (`_on_undo_save_finished`: „az Undo Save lezárása után mindkét szerkesztőverem tiltott"); a lánc szerinti vermet az `edit_controller_session_mixin.py:120,262,399` (`_seed_undo_from_chain`) építi, az Undo Save utáni úton nem hívódik.
>
> **Teendő:** az Undo Save sikere után az Undo-verem épüljön újra a (visszaállított) láncból (`_seed_undo_from_chain`), a Redo-verem maradjon üres. Láncszerkesztésnél (Kiegyenesítés) így a gomb „Undo Straighten" és aktív; szövegszerkesztésnél (nincs lánc-elem) az eredmény változatlanul tiltott, csupasz Undo. **Nem része:** az „Undo Straighten" kattintásának hatása az Undo Save után (nincs mérve), több láncelem után az Undo Save (nincs felvéve), egymás utáni többszöri Mentés és Undo Save, a Mentés eredeti-mappa ini-kulcsai (a D jegytörzs része).
>
> **Kész, ha:** (1) Kiegyenesítés, Apply, Mentés, Undo Save után az Undo gomb „Undo Straighten" és aktív, a Redo tiltott, a kép a kiegyenesített (a renderelt próba a `job-940 __20`-szal veti össze); (2) a fő ini-ben a `filters=tilt=...` és a `moddate` áll, a `.picasaoriginals/gray_ramp.jpg` nincs, a kép a Mentés előtti bájtokat és módosítási időt kapja vissza; (3) Szöveg, Apply, Mentés, Undo Save után az Undo és a Redo tiltott, csupasz (a `job-919 __22`); (4) Mentés nélküli szerkesztésnél (Apply után) az Undo gomb nem „Undo Save".

### Job-949..950 (az ötödik javított kör: Retusálás Mégse és újranyitás, Szöveg forgatás szögtérképe)

**Bemenet és olvasat.** Két felvétel (1280×1024): `job-949` = `7327-11f`, `job-950` = `7327-12j`. Lépés/kocka: 30/31, 40/41; a `kepernyo__NN` az (NN-1). lépés utáni állapot. A döntő kockákat egyenként megvizsgáltam, az azonosakat md5-tel ellenőriztem; a feliratokat, gombállapotokat, gyűrűméreteket és szögeket közvetlen méréssel elemeztem.

#### Job-949 (`7327-11f`): Retusálás Mégse függő kijelöléssel és anélkül, újranyitáskori ecsetméret, semleges panelkattintás

Tesztkép: a 1024×256-os `gray_ramp.jpg`. A lépéssor: belépés a Retusálás eszközbe, a Brush Size fogantyú húzása 134 → 107 (t ≈ 0,242); Cancel függő kijelölés nélkül; újranyitás; első kattintás a képre (600, 450); semleges kattintás a panel üres területén (140, 600); kattintás a képre (900, 450); kattintás (600, 450); Cancel; második újranyitás.

| Kocka | Előtte végrehajtott lépés | Kép, panel |
|---|---|---|
| `__10-11` | `kattint (55,275)` (Retouch) | Friss panel; a fogantyú a sáv KÖZEPÉN (közép x = 134,5, sáv x 74..196, y 274..280); induló ecsetméret s = 0,25. |
| `__12-13` | `huz (134,277)-(107,277)` | A fogantyú közepe x = 105,5-106 (t = (105,5 - 79,5)/107,5 = 0,242). |
| `__14-15` | `kattint (200,391)` (Cancel) | **Függő kijelölés NÉLKÜL a Cancel azonnal KILÉP az Alapjavítások fülre**: a panel pixel (55, 275) = [79, 91, 144] (Alapjavítások Retouch csempe ikonja), a képterület és gombok bájtra azonosak (md5 = `a464342e`). |
| `__16-17` | `kattint (55,275)` (újranyitás 1.) | **A Retusálás panel megnyílik, és a csúszka PIXELRE AZONOS a Kocka 12 húzott állapotával** (`slider16 == slider12`, Max diff = 0): a fogantyú közepe x = 105,5-106, **az előzőleg beállított érték MEGMARAD**. |
| `__18-19` | `kattint (600,450)` (1. kattintás) | Gyűrű jelenik meg (600, 450) körül: világos pontok x = 579..622 (2Rx = 43 px), y = 427..472 (2Ry = 45 px), **mért sugár R = 22,5..23,0 képpont**. Az ecsetméret tehát pontosan a megőrzött t = 0,242 csúszkaérték szerinti (`97·0,242 = 23,5`), nem az induló R = 24,0! |
| `__20-21` | `kattint (140,600)` (semleges kattintás a panelen) | **A függő kijelölés nyomtalanul ELDOBÓDIK**: a gyűrű eltűnik a képről, a panel nyitva marad, a képterület bájtra azonos a megnyitáskori tiszta állapottal (`__20` md5-je azonos `__16`-tal, `503eaadb`). |
| `__22-23` | `kattint (900,450)` | **Új első kattintás jön létre** (új gyűrű jelenik meg (900, 450) körül, x = 877..922, y = 427..472, **mért R = 22,5..23,0**): a semleges kattintás utáni kattintás nem forráskattintásként foltot véglegesít, hanem új kijelölést indít. |
| `__24-25` | `kattint (600,450)` | Második kattintás (forrás) -> a folt létrejön a képen (a gyűrű az egér körül marad). |
| `__26-29` | `kattint (200,391)` (Cancel) | **A Cancel ismét KILÉP az Alapjavítások fülre** (`__26-29` bájtra azonos md5 = `16bddd2e`). |
| `__30-31` | `kattint (55,275)` (újranyitás 2.) | **A csúszka ismét pixelre azonos a húzott Kocka 12-vel** (`slider30 == slider12`, Max diff = 0): a fogantyú közepe x = 105,5-106, a megjegyzett érték többszöri kilépés és újranyitás után is stabil. |

**Eldőlt (949), nagy bizalommal:**
1. **A Cancel gomb függő kijelölés nélkül azonnal kilép az eszközből** az Alapjavítások fülre (`__14-15`, `__26-29`).
2. **A Cancel függő kijelöléssel (`job-939 __16-17`) nem lép ki, hanem először csak a függő kijelölést dobja el.**
3. **A panel semleges (nem vezérlőre eső) területére kattintás azonnal eldobja a függő kijelölést** (`__20-21`), a panel nyitva marad, a következő képre kattintás új első kattintás lesz (`__22-23`).
4. **Az ecsetméret (Brush Size) újranyitáskor MEGŐRZŐDIK**: mindkét újranyitáskor (`__16-17`, `__30-31`) a csúszka és a fogantyú pixelre azonos a korábban beállított állással (`slider12`), az ecsetkör mérete pedig a megjegyzett értéknek felel meg (R = 22,5..23,0, a t = 0,242 szerinti). Nem áll vissza az induló s = 0,25 / R = 24,0 alapértékre.

#### Job-950 (`7327-12j`): Szöveg forgatása, szögtérkép három húzással és a .picasa.ini

Tesztkép: a 1024×256-os `gray_ramp.jpg`. Szöveg: `PicasaPy7327` (12 karakter). Három kör: újranyitás, a blokk kijelölése, a forgató fogantyú húzása három különböző szögbe, az első kettőnél Cancel, a harmadiknál Apply.

| Kocka | Előtte végrehajtott lépés | Kép, panel |
|---|---|---|
| `__10-15` | Text eszköz nyitása, `PicasaPy7327` gépelése | Szöveg a képen. |
| `__16-17` | `kattint (88,406)` (Apply) | Alapjavítások fül, szöveg a képen rögzítve. |
| `__18-19` | `kattint (138,275)` (Text újranyitás) | Text panel nyitva. |
| `__20-21` | `kattint (620,405)` | A blokk kijelölve: **forgatókorong 24 osztással** (középpont kb. (627, 405), sugár R = 81), a piros pont a fogantyú közepén pontosan **(708,0; 405,0)**. |
| `__22-23` | `huz (708,405)-(708,422)` (1. húzás) | Nyers egérmozgás dy = 17, dx = 81 -> nyers szög = `atan(17/81)` = **11,85°**. A piros fogantyú pozíciója: **(707,7; 414,8)**, középpontból dy = 9,8, dx = 80,7 -> elfordulási szög **6,95°..7,13°** (Hough medián 6,65°). |
| `__24-25` | `kattint (191,406)` (Cancel) | Alapjavítások fül, az 1. forgatás elvetve. |
| `__26-27` | Text újranyitás | Text panel. |
| `__28-29` | `kattint (620,405)` | Blokk kijelölve, piros fogantyú újra (708,0; 405,0). |
| `__30-31` | `huz (708,405)-(708,445)` (2. húzás) | Nyers egérmozgás dy = 40, dx = 81 -> nyers szög = `atan(40/81)` = **26,28°**. A korong eltűnt, a forgatott keret és szöveg látható: a keret hosszú élének dőlése **30,17°**, Hough vonalak mediánja **30,02°** (pontosan a **30,000°** = π/6 rad 15°-os főosztás!). |
| `__32-33` | `kattint (191,406)` (Cancel) | Alapjavítások fül, a 2. forgatás elvetve. |
| `__34-35` | Text újranyitás | Text panel. |
| `__36-37` | `kattint (620,405)` | Blokk kijelölve, piros fogantyú újra (708,0; 405,0). |
| `__38-39` | `huz (708,405)-(708,458)` (3. húzás) | Nyers egérmozgás dy = 53, dx = 81 -> nyers szög = `atan(53/81)` = **33,20°**. A keret hosszú élének dőlése **38,52°**, Hough vonalak mediánja **38,07°**. |
| `__40-41` | `kattint (88,406)` (Apply) | Alapjavítások fül, forgatott szöveg rögzítve a képen. |

A záró `picasa.ini` szó szerint:
```ini
[gray_ramp.jpg]
text=1;133;12;PicasaPy7327;Times;0.322397,0.066892,0.039834,0.669879;v1,4294967295,4278190080,128.000000,1.000000,0.000000,1.000000,400,0,49152;;
backuphash=37406
textactive=1
```

A 3. húzás után a tárolt negyedik mező: **0.669879 radián = 38,3812°** (a renderelt szöveg dőlése Kocka 40-ben 38,4°..39,5°)!

##### KIEMELT: A Szöveg forgatásának szögtérképe és geometriája, LEZÁRVA (nagy bizalom)

Az öt mért mintából összeállított szögtérkép:

| Minta | Nyers egérmozgás | Nyers szög | Látható fogantyú / keret | Tárolt ini-szög (radián) | Tárolt fok | Megfigyelés |
|---|---|---|---|---|---|---|
| `job-950` 1. húzás | (708,405) → (708,422) | 11,85° | fogantyú (707,7; 414,8), keret 7,1° | nincs (Cancel) | - | finom, folytonos szög |
| `job-942` | (708,405) → (708,435) | 20,32° | fogantyú (703,3; 429,2), 17,6° | `0.300780` | 17,234° | finom, nem 15° többszöröse |
| `job-920` és `job-950` 2. húzás | (708,405) → (708,445) | 26,28° | keret 30,02°..30,17° | `0.523599` | 30,000° | **mágneses rászaladás** (30° = 2×15°) |
| `job-950` 3. húzás | (708,405) → (708,458) | 33,20° | keret 38,07°..38,52° | `0.669879` | 38,381° | finom, nem 15° többszöröse |

**Mit mond ki:**
1. **A forgatás FOLYAMATOS és finom**: a tárolt és látható szögek (7°, 17,234°, 38,381°) egyértelműen bizonyítják, hogy nem merev 15°-os diszkrét kvantálás működik. A 15°-os osztásoknál (pl. 30°-nál a nyers 26,28°-ból 30,000° lett) mágneses rászaladás (snap) lép fel, ha az egér a főosztás közvetlen vonzáskörzetébe esik.
2. **A forgatott blokk geometriájának változása**:
   - 0°: `x=0.316406, y=0.144531, s=0.033333, rot=0.000000`
   - 17,234° (0,300780 rad): `x=0.317762, y=0.110521, s=0.035546, rot=0.300780`
   - 38,381° (0,669879 rad): `x=0.322397, y=0.066892, s=0.039834, rot=0.669879`
   A függőleges eltolódás aránya a forgatási szöghöz képest szinte tökéletesen konstans lineáris: `dy / rad = -0,1131` (17,2°-nál) és `-0,1159` (38,4°-nál), vagyis `dy ≈ -0,115 · rad`. A vízszintes pozíció kismértékben nő (`dx / rad ≈ +0,0045..+0,0089`), a méretszorzó `s / s0` 1,0664 (17,2°) és 1,1950 (38,4°). A tárolt pont a forgatott szövegdoboz bal felső befoglaló sarka.
3. **Az L jegytörzs (Szöveg forgatókorong) ezzel véglegesíthető.**

#### Összevetés a mai PicasaPy-val és fejlesztői jegytörzsek (job-949..950): L véglegesítve, W

| Eredeti (mérés) | Nálunk (fájl:sor) | Ítélet |
|---|---|---|
| A Cancel gomb függő kijelölés mellett a félbehagyott foltot dobja el, kilépés nélkül; a panelre kattintás szintén eldobja; függő kijelölés nélkül kilép az Alapjavítások fülre (`job-949`, `job-939`) | `PhotoViewerEditorPanel.qml:216` (`onRetouchCancelRequested: editorPanel.retouchActive = false`: azonnal kilép a `retouchPatchPending` vizsgálata nélkül); a panel semleges kattintása nem dobja el a félbehagyott foltot (`cancelRetouchPatch()`) | **Eltérés** (W jegytörzs). |
| A Retusálás ecsetmérete újranyitáskor megőrzi az előzőleg beállított csúszkapozíciót (`job-949 __16, __30`) | `edit_controller_retouch_mixin.py:86-99` (`enterRetouchTool`: nem nullázza a `_brush_size`-t) | **Egyezik a kontrollerben**, a felületi őrök és a Cancel-viselkedés köti be helyesen. |
| A szövegblokk kijelölésekor forgatókorong jelenik meg (24 osztás, R = 81), folyamatos forgatással és 15°-os snap-pel, a `text=` negyedik mezőjébe radián kerül, az y eltolódás lineáris (`job-950`, `job-942`, `job-920`) | `PhotoViewerPhotoArea.qml:667-722` (nincs forgatókorong, csak 1 px kék keret, nem forgatható) | **Eltérés** (L jegytörzs, véglegesítve). |

##### (L) Szöveg: a kijelölt blokk forgatókorongja és a forgatás tárolása (jegy: külön; FÉLKÉSZ, a `job-953`..`job-955` dönti el, addig nem megy ki)

> **Mi a hiba:** az eredeti Szöveg eszközben a képen kattintással kijelölt blokk köré forgatókorong rajzolódik (24 osztás, 15°-onként, R = 81 fogantyú-sugár), amelynek piros fogantyúját húzva a blokk finoman, folyamatosan elfordul; a mért pontok szerint a 15° többszöröseire rászalad (a 26,28° nyers húzás 30,000° lett), de a rászaladás sávja és a nyers húzásszög leképezése **NINCS MEG** (a 11,85° nyers húzás látható szöge 6,95°..7,13°, a 20,32°-é 17,234°, a 33,20°-é 38,381°: ez nem azonosság, és a sáv legalább 3,7°, nem ±2°), és az elfordulás a `text=` sor geometriájának negyedik mezőjébe kerül radiánban, miközben a tárolt pozíció a forgatott blokk bal felső sarkaként módosul (`dy ≈ -0,115 · rad`). Nálunk a kijelölt blokk csak egy vékony kék keretet kap, forgatókorong nincs, forgatni nem lehet.
>
> **Eredeti:** `job-920 __28` (korong 24 osztással, fogantyú 81 px-re), `job-942 __20-22` (tárolt 17,234° = 0,300780 rad), `job-950 __20-23` (nyers 11,85° → látható 6,95°..7,13°), `job-950 __30` (nyers 26,28° → 30,000° snap), `job-950 __38-40` (nyers 33,20° → tárolt 38,381° = 0,669879 rad); geometriák: 0° `(0.316406, 0.144531, 0.033333)`, 17,2° `(0.317762, 0.110521, 0.035546)`, 38,4° `(0.322397, 0.066892, 0.039834)`.
>
> **Nálunk:** `src/picasapy/app/qml/PicasaPy/PhotoViewerPhotoArea.qml:667-722` (a kijelölt blokk 1 képpontos kék kerete; a `rotation` a fájlból olvasott érték, `transformOrigin: Item.TopLeft`, fogantyú és interakció nincs), `src/picasapy/app/edit_controller_text_mixin.py:446-470` (`selectTextOverlay`), `src/picasapy/ini/text_overlay.py:123-137,406-415` (a forgatás radiánban parszolva és írva).
>
> **Teendő:** (1) a kijelölt szövegblokk köré forgatókorong rajzolása: 24 osztásvonal (15°-onként), a kör sugara a `job-920 __28` kockáján mérendő (**NINCS MEG**), a fogantyú nyíllal a vízszintes tengelyen 81 képpontra a középponttól, piros fogantyúponttal; (2) a fogantyú húzása a `job-953`..`job-955` mérésével meghatározott leképezés szerint forgassa el a blokkot, és a mért sávban szaladjon rá a 15° többszöröseire; (3) az elforgatás radiánban a `text=` negyedik mezőjébe kerüljön pozitív (óramutató szerinti) előjellel, a tárolt `x`, `y` a forgatott befoglaló bal felső sarkaként frissüljön; (4) Apply után a forgatott szöveg maradjon a képen, az Undo és Redo maradjon tiltott (szöveg-invariáns).
>
> **Kész, ha:** (1) meglévő vagy friss szövegre kattintva megjelenik a 24 osztásos forgatókorong és a piros fogantyú; (2) a fogantyú húzásakor a szöveg elfordul, 30° környékén rászalad a 30,000°-ra (`0.523599`), köztes szögnél finoman beállítható (pl. 17,2° és 38,4°); (3) Apply után a `text=` negyedik mezője a beállított radiánértéket kapja; (4) a renderelt próba a forgatott blokkot a `job-950 __40` képével veti össze.

##### (W) Retusálás: Cancel függő kijelölésnél és semleges panelkattintás (jegy: külön)

> **Mi a hiba:** az eredeti Retusálás eszközben ha van félbehagyott folt (az első kattintás megtörtént a javítandó területre, de a második forráskattintás még nem), a „Mégse” (Cancel) gomb kattintása NEM lép ki az eszközből, hanem csak a félbehagyott foltot dobja el, és az eszköz nyitva marad. Ugyanígy a bal panel semleges (nem vezérlőre eső) területére kattintás is eldobja a félbehagyott foltot, és a következő képre kattintás új első kattintás lesz. Csak akkor lép ki az Alapjavítások fülre a Mégse gomb, ha nincs félbehagyott folt. Nálunk a QML közvetlenül zárja az eszközt (`retouchActive = false`), függetlenül attól, hogy van-e függő folt.
>
> **Eredeti:** `job-949 __14-15` (függő kijelölés nélkül a Cancel azonnal kilép az Alapjavítások fülre), `job-939 __16-17` és `job-949 __20-21` (függő kijelölésnél a Cancel, illetve a panelre kattintás (140, 600) a gyűrűt leveszi, a képterület visszaáll az induló tiszta állapotra, a panel nyitva marad), `job-949 __22-23` (a panelkattintás után a képre kattintva új gyűrű nyílik (900, 450) körül, nem folt véglegesül); `job-949 __26-29` (újabb Cancel kilép az Alapjavítások fülre); `job-949 __16, __30` (újranyitáskor az előzőleg beállított ecsetméret megmarad).
>
> **Nálunk:** `src/picasapy/app/qml/PicasaPy/PhotoViewerEditorPanel.qml:216`:
>
> ```qml
> onRetouchCancelRequested: editorPanel.retouchActive = false
> ```
>
> A vezérlőben megvan a `cancelRetouchPatch()` slot (`src/picasapy/app/edit_controller_retouch_mixin.py:157-166`), de a Cancel gomb nem hívja, és a panel felülete sincs bekötve.
>
> **Teendő:** (1) a Retusálás panel Mégse gombja (`onRetouchCancelRequested`) vizsgálja meg, hogy van-e félbehagyott folt (`retouchPatchPending`): ha van, hívja meg az `editController.cancelRetouchPatch()`-et és NE zárja be az eszközt (`retouchActive` maradjon `true`); ha nincs félbehagyott folt (`!retouchPatchPending`), akkor lépjen ki az eszközből (`retouchActive = false`); (2) a bal panel üres területére kattintás szintén hívja meg a `cancelRetouchPatch()`-et, ha van függő folt; (3) újranyitáskor a panel csúszkája és az ecsetméret őrizze meg az előzőleg beállított értéket (a kontroller már megőrzi, a felületi kötés ezt tartsa tiszteletben).
>
> **Kész, ha:** (1) első kattintás után (gyűrű a képen) a Mégse gombra kattintva a gyűrű eltűnik, de a Retusálás panel nyitva marad; (2) újabb Mégse kattintásra a panel bezárul és visszatér az Alapjavítások fülre; (3) első kattintás után a panel üres területére kattintva a gyűrű eltűnik, és a következő kattintás a képre új első kattintást készít; (4) függő folt nélküli Mégse kattintásra azonnal visszatér az Alapjavítások fülre; (5) a renderelt próba az állapotokat a `job-949 __14`, `__16`, `__20` kockáival veti össze.

#### Vörösszem (13): kell-e még mérés?

**Igen, kell**: a #7378 (a mentett kiegyenesítésnél felugró Info-ablak, a panelcím és a megjegyzés) és a #7386 (a panel gombsora, megjegyzése, a fülsáv) a `job-837` felvételét valósítják meg; a Vörösszem Apply-ja, az Undo-megerősítése és a mentett fájl semelyik felvételen nincs mérve (a `edit_controller_history_mixin.py:19-22` megjegyzése is ezt mondja: „a Vörösszem eredeti viselkedése nincs mérve (7327-10)"), tehát a két jegy ezt NEM fedi. A hiány pontosan: a PicasaTeszt mesterpéldányban nincs vörösszemes tesztkép. Megnevezett irány: szabadon használható, vörösszemes fotó szerzése stockfotó-tárból és bemásolása a PicasaTeszt mappa mesterpéldányába, utána a `7327-10` lefuttatása.

A `7327-11f` (`job-949`) és `7327-12j` (`job-950`) lefutott és kiértékelt; a `7327-10` (Vörösszem Apply, Undo, Mentés) lépéssora változatlanul a `.tmp/javitott-lepesek/` mappában vár a vörösszemes tesztképre.

### Mért koordináták a további Colab-feladatokhoz

A #798 `kepernyo__23.png` képe 1280 × 1024 felbontású. A gombképek középpontját képpontban mértem; a Crop panelben nincs csúszka.

| Crop vezérlő | Koordináta | Forrás |
|---|---:|---|
| Apply | `(84,403)` | mérés (job-798, `kepernyo__23.png`) |
| Cancel | `(188,403)` | mérés (job-798, `kepernyo__23.png`) |
| Reset | `(136,368)` | mérés (job-798, `kepernyo__23.png`) |
| Crop slider | NINCS MEG: a felvételen csúszka nincs | mérés (job-798, `kepernyo__23.png`) |
| Straighten csúszka | fogantyú alapállásban `(689,863)`, a sáv x 557-823, y 850-877 | mérés (job-836 `__10`) |
| Straighten Apply / Cancel | `(875,863)` (x 835-916) / `(962,863)` (x 922-1003), y 850-877 | mérés (job-836 `__10`) |
| Redeye Auto / Preview / Reset | `(83,332)` / `(189,332)` / `(136,365)` | mérés (job-837 `__10`) |
| Redeye Apply / Cancel | `(83,400)` / `(190,400)` | mérés (job-837 `__10`) |
| Retouch Brush Size csúszka / Reset | `(134,277)` (sáv x 74-196) / `(135,309)` | mérés (job-838 `__14`) |
| Retouch Undo Patch / Redo Patch | `(73,345)` / `(198,344)` | mérés (job-838 `__14`) |
| Retouch Apply / Cancel | `(74,391)` / `(200,391)` | mérés (job-838 `__14`) |
| Text Font / Size | `(170,173)` / `(93,203)` | mérés (job-839 `__14`) |
| Text B / I / U | `(185,202)` / `(215,202)` / `(245,202)` | mérés (job-839 `__14`) |
| Text igazítás bal / közép / jobb | `(185,233)` / `(215,233)` / `(245,233)` | mérés (job-839 `__14`) |
| Text szövegszín / áthúzott négyzet / körvonalszín / vastagság-csúszka | `(40,276)` / `(69,276)` / `(124,276)` / `(192,278)` | mérés (job-839 `__14`) |
| Text Transparency csúszka | `(149,337)` | mérés (job-839 `__14`) |
| Text Copy Caption / Clear All | `(86,372)` / `(189,372)` | mérés (job-839 `__14`) |
| Text Apply / Cancel | `(88,406)` / `(191,406)` | mérés (job-839 `__14`) |
| Felugró ablakok | „Save” `(687,553)` és „Cancel” `(766,553)` (836 `__26`); „Confirm” „Undo” `(687,543)` és „No” `(766,543)` (838 `__36`); „Info” „OK” `(643,566)` (837 `__22`) | mérés |

A mért koordináták bekerültek a munkafa `.tmp/colab-kitoltott/7327-8a-vagas-alkalmaz-visszavon.json` és `.tmp/colab-kitoltott/7327-8b-vagas-megse-alaphelyzet.json` kimenetébe. A 9, 10, 11 és 12 feladat koordinátái a `job-836`..`job-839` felvételeiből mértek (a vezérlők befoglaló dobozának közepe, kb. ±2 képpont); a javított lépéssorok ezeket használják.

### Igazolt fejlesztői eltérések és javasolt jegytörzsek

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A `Ctrl+Shift+E` az eredeti szerkesztőben a Jó napom van műveletet aktiválja: bináris `0x005e638b` → `0x005fe370(panel, "enhance")`; mérés (job-810, `kepernyo__13` és `__15`). | `MainKeyboardShortcuts.qml:166-174`: `sequence: "Ctrl+Shift+E"`; `enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve`; `onActivated: hostWindow.kotegEffekt("enhance")`. A `MainWindowCommands.qml:171-172` kapuja `!hostWindow.viewerOpen`. | A szerkesztőben a Ctrl+Shift+E legyen elérhető az aktuális képen, és aktiválja a Jó napom van csempét. A könyvtári út adat-/fájleffektjét külön kell mérni, mielőtt annak viselkedését módosítjuk. |
| A `cropapply` út (`0x005ecd60`) a `cropselection` aktív panelállapotában a `FUN_006b0200` → `FUN_006b4300` láncon módosítja a rekordlistát. Ha a lista utolsó eleme `crop64` (`0x00c80adc`), a meglévő téglalap koordinátái íródnak át (`0x006b43bd`-`0x006b447b`); egyébként új rekord kerül a lista végére (`0x006b452e`-`0x006b4662`). | `src/picasapy/app/edit_controller_crop_mixin.py:119-124` hívja az `append_crop()`-ot; `src/picasapy/edit/session_core.py:123-124` szó szerint új `crop64` műveletet fűz a teljes lánchoz. | Az új Crop csak akkor helyettesítse a lánc végén álló `crop64` téglalapot, ha közvetlenül az az utolsó művelet; egyébként maradjon a láncvégi hozzáfűzés. A pontos jegytörzs lent szerepel. |

**Javasolt fejlesztői jegytörzs:**

> A Picasa 3.9 szerkesztőjében a Ctrl+Shift+E a Jó napom van műveletet indítja (`0x005e638b` → `0x005fe370(panel, "enhance")`; `job-810` képein a csempe halványra vált és az Undo felirat `Undo I'm Feeling Lucky`). A PicasaPy jelenlegi kötése:
>
> ```qml
> sequence: "Ctrl+Shift+E"
> enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve
> onActivated: hostWindow.kotegEffekt("enhance")
> ```
>
> `Eredeti:` a `Ctrl+Shift+E` a szerkesztőben a Jó napom van eszközt aktiválja.
>
> `Nálunk:` a gyorsbillentyű egyetlen kötése könyvtári köteg-effekt, a `!hostWindow.viewerOpen` kapu miatt a szerkesztőben letiltott (`MainKeyboardShortcuts.qml:166-174`, `MainWindowCommands.qml:171-172`).
>
> `Teendő:` a szerkesztőben is legyen elérhető a `Ctrl+Shift+E`, és az aktuális képen ugyanazt a Jó napom van csempét aktiválja; a könyvtári út jelenlegi viselkedése maradjon külön ellenőrzési pont.
>
> `Kész, ha:` egy megnyitott képnél a Ctrl+Shift+E után a Jó napom van csempe aktív állapotot jelez és az Undo felirat a művelet nevét mutatja; a könyvtári egyképes és többképes viselkedés külön ellenőrizhető, és a billentyű szövegmező-fókusz közben nem fut.

**Javasolt fejlesztői jegytörzs - egymást követő vágások:**

> Az eredeti Picasa 3.9 `cropapply` útja (`FUN_005ecd60`, `0x005ece75`-`0x005ecece`) a `FUN_005d4b60`-hoz jut. Aktív `cropselection` panelnél a hívási lánc a `FUN_006b0200`-n keresztül eléri a `FUN_006b4300`-at. Ez a lista utolsó elemét `crop64`-hez hasonlítja (`0x006b43bd`-`0x006b43ee`); egyezéskor a meglévő rekord négy koordinátáját frissíti (`0x006b4472`-`0x006b447b`), más típusú végrekord esetén pedig új `crop64` elemet készít és a lista végére fűz (`0x006b452e`-`0x006b4662`).
>
> **Eredeti:** közvetlenül egymás után alkalmazott, megváltozott Crop esetén a lánc végi `crop64` rekord koordinátái változnak (új elem és redo-ürítés nélkül); üres téglalapnál az utolsó `crop64` törlődik. Ha a lánc üres vagy más művelet áll a végén, érvényes téglalapnál az új Crop külön rekord a lista végén, és a redo-lista kiürül; üres téglalapnál nem történik semmi.
>
> **Nálunk:** `src/picasapy/app/edit_controller_crop_mixin.py:119-124` minden megváltozott kijelölésnél hívja az `append_crop()`-ot. A jelenlegi kód:
>
> ```python
> new_op = _new_op("crop64", ("1", encode_rect64(rect)))
> return EditSession(ops=self.ops + (new_op,))
> ```
>
> A `session_core.py:123-124` nem vizsgálja, hogy a lánc utolsó művelete `crop64`-e, ezért ismételt Cropnál is új elemet ad hozzá.
>
> **Teendő:** a Crop Apply lánckezelése a lánc utolsó eleme szerint ágazzon. Ha az `crop64` és az új téglalap érvényes, írja át annak koordinátáit helyben (új elem és redo-ürítés nélkül); ha `crop64` és a téglalap üres, törölje az utolsó elemet. Ha a lánc üres vagy más művelet áll a végén, érvényes téglalapnál fűzzön új `crop64` elemet a végére és ürítse a redo-listát (üres téglalapnál ne tegyen semmit). A közbeeső és korábbi műveletek maradjanak; a mentett `crop=` mindig az (új) utolsó `crop64` tükre. Az Undo/Redo végállapotot az eredeti Picasa helyes előfeltételű felvételéhez igazítsa.
>
> **Kész, ha:** (1) `crop64` végű láncra végzett, érvényes és eltérő téglalapú Crop Apply után az utolsó rekord koordinátái változnak, a rekordok száma nem nő, a redo-lista nem ürül; (2) ha a lánc üres vagy `bw` (vagy más művelet) áll a végén, az új Crop külön rekordként a végére kerül, a korábbi elemek érintetlenek, a redo-lista kiürül; (3) `crop64` végű láncon üres téglalappal végzett Apply törli az utolsó `crop64`-et, más végrekordnál az üres téglalap nem változtat a láncon; (4) minden esetben a `crop=` tükörértéke a hatályos (utolsó) vágás, a mentett `filters=` lánc a várt rekordokat tartalmazza; (5) két közvetlenül egymás utáni Apply után EGY Undo mindkét vágást visszaveszi (vágatlan kép, az eszköz felirata „Crop", a Visszavonás letiltva), a Redo a MÁSODIK téglalapot hozza vissza; ha a két vágás között más művelet áll, az újravágás Undo-ja az előző vágást állítja vissza; (6) az (5) pont látható állapotát (kép, gombok) a `job-821` helyes újrafelvétele megerősítette (`__20`, `__22`, `__24`, `__26`, `__28`); az eszközfelirat „Crop”/„Recrop” váltása külön tétel (lásd „Job-821 nyomán (A)”).
>
> **Állapot (1.0.171):** ez a jegytörzs a #7367-ben megvalósult (`recrop.py`, `edit_controller_crop_mixin.py:111-123`; tesztek: `tests/app/test_edit_controller_recrop_7367.py`, `tests/edit/test_session_recrop_7367.py`). A fenti „Nálunk” bekezdés fájl:sor hivatkozásai a javítás előtti kódra vonatkoznak.

### Nyitott pontok és következő bizonyító lépés

- **Lezárva a `job-836`..`job-839`-cel:** a Straighten, Redeye, Retouch és Text panel megnyitása, felépítése, alapértéke, koordinátái, a Cancel és az Apply hatása (a `job-798` újrafelvétele helyett). A javított lépéssorok közül lefutott és kiértékelt: `7327-8d`, `7327-9`, `7327-9b`, `7327-11`, `7327-11b`, `7327-12`, `7327-12b` (`job-907`..`job-913`, lásd „Job-907..913”); hátra van a `7327-10` (vörösszemes tesztkép kell) és a „Javított lépéssorok (job-907..913 nyomán)” kilenc új sora (ez a kilenc a `job-917`..`job-925` felvételekkel lefutott; lásd „Job-917..925”).
- `job-809` batch útjának ini/DB/export/állapotsor mérése; a képernyőkép kijelölést mutat, de az írásokat nem.
- **Lezárva a `job-837`-tel:** a Vörösszem tilt-figyelmeztetése (a tilt a feladat saját Kiegyenesítés-lépéséből keletkezett, a záró ini `filters=tilt=1,0.391249,0.000000;`); a `job-811` megismétlése nem kell.
- `job-821` (két egymás utáni vágás, majd Undo, Redo, Undo, Undo) **lezárta** az ismételt Apply utáni látható Undo/Redo állapotot (a `job-815` csupa fekete kockái és a `job-813 kepernyo__20` hibás előfeltétele helyett). A 29 képkockából a döntők: `__14` (Apply 1 után „Recrop”, aktív „Undo Crop”, 415×187), `__20` (Apply 2 után 415×188), `__22` (EGY Undo után vágatlan kép, „Crop”, tiltott Undo, „Redo Crop”), `__24` (a Redo a második vágást hozza vissza, képpontra azonos az `__20`-szal), `__26` és `__28` (bájtra azonos `__22`-vel, a tiltott gombon az Undo nem hat); a záró ini: `redo=crop64=1,84bf4400ec7fffff;`, `filters=` nincs. A kockánkénti tábla és a döntés a „job-821” alszakaszban. Az első Apply utáni ini és a `redo=` írási időpontja nincs felvéve: lásd a következő pontot.
- **Lezárva a `job-829`..`job-832` alapján:** a `redo=` az eredetiben a szerkesztés alatti, újranyitáskor eldobott tükör; a látható viselkedés a PicasaPy-ban egyezik, fejlesztői jegy nem kell (részletek a „Job-821 nyomán (B)” pontban). A `job-911` lezárta az újranyitott kijelölés 187→188 kérdését: az első Apply után a tárolt téglalap 415×187, a 188 csak az újranyitás utáni megjelenítési úton keletkezik.
- **Fejlesztői jegytörzs kész:** a Crop csempe „Recrop” felirata („Job-821 nyomán (A)”).
- A teljes kimenetből a `job-907`..`job-913` után hiányzik: a Redeye Apply/Undo/Save (`7327-10`), a Retusálás ecsetméretének köztes állásai és a képméret/nagyítás szerepe (`7327-11c`, `7327-11d`), a Szöveg Clear All utáni Cancel, a helyben szerkesztett blokk ini-je, a forgatókorong és az „Undo Save” gomb hatása (`7327-12d`, `7327-12e`, `7327-12f`), a Vágás-figyelmeztetés a megnyitás után, a Kiegyenesítés végállása és a két `tilt` tagú lánc Undo/Redo-ja (`7327-9c`, `7327-9d`, `7327-9e`), az index a Mentés után (`7327-9f`). A `job-917`..`job-925` után hiányzik: a Redeye Apply/Undo/Save (`7327-10`), a Retusálás újranyitáskori állapota és a középállás (`7327-11e`), a láncszerkesztés „Undo Save”-je (`7327-12g`), a szerkesztett és forgatott blokk geometriája és a szög lépése (`7327-12h`, `7327-12i`), a Vágás kiegyenesített képen (`7327-9g`).
- **Fejlesztői jegytörzsek kész (`job-907`..`job-913`):** G (ecsetméret, előfeltétele `7327-11c` és `7327-11d`; a #7379 494-es osztója a mérés szerint nem adható ki), H (az Újra a retusálás-visszavonás után letiltott), I (nincs Vágás-figyelmeztetés a megnyitáskor), J (a Kiegyenesítés újranyitása és a csúszka 253 képpontos skálája).
- **Fejlesztői jegytörzsek kész (`job-917`..`job-925`):** G véglegesítve (ecsetméret), M (a Clear All eszközön belüli piszkozat, a Cancel visszahozza), N (Mentés után az Undo gomb „Undo Save”); L (a forgatókorong) előfeltétele a `7327-12h` és `7327-12i`.
- **A `job-939`..`job-943` után hiányzott:** a Vörösszem Apply/Undo/Mentés (`7327-10`, vörösszemes tesztkép kell), a Retusálás újranyitáskori csúszka- és ecsetállapota és a Cancel függő kijelöléssel (`7327-11f`), a forgatás egér-szög → tárolt szög leképezése és a geometria képlete forgatott blokknál (`7327-12j`).
- **Lezárva a `job-939`..`job-943`-mal:** az 1:1 gomb a Retusálásban (100%, a gyűrű R = 100·s·z, `job-939`); az Undo Save láncszerkesztésnél (`job-940`: „Undo Straighten” aktív, V jegytörzs); a szerkesztés önmagában nem változtat a szöveg geometriáján, a kijelölő kattintás a kurzort a kattintott karakterhatárra teszi (`job-941`); a Vágás kiegyenesített képen (`job-943`: forrásképi `crop64`, a kivágott ablakra újra alkalmazott kiegyenesítés, a húzott → tárolt téglalap szabálya három mintára, T jegytörzs).
- **Lezárva a `job-949` és `job-950`-nel:** a Retusálás Cancel viselkedése függő kijelölés nélkül (azonnal kilép) és függő kijelöléssel (csak a kijelölést dobja el), a panel semleges kattintása (eldobja a függő kijelölést), az ecsetméret és fogantyú megőrzése újranyitáskor (`job-949`, W jegytörzs); a Szöveg forgatásának szögtérképe (7°, 17,2°, 30,0°, 38,4°), a folytonos szög mágneses rászaladása 15°-os osztásoknál, a forgatott geometria függőleges eltolódása (`dy ≈ -0,115 · rad`) és tárolása (`job-950`, L jegytörzs véglegesítve).
- **Fejlesztői jegytörzsek kész (`job-939`..`job-950`):** T (Vágás kiegyenesített képen), V (az Undo Save utáni Undo-verem a láncból épül, a #7408 pontosítása), L (Szöveg forgatókorong és forgatott geometria, véglegesítve), W (Retusálás Cancel függő kijelölésnél és semleges panelkattintás).
- **Egyetlen nyitott blokkolt kérdés maradt:** a Vörösszem Apply/Undo/Mentés (`7327-10`), amelyhez valódi vörösszemes tesztkép szükséges a PicasaTeszt mappa mesterpéldányába.

## Nyitott kérdések mérlege

A pontok száma 19. A `job-949` és `job-950` után a (14) Retusálás lezárult, a (15) Szöveg a forgatás leképezésén kívül lezárult; a leképezést a `job-953`..`job-955` méri. Egyetlen blokkolt pont maradt: a (13) Vörösszem (vörösszemes tesztképre vár). Minden pont pontosan egy csoportban áll.

- **Lezárva (15):**
  1. a szerkesztői `Ctrl+Shift+E` paritáshiánya;
  2. Crop Apply/Undo/Redo új, vágatlan képen;
  3. Crop Reset, új kijelölés, Cancel, Apply nélkül;
  4. a bináris Crop-végrekord szabálya és az eltérés (a #7367 javította);
  5. az ismételt Apply utáni látható Undo/Redo gomb- és képállapot (`job-821`);
  6. a `redo=` írási ideje és az újranyitás utáni Redo (`job-829`..`job-832`);
  7. a Kiegyenesítés panel felépítése, alapállása, húzása, Cancelje és Apply-ja, az Undo/Redo felirat és kép, az ini-sor (`job-836`);
  8. a Vörösszem panel alapállapota és a tilt-figyelmeztetés futásidejű feltétele és alakja (`job-837`);
  9. a Retusálás panel elemei, a kétkattintásos folt, a helyi Undo/Redo/Reset, a Cancel, az Apply, a megerősítő ablak szövege és alakja (`job-838`);
  10. a retusált kép végső fájl- és ini-állapota (`job-838`);
  11. a Szöveg panel felépítése, a képre gépelés, a Cancel, az Apply, az Undo hiánya és az ini-sor (`job-839`);
  12. Kiegyenesítés és Vágás: a Vágás-figyelmeztetés aktív kiegyenesítés mellett sehol nem jelenik meg, a csúszka végállása `-1,000000` és `1,000000`, a fogantyú KÖZEPE lineárisan járja a 253 képpontot, minden Apply külön visszavonási lépés (`job-922`..`job-924`), és a Vágás kiegyenesített képen (`job-943`): a `crop64` forrásképi, az eredmény a kivágott ablakra újra alkalmazott kiegyenesítés, a húzott → tárolt téglalap szabálya (T jegytörzs);
  14. **Retusálás lezárva:** az ecsetméret lineáris leképezése (`R = 100·s·z`), a kép méretétől független, a nagyítással arányos, az 1:1 gomb 100%-ra állít (`job-917`/`job-918`/`job-939`), a Cancel függő kijelölés nélkül azonnal kilép az Alapjavítások fülre, függő kijelöléssel csak a kijelölést dobja el, a panel semleges kattintása szintén eldobja a kijelölést, újranyitáskor a csúszka és az ecsetméret megmarad (`job-949`, W jegytörzs);
  15. **Szöveg, a forgatás nélkül lezárva:** az Undo Save hatása szövegnél és láncszerkesztésnél (N és V jegytörzs), a Clear All utáni Cancel (M), a helyben szerkesztett blokk (egy blokk, a szerkesztés a geometriát nem változtatja, a kattintás a kurzort a karakterhatárra teszi, `job-941`), a forgatás tárolása (a negyedik mező radián, `job-942`, `job-950`); a forgatás leképezése az L jegytörzsben nyitott, lásd a blokkolt pontot;
  17. a Crop első Apply után mentett téglalap mérete és a 187/188 kérdés (`job-911`).
- **Blokkolt (1):** (13) Vörösszem: Apply, Undo-megerősítés, mentett fájl. **Kell még mérés**: a #7378 és a #7386 a `job-837` felvételét (panel, megjegyzés, tilt-Info) valósítja meg, az Apply/Undo/Mentés nincs mérve, tehát nem fedik. Hiány: valódi vörösszemes tesztkép a PicasaTeszt mesterpéldányban; irány: szabadon használható vörösszemes fotó stockfotó-tárból, utána `7327-10`.
- **Nyitott részkérdés a (15)-ön belül:** a Szöveg forgatókorongjának húzásszög-leképezése és rászaladási sávja (L jegytörzs). Irány: a `job-953`..`job-955` (7327-12ka..c) söprése nyolc húzásszöggel; az eredmény után az L véglegesíthető.
- **Hatókörön kívül (3):** (16) a Picasa saját PMP/db3 indexének írása a Mentés és a leállítás után (`job-925`: oszlopfájl nincs; a PicasaPy saját SQLite indexet ír, az eredeti adatbázist csak olvassa); (18) a toolbar-gombok súgója: a Colab végrehajtó lépéskészletében nincs egérmozgatás (hover), ezért ezen a csatornán nem mérhető; a súgószöveg a Picasa saját erőforrásaiból (a `stringres` és a `tooltips` táblákból) olvasható, a menü- és helyi menü-állapotokat a `job-807` és a `job-808` már mérte; (19) a hálózati és írásvédett helyek, a teljes hibaszöveg: a Wine-ban csak a `C:` meghajtó látszik, a végrehajtónak nincs hálózati vagy írásvédett helye; a hibaszövegek a binárisból (`IDS_*` sztringek) nyerhetők.
- **Nyílt névtelen (0).**

Állapotsor: **0 nyílt névtelen · 15 lezárva · 1 blokkolt · 3 hatókörön kívül**; az összeg 19. A blokkolt (13) pont kivételével a #7327 minden kérdése lezárult. A feltárt eltérésekre kész fejlesztői jegytörzsek (G, H, I, J, L, M, N, T, V, W) önálló fejlesztési jegyként vihetők át kódba; az L csak a `job-953`..`job-955` után.
