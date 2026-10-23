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
`Preferences\EnableScreenCap`. Nulla értéknél a `Scrapture` objektum és a
figyelőszál nem jön létre. Nem nulla
értéknél az objektum megkapja a `Scrapture::vftable` címet
(`0x00c91728`, `0x0040ca6f`), és indul a `0x0097b350` szálindító.

A szál belépője `0x0097aeb0`; a vtable `+0x08` rekeszéből hívja a
`0x00591470` metódust. A `0x00591470` a `GetAsyncKeyState`-tel a
`VK_SNAPSHOT` (`0x2c`) és `VK_PRINT` (`0x2a`) billentyűt figyeli, majd
`Sleep(0x14)`-gyel vár a következő ellenőrzésig. A vizsgált út tehát
háttérszálas ismételt billentyű-lekérdezés. A `paszta.py` teljes `.text`
pásztázása a `0x00590f40` címre egyetlen közvetlen hívást talált:
`0x005914f1`-et, a fenti billentyűfigyelőből. A `Scrapture::vftable`
(`0x00c91728`) `+0x08` rekesze szintén `0x00591470`-re mutat; a teljes
szövegszakasz közvetlen címhivatkozásai a táblára a beállítási ág
`0x0040ca6f` és a konstruktor `0x00590ef5` utasításai.

A `RegisterHotKey` nem szerepel az importtáblában. A talált
`SetWindowsHookExA`-hívás a `0x0097de80` függvényben van (`0x0097df86`-nál
az API-nak átadott típusérték `5`); négy közvetlen hívója van:
`0x00980670`, `0x00980700`, `0x009807f0`, `0x009bac20`. Egyik sem része a
`Scrapture` közvetlen hívási láncának. Ezek az eredmények a billentyűfigyelő
útvonalat támasztják alá, de az indirekt gyorsbillentyű- vagy menü-dispatch
hiányát nem bizonyítják.

**Külön menüindító ág: NINCS MEG.** A következő célzott irány az
acceleratortábla létrehozójának (`0x00923110`), a
`TranslateAcceleratorA`-t hívó feldolgozónak (`0x0097fc30`) és az
üzenetciklusnak (`0x00855770`) az összekötése a rögzítővel.

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
hívott GDI `BitBlt` másolja. Az alapmód ezért a virtuális asztal
képernyőterületét célozza, a csatlakoztatott monitorokkal együtt; a Ctrl és
Alt ablakméretű területet ad.

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
| Alapnév-beállítás | `Scrapture::defaultname`; hiányzó értéknél `Fullscreen capture` (`0x00c916dc`, `0x00c916c8`) |
| Első fájlnév | `Scrapture::defaultname` hiányában `Fullscreen capture.bmp`, ha ez még nem létezik |
| Névütközés | A `0x00993650` a `%s-%03lu` (`0x00cd8d64`) mintával a fájlnév-komponenshez fűz sorszámot. A számláló `1`-ről indul (`0x00993a96`); ütközéskor a meglévő számot növeli (`0x00993b56`). A kiterjesztés külön komponensként marad a `.bmp`-nél (`0x009a37b0`, `0x009a3930`), ezért az első ütközés utáni példa `Fullscreen capture-001.bmp`. A háromjegyű alak minimumszélesség, a sorszám nem időbélyeg. |
| Formátum | BMP: a `0x00590f40` `.bmp` kiterjesztést fűz hozzá (`0x00c865cc`); a `0x009ad2d0` `wb` módban nyit fájlt és `BM` fejlécet ír. |
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
üzenetet küld a kimeneti útvonallal (`0x005913ac`-`0x005913c5`). A főablak ezt a `0x0057d080`
értesítő-ágra továbbítja (`0x00601090`, `0x00601f33`-`0x00601f76`). A
`0x0057d080` a `Screenshot saved` és `click to view` szövegeket használja
(`0x00c8ab60`, `0x00c90394`), majd értesítést jelenít meg. A buborék
létezését az eredeti Picasáról készült képernyőkép is megerősíti
([picasa-lebego-ertesito.md](picasa-lebego-ertesito.md), 1. ág).

