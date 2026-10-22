# Forrás nélküli jegyek összevetése, 4. köteg (#5527)

Ez a lap a #5186 gyűjtő negyedik kötegének kilenc jegyét veti össze az eredeti
Picasa 3.9-cel. A forrás a helyi `Picasa3.exe`, a belőle kinyert
`runtime/respack.yt` erőforrások és a már rögzített bináris/specifikációs
vizsgálatok. A mai állapotot a PicasaPy QML- és Python-kódjából olvastam.
Az exe PE verzió-erőforrása `FileVersion 3.9.141.259` (`mérés (VS_VERSION_INFO)`),
ami igazolja, hogy vizsgált bináris a Picasa 3.9 ágából való.

Az eredeti programot ebben a körben nem futtattam, új Colab-felvétel nem
készült. A mérőadat archívumából nem bontottam ki fájlt: a feladatot lezáró
hover-, billentyű-, retusálási és importálási felvétel nem volt azonosítható.
Teljes `.text` pásztázás nem történt. Kódhoz nem nyúltam, tesztet nem
futtattam.

## Következtetés

Az eredeti forrás alapján a #4563 mai ismétlése eltérés; a #4546 és #4547
egyezik. A többi hat tételnél a kód és az erőforrás részben egyezik, de a
felhasználói felületen látható eredeti állapotot célzott Colab-felvételnek kell
lezárnia.

## Bizonyítottsági fok

**Feltételes, összesítve.** Megerősített a #4546, #4547 és #4563 forrás/kód
ítélete két külön úton; feltételes a #4527, #4532 és #4533; nyitott az eredeti
interakcióra a #4530, #4543 és #4596.

Ítélet: **EGYEZIK** = a bizonyított eredeti viselkedést a mai kód követi;
**ELTÉR** = bizonyított különbség; **FELTÉTELES** = a részleges forrás egyezik,
de egy felületi részlet nyitott; **NYITOTT** = a forrás nem dönti el az eredeti
viselkedést.

## 4. Tételenként

