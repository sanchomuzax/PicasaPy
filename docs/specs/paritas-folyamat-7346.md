# #7346: A három Effektek lap folyamata

Vizsgálati tárgy: Picasa 3.9.141.259 és a munkafa jelenlegi PicasaPy-forrása. Ez a lap az effektválasztás, paraméterezés, alkalmazás, elvetés, ismétlés és lánc folyamatait kapcsolja össze. A csempegrafikák és az effektalgoritmusok képpont-paritása külön kutatás.

## Következtetés

Az eredeti három Effektek lapjának 36 csempéje és mind a kilenc Shift-változata megvan a PicasaPyban; az eredeti futtatott felvételek a paraméterpanel alapfolyamatát is részben rögzítik. Két jelenlegi forráseltérés igazolható: a Kép ▸ Csoportos szerkesztés parancsai a PicasaPyban csak a fület választják ki, az eredeti pedig a célvezérlőt is; továbbá a csempék kék jelvényének feltétele a két programban mást jelent. A teljes futásidejű paritás nyitott, mert nem áll rendelkezésre friss, párhuzamos Picasa 3.9/PicasaPy mérés az ismétlésről, megjegyzett paraméterállapotról, mentett képfájlról és visszavonás/újra állapotról.

**Helyesbítés (2026-11-22, Zárókör):** a D1 állítása megdőlt. A Kép ▸ Csoportos szerkesztés parancsai szerkesztőben nyitott képnél az eredetiben a csempekattintás végpontját is futtatják (az egykattintásos hatás a képre kerül, a Sharpen a paneljét nyitja), nem csak fület váltanak. A kérdések mérlege a Zárókör végén: 12 lezárva, 4 blokkolt, 2 hatókörön kívül, 0 csak nyitva. Az írásvédett-kapu (13. tétel) kiolvasása után: 13 lezárva, 5 blokkolt, 2 hatókörön kívül, 0 csak nyitva (T2).

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
- ~~Ghidra-kör nem szükséges: a nyitott pontok futásidejű mérések, az eredeti csempe- és menüút feloldásához a célzott disassembly és a korábbi mérések elegendők.~~ **HELYESBÍTVE (Zárókör):** a csempe- és menüút a disassemblyből eldőlt, de az írásvédett-kapu feltételéhez (0x00541fc0) és a paraméterpanel kezdőérték-forrásához Ghidra-kör kell; lásd a Zárókör mérlegének 13. és 14. tételét. **A 13. tétel azóta eldőlt** a 0x00541fc0 és a 0x0047cea0 kiolvasásával (T2); a 14. tételhez még kell.

## Módosított fájlok

- docs/specs/paritas-folyamat-7346.md: a csempék, menük, paraméterpanel és mentési folyamat összevetése; két forrásból alátámasztott eltérés; nyitott Colab-lépések.

## Zárókör (2026-11-22)

### Következtetés

A három Effektek lap folyamatából a lezárható pontok egyeznek az eredetivel: a 36 csempe és a kilenc Shift-pár, a kék jelvény jelentése, a paraméterpanel Alkalmaz és Mégse gombja (az Escape is), valamint a többképes Copy All Effects figyelmeztetés. Az eredeti effekt-paraméterpanelén nincs Alaphelyzet gomb, ezért a PicasaPy panelének sem kell.

A zárókör egy valódi eltérést talált, és ezzel az első kör D1 szakasza megfordul. A Kép ▸ Csoportos szerkesztés parancsai az eredetiben szerkesztőben nyitott képnél nem csak fület váltanak: a fül kiválasztása után ugyanazt a végpontot futtatják, mint a csempekattintás (az egykattintásos hatás azonnal a képre kerül, a Sharpen a paraméterpaneljét nyitja). A Ctrl+Shift+B kezelője azonos felépítésű a már mért Ctrl+Shift+E kezelőjével, ezért az is a megnyitott képre hat. A PicasaPyban a menüparancs csak fülváltás, a Ctrl+Shift+B szerkesztőben ki van kapcsolva. Erre egy fejlesztői jegytörzs készült (T1).

Új lelet az írásvédett-kapu is, és a neve félrevezető: a 0x00541fc0 nem írásvédettséget vizsgál, hanem azt, hogy a megnyitott mappa az iPhoto- vagy az Apple Photos-könyvtárban van-e. Ott a csempekattintás, a kötegelt effekt, a Ctrl+Shift+B/E és az Auto RedEye előtt rákérdez ("Make a Copy" / "Cancel Edit"); sima írásvédett mappánál nem kérdez, az általános "This file is read only" szöveg a kapuból elérhetetlen. Nálunk nincs ilyen kapu, a mentéskori írásvédett-jelzés pedig más feltételre épül, és az eredeti olyan szövegét használja, amelyet az eredeti a sima írásvédett mappánál nem mutat (T2, T3). A "Make a Copy" célmappájának utolsó eleme és a sima írásvédett fájl eredeti viselkedése futásmérésre vár (T4, C4a, C4b). Három további tétel futásmérésre vár, ezekhez Colab-lépéssor van (C1-C3).

### Helyesbítések az első kör szövegéhez

| Az első kör állítása | Helyesbítés | Bizonyíték |
|---|---|---|
| D1: az eredeti menüág "a vezérlőhöz navigál", a "Kész, ha" szerint "nem alkalmazza automatikusan". | Megdőlt. Szerkesztő-ágban az eredeti a csempekattintással egyenértékű: fül és csempevégpont. | 1. szakasz |
| A 0x00579330 "szerkesztőállapot-ellenőrzése után navigál". | A 0x00579330 egy 37 bájtos őr (0x00579330-0x00579354): igazat ad, ha a [0x00d67914] nem nulla, az `editpanel/preview` (0x00c88a2c) létezik és a +0x20c bájtja 0. Nem navigál, a navigálást a hívó kezelők végzik. | `cmp dword ptr [0xd67914], 0` (0x00579330), `mov edx, 0xc88a2c; call 0x9c2fc0` (0x00579339), `cmp byte ptr [eax + 0x20c], 0; sete al` (0x0057934a) |
| "Ghidra-kör nem szükséges." | Két ponton szükséges: az írásvédett-kapu feltétele (0x00541fc0) és a paraméterpanel kezdőérték-forrása (a panelfelépítő 0x00750ff0 és hívottja, a 0x006ac980). | 3. szakasz, 13. és 14. tétel |
| Az írásvédett-kapu "az írásvédett fájl kapuja" (a T2 első változata és a `paritas-ellenorzes-archiv-2.md` 3038. sora: "Írásvédett lemezen (pl. CD-ROM) az ini- és fájlírás elutasításra kerül (`AllowReadOnlyEdits` kapu `0x00602100`-ban)"). | Megdőlt. A kapu nem írásvédettséget vizsgál, hanem azt, hogy a mappa útvonala az iPhoto- vagy az Apple Photos-könyvtár alatt van-e; sima írásvédett mappánál a kapu nulla értékkel kilép. A kérdés és a "Make a Copy" ág is csak könyvtári képekre él. | T2: `call 0x0047cea0` (0x00542109), `call 0x00987030` (0x0054212c), `xor eax, eax` (0x00542161); az elágazás-elemzés |
| A `picasa-menu-parancsok-viselkedes.md` 1649. sora: a `0x00602100` az `AllowReadOnlyEdits` olvasása után "a kijelölés körét (`0x541fc0`)" kezeli. | Nem a kijelölés körét: a `0x00541fc0` az iPhoto-/Photos-kapu, nullát ad, ha a művelet futhat, és nem nullát, ha nem. | T2, "A visszatérési érték és a három effektes hívó" |
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
| Ctrl+Shift+B | `0x005e6370` → `0x005fe370(panel, "bw")`, szerkesztő-állapot vizsgálata nélkül, a megnyitott képre (a Ctrl+Shift+E ikertestvére, `job-810`) | nézőben kikapcsolva | a Ctrl+Shift+E mintájára (`MainKeyboardShortcuts.qml:166-192`) nézőben is él, ugyanazzal a kapuval (`panel.enabled`, nincs aktív módváltó eszköz, kiegyenesítés vagy paraméterpanel) |

