# Picasa képernyőkép-rögzítése (#5608, 2026-10-23)

Az eredeti Picasa 3 képernyőkép-készítő útja. A rögzítést végző függvény a
`0x00590f40`; a billentyűt figyelő metódus a `0x00591470`. A `Scrapture`
osztálynevet visszaadó függvény `0x00590ec0`.

## 1. Indítás

Az induláskori állapotkezelő (`0x0040bf70`) a `Preferences` szekció
`EnableScreenCap` kulcsát olvassa. A kiolvasás előtt az alapérték DWORD-ja
`1` (`0x0040ca13`); a `0x00407a20` az általános beállításolvasó. Ez
HKCU-t ad át (`HKEY_CURRENT_USER`, `0x80000001`, `0x00407a3b`) a
`0x00408060` kulcsútvonal-olvasónak; a szekció és kulcs itt
`Preferences\EnableScreenCap`. Ugyanebben a kódrészben a függvény létrehozza
a `Scrapture` objektumot (`0x0040ca49`-`0x0040ca75`), majd meghívja a
`0x0097b350` szálindítót (`0x0040ca78`). A `0x004019b0` a beolvasott értéket
adja vissza (`0x0040ca24`); a függvény nulla ellen hasonlítja
(`0x0040ca41`), és nulla esetén a `0x0040ca9d` címre ugrik, az objektum- és
szálindító ág mögé. Nem nulla értéknél végrehajtja az objektumlétrehozást,
majd a szálindítást. A `EnableScreenCap` alapértéke tehát `1`; a `0` letiltja
ezt a figyelőszálat.

A szál belépője `0x0097aeb0`; a vtable `+0x08` rekeszéből hívja a
`0x00591470` metódust. Ez a metódus először a `Scrapture` vtable `+0x04`
rekeszén hív egy állapotvizsgálót (`0x0059147d`-`0x00591488`; a nyers
vtable-ben a rekesz `0x00408b30`-ra mutat). Nem nulla `AL`-eredménynél
kilép; nulla eredménynél lekérdezi a `GetAsyncKeyState`-tel a
`VK_SNAPSHOT` (`0x2c`), majd: ha az nem aktív: a `VK_PRINT` (`0x2a`)
billentyűt; mindkét esetben a `GetAsyncKeyState` eredményének 15. bitjét
vizsgálja. Bármelyik aktív állapota rögzítést indít; felengedési élre nem
vár. A `0x005914f1`
közvetlenül hívja a `0x00590f40`-et. A Ctrl (`0x11`) állapota `0` vagy
`1` célmódot ad át, Alt (`0x12`) esetén pedig a `GetCursorPos` →
`WindowFromPoint` eredménye kerül célként átadásra; az Alt-ág megelőzi a
Ctrl-módot. A rögzítés után a metódus `WaitForSingleObject`-ot hív a
`DAT_00d689cc` fogantyúra `0x7d0` milliszekundumos időkorláttal, majd
`Sleep(0x14)` következik; ezután újra meghívja a vtable `+0x04` állapotvizsgálót
(`0x0059150f`-`0x00591518`), és nulla eredménynél visszatér a
billentyű-lekérdezéshez. A vtable-metódus állapotának jelentése és
kapcsolata az `EnableScreenCap` beállítással **NINCS MEG**. A vizsgált út
tehát háttérszálas, ismételt billentyű-lekérdezés. A `paszta.py` teljes `.text`
pásztázása a `0x00590f40` címre egyetlen közvetlen hívást talált:
`0x005914f1`-et, a fenti billentyűfigyelőből. A 2026-10-23-i kapuzott
újrafutás (`paszta.memoria_kapu(1536)`) 2 884 879 utasítást dolgozott fel,
és ugyanezt az egyetlen közvetlen hívást adta. A `Scrapture::vftable`
(`0x00c91728`) `+0x08` rekesze szintén `0x00591470`-re mutat; a teljes
szövegszakasz két közvetlen címhivatkozása közül az egyik az állapotkezelő
`0x0040ca6f`, a másik a konstruktor `0x00590ef5` utasítása.