**Nyitott:** a `0x0057d080` a buborék előtt meghív egy útvonal-kereső
útvonalat (`0x004f92c0` → `0x004e7d10`); az utóbbi bejárja a gyűjtemény
adatait, és egy ágán a `0x004e31a0` függvényt is meghívja. Ez a
diszasszemblálás nem dönti el, hogy a kimeneti BMP ilyenkor azonnal bekerül-e a könyvtári
indexbe. A `0x0057d080` a `clickview` műveletet is előkészíti, de a kattintási
viselkedést a `0x0057d1e4`-nél hívott, az objektum vtable-jéből vett
`+0x68` metódus valósítja meg; ennek célfüggvénye és navigációs célja itt
**NINCS MEG**.

## 5. Független ellenőrzési utak és cáfoló próba

**A út: előállító:** a `0x0040bf70` beállításkapuja → a
`0x0097b350`/`0x0097aeb0` szálindítás → a `Scrapture` vtable `+0x08`
rekeszén `0x00591470` → `0x00590f40` → `0x009ad2d0` BMP-írás.

**B út: osztályadat és fogyasztó:** a `Scrapture::vftable` nyers
rekeszei (`0x00c91728`) a `0x00591470` figyelőmetódust adják; a külön
főablak-üzenetkezelő (`0x00601090`) a rögzítő `0x63617042` és
`0x63617043` üzeneteit a `0x00445a30` kategorizáló, illetve a
`0x0057d080` értesítő útvonalra viszi. Az utóbbi útvonal `Screenshot
saved`/`click to view` kulcsait használja, és a meglévő Picasa-képernyőkép
függetlenül igazolja a buborékot. **Az utak a mappabesorolásnál és a
buboréknál egyeznek.** A képfájl azonnali indexelésére nem adnak két
egyező bizonyítékot.

**Cáfoló próba: „a Print Screen-hook indítja a rögzítést”:** megkerestem
a rögzítőfüggvény közvetlen hívásait a teljes `.text`-ben, majd külön
követtem a `SetWindowsHookExA` egyetlen importált hívóját. A közvetlen
címhivatkozás-pásztázás csak a `0x005914f1` billentyűfigyelőből jövő
hívást találta. A hook-jelölt `0x0097de80` más függvény; a rögzítőhöz nem
vezet közvetlen hivatkozás, és a `Scrapture` útja saját maga kérdezi le a
billentyűállapotot (`0x00591470`). A billentyűkampó-feltevés tehát nem cáfolja a
billentyűfigyelő út bizonyítékát. Ez a próba **nem** zárja ki az indirekt
menü-/accelerator-útvonalat; annak keresése a fenti nyitott irány.

## 6. PicasaPy: jelenlegi állapot

| Eredeti Picasa | PicasaPy a forrás áttekintésekor | Következő fejlesztési munka |
|---|---|---|
| Ismételt billentyű-lekérdezés és rejtett `EnableScreenCap` kapcsoló | Nincs rögzítő vagy bekötött gyorsbillentyű | Preferencia és háttérbeli rögzítőút, a fenti billentyűmódokkal |
| BMP a `Picasa\Screen Captures` projektmappába | `ProjectFolderKind.SCREEN_CAPTURES` és honosított név létezik (`src/picasapy/app/project_folder_names.py`); képfájlíró nincs | BMP-kimenet, ütközéskor sorszám, célmappa előkészítése és projektbesorolás |
| Mentés után `Screenshot saved` értesítés | A `PicasaNotifier.qml` képernyőfelvételi eseményt nem köt be; a forráskód megjegyzése is hiányzó funkcióként nevezi meg | Kimeneti útvonal átadása az értesítőnek és „megtekintés” művelet |

## 7. Bizonyítottság és nyitott irányok

**Összesített fok: feltételes.** Az indítási kapu, a billentyűmódok, a
BMP-kimenet, a mappalétrehozás és a Projektek-besorolás binárisból
visszakereshető, a két ellenőrzési út pedig a mappabesorolásnál és a
buboréknál egyezik. A kurzor tényleges képpontbeli jelenléte, az azonnali
képfájl-indexelés és a buborék-kattintás navigációja nyitott.

