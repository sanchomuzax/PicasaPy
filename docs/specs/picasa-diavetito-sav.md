# A diavetítő vezérlősávja az eredeti oneup.tre szerint (#5537)

Ez a lap a diavetítő alsó vezérlősávját veti össze az eredeti Picasa 3.9
`oneup.tre` erőforrásával és a kattintáskezelő diszasszemblálásával. A mai
sáv a `SlideshowView.qml` `controlsRow` sora. Minden állítás mellett cím vagy
fájl:sor áll. Ami nincs igazolva, az `NINCS MEG`.

A jegy 17 tételt említ. Ez a lap is 17 tételt vizsgál, és minden tételhez
külön sort ad.

**Bizonyítékforrások**

- Erőforrás: `referencia/tre-eroforrasok/oneup.tre` (szülő és horgonyzás),
  `oneuptext.tre` (feliratok), `macros.tre` (a horgony-makrók).
- Eseménykezelő: a OneUpUI vtáblája `0x00cbd5c4`. Ennek 22. eleme
  (`0x00cbd61c`) a `0x008032e0` diszpécser.
- Gomb-csomópont: a `ytButtonNode` vtáblája `0x00ce4874`. A kezelő
  `0x00a64050`, a tüzelés `0x00a65170` (vtábla 30. eleme, `0x00ce48ec`),
  a parancs-kibocsátó `0x00a64a10`.
- Konstruktor: `0x00802c60`, amely betölti az `oneup` erőforrást.
- Mai kód: `src/picasapy/app/qml/PicasaPy/SlideshowView.qml`,
  `src/picasapy/app/qml/PicasaPy/PicasaButton.qml`.

## 1. Csoportok és sorrend

A horgonyzást a `macros.tre` makrói adják: `m_offsetLB` bal-alsó
(`macros.tre:71-73`), `m_offsetRB` jobb-alsó (`macros.tre:97-99`), `m_centerX`
vízszintes középre (`macros.tre:11-12`), `m_offsetB` alsó (`macros.tre:56-57`).
A `stripback` (`oneup.tre:164-166`) a sáv tartója. A `centergroup`
(`oneup.tre:156-158`) ennek középre igazított gyermeke.

A `.tre` nem ad x-koordinátát a vezérlőknek. Ezért a sorrend a csoporton belül
magából az erőforrásból `NINCS MEG`. A `.tre` deklarációs sorrendje
(`oneup.tre:40-143`) nem vizuális sorrend, ezt bizonyítékként nem használom.
Az alábbi „Mai hely” oszlop a #7281 előtti kódot rögzíti; az új, képernyőn
mért sorrendet a következő táblázat adja.

| Vezérlő | Szülő és horgony (oneup.tre) | Csoport (a .tre szerint) | Mai hely (controlsRow, 1-től) | Eredmény |
|---|---|---|---|---|
| `exit` | `stripback`, `m_offsetLB` (40-42) | bal | 1 | EGYEZIK |
| `transtype` | `stripback`, `m_offsetLB` (103-105) | bal | 7 | ELTÉR |
| `timeline` | `centergroup`, `m_offsetLB` (59-61) | közép, bal almás | 2 (feltételesen) | ELTÉR |
| `prev` | `centergroup`, `m_offsetLB` (75-77) | közép, bal almás | 2 | ELTÉR |
| `auto` | `centergroup`, `m_offsetB` + `m_centerX` (71-73) | közép, középső | 3 | ELTÉR |
| `next` | `centergroup`, `m_offsetLB` (79-81) | közép, bal almás | 4 | ELTÉR |
| `minusone`, `plusone` | `dtclip` a `centergroup`-ban, `m_offsetRB` (133-143, 153-154) | közép, jobb almás | 10 (kijelzési idő blokk) | ELTÉR |
| `rotateleft` | `stripback`, `m_offsetRB` (87-88) | jobb | 5 | ELTÉR |
| `rotateright` | `stripback`, `m_offsetRB` (90-91) | jobb | 6 | ELTÉR |
| `star` | `stripback`, `m_offsetRB` (97-98) | jobb | 9 | ELTÉR |
| `captionbutton` | `stripback`, `m_offsetRB` (121-124) | jobb | 8 | ELTÉR |

Az eredetiben három csoport van: bal (`exit`, `transtype`), közép
(`centergroup`: `timeline`, `prev`, `auto`, `next` és a kijelzési idő blokk),
jobb (`rotateleft`, `rotateright`, `star`, `captionbutton`). A mai sor egyetlen
lista (`SlideshowView.qml:981`). A kijelzési idő blokk a jobb szélen áll, a
forgatás a sor közepén. Az `exit` az egyetlen tétel, amelynek a csoportja és a
helye egyezik.

