# Az Ajándék-CD teljes folyamata az eredeti Picasával összevetve: belépési pontok, ablak, hatás

## Következtetés

Az eredeti Picasában a Létrehozás menü és a fő nézet `thumbui/cdmode` eleme nyitja meg a közös `publish` panel Ajándék-CD módját; a panel gombja fizikai lemezírást indít, és meghajtó hiányakor ISO-fájlt ajánl fel. A PicasaPy ugyanennek a panelnek a lemezkép-készítő útját valósítja meg, de mindig ISO-fájlt ment, és a fizikai író, lemeztörlés, írási folyamat és megszakítás kezelése nem része a vizsgált útvonalnak.

A teljes futásidejű paritás nem zárható le: az elérhető mérőadat-archívumban nincs Ajándék-CD felvétel. A forrásfájlok és az utasításszintű bináris olvasás több lépést alátámaszt, de a `.picasa.ini`, az index, a könyvtárnézet és a kijelölés művelet utáni állapotáról, hálózati vagy írásvédett célról, valamint a félbeszakított írás maradványairól nem ad futásidejű bizonyítékot.

## Módszer és bizonyítottság

- Vizsgált bináris: Picasa 3.9.141.259, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. A fájlt nem futtattam és nem másoltam a munkafába.
- A `grep -rn "job-[0-9]" docs/specs/` futtatott mérésekre mutató találatai között a kapcsolódó `ajandek-cd-kimenet.md` lapon nincs Ajándék-CD felvétel. A mérőadat-tár név szerinti szűrése sem talált `gift`, `ajand`, `burn`, `cd` vagy `job-<szám>` címkéjű tagot; ezért a `.bt/` alá nem bontottam ki fájlt.
- Az eredeti binárisból az indexben meghatározott méretű függvényeket az `annot_disasm.py` eszközzel olvastam. A teljes `.text` pásztázás kizárólag a `paszta.utasitasok()` útján futott, a `paszta.memoria_kapu()` első műveletként.
- Összesített bizonyítottsági fok: **feltételes**. A függvények vezérlőágai és a statikus `.fen`/`.tre` felületleírók egyeznek, de nem helyettesítik az eredeti program futtatott mérését. A futásidejű állapotokat nem következtetem ki pusztán sztringből vagy indexhiányból.

