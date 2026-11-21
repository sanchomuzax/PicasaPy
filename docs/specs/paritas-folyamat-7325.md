# A Beállítások ablak (Eszközök ▸ Beállítások) teljes folyamata az eredeti Picasával összevetve: belépési pontok, ablak, alapértékek, hatás

## Hatókör és bizonyosság

Ez a lap a #7325 kérdését dolgozza fel. A vizsgált eredeti `Picasa3.exe` SHA-256 értéke `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`, verziója 3.9.141.259; a helyi másolat bitre egyezik az indexelttel. A fájlt csak statikusan vizsgáltam (capstone, `paszta.py` a teljes `.text` pásztázásához), nem futtattam, nem másoltam a repóba.

**A lap NEM ismétli a fülenkénti összevetést.** A 8 fül mezői, felirata, kulcsa és alapértéke a [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) 871-1352. sorában van (#5470, #5483, #5489, #5516, #5906), a 39 kulcs életciklusa a 460-560. sorban (#6062), a nyelvválasztó a 635. szakasztól (#3553). Ez a lap a **folyamatot** adja: ki nyitja az ablakot, mit jegyez meg, mit ír az OK, és mi történik **az OK után**, azonnal. Ez utóbbi eddig sehol nem volt leírva, és több korábbi `NINCS MEG` sort megválaszol.

**Futtatott felvételek.** `grep -rn "job-[0-9]" docs/specs/` az Opciókra három felvételt ad: job-190 (az ablak 584 x 345 px, rögzített méret), job-237 és job-238 (friss profil fülsora, `Web Albums` cím). Egyik sem méri az **OK utáni hatást**, ezért minden hatásállítás statikus. Ahol futtatott mérés kell, a 6. szakasz pontos Colab-lépéssort ad.

**Összesített bizonyítottság: erős** a belépési pontokra, a megjegyzett lapra, az OK és a Mégse szerkezetére és a `disposepreviews` viselkedésére (két független statikus út, lásd az 5. szakaszt); **feltételes** a fájltípus-váltás, az importcél-felvétel és az arcküszöb-újratöltés pontos jelentésére (a hívott belső függvények törzse nincs dekompilálva).

## 0. Bizonyítási terv és cím-atlasz

Cím-atlasz (`atlasz_keres.py 0x00559150 0x006e3990 0x006e1100 0x006e0cb0`), kivonat: a `0x00559150` menüépítőt a [picasa-menusor-csoportok.md](picasa-menusor-csoportok.md) és a [picasa-menu-leltar.md](picasa-menu-leltar.md) írja le; a `0x006e3990` mentőt eddig csak kulcslistaként a [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md), a [paritas-folyamat-7289.md](paritas-folyamat-7289.md) és a nyomtatási lapok említették; a `0x005cf5b0` megnyitót **egyetlen lap sem említi**.

1. **Kérdés:** ki nyitja a Beállítások ablakot, mit jegyez meg, mit ír az OK és mi fut le utána, mi a Mégse hatása, és mindez hol tér el a PicasaPy-tól.
2. **Vizsgálatok** (szó szerint): `scan_imm.py 0x9cab` (a parancsazonosító összes hivatkozása a teljes `.text`-ben); `scan_imm.py 0x5cf5b0` (a megnyitó hívói); `scan_imm.py 0xc95630` (a `disposepreviews` sztring összes kódbeli hivatkozása); `picasa_dis.py 0x005cf5b0 2564`, `0x006e3990 7507`, `0x006e1100 9494`, `0x006e36e0 270`; `sqlite3 ... string_xrefs` a 37 beállításkulcsra; a rtti-vtábla `COptionsDialog::vftable` 87-90. helye.
3. **Igazolná / cáfolná:** a megnyitó hívó-szerkezete és a kezelő-tábla a `0x9cab` -> `0x005cbddd` leképezést; a `disposepreviews` kilépéskori olvasója cáfolná az OK-ra szóló ürítést (a teljes `.text` pásztázás ilyet nem talált).
4. **Amit csak mérés dönt el:** a 6. szakasz Colab-lépéssorai.

## 1. Az eredeti menete

### 1.1 Belépési pontok

| # | Belépési pont | Bináris bizonyíték |
|---|---|---|
| 1 | **Eszközök ▸ Options...** (`eMenuTools::ID_TOOLS_OPTIONS`, felirat `&Options...`). Egyetlen menüsor, feltétel nélküli. Gyorsbillentyű **nincs**. | A menüépítő `0x00559150` rekordja: `eMenuTools::ID_TOOLS_OPTIONS` `0x00c8df30`, `&Options...` `0x00c8df50`, parancs `mov word ptr [0xd6e9ae], 0x9cab` (`0x0055c9c5`). A főablak-diszpécser `0x005cb990` a `0x9c42`-`0x9d3f` tartományt bájt-táblából (`0x005cdb34`, a `0x9cab` indexe `0x69`, értéke 36) és dword-táblából (`0x005cd9fc`, 36. elem `0x005cbddd`) osztja; a kezelő: `push 1; push -1; push ebx; xor ecx, ecx; call 0x5cf5b0` (`0x005cbddd`-`0x005cbde4`). A `0x9cab` a teljes `.text`-ben csak két helyen szerepel: a menürekordban és az `EnableMenuItem` hívásban (lásd 3. sor). Az Eszközök menü a menüsor 7. menüje (`menuk.json`: `menuk[6]`, `tetelek[12]`). |
| 2 | **Webalbum-szinkron megerősítő ablak, `change` gombja**: az ablak a 6. fülön (Web Albums) nyitja az Opciókat, a fül nem mentődik a megnyitó 3. paraméterével (0). A szolgáltatás megszűnt. | A `0x007df2b0` (280 b) a `change` eseménynevet hasonlítja (`0x00cb9468`), majd `push 0; push 6; push [ebx+0xc8]; call 0x5cf5b0` (`0x007df340`-`0x007df347`); az ablak sztringjei: `confirmsync::public`, `confirmsync::unlisted`, `confirmsync::signinRequired`, `Public on the web`, `Limited, anyone with the link`. A megnyitónak ez a **másik egyetlen** hívója. |
| 3 | **Menüsor-zár**: a `CThumbUI` 5. vtábla-helye (`0x00c9068c` -> `0x007615d0`) (az első argumentum nulla = zárolás, a számláló `[this+0x3230]` nő; nem nulla = feloldás, a számláló csökken) a menüsor első 7 almenüjének minden tételét szürkére állítja (`EnableMenuItem`, `MF_BYPOSITION`), és zároláskor, ha a második argumentum igaz, az **Opciókat parancsazonosító szerint visszaengedélyezi** (`push 0; push 0x9cab`, `0x00761694`-`0x0076169c`). Vagyis zárolt menüsornál az Opciók az egyetlen elérhető tétel. A zároló hívói **NINCS MEG**. | `0x007615d0`: számláló `[this+0x3230]`, `GetMenu`/`GetSubMenu`/`GetMenuItemCount`/`EnableMenuItem` a `0x00c408dc`/`0x00c408cc`/`0x00c408c4`/`0x00c40818` import-helyeken (a négy IAT-bejegyzés értéke egyezik az `EnableMenuItem` stb. név-címeivel). |
| 4 | Más belépési pont **nincs**: se eszköztár-gomb, se helyi menü, se gyorsbillentyű, se közvetlen `WM_COMMAND` küldés (a `0x9cab` immediate csak a fenti két helyen áll), se kódba írt billentyűág. | Teljes `.text` pásztázás a `0x9cab` és a `0x5cf5b0` értékre; a gyorsbillentyű-lap az `Options` szóra nem ad tételt, a `CreateAcceleratorTableA` egyetlen hívója egy üres OLE-tábla ([picasa-gyorsbillentyuk.md](picasa-gyorsbillentyuk.md) 2509. sor). |

### 1.2 Az ablak és a megjegyzett állapot

A megnyitó a **`0x005cf5b0`** (2564 b); paraméterei: főablak, fül (`-1` = az utolsó), mentési jelző (a menü: `1`, a szinkron-ablak: `0`).

- **Felépítés.** A `0x005c6830` konstruktor az `options` sablont (`0x00c94e28`, a `runtime/options.fen`) tölti; vtábla `COptionsDialog` (`0x00c9a404`).
- **Kezdőfül.** A fül `-1`-nél a megnyitó a `Preferences\LastUsedOptionsPage` értéket olvassa (`0x00c95600`, olvasás `0x005cf5d6`-`0x005cf608`, **alapérték 0** = az első fül). Az eredő fülindexet egy 8 bájtos érték-objektumba (vtábla `0x00c8b714`) csomagolja, és a `0x008d3060` a `tabs` nevű vezérlő értékének állítja (`0x005cf671`-`0x005cf6bf`). A fülindex feltehetően 0-alapú (General 0, E-Mail 1, File Types 2, Slideshow 3, Printing 4, Network 5, Web Albums 6, Name Tags 7): ezt a szinkron-ablak hatos értéke (a webalbum-szinkron beállításait nyitja) támasztja alá; a pontos leképezést az M2 mérés (`LastUsedOptionsPage`) rögzíti. **Feltételes.**
- **Megjegyzés.** A `LastUsedOptionsPage` az ablak **minden lezárásakor** mentődik, OK és Mégse esetén egyaránt: a `COptionsDialog` destruktora (`0x006e36e0`) a `tabs` vezérlő aktuális értékét kiírja (`0x006e373d`-`0x006e3767`), és a megnyitó is megteszi, ha a 3. paraméter nem nulla (`0x005cf708`-`0x005cf727`, a `0x006e5970` adja az aktuális fület). A `LastUsedOptionsPage` kizárólag a `0x005cf5b0` és a `0x006e36e0` függvényben szerepel (sztring-xref).
- **Modalitás és eredmény.** Az ablak a főablak kezelőjével nyílik modálisan; az eredmény 0 = OK, 1 = Mégse, 2 = az ablak nem épült fel (`0x005cf6e3`). `test esi, esi; jne 0x5cff66` (`0x005cf72c`-`0x005cf736`): nem nulla eredménynél semmi nem fut le.
- **Kezdő pillanatkép** (az OK utáni összehasonlításhoz): a `0x006e1100` a 12 fájltípus-kapcsoló kezdőállapotát a `[dialog+0xcc]` bájt-tömbbe (`0x006e1bc0`-`0x006e1bf3`, a nevek táblája `0x00c7e1f0`), az importcél eredeti szövegét a `[dialog+0xc8]`-ba, a `ReportStats` "nincs tárolva" jelzőjét a `[dialog+0xd8]`-ba teszi.

### 1.3 Az OK: mit ír (két réteg)

Az eredménykezelő `0x008d2720`: 0 eredménynél a `COptionsDialog` vtábla 89. helyét hívja (`0x00c9a568` -> `0x006e3990`), 1 eredménynél a 90. helyet (`0x00c9a56c` -> `0x00b0d990`, egyetlen `ret`). Az OK tehát ír, a Mégse **semmit nem ír** (a `LastUsedOptionsPage` kivételével, az a destruktorban mentődik).

**1. réteg, általános mentés** (új lelet). A `0x006e3990` legelső művelete a `call 0x9a58e0` (`0x006e39af`): a párbeszéd "kötött vezérlőnevek" listáján (`[dialog+0xa8]`, darabszám `[dialog+0xac] / 2`) végigmegy, és mindegyikre a `0x009a5b30`-at hívja. Ez megkeresi a vezérlőt név szerint (vtábla `+0xec`), kiolvassa az értékét (`+0xc`), és kiírja a `Preferences\<vezérlőnév>` helyre (`0x009a5b9e`-`0x009a5bc4`). A listát a `0x006e1100` tölti a `0x009a5c10` segéddel (hívások: `0x006e13f0`, `0x006e16f3`, `0x006e1cd2`, `0x006e1f94`, `0x006e2e2e`):

- **Általános fül, 8 név** (`0x006e135a`-`0x006e1392`), alapértékekkel (`0x006e1398`-`0x006e13dc`): `UITransitions` 1, `ShowTooltips` 1, `SingleClickExit` 0, `disposepreviews` 0, `DoNotConfirmDeleteFromDisk` 0, `DoNotConfirmRemoveFromAlbum` 0, `autoexclude` 1, `usagestats` (a `ReportStats == 1` eredménye);
- **fájltípusok, 12 név** (a `0x00c7e1f0` tábla): `SupportTIF`, `SupportWEBP`, `SupportBMP`, `SupportGIF`, `SupportPSD`, `SupportPNG`, `SupportRAW`, `SupportMovies`, `SupportQuicktime`, `SupportAudio`, `SupportHTTP`, `SupportTGA` (a `SupportAudio` és a `SupportHTTP` vezérlő nélküli, a `0x009a5b30` ilyenkor hamisat ad vissza és kihagyja);
- **diavetítés, 2 név:** `LoopSlideshow`, `PlayMP3Tracks` (`0x006e1f74`-`0x006e1f94`).

Ez a lelet megválaszolja a [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) #6062 táblájának azon sorait, ahol az íróút `NINCS MEG` volt (`UITransitions`, `ShowTooltips`, `SingleClickExit`, `disposepreviews`, `autoexclude`, `LoopSlideshow`, `PlayMP3Tracks`, `SupportRAW`, `SupportTGA`, a `DoNotConfirm*` kulcsok vezérlő-oldali írása): **az íróút az Opciók OK-ja**, a `0x006e39af` -> `0x009a5b30` láncon, minden elfogadáskor, módosítástól függetlenül.

**2. réteg, egyedi mentők** a `0x006e3990` törzsében (a kulcsok és címek fülenként a [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) 13. szakaszában): `ReportStats` (a kulcs csak akkor íródik, ha a jelölő be van kapcsolva, **vagy** a kulcs korábban is tárolt volt: `0x006e3ab4`-`0x006e3adc`; a hiányzó kulcs jelölés nélkül hiányzó marad), `AutoUpgradeCheck`/`AutoUpgradeAsk`, a nyelv (`ytHLocal::langchange`, megerősítő kérdéssel `0x006e3c15`-`0x006e3cf0`), `AcquirePath` (**csak ha** az importcél szövege eltér a kezdőértéktől: a `0x006e5740` `0x006e3d1d`-nél), `EmailPrepType`/`DoNotPromptForEmailPref`/`EmailExportSize`, `MP3SlideshowPath`, `PrinterQuality`, `PrintResamplerQuality`, `PrintProxyPreview`, `PrintSize%d`, a hálózati kulcsok és a `LogLevel`, `PWA*`, az arcfelismerő kulcsok. A felhasználónak látszó üzenet a `0x006e3990` törzsében **egyetlen**: a nyelvváltás megerősítése (`CGeneralPrefsPage::LangChange`, `0x006e3cab`); a `0x00401900` írások után nincs hibaág.

### 1.4 Az OK után: azonnali hatások (új lelet, a megnyitó `0x005cf772`-`0x005cff6d` szakasza)

A mentés után, a megnyitó még ugyanabban a hívásban, ebben a sorrendben:

| Sorrend | Feltétel | Hatás | Cím | Fok |
|---|---|---|---|---|
| a | a főablak `[ebp+0xeb0]` mutatója nem üres | a mutatott objektumon jelzőbit-állítás (`+8` `|= 2`, `+0x290` bájt = 1); jelentése **NINCS MEG** | `0x005cf73c`-`0x005cf76b` | a cím és az írás erős, a jelentés nyitott |
| b | az importcél szövege változott (`0x006e5740`) | az új célmappa **felvétele a mappatárba**: `0x004ef8f0` (keresés; `9` = nincs találat), `0x004f1e50` (kis-nagybetűtlen útvonal-összehasonlítás egy listában), majd `0x004f6a20` (a `scanlist.txt` kezelő, [picasa-mappakezelo.md](picasa-mappakezelo.md) 11. szakasz), és a `0x004f5960` (`watchedfolders.txt`), `0x004f5d90` (`frexcludefolders.txt`) újraírása. Hiba esetén a megnyitó a hibakódot adja vissza (a menükezelő eldobja, **nincs üzenet**). A felvétel pontos módja (egyszeri vagy folyamatos figyelés) **NINCS MEG**. | `0x005cf772`-`0x005cfaf1` | feltételes |
| c | mindig | a `SingleClickExit` kiolvasása (alapérték 0) az **élő** jelzőbe: `[ebp+0x31ac]` | `0x005cfafc`-`0x005cfb27` | erős |
| d | a 12 fájltípus-kapcsoló összevetése a kezdő pillanatképpel | minden megváltozott típusra a szűrő frissítése (`0x004fadb0`, típus-kódokkal, a 30 ágú táblát a [picasa-mappakezelo.md](picasa-mappakezelo.md) 2521. sora írja); ha volt **letiltott** típus: `0x004fb9c0`; ha volt **engedélyezett**: `0x004efb40`; végül mindig `0x004ebe40`. A film-típusnál a `searchoptions/moviesearch` elem frissítése is (`0x005d4a90`, `SupportMovies`). A `0x004fb9c0` a mappatár rekordjain megy végig (a rekord `+0x18` típusa a `2, 3, 6-0x12, 0x15-0x18, 0x1a, 0x1b-0x1d, 0x1f` képtípus-kódok egyike, `0x3e9` kivételével), és az `0x004e2cc0` vizsgálat igaz eredményénél a rekordot kiveszi (`0x004f9450`, a számláló `[this+0x4d4]` csökken). **Feltételes olvasat:** a letiltott típusokra az OK után azonnal fut egy rekord-kivételi menet, nem a következő pásztázásra vár; az `0x004e2cc0` vizsgálat jelentése és az engedélyezésnél hívott `0x004efb40` jelentése **NINCS MEG**. | `0x005cfb50`-`0x005cfd8f` | feltételes |
| e | a `thumbui/printpanel` elem létezik (`0x005cfda3`-`0x005cfdad`) és a `+0x20c` bájtja nulla (`0x005cfdb1`) | a gyorsméret-gombok újracímkézése (`0x00743700`) és a panel frissítése (`0x00745980`); a köteg végén az egérkurzor nyílra áll (`LoadCursorA(0, 0x7f00)`, `SetCursor`) | `0x005cfd94`-`0x005cfde5` | erős a szerkezetre; a `+0x20c` bájt jelentése nyitott |
| f | `disposepreviews` nem nulla | **a kapcsoló visszaáll nullára** (`0x00401900`, érték 0), és a két memóriabeli bélyegképtár (`[könyvtár+0x22d0]`, `[könyvtár+0x237c]`) azonnal újrainicializálódik (`0x006b8710` kétszer; ugyanez a pár a Ctrl+Shift+U parancs, [picasa-gyorsbillentyuk.md](picasa-gyorsbillentyuk.md) 959. sor). A `0x006b8710` törzsében nincs fájlkezelő API-hívás; a lemezes cache törlése **NINCS MEG**. | `0x005cfdeb`-`0x005cfe48` | erős |
| g | mindig | az arcküszöbök **újratöltése** a `Preferences`-ből (`0x0048aab0`, mentés jelző 0: `FRSuggestionThreshold`, `FRSuggestionSingleThreshold`, `FRSortThreshold`, `FRRecommendIncludeLimit`, `FRRecommendShowLimit`, /100 skálával), majd a `0x00487590` (3932 b) futtatása és az arcpanel jelzőjének beállítása (`[ebp+0x2c0]+0x166`). A `0x0048aab0` **mindig `0xf4240`-et ad vissza** (`0x0048ae7e`), ezért a `cmp eax, 0xf4240` ág (`0x005cfe74`) mindig teljesül. A `0x00487590` jelentése **NINCS MEG**. | `0x005cfe67`-`0x005cfeef` | feltételes |
| h | a `BgFaceDetectThread` értéke változott (a megnyitás előtti és a mostani érték eltér, `0x005cff39`) | az arcfelismerő objektum (`[[ebp+0x2bc]+0x2db4]`) `+0x74` bájtja az új értékre áll; bekapcsolásnál `0x0047bee0` (munka sorba állítása, [picasa-arcfelismeres-kutatasi-naplo.md](picasa-arcfelismeres-kutatasi-naplo.md) 3414. sor: producer-jelölt), kikapcsolásnál `0x0047c160(0)` | `0x005cfef6`-`0x005cff61` | erős a szerkezetre, a két hívott függvény jelentése feltételes |
| i | **mindig**, OK és Mégse esetén is | a főablak nézetfrissítése (`0x0065b840(főablak, 0, 0, 1)`; a függvény sztringjei: `searchcontainer/searchbutton`, `searchcontainer/searchclr`) | `0x005cff66`-`0x005cff6d` | erős a hívásra, a pontos hatás feltételes |

Az e és a g sorban egy köteg-számláló (`[0xd6793c]`, `0x005cfdc5`, `0x005cfe8b`) és a `0x0097e4c0` hívás fogja össze a felületfrissítést (a mappakezelő törlési lánca ugyanezt a mintát használja, [picasa-mappakezelo.md](picasa-mappakezelo.md) 15.3). A megnyitó saját sztringjei között állapotsor-szöveg nincs (csak a `Preferences` kulcsok és a `searchoptions/moviesearch`, `thumbui/printpanel` nevek); a hívott függvények törzsét ebből a szempontból nem vizsgáltam.

### 1.5 Mégse, hiba, visszavonás

- **Mégse / bezárás:** az 1. és a 2. réteg nem fut, a b-h sorok sem; csak az i sor (nézetfrissítés) és a `LastUsedOptionsPage` mentése. (`0x008d2720` 1-es ág, `0x00b0d990` üres rutin; `jne 0x5cff66`.)
- **Hiba:** az ablak felépítési hibája (2-es eredmény) mellékhatás nélkül zár. A Preferences-írások (`0x00401900`) visszatérési értékét sem a `0x006e3990`, sem a megnyitó nem vizsgálja; az importcél-felvétel hibakódját a menükezelő eldobja (`0x005cbde9`). Hálózati vagy írásvédett helyre vonatkozó külön ág, üzenet vagy érvényesség-vizsgálat az Opciók láncában **nincs** (a `0x006e3990` és a `0x005cf5b0` sztringjei között ilyen nincs).
- **Visszavonás:** az Opcióknak nincs visszavonási története; az OK után az eredeti értékek csak újabb Opciók-kör útján állíthatók vissza.

## 2. Összevetés: Eredeti | Nálunk | Teendő

A "Nálunk" oszlop a munkafa (`research/7325-claude`, `main` 6afb212f3) szó szerinti kódsorait idézi.

| # | Eredeti (bináris cím) | Nálunk (fájl:sor, idézet) | Teendő |
|---|---|---|---|
| 1 | **Menü-belépés:** Eszközök ▸ Options..., `0x9cab` -> `0x005cbddd` -> `0x005cf5b0(-1)`; gyorsbillentyű nincs. | `PicasaToolsMenu.qml:435-438`: `MenuItem { objectName: "menuToolsOptions"; text: qsTr("&Options..."); onTriggered: bar.optionsRequested() }`; `MainMenuBar.qml:293`: `onOptionsRequested: hostOptionsDialog.open()`. Az `optionsRequested` jelzést egyedül ez a menütétel adja ki (`grep -rn optionsRequested src/picasapy`: `PicasaToolsMenu.qml:438` és a jelzés deklarációja `PicasaMenuBar.qml:303`), gyorsbillentyű vagy más belépési pont nincs. | **Egyezik.** Nincs teendő. |
| 2 | **Webalbum-szinkron ablak `change` -> 6. fül** (`0x007df2b0`, `0x007df347`). | Nincs szinkron-megerősítő ablak; a Web Albums fül letiltott (`OptionsTabWebAlbums.qml`, lásd a [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) 985. sorát). | **Szándékos eltérés** (megszűnt szolgáltatás). Nincs teendő. |
| 3 | **Menüsor-zár, az Opciók kivétel** (`0x007615d0`, `0x00761696`). A zároló hívói NINCS MEG. | `PicasaToolsMenu.qml:435-438`: a `MenuItem`-nek nincs `enabled` kötése, tehát mindig elérhető; menüsor-zár nincs. | **NYITVA (BLOKKOLT)**: nem tudni, mikor zárol az eredeti. Lásd a 6. szakasz M6 mérését. |
| 4 | **Kezdőfül és megjegyzett fül:** a menü `-1`-gyel nyit, ezért az **utoljára használt fülre**; az érték a `Preferences\LastUsedOptionsPage` (alapérték 0), **minden lezáráskor mentődik**, az OK megnyomásakor és Mégse-nél is, tehát munkamenetek között is megmarad (`0x005cf5d6`, `0x006e373d`). | `OptionsDialog.qml:101-105`: `function open() { optionsDraft.discard(); optionsWindow.visible = true; Qt.callLater(function() { okButton.forceActiveFocus() }) }`: a `tabBar.currentIndex`-hez nem nyúl. A példány megmarad (`MainWindowDialogStack.qml:353-356`: `DeferredDialog { id: optionsDialog ... sourceComponent: Component { OptionsDialog { } } }`, a `Loader` nem kapcsol vissza), így a fül **egy munkameneten belül** megmarad, **újraindítás után nem**. `grep LastUsedOptions\|options/lastPage` a `src/`-ben: nincs találat. | **ELTÉR.** Jegy: A (lent). |
| 5 | **OK = mentés, Mégse = elvetés** (`0x008d2720`, `0x006e3990`, `0x00b0d990`). | `OptionsDialog.qml:112-116`: `function acceptOptions() { optionsDraft.commit(); saveAcceptedOptionSettings(); optionsWindow.visible = false }`; `:147-150`: `function cancelOptions() { optionsDraft.discard(); optionsWindow.visible = false }`; `:152`: `onClosing: optionsDraft.discard()`. | **Egyezik** (#5906). Nincs teendő. |
| 6 | **Általános mentés:** minden elfogadáskor a 8 + 12 + 2 kötött vezérlő kiíródik, módosítástól függetlenül (`0x006e39af`, `0x009a5b30`). | `option_settings.py:100-105`: `def save_all_option_settings(settings, values): ... for key in OPTION_SETTING_KEYS: settings.setValue(key, values[key])`; hívója `OptionsDialog.qml:118-145` (`saveAcceptedOptionSettings`) minden OK-n. | **Egyezik** a hatásban (minden OK mind a 16 kulcsot írja). Nincs teendő. |
| 7 | **`SingleClickExit` élő jelző** az OK után (`0x005cfb27`, `[ebp+0x31ac]`). | `appearance_controller.py:259-267`: `self._single_click_exit_enabled = enabled; self._get_settings().setValue(SINGLE_CLICK_EXIT_KEY, ...); self.singleClickExitEnabledChanged.emit()`. | **Egyezik.** Nincs teendő. |
| 8 | **`Clear cache files` = egyszeri, azonnali művelet OK-ra:** ha a jelölő be van kapcsolva, a két memóriabeli bélyegképtár azonnal újrainicializálódik, és **a jelölő nullára áll vissza** (`0x005cfdeb`-`0x005cfe48`). Kilépéskor semmi nem olvassa a kulcsot: a `disposepreviews` sztring a teljes `.text`-ben csak három helyen szerepel (`0x005cf5b0`, `0x006e0cb0`, `0x006e1100`). | `appearance_controller.py:279-282`: `self._dispose_previews_on_exit = enabled; self._get_settings().setValue(DISPOSE_PREVIEWS_ON_EXIT_KEY, "true" if enabled else "false")`; `library_controller_activity.py:352-356`: `if getattr(self, "disposePreviewsOnExit", False): ... self._provider.wait_for_done(10_000); self._provider.clear_cache()`: **tartós jelölő, kilépéskor ürít (lemezes és memóriabeli cache-t)**; az az OK megnyomásakor nem történik semmi, és a jelölő nem áll vissza. | **ELTÉR** (időzítés és jelleg). Jegy: B (lent). A [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) 912. sorának "EGYEZIK" minősítése ezzel helyesbítve. |
| 9 | **Fájltípus-váltás azonnali hatása:** OK után a szűrő frissül; a letiltott típusokra rekord-kivételi menet, az engedélyezettekre külön hívás fut (`0x005cfb50`-`0x005cfd8f`, `0x004fb9c0`, `0x004efb40`; a pontos jelentés feltételes, lásd az 1.4 d sort). | `library_controller_folders.py:206-210`: `def setFileTypeEnabled(self, group, enabled): ... set_file_type_enabled(settings, group, enabled); self._filetype_scan_snapshot = enabled_filetype_groups(settings)`: csak a **következő pásztázás** pillanatképét frissíti, azonnali eltávolítás vagy újraolvasás nincs. | **ELTÉR (feltételes).** Kutatási jegy: C (lent), a fejlesztés utána. |
| 10 | **Importcél módosítása felveszi a mappát a mappatárba** (`0x005cf772`-`0x005cfaf1`: `0x004ef8f0`, `0x004f6a20`, `0x004f5960`, `0x004f5d90`). Az `AcquirePath` kulcsot csak változásnál írja. | `import_source_controller_state.py:198-201`: `if normalized == self.defaultDestination: return`; `self._get_settings().setValue(DEFAULT_DESTINATION_SETTINGS_KEY, normalized)`; `self.defaultDestinationChanged.emit()`: csak a QSettings-értéket írja, a mappatárba nem veszi fel. Az `is_dir()` vizsgálat (`:193`) csendben eldobja a nem létező célt. | **ELTÉR (feltételes).** Kutatási jegy: D (lent). |
| 11 | **Arcfelismerés ki-be az OK után:** csak **változásnál** indít (`0x0047bee0`) vagy állít le (`0x0047c160`) (`0x005cff39`: `cmp [esp+0x58], ebx`). | `face_scan_controller_settings_mixin.py:50-56`: `def setAutomaticDetectionEnabled(self, enabled): self._settings.setValue(...); if enabled: self.scanNewFaces() elif self._automatic_scan: self.cancelScan()`: a staged író csak módosított kapcsolónál fut, tehát gyakorlatilag egyezik. Apróság: a kétszer átváltott (végül változatlan) kapcsolónál is meghívódik. | **Egyezik** (érdemi eltérés nincs). Nincs teendő. |
| 12 | **Arcküszöbök újratöltése és `0x00487590` futtatása minden OK-n** (`0x005cfe67`-`0x005cfeef`). | `face_scan_controller_embedding_mixin.py:61-66`: `def _csoportositasi_beallitasok(self) -> tuple[bool, int, int]: ... return (self.suggestionsEnabled(), self.suggestionThreshold(), self.clusterThreshold(),)`: a küszöböt a csoportosító munka indításakor olvassa a QSettings-ből, tehát az új érték a következő csoportosításra érvényes; az OK-ra szóló azonnali újraszámítás nincs. | **NYITVA (BLOKKOLT)**: a `0x00487590` jelentése NINCS MEG. Kutatási jegy: E (lent). |
| 13 | **Nyomtatási gyorsméret-gombok frissítése nyitott panelen** (`0x005cfd94`-`0x005cfde5`). | `PrintDialogLogic.qml:248-249`: `hostWindow.printSizeIds = printController.printSizes(); hostWindow.printSizePresetIds = printController.printSizePresets()`: a nyomtatás párbeszéd **minden megnyitáskor** újraolvassa; nyitva maradó nyomtatási panelünk nincs. | **Egyezik a megfigyelhető viselkedésben** (feltételes: nincs mérve, hogy a mi felületünkön lehet-e nyitott panel az Opciók alatt). Nincs teendő. |
| 14 | **Hibaág az az OK ágában nincs**, az egyetlen üzenet a nyelvváltás megerősítése; a Preferences-írás hibája és az importcél-hiba csendes. | `OptionsDialog.qml:118-145`: a `saveAcceptedOptionSettings` hiányzó vezérlőnél **csendben visszatér** (`return`), hibaüzenet nincs; a nyelvváltás megerősítése a [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) 635. szakaszában egyezőnek mért. | **Egyezik.** Nincs teendő. |
| 15 | **Az ablak megnyitásának feltétele:** modális a főablakra (a megnyitó a főablak kezelőjét adja át). | `OptionsDialog.qml:22`: `modality: Qt.ApplicationModal`. | **Egyezik.** Nincs teendő. |

**Összesítés:** 15 sor: 8 egyezik (1, 5, 6, 7, 11, 13, 14, 15), 1 szándékos eltérés (2), 4 eltérés (4 és 8 igazolt; 9 és 10 feltételes), 2 nyitott (3, 12). Két **igazolt, megvalósítható** eltérés van: a megjegyzett fül (4) és a `Clear cache files` időzítése (8).

## 3. Mit NEM állítok

- Nem állítom, hogy a `0x004fb9c0` **törli a fájlt**: a rekordot a mappatárból veszi ki; a lemezen lévő fájl sorsa nem vizsgált.
- Nem állítom, hogy a `0x006b8710` a **lemezes** cache-t törli: törzsében nincs fájl-API, a hívott segédek (`0x006b5bc0`, `0x00980ec0` stb.) nincsenek megnézve.
- Nem állítom, hogy az importcél felvétele **folyamatos figyelés**: a `scanlist.txt` kezelő hívása egyszeri beolvasást is jelenthet; a mód NINCS MEG.
- A `usagestats` vezérlőnév a kötött listában van (`0x006e1392`), tehát az általános mentés feltehetően a `Preferences\usagestats` kulcsot is kiírná; a registryben való tényleges megjelenése **NINCS MEG** (M3 mérés).

## 4. A két független út és a cáfoló kísérlet

- **A út (utasításszint):** a `0x005cbddd` kezelő és a `0x005cf5b0` megnyitó, a `0x006e3990` mentő és a `0x006e36e0` destruktor soronkénti olvasása.
- **B út (teljes `.text` pásztázás és index):** a `0x9cab`, `0x5cf5b0` és `0xc95630` immediate-ek pásztázása a `paszta.py` darabolt mintájával (memóriaplafon alatt); a `string_xrefs` a 37 kulcsra: a `LastUsedOptionsPage` csak `0x005cf5b0` és `0x006e36e0`; a `disposepreviews` csak `0x005cf5b0`, `0x006e0cb0`, `0x006e1100`; az `AcquirePath` csak `0x00513830` és `0x006e3990`.
- **Egyezés:** a két út a belépési pontra (egy menüsor + egy szinkron-ablak hívó), a megjegyzett fülre és a `disposepreviews` viselkedésére ugyanazt adja.
- **Cáfoló kísérlet 1:** azt próbáltam cáfolni, hogy a `disposepreviews` kilépéskor tartós beállításként működik (ahogy a PicasaPy #5897 megvalósítja). Ehhez kilépéskori olvasó kellene: a teljes `.text` pásztázásban a sztring címe (`0x00c95630`) csak három kódhelyen áll, és egyik sem kilépési út (megnyitó, regisztráló, ablak-inicializáló). A cáfolat nem sikerült, tehát az OK-ra szóló egyszeri ürítés áll.
- **Cáfoló kísérlet 2:** azt próbáltam cáfolni, hogy van más belépési pont (eszköztár, gyorsbillentyű, `WM_COMMAND` küldés). A `0x9cab` immediate csak a menürekordban és az `EnableMenuItem` hívásban szerepel; a megnyitónak két hívója van. Nem sikerült cáfolni, de a vtábla-hívások az indexben nem látszanak, ezért a "nincs más belépési pont" **feltételes** a közvetett hívásokra.
- **Független újralevezetés (#140):** nem futott: ebben a körben nincs alügynök-eszköz. A bizonyítottsági fok ezért az "erős" mellett marad, a "megerősített" nincs kimondva.

## 5. Javasolt fejlesztői jegytörzsek

### A. Az Opciók ablak az utoljára használt fülre nyíljon, és ezt munkamenetek között is jegyezze meg

**Eredeti:** `0x005cf5d6`-`0x005cf608` (a `Preferences\LastUsedOptionsPage` olvasása, alapérték 0, a menü `-1`-gyel hívja), `0x006e373d`-`0x006e3767` (a `COptionsDialog` destruktora **minden lezáráskor**, az OK megnyomásakor és Mégse-nél is kiírja a `tabs` vezérlő értékét), `0x005cf708`-`0x005cf727`.

**MIT AD MA:** `OptionsDialog.qml:101-105` a `tabBar.currentIndex`-hez nem nyúl; a fül egy munkameneten belül megmarad (a `DeferredDialog` példány él), újraindítás után mindig az első fülre nyit.

**Teendő:** a fül indexét minden lezáráskor (OK és Mégse, valamint ablakbezárás) mentse QSettings-be, és a következő megnyitáskor erre a fülre nyisson; a kulcs hiányában az első fül. A PicasaPy 9. füle (Google Photos, index 8) is menthető; ha az érték nagyobb a fülek számánál, az első fül. A `openGooglePhotos()` (`OptionsDialog.qml:107-110`) saját belépés marad. **Kész, ha:** (1) új profilon az első megnyitás az Általános fülre nyit; (2) a Névcímkék fülre váltás és Mégse után az újraindított alkalmazás ismét ezt a fület mutatja; (3) teszt mindkét útra (OK, Mégse).

### B. A `Clear cache files` egyszeri, azonnali művelet legyen, ne kilépéskori tartós beállítás

**Eredeti:** `0x005cfdeb`-`0x005cfe48`: az Opciók OK-ja után, ha a `disposepreviews` nem nulla, a megnyitó nullát ír vissza a kulcsba, és a két memóriabeli bélyegképtárat (`[könyvtár+0x22d0]`, `[könyvtár+0x237c]`) azonnal újrainicializálja (`0x006b8710` kétszer). A kulcsot kilépéskor semmi nem olvassa (a sztring a teljes `.text`-ben csak három helyen áll: `0x005cf5b0`, `0x006e0cb0`, `0x006e1100`).

**MIT AD MA:** `library_controller_activity.py:352-356` kilépéskor üríti a lemezes és memóriabeli cache-t, ha a tartós jelölő be van kapcsolva; az az OK megnyomásakor nem történik semmi, a jelölő bekapcsolva marad.

**MIHEZ NE NYÚLJ:** ne törölj lemezes cache-t az OK-ra szóló ürítésben, amíg a `0x006b8710` lemezes hatása NINCS MEG (a PicasaPy lemezes miniatűr-cache-e a mi saját megoldásunk, nem az eredeti bélyegképtár); a Ctrl+Shift+U ürítéssel egyező memóriabeli újrainicializálás a bizonyított rész.

**Teendő:** az OK elfogadásakor, ha a jelölő be van kapcsolva, a PicasaPy memóriabeli bélyegkép-gyorsítótárát azonnal ürítse, és a jelölő álljon vissza kikapcsoltra; a kilépéskori ürítés szűnjön meg (vagy a döntés legyen kimondva). **Kész, ha:** (1) bejelölt jelölővel OK után a következő megnyitáskor a jelölő üres; (2) a gyorsítótár ürült; (3) nem bejelölt jelölőnél semmi nem ürül. **A megvalósítás előtt javasolt az M1 Colab-mérés** (egy feladat), mert a viselkedés megváltoztatása működő (#5897) funkciót érint.

### C. Kutatási jegy: a fájltípus-váltás azonnali hatása OK után (`bináris-kutatható`)

**Eredeti:** `0x005cfb50`-`0x005cfd8f`, `0x004fb9c0` (letiltott típusokra futó rekord-vizsgálat és -kivétel, feltételes olvasat), `0x004efb40` (engedélyezett típusokra, jelentése NINCS MEG), `0x004ebe40`.

**Ghidra-kötegbe:** `0x004efb40`, `0x004fb9c0`, `0x004ebe40`, `0x004e2cc0`, `0x004f9450` dekompilálása. **Colab:** M4. A fejlesztési jegy (PicasaPy: azonnali kivétel/újraolvasás OK után) csak az eredmény után nyitható.

### D. Kutatási jegy: az importcél felvétele a mappatárba (`bináris-kutatható`)

**Eredeti:** `0x005cf772`-`0x005cfaf1`, `0x004f6a20` (`scanlist.txt` kezelő), `0x004f5960`, `0x004f5d90`.

**Ghidra-kötegbe:** a `0x005cf7e9`-`0x005cfa22` rekord összeállítása (a delta-rekord `+0x30` mezője `2`) és a `0x004f6a20` hívási módja; **Colab:** M5.

### E. Kutatási jegy: az arcküszöb-újratöltés és a `0x00487590` jelentése (`bináris-kutatható`)

**Eredeti:** `0x005cfe67`-`0x005cfeef`, `0x0048aab0` (mindig `0xf4240`-et ad), `0x00487590` (3932 b). **Ghidra:** `0x00487590` dekompilálása; **Colab:** az arcos mintakészlettel a Névcímkék fül küszöb-csúszkájának mozgatása OK-val, majd a Személyek panel javaslatainak összevetése azonnal.

## 6. Nyitott kérdések, és a Colab-lépéssorok

A lépéseket a `colab_felmero.py menu "Tools" "Options..."` adja a menükatalógusból (Eszközök a 7. menü, `Options...` a 13. tétel); a kimeneti jelzők: `kepernyokep,registry,profil,allapot`. Új profil: `--indulas friss`.

- **M1, `disposepreviews` egyszeri művelet.** Friss profil; Tools ▸ Options...; Általános fül: "Clear cache files" bejelölése; OK; Tools ▸ Options... újra; képernyőkép és `registry`. **Várt (ha a bináris út helyes):** a jelölő üres, a `disposepreviews` érték 0 (vagy nem létezik). **Cáfolja:** ha a jelölő bejelölt marad és a kulcs 1.
- **M2, megjegyzett fül.** Friss profil; Options...; a Name Tags fül (8.) kiválasztása; Cancel; `registry`: `LastUsedOptionsPage`; Options... újra: melyik fül nyílik; majd a Picasa újraindítása (`indulas: folytat`) és Options...: melyik fül. **Várt:** 7 (Name Tags) a registryben, és mindkétszer a Name Tags fül.
- **M3, általános mentés.** Options...; Általános: "Show tooltips" ki, "Single-click to exit Edit View" be; OK; `registry`. **Várt:** `ShowTooltips`=0, `SingleClickExit`=1; kérdés, hogy a `usagestats` kulcs megjelenik-e, és a nem módosított nyolc kötött kulcs mind kiíródik-e.
- **M4, fájltípus-váltás azonnali hatása.** Minta mappakészlet figyelt mappával (Tools ▸ Folder Manager...); Options... ▸ File Types: egy olyan típus kikapcsolása, amelyből van fájl a mintában; OK; újraindítás nélkül képernyőkép és `db3`; majd ugyanezt vissza (engedélyezés), és a képernyőkép. **Eldönti:** a fájlok azonnal eltűnnek-e, illetve megjelennek-e.
- **M5, importcél-felvétel.** Options... ▸ General ▸ Browse...: egy új, üres mappa; OK; Tools ▸ Folder Manager...: megjelenik-e a mappa, melyik állapotban (Scan Always, Scan Once, Remove from Picasa); `profil`: `watchedfolders.txt`, `scanlist.txt`.
- **M6, menüsor-zár.** Egy hosszú háttérművelet közben (Tools ▸ Back Up Pictures... vagy nagy export) a Tools menü képernyőképe: mely tételek szürkék, és az Options... elérhető-e.

**Nyitott kérdések mérlege** (a [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) régi `NINCS MEG` sorait is beleszámítva):

| # | Kérdés | Állapot |
|---|---|---|
| 1 | Mikor és mi váltja ki a `disposepreviews` írását, és kilépéskor olvassa-e valami? | **LEZÁRVA** (erős): az OK váltja ki, kilépéskor nem olvassa semmi (két független út). M1 csak megerősít. |
| 2 | Melyik fülre nyit az Opciók, és megmarad-e az újraindítás után? | **LEZÁRVA** (erős): `LastUsedOptionsPage`, minden lezáráskor mentve. M2 csak megerősít. |
| 3 | Van-e hibaág vagy üzenet az Opciók mentési láncában? | **LEZÁRVA** (feltételes): nincs a `0x006e3990` és a `0x005cf5b0` saját sztringjei között, a nyelvváltás megerősítésén kívül. |
| 4 | Törli-e a `0x006b8710` a lemezes cache-t, és mit tesz a `0x004fb9c0`/`0x004efb40` a lemezen lévő fájlokkal? | **BLOKKOLT:** Ghidra-dekompilálás (C jegy) és M1/M4 kell, tőlünk (a hívó adja fel a Colab-feladatot). |
| 5 | Milyen módban veszi fel az importcélt a mappatárba? | **BLOKKOLT:** Ghidra (D jegy) és M5. |
| 6 | Mit számol újra a `0x00487590` az OK után? | **BLOKKOLT:** Ghidra (E jegy). |
| 7 | Mikor zárolja a menüsort a `0x007615d0`? | **BLOKKOLT:** M6, vagy a CThumbUI 5. vtábla-helyének hívóit kereső Ghidra-pásztázás. |
| 8 | Kiírja-e a generikus mentés a `Preferences\usagestats` kulcsot? | **BLOKKOLT:** M3. |
| 9 | Megvan-e a `ReportStats` "nincs tárolva" háromállapotú viselkedése nálunk? | **LEZÁRVA** (a #5470 és ez a lap): az eredeti nem írja a kulcsot jelölés nélkül, a PicasaPy-ban a jelölő letiltott, tehát nincs eltérés a hiányzó funkció miatt. |

**Nyitott kérdések: 0 nyílt (örökölt) · 4 lezárva · 5 blokkolt · 0 hatókörön kívül · 0 "csak nyitva".**

## 7. Módosított fájlok

- `docs/specs/paritas-folyamat-7325.md` (új lap)
- `docs/specs/00-index.md` (egy sor)
- `docs/specs/picasa-fo-ablak-elrendezes.md` (a megválaszolt `NINCS MEG` sorok helyesbítése: 483., 912. sor, és a #6062 tábla utáni megjegyzés)
