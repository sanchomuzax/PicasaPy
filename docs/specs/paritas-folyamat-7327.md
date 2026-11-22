# A szerkesztő Alapjavítások eszközeinek folyamata (#7327)

**Státusz: nyitott, feltételes.** Az eredeti menü- és eszközutak több részlete a binárisból azonosítható, a jelenlegi PicasaPy útjai forrásból követhetők, és a #798, #807-812 mérések részfolyamatokat rögzítenek. A `Ctrl+Shift+E` szerkesztői használatánál igazolt eltérés van: az eredeti működést a bináris és a #810 kép mutatja, míg a PicasaPy kötése csak könyvtárnézetben él. A kilenc művelet teljes, belépéstől fájlmentésig tartó összevetéséhez továbbra sincs elegendő felvétel.

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
| **Vágás.** Eredeti eszközbelépő `0x005efa30`; felületi mezők, aránylista, javaslatok és Alkalmaz/Mégse/Reset vezérlők a `ui-audit-editor.md` 5. szakaszában. A vágás rétegződését és `filters=`/`crop=` szerepét a `filters-decoded.md` „Az ÍRÁS oldala: az újravágás HALMOZ” szakasza tárgyalja. | A csempe: `EditorTabCommonFixes.qml:91-99`, a panel és figyelmeztetés: `EditorCropPanel.qml:54-85`, gombok: `EditorCropPanel.qml:380-402`. Az Alkalmaz és visszavonás: `edit_controller_crop_mixin.py:92-137`; a mezőnyitáskor visszaállított képarány: `EditorPanel.qml:293-306`. | **Meglevő rész-egyezés:** a `vagas-eszkoz-allapot.md` már rögzíti a 19 mai arányt, a három javaslatot, a Reset jelentését és az újravágás halmozását. `NINCS MEG`: eredeti és mai futó belépési feltétel, alapállapot megjegyzése, Apply/Cancel utáni fájl, bal panel, rács, kijelölés és mentés összevetése. A Colab-felvétel az eszközt tiszta és már vágott képen végezze el. |
| **Kiegyenesítés.** Eredeti vezérlőneve `horizonadjust`; a `ui-audit-editor.md` a `job-70` 4. képéből az eszköz közbeni szürke panelállapotot dokumentálja (`:653`). A kiegyenesítés és a vörösszem-javítás kölcsönhatására vonatkozó red-eye figyelmeztetést a `0x005f30e0` út kezeli, lásd lent. | Csempe: `EditorTabCommonFixes.qml:100-112`; csúszka-előnézet és mentés: `edit_controller_effects_finetune_mixin.py:74-98`; a mód belépése és a korábbi paraméter visszatöltése: `PhotoViewerEditorPanel.qml:95-107`. | `NINCS MEG`: az eredeti csúszka alapértéke és megjegyzett állapota, a Cancel és Apply fájlhatása, billentyűs megszakítás, hálózati/írásvédett hiba, illetve a mentés utáni index/rács/állapotsor. A `job-70` nem teljes folyamatmérés. |
| **Vörösszem.** A panel elemei és eredeti szövegei már dokumentáltak: Auto, Preview, Reset, Apply, Cancel, találati/üres/Reset utáni szövegek (`ui-audit-editor.md:1186-1263`). A koordináták a szerkesztés idején élnek; az eredeti vörösszem-javítás a mentett képpontokba kerül és nem nyerhető vissza a réteg ismételt alkalmazásával (`ui-audit-editor.md:1230-1257`; `IDS_CONFIRM_UNDO_REDEYE`, bináris `0x00752ae0`). | Csempe: `EditorTabCommonFixes.qml:114-125`; panel: `EditorRedeyePanel.qml`; Apply/Cancel kötése: `PhotoViewerEditorPanel.qml:211-230`; puffer, egyedi keret-Undo, Reset és Apply: `edit_controller_redeye_mixin.py:298-465`. | A meglévő `vorosszem-eszkoz-terve.md` a képpont-algoritmus mérését írja le, a teljes panelfolyamatot nem. A batch belépő belső útjának eltérése fent szerepel, de látható kimeneti eltérés nem bizonyított. `NINCS MEG`: a párban végzett eredeti és mai interakció, a tényleges Apply/Cancel megszakítási hatás, mentett fájl és index/rács/oldalsáv/állapotsor összevetése. |
| **Retusálás.** Eredeti eszközbelépő `0x005f7140`; a felületi erőforrás `retouchapply`, `retouchcancel`, `retouchoverlay` (`ui-audit-editor.md:2467-2469`). A `job-315` összefoglaló retusált kép mentésekor eredeti-biztonsági másolatot és ini-hatást említ; a nyers ini hiányzik, a `filters` helyéről a job-253 és a bináris spec ellentmond a job-315 leírásának (`paritas-ellenorzes-archiv-1.md:851-883`). | Csempe: `EditorTabCommonFixes.qml:171-183`; panel, ecset és foltgombok: `EditorRetouchPanel.qml:80-187`; Apply/Cancel: `PhotoViewerEditorPanel.qml:193-208`; puffer, helyi Undo/Redo és Apply: `edit_controller_retouch_mixin.py:74-223`. | `NINCS MEG`: eredeti pontos mezőértékek, első és második ecsetkattintás képkockái, félbehagyás és panel-Mégse után visszaálló kép, valamint teljes Save utáni állapot. A `job-315` csak részleges, összefoglalt mérés, ezért a bizonytalan ini-különbséget nem tekintem eltérésnek. |
| **Szöveg.** Eredeti eszközbelépő `0x005f5b30`; a szerkesztő mód váltásakor a `edittextapply`/`edittextcancel` gombok zárják az eszközt (`ui-audit-editor.md:2467`). Az eredeti felirat tárolása és fájlba írása a `picasa-ini-format.md` szöveges rétegről szóló szakaszában szerepel. | Csempe: `EditorTabCommonFixes.qml:185-200`; panel mezői és gombjai: `EditorTextPanel.qml:1-430`; Apply/Cancel: `PhotoViewerEditorPanel.qml:233-248`; a controller az `applyText()` során blokkot módosít vagy új blokkot hoz létre: `edit_controller_text_mixin.py:501-545`. A szöveg külön `text=`/`textactive=` kulcspárja: `edit_controller_save_mixin.py:213-253`. | A jelenlegi kódútra közvetlen forrásbizonyíték van, de az eredeti és mai teljes interakció, megjegyzett panelállapot és mentett fájl egyezése `NINCS MEG`. Colab-felvétel szükséges egy meglévő és egy új szövegblokkal, Apply, Cancel, Undo, Save sorrendben. |
| **Jó napom van.** Eredeti `editpanel/enhance` vezérlő; könyvtári batch parancs `0x9d5e`, kezelője `0x005cc97b`; a bináris batch minta szerkesztőnyitáskor a megfelelő csempére navigál, könyvtárban a kijelölt képekre alkalmaz (`picasa-menu-parancsok-viselkedes.md:1535-1625`). A `Ctrl+Shift+E` eredeti editor-hatását a bináris `0x005e638b` és a `job-810` méri; egyképes paneles hatásról a `job-812` ad képet. | A csempe: `EditorTabCommonFixes.qml:127-141`. A batch menü: `PicasaPictureMenu.qml:56-59`. Az effektmentés: `edit_controller_effects_mixin.py:72-88`; batch írás és háttérszál: `batch_effect_controller.py:130-156,340-378`. | A szerkesztői gyorsbillentyű hiánya igazolt, lásd a fejlesztői javaslatot lent. `NINCS MEG`: PicasaPy futásképe az eredetihez párosítva, a könyvtári shortcut adat-/fájlhatása, Save utáni index/rács/állapotsor és a teljes kijelölési feltétel. |
| **Automatikus kontraszt és automatikus szín.** Eredeti menüparancsok: Auto Contrast `0x9d49` / kezelő `0x005cc917`; Auto Color `0x9d48` / kezelő `0x005cc949`; a panelvezérlők `editpanel/autolighting` és `editpanel/autocolor` (`picasa-menu-parancsok-viselkedes.md:1535-1590,1610-1632`). A menü a szerkesztőben a csempére visz, könyvtárban a kijelölt képeken batch műveletet indít (`0x00579330`, `0x005fe370`); a batch utáni rácsot a `job-809`, az egyképes Undo/Redo feliratot a `job-812` mutatja. | Csempék: `EditorTabCommonFixes.qml:143-169`; batch parancsok: `PicasaPictureMenu.qml:44-53`; lánc-hozzáfűzés: `edit_controller_effects_mixin.py:72-88`; háttérmunka: `batch_effect_controller.py:340-378`. | A mérések az eredeti látható műveleti állapotot és a kijelölést igazolják. `NINCS MEG`: PicasaPy futásképe, fájl/ini/DB kimenet, Cancel/Save, index/rács/oldalsáv/állapotsor páros összevetése. |
| **Derítőfény.** A szerkesztő bal paneljének csúszkája a mért Picasa UI auditban a Gyakori javítások fül alatt szerepel (`ui-audit-editor.md:294-310`). A `job-812` képe a csúszka mozgatása utáni képernyőt és Undo feliratot rögzíti. Külön eredeti belépési billentyűt vagy batch menüparancsot itt nem azonosítottunk. | Ikon, cím és csúszka: `EditorTabCommonFixes.qml:273-326`; a panel-érték változása a finomhangoló controllerhez fut (`edit_controller_effects_finetune_mixin.py`). | A `job-812` nem adja meg a csúszka pontos koordinátáit, induló értékét vagy mentési következményét. `NINCS MEG`: az eredeti tárolt érték, PicasaPy-val párosított fájlhatás, valamint a teljes UI-utóhatás. |

