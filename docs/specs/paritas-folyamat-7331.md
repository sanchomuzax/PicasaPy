# #7331: Beállítások OK-ja: arcküszöb-frissítés és a `0x00487590` szerepe

**Állapot: feltételes.** A statikus bináris út megmutatja, mikor hívódik a `0x00487590`, és hogy az albumcímke-tagságot módosító segédeket használja. A kapott lista pontos jelentése és a Személyek panel azonnali, látható változása nincs igazolva.

## Forráshivatkozás és hatókör

A feladat a `docs/specs/paritas-folyamat-7325.md` 5. szakaszára hivatkozott. Ez a fájl nincs meg ebben a munkafában, ezért az állítólagos 5. szakasz tartalmát nem vettem át és nem rekonstruáltam. Ez a lap kizárólag a #7331-ben megadott címekre és kérdésre szorítkozik.

Az eredeti Ghidra-kimenet már rendelkezésre áll: `~/picasapy-agent/referencia/ghidra/2026-11-20-koteg-574-579.txt`, `FUN_00487590`. A célzott helyi diszasszembly a `0x0048aab0`, `0x005cf5b0` és `0x00487590` függvényekre készült; teljes `.text` pásztázás nem történt.

## Következtetés

A `0x005cf5b0` a `0x00487590`-et csak akkor hívja, ha a `0x0048aab0(0)` pontosan `0xf4240`-et ad. Ebben az útban a `0x0048aab0` ezt az értéket akkor adja, ha a `FRSuggestionThreshold` vagy a `FRSuggestionSingleThreshold` értéke változott; ha mindkettő változatlan, nullával tér vissza. Ez cáfolja azt az állítást, hogy mindig `0xf4240`-et ad.

A `0x00487590` egy, a `0x00449a90`-től kapott lista alapján albumcímke-tagságot távolít el és ad hozzá (`0x0045ecf0`, `0x004d9aa0`). Ez tagsági listaegyeztető műveletként olvasható. A lista pontos jelentése és az, hogy ez azonnal módosítja-e a People panel javaslatait, **NINCS MEG**. A statikus kód önmagában nem bizonyítja a Red detektor újrafuttatását vagy a panel látható frissülését.

## Bizonyíték

| Érték vagy állítás | Forrás |
|---|---|
| A `0x005cf5b0` a `0x0048aab0(0)` eredményét `0xf4240`-hez hasonlítja; eltéréskor kihagyja a `0x00487590`-et. | bináris (`0x005cfe6d`-`0x005cfe79`) |
| A `0x0048aab0` az `arg=0` útban beolvassa a `FRSuggestionThreshold`, `FRSuggestionSingleThreshold`, `FRSortThreshold` és `FRRecommendIncludeLimit` kulcsokat. | bináris (`0x0048aab0`-`0x0048ad98`) |
| A visszatérési feltétel csak a korábbi és új `FRSuggestionThreshold`, valamint `FRSuggestionSingleThreshold` értéket hasonlítja össze; egyezéskor `0`, eltéréskor `0xf4240` a visszatérés. | bináris (`0x0048ad9e`-`0x0048adcc`, `0x0048ae7e`-`0x0048ae87`) |
| A felületi `facethresh1` kulcsa `FRSortThreshold`; a `0x0048aab0` ezt újratölti, de nem hasonlítja össze a sentinel kiválasztásakor. | bináris (`0x006e0ee8`, `0x0048ab56`-`0x0048ab9b`, `0x0048ad9e`-`0x0048adc2`); korábbi megfeleltetés: [picasa-arcfelismeres.md §1.1](picasa-arcfelismeres.md) |
| Sentinel esetén a hívó meghívja a `0x00487590`-et, majd feltételesen a `0x0047baf0`-t, és beállítja a panelobjektum `+0x166` bájtját. | bináris (`0x005cfe7b`-`0x005cfed6`) |
| A `0x00487590` a `0x00449a90`-től kér listát, majd albumonként a `0x0045ecf0` és `0x004d9aa0` címkemódosítókat hívja; a végén nullával tér vissza. | bináris (`0x00487590`; Ghidra: `2026-11-20-koteg-574-579.txt`, a függvény C-törzse) |
| A `0x0045ecf0` címketagságot távolít el; a `0x004d9aa0` címketagságot ad hozzá. | bináris (`0x0045ecf0`, `0x004d9aa0`); korábbi helper-azonosítások: [ui-audit-context-menus.md §D.8.3](ui-audit-context-menus.md), [picasa-arcfelismeres-kutatasi-naplo.md](picasa-arcfelismeres-kutatasi-naplo.md) |
| A `0x00449a90` kimeneti listájának pontos elem- és albumjelentése. | NINCS MEG |
| A Beállítások OK-ja utáni azonnali People-panel javaslatlista-változás a mintaképeken. | NINCS MEG; a helyi `meroadat.tar` nem tartalmaz ehhez használható arcmintát vagy felvételt. |

## Két bizonyítéki út

