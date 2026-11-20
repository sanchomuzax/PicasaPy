# A film készítésének teljes folyamata az eredeti Picasával összevetve: belépési pontok, ablak, hatás

## Hatókör és mérések

Ez a lap a #7288 kérdésére szűkít: honnan indul a filmkészítés, milyen panelt nyit, mit kérdez, majd milyen fájl- és felületi hatása igazolható. Az eredeti vizsgálat tárgya a Picasa 3.9.141.259 binárisa, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. Csak statikus vizsgálat történt.

Az előírt előzetes ellenőrzés eredménye:

- A `docs/specs/` alatt nem volt korábbi film/movie nevű önálló folyamatlap. A panel és a kimenet részleteit a `picasa-create-features.md` 2.6/c, 2.7 és 2.8/d szakasza tartalmazza.
- A meglévő futtatott eredmény a `paritas-ellenorzes-archiv-1.md:1112` `job-640/14` sora. A Picasa „This feature is not supported for Linux” hibát adott, ezért abból kész WMV, indexelés vagy siker utáni nézet nem olvasható ki. A fejlécgomb kijelölési feltételét ugyanott külön bináris út igazolja.
- A `~/.local/share/picasapy-meroadat/meroadat.tar` taglistájában 944 tag volt, de nem volt film/movie vagy job nevű tag. Nem kellett tagot kibontani. A korábbi specifikáció is rögzíti, hogy nincs összevethető natív filmkimenet.

**Pontosítás a meglévő #5664 A állításhoz:** az eredeti menüépítő a Movie almenü alá három elemet hoz létre. Ezért a korábbi leírás azon mondata, hogy az eredeti egy szinttel közvetlenebb menüt használ, nem egyezik a `0x00559150` utasításútjával. A jelenlegi menüfa szerkezete egyezik; a normál parancs felirata tér el: eredetileg `From Selection...`, nálunk `New Movie...`. A korábbi lapot e feladat hatókörén kívül nem módosítom.

Az értékek és hiányok alább `bináris (0x...)`, `mérés (job-...)` vagy `NINCS MEG` jelölésűek. A forráskód-hivatkozás statikus PicasaPy-ellenőrzés, nem futó felületmérés.