## Közös Alkalmazás, kilépés, visszavonás és mentés

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Az eredeti szerkesztő módváltáskor a `0x005f8d80` lezáró kapun átmegy. Módosított eszköznél az „Apply changes to the current image?” kérdést adja; az Apply, Discard és Cancel ág különbözik. Cancelnél a fókuszváltás nem történik meg. A `DoNotAskOnEndEditModality` beállítás kérdés nélkül alkalmazást választ (`ui-audit-editor.md:2421-2464`). Ez külön módváltási kérdés, nem az egyes eszközök saját panel-gombja. | PicasaPy eszközmód-váltása: `PhotoViewerEditorPanel.qml:95-109`; eszközönkénti panel Cancel az egyes sorokban; közös Undo/Redo: `edit_controller_history_mixin.py:60-84`. | Az eredeti oldali kapu binárisból ismert, de a teljes kérdés és válaszút PicasaPy-hoz viszonyított minden eszközre kiterjedő futó összevetése `NINCS MEG`. A meglévő UI audit a fókuszváltási esetre ad eredeti bizonyítékot; az Enter/Escape és egyes eszközönkénti kilépés további mérést igényel. |
| Red Eye Undo saját megerősítő szövege jelzi, hogy a kijavított szemek nem állíthatók vissza a javítás ismételt alkalmazásával (`IDS_CONFIRM_UNDO_REDEYE`, `0x00752ae0`). Retouch mentésről részleges mérés a `job-315`. Egyéb eszközök teljes undo/redo és mentési mellékhatásai itt nincsenek végigmérve. | A globális Undo/Redo a korábbi szerkesztési láncot visszaállítja és a `_save()` útján kiírja (`edit_controller_history_mixin.py:60-84`). A lánc, `crop`, `backuphash` ini-frissítése, írási hibák és háttérben futó újrarajzolás: `edit_controller_save_mixin.py:145-210`. A szöveg külön ini-kulcsokon mentődik: `:213-253`. | `NINCS MEG`: az eredeti és mai műveleti lépések pontos megfelelése, az Undo egyes eszközöknél réteg- vagy fájlszintű hatása, mentés utáni eredeti fájl és biztonsági másolat, DB/index, bal panel, rács, kijelölés, háttérmunka és állapotsor közvetlen összevetése. A `job-315` nyers ini- és profilmelléklete nélkül a retus-ini eltérés nem eldönthető. |
| A `0x005f30e0` kód a `filters` lánc beolvasása után a `tilt` tokent összeveti; találatkor az `IDS_WARN_REDEYE_ACCURACY` feliratot jelenítő hívást végzi (`0x005f3370-0x005f3438`). Ugyanitt `redeye.tmp` néven fájlt nyit `CreateFile`-lel `GENERIC_READ|GENERIC_WRITE` és `OPEN_ALWAYS` paraméterrel. Sikertelen nyitáskor a hiba szövege: “Unable to write redeye due to a disk error. The disk may be full or read-only.” (bináris `0x005f30e0`, string xrefek `0x00c984e0-0x00c98550`). A `mérés (job-811)` tilt nélküli és tervezetten `tilt=1,0.18` bemenetű Redeye panelt mutat; egyik képen sincs látható figyelmeztetés. | A mai vörösszem figyelmeztetés feltétele `panel.straightenActive`: `EditorRedeyePanel.qml:81-96`. A mentés előtti írásvédettség-ellenőrzés `edit_controller_save_mixin.py:256-270`; az ini-írás hibája `:186-198`. | A `job-811` nem mutat figyelmeztető ablakot, de az engedélyezett `allapot.json` nem adja vissza a betöltött ini-t, ezért a `tilt` feltétel tényleges kipróbálása még nem igazolt. Az eredeti teljes hibaablak, fájlrendszer-állapot, megszakítás és hálózati hely összevetése `NINCS MEG`. Fejlesztési eltérést ebből ne állítsunk. |

