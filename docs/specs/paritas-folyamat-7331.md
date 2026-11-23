# #7331: Beállítások OK-ja: arcküszöb-frissítés és a `0x00487590` szerepe

**Állapot: a működés lezárva a binárisból (erős fok), a látható panelváltozás felvétele a fejlesztői jegy elfogadási próbája.** A Beállítások OK-ja a `0x00487590`-et csak akkor futtatja, ha a `FRSuggestionThreshold` vagy a `FRSuggestionSingleThreshold` értéke megváltozott. A függvény személyalbumonként egyezteti a címketagságot, utána az OK-kezelő háttérmunkát ütemez (`0x0047baf0`), és a panelobjektum `+0x166` bájtját 1-re állítja. A bájt Személyek panelre vonatkozó szerepe **erős következtetés**, nem közvetlenül olvasott tény: az olvasója nincs azonosítva.

## Forráshivatkozás és hatókör

Ez a lap a [paritas-folyamat-7325.md](paritas-folyamat-7325.md) 5. szakaszának **E jegyét** zárja le ("az arcküszöb-újratöltés és a `0x00487590` jelentése"). A két lap összevetése:

| A 7325-ös lap állítása | Ennek a lapnak az eredménye |
|---|---|
| 1.4 g sor, 2. szakasz 12. sor, 5. szakasz E jegy: a `0x0048aab0` **mindig `0xf4240`-et ad** (`0x0048ae7e`), ezért az ág minden OK-n lefut. | **Megdőlt.** A `0x0048ae7e` csak az egyik visszatérési ág: ha a két küszöb változatlan, a függvény nullát ad (`0x0048adc4`), és a `0x00487590` nem fut. Az OK-ra szóló frissítés tehát **küszöbváltozáshoz kötött**. |
| 1.4 g sor és 6. szakasz 6. kérdés: a `0x00487590` jelentése NINCS MEG. | **Megválaszolva** (erős fok): személyalbumonként címketagságot egyeztet; a listát a `0x00449a90` adja. |
| E jegy: Ghidra-dekompilálás és Colab-felvétel kell. | A dekompiláció elkészült. A Colab-felvétel a fejlesztői jegy elfogadási próbájává lett (lásd alább). |
| Az 1.4 többi sora (a-f, h, i), az A-D jegyek, az 1-5. és 7-9. kérdés. | Érintetlenek. |

Ahol a két lap eltér, ez a lap az érvényes: az állítása a `0x0048ad9e`-`0x0048adcc` utasításokra épül, a 7325-ös lap csak a `0x0048ae7e` ágat látta.

A vizsgált eredeti `Picasa3.exe` a 7325-ös lapon megadott példány. Csak statikusan vizsgáltam: Ghidra-dekompiláció (`0x00487590`, `0x00449a90`, az OK-kezelő `0x005cf5b0` sentinel-ága) és célzott utasításszintű diszasszembly (`0x0048aab0`, `0x00487590`). Teljes `.text` pásztázás nem történt.

## Következtetés