**Nem szabad:** a könyvtárnézeti ág (kijelölt képekre köteg) változatlan; a forgatás és a vörösszem-javítás ága változatlan; a Sharpen menüparancs nem alkalmaz hatást a panel Alkalmazása előtt; a Shift-változatok (`unsharp`, `grain`) a menüben nincsenek (nincs felhasználói eset, `picasa-menu-parancsok-viselkedes.md` 33.3).

**Kész, ha:**

- [ ] Nyitott nézőnél a Sepia, a Black and White, a Warmify és a Film Grain parancs után a kép módosult, a `filters=` lánc végén az effekt áll, a Visszavonás/Újra sor az effektet mutatja, és egy Visszavonás visszaadja az előző állapotot; az eredmény megegyezik a csempekattintáséval (a Film Grainnél az egyképes köteg eredményével).
- [ ] Az Auto Contrast, az Auto Color és az I'm Feeling Lucky nyitott nézőnél az 1. fület választja és a csempe kattintásával egyező hatást ad (a láncvégi no-op szabály, `enhanceInViewer` megjegyzése, megmarad).
- [ ] A Sharpen nyitott nézőnél a 3. fület választja és ugyanúgy nyitja meg a Sharpen paneljét, mint a Sharpen csempe (`effect_params.py:485`: `unsharp2`, Amount csúszka); a lánc nem változik, amíg az Alkalmaz nincs megnyomva; a Mégse visszaadja az állapotot.
- [ ] A Ctrl+Shift+B nyitott nézőnél a megnyitott képre fekete-fehéret ad, a kapuk a `enhanceInViewer` kapuival azonosak; könyvtárnézetben a viselkedése változatlan.
- [ ] A `tests/app/qml_functional/test_sepia_bw_fulvalasztas_7123.py` "Nem szabad" pontja ("a nézőben a tétel NEM módosítja a `filters=` láncot") megfordul: a teszt a hatást is méri, valódi menükattintással és valódi billentyűvel (nem a metódus hívásával).
- [ ] Vizuális ellenőrzés: C1 felvételei (eredeti) és a PicasaPy képe ugyanazon a képen, a három állapot (előtte, utána, Undo után) egymás mellett, mért eltéréssel; ahol a teszt csak számol, a jegy kimondja, hogy a vizuális egyezést nem méri.

**Bizonyítottsági fok:** erős (statikus), futásmérés NINCS (C1). Megfejtve, hogy az eredeti a csempe végpontját hívja; a látható hatás (Undo felirat, jelvény) méréséhez C1 kell.

**Mit NEM tudok, de a szöveg alapján tudni látszik:** (1) hogy a menüparancs hogyan viselkedik nyitott paraméterpanel mellett (C1 7. lépés); (2) hogy a `[0x00d67849]` jelző mit jelent (a Shift-ág él-e egyáltalán); (3) hogy a `0x00a54b70` hívás mit frissít; (4) ~~hogy a menüág a `0x006021d0` burkolót megkerüli, ezért az írásvédett-kapu e menüágban nem látszik~~ **LEZÁRVA (T2):** a szerkesztő menüág öt közvetlen hívású parancsa (Sepia, Sharpen, Black and White, Warmify, Film Grain) a `0x005f8520`-at kapu nélkül hívja, tehát iPhoto-/Photos-mappában sem kérdez; a három Auto parancs a csempeelemen át átmegy a kapun (erős következtetés).