## A `0x005f30e0` figyelmeztetés cáfoló vizsgálata

**Feltételes állítás:** a vörösszem figyelmeztetés nem feltétlenül minden eszköznyitáskor jelenik meg. A helyi függvény-diszasszemblálás szerint a `filters` tagokat végigjáró ciklus csak a `tilt` token találatakor jut a figyelmeztetés-híváshoz. A folytató ág találat nélkül a következő láncelemre, illetve a figyelmeztetést elkerülő folytatásra ugrik.

**Cáfoló kísérlet:** megpróbáltam cáfolni azt a lehetséges következtetést, hogy a figyelmeztetés feltétel nélküli, vagyis minden Red Eye nyitásnál megjelenik. A disassembly ellenpélda-ágat mutat a `tilt` nélküli láncra. Az eredeti spec `forras-audit-5186-2.md:28,413-430` korábban a megjelenési feltételt nyitottnak hagyta, ezért ez a viselkedés valódi pontosítás, nem korábbi mérésből másolt állítás.

**A cáfoló ellenőrzése:** a függvény címe, a figyelmeztetés string-xrefje és a lépésenkénti disassembly összeköti a sztringet és az ágat. A keresett címet a meglévő Ghidra-fájlokban is ellenőriztem; ott erre a kérdésre használható teljes, független dekompilált törzset nem találtam. Nincs második, futásidejű eredeti felvétel, ezért a feltételt **nem** emelem megerősítettre. A Colab-próba két azonos képen, egyiken tilt nélkül, másikon kiegyenesítés alkalmazása után rögzítse a vörösszem eszköz megnyitását.