| jegy | eredeti forrás és lelet | mai kód | ítélet és teendő |
|---|---|---|---|
| #4527 | `runtime/respack.yt` → `thumbui_text.tre:112-113`: az `Add/Remove Star` súgó célja `thumbui/startoggle`. A More külön súgója `outputlayout_text.tre:56-60`. | `TrayBar.qml:1250-1271` a csillaggomb hoveréhez köti ugyanezt a súgót; a More külön szöveget kap (`:2279-2308`). | **FELTÉTELES, célhoz kötés egyezik.** Az erőforrás nem bizonyítja, hogy a felugró a képernyőn pontosan a csillag fölött jelenik meg. Colab-felvétel kell: a tálca csillagára, majd a More gombra külön rámutatni, mindkét súgót a gombhoz képest rögzíteni. |
| #4530 | `searchcontainer.tre:4-10` tartalmazza a rejtett `searchautocomplete` elemet; a bináris `0x0040e7b0` ezt az erőforrást kéri le. Ez a javaslatlista létezését bizonyítja, a billentyűkiosztást nem. | `SearchSuggestions.qml:42-68`, `MainToolbar.qml:821-832` és `Main.qml:2977-2986` kezeli a fel/le, Enter és Escape billentyűt. | **NYITOTT az eredeti kiosztásra; a mai kód a jegyben kért billentyűket kezeli.** Colab-felvétel kell: olyan keresés, amely több javaslatot ad; fel/le közben a kijelölés, Enter után a kiválasztás, Escape után a lista eltűnése legyen rögzítve. |
| #4532 | `searchcontainer.tre:30-95` felsorolja a szűrővezérlőket, az idősávot és külön a `search_icon` elemet; a `picasa-kereses-modok.md` 3. szakasza öt szűrőkapcsolót azonosít. A `search_icon` nem kap szűrőgomb-kezelőt. | `MainToolbar.qml:725-728` a korábbi kezelő nélküli jelet térközzel váltja fel; a mozgófilm külön szűrőgomb. | **FELTÉTELES.** A forrás vezérlőlistája nem igazol további szűrőgombot; a sávvégi pontos vizuális helyzetet nem dönti el. Colab-felvétel kell a keresősáv és az összes szűrő teljes szélességű nézetéről. |
| #4533 | `ui-audit-context-menus.md` 6.3: `AlbumPhoto::ID_FILEOPENWITH` → „Open With”, a listát Windows Shell társítások adják. A bináris `0x00730790` a helyi menü parancsát tartalmazza; a `0x00772300` az `OpenWithList` beállítási útvonalat dolgozza fel. | `PhotoContextMenu.qml:350-390` programválasztást ad; `OpenWithDialog.qml:26-33,45-61,94-107` és `fileops_controller.py:731-761` a kijelölt programmal indítja a képet. Windowson a Shell felülete marad. | **FELTÉTELES EGYEZÉS.** A menüparancs és az alkalmazáslista útja megvan, a statikus bizonyíték nem zárja össze az eredeti menükattintást a program tényleges indításával. Colab-felvétel kell: a képrács helyi menüjéből program választása, majd annak igazolása, hogy a kép abban nyílik meg. |
| #4543 | `editpanel.tre:219-229,958-962` megjeleníti a `thumbui/circlecursor` elemet és a `RetoucherHandler`-t; az `editpanel/retouchtarget` xrefje `0x005f74a0`. Ez a retusáló kört/kezelőt igazolja, de nem a cél- és forráskörök külön állapotát. | `PhotoViewer.qml:3862-3882,3906-3944` rögzíti az első kattintás célját, a második kattintás forrását, és külön cél-, forrás- és egérkurzorkört rajzol; a vezérlő útja `edit_controller.py:1727-1747`. | **NYITOTT az eredeti két kör viselkedésére.** Colab-felvétel kell: retusálás aktiválása; első kattintás a célon; egérmozgatás a forrásra; a cél és a mozgó forrás/kurzorjelölő rögzítése; második kattintás utáni állapot rögzítése. |
| #4546 | `edittextpanel.tre:19-22` adja a betűtípus-legördülőt. A `0x0062d750` szövegpanel-építő a `edittextpanel/fontfamily` elemet használja és meghívja a `0x00825e90` betűcsalád-lekérdezőt; utóbbi a GDI32 `EnumFontFamiliesExW` importot (`0x0092348a`) hívja (`0x00825ef8`). | `EditorTextPanel.qml:121-131` a kontroller listáját mutatja; `edit_controller.py:937-943` és `render/text_fonts.py:98-137` Qt alatt a telepített rendszer-betűcsaládokat kéri le. | **EGYEZIK - megerősített.** Az eredeti szövegpanel betűcsaládokat enumerál; a mai alkalmazás a Qt rendszer-betűkészletét kínálja. |
| #4547 | `edittextpanel.tre:75-97` három külön erőforrásréteget rendel a balra, középre és jobbra igazításhoz. A `runtime/respack.yt` három rétegének pixelképe különböző vonaligazítást mutat. | `EditorTextPanel.qml:238-288` külön `AlignIcon` elemeket és igazítási értékeket ad; `AlignIcon.qml:20-35` ezek szerint helyezi el a vonalakat. | **EGYEZIK - megerősített.** Az eredeti ikonok különbözők, és a mai három jel is különbözik. A képpont-pontosságú alakazonosság nem volt a jegy állítása. |
| #4563 | A `oneup.tre:75-81` nézőbeli `oneup/prev` és `oneup/next` gombokra `mousedown`-t ad, `setautorepeat`-et nem. Ugyanebben az erőforrásban a `plusone`/`minusone` kap `setautorepeat`-et (`:133-143`). A `0x008032e0` kattintási ágai a `0x00802980`/`0x008029f0` léptetőket hívják; a `0x00803180` ismétlő hurka külön egérgörgő-esemény (`0x20a`). | `PhotoViewer.qml:1855-1863,2021-2029` `autoRepeat: true`-t állít be mindkét nézőgombra. | **ELTÉR - megerősített.** A korábbi `szerkeszto-felso-sav.md:193-197` hivatkozás a `filmcontainer` filmszalag-nyilaira vonatkozik, nem a `oneup` nézőgombokra. Teendő: a két nézőgombból törölni az `autoRepeat: true`-t és az arra hivatkozó megjegyzést; a filmszalag gombjainak ismétlését ez nem érinti. |
| #4596 | A bináris `0x00520fa0` az `Import Files/Folder` címet (`0x00c88d70`) használja; az `acquirepanel_text.tre:114-115` kommentelt súgója „folder … or single images from disk” szöveget tartalmaz. A cím és a kommentelt súgó a fájlforrás szándékát jelzi, de nem bizonyítja az aktív fájlválasztó műveletét. | `ImportSourceDialog.qml:368-377,978-1004` `FileDialog.OpenFiles`-t használ; `import_source_controller.py:795-814` a kijelölt fájlokat beolvassa; `importsource.py:254-286` egyedi fájlútvonalakból épít forrást. | **NYITOTT az eredeti tényleges fájlkijelölésre; a mai kód támogatja.** Colab-felvétel kell: az eredeti importpanelről fájlt tallózni, legalább egy kiválasztott képet importálni, majd a kiválasztott kép megjelenését rögzíteni. |