1. **A kapu (bizonyított).** A `0x005cf5b0` a `0x0048aab0(0)` eredményét `0xf4240`-hez hasonlítja, és csak egyezéskor hívja a `0x00487590`-et. A `0x0048aab0` az új és a korábbi `FRSuggestionThreshold`, valamint `FRSuggestionSingleThreshold` értéket veti össze: egyezéskor nullát, eltéréskor `0xf4240`-et ad. A `FRSortThreshold` (a felületen `facethresh1`) újratöltődik, de a kapuban nem vesz részt.
2. **A sentinel ág sorrendje (bizonyított).** `0x0097e4c0`, a köteg-számláló (`[0xd6793c]`) növelése, `0x00487590(+0x2bc objektum)`, feltételesen `0x0047baf0(0, 0)`, a számláló csökkentése, a `+0x166` bájt 1-re állítása, nullára érő számlálónál a nyíl kurzor visszaállítása.
3. **A `0x00449a90` (erős).** A személyalbum-azonosítók felsorolója a `+0x2bc` (`+700`) objektumon. A küszöbértékekhez csak a hívó kapuján át kapcsolódik; maga nem olvas küszöböt.
4. **A `0x00487590` (erős következtetés).** A `0x00449a90`-től kapott listán végigmegy, albumonként lekéri az albumobjektumot, és a `0x0045ecf0` (címketagság eltávolítása), majd a `0x004d9aa0` (címketagság hozzáadása) segéddel egyezteti a tagságot. A segédek szerepe korábbi, más hívási környezetű elemzésből származik. Közvetlen Red-pontszám hívás nincs benne (lásd a cáfoló kísérleteket).
5. **A `0x0047baf0` és a `+0x166` (erős következtetés).** A `0x0047baf0` a háttér-arcmunka sorába rak egy normál munkatételt (a `+0x10` jelző 0). A `+0x166` bájt egy jelző a `+0x2c0` panelobjektumon, amelyet az OK-kezelő 1-re állít. Hogy ez a **Személyek panel újratöltését** váltja ki, abból következik, hogy a `0x008226e0` ugyanezen az objektumon kéri a személyalbumok alsó listáit, és hogy a jelző a tagságegyeztetés után áll be; az olvasója nincs azonosítva.
6. **Ami NINCS MEG:** a Személyek panel pontos, látható változása az OK után (mely javaslatok jelennek meg vagy tűnnek el, emelt és lazított küszöbnél), és a `+0x166` olvasója. Az első a fejlesztői jegy felvételes elfogadási próbája, nem a kutatás blokkolója.

## Bizonyíték

| Érték vagy állítás | Fok | Forrás |
|---|---|---|
| A `0x005cf5b0` a `0x0048aab0(0)` eredményét `0xf4240`-hez hasonlítja; eltéréskor kihagyja a `0x00487590`-et. | bizonyított | bináris (`0x005cfe6d`-`0x005cfe79`); Ghidra-dekompiláció: `iVar6 = FUN_0048aab0(0); if (iVar6 == 1000000)` |
| A `0x0048aab0` az `arg=0` útban beolvassa a `FRSuggestionThreshold` (`0xc81cc0`), `FRSuggestionSingleThreshold` (`0xc81cd8`), `FRSortThreshold` (`0xc81cf4`) és `FRRecommendIncludeLimit` (`0xc81d04`) kulcsot, a mezők `this+0x3498`, `+0x349c`, `+0x34a0`, `+0x34a4`. | bizonyított | bináris (`0x0048aab0`-`0x0048ad98`) |
| A visszatérés csak a `this+0x3498` és `this+0x349c` mezőt (korábbi érték) hasonlítja az újonnan beolvasottal; mindkettő egyezésekor `xor eax, eax` (`0`), különben `0xf4240`. | bizonyított | bináris (`0x0048ad9e`-`0x0048adcc`, `0x0048ae7e`-`0x0048ae87`) |
| A felületi `facethresh0` kulcsa `FRSuggestionThreshold`, a `facethresh1` kulcsa `FRSortThreshold`. A `FRSuggestionSingleThreshold` (gyári 90) nem szerepel a vezérlő-kulcs táblában, és a teljes `.text` szerint csak a `0x0048aab0` és a `0x00415790` éri el. | bizonyított | bináris (`0x006e0eda`, `0x006e0ee8`, `0x0048ac6f`); [picasa-arcfelismeres.md §1.1](picasa-arcfelismeres.md), [picasa-arcfelismeres-kutatasi-naplo.md](picasa-arcfelismeres-kutatasi-naplo.md) |
| Sentinel esetén a hívó meghívja a `0x00487590`-et, majd feltételesen a `0x0047baf0(0, 0)`-t (ha a `+0x2a20` objektum létezik, és annak `+4` vtábla-hívása nullát ad), és beállítja a `*(param_2[0xb0] + 0x166) = 1` bájtot. | bizonyított | bináris (`0x005cfe7b`-`0x005cfed6`); Ghidra-dekompiláció |
| A `0x00487590` a `0x00449a90(param_1, &lista, 0, 0, 0)` hívással kér listát, a lista elemeire az albumobjektumot a `+0x48` alobjektum `+0x2c` vtábla-hívásával kéri le, majd `0x0045ecf0(param_1, &x, azonosító)` és `0x004d9aa0(param_1 + 0x68, &x, 0, 2)` következik; a függvény nullával tér vissza. | bizonyított | Ghidra-dekompiláció (`FUN_00487590`) |
| A `0x0045ecf0` címketagságot távolít el; a `0x004d9aa0` címketagságot ad hozzá. | erős következtetés | korábbi helper-azonosítások: [ui-audit-context-menus.md §D.8.3](ui-audit-context-menus.md), [picasa-arcfelismeres-kutatasi-naplo.md](picasa-arcfelismeres-kutatasi-naplo.md) |
| A `0x00449a90` személyalbum-azonosítókat sorol fel. A `0x0056c5a0` (a Személyek helyi menü építője) `FUN_00449a90(*(param_1 + 700), ...)` hívással kéri, és üres listánál a `ThumbUI::PeopleCMEmpty` szöveget adja; a `0x008226e0` (arcos filmkészítés) a `+0x2bc` objektumon kéri, és minden azonosítóhoz a `+0x2c0` objektumon alsó listát; a `0x00487590` albumonként iterál rajta. | erős (három hívó egybehangzó) | Ghidra-dekompiláció; [picasa-create-features.md](picasa-create-features.md) (`0x008226e0`); a `0x00449a90` öt hívójából kettő (`0x0048ef20`, `0x00490350`) nincs vizsgálva |
| A `0x0047baf0` a rekord `+0x10` bájtját 0-ra építi, és a munkasor-építőbe (`0x0049de00`) adja; a lánc `0x004987c0` -> `0x0047b020` (fogyasztó). A jelző pontos jelentése nyitott. | bizonyított a láncra; a jelentés NINCS MEG | [picasa-arcfelismeres-kutatasi-naplo-2026-10.md](picasa-arcfelismeres-kutatasi-naplo-2026-10.md) (`0x0047bb7a`, `0x0049de46`) |
| A `+0x166` bájt olvasója. | NINCS MEG | nem azonosított |
| A Beállítások OK-ja utáni Személyek panel pontos változása a mintaképeken. | NINCS MEG | felvétel kell (lásd az elfogadási próbát) |