### Képernyőn mért sorrend (#7281, #7197)

A `picasa-colab-jobs` #762 `video__08.mp4` felvételének 12. és 100. másodperce
alapján, szünetben balról jobbra: Kilépés, képikon és csúszka, forgatás balra,
forgatás jobbra, Előző, Lejátszás, Következő, csillag, átmenet-választó,
feliratmód, Display Time. A lista végén álló szünetben a képikon és csúszka
látszik; az első képen álló szünetben ugyanez a hely üres. A #7197 mérési jegy
rögzíti, hogy a két felvételi pont sorrendje egyezik.

A `oneup.tre` (a 40-143. sorok vezérlőelemei) nem tartalmaz csúszka- vagy
képikon-elemet, és működésükre sincs adat. A `sszoomsliderclip` név csak a
külön szerkesztői `editoneup.tre`-ben szerepel, ezért nem bizonyíték a normál
diavetítő csúszkájának funkciójára. A csúszka funkcióját a #7284 állapította meg
(lásd az 5. szakaszt), a #7322 pedig megvalósítja: a mért helyen a lista végén
megállt vetítésnél képikon és csúszka áll, máskor a hely üres.

## 2. Tételek elemenként

| Tétel | Eredeti forrás | Mai kód | Eredmény |
|---|---|---|---|
| 1. `exit` felirat | `oneuptext.tre:7-8` („Exit”) | `SlideshowView.qml:990` (`"✕ " + qsTr("Exit")`) | EGYEZIK (a szöveg). A ✕ jel nincs a `.tre`-ben. |
| 2. `exit` ikon | `oneup.tre:28-29` (`oneup/exit_icon`, `m_buttoniconleft`). Az ikon grafikája `NINCS MEG`. | `SlideshowView.qml:990` (✕ jel) | NINCS MEG |
| 3. `exit` művelet | `0x00803527`-`0x00803573`: a vezérlő vtábla `+0x24` metódusa egy objektumot ad. Ennek vtábla `+0x14` metódusát hívja `(0, 0)` argumentumokkal. A célobjektum `NINCS MEG`. | `SlideshowView.qml:992` (`show.stop()`) | NINCS MEG |
| 4. `timeline` gomb | `oneup.tre:59-61`, felirat `oneuptext.tre:4-5` („Timeline”). Kattintási ág: `0x00803500`-`0x00803522` (`0x00cbd528`), a `0x007fda00` hívással. | `SlideshowView.qml` `slideshowTimelineButton`; a `Main.qml` a vetítés lezárása után a menüvel közös `toggleTimeline()`-t hívja. | ELTÉR (a PicasaPy-beli belépési út alkalmazás-szintű) |
| 5. `auto` (lejátszás, szünet) | `oneup.tre:71-73`, ikon `67-69`. Kattintási ág: `0x00803486` (`0x00cbd510`), a `0x00803110` hívással. | `SlideshowView.qml:999-1004` (`togglePause()`, 1004) | EGYEZIK (a funkció) |
| 6. `auto2` | `oneup.tre:20-23` (gyökér-gyermek, a sáv felett, 97 képpontot hagyva az alja fölött). Kattintási ág: `0x008034c5` (`0x00cbd51c`), a `0x00803110` hívással. A kattintási célként való elérhetősége `NINCS MEG`: a `.tre`-ben nincs találat-jelző. | nincs megfelelő | NINCS MEG |
| 7. `prev` | `oneup.tre:75-77` (`Property mousedown 1`). Kattintási ág: `0x008035ab` (`0x00cbd43c`), a `0x00802980` hívással (a léptetés `[+0x3f4]` mezőjét csökkenti). Lenyomásra sül el: `0x00a643f8`-`0x00a64425`; a felengedési ág `0x00a64556`-`0x00a6455d` kihagyja. | `SlideshowView.qml:994-997` (`onClicked: show.goBack()`, 997). Nincs `lenyomasra`. | ELTÉR (felengedésre sül el) |
| 8. `next` | `oneup.tre:79-81` (`Property mousedown 1`). Kattintási ág: `0x008035f4` (`0x00cbd448`), a `0x008029f0` hívással (a `[+0x3f4]` mezőt növeli). Lenyomásra sül el, ugyanúgy, mint a 7. | `SlideshowView.qml:1006-1010` (`onClicked: show.advance()`, 1010). Nincs `lenyomasra`. | ELTÉR (felengedésre sül el) |
| 9. `rotateleft` | `oneup.tre:87-88`. Kattintási ág: `0x008036f2`-`0x00803723` (`0x00cbd454`), a `[+0x260]` objektum vtábla `+8` hívása `-1` iránnyal. | `SlideshowView.qml:1012-1016` (`rotateCurrent(-1)`, 1016) | EGYEZIK (a funkció és az irány). Az `↺` glifa `NINCS MEG`. |
| 10. `rotateright` | `oneup.tre:90-91`. Kattintási ág: `0x0080368a`-`0x008036b8` (`0x00cbd468`), a `[+0x260]` objektum vtábla `+8` hívása `+1` iránnyal. | `SlideshowView.qml:1018-1022` (`rotateCurrent(1)`, 1022) | EGYEZIK (a funkció és az irány). Az `↻` glifa `NINCS MEG`. |
| 11. `star` | `oneup.tre:97-98`. Kattintási ág: `0x00803733`-`0x008037be` (`0x00cbd4c4`), a `[+0x260]` objektum vtábla `+4` hívása a gomb állapotbájtjával. | `SlideshowView.qml:1057-1061` (`starCurrent()`, 1061) | EGYEZIK (a funkció) |
| 12. `transtype` (átmenet-választó) | `oneup.tre:103-105`. A kattintáskezelő nem ágazik rá. A név csak a `0x008037e0` láthatóság-kezelőben szerepel (`0x00803a30`-`0x00803a83`). A lista tartalma és a választás útja `NINCS MEG`. | `SlideshowView.qml` `slideshowTransitionBox`, a Timeline gombbal kölcsönösen kizáró láthatósággal. | EGYEZIK (láthatóság; a lista útja külön lelet) |
| 13. feliratgomb (`captionbutton`) | `oneup.tre:121-124` (`showtarget caption_yesicon`, `hidetarget caption_icon`), `oneup.tre:168-170` (`oneup/caption`). Kattintási ág: `0x00803373`-`0x008033b7` (`0x00cbd4d0`). A `[+0x359]` állapotbájt alapján a `0x009cd730` mutat, a `0x009cd760` rejt az `oneup/caption` elemen (`0x00cbd4a8`). | `SlideshowView.qml:1045-1056`. `feliratModok` a 120. sorban, a ciklus 1051-1055. | ELTÉR (2 állapot a binárisban, 3 a mai kódban) |
| 14. `plusone` (+) | `oneup.tre:133-135` (`setautorepeat 1`). Kattintási ág: `0x008033e3`-`0x00803401` (`0x00cbd4f0`), a `0x00802ff0` hívása `+1,0` értékkel. A felső határ `20`: `0x00802b7e`-`0x00802b8f` (`0x00cf4974`, f32 = 20,0). | `SlideshowView.qml:1131-1139` (autoRepeat 1137, `enabled: show.seconds < 30` 1138) | ELTÉR (felső határ: 30 a mai kódban, 20 a binárisban) |
| 15. `minusone` (-) | `oneup.tre:141-143` (`setautorepeat 1`). Kattintási ág: `0x00803438`-`0x00803447` (`0x00cbd500`), a `0x00802ff0` hívása `-1,0` értékkel (`0x00cf3ed0`). Az alsó határ `1`: `0x00802b6d` (`fld1`). | `SlideshowView.qml:1093-1107` (autoRepeat 1105, `enabled: show.seconds > 1` 1106) | EGYEZIK |
| 16. „Display Time” felirat | `oneuptext.tre:10-11` (`Text oneup/tpslabel`) | `SlideshowView.qml:1088` (`qsTr("Display Time")`) | EGYEZIK |
| 17. kijelzési idő értéke, egyes szám | `0x0080304c`-`0x0080305d`: `cmp esi, 1`. Egyes szám: `OneUpUI::second` (`0x00cb23d0`). Többes szám: `OneUpUI::seconds` (`0x00cb23e8`). Formátum: `OneUpUI::Format` (`0x00cb2404`), `%d %s` (`0x00cb23fc`). | `SlideshowView.qml:1126` (`show.seconds + " " + qsTr("seconds")`) | ELTÉR (angol felületen „1 seconds”; a magyar fordítás mindkét esetben „másodperc”) |

