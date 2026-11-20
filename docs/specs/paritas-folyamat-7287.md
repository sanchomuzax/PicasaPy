# A kollázs készítésének teljes folyamata az eredeti Picasával összevetve: belépési pontok, ablak, hatás

**Tárgy:** a Picasa 3.9.141.259 kollázs-létrehozási útvonalai, felülete, kimenete és megszakítási ágai, összevetve a PicasaPy jelenlegi forrásával.

**Bizonyítottsági fok: feltételes.** A menü és a fejléc közös panelkezelője utasításszinten megvan, a fejléc adatforrásának eltérését futtatott job-640/9 felvétel támasztja alá. A belépők teljes listája nem zárható le, mert a 0x0053ce00 kollázság látható forrása nyitott; a mentés utáni nézetre a korábbi specifikációk ellentmondanak, a hálózati, írásvédett és visszavonási próbák pedig hiányoznak.

## 1. Belépési pontok

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Létrehozás menü: 0x00559150 építi az ID_COLLAGEMAKER / &Picture Collage... tételt; a 0x005cb990 diszpécser a 0x007463c0 panelkezelőre jut. | src/picasapy/app/qml/PicasaPy/PicasaCreateMenu.qml:31-35; src/picasapy/app/qml/PicasaPy/MainMenuBar.qml:154-158,338; src/picasapy/app/qml/PicasaPy/MainProjectTabs.qml:161-174 | A fő belépő létezik. Nálunk a menü akkor aktív, ha a néző zárva van és van kijelölés vagy tálcatartalom. Az eredeti menütétel pontos engedélyezési feltétele NINCS MEG, ezért feltételbeli eltérést nem állítok. |
| Kimeneti sáv: 0x005d9cc0 kezeli az outputlayout/collage útvonalat, és a 0x007463c0-at hívja. | src/picasapy/app/qml/PicasaPy/MainTrayBar.qml:68; src/picasapy/app/qml/PicasaPy/TrayActionArea.qml:493-512; src/picasapy/app/qml/PicasaPy/MainProjectTabs.qml:95-105,107-125,161-174 | A PicasaPy tálcagomb nézőn kívül, kijelölés esetén aktív. Megnyitáskor a jelenlegi nézetben feloldható tálcautakat adja át, ezek hiányában a kijelölést. Az eredeti felhasználói vezérlő és annak feltétele a statikus hívási útból önmagában nem azonosítható. |
| Mappa- és személyfejléc: 0x005e0f70 kezeli a create_collage nevet; headerpanel.tre:89 és faceheaderpanel.tre:100 tartalmaz ilyen vezérlőt. | src/picasapy/app/qml/PicasaPy/LightboxHeaderButtons.qml:94-127; src/picasapy/app/qml/PicasaPy/LightboxFeedGroup.qml:80-99; src/picasapy/app/qml/PicasaPy/LightboxFeedPersonHeader.qml:72-79; src/picasapy/app/qml/PicasaPy/MainProjectTabs.qml:110-125 | Igazolt eltérés a job-640/9 mérés szerint: az eredeti felvételen két kép van a vásznon és 22 klip marad; a PicasaPy felvétele 24 klipet/csomópontot ad át. A fejléc adatforrását egyező mérési bemenettel kell javítani. Javasolt fejlesztői jegytörzs a lap végén. |
| Egy további "collage" ág a 0x0053ce00-ban a 0x007463c0-at hívja. A forrásvezérlő nem azonosítható utasításszinten. | A fejléc és a tálca útjai láthatók a src/picasapy/app/qml/PicasaPy/LightboxHeaderButtons.qml:94-127 és src/picasapy/app/qml/PicasaPy/TrayActionArea.qml:493-512 fájlokban, de ezek egyikét sem lehet a bináris ághoz kötni. | Nyitott, blokkoló a belépőlista teljességére. Ghidra-kör kell: 0x0053CE00 - az utasításszinten látott collage parancság melyik, a felhasználónak látható eszközről indul, és milyen előfeltétellel [blokkoló]. |
| Helyi menük: az átvizsgált CollageS és CollageD elemek már megnyitott kollázs vászonműveletei. A könyvtári létrehozó parancs a 0x00559150 menüben szerepel. | Az átvizsgált helyi menüleltár: docs/specs/ui-audit-context-menus.md:281-298,450-452; PicasaPy Create menü: src/picasapy/app/qml/PicasaPy/PicasaCreateMenu.qml:31-35. | A vizsgált leltárban nincs könyvtári kollázs-létrehozó helyimenü-tétel. Ez nem teljes bináris negatív bizonyíték, új mérés vagy független teljes pásztázás nélkül nem állítok általános hiányt. |
| Gyorsbillentyű: a menücímben & szerepel. Külön kollázs-létrehozó billentyűsorozat NINCS MEG. | docs/specs/picasa-gyorsbillentyuk.md:19-34,550-552; src/picasapy/app/qml/PicasaPy/PicasaCreateMenu.qml:31-35 | A katalógusban nincs dedikált létrehozó shortcut. Az & hozzáférési jelölés pontos billentyűsorozata nincs mérve. A PicasaPy vászonparancsai nem azonosak a létrehozó shortcut-tal. |