## Eredeti / nálunk / teendő

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `eMenuCreate::ID_BURNCD`, `0x00559150`: a Létrehozás menü `Create a &Gift CD...` tétele. A `&` menün belüli billentyű-mnemonikát jelöl, nem igazolt globális gyorsbillentyűt. | `src/picasapy/app/qml/PicasaPy/PicasaCreateMenu.qml:46-50`; az engedélyezési feltétel `MainMenuBar.qml:148-158`; az esemény bekötése `MainMenuBar.qml:343`. A menü akkor él, ha nincs nyitva a fotónéző és van kijelölt kép vagy képtálcaelem. | A jelenlegi feltétel forrásból ismert. Az eredeti menü aktiválási feltétele és az eredeti globális gyorsbillentyű nem dőlt el. Lásd D1, ha a teljes belépési paritás cél. |
| Aktív főnézeti módgomb `thumbui/cdmode`; kezelőcímek `0x005cb990`, `0x005d9cc0`, `0x005e0f70`. A panel saját indítógombja `publish/presentcd_go`, melynek ágát a `0x00679ca0` kezeli. A `headerpanel/create_cd` és `faceheaderpanel/create_cd` a meglévő lapon hivatkozott `.tre`-fájlokban kommentelt, kikapcsolt elem. | A vizsgált PicasaPy útvonal a Létrehozás menüből indul (`PicasaCreateMenu.qml:46-50`, `MainMenuBar.qml:343`). A `publish/presentcd_go` megfelelője `PublishPanel.qml:256-263`. | A `thumbui/cdmode`-nak nincs azonosított PicasaPy-beli párja; a két kikapcsolt fejlécgomb nem eltérés. Helyi menü útvonalat nem igazoltam, ezért annak hiányát nem állítom. Lásd D1. |
| Több író esetén meghajtóválasztó: `0x0066b6a0` vizsgálja a meghajtók számát; a `cdchoose` erőforrást a `0x0066b2d0` építi. A statikus `runtime/cdchoose.fen` szövege szerint egynél több meghajtónál `Drives:` listából lehet választani, OK/Cancel gombbal. A `Preferences\\lastcddriveused` értéket a `0x0066b430` és `0x0066b6a0` olvassa a korábbi választás előállításához. | `src/picasapy/app/qml/PicasaPy/GiftCdHost.qml:81-92`: fájlmentő párbeszéd ISO szűrővel, alapértelmezett Képek mappával. Meghajtólistát nem nyit. | Eltérő célválasztás. A binárisban a korábban használt meghajtó beolvasása bizonyított; annak írása új választás után nem bizonyított. D2 csak akkor, ha fizikai író támogatása cél. |
| Ajándék-CD beállításai: `0x0066f470` méretértékei 0, 640, 800, 1600; `Preferences\\CDSlideshow` és `Preferences\\CDSlideshowInclSetup` alapértéke 1; `CDLimitSize` alapértéke 0 (`0x006706d0`, `0x0067112e-0x00671159`). A törlés jelölő `Preferences\\CDEraseFirst` kulcsát a `0x006706d0` 1-es alapértékkel olvassa, az írási ága pedig `0x00675710` alatt újra olvassa. A három közvetlen kulcshivatkozás a biztonságos teljes pásztázásban `0x006710ca`, `0x006757c3`, `0x0067b69e`. A `PicasaCDName` erőforrásban a `Picasa CD` tartalékérték szerepel (`0x0067c5e9-0x0067c5f3`); a paramétertől függő esetleges felülírás nincs teljesen tisztázva. | `PublishPanel.qml:179-197` ad diavetítő jelölőt és négy méretet. `GiftCdHost.qml:48-50` megnyitáskor az aktuális mappa nevét tölti a CD név mezőjébe (`PublishPanel.qml:209-224`). A `PublishPanel.qml:234-249` a `Include Picasa` és `Erase Media` feliratot elrejti; nincs hozzájuk működő jelölő. A diavetítő állapot QSettings-be mentése `ajandek_cd_controller.py:54-68`. A méretfokozat állapotának mentését ez a komponens nem mutatja. | Az Ajándék-CD kapcsolói nem teljesek, a név alapértéke eltérő forrásból ered, és a méret megjegyzett állapota PicasaPy-ben nem bizonyított. Az eredeti `CDEraseFirst` átállítás utáni mentése szintén nyitott. D3 csak a választott, támogatott opciók körére készüljön. |
| A `publish` panel a képtálcán pipával kiválasztott tételekről szól (`publish/giftcdtext`, meglévő spec 13. szakasz). A `0x006740a0` kezdeti gyűjtése a szükséges lemezek számáról ad szöveget; a `0x00673de0` az írás előtti lemezellenőrzést végzi. Ha nincs elérhető író, igen/nem kérdéssel ISO-kimenetet ajánl; az ISO mentőablakot a `0x00674c00` építi `CD%d.iso`, `ISO Files` / `*.iso` szűrővel. | `GiftCdHost.qml:63-78` a tálca elemszámát és diavetítő állapotát adja át; `ajandek_cd_controller.py:81-103` főszálon pillanatképet vesz a tálcáról és háttérmunkát indít; `GiftCdHost.qml:81-92` mindig ISO fájl célját kéri. | Az eredeti fizikai lemezút és PicasaPy ISO út eltér. A jelenlegi útban nincs fizikai meghajtó- vagy lemeztörlési ág. Lásd D2 és D3. |
| Az eredeti Ajándék-CD ág által a lemezre másolt állományok és az `autorun.inf` forrásai, valamint a kimeneti opciók a kapcsolódó `ajandek-cd-kimenet.md` 1-5. és 12. szakaszában szerepelnek. Az ISO-út lehetséges; a teljes folyamat nem csak azt jelenti. | `src/picasapy/burn/ajandek_cd.py:81-125` ISO 9660/Joliet lemezképet épít a kimeneti út mellett ideiglenes könyvtárban, majd `os.replace`-szel helyezi végleges helyére. A kimeneti builder nem tesz `.picasa.ini`-t az ISO-ba. | A kimeneti formátum ismert. A forrásmappában lévő `.picasa.ini`, a helyi index, a bal hasáb, a rács és a kijelölés futás utáni állapotáról egyik útvonalhoz sincs megfelelő előtte/utána felvétel. Ezekre nincs igazolt javítási jegy. |
| Írási folyamat és állapot: `0x00672f50` kezeli többek között a `Preparing to write`, `Writing...`, `Verifying...`, `Finishing Disc`, `Writing complete!` állapotokat; `0x00678630` tartalmazza a `CD in Progress`/`Disc Done` állapotot. `0x00672380` kezeli a `Not Enough Disk Space on Drive` esetet. | A PicasaPy munka háttérszálas (`ajandek_cd_controller.py:87-103`); a panel csak `dolgozik` állapotban tiltja az újraindítást (`PublishPanel.qml:58-64`, `256-263`). Az elkészült lemezkép vagy hiba a `GiftCdHost.qml:94-105` útján jelenik meg; százalékos haladási felületet ez az út nem tartalmaz. | A részletes folyamatjelzés és a fizikai lemezkapacitás állapotai eltérnek. D4 javasolt, ha a felhasználónak a háttérmunka alatt látható előrehaladás és megszakítható művelet kell. |
| Nincs író: `0x00673de0` „Unable to find an available CD drive...” kérdése; lemezellenőrzési hiba: „Unable to check disc. Please try again”. Írási/engine hibaágak: `0x00671ef0`, `0x00672f50`; ISO felülírási hiba: `0x00674c00` (`Unable to overwrite file`). Újraírható, fájlokat tartalmazó lemeznél `0x006755f0` törlési jóváhagyást kér. | A worker általános kivételt naplóz, üres eredményt jelez, majd a QML hibaablakot nyit (`ajandek_cd_controller.py:105-127`, `GiftCdHost.qml:97-105`, `155-169`). A sikertelen egyedi exportokat a sikerablak darabszámmal közli (`GiftCdHost.qml:128-135`). | A konkrét hálózati vagy írásvédett cél, fizikai lemezhiba és törlési jóváhagyás eredménye nem mérhető a statikus ágakból. Ezeknél `NINCS MEG`; a tetszőleges kivétel kezelése nem bizonyítja a felhasználói kimenet megfelelőségét. |
| Futó írás megszakítása: `0x0067be30` `Do you want to cancel your current burn?` kérdést és `Don't Cancel` / `Cancel Burn` gombot állít elő; az igen ág megszakítási metódust hív. A félbehagyott lemez tartalma, a gomb pontos állapota és a visszavonás eredménye nincs futtatott felvétellel igazolva. | A vizsgált `GiftCdHost.qml:73-78` Cancel eseménye bezárja a panelt. A worker indításához nincs ezen az útvonalon leállítási jel vagy megszakítás gomb. | A megszakítás viselkedése eltér. A visszavonási eredmény, a lemezen maradó adatok és az undo állapota mindkét termékben `NINCS MEG`. Lásd D4. |

