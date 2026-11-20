# Az Ajándék-CD teljes folyamata az eredeti Picasával összevetve: belépési pontok, ablak, hatás

## Következtetés

Az eredeti Picasa 3.9 méréseiben a `Create a Gift CD...` menüpont 0 és 3 kijelölt képnél is aktív, és mindkét esetben a bejelölt `PicasaTeszt (24)` mappát teszi a CD tartalmává. A panel alapértékei mindkét felvételen `PicasaTeszt`, `Original Size` és bekapcsolt diavetítés; a név és a diavetítés módosítása a panel bezárása és újranyitása után visszaállt. Ez eltér a PicasaPy tálcaalapú bemenetétől és az azonnal tartósított diavetítés-beállítástól.

A #792 mérés nem jutott el az író nélküli Burn Disc kérdésig vagy az ISO mentőablakig: a panel megnyitásakor az IMAPI2-hibaablak jelent meg, de a Burn Disc-kattintás utáni képeken csak a panel látszik. Ezért az eredeti kérdés és az ISO mentőablak futásidejű neve/mappája **NINCS MEG**. A belépési módok, művelet utáni fájl/indexállapot, hálózati vagy írásvédett cél és megszakítás további mérése is nyitott.

## Módszer és bizonyítottság

- Vizsgált bináris: Picasa 3.9.141.259, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. A fájlt nem futtattam és nem másoltam a munkafába.
- A korábbi statikus kutatáshoz tartozó `ajandek-cd-kimenet.md` felvételeit külön kezeltem. E kiegészítő kör közvetlen mérőanyaga a megadott `m7305/terv.md` és a j790-j793 futások (#790-#793), a `kepernyo__NN.png`, `allapot.json` és `kepmappa__lista.json` állományokkal; ezekből csak a döntési szabály szerinti bizonyítékot használtam.
- Az eredeti binárisból az indexben meghatározott méretű függvényeket az `annot_disasm.py` eszközzel olvastam. A teljes `.text` pásztázás kizárólag a `paszta.utasitasok()` útján futott, a `paszta.memoria_kapu()` első műveletként.
- Összesített bizonyítottsági fok: **feltételes**. A menü és panel alapállapotát két külön futás rögzíti; az újranyitás egy, a Burn Disc út egy sikertelen célállapotú futásból ismert. A teljes folyamat, a PicasaPy futásidejű viselkedése és a lemezművelet utóhatása nem igazolt.

## Futtatott mérés: a panel és az újranyitás (#790-#793)

| Mérés | Képernyőkép / adat | Megfigyelés |
|---|---|---|
| #790, 0 kijelölt kép | `kepernyo__07`, `kepernyo__12` | A `Create a Gift CD...` menütétel aktív. Megnyílik a panel; a bal oldali `Folders (1)` alatt a `PicasaTeszt (24)` mappa be van jelölve. A CD Name `PicasaTeszt`, a Photo Size `Original Size`, az Include Slideshow bejelölt, az Include Picasa szürke; a Burn Disc aktív. Az állapotsor `Calculating (24) 24 files 10.1 MB Est. 1 CD or 1 DVD` értéket mutatja. |
| #791, 3 kijelölt kép | `kepernyo__13`, `kepernyo__18` | A menütétel aktív és ugyanaz a panel nyílik. A három mező értéke változatlan, a `PicasaTeszt (24)` mappa bejelölt, az állapotsor továbbra is 24 fájlt számlál. A három képes kijelölés nem változtatja meg az alapértelmezett tartalomkészletet ebben a próbában. |
| #792, Burn Disc író nélkül | `kepernyo__14`, `kepernyo__19`-`25`, `allapot.json` | A panel megnyitásakor `Confirm` ablak jelenik meg: `Unable to connect to Windows IMAPI2 CD Engine. Click OK to open the troubleshooting webpage.`; gombjai `OK` és `No`. Az Escape után a panel visszatér. A Burn Disc-kattintás után nem jelenik meg új kérdés vagy mentőablak; a képek és az ablaklista a Picasa panelt mutatják. A tervezett íróhiányos kérdés/ISO állapot **nem valósult meg**, ezért erről a futásról nincs következtetés. |
| #793, módosítás és újranyitás | `kepernyo__22`, `kepernyo__24`, `kepernyo__26`, `kepernyo__32` | A CD Name `ProbaCD`-re változik, az Include Slideshow kikapcsolható. A Cancel visszatér a könyvtárba, ahol a 3 képes kijelölés és a Selection tálca megmarad. A menüből újranyitott panelen a CD Name ismét `PicasaTeszt`, a diavetítés pedig bejelölt. A Photo Size megjegyzett állapotát ez a futás nem tesztelte. |

Minden itt közölt szám és felirat képernyőképről vagy a futás állapot-JSON-jából származik. A `.picasa.ini` tartalmáról és a helyi indexről ezek a feladatok nem adnak mérést.

## Eredeti / nálunk / teendő

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `eMenuCreate::ID_BURNCD`, `0x00559150`: a Létrehozás menü `Create a &Gift CD...` tétele. A `&` menün belüli billentyű-mnemonikát jelöl, nem igazolt globális gyorsbillentyűt. A #790/#791 felvételen 0 és 3 képkijelölés mellett is aktív. | `src/picasapy/app/qml/PicasaPy/PicasaCreateMenu.qml:46-50`; a kapu `MainMenuBar.qml:165-167`; az esemény bekötése `MainMenuBar.qml:343`. A PicasaPy a menüt kijelölt képpel vagy nem üres tálcával engedélyezi. | Mért eltérés: az eredeti 0 kijelöléssel, üres tálca mellett is megnyitja a panelt; a mostani PicasaPy-kapu ekkor tilt. A teljes tartalomkészlet is eltér: az eredeti a `PicasaTeszt (24)` mappát pipálja be és 24 fájlt számlál, a PicasaPy a képtálcát adja át. Lásd D1. |
| Aktív főnézeti módgomb `thumbui/cdmode`; kezelőcímek `0x005cb990`, `0x005d9cc0`, `0x005e0f70`. A panel saját indítógombja `publish/presentcd_go`, melynek ágát a `0x00679ca0` kezeli. A `headerpanel/create_cd` és `faceheaderpanel/create_cd` a meglévő lapon hivatkozott `.tre`-fájlokban kommentelt, kikapcsolt elem. | A vizsgált PicasaPy útvonal a Létrehozás menüből indul (`PicasaCreateMenu.qml:46-50`, `MainMenuBar.qml:343`). A `publish/presentcd_go` megfelelője `PublishPanel.qml:256-263`. | A `thumbui/cdmode`-nak nincs azonosított PicasaPy-beli párja; a két kikapcsolt fejlécgomb nem eltérés. Helyi menü útvonalat nem igazoltam, ezért annak hiányát nem állítom. Lásd D1. |
| Több író esetén meghajtóválasztó: `0x0066b6a0` vizsgálja a meghajtók számát; a `cdchoose` erőforrást a `0x0066b2d0` építi. A statikus `runtime/cdchoose.fen` szövege szerint egynél több meghajtónál `Drives:` listából lehet választani, OK/Cancel gombbal. A `Preferences\\lastcddriveused` értéket a `0x0066b430` és `0x0066b6a0` olvassa a korábbi választás előállításához. | `src/picasapy/app/qml/PicasaPy/GiftCdHost.qml:81-92`: fájlmentő párbeszéd ISO szűrővel, alapértelmezett Képek mappával. Meghajtólistát nem nyit. | Eltérő célválasztás. A binárisban a korábban használt meghajtó beolvasása bizonyított; annak írása új választás után nem bizonyított. D2 csak akkor, ha fizikai író támogatása cél. |
| Ajándék-CD beállításai: `0x0066f470` méretértékei 0, 640, 800, 1600; a statikus olvasóban a diavetítés alapértéke 1. A #790/#791 felvételen a Photo Size `Original Size`, az Include Slideshow bejelölt. A #793 felvételen a kikapcsolt diavetítés a panel bezárása/újranyitása után ismét bejelölt. | `PublishPanel.qml:179-197` adja a diavetítés-jelölőt és a négy méretet. A CD név nyitáskori értéke `GiftCdHost.qml:48-50`; a diavetítés állapotát `ajandek_cd_controller.py:54-68` QSettings-be menti, `GiftCdHost.qml:63-77` pedig ezt tölti vissza. | Az alapértékek a mért esetben egyeznek, de a megjegyzési időzítés eltér: Picasa a Mégse és az újranyitás után visszaállítja, a PicasaPy kattintáskor azonnal tartósította (a #7315 javítja). A Photo Size módosítás utáni visszaállítása, a Picasa telepítő/törlés opciók futtatott viselkedése és a `CDEraseFirst` mentése nyitott. Lásd D3. |
| A `publish` panel kimenetét a felületen bepipált mappa jelöli: #790/#791 alatt `PicasaTeszt (24)`, 24 fájl. A `0x00673de0` íróhiány esetén ISO ágat tartalmaz; a mentőablakot a `0x00674c00` építi `CD%d.iso`, `ISO Files` / `*.iso` szűrővel. A #792 nem jutott el ehhez az ághoz. | `GiftCdHost.qml:63-78` a tálca elemszámát adja át; `ajandek_cd_controller.py:89-103` a tálcarekordokból készít bemenetet; `GiftCdHost.qml:81-92` ISO célválasztót nyit. | A mérések a PicasaPy ISO-only és az eredeti fizikai író út különbségét nem zárják le. A #792-ben sem a hiányzó-író kérdés, sem a `CD%d.iso` mentőablak, sem annak mappája nem jelent meg; ezeket a futásidejű adatokat ne tekintsük mértnek. Lásd D2. |
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

- **A, statikus bináris és erőforrás:** az `0x00679ca0` callbacket az Ajándék-CD `publish/presentcd_go` útjához követtem; ez a `0x00673de0` kapuhoz jut. A függvények és a `runtime/cdchoose.fen` a meghajtó-, beállítás-, írás- és megszakítási ágakat írják le.
- **B, eredeti futás:** a #790-#793 felvételek képei és állapot-JSON-jai. A #790 és #791 két külön futása ugyanazt az aktív menüt, panelt és alapértékeket mutatja; a #793 egy újranyitási próbát ad.
- **PicasaPy-összevetés:** a QML/Python-forrás a saját belépési feltételt, tálcaalapú bemenetet és beállításmentést adja.
- **Egyezés és határ:** A statikus út azonosítja a panel és írási ágak szerkezetét; B adja a futásidejű állapotokat. A két független futás megerősíti a 0/3 kijelölésnél mért panelalapértékeket. A #792 nem erősítette meg az íróhiányos kérdést; a hálózati/írásvédett hibák, művelet utáni helyi index és `.picasa.ini`, valamint a megszakítás maradványa nyitott.

## Cáfoló kísérlet

Az első olvasat szerint a törlési jelölőhöz nem tartozik megjegyzett beállítás, mert a korábban vizsgált `0x0066f470` `option_*` olvasóban nincs ilyen kulcs. Ezt a következtetést cáfoltam a teljes, memóriakapus `.text` pásztázással: a `CDEraseFirst` kulcs címe három közvetlen kódbeli hivatkozásban szerepel. A `0x006706d0` beolvasáskor 1-es alapértéket ad, a `0x00675710` az írási ág előtt ismét beolvassa. A cáfoló a kulcs létezését és használatát megerősíti; az érték módosítás utáni mentését nem bizonyítja, ezért ezt nyitottként hagytam.

A friss feltevést - „Ajándék-CD csak kijelölt képpel nyitható” - az ellenkező állapotban próbáltam cáfolni. A #790 `kepernyo__07` képen 0 kijelölt képnél is aktív a menüpont, és a `kepernyo__12` képen megnyílik a panel; a feltevés hamis. A #791 másik futása 3 kijelölésnél ugyanazt a `PicasaTeszt (24)` / 24 fájlos alapot mutatja.

A #792 Burn Disc próbáját a saját mércével ellenőriztem: a #792 `allapot.json` szerint a Burn Disc-kattintás utáni lépésekben az ablaklista csak `Picasa 3`-at tartalmaz; a képernyőképek szintén a panelt mutatják. Ez nem cáfolja az eredeti bináris íróhiányos ágát, hanem azt mutatja, hogy ez a mérés nem váltotta ki a tervezett állapotot.

## A jegy „Kész, ha” pontjai

1. ⛔ **Belépési pontok és feltétel:** a Létrehozás menü 0 és 3 kijelölésnél aktív; a panel megnyílik. A `thumbui/cdmode` és kikapcsolt fejlécelemek statikusan azonosítottak, de a helyi menü és globális gyorsbillentyű nincs futásban mérve.
2. ⛔ **Ablak, mezők, alapértékek, megjegyzett állapot:** a két alapállapot-felvétel és a CD-név/diavetítés Cancel utáni újranyitása megvan. A Photo Size módosítás utáni állapota, újraindítás utáni viselkedés, `CDEraseFirst` mentése és a Burn Disc kérdése nyitott.
3. ⛔ **Hatás:** a bal hasábban bejelölt `PicasaTeszt (24)`, a 24 fájlos állapotsor és a Cancel után megmaradó 3-as kijelölés megvan. Burn/ISO művelet nem történt; `.picasa.ini`, index, fájlrendszer, rács és kijelölés írás utáni állapotáról nincs mérés.
4. ⛔ **Hiba, megszakítás, hálózati vagy írásvédett hely, visszavonás:** az IMAPI2-panelnyitási hiba mért. A tervezett íróhiányos kérdés, az ISO mentőablak és célmappája, hálózat, írásvédelem, félbeszakított írás maradványa és undo hatása nincs megmérve.

## Javasolt fejlesztői jegytörzsek

Az alábbiak javaslatok, nem megnyitott jegyek. A fizikai író támogatását külön termékdöntésként kell kezelni; a jelenlegi ISO célút ettől még működő PicasaPy-kimenet.

### D1. Ajándék-CD belépési pontjainak paritása

**Eredeti:** `0x00559150` (`eMenuCreate::ID_BURNCD`); a #790 `kepernyo__07` és #791 `kepernyo__13` szerint a menü 0 és 3 kijelölésnél is aktív. Mindkét panelen a `PicasaTeszt (24)` mappa van bejelölve, 24 fájlos számlálóval (#790 `kepernyo__12`, #791 `kepernyo__18`). A főnézeti `thumbui/cdmode` statikus címei `0x005cb990` / `0x005d9cc0` / `0x005e0f70`.

**Nálunk:** `PicasaCreateMenu.qml:46-50` és `MainMenuBar.qml:165-167`; a `GiftCdHost.qml:65-66` a tálcát számolja, az `ajandek_cd_controller.py:89-100` a tálcarekordokat adja át.

**Teendő:** adjunk Gift-CD-specifikus kaput és forráskészletet: kijelölés és üres tálca mellett a menü nyíljon, az aktuális mappa legyen az alapértelmezett kijelölt forrás; 3 képkijelölés mellett se váltsa le automatikusan a 24 képes, kipipált mappát a képtálca három elemére. A PicasaPy főnézeti módgombja legyen elérhető, ha a `thumbui/cdmode` paritás része ennek a fejlesztésnek. Helyi menüt vagy globális gyorsbillentyűt ne vezessünk be bizonyíték nélkül.

**Kész, ha:** 0 kijelölt kép és üres tálca esetén a menü aktív és a kiválasztott mappa fájljait számlálja; 3 kijelölt kép esetén az alapértelmezett tartalom továbbra is a mappa, amíg a felhasználó a panelen át nem állítja; mindkét esetben a Burn Disc az eredetihez mért fájlszám szerint engedélyezett. A módgomb ugyanazt a panelt nyitja, ha megvalósítjuk.

### D2. Fizikai meghajtó és ISO célválasztás

**Eredeti:** `0x0066b6a0` (több író választása), `0x00673de0` (meghajtó-ellenőrzés és ISO-fallback), `0x00674460`, `0x00674c00` (ISO mentés).

**Nálunk:** `GiftCdHost.qml:81-92` mindig `.iso` mentőablakot nyit.

**Teendő:** ha a termék támogat fizikai írást, adjunk célválasztót az elérhető meghajtóknak, több író esetén választóablakot, és meghajtó hiányakor maradjon választható az ISO-kimenet. A #792 mérés nem igazolta a Burn Disc utáni kérdést vagy az ISO mentőablakot; a statikus `CD%d.iso` alapnév és `*.iso` szűrő ne legyen futásidejű paritásként idézve, a célmappát pedig ne állítsuk, amíg új mérés nem rögzíti.

**Kész, ha:** fizikai író és ISO cél is választható; több írónál a kiválasztás egyértelmű; nulla írónál a felhasználó ISO-ra válthat vagy visszaléphet; hálózati és írásvédett ISO célra mért hibaüzenet jelenik meg.

### D3. A támogatott opciók állapota

**Eredeti:** `0x0066f470` (méret és vetítő/telepítő opciók), `0x006710ca` (`CDEraseFirst` beolvasás), `0x006757c3` (törlés előtti beolvasás).

**Nálunk:** `PublishPanel.qml:179-197`, `234-249`; tartós diavetítő-beállítás `ajandek_cd_controller.py:54-68`.

**Teendő:** az Include Slideshow állapotát a panelben ideiglenesen tartsuk; Cancel után az újranyitott panelen a #793 szerint vissza kell állnia a bejelölt alapértékre. Ne mentsük QSettings-be kattintáskor. A sikeres írás utáni mentési szabályt és az újraindítás utáni állapotot külön mérés döntse el. Az `Include Picasa` opció csak akkor kerüljön be, ha a hozzá tartozó telepítőcsomag szállítható.

**Kész, ha:** a #790/#791 alapértékek (`Original Size`, Include Slideshow be) megegyeznek; a #793 szerinti kikapcsolás és Cancel után a következő megnyitás visszatér a bejelölt alapra; sikeres Burn és alkalmazás-újraindítás utáni mentési szabályról csak külön mérés után állítunk.

### D4. Haladás és megszakítás

**Eredeti:** `0x00672f50` (írási/ellenőrzési haladás), `0x00678630` (háttérállapot), `0x0067be30` (megszakítás megerősítése).

**Nálunk:** háttérszál `ajandek_cd_controller.py:87-127`; a Cancel `GiftCdHost.qml:73-78` csak bezárja a panelt.

**Teendő:** a háttérmunka adjon látható haladást, és futás alatt a megszakítási kérés jusson el a workerhez. A befejezés, hiba és megszakítás külön kimeneti állapotot kapjon.

**Kész, ha:** munka közben látszik az állapot és nem indítható második művelet; a megszakítás megerősítés után leállítja az aktuális munkát; a felület nem jelez sikert részleges ISO után.

### D5. A CD név mező alapértéke - mért egyezés

**Eredeti:** `0x0067c5e9-0x0067c5f3` a `PicasaCDName` erőforrás `Picasa CD` tartalékértékét tölti be, a konstruktor egyik módágában.

**Nálunk:** `GiftCdHost.qml:48-50` megnyitáskor az aktuális mappa utolsó elemét állítja a névmezőbe.

**Teendő:** nincs fejlesztési jegy a mért esetre. A #790/#791 felvételen az eredeti név `PicasaTeszt`; a #793 módosítás után, a panel újranyitásakor a mező visszatér `PicasaTeszt`-re. Ez egyezik a `GiftCdHost.qml:48-50` aktuális mappanév-alapú újrainicializálásával.

**Nyitva:** más megnyitási módban a statikus `Picasa CD` tartalékérték tényleges használata; alkalmazás-újraindítás utáni névállapot.

## Nyitott

- `NINCS MEG`: a #792 tervezett Burn Disc íróhiányos kérdése, az igen ág ISO mentőablaka, annak futásidejű alapneve és mappája. Megszerzés: a Burn Disc gomb aktiválását és az Igen ágát tartalmazó eredeti Colab-felvétel, amelyben a képek ténylegesen mutatják a kérdést és mentőablakot.
- `NINCS MEG`: fizikai íróval végzett futás és a fájl/index/`.picasa.ini` változásai. A Burn Disc nem váltott ki látható célműveletet a #792-ben; `.picasa.ini`, index, bal hasáb, rács és kijelölés írás utáni állapota ezért nincs megmérve.
- `NINCS MEG`: az eredeti futásidejű módgomb, helyi menü, globális gyorsbillentyű és menüállapot más mappákkal/profilokkal; a #790/#791 csak a Létrehozás menüt mérte a PicasaTeszt mappán.
- `NINCS MEG`: a `Preferences\\CDEraseFirst` módosítás utáni tényleges mentése; a teljes pásztázás megtalálta mindhárom közvetlen kódbeli hivatkozást, de a kulcs-író viselkedés nem igazolt.
- `NINCS MEG`: a `Preferences\\lastcddriveused` új választás után frissül-e, vagy csak korábban rögzített értékből állítja vissza a listát.
- `NINCS MEG`: a `PicasaCDName` `Picasa CD` tartalékértékét mely megnyitási helyzet használja; a mért `PicasaTeszt` mappa esetén a név-egyezés és Cancel utáni visszaállás megerősített.
- `NINCS MEG`: a Photo Size kiválasztásának mentése/újranyitása és az Include Slideshow állapota sikeres CD-készítés, illetve alkalmazás-újraindítás után. A #793 csak Cancel utáni újranyitást mérte.
- `NINCS MEG`: helyi menü vagy globális billentyűparancs az eredeti Picasában.
- `NINCS MEG`: hálózati/írásvédett cél, lemezhiba, megszakítás utáni részleges adat, valamint a művelet visszavonásának hatása.
- Ghidra-kör nem szükséges a fenti, címzett kérdésekhez; a nyitottságot a hiányzó futtatott mérés és az állapotírás nem eldöntött útja okozza.

## Módosított fájlok

- `docs/specs/paritas-folyamat-7305.md`: a statikus összevetés kiegészült a #790-#793 futásidejű eredményekkel és az el nem ért Burn Disc ággal.
- `docs/specs/00-index.md`: frissült a lap összefoglalója.