## A két független út

| jegy | A út | B út | egyezés |
|---|---|---|---|
| #4527 | `thumbui_text.tre` a csillagsúgót a csillaghoz rendeli. | A More külön `outputlayout_text.tre` súgót kap; a mai QML is külön kezeli a két gombot. | A célhoz kötés egyezik; a képernyőn mért pozíció nyitott. |
| #4530 | A `.tre` és a `0x0040e7b0` bizonyítja a javaslatlista vezérlőt. | A mai QML billentyűkezelése külön út, az eredeti billentyűkiosztást nem bizonyítja. | Nem elegendő az eredeti viselkedés eldöntéséhez. |
| #4532 | A `searchcontainer.tre` teljes elemkészlete. | A `picasa-kereses-modok.md` 3. szakaszának bináris sztringkörnyezete (`0x00660c80`) azonosítja a szűrőcsaládot. | Nincs további szűrőgomb; a sávon belüli pontos hely nyitott. |
| #4533 | A `0x00730790` menüparancs és az `AlbumPhoto::ID_FILEOPENWITH`. | A `0x00772300` `OpenWithList` társításlista-útja, valamint a mai kiválasztás/indítás kódja. | A programválasztás egyezik; a korabeli menükattintás és indítás futó igazolása hiányzik. |
| #4543 | A `.tre` retusáló overlayt és körkurzort nevez meg. | A külön xref (`0x005f74a0`) a `retouchtarget` vezérlőt is azonosítja, de egyik út sem mondja meg a két kör láthatósági sorrendjét. | A két eredeti út a retusáló/target vezérlőt igazolja, nem a cél-/forráskör viselkedését. |
| #4546 | A `0x0062d750` a szövegpanel betűlista-elemét építi. | A `0x00825e90` `EnumFontFamiliesExW`-t hívja; a két függvény között bináris hívási él van. | Egyezik: a szövegpanel rendszerbetűket kér le. |
| #4547 | A `.tre` három külön ikonréteghez rendeli a három igazítógombot. | A respackből kivont három réteg pixelei eltérően igazított vonalakat adnak. | Egyezik; a mai kód külön jeleket rajzol. |
| #4563 | A `oneup.tre` a prev/next gomboknál csak `mousedown`-t ad, ismétlést nem; a `picasa-eger-es-kijeloles.md` 7. szakaszának ismétlő-listája is csak a plusz/mínusz gombokat sorolja fel. | A `0x008032e0` a prev/next parancsot kezeli; a külön ismétlő út `0x00803180`-ban az egérgörgőé. | Egyezik: az eredeti nem kér tartott gombos ismétlést; a mai kód eltér. |
| #4596 | A `0x00520fa0` fájlokat és mappát nevező címe. | A kommentelt tooltip egyedi képeket említ, de aktív fájlválasztásra nincs bizonyíték. | Nem elegendő az eredeti tényleges működés eldöntéséhez. |

## Cáfoló kísérlet

A #4563-hoz azt a saját következtetésemet próbáltam megcáfolni, hogy az eredeti
néző nyilai nem ismételnek: hátha a korábbi `m_autorepeat`-forrás ugyanazokra a
gombokra vonatkozik, vagy a OneUpUI eseménykezelő tartott egérgombnál ismétel.
Az első lehetőséget a két külön erőforrásnév cáfolja: a `filmcontainer` nyilai
és a `oneup/prev`-`oneup/next` eltérő vezérlők. A másodikat az ellenőrzött
`oneup.tre` és a `0x00803180` eseményút nem támasztja alá: explicit
automatikus ismétlés a `plusone`/`minusone` vezérlőkön van; a binárisban
ismételt léptetés az egérgörgő eseményén látszik. A cáfoló ellenőrzése ugyanezt
az eredményt adta, ezért a `filmcontainer`-re hivatkozó korábbi egyezés hibás.