## Belépési pontok

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Felső menü: `Create > Movie` alatt három parancs: From Selection `0x9d58`, From Faces in Selection `0x9d59`, From People Albums `0x9d5a`; a menüépítő `0x00559150`, a közös indító `0x0057cb60`. | `PicasaCreateMenu.qml:52-78`, jelzések bekötése `MainMenuBar.qml:339-341`. A három parancs megvan, de a normál sor neve `New Movie...`. | **Igazolt eltérés:** a normál menütétel felirata tér el. A menüfa mélysége egyezik. Javaslat: `New Movie...` feliratot cseréljük az eredeti `From Selection...` megfelelőjére; a face és People parancs maradjon külön. A natív menüpontok pontos szürke/aktív feltétele `NINCS MEG`; a parancsok bemeneti útja ismert. |
| Mappa fejléc `headerpanel/create_movie`: közvetlen hívás `0x005e0f70 -> 0x0057cb60`. Két vagy több kijelölt kép esetén a kijelöltek, egyébként a csoport összes képe kerül átadásra (`0x00699cd0`, `0x005c7e40`, `0x005c76b0`). | `LightboxHeaderButtons.qml:150-172`; a sorok kiválasztása `LightboxFeedGroup.qml:101-121`; továbbítás `MainProjectTabs.qml:127-132`. Két vagy több, a csoportba eső kijelölt kép esetén a kijelöltek, máskülönben az egész csoport kerül átadásra. | **EGYEZIK** a statikusan igazolt bemeneti szabály. A `job-640/14` Linux-hibája nem alkalmas a sikeres natív panel indulásának vagy bemeneti képlistájának futásidejű igazolására. |
| Emberek album fejléce: `faceheaderpanel/create_movie` és `faceheaderpanel/create_face_movie`; a `0x005e0f70` közös belépője a face gombnál `0x9d59` módot ad át. A két gomb felirata és mérete a `picasa-arcfelismeres.md:1569-1624` lapon van. | A két QML gomb `LightboxHeaderButtons.qml:173-218` alatt ugyanarra a `personMovieRequested` jelzésre fut. A jelzés az `openPersonAlbumMovie()` ágon a nem üres People-albumok összes forrását kéri le (`LightboxFeedPersonHeader.qml:81-84`, `MainPeopleAlbumState.qml:77-90`, `people_controller.py:209-222`). | **NINCS MEG**, hogy az eredeti `create_movie` és `create_face_movie` gomb külön-külön milyen pontos személyalbum-listát használ. A címek a közös belépőt és a `0x9d59` face módot igazolják, de a sorindexből épített forráslista teljes útja itt nincs lezárva. Eltérést és fejlesztői jegyet addig nem állítunk. Megszerzés: az eredeti Emberek album fejlécén mindkét gombot futtatni, előtte-utána kliplistát rögzíteni; szükség esetén a row-indexet feldolgozó út célzott követése. |
| Alsó kimeneti sáv `outputlayout/makemovie`: a `0x005d9cc0` `0x005dab7d-0x005dac01` ága `row=-1` értékkel hívja a `0x0057cb60`-at. A `[0x00d67849]` jelző megnyitja a Shift-állapot vizsgálatát, amely `0x9d59` arc módot adhat. | `trayMovieButton` `TrayActionArea.qml:521-547`, bekötése `MainTrayBar.qml:67-70`. A gomb csak nem üres rácskijelölésnél engedélyezett. A Filmkészítő bemeneti útja tartott képek esetén a tálcát választja (`MovieMakerActions.qml:10-40`, `create_collage_operations.py:23-38`). | **Nyitott:** az eredeti gomb engedélyezési feltétele tartott képek és üres rácskijelölés mellett `NINCS MEG`; a `[0x00d67849]` szerepe sincs megnevezve. A mai gomb csak rácskijelölést kapuz, miközben a menü tálcával is nyitható. Ez önmagában nem bizonyít eltérést. A natív `Shift` ág feltételes; a PicasaPy gomb nem ad át módosítóbillentyűt. A két feltételt tiszta Windows-felvételen kell összevetni.
| Képkontextus menü: a teljes 418 parancsos leltárban a `MMFilm` a filmcsík diájának saját menüje (`0x00734a80`), nem könyvtári filmindító. A 25 menüépítő összesítése: `ui-audit-context-menus.md:271-298,744`. A gyorsbillentyű-leltárban nincs Filmkészítőt indító billentyű; a `/`, `,`, `.` videólejátszási nevek (`picasa-gyorsbillentyuk.md:205-207`). | A könyvtári, kép-, tálca- és People-helyi menük nem adnak további Movie Maker indítót; nincs dedikált Movie Maker `Shortcut`. | **EGYEZIK a feltárt leltár szerint.** A menüépítők teljes listája és a kulcstábla független a bináris-index negatív találatától. |

## Panel, kérdések és megjegyzett állapot

Az eredeti Filmkészítő a főablakba ágyazott `panelroot/makemoviepanel`, nem külön felső szintű párbeszédablak. A `800 x 534` méret tervvászon-adat; tényleges pixelméretet nem állít. Bal oldali beállítófülek, jobb előnézet és alsó filmcsík tartozik hozzá. A PicasaPy is főablakba ágyazott projektlapot nyit (`MovieMakerDialog.qml:6-25`); a két szerkezet egyezik. A két program azonos ablakméretű, futó képernyőkép-összevetése `NINCS MEG`.