## 2. Ablak, mezők, alapértékek és kérdések

A job-640/9 meglévő eredeti felvétele a Létrehozás menüből nyíló Picture Collage panelt mutatja: Settings és Clips lap, elrendezésválasztó, Draw Shadows, Show Captions, Desktop Background, Create Collage, Reset és Close. A PicasaPy megfelelője Kollázs munkalap, két lappal, elrendezés- és oldalformátum-választóval, árnyék- és feliratkapcsolóval, valamint létrehozó, háttérkép, visszaállító és bezáró művelettel. A mért profilállapot nem tiszta telepítés, ezért a felvételből alapérték nem következik.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| job-640/9: Settings / Clips; Picture Pile; 4:3; Draw Shadows és Show Captions bekapcsolva; Desktop Background, Create Collage, Reset, Close. | src/picasapy/app/qml/PicasaPy/CollagePanel.qml:333-384; docs/specs/kollazs-panel-ui-spec.md; docs/specs/picasa-create-features.md:65-740 | A meglévő felvétel szerinti fő panel és műveletek megvannak. Ez mentett profil felvétele, nem alapérték-mérés. |
| Megőrzött értékek: collage::theme alap picturepile (0x0082b3d0); collage::format 2 feltételesen (0x0082b07a); showcaptions alap 1 (0x0082b828). Az `orientation`, `shadows` és `bgcolor` aktuális tárolt értékből jön (0x0083a1a0, 0x0082afb6, 0x0082c4e0). A shadows témaalapú alapállapota Picture Pile és Contact Sheets esetén be, más témáknál ki (picasa-kollazs-felulet.md:258-262). | A mezők vezérlése a src/picasapy/app/qml/PicasaPy/CollagePanel.qml-ben és a kollázs-vezérlőben; részletes mai megfeleltetés: docs/specs/kollazs-panel-ui-spec.md. | Az alapértékeket nem szabad a job-640/9 képből levezetni. A többi beállítás tiszta profilú futtatott értéke NINCS MEG. A teljes vezérlőleltárt a hivatkozott UI-spec tartalmazza. |
| Meglévő kollázs újraírásakor csere / új létrehozása / Mégse kérdés: 0x0083ba60, 0x0061df10; bezáráskor piszkozat mentése / módosítás elvetése / Mégse. | src/picasapy/app/qml/PicasaPy/CollagePanel.qml:309-330,428-460; src/picasapy/app/qml/PicasaPy/CollageDialogs.qml; docs/specs/kollazs-eletciklus.md:54-72,300-338 | A kérdezési ágak és a hatásuk részletesen szerepel a meglévő életciklus-specben. A jegyhez itt nem kell új párbeszédet kitalálni. |
| Üres vászon: 0x0083ce90 útvonalhoz tartozó "Mentés mellőzve" kérdés; háttérképnél formátumeltérés kérdés. A render megszakítási prompt szövege szerepel a picasa-kollazs-felulet.md:1291-1309 lapon. | src/picasapy/app/qml/PicasaPy/CollagePanel.qml:442-460,486-509; src/picasapy/app/qml/PicasaPy/CollageDialogs.qml:73-106 | Az üres vászon, mentési megszakítás és háttérkép-formátum ág PicasaPy oldalon külön kezelt. A teljes eredeti kérdésszöveg és a normál létrehozásra vonatkozó feltételek a hivatkozott specifikációkban vannak. |