## A jegy „Kész, ha” pontjai

- ✅ **#4527:** eredeti súgócél és mai gombkötés dokumentálva. A hover-felvétel hiányát és a szükséges lépést megneveztem.
- ✅ **#4530:** a javaslatlista eredeti erőforrása, mai billentyűkezelés és a nyitott Colab-mérés dokumentálva.
- ✅ **#4532:** eredeti vezérlőkészlet és mai térköz dokumentálva; a sávvégi vizuális helyzethez felvételi lépés szerepel.
- ✅ **#4533:** eredeti parancs és társításlista-forrás, mai programválasztás/indítás dokumentálva; a futó igazolás határa jelezve.
- ✅ **#4543:** eredeti retusáló körkurzor-forrás, mai cél-/forráskör-kód és a szükséges felvétel dokumentálva.
- ✅ **#4546:** eredeti szövegpanel-építő, GDI-hívás és mai rendszerbetű-lista összekötve.
- ✅ **#4547:** eredeti három külön ikonréteg és a kivont képek, valamint a mai három jel dokumentálva.
- ✅ **#4563:** eredeti forrás, mai eltérés és pontos megvalósítási teendő dokumentálva.
- ✅ **#4596:** eredeti cím és kommentelt szándék, mai fájlválasztási út, valamint a hiányzó eredeti működés felvételi lépése dokumentálva.

## Javasolt jegytörzs-bővítés

### #4563 - fejlesztői teendő

| | lelet |
|---|---|
| **Eredeti** | A `oneup/prev` és `oneup/next` a `oneup.tre` szerint `mousedown` gomb, automatikus ismétlés nélkül; a kattintást a `0x008032e0` ágai a `0x00802980` és a `0x008029f0` léptetőre vezetik. A `m_autorepeat` a filmszalag másik vezérlőpárjához tartozik. |
| **Nálunk** | A `PhotoViewer.qml` előző/következő gombja `autoRepeat: true`. |
| **Teendő** | A `viewerPrevButton` és `viewerNextButton` `autoRepeat: true` sorának törlése, a két elavult megjegyzés javítása. A filmszalag saját ismétlése maradjon a maga vezérlőin. |

**Kész, ha:** a néző előző/következő gombja egy lenyomásra egy képet lép; a filmszalag nyilai továbbra is nyomva tartva ismételnek; a kódmegjegyzés a `oneup.tre` forrásra hivatkozik.

A többi tételnél a jelenlegi bizonyíték vagy egyezést mutat, vagy a fenti Colab-felvételre vár; fejlesztői módosítást egyikre sem javaslok a nyitott eredeti viselkedés kitalálása nélkül.

## Új kutatási jegyjavaslatok

Nincs. A nyitott pontok a most vizsgált jegyek eredeti viselkedésének célzott Colab-felvételei; külön kutatási kérdést nem alkotnak.

## Nyitott

- #4527: a két súgó tényleges, gombhoz viszonyított helye - Colab hover-felvétel.
- #4530: az eredeti Up/Down/Enter/Escape viselkedése - Colab-felvétel, vagy célzott key-event-kezelő visszafejtése.
- #4532: a szűrősáv végének pontos eredeti képe - teljes szélességű Colab-felvétel.
- #4533: az eredeti Open With menüpont kiválasztásának és képindításának futó igazolása - Colab-felvétel.
- #4543: a cél- és forráskör eredeti kattintási/mozgatási állapota - retusálási Colab-felvétel.
- #4596: az eredeti tényleges fájlkijelölés és import - egyedi fájlos Colab-felvétel.

## Módosított fájlok

- `docs/specs/forras-audit-5186-4.md` - a #5527 kilenc jegyének negyedik kötege.
- `docs/specs/00-index.md` - a negyedik köteg hivatkozása.
- `docs/specs/paritas-ellenorzes.md` - elavult #4530, #4532, #4533, #4546, #4547, #4563 és #4596 sorok pontosítása.