**Colab-kiegészítés:** a `job-811` `kepernyo__11.png` és `kepernyo__19.png` képein nem látszik figyelmeztető ablak. A feladatleírás szerint a második képhez ini-előkészítés adta a `tilt=1,0.18` elemet, de a `allapot.json` nem tartalmaz ini-visszaolvasást. Ez a kép cáfolja azt, hogy a figyelmeztetés minden panelnyitáskor látható, de önmagában nem cáfolja a `tilt` feltételre vonatkozó bináris állítást, mert a betöltött lánc nincs függetlenül igazolva.

## Független utak és bizonyítottsági fok

**A út:** a Picasa3.exe indexe és célzott függvény-diszasszemblálása, valamint attól független eredeti képernyőmérés. A `Ctrl+Shift+E` esetében a bináris `0x005e638b` útja és a `job-810` szerkesztői képe egyezik. A `0x005f30e0` red-eye `tilt` feltételhez a `job-811` képe nem mutat figyelmeztetést, de a betöltött ini hiányában nem ad cáfoló bizonyítékot.

**B út:** a jelenlegi PicasaPy forrásának teljes `src/picasapy` keresése és a kötés feltételének követése. A `Ctrl+Shift+E`-hez egy bindinget találtam (`MainKeyboardShortcuts.qml:166-174`), a kapu `!hostWindow.viewerOpen` (`MainWindowCommands.qml:171-172`), ezért a mérésen látható eredeti szerkesztői működés nincs bekötve. Ez az út az eredeti bináris útjától függetlenül ugyanarra az eltérésre jut.