### #5653: a Timeline gomb és az átmenet-választó láthatósága

A `slideshowTimelineButton` akkor látszik, ha a `Preferences/BigSlideshow2`
értéke igaz (hiányzó kulcsnál 1), a képernyőmélység 16 vagy 32 bit, és a
vetítést nem az Időrend-bemutatóból indították. Minden más esetben a
`slideshowTransitionBox` látszik; a két elem láthatósága fordított. A
képernyőmélység a host `QScreen` értéke, a tesztek a QML tulajdonságot
helyettesíthetik.

Az eredeti `0x007fda00` a qshow belső Időrend-módját állítja be (a
`picasa-create-features.md` 2/b/2 pontja). A #5653 felületi szerződése szerint
a PicasaPy-gomb a meglévő Nézet ▸ Időrend belépést használja: bezárja a
diavetítést, majd a `Main.qml` `toggleTimeline()` függvényén keresztül a #5377
`TimelineView`-ját nyitja meg. Ez a PicasaPy belépési útja, nem állítás a két
belső mód bináris azonosságáról.

## 3. Eltérések és jegyjavaslatok

Minden javaslat három részből áll: **Eredeti**, **Nálunk**, **Teendő**.

### Jegyjavaslat 1: `prev` és `next` lenyomásra lépjen