| Állítás | Forrás |
|---|---|
| HKCU `Preferences\EnableScreenCap`, alapérték `1`, objektum/szál létrehozása | bináris (`0x0040bf70`, `0x0040ca13`, `0x0040ca6f`, `0x0040ca78`, `0x00407a3b`) |
| Print Screen / Print ismételt lekérdezés és Ctrl/Alt mód | bináris (`0x00591470`, `0x00590f40`) |
| Virtuális asztal és GDI-másolás | bináris (`0x00590f40`, `0x009aa990`) |
| Név, ütközési sorszám, kiterjesztés | bináris (`0x00c916c8`, `0x00cd8d64`, `0x00993650`, `0x00c865cc`) |
| BMP-fejléc és fájlírás | bináris (`0x009ad2d0`) |
| Célmappa létrehozása | bináris (`0x00590f40`, `0x009a3db0`, `0x00d6957c`, `0x00c337aa`) |
| Projektek-besorolás | bináris (`0x00601090`, `0x00445a30`, `0x00c809e8`, `0x00c7ec64`) |
| Értesítő buborék | bináris (`0x00601090`, `0x0057d080`, `0x00c8ab60`, `0x00c90394`); mérés (eredeti Picasa-képernyőkép, 2026-08-20) |
| Kurzor bekerül-e a BMP-be | NINCS MEG; Windows-futásidejű mérés kell |
| Egyetlen közvetlen hívó a `0x00590f40`-hez; `Scrapture` vtable-kapcsolat | bináris (`paszta.py` teljes `.text` pásztázás; `0x005914f1`, `0x00c91728`, `0x0040ca6f`, `0x00590ef5`) |
| Névütközés kezdő sorszáma és növelése | bináris (`0x00993a96`, `0x00993b56`, `0x00cd8d64`) |
| A képfájl azonnali indexelése | NINCS MEG; a `0x004f92c0`/`0x004e7d10` út célfüggvényeit kell követni |
| A buborék kattintási célja | NINCS MEG; a `0x0057d1e4` vtable `+0x68` hívás célfüggvényét kell azonosítani |

Ghidra-kör kell: 0x004f92c0: az útvonal-keresés csak meglévő könyvtári elemet talál-e, vagy a friss BMP-t is indexeli [blokkoló]
Ghidra-kör kell: 0x004e7d10: a bejárt gyűjteményadat tartalmazhatja-e már a friss BMP-t [blokkoló]
Ghidra-kör kell: 0x004e31a0: az ág indexbe ír vagy csak meglévő elemet keres [blokkoló]
Ghidra-kör kell: 0x0057d080: a `0x0057d1e4` vtable `+0x68` hívás célfüggvénye és a `clickview` művelet kattintási célja [blokkoló]
Ghidra-kör kell: 0x00923110: az acceleratortábla tartalmaz-e képernyőkép-indító parancsot [blokkoló]
Ghidra-kör kell: 0x0097fc30: az accelerator-/üzenetút továbbít-e képernyőkép-indítást [blokkoló]
Ghidra-kör kell: 0x00855770: az üzenetciklus eléri-e a `Scrapture`-t vagy a `0x00590f40` függvényt [blokkoló]

Futásidejű mérés kell: eredeti Windows Picasában a kurzor láthatósága a mentett BMP-n; ugyanott a fájl indexbe kerülésének és a buborék-kattintásnak a sorrendje.

## Hivatkozások

- [A gyári projekt-mappák](picasa-gyari-projekt-mappak.md): a `Screen Captures` erőforrás és a lokalizált útvonal.
- [A lebegő értesítősáv](picasa-lebego-ertesito.md): a képernyőkép-értesítő képernyőképe és fordításai.
- [A főablak elrendezése](picasa-fo-ablak-elrendezes.md): az `EnableScreenCap` induláskori állapotkezelője.