## Két bizonyítéki út

- **A út: utasításszintű diszasszembly.** A `0x0048aab0` két lebegőpontos összehasonlítása (`fucompp`, `0x0048ad9e`-`0x0048adbd`) és a két visszatérési ág (`0x0048adc4`: nulla; `0x0048ae7e`: `0xf4240`), valamint a `0x00487590` teljes, 1273 soros célzott diszasszemblyje a közvetlen hívási célokkal.
- **B út: Ghidra-dekompiláció.** Az OK-kezelő sentinel-ága (`== 1000000`, a hívási sorrend, a `+0x166` írás), a `0x00487590` törzse (hívott függvények, az albumonkénti ciklus, a `return 0`) és a `0x00449a90` törzse, hívó-listájával.

A két út egyezik a kapuról, a hívási sorrendről és a tagságmódosító hívásokról. Mivel mindkettő ugyanazon bináris függvényeket elemzi, és független futásmérés a Személyek panelről nincs, a **teljes felhasználói következmény** (mi látszik a panelen) nem megerősített: a működés erős, a látható hatás NINCS MEG.

## Cáfoló kísérletek

1. **A "`0x0048aab0` mindig `0xf4240`" állítás cáfolata.** Az azonos `arg=0` útban a két küszöb változatlan ágát vizsgáltam: a `0x0048adc4` címen `xor eax, eax`, majd `ret 4`. Az állítás megdőlt; ez a 7325-ös lap azonos állítását is érinti (lásd a Forráshivatkozás szakaszt).
2. **A tagság-egyeztető olvasat cáfolási próbája.** A `0x00487590` teljes diszasszemblyjében a közvetlen hívási célok: `0x0097caf0`, `0x0097c810`, `0x006a2a60`, `0x006a2a30`, `0x009829f0`, `0x0074cf40`, `0x004d9aa0`, `0x0045ecf0`, `0x00449a90`, `0x00413490`, `0x004133e0`. A dokumentált `0x0048e1f0` Red-pontszám szűrő és a `0x0047baf0` nem szerepel közöttük. A Ghidra-törzs nem közvetlen hívásai: 16 vtábla-hívás `+0x18`/`+0x1c` ofszettel (az `EnterCriticalSection`/`LeaveCriticalSection` ág párja, zár és feloldás), 9 `LeaveCriticalSection` a `pcVar9` aliason át, és 1 albumobjektum-lekérés (`+0x2c`). Detektorra utaló indirekt hívás nincs, a `+0x2c` célfüggvényének törzse viszont nincs vizsgálva, ezért a kizárás erős, nem teljes. A próbát utasításszinten futtattam, nem indexhiányra építettem.
3. **A `0x00449a90` személyalbum-értelmezésének cáfolási próbája.** Azt próbáltam cáfolni, hogy a lista személyalbum-azonosító: ehhez olyan hívó kellene, amely másféle elemként használja. A három vizsgált hívó mind személyazonosítóként használja (helyi menü, filmkészítés, albumonkénti egyeztetés). Cáfolat nem adódott; a másik két hívó vizsgálatlansága miatt a fok erős, nem bizonyított.