- **A út: a bináris utasításszintű olvasása:** a `0x0048aab0` összehasonlításai és visszatérési ágai, majd a `0x005cf5b0` feltételes hívása megadják a sentinel kaput és a hívási sorrendet. A `0x00487590` célzott diszasszembly-je közvetlenül mutatja a `0x00449a90`, `0x0045ecf0` és `0x004d9aa0` hívásokat.
- **B út: Ghidra-függvénytörzs és a segédfüggvények külön azonosítása:** a meglévő Ghidra-kimenet a `0x00487590` listakezelő ciklusát és albumonkénti segédfüggvény-hívásait külön C-nézetben mutatja. A másik két helper szerepét a korábbi, más hívási környezetből származó spec-elemzések rögzítik.

A két út egyezik a kapuról és az albumcímke-tagság módosításáról. Mivel ugyanazon bináris függvények elemzésére támaszkodnak, és nincs független futásmérés a People panelről, a teljes felhasználói következmény bizonyítottsága **feltételes**, nem megerősített.

## Cáfoló kísérletek

1. **A „`0x0048aab0` mindig `0xf4240`” állítás cáfolata:** az azonos `arg=0` útban megvizsgáltam a két küszöb változatlan ágát. Az utasítások a `0x0048adc4` címen nullázzák az `EAX`-ot, majd visszatérnek. Az állítás megdőlt; a változatlan és változott ágakat ugyanazzal az utasításszintű mércével ellenőriztem.
2. **A tagság-egyeztető olvasat cáfolási próbája:** a `0x00487590` teljes, 1273 soros célzott diszasszembly-jében közvetlen hívásként kerestem a már dokumentált `0x0048e1f0` Red-pontszám utólagos ajánlási szűrőt. Közvetlen hívást nem találtam; a közvetlen hívások között a `0x0045ecf0` és `0x004d9aa0` címkemódosítók viszont szerepelnek. Ez támogatja, de nem bizonyítja a tagság-egyeztető értelmezést: a függvény több indirekt hívása feloldatlan, így közvetett Red- vagy detektorhívás nem zárható ki. A negatív próbát ezért azonos célzott diszasszembly-vel, nem indexhiánnyal ellenőriztem.

## A briefben megadott „Kész, ha” vizsgálati pontok

- ✅ **A `0x00487590` Ghidra-dekompilálása:** megvan a `2026-11-20-koteg-574-579.txt` fájlban, a `FUN_00487590` törzseként.
- ⛔ **Colab: küszöbcsúszka mozgatása, OK, majd a Személyek panel javaslatainak azonnali összevetése:** nincs helyi arcminta és nincs ilyen mérés. A Colab-felvétel nem készült el.

## Nyitott

- `Ghidra-kör kell: 0x00449a90: pontosan milyen személy-, arc- vagy albumbejegyzéseket ad vissza a 0x00487590 által feldolgozott listában, és hogyan kapcsolódik ez a küszöbértékekhez? [blokkoló]` A címet a meglévő `referencia/ghidra/*.txt` fájlokban kerestem; hivatkozások vannak, önálló `0x00449a90` dekompiláció nincs.
- **Colab-mérés szükséges:** az arcos mintakészleten a Névcímkék küszöbcsúszkáját módosítani, OK-t választani, majd azonnal összevetni a Személyek panel javaslatait; rögzíteni kell a mozdított vezérlőt és a javaslatlistát OK előtt és után. A helyi `meroadat.tar` ehhez nem tartalmaz adatot.
- **A közvetett frissítőút nyitott:** a `0x00487590` feloldatlan indirekt hívásai és a `0x0047baf0` látható felületi hatása nincsenek azonosítva.
- **Forráslap hiányzik:** a hivatkozott `docs/specs/paritas-folyamat-7325.md` nem érhető el ebben a munkafában; a #7331-et ettől független új lapon dokumentáltam.

## Javasolt jegytörzs-bővítés

A `0x00487590` dekompilálása elkészült. A `0x005cf5b0` csak akkor hívja, ha a `0x0048aab0(0)` `0xf4240`-et ad; a közvetlen diszasszembly szerint ez a `FRSuggestionThreshold` vagy `FRSuggestionSingleThreshold` változásához kötött, nem minden beállítás-OK-hoz. A `0x00487590` listaalapú albumcímke-tagságot egyeztet a `0x0045ecf0` és `0x004d9aa0` hívásával. A lista jelentése és a People panel azonnali változása nincs bizonyítva. A Colab-felvételhez szükséges arcminta a helyi mérőadatban nem található.

**Teendő:** célzott Ghidra-kör a `0x00449a90` listajelentésére, majd Colab-felvétel a küszöb OK előtti/utáni javaslatlistával. Eredeti/PicasaPy eltérés vagy fejlesztői teendő ebből a kutatásból nem bizonyított.

## Új kutatási jegyjavaslatok

Nincs. A hiányzó listaértelmezés és a Colab-mérés ugyanennek a #7331 kérdésnek a nyitott része.

## Módosított fájlok

- `docs/specs/paritas-folyamat-7331.md`: a #7331 statikus eredményei, bizonyítottsági határai, cáfoló próbái és nyitott mérése.
- `docs/specs/00-index.md`: indexhivatkozás erre az új lapra.