| | lelet |
|---|---|
| **Eredeti** | A `oneup/prev` és `oneup/next` a `oneup.tre` szerint `mousedown` gomb (`oneup.tre:75-81`). A lenyomás ága `0x00a643f8`-`0x00a64425` elsüti a parancsot, a felengedés ága `0x00a64556`-`0x00a6455d` kihagyja. |
| **Nálunk** | A két gombon `onClicked` van (`SlideshowView.qml:997`, `1010`), a `PicasaButton` opt-in `lenyomasra` tulajdonsága (`PicasaButton.qml:136`) nincs bekapcsolva. |
| **Teendő** | `lenyomasra: true` a sáv ◀ és ▶▶ gombján (`SlideshowView.qml:994-997` és `1006-1010`), a `PicasaButton.qml:136` opt-in tulajdonságával. |

**Kész, ha:** egy lenyomás egy képet lép, és a felengedés nem lép másodszor. Ha a kézi próba eltérő, a jegy marad nyitva.

### Jegyjavaslat 2: a kijelzési idő felső határa

| | lelet |
|---|---|
| **Eredeti** | A `+1` és `-1` lépés után a kijelzési idő értéke `1` és `20` közé szorul (`0x00802b6d`, `0x00802b7e`-`0x00802b8f`, a konstans `0x00cf4974` = 20,0). |
| **Nálunk** | A felső határ `30` (`SlideshowView.qml:1138`, `controller.py:596`). A `controller.py:591-594` komment szerint ez a mi választásunk, és `NINCS KIMÉRVE`. |
| **Teendő** | A `controller.py` `SLIDESHOW_SECONDS_MAX` értéke `20`, és a `SlideshowView.qml:1138` `< 20`. A `screensaver_controller.py:49` (`_SECONDS_MAX = 30.0`) külön vizsgálandó: `NINCS MEG`, hogy a képernyővédő követi-e az eredeti határt. |

### Jegyjavaslat 3: egyes szám a kijelzési időnél

| | lelet |
|---|---|
| **Eredeti** | Ha az érték `1`, a felirat kulcsa `OneUpUI::second` (`0x0080304c`-`0x0080305d`). |
| **Nálunk** | `show.seconds + " " + qsTr("seconds")` (`SlideshowView.qml:1126`). Mindig többes szám. |
| **Teendő** | Egyes szám külön kulcs: `show.seconds === 1 ? qsTr("second") : qsTr("seconds")`. A magyar fordítás (`picasapy_hu.ts`, a „seconds” bejegyzés) egy alakot ad: „másodperc”. Így a magyar felületen nincs látható eltérés. Ha a kód változik, a `tests/app/test_i18n_dictionary_4313.py` őrt is le kell futtatni. |

### Jegyjavaslat 4: az idővonal gomb hiányzik

| | lelet |
|---|---|
| **Eredeti** | A `timeline` gomb a `centergroup` bal almás tagja (`oneup.tre:59-61`), felirata „Timeline” (`oneuptext.tre:4-5`). A `0x008037e0` a `timeline` és a `transtype` láthatóságát fordítva kapcsolja: ha az egyik látszik, a másik nem (`0x00803a03`-`0x00803a64`). |
| **Nálunk** | A sávon nincs idővonal gomb (`SlideshowView.qml` nem tartalmaz `timeline` elemet). |
| **Teendő** | A gomb csak a cél igazolása után vehető fel. A `0x007fda00` cél (`0x00802230`) és a `0x008037e0` jelző jelentése `NINCS MEG`. A magyar felirat a `picasapy_hu.ts` szerint `Időrend`. |