**Érintett fájlok:** `PhotoViewerGeometryActions.qml`, `MainMenuBar.qml`, `MainKeyboardShortcuts.qml`, `MainWindowCommands.qml` (csak olvasva), `tests/app/qml_functional/test_sepia_bw_fulvalasztas_7123.py`; a Ctrl+Shift+E nézőbeli tesztje (#7352) a billentyűs teszt mintája.

**Független újralevezetés (#140):** nem készült; a T1 foka addig "erős".

### T2. Az írásvédett-kapu (0x00541fc0): feltétel, gombok, másolás és a lefedett utak (LEZÁRVA, két al-kérdés kivételével)

**Következtetés.** A kapu neve félrevezető: **nem írásvédettséget vizsgál.** Nem néz fájlattribútumot, mappa-írhatóságot vagy hálózati helyet; az egyetlen feltétele a megnyitott mappa útvonala: az iPhoto- vagy az Apple Photos-könyvtár alatt van-e. Ha igen, a szerkesztő művelet előtt rákérdez ("Make a Copy" / "Cancel Edit"), és a művelet ezen a kattintáson egyik válasz után sem fut le (egy szélső eset kivételével, lent). Minden más mappánál, a sima írásvédettnél is, a kapu nullával kilép, nem kérdez, és a művelet fut. Az általános "This file is read only..." szöveg a kapuból elérhetetlen (lásd lent, bájtpásztázással).

**A feltétel lépésről lépésre** (a teljes 1952 bájt elolvasva, a disassembly és a dekompiláció azonos olvasata; ecx = a főablak-objektum, `[this + 0xeac]` az aktuális mappa- vagy albumcsomópont, `[this + 0x2bc]` az adatbázis-környezet, a verem `param_2` bájtja a "csendes mód" jelző):

| Lépés | Cím | Mit tesz |
|---|---|---|
| 1 | 0x00541fde, 0x00541fec | `mov eax, [edi + 0xeac]` ... `je 0x5420bb`: ha nincs aktuális csomópont, a kapu 0-t ad (0x005420bb: `xor eax, eax`) |
| 2 | 0x00542051 | `call eax`: a `[[db + 0x48] + 0x14]` vtábla-rekesz a csomópont `+0x3c0` azonosítójával: a csomópont mappaútvonala sztringként |
| 3 | 0x0054206c-0x005420f9 | Üres útvonalnál (album) a kijelölés listája (`0x007166c0`); ha az is üres, 0 (0x005420bb); különben az első elem rekordjából (`0x004edf60`, a `db + 0xf8` tábla) jön az útvonal |
| 4 | 0x00542109 | `call 0x0047cea0(db, &útvonal, 0)`: az iPhoto-alapútvonal előtagja-e az útvonalnak; `jne 0x542168` (0x00542110), ha igen |
| 5 | 0x00542113-0x00542133 | Ha nem: `call 0x0047cfc0(db)` (az Apple Photos-alapútvonal, lusta képzéssel), majd `call 0x00987030` (ecx = alapútvonal, eax = &útvonal, `push 0`); `jne 0x542168` (0x00542133), ha igen |
| 6 | 0x00542161 | Ha egyik sem: `xor eax, eax; jmp 0x542745`: **0, a művelet fut** |
| 7 | 0x00542168-0x0054216f | `cmp byte ptr [esp + 0x3414], bl; jne 0x54272a`: ha a `param_2` bájt nem nulla (csendes mód), nincs kérdés, a kilépő érték `0xf4242` (0x00542740) |
| 8 | 0x00542175-0x005422c6 | A kérdés és a két gomb (lent) |

**Az előtag-teszt.**

- **`0x0047cea0`** (279 bájt, 0x0047cea0-0x0047cfb6): a `[db + 0x2e78]` az iPhoto-alapútvonal gyorsítótára, üresen a `0x0099bce0` építi (0x0047ced1). Ha a harmadik argumentum nulla (`cmp byte ptr [esp + 0x1c], 0; je 0x47cf97`, 0x0047ceeb-0x0047cef2), a `0x00987030`-at hívja és `setne al`-t ad (0x0047cfa6-0x0047cfb0). Nem nulla harmadik argumentumnál bájtonkénti egyenlőség-vizsgálat (0x0047cf20-0x0047cf3a); ezt más hívók használják (például `0x004ac8f0`), a kapu nem.
- **`0x00987030`**: igaz, ha az eax által mutatott sztring (a mappa útvonala) az ecx-beli alapútvonallal **kezdődik** (vagy azzal egyenlő). Üres vagy nulla alapútvonalra hamis (0x009870c5). A veremargumentum nulla (`cmp byte ptr [esp + 4], 0; je 0x987073`, 0x0098704b-0x00987055), ezért a **kis- és nagybetűt nem különbözteti meg** (az A-Z betűk +0x20, 0x0098707b-0x009870a0, csak ASCII). Útvonalhatár-vizsgálat nincs: a `...\iPhoto Library\Masters2` is előtagként egyezne.
- **Az iPhoto-alapútvonal** (`0x0099bce0`): `<Képek mappa>` + "iPhoto Library" (0x00c81800, 0x0099bd23) + "Masters" (0x00c8b454, 0x0099bdda), ha a "Masters" mappa létezik (`call 0x992ed0`, `je 0x99be80`, 0x0099bdfd-0x0099be04), különben "Originals" (0x00c81904, 0x0099be8d). A `0x00992ed0` egy létezés-vizsgálat: a függvénymutatón át (`call [0xd694bc]`) kapott értéket csak a -1-hez hasonlítja (`cmp eax, -1; setne bl`, 0x00992f0d-0x00992f11), attribútumbitekhez nem nyúl.
- **Az Apple Photos-alapútvonal** (`0x0099bf40`, a `0x0047cfc0`-n át): `<Képek mappa>` + "Photos Library" (0x00cd8fec, 0x0099bf83) + "Masters" (0x0099c03a), ha létezik (`call 0x992ed0`, 0x0099c05d), különben "Originals" (0x0099c0ed).
- **`<Képek mappa>`** (`0x009966a0`): ha a `[0x00d4a61c]` objektum létezik, annak `+0x54` sztringje (0x009966b4-0x009966cc); ha nem, a CSIDL 0x27 (CSIDL_MYPICTURES: `push 0x27; call 0x996140`, 0x009966ef).

**A kérdés és a két gomb** (0x00542175-0x005422c6). A szövegeket a `0x009ae560` kulcs szerint keresi, a beégetett szöveg az alapérték:

| Eset | Szöveg | Kulcs |
|---|---|---|
| iPhoto-könyvtár | "This file belongs to iPhoto, and is read only. In order to edit this file, Picasa needs to copy the file's event out of iPhoto. Would you like to make a copy now?" (0x00c8af30) | `CThumbUI::iPhotoReadOnlyPrompt` (0x00c8afd4) |
| Apple Photos-könyvtár | "This file belongs to Apple Photos, and is read only. In order to edit this file, Picasa needs to copy the file's event out of Photos. Would you like to make a copy now?" (0x00c8aff8) | `CThumbUI::ApplePhotosReadOnlyPrompt` (0x00c8b0a4) |
| általános (elérhetetlen) | "This file is read only. In order to edit this file, Picasa needs to copy the file's folder. Would you like to make a copy now?" (0x00c8ae90) | `CThumbUI::ReadOnlyPrompt` (0x00c8af10) |

A szöveg kiválasztása a 0x00542239-0x00542255 között: az iPhoto-jelző (`[esp + 0x1e]`) igaz, akkor az iPhoto-szöveg; különben az Apple Photos-jelző (`[esp + 0x2b]`) igaz, akkor az Apple Photos-szöveg; különben az általános. A gombok: igen = "Make a Copy" (0x00c8b0ec, kulcs `ReadOnlyCopy::YesButton`, 0x00c8b0f8), nem = "Cancel Edit" (0x00c8b0c8, kulcs `ReadOnlyCopy::NoButton`, 0x00c8b0d4); a hívás `0x009bac20(0, szöveg, igen, nem, 0, 0)` (0x005422bc), a kimenet `test al, al; je 0x542706` (0x005422c4-0x005422c6): nulla = "Cancel Edit".

**Az általános szöveg elérhetetlen.** A kérdés-szakaszba (0x00542168) a függvényen kívülről csak két ugrás vezet, a 0x00542110 és a 0x00542133, és mindkettő az iPhoto-, illetve az Apple Photos-teszt igaz ága (az összes 64 elágazás elemezve). Az általános ág csak akkor választódna, ha mindkét jelző hamis, de akkor a kapu a 0x00542161-en már 0-val kilépett. A szöveg és a kulcsa az egész képfájlban egy-egy helyről hivatkozott (0x0054217b és 0x00542176).

**"Cancel Edit".** A 0x00542706-0x00542745 szakasz csak a sztringek felszabadítását (`0x00401000`, `0x00412790`) tartalmazza, majd `mov eax, 0xf4242` (0x00542740). Nincs másolás, nincs módosítás; a kilépő érték 1000002.

**"Make a Copy"** (0x005422cc-0x00542702):

1. Listák: `0x007164b0(csomópont)` (a mappa képobjektumainak listája, a `paritas-ellenorzes-archiv-1.md` 1440. sora szerint) és `0x007166c0(csomópont, 0)` (a kijelölés listája). Ha az útvonal a 2. lépésben üres volt (album, a `[esp + 0x1f]` jelző, 0x005422fd), még a `0x00441cd0` mappakeresés, a `[db + 0x48]` `+0x2c` rekesze, a `0x006ca8c0` és a `0x00891110` következik (0x00542301-0x005423b3); a lista bővítése nincs végigkövetve. A `[this + 0x284]` objektum `+0x10` rekeszét a "]hidden" névvel hívja (0x005423d4-0x005423d9); a szerepe nincs kiolvasva. Ha ezután a lista üres (0x005423e0-0x005423e4), a kapu 0-t ad, tehát a művelet az eredeti mappán fut.
2. Célmappa: `<Képek mappa>` (`0x009966a0`, 0x0054254d) + a kulcs szerinti relatív rész: iPhoto-nál "Picasa/Imported From iPhoto/" (0x00c8b138, kulcs `CThumbUI::iPhotoReadOnlyPath`, 0x00c8b158; 0x00542501-0x0054250b), Apple Photos-nál "Picasa/Imported From Apple Photos/" (0x00c8b178, kulcs `CThumbUI::applePhotosReadOnlyPath`, 0x00c8b19c; 0x00542513-0x00542518). Az általános "Imported Files" (0x00c8b110, kulcs `CThumbUI::ReadOnlyPath`, 0x00c8b120) elérhetetlen ágon áll. Az összeépítést a `0x00408390` (útvonalszerkezet), a `0x009a3c70` és `0x009a38a0` (a forrásszerkezet `+0x410` sztringjének átvétele: `mov eax, [eax + 0x410]` 0x009a3c70, `lea ebx, [ebp + 0x410]` 0x009a38d8), valamint a `0x0049ff10` és `0x009a37b0` (a fájlnév és a kiterjesztés a rekordból) végzi (0x0054256a-0x00542630).
3. Másolás: `call 0x005350b0` (0x00542672; ecx = főablak, a képlista, a célszerkezet, három darab `push 1`). A `0x005350b0` a Beillesztés közös fájlmásoló rutinja; névütközésnél a "Rename Duplicates" / "Skip Duplicates" választást adja (`paritas-ellenorzes.md` 903. sor). A Beillesztés Copy/Move megerősítését a `0x00535020` kéri (ugyanott, 900. sor); a kapu közvetlenül a `0x005350b0`-t hívja, a `0x00535020` nincs a hívottjai közt, tehát ez a megerősítés itt nem szerepel (statikus).
4. Eredmény: ha a `0x005350b0` nullát ad, a kilépő érték `0xf4242` (0x005426c4-0x005426c6, 0x00542706); ha nem nullát, a kapu azt adja vissza (`mov eax, esi`, 0x00542702).

**A visszatérési érték és a három effektes hívó.** A kapu nulla kilépő értéke azt jelenti: a művelet fut; minden nem nulla: a művelet nem fut. A három, effekttel foglalkozó hívó így kezeli:

| Hívó | A kulcs hatása | Nem nulla érték esetén |
|---|---|---|
| `0x006021d0` (csempekattintás-burkoló) | olvassa az `AllowReadOnlyEdits` kulcsot; nem nulla esetén a kaput kihagyja (0x00602205 `jne 0x602266`) | a `0x005f8520` nem hívódik (0x0060220f-0x00602213); ha a szerkesztő nyitva van (`editpanel/preview` létezik, `[+0x20c]` bájtja 0), előbb a `0x005f8160` rendezi az állapotot (0x00602215-0x0060223c); visszatér a kapu értékével |
| `0x005fe370` (kötegelt effekt) | nem olvassa a kulcsot; `param_2` = 0 (0x005fe383) | `mov eax, 0xf4242; ret 4` (0x005fe391) |
| `0x00602100` (Auto RedEye keret) | olvassa a kulcsot, a `0x006021d0`-nal azonos mintában (0x00602107, 0x00602133-0x00602135) | visszatér a kapu értékével (0x0060213f-0x0060218b), a delegált kezelő nem hívódik |

Tehát a "Make a Copy" után sem a másolaton, sem az eredeti mappán nem fut le az effekt ezen a kattintáson. Mi látszik utána a képernyőn (melyik mappa és kép van kijelölve), azt a 19. tétel méri. A tizenhárom hívóhely közül egyetlen, a `0x005d21bf` (a `0x005d21a0` függvényben) hív csendes móddal (`param_2 = ([esi + 0x20] != 0x8000001)`, 0x005d21b7-0x005d21be): iPhoto-/Photos-mappában ez a hívás kérdés nélkül elutasít. A függvény funkciója nincs azonosítva (hívói: 0x005d2290 és 0x005de8e0).

**Mely utak mennek át a kapun** (a Kész, ha harmadik pontja):

| Út | Belépő | Átmegy-e | Bizonyíték |
|---|---|---|---|
| Csempekattintás | `0x005d59f0` és `0x005d3290` → `0x006021d0` | igen; az `AllowReadOnlyEdits` kikapcsolja | 0x0060220a |
| A Kép ▸ Csoportos szerkesztés nyolc parancsa, könyvtári ág | 0x005cc93f, 0x005cc971, 0x005cc9a3, 0x005cca3d, 0x005cca67, 0x005cca94, 0x005ccac1, 0x005ccb2c → `0x005fe370` | igen; a kulcs nem kapcsolja ki | 0x005fe388 |
| Ctrl+Shift+B és Ctrl+Shift+E | 0x005e6381 és 0x005e6398 → `0x005fe370` | igen, szerkesztőben nyitott képen is (a kezelő nem vizsgál szerkesztő-állapotot, 1. szakasz) | 0x005fe388 |
| Auto RedEye | 0x005ccb41, 0x005d64a5, 0x005d68c6 → `0x00602100` | igen; a kulcs kikapcsolja | 0x0060213a |
| Menü, szerkesztő-ág: Auto Contrast, Auto Color, I'm Feeling Lucky | az `editpanel/autolighting`, `autocolor`, `enhance` elem kattintása → csempekezelő → `0x006021d0` | igen (erős következtetés; az elemek kattintás-kezelőjét nem követtem végig, 1. szakasz) | 1. szakasz |
| Menü, szerkesztő-ág: Sepia, Sharpen, Black and White, Warmify, Film Grain | 0x005cc9e5 → `0x005f8520` közvetlenül | **nem**: a `0x005f8520` nem hívja a kaput (nincs a tizenhárom hívóhely közt) | 0x005cc9e5 és a hívóhelyek bájtpásztázása |

A tizenhárom hívóhely további tagjai: a csempekezelő `0x005d59f0` alatti kezelők (`0x005f2840` (`editpanel/picnikwin`), `0x005f7140`, `0x005f8200`, `0x005f82c0`, `0x005f8380` (`finetune`)), a forgatás közös végrehajtója `0x005eef30`, valamint `0x00532ec0`, `0x0053a790` és `0x005d21a0`; ezek azonosítása nem a #7346 tárgya.

**A `Preferences\AllowReadOnlyEdits` kulcs.** A `0x00407a20` a `0x80000001` (HKEY_CURRENT_USER, 0x00407a3b) alatt a "Preferences" (0x00c7eafc) és az "AllowReadOnlyEdits" (0x00c9a044) nevekhez köti az olvasót; a `0x004019b0` egy négy bájtos (DWORD) értéket olvas (`mov dword ptr [esp + 0x10], 4`, 0x00401a3e). Nem nulla érték: a kapu kimarad. Hogy a kulcs hiányában mekkora értéket ad az olvasó, a `0x00407a20` belsejéből nincs végigkövetve; a hívók a `xor eax, eax`-szel (0x006021e7, 0x00602117) nullát adnak át, ezt alapértéknek olvasom (erős következtetés, a kulcs nélküli C4a mérés megerősíti: a kérdés megjelenik). A Preferences-kulcsok helye a `00-index.md` 2026-09-03-i feljegyzése szerint `HKEY_CURRENT_USER\SOFTWARE\Google\Picasa\Picasa2\Preferences`. A név az egész képfájlban két négy bájtos hivatkozásból áll elő (0x00602107 és 0x006021d7), tehát csak a `0x00602100` és a `0x006021d0` olvassa; a nevén nincs író a futtatható állományban.

**Bizalmi fok: erős (statikus, két független út).** (a) A függvény teljes disassembly-je és a dekompiláció azonos olvasatot ad. (b) A hívások és a sztring-hivatkozások bájtszintű pásztázása (lent). Futásmérés a kapuról: NINCS (C4a). A "Make a Copy" célmappájának utolsó eleme és a másolt fájlok köre nincs kiolvasva (19. tétel).

**Cáfoló kísérlet.** (1) Kerestem a kapuban fájlattribútumot, írhatóságot vagy hálózati helyet vizsgáló hívást: a 40 közvetlen hívott közt az egyetlen import az `InterlockedIncrement`, a többi belső függvény; a három közvetett hívás (a vtábla-rekeszek: 0x00542051, 0x00542390, 0x005423d9) kimenete a kapu számára útvonal, rekord, illetve lista. A lemezre csak a `0x00992ed0` létezés-vizsgálata néz (Masters vagy Originals), ez a -1-et vizsgálja, nem az attribútumbiteket. (2) Kerestem olyan utat, amely az általános "read only" szöveghez vezet: nincs (lásd fent, 64 elágazás). (3) Kerestem olyan hívót, amely az `AllowReadOnlyEdits`-t máshol is olvassa: nincs (két hivatkozás).

**Bájtszintű pásztázással igazolt negatív állítások** (a teljes Picasa3.exe, E8 és E9 relatív célok a `.text`-ben, abszolút 4 bájtos hivatkozások a teljes állományban):

- A `0x00541fc0`-ra pontosan tizenhárom `call` mutat (0x00532eec, 0x0053a7a6, 0x005d21bf, 0x005eef3f, 0x005f2856, 0x005f3104, 0x005f714f, 0x005f8209, 0x005f82c9, 0x005f8394, 0x005fe388, 0x0060213a, 0x0060220a), `jmp` és abszolút mutató (vtábla) nincs.
- Az általános kérdésszöveg, a kulcsa, az iPhoto- és Photos-szöveg, mindkét gombfelirat és az "Imported Files" egy-egy hivatkozással szerepel, mind a `0x00541fc0`-ban (0x0054217b, 0x00542176, 0x005421ab, 0x005421d5, 0x00542273, 0x00542292, 0x005424d3).
- Az `AllowReadOnlyEdits` nevére két hivatkozás van: 0x00602107 és 0x006021d7.
- A `0x005f8520`-ra hét hívás mutat (0x005956ab, 0x00595d94, 0x005cc9e5, 0x005d77be, 0x005d78c1, 0x005fe494, 0x0060226d); a `0x005fe494` a `0x005fe370` belsejében a kapu UTÁN, a `0x0060226d` a burkolóban a kapu után (vagy a kulcs miatt a kapu kihagyása után) áll; a többi négy (a sztringjeik szerint a videóvágó vezérlők `0x005952d0` és `0x00595960`, valamint a fülváltó segédek `0x005d7780` és `0x005d77d0`) és a menü (0x005cc9e5) kapu nélkül hívja.

**Nálunk (szó szerinti idézetek).**

A csempekattintás útján nincs útvonal- vagy írhatóságvizsgálat. `src/picasapy/app/qml/PicasaPy/EditorEffectsTab1.qml:79`:

```qml
onButtonClicked: if (!panel.tryOpenParamPanel("sepia", label)) panel.effectRequested("sepia")
```

és `src/picasapy/app/edit_controller_effects_mixin.py:78-86` (az `applyEffect` törzse):

```python
        self._require_active()
        key = name.casefold()
        if key not in _APPLICABLE_EFFECTS:
            raise ValueError(f"Érvénytelen effekt: {name!r}")
        self._push_undo(key)
        self._session = self._session.append_effect(
            _EFFECT_INI_NAMES.get(key, key), _EFFECT_PARAMS.get(key, ("1",))
        )
        self._save()
```

Az egyetlen írhatóság-ellenőrzés a mentésben van: `edit_controller_save_mixin.py:159` és `:226` (`if not self._check_writable_before_save():`), maga a függvény a `:265-270`-en:

```python
        assert self._ini_path is not None
        folder = self._ini_path.parent
        if is_folder_writable(folder):
            return True
        self.editSaveReadOnly.emit()
        return False
```

A jelzés szövege `src/picasapy/app/qml/PicasaPy/EditorDialogs.qml:73-76`:

```qml
            editReadOnlyDialog.ask("", qsTr(
                "This file is read only. In order to edit this file, "
                + "PicasaPy needs to copy the file's folder. Would you "
                + "like to make a copy now?")
```

és a `:77-80` (a második bekezdés, az "Igen" gomb tiltott a `:51` `yesEnabled: false` miatt): "The automatic copy is not available yet. To edit this picture, copy it to a writable folder yourself, or remove the write protection."

Az iPhoto- és Apple Photos-fogalom hiánya: `grep -rniE "iphoto|apple ?photos|Imported From|AllowReadOnly|iPhoto Library|Photos Library" src/picasapy --include="*.py" --include="*.qml"` négy találatot ad, mind más tárgyú: `index/schema.py:399` (megjegyzés), `google_photos_api.py:1` és `:29` (a Google Fotók API-ja), `app/initial_scan.py:8` (az eredeti első indítási kérdésének leírása egy docstringben).

**Igazolt eltérések.**

- **E1: nincs iPhoto/Apple Photos-kapu.** Az eredeti az iPhoto- vagy Apple Photos-könyvtár alatti mappa képein a szerkesztő műveletek előtt kérdez; nálunk a csempekattintás, a kötegelt effekt és a gyorsbillentyűk azonnal alkalmaznak (a fenti idézetek). A könyvtári mappa PicasaPy-ban Képek-mappa alatti `iPhoto Library` vagy `Photos Library` könyvtárként létezhet (Mac-ről másolt könyvtár), tehát az eset valós, bár ritka.
- **E2: a mentéskori jelzés más feltételre épül, és olyan szöveget mutat, amelyet az eredeti a sima írásvédett mappánál nem.** Az eredeti kapuja a sima írásvédett mappánál nem kérdez, és az általános szöveg elérhetetlen; a PicasaPy az `is_folder_writable` eredményére (próbafájl írása) jelez, és éppen az általános szöveget mutatja. Hogy az eredeti sima írásvédett mappában mit tesz a szerkesztéskor és a mentéskor, azt a 20. tétel méri; addig a PicasaPy jelzését nem szabad eltávolítani.

**Mit NEM tudok (megnevezett következő irányokkal).**

1. A célmappa utolsó eleme és a másolt fájlok köre (csak a kiválasztott kép, vagy a mappa összes képe), a másolt fájlok neve, és hogy a kattintás után melyik mappa és kép van kijelölve: 19. tétel; irány a T4 és a C4a.
2. A "]hidden" hívás (`[this + 0x284]` vtábla `+0x10`) szerepe, és a `0x0052e1f0`, `0x004bb3f0`, `0x0053c020` hívások szerepe a másolás előtt (0x00542643-0x00542658): T4 1. pont.
3. A sima írásvédett fájl és mappa eredeti viselkedése: 20. tétel; irány a C4b.
4. A `0x005350b0` harmadik-ötödik argumentumának (`1, 1, 1`) jelentése, a Beillesztés `0`-s ötödik argumentumával szemben (`paritas-ellenorzes.md` 856. sor): T4 1. pont.

### T3. Fejlesztői jegytörzs: az iPhoto- és Apple Photos-könyvtárban lévő képek szerkesztése előtt jelenjen meg a másolási kérdés

**Cím:** Az iPhoto- vagy Apple Photos-könyvtár alatti mappa képein a szerkesztő műveletek előtt kérdezzen a program: "Make a Copy" vagy "Cancel Edit"

**ELŐFELTÉTEL:** a 19. tétel (a "Make a Copy" célmappájának utolsó eleme, a másolt fájlok köre, a kattintás utáni nézet) lezárása a T4 szerint. Nélküle a "Make a Copy" ág nem írható meg mért érték nélkül, a kapu és a "Cancel Edit" önmagában pedig félkész funkció lenne, ezért a jegy egészben vehető fel, a 19. tétel lezárása után.

**MIT AD MA (mérve a mai kódon, 03ef17a81):** a csempekattintás, a kötegelt effekt és a gyorsbillentyűk útvonalvizsgálat nélkül alkalmaznak (`EditorEffectsTab1.qml:79`, `edit_controller_effects_mixin.py:78-86`); az iPhoto-/Apple Photos-fogalom a kódban nincs (a T2 "Nálunk" szakaszának greppje).

**Eredeti / nálunk / teendő**

| Elem | Eredeti (bináris) | Nálunk | Teendő |
|---|---|---|---|
| Feltétel | `0x00541fc0`: a mappa útvonala a `<Képek mappa>/iPhoto Library/Masters` (ha a "Masters" létezik, különben `.../Originals`) vagy a `<Képek mappa>/Photos Library/Masters` (vagy `Originals`) előtagjával kezdődik, kis- és nagybetűt nem megkülönböztetve (ASCII), útvonalhatár nélkül | nincs | tiszta függvény a feltételre (`fileops`), a Képek mappa a felhasználó Képek mappája |
| Kérdés | iPhoto: "This file belongs to iPhoto, and is read only. In order to edit this file, Picasa needs to copy the file's event out of iPhoto. Would you like to make a copy now?"; Apple Photos: ugyanez "Apple Photos" és "Photos" szavakkal; gombok: "Make a Copy" és "Cancel Edit" | nincs (a mentéskori `EditorDialogs.qml:73-76` szövege az általános, nem ez) | `ConfirmDialog` a két szöveggel, a "Picasa" szó helyén "PicasaPy" (a meglévő gyakorlat szerint, `EditorDialogs.qml:75`) |
| "Cancel Edit" | nincs módosítás, a művelet nem fut (0x00542706-0x00542740) | nincs | a lánc, a Visszavonás sor és a `.picasa.ini` változatlan |
| "Make a Copy" | a `<Képek mappa>/Picasa/Imported From iPhoto/` (illetve `.../Imported From Apple Photos/`) alá másol a `0x005350b0` fájlmásolóval; az effekt ezen a kattintáson nem fut; a célmappa utolsó eleme és a másolt fájlok köre a 19. tétel | nincs | **a 19. tétel lezárása után**; addig nem kezdhető |
| Lefedett utak | csempekattintás, kötegelt effekt (könyvtári menüág), Ctrl+Shift+B és Ctrl+Shift+E, Auto RedEye, a három Auto parancs a szerkesztő menüágában (csempeelemen át); **nem**: a szerkesztő menüág Sepia, Sharpen, Black and White, Warmify, Film Grain parancsa | egyik sem | ugyanezek, ugyanígy: a menü szerkesztő-ágának öt közvetlen hívású parancsa nem kérdez (paritás) |
| `AllowReadOnlyEdits` | HKCU, DWORD, nem nulla kikapcsolja a kaput csempekattintásnál és Auto RedEye-nál | nincs | nincs teendő: a kulcsot az eredeti sem állítja be sehol (nincs író), a PicasaPynak nincs ilyen beállítása |

**Nem szabad:** a mentéskori `editSaveReadOnly` jelzést eltávolítani vagy átírni, amíg a 20. tétel nincs mérve; a sima írásvédett mappa (nem könyvtár) viselkedését megváltoztatni; a kapuhoz hálózati vagy attribútum-vizsgálatot adni (az eredeti nem vizsgál); az általános "This file is read only..." szöveget a kapu elé kitenni (az eredetiben elérhetetlen).

**Kész, ha:**

- [ ] Egy `<Képek mappa>/iPhoto Library/Masters/Esemeny1/` alatti képen a Sepia csempe valódi egérkattintása után megjelenik az iPhoto-szöveg a két gombbal; a teszt valódi kattintással fut (nem metódushívással), és a szöveget, a gombfeliratokat méri.
- [ ] Ugyanez az `Originals` alapmappával (ha nincs "Masters"), az Apple Photos-könyvtárral (`Photos Library`), és kis- és nagybetű eltéréssel (`IPHOTO LIBRARY/masters`).
- [ ] "Cancel Edit" után a `filters=` lánc és a Visszavonás sor változatlan, és az effekt nem került a képre.
- [ ] Negatív kontroll: egy közönséges, írásvédett és egy írható mappában a kérdés nem jelenik meg.
- [ ] A kötegelt effekt (könyvtári nézet) és a Ctrl+Shift+B/E ugyanígy kérdez; a szerkesztő menüágának Sepia/Sharpen/Black and White/Warmify/Film Grain parancsa nem kérdez, a három Auto parancs kérdez.
- [ ] Vizuális ellenőrzés: C4a felvételei (eredeti) és a PicasaPy képe a kérdésről, egymás mellett; ahol a teszt csak számol, a jegy kimondja, hogy a vizuális egyezést nem méri.
- [ ] A "Make a Copy" ág a 19. tétel mért értékeivel: célmappa, fájlnevek, a kattintás utáni nézet, és az effekt nem fut ezen a kattintáson.

**Bizonyítottsági fok:** erős (statikus, a T2 két független útja); futásmérés NINCS (C4a).

**Érintett fájlok:** `fileops/` (új feltételfüggvény), `EditorEffectsTab1.qml`, `edit_controller_effects_mixin.py`, `batch_effect_controller.py`, `MainKeyboardShortcuts.qml`, `MainMenuBar.qml`, `EditorDialogs.qml` (csak olvasva, a mentéskori jelzés marad).

### T4. Kutatási jegytörzs: a "Make a Copy" részletei és a sima írásvédett fájl eredeti viselkedése (19. és 20. tétel)

**MIT AD MA:** a kapu feltétele és a két gomb hatása kiolvasva (T2); a célmappa utolsó eleme, a másolt fájlok köre, a kattintás utáni nézet és a sima írásvédett fájl eredeti viselkedése nincs.

**NYITOTT (megnevezett következő irányok):**

1. **19. tétel, a dekompiláció útja.** Ghidra-kör a `0x009a3c70`, `0x009a38a0`, `0x009a3db0`, `0x009a37b0`, `0x0049ff10`, `0x00408390` (az útvonalszerkezet mezői: `+0x208`, `+0x410`, `+0x618`, `+0x620`, `+0x820`, `+0x828`), a `0x005350b0` (az argumentumok jelentése és a visszatérési értéke), a `0x007164b0`, `0x007166c0` és a "]hidden" hívás célja (`[this + 0x284]` vtábla `+0x10`), valamint a `0x0052e1f0`, `0x004bb3f0`, `0x0053c020` függvényekre.
2. **19. tétel, a mérés útja (C4a).** Nem kell hozzá fájlattribútum: elég, hogy a mintakép a `<Képek mappa>\iPhoto Library\Masters\Esemeny1\` alatt álljon; a mintakészlet elhelyezéséhez a végrehajtónak kell egy útvonal-kulcs.
3. **20. tétel (C4b).** A sima írásvédett fájl mérése a végrehajtó új lépését igényli (`csak_olvashato`), mert ma nem tud fájlattribútumot állítani.

**Kész, ha:** a lap kimondja a célmappa teljes útját és a másolt fájlok nevét és körét mért képkockával (19. tétel), valamint a sima írásvédett fájl eredeti viselkedését (20. tétel), vagy mindkettőre a dekompilációból kiolvasott, megnevezett eredményt; ezután a T3 előfeltétele teljesül.

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
| 12 | Írásvédett kép: a kapu megléte és helye | LEZÁRVA | `0x006021d0` → `0x00541fc0` a végpont előtt (T2). A kapu nem írásvédettséget, hanem iPhoto-/Apple Photos-könyvtári mappát vizsgál (13. tétel). Nálunk nincs ilyen kapu: eltérés E1, T3 |
| 13 | A kapu feltétele, a két gomb hatása, a lefedett utak | LEZÁRVA, eltéréssel | a feltétel az útvonal-előtag (`0x0047cea0` → `0x00987030`, `0x0047cfc0`, 0x00542109-0x00542161), nem fájlattribútum; "Cancel Edit" és "Make a Copy" után a művelet nem fut (0x00542740, 0x00542702, a három hívó `test eax, eax`); az általános szöveg elérhetetlen (két ugrás vezet a kérdéshez, 64 elágazás elemezve); az `AllowReadOnlyEdits` csak a `0x006021d0`-ban és a `0x00602100`-ban olvasott (két hivatkozás); a menü szerkesztő-ágának öt parancsa kapu nélkül fut. Bájtpásztázás: tizenhárom `call`, nincs `jmp` és vtábla-mutató. Nálunk: E1 és E2, T3 |
| 14 | Paraméteres effekt: Mégse, újranyitás, értékek megőrzése | BLOKKOLT | a sztring-hivatkozásokból és a kezelőkből nem olvasható ki: a panelfelépítő `0x00750ff0` (1702 bájt) és hívottja, a `0x006ac980` (1510 bájt, nincs sztringje) az első jelölt a kezdőértékek forrására; a `0x007518e0` csak elrejti a vezérlőket (hívásai `0x009c2fc0` névkeresések). Kell: C2 Colab-feladat (a mi gépünk, tulajdonosi kérés nincs), vagy Ghidra a két függvényre. Ide tartozik a csúszka dupla kattintásos visszaállítása (C2 7. lépés) |
| 15 | Paraméteres effekt ismétlése, Undo/Redo felirat és lépésszám ismétlés után | BLOKKOLT | a felirat szövege ismert (`CFilterStackUI::undoname` "Undo ", `redoname` "Redo "; hivatkozza a `0x007533b0`), a lépésszám és a paraméteres ismétlés viselkedése nincs kiolvasva (a `0x00750ff0` ága). Kell: C2 Colab-feladat |
| 16 | Alkalmaz utáni `.picasa.ini`, Mentés lemezre, Undo/Redo mentés előtt és után, indexhatás | BLOKKOLT | az ini írásának helye nincs kiolvasva: a `0x007533b0` sztringjei a Mentés gombot (`editpanel/writetodisk`, `CFilterStackUI::save`) és az Undo/Redo feliratokat érintik, a lemezre írás helye nem látszik belőlük. Kell: C3 Colab-feladat (`picasa_ini`, `kepmappa`, `db3` kimenet; a végrehajtó mindhármat tudja) |
| 17 | A csempegrafikák és az effektalgoritmusok képpont-paritása | HATÓKÖRÖN KÍVÜL | a lap fejléce (3. sor) külön kutatásra utalja; a render-sáv paritás-jegyei viszik (`filterdesc-registry.md`, #626) |
| 18 | A PicasaPy hatodik, "Legacy Effects" füle | HATÓKÖRÖN KÍVÜL | saját kiegészítés (`EditorTabBar.qml:136-152`), az eredetiben nincs; a szerkesztő fülsávja a tulajdonosi döntés szerint hét fül (`docs/decisions/szerkeszto-bal-panel.md`, 2026-08-15) |
| 19 | A "Make a Copy" célmappájának utolsó eleme, a másolt fájlok köre és neve, a kattintás utáni nézet | BLOKKOLT | a célmappa szülője kiolvasva (`<Képek mappa>/Picasa/Imported From iPhoto/` illetve `.../Imported From Apple Photos/`), az utolsó elemet és a fájlkört az útvonalszerkezet mezői (`+0x410`, `+0x618`, `+0x820`) adják, ezek nincsenek végigolvasva. Kell: T4 1. és 2. pontja (célzott dekompiláció, vagy C4a mérés, amelyhez fájlattribútum nem kell, csak a mintakép helye). Kitől: a mi gépezetünktől |
| 20 | Sima írásvédett fájl vagy mappa: mit tesz az eredeti szerkesztéskor és mentéskor | BLOKKOLT | a kapu nem vizsgálja (13. tétel), a mentési hiba szövege és a fájl állapota nincs kiolvasva. Kell: C4b (a végrehajtó új `csak_olvashato` lépése). Kitől: a mi gépezetünktől |

**Nyitott kérdések: 0 nyílt · 13 lezárva · 5 blokkolt · 2 hatókörön kívül · 0 "csak nyitva".**

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

**C4a. iPhoto-könyvtári kép: a kapu és a "Make a Copy" (T2 megerősítése, 19. tétel).** Fájlattribútum nem kell hozzá, csak a hely számít: a mintaképek a `<Képek mappa>\iPhoto Library\Masters\Esemeny1\` alatt állnak (`kep1.jpg`, `kep2.jpg`), két további kép a közönséges `<Képek mappa>\Esemeny2\` alatt; a Picasa mindkét mappát beolvassa. A mintakészlet elhelyezéséhez a végrehajtónak kell egy útvonal-kulcs. Kimenet: `kepernyokep`, `allapot`, `picasa_ini`, `kepmappa`.

1. Szerkesztőben `Esemeny1/kep1.jpg`, a Sepia csempe (137, 181) kattintása. Képkocka: megjelenik-e a kérdés, a szöveg betűre pontosan, a két gomb felirata; a `picasa_ini` `filters=` sora. (Az `AllowReadOnlyEdits` kulcs nincs beállítva: a T2 szerint ekkor a kapu él.)
2. "Cancel Edit". Képkocka; változott-e a kép, az Undo sor és a `filters=`; a mappa tartalma (`kepmappa`).
3. Újra Sepia, "Make a Copy". Képkocka közvetlenül utána és egy másodperc múlva. Rögzítendő: a létrejött mappa teljes útja és neve, a másolt fájlok neve és száma (csak `kep1`, vagy `kep1` és `kep2`), az `Esemeny1` változatlansága (méret, dátum), melyik mappa és melyik kép van kijelölve, az Undo sor, a `filters=` az eredetin és a másolaton (19. tétel).
4. A másolt képen Sepia: kérdez-e (a T2 szerint nem), hat-e.
5. Negatív kontroll: `Esemeny2/kep1.jpg`, Sepia: nem kérdez, alkalmaz.
6. Kontroll: `<Képek mappa>\iPhoto Library\Originals\Esemeny3\` minta (Masters mappa nélkül), Sepia: kérdez-e (az "Originals" ág).
7. Kontroll: Ctrl+Shift+B az `Esemeny1` mappa kijelölt képén (könyvtári nézet) és a szerkesztőben nyitott képen; Kép ▸ Csoportos szerkesztés ▸ Sepia a szerkesztőben (a T2 szerint nem kérdez) és ▸ Auto Contrast (a T2 szerint kérdez).
8. Kiértékelés: a T2 megerősített, ha az 1. lépésben a kérdés megjelenik, az 5.-ben nem; cáfolt, ha az 5.-ben is megjelenik (akkor van más feltétel) vagy az 1.-ben nem.

**C4b. Sima írásvédett fájl és mappa (20. tétel).** Előfeltétel: a végrehajtó új `csak_olvashato` lépése (ma nem tud fájlattribútumot állítani). Közönséges mappa, `kep1.jpg` csak olvasható attribútummal: (1) Sepia csempe: kérdez-e (a T2 szerint nem); (2) módosul-e a kép a szerkesztőben, mit mutat az Undo sor; (3) Mentés (`editpanel/writetodisk`) vagy lépés a következő képre: milyen szöveg jelenik meg (képkocka), a fájl és a `picasa_ini` állapota; (4) ugyanez egy olyan mappában, ahová a mappa jogai tiltják az írást. Kiértékelés: a T3 "Nem szabad" pontja a mentéskori jelzésről itt dől el.

### 5. Amit KIZÁRTAM

- Az első kör "a menü csak navigál, nem alkalmaz" állítását (D1): az öt névvel hívó ág a `0x005f8520`-ra fut, ami a csempe végpontja. Ez az út zárva, ne járja újra senki.
- Azt, hogy a `0x00579330` navigáló függvény: 37 bájtos feltétel-őr.
- Azt, hogy az effekt-paraméterpanelen az Alaphelyzet gomb "hiánya a PicasaPy forrásában nem bizonyít semmit": az eredeti erőforrásában is hiányzik, két független úton (erőforrásfájl és felvétel).
- Azt a feltevést, hogy a #7123 tesztje az eredeti viselkedést rögzítette: a teszt az akkor nyitott kérdést ("kijelöl vagy alkalmaz is") a nem-alkalmazás irányába zárta.
- Azt, hogy a Copy All Effects többképes ágához új felvétel kell: a #6861 valódi menükattintásos teszt az eredeti mért Info-szövegével egyezik.
- Azt, hogy az írásvédett-kapu fájlattribútumot, mappa-írhatóságot vagy hálózati helyet vizsgál: a teljes függvény elolvasva, az egyetlen feltétel az útvonal-előtag (T2). Ez az első kör és a `paritas-ellenorzes-archiv-2.md` 3038. sorának olvasatát megdönti.
- Azt, hogy az általános "This file is read only..." szöveg a Picasában valaha megjelenik a kapun át: a kérdés-szakaszhoz csak az iPhoto- és Apple Photos-teszt igaz ága vezet, a szöveg egyetlen hivatkozása a kapuban áll.
- Azt, hogy a fájlattribútum-állító végrehajtó-lépés a T2 megerősítésének előfeltétele: nem az, elég a mintakép helye (C4a); a `csak_olvashato` lépés csak a 20. tételhez kell (C4b).