## A folyamat bizonyított elemei

### Belépés és ablak

Az `ajandek-cd-kimenet.md` 9. szakasza a `eMenuCreate::ID_BURNCD` menüpontot, a `thumbui/cdmode` főnézeti elemet és a `publish/presentcd_go` indítógombot aktívként írja le; a két fejléc-paneles `create_cd` elemet kommenteltként dokumentálja. A menücímke ampersandja menün belüli billentyű-mnemonikát ad. Helyi menü vagy a parancsot közvetlenül indító globális gyorsbillentyű nincs bizonyítva.

Az eredeti `publish` erőforrás a kijelölés és beállítások paneljét tartalmazza, méretválasztóval, CD név mezővel és három jelölővel. Az `ajandek-cd-kimenet.md` 11. szakasza a diavetítés és a Picasa telepítő kapcsolójának `1` alapértékét és beállításkulcsait rögzíti. A `CDEraseFirst` állapotot a teljes pásztázás kulcshivatkozásai alátámasztják, de az átállított érték elmentését nem.

A meghajtóválasztó feltételét két külön út támasztja alá: az utasítások `0x0066b6a0` alatt `esi < 2` esetén elágaznak a választó felépítése elől, és a külön `cdchoose.fen` statikus erőforrás kifejezetten több íróról kérdez. Ez megerősíti a több meghajtós dialógus célját, nem bizonyítja az ablak tényleges futásidejű megjelenését.

### Kimenet és állapot

Az eredeti fizikai írás folyamatában a lemezellenőrzés megelőzi az írást; hiányzó meghajtónál ISO-kimenet választható. A progress függvény külön írja ki az előkészítés, írás, ellenőrzés, befejezés és hiba állapotait. A kapcsolódó kimeneti specben már megvannak a lemezre kerülő fájlok és az opciós ágak; ezt a lapot változatlanul hagytam.

A PicasaPy controller a képtálca pillanatképéből épít ISO-t háttérszálon. A QML ISO mentőablakot és kész/hiba párbeszédet mutat. A controller/builder vizsgált részében nincs explicit `.picasa.ini` írás vagy indexfrissítés, de futás utáni mérés hiányában ezt nem emelem teljes alkalmazásszintű negatív állítássá.

## A két független út

