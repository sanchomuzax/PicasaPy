# A specifikációk tartalomjegyzéke

**Ez a lap a belépési pont a `docs/specs/`-be.** Alább előbb a **valóban
nyitott kérdések** listája (ebből válasszon témát egy kutatói kör), majd a
spec-lapok témakörönként.

*(A lapok DARABSZÁMA szándékosan nincs kiírva: kézzel karbantartott
leltár-szám némán elavul — ezt a hibaosztályt a #1512 őre tiltja.
A 2026-09-02-i állapotban a kiírt „34" már 71 fájl mellett állt.)*

**A lenti „Nyitott kérdések" lista kézzel ellenőrzött**, nem gépi
szó-számlálás. Egy 2026-08-16-i átvilágítás kimutatta, hogy a
`Nyitva`/`dekódolatlan` szavak **kétharmada hivatkozás** egy máshol már
megválaszolt pontra — a gépi számlálás tehát háromszorosára fújta a
képet (pl. `filterdesc-registry.md`: 6 találat, **0** valódi nyitott
kérdés).

*Utolsó átvilágítás: 2026-08-16 (a második, tízkörös menet után).*

## 🔶 Nyitott kérdések — innen válassz kutatói kört

### [ui-audit-editor.md](ui-audit-editor.md) — ✅ nincs nyitott kérdés (a #2061 2026-09-04-én LEZÁRULT; a fejléc 2026-09-05-ig elavult volt)

⭐ **2026-09-04 — a `plugins/red.cfg` LELTÁRA a `picasa-arcfelismeres.md`-ben (#2239, TULAJDONOSI DÖNTÉS alapján tájékoztató, nem normatív).** A tulajdonos 2026-09-04-én úgy döntött: *a korábbi működés kerüljön a dokumentációba, és a majdani saját eljárás specifikációjánál legyen irányadó, de **most ne épüljön be***. ⭐ **A fájl:** a `Red.dll` arc- ÉS vörösszem-motorjának betanított konfigurációja (2,2 MB) — **19 525 objektum, 75 osztály**. A szerializálás hatbájtos fejléce (`00 <len> <ClassId> 00`) és négy tároló-osztály payloadja megfejtve; a `ClassId→osztálynév` tábla a DLL regisztrációs sorozatából (550 osztály). ⭐ **Osztálycsaládok:** `ebs_` 12 215 (tárolók) · `ets_` 4 827 (mátrix/vektor) · `vlf_` 921 (lokális jellemzők) · `vqc_` 729 (kvantálás) · `egp_` 561 (térbeli gráf) · `vfv_` 242 · `vde_` 12 · `vfr_` 7 (legfelső szint) · **`vrd_` 6 (VÖRÖSSZEM — ugyanez a fájl a vörösszem-detektort és -korrektort is tartalmazza)** · `vpf_` 5. ⭐ **A lánc sorrendje** a `vfr_VdeFaceFinder`-től a `vfr_SowGrowStampClusterer`-ig, offszetekkel. ⭐ **Az egyetlen kiolvasott paraméter-ötös:** a klaszterező `0,7 / 0,98 / 1,0 / 25 000 000 / 25 000 000` (a mezők NEVE nincs megfejtve). ⛔ **Nem megfejtett:** a 75 osztályból 71 payload-sémája és a paraméterek jelentése. ⚠️ **A fájl a PARAMÉTEREKET adja, az ELJÁRÁST nem** — ez a fő oka annak, hogy az átvétele nem javasolt. A parser a privát repóban marad. Jegy: **#2239** (lezárva).

⭐ **2026-09-04 — a két FELTÖLTŐ gomb kapcsolási feltétele kimérve (#1935, `ui-audit-editor.md`).** A `quickupload` és az `uploadchanges` ugyanabban a `0x00567a00`-ban dől el, mint a `weblink` és a két projekt-gomb. ⭐ **A két segédfüggvény kiolvasva:** `0x009cd730` = rejtés (`vtbl+0x68`), `0x009cd760` = mutatás (`vtbl+0x6c`). ⭐ **Külső kapu:** `0x00567d46` `test byte [esp+0x2c], 4` — a `0x00563cb0` állapotkódja; a függvény **pontosan három** kódot ír: **8** (`[obj+0x3094]>0` vagy `[obj+0x30a0]>0` vagy a `Preferences\LastUserESState`-et olvasó `0x00431290`) ⇒ **egyik gomb sem**; **6** (aktív szerkesztő-eszköz: `edittextoverlay`/`cropselection`/`redselection`/`peoplepanel/manual_frame`, vagy `previewclip2`) és **5** (normál eset) ⇒ átmegy. ⭐ **A kapun belül a két gomb KIZÁRJA egymást:** ha a képhez tartozó `[o+0x38]` sztring nem üres, az `uploadchanges` látszik, különben a `quickupload` — mindig legfeljebb egy. ⭐ **Ráadás:** a `weblink` gomb csak **1-nél hosszabb** sztringnél jelenik meg (`0x00567d1e`). ⛔ **Nem azonosított:** az `[o+0x38]` mező jelentése és az 5/6/8 kódok neve — a gomb-logika ezek nélkül is teljes. ⛔ **Nálunk (mérve):** a „Gyors feltöltés" a helyi menüben **`retired: true`** (megszűnt szolgáltatás, #422), a fejléc-gombok pedig nincsenek meg — és a mérés szerint ez **helyes**: élő feltöltési munkamenet nélkül az eredeti sem mutatja őket. Jegy: **#1935**.

⭐ **2026-09-04 — a BETŰMÉRET leképezése ZÁRT: `tárolt = listaérték ÷ 360` (#2287, `picasa-ini-format.md`).** ⭐ **A méretlista statikus, 16 egész** (`.data`, két azonos példány: `0x00c7dab8` és `0x00c7e4f0`): **8, 10, 12, 14, 16, 18, 20, 22, 26, 30, 36, 48, 60, 72, 84, 96**; a legördülő `"%d"`-vel írja ki (`0xc81844`) ⇒ **nincs százalék**, egészek vannak. Az alapérték **12** (`0x0062d463`). ⭐ **Az átváltó a `0x005b35a0`:** `méret_képpont = választott × (kép_magassága ÷ 360)` — a 360,0 a `0xcf3d50`-ből kiolvasva, ugyanaz a konstans, mint az író másik ágában. Az eredmény a szöveg-objektum `+0x50` tagja, amit a `text=` írója a `[vtbl+0x98]` getterrel (`0x005ba960`) olvas. ⭐ **A kör bezárul:** az író `méret ÷ magasság`-ot tárol, tehát a **magasság kiesik** ⇒ `tárolt = listaérték ÷ 360`. ⭐ **Ellenőrzés hat valódi export-blokkon: 3/3** — a `0,033333`, `0,061111` és `0,072222` pontosan **12**, **22** és **26**, mind a listában; a másik három nem egész (kézzel átméretezve). ⇒ **A „hány képpont a 100%" kérdés tárgytalan**: az eredetiben abszolút lista van, és a kép magassága 360 egységnek számít. ⛔ **Nálunk (mérve):** `EditorTextPanel.qml:106` **20–400 százalék**, `stepSize: 10`; a rajzoló a `geometry.size`-ot nem olvassa, hanem a `_SCALE_TO_PIXELS = 30` állandót használja (`render/text_overlay.py:47`). Jegy: **#2287**.

⭐ **2026-09-04 — a `text=` stílusblokk MÉRTÉKEGYSÉG-LEKÉPEZÉSE (#2271, `picasa-ini-format.md`).** ⭐ **A tagtérkép TELJES:** az előző kör a beolvasóból négy mezőt kötött taghoz, az **író** (`0x00a4e3b0`) getterei a maradék ötöt is megadják — 1. `+0x20`, 2. `+0x38`, **5. `+0x3c` (float)**, **6. `+0x34` (float)**, 7. `+0x1c`, 8. három bájt (`+0x14`, `+0x2c`, `+0x28`), 9. `+0x18`. ⭐ **A két csúszka útja: NINCS átszámítás.** A `0x0062f3c0` kezelő az átlátszatlanság-csúszka nyers értékét teszi a `+0x34`-be, **alulról 0,1-re vágva** (`0x0062f460`, a konstans `0xcf4888`/`0xc7e4a0` = **0.1**) ⇒ nulla átlátszatlanság nem áll elő; a körvonalvastagságot ugyanígy a `+0x3c`-be, **de a pontos 0,0 nem tárolódik**: a program a „nincs körvonal" ágra ugrik (`0x0062f555` → `0x0062f581`), ami a 8. mező alsó bájtját állítja. ⭐ **A méret képlete:** ha a 9. mező `0x8000` bitje áll (minden mintában áll), a tárolt érték = **em-képpont ÷ a kép MAGASSÁGA** (`0x00a4e5aa`); ha nem áll, `× 360,0` is (`0xcf3d50`, kiolvasva). A korábbi képpont-mérés ezt függetlenül igazolja (82,13 és 140,62 a mért 82/141 mellett). ⭐ **A csúszka TARTOMÁNYA is megvan: `[0, 1]`** — a `ytSliderHandler` (RTTI `0x00cda46c`) érték-beállítója (`vtbl+0x10` → `0x00aaf220`) a kattintás helyét a **sáv hosszával** osztja (`0x00aaf252`), majd **0,0-ra és 1,0-ra vágja** (`0x00aaf259`–`0x00aaf282`); a görgő egy kattanása a tartomány **2 %-a** (`0xcf48a8` = 0.02, a delta ÷ 15,0). ⇒ a mintákban látott 0,25 és 0,5 a csúszka negyed, illetve fél állása, és **nálunk a 0–8-as, egész lépésű körvonal-csúszka MÉRTÉKEGYSÉGE az eltérés**, nem a leképezés. ⛔ **Szűkült, nem oldódott meg:** a 0,757813 tárolt vs. 0,53 mért átlátszatlanság eltérése **nem az írásban van** (az azonosság), hanem a RAJZOLÓBAN. Jegy: **#2271** (kommentelve, `ready` vissza).

⭐ **2026-09-04 — az effekt-csempe előnézete a szerkesztési lánc TETEJÉN áll (#2061, LEZÁRVA; `ui-audit-editor.md`).** A tulajdonos hat képernyőképe (`research/#2061-effekt-latszik/`, a `.gitignore` miatt nem a repóban) **három független ELŐTTE/UTÁNA párt** ad, három KÜLÖNBÖZŐ effekt-fülön; a kapcsoló mindháromnál a Fekete-fehér, és az állapotot a felület maga kiírja (`Újra: Fekete-fehér` vs. `Visszavonás: Fekete-fehér`). Alkalmazott B&W mellett **minden csempe alapja szürke**. ⭐ **Kontroll:** a saját színt előállító csempék (`Hőtérkép`, `Kéttónusú`, `Neon`, `Ceruzarajz`) mindkét állapotban azonosak — pont ez várható. ⛔ **MEGDŐLT** az előző kör feltételes olvasata („a leíró két hard nullája az ALAP kép mellett szól"): a `[X+8]`/`[X+0xc]` pár az ÉLŐ szerkesztési állapot, nem az eredeti kép. ⭐ **A csempesor újraépítése kimerítően:** a `0x005d7c20`-nak **két** `call rel32` hívója van (`0x005d7a85` = a fül-tartalomépítő `0x005d78d0` / `editpanel/fxthumbs`; `0x005e6771` = a billentyűkezelő SHIFT-újraellenőrzése), a fül-tartalomépítőnek **három** — és **közvetett hívás kizárva**: mindkét cím nyers négybájtos alakja **nulla** alkalommal fordul elő bármelyik szekcióban ⇒ csúszka-húzás közben NINCS újraépítés. ⭐ **Nálunk (mérve):** az `app/effect_thumbnails.py` az ALAP képen renderel (kimondott egyszerűsítés, #338) — tehát ez **mért eltérés**. A csere ára lemérve ezen a gépen: a **40** effekt (a modul kommentje még 36-ot ír) teljes újraszámolása egy 200 px-es forrásból **medián 54,5 ms**; a szálszám alig számít (1/2/4 szál: 56,7 / 53,3 / 59,0 ms), és a lánc alkalmazása a 200 px-es forrásra **0,51 ms**. Jegyek: **#2061** (lezárva), **#2273** (a megvalósítás).

⭐ **2026-09-04 — NÉGY kék jelvény van, nem három: a `Színinvertálás` a 2.
effekt-fülön is jelvényes (#2125, `filterdesc-registry.md`).** Ugyanazokból a
felvételekből, fülenkénti bontásban: 1. fül **Szépia / Fekete-fehér /
Melegítés**, 2. fül **Színinvertálás**, 3. fül **egy sem**. Az `Invert`
`mode="effect"`, tehát a `mode`-ból levezetett lánc szerint nem lehetne
jelvénye — és a jelvény **két különböző felvételen**, eltérő szerkesztési
állapot mellett is látszik. ⛔ **MEGDŐLT** a korábbi „három jelvény, mind az
1. fülön — a kódban nincs út a negyedikhez" állítás. ⛔ **A „ki írja még a `FilterDesc + 4`-et" kérdés 2026-09-04-én MEGDŐLT: SENKI** — nyolc független ellenőrzés (a `FilterDesc` ctor **egyetlen** hívója; a jelvény-jelző **egyetlen** írása; a getter **egyetlen** vtáblája; mind a **2856** RTTI-vtábla `+0x14` slotja; a 36 csempe `mode`-ja az XML-ből; a `.tre` egyetlen jelvény-rétege). A jelvény képpont-szinten **ugyanaz az elem**, a csempe pedig igazoltan az `Invert` (`filter_Invert_label0` = „Színinvertálás"). ⇒ **a kérdés nem a binárisban van:** a futó telepítés `runtime\filterdesc.xml`-je eltérhet a kutatási másolatunkétól. Jegy: **#2125** (`blocked` + `felhasználóra-vár`, egyetlen gépies kéréssel).

### [picasa-menusor-csoportok.md](picasa-menusor-csoportok.md) — nincs nyitott kérdés

⭐ **2026-09-03 — a Szerkesztés menü TELJES szerkezete kimérve, és a visszavonás-kérdés LEZÁRVA (#1795).** A menüt ugyanaz a táblavezérelt függvény építi (`0x00559150`), mint az Eszközökét: a tábla `0x00d6db80`-on áll, **20 bájtos rekordokkal**, a **darabszám-konstans 14** (`push 0xe`, `0x00559c76`; gyerekmutató `push 0xd6db80`, `0x00559c7c`) = **11 tétel + 3 elválasztó**, tehát a csoportosztás **3 | 2 | 2 | 4**. A lap tartalmazza mind a 14 rekordot címmel, kulccsal, angol ÉS magyar felirattal, gyorsbillentyűvel és parancsazonosítóval (`0x9d39` Kivágás … `0x9c90` Kijelölés törlése). ⛔ **A #1774 „feltételes visszavonás"-hipotézise MEGDŐLT, két független mérésből:** (1) a feltöltő blokkban (`0x005598b2`–`0x00559c4c`) **pontosan 11** feltételes ugrás van, mind a felirat-feloldás `NULL`-ellenőrzése — állapotfüggő elágazás nincs; (2) az `eMenuEdit::ID_UNDO`/`ID_REDO` **literál a teljes `Picasa3.exe`-ben 0 alkalommal** fordul elő (ASCII és UTF-16LE), tehát halott erőforrás-bejegyzés. **Hol VAN visszavonás:** a szerkesztő panel gombján (`CFilterStackUI::undolabel`), a **Kép** menü `Undo All Edits` tételén, a szövegmező helyi menüjében (`Address::ID_UNDO`, a menüt a `0x007331e0` építi) és a mentés-visszavonó párbeszédben. **Melléklelet:** a lap „nem dönti el" listájáról a **mnemonikok** is lekerültek — a szövegtár 142 honosított mnemonikot ad, nálunk 144 menütételből 11-en van; jegy: **#2152**. Jegyek: **#1795** (lezárva), **#2151** (a hamis indoklás javítása), **#2152**.

⭐ **2026-09-03 — az Eszközök menü TELJES szerkezete kimérve (#1794).** A menüt **egyetlen** függvény építi (`0x00559150`, 15 495 b), és nem `AppendMenuW`-vel: az egész függvényben **két** Win32-hívás van, a menü egy `.data`-beli rekord-tábla (`0x00d6e678`…`0x00d6e9a8`). Az `eMenuTools::` névtér mind a **36** kulcsa itt szerepel. **A Kísérleti almenü darabszáma konstans `9`** (`0x0055c928`), a gyerek-mutatója `0x00d6e798` (`0x0055c91e`); a kilenc tétel a `0x0055c295`…`0x0055c4c9` blokkban épül: FTP-közzététel · **Fájlok másodpéldányainak megjelenítése** (`ID_DUPES`, a 2. helyen) · Keresés… ▸ (maga is almenü, **hat színnel**: Piros/Narancssárga/Sárga/Zöld/Kék/Lila, `0x0055c078`…`0x0055c1c8`) · Keresési eredmények mentése · Címke megjelenítése albumként · Útlevélkép · Üres online albumok törlése · **Adatbázis helyének kiválasztása** · Arcinformációk írása XMP-adatokba. A Feltöltés almenü 3, a Geocímke 4 tételes. ⛔ **A „Find Faces" felirat a TELJES szövegtárban nem létezik** — az arckeresés az eredetiben **nem menüparancs**, a miénk tudatos eltérés. A felső szint fedi a tulajdonos képernyőmentését, egy feltételesnek tűnő tétellel több (`ID_TOOLS_DOWNLOAD_FACES`). Megvalósítás (a duplikátum-kereső áthelyezése, a feliratok, az eltérés kimondása): **#2142**. Jegyek: **#1794** (lezárva), **#2142**.

### [picasa-lebego-ertesito.md](picasa-lebego-ertesito.md) — nincs nyitott kérdés

⭐ **2026-09-03 — a két animált sáv JELENTÉSE megvan, és a #2034 egyik következtetése MEGDŐLT (#2122).** A rajzoló **nem** a gyorsítótárazott `cella+0x88`/`+0xa0` értéket olvassa — **újra kiértékeli** a sávokat (`0x00658423`, `0x0065903b`, `0x006590b4` → `0x00655950` → az általános kulcskocka-kiértékelő `0x009e5e70`, a sávot `edi`-ben kapva). A skálázás adja meg a mértékegységet: `fild [popup+0x1c0]` × **B sáv** (`0x00659040`–`0x00659061`) és `fild [popup+0x1bc]` × **A sáv** (`0x00659069`–`0x0065908a`). A `popup+0x1b4` a **`notifier/cell1`** réteg rekesze, a rétegstruktúra `+8` mezője **szélesség**, a `+0xc` **magasság** (a fogantyú rajzolása bizonyítja, `0x0065879b`) ⇒ **`+0x1bc` = 247 px, `+0x1c0` = 45 px, `+0x1e4` = a `basedecrect` 21 px-e**. Független megerősítés: a kattintáskezelő a cella sorszámát `(egérY − 2) / [popup+0x1c0]` alakban számolja (`0x00657eb4`). ⇒ **az A sáv vízszintes eltolás cellaszélesség-egységben (a `−1,0` = −247 px), a B sáv függőleges eltolás cellamagasság-egységben (a cél a verembeli sorszám = sorszám × 45 px)** — tehát a becsúszás VALÓDI, és a cellák egymáshoz is **csúsznak**, nem ugranak. ⛔ **HELYESBÍTÉS:** a #2034 köre azt írta, hogy „a becsúszás-hipotézis megdőlt, mert a pozíciót a tick közvetlen `mov`-val írja" — a `mov` által írt érték épp a sáv-kiértékelőtől jön, és a `+0xb0`/`+0xb4` csak **változás-őr** (utolsó ismert pozíció), ami a popup vtable `+0x50` újrarajzolóját ébreszti. **Melléklelet:** a cellaelhelyezés a `0x00d678d4` bájton ágazik el, ami a **jobbról balra (RTL) elrendezés** jelzője — a `Preferences`/`RTL` beállításkulcsból töltve (`0x0098f8af`–`0x0098f8e1`), 114 hivatkozással. **Nálunk (mérve):** csak átlátszóság-animáció van (250/500 ms), `x`/`y` animáció sehol. Jegyek: **#2122** (lezárva), **#2157** (a csúszás megépítése).

⭐ **2026-09-03 — a cella jobb sávjának három rétegéről kiderült, hogy EGYIK SEM vezérlő (#2035).** Az **összecsukás** halott erőforrás: a `popup+0x13c` slotra a `0x00654800`–`0x0065AC00` tartományban (a `CNotifierPopup` és a `CBaseNotifier` MINDEN vtable-metódusa beleesik) **csak** a konstruktor (`0x00657046`) és a destruktor (`0x006572d3`) hivatkozik — **sosem rajzolódik ki**. A **fogantyú** kirajzolódik (`0x0065878e` → réteg-blit `0x009ab410`), de nem interaktív. **Miért lehetetlen a vonszolás:** az ablak üzenetkezelője (`0x00657d10`) pontosan **hat** üzenetet kezel — `WM_LBUTTONDOWN` (0x201), `WM_SIZING` (0x214), `WM_MOVING` (0x216), `WM_SETCURSOR` (0x20), `WM_CLOSE` (0x10), `WM_SHOWWINDOW` (0x18) —, és **nincs köztük `WM_MOUSEMOVE` és `WM_LBUTTONUP`**; a `WM_SETCURSOR` egyetlen kurzort tölt (`IDC_ARROW`, `0x7F00`). A kattintás **egyetlen** téglalapot vizsgál és **egyetlen** jelzőt állít (`cella+0x14`, `0x00657f13`); a három rétegre nincs külön találati vizsgálat. A lap tartalmazza mind a nyolc réteg slotját hivatkozás-számmal. Megvalósítás (a fogantyú kirajzolása, a komment pontosítása): **#2133**. Jegyek: **#2035** (lezárva), **#2133**.

⭐ **2026-09-03 — a két animált sáv TELJES ÁLLAPOTGÉPE mérve (#2122), benne egy eddig ismeretlen animációval.** A sáv-író (`0x006558b0`) hívási helyei **kimerítően** végigpásztázva: **pontosan kettő van**. Élő cellára képkockánként a cél (**−1,0** ; a cella **sorszáma**), **0,6 s** alatt (`0x00c7e304`); **elbocsátáskor** viszont (**0,0** ; **0,0**), **0,3 s** alatt (`0x00c7dcc8`, `0x00655c98`) — tehát **az eltűnés kétszer gyorsabb, mint a beállás**, és ez a 0,3 s eddig sehol nem szerepelt. Az elbocsátás egyben `cella+0x11 = 1`-et állít (a tick ezt nézi) és **nullázza a határidőt** (`+0xb8`). A kezdőállapot mindkét sávra **0,0**; a cella `+0x0c` mezője **−1,0** (ugyanaz a konstans, mint az A sáv célja). **NEGATÍV EREDMÉNY, mérve:** a `0x00654800`–`0x0065AC00` teljes tartományban (a `CNotifierPopup` és a `CBaseNotifier` MINDEN vtable-metódusa beleesik) a `cella+0x88`/`+0xa0` értékeket **semmi nem olvassa rajzoláshoz** — csak a legutolsó kulcskocka kiolvasása, két cella-másolás és a konstruktor. ⇒ a sávokat **nem az értesítő** fordítja képi mennyiséggé; a kulcskocka-rendszer általános (`0x009e6010`-nek **22** hívója van). **Nyitva:** melyik képi mennyiséget vezérlik és mit jelent a `−1,0` — **#2122**.

⭐ **2026-09-03 — az ANIMÁCIÓ ALAKJA MEGVAN, és EGYIK felkínált lehetőség sem volt jó.** A #2034 „becsúszás VAGY áttűnés" kérdésére a válasz a harmadik: a tick (`0x006575b0`) cellánként **két absztrakt skalársávot** animál kulcskockásan (`cella+0x80…0x94` és `+0x98…0xac`, 40 bájt/kulcskocka, az utolsó érték `[bázis + n·40 − 0x18]`). Az átmenet **hossza 0,6 s** (`0x00c7e304`, kiolvasva), a **görbe exponenciális** `u = 8·t` skálán (`0x0072df60` függvénymutató + `0x00c7ea10` = 8,0). Az egyik sáv célértéke állandó **−1,0** (`0x00cf3ed0`), a másiké a cella **sorszáma a veremben**. **A becsúszás-hipotézis MEGDŐLT:** a pozíciót (`cella+0xb0`/`+0xb4`) a tick **közvetlen `mov`-val** írja (`0x00657827`), tehát a képernyőn kívüli parkolóhely nem egy vízszintes animáció kiindulópontja. A lap „Elszámolás" táblájának 2. sora ✅-re váltott. **Nyitva:** mit vezérel a két sáv a rajzoló oldalon — **#2122**. Jegyek: **#2034** (lezárva), **#2122**.

### [picasa-kereses-modok.md](picasa-kereses-modok.md) — nincs nyitott kérdés

⭐ **2026-09-03 — az idő-csúszka NEM tartomány-választó, hanem KOR-szűrő; a teljes képlet kiolvasva (#1830).** A felirat („Filter by date range" / „Szűrés dátumtartomány szerint") **félrevezet — az eredetiben is**: az egyfogantyús `timeslider/scaleslider` egyetlen `float` értéke (`s`) egy maximális kort ad meg. **A képlet:** `s == 0` → nincs szűrés; egyébként `napok = 2^(13·(1−s)) + 1`, a vágópont pedig `MOST − napok` (nap-egységű `double`, ugyanaz az OLE-dátum-ábrázolás, mint a `.picasa.ini` `date=` kulcsáé). A konstansok kiolvasva: `0x00cf4c08` = **13.0**, `0x00cf3a48` = **2.0**, `0x00c7e328` = **1.0**. **A képlet KÉT független helyen azonos:** a találati fejlécben (`0x0066345c`) és **a tényleges keresés-végrehajtóban** (`0x0065ee3f`, a `0x0065d010`-ben) ⇒ a csúszka valóban szűr, nem csak feliratot állít. **A mértékegység csonkolt egészekkel dől el:** `napok < 30` → nap; `hetek(=napok/7) < 10` → hét; `hónap(=napok/30) ≤ 12` VAGY `év(=napok/365) == 0` → hónap; különben év — a négy felirat `CThumUI::searchpicsdaysold`/`wksold`/`mosold`/`yearsold` („Legfeljebb %d napos/hetes/hónapos/éves képek."). **A skála logaritmikus és FORDÍTOTT:** a bal vég ≈22,4 évet enged át, a jobb vég 2 napra szűkít; a váltópontok `s ≈ 0,3382` (390 nap), `0,5302` (70 nap), `0,6263` (30 nap). ⛔ **NEGATÍV:** a `searchcontainer/timecontainer` és a `..._label` a kódból **soha nem hivatkozott** — tisztán felületleíró elemek, a `_label` csak a buboréksúgót hordozza. **Geometria:** vályú 97 × 7, fogható sáv 88 × 13, fogantyú **10 × 13**, konténer 104 × 16. **Nálunk (mérve):** a csúszka ott van, de `enabled: false`, `objectName` és súgó nélkül (`MainToolbar.qml:438`), és a `queries.py`-ban **nincs** `taken_at`-alapú szűrő — noha a `taken_at` oszlop létezik. Jegy: **#1830**.

⭐ **2026-09-03 — a keresősáv hetedik eleme, a `searchoptions/dupesearch` FELTÁRVA, és AZONOS a Kísérleti almenü tételével (#2169).** **Milyen vezérlő:** értékkel rendelkező kapcsoló (`0x009cd8f0(elemnév, érték)`), **induláskor REJTETT** — a főablak-építő a vtable `+0x68`-cal elrejti (`0x0040c8c9`), a **`Ctrl+F6`** a `+0x6c`-vel megjeleníti (`0x005e62c8`). **Mit csinál:** a parancs (`0x005ccc14`) bekapcsolja a `searchcontainer/searchbutton`-t ÉS a `dupesearch`-öt, majd `0x0065b840`-nel **újrafuttatja a keresést** — az eredmény a **találati rácsban** jelenik meg, nem párbeszédben. **A kattintás ugyanez:** a keresőbeállítás-kezelő (`0x005d8810`) `repe cmpsb`-vel veti össze a nevet (`0x005d94c1`, `0x005d94d3`, hossz `0x19`), és a **`0x005d95af`** ágra megy — `push 1; push 0; push 0; push panel; call 0x0065b840`, **bitre ugyanaz a hívás**. ⭐ **AZONOSSÁG BIZONYÍTVA:** a bekapcsoló ág parancsazonosítója **`0x9d57`** (a magas tábla `0x005cde04`/`0x005cdc30`, `eax = cmd − 0x9d44`), és ugyanez a szám áll az `eMenuTools::ID_DUPES` menürekordjában (`0x0055c31e: mov word [0xd6e7b6], 0x9d57`) ⇒ a menütétel és a keresősáv-kapcsoló **ugyanaz a funkció**. **Nálunk (mérve):** a `dedup/` mag megvan, de a felület **önálló párbeszéd** (`Main.qml:1123`), nem keresési mód. Jegyek: **#2169** (lezárva), **#2174** (a felületi bekötés), **#2142** (a menütétel helye, kommentelve).

### [picasa-gyorsbillentyuk.md](picasa-gyorsbillentyuk.md) — nincs nyitott kérdés

⭐ **2026-09-03 — a diavetítésnek és a videónak NINCS saját billentyűkezelője: a navigációs billentyűk ESEMÉNYKÉNT mennek a fókuszált elemnek (#2164, LEZÁRVA).** A lánc 5. szeme (`0x00a53b00`) saját index+ugrótáblát használ (`0x00a53bb4`/`0x00a53ba8`, VK `0x08`…`0x70`), és három ágra oszt: **Backspace, Enter, Esc, Space, PageUp/Down, Home/End, mind a négy nyíl, Insert, Delete, F1** → `0x00a582f0` **továbbító**; **Shift/Ctrl/Alt önmagában** → eldobás; minden más → `Ctrl`+`A…Z` ág. A `Tab` `WM_CHAR`-on külön megy (`0x00a58170`, Shifttel fordítva). A továbbító **eseményobjektumot épít** (`0x005c5da0`, `0x009dd770`, `0x005de720`), megkülönbözteti a `WM_KEYUP`-ot (`0x00a58322`), és a **fókuszált elemnek** küldi. ⛔ **HELYESBÍTÉS:** az előző kör a nyolc `cmp ax, 0x20` helyet lehetséges `Space`-kezelőnek jelölte — **mind a nyolc bitmélység-vizsgálat**: a szomszédos ág `cmp eax, 0x32595559` = a **`'YUY2'` FourCC**, a hibakód `0x8004022a` = **`VFW_E_TYPE_NOT_ACCEPTED`**, a mező pedig `word ptr [reg+0x0e]` = a `BITMAPINFOHEADER` **`biBitCount`**-ja (1/8/24/32 bit). A kitűzött „következő lépés" tárgytalan. Ezzel **öt független kizárás** áll össze, és a kérdés lezárul. Jegy: **#2164** (lezárva).

⭐ **2026-09-03 — a billentyűkezelés LÁNC, nem nézetenkénti kezelő — és a `Ctrl+W` MÉGIS létezik (#2164).** A `0x005e6710` egy felelősség-láncot hív végig (`0xf4240` = kezelve, `0xf4241` = tovább): `0x00760970` → a Shift-csempeváltás → **`0x005d2290`** (csúszka-léptetés) → **`0x005b2390`** (projektlap-sáv) → **`0x00a53b00`** (általános vezérlő) → az F-billentyűk → **`0x005e60d0`** (a 34 elemes Ctrl-tábla). ⛔ **HELYESBÍTÉS:** az előző kör negatív listája szerint a `Ctrl+W`-nek „nincs ága" — ez a Ctrl-táblára igaz, de a billentyűt a lánc **4. szeme** fogja el: `Ctrl+Left`/`Ctrl+Right` (`0x005b23a6`/`0x005b23b6`) lapot vált, **`Ctrl+Tab`** (`Shift`-tel visszafelé, `0x005b23c8`) és **`Ctrl+W`** (`0x005b23dd`) bezár. **Új lelet:** a **csúszka-léptetés** (`0x005d2290`, `WM_CHAR`): `+`/`=` → **+0,02**, `−`/`_` → **−0,02** (`0x00cf50d8`/`0x00cf50d4`), a cél az `editslider<N>/editslider`, ahol `N = [panel+0x337c] + 1` (a fókuszban lévő csúszka). **NEGYEDIK, független kizárás a diavetítésre/videóra:** a `movsx/movzx …, word ptr [reg+8]` minden előfordulását végigpásztázva **húsz** VK-lánc van a `.text`-ben, mindegyik gazdafüggvénye azonosítva (10.16) — **egyik sem a diavetítésé vagy a videóé**. A `Space` nyolc `cmp ax, 0x20` helye sztring nélküli függvényekben ül; a következő lépés négy címmel megnevezve. **Nálunk (mérve):** a négy lap-billentyű és a négy léptető-karakter **egyike sincs meg**. Jegyek: **#2164** (szűkítve), **#2170** (a bekötés).

⭐ **2026-09-03 — a valódi kezelő a `0x005e6710`; a `0x005e60d0` csak a Ctrl-ÁGA — és a szerkesztőnek NINCS külön billentyűkezelője (#2164).** A `0x005e6814` `test al, 4` / `jg 0x5e69cc` vezet a Ctrl-táblába ⇒ **a `Ctrl` = 4-es bit azonosítása MÉRT** (eddig „erős" volt). A módosító nélküli billentyűk a `0x005e6710`-ben, `cmp ax, imm16` láncban: **F1** (`editpanel/edithelpbutton`), **F2** (átnevezés), **F3** (`searchcontainer/searchbutton` — ugyanaz az elem, mint a `Ctrl+F`), **F4** (`thumbui/startoggle`), **F5**, **F11**, **F12**. ⛔ **NEGATÍV EREDMÉNY, három független mérésből:** (1) a kombináció-építő `0x005c5f90` és az összevető `0x005c5fc0` hívóinak száma **1 – 1**; (2) a teljes `.text` 174 ugrótáblás `switch`-éből **egyetlen** indexel a VK-ból; (3) a `cmp ax, 0xBC/0xBE/0xBF` (`,` `.` `/`) alak **nulla** előfordulás ⇒ a szerkesztő és a könyvtárnézet **egy kezelőn osztozik** (a 7.4 pont lezárva), a diavetítés/videó pedig **nem ugrótáblás** kezelőben van (a 7.3 szűkül). ⭐ **MELLÉKLELET a #2141/#2146-hoz:** a `0x005e6710` a VK-vizsgálat ELŐTT `VK_SHIFT` le-/felengedésre `GetAsyncKeyState`-tel összeveti a tárolt `[panel+0x33a8]` jelzőt, és eltéréskor **újrafuttatja a csempeépítőt** (`0x005d7c20`) ⇒ **a Shift-váltás ÉLŐ**, nem a fül felépülésekor — a #2141 köre ezt tévesen írta. Jegyek: **#2164** (szűkítve, `ready`), **#2141** és **#2146** (kommentelve).

⭐ **2026-09-03 — a lap 7.1 pontja LEZÁRVA: megvan a menün kívüli billentyűk kódba írt elágazása (#442).** A 7.1 azt írta, hogy „nem fejtettük vissza, hol áll össze a (billentyű, módosító) → cmd leképezés a menün kívüli billentyűkre… statikus tömböt kerestünk — nincs a fájlban, tehát kódba írt elágazás". **A feltevés helyes volt, és a kód meg is van:** a könyvtárnézet kezelője a **`0x005e60d0`**, egy ugrótáblás `switch` — `movsx edi, word ptr [esi+8]` (VK) → `lea eax,[edi−0xd]` → `cmp eax,0x6b` → `movzx ecx, byte ptr [eax + 0x5e66a4]` (**indextábla, 108 bájt**) → `jmp dword ptr [ecx*4 + 0x5e6614]` (**ugrótábla, 36 bejegyzés**). Mindkét tábla kiolvasva ⇒ **34 kezelt billentyű**, ebből **8** közvetlen vezérlő-kattintás (`0x009cd8a0(elemnév)` → vtable `+0x78`): **`Ctrl+0` → `thumbui/toggle_right_drawer`** (a jobb fiók), **`Ctrl+9` → `editpanel/toggle_left_drawer`** (a bal fiók), **`Ctrl+F` → `searchcontainer/searchbutton`**, `Ctrl+1/2/3` → `smallthumbs`/`largethumbs`/`fullview`, `Ctrl+N` → `newalbum`, `Ctrl+F6/F7/F8` → `dupesearch`/`loadsim`/`clearsim`. A `Ctrl` kötelező (`0x005e6178`); a `Shift`/`Alt` a `0x005c5f90` szerkezetének `+1`/`+2` mezője — az azonosítás **két független egyezésből** (a lap 3.3 táblája: `Ctrl+3` = szerkesztési nézet, `Ctrl+R`/`Ctrl+Shift+R` = forgatás). ⭐ **Ezzel a 7.2 pont tizenkét ⬜ rekeszéből HÉT megoldódott** (`Ctrl+K` — ugyanaz az ág, mint a `Ctrl+T`; `Ctrl+Shift+B` = `bw`; `Ctrl+Shift+E` = `enhance`; `Ctrl+F`; `Ctrl+Shift+H`; `Ctrl+Shift+V`; és **`Ctrl+W`: NINCS ág**), a maradék öt (`F11`, `/`, `,`, `.`, 47.) pedig **a kezelő VK-tartományán kívül** esik. **Negatív eredmény, mérve:** `Ctrl+7`, `Ctrl+J`, `Ctrl+Q`, `Ctrl+W`, `Ctrl+Z`, `Ctrl+F1`…`F5` és a `0x0E`–`0x2F` tartomány a kihagyó ágra mutat — ezekre ne kössünk semmit. **Nálunk (mérve):** 27 `Shortcut` elem, 24 kombináció; a 34 ágból **20 hiányzik**. Jegyek: **#442** (lezárva), **#2163** (a húsz bekötése), **#2164** (a szerkesztő/diavetítés/párbeszédek kezelői).

### [filterdesc-registry.md](filterdesc-registry.md) — 2 BLOKKOLT tétel (a #2125, a tulajdonos telepítésének `filterdesc.xml`-jét kéri; és a #2456, a `PicnikFocalPixelate` HETES alakjának exportja)

⭐ **2026-09-05 — a kimeneti gombsor osztásköze 55, és megvan az OKA (#1504).** A `#1345` a respack rétegfejlécéből **59**-et vezetett le, a `#1420` kirajzolt képernyőképen **55**-öt mért. **Az 55 nyer.** Az elrendező (`0x00597f80`) a kurzort a gyerek elrendezés UTÁNI, tényleges szélességével lépteti (`0x0059883e`–`0x00598863`: `x1 − x0`, majd akkumulátorhoz adás) — az pedig a gomb saját respack-doboza, **55**; a `59 × 40` a `docbounds` cella-GRAFIKA mérete, nem osztásköz. Mellékesen kimérve: az `outputlayout.tre` **az egyetlen** hely a teljes `.tre`-készletben, ahol `Property cellwidth 50` / `cellheight 52` szerepel, és a két nevet **egyetlen** függvény ismeri (`0x00597390` → `+0x274` / `+0x278`), amit az elrendező a `0x0059862c`-en olvas (`cellwidth == 0` ⇒ a gyerek saját szélessége). A deklarált 50 a léptetésben **nem** jelenik meg — ez marad feltételes. Nálunk `TrayBar.qml:333` `actionCellWidth: 59` ⇒ soronként ~20 képponttal szellősebb. Jegy: **#1504** (a kód átvezetése fejlesztés).

⭐ **2026-09-05 — a Glow LEKICSINYÍTETT képen dolgozik, és ettől a `/8`-as vignetta-konstansunk LEVEZETETT lett (#2159).** ⛔ Helyesbítés: a lap eddig azt írta, hogy a blur-átváltó (`0x00bb89b0`) a gyakorlatban azonosság, mindig 1,0-t ad — **hamis**: a `Vignette`/`Matte` `xblur`-je `Blur·0,02·max(W,H)/4`, a 2560-as referenciaképen **448** (Blur=35), illetve **640** (Blur=50), vagyis a `p ≥ 255` ágra esik; az `X` nevezője sem `p`, hanem `min(p,255)` (`0x00cf3a00` = 255,0f). **Amire a visszatérés való:** a puffer LÉPTÉKE — az egyetlen hívó (`0x00bb8f70`) megszorozza vele a kép szélességét és egésszé csonkítja (`0x00bb91d3`, `0x00bb921a`), a gyorsút pedig csak `1,0`-nál fut. ⇒ a maszképítő 253-as vágása és 255-ös sugárkorlátja a **lekicsinyített** térben él. **Ez magyarázza a korábbi kör 13-szoros romlását:** teljes felbontásban minden `Blur > 13,2` ugyanazt a sugarat kapná — a golden viszont a `Blur=35` és a `Blur=50` exportot **ΔE 10,233**-mal különbözőnek méri. A lekicsinyítéssel végigszámolva a lánc három független Blur-álláson 1–2%-ra egyezik az eddig ILLESZTETT `0,02/8` konstansunkkal (a mi sugarunk = az eredeti menetenkénti dobozsugara, és `quality=3` dobozmenet szórása `√(r(r+1)) ≈ r`) ⇒ **a `/8` levezetett, nem illesztett**. Mérve: a levezetett sugár 4-ből 3 goldenen javít (átlag ΔE 1,342 → 1,301). Alapmérés a jegyben. Jegy: **#2159**.

⭐ **2026-09-05 — a `PicnikFocalPixelate` ini-aritása 7, és a #685 szettje SOSEM ezt próbálta (#2456).** A Glimmer-effektek `.picasa.ini`-alakja `vezérlőszám + (puck ? 2 : 0)` érték; a szettben szereplő **31 effektből 30** pontosan ennyit kapott, és mind a 30-nak volt ható esete. A kivétel a `PicnikFocalPixelate`: **5** vezérlője van (a `_chkReverse` jelölőt a korábbi leírásaink kihagyták, `filterdesc.xml:869`) + puck ⇒ **7**, a szett viszont **1 · 4 · 6** értékkel próbálta — a hatos alak a `FocalZoom` vezérlőkészlete. A `merokit-2` „halott” csoportjában **9 rövid alakból 9** maradt tétlen, köztük a `triple=1;`, holott a `triple` a saját hármas alakján ΔE 21,42-t ad ⇒ rövid alaknál a „nem történt semmi” a LISTA HOSSZÁRA bizonyíték, nem a szűrőre. ⛔ Ezért a #1142 verdiktje (`chain.MEASURED_NOT_RUNNING_OPS`) **nem megalapozott**. Mellette kimérve: a teljes műveletgráf (`filterdesc.xml:859–886`) — körmaszk + `Nested(BlendAlpha, Mask)` + `Resize(W/Impact) → Resize(W, smoothing=false)`; a `Reverse` **megcseréli** a belső/külső alfát, tehát alapállásban a körön KÍVÜL pixelez; és a körmaszk **NEM közös** a `FocalZoom`-mal (az előnézet→teljes felbontás átváltó csak annak a képletében van — nálunk közös `focal_mask()` fut, `render/focal.py:40`). Kimerítő pásztázás mind a 84 szűrőn: ez az **egyetlen**, ahol számított `CircularGradientImageMask` ül a `NestedImageOperation`-ön. Negatív lelet: a `runtime\picnik_effects\` könyvtár (`0x00c7f168`) a szállított telepítésben **nem létezik**, de a `PicnikGrain`/`PicnikTint` mérten lefut ⇒ nem ez az ok.

⭐ **2026-09-05 — a szállított `QuantizePalette` `Depth` = 4, és NEM kellett hozzá a tulajdonos gépe (#2454).** Az index eddig ezt a kérdést a #2125 blokkolt kérésével együtt sorolta („ugyanabból a fájlból derül ki") — **fölöslegesen**: a `Depth` **szállított konstans**, és ott van a kutatási másolatunkban: `research/copy_Picasa_3_7/Picasa3/runtime/filterdesc.xml:1255` → `<QuantizePaletteImageOperation Depth="4" Steps="{_sldrSteps.value}"/>`. *(A #2125 továbbra is blokkolt, mert az a FUTÓ telepítés — frissítéssel kicserélhető — fájlját kéri; a `Depth` viszont nem függ ettől.)* **A teljes paraméterlánc a leíróból:** Steps 2–30 (8) · Smoothing 0–100 (80) · Fade 0–100 (0) · elmosás `σ = (100 − Smoothing)/10 + 0,1`, `quality=3` · keverés `1 − Fade/100`. **Amit a lap saját szabályával együtt jelent:** a csomópont csak `Depth > 1`-nél hasad (`0x00bcb8e6`) és a gyerek `Depth−1`-et örököl (`0x00bcb9a6`) ⇒ `Depth = 4` mellett **három** osztási szint, legfeljebb **8³ = 512** levél — szemben a kódbeli alapérték (2) egyetlen szintjével (8 levél). ⚠️ **Nálunk:** a `glimmer_tone.py:286` az elmosást és a keverést **bitre az eredeti képlettel** végzi, a kvantálást viszont csatornánként egyenletesen; a docstring „egyenértékűséget" állít a `Depth`-tel — **ez nincs mérve** → **#2454** (mérést kér, nem átírást).

⭐ **2026-09-03 — a Glow maszképítője (`0x00bcc2e0`) TELJESEN kiolvasva, és a lépcsős képlet ROSSZ paraméterhez volt kötve (#2102).** A két 255-re vágott egész a **két blur-sugár**: `r_x = min(255, trunc(ceil((xblur−1)·0,5)·quality + 1))` és ugyanez `yblur`-rel — a két blokk azért néz ki egyformának, mert az elsőt egy `push ecx` (`0x00bcc3d4`) előzi meg, így ott az `[esp+0x88]` a bázis `[esp+0x84]`, azaz az `xblur`. ⛔ **HELYESBÍTÉS:** az előző kör a `ceil((s−1)/2)` képletet a **`strength`**-hez kötötte, és ebből azt jósolta, hogy a tag minden Glow-hívásra állandó 1 — **mindkettő megdőlt**. A `strength` valójában a `0x00bcbd90`-ben lép be **8.8-as fixpontos szorzóként**: `trunc(strength × 256)` (`0x00cf39d8` = 256,0), négyszer az `mm7`-be, mellette a `0x0100` (= 1,0) az `xmm7`-be és a `0x0080` (= 0,5 kerekítés) az `mm6`-ba. **A vágások mind kiolvasva** (`0x00bc52c0` + a hívó törzse): `glowalpha` **[0,1]** → bájt `trunc(a×255)`; `xblur`, `yblur` **[0, 253]** (`0x00cf0b4c` = 253,0f); `strength` **[0, 255]**; `quality` egész **[1, 15]** (alap 3). **A blur átváltója (`0x00bb89b0`) is teljesen kiolvasva** — zárt alakja `k = (p<255) ? 1 : 255/p`, `X = ((100+d) − d·k)/p`, `return (X>3) ? k : k·X/3` —, és **a gyakorlatban azonosság: minden filterdesc-beli Glow-értékre pontosan 1,0**, a képmérettől függetlenül. **Nálunk (mérve):** a `glimmer_ops.py` a nyers blurt szigmaként használja (`:575`) és a `strength`-et **[0,1]-re vágott** keverési súlyként (`:578`) — négy pontos eltérés. ⚠️ **A hatás NINCS mérve**, ezért a megvalósítási jegy MÉRÉSSEL kezdődik: **#2159**. Jegyek: **#2102** (lezárva), **#2159**.

⭐ **2026-09-03 — mind a HÁROM effekt-fül összevetve a csempe-táblával: az 1. fülön HÁROM téves kötés (#2141).** A tábla 36 rekordja pontosan a három eredeti fül 3×12-es rácsa, és a mi `EditorEffectsTab1/2/3.qml`-ünk **pozícióról pozícióra** ennek felel meg. **A 2. és a 3. fül mind a 24 csempéje egyezik.** Az 1. fülön három csempe **ugyanazt a hibát** követi el — a felirat az eredeti elsődlegesé, a hívás viszont másik szűrőt indít: „Élesítés" → `unsharp` (**Élesítés (régi)**) `unsharp2` helyett · „Filmszemcse" → `grain2` a `PicnikGrain` helyett · „Árnyalás" → `tint` (**Árnyalás (régi)**) a `PicnikTint` helyett. Kettőnél a hívott kulcs éppen az, amit az eredeti a **Shift** alá rejt ⇒ a felhasználó ma jelzés nélkül a „(régi)" változatot kapja. **Melléklelet:** a mi 7. (örökölt) fülünk bevezetője azt állítja, hogy ezek a szűrők „nem érhetők el a mai Picasában" — a lista első eleme, a `radtint` (*Sugaras árnyalás*) viszont **elérhető**: az 1. fül 12. csempéjén (`dir_tint`) a Shift hozza elő. Jegyek: **#2141** (hatóköre nőtt, a címe javítva), **#2146**, **#2148**.

⭐ **2026-09-03 — a csempe MÁSODIK szűrőjét a SHIFT kapcsolja be (#2141).** A csempe-tábla (`0x00c7e5a0`) hármasainak második mezője **nem passzív tartalék**: a fül felépülésekor a program egyszer lekérdezi a Shift állapotát — `push 0x10` (VK_SHIFT) → `call [0xc406f8]` = **`GetAsyncKeyState`** (a betöltési táblából feloldva: `0x00c406f8` → `0x00922efc`, hint 256) → `shr eax,0xf` / `and al,1` → `[panel+0x33a8]` (`0x005d7c91`…`0x005d7cc0`) —, és a csempeépítő ez alapján választ: Shift nélkül az elsődleges (`0x005d7d2e`), Shifttel a másodlagos (`0x005d7d70`), ha van (`0x005d7d78`). **Kilenc** csempének van másodlagosa: `unsharp2`/`unsharp` · `PicnikGrain`/`grain` · `PicnikTint`/`tint` · `glow2`/`glow` · `dir_tint`/`radtint` · `HeatMap`/`NightVision` · `Vignette`/`Matte` · `Pixelate`/`PicnikFocalPixelate` · `Border`/`RoundedEdges`; a maradék **27** mezője `NULL`. **Helyesbítés a #1869 köréhez:** a második mezőt „örökölt id"-nek nevezni pontatlan — négy felirata tényleg „(Old)", **öté viszont önálló effekt** (Radial Tint, Night Vision, Matte, Focal Pixelate, Rounded Edges). **Nálunk (mérve):** a `ShiftModifier`/`Qt.Shift` **egyáltalán nem fordul elő** az `EditorEffectsTab*.qml`-ben és a `ToolTile.qml`-ben — a funkció hiányzik. Jegyek: **#2141** (a kérdése megválaszolva), **#2146** (a Shift-ág megépítése).

⭐ **2026-09-03 — az effekt-csempe KÉK JELVÉNYE MEGFEJTVE (#1869): `mode="oneclick"`.** A parser (`0x008ff550`) a `mode` attribútumot egésszé fordítja (`0x00900490`: **`oneclick`→1**, `hard`→2, `effect`→4, `soft`→5, `tool`→6, `history`→7, más→0) és a `FilterDesc + 4`-be írja (`0x008ff847`); a csempeépítő (`0x005d7c20`) ezt olvassa (`CGenericFilter` vtbl `+0x14` = `0x008f6cc0`), `cmp eax, 1` (`0x005d7ec2`), és ezzel mutatja/rejti az `editpanel/fx%d_adorn` vezérlőt (`0x005d8108` → `[vtbl+0x6c]` / `[vtbl+0x68]`). Az „1" tehát **nem számláló és nem erőforrás-index**, hanem az `oneclick` mód enum-értéke. **Melléktermék:** az effekt-csempék TELJES táblája — `0x00c7e5a0`, **36 rekord × 12 bájt** (mai id + örökölt id), 12 csempe/fül ⇒ három effekt-fül; a lap tartalmazza mind a 36-ot. Ez oldja fel a „Filmszemcse nincs megjelölve" rejtvényt: annak csempéje a **`PicnikGrain`**-hez kötődik (`effect`), nem a `grain`/`grain2`-höz. **Nyitva:** a tulajdonos NEGYEDIK jelvényt látott a 2. effekt-fülön (`Invert`, `mode="effect"`) — ellentmondás, jegy **#2125** (`felhasználóra-vár`). A megvalósítás: **#2126** (nálunk ma az „alkalmazva" számláló kapcsolja, `EditorPanel.qml:352`). Jegyek: **#1869** (lezárva), **#2125**, **#2126**.

⭐ **2026-09-03 — a `GlowImageOperation` KEVERÉSE kimérve, és a `strength` LÉPCSŐSNEK bizonyult.** A kompozitálás (`0x00bb992d → 0x008f59d0 → 0x008f4780`) **közönséges source-over**, erősség-tag nélkül: `T = src·a + dst·(255−a)`, `out = (T + (T>>8) + 1) >> 8`; az SSE-konstansok kiolvasva (`0xcd0550` = 1, `0xcd0560` = 255), az alfa a FORRÁS képpont 4. bájtja. ⇒ **a `strength` nem keverési súly** — ezt a modellcsaládot (a `glimmer_ops.py:578`-at is) a mérés kizárja. A rajzoló argumentumlistája most a binárisból van (nem a Flash-analógiából): `(forrás, color, glowalpha, xblur, yblur, strength, quality, cél)`, és két meglepetéssel: a **`strength` natív alapértéke 0,0** (`fldz`, `0x00bb8eb5`), a `color` alfa-bájtja pedig **beégetve `0xFF`** (`0x00bb8e5f`). A `strength` a maszképítőben (`0x00bcc2e0`) **`ceil((s−1)/2)`** alakban lép be (`−1,0` a `0xc7e328`, `×0,5` a `0xc72150`; a `0x00529e10` = **`ceilf`**, a `0x00c12fd0` névtáblájával bizonyítva). **Ellenőrizhető jóslat:** a `filterdesc.xml` MINDEN Glow-hívására (1,1…1,5 és a Vignette/Matte `[1..2]` csúszkája) ez a tag **állandó 1** — ezért illeszkedik a Vignette-goldenre kalibrált modellünk. **Nyitva:** a `0x00bcc2e0` második fele (`0x00bcc438`-tól) — célzott dekompiláció kell. Jegy: **#2102**.

### [filters-decoded.md](filters-decoded.md) — 1 BLOKKOLT tétel (a #2456: fut-e a `PicnikFocalPixelate` a SAJÁT, hetes alakjával — egy windowsos export dönti el)

✅ **2026-08-24 — az utolsó kérdés (a `FocalZoom` perem-módja) LEZÁRVA MÉRÉSSEL:**
a halmozás csak nagyít (`zoom ≥ 1`), ezért minden minta a képen belülre esik —
négy perem-mód **bitre azonos** kimenetet ad képen belüli fókuszpontra. A mai
`cv2.BORDER_REPLICATE` helyes. Melléklelet: a natív mag (`0x00bcf4b0`) igazolja a
`zoom_max_offset` és `zoom_sample_count` képleteinket. Jegy: **#1351**.

### [picasa-create-features.md](picasa-create-features.md) — 1 nyitott kérdés (a #1412)

⭐ **2026-09-05 — a `.cxf` `scale` ÍRÓJA megvan, és semmit nem alakít át (#1412).** A lap eddig a `+0x2c` mezőt csak a **layout** oldaláról azonosította a `scale`-lel; most az **író** oldaláról is megvan, tehát a mezőazonosság **két független forrásból** áll. `FUN_008347b0` (ugyanaz, amelyik az `albumTitle`/`orientation`/`shadows`/`theta` attribútumokat is írja): `0x00835096` `push "scale"` (`0x00cbf80c`) → `0x008350ab` `mov ecx,[ebx+0x48]` → `0x008350ae` `mov edx,[esp+0x24]` → **`0x008350b2` `fld dword ptr [edx+ecx+0x2c]`** → `%f` (`0x00c817c0`) → `0x008350c9`. ⛳ **Kontroll a valódi fájlon:** a `%f` **hat tizedest** ad, és a mintáink pontosan így néznek ki (`scale="337.000000"`, `scale="1.000000"`) ⇒ nem másik függvény írja. ⇒ **a fájlban álló `313` pontosan a csomópont `+0x2c` mezője a mentés pillanatában**, íráskori átszámítás nincs. ⚠️ **Ez a kör NEM vezette le a 313-at**, és a `+0x2c` íróinak pásztázása a 2026-09-02-i eredményt **reprodukálta** (indexelt/SSE/disp32 alakú író nincs; a kollázs-sáv egyetlen mutatós találata, `0x0087b895`–`0x0087b898`, csak **másol** két csomópont közt). A **#1412 marad blokkolt**: a legolcsóbb út továbbra is egy **fekvő** tájolású Indexkép-`.cxf` a tulajdonos Picasájából.

⭐ **2026-09-03 (2.1 bővítés) — a 22 átmenet HIVATALOS MAGYAR neve.** A lap
eddig csak az **angol** neveket adta meg, és a **#432 sem** tartalmazta a
magyart — így a legördülő magyar felületen angolul jelent volna meg. A teljes
22 soros tábla most a lapon áll (`CTransitions::*`, `stringres-en-hu.tsv`).
⚠️ **Négy fordítás megtévesztő:** `wiperight` = **„Törlés"** (nem „…jobbra"),
`pushright` = **„Tolás"**, `circleout` = **„Kör"** — az alapirány rövid nevet
kap; és `timelapse` = **„Gyorsítás"**, nem „Időzített felvétel".
⚠️ **NE keverd össze a `CThemePrefs::` családdal** — az egy MÁSIK, **tíz**
elemű készlet (Sakktábla, Kollázs, Google Modulok…): *ha egy kör tíz
átmenetet talál, rossz családot néz.* **Új mérés:** a `makemoviepanel/rewind`
(**„Vissza a kijelölt diához"**) megjelenítése `0x0061681e`
(`[+0x210]=1`, `[+0x248]=0xff`); ⛔ **elvetett hipotézis:** az őrző globális
(`0xd67914`) **nem** szolgáltatás-kapcsoló, hanem a **felületi fa
gyökérmutatója** — egyetlen írója a keret-indító (`0x009c3a36`), és mind az
1712 olvasója `cmp …, 0` null-ellenőrzés. **NINCS MÉRVE**, mit csinál a gomb
kattintásra (az olcsó lánc kimerült). A fülek magyarul: **„Mozgófilm" ·
„Dia" · „Klipek"**. ⇒ **A `makemoviepanel` feltáratlan listája ÜRES: 5 → 0**
(globálisan 116 → 111); ezzel a **#2093** 3. pontjának négy elavult
felülbírálása is rendezve. Komment: **#432**.

⭐ **2026-09-01 — a #1412 egyik KORLÁTJA MEGDŐLT:** a jegy szerint „egy mintánk van (AI6)", de a `kollazs-golden/` **tizenegy** `.cxf`-je közt a **`regulargrid` (AI5) is egyetlen `scale`-t** használ (330) ⇒ **második adatpont**. Levezetve: a kizárt 300 és 359 az **oszlop-** és **sor-osztás**; az AI5-re pontos a megfelelés (`0,322266 × 1024 = 330`), az AI6-ra keresett tört **0,305664** — a felirat-sávot is tartalmazó cella lehet. Részletek a #1412 kommentjében. **Folytatás (2026-09-01):** mind a hat téma átmérve (`kollazs-eletciklus.md` **17.**) — a `picturepile` szorzója **pontosan 1,25000**, a `regulargrid`-é **1,00000**, a `contactsheet`-é **node-független**; a `scale` a **rajzolt méret**, nem a befoglaló dobozé; a 313 **nem beégetett konstans** (nulla találat a `.text`-ben). **Folytatás (2026-09-02):** a `.cxf`-író bináris oldala kimérve (`picasa-create-features.md` **1.6/g**): a csomópont-tömb **56 bájtos**, a `scale` a `+0x2c` (`0x008350b2`), a `theta` a `+0x28`; a mentés-szervező (`0x00834700`) **nem készíti elő** a csomópontokat. A 2026-08-30-i „vetítés/render-scale" magyarázat **MEGDŐLT**: a `regulargrid` elhelyezője **ugyanúgy `1,0`-t ír** a `+0x2c`-be (`0x0088520d`→`0x0088522d`), mint a contactsheeté — az `1,0` a norma. Kimerítő negatív pásztázás: indexelt, SSE- és disp32-alakú `+0x2c`-író **nincs**; a végleges értéket a kollázs-sáv 37 mutatós írójának egyike adja. A jegy **`blocked` + `felhasználóra-vár`** (fekvő Indexkép-minta). **⛔ Két SZÁMHELYESBÍTÉS a FILM fejezetben (2026-09-03):** az átmenetek száma **22, nem 18/21** — a 2.1 táblájából kimaradt a **`rect`** („Négyszög"), és a `0x00771a10` átmenet-nyilvántartó (934 b) **mind a 22 kulcsra** hivatkozik, tehát élő; a szövegdia-stílusoké **12, nem 11** — a 2.3 kilencet nevezett meg „+ további kettő" megjegyzéssel, holott **három** hiányzott (`Centered`, `I'm Feeling Lucky`, `Caption`). Mindkét lista most teljes, hivatalos magyar fordítással. Jegy-komment és címjavítás: **#432**.

⭐ **2026-09-02 (2.3/b) — a SZÖVEGES DIA fülének működése:** a beszúrás `<type>=2` rekordot hoz létre „Szöveg" placeholderrel, **a kijelölt dia UTÁN** (üres kijelölésnél a lista elejére), majd átvált a 2. fülre és a beviteli mezőre teszi a fókuszt (`WM_SETFOCUS`); a három kapcsoló mezői: **`<weight>` = 400/700** (GDI-súly, nem logikai!), `<italic>`, `<outline>`; a három legördülő a `<fontname>`, `<size>` és `<styleid>` mezőt írja, a **betűméret-lista teljes tartalma** `8·10·12·14·16·18·20·22·26·30·36·48·60·72·84·96` (`0x00c7e4f0`), a betűtípus a **`Preferences\makemovie::textfont`** kulcsba is bekerül; a két színválasztó `text_` / `bkg_` **előtag** szerint dől el. **Negatív eredmény:** a `titleoption_listbox` ága **halott kód** (a panelépítő nem hozza létre, és a névre egyetlen hivatkozás van a binárisban). Kommentek: **#432**, **#436**.

⭐ **2026-09-02 (2.5/c) — az „Opciók" fül és a KLIPTÁLCA működése:** a négy tálcagomb (`addclips` → klipgyűjtő mód, `addtomovie` → a lista **végére** fűz, `deleteclips` → töröl, `solo` → nincs parancs-ága); a három rendezés-rádiógomb az `.mxf` **`<ordering>`** mezőjét adja (**smart=0, album=1, chronological=2**), és a kattintás **önmagában nem számol újra**; a két csúszka képlete **kimérve**: `burstmodethresh = ⌊s²×86 400⌋` másodperc (maximum **pontosan 24 óra**, négyzetes görbe) és `felhasznált képek = ⌊t²×N⌋`, ahol N az „Összes fotó" darabszám — az `s` normalizáltsága a hangerő `×1000`-es skálázásából **mért**; új vezérlő: **„Dátumok megjelenítése"** (`showdates`); és egy eddig ismeretlen kapu: a **`CMakeFaceMoviePanel::askapplyswitchconfirm`** („Még nem alkalmazott módosítások vannak az Opciók lapon"), amelynek „Ne kérdezze meg újra" beállítása után a Mozgófilm létrehozása **némán eldobja** a függő módosításokat. Kommentek: **#1408**, **#432**, **#436**.

⭐ **2026-09-02 (2.6/c) — a „Mozgófilm létrehozása” gomb TELJES kimeneti menete:** a `render`, a `cancel` és az `export_youtube` **egy ágon** fut (`0x00620421`), a YT csak **előlépés** ugyanahhoz a `.wmv`-hez; a célmappa `<Képek>\Picasa\<honosított „Movies”>` (magyarul **Mozgófilmek**), **`My Videos` tartalékkal**, és a mappa `.picasa.ini`-t kap `P2category=Projects (internal)` sorral; a fájlnév négy lépésben áll össze (alapnév → `diavetites_jellegu_film` → „Helyreállított automatikus másolat” → tiltott karakterek kiszűrése), a kiterjesztés **`.wmv`**, a kódoló a futásidőben betöltött **`wmvcore.dll`** (`WMCreateProfileManager`, `WMCreateWriter`); a „Lecseréli a meglévőt, vagy újat hoz létre?” párbeszéd **felszabadítja** a régi fájl helyét, a másik mód **sorszámoz**; hibánál a `Preferences\SupportMovies` kulcs **elnémítja** az üzenetet. Jegy: **#1977**, komment: **#432**. ✅ **2026-09-03: a `0x00d694c0` mutató MEGVAN** — a **fájltörlés platformfüggő mutatója**: Windows NT-n a saját `0x009aecc0` burkoló (**`MultiByteToWideChar(CP_UTF8)`** → **`DeleteFileW`**), Windows 9x-en a nyers **`DeleteFileA`**; az elágazás a `GetVersion()` magas bitjén (`0x00c32bde`). Ezzel a 2.6/c „csere mód" lépése is teljes: a régi fájlt **törli**, `ERROR_ACCESS_DENIED`-nél 5 másodpercig újrapróbálja. Melléklelet: ugyanez a hibaosztály nálunk a **#1991** volt (lezárva) — a Picasa **ugyanazt a mintát** használta, amit mi is. A feloldás receptje: `binaris-regeszet-modszertan.md` **20.**

⭐ **2026-09-01 (2.9):** a filmkészítő **filmszalagja teljes fogd-és-vidd felület** (`filmstripmove/insert/dragtoclips/doubleclick/context`), a **négy csúszka** egy kezelőben, és a filmkészítő **saját, menthető projekt** (`CMakeMoviePanel::autosave`, „Back to Movie Maker", `Preferences\SupportMovies`). **2.10 (2026-09-01):** a `titledialog` — a **szöveges dia szerkesztője** (stílus- és méretválasztó, élő előnézet, `captionchk` a képfelirat átemelésére); a szöveges dia a filmszalagon **„Text Slide"** néven jelenik meg, az infósor `%s  %dx%d pixels` + `(%d of %d)`.

⭐ **2026-08-30 — a „Film készítése" szakasz MŰKÖDÉS-sel bővült** (2.5/b–2.8):
a `CMakeFaceMoviePanel` **„recompute" megerősítője** (`askapplyconfirm`
preferencia, a „Do not ask again" párbeszéd → #1408); a **7 kimeneti méret**
(320x240 … 1920x1080), a **3 hangsáv-opció** (Truncate/Fit/Loop), a film
**Preferences-kulcsok** (`showcaptions`, `cropfit`, `movievolume` 0..1000
alap 500, `makemovie1to1` alap 1); a **`video_control_bar2` sáv MŰKÖDÉSE**
(a `time` = `%02d:%02d:%02d` / `%02d:%02d:%02d` a DirectShow 100 ns-os
időből), és a **MoviePreviewHandler billentyű-térképe** (Space/Pause →
play-pause, Enter/Esc → teljes képernyő → #1154 42–44.). Jegy-kommentek:
**#432**, **#452**, **#1408**.

3. **Az Indexkép (contactsheet) `.cxf` `scale=313`-ának levezetése** — a
   Ghidra-C (2026-08-30) kizárta a layout-ból (a `0x00888210` 1,0-t ad a
   node `+0x2c`-be); a `313` a vetítés/render-scale képlete kell →
   `docs/specs/picasa-create-features.md` 1.9.14 + **#1412** (a jegy nyitva,
   fejlesztés + kutatás).

1. ~~**A Képkockamozaik kényszeres vágási szabálya**~~ — **A SZABÁLY KUTATÁSA MEGVAN**
   (#431/#916, 1.9.14, 2026-08-18): a kényszeres levél a téglalapot
   változatlanul átveszi és nem darabol tovább; a „nincs kényszer" jelölés
   mind a négy koordináta −1,0. A „melyik részfába irányítja" kérdés
   **tárgytalan**: nincs irányítás — a keresés körönként, képenként
   stempeli be a kényszert a csomópontba, és elutasításos mintavétellel
   találja meg a jó elrendezést. Ugyanitt megvan a pakoló **célfüggvénye**
   is (`0x00893570`, mindhárom rácsos témára közös): az **elpazarolt
   terület** minimalizálása. ⚠️ **A #916-os JEGY (a `CLocationTree` pakoló
   MEGVALÓSÍTÁSA és annak feltárása) NYITOTT** — a mai bekötésben a
   `_FRAMEGRID_CENTER` közelítés áll; a `0x008906e0` 7. slot ciklusa és a
   `0x008910b0` csomópont-gyártó dekompilációja a teendő
   (`kollazs-panel-ui-spec.md:1188`).
2. ~~**A Képkupac kezdeti (x, y) szórása**~~ — **elavult jelölés volt**: a
   szórás az 1.9.12-ben már 2026-08-14 óta megvan („legjobb jelölt"
   mintavételezés). A 2026-08-17-i átvilágítás vette le.

### [picasa-kollazs-felulet.md](picasa-kollazs-felulet.md) — nincs nyitott kérdés

⭐ **2026-09-03 — a 9. bit (keretválasztó) RENDERELT bizonyítéka megvan, a #997 leletje ELAVULT.** Eddig a bit jelentését csak a `0x00831750` fogyasztó-oldala támasztotta alá; most a tulajdonos valódi `AI6.jpg`-jén (3841 × 5120, `contactsheet`) képpontszinten is megvan: az első csempe körül **`(238,238,238)`** sáv fut — bájtra a `frames.WHITE_BORDER_BGR` —, a szélessége **41 / 42 / 43 px** három élen, a szabály pedig szabad paraméter nélkül `b = 0,05·(907 − 2b) ⇒ **41,23 px**`. Tehát az eredeti Indexkép **kirajzolja** a keretet, nem csak a `.cxf`-be írja. A lap **2.1/b**. **A mai kódunk is helyes** (**2.1/c**): a három keret-állás három különböző lapot ad, a felületi lánc ép — a #997 („a keretválasztó nem hat") a #1273 óta nem áll. **Új lelet:** a `test_indexkep_1273.py` tűrése elnyeli a keret elhagyását (`noborder`-rel is ÁTMEGY), tehát az őrnek **nincs foga** erre — önálló jegy: **#2118**. Jegyek: **#997** (lezárva), **#2118**.

✅ **2026-08-24 — az utolsó kérdés (a 6. bit MIÉRT a három rácsos témán van) LEZÁRVA**, ld. a lap **2/c** szakaszát: a bit pontosan a három `*Grid*` osztályon áll, és **nem öröklődésből** (a `CRegularGridTheme` szerkezetileg külön áll, mégis beállítja) — szándékos, témánként kiírt képesség-deklaráció. A *szándék* hatókörön kívül: nincs a binárisban. Jegy: **#1170**.

⭐ **2026-08-21, működés-kör (kilenc kérdés):** a
`kollazs-eletciklus.md` **16.** szakasza négy, eddig sehol nem szereplő
viselkedést rögzít — a **kattintható kész-értesítés**
(`collage::done` = „A kollázs kész (kattintson ide)"), a **„Mentés
mellőzve"** és a **formátum-eltérés** figyelmeztetése, a főablak
**várakozó állapota**, és a **`hascollage` PMP-oszlop** (1 bájt/sor,
valódi adaton mérve; a PMP-oszlopok **nem egyforma hosszúak**).
*(2026-08-21: a `hascollage` **jelentése is megfejtve** — ALBUM-oszlop,
„ehhez az albumhoz tartozik `PicasaCollage.cxf`", és az album
betöltésekor/mentésekor **fájl-létezésből** áll elő, nem a kollázs
mentésekor: [pmp-database.md](pmp-database.md).)*
Jegy: **#1168**. Az alábbi hat kérdést ez a kör NEM érintette.


*(A 2026-08-18-i két kör az eredeti hét kérdést **mind** lezárta — az
elszámolás a lap **12.** szakaszában. Ugyanaznap a harmadik, kimenet-kör
megfejtette a mentés TELJES törvényét — hova, milyen néven, hogyan, mi
történik utána; fájlválasztó bizonyítottan NINCS — a lap **9.1/b**
szakaszában. Az alábbi kérdések egyike sem igényel futó Picasát.)*

1. ~~A képesség-maszk **6. bitje** mit kapcsol?~~ — **MEGFEJTVE**
   (2026-08-21, a lap **2.**): a `collagepanel/groupnode`
   (`CollageNodeHandler` vtable 5. rekesze, `0x008603c0`) **külön,
   overlay feldolgozási ágba** kerül; a `+0x219` jelző hatására a
   jelenetgráf-bejáró (`0x009e2aa5`) külön verembe másolja a rekordot és
   korán kilép. A bit a három **rács-témánál** áll. A csomópont
   **vizuális szerepe is mérve** (a lap **2/b**): egy **`#F85E0F` színű,
   2 képpont vastag, élsimított KÖRVONALAS téglalap**
   (`ytShapeNode` + `ShapeDraw<RectSampler>`); a raszterező a belső
   képpontokat kihagyja (`0x007deddd` → `0x007defb0`), a bájtsorrend
   pedig a `0xFF7D8397` négy előfordulásával kalibrálva.
   **Ami MARAD:** miért épp a három rács-téma kapja a bitet.
   Jegy: **#1170**.
   *(A többi öt bit 2026-08-18-án lezárult: 12. = a téma megvalósítja a
   9. vtable-slotot, 13. = automata `collage_adapt`, 14. = a
   `collage::shadows` alapértéke, 15./16. = halott bitek.)*
2. ~~Mi a **célja** a `FILE_ATTRIBUTE_TEMPORARY`-nak?~~ — **LEZÁRVA**
   (2026-08-21, a lap **9.1/c**): a **hatóköre** kimérve — **öt** hely,
   mind projekt-kimenet (végleges és piszkozat kollázs-JPEG, kollázs- és
   film-automentés, film-kimenet); a Picasa **soha nem veszi le** és
   **soha nem olvassa vissza**, tehát a programon belül semmit nem
   vezérel. A **szándék** nincs a binárisban és nem is lesz. Linuxon
   nincs megfelelője — **nincs teendő**. Jegy: **#979**.
3. ~~Az **5120-as felső renderméret** szemantikája~~ — **LEZÁRVA**
   (2026-08-21, a lap **9.1/d**): négy dwordként utazik
   (`0, 0, 5120, 5120` = **négyzetes** doboz), és a mentési feladat
   `+0x64..+0x70` mezőibe kerül (`0x00838fc3`–`0x00838fe1`). Szabály:
   **lépték = 5120 / max(szél, mag)**, oldalarány megtartásával; hat
   golden fájl igazolja **mindkét tájolásban**. A `0x0087dcd0`-s nyom
   **téves volt** — az a hívás a mentés előkészítése.
4. ~~Az árnyék-képlet bemenete~~ — **LEZÁRVA** (2026-08-18, második
   árnyék-kör): az árnyék **témánként négy külön paraméterkészlettel**
   dolgozik (alfa 102 a Képkupacnál és a rácsos témáknál, 153 a Rácsnál
   és az Indexképnél); a `k` a képek cellaéle képpontban, az `A` lépték
   a 9.0 darabszám-képlete. Nem maradt feltételes állítás — a lap
   **9/b**-je. *(A jegy #977, már nem blokkolt.)*
5. ~~A polaroid-felirat **`vt[0x38]`** kapcsolója~~ — **HATÓKÖRÖN KÍVÜL**
   (2026-08-21, a lap **9/c**): a lánc végigkövetve (`ytSkia` `vt[0x28]`
   → `0x009033e0`), de a kapcsolónak **nincs „ki" állapota** — a `.text`
   teljes pásztázása szerint egyetlen szövegcsomópont-hívó sem ad 0-t —,
   ezért nincs megfigyelhető különbség, amit reprodukálni lehetne.
   Képernyőkép sem segítene. *(A `vt[0x2c]` ugyanaznap MEGFEJTVE: a
   `.tre` `textalign` bejárata — `0x009c7c00` hívja pontosan ezt a
   rekeszt, `"right"`→2, `"center"`→1 —, a kollázs **1**-et ad, tehát
   **KÖZÉPRE**; a `_draw_polaroid_caption`-ünk már így csinálja.)*
   Jegy: **#978**.
6. ~~Az **`avgcolor` adatbázismezőt** mi és milyen képlettel állítja elő?~~
   — **LEZÁRVA** (2026-08-21): a képlet a
   [pmp-database.md](pmp-database.md) „Az `imagedata_avgcolor` oszlop"
   szakaszában — csatornánkénti összeg / képpontszám **csonkoló** egész
   osztással, `0xAARRGGBB`-be csomagolva (`0x009ac640`); az élő,
   140 755 soros oszlop eloszlása a csonkolást függetlenül igazolja.
   A mi képletünk **két ponton eltér** → **#1171**.


### [export-parbeszed.md](export-parbeszed.md) — nincs nyitott kérdés

*(2026-08-20, három kör. A lap teljes: a `.fen` leíró, mind a 28 magyar
felirat, a kötések, a 9 beállítás-kulcs, a **képpontra mért geometria** a
tulajdonos képernyőképéről, a **teljes eseménykezelő-térkép** címekkel, és
az öt minőség-fokozat számértéke. A három korábbi nyitott kérdés a lap
**11.** szakaszában lezárva: a film-rádió alapértéke **0 = „Első
képkocka"**; a 193-as minőségérték
gyakorlati következménye bizonyítottan nulla, tehát a „Maximális"
nálunk maradhat 100.)*

0. ⭐ **2026-08-21, működés-kör:** a lap **8.** szakasza a kilenc
   működés-kérdést válaszolja meg (három belépési pont, a közös
   `CImageOutput` mag, a `.picasa.ini`-átvitel, az `]history:export`
   token, tíz hibaág, a registry-állapot). A **film-rádió
   ALAPÉRTELMEZÉSE lezárva** (`FileExportMovie` → `setne`). A maradék
   hét kérdés a lap **9.** szakaszában és a munkasorban. Jegy: **#1166**.

   ⭐ **2026-08-21, `CImageOutput`-kör** — a lap **10.** szakasza a
   9. szakasz 1., 3. és 4. pontját zárja le, utasításszinten:
   **az export után megnyílik a célmappa az Intézőben**
   (`ShellExecuteA`, `0x007414b6`), majd `]history:export` token —
   **indexelés és nézetfrissítés NINCS** a záró ágban; a **sorszámozás**
   teljes szabálya (`%0*d-%s`, szélesség = a kijelölt képek számának
   jegyszáma, 1-től, kötőjel + teljes eredeti fájlnév, `0x0073ee70`);
   az exportált mappa `.picasa.ini`-je **csak `caption` + `keywords`**
   (vesszős, `0x00740485`/`0x0074050d`); és **minden exportált fájl
   UGYANAZT az időbélyeget kapja** — mind a három mezőben, az export
   indulásának pillanatát (`0x00740c14` → `0x00740e57`).
   *(Ugyanaznap a **13.7**: a beállítások **OK-ra, egyetlen menetben**
   íródnak ki — a közös lezáró `0x008d2720` hívja a `vt[0x164]`-et, ha a
   lezárási kód 0 —, és **Mégsére semmi nem történik**: a `vt[0x168]` a
   `CExportPrefsDialog`-nál üres tő, `0x00b0d990`.)*
   *(És a **13.8**: az alapértelmezett célmappa neve a **szövegtárból**
   jön — angolul `export`, **magyarul `exportálás`** —, a név
   **fájlnév-tisztításon** megy át (`0x009946f0`, tiltott halmaz
   `\ / : * ? " < > |`), és a megjelenített útvonal **Wine-észleléssel**
   Unix-alakú is lehet (`0x0073a140`, `ShowUnixPaths`). Mellékesen egy
   **ütközés**: a mért időbélyeg-viselkedés és a mi `shutil.copy2`-nk
   kizárja egymást → **#1138**.)*
   *(És a **13.9**: az `]history:*` **NEM ini-token**, hanem az
   `albumdata_token.pmp` album-sorának tokenje — a tulajdonos valódi
   adatbázisában **kettő él** belőle (`]history:email` = „Elküldve
   e-mailben", `]history:upload` = „Feltöltve"), a négy literál a
   `0xc81238`–`0xc81268` blokkban, közös regisztrálóval (`0x0041c340`).
   **Exportot kérni a felhasználótól NEM kell.** Névcsapda: a
   `CThumbDB::Exported` kulcs a **feltöltés** gyűjteményét nevezi meg.)*

1. ~~**Mi TILTJA LE a film-rádiókat?**~~ — **LEZÁRVA** (2026-08-21, a lap
   **13.10**). **A párbeszéd SAJÁT kódja tiltja**, ha a kijelölésben
   **egyetlen film sincs**: `0x007394b3` (`[dlg+0xcd] == 0`) →
   `vt[0x114]("movies", 0)` (`0x007394e1`); a jelzőt a létrehozó
   (`0x005312b0`) teszi oda a `0x005c7990` vizsgálóból; a filmtípusok
   kódjai **8, 9, 10, 11, 12, 23, 29**. **KÉT korábbi állításunk
   megdőlt:** (a) „a párbeszéd saját kódja NEM tiltja le" — de igen, a
   `movies` név **második** hivatkozása épp a tiltás; (b) „a csoport
   címkéje fekete marad" — a képernyőképen a **címke is szürke**.

### [vagas-eszkoz-allapot.md](vagas-eszkoz-allapot.md) — nincs nyitott kérdés

~~A **kollázs Oldalformátum** legördülőjének sorrendje~~ — **MEGVAN**
(#876): a felépítő `0x007cc990` két kapcsolója adja; a kollázs esete az,
amikor **mindkettő hamis**. Ugyanitt derült ki, hogy a nyomatméretek
**metrikus/angolszász** ágra oszlanak.

### [picasa-gomb-es-menu-rendszer.md](picasa-gomb-es-menu-rendszer.md) — nincs nyitott kérdés

⭐ **2026-09-05 (129. kör) — MELYIK 13 elem villog („throb"), és MIÉRT.** A `runtime/respack.yt` teljes `superbutton(<stílus>, …)` kötéslistájából (171 kötés) **13 elem** kap villogó stílust, név szerint: `acquirepanel/anowbutton` (Importálás), `printpanel/pnowbutton` (Nyomtatás), `publish/backup_go` · `presentcd_go` (Lemezírás) · `webpublish_go` · `replicate_go`, `collab/ok` és `upload/ok` (Upload), `compose_share/send`, `collagepanel/sharebutton`, `makemoviepanel/render`, `printoptions/ok`, és **`thumbui/single_action_return`**. **A minta:** minden panelen a **fő cselekvés** gombja villog. ⭐ **A feltétel kimérve:** a `ytPopupListNodeCreator` (`FUN_00608da0`) négy 40 bájtos állapotképet másol az elemből (`+0x264` `_n`, `+0x28c` `_p`, `+0x2b4` `_h`, `+0x2dc` **`_t`**), és mindkét hívóhelyén (`0x00609248`, `0x006095fc`) a **negyedik** kép **szélesség**-mezőjét nézi — nem nulla ⇒ `mov byte [elem+0x35b],1`. A mezőazonosítás három konstruktorból (`0x009a8a80`, `0x009a8b60`, `0x009a8bc0`); a másoló `0x009a8ca0` `rep movsd ecx=0xa` ⇒ pontosan 40 bájt. ⇒ **egy elem akkor és csak akkor villog, ha a stílusa ad neki `_t` képet** — nincs futásidejű feltétel. ⛔ **Ez MEGDÖNTI a 125. kör lezárását** (`getmore-klipgyujto-mod.md` 3.3): a `single_action_return` **igenis villog**. Az ok: a stílus↔elem kötés **nincs a `.tre` szövegekben** (141 fájlból 89-et semmi nem `#include`-ol, a stílusnevekre nulla hivatkozás; kontroll: a panel-nevekre VAN) — csak a respackben. **Nálunk (mérve):** `grep -rn "throb" src/` → **0**, `SequentialAnimation` a QML-ben → **0** ⇒ egyetlen gombunk sem pulzál → **#2438**. ⚠️ A pulzálás **ÜTEME NINCS MÉRVE** (a `_t` kép csak a végállapotot adja).

1. ~~a **letiltott** gomb rajza~~ — **MEGVAN** (#893): a rajzoló az alfát
   **néggyel osztja** (`0x009e3178`), kivétel nélkül
2. ~~a `popuplist` **lenyíló panel** színei~~ — **MEGVAN** (#894):
   `listdecrect`, sík `#E8E8E8` kitöltés, `#BABABA` keret
3. ~~**A kiemelt sor SZÍNE**~~ — **MEGVAN** (2026-08-21, a lap 8.
   szakasza): **`#7D8397`**, kódkonstans, a binárisban **`0xFF7D8397`**
   alakban, **négy** helyen (`0x006084e2` = `ytTextPopupListItem`,
   `0x00665bc9` = `CAddToList`, `0x007af034` = a feltöltés-lista,
   `0x007cea13` = a webalbum-panel), mindenütt a
   `test byte ptr [sor+4], 2` kijelölt-bit mögött. A nem kijelölt sor
   **`#FDFDFD`**. **A 2026-08-18-i „nincs a binárisban" negatív eredmény
   TÉVES VOLT:** a 24 bites alakra kerestünk, a konstans 32 bites
   (alfával) — a képernyőkép-mérés végig helyes volt. Jegy: **#894**.
4. ~~**A buboréksúgó rajza**~~ — **MEGVAN** (2026-08-21, a lap **8/c**):
   a tulajdonos képernyőképéből képpontonként mérve — kitöltés
   **`#F4F1E5`**, keret **`#B7B5AC` 1 px**, **derékszögű** sarkok, fekete
   szöveg, és **árnyék CSAK a jobb és alsó élen** (a bal/felső élen
   nincs). Az utóbbi a döntő nyom: ez pontosan a Win32
   **`CS_DROPSHADOW`** ablakstílus automatikus, rendszer-rajzolta
   árnyéka — ami megmagyarázza, miért nem volt sehol árnyék-kód a
   binárisban (a 8/b tizenegy pontos negatív leltára). Jegy: **#901**.

### [picasa-konyvtar-eszkoztar-viselkedes.md](picasa-konyvtar-eszkoztar-viselkedes.md) — nincs nyitott kérdés

⭐ **2026-08-24** — a lap egyetlen nyitott kérdése (**a `folderviewpopup` ▾
menü feliratai**) **LEZÁRVA**, és **képernyőkép nélkül**: a menüépítő
(`0x00559150`) 20 bájtos rekordtömbjének gépi végigjárása **160
parancsazonosítót** oldott fel egyértelműen. A ▾ menü a
`Nézet ▸ Mappanézet` almenü.

⭐ **2026-08-30 — a két további NYITVA pont LEZÁRVA, és a `prenotify`
„dekódolatlan" jelölés MEGFEJTVE** (a lap **4/c** szakasza): a
`0x005e2000` kezelő **teljes parancstérképe** a dokumentum-mezőkből — a
`ShowAlbumThumbnails2` preferencia a **„Indexképek megjelenítése a
könyvtárban"** (0x9cd7) pipa-tétel a ▾ menüben; a mód-mező
(`+0x2c0+0xd8`) 0/1/2/5 = a **rendezés-mód kódja** (Dátum / Legutóbbi
változtatások / Név / Méret); a `0x9e18/19/38` hármas a `+0x2c0+0xdc`
mező 0/1/2 rádiója — **2026-08-31 óta azonosítva is: a személy-lista
rendezésének három módja** (`Preferences\peoplesort`), ld.
`picasa-menu-parancsok-viselkedes.md` 36.3. A `prenotify` a `.tre`-parszerből (0x009ca5e0 →
0x009c7840) `[elem+0x380]=1` — a folderview a váltás előtt értesít.

**Két helyesbítés ugyanebből a körből:**
1. ⛔ a lap korábban a `flatview`-hoz `0x9c8b`-t, a `folderview`-hoz
   `0x9cbd`-t rendelt — **mindkettő TÉVES**, azok **rendezés**-parancsok
   (`ID_VIEWBYDATE`, `ID_VIEWBYRECENT`). A valódiak: **`0x9db6`**
   (Egyszerű mappanézet) és **`0x9db9`** (Fanézet).
2. ⭐ **HÁROM** mappanézet-mód van, nem kettő — a harmadik a
   **`ID_VIEW_WATCHED` = „Egyszerűsített fanézet"** (`0x9db8`), ami eddig
   sehol nem szerepelt nálunk (a `FolderHierarchyView.qml` fejléce is két
   módról ír). Jegy: **#853**.

### [picasa-arcfelismeres.md](picasa-arcfelismeres.md) — nincs nyitott kérdés (az `albumpeoplechecksum` képlete MEGVAN, 2026-09-05)

⭐⭐ **2026-09-05 (14.6) — MEGVAN az `albumpeoplechecksum` KÉPLETE, és 9 albumból 8-on BITRE egyezik.** A képlet: `acc = 0`, majd minden `i` **képindexre növekvő sorrendben**, ha `personalbumid[i] == <az album sorindexe>` **és** (`i >= len(facequality)` **vagy** `facequality[i] >= 5000`): `acc = rol(acc,7) XOR i`. **A hajtogatott érték maga a KÉPINDEX** — nem a `contactid` (ez zárja le a 14.2 és 14.5 kizárásait). **Számoló:** `FUN_0048ec70` (668 b, `ret 0x14`), a `FUN_0048ef20` hívja a `0x0048f1bf`-en, az eredmény a **3. argumentum** kimenő mutatóként. Címek: a nullázás `0x0048ece3`, az 1. szűrő `0x0048ed6e` (`ARG4[i] == ARG2`), a küszöb `0x0048ed85` (`0x1388` = **5000**), a hajtogatás `0x0048ed95`–`0x0048eda6` (`rol ebx,7` + `xor ebx,eax`), üres bemenetre `return 9`. ⛳ **A 114. kör megállását HORGONYOS veremszámolás oldotta fel, dekompiláció NÉLKÜL:** a `[esp+0x150]` ARG1-hivatkozás 12 helyen azonos szintet (`0x14c`) ad, és ezzel a `0x0048f19f` `lea edx,[esp+0x38]` push-onként visszaszámolva **`&local_0x30`** — három független rekesz-egyezéssel hitelesítve (`0x30`, `0x1f`, `0x28`). **MÉRÉS** (`research/testdata/Picasa2-arcok`, saját `pmpimport` olvasóval, 3338 sor): **8/9 bitre egyezik**; a küszöb nélkül csak 3 egyezne, tehát **nem elhagyható**. ✅ **A „1 tag → 0" csapda feloldva:** a 112-es album egyetlen képének (`3085`) `facequality`-je **38**, a küszöb alatt ⇒ a hajtogatás üres, a `0` **kiszámolt, helyes érték**. A 115-ös album eltérése **elavult tárolt értékkel** magyarázható (mind a 127 részhalmaz, más küszöb, fordított sorrend és ±1 eltolás kipróbálva és kizárva) — bizalmi fok **erős**, nem megerősített. **Nálunk:** az oszlopot nem olvassuk és nem számoljuk; a PicasaPy nem ír PMP-t, ezért ez nem hiány. Jegy **#2391** — **LEZÁRVA**.

⭐ **2026-09-05 (14.4) — a keresési tér a teljes binárisról KÉT függvényre szűkült.** A 14.2 javaslata (számold ki az oszlop indexét a regisztrációk sorrendjéből) **fölösleges volt**: az oszlopok **tagobjektumok fix eltoláson**, tehát elég az eltolásra pásztázni. Az `albumpeoplechecksum` a **`CThumbDB + 0x27b0`**, az `albumcontactids` a `+0x2748` (a regisztrációs `mov eax, <névhossz>` — 19, illetve 15 — bájtra hitelesíti a párosítást, `0x00415bcc` / `0x00415bbc`). ⛔ **Kimerítő:** a teljes `.text`-ben **hat** hely nyúl a `+0x27b0`-hoz, és közülük **egyetlen ír**: `0x0048f79d` a `FUN_0048ef20`-ban; az érték a `0x0048f7f8`-on lévő veremrekeszből jön, és **csak változás esetén** íródik (`0x0048f7fe`). Összevetésül az `albumcontactids` 15 helyen, 12 függvényben szerepel. **A képlet továbbra sincs meg**, de a folytatás két megnevezett függvény célzott olvasása (`FUN_0048ef20`, `FUN_0048af60`), és a 9 album mért értéke a repóban van, tehát azonnal ellenőrizhető. Jegy: **#2391**. · ⭐ **2026-09-05 (14.5) — KÉT jelölt kiesett, és megvan, HOL áll meg az olcsó ág.** A `FUN_0048af60` **nem** a számoló: egyetlen hívója van, és a törzse az album `albumcontactids` értékét olvassa ki a generikus oszlopolvasóval (`FUN_00448fb0`, 21 hívó), majd **sztringet/vektort másol** (`0x0048af7a`, `0x0048af83`, `0x0048afa2`). A `FUN_0048bd80` sem: a `0x0048be5d` előtt a vektort **üríti** (`0x0048be4a` felszabadítás, `0x0048be56`). ⛔ **A megállás oka pontosan megvan:** a `0x0048f7f8` olvasásához tartozó ÍRÁS **nincs ugyanazon a nyers `[esp+0x30]` eltoláson** — a törzs hét ilyen hivatkozásából a két írás (`0x004900c9`, `0x00490281`) egy 16 bites tömbön futó ciklus **számlálója** (`0x0049026e`), tehát más `esp`-állapot ⇒ **bázisblokkonkénti `esp`-követés kell**, és ITT indokolt a célzott dekompiláció, egyetlen pontos kérdéssel. ⭐ **A contactid-hipotézis MÁSODSZOR is megdőlt, független adaton:** a 112-es albumnak VAN egyedi `albumcontactids` értéke, a checksumja mégis **0**. ⚠️ **Csapda a következő körnek:** az „1 tag → 0” **nem törvény** — ugyanígy jelentheti azt is, hogy az oszlopot **még sosem írták** (az író csak változáskor ír); az adat a két olvasat közt nem dönt.

⚠️ **2026-09-04 — a fejléc PONTOSÍTVA.** Korábban „2 BLOKKOLT tétel" állt itt; a mérés szerint ez félrevezető:
a **14.1** (gyorsítótábla) **LEZÁRVA** (megerősítve, egyetlen üres bejegyzés), a **14.2** pedig **nem a
tulajdonosra vár** — a hozzá kellő adat **megvan és mérve van** (9 nevesített személy-album, a `db3` arc-oszlopai
élő adaton). Ami hiányzik, az a **képlet**, és a 14.2 megnevezi a folytatás pontos helyét is (az oszlop
**indexét** a `0x004127c0` / `0x00415790` regisztrációk sorrendjéből kell kiszámolni, majd a generikus
oszlop-beállító hívásait szűrni rá). ⇒ **A #1238 emiatt LEZÁRVA** — a jegy még a tulajdonostól kérte azt az
adatot, ami 2026-08-22 óta a birtokunkban van és fel is van dolgozva.

⭐ **2026-09-03 (15. szakasz) — a személy-album FEJLÉCSÁVJA és a javaslat-munkafolyamat felülete.** A lap eddig a motort és az adatot írta le; a felület, amin a javaslatokat jóváhagyják, hiányzott. ⛔ **Miért nem látta a lefedettségi mérés:** a kód **puszta levélnéven** hivatkozik az elemekre, és a példány névtere **dinamikus** (`albumheader/%x/%d`, `0x0074ad40`) ⇒ a `string_xrefs`-ben **nulla** találat `faceheaderpanel/`-re. **A fejlécsáv elosztója** (`0x005e0f70`, 3930 b) **25 parancsot** ismer, ebből nyolc a javaslat-munkafolyamaté. ⭐ **A „További javaslatok keresése" LEJJEBB VISZI A KÜSZÖBÖT:** `küszöb = FRSuggestionThreshold / 100 − 0,1` (alapértéken **0,75**), a három konstans kiolvasva (`0x006028be` = 85, `0x00cf3a08` = 100.0, `0x00c7dd30` = 0.1) — és **nem írja vissza** a beállítást (nincs `0x00401900` hívás). **Az elvetés a `.picasa.ini`-be megy:** a `confirmsel`/`ignore`/`removesel` közös kezelője (`0x005c9b00`) a `]ignoreface` és `]unknownface` tokeneket írja. A **„Név hozzáadása"** az Emberek panelt nyitja (`header_addname:%s`). Teljes magyar felirat-készlet + geometria (a `confirmsug` és a `confirmsel` **ugyanazt** a 88 × 27-es téglalapot foglalja — váltakozó gomb), és az „Ismeretlen emberek" testvérpanel két váltógomb-párja. **Nálunk (mérve):** egyetlen általános fejléc öt gombbal (`LightboxHeader.qml`), a javaslat-vezérlőkből **egy sincs**. Jegy: **#2187**.

⭐ **2026-08-22, arcfelismerés-kör (#26)** — új lap, a funkció **működése**
(nem a felülete): a három független réteg és a hét `Preferences`-kapcsolójuk
alapértékekkel, a két küszöb-legördülő teljes létrája (**50–95, ötösével,
alap 85**, az ugrótáblák nyers bájtjaiból), a `.picasa.ini` **KÉT** írási
útvonala és egy eddig sehol nem dokumentált kulcs (**`facedata`** — a 859
fájlos korpuszban **0** előfordulás), a `db3` kilenc arc-oszlopa **élő
adaton mérve**, a három romboló művelet pontos hatóköre, és a
`frversion="1.5"` migrációs kapu.

**Két korábbi állításunk MEGDŐLT:** a `facerect` nem „szentinel-es rect",
hanem **tisztán 0/1 logikai jelző**; és a tesztkészletben **igenis van
nevesítés** (13 941 régió).

✅ **Ugyanaznap FELOLDVA:** a tulajdonos adott egy nevesített arcokat
tartalmazó adatbázist, és ezzel a **teljes személy-album modell** megvan
(`]facealbum:<N>` ↔ `albumcontactids` ↔ `contacts.xml`, **9/9 egyezés**),
a **`facerectdata` jellemzőpontjai** (`conf`/`pan`/`leye`/`reye`/`mouth`),
és a felismerési **javaslat + pontszám** oszlopok. Ugyanitt **megdőlt a
saját reggeli állításunk**: a `facerect` IGENIS tárol valódi rect64-et.
Blokkolt maradt: a két `*checksum` képzési szabálya és a
`CreateAcceleratorTableA` tartalma (**#1238**).

### [picasa-elso-inditas.md](picasa-elso-inditas.md) — nincs nyitott kérdés

*(Új lap, 2026-08-21: az első indítás `initialscan` panelje — két
szövegkészlet (migráció / tiszta telepítés), 640×463 geometria, két rádió,
**rejtett Mégse**. Jegy: **#1167**. Egyik kérdés sem igényel futó Picasát.)*

1. ~~Mit ír a két rádió?~~ — **LEZÁRVA** (6.1): a panel nem ír fájlt,
   **−1/1/2 kódot** ad vissza. Ami MARAD: hol lesz ebből
   `scanlist.txt`-bejegyzés (`0x0040d6e3`-tól).
2. ~~Mi dönti el, melyik szövegkészlet~~ (`Text1` migráció / `Text2`
   tiszta telepítés) jelenik meg — **LEZÁRVA** (6.6): a felderítő
   `0x00406c00` a `+0x1020` sztringet a p1import ágon tölti
   (`0x00406ee9`), az indulás-rutin ez alapján dönt (0=migráció,
   1=tiszta). Megerősítve dekompilációval (2026-08-30).
3. ~~Hol jelenik meg a panel~~ (saját ablak vagy beágyazva), és mi
   történik, ha a felhasználó bezárja az ablakot (a Mégse rejtett) —
   **LEZÁRVA** (6.7): saját MODÁLIS ablak, bezárásra −1 a rekeszbe, az
   indulás `0xF4242`-vel megszakad.

### [picasa-mappanezet.md](picasa-mappanezet.md) — nincs nyitott kérdés

### [picasa-mappakezelo.md](picasa-mappakezelo.md) — nincs BLOKKOLT tétel (a hatókörön kívüli Apple-ágon felül; 2026-09-05: mindkettő lezárult, a `Type = 25` negatívan)

⭐ **2026-09-02 (16.2/b) — a könyvtárbejáró hibakereső kiíratása TELJESEN
feltárva, és egy eddig sehol nem dokumentált MÁSODIK kimenettel.** A
`0x004f25f0` **négy módban** hívható: az 1–3. a `dirscanner-start/up/
shutdown.csv`-t írja a `Preferences\WriteDirscannerCSV` **kapu** mögött, a
**4. mód a kaput átugorja és meg is nyitja** a fájlt. Mindkét kimenet a
**`#db3\`** mappába megy, `"w"` módban. A sorformátum
`"%s",%f,%f,%d,%d,%d,%d` (a hét oszlop forrás-eltolásaival), és a `Dirty`
meg a `Valid` **külön** jelző. ⭐ **A `badfiles.txt`** ugyanabban a
függvényben készül: a `Type == 4` → `%s (badfile)`, a `Type == 5` →
`%s (baddirectory)` ⇒ **a bejáró nyilvántartja a hibás fájlokat és
mappákat**. ⛔ Ebből termékhiba is előkerült: a mi `scanner/walker.py`-unk
**hét `OSError`-ágat némán elnyel** → **#1998**.

⭐ **2026-09-05 — a két blokkolt tételből EGY teljesen lezárult, a másik
háromnegyedéig; dekompiláció nélkül, helyi diszasszemblátumból.**

- ✅ **A `DirscanRegression`:** a bejárás végén, ha a kulcs be van
  kapcsolva, a Picasa kiírja a **4. módú** CSV-t (a `WriteDirscannerCSV`
  kaput megkerülve) és **azonnal kilép** (`ExitProcess`,
  `0x004e9d37`–`0x004e9d42`). Egyszer olvassa be (őrbit a `0x00da03c4`-en),
  a `0x00da03c0` bájtban tartja; ugyanez a függvény
  `QueryPerformanceCounter`-rel **méri is** a bejárást. ⇒ fejlesztői
  regressziós futtató, a termékre nincs hatása.
- ⚠️ **Helyesbítés — a `Type`-tétel részben ELAVULT volt:** az `1`
  (könyvtár) és az `1001` (arcsablon-bejegyzés) jelentését a
  `pmp-database.md` 8.1 **már megmérte** két valódi katalóguson (a 1001-et
  halmaz-azonossággal, 412 = 412). A blokkolás azért maradt, mert a
  választ MÁSIK lap adta.
- ✅ **ÚJ: a névfeloldás pontos szabálya.** `valid == 0` **vagy**
  `Type ∈ {1, 5, 25, 1001}` ⇒ a név önmagában a teljes út; különben
  szülő + név; hibás vagy `Type = 0` szülőnél **tartalék sztring, nem
  kivétel** (`0x004f27f3`–`0x004f2887`).
- ✅ **ÚJ: a `pmp-database.md` mért 412-es anomáliája megmagyarázva** — a
  `FUN_004e2990` (66 b) szülőlekérdező a `Type == 1001`-et a `+26`
  beolvasása ELŐTT zárja rövidre; arcsablon-bejegyzésen az a mező nem
  szülőindex. ⇒ terméki lelet: a mi szabályunk más → **#2404**.
- ✅ **ÚJ (erős): a `Type = 5` „HIBÁS könyvtár"**, nem „2. fajta" — a
  `badfiles.txt`-írója feltétel nélkül listázza (`0x004f2aaa`).

⭐ **2026-09-05 (122. kör) — a `Type = 25` NEGATÍVAN eldőlt.** A `típus`
mező forrása a **fájltípus-tábla 30 ágú kapcsolója** (`0x004fadb0`, tábla
`0x004fb948`); a tárolt érték az **ágindex + 2** (tíz független ponton
igazolva a `pmp-database.md` 8.1 mért táblájával). A **25-ös tárolt érték a
23. ághoz** tartozik, az pedig a **közös alapeset** (`0x004fb93f`), amely
**egyetlen kiterjesztést sem regisztrál**. ⇒ **A 25 nem
fájlformátum-típus** — egybevág azzal, hogy a bejáró a `{1, 5, 25, 1001}`
és a `{1, 25, 26}` **szerkezeti** halmazokban használja. A pontos szerepe
továbbra sincs megnevezve, de a formátum-irány **kizárva**. Részletek és a
teljes kiterjesztés↔típus tábla: `pmp-database.md`, „A `típus` FORRÁSA".
⛔ Terméki lelet: a `.jpe`, `.mpeg` és `.ty` **hiányzik** a beolvasó
szűrőnkből → **#2415**.

✅ **2026-08-24 — a két megmaradt „erős, nem megerősített" állítás MEGERŐSÍTVE:**

1. **Nincs minimális ablakméret** (2.3) — a kikötés megszűnt: a program **4**
   ablakosztályt regisztrál, mind a négy ablakeljárás átnézve, `WM_GETMINMAXINFO`
   és `WM_SIZING` **egyikben sincs**, ugrótáblás diszpécser sincs. *(Melléklelet:
   a 9. szakasz összevető táblájának 2. sora ELAVULT volt — a mi kódunk már
   `minimumWidth: 0` / `minimumHeight: 0`.)*
2. **A meghajtó-figyelmeztetés „NEM" ága** (6.1/b) — az út végigkövetve: sehol
   nem menti el a korábbi rádióállást, tehát **nem visszaállít, hanem feltétel
   nélkül** az „Eltávolítás" tételre kapcsol; a `+0x359` általános „benyomva"
   jelző (235 előfordulás), nem állapotmentő. Jegy: **#1334**.

### [picasa-eger-es-kijeloles.md](picasa-eger-es-kijeloles.md) — nincs nyitott bináris kérdés

⭐ **2026-08-22, mappahatár-kör (#1219)** — a **15.** szakasz bizonyítja, hogy
a mappahatáron való átnyúlás az eredetiben **nem egy ellenőrzés, hanem
szerkezetileg lehetetlen**: a feed konténere (`0x0076a390`) mindig pontosan
EGY sor kijelölés-csomópontját éri el, és mind a négy mag (tartomány
`0x00716ae0`, léptetés `0x00717eb0`, határ-ág `0x00717d10`, lasszó-teszt
`0x0071bc90`) csak a saját csomópontja `count()`/`itemAt()` párján iterál.
**A #1219 kifejezetten mérendőnek jelölt kérdése megválaszolva:** a nyilas
léptetés a mappa végén **MEGÁLL** (`0x00718031` `jbe`, mindkét vég ugyanaz
az ág), nem lép át és nem jelöl ki újat. **Egy állítás MEGDŐLT:** a
lasszónk hatóköre már ma is helyes.

*(A #905 nyolc, korábban csak névből következtetett `.tre` tulajdonsága a lap
1/c szakaszában kapott bináris választ; a végső látványbeli finomítások a
szakaszban külön bizonyítottsági fokkal szerepelnek.)*

⭐ **2026-08-20, kijelölés-kör:** a lap négy ÚJ szakaszt kapott, és ezek a
kijelölés eddig hiányzó **hatókörét** rögzítik:
**10.** a könyvtárnézet `CMultiAlbumNode`, **mappánként külön
`CSelectionNode`**-dal — mappaváltáskor a régi mappa kijelölése törlődik,
tehát a Picasában **nem létezik mappákon átnyúló kijelölés** ·
**11.** a Ctrl+A / Ctrl+D / Ctrl+I / Csillagozottak parancsazonosítói
(`0x9cb8` / `0x9c90` / `0x9c47` / `0x9d5b`) a kezelőikig, és a
„mindent kijelöl" mag (`0x00716f40`) · **12.** Home / End / Shift+Home /
Shift+End / Ctrl+Home / Ctrl+End / PageUp / PageDown teljes leképezése ·
**13.** a kijelölés-változás ára — az eredetiben egy menet, nálunk
**mért** 10 010 `stat()` + 6 006 ini-beolvasás egyetlen Ctrl+A-ra ·
**14.** a lasszó és a képhúzás **geometriai** szétválasztása: a
találat-vizsgálat a **kirajzolt képre** szűkít (középre igazítva,
`0.5` @ `0x00c72150`), a rács a mozgást elemtalálatnál **nem nyeli el**
(`0xF4241`), és az elrendezés cellák közti hézagot hagy — vagyis **ez sem
a mi döntésünk**, mint korábban gondoltuk
(jegyek: #1145, #1146, #1147, #1148).

1. ~~A **gumikeretes kijelölés** szabálya~~ — a `ytSelectionDragHandler` a
   **szerkesztő** téglalapjaié, nem a rácsé: **arányt kényszerít**
   (Shift 1,0 · Ctrl 4/3 · Alt 3/2, #891). ~~A RÁCS lasszójának szabálya~~ — **MEGVAN**
   (2026-08-18, 4/e): **metszés-teszt**, nem tartalmazás; a metszetnek
   szigorúan pozitív területűnek kell lennie.
2. ~~A **Shift-tartomány horgonya**~~ — **MEGVAN** (#892): a horgony a
   `[this+0x390]`, és Shifttel **egyesével bővít**, a horgony **továbblép**
   (nem Intéző-féle tartomány)
3. ~~A **26 belső eseménykód** jelentése~~ — **A GYAKORLATHOZ ELÉG MEGVAN**
   (2026-08-18, 4.2/b): a harmadik nekifutás megfordította az irányt, és
   nem az ablakeljárás felől, hanem a **84 `*Handler` viselkedéséből**
   olvasta ki. Nyolc kód jelentése megerősítve (1 = bal le, 2/3 = mozgás,
   4 = fel, 5 = jobb le, 0x0b = ejtés, 0x13 = találat-vizsgálat,
   0x1b = elrendezés, 0x1f/0x20 = be/ki), a visszatérési értékekkel együtt
   (`0xF4240` = kezeltem, `0xF4241` = add tovább). **Maradék:** a `WM_*` →
   belső leképezés — de a megvalósításhoz nem kell
4. ~~A **jobbklikk útja**~~ — **MEGVAN** (2026-08-18, 4/f): tizenhat helyi
   menü erőforrásneve a birtokló függvénnyel; a rácsnak album- és
   mappanézetben **külön** menüje van

### [picasa-ini-format.md](picasa-ini-format.md) — 1 BLOKKOLT tétel (a `[encoding]` fejléc, #2452; a `rotate(0)` és a `text=` stílusblokk 2026-09-05-én LEZÁRULT)

⭐ **2026-09-05 — MEGVAN, miért nincs `[encoding]` fejléc a korpuszban: ROSSZ ÍRÓT néztünk.** A lap eddig azt rögzítette, hogy a `0x0068ac80` „feltétel nélkül" a `[Picasa]` elé fűzi a `[encoding]\r\nutf8=1\r\n[Picasa]\r\n` literált (`0x00ca77f0`, 30 bájt), miközben a tulajdonos **694** album-jellegű `.picasa.ini`-jéből **egy sem** tartalmazza. **Az ellentmondás feloldva:** a `.picasa.ini` literált **43 függvény** érinti, és a `FUN_0068ac80` ezek egyike — **két** közvetlen hívóval (`0x00696d31`, `0x0069b87d`, kimerítő `e8`-pásztázás). A láncot RTTI-vel feloldva a gazda osztályok: **`PrepareCollection`** (vtábla-fej `0x00ca7c54`) és **`AlignedImageCollection`** (`0x00ca7d8c`) ⇒ az **export/előkészítés** ága, nem a fotómappákba író út. ⛳ **Élő kontroll:** `research/testdata/` alatt **71** `.picasa.ini`, ebből `[encoding]`-ot tartalmaz **0**; `Picasa.ini` (nagy P) fájl **0**. ⛔ **BLOKKOLT részkérdés → #2452:** ír-e a friss export ténylegesen `[encoding]`-ot? A meglévő exportált mintánk (`research/#2007-rotate-ini/`) **nem** tartalmazza, de azt az importálás és a négyszeri forgatás **újraírta**, tehát nem dönt; kell egy **érintetlen** friss export. ⭐ **A `rotate(0)` tétel nem blokkolt** — a lap „A nyitott kérdés LEZÁRVA — a tulajdonos élő mérése (#2007)" szakasza megválaszolta; a fejléc 2026-09-05-ig elavultan sorolta. ⛔ **HELYESBÍTVE a `picasa-create-features.md`-ben is:** az a lap **sztring-szomszédságból** („az `.exe`-ben közvetlenül az `autosave.cxf` után") azt állította, hogy a **kollázs-mentés** ír `[encoding] utf8=1` + `[Picasa] name=` szekciókat — téves; a #1050 ezt már élő adaton cáfolta, most a hívási lánc is.

⭐ **2026-09-05 — a `text=` stílusblokk KÉT blokkolt tétele LEZÁRVA, dekompiláció nélkül.** ⭐ **A 9. mező BITJEI:** a mezőt egy általános jelzőkapcsoló állítja (`0x005ba8a0`, a `0x00c943d4` vtábla **`+0x6c`** rése: `if (bool) [ecx+0x18] |= maszk; else &= ~maszk`), és a `+0x18` tag épp a 9. mező. **Bit 0 (`0x0001`) = ALÁHÚZOTT** (`0x0062ebb3`: az `edittextpanel/underline` ágban `push 1`); **bit 3 (`0x0008`) = DŐLT** (`0x005ba7b0`, vtbl `+0x34`: `push 8`, az `edittextpanel/italic` ág hívja). ⇒ a korpusz `0xC000`/`0xC001`/`0xC008` hármasa maradéktalanul megmagyarázva. Bit 14 (`0x4000`) a felirat létrehozásakor bekapcsolva születik (`0x005f633f`) és a `0x005bae39` szerint „egy méretarány pontosan 1.0"-t jelöl — **felhasználói jelentése nincs megállapítva**; bit 15 (`0x8000`) forrása **NINCS MEG** (a konstruktor a szót 0-ra állítja, és `push 0xC000`/`push 0x8000` + jelzőkapcsoló a binárisban sehol). ⛔ **KIZÁRVA: a félkövér nem bit ebben a mezőben** — az `edittextpanel/bold` ág a **betűsúlyt** írja (`0x0062e972`: `and eax,0x12c` + `add eax,0x190` ⇒ **700** be / **400** ki), a 7. mezőbe. ⭐ **Az ÁTLÁTSZATLANSÁG sora elavult jelölés volt:** „a leképezés nyitva marad" állt benne, holott a lap „A 6. mező (átlátszatlanság)" szakasza már megválaszolta (a csúszka nyers értéke, alulról 0,1-re vágva, `0x0062f449`–`0x0062f488`) — javítva. **Nálunk (mérve):** a `trailer` mező állandó `49152`, változatlanul őrizve; a rajzolónk viszont tudja a dőltet és az aláhúzást ⇒ **megrajzoljuk, de nem mentjük** → **#2448**.

⛔ **2026-09-02 — SAJÁT HELYESBÍTÉS a `geotag` írásán:** a lap írási-sorrend
táblája azt állította, hogy a kulcsnak „két ága" van (`%lf %lf` **vagy**
`%lf,%lf`). Ez téves: a szóközös alak a **belső érték beolvasása**
(`sscanf`, `0xca74d8`, pontosan két mezőt vár), a vesszős a **fájlba írás**
(`sprintf`, `0xc8187c`). A lemezre írt alak egyféle, és **hat tizedesjegyű** —
84/84 élő sor igazolja. Részletek: `picasa-helyek-panel.md` 1. szakasz.

⭐ **2026-09-02 (3. kör) — a LEGACY `crop=` alak és a MIGRÁCIÓ.** A
binárisban van egy **második, Picasa 2 korabeli** vágás-alak:
`crop=%d,%d,%d,%d,%d;` (`0x00c8130c`, mind az öt mező kötelező:
`cmp eax, 5`). A `0x004221b0` **négy 16 bites szót** pakol egy 64 bitesbe,
és **`crop64=1,<hex>`** filter-tokenné alakítja — a hívó a
`0x00425f60` **olvasó**, tehát a **migráció beolvasáskor fut**. Élő adat:
a korpusz **761/761** `crop=` sora már `rect64` ⇒ a tulajdonos gyűjteménye
teljesen migrált. Nálunk a régi alak `ValueError`-t adna
(`ini/rect64.py:28`) → **#2008** (P4, megelőző).

⭐ **2026-09-05 — MINDKÉT tétel LEZÁRVA, dekompiláció NÉLKÜL** (helyi
diszasszemblátum + verem-eltolás visszaszámolása):

1. ✅ **A mezőfelosztás:** `crop=<ELDOBOTT>,<bal>,<felső>,<jobb>,<alsó>;`
   **képpontban**, az eredeti kép `W × H` méretéhez viszonyítva. Három
   független bizonyíték: az alapérték-blokk (`0x004222e8`: `0,0,0,-1,-1`),
   a metszés `max/max/min/min` iránya (`0x00422491` → `FUN_009b4960`), és
   a tartomány-ellenőrzés (`0x004224b0`–`0x00422500`: `bal<jobb`,
   `felső<alsó`, `bal≥0`, `felső≥0`, `jobb≤W`, `alsó≤H`). Kontroll: a
   csomagolás `bal<<48|felső<<32|jobb<<16|alsó` — a `rect64` sorrendje.
   ⇒ **a #2008 megvalósíthatóvá vált** (a `blocked` címke levéve).
2. ✅ **Az ELSŐ számot a Picasa 3 ELDOBJA** — az `E+0x50` rekeszbe olvassa,
   `0`-ra állítja, és a 2547 bájtos törzsben **egyetlen utasítás sem
   olvassa vissza** (kimerítő eltolás-ellenőrzés a lapon).
3. ✅ **A `crop=` sor kiírása:** a Picasa 3 **csak** `crop=rect64(%s)`
   alakot ír (`0x00ca786c`), és **0 értéknél a sort elhagyja**
   (`0x0068b610`: `or eax,esi ; je`). Nálunk ez **egyezik** (mérve:
   `app/edit_controller.py:2032` `with_removed(..., "crop")`). Hogy egy
   legacy-migráció után a sor eltűnik-e, **erős következtetés** — a
   falszifikáláshoz migráció előtti/utáni fájlpár kell.

Lap: `picasa-ini-format.md`, „A LEGACY `crop=` alak" szakasz; jegy **#2008**.


⭐ **2026-09-02 (2. kör) — az ini ÍRÓJA két függvény, és van egy
kulcs→ALAPÉRTÉK tábla.** A `0x0068ac80` az album-szintű részt
(`name`/`description`/`location`/`category`/`date`), a `0x0068b320` a
képenkénti szekciókat írja; ugyanaz a két hívó fűzi őket össze. ⭐ A
`0x0068b320` két NULL-lal lezárt tömbje kimondja, mit tekint a Picasa
**alapértéknek**: `flipped`→**`flipped(0)`**, `rotate`→**`rotate(0)`**,
`filters`/`text`/`moddate`→**üres**. ⇒ **a `rotate` nullája NEM a kulcs
elhagyása** — a korpuszban **1 735** `rotate=rotate(0)` sor van. ⛔ Nálunk
a forgatás 0-nál **törli** a kulcsot, és a kód kommentje ezt „bitre pontos
round-trip"-nek mondja — Picasa-eredetű fájlon **fordítva igaz** →
**#2004**. Plusz: a `[encoding]` literál pontos alakja **CRLF-fel**
(`0x00ca77f0`, 30 bájt), és **0/859** valós fájl tartalmazza (694
album-jellegűből is nulla) ⇒ írásnál **nem szabad magunktól bevezetni**.

1. **Ha a `rotate=` sor HIÁNYZIK és a felhasználó 0-ra forgat, kiírja-e a
   Picasa a `rotate(0)`-t?** A korpusz csak a végállapotot mutatja.
   **Megszerzés:** a tulajdonos windowsos Picasájában egy `rotate=` nélküli
   képet 4×90°-kal elforgatni. A #2004-et nem blokkolja.


⭐ **2026-09-02 — a `text=` STÍLUSBLOKK két nyitott mezőjéből kettő megvan.**
A szerkesztő szöveg-eszközének (`edittextpanel`) kezelőiből: a formátum
maga `v1,%u,%u,%f,%f,%f,%f,%u,%u,%u` (`0x00ce42e8`; az olvasó `cmp eax, 9`),
és **az olvasó két RÉGEBBI, `v1` nélküli alakot is ismer** ⇒ a `v1`
formátum-verzió. Az **5. mező (`<a>`) a KÖRVONAL VASTAGSÁGA** (0…1, alap
**0,5**, **0 = nincs körvonal**), a **8. mező a betűsúly** (400 / **700**
félkövéren), az **igazítás** értékkészlete **0 = bal · 1 = közép ·
2 = jobb** (`0x0062f300`). ⛔ **Ebből kiderült egy termékhiba is:** a mi
írónk **csak a két színt** adja át, tehát nálunk a körvonal mindig eltűnik
és minden felirat félkövér → **#1994**.

1. **Melyik float az ÁTLÁTSZATLANSÁG — a 4. vagy a 6.?** Mindkettő
   `1.000000` mind a három valós blokkban (az alapérték), ezért a korpusz
   nem különbözteti meg őket. **Megszerzés:** egyetlen `.picasa.ini` a
   tulajdonos windowsos Picasájából, amelyben a felirat **csökkentett
   átlátszósággal** készült.
2. **Mi a `<b>` (9. mező)?** A korpuszban `0` és `258` (`0x102`); az
   `<a>`-val együtt mozog, de ez következtetés. **Megszerzés:** ugyanaz
   az egy minta, ha benne az **igazítás** és a **dőlt/aláhúzott** is
   eltér az alapértelmezettől.

✅ **2026-08-24 — LEZÁRVA.** „Mit tesz a Picasa, ha külső program írja az
inifájlt?" A kulcs **nem a képfájl, hanem maga a `.picasa.ini`**: a Picasa
mappánként eltárolja az ini **utolsó írási idejét** (`albumdata_inisync`,
FILETIME), és ha a lemezen lévő fájl újabb, újraolvassa — **`flags = 3`**-mal,
tehát a `filters` is hatókörben. Mérés: **783/787 bitre egyező** valódi
mappán (99,5%). ⇒ **elég írni az ini-t**; a képfájl érintése az eredetiben
nem létező út → **#1320**. Részletek: a lap „MEGFEJTVE: az újraolvasás
kulcsa az INI FÁJL saját dátuma" szakasza.

A megmaradt szál (miért nem jelenik meg mégsem a `filters=`) **nem a
kiváltás** kérdése — a szigorú beolvasás ága, **#685**.

### [szerkeszto-felso-sav.md](szerkeszto-felso-sav.md) — ✅ nincs nyitott kérdés (a blokkolt tétel 2026-09-05-én lezárult)

⭐ **2026-09-02, #1905-kör:** a szerkesztő fejlécének mind a hét vezérlője
kimérve (a tervezővászon mérete = a futásidejű képpontméret, hat elemen
igazolva a tulajdonos felvételén); a „paletta-ikonos gomb" = **`quickupload`**
(„Upload to your Web Albums Drop Box", `OneUp::ID_QUICKUPLOAD`) → **#1935**;
a filmszalag **hét férőhelyes** (`7 × 28 + 6 × 3 = 214`), az aktuális kép
**mindig a középső férőhelyen**; a hisztogram-doboz horgonya **`root.alsó − 95`**.

✅ **2026-09-05 — a bélyegképre kattintás szemantikája LEZÁRVA, és Ghidra NEM kellett.** A `CFilmstrip::vftable` (`0x00c9359c`) **29. rése** a `FUN_005a73d0` (1 520 b); az eseménykódot a `[esemény+8]` hozza (`0x005a7427`), a jelentésük a `picasa-eger-es-kijeloles.md` 4.2/b **már megerősített** táblájából. ⭐ **A kattintás KIVÁLASZT — de a gomb FELENGEDÉSÉRE** (kód 4, `0x005a7781`): lenyomásra (kód 1 **és 0x0d — ugyanaz az ág**) a kezelő csak találat-vizsgálatot végez (`[vtbl+0x80]` → `[this+0x380]`), elmenti a húzás kezdő X-ét (`[this+0x378]`) és megfogja az egeret. ⭐ **Üres területre kattintás nem választ** (`[this+0x380] == -1` ág, `0x005a77a6`). ⭐ **A kiválasztás VISSZAVONHATÓ:** az új index beáll (`[this+0x388]`), kimegy a **`filmstripmove`** értesítés (`0x00c93584`, `[vtbl+0x70]`), és ha a gazda **`0xF4242`**-vel válaszol, a régi index **visszaáll** (`0x005a7813`); elfogadva a `[vtbl+0x84]` görget/középre állít **`-1.0`**-lel (`0x00cf3ed0`). ✅ **Nálunk (mérve):** `PhotoViewer.qml:716–718` `TapHandler.onTapped` = **felengedés** ⇒ a lényegi viselkedés MEGEGYEZIK; a vétó-út hiánya **nem termékhiba** (nálunk nincs elutasítási ág, amit vétózni lehetne). Jegy: **#1935**.

### [getmore-klipgyujto-mod.md](getmore-klipgyujto-mod.md) — nincs BLOKKOLT tétel (2026-09-05-én lezárult)

⭐ **2026-09-02:** a `thumbui` `single_action_*` hármasa feltárva — a
kollázs/filmkészítő **klip-gyűjtő módja**. Két belépési pont, három
visszatérő felirat (`collagepanel::back_to_collage` · `CMakeMoviePanel::back_to_slideshow`
· `thumbui::back_to_previous_tab`), a ✕ **csak elrejt**. Helyesbítés: a
`konyvtar-ablak-meretek.md` 5.8 „haladásjelzés" elnevezése téves volt. → **#1939**.

⭐ **2026-09-05 — a throb MECHANIZMUSA kimérve, és a javasolt út HELYESBÍTVE.**
A jelző az **`elem + 0x35b`** (egy bájt). Beállítja a `.tre`
`Property throb 1` (`0x009c7891`, elemzési időben); **törli** az
`eThrobOff` parancs (`0x00601eb0`). Futásidőben **három** hely kapcsolja
be: `0x0062c3ac` — **névvel**, a `thumbui/webcambutton`-ra —, valamint
`0x00609251` és `0x00609605` a `FUN_00608da0`-ban, ahol az elem
verem-rekeszből jön, nem literálból. **Kimerítő sztring-leltár** (nyers
`[Tt]hrob` bájtkeresés): **három** találat, `eThrobOn` **nincs**; a
binárisban throb-bal kapcsolatban **egyetlen** elem van megnevezve, a
webkamera-gomb. ⛔ **A korábban javasolt `0x00601090` ZSÁKUTCA:** az a
parancs-diszpécser, és az `eThrobOff` ága a jelzőt **csak törli** — a
bekapcsolásról semmit nem mond.

⭐ **2026-09-05 (125. kör) — LEZÁRVA, NEGATÍVAN: a visszatérő gomb NEM
villog.** A két név nélküli throb-bekapcsoló ugyanabban a
`FUN_00608da0`-ban ül, és az **új objektumot gyárt** (`0x00608db1`:
`push 0x420` → foglalás, majd `0x00608dca` konstruktor). A függvény
mutatója a `.rdata`-ban **egyszer** áll (`0x00c80594`) ⇒ vtábla-fej
`0x00c8058c`, **2. rés**, COL `0x00cf853c` (`offset = 0`) ⇒ az osztály
**`ytPopupListNodeCreator`**. A bekapcsolás tehát a **frissen létrehozott
felugró-lista tételre** hat, nem `.tre`-ből származó gombra. Ezzel a
bizonyítás teljes: sem `.tre`-tulajdonság, sem névvel megcímzett parancs,
sem a két név nélküli út nem érheti el a `single_action_return`-t ⇒ a
negyedik (`_t`) bőr rajta **használatlan**. Jegy-komment: **#1939**.

⚠️ Külön téma (nem ennek a lapnak a kérdése, jegy nem tartozik hozzá):
**melyik** felugró-lista tétel villog és **mikor** — a feltétel a
`FUN_00608da0` helyi rekesze, amit egy korábbi hívás tölt.
   Lap: `getmore-klipgyujto-mod.md` 3.3; jegy **#1939**.

### [racs-nagyito.md](racs-nagyito.md) — nincs nyitott kérdés (2026-09-05)

⭐ **2026-09-05:** az utolsó blokkolt tétel — **„mekkora a nagyítás?"** —
**LEZÁRVA**, és a válasz az, hogy **nincs nagyítási arány**. A rajzoló ág
(`0x0077bb10`) elolvasva: a lencse a **teljes méretű képet 1:1-ben**
rajzolja egy **161 × 161**-es felületre (`0x0077c445`: `mov edx, 0xa1`),
csak eltolva, hogy a kurzor alatti képpont a **közepére** essen (a `80.0`
a `0x00cf4c30`-ból, a teljes binárisban **egyetlen** hivatkozással —
`0x0077bc5c`; és 80 = a 161 pontos közepe). A célterület
(`0x0077bcf5`–`0x0077bd19`) szélessége algebrailag `W`, magassága `H`,
tehát **skálázás nincs** — ez nem illesztés, hanem a kifejezés
következménye. Ezért nem talált arányt hét függvény átolvasása sem.
Kizárva: a `2276,5556` (`0x00d35808`, 15 olvasó a `.text`-ben, író nincs)
és a `0,5` (`0x00c72150`, a kép közepét számolja). Lap:
`racs-nagyito.md` 5/b.

⚠️ **Ebből terméki hiba lett:** nálunk a lencse a **bélyegképet** mutatja
zsugorítva (`LightboxFeed.qml:963` `source: elem.thumbUrl`), a
`nagyitas: 2.5` tulajdonság (`:846`) pedig **sehol nincs felhasználva** —
a nagyítónk **nem nagyít**. Jegy: **#2399**.

⭐ **2026-09-02:** a rács-nagyító működése feltárva — az 51.3 három korábbi
blokkolt részkérdéséből **három lezárva**. Helyesbítés: az 51.3
„nálunk nincs" állítása **elavult** (a #1808 azóta megépítette, a #1911
vette ki a gombot). Jegy-komment: **#1911**, **#460**.

### [racs-ures-allapot.md](racs-ures-allapot.md) — nincs BLOKKOLT tétel (2026-09-05-én lezárult)

⭐ **2026-09-02:** a `thumbui` `lightbox_esolo_*` párja **HALOTT** az
eredetiben (nyers bájtkeresés: 0 találat; pozitív kontroll a testvér
`lightbox_bgtext`-en) ⇒ **nem építjük meg**; helyette a `lightbox_bgtext`
**hét** kontextus-szövege él. Helyesbítés: a
`picasa-menu-parancsok-viselkedes.md` 51.4 „kis jegy értéke lehet" sora.
Jegy: **#1945**.

⭐ **2026-09-05 — a számított ág LEZÁRVA, dekompiláció nélkül.** A
`push edx` értékét **háromágú névösszevetés** állítja be (21 bájtos
`repe cmpsb`): `publish/rpoptionbox1` → panel-mód 1 → szövegindex **3**
(*All photos have been uploaded*) · `rpoptionbox2` → mód 2 → **4**
(*All photos currently online have these settings*) · `rpoptionbox3` →
mód 3 → **5** (*No photos can be removed from…*). Címek: `0x0067b171`,
`0x0067b1dc`, `0x0067b237`; a hívás `0x0067b285`. A minta:
**szövegindex = panel-mód + 2**. ⭐ **Független megerősítés a
`biztonsagi-mentes.md` 14. szakaszából:** a harmadik `label_rpoptionbox`
valódi funkciója az **online elemek eltávolítása** — pontosan az 5-ös
szöveg. ⚠️ A 0 · 1 · 2 index hívója **feltételes** marad (a 0 az
immediate-tel igazolt alapeset). Jegy-komment: **#1945**.

### [biztonsagi-mentes.md](biztonsagi-mentes.md) — ✅ nincs nyitott kérdés (2026-09-05: az utolsó blokkolt tétel lezárult)

⭐ **2026-09-05 (15. szakasz) — a `publish` sáv ÁLLAPOT-FRISSÍTŐJE, és egy HALOTT vezérlő-hármas (#440).** A 14. szakasz a sáv elemeit szerkezeti horgonyokkal adta meg (hol vannak); ez azt, hogy **mikor mit mutat**. Egyetlen függvény dönti el: **`FUN_00670160`** (1253 b, három paraméter, a harmadik a mód), négy hívóval (kimerítő `e8 rel32` pásztázás: `0x006708b1`, `0x00670e44`, `0x00676aa0`, `0x0067ba83`). ⭐ **A mód a panel `+0xd4` mezője**, és a három `rpoptionbox` írja: „Feltöltés" ⇒ **1** (`0x0067b1e9`), „Opciók módosítása" ⇒ **2** (`0x0067b17e`), „Online eltávolítás" ⇒ **3** (`0x0067b243`); kezdőérték 1 (`0x00670823`). ⛔ **NEGATÍV EREDMÉNY:** a függvény három azonos blokkja (`0x0067026b`/`0x00670342`/`0x00670419`) a módot 0/1/2-vel hasonlítja, és **mindhárom UGYANAZT a nevet kéri** — `publish/buoptionbox1` (`0x00ca459c`) —, ilyen elem viszont a **141** kicsomagolt `.tre` egyikében sincs (**ismert pozitív kontroll:** `rpoptionbox1` megvan a `publish.tre`/`publish_text.tre`-ben; a `publish.tre` egyetlen `#include`-ja a szövegfájl, tehát a 125 elemes készlet teljes). A névfeloldó (`0x009c2fc0`) és a rákövetkező `__RTDynamicCast` (`0x00c07db2`) `NULL`-t ad ⇒ **halott kód, nem kell megépíteni**; másodlagos jel, hogy 0/1/2-t vár, miközben a mező mérten 1/2/3. ⭐ **Négy ÉLŐ állapotszabály** (az elem `+0x20e` bájtja a REJTETT jelző — függetlenül igazolva a `FUN_0066fde0`-ból, `0x0066fe24`/`0x0066fe59`): **(1)** a `publish/backup_go` felirata „Biztonsági mentés", ha a kiválasztott készlet neve (`[panel+0x168]`) nem üres, különben **„Írás"** (`0x0067051b`–`0x00670581`); **(2)** a `publish/deletebackupset` **rejtve**, ha a készletek száma ≤ 1 (`0x006705c9`); **(3)** a `publish/backup_set_menu` **rejtve**, ha nincs egy készlet sem (`0x0066fdee`); **(4)** a `publish/backupcdheader` **kétállapotú** szövegelem, index 1, ha van kiválasztott készlet, különben 0 (`0x006705ea`–`0x0067063a`) — a két szöveg „Biztonsági másolat létrehozása CD-re/DVD-re" és „Készlet létrehozása vagy egy meglévő használata". ⛔ **Nálunk (MÉRVE):** a négy elemnévre `src/`-ben **0 találat** — a sáv nem létezik. Jegy: **#440** (kommentelve).

⭐ **2026-09-05 (15.6–15.9) — a mód KIMERÍTŐ írói/olvasói, a LÁTHATÓ következménye, és a készlet-párbeszéd vezérlői (#440).** Kimerítő bájtminta-pásztázás a teljes `.text`-en (`mov [ebx/esi+0xd4], imm32`) + a mentés-modul minden `+0xd4` hivatkozása: a `CBurnPanel` módjának **pontosan három** írója van (15.1), és **nyolc további függvény** olvassa 1/2/3-mal (`FUN_0066cb20`, `FUN_0066e970`, `FUN_0066ea40`, `FUN_0066eac0`, `FUN_0066eb40`, `FUN_006772b0`, `FUN_0067b7e0`, `FUN_0067be30`). ⛔ **KIZÁRVA:** a pásztázás negyedik-ötödik találata (`0x00679412`, `0x0067945d`) **más osztályé** — a `FUN_00679310` `__thiscall`, **nulla közvetlen hívóval**, és a címe egyetlen adathelyen áll: a `NewBkDialog::vftable` belsejében (`0x00ca6a18`; RTTI-horgony `0x00ca68b4`, a `CBurnPanel` vtáblái `0x00ca62e8`–`0x00ca6384`); ott az értékkészlet 0/1/2, itt 1/2/3. ⭐ **A mód LÁTHATÓ következménye** (15.7): a `FUN_0066cb20` a módból FŐNEVET választ — 1 ⇒ `il_BurnPanel::upload` „feltöltés” (`0x0066cdb5`), 2 ⇒ `::change` „módosítás” (`0x0066cdcd`), 3 ⇒ `::removal` „eltávolítás” (`0x0066cdc1`) —, és a `publish/final_storage` elembe teszi a PWA tárhely-előrejelzés négy mondatának egyikébe (`PWA_storage_total` / `_nolimit` / `PWA_no_storage_change` / `_nolimit`; `0x0066ceee` / `0x0066d004` / `0x0066d0ea` / `0x0066d187`); számolás közben `il_BurnPanel::calculating` „Számítás…”. ⚠️ A magyar sorszámozott helyőrzőket használ és **felcseréli** őket (`%3$s/%1$s`). ⭐ **A készlet-párbeszéd vezérlői** (15.8): `name` · `files` · `type` · `disk` + a `typegroup` szülő, hash-alapú név→elem keresőn át (`0x0052e590`); három szerep: felépítés `FUN_00678e80`, vezérlő→objektum `FUN_00679310`, objektum→vezérlő `FUN_00679570`. A párbeszéd `[this+0xd4]` tartalom-módja 0/1/2 — **ugyanaz az értékkészlet, mint a `backups.xml` `type` mezőjéé** (`bkallfiles`/`bkonlypics`/`bkonlyexif`); a másoló utasítás nincs meg, ezért **erős, nem külön igazolt**. ⛔ **Nálunk (MÉRVE):** a 15.6–15.8 elemneveire `src/`-ben **0 találat**, 64 találatos kontrollal (mind helyi adatmappa-kezelés). Jegy: **#440**.

⭐ **2026-09-05 (9.2) — A `BKTag` MÉGIS BEKERÜL A `.picasa.ini`-BE — de nem címkeként, hanem KULCS-ELŐTAGKÉNT (#440).** A blokkolt tétel LEZÁRVA. A kép szakaszába a Picasa egy **készletenkénti testvérkulcsot** ír a sima `backuphash` mellé: **`BKTag <készletnév>-backuphash=<érték>`**, ugyanazzal a 16 bites időbélyeg-lenyomat-képlettel (#643). ⛳ **Élő minta** a tulajdonos 2026-09-03-i mentése után: egy valódi `.picasa.ini` **20/20 szakaszában** ott a kulcs, mind `40037`, és a sima `backuphash` is `40037` ugyanott; a korpusz további öt `backuphash`-es fájljában készletenkénti kulcs nincs, és ott az érték képenként különböző (13/13 · 11/11 · 8/8 · 1/1 · 1/1). ⭐ **Bináris oldal:** az utótag literálja `0x00c81450`; az összefűzés `0x00429d1c`–`0x00429d25`; az adatbázis-olvasás `0x00429d3b` → `0x006a5790`; ha az érték 0, új bélyeg `0x00429d4d` → `0x0098b6e0` (`__time64` → `localtime64` → `0x0098b550`) + XOR-hajtás `0x00429d5c`–`0x00429d6c`; ini-írás `0x00429d86` → `0x00454770`; adatbázis-írás `0x00429d9f` → `0x006a5a60`. Átnevezéskor a régi ÉS az új kulcsnév is felépül (`0x00473fd5` / `0x0047402f`). ⛔ **MEGDŐLT** a 9. szakasz első olvasata („a mentés KULCSSZÓT tesz a képekre, nálunk a `keywords=` a megfelelője"): a `"BKTag "` (`0x00ca4698`) és a `"BKTag %s"` (`0x00ca614c`) literálra a teljes `Picasa3.exe`-ben **pontosan egy-egy** kódhivatkozás van (`0x00670b04`, `0x0067ad63`, kimerítő négybájtos pásztázás), és mindkettő a mentés-készlet rekordjának `setname` mezőjét építi, amit a `0x006759c0` a `backups.xml`-be ír — a kulcsszóíróhoz (`keywords=%s`, `0x0068b8bd`) egyik úton sincs kapcsolat. ⇒ **az inkrementalitás összehasonlítás:** `<készlet>-backuphash == backuphash` ⇒ naprakész. ⛔ **Nálunk (MÉRVE):** az `ini/document.py` a szóközös, ékezetes kulcsot helyesen olvassa és bitre azonosan írja vissza, `with_value` után is megmarad — **javítanivaló nincs**, őr-teszt viszont nincs rá: **#2462**. Lapok: `biztonsagi-mentes.md` 9.2, `picasa-ini-format.md`. Jegy: **#440**.

⭐ **2026-09-04 (13. szakasz) — a MENTÉS-KÉSZLET KÉT LELTÁRFÁJLJA MEGVAN.**
A tulajdonos átadta egy valódi mentés lemezképét (Picasa 3.9.141.259,
2026-09-03), és ezzel a **`PicasaManifest.xml` teljes nyelvtana mérve**
(elemek, attribútumok, CRLF, BOM nélkül, `shouldRestore` csak `NO` értékkel,
`[P]` / `$Application Data` útvonal-álnevek), a **`files.txt` nyelvtana** pedig
az író formátumsztringjeiből: `#`-es fejléc, majd tételenként **útvonal /
felirat / `ft,<négy hex FILETIME-fél>`**, a rejtetteknél `hf,1` — író
`0x008447b0`, `"w"` módban; a **mentés-ág feliratot ír, `ft,` sort nem**
(`0x00693bfc`). A két nevet **testvérfüggvény-pár** építi (`0x00843a30` /
`0x00843a90`), és **ugyanaz a virtuális metódus** írja mindkét fájlt
(`FUN_00692640` = `PrepareCollection::vftable` **+0x74**). Logikai
attribútumok: **hamis = `NO` vagy `FALSE`, minden más igaz**
(`FUN_0040eef0` a `PicasaRestore.exe`-ben) ⇒ `isHidden="YES"`. Az
`appVersion` a build **`%2.2f`** szerinti alakja (`141.259` → `141.26`).
⛔ **Negatív eredmény:** az `ft_abs,` rekordfajta **halott** — a `Picasa3.exe`
soha nem írja, a beolvasóban egyetlen hivatkozása a diszpécser, és
hétbájtos előtag-átlépés (`add eax, 7`) a teljes fájlban **nulla**
találat (a pásztázó ismert pozitívval ellenőrizve). ⛔ **Lemezre írt
készletben `files.txt` NINCS** — a leltár ott a `PicasaManifest.xml`.
Jegy **#2090** (LEZÁRVA), komment: **#440**.

⭐ **2026-09-03 (11.1 ÁTÍRVA) — a `files.txt` írása MEGVAN, és két korábbi
olvasat MEGDŐLT.** A `0x00677f6d` **nem** írás-hívás: a `0x00d69518` mutató
`GetFileAttributesEx`. A valódi menet **bájtra fűzés** (`0x00677de6`–
`0x00677ecb`): `CreateFile(OPEN_ALWAYS, R/W)` a célra + `CreateFile(OPEN_EXISTING,
GENERIC_READ)` a forrásra, **mindkettő teljes beolvasása**, `SetFilePointer(0,
FILE_BEGIN)`, majd **a régi, utána az új tartalom** kiírása — és a blokk csak
akkor fut, ha a másolandó elem célja maga a `files.txt` (mért `strcmp`,
`0x00677d38`). **Sorformázó a Picasa3.exe-ben NINCS**, a `\files.txt` sztring
egyszer fordul elő és **egyik társ-binárisban sem** (14 index, két lekérdezési
alak). A kérdés átfogalmazódott: nem „mi a sorformátum", hanem **„mi van a
forrásfájlban"** — ez **2026-09-04-én LEZÁRVA** (ld. a fenti bejegyzést és a
13. szakaszt); a **jegy #2090** ezzel lezárva. Komment: **#440**.

⭐ **2026-09-03 (12. szakasz) — a LEMEZRE ÍRÁS menete.** A 10. szakasz a
`publish` sávot írta le; ez azt, ami az **OK után** történik. **Mért képlet**
a lemez használható kapacitására (`0x0066be90`): `szektorszám × 2048 −
tartalék`, ahol a tartalék **DVD-nél 4 096 000**, **CD-nél 409 600** bájt
(`0x0066bf50` / `0x0066bf58`); kétrétegű lemeznél (médiatípus **`0x214`**)
rögzített **8 547 991 552** bájt; ha a kapacitás nem olvasható, a tartalék
alapérték **688 072 704** bájt. A „DVD-e?" hat kódra igaz (`0x00666400`).
⭐ **A mentés TÖBB LEMEZRE folytatódhat**, és a Picasa sorszámozza őket
(„Ez lesz a(z) %d. számú lemez a(z) %d darabból", `InsertNext::13`) —
**lemezíró nélkül ISO-fájl(ok)ba** is dolgozik (`InsertNext::7*`), ez a mi
környezetünkben az implementálható ág. A 21 írás-állapot, a törlés-
figyelmeztetés és a médiatípus-nevek hivatalos magyar szövege a lapon.
Melléklelet: a `WriteProgress::13` („Mentési készlet frissítése") kimondja,
hogy a **`BKTag` címkézés az írás VÉGÉN** fut, nem az elején. Új jegy:
**#2074**.

⭐ **2026-09-03 (12.8) — HÁROM külön kódkészlet, kettő megfejtve.** A lemez
felismerése nem egy számozáson megy: **(a)** az írhatósági állapot `0x301`–
`0x304` (`0x006665c0`, négy név + „Unknown"); **(b)** a **lemezformátum
`0xA1`–`0xFA`, 25 nevesített eset** (`0x00666630`, kétszintű ugrótábla
`0x0066682c` → `0x006667c4`) — a teljes tábla hivatalos magyar fordítással a
lapon (31 `ytICDVDR::MT*`/`MF*` kulcs); **(c)** a családkód `0x2xx`, hat érték,
**továbbra is megfejtetlen**.

⛔ **Megdőlt magyarázat:** a `0x2xx` **nem** az IMAPI2
`IMAPI_MEDIA_PHYSICAL_TYPE` + `0x200` — az illesztés ellentmond önmagának (a
kétrétegű IMAPI-kódok hiányoznak a „DVD-e?" listából, miközben a `0x214`
kapja a kétrétegű kapacitást). A `CDVDR.yti` indexében nincs médiatípus-szöveg,
és a nyers konstanskeresés sem szűkít. **NINCS MEG:** öt kód jelentése; a
megszerzés útja a `0x2xx` mezőt beállító COM-hívási lánc
(`IDiscRecorder2` → `CurrentPhysicalMediaType`). Lap: `biztonsagi-mentes.md`
12.8; jegy **#2074**.

⭐ **2026-09-02 (11. szakasz):** a `files.txt` **megnyitási módja MÉRVE** —
`OPEN_ALWAYS` + `GENERIC_READ | GENERIC_WRITE` (`0x00677de6`), `OPEN_EXISTING`
tartalékkal (`0x00677e31`) ⇒ a Picasa **vissza is olvassa**, nem csonkolja; a
csak-olvasható jelzőt itt is leveszi (`0x0067834e` → `0x00678362`). A
**sorformátum továbbra is BLOKKOLT, de szűkítve**: az író hívás
(`0x00677f6d`) **belső függvénymutatón** (`0xd69518`) megy, nem nevesített
importon — ezért nem találja meg sem a sztring-, sem az importnév-keresés.
Melléklelet: a `replicates.xml` mezőlistája **tételesen azonos** a
`backups.xml`-ével (közös író `0x006759c0`, közös olvasó `0x00676910`), az
utoljára használt cél **két külön kulcsban** él (`LastBkSet` /
**`LastReplTarget`**), és megvan a replikáció **négy állapotszövege** hivatalos
magyar fordítással. ⭐ **Strukturális kulcs:** a parancsdiszpécser
(`0x005fa770`) a sáv gombjait **`publish/%s_go` / `publish/%s_cancel`** alakban
szólítja meg, a `%s` ∈ {`backup`, `presentcd`, `replicate`} — ez egy **mért,
konkrét példa** a módszertani lap 19. szakaszának „dinamikusan összerakott
név" hamis-pozitív osztályára. Jegy-komment: **#440**.

⭐ **2026-09-02:** a mentés **MIT ÍR** oldala feltárva (az 50.2 a fogalmat és
a felületet adta, ezt nem): `backups.xml` négy mezővel, **három**
tartalom-mód, `files.txt` a célmappában, honosított
`\Picasa biztonsági másolat\`, lemezhely-ellenőrzés. Jegy: **#440**.

⭐ **2026-09-02 (2. kör) — HÁROM lezárás és KÉT helyesbítés:**
a `backups.xml` **a `db3` mappában** van (`#db3\` token, `0x00c7eeb8`,
átadva `0x00670ca8`/`0x00670aa8`), `"wb"` módban, a csak-olvasható jelző
levétele után; **az inkrementalitást adatbázis-CÍMKE adja: `BKTag ` +
a készlet neve** (`0x00670b25`) — nincs külön mentés-nyilvántartás.
⛔ **Megdőlt:** a `0x009bfde0` **nem** útvonal-építő, hanem az **XML
behúzása** (80 szóköz, a `0x009bfed0` elem-író hívja); és a
**`Picasa2Backups` nem mappa, hanem a fájl XML-gyökéreleme**. Új
szakaszok: 9. (BKTag), 10. (a `publish` sáv három módja, hét
beállításkulcsa, öt párbeszéde és tizenhárom tájékoztató szövege).

*(A „mi a `files.txt` sorformátuma / tartalma" kérdés **2026-09-04-én
LEZÁRVA** — ld. a 13. szakaszt és a fenti bejegyzést.)*

1. **A `BKTag` címke a `.picasa.ini`-be is kikerül, vagy csak az
   SQLite-indexbe?** ⚠️ A korpusz **nem tudja eldönteni**: a `BKTag`-re
   nulla találat, de a `keywords=`-re **is** — a korpusz kulcsszavakat
   egyáltalán nem tartalmaz. **Megszerzés:** a `0x00670b25` utáni
   felhasználó dekompilációja, vagy egy `.picasa.ini` olyan gépről, ahol
   futott a mentés.

### [ajandek-cd-kimenet.md](ajandek-cd-kimenet.md) — nincs BLOKKOLT tétel (2026-09-05-én a KIADÁS gomb is lezárult)

⭐ **2026-09-05 — a KIADÁS gomb LEZÁRVA: a kiadást a WINDOWS végzi.** A
korábbi blokkolás indoka („nincs `IOCTL_STORAGE_EJECT_MEDIA` **sztring**")
**rossz kereséssel** dolgozott: az IOCTL **szám** (`0x002D4808`), nem
sztring. A konstansra keresve **mindkét binárison 0 találat**, és — ez a
döntő — **egyik sem importálja a `DeviceIoControl`-t**; `\\.\`
eszközútvonal, `cdaudio`/`door open` MCI-parancs, `Eject` sztring sincs
sehol. Ami VAN: a `CDVDR.yti` hordozza a **`MsftDiscRecorder2`**
(`0x0004560c`) és a **`MsftDiscFormat2Data`** (`0x00045aa8`) **CLSID**-jét,
`CoCreateInstance`-szal példányosít, és a DLL-függőségei közt **egyetlen
eszközvezérlő API sincs**. ⇒ a kiadás a Windows **`IDiscRecorder2::EjectMedia()`**
COM-metódusa — ezért nincs hozzá nyom a Picasa binárisaiban. Linuxon a
megfelelője platform-szolgáltatás (`eject` / UDisks). Lap: 13.;
jegy-komment: **#2074**.

### [ui-audit-editor.md](ui-audit-editor.md) — nincs nyitott kérdés

⭐ **2026-09-04 (#2305) — a szerkesztő NAGYÍTÁS-HÁRMASA.** Az `editpanel/fit`
és az `editpanel/1to1` egy **összeragasztott kétszegmenses gombpár** az
`editbase` jobb alsó sarkában (`zoombuttcontainer`, `m_offsetRB`), gombonként
**37 × 22** (x 286…323 és 323…360, y 449…471), utánuk a nagyító (368…392) és a
csúszka (399…526). **A kattintás művelete kiolvasva:** `fit` → `0.0f`
(`0x005d5ccc`, `fldz`), `1to1` → **`0.5f`** (`0x005d5d45`, `0x00c7dafc`),
mindkettő a `0x005ee590` animált beállítóval. ⇒ **a szerkesztő
nagyítás-csúszkája normalizált értéket tárol: `0.0` = illesztés, `0.5` =
valódi méret (100 %)** — ezt a visszafelé irányú állapotválasztó
(`FUN_005d1c70`, 82 b) is ugyanezzel a két konstanssal dönti el.
⛔ **Az `editpanel/inbetweenzoom` SOSEM LÁTSZIK** (`m_hidden`, 2 × 2 képpont):
a rádiócsoport „egyik sem" tagja, **nem megépítendő vezérlő**. A hivatalos
magyar súgók: „Beillesztheti a fotót a megjelenítési területbe" /
„Fotó megjelenítése tényleges méretben" — a mi fordításunk mindkettőnél más.
Jegy: **#2305** (komment), a megvalósítás **ÚJ JEGY**.

⭐ **2026-09-04 (#2312) — a nagyítás-csúszka TELJES LEKÉPEZÉSE MEGVAN.**
A képletet a képelem elrendezője számolja (`FUN_00a5f500`, 3622 b, a
`+0x3a0` tulajdonságot 13 helyen olvassa); a hatványozó a `0x005568e0`
`float`-burkolón át a CRT **`pow`** (`0x00c0b410`, `fyl2x` a
`0x00c0b4ba`-nél), az alap mindig **2.0**. Töréspont **0.5**
(`0x00a601bc`): alatta **`skála = 1 + (2^(2v) − 1)·(r − 1)`**
(`0x00a601cf`), fölötte **`skála = r · 2^(4(v − 0.5))`** (`0x00a601fb`),
ahol a skála az **illesztett** mérethez viszonyul. ⇒ `v=0` → illesztés,
`v=0.5` → **100 %**, `v=1` → **400 %**, és a felső fél negyedenként
pontosan duplázódik. ⇒ **az illesztett méretnél kisebbre nem lehet
zoomolni**, és a **100 % mindig a csúszka felezőpontja**. Jegy: **#2312**
(lezárva), a megvalósítás: **#2311**.

⭐ **2026-09-03 — a szerkesztő MARADÉK három vezérlője.** Mindhárom
`m_hidden` alapállapotban, ezért ránézésre nem tűnnek fel. ⭐ **Ugyanaz a
funkció KÉT ALAKBAN:** a szöveg-overlay láthatósága a **menüben két külön
parancs** (`ID_PICTURE_SHOW_TEXT`/`…HIDE_TEXT`), a szerkesztő panelen viszont
**egyetlen jelölőnégyzet** (`editpanel/showtextcheckbox`,
`superbutton(buttcon_checkbox)`, az **1. fülön**, felirata **„Szöveg
megjelenítése"**) — aki csak a menü-specet olvassa, lemarad a
jelölőnégyzetről. ⛔ **NINCS hozzá `Preferences`-kulcs** (mérve, két
lekérdezési alakkal) ⇒ munkamenet-szintű nézetkapcsoló, nem tartós
beállítás. ⭐ **Az `editpanel/editslideshow` a már megépített `editcollage`
IKERPÁRJA:** mindkettő `root`-gyerek, mindkettő `m_hidden`, és **ugyanaz a
kezelő** (`0x00567a00`) — a szerkesztő felismeri, hogy a kép egy PROJEKT
kimenete, és felkínálja a forrás újranyitását. Nálunk a **kollázs-ág megvan**
(#1002), a **mozgófilm-ág nincs** ⇒ **#2114**. Végül: az
`editpanel/edithelpbutton` **ikonja ki van kommentezva** — ugyanaz a
„lecsupaszított súgógomb" minta, mint a `printpanel/phelpbutton`-nál ⇒ nem
kell megépíteni. ⇒ **Az `editpanel` feltáratlan listája ÜRES: 3 → 0**
(globálisan 103 → **100**). Komment: **#425**, **#1002**.

⭐ **2026-09-03 — a KETTŐS NÉZET (2-up) teljes vezérlőkészlete.** A **#434** a
*fogalmat* rögzítette (három üzemmód, `TwoUp*` kulcsok), de **egyetlen
elemnevet és címet sem** tartalmazott. Most megvan: a három üzemmód **egyetlen
háromszegmenses kapcsoló** (`only_1up` **bal** · `ab_2up` **közép** · `aa_2up`
**jobb**, a respack `buttcon_LS/MS/RS` rajzaiból), a kölcsönös kizárás
**`Property uptarget`**-tel megy — mindegyik **név szerint felengedi a másik
kettőt**, ezért az aktív gombra kattintva **nem tűnik el minden pipa** *(ez a
mi rádió-csapdánk ellenszere)*; az alapértelmezett a `only_1up`
(**`setpressed 1`**, `editpanel.tre:1196`). Két segédgomb **alapból rejtett**
(`swap_2up_focus` = „Fókusz váltása a képek között", `swap_2up_layout` =
„Váltás a vízszintes és a függőleges elrendezés között"), ahogy az
`editpanel/weblink` is. ⭐ **A szerkesztési ütközés párbeszéde teljes
szöveggel** (`CThumbUI::Confirm2up*`, `0x0056aad0`): **„Szerkesztett
változatok kiválasztása"** / „A képnek két szerkesztett változata van.
Melyiket szeretné megtartani?" — és a válaszgombok **NEM „A/B", hanem
HELYZETEK**, **négy** darab (`Bal` · `Jobb` · `Fent` · `Lent`), mert a
párbeszéd az aktuális elrendezéshez igazodik. ⛔ **A `wipe_2up_toggle` a
kódban NÉV, a felületen NINCS** — sem `.tre`, sem respack-réteg. ⇒ Az
`editpanel` feltáratlan listája **11 → 3** (globálisan 111 → **103**).
Komment: **#434**.

### [picasa-nyomtatas.md](picasa-nyomtatas.md) — nincs nyitott kérdés

⭐ **2026-09-03 — HÁROM TÉVES ÁLLÍTÁS JAVÍTVA, és a panel alsó gombjai
feltárva.** ⛔ A lap azt írta, hogy a nyomtatási beállítások párbeszéd
**„21 felirat, mind angolul, nem került át a fordítható erőforrásokba"** —
**mindhárom állítás téves**: **26 bejegyzés** (23 felirat + 3 buboréksúgó),
**mind magyarul is megvan**, a kicsomagolt `i18n\printoptionstext.xml`-ben
(`referencia/i18n-hu/`, 4 202 bájt). A teljes magyar tábla most a lapon áll.
⚠️ **Két hivatalos buboréksúgó HIBÁS fordítás:** az `apply` és az `ok` súgója
„a Google Fotókra" alkalmazásról beszél, holott a párbeszéd a nyomat
szegélyét és feliratát állítja. ⛔ Második helyesbítés: a `phelpbutton`
**nincs** „teljesen kikommentezva" — csak az **ikonja, felirata, színe és
horgonya**; maga a gomb él, `vbutton`-ként (rajz nélküli találati terület).
**Új mérés:** a `psetupbutton` a **Windows nyomtató-tulajdonságok**
párbeszédét nyitja (`0x00861750`: `OpenPrinterA` + kétszer
`DocumentPropertiesA`); a `froogle` **megerősítést kér**, majd a
**`https://uploader.picasa.com/froogle.php?q=%s`** címet nyitja meg a
**nyomtató nevével** — adatvédelmi szempontból nem semleges, és a
szolgáltatás megszűnt ⇒ **hatókörön kívül**. Végül: **két** minőségszöveg-
család van (`CPrintDlg::*qual` és `ThumbUIPrint::Review*`), és a magyar
`PrintCount` **megcseréli a pozicionális argumentumokat** (`%2$d / %1$d`).
⇒ **A `printpanel` ezzel teljesen feltárt: feltáratlan 6 → 0**
(globálisan 122 → 116). Komment: **#1780**, **#446**; új jegy: **#2103**.

⭐ **2026-09-03 (11. szakasz) — a panel HÁROM JELÖLŐNÉGYZETE, és egy REJTETT
MELLÉKHATÁS.** A 3./10. szakasz a *belső* beállításokat írta le; a felhasználó
viszont három négyzetet lát: **„Diavetítéssel együtt"** (`publish/optionbox1` →
`Preferences\CDSlideshow`, alapérték **1**), **„Adathordozó törlése"**
(`optionbox2`), **„A Picasával együtt"** (`optionbox3` →
`Preferences\CDSlideshowInclSetup`, alapérték **1**). ⭐ **A „Diavetítéssel
együtt" NEM csak a vetítőt teszi a lemezre:** ugyanaz az érték állítja be az
`option_convertnonjpeg` kulcsot (`0x0066f6f3`) — vagyis **bekapcsolva a
nem-JPEG képek JPEG-be konvertálódnak**, és ezt a felület sehol nem jelzi.
A mentés-ágon nincs ilyen kapcsoló: a visszaállító **mindig** rákerül a
lemezre (`0x0066f57d`). A `_go`/`_eject` **nem külön gomb**, hanem
**mód-függő rés** (`0x0066bf90` → `[obj+0x2a0]`, `[obj+0x2a4]`). A készlet
alapértelmezett neve **„Saját mentési készlet"** (`il_BurnPanel::bksetname`).
A Kiadás gomb tényleges művelete a **`CDVDR.yti` COM-oldalán** van — ugyanaz a
tétel, mint a **#2074**. ⇒ **A `publish` panel ezzel TELJESEN feltárt:
feltáratlan 5 → 0**, lekutatva 30/30. Komment: **#32**, **#440**.

⭐ **2026-09-03 (9–10. szakasz) — a BELÉPÉSI PONTOK, és egy BLOKKOLT tétel
LEZÁRVA.** A lap eddig azt írta le, mi kerül a lemezre; azt nem, **honnan
indul**. Öt belépési pont: `eMenuCreate::ID_BURNCD` (a **Létrehozás** menüben —
a lap korábban `eMenuTools`-t írt, **helyesbítve**), a `thumbui/cdmode`
üzemmód-gomb (magyarul **„Ajándék CD"**, buboréksúgó: *„CD/DVD létrehozása
beépített diavetítéssel…"*), a `publish/presentcd_go` (**„Lemezre írás"**), és
**kettő, ami a `.tre`-ben KI VAN KOMMENTEZVE**: `headerpanel/create_cd` és
`faceheaderpanel/create_cd` — a bináris ismeri a nevüket, a felületleíró
kikapcsolja őket. ⭐ **A 7. mérleg BLOKKOLT tétele („a 16 beállítás
értékkészlete") LEZÁRULT dekompiláció nélkül:** a `0x0068eea0` a **második**
függvény (a blokkolás indoka „egyetlen olvasó" volt), és a 16 kulcsot **16
egymás utáni dwordre** képezi (`+0x454`…`+0x490`, hézag nélkül) — ez egyben
igazolja a lista teljességét, és megadja a **hiányzó tizenhatodik** kulcsot
(`option_copysrctotempdest`). A `0x0066f470` húsz beállító híváshelye
kiolvasva, köztük **`option_jpegquality = 85`** — ugyanaz, amit mi is adunk
(`exporter.py:62`), **egyezik**. **Megdőlt:** „a beállításokat a `Preferences`
tárolja" (nulla `Preferences\option…` sztring) és „az Ajándék CD nem
fényképexport" (`picasa-menu-parancsok-viselkedes.md` `ID_BURNCD`, javítva).
Komment: **#32**, új jegy: **#2095**.

⭐ **2026-09-02:** az Ajándék-CD kimenete feltárva — a lemez **önjáró**
(`PicasaCD.exe` + `Picasa CD Slideshow.app` + `PicasaRestore.exe` +
`Picasa Restore.app` + `setup.exe` + `Download Picasa.url` + generált
`autorun.inf`), a forrásmappa **élő mintaként megvan** a repóban, és a
lemez mappanevei **honosítottak**. Nálunk a menüpont **halott helyőrző**
(`PicasaMenuBar.qml:1329`). Jegy-komment: **#32**, **#440**.

1. ~~Mi a 16 kimeneti beállítás ÉRTÉKKÉSZLETE?~~ **LEZÁRVA (2026-09-03)** —
   dekompiláció nélkül: a `0x0068eea0` a **második** függvény (a blokkolás
   indoka „egyetlen olvasó" volt), és 16 egymás utáni dwordre képezi a
   kulcsokat; a `0x0066f470` húsz beállító híváshelye kiolvasva. Lap:
   `ajandek-cd-kimenet.md` **10.**
2. ~~Melyik ÁG melyik üzemmódhoz tartozik?~~ **LEZÁRVA (2026-09-04, #2095)** —
   szintén dekompiláció nélkül. A `+0x13e`/`+0x13f` mód-bájtnak a teljes
   binárisban **egyetlen írója** van (a panel konstruktora, `0x0066bf90`), és
   **ugyanaz a függvény** választja belőlük a `publish/presentcd_go` /
   `backup_go` / `replicate_go` vezérlőnevet — a név megnevezi az üzemmódot:
   `0/–` = **Ajándék-CD**, `≠0/0` = **biztonsági mentés lemezre**,
   `≠0/≠0` = **replikáció (feltöltés)**. A belépési elemnevek
   (`thumbui/cdmode` · `backup` · `replicate`) és az ágak tartalma
   (`option_isupload`, a `PicasaRestore` másolása) függetlenül ugyanezt adja.
   Lap: `ajandek-cd-kimenet.md` **12.**

### [pmp-database.md](pmp-database.md) — 1 BLOKKOLT tétel (2026-09-05)

⭐ **2026-09-05 (8.4) — MEGERŐSÍTVE: a maradék 4042 nem egyező sor oka a fájlok ÁTHELYEZÉSE.** Az előző kör „erős, nem megerősített" magyarázata **bizonyítva**. A módszer: ha a fájl áthelyeződött, a **neve megmarad**, csak a szülő könyvtára más — ezért a katalógus **7669 könyvtár-bejegyzésének** mindegyikére kiszámoltam az útvonal-előtag hash-ét, és soronként megkerestem, melyik előtaggal folytatva adja a fájl neve épp a **tárolt** ellenőrzőösszeget. **Eredmény: 3976 / 4042 (98,4 %) megmagyarázva** egy másik, ma is létező könyvtárral; nem magyarázva 66; és mindezt **mindössze 29** „régi" szülő fedi le (egyetlenre 1081 fájl). ⛳ **Kontroll:** egy ismerten EGYEZŐ sorra a kereső a **saját mai szülőjét** találja meg. ⛳ **Véletlen kizárva:** 7669 jelölt és 1/1 000 231 esély mellett ~31 véletlen találat volna várható, nem 3976 — és a véletlen 7669 könyvtár közt szórna szét, nem koncentrálódna 29-re. ⇒ **Az ellenőrzőösszeg eltérése — ha az idő- és mérettagok stimmelnek — azt jelenti, hogy a fájl ÁTHELYEZŐDÖTT**, és a régi hely visszakereshető. Ez a #2435 importőrének **mozgás-felismerő** képességet ad; oda kommentelve.

⭐⭐ **2026-09-05 (8.4 + 8.8 + 8.10) — LEZÁRVA: a „615 nem egyező sor" oka az ELŐJELES BÁJT volt, és a képlet-leírásunk HIBÁS VOLT.** A sztring-hash ciklusa a bájtot **`movsx`-szel, ELŐJELESEN** tölti be (`0x006b9a3f` és `0x006b9a47` a 8.10-es, `0x006b98da` és `0x006b98e2` a 8.8-as hashben) — a mi leírásunk előjel nélkül adta meg. ASCII néven a kettő azonos, nem-ASCII néven teljesen eltér. **A szétválás kivétel nélküli volt:** a 2776 vizsgált sorból a 2161 egyező **mind** tiszta ASCII útvonalú, a 615 nem egyező **mind** tartalmaz nem-ASCII bájtot. **Előjelesen, UTF-8 úton újramérve három katalóguson:** „arcok" **2776/2776 (100 %)**, nagy **129 047/133 089 (96,96 %)**, „másolat" **2354/2354 (100 %)** — a korábbi 2161 · 48 605 · 1932 pontosan reprodukálódik előjel nélkül, tehát ugyanazt a halmazt mérjük. ⛔ **A 2. mód versengő magyarázata MÉRVE ELVETVE:** 0/615 és 0/4042. **A nagy katalógus maradék 4042 sorára:** `cs ^ (idő+méret tagok)` **4041 esetben** a modulus (1 000 231) alá esik ⇒ az időbélyeg és a méret HELYES, csak az útvonal-hash tér el ⇒ **átnevezett/áthelyezett fájl** (erős, nem megerősített); 3979 közülük tiszta ASCII, tehát az előjel-hibával már nem magyarázható. ⚠️ **Aki a régi spec szerint valósította volna meg, 36 %-os találati arányt kapott volna** — a helyesbítés a **#2435**-be kommentelve.

⭐ **2026-09-05 (13. szakasz) — az ellenőrzőösszeg-mód BELÉPÉSI PONTJA egyetlen, és `CThumbDB`-é.** A munkasor tétele („mind a 29 jelölt `CThumbDB`-e?") **LEZÁRVA — igen**, de nem a jelöltlistán át: a lánc **egyedisége** adja a választ. A módválasztó `0x004e3ab0`-nak a **teljes binárisban egyetlen** hívója van (`0x0042a832`, a `0x0042a800` törzsében); a `0x0042a800`-nak **nulla** közvetlen hívója, és a címe **egyetlen helyen** szerepel a fájlban: a `CThumbDB` vtáblájának 34. résében (`0x00c82184`, vtábla `0x00c820fc`, objektum-eltolás 84). ⛳ **Kontroll-pásztázás vtábla-fej szabály NÉLKÜL: 2233 lehetséges 34. rés-cél, ebből `ret 0x18` (hat argumentum) pontosan EGY** — a `0x0042a800`; a 13 indexeletlen találat egyike sem függvénykezdet (kézzel ellenőrizve). ⇒ bármely hatargumentumú, 34. résen át menő hívás csak ide mutathat. ⛔ **HELYESBÍTÉS:** a 121. kör „29 jelölt" száma **nem reprodukálható** — a push-számlálás szabályfüggő (17 / 21 / 27), mert kilenc találatnál a „hat push" a **függvény prológusa** volt, nem argumentum. A szám tehát nem bizonyíték; a 121. kör KÖVETKEZTETÉSE viszont áll, mert az a stabil literál-argumentumokon nyugszik. **Nálunk (mérve):** a `checksum` mezőt beolvassuk (`pmpimport/thumbindex.py:169`), de egyik mód képlete sincs megvalósítva, és sehol nem ellenőrizzük → **#2435**.

⭐ **2026-09-03 (8. szakasz) — a `thumbindex.db` és a `*_index.db` BÁJTFORMÁTUMA megfejtve.** A `thumbindex.db`: `uint32` magic `0x40466666` + `uint32` rekordszám + rekordonként **ASCIIZ útvonal + 30 bájtos farok** (két `FILETIME`, méret, típus, `dirty`, `valid`, kiegészítő). ⭐ **A hét mező PONTOSAN a 2. szakasz diagnosztikai CSV-fejléce** — a bináris rekord és a `WriteDirscannerCSV` kimenete ugyanaz a szerkezet. A három `*_index.db`: **float verzió (1.6) + NÉGY párhuzamos `uint32`-tömb** (üres · **Checksum** · **Offset** · **Size**) — ⚠️ **ez a lap 8.2 szakaszának HELYESBÍTETT modellje**; a korábban itt állt „20 bájt fejléc + 12 bájt/slot (`uint64 q` + `uint32 u`)" leírás **MEGDŐLT** (a két modell bitre ugyanazt a fájlméretet adja, ezért a méret-ellenőrzés nem szűrte ki). Az indexbejegyzés 2026-09-05-ig hordozta az elavult alakot. **Ellenőrizve:** 140 758 rekord 0 bájt maradékkal; 1 689 080 = 20 + 140 755 × 12 és 3 287 072 = 20 + 273 921 × 12 pontosan. ⭐ **2026-09-04: a kulcs (a Picasa szóhasználatában `Checksum`) KÉPLETE MEGVAN** és mért (8.10): `(JS_hash(teljes_út) mod 1 000 231) ^ rol(idő_lo,13) ^ rol(idő_hi,17) ^ rol(méret,18)`, ahol az idő a **második** FILETIME; három katalóguson 48 605 + 2 161 + 1 932 pontos 32 bites egyezés. ⚠️ **A korábban itt felsorolt kizárások (10 mező-összevetés, 24 hash-kombináció) a MEGDŐLT szerkezet-modellre épültek — ne tekintsd őket érvényesnek** (a lap 8.6 visszavonta őket). ⭐ **2026-09-05: KÉT ellenőrzőösszeg-mód van.** A számoló `FUN_006b99f0` egyetlen verem-paramétere kapcsoló; a **2. módban** (`0x006b9b26`) **nincs útvonal és nincs méret**: `rol(q_lo,13) ^ rol(q_hi,17)`, ahol `q = (FILETIME + 5 000 000) / 10 000 000` — vagyis **egész másodpercre kerekített** idő. A hat hívóból öt fixen `1`-et ad, egy (`0x004e3c13`) futásidejűt, ami a `CThumbDB` **34. réséből** ered. Jegyek: **#2195** (olvasó, kommentelve), **#1** (db3-import gyűjtő).

⭐ **2026-09-05 (120. kör) — MIKOR jut a 2. mód: LEZÁRVA.** Az egyetlen
futásidejű hívóhely elágazása szerint **három feltétel bármelyike** a 2.
módot választja: a hívó kifejezetten `0`-t ad (`0x004e3bc2`), **vagy** a
rekord `Type`-ja `0` (`0x004e3bcb`), **vagy** nincs szülője
(`0x004e3bd7`). Mivel a `+26 == 0xFFFFFFFF` szentinel pontosan a
`Type ∈ {0,1,5}` halmazon áll (8.1), **a könyvtárak és az üres slotok
mindig a 2. módot kapják**. ⭐ **Az 1. mód KÉT sztringet hasheli** — a
szülő nevét és a sajátot, összefűzés nélkül, ugyanabba az akkumulátorba
(`0x004e3bdd`–`0x004e3c0e`); hibás szülőindexnél a `[objektum+0x550]`
tartalékra esik, ugyanarra, mint a névfeloldás. ⇒ Aki kompatibilis
gyorsítótárat ír, a **sorrendet** kell eltalálnia.

⭐ **2026-09-05 (121. kör) — MELYIK HÍVÓ ad 0-t: LEZÁRVA.** A metódus
`ret 0x18`-ja (`0x0042a844`) hat verem-argumentumot ír elő, a mód a 2.
(a hívás előtti 5. push). Erre szűrve a 93 jelöltből **29** marad:
**10 ad literál `0`-t** (`0x004245eb` · `0x0042f6c0` · `0x0042f710` ·
`0x0043bc8e` · `0x0045a966` · `0x00481993` · `0x0064bea8` · `0x006a969f` ·
`0x006ac079` · `0x00793740`), 5 literál `1`-et, 14 futásidejűt. ⭐ **Két
0-s hívó teljesen elolvasva** (`FUN_0042f6a0`, 74 b; `FUN_00793720`, 70 b):
mindkettő `CThumbDB` **másodlagos felület** (`[esi-4]` vtábla, `lea ecx,[esi-4]`),
és mindkettő **ÜRES sztringgel** hív (`0x00c7f979`, kiolvasva: `""`). ⇒ **A
2. mód akkor jár, ha a hívónak nincs második sztringje** — az 1. mód
ugyanis két sztringet hajt a hash-be, és üressel az értelmetlen volna.

⭐ **Ezzel a 615-ös tétel magyarázata ÚJRA KISZÉLESEDETT** (a 120. kör
szűkítése után): a 2. mód **nem** korlátozódik a szülő nélküli
bejegyzésekre, mert tíz hívóhely kifejezetten kéri. ⇒ A döntő lépés megint
a legolcsóbb: a `Checksum₂` kiszámolása a 615 sorra.

1. **Mind a 29 jelölt a `CThumbDB` 34. rése?** Kettő megerősítve; a
   többinél a hívási minta azonos (`…, m, 1, 1, m, …`), de nincs külön
   igazolva, hogy a fogadó `CThumbDB`. **Megszerzés:** hívóhelyenként a
   fogadó típusának ellenőrzése (a vtábla honnan jön), vagy a lap 11.
   szakaszának felület-térképe.
2. **A 615 nem egyező sor oka** — „elavult ellenőrzőösszeg" **vagy** „a 2.
   módban íródott". ⚠️ **2026-09-05-i szűkítés:** a 615 sor **mind
   fájl-típusú**, tehát van szülőjük ⇒ a 2. mód náluk csak úgy jöhetett
   szóba, ha a hívó kifejezetten `0`-t adott — és a 121. kör szerint **tíz
   hívóhely pontosan ezt teszi**. **Megszerzés:** a `Checksum₂`
   újraszámolása a 615 sorra (olcsó, új adatgyűjtés nélkül).

⭐ **2026-09-02 — SAJÁT HELYESBÍTÉS a bélyegkép-gyorstár kulcsvektorán:** a lap
korábbi következtetése („a kulcs tárankénti, nem globális fotó-azonosító")
**érvénytelen** — két **eltérő hosszú** vektort vetett össze rés szerint
(`thumbs` 140 755 vs. `previews` 273 921). Azonos résterű tárak közt mérve a
kulcsvektor **bitre azonos**: `thumbs` ≡ `thumbs2` (140 755/140 755 és
3 338/3 338), `previews` ≡ `bigthumbs` (273 921/273 921) — noha a tárolt blob
más (144 px vs. 72 px JPEG). ⇒ **a kulcs nem lehet a blob ellenőrzőösszege**,
hanem a forrásfotóra vonatkozó, sorindexhez kötött bélyeg.
Melléklelet: az „elavult sorok maradnak a `previews`/`bigthumbs` vektorban"
eddigi *következtetés* **MÉRÉSSÉ** vált (az `arcok` készletben 216, illetve 217
élő bejegyzés nem valódi JPEG-re mutat, ebből 185+185 a katalóguson túli
sloton; a tulajdonos nagy mentésében **0 anomália** mind a négy tárban) ⇒ a
beolvasónak a `FFD8`/`FFD9` tartalom-ellenőrzés **kötelező**. Plusz a tároló
bináris oldala: `CBlockFile` (`.\thumblab\CBlockFile.cpp`), a
`Preferences ▸ Write blockfile CSV` kapuval kapuzott `Size,Offset,Checksum`
hibakereső dump (`0x006b5e00`) és a `Restore` helyreállító ág.
Jegy-komment: **#1446**.

1. **Hogyan képződik az `*_index.db` kulcsvektora?** Réshez (sorindexhez)
   kötött bélyeg, amivel a Picasa eldönti, hogy a gyorstárazott blob még a mai
   forráshoz tartozik-e. **Hét jelölt kizárva** (`imagedata_originfast`,
   `originslow`, `onlinechecksum`, `long`, `rotate`, `filetype`, `tagdate` —
   alsó és felső 32 biten is, 0/3 204 egyezés). **Megszerzés:** a `CBlockFile`
   írási útjának (`0x006b61e0` környéke) célzott dekompilációja, vagy a kulcs
   változásának megfigyelése egy fájl módosítása után élő Picasában.
   Lap: `pmp-database.md`; jegy **#1446**.

### [picasa-email-kuldes.md](picasa-email-kuldes.md) — 0 nyílt · 3 lezárva · 0 blokkolt (frissítve: 2026-09-05)

⭐ **2026-09-05 (3/b szakasz) — a Beállítások E-mail fülének csúszkája: NYOLC fokozat, MÉRVE.** `options/bind47.list` = **`160|320|480|640|800|1024|1200|1600`**, a felirat `options/bind47.format` = `%s képpont` (`referencia/i18n-hu/options.xml`). ⛔ **HELYESBÍTÉS:** a lap korábban azt állította, hogy a Beállítások natív Win32 lap, ezért a feliratai nincsenek a stringres anyagban — **téves**; a fül teljes egészében stringres-panel, és a 17 eleme végig megvolt a saját kutatási anyagunkban. A korábbi „a 480 az export-lista **második** eleme" kapcsolat **elvetve**: az export hét értéket ad (`export/bind17.list`), az E-mail nyolcat (a **160**-nal), tehát a 480 a **harmadik**. A `bind51` **nem** második csúszka, hanem az „Egyedülálló képek mérete" első gombjának feliratkötése. ⛔ **Negatív leletek:** (1) a `320…1600` sorozat sem `int32`-ként, sem `int16`-ként **nem szerepel** a binárisban — a listák szövegként élnek; (2) a `%d pixels (for e-mail)` sablonok megvannak (RT_STRING 9. blokk, adat-RVA `0x00a03458`: **140**/**141**/**142**), de a `LoadStringW` **nincs importálva**, a `LoadStringA` IAT-rekeszére (`0x009ae710`) pedig **nulla hivatkozás** van a fájlban ⇒ nem ezek a fül feliratai; (3) módszertani helyesbítés: a `push 0x8c`…`0x8f` négyes (`0x0047820e`–`0x0047829c`) **hasítótáblás keresés kulcsa** (`0x0049c900`), nem sztringazonosító. **Nálunk (mérve):** a nyolc fokozat és a 480 **már helyes** (`mailer/command.py:22`), de az `OptionsTabEmail.qml`-ből hiányzik a harmadik levelezőgomb (`radio42`, „A Google Fiók használata") és más a csoportcím → **#2432**.

⭐ **2026-09-03 (6. szakasz) — MEGVAN a beállítások TÁROLÓJA, és nem csak az e-mailé.** A Picasa minden beállítása a **Windows-registryben** él: `HKEY_CURRENT_USER\SOFTWARE\Google\Picasa\Picasa2\Preferences\<kulcs>`. A teljes útvonal szó szerint a binárisban (`0x00c8ae5c`), és három, egy blokkban beállított darabból áll össze (`SOFTWARE\Google\Picasa\` `0x00c7f0c4` + `Picasa2` `0x00c7edd0` + `Preferences` `0x00c7eafc`); a `HKEY_CURRENT_USER` konstans két helyen kiolvasva (`0x00407a3b`, `0x00541bd8`). ⛔ **NEM fájlban van:** a `research/testdata/` valódi Picasa-adatmappája egyetlen beállításfájlt sem tartalmaz. **A hozzáférés-készlet:** `0x00407a20` (objektum + alapérték), `0x00408060` (kulcs-megnyitás), `0x004019b0` (olvasás), `0x00401900` (írás), `0x004018e0` (burkoló). **Hét alszekció** azonosítva: `HotFolders`, `Plugins\`, `Buttons\Exclude`, `Buttons\UserConfig`, `AspectRatios`, `PrinterData`, `RSSDownload`. **A `choose_mail` viselkedése:** a kapu (`0x007420f0`) alapértékei `EmailPrepType`=**3**, `DoNotPromptForEmailPref`=**0** ⇒ **friss telepítésen az első küldéskor a párbeszéd MEGJELENIK**; az OK-ág (`0x0084fb10`) `mymail`→**3**, `gsender`→**5**; és a mód **csak akkor marad meg**, ha a jelölőnégyzet be van pipálva (`0x0084f6b0`: a jelölőnégyzet állapotát MINDIG kiírja, az `EmailPrepType`-ot csak pipálva). **Nálunk (mérve):** `QSettings`, a két kulcs egybeolvasztva, és az alapérték **fordított** (`email_controller.py:158` — `True` = ne kérdezz) ⇒ a választó párbeszéd friss profilon elérhetetlen. Jegy: **#2184**.

⭐ **2026-09-02 — az e-mail méret-beállítás SZEMANTIKÁJA mérve:** az
`EmailExportSize` **közvetlen képpont-érték** (a hosszabb oldal), **nem**
listaindex, és az alapértéke **480** — három független helyen kiolvasva
(`0x006e1756`, `0x006e3f2b`, `0x00743094`). A `0` jelentése **eredeti méret**
(`option_useorig`); nem nulla értéknél az `option_imagesizelimit` **és** az
`option_estimate` is megkapja. Az `EmailSinglePicture` **kapcsoló**, nem méret:
egy kép + bekapcsolt állapot ⇒ a méret 0 lesz. Az `EmailMovie` az
`option_preservemovies`-t állítja; a mellékletek a `temp\email\` mappába
kerülnek. **Nálunk ez szerkezetileg más** (két ötfokozatú index-csúszka,
kitalált értékekkel, és a mért 480 elő sem fordul a listánkban) → **#2020**.

1. **Mik a Beállítások ▸ E-mail lap csúszkájának LÉPÉSEI?** Az olcsó lánc
   kimerült: a lap natív Win32 erőforrás, ezért sem a `.tre`, sem a
   `respack.yt`, sem a `stringres` nem tartalmazza; a `%d pixels (for e-mail)`
   sablon megvan a PE sztringtáblájában, de a számot futásidőben kapja, és
   statikus méret-tömb nincs a binárisban (végigkeresve). **Megszerzés:**
   egyetlen képernyőkép a futó Picasa `Eszközök ▸ Beállítások ▸ E-mail`
   lapjáról. Jegy: **#2020** (`blocked` + `felhasználóra-vár`).

### [picasa-beepitett-webszerver.md](picasa-beepitett-webszerver.md) — nincs nyitott kérdés (ÚJ lap, 2026-09-02)

⭐ **2026-09-02 — a Picasa 3 BEÉPÍTETT HTTP/WebDAV-kiszolgálója feltárva.** Az
eredeti **hallgatózó kiszolgálót** futtat: HTTP Basic hitelesítés
(`WWW-Authenticate: Basic realm="Picasa"`, jelszó a `LANPassword`-ből, a
felhasználónév fixen `picasaserver`), WebDAV (`OPTIONS`/`PROPFIND`, 13 `D:*`
elem, a megosztás `\\localhost\picasa`, a DAV-ág **80-as portot** igényel),
**14 végpont** (`/albumlist` … `/dbdebug`) plusz `/repost` és `/upload`,
kép-végpontok (`image/`, `thumb/`, `sthumb/`, `original/`), két hibakereső lap
(a `/dbdebug` **adatbázis-böngésző**, a `/uidebug` rajzolási időmérésekkel), és
egy LAN-hirdetés, ami **gépnevet és felhasználónevet** tesz a hálózatra
(`0x00937800`). Külön beérkező felület a **`picasa://` URL-séma**, amelynek egy
ága **külső URL-ről tölt be bővítményt**. **Nálunk mindebből semmi nincs
(mérve), és a javaslat: ne is legyen** → **#2023** (döntés-jegy, őr-teszttel).
Melléklelet: a `/filesigs` `text/plain` mezőlistája **független** megerősítése
a fotó-rekordunknak — és a **`flip` mező negatív eredmény**
(`imagedata_flipped.pmp`: 3 011/3 011 üres; a 859 fájlos ini-korpuszban 0 db
`flip=` sor).

### [binaris-regeszet-modszertan.md](binaris-regeszet-modszertan.md) — nincs nyitott kérdés (ÚJ szakasz, 2026-09-03)

⭐ **2026-09-03 (22.6) — a lefedettségi axis mint KUTATÁSI forrás KIMERÜLT.** A `feltáratlan` lista mind a **69** tételét megvizsgálva: **60 (87%) bizonyíthatóan már dokumentált** (5-nek a minősített neve, 55-nek a levélneve + a panel neve szerepel a panel SAJÁT spec-lapján — pl. mind a 10 `compose_mail` és 9 `choose_mail` a `picasa-email-kuldes.md`-en). A **9 valóban nyitottból** 7 **hatókörön kívül** (az `activity/activitybutton` a **Feltöltéskezelőt** nyitja — `0x007d3f90`: „Upload Manager", `%.2f KBps` —, ami Picasa Web Albums-gépezet), 1 a testvér-vezérlő már mért párja, és **1-et ez a kör tárt fel** (`outputlayout/morebutton`, #2191). ⛔ **Negatív:** a `filesafe.ioq` és az `albumsafe.ioq` a **teljes binárisban sehol** nem szerepel a store-inicializálón kívül, és élő mintánkban mindhárom `.ioq` **0 bájtos** — nincs miből visszafejteni. ⇒ **A következő kutatói körök NE az axisból válasszanak**, amíg a #2182 őre meg nem épül: az axis „feltáratlan" oszlopa ma a **dokumentáltság** hiányát méri, nem a tudásét.

⭐ **2026-09-03 (22.5) — a saját 22.4-es szabályunk megsértése TIZENKÉT elembe került.** A lefedettségi mérő `feltáratlan` (kutatói kört igénylő) listájának mind a **100** tételét megvizsgálva: **19**-nek a TELJES `panel/elem` neve szerepel egy kézzel írt spec-lapon, és ebből **18 némán elveszett** — mind a **18/18** azért, mert a szakaszában nincs **horgony** (`0x…` cím vagy `fájl:sor`), és a `lekutatott_elemek()` az ilyen szakaszt teljesen átugorja. A 18-ból **12 valódi dokumentáció** volt: a `picasa-nyomtatas.md` printoptions-elemtáblája, ami csak egy **sorszám nélküli `.xml`-re** hivatkozott. Egyetlen bekezdésnyi javítás után, mérve: **feltáratlan 100 → 88, lekutatva 154 → 166.** A maradék 6 NEM dokumentáció (kurzor-tulajdonság felsorolások, illetve egy hiba-példa) — ezért mondja ki a szakasz, hogy **a puszta névelőfordulás nem lefedettség**, a találati SORT is meg kell nézni. ⛔ **Két saját, korábbi állítás MEGDŐLT ugyanebben a körben:** (1) „a mérő kimenete ingadozik" — nem, két futás **bájtra azonos**, a commitolt lap csak **elavult** volt; (2) „a lista 68%-a hamis" — az első, hibás mérésem száma; a helyes **12/100**. Az őr, ami ezt a jövőben megfogná, **nincs meg** — jegy: **#2182**.

⭐ **2026-09-03 (22. szakasz) — MEKKORA a 18. szakasz hibája? Lemérve.** A 18.
kimondta a szabályt (*elemnév és cím egy szakaszban*), de senki nem mérte, hány
elemet érint — pedig a szám egy KÖZÖLT mutatóban ül. A 168 „feltáratlan" elemből
**50 (30%) teljes néven szerepel** egy kézzel írt spec-lapon; 41 dedikált lapon
is. **Három mechanizmus rejti el a bizonyítékot:** (1) nincs horgony a
szakaszban (a `biztonsagi-mentes.md` 10.3 tizenkét `publish/…` feliratát a
`panel-feliratok-hu.tsv`-sorszám igazolja, ami nem illeszkedik a mintára);
(2) a lap a **levélnevet** használja (a `konyvtar-ablak-meretek.md` 4. szakasza
mind a 18 lebegő gomb geometriáját megadta `thumbui/` előtag nélkül —
**egyetlen sort sem** talált a detektor); (3) **kézi `hianyzik` felülbírálás
árnyékolja** a gépi `lekutatva`-t (hat elem; kettőnek a saját megjegyzése
mondta ki, hogy „De FELTÁRVA"). ⛔ **Egy aggály ELVETVE:** a részsztringes
keresés a mai 88 `lekutatva`-ból **nullát** igazol hamisan (szóhatáros
újrafuttatás: 88/88). **Javítva ebben a körben:** 37 felülbírálás + a
`konyvtar-ablak-meretek.md` 4. szakasza teljes nevekre —
**feltáratlan 164 → 128** (ugyanazzal a QML-fával mérve). Jegy: **#1878**,
maradék: **#2093**.

⭐ **2026-09-03 (21. szakasz) — a Picasa UTF-8 rétege: a TELJES futásidejű
thunk-tábla.** A 20. szakasz receptjét az egész `.text`-en végigfuttatva
kiderült, hogy nem elszigetelt trükk: a Picasa **68 ANSI Win32 API-t** vezet át
globális mutatókon (`0x00d694bc`–`0x00d695c8`), és induláskor a `GetVersion`
magas bitje szerint tölti fel őket — 9x-en a nyers `…A` importtal, NT-n **saját
UTF-8 burkolóval** (`MultiByteToWideChar(CP_UTF8= 65001)` → `…W`). A lap most a
**teljes 68 soros táblát** tartalmazza (mutató · DLL · `…A` név · IAT-rekesz ·
burkoló), a szkript pedig a privát repóban él (`eszkozok/rt_thunks.py`).
**Két következmény:** (1) minden `call dword ptr [0x00d69…]` egy lépésben névre
hozható — a „nem oldható fel, futásidejű mutató" indoklás ma **hiba**, nem
korlát; (2) a Picasa belső sztringjei NT alatt **UTF-8-asak**, ami a
`.picasa.ini`, a `files.txt` és a `watchedfolders.txt` kódolására nézve
**normatív**.

⭐ **2026-09-02 — egy ELVETETT mérőszám, kontrollal megbuktatva (19. szakasz).**
A kézenfekvő ötlet — „ha egy felületi elem neve nincs benne a `Picasa3.exe`-ben,
akkor halott" — **használhatatlan**: a 2 020 elemű leltárból **935 (46,3%)** és
a lefedettségi hiánylista 363 tételéből **78 (21,5%)** esne bele, köztük a
`thumbui/loupehit` (a rács-nagyító, amit a #1911/#1951 épp megépített) és a
`printpanel/printsizes`. Két megnevezett hamis-pozitív osztály: a **dinamikusan
összerakott név** (`quickcontainer%d`, `palette_%d`, `tabpanel%d`, `%s_label` —
a formátumsztringek mérve megvannak) és a **szerkezeti gyerek** (`-label`,
`_icon`, `_group`, `_well`). A helyükre egy **négyfeltételes** szabály lépett
(`m_hidden` + nulla névtalálat + nincs névelőállító sablon + a felirat sincs
sehol); ezt a 2 020 elemből **három** állja ki: a `thumbui/lightbox_esolo_button`
(„Search All"), a `thumbui/lightbox_esolo_text` („No results found in this
album") és a közös szülőjük, a `thumbui/albumsback` — egy **album-szűkített
keresés üres állapota**, amit a kódból kivettek, a felületleíróban viszont
bennmaradt. Jegy: **#2027**.

### [picasa-keptalca.md](picasa-keptalca.md) — nincs nyitott kérdés (ÚJ szakasz, 2026-09-03)

⭐ **2026-09-03 (20. szakasz) — a mappa-token TELJESEN feltárva, és a #1919
egyik elfogadási feltétele MEGDŐLT.** A tokent **nem parancs** teszi a
tálcára, hanem a kijelölés TÍPUSA: a `0x0056bc10` egy
`__RTDynamicCast`-tal (`0x0056bc52`) próbálja `CAlbumSelectionNode`-dá
alakítani a kijelölést, és csak siker esetén tölti ki a `+0xeac` mezőt. A
felirat **négy változatban** áll elő (`Kiválasztott album` /
`Kiválasztott mappa` / `fotó` / `Nincs kijelölés`, keret `%s - %d %s`) —
a #1919-ben szereplő nagykötőjel helyett **kiskötőjellel**. A token a
teljes tálca-vásznat elfoglalja (`scratch/album` téglalapja azonos a
`scratch/docbounds`-szal), a `thumbui/scratch` pedig épp e vászon
kivágása, és a tulajdonos húsz felvételéből **egyen sincs vegyes
tartalom** ⇒ **rács és token kizárja egymást**, a #1919 „vegyesen is tud"
pontja törlendő. Melléktermék: a `scratch/highlight` kék pirula
**70%-os átlátszósága** vezetett a respack-fejléc helyesbítéséhez
(**#2178**), a felvételsorozat pedig a „Kijelölés" vízjel hibájához
(**#2179**).

⭐ **2026-09-02 (19. szakasz) — a tálcának SAJÁT kijelölése van.** A tulajdonos
képernyőképe (futó Picasa 3) mutatja: a tálcán a középső kép **kijelölve**. A
bináris ezt megmagyarázza: a tálca **ugyanolyan `CSelectionNode`**, mint a
fotórács (`[ebx+0xea4]`), és a számlálója (`0x00716cb0`) **elemenkénti**
jelzőt olvas (`cmp byte ptr [ecx+0x5a], 0`). Ezért van értelme a helyi menü
„Kijelölés eltávolítása" tételének. **Nálunk a tálca bélyegképein egyetlen
kattintás-kezelő sincs** (mérve: `TrayBar.qml:503`, a csíkban csak jobb gombos
`TapHandler` a 250. sorban), és a tálca parancsai a **RÁCS** kijelölésén
dolgoznak → **#2039**.
⛔ **Ugyanaznapi SAJÁT HELYESBÍTÉS:** a #2039 először azt állította, hogy a
kijelölés keretének színe „NINCS MÉRVE". **Téves** — a
`runtime/constants.ui`-ban áll, a fájl saját megjegyzésével együtt:
`thumbsel_color1=#009EFF` (kívül) / `thumbsel_color2=#FFFFFF` (belül), és a
`design-guide.md` 63. sora **2026-08-06 óta** dokumentálja (#384); a rácsunk
meg is valósítja. **Módszertani tanulság:** a `runtime/*.ui` szövegfájlok a
bizonyítéklánc **elejére** tartoznak — a Picasa a felület számadatainak egy
részét szándékosan kiszervezte oda.

### [design-guide.md](design-guide.md) — nincs nyitott kérdés (ÚJ szakasz, 2026-09-02)

⭐ **2026-09-02 — a `runtime/constants.ui` ÁTVILÁGÍTVA.** A fájl **46 élő
kulcsot** tartalmaz; ezek közül **csak a 23 szín-kulcs mérhető** azzal, hogy
megkeressük az értéket a `src/`-ben (egy `#634B45` megkülönböztető, egy puszta
`22` bármire illeszkedik — a számos kulcsokról ezért **nem állítunk semmit**).
Mérés: **11 megvan** a kódunkban, **3 hatókörön kívül** (Mac-változatok,
Linux-first projekt), **9 hiányzik**. ⚠️ A legfontosabb hiányzó az
**`alayout_titleColor=#634B45`** (mappa-cím): ugyanannak a blokknak a betűjét
(`Georgia`) és méretét (20) **már átvettük** (`LightboxHeader.qml:96–97`), a
színt nem — nálunk `Theme.folderTitle` → `ink` → `#1c1b19`. ⛔ **A lap
korábbi `✅` jelölése ezen a soron félrevezető volt** (a hármasból kettő volt
kész), javítva. A maradék nyolc színre a **szerepük NINCS MÉRVE** a mi
felületünkön — vakon átvenni tilos. Jegy: **#2043**.

### [pmp-database.md](pmp-database.md) — a BORÍTÓ-kérdés lezárva (2026-09-02)

⭐ **2026-09-04 (2.) — az `AdjustCurves` négy görbéjének SORRENDJE
(`filterdesc-registry.md`, #2238/1).** Az attribútum-olvasó
(`0x00bb9b60`, 255 b) bájtszintű kiolvasása **zárt** megfeleltetést ad:
`MasterCurve` = **`+0x40`** · `RedCurve` = **`+0x44`** ·
`GreenCurve` = **`+0x48`** · `BlueCurve` = **`+0x4c`** — mind a négy név és
mind a négy eltolás pontosan egyszer, azonos (növekvő) sorrendben, azonos
háromlépéses mintával (név → régi érték olvasása → új érték írása).
⇒ **A megvalósító nem feltevésből dolgozik.** Melléklelet: ugyanez az
olvasó a görbék ELŐTT beolvassa az `ExposureAdjustmentStops` attribútumot a
`+0x50` tagba (`0x00bb9b88`). ✅ **A szerepe MÉRVE (2026-09-04)**: az ELŐJELE választ a sötétítő (13,0)·(116,74)·(208,156)·(255,221) és a világosító (0,17)·(47,81)·(129,186)·(221,255) négypontos görbe közt, az ABSZOLÚT ÉRTÉKE az erősség.
⛔ Az alkalmazó (`0x00bb9e00`) a keresett `mov r32, [reg+disp8]` alakkal
**nem** hivatkozik a négy tagra (438 bájton nulla) — de ebből **nem
következik**, hogy nem használja; más címzési alak vagy paraméterátadás
nincs kizárva. ✅ **A `Depth` kérdése (#2238/2) 2026-09-04-én LEZÁRVA** (#2231): az akkori
öt bitmaszk-keresés **helyes volt, de rossz helyen** — a maszkok a
`0x00bb5e04` és `0x00bb5e1c` körül állnak, `cl`/`dl` regiszterrel, a `Depth`
pedig **nem is ebben a függvényben** dől el, hanem az oktree
csomópont-beszúrójában (`0x00bcb8e6`: `cmp [csomópont+0x10], 1` · `jbe` ⇒
csak `Depth > 1` esetén hasít; `0x00bcb9a6`: a gyerek `Depth − 1`-et örököl).
A **4268 bájtos** puffer is megvan: **három 1024 bájtos, 256 elemű tábla**
a `0xb8`, `0x4b8` és `0x8b8` eltoláson. Jegy: **#2231**.

⭐ **2026-09-04 — a `rainbow` ALT-os ágának kapcsolója LEZÁRVA: a
`0x00d67849` = „a Picasa az ELŐTÉRBEN van" (`filterdesc-registry.md`,
#2224).** A `0x00d67849` **nyers, négybájtos** keresése a végrehajtható
szekciókban **139** előfordulást ad: **137 olvasás, 2 írás**. ⭐ **A kapu,
amit az előző kör „helyi bájtnak" hitt, a függvény MÁSODIK PARAMÉTERE:**
`sub esp,0xa4` + négy `push` = **0xb4** ⇒ `[esp+0xb4]`=visszatérési cím,
`[esp+0xb8]`=1., **`[esp+0xbc]`=2. paraméter** (a `ret 8` is két
paramétert mond). A `0x005760e0` a **főablak-helyreállító**
(`Preferences\mainwinpos` / `mainwinismax`), és ha a 2. paraméter igaz,
`ShowWindow` → `SetFocus` → `BringWindowToTop` → `SetForegroundWindow` →
**`mov byte [0x00d67849], 1`** → `UpdateWindow`. ⭐ **Az öt hívó
mind kimérve** (a `.text` teljes `e8`-pásztázásából — az index `xrefs`
csak hármat ismer): `0x0040ce0b`, `0x0040d078`, `0x0040d428`,
`0x0040dcaa` **1**-gyel, `0x0040da02` **0**-val ⇒ a kapcsoló a rendes
indulás része. ⭐ **A második írás zárja le a jelentést:** a
`0x00a52890` ablakeljárásban az ugrótábla a **`0x1C` = `WM_ACTIVATEAPP`**
azonosítót — és csak azt — vezeti a `0x00a52e0c` blokkra, ahol
`mov eax,[ecx+8]` (`wParam`) → **`0x00a52e66` `mov byte [0x00d67849], al`**
⇒ a bájt **az alkalmazás előtér-állapota**. *(Helyesbítés: a cím
`0x00a52e66`, nem `0x00a52e65` — a nyers keresés az operandust adta.)*
⭐ **A 137 olvasásból 81** 28 bájton belül `GetAsyncKeyState`-et hív
(`0x00c406f8`) — köztük a `0x005d672b`, amiből a kérdés indult; ez az
őr azért kell, mert a `GetAsyncKeyState` rendszerszintű. ⇒ **A `rainbow`
ALT-os útja egy átlagos telepítésen ÉL** (a korábbi „alapból nem él" csak
az indulás pillanatára igaz). ⛔ **Nálunk (mérve):** a `rainbow` név öt
helyen ismert, de a `KNOWN_UNRENDERED_OPS`-ban ül ⇒ **nem renderel**; az
`AltModifier` a szerkesztőben **nulla** előfordulás. Az ALT-ág megépítése
ezért ma hazug gombot adna — a rejtett módosítós ágak jegye a **#2146**.
⭐ **Negatív eredmény:** az „előtérben vagyunk-e" őrt nálunk **nem kell
megépíteni** (Qtben a módosítót az esemény hozza, és esemény csak
fókuszált ablakhoz érkezik). Jegy: **#2224** (lezárva), **#2146**
(kommentelve).

⭐ **2026-09-03 (8. kör) — a hasonlóság-rekord KÖZEPE: 216 bájt
(`picasa-kereses-modok.md`).** ⛔ **Helyesbítés az előző körre:** az azt
állította, hogy a normalizáló (`0x007ebd90`) nem ír a rekord `+0x082`-től
induló területére — **téves**. A keresésem mintaillesztéses volt, és csak a
közvetlen `[edi+eltolás]` alakokat ismerte; a tényleges írás **SIB-alakú**
(`0x007ebf39`, `mov byte ptr [esi + edi - 1], al`, ahol az `edi` **index**).
A teljes törzs diszasszemblálása megtalálta. ⭐ **A hurok 216 iterációs**
(`0x007ebf23`, `cmp esi, 0xd8`), és **elemenként egy bájtot** ír: a vektor
elemét egy átalakító után megszorozza a skálatényezővel, **255,0-nál vágja**
(`0x00cf39d0` / `0x00cf3a00`), majd **csonkítva** egészre konvertálja
(`0x007ebf1e` `or eax, 0xC00` + `fistp`). A skálát a 216 elem maximumából
képzi, **0,001-es alsó korláttal** (`0x00cf3db0` / `0x00c7999c`).
⇒ **A 380 bájtból 377 elszámolva:** `+0x000` jelzőbájt · `+0x002…+0x081`
8×8 RGB565 · `+0x082…+0x159` 216 bájt · `+0x15C…+0x17B` 8 `float`;
ismeretlen már csak `+0x001`, `+0x15A`, `+0x15B` (**3 bájt**).
⛔ **NINCS MEG** az elemenkénti átalakítás: `0x0049fe60` → `0x00c0b310` →
`0x00c14398`, egy nem azonosított CRT-matematikai függvény.
⚠️ Ugyanaz a csapda MÁSODSZOR (a 66. kör rövid `fld`-kódolása után):
**regiszter-használatot ne mintaillesztéssel keress** — diszasszembláld a
teljes törzset, darabolva, és a szövegben keress a regiszternévre.
Jegy: **#447**.

⭐ **2026-09-03 (7. kör) — HÁROM Glimmer-leltár, és egy TÉVES jegy-tétel
(`filterdesc-registry.md`).** A #2211 munkalistája élén a
`TiledImageOperation` állt „**0 említéssel**". ⛔ **Ilyen nevű művelet nem
létezik** — a valódi neve **`TiledImageMask`**, és az a lap szerint a
**legjobban dokumentált** műveletünk (**17** említés a `docs/specs/` alatt,
mind a tizenkét attribútuma kiolvasva a `filters-decoded.md` 2026-08-16-i
szakaszában). A „0 említés" tehát tisztán a **rossz név** műterméke volt.
A lista másik **kilenc** neve ellenőrizve: mind pontos. ⭐ **A készletről
három különböző leltár készíthető, és egyik sem teljes önmagában:**
`filterdesc.xml` által **HASZNÁLT 31** · a binárisban név szerint
**REGISZTRÁLT 35** · az RTTI-ben **LÉTEZŐ 37** konkrét osztály (+2
ősosztály). A különbségek névvel és címmel kiírva: három osztály
(`BlendImageOperation`, `PaintMaskPlusImageMask`, `ShapeGradientImageMask`)
**létezik, de nincs regisztrációs sztringje** — tehát `filterdesc.xml`-ből
nem hozható létre, a motor belsőleg példányosítja. A negatív állítás mind a
**13 bináris-indexen** ellenőrizve, mindenütt nulla találattal. A 4.5
szakasz fejléce egyértelműsítve („mind a 31" → „a HASZNÁLT 31"). Jegy:
**#2211** (komment), **#626** (komment).

⭐ **2026-09-03 (6. kör) — a hasonlóság-rekord eleje: 8×8 RGB565
BÉLYEGKÉP (`picasa-kereses-modok.md`).** A kvantáló (`0x007eb8c0`) egy
kibontott kettős ciklus: soronként **nyolc** `uint16`-ot ír
(`0x007eb90a`…`0x007ebac9`), majd `add esi, 16`; a külső ciklus
`cmp edx, 8` / `jb` ⇒ **8 sor × 8 képpont × 2 bájt = 128 bájt**. Az érték a
már ismert RGB565-kód. ⇒ **A rekord elején egy 8×8-as, RGB565-be kvantált
bélyegkép áll** — ez a Picasa hasonlósági ujjlenyomatának első fele.
⭐ **A rekord KEZDETE is rögzítve:** mindkét közbenső hívás
callee-cleanup (`ret 4`: a kvantáló vége, illetve `0x007ebf4e`), tehát a
`rep movsd` forrása (`0x007eb5d0`, `esp+0x264`) ugyanaz a cím, mint a
`0x007eb5a3`-nál 1-re állított **jelzőbájt**. Teljes kép:
`+0x000` jelzőbájt=1 · `+0x002…+0x081` 8×8 RGB565 · `+0x082…+0x15B` 218
bájt ISMERETLEN · `+0x15C…+0x17B` 8 `float`. ⚠️ A 218 bájtos rész a
normalizálónak átadott `edi` (`0x007eb5b8`, pontosan `+0x082`) célterülete,
**de a normalizáló nem ír oda** — a 460 bájtos törzsében nulla `edi`-célú
írás; a hurok után **skálatényezőt** számol (`0x00cf3db0` küszöb,
`0x00c7999c` nulla-védelem). ⚠️ Melléklelet: a `functions` tábla ezt a
függvényt **442** bájtosnak mondja, a `ret 4` viszont a **446.** bájtnál
áll — az indexbeli méretre vágás **levágja a függvény végét**. Jegy:
**#447**.

⭐ **2026-09-03 (5. kör) — a 380 bájtos hasonlóság-rekord SZERKEZETE
(`picasa-kereses-modok.md`).** Az összeállító kód (`0x007eb5c4`–`0x007eb5f6`)
maradék nélkül megmagyarázza a rekordot: `rep movsd` `ecx = 0x5F` = **95
dword = pontosan 380 bájt** a `esp+0x264`-nél álló munkapufferből, **majd
nyolc `float`-tárolás felülírja az utolsó 32 bájtot**. ⇒ a rekord két
része: `+0x000…+0x15B` (348 bájt) a munkapufferből, `+0x15C…+0x17B`
(8 `float`) a négy `0x007ea650`-hívás skalárjaiból. ⭐ **A megfeleltetés
ZÁRT:** a négy hívás nyolc kimeneti címe pontosan egyszer szerepel a nyolc
tárolás forrásaként, hívási sorrendben — ez egyben hitelesíti a hívási
hely-táblát is. ⚠️ **Helyesbítés az előző körre:** a `0x007ea650` **nem** a
vektor építője — három paramétert kap (`kép-leíró`, `kimenet1`,
`kimenet2`), **két skalárt** ad hívásonként, és **négy különböző képre**
fut (`esp+0x74`, `esp+0xE0`, `esp+0x108`, `esp+0x130`). A nyitott kérdés
ezzel **szűkült**: nem a 380 bájt, hanem a **348 bájtos első rész**, amit
az RGB565-kvantáló (`0x007eb8c0`) tölt; a rekord első két bájtja a kvantáló
paraméterén kívülről jön. Mintafájl továbbra sincs. Jegy: **#447**.

⭐ **2026-09-03 (4. kör) — a HASONLÓSÁG-ADATBÁZIS tárolása és a lánc
(`picasa-kereses-modok.md`).** A `searchoptions/similarthumb` mögötti
hasonlóság-keresésnek saját, tartós adatbázisa van, és az a **`CBlockFile`**
keretben él (ugyanaz, mint a bélyegképeké). **A rekord FIX 380 bájt**
(`0x007eb652` `push 0x17c`, `0x007eb659` a leíró méret-mezője,
`0x007eb661` memcpy); visszaolvasáskor `0x007eb235` `cmp eax, 0x17c` /
`jne` ⇒ **nincs verziómező**, a 380-tól eltérő méretű bejegyzést a Picasa
érvénytelennek veszi és újraszámolja. A lánc: `0x007e95f0` → `0x007ead60`
(`CSimSearch::updating`, „Updating similarity database…") → átméretezés a
`Preferences\ResampleFilter2` szerint (`0x00a3f490`; a nagy átméretező
`0x00a42c20` **4×** fut) → jellemző-kinyerés `0x007ea650` (**4×**) →
normalizálás `0x007ebd90`. ⭐ **A képpont-kvantálás RGB565**
(`0x007eb8e4`–`0x007eb900`: R>>3, G>>2, B>>3, BGRA sorrendből). ⭐ **A
memóriabeli vektor 216 `float`** (`0x007ebda2` `mov edx, 0x24` = 36
iteráció × 6 elem, lépés `0x18`) = 864 bájt — a tárolt 380-nál nagyobb,
tehát a tárolt alak **tömörített**. ⛔ **A 380 bájt belső elrendezése NINCS
MEG**, és **mintafájl sincs** a repóban (a tulajdonos sosem futtatta a
funkciót); a megfejtés útja a `0x007ea650` (1802 b) teljes
diszasszemblálása. Melléklelet: a `makemoviecache.db` írási helyén a leíró
**4 bájtos** blobot ad át (`0x0080f9a5`). Jegy: **#447**.

⭐ **2026-09-03 (3. kör) — MEGVAN A BÉLYEGKÉP-GYORSÍTÓTÁR ELLENŐRZŐÖSSZEGE.**
A hetek óta nyitott örökölt kérdés lezárva. Az osztály neve **`CBlockFile`**
(`.\thumblab\CBlockFile.cpp`), és a Picasa **saját** CSV-kiírója
(`0x006b5e00`, „Write blockfile CSV") nevezi meg a három tömböt:
`Size,Offset,Checksum` — a kiírás sorrendje (`0x006b5ed6`–`0x006b5ef1`)
a `+0x54`/`+0x5c`/`+0x64` tárolókhoz köti őket. **A képlet**
(`0x006b9af8`–`0x006b9b1d`):
`Checksum = (JS_hash(teljes_út) mod 1 000 231) ^ rol(idő_lo,13) ^
rol(idő_hi,17) ^ rol(fájlméret,18)`, ahol a `JS_hash` `0x12345678`-cal
magvetett, kisbetűsítő, és `idő` a `thumbindex.db` **MÁSODIK** FILETIME
mezője. **Ellenőrzés: 48 605 pontos, 32 bites egyezés** a nagy katalóguson
(továbbá 2 161 és 1 932 a két kicsin) — véletlen egyezés kizárva. A nem
egyező bejegyzések aránya a katalógus korával nő (74,2 % → 67,8 % → 36,5 %):
**az eltérés maga a jelzés**, amiért a mező létezik (elavult bélyegkép), és
ezt a `dirty`/`valid` bájt NEM jelöli. ⭐ **A `CBlockFile` nem
bélyegkép-specifikus:** az író 19 hívási helye közt ott a
`makemoviecache.db` (`0x0080f830`) és a **hasonlóság-kereső adatbázisa**
(`0x007ead60`, `CSimSearch::updating`) ⇒ egy olvasó mindhármat megnyitja.
⭐ A `Size` mező **24 bites** (`& 0xFFFFFF`), és az író a 16 MB fölötti
blobot **elutasítja** (`0x006b75f7`/`0x006b7603`); a felső 8 bit mind a 17
mintaindexben, 302 000+ bejegyzésen **nulla**. ⚠️ Módszertani lelet: a
„nincs több forgatás-hash az osztályban" korábbi negatívum **téves volt** —
a függvényindexre épült, az pedig nem fedi a `0x006b9b50`…`0x006b9dd0`
tartományt; a **bájtszintű** pásztázás hét további forgatást talált, és az
egyik volt a válasz. Jegy: **#2195**.

⭐ **2026-09-03 (2. kör) — a `thumbindex.db` NEM útvonalat tárol, és a
`típus` FORMÁTUMKÓD.** Két helyesbítés a `pmp-database.md` 8.1-en, amelyek
nélkül a most nyitott olvasó-jegy (#2195) rossz útvonalakat adna:
**(1)** fájl-bejegyzésnél a rekord csak a **nevet** tartalmazza — a mért
133 089 fájlnév közül **egyetlenegyben sincs** `\`, és a `+26` mező a
**szülőmappa slotindexe** (érvényes: 133 089/133 089); a teljes út
`név(szülő) + név`. **(2)** A `típus` nem „mappa vagy fájl", hanem
**tizenkét értékű formátumkód**, amit a Picasa a **tartalomból** állapít
meg, nem a kiterjesztésből: 33 `.png` nevű fájl JPEG-ként (2), 26 `.jpg` +
4 `.jpeg` PNG-ként (14) van bejegyezve. ⭐ A `típus = 1001` az
**arcsablon-bejegyzés** — halmaz-azonosság a `facetemplatesV2_index.db`
foglalt slotjaival (412 = 412, metszet 412). A `típus = 0` **üres slot**
(név, méret, mindkét időbélyeg, `dirty`, `valid` mind nulla, 5 325/5 325) —
ez magyarázza a nem zsugorodó tömböket és a `valid` bájt szerepét.
⛔ **Negatív, döntő:** a tár fordítási egységének egyetlen forgatás-hash-e
(`0x006b9870`) **nem** a bélyegkép-kulcs — egyetlen hívója (`0x006ecd50`)
az `onlinechecksum` / `LHUpload` sztringeket viseli, tehát a megszűnt
webalbum-szinkroné. Az algoritmusa mégis kiolvasva (8.8): `0x12345678`-cal
magvetett, kisbetűsítő sztring-hash `mod 1 000 231`, forgatott
időbélyeg-tagokkal — és egy **időzóna-toleráns egyeztetővel**, amely
−12 h…+12 h között **óránként** végigpróbálja a jelölteket. Élő
ellenőrzés **NINCS MEG**: az oszlop mind a három katalógusban üres.
A bélyegkép-kulcsra a valódi kulcstömbön 9 + 60 + 28 próba és mind az 59
PMP-oszlop **nullát** adott (8.9). Jegy: **#2195**.

⭐ **2026-09-03 — a `*_index.db` NÉGY PÁRHUZAMOS TÖMB, és az előző napi
leírás HELYESBÍTVE.** A `pmp-database.md` 8.2 szakaszának első kiadása
„20 bájt fejléc + N × 12 bájtos rekord (`uint64 q` + `uint32 u`)"-t írt le.
**A szerkezet téves volt** — és a hiba azért maradt észrevétlen, mert a két
modell **bitre ugyanazt a fájlméretet** adja (`20 + 12N`), tehát a
méret-ellenőrzés nem tudta megkülönböztetni őket. A valódi szerkezet az
**író kódjából** olvasva: `0x006b7fc0` (a tár másodlagos vtáblájának,
`0x00ca84e8`, 1. rekesze) kiír 4 bájt verziót (`0x00d678e0` globál, `1.6`),
majd háromszor hívja a `0x0099c1e0` tároló-írót, amely
`fwrite(&darab,4,1,f)` után `fwrite(adat,4,darab,f)`-et tesz — **nincs 12
bájtos rekord**. A négy tömb: üres · **kulcs** · **eltolás** · **hossz**.
Az ellenőrzés, ami a méretnél erősebb: a legutolsó `eltolás+hossz`
**bitre** az adatfájl mérete (144/3 338/140 755 slotos katalóguson egyaránt).
⭐ A blobok **nyers JPEG-ek** ⇒ a PicasaPy `seek`+`read`-del kiveheti az
eredeti bélyegképet, **a kulcs képzésének ismerete nélkül**. A slot indexe
maga az azonosító (`thumbindex.db` rekordsorszáma), a `bigthumbs`/`previews`
nagyobb slotszáma **túlfoglalás**, nem másik azonosítótér. A kulcs **nem**
tartalom-hash (kétirányú cáfolat: 217/217 azonos kulcs eltérő blobbal,
310 azonos blob eltérő kulccsal). ⛔ **Visszavonva** a korábbi kiadás `q`/`u`
statisztikái és kizárásai — nem létező mezőkre vonatkoztak; a bennük közölt
ferde bit-eloszlás (0,16 az 0,50 helyett) valójában **a saját modell
cáfolata** volt, csak érdekességként lett leírva. Jegy: **#2195**.

⭐ **2026-09-02 — az ÖTÖDIK bélyegkép-tár: `albums.db`, a mappák BORÍTÓJA.**
A tulajdonos képernyőképe mutatta, hogy a bal hasáb fastruktúrájában **fotó-kupac**
áll a sárga mappaikon helyett. Nem futásidejű: **mappánként egy mentett
raszter**. A tár-nevek egyetlen függvényben (`0x00415790`) állnak, és az
`albums.db` **együtt szerepel** a másik néggyel (`m_albumThumbs`). Kapcsoló:
`Preferences\ShowAlbumThumbnails2` (a Nézet menü „Indexképek megjelenítése a
könyvtárban" pipája, alapérték **0**). **A formátum NEM JPEG**: 8 bájt fejléc
(`uint32 width`, `uint32 height`) + `w*h*4` bájt **BGRA** — a
`8 + w*h*4 == hossz` azonosság **37/37** élő bejegyzésre teljesül, `FFD8`
kezdet 0/37. Aránytartó (leghosszabb oldal 72–119 px), **valódi
átlátszósággal** (1 400–2 200 átlátszó képpont mintánként). Kirenderelve:
**egy elülső fotó + 1–3 mögötte, kifordítva** ⇒ a „legrégebbi kép mini
ikonja" feltevés **megdőlt**. A rés-index az **albumtábla sorindexe**, és a
lemezes mappák is albumként szerepelnek (élő minta: `wallpapers`, `space`,
`volt` a `albumdata_filename`-mel). Nálunk **minden sor ugyanaz a mappaikon**
(`FolderTreeItem.qml:101`) → **#2049**.

**A kérdés — „MELYIK fotókból áll a kupac, és milyen sorrendben?" —
2026-09-02-án LEZÁRULT** (`pmp-database.md` **7. szakasz**, jegy **#2049**):
az összeállító a `0x00423780` (2167 b), amit a `0x00423500` hív. A lista
**első `min(N,4)`** eleme kerül a kupacba (`0x004237ab` `cmp eax,4`), hátulról
előre rajzolva, tehát a **lista első eleme kerül legfelülre**
(`0x00423f45`–`0x00423f4d`). Az elrendezés **albumonként determinisztikus**:
`srand(rés-index ^ 0x133475)` (`0x00423a2b`), MSVCRT-generátorral
(`0x00c08221`). Fotónként: forgatás **±0,1 rad = ±5,73°** (a legalsó fotó
forgatás nélkül), oldaleltolás `±4·i`, függőleges `5i…9i`. A vászon a kupac
**befoglaló téglalapja** (`0x00423f70`). A lágy árnyék **sugara 5 px**
(mérve: ~5 képpontos alfa-lefutás 37 valódi borítón), **alfája 153**
(`0.6 × 255`, `0x00a6e32e`). Megdőlt: „a legrégebbi képből készül".

### Nincs nyitott kérdés

`filterdesc-registry.md` · `ui-audit-context-menus.md` · `ui-audit-mainwindow.md` · `picasa-native-filter-registry.md` · **`ui-audit-editor.md`** · és a lenti táblák
minden további lapja.

## Formátum-specifikációk (adatfájlok, erőforrások)

| lap | miről szól |
|---|---|
| [picasa-ini-format.md](picasa-ini-format.md) | A `.picasa.ini` — az igazságforrás, round-trip szabályokkal · ⭐ **2026-09-04: a `[Picasa] date=` OLVASÓJA `atof` (#2304)** — `0x00441ed0`: alapérték **`949998.0`** (`0x00c7ccf8`), majd `0x0044248d` → `0x00c080d7` (`atof`) ⇒ az **ISO-alak némán 1905-öt ad**; az író (`0x00710080`) `%f`-fel ír és a **0.0-t kihagyja**; a közös beállító `0x004460a0` egy hívásból tölti a DB-t ÉS az ini-t. ⚠️ NYITVA: melyik hívó süti el először új mappára (vtábla-mutató a `0x00c81fb0`-on) |
| [picasa-beepitett-webszerver.md](picasa-beepitett-webszerver.md) | **A Picasa 3 beépített HTTP/WebDAV-kiszolgálója** — a bekapcsoló beállítások (`AllowRemoteWeb`, `LANShareAlbums`, `LANPassword`, `DAVSupport`, `EnableTester`, `UIProfiling`), a 14 végpont teljes listája, a kép- és bélyegkép-URL-ek, a WebDAV-válaszok, a LAN-hirdetés mezői, a `text/plain` metaadat-alak (album + fájl), és a `picasa://` URL-séma öt művelete. Döntés: **nem építjük meg** (#2023) |
| [pmp-database.md](pmp-database.md) | A központi adatbázis (`db3` / PMP) — **és a bélyegkép-gyorstár blokkfájl-formátuma**: a négy szint mért mérete (72/144/288/640 px), az `*_index.db` három vektora (`20 + 12n`, 11 fájlon mérve), a slot ↔ `thumbindex.db` sorindex kötés, a kulcsvektor **azonos résterű tárak közt bitre azonos** (⇒ nem blob-ellenőrzőösszeg), az elavult sorok mért veszélye és a `CBlockFile` bináris oldala · ⭐ **2026-09-04 (9. szakasz, #2304): az `albumdata_date.pmp` a MAPPA saját dátuma** — a tulajdonos VALÓDI adatbázisából mérve: az `AI` mappa sora `45244.72859953704` (OLE Variant, alappont 1899-12-30) ⇒ **2023-11-14 17:29:11**, pontosan az a nap, amit az eredeti a fejlécben mutat, és az az év, amely alá a bal hasábban sorolja ⇒ **a fejlécdátum és az évcsoport ugyanabból az EGY mezőből jön**. ⛔ **NEM a képekből számolódik**: a virtuális albumok mind az adatbázis létrehozási idejét viselik, a lemezmappák értékei 2009…2026 közt szórnak, és a másodperc-pontos érték semmilyen kép-aggregátumból nem adódna. Az `albumdata_category` mért értékkészlete: `0` virtuális · `1` eltérő besorolású lemezmappa · `2` közönséges lemezmappa · `8` „Név nélküliek”. ⚠️ Nálunk a `folder_date.py:72` **eldobja az időrészt** (nap pontosság) · ⭐ **2026-09-04 (#2335/#2336): MIT AD MA a db3-importunk, VALÓDI adatbázison mérve** — a hat behozott oszlop mellett elveszik **342** kép kulcsszava, **219** kép helyadata és **115** címke-dátum; ⛔ **`imagedata_star.pmp` NEM LÉTEZIK** a 65 valódi oszlop közt, ezért minden kép csillagozatlanul jön be (a csillag a `starlist.txt`-ben van, 50 kép) — és a teszt maga gyártja a hiányzó oszlopot, ezért zöld · ⚠️ **2026-09-04 HELYESBÍTVE (#1446): a kulcs képlete NEM volt nyitott** — a lap **8.10** szakasza 2026-09-03 óta tartalmazza (`(JS_hash(út) mod 1 000 231) ^ rol(idő_lo,13) ^ rol(idő_hi,17) ^ rol(méret,18)`); a korábbi »NYITOTT« mondatok elavult jelölések voltak, javítva. ⭐ **Független ellenőrzés a valódi katalóguson: 2161/2776 pontos egyezés** a MÁSODIK FILETIME-mal és bájtonkénti kódolással (az elsővel 0, UTF-16LE-vel 0) ⇒ a képlet és a mezőválasztás MEGERŐSÍTVE. ⛔ 615 sor egyikkel sem egyezik — elavult gyorsítótár a legvalószínűbb, de BLOKKOLT: frissen újraépített bélyegkép-tár vagy az ÍRÓ ágának kimérése kell hozzá · ⭐ **2026-09-04: az `albumdata_date` TÁROLT, nem számított (#2304)** — az `autodate` parancs (`0x00cc1c20`, kezelő `0x00849dc0` → `0x00441760`) a mappa elemeinek **legkorábbi** idejét számolja (őrszem `949998.0` a `0x00c7ccf8`-on; üres albumnál `-1` ⇒ nem ír dátumot), de a tárolt érték **0/23 mappán** egyezik a mai legkorábbi vagy legkésőbbi képidővel ⇒ egyszer beáll és nem számolódik újra; a 144 albumsorból **0 dátumtalan**. ⚠️ NYITVA: mi írja be a mappa **első** dátumát · ⭐ **2026-09-04: a mappadátum-beállító a `CThumbDB` vtáblájában ül (#2304)** — `CThumbDB::vftable` **`0x00c81fa4`**, a `date` a **3. rés** (`0x004460a0`); a szomszédok tulajdonságonkénti beállítók (2 = `description` `0x00443c90`, 4 = `location` `0x0044fa80`). **Kimerítő negatív:** a teljes `.text`-ben **0** `call [reg+0x0c]` (a pásztázó ismert pozitívval hitelesítve: 21 110 `ff 15`, 951 `ff 50`) ⇒ a hívás `mov reg,[vtábla+0xc]` + `call reg`. ⛔ **2026-09-05 HELYESBÍTVE (11. szakasz, #2304): az »olcsó lánc kimerült« KORAI volt** — a pásztázás csak a `call [reg+0x0c]` alakot nézte, és kimaradt az `e9`-es (ugró) thunk-keresés meg a több-öröklődéses vtáblák RTTI-feloldása. ⭐ Mindkettő adott eredményt: a három tulajdonság-beállítóhoz **1–1 igazító thunk** tartozik (`0x0049f390` = dátum, `0x0049f4a0` = leírás, `0x0049f310` = hely; mind `sub ecx, 8` + `jmp`, egy ~57 darabos, 8 bájtos thunk-futamban), és az RTTI szerint a `0x00c81fa4` vtábla **`IThumbDB`** (offset 72), a `0x00c820d0` pedig **`IAlbumStore`** (offset 80) — a 80−72=8 a thunk igazításával számtanilag zár ⇒ **a beállítók INTERFÉSZ-metódusok**, ezért nincs közvetlen hívásuk. ⭐ **A `CThumbDB` teljes objektum-kiosztása** (konstruktor `FUN_00415790` + RTTI, két független forrásból): `+0x00` alap, `+0x48` IThumbDB, `+0x4c` IThumbnailSource, `+0x50` IAlbumStore, `+0x54` IImageStore, `+0x58` IGetImage, `+0x5c` IVirtualFile, `+0x60` **ytINI::CallBack**, `+0x64` **IAlbumPersistedCallback** (ez a két utóbbi szerep eddig nem volt dokumentálva); a példány az alkalmazás-objektum **`+0x1034`** mezőjében él (232 olvasás, 108 függvény). ⛔ **Új kimerítő negatívok:** `IAlbumStore` felvétele **0** (a thunk-vtábla a gyakorlatban halott), `IThumbDB` felvétele 71 hely/49 függvény, az általános 3. rés-hívás 796 hely/528 függvény; a két halmaz metszete **egyetlen** függvény, és az **téves riasztás** (`FUN_006f5580` a saját elsődleges vtábláját hívja; a `lea reg,[reg-0x48]` a CThumbDB interfész-metódusainak ujjlenyomata). ✅ **2026-09-05 LEZÁRVA (12. szakasz, #2304): MEGVAN mindkét hívó.** **Helyi, automatikus út:** `FUN_00441ac0` (110 b) — meghívja az **autodate**-számolót (`0x00441760`, a mappa elemeinek legkorábbi ideje), és ha az sikerül, a 3. réssel beállítja a dátumot **`bool = 0`**-val ⇒ **csak az adatbázisba ír, a `.picasa.ini`-be NEM**; három hívási helye van, az egyik a **„Folders on Disk” / „Other Stuff”** sztringes `FUN_00441e00` (a mappa-felvételi út). **Online album út:** `FUN_006f2fc0` — a webalbum-hírcsatorna dátumát írja, **`bool = 1`** ⇒ **DB ÉS `.picasa.ini`**. ⭐ **A beállító szignatúrája:** (azonosító, `double` dátum, `bool` ini-kapcsoló); a törzs `add esi,-0x48`-cal számol vissza a valódi objektumra — ez a 11.2 interfész-azonosításának **független megerősítése**. ⛔ **Miért kerülte el négy korábbi pásztázás:** (a) a `GetThumbDB()` **akcesszor** (`0x004a0d60`, 19 b) miatt nincs inline `[app+0x1034]` a hívási helyen; (b) a helyi hívó **maga is CThumbDB-metódus**, így a `this` már az IThumbDB ⇒ **nincs `+0x48` igazítás**; (c) a 3. rés hívása bájtmintával nem szűrhető (796 hely). ⭐ **Ami eldöntötte: az ARGUMENTUM TÍPUSA** — a `double` a vermen kötelezően `sub esp,8` + `fstp qword [esp]` párt hoz; erre pásztázva 356 → 58 → **2** valódi találat · ⭐ **2026-09-05 (10. szakasz, #2304): a `thumbindex` KÉT IDŐBÉLYEGE — honnan jön és mikor frissül.** A könyvtárbejáró (`FUN_004e62d0`) a `WIN32_FIND_DATAA`-ból **csak négy mezőt** olvas (attribútum `+0x208`, **`ftLastWriteTime` `+0x21c`**, `nFileSizeLow` `+0x228`, név `+0x234`); ⛔ **kimerítő negatív** (ismert pozitívval hitelesítve): a `ftCreationTime` (`+0x20c`) és a `ftLastAccessTime` (`+0x214`) eltolására **egyetlen hivatkozás sincs** a bejáró függvénycsoportjában. ⇒ **A rekord 2. mezője NEM „hozzáférési idő”, hanem a fájl MÓDOSÍTÁSI ideje** (`0x004e74bd` → `0x004e74dc`) — a Picasa saját CSV-fejléce rossz nevet ad neki. ⭐ **Az 1. mezőnek EGYETLEN írója van** (`0x004eeb10`) és annak **egyetlen hívója** (`0x00427898`, a képbeolvasóban): a kép **metaadat-dátuma** (tulajdonság `0x37`, őrszem `949998.0`), a beolvasáskor rögzítve — a pásztázó **soha nem frissíti**. Mindkét mező `TzSpecificLocalTimeToSystemTime`-mal készül ⇒ **helyi** időből származó UTC. **Mérés** 140 758 rekorden: a névbe kódolt felvételi idővel az 1. mező 59,5 %-ban másodpercre, 91,8 %-ban percen belül egyezik, a 2. mező csak 25,4 % / 32,1 %; az 1. mező **soha nem nulla** (0/135 433), a 2. mező 1101-szer az; metaadat-dátum nélküli fájloknál (`.png`, 32/33) a kettő **egybeesik**. ⛔ **Helyesbítés a 69. tételhez:** a tartalék-szabályunk **nem** tér el az eredetitől — a különbség a **rögzítettség** (ő befagyasztja, mi élőben olvassuk a `mtime`-ot). Jegyek: **#2304**, **#2375**, **#2373** |
| [picasa-arcfelismeres.md](picasa-arcfelismeres.md) | **Az arcfelismerés TELJES működése** — a három réteg és kapcsolóik, a két küszöb-létra, a KÉT ini-írási útvonal (`facedata`!), a `db3` arc-oszlopai élő adaton mérve, a három romboló művelet, a verzió-migráció; **15.: a személy-album fejlécsávja** — 25 parancs, a küszöb-lazítás képlete, a `]ignoreface` írás (#2187) |
| [picasa-imagedata-rekord.md](picasa-imagedata-rekord.md) | Az `imagedata` rekord — belső kép-nyilvántartás |
| [picasa-respack-format.md](picasa-respack-format.md) | `respack.yt` — a bináris erőforráscsomag (megfejtve); **2026-09-03: a rétegfejléc 8–9. bájtja ÁTLÁTSZÓSÁG** (`uint16`, 256 = átlátszatlan) — a lap két korábbi sora téves volt, a kicsomagolónk ma eldobja a mezőt (**#2178**) |
| [picasa-program-resources.md](picasa-program-resources.md) | Erőforrás- és formátum-leltár (gombok, web-export, plugin-ök) |
| [picasa-fen-dialogs.md](picasa-fen-dialogs.md) | A `.fen` dialógus-definíciók |
| [picasa-web-template-nyelv.md](picasa-web-template-nyelv.md) | A web-export sablonnyelve |
| [picasa-exe-strings.md](picasa-exe-strings.md) | Bináris string-bányászat |
| [picasa-beepitett-konyvtarak.md](picasa-beepitett-konyvtarak.md) | A Picasa beépített nyílt forráskódú könyvtárai |
| [picasa-linux-mod.md](picasa-linux-mod.md) | **A Picasa Linux-módja** — mit tiltott le maga a Google Wine alatt, és miért |

## Képfeldolgozás (szűrők, render)

| lap | miről szól |
|---|---|
| [filters-decoded.md](filters-decoded.md) | A szűrők visszafejtett modelljei + golden-verdiktek |
| [filterdesc-registry.md](filterdesc-registry.md) | A `filterdesc.xml` — csúszkanevek, tartományok, alapértékek. ✅ **2026-09-03 — a 34 Glimmer-művelet VTABLE-TÉRKÉPE** (#2211): minden osztályhoz vtable, attribútum-beolvasó (1. rés), alkalmazó (6. rés), munkavégző (8. rés) és **attribútum → tagoffszet** tábla. **Két közös motor**: `0x00bb7c80` (kép-bejáró, 7 művelet) és `0x00bc16b0` (színmátrix-alkalmazó, 4 művelet); a `GetVar`/`Nested`/`Tint` alkalmazója **6 bájtos no-op** ⇒ szerkezeti műveletek, nincs saját képpont-menetük. A **`TwoTone` és a `GradientMap` bitre ugyanazt a munkavégzőt futtatja** (`0x00bb87b0`) ⇒ a TwoTone kétmegállós színátmenet-leképezés. A `BlendAlpha` **ős-attribútum**, minden művelethez elérhető. ✅ **A `HSVGradientMap` interpolációja** (#2238): `s`/`v` lineáris, a **színezet a RÖVIDEBB ÍVEN** (ha a két hue távolsága > 180°, az egyik végpont ±360-nal eltolódik). ✅ **A `QuantizePalette` `Depth`-je az oktree MÉLYSÉG-KERETE** (#2238) — hány szint mélyre mehet a fa, azaz hány bitet néz csatornánként; a gyerekindex a `7 − szint`-edik bitből áll, a szétvágás lusta. ✅ **Az `EdgeDetectionB` ÖSSZETETT** (#2238): a `[+0x34]` gyerek egy `SimpleColorMatrix`, és a `100 − detail` annak a **`contrast`**-ja; a művelet emellett `Blur`, `EdgeDetectionSobel` és `AdjustCurves` gyerekeket is épít. ✅ **2026-09-04 (#2238): az `Exposure` NEGYEDIK attribútuma a **`fill`** (`+0x50`) — és épp az hajtja az 5 pontos derítőfény-görbét; a négy attribútum ága: `exposure` → a fix tábla, `contrast`, `fill` → a paraméteres görbe, `blacks`. Az `AdjustCurves` négy görbéjének SORRENDJE is kiolvasva: `MasterCurve` +0x40 · `RedCurve` +0x44 · `GreenCurve` +0x48 · `BlueCurve` +0x4c. ✅ **Az `Exposure` KÉT görbéje számszerűen** (#2211): egy FIX nyolcpontos tábla (14→0 … 255→**160**, sötétítő) és egy ÖT pontos, paraméteres görbe ((0,0) · (6, 42s+6) · (36, 112s+36) · (126, 72s+126) · (255,255)) — derítőfény-alak, `s = 0`-nál azonosság. Mellé egy módszertani apróság: a „közel a nullához" próba a float **bitmintáján** megy (`|bitkülönbség| < 8` → a görbe kimarad). ✅ **A `HSVGradientMap` megállói HSV-ben vannak** (#2211): minden megálló `color{h,s,v}` + `position`; **`h` fokban (0–360), `s`/`v` százalékban (0–100)**, a szektor `h/360·6`, a kimenet ×255 — ez különbözteti meg a `GradientMap`-tól, ahol a megállók RGB-ben vannak. ✅ **A `QuantizePalette` OKTREE-alapú palettaválasztó** (#2211, #2231) — a `Steps` a paletta MÉRETE, nem a csatornánkénti szintszám; nálunk egyenletes lépésköz. Mellé a MASZK-osztályok térképe: náluk az attribútum-beolvasó az **5. rés**, a `TiledImageMask` **tizenkét** attribútumot ismer (a `red.cfg` hetet használ), és a `ShapeGradient` a `CircularGradient` lecsupaszított változata (közös beolvasó és alkalmazó). ✅ **Ugyanaznap HÉT MŰVELET is kimérve** (#2211): az **`AutoFix`** teljes — csatornánkénti hisztogram, majd `LUT[x] = clamp(round((x−lo)/(hi−lo)·255+0,5))`, **vágás nélkül** (nálunk a vágópontos „Jó napom van”-modell fut, **#2229**); az **`AdjustCurves`** négy görbe-tagja `+0x40`…`+0x4c`, előttük az `ExposureAdjustmentStops`; a **`Resize`** ugyanazt a `ytResampler`-t hívja, mint a forgatás (lépték = 1 → doboz, egyébként **Mitchell–Netravali B = C = 0,4**) — nálunk bilineáris, **#2227**; a **`TwoTone`** bizonyítottan a `GradientMap` két megállóval (közös munkavégző + a `+0x40` tag + a GradientMap-beolvasó meghívása); az **`IR`** szürkítő mátrixa `[redweight, 2,0, −1−redweight]` mindhárom csatornára (a súlyok összege mindig 1), mellé egy izotróp elmosás `xblur = yblur = greenglow` (alap 5,0), `greenglowalpha` (alap 0,25) keveréssel, `redweight` alap **−0,5**; a **`MultiplyColorMatrix`** teljes 4×5 mátrixa (a három színcsatorna szorzása `multiplier`-rel, alfa érintetlen); az **`EdgeDetectionB`** belső paramétere **`100 − detail`**. Módszertan: az alapérték mindig a getter elé betöltött konstans, a gyerekművelet tagoffszete pedig azonosítja a gyerek osztályát. |
| [picasa-native-filter-registry.md](picasa-native-filter-registry.md) | A natív szűrő-tábla: 49 név → kezelő + képen belüli vezérlők |
| [picasa-native-filter-workers.md](picasa-native-filter-workers.md) | A natív szűrők munkafüggvényei — hívási térkép |
| [histogram-reference.md](histogram-reference.md) | Hisztogram-referencia és összevetés |

## Felület — KÖTELEZŐ méretspecifikációk

Ezek **normatívak**: a felületnek pontosan ezeket kell követnie.

| lap | miről szól |
|---|---|
| [szerkeszto-panel-meretek.md](szerkeszto-panel-meretek.md) | A szerkesztő bal panelje (201 elem) — **az 1. fül gombsorrendjének EGYETLEN érvényes forrása** |
| [szerkeszto-felso-sav.md](szerkeszto-felso-sav.md) | **A szerkesztő FELSŐ SÁVJA (`oneup_controls`)** — a hét vezérlő képpontos geometriája két, egymást igazoló forrásból; a „paletta-ikonos gomb" = `quickupload` (Web Albums Drop Box); a filmszalag **hét férőhelyes**, az aktuális kép **mindig középen**; a kijelölés-keret `#009EFF`+`#D4D4D4`; a hisztogram-doboz horgonya `root.alsó − 95` |
| [getmore-klipgyujto-mod.md](getmore-klipgyujto-mod.md) | **A „Továbbiak…" klip-gyűjtő MÓD** — két belépési pont (kollázs, filmkészítő), a visszatérő gomb **pontosan három** felirata, a kijelölés a **képtálcán át** megy a projektbe, a ✕ **csak elrejti** a sávot (`hidetarget`), és a sáv **eltakarja** a Nyomtatás/E-mail/Export/Feltöltés sort |
| [racs-nagyito.md](racs-nagyito.md) | **A rács-NAGYÍTÓ** — kör alakú üveglencse **103 × 103** (belső 65), a `loupe_sm` a **belső rétege** (51 × 51); a kurzor **közepére** ül; **áttűnéssel** jelenik meg (0,4 be / 1,2 ki, alfa 1…256); **nincs saját egérmutató** (mért negatív); nálunk a réteg megvan, a **kapcsoló hiányzik**; **nincs nagyítási arány** — a teljes méretű kép **1:1**-es, 161 × 161-es kivágata a kurzor alatti képpontra középezve (`0x0077c445`, `0x0077bcf5`), nálunk viszont a bélyegkép zsugorítva (#2399) |
| [racs-ures-allapot.md](racs-ures-allapot.md) | **A rács ÜRES ÁLLAPOTA** — a `lightbox_bgtext` **hét** kontextus-szövege (ebből négy megnyugtató, nem hibaüzenet), a választó `0x00676b10` és a `LastUserESState`-től függő márkaváltás („Picasa Web Albums" ↔ „Google Photos"); és hogy a **„Keresés mindenhol" gomb HALOTT** az eredetiben (négy lekérdezés-alak + pozitív kontroll) |
| [biztonsagi-mentes.md](biztonsagi-mentes.md) | **A biztonsági mentés MŰKÖDÉSE** — `backups.xml` a **`db3`** mappában (`setname` · `diskroot` · `filter` · `type`), **három tartalom-mód** (`bkallfiles`/`bkonlypics`/`bkonlyexif`), a célmappába írt `files.txt`, a honosított alapértelmezett mappanév, a lemezhely-ellenőrzés — és hogy **ugyanaz a függvény írja a `replicates.xml`-t is** · ⭐ **2026-09-04 (14. szakasz): a `publish` sáv TIZENKÉT elemének SZERKEZETI HORGONYA** — a lap eddig teljes néven leírta őket, de `0x`-cím és `fájl:sor` nélkül, ezért a lefedettségi mérés feltáratlannak sorolta; most mind a 12-nek megvan a `respack.yt` eltolása, a geometriája és a `publish.tre` szülősora. ⚠️ **Csapda kimondva:** a `respack.yt` zárójeles rétegneve a tervezővászon **helyőrzője**, NEM a felirat — a három `label_rpoptionbox` mindegyikénél félrevezet (`Change Sync` helyett a valódi funkció **az online elemek eltávolítása**). Formátum-részlet: a `publish_text.tre:120` **`Tooltip1`** kulcsszóval deklarál |
| [ajandek-cd-kimenet.md](ajandek-cd-kimenet.md) | **Az Ajándék-CD / mentő lemez KIMENETE** — a lemez **önjáró**, Windows ÉS macOS vetítővel és visszaállítóval, telepítővel és letöltő-linkkel; az `autorun.inf` **pontos sablonja**; a **16 kimeneti beállítás** teljes listája; és hogy a lemez mappanevei **honosítottak** („Biztonsági mentés" / „Képek"). ✅ **2026-09-03 — a HÁROM ÜZEMMÓD szétválasztva** (#2095): a panel `+0x13e`/`+0x13f` bájtja dönt — `0/–` = **Ajándék-CD**, `≠0/0` = **biztonsági mentés lemezre**, `≠0/≠0` = **replikáció (feltöltés)**; a két bájtnak egyetlen írója van (a konstruktor, `0x0066bf90`), és ugyanaz választja belőlük a `publish/presentcd_go` / `backup_go` / `replicate_go` vezérlőnevet. Üzemmódonkénti alapérték-tábla a 12.4-ben; a méretfokozatok **eredeti / 640 / 800 / 1600**; a replikációs módban **nincs kiadás-gomb**. Két helyesbítés: az `option_backup` a mentés-ágon **1** (nem 0), és a 16 `option_*` tagoffszet a **motorobjektumhoz** tartozik, nem a 984 bájtos panelhez. |
| [konyvtar-ablak-meretek.md](konyvtar-ablak-meretek.md) | A könyvtár-ablak (156 elem) |
| [picasa-konyvtar-eszkoztar-viselkedes.md](picasa-konyvtar-eszkoztar-viselkedes.md) | A fő eszköztár öt gombjának VISELKEDÉSE (Import, Új album, nézetváltó pár, Nézet-beállítások, Webkamera) — nem geometria |
| [jobb-fiok-meretek.md](jobb-fiok-meretek.md) | A jobb oldali fiók („Metaadatok", 80 elem) |
| [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) | A fő ablak elrendezése — a forrásból; **és a MEGŐRZÖTT állapot** (2026-09-03): `Preferences/mainwinpos` = `rect(%ld %ld %ld %ld)` + `mainwinismax`; az induláskori állapot-alkalmazó `0x0040bf70`; a `HLISTDIV=0.216406` / `VLISTDIV=0.1` **beírva, de SOHA nem olvasva** (három független negatív) — csapda, ne valósítsuk meg; a bal panel osztója a `HLISTOFFSET2=240`, ami **kódból is** megvan (`0xcf48b0`), és a kezelőjében (`ytSplitterOffsetHandler`, `0x009d9d80`) **nincs beégetett alsó/felső határ** · **2026-09-04 (#2305): az alsó sáv JOBB SZÉLE** — mért sorrend `scale_group` (366…525: `loupehit` 25 + `scalecontainer` 127) → `metadata_group` (545…785, 4 × 60); és három NEGATÍV eredmény: a négy panelkapcsolónak **nincs `Label` sora** (csak `Tooltip`), a csúszka mellett **nincs `−`/`+` gomb** (a 159 képpontot a két gyerek pontosan kitölti), és a két nagyítás-gomb **`editpanel/`-elem**, nem ide való · ⭐ **2026-09-04 (#2329): a könyvtár OSZTÓSÁVJA** — `hlistsizer` + `hlisthandle` (`thumbui.tre:512–520`), kezelő `ytSplitterOffsetHandler` (RTTI `0x00d4734c`, gyártó `0x009da130`). A **240** nem csak alapérték, hanem az **alsó korlát** (`0x009d9df6`), a felső pedig **panelszélesség − 240** (`0x009d9e31`) — ugyanaz a konstans (`0x00cf48b0`) mindkét oldalon, és ugyanez az osztály viszi a függőleges osztót is. ⛔ **Kimerítő negatív: az állása NEM őrződik meg** — a `HLISTOFFSET` egyetlen alakban sem szerepel a binárisban, a `hsplitoffset`-re pedig pontosan egy kódhivatkozás van (a saját név-visszaadója), miközben a fiókok `RIGHTDRAWEROFFSET`/`LEFTDRAWEROFFSET` eltolása igenis megőrződik. ⚠️ Nálunk a legkisebb 160, a legnagyobb fix 600 · ⭐ **2026-09-04 (#754): a `varbutton` KEZELŐ megfejtve** — a felület minden ki-be kapcsolható részét ez mozgatja (11 felhasználás, mind jelentéssel). Nyelvtan `%s %f %f %d %s %s` (`0x00cda73c`), osztály `ytVarButtonHandler`, gyártó `0x009da240`; a 2. érték alapértéke a **−1000-es őrszem** = „engedéskor állítsd vissza az eredetire", az animálás-jelzőé **1** = **0,4 s** átmenet (`0x00cf4ce0`). A **jobb fiók 280**, a **szerkesztő bal panelje 279** képpont; a teljes képernyős mód hat változó egyidejű nullázása, animáció nélkül · ⭐ **2026-09-04 (#440/#2074): a főablak MÓD-GÉPE** — a `macros.tre` 192–300. sora külön `MODE MACROS` blokk: nyolc mód, mindegyik teljes mutat/rejt listával, és a három publikáló mód (Ajándék CD · Mentés · Replikáció) **ugyanazt a hármat rejti el**: keresősáv, alsó él-díszítés, logó. Három makró (`m_webcontrolset_enable`, `m_collage_enable`, `m_search_disable`) **definiálva van, de egyetlen `.tre`-elem sem viseli**. A `thumbui/backup` `m_hidden` — a forrás megjegyzése szerint is. ⚠️ **20 elem `m_render_offscreen` = XConstraint −9999**: parancs-proxik, sosem látszanak — a lefedettségi mérésben nem hiányzó vezérlők · ⭐ **2026-09-04 (#2344): a WebP-kérdés eldőlt** — a Picasa 3.9 **indexeli** a WebP-t (`SupportWEBP` alapérték **1**; `.webp` `0x00467ca0`, `*.webp;` `0x00520220`; és a tulajdonos valódi `thumbindex.db`-jében **van** ilyen fájl). ⛔ Ezzel **megdőlt** a `scanner/filetypes.py` fejlécének állítása, hogy „a Picasa nem támogatta" — a `.webp` hiányzik a szűrőnkből, tehát némán eltűnnek ezek a képek. ⚠️ Külön, NEM mért kérdés: a `SupportGIF`/`SupportPNG` alapértéke **0**, a katalógusban mégis 125 PNG van · ⭐ **2026-09-04 (#2344): a `Support*` kapcsolók HATÓKÖRE** — mind a **négy** olvasó megnevezve (`0x00520220` a `CAcquireUI` fájlszűrője, `0x0051ceb0` az importálás maszkja, `0x004e04a0`, `0x004183c0` az indulási/adatbázis-ág), a kulcsnevek adatcímeivel együtt. ⇒ mind az **importálás/megnyitás** vagy az **indulás** ágán ül ⇒ a kapcsoló nem egyszerűen „bekerül-e a katalógusba". ⚠️ NYITVA: megnézi-e a **figyelt mappák pásztázása** ezt a maszkot · ⭐ **2026-09-04 PONTOSÍTVA: a `Support*` kapcsolók a FÁJLTÍPUS-TÁBLÁT építik** — a lánc mérve: `0x00402f90` → `0x004183c0` → `0x004e04a0` (12 kapcsoló) → `0x004fadb0` (**30 bejegyzéses ugrótábla**, `0x004fb948`) → `0x004fa590`, amely a kiterjesztés-sztringeket (`.jpg` `0x00c80a50`, `.jpeg`, `.jpe`, …) egy objektum **`+0x3dc`/`+0x3e0`** mezőjébe fűzi. Vagyis nem csak az importáló párbeszédé. ⚠️ NYITVA: a **figyelt mappák pásztázása** ebből a táblából dolgozik-e — a folytatás a `+0x3dc` tömb OLVASÓINAK keresése · ⭐ **2026-09-04 LEZÁRVA: a pásztázó modul a `Support*`-tábla alapján sorol be** — a táblát a `CChangeLogger`/`Dirscanner` modul objektuma tartja (`+0x3dc` tömb, `+0x3e0` csomagolt elemszám); az író thunk `0x004e3670` UGYANENNEK a modulnak a metódusa, az olvasó `0x004e2c40`: kiterjesztés `0x004e2a00`-val (`strrchr` `.`), kis-nagybetű-független összevetés `0x00bf697a`-val, találatnál a párosított típusérték, egyébként **`0x3e8` = 1000** |

## Felület — auditok és lefedettség

| lap | miről szól |
|---|---|
| [ui-audit-editor.md](ui-audit-editor.md) | A szerkesztőpanel: fülek, effekt-csempék, dialógusok |
| [ui-audit-mainwindow.md](ui-audit-mainwindow.md) | Főablak: mappafa, eszköztár, tálca, görgetősáv |
| [ui-audit-menus.md](ui-audit-menus.md) | A teljes menürendszer |
| [ui-audit-context-menus.md](ui-audit-context-menus.md) | Jobbklikkes helyi menük |
| [ui-lefedettseg.md](ui-lefedettseg.md) | Az eredeti panelek ↔ a mi QML-fánk megfeleltetése · ⛔ **2026-09-05: a KUTATÁSI axis KIMERÜLT.** A `ui-lefedettseg-elemek.csv` 173 tétele: **120 `megvan` · 49 `lekutatva` · 3 `nem-cél` · 1 `hiányzik`** ⇒ **nulla feltáratlan elem**. A megmaradt 49 `lekutatva` tétel **megvalósítási**, nem kutatási hiány (panelenként: publish 12, makemoviepanel 9, editpanel 7, keywords 5, thumbui 5, video_control_bar 3, outputlayout 2, searchoptions 2, video_control_bar2 2, searchcontainer 1, printpanel 1), az egyetlen `hiányzik` (`thumbui/hviewtoggle` — `thumbui.tre:406/412/415`, a folderview+flatview gombpár tartója) pedig a #1421/#1454 alatt fut. ⇒ **Kutatói kör ebből az axisból már nem tud témát venni** — a `00-index` nyitott kérdései és a lapok BLOKKOLT tételei a következő forrás. |
| [picasa-beviteli-mezok.md](picasa-beviteli-mezok.md) | Beviteli mezők és párbeszédpanelek |
| [picasa-gyorsbillentyuk.md](picasa-gyorsbillentyuk.md) | **A gyorsbillentyűk teljes tára ÉS a funkciójuk** — a `Picasa3i18n.dll` 48 rekeszes `SHORTCUTS.XML` keymapje (nyolc nyelv, **magyar nincs** → az angol alaptábla fut); a menüsáv 32 és a helyi menük 44 rekordja **parancsazonosítóval és rekordcímmel**; a jelzőbájt három bitje mérve (a 2. bit fordított: `Ctrl` akkor van, ha 0); a keymap kommentjei **három helyen elavultak** (`Ctrl+S`, `Ctrl+T`, `Ctrl+W`); és a mai kiosztásunk tételes összevetése (34 egyedi kombinációból 18 megvan / 2 eltér / 14 hiányzik). Jegy: **#1154** |

## Viselkedés és funkciók

| lap | miről szól |
|---|---|
| [picasa-create-features.md](picasa-create-features.md) | A „Létrehozás" menü funkciói |
| [picasa-kollazs-felulet.md](picasa-kollazs-felulet.md) | A Kollázs teljes működése — parancstábla, gyűrű, helyi menük, kimenet |
| [kollazs-atvilagitas.md](kollazs-atvilagitas.md) | **A Kollázs TELJES átvilágítása** — eredeti / nálunk / jegy minden vezérlőre, a panelen kívüliekkel; és kimondva, amit NEM néztünk meg. *(2026-08-21: a 9. szakasz átvizsgálva — két tétel ELAVULT volt (a lap 1. szakasza már lezárta őket), a `.cxf` visszaolvasása MEGMÉRVE (`CCollageParser`, a mi olvasónk lefedi a teljes szótárt); valóban nyitott már csak a **futó program** viselkedése és a **betöltési sorrend nagy albumon**.)* |
| [kollazs-panel-ui-spec.md](kollazs-panel-ui-spec.md) | **A Kollázs-panel MEGVALÓSÍTÁSI UI-specifikációja** — elemfa, `objectName`-ek, a `.tre` kényszereiből levezetett méretezési törvény, vezérlő-API, teszt-szerződés, jegyekre bontás |
| [export-parbeszed.md](export-parbeszed.md) | **Az „Exportálás mappába" párbeszéd** — a `export.fen` leíró, mind a 28 magyar felirat, a kötések, a 9 megőrzött beállítás, és a képminőség öt fokozatának **számértéke a binárisból** |
| [kollazs-eletciklus.md](kollazs-eletciklus.md) | **A kollázs életciklusa** — a három állapot, az átmenetek, mindhárom párbeszéd szó szerint |
| [picasa-bezaras-es-kilepes.md](picasa-bezaras-es-kilepes.md) | Mit zár be az „X" — bezárás és kilépés; a kilépési kapu 8 lépése, a négy kilépési figyelmeztetés (feltöltés, import, aktív szerkesztő-eszköz, `WarnClosePlugins`), minden bezáró gomb névparancsa, kilépéskori mentések. Nyitva: az `exit_nag` kapcsoló hatása |
| [picasa-nyomtatas.md](picasa-nyomtatas.md) | A nyomtatás — panel (61 elem), 17 méret, beállítások; a printoptions-elemtábla **szerkezeti horgonyt** kapott (`printoptions.tre` / `printoptionstext.tre` sorszámok), ettől 12 eleme kikerült a „feltáratlan" listáról · ⭐ **2026-09-04: a kis-kep kuszob KIMERVE** — `Preferences\DPIWarning`, **alaperték `0x96` = 150** (`0x0085c08b` → `0x00407a20`); a minimum-keresés magva `1000000.0` (`0x00cf4900`), és az állapotsor `0x00745d15`-nél `cmp esi, 0xf4240`-nel hagyja ki a legkisebb-kép sort. A Review/Ready váltás **darabszám-alapú** (`0x00745d5c`), nem DPI-alapú ⇒ ezért van két gombpár a `.tre`-ben. ⚠️ NYITVA: hova navigál a `printpanel/froogle` gomb · ⭐ **2026-09-04: a `printpanel/froogle` gomb LEZÁRVA** — a kattintás `0x00743980` (`0x007444a4`) → **`0x00744750`**: a kiválasztott nyomtató nevét megerősítés után (`ThumbUIPrint::FrooglePrompt`, igen/nem `0x009bac20`) elküldi a **`https://uploader.picasa.com/froogle.php?q=%s`** címre kellék-keresésre. **Javaslat: NE építsük meg** (megszűnt szolgáltatás). ⛔ Önhelyesbítés: a `0x00744a00` NEM a kezelője — ott csak egy általános elem-metódus (`[+0x68]`, a binárisban 181 helyen) fut rá · ⭐ **2026-09-04: két REJTETT nyomtatási beállítás** — `PrinterQuality` (`0x00ca9a18`, alapérték **2**) és `PrinterUseTiles` (`0x00cb0cb4`, alapérték **0**); a panel „optimalizált” állapota (`0x00745f80`) csak `PrinterQuality != 1001` ÉS `PrinterUseTiles != 0` esetén igaz ⇒ **alapból a normál gomb** látszik. Az író `0x00746060` mindkettőt kiírja és azonnal alkalmaz (`0x008613b0`). A `PrinterQuality` a nyomtató **`GetDeviceCaps`**-lekérdezésébe jut (IAT `0x00c40108`; indexek 10/88/90/110–113). ⛔ **Kimerítő negatív:** a `PrinterUseTiles`-nak csak **2** hivatkozója van, mindkettő a panelben · ⭐ **2026-09-04: az INDEXKÉP három belépési ponton él** — nyomtatási méret (`ytPrintSizes::eContact`, panelgomb `printpanel/photoindexbutton`), kollázstípus (`contactsheet`, `0x0082e8b0`) és menüparancs (`eMenuLabelFolder::ID_FILE_PRINTCONTACTSHEET`, `0x00559150`). A hivatalos magyar felirat mindenütt **„indexkép"**, soha nem „bélyegkép" — a menüé **`&Indexképek nyomtatása...`**. Kuriózum: a `0x0057b050` **`ginormous.jpg`**-t ír és megnyitja, de a szövegkulcs névtere `UNUSED!` · ⛔ **2026-09-04 ÖNHELYESBÍTÉS + összevonás:** a lapon **két froogle-szakasz** és két, egymásnak ellentmondó `phelpbutton`-állítás állt. A 09-04-i körök részben ÚJRA levezették a 09-03-i szakaszt; a `phelpbutton`-t tévesen „letiltott vezérlőnek" mondták — **maga az elem NEM kikommentezett**, csak az ikonja/felirata/színe/horgonya (`vbutton`, rajz nélküli találati terület). A duplikátum összevonva, a kattintás-út (`0x00743980` → `0x00744750`) megmaradt kiegészítésként · ⭐ **2026-09-04: a panel INFORMÁCIÓS mezői** (`0x00745980`) — `IDS_COPIES` (azonosító `0x3b` = 59) → `numberprints`; `ThumbUIPrint::PrintCount` = `%d of %d` → `previewnumber`; `printername`; `paperinfo`; `statustext`; a lapok száma `[esi+0x18]>>1`, és az aktuális index **lapszám−1-re korlátozódik** (`0x00745b73`). A segédfüggvények csoportosítanak: `0x009cd870` = szövegbeállító, `0x009cd110` = gomb-állapot. ⚠️ Nálunk a **`paperinfo` kijelző hiányzik** |
| [picasa-email-kuldes.md](picasa-email-kuldes.md) | E-mail-küldés — választó, beépített Gmail-szerkesztő, beállítások; **6.: a beállítások TÁROLÓJA** (`HKCU\SOFTWARE\Google\Picasa\Picasa2\Preferences\`, hét alszekcióval) és a `choose_mail` írási szabálya (#2184) |
| [picasa-importalas.md](picasa-importalas.md) | Az importálás panelje — tipp-sor, kártyatörlés-figyelmeztetés, hibák |
| [picasa-elso-inditas.md](picasa-elso-inditas.md) | **Az első indítás `initialscan` panelje** — migrációs és tiszta-telepítés változat, geometria, a kihagyhatatlan választás |
| [lanc-szakadasok-leltar.md](lanc-szakadasok-leltar.md) | **Ahol a háttér kész, de a felület nem éri el** — mért leltár: a regisztrált vezérlők közül egy sem holt, de több tucat tag elérhetetlen a QML-ből, jelentős részüket csak a teszt hívja. A pontos, mindig friss számot a lap generált blokkja és a `scripts/kepesseg_or.py` futásának kimenete adja — ide szándékosan nem írjuk ki (#1508, #1512). Négy megerősített lelet (Nyomtatás · arckeresés-indítás · e-mail küldés · visszavonás-gombok) és a naiv `.tagnév` keresés csapdája (négy név két gazdával). Jegyek: **#1472**–**#1476** |
| [nema-tagok-1052.md](nema-tagok-1052.md) | **A #1052 huszonhat néma vezérlő-tagjának döntése** — tagonként HIBA / SZÁNDÉKOS / HALOTT, kétféle alakú kereséssel igazolva. A jegy **„gomb aktív állapota" feltevése MEGDŐLT**: a #116 az egygombos javításokról szándékosan levette a „benyomva" állapotot, a csempe a `*Enabled` párt köti — a három `*Active` property maradék. Egy új, felhasználót érintő lelet: a vágás „Alaphelyzet" gombja csak a KIJELÖLÉST törli, a mentett vágást nem. Négy tag azóta bekötést kapott (#1472, #1473), egy soron a jegy tévedett (`setSimplified`). Jegy: **#1052** |
| [picasa-szinkereses.md](picasa-szinkereses.md) | **A hat szín szerinti keresés MEGFEJTVE** — NEM az átlagszínt osztályozza: telítettséggel súlyozott **hue-hisztogram** az egész rasztról, hét vödörrel, a legnagyobb nyer (`0x009dbd10`). Küszöbök: `MAX==0` és `S<=50` képpont kimarad; `b=H/10`; mért **rés** 353,0–358,8°-nál; akromatikus ⇒ mind a három token. Jegy: **#1480** |
| [picasa-tartalomkulcs.md](picasa-tartalomkulcs.md) | **A tartalom-kulcs (`originfast`) — 10/10 igazolva** valódi fájlokon: `MD5(uint32_le(méret) ‖ első 16834 bájt ‖ utolsó 16834 bájt)` első 8 bájtja. Három téves jelölt mérve kizárva (`onlinechecksum` u32, `originhash` 0/32, `backuphash` u16). ✅ **2026-09-04 — a PMP-oszloptábla regisztrációja kiolvasva** (#1482): `originslow` **`+0x9d8`**, `originfast` **`+0xa40`** (a `+0x978` a `revertable`), és a kettő **ugyanaz az oszlop-osztály**; a bájt- és az u64-oszlop a vtable 11. résében tér el. Mért negatívum: a két tagot a teljes binárisban csak a regisztráló és a destruktor érinti ⇒ **az érték-írás nem literális tagoffszeten megy**, az `originslow` képletét ne ott keressük. ✅ **2026-09-05 — az `originslow` MEGFEJTVE ÉS MEGMÉRVE (#1482): `MD5(teljes fájl)[0:8]` kis-endián, 18/18** valódi fájlon. A hasher `0x00a4ce40` (64 KB-os stream); az EGYETLEN előállító a `0x004353a0` — a diszpécser (`0x00a4cd00`) csak akkor számolja, ha a hívó ad neki célt (`test edi,edi`, `0x00a4cd3d`), és a másik hívó (`0x0070e080`) ezt `xor edi,edi`-vel kikapcsolja (`0x0070e594`). ⛔ A korábbi „0/4"/„0/8" negatívumok **mintahibák**: olyan sorokon mértek, ahol a fájl azóta megváltozott — kontrollal (a saját `originfast`) ez azonnal látszik: véletlen sorokon a fast 24/25, a slow-os sorokon 1/70, és a 70-es keresztáblában NULLA az ellenpélda. Szerepe MÉRVE: a gyors kulcs **ütközésfeloldója** — ütköző `originfast` mellett 46,8%, egyedi mellett 1,65% (**28,5× dúsulás**), és ahol jelen van, 4352 értékből 3407 különböző. Ez összecseng a #1648-cal (a másolat örökli a forrás `originfast`-ját). Jegyek: **#1481**, **#1482 (LEZÁRVA)** |
| [picasa-mappanezet.md](picasa-mappanezet.md) | **A `Nézet ▸ Mappanézet` MŰKÖDÉS-specje — egy funkcionális félreértést javít**: ez NEM rendezés, hanem a bal hasáb **gyökere és hierarchiája**. A lapos↔fa **kizáró pár** (`[+0x9d]`), az „Egyszerűsített fanézet" viszont **független kapcsoló**, ami a `SimplifiedHierarchy` beállítással az `all` gyökeret **`watched`-re cseréli**. Hat gyökér-token, négy gyökér a helyi menüben, a fejlécfelirat („Alapértelmezett nézet" / „Sajátgép"), a `LastViewRoot`/`LastViewRoot2` tárolás, és a visszaesés a Sajátgépre hibaesetben. Jegyek: **#1407**, **#1454** |
| [picasa-mappakezelo.md](picasa-mappakezelo.md) | **A Mappakezelő TELJES specifikációja** — elrendezés és tervezővászon-geometria, az átméretezés szabályai (`winsize` → `SC_SIZE`), a fa és az öröklődő állapot, a három rádió, az arcfelismerés-kapcsoló, a három figyelmeztetés, az OK/Mégse delta-szemantikája, a Súgó URL-je |
| [picasa-keptalca.md](picasa-keptalca.md) | **A Képtálca (`scratch`, „Selection") MŰKÖDÉS-specje** — a döntő lelet, hogy a tálca **nem marad meg újraindítás után** (három független negatív ellenőrzés); a négy vezérlő felirat NÉLKÜL, csak ikon+súgó; a helyi menü **nyolc sora** (ebből csak kettő a `Tray::` névtérből); a bélyegképek **négyzetesek és középre vágottak** (16 mért eset, a méret-képlet NINCS MEG); a `scratch` a `scratchlabel` FÖLÖTT; az összecsukott mappa-token; **két külön** ürítés-megerősítés; a 36,5%-os doboz-kényszer; a `trayexec` adatvezérelt műveletsor; két negatív eredmény (a `.pbz` placement NEM az alap-sorrend, a `Tray contains:` hibakereső lap); **a rács osztásköze a két irányban AZONOS** (a #1914 „3 px sor / 0 px oszlop" kérése megdőlt, 18.); **a kimeneti gombsor (`outputlayout`) egyetlen 55 × 36-os cellasablonból épül**, és van benne túlcsordulás-gomb („További lehetőségek…"), ami nálunk hiányzik (21., #2191); **a mappa-token teljes feltárása** — típustesztes kiváltó, négy felirat, mért geometria, és hogy a token és a bélyegkép-rács KIZÁRJA egymást (20.) |
| [picasa-helyek-panel.md](picasa-helyek-panel.md) | **A Helyek panel (geocímkézés) MŰKÖDÉS-specje** — a `geotag=` kulcs alakja **kimérve** (`%lf,%lf`, mindig **hat tizedesjegy**; a korpusz 84/84 sora 6/6 jegyű) és a mi `format_geotag()`-ünk **19/84 (22,6%) értéket másképp írna** (→ **#2012**); a **két megerősítő kérdés MÉRT küszöbökkel** — hely megváltoztatása **> 20 kijelölt** elem (`0x00652585` `cmp ebx,0x14`), hely törlése **> 5 GEOCÍMKÉZETT** elem (`0x006527ad` `cmp esi,5`, a számláló `0x006524c0`) —, nálunk **egyik sincs** (→ **#2013**); a törlőgomb felirata **dinamikus** (`Clear %d Geotag(s)`); a beágyazott Google-térkép **kétirányú JS-hídja** teljes táblával (11 natív→JS hívás és a `geotag:` / `cleargeotag:` / `showphotos:` visszaút, mind **ellenőrzőösszeggel**, a parancskezelő a `0xca2470` vtable-ben); a buborékablak 12 felirata, köztük a **külön „Move" és „Put"** szöveg; és két negatív lelet: **a `picasa.setMapType` a v3-as szkriptben ÜRES FÜGGVÉNY** (a mentett térképtípus némán hatástalan — a v2-ben még működött), illetve a panelnek **nincs `respack.yt`-geometriája** |
| [picasa-metaadat-tulajdonsagok.md](picasa-metaadat-tulajdonsagok.md) | ⭐ **ÚJ (2026-09-05, #2375): a Picasa metaadat-kulcstere TELJES egészében.** A Picasa a kép EXIF/IPTC adatait **egyetlen, egész számmal kulcsolt szótárba** olvassa (`BinaryMetadata`, RTTI `0x00d402b4`; `GetString` = `0x009f05c0`, 143 hívási hely a `.text`-ben), és a program mindenhonnan ebből kérdez. ⭐ **A kulcs = a tulajdonságtábla `id` mezője + 1** — négy független hívási hely dönti el, a legerősebb a geocímke-hármas (`0x009f15e5`: `0x8c`/`0x8e` a SZÖVEGES lekérdezőn = GPSLatitudeRef/GPSLongitudeRef ASCII[2], `0x8d` a SZÁMSOROS `0x009f1250`-en = GPSLatitude RATIONAL[3]); a `+1` nélküli olvasat mindegyiken rossz lekérdezőt adna. **Teljes tábla kiírva:** 176 EXIF/TIFF-bejegyzés (`0x00c782f0`, 28 bájtos rekordok) + 55 IPTC-bejegyzés (`0x00c77c24`, 20 bájtos rekordok, a szabványos hosszkorlátokkal — 2:120 max 2000, 2:122 max 32), névtér-enummal (0 = IFD0, 1 = Exif, **2 = üres**, 3/4/5 = gyártói jegyzet *feltételesen* Canon/Nikon/Olympus, 24 = GPS, 25 = Interop, 26 = IFD1). ⭐ **A #2304-re:** a `0x37` = EXIF **`0x9003` DateTimeOriginal** (nem a szomszédos `0x9004` DateTimeDigitized!), a `0x68` = `0xa420` ImageUniqueID, a `0xe4` = **IPTC 2:120 Caption/Abstract**. ⛔ **Négy IPTC-sor ÜTKÖZŐ `id`-t visel** (2:60 és 2:62 → 55, 2:63 és 2:65 → 56, 2:85 → 29, 2:118 → 40) ⇒ ugyanaz a belső tulajdonság több forrásból is feltölthető. ✅ **MIT AD MA:** mind a négy vizsgált mezőt a `metadata/reader.py` **ugyanazon a címszámon** olvassa (`:41` 36867, `:59` 42016, `:63` (2,120), `:42–43` Make/Model) ⇒ **termékteendő nincs**. Jegy: **#2375** |
| [picasa-menu-leltar.md](picasa-menu-leltar.md) | **A menüsor gépi leltára a binárisból** — 189 tétel 18 `eMenu*` névtérben; a lefedettségünk 150/189 (79%), a 39 hiányzó három csoportban (14 hatókörön kívül, 18 érdemi, 1 almenü). Jegy: **#1397** |
| [picasa-menu-parancsok-viselkedes.md](picasa-menu-parancsok-viselkedes.md) | **A menüparancsok VISELKEDÉSE** (#1434) — a `.fen` párbeszédleírók mint leggyorsabb út; az effektus-vágólap **nem** rendszer-vágólap; a dátum-állítás **nem** fájlidőt ír; a menüsor **kilenc almenüje**; a Beállítások 8 füle és ~78 vezérlője (köztük a nyomtatás **Lanczos-3/8** választása); a Személyek kezelése hat azonosító-mezője; és a beállítások tárolási helye (`SOFTWARE\Google\Picasa\Picasa2\Preferences\`). **33. tétel (2026-08-30): a KÉP menü teljes cmd→kezelő térképe** (16 + 4 geotag-parancs, a kép-menübeli Szépia/Fekete-fehér `0x9d4a`/`0x9d4c` külön batch-parancsok), a Csoportos szerkesztés **kétágú mintája** (szerkesztő-navigáció `0x579330` vs. batch `0x5fe370`), a FILM_GRAIN **Shift-függő grain/grain2** váltása (`GetAsyncKeyState(0x10)`), az AUTO_REDEYE keret-útja (`0x602100(0x5f39d0)`), és a Geotag almenü: Google Earth-ellenőrzés CLSID-vel + InstallEarth-párbeszéd, a GEOUNTAG megerősítője (`ClearGeoTag::warn`). **34. tétel (2026-08-31): az öt lefedettségi parancs** — forgatás (fix 90/270°, háttérszálon, `rotate=` = negyedfordulat-tároló, **#1162 lezárva**), Undo All Edits (egy/több/film megerősítés-hármas, `redeye`/`retouch`/`picnik` token-törlés), Unhide/Hide (`hidden=yes` kulcs, online-album-megerősítés), Reset Faces (sima = kijelölés, kérdés nélkül; Ctrl/Shift = könyvtárszintű FIGYELEM-párbeszéd). **35. tétel (2026-08-31): Poszter (papírméret-lista nyelvi feltétellel), képernyővédő (saverlist.txt a #db3 mappában, telepítés-ellenőrzés, rundll32-install), TiVo (Windows-only akció — hatókörön kívül-javaslat), keresés-mentése (1000-es küszöb, „Create Album" gomb), biztonsági mentés (backup.xml + backuphash + il_BurnPanel). **36. tétel (2026-08-31):** a névcímke-letöltés **halott menütétel** (`RemoveMenu` feltétel nélkül); a Mappakezelő **engedélyezési kapuja** (szürke, amíg a szerkesztő-előnézet aktív) és a `+0x34a4` holt jelzőbit; a lista-rendezés **három registry-kulcsa** (`datesort` = teljes módszám, `peoplesort`, `albumlistflip`), a „méret" = **64 bites bájtösszeg**, és hogy a rendezés-tételek **három menüben** élnek (a menüsáv Nézet menüjében is — a #1454 megjegyzésének helyesbítése). **37. tétel (2026-08-31):** a jobb fiók négy lapja **kizáró rádiócsoport** (minden ág elrejti a másik hármat), a menü→névparancs híd (`0x0065ab50`), az `ID_CAPTAG` **két menüben két külön azonosítóval** (`0x9d2c` vs `0x9de4`), és az `active_metadata_tab` kulcs, amelynek **három olvasója és nulla írója** van. **38. tétel (2026-08-31):** a „Rejtett képek" bekapcsolása **jelszót ajánl** (`IDS_PROMPT_HIDDEN_PWD_*`, „Add Password"/„Don't Add Password", `DoNotConfirmHiddenPwd`); az Idővonal **teljes képernyős bemutató-mód** a Flipbookkal közös kezelőn; a háttérkép **BMP-t ír** a `Picasa\Backgrounds`-ba és **középre** teszi (`WallpaperStyle=0`, `TileWallpaper=0`). **39. tétel (2026-08-31, az első UI-lefedettségi kör):** a `printoptions` panel **tizenegy `Preferences\printoptions::*` kulcsot** ír (felirat forrása/helye/betűje/mérete/színe/tördelése, szegély megléte/vastagsága/színe/csak-alul/egyenletes); a fogyasztó a nyomtatási rajzoló (`0x00776180`); indexkép-nyomtatásnál a panel **tiltva**, saját magyarázó szöveggel. **39.8 (2026-09-03):** a panel **felirat-rétege külön fájlból** jön · ⭐ **2026-09-04 (67. tétel, #2304) — a 36. tétel KIEGÉSZÍTÉSE, önhelyesbítéssel:** a rendezésnek van egy **negyedik belépési pontja** (a könyvtár-nézet két gombja: `thumbui/datesort` → mód **0**, `thumbui/namesort` → mód **2**), a komparátornak egy **negyedik módja** (`4`, `0x004a7e2a`, vezérlő nélkül), és a szempontváltás **megtartja a fordított sorrendet** (`FUN_004b07c0` mindkettőt egyszerre veszi). ⛔ A tétel első változata négy dolgot MEGISMÉTELT a 36.-ból, a Méret mód-számát pedig tévesen NINCS MEG-nek jelölte — **a 36.4 szerint 5**, és a mértékegysége 64 bites bájtösszeg · ⭐ **2026-09-04 (68. tétel, #2320) — a mód-készlet TELJES:** a `+0xd8`-nak **két** írója van (a validálás nélküli registry-betöltő és a `FUN_004b07c0`), és a hívóláncuk kimerítően felsorolva ⇒ a felületről elérhető készlet **{0,1,2,3,5}** + a fordítás-váltó (`0x005cd61c`, `sete cl`). ⭐ **Ötödik mód: 3** (`0x005cd5f2`) — a 36.3 listája ezt sem tartalmazta —, és a komparátor a **2-vel azonosan** kezeli. ⛔ **A 4. mód a felületről ELÉRHETETLEN**: egyetlen hívó sem ad át 4-et; csak kézzel írt `datesort=4` registry-értékkel lépne működésbe ⇒ **nem megépítendő**. ⭐ **A névhasonlítás ASCII-only kisbetűsítést végez** (`A`–`Z` + 0x20, `0x004a7fda`) ⇒ az ékezetes nagybetűk NEM esnek egybe a kisbetűs párjukkal; nálunk `casefold()` (Unicode) van (`models.py:347`, `photo_sort.py:74`) — lehetséges oka a #2304 sorrend-eltérésének, de ok-okozatilag NINCS bizonyítva · ⭐ **2026-09-04 (69. tétel, #2304): a mappa-tartalom „Dátum” rendezésének KULCSA** — mérve a tulajdonos valódi katalógusán: a `thumbindex` rekord **1. FILETIME**-ja. A **fájlnév mint kulcs KIZÁRVA** (0/18 egyezés), a tárolt időbélyeg a jegyben rögzített **első tíz nevet pontosan** visszaadja, és csak az 1. FILETIME fésüli össze a névcsoportokat úgy, ahogy az eredeti. ⛔ **2026-09-05 HELYESBÍTVE (#2304):** a „nálunk EXIF-hiány esetén a mai `mtime` a tartalék” megjegyzés **eltérésként** olvasódott, holott az eredeti is a fájl módosítási idejére esik vissza (`pmp-database.md` 10.3–10.4) — a valódi különbség a **rögzítettség**: a Picasa a beolvasáskori értéket fagyasztja be és nem frissíti, mi minden rendezéskor élőben olvassuk · ⛔ **2026-09-04 HELYESBÍTVE (35.6, #440):** a `backup.xml` **NEM** a mentés-készletek könyve — a `0x0066f2b0` (438 b, 1 hívó) a **névjegyzéket** írja (`contacts.xml` + előző példánya `backup.xml`); a készletek a **`backups.xml`**-ben vannak a `db3\` alatt (`0x006759c0` / `0x00676910`). A `0x0066f470` sem a `backup.xml` kezelője, hanem a **16 `option_*` beállítás** tára |
(`i18n\printoptionstext.xml`, `0x0085d550`), és a fájl **kicsomagolva megvan**
(`referencia/i18n-hu/printoptionstext.xml`, 27 bejegyzés) — négy felirattal,
amit a lefedettségi lista nem nevezett meg (`border_size_label`,
`border_none_label`, `border_max_label`, `caption_color_label`);
⭐ **a szegélyvastagság CSÚSZKA** („Egyik sem" … „Maximális",
`printborderslider/scaleslider`, `Property slider 2`, saját névtérben a `root`
alatt), nem számmező; a két legördülő (`fontfamily`, `sizelist`) **runtime
töltődik** (`maxrows 7`, tételek sem a `.tre`-ben, sem az i18n-fájlban) ⇒ a
betűméret-lista blokkolt kérdése két további forrásra nézve negatív;
⚠️ **hibás hivatalos szöveg:** az `apply`/`ok` buboréksúgója
nyomtatás helyett **„a Google Fotókra"** hivatkozik — hogy fordítási hiba-e
vagy az angol is ilyen, **NINCS MEG** (angol i18n-csomag nincs a kutatási
anyagban); ezt a két szöveget **nem vesszük át**. Jegy-komment: **#1780**.
**39.3–39.7 (2026-09-02):** a **Mégse VISSZATÖLT** (a vezérlők azonnal írnak, az „Alkalmaz" csak újrarajzol, az ablak X-ével bezárva a módosítások BENT MARADNAK); a két rádiócsoport értékkészlete **0–3** (nincs szöveg/képfelirat/fájlnév/Exif) és **0–2** (kép alatt/képen/szegélyen); mind a tizenegy kulcs **alapértéke** kimérve (`textsize`=12, `bordersize`=10, **`evenborder`=1** az egyetlen bekapcsolt), a `.tre` `setpressed` értékeivel keresztmérve — egy eltéréssel (`wrap_checkbox`), ahol a **beállítás nyer**; ⛔ helyesbítés: a `usefilename`-nek **VAN** felirata („Fájlnév"); ⛔ negatív: a betűméret-lista **nem** a filmkészítő statikus táblájából jön. Nyitva: honnan töltődik a lista. **40. tétel (2026-08-31):** a `printpanel` **DPI-őrt** tartalmaz („Smallest picture: %d pixels/inch.", „%d small picture(s) found.", „Please review before printing."), a nyomatméretet a `Preferences\PrintLastSize` **tartósan** őrzi, a példányszám **képenkénti**, és a „Szegély- és szövegopciók" gomb nyitja a `printoptions`-t. **41. tétel (2026-08-31):** az `acquirepanel` importálás — `AcquirePath` / `LastImport%x` / `acquireUseSubFolder` kulcsok, az almappa-elnevezés **három módja** (kézi cím / „Date Taken (YYYY-MM-DD)" / mai dátum), kártya-törlés megerősítéssel; **és a lecke: a „hiányzik" oszlop JELÖLT, nem ítélet** — tíz elem téves riasztás volt. **42. tétel (2026-08-31):** a `collagepanel` megfeleltetési sora **elavult** volt (egyetlen fájlra mutatott, és azt állította, hogy nincs interaktív szerkesztő) — **egy sor 38 helyesen megvalósított elemet rejtett el**; javítás után a tábla 87 → 132 párosítva, 425 → 397 hiány. **43. tétel (2026-08-31):** a megfeleltetési fájl **mind a 74 sorának** átvilágítása — a `collagepanel` volt az EGYETLEN elavult (negatív eredmény); és a gyorscímke-beállító az eredetiben **TÍZ** helyet ad (`edit_0..9`, `cmp eax, 0xa`), nálunk nyolc. **44. tétel (2026-08-31):** a `buttonmgr` — a Picasa gombsávja **BŐVÍTMÉNY-RENDSZER** volt (`http://picasa.smo/buttons`, „Launch Picasa and import buttons?", `#buttons\` mappa); a testreszabás a `Preferences\Buttons\UserConfig` és `…\Exclude` kulcsokban él. **45. tétel (2026-09-01):** a mérés **VAK a csoportosztásra, a sorrendre és az elrendezésre** (az elválasztókat kidobja) — a „hiányzik = 0" csak annyit jelent, hogy *nincs hiányzó vezérlő*; plusz egy **tudott eltérések** táblája a kimondatlanság ellen. **46. tétel (2026-09-01):** a `faceheaderpanel` javaslat-munkafolyamata **négy külön parancs** (`selectsug`/`confirmsug`/`sug_filter`/`moresug`), és a „További javaslatok keresése" **újra-klaszterezés**, nem szűrő; a lelet a #26-ra ment, mert arcfelismerő motor nélkül nem valósítható meg. **47. tétel (2026-09-01):** a `choose_mail` levelezőprogram-választó (`EmailPrepType`, `DoNotPromptForEmailPref`) — **és egy NÉMA BEÁLLÍTÁS nálunk**: a „Let me choose each time" rádiógomb tárolódik, de a `sendRows()` nem olvassa el. **48. tétel (2026-09-01):** a **néma beállítás** mint önálló hibaosztály — a két meglévő őr (`nema_jelzesek.py`, `nema_slotok.py`) **mérve NEM fogja meg**; „a beállítás él, csak nem hat". **49. tétel (2026-09-01):** KÉT SAJÁT HELYESBÍTÉS — a `GetSubMenu(…,2)` a menü **fogantyúját** adja, nem a tétel helyét (#1766 leállítva); és a #1798 valódi oka nem a beállítás olvasása volt, hanem hogy a `sendRows()`-nak **nem volt hívója** ⇒ néma vezérlőnél a **teljes láncot** kell mérni, mindkét irányból. **50. tétel (2026-09-01):** a `publish` **HÁROM panel egy névtérben** (mentés · Ajándék-CD · webre töltés), és csak a harmadik halott; a mentés **nevesített KÉSZLETEKBE** szerveződik (új/szerkeszt/töröl, `LastBkSet`, „My Backup Set"); plusz: a Picasa **maga tudott a Wine-ról** (`wine_get_unix_file_name`, `ShowUnixPaths` hét helyen). **51. tétel (2026-09-01):** a `thumbui` hiányainak nagy része **ELHELYEZÉS-kérdés** (nálunk menüben, az eredetiben eszköztáron) — nyolc elem felülbírálva; a valódi hiány a **rács-NAGYÍTÓ** („Click and drag over photos to magnify them"). **52. tétel (2026-09-01):** a szerkesztő **kétképes módja** (A-A / A-B) — az A-A-ban a két példány **KÜLÖN szerkeszthető**, és kilépéskor a Picasa megkérdezi, melyiket tartsd meg („Choose Edits", Top/Bottom/Left/Right, `DoNotAskOnEnd2Up`); a lelet a #6-ra ment. **53. tétel (2026-09-01):** az `editpanel` **vágás / retus / vörösszem** füle — mind a tíz jelölt elem **téves riasztás**, nálunk megvan; sőt helyenként gazdagabb (egyenesítés-figyelmeztetés, egyéni képarány hozzáadása, régió-számláló). **54. tétel (2026-09-01):** a szöveg-fül nálunk teljes, de a **FELIRAT két vezérlője hiányzik** (`captionbutton` = elrejtés, `captiontrash` = törlés); a láthatóság **tartós** (`Preferences\LastCaptionButton`), és **két belépési pontja** van (szerkesztő + egyképes nézet) **55. tétel (2026-09-01):** a **finomhangolás** és az **effekt-fülek** — négy téves riasztás (`filllight_icon`, `droppertoggle`, `faces_button`, `filter_name` mind megvan); az egyetlen valódi hiány az **„Edit Movie" gomb**, ami a #432/#452 belépési pontja. **56. tétel (2026-09-01):** a `headerpanel` tíz eleméből **öt halott** (webes szinkron) és **öt élő**; valódi hiány a **`save_edits`** és a **`select_star`**; a fejléc gombjai **számlálós feliratúak** (`albumbutton_*%d`). **57. tétel (2026-09-01):** a `compose_mail` a Gmail-ághoz tartozik ⇒ **hatókörön kívül** (mérve, nem feltételezve), **de két élő részletet** hoz a #1798-ra: `Preferences\EmailAutocomplete` (címzett-kiegészítés) és a **„Preparing attachments…"** folyamatjelző. **59. tétel (2026-09-01):** a keresősávból **három szűrő hiányzik** (arcos képek, csak filmek, dátum-tartomány — ez utóbbi **CSÚSZKA**, nem dátumválasztó); és van egy eddig nem dokumentált, gazdagabb **`searchoptions`** réteg (hasonlóság-keresés mintaképpel, másodpéldány, gép szerinti szűrés). **60. tétel (2026-09-01):** a `searchoptions` feltárva — a **hasonlóság-keresésnek SAJÁT ADATBÁZISA** van („Updating similarity database (will be fast next time)") és **saját eredmény-albuma** („Similarity Search Results"); ez NEM ugyanaz, mint a mi másodpéldány-keresőnk. **61. tétel (2026-09-01):** a „rejtett vezérlőcsoportok" keresése — **NEGATÍV eredmény**: a leltárból hiányzó tíz csoportból kilenc **grafikai erőforrás**, a tizedik (`notifier`) már feltárva ⇒ a keresést nem érdemes megismételni. Melléklelet: a gombok **HÁROM állapotúak** (`_n`/`_h`/`_p`, 1252 erőforrásnév). **62. tétel (2026-09-01):** a névtelen/mellőzött arcok fejléce — két téves riasztás (a mellőzés és a kézi hozzáadás megvan), a névtelen↔mellőzött váltás pedig nálunk **albumon** át megy, nem fejléc-gombbal ⇒ tudatos eltérés a 45.3 táblában. **63. tétel (2026-09-01):** a címke-panel nálunk **teljes**, és a geocímke-párbeszéd `tagall` művelete is megvan (`setGeotagRows` a teljes kijelölésre) — a Google Earth-párbeszéd navigációja hatókörön kívül. **64. tétel (2026-09-01):** a **videó VÁGHATÓ** az eredetiben (`setin`/`setout`/`trimslider`, a vágáspontok a `.picasa.ini` `filters=` láncába kerülnek `moviestart`/`movieend` néven), és **képkocka menthető** belőle (`capture_frame`); nálunk a tokent **megőrizzük**, de beállítani nem tudjuk. **58. tétel (2026-09-01):** a webkamera-panel **KÉT rögzítési módot** ad (videoklip ÉS `snapshot` állókép), **külön kép- és hangforrást**, a klip **visszajátszását a panelen belül**, és tartós méretet (`Preferences\capturemoviesize`) — a tartalom a #853-hoz **58.5–58.6 (2026-09-02):** ⭐ a KIMENET is megvan — a felvétel a `<Képek>\Picasa\`**Rögzített videoklipek** mappába megy (ugyanaz a hármas lánc, mint a filmnél), a mappa **`.picasa.ini`-t kap** `P2category=Projects (internal)` sorral, **de csak létrehozáskor**; az állókép neve **`snapshot.jpg`**, és ütközésnél a **`%s-%03lu`** mintával sorszámozódik (`snapshot-001.jpg`) — ez **MÁS**, mint a kollázs/film `%s%lu`-ja —, legfeljebb 4096-ig; a videóból mentett **képkocka UGYANIDE** megy (`CCaptureFrame::CaptureFolder`, négy magyar állapotszöveggel); a panel kilenc állapotszövege és mind a tizenegy vezérlője **teljes névvel** kiírva. Élő minta: a korpuszban a `Captured Videos` és a `Rögzített videoklipek` egyszerre áll. |
| [picasa-megjelenitesi-modok.md](picasa-megjelenitesi-modok.md) | **A `Nézet ▸ Megjelenítési mód` almenü MEGFEJTVE** (#1409) — nem hat mód, hanem **tizenegy, egyetlen kizáró rádiócsoportban** (`0x00575670`); nincs köztük kapcsoló. Minden mód egy **képsoronkénti képpont-átalakító**, a `+0x254` horgon át, az ablak újrarajzolásakor. Mérve: a túlcsordulás-jelölés **csak a tiszta fehéret** festi **`#FF7F7F`**-re; a Projektor mód ×220/256, az LCD fehérpont ×246/256 (egyenletes sötétítés, színeltolás nélkül); a 16 bites szemcsézés MT-zaj +0…7/0…3/0…7 telítő összeadással; a Lineáris gamma egy **beégetett 256 bájtos LUT** (NEM `x^(1/2.2)`, hanem ≈ gamma 1,44) — a lap közli a teljes táblát. **A mód nem tárolódik**: minden indításkor „Automatikus”. Két korábbi spec-tévedés javítva (elcsúszott parancsazonosító-tábla; „12 tétel / az AUTO nincs a tömbben”). ✅ **2026-08-30 — a NY-5 (`Színkezelés használata`, #1582) LEZÁRVA az olcsó lánccal**: önálló kapcsoló, `Preferences\EnableColorManagement` (alap 0), bekapcsoláskor a szerkesztő-előnézet újraépül, az ICC a beágyazott `icc_camera_profile`/`icc_camera_to_tone_matrix` tagokból. Melléklelet (⚠️): a `0x9c9e` funkcionálisan a `ShowHidden`-t kezeli, az `EnableColorManagement` pipája a `0x9d72`-n ül — a menü-felirat párosítás a tulajdonos képeivel MEGERŐSÍTVE (a pipa a „Színkezelés használata" során), ld. 5.12. ✅ **A NY-1/3/4 (#1580) is LEZÁRVA**: NY-1 a mód NEM hat az exportra/nyomtatásra (a kimenetek bájtszinten azonosak); NY-3 a Mac gamma VILÁGOSÍT (`pow(x,1/1,6)`, teljes felületre, a fotó +15,7%), a „fekete képernyő" feltételezés megdőlt → **#1730** a megvalósítási jegy; NY-4 diavetítésben nem hat. ✅ **2026-08-30 — NY-2 („miért 1,44") LEZÁRVA matematikailag**: a 256 bájtos tábla legjobb hatványillesztése p=0,6944 (`round(255·(i/255)^p)`), azaz gamma 1,440; a tábla a szerződés, képlet-illesztés NEM kell. Maradt: NY-6 (csak bit-szemcséhez). |
| [picasa-kereses-modok.md](picasa-kereses-modok.md) | **A keresési módok és a másodpéldány-kereső** — az `ID_DUPES` keresési MÓD, nem panel; a keresési sáv 6 élő és **13 halott** eleme tételesen; a „hasonló képek" keresés az eredetiben NEM létezik; az importáláskori dupe-ellenőrzés aszinkron feladatsor; **az idő-csúszka KOR-szűrő** (`napok = 2^(13·(1−s))+1`), nem dátumtartomány, és a felirata az eredetiben is félrevezet. **A másodpéldány-DÖNTÉS KULCSA Ghidrával MEGFEJTVE (2026-08-30):** az \`originfast\` (MD5) 64 bites keresése a dupe-listában — a #1481 képlete. Jegy: **#1398** |
| [picasa-nerdview-panel.md](picasa-nerdview-panel.md) | **A „Hisztogram és fényképezőgép-adatok" panel MÉRT geometriája** — a panel 238 × 144; a felirat egysoros, 11 képpont magas és **nem félkövér** (a `.tre` semmit nem jelöl); a hisztogram 213 × 59 (ez nálunk helyes); a két adatoszlop 138 + 6 rés + 69. Jegy: **#1344** |
| [picasa-lebego-ertesito.md](picasa-lebego-ertesito.md) | A lebegő értesítősáv (`CNotifierPopup`) — képernyőfelvétel- és import-értesítés, kattintás-viselkedés. ⚠️ **Az „a geometria NYITOTT" megjegyzés 2026-08-24-én ELAVULTNAK bizonyult:** a geometria mérve van (a lap „Geometria — mérve a binárisból" szakasza), a pozicionálás dekompilálva (`SPI_GETWORKAREA` + 144 képpont). **Ami tényleg nyitva volt: a cella élettartama és az animáció ütemforrása** — a cella élettartama **LEZÁRVA 2026-08-26** (abszolút határidő `cella+0xb8`, képkockánként ellenőrizve), az ütemforrás **LEZÁRVA 2026-08-30** (a vtable 0x60 rekesze: `CNotifierPopup::vftable` 25. rekesz = `0x006575b0`). Jegy: **#1130** |
| [vorosszem-eszkoz-terve.md](vorosszem-eszkoz-terve.md) | A vörösszem-eszköz terve |
| [vagas-eszkoz-allapot.md](vagas-eszkoz-allapot.md) | A vágás-eszköz állapota — 19 arány, egyéni arányok, 3 javaslat |

## Nyelv és megjelenés

| lap | miről szól |
|---|---|
| [picasa-hu-terminology.md](picasa-hu-terminology.md) | Hivatalos Picasa-magyar terminológia |
| [picasa-effekt-nevek.md](picasa-effekt-nevek.md) | Az effektek nevei és buboréksúgói |
| [picasa-effekt-feliratok.md](picasa-effekt-feliratok.md) | Az effekt-vezérlők feliratai |
| [picasa-gomb-es-menu-rendszer.md](picasa-gomb-es-menu-rendszer.md) | **A gomb- és menürendszer** — 9-szeletes gombok, állapotszínek, tipográfia, a kétféle menü |
| [picasa-eger-es-kijeloles.md](picasa-eger-es-kijeloles.md) | **Egér, kijelölés, kattintás-viselkedés** — a `.tre` interakciós szótár, a Ctrl/Shift-modell, a kijelölés **mappa-hatóköre**, a Ctrl+A/Home/End teljes leképezése |
| [design-guide.md](design-guide.md) | Dizájn-kézikönyv — hűség-referencia |
| [ux-principles.md](ux-principles.md) | UX-alapelvek — „a Picasa lelke" |

## Módszertan és tervezés

| lap | miről szól |
|---|---|
| [binaris-regeszet-modszertan.md](binaris-regeszet-modszertan.md) | **A szerszámosláda**: mit hoz ki egy eszköz, és mit NEM lát; **22.5: a horgony-előírás megsértése 12 leírt elemet tett láthatatlanná** a lefedettségi mérésben (#2182) |
| [feature-map.md](feature-map.md) | Funkciótérkép és fázisterv |

## Mikor kell ezt a lapot frissíteni

| mikor | mit |
|---|---|
| **Új spec-lap születik** | egy sor a témakör táblájába — **ugyanabban a PR-ban** |
| **Egy kör nyitott kérdést ZÁR LE** | a kérdés kikerül a „Nyitott kérdések" listáról; ha a lapon nem marad több, a lap fejléce is |
| **Egy kör ÚJ nyitott kérdést talál** | egy sor a lap listájába, **egy mondatban megfogalmazva** — ne csak „Nyitva" szót írj a spec-lapra |
| **Egy lap átnevezése/összevonása** | a hivatkozás javítása |
| **Kutatói kör INDULÁSAKOR** | csak olvasod — innen választasz témát |

**A frissítés nem külön kör.** Aki hozzányúl egy spec-laphoz, ugyanabban a
PR-ban hozza rendbe ezt a listát is — így az index nem tud elavulni.

⚠️ **Ne gépi szó-számlálással tartsd karban.** A `Nyitva`/`dekódolatlan`
szavak nagy része **hivatkozás** egy máshol megválaszolt pontra; a
számlálás háromszorosára fújja a képet. A lista **kézzel írt kérdésekből**
áll, mert egy kutatói kör kérdést választ, nem szót.

A gyanús helyek gyors előkeresésére (ellenőrzésre, nem karbantartásra):

```bash
grep -n 'Nyitva\|NYITOTT\|dekódolatlan\|uncalibrated' docs/specs/*.md \
  | grep -v '~~' | grep -v 'LEZÁRVA\|MEGVÁLASZOLVA\|MEGOLDVA\|MEGDŐLT'
```