A mezők és alapértékek teljes tételes összevetése a `picasa-create-features.md:6441-6466` alatt található. Ott vannak a felbontás, diaidő, átmenet, átfedés, hangsáv, szöveges dia, rendezés, képarány, felirat, dátum, crop, célfájl és fájlnév állapotai, bináris címmel vagy megadott megszerzési úttal. A már igazolt panel-eltérések #5664 A-F jegytörzsei ugyanott szerepelnek; itt nem másoljuk meg őket.

| Kérdés vagy megjegyzett állapot | Eredeti | Nálunk | Teendő |
|---|---|---|---|
| Korábban készült film célja | Ha a panelben korábbi filmútvonal van, a `0x00620718-0x0062082c` kérdezi: meglévő cseréje, új fájl, vagy Mégse. A Mégse visszatér a szerkesztéshez (`0x00620804`). | `previousMoviePath` esetén a Replace/Create New párbeszéd nyílik (`MovieMakerActions.qml:133-147`). | **EGYEZIK** a csere, új kimenet és megszakítás választás. |
| Render előtti beállításkérdés | A `0x0061df10` render útja `0x006204ec`-nél `askapplyswitchconfirm` kaput vizsgál. A hívó 0 esetén újraszámol, 2 esetén megszakít, más eredménnyel renderel tovább (`0x00620510-0x006205a5`). A gombfelirat és eredménykód pontos megfeleltetése `NINCS MEG`. | `startMovieExport()` a pillanatnyi QML értékeket közvetlenül átadja, nincs megfelelő kapu (`MovieMakerActions.qml:148-175`). | **Eltérés, a kérdés megléte igazolt.** Javasolt fejlesztői jegytörzs lent. A gombok pontos eredménykódját előbb natív Windows-méréssel kell rögzíteni. A korábbi #5664 összevetés részletesen dokumentálja a kérdés szövegét és korlátait (`picasa-create-features.md:5516-5526`). |
| Felhasználó bezárja a még ki nem exportált projektet | Van `CMakeMoviePanel::autosave`, `Movies/autosave.mxf` és helyreállított projekt út (`0x0068a4b0`). A pontos automatikus mentési időzítés `NINCS MEG`. | Az `.mxf` projektoldalfájl csak sikeres export után íródik (`create_movie_controller.py:566-580`; korábbi összevetés: `picasa-create-features.md:6465`). | **Eltérés:** a félbehagyott projekt automatikus visszaállítása hiányzik. A pontos natív mentéskiváltást ne becsüljük; a #5664 E fejlesztői jegytörzs ezt külön rögzíti. |

## Export és fájlhatás

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Alap cél `<My Pictures>\\Picasa\\Movies`, lokalizált mappanévvel; sikertelen létrehozáskor `My Videos` tartalék (`0x0061cf20`, `0x00620af9-0x00620b1d`). A mappa `.picasa.ini` fájljában `P2category=Projects (internal)` (`0x0061d005`, `0x00445a30`). A film `.wmv` (`0x00620b84`, literál `0x00c81a44`), a WMV író `0x00549240`. | Alapértelmezett cél és album-ini: `create_movie_controller.py:236-265`; MP4 export: `create_movie_controller.py:487-498`; siker utáni index-értesítés `:585-588`. | **Fájltípus eltérés:** nálunk `.mp4`/`mp4v`, az eredetiben `.wmv`. Ez már az #5664 D jegytörzsben szerepel; az MP4 hordozhatósági döntését ne írjuk felül az új jegyben. Az ini és az index felé küldött értesítés útja megvan. |
| Csere módban régi fájl törlése, `ERROR_ACCESS_DENIED` esetén 5 másodpercnyi újrapróbálás (`0x00991f00`, `0x009aed2f`); ütközésnél egyedi fájlnév (`0x00993030`). | Célcsere vagy új fájl (`MovieMakerActions.qml:133-147`), kimeneti fájlnév és mappakezelés az `app/movie_output.py` modulban; pontos összevetés `picasa-create-features.md:6462-6463`. | A csere/új fájl kérdés egyezik. Az eltérő alapnév és sorszámozás korábbi #5664 C jegytörzs; új teendőt nem duplázunk. |
| Szerkesztés közbeni autosave `.mxf`; siker után a panel visszavált a könyvtárlapra (`0x0068a4b0`, `0x00620e68-0x00620f77`). | A controller a videó sikerét követően próbálja írni az `.mxf` projektet, a sikert jelzi; a QML az export indításakor bezárja a Movie Maker oldalt és progress ablakot nyit (`create_movie_controller.py:566-596`, `MovieMakerActions.qml:148-177`, `MovieMakerDialogs.qml:108-147`). | A generált fájl index-értesítést kap. A bal hasáb pontos változása, az új sor rácsbeli megjelenése és a kijelölés siker utáni állapota mindkét programban `NINCS MEG`, mert nincs sikeres natív kimeneti mérés és ehhez kötött utóállapot-felvétel. A #5664 `job-640/14` nem jutott el exportig. |