### Jegyjavaslat 5: az átmenet-választó láthatósága

| | lelet |
|---|---|
| **Eredeti** | A `transtype` és a `timeline` a `0x008037e0` szerint kölcsönösen kizáróak: a jelző igaz esetén az átmenet-választó látszik, hamis esetén az idővonal (`0x00803a03`-`0x00803a64`). A jelző a `0x00d33958` globális értéken, a `0x004019b0` visszatérésén és a paraméter második bájtján alapul (`0x0080381e`-`0x0080384e`). |
| **Nálunk** | Az átmenet-választó mindig látszik (`SlideshowView.qml:1026`). |
| **Teendő** | `NINCS MEG`, mit jelent a `0x00d33958` érték. Előbb azt kell kimérni, és csak utána lehet kódjavaslatot tenni. |

### Jegyjavaslat 6: a feliratgomb állapotai

| | lelet |
|---|---|
| **Eredeti** | A feliratgomb két állapotot ad: a kattintáskezelő a `captionbutton` `[+0x359]` bájtja alapján mutatja vagy rejti a feliratot (`oneup/caption`, `0x00803381`-`0x008033b7`). A diavetítő kattintáskezelőjében harmadik állapot nincs. A kattintás általi váltás íróját nem azonosítottam (lásd a 4. szakaszt). |
| **Nálunk** | Három állapot: felirat, fájlnév, semmi (`SlideshowView.qml:120`, ciklus 1051-1055). |
| **Teendő** | Döntés a jegyben: két állapot (a `caption_icon` és `caption_yesicon` ikonpárral), vagy a harmadik állapot forrásának megkeresése. A forrás `NINCS MEG`. A `captionmode` beállítást a `0x005749e0` írja (`[this+0xdd8]` értékkel). A `0x005643e0` a beállítás-betöltő, ahol a `captionmode` név szerepel. Az értékkészlet nincs kimérve. |

### Jegyjavaslat 7: a csoportok és a sorrend

| | lelet |
|---|---|
| **Eredeti** | Három csoport van: bal (`exit`, `transtype`), közép (`centergroup`), jobb (`rotateleft`, `rotateright`, `star`, `captionbutton`). A csoportokon belüli sorrend `NINCS MEG`. |
| **Nálunk** | Egyetlen lista, a kijelzési idő a jobb szélen (`SlideshowView.qml:981-1139`). |
| **Teendő** | A sáv átrendezése a csoportok szerint. A csoporton belüli sorrendet az eredeti Picasa képernyőképéről kell kimérni. A kódhoz csak ez után nyúljon a jegy. |

## 4. Nyitott pontok

- **A csoporton belüli sorrend.** A `.tre` és a `0x00802c60` konstruktor továbbra sem adja meg a sorrendet; a képernyőn mért eredményt a fenti #7197 felvétel rögzíti.
- **Az `exit` cél.** A `0x00803527` ág vtábla `+0x24` objektuma és a vtábla `+0x14` metódusa nincs azonosítva. A `show.stop()` egyezése ezért nincs igazolva.
- **Az `auto2` kattintási cél.** A `.tre` nem ad találat-jelzőt. Hogy az eredetiben a kép kattintása is léptet-e, nincs igazolva.
- **Az esemény útja a gombtól a diszpécserig.** A parancs-kibocsátó `0x00a64a10` a gomb vtábla `+0x70` elemét hívja (`0x00ce48e4`), ennek célja `0x009e3b00`. A `0x009e3b00` végig nincs követve. A `0x8000004` típus közvetlen tárolása a `.text`-ben egyetlen helyen van: `0x00a64b02`. Regiszteren át történő írást nem zártam ki.
- **A feliratgomb állapotának írója.** A `[+0x359]` bájtot a kép több helyen írja és olvassa, ezért a kattintás általi váltás íróját nem azonosítottam. A `0x00a65187`-`0x00a651ae` ág akkor fordítja meg a bájtot, ha a `[+0x35a]` bájt nem nulla, a `[+0x213]` nulla, és a `[+0x244]` nem nulla. A `[+0x35a]` bájtot a `.tre` `buttcon` tulajdonsága írja (`0x009cbf90` hívja a `0x009c7900`-at). A `captionbutton`-on nincs `buttcon` (`oneup.tre:121-124`). A kezdőállapot írója is `NINCS MEG`.
- **A `transtype` lista és választás útja.** A mai `SlideshowView.qml:1030` „22 soros” állítása nincs igazolva.

A kódhoz nem nyúltam. A jegyjavaslatokat a hívó dönti el.