- **A, bináris vezérlés:** az `0x00679ca0` callbacket az Ajándék-CD `publish/presentcd_go` útjához követtem; ez a `0x00673de0` kapuhoz jut. A meghajtólistát, beállításokat, írási állapotokat és törlési/megszakítási ágakat a pontos méretű függvények utasításszintű olvasása adta.
- **B, külön felület- és forrásút:** az eredeti `runtime/cdchoose.fen` dialógusleírása, a `publish`/`thumbui` elemeket felsoroló meglévő spec, valamint a PicasaPy QML és Python bekötése. A statikus meghajtóablak szövege egyezik az A út több meghajtós ágával; a PicasaPy kód külön ISO célválasztást mutat.
- **Egyezés:** a dialógus célja, az ISO ág és a PicasaPy ISO-only út a két leírásban egyezik. **Nem igazolt:** tényleges menüengedélyezés az eredeti futásban, az ablakok futtatott állapota, a helyi index/könyvtár utóhatása, a hálózati és írásvédett hibák, valamint a megszakítás utáni állapot.

## Cáfoló kísérlet

Az első olvasat szerint a törlési jelölőhöz nem tartozik megjegyzett beállítás, mert a korábban vizsgált `0x0066f470` `option_*` olvasóban nincs ilyen kulcs. Ezt a következtetést cáfoltam a teljes, memóriakapus `.text` pásztázással: a `CDEraseFirst` kulcs címe három közvetlen kódbeli hivatkozásban szerepel. A `0x006706d0` beolvasáskor 1-es alapértéket ad, a `0x00675710` az írási ág előtt ismét beolvassa. A cáfoló a kulcs létezését és használatát megerősíti; az érték módosítás utáni mentését nem bizonyítja, ezért ezt nyitottként hagytam.

## A jegy „Kész, ha” pontjai

1. ⛔ **Belépési pontok és feltétel:** a menü, a főnézeti `thumbui/cdmode`, a panel gombja és a két kikapcsolt fejléc-elem azonosítva. A helyi menü, globális gyorsbillentyű és az eredeti menü aktiválási feltétele nyitott.
2. ⛔ **Ablak, mezők, alapértékek, megjegyzett állapot:** a panel statikus mezői, három opciója, méretfokozatai, a több meghajtós választó és a fontos alapértékek ismertek. Az eredeti futtatott megjelenés, a `CDEraseFirst` átállítás mentése és a névmező esetleges felülírása nyitott.
3. ⛔ **Hatás:** a fizikai lemez és ISO kimeneti útja, a PicasaPy ISO builder, háttérszál és visszajelzés ismert. A `.picasa.ini`, index, bal hasáb, rács és kijelölés művelet utáni állapota nincs mérve.
4. ⛔ **Hiba, megszakítás, hálózati vagy írásvédett hely, visszavonás:** néhány eredeti kérdés és hibaág statikusan olvasható. A hálózat, írásvédelem, félbeszakított írás maradványa és undo hatása nincs megmérve.

## Javasolt fejlesztői jegytörzsek

Az alábbiak javaslatok, nem megnyitott jegyek. A fizikai író támogatását külön termékdöntésként kell kezelni; a jelenlegi ISO célút ettől még működő PicasaPy-kimenet.

### D1. Ajándék-CD belépési pontjainak paritása

**Eredeti:** `0x00559150` (`eMenuCreate::ID_BURNCD`), `0x005cb990` / `0x005d9cc0` / `0x005e0f70` (`thumbui/cdmode`), `0x0066bf90` (`publish` panel).

**Nálunk:** `PicasaCreateMenu.qml:46-50` és `MainMenuBar.qml:343`.

**Teendő:** a Létrehozás menü mellett tegyük elérhetővé az Ajándék-CD panelt a főnézet megfelelő módgombjáról is, és ugyanarra a hostra irányítsuk mindkét utat. Az eredeti menü- és kijelölési feltételt futtatott méréssel kell felvenni, mielőtt a PicasaPy kapuját hozzáigazítjuk.

**Kész, ha:** mindkét igazolt belépés ugyanazt a panelt nyitja; a panelelem/menü engedélyezése a rögzített eredeti feltételt követi; helyi menüt vagy globális gyorsbillentyűt csak külön bizonyíték után adunk hozzá.

### D2. Fizikai meghajtó és ISO célválasztás

**Eredeti:** `0x0066b6a0` (több író választása), `0x00673de0` (meghajtó-ellenőrzés és ISO-fallback), `0x00674460`, `0x00674c00` (ISO mentés).

**Nálunk:** `GiftCdHost.qml:81-92` mindig `.iso` mentőablakot nyit.

**Teendő:** ha a termék támogat fizikai írást, adjunk célválasztót az elérhető meghajtóknak, több író esetén választóablakot, és meghajtó hiányakor maradjon választható az ISO-kimenet. A korábbi meghajtó előválasztását csak az írási irány bizonyítása után tegyük tartóssá.