Az eredeti renderág a `0x0061d820 -> 0x0061d350` úton `projectutils::draft` állapotot és „PISZKOZAT” feliratot használ; a hozzá tartozó szöveg szerint a film még nem készült el. Ez a projekt állapotát igazolja, nem a pontos állapotsor-üzenetet vagy annak képernyőbeli helyét. A PicasaPy modális számlálót mutat: `Creating movie: n / n` (`MovieMakerDialogs.qml:108-147`). Az eredeti állapotsor és progress UI képernyőkép-összevetése `NINCS MEG`.

## Hiba, megszakítás, hálózati vagy írásvédett cél, visszavonás

- Eredeti panel `cancel` parancsa a bezáró ágra megy (`0x0061e1e0`, `0x00620421`, `0x00620ed3`). A készítés előtti bezárás ismert; render közbeni megszakítás működése `NINCS MEG`.
- Eredeti célmappa létrehozási hiba a `My Videos` könyvtárra terel (`0x00620af9-0x00620b1d`). A render hibakódja a `MakeMoviePanelNoMovie` üzenetbe kerül (`0x00620e00`); a `Preferences\\SupportMovies` beállítás egy ágban elnyomja a hibát (`0x00620db2-0x00620dfe`). A csere fájlhozzáférés megtagadásakor 5 másodpercig próbálkozik újra. Hálózati megosztás és külön írásvédett célmappa natív futásidejű eredménye `NINCS MEG`.
- A `job-640/14` csak a Linux/Wine tiltó üzenetet mérte; ez nem renderhiba és nem sikeres exportpróba.
- PicasaPyban hiányzó forrás, `ValueError`, `OSError` és `RuntimeError` `movieFailed` hibát ad (`create_movie_controller.py:512-560`); a QML bezárja a progress ablakot és hibaüzenetet mutat (`CreateDialogs.qml:179-185`). A célmappa `.ini`-írása a render előtt történik (`:236-265`); a kész MP4 mellett az `.mxf` oldalfájl írási hibája naplózódik, de nem fordítja vissza a kész videót (`:566-588`).
- A PicasaPy progress ablak modális és `NoAutoClose`, de nincs benne Mégse művelet (`MovieMakerDialogs.qml:108-147`). A háttérmunka daemonszálon fut (`create_movie_controller.py:595-596`). A natív render közbeni megszakítással és a hálózati/írásvédett hely viselkedéssel való összevetés `NINCS MEG`.
- A filmfájl exportjára vonatkozó natív Undo vagy PicasaPy Undo viselkedés `NINCS MEG`. A filmcsík `MMFilm` helyi menüje szerkesztési műveleteket tartalmaz, de nem bizonyítja az elkészült videó visszavonását. Megszerzés: eredeti sikeres export után Undo/Redo és fájl-, projekt-, kijelölésállapot rögzítése, azonos PicasaPy menetben is.