## 5. #7284: a vetítésben megjelenő zoomikon és csúszka

Az Exit után látható képikon és csúszka a normál `editoneup` vetítési út
`editpanel` zoomvezérlője. Nem a `0x00802c60` által betöltött `oneup` sáv
`plusone`/`minusone` párja: azok a vetítési időt léptetik
(`oneup.tre:133-143`, `0x008032e0:0x008033e3-0x00803447`).

| Elem vagy művelet | Azonosítás és bizonyíték |
|---|---|
| Nagyítónak látszó ikon | `editpanel/zoomup_icon`, `editpanel.tre:1288-1289`. |
| Csúszkasín és fogantyú | `zoomslider/scaleslider` és `zoomslider/thumb`, `editpanel.tre:1291-1296`; a sín `Property slider 3` tulajdonságú. |
| Vetítési sávhoz illesztő klip | `editoneup/sszoomsliderclip`, `editoneup.tre:68-69`. A `0x0075de50` vetítési belépési ágában ezt és az `editpanel/zoomsliderrect` csomópontot adja át a `0x0075ddf0`-nek (`2026-11-19-koteg-496-517.txt:2464-2474`). A másik állapotág az `editpanel/zoomsliderclip` és `editpanel/zoomsliderrect` csomópontot adja át (`:2733-2747`). |
| Húzás eseményútja | A `0x005de8e0` a `zoomslider/scaleslider` eseményt a `0x005d2020`-hoz irányítja (`2026-10-21-koteg-1021b.txt:3090-3190`). Ez a kapott lebegőpontos értéket a `0x005d1470`-nek adja (`0x005d2081-0x005d208d`), amely a zoomvezérlő `+0xe50` mezőjét írja (`0x005d14b8-0x005d14c3`). |
| Mit állít | A `0x005d1470` ezután a `0x005d1520` képelem-frissítő útját hívja. A lánc a két képelem `+0x3a0` skáláját frissítő `0x005c5ed0`-hez jut. A húzás a fotó nagyítását állítja, nem a vetítési időt vagy a képlépést. A szerkesztői zoomlánc további leírását lásd a **„A szerkesztő nagyítás-hármasa”** szakaszban. |
| A `0x0075ddf0` helper | A 93 bájtos függvény feloldja a kapott két csomópontnevet; ha mindkét csomópont létezik, a `0x009df550`-et hívja a két csomóponttal és `1` paraméterrel. Ebben a függvénytörzsben nincs közvetlen `m_hidden` írás vagy név szerinti show/hide hívás. |

**A `0x008032e0` nem kezeli a húzást.** A teljes név szerinti áglistában nincs
slider-ág; a `plusone` és `minusone` a `0x00802ff0` időállító függvényt hívja.
Ezt a Ghidra-kimenet és a teljes 1274 bájtos helyi diszasszemblálás is
alátámasztja. A csúszka külön `0x005de8e0` → `0x005d2020` eseményúton működik.

### 5.1 A zoomklip párba állítása nem láthatósági kapcsoló (2026-11-20)

A 2026-11-20-i Ghidra-kimenet a `0x0075ddf0` segédet pontosítja
(`~/picasapy-agent/referencia/ghidra/2026-11-20-koteg-567-573.txt:1-35`).
Két erőforrásnevet old fel a `0x009c2fc0`-n keresztül; ha mindkét elem
létezik, `0x009df550(elem1, elem2, 1)` hívást végez. A segéd nem ír
láthatósági jelzőt, és nem állít zoomértéket.

A `0x0075de50` hívóágában a `[panel+0x332f] == 0` feltétel vezet a
`0x0075e4bd` címre; ott a `0x0075e508` hívás az
`editoneup/sszoomsliderclip` és `editpanel/zoomsliderrect` nevekkel éri el a
segédet. A nem nulla ág az `editpanel/zoomsliderclip` és
`editpanel/zoomsliderrect` párt adja át (`0x0075e0b9`-`0x0075e0ee`). A
Ghidra-dekompiláció és a függvényhatárra korlátozott, 3183 bájtos helyi
diszasszemblálás ugyanazt az ágat és névpárt mutatja; ezek ugyanazon bináris
út két olvasatai, ezért önmagukban nem számítanak két független bizonyítékútnak.

