# A poszter készítésének teljes folyamata az eredeti Picasával összevetve: belépési pontok, ablak, hatás

## Hatókör és bizonyosság

Ez a lap a #7306 kérdését dolgozza fel. A vizsgált eredeti `Picasa3.exe` SHA-256 értéke `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`, verziója 3.9.141.259. A fájlt csak statikusan vizsgáltam, nem futtattam és nem másoltam a repóba.

**Összesített bizonyítottság: feltételes.** A menüparancs, a párbeszéd definíciója, a fájlnév, a kimeneti formátum és a generáló függvény statikusan követhető. Az eredeti futtatott Picasa-folyamat felvétele nem található meg a helyi mérőadatban, ezért az alapértékek, a keletkező képek pontos határai, az index és a felület utóhatásai, valamint a hibák felhasználói kezelése nyitott.

A korábbi futtatott felvételek keresése (`grep -rn "job-[0-9]" docs/specs/`) és a poszterlapok listázása (`ls docs/specs | grep -i 'poster\|poszter'`) megtörtént. Külön poszterfolyamat-specifikáció nem volt; a releváns statikus leírás a `picasa-create-features.md` 3.1. pontja, a menüleírás pedig a `picasa-menu-parancsok-viselkedes.md` 35.1-35.2. pontja. A tar 944 bejegyzéséből a poszterhez hasonló nevű `3084-poszterizalas` és `2770-poszterizalas` képminták kerültek elő, folyamatfelvétel nem. Mérőadatot nem bontottam ki.

## Eredeti menet

### Belépési pontok

- **Létrehozás menü:** a `0x00559150` menüépítő létrehozza a `Make a &Poster...` elemet, és a `0x9d30` parancsazonosítót írja a menürekordba (`0x0055bbf0`). A `0x005cb990` diszpécser `0x005cc151` helyen hívja a `0x00530c10` kezelőt. A felirat `&` jele menü-mnemonikát jelöl. Külön, például Ctrl billentyűs gyorsbillentyűt a statikus bizonyíték nem mutat.
- **Külön `makeposter` akció:** a `0x005ddb80` függvény `0x005ddca8` helyen a `makeposter` szöveget vizsgálja, majd `0x005ddcb6` címen meghívja a `0x00530c10` kezelőt. A meglévő menüspecifikáció ezt a Képtálca önálló gombjához köti (`picasa-menu-parancsok-viselkedes.md:1940-1942`, címkeazonosító: `{FF04B854-3029-46ff-B762-FB9AF417F93F}`). A gomb láthatóságának és engedélyezésének feltételét futtatott felvétel nem igazolja.
- **`toys/toy8` akcióág:** a `0x005d56e0` függvény a `toys/toy8` nevet vizsgálja, majd `0x005d59d1` címen a poszterkezelőt hívja. A hívás a `0x005de8e0` akció-elosztó útjában van. A név és a hívás igazolt, a felhasználó számára látható vezérlő vagy billentyű ehhez az ághoz nincs megállapítva.
- A helyi QML-ben egyetlen poszter-menüelem található. Kontextusmenü vagy külön billentyűparancs nincs dokumentálva.
- Az eredeti aktiválási feltétel a menü felől nem dőlt el. A kezelő a `0x007166c0` állapotvizsgálatot hívja, de ennek és a menü engedélyezési szabályának teljes felhasználói feltételét a meglévő adatok nem írják le.

### Párbeszéd és állapot

A `0x007387c0` a `poster` párbeszéd erőforrását tölti be. A telepített `runtime/poster.fen` a `Poster Settings` ablakot, a súgószöveget, a `Poster size` 200%-tól 1000%-ig terjedő listáját, a `Paper size` választót, az `Overlap tiles` jelölőt, valamint az OK és Cancel gombot írja le. A papírméretek területi beállítás szerint `10x15` és `20x25`, illetve `4x6` és `8.5x11` (`0x00738800`, `0x0073895a`-`0x007389ce`). Az erőforrás nem tartalmaz futásidejű képet vagy mérési adatot.