A `RegisterHotKey` nem szerepel az importtáblában. A talált
`SetWindowsHookExA`-hívás a `0x0097de80` függvényben van (`0x0097df86`-nál
az API-nak átadott típusérték `5`); négy közvetlen hívója van:
`0x00980670`, `0x00980700`, `0x009807f0`, `0x009bac20`. Egyik sem része a
`Scrapture` közvetlen hívási láncának. Ezek az eredmények a billentyűfigyelő
útvonalat támasztják alá, de az indirekt gyorsbillentyű- vagy menü-dispatch
hiányát nem bizonyítják.

**Külön menü-/accelerator-indító ág: NINCS MEG.** A meglévő Ghidra-kimenet
a `0x0097fc30` üzenetciklusban `TranslateAcceleratorA`-t mutat a
`DAT_00d4a4d4` gyorsbillentyű-táblával, de nem azonosítja a tábla tartalmát
vagy a rögzítőhöz vezető parancsot. A második, ugyanígy kapuzott teljes
`.text`-pásztázás szintén 2 884 879 utasítást dolgozott fel, és egyetlen
abszolút hivatkozást talált a `DAT_00d4a4d4` címére: az olvasást
`0x0097fd18`-nál; ez sem mutatja meg a tábla feltöltését. A `0x00923110`
meglévő kimenete egy
külön általános táblakészítőt mutat, kapcsolatát ezzel a fő ciklussal nem
igazolja. A következő célzott irány a fő ciklus HACCEL-táblájának
feltöltése és parancsútja, majd ennek összevetése a `Scrapture` objektummal.

| Módosító | A `0x00591470` által átadott cél |
|---|---|
| nincs | `0`; a `0x00590f40` `GetDesktopWindow`-t választ |
| Ctrl (`0x11`) | `1`; a `0x00590f40` `GetForegroundWindow`-t választ |
| Alt (`0x12`) | `GetCursorPos` → `WindowFromPoint`; a kurzor alatti ablak fogantyúja |

Az Alt-ág közvetlenül ablakfogantyút ad át, ezért az Alt választása megelőzi
a Ctrl-módot. A `0x0040bf70` és a `0x00591470` közti vtable-kapcsolatot a
`Scrapture::vftable` adatai és a szálhívás is alátámasztja.

## 2. Mit rögzít

Alapállapotban a cél a `GetDesktopWindow`; Ctrl mellett az előtérablak,
Alt mellett a kurzor alatti ablak. A `0x00590f40` `GetWindowRect`-tel kéri
le a cél téglalapját, majd a `GetSystemMetrics` `0x4c`, `0x4d`, `0x4e`,
`0x4f` azonosítóival (`SM_X/Y/CX/CYVIRTUALSCREEN`) a virtuális képernyő
határaihoz igazítja. A képet a képernyő DC-jéből a `0x009aa990`-en át
hívott GDI `BitBlt` másolja. Az alapmód a `GetDesktopWindow` téglalapját
célozza, és azt a virtuális képernyő határaihoz vágja; Ctrl és Alt esetén a
kiválasztott ablak téglalapját vágja ugyanígy. Ez a virtuális asztali
rögzítési útvonalat bizonyítja, de a statikus kód nem dönti el, hogy a
`GetWindowRect(GetDesktopWindow())` futásidejű téglalapja a másodlagos
monitorokat is lefedi-e. Így az sem bizonyított, hogy egy kimeneti fájl az
összes csatlakoztatott monitor képét tartalmazza. **NINCS MEG**; ehhez
Windows alatt, több monitorral végzett rögzítés és a mentett kép mérése kell.

**Kurzor:** a Picasa kódja a `GetCursorPos`-t az Alt-módú célablak
kiválasztására használja. A `0x00590f40` → `0x009aa990` rögzítési útban
nincs külön kurzorrajzolás. Azt viszont a statikus Picasa-kód nem dönti el,
hogy a képernyő DC-ből végzett `BitBlt` eredményén a Windows megjeleníti-e a
kurzort. **NINCS MEG**; eldöntéséhez eredeti Picasán kell rögzíteni egy
képet úgy, hogy a kurzor ismert helyen áll, majd a kimeneti BMP-t
ellenőrizni.

## 3. Kimenet és célmappa