## Igazolt eltérés és fejlesztői feladat

**Eredeti:** `0x005cf5b0` (OK-kezelő), `0x0048aab0` (küszöbváltozás-kapu, `0xf4240` sentinel), `0x00487590` (személyalbum-tagság egyeztetése), `0x00449a90` (személyalbum-azonosítók), `0x0047baf0` (munkatétel a háttér-arcmunka sorába), `*(param_2[0xb0] + 0x166)` (frissítési jelző a panelobjektumon).

**PicasaPy-forrás (szó szerinti idézet, a sor végi `noqa` megjegyzés elhagyva):**

`src/picasapy/app/face_scan_controller_settings_mixin.py:77-83`:
```python
    @Slot(int)
    def setSuggestionThreshold(self, step: int) -> None:
        """A javaslatküszöb mentése a tízfokozatú beállítási létrán."""
        self._settings.setValue(
            self.SUGGEST_STEP_KEY,
            self._ervenyes_kuszob_lepcso(step, DEFAULT_SUGGEST_STEP),
        )
```
és `src/picasapy/app/qml/PicasaPy/OptionsDialog.qml:164-170`:
```qml
        optionsDraft.commit()
        saveAcceptedOptionSettings()
        if (!clearCacheTouched)
            applySavedClearCacheFiles()
        if (fileTypesChanged && typeof controller.rescan === "function")
            controller.rescan()
        optionsWindow.visible = false
```

**Eltérés leírása.** Az eredeti OK-kezelő a küszöbváltozásnál (a `0x0048aab0(0)` eredménye `0xf4240`) azonnal egyezteti a személyalbumok címketagságát (`0x00487590`), háttérmunkát ütemez (`0x0047baf0`), és a panelobjektumon jelzőt állít (`+0x166`, erős következtetés szerint a Személyek panel újratöltéséhez). A PicasaPy OK-ja a javaslatküszöb módosított értékét csak a QSettings-be írja (`setSuggestionThreshold`), a `acceptOptions` (`OptionsDialog.qml:142-171`) pedig a fájltípus-váltásra figyel (`:143-159`, `rescan()` a `:168-169` sorban), a küszöbre nem. A küszöböt a csoportosító munka csak az indításkor olvassa (`face_scan_controller_embedding_mixin.py:61-67`), ezért az új érték a következő csoportosításig nem hat a javaslatokra.

## Javasolt fejlesztői jegytörzs

**Javasolt jegycím:** Beállítások OK: a javaslatküszöb módosítása után azonnal frissüljenek a Személyek panel javaslatai (az eredeti `0x005cf5b0` küszöbváltozás-kapuja)