A `0x007387c0` inicializáló a `factor` és `paper` mezőt nullára, az `overlap` mezőt hamisra állítja (`0x007387ce`-`0x007387dc`). A `0x00738800` konstruktor `paper` beállítást olvas, a `0x00738a70` adatkapcsoló pedig a `factor`, `paper` és `overlap` nevű kulcsokat olvassa. A korábbi specifikáció a `paper` utolsó választásának visszaállítását igazolja. A `factor` és `overlap` módosított értékének következő megnyitáskor való megőrzését, a hiányzó kulcsok fallback értékét, valamint az első megnyitás tényleges kiválasztott sorait nem igazolja a statikus kódút és a rendelkezésre álló mérés.

Az eredeti párbeszéd OK és Cancel választást kér. A Cancel ágon a poszterkezelő nem jut el a fájlíró ciklushoz. A teljes feladatban másik megerősítő kérdés nincs azonosítva; egy hibát követő eredeti üzenet vagy kérdés futásidejű megjelenése nincs megmérve.

### Fájlok és képtartalom

A `0x00530c10` a kiválasztott nagyítási tényezőből `N=2..10` értéket készít, majd két ciklussal N sor és N oszlop lapot ír. A fájlnév formátuma `%d-%d-%s`; az argumentumok oszlop, majd sor, a kimeneti kiterjesztés `.jpg`. Az új útvonal a forrás útvonalát használja, ezért a lapok a forrás mellett készülnek. Az író a fájlt `wb` módban nyitja (`0x009d6010`, `0x009d6041-0x009d6053`), a poszterkezelő pedig `0x5a`, azaz 90 JPEG-minőségi értéket ad át (`0x00530c10`). Meglévő azonos nevű kimenet felülírására a `wb` nyitás ad lehetőséget.

Az átfedéses ág a `0x00cf4f20` címen tárolt `1.100000023841858` és a `0x00cf50b0` címen tárolt `-0.10000002384185791` konstansokat használja; a `0x00c72150` értéke `0.5`. Ezek a `0x00530c10` koordináta-átalakításában szerepelnek. Ez megerősíti, hogy az átfedés geometriát változtat, de az eredeti kerekítés és pontos képpont-határok futtatott kimenet nélkül nem igazoltak. A súgó az azonos képarányú forráskép előzetes vágását javasolja; eltérő képarányú kimenet pontos levágása nyitott.

A `paper` választásnak a lapgeneráló ciklus pixelgeometriájára gyakorolt hatása nincs igazolva. Az író `1` és `4` paramétere közül a `4` jelentése, továbbá az EXIF és más metaadatok megőrzése vagy eltávolítása nincs megállapítva.

### Index, felület, háttérmunka és hibák

A `0x00530c10` minden létrehozási ciklus után meghívja a `0x0053de70` függvényt az új útvonallal. A függvény `AddLocateFile` belépési pontot tartalmaz, és egyes ágai `locate`, `indexonly` vagy `indexonlyreadonly` műveletneveket vizsgálnak. A 7306-hoz elérhető diszasszemblálás nem dönti el, hogy a poszter hívási ág a fájlt hozzáadja-e az indexhez, megváltoztatja-e a bal hasábot, a rácsot vagy a kijelölést. A `.picasa.ini` változásáról nincs futtatott adat.

A poszterkezelőn belül a modális párbeszéd után közvetlenül fut a két lapgeneráló ciklus; külön poszter-munkaszálat, százalékos előrehaladási hívást vagy Cancel-visszahívást nem találtam ebben a függvényben. A `0x009d6010` író kódjának látható hibaágai nem nulla visszatérési értéket adnak, a poszterkezelő ezt a visszatérési értéket nem vizsgálja, hanem utána meghívja a `0x0053de70` függvényt. Hogy írásvédett vagy hálózati cél esetén mi jelenik meg, illetve maradnak-e részleges lapok, futásidejű felvétel nélkül nyitott.

Az eredeti megszakítás, haladásjelzés, állapotsor, bal hasáb, rács, kijelölés és visszavonás pontos viselkedéséről nincs mérés. A generáló függvényben külön visszavonási műveletet nem találtam, de ez önmagában nem bizonyítja az összes külső visszavonási út hiányát.