| Tulajdonság | Binárisból kiolvasott érték |
|---|---|
| Alapnév | A kiválasztott ablak címét olvassa (`0x00590fec`-`0x0059100a`, `0x00986200`). Ha nincs használható cím, a `Scrapture::defaultname` erőforráskulcshoz kér szöveget (`0x00c916dc`); ennek hiányában `Fullscreen capture` a tartalék szöveg (`0x00c916c8`). |
| Dátum-idő | A `0x0098b6e0` dátum-idő értékéből a `0x0098c470` `VarBstrFromDate`-tel készít szöveget (`0x00c405c4`, LCID `0x400`, flags `0`); a szöveg egy szóközzel kerül az alapnév után (`0x00591067`-`0x00591094`). A pontos megjelenítési alak a futásidejű locale-tól függ, ezért **NINCS MEG** egyetlen állandó formátumként; egy konkrét alakhoz az eredeti Picasát a cél-locale alatt kell mérni. |
| Fájlnév | Minta: `<ablakcím vagy tartalék alapnév> <locale szerinti dátum-idő>.bmp`. Ha nincs cím és a `Scrapture::defaultname` erőforráskulcs feloldása sikertelen, az alap `Fullscreen capture`; a `.bmp` kiterjesztés a `0x00591099` utasításnál kerül hozzá. |
| Névütközés | A `0x00993650` a `%s-%03lu` (`0x00cd8d64`) mintával a fájlnév-komponenshez fűz sorszámot. A számláló `1`-ről indul (`0x00993a96`); ütközéskor növeli (`0x00993b56`). A kiterjesztés külön komponensként marad a `.bmp`-nél (`0x009a37b0`, `0x009a3930`), ezért az első ütközés utáni minta `<alapnév> <dátum-idő>-001.bmp`. A háromjegyű alak minimumszélesség; a sorszám nem időbélyeg. |
| Formátum | A `0x009ad2d0` `wb` módban nyit fájlt, `BM` aláírást ír (`0x009ad382`, `0x009ad387`), majd 40 bájtos `BITMAPINFOHEADER`-t, 54 bájtos képadat-eltolást, 1 síkot, 24 bit/pixelt és 0 tömörítési értéket állít be (`0x009ad3e4`-`0x009ad469`). A képpontokat soronként 3 bájttal írja (`0x009ad550`-`0x009ad569`): ez 24 bites, tömörítetlen BMP. |
| JPEG-minőség | Nem alkalmazható: ez az út BMP-t ír; JPEG-minőségi értéket nem olvas. |
| Célmappa | A `Scrapture::capturepath` alapértéke `Picasa\Screen Captures\` (`0x00c9170c`, `0x00c916f4`); erőforrás magyarul `Picasa\Képernyőfelvételek\` is lehet. |

A `0x00590f40` a rögzítési út összeállítása után meghívja a
`0x009a3db0` útvonal-előkészítőt (`0x00591262`), még a fájlírás előtt. Ez
a `0x00d6957c` függvénymutatón át `CreateDirectoryW`-t vagy
`CreateDirectoryA`-t hív. A mutatót inicializáló kód (`0x00c337aa`-
`0x00c337ba`) a két API-út valamelyikére állítja; az importtábla
`0x009b1140` címen `CreateDirectoryW`-t, `0x00c40510` címen
`CreateDirectoryA`-t azonosít. A `0x009a3db0` hiányzó szülőút esetén a
`0x009a3b50`-nel felbontja az útvonalat és rekurzívan újrapróbálja a
létrehozást. A hívó csak ezután jut a BMP-íróhoz (`0x009ad2d0`).

## 4. Könyvtárba vétel és értesítés

Miután a célmappa előkészítése sikerült, a rögzítő `0x63617042` üzenetet
küld a főablaknak (`0x005912d0`). A főablak kezelője (`0x00601090`) ezt a
`0x00445a30` útvonalra adja. Ez a függvény a mappát ellenőrzi, majd a
`.picasa.ini` `P2category` értékét `Projects (internal)`-ra állítja
(`0x00445b0c`-`0x00445b47`; a `P2category` kulcs `0x00c809e8`, a projekt
értéke `0x00c7ec64`). Így a `Picasa\Screen Captures` mappa a Projektek
gyűjteménybe kerül. Ez mappaszintű besorolás, nem bizonyíték a képfájl
adatbázisba írásának pontos időzítésére.

A BMP-író (`0x009ad2d0`) meghívása után a `0x00590f40` `0x63617043`
üzenetet küld a kimeneti útvonallal (`0x005913ac`-`0x005913c5`). A hívó
nem ellenőrzi az író visszatérési értékét az üzenet előtt; ezért a `capC`
önmagában a mentés sikerét nem bizonyítja. A főablak ezt a `0x0057d080`
értesítő-ágra továbbítja (`0x00601090`, `0x00601f33`-`0x00601f76`). A
`0x0057d080` a `Screenshot saved` és `click to view` szövegeket használja
(szövegek: `0x00c8ab60`, `0x00c90394`; kulcsok: `0x00c8ab74`,
`0x00c903a4`), majd értesítést jelenít meg. A buborék létezését az eredeti
Picasáról készült képernyőkép is megerősíti
([picasa-lebego-ertesito.md](picasa-lebego-ertesito.md), 1. ág).

Ha nincs főablak-fogantyú, a rögzítő a `DAT_00d695b8` függvénymutatót hívja
`open` művelettel és a kimeneti fájl útvonalával (`0x005913cf`-`0x005913f0`).
A `0x00c80fc0` cím ASCII tartalma `open`. A mutatót inicializáló helyi
diszasszemblálás két ágat mutat: a `0x00c33b6a` utasítás a
`0x009b2890`-et írja be; a `0x00c33b7a` az `0x00c405e0` címen tárolt
függvénymutatót. Az utóbbi nyers PE-értéke `0x009239a8`, amelyet az
importjegyzék `ShellExecuteA`-ként azonosít. A `0x009b2890` függvény a
`0x00c40630` címen levő mutatón át hív; annak PE-értéke `0x00923998`, az
importjegyzék szerint `ShellExecuteW`. Így mindkét feloldott ág a fájl
`ShellExecute`-tel, `open` művelettel történő megnyitását kéri. A
`0x00c33b68` a `0x00d6fc58` értékét `0x80000000`-hez hasonlítja: ha kisebb,
a `ShellExecuteW`-t tartalmazó `0x009b2890`-et állítja be; ha legalább
ekkora, az `0x00c405e0`-n át a `ShellExecuteA`-t. A globális érték
platformonkénti jelentése nincs feloldva. Ez a fájlt adja át a shellnek;
nem bizonyítja, hogy a buborék a mappára navigál.

**Nyitott:** a `0x0057d080` a buborék előtt meghív egy útvonal-kereső
útvonalat (`0x004f92c0` → `0x004e7d10`); az utóbbi bejárja a gyűjtemény
adatait, és egy ágán a `0x004e31a0` függvényt is meghívja. Ez a
diszasszemblálás nem dönti el, hogy a kimeneti BMP ilyenkor azonnal bekerül-e a könyvtári
indexbe. A `0x0057d080` a `clickview` műveletet is előkészíti, de a kattintási
viselkedést a `0x0057d1e4`-nél hívott, az objektum vtable-jéből vett
`+0x68` metódus valósítja meg; ennek célfüggvénye és navigációs célja itt
**NINCS MEG**.

Az `open` ág `ShellExecuteA`/`ShellExecuteW` feloldását nem szabad a fenti
buborék-kattintással azonosítani: a két művelet külön útvonal, és a kattintási
callback dinamikus címzettjének osztálya nincs bizonyítva.

## 5. Független ellenőrzési utak és cáfoló próba

**A út: beállítás és vezérlési út utasításszinten:** a `0x0040bf70`
`Preferences\EnableScreenCap` olvasása `1` alapértékkel, a visszaadott érték
nulla-ellenőrzése (`0x0040ca41`-`0x0040ca47`), majd a nem nulla ágon az
objektum- és szálindítás (`0x0040ca49`-`0x0040ca78`). A szál
`0x0097aeb0` belépője a `Scrapture` vtable `+0x08` metódusát hívja
(`0x0097af1c`-`0x0097af23`), ez a `0x00591470`; a billentyűfigyelő
közvetlenül hívja a `0x00590f40` rögzítőt (`0x005914f1`), amely a
`0x009ad2d0` BMP-írót használja. A vtable `+0x04` állapotvizsgálójának
jelentése ettől külön nyitott.

**B út: független hivatkozáslánc és fogyasztók:** a beállításkezelő a
`0x00c91728` `Scrapture::vftable` címet írja az objektumba
(`0x0040ca6f`-`0x0040ca75`); a vtable `+0x08` rekesze `0x00591470`.
Külön a `0x0097b350` a `0x0097aeb0` szálbelépőt adja át
(`0x0097b3a3`), amely a saját vtable `+0x08` rekeszét hívja
(`0x0097af1c`-`0x0097af23`). A teljes `.text` pásztázás a
`0x00590f40` egyetlen közvetlen hívójaként a billentyűfigyelő
`0x005914f1` utasítását találta. Ez a hivatkozáslánc a beállításolvasástól
függetlenül ugyanarra a háttérbeli billentyűfigyelőre és rögzítőhívásra mutat.
A külön főablak-üzenetkezelő (`0x00601090`) a rögzítő `0x63617042` és
`0x63617043` üzeneteit a `0x00445a30` kategorizáló, illetve a
`0x0057d080` értesítő útvonalra viszi. Az utóbbi útvonal `Screenshot
saved`/`click to view` kulcsait használja, és a meglévő Picasa-képernyőkép
függetlenül igazolja a buborékot. A BMP-típusra külön ellenőrzés a
`0x009ad2d0` író fejléc- és képpontútja (`BM`, 24 bit/pixel, 0 tömörítés),
nem pusztán a hívó által hozzáfűzött kiterjesztés. **Az utak a
mappabesorolásnál, a BMP-formátumnál és a buboréknál egyeznek.** A képfájl
azonnali indexelésére nem adnak két egyező bizonyítékot.

A főablak nélküli `open` API-nál az A út az inicializáló utasításokból követi
a két mutatóágat (`0x00c33b68`-`0x00c33b7a`); a B út külön a nyers PE
mutatóértékeit (`0x00c405e0`, `0x00c40630`) és az importjegyzék API-neveit
veti össze. Mindkettő ugyanazt az ANSI/Unicode `ShellExecute`-választást adja.

**Cáfoló próba 1: „a `.bmp` csak kiterjesztés, a tartalom lehet JPEG”:**
követtem a hívótól a `0x009ad2d0` íróig, majd a fejlécmezőket és a
képpontírást is ellenőriztem. Az író `BM` fejlécet, 24 bit/pixelt és 0
tömörítést állít be, majd három bájtot ír képpontonként; a JPEG-hipotézist
ez a második, íróoldali bizonyíték cáfolja.

**Cáfoló próba 2: „a Print Screen-hook indítja a rögzítést”:** megkerestem
a rögzítőfüggvény közvetlen hívásait a teljes `.text`-ben, majd külön
követtem a `SetWindowsHookExA` hívóját. A közvetlen hívás-pásztázás csak a
`0x005914f1` billentyűfigyelőből jövő hívást találta; a hook-jelölt
`0x0097de80`-tól nem vezetett közvetlen hivatkozás a rögzítőhöz. A
`Scrapture` útja saját maga kérdezi le a billentyűállapotot
(`0x00591470`). Ez a próba a közvetlen hook-utat nem támasztja alá, de az
indirekt accelerator-/menü-dispatchot **nem** zárja ki.

**Cáfoló próba 3: „a buborék `+0x68` hívása a `CNotifierPopup` kattintási
metódusa”:** a `CNotifierPopup::vftable` nyers rekeszét külön ellenőriztem;
`0x00ca28b4` valóban a `0x00659340` címre mutat. A `0x00659340`
diszasszemblálása animációs/nézetfrissítő műveletet mutat, nem fájlmegnyitást
vagy mappára navigálást. Mivel a `0x0057d080` dinamikus hívásának címzettje
nincs ehhez az osztályhoz kötve, ez a hasonló rekeszeltolás nem azonosítja a
kattintási callbacket; a kattintási cél továbbra is nyitott.

## 6. PicasaPy: jelenlegi állapot

| Eredeti Picasa | PicasaPy a forrás áttekintésekor | Következő fejlesztési munka |
|---|---|---|
| Ismételt billentyű-lekérdezés és rejtett `EnableScreenCap` kapcsoló | Nincs rögzítő vagy bekötött gyorsbillentyű | Preferencia és háttérbeli rögzítőút, a fenti billentyűmódokkal |
| BMP a `Picasa\Screen Captures` projektmappába | `ProjectFolderKind.SCREEN_CAPTURES` és honosított név létezik (`src/picasapy/app/project_folder_names.py`); képfájlíró nincs | BMP-kimenet, ütközéskor sorszám, célmappa előkészítése és projektbesorolás |
| Mentés után `Screenshot saved` értesítés | A `PicasaNotifier.qml` képernyőfelvételi eseményt nem köt be; a forráskód megjegyzése is hiányzó funkcióként nevezi meg | Kimeneti útvonal átadása az értesítőnek és „megtekintés” művelet |

## 7. Bizonyítottság és nyitott irányok

**Összesített fok: feltételes.** A `Preferences\EnableScreenCap` olvasása,
`1` alapértéke és nulla értéknél a figyelőszál kihagyása, a billentyűmódok,
fájlnév-képzés, BMP-kimenet,
mappalétrehozás, mappabesorolás és buborék binárisból visszakereshető; a
teljes képernyő többmonitoros terjedelme, a kurzor képpontbeli jelenléte, a
menü/accelerator út, az azonnali képfájl-indexelés és a buborék kattintási
célja nyitott. A külön ellenőrzési utak a BMP-író tartalmán, a
mappabesorolásnál és a buboréknál egyeznek.

| Állítás | Forrás |
|---|---|
| HKCU `Preferences\EnableScreenCap` olvasása; alapérték `1`; nulla értéknél az objektum- és szálindítás átugrása | bináris (`0x0040bf70`, `0x0040ca13`, `0x0040ca24`, `0x0040ca41`-`0x0040ca47`, `0x0040ca49`-`0x0040ca78`, `0x00407a3b`) |
| Print Screen / Print ismételt lekérdezés és Ctrl/Alt mód | bináris (`0x00591470`, `0x00590f40`) |
| Figyelőciklus állapotkapuja, rögzítés utáni várakozás és ismételt lekérdezés | bináris (`0x0059147d`-`0x00591488`, `0x005914f6`-`0x00591518`, `0x00c91728`, `0x00408b30`; `WaitForSingleObject` import `0x00921d4c`, `Sleep` import `0x00921ba0`); a `+0x04` állapotjelentése és kapcsolata a preferenciával: NINCS MEG |
| Virtuális asztal célzása, képernyőhatár-vágás és GDI-másolás; többmonitoros eredmény | bináris (`0x00590f40`, `0x009aa990`); többmonitoros kimenet: NINCS MEG, futásidejű mérés kell |
| Ablakcím/tartalék név, locale-függő dátum-idő, ütközési sorszám, kiterjesztés | bináris (`0x00986200`, `0x00c916c8`, `0x0098b6e0`, `0x0098c470`, `0x00cd8d64`, `0x00993650`, `0x00c865cc`) |
| 24 bites, tömörítetlen BMP-fejléc és képpontírás | bináris (`0x009ad2d0`, `0x009ad382`-`0x009ad569`) |
| Célmappa létrehozása | bináris (`0x00590f40`, `0x009a3db0`, `0x00d6957c`, `0x00c337aa`) |
| Projektek-besorolás | bináris (`0x00601090`, `0x00445a30`, `0x00c809e8`, `0x00c7ec64`) |
| Értesítő buborék; főablak nélkül `open` műveletű indirekt hívás | bináris (`0x00601090`, `0x0057d080`, `0x005913cf`-`0x005913f0`, `0x00c8ab60`, `0x00c90394`); mérés (eredeti Picasa-képernyőkép, 2026-08-20) |
| Főablak nélküli `open` ág API-választása | bináris (`0x00c33b68`-`0x00c33b7a`, `0x00c405e0` → `0x009239a8` `ShellExecuteA`, `0x009b2890` → `0x00c40630` → `0x00923998` `ShellExecuteW`; `0x00c80fc0` = `open`) |
| Fájlíró után jön-e `capC` csak siker esetén | bináris (`0x005913ac`-`0x005913c5`): nincs visszatérésiérték-ellenőrzés, ezért az üzenet nem igazolja a sikeres mentést |
| Kurzor bekerül-e a BMP-be | NINCS MEG; Windows-futásidejű mérés kell |
| Egyetlen közvetlen hívó a `0x00590f40`-hez; `Scrapture` vtable-kapcsolat | bináris (`paszta.py` teljes `.text` pásztázás; `0x005914f1`, `0x00c91728`, `0x0040ca6f`, `0x00590ef5`) |
| Névütközés kezdő sorszáma és növelése | bináris (`0x00993a96`, `0x00993b56`, `0x00cd8d64`) |
| A képfájl azonnali indexelése | NINCS MEG; a meglévő Ghidra-kimenet a `0x004f92c0` → `0x004e7d10` utat és az `0x004e31a0` indirekt vtable-hívását mutatja, de a konkrét callback hatását nem |
| A buborék kattintási célja | NINCS MEG; a `0x0057d1e4` vtable `+0x68` hívás célfüggvényét kell azonosítani |
| A vtable `+0x04` állapotkapujának jelentése; menü-/accelerator-parancs vezet-e képernyőképhez | NINCS MEG; az állapotkapuhoz a `0x00408b30` helper célját és állapotforrását, majd a `0x00c40328` mutató inicializálását és használatát kell követni; az acceleratorhoz a `0x0097fc30` által olvasott `DAT_00d4a4d4` tábla feltöltési és parancsútját kell a `Scrapture` objektummal összekötni |
| Főablak nélküli ágon a rendszer melyik `ShellExecute` API-t választja | NINCS MEG; a `0x00c33b68` a `0x00d6fc58` alapján választ `ShellExecuteA` (`0x009239a8`) és `ShellExecuteW` (`0x00923998`) között; a globális érték eredetét és platformjelentését kell feloldani |

Ghidra-kör kell: 0x004e31a0: a `0x004f92c0` → `0x004e7d10` keresési út az `param_3 + 0x344 + 0x10` sloton mely konkrét callbacket hívja, és az a friss képfájlt indexbe írja-e vagy csak keres [blokkoló]. A meglévő `0x004e31a0` dekompilált kimenet az indirekt hívást mutatja, a célfüggvényt nem.
Ghidra-kör kell: 0x0057d080: a `0x0057d1e4` vtable `+0x68` hívás konkrét célfüggvénye és a `clickview` művelet kattintási navigációja [blokkoló]. A meglévő dekompilált kimenet a hívást és a kulcsot mutatja, a célfüggvényt nem.
Ghidra-kör kell: 0x0097fc30: a `DAT_00d4a4d4` HACCEL-tábla létrehozási/feltöltési útja és parancsazonosítói indíthatják-e a `Scrapture`-t vagy a `0x00590f40`-et [blokkoló]. A meglévő dekompilált kimenet a `TranslateAcceleratorA` hívást mutatja, de a tábla tartalmát és a rögzítőhöz vezető parancsot nem.
Ghidra-kör kell: 0x00c33b68: a meglévő `2026-10-23-sor-277-280.txt` kimenet a `ShellExecuteA`/`ShellExecuteW` választást mutatja, de nem azonosítja, mi állítja elő a belépéskor használt `in_CF` feltételt; a `0x00d6fc58` eredetét és a platformfeltételt kell feloldani.

Futásidejű mérés kell: eredeti Windows Picasában a kurzor láthatósága a mentett BMP-n; többmonitoros rendszeren a kimeneti BMP téglalapja; a fájl indexbe kerülésének pillanata és a buborék kattintási célja; továbbá a dátum-idő szövegalakja a cél-locale alatt.

## Hivatkozások

- [A gyári projekt-mappák](picasa-gyari-projekt-mappak.md): a `Screen Captures` erőforrás és a lokalizált útvonal.
- [A lebegő értesítősáv](picasa-lebego-ertesito.md): a képernyőkép-értesítő képernyőképe és fordításai.
- [A főablak elrendezése](picasa-fo-ablak-elrendezes.md): az `EnableScreenCap` induláskori állapotkezelője.