## 3. Fájlok, index, nézet és háttérmunka

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Sikeres mentés: a 0x0083ba60 útvonalon párban létrejövő .jpg és .cxf; kollázs célmappája és Projects kategóriája a picasa-kollazs-felulet.md:1315-1352 szerint. | src/picasapy/app/collage_output.py:367-387,449-510,513-596 | A PicasaPy párban írja a két kimenetet, és a célmappát Projects-ként rögzíti a .picasa.ini-ben. |
| A PicasaPy indexfrissítése mentés után: nincs közvetlen eredeti SQLite-index, ez a mai alkalmazás belső rétege. | src/picasapy/app/collage_save_render.py:187-230; src/picasapy/app/collage_save.py:261-286 | A mentett kollázs bekerül a célmappa indexébe; indexhiba külön kezelhető. Az eredeti Picasa index belső írási útjának tételes összevetése NINCS MEG. |
| Eredeti futásjelzések: inicializálás, százalékos renderelés és megszakítás szövegei a picasa-kollazs-felulet.md:1303-1309 lapon; az életciklus-lap Várakozás a kollázs elkészítésére... főablak-állapotot is rögzít (kollazs-eletciklus.md:757-762). | src/picasapy/app/collage_save_render.py:35-94,232-286; src/picasapy/app/qml/PicasaPy/CollagePanel.qml:468-510; állapotjelzés: src/picasapy/app/qml/PicasaPy/TrayBar.qml:177-178, src/picasapy/app/qml/PicasaPy/TrayInfoBar.qml:116-118 | A PicasaPy renderelő háttérmunkát és panelbeli folyamatjelzést használ. Az eredeti és a mai globális állapotsor teljes, azonos bemenetes összevetése NINCS MEG. |
| Mentés utáni eredeti nézet ellentmondásos a meglévő feljegyzésekben: kollazs-eletciklus.md:327-338 képnézetet ír, :711-727 értesítést említ, míg :340-371,802-816 az értesítést a háttérkép-ághoz rendeli. A job-640/9 nem mentés utáni felvétel. | src/picasapy/app/qml/PicasaPy/MainProjectTabs.qml:241-272 a mentett képet kijelöli a könyvtárban, automatikusan nem nyitja meg a nézőt. | A mentés utáni nézet, bal hasáb, rács és kijelölés paritása nyitott. Ebből jelenleg nem készül eltérés-jegy. Futtatott, tiszta eredeti mentési felvétel kell. |

## 4. Hiba, megszakítás, hálózat, írásvédelem és visszavonás

- **Üres bemenet és formátum:** eredeti párbeszéd és szöveg megvan a picasa-kollazs-felulet.md:1291-1309 lapon. PicasaPy oldalon a src/picasapy/app/qml/PicasaPy/CollagePanel.qml:486-509 kezeli ezeket.
- **Render megszakítása:** az eredeti megszakítási kérdés szövege megvan a picasa-kollazs-felulet.md:1303-1309 lapon. PicasaPy megerősítést kér, majd a vezérlő megszakítja a folyamatot (src/picasapy/app/qml/PicasaPy/CollagePanel.qml:417-423,457-460; src/picasapy/app/collage_save.py:178-227).
- **Mentési hiba:** PicasaPy hibaüzenetet jelenít meg (src/picasapy/app/qml/PicasaPy/CollagePanel.qml:474-480; src/picasapy/app/qml/PicasaPy/CollageDialogs.qml:73-106). Ezzel az eredeti fájlírási hiba pontos párbeszédének egyezése nincs igazolva.
- **Hálózati vagy írásvédett hely:** eredeti futtatott próba NINCS MEG. PicasaPy pontos hálózati és fájlrendszer-hibaüzenete sem lett ezen a kutatási körön futtatva. Eltérés nem állítható.
- **Visszavonás:** a mentés utáni művelet visszavonása eredeti futtatott próbával NINCS MEG. A bezáráskori módosításelvetés és a render megszakítása nem azonos a sikeresen létrehozott kollázs visszavonásával.
- **Kijelölés, rács, bal hasáb és állapotsor:** belépéskor a job-640/9 a fejléc eltérő bemenetét rögzíti; a mentés utáni eredeti állapot NINCS MEG. A meglévő specifikációk utólagos állapotleírásai ellentmondanak, ezért ezt mérésnek kell eldöntenie.