**Mi a hiba:** A Beállítások ▸ Névcímkék fülén a Javaslatküszöb csúszka mozgatása és az OK után a Személyek panel javaslatai változatlanok maradnak, amíg új csoportosítás nem fut. Az eredeti Picasában az OK küszöbváltozás esetén azonnal egyezteti a személyek tagságát, háttérmunkát ütemez, és jelzi a panelnek a frissítést.

**Eredeti címekkel:**
- `0x005cf5b0`: az OK-kezelő; `0x0048aab0(0) == 0xf4240` esetén fut a küszöbváltozás ága.
- `0x0048aab0`: a `FRSuggestionThreshold` (felületen `facethresh0`) vagy a `FRSuggestionSingleThreshold` változása ad `0xf4240`-et; a `FRSortThreshold` (`facethresh1`, a PicasaPy-ban a csoportküszöb) változása **nem**.
- `0x00487590` + `0x00449a90` + `0x0045ecf0` + `0x004d9aa0`: személyalbumonkénti címketagság-egyeztetés.
- `0x0047baf0(0, 0)`: munkatétel a háttér-arcmunka sorába (ha a `+0x2a20` objektum létezik, és a `+4` vtábla-hívása nullát ad).
- `*(param_2[0xb0] + 0x166) = 1`: frissítési jelző a panelobjektumon (a Személyek panelre vonatkozó szerepe erős következtetés).

**Nálunk (fájl:sor):**
- `src/picasapy/app/qml/PicasaPy/OptionsTabNameTags.qml:104-123`: a csúszka (`from: 50`, `to: 95`, `stepSize: 5`) a piszkozatba ír (`root.stage("nameTags.suggestionThreshold", ...)`), az OK-n a `setSuggestionThreshold(step)` fut.
- `src/picasapy/app/face_scan_controller_settings_mixin.py:77-83`: a `setSuggestionThreshold` csak a `faces/suggestStep` kulcsot menti.
- `src/picasapy/app/qml/PicasaPy/OptionsDialog.qml:142-171`: az `acceptOptions` a fájltípusnál összeveti az OK előtti és utáni értéket (`:143-159`), a javaslatküszöbnél nem. Az `optionsDraft.isStaged(...)` minta a `:163` sorban már megvan.
- `src/picasapy/app/face_scan_controller_embedding_mixin.py:61-67`: a küszöböt a csoportosítás indításakor olvassa.
- A meglévő újraszámoló: `src/picasapy/index/face_groups.py:54` (`javaslatokat_ujraszamol(conn, suggest_threshold)`), hívja a `src/picasapy/app/face_scan_controller_suggestions_mixin.py:166-196` (`moreSuggestions`): index megnyitása, újraszámolás, `commit`, `unnamedCountChanged.emit()`. **Megszorítás:** a segéd csak a javaslat nélküli, névtelen arcokra ír új javaslatot (`state = 'unnamed' AND suggested_name IS NULL`), meglévőt nem von vissza, így csak a küszöb lazításánál ad új javaslatot.

**Teendő:**
1. Az `acceptOptions()`-ban a `commit()` előtt rögzítsd a javaslatküszöb mostani lépcsőjét (`faceScanController.suggestionThreshold()`), és commit után vesd össze az újjal. Csak a `faces/suggestStep` változása váltson ki frissítést; a `faces/clusterStep2` (csoportküszöb) változása önmagában ne.
2. Változásnál számold újra a javaslatokat az új küszöbbel a `javaslatokat_ujraszamol` segéddel, a `moreSuggestions` mintájára (`commit`, majd `unnamedCountChanged.emit()`, hogy a Személyek panel újratöltsön). Nagy könyvtárban a számítás ne blokkolja a felületet (az eredeti háttérmunkasorba ütemez).
3. Emelt küszöbnél a segéd nem von vissza korábbi javaslatot. Hogy az eredeti OK után csökken-e a lista (a `0x0045ecf0` tagságot távolít el), azt az elfogadási próba felvétele dönti el; csak ha csökken, kell visszavonás.
4. Változatlan küszöbnél az OK semmit ne számoljon újra.

