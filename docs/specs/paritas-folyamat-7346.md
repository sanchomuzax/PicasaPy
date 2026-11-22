# #7346: A három Effektek lap folyamata

Vizsgálati tárgy: Picasa 3.9.141.259 és a munkafa jelenlegi PicasaPy-forrása. Ez a lap az effektválasztás, paraméterezés, alkalmazás, elvetés, ismétlés és lánc folyamatait kapcsolja össze. A csempegrafikák és az effektalgoritmusok képpont-paritása külön kutatás.

## Következtetés

Az eredeti három Effektek lapjának 36 csempéje és mind a kilenc Shift-változata megvan a PicasaPyban; az eredeti futtatott felvételek a paraméterpanel alapfolyamatát is részben rögzítik. Két jelenlegi forráseltérés igazolható: a Kép ▸ Csoportos szerkesztés parancsai a PicasaPyban csak a fület választják ki, az eredeti pedig a célvezérlőt is; továbbá a csempék kék jelvényének feltétele a két programban mást jelent. A teljes futásidejű paritás nyitott, mert nem áll rendelkezésre friss, párhuzamos Picasa 3.9/PicasaPy mérés az ismétlésről, megjegyzett paraméterállapotról, mentett képfájlról és visszavonás/újra állapotról.

**Helyesbítés (2026-11-22, Zárókör):** a D1 állítása megdőlt. A Kép ▸ Csoportos szerkesztés parancsai szerkesztőben nyitott képnél az eredetiben a csempekattintás végpontját is futtatják (az egykattintásos hatás a képre kerül, a Sharpen a paneljét nyitja), nem csak fület váltanak. A kérdések mérlege a Zárókör végén: 12 lezárva, 4 blokkolt, 2 hatókörön kívül, 0 csak nyitva.

## Bizonyítottsági fok

**Nyitott az egész folyamatra nézve.** A csempetábla, a Shift-út, a menükód és a PicasaPy paraméteres alkalmazási útja forrásból azonosított. A már futtatott eredeti képernyőképek a csempéket és hat paraméterpanelt igazolnak, de nem fedik le a kért teljes folyamatot. A két eltérés a bináris/korábbi eredeti mérés és a mai PicasaPy-forrás összevetéséből áll; a teljes interakciós végállapotokat Colab-mérésnek kell ellenőriznie.

## A megadott cím helyesbítése

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A briefben megadott 0x00559150 a főmenü-rekordokat regisztráló függvény; a string-xrefek között Copy All Effects, Paste All Effects, Edit View és Show Edit Controls szerepel. | Ez nem fülekhez tartozó mai PicasaPy-fájl. A csempéket az EditorTabHost.qml:102-129 tölti be. | A továbbiakban a 0x00559150-et csak menübelépőként használom. A csempetábla címe 0x00c7e5a0; olvasója 0x005d7c20. |

**Független ellenőrzés:** a helyi SQLite-függvényrekord és a célzott disassembly a 0x00559150-et menürekordokat regisztráló rutinba teszi; az effekttáblát külön, a 0x005d7c20 adatindexelése és a 0x00c7e5a0 tartalma azonosítja. A menüben szereplő sztringek a két út közötti kontrollt adják.

## 1. Belépési pontok, feltételek és a 36 csempe

Az eredeti táblát a 0x005d7c20 olvassa a 0x00c7e5a0 címtől: 36 darab, 12 bájtos rekord, három szerkesztőfülön 12-12 csempe. A három tab tartalmát és a sorrendet már függetlenül ellenőrizték az editpanel.tre erőforrással és a 2026-07-17-i képernyőképekkel; ezt a kört nem ismételtem meg. Az eredeti fülek a szerkesztő 3-5. fülei. A PicasaPyban ugyanez az activeTab 2-4: a csempék a következő fájlokban állnak.

| Eredeti tab és rekordok (0x00c7e5a0) | Eredeti csempék sorrendben | Nálunk (fájl:sor) | Teendő |
|---|---|---|---|
| 3. tab, rekord 1-12 | Élesítés / Szépia / Fekete-fehér / Melegítés / Filmszemcse / Árnyalás / Telítettség / Lágy fókusz / Ragyogás / Szűrt FF / Fókuszos FF / Színátmenet. Kulcsok: unsharp2, sepia, bw, warm, PicnikGrain, PicnikTint, sat, radblur, glow2, ansel, radsat, dir_tint. | EditorEffectsTab1.qml:54-199; a láthatóság EditorEffectsTab1.qml:20 és EditorTabHost.qml:102-109. | A 12 eredeti kulcs és sorrend szerepel. |
| 4. tab, rekord 13-24 | Infravörös film / Lomo-szerű / Holga-szerű / HDR-szerű / Cinemascope / Orton-szerű / 1960-as évek / Színek megfordítása / Hőtérkép / Keresztelőhívás / Poszterizálás / Kéttónusú. Kulcsok: IR, Lomo, Holga, HDR, Cinemascope, Orton, Sixties, Invert, HeatMap, CrossProcess, QuantizePalette, TwoTone. | EditorEffectsTab2.qml:53-156; a láthatóság EditorEffectsTab2.qml:19-20 és EditorTabHost.qml:111-119. | A 12 eredeti kulcs és sorrend szerepel. |
| 5. tab, rekord 25-36 | Felpörgetés / Lágyítás / Vignetta / Képpontnagyítás / Fókusznagyítás / Ceruzarajz / Neon / Képregény / Szegély / Árnyékvetés / Múzeumi paszpartu / Polaroid. Kulcsok: Boost, Soften, Vignette, Pixelate, FocalZoom, PencilSketch, Neon, Comicize, Border, DropShadow, MuseumMatte, Polaroid. | EditorEffectsTab3.qml:53-187; a láthatóság EditorEffectsTab3.qml:19-20 és EditorTabHost.qml:121-129. | A 12 eredeti kulcs és sorrend szerepel. |

Az eredeti csempe harmadik és negyedik táblamezője (rekordonként +0 és +4) az elsődleges, illetve alternatív szűrőkulcs. A Shiftet a 0x005d6e8f út olvassa; a kiválasztott kulcs a 0x006021d0 → 0x005f8520 effektágra kerül.

| Eredeti Shift-pár | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| unsharp2 → unsharp; PicnikGrain → grain; PicnikTint → tint; glow2 → glow; dir_tint → radtint | EditorEffectsTab1.qml:57-73, 99-116, 118-136, 153-166, 184-199 | Egyezik. |
| HeatMap → NightVision | EditorEffectsTab2.qml:117-132 | Egyezik. |
| Vignette → Matte; Pixelate → PicnikFocalPixelate; Border → RoundedEdges | EditorEffectsTab3.qml:78-114, 148-163 | Egyezik. |

A PicasaPy hatodik, „Legacy Effects” füle saját kiegészítésként van dokumentálva az EditorTabBar.qml:136-152 és EditorPanel.qml:54-59 soroknál; nem számít hiányzó eredeti fülnek.

### Menü, helyi menü és gyorsbillentyű