**Kész, ha:** fizikai író és ISO cél is választható; több írónál a kiválasztás egyértelmű; nulla írónál a felhasználó ISO-ra válthat vagy visszaléphet; hálózati és írásvédett ISO célra mért hibaüzenet jelenik meg.

### D3. A támogatott opciók állapota

**Eredeti:** `0x0066f470` (méret és vetítő/telepítő opciók), `0x006710ca` (`CDEraseFirst` beolvasás), `0x006757c3` (törlés előtti beolvasás).

**Nálunk:** `PublishPanel.qml:179-197`, `234-249`; tartós diavetítő-beállítás `ajandek_cd_controller.py:54-68`.

**Teendő:** a fizikai lemezírás célba vétele esetén az eredetihez illő, platformon támogatott kapcsolókat kössük tényleges kimeneti viselkedéshez, és az állapotot nyissuk vissza ugyanazzal a beállítással. Az `Include Picasa` opció csak akkor kerüljön be, ha a hozzá tartozó telepítőcsomag szállítható.

**Kész, ha:** a képméret, diavetítés, Picasa tartozékok és lemeztörlés látható állapota pontosan az implementált kimenetet kapcsolja; a megjegyzett érték újranyitás és újraindítás után a mért szerződés szerint áll vissza.

### D4. Haladás és megszakítás

**Eredeti:** `0x00672f50` (írási/ellenőrzési haladás), `0x00678630` (háttérállapot), `0x0067be30` (megszakítás megerősítése).

**Nálunk:** háttérszál `ajandek_cd_controller.py:87-127`; a Cancel `GiftCdHost.qml:73-78` csak bezárja a panelt.

**Teendő:** a háttérmunka adjon látható haladást, és futás alatt a megszakítási kérés jusson el a workerhez. A befejezés, hiba és megszakítás külön kimeneti állapotot kapjon.

**Kész, ha:** munka közben látszik az állapot és nem indítható második művelet; a megszakítás megerősítés után leállítja az aktuális munkát; a felület nem jelez sikert részleges ISO után.

### D5. A CD név mező alapértéke

**Eredeti:** `0x0067c5e9-0x0067c5f3` a `PicasaCDName` erőforrás `Picasa CD` tartalékértékét tölti be, a konstruktor egyik módágában.

**Nálunk:** `GiftCdHost.qml:48-50` megnyitáskor az aktuális mappa utolsó elemét állítja a névmezőbe.

**Teendő:** a fenti eredeti ágat futtatott méréssel kell összevetni az aktuális mappa nevével és az esetleges korábbi névvel. Csak ezután igazítsuk a PicasaPy alapértékét.

**Kész, ha:** ugyanazon megnyitási helyzetben a CD név mező induló értéke és újranyitás utáni viselkedése megegyezik a mért szerződéssel.

## Nyitott

- `NINCS MEG`: az eredeti program futtatott állapotfelvétele a 7305 folyamatról. Konkrét beszerzési út: a Picasa 3.9 hashével egyező eredeti rendszeren mérni kell az aktív menü/módgomb megnyitását, panel állapotát, fizikai íróval és író nélkül futó műveletet, majd előtte/utána `.picasa.ini`, index, kijelölés, rács és bal hasáb állapotot.
- `NINCS MEG`: a `Preferences\\CDEraseFirst` módosítás utáni tényleges mentése; a teljes pásztázás megtalálta mindhárom közvetlen kódbeli hivatkozást, de a kulcs-író viselkedés nem igazolt.
- `NINCS MEG`: a `Preferences\\lastcddriveused` új választás után frissül-e, vagy csak korábban rögzített értékből állítja vissza a listát.
- `NINCS MEG`: a PicasaCDName `Picasa CD` tartalékértéke mellett pontosan mely megnyitási állapot ad felülírt nevet.
- `NINCS MEG`: helyi menü vagy globális billentyűparancs az eredeti Picasában.
- `NINCS MEG`: hálózati/írásvédett cél, lemezhiba, megszakítás utáni részleges adat, valamint a művelet visszavonásának hatása.
- Ghidra-kör nem szükséges a fenti, címzett kérdésekhez; a nyitottságot a hiányzó futtatott mérés és az állapotírás nem eldöntött útja okozza.

## Módosított fájlok

- `docs/specs/paritas-folyamat-7305.md`: a #7305 teljes folyamatának statikus összevetése, bizonyítéki korlátokkal és nyitott mérési pontokkal.
- `docs/specs/00-index.md`: új tartalomjegyzék-sor ehhez a laphoz.