**Kész, ha:**
1. A Javaslatküszöb módosítása és OK után újraindítás és új szkennelés nélkül újratöltődik a Személyek panel javaslatlistája (teszt: lazított küszöb után nő a javaslatos arcok száma, és az `unnamedCountChanged` megérkezik).
2. Változatlan küszöbnél az OK nem hívja a `javaslatokat_ujraszamol`-t (teszt).
3. A csoportküszöb önmagában nem indít újraszámolást (teszt).
4. **Elfogadási próba, látás alapján:** az arcos mintakészleten az eredeti Picasa felvétele (Névcímkék fül, a Javaslatküszöb csúszka mozgatása, OK, a Személyek panel javaslatlistája az OK előtt és után, a `FRSuggestionThreshold` registry-érték) és a PicasaPy renderelt képe ugyanazon a készleten. Eltérésnél a felvétel az irányadó, nem ez a lap.

## Nyitott kérdések mérlege

| # | Kérdés | Állapot |
|---|---|---|
| 1 | Mikor hívódik a `0x00487590`? | **LEZÁRVA** (bizonyított): csak ha a `0x0048aab0(0)` `0xf4240`-et ad, azaz a `FRSuggestionThreshold` vagy a `FRSuggestionSingleThreshold` változott. |
| 2 | Mi a `0x00449a90` listája, és hogyan kapcsolódik a küszöbökhöz? | **LEZÁRVA** (erős): személyalbum-azonosítók a `+0x2bc` objektumon; a küszöbhöz csak az OK-kezelő kapuján át kapcsolódik. |
| 3 | Mit tesz a `0x00487590`? | **LEZÁRVA** (erős következtetés): személyalbumonként címketagságot egyeztet; közvetlen Red-pontszám hívás nincs benne. |
| 4 | Mit tesz a `0x0047baf0`, és mi a `+0x166` bájt? | **LEZÁRVA** (erős következtetés): munkatétel a háttér-arcmunka sorába, illetve frissítési jelző a panelobjektumon; az olvasó nincs azonosítva. |
| 5 | Futhat-e közvetett Red- vagy detektorhívás a `0x00487590`-ben? | **LEZÁRVA** (erős): a nem közvetlen hívások közül 25 zár/feloldás, 1 albumobjektum-lekérés; a `+0x2c` cél törzse nincs vizsgálva. |
| 6 | Mi látszik a Személyek panelen az OK után (lazított és emelt küszöbnél)? | **ÁTSOROLVA** a fejlesztői jegy elfogadási próbájába (Kész, ha 4. pont). Nem blokkoló: a fejlesztői teendő a bináris láncból következik. |

**Nyitott kérdések: 5 lezárva · 1 átsorolva a fejlesztői jegy elfogadási próbájába · 0 blokkolt · 0 hatókörön kívül.**

## Mit NEM állítok

- Nem állítom, hogy a Beállítások OK-ja **újrafuttatja a Red detektort**: közvetlen hívás nincs, a közvetett hívások közül egy (`+0x2c`) nincs vizsgálva.
- Nem állítom, hogy a `+0x166` bájtot a Személyek panel olvassa: az olvasó nincs azonosítva.
- Nem állítom, hogy a `0x0047baf0` munkatétele a "javaslatok újraértékelése": a jelző jelentése a korábbi arcfelismerési kutatásban is nyitott (N1).
- Nem állítom, hogy a `0x0045ecf0` és a `0x004d9aa0` a PicasaPy `suggested_name` mezőjének felel meg: a címketagság és a javaslat kapcsolata nálunk az elfogadási próbán dől el.

## Módosított fájlok

- `docs/specs/paritas-folyamat-7331.md`: a #7331 eredményei, bizonyítottsági fokai, cáfoló próbái, a 7325-ös lappal való összevetés és a fejlesztői jegytörzs.
- `docs/specs/00-index.md`: indexhivatkozás erre a lapra.
- `changelog.d/7331.md`: változásnapló-töredék.