| Eredeti (bináris cím / mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A 0x00d6e4ac menürekord Kép ▸ Csoportos szerkesztés almenüje nyolc effekt/javítás tételt tartalmaz: Auto Contrast 0x9d49, Auto Color 0x9d48, I'm Feeling Lucky 0x9d5e, Sepia 0x9d4a, Sharpen 0x9d4b, Warmify 0x9d4d, Film Grain 0x9d4e, Black and White 0x9d4c. A 0x00579330 állapotvizsgálat a szerkesztőben vezérlőhöz navigál, a könyvtárnézetben a kijelölésen batch ágat indít. | PicasaPictureMenu.qml:43-90; MainMenuBar.qml:492-507; PhotoViewerGeometryActions.qml:367-379. | **Eltérés:** a viewer ág kezeli a fenti nyolc nevet, de csak editorPanel.selectTab(0) vagy editorPanel.selectTab(2) hívást végez. A cél-effekt vezérlőjét/csempéjét nem választja ki. Lásd D1. |
| A 0x00559150 menüépítő Edit menüjében Copy All Effects (rekord 0x00d6dbd0, parancs 0x9d6f) és Paste All Effects (rekord 0x00d6dbe4, parancs 0x9d70) áll; a menüpontoknak nincs gyorsbillentyűjük. Több kijelölt kép esetén a Copy All Effects eredeti Info-üzenetét a korábbi #6860 futás rögzíti. | PicasaEditMenu.qml:80-90; MainMenuBar.qml:466-475; photo_ops_effect_clipboard_mixin.py:52-70 és :72-110. | A mai forrás egy képet követel másolási forrásnak és több célra engedi a beillesztést. A korábbi PicasaPy-mérési sor (archív #6860) régi kódállapotra vonatkozik; a mai dialógus-út forrásból megvan, friss képkocka még kell. |
| A Csoportos szerkesztés nyolc parancsához a billentyűleltár Ctrl+Shift+B-t (Black and White) és Ctrl+Shift+E-t (I'm Feeling Lucky) dokumentál; egyik sem a 36 csempe önálló shortcutja. A csempén tartott Shift a kilenc alternatív kulcsot választja. | MainKeyboardShortcuts.qml:155-175; EditorPanel.qml:172-180; a fül/rács bekötése EditorTabBar.qml:88-135. | A közvetlen csempe-választás Shift-párja megvan. A két Ctrl+Shift parancsot külön, batch/menüútként kell kezelni, nem a csempe aktiválásaként. |
| A meglévő főmenü- és helyi menüleltár a csempéket nem helyezi kép-/néző-helyi menübe; a közvetlen csempebelépő a három szerkesztőfül. | PhotoContextMenu.qml és ViewerContextMenu.qml; a főmenü hatása a fenti sorokban. | A jelenlegi helyi menükben sincs 36 effektet kiválasztó parancs. A jegyhez nem javaslok új helyi menüt. |

#### D1: Menüparancs csak fület választ, vezérlőt nem

**HELYESBÍTVE (2026-11-22, Zárókör):** a "navigál, nem alkalmaz" olvasat téves. A 0x00579330 csak őr; az öt névvel hívó ág (Sepia, Sharpen, Black and White, Warmify, Film Grain) a csempe végpontját (0x005f8520) futtatja, a három javítás a csempét kattintja. A helyes szöveg és a jegytörzs a Zárókör 1. szakaszában és T1-ben van. Az alábbi eredeti szöveg csak a nyomon követhetőség miatt marad.

Az eredeti menüág a 0x00579330 szerkesztőállapot-ellenőrzése után a megfelelő editpanel/tab* és az effekt saját vezérlőneve felé navigál; a függvénycsoportban például az editpanel/autolighting, editpanel/autocolor, editpanel/enhance, editpanel/sepia út szerepel. A korábbi paritás-specifikáció ezt a kétágú működést és a képernyőnézetet már dokumentálja.

A jelenlegi PicasaPy-kód szó szerinti releváns része:

```qml
function selectMenuEffect(name) {
    if (name === "autolight" || name === "autocolor"
            || name === "enhance") {
        editorPanel.selectTab(0)
        return true
    }
    if (name === "sepia" || name === "unsharp" || name === "warm"
            || name === "grain2" || name === "bw") {
        editorPanel.selectTab(2)
        return true
    }
    return false
}
```

Forrás: PhotoViewerGeometryActions.qml:367-378. Az első ágnál a menü a Gyakori javítások fület, a másodiknál az Élesítés-Színátmenet csempelapot mutatja, de egyik esetben sem adja át a célvezérlő nevét, és nem teszi aktívvá a célcsempét. A főmenü viewer ága a sikeres selectMenuEffect után visszatér a MainMenuBar.qml:492-500 sorokon.

## 2. Paraméterpanel, alkalmazás, elvetés és ismétlés

| Eredeti (bináris cím / mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A #81-#86 korábbi Colab-felvételek hat paraméterpanelt rögzítettek: Soft Focus, Focal B&W, Graduated Tint, Glow, Vignette és Focal Zoom. A nyitott panel Apply/Cancel vezérlőt mutat; a fülkattintás az első fül letiltott/elmosott tartalmára vált, a csempékre kattintás nem zárja be, az Escape Cancel. A források összefoglalója: ui-audit-editor.md:638-670. | tryOpenParamPanel csak katalógusos effektet nyit: editorpanel_logika.js:109-115. A paramétercsoportot az EditorParamPanel.qml:242-428 rajzolja; a két gomb :492-525. | A panel ismert alapfolyamata egyezik a dokumentált méréssel. A hat képkocka nem igazolja az összes effekt alapértékét vagy a későbbi újranyitás állapotát. |
| Az eredeti vezérlőfeliratok és effektfüggő felülírások a 0x008fcfa0, 0x008fe9b0 és 0x008fee80 függvényekből, valamint a független filterdesc.xml listából vannak dokumentálva; lásd picasa-effekt-feliratok.md § „A feloldás az EXE-ben van” és filterdesc-registry.md §4.2. | effect_params.py:180-508 adja a PicasaPy-katalógust; editorpanel_logika.js:120-149 induló értékeket állít; EditorParamPanel.qml:242-428 jeleníti meg őket. | A specifikációkban szereplő címkék és regiszterértékek nem ismételt futásmérések. Az effekt-panelenkénti, újranyitás utáni értékek egyezése nyitott. |
| Az eredeti erőforrásban közös paramétervezérlő-készlet szerepel; a #81-#86 screenshotok hat panelen mutatják a konkrét felületet. Egy külön „Alaphelyzet” művelet hatását ezek nem mérik. | A jelenlegi panel gombsora Apply és Cancel; EditorParamPanel.qml:486-525. Külön reset gomb nincs ebben a gombsorban. | Alaphelyzet utáni eredeti viselkedés: NINCS MEG. A reset gomb hiánya a jelenlegi panel forrásában nem bizonyítja az eredeti reset-szemantikát. |
| A 0x006021d0 → 0x005f8520 út a kiválasztott effektet a szerkesztési állapotba adja; az eredeti Undo/Redo sor a csempék alatt van (ui-audit-editor.md §3.2). A 3229 mérés azt igazolja, hogy a filters= sorrend a műveleti sorrendet követi; 5658 helyi láncon nincs kikényszerített globális sorrend. | Paraméter nélküli effekt: edit_controller_effects_mixin.py:73-88. Paraméteres: edit_controller_effects_params_mixin.py:55-96, :99-130. A láncvégi hozzáfűzés _session_with_effect-ben történik; az Apply undo-t tol, ment, revíziót emel. | PicasaPy útja forrásból ismert. A 3229 futás a láncsorrendet, nem az eredeti csempe kétszeri kattintásának eredményét bizonyítja. Az eredeti azonos effekt ismétlése és undo/redo lépései: NINCS MEG. |
| Az eredeti kép lemezre írás utáni képkimenete és a megfelelő filters= lánc egyetlen egybefüggő, előtte/utána felvételben itt nincs meg. A 684-es merőkészlet effektképei render-kimenetek; nem panel-/mentés-folyamat felvételei. | PicasaPy Apply a szerkesztési láncot menti; edit_controller_save_mixin.py:145-183 a filters kulcsot az ini API-n át írja. A fizikai képfájl mentése külön folyamat. | Eredeti vs. mai .picasa.ini, mentett képfájl, Undo és Redo teljes összevetése: NINCS MEG. |

### Colab-lépéssor a nyitott futásidejű kérdésekhez

1. Ugyanazt a kontrollképet nyisd meg mindkét programban, azonos kezdeti filters= lánccal; jegyezd fel a képfájl és .picasa.ini előállapotát. Eredeti Picasában nyisd meg a hat már mért paraméterpanel egyikét, egy másik panelen pedig egy még nem mért effektet; rögzítsd a csúszka/checkbox/szín értékeket, fülkattintás utáni panelt, Escape-et és Alkalmaz/Mégse állapotot.
2. Ugyanazon a képen ugyanazt a paraméteres effektet nyisd meg, állíts el egy paramétert, Mégse, nyisd meg újra, majd Alkalmaz. Ezután ugyanazt a csempét alkalmazd még egyszer; minden lépés után mentsd el a .picasa.ini másolatát, a Visszavonás/Újra feliratot, és készíts képkockát. Végül Save to Disk után hasonlítsd össze a fájlt.
3. A menüpróbát külön végezd el: könyvtárban 0/1/2 kijelöléssel, editorban nyitott képpel is válts a Csoportos szerkesztés Sepia, Sharpen és Auto Contrast pontjaira; jegyezd fel, hogy a konkrét vezérlő/csempe aktívvá válik-e és módosul-e a lánc. Copy All Effects esetén 1, majd 2 forrásképpel; Paste All Effects esetén 2 célképpel mérj. Kontrollként ellenőrizd a helyi menüket, a Ctrl+Shift+B/E és Shift billentyűt.

## 3. Több kijelölt kép, Cancel, Reset és Save

| Kérdés | Eredeti | PicasaPy | Állapot |
|---|---|---|---|
| Effektcsempe egy képnél | A csempe az editor aktív képét célozza; 0x005d6eac-0x005d6eaf → 0x006021d0. | A csempe paraméteres útra vagy effectRequested jelre kerül; a controller az aktív szerkesztési munkamenetet módosítja. | Forrásút ismert; aktuális kép utáni mentési végállapot Colab-mérést igényel. |
| Több kép kijelölése | Könyvtárnézetben a Csoportos szerkesztés almenü egyes effektjei a teljes kijelölésre batch ágon futnak. Copy All Effects egyetlen forrásképet kér; Paste All Effects a kiválasztott célokra vonatkozik. | PicasaPictureMenu.qml:43-90 a batch menü; photo_ops_effect_clipboard_mixin.py:65-67 egyetlen másolási forrást kér, :72-110 több célra illeszt. | A jelenlegi kód mintája egyezik. A PicasaPy régi, többképes Copy mérését nem alkalmazom a mai kódra; friss képkocka szükséges a felületi megerősítéshez. |
| Paraméterpanel Mégse | A #81-#86 felvételek Escape/Cancel után a mentett panelállapotot hozzák vissza. | editorpanel_logika.js:191-198 discardEffectPreview hívást, majd bezárást végez; controller :74-79 visszaállítja a preview-t mentett munkamenetre. | Rész-egyezés bizonyított; egyező képfájl- és ini-pillanatkép még nincs. |
| Paraméterpanel Alaphelyzet | Külön Reset-akció és annak állapotváltozása: NINCS MEG. | A paraméterpanelben Apply/Cancel van; a paraméterértékeket megnyitáskor a katalógus adja, külön reset út nincs a panelben. | Nyitott; nem állítok eltérést. |
| Ugyanazon effekt ismételt alkalmazása | Két azonos csempekattintás utáni filters= lánc, Undo/Redo sor és mentett fájl: NINCS MEG. | A vezérlő minden érvényes apply esetén új láncvégi műveletet, Undo-lépést és mentést készít. | NINCS MEG, hogy az eredeti ismétlés ugyanilyen-e. |
| Mentés lemezre | Csempe Apply, .picasa.ini és a tényleges mentett JPEG együttes előtte/utána mérése: NINCS MEG. | Apply a szerkesztési láncot írja az ini-be; a fizikai képfájl mentését a külön mentési folyamat végzi. | A teljes eredeti/PicasaPy összevetés nyitott. |

## Bizonyíték és független utak

| Állítás | Forrás |
|---|---|
| A megadott 0x00559150 menüépítő, nem a 36 effekt csempetáblája. | bináris (0x00559150); függetlenül a string_xrefs menürekordjai |
| A csempe-adattábla 36 rekordos; 3×12 sorrendje az eredeti UI-képekkel egyezik. | bináris (0x00c7e5a0; 0x005d7c20); mérés (ui-audit-editor.md, 2026-07-17 20:56:45/50/55) |
| A kilenc másodlagos kulcsot Shift választja, és ugyanaz az élő effektág kapja. | bináris (0x005d6e8f; 0x006021d0; 0x005f8520); mérés (korábbi editor-audit) |
| A paraméterpanel, a fülkattintás és Escape hat panelen rögzített. | mérés (picasa-colab-jobs #81-#86; ui-audit-editor.md:638-670) |
| A lánc sorrendje műveleti sorrend; nincs kikényszerített globális filter-sorrend. | mérés (3229-lanc-sorrend; picasa-ini-format.md:2881-2894; 5658 lánc) |
| A paraméteres Apply hozzáfűz, undo-t készít, és ment; Cancel a preview-t dobja el. | NINCS MEG: eredeti és mai, egyező mentett fájlt tartalmazó futásidejű pár. A mai kódút: edit_controller_effects_params_mixin.py:55-130. |
| A Copy All Effects jelenlegi PicasaPy-forrása több képnél dialógust küld. | NINCS MEG: friss, mai UI-felvétel. A korábbi mérés megelőzi a jelenlegi kódút ellenőrzését; forrás: photo_ops_effect_clipboard_mixin.py:65-70, MainWindowDialogStack.qml:113-117. |
| A PicasaPy menüjének nézőbeli ága a lapot választja, nem a konkrét vezérlőt. | bináris (0x00579330 és a 0x9d49/0x9d4a/0x9d4c/0x9d5e parancságak); PicasaPy forrásidézet: PhotoViewerGeometryActions.qml:367-377. |
| HELYESBÍTVE: a jelvény az eredetiben is a one-click típust jelzi (#1869), nincs eltérés. | bináris (0x005d7eca; 0x005d8111/0x005d8116); mérés (#2061 előtte/utána); PicasaPy forrás: editorpanel_logika.js:87-89 és PanelButton.qml:570. |
| Ismételt azonos csempealkalmazás és Alaphelyzet utáni állapot. | NINCS MEG. |

### A két független út

- **A: eredeti:** a 0x00c7e5a0 csempetábla, a 0x005d7c20 csempeépítő, a 0x005d6e8f Shift-választó és a 0x00579330 menüág utasításszintű olvasása. Ez adja a csempesorrendet, alternatív kulcsot, menüágat és eredeti jelvényfeltételt.
- **B: független UI/adatréteg:** az editpanel.tre erőforrás és a korábbi eredeti képernyőképek adják a három 12-es rácsot; a #81-#86 futások a paraméterpanel interakcióját, a #2061 a jelvény állapotváltozását mutatja; a 3229 mérés a filters= sorrendet ellenőrzi.
- **Nálunk:** a mai QML és controller út önálló, forrásból ellenőrizhető. A menülap-eltérés és a jelvényeltérés a két rendszer összevetéséből következik; az ismétlés, reset és lemezmentés dinamikus kérdés marad.

### Cáfoló kísérlet

Megpróbáltam megcáfolni, hogy a többképes Copy All Effects ma is eltér. A korábbi UI-auditban szereplő PicasaPy-mérés nem mutatott üzenetet, de a jelenlegi vezérlő több kijelölt sornál jelzést bocsát ki, és a QML dialógusra köti. A régi felvétel tehát nem cáfolja a jelenlegi forrásút állítását; friss UI-kép kell a felhasználói láthatóság ellenőrzéséhez.

Második cáfoló ellenőrzésként a #81 Escape utáni állapotát (az első fül) vetettem össze a jelenlegi paraméterpanel-lezárással. Az eredeti mért sorozatban Escape előtt fülkattintás is történt; a mai kód csak felfüggesztett panelnél áll vissza az első fülre. Ez a rögzített interakcióval egyezik, így nem vettem fel eltérésnek.

## A jegy „Kész, ha” pontjai

1. ✅ **Belépési pontok és kijelölési feltételek részben feltérképezve:** három csempefül, a batch menü nyolc effektje, két keyboard shortcut, Copy/Paste All Effects és a többképes Copy mérés megvan. A közvetlen helyi menü/összes kijelölési állapot teljes futásmérése nyitott.
2. ⛔ **Vezérlők, alapértékek, megjegyzett állapot:** az eredeti hat paraméterpanel mért, a címkeregiszter és katalógus már specifikált; az összes effekt újranyitás utáni állapotát nem mértük.
3. ⛔ **Előnézet, filters=, mentett fájl, Undo/Redo:** jelenlegi forrásút és korábbi láncsorrend-mérés megvan; teljes eredeti/PicasaPy mentési pár nincs.
4. ⛔ **Több kijelölés, Mégse/Alaphelyzet, ismétlés, mentés:** Copy/Paste és Cancel forrásút azonosított; mai UI-megerősítés, Reset, ismételt effekt és Save to Disk utáni fájl pármérése hiányzik.
5. ✅ **Eltérés esetén idézett PicasaPy-kódsor:** D1 és D2 alatt szó szerinti forrásrészlet áll.

## Javasolt jegytörzs-bővítés

Két fejlesztői teendő indokolt a kutatás alapján.

### D1: a menüvezérlő kiválasztása

> **HELYESBÍTVE (2026-11-22, Zárókör):** az alábbi "Eredeti" és "Kész, ha" szöveg ("nem alkalmazza automatikusan") téves, ne ez alapján építsen senki. A fejlesztői jegytörzs a Zárókör T1 szakasza.

**Eredeti:** a 0x00579330 menüág editorpanelen belül a megfelelő lapot és konkrét vezérlőt nyitja meg; például Auto Contrast → editpanel/autolighting, Auto Color → editpanel/autocolor, I'm Feeling Lucky → editpanel/enhance, Sepia → editpanel/sepia.

**Nálunk:** PhotoViewerGeometryActions.qml:367-377 csak editorPanel.selectTab(0) vagy editorPanel.selectTab(2) hívást végez, majd igaz értékkel visszatér; a vezérlő/csempe azonosítóját nem választja ki.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| 0x00579330: nyitott editor esetén az adott effekt saját vezérlőjére navigál; könyvtárnézetben batch műveletet indít. | PhotoViewerGeometryActions.qml:367-377: a 8 támogatott menüeffektből csak a Common Fixes vagy az Effects lapot választja. | Viewerben a megfelelő konkrét eszközt/csempét aktiválja vagy jelölje ki anélkül, hogy idő előtt láncmódosítást végezne. Könyvtárban a batch út maradjon a kijelölésre. |

**Kész, ha:**

- Nyitott nézőnél Auto Contrast, Auto Color, I'm Feeling Lucky, Sepia, Sharpen, Warmify, Film Grain és Black and White a megfelelő konkrét vezérlőhöz visz; nem alkalmazza automatikusan és nem módosítja a filters= láncot.
- Könyvtárnézetben ugyanezek a menüpontok a kijelölés képeire futnak.
- Egy és több kép kijelölésével, valamint egy nyitott nézővel a megfelelő csempe/vezérlő megjelenik; az aktív kép és a kijelölés megmarad.

### D2: alkalmazott effektjelvény (HELYESBÍTVE: nem eltérés)

**Helyesbítés (2026-11-21):** ez a szakasz téves. Az „állapotkód 1” a szűrő leírásának `+4` mezője, vagyis a `mode` attribútum egész értéke (`oneclick` = 1), ahogy a #1869 megfejtése levezeti (`docs/specs/filterdesc-registry.md`, a `mode` attribútum szakasza: `0x008ff847`, `0x005d7ec2`, `0x005d7eca`). Ez a szűrő fajtájától függő, állandó tulajdonság, nem az alkalmazott állapot. A #2061 a csempe előnézetéről szól, nem a jelvényről. A PicasaPy jelenlegi viselkedése egyezik az eredetivel; a #7354 ezért lezárult. Az alábbi eredeti szöveg csak a nyomon követhetőség miatt marad.


**Eredeti:** a 0x005d7c20 csak akkor mutatja az fx%d_adorn elemet, ha az effekt állapotkódja 1 (0x005d7eca; megmutat/elrejt: 0x005d8111/0x005d8116).

**Nálunk:** a szó szerinti logika (`editorpanel_logika.js:87-89`):

```js
function hasBadge(effectName) {
    return panel.oneClickEffects.indexOf(effectName) >= 0
}
```

A megjelenítés feltétele (`PanelButton.qml:570`):

```qml
visible: pbtn.badge && pbtn.thumbSource !== ""
```

Ez a szűrő kategóriáját ellenőrzi, nem a filters= láncban való jelenlétét.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Kék jelvény = az adott effekt alkalmazva van-e a képen. | Kék jelvény = a szűrő one-click kategóriájú-e. | A jelvény láthatósága a jelenlegi szerkesztési láncban az adott effekt meglétét kövesse, és frissüljön Apply, Undo, Redo és képváltás után. |

**Kész, ha:**

- Olyan képen, amelynek láncában az effekt nincs jelen, a jelvény rejtve van; az effekt hozzáadásakor láthatóvá válik.
- Undo eltünteti, Redo visszahozza; az állapot egy másik képre váltáskor annak láncából frissül.
- A jelvényen nincs előfordulásszám, az eredeti állapotjelző vizuális jelentése marad.

### Colab-méréshez átadható lépések

Az ismételt alkalmazás, reset, újranyitás és lemezre mentés bizonyításához lásd fent a Colab-lépéssor három pontját. Ez kutatási hiány, nem új fejlesztési kérdés.

## Új kutatási jegyjavaslatok

Nincs külön kutatási kérdés: a megmaradt futásmérés a #7346 nyitott pontjait zárja.

## Nyitott

- NINCS MEG: ugyanazon paraméteres effekt módosítás, Mégse, újranyitás és érték-megőrzés az eredeti Picasában.
- NINCS MEG: Alaphelyzet/Reset művelet és utána a paraméterpanel, preview, lánc, undo állapota.
- NINCS MEG: azonos csempe ismételt alkalmazása, filters= eredmény és Undo/Redo lépésszám.
- NINCS MEG: az Apply utáni eredeti .picasa.ini, a Save to Disk fájlkimenete, valamint az Undo/Redo mentés előtti és utáni eredménye.
- NINCS MEG: friss PicasaPy felvétel a jelenlegi Copy All Effects többképes figyelmeztetéséről.
- NINCS MEG: a menüvezérlő kiválasztásának aktuális PicasaPy-képernyőképes megerősítése; a forráskód csak a fülváltást igazolja.
- ~~Ghidra-kör nem szükséges: a nyitott pontok futásidejű mérések, az eredeti csempe- és menüút feloldásához a célzott disassembly és a korábbi mérések elegendők.~~ **HELYESBÍTVE (Zárókör):** a csempe- és menüút a disassemblyből eldőlt, de az írásvédett-kapu feltételéhez (0x00541fc0) és a paraméterpanel kezdőérték-forrásához Ghidra-kör kell; lásd a Zárókör mérlegének 13. és 14. tételét.

## Módosított fájlok

- docs/specs/paritas-folyamat-7346.md: a csempék, menük, paraméterpanel és mentési folyamat összevetése; két forrásból alátámasztott eltérés; nyitott Colab-lépések.

## Zárókör (2026-11-22)

### Következtetés

A három Effektek lap folyamatából a lezárható pontok egyeznek az eredetivel: a 36 csempe és a kilenc Shift-pár, a kék jelvény jelentése, a paraméterpanel Alkalmaz és Mégse gombja (az Escape is), valamint a többképes Copy All Effects figyelmeztetés. Az eredeti effekt-paraméterpanelén nincs Alaphelyzet gomb, ezért a PicasaPy panelének sem kell.

A zárókör egy valódi eltérést talált, és ezzel az első kör D1 szakasza megfordul. A Kép ▸ Csoportos szerkesztés parancsai az eredetiben szerkesztőben nyitott képnél nem csak fület váltanak: a fül kiválasztása után ugyanazt a végpontot futtatják, mint a csempekattintás (az egykattintásos hatás azonnal a képre kerül, a Sharpen a paraméterpaneljét nyitja). A Ctrl+Shift+B kezelője azonos felépítésű a már mért Ctrl+Shift+E kezelőjével, ezért az is a megnyitott képre hat. A PicasaPyban a menüparancs csak fülváltás, a Ctrl+Shift+B szerkesztőben ki van kapcsolva. Erre egy fejlesztői jegytörzs készült (T1).

Új lelet az írásvédett kép effektjének kapuja is: az eredeti a csempekattintás előtt rákérdez a másolásra, nálunk csak mentéskor jön jelzés. A kapu feltétele Ghidra-körre vár (T2, kutatási jegytörzs). Négy tétel futásmérésre vár, ezekhez Colab-lépéssor van (C1-C3), a negyedikhez a végrehajtó hiányzó képessége és a Ghidra-kör kell (C4).

### Helyesbítések az első kör szövegéhez

| Az első kör állítása | Helyesbítés | Bizonyíték |
|---|---|---|
| D1: az eredeti menüág "a vezérlőhöz navigál", a "Kész, ha" szerint "nem alkalmazza automatikusan". | Megdőlt. Szerkesztő-ágban az eredeti a csempekattintással egyenértékű: fül és csempevégpont. | 1. szakasz |
| A 0x00579330 "szerkesztőállapot-ellenőrzése után navigál". | A 0x00579330 egy 37 bájtos őr (0x00579330-0x00579354): igazat ad, ha a [0x00d67914] nem nulla, az `editpanel/preview` (0x00c88a2c) létezik és a +0x20c bájtja 0. Nem navigál, a navigálást a hívó kezelők végzik. | `cmp dword ptr [0xd67914], 0` (0x00579330), `mov edx, 0xc88a2c; call 0x9c2fc0` (0x00579339), `cmp byte ptr [eax + 0x20c], 0; sete al` (0x0057934a) |
| "Ghidra-kör nem szükséges." | Két ponton szükséges: az írásvédett-kapu feltétele (0x00541fc0) és a paraméterpanel kezdőérték-forrása (a panelfelépítő 0x00750ff0 és hívottja, a 0x006ac980). | 3. szakasz, 13. és 14. tétel |
| A #7123 tesztje: "a nézőben a tétel NEM módosítja a `filters=` láncot". | A bináris olvasata szerint a tétel módosítja (egykattintásos effektnél), a teszt "Nem szabad" pontja megfordul (T1). | `tests/app/qml_functional/test_sepia_bw_fulvalasztas_7123.py`, docstring "A „Nem szabad” pontok" |

A #7084 zárókörének örökölt kérdése ("a 0x005f8520 pontos hatása, csak kijelöl vagy alkalmaz is") ezzel **LEZÁRVA**: a 0x005f8520 a csempekattintás végpontja, alkalmaz (egykattintásos szűrőnél) vagy panelt nyit (paraméteres szűrőnél).

### 1. Az eredeti szerkesztő-ága, tételesen

A Kép ▸ Csoportos szerkesztés nyolc effekt-parancsának kezelője (főablak-diszpécser 0x005cb990) mind ugyanazt a kétágú mintát követi: `call 0x00579330; test al, al; je <könyvtár-ág>`. A szerkesztő-ág (az őr igaz) a következő. A címek az EXE-ből közvetlenül kiolvasott utasítások (`pe_dis.py`), a sztringek a megadott címen állnak.

| Parancs | Kezelő | Szerkesztő-ág (őr igaz) | Könyvtár-ág (őr hamis) |
|---|---|---|---|
| Auto Contrast (0x9d49) | 0x005cc917 | `0x009cd8a0("editpanel/tab1")` (0x00c94b8c), majd `0x009cd8a0("editpanel/autolighting")` (0x00c9501c) | `0x005fe370("autolight")` (0x00c95034) a kijelölésre |
| Auto Color (0x9d48) | 0x005cc949 | tab1, majd `"editpanel/autocolor"` (0x00c95040) | `0x005fe370("autocolor")` (0x00c95054) |
| I'm Feeling Lucky (0x9d5e) | 0x005cc97b | tab1, majd `"editpanel/enhance"` (0x00c94b9c) | `0x005fe370("enhance")` (0x00c81580) |
| Sepia (0x9d4a) | 0x005cca47 | `0x009cd8a0("editpanel/tab3")` (0x00c901b8), majd `0x005f8520("sepia")` (0x00c94d70) | `0x005fe370("sepia")` |
| Sharpen (0x9d4b) | 0x005cc9ad | tab3, majd `0x005f8520(név)`: ha a [0x00d67849] nem nulla és a Shift le van nyomva (`GetAsyncKeyState(0x10)`, 0x005cc9c0-0x005cc9d6) `"unsharp"` (0x00c94d78), különben `"unsharp2"` (0x00c94d80) | `0x005fe370(ugyanez a név)` |
| Black and White (0x9d4c) | 0x005cca71 | tab3, majd `0x005f8520("bw")` (0x00c8145c) | `0x005fe370("bw")` |
| Warmify (0x9d4d) | 0x005cca9e | tab3, majd `0x005f8520("warm")` (0x00c94d68) | `0x005fe370("warm")` |
| Film Grain (0x9d4e) | 0x005ccacb | tab3, majd `0x005f8520(név)`: Shifttel (ugyanaz a [0x00d67849] és VK_SHIFT kapu) `"grain"` (0x00c94d54), különben `"grain2"` (0x00c95060) | `0x005fe370(ugyanez a név)` |

Az öt névvel hívó ág közös farka: a 0x005cc9e3-on `mov eax, ebx; call 0x005f8520`, utána `0x00a54b70(ebx, 1, 1, 0.0f, {-1,-1,-1,-1})` (0x005cca10; a hívás hatását nem olvastam ki), majd `jmp 0x005cd9e6` (a diszpécser vége).

**Mit hív az ág:**

- **`0x009cd8a0(név)`** név szerint feloldja a felületi elemet (`0x009c2fc0`), típust ellenőriz (`0x00c07db2`), majd a vtábla +0x78 rekeszét hívja (0, 0) argumentummal: a "kattintás". Ugyanez kattintja a Ctrl+9-nél a fiókkapcsolót (`picasa-gyorsbillentyuk.md` 10.3 és 10.8, megerősített). A fül tehát valódi fülkattintás. Az `editpanel/autolighting`, `editpanel/autocolor` és `editpanel/enhance` elem kattintása erős következtetés szerint a csempekezelőbe (0x005d59f0) fut: a #2148 leltára szerint ennek hét statikus szűrőnevű `0x006021d0` hívása közt az `autolight`, `autocolor` és `enhance` szerepel (`filterdesc-registry.md`, "A 0x6021d0 a felületi szűrőt alkalmaz belépési pont"); az elemek kattintás-kezelőjét nem követtem végig.
- **`0x006021d0(név)`** a csempekattintás burkolója: előbb a `Preferences\AllowReadOnlyEdits` kulcsot olvassa (0x006021d6-0x006021f5), a kapu `0x00541fc0` hívása (0x0060220a) után a név a `0x005f8520`-ra jut (0x0060226d). Két hívója van: 0x005d59f0 (7 hívás) és 0x005d3290 (1 hívás).
- **`0x005f8520(név)`** a név szerinti szűrőalkalmazó. A nevet a `[0x00d67f68]` szolgáltatás vtábla +8 rekesze oldja fel szűrőleíróvá (0x005f855b-0x005f8570), a leíró `+4` mezője a `mode` egész értéke. Ha `mode == 1` (`oneclick`, `filterdesc-registry.md` 1.2): a 0x005f8653-0x005f86eb ág az `0x00750ed0` hívással a szűrőt a kép szerkesztési listájára veszi (a `0x006ac4a0` az új szűrőobjektumot a `[ebx+0x10c]` vektor végére írja, 0x006ac6b2-0x006ac6d0), majd a `0x007533b0` frissíti a Visszavonás/Újra és a Mentés gombot (sztringjei: `editpanel/filter_undo`, `editpanel/filter_redo`, `editpanel/writetodisk`, `CFilterStackUI::undoname`, `Undo `), végül `0x00476a60` frissít. Minden más `mode` a 0x005f86f0 ágra megy: a `0x00750ff0` hivatkozott sztringjei `editpanel/editslider%d_container`, `editpanel/colorwheel%d`, `editpanel/editlabel%d`, `editpanel/ok`, `editpanel/cancel`, `editpanel/filter_name`: ez a paraméterpanel felépítése. A `mode` az effektre (4) a 0x005f85a0-0x005f85b3-ban külön jelzőt állít.

A nyolc parancs szerkesztő-ága tehát megegyezik azzal, amit a megfelelő csempe kattintása tenne: az egykattintásos szűrők (`autolight`, `autocolor`, `enhance`, `sepia`, `bw`, `warm`, `grain2`) azonnal a képre kerülnek, a `unsharp2` (`mode="effect"`, `filterdesc.xml:250`) a Sharpen paneljét nyitja.

**Cáfoló kísérlet.** (1) Kerestem olyan utat az öt névvel hívó ágban, amely megkerüli a `0x005f8520`-at: nincs, mind az 0x005cc9e3-on át megy. (2) Megvizsgáltam, hogy a `0x005f8520` egykattintásos szűrőnél csak "kijelölhet-e": a csempekattintás ugyanide jut (`0x005d59f0` → `0x006021d0` → `0x005f8520`, #2456), és az egykattintásos csempe (Sepia, B&W, Warmify) kattintása az eredetiben a képre alkalmazza az effektet, nem csak kijelöli (ezt a PicasaPy csempéi és a mért render-kimenetek, `ui-audit-editor.md` 100. sor, ennek megfelelően valósítják meg), tehát ez a végpont nem csak kijelöl. (3) A Ctrl+Shift+B és Ctrl+Shift+E kezelője (0x005e6370 és 0x005e638b) azonos felépítésű: a `[esp + 0x11]` jelző vizsgálata (`cmp byte ptr [esp + 0x11], 0`), majd `mov eax, <név>; call 0x005fe370`, a szerkesztő-állapot vizsgálata nélkül. A Ctrl+Shift+E szerkesztőben mért (`job-810`: a csempe elhalványul, az Undo felirat "Undo I'm Feeling Lucky"), tehát a `0x005fe370` a megnyitott képre hat; a Ctrl+Shift+B ugyanezt a függvényt hívja `"bw"` névvel (0x00c8145c).

**Bizalmi fok: erős (statikus, két független hívási út: a kezelők és a csempekezelő ugyanazon a végponton találkoznak).** Futásmérés a menüről magáról: NINCS (C1). Megfejtve, hogy az eredeti a csempe végpontját hívja; hogy a képernyőn pontosan mit lát a felhasználó (Undo felirat, jelvény, panel), azt C1 méri.

### 2. Nálunk (szó szerinti idézetek)

`src/picasapy/app/qml/PicasaPy/PhotoViewerGeometryActions.qml:367-379`:

```qml
function selectMenuEffect(name) {
    if (name === "autolight" || name === "autocolor"
            || name === "enhance") {
        editorPanel.selectTab(0)
        return true
    }
    if (name === "sepia" || name === "unsharp" || name === "warm"
            || name === "grain2" || name === "bw") {
        editorPanel.selectTab(2)
        return true
    }
    return false
}
```

`src/picasapy/app/qml/PicasaPy/MainMenuBar.qml:493-495`: `if (hostWindow.viewerOpen) {` / `var viewer = hostWindow.ensurePhotoViewer()` / `if (viewer && viewer.selectMenuEffect(name)) return`. Nézőben a menü tehát a fülváltásnál megáll: a hatás nem kerül a képre, a Sharpen panelje sem nyílik. A #7123 előtt a `sepia` és a `bw` még az egyképes `applyEffectMany([row], name)` kötegre esett (ez alkalmazott), a #7123 ezt fülváltásra cserélte az akkor még nyitott kérdés mellett (`cc54761fb`).

`src/picasapy/app/qml/PicasaPy/MainKeyboardShortcuts.qml:158-159`: `sequence: "Ctrl+Shift+B"` / `enabled: hostWindow._konyvtariGyorsbillentyuEngedelyezve`, ahol a `MainWindowCommands.qml:171-172` szerint `_konyvtariGyorsbillentyuEngedelyezve: !hostWindow.viewerOpen && !hostWindow._szovegmezoneVanFokusz`. Nézőben a Ctrl+Shift+B tehát nem tesz semmit. A testvére, a Ctrl+Shift+E a #7352-ben nézőben is él (`MainKeyboardShortcuts.qml:166-192`).

A csempekattintás mintája, amelyet a menünek is követnie kell: `EditorTabCommonFixes.qml:98` `onActivated: (tool) => panel.handleToolClick(tool)`; `EditorEffectsTab1.qml:79` `onButtonClicked: if (!panel.tryOpenParamPanel("sepia", label)) panel.effectRequested("sepia")`; a Sharpen csempe `EditorEffectsTab1.qml:69` (`szuro` = `unsharp2`, Shifttel `unsharp`). A már meglévő nézőbeli billentyű-minta `MainKeyboardShortcuts.qml:186-191`:

```qml
        function enhanceInViewer(panel) {
            if (!panel || !panel.enabled || panel.modeToolActive
                    || panel.tiltActive || panel.paramPanelActive)
                return
            panel.handleToolClick("enhance")
        }
```

### T1. Fejlesztői jegytörzs: a Csoportos szerkesztés és a Ctrl+Shift+B a megnyitott képen a csempekattintással egyenértékű

**Cím:** A Kép ▸ Csoportos szerkesztés nyolc effektparancsa és a Ctrl+Shift+B a szerkesztőben megnyitott képre hat, ne csak fület váltson

**MIT AD MA (mérve a mai kódon, 5b417cc62):** nyitott nézőnél a nyolc parancs közül a három javítás a 0. fület, az öt effekt a 2. fület választja, és ennyi (`PhotoViewerGeometryActions.qml:367-379`, `MainMenuBar.qml:493-495`). A Ctrl+Shift+B nézőben nem él (`MainKeyboardShortcuts.qml:158-159`, `MainWindowCommands.qml:171-172`). A könyvtárnézeti ág (kijelölésre köteg) helyes, nem érintendő.

**Eredeti / nálunk / teendő**

| Parancs | Eredeti szerkesztő-ágban (1. szakasz) | Nálunk | Teendő |
|---|---|---|---|
| Auto Contrast | 1. fül (`editpanel/tab1`, nálunk a 0. index), majd az `autolighting` csempe kattintása | `selectTab(0)` | `selectTab(0)`, majd `handleToolClick("autolight")` |
| Auto Color | 1. fül, majd az `autocolor` csempe kattintása | `selectTab(0)` | `selectTab(0)`, `handleToolClick("autocolor")` |
| I'm Feeling Lucky | 1. fül, majd az `enhance` csempe kattintása | `selectTab(0)` | `selectTab(0)`, `handleToolClick("enhance")` |
| Sepia | 3. fül (`editpanel/tab3`, nálunk a 2. index), majd a `sepia` effekt a csempe végpontján | `selectTab(2)` | `selectTab(2)`, majd a csempe útja: `effectRequested("sepia")` |
| Black and White | 3. fül, `bw` | `selectTab(2)` | `selectTab(2)`, `effectRequested("bw")` |
| Warmify | 3. fül, `warm` | `selectTab(2)` | `selectTab(2)`, `effectRequested("warm")` |
| Sharpen | 3. fül, `unsharp2` (Shift nélkül): paraméteres, a panelt nyitja, nem alkalmaz | `selectTab(2)` | `selectTab(2)`, `tryOpenParamPanel("unsharp2", label)`: a panel nyílik Alkalmaz és Mégse gombbal, a lánc nem változik, amíg az Alkalmaz meg nem történik |
| Film Grain | 3. fül, `grain2` (a 0x00c7e5a0 csempetábla szerint az 1. fül 5. csempéje a `PicnikGrain`, a `grain2`-nek nincs csempéje) | `selectTab(2)` | `selectTab(2)`, majd a `grain2` egyképes alkalmazása. Az `applyEffect` `_APPLICABLE_EFFECTS` halmaza (`edit_controller_shared.py:305`) a `grain2`-t nem tartalmazza (a fájlban csak a `_ONE_CLICK_KEYS`-ben áll, 212. sor; az `_EFFECT_NAMES`-ben a `grain` áll, 251. sor), tehát `applyEffect("grain2")` `ValueError`-t adna. Vagy a névkészletet kell bővíteni, vagy a #7123 előtti `applyEffectMany([row], "grain2")` utat kell úgy visszaállítani, hogy a nyitott szerkesztési munkamenet frissüljön |
| Ctrl+Shift+B | `0x005e6370` → `0x005fe370(panel, "bw")`, szerkesztő-állapot vizsgálata nélkül, a megnyitott képre (a Ctrl+Shift+E ikertestvére, `job-810`) | nézőben kikapcsolva | a Ctrl+Shift+E mintájára (`MainKeyboardShortcuts.qml:166-192`) nézőben is él, ugyanazzal a kapuval (`panel.enabled`, nincs móduseszköz, kiegyenesítés vagy paraméterpanel) |

**Nem szabad:** a könyvtárnézeti ág (kijelölt képekre köteg) változatlan; a forgatás és a vörösszem-javítás ága változatlan; a Sharpen menüparancs nem alkalmaz hatást a panel Alkalmazása előtt; a Shift-változatok (`unsharp`, `grain`) a menüben nincsenek (nincs felhasználói eset, `picasa-menu-parancsok-viselkedes.md` 33.3).

**Kész, ha:**

- [ ] Nyitott nézőnél a Sepia, a Black and White, a Warmify és a Film Grain parancs után a kép módosult, a `filters=` lánc végén az effekt áll, a Visszavonás/Újra sor az effektet mutatja, és egy Visszavonás visszaadja az előző állapotot; az eredmény megegyezik a csempekattintáséval (a Film Grainnél az egyképes köteg eredményével).
- [ ] Az Auto Contrast, az Auto Color és az I'm Feeling Lucky nyitott nézőnél az 1. fület választja és a csempe kattintásával egyező hatást ad (a láncvégi no-op szabály, `enhanceInViewer` megjegyzése, megmarad).
- [ ] A Sharpen nyitott nézőnél a 3. fület választja és ugyanúgy nyitja meg a Sharpen paneljét, mint a Sharpen csempe (`effect_params.py:485`: `unsharp2`, Amount csúszka); a lánc nem változik, amíg az Alkalmaz nincs megnyomva; a Mégse visszaadja az állapotot.
- [ ] A Ctrl+Shift+B nyitott nézőnél a megnyitott képre fekete-fehéret ad, a kapuk a `enhanceInViewer` kapuival azonosak; könyvtárnézetben a viselkedése változatlan.
- [ ] A `tests/app/qml_functional/test_sepia_bw_fulvalasztas_7123.py` "Nem szabad" pontja ("a nézőben a tétel NEM módosítja a `filters=` láncot") megfordul: a teszt a hatást is méri, valódi menükattintással és valódi billentyűvel (nem a metódus hívásával).
- [ ] Vizuális ellenőrzés: C1 felvételei (eredeti) és a PicasaPy képe ugyanazon a képen, a három állapot (előtte, utána, Undo után) egymás mellett, mért eltéréssel; ahol a teszt csak számol, a jegy kimondja, hogy a vizuális egyezést nem méri.

**Bizonyítottsági fok:** erős (statikus), futásmérés NINCS (C1). Megfejtve, hogy az eredeti a csempe végpontját hívja; a látható hatás (Undo felirat, jelvény) méréséhez C1 kell.

**Mit NEM tudok, de a szöveg alapján tudni látszik:** (1) hogy a menüparancs hogyan viselkedik nyitott paraméterpanel mellett (C1 7. lépés); (2) hogy a `[0x00d67849]` jelző mit jelent (a Shift-ág él-e egyáltalán); (3) hogy a `0x00a54b70` hívás mit frissít; (4) hogy a menüág a `0x006021d0` burkolót megkerüli (a `0x005f8520` közvetlen hívásai közt nincs `0x00541fc0`), ezért az írásvédett-kapu e menüágban nem látszik (T2).

**Érintett fájlok:** `PhotoViewerGeometryActions.qml`, `MainMenuBar.qml`, `MainKeyboardShortcuts.qml`, `MainWindowCommands.qml` (csak olvasva), `tests/app/qml_functional/test_sepia_bw_fulvalasztas_7123.py`; a Ctrl+Shift+E nézőbeli tesztje (#7352) a billentyűs teszt mintája.

**Független újralevezetés (#140):** nem készült; a T1 foka addig "erős".

### T2. Kutatási jegytörzs: az írásvédett kép effektjének kapuja (0x00541fc0), feltétel és másolási folyamat

**MIT AD MA:** a PicasaPy a mentés előtt ellenőrzi a mappa írhatóságát, és csak jelez (`edit_controller_save_mixin.py:256-270`: `if is_folder_writable(folder): return True` / `self.editSaveReadOnly.emit()` / `return False`), a szerkesztés alkalmazásakor nem kérdez, és a másolást nem végzi el (a `fileops/writable.py` fejléce ezt maga kimondja).

**Eredeti (bináris):** a csempekattintás burkolója (`0x006021d0`) a végpont (`0x005f8520`) előtt a `0x00541fc0`-t hívja (0x0060220a). A `0x00541fc0` sztringjei (`string_xrefs`): "This file is read only. In order to edit this file, Picasa needs to copy the file's folder. Would you like to make a copy now?" (0x00c8ae90, kulcs `CThumbUI::ReadOnlyPrompt`), a gombok "Make a Copy" (0x00c8b0ec) és "Cancel Edit" (0x00c8b0c8), az iPhoto (0x00c8af30) és az Apple Photos (0x00c8aff8) változat, a másolat helye "Imported Files" (0x00c8b110), "Picasa/Imported From iPhoto/" (0x00c8b138), "Picasa/Imported From Apple Photos/" (0x00c8b178). A másolás a `0x005350b0` fájlmásoló rutinra támaszkodik (hívás: 0x00542672; a rutinról `paritas-ellenorzes.md:985`). A `0x00541fc0` kivétele a `Preferences\AllowReadOnlyEdits` (0x00c9a044): a burkoló beolvassa, és értékétől függően közvetlenül a végpontra ugorhat (0x006021fa-0x00602205, 0x00602266). A kapu ugyanígy áll az `0x005fe370` (kötegelt effekt) és a `0x00602100` (Auto RedEye keret) elején.

**NYITOTT (megnevezett következő irány):**

1. A kapu feltétele. A `0x00541fc0` eleje a `0x0047cea0` (279 bájt, útvonal-egyeztetés) és a `0x00987030` (bájt-előtag összehasonlítás) hívásaitól függően kerüli meg a kérdést (0x00542109-0x00542168); hogy ez írásvédett fájlattribútum, nem írható mappa vagy egy ismert könyvtár-előtag, nem olvasható ki ebből a szintből. Következő irány: Ghidra-kör a `0x00541fc0` (1952 bájt) és a `0x0047cea0` dekompilálására (Ghidra-sorba felveendő: `0x00541fc0`, `0x0047cea0`).
2. A "Make a Copy" folyamata: a másolat helye és neve, az eredeti kép sorsa, utána lefut-e az effekt. Következő irány: ugyanez a Ghidra-kör; futásmérés csak akkor, ha a végrehajtó (`picasa-colab-jobs`) megkap egy lépést, amely a mintafájlt csak olvashatóvá teszi (ma nincs ilyen lépés, a `--extra` kulcsai: `mintakeszlet`, `picasa_ini_be`, `minta_kiadasbol`, `wine_desktop`, `wine_kodlap`).
3. A menü szerkesztő-ágában (T1) a kapu megléte: a `0x005f8520` közvetlen hívásai közt nincs `0x00541fc0`, a kapu máshol (a hívóban vagy a `0x00a54b70`-ben) lehet; az 1. pont dekompilációja után a `0x00a54b70` is átnézendő.

**Kész, ha:** a spec-lap tartalmaz egy "Írásvédett kép szerkesztése" szakaszt, amely kimondja a kapu feltételét, a két gomb hatását, a másolat helyét, és hogy a menüág, a csempekattintás és a Ctrl+Shift+B/E mind áthalad-e a kapun; ezután a fejlesztői jegy (a PicasaPy mentéskori jelzése helyett kattintáskori kérdés) önállóan megírható.

### 3. A nyitott kérdések mérlege

| # | Kérdés | Állapot | Indok és bizonyíték |
|---|---|---|---|
| 1 | A 36 csempe táblája, sorrendje, kulcsai | LEZÁRVA | 0x00c7e5a0 / 0x005d7c20, két független út (1. kör); PicasaPy `EditorEffectsTab1-3.qml` |
| 2 | A kilenc Shift-pár | LEZÁRVA | 0x005d6e8f → 0x006021d0 → 0x005f8520 (1. kör, #2456) |
| 3 | A kék jelvény jelentése | LEZÁRVA | `mode="oneclick"` = 1 (0x005d7eca; 1. kör D2 helyesbítve, #1869). A #2061 felvételek négy jelvényt mutatnak (Szépia, Fekete-fehér, Melegítés, Színinvertálás: `filterdesc-registry.md` "A jelvény azonossága"); a PicasaPy `_ONE_CLICK_KEYS` (`edit_controller_shared.py:204-218`) ugyanezt a négy csempekulcsot (`sepia`, `bw`, `warm`, `invert`) jelöli, a többi egykattintásos kulcsnak nincs csempéje. Az `Invert` XML-módja (`effect`) és a felvétel közti #2125 anomália ismert, a PicasaPy a felvételt követi |
| 4 | Helyi menü, eszköztár: van-e effektparancs | LEZÁRVA | a 36 csempének nincs menü- vagy helyi menü belépője (1. kör menüleltára; a `job-808` szerkesztői helyi menüje általános kép- és fájlműveleteket mutat, `paritas-folyamat-7327.md` 114. sor); a nyolc Csoportos szerkesztés tétel a főmenüben van |
| 5 | Csoportos szerkesztés könyvtárnézetben | LEZÁRVA | őr hamis ág: `0x005fe370(név)` a kijelölésre (1. szakasz tábla); PicasaPy `PicasaPictureMenu.qml:43-90`, `batch_effect_controller.py`; `job-807`, `job-809` |
| 6 | Csoportos szerkesztés nyitott szerkesztőben | LEZÁRVA, eltéréssel | 1. szakasz: fül és csempevégpont. T1 |
| 7 | Ctrl+Shift+B nyitott szerkesztőben | LEZÁRVA, eltéréssel | `0x005e6370` → `0x005fe370(panel, "bw")`, a Ctrl+Shift+E ikertestvére (`job-810`); T1 |
| 8 | Paraméterpanel gombjai, feliratai, tippjei, Escape | LEZÁRVA | `editpanel.tre` `editpanel/ok` és `editpanel/cancel`, a Mégse `Property escapekey 1`; `editpaneltext.tre`: "Apply" / "Apply Changes", "Cancel" / "Cancel Changes"; a #81-#86 felvételek (`ui-audit-editor.md` 4.0); PicasaPy `EditorParamPanel.qml:498-515` (feliratok, tippek), `PhotoViewerKeyboard.qml:11-14,25-27` (Escape = Mégse). A két `.tre` forrás reprodukálása: `python3 tools/picasa/respack.py tre <respack.yt> <üres mappa>` |
| 9 | Alaphelyzet gomb a paraméterpanelen | LEZÁRVA: nincs | a közös effektpanel erőforrása (`editpanel.tre`) csak `ok` és `cancel` gombot, `filter_name`, `editslider1-4`, `colorwheel0-1`, `editcircle1`, `droppertoggle` elemet tartalmaz; Reset felirat csak a vágás (`cropdiscard`), a vörösszem (`redeyediscard`) és a retusálás (`retouchreset`) elemhez van (`editpaneltext.tre` 231., 288., 304. sor); hat felvétel (#81-#86) sem mutat ilyet |
| 10 | Copy All Effects több kijelölt képnél | LEZÁRVA | az eredeti Info ablak felvételen (`paritas-ellenorzes-archiv-1.md:1043`, "Please select a single picture to copy the effects from."); nálunk valódi menükattintásos teszt (`tests/app/qml_functional/test_copy_all_effects_6861.py`: menü, kattintás, dialógus címe "Info", szövege, a vágólap változatlan) és `MainWindowDialogStack.qml:113-117` |
| 11 | Azonos egykattintásos csempe ismételt alkalmazása: a lánc | LEZÁRVA (erős, statikus) | a `0x006ac4a0` az új szűrőobjektumot a vektor végére írja (0x006ac6b2-0x006ac6d0), azonos nevű bejegyzés keresése nincs a függvényben (a névvizsgálat csak a `moviestart` és a `movieend` sztringekre ág, 0x006ac6fa, 0x006ac807); nálunk a láncvégi hozzáfűzés (`edit_controller_effects_mixin.py:73-88`). Az Undo felirat és lépésszám a 15. tételben |
| 12 | Írásvédett kép: a kapu megléte és helye | LEZÁRVA | `0x006021d0` → `0x00541fc0` a végpont előtt (T2 bizonyíték). Nálunk csak mentéskor jelez: eltérés, T2 |
| 13 | Írásvédett kapu feltétele és a másolási folyamat | BLOKKOLT | gépi úton nem eldönthető ebből a szintből: a feltétel a `0x0047cea0` és `0x00987030` dekompilációján múlik; a futásmérés a végrehajtó hiányzó képessége miatt nem adható fel. Kell: Ghidra-kör (`0x00541fc0`, `0x0047cea0`), és ha mérés kell, a végrehajtóban egy "csak olvasható" lépés. Kitől: nem a tulajdonostól, hanem a mi gépezetünktől (Ghidra-sor, `picasa-colab-jobs` bővítés) |
| 14 | Paraméteres effekt: Mégse, újranyitás, értékek megőrzése | BLOKKOLT | a sztring-hivatkozásokból és a kezelőkből nem olvasható ki: a panelfelépítő `0x00750ff0` (1702 bájt) és hívottja, a `0x006ac980` (1510 bájt, nincs sztringje) az első jelölt a kezdőértékek forrására; a `0x007518e0` csak elrejti a vezérlőket (hívásai `0x009c2fc0` névkeresések). Kell: C2 Colab-feladat (a mi gépünk, tulajdonosi kérés nincs), vagy Ghidra a két függvényre. Ide tartozik a csúszka dupla kattintásos visszaállítása (C2 7. lépés) |
| 15 | Paraméteres effekt ismétlése, Undo/Redo felirat és lépésszám ismétlés után | BLOKKOLT | a felirat szövege ismert (`CFilterStackUI::undoname` "Undo ", `redoname` "Redo "; hivatkozza a `0x007533b0`), a lépésszám és a paraméteres ismétlés viselkedése nincs kiolvasva (a `0x00750ff0` ága). Kell: C2 Colab-feladat |
| 16 | Alkalmaz utáni `.picasa.ini`, Mentés lemezre, Undo/Redo mentés előtt és után, indexhatás | BLOKKOLT | az ini írásának helye nincs kiolvasva: a `0x007533b0` sztringjei a Mentés gombot (`editpanel/writetodisk`, `CFilterStackUI::save`) és az Undo/Redo feliratokat érintik, a lemezre írás helye nem látszik belőlük. Kell: C3 Colab-feladat (`picasa_ini`, `kepmappa`, `db3` kimenet; a végrehajtó mindhármat tudja) |
| 17 | A csempegrafikák és az effektalgoritmusok képpont-paritása | HATÓKÖRÖN KÍVÜL | a lap fejléce (3. sor) külön kutatásra utalja; a render-sáv paritás-jegyei viszik (`filterdesc-registry.md`, #626) |
| 18 | A PicasaPy hatodik, "Legacy Effects" füle | HATÓKÖRÖN KÍVÜL | saját kiegészítés (`EditorTabBar.qml:136-152`), az eredetiben nincs; a szerkesztő fülsávja a tulajdonosi döntés szerint hét fül (`docs/decisions/szerkeszto-bal-panel.md`, 2026-08-15) |

**Nyitott kérdések: 0 nyílt · 12 lezárva · 4 blokkolt · 2 hatókörön kívül · 0 "csak nyitva".**

### 4. Colab-lépéssorok

A lépések a végrehajtó igéit használják (`picasa: indit`, `var_ablak`, `kattint`, `billentyu`, `var`). A koordináták a `referencia/felulet-terkep` katalógusaiból valók (1280x1024 képernyő): fülek `ful1` (28, 95), `ful3` (139, 95); Alapjavítások: Auto Contrast (136, 231), Auto Color (217, 231), I'm Feeling Lucky (56, 232); 1. effektfül: Sharpen (48, 181), Sepia (137, 181), B&W (225, 180), Warmify (48, 252), Soft Focus (136, 322). Minden feladat friss indulásból megy, hogy az Undo-állapotok ne keveredjenek. Tesztkép: a mintamappa vágatlan, színes képe (a #7327 felvételek `color_patches.jpg`-ja jó). Kimenet, ha nem írom másként: `kepernyokep`, `allapot`, `picasa_ini`.

**C1. A menü és a Ctrl+Shift+B nyitott szerkesztőben (T1 megerősítése; nem előfeltétele a jegynek).**

1. `picasa: indit`, `var_ablak: Picasa`, dupla kattintás a képen: a szerkesztő nyílik. Képkocka A: kiinduló állapot (aktív fül, csempék, a Visszavonás/Újra sor szürke).
2. Kép ▸ Csoportos szerkesztés ▸ (a nyolc parancs egyike, a menüt a `menuk.json` `eMenuPicture::BatchEdit` rekordja szerint nyisd). Nyolc külön feladat: Auto Contrast, Auto Color, I'm Feeling Lucky, Sepia, Sharpen, Warmify, Film Grain, Black and White.
3. Képkocka B. Rögzítendő: aktív fül; változott-e a kép (képponteltérés A-hoz képest a kép területén); a Visszavonás/Újra sor szövege (várt, ha igaz: "Undo Sepia" és társai); a megfelelő csempe jelvénye vagy halvány állapota; Sharpen esetén megnyílt-e a paraméterpanel Alkalmaz és Mégse gombbal; a `picasa_ini` `filters=` sora.
4. Kontroll, külön feladat: ugyanaz a kép, a parancs helyett a csempe kattintása (az Auto hármas az 1. fülön, a többi a 3. fülön a fenti koordinátákon). B és a kontroll képe, Undo sora és `filters=` sora egyezik-e.
5. Külön feladat: szerkesztőben `billentyu: ctrl+shift+b`; képkocka, Undo sor, `filters=`. Pozitív kontroll: `ctrl+shift+e` (a `job-810` már rögzítette).
6. Külön feladat: nyitott Soft Focus panel (136, 322) mellett a Sepia menüparancs: marad-e a panel, kerül-e hatás a képre, mit mutat az Undo sor.
7. Kiértékelés: T1 megerősített, ha a 2-3. lépés hatása a 4. lépés kontrolljával egyezik; cáfolt, ha csak az aktív fül változik, a kép, az Undo sor és a `filters=` nem. Cáfolat esetén T1 elvetendő, és az első kör D1 szakasza egy mérésen alapuló, mai állapotot rögzítő szövegre cserélendő.

**C2. Paraméteres effekt: újranyitás, ismétlés, Undo/Redo (14. és 15. tétel).**

1. Szerkesztő, 1. effektfül, Soft Focus (136, 322): a panel nyílik. Képkocka és az összes csúszka kijelzett értéke (ez az alapérték).
2. Egy csúszkát elhúz (rögzítsd a kiinduló és a végső helyét), képkocka; Mégse; képkocka. Soft Focus újra: a csúszka az alapértéken áll, vagy az elhúzott helyen? (14. tétel).
3. Csúszkát elhúz; Alkalmaz; képkocka; a Visszavonás/Újra sor szövege. A `picasa_ini` kimenet külön feladatban.
4. Soft Focus újra, a csúszkák értéke (az utoljára alkalmazott, vagy az alap?). Alkalmaz változtatás nélkül: Undo sor. Majd annyiszor Visszavonás, amíg az Undo sor szürke nem lesz: rögzítsd a képet és a sort minden lépés után (a lépésszám a 15. tétel).
5. Egykattintásos ismétlés: Sepia (137, 181) kétszer egymás után: képkocka, Undo sor, `picasa_ini` (két `sepia` bejegyzés van-e a `filters=` sorban: a 11. tétel futásmérése), Visszavonás, képkocka, Újra, képkocka.
6. Ugyanez az I'm Feeling Lucky csempével (56, 232), mert a PicasaPy ott "láncvégi no-op" szabályt alkalmaz (`MainKeyboardShortcuts.qml:183-185`): az eredeti kétszeri kattintásnál bővül-e a lánc, és mit mutat az Undo sor.
7. A csúszka fogantyúján dupla kattintás: visszaáll-e az alapértékre (képkocka, érték).

**C3. A mentés ideje és az indexhatás (16. tétel).** Három külön feladat, mind: szerkesztő, Sepia csempe kattintása; kimenet: `kepernyokep`, `allapot`, `picasa_ini`, `kepmappa`, `db3`.

1. A feladat a kattintás után még a szerkesztőben ér véget. Rögzítendő: van-e `filters=` sor a `picasa_ini`-ben (azonnal ír-e); `db3` bélyegkép-bejegyzés változása.
2. A feladat a következő képre lépés után ér véget (nyíl a szerkesztőben). Ugyanazok a kimenetek.
3. A feladat a szerkesztő Mentés (Save, `editpanel/writetodisk`) gombja után ér véget. Rögzítendő: az eredeti képfájl mérete és dátuma (`kepmappa`), az eredeti-másolat (backup) megjelenése, a `backuphash` a `picasa_ini`-ben, a gomb felirata ("Undo save and keep edits" tipp), a Visszavonás/Újra sor.
4. Kiegészítés, ha a három eltér: ugyanez Alkalmaz után egy paraméteres effektre (Soft Focus), mert a `0x00750ff0` ág a `0x00750ed0`-től eltérő úton ír.

**C4. Írásvédett kép (13. tétel).** Futásmérés ma nem adható fel: a végrehajtó nem tud fájlattribútumot állítani. Ezért a következő irány a T2 1. pontja (Ghidra), és csak utána a végrehajtó bővítése egy `csak_olvashato` lépéssel (a `picasa-colab-jobs` privát repó feladata, nem ez a lap).

### 5. Amit KIZÁRTAM

- Az első kör "a menü csak navigál, nem alkalmaz" állítását (D1): az öt névvel hívó ág a `0x005f8520`-ra fut, ami a csempe végpontja. Ez az út zárva, ne járja újra senki.
- Azt, hogy a `0x00579330` navigáló függvény: 37 bájtos feltétel-őr.
- Azt, hogy az effekt-paraméterpanelen az Alaphelyzet gomb "hiánya a PicasaPy forrásában nem bizonyít semmit": az eredeti erőforrásában is hiányzik, két független úton (resource és felvétel).
- Azt a feltevést, hogy a #7123 tesztje az eredeti viselkedést rögzítette: a teszt az akkor nyitott kérdést ("kijelöl vagy alkalmaz is") a nem-alkalmazás irányába zárta.
- Azt, hogy a Copy All Effects többképes ágához új felvétel kell: a #6861 valódi menükattintásos teszt az eredeti mért Info-szövegével egyezik.