## Összevetés

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Létrehozás menü: `0x0055bbf0`, parancs `0x9d30`, hívás `0x005cc151` | `src/picasapy/app/qml/PicasaPy/PicasaCreateMenu.qml:23-27`; feltétel: `MainMenuBar.qml:148-149` | A menüút megvan. A felhasználói feltétel az eredetivel való paritásra mérendő. Külön gyorsbillentyűt nem állítunk a kódból. |
| Képtálca akció: `0x005ddb80`, `makeposter` hívás `0x005ddcb6` | A QML-ben poszterként csak a Létrehozás menüelem található; nincs külön Képtálca-poszterhívás | Fejlesztői eltérés: a külön Képtálca-gomb hiányzik. Javasolt jegytörzs lent. A láthatósági feltételt futtatott eredeti felvétellel kell rögzíteni. |
| `toys/toy8` ág: `0x005d56e0`, hívás `0x005d59d1` | A QML-ben nem találtam ennek megfelelő akcióágat | A bináris út létezik, de UI-kapu nincs bizonyítva. Ne fejlesszünk rá, amíg a hozzá tartozó vezérlő nincs azonosítva. |
| Erőforrás betöltése: `0x007387c0`; kulcsok `0x00738800`, `0x00738a70` | `src/picasapy/app/qml/PicasaPy/PosterCreateDialog.qml:7-13,36-63,68-132`; papírméret: `src/picasapy/app/poster_controller.py:99-120` | A mezők és a területi papírméretek megvannak. Nálunk a nagyítás 200%-ra, az átfedés kikapcsoltra áll minden megnyitáskor, a papírméret utolsó választása megmarad. Az eredeti kulcsok tényleges mentése és az első megnyitás értékei nyitottak. |
| `N x N`, `%d-%d-%s`, `.jpg`, minőség `0x5a`: `0x00530c10`, `0x009d6010` | `src/picasapy/printing/poster.py:74-123` | A rács, oszlop-sor sorrend, `.jpg`, azonos nevű kimenet felülírása és JPEG-minőség 90 statikus forrás szerint egyezik. |
| Átfedés: konstansok `0x00cf4f20`, `0x00cf50b0`, `0x00c72150`; koordinátakód `0x00530c10` | `src/picasapy/printing/poster.py:36-48` | A jelenlegi kód cellánkénti 10%-os kiterjesztést és egész kerekítést használ. Pontos képpont-paritásra nincs mérés; eltérést még ne állítsunk. |
| Lapírás után `0x0053de70` | `src/picasapy/printing/poster.py:121-123`; eredménykezelés: `CreateDialogs.qml:187-198` | Az eredeti index-, lista- és kijelöléshatás nyitott. Nálunk nincs közvetlen index- vagy kijelölésmódosítás a poszteríróban; a háttérben működő figyelők utóhatása nincs összevetve. |
| A poszterkezelő közvetlen lapciklust futtat; az író visszatérési értékét nem kezeli | `src/picasapy/app/poster_controller.py:122-208`; állapotszöveg: `src/picasapy/app/busy_activity.py:77`; eredmény: `src/picasapy/app/qml/PicasaPy/CreateDialogs.qml:187-198` | Nálunk külön folyamat, 120 másodperces időkorlát, háttérállapot és siker/hiba ablak van. Az eredeti felhasználói hibaüzenet, hálózati vagy írásvédett cél viselkedése nincs megmérve. |
| Cancel az eredeti párbeszédben; a lapgeneráló függvényben nincs külön progress vagy megszakítási ág | `src/picasapy/app/qml/PicasaPy/PosterCreateDialog.qml:119-132`; `src/picasapy/app/poster_controller.py:136-208` | A megnyitott ablak Cancel gombja elutasítja a műveletet, a már futó workerhez nincs poszter-megszakítási visszahívás. Az eredeti futás megszakítása és visszavonása nyitott. |
| `.picasa.ini`, SQLite-index, bal hasáb, rács és kijelölés: `0x0053de70` utólagos hívás, teljes hatása NINCS MEG | `src/picasapy/printing/poster.py:51-70,121-123`; nincs poszter-specifikus indexhívás | Eredeti programfelvétel kell a fájlok, `.picasa.ini`, `index.db`, mappalista, rács és kijelölés előtte-utána állapotával. |

## A két független út