## Bizonyítottsági fok, két út és cáfoló kísérlet

**Összesített fok: feltételes.** A menüparancsok, a mappa fejléc bemeneti szabálya, a főablakba ágyazott panel, a fájlút és a fő renderág statikusan azonosítható. A siker utáni natív felületi állapot, a People-fejléc pontos forráslistája, hálózati/írásvédett hely, render megszakítása és Undo nincs futó natív méréssel igazolva.

- **A út:** a `0x00559150`, `0x005cb990`, `0x005e0f70`, `0x005d9cc0`, `0x0057cb60`, `0x00618050` és `0x00699cd0` célzott disassembly/dekompilációja a menüt, a kétféle fejlécindítást, a tálcagomb közös belépőjét és a normál mappa-fejléc kijelölési küszöbét adja.
- **B út:** az eredeti `.tre`/szövegerőforrások, a `picasa-menu-parancsok.csv` parancsazonosítói, a 25 helyi menü építő leltára és a jelenlegi QML/Python másik rétegű ellenőrzése. A menüparancsok és a mappa-fejléc bemeneti feltétele egyezik az A úttal. A PicasaPy exportoldali hatásait a QML és a controller külön kódrétege mutatja.
- **Cáfoló kísérlet:** a feltételezett további helyi menü és gyorsbillentyű keresését a teljes natív menüparancs-leltárral, mind a 25 helyi menü építővel és a `SHORTCUTS.XML` kulcstáblájával ellenőriztem. A `MMFilm` csak a dia helyi menüje; `/`, `,`, `.` videónézeti billentyűnevek, nem filmkészítő-indítók. Ez nem talált új könyvtári filmindítót. A tálca Shift-ágánál külön ellenőriztem a `0x00d67849` jelzőt: a disassembly feltételesen olvassa, a jelző szerepe nincs megfejtve, ezért a shift viselkedés teljes egyezését nem állítom.

## Javasolt fejlesztői jegytörzsek

### 1. A normál Movie Maker menüpont a natív feliratot használja

**Eredeti:** `0x00559150` a `Create > Movie` almenübe teszi a `eMenuCreateMovie::MOVIE`, `0x9d58` parancsot `From Selection...` felirattal.

**Nálunk:** ugyanebben az almenüben `New Movie...` feliratú sor indítja a normál filmkészítést (`PicasaCreateMenu.qml:52-66`).

**Teendő:** a normál sor feliratát igazítsd a mért eredeti `From Selection...` felirathoz. A menüfa mélységén ne változtass.

**Kész, ha:** a Movie almenüben a normál sor az eredeti feliratot használja, és a From Faces in Selection valamint From People Albums külön parancsként továbbra is elérhető.

### 2. A render előtti opciókérdés kerüljön át a filmkészítőbe

**Eredeti:** `0x0061df10`, `0x006204ec-0x006205a5`; az `askapplyswitchconfirm` kapu a render előtt kérdez, majd újraszámol, megszakít vagy renderel.

**Nálunk:** a `MovieMakerActions.qml:148-175` közvetlenül a pillanatnyi mezőket exportálja.

**Teendő:** a mért natív feltételekkel jelenítsd meg a render előtti kérdést. A gombcímkék és `0`/`2`/egyéb eredménykód megfeleltetését ne találgatással kösd be; előbb rögzítsd tiszta Windows Picasán.

**Kész, ha:** a megerősítés ugyanazon feltételeknél jelenik meg; a három művelet eredménye mérés alapján újraszámolás, megszakítás vagy export; a megjegyzés beállítása is a mért natív ágat követi.

### 3. A félbehagyott filmprojekt legyen visszaállítható

**Eredeti:** `0x0068a4b0`, `CMakeMoviePanel::autosave`, `Movies/autosave.mxf`; az automatikus mentés pontos időzítése `NINCS MEG`.