**Az elemek argumentumsorrendje.** A hívó a klip nevét, majd a téglalap nevét
adja át. A `0x0075ddf0` az `EAX`-ban kapott második nevet (`zoomsliderrect`)
oldja fel először, a veremargumentumban kapott első nevet (`sszoomsliderclip`)
másodszor; ezeket ebben a sorrendben adja a `0x009df550`-nek
(`0x0075ddf0:0x0075ddf0`-`0x0075de41`). Így a `0x009df550` első objektuma az
`editpanel/zoomsliderrect`, a második az `editoneup/sszoomsliderclip`.

A `0x009df550` 291 bájtos helyi diszasszemblálása a téglalap geometriájához
kapcsolódó ágat mutat: olvassa az első (`zoomsliderrect`) elem `[+0x213]` és
`[+0x244]` mezőjét, virtuális `+4` és `+8` metódust, valamint
`0x009dea70`, `0x009df680`, `0x009df290`, `0x009de880` és `0x009e6120`
segédeket hív. A belső mező- és visszatérési kapuk sikeres ágán, a harmadik
`1` argumentum mellett az első elem `[+8]` jelzőjét módosítja és a
`[+0x14c]`, `[+0x150]` mezőjét írja. E mezők pontos, név szerinti szerepe
`NINCS MEG`; a közvetett virtuális hívások teljes hatása sem ismert. Ez
bizonyítja, hogy a helper a `zoomsliderrect` geometriai feldolgozását a
`sszoomsliderclip` elemhez viszonyítva kéri, de nem mondja meg, mikor
rajzolódik ki a csúszka.

**Friss Colab-mérések.** A feladatban közölt eredmény szerint a job-775-778
kézi szünetet mér az
1., 11. és 22. dián, valamint a lista végén; a zoomsáv egyik képen sem
látszik. A job-785/786 jobb kattintást mér szünet után; a sáv ott sem jelenik
meg. **Cáfoló kísérlet:** az ellenőrizendő állítás az volt, hogy a kézi
listavégi szünet önmagában elég a vezérlő előhozásához. A 775-778-as eredmény
magában foglal listavégi kézi szünetet, de azon sem látszik a sáv; a 785/786
jobb kattintása után sincs látható sáv. Ez a mért próbákban cáfolja e két
esemény önálló elégségességét. **A cáfolat határa:** a megadott eredmények nem
adnak párosított kurzorpozíciót és automatikus listavégi megállást, ezért nem
zárják ki, hogy egérmozgás vagy más, nem vizsgált feltétel mellett megjelenjen.
A job-789 folyamatos egérmozgást vizsgál
szünet után, de a végrehajtói JSON helyi kiolvasása hálózati hibával leállt,
és a helyi `meroadat.tar` nem tartalmazza ezt a feladatot vagy a `video__08.mp4`
tagot. A 789 eredménye ezért `NINCS MEG`.

A korábbi `video__08.mp4` képkockaolvasatban az Exit utáni hely az első
szünetnél üres, a feladatot kiváltó felvétel lista végi szünetében pedig a
képikon és a csúszka látszott (`t=100 s`). A különböző felvételek és
szüneteltetési okok nem párosítottak, ezért ez nem állapít meg láthatósági
feltételt. A `0x0075de50` `[+0x332f] == 0` ága csak a klip/rect elem-pár
beállításának feltétele; ezt nem szabad a megjelenés feltételeként átvenni.

**Láthatóság: NYITOTT.** A binárisban azonosított clip-pár és a mostani
Colab-próbák nem mondják meg, milyen mutató-, időzítési vagy vetítési állapot
teszi ténylegesen láthatóvá a zoomvezérlőt. A konkrét következő bizonyíték a
job-789 végrehajtói eredményének visszakereshető JSON-ja; ha abban nincs
képkockával igazolt láthatósági eredmény, azonos futásban kell összevetni a
mozdulatlan kurzort a szünet után folyamatosan mozgatott kurzorral, első,
középső és utolsó dián. Addig a „csak a lista végén látszik” állítás
`NINCS MEG`.

**A húzás hatása.** A `zoomslider/scaleslider` eseményút a `0x005d2020`-on
átadja a lebegőpontos csúszkaértéket a `0x005d1470`-nek; ez a néző
`[+0xe50]` értékét írja (`0x005d14b8`-`0x005d14c3`), majd hívja a
`0x005d1520`-t. Az út a `0x005c5ed0`-hoz vezet, ahol a képelem `[+0x3a0]`
skálamezője frissül. A bináris tehát a fotó nagyítását/skáláját állítja, nem
a diaindexet vagy a vetítési időt. A `0x008032e0` `plusone`/`minusone` ágai
ettől külön a `0x00802ff0` vetítési-idő útját használják.

