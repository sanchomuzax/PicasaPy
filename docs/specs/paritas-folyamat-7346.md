# #7346: A három Effektek lap folyamata

Vizsgálati tárgy: Picasa 3.9.141.259 és a munkafa jelenlegi PicasaPy-forrása. Ez a lap az effektválasztás, paraméterezés, alkalmazás, elvetés, ismétlés és lánc folyamatait kapcsolja össze. A csempegrafikák és az effektalgoritmusok képpont-paritása külön kutatás.

## Következtetés

Az eredeti három Effektek lapjának 36 csempéje és mind a kilenc Shift-változata megvan a PicasaPyban; az eredeti futtatott felvételek a paraméterpanel alapfolyamatát is részben rögzítik. Két jelenlegi forráseltérés igazolható: a Kép ▸ Csoportos szerkesztés parancsai a PicasaPyban csak a fület választják ki, az eredeti pedig a célvezérlőt is; továbbá a csempék kék jelvényének feltétele a két programban mást jelent. A teljes futásidejű paritás nyitott, mert nem áll rendelkezésre friss, párhuzamos Picasa 3.9/PicasaPy mérés az ismétlésről, megjegyzett paraméterállapotról, mentett képfájlról és visszavonás/újra állapotról.

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
- Ghidra-kör nem szükséges: a nyitott pontok futásidejű mérések, az eredeti csempe- és menüút feloldásához a célzott disassembly és a korábbi mérések elegendők.

## Módosított fájlok

- docs/specs/paritas-folyamat-7346.md: a csempék, menük, paraméterpanel és mentési folyamat összevetése; két forrásból alátámasztott eltérés; nyitott Colab-lépések.