## 5. Két független út és cáfoló kísérlet

- **A út, bináris:** a menüépítő és diszpécser utasításai a kollázs közös panelkezelőjéhez vezetnek; a 0x005e0f70 fejléc-névkezelő és a headerpanel.tre / faceheaderpanel.tre erőforrásrekordok a fejlécből indítható vezérlőt támasztják alá.
- **B út, futtatott felvétel:** a job-640/9 eredeti és PicasaPy képei külön rögzítik a vászonon látható képek, kliplista, projektlap és kijelölés állapotát. Ez a mérési út nem a bináris diszasszemblálásból származik. A két út egyezik abban, hogy a fejléc valós kollázsbelépő, de a forráskészlet viselkedése eltér.
- **Cáfoló kísérlet:** megpróbáltam cáfolni a forráskészlet-eltérést azzal a hipotézissel, hogy a fejléc és a menü ugyanarra a panelkezelőre jut, tehát azonos bemenetet ad. A diszasszemblálás csak a panelkezelő azonosságát igazolja; a job-640/9 felvétel két vászonképet és 22 klipet mutat az eredeti oldalon, míg a PicasaPy mérés 24 klipet/csomópontot. A cáfoló kísérlet nem cáfolta a mért eltérést. A visszaellenőrzés a két forrást külön mércével végezte: bináris cím és utasítás az A úton, rögzített felvétel a B úton.

## 6. A jegy kimeneti pontjai

- Minden kért belépési pontra van bináris, mért vagy nyitott státusz. A lista teljessége a 0x0053ce00 Ghidra-kérdés miatt nyitott.
- Az ablak vezérlői, a beállítások és a kérdések dokumentálva vannak; a job-640/9 profilértékei nem tiszta telepítés alapértékei.
- A fájlpár, .picasa.ini kategória és mai indexfrissítés össze van vetve. Az eredeti belső indexírás nem ismert.
- A mentés utáni nézet, hálózati és írásvédett hely, mentési hiba eredeti párbeszéde és siker utáni visszavonás nyitott, nem szerepel igazolatlan eltérésként.
- Az egyetlen bizonyított futásidejű eltérés a fejlécből indított képkészlet, job-640/9 alapján.

## 7. Javasolt fejlesztői jegytörzs

### Fejlécből indított kollázs forrásképei

**Eredeti: 0x005E0F70**

Az eredeti Picasa 3.9 fejlécből indított kollázs felvételén két kép van a vásznon, 22 klip marad a kliplistában (job-640/9). A PicasaPy ugyanilyen fejlécműveletének mérése 24 klipet/csomópontot ad át. A fejléc belépő forráskészletét az eredeti viselkedéshez kell igazítani, és ellenőrizni kell az eredményt azonos albumon, kijelölésen és tálcaállapoton.

**Kész, ha:**

- ugyanaz a forrásalbum és kijelölés az eredeti és a PicasaPy fejlécműveletén azonos képkészletet ad;
- a vászonra kerülő képek és a kliplistában maradó képek száma egyezik a job-640/9 szerinti eredménnyel;
- a mérés rögzíti a kijelölés és a tálca állapotát is.