> **Bizonyítottsági fok:** a zoomvezérlő erőforrás-eredete és képskála-hatása
> statikus bizonyítékkal alátámasztott; a láthatósági feltétel nyitott, ezért
> a teljes #7284 kérdés **nyitott**. A 775-778 és 785/786 mérések negatívak a
> megnevezett kézi eseményekre; a 789 eredményét nem sikerült ellenőrizni.

**Következtetés.** A sávon látható nagyító nem a `oneup` saját időállító
vezérlője: az `editpanel` zoomcsúszkáját az `editoneup/sszoomsliderclip`
klip kapcsolja a vetítő nézetéhez. A csúszka húzása a kép skáláját állítja.
Az elempár beállításának módjelzője nem láthatósági szabály; a jelenlegi
Colab-adatok sem azonosították, mi hozza elő a vezérlőt, ezért a #7284 teljes
lezárása a 789-es eredmény vagy egy kontrollált mozgáspróba előtt nem
indokolt.

### PicasaPy fejlesztői következmény

| | |
|---|---|
| **Eredeti** | `editpanel/zoomup_icon` (`editpanel.tre:1288-1289`), `zoomslider/scaleslider` és `zoomslider/thumb` (`editpanel.tre:1291-1296`); a vetítési út az `editoneup/sszoomsliderclip`-et használja (`editoneup.tre:68-69`, a `0x0075de50` vetítési belépési ágában). Húzásra a kép skálája változik. |
| **Nálunk** | A #7322 óta megvan: a lista végén megállt vetítésnél a sávon képikon és nagyítócsúszka áll, lásd a következő szakaszt. |
| **Teendő** | Nincs; a megvalósítás a #7322-ben készült el. |
| **Kész, ha** | A csúszka húzása az aktuális kép skáláját változtatja, a diaindexet nem; a láthatóság megfelel azonos szünet-, dia-, egér- és képméretfeltételek mellett rögzített eredeti viselkedésnek. |

### #7322: a PicasaPy megvalósítása

A `SlideshowControls.qml` a Kilépés utáni mért helyen (157 képpont: a 24
képpontos ikon, 6 képpont rés és a 127 képpontos csúszka) a lista végén
megállt vetítésnél képikont és csúszkát mutat. A `SlideshowView.listaVegen`
akkor igaz, ha a vetítő látszik és nincs következő kép (ismétlés nélkül az
utolsó dián). Az első és a középső dián szüneteltetve a hely üres marad
(`kepernyo__13`-`15`, job-796 `kepernyo__14`-`17`), a lista végén megjelenik
(`kepernyo__32`-`37`). Ismétléssel nincs lista vége, tehát a csúszka sem látszik.

| Tétel | Megvalósítás | Forrás vagy fok |
|---|---|---|
| Ikon és csúszka grafikája | A szerkesztő nagyítósávjának meglévő elemei: `EditorSlider` `scaleslider` családja és a `loupe.svg` (`TrayTopRow.qml`, `viewerZoomUpIcon`, `zoomSlider`). A `loupe.svg` vonala sötét, ezért a sötét vetítősávon világos lap van alatta. | A grafika a projekt saját rajza; az eredeti erőforrás pixelképével nincs összevetve |
| Csúszka értéke | [0, 1], a húzás a `SlideshowView.imageZoomValue` értékét írja. A diaindexet nem. | `0x005de8e0` → `0x005d2020` → `0x005d1470` (5. szakasz) |
| Érték és nagyítás | A néző mért leképezése: 0 = illesztés, 0,5 = valódi méret, 1 = 400 % (`skalaErtekbol`, #2492). | Következtetés: a vetítés ugyanazt a zoomláncot használja. A leképezés vetítésbeli használata nincs külön mérve |
| Nagyítás hatóköre | A `SlideshowCurrentImage.qml` külön `Scale` réteget kap, az átmenetek `scale` tulajdonságától függetlenül. A lista végének elhagyása (léptetés, kilépés) nullázza az értéket. | PicasaPy-döntés: a nagyítás az aktuális képé |
| Következő nyíl | A lista végén tiltott (szürke). A billentyűs Jobb továbbra is az első képre fordít (#7190). | `kepernyo__32`-`37` (a nyíl szürke) |

Nyitott marad: a csúszkával nagyított kép nem húzható (nincs pásztázás), mert az
eredeti pásztázásról nincs adat. A lista végén álló vetítés `playing` állapota
a PicasaPyban igaz marad (az időzítő üresen jár), az eredeti ilyenkor megállt;
a láthatóság ezért a `playing` állapotától függetlenül a lista végéhez kötött.