**Nálunk:** a film `.mxf` oldalfájl a videó sikeres létrehozása után készül (`create_movie_controller.py:566-580`).

**Teendő:** a nem exportált klip- és diaállapot legyen helyreállítható filmprojektként; a natív kiváltási feltételt és időzítést előbb mérd meg.

**Kész, ha:** az exportálatlan projekt bezárás vagy újraindulás után visszaállítható; a helyreállítás nem írja felül a meglévő kész videót; a mentési kiváltást mérés dokumentálja.

Az alapérték-, fájlnév-, WMV/MP4- és célfájl-választó eltérésekre a korábbi `picasa-create-features.md:6489-6588` #5664 A-F javaslatai érvényesek, itt nem készül duplikált jegytörzs.

## A jegy „Kész, ha” pontjai

- ✅ **Belépési pontok:** menü, mappa-fejléc, People-fejléc és alsó műveletsor felvéve, bináris címmel és PicasaPy-forrással.
- ✅ **Helyi menü és gyorsbillentyű:** a 25 natív menüépítő és a kulcstábla átvizsgálva; a talált `MMFilm` a filmszalag diahelyi menüje.
- ✅ **Panel és alapállapot:** a főablak-panel egyezése, a mezők és preferenciák hivatkozása, a külön megjegyzett állapotok rögzítve.
- ✅ **Fájlhatás:** natív WMV, MXF autosave, `.picasa.ini`, projektkategória, csere/fájlnév és PicasaPy MP4/index-értesítés táblázatban.
- ⛔ **Siker utáni bal hasáb, rács és kijelölés:** nincs sikeres eredeti filmfelvétel; a `job-640/14` a platformkapunál megállt.
- ⛔ **Hiba, megszakítás, hálózat, írásvédelem és Undo futásidejű kimenete:** tiszta Windows Picasa menet és állapotfelvétel szükséges.

## Új kutatási jegyjavaslatok

- **Film siker utáni könyvtárállapot:** hol jelenik meg a natív kimenet a bal hasábban és a rácsban, mi lesz kijelölve, illetve mely indexfájl változik. Keresd `0x00620e68-0x00620f77` után a mappa/index frissítést; készíts sikeres Windows Picasa kimeneti felvételt.
- **Film kimeneti hibaterek:** render megszakítás, hálózati cél és írásvédett cél viselkedése. A natív célzott ágak `0x0061cf20`, `0x00620421`, `0x00620db2-0x00620e00`, `0x00991f00`; a pontos felhasználói eredményt tiszta futásban rögzítsd.

## Nyitott

- `NINCS MEG`: az eredeti People-fejléc két gombjának teljes forráslistája, módonként. Megszerzés: mindkét gomb natív futtatása címkézett People-albumkészlettel; a belépőn átadott row-index út követése.
- `NINCS MEG`: alsó Movie gomb engedélyezése tartott képeknél üres rácskijelöléssel, valamint a `0x00d67849` jelző jelentése. Megszerzés: tiszta natív felületmérés és a globális jelző írójának célzott visszakövetése.
- `NINCS MEG`: első panelnyitás néhány értéke, a siker utáni bal hasáb/rács/kijelölés, natív autosave időzítése, hálózati és írásvédett cél, export megszakítása, Undo. A mező-alapértékek megszerzési útja a `picasa-create-features.md:6454-6588` szakaszban szerepel.
- E körben új Ghidra-dekompiláció nem szükséges; a nyitott állításokhoz natív Windows-mérés kell, kivéve ha a későbbi row-index visszakövetés megakad a típusos hívási gráfon.

## Módosított fájlok

- `docs/specs/paritas-folyamat-7288.md`: új folyamat-összevető lap, belépési pontok, panel, exporthatás, hibák és nyitott mérések.
- `docs/specs/00-index.md`: az új lap hivatkozása.