**Egyezés:** a `Ctrl+Shift+E` szerkesztői eltérésnél A és B egymástól függetlenül ugyanarra jut; ez a részállítás **megerősített**. A teljes jegyre a bizonyítottsági fok **feltételes**, mert a többi eszköz panel-, fájl-, ini-, index-, hiba- és mentési folyamata nincs végigmérve.

## A jegy „Kész, ha” pontjai

- ⛔ A belépési pontok részben összevetve: `job-807` menüállapotokat rögzít nulla, egy és két kijelölt képnél; `job-808` helyi menüket a könyvtárban és szerkesztőben; `job-810` a szerkesztői `Ctrl+Shift+E`-t. A teljes toolbar-súgó és minden eszköz összes belépője `NINCS MEG`.
- ⛔ Ablakok és mezők részben felmérve: `job-798` alapján csak a Crop panel és Escape utáni szerkesztőnézet látszik; a Straighten, Redeye, Retouch és Text képek nem váltottak panelt. `job-812` a gyors javító csempék, Undo/Redo és Derítőfény egyképes állapotát mutatja. A többi panel alapértékei, megjegyzett állapota és kérdése `NINCS MEG`.
- ⛔ A műveleti képek megvannak (`job-809`, `job-812`), de a fájl, `.picasa.ini`, index/DB, bal hasáb, háttérmunka és állapotsor teljes összevetése nincs igazolva a megtekintett képekből és `allapot.json`-okból. A `job-315` továbbra is részleges.
- ⛔ A `job-812` Undo/Redo feliratot mutat; a Redeye Undo-kérdés, írási hiba, megszakítás, hálózati és írásvédett hely összevetése `NINCS MEG`.
- ✅ Az Eredeti/Nálunk/Teendő táblázat, a mért eredmények és a nyitott kérdések dokumentáltak; a `Ctrl+Shift+E` editor-paritáshiányhoz kész fejlesztői javaslat szerepel.

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

## Javasolt jegytörzs-bővítés

„A #7327 futtatott köre részben lezárta a belépési pontokat, a panelállapotokat és az egyképes automatikus javításokat (`docs/specs/paritas-folyamat-7327.md`, `Mérési eredmény (Colab)`). A bináris `0x005e638b` útja és a `job-810` szerkesztői felvétele igazolja, hogy az eredeti `Ctrl+Shift+E` a Jó napom van csempét aktiválja. A PicasaPy egyetlen kötése a `MainKeyboardShortcuts.qml:166-174` fájlban a `!viewerOpen` kapu miatt nem érhető el a szerkesztőben; a pontos forrásidézet és a fejlesztői teendő alább szerepel. A fájl/ini/index-utóhatás, a többi panel Apply/Cancel, a red-eye figyelmeztetés tilt-bemenettel, valamint a hiba- és hálózati/írásvédett ágak nyitottak.”

## Új kutatási jegyjavaslatok

Nincs külön új kérdés: a futtatott hiányok a #7327 céljához tartoznak, és a Colab-felvételi tervben szerepelnek.

## Nyitott

- A teljes eszközfolyamatok és minden belépési pont élő összevetése: `NINCS MEG`, megszerzés a fenti Colab-felvételi tervvel.
- Az eredeti Auto Red Eye módosított fájltípusokra vonatkozó élő kezelése, a fájlírási hiba ablakának pontos alakja, a `redeye.tmp` életciklusa és az állapotsor/időzítés: `NINCS MEG`, a 2., 3. és 8. Colab-lépéssel.
- Az eredeti hálózati és írásvédett mentési ágak minden eszköz esetén: `NINCS MEG`, a 8. Colab-lépéssel.
- `Ghidra-kör kell` pont nincs: a jelenlegi nyitott kérdések látható viselkedésre és futásidejű fájl-/UI-hatásra vonatkoznak; a feltárt diszasszemblálás elegendő volt az ismert statikus ágak megnevezéséhez.