- **A út:** a `0x00530c10` utasításszintű olvasása és meglévő Ghidra-kimenete a menü utáni párbeszédet, a két lapciklust, a névmintát, a JPEG-írást és az utólagos hívást követi végig. A `0x009d6010` külön diszasszemblálása megmutatja a `wb` fájlnyitást és a hibavisszatéréseket.
- **B út:** az index `xrefs` és `string_xrefs` táblái, valamint a `paszta.py` memória-kapuval végzett teljes `.text` operandus-keresése egymástól függetlenül azonosítja a `0x9d30` menürekordot és a három közvetlen `0x00530c10` hívási helyet. A statikus PE-adatkiolvasás külön ellenőrzi az átfedési konstansok számait; a helyi `poster.py` pedig a jelenlegi név-, minőség- és kiterjesztési szabályt mutatja.
- A két út egyezik a menü-hívásról, a három statikus akcióútról és a lapírás paramétereiről. Az eredeti futás utóhatásairól egyik út sem ad mérést, ezért a teljes folyamat bizonyítottsága feltételes marad.

## Cáfoló kísérlet

**Vizsgált feltevés:** a Poszter egyetlen belépési pontja a Létrehozás menü. A `paszta.py` teljes `.text` pásztázása után célzottan ellenőriztem a `0x005d59d1` és `0x005ddcb6` hívási helyet. A `0x005d56e0` ág a `toys/toy8` szövegre, a `0x005ddb80` ág a `makeposter` szövegre hívja ugyanazt a `0x00530c10` kezelőt. A „csak menüút létezik” feltevés megdőlt. A cáfoló ellenőrzése ugyanazzal a mércével történt: a két callsite és a hozzájuk tartozó ág diszasszemblálása igazolja a kódút meglétét, de a `toys/toy8` felületi elérhetőségét nem.

## A jegy „Kész, ha” pontjai

- ⛔ **Minden belépési pont és feltétel:** a Létrehozás menü és a Képtálca `makeposter` akció statikusan azonosított. A `toys/toy8` hívás UI-kapuja, az engedélyezési feltételek és a kontextusmenü/gyorsbillentyű kérdése futásidejű vagy további célzott bizonyíték nélkül nyitott.
- ⛔ **Ablak, alapérték, állapot, kérdések:** a mezők, értéktartományok, területi papírméretek, az inicializáló nullázása, OK és Cancel statikusan igazolt. Az eredeti effektív első értékek, a `factor` és `overlap` mentése, valamint a létrehozás utáni bármely kérdés nincs mérve.
- ⛔ **Fájlok és alkalmazáshatás:** a lapok rácsa, névmintája, kiterjesztése és JPEG-minősége statikusan igazolt. Az overlap képpontjai, `.picasa.ini`, index, bal hasáb, rács és kijelölés változása nincs eredeti felvétellel ellenőrizve.
- ⛔ **Hiba, megszakítás, hálózati vagy írásvédett cél, visszavonás:** az író visszatérési értékének kezelése és a kódutak részben ismertek, de felhasználói hatásuk nincs mérve. A lefedettségi pont teljesítése eredeti programfelvételt igényel.

## Javasolt jegytörzs-bővítés

**Javasolt fejlesztői jegytörzs: a Képtálca önálló Poszter gombja**

Eredeti: `0x005ddcb6` (`makeposter` ág a `0x005ddb80` akció-elosztóban), ugyanazt a `0x00530c10` kezelőt hívja. A meglévő menüspecifikáció a Képtálca gombját és címkeazonosítóját is rögzíti (`picasa-menu-parancsok-viselkedes.md:1940-1942`).

Nálunk: `src/picasapy/app/qml/PicasaPy/PicasaCreateMenu.qml:23-27` egyetlen Létrehozás menüelemet ad; a poszterhez külön Képtálca-vezérlő nincs a QML-ben.

Teendő: adjunk külön Képtálca Poszter műveletet, amely a meglévő poszterpárbeszédet nyitja meg. A láthatóság és engedélyezés feltételét a fejlesztés előtt eredeti Picasa-felvétellel kell rögzíteni.

Kész, ha:

1. A Képtálcán külön Poszter gomb található a Létrehozás menüelemen felül.
2. A gomb ugyanazt a poszterpárbeszédet nyitja meg, és ugyanazokat a lapgeneráló opciókat használja.
3. Láthatósága és engedélyezése az eredeti program felvételével összevethető állapotokban egyezik.
4. A menüút továbbra is a meglévő párbeszédhez és kimenethez vezet.

