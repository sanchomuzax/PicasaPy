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
`NINCS MEG`. A `.tre` deklarációs sorrendje (`oneup.tre:40-143`) nem vizuális
sorrend, ezt bizonyítékként nem használom.

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

- **A csoporton belüli sorrend.** A `0x00802c60` konstruktor beállítja a vtáblákat, és a `0x009c68a0` hívással tölti be az erőforrást. A gyermekek elhelyezése nincs végigkövetve. Ehhez a betöltő (`0x009c68a0`) és az elrendezés követése kell, vagy mért képernyőkép.
- **Az `exit` cél.** A `0x00803527` ág vtábla `+0x24` objektuma és a vtábla `+0x14` metódusa nincs azonosítva. A `show.stop()` egyezése ezért nincs igazolva.
- **Az `auto2` kattintási cél.** A `.tre` nem ad találat-jelzőt. Hogy az eredetiben a kép kattintása is léptet-e, nincs igazolva.
- **Az esemény útja a gombtól a diszpécserig.** A parancs-kibocsátó `0x00a64a10` a gomb vtábla `+0x70` elemét hívja (`0x00ce48e4`), ennek célja `0x009e3b00`. A `0x009e3b00` végig nincs követve. A `0x8000004` típus közvetlen tárolása a `.text`-ben egyetlen helyen van: `0x00a64b02`. Regiszteren át történő írást nem zártam ki.
- **A feliratgomb állapotának írója.** A `[+0x359]` bájtot a kép több helyen írja és olvassa, ezért a kattintás általi váltás íróját nem azonosítottam. A `0x00a65187`-`0x00a651ae` ág akkor fordítja meg a bájtot, ha a `[+0x35a]` bájt nem nulla, a `[+0x213]` nulla, és a `[+0x244]` nem nulla. A `[+0x35a]` bájtot a `.tre` `buttcon` tulajdonsága írja (`0x009cbf90` hívja a `0x009c7900`-at). A `captionbutton`-on nincs `buttcon` (`oneup.tre:121-124`). A kezdőállapot írója is `NINCS MEG`.
- **A `transtype` lista és választás útja.** A mai `SlideshowView.qml:1030` „22 soros” állítása nincs igazolva.

A kódhoz nem nyúltam. A jegyjavaslatokat a hívó dönti el.