## Módosított fájlok

- `docs/specs/paritas-folyamat-7327.md`: a #798 és #807-812 futtatott eredményei, a koordinátakimenet, a megerősített editor-gyorsbillentyű eltérés és a fennmaradó mérési kérdések.

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

### Mért koordináták a további Colab-feladatokhoz

A #798 `kepernyo__23.png` képe 1280 × 1024 felbontású. A gombképek középpontját képpontban mértem; a Crop panelben nincs csúszka.

| Crop vezérlő | Koordináta | Forrás |
|---|---:|---|
| Apply | `(84,403)` | mérés (job-798, `kepernyo__23.png`) |
| Cancel | `(188,403)` | mérés (job-798, `kepernyo__23.png`) |
| Reset | `(136,368)` | mérés (job-798, `kepernyo__23.png`) |
| Crop slider | NINCS MEG: a felvételen csúszka nincs | mérés (job-798, `kepernyo__23.png`) |
| Straighten Apply/Cancel/slider | NINCS MEG: helyes Straighten panelkép nincs | mérés (job-798 képei) |
| Redeye Auto/Apply | NINCS MEG: helyes Redeye panelkép nincs | mérés (job-798 képei) |
| Retouch Apply/Cancel | NINCS MEG: helyes Retouch panelkép nincs | mérés (job-798 képei) |
| Text Apply/Cancel | NINCS MEG: helyes Text panelkép nincs | mérés (job-798 képei) |

A mért koordináták bekerültek a munkafa `.tmp/colab-kitoltott/7327-8a-vagas-alkalmaz-visszavon.json` és `.tmp/colab-kitoltott/7327-8b-vagas-megse-alaphelyzet.json` kimenetébe. A 9, 10, 11 és 12 feladat koordinátáit nem töltöttem ki, mert a képek nem adnak hozzájuk megfelelő panelt.

### Igazolt fejlesztői eltérés és javasolt jegytörzs

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A `Ctrl+Shift+E` az eredeti szerkesztőben a Jó napom van műveletet aktiválja: bináris `0x005e638b` → `0x005fe370(panel, "enhance")`; mérés (job-810, `kepernyo__13` és `__15`). | `MainKeyboardShortcuts.qml:166-174`: `sequence: "Ctrl+Shift+E"`; `enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve`; `onActivated: hostWindow.kotegEffekt("enhance")`. A `MainWindowCommands.qml:171-172` kapuja `!hostWindow.viewerOpen`. | A szerkesztőben a Ctrl+Shift+E legyen elérhető az aktuális képen, és aktiválja a Jó napom van csempét. A könyvtári út adat-/fájleffektjét külön kell mérni, mielőtt annak viselkedését módosítjuk. |

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

### Nyitott pontok és következő bizonyító lépés

- `job-798` újrafelvétele helyes Straighten, Redeye, Retouch és Text panelnyitással; minden panelről Apply, Cancel, Reset és csúszka koordináta, alapérték és megjegyzett állapot.
- `job-809` batch útjának ini/DB/export/állapotsor mérése; a képernyőkép kijelölést mutat, de az írásokat nem.
- `job-811` megismétlése a betöltött ini visszaolvasásával, hogy a `tilt=1,0.18` előkészítés ténylegesen jelen legyen a Redeye megnyitásakor.
- A Crop, Straighten, Redeye Apply/Cancel/Undo/Save, Retouch ecset-Undo/Reset/Apply/Save és Text módosítás/új blokk/cancel/apply teljes ini- és fájlkimenete a koordinátákkal kitöltött 8a/8b és a hiányos 9-12 feladatok folytatásával.
- Írásvédett és hálózati mentés, teljes hibaszöveg, megszakítás, index, bal hasáb, rács, kijelölés, háttérmunka és állapotsor: `NINCS MEG`.