Ezen kívül fejlesztési eltérést még nem javaslok: a kimeneti név, a formátum és a minőségi érték statikusan egyezik; az overlap és az eredeti utóhatások külön mérés nélkül nem minősíthetők eltérésnek.

## Új kutatási jegyjavaslatok

Nincs külön új jegyjavaslat. Az eredeti programfelvétel a #7306 nyitott „Kész, ha” pontjainak eldöntéséhez szükséges.

## Nyitott

- Ghidra-kör kell: `0x0053de70` - az egyes poszterlapok utáni `AddLocateFile` hívás index-, balhasáb-, rács- és kijelöléshatása [blokkoló]. A meglévő Ghidra-kimenetekben a `0x0053de70` poszterhívóként szerepelnek, de a függvény teljes dekompilációja nem található.
- Eredeti Picasa 3.9 Colab-felvétel kell: friss profillal a menü és a Képtálca gomb állapota; egyszeres és többszörös kijelölés; a párbeszéd első és ismételt megnyitása; az OK, Cancel, be- és kikapcsolt overlap; az írásvédett és hálózati cél; a létrejött fájlok és `.picasa.ini`/index előtte-utána állapota; az állapotsor, rács, kijelölés és visszavonás rögzítése.
- Aszimmetrikus tesztképpel kell mérni az eredeti overlap képpont-határait, a kerekítést, az esetleges levágást és a metaadatokat. A mérés előtt ezekre nincs pontos átadott érték.
- A poszterpárbeszéd `factor`, `paper`, `overlap` beállításainak első és következő megnyitás közötti változását mérni kell.

## Módosított fájlok

- `docs/specs/paritas-folyamat-7306.md`: új, a #7306-ra szűkített folyamat-összevetés és nyitott bizonyítéklista.
- `docs/specs/00-index.md`: új hivatkozás erre a lapra.
- `.codex-jelentes.md`: hozzáférési és kutatási ellenőrzőpontok a folytathatósághoz.

## Eredeti mérés (#794, #795, 2026-11-20)

### Következtetés

A Picasa 3.9 két külön futásban 200%-os, `4x6` papírméretű, átfedés nélküli poszterpárbeszédet mutatott. Egy 800×800 képpontos `color_patches.jpg` képből négy JPEG-lap keletkezett a forrásmappában; a Picasa ezután a `1-1-color_patches.jpg` lap szerkesztőnézetét nyitotta meg, a forráskép pedig a Selection tálcán maradt. A második megnyitáskor az egyszer bekapcsolt `Overlap tiles` ismét üres volt. A PicasaPy kód az alapértékekkel és a fájlnév/darabszám mintával egyezik; a befejezés utáni automatikus szerkesztőnézet helyett az eredmény-párbeszédet nyitja meg.

**Bizonyítottsági fok: feltételes.** Az alapértékek és a kimeneti fájlok két külön Picasa-futásban ismétlődtek, és a képernyőképet a fájllista is alátámasztja. Az átfedés megőrzését és a befejezés utáni nézetet egy-egy futás mérte; a PicasaPy-oldal forráskódból, nem futtatott összehasonlításból ismert. A teljes #7306 issue-törzs nem része a kapott feladatleírásnak, ezért ez a lap csak a megadott mérési kérdésekről következtet.

### Módszer és forrás

- Eredeti program: Picasa 3.9 Colab-felvételek, a terv `m7305/terv.md` f05 és f06 lépéssorai szerint.
- **#794 / f05:** egy kijelölt kép (`color_patches.jpg`), `kepernyo__09`-`15`, `kepmappa__lista.json`.
- **#795 / f06:** egy kijelölt kép, `Overlap tiles` bejelölése, OK, majd a párbeszéd újranyitása; `kepernyo__11`-`21`, `allapot.json`, `kepmappa__lista.json`.
- A bináris parancs, beállítások és kimeneti út korábbi elemzése: `picasa-create-features.md` 3.1; különösen `ID_POSTER` `0x9d30`, a kezelő `0x00530c10`, a párbeszéd `0x007387c0`, valamint a `%d-%d-%s` fájlnév-formátum.
- A `kepmappa__lista.json` teljes mappalistája 91 meglévő bejegyzést és 4 új poszter-JPEG-et tartalmaz; a Picasa képernyőjén a képtár számlálója 28/28. E két számlálás eltérő nézetre vonatkozik, ezért nem helyettesítem egymással.

### Eredeti / nálunk / teendő

| Eredeti (bináris cím / mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x007387c0` párbeszédkonstruktor; #794 `kepernyo__11` és #795 `kepernyo__11`: Poster size `200%`, Paper size `4x6`, `Overlap tiles` üres. Mindkét felvétel azonos első megnyitási értéket mutatott. | `src/picasapy/app/qml/PicasaPy/PosterCreateDialog.qml:36-51`: minden nyitáskor 200%-ot választ, az átfedést kikapcsolja; a papírméretet a mentett értékből tölti be. Az amerikai méretkészlet és alapérték `src/picasapy/app/poster_controller.py:99-120`. | A mért amerikai beállításban egyezik; nincs igazolt fejlesztési eltérés. A más régióban látható papírméretet azonos lokalizációval kell összevetni. |
| `0x005cc150` → `0x00530c10`; #794 `kepernyo__09`-`11`: egy kijelölt képnél a `Make a Poster...` menüpont aktív és megnyitja a Poster Settings ablakot. | `src/picasapy/app/qml/PicasaPy/PicasaCreateMenu.qml:23-27`; a kapu `MainMenuBar.qml:157-158`. | Az egyképes mérés egyezik. Az eredeti 0 kijelölt képes aktiválási állapotát az f05/f06 nem vizsgálta; arra ne terjesszük ki ezt a leletet. |
| #794 `kepernyo__12`-`15` és `kepmappa__lista.json`: az `800×800`-as forrásból négy új fájl jött létre a `drive_c/PicasaTeszt` mappában: `0-0-color_patches.jpg`, `0-1-color_patches.jpg`, `1-0-color_patches.jpg`, `1-1-color_patches.jpg`. A Picasa által kijelzett utolsó lap `400×400` képpontos. | `src/picasapy/printing/poster.py:101-123`: a nagyítás százasa adja a rács méretét; a lapnév `<oszlop>-<sor>-<forrásnév>.jpg`, a forrás mappájába írva. A párbeszéd `PosterCreateDialog.qml:54-63` átadja a 200%-ot és a papírméretet. | A vizsgált 200%-os négyzetes esetben a kimeneti darabszám, nevek és célmappa egyeznek. A szimmetrikus 2×2 kimenet a névben szereplő sor/oszlop szemantikáját önmagában nem dönti el; az eltérő képarányú geometriát és az átfedés képpontjait ne tekintsük e méréssel igazoltnak. |
| #794 `kepernyo__15`: a Picasa szerkesztőnézetre vált, a `PicasaTeszt > 1-1-color_patches.jpg` lapot mutatja, a képtárban `28 of 28` jelzéssel; a Selection tálcán az eredeti kép miniatűrje marad. | `src/picasapy/app/qml/PicasaPy/MainWindowDialogStack.qml:309` → `CreateDialogs.qml:187-192`: siker után a `Poster tiles saved.` eredmény-párbeszédet és a fájlutakat mutatja. A `poster_controller.py:122-208` a kimeneti fájlok listáját jelzi. | Eltérés: a Picasa automatikusan az utolsó poszterlap szerkesztőnézetét nyitja, a PicasaPy sikerútja pedig eredmény-párbeszédet nyit. Lásd D1. |
| #795 `kepernyo__13`, `kepernyo__20`: az első panelen az átfedés bejelölve, a következő megnyitáskor üres. | `PosterCreateDialog.qml:50` minden megnyitáskor `false`-ra állítja a jelölőt. | A beállítás Cancel/újranyitás állapotában egyezik. Nincs fejlesztési eltérés erre a megfigyelt viselkedésre. |

### Bizonyítottság és cáfoló kísérlet

- **A, eredeti képernyők:** #794 és #795 képei megmutatják a beállításokat, az OK utáni szerkesztőnézetet, a kijelölést és az átfedés második megnyitáskori állapotát.
- **B, fájlrendszer-lista és kódsorok:** #794/#795 `kepmappa__lista.json` listája a négy új nevet és méretet rögzíti; a PicasaPy `poster.py` fájlnév- és lapgeneráló kódja, illetve a `CreateDialogs.qml` sikerútja külön forrásból hasonlítható hozzá.
- **Egyezés:** a panel 200% / 4x6 / átfedés ki alapértéke, a négy 200%-os fájl és az átfedés visszaállása egyezik a megvizsgált PicasaPy-kód viselkedésével.
- **Cáfoló kísérlet:** a „bekapcsolt átfedés a következő megnyitásra is megmarad” állítást a #795-ben próbáltam cáfolni. A `kepernyo__13` képen bekapcsolt, a `kepernyo__20` képen kikapcsolt állapot látszik, miközben az `allapot.json` mindkét esetben `Poster Settings` ablakot jelez. A második kép a Cancel előtti párbeszédet mutatja, tehát nem a bezárás utáni képet néztem félre.

### A megadott mérési kérdések állapota

1. ✅ **Poszter alapértékei:** 200%, `4x6`, átfedés kikapcsolva; két külön futás képe egyezik (#794/#795 `kepernyo__11`).
2. ✅ **Létrejött fájlok neve és darabszáma:** négy megnevezett JPEG az eredeti mappában (#794 `kepmappa__lista.json`).
3. ✅ **Picasa végállapot:** szerkesztőnézet, utolsó lap `1-1-color_patches.jpg`, képtár `28 of 28`, Selection tálcán az eredeti kép (#794 `kepernyo__15`).
4. ✅ **Átfedés újranyitáskor:** a bekapcsolt állapot a második megnyitásra kikapcsolt (#795 `kepernyo__13`, `kepernyo__20`).
5. ⛔ **PicasaPy végállapot futtatott egyezése:** nem futtattam PicasaPy-t; a forrásban siker-párbeszéd van, az eredeti pedig szerkesztőnézetre vált. A runtime-paritás nincs igazolva.

### Javasolt fejlesztői jegytörzs

#### D1. A poszterlap elkészülte utáni nézet

**Eredeti:** a Picasa-colab-jobs #794 `kepernyo__15` képe szerint az OK után az Editor nézet nyílik meg az utolsó lapon, `1-1-color_patches.jpg`-n, `28 of 28` számlálóval; a Selection tálcán az eredeti `color_patches.jpg` marad.

**Nálunk:** `MainWindowDialogStack.qml:309` és `CreateDialogs.qml:187-192` siker-párbeszédet nyit a poszterlapok útvonalaival; nincs ebben a sikerútban explicit editor-navigáció.

**Teendő:** a sikeresen elkészült lapok után frissítsük a könyvtárnézetet, nyissuk meg az utolsó generált lapot szerkesztőnézetben, és hagyjuk meg a forráskép kijelölését a Selection tálcán.

**Kész, ha:** egy kijelölt forráskép 200%-os poszterének elkészülte után a szerkesztő az utolsó kimeneti JPEG-et mutatja; a lap a mappában látszik, a képtár számlálója a friss állapotot mutatja, a forráskép Selection tálcás kijelölése megmarad.

### Nyitott

- `NINCS MEG`: a Poszter menü aktiválási feltétele 0 kijelölt képnél; a megadott mérések csak egy kijelölt képet használtak.
- `NINCS MEG`: a PicasaPy futásidejű rácsfrissítés, eredmény-párbeszéd és kijelölés utáni állapota; a fenti PicasaPy-összevetés kódszintű.
- `NINCS MEG`: az átfedés pontos képpont-geometriája, a nem négyzetes/eltérő képarányú kép lapjai, a metaadatok és a papírméret vágásra gyakorolt hatása. A megadott `kepmappa` lista neveket és fájlméreteket tartalmaz, képadatot nem.
- `NINCS MEG`: a papírméret megjegyzésének viselkedése megváltoztatott papírméret után; a f05/f06 nem választott másik méretet.
- Ghidra-kör nem szükséges a fenti, szűk mérésekhez; az átfedés pontos képlete és az eltérő képarányú lapozás külön, célzott bináris/futtatott munka.

### Módosított fájlok

- `docs/specs/paritas-folyamat-7306.md`: a #794/#795 felvételek, a PicasaPy-kód és a mért eltérés összevetése.
